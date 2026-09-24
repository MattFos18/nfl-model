"""Stake sizing backtest (23 Sep 2026): the flag's bets 2015 to 2025 (regular season, weeks 1 to 17, 4+ edge, at the
closing line and -110), staked four ways, per window:

  flat       one unit a bet
  kelly_q    a quarter of the Kelly fraction from the calibrated cover odds (the live rule: picks.kelly_stake)
  kelly_h    half Kelly
  kelly_f    full Kelly (for scale; nobody should bet it)

The calibrated cover odds are walk-forward: each season's logistic fit (picks.calibration's form, |edge| capped at
7) uses only the seasons before it, from 2015 (the live rule uses 2019 on; the backtest needs the earlier seasons
to have a fit for 2019). Bankroll starts at 100 each window; a week's bets are sized from the bankroll at the start
of the week. Reported: record, units at flat stakes, ROI, final bankroll, largest peak-to-trough drawdown, longest
losing streak, and the share of seasons that lost money at flat stakes. Also the chance of the record by luck: a
one-sided binomial p-value against the 52.4% a -110 bet needs to break even.

Output reports/sizing_backtest.csv (one row per window x staking), reports/sizing_seasons.csv (by season) and
reports/cover_calibration.csv (the calibrated cover odds on every game in bands against how often the side covered).
"""
from __future__ import annotations
import sys
import numpy as np, pandas as pd
from pathlib import Path
from scipy.stats import binom
from sklearn.linear_model import LogisticRegression
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from nflmodel import backtest as B, picks as P
from nflmodel.model import OUT, REP

BREAK_EVEN = 110 / 210
STAKES = {"flat": None, "kelly_q": 0.25, "kelly_h": 0.5, "kelly_f": 1.0}


