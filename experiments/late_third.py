"""Third-window check (2015 to 2018) for the dead-team input that helped both windows: out of the race from week
12 with a win rate at or under 40%, own and opponent; and the 30% variant. Output reports/late_third.csv."""
import numpy as np, pandas as pd
from nflmodel import model as M, backtest as B
from nflmodel.model import OUT
f = M.with_trends(pd.read_parquet(OUT / "features_asof.parquet")); g = pd.read_parquet(OUT / "games.parquet")
r = g[(g.game_type == "REG") & g.home_score.notna()][["game_id", "season", "week", "home_team", "away_team", "home_score", "away_score"]]
long = pd.concat([r.assign(team=r.home_team, win=(r.home_score > r.away_score).astype(float)), r.assign(team=r.away_team, win=(r.away_score > r.home_score).astype(float))]).sort_values(["season", "team", "week"])
long["wb"] = long.groupby(["season", "team"]).win.cumsum() - long.win; long["gb"] = long.groupby(["season", "team"]).cumcount()
long["pct"] = np.where(long.gb > 0, long.wb / long.gb.clip(lower=1), 0.5); pct = long.set_index(["game_id", "team"]).pct
f["pct_before"] = [pct.get((k, t), 0.5) for k, t in zip(f.game_id, f.team)]; f["opp_pct_before"] = [pct.get((k, t), 0.5) for k, t in zip(f.game_id, f.opp)]
base = M.FEATS.copy(); rows = []
def run(name, cols):
    M.FEATS = base + cols
    p3 = M.walk_forward(f, range(2015, 2019)); d = B.join(p3, g); M.FEATS = base
    d = d[(d.game_type == "REG") & d.season.isin(range(2015, 2019)) & (d.week < 18) & d.spread_line.notna() & d.home_score.notna()]
    pm = B.points_miss(d).set_index("target"); e = d.model_spread - d.spread_line; res = np.sign(d.home_score - d.away_score - d.spread_line)
    m = (np.abs(e) >= 4) & (res != 0); w = int((np.sign(e[m]) == res[m]).sum())
    late = d[d.week >= 14]; el = late.model_spread - late.spread_line; rl = np.sign(late.home_score - late.away_score - late.spread_line); ml = (np.abs(el) >= 4) & (rl != 0); wl = int((np.sign(el[ml]) == rl[ml]).sum())
    row = {"variant": name, "team_mae": round(float(pm.loc["team points", "model_mae"]), 4), "margin_mae": round(float(pm.loc["margin", "model_mae"]), 4), "ats4": f"{w}-{int(m.sum()) - w}", "late_ats4": f"{wl}-{int(ml.sum()) - wl}"}
    rows.append(row); print(row, flush=True)
run("today", [])
for start, cut in [(12, 0.4), (12, 0.3)]:
    late = (f.week >= start).astype(float); f["dead"] = late * (f.pct_before <= cut).astype(float); f["opp_dead"] = late * (f.opp_pct_before <= cut).astype(float)
    run(f"out of the race: week {start}+, win rate <= {cut:.0%}", ["dead", "opp_dead"])
pd.DataFrame(rows).to_csv("reports/late_third.csv", index=False); print("DONE")
