"""Forecast weather in the backtest (2 Oct 2026, Matt: make the backtest "100% accurate, no cheating"; adopt what is
clearly better). Pre-registration and results: reports/forecast_weather_backtest.md.

A  the honest baseline: a played game with a stored forecast (2018 on) is priced on it (model.priced_weather: wind_out
   from the wind reading, cold from the GFS MOS temperature, the points equations' rain from the RAIN_FC reading), trained
   on the recorded weather, like a live fit. "recorded" is the old backtest (model.FORECAST_WEATHER = False).
B  on top of A, each of today's adoptions with and without it: B1 wind points, B2 rain_fc in the total, B3 qb_form_sum.
C  the wind points' curve: C1 a decreasing isotonic fit (blocks shrunk by K = 50 like the bands), C2 bands [0,8), [8,10),
   [10,15), 15+; against the current bands. Wind points and the curves are added after the walk-forward from the same pool
   the model builds (each season's amounts from earlier seasons only), checked to reproduce model.wind_points exactly.

Scored per window (2015-18 / 2019-22 / 2023-25, regular season): team points, total and margin miss; the spread flag
(4+), the totals flag (55%+ under) and the wind under (10+ mph), weeks 1-17; nflmodel.study_gate on team points miss and
on total miss; 50 within-season shuffles for what passes parts 1-2 (--placebo; B2 and B3 refit the model per draw on 6
processes, the trees read from this run's own fits, which are never written to data/processed/trees_cache.parquet).
Writes reports/forecast_weather_backtest.csv and the result tables to reports/forecast_weather_backtest_results.md.

    python -m experiments.forecast_weather_backtest [--placebo]
"""
from __future__ import annotations
import pickle, sys, tempfile
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.isotonic import IsotonicRegression
from nflmodel import backtest as B, model as M, picks as P, study_gate as G, wind_live as WL
from nflmodel.features import OUT, ROOT

REP = ROOT / "reports"
TMP = Path(tempfile.gettempdir()) / "forecast_weather_backtest"
WIN = {"2015-18": (2015, 2018), "2019-22": (2019, 2022), "2023-25": (2023, 2025)}
GAMES = pd.read_parquet(OUT / "games.parquet")
NPLAC, SEED, K = 50, 11, M.WIND_K
M.save_trees_cache = lambda: None   # an experiment never rewrites data/processed/trees_cache.parquet
TOTAL_LIVE = list(M.TOTAL_FEATS)
EDGES = {"bands": list(M.WIND_BANDS), "C2": [0.0, 8.0, 10.0, 15.0, float("inf")]}
_PREP = M.prep


def feats() -> pd.DataFrame:
    return M.with_trends(pd.read_parquet(OUT / "features_asof.parquet"))


def absorb() -> None:
    """Keep this run's fresh tree fits in memory, so the next run with the same inputs reads them back."""
    if M._TC["new"]:
        M._TC["df"] = pd.concat([M._trees_cache()] + M._TC["new"], ignore_index=True).drop_duplicates(["key", "game_id", "team"], keep="last")
        M._TC["new"] = []


def run(f, forecast=True, total_feats=None):
    M.FORECAST_WEATHER = forecast
    M.TOTAL_FEATS[:] = total_feats or TOTAL_LIVE
    M.DIST.clear()
    try:
        p = M.walk_forward(f, range(2015, 2026), M.RIDGE)
    finally:
        M.TOTAL_FEATS[:] = TOTAL_LIVE; M.FORECAST_WEATHER = True; M.prep = _PREP
    absorb()
    return p, {k: v["tres"] for k, v in M.DIST.items()}


ACT = None


def actual() -> pd.Series:
    global ACT
    if ACT is None:
        g = GAMES[GAMES.home_score.notna()]; ACT = pd.Series((g.home_score + g.away_score).values, index=g.game_id)
    return ACT


def _amounts(method, w, r, wt):
    """Wind amounts for test winds wt from the pool (w, r): r is actual minus the model's total before wind points."""
    c = r - r.mean()
    if method in EDGES:
        e = np.asarray(EDGES[method]); b = np.searchsorted(e, wt, side="right") - 1; bp = np.searchsorted(e, w, side="right") - 1
        s = pd.Series(c).groupby(bp).agg(["sum", "size"])
        return np.array([s["sum"].get(x, 0.0) / (s["size"].get(x, 0) + K) for x in b])
    if method == "C1":
        o = np.argsort(w, kind="stable"); ws, cs = w[o], c[o]
        fit = IsotonicRegression(increasing=False).fit_transform(ws, cs)
        blk = np.r_[0, np.cumsum(np.abs(np.diff(fit)) > 1e-12)]   # isotonic blocks: runs of equal fitted values
        bs = pd.Series(cs).groupby(blk).agg(["sum", "size"])
        i = np.clip(np.searchsorted(ws, wt, side="right") - 1, 0, len(ws) - 1)
        return np.array([bs["sum"][blk[j]] / (bs["size"][blk[j]] + K) for j in i])
    raise ValueError(method)


