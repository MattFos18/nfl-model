"""Recency-weighted refit: the regression is refit every week on every game since 2013 with equal weight, so a
coefficient like home field is an average over thirteen seasons even though home field has drifted. Weight each
training game by how many seasons old it is (0.95, 0.9, 0.8, 0.7 per season). Output reports/recency.csv."""
import numpy as np, pandas as pd
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from nflmodel import model as M
from nflmodel.model import OUT
from experiments.common import both
f = M.with_trends(pd.read_parquet(OUT / "features_asof.parquet"))
orig = M.fit_points
def make(decay):
    def fit(train, alpha=10.0):
        w = decay ** (train.season.max() - train.season.values)
        m = make_pipeline(StandardScaler(), Ridge(alpha=alpha)); m.fit(train[M.FEATS].values, train.pf.values, ridge__sample_weight=w); return m
    return fit
rows = []
for name, d in [("equal weight (current)", None), ("0.95 per season", 0.95), ("0.9 per season", 0.9), ("0.8 per season", 0.8), ("0.7 per season", 0.7)]:
    M.fit_points = orig if d is None else make(d); r = both(f); M.fit_points = orig
    rows.append({"variant": name, **{f"{k}_{w}": v for w, dd in r.items() for k, v in dd.items()}}); print(name, {w: (r[w]["team_mae"], r[w]["margin_mae"], r[w]["ats5"]) for w in r}, flush=True)
pd.DataFrame(rows).to_csv("reports/recency.csv", index=False); print("DONE")
