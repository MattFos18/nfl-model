"""Input ablation (3 Oct 2026, Matt: "ensure everything used in the predictions earns its spot fully and accurately, not
biased, no cheating, no errors"). Pre-registration and results: reports/input_ablation.md.

Every live piece of the prediction, the model with against without it, on main's honest backtest:
  P1-P22  each input of model.FEATS (the points equations, every blend member), dropped and refit (team points miss)
  T1-T11  each input of model.TOTAL_FEATS, dropped and refit (total miss)
  B1-B7   each model of the blend (BLEND_LABEL) left out of the average (team points miss)
  W1      wind points (total miss); S1 the share-out of the total to the two teams (team points miss)
  C1-C5   the cover, over, home win and teaser (spread, total) calibrations against the raw chance (log loss)
Each scored through nflmodel.study_gate (base = without the piece, new = live) with the spread flag, totals flag and wind
under records and 50 within-season placebo draws of that piece (refit for P and T). Walk-forward 2015-2025 with
model.walk_forward; trees refit wherever their inputs change; data/processed/trees_cache.parquet is never written.
The P and T placebo draws refit only the equation the shuffle touches (fast_totals / fast_points, the same weekly loop as
walk_forward; check_fast shows them equal to walk_forward to 0.0). Intermediate runs and draws are kept in
<tmp>/input_ablation so an interrupted run resumes (--max-draws N: one bounded batch of draws, then stop).
Writes reports/input_ablation.csv and reports/input_ablation_results.md; --combined writes reports/input_ablation_combined.md.

    python -m experiments.input_ablation [--workers 10] [--max-draws N] [--combined P7,P8,...]
"""
from __future__ import annotations
import os
for _v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):   # one thread a process: the draws run in parallel
    os.environ.setdefault(_v, "1")
import json, sys, tempfile, time
from pathlib import Path
import numpy as np, pandas as pd
from nflmodel import backtest as B, model as M, picks as P, study_gate as G
from nflmodel.features import OUT, ROOT

M.save_trees_cache = lambda: None   # an experiment never rewrites data/processed/trees_cache.parquet
from experiments import forecast_weather_backtest as FW   # noqa: E402  (wind amounts, re-pricing, scoring)
from experiments import calibration_recheck as CR          # noqa: E402  (calibration rows)

REP = ROOT / "reports"
TMP = Path(tempfile.gettempdir()) / "input_ablation"
WIN = {"2015-18": (2015, 2018), "2019-22": (2019, 2022), "2023-25": (2023, 2025)}
GAMES = pd.read_parquet(OUT / "games.parquet")
NPLAC, SEED = 50, 3103
FEATS_LIVE, TOTAL_LIVE = list(M.FEATS), list(M.TOTAL_FEATS)
_PREP, _PW, _GF = M.prep, M.priced_weather, M._game_frame
GAME_LEVEL = {"neutral", "dome", "wind_out", "cold", "rain", "div_game"}
# each totals input and the team-game column it is built from (model._game_frame)
TOTAL_SRC = {"off_sum": "off_epa_play", "def_sum": "def_epa_play", "pf_sum": "off_pf", "pa_sum": "def_pf", "qb_sum": "qb_rating",
             "qb_out_sum": "qb_out", "wind_out": "wind_out", "rain_fc": "rain_fc", "cold": "cold", "dome": "dome", "qb_form_sum": "qb_form"}
PIECES = ([(f"P{i + 1}", "points", c) for i, c in enumerate(FEATS_LIVE)] + [(f"T{i + 1}", "total", c) for i, c in enumerate(TOTAL_LIVE)] +
          [(f"B{i + 1}", "blend", k) for i, k in enumerate(M.BLEND_LABEL)] + [("W1", "wind", "wind points"), ("S1", "share", "share-out")] +
          [("C1", "cal", "cover"), ("C2", "cal", "over"), ("C3", "cal", "home win"), ("C4", "cal", "teaser spread leg"), ("C5", "cal", "teaser total leg")])
LABEL = {k: f"{k} {c}" for k, _, c in PIECES}
LABEL.update({f"B{i + 1}": f"B{i + 1} {v}" for i, v in enumerate(M.BLEND_LABEL.values())})
LABEL.update({"T8": "T8 rain_fc (RAIN_FC)", "T11": "T11 qb_form_sum (QB form)", "B7": "B7 Boosted trees"})


