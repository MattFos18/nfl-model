"""Weekly picks table: every game with the model's score, line, edge, probabilities and bet flag.

Usage: python -m nflmodel.picks --season 2026 --week 4 [--baseline]
Writes reports/picks_<season>_wk<week>.md and .csv.
"""
from __future__ import annotations
import argparse
import numpy as np, pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT, REP = ROOT / "data" / "processed", ROOT / "reports"
SPREAD_EDGE, TOTAL_EDGE = 4.0, None   # 23 Sep 2026: 4 replaced 5 (best overall rate at twice the volume, both windows; reports/threshold_sweep.csv)  # spread: the ROI-best threshold that holds in both backtest windows. Totals: no threshold does (22 Sep 2026 sweep), so no total flags
SHADOW_EDGE = 4.5   # 23 Sep 2026: logged alongside the flag, never bet, to decide the cut on live games (4.5 showed the best rate on the rebuilt backtest)
LAST_BET_WEEK = 17   # no flags in Week 18: starters rest and the line knows it before the ratings do
EARLY_LAST_WEEK = 13   # the early-weeks shadow: weeks 14 to 17 are the one stretch where the flag sits under break-even (docs section 14)
TREES_EDGE = 5.0   # 25 Sep 2026: the blend's tree model on its own (reports/bet_wins.csv)
TOTAL_SHADOW = {"prob": 0.55, "side": "under"}   # 25 Sep 2026: unders at a 55%+ chance (the skewed spread of real totals, model.p_over_emp); overs lose every way tried (experiments/totals_fix.py). Graded live, not bet
EARLY_UNDER = {"weeks": 3, "prob": 0.59}   # 30 Sep 2026 (reports/bet_rules_sweep.md): unders needing 59%+ in weeks 1 to 3 (55% after) beat the totals flag on all three windows; tracked, not bet
HOOK = {"on": (2.5, 3.0, -3.0, -3.5), "odds": -125}   # 30 Sep 2026 (reports/spread_research.md): the flag's bet bought half a point on or off 3 at -125; tracked, not bet
# 27 Sep 2026: the 55% cut is on the RAW chance p_over_emp (rule_mask, bet(), the Backtest tab, report_records: the rule and every record it
# has stay as they were). The chance the cards DISPLAY is the calibrated one, p_over_cal (over_calibration below): the same monotone
# mapping for every game, so a threshold on one is a threshold on the other (a 55% under raw reads about 53% calibrated on today's fit)
# shadow rules: recorded and graded next to the flag, never bet. name -> (spread edge, side restriction, label)
SHADOWS = {"shadow45": (SHADOW_EDGE, None, f"{SHADOW_EDGE:g}+ edge"), "shadowdog": (SPREAD_EDGE, "dog", f"{SPREAD_EDGE:g}+ edge, model's side the underdog or pick'em"),
           "shadowearly": (SPREAD_EDGE, "wk13", f"{SPREAD_EDGE:g}+ edge, weeks 1 to {EARLY_LAST_WEEK} only"),
           "shadowtrees": (TREES_EDGE, "trees", f"boosted trees alone, {TREES_EDGE:g}+ edge"),
           "shadowunder": (TOTAL_SHADOW["prob"], "under_prob", f"Under, {100 * TOTAL_SHADOW['prob']:.0f}%+ chance (the totals flag)"),
           "shadowunderearly": (TOTAL_SHADOW["prob"], "under_prob_early", f"Under, {100 * EARLY_UNDER['prob']:.0f}%+ chance in weeks 1 to {EARLY_UNDER['weeks']}, {100 * TOTAL_SHADOW['prob']:.0f}%+ after"),
           "shadowhook": (SPREAD_EDGE, "hook", f"{SPREAD_EDGE:g}+ edge on +2.5, +3, -3 or -3.5, half a point bought on or off 3 at {HOOK['odds']}")}
