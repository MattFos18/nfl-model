"""Offseason turnover: early in a season the ratings lean on last season, but the roster may not be last season's.
Continuity = the share of last season's offensive (defensive) snaps taken by players on this week's roster, applied
for weeks 1 to 8 (1.0 after). Own and opponent, both windows. Output reports/continuity.csv."""
import numpy as np, pandas as pd
from nflmodel import model as M, positions as P
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
    if week > 8: return 1.0
    prev = (last_off if side == "off" else last_def).get((season - 1, team))
    keys = roster_keys.get((season, week, team))
    if prev is None or keys is None or prev.sum() == 0: return np.nan
    return float(prev[prev.index.isin(keys)].sum() / prev.sum())
f = M.with_trends(pd.read_parquet(OUT / "features_asof.parquet"))
f["off_continuity"] = [cont(r.season, r.week, r.team, "off") for r in f[["season", "week", "team"]].itertuples()]
f["opp_def_continuity"] = [cont(r.season, r.week, r.opp, "def") for r in f[["season", "week", "opp"]].itertuples()]
for c in ["off_continuity", "opp_def_continuity"]:
    print(c, f[c].describe().round(3).to_dict(), flush=True); f[c] = f[c].fillna(f[c].median())
# as an interaction: how much of last season's rating to trust (continuity x early-season flag)
f["early"] = (f.week <= 8).astype(float)
f["off_turnover_early"] = (1 - f.off_continuity) * f.early; f["opp_def_turnover_early"] = (1 - f.opp_def_continuity) * f.early
B = M.FEATS.copy(); rows = []
for name, feats in {"base": B, "+ own offensive continuity": B + ["off_turnover_early"], "+ opponent defensive continuity": B + ["opp_def_turnover_early"], "+ both": B + ["off_turnover_early", "opp_def_turnover_early"]}.items():
    M.FEATS = feats; r = both(f); M.FEATS = B
    rows.append({"variant": name, **{f"{k}_{w}": v for w, d in r.items() for k, v in d.items()}}); print(name, {w: (r[w]["team_mae"], r[w]["margin_mae"], r[w]["ats5"]) for w in r}, flush=True)
pd.DataFrame(rows).to_csv("reports/continuity.csv", index=False); print("DONE")
