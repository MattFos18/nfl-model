"""The sweep's finalists inside the live seven-model blend (25 Sep 2026): each rating setting that helped on every
window in experiments/sweep_all.py, alone and together, priced with model.walk_forward (the live pipeline) on
2015-2025. Writes reports/sweep_confirm.csv. Usage: python experiments/sweep_confirm.py <index> [<index> ...]"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import numpy as np, pandas as pd
from nflmodel import model as M, ratings as R, backtest as B
from nflmodel.model import OUT
V = [("live", {}), ("last season 0.65", {"prior": 0.65}), ("QB shrink 100", {"qb_k": 100.0}), ("QB fade per season 0.7", {"qb_season_fade": 0.7}),
     ("QB decay per game 0.97", {"qb_decay": 0.97}), ("last season 0.65 + QB shrink 100", {"prior": 0.65, "qb_k": 100.0}),
     ("last season 0.65 + QB shrink 100 + QB fade 0.7", {"prior": 0.65, "qb_k": 100.0, "qb_season_fade": 0.7})]
W = {"2015-18": (2015, 2018), "2019-22": (2019, 2022), "2023-25": (2023, 2025)}


def main(idx):
    tg = pd.read_parquet(OUT / "team_games.parquet"); games = pd.read_parquet(OUT / "games.parquet"); qb = pd.read_parquet(OUT / "qb_games.parquet")
    for i in idx:
        lab, chg = V[i]
        f = M.with_trends(R.build_features({**R.DEFAULT, **chg}, tg=tg, games=games, qb=qb))
        d = B.join(M.walk_forward(f, range(2015, 2026)), games); d = d[d.game_type == "REG"]
        r = {"variant": lab}
        for w, (a, b) in W.items():
            x = d[d.season.between(a, b)]
            r[f"margin_{w}"] = round(float(x.margin_err.abs().mean()), 4); r[f"team_{w}"] = round(float(pd.concat([x.home_err.abs(), x.away_err.abs()]).mean()), 4); r[f"total_{w}"] = round(float(x.total_err.abs().mean()), 4)
            y = x[x.spread_line.notna() & (x.week <= 17)]; e = y.spread_edge; k = e.abs() >= 4; c = (y.result - y.spread_line)[k] * np.sign(e[k]); r[f"4+_{w}"] = f"{int((c > 0).sum())}-{int((c < 0).sum())}"
            z = x[x.total_line.notna() & (x.week <= 17)]; u = z[(z.model_total - z.total_line) <= -3]; r[f"u3_{w}"] = f"{int((u.total < u.total_line).sum())}-{int((u.total > u.total_line).sum())}"
        print(r, flush=True)
        out = Path("reports/sweep_confirm.csv"); prev = pd.read_csv(out) if out.exists() else pd.DataFrame()
        pd.concat([prev[prev.variant != lab] if len(prev) else prev, pd.DataFrame([r])], ignore_index=True).to_csv(out, index=False)


if __name__ == "__main__":
    main([int(x) for x in sys.argv[1:]])
