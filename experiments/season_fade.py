"""A faster fade of last season (28 Sep 2026, Matt: New England 1-2 and rated 7th; is the model leaning on last season too
hard?). The rating's last-season games carry the multiplier `prior` (0.8 live) on top of the per-game decay (0.94 live).
Each variant rebuilds the ratings, prices every game 2015-2025 with the live pipeline (model.walk_forward, its own trees
cache so the live cache is untouched) and is scored on the three windows: margin, team-points and total misses, the
4+ flag record and the 3+ under record. Adopted only if better on every window. Writes reports/season_fade.csv.
Usage: python experiments/season_fade.py"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import numpy as np, pandas as pd
from nflmodel import model as M, ratings as R, backtest as B
from nflmodel.model import OUT
V = [("live: last season x0.8, decay 0.94", {}), ("last season x0.65", {"prior": 0.65}), ("last season x0.5", {"prior": 0.5}), ("last season x0.35", {"prior": 0.35}),
     ("last season x0.2", {"prior": 0.2}), ("last season x0.5, decay 0.92", {"prior": 0.5, "decay": 0.92}), ("last season x0.65, decay 0.90", {"prior": 0.65, "decay": 0.90}),
     ("last season x1.0 (slower)", {"prior": 1.0})]
W = {"2015-18": (2015, 2018), "2019-22": (2019, 2022), "2023-25": (2023, 2025)}


def main():
    M.TREES_CACHE = Path("/tmp/claude-0/-home-user/c1e0d18e-681a-50ba-b0bb-6c809c2e3dee/scratchpad/tease/trees_cache_fade.parquet"); M._TC = {"df": None, "used": set(), "new": []}
    tg = pd.read_parquet(OUT / "team_games.parquet"); games = pd.read_parquet(OUT / "games.parquet"); qb = pd.read_parquet(OUT / "qb_games.parquet")
    rows = []
    for lab, chg in V:
        M._TC = {"df": None, "used": set(), "new": []}
        f = M.with_trends(R.build_features({**R.DEFAULT, **chg}, tg=tg, games=games, qb=qb))
        d = B.join(M.walk_forward(f, range(2015, 2026)), games); d = d[d.game_type == "REG"]
        r = {"variant": lab}
        for w, (a, b) in W.items():
            x = d[d.season.between(a, b)]
            r[f"margin_{w}"] = round(float(x.margin_err.abs().mean()), 4); r[f"team_{w}"] = round(float(pd.concat([x.home_err.abs(), x.away_err.abs()]).mean()), 4); r[f"total_{w}"] = round(float(x.total_err.abs().mean()), 4)
            y = x[x.spread_line.notna() & (x.week <= 17)]; e = y.spread_edge; k = e.abs() >= 4; c = (y.result - y.spread_line)[k] * np.sign(e[k]); r[f"4+_{w}"] = f"{int((c > 0).sum())}-{int((c < 0).sum())}"
            # the early weeks alone (1 to 4), where last season carries most of the rating
            xe = x[x.week <= 4]; r[f"margin_w1-4_{w}"] = round(float(xe.margin_err.abs().mean()), 4)
            z = x[x.total_line.notna() & (x.week <= 17)]; u = z[(z.model_total - z.total_line) <= -3]; r[f"u3_{w}"] = f"{int((u.total < u.total_line).sum())}-{int((u.total > u.total_line).sum())}"
        print(r, flush=True); rows.append(r)
        pd.DataFrame(rows).to_csv("reports/season_fade.csv", index=False)
    print("DONE", flush=True)


if __name__ == "__main__":
    main()
