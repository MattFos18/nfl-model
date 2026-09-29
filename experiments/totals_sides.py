"""Overs against unders (29 Sep 2026, Matt: "the unders are really good and the overs are garbage").

Three parts, every number walk-forward (a game is priced only with games played before its week):
  Part 1  diagnosis on 2015-2025 from data/processed/pred_v3.parquet (the live walk-forward totals): the record and
          ROI of leaning over and under at every edge and every chance band, by window; the signed bias of the model
          total (model minus actual) by projected total, line, roof, wind and cold, primetime, division, week of the
          season, rest, the two teams' pace and ratings, the referee and the sign of the model's edge; the reliability
          of p_over_emp by band, over-leans and under-leans apart.
  Part 2  fixes to the total equation and to the chance, each a weekly-refit walk-forward of the total equation
          (a) shrink the total's deviation from the training mean by s, s fitted on 2019-22 (and s refit every week
              from the earlier walk-forward misses); (b) shrink only the upside (above the mean, and above a knee);
          (c) the chance: symmetric residuals, a two-piece curve from the upper and lower halves, and residual pools
              from earlier out-of-sample games (all of them, and only games projected on the same side of the mean);
          (d) scoring drift in forms scoring_env.py did not try: a league-level offset with a fixed coefficient (the
              equation fits total minus the league's recent mean total and adds it back) and a correction by the
              equation's own recent out-of-sample miss (recency weights were tried in sweep_totals.csv and are not
              repeated); (e) wind x both teams' pass rate, and warm or dome teams in the cold; (f) the total as the
              sum of the two team-points equations (the ridge alone, and the live seven-model blend from pred_v3)
          The total equation does not touch the points blend or the trees, so the walk-forward here refits only the
          total equation (M.total_model's exact fit: ridge alpha 10 on M.TOTAL_FEATS, training from 2013, weekly);
          the base run reproduces pred_v3's model_total and p_over_emp to 1e-13 (checked at the start of every run).
          M.walk_forward is not called, and M.TREES_CACHE is pointed at a scratch path in case anything does.
  Part 3  rules on pred_v3: over rules (chance 55/58/60/65%, edge 2-6, filtered by roof, total, primetime,
          division) and the under rule's cutoff, per window, units at -110 and a bootstrap chance that ROI > 0.

Bets: regular season, weeks 1 to 17 (picks.LAST_BET_WEEK), a closing total, pushes dropped from the record.
Windows: 2015-18 (never tuned on), 2019-22 (tuned on), 2023-25 (held out). Lines are used only to grade and to read
the chance at the line; nothing from the market enters any equation.
Writes reports/totals_sides.csv and reports/totals_sides.md.    python -m experiments.totals_sides
"""
import sys, os, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import numpy as np, pandas as pd
from scipy.stats import norm
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from nflmodel import model as M
from nflmodel.model import OUT

T0 = time.time()
REP = Path(__file__).resolve().parent.parent / "reports"
SCRATCH = Path(os.environ.get("TOTALS_SIDES_SCRATCH", "/tmp/totals_sides")); SCRATCH.mkdir(parents=True, exist_ok=True)
M.TREES_CACHE = SCRATCH / "trees_cache.parquet"; M._TC = {"df": None, "used": set(), "new": []}   # nothing under data/processed is written
W = {"2015-18": (2015, 2018), "2019-22": (2019, 2022), "2023-25": (2023, 2025)}
ALLW = {**W, "2015-25": (2015, 2025)}
VIG, LAST_WEEK, UNDER_CUT = 1.1, 17, 0.55
PR_C = 1.22          # centre of the two teams' pass rate sum (league pass rate about 0.61 a team)
RNG = np.random.default_rng(20260929)
NBOOT = 10000
CSV_ROWS: list = []


def log(*a):
    print(f"[{time.time() - T0:6.1f}s]", *a, flush=True)


def keep(section: str, df: pd.DataFrame):
    CSV_ROWS.append(df.assign(section=section))
    return df


# ----------------------------------------------------------------------------------------------------------- data
def build():
    f = M.prep(M.with_trends(pd.read_parquet(OUT / "features_asof.parquet")))
    tg = pd.read_parquet(OUT / "team_games.parquet", columns=["game_id", "season", "week", "team", "pass_rate"]).sort_values(["team", "season", "week"])
    # each team's pass rate as of the game: exponentially weighted over its previous games (0.9 a game), never its own
    tg["pr_asof"] = tg.groupby("team").pass_rate.transform(lambda s: s.shift(1).ewm(alpha=0.1, ignore_na=True).mean())
    f = f.merge(tg[["game_id", "team", "pr_asof"]], on=["game_id", "team"], how="left"); f["pr_asof"] = f.pr_asof.fillna(PR_C / 2)
    G = M._game_frame(f)
    h = f[f.home == 1].set_index("game_id").loc[G.index]; a = f[f.home == 0].set_index("game_id").loc[G.index]
    for c in ("season", "week", "game_type", "total_line"):
        G[c] = h[c].values
    G["pace_sum"] = (h.off_plays + a.off_plays).values
    G["off_h"], G["off_a"], G["def_h"], G["def_a"] = h.off_epa_play.values, a.off_epa_play.values, h.def_epa_play.values, a.def_epa_play.values
    G["wic_sum"] = (h.warm_in_cold + a.warm_in_cold).values
    G["pr_sum"] = (h.pr_asof + a.pr_asof).values
    G["wind_pass"] = G.wind_out * (G.pr_sum - PR_C)
    gm = pd.read_parquet(OUT / "games.parquet").set_index("game_id")
    for c in ("roof", "temp", "wind", "primetime", "div_game", "home_rest", "away_rest", "referee", "home_score", "away_score"):
        G["g_" + c] = gm[c].reindex(G.index).values
    # the league's mean game total over the last N played games before each (season, week) slot (games.parquet from 2012)
    pg = gm[gm.home_score.notna() & (gm.season >= 2011)].sort_values(["season", "week"])
    tot = (pg.home_score + pg.away_score).values; sw = list(zip(pg.season, pg.week)); cs = np.concatenate([[0], np.cumsum(tot)])
    slots = sorted(set(zip(G.season, G.week))); import bisect
    for N in (128, 256, 512):
        lv = {}
        for s, w in slots:
            k = bisect.bisect_left(sw, (s, w)); lo = max(0, k - N); lv[(s, w)] = (cs[k] - cs[lo]) / max(1, k - lo)
        G[f"lvl{N}"] = [lv[(s, w)] for s, w in zip(G.season, G.week)]
    return f, G


# ----------------------------------------------------------------------------------------------------------- chances
def p_emp(mt, L, res):
    """Over chance read off a residual pool shifted to each game's total, pushes left out (model.price_at)."""
    mt = np.asarray(mt, float); L = np.asarray(L, float); res = np.asarray(res, float)
    v = mt[:, None] + res[None, :]
    over = (v > L[:, None]).mean(1); nonpush = (v != L[:, None]).mean(1)
    out = over / np.maximum(1e-9, nonpush); out[np.isnan(L)] = np.nan
    return out


def p_twopiece(mt, L, res):
    """A two-piece normal: centred on the median miss, the upper half's spread above it and the lower half's below."""
    med = np.median(res); up = res[res > med] - med; dn = med - res[res < med]
    su, sd = np.sqrt(np.mean(up ** 2)), np.sqrt(np.mean(dn ** 2))
    c = np.asarray(mt, float) + med; L = np.asarray(L, float)
    return np.where(L >= c, 1 - norm.cdf((L - c) / su), norm.cdf((c - L) / sd))


