"""A calibrated chance for every yards prop line (29 Sep 2026). The player projection (nflmodel/props.py) sets each yards
line L as a median (the median factor MED / MED_TIER on the projected mean M) and keeps the mean beside it, but carries
no chance that the actual beats a book number x: the grading picks a side by edge = projection - line, and the page
ranks only game bets, which have a calibrated chance. Here every player-game of the walk-forward frame
(experiments/props_by_season.build: the live rule's inputs, its line L, its mean M and what happened) is given
P(actual > x) for an arbitrary book number x from three families, every parameter fitted on 2017-18 only, and scored on
2019-22 and 2023-25 at hypothetical book numbers x = L + delta (delta in -15 .. +15 yards in steps of 5; passing x3;
receptions -2 .. +2 catches; a number below 0.5 is dropped, no book hangs one):

  normal    actual ~ Normal(M, s), s = c x M (normal_prop); s = a + b x M (normal_lin); s = a x M^b (normal_pow);
            c per tier of M (normal_tier). P(over x) = 1 - Phi((x - M) / s).
  log-normal / gamma with mean M and a dispersion fitted on 2017-18: lognorm (sigma), lognorm_tier (sigma per tier of
            M), lognorm_pow (sigma = a x M^b); gamma (shape k), gamma_tier (k per tier of M), gamma_pow (k = a x M^b).
            P(over x) = 1 - F(x) with F the log-normal (mu = ln M - sigma^2 / 2) or gamma (shape k, scale M / k) cdf;
            1 when x <= 0.
  empirical the distribution of actual / L (emp_ratio) or actual - L (emp_diff) over the earlier seasons' rows in the
            same tier of L (receiving and rushing 0-20, 20-40, 40-60, 60-80, 80+; passing 0-175, 175-225, 225-275,
            275+; receptions 0-2, 2-4, 4-6, 6+), walk-forward: a 2019+ row reads only seasons before it, 2017 on.
            P(over x) = share of those rows with actual / L > x / L (or actual - L > x - L).
            emp_knn_ratio / emp_knn_diff: the same, but over the K earlier rows nearest in L (K = 10% of the history, 300 to
            1500) instead of a fixed tier, since within the 0-20 tier the shape of actual / L changes fast with L.
  L-centred normal_L (mean L, s = a + b L), lognorm_L (median L, sigma; sigma per tier of L: lognorm_L_tier; sigma =
            a L^b: lognorm_L_pow): P(over L) = 0.5 by construction. Added after the first pass showed the passing mean M
            sits 14% above the actual mean (the median factor absorbs a bias there), so a chance centred on M is off.
  receptions (counts) also: poisson (mean M = the receptions line / MED_CATCH) and negbin (mean M, size r fitted).
Every parametric dispersion is chosen on 2017-18 by the same objective the study scores: the mean log loss of P(over x)
over the delta grid. Tiers for the parametric forms are tiers of M with the same edges as the empirical tiers of L.
Scores: Brier and log loss of P(actual > x) against what happened (a tie at x is left out, a push), per stat x
distribution x window x delta; a reliability table (bins of the stated chance, pooled over the deltas, against the
realised over rate, n per bin); and at delta 0 the mean stated chance, its mean distance from 0.5 (the line is the
median, so a good distribution says about 0.5 there) and the realised over rate.
ADOPTION RULE, set before the run: per stat, the distribution with the lowest mean log loss over the deltas on 2019-22
is adopted only if it is also the lowest on 2023-25 (the family, not the tier count: a tier variant of the same family
counts as the family) and its reliability is within 3 points of the stated chance in every bin with n >= 200 on both
windows. Otherwise the best one that passes the reliability check on both windows, and the report says so.
No market inputs: the frame carries no book line; x is an offset from our own line. Walk-forward, as-of only.
Output reports/props_chance.csv, reports/props_chance_reliability.csv, reports/props_chance.md.
Usage: python -m experiments.props_chance   (the frames are built once and cached as parquet in the scratchpad)"""
import numpy as np, pandas as pd, pathlib, sys, time
from scipy import stats, optimize
from scipy.special import gammaincc, gammaln
from nflmodel import props as PR
SCR = pathlib.Path("/tmp/claude-0/-home-user/c1e0d18e-681a-50ba-b0bb-6c809c2e3dee/scratchpad/props_chance"); SCR.mkdir(parents=True, exist_ok=True)
FIT = (2017, 2018); WIN = {"2019-22": (2019, 2022), "2023-25": (2023, 2025)}
STATS = {"rec_yards": ("rec", "yds"), "rush_yards": ("rush", "yds"), "pass_yards": ("pass", "yds"), "rec_catches": ("rec", "catch")}
DELTAS = {"rec_yards": [-15, -10, -5, 0, 5, 10, 15], "rush_yards": [-15, -10, -5, 0, 5, 10, 15], "pass_yards": [-45, -30, -15, 0, 15, 30, 45], "rec_catches": [-2, -1, 0, 1, 2]}
TIERS = {"rec_yards": [0, 20, 40, 60, 80, np.inf], "rush_yards": [0, 20, 40, 60, 80, np.inf], "pass_yards": [0, 175, 225, 275, np.inf], "rec_catches": [0, 2, 4, 6, np.inf]}
MIN_X = 0.5; BINS = np.round(np.arange(0, 1.01, 0.1), 1); REL_N, REL_TOL = 200, 0.03; EPS = 1e-4
OUT_CSV, OUT_REL, OUT_MD = "reports/props_chance.csv", "reports/props_chance_reliability.csv", "reports/props_chance.md"
_NS = None


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def frame(kind):
    """The by-season frame for the kind, built once (the slow part) and cached: L the live rule's yards line (median
    factor, team reconciliation, injury and snap factors), M the mean scaled the same way (L / the median factor of the
    unscaled mean, which is what the card's proj_*_yards_mean is), act_yds; receptions: the line and its mean."""
    global _NS
    p = SCR / f"frame_{kind}.parquet"
    if p.exists():
        log("cached frame", kind); return pd.read_parquet(p)
    if _NS is None:
        log("loading props_by_season (the frame builder)")
        src = pathlib.Path(__file__).with_name("props_by_season.py").read_text().split("by_season, by_pos, by_bucket = [], [], []")[0]
        _NS = {"__name__": "bys"}; exec(compile(src, "bys", "exec"), _NS)
    log("building frame", kind); t0 = time.time()
    f, ev = _NS["build"](kind)
    keep = ["pid", "posteam", "season", "week", "game_id", "pos", "act_n", "act_yds", "mean_line", "yds_line"] + (["act_catch", "catch_line"] if kind == "rec" else [])
    f = f[keep].copy(); f["M"] = f.yds_line / PR.med_factor(kind, f.mean_line.values); f["L"] = f.yds_line
    if kind == "rec": f["M_catch"] = f.catch_line / PR.MED_CATCH; f["L_catch"] = f.catch_line
    f = f[(f.L > 0) & (f.M > 0)].reset_index(drop=True); f.to_parquet(p)
    log(f"built {kind}: {len(f)} rows in {time.time() - t0:.0f}s"); return f


