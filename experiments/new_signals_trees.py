"""Can the tree model use the new signals where the equation could not (25 Sep 2026)? Trees on the live inputs plus every
family in experiments/new_signals.py, placed in the seven-model blend in place of the live trees; graded like
experiments/bet_wins.py. Writes reports/new_signals_trees.csv."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from nflmodel import model as M
from nflmodel.model import OUT
from experiments import new_signals as NS
from experiments.bet_wins import REP


def main():
    raw = NS.build_raw(); A = NS.asof(raw)
    o = A.rename(columns={c: "o_" + c for c in NS.OPP_OF}).rename(columns={"team": "opp", "opp": "team"})[["game_id", "team"] + ["o_" + c for c in NS.OPP_OF]]
    A = A.merge(o, on=["game_id", "team"], how="left")
    f = M.prep(M.with_trends(pd.read_parquet(OUT / "features_asof.parquet"))).merge(A.drop(columns=["season", "week", "opp", "home", "rest"]), on=["game_id", "team"], how="left")
    f["altitude"] = ((f.opp == "DEN") & (f.home == 0)).astype(float)
    new = [c for c in A.columns if c not in ("game_id", "season", "week", "team", "opp", "home", "rest")] + ["altitude"]
    f[new] = f[new].fillna(0.0); cols = list(M.FEATS) + new; played = f[f.pf.notna()]; rows = []
    for s in range(2015, 2026):
        for wk in sorted(f[f.season == s].week.unique()):
            train = played[(played.season >= 2013) & ((played.season < s) | ((played.season == s) & (played.week < wk)))]
            test = f[(f.season == s) & (f.week == wk)]
            h = test[test.home == 1].set_index("game_id"); a = test[test.home == 0].set_index("game_id"); ids = h.index.intersection(a.index)
            if len(ids) == 0:
                continue
            m = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.03, max_leaf_nodes=8, min_samples_leaf=60, l2_regularization=1.0, random_state=0).fit(train[cols].values, train.pf.values)
            rows.append(pd.DataFrame({"game_id": ids, "sp_trees_new": m.predict(h.loc[ids, cols].values) - m.predict(a.loc[ids, cols].values)}))
        print("priced", s, flush=True)
    p = pd.read_parquet(REP / "bet_wins_preds.parquet").merge(pd.concat(rows), on="game_id"); p = p[(p.week <= 17) & p.spread_line.notna()]
    lin = ["sp_base", "sp_success", "sp_split", "sp_plays", "sp_alpha3", "sp_alpha30"]
    p["blend_live"] = p[lin + ["sp_gbm"]].mean(axis=1); p["blend_new"] = p[lin + ["sp_trees_new"]].mean(axis=1)
    W = {"2015-18": (2015, 2018), "2019-22": (2019, 2022), "2023-25": (2023, 2025)}; out = []
    for col in ["sp_gbm", "sp_trees_new", "blend_live", "blend_new"]:
        r = {"model": col}
        for w, (a_, b_) in W.items():
            d = p[p.season.between(a_, b_)]; r[f"mae_{w}"] = round(float((d[col] - d.result).abs().mean()), 3)
            for cut in (4, 5):
                e = d[col] - d.spread_line; bb = d[e.abs() >= cut]; c = (bb.result - bb.spread_line) * np.sign(e[e.abs() >= cut]); r[f"{cut}+_{w}"] = f"{int((c > 0).sum())}-{int((c < 0).sum())}"
        out.append(r)
    o = pd.DataFrame(out); o.to_csv(REP / "new_signals_trees.csv", index=False); pd.set_option("display.width", 250); print(o.to_string(index=False))


if __name__ == "__main__":
    main()
