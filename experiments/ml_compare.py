"""The published study's comparison, run properly on our data (29 Sep 2026, Matt: a study compared linear regression,
gradient boosting and a neural network for NFL totals and spreads, each on three feature sets, reporting RMSE and
"classification accuracy" at betting thresholds). Here: five model families x four feature sets x two targets, walk-forward
2015-2025, scored per window against the live model (data/processed/pred_v3.parquet, the seven-model blend for the spread
and the total equation for the total, which is exactly what the site prices and grades).

Targets
  points   each team's points (the live target); margin = home - away, total = home + away
  total    the game total directly (one row per game, both teams' inputs summed; the live total equation's inputs are set 1)
Feature sets (no market input in any: spread_line, total_line, implied and the line-derived trends are excluded and asserted)
  1 live     model.FEATS (points) / model.TOTAL_FEATS (total)
  2 wide     FEATS + FEATS_WIDE + every signal family of experiments/new_signals.py (own side and the opponent's matching side);
             for the total, TOTAL_FEATS + the two teams' sums of each of those
  3 lasso    the subset of set 2 a cross-validated lasso keeps, chosen on the training rows only inside every refit
  4 forward  forward selection from set 2 with the ridge, chosen once on 2013-18 only (season refits, validation 2015-18)
Models
  ridge (alpha 10, the live form), lasso (LassoCV inside every refit), gradient boosting (HistGradientBoostingRegressor,
  grid tuned on 2013-18), random forest (min leaf tuned on 2013-18), MLP (standardised inputs and target, early stopping,
  grid tuned on 2013-18). Ridge, lasso and boosting refit before every week; forest and MLP every 4 weeks (the model is
  older, the inputs are still as of each game). Every fit trains on every played game (playoffs included) from 2013 on.

Stages (run in order; the slow ones in the background, each writes its predictions to the scratch folder)
  python experiments/ml_compare.py frames | fs | time | run --model lasso | tune --model hgb | run --model hgb | report
Writes reports/ml_compare.csv and appends the results to reports/ml_compare.md (whose adoption rule was written first)."""
import os
os.environ.setdefault("OMP_NUM_THREADS", "1"); os.environ.setdefault("OPENBLAS_NUM_THREADS", "1"); os.environ.setdefault("MKL_NUM_THREADS", "1")
import sys, json, time, argparse, warnings
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import numpy as np, pandas as pd
from sklearn.linear_model import Ridge, LassoCV
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.compose import TransformedTargetRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.exceptions import ConvergenceWarning
from nflmodel import model as M
from nflmodel.model import OUT

warnings.filterwarnings("ignore", category=ConvergenceWarning)
ROOT = Path(__file__).resolve().parent.parent; REP = ROOT / "reports"
SCR = Path(os.environ.get("ML_SCR", "/tmp/claude-0/-home-user/c1e0d18e-681a-50ba-b0bb-6c809c2e3dee/scratchpad/ml")); SCR.mkdir(parents=True, exist_ok=True)
M.TREES_CACHE = SCR / "trees_cache.parquet"   # never write data/processed (this study does not call the blend, but just in case)
W = {"2015-18": (2015, 2018), "2019-22": (2019, 2022), "2023-25": (2023, 2025)}
FIRST, LAST, TRAIN_FROM = 2015, 2025, 2013
BANNED = {"spread_line", "total_line", "implied", "home_implied", "away_implied", "h2h_cover", "coach_ats", "qb_ats", "ref_over", "ref_home_cover",
          "hfa_fit", "pf", "pa", "result", "total", "margin"}
