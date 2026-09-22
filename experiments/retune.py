"""The rating knobs, re-checked under the weekly refit with eighteen inputs: one knob at a time around the current
setting (decay per week, last season's weight, pull toward average, QB shrinkage and decay), features rebuilt for
each, scored on both windows. Output reports/retune.csv."""
import pandas as pd
from nflmodel import ratings as R, model as M
from nflmodel.model import OUT
from experiments.common import both
tg = pd.read_parquet(OUT / "team_games.parquet"); games = pd.read_parquet(OUT / "games.parquet"); qb = pd.read_parquet(OUT / "qb_games.parquet")
base = dict(R.DEFAULT)
variants = [("current", {})]
for k, vals in {"decay": [0.88, 0.92], "prior": [0.35, 0.65], "alpha": [10.0, 24.0], "qb_k": [90.0, 250.0], "qb_decay": [0.975, 0.992]}.items():
    for v in vals:
        variants.append((f"{k} {v}", {k: v}))
rows = []
for name, chg in variants:
    p = {**base, **chg}
    f = M.with_trends(R.build_features(p, tg=tg, games=games, qb=qb))
    r = both(f)
    rows.append({"variant": name, **{f"{k}_{w}": v for w, d in r.items() for k, v in d.items()}}); print(name, {w: (r[w]["team_mae"], r[w]["margin_mae"], r[w]["ats5"]) for w in r}, flush=True)
pd.DataFrame(rows).to_csv("reports/retune.csv", index=False); print("DONE")