WINDOWS = {"2015-18": (2015, 2018), "2019-22": (2019, 2022), "2023-25": (2023, 2025)}
WINDOW_LABEL = {"2015-18": "untouched", "2019-22": "tuning", "2023-25": "held out"}   # the words reports/backtest_v3.md and docs section 9 use
CAL_FROM, CAL_CAP = 2019, 7.0   # the cover calibration: regular-season games from this season on, the edge capped at this many points
OVER_CAL_FROM, OVER_CAL_CLIP, OVER_CAL_MIN_N = 2015, 0.02, 200   # 27 Sep 2026: the over calibration (over_calibration): regular-season games from this season on (every priced season; the audit fit from 2015 scored best on every window, reports/calibration_audit.md), p_over_emp clipped to [0.02, 0.98] before the logit, the identity under 200 games
# 27 Sep 2026: the home win calibration (home_calibration): the same form on p_home (the audit: the home side won 39% of the games it was
# said to win 45% of, 2015-25 n 556, z -3.0; a home-field term that follows recent seasons did not fix it, reports/home_field_recency.md).
# Fit on regular-season games from 2015 to the season before the one priced, ties dropped; the identity under 500 games (two seasons: with
# the over's 200 the 2016 season was scored on a fit to 2015 alone, 256 games, which read worse than the raw chance and left 2016-18 a wash;
# from two seasons on the mapping is better by log loss and Brier on 2016-18, 2019-22, 2020-22 and 2023-25, the three later windows the same either way)
HOME_CAL_FROM, HOME_CAL_CLIP, HOME_CAL_MIN_N = 2015, 0.02, 500
KELLY_FRACTION, DEFAULT_ODDS = 0.25, -110.0   # the stake: a quarter of the Kelly fraction; the price when no book's is logged
# 28 Sep 2026: 6-point teaser legs on the model's side (the Picks tab's teaser builder). The raw chance is the bell curve's (the fit's
# sigma) at the line moved TEASE_PTS the model's way; it runs hot (said 72-73%, hit 70.7% on spreads and 68-71% on totals, every window),
# so each leg is calibrated on the seasons before the one priced from TEASE_FROM: spreads by a shift of the logit (the two-coefficient
# form lost to the raw chance on 2023-25 by log loss), totals by intercept and slope (better than the raw chance and the shift on 2016-18
# and 2023-25); both forms beat the raw chance on 2016-18, 2019-22 and 2023-25 by log loss and Brier (reports/decision_log.md). The
# identity under TEASE_MIN_N legs. TEASER_ODDS: the book price the builder starts from by number of legs (editable on the page);
# PARLAY_LEG_ODDS the straight price a parlay leg starts from.
TEASE_PTS, TEASE_FROM, TEASE_CLIP, TEASE_MIN_N = 6.0, 2015, 0.02, 200
TEASE_SLOPE = {"spread": False, "total": True}   # whether the leg's calibration fits a slope on the logit (False: a shift, slope 1)
TEASER_ODDS = {2: -110.0, 3: 160.0, 4: 260.0, 5: 400.0, 6: 600.0}
PARLAY_LEG_ODDS = -110.0


def tease_raw(edge_abs: float, sigma: float, pts: float = TEASE_PTS) -> float:
    """The bell curve's chance that the model's side covers its line moved `pts` its way: the margin (or total) as a normal on
    the model's number with the fit's sigma, so the side that is |edge| points inside the line clears the teased line when the
    miss stays inside |edge| + pts."""
    from scipy.stats import norm
    return float(norm.cdf((abs(float(edge_abs)) + pts) / float(sigma)))


def _tease_rows(pred: pd.DataFrame, games: pd.DataFrame) -> pd.DataFrame:
    """The legs the teaser calibration learns from: regular season from TEASE_FROM, a line and a result, the model's side
    (edge not zero), pushes at the teased line dropped; kind (spread, total), lg = logit of the raw chance (clipped to
    TEASE_CLIP), hit = the teased line covered. Priced at the schedule's closing line (pred_v3), which is what the backtest grades."""
    g = games.set_index("game_id")
    d = pred[(pred.game_type == "REG") & (pred.season >= TEASE_FROM)].copy()
    d["hs"] = d.game_id.map(g.home_score); d["as_"] = d.game_id.map(g.away_score); d["sl"] = d.game_id.map(g.spread_line); d["tl"] = d.game_id.map(g.total_line)
    d = d[d.hs.notna()]
    m = d.hs - d.as_; t = d.hs + d.as_
    out = []
    for kind, edge, val, line, sig in [("spread", d.model_spread - d.sl, m, d.sl, d.sigma_margin), ("total", d.model_total - d.tl, t, d.tl, d.sigma_total)]:
        ok = edge.notna() & (edge != 0) & line.notna() & sig.notna()
        e, v, l, sg = edge[ok], val[ok], line[ok], sig[ok]
        raw = pd.Series([tease_raw(x, y) for x, y in zip(e, sg)], index=e.index)
        dd = pd.Series(np.where(e > 0, v - (l - TEASE_PTS), (l + TEASE_PTS) - v), index=e.index)   # the side's margin over its teased line
        x = pd.DataFrame({"season": d.season[ok], "kind": kind, "raw": raw, "hit": (dd > 0).astype(int)})[dd != 0]
        out.append(x)
    x = pd.concat(out)
    q = x.raw.clip(TEASE_CLIP, 1 - TEASE_CLIP); x["lg"] = np.log(q / (1 - q))
    return x[["season", "kind", "lg", "hit"]]


def _fit_logit(d: pd.DataFrame, y: str, slope: bool, min_n: int) -> tuple[float, float, int]:
    """(a, b, n): logistic(a + b x lg) fit on d, with b free (slope) or fixed at 1 (a shift alone, by Newton's method on the
    intercept); the identity (0, 1, n) under min_n rows or one outcome only."""
    if len(d) < min_n or d[y].nunique() < 2:
        return (0.0, 1.0, int(len(d)))
    if slope:
        from sklearn.linear_model import LogisticRegression
        m = LogisticRegression(C=10.0).fit(d[["lg"]].values, d[y].values)
        return (float(m.intercept_[0]), float(m.coef_[0][0]), int(len(d)))
    a, lg, yy = 0.0, d.lg.values, d[y].values
    for _ in range(100):
        q = 1.0 / (1.0 + np.exp(-(a + lg))); step = (yy - q).sum() / max(1e-12, (q * (1 - q)).sum())
        a += step
        if abs(step) < 1e-12:
            break
    return (float(a), 1.0, int(len(d)))