MODELS = ["ridge", "lasso", "hgb", "rf", "mlp"]
SETS = ["live", "wide", "lasso", "forward"]
EVERY = {"ridge": 1, "lasso": 1, "hgb": 1, "rf": 4, "mlp": 4}   # refit every N regular-season weeks
GRID = {"hgb": [dict(max_iter=300, learning_rate=0.03, max_leaf_nodes=8, min_samples_leaf=60, l2_regularization=1.0),    # the live trees
                dict(max_iter=300, learning_rate=0.03, max_leaf_nodes=4, min_samples_leaf=100, l2_regularization=1.0),
                dict(max_iter=600, learning_rate=0.015, max_leaf_nodes=6, min_samples_leaf=100, l2_regularization=3.0),
                dict(max_iter=150, learning_rate=0.05, max_leaf_nodes=16, min_samples_leaf=40, l2_regularization=1.0),
                dict(max_iter=500, learning_rate=0.02, max_depth=2, min_samples_leaf=200, l2_regularization=3.0)],
        "mlp": [dict(hidden_layer_sizes=(8,), alpha=1e-2), dict(hidden_layer_sizes=(16,), alpha=1e-1), dict(hidden_layer_sizes=(32,), alpha=1.0),
                dict(hidden_layer_sizes=(32, 16), alpha=1e-1), dict(hidden_layer_sizes=(64, 32), alpha=1.0)],
        "rf": [dict(min_samples_leaf=25), dict(min_samples_leaf=75), dict(min_samples_leaf=200)]}


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


# ---------------------------------------------------------------- frames
def frames():
    from experiments import new_signals as NS
    t0 = time.time()
    raw = NS.build_raw(); A = NS.asof(raw)
    o = A.rename(columns={c: "o_" + c for c in NS.OPP_OF}).rename(columns={"team": "opp", "opp": "team"})[["game_id", "team"] + ["o_" + c for c in NS.OPP_OF]]
    A = A.merge(o, on=["game_id", "team"], how="left")
    f = M.prep(M.with_trends(pd.read_parquet(OUT / "features_asof.parquet")))
    f = f.merge(A.drop(columns=["season", "week", "opp", "home", "rest"]), on=["game_id", "team"], how="left")
    f["altitude"] = ((f.opp == "DEN") & (f.home == 0)).astype(float)
    ns = [c for c in A.columns if c not in ("game_id", "season", "week", "team", "opp", "home", "rest")] + ["altitude"]
    f[ns] = f[ns].fillna(0.0)
    wide = list(dict.fromkeys(list(M.FEATS) + list(M.FEATS_WIDE) + ns))
    bad = [c for c in wide if c in BANNED or "line" in c or "implied" in c or "cover" in c or "ats" in c.split("_")]
    assert not bad, bad
    # a line-derived input would track the line: report the strongest correlation of any wide input with the implied points
    pl = f[f.pf.notna() & f.implied.notna() & (f.season >= TRAIN_FROM)]
    cr = pl[wide].corrwith(pl.implied).abs().sort_values(ascending=False)
    log("largest |corr| with implied points:", cr.head(6).round(3).to_dict())
    keep = ["game_id", "season", "week", "game_type", "team", "opp", "home", "pf", "pa"] + [c for c in dict.fromkeys(wide + M.TOTAL_FEATS + ["qb_form", "ref_tot", "ref_over"]) if c in f.columns]
    T = f[[c for c in dict.fromkeys(keep)]].copy()
    # game frame: the live total inputs, plus both teams' sum of every wide input (home dropped: it sums to 1)
    base = M._game_frame(f)
    h = f[f.home == 1].set_index("game_id"); a = f[f.home == 0].set_index("game_id"); ids = base.index
    G = pd.DataFrame({"game_id": ids, "season": h.loc[ids, "season"].values, "week": h.loc[ids, "week"].values, "game_type": h.loc[ids, "game_type"].values,
                      "home_team": h.loc[ids, "team"].values, "away_team": a.loc[ids, "team"].values, "total": base.total.values})
    for c in M.TOTAL_FEATS:
        G[c] = base[c].values
    sums = {"s_" + c: h.loc[ids, c].values + a.loc[ids, c].values for c in wide if c not in ("home", "o_altitude")}
    G = pd.concat([G, pd.DataFrame(sums)], axis=1); wide_g = list(M.TOTAL_FEATS) + list(sums)
    assert not [c for c in wide_g if c in BANNED]
    T.to_parquet(SCR / "team_frame.parquet", index=False); G.to_parquet(SCR / "game_frame.parquet", index=False)
    live = pd.read_parquet(OUT / "pred_v3.parquet"); live = live[live.season.between(FIRST, LAST)]
    live[["game_id", "season", "week", "home_exp", "away_exp", "model_spread", "model_total", "home_m_ridge", "away_m_ridge", "home_m_trees", "away_m_trees"]].to_parquet(SCR / "live_preds.parquet", index=False)
    sets = {"points": {"live": list(M.FEATS), "wide": wide}, "total": {"live": list(M.TOTAL_FEATS), "wide": wide_g}}
    (SCR / "sets.json").write_text(json.dumps(sets, indent=1))
    na = T[T.pf.notna() & (T.season >= TRAIN_FROM)][wide].isna().sum(); na = na[na > 0]
    log(f"frames: team {T.shape}, game {G.shape}, wide points {len(wide)} inputs, wide total {len(wide_g)}; NaN columns in played rows: {na.to_dict()}; {time.time() - t0:.0f}s")


