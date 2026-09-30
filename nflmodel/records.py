"""The Backtest tab's standard records (30 Sep 2026, Matt: one standard record, the same periods everywhere, all games
beside our bets, totals together and over and under apart). Reads the live rules from picks.py and changes none of
them; kept apart from picks.py so the backtests stamped on picks.py's code are not marked stale by a display table."""
from __future__ import annotations
import numpy as np
import pandas as pd
from .picks import DEFAULT_ODDS, LAST_BET_WEEK, SPREAD_EDGE, TOTAL_SHADOW, WINDOWS, WINDOW_LABEL, break_even, rule_mask


def _cell(won: pd.Series, push: pd.Series) -> dict:
    """W-L-P, win % (pushes out), units at DEFAULT_ODDS (a win +1, a loss the price) and ROI on the amount risked."""
    w, l, p = int(won.sum()), int((~won & ~push).sum()), int(push.sum())
    risk = -DEFAULT_ODDS / 100 if DEFAULT_ODDS < 0 else 1.0; win = 1.0 if DEFAULT_ODDS < 0 else DEFAULT_ODDS / 100
    u = w * win - l * risk
    return {"w": w, "l": l, "p": p, "pct": round(w / (w + l), 4) if w + l else None, "units": round(u, 1), "roi": round(u / (risk * (w + l)), 4) if w + l else None}


def standard_records(d: pd.DataFrame, season_now: int) -> dict:
    """The Backtest tab's one standard table (30 Sep 2026, Matt: the same periods for every record, all games beside our
    bets, totals together and over and under apart): regular season, graded at the closing line, pushes shown, one unit
    at DEFAULT_ODDS. Every game = the model's side on every game with a line (the spread: its number against the line;
    the total: its chance, over when p_over_emp >= 0.5); the bets = the live rules (rule_mask), weeks 1 to LAST_BET_WEEK.
    d is the joined backtest table (played regular-season games with a line)."""
    first = int(d.season.min())
    periods = [{"key": k, "from": a, "to": b, "label": WINDOW_LABEL[k]} for k, (a, b) in WINDOWS.items()]
    periods += [{"key": str(season_now), "from": season_now, "to": season_now, "label": "this season"}, {"key": "All", "from": first, "to": season_now, "label": f"{first} to now"}]
    e = d.model_spread - d.spread_line; cm = d.home_score - d.away_score - d.spread_line
    sp_ok = d.spread_line.notna() & (e != 0); sp_won = ((e > 0) & (cm > 0)) | ((e < 0) & (cm < 0)); sp_push = cm == 0
    ct = d.home_score + d.away_score - d.total_line; t_ok = d.total_line.notna() & d.p_over_emp.notna() if "p_over_emp" in d.columns else d.total_line.notna() & False
    over = d.p_over_emp >= 0.5 if "p_over_emp" in d.columns else pd.Series(False, index=d.index)
    t_won = (over & (ct > 0)) | (~over & (ct < 0)); t_push = ct == 0
    p_side = np.where(over, d.p_over_emp, 1 - d.p_over_emp) if "p_over_emp" in d.columns else np.zeros(len(d))
    bar = TOTAL_SHADOW["prob"]; wk = d.week <= LAST_BET_WEEK
    pc = f"{round(100 * bar)}%+ chance"
    rows = {"spread": [("Every game", "", "the model's side against the spread, every game with a line", sp_ok),
                       (f"Our bets: {SPREAD_EDGE:g}+ edge", "", f"weeks 1 to {LAST_BET_WEEK}, the live rule", rule_mask(d, SPREAD_EDGE) & sp_ok)],
            "total": [("Over or under", "Every game", "the model's side of the total (its chance), every game with a line", t_ok),
                      ("Overs", "Every game", "the games it leaned over", t_ok & over), ("Unders", "Every game", "the games it leaned under", t_ok & ~over),
                      ("Our bets: unders", pc, f"weeks 1 to {LAST_BET_WEEK}, the live rule", t_ok & wk & ~over & (p_side >= bar)),
                      ("Overs (not bet)", pc, "the same bar on the over side", t_ok & wk & over & (p_side >= bar)),
                      ("Over or under", pc, f"weeks 1 to {LAST_BET_WEEK}", t_ok & wk & (p_side >= bar))]}
    seasons = sorted(int(x) for x in d.season.unique())
    out = {"periods": periods, "seasons": seasons, "odds": DEFAULT_ODDS, "break_even": round(break_even(), 4)}
    for mkt, spec in rows.items():
        won, push = (sp_won, sp_push) if mkt == "spread" else (t_won, t_push)
        out[mkt] = [{"row": lab, "group": grp, "what": what, "bet": lab.startswith("Our bets"),
                     "cells": {pr["key"]: _cell(won[m & d.season.between(pr["from"], pr["to"])], push[m & d.season.between(pr["from"], pr["to"])]) for pr in periods},
                     "by_season": {str(y): _cell(won[m & (d.season == y)], push[m & (d.season == y)]) for y in seasons}} for lab, grp, what, m in spec]
    return out


