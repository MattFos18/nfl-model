"""Weekly picks table: every game with the model's score, line, edge, probabilities and bet flag.

Usage: python -m nflmodel.picks --season 2026 --week 4 [--baseline]
Writes reports/picks_<season>_wk<week>.md and .csv.
"""
from __future__ import annotations
import argparse
import numpy as np, pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT, REP = ROOT / "data" / "processed", ROOT / "reports"
SPREAD_EDGE, TOTAL_EDGE = 4.0, None   # 23 Sep 2026: 4 replaced 5 (won every season 2019 to 2025 on the twenty-input model, reports/threshold_sweep.csv)  # spread: the ROI-best threshold that holds in both backtest windows. Totals: no threshold does (22 Sep 2026 sweep), so no total flags


def fair_ml(p):
    return np.where(p >= 0.5, -100 * p / (1 - p), 100 * (1 - p) / p)


def table(season: int, week: int, spread_edge=SPREAD_EDGE, total_edge=TOTAL_EDGE) -> pd.DataFrame:
    pred = pd.read_parquet(OUT / "pred_v3.parquet")
    games = pd.read_parquet(OUT / "games.parquet")
    base = pd.read_parquet(OUT / "pred_baseline.parquet") if (OUT / "pred_baseline.parquet").exists() else None
    p = pred[(pred.season == season) & (pred.week == week)].copy()
    g = games.set_index("game_id")
    p["gameday"] = p.game_id.map(g.gameday)
    p["spread_line"] = p.game_id.map(g.spread_line)
    p["total_line"] = p.game_id.map(g.total_line)
    p["home_score"] = p.game_id.map(g.home_score)
    p["away_score"] = p.game_id.map(g.away_score)
    p["spread_edge"] = p.model_spread - p.spread_line
    p["total_edge"] = p.model_total - p.total_line
    if base is not None:
        b = base.set_index("game_id")
        p["old_home"] = p.game_id.map(b.home_exp)
        p["old_away"] = p.game_id.map(b.away_exp)

    def bet(r):
        out = []
        if r.week >= 18:
            return ""   # final week: starters rest and the line knows it before the ratings do (7-11 on flags 2019 to 2025)
        if pd.notna(r.spread_line) and abs(r.spread_edge) >= spread_edge:
            side = r.home_team if r.spread_edge > 0 else r.away_team
            line = -r.spread_line if r.spread_edge > 0 else r.spread_line
            out.append(f"{side} {line:+g}")
        if total_edge is not None and pd.notna(r.total_line) and abs(r.total_edge) >= total_edge:
            out.append(("Over " if r.total_edge > 0 else "Under ") + f"{r.total_line:g}")
        return ", ".join(out) if out else ""
    p["bet"] = p.apply(bet, axis=1)
    # calibrated cover and over odds: what edges of this size have actually converted to, fitted on every graded
    # backtest game before this season (the model's own cover odds run about 10 points hot: the line carries
    # information the model does not)
    cal_s, cal_t = calibration(pred, games, season)
    p["p_cover_cal_home"] = [cal_p(cal_s, e) if e > 0 else 1 - cal_p(cal_s, e) for e in p.spread_edge.fillna(0)]
    p["p_over_cal"] = [cal_p(cal_t, e) if e > 0 else 1 - cal_p(cal_t, e) for e in p.total_edge.fillna(0)]
    p.loc[p.spread_line.isna(), "p_cover_cal_home"] = np.nan; p.loc[p.total_line.isna(), "p_over_cal"] = np.nan
    # the best available number for the model's side across the books in the latest line snapshot
    from . import lines as LN
    best = [best_number(LN.history(r.game_id), r) for r in p.itertuples()]
    p["best_line"] = [b[0] for b in best]; p["best_book"] = [b[1] for b in best]
    p["spread_edge_best"] = [(r.model_spread - b[2]) if b[2] is not None else np.nan for r, b in zip(p.itertuples(), best)]
    # a flagged spread is bet at the best available number (the flag itself is decided on the consensus line)
    def at_best(r):
        if not r.bet or r.best_line is None or pd.isna(r.best_line):
            return r.bet
        parts = []
        for b in r.bet.split(", "):
            if b.startswith(("Over", "Under")):
                parts.append(b)
            else:
                parts.append(f"{b.split()[0]} {r.best_line:+g}")
        return ", ".join(parts)
    p["bet"] = p.apply(at_best, axis=1)
    # stake on a flagged spread: quarter Kelly from the calibrated cover odds for the model's side, at the best book's
    # price when it is logged, otherwise -110
    p["bet_p"] = [(pc if e > 0 else 1 - pc) if (b and pd.notna(pc)) else np.nan for b, e, pc in zip(p.bet, p.spread_edge.fillna(0), p.p_cover_cal_home)]
    p["bet_odds"] = [(b[3] if b[3] is not None else -110.0) if bet else np.nan for bet, b in zip(p.bet, best)]
    p["stake_pct"] = [kelly_stake(pw, od) if pd.notna(pw) else np.nan for pw, od in zip(p.bet_p, p.bet_odds)]
    return p.sort_values("gameday")


