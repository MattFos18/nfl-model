"""Forecast weather vs the weather that happened, and what it costs the game model (30 Sep 2026).

The live cards price weather from a kickoff forecast (nflmodel/weather.py: temperature and wind from Open-Meteo patched
into games.parquet; rain from a 50%+ chance or 1 mm+ in the kickoff hour, trends.situation_extras). The backtest, and
every weather coefficient fitted on it, uses the weather that happened: the schedule's temperature and wind, rain from
the play-by-play weather text. data/weather/forecast_archive.csv holds what Open-Meteo forecast one day (d1) and two
days (d2) before each played outdoor kickoff hour, 2022-2025: temperature from 2022, wind, gusts and precipitation from
2024-01-20 (no precipitation chance: the previous-runs archive does not keep it, so the archive's rain call is the 1 mm
half of the live rule only).

1. How far off is the forecast: bias, mean absolute error, and how often each flag the model uses flips.
2. What it costs: the live walk-forward (experiments/situational_game.py's verified engine, fresh trees, refit before
   every regular-season week on every played game since 2013) scored with the d1 forecast as the weather inputs of the
   priced games instead of the actuals, all else unchanged. The fits are the same; only the priced week's inputs move.
3. Candidates that use only what is known before kickoff, each scored with the forecast as input, per season:
   (a) shrink:     each weather coefficient shrunk toward zero (the ridge form: the input pulled toward its training
                   mean) by lambda = the slope of the actual on the forecast over every earlier forecast game (the
                   errors-in-variables attenuation factor, clipped to [0, 1]); walk-forward, no change under 40 pairs
   (b) train_fc:   the d1 forecast as the training inputs wherever it exists (temperature 2022 on, wind and rain 2024 on)
   (c1) calib:     E[actual | forecast] by least squares on earlier pairs (wind; cold and rain as flags), bias included
   (c2) prob:      cold as P(temperature under 35F | forecast) from the earlier forecast errors (normal, bias and sd),
                   rain as P(rain | forecast precipitation) by a logistic fit on earlier pairs, wind as in c1
   (c3) bias:      the forecast less its earlier mean error (temperature and wind), flags from the corrected values
   (c4) rain_any:  the rain flag at measurable precipitation (0.01 in, 0.25 mm) instead of 1 mm
   Rule (reports/round3_rule.md, as far as the data allows): the team points miss and the total miss lower on every
   season the candidate changes; spread-flag and totals-flag wins minus losses not below the base on any season and the
   calibrated win-chance log loss not above it; a within-season shuffle placebo (50 draws) beaten on every season in
   45+ draws; no market input, no look-ahead (every parameter fitted on games before the priced week).
   The placebo for a test-side candidate shuffles, within season, its per-game change to the forecast input (the same
   adjustments landed on the wrong games); for train_fc it shuffles the training rows' forecast-minus-actual changes.

    WXF_SCRATCH=/path python -m experiments.weather_forecast --stage errors|run|decomp|placebo_b|report
Writes reports/weather_forecast.csv and reports/weather_forecast.md; everything else goes to WXF_SCRATCH.
"""
from __future__ import annotations
import os, sys, time, json, argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
SCR = Path(os.environ.get("WXF_SCRATCH", "/tmp/claude-0/-home-user/c1e0d18e-681a-50ba-b0bb-6c809c2e3dee/scratchpad/wxf")); SCR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("SG_SCRATCH", str(SCR / "sg"))
import numpy as np, pandas as pd
from scipy.stats import norm
from sklearn.linear_model import Ridge, LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.ensemble import HistGradientBoostingRegressor
from threadpoolctl import threadpool_limits
from nflmodel import model as M, trends as TR
from nflmodel.model import OUT
from experiments import situational_game as SG

ROOT = Path(__file__).resolve().parent.parent
REP = ROOT / "reports"
SEASONS = [2022, 2023, 2024, 2025]
SG.WINDOWS = {str(s): (s, s) for s in SEASONS}          # score() reads this: one window per season
WINS = list(SG.WINDOWS)
RAIN_MM = TR.RAIN_MM; MM_PER_IN = 25.4
COLD = M.COLD_F
MIN_PAIRS, MIN_RAIN_EVENTS = 40, 5
N_PLACEBO = 50
WIND_BANDS = [0, 10, 15, np.inf]    # wind level: calm-to-breezy, 10-15 mph, 15+ mph
BASE_FEATS, BASE_TOTAL = list(M.FEATS), list(M.TOTAL_FEATS)
WX_IN = ["wind_out", "cold", "rain"]                  # game-level weather inputs a forecast replaces (warm_in_cold follows cold)


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


# --------------------------------------------------------------------------------------------------------- the data
def pbp_weather_text(seasons) -> dict:
    import pyarrow.parquet as pq
    wx = {}
    for s in seasons:
        f = ROOT / "data" / "raw" / "pbp" / f"play_by_play_{s}.parquet"
        if f.exists():
            t = pq.read_table(f, columns=["game_id", "weather"]).to_pandas()
            wx.update(t.groupby("game_id").weather.first().to_dict())
    return wx