def tease_calibration(pred: pd.DataFrame, games: pd.DataFrame, season: int) -> dict:
    """{"spread": (a, b, n), "total": (a, b, n)}: each leg kind's calibration, fit on regular-season legs from TEASE_FROM to
    season - 1 (the season being priced never learns from itself; in-season the fit is the one made before Week 1), a shift
    for spreads and intercept-and-slope for totals (TEASE_SLOPE). The identity under TEASE_MIN_N legs."""
    d = _tease_rows(pred, games); d = d[d.season < season]
    return {k: _fit_logit(d[d.kind == k], "hit", TEASE_SLOPE[k], TEASE_MIN_N) for k in ("spread", "total")}


def tease_calibrations(pred: pd.DataFrame, games: pd.DataFrame) -> dict:
    """season -> tease_calibration as of that season, for every season the prediction table holds (the calibration audit
    grades each season with the fit that would have been in force)."""
    return {int(s): tease_calibration(pred, games, int(s)) for s in sorted(pred.season.unique())}


def tease_cal_p(cal, raw) -> float:
    """The calibrated teased chance: logistic(a + b x logit(raw clipped to TEASE_CLIP))."""
    a, b = cal[0], cal[1]
    q = min(max(float(raw), TEASE_CLIP), 1 - TEASE_CLIP)
    return float(1.0 / (1.0 + np.exp(-(a + b * np.log(q / (1 - q))))))


def parlay_odds(american: list[float]) -> float:
    """The American price of a parlay of straight legs at these prices: the decimal payouts multiplied."""
    dec = 1.0
    for o in american:
        dec *= (1.0 + 100.0 / abs(o)) if o < 0 else (1.0 + o / 100.0)
    return round((dec - 1.0) * 100.0, 1) if dec >= 2.0 else round(-100.0 / (dec - 1.0), 1)


def break_even(odds: float = DEFAULT_ODDS) -> float:
    """The win rate a bet at these American odds needs to break even."""
    return abs(odds) / (abs(odds) + 100.0) if odds < 0 else 100.0 / (odds + 100.0)


def page_rules(d: pd.DataFrame | None = None) -> dict:
    """Everything the page says about the betting rules, from the constants above (and each rule's backtest record when d,
    the joined backtest table of played regular-season games with a line, is given), so no sentence on the page restates
    a number by hand."""
    out = {"spread_edge": SPREAD_EDGE, "total_edge": TOTAL_EDGE, "total_shadow": TOTAL_SHADOW, "last_week": LAST_BET_WEEK, "early_last_week": EARLY_LAST_WEEK,
           "kelly_fraction": KELLY_FRACTION, "default_odds": DEFAULT_ODDS, "break_even": round(break_even(), 4), "cal_from": CAL_FROM, "cal_cap": CAL_CAP, "over_cal_from": OVER_CAL_FROM, "home_cal_from": HOME_CAL_FROM,
           "tease_pts": TEASE_PTS, "tease_from": TEASE_FROM, "tease_min_n": TEASE_MIN_N, "teaser_odds": {str(k): v for k, v in TEASER_ODDS.items()}, "parlay_leg_odds": PARLAY_LEG_ODDS,
           "windows": [{"key": k, "from": a, "to": b, "label": WINDOW_LABEL[k]} for k, (a, b) in WINDOWS.items()]}
    if d is not None:
        out["rules"] = rule_records(d).to_dict("records")
    return out


def _spread(d, side_rule=None):
    """The spread a rule reads: the model's, or the tree model's alone for the trees shadow."""
    if side_rule == "trees":
        return d.home_m_trees - d.away_m_trees if "home_m_trees" in d.columns else pd.Series(np.nan, index=d.index)
    return d.model_spread


def rule_mask(d: pd.DataFrame, edge: float, side_rule=None) -> pd.Series:
    """The games a rule bets on, from a joined prediction table (same tests as bet() below): regular season, weeks 1 to LAST_BET_WEEK."""
    if side_rule in ("under_prob", "under_prob_early"):
        if "p_over_emp" not in d.columns:
            return pd.Series(False, index=d.index)
        thr = np.where(d.week <= EARLY_UNDER["weeks"], EARLY_UNDER["prob"], edge) if side_rule == "under_prob_early" else edge
        return ((1 - d.p_over_emp) >= thr) & (d.week <= LAST_BET_WEEK) & d.total_line.notna()
    e = _spread(d, side_rule) - d.spread_line
    m = (e.abs() >= edge) & (d.week <= LAST_BET_WEEK) & d.spread_line.notna()
    if side_rule == "dog":
        m &= ~((np.sign(e) == np.sign(d.spread_line)) & (d.spread_line != 0))
    if side_rule == "wk13":
        m &= d.week <= EARLY_LAST_WEEK
    if side_rule == "hook":   # our side's number on 2.5, 3 or 3.5 either way, where half a point moves it on or off 3
        m &= pd.Series(np.where(e > 0, -d.spread_line, d.spread_line), index=d.index).isin(HOOK["on"])
    return m


