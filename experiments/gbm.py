"""A second model family as a check on the linear equation: gradient-boosted trees on the same twenty inputs.
Refit before every season (weekly refits of a tree model are too slow to walk forward), against ridge refit the
same way, so the comparison is fair; then ridge with the weekly refit (today's model) for scale. Both windows.
Output reports/gbm.csv."""
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from nflmodel import model as M, backtest as B
from nflmodel.model import OUT
from experiments.common import WINDOWS, score
f = M.prep(M.with_trends(pd.read_parquet(OUT / "features_asof.parquet"))); games = pd.read_parquet(OUT / "games.parquet")
played = f[f.pf.notna()]
def walk(kind, seasons, **kw):
    preds = []
    for s in seasons:
        tr = played[(played.season < s) & (played.season >= 2013)]; te = f[f.season == s]
        X, y = tr[M.FEATS].values, tr.pf.values
        if kind == "gbm":
            m = HistGradientBoostingRegressor(max_iter=kw.get("iters", 300), learning_rate=kw.get("lr", 0.03), max_depth=kw.get("depth", 3), min_samples_leaf=40, l2_regularization=1.0, random_state=0).fit(X, y)
            exp = m.predict(te[M.FEATS].values)
        else:
            mm = M.fit_points(tr, 10.0); exp = mm.predict(te[M.FEATS].values) if hasattr(mm, "predict") else mm[-1].predict(mm[0].transform(te[M.FEATS].values))
        t = te[["game_id", "season", "week", "team", "home"]].copy(); t["exp"] = exp
        h = t[t.home == 1].set_index("game_id"); a = t[t.home == 0].set_index("game_id"); ids = h.index.intersection(a.index)
        pr = pd.DataFrame({"game_id": ids, "season": h.loc[ids, "season"].values, "week": h.loc[ids, "week"].values, "home_exp": h.loc[ids, "exp"].values, "away_exp": a.loc[ids, "exp"].values})
        pr["model_spread"] = pr.home_exp - pr.away_exp; pr["model_total"] = pr.home_exp + pr.away_exp; preds.append(pr)
    return pd.concat(preds, ignore_index=True)
rows = []
def run(name, kind, **kw):
    out = {}
    for w, seasons in WINDOWS.items():
        p = walk(kind, seasons, **kw); p["game_type"] = p.game_id.map(games.set_index("game_id").game_type)
        out[w] = score(p, seasons)
    rows.append({"variant": name, **{f"{k}_{ww}": v for ww, d in out.items() for k, v in d.items()}}); print(name, {ww: (out[ww]["team_mae"], out[ww]["margin_mae"], out[ww]["ats5"]) for ww in out}, flush=True)
run("ridge, refit each season", "ridge")
run("boosted trees, depth 3, 300 rounds", "gbm"); run("boosted trees, depth 2, 600 rounds", "gbm", depth=2, iters=600); run("boosted trees, depth 4, 200 rounds", "gbm", depth=4, iters=200)
pd.DataFrame(rows).to_csv("reports/gbm.csv", index=False); print("DONE")