def pairs_table() -> pd.DataFrame:
    """One row per archived outdoor game: forecast (d1, d2), the model's actual (schedule temp and wind, play-by-play
    rain), and Open-Meteo's reanalysis for the same hour."""
    fa = pd.read_csv(ROOT / "data" / "weather" / "forecast_archive.csv")
    g = SG.GAMES.set_index("game_id")
    fa = fa[fa.game_id.isin(g.index)].copy()
    fa["game_type"] = fa.game_id.map(g.game_type); fa["kickoff_et"] = fa.game_id.map(g.kickoff_et)
    fa["home_team"] = fa.game_id.map(g.home_team); fa["away_team"] = fa.game_id.map(g.away_team)
    fa["act_temp"] = fa.game_id.map(g.temp); fa["act_wind"] = fa.game_id.map(g.wind)
    txt = pbp_weather_text(sorted(fa.season.unique()))
    w = fa.game_id.map(lambda k: str(txt.get(k, "") or "").lower())
    fa["act_text"] = w.ne("")
    fa["act_rain"] = np.where(fa.act_text, w.map(lambda s: float(any(k in s for k in ["rain", "shower", "drizzle", "storm"]))), np.nan)
    for d in (1, 2):
        fa[f"precip_mm_d{d}"] = fa[f"precip_d{d}"] * MM_PER_IN
        fa[f"rain_d{d}"] = np.where(fa[f"precip_d{d}"].notna(), (fa[f"precip_mm_d{d}"] >= RAIN_MM).astype(float), np.nan)
    ra = pd.read_csv(ROOT / "data" / "weather" / "archive_kickoff.csv").drop_duplicates("game_id").set_index("game_id")
    fa["re_temp"] = fa.game_id.map(ra.temp); fa["re_wind"] = fa.game_id.map(ra.wind); fa["re_precip_mm"] = fa.game_id.map(ra.precip) * MM_PER_IN
    fa["re_rain"] = np.where(fa.re_precip_mm.notna(), (fa.re_precip_mm >= RAIN_MM).astype(float), np.nan)
    return fa.sort_values("kickoff_et").reset_index(drop=True)


# -------------------------------------------------------------------------------------------------- 1. the errors
def _cont(x, y):
    m = x.notna() & y.notna(); e = (x - y)[m]
    return {"n": int(m.sum()), "bias": float(e.mean()) if m.any() else np.nan, "mae": float(e.abs().mean()) if m.any() else np.nan,
            "rmse": float(np.sqrt((e ** 2).mean())) if m.any() else np.nan, "corr": float(np.corrcoef(x[m], y[m])[0, 1]) if m.sum() > 2 else np.nan}


def _flag(f, a):
    m = f.notna() & a.notna(); f, a = f[m].astype(int), a[m].astype(int)
    return {"n": int(m.sum()), "fc_rate": float(f.mean()) if m.any() else np.nan, "act_rate": float(a.mean()) if m.any() else np.nan,
            "flips": int((f != a).sum()), "flip_pct": float((f != a).mean()) if m.any() else np.nan,
            "fc1_act0": int(((f == 1) & (a == 0)).sum()), "fc0_act1": int(((f == 0) & (a == 1)).sum()), "both1": int(((f == 1) & (a == 1)).sum())}


def error_rows(fa: pd.DataFrame) -> list[dict]:
    rows = []
    groups = [("all", fa)] + [(str(s), fa[fa.season == s]) for s in SEASONS]
    for lab, x in groups:
        for d in (1, 2):
            for var, act, src in [("temp", "act_temp", "schedule"), ("wind", "act_wind", "schedule"), ("temp", "re_temp", "reanalysis"), ("wind", "re_wind", "reanalysis")]:
                r = _cont(x[f"{var}_d{d}"], x[act])
                if r["n"]:
                    rows.append({"section": "error", "item": f"{var} ({'F' if var == 'temp' else 'mph'})", "lead": f"d{d}", "against": src, "season": lab, **r})
            # flags
            for var, fc, act, src in [("cold (<35F)", (x[f"temp_d{d}"] < COLD).where(x[f"temp_d{d}"].notna()), (x.act_temp < COLD).where(x.act_temp.notna()), "schedule"),
                                      ("cold (<35F)", (x[f"temp_d{d}"] < COLD).where(x[f"temp_d{d}"].notna()), (x.re_temp < COLD).where(x.re_temp.notna()), "reanalysis"),
                                      ("rain (1 mm+ fc vs pbp text)", x[f"rain_d{d}"], x.act_rain, "pbp text"),
                                      ("rain (1 mm+ fc vs 1 mm+ reanalysis)", x[f"rain_d{d}"], x.re_rain, "reanalysis"),
                                      ("rain (0.25 mm+ fc vs pbp text)", (x[f"precip_mm_d{d}"] >= 0.25).where(x[f"precip_mm_d{d}"].notna()), x.act_rain, "pbp text")]:
                r = _flag(fc, act)
                if r["n"]:
                    rows.append({"section": "flag", "item": var, "lead": f"d{d}", "against": src, "season": lab, **r})
            for src, act in [("schedule", x.act_wind), ("reanalysis", x.re_wind)]:
                fb = pd.cut(x[f"wind_d{d}"], WIND_BANDS, right=False, labels=False); ab = pd.cut(act, WIND_BANDS, right=False, labels=False)
                m = fb.notna() & ab.notna()
                if m.any():
                    rows.append({"section": "flag", "item": "wind level (<10 / 10-15 / 15+ mph)", "lead": f"d{d}", "against": src, "season": lab, "n": int(m.sum()),
                                 "fc_rate": float((fb[m] >= 1).mean()), "act_rate": float((ab[m] >= 1).mean()), "flips": int((fb[m] != ab[m]).sum()),
                                 "flip_pct": float((fb[m] != ab[m]).mean()), "fc1_act0": int((fb[m] > ab[m]).sum()), "fc0_act1": int((fb[m] < ab[m]).sum())})
    return rows


def stage_errors():
    fa = pairs_table(); fa.to_csv(SCR / "pairs.csv", index=False)
    rows = error_rows(fa)
    # what an average error is worth in the model: the points equation's per-unit coefficients (the live fits of 2023-25,
    # from pred_v3) and the total equation fitted on 2013-2024
    pv = pd.read_parquet(OUT / "pred_v3.parquet"); pv = pv[pv.season.between(2023, 2025)]
    coef = {k: float(pv[f"coef_{k}"].mean()) for k in ["wind_out", "cold", "rain", "warm_in_cold"]}
    fp = M.prep(M.with_trends(pd.read_parquet(OUT / "features_asof.parquet")))
    G = M._game_frame(fp[fp.pf.notna() & fp.season.between(M.TRAIN_FROM, 2024)])
    tm = make_pipeline(StandardScaler(), Ridge(alpha=10.0)).fit(G[BASE_TOTAL].values, G.total.values)
    tc = dict(zip(BASE_TOTAL, tm[-1].coef_ / tm[0].scale_))
    for k in ["wind_out", "cold", "rain", "warm_in_cold"]:
        rows.append({"section": "coef", "item": k, "lead": "", "against": "", "season": "2023-25 fits", "points_per_unit_team": coef[k], "total_per_unit": tc.get(k, np.nan)})
    pd.DataFrame(rows).to_csv(SCR / "errors.csv", index=False)
    log("errors written", len(rows))