# ---- shuffles: one permutation per draw, applied to the prepared rows and to the priced rows alike --------------------
_ST: dict = {}


def _perm(g: pd.DataFrame, level: str, seed: int) -> np.ndarray:
    """Row positions: row i takes its value from row perm[i]; within season, by team-game or by whole game (home row from
    the donor game's home row)."""
    rng = np.random.default_rng(seed); n = len(g)
    if level == "team":
        return G.shuffle_within_season(np.arange(n), g.season.values, rng).astype(int)
    gid = g.game_id.values; gm = pd.DataFrame({"game_id": gid, "season": g.season.values}).drop_duplicates("game_id")
    donor = dict(zip(gm.game_id, gm.game_id.values[G.shuffle_within_season(np.arange(len(gm)), gm.season.values, rng).astype(int)]))
    pos = {(k, h): i for i, (k, h) in enumerate(zip(gid, g.home.values))}
    return np.array([pos.get((donor[k], h), i) for i, (k, h) in enumerate(zip(gid, g.home.values))], dtype=int)


def _shuffled(g: pd.DataFrame) -> pd.DataFrame:
    spec = _ST.get("spec")
    if spec is None:
        return g
    target, col, perm = spec["target"], spec["col"], _ST["perm"]
    g = g.copy()
    if target == "points":   # the points equations read col__sh (run() swaps the name in FEATS); totals and structure keep col
        g[col + "__sh"] = g[col].values[perm]
    else:                    # the totals equation reads col__tot (_game_frame below); the points equations keep col
        g[col + "__tot"] = g[col].values[perm]
    return g


def _prep(f):
    g = _PREP(f); _ST["raw"] = g
    if _ST.get("spec") is not None:
        _ST["perm"] = _perm(g, _ST["spec"]["level"], _ST["spec"]["seed"])
    return _shuffled(g)


def _priced(f):
    return _shuffled(_PW(_ST["raw"])) if _ST.get("spec") is not None else _PW(f)


def _game_frame(f):
    tot = [c for c in f.columns if c.endswith("__tot")]
    if tot:
        f = f.copy()
        for c in tot:
            f[c[:-5]] = f[c].values
    return _GF(f)


M.prep, M.priced_weather, M._game_frame = _prep, _priced, _game_frame
_F = None


def feats() -> pd.DataFrame:
    global _F
    if _F is None:
        _F = M.with_trends(pd.read_parquet(OUT / "features_asof.parquet"))
    return _F


def run(drop_feat=None, drop_total=None, spec=None) -> pd.DataFrame:
    """The live model refit walk-forward 2015-2025, with one input dropped or one input shuffled (spec)."""
    sh = spec["col"] if spec is not None and spec["target"] == "points" else None
    M.FEATS[:] = [c + "__sh" if c == sh else c for c in FEATS_LIVE if c != drop_feat]; M.TOTAL_FEATS[:] = [c for c in TOTAL_LIVE if c != drop_total]
    _ST.clear(); _ST["spec"] = spec; M.DIST.clear()
    try:
        p = M.walk_forward(feats(), range(2015, 2026), M.RIDGE)
        _ST["tres"] = {k: v["tres"] for k, v in M.DIST.items()}
    finally:
        M.FEATS[:] = FEATS_LIVE; M.TOTAL_FEATS[:] = TOTAL_LIVE; _ST["spec"] = None
    return p


def _reset_trees():
    M.TREES_CACHE = TMP / "trees_base.parquet"; M._TC.update({"df": None, "used": set(), "new": []})


def quick_miss(p) -> dict:
    d = B.join(p, GAMES); d = d[(d.game_type == "REG")]
    return {w: {"team": float(np.r_[x.home_err.abs(), x.away_err.abs()].mean()), "total": float(x.total_err.abs().mean())}
            for w, (lo, hi) in WIN.items() for x in [d[d.season.between(lo, hi)]]}


# ---- fast refits for the placebo draws: only the equation the shuffle touches is refit (walk_forward's own weekly loop,
# the same rows, order and fits); checked against model.walk_forward to 1e-9 (check_fast) before any draw is used ---------
def _frames(spec):
    """walk_forward's training rows (prep) and priced rows (priced_weather), with spec's shuffle."""
    _ST.clear(); _ST["spec"] = spec
    try:
        f = M.prep(feats()); played = f[f.pf.notna()]; fpr = M.priced_weather(f)
    finally:
        _ST["spec"] = None
    return played, fpr


