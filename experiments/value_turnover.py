"""Offseason turnover by value, not snaps (25 Sep 2026, Matt: "why does Micah Parsons have no impact when he's out?").
Parsons has been on a reserve list since December 2025, so the injury inputs (players newly out against the last game)
never see him, and the offseason-turnover input counts him only as his share of last season's defensive snaps (about
6% for GB, a tenth of a point). ATL lost 70% of last season's defensive snaps and the input charged them for it, with
no credit for who replaced them (they held GB to 14).

Here, as of Week 1 of each season, every player's value above replacement (positions.all_values: defenders by coverage,
pressure, run stops and forced fumbles; linemen, backs and receivers by their own measures; EPA per team play) is
tallied per team:
  gone   last season's players for the team (most snaps there) not on its active roster this week (left, cut, retired,
         or on a reserve list like Parsons)
  new    players on the active roster this week who played last season for another team, at their value there
for the defense (own and the opponent's) and the non-QB offense, active in Weeks 1 to 8 like the snap-share input,
added to the live equation. Walk-forward 2015-2025, scored on 2015-18, 2019-22 and 2023-25.
Writes reports/value_turnover.csv."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import numpy as np, pandas as pd
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from nflmodel import model as M, positions as PS, players as PL
from nflmodel.model import OUT

REP = Path(__file__).resolve().parent.parent / "reports"
CACHE = OUT / "value_turnover_values.parquet"


def values():
    if CACHE.exists():
        return pd.read_parquet(CACHE)
    g = pd.read_parquet(OUT / "games.parquet"); fr = []
    for s in range(2014, 2027):
        v = PS.all_values(g, s, 1)[["player_id", "group", "value_above_replacement"]].assign(season=s); fr.append(v); print("values", s, len(v), flush=True)
    v = pd.concat(fr, ignore_index=True); v.to_parquet(CACHE); return v


def table():
    V = values(); V = V[V.group != "QB"].dropna(subset=["value_above_replacement"])
    sn = pd.read_parquet(OUT / "snap_exposure.parquet", columns=["player_id", "season", "team", "offense_snaps", "defense_snaps"])
    sn["snaps"] = sn.offense_snaps.fillna(0) + sn.defense_snaps.fillna(0)
    last_team = sn.groupby(["player_id", "season", "team"]).snaps.sum().reset_index().sort_values("snaps").drop_duplicates(["player_id", "season"], keep="last")
    lt = {(p, s): t for p, s, t in zip(last_team.player_id, last_team.season, last_team.team)}
    ros = PL.load_rosters(range(2014, 2027)); ros = ros[ros.status == "ACT"]
    active = {k: set(x.gsis_id.dropna()) for k, x in ros.groupby(["season", "week", "team"])}
    val = {(p, s): (g_, v) for p, s, g_, v in zip(V.player_id, V.season, V.group, V.value_above_replacement)}
    # last season's contributors by team: every valued player whose most-snaps team last season was that team
    by_team = {}
    for (p, s), (g_, v) in val.items():
        t = lt.get((p, s - 1))
        if t is not None:
            by_team.setdefault((s, t), []).append((p, g_, v))
    games = pd.read_parquet(OUT / "games.parquet"); games = games[games.game_type == "REG"]
    rows = []
    for r in games.itertuples():
        if r.week > 8 or r.season < 2014:
            continue
        for tm in (r.home_team, r.away_team):
            act = active.get((r.season, r.week, tm), set()); out = {"game_id": r.game_id, "team": tm}
            for side, grp in (("def", {"Defense"}), ("off", {"Skill", "OL"})):
                gone = sum(v for p, g_, v in by_team.get((r.season, tm), []) if g_ in grp and p not in act)
                new = sum(val[(p, r.season)][1] for p in act if (p, r.season) in val and val[(p, r.season)][0] in grp and lt.get((p, r.season - 1)) not in (None, tm))
                out[f"{side}_gone"], out[f"{side}_new"] = gone, new
            rows.append(out)
    return pd.DataFrame(rows)


def main():
    T = table()
    f = M.prep(M.with_trends(pd.read_parquet(OUT / "features_asof.parquet"))).merge(T, on=["game_id", "team"], how="left")
    o = T.rename(columns={"team": "opp", "def_gone": "opp_def_gone", "def_new": "opp_def_new", "off_gone": "opp_off_gone", "off_new": "opp_off_new"})
    f = f.merge(o, on=["game_id", "opp"], how="left")
    cols = ["def_gone", "def_new", "off_gone", "off_new", "opp_def_gone", "opp_def_new", "opp_off_gone", "opp_off_new"]
    f[cols] = f[cols].fillna(0.0) * (f.week <= 8).values[:, None]
    g = f[(f.team == "GB") & (f.game_id == "2026_03_ATL_GB")]
    print("ATL at GB, GB's row:", g[cols].round(4).to_dict("records"))
    V = {"live": [], "opp defense gone": ["opp_def_gone"], "opp defense gone + new": ["opp_def_gone", "opp_def_new"],
         "own offense gone + new": ["off_gone", "off_new"], "all four": ["opp_def_gone", "opp_def_new", "off_gone", "off_new"]}
    played = f[f.pf.notna()]; rows = []
    for s in range(2015, 2026):
        for wk in sorted(f[f.season == s].week.unique()):
            tr = played[(played.season >= 2013) & ((played.season < s) | ((played.season == s) & (played.week < wk)))]
            te = f[(f.season == s) & (f.week == wk)]
            h = te[te.home == 1].set_index("game_id"); a = te[te.home == 0].set_index("game_id"); ids = h.index.intersection(a.index)
            if not len(ids):
                continue
            gg = pd.DataFrame({"game_id": ids, "season": s, "week": wk})
            for lab, ex in V.items():
                c = list(M.FEATS) + ex; m = make_pipeline(StandardScaler(), Ridge(alpha=10.0)).fit(tr[c].values, tr.pf.values)
                gg[f"h|{lab}"], gg[f"a|{lab}"] = m.predict(h.loc[ids, c].values), m.predict(a.loc[ids, c].values)
            rows.append(gg)
    P = pd.concat(rows).merge(pd.read_parquet(OUT / "games.parquet")[["game_id", "game_type", "home_score", "away_score", "result", "spread_line"]], on="game_id")
    P = P[(P.game_type == "REG") & P.result.notna()]
    out = []
    for lab in V:
        r = {"variant": lab}
        for w, (a_, b_) in {"2015-18": (2015, 2018), "2019-22": (2019, 2022), "2023-25": (2023, 2025)}.items():
            d = P[P.season.between(a_, b_)]; sp = d[f"h|{lab}"] - d[f"a|{lab}"]
            r[f"margin_{w}"] = round(float((sp - d.result).abs().mean()), 4)
            r[f"margin_wk1-8_{w}"] = round(float((sp - d.result)[d.week <= 8].abs().mean()), 4)
            r[f"team_{w}"] = round(float(pd.concat([(d[f"h|{lab}"] - d.home_score).abs(), (d[f"a|{lab}"] - d.away_score).abs()]).mean()), 4)
            x = d[d.spread_line.notna() & (d.week <= 17)]; e = (x[f"h|{lab}"] - x[f"a|{lab}"]) - x.spread_line; k = e.abs() >= 4; c_ = (x.result - x.spread_line)[k] * np.sign(e[k])
            r[f"4+_{w}"] = f"{int((c_ > 0).sum())}-{int((c_ < 0).sum())}"
        out.append(r); print(r, flush=True)
    pd.DataFrame(out).to_csv(REP / "value_turnover.csv", index=False)


if __name__ == "__main__":
    main()