# ------------------------------------------------------------------------------------------- forecast input builders
def game_inputs(fa: pd.DataFrame, mode: str) -> pd.DataFrame:
    """Per game, the forecast-based values of wind_out, cold, rain (NaN = keep the model's actual).
    mode "live": wherever the forecast exists (what the live path would have used); "swap": only where the actual
    reading exists as well (a like-for-like replacement)."""
    v = pd.DataFrame(index=fa.game_id.values)
    t, w, r = fa.temp_d1.values, fa.wind_d1.values, fa.rain_d1.values
    if mode == "swap":
        t = np.where(fa.act_temp.notna(), t, np.nan); w = np.where(fa.act_wind.notna(), w, np.nan); r = np.where(fa.act_text, r, np.nan)
    v["wind_out"] = w
    v["cold"] = np.where(np.isnan(t), np.nan, (t < COLD).astype(float))
    v["rain"] = r
    return v


def _before(fa, s, wk):
    """Pairs available before (season s, week wk): every archived game played earlier."""
    return (fa.season < s) | ((fa.season == s) & (fa.week < wk))


def walk_params(fa: pd.DataFrame, weeks: list) -> dict:
    """(season, week) -> the parameters each candidate fits on the forecast/actual pairs before that week."""
    P = {}
    for s, wk in weeks:
        b = fa[_before(fa, s, wk)]
        p = {}
        # temperature pairs (actual reading known)
        tp = b[b.temp_d1.notna() & b.act_temp.notna()]
        p["n_temp"] = len(tp)
        if len(tp) >= MIN_PAIRS:
            e = tp.temp_d1 - tp.act_temp
            p["temp_bias"], p["temp_sd"] = float(e.mean()), float(e.std())
            fc_c = (tp.temp_d1 < COLD).astype(float).values; ac_c = (tp.act_temp < COLD).astype(float).values
            p["cold"] = _ols(fc_c, ac_c)
        wp = b[b.wind_d1.notna() & b.act_wind.notna()]
        p["n_wind"] = len(wp)
        if len(wp) >= MIN_PAIRS:
            p["wind"] = _ols(wp.wind_d1.values, wp.act_wind.values)
            p["wind_bias"] = float((wp.wind_d1 - wp.act_wind).mean())
        rp = b[b.rain_d1.notna() & b.act_text]
        p["n_rain"] = len(rp); p["n_rain_events"] = int(rp.act_rain.sum()) if len(rp) else 0
        if len(rp) >= MIN_PAIRS and p["n_rain_events"] >= MIN_RAIN_EVENTS:
            p["rain"] = _ols(rp.rain_d1.values, rp.act_rain.values)
            X = np.log1p(rp.precip_mm_d1.values.clip(0))[:, None]
            lr = LogisticRegression(C=1.0).fit(X, rp.act_rain.values.astype(int))
            p["rain_logit"] = (float(lr.intercept_[0]), float(lr.coef_[0][0]))
        P[(s, wk)] = p
    return P