def fast_totals(spec=None, drop=None) -> pd.DataFrame:
    """model_total (wind points in) and p_over_emp for every 2015-2025 game: the totals equation refit every week as
    walk_forward does (model.total_model on the same games), the wind pool built the same way."""
    from sklearn.linear_model import Ridge
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    played, fpr = _frames(spec)
    tf = [c for c in TOTAL_LIVE if c != drop]
    GP, GT = M._game_frame(played), M._game_frame(fpr)
    hp = played[played.home == 1].set_index("game_id"); gs = hp.season.reindex(GP.index).values; gw = hp.week.reindex(GP.index).values
    _h, _a = played[played.home == 1].set_index("game_id"), played[played.home == 0].set_index("game_id")
    act = (_h.pf + _a.pf.reindex(_h.index)).dropna().to_dict()
    wind = M._wind_readings(); wpool, out = {}, []
    for s in range(2015, 2026):
        test_all = fpr[fpr.season == s]
        for wk in sorted(test_all.week.unique()):
            te_rows = test_all[test_all.week == wk]
            h = te_rows[te_rows.home == 1].set_index("game_id"); a = te_rows[te_rows.home == 0].set_index("game_id")
            ids = h.index.intersection(a.index)
            if len(ids) == 0:
                continue
            tr = GP[(gs >= M.TRAIN_FROM) & ((gs < s) | ((gs == s) & (gw < wk)))]
            m = make_pipeline(StandardScaler(), Ridge(alpha=10.0)).fit(tr[tf].values, tr.total.values)
            raw = m.predict(GT.loc[ids, tf].values); tres = tr.total.values - m.predict(tr[tf].values)
            pool_ = [x for s_, v in wpool.items() if s_ < s for x in v]
            fw = pd.Series(ids).map(wind).astype(float).values
            mt = raw + np.array([M.wind_points(pool_, x) for x in fw])
            tl = h.loc[ids, "total_line"].values
            pe = [float(np.mean(t + tres > l) / max(1e-9, np.mean(t + tres != l))) if pd.notna(l) else np.nan for t, l in zip(mt, tl)]
            out.append(pd.DataFrame({"game_id": ids, "model_total": mt, "p_over_emp": pe}))
            for gid, x, r, gt in zip(ids, fw, raw, h.loc[ids, "game_type"].values):
                if pd.notna(x) and gt == "REG" and gid in act:
                    wpool.setdefault(s, []).append((float(x), float(act[gid]) - float(r)))
    return pd.concat(out, ignore_index=True)


def fast_points(spec=None, drop=None) -> pd.DataFrame:
    """model_spread and each blend member for every 2015-2025 game: the seven points models refit every week as
    walk_forward does (model.fit_blend / predict_blend on the same rows; trees fit fresh, one thread)."""
    from sklearn.ensemble import HistGradientBoostingRegressor
    from sklearn.linear_model import Ridge
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    from threadpoolctl import threadpool_limits
    played, fpr = _frames(spec)
    sh = spec["col"] if spec is not None and spec["target"] == "points" else None
    fe = [c + "__sh" if c == sh else c for c in FEATS_LIVE if c != drop]
    out = []
    with threadpool_limits(limits=1):
        for s in range(2015, 2026):
            test_all = fpr[fpr.season == s]
            for wk in sorted(test_all.week.unique()):
                train = played[(played.season >= M.TRAIN_FROM) & ((played.season < s) | ((played.season == s) & (played.week < wk)))]
                test = test_all[test_all.week == wk]; y = train.pf.values
                allc = sorted(set(fe) | {c for ex, _ in M.BLEND.values() for c in ex}); mu = train[allc].mean()
                pr = {}
                m = make_pipeline(StandardScaler(), Ridge(alpha=M.RIDGE)).fit(train[fe].values, y)
                pr["ridge"] = m.predict(test[fe].fillna(mu[fe]).values)
                for k, (extra, al) in M.BLEND.items():
                    cols = fe + extra
                    m = make_pipeline(StandardScaler(), Ridge(alpha=al)).fit(train[cols].fillna(train[cols].mean()).values, y)
                    pr[k] = m.predict(test[cols].fillna(mu[cols]).values)
                t = HistGradientBoostingRegressor(**M.TREES).fit(train[fe].values, y)
                pr["trees"] = t.predict(test[fe].fillna(mu[fe]).values)
                bl = np.mean([pr[k] for k in M.BLEND_LABEL], axis=0)
                x = pd.DataFrame({"game_id": test.game_id.values, "home": test.home.values, "blend": bl, **{f"m_{k}": pr[k] for k in M.BLEND_LABEL}})
                h = x[x.home == 1].set_index("game_id"); a = x[x.home == 0].set_index("game_id"); ids = h.index.intersection(a.index)
                if len(ids) == 0:
                    continue
                g = pd.DataFrame({"game_id": ids, "model_spread": (h.loc[ids, "blend"] - a.loc[ids, "blend"]).values})
                for k in M.BLEND_LABEL:
                    g[f"home_m_{k}"], g[f"away_m_{k}"] = h.loc[ids, f"m_{k}"].values, a.loc[ids, f"m_{k}"].values
                out.append(g)
    return pd.concat(out, ignore_index=True)