def record(d: pd.DataFrame, m: pd.Series, side_rule=None) -> tuple[int, int]:
    """Wins and losses on the rule's side over the rows m (pushes dropped)."""
    if side_rule in ("under_prob", "under_prob_early"):
        cm = d.home_score + d.away_score - d.total_line; f = m & (cm != 0); w = int((cm < 0)[f].sum())
        return w, int(f.sum()) - w
    if side_rule == "hook":   # graded at the bought number: our side's line plus half a point
        e = d.model_spread - d.spread_line; ours = np.where(e > 0, d.home_score - d.away_score, d.away_score - d.home_score)
        cm = pd.Series(ours + np.where(e > 0, -d.spread_line, d.spread_line) + 0.5, index=d.index)
        f = m & (cm != 0); w = int((cm > 0)[f].sum())
        return w, int(f.sum()) - w
    e = _spread(d, side_rule) - d.spread_line; cm = d.home_score - d.away_score - d.spread_line
    f = m & (cm != 0); w = int((((e > 0) & (cm > 0)) | ((e < 0) & (cm < 0)))[f].sum())
    return w, int(f.sum()) - w


def rule_records(d: pd.DataFrame) -> pd.DataFrame:
    """Every rule (the flag and the shadows) on the three backtest windows, regular season, weeks 1 to LAST_BET_WEEK.
    d is backtest.join(pred, games) limited to played regular-season games with a line."""
    rules = [("model", SPREAD_EDGE, None, f"{SPREAD_EDGE:g}+ edge (the flag)")] + [(n, e, s, lab) for n, (e, s, lab) in SHADOWS.items()]
    rows = []
    for name, edge, sr, lab in rules:
        r = {"rule": name, "label": lab, "edge": edge, "side_rule": sr}
        for w, (a, b) in WINDOWS.items():
            x = d[d.season.between(a, b)]; wi, lo = record(x, rule_mask(x, edge, sr), sr); r[w] = f"{wi}-{lo}"
        rows.append(r)
    return pd.DataFrame(rows)


def fair_ml(p):
    return np.where(p >= 0.5, -100 * p / (1 - p), 100 * (1 - p) / p)