def fit_ridge(X, y, w=None):
    m = make_pipeline(StandardScaler(), Ridge(alpha=10.0))
    m.fit(X, y, **({"ridge__sample_weight": w} if w is not None else {}))
    return m


def run(G, feats=None, post=None, offset=None, offset_c=1.0, seasons=range(2014, 2026), chances=True, keep_tres=False):
    """The total equation walk-forward, refit before every week on every played game since 2013. post(pred, mu, s, w)
    reshapes the prediction (applied to the training games too, so the residual pool matches); offset: a column the
    equation's target is measured from (coefficient offset_c, fixed), added back to the prediction."""
    feats = list(feats or M.TOTAL_FEATS); played = G[G.total.notna()]; out = []; tres_d = {}
    for s in seasons:
        for w in sorted(G[G.season == s].week.unique()):
            tr = played[(played.season >= M.TRAIN_FROM) & ((played.season < s) | ((played.season == s) & (played.week < w)))]
            te = G[(G.season == s) & (G.week == w)]
            y = tr.total.values
            otr = offset_c * tr[offset].values if offset else 0.0; ote = offset_c * te[offset].values if offset else 0.0
            m = fit_ridge(tr[feats].values, y - otr)
            ptr = m.predict(tr[feats].values) + otr; pte = m.predict(te[feats].values) + ote; raw = pte.copy(); mu = float(y.mean())
            if post is not None:
                ptr, pte = post(ptr, mu, s, w), post(pte, mu, s, w)
            tres = y - ptr
            o = pd.DataFrame({"mt": pte, "raw": raw, "mu_tr": mu, "season": s, "week": w}, index=te.index)
            if chances:
                L = te.total_line.values
                o["p_emp"] = p_emp(pte, L, tres)
                o["p_sym"] = p_emp(pte, L, np.concatenate([tres - tres.mean(), tres.mean() - tres]))
                o["p_2p"] = p_twopiece(pte, L, tres)
                o["p_norm"] = 1 - norm.cdf((L - pte) / np.std(tres))
            if keep_tres:
                tres_d[(s, w)] = tres
            out.append(o)
    P = pd.concat(out)
    return (P, tres_d) if keep_tres else P


def oos_pools(P, G, seasons=range(2015, 2026)):
    """Chances from earlier out-of-sample misses (actual minus the walk-forward total, 2014 on): the whole pool, and
    only the games projected on the same side of their training mean as this one."""
    x = P.join(G[["total"]]); x = x[x.total.notna()].copy(); x["res"] = x.total - x.mt; x["hi"] = x.mt > x.mu_tr
    x = x.sort_values(["season", "week"])
    pa, ph = pd.Series(np.nan, index=P.index), pd.Series(np.nan, index=P.index)
    for s in seasons:
        for w in sorted(P[P.season == s].week.unique()):
            prev = x[(x.season < s) | ((x.season == s) & (x.week < w))]
            te = P[(P.season == s) & (P.week == w)]; L = G.total_line.reindex(te.index).values
            pa.loc[te.index] = p_emp(te.mt.values, L, prev.res.values)
            hi = (te.mt > te.mu_tr).values; r = np.empty(len(te))
            for flag in (True, False):
                k = hi == flag
                if k.any():
                    r[k] = p_emp(te.mt.values[k], L[k], prev.res.values[prev.hi.values == flag])
            ph.loc[te.index] = r
    return pa, ph


# ----------------------------------------------------------------------------------------------------------- grading
def rec(x, side):
    """w, l, push, units, roi for betting `side` (+1 over, -1 under) on every row of x."""
    d = (x.total - x.total_line).values * side
    w, l, p = int((d > 0).sum()), int((d < 0).sum()), int((d == 0).sum())
    u = w - VIG * l
    return w, l, p, u, (u / (VIG * (w + l)) if w + l else np.nan)


def bets_frame(D):
    return D[(D.game_type == "REG") & (D.week <= LAST_WEEK) & D.total_line.notna() & D.total.notna()]


def fmt(w, l):
    return f"{w}-{l}"


def score_variant(P, G, mt="mt", p="p_emp"):
    """Per window: total MAE and bias (regular season), the 55% under rule, over at 55%+, over at 3+ edge, log loss."""
    D = P[[mt] + ([p] if p else [])].rename(columns={mt: "mt_", **({p: "p_"} if p else {})}).join(G[["season", "week", "game_type", "total", "total_line"]])
    out = {}
    for wn, (a, b) in W.items():
        r = D[(D.game_type == "REG") & D.season.between(a, b) & D.total.notna()]
        out[f"mae_{wn}"] = round(float((r.mt_ - r.total).abs().mean()), 4); out[f"bias_{wn}"] = round(float((r.mt_ - r.total).mean()), 3)
        bx = bets_frame(r)
        if p:
            for lab, m, side in (("under55", (1 - bx.p_) >= UNDER_CUT, -1), ("over55", bx.p_ >= UNDER_CUT, 1)):
                w_, l_, _, u, roi = rec(bx[m], side)
                out[f"{lab}_{wn}"] = fmt(w_, l_); out[f"{lab}_pct_{wn}"] = round(w_ / (w_ + l_), 4) if w_ + l_ else np.nan; out[f"{lab}_u_{wn}"] = round(u, 1)
            nb = bx[bx.total != bx.total_line]; q = nb.p_.clip(0.02, 0.98); yv = (nb.total > nb.total_line).astype(float)
            out[f"logloss_{wn}"] = round(float(-(yv * np.log(q) + (1 - yv) * np.log(1 - q)).mean()), 5)
        e = bx.mt_ - bx.total_line
        w_, l_, _, u, _ = rec(bx[e >= 3], 1); out[f"over3_{wn}"] = fmt(w_, l_); out[f"over3_u_{wn}"] = round(u, 1)
        w_, l_, _, u, _ = rec(bx[e <= -3], -1); out[f"under3_{wn}"] = fmt(w_, l_); out[f"under3_u_{wn}"] = round(u, 1)
    return out


