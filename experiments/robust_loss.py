"""Robust loss for the points equation (23 Sep 2026): the model is judged by mean absolute error, and scores have
blowouts, so a fit that leans less on the tails might miss by less. Same twenty-two inputs, weekly refit, both
windows: ridge (today), Huber (epsilon 1.35 on standardized residuals, ridge-sized penalty), and least absolute
deviations (quantile regression at the median). Output reports/robust_loss.csv."""
import sys, time
import numpy as np, pandas as pd
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from sklearn.linear_model import Ridge, HuberRegressor, QuantileRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from nflmodel import model as M
from nflmodel.model import OUT, REP
from experiments.common import both

f = M.with_trends(pd.read_parquet(OUT / "features_asof.parquet"))
rows = []
def add(name, r, t0):
    rows.append({"model": name, **{f"{k}_{w}": v for w, d in r.items() for k, v in d.items()}}); print(name, {w: (r[w]["team_mae"], r[w]["margin_mae"], r[w]["ats4"]) for w in r}, f"{time.time() - t0:.0f}s", flush=True)
orig = M.fit_points
t0 = time.time(); add("ridge alpha 10 (today)", both(f), t0)
for eps in (1.35, 2.0):
    def fit_huber(train, alpha=10.0, eps=eps):
        m = make_pipeline(StandardScaler(), HuberRegressor(epsilon=eps, alpha=alpha / len(train), max_iter=500)); m.fit(train[M.FEATS].values, train.pf.values); return m
    M.fit_points = fit_huber; t0 = time.time(); add(f"huber epsilon {eps}", both(f), t0); M.fit_points = orig
def fit_lad(train, alpha=10.0):
    m = make_pipeline(StandardScaler(), QuantileRegressor(quantile=0.5, alpha=1e-4, solver="highs")); m.fit(train[M.FEATS].values, train.pf.values); return m
M.fit_points = fit_lad; t0 = time.time(); add("least absolute deviations (median regression)", both(f), t0); M.fit_points = orig
pd.DataFrame(rows).to_csv(REP / "robust_loss.csv", index=False); print(pd.DataFrame(rows).to_string(index=False))