def table(season: int, week: int, spread_edge=SPREAD_EDGE, total_edge=TOTAL_EDGE) -> pd.DataFrame:
    """This week's games priced against the current consensus line: the newest lines-log snapshot, median across
    sources to the half point (lines.latest), the schedule's line only where the log has none (26 Sep 2026: the flag,
    edges and cover odds were decided on the Tuesday nflverse line while the card showed the live one). The model's
    chances are re-priced at that line with the fit that priced the game (model.price_at, pred_v3_dist.json); the
    model's points never read a line. Runs in the weekly run and in every line watch (export_web --week)."""
    from . import lines as LN, model as M
    pred = pd.read_parquet(OUT / "pred_v3.parquet")
    games = pd.read_parquet(OUT / "games.parquet")
    p = pred[(pred.season == season) & (pred.week == week)].copy()
    g = games.set_index("game_id")
    p["gameday"] = p.game_id.map(g.gameday)
    log = LN.load_log()
    live = LN.live_lines(p[["game_id"]].assign(spread_line=p.game_id.map(g.spread_line), total_line=p.game_id.map(g.total_line)), log).set_index("game_id")
    for c in live.columns:
        p[c] = p.game_id.map(live[c])
    p["home_score"] = p.game_id.map(g.home_score)
    p["away_score"] = p.game_id.map(g.away_score)
    p["spread_edge"] = p.model_spread - p.spread_line
    p["total_edge"] = p.model_total - p.total_line
    p["tree_edge"] = _spread(p, "trees") - p.spread_line
    dist = M.load_dist(season, week)
    if dist is not None:   # the model's cover and over chances at the live line, same function and fit as the model run
        pr = [M.price_at(r.model_spread, r.model_total, r.spread_line, r.total_line, dist) for r in p.itertuples()]
        for k in ("p_home", "p_cover_home", "p_over", "p_over_emp"):
            p[k] = [x[k] for x in pr]
    p["priced_live"] = dist is not None

    def bet(r, spread_edge=spread_edge, total_edge=total_edge, side_rule=None):
        out = []
        if r.week > LAST_BET_WEEK:
            return ""   # final week: starters rest and the line knows it before the ratings do
        if side_rule == "dog" and pd.notna(r.spread_line) and np.sign(r.spread_edge) == np.sign(r.spread_line) and r.spread_line != 0:
            return ""   # the model's side is the favourite: the dogs-only rule sits this one out
        if side_rule == "wk13" and r.week > EARLY_LAST_WEEK:
            return ""   # the early-weeks rule sits out the late season
        if side_rule in ("under_prob", "under_prob_early"):
            pe = getattr(r, "p_over_emp", np.nan); thr = EARLY_UNDER["prob"] if side_rule == "under_prob_early" and r.week <= EARLY_UNDER["weeks"] else spread_edge
            return f"Under {r.total_line:g}" if pd.notna(r.total_line) and pd.notna(pe) and 1 - pe >= thr else ""
        if side_rule == "hook":
            return ""   # built from the flag's bet at the best number, below
        se = r.tree_edge if side_rule == "trees" else r.spread_edge
        if pd.notna(r.spread_line) and pd.notna(se) and abs(se) >= spread_edge:
            side = r.home_team if se > 0 else r.away_team
            line = -r.spread_line if se > 0 else r.spread_line
            out.append(f"{side} {line:+g}")
        if total_edge is not None and pd.notna(r.total_line) and abs(r.total_edge) >= total_edge:
            out.append(("Over " if r.total_edge > 0 else "Under ") + f"{r.total_line:g}")
        return ", ".join(out) if out else ""
    p["bet"] = p.apply(bet, axis=1)
    for name, (edge, side_rule, _) in SHADOWS.items():   # the shadow rules: recorded, graded, never bet
        p[f"{name}_bet"] = p.apply(lambda r, e=edge, sr=side_rule: bet(r, e, None, sr), axis=1)
    p["shadow_bet"] = p["shadow45_bet"]
    # calibrated cover odds: what spread edges of this size have actually converted to, fitted on every graded
    # backtest game before this season (the model's own cover odds run about 10 points hot: the line carries
    # information the model does not). Totals carry one chance, p_over_emp (26 Sep 2026, reports/total_prob.csv: the
    # calibrated total chance scored better on two windows of three by log loss but not on 2020-22, and the 55% under
    # flag re-expressed on it did worse on 2016-18, so it failed the every-window test; the card showed both before)
    cal_s, _ = calibration(pred, games, season)
    p["p_cover_cal_home"] = [cal_p(cal_s, e) if e > 0 else 1 - cal_p(cal_s, e) for e in p.spread_edge.fillna(0)]
    p.loc[p.spread_line.isna(), "p_cover_cal_home"] = np.nan
    # calibrated over chance (27 Sep 2026, reports/calibration_audit.md): p_over_emp is priced as if the model's total were the truth
    # and the line carried nothing, and runs too far from 50% both ways (said 63% over, 50% came, 2015-25). p_over_cal maps it with
    # a logistic on its logit, fit on the seasons before this one from OVER_CAL_FROM: better log loss and Brier on every window.
    # The cards show p_over_cal; the totals flag (TOTAL_SHADOW, bet() above) stays on the raw p_over_emp, as documented at the constant
    cal_o = over_calibration(pred, games, season)
    p["p_over_cal"] = [over_cal_p(cal_o, x) if pd.notna(x) else np.nan for x in p.p_over_emp] if "p_over_emp" in p.columns else np.nan
    # 6-point teaser legs on the model's side (28 Sep 2026, the Picks tab's builder): the raw bell-curve chance at the teased line and its
    # calibrated one (tease_calibration, fit on the seasons before this one from TEASE_FROM); NaN without a line or on a zero edge
    cal_t = tease_calibration(pred, games, season)
    for kind, edge, sig in [("spread", p.spread_edge, p.sigma_margin), ("total", p.total_edge, p.sigma_total)]:
        raw = [tease_raw(e, sg) if pd.notna(e) and e != 0 and pd.notna(sg) else np.nan for e, sg in zip(edge, sig)]
        p[f"tease_{kind}_raw"] = raw
        p[f"tease_{kind}_cal"] = [tease_cal_p(cal_t[kind], r) if pd.notna(r) else np.nan for r in raw]
    # calibrated home win chance (27 Sep 2026, reports/calibration_audit.md): p_home runs hot when the home side is a slight underdog (said 45%,
    # won 39%, 2015-25). p_home_cal maps it the same way, a logistic on its logit fit on the seasons before this one from HOME_CAL_FROM: better
    # log loss and Brier on every window. The cards show p_home_cal; p_home stays on the row (the season simulation and the season file read it)
    cal_h = home_calibration(pred, games, season)
    p["p_home_cal"] = [home_cal_p(cal_h, x) if pd.notna(x) else np.nan for x in p.p_home] if "p_home" in p.columns else np.nan
    # the best available number for the model's side across the books in the latest line snapshot
    best = [best_number(LN.history(r.game_id, log), r) for r in p.itertuples()]
    p["best_line"] = [b[0] for b in best]; p["best_book"] = [b[1] for b in best]
    p["spread_edge_best"] = [(r.model_spread - b[2]) if b[2] is not None else np.nan for r, b in zip(p.itertuples(), best)]
    # a flagged spread is bet at the best available number (the flag itself is decided on the consensus line)
    def at_best(r, col="bet"):
        b0 = getattr(r, col)
        if not b0 or r.best_line is None or pd.isna(r.best_line):
            return b0
        parts = []
        for b in b0.split(", "):
            if b.startswith(("Over", "Under")):
                parts.append(b)
            else:
                parts.append(f"{b.split()[0]} {r.best_line:+g}")
        return ", ".join(parts)
    p["bet"] = p.apply(at_best, axis=1)
    for name in SHADOWS:
        p[f"{name}_bet"] = p.apply(lambda r, c=f"{name}_bet": at_best(r, c), axis=1)
    p["shadow_bet"] = p["shadow45_bet"]
    # the hook: the flag's spread at the number it is bet at, bought half a point when that moves it on or off 3, at HOOK's price
    def hook(b0):
        for b in (b0 or "").split(", "):
            if b and not b.startswith(("Over", "Under")):
                side, ln = b.rsplit(" ", 1)
                if float(ln) in HOOK["on"]:
                    return f"{side} {float(ln) + 0.5:+g}"
        return ""
    p["shadowhook_bet"] = [hook(b) for b in p.bet]
    p["shadowhook_odds"] = [HOOK["odds"] if b else np.nan for b in p.shadowhook_bet]
    # stake on a flagged spread: quarter Kelly from the calibrated cover odds for the model's side, at the best book's
    # price when it is logged, otherwise -110
    p["bet_p"] = [(pc if e > 0 else 1 - pc) if (b and pd.notna(pc)) else np.nan for b, e, pc in zip(p.bet, p.spread_edge.fillna(0), p.p_cover_cal_home)]
    p["bet_odds"] = [(b[3] if b[3] is not None else DEFAULT_ODDS) if bet else np.nan for bet, b in zip(p.bet, best)]
    p["stake_pct"] = [kelly_stake(pw, od) if pd.notna(pw) else np.nan for pw, od in zip(p.bet_p, p.bet_odds)]
    return p.sort_values("gameday")


