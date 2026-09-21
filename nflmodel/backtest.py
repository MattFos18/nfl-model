"""Grade a prediction table against results and closing lines.

A prediction table has one row per game with: game_id, away_exp, home_exp, p_home (home win probability),
model_spread (home minus away, positive = home favored, same sign as nflverse spread_line), model_total.
Optionally p_cover_home and p_over (from a fitted margin distribution) for calibration.

Reports: points miss (per team, margin, total) next to Vegas; ATS and totals record at the bet thresholds
with ROI at -110; results by season and by edge size; Brier score and calibration of win probability.
"""
from __future__ import annotations
import numpy as np, pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "processed"
VIG = 1.1  # risk 1.1 to win 1 at -110


def join(pred: pd.DataFrame, games: pd.DataFrame | None = None) -> pd.DataFrame:
    games = pd.read_parquet(OUT / "games.parquet") if games is None else games
    cols = ["game_id", "season", "week", "game_type", "away_team", "home_team", "away_score", "home_score", "result",
            "total", "spread_line", "total_line", "home_implied", "away_implied", "home_moneyline", "away_moneyline"]
    d = pred.drop(columns=[c for c in cols if c in pred.columns and c != "game_id"]).merge(games[cols], on="game_id")
    d = d[d.home_score.notna()].copy()
    d["margin_err"] = d.model_spread - d.result
    d["total_err"] = d.model_total - d.total
    d["home_err"] = d.home_exp - d.home_score
    d["away_err"] = d.away_exp - d.away_score
    d["v_margin_err"] = d.spread_line - d.result
    d["v_total_err"] = d.total_line - d.total
    d["v_home_err"] = d.home_implied - d.home_score
    d["v_away_err"] = d.away_implied - d.away_score
    d["spread_edge"] = d.model_spread - d.spread_line   # >0: model likes home more than the market
    d["total_edge"] = d.model_total - d.total_line
    d["home_win"] = (d.result > 0).astype(float)
    return d


