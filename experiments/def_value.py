"""Defender value: credited plays only, or credited plays plus coverage and pass rush? (24 Sep 2026)

The Players tab values a defender by the -EPA of the plays he is credited on (tackles, sacks, QB hits, passes
defended, interceptions, forced fumbles), per snap. A corner who is rarely thrown at, or who allows short catches,
gets no credit for it, and a rusher gets nothing for a pressure that is not a hit or a sack. Pro Football Reference's
weekly advanced defense table (2018 on) has what is missing: targets, yards and touchdowns allowed in coverage, and
hurries.

Test: each team-game's defense against the defenders who actually played it. For every defender, a decayed, shrunk
per-snap rate of each component as of the game (earlier games only). A lineup's component = the sum over its
defenders of rate x his snap share that game. Then the team's defensive EPA per play (and per dropback) is predicted
from the team's own prior defensive EPA plus the lineup components, fitted leave-one-season-out inside each window:

  M0  team prior only
  M1  + credited plays (today's value)
  M2  + credited plays, coverage yards saved, coverage TDs allowed, hurries

Adopt the extra components only if M2 beats M1 on both windows (2019-22 and 2023-25). Writes reports/def_value.csv.
"""
from __future__ import annotations
import numpy as np, pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
import sys; sys.path.insert(0, str(ROOT))
OUT, RAW, REP = ROOT / "data" / "processed", ROOT / "data" / "raw", ROOT / "reports"
DECAY, K = 0.99, 300.0
COMPS = ["credit", "cov_yds", "cov_td", "hurry", "press", "cov_int"]


def player_games() -> pd.DataFrame:
    dg = pd.read_parquet(OUT / "defender_games.parquet")
    dg = dg[dg.season >= 2017].rename(columns={"plays": "snaps", "epa": "credit"})
    fs = sorted((RAW / "pfr_advstats").glob("advstats_week_def_*.parquet"))
    a = pd.concat([pd.read_parquet(f) for f in fs], ignore_index=True)
    ids = {}
    for f in sorted((RAW / "rosters").glob("roster_weekly_*.parquet")):
        rr = pd.read_parquet(f, columns=["gsis_id", "pfr_id"]).dropna().drop_duplicates("pfr_id"); ids.update(dict(zip(rr.pfr_id, rr.gsis_id)))
    a["player_id"] = a.pfr_player_id.map(ids); a = a.dropna(subset=["player_id"])
    lg = a[a.def_targets > 0].groupby("season").apply(lambda x: x.def_yards_allowed.sum() / x.def_targets.sum()).rename("lg_ypt")
    a = a.merge(lg, on="season", how="left")
    a["cov_yds"] = (a.lg_ypt * a.def_targets.fillna(0) - a.def_yards_allowed.fillna(0))    # yards saved against the league's yards per target
    a["cov_td"] = -a.def_receiving_td_allowed.fillna(0)
    a["hurry"] = a.def_times_hurried.fillna(0)                                              # pressures that were not a hit or a sack (those are credited already)
    a["press"] = a.def_pressures.fillna(0)                                                  # every pressure: hurries, hits and sacks
    a["cov_int"] = a.def_ints.fillna(0)
    a = a.groupby(["game_id", "player_id"], as_index=False)[["cov_yds", "cov_td", "hurry", "press", "cov_int"]].sum()
    from nflmodel.positions import pfr_def_games     # the adopted matching (pfr id, then name inside the game)
    a = a.drop(columns=["cov_yds", "press", "cov_int"]).merge(pfr_def_games(dg.rename(columns={"snaps": "plays", "credit": "epa"})), on=["game_id", "player_id"], how="outer")
    d = dg.merge(a, on=["game_id", "player_id"], how="left")
    d["has_pfr"] = d.cov_yds.notna()
    for c in ["cov_yds", "cov_td", "hurry", "press", "cov_int"]:
        d[c] = d[c].fillna(0.0)
    return d.sort_values(["season", "week"]).reset_index(drop=True)