def calibration(pred: pd.DataFrame, games: pd.DataFrame, season: int):
    """Logistic fit of 'the model's side covered' on |edge| (capped at 7), regular season, seasons before `season`,
    for spreads and for totals. Returns (intercept, slope) pairs."""
    from sklearn.linear_model import LogisticRegression
    g = games.set_index("game_id")
    d = pred[(pred.game_type == "REG") & (pred.season < season) & (pred.season >= CAL_FROM)].copy()
    d["hs"] = d.game_id.map(g.home_score); d["as_"] = d.game_id.map(g.away_score); d["sl"] = d.game_id.map(g.spread_line); d["tl"] = d.game_id.map(g.total_line)
    d = d[d.hs.notna()]
    out = []
    for edge, res in [(d.model_spread - d.sl, np.sign(d.hs - d.as_ - d.sl)), (d.model_total - d.tl, np.sign(d.hs + d.as_ - d.tl))]:
        ok = edge.notna() & (res != 0) & res.notna()
        won = (np.sign(edge[ok]) == res[ok]).astype(int)
        x = np.minimum(np.abs(edge[ok].values), CAL_CAP)[:, None]
        if len(won) < 200 or won.nunique() < 2:
            out.append((0.0, 0.0)); continue
        m = LogisticRegression(C=10.0).fit(x, won)
        out.append((float(m.intercept_[0]), float(m.coef_[0][0])))
    return out[0], out[1]


def cal_p(cal, edge):
    a, b = cal
    return float(1.0 / (1.0 + np.exp(-(a + b * min(abs(float(edge)), CAL_CAP)))))


def _over_rows(pred: pd.DataFrame, games: pd.DataFrame) -> pd.DataFrame:
    """The games the over calibration learns from: regular season from OVER_CAL_FROM, a total line, a result, pushes dropped;
    lg = logit of p_over_emp (clipped to OVER_CAL_CLIP), over = the over hit. The chance is the model run's, priced at the
    schedule's closing total (pred_v3), which is what the backtest grades."""
    g = games.set_index("game_id")
    d = pred[(pred.game_type == "REG") & (pred.season >= OVER_CAL_FROM) & pred.p_over_emp.notna()].copy()
    d["tot"] = d.game_id.map(g.home_score) + d.game_id.map(g.away_score); d["tl"] = d.game_id.map(g.total_line)
    d = d[d.tot.notna() & d.tl.notna() & (d.tot != d.tl)]
    q = d.p_over_emp.clip(OVER_CAL_CLIP, 1 - OVER_CAL_CLIP)
    d["lg"] = np.log(q / (1 - q)); d["over"] = (d.tot > d.tl).astype(int)
    return d[["season", "lg", "over"]]


def over_calibration(pred: pd.DataFrame, games: pd.DataFrame, season: int) -> tuple[float, float, int]:
    """(a, b, n): logistic fit of 'the over hit' on logit(p_over_emp), regular season, seasons OVER_CAL_FROM to season - 1
    (27 Sep 2026: the season being priced never learns from itself, the same discipline as calibration() above; in-season
    the fit is the one made before Week 1). The identity (0, 1) under OVER_CAL_MIN_N games, so p_over_cal = p_over_emp."""
    from sklearn.linear_model import LogisticRegression
    d = _over_rows(pred, games); d = d[d.season < season]
    if len(d) < OVER_CAL_MIN_N or d.over.nunique() < 2:
        return (0.0, 1.0, int(len(d)))
    m = LogisticRegression(C=10.0).fit(d[["lg"]].values, d.over.values)
    return (float(m.intercept_[0]), float(m.coef_[0][0]), int(len(d)))


def over_calibrations(pred: pd.DataFrame, games: pd.DataFrame) -> dict:
    """season -> over_calibration as of that season, for every season the prediction table holds (backtest.js and the
    calibration audit grade each season with the fit that would have been in force)."""
    return {int(s): over_calibration(pred, games, int(s)) for s in sorted(pred.season.unique())}


