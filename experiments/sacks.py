"""Pass protection and pass rush: sacks allowed per dropback (offense) and sacks made per opponent dropback (defense),
opponent-adjusted with the same joint solve as the other ratings, as inputs. Both windows against the twenty-input
model. Output reports/sacks.csv."""
import numpy as np, pandas as pd, pyarrow.parquet as pq
from nflmodel import ratings as R, model as M
from nflmodel.features import RAW, OUT, TEAM_FIX
from experiments.common import both
frames = []
for s in range(2012, 2027):
    f = RAW / "pbp" / f"play_by_play_{s}.parquet"
    if f.exists(): frames.append(pd.read_parquet(f, columns=["game_id", "season", "week", "posteam", "defteam", "qb_dropback", "sack"]))
p = pd.concat(frames, ignore_index=True); p = p[(pd.to_numeric(p.qb_dropback, errors="coerce") == 1) & p.posteam.notna()]
for c in ["posteam", "defteam"]: p[c] = p[c].replace(TEAM_FIX)
g = p.groupby(["game_id", "season", "week", "posteam", "defteam"]).agg(db=("sack", "size"), sacks=("sack", lambda x: pd.to_numeric(x, errors="coerce").fillna(0).sum())).reset_index()
g["sack_rate"] = g.sacks / g.db
tg = pd.read_parquet(OUT / "team_games.parquet")
tg2 = tg.drop(columns=[c for c in ["sack_rate"] if c in tg.columns]).merge(g.rename(columns={"posteam": "team", "defteam": "opp"})[["game_id", "team", "opp", "sack_rate"]], on=["game_id", "team", "opp"], how="left")
# as-of rating with the same window and joint solve: offense term = sacks allowed (lower is better), defense term = sacks made
cache = {}
def rating(season, week):
    k = (season, week)
    if k in cache: return cache[k]
    rows, w = R.window(tg2[tg2.sack_rate.notna()], season, week, R.DEFAULT["decay"], R.DEFAULT["prior"])
    teams = sorted(set(tg2[tg2.season == season].team) | set(rows.team))
    O, D, mu, h = R.solve(rows, rows.sack_rate.values.astype(float), w, teams, R.DEFAULT["alpha"])
    cache[k] = (O.to_dict(), D.to_dict()); return cache[k]
f = M.with_trends(pd.read_parquet(OUT / "features_asof.parquet"))
oo, dd = [], []
for r in f[["season", "week", "team", "opp"]].itertuples():
    O, D = rating(r.season, r.week); oo.append(O.get(r.team, 0.0)); dd.append(D.get(r.opp, 0.0))
f["off_sack_rate"] = oo; f["def_sack_rate"] = dd    # offense: sacks allowed above average (bad); defense faced: sacks made above average
print("sack rating sd", round(float(np.std(oo)), 4), flush=True)
B = M.FEATS.copy(); rows = []
for name, feats in {"base (20)": B, "+ sacks allowed (offense)": B + ["off_sack_rate"], "+ sacks made (defense faced)": B + ["def_sack_rate"], "+ both": B + ["off_sack_rate", "def_sack_rate"]}.items():
    M.FEATS = feats; r = both(f); M.FEATS = B
    rows.append({"variant": name, **{f"{k}_{w}": v for w, d in r.items() for k, v in d.items()}}); print(name, {w: (r[w]["team_mae"], r[w]["margin_mae"], r[w]["ats5"]) for w in r}, flush=True)
pd.DataFrame(rows).to_csv("reports/sacks.csv", index=False); print("DONE")