def wind_amounts(p, method="bands", wind=None) -> np.ndarray:
    """Each game's wind points, each season from the pool of earlier seasons' regular-season forecast games."""
    fw = (p.wind_fc if wind is None else p.game_id.map(wind)).astype(float).values
    r = (p.game_id.map(actual()) - p.model_total_raw).values
    pool = ~np.isnan(fw) & (p.game_type == "REG").values & ~np.isnan(r)
    out = np.zeros(len(p))
    for s in sorted(p.season.unique()):
        tr = pool & (p.season.values < s); te = (p.season.values == s) & ~np.isnan(fw)
        if tr.any() and te.any():
            out[te] = _amounts(method, fw[tr], r[tr], fw[te])
    return out


def apply(p, tres, amt) -> pd.DataFrame:
    """The prediction table with wind points amt in place of the run's: total, team points and the over chance re-priced."""
    q = p.copy(); q["wind_pts"] = amt; q["model_total"] = q.model_total_raw + amt
    q["home_exp"] = (q.model_total + q.model_spread) / 2; q["away_exp"] = (q.model_total - q.model_spread) / 2
    pe = []
    for s, w, mt, tl in zip(q.season, q.week, q.model_total, q.total_line):
        if pd.isna(tl):
            pe.append(np.nan); continue
        x = mt + tres[(int(s), int(w))]; pe.append(float(np.mean(x > tl) / max(1e-9, np.mean(x != tl))))
    q["p_over_emp"] = pe
    return q


def score(p) -> dict:
    d = B.join(p, GAMES); d = d[(d.game_type == "REG") & d.season.between(2015, 2025)]
    out = {}
    for w, (lo, hi) in WIN.items():
        x = d[d.season.between(lo, hi)]
        out[w] = {"team": float(np.r_[x.home_err.abs(), x.away_err.abs()].mean()), "total": float(x.total_err.abs().mean()),
                  "margin": float(x.margin_err.abs().mean()),
                  "spread": P.record(x, P.rule_mask(x, P.SPREAD_EDGE)),
                  "totals": P.record(x, P.rule_mask(x, P.TOTAL_SHADOW["prob"], "under_prob"), "under_prob"),
                  "wind": P.record(x, P.rule_mask(x, P.WIND_UNDER["mph"], "wind_under"), "wind_under")}
    return out


def misses(p, amt) -> dict:
    """Team points and total miss per window with wind points amt (placebo draws: no re-pricing needed)."""
    a = actual(); keep = (p.game_type == "REG").values & p.game_id.isin(a.index).values
    mt = p.model_total_raw.values + amt; hs = p.game_id.map(GAMES.set_index("game_id").home_score).values; as_ = p.game_id.map(GAMES.set_index("game_id").away_score).values
    he, ae = (mt + p.model_spread.values) / 2 - hs, (mt - p.model_spread.values) / 2 - as_; te = mt - p.game_id.map(a).values
    out = {}
    for w, (lo, hi) in WIN.items():
        m = keep & p.season.between(lo, hi).values
        out[w] = {"team": float(np.r_[np.abs(he[m]), np.abs(ae[m])].mean()), "total": float(np.abs(te[m]).mean())}
    return out


def gate_rows(base, new, key, placebo=None, wind_only=False):
    rows = G.gate({w: (base[w][key], new[w][key]) for w in WIN},
                  {w: {"spread flag": (base[w]["spread"], new[w]["spread"]), "totals flag": (base[w]["totals"], new[w]["totals"]),
                       "wind under": (base[w]["wind"], new[w]["wind"])} for w in WIN}, placebo,
                  fit_window="2015-18" if wind_only else None)
    if wind_only:   # wind points act from 2019 only (no earlier pool for 2018): 2015-18 is identical by construction
        rows = [(c, True, "not scored: the input is zero on every game (no earlier forecasts)") if c == "beats its placebo on 2015-18" else (c, o, d) for c, o, d in rows]
    return rows


def passes12(rows) -> bool:
    return all(o for c, o, _ in rows if not c.startswith("beats its placebo"))


# ---- placebo draws ---------------------------------------------------------------------------------------------------
def _shuffle_game_col(f, col, seed):
    rng = np.random.default_rng(seed); g = f[f.home == 1][["game_id", "season", col]].drop_duplicates("game_id")
    g[col] = G.shuffle_within_season(g[col].values, g.season.values, rng)
    return f.drop(columns=col).merge(g[["game_id", col]], on="game_id", how="left").assign(**{col: lambda x: x[col].fillna(0.0)})