def _ols(x, y):
    """(intercept, slope) of y on x; slope clipped to [0, 1] for the shrink (a), intercept keeps the means matched."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    vx = x.var()
    b = float(np.cov(x, y, bias=True)[0, 1] / vx) if vx > 0 else 1.0
    return {"a": float(y.mean() - b * x.mean()), "b": b, "mx": float(x.mean()), "my": float(y.mean())}


def train_means(fp: pd.DataFrame, weeks: list) -> dict:
    """(season, week) -> the training rows' mean of each weather input (what the ridge's coefficient multiplies the
    deviation from), so shrinking a coefficient by lambda is the input pulled toward this mean by lambda."""
    played = fp[fp.pf.notna() & (fp.season >= M.TRAIN_FROM)]
    out = {}
    for s, wk in weeks:
        tr = played[(played.season < s) | ((played.season == s) & (played.week < wk))]
        out[(s, wk)] = tr[WX_IN + ["warm_in_cold"]].mean().to_dict()
    return out


def candidate_inputs(fa: pd.DataFrame, base_live: pd.DataFrame, params: dict, tmeans: dict) -> dict:
    """name -> per-game frame of (wind_out, cold, rain, warm_in_cold scale handled later), NaN = keep base_live.
    Every candidate starts from the live forecast inputs and changes them with parameters from earlier pairs only."""
    C = {k: base_live.copy() for k in ["a_shrink", "c1_calib", "c2_prob", "c3_bias", "c4_rain_any"]}
    for r in fa.itertuples():
        p = params[(r.season, r.week)]; g = r.game_id
        tm = tmeans[(r.season, r.week)]
        # --- (a) shrink the coefficient: x -> mean_train + lambda (x - mean_train), lambda = clip(slope, 0, 1)
        for k, pk in [("wind_out", "wind"), ("cold", "cold"), ("rain", "rain")]:
            x = base_live.at[g, k]
            if pd.notna(x) and pk in p:
                lam = min(1.0, max(0.0, p[pk]["b"]))
                C["a_shrink"].at[g, k] = tm[k] + lam * (x - tm[k])
        # --- (c1) E[actual | forecast], least squares on earlier pairs
        for k, pk in [("wind_out", "wind"), ("cold", "cold"), ("rain", "rain")]:
            x = base_live.at[g, k]
            if pd.notna(x) and pk in p:
                v = p[pk]["a"] + p[pk]["b"] * x
                C["c1_calib"].at[g, k] = max(0.0, v) if k == "wind_out" else min(1.0, max(0.0, v))
        # --- (c2) probabilities: P(temp < 35 | forecast), P(rain | forecast precipitation); wind as c1
        if pd.notna(base_live.at[g, "cold"]) and "temp_bias" in p and pd.notna(r.temp_d1):
            C["c2_prob"].at[g, "cold"] = float(norm.cdf((COLD - (r.temp_d1 - p["temp_bias"])) / max(p["temp_sd"], 0.5)))
        if pd.notna(base_live.at[g, "rain"]) and "rain_logit" in p and pd.notna(r.precip_mm_d1):
            a, b = p["rain_logit"]
            C["c2_prob"].at[g, "rain"] = float(1 / (1 + np.exp(-(a + b * np.log1p(max(0.0, r.precip_mm_d1))))))
        if pd.notna(base_live.at[g, "wind_out"]) and "wind" in p:
            C["c2_prob"].at[g, "wind_out"] = max(0.0, p["wind"]["a"] + p["wind"]["b"] * base_live.at[g, "wind_out"])
        # --- (c3) bias-corrected temperature and wind
        if pd.notna(base_live.at[g, "cold"]) and "temp_bias" in p and pd.notna(r.temp_d1):
            C["c3_bias"].at[g, "cold"] = float((r.temp_d1 - p["temp_bias"]) < COLD)
        if pd.notna(base_live.at[g, "wind_out"]) and "wind_bias" in p:
            C["c3_bias"].at[g, "wind_out"] = max(0.0, base_live.at[g, "wind_out"] - p["wind_bias"])
        # --- (c4) rain at measurable precipitation (0.01 in): a fixed, standard threshold, nothing fitted
        if pd.notna(base_live.at[g, "rain"]) and pd.notna(r.precip_mm_d1):
            C["c4_rain_any"].at[g, "rain"] = float(r.precip_mm_d1 >= 0.25)
    return C


def apply_inputs(fp: pd.DataFrame, gv: pd.DataFrame) -> pd.DataFrame:
    """fp with each game's wind_out / cold / rain replaced where gv holds a value (both team rows), warm_in_cold
    recomputed from the new cold (the live rule: cold x warm-or-dome team)."""
    fp = fp.copy()
    for k in WX_IN:
        v = fp.game_id.map(gv[k])
        m = v.notna() & (fp.dome == 0)
        fp.loc[m, k] = v[m].values
    fp["warm_in_cold"] = fp["cold"] * fp.team.isin(M.WARM_OR_DOME).astype(float)
    return fp


def shuffled_delta(base_live: pd.DataFrame, cand: pd.DataFrame, fa: pd.DataFrame, seed: int) -> pd.DataFrame:
    """The placebo: the candidate's per-game change to the live forecast input, shuffled within season across the
    games that carry the change's inputs (each input shuffled among the games holding that forecast)."""
    rng = np.random.default_rng(seed)
    out = base_live.copy(); season = fa.set_index("game_id").season
    for k in WX_IN:
        d = (cand[k] - base_live[k])
        for s in SEASONS:
            ix = [g for g in d.index if season.get(g) == s and pd.notna(base_live.at[g, k])]
            if not ix:
                continue
            vals = d.loc[ix].fillna(0.0).values[rng.permutation(len(ix))]
            nv = base_live.loc[ix, k].values + vals
            out.loc[ix, k] = np.clip(nv, 0.0, None) if k == "wind_out" else np.clip(nv, 0.0, 1.0)
    return out


# ------------------------------------------------------------------------------------------------------- the engine
def engine(fp_train: pd.DataFrame, tests: dict, seasons=SEASONS) -> dict:
    """SG.lean_walk_forward's numbers, fitted once per week on fp_train and priced for every test variant (the same
    fits: only the priced week's inputs differ). tests: name -> prepped team rows (the test seasons, base row order)."""
    feats, tfeats = BASE_FEATS, BASE_TOTAL
    played = fp_train[fp_train.pf.notna() & (fp_train.season >= M.TRAIN_FROM)]
    Gtr = M._game_frame(played)
    blend_cols = {k: feats + extra for k, (extra, _) in M.BLEND.items()}
    allc = sorted(set(feats) | {c for cols in blend_cols.values() for c in cols})
    # per variant: rows by (season, week), and the game frame of its rows
    TV = {}
    for name, fv in tests.items():
        Gv = M._game_frame(fv)
        TV[name] = (dict(tuple(fv.groupby(["season", "week"], sort=False))), Gv)
    first = next(iter(tests.values()))
    out = {n: [] for n in tests}
    for s in seasons:
        ta = first[first.season == s]
        for wk in sorted(ta.loc[ta.game_type == "REG", "week"].unique()):
            tr = played[(played.season < s) | ((played.season == s) & (played.week < wk))]
            y = tr.pf.values; X = tr[feats].values
            ridge = make_pipeline(StandardScaler(), Ridge(alpha=M.RIDGE)).fit(X, y)
            mu = tr[allc].mean()
            models = {"ridge": (ridge, feats)}
            for k, (extra, al) in M.BLEND.items():
                cols = blend_cols[k]
                models[k] = (make_pipeline(StandardScaler(), Ridge(alpha=al)).fit(tr[cols].fillna(tr[cols].mean()).values, y), cols)
            models["trees"] = (HistGradientBoostingRegressor(**M.TREES).fit(X, y), feats)
            trh = tr[tr.home == 1].set_index("game_id"); tra = tr[tr.home == 0].set_index("game_id")
            tid = trh.index.intersection(tra.index)
            trp = ridge.predict(X)
            ph = pd.Series(trp[(tr.home == 1).values], index=trh.index); pa = pd.Series(trp[(tr.home == 0).values], index=tra.index)
            tr_margin = (trh.loc[tid, "pf"] - tra.loc[tid, "pf"]).values; tr_mu = (ph.loc[tid] - pa.loc[tid]).values
            sigma_m = float(np.std(tr_margin - tr_mu)); K = M.key_weights(tr_margin, tr_mu, sigma_m)
            trG = Gtr.loc[tid]
            tm = make_pipeline(StandardScaler(), Ridge(alpha=10.0)).fit(trG[tfeats].values, trG.total.values)
            tres = trG.total.values - tm.predict(trG[tfeats].values)
            for name in tests:
                rows, Gv = TV[name]
                te = rows[(s, wk)]
                hmask = (te.home == 1).values
                h_ids = te.game_id.values[hmask]; aset = set(te.game_id.values[~hmask]); ids = [g for g in h_ids if g in aset]
                preds = [m.predict(te[cols].fillna(mu[cols]).values) for m, cols in models.values()]
                bl = pd.Series(np.mean(preds, axis=0), index=te.game_id.values + np.where(hmask, "|h", "|a"))
                rec = pd.DataFrame({"game_id": ids, "season": s, "week": wk})
                rec["model_spread"] = bl.loc[[g + "|h" for g in ids]].values - bl.loc[[g + "|a" for g in ids]].values
                rec["p_home"] = SG._p_home(rec.model_spread.values, sigma_m, K.values)
                rec["model_total"] = tm.predict(Gv.loc[ids, tfeats].values)
                tl = SG.GAMES.set_index("game_id").total_line.reindex(ids).values
                v = rec.model_total.values[:, None] + tres[None, :]
                with np.errstate(invalid="ignore", divide="ignore"):
                    pe = (v > tl[:, None]).mean(axis=1) / np.maximum(1e-9, (v != tl[:, None]).mean(axis=1))
                rec["p_over_emp"] = np.where(np.isnan(tl), np.nan, pe)
                out[name].append(rec)
    return {n: SG.finish(pd.concat(v, ignore_index=True)) for n, v in out.items()}


