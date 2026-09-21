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
SPREAD_EDGE, TOTAL_EDGE = 5.0, 6.0  # ROI-best thresholds that hold in both backtest windows; see docs/how_it_works.md section 8


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
        if pd.notna(r.spread_line) and abs(r.spread_edge) >= spread_edge:
            side = r.home_team if r.spread_edge > 0 else r.away_team
            line = -r.spread_line if r.spread_edge > 0 else r.spread_line
            out.append(f"{side} {line:+g}")
        if pd.notna(r.total_line) and abs(r.total_edge) >= total_edge:
            out.append(("Over " if r.total_edge > 0 else "Under ") + f"{r.total_line:g}")
        return ", ".join(out) if out else ""
    p["bet"] = p.apply(bet, axis=1)
    return p.sort_values("gameday")


def markdown(p: pd.DataFrame, season: int, week: int) -> str:
    rows = []
    for r in p.itertuples():
        our_line = f"{r.home_team} {-r.model_spread:+.1f} / {r.model_total:.1f}"
        vegas = f"{r.home_team} {-r.spread_line:+g} / {r.total_line:g}" if pd.notna(r.spread_line) else "no line yet"
        edge = f"{r.spread_edge:+.1f} / {r.total_edge:+.1f}" if pd.notna(r.spread_line) else ""
        cover = f"{r.p_cover_home:.0%}" if pd.notna(r.p_cover_home) else ""
        over = f"{r.p_over:.0%}" if pd.notna(r.p_over) else ""
        old = f"{r.old_away:.1f}-{r.old_home:.1f}" if "old_home" in p.columns and pd.notna(r.old_home) else ""
        rows.append({"Game": f"{r.away_team} @ {r.home_team}", "Date": r.gameday,
                     "Our score": f"{r.away_team} {r.away_exp:.1f}, {r.home_team} {r.home_exp:.1f}",
                     "Old model": old, "Our line": our_line, "Vegas": vegas, "Edge (spread / total)": edge,
                     "Home win": f"{r.p_home:.0%}", "Home cover": cover, "Over": over, "Bet": r.bet})
    df = pd.DataFrame(rows)
    hdr = [f"# Week {week}, {season}: model picks", "",
           "Our line is home spread / total. Edge = model minus Vegas (spread: positive favours the home side; total: positive favours the over).",
           f"Bet flag: spread when the edge is {SPREAD_EDGE:g}+ points, total when {TOTAL_EDGE:g}+. These are the thresholds with the best ROI that held in both "
           "backtest windows (2019 to 2022 and 2023 to 2025), but the samples are small: 131 spread bets at 5+ went 54.2% (+3.5% ROI), 57 total bets at 6+ went 61.4%. "
           "Edges under those thresholds have lost money in every window. Full table in docs/how_it_works.md.", ""]
    return "\n".join(hdr + [df.to_markdown(index=False), ""])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", type=int, default=2026)
    ap.add_argument("--week", type=int, required=True)
    a = ap.parse_args()
    p = table(a.season, a.week)
    REP.mkdir(exist_ok=True)
    p.to_csv(REP / f"picks_{a.season}_wk{a.week}.csv", index=False)
    md = markdown(p, a.season, a.week)
    (REP / f"picks_{a.season}_wk{a.week}.md").write_text(md)
    print(md)
