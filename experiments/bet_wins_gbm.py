"""Sensitivity of experiments/bet_wins.py to the tree model's settings (25 Sep 2026): the gradient-boosted spread model
refit under three other settings, each put in the seven-model blend in place of the original, graded the same way.
Writes reports/bet_wins_gbm.csv. A blend whose gain holds only for one setting is luck."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from nflmodel import model as M
from nflmodel.model import OUT
from experiments.bet_wins import REP, SEASONS

CFG = {"g_fast": dict(max_iter=150, learning_rate=0.06, max_leaf_nodes=8, min_samples_leaf=60, l2_regularization=1.0),
       "g_deep": dict(max_iter=300, learning_rate=0.03, max_leaf_nodes=16, min_samples_leaf=40, l2_regularization=1.0),
       "g_slow": dict(max_iter=600, learning_rate=0.015, max_leaf_nodes=6, min_samples_leaf=100, l2_regularization=3.0)}


def main():
    f = M.prep(M.with_trends(pd.read_parquet(OUT / "features_asof.parquet"))); played = f[f.pf.notna()]; F = list(M.FEATS); rows = []
    for s in SEASONS:
        for wk in sorted(f[f.season == s].week.unique()):
            train = played[(played.season >= 2013) & ((played.season < s) | ((played.season == s) & (played.week < wk)))]
            test = f[(f.season == s) & (f.week == wk)]
            h = test[test.home == 1].set_index("game_id"); a = test[test.home == 0].set_index("game_id"); ids = h.index.intersection(a.index)
            if len(ids) == 0:
                continue
            g = pd.DataFrame({"game_id": ids})
            for k, c in CFG.items():
                m = HistGradientBoostingRegressor(random_state=0, **c).fit(train[F].values, train.pf.values)
                g[f"sp_{k}"] = m.predict(h.loc[ids, F].values) - m.predict(a.loc[ids, F].values)
            rows.append(g)
        print("priced", s, flush=True)
    p = pd.read_parquet(REP / "bet_wins_preds.parquet").merge(pd.concat(rows), on="game_id")
    p = p[(p.week <= 17) & p.spread_line.notna()]
    lin = ["sp_base", "sp_success", "sp_split", "sp_plays", "sp_alpha3", "sp_alpha30"]
    W = {"2015-18": (2015, 2018), "2019-22": (2019, 2022), "2023-25": (2023, 2025)}; out = []
    for g in ["sp_gbm"] + [f"sp_{k}" for k in CFG]:
        p["b7"] = p[lin + [g]].mean(axis=1)
        for col, lab in ((g, g[3:]), ("b7", f"blend with {g[3:]}")):
            r = {"model": lab}
            for w, (a, b) in W.items():
                d = p[p.season.between(a, b)]; r[f"mae_{w}"] = round(float((d[col] - d.result).abs().mean()), 3)
                for cut in (4, 5):
                    e = d[col] - d.spread_line; bb = d[e.abs() >= cut]; c = (bb.result - bb.spread_line) * np.sign(e[e.abs() >= cut])
                    r[f"{cut}+_{w}"] = f"{int((c > 0).sum())}-{int((c < 0).sum())}"
            out.append(r)
    o = pd.DataFrame(out); o.to_csv(REP / "bet_wins_gbm.csv", index=False); pd.set_option("display.width", 250); print(o.to_string(index=False))


if __name__ == "__main__":
    main()
