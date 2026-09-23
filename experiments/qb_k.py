"""The QB shrinkage weight (150 dropbacks) was tuned at the old replacement level (-0.05). Re-check it at -0.12:
80, 150, 250 and 400 dropbacks, features rebuilt each time, both windows. Output reports/qb_k.csv."""
import pandas as pd
from nflmodel import ratings as R, model as M
from nflmodel.features import OUT
from experiments.common import both
tg = pd.read_parquet(OUT / "team_games.parquet"); games = pd.read_parquet(OUT / "games.parquet"); qb = pd.read_parquet(OUT / "qb_games.parquet")
rows = []
import os
KS = [float(x) for x in os.environ["KS"].split(",")] if os.environ.get("KS") else [80.0, 150.0, 250.0, 400.0]
for k in KS:
    p = dict(R.DEFAULT, qb_k=k)
    f = M.with_trends(R.build_features(p, tg=tg, games=games, qb=qb)); r = both(f)
    rows.append({"variant": f"qb_k {k:g}" + (" (today)" if k == 150 else ""), **{f"{kk}_{w}": v for w, d in r.items() for kk, v in d.items()}})
    print(k, {w: (r[w]["team_mae"], r[w]["margin_mae"], r[w]["ats5"]) for w in r}, flush=True)
out = "reports/qb_k.csv"
old = pd.read_csv(out) if os.path.exists(out) else pd.DataFrame()
new = pd.concat([old, pd.DataFrame(rows)], ignore_index=True).drop_duplicates("variant", keep="last")
new["k"] = new.variant.str.extract(r"qb_k (\d+)").astype(float); new.sort_values("k").drop(columns="k").to_csv(out, index=False); print("DONE")