# ----------------------------------------------------------------------------------------------------------- part 1
def part1(G):
    pv = pd.read_parquet(OUT / "pred_v3.parquet").set_index("game_id")
    D = pv[["model_total", "p_over_emp", "p_over", "sigma_total", "home_pts_eq", "away_pts_eq"]].join(G, how="inner")
    D = D[(D.game_type == "REG") & D.season.between(2015, 2025) & D.total.notna() & D.total_line.notna()].copy()
    D["edge"] = D.model_total - D.total_line; D["lean"] = np.where(D.edge > 0, "over", "under")
    D["win"] = pd.cut(D.season, [2014, 2018, 2022, 2025], labels=list(W)).astype(str)
    Bx = bets_frame(D).copy()
    T = {}
    # 1a. leaning each side by edge band, by window
    rows = []
    bands = [(0, 2, "0-2"), (2, 3, "2-3"), (3, 4, "3-4"), (4, 5, "4-5"), (5, 6, "5-6"), (6, 99, "6+"), (2, 99, "2+ (all)"), (3, 99, "3+ (all)"), (4, 99, "4+ (all)"), (5, 99, "5+ (all)")]
    for side, sg in (("over", 1), ("under", -1)):
        for lo, hi, lab in bands:
            r = {"lean": side, "edge": lab}
            for wn, (a, b) in ALLW.items():
                x = Bx[Bx.season.between(a, b)]; e = x.edge * sg; x = x[(e >= lo) & (e < hi)]
                w_, l_, p_, u, roi = rec(x, sg)
                r[wn] = f"{w_}-{l_} ({roi:+.1%})" if w_ + l_ else "0-0"
                if wn == "2015-25":
                    r["units"] = round(u, 1); r["mean_edge"] = round(float((x.edge * sg).mean()), 2) if len(x) else np.nan
                    r["mean_realized"] = round(float(((x.total - x.total_line) * sg).mean()), 2) if len(x) else np.nan
                    r["median_realized"] = round(float(((x.total - x.total_line) * sg).median()), 2) if len(x) else np.nan
            rows.append(r)
    T["edge"] = keep("p1_edge_bands", pd.DataFrame(rows))
    # 1b. by the chance of the side the chance favours
    rows = []
    D["pside"] = np.where(D.p_over_emp >= 0.5, D.p_over_emp, 1 - D.p_over_emp); D["cside"] = np.where(D.p_over_emp >= 0.5, "over", "under")
    Bx = bets_frame(D).copy()
    for side, sg in (("over", 1), ("under", -1)):
        for lo, hi, lab in ((0.50, 0.55, "50-55"), (0.55, 0.60, "55-60"), (0.60, 0.65, "60-65"), (0.65, 1.01, "65+"), (0.55, 1.01, "55+ (all)")):
            r = {"lean": side, "chance": lab}
            for wn, (a, b) in ALLW.items():
                x = Bx[Bx.season.between(a, b) & (Bx.cside == side) & (Bx.pside >= lo) & (Bx.pside < hi)]
                w_, l_, p_, u, roi = rec(x, sg)
                r[wn] = f"{w_}-{l_} ({roi:+.1%})" if w_ + l_ else "0-0"
                if wn == "2015-25":
                    r["units"] = round(u, 1); r["stated"] = round(float(x.pside.mean()), 3); r["won"] = round(w_ / (w_ + l_), 3) if w_ + l_ else np.nan
            rows.append(r)
    T["chance"] = keep("p1_chance_bands", pd.DataFrame(rows))
    # 1c. reliability by window, over-leans and under-leans apart (the chance's own side)
    rows = []
    for side in ("over", "under"):
        for lo, hi, lab in ((0.50, 0.55, "50-55"), (0.55, 0.60, "55-60"), (0.60, 0.65, "60-65"), (0.65, 1.01, "65+")):
            r = {"lean": side, "band": lab}
            for wn, (a, b) in ALLW.items():
                x = Bx[Bx.season.between(a, b) & (Bx.cside == side) & (Bx.pside >= lo) & (Bx.pside < hi) & (Bx.total != Bx.total_line)]
                won = ((x.total > x.total_line) if side == "over" else (x.total < x.total_line)).mean()
                r[wn] = f"{x.pside.mean():.1%} said, {won:.1%} won (n {len(x)})" if len(x) else ""
                if wn == "2015-25":
                    r["gap_pts"] = round(100 * (won - x.pside.mean()), 1)
            rows.append(r)
    T["rel"] = keep("p1_reliability", pd.DataFrame(rows))
    # 1d. signed bias (model total minus actual) by situation
    D["tier_model"] = pd.cut(D.model_total, [0, 40, 43, 46, 49, 52, 99], labels=["<40", "40-43", "43-46", "46-49", "49-52", "52+"], right=False)
    D["tier_line"] = pd.cut(D.total_line, [0, 40, 43, 46, 49, 52, 99], labels=["<40", "40-43", "43-46", "46-49", "49-52", "52+"], right=False)
    D["roof2"] = np.where(D.dome == 1, "indoors (dome or closed)", np.where(D.g_roof == "open", "retractable, open", "outdoors"))
    out_ = D.dome == 0
    D["windb"] = np.where(~out_, "indoors", pd.cut(D.g_wind.fillna(D.g_wind.median()), [-1, 10, 15, 99], labels=["outdoors, wind <10", "outdoors, wind 10-14", "outdoors, wind 15+"], right=False).astype(str))
    D["coldb"] = np.where(~out_, "indoors", np.where(D.cold == 1, "outdoors, under 35F", "outdoors, 35F+"))
    D["wicb"] = np.where(D.wic_sum > 0, "a warm or dome team in the cold", "no")
    D["prime"] = np.where(D.g_primetime.astype(bool), "primetime", "day")
    D["div"] = np.where(D.g_div_game.astype(float) == 1, "division", "non-division")
    D["wkb"] = pd.cut(D.week, [0, 4, 13, 18], labels=["1-4", "5-13", "14-18"])
    mnr = np.minimum(D.g_home_rest, D.g_away_rest); mxr = np.maximum(D.g_home_rest, D.g_away_rest)
    D["restb"] = np.where(mnr <= 5, "short week (Thursday)", np.where(mxr >= 10, "a team off a bye", "normal"))
    D["paceb"] = pd.qcut(D.pace_sum, 3, labels=["slow third", "middle third", "fast third"])
    med = pd.concat([D.off_h, D.off_a]).median()
    D["offb"] = np.where((D.off_h > med) & (D.off_a > med), "both offenses above median", np.where((D.off_h <= med) & (D.off_a <= med), "both below median", "one of each"))
    dmed = pd.concat([D.def_h, D.def_a]).median()   # def_epa_play: EPA allowed, low is good
    D["defb"] = np.where((D.def_h < dmed) & (D.def_a < dmed), "both defenses good", np.where((D.def_h >= dmed) & (D.def_a >= dmed), "both defenses bad", "one of each"))
    D["refb"] = pd.qcut(D.ref_tot.rank(method="first"), 3, labels=["referee low-scoring third", "middle third", "high-scoring third"])
    D["signb"] = np.where(D.edge > 0, "model over the line", "model under the line")
    D["sign_edge"] = pd.cut(D.edge, [-99, -6, -4, -2, 0, 2, 4, 6, 99], labels=["under 6+", "under 4-6", "under 2-4", "under 0-2", "over 0-2", "over 2-4", "over 4-6", "over 6+"], right=False)
    dims = [("projected total", "tier_model"), ("line", "tier_line"), ("roof", "roof2"), ("wind", "windb"), ("cold", "coldb"), ("warm/dome team in cold", "wicb"),
            ("primetime", "prime"), ("division", "div"), ("week", "wkb"), ("rest", "restb"), ("pace (both offenses' plays)", "paceb"), ("offenses", "offb"),
            ("defenses", "defb"), ("referee (ref_tot)", "refb"), ("sign of the edge", "signb"), ("signed edge", "sign_edge")]
    rows = []
    for name, col in dims:
        for k, x in D.groupby(col, observed=True):
            r = {"dim": name, "group": str(k), "games": len(x), "model_bias": round(float((x.model_total - x.total).mean()), 2),
                 "line_bias": round(float((x.total_line - x.total).mean()), 2), "model_minus_line": round(float(x.edge.mean()), 2)}
            for wn, (a, b) in W.items():
                xx = x[x.season.between(a, b)]; r[f"bias {wn}"] = round(float((xx.model_total - xx.total).mean()), 2) if len(xx) else np.nan
            nb = x[x.total != x.total_line]; r["over_hit"] = round(float((nb.total > nb.total_line).mean()), 3)
            bx = bets_frame(x); ov = bx[bx.edge >= 3]; un = bx[(1 - bx.p_over_emp) >= UNDER_CUT]
            w_, l_, _, u, _ = rec(ov, 1); r["over 3+"] = f"{w_}-{l_}"; w_, l_, _, u, _ = rec(un, -1); r["under 55%"] = f"{w_}-{l_}"
            rows.append(r)
    T["bias"] = keep("p1_bias", pd.DataFrame(rows))
    # 1e. how much of the edge comes true, by side and window: slope of (actual - line) on (model - line)
    rows = []
    for side, sg in (("over", 1), ("under", -1)):
        for wn, (a, b) in ALLW.items():
            x = D[D.season.between(a, b) & (np.sign(D.edge) == sg)]
            e = x.edge.values; rz = (x.total - x.total_line).values
            slope = float(np.polyfit(e, rz, 1)[0]); ne = x[x.total != x.total_line]
            rows.append({"lean": side, "window": wn, "games": len(x), "mean_edge": round(float(e.mean()), 2), "mean_actual_minus_line": round(float(rz.mean()), 2),
                         "median_actual_minus_line": round(float(np.median(rz)), 2), "share_of_edge_realized": round(float(rz.mean() / e.mean()), 2),
                         "slope": round(slope, 2), "side_won": round(float(((ne.total - ne.total_line) * sg > 0).mean()), 3),
                         "model_bias": round(float((x.model_total - x.total).mean()), 2), "line_bias": round(float((x.total_line - x.total).mean()), 2)})
    T["realize"] = keep("p1_realized", pd.DataFrame(rows))
    # 1f. the referee: is a referee's miss a trait? variance of per-referee mean misses against chance, and odd vs even seasons
    D["res"] = D.total - D.model_total
    rg = D.groupby("g_referee").res.agg(["mean", "count", "std"]); rg = rg[rg["count"] >= 40]
    obs_var = float(rg["mean"].var()); exp_var = float((D.res.var() / rg["count"]).mean())
    odd = D[D.season % 2 == 1].groupby("g_referee").res.agg(["mean", "count"]); even = D[D.season % 2 == 0].groupby("g_referee").res.agg(["mean", "count"])
    j = odd.join(even, lsuffix="_odd", rsuffix="_even").dropna(); j = j[(j.count_odd >= 20) & (j.count_even >= 20)]
    T["ref"] = {"refs": len(rg), "obs_var": round(obs_var, 3), "exp_var": round(exp_var, 3), "ratio": round(obs_var / exp_var, 2), "split_corr": round(float(j.mean_odd.corr(j.mean_even)), 3), "split_n": len(j),
                "sd_between_refs": round(float(np.sqrt(max(0.0, obs_var - exp_var))), 2)}
    keep("p1_referee", pd.DataFrame([T["ref"]]))
    # 1g. skew: the typical game against the average
    rz = D.total - D.total_line
    T["skew"] = {"mean": round(float(rz.mean()), 2), "median": round(float(rz.median()), 2), "under_share": round(float((rz[rz != 0] < 0).mean()), 3),
                 "mean_model_minus_actual": round(float((D.model_total - D.total).mean()), 2), "median_model_minus_actual": round(float((D.model_total - D.total).median()), 2)}
    keep("p1_skew", pd.DataFrame([T["skew"]]))
    return D, T


