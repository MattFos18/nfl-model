"""A home-field term that follows recent seasons (27 Sep 2026). The calibration audit (reports/calibration_audit.md)
found the home win chance running hot when the home side is a slight underdog: said 45.5%, won 39.1% (2015-25, n 556,
z -3.0; 2023-25 alone 45.0% said, 33.9% won, n 180). In 2019-22 the model said 56.0% home and 52.4% happened, its
margin ran 0.98 points too far toward the home side, and the fitted home coefficient was 2.2 / 1.9 points in 2019 /
2020 against a realised home margin near zero. The one league home-field term (`home` in model.SIT_FEATS) is fit by
ridge on every season since 2013 with equal weight, so it lags the fall in home advantage. Earlier tests were about
WHO has more home field (per team, 21-22 Sep; home x division and home x short week, 23 Sep: all lost); this one is
about WHEN, the league-wide level moving over time.

Walk-forward over 2015-2025 (the weekly refit, the seven-model blend, every game priced with earlier games only), the
three windows (2015-18 untouched, 2019-22 tuning, 2023-25 held out). Candidates, nothing fit on the evaluation windows:

  A   recency weights on the whole points fit: every training game weighted decay ** (seasons old), decay 0.8 / 0.7 /
      0.6, on the ridge, the five blend ridges and the trees (a full walk-forward each). 23 Sep's recency.py tested the
      ridge alone before the blend existed and lost the held-out window.
  A2  the same decay applied only to the home term (two stage): the fit as now, then the home term re-read from the
      training games' residuals weighted by season age.
  B   a rolling home term: the home field seen in each training game (actual margin minus the ridge margin, plus the
      fitted home coefficient, non-neutral games) averaged over the last K completed seasons (K 2 / 3 / 4), shrunk
      toward the fitted coefficient with N games of weight (N 0 / 100 / 300). N 0 is the plain two-stage refit.
  C   B plus the current season's completed weeks, weighted 1x or 3x a game, so 2020 (empty stadiums) is caught during
      2020 rather than the season after.
  D   home x era: home * (season >= 2020) as an extra input to every model in the blend. The coefficient is learned
      from 2020 games as they arrive (zero before them), but the break year is hindsight; it tests whether one level
      shift explains the miss.

A2, B and C shift the blend's spread by (rolling term - fitted coefficient) and re-price the home win chance with the
same week's fitted distribution (model.price_at, the DIST the base pass stored); the total is untouched. That is what
the change would do inside walk_forward, so they are computed from one base pass plus a ridge-only refit per week.

Scored per window: the miss (margin and total mean absolute error, regular season with a line, as backtest_v3.md
and the README report it), the bets (the 4-point flag and the totals flag, weeks 1 to 17, picks.rule_records'
grading) and the home-win calibration by decile (the audit's check: a bucket of 150+ games more than 2.5 binomial
standard errors out fails), plus the pooled 2015-25 table the check also reads. The standing rule: adopted only if
better on all three windows on both the miss and the bets.

Output: reports/home_field_recency.csv (every variant x window x metric, long) and reports/home_field_recency.md.
Runtime: one full pass is about five minutes on four cores; the five full passes run in parallel, one core each."""
import os, sys, time
os.environ.setdefault("OMP_NUM_THREADS", "1")   # one core per full pass; the passes run side by side
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from multiprocessing import get_context
import numpy as np, pandas as pd
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import HistGradientBoostingRegressor
from nflmodel import model as M, backtest as B, picks as P
from nflmodel.model import OUT

REP = Path(__file__).resolve().parent.parent / "reports"
SEASONS = range(2015, 2026)
ERA = 2020                     # D's break year
CAL_MIN_N, CAL_Z = 150, 2.5    # the audit's check (tie_check.CAL_MIN_N, CAL_Z)
CAL_WINDOWS = list(P.WINDOWS.items()) + [("2015-25", (2015, 2025))]
UNDER = P.TOTAL_SHADOW["prob"]
GAMES = pd.read_parquet(OUT / "games.parquet")
FULL = {"base": None, "A decay 0.8": ("A", 0.8), "A decay 0.7": ("A", 0.7), "A decay 0.6": ("A", 0.6), "D home x era (2020+)": ("D", None)}


