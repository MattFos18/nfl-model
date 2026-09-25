"""Fix the overs (25 Sep 2026, Matt: "figure out how to fix it"). Our own data only; the closing total is what a bet is
graded against. Why the overs lose (docs section 38): game totals are right-skewed, so a model of the average calls
overs that the typical game does not reach (over calls: +0.7 points over the line on average, but 49.5% won), and the
equation learns the league's scoring level from past seasons, so it lags a league-wide drop (2017, 2022, 2023).

Walk-forward over 2015-2025, weekly refit, every game priced with earlier games only:
  mean         the live total equation (ridge, the average total)
  median       the same inputs fitted to the median total (absolute-error loss): the typical game, not the average
  mean_drift   + the league's scoring over the previous 17 weeks of games (the equation can follow a league-wide shift)
  median+drift both
  trees_med    gradient-boosted trees on the same inputs plus pace and both offenses' pass and success ratings, median loss
  dist         the live mean with a skewed spread: P(over) from the training residuals of games like this one (an
               empirical distribution of actual minus predicted, shifted to this game's prediction); bet at P >= 0.55
  logit        P(over) from a logistic fit on earlier seasons' walk-forward bets: the edge, both offenses' pace, dome,
               wind and the league drift; bet at P >= 0.55
Records by side at 3+ (and the P rules), misses, by window. Writes reports/totals_fix.csv and totals_fix_preds.parquet."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import numpy as np, pandas as pd
from sklearn.linear_model import Ridge, QuantileRegressor, LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import HistGradientBoostingRegressor
from nflmodel import model as M
from nflmodel.model import OUT

REP = Path(__file__).resolve().parent.parent / "reports"
W = {"2015-18": (2015, 2018), "2019-22": (2019, 2022), "2023-25": (2023, 2025)}
EXTRA = {"pace_sum": "off_plays", "dpace_sum": "def_plays", "pass_sum": "off_pass_epa", "succ_sum": "off_success", "dpass_sum": "def_pass_epa"}


def frame(x: pd.DataFrame) -> pd.DataFrame:
    g = M._game_frame(x)
    h = x[x.home == 1].set_index("game_id"); a = x[x.home == 0].set_index("game_id"); ids = g.index
    for k, c in EXTRA.items():
        g[k] = (h.loc[ids, c] + a.loc[ids, c]).values
    g["season"] = h.loc[ids, "season"].values; g["week"] = h.loc[ids, "week"].values
    return g


def main():
    f = M.prep(M.with_trends(pd.read_parquet(OUT / "features_asof.parquet")))
    for c in EXTRA.values():
        f[c] = f[c].fillna(f[c].mean())
    G = frame(f); gm = pd.read_parquet(OUT / "games.parquet").set_index("game_id")
    G["total_line"] = gm.total_line.reindex(G.index); G["game_type"] = gm.game_type.reindex(G.index)
    G = G.sort_values(["season", "week"])
    # the league's scoring over the previous 17 weeks of played games, as of each week
    wk = G[G.total.notna()].groupby(["season", "week"]).total.agg(["sum", "count"]).reset_index()
    wk["drift"] = wk["sum"].shift(1).rolling(17, min_periods=4).sum() / wk["count"].shift(1).rolling(17, min_periods=4).sum()
    allw = G[["season", "week"]].drop_duplicates().merge(wk[["season", "week", "drift"]], on=["season", "week"], how="left").sort_values(["season", "week"])
    allw["drift"] = allw.drift.ffill(); G = G.reset_index().merge(allw, on=["season", "week"], how="left").set_index("game_id")
    G["drift"] = G.drift.fillna(G.drift.mean())
    base = list(M.TOTAL_FEATS); dr = base + ["drift"]; big = dr + list(EXTRA)
    rows = []
    for s in range(2015, 2026):
        for w in sorted(G[G.season == s].week.unique()):
            tr = G[G.total.notna() & (G.season >= 2013) & ((G.season < s) | ((G.season == s) & (G.week < w)))]
            te = G[(G.season == s) & (G.week == w)]
            if not len(te):
                continue
            o = pd.DataFrame(index=te.index)
            rm = make_pipeline(StandardScaler(), Ridge(alpha=10.0)).fit(tr[base].values, tr.total.values)
            o["mean"] = rm.predict(te[base].values); resid = tr.total.values - rm.predict(tr[base].values)
            o["mean_drift"] = make_pipeline(StandardScaler(), Ridge(alpha=10.0)).fit(tr[dr].values, tr.total.values).predict(te[dr].values)
            o["median"] = make_pipeline(StandardScaler(), QuantileRegressor(quantile=0.5, alpha=0.002, solver="highs")).fit(tr[base].values, tr.total.values).predict(te[base].values)
            o["median_drift"] = make_pipeline(StandardScaler(), QuantileRegressor(quantile=0.5, alpha=0.002, solver="highs")).fit(tr[dr].values, tr.total.values).predict(te[dr].values)
            o["trees_med"] = HistGradientBoostingRegressor(loss="absolute_error", max_iter=300, learning_rate=0.03, max_leaf_nodes=8, min_samples_leaf=60, random_state=0).fit(tr[big].values, tr.total.values).predict(te[big].values)
            # P(over) from the empirical residuals of the training games: this game's mean + every residual, share above the line
            o["p_dist"] = [float(np.mean(m + resid > L)) / max(1e-9, float(np.mean(m + resid != L))) if pd.notna(L) else np.nan for m, L in zip(o["mean"], te.total_line)]
            o["season"], o["week"] = s, w
            rows.append(o)
        print("priced", s, flush=True)
    pd.concat(rows).to_parquet(REP / "totals_fix_raw.parquet")
    P = pd.concat(rows).join(G[["total", "total_line", "game_type", "drift"] + base + list(EXTRA)])
    P = P[(P.game_type == "REG") & P.total.notna()]
    # logistic P(over) from earlier seasons' walk-forward rows: edge, pace, dome, wind, drift
    P["edge"] = P["mean"] - P.total_line; LX = ["edge", "pace_sum", "dome", "wind_out", "drift"]; P["p_logit"] = np.nan
    for s in range(2016, 2026):
        tr = P[(P.season < s) & P.total_line.notna() & (P.total != P.total_line)]; te = P[(P.season == s) & P.total_line.notna()]
        lg = make_pipeline(StandardScaler(), LogisticRegression(C=0.5)).fit(tr[LX].values, (tr.total > tr.total_line).astype(int).values)
        P.loc[te.index, "p_logit"] = lg.predict_proba(te[LX].values)[:, 1]
    P.to_parquet(REP / "totals_fix_preds.parquet")
    out = []
    for col in ["mean", "mean_drift", "median", "median_drift", "trees_med"]:
        for cut in (3, 4):
            r = {"model": col, "rule": f"{cut}+"}
            for wn, (a, b) in W.items():
                x = P[P.season.between(a, b) & (P.week <= 17) & P.total_line.notna()]
                r[f"miss_{wn}"] = round(float((P[P.season.between(a, b)][col] - P[P.season.between(a, b)].total).abs().mean()), 3)
                e = x[col] - x.total_line
                for side, lab in ((1, "over"), (-1, "under")):
                    k = e * side >= cut; v = (x.total - x.total_line)[k] * side; r[f"{lab}_{wn}"] = f"{int((v > 0).sum())}-{int((v < 0).sum())}"
            out.append(r)
    for col in ["p_dist", "p_logit"]:
        for thr in (0.55, 0.58):
            r = {"model": col, "rule": f"P>={thr}"}
            for wn, (a, b) in W.items():
                x = P[P.season.between(a, b) & (P.week <= 17) & P.total_line.notna() & P[col].notna()]
                for side, lab in ((1, "over"), (-1, "under")):
                    pp = x[col] if side == 1 else 1 - x[col]; k = pp >= thr; v = (x.total - x.total_line)[k] * side; r[f"{lab}_{wn}"] = f"{int((v > 0).sum())}-{int((v < 0).sum())}"
            out.append(r)
    o = pd.DataFrame(out); o.to_csv(REP / "totals_fix.csv", index=False); pd.set_option("display.width", 250); print(o.to_string(index=False))
    # where over calls win: the live mean's 3+ over calls split by situation, each window
    x = P[(P.week <= 17) & P.total_line.notna() & ((P["mean"] - P.total_line) >= 3)].copy(); x["won"] = x.total > x.total_line; x["lost"] = x.total < x.total_line
    x["pace"] = np.where(x.pace_sum > x.pace_sum.median(), "fast", "slow"); x["roof"] = np.where(x.dome == 1, "dome", "outdoors"); x["windy"] = np.where(x.wind_out >= 10, "wind 10+", "calm")
    x["offenses"] = np.where(x.pass_sum > 0, "good passing", "weak passing"); x["win"] = pd.cut(x.season, [2014, 2018, 2022, 2025], labels=list(W))
    sub = []
    for dim in ("pace", "roof", "windy", "offenses"):
        t = x.groupby([dim, "win"], observed=True)[["won", "lost"]].sum().reset_index(); t["dim"] = dim; sub.append(t.rename(columns={dim: "group"}))
    s_ = pd.concat(sub); s_.to_csv(REP / "totals_fix_overs_by_situation.csv", index=False); print(s_.to_string(index=False))


if __name__ == "__main__":
    main()