# ---------------------------------------------------------------------------------------------------------- scoring
_HIST = None


def score_pred(P: pd.DataFrame) -> dict:
    """SG.score per season; the calibration history (2015-2021) is the live walk-forward's own (pred_v3), identical for
    every variant, so each variant's 2022-25 calibration is fitted the live way on its own earlier seasons."""
    global _HIST
    if _HIST is None:
        pv = pd.read_parquet(OUT / "pred_v3.parquet")
        _HIST = SG.finish(pv[(pv.game_type == "REG") & pv.season.between(2015, 2021)][["game_id", "season", "week", "model_spread", "model_total", "p_home", "p_over_emp"]].copy())
    return SG.flat(SG.score(pd.concat([_HIST, P], ignore_index=True)))


def subset_miss(P: pd.DataFrame, ids: set) -> dict:
    g = SG.GAMES.set_index("game_id"); d = P[P.game_id.isin(ids)].copy()
    d["hs"] = d.game_id.map(g.home_score); d["as_"] = d.game_id.map(g.away_score); d = d[d.hs.notna()]
    o = {}
    for w in WINS:
        x = d[d.season == int(w)]
        e = np.concatenate([(x.home_exp - x.hs).values, (x.away_exp - x.as_).values])
        o[f"sub_n_{w}"] = int(len(x)); o[f"sub_team_mae_{w}"] = float(np.abs(e).mean()) if len(e) else np.nan
        o[f"sub_total_mae_{w}"] = float(np.abs(x.model_total - (x.hs + x.as_)).mean()) if len(x) else np.nan
    return o


def prepared():
    fp = M.prep(M.with_trends(pd.read_parquet(OUT / "features_asof.parquet")))
    fa = pairs_table()
    fa = fa[fa.game_id.isin(fp.game_id)]
    test = fp[fp.season.isin(SEASONS)].copy()
    weeks = sorted(set(zip(fa.season, fa.week)))
    return fp, fa, test, weeks


def stage_run():
    t0 = time.time()
    fp, fa, test, weeks = prepared()
    live = game_inputs(fa, "live"); swap = game_inputs(fa, "swap")
    params = walk_params(fa, weeks); tmeans = train_means(fp, weeks)
    (SCR / "params.json").write_text(json.dumps({f"{s}-{w}": p for (s, w), p in params.items()}, default=float, indent=0))
    C = candidate_inputs(fa, live, params, tmeans)
    tests = {"actual": test, "fc_swap": apply_inputs(test, swap), "fc_live": apply_inputs(test, live)}
    for k, gv in C.items():
        tests[k] = apply_inputs(test, gv)
    for k, gv in C.items():
        for sd in range(N_PLACEBO):
            tests[f"{k}|pl{sd}"] = apply_inputs(test, shuffled_delta(live, gv, fa, 1000 + sd))
    # which games each candidate actually changes (for "every season it can be scored on")
    changed = {}
    for k in list(C) + ["fc_swap", "fc_live"]:
        a = tests["fc_live" if k in C else "actual"]; b = tests[k]
        diff = (a[WX_IN + ["warm_in_cold"]].values != b[WX_IN + ["warm_in_cold"]].values).any(axis=1)
        changed[k] = sorted(set(b.game_id[diff]))
    (SCR / "changed.json").write_text(json.dumps(changed))
    log("variants", len(tests))
    with threadpool_limits(limits=1):
        R = engine(fp, tests)
    log("engine done", round(time.time() - t0), "s")
    # (b) training on the forecast inputs wherever they exist; priced with the live forecast inputs
    fpb = apply_inputs(fp, live)
    with threadpool_limits(limits=1):
        Rb = engine(fpb, {"b_train_fc": tests["fc_live"]})
    R.update(Rb)
    log("train_fc done", round(time.time() - t0), "s")
    (SCR / "preds").mkdir(exist_ok=True)
    for k, P in R.items():
        if "|pl" not in k:
            P.to_parquet(SCR / "preds" / f"{k}.parquet", index=False)
    fc_games = set(fa.game_id)
    rows = []
    for k, P in R.items():
        rows.append({"name": k, **score_pred(P), **subset_miss(P, fc_games)})
    pd.DataFrame(rows).to_csv(SCR / "scores.csv", index=False)
    log("scored", len(rows), round(time.time() - t0), "s")
    # engine check: the actual variant against SG.lean_walk_forward on 2023
    G = SG.game_frame(fp); G["total_line"] = G.index.map(SG.GAMES.set_index("game_id").total_line)
    with threadpool_limits(limits=1):
        ref = SG.lean_walk_forward(fp, G, BASE_FEATS, BASE_TOTAL, seasons=[2023])
    j = R["actual"].merge(ref, on="game_id", suffixes=("", "_ref"))
    chk = {c: float((j[c] - j[c + "_ref"]).abs().max()) for c in ["model_spread", "model_total", "p_home", "p_over_emp"]}; chk["games"] = int(len(j))
    pv = pd.read_parquet(OUT / "pred_v3.parquet"); j2 = R["actual"].merge(pv[["game_id", "model_spread", "model_total"]], on="game_id", suffixes=("", "_live"))
    chk["vs_pred_v3_spread_mean_abs"] = float((j2.model_spread - j2.model_spread_live).abs().mean())
    chk["vs_pred_v3_total_max_abs"] = float((j2.model_total - j2.model_total_live).abs().max())
    (SCR / "engine_check.json").write_text(json.dumps(chk, indent=1)); log("engine check", chk)