def over_cal_p(cal, p_over_emp) -> float:
    """The calibrated over chance: logistic(a + b x logit(p_over_emp clipped to OVER_CAL_CLIP))."""
    a, b = cal[0], cal[1]
    q = min(max(float(p_over_emp), OVER_CAL_CLIP), 1 - OVER_CAL_CLIP)
    return float(1.0 / (1.0 + np.exp(-(a + b * np.log(q / (1 - q))))))


def _home_rows(pred: pd.DataFrame, games: pd.DataFrame) -> pd.DataFrame:
    """The games the home win calibration learns from (27 Sep 2026): regular season from HOME_CAL_FROM, a result, ties dropped
    (a tie is neither a home win nor a loss); lg = logit of p_home (clipped to HOME_CAL_CLIP), hw = the home side won. The chance
    is the model run's, priced with the fit that priced the game (pred_v3), which is what the audit grades."""
    g = games.set_index("game_id")
    d = pred[(pred.game_type == "REG") & (pred.season >= HOME_CAL_FROM) & pred.p_home.notna()].copy()
    d["res"] = d.game_id.map(g.home_score) - d.game_id.map(g.away_score)
    d = d[d.res.notna() & (d.res != 0)]
    q = d.p_home.clip(HOME_CAL_CLIP, 1 - HOME_CAL_CLIP)
    d["lg"] = np.log(q / (1 - q)); d["hw"] = (d.res > 0).astype(int)
    return d[["season", "lg", "hw"]]


def home_calibration(pred: pd.DataFrame, games: pd.DataFrame, season: int) -> tuple[float, float, int]:
    """(a, b, n): logistic fit of 'the home side won' on logit(p_home), regular season, seasons HOME_CAL_FROM to season - 1 (the
    season being priced never learns from itself; in-season the fit is the one made before Week 1). The identity (0, 1) under
    HOME_CAL_MIN_N games, so p_home_cal = p_home. Tested 27 Sep 2026 against a richer form with an intercept shift for the home
    side being the model's underdog (the bucket where the miss sits): worse than the raw chance on 2016-18 and on log loss in
    2019-22, so the two-coefficient form stays (reports/decision_log.md)."""
    from sklearn.linear_model import LogisticRegression
    d = _home_rows(pred, games); d = d[d.season < season]
    if len(d) < HOME_CAL_MIN_N or d.hw.nunique() < 2:
        return (0.0, 1.0, int(len(d)))
    m = LogisticRegression(C=10.0).fit(d[["lg"]].values, d.hw.values)
    return (float(m.intercept_[0]), float(m.coef_[0][0]), int(len(d)))


def home_calibrations(pred: pd.DataFrame, games: pd.DataFrame) -> dict:
    """season -> home_calibration as of that season, for every season the prediction table holds (backtest.js and the
    calibration audit grade each season with the fit that would have been in force)."""
    return {int(s): home_calibration(pred, games, int(s)) for s in sorted(pred.season.unique())}


def home_cal_p(cal, p_home) -> float:
    """The calibrated home win chance: logistic(a + b x logit(p_home clipped to HOME_CAL_CLIP))."""
    a, b = cal[0], cal[1]
    q = min(max(float(p_home), HOME_CAL_CLIP), 1 - HOME_CAL_CLIP)
    return float(1.0 / (1.0 + np.exp(-(a + b * np.log(q / (1 - q))))))


def best_number(hist: pd.DataFrame, r):
    """(line for the model's side, book, home_spread used) from the latest snapshot; None when there is no log."""
    if hist is None or len(hist) == 0 or pd.isna(r.spread_line):
        return (None, None, None, None)
    last = hist[hist.ts == hist.ts.max()]; last = last[last.home_spread.notna()]
    if len(last) == 0:
        return (None, None, None, None)
    home_side = r.spread_edge > 0
    pick = last.loc[last.home_spread.idxmin()] if home_side else last.loc[last.home_spread.idxmax()]
    hs = float(pick.home_spread)
    line = -hs if home_side else hs
    book = str(pick.source).replace("oddsapi:", "").replace("espn:", "")
    odds = pick.get("spread_odds_home" if home_side else "spread_odds_away", np.nan)
    return (line, book, hs, float(odds) if pd.notna(odds) else None)


def kelly_stake(p_win: float, odds: float = DEFAULT_ODDS, fraction: float = KELLY_FRACTION) -> float:
    """Share of bankroll to stake at American odds, as a percentage: the Kelly criterion times a fraction (a quarter
    by default; full Kelly assumes the cover odds are exact, and calibrated odds are an estimate). 0 when the odds
    do not pay enough for the edge."""
    b = 100.0 / abs(odds) if odds < 0 else odds / 100.0
    k = (p_win * b - (1.0 - p_win)) / b
    return round(max(0.0, k) * fraction * 100.0, 2)


