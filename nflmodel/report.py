"""Assemble reports/backtest_v3.md: 3.0 against the closing line, tuned on 2019 to 2022,
judged on 2023 to 2025, with the market blend and the threshold sweep on the tuning window only.

Usage: python -m nflmodel.report
"""
from __future__ import annotations
import numpy as np, pandas as pd
from pathlib import Path
from . import backtest as bt

ROOT = Path(__file__).resolve().parent.parent
OUT, REP = ROOT / "data" / "processed", ROOT / "reports"
TUNE, TEST = range(2019, 2023), range(2023, 2026)


def compare_points(new: pd.DataFrame, seasons) -> pd.DataFrame:
    n = new[new.season.isin(seasons) & (new.game_type == "REG") & new.spread_line.notna()]
    pn = bt.points_miss(n).set_index("target")
    return pd.DataFrame({"3.0": pn.model_mae, "Vegas close": pn.vegas_mae, "games": pn.n}).round(2)


def market_blend(new: pd.DataFrame):
    """pred = a * model + (1-a) * line. Fit a on the tuning window by margin MAE, report both windows."""
    d = new[new.game_type == "REG"]
    rows = []
    best_a, best = None, 9e9
    for a in np.round(np.arange(0, 1.01, 0.1), 2):
        t = d[d.season.isin(TUNE)]
        mae = np.abs(a * t.model_spread + (1 - a) * t.spread_line - t.result).mean()
        if mae < best:
            best, best_a = mae, a
        v = d[d.season.isin(TEST)]
        rows.append({"a (model share)": a, "margin MAE 2019-22": mae,
                     "margin MAE 2023-25": np.abs(a * v.model_spread + (1 - a) * v.spread_line - v.result).mean(),
                     "total MAE 2023-25": np.abs(a * v.model_total + (1 - a) * v.total_line - v.total).mean()})
    return best_a, pd.DataFrame(rows).round(3)


def threshold_table(d: pd.DataFrame, kind: str, edges=(1, 2, 3, 4, 5, 6, 7, 8)) -> pd.DataFrame:
    rows = []
    for e in edges:
        b = bt.grade_spread(d, e) if kind == "spread" else bt.grade_total(d, e)
        s = bt.summarize_bets(b).iloc[0]
        rows.append({"edge": e, **s.to_dict()})
    return pd.DataFrame(rows).round(3)


def clv_proxy(d: pd.DataFrame, edge: float) -> str:
    """Closing line value can't be measured yet (only closing lines are stored); say so once."""
    return ("Closing line value is not measurable in this backtest: nflverse stores closing lines only. "
            "It starts being logged from the first live week (open, midweek, close).")


def main():
    new = bt.join(pd.read_parquet(OUT / "pred_v3.parquet"))
    L = ["# NFL Model 3.0 backtest", "",
         "Walk-forward: every week is priced with only games played before it; the points regression is refit before every week on every "
         "played game since 2013. Rating parameters, ridge strength and bet thresholds were chosen on 2019 to 2022 only. "
         "2023 to 2025 is the held-out test the tuning never saw.", ""]
    L += ["## 1. Points miss (mean absolute error) against Vegas", "",
          "Tuning window 2019 to 2022:", "", compare_points(new, TUNE).to_markdown(), "",
          "Held-out 2023 to 2025:", "", compare_points(new, TEST).to_markdown(), "",
          "Held-out, Week 5 on:", "", compare_points(new[new.week > 4], TEST).to_markdown(), ""]
    for name, seasons in [("2019 to 2022 (tuning)", TUNE), ("2023 to 2025 (held out)", TEST)]:
        d = new[new.season.isin(seasons) & (new.game_type == "REG")]
        bs = bt.brier(d)
        L += [f"## 2. Win probability, {name}", "",
              f"Brier score (lower is better): 3.0 {bs['brier_model']:.4f}, market moneyline {bs['brier_market']:.4f}.", "",
              "3.0 calibration:", "", bt.calibration(d).round(3).to_markdown(), ""]
    d_t = new[new.season.isin(TUNE) & (new.game_type == "REG")]
    d_v = new[new.season.isin(TEST) & (new.game_type == "REG")]
    L += ["## 3. Spreads: threshold sweep on the tuning window (2019 to 2022)", "", threshold_table(d_t, "spread").to_markdown(index=False), "",
          "## 4. Totals: threshold sweep on the tuning window", "", threshold_table(d_t, "total").to_markdown(index=False), ""]
    # lock the sheet's thresholds unless the sweep shows a threshold with 100+ bets and better ROI
    st = threshold_table(d_t, "spread")
    tt = threshold_table(d_t, "total")
    s_ok = st[st.bets >= 100].sort_values("roi", ascending=False).iloc[0]
    t_ok = tt[tt.bets >= 100].sort_values("roi", ascending=False).iloc[0]
    L += [f"Best spread threshold with 100+ bets on the tuning window: {s_ok.edge:g} (ROI {s_ok.roi:+.3f}). "
          f"Best total threshold: {t_ok.edge:g} (ROI {t_ok.roi:+.3f}). The held-out results below use the live flags (5 / 6) and, separately, these.", ""]
    for label, se, te in [("live flags (5 / 6)", 5.0, 6.0), (f"tuned ({s_ok.edge:g} / {t_ok.edge:g})", float(s_ok.edge), float(t_ok.edge))]:
        sp, to = bt.grade_spread(d_v, se), bt.grade_total(d_v, te)
        L += [f"## 5. Held-out 2023 to 2025, {label}", "", "Spreads:", "", bt.summarize_bets(sp).round(3).to_markdown(), "",
              bt.summarize_bets(sp, "season").round(3).to_markdown(), "", "By edge size:", "", bt.edge_buckets(sp, edges=(se, se + 1, se + 2, se + 4, 99)).round(3).to_markdown(), "",
              "Totals:", "", bt.summarize_bets(to).round(3).to_markdown(), "", bt.summarize_bets(to, "season").round(3).to_markdown(), ""]
    a, mb = market_blend(new)
    L += ["## 6. Market plus model", "",
          f"Blend the model line with the closing line, pred = a x model + (1 - a) x line. Best a on 2019 to 2022 by margin MAE: {a:g}.", "",
          mb.to_markdown(index=False), "",
          "Bet selection is unchanged by blending (the edge is scaled, not re-ordered), so this only improves the score and the probabilities.", "",
          "## 7. Closing line value", "", clv_proxy(new, 3.0), ""]
    txt = "\n".join(L)
    (REP / "backtest_v3.md").write_text(txt)
    print(txt)


if __name__ == "__main__":
    main()
