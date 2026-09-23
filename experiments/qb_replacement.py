"""The QB rating shrinks toward a flat replacement level of -0.05 EPA per dropback; that level was set by hand.
Rebuild the features with the level at -0.12, -0.08, -0.05 (today), -0.02 and 0.0 and score both windows.
Output reports/qb_replacement.csv."""
import pandas as pd
from nflmodel import ratings as R, model as M
from nflmodel.features import OUT
from experiments.common import both
tg = pd.read_parquet(OUT / "team_games.parquet"); games = pd.read_parquet(OUT / "games.parquet"); qb = pd.read_parquet(OUT / "qb_games.parquet")
rows = []
orig = R.QBRatings.__init__
import os, sys
LEVELS = [float(x) for x in os.environ["LEVELS"].split(",")] if os.environ.get("LEVELS") else [-0.12, -0.08, -0.05, -0.02, 0.0]
for lvl in LEVELS:
    def init(self, q, k, decay, prior_epa=lvl, _o=orig): _o(self, q, k, decay, prior_epa)
    R.QBRatings.__init__ = init
    f = M.with_trends(R.build_features(R.DEFAULT, tg=tg, games=games, qb=qb)); r = both(f)
    rows.append({"variant": f"replacement level {lvl:+.2f}", **{f"{k}_{w}": v for w, d in r.items() for k, v in d.items()}})
    print(lvl, {w: (r[w]["team_mae"], r[w]["margin_mae"], r[w]["ats5"]) for w in r}, flush=True)
R.QBRatings.__init__ = orig
out = "reports/qb_replacement.csv"
old = pd.read_csv(out) if os.path.exists(out) else pd.DataFrame()
new = pd.concat([old, pd.DataFrame(rows)], ignore_index=True).drop_duplicates("variant", keep="last")
new["lvl"] = new.variant.str.extract(r"([-+]\d\.\d+)").astype(float); new.sort_values("lvl").drop(columns="lvl").to_csv(out, index=False); print("DONE")
