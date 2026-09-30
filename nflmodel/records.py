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
                      ("Over or under", pc, f"weeks 1 to {LAST_BET_WEEK}", t_ok & wk & (p_side >= bar)),
                      ("Overs (not bet)", pc, "the same bar on the over side", t_ok & wk & over & (p_side >= bar)),
                      ("Our bets: unders", pc, f"weeks 1 to {LAST_BET_WEEK}, the live rule", t_ok & wk & ~over & (p_side >= bar))]}
    seasons = sorted(int(x) for x in d.season.unique())
    out = {"periods": periods, "seasons": seasons, "odds": DEFAULT_ODDS, "break_even": round(break_even(), 4)}
    for mkt, spec in rows.items():
        won, push = (sp_won, sp_push) if mkt == "spread" else (t_won, t_push)
        out[mkt] = [{"row": lab, "group": grp, "what": what, "bet": lab.startswith("Our bets"),
                     "cells": {pr["key"]: _cell(won[m & d.season.between(pr["from"], pr["to"])], push[m & d.season.between(pr["from"], pr["to"])]) for pr in periods},
                     "by_season": {str(y): _cell(won[m & (d.season == y)], push[m & (d.season == y)]) for y in seasons}} for lab, grp, what, m in spec]
    return out
