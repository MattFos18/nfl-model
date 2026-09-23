"""Legitimacy tests on the walk-forward predictions (no refit): does the model carry information beyond the closing
line, or is the flag record something noise could produce? Output reports/legitimacy.md and legitimacy.csv.
1. Encompassing regression: margin on the closing spread and the model spread, held out. If the model's weight is
   near zero the line already contains everything the model knows.
2. Placebo: shuffle the model's lines across games within each week 2,000 times and record the 4+ flag record each
   time; where does the real record sit in that distribution?
3. Bootstrap: 2,000 resamples of the real 4+ flags, the 90% interval of the win rate and units at -110.
4. Leave-one-season-out: the 4+ record and spread miss per season, so no single season carries the result.
5. Every-game accuracy against the line, by season: is the model closer to the result than the line anywhere?"""
import numpy as np, pandas as pd
from nflmodel import backtest as B
from nflmodel.model import OUT
from nflmodel.features import ROOT
rng = np.random.default_rng(7)
p = pd.read_parquet(OUT / "pred_v3.parquet"); g = pd.read_parquet(OUT / "games.parquet"); d = B.join(p, g)
d = d[(d.game_type == "REG") & d.home_score.notna() & d.spread_line.notna() & (d.week < 18) & d.season.between(2019, 2025)].copy()
d["margin"] = d.home_score - d.away_score; d["edge"] = d.model_spread - d.spread_line; d["cover_res"] = np.sign(d.margin - d.spread_line)
L = [f"# Legitimacy tests, {pd.Timestamp.now('UTC'):%Y-%m-%d}", "", f"{len(d)} regular-season games 2019 to 2025, weeks 1 to 17, walk-forward predictions.", ""]
rows = []
# 1. encompassing
for name, sub in [("2019-22", d[d.season <= 2022]), ("2023-25", d[d.season >= 2023]), ("all", d)]:
    X = np.column_stack([np.ones(len(sub)), sub.spread_line, sub.model_spread]); beta, *_ = np.linalg.lstsq(X, sub.margin, rcond=None)
    resid = sub.margin - X @ beta; se = np.sqrt(np.diag(np.linalg.inv(X.T @ X)) * resid.var(ddof=3)); t = beta / se
    rows.append({"test": "encompassing", "window": name, "line_weight": round(beta[1], 3), "model_weight": round(beta[2], 3), "model_t": round(t[2], 2)})
    L.append(f"- Encompassing, {name}: margin = {beta[0]:.2f} + {beta[1]:.3f} x line + {beta[2]:.3f} x model (model t = {t[2]:.2f}). A model weight above zero with t past 2 means the line does not already contain what the model knows.")
L.append("")
# 2. placebo
def rec(x):
    f = (x.edge.abs() >= 4) & (x.cover_res != 0); w = int((np.sign(x.edge[f]) == x.cover_res[f]).sum()); return w, int(f.sum()) - w
real_w, real_l = rec(d); real_pct = real_w / (real_w + real_l)
pl = []
for _ in range(2000):
    s = d.copy(); s["model_spread"] = s.groupby(["season", "week"]).model_spread.transform(lambda v: rng.permutation(v.values)); s["edge"] = s.model_spread - s.spread_line
    w, l = rec(s); pl.append(w / (w + l) if w + l else np.nan)
pl = np.array(pl); pl = pl[~np.isnan(pl)]
rows.append({"test": "placebo", "window": "all", "real_pct": round(real_pct, 3), "placebo_mean": round(pl.mean(), 3), "placebo_95th": round(np.percentile(pl, 95), 3), "share_of_placebos_at_or_above_real": round(float((pl >= real_pct).mean()), 4)})
L += [f"- Placebo: the real 4+ record is {real_w}-{real_l} ({real_pct:.1%}). Shuffling the model's lines within each week 2,000 times gives a mean of {pl.mean():.1%} and a 95th percentile of {np.percentile(pl, 95):.1%}; {(pl >= real_pct).mean():.2%} of shuffles reach the real record.", ""]
# 3. bootstrap
f = d[(d.edge.abs() >= 4) & (d.cover_res != 0)]; wins = (np.sign(f.edge) == f.cover_res).values.astype(float)
bs = np.array([rng.choice(wins, len(wins)).mean() for _ in range(2000)]); units = (bs * len(wins)) - (1 - bs) * len(wins) * 1.1
rows.append({"test": "bootstrap", "window": "all", "n": len(wins), "pct_5th": round(np.percentile(bs, 5), 3), "pct_50th": round(np.percentile(bs, 50), 3), "pct_95th": round(np.percentile(bs, 95), 3), "share_below_breakeven": round(float((bs < 0.5238).mean()), 3)})
L += [f"- Bootstrap on the {len(wins)} real 4+ flags: 90% interval for the win rate {np.percentile(bs, 5):.1%} to {np.percentile(bs, 95):.1%}; {(bs < 0.5238).mean():.1%} of resamples fall under the 52.4% break-even.", ""]
# 4. leave-one-season-out and 5. per-season accuracy
L += ["| Season | Games | 4+ flags | Spread miss, model | Spread miss, line | Model closer |", "|---|---|---|---|---|---|"]
for s, x in d.groupby("season"):
    w, l = rec(x); mm = (x.margin - x.model_spread).abs().mean(); vm = (x.margin - x.spread_line).abs().mean()
    rows.append({"test": "season", "window": str(s), "games": len(x), "flags": f"{w}-{l}", "model_miss": round(mm, 3), "line_miss": round(vm, 3)})
    L.append(f"| {s} | {len(x)} | {w}-{l} | {mm:.2f} | {vm:.2f} | {'yes' if mm < vm else 'no'} |")
rest = [f"{rec(d[d.season != s])[0]}-{rec(d[d.season != s])[1]}" for s in sorted(d.season.unique())]
L += ["", f"- Leave-one-season-out 4+ records (each season dropped in turn): {', '.join(rest)}. No single season carries the record if every one of these stays above break-even.", ""]
L.append("Reading: the line beats the model on the miss every season (it should; it is the market). The question the flag rests on is whether the model's disagreements with the line carry information, which the encompassing weight, the placebo and the bootstrap answer.")
(ROOT / "reports" / "legitimacy.md").write_text("\n".join(L) + "\n"); pd.DataFrame(rows).to_csv(ROOT / "reports" / "legitimacy.csv", index=False); print("\n".join(L))
