"""Ideas not yet run under the both-windows rule: rest (short week / off a bye, and the rest difference in days),
playing surface, teams out of the race late in the season, and the ridge penalty on the twenty-input model.
Output reports/rest_more.csv."""
import numpy as np, pandas as pd
from nflmodel import model as M
from nflmodel.model import OUT
from experiments.common import both
f = M.with_trends(pd.read_parquet(OUT / "features_asof.parquet"))
g = pd.read_parquet(OUT / "games.parquet")
# surface
surf = g.set_index("game_id").surface.fillna("").str.lower()
f["turf"] = f.game_id.map(lambda k: 0.0 if surf.get(k, "") in ("grass", "") else 1.0)
# record through the previous week, from games (regular season only)
r = g[g.game_type == "REG"][["game_id", "season", "week", "home_team", "away_team", "home_score", "away_score"]].dropna(subset=["home_score"])
long = pd.concat([r.assign(team=r.home_team, win=(r.home_score > r.away_score).astype(float)), r.assign(team=r.away_team, win=(r.away_score > r.home_score).astype(float))])
long = long.sort_values(["season", "team", "week"]); long["wins_before"] = long.groupby(["season", "team"]).win.cumsum() - long.win
long["games_before"] = long.groupby(["season", "team"]).cumcount(); long["pct_before"] = np.where(long.games_before > 0, long.wins_before / long.games_before.clip(lower=1), 0.5)
rec = long.set_index(["game_id", "team"]).pct_before
f["pct_before"] = [rec.get((k, t), 0.5) for k, t in zip(f.game_id, f.team)]
f["opp_pct_before"] = [rec.get((k, t), 0.5) for k, t in zip(f.game_id, f.opp)]
late = (f.week >= 14).astype(float)
f["dead"] = late * (f.pct_before <= 0.3).astype(float); f["opp_dead"] = late * (f.opp_pct_before <= 0.3).astype(float)
f["rest_diff"] = (f.rest - f.opp_rest).clip(-7, 7).fillna(0.0)
print("turf share", round(float(f.turf.mean()), 3), "dead share", round(float(f.dead.mean()), 3), flush=True)
base_feats = M.FEATS.copy(); rows = []
def row(name, r): return {"added": name, **{f"{k}_{w}": v for w, d in r.items() for k, v in d.items()}}
base = both(f); rows.append(row("(none)", base)); print("base", base, flush=True)
cands = {"rest short / long, both teams": ["rest_short", "rest_long", "opp_rest_short", "opp_rest_long"], "rest difference in days": ["rest_diff"],
         "artificial turf": ["turf"], "out of the race after week 13 (own / opp)": ["dead", "opp_dead"], "record so far (own / opp)": ["pct_before", "opp_pct_before"]}
for name, cols in cands.items():
    M.FEATS = base_feats + cols; r = both(f); rows.append(row(name, r))
    print(name, {w: (round(r[w]["team_mae"] - base[w]["team_mae"], 4), r[w]["ats5"]) for w in r}, flush=True); M.FEATS = base_feats
for a in [3.0, 30.0, 100.0]:
    r = both(f, alpha=a); rows.append(row(f"ridge penalty {a:g} (now 10)", r)); print("ridge", a, {w: (round(r[w]["team_mae"] - base[w]["team_mae"], 4), r[w]["ats5"]) for w in r}, flush=True)
df = pd.DataFrame(rows)
for w in ["2019-22", "2023-25"]: df[f"delta_{w}"] = df[f"team_mae_{w}"] - df.loc[0, f"team_mae_{w}"]
df["verdict"] = ["base" if i == 0 else ("helps both" if d1 < -0.001 and d2 < -0.001 else ("helps one" if d1 < -0.001 or d2 < -0.001 else "no")) for i, (d1, d2) in enumerate(zip(df["delta_2019-22"], df["delta_2023-25"]))]
df.to_csv("reports/rest_more.csv", index=False); print(df[["added", "delta_2019-22", "ats5_2019-22", "delta_2023-25", "ats5_2023-25", "verdict"]].to_string()); print("DONE")