def main():
    games = pd.read_parquet(OUT / "games.parquet"); pred = pd.read_parquet(OUT / "pred_v3.parquet")
    d = B.join(pred, games); d = d[(d.game_type == "REG") & d.spread_line.notna() & d.home_score.notna()].copy()
    d["edge"] = d.model_spread - d.spread_line; d["cm"] = d.home_score - d.away_score - d.spread_line
    d["won"] = np.where(d.cm == 0, np.nan, ((d.edge > 0) & (d.cm > 0)) | ((d.edge < 0) & (d.cm < 0)))
    # walk-forward calibration, fit per season on the seasons before it
    cal = {}
    for s in sorted(d.season.unique()):
        tr = d[(d.season < s) & d.won.notna()]
        if len(tr) < 200:
            continue
        x = np.minimum(tr.edge.abs().values, 7.0)[:, None]; m = LogisticRegression(C=10.0).fit(x, tr.won.astype(int).values)
        cal[s] = (float(m.intercept_[0]), float(m.coef_[0][0]))
    bets = d[P.rule_mask(d, P.SPREAD_EDGE)].copy()
    bets["p"] = [1 / (1 + np.exp(-(cal[s][0] + cal[s][1] * min(abs(e), 7.0)))) if s in cal else np.nan for s, e in zip(bets.season, bets.edge)]
    bets = bets[bets.p.notna()].sort_values(["season", "week", "game_id"])
    rows, seasons = [], []
    for w, (a, b) in {"2016-18": (2016, 2018), "2019-22": (2019, 2022), "2023-25": (2023, 2025), "2019-25": (2019, 2025)}.items():
        x = bets[bets.season.between(a, b)]
        for name, frac in STAKES.items():
            bank = 100.0; peak = 100.0; dd = 0.0; streak = 0; worst = 0; units = 0.0; staked = 0.0
            for (s, wk), g in x.groupby(["season", "week"], sort=True):
                start = bank
                for r in g.itertuples():
                    if frac is None:
                        stake = 1.0
                    else:
                        stake = start * P.kelly_stake(r.p, -110.0, frac) / 100.0
                    if pd.isna(r.won):
                        continue
                    pnl = stake * (100 / 110) if r.won else -stake
                    bank += pnl if frac is not None else 0.0
                    units += pnl if frac is None else 0.0; staked += stake
                    streak = 0 if r.won else streak + 1; worst = max(worst, streak)
                    if frac is None:
                        peak = max(peak, 100 + units); dd = max(dd, peak - (100 + units))
                    else:
                        peak = max(peak, bank); dd = max(dd, (peak - bank) / peak * 100)
            wi = int((x.won == True).sum()); lo = int((x.won == False).sum())  # noqa
            p_luck = float(binom.sf(wi - 1, wi + lo, BREAK_EVEN)) if wi + lo else np.nan
            rows.append({"window": w, "staking": name, "bets": wi + lo, "record": f"{wi}-{lo}", "win_pct": round(wi / max(wi + lo, 1), 4),
                         "units_flat": round(units, 2) if frac is None else np.nan, "roi_flat": round(units / max(staked, 1e-9), 4) if frac is None else np.nan,
                         "final_bankroll": round(bank, 1) if frac is not None else np.nan, "growth_pct": round(bank - 100, 1) if frac is not None else np.nan,
                         "max_drawdown": round(dd, 2), "drawdown_unit": "units" if frac is None else "% of peak", "longest_losing_streak": worst,
                         "p_value_vs_break_even": round(p_luck, 5)})
        for s, g in x.groupby("season"):
            if w != "2019-25" and w != "2016-18" or True:
                wi = int((g.won == True).sum()); lo = int((g.won == False).sum())  # noqa
                seasons.append({"window": w, "season": int(s), "record": f"{wi}-{lo}", "win_pct": round(wi / max(wi + lo, 1), 3), "units_flat": round(wi * 100 / 110 - lo, 2)})
    R = pd.DataFrame(rows); S = pd.DataFrame(seasons).drop_duplicates("season")
    losing = S.assign(lost=S.units_flat < 0)
    R["seasons_losing_flat"] = [f"{int(losing[losing.season.between(*{'2016-18': (2016, 2018), '2019-22': (2019, 2022), '2023-25': (2023, 2025), '2019-25': (2019, 2025)}[w])].lost.sum())} of {int(losing.season.between(*{'2016-18': (2016, 2018), '2019-22': (2019, 2022), '2023-25': (2023, 2025), '2019-25': (2019, 2025)}[w]).sum())}" for w in R.window]
    R.to_csv(REP / "sizing_backtest.csv", index=False); S.drop(columns="window").to_csv(REP / "sizing_seasons.csv", index=False)
    # reliability of the calibrated cover odds on every game with a line (not only the flags), walk-forward, per window:
    # in bands of the stated chance for the model's side, how often that side covered
    allg = d[d.won.notna()].copy()
    allg["p"] = [1 / (1 + np.exp(-(cal[s_][0] + cal[s_][1] * min(abs(e), 7.0)))) if s_ in cal else np.nan for s_, e in zip(allg.season, allg.edge)]
    allg = allg[allg.p.notna()]; cr = []
    for w, (a, b) in {"2019-22": (2019, 2022), "2023-25": (2023, 2025)}.items():
        x = allg[allg.season.between(a, b)]
        for lo, hi in ((0.0, 0.5), (0.5, 0.52), (0.52, 0.54), (0.54, 0.56), (0.56, 0.58), (0.58, 0.6), (0.6, 0.63), (0.63, 1.0)):
            bb = x[(x.p >= lo) & (x.p < hi)]
            if len(bb):
                cr.append({"window": w, "band_from": lo, "band_to": hi, "games": int(len(bb)), "said": round(float(bb.p.mean()), 4), "covered": round(float(bb.won.astype(float).mean()), 4)})
    pd.DataFrame(cr).to_csv(REP / "cover_calibration.csv", index=False); print(pd.DataFrame(cr).to_string(index=False))
    print(R.to_string(index=False)); print(S.drop(columns="window").to_string(index=False))


if __name__ == "__main__":
    main()