# ----------------------------------------------------------------------------------------------------------- part 3
FILTERS = {"all": lambda x: x.total_line.notna(), "indoors": lambda x: x.dome == 1, "outdoors": lambda x: x.dome == 0,
           "line 47+": lambda x: x.total_line >= 47, "line under 43": lambda x: x.total_line < 43, "primetime": lambda x: x.g_primetime.astype(bool),
           "day games": lambda x: ~x.g_primetime.astype(bool), "division": lambda x: x.g_div_game.astype(float) == 1, "weeks 1-8": lambda x: x.week <= 8, "weeks 9-17": lambda x: x.week >= 9}


def rules(D, pcol="p_over_emp", src="p_over_emp (live)"):
    Bx = bets_frame(D); rows = []
    over_r = [(f"over, chance {round(100 * c)}%+", (lambda c: lambda x: x[pcol] >= c)(c)) for c in (0.55, 0.58, 0.60, 0.65)] + \
             [(f"over, edge {e}+", (lambda e: lambda x: x.edge >= e)(e)) for e in (2, 3, 4, 5, 6)] + \
             [("over, edge 3+ and chance 55%+", lambda x: (x.edge >= 3) & (x[pcol] >= 0.55))]
    under_r = [(f"under, chance {round(100 * c)}%+", (lambda c: lambda x: (1 - x[pcol]) >= c)(c)) for c in (0.52, 0.53, 0.54, 0.55, 0.56, 0.57, 0.58, 0.60, 0.62, 0.65)] + \
              [(f"under, edge {e:g}+", (lambda e: lambda x: x.edge <= -e)(e)) for e in (2, 2.5, 3, 3.5, 4, 5, 6)]
    for side, sg, rl in (("over", 1, over_r), ("under", -1, under_r)):
        for rname, rm in rl:
            for fname, fm in FILTERS.items():
                if side == "under" and fname != "all" and not rname.startswith("under, chance 55"):
                    continue   # the under cutoffs are swept on every game; filters only on the live 55% rule
                r = {"source": src, "side": side, "rule": rname, "filter": fname}; mins = []; ok = True
                for wn, (a, b) in ALLW.items():
                    x = Bx[Bx.season.between(a, b)]; x = x[rm(x) & fm(x)]
                    w_, l_, p_, u, roi = rec(x, sg)
                    r[f"rec {wn}"] = f"{w_}-{l_}"; r[f"units {wn}"] = round(u, 1); r[f"roi {wn}"] = round(roi, 3) if w_ + l_ else np.nan
                    if wn != "2015-25":
                        mins.append(roi if w_ + l_ >= 15 else -9); ok &= (w_ + l_ >= 15) and roi > 0
                r["wins all three"] = ok; r["worst window roi"] = round(min(mins), 3)
                rows.append(r)
    return pd.DataFrame(rows)


def boot(D, side, rm, fm, pcol="p_over_emp"):
    Bx = bets_frame(D); out = {}
    for wn, (a, b) in ALLW.items():
        x = Bx[Bx.season.between(a, b)]; x = x[rm(x) & fm(x)]
        d = (x.total - x.total_line).values * (1 if side == "over" else -1); d = d[d != 0]
        u = np.where(d > 0, 1.0, -VIG)
        if not len(u):
            out[wn] = np.nan; continue
        idx = RNG.integers(0, len(u), size=(NBOOT, len(u)))
        out[wn] = round(float((u[idx].mean(1) > 0).mean()), 3)
    return out


# ----------------------------------------------------------------------------------------------------------- main
def md_table(df, cols=None, floatfmt=None):
    df = df[cols] if cols else df
    return df.to_markdown(index=False)