def calibration(pred: pd.DataFrame, games: pd.DataFrame, season: int):
    """Logistic fit of 'the model's side covered' on |edge| (capped at 7), regular season, seasons before `season`,
    for spreads and for totals. Returns (intercept, slope) pairs."""
    from sklearn.linear_model import LogisticRegression
    g = games.set_index("game_id")
    d = pred[(pred.game_type == "REG") & (pred.season < season) & (pred.season >= 2019)].copy()
    d["hs"] = d.game_id.map(g.home_score); d["as_"] = d.game_id.map(g.away_score); d["sl"] = d.game_id.map(g.spread_line); d["tl"] = d.game_id.map(g.total_line)
    d = d[d.hs.notna()]
    out = []
    for edge, res in [(d.model_spread - d.sl, np.sign(d.hs - d.as_ - d.sl)), (d.model_total - d.tl, np.sign(d.hs + d.as_ - d.tl))]:
        ok = edge.notna() & (res != 0) & res.notna()
        won = (np.sign(edge[ok]) == res[ok]).astype(int)
        x = np.minimum(np.abs(edge[ok].values), 7.0)[:, None]
        if len(won) < 200 or won.nunique() < 2:
            out.append((0.0, 0.0)); continue
        m = LogisticRegression(C=10.0).fit(x, won)
        out.append((float(m.intercept_[0]), float(m.coef_[0][0])))
    return out[0], out[1]


def cal_p(cal, edge):
    a, b = cal
    return float(1.0 / (1.0 + np.exp(-(a + b * min(abs(float(edge)), 7.0)))))


def best_number(hist: pd.DataFrame, r):
    """(line for the model's side, book, home_spread used) from the latest snapshot; None when there is no log."""
    if hist is None or len(hist) == 0 or pd.isna(r.spread_line):
        return (None, None, None, None)
    last = hist[hist.ts == hist.ts.max()]; last = last[last.home_spread.notna()]
    if len(last) == 0:
        return (None, None, None, None)
    home_side = r.spread_edge > 0
    pick = last.loc[last.home_spread.idxmin()] if home_side else last.loc[last.home_spread.idxmax()]
    hs = float(pick.home_spread)
    line = -hs if home_side else hs
    book = str(pick.source).replace("oddsapi:", "").replace("espn:", "")
    odds = pick.get("spread_odds_home" if home_side else "spread_odds_away", np.nan)
    return (line, book, hs, float(odds) if pd.notna(odds) else None)


def kelly_stake(p_win: float, odds: float = -110.0, fraction: float = 0.25) -> float:
    """Share of bankroll to stake at American odds, as a percentage: the Kelly criterion times a fraction (a quarter
    by default; full Kelly assumes the cover odds are exact, and calibrated odds are an estimate). 0 when the odds
    do not pay enough for the edge."""
    b = 100.0 / abs(odds) if odds < 0 else odds / 100.0
    k = (p_win * b - (1.0 - p_win)) / b
    return round(max(0.0, k) * fraction * 100.0, 2)