def weighted_fits(decay):
    """model.fit_points and fit_blend with sample weights decay ** (seasons before the season being priced)."""
    def wts(train): return decay ** (train.season.max() - train.season.values)
    def fit_points(train, alpha=M.RIDGE):
        m = make_pipeline(StandardScaler(), Ridge(alpha=alpha)); m.fit(train[M.FEATS].values, train.pf.values, ridge__sample_weight=wts(train)); return m
    def fit_blend(train, ridge_model=None, alpha=10.0):
        w = wts(train); ms = {"ridge": (ridge_model or fit_points(train, alpha), list(M.FEATS))}
        for k, (extra, al) in M.BLEND.items():
            cols = list(M.FEATS) + extra
            m = make_pipeline(StandardScaler(), Ridge(alpha=al)); m.fit(train[cols].fillna(train[cols].mean()).values, train.pf.values, ridge__sample_weight=w); ms[k] = (m, cols)
        t = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.03, max_leaf_nodes=8, min_samples_leaf=60, l2_regularization=1.0, random_state=0)
        t.fit(train[M.FEATS].values, train.pf.values, sample_weight=w); ms["trees"] = (t, list(M.FEATS))
        ms["_means"] = train[sorted({c for m, cols in ms.values() for c in cols})].mean()
        return ms
    return fit_points, fit_blend


def full_pass(name):
    """One walk-forward under a variant (in its own process, so the patches stay local): the prediction table and DIST."""
    spec = FULL[name]
    f = M.with_trends(pd.read_parquet(OUT / "features_asof.parquet"))
    if spec and spec[0] == "A":
        M.fit_points, M.fit_blend = weighted_fits(spec[1])
    if spec and spec[0] == "D":
        prep0 = M.prep
        def prep_era(x):
            x = prep0(x); x["home_era"] = x.home * (x.season >= ERA).astype(float); return x
        M.prep = prep_era; M.FEATS = list(M.FEATS) + ["home_era"]
    t0 = time.time(); pred = M.walk_forward(f, SEASONS)
    print(f"{name}: {len(pred)} games in {time.time() - t0:.0f}s", flush=True)
    return name, pred, dict(M.DIST)


def home_seen(f):
    """Per (season, week) fit of the walk: the fitted home coefficient and, for every training game, the home field seen
    in it: actual margin minus the ridge margin, plus the coefficient (so a game that went as the equation said reads
    as the coefficient). Neutral-site games left out."""
    fp = M.prep(f); played = fp[fp.pf.notna()]; ih = M.FEATS.index("home"); out = {}
    for s in SEASONS:
        for wk in sorted(fp[fp.season == s].week.unique()):
            train = played[(played.season >= M.TRAIN_FROM) & ((played.season < s) | ((played.season == s) & (played.week < wk)))]
            m = M.fit_points(train); coef = float(m[-1].coef_[ih] / m[0].scale_[ih])
            tr = train.assign(pred=m.predict(train[M.FEATS].values))
            h = tr[tr.home == 1].set_index("game_id"); a = tr[tr.home == 0].set_index("game_id"); ids = h.index.intersection(a.index)
            keep = h.loc[ids, "neutral"].values == 0
            seen = ((h.loc[ids, "pf"] - a.loc[ids, "pf"]) - (h.loc[ids, "pred"] - a.loc[ids, "pred"]) + coef).values[keep]
            out[(int(s), int(wk))] = (coef, h.loc[ids, "season"].values[keep].astype(int), seen)
    return out


def rolling_term(seen, s, wk, K=None, cur_w=0.0, N=0.0, decay=None):
    """The home term for the fit of (s, wk): the weighted mean of the home field seen in the training games, shrunk
    toward the fitted coefficient with N games of weight. Window: the last K completed seasons (weight 1) and the
    current season's played games (weight cur_w); or every season weighted decay ** age when decay is given."""
    coef, seasons, x = seen[(s, wk)]
    if decay is not None:
        w = decay ** (s - seasons).astype(float)
    else:
        w = np.where((seasons >= s - K) & (seasons < s), 1.0, np.where(seasons == s, cur_w, 0.0))
    return (float((w * x).sum()) + N * coef) / (float(w.sum()) + N), coef


def shifted(pred, dist, seen, **kw):
    """The base table with the spread shifted by (rolling home term - fitted coefficient) and p_home re-priced with the
    same week's distribution; the total untouched. Also the term used, per game."""
    p = pred.copy(); shift = np.zeros(len(p)); term = np.zeros(len(p))
    for (s, wk), idx in p.groupby(["season", "week"]).indices.items():
        h, coef = rolling_term(seen, int(s), int(wk), **kw); shift[idx] = h - coef; term[idx] = h
    p["model_spread"] = p.model_spread + shift; p["home_term"] = term
    p["home_exp"] = (p.model_total + p.model_spread) / 2; p["away_exp"] = (p.model_total - p.model_spread) / 2
    p["p_home"] = [M.price_at(mu, mt, sl, tl, dist[(int(s), int(w))])["p_home"] for mu, mt, sl, tl, s, w in zip(p.model_spread, p.model_total, p.spread_line, p.total_line, p.season, p.week)]
    return p