def load():
    T = pd.read_parquet(SCR / "team_frame.parquet"); G = pd.read_parquet(SCR / "game_frame.parquet"); S = json.loads((SCR / "sets.json").read_text())
    fs = SCR / "forward.json"
    if fs.exists():
        for k, v in json.loads(fs.read_text()).items():
            S[k]["forward"] = v
    return T, G, S


def frame_for(target, T, G):
    return (T, "pf") if target == "points" else (G, "total")


# ---------------------------------------------------------------- models
def make(model, cfg=None, seed=0):
    cfg = cfg or {}
    if model == "ridge":
        return make_pipeline(StandardScaler(), Ridge(alpha=10.0))
    if model == "lasso":
        return make_pipeline(StandardScaler(), LassoCV(alphas=30, cv=5, max_iter=5000, random_state=0))
    if model == "hgb":
        return HistGradientBoostingRegressor(random_state=seed, **cfg)
    if model == "rf":
        return RandomForestRegressor(n_estimators=150, max_features=0.33, max_samples=0.5, n_jobs=1, random_state=seed, **cfg)
    if model == "mlp":
        net = MLPRegressor(early_stopping=True, validation_fraction=0.15, n_iter_no_change=20, max_iter=400, learning_rate_init=1e-3, batch_size=200, random_state=seed, **cfg)
        return TransformedTargetRegressor(regressor=make_pipeline(StandardScaler(), net), transformer=StandardScaler())
    raise ValueError(model)


def xy(df, cols, mu):
    return df[cols].astype(float).fillna(mu[cols]).values


def fit_predict(model, cfg, train, test, cols, ycol):
    mu = train[cols].astype(float).mean()
    m = make(model, cfg).fit(xy(train, cols, mu), train[ycol].values)
    return m, m.predict(xy(test, cols, mu))


def lasso_select(train, cols, ycol):
    mu = train[cols].astype(float).mean()
    m = make("lasso").fit(xy(train, cols, mu), train[ycol].values)
    sel = [c for c, b in zip(cols, m[-1].coef_) if abs(b) > 1e-10]
    return sel or cols[:1], m, mu


def train_rows(df, s, wk):
    p = df[df[("pf" if "pf" in df.columns else "total")].notna() & (df.season >= TRAIN_FROM)]
    return p[(p.season < s) | ((p.season == s) & (p.week < wk))]


def reg_weeks(df, s):
    return sorted(df[(df.season == s) & (df.game_type == "REG")].week.unique())


# ---------------------------------------------------------------- forward selection (2013-18 only)
def season_cv(df, ycol, cols, model="ridge", cfg=None, seasons=range(2015, 2019), sel=None):
    """Season refits on 2013..s-1, scored on season s (played, regular season), s in 2015-18: pooled MAE, RMSE."""
    err = []
    for s in seasons:
        tr = train_rows(df, s, 1); te = df[(df.season == s) & (df.game_type == "REG") & df[ycol].notna()]
        c = sel[str(s)] if sel is not None else cols
        _, p = fit_predict(model, cfg, tr, te, c, ycol); err.append(p - te[ycol].values)
    e = np.concatenate(err); return float(np.abs(e).mean()), float(np.sqrt((e ** 2).mean()))


def forward():
    T, G, S = load(); out = {}
    for target in ("points", "total"):
        df, ycol = frame_for(target, T, G); df = df[df.season <= 2018]; pool = list(S[target]["wide"]); chosen, best = [], np.inf
        while True:
            res = {c: season_cv(df, ycol, chosen + [c])[0] for c in pool if c not in chosen}
            c, v = min(res.items(), key=lambda kv: kv[1])
            if best - v < 1e-3:
                break
            chosen.append(c); best = v; log(f"forward {target}: + {c} -> MAE {v:.4f} ({len(chosen)} inputs)")
        out[target] = chosen
    (SCR / "forward.json").write_text(json.dumps(out, indent=1)); log("forward done", {k: len(v) for k, v in out.items()})