def merged(base, tot=None, pts=None) -> pd.DataFrame:
    """The baseline table with a fast refit's total or spread in place; team points re-shared."""
    q = base.copy()
    if tot is not None:
        t = tot.set_index("game_id"); q["model_total"] = q.game_id.map(t.model_total); q["p_over_emp"] = q.game_id.map(t.p_over_emp)
    if pts is not None:
        q["model_spread"] = q.game_id.map(pts.set_index("game_id").model_spread)
    q["home_exp"] = (q.model_total + q.model_spread) / 2; q["away_exp"] = (q.model_total - q.model_spread) / 2
    return q


def check_fast() -> dict:
    """The fast refits against model.walk_forward: the baseline, one dropped input of each kind; max abs differences."""
    base = pd.read_parquet(TMP / "base.parquet").set_index("game_id")
    ft, fp = fast_totals().set_index("game_id"), fast_points().set_index("game_id")
    vt, vp = pd.read_parquet(TMP / "var_T8.parquet").set_index("game_id"), pd.read_parquet(TMP / "var_P10.parquet").set_index("game_id")
    dt, dp = fast_totals(drop="rain_fc").set_index("game_id"), fast_points(drop="cold").set_index("game_id")
    d = lambda x, y, c: float(np.nanmax(np.abs(x[c].values - y[c].reindex(x.index).values)))
    out = {"base model_total": d(ft, base, "model_total"), "base p_over_emp": d(ft, base, "p_over_emp"), "base model_spread": d(fp, base, "model_spread"),
           "base home_m_trees": d(fp, base, "home_m_trees"), "T8 model_total": d(dt, vt, "model_total"), "T8 p_over_emp": d(dt, vt, "p_over_emp"),
           "P10 model_spread": d(dp, vp, "model_spread"), "games": (len(ft), len(fp), len(base))}
    return out


def job_variant(args):
    """A full drop-one run, saved to TMP."""
    key, kind, col = args
    out = TMP / f"var_{key}.parquet"
    if not out.exists():
        _reset_trees()
        p = run(drop_feat=col if kind == "points" else None, drop_total=col if kind == "total" else None)
        tmp = out.with_suffix(".part"); p.to_parquet(tmp, index=False); tmp.replace(out)
    return key


_B = None


def _base() -> pd.DataFrame:
    global _B
    if _B is None:
        _B = pd.read_parquet(TMP / "base.parquet")
    return _B


def job_placebo(args):
    """One placebo draw of a P or T piece: the input shuffled within season, the model refit; the two misses kept."""
    key, kind, col, i = args
    out = TMP / "plac" / f"{key}_{i:02d}.json"
    if not out.exists():
        _reset_trees()
        src = col if kind == "points" else TOTAL_SRC[col]
        level = ("game" if col in GAME_LEVEL else "team") if kind == "points" else "game"
        seed = SEED * 100000 + [k for k, _, _ in PIECES].index(key) * 1000 + i
        spec = {"target": kind, "col": src, "level": level, "seed": seed}
        base = _base()   # only the equation the shuffle touches is refit (fast_totals / fast_points = walk_forward, check_fast)
        p = merged(base, tot=fast_totals(spec)) if kind == "total" else merged(base, pts=fast_points(spec))
        tmp = out.with_suffix(".part"); tmp.write_text(json.dumps(quick_miss(p))); tmp.replace(out)   # whole files only (a run can be stopped)
    return key, i