def cal_table(x, key, said, y, edges):
    b = pd.cut(key, edges, right=False); t = x.groupby(b, observed=True).agg(n=(y, "size"), said=(said, "mean"), actual=(y, "mean"))
    t["se"] = np.sqrt(t.said * (1 - t.said) / t.n); t["z"] = (t.actual - t.said) / t.se
    return t


def score(pred) -> list[dict]:
    """Every metric per window, long: the miss, the bets, the home-win calibration (the check's failing buckets, the
    slight-underdog bucket, the Brier score, said and happened home) and the home term used."""
    d = B.join(pred, GAMES); d = d[(d.game_type == "REG") & d.spread_line.notna() & d.home_score.notna()].copy()
    d["hw"] = (d.result > 0).astype(float) + 0.5 * (d.result == 0)
    rows = []
    for w, (a, b) in CAL_WINDOWS:
        x = d[d.season.between(a, b)]; r = {"window": w}
        if w in P.WINDOWS:
            r["margin_mae"] = float((x.result - x.model_spread).abs().mean()); r["total_mae"] = float((x.total - x.model_total).abs().mean())
            fw, fl = P.record(x, P.rule_mask(x, P.SPREAD_EDGE)); uw, ul = P.record(x, P.rule_mask(x, UNDER, "under_prob"), "under_prob")
            r.update({"flag_record": f"{fw}-{fl}", "flag_pct": fw / (fw + fl) if fw + fl else np.nan, "flag_net": fw - fl,
                      "under_record": f"{uw}-{ul}", "under_pct": uw / (uw + ul) if uw + ul else np.nan})
            r["margin_bias"] = float((x.result - x.model_spread).mean())   # results minus model: negative = the model leant home too far
            if "home_term" in x.columns:
                r["home_term_mean"] = float(x.home_term.mean())
        t = cal_table(x, x.p_home, "p_home", "hw", np.arange(0, 1.01, 0.1)); bad = t[(t.n >= CAL_MIN_N) & (t.z.abs() > CAL_Z)]
        k = pd.Interval(0.4, 0.5, closed="left")
        r.update({"cal_fails": int(len(bad)), "cal_fail_buckets": "; ".join(f"{ix}: said {q.said:.3f} won {q.actual:.3f} n {int(q.n)} z {q.z:+.1f}" for ix, q in bad.iterrows()),
                  "cal_worst_z": float(t[t.n >= CAL_MIN_N].z.abs().max()) if (t.n >= CAL_MIN_N).any() else np.nan,
                  "p40_50_n": int(t.loc[k, "n"]) if k in t.index else 0, "p40_50_said": float(t.loc[k, "said"]) if k in t.index else np.nan,
                  "p40_50_won": float(t.loc[k, "actual"]) if k in t.index else np.nan, "p40_50_z": float(t.loc[k, "z"]) if k in t.index else np.nan,
                  "brier": float(((x.p_home - x.hw) ** 2).mean()), "said_home": float(x.p_home.mean()), "won_home": float(x.hw.mean()), "games": int(len(x))})
        rows.append(r)
    return rows


def qualifies(r: pd.DataFrame, base: pd.DataFrame) -> bool:
    """Better on all three windows on both the miss (margin and total not worse, margin lower) and the bets (flag rate
    higher, totals flag rate not lower)."""
    ok = True
    for w in P.WINDOWS:
        a, b = r[r.window == w].iloc[0], base[base.window == w].iloc[0]
        ok &= (a.margin_mae < b.margin_mae) and (a.total_mae <= b.total_mae + 1e-9) and (a.flag_pct > b.flag_pct) and (a.under_pct >= b.under_pct - 1e-9)
    return bool(ok)


