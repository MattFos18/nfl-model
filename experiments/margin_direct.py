"""Predict the margin directly (one regression on home-minus-away inputs) instead of two team scores subtracted.
Same inputs, weekly refit, both windows; margin miss and flags. Output reports/margin_direct.csv."""
import numpy as np, pandas as pd
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from nflmodel import model as M, backtest as B
from nflmodel.model import OUT
f = M.prep(M.with_trends(pd.read_parquet(OUT / "features_asof.parquet"))); games = pd.read_parquet(OUT / "games.parquet")
TEAM = ["off_epa_play", "def_epa_play", "off_pf", "def_pf", "qb_rating", "qb_out", "warm_in_cold", "skill_out_value", "opp_skill_out_value", "off_snap_out", "opp_def_snap_out"]
def frame(df):
    h = df[df.home == 1].set_index("game_id"); a = df[df.home == 0].set_index("game_id"); ids = h.index.intersection(a.index)
    X = pd.DataFrame({c: h.loc[ids, c].values - a.loc[ids, c].values for c in TEAM}, index=ids)
    X["neutral"] = h.loc[ids, "neutral"].values; X["margin"] = (h.loc[ids, "pf"] - a.loc[ids, "pf"]).values
    X["season"] = h.loc[ids, "season"].values; X["week"] = h.loc[ids, "week"].values; X["spread_line"] = h.loc[ids, "spread_line"].values
    return X
G = frame(f); played = G[G.margin.notna()]
rows = []
for win, seasons in {"2019-22": range(2019, 2023), "2023-25": range(2023, 2026)}.items():
    preds = []
    for s in seasons:
        for wk in sorted(G[G.season == s].week.unique()):
            tr = played[(played.season >= 2013) & ((played.season < s) | ((played.season == s) & (played.week < wk)))]
            te = G[(G.season == s) & (G.week == wk)]
            cols = TEAM + ["neutral"]
            m = make_pipeline(StandardScaler(), Ridge(alpha=10.0)).fit(tr[cols].values, tr.margin.values)
            te = te.assign(pred=m.predict(te[cols].values)); preds.append(te)
    P = pd.concat(preds); P = P[P.margin.notna() & P.spread_line.notna()]
    mae = float(np.abs(P.pred - P.margin).mean()); edge = P.pred - P.spread_line; res = np.sign(P.margin - P.spread_line)
    m5 = (np.abs(edge) >= 5) & (res != 0); w = int((np.sign(edge[m5]) == res[m5]).sum()); l = int(m5.sum() - w)
    # the two-team model on the same games, for the comparison
    two = pd.read_parquet(OUT / "pred_v3.parquet"); two = two[two.game_id.isin(P.index)].set_index("game_id").loc[P.index]
    mae2 = float(np.abs(two.model_spread - P.margin).mean())
    rows.append({"window": win, "direct_margin_mae": round(mae, 4), "two_team_margin_mae": round(mae2, 4), "direct_ats5": f"{w}-{l}", "n": int(len(P))}); print(rows[-1], flush=True)
pd.DataFrame(rows).to_csv("reports/margin_direct.csv", index=False); print("DONE")
