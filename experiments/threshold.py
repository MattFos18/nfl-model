"""Flag threshold re-swept after the rating re-tune (windows: 2019-22, 2023-25, all = 2019-25; the live season is a column of its own): spread edges 3 to 7 on both windows and season by season,
record, win rate and ROI at -110, plus totals for the record. Output reports/threshold_sweep.csv."""
import numpy as np, pandas as pd
from nflmodel import backtest as B
from nflmodel.model import OUT
p = pd.read_parquet(OUT / "pred_v3.parquet"); g = pd.read_parquet(OUT / "games.parquet")
d = B.join(p, g); d = d[(d.game_type == "REG") & d.home_score.notna() & d.spread_line.notna() & (d.week < 18)].copy()
d["edge"] = d.model_spread - d.spread_line; d["margin"] = d.home_score - d.away_score
d["res"] = np.sign(d.margin - d.spread_line); d["tedge"] = d.model_total - d.total_line; d["tres"] = np.sign(d.home_score + d.away_score - d.total_line)
rows = []
def rec(x, e, r):
    x = x[(np.abs(x[e]) >= cut) & (x[r] != 0)]; w = int((np.sign(x[e]) == x[r]).sum()); l = int(len(x) - w)
    return w, l, (w - l * 1.1) / (w + l) if w + l else np.nan
for cut in [3, 3.5, 4, 4.5, 5, 5.5, 6, 7]:
    for market, e, r in [("spread", "edge", "res"), ("total", "tedge", "tres")]:
        for win, sub in [("2019-22", d[d.season <= 2022]), ("2023-25", d[d.season.between(2023, 2025)]), ("all", d[d.season.between(2019, 2025)]), ("2015-18", d[d.season.between(2015, 2018)])] + [(str(s), d[d.season == s]) for s in sorted(d.season.unique())]:
            w, l, roi = rec(sub, e, r); rows.append({"market": market, "cut": cut, "window": win, "wins": w, "losses": l, "pct": round(w / (w + l), 3) if w + l else np.nan, "roi": round(roi, 3) if w + l else np.nan})
t = pd.DataFrame(rows); t.to_csv("reports/threshold_sweep.csv", index=False)
pv = t[t.market == "spread"].pivot(index="cut", columns="window", values="pct"); pn = t[t.market == "spread"].pivot(index="cut", columns="window", values="wins").astype(str) + "-" + t[t.market == "spread"].pivot(index="cut", columns="window", values="losses").astype(str)
print("SPREAD win rate (weeks 1-17)"); print(pv[["2019-22", "2023-25", "all"] + [c for c in pv.columns if c.isdigit()]].to_string()); print(pn[["2019-22", "2023-25", "all"]].to_string())
pv = t[t.market == "total"].pivot(index="cut", columns="window", values="pct"); print("TOTAL win rate"); print(pv[["2019-22", "2023-25", "all"]].to_string()); print("DONE")
