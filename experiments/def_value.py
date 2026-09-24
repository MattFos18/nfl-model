"""Defender value: credited plays, or what each defender's plays were worth (24 Sep 2026)?

The Players tab valued a defender by the -EPA of the plays he was credited on (tackles, sacks, QB hits, passes
defended, interceptions, forced fumbles), per snap. Two faults found in the audit: the credits were summed per game,
not per play, so each game counted once, at his first credited play's EPA; and a corner nobody throws at, or who
allows short catches, had nothing credited, while a tackle after a long gain counted against the tackler. The
replacement (nflmodel/positions.py, DEF_W) values each defender's plays at what they are worth to the defense's EPA,
with weights measured on 2016-18 plays: coverage yards saved against the league's yards per target (PFR), picks,
sacks and other pressures (PFR), run stops and forced fumbles.

Test: each team-game's defense against the defenders who played it. For every defender, a decayed, shrunk per-snap
rate as of the game (earlier games only). A lineup's value = sum over its defenders of rate x snap share that game.
The team's defensive EPA per play (per dropback, per run) is predicted from the team's own prior defensive EPA plus
the lineup value, fitted leave-one-season-out inside each window:

  M0  team prior only
  M1  + credited plays (the old value, with the per-play fix)
  M2  + the new value (coverage, picks, pressures, run stops, forced fumbles)

Adopt M2 only if it beats M1 on both windows (2019-22 and 2023-25). Writes reports/def_value.csv. (An earlier
version of this file, on the per-game credit sums, tested coverage and pressures as extra terms beside them.)
"""
from __future__ import annotations
import numpy as np, pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT, REP = ROOT / "data" / "processed", ROOT / "reports"
DECAY, K = 0.99, 300.0
COLS = ["credit_epa", "epa"]


def rates_asof(d: pd.DataFrame, cols) -> pd.DataFrame:
    """Each player-game row gets the player's decayed, shrunk per-snap rate of each column from his earlier games."""
    d = d.sort_values(["season", "week"]).reset_index(drop=True); out = np.zeros((len(d), len(cols)))
    for _, idx in d.groupby("player_id").indices.items():
        sn = d.plays.values[idx]; vals = d[cols].values[idx]; num = np.zeros(len(cols)); den = 0.0
        for j, i in enumerate(idx):
            out[i] = num / (den + K)
            den = den * DECAY + sn[j]; num = num * DECAY + vals[j]
    return d.join(pd.DataFrame(out, columns=[f"r_{c}" for c in cols]))


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
    dg = pd.read_parquet(OUT / "defender_games.parquet"); dg = dg[dg.season >= 2017]
    d = rates_asof(dg, COLS)
    tsn = d.groupby(["game_id", "team"]).plays.transform("max"); d["w"] = d.plays / tsn
    lin = d.assign(**{f"L_{c}": d[f"r_{c}"] * d.w for c in COLS}).groupby(["game_id", "team"], as_index=False)[[f"L_{c}" for c in COLS]].sum()
    tg = pd.read_parquet(OUT / "team_games.parquet"); tg = tg[(tg.game_type == "REG") & tg.def_epa_play.notna() & (tg.season >= 2017)].copy()
    res = []
    for target in ["def_epa_play", "def_pass_epa", "def_rush_epa"]:
        tg[f"prior_{target}"] = team_prior(tg, target)
        x = tg.merge(lin, on=["game_id", "team"], how="inner")
        for window, seasons in [("2019-22", range(2019, 2023)), ("2023-25", range(2023, 2026))]:
            w = x[x.season.isin(seasons)]
            for name, fc in [("M0 team prior", []), ("M1 + credited plays (old, per-play fix)", ["L_credit_epa"]), ("M2 + new value", ["L_epa"])]:
                err, coefs = [], []
                for s in seasons:
                    tr, te = w[w.season != s], w[w.season == s]
                    X = np.column_stack([np.ones(len(tr)), tr[f"prior_{target}"]] + [tr[c] for c in fc]); b = np.linalg.lstsq(X, tr[target].values, rcond=None)[0]
                    Xt = np.column_stack([np.ones(len(te)), te[f"prior_{target}"]] + [te[c] for c in fc]); err.append(te[target].values - Xt @ b); coefs.append(b)
                e = np.concatenate(err); b = np.mean(coefs, axis=0)
                res.append({"target": target, "window": window, "model": name, "rmse": round(float(np.sqrt(np.mean(e ** 2))), 6), "mae": round(float(np.mean(np.abs(e))), 6), "n": int(len(e)),
                            "coefs": ", ".join(f"{k} {v:+.4g}" for k, v in zip(["const", "prior"] + fc, b))})
    return pd.DataFrame(res)


if __name__ == "__main__":
    r = evaluate(); REP.mkdir(exist_ok=True); r.to_csv(REP / "def_value.csv", index=False)
    pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 120)
    for t in r.target.unique():
        print(t); print(r[r.target == t].pivot_table(index="model", columns="window", values="rmse").to_string())
    print(r[r.model.str.startswith(("M1", "M2"))][["target", "window", "model", "coefs"]].to_string(index=False))