def main():
    t0 = time.time()
    with get_context("fork").Pool(min(4, len(FULL))) as pool:
        full = {n: (p, d) for n, p, d in pool.map(full_pass, list(FULL))}
    print(f"full passes done in {time.time() - t0:.0f}s", flush=True)
    base, dist = full["base"]
    f = M.with_trends(pd.read_parquet(OUT / "features_asof.parquet"))
    seen = home_seen(f); print(f"home field seen per fit in {time.time() - t0:.0f}s", flush=True)
    variants = {n: p for n, (p, _) in full.items()}
    for K in (2, 3, 4):
        for N in (0, 100, 300):
            variants[f"B last {K} seasons, shrink {N}"] = shifted(base, dist, seen, K=K, N=N)
    for K in (2, 3):
        for cw in (1.0, 3.0):
            for N in (0, 100, 300):
                variants[f"C last {K} seasons + this season x{cw:g}, shrink {N}"] = shifted(base, dist, seen, K=K, cur_w=cw, N=N)
    for dc in (0.8, 0.7, 0.6):
        for N in (0, 100):
            variants[f"A2 home term decay {dc}, shrink {N}"] = shifted(base, dist, seen, decay=dc, N=N)
    rows = []
    for n, p in variants.items():
        for r in score(p):
            rows.append({"variant": n, **r})
    wide = pd.DataFrame(rows)
    b = wide[wide.variant == "base"]
    wide["qualifies"] = [qualifies(wide[wide.variant == v], b) for v in wide.variant]
    long = wide.melt(id_vars=["variant", "window"], var_name="metric", value_name="value").dropna()
    long.to_csv(REP / "home_field_recency.csv", index=False)
    # the home term each variant carried by season (what the model believed home field was worth), for the report
    terms = {}
    for n, p in variants.items():
        col = p["home_term"] if "home_term" in p.columns else p["coef_home"]
        terms[n] = p.assign(t=col).groupby("season").t.mean()
    terms = pd.DataFrame(terms).T
    write_md(wide, terms)
    print(wide[wide.window.isin(P.WINDOWS)][["variant", "window", "margin_mae", "total_mae", "flag_record", "under_record", "cal_fails", "p40_50_said", "p40_50_won", "p40_50_z", "qualifies"]].round(3).to_string(index=False))
    print("DONE", f"{time.time() - t0:.0f}s")


def write_md(wide: pd.DataFrame, terms: pd.DataFrame) -> None:
    b = wide[wide.variant == "base"].set_index("window")
    L = ["# A home-field term that follows recent seasons (27 Sep 2026)", "",
         "`experiments/home_field_recency.py`. Walk-forward 2015-2025 with the weekly refit and the blend; every quantity as of the game. "
         "Miss = mean absolute error of the spread and of the total (regular season with a line). Bets = the 4-point flag and the totals flag "
         "(unders at 55%+), weeks 1 to 17, wins-losses. Calibration = the audit's home-win check: buckets of the stated home chance with 150+ games "
         "more than 2.5 standard errors out (fails), and the slight-underdog bucket [0.4, 0.5) said / won / z. Full table: `reports/home_field_recency.csv`.", "",
         f"Base: margin miss {b.loc['2015-18', 'margin_mae']:.3f} / {b.loc['2019-22', 'margin_mae']:.3f} / {b.loc['2023-25', 'margin_mae']:.3f}, "
         f"flag {b.loc['2015-18', 'flag_record']} / {b.loc['2019-22', 'flag_record']} / {b.loc['2023-25', 'flag_record']}, "
         f"failing buckets {int(b.loc['2015-18', 'cal_fails'])} / {int(b.loc['2019-22', 'cal_fails'])} / {int(b.loc['2023-25', 'cal_fails'])} (pooled 2015-25: {int(b.loc['2015-25', 'cal_fails'])}).", "",
         "## Every variant, the three windows (2015-18 untouched / 2019-22 tuning / 2023-25 held out)", "",
         "| Variant | Margin miss | Total miss | Flag | Totals flag | Home-win buckets failing (pooled) | [0.4, 0.5) said / won (z) | Qualifies |", "|---|---|---|---|---|---|---|---|"]
    for v in wide.variant.unique():
        r = wide[wide.variant == v].set_index("window"); ws = list(P.WINDOWS)
        cell = lambda k, fmt: " / ".join(fmt(r.loc[w, k]) for w in ws)
        f3 = lambda q: f"{q:.3f}"; fi = lambda q: str(int(q))
        dog = " / ".join("{:.2f}-{:.2f} ({:+.1f})".format(r.loc[w, "p40_50_said"], r.loc[w, "p40_50_won"], r.loc[w, "p40_50_z"]) for w in ws)
        L.append(f"| {v} | {cell('margin_mae', f3)} | {cell('total_mae', f3)} | {cell('flag_record', str)} | {cell('under_record', str)} | "
                 f"{cell('cal_fails', fi)} ({int(r.loc['2015-25', 'cal_fails'])}) | {dog} | {'yes' if r.qualifies.iloc[0] else 'no'} |")
    L += ["", "## The home term carried, by season (points; the base is the fitted coefficient, the others the term used)", "",
          "| Variant | " + " | ".join(str(c) for c in terms.columns) + " |", "|---|" + "---|" * len(terms.columns)]
    for v, r in terms.iterrows():
        L.append(f"| {v} | " + " | ".join(f"{q:.2f}" for q in r.values) + " |")
    q = wide[wide.qualifies & (wide.variant != "base")].variant.unique()
    L += ["", "## Verdict", "", (f"Qualifying on all three windows on both the miss and the bets: {', '.join(q)}." if len(q) else
          "No variant is better on all three windows on both the miss and the bets; the model is untouched (decision log, 27 Sep 2026).")]
    (REP / "home_field_recency.md").write_text("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
