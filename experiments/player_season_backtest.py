"""Player season totals backtest (23 Sep 2026): season yards projected as of weeks 1, 5, 9 and 13 of 2019 to 2025 against
what the player finished with, beside two baselines (pace: his yards per team game so far over the whole schedule,
last season's total before anything is played; last season: his previous season's total), by kind and window.

Two constants per kind are fitted first on 2016 to 2018 as of the same weeks, on the error they are judged by (mean
absolute error of the season total): the availability share (the games his team has left that a player in his spot
goes on to play, a grid from 0.5 to 1.0) and a blend weight toward the pace baseline (0 to 1 in quarters; 1 would be
pace itself). The mean share of games actually played is written too (avail_mean_share rows) for the record. The
breakout flag (a top-24 receiver, top-24 rusher or top-12 passer projection at a per-game rate at least 1.25 x last
season's) is scored by how often it came true (the same test on what he finished with), beside the base rate among
every top-N projection.

The as-of rows are built once (availability 1, blend 0: the components) and cached in reports/player_season_rows.csv,
so the grid and the scoring are cheap; delete the cache to rebuild.

Output: reports/player_season_backtest.csv (rows: fit by kind; avail_mean_share by kind; mae by kind x window x as-of
week; breakout by kind x window x as-of week).
"""
from __future__ import annotations
import sys, time
import numpy as np, pandas as pd
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from nflmodel import player_season as PS
from nflmodel.positions import names_by_id

OUT, REP = PS.OUT, PS.REP
WEEKS = [1, 5, 9, 13]
FIT_SEASONS, TEST_SEASONS = [2016, 2017, 2018], list(range(2019, 2026))
WINDOW = {s: "2019-22" if s <= 2022 else "2023-25" for s in TEST_SEASONS}
AVAIL_GRID = np.round(np.arange(0.3, 1.0001, 0.025), 3)
BLEND_GRID = [0.0, 0.25, 0.5, 0.75, 1.0]
CACHE = REP / "player_season_rows.csv"
TOPW = PS.TOPW   # the top of each list by projection, for the accuracy the page leads with (one source: nflmodel/player_season.py)


def rows_for(d, games, names, season, week):
    p = PS.project(d, names, games, season, week, mode="asof", avail={"rec": 1.0, "rush": 1.0, "pass": 1.0})
    act = PS.season_actuals(d, season).set_index(["kind", "player_id"])
    key = list(zip(p.kind, p.player_id))
    p["actual_yards"] = [float(act.yards.get(k, 0.0)) if k in act.index else 0.0 for k in key]
    p["actual_td"] = [float(act.td.get(k, 0.0)) if k in act.index else 0.0 for k in key]
    p["actual_games"] = [int(act.games.get(k, 0)) if k in act.index else 0 for k in key]
    p["games_left_played"] = (p.actual_games - p.games_so_far).clip(lower=0)
    p["actual_rank"] = p.groupby("kind").actual_yards.rank(ascending=False, method="first").astype(int)
    p["actual_pg"] = p.actual_yards / p.actual_games.clip(lower=1)
    return p


def build_rows() -> pd.DataFrame:
    t0 = time.time()
    games = pd.read_parquet(OUT / "games.parquet")
    from nflmodel.props import official
    d = official(pd.read_parquet(OUT / "scheme_plays.parquet"))
    names = names_by_id(range(2014, 2027))
    rows = []
    for s in FIT_SEASONS + TEST_SEASONS:
        for w in WEEKS:
            if s == 2016 and w == 1:     # no charted season before 2016: the first profiles come in-season
                continue
            p = rows_for(d, games, names, s, w); rows.append(p)
            print(f"{s} week {w}: {len(p)} players ({time.time() - t0:.0f}s)", flush=True)
    R = pd.concat(rows, ignore_index=True)
    R.round(3).to_csv(CACHE, index=False)
    return R


def evaluate(R: pd.DataFrame, avail: dict, blend: dict) -> pd.DataFrame:
    """Projected yards for every row under the constants: so far + per game x games left x avail, blended toward pace."""
    R = R.copy()
    a = R.kind.map(avail).astype(float); b = R.kind.map(blend).astype(float)
    ours = R.yards_so_far + R.yards_pg * R.team_games_left * a
    R["proj_yards"] = (1 - b) * ours + b * R.pace_yards
    R["proj_td"] = R.td_so_far + R.td_pg * R.team_games_left * a
    R["proj_pg"] = R.proj_yards / R.team_games.clip(lower=1)
    R["rank"] = R.groupby(["season", "week", "kind"]).proj_yards.rank(ascending=False, method="first").astype(int)
    R["breakout"] = (R["rank"] <= R.kind.map(PS.TOP_N)) & (R.proj_pg >= PS.BREAK_UP * R.prev_pg) & (R.prev_games > 0)
    R["err"] = (R.proj_yards - R.actual_yards).abs(); R["pace_err"] = (R.pace_yards - R.actual_yards).abs(); R["prev_err"] = (R.prev_yards - R.actual_yards).abs()
    R["bias"] = R.proj_yards - R.actual_yards
    R["rel"] = R.err / R.actual_yards.clip(lower=1)   # the miss as a share of what he finished with (24 Sep 2026: the page's accuracy %)
    return R