def main():
    rt = {}
    f, G = build(); log("features and game frame", G.shape)
    # --- base walk-forward (the live total equation) and the reproduction check against pred_v3
    t = time.time(); P0, TRES = run(G, keep_tres=True); rt["base walk-forward (2014-2025, weekly)"] = time.time() - t
    pv = pd.read_parquet(OUT / "pred_v3.parquet").set_index("game_id")
    j = P0[P0.season >= 2015].join(pv[["model_total", "p_over_emp"]], how="inner")
    dmt, dpe = float((j.mt - j.model_total).abs().max()), float((j.p_emp - j.p_over_emp).abs().max())
    log(f"reproduction vs pred_v3: model_total max diff {dmt:.2e}, p_over_emp max diff {dpe:.2e}, {len(j)} games")
    assert dmt < 1e-6 and dpe < 1e-9, "the walk-forward here does not reproduce pred_v3"
    # --- Part 1
    t = time.time(); D, T1 = part1(G); rt["part 1"] = time.time() - t; log("part 1 done")
    # --- Part 2
    t = time.time(); V = []   # (family, name, P, mt col, p col)
    pa, ph = oos_pools(P0, G); P0["p_oos"], P0["p_oos_half"] = pa, ph; log("oos pools done")
    V.append(("base", "live total equation, p_over_emp", P0, "mt", "p_emp"))
    # (a) shrink toward the training mean
    for s_ in np.round(np.arange(0.70, 1.001, 0.05), 2):
        if s_ == 1.0:
            continue
        P = run(G, post=(lambda s_: lambda p, mu, s, w: mu + s_ * (p - mu))(s_), seasons=range(2015, 2026))
        V.append(("a shrink", f"s {s_:.2f}", P, "mt", "p_emp"))
    log("(a) grid done")
    # (a-wf) s refit before every week: through-origin slope of (actual - mean) on (projection - mean) over earlier out-of-sample games since 2014
    x = P0.join(G[["total"]]); x = x[x.total.notna()].sort_values(["season", "week"]); sdict = {}
    for s in range(2015, 2026):
        for w in sorted(P0[P0.season == s].week.unique()):
            pr = x[(x.season < s) | ((x.season == s) & (x.week < w))]; dv = pr.mt - pr.mu_tr
            sdict[(s, w)] = float(np.clip((dv * (pr.total - pr.mu_tr)).sum() / (dv ** 2).sum(), 0.5, 1.2))
    P = run(G, post=lambda p, mu, s, w: mu + sdict[(s, w)] * (p - mu), seasons=range(2015, 2026))
    V.append(("a shrink", "s refit weekly from earlier misses", P, "mt", "p_emp"))
    rt["s refit, first/last"] = f"{sdict[(2015, 1)]:.3f} / {sdict[(2025, max(w for s, w in sdict if s == 2025))]:.3f}"
    log("(a-wf) done", rt["s refit, first/last"])
    # (b) the upside only
    for u_ in (0.5, 0.6, 0.7, 0.8, 0.9):
        P = run(G, post=(lambda u_: lambda p, mu, s, w: np.where(p > mu, mu + u_ * (p - mu), p))(u_), seasons=range(2015, 2026))
        V.append(("b upside", f"above the mean x {u_:.1f}", P, "mt", "p_emp"))
    for k_ in (2.0, 4.0):
        for u_ in (0.3, 0.5):
            P = run(G, post=(lambda k_, u_: lambda p, mu, s, w: np.where(p > mu + k_, mu + k_ + u_ * (p - mu - k_), p))(k_, u_), seasons=range(2015, 2026))
            V.append(("b upside", f"knee +{k_:g}, beyond it x {u_:.1f}", P, "mt", "p_emp"))
    log("(b) done")
    # (c) the chance
    for pc, nm in (("p_sym", "symmetric residuals (mirrored)"), ("p_2p", "two-piece: upper half above, lower half below the median"), ("p_norm", "normal curve (p_over)"),
                   ("p_oos", "earlier out-of-sample misses, all"), ("p_oos_half", "earlier out-of-sample misses, same projected half")):
        V.append(("c chance", nm, P0, "mt", pc))
    # (d) drift, forms scoring_env did not try
    for N in (128, 256, 512):
        for c_ in (0.5, 1.0):
            P = run(G, offset=f"lvl{N}", offset_c=c_, seasons=range(2015, 2026))
            V.append(("d drift", f"offset: league mean of last {N} games x {c_:g}", P, "mt", "p_emp"))
    x = P0.join(G[["total", "total_line"]]); xs = x[x.total.notna()].sort_values(["season", "week"])
    for N in (128, 256):
        for k_ in (0.5, 1.0):
            bias = {}
            for s in range(2015, 2026):
                for w in sorted(P0[P0.season == s].week.unique()):
                    pr = xs[(xs.season < s) | ((xs.season == s) & (xs.week < w))].tail(N); bias[(s, w)] = float((pr.total - pr.mt).mean())
            P = P0[P0.season >= 2015].copy(); b_ = np.array([bias[(s, w)] for s, w in zip(P.season, P.week)])
            P["mt"] = P.mt + k_ * b_
            P["p_emp"] = np.concatenate([p_emp(P.mt.values[(P.season == s).values & (P.week == w).values], G.total_line.reindex(P.index[(P.season == s).values & (P.week == w).values]).values, TRES[(s, w)])
                                         for s, w in dict.fromkeys(zip(P.season, P.week))])
            V.append(("d drift", f"own recent miss: last {N} games x {k_:g}", P, "mt", "p_emp"))
    log("(d) done")
    # (e) weather interactions
    base = list(M.TOTAL_FEATS)
    for nm, extra in (("+ wind x pass rate", ["wind_pass"]), ("+ warm/dome team in the cold", ["wic_sum"]), ("+ both", ["wind_pass", "wic_sum"]), ("+ both, and the pass-rate sum", ["wind_pass", "wic_sum", "pr_sum"])):
        P = run(G, feats=base + extra, seasons=range(2015, 2026)); V.append(("e weather", nm, P, "mt", "p_emp"))
    log("(e) done")
    # (f) the total from the team-points equations
    t2 = time.time(); played = f[f.pf.notna()]; out = []
    for s in range(2015, 2026):
        for w in sorted(f[f.season == s].week.unique()):
            tr = played[(played.season >= M.TRAIN_FROM) & ((played.season < s) | ((played.season == s) & (played.week < w)))]; te = f[(f.season == s) & (f.week == w)]
            m = M.fit_points(tr); te = te.assign(pr=m.predict(te[M.FEATS].values)); trp = tr.assign(pr=m.predict(tr[M.FEATS].values))
            gs = te.groupby("game_id").pr.sum(); gt = trp.groupby("game_id").agg(pr=("pr", "sum"), pf=("pf", "sum"), n=("pr", "size")); gt = gt[gt.n == 2]
            res = (gt.pf - gt.pr).values; gs = gs.reindex(G.index.intersection(gs.index))
            out.append(pd.DataFrame({"mt": gs.values, "p_emp": p_emp(gs.values, G.total_line.reindex(gs.index).values, res), "season": s, "week": w}, index=gs.index))
    PS = pd.concat(out); V.append(("f team points", "sum of the ridge points equation (own misses for the chance)", PS, "mt", "p_emp"))
    rt["(f) ridge-sum walk-forward"] = time.time() - t2
    PB = P0[P0.season >= 2015].copy(); PB["mt"] = (pv.home_pts_eq + pv.away_pts_eq).reindex(PB.index)
    PB["p_emp"] = np.concatenate([p_emp(PB.mt.values[(PB.season == s).values & (PB.week == w).values], G.total_line.reindex(PB.index[(PB.season == s).values & (PB.week == w).values]).values, TRES[(s, w)])
                                  for s, w in dict.fromkeys(zip(PB.season, PB.week))])
    V.append(("f team points", "sum of the live seven-model blend (pred_v3; total equation's misses for the chance)", PB, "mt", "p_emp"))
    PA = PB.copy(); PA["mt"] = (PB.mt + P0.mt.reindex(PB.index)) / 2
    PA["p_emp"] = np.concatenate([p_emp(PA.mt.values[(PA.season == s).values & (PA.week == w).values], G.total_line.reindex(PA.index[(PA.season == s).values & (PA.week == w).values]).values, TRES[(s, w)])
                                  for s, w in dict.fromkeys(zip(PA.season, PA.week))])
    V.append(("f team points", "half the total equation, half the blend sum", PA, "mt", "p_emp"))
    log("(f) done")
    rows = []
    for fam, nm, P, mc, pc in V:
        rows.append({"family": fam, "variant": nm, **score_variant(P[P.season >= 2015], G, mc, pc)})
    S = pd.DataFrame(rows); rt["part 2"] = time.time() - t
    b0 = S.iloc[0]
    # the verdict by the rule: MAE better on all three with the under record not worse on any, or the under record better on all three with MAE not worse on any
    def verdict(r):
        dm = [r[f"mae_{w}"] - b0[f"mae_{w}"] for w in W]; du = [r[f"under55_pct_{w}"] - b0[f"under55_pct_{w}"] for w in W]
        mae_all, mae_ok = all(d < -1e-4 for d in dm), all(d <= 1e-4 for d in dm)
        und_all, und_ok = all(d > 0 for d in du), all(d >= 0 for d in du)
        if r.name == 0:
            return "base"
        if (mae_all and und_ok) or (und_all and mae_ok):
            return "ADOPTABLE"
        return f"not adopted: MAE better on {sum(d < -1e-4 for d in dm)}/3, under 55% win rate better on {sum(d > 0 for d in du)}/3"
    S["verdict"] = S.apply(verdict, axis=1)
    keep("p2_variants", S)
    # the fitted s and u on 2019-22
    # the knob fitted on 2019-22 (the base, s = u = 1, is a candidate: if it wins, no shrink fits)
    a_rows = S[(S.family == "a shrink") & S.variant.str.startswith("s 0")]; b_rows = S[(S.family == "b upside") & S.variant.str.startswith("above")]
    a_best = a_rows.loc[a_rows["mae_2019-22"].idxmin()].copy(); b_best = b_rows.loc[b_rows["mae_2019-22"].idxmin()].copy()
    if b0["mae_2019-22"] <= a_best["mae_2019-22"]:
        a_best["variant"] = f"1.00 (no shrink: the best s below 1, {a_best['variant']}, misses 2019-22 by {a_best['mae_2019-22']:.4f} against {b0['mae_2019-22']:.4f})"
    if b0["mae_2019-22"] <= b_best["mae_2019-22"]:
        b_best["variant"] = f"1.0 (no cap: the best factor below 1, {b_best['variant']}, misses 2019-22 by {b_best['mae_2019-22']:.4f} against {b0['mae_2019-22']:.4f})"
    # the two-piece chance against the live one at neighbouring cuts, and how many flags it changes
    X = P0[P0.season >= 2015].join(G[["game_type", "total", "total_line"]]); X = bets_frame(X); rows = []
    for c in (0.53, 0.54, 0.55, 0.56, 0.57, 0.58, 0.60):
        r = {"cut": f"{round(100 * c)}%"}
        for wn, (a, b) in W.items():
            x = X[X.season.between(a, b)]
            for pc, nm in (("p_emp", "live"), ("p_2p", "two-piece")):
                w_, l_, _, u, _ = rec(x[(1 - x[pc]) >= c], -1); r[f"{nm} {wn}"] = f"{w_}-{l_} ({u:+.1f}u)"
            r[f"flags changed {wn}"] = int((((1 - x.p_emp) >= c) != ((1 - x.p_2p) >= c)).sum())
        rows.append(r)
    TP = keep("p2_twopiece_cuts", pd.DataFrame(rows))
    log("part 2 scored")
    # --- Part 3
    t = time.time(); R = rules(D); keep("p3_rules", R)
    ob = R[(R.side == "over")].sort_values("worst window roi", ascending=False).iloc[0]
    ub = R[(R.side == "under")].sort_values("worst window roi", ascending=False).iloc[0]
    ul = R[(R.side == "under") & (R.rule == "under, chance 55%+") & (R["filter"] == "all")].iloc[0]
    def mask_of(row, pcol="p_over_emp"):
        rn = row["rule"]; num = float(rn.split()[-1].rstrip("%+")) if "and" not in rn else None
        if "and" in rn:
            rm = lambda x: (x.edge >= 3) & (x[pcol] >= 0.55)
        elif "chance" in rn:
            c = num / 100; rm = (lambda x: x[pcol] >= c) if row.side == "over" else (lambda x: (1 - x[pcol]) >= c)
        else:
            rm = (lambda x: x.edge >= num) if row.side == "over" else (lambda x: x.edge <= -num)
        return rm, FILTERS[row["filter"]]
    BT = []
    pick = lambda rn: R[(R.rule == rn) & (R["filter"] == "all")].iloc[0]
    for lab, row in (("best over rule (by worst window)", ob), ("best under rule (by worst window)", ub), ("the live under rule (55%, every game)", ul),
                     ("under, 58% chance", pick("under, chance 58%+")), ("under, 3+ edge", pick("under, edge 3+")), ("under, 4+ edge", pick("under, edge 4+"))):
        rm, fm = mask_of(row); bs = boot(D, row.side, rm, fm)
        BT.append({"which": lab, "rule": row["rule"], "filter": row["filter"], **{f"rec {w}": row[f"rec {w}"] for w in ALLW}, **{f"units {w}": row[f"units {w}"] for w in ALLW},
                   **{f"P(roi>0) {w}": bs[w] for w in ALLW}})
    BT = keep("p3_bootstrap", pd.DataFrame(BT))
    # by season: the live rule, the candidates and the one over rule that passes
    Bs = bets_frame(D); rows = []
    for lab, side, m in (("under, chance 55%+ (live)", -1, (1 - Bs.p_over_emp) >= 0.55), ("under, chance 58%+", -1, (1 - Bs.p_over_emp) >= 0.58), ("under, chance 62%+", -1, (1 - Bs.p_over_emp) >= 0.62),
                         ("under, edge 3+", -1, Bs.edge <= -3), ("under, edge 4+", -1, Bs.edge <= -4), ("over, chance 60%+, line under 43", 1, (Bs.p_over_emp >= 0.60) & (Bs.total_line < 43)),
                         ("over, edge 3+", 1, Bs.edge >= 3)):
        r = {"rule": lab}
        for s in range(2015, 2026):
            w_, l_, _, u, _ = rec(Bs[m & (Bs.season == s)], side); r[str(s)] = f"{w_}-{l_}"
        w_, l_, _, u, roi = rec(Bs[m], side); r["2015-25"] = f"{w_}-{l_}"; r["units"] = round(u, 1); r["losing seasons"] = sum(int(a) < int(b) for a, b in (r[str(s)].split("-") for s in range(2015, 2026)))
        rows.append(r)
    BS = keep("p3_by_season", pd.DataFrame(rows))
    # over rules on the best alternative chance from part 2 (c), if one reads over games differently
    Dc = D.join(P0[["p_oos_half", "p_oos", "p_sym"]], how="left")
    R2 = pd.concat([rules(Dc, "p_oos_half", "oos misses, same half"), rules(Dc, "p_oos", "oos misses, all")]); R2 = R2[R2.side == "over"]; keep("p3_rules_alt_chance", R2)
    rt["part 3"] = time.time() - t
    # --- write
    pd.concat(CSV_ROWS, ignore_index=True).to_csv(REP / "totals_sides.csv", index=False)
    write_md(D, T1, S, a_best, b_best, R, R2, BT, rt, dmt, dpe, sdict, BS, TP)
    log("DONE", {k: (round(v, 1) if isinstance(v, float) else v) for k, v in rt.items()})


