"""Late-season weakness (weeks 14 to 17 are the only stretch where the flag loses; the model overrates teams out
of the race late). Candidates on both windows: a dead-team input (win rate through the previous week at or under
a cut, from a start week), own and opponent; the same interacted with the week; and a plain late-season flag.
Output reports/late_season.csv."""
import numpy as np, pandas as pd
from nflmodel import model as M
from nflmodel.model import OUT
from experiments.common import both
f = M.with_trends(pd.read_parquet(OUT / "features_asof.parquet")); g = pd.read_parquet(OUT / "games.parquet")
r = g[(g.game_type == "REG") & g.home_score.notna()][["game_id", "season", "week", "home_team", "away_team", "home_score", "away_score"]]
long = pd.concat([r.assign(team=r.home_team, win=(r.home_score > r.away_score).astype(float)), r.assign(team=r.away_team, win=(r.away_score > r.home_score).astype(float))]).sort_values(["season", "team", "week"])
long["wb"] = long.groupby(["season", "team"]).win.cumsum() - long.win; long["gb"] = long.groupby(["season", "team"]).cumcount()
long["pct"] = np.where(long.gb > 0, long.wb / long.gb.clip(lower=1), 0.5); pct = long.set_index(["game_id", "team"]).pct
f["pct_before"] = [pct.get((k, t), 0.5) for k, t in zip(f.game_id, f.team)]; f["opp_pct_before"] = [pct.get((k, t), 0.5) for k, t in zip(f.game_id, f.opp)]
base_feats = M.FEATS.copy(); rows = []
def row(name, r): return {"added": name, **{f"{k}_{w}": v for w, d in r.items() for k, v in d.items()}}
base = both(f); rows.append(row("(none)", base)); print("base", {w: (base[w]["team_mae"], base[w]["margin_mae"]) for w in base}, flush=True)
def run(name, cols):
    M.FEATS = base_feats + cols; r = both(f); rows.append(row(name, r)); M.FEATS = base_feats
    print(name, {w: (round(r[w]["team_mae"] - base[w]["team_mae"], 4), round(r[w]["margin_mae"] - base[w]["margin_mae"], 4), r[w]["ats5"]) for w in r}, flush=True)
for start in [12, 14]:
    for cut in [0.3, 0.4]:
        late = (f.week >= start).astype(float)
        f["dead"] = late * (f.pct_before <= cut).astype(float); f["opp_dead"] = late * (f.opp_pct_before <= cut).astype(float)
        run(f"out of the race: week {start}+, win rate <= {cut:.0%} (own + opp)", ["dead", "opp_dead"])
late = (f.week >= 14).astype(float)
f["late_pct"] = late * (f.pct_before - 0.5); f["opp_late_pct"] = late * (f.opp_pct_before - 0.5)
run("late season x record so far (own + opp), week 14+", ["late_pct", "opp_late_pct"])
f["late"] = late; run("late-season flag (week 14+)", ["late"])
df = pd.DataFrame(rows)
for w in ["2019-22", "2023-25"]: df[f"delta_{w}"] = (df[f"team_mae_{w}"] - df.loc[0, f"team_mae_{w}"]).round(4)
df["verdict"] = ["base" if i == 0 else ("helps both" if d1 < -0.001 and d2 < -0.001 else ("helps one" if d1 < -0.001 or d2 < -0.001 else "no")) for i, (d1, d2) in enumerate(zip(df["delta_2019-22"], df["delta_2023-25"]))]
df.to_csv("reports/late_season.csv", index=False); print(df[["added", "delta_2019-22", "delta_2023-25", "verdict"]].to_string()); print("DONE")