# ---------- distributions: each is fit(y, M, X) -> params on the fit rows, p_over(M, x, params) -> P(actual > x) ----------
def _phi_over(x, mean, s):
    return 1 - stats.norm.cdf((x - mean) / np.maximum(s, 1e-6))


def _ln_over(x, M, sig):
    sig = np.maximum(sig, 1e-6); mu = np.log(M) - sig ** 2 / 2
    with np.errstate(divide="ignore", invalid="ignore"):
        out = 1 - stats.norm.cdf((np.log(np.where(x > 0, x, 1.0)) - mu) / sig)
    return np.where(x > 0, out, 1.0)


def _gamma_over(x, M, k):
    k = np.maximum(k, 1e-3)
    with np.errstate(divide="ignore", invalid="ignore"):
        out = gammaincc(k, np.where(x > 0, x, 0.0) * k / M)
    return np.where(x > 0, out, 1.0)


def _nb_over(x, M, r):
    """P(N > x) for a negative binomial with mean M and size r (var = M + M^2 / r): P(N >= floor(x) + 1)."""
    r = np.maximum(r, 1e-3); p = r / (r + M); return 1 - stats.nbinom.cdf(np.floor(x), r, p)


def _pois_over(x, M):
    return 1 - stats.poisson.cdf(np.floor(x), M)


def _lnL_over(x, L, sig):
    """Log-normal with median L (mu = ln L): P(over x) = 1 - Phi(ln(x / L) / sigma)."""
    sig = np.maximum(sig, 1e-6)
    with np.errstate(divide="ignore", invalid="ignore"):
        out = 1 - stats.norm.cdf(np.log(np.where(x > 0, x, 1.0) / L) / sig)
    return np.where(x > 0, out, 1.0)