def stage_decomp():
    """Which forecast input carries the cost: the live forecast for one input at a time (the others actual)."""
    fp, fa, test, weeks = prepared()
    live = game_inputs(fa, "live")
    tests = {}
    for k, cols in [("fc_temp_only", ["cold"]), ("fc_wind_only", ["wind_out"]), ("fc_rain_only", ["rain"])]:
        gv = live.copy()
        for c in WX_IN:
            if c not in cols:
                gv[c] = np.nan
        tests[k] = apply_inputs(test, gv)
    with threadpool_limits(limits=1):
        R = engine(fp, tests)
    fc_games = set(fa.game_id)
    rows = [{"name": k, **score_pred(P), **subset_miss(P, fc_games)} for k, P in R.items()]
    S = pd.read_csv(SCR / "scores.csv"); S = S[~S.name.isin(list(R))]
    pd.concat([S, pd.DataFrame(rows)], ignore_index=True).to_csv(SCR / "scores.csv", index=False); log("decomp done")


def stage_placebo_b(jobs=4):
    """Placebo for train_fc: the training rows' forecast-minus-actual changes shuffled within season (refit each draw)."""
    from joblib import Parallel, delayed
    fp, fa, test, weeks = prepared()
    live = game_inputs(fa, "live")
    fc_live = apply_inputs(test, live)
    base_act = pd.DataFrame(index=live.index)
    fpg = fp[fp.home == 1].set_index("game_id")
    for k in WX_IN:
        base_act[k] = fpg[k].reindex(live.index)
    def one(sd):
        with threadpool_limits(limits=1):
            fake = shuffled_delta(base_act, live.where(live.notna(), base_act), fa, 5000 + sd)
            P = engine(apply_inputs(fp, fake), {"x": fc_live})["x"]
        return {"name": f"b_train_fc|pl{sd}", **score_pred(P)}
    rows = Parallel(n_jobs=jobs, backend="loky")(delayed(one)(sd) for sd in range(N_PLACEBO))
    pd.DataFrame(rows).to_csv(SCR / "placebo_b.csv", index=False); log("placebo_b done")


# ----------------------------------------------------------------------------------------------------------- report
CAND = {"a_shrink": "(a) shrink each weather coefficient by the forecast's reliability",
        "b_train_fc": "(b) train on the d1 forecast where it exists",
        "c1_calib": "(c1) E[actual | forecast] (least squares, bias included)",
        "c2_prob": "(c2) probability inputs: P(cold), P(rain | precipitation); wind as c1",
        "c3_bias": "(c3) bias-corrected temperature and wind",
        "c4_rain_any": "(c4) rain flag at measurable precipitation (0.25 mm)"}


def deltas(r, b):
    d = {}
    for w in WINS:
        d[f"d_team_{w}"] = r[f"team_mae_{w}"] - b[f"team_mae_{w}"]
        d[f"d_total_{w}"] = r[f"total_mae_{w}"] - b[f"total_mae_{w}"]
        d[f"d_margin_{w}"] = r[f"margin_mae_{w}"] - b[f"margin_mae_{w}"]
        d[f"d_sp_{w}"] = (r[f"sp_w_{w}"] - r[f"sp_l_{w}"]) - (b[f"sp_w_{w}"] - b[f"sp_l_{w}"])
        d[f"d_to_{w}"] = (r[f"to_w_{w}"] - r[f"to_l_{w}"]) - (b[f"to_w_{w}"] - b[f"to_l_{w}"])
        d[f"d_ll_{w}"] = r[f"ll_cal_{w}"] - b[f"ll_cal_{w}"]
        d[f"d_subteam_{w}"] = r[f"sub_team_mae_{w}"] - b[f"sub_team_mae_{w}"] if f"sub_team_mae_{w}" in r and pd.notna(r.get(f"sub_team_mae_{w}")) else np.nan
        d[f"d_subtotal_{w}"] = r[f"sub_total_mae_{w}"] - b[f"sub_total_mae_{w}"] if f"sub_total_mae_{w}" in r and pd.notna(r.get(f"sub_total_mae_{w}")) else np.nan
    return d