def log_run(p: pd.DataFrame, run_at: str | None = None) -> pd.DataFrame:
    """Append this run's numbers for every game of the week to data/runs/pred_history.csv, so the page can show how
    the model's line moved from run to run (Tuesday to Saturday) beside how the market moved."""
    run_at = run_at or pd.Timestamp.now("UTC").strftime("%Y-%m-%d %H:%M UTC")
    RUNS = OUT.parent / "runs"; RUNS.mkdir(parents=True, exist_ok=True)
    cols = ["season", "week", "game_id", "model_spread", "model_total", "spread_line", "total_line", "bet"]
    rows = p[cols].copy(); rows.insert(0, "run_at", run_at)
    rows = rows[p.home_score.isna().values] if "home_score" in p.columns else rows   # only games not yet played
    f = RUNS / "pred_history.csv"
    rows.round(3).to_csv(f, mode="a", header=not f.exists(), index=False)
    return rows


def markdown(p: pd.DataFrame, season: int, week: int) -> str:
    rows = []
    for r in p.itertuples():
        our_line = f"{r.home_team} {-r.model_spread:+.1f} / {r.model_total:.1f}"
        vegas = f"{r.home_team} {-r.spread_line:+g} / {r.total_line:g}" if pd.notna(r.spread_line) else "no line yet"
        edge = f"{r.spread_edge:+.1f} / {r.total_edge:+.1f}" if pd.notna(r.spread_line) else ""
        cover = f"{r.home_team} {r.p_cover_home:.0%} / {r.away_team} {1 - r.p_cover_home:.0%}" if pd.notna(r.p_cover_home) else ""
        over = f"Over {r.p_over:.0%} / Under {1 - r.p_over:.0%}" if pd.notna(r.p_over) else ""
        old = f"{r.old_away:.1f}-{r.old_home:.1f}" if "old_home" in p.columns and pd.notna(r.old_home) else ""
        rows.append({"Game": f"{r.away_team} @ {r.home_team}", "Date": r.gameday,
                     "Our score": f"{r.away_team} {r.away_exp:.1f}, {r.home_team} {r.home_exp:.1f}",
                     "Old model": old, "Our line": our_line, "Vegas": vegas, "Edge (spread / total)": edge,
                     "Win": f"{r.home_team} {r.p_home:.0%} / {r.away_team} {1 - r.p_home:.0%}", "Cover the spread": cover, "Total": over, "Flag": r.bet,
                     "Stake": f"{r.stake_pct:g}% at {r.bet_odds:+g}" if "stake_pct" in p.columns and pd.notna(r.stake_pct) else ""})
    df = pd.DataFrame(rows)
    hdr = [f"# Week {week}, {season}: model picks", "",
           "Our line is home spread / total. Edge = model minus Vegas (spread: positive favours the home side; total: positive favours the over). "
           "Win, cover and total are the model's chances for each side at the current line; 52.4% is break-even at -110.",
           f"Bet flag: spread when the edge is {SPREAD_EDGE:g}+ points. On the current model that cut won in every season from 2019 to 2025 "
           "(weeks 1 to 17: 90-67 on the tuning window, 47-30 held out), at twice the volume of the old 5-point cut and the same rate. Totals are not flagged: no total "
           "threshold wins in both windows. No flags in Week 18, where resting starters make the line smarter than the ratings. The full sweep is on the Results tab of the page. "
           "Stake is a quarter of the Kelly fraction from the calibrated cover odds at the book's price, as a share of the bankroll.", ""]
    return "\n".join(hdr + [df.to_markdown(index=False), ""])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", type=int, default=2026)
    ap.add_argument("--week", type=int, required=True)
    a = ap.parse_args()
    p = table(a.season, a.week)
    REP.mkdir(exist_ok=True)
    p.to_csv(REP / f"picks_{a.season}_wk{a.week}.csv", index=False)
    log_run(p)
    md = markdown(p, a.season, a.week)
    (REP / f"picks_{a.season}_wk{a.week}.md").write_text(md)
    print(md)