FAMILY = {   # name -> (p_over(x, M, L, theta), the parameter count, the initial guess, the bounds, the family key)
    "normal_prop": (lambda x, M, L, th: _phi_over(x, M, th[0] * M), 1, [0.7], [(0.05, 5.0)], "normal"),
    "normal_lin": (lambda x, M, L, th: _phi_over(x, M, th[0] + th[1] * M), 2, [5.0, 0.5], [(0.0, 500.0), (0.0, 5.0)], "normal"),
    "normal_pow": (lambda x, M, L, th: _phi_over(x, M, th[0] * M ** th[1]), 2, [1.5, 0.8], [(0.01, 200.0), (0.05, 1.5)], "normal"),
    "lognorm": (lambda x, M, L, th: _ln_over(x, M, th[0]), 1, [0.6], [(0.05, 3.0)], "lognorm"),
    "lognorm_pow": (lambda x, M, L, th: _ln_over(x, M, th[0] * M ** th[1]), 2, [2.0, -0.3], [(0.05, 50.0), (-1.5, 0.5)], "lognorm"),
    "gamma": (lambda x, M, L, th: _gamma_over(x, M, th[0]), 1, [2.0], [(0.1, 50.0)], "gamma"),
    "gamma_pow": (lambda x, M, L, th: _gamma_over(x, M, th[0] * M ** th[1]), 2, [0.3, 0.5], [(0.001, 50.0), (-0.5, 1.5)], "gamma"),
    # centred on the line rather than the mean (the median is L by construction, so P(over L) = 0.5): a normal around L with s = a + b L, a log-normal with median L
    "normal_L": (lambda x, M, L, th: _phi_over(x, L, th[0] + th[1] * L), 2, [5.0, 0.5], [(0.0, 500.0), (0.0, 5.0)], "normal_L"),
    "lognorm_L": (lambda x, M, L, th: _lnL_over(x, L, th[0]), 1, [0.6], [(0.05, 3.0)], "lognorm_L"),
    "lognorm_L_pow": (lambda x, M, L, th: _lnL_over(x, L, th[0] * L ** th[1]), 2, [2.0, -0.3], [(0.05, 50.0), (-1.5, 0.5)], "lognorm_L"),
}
TIERED = {"normal_tier": "normal_prop", "lognorm_tier": "lognorm", "gamma_tier": "gamma", "lognorm_L_tier": "lognorm_L"}   # the one-parameter form fitted per tier (of M; of L for the L-centred form)
COUNT_FAMILY = {"poisson": (lambda x, M, L, th: _pois_over(x, M), 0, [], [], "poisson"), "negbin": (lambda x, M, L, th: _nb_over(x, M, th[0]), 1, [5.0], [(0.1, 500.0)], "negbin")}
KNN_FRAC, KNN_MIN, KNN_MAX = 0.10, 300, 1500   # emp_knn: the K earlier rows nearest in L, K = 10% of the history, at least 300, at most 1500


def fam(n):
    """The family of a distribution name (a tier variant counts as its family)."""
    return FAMILY[n][4] if n in FAMILY else COUNT_FAMILY[n][4] if n in COUNT_FAMILY else FAMILY[TIERED[n]][4] if n in TIERED else n.replace("_ratio", "").replace("_diff", "")


def scores(p, o):
    p = np.clip(p, EPS, 1 - EPS); return float(np.mean((p - o) ** 2)), float(-np.mean(o * np.log(p) + (1 - o) * np.log(1 - p)))


def grid(y, L, deltas):
    """Every (row, delta) with x = L + delta >= MIN_X and no tie: the x, the outcome, the row index."""
    xs, os_, idx, ds = [], [], [], []
    for dl in deltas:
        x = L + dl; m = (x >= MIN_X) & (y != x); xs.append(x[m]); os_.append((y[m] > x[m]).astype(float)); idx.append(np.flatnonzero(m)); ds.append(np.full(int(m.sum()), dl))
    return np.concatenate(xs), np.concatenate(os_), np.concatenate(idx), np.concatenate(ds)


def fit_family(name, y, M, L, deltas):
    fn, npar, x0, bnd, _ = {**FAMILY, **COUNT_FAMILY}[name]
    if npar == 0: return []
    x, o, idx, _ = grid(y, L, deltas); Mi, Li = M[idx], L[idx]
    obj = lambda th: scores(fn(x, Mi, Li, np.asarray(th, float)), o)[1]
    if npar == 1:
        r = optimize.minimize_scalar(lambda t: obj([t]), bounds=bnd[0], method="bounded"); return [float(r.x)]
    r = optimize.minimize(obj, x0, method="Nelder-Mead", options={"xatol": 1e-4, "fatol": 1e-7, "maxiter": 2000})
    th = np.clip(r.x, [b[0] for b in bnd], [b[1] for b in bnd]); return [float(v) for v in th]


