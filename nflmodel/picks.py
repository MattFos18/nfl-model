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
SPREAD_EDGE, TOTAL_EDGE = 5.0, None  # spread: the ROI-best threshold that holds in both backtest windows. Totals: no threshold does (22 Sep 2026 sweep), so no total flags


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
    return p.sort_values("gameday")


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
                     "Win": f"{r.home_team} {r.p_home:.0%} / {r.away_team} {1 - r.p_home:.0%}", "Cover the spread": cover, "Total": over, "Flag": r.bet})
    df = pd.DataFrame(rows)
    hdr = [f"# Week {week}, {season}: model picks", "",
           "Our line is home spread / total. Edge = model minus Vegas (spread: positive favours the home side; total: positive favours the over). "
           "Win, cover and total are the model's chances for each side at the current line; 52.4% is break-even at -110.",
           f"Bet flag: spread when the edge is {SPREAD_EDGE:g}+ points. That is the threshold with the best return that held in both backtest windows "
           "(2019 to 2022 and 2023 to 2025), on small samples: 116 spread bets at 5+ went 68-48. Totals are not flagged: no total threshold won in both windows "
           "(the 6+ rule went 27-26). No flags in Week 18, where resting starters make the line smarter than the ratings. The full sweep is on the History tab of the data room.", ""]
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
