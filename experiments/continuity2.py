"""Roster continuity looked strong; before adopting: (a) the early-season cutoff (4, 6, 8, 12 weeks, and all season),
(b) the third window 2015 to 2018, (c) coefficient signs. Output reports/continuity2.csv."""
import numpy as np, pandas as pd
from nflmodel import model as M, positions as P, backtest as B
from nflmodel.features import RAW, OUT, TEAM_FIX
from experiments.common import both
snaps = P.snaps_by_game(range(2012, 2027))
ros = []
for s in range(2013, 2027):
    f = RAW / "rosters" / f"roster_weekly_{s}.parquet"
    if f.exists():
        r = pd.read_parquet(f, columns=["season", "week", "team", "full_name", "status"]); r["team"] = r.team.replace(TEAM_FIX); ros.append(r[r.status == "ACT"])
ros = pd.concat(ros, ignore_index=True); ros["key"] = ros.full_name.map(P.norm)
roster_keys = {k: set(g.key) for k, g in ros.groupby(["season", "week", "team"])}
last_off = {}; last_def = {}
for (s, t), g in snaps.groupby(["season", "team"]):
    last_off[(s, t)] = g.groupby("key").offense_snaps.sum(); last_def[(s, t)] = g.groupby("key").defense_snaps.sum()
def cont(season, week, team, side):
    prev = (last_off if side == "off" else last_def).get((season - 1, team)); keys = roster_keys.get((season, week, team))
    if prev is None or keys is None or prev.sum() == 0: return np.nan
    return float(prev[prev.index.isin(keys)].sum() / prev.sum())
f = M.with_trends(pd.read_parquet(OUT / "features_asof.parquet")); games = pd.read_parquet(OUT / "games.parquet")
f["oc"] = [cont(r.season, r.week, r.team, "off") for r in f[["season", "week", "team"]].itertuples()]
f["dc"] = [cont(r.season, r.week, r.opp, "def") for r in f[["season", "week", "opp"]].itertuples()]
f["oc"] = f.oc.fillna(f.oc.median()); f["dc"] = f.dc.fillna(f.dc.median())
B_ = M.FEATS.copy(); rows = []
def add_cols(cut):
    e = (f.week <= cut).astype(float) if cut else 1.0
    f["off_turnover_early"] = (1 - f.oc) * e; f["opp_def_turnover_early"] = (1 - f.dc) * e
for cut in [4, 6, 8, 12, None]:
    add_cols(cut); M.FEATS = B_ + ["off_turnover_early", "opp_def_turnover_early"]; r = both(f); M.FEATS = B_
    rows.append({"variant": f"cutoff week {cut}" if cut else "all season", **{f"{k}_{w}": v for w, d in r.items() for k, v in d.items()}}); print(rows[-1]["variant"], {w: (r[w]["team_mae"], r[w]["margin_mae"], r[w]["ats5"]) for w in r}, flush=True)
# third window with cutoff 8, and the coefficients
add_cols(8)
def score3(feats):
    M.FEATS = feats; p = M.walk_forward(f, range(2015, 2019)); M.FEATS = B_
    d = B.join(p, games); d = d[(d.game_type == "REG") & d.season.isin(range(2015, 2019))]; pm = B.points_miss(d).set_index("target"); sp = B.summarize_bets(B.grade_spread(d, 5.0)).iloc[0]
    return round(float(pm.loc["team points", "model_mae"]), 4), round(float(pm.loc["margin", "model_mae"]), 4), f"{int(sp.wins)}-{int(sp.losses)}"
t0 = score3(B_); t1 = score3(B_ + ["off_turnover_early", "opp_def_turnover_early"])
print("third window base", t0, "with continuity", t1, flush=True)
rows.append({"variant": "third window 2015-18: base", "team_mae_third": t0[0], "margin_mae_third": t0[1], "ats5_third": t0[2]})
rows.append({"variant": "third window 2015-18: + continuity (cutoff 8)", "team_mae_third": t1[0], "margin_mae_third": t1[1], "ats5_third": t1[2]})
M.FEATS = B_ + ["off_turnover_early", "opp_def_turnover_early"]; ct = M.coefficient_table(M.prep(f), range(2013, 2026)); M.FEATS = B_
print(ct[ct.feature.isin(["off_turnover_early", "opp_def_turnover_early"])].to_string() if "feature" in ct.columns else ct.tail(3).to_string(), flush=True)
pd.DataFrame(rows).to_csv("reports/continuity2.csv", index=False); print("DONE")
