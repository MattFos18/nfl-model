"""Is the equation itself saturated? Same 13 inputs: ridge alpha sweep, pairwise interactions and squares of the
ratings, and a gradient-boosted tree (nonlinear) on the same inputs, refit per season for speed and compared with
ridge refit the same way. Output reports/equation_checks.csv."""
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler, PolynomialFeatures
from sklearn.linear_model import Ridge
from nflmodel import model as M
from nflmodel.model import OUT
from experiments.common import both
f = M.with_trends(pd.read_parquet(OUT / "features_asof.parquet"))
rows = []
def add(name, r):
    rows.append({"model": name, **{f"{k}_{w}": v for w, d in r.items() for k, v in d.items()}}); print(name, {w: (r[w]["team_mae"], r[w]["ats5"]) for w in r}, flush=True)
for a in [1.0, 3.0, 10.0, 30.0, 100.0]:
    add(f"ridge alpha {a}, weekly refit", both(f, alpha=a))
orig_fit = M.fit_points
RAT = ["off_epa_play", "def_epa_play", "off_pf", "def_pf", "qb_rating"]
def fit_inter(train, alpha=10.0):
    X = train[M.FEATS].values; P = PolynomialFeatures(2, include_bias=False).fit(train[RAT].values); Z = np.hstack([X, P.transform(train[RAT].values)[:, len(RAT):]])
    m = make_pipeline(StandardScaler(), Ridge(alpha=alpha)).fit(Z, train.pf.values)
    class W:
        def predict(self, Xn): return m.predict(np.hstack([Xn, P.transform(Xn[:, :len(RAT)])[:, len(RAT):]]))
        def __getitem__(self, i): return m[i]
    return W()
# FEATS order: RATING_FEATS then qb_rating, so the first five columns are the ratings the interactions use
assert M.FEATS[:5] == RAT, M.FEATS[:5]
M.fit_points = fit_inter; add("ridge + rating interactions and squares", both(f)); M.fit_points = orig_fit
def fit_gbm(train, alpha=10.0):
    m = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.04, max_depth=3, min_samples_leaf=60, l2_regularization=1.0).fit(train[M.FEATS].values, train.pf.values)
    class W:
        def predict(self, Xn): return m.predict(Xn)
        def __getitem__(self, i):
            class S: coef_ = np.zeros(len(M.FEATS)); scale_ = np.ones(len(M.FEATS))
            return S()
    return W()
add("ridge, refit per season (for the tree comparison)", both(f, refit="season"))
M.fit_points = fit_gbm; add("gradient-boosted trees, same inputs, refit per season", both(f, refit="season")); M.fit_points = orig_fit
pd.DataFrame(rows).to_csv("reports/equation_checks.csv", index=False)
print("DONE")
