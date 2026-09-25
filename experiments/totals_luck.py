"""Is the totals flag skill or luck, and why only unders (25 Sep 2026, Matt)? On the live walk-forward prices
(pred_v3, 2015-2025 regular season weeks 1 to 17, pushes out): blind unders by window; the under rate by decile of the
model's edge; the correlation of the edge with (actual - line); a shuffle test (the model's chances permuted within each
season, 5,000 times) of the 55% rule, and of the best of eight cuts; the rule's lift over blind unders by season.
Writes reports/totals_luck.csv (by season) and prints the rest."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import numpy as np, pandas as pd
from nflmodel import backtest as B
from nflmodel.model import OUT


def main():
    d = B.join(pd.read_parquet(OUT / "pred_v3.parquet"))
    d = d[(d.game_type == "REG") & d.total_line.notna() & (d.week <= 17) & (d.season <= 2025) & (d.total != d.total_line)].copy()
    d["edge"] = d.model_total - d.total_line; d["res"] = d.total - d.total_line; d["under"] = (d.res < 0).astype(int); d["pu"] = 1 - d.p_over_emp; d["rule"] = d.pu >= 0.55
    print(d.assign(bin=pd.qcut(d.edge, 10, labels=False)).groupby("bin").agg(edge=("edge", "mean"), under_rate=("under", "mean")).round(3).to_string())
    for a, b in ((2015, 2018), (2019, 2022), (2023, 2025)):
        x = d[d.season.between(a, b)]; print(f"{a}-{b}: blind unders {x.under.mean():.1%}, corr(edge, actual - line) {np.corrcoef(x.edge, x.res)[0, 1]:+.3f}")
    rng = np.random.default_rng(0); cuts = [0.52, 0.53, 0.54, 0.55, 0.56, 0.57, 0.58, 0.6]; one, best = [], []
    for _ in range(5000):
        pu = d.groupby("season").pu.transform(lambda s: rng.permutation(s.values))
        one.append(d.under[pu >= 0.55].mean()); best.append(max(d.under[pu >= c].mean() for c in cuts))
    o1, ob = d.under[d.rule].mean(), max(d.under[d.pu >= c].mean() for c in cuts)
    print(f"55% rule {o1:.2%}: shuffled p = {np.mean(np.array(one) >= o1):.4f}; best of eight cuts {ob:.2%}: shuffled p = {np.mean(np.array(best) >= ob):.4f}")
    s = d.groupby("season").apply(lambda x: pd.Series({"blind_under": x.under.mean(), "rule_under": x.under[x.rule].mean(), "rule_bets": int(x.rule.sum())}))
    s["lift"] = s.rule_under - s.blind_under; s.round(3).to_csv(Path(__file__).resolve().parent.parent / "reports" / "totals_luck.csv"); print(s.round(3).to_string())


if __name__ == "__main__":
    main()