# ---- post-hoc pieces --------------------------------------------------------------------------------------------------
def with_points(p, home, away) -> pd.DataFrame:
    """The table with each team's points equation number replaced (blend members): spread re-made, the total shared out."""
    q = p.copy(); q["model_spread"] = home - away
    q["home_exp"] = (q.model_total + q.model_spread) / 2; q["away_exp"] = (q.model_total - q.model_spread) / 2
    return q


def blend_without(p, k, member=None):
    ks = [x for x in M.BLEND_LABEL if x != k]
    h = p[[f"home_m_{x}" for x in ks]].mean(axis=1); a = p[[f"away_m_{x}" for x in ks]].mean(axis=1)
    if member is not None:   # the member's predictions put back shuffled (placebo)
        h = (h * len(ks) + member[0]) / (len(ks) + 1); a = (a * len(ks) + member[1]) / (len(ks) + 1)
    return with_points(p, h.values, a.values)


def team_shuffle(p, hcol, acol, rng):
    """A team-game column shuffled among the season's team-games (home and away rows pooled)."""
    v = np.r_[p[hcol].values, p[acol].values]; s = np.r_[p.season.values, p.season.values]
    x = G.shuffle_within_season(v, s, rng); n = len(p)
    return x[:n], x[n:]


def no_share(p, shift=None) -> pd.DataFrame:
    q = p.copy(); sh = 0.0 if shift is None else shift
    q["home_exp"] = q.home_pts_eq + sh; q["away_exp"] = q.away_pts_eq + sh
    return q


def cal_sets(p) -> dict:
    """C1-C5: rows with raw and calibrated chance and the outcome, each season on the fit in force (calibration_recheck)."""
    return {"C1": CR.cover_rows(p),
            "C2": CR.logit_rows(P._over_rows(p, GAMES), "over", P.over_calibrations(p, GAMES)),
            "C3": CR.logit_rows(P._home_rows(p, GAMES), "hw", P.home_calibrations(p, GAMES)),
            "C4": CR.logit_rows(P._tease_rows(p, GAMES), "hit", P.tease_calibrations(p, GAMES), "spread"),
            "C5": CR.logit_rows(P._tease_rows(p, GAMES), "hit", P.tease_calibrations(p, GAMES), "total")}


plac_na: set = set()   # pieces whose placebo is not defined (filled in main)
CWIN = {"2015-18": (2016, 2018), "2019-22": (2019, 2022), "2023-25": (2023, 2025)}


def cal_scores(key, d, pcol="cal"):
    ll, br = {}, {}
    for w, (lo, hi) in CWIN.items():
        x = d[d.season.between(lo, hi)]
        if key == "C3" and w == "2015-18":
            x = x[x.season >= 2017]   # 2016's home calibration is the identity (under 500 games), as calibration_recheck
        ll[w], br[w] = CR.scores(x[pcol], x.y)
    return ll, br


def _logit(p):
    q = np.clip(np.asarray(p, float), 1e-6, 1 - 1e-6); return np.log(q / (1 - q))


# ---- scoring and verdicts ---------------------------------------------------------------------------------------------
def rec(t):
    return "%d-%d" % tuple(t)


def verdict(rows) -> str:
    """Pre-registered: earns its spot (gate passes), fails (no better with it on 2+ windows, or worse on a window and
    beaten by its placebo on 2+ windows), thin (the rest)."""
    if G.passes(rows):
        return "earns its spot"
    better = {c[len("better on "):]: o for c, o, _ in rows if c.startswith("better on ")}
    plac = [o for c, o, _ in rows if c.startswith("beats its placebo")]
    lost = sum(not o for o in better.values())
    if lost >= 2 or (lost >= 1 and sum(not o for o in plac) >= 2):
        return "fails"
    return "thin"


