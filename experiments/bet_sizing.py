"""Bet sizing (3 Oct 2026, Matt: would sizing bets by bankroll or confidence increase return?). Report only.

Every live bet on the honest backtest (pred_v3), 2015-2025, regular season, weeks 1-17: the spread flag (|edge| 4+),
the totals flag (unders at a 55%+ raw chance) and the wind under (forecast 10+ mph); a game bet by both under rules
counts once. Graded at -110 at the closing line, pushes return the stake. Bankroll 100, bets in date order, same-day
bets sized from the bankroll at the start of the day:

  S1 flat 1 unit   S2 1% of bankroll   S3 2% of bankroll   S4 quarter Kelly (cap 3%)   S5 half Kelly (cap 3%)

Kelly chances are the calibrated ones the card shows, known before the game: spreads from the cover calibration fit on
the seasons before (from 2015, 200 games needed), unders 1 - p_over_cal (picks.over_calibrations). Stress test: 200
draws flipping wins to losses so the win rate is 2.5 points lower. Writes reports/bet_sizing.csv (one row per period
x strategy) and reports/bet_sizing_stress.csv. Pre-registration: reports/bet_sizing.md.
"""
from __future__ import annotations
import sys
import numpy as np, pandas as pd
from pathlib import Path
from sklearn.linear_model import LogisticRegression
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from nflmodel import backtest as B, picks as P
from nflmodel.model import OUT, REP

ODDS, WIN_PAY = -110.0, 100 / 110
CAP = 3.0   # % of bankroll a Kelly bet may stake
PERIODS = {"2015-25": (2015, 2025), "2015-18": (2015, 2018), "2019-22": (2019, 2022), "2023-25": (2023, 2025)}
STRATS = {"S1 flat 1 unit": ("flat", None), "S2 1% of bankroll": ("pct", 1.0), "S3 2% of bankroll": ("pct", 2.0),
          "S4 quarter Kelly": ("kelly", 0.25), "S5 half Kelly": ("kelly", 0.5)}
DRAWS, DROP, SEED = 200, 0.025, 2026


def bets() -> pd.DataFrame:
    """One row per bet: season, week, day, kickoff, kind, won (1/0, NaN push), p (calibrated chance for the bet's side)."""
    games = pd.read_parquet(OUT / "games.parquet"); pred = pd.read_parquet(OUT / "pred_v3.parquet")
    d = B.join(pred, games); d = d[(d.game_type == "REG") & d.season.between(2015, 2025)].copy()
    g = games.set_index("game_id"); d["day"] = d.game_id.map(g.gameday); d["ko"] = d.game_id.map(g.kickoff_et).astype(str)
    # spread: the cover calibration, walk-forward from 2015 (picks.calibration's form)
    sp = d[d.spread_line.notna()].copy(); sp["edge"] = sp.model_spread - sp.spread_line
    cm = sp.home_score - sp.away_score - sp.spread_line
    sp["won"] = np.where(cm == 0, np.nan, (((sp.edge > 0) & (cm > 0)) | ((sp.edge < 0) & (cm < 0))).astype(float))
    cal = {}
    for s in range(2015, 2026):
        tr = sp[(sp.season < s) & sp.won.notna() & (sp.edge != 0)]
        if len(tr) >= 200:
            m = LogisticRegression(C=10.0).fit(np.minimum(tr.edge.abs().values, P.CAL_CAP)[:, None], tr.won.astype(int).values)
            cal[s] = (float(m.intercept_[0]), float(m.coef_[0][0]))
    sb = sp[P.rule_mask(sp, P.SPREAD_EDGE)].copy()
    sb["p"] = [P.cal_p(cal[s], e) if s in cal else np.nan for s, e in zip(sb.season, sb.edge)]
    sb["kind"] = "spread"
    # unders: the totals flag or the wind under, once per game; chance 1 - p_over_cal on the fit in force that season
    tt = d[d.total_line.notna()].copy()
    m_flag = P.rule_mask(tt, P.TOTAL_SHADOW["prob"], "under_prob"); m_wind = P.rule_mask(tt, P.WIND_UNDER["mph"], "wind_under")
    ub = tt[m_flag | m_wind].copy()
    ub["kind"] = np.where(m_flag[m_flag | m_wind] & m_wind[m_flag | m_wind], "under (both)", np.where(m_flag[m_flag | m_wind], "under (totals flag)", "under (wind)"))
    co = P.over_calibrations(pred, games)
    ub["p"] = [1 - P.over_cal_p(co[int(s)], x) if pd.notna(x) and int(s) in co else np.nan for s, x in zip(ub.season, ub.p_over_emp)]
    tot = ub.home_score + ub.away_score - ub.total_line
    ub["won"] = np.where(tot == 0, np.nan, (tot < 0).astype(float))
    # cross-check against the live records (picks.record)
    for w, (a, b) in P.WINDOWS.items():
        x = d[d.season.between(a, b)]
        print(w, "flag", P.record(x, P.rule_mask(x, P.SPREAD_EDGE)), "totals flag", P.record(x, P.rule_mask(x, P.TOTAL_SHADOW["prob"], "under_prob"), "under_prob"),
              "wind", P.record(x, P.rule_mask(x, P.WIND_UNDER["mph"], "wind_under"), "wind_under"))
    cols = ["game_id", "season", "week", "day", "ko", "kind", "won", "p"]
    out = pd.concat([sb[cols], ub[cols]]).sort_values(["day", "ko", "game_id", "kind"]).reset_index(drop=True)
    return out