def stage_report():
    S = pd.read_csv(SCR / "scores.csv").set_index("name")
    E = pd.read_csv(SCR / "errors.csv")
    changed = json.loads((SCR / "changed.json").read_text())
    chk = json.loads((SCR / "engine_check.json").read_text())
    pb = pd.read_csv(SCR / "placebo_b.csv").set_index("name") if (SCR / "placebo_b.csv").exists() else None
    reg = set(SG.GAMES.loc[SG.GAMES.game_type == "REG", "game_id"])
    changed = {k: [g for g in v if g in reg] for k, v in changed.items()}   # the engine prices regular-season weeks only
    season_of = lambda ids: sorted({int(g[:4]) for g in ids})
    rows = []
    # cost of the forecast
    b = S.loc["actual"]
    for k in ["fc_swap", "fc_live", "fc_temp_only", "fc_wind_only", "fc_rain_only"]:
        if k not in S.index:
            continue
        r = S.loc[k]; d = deltas(r, b)
        rows.append({"section": "cost", "name": k, "seasons_changed": " ".join(map(str, season_of(changed.get(k, [])))), "games_changed": len(changed.get(k, [])) or np.nan,
                     **{c: r[c] for c in S.columns if any(c.endswith("_" + w) for w in WINS)}, **d})
    rows.append({"section": "cost", "name": "actual", **{c: b[c] for c in S.columns if any(c.endswith("_" + w) for w in WINS)}})
    # candidates against fc_live
    base = S.loc["fc_live"]
    ver = []
    for k in CAND:
        r = S.loc[k]; d = deltas(r, base)
        sc = [str(s) for s in season_of(changed.get(k, [])) if str(s) in WINS] if k != "b_train_fc" else WINS
        r1 = bool(sc) and all(d[f"d_team_{w}"] < 0 and d[f"d_total_{w}"] < 0 for w in sc)
        r2 = all(d[f"d_sp_{w}"] >= 0 and d[f"d_to_{w}"] >= 0 and d[f"d_ll_{w}"] <= 1e-9 for w in WINS)
        # placebo
        if k == "b_train_fc":
            pl = pb if pb is not None else pd.DataFrame()
        else:
            pl = S[S.index.str.startswith(k + "|pl")]
        beaten = None
        if len(pl):
            beaten = 0
            for _, x in pl.iterrows():
                if any((base[f"team_mae_{w}"] - x[f"team_mae_{w}"]) >= (base[f"team_mae_{w}"] - r[f"team_mae_{w}"]) or
                       (base[f"total_mae_{w}"] - x[f"total_mae_{w}"]) >= (base[f"total_mae_{w}"] - r[f"total_mae_{w}"]) for w in sc):
                    beaten += 1
        r3 = beaten is not None and len(pl) >= N_PLACEBO and (len(pl) - beaten) >= 45
        verdict = "adopt" if (r1 and r2 and r3) else "not adopted"
        why = []
        if not r1: why.append("miss not lower on every season it changes")
        if not r2: why.append("costs flags or calibration")
        if beaten is not None and not r3: why.append(f"placebo beat or matched it in {beaten} of {len(pl)} draws")
        ver.append({"name": k, "rule1": r1, "rule2": r2, "placebo_beaten": beaten, "placebo_draws": len(pl), "rule3": r3, "verdict": verdict, "why": "; ".join(why)})
        rows.append({"section": "candidate", "name": k, "label": CAND[k], "seasons_changed": " ".join(sc), "games_changed": len(changed.get(k, [])) if k != "b_train_fc" else np.nan,
                     **{c: r[c] for c in S.columns if any(c.endswith("_" + w) for w in WINS)}, **d, **ver[-1]})
    rows.append({"section": "candidate_base", "name": "fc_live", **{c: base[c] for c in S.columns if any(c.endswith("_" + w) for w in WINS)}})
    out = pd.concat([pd.DataFrame(rows), E.assign(name=E.item)], ignore_index=True)
    out.to_csv(REP / "weather_forecast.csv", index=False)
    V = pd.DataFrame(ver)
    write_md(S, E, V, changed, chk)
    log("report written")


def _f(x, n=3):
    return "" if x is None or (isinstance(x, float) and np.isnan(x)) else f"{x:.{n}f}"