# ---------------------------------------------------------------- walk-forward
def walk(model, target, cfgs, sel_all):
    T, G, S = load(); df, ycol = frame_for(target, T, G); every = EVERY[model]; rows = []; t0 = time.time()
    new_sel = {}
    for s in range(FIRST, LAST + 1):
        weeks = reg_weeks(df, s); blocks = [weeks[i:i + every] for i in range(0, len(weeks), every)]
        for blk in blocks:
            wk = blk[0]; tr = train_rows(df, s, wk); te = df[(df.season == s) & df.week.isin(blk) & (df.game_type == "REG")]
            if len(te) == 0:
                continue
            out = te[["game_id", "season", "week"] + (["team", "home"] if target == "points" else [])].copy()
            key = f"{s}-{wk}"
            if model == "lasso":   # the lasso fit on the wide set is also the set-3 selection every model uses
                sel, m, mu = lasso_select(tr, S[target]["wide"], ycol); new_sel[key] = sel
                out["p_wide"] = m.predict(xy(te, S[target]["wide"], mu))
            for st in SETS:
                if model == "lasso" and st == "wide":
                    continue
                cols = (new_sel[key] if model == "lasso" else sel_all[key]) if st == "lasso" else S[target][st]
                _, out[f"p_{st}"] = fit_predict(model, cfgs.get(st), tr, te, cols, ycol)
            rows.append(out)
        log(f"{model} {target} priced {s} ({time.time() - t0:.0f}s)")
    if model == "lasso":
        (SCR / f"lasso_sel_{target}.json").write_text(json.dumps(new_sel))
    p = pd.concat(rows, ignore_index=True); p.to_parquet(SCR / f"pred_{model}_{target}.parquet", index=False)
    return p


def tune(model):
    T, G, S = load(); best = {}
    for target in ("points", "total"):
        df, ycol = frame_for(target, T, G); df = df[df.season <= 2018]
        sel = json.loads((SCR / f"lasso_sel_{target}.json").read_text()); sel = {str(s): sel[f"{s}-{reg_weeks(df, s)[0]}"] for s in range(2015, 2019)}
        best[target] = {}
        for st in SETS:
            res = []
            for i, cfg in enumerate(GRID[model]):
                t0 = time.time(); mae, rmse = season_cv(df, ycol, S[target].get(st), model, cfg, sel=sel if st == "lasso" else None)
                res.append((mae, i)); log(f"tune {model} {target} {st} cfg{i} MAE {mae:.4f} RMSE {rmse:.4f} ({time.time() - t0:.0f}s)")
            best[target][st] = GRID[model][min(res)[1]]
    (SCR / f"tuned_{model}.json").write_text(json.dumps(best, indent=1)); log("tuned", model, best)


def run(model, targets):
    for target in targets:
        cfgs = json.loads((SCR / f"tuned_{model}.json").read_text())[target] if model in GRID else {}
        sel = json.loads((SCR / f"lasso_sel_{target}.json").read_text()) if model != "lasso" else None
        walk(model, target, cfgs, sel)
    log("run done", model)


def timing():
    T, G, S = load()
    for target in ("points", "total"):
        df, ycol = frame_for(target, T, G); tr = train_rows(df, 2025, 17); te = df[(df.season == 2025) & (df.week == 17)]
        for model in MODELS:
            for st in ("live", "wide"):
                t0 = time.time(); fit_predict(model, GRID.get(model, [{}])[0] if model in GRID else None, tr, te, S[target][st], ycol)
                log(f"one refit: {model} {target} {st} ({len(tr)} rows x {len(S[target][st])} inputs): {time.time() - t0:.1f}s")


# ---------------------------------------------------------------- scoring
def grade_spread(d, sp, cut=4.0):
    x = d[(d.week <= 17) & d.spread_line.notna()]; e = sp.loc[x.index] - x.spread_line; cm = x.result - x.spread_line
    m = (e.abs() >= cut) & (cm != 0); w = int(((np.sign(e) == np.sign(cm)) & m).sum()); return w, int(m.sum()) - w