def write_md(D, T1, S, a_best, b_best, R, R2, BT, rt, dmt, dpe, sdict, BS, TP):
    L = ["# Overs against unders: diagnosis, fixes, rules (29 Sep 2026)", "",
         "`experiments/totals_sides.py`, `reports/totals_sides.csv`. Matt: the unders are really good and the overs are garbage.",
         "Every number is walk-forward (a game priced only with games before its week). Windows: 2015-18 (never tuned on),",
         "2019-22 (tuned on), 2023-25 (held out). Bets: regular season, weeks 1-17, a closing total, pushes dropped, -110.", "",
         "## Adoption rule (written before the results)", "",
         "- A change to the total equation or to the chance is adopted only if the total miss (MAE, regular season) or the",
         "  55%+ under record (win rate at the cut) improves on all three windows, with nothing worse on any window: the MAE not",
         "  higher (0.0001 tolerance) and the under win rate not lower. A one- or two-window gain is not adopted.",
         "- A betting rule (over or under) is adopted only if it wins (ROI above zero at -110, 15+ bets) on all three windows.",
         "- Knobs (the shrink s, the upside factor) are fitted on 2019-22 only; 2015-18 and 2023-25 judge them.", ""]
    # Part 1
    sk = T1["skew"]; ref = T1["ref"]
    L += ["## Part 1: where the overs go wrong", "", "__DIAGNOSIS__", "",
          "### Leaning each side, by edge (model total minus the line), record and ROI", "", md_table(T1["edge"]), "",
          "`mean_realized`: the actual total minus the line on the lean's side, all 2015-25 (positive = the lean was right on average);",
          "`median_realized`: the typical game.", "",
          "### How much of the edge comes true, by side", "", md_table(T1["realize"]), "",
          "`slope`: points of (actual minus line) per point of (model minus line) within the side; 1 would mean the edge is fully real.", "",
          "### Leaning each side by the empirical chance (p_over_emp), record and ROI", "", md_table(T1["chance"]), "",
          "### Reliability of p_over_emp, over-leans and under-leans apart", "", md_table(T1["rel"]), "",
          f"### Signed bias, model total minus actual (positive = the model too high), 2015-25 regular season", "",
          md_table(T1["bias"]), "",
          f"All games: actual minus line mean {sk['mean']:+.2f}, median {sk['median']:+.2f}, unders win {sk['under_share']:.1%} of non-push games; "
          f"model minus actual mean {sk['mean_model_minus_actual']:+.2f}, median {sk['median_model_minus_actual']:+.2f}.", "",
          f"Referees ({ref['refs']} with 40+ games): the spread of their mean misses is {ref['ratio']}x what chance gives (variance {ref['obs_var']} against {ref['exp_var']}); "
          f"odd-season against even-season mean miss correlates {ref['split_corr']} over {ref['split_n']} referees; between-referee sd about {ref['sd_between_refs']} points.", ""]
    # Part 2
    def cell(r, w):
        return f"{r[f'mae_{w}']:.4f} / {r[f'bias_{w}']:+.2f} / {r[f'under55_{w}']} ({r[f'under55_pct_{w}']:.1%}, {r[f'under55_u_{w}']:+.1f}u) / {r[f'over55_{w}']} / {r[f'over3_{w}']} / {r[f'logloss_{w}']:.4f}"
    L += ["## Part 2: fixes to the total and the chance", "",
          f"The walk-forward refits the total equation before every week (training from 2013), exactly as `M.walk_forward` prices the total; "
          f"the base run matches pred_v3 (model_total within {dmt:.1e}, p_over_emp within {dpe:.1e}). Knobs picked on 2019-22 MAE: shrink s = "
          f"{a_best['variant']}, upside = {b_best['variant']}. The weekly-refit s (from earlier out-of-sample misses) ran {rt['s refit, first/last']} (2015 Week 1 / 2025 last week).", "",
          "Each cell: total MAE / bias (model minus actual) / 55%+ under record (win rate, units) / 55%+ over record / 3+ edge over record / log loss of the over chance.", "",
          "| family | variant | 2015-18 | 2019-22 | 2023-25 | verdict |", "|---|---|---|---|---|---|"]
    for _, r in S.iterrows():
        L.append(f"| {r.family} | {r.variant} | {cell(r, '2015-18')} | {cell(r, '2019-22')} | {cell(r, '2023-25')} | {r.verdict} |")
    L += ["", "### The two-piece chance against the live one at neighbouring under cuts", "", md_table(TP), "", "__PART2__", ""]
    # Part 3
    cols = ["side", "rule", "filter"] + [f"rec {w}" for w in ALLW] + [f"roi {w}" for w in W] + ["units 2015-25", "wins all three"]
    ov = R[R.side == "over"].sort_values("worst window roi", ascending=False)
    L += ["## Part 3: rules", "", "### Over rules (live p_over_emp and the edge), the 15 best by their worst window", "", md_table(ov.head(15), cols), "",
          f"Over rules tried: {len(ov)}; winning all three windows: {int(ov['wins all three'].sum())}.", "",
          "### The under rule's cutoff, every game", "", md_table(R[(R.side == 'under') & (R['filter'] == 'all')], cols), "",
          "### The 55% under rule by filter", "", md_table(R[(R.side == 'under') & (R.rule == 'under, chance 55%+')], cols), "",
          "### Over rules read off the out-of-sample chance (Part 2 c), the 8 best by worst window", "",
          md_table(R2.sort_values("worst window roi", ascending=False).head(8), ["source"] + cols), "",
          f"Over rules on those chances winning all three windows: {int(R2['wins all three'].sum())} of {len(R2)}.", "",
          "### By season (weeks 1-17)", "", md_table(BS), "",
          "### Units at -110 and the bootstrap chance that ROI is above zero (10,000 resamples of the bets)", "", md_table(BT), "",
          "__PART3__", "", "## Verdict", "", "__VERDICT__", "", "## Runtime", ""]
    for k, v in rt.items():
        L.append(f"- {k}: {v:.1f} s" if isinstance(v, float) else f"- {k}: {v}")
    txt = "\n".join(L)
    for key, val in NARRATIVE.items():
        txt = txt.replace(f"__{key}__", val)
    (REP / "totals_sides.md").write_text(txt + "\n")