def drop_costs_wins(base, var) -> list[str]:
    """Records whose wins minus losses are lower without the piece (base = live, var = without) on some window."""
    out = []
    for w in WIN:
        for r in ("spread", "totals", "wind"):
            (wb, lb), (wv, lv) = base[w][r], var[w][r]
            if wv - lv < wb - lb:
                out.append(f"{r} {w} {wb}-{lb} -> {wv}-{lv}")
    return out


def main():
    TMP.mkdir(exist_ok=True); (TMP / "plac").mkdir(exist_ok=True)
    nw = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else 10
    t0 = time.time()
    base_f = TMP / "base.parquet"
    if not base_f.exists():
        M.TREES_CACHE = TMP / "none.parquet"; M._TC.update({"df": None, "used": set(), "new": []})
        p = run(); p.to_parquet(base_f, index=False)
        pd.to_pickle(_ST["tres"], TMP / "base_tres.pkl")
        pd.concat(M._TC["new"], ignore_index=True).drop_duplicates(["key", "game_id", "team"]).to_parquet(TMP / "trees_base.parquet", index=False)
        print(f"baseline done {time.time() - t0:.0f}s", flush=True)
    base = pd.read_parquet(base_f); tres = pd.read_pickle(TMP / "base_tres.pkl")
    model_pieces = [(k, kind, c) for k, kind, c in PIECES if kind in ("points", "total")]
    from concurrent.futures import ProcessPoolExecutor
    combined = sys.argv[sys.argv.index("--combined") + 1].split(",") if "--combined" in sys.argv else None
    with ProcessPoolExecutor(nw) as ex:
        # totals variants first (trees read back from the baseline's fits), then the points variants, then the draws
        todo = [a for a in model_pieces if a[1] == "total"] + [a for a in model_pieces if a[1] == "points"]
        for k in ex.map(job_variant, todo):
            print("variant", k, f"{time.time() - t0:.0f}s", flush=True)
        draws = [(k, kind, c, i) for k, kind, c in sorted(model_pieces, key=lambda a: a[1] != "total") for i in range(NPLAC)]
        draws = [d for d in draws if not (TMP / "plac" / f"{d[0]}_{d[3]:02d}.json").exists()]
        if "--max-draws" in sys.argv:   # a bounded batch (the draws resume from the files already written)
            n_max = int(sys.argv[sys.argv.index("--max-draws") + 1])
            if len(draws) > n_max:
                list(ex.map(job_placebo, draws[:n_max], chunksize=1))
                print(f"batch done; {len(draws) - n_max} draws left", flush=True)
                return
        for n, (k, i) in enumerate(ex.map(job_placebo, draws, chunksize=1)):
            if n % 25 == 0:
                print("placebo", k, i, f"{n + 1}/{len(draws)}", f"{time.time() - t0:.0f}s", flush=True)
    sc_base = FW.score(base); bmiss = quick_miss(base)
    res, csv = {}, []
    for k, kind, c in PIECES:
        key = "team" if kind in ("points", "blend", "share") else "total"
        if kind in ("points", "total"):
            var = pd.read_parquet(TMP / f"var_{k}.parquet"); sv = FW.score(var); vm = quick_miss(var)
            ds = [json.loads((TMP / "plac" / f"{k}_{i:02d}.json").read_text()) for i in range(NPLAC)]
            plac = {w: [vm[w][key] - d[w][key] for d in ds] for w in WIN}
        elif kind == "blend":
            sv = FW.score(blend_without(base, c)); vm = quick_miss(blend_without(base, c)); rng = np.random.default_rng(SEED + 7 * len(res))
            plac = {w: [] for w in WIN}
            for i in range(NPLAC):
                dm = quick_miss(blend_without(base, c, team_shuffle(base, f"home_m_{c}", f"away_m_{c}", rng)))
                for w in WIN:
                    plac[w].append(vm[w][key] - dm[w][key])
        elif kind == "wind":
            nw_ = FW.apply(base, tres, np.zeros(len(base))); sv = FW.score(nw_); vm = quick_miss(nw_)
            rng = np.random.default_rng(SEED + 1); wind = FW.WL.readings(); gid = base[base.wind_fc.notna()][["game_id", "season"]]
            plac = {w: [] for w in WIN}
            for i in range(NPLAC):
                sh = dict(zip(gid.game_id, G.shuffle_within_season(gid.game_id.map(wind).values, gid.season.values, rng)))
                dm = FW.misses(base.assign(wind_fc=base.game_id.map(sh).astype(float)), FW.wind_amounts(base, "bands", sh))
                for w in WIN:
                    plac[w].append(vm[w][key] - dm[w][key])
        elif kind == "share":
            ns = no_share(base); sv = FW.score(ns); vm = quick_miss(ns); rng = np.random.default_rng(SEED + 2)
            shift = (base.home_exp - base.home_pts_eq).values; plac = {w: [] for w in WIN}
            for i in range(NPLAC):
                dm = quick_miss(no_share(base, G.shuffle_within_season(shift, base.season.values, rng)))
                for w in WIN:
                    plac[w].append(vm[w][key] - dm[w][key])
        if kind == "cal":
            d = cal_sets(base)[k]; ll, br = cal_scores(k, d, "cal"); llr, brr = cal_scores(k, d, "raw")
            adj = _logit(d.cal) - _logit(d.raw); rng = np.random.default_rng(SEED + 10 + int(k[1:])); plac = {w: [] for w in WIN}
            for i in range(NPLAC):
                dd = d.assign(pl=1.0 / (1.0 + np.exp(-(_logit(d.raw) + G.shuffle_within_season(adj, d.season.values, rng)))))
                lp, _ = cal_scores(k, dd, "pl")
                for w in WIN:
                    plac[w].append(llr[w] - lp[w])
            miss = {w: (llr[w], ll[w]) for w in WIN}
            rows = G.gate(miss, {w: {"spread flag": (sc_base[w]["spread"],) * 2, "totals flag": (sc_base[w]["totals"],) * 2, "wind under": (sc_base[w]["wind"],) * 2} for w in WIN},
                          plac, calibration={w: (brr[w], br[w]) for w in WIN})
            if all(np.ptp(adj[d.season.values == s]) < 1e-9 for s in np.unique(d.season.values)):
                # a shift-only calibration (the teaser spread leg): one adjustment per season, so a within-season shuffle
                # is the identity and the placebo is not defined (audit, 3 Oct 2026); scored on parts 1 and 2 only
                rows = [(c, True, "not defined: one shift per season, a within-season shuffle changes nothing") if c.startswith("beats its placebo") else (c, o, dt)
                        for c, o, dt in rows]
                plac_na.add(k)
            sv = sc_base
        else:
            miss = {w: (vm[w][key], bmiss[w][key]) for w in WIN}
            rows = G.gate(miss, {w: {"spread flag": (sv[w]["spread"], sc_base[w]["spread"]), "totals flag": (sv[w]["totals"], sc_base[w]["totals"]),
                                     "wind under": (sv[w]["wind"], sc_base[w]["wind"])} for w in WIN}, plac)
        v = verdict(rows); cost = drop_costs_wins(sc_base, sv)
        res[k] = {"kind": kind, "label": LABEL[k], "key": "log loss" if kind == "cal" else key, "miss": miss, "rows": rows, "verdict": v, "sv": sv, "cost": cost, "plac": plac}
        for w in WIN:
            real = miss[w][0] - miss[w][1]
            csv.append({"piece": LABEL[k], "group": kind, "scored_on": res[k]["key"], "window": w, "miss_without": round(miss[w][0], 5), "miss_with": round(miss[w][1], 5),
                        "gain": round(real, 5), "placebo_beaten": ("not defined" if k in plac_na else int((real > np.asarray(plac[w])).sum())), "placebo_p90": round(float(np.percentile(plac[w], 90)), 5),
                        "spread_without": rec(sv[w]["spread"]), "spread_with": rec(sc_base[w]["spread"]), "totals_without": rec(sv[w]["totals"]),
                        "totals_with": rec(sc_base[w]["totals"]), "wind_without": rec(sv[w]["wind"]), "wind_with": rec(sc_base[w]["wind"]),
                        "gate_pass": G.passes(rows), "verdict": v, "drop_costs_wins": "; ".join(cost)})
        print(LABEL[k], v, flush=True)
    pd.DataFrame(csv).to_csv(REP / "input_ablation.csv", index=False)
    cand = [k for k, r in res.items() if r["verdict"] == "fails" and not r["cost"] and r["kind"] in ("points", "total", "blend", "wind", "share")]
    print("drop candidates (fail, no flag cost):", cand, flush=True)
    write_md(res, sc_base, bmiss, cand)
    if combined:
        run_combined(combined, sc_base, bmiss)
    print(f"done {time.time() - t0:.0f}s; variants: 1 baseline + {len(PIECES)} drop-one + {len(PIECES) * NPLAC} placebo draws", flush=True)