def fit_tiered(base, y, M, L, deltas, edges):
    t = np.digitize(L if base.endswith("_L") else M, edges[1:-1]); out = []
    for i in range(len(edges) - 1):
        m = t == i; out.append(fit_family(base, y[m], M[m], L[m], deltas)[0] if m.sum() >= 50 else np.nan)
    out = pd.Series(out).ffill().bfill().tolist(); return out


def p_parametric(name, params, x, M, L, edges=None):
    if name in TIERED:
        base = TIERED[name]; fn = FAMILY[base][0]; t = np.digitize(L if base.endswith("_L") else M, edges[1:-1]); th = np.asarray(params, float)[t]   # one parameter per row, by its tier
        return fn(x, M, L, [th])
    fn = {**FAMILY, **COUNT_FAMILY}[name][0]; return fn(x, M, L, np.asarray(params, float))


def p_knn(kind_key, f, y, L, x, idx, deltas):
    """Walk-forward, local: for a row of season S with line L, the K rows of seasons < S nearest to it in L (K = KNN_FRAC of
    the history, between KNN_MIN and KNN_MAX), and the share of them whose ratio (or difference) beats the threshold."""
    season = f.season.values; val = (y / L) if kind_key == "ratio" else (y - L); out = np.full(len(x), np.nan)
    thr = (x / L[idx]) if kind_key == "ratio" else (x - L[idx]); rid = idx
    for s in np.unique(season[idx]):
        if s < WIN["2019-22"][0]: continue
        hm = season < s; order = np.argsort(L[hm]); hL, hv = L[hm][order], val[hm][order]; n = len(hL); K = int(min(KNN_MAX, max(KNN_MIN, KNN_FRAC * n))); half = K // 2
        rows = np.flatnonzero(season == s); pos = np.clip(np.searchsorted(hL, L[rows]) - half, 0, max(n - K, 0))
        where = {r: i for i, r in enumerate(rows)}; sel = np.flatnonzero(season[idx] == s)
        for j in sel:
            i = where[rid[j]]; w = hv[pos[i]:pos[i] + K]; out[j] = np.mean(w > thr[j])
    return out


def p_empirical(kind_key, f, y, L, x, idx, edges):
    """Walk-forward: for a row of season S, the share of the rows of seasons < S in its tier of L whose ratio (or
    difference) beats the threshold. kind_key 'ratio' or 'diff'."""
    season = f.season.values; tier = np.digitize(L, edges[1:-1]); val = (y / L) if kind_key == "ratio" else (y - L)
    thr = (x / L[idx]) if kind_key == "ratio" else (x - L[idx]); out = np.full(len(x), np.nan); si, ti = season[idx], tier[idx]
    for s in np.unique(si):
        if s < WIN["2019-22"][0]: continue
        hist_m = season < s
        for t in np.unique(ti[si == s]):
            h = np.sort(val[hist_m & (tier == t)]); m = (si == s) & (ti == t)
            if len(h) == 0: continue
            out[m] = 1 - np.searchsorted(h, thr[m], side="right") / len(h)
    return out