def main():
    R = pd.read_csv(CACHE) if CACHE.exists() else build_rows()
    R = R[R.team_games_left > 0]
    fit = R[R.season.isin(FIT_SEASONS)]; test = R[R.season.isin(TEST_SEASONS)].copy(); test["window"] = test.season.map(WINDOW)
    out = []
    # 1. fit on 2016 to 2018: availability and blend by kind, on the season-total error
    avail, blend = {}, {}
    for k in ("rec", "rush", "pass"):
        fk = fit[fit.kind == k]; best = None
        for a in AVAIL_GRID:
            for b in BLEND_GRID:
                e = evaluate(fk, {k: a}, {k: b}).err.mean()
                if best is None or e < best[0]:
                    best = (e, float(a), float(b))
        avail[k], blend[k] = best[1], best[2]
        share = float(fk.games_left_played.sum() / fk.team_games_left.sum())
        out.append({"row": "fit", "kind": k, "window": "2016-18", "asof_week": "all", "avail": best[1], "blend": best[2], "mae": best[0], "n": int(len(fk))})
        out.append({"row": "avail_mean_share", "kind": k, "window": "2016-18", "asof_week": "all", "value": round(share, 3)})
        print(f"fit {k}: availability {best[1]}, blend toward pace {best[2]}, error {best[0]:.1f} (mean share of games played {share:.3f})", flush=True)
    # 2. the test seasons under the fitted constants
    T = evaluate(test, avail, blend)
    for (k, w, wk), g in T.groupby(["kind", "window", "week"]):
        out.append({"row": "mae", "kind": k, "window": w, "asof_week": wk, "n": int(len(g)), "mae": g.err.mean(), "pace_mae": g.pace_err.mean(), "prev_mae": g.prev_err.mean(), "bias": g.bias.mean(), "within10": float((g.rel <= 0.10).mean()), "within20": float((g.rel <= 0.20).mean()), "within20_prev": float(((g.prev_yards - g.actual_yards).abs() / g.actual_yards.clip(lower=1) <= 0.20).mean()), "within20_top": float((g[g["rank"] <= TOPW[k]].rel <= 0.20).mean()), "n_top": int((g["rank"] <= TOPW[k]).sum())})
    for (k, w), g in T.groupby(["kind", "window"]):
        out.append({"row": "mae", "kind": k, "window": w, "asof_week": "all", "n": int(len(g)), "mae": g.err.mean(), "pace_mae": g.pace_err.mean(), "prev_mae": g.prev_err.mean(), "bias": g.bias.mean(), "within10": float((g.rel <= 0.10).mean()), "within20": float((g.rel <= 0.20).mean()), "within20_prev": float(((g.prev_yards - g.actual_yards).abs() / g.actual_yards.clip(lower=1) <= 0.20).mean()), "within20_top": float((g[g["rank"] <= TOPW[k]].rel <= 0.20).mean()), "n_top": int((g["rank"] <= TOPW[k]).sum())})
    # 3. breakouts: flagged as of the week; true when he finished at least BREAK_UP x last season per game and inside the top N
    T["hit"] = (T.actual_pg >= PS.BREAK_UP * T.prev_pg) & (T.actual_rank <= T.kind.map(PS.TOP_N)) & (T.prev_games > 0)
    top = T[T["rank"] <= T.kind.map(PS.TOP_N)]
    for (k, w, wk), g in top.groupby(["kind", "window", "week"]):
        fl = g[g.breakout]
        out.append({"row": "breakout", "kind": k, "window": w, "asof_week": wk, "n": int(len(fl)), "value": (float(fl.hit.mean()) if len(fl) else np.nan), "base_rate": float(g.hit.mean())})
    for (k, w), g in top.groupby(["kind", "window"]):
        fl = g[g.breakout]
        out.append({"row": "breakout", "kind": k, "window": w, "asof_week": "all", "n": int(len(fl)), "value": (float(fl.hit.mean()) if len(fl) else np.nan), "base_rate": float(g.hit.mean())})
    o = pd.DataFrame(out); o.round(4).to_csv(REP / "player_season_backtest.csv", index=False)
    print(o[(o.row == "mae") & (o.asof_week.astype(str) == "all")].round(1).to_string(index=False))
    print(o[(o.row == "breakout") & (o.asof_week.astype(str) == "all")].round(3).to_string(index=False))
    print("AVAIL =", avail, "BLEND =", blend)


if __name__ == "__main__":
    main()