def log_run(p: pd.DataFrame, run_at: str | None = None) -> pd.DataFrame:
    """Append this run's numbers for every game of the week to data/runs/pred_history.csv, so the page can show how
    the model's line moved from run to run (Tuesday to Saturday) beside how the market moved."""
    run_at = run_at or pd.Timestamp.now("UTC").strftime("%Y-%m-%d %H:%M UTC")
    RUNS = OUT.parent / "runs"; RUNS.mkdir(parents=True, exist_ok=True)
    cols = ["season", "week", "game_id", "model_spread", "model_total", "spread_line", "total_line", "bet"]
    rows = p[cols].copy(); rows.insert(0, "run_at", run_at)
    # every game of the week, played or not (26 Sep 2026: played games were left out, so a card re-priced after its game
    # showed a model number that no row of its run history held; runs[] must always hold the run that priced the card)
    f = RUNS / "pred_history.csv"
    rows.round(3).to_csv(f, mode="a", header=not f.exists(), index=False)
    return rows


def markdown(p: pd.DataFrame, season: int, week: int) -> str:
    rows = []
    for r in p.itertuples():
        our_line = f"{r.home_team} {-r.model_spread:+.1f} / {r.model_total:.1f}"
        vegas = f"{r.home_team} {-r.spread_line:+g} / {r.total_line:g}" if pd.notna(r.spread_line) else "no line yet"
        edge = f"{r.spread_edge:+.1f} / {r.total_edge:+.1f}" if pd.notna(r.spread_line) else ""
        cover = f"{r.home_team} {r.p_cover_home:.0%} / {r.away_team} {1 - r.p_cover_home:.0%}" if pd.notna(r.p_cover_home) else ""
        po = getattr(r, "p_over_cal", np.nan) if pd.notna(getattr(r, "p_over_cal", np.nan)) else r.p_over_emp   # 27 Sep 2026: the calibrated chance, as the card; the raw p_over_emp stays in the csv
        over = f"Over {po:.0%} / Under {1 - po:.0%}" if pd.notna(po) else ""
        ph = getattr(r, "p_home_cal", np.nan) if pd.notna(getattr(r, "p_home_cal", np.nan)) else r.p_home   # 27 Sep 2026: the calibrated win chance, as the card; the raw p_home stays in the csv
        rows.append({"Game": f"{r.away_team} @ {r.home_team}", "Date": r.gameday,
                     "Our score": f"{r.away_team} {r.away_exp:.1f}, {r.home_team} {r.home_exp:.1f}",
                     "Our line": our_line, "Vegas": vegas, "Edge (spread / total)": edge,
                     "Win": f"{r.home_team} {ph:.0%} / {r.away_team} {1 - ph:.0%}", "Cover the spread": cover, "Total": over, "Flag": r.bet,
                     "Stake": f"{r.stake_pct:g}% at {r.bet_odds:+g}" if "stake_pct" in p.columns and pd.notna(r.stake_pct) else "",
                     **{f"Shadow: {lab}": (getattr(r, f"{name}_bet", "") if isinstance(getattr(r, f"{name}_bet", ""), str) else "") for name, (_, _, lab) in SHADOWS.items()}})
    df = pd.DataFrame(rows)
    # the flag's backtest records, computed from the prediction table every time (never typed in, so never stale)
    try:
        from . import backtest as B
        from .model import OUT as _O
        _d = B.join(pd.read_parquet(_O / "pred_v3.parquet"), pd.read_parquet(_O / "games.parquet"))
        _d = _d[(_d.game_type == "REG") & _d.home_score.notna() & _d.spread_line.notna()]
        _r = rule_records(_d).set_index("rule").loc["model"]
        rec_txt = f"{_r['2019-22']} on the tuning window and {_r['2023-25']} held out (weeks 1 to 17), and {_r['2015-18']} on the untouched 2015 to 2018 window"
    except Exception:  # noqa
        rec_txt = "on the Backtest tab"
    hdr = [f"# Week {week}, {season}: model picks", "",
           "Our line is home spread / total. Edge = model minus Vegas (spread: positive favours the home side; total: positive favours the over). "
           f"Win, cover and total are the model's chances for each side at the current line (the win and total chances calibrated on the backtest, picks.home_calibration and picks.over_calibration, 27 Sep 2026; the raw p_home stays in the csv, and the totals flag reads the raw p_over_emp there); {100 * break_even():.1f}% is break-even at {DEFAULT_ODDS:+g}.",
           f"Bet flag: spread when the edge is {SPREAD_EDGE:g}+ points. On the current model that cut is {rec_txt}. Totals are not flagged: no total "
           "threshold wins in both windows. No flags in Week 18, where resting starters make the line smarter than the ratings. The full sweep is on the Results tab of the page. "
           "Stake is a quarter of the Kelly fraction from the calibrated cover odds at the book's price, as a share of the bankroll. "
           f"Shadow columns are rules logged and graded but never bet ({'; '.join(lab for _, _, lab in SHADOWS.values())}), to decide the rule on live games.", ""]
    return "\n".join(hdr + [df.to_markdown(index=False), ""])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", type=int, default=2026)
    ap.add_argument("--week", type=int, required=True)
    a = ap.parse_args()
    p = table(a.season, a.week)
    REP.mkdir(exist_ok=True)
    p.to_csv(REP / f"picks_{a.season}_wk{a.week}.csv", index=False)
    log_run(p)
    md = markdown(p, a.season, a.week)
    (REP / f"picks_{a.season}_wk{a.week}.md").write_text(md)
    print(md)