def points_miss(d: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for name, m, v in [("team points", ["home_err", "away_err"], ["v_home_err", "v_away_err"]),
                       ("margin", ["margin_err"], ["v_margin_err"]), ("total", ["total_err"], ["v_total_err"])]:
        rows.append({"target": name, "model_mae": np.abs(d[m].values).mean(), "vegas_mae": np.abs(d[v].values).mean(),
                     "model_bias": d[m].values.mean(), "n": len(d)})
    return pd.DataFrame(rows)


def grade_spread(d: pd.DataFrame, edge: float) -> pd.DataFrame:
    """Bet the home side when spread_edge >= edge, the away side when <= -edge. result - spread_line > 0 = home covers."""
    b = d[d.spread_edge.abs() >= edge].copy()
    b["side"] = np.where(b.spread_edge > 0, "home", "away")
    cover = b.result - b.spread_line
    b["win"] = np.where(b.side == "home", cover > 0, cover < 0)
    b["push"] = cover == 0
    b["units"] = np.where(b.push, 0, np.where(b.win, 1.0, -VIG))
    return b


def grade_total(d: pd.DataFrame, edge: float) -> pd.DataFrame:
    b = d[d.total_edge.abs() >= edge].copy()
    b["side"] = np.where(b.total_edge > 0, "over", "under")
    diff = b.total - b.total_line
    b["win"] = np.where(b.side == "over", diff > 0, diff < 0)
    b["push"] = diff == 0
    b["units"] = np.where(b.push, 0, np.where(b.win, 1.0, -VIG))
    return b


def summarize_bets(b: pd.DataFrame, by=None) -> pd.DataFrame:
    def agg(x):
        w, l, p = int(x.win[~x.push].sum()), int((~x.win[~x.push]).sum()), int(x.push.sum())
        n = w + l
        return pd.Series({"bets": n, "wins": w, "losses": l, "pushes": p, "win_pct": w / n if n else np.nan,
                          "units": x.units.sum(), "roi": x.units.sum() / (n * VIG) if n else np.nan})
    if by is None:
        return agg(b).to_frame("all").T
    return b.groupby(by).apply(agg, include_groups=False)


def brier(d: pd.DataFrame, p="p_home") -> dict:
    valid = d[d[p].notna()]
    bs = ((valid[p] - valid.home_win) ** 2).mean()
    # market Brier from moneylines when available
    ml = valid[valid.home_moneyline.notna() & valid.away_moneyline.notna()]
    def imp(m):
        m = m.astype(float)
        return np.where(m < 0, -m / (-m + 100), 100 / (m + 100))
    ph, pa = imp(ml.home_moneyline), imp(ml.away_moneyline)
    p_mkt = ph / (ph + pa)
    bs_mkt = ((p_mkt - ml.home_win) ** 2).mean() if len(ml) else np.nan
    return {"brier_model": bs, "brier_market": bs_mkt, "n": len(valid)}


def calibration(d: pd.DataFrame, p="p_home", bins=(0, .3, .4, .5, .6, .7, 1.01)) -> pd.DataFrame:
    valid = d[d[p].notna()].copy()
    valid["bin"] = pd.cut(valid[p], bins, right=False)
    return valid.groupby("bin", observed=True).agg(n=(p, "size"), predicted=(p, "mean"), actual=("home_win", "mean"))


def edge_buckets(b: pd.DataFrame, col="spread_edge", edges=(3, 4, 5, 7, 10, 99)) -> pd.DataFrame:
    b = b.copy()
    b["bucket"] = pd.cut(b[col].abs(), [edges[0]] + list(edges[1:]), right=False)
    return summarize_bets(b, "bucket")


def report(pred: pd.DataFrame, name: str, spread_edge=3.0, total_edge=4.0, games=None) -> str:
    d = join(pred, games)
    d = d[d.game_type == "REG"]
    lines = [f"# {name}: backtest {int(d.season.min())} to {int(d.season.max())}", "",
             f"{len(d)} regular-season games, every week priced with only the games played before it.", ""]
    lines += ["## Points miss (mean absolute error), model vs the closing line", "",
              points_miss(d).round(2).to_markdown(index=False), ""]
    pm = points_miss(d[d.week > 4])
    lines += ["From Week 5 on:", "", pm.round(2).to_markdown(index=False), ""]
    bs = brier(d)
    lines += ["## Win probability", "", f"Brier score: model {bs['brier_model']:.4f}, market (moneyline) {bs['brier_market']:.4f} on {bs['n']} games.",
              "", calibration(d).round(3).to_markdown(), ""]
    sp = grade_spread(d, spread_edge)
    lines += [f"## Spreads, bet when the model differs from the line by {spread_edge:g}+ points", "",
              summarize_bets(sp).round(3).to_markdown(), "", "By season:", "", summarize_bets(sp, "season").round(3).to_markdown(), "",
              "By edge size:", "", edge_buckets(sp).round(3).to_markdown(), "",
              "By side:", "", summarize_bets(sp, "side").round(3).to_markdown(), ""]
    to = grade_total(d, total_edge)
    lines += [f"## Totals, bet when the model differs from the line by {total_edge:g}+ points", "",
              summarize_bets(to).round(3).to_markdown(), "", "By season:", "", summarize_bets(to, "season").round(3).to_markdown(), "",
              "By side:", "", summarize_bets(to, "side").round(3).to_markdown(), ""]
    lines += ["## Threshold sweep (spreads)", ""]
    rows = []
    for e in [0, 1, 2, 3, 4, 5, 6, 7]:
        s = summarize_bets(grade_spread(d, e)).iloc[0]
        rows.append({"edge": e, **s.to_dict()})
    lines += [pd.DataFrame(rows).round(3).to_markdown(index=False), "", "## Threshold sweep (totals)", ""]
    rows = []
    for e in [0, 1, 2, 3, 4, 5, 6, 7]:
        s = summarize_bets(grade_total(d, e)).iloc[0]
        rows.append({"edge": e, **s.to_dict()})
    lines += [pd.DataFrame(rows).round(3).to_markdown(index=False), ""]
    return "\n".join(lines)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("pred")
    ap.add_argument("--name", default="model")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    pred = pd.read_parquet(a.pred)
    txt = report(pred, a.name)
    if a.out:
        Path(a.out).write_text(txt)
    print(txt)