def grade_under(d, tot, cut=3.0):
    x = d[(d.week <= 17) & d.total_line.notna()]; e = tot.loc[x.index] - x.total_line; cm = x.total - x.total_line
    m = (e <= -cut) & (cm != 0); w = int(((cm < 0) & m).sum()); return w, int(m.sum()) - w


def rec(t):
    return f"{t[0]}-{t[1]}"


def pct(t):
    return t[0] / max(1, t[0] + t[1])


def metrics(d, sp=None, tot=None, hp=None, ap=None):
    r = {}
    if hp is not None:
        e = np.concatenate([(hp - d.home_score).values, (ap - d.away_score).values]); r["team_mae"] = np.abs(e).mean(); r["team_rmse"] = np.sqrt((e ** 2).mean())
    if sp is not None:
        e = (sp - d.result).values; r["margin_mae"] = np.abs(e).mean(); r["margin_rmse"] = np.sqrt((e ** 2).mean()); t = grade_spread(d, sp); r["spread4"] = rec(t); r["spread4_pct"] = pct(t)
    if tot is not None:
        e = (tot - d.total).values; r["total_mae"] = np.abs(e).mean(); r["total_rmse"] = np.sqrt((e ** 2).mean()); t = grade_under(d, tot); r["under3"] = rec(t); r["under3_pct"] = pct(t)
    return r


def study_curve(d, pred, line, actual, fracs):
    """Accuracy of the model's side (over/under, or home/away against the spread) when |pred - line| >= frac * |line|."""
    x = d[(d.week <= 17) & d[line].notna()]; e = pred.loc[x.index] - x[line]; cm = x[actual] - x[line]; out = []
    for fr in fracs:
        m = (e.abs() >= fr * x[line].abs()) & (e != 0) & (cm != 0)
        out.append({"frac": fr, **{w: (int(((np.sign(e) == np.sign(cm)) & m & x.season.between(a, b)).sum()), int((m & x.season.between(a, b)).sum())) for w, (a, b) in W.items()}})
    return out