def write_md(res, sc_base, bmiss, cand):
    L = ["# Input ablation: results (written by experiments/input_ablation.py)", "",
         "Live model refit walk-forward 2015-2025 on main (regular season scored; flags weeks 1-17 at the close, -110).", "",
         "| Window | Team miss | Total miss | Spread flag | Totals flag | Wind under |", "|---|---|---|---|---|---|"]
    L += [f"| {w} | {bmiss[w]['team']:.4f} | {bmiss[w]['total']:.4f} | {rec(sc_base[w]['spread'])} | {rec(sc_base[w]['totals'])} | {rec(sc_base[w]['wind'])} |" for w in WIN]
    L += ["", "## Summary (gain = miss without minus miss with; placebo = draws beaten of 50)", "",
          "| Piece | Scored on | Gain 2015-18 | Gain 2019-22 | Gain 2023-25 | Bet records without it (spread / totals flag) | Placebo | Verdict | Dropping costs flag wins |",
          "|---|---|---|---|---|---|---|---|---|"]
    for k, r in res.items():
        g = [r["miss"][w][0] - r["miss"][w][1] for w in WIN]
        pl = " / ".join(str(int((r["miss"][w][0] - r["miss"][w][1] > np.asarray(r["plac"][w])).sum())) for w in WIN)
        pl = "not defined" if k in plac_na else pl
        bt = "unchanged" if r["kind"] == "cal" else " / ".join(f"{rec(r['sv'][w]['spread'])}, {rec(r['sv'][w]['totals'])}" for w in WIN)
        L.append(f"| {r['label']} | {r['key']} | {g[0]:+.4f} | {g[1]:+.4f} | {g[2]:+.4f} | {bt} | {pl} | {r['verdict']} | {'yes: ' + '; '.join(r['cost']) if r['cost'] else 'no'} |")
    L += ["", f"Drop candidates (verdict fails and dropping costs no flag wins): {', '.join(cand) if cand else 'none'}", ""]
    for k, r in res.items():
        L += [f"## {r['label']}: study_gate on {r['key']}", "", G.markdown(r["rows"]), ""]
    (REP / "input_ablation_results.md").write_text("\n".join(L) + "\n", encoding="utf-8")