def main():
    rows, rel, params_out, d0 = [], [], [], []
    for stat, (kind, what) in STATS.items():
        f = frame(kind); deltas, edges = DELTAS[stat], TIERS[stat]
        if what == "yds": y, M, L = f.act_yds.values.astype(float), f.M.values.astype(float), f.L.values.astype(float)
        else: y, M, L = f.act_catch.values.astype(float), f.M_catch.values.astype(float), f.L_catch.values.astype(float)
        fit_m = f.season.between(*FIT).values; log(f"{stat}: {len(f)} rows, fit rows {int(fit_m.sum())}, mean L {L.mean():.1f}, mean M {M.mean():.1f}, mean actual {y.mean():.1f}")
        fams = (list(FAMILY) + list(TIERED)) if what == "yds" else ["normal_prop", "normal_tier", "lognorm", "gamma", "lognorm_L", "lognorm_L_tier", "poisson", "negbin"]
        params = {}
        for name in fams:
            if name in TIERED: params[name] = fit_tiered(TIERED[name], y[fit_m], M[fit_m], L[fit_m], deltas, edges)
            else: params[name] = fit_family(name, y[fit_m], M[fit_m], L[fit_m], deltas)
            params_out.append({"stat": stat, "dist": name, "params": ", ".join(f"{v:.4f}" for v in params[name]) if name not in TIERED else ", ".join(f"{edges[i]:.0f}+: {v:.4f}" if i == len(edges) - 2 else f"{edges[i]:.0f}-{edges[i + 1]:.0f}: {v:.4f}" for i, v in enumerate(params[name]))})
            log(f"  fit {name}: {params_out[-1]['params']}")
        x, o, idx, dl = grid(y, L, deltas); Mi = M[idx]; season_i = f.season.values[idx]
        P = {name: p_parametric(name, params[name], x, Mi, L[idx], edges) for name in fams}
        for e in ("ratio", "diff"): P[f"emp_{e}"] = p_empirical(e, f, y, L, x, idx, edges); log(f"  emp_{e} done")
        for e in ("ratio", "diff"): P[f"emp_knn_{e}"] = p_knn(e, f, y, L, x, idx, deltas); log(f"  emp_knn_{e} done")
        for name, p in P.items():
            for w, (a, b) in WIN.items():
                wm = (season_i >= a) & (season_i <= b) & ~np.isnan(p)
                for d in deltas:
                    m = wm & (dl == d)
                    if not m.sum(): continue
                    br, ll = scores(p[m], o[m]); rows.append({"stat": stat, "dist": name, "window": w, "delta": d, "n": int(m.sum()), "brier": round(br, 5), "logloss": round(ll, 5), "mean_p": round(float(p[m].mean()), 4), "over_rate": round(float(o[m].mean()), 4)})
                    if d == 0: d0.append({"stat": stat, "dist": name, "window": w, "n": int(m.sum()), "mean_p_over": round(float(p[m].mean()), 4), "mean_abs_from_half": round(float(np.abs(p[m] - 0.5).mean()), 4), "over_rate": round(float(o[m].mean()), 4)})
                bi = np.clip(np.digitize(p[wm], BINS[1:-1]), 0, len(BINS) - 2)
                for k in range(len(BINS) - 1):
                    m = bi == k
                    if m.sum(): rel.append({"stat": stat, "dist": name, "window": w, "bin_lo": BINS[k], "bin_hi": BINS[k + 1], "n": int(m.sum()), "mean_p": round(float(p[wm][m].mean()), 4), "over_rate": round(float(o[wm][m].mean()), 4), "gap": round(float(o[wm][m].mean() - p[wm][m].mean()), 4)})
            g = [r for r in rows if r["stat"] == stat and r["dist"] == name]
            log(f"  {name:12s} " + "  ".join(f"{w}: ll {np.mean([r['logloss'] for r in g if r['window'] == w]):.4f} d0 {next((r['logloss'] for r in g if r['window'] == w and r['delta'] == 0), np.nan):.4f}" for w in WIN))
    R = pd.DataFrame(rows); R.to_csv(OUT_CSV, index=False); RL = pd.DataFrame(rel); RL.to_csv(OUT_REL, index=False); D0 = pd.DataFrame(d0); PM = pd.DataFrame(params_out)
    # ---------- summary, the decision and the report ----------
    summ = R.groupby(["stat", "dist", "window"]).agg(n=("n", "sum"), logloss=("logloss", "mean"), brier=("brier", "mean")).reset_index()
    summ = summ.merge(R[R.delta == 0][["stat", "dist", "window", "logloss", "brier"]].rename(columns={"logloss": "logloss_d0", "brier": "brier_d0"}), on=["stat", "dist", "window"], how="left")
    def rel_ok(stat, dist, w):
        g = RL[(RL.stat == stat) & (RL.dist == dist) & (RL.window == w) & (RL.n >= REL_N)]; return bool((g.gap.abs() <= REL_TOL).all()), float(g.gap.abs().max()) if len(g) else np.nan
    md = ["# A calibrated chance for every yards prop line", "", "29 Sep 2026. experiments/props_chance.py. " + __doc__.split("\n\n")[0].split("Usage:")[0].strip().replace("\n", " "), "",
          "## Adoption rule (set before the run)", "", f"Per stat, the distribution with the lowest mean log loss over the delta grid on 2019-22 is adopted only if it is also the lowest on 2023-25 and its reliability (bins of the stated chance pooled over the deltas) is within {REL_TOL * 100:.0f} points of the stated chance in every bin with n >= {REL_N} on both windows. Where the best by log loss fails the reliability check, the best one that passes it on both windows is named instead and the report says so. Nothing here reads a book line: x is an offset from our own line L.", "",
          "## Frames", "", "The walk-forward by-season frame (experiments/props_by_season.build): every player-game with a touch of the kind, projected from the previous games only. L is the live rule's line (the median factor on the mean, the team reconciliation, the injury report and snap trend), M = L / the median factor, i.e. the mean scaled the same way, which is what the card's proj_*_yards_mean carries. The frame grades only games with a touch, so a chance read off it is for a player who gets on the stat sheet; the zero-touch games of a projected player (the active frame of round 17) are not in it, and a line for a player at risk of no touches is not covered.", ""]
    frames_note = []
    for stat, (kind, what) in STATS.items():
        ff = frame(kind); n_fit = int(ff.season.between(*FIT).sum()); frames_note.append(f"- {stat}: {len(ff)} player-games 2017-25, {n_fit} in the fit window 2017-18, {int(ff.season.between(2019, 2022).sum())} in 2019-22, {int(ff.season.between(2023, 2025).sum())} in 2023-25.")
    md += frames_note + ["", "## Fitted parameters (2017-18, chosen by the delta-grid log loss)", "", "Parametric tiers are tiers of M (the mean) with the empirical tiers' edges (tiers of L for the L-centred forms); the empirical tiers are tiers of L (the line). Forms: normal_prop s = c M; normal_lin s = a + b M; normal_pow s = a M^b; lognorm sigma; lognorm_pow sigma = a M^b; gamma shape k; gamma_pow k = a M^b; normal_L mean L, s = a + b L; lognorm_L median L, sigma (lognorm_L_pow: sigma = a L^b); negbin size r (variance M + M^2 / r). A parameter at a bound of its search box (normal_lin a = 500, normal_pow a = 200 or b = 0.05, lognorm_pow at 50 or -1.5, gamma_pow at 0.001 or 1.5) means the form found no fit.", "", PM.to_markdown(index=False), ""]
    verdicts = []
    for stat in STATS:
        s = summ[summ.stat == stat]; md += [f"## {stat}", "", "Mean log loss and Brier over the delta grid, and at delta 0 (x = L), by window:", ""]
        piv = s.pivot(index="dist", columns="window", values=["logloss", "logloss_d0", "brier"]); piv.columns = [f"{a}_{b}" for a, b in piv.columns]; piv = piv.round(5).sort_values("logloss_2019-22")
        md += [piv.to_markdown(), "", "At delta 0 (the line is the median, so a good distribution says about 0.5): the mean stated chance of the over, its mean distance from 0.5, the realised over rate:", "", D0[D0.stat == stat].drop(columns="stat").to_markdown(index=False), ""]
        best1 = piv.index[0]; best2 = s[s.window == "2023-25"].sort_values("logloss").dist.iloc[0]
        ok1 = rel_ok(stat, best1, "2019-22"); ok2 = rel_ok(stat, best1, "2023-25")
        same = best1 == best2 or fam(best1) == fam(best2)
        chosen, why = None, ""
        if same and ok1[0] and ok2[0]:
            chosen, why = best1, f"best by log loss on 2019-22 ({best1}) and on 2023-25 ({best2}{'' if best1 == best2 else ', the same family'}), reliability within {REL_TOL * 100:.0f} points in every bin with n >= {REL_N} on both windows (largest gap {ok1[1] * 100:.1f} / {ok2[1] * 100:.1f} points)"
        else:
            why = f"best by log loss on 2019-22 is {best1}, on 2023-25 {best2}; {best1} " + ("passes" if ok1[0] and ok2[0] else "fails") + f" the reliability check (largest gap {ok1[1] * 100:.1f} / {ok2[1] * 100:.1f} points)"
            for cand in piv.index:
                a, b = rel_ok(stat, cand, "2019-22"), rel_ok(stat, cand, "2023-25")
                if a[0] and b[0]: chosen = cand; why += f"; the best that passes the reliability check on both windows is {cand} (largest gap {a[1] * 100:.1f} / {b[1] * 100:.1f} points), adopted under the rule's second clause"; break
            if chosen is None: why += "; nothing passes the reliability check on both windows, so nothing is adopted"
        verdicts.append((stat, chosen, why))
        md += [f"**Verdict for {stat}:** {why}.", ""]
        for w in WIN:
            md += [f"Reliability on {w} (bins of the stated chance pooled over the deltas; gap = realised - stated, in points; flagged when |gap| > {REL_TOL * 100:.0f} with n >= {REL_N}):", ""]
            show = [d for d in ([chosen] if chosen else []) + [best1] if d] ; show = list(dict.fromkeys(show))
            for dist_ in show:
                g = RL[(RL.stat == stat) & (RL.dist == dist_) & (RL.window == w)].copy(); g["flag"] = np.where((g.n >= REL_N) & (g.gap.abs() > REL_TOL), "x", ""); g["gap"] = (100 * g.gap).round(1)
                md += [f"{dist_}:", "", g[["bin_lo", "bin_hi", "n", "mean_p", "over_rate", "gap", "flag"]].to_markdown(index=False), ""]
    md += ["## How to compute P(over x) in the live rule", "", "The card carries L = proj_<kind>_yards (the line) and M = proj_<kind>_yards_mean (the mean, scaled the same way). For a book number x:", ""]
    for stat, chosen, _ in verdicts:
        if chosen is None: md.append(f"- {stat}: nothing adopted."); continue
        prs = PM[(PM.stat == stat) & (PM.dist == chosen)].params; pr = prs.iloc[0] if len(prs) else ""; edges = TIERS[stat]
        if chosen == "normal_prop": md.append(f"- {stat}: normal_prop, c = {pr}. s = c x M; P(over x) = 1 - Phi((x - M) / s).")
        elif chosen == "normal_lin": md.append(f"- {stat}: normal_lin, (a, b) = ({pr}). s = a + b x M; P(over x) = 1 - Phi((x - M) / s).")
        elif chosen == "normal_pow": md.append(f"- {stat}: normal_pow, (a, b) = ({pr}). s = a x M^b; P(over x) = 1 - Phi((x - M) / s).")
        elif chosen == "normal_tier": md.append(f"- {stat}: normal_tier, c by tier of M ({pr}). s = c x M; P(over x) = 1 - Phi((x - M) / s).")
        elif chosen == "lognorm": md.append(f"- {stat}: lognorm, sigma = {pr}. mu = ln M - sigma^2 / 2; P(over x) = 1 - Phi((ln x - mu) / sigma) for x > 0, else 1.")
        elif chosen == "lognorm_tier": md.append(f"- {stat}: lognorm_tier, sigma by tier of M ({pr}). mu = ln M - sigma^2 / 2; P(over x) = 1 - Phi((ln x - mu) / sigma) for x > 0, else 1.")
        elif chosen == "lognorm_pow": md.append(f"- {stat}: lognorm_pow, (a, b) = ({pr}). sigma = a x M^b; mu = ln M - sigma^2 / 2; P(over x) = 1 - Phi((ln x - mu) / sigma) for x > 0, else 1.")
        elif chosen == "gamma": md.append(f"- {stat}: gamma, k = {pr}. P(over x) = Q(k, x k / M) (the regularised upper incomplete gamma, scipy.special.gammaincc(k, x * k / M); scipy.stats.gamma.sf(x, a=k, scale=M / k)) for x > 0, else 1.")
        elif chosen == "gamma_tier": md.append(f"- {stat}: gamma_tier, k by tier of M ({pr}). P(over x) = gammaincc(k, x k / M) for x > 0, else 1.")
        elif chosen == "gamma_pow": md.append(f"- {stat}: gamma_pow, (a, b) = ({pr}). k = a x M^b; P(over x) = gammaincc(k, x k / M) for x > 0, else 1.")
        elif chosen == "poisson": md.append(f"- {stat}: poisson, mean M = proj_catches_mean (the receptions line / MED_CATCH). P(over x) = 1 - PoissonCDF(floor(x); M).")
        elif chosen == "negbin": md.append(f"- {stat}: negbin, size r = {pr}, mean M = proj_catches_mean. p = r / (r + M); P(over x) = 1 - NegBinCDF(floor(x); r, p) (scipy.stats.nbinom.sf(floor(x), r, p)).")
        elif chosen == "normal_L": md.append(f"- {stat}: normal_L, (a, b) = ({pr}). s = a + b x L; P(over x) = 1 - Phi((x - L) / s) (centred on the line, so 0.5 at x = L).")
        elif chosen == "lognorm_L": md.append(f"- {stat}: lognorm_L, sigma = {pr}. P(over x) = 1 - Phi(ln(x / L) / sigma) for x > 0, else 1 (median L, so 0.5 at x = L).")
        elif chosen == "lognorm_L_tier": md.append(f"- {stat}: lognorm_L_tier, sigma by tier of L ({pr}). P(over x) = 1 - Phi(ln(x / L) / sigma) for x > 0, else 1.")
        elif chosen == "lognorm_L_pow": md.append(f"- {stat}: lognorm_L_pow, (a, b) = ({pr}). sigma = a x L^b; P(over x) = 1 - Phi(ln(x / L) / sigma) for x > 0, else 1.")
        elif chosen.startswith("emp_knn"):
            what = "actual / L" if chosen.endswith("ratio") else "actual - L"
            md.append(f"- {stat}: {chosen}: keep a reference table of (L, actual) for every row of the by-season frame from 2017 to the last completed season (rebuilt each run, as the game model keeps its training misses in model.price_at). For a line L, take the K rows nearest to it in L (K = {KNN_FRAC:.0%} of the table, at least {KNN_MIN}, at most {KNN_MAX}: sort the table by L, find L's position, take K/2 rows on each side, shifted in from the ends), and P(over x) = the share of those rows with {what} > {'x / L' if chosen.endswith('ratio') else 'x - L'}.")
        elif chosen.startswith("emp_"):
            what = "actual / L" if chosen == "emp_ratio" else "actual - L"
            md.append(f"- {stat}: {chosen}: the empirical distribution of {what} over the frame's rows (2017 to the last completed season) in the tier of L (edges {edges[:-1]}); P(over x) = share of those rows with {what} > {'x / L' if chosen == 'emp_ratio' else 'x - L'}. The reference set is rebuilt each run from the by-season frame (a table per stat x tier: the sorted values), as the game model keeps its training misses (model.price_at).")
    md += ["", "## Reading of the results (29 Sep 2026, written after the run; the tables above are the evidence)", "",
           "- The mean M is not the mean of what happened for passing: on 2017-25 M averages 266 yards against 233 actual (the linear median factor MED_TIER['pass'], 0.63 + 0.00091 x M, absorbs a bias there, since passing yards are nearly symmetric and a true median factor would sit near 0.95). Every M-centred form (normal, log-normal, gamma with mean M) is therefore off for passing, and the M-centred forms say 0.43 to 0.60 at x = L for every stat; only the L-centred forms (0.5 by construction) and the empirical ones (the fit window's own over rate, 0.50 to 0.53) sit where a median line should. Receiving and rushing M do match the actual mean (31.8 / 31.7 and 31.1 / 30.9).",
           "- The first pass (tiers of L, and every parametric form) failed the reliability check in the tail bins, and the failures were all rows with a small line and a large positive delta (L of 2 to 6, x of 12 to 21: numbers no book hangs). Within the 0-20 tier the shape of actual / L changes fast with L (the median of actual / L is 2.1 below L = 5, 1.1 at 10 to 20: the median factor undershoots at tiny means), so the fixed tier pools rows that do not belong together. The nearest-neighbour empirical (emp_knn, K earlier rows nearest in L) fixes that and is the best by log loss on both windows for receiving yards and receptions, and passes the reliability check on both.",
           "- Rushing: emp_knn_diff is the best by log loss on both windows and within 1.5 points in every bin but one: the 0-0.1 bin on 2019-22 (239 rows, stated 9.4%, realised 13.4%, a 4.0-point gap; on 2023-25 every bin is within 0.7). Under the rule as set it is not adopted; the miss is one thin tail bin, and adopting it anyway is a call for the reader, not this study.",
           "- Passing: the fixed-tier empirical (emp_ratio / emp_diff, the same family) is the best by log loss on both windows but emp_ratio misses the reliability bar by a tenth of a point in one bin on 2023-25 (3.1); emp_knn_diff is the best that passes on both windows and is adopted under the rule's second clause. Its gaps on 2023-25 run 2 to 3 points negative across the bins: the passing line ran high in 2023-25 (over rate 0.484 at x = L), which no distribution around the line can know.",
           "- Receptions: emp_knn_ratio beats the count models (negbin, poisson) on both windows and is within 2 points in every bin. The Poisson and negative binomial around the receptions mean M (the line / MED_CATCH) say 0.50 to 0.52 at x = L while 0.56 to 0.57 of the games went over: the receptions line sits low.",
           "- On integration: emp_knn needs a reference table per stat, (L, actual) for every row of the by-season frame from 2017 to the last completed season (the cached frames this script writes carry it: season, L, act_yds / act_catch), rebuilt when props_by_season is rerun; at 36k receiving rows K is the cap of 1500. The frame grades only games with a touch, so the chance is conditional on the player getting on the stat sheet.", "",
           "Pushes: a book number the actual can land on (a whole number) is a push; the scoring here left ties out. In the grading, the side is the one with the higher chance (over when P(over x) > 0.5, which is the same side as edge = L - x > 0 for a median-consistent distribution), and the chance is the number to rank props by, as the page ranks game bets.", ""]
    pathlib.Path(OUT_MD).write_text("\n".join(md))
    print("\n" + summ.sort_values(["stat", "window", "logloss"]).to_string()); print("\nverdicts:")
    for stat, chosen, why in verdicts: print(f"  {stat}: {chosen} -- {why}")
    print("DONE")


if __name__ == "__main__":
    main()