def report():
    games = pd.read_parquet(OUT / "games.parquet")[["game_id", "season", "week", "game_type", "home_score", "away_score", "result", "total", "spread_line", "total_line"]]
    g = games[(games.game_type == "REG") & games.season.between(FIRST, LAST) & games.home_score.notna()].set_index("game_id")
    live = pd.read_parquet(SCR / "live_preds.parquet").set_index("game_id").reindex(g.index)
    assert live.model_spread.notna().all()
    cand = {("live model", "live", "live"): dict(sp=live.model_spread, tot=live.model_total, hp=live.home_exp, ap=live.away_exp),
            ("live ridge alone", "live", "points"): dict(sp=live.home_m_ridge - live.away_m_ridge, hp=live.home_m_ridge, ap=live.away_m_ridge, tot=live.home_m_ridge + live.away_m_ridge),
            ("live trees alone", "live", "points"): dict(sp=live.home_m_trees - live.away_m_trees, hp=live.home_m_trees, ap=live.away_m_trees, tot=live.home_m_trees + live.away_m_trees)}
    runtimes = json.loads((SCR / "runtimes.json").read_text()) if (SCR / "runtimes.json").exists() else {}
    for model in MODELS:
        pp, pt = SCR / f"pred_{model}_points.parquet", SCR / f"pred_{model}_total.parquet"
        if pp.exists():
            p = pd.read_parquet(pp); h = p[p.home == 1].set_index("game_id").reindex(g.index); a = p[p.home == 0].set_index("game_id").reindex(g.index)
            for st in SETS:
                if f"p_{st}" in p.columns:
                    cand[(model, st, "points")] = dict(sp=h[f"p_{st}"] - a[f"p_{st}"], tot=h[f"p_{st}"] + a[f"p_{st}"], hp=h[f"p_{st}"], ap=a[f"p_{st}"])
        if pt.exists():
            p = pd.read_parquet(pt).set_index("game_id").reindex(g.index)
            for st in SETS:
                if f"p_{st}" in p.columns:
                    cand[(model, st, "total")] = dict(tot=p[f"p_{st}"])
    # the stacked blends: live + w * (model - live), w on a 0.05 grid fitted on 2015-18 by MAE
    e18 = g.season.between(2015, 2018)
    for (model, st, tgt), c in list(cand.items()):
        if model.startswith("live"):
            continue
        for kind, lv, act in (("sp", live.model_spread, g.result), ("tot", live.model_total, g.total)):
            if c.get(kind) is None or c[kind].isna().any():
                continue
            ws = np.round(np.arange(0, 1.0001, 0.05), 2)
            w = min(ws, key=lambda w_: float(np.abs((lv + w_ * (c[kind] - lv) - act)[e18]).mean()))
            cand[(f"stack live+{model}", st, tgt + ("/spread" if kind == "sp" else "/total"))] = {kind: lv + w * (c[kind] - lv), "w": w}
    rows = []
    for (model, st, tgt), c in cand.items():
        for w, (a, b) in W.items():
            m = g.season.between(a, b); d = g[m]
            r = {"model": model, "features": st, "target": tgt, "window": w, "n_games": int(m.sum()), "stack_w": c.get("w")}
            r.update(metrics(d, **{k: (v[m] if v is not None else None) for k, v in c.items() if k in ("sp", "tot", "hp", "ap")}))
            rows.append(r)
    for w, (a, b) in W.items():
        d = g[g.season.between(a, b)]
        rows.append({"model": "the closing line", "features": "-", "target": "-", "window": w, "n_games": len(d), "margin_mae": (d.spread_line - d.result).abs().mean(), "margin_rmse": np.sqrt(((d.spread_line - d.result) ** 2).mean()),
                     "total_mae": (d.total_line - d.total).abs().mean(), "total_rmse": np.sqrt(((d.total_line - d.total) ** 2).mean())})
    R = pd.DataFrame(rows)
    # adoption
    L = R[R.model == "live model"].set_index("window")
    def verdict(grp, kind):
        mae, rc = ("margin_mae", "spread4_pct") if kind == "sp" else ("total_mae", "under3_pct")
        x = grp.set_index("window")
        if x[mae].isna().any():
            return None
        return bool(all(x.loc[w, mae] < L.loc[w, mae] for w in W) and all(x.loc[w, rc] >= L.loc[w, rc] - 1e-12 for w in W))
    ad = []
    for (model, st, tgt), grp in R[R.model != "the closing line"].groupby(["model", "features", "target"], sort=False):
        if model == "live model":
            continue
        ad.append({"model": model, "features": st, "target": tgt, "adopt_spread": verdict(grp, "sp") if "margin_mae" in grp and grp.margin_mae.notna().all() else None,
                   "adopt_total": verdict(grp, "tot") if "total_mae" in grp and grp.total_mae.notna().all() else None})
    AD = pd.DataFrame(ad); R = R.merge(AD, on=["model", "features", "target"], how="left")
    for c in R.columns:
        if R[c].dtype == float:
            R[c] = R[c].round(4)
    R.to_csv(REP / "ml_compare.csv", index=False)
    # the study's style: threshold as a share of the line
    fr_t = np.round(np.arange(0, 0.1001, 0.005), 3); fr_s = np.round(np.arange(0, 0.5001, 0.05), 2); st_rows = []
    n_min_pooled, n_min_1518 = 500, int(np.ceil(500 * 4 / 11))
    for key, c in cand.items():
        for kind, pred, line, act, frs in (("totals", c.get("tot"), "total_line", "total", fr_t), ("spreads", c.get("sp"), "spread_line", "result", fr_s)):
            if pred is None or pred.isna().any():
                continue
            cur = study_curve(g, pred, line, act, frs)
            def acc(r, w):
                return r[w][0] / max(1, r[w][1])
            pooled = [(r["frac"], sum(r[w][0] for w in W) / max(1, sum(r[w][1] for w in W)), sum(r[w][1] for w in W)) for r in cur]
            ok = [x for x in pooled if x[2] >= n_min_pooled]; la = max(ok, key=lambda x: x[1]) if ok else (np.nan, np.nan, 0)
            ok18 = [r for r in cur if r["2015-18"][1] >= n_min_1518]; hp = max(ok18, key=lambda r: acc(r, "2015-18")) if ok18 else None
            z = cur[0]
            st_rows.append({"model": key[0], "features": key[1], "target": key[2], "market": kind, "rmse_2015_25": float(np.sqrt(((pred - g[act]) ** 2).mean())),
                            "acc_at_0_pooled": sum(z[w][0] for w in W) / max(1, sum(z[w][1] for w in W)),
                            "lookahead_best_frac": la[0], "lookahead_best_acc": la[1], "lookahead_n": la[2],
                            "picked_frac_2015_18": hp["frac"] if hp else np.nan,
                            **({f"acc_{w}": acc(hp, w) for w in W} if hp else {}), **({f"n_{w}": hp[w][1] for w in W} if hp else {})})
    STY = pd.DataFrame(st_rows).round(4); STY.to_csv(SCR / "study_style.csv", index=False)
    pd.concat([R.assign(table="per window"), STY.assign(table="study style", window="2015-25 / picked on 2015-18")], ignore_index=True).to_csv(REP / "ml_compare.csv", index=False)
    write_md(R, AD, STY, runtimes)
    log("report written")


