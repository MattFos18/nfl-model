"""Season simulation backtest (23 Sep 2026): how good are the win totals, division, playoff and Super Bowl odds when
made as of several weeks of every season 2019 to 2025, and do two knobs help on both windows.

As of week w the simulation sees the games before w (real scores) and the game model's ratings and fit as of w; the
games from w on are drawn (the week-w games from the model's own predictions, later ones from its equation on the
as-of ratings). Scored against what happened: mean absolute error of expected wins (beside the pace baseline, current
wins plus half the games left), Brier score of the division odds (beside the current leader and a flat quarter), Brier
of the playoff odds (beside the flat share of the field), log loss of the Super Bowl and conference odds (beside flat
1/32 and 1/16), and the champion's rank in the Super Bowl odds. Knobs: future-game margins shrunk toward zero
(SHRINK), and the residual scale widened (SIGMA_MULT). A knob is adopted only when it lowers the wins error, the
division Brier and the playoff Brier on both windows (2019-22, 2023-25), averaged over the as-of weeks.

Output: reports/season_backtest.csv, one row per variant x season x as-of week, plus window means (season = "mean").
"""
from __future__ import annotations
import sys, time, itertools
import numpy as np, pandas as pd
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from nflmodel import season as SE

OUT, REP = SE.OUT, SE.REP
WEEKS = [1, 5, 9, 13, 17]
SEASONS = list(range(2019, 2026))
WINDOW = {s: "2019-22" if s <= 2022 else "2023-25" for s in SEASONS}
VARIANTS = [(sh, sm) for sh in (0.0, 0.1, 0.2, 0.3) for sm in (1.0, 1.15)]
N_SIMS = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
METRICS = ["wins_mae", "pace_mae", "div_brier", "div_brier_leader", "div_brier_flat", "div_ll", "div_ll_flat", "div_hit", "po_brier", "po_brier_flat", "sb_ll", "sb_ll_flat", "conf_ll", "conf_ll_flat", "champ_rank"]


def main():
    games = pd.read_parquet(OUT / "games.parquet"); pred = pd.read_parquet(OUT / "pred_v3.parquet")
    f = SE._frame()
    rows = []; t0 = time.time()
    for s in SEASONS:
        act = SE.actuals(games, s)
        if act is None:
            print("no actuals for", s); continue
        for w in WEEKS:
            P = SE.profiles(f, s, w); fit = SE.fit_asof(pred, s, w)
            for sh, sm in VARIANTS:
                sim = SE.simulate(s, w, games, P, fit, pred, n_sims=N_SIMS, shrink=sh, sigma_mult=sm, seed=s * 100 + w)
                sc = SE.score(sim, act)
                rows.append({"variant": f"shrink{sh:g}_sig{sm:g}", "shrink": sh, "sigma_mult": sm, "season": s, "window": WINDOW[s], "asof_week": w, "games_left": sim["games_left"], **sc})
            print(f"{s} week {w} done ({time.time() - t0:.0f}s)", flush=True)
    d = pd.DataFrame(rows)
    means = d.groupby(["variant", "shrink", "sigma_mult", "window"])[METRICS].mean().reset_index()
    means["season"] = "mean"; means["asof_week"] = "all"; means["games_left"] = np.nan
    by_week = d.groupby(["variant", "shrink", "sigma_mult", "window", "asof_week"])[METRICS].mean().reset_index()
    by_week["season"] = "mean"; by_week["games_left"] = np.nan
    out = pd.concat([d, by_week, means], ignore_index=True)
    # adoption: a variant must beat the base on wins error, division Brier and playoff Brier on both windows
    base = means[(means.shrink == 0.0) & (means.sigma_mult == 1.0)].set_index("window")
    verdict = {}
    for v, g in means.groupby("variant"):
        g = g.set_index("window")
        ok = all(g.loc[w, m] < base.loc[w, m] for w in ("2019-22", "2023-25") for m in ("wins_mae", "div_brier", "po_brier"))
        verdict[v] = "better on both windows" if ok else ("base" if v == "shrink0_sig1" else "not adopted")
    out["verdict"] = out.variant.map(verdict)
    REP.mkdir(exist_ok=True); out.round(4).to_csv(REP / "season_backtest.csv", index=False)
    print(means.round(4).sort_values(["window", "wins_mae"]).to_string(index=False))
    print(verdict)


if __name__ == "__main__":
    main()