def write_md(S, E, V, changed, chk):
    reg = set(SG.GAMES.loc[SG.GAMES.game_type == "REG", "game_id"])
    L = ["# Forecast weather vs actual weather in the game model", "",
         "30 Sep 2026. `experiments/weather_forecast.py`; rows in `reports/weather_forecast.csv`. Forecasts from",
         "`data/weather/forecast_archive.csv` (Open-Meteo previous runs: d1 = the forecast one day before the kickoff hour),",
         f"{len([g for g in changed['fc_live'] if g in reg])} regular-season outdoor games whose inputs change. Actuals are the model's own: the schedule's temperature and wind, rain from the",
         "play-by-play weather text. The archive has no precipitation chance, so its rain call is the 1 mm half of the live rule",
         "(the live rule also calls rain at a 50%+ chance). Temperature forecasts cover 2022-25; wind and rain 2024-25.", ""]
    L += ["## 1. How far off is the forecast (d1, all seasons)", "",
          "| input | against | games | bias (fc - actual) | mean abs error | rmse | corr |", "|---|---|---|---|---|---|---|"]
    e = E[(E.section == "error") & (E.lead == "d1") & (E.season == "all")]
    for r in e.itertuples():
        L.append(f"| {r.item} | {r.against} | {int(r.n)} | {r.bias:+.2f} | {r.mae:.2f} | {r.rmse:.2f} | {r.corr:.3f} |")
    L += ["", "By season (d1 against the schedule): " + "; ".join(
        f"{r.season} {r.item.split()[0]} bias {r.bias:+.2f}, MAE {r.mae:.2f} (n {int(r.n)})"
        for r in E[(E.section == "error") & (E.lead == "d1") & (E.against == "schedule") & (E.season != "all")].itertuples()), ""]
    e2 = E[(E.section == "error") & (E.lead == "d2") & (E.season == "all") & (E.against == "schedule")]
    L += ["Two days out (d2, against the schedule): " + "; ".join(f"{r.item.split()[0]} bias {r.bias:+.2f}, MAE {r.mae:.2f}" for r in e2.itertuples()), ""]
    L += ["| flag (d1) | against | games | forecast rate | actual rate | flips | flip % | fc yes, actual no | fc no, actual yes |", "|---|---|---|---|---|---|---|---|---|"]
    for r in E[(E.section == "flag") & (E.lead == "d1") & (E.season == "all")].itertuples():
        L.append(f"| {r.item} | {r.against} | {int(r.n)} | {r.fc_rate:.1%} | {r.act_rate:.1%} | {int(r.flips)} | {r.flip_pct:.1%} | {int(r.fc1_act0)} | {int(r.fc0_act1)} |")
    co = E[E.section == "coef"]
    L += ["", "What an input is worth (points per team per unit in the 2023-25 live fits; game total per unit, total equation fit 2013-24): " +
          "; ".join(f"{r.item} {r.points_per_unit_team:+.3f} / " + ("not in the total" if pd.isna(r.total_per_unit) else f"{r.total_per_unit:+.3f}") for r in co.itertuples()), ""]
    # cost
    L += ["## 2. What the forecast costs the model", "",
          "The live walk-forward refit before every week (fresh trees), the priced week's weather inputs from the d1 forecast; the fits",
          "are unchanged. `fc_live`: the forecast wherever it exists (the live path). `fc_swap`: only where the actual reading exists too.",
          "Team points miss / total miss over every regular-season game of the season; spread flag and totals flag W-L on the live rules.", "",
          "| variant | season | team miss | total miss | spread flag | totals flag | cal. log loss | forecast games: team miss | total miss |", "|---|---|---|---|---|---|---|---|---|"]
    for k in ["actual", "fc_swap", "fc_live", "fc_temp_only", "fc_wind_only", "fc_rain_only"]:
        if k not in S.index:
            continue
        r = S.loc[k]
        for w in WINS:
            L.append(f"| {k} | {w} | {r[f'team_mae_{w}']:.4f} | {r[f'total_mae_{w}']:.4f} | {int(r[f'sp_w_{w}'])}-{int(r[f'sp_l_{w}'])} | {int(r[f'to_w_{w}'])}-{int(r[f'to_l_{w}'])} | {r[f'll_cal_{w}']:.4f} | {_f(r[f'sub_team_mae_{w}'])} ({int(r[f'sub_n_{w}'])} g) | {_f(r[f'sub_total_mae_{w}'])} |")
    L += [""]
    # candidates
    base = S.loc["fc_live"]
    L += ["## 3. Candidates (each against `fc_live`, scored with forecast inputs)", "",
          "Change in team points miss / total miss (negative = better), spread and totals flag W-L change, calibrated log loss change.", "",
          "| candidate | season | d team miss | d total miss | d spread W-L | d totals W-L | d log loss |", "|---|---|---|---|---|---|---|"]
    for k in CAND:
        r = S.loc[k]; d = deltas(r, base)
        for w in WINS:
            L.append(f"| {k} | {w} | {d[f'd_team_{w}']:+.4f} | {d[f'd_total_{w}']:+.4f} | {int(d[f'd_sp_{w}']):+d} | {int(d[f'd_to_{w}']):+d} | {d[f'd_ll_{w}']:+.5f} |")
    L += ["", "| candidate | seasons it changes | rule 1 (miss) | rule 2 (flags) | placebo beaten / draws | verdict | why |", "|---|---|---|---|---|---|---|"]
    for v in V.itertuples():
        sc = " ".join(str(s) for s in sorted({int(g[:4]) for g in changed.get(v.name, []) if g in reg})) if v.name != "b_train_fc" else "2022-25 (fits)"
        L.append(f"| {v.name} | {sc} | {v.rule1} | {v.rule2} | {'' if pd.isna(v.placebo_beaten) else int(v.placebo_beaten)} / {v.placebo_draws} | {v.verdict} | {v.why} |")
    L += ["", f"Engine check: the `actual` variant against situational_game.lean_walk_forward on 2023: max differences {json.dumps({k: v for k, v in chk.items() if k in ('model_spread', 'model_total', 'p_home', 'p_over_emp')})}; "
          f"against pred_v3 (cached trees) mean |spread| difference {chk['vs_pred_v3_spread_mean_abs']:.3f}.", ""]
    a, f = S.loc["actual"], S.loc["fc_live"]
    net = lambda r, k, w: int(r[f"{k}_w_{w}"] - r[f"{k}_l_{w}"])
    L += ["## Verdict", "",
          "Cost of the forecast (fc_live minus actual), team points miss " + " / ".join(f"{f[f'team_mae_{w}'] - a[f'team_mae_{w}']:+.4f}" for w in WINS) +
          ", total miss " + " / ".join(f"{f[f'total_mae_{w}'] - a[f'total_mae_{w}']:+.4f}" for w in WINS) + f" ({' / '.join(WINS)}); spread-flag net W-L change " +
          " / ".join(f"{net(f, 'sp', w) - net(a, 'sp', w):+d}" for w in WINS) + ", totals-flag net change " + " / ".join(f"{net(f, 'to', w) - net(a, 'to', w):+d}" for w in WINS) + ".",
          "The cost is small and not one-signed: the forecast priced 2025 better than the actuals did, which says the difference is",
          "within the noise of ~180 forecast games a season. Rain drives the 2024 cost (the 1 mm forecast calls rain in a third as",
          "many games as the play-by-play text records, so most rain games are priced dry); rain and wind both drive the 2025 gain;",
          "temperature moves almost nothing (the cold flag flips in 3% of games).", "",
          "No candidate passes the rule. With two to four scoreable seasons of 177-190 outdoor games, and gains of at most a few",
          "thousandths of a point, none of these results would be strong enough to adopt even if one had passed every season;",
          "the live weather treatment stays as it is. Rules 1 and 2 are checked on 2022-25 only (the round-3 windows 2015-18 and",
          "2019-22 have no archived forecast), and the placebo is run for the test-side candidates (train_fc's refit placebo",
          "runs only past the rule's gate, which it does not reach).", ""]
    (REP / "weather_forecast.md").write_text("\n".join(L) + "\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--stage", required=True); ap.add_argument("--jobs", type=int, default=4)
    a = ap.parse_args()
    {"errors": stage_errors, "run": stage_run, "placebo_b": lambda: stage_placebo_b(a.jobs), "decomp": stage_decomp, "report": stage_report}[a.stage]()
