"""Defenders out as a game-model input, on the corrected defender value (24 Sep 2026).

experiments/positions.py tested this on 22 Sep with the old defender value (credited plays summed per game) and did
not adopt it. The value is now what each defender's plays were worth (coverage, picks, pressures, run stops),
against his own group's replacement (edge, interior line, linebacker, corner, safety). For every team-game: the sum,
over defenders listed Out or Doubtful (or off the active roster), of (value - replacement) x snap share over his last
eight games. Variants on the current model's inputs, both windows. Writes reports/def_value_out.csv."""
import numpy as np, pandas as pd
from nflmodel import model as M, positions as P, players as PL
from nflmodel.model import OUT
from experiments.common import both

games = pd.read_parquet(OUT / "games.parquet"); seasons = range(2013, 2027)
dg = pd.read_parquet(OUT / "defender_games.parquet")
roles = P.defender_roles(dg); dg = dg.assign(role=dg.player_id.map(roles))
inj = PL.load_injuries(seasons); inj = inj[inj.report_status.isin(["Out", "Doubtful"])]
out_by = {k: set(g.gsis_id.dropna()) for k, g in inj.groupby(["season", "week", "team"])}
for k, ids in PL.unavailable_by_week(seasons).items():
    out_by[k] = out_by.get(k, set()) | ids
pv = PL.PlayerValues(dg, 0.99, 300.0)
def_by = {pid: g for pid, g in dg.groupby("player_id")}
team_dsn = dg.groupby(["game_id", "team"]).plays.max()
long = pd.concat([games[["game_id", "season", "week", "home_team"]].rename(columns={"home_team": "team"}), games[["game_id", "season", "week", "away_team"]].rename(columns={"away_team": "team"})])
long = long[long.season >= 2013]
rows = []
for r in long.itertuples():
    dv = 0.0
    for pid in out_by.get((r.season, r.week, r.team), set()):
        g = def_by.get(pid)
        if g is None:
            continue
        h = g[(g.season < r.season) | ((g.season == r.season) & (g.week < r.week))].tail(8)
        if len(h) == 0:
            continue
        role = roles.get(pid, "CB"); v, n = pv.value(pid, role, r.season, r.week); pr = pv.prior(role, r.season)
        tsn = team_dsn.reindex(list(zip(h.game_id, h.team))).values
        share = float(np.nanmean(h.plays.values / tsn)) if len(tsn) else 0.0
        dv += (v - pr) * min(share, 1.0)
    rows.append({"game_id": r.game_id, "team": r.team, "def_value_out": dv})
X = pd.DataFrame(rows)
f = M.with_trends(pd.read_parquet(OUT / "features_asof.parquet")).merge(X, on=["game_id", "team"], how="left")
f = f.merge(X.rename(columns={"team": "opp", "def_value_out": "opp_def_value_out"}), on=["game_id", "opp"], how="left")
for c in ["def_value_out", "opp_def_value_out"]:
    f[c] = f[c].fillna(0.0)
B = M.FEATS.copy(); res = []
for name, feats in {f"base ({len(B)})": B, "+ opponent defenders' value out": B + ["opp_def_value_out"], "+ own defenders' value out": B + ["def_value_out"],
                    "+ both": B + ["opp_def_value_out", "def_value_out"]}.items():
    M.FEATS = feats; rr = both(f); M.FEATS = B
    res.append({"variant": name, **{f"{k}_{w}": v for w, d in rr.items() for k, v in d.items()}})
    print(name, {w: (rr[w]["team_mae"], rr[w]["margin_mae"], rr[w]["ats4"]) for w in rr}, flush=True)
pd.DataFrame(res).to_csv("reports/def_value_out.csv", index=False); print("DONE")