def write_md(R, AD, STY, runtimes):
    md = (REP / "ml_compare.md").read_text(); cut = md.find("\n## Results")
    md = md if cut < 0 else md[:cut + 1]
    S = json.loads((SCR / "sets.json").read_text()); fw = json.loads((SCR / "forward.json").read_text())
    tn = {m: json.loads((SCR / f"tuned_{m}.json").read_text()) for m in GRID if (SCR / f"tuned_{m}.json").exists()}
    def tbl(df):
        return df.to_markdown(index=False) if len(df) else "(none)"
    def wide_cell(x, cols):
        return {w: " / ".join(str(x.loc[w, c]) if c in x.columns and pd.notna(x.loc[w, c]) else "-" for c in cols) for w in W}
    out = ["## Results", ""]; L = R[R.model == "live model"].set_index("window")
    out.append(f"Inputs: set 1 is {len(S['points']['live'])} points inputs / {len(S['total']['live'])} total inputs; set 2 is {len(S['points']['wide'])} / {len(S['total']['wide'])}; "
               f"set 4 (forward, ridge, chosen on 2013-18 only): points {', '.join(fw['points'])}; total {', '.join(fw['total'])}. "
               "Set 3 is refit inside every refit (a LassoCV on the training rows). No input reads a line (asserted by name; the "
               "wide inputs' largest correlation with the market's implied points is the offense and defense ratings, as it should be).")
    out.append(""); out.append("Tuned on 2013-18 (season refits, validation 2015-18): " + "; ".join(f"{m}: " + ", ".join(f"{t}/{s} {v}" for t in tn[m] for s, v in tn[m][t].items()) for m in tn))
    out.append("")
    # main table: spreads (points target)
    sp = R[R.target.isin(["points", "live"])].copy(); rows = []
    for (m, s), grp in sp.groupby(["model", "features"], sort=False):
        x = grp.set_index("window")
        rows.append({"model": m, "features": s, **{f"team MAE/RMSE {w}": f"{x.loc[w, 'team_mae']:.3f} / {x.loc[w, 'team_rmse']:.3f}" for w in W},
                     **{f"margin MAE/RMSE {w}": f"{x.loc[w, 'margin_mae']:.3f} / {x.loc[w, 'margin_rmse']:.3f}" for w in W}, **{f"4+ {w}": x.loc[w, "spread4"] for w in W}})
    out += ["### Spreads: team points and margin (model of each team's points)", "", tbl(pd.DataFrame(rows)), ""]
    rows = []
    for (m, s, t), grp in R[R.total_mae.notna() & ~R.model.str.startswith("stack") & (R.model != "the closing line")].groupby(["model", "features", "target"], sort=False):
        x = grp.set_index("window")
        rows.append({"model": m, "features": s, "target": t, **{f"total MAE/RMSE {w}": f"{x.loc[w, 'total_mae']:.3f} / {x.loc[w, 'total_rmse']:.3f}" for w in W}, **{f"under 3+ {w}": x.loc[w, "under3"] for w in W}})
    out += ["### Totals (the total direct, and the sum of the two team scores)", "", tbl(pd.DataFrame(rows)), ""]
    cl = R[R.model == "the closing line"].set_index("window")
    out += ["The closing line for scale: margin MAE/RMSE " + ", ".join(f"{w} {cl.loc[w, 'margin_mae']:.3f} / {cl.loc[w, 'margin_rmse']:.3f}" for w in W) +
            "; total " + ", ".join(f"{w} {cl.loc[w, 'total_mae']:.3f} / {cl.loc[w, 'total_rmse']:.3f}" for w in W) + ".", ""]
    for isp in (True, False):
        rows = []
        for (m, s, t), grp in R[R.model.str.startswith("stack") & R.target.str.endswith("spread" if isp else "total")].groupby(["model", "features", "target"], sort=False):
            x = grp.set_index("window"); k = "margin_mae" if isp else "total_mae"; b = "spread4" if isp else "under3"
            rows.append({"blend": m, "features": s, "ML target": t.split("/")[0], "w (2015-18)": x.stack_w.iloc[0], **{f"{'margin' if isp else 'total'} MAE {w}": round(x.loc[w, k], 3) for w in W},
                         **{f"{'4+' if isp else 'under 3+'} {w}": x.loc[w, b] for w in W}})
        out += [f"### Stacked blends, {'spread' if isp else 'total'}: live + w x (model - live), w on a 0.05 grid fitted on 2015-18 by MAE", "",
                "Live for reference: " + ", ".join(f"{w} {L.loc[w, 'margin_mae' if isp else 'total_mae']:.3f} ({L.loc[w, 'spread4' if isp else 'under3']})" for w in W), "", tbl(pd.DataFrame(rows)), ""]
    s2 = STY[~STY.model.str.startswith("stack")].copy()
    def cell(r, w):
        return f"{r[f'acc_{w}']:.3f} ({int(r[f'n_{w}'])})" if pd.notna(r.get(f"acc_{w}")) else "-"
    out += ["### The study's style: accuracy of the model's side when the edge is at least a share of the line", "",
            "Totals: shares 0 to 10% of the total line (0.5% steps); spreads: 0 to 50% of the spread line (5% steps); weeks 1-17, pushes out. "
            "\"Look-ahead\" is what the study reports: the best share over 2015-25 pooled with 500+ bets, chosen after seeing every "
            "result. \"Picked on 2015-18\" chooses the share on 2015-18 only (at least 182 bets there: 500 pro-rated to four of eleven "
            "seasons) and reports every window at that share, accuracy (bets); only 2019-22 and 2023-25 are out of sample. Break-even at -110 is 52.4%.", ""]
    for mk in ("totals", "spreads"):
        x = s2[s2.market == mk]
        rows = [{"model": r["model"], "features": r["features"], "target": r["target"], "RMSE 2015-25": round(r["rmse_2015_25"], 2), "acc, every game": f"{r['acc_at_0_pooled']:.3f}",
                 "look-ahead best (share, acc, bets)": f"{r['lookahead_best_frac']:g}, {r['lookahead_best_acc']:.3f}, {int(r['lookahead_n'])}" if pd.notna(r["lookahead_best_frac"]) else "-",
                 "share picked on 2015-18": f"{r['picked_frac_2015_18']:g}", **{w: cell(r, w) for w in W}} for r in x.to_dict("records")]
        out += [f"**{mk.capitalize()}**", "", tbl(pd.DataFrame(rows)), ""]
    if runtimes:
        out += ["### Runtimes", "", "\n".join(f"- {k}: {v}" for k, v in runtimes.items()), ""]
    ok_sp = AD[AD.adopt_spread == True]; ok_t = AD[AD.adopt_total == True]
    out += ["### Verdict against the rule", "", f"Passing on spreads: {', '.join(f'{r.model} / {r.features} / {r.target}' for r in ok_sp.itertuples()) or 'none'}. "
            f"Passing on totals: {', '.join(f'{r.model} / {r.features} / {r.target}' for r in ok_t.itertuples()) or 'none'}.", ""]
    (REP / "ml_compare.md").write_text(md.rstrip("\n") + "\n\n" + "\n".join(out))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("stage"); ap.add_argument("--model"); ap.add_argument("--targets", default="points,total")
    a = ap.parse_args(); t0 = time.time()
    {"frames": frames, "fs": forward, "time": timing, "report": report}.get(a.stage, lambda: None)()
    if a.stage == "tune":
        tune(a.model)
    if a.stage == "run":
        run(a.model, a.targets.split(","))
    log(f"stage {a.stage} {a.model or ''} {a.targets if a.stage == 'run' else ''}: {time.time() - t0:.0f}s")