def _periods_of(d: pd.DataFrame, season_now: int) -> list:
    first = int(d.season.min())
    return [(k, a, b) for k, (a, b) in WINDOWS.items()] + [(str(season_now), season_now, season_now), ("All", first, season_now)]


def appendix(d: pd.DataFrame, season_now: int) -> dict:
    """The Backtest tab's appendix (30 Sep 2026, Matt: every edge tested by period and season, week by week, us against
    Vegas), all from the joined backtest table d (played regular-season games with a line), the live rules unchanged."""
    per = _periods_of(d, season_now); seasons = sorted(int(x) for x in d.season.unique())
    e = d.model_spread - d.spread_line; cm = d.home_score - d.away_score - d.spread_line
    sp_won = ((e > 0) & (cm > 0)) | ((e < 0) & (cm < 0)); sp_push = cm == 0; sp_ok = d.spread_line.notna() & (e != 0)
    ct = d.home_score + d.away_score - d.total_line; t_ok = d.total_line.notna() & d.p_over_emp.notna()
    over = d.p_over_emp >= 0.5; t_won = (over & (ct > 0)) | (~over & (ct < 0)); t_push = ct == 0
    wk = d.week <= LAST_BET_WEEK
    trees = (d.home_m_trees - d.away_m_trees - d.spread_line) if "home_m_trees" in d.columns else pd.Series(np.nan, index=d.index)
    def block(won, push, m):
        return {"cells": {k: _cell(won[m & d.season.between(a, b)], push[m & d.season.between(a, b)]) for k, a, b in per},
                "by_season": {str(y): _cell(won[m & (d.season == y)], push[m & (d.season == y)]) for y in seasons}}
    # every edge tested: cumulative cutoffs and the other rules on the Bets tab, weeks 1 to LAST_BET_WEEK
    sp_rules = [(f"{c:g}+ points", sp_ok & wk & (e.abs() >= c), c == SPREAD_EDGE) for c in (1, 2, 3, 4, 4.5, 5, 5.5, 6, 7, 8)]
    sp_rules += [(f"{SPREAD_EDGE:g}+, model's side the underdog or pick'em", sp_ok & wk & (e.abs() >= SPREAD_EDGE) & ~((np.sign(e) == np.sign(d.spread_line)) & (d.spread_line != 0)), False),
                 (f"{SPREAD_EDGE:g}+, weeks 1 to 13 only", sp_ok & (d.week <= 13) & (e.abs() >= SPREAD_EDGE), False)]
    tr_won = ((trees > 0) & (cm > 0)) | ((trees < 0) & (cm < 0))
    p_side = np.where(over, d.p_over_emp, 1 - d.p_over_emp)
    t_rules = []
    for pr in (0.52, 0.55, 0.58, 0.60):
        t_rules += [(f"Unders, {round(100 * pr)}%+ chance", t_ok & wk & ~over & (p_side >= pr), pr == TOTAL_SHADOW["prob"]),
                    (f"Overs, {round(100 * pr)}%+ chance", t_ok & wk & over & (p_side >= pr), False)]
    out = {"periods": [{"key": k, "from": a, "to": b} for k, a, b in per], "seasons": seasons,
           "edges": {"spread": [{"row": lab, "bet": bet, **block(sp_won, sp_push, m)} for lab, m, bet in sp_rules] +
                               [{"row": "Boosted trees alone, 5+ points", "bet": False, **block(tr_won, sp_push, sp_ok & wk & (trees.abs() >= 5))}],
                     "total": [{"row": lab, "bet": bet, **block(t_won, t_push, m)} for lab, m, bet in t_rules]}}
    # week by week: our bets' units each week, per season, and the count of winning and losing weeks
    risk = -DEFAULT_ODDS / 100 if DEFAULT_ODDS < 0 else 1.0; win = 1.0 if DEFAULT_ODDS < 0 else DEFAULT_ODDS / 100
    wkly = {}
    for mkt, (won, push, m) in {"spread": (sp_won, sp_push, rule_mask(d, SPREAD_EDGE) & sp_ok),
                                "total": (t_won, t_push, t_ok & wk & ~over & (p_side >= TOTAL_SHADOW["prob"]))}.items():
        x = d[m].assign(u=np.where(won[m], win, np.where(push[m], 0.0, -risk)), w=won[m].astype(int), l=(~won[m] & ~push[m]).astype(int), p=push[m].astype(int))
        g = x.groupby(["season", "week"]).agg(w=("w", "sum"), l=("l", "sum"), p=("p", "sum"), u=("u", "sum")).reset_index()
        rows = []
        for y in seasons:
            gy = g[g.season == y]
            rows.append({"season": int(y), "weeks": {str(int(r.week)): {"w": int(r.w), "l": int(r.l), "p": int(r.p), "u": round(float(r.u), 2)} for r in gy.itertuples()},
                         "up": int((gy.u > 0).sum()), "down": int((gy.u < 0).sum()), "even": int((gy.u == 0).sum()),
                         "best": round(float(gy.u.max()), 2) if len(gy) else None, "worst": round(float(gy.u.min()), 2) if len(gy) else None})
        # the longest runs of straight wins and straight losses, bet by bet in kickoff order (30 Sep 2026, Matt); a push
        # neither extends nor breaks a run
        order = [c for c in ("season", "week", "gameday", "game_id") if c in x.columns]
        best_w = best_l = run_w = run_l = 0
        for w_, l_ in zip(x.sort_values(order).w, x.sort_values(order).l):
            if w_: run_w, run_l = run_w + 1, 0
            elif l_: run_w, run_l = 0, run_l + 1
            best_w, best_l = max(best_w, run_w), max(best_l, run_l)
        wkly[mkt] = {"rows": rows, "last_week": LAST_BET_WEEK, "up": int((g.u > 0).sum()), "down": int((g.u < 0).sum()), "even": int((g.u == 0).sum()),
                     "streak_win": int(best_w), "streak_loss": int(best_l),
                     # each week of the season across the seasons that had a bet that week (30 Sep 2026, Matt: "an average per week
                     # so we see the best performing week"): its record, units and units a season
                     "by_week": {str(int(wk_)): {"w": int(gw.w.sum()), "l": int(gw.l.sum()), "p": int(gw.p.sum()), "units": round(float(gw.u.sum()), 2),
                                                 "seasons": int(len(gw)), "avg": round(float(gw.u.mean()), 2)} for wk_, gw in g.groupby("week")}}
    out["weekly"] = wkly
    # us against Vegas, every game: the straight-up winner, the miss of the margin and the total, how often our number
    # landed closer to the final than the closing line, and how far it sat from the line
    fav_m = np.sign(d.model_spread); fav_v = np.sign(d.spread_line); res = np.sign(d.home_score - d.away_score)
    mar = d.home_score - d.away_score; tot = d.home_score + d.away_score
    def vs(x):
        ok = x.spread_line.notna(); su = ok & (res[x.index] != 0)
        mm, vm = (x.model_spread - (x.home_score - x.away_score)).abs(), (x.spread_line - (x.home_score - x.away_score)).abs()
        tt = x.total_line.notna(); mt, vt = (x.model_total - (x.home_score + x.away_score)).abs(), (x.total_line - (x.home_score + x.away_score)).abs()
        cl = ok & (mm != vm); clt = tt & (mt != vt)
        return {"games": int(ok.sum()),
                "su_model": round(float((fav_m[x.index] == res[x.index])[su & (fav_m[x.index] != 0)].mean()), 4) if su.any() else None,
                "su_vegas": round(float((fav_v[x.index] == res[x.index])[su & (fav_v[x.index] != 0)].mean()), 4) if su.any() else None,
                "margin_model": round(float(mm[ok].mean()), 2), "margin_line": round(float(vm[ok].mean()), 2),
                "closer_margin": round(float((mm < vm)[cl].mean()), 4) if cl.any() else None,
                "total_model": round(float(mt[tt].mean()), 2) if tt.any() else None, "total_line": round(float(vt[tt].mean()), 2) if tt.any() else None,
                "closer_total": round(float((mt < vt)[clt].mean()), 4) if clt.any() else None,
                "gap_spread": round(float((x.model_spread - x.spread_line)[ok].abs().mean()), 2), "gap_total": round(float((x.model_total - x.total_line)[tt].abs().mean()), 2) if tt.any() else None}
    out["vegas"] = {"cells": {k: vs(d[d.season.between(a, b)]) for k, a, b in per}, "by_season": {str(y): vs(d[d.season == y]) for y in seasons}}
    # how far our number sat from the line, and how our side did at each distance (every game, weeks 1 to LAST_BET_WEEK)
    bands = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7), (7, 99)]
    te = d.model_total - d.total_line
    out["gap_bands"] = {"spread": [{"band": f"{a}+" if b == 99 else f"{a}–{b}", "from": a, **_cell(sp_won[sp_ok & wk & e.abs().between(a, b, inclusive="left")], sp_push[sp_ok & wk & e.abs().between(a, b, inclusive="left")])} for a, b in bands],
                        "total": [{"band": f"{a}+" if b == 99 else f"{a}–{b}", "from": a, **_cell(t_won[t_ok & wk & te.abs().between(a, b, inclusive="left")], t_push[t_ok & wk & te.abs().between(a, b, inclusive="left")])} for a, b in bands]}
    return out