def stake_pct(kind: str, arg, p) -> float:
    if kind == "pct":
        return arg
    if pd.isna(p):
        return 0.0
    return min(P.kelly_stake(float(p), ODDS, arg), CAP)


def simulate(x: pd.DataFrame, won: np.ndarray, kind: str, arg) -> dict:
    bank, peak, dd, streak, worst = 100.0, 100.0, 0.0, 0, 0
    season_start, losing, zero = {}, 0, 0
    days = x.day.values; seasons = x.season.values; ps = x.p.values
    i, n = 0, len(x)
    while i < n:
        j = i
        while j < n and days[j] == days[i]:
            j += 1
        start = bank
        if seasons[i] not in season_start:
            season_start[seasons[i]] = start
        for k in range(i, j):
            st = 1.0 if kind == "flat" else start * stake_pct(kind, arg, ps[k]) / 100.0
            zero += st == 0
            w = won[k]
            if np.isnan(w):
                continue
            bank += st * WIN_PAY if w else -st
            if st > 0:
                streak = 0 if w else streak + 1; worst = max(worst, streak)
        peak = max(peak, bank); dd = max(dd, (peak - bank) / peak * 100)
        i = j
    order = sorted(season_start)
    for a, b in zip(order, order[1:] + [None]):
        e = season_start[b] if b is not None else bank
        losing += e < season_start[a]
    n_seasons = len(order)
    growth = (max(bank, 1e-9) / 100.0) ** (1 / max(n_seasons, 1)) - 1
    return {"end": bank, "growth": growth, "dd": dd, "streak": worst, "losing": losing, "seasons": n_seasons, "zero": zero}


def main():
    allb = bets()
    print(allb.groupby(["kind"]).agg(n=("won", "size"), wins=("won", "sum"), p_mean=("p", "mean")).to_string())
    # the bets Kelly stakes nothing on: no chance known, or a chance at or under break-even, and how they did
    off = allb.p.isna() | (allb.p <= P.break_even(ODDS))
    print("Kelly stakes:", int((~off).sum()), "bets, won", round(float(allb.won[~off].mean()), 4), "| no stake:", int(off.sum()),
          "bets (no chance known", int(allb.p.isna().sum()), "), won", round(float(allb.won[off].mean()), 4))
    print(allb[off].groupby("kind").size().to_string())
    rows, stress = [], []
    rng = np.random.default_rng(SEED)
    for per, (a, b) in PERIODS.items():
        x = allb[allb.season.between(a, b)].reset_index(drop=True)
        won = x.won.values.astype(float)
        wi, lo = int(np.nansum(won)), int((won == 0).sum())
        for name, (kind, arg) in STRATS.items():
            r = simulate(x, won, kind, arg)
            rows.append({"period": per, "strategy": name, "bets": len(x), "record": f"{wi}-{lo}", "win_pct": round(wi / (wi + lo), 4),
                         "ending_bankroll": round(r["end"], 1), "avg_yearly_growth_pct": round(100 * r["growth"], 2),
                         "worst_drawdown_pct": round(r["dd"], 1), "longest_losing_streak": r["streak"],
                         "seasons_losing": f"{r['losing']} of {r['seasons']}", "bets_staked_zero": r["zero"]})
        flips = int(round(DROP * (wi + lo))); win_idx = np.flatnonzero(won == 1)
        ends = {name: [] for name in STRATS}
        for _ in range(DRAWS):
            w2 = won.copy(); w2[rng.choice(win_idx, flips, replace=False)] = 0.0
            for name, (kind, arg) in STRATS.items():
                ends[name].append(simulate(x, w2, kind, arg)["end"])
        for name in STRATS:
            e = np.array(ends[name])
            stress.append({"period": per, "strategy": name, "win_pct_stressed": round((wi - flips) / (wi + lo), 4), "flips": flips, "draws": DRAWS,
                           "median_ending_bankroll": round(float(np.median(e)), 1), "p10_ending_bankroll": round(float(np.percentile(e, 10)), 1),
                           "share_below_100": round(float((e < 100).mean()), 3)})
    R, S = pd.DataFrame(rows), pd.DataFrame(stress)
    R.to_csv(REP / "bet_sizing.csv", index=False); S.to_csv(REP / "bet_sizing_stress.csv", index=False)
    pd.set_option("display.width", 250)
    print(R.to_string(index=False)); print(S.to_string(index=False))


if __name__ == "__main__":
    main()
