"""Round two: slower decay and more last-season weight looked better on both windows; push further and combine. Output reports/retune2.csv."""
import pandas as pd
from nflmodel import ratings as R, model as M
from nflmodel.model import OUT
from experiments.common import both
tg = pd.read_parquet(OUT / "team_games.parquet"); games = pd.read_parquet(OUT / "games.parquet"); qb = pd.read_parquet(OUT / "qb_games.parquet")
base = dict(R.DEFAULT); rows = []
for name, chg in [("current", {}), ("decay 0.94", {"decay": 0.94}), ("prior 0.8", {"prior": 0.8}), ("decay 0.92 + prior 0.65", {"decay": 0.92, "prior": 0.65}),
                  ("decay 0.94 + prior 0.8", {"decay": 0.94, "prior": 0.8}), ("decay 0.92 + prior 0.65 + alpha 10", {"decay": 0.92, "prior": 0.65, "alpha": 10.0}), ("decay 0.96 + prior 1.0", {"decay": 0.96, "prior": 1.0})]:
    p = {**base, **chg}; f = M.with_trends(R.build_features(p, tg=tg, games=games, qb=qb)); r = both(f)
    rows.append({"variant": name, **{f"{k}_{w}": v for w, d in r.items() for k, v in d.items()}}); print(name, {w: (r[w]["team_mae"], r[w]["margin_mae"], r[w]["ats5"]) for w in r}, flush=True)
pd.DataFrame(rows).to_csv("reports/retune2.csv", index=False); print("DONE")