NARRATIVE = {
    "DIAGNOSIS": """**In plain words.** The overs lose for three reasons that stack; the unders win for one of the same reasons plus a real
signal at large edges.

1. **The typical game lands under.** Over 2,895 regular-season games of 2015-25 the actual total beat the closing line by
   +0.40 points on average, but the median game landed 0.5 under it, and unders won 51.1% of non-push games. The total
   equation predicts the average: its bias is +0.04, yet it sits 0.71 above the median game. A bet is paid on the typical
   game, so every over starts about a point behind and every under a point ahead.
2. **The model leans over, and its over projections run hot.** It sits over the line in 1,689 games and under in 1,206
   (0.4 points above the line on average). On its over-leans it is 1.38 points too high (the line is 0.84 too low); only
   38% of an over edge comes true on average, and each point of over edge buys 0.15 points of actual-minus-line. The median
   over-lean lands 0.5 over and wins 50.5%, under the 52.4% break-even. Over edges of 2, 3, 4 and 5 points all lose (-4% to
   -19% ROI over 2015-25, and in nearly every window); the edge size carries no information until 6+ (26-17, 43 bets).
   The over-leans that go worst are the model's biggest projections (projected 49-52: over 3+ 36-47; 52+: 11-20; line
   46-49: 24-36), cold outdoor games (model +2.95 too high; a warm-climate or dome team in the cold +4.7, over 3+ 6-17),
   primetime (+0.88, over 3+ 41-53) and games of one good and one bad offense (+0.66, over 3+ 104-119). Over calls on low
   lines are fine (line under 40: 50-40; 40-43: 74-68). Division games (+0.72) and two good defenses (+0.82) also run hot
   on every window, though their over calls only break even. By window the over-lean overshoot is +2.20 (2015-18, the 2017
   drop), +1.07 (2019-22) and +0.83 (2023-25).
3. **The chance ignores both.** p_over_emp on over-leans said 57%, 62% and 68% in the 55-60, 60-65 and 65+ bands and won
   49.4%, 50.0% and 55.7% (8 to 12 points hot); on under-leans it said 57%, 62% and 69% and won 51.6%, 55.5% and 65.3%
   (3 to 7 points hot). An over at a "60%" chance is a coin flip; an under at 65% is close to what it says.

**The unders.** Small under edges (0 to 3 points) lose like the overs; from 3 points up the under edge is real: 177-112
(+16.9% ROI) with 44% of the edge coming true and the median game 2.75 under the line, positive in every window and every
edge band from 3 up. The under-leans are also too extreme on average (model 1.85 too low), but the skew is on their side.

**What does not matter.** Pace, rest and the week of the season move the bias by half a point or less and not the same way
in every window. The referee carries no trait left in the misses (the per-referee spread is 0.66x chance and
odd-season against even-season correlates -0.19), so ref_tot already has what there is.""",
    "PART2": """**Reading Part 2.** No change to the equation passes, and nothing moves the over side:

- (a) Shrinking the total toward the training mean lowers the 2015-18 miss (the 2017 drop) and raises the miss on 2019-22 and
  2023-25 at every s; fitted on 2019-22 the best s is 1.0 (no shrink). The out-of-sample slope of actual on projection is
  0.65 to 0.93, so the deviations are too big for the average, but shrinking does not lower the absolute miss outside
  2015-18, and the under record falls on 2019-22 and 2023-25 at every s.
- (b) Capping the upside at 0.5 to 0.9 of the deviation cuts the 2015-18 and 2023-25 misses, raises 2019-22, drags the bias
  negative and costs the under record on 2019-22 and 2023-25 at every factor. The overs it removes were not the losing ones (the over 3+ record
  shrinks without improving).
- (c) The two-piece chance meets the letter of the rule at the 55% cut by 1 to 6 bets a window (141-130, 175-127, 70-58
  against 135-127, 175-128, 71-59), but at 53, 54, 56, 57 and 58% it is worse by units on at least one window (it is
  ahead on all three only at 55 and 60%), it
  changes only 3 to 15 flags a window, and its log loss is worse on all three windows: a coin-flip difference, not adopted.
  The symmetric and normal chances drop the skew and with it a third of the unders; the out-of-sample pools read
  slightly better by log loss on two windows but lose under record on all three, and no over rule on them wins.
- (d) Both new drift forms (a league-level offset with a fixed coefficient, and a correction by the equation's own recent
  miss) trade windows the way the scoring_env inputs did: the 128/256-game forms help 2019-22 or 2023-25 and hurt 2015-18;
  the 512-game offset helps 2015-18 and 2023-25 and hurts 2019-22.
- (e) Wind x both teams' pass rate and the warm-or-dome-team-in-the-cold count lower the 2015-18 miss only; the cold-game
  overshoot is almost all 2015-18 (+9.99 there, +1.4 since), 70 games in all.
- (f) The sum of the team-points equations misses by more on every window (blend sum 10.758 / 10.576 / 10.281 against
  10.744 / 10.541 / 10.177); half of each is better on two windows and worse on 2023-25. The total keeps its own equation.""",
    "PART3": """**Reading Part 3.** One over rule of 100 meets the letter: over at a 60%+ chance on a line under 43 (31-25, 18-16, 33-27,
+7.2 units, bootstrap chance of a positive ROI 0.71 over 2015-25, two losing seasons of eleven). At a true 50% a rule has
about a one-in-three chance of a positive ROI in a window of 60 to 100 bets, so about 3 of 100 rules would pass all three
windows by luck alone; one passing is less than chance. No over rule is adopted. Over 3+ has six losing seasons of eleven.

The live under rule (55%) no longer wins on all three windows: 2015-18 is 135-127, -4.7 units (ROI -1.6%, bootstrap 0.38).
The cuts that do: chance 58% (243-187, +37.3u, but 2023-25 is +0.9u), 62% (136-76, +52.4u), and the edge 3+ and 3.5+
(177-112, +53.8u; 134-74, +52.6u). Under at 3+ points of edge has no losing season in eleven (2016 is 11-11), and every
edge cut from 3 up is positive on every window (4+ and 5+ have under 15 bets in 2023-25). Its bootstrap chance of a positive
ROI is 0.81 / 1.00 / 0.70 by window and 0.999 over 2015-25. Of the 55% rule's filters, primetime and weeks 9-17 win all
three windows (105-61, 185-131), but those are two of nine filters tried on it.""",
    "VERDICT": """- **The total equation and the chance: nothing adopted.** No form of shrink, upside cap, drift term, weather interaction
  or team-points sum lowers the total miss on all three windows, and none lifts the under record on all three; the one
  chance that meets the letter (two-piece) does so by a handful of bets, reverses at the neighbouring cuts and scores worse
  by log loss on every window. The total equation, TOTAL_FEATS and p_over_emp stay as they are.
- **Overs: no rule.** The overs lose because the typical game lands under the line, because the equation's over-leans run
  1.4 points hot (mostly its biggest projections, cold games with warm or dome teams, primetime and mismatched offenses),
  and because the chance does not know either. One over rule of 100 passes, fewer than luck gives; keep overs unflagged.
- **Unders: the 55% cut fails the every-window rule on 2015-18 today** (135-127, -4.7u). Under at 3+ points of edge (model
  total 3 or more below the line) wins on all three windows (61-46, 95-50, 21-16; +10.4, +40.0, +3.4 units at -110; 177-112,
  +53.8u, ROI +16.9% over 2015-25), with no losing season, and every edge cut from 3 up is positive on every window. It
  meets the adoption rule and is recommended as the tracked totals flag in place of the 55% chance. Caveats: it was chosen
  after all three windows were seen (15 under rules tried), so no untouched window is left to confirm it; 2023-25 is thin
  (37 bets, bootstrap 0.70); and on the 25 Sep equation (before qb_form_sum and ref_tot) the same rule was 10-13 on 2023-25
  (reports/totals_fix.csv), so the record moves with the equation. Grade it live, not bet, as the 55% rule is now.""",
}

if __name__ == "__main__":
    main()