def _job(args):
    what, seed = args
    M.TREES_CACHE = TMP / "trees.parquet"; M._TC.update({"df": None, "used": set(), "new": []})
    if what == "rain":
        M.prep = lambda f: _shuffle_game_col(_PREP(f), "rain_fc", seed)
    else:   # each team-game's qb_form shuffled among the season's team-games
        def pq(f, seed=seed):
            f = _PREP(f); f["qb_form"] = G.shuffle_within_season(f.qb_form.values, f.season.values, np.random.default_rng(seed)); return f
        M.prep = pq
    p, _ = run(feats())
    return misses(p, p.wind_pts.values)


def rec(t):
    return "%d-%d" % t


def table(res) -> list[str]:
    L = ["| Variant | Window | Team miss | Total miss | Margin miss | Spread flag (4+) | Totals flag (55% under) | Wind under (10+ mph) |", "|---|---|---|---|---|---|---|---|"]
    return L + [f"| {v} | {w} | {sc[w]['team']:.4f} | {sc[w]['total']:.4f} | {sc[w]['margin']:.4f} | {rec(sc[w]['spread'])} | {rec(sc[w]['totals'])} | {rec(sc[w]['wind'])} |"
                for v, sc in res.items() for w in WIN]


def main():
    TMP.mkdir(exist_ok=True); cache = TMP / "runs.pkl"
    if cache.exists():
        runs = pickle.loads(cache.read_bytes())
    else:
        f = feats(); runs = {}
        runs["recorded"] = run(f, forecast=False); print("recorded done", flush=True)
        runs["A"] = run(f); print("A done", flush=True)
        runs["A_no_rain"] = run(f, total_feats=[c for c in TOTAL_LIVE if c != "rain_fc"]); print("no rain done", flush=True)
        runs["A_no_qbform"] = run(f, total_feats=[c for c in TOTAL_LIVE if c != "qb_form_sum"]); print("no qb form done", flush=True)
        cache.write_bytes(pickle.dumps(runs))
        M._trees_cache().to_parquet(TMP / "trees.parquet", index=False)
    pA, tA = runs["A"]
    chk = wind_amounts(pA); assert np.allclose(chk, pA.wind_pts.values, atol=1e-9), np.abs(chk - pA.wind_pts.values).max()
    res = {k: score(v[0]) for k, v in runs.items()}
    res["A_no_wind_pts"] = score(apply(pA, tA, np.zeros(len(pA))))
    amtC = {m: wind_amounts(pA, m) for m in ("C1", "C2")}
    for m, a in amtC.items():
        res[f"A_{m}"] = score(apply(pA, tA, a))
    pd.DataFrame([{"variant": v, "window": w, "team_miss": round(sc[w]["team"], 4), "total_miss": round(sc[w]["total"], 4),
                   "margin_miss": round(sc[w]["margin"], 4), "spread_flag": rec(sc[w]["spread"]), "totals_flag": rec(sc[w]["totals"]),
                   "wind_under": rec(sc[w]["wind"])} for v, sc in res.items() for w in WIN]).to_csv(REP / "forecast_weather_backtest.csv", index=False)

    comps = {"B1 wind points": ("A_no_wind_pts", "A", True), "B2 rain in the total": ("A_no_rain", "A", False),
             "B3 QB form in the total": ("A_no_qbform", "A", False), "C1 isotonic curve vs bands": ("A", "A_C1", True),
             "C2 bands 0/8/10/15 vs bands": ("A", "A_C2", True)}
    gates = {name: {k: gate_rows(res[b], res[n], k, wind_only=wo) for k in ("team", "total")} for name, (b, n, wo) in comps.items()}
    # the placebo is drawn for whatever passes parts 1-2 on team points miss (the round-3 rule's miss for the game model)
    need = {name for name, g in gates.items() if passes12(g["team"])}
    print("pass parts 1-2:", need, flush=True)
    plac = {}
    if "--placebo" in sys.argv:
        rng = np.random.default_rng(SEED); wind = WL.readings()
        gid = pA[pA.wind_fc.notna()][["game_id", "season"]]
        wdraws = []
        for i in range(NPLAC):
            sh = dict(zip(gid.game_id, G.shuffle_within_season(gid.game_id.map(wind).values, gid.season.values, rng))); wdraws.append(sh)
        base_m = {"B1 wind points": misses(pA, np.zeros(len(pA))), "C1 isotonic curve vs bands": misses(pA, pA.wind_pts.values),
                  "C2 bands 0/8/10/15 vs bands": misses(pA, pA.wind_pts.values)}
        meth = {"B1 wind points": "bands", "C1 isotonic curve vs bands": "C1", "C2 bands 0/8/10/15 vs bands": "C2"}
        for name in [n for n in meth if n in need]:
            ds = [misses(pA.assign(wind_fc=pA.game_id.map(sh).astype(float)), wind_amounts(pA, meth[name], sh)) for sh in wdraws]
            plac[name] = {k: {w: [base_m[name][w][k] - d[w][k] for d in ds] for w in WIN} for k in ("team", "total")}
        jobs = [("rain", "B2 rain in the total"), ("qbform", "B3 QB form in the total")]
        todo = [(w_, n_) for w_, n_ in jobs if n_ in need]
        if todo:
            from concurrent.futures import ProcessPoolExecutor
            with ProcessPoolExecutor(6) as ex:
                for what, name in todo:
                    ds = list(ex.map(_job, [(what, SEED * 1000 + i) for i in range(NPLAC)]))
                    b = misses(runs[comps[name][0]][0], runs[comps[name][0]][0].wind_pts.values)
                    plac[name] = {k: {w: [b[w][k] - d[w][k] for d in ds] for w in WIN} for k in ("team", "total")}
                    print("placebo", name, "done", flush=True)
        for name, pl in plac.items():
            b, n, wo = comps[name]
            gates[name] = {k: gate_rows(res[b], res[n], k, pl[k], wind_only=wo) for k in ("team", "total")}
        pickle.dump(plac, open(TMP / "placebo.pkl", "wb"))

    # the total-points effect by forecast wind at the latest fit (2026's pool: 2018-2025), and the 8-10 mph check
    f = M.prep(feats()); tr = f[f.pf.notna() & (f.season >= M.TRAIN_FROM)]
    gf = M._game_frame(tr); from sklearn.linear_model import Ridge; from sklearn.pipeline import make_pipeline; from sklearn.preprocessing import StandardScaler
    tm = make_pipeline(StandardScaler(), Ridge(alpha=10.0)).fit(gf[M.TOTAL_FEATS].values, gf.total.values)
    per_mph = float((tm[-1].coef_ / tm[0].scale_)[M.TOTAL_FEATS.index("wind_out")])
    pool = pA[pA.wind_fc.notna() & (pA.game_type == "REG") & pA.game_id.isin(actual().index)]
    pw, pr = pool.wind_fc.values, (pool.game_id.map(actual()) - pool.model_total_raw).values
    eff = {m: [(mph, per_mph * mph, float(_amounts(m, pw, pr, np.array([float(mph)]))[0])) for mph in (0, 5, 9, 10, 14, 15, 20)] for m in ("bands", "C1", "C2")}
    d = B.join(pA, GAMES); d = d[(d.game_type == "REG") & d.season.between(2019, 2025) & d.wind_fc.notna()]
    band_chk = []
    for lo, hi in [(0, 8), (8, 10), (10, 15), (15, 99)]:
        m = (d.wind_fc >= lo) & (d.wind_fc < hi); x = d[m]
        row = {"band": f"[{lo},{hi})", "n": int(m.sum()), "A_bands": float((x.total - x.model_total).mean()), "before_wind_pts": float((x.total - x.model_total_raw).mean())}
        for mth, a in amtC.items():
            row[f"A_{mth}"] = float((x.total - x.model_total_raw - pd.Series(a, index=pA.game_id.values).reindex(x.game_id).values).mean())
        band_chk.append(row)

    L = ["# Forecast weather in the backtest: results (2 Oct 2026)", "", "Every variant is the live model refit walk-forward 2015-2025 (regular season; flags weeks 1-17 at the close).", ""]
    L += table(res)
    for name, g in gates.items():
        for k, lab in (("team", "team points miss"), ("total", "total miss")):
            L += ["", f"## {name}: study_gate on {lab}", "", G.markdown(g[k])]
    L += ["", f"## Total-points effect by forecast wind (latest fit: totals equation {per_mph:+.3f} per mph; wind points from the 2018-2025 pool)", "",
          "| Forecast wind (mph) | " + " | ".join(f"{m}: equation + wind points = total" for m in eff) + " |", "|---|" + "---|" * len(eff)]
    for i, mph in enumerate((0, 5, 9, 10, 14, 15, 20)):
        L.append(f"| {mph} | " + " | ".join(f"{eff[m][i][1]:+.2f} {eff[m][i][2]:+.2f} = {eff[m][i][1] + eff[m][i][2]:+.2f}" for m in eff) + " |")
    L += ["", "## Mean miss (actual total minus the model's total) by forecast-wind band, 2019-2025 regular season", "",
          "| Band | Games | Before wind points | Bands (A) | C1 | C2 |", "|---|---|---|---|---|---|"]
    L += [f"| {r['band']} | {r['n']} | {r['before_wind_pts']:+.2f} | {r['A_bands']:+.2f} | {r['A_C1']:+.2f} | {r['A_C2']:+.2f} |" for r in band_chk]
    (REP / "forecast_weather_backtest_results.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