def run_combined(keys, sc_base, bmiss):
    """Round-3 part 5: every piece to be dropped removed together, refit, against the live model on both misses."""
    kinds = {k: (kind, c) for k, kind, c in PIECES}
    feats_drop = [kinds[k][1] for k in keys if kinds[k][0] == "points"]; tot_drop = [kinds[k][1] for k in keys if kinds[k][0] == "total"]
    other = [k for k in keys if kinds[k][0] not in ("points", "total")]
    assert not other, f"combined run handles model inputs only: {other}"
    M.FEATS[:] = [c for c in FEATS_LIVE if c not in feats_drop]; M.TOTAL_FEATS[:] = [c for c in TOTAL_LIVE if c not in tot_drop]
    _ST.clear(); M.DIST.clear(); _reset_trees()
    try:
        p = M.walk_forward(feats(), range(2015, 2026), M.RIDGE)
    finally:
        M.FEATS[:] = FEATS_LIVE; M.TOTAL_FEATS[:] = TOTAL_LIVE
    p.to_parquet(TMP / f"combined_{'_'.join(keys)}.parquet", index=False)
    sv, vm = FW.score(p), quick_miss(p)
    L = [f"# Combined drop {', '.join(keys)} against the live model", ""]
    for key in ("team", "total"):
        rows = G.gate({w: (bmiss[w][key], vm[w][key]) for w in WIN},
                      {w: {"spread flag": (sc_base[w]["spread"], sv[w]["spread"]), "totals flag": (sc_base[w]["totals"], sv[w]["totals"]),
                           "wind under": (sc_base[w]["wind"], sv[w]["wind"])} for w in WIN})
        L += [f"## {key} miss (base = live, new = without)", "", G.markdown(rows), ""]
    (REP / "input_ablation_combined.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L), flush=True)


if __name__ == "__main__":
    main()