def rates_asof(d: pd.DataFrame) -> pd.DataFrame:
    """Each player-game row gets the player's decayed, shrunk per-snap rate of each component from his earlier games."""
    out = []
    for pid, g in d.groupby("player_id", sort=False):
        g = g.sort_values(["season", "week"]); sn = g.snaps.values.astype(float)
        num = {c: 0.0 for c in COMPS}; den = 0.0; rows = []
        for i in range(len(g)):
            rows.append([num[c] / (den + K) for c in COMPS])
            den = den * DECAY + sn[i]
            for c in COMPS:
                num[c] = num[c] * DECAY + float(g[c].values[i])
        r = pd.DataFrame(rows, columns=[f"r_{c}" for c in COMPS], index=g.index); out.append(r)
    return d.join(pd.concat(out))


def team_prior(tg: pd.DataFrame, col: str) -> pd.Series:
    """The team's decayed defensive EPA before each game (0.94 a week, last season at 0.8, like the model)."""
    tg = tg.sort_values(["season", "week"]); pri = pd.Series(index=tg.index, dtype=float)
    for team, g in tg.groupby("team"):
        num = den = 0.0; last_season = None
        for i, r in g.iterrows():
            if last_season is not None and r.season != last_season:
                num *= 0.8; den *= 0.8
            pri[i] = num / (den + 3.0)
            if pd.notna(r[col]):
                num = num * 0.94 + r[col]; den = den * 0.94 + 1.0
            last_season = r.season
    return pri


def evaluate() -> pd.DataFrame:
    d = rates_asof(player_games())
    tsn = d.groupby(["game_id", "team"]).snaps.transform("max"); d["w"] = d.snaps / tsn
    lin = d.assign(**{f"L_{c}": d[f"r_{c}"] * d.w for c in COMPS}).groupby(["game_id", "team"], as_index=False)[[f"L_{c}" for c in COMPS]].sum()
    tg = pd.read_parquet(OUT / "team_games.parquet"); tg = tg[(tg.game_type == "REG") & tg.def_epa_play.notna() & (tg.season >= 2017)].copy()
    res = []
    for target in ["def_epa_play", "def_pass_epa"]:
        tg[f"prior_{target}"] = team_prior(tg, target)
        x = tg.merge(lin, on=["game_id", "team"], how="inner")
        for window, seasons in [("2019-22", range(2019, 2023)), ("2023-25", range(2023, 2026))]:
            w = x[x.season.isin(seasons)]
            for name, cols in [("M0 team prior", []), ("M1 + credited plays", ["L_credit"]), ("M2 + coverage and hurries", [f"L_{c}" for c in COMPS]), ("M3 + coverage only", ["L_credit", "L_cov_yds", "L_cov_td"]),
                               ("M4 coverage yards and hurries, no credited plays", ["L_cov_yds", "L_hurry"]), ("M5 credited plays, coverage yards, hurries", ["L_credit", "L_cov_yds", "L_hurry"]),
                               ("M6 coverage yards and pressures", ["L_cov_yds", "L_press"]), ("M7 coverage yards, pressures, interceptions", ["L_cov_yds", "L_press", "L_cov_int"])]:
                err = []; coefs = []
                for s in seasons:
                    tr, te = w[w.season != s], w[w.season == s]
                    X = np.column_stack([np.ones(len(tr)), tr[f"prior_{target}"]] + [tr[c] for c in cols]); b = np.linalg.lstsq(X, tr[target].values, rcond=None)[0]
                    Xt = np.column_stack([np.ones(len(te)), te[f"prior_{target}"]] + [te[c] for c in cols]); err.append(te[target].values - Xt @ b); coefs.append(b)
                e = np.concatenate(err); b = np.mean(coefs, axis=0)
                res.append({"target": target, "window": window, "model": name, "rmse": round(float(np.sqrt(np.mean(e ** 2))), 6), "mae": round(float(np.mean(np.abs(e))), 5), "n": int(len(e)),
                            "coefs": ", ".join(f"{k} {v:+.4g}" for k, v in zip(["const", "prior"] + cols, b))})
    return pd.DataFrame(res)


if __name__ == "__main__":
    r = evaluate(); REP.mkdir(exist_ok=True); r.to_csv(REP / "def_value.csv", index=False)
    pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 140)
    print(r.to_string(index=False))
