"""Bet rules sweep (30 Sep 2026, Matt: "Did all the thresholds and timing of weeks, kinds of games, kind of bet, favorite vs
not favorites and sizing of thresholds get tested? Test a bunch of these ... report back all these new tested ideas and the
outcomes"). Research only: nothing here feeds the site or the picks.

Data: the walk-forward backtest table the site grades (backtest.join(pred_v3, games)), regular season, played, with a closing
line. Every spread rule bets the model's side (model_spread - spread_line), graded at the closing line at -110 (a win +1, a
loss -1.1), pushes out. Totals rules bet the under or the over at the closing total the same way. Moneylines are graded at
nflverse's closing moneyline, one unit risked a bet.

Windows: 2015-18 (never used for any choice), 2019-22 (where the 4-point cut was chosen), 2023-25 (held out), 2015-25 pooled,
and 2026 to date shown apart.

Families (column `family`): thresholds, timing, kinds of game, favourite/dog, bet type, sizing, line timing (openers 2015-21).

Honesty checks, per rule (columns on every row of the rule):
  vs_live_*     better than the live rule (4+ spread flag, or the 55% unders rule) on every one of the three windows,
                in units and in win % (ROI for moneylines)
  placebo_p     the rule's selection shuffled within season inside its parent pool (the live flag for a filter of the
                flag; every game the model has a side on, for a new threshold), 200 draws, 2015-25 pooled: the share of
                random subsets of the same size per season whose units are at least the rule's
Writes reports/bet_rules_sweep.csv (one row per rule x window), reports/bet_rules_sweep.md, and two side tables:
reports/bet_rules_sweep_kelly.csv (bankroll paths by staking) and reports/bet_rules_sweep_clv.csv (line moves after the opener).

Usage: python experiments/bet_rules_sweep.py
"""
from __future__ import annotations
import sys
import numpy as np, pandas as pd
from pathlib import Path
from scipy.stats import binom
from sklearn.linear_model import LogisticRegression

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from nflmodel import backtest as B, picks as P   # noqa: E402

OUT, REP = ROOT / "data" / "processed", ROOT / "reports"
BE = 110 / 210                      # break-even at -110
WIN, RISK = 1.0, 1.1                # -110: a win +1, a loss -1.1
LIVE_EDGE, LIVE_LAST = P.SPREAD_EDGE, P.LAST_BET_WEEK
UNDER_P = P.TOTAL_SHADOW["prob"]
WINDOWS = {"2015-18": (2015, 2018), "2019-22": (2019, 2022), "2023-25": (2023, 2025), "2015-25": (2015, 2025), "2026": (2026, 2026)}
MAIN3 = ["2015-18", "2019-22", "2023-25"]
OPEN_WINDOWS = {"2015-18": (2015, 2018), "2019-21": (2019, 2021), "2015-21": (2015, 2021)}
N_PLACEBO, SEED = 200, 7
MIN_BETS = 40                       # a rule needs about this many bets in each window before it can be recommended


# ---------------------------------------------------------------------------------------------------------------- data
def load() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    g = pd.read_parquet(OUT / "games.parquet"); p = pd.read_parquet(OUT / "pred_v3.parquet")
    d = B.join(p, g)
    d = d[(d.game_type == "REG") & d.home_score.notna() & d.spread_line.notna()].copy()
    extra = g.set_index("game_id")[["primetime", "slot", "roof", "div_game", "home_rest", "away_rest", "weekday", "location"]]
    for c in extra.columns:
        d[c] = d.game_id.map(extra[c])
    d = d.sort_values(["season", "week", "game_id"]).reset_index(drop=True)

    # spreads: the model's side
    d["edge"] = d.model_spread - d.spread_line
    d["ae"] = d.edge.abs()
    d["home_side"] = d.edge > 0
    cm = d.home_score - d.away_score - d.spread_line
    d["sp_push"] = cm == 0
    d["sp_won"] = ((d.edge > 0) & (cm > 0)) | ((d.edge < 0) & (cm < 0))
    d["sp_ok"] = d.edge != 0
    d["sp_u"] = np.where(d.sp_push, 0.0, np.where(d.sp_won, WIN, -RISK))
    sl = d.spread_line
    d["pickem"] = sl == 0
    d["fav"] = ((d.edge > 0) & (sl > 0)) | ((d.edge < 0) & (sl < 0))      # our side lays points
    d["dog"] = ((d.edge > 0) & (sl < 0)) | ((d.edge < 0) & (sl > 0))      # our side gets points
    d["our_rest"] = np.where(d.home_side, d.home_rest, d.away_rest); d["opp_rest"] = np.where(d.home_side, d.away_rest, d.home_rest)
    lo_, hi_ = np.minimum(sl, d.model_spread), np.maximum(sl, d.model_spread)
    d["home_u"] = np.where(d.sp_push, 0.0, np.where(cm > 0, WIN, -RISK)); d["home_won"] = cm > 0
    d["away_u"] = np.where(d.sp_push, 0.0, np.where(cm < 0, WIN, -RISK)); d["away_won"] = cm < 0
    d["all_ok"] = pd.Series(True, index=d.index)
    d["cross3"] = ((lo_ < 3) & (hi_ > 3)) | ((lo_ < -3) & (hi_ > -3))
    d["cross7"] = ((lo_ < 7) & (hi_ > 7)) | ((lo_ < -7) & (hi_ > -7))

    # totals
    d["p_under"] = 1 - d.p_over_emp
    d["tedge"] = d.model_total - d.total_line
    ct = d.home_score + d.away_score - d.total_line
    d["t_push"] = ct == 0
    d["un_u"] = np.where(d.t_push, 0.0, np.where(ct < 0, WIN, -RISK)); d["un_won"] = ct < 0
    d["ov_u"] = np.where(d.t_push, 0.0, np.where(ct > 0, WIN, -RISK)); d["ov_won"] = ct > 0
    d["t_ok"] = d.total_line.notna()

    # moneyline on the model's spread side, and the model's win chance against the vig-free book
    def payout(o):
        o = np.asarray(o, float); return np.where(o < 0, 100 / np.abs(o), o / 100)
    d["ml_odds"] = np.where(d.home_side, d.home_moneyline, d.away_moneyline).astype(float)
    tie = d.home_score == d.away_score
    hw = d.home_score > d.away_score
    side_won = np.where(d.home_side, hw, (d.away_score > d.home_score))
    d["ml_push"] = tie
    d["ml_won"] = side_won & ~tie
    d["ml_u"] = np.where(tie, 0.0, np.where(side_won, payout(d.ml_odds.fillna(-110)), -1.0))
    d["ml_ok"] = d.home_moneyline.notna() & d.away_moneyline.notna()
    ih, ia = 1 / (1 + payout(d.home_moneyline.fillna(-110))), 1 / (1 + payout(d.away_moneyline.fillna(-110)))
    d["book_h"] = ih / (ih + ia)
    hc = P.home_calibrations(p, g)
    d["p_home_cal"] = [P.home_cal_p(hc[int(s)], ph) for s, ph in zip(d.season, d.p_home)]
    for tag, col in (("cal", "p_home_cal"), ("raw", "p_home")):
        eh = d[col] - d.book_h
        d[f"wc_edge_{tag}"] = eh.abs(); d[f"wc_home_{tag}"] = eh > 0
        won_h = hw & ~tie; won_a = (d.away_score > d.home_score)
        w_ = np.where(eh > 0, won_h, won_a)
        od = np.where(eh > 0, d.home_moneyline, d.away_moneyline).astype(float)
        d[f"wc_u_{tag}"] = np.where(tie, 0.0, np.where(w_, payout(np.nan_to_num(od, nan=-110)), -1.0))
        d[f"wc_won_{tag}"] = w_ & ~tie
        d[f"wc_dog_{tag}"] = od > 0

    # walk-forward calibrated cover chance (picks.calibration's form, |edge| capped at 7, seasons before, from 2015)
    d["p_cover"] = np.nan
    for s in sorted(d.season.unique()):
        tr = d[(d.season < s) & d.sp_ok & ~d.sp_push]
        if len(tr) < 200:
            continue
        m = LogisticRegression(C=10.0).fit(np.minimum(tr.ae.values, P.CAL_CAP)[:, None], tr.sp_won.astype(int).values)
        idx = d.season == s
        d.loc[idx, "p_cover"] = m.predict_proba(np.minimum(d.loc[idx, "ae"].values, P.CAL_CAP)[:, None])[:, 1]
    oc = P.over_calibrations(p, g)
    d["p_under_cal"] = [1 - P.over_cal_p(oc[int(s)], po) if oc[int(s)][2] >= P.OVER_CAL_MIN_N else np.nan for s, po in zip(d.season, d.p_over_emp)]
    return d, g, p


# ------------------------------------------------------------------------------------------------------------- grading
ROWS: list[dict] = []
RULES: dict[str, dict] = {}


def _cell(x: pd.DataFrame, won, push, units, stake, risk_unit) -> dict:
    w = int((won & ~push).sum()); p_ = int(push.sum()); l = int((~won & ~push).sum()); n = w + l
    u = float((units * stake).sum()); risked = float((stake * risk_unit)[~push].sum())
    s_units = (units * stake).groupby(x.season).sum()
    return {"bets": n, "w": w, "l": l, "p": p_, "win_pct": round(w / n, 4) if n else np.nan, "units": round(u, 2),
            "roi": round(u / risked, 4) if risked else np.nan, "staked": round(risked, 2),
            "seasons_up": int((s_units > 0).sum()), "seasons_with_bets": int(len(s_units)),
            "p_luck": round(float(binom.sf(w - 1, n, BE)), 4) if n else np.nan}


def add(family: str, rule: str, mask: pd.Series, market: str = "spread", stake: pd.Series | None = None, parent: pd.Series | None = None,
        compare: str | None = "auto", note: str = "", d: pd.DataFrame | None = None, windows: dict = WINDOWS, key: str | None = None):
    """Grade one rule on every window. market: spread / under / over / ml / wc_cal / wc_raw. parent: the pool the placebo draws from."""
    d = D if d is None else d
    col = {"spread": ("sp_won", "sp_push", "sp_u", "sp_ok", RISK), "under": ("un_won", "t_push", "un_u", "t_ok", RISK),
           "over": ("ov_won", "t_push", "ov_u", "t_ok", RISK), "ml": ("ml_won", "ml_push", "ml_u", "ml_ok", 1.0),
           "wc_cal": ("wc_won_cal", "ml_push", "wc_u_cal", "ml_ok", 1.0), "wc_raw": ("wc_won_raw", "ml_push", "wc_u_raw", "ml_ok", 1.0),
           "home": ("home_won", "sp_push", "home_u", "all_ok", RISK), "away": ("away_won", "sp_push", "away_u", "all_ok", RISK)}[market]
    won_c, push_c, u_c, ok_c, ru = col
    m = mask.fillna(False).astype(bool) & d[ok_c]
    st = pd.Series(1.0, index=d.index) if stake is None else stake.fillna(0.0)
    if compare == "auto":
        compare = {"spread": "live_spread", "under": "live_under", "over": "live_under", "ml": "live_spread", "wc_cal": "live_spread", "wc_raw": "live_spread",
                   "home": "live_spread", "away": "live_spread"}[market]
    key = key or f"{family}|{rule}"
    RULES[key] = {"family": family, "rule": rule, "market": market, "mask": m, "parent": None if parent is None else (parent.fillna(False).astype(bool) & d[ok_c]),
                  "u": d[u_c] * st, "compare": compare, "note": note, "cells": {}, "d": d, "stake": stake is not None}
    for w, (a, b) in windows.items():
        sel = m & d.season.between(a, b); x = d[sel]
        c = _cell(x, d.loc[sel, won_c].astype(bool), d.loc[sel, push_c].astype(bool), d.loc[sel, u_c], st[sel], ru)
        if market in ("ml", "wc_cal", "wc_raw") and c["bets"]:
            c["p_luck"] = ml_luck(d[sel], market, c["units"])
        RULES[key]["cells"][w] = c
        ROWS.append({"family": family, "rule": rule, "market": market, "window": w, **c, "note": note, "key": key})


def ml_luck(x: pd.DataFrame, market: str, units: float, n: int = 4000) -> float:
    """The chance of units at least this large if every moneyline bet won at the vig-free book chance of its side (the
    moneyline's equivalent of the binomial against break-even; prices differ bet to bet, so a flat 52.4% does not apply)."""
    rng = np.random.default_rng(11)
    home = x.home_side if market == "ml" else x[f"wc_home_{market[3:]}"]
    ph = np.where(home, x.book_h, 1 - x.book_h)
    od = np.where(home, x.home_moneyline, x.away_moneyline).astype(float)
    pay = np.where(od < 0, 100 / np.abs(od), od / 100)
    keep = ~(x.home_score == x.away_score).values
    ph, pay = ph[keep], pay[keep]
    sim = np.where(rng.random((n, len(ph))) < ph, pay, -1.0).sum(axis=1)
    return round(float((sim >= units - 1e-9).mean()), 4)


# ------------------------------------------------------------------------------------------------------------ the rules
def spread_rules(d: pd.DataFrame):
    wk17 = d.week <= LIVE_LAST
    flag = (d.ae >= LIVE_EDGE) & wk17
    allside17 = d.sp_ok & wk17
    all18 = d.sp_ok
    flag18 = d.ae >= LIVE_EDGE
    add("live", "LIVE: spread 4+ edge, weeks 1-17", flag, compare=None, parent=allside17, key="live_spread")

    # 1 thresholds
    for t in np.arange(2.0, 8.01, 0.5):
        if t == LIVE_EDGE:
            continue
        add("thresholds", f"spread {t:g}+ edge", (d.ae >= t) & wk17, parent=allside17 if t < LIVE_EDGE else flag)
    for a, b in [(0, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 99), (4, 6)]:
        lab = f"spread edge band {a}-{b}" if b < 99 else f"spread edge band {a}+"
        add("thresholds", lab, (d.ae >= a) & (d.ae < b) & wk17, parent=allside17 if a < LIVE_EDGE else flag)

    # 2 timing
    for a, b in [(1, 4), (5, 8), (9, 13), (14, 17), (18, 18)]:
        add("timing", f"4+ edge, weeks {a}-{b}", flag18 & d.week.between(a, b), parent=flag18)
    for L in range(10, 19):
        if L == LIVE_LAST:
            continue
        add("timing", f"4+ edge, last bet week {L}", flag18 & (d.week <= L), parent=flag18 if L > LIVE_LAST else flag)
    add("timing", "4+ edge, skip weeks 1-2", flag & (d.week >= 3), parent=flag)
    add("timing", "4+ edge, skip weeks 1-3", flag & (d.week >= 4), parent=flag)
    for te in (5.0, 6.0):
        m = wk17 & np.where(d.week <= 3, d.ae >= te, d.ae >= LIVE_EDGE)
        add("timing", f"weeks 1-3 need {te:g}+, else 4+", pd.Series(m, index=d.index), parent=flag)
    add("timing", "4+ edge, weeks 1-13 (the early shadow)", flag & (d.week <= 13), parent=flag)

    # 3 kinds of game (filters of the live flag, each with its complement)
    dome = d.roof.isin(["dome", "closed"])
    kinds = [
        ("division game", d.div_game == 1), ("non-division game", d.div_game == 0),
        ("primetime", d.primetime.astype(bool)), ("not primetime", ~d.primetime.astype(bool)),
        ("Thursday night", d.slot == "TNF"), ("Sunday night", d.slot == "SNF"), ("Monday night", d.slot == "MNF"),
        ("Sunday early (1pm ET)", d.slot == "SUN_EARLY"), ("Sunday late (4pm ET)", d.slot == "SUN_LATE"),
        ("dome or closed roof", dome), ("outdoor or open roof", ~dome),
        ("a team on short rest (<=5 days)", np.minimum(d.home_rest, d.away_rest) <= 5), ("no team on short rest", np.minimum(d.home_rest, d.away_rest) > 5),
        ("our side off a bye (rest >= 12)", d.our_rest >= 12), ("opponent off a bye", d.opp_rest >= 12),
        ("our side 3+ more days rest", (d.our_rest - d.opp_rest) >= 3), ("our side 3+ fewer days rest", (d.our_rest - d.opp_rest) <= -3),
        ("equal rest", d.our_rest == d.opp_rest),
        ("our side at home", d.home_side), ("our side away", ~d.home_side),
        ("big line |line| >= 7", d.spread_line.abs() >= 7), ("small line |line| < 7", d.spread_line.abs() < 7), ("line within 3 (|line| <= 3)", d.spread_line.abs() <= 3),
        ("line on 3 exactly", d.spread_line.abs() == 3), ("line on 7 exactly", d.spread_line.abs() == 7),
        ("our number crosses 3", d.cross3), ("our number crosses 7", d.cross7), ("crosses 3 or 7", d.cross3 | d.cross7), ("crosses neither 3 nor 7", ~(d.cross3 | d.cross7)),
        ("high total (>= 47)", d.total_line >= 47), ("low total (<= 40)", d.total_line <= 40), ("mid total (40.5-46.5)", d.total_line.between(40.5, 46.5)),
    ]
    for lab, k in kinds:
        add("kinds of game", f"4+ edge, {lab}", flag & pd.Series(k, index=d.index).astype(bool), parent=flag)

    # 4 favourite / underdog, at the 4+ edge and across edges
    sides = [("our side the favourite", d.fav), ("our side the underdog", d.dog), ("pick'em", d.pickem), ("underdog or pick'em (the dog shadow)", d.dog | d.pickem),
             ("home dog", d.dog & d.home_side), ("road dog", d.dog & ~d.home_side), ("home favourite", d.fav & d.home_side), ("road favourite", d.fav & ~d.home_side)]
    for t in (3.0, 4.0, 5.0, 6.0):
        base = (d.ae >= t) & wk17
        for lab, k in sides:
            add("favourite/dog", f"{t:g}+ edge, {lab}", base & k, parent=base)
    for a, b in [(0, 2), (2, 4), (4, 6), (6, 99)]:
        base = (d.ae >= a) & (d.ae < b) & wk17
        for lab, k in sides[:2]:
            add("favourite/dog", f"edge band {a}-{b if b < 99 else '+'}, {lab}", base & k, parent=base)

    # the market's own angles, no model: is a filter above the model's skill or a known market lean?
    rd, hd = d.spread_line > 0, d.spread_line < 0          # the away side is the dog / the home side is the dog
    add("favourite/dog", "BLIND: every road dog ATS (no model), weeks 1-17", rd & wk17, market="away", parent=None)
    add("favourite/dog", "BLIND: every home dog ATS (no model), weeks 1-17", hd & wk17, market="home", parent=None)
    add("favourite/dog", "BLIND: every road dog getting 3.5+ (no model), weeks 1-17", (d.spread_line >= 3.5) & wk17, market="away", parent=None)
    add("favourite/dog", "model's side a road dog, any edge, weeks 1-17", d.dog & ~d.home_side & wk17, parent=allside17)
    add("favourite/dog", "model's side a road dog, edge under 4, weeks 1-17", d.dog & ~d.home_side & wk17 & (d.ae < LIVE_EDGE), parent=allside17)
    add("kinds of game", "BLIND: every away side ATS (no model), weeks 1-17", wk17, market="away", parent=None)

    # 5 bet type: the moneyline on the same side as the spread flag, and win-chance value against the vig-free moneyline
    for t in (3.0, 4.0, 5.0, 6.0):
        base = (d.ae >= t) & wk17
        add("bet type", f"moneyline on the {t:g}+ spread side", base, market="ml", parent=None)
        if t == 4.0:
            add("bet type", "moneyline on the 4+ spread side, our side the dog", base & d.dog, market="ml")
            add("bet type", "moneyline on the 4+ spread side, our side the favourite", base & d.fav, market="ml")
            add("bet type", "moneyline on the 4+ spread side, price -200 or better", base & (d.ml_odds >= -200), market="ml")
    for tag in ("cal", "raw"):
        for t in (0.03, 0.05, 0.08, 0.10):
            base = (d[f"wc_edge_{tag}"] >= t) & wk17
            add("bet type", f"moneyline, model win chance ({tag}) beats no-vig book by {t:.0%}", base, market=f"wc_{tag}")
            if tag == "cal":
                add("bet type", f"moneyline, win chance ({tag}) beats book by {t:.0%}, dogs only", base & d[f"wc_dog_{tag}"], market=f"wc_{tag}")
                add("bet type", f"moneyline, win chance ({tag}) beats book by {t:.0%}, favourites only", base & ~d[f"wc_dog_{tag}"], market=f"wc_{tag}")


def total_rules(d: pd.DataFrame):
    wk17 = d.week <= LIVE_LAST
    und = (d.p_under >= UNDER_P) & wk17
    und18 = d.p_under >= UNDER_P
    all_t17 = d.t_ok & wk17
    add("live", "LIVE: under at 55%+ chance, weeks 1-17", und, market="under", compare=None, parent=all_t17, key="live_under")
    for c in range(52, 63):
        if c == 55:
            continue
        add("thresholds", f"under at {c}%+ chance", (d.p_under >= c / 100) & wk17, market="under", parent=all_t17 if c < 55 else und)
    for a, b in [(0.50, 0.53), (0.53, 0.55), (0.55, 0.57), (0.57, 0.59), (0.59, 1.0)]:
        add("thresholds", f"under chance band {a:.0%}-{b:.0%}" if b < 1 else f"under chance band {a:.0%}+", (d.p_under >= a) & (d.p_under < b) & wk17, market="under",
            parent=all_t17 if a < 0.55 else und)
    for c in range(52, 63):
        add("thresholds", f"over at {c}%+ chance", ((1 - d.p_under) >= c / 100) & wk17, market="over", parent=all_t17)
    for t in range(1, 9):
        add("thresholds", f"under at a {t}+ point total edge", (d.tedge <= -t) & wk17, market="under", parent=all_t17)
        add("thresholds", f"over at a {t}+ point total edge", (d.tedge >= t) & wk17, market="over", parent=all_t17)
    add("bet type", "every under (blind, weeks 1-17)", all_t17, market="under", parent=all_t17)
    add("bet type", "every over (blind, weeks 1-17)", all_t17, market="over", parent=all_t17)

    # timing
    for a, b in [(1, 4), (5, 8), (9, 13), (14, 17), (18, 18)]:
        add("timing", f"under 55%+, weeks {a}-{b}", und18 & d.week.between(a, b), market="under", parent=und18)
    for L in range(10, 19):
        if L == LIVE_LAST:
            continue
        add("timing", f"under 55%+, last bet week {L}", und18 & (d.week <= L), market="under", parent=und18 if L > LIVE_LAST else und)
    add("timing", "under 55%+, skip weeks 1-2", und & (d.week >= 3), market="under", parent=und)
    add("timing", "under 55%+, skip weeks 1-3", und & (d.week >= 4), market="under", parent=und)
    for c in (0.57, 0.59):
        m = wk17 & np.where(d.week <= 3, d.p_under >= c, d.p_under >= UNDER_P)
        add("timing", f"under: weeks 1-3 need {c:.0%}+, else 55%+", pd.Series(m, index=d.index), market="under", parent=und)

    # kinds of game
    dome = d.roof.isin(["dome", "closed"])
    kinds = [("division game", d.div_game == 1), ("non-division game", d.div_game == 0),
             ("primetime", d.primetime.astype(bool)), ("not primetime", ~d.primetime.astype(bool)),
             ("dome or closed roof", dome), ("outdoor or open roof", ~dome),
             ("a team on short rest (<=5 days)", np.minimum(d.home_rest, d.away_rest) <= 5), ("a team off a bye", np.maximum(d.home_rest, d.away_rest) >= 12),
             ("high total (>= 47)", d.total_line >= 47), ("low total (<= 40)", d.total_line <= 40), ("mid total (40.5-46.5)", d.total_line.between(40.5, 46.5)),
             ("big line |line| >= 7", d.spread_line.abs() >= 7), ("small line |line| < 7", d.spread_line.abs() < 7),
             ("wind 15+ mph outdoors", (~dome) & (d.game_id.map(G.set_index("game_id").wind) >= 15))]
    add("kinds of game", "BLIND: every primetime under (no model), weeks 1-17", d.primetime.astype(bool) & all_t17, market="under", parent=None)
    add("kinds of game", "BLIND: every non-primetime under (no model), weeks 1-17", ~d.primetime.astype(bool) & all_t17, market="under", parent=None)
    add("timing", "BLIND: every under in weeks 9-13 (no model)", d.week.between(9, 13) & d.t_ok, market="under", parent=None)
    for lab, k in kinds:
        add("kinds of game", f"under 55%+, {lab}", und & pd.Series(k, index=d.index).astype(bool), market="under", parent=und)


# -------------------------------------------------------------------------------------------------------------- sizing
def sizing(d: pd.DataFrame):
    wk17 = d.week <= LIVE_LAST
    flag = (d.ae >= LIVE_EDGE) & wk17
    tier = pd.Series(np.select([d.ae >= 6, d.ae >= 5, d.ae >= 4], [2.0, 1.5, 1.0], 0.0), index=d.index)
    lin = (d.ae / 4).clip(upper=2.0)
    add("sizing", "4+ flag, tiered stakes (1u 4-5, 1.5u 5-6, 2u 6+)", flag, stake=tier, parent=None)
    add("sizing", "4+ flag, linear stakes (edge/4 units, capped at 2u)", flag, stake=lin, parent=None)
    add("sizing", "4+ flag, inverse tiers (2u 4-5, 1.5u 5-6, 1u 6+)", flag, stake=pd.Series(np.select([d.ae >= 6, d.ae >= 5, d.ae >= 4], [1.0, 1.5, 2.0], 0.0), index=d.index), parent=None)
    und = (d.p_under >= UNDER_P) & wk17
    ut = pd.Series(np.select([d.p_under >= 0.59, d.p_under >= 0.57, d.p_under >= 0.55], [2.0, 1.5, 1.0], 0.0), index=d.index)
    add("sizing", "under 55%+, tiered stakes (1u 55-57%, 1.5u 57-59%, 2u 59%+)", und, market="under", stake=ut, parent=None)
    add("sizing", "under 55%+, linear stakes (1u + (chance-55%)/4%, capped 2u)", und, market="under", stake=(1 + (d.p_under - 0.55) / 0.04).clip(upper=2.0), parent=None)


def kelly_paths(d: pd.DataFrame) -> pd.DataFrame:
    """Bankroll 100 at the start of each window; each week's bets sized from the bankroll at the start of the week; flat =
    1 unit (1% of the starting 100) a bet. Kelly from the walk-forward calibrated chance of the side at -110."""
    wk17 = d.week <= LIVE_LAST
    specs = {"spread 4+ flag": ((d.ae >= LIVE_EDGE) & wk17 & d.sp_ok & d.p_cover.notna(), "p_cover", "sp_won", "sp_push"),
             "under 55%+": ((d.p_under >= UNDER_P) & wk17 & d.t_ok & d.p_under_cal.notna(), "p_under_cal", "un_won", "t_push")}
    out = []
    for lab, (m, pc, wc, pu) in specs.items():
        for w, (a, b) in {"2016-18": (2016, 2018), "2019-22": (2019, 2022), "2023-25": (2023, 2025), "2016-25": (2016, 2025), "2026": (2026, 2026)}.items():
            x = d[m & d.season.between(a, b)]
            for name, frac in {"flat 1u": None, "quarter Kelly": 0.25, "half Kelly": 0.5}.items():
                bank = peak = 100.0; dd = 0.0; stakes = []
                for _, gw in x.groupby(["season", "week"], sort=True):
                    start = bank
                    for r in gw.itertuples():
                        st = 1.0 if frac is None else start * P.kelly_stake(getattr(r, pc), -110.0, frac) / 100.0
                        if getattr(r, pu):
                            continue
                        stakes.append(st)
                        bank += st * (100 / 110) if getattr(r, wc) else -st
                        peak = max(peak, bank); dd = max(dd, (peak - bank) / peak * 100)
                n = int((~x[pu]).sum()); wv = int((x[wc] & ~x[pu]).sum())
                out.append({"rule": lab, "window": w, "staking": name, "bets": n, "record": f"{wv}-{n - wv}", "final_bankroll": round(bank, 1),
                            "growth_pct": round(bank - 100, 1), "max_drawdown_pct": round(dd, 1), "mean_stake_pct": round(float(np.mean(stakes)), 2) if stakes else np.nan,
                            "mean_chance_said": round(float(x[pc].mean()), 4) if len(x) else np.nan})
    return pd.DataFrame(out)


# ------------------------------------------------------------------------------------------------------- line timing
def line_timing(d: pd.DataFrame) -> pd.DataFrame:
    """2015-21: the rule on the model against the opening line. The model's number is the pre-kickoff one (Sunday's injuries
    and weather), so 'full model at the opener' flatters the early bet; the Tuesday model (pred_tuesday.parquet, the same fits
    with the injury and weather inputs at zero, built by nflmodel/opener_study.py) is the fairer early number."""
    o = pd.read_csv(ROOT / "data" / "archive" / "openers_2015_2021.csv").drop(columns=["season", "week"]).set_index("game_id")
    x = d[d.game_id.isin(o.index)].copy()
    for c in ("open_spread", "open_total", "close_spread"):
        x[c] = x.game_id.map(o[c])
    x["close_total_arch"] = x.game_id.map(o.close_total)
    bad = (((x.close_spread - x.spread_line).abs() > 2) | ((x.close_total_arch - x.total_line).abs() > 3) | (x.open_total < 25) | (x.close_total_arch < 25)
           | ((x.open_spread == 0) & (x.spread_line.abs() >= 7)) | ((x.open_spread - x.spread_line).abs() > 10) & (np.sign(x.open_spread) != np.sign(x.spread_line)))
    tue = pd.read_parquet(OUT / "pred_tuesday.parquet").set_index("game_id")
    # what the dropped rows would have added to the opener study's Tuesday record (4+ vs the opener, graded there, 2019-21, every week)
    xb = x[bad & x.season.between(2019, 2021)]; eb = xb.game_id.map(tue.model_spread) - xb.open_spread; cb = xb.home_score - xb.away_score - xb.open_spread
    sb = (eb.abs() >= LIVE_EDGE) & (cb != 0)
    bad_rec = f"{int((sb & (np.sign(eb) == np.sign(cb))).sum())}-{int((sb & (np.sign(eb) != np.sign(cb))).sum())}"
    x = x[~bad & x.open_spread.notna()].copy()
    x["tue_spread"] = x.game_id.map(tue.model_spread); x["tue_total"] = x.game_id.map(tue.model_total)
    margin = x.home_score - x.away_score; tot = x.home_score + x.away_score
    notes = {"dropped_suspect_openers": int(bad.sum()), "games": int(len(x)), "dropped_rows_tuesday_4plus_2019_21": bad_rec}

    def graded(side_home, line):
        cm_ = margin - line
        push = cm_ == 0; won = (side_home & (cm_ > 0)) | (~side_home & (cm_ < 0))
        return won, push

    wk17 = x.week <= LIVE_LAST
    out_rows = []
    for model_lab, ms in (("full model", x.model_spread), ("Tuesday model", x.tue_spread)):
        for t in (3.0, 4.0, 5.0):
            e_open = ms - x.open_spread; e_close = ms - x.spread_line
            for sel_lab, e in (("vs opener", e_open), ("vs close", e_close)):
                m = (e.abs() >= t) & wk17 & (e != 0)
                side_home = e > 0
                for grade_lab, line in (("graded at opener", x.open_spread), ("graded at close", x.spread_line)):
                    if sel_lab == "vs close" and grade_lab == "graded at opener":
                        continue
                    won, push = graded(side_home, line)
                    mv = np.sign(x.spread_line - x.open_spread)            # +: the close moved toward the home side
                    toward = (mv != 0) & (np.sign(e) == mv); away = (mv != 0) & (np.sign(e) == -mv); still = mv == 0
                    rule = f"{model_lab}, {t:g}+ edge {sel_lab}, {grade_lab}"
                    for sub_lab, sub in (("all", m), ("close moved toward our side", m & toward), ("close moved away", m & away), ("close did not move", m & still)):
                        if sub_lab != "all" and not (sel_lab == "vs opener"):
                            continue
                        for w, (a, b) in OPEN_WINDOWS.items():
                            s_ = sub & x.season.between(a, b)
                            c = _cell(x[s_], won[s_], push[s_], pd.Series(np.where(push[s_], 0.0, np.where(won[s_], WIN, -RISK)), index=x[s_].index), pd.Series(1.0, index=x[s_].index), RISK)
                            base_n = int((m & x.season.between(a, b)).sum())
                            out_rows.append({"family": "line timing", "rule": rule if sub_lab == "all" else f"{rule}, {sub_lab}", "market": "spread", "window": w, **c,
                                             "note": (f"share of the rule's bets: {int(s_.sum()) / base_n:.0%}" if sub_lab != "all" and base_n else ""), "key": f"lt|{rule}|{sub_lab}"})
    # totals: unders at a point edge against the opener
    for model_lab, mt in (("full model", x.model_total), ("Tuesday model", x.tue_total)):
        for t in (3.0,):
            for sel_lab, line_sel in (("vs opener", x.open_total), ("vs close", x.total_line)):
                m = ((mt - line_sel) <= -t) & wk17
                for grade_lab, line in (("graded at opener", x.open_total), ("graded at close", x.total_line)):
                    if sel_lab == "vs close" and grade_lab == "graded at opener":
                        continue
                    ct_ = tot - line; push = ct_ == 0; won = ct_ < 0
                    for w, (a, b) in OPEN_WINDOWS.items():
                        s_ = m & x.season.between(a, b)
                        c = _cell(x[s_], won[s_], push[s_], pd.Series(np.where(push[s_], 0.0, np.where(won[s_], WIN, -RISK)), index=x[s_].index), pd.Series(1.0, index=x[s_].index), RISK)
                        out_rows.append({"family": "line timing", "rule": f"{model_lab}, under at a {t:g}+ point edge {sel_lab}, {grade_lab}", "market": "under", "window": w, **c, "note": "", "key": "lt_tot"})
    # how often the close moved toward the opener bet's side, full and Tuesday model, 4+
    mv = np.sign(x.spread_line - x.open_spread)
    clv = []
    for model_lab, ms in (("full model", x.model_spread), ("Tuesday model", x.tue_spread)):
        e = ms - x.open_spread; m = (e.abs() >= LIVE_EDGE) & wk17
        for w, (a, b) in OPEN_WINDOWS.items():
            s_ = m & x.season.between(a, b)
            tw = int((s_ & (mv != 0) & (np.sign(e) == mv)).sum()); aw = int((s_ & (mv != 0) & (np.sign(e) == -mv)).sum()); st = int((s_ & (mv == 0)).sum())
            pts = float((np.sign(e[s_]) * (x.spread_line - x.open_spread)[s_]).mean()) if s_.any() else np.nan
            clv.append({"model": model_lab, "window": w, "bets": int(s_.sum()), "close_moved_toward": tw, "moved_away": aw, "no_move": st,
                        "toward_pct_of_moves": round(tw / (tw + aw), 3) if tw + aw else np.nan, "mean_points_toward": round(pts, 2)})
    # every game: the move and the model's side
    for model_lab, ms in (("full model", x.model_spread), ("Tuesday model", x.tue_spread)):
        e = ms - x.open_spread; s_ = (e != 0) & wk17
        tw = int((s_ & (mv != 0) & (np.sign(e) == mv)).sum()); aw = int((s_ & (mv != 0) & (np.sign(e) == -mv)).sum())
        clv.append({"model": model_lab + " (every game)", "window": "2015-21", "bets": int(s_.sum()), "close_moved_toward": tw, "moved_away": aw, "no_move": int((s_ & (mv == 0)).sum()),
                    "toward_pct_of_moves": round(tw / (tw + aw), 3), "mean_points_toward": round(float((np.sign(e[s_]) * (x.spread_line - x.open_spread)[s_]).mean()), 2)})
    return pd.DataFrame(out_rows), pd.DataFrame(clv), notes


# ------------------------------------------------------------------------------------------------------ honesty checks
def honesty():
    rng = np.random.default_rng(SEED)
    live = {"live_spread": RULES["live_spread"], "live_under": RULES["live_under"]}
    res = {}
    for k, r in RULES.items():
        info = {}
        cmp_ = r["compare"]
        if cmp_ in live:
            L = live[cmp_]["cells"]; C = r["cells"]
            use_roi = r["market"] in ("ml", "wc_cal", "wc_raw") or r["stake"]
            info["beats_live_units_all3"] = all(C[w]["units"] > L[w]["units"] for w in MAIN3)
            if use_roi:
                info["beats_live_pct_all3"] = all((C[w]["roi"] if C[w]["bets"] else -9) > L[w]["roi"] for w in MAIN3)
            else:
                info["beats_live_pct_all3"] = all((C[w]["win_pct"] if C[w]["bets"] else 0) > L[w]["win_pct"] for w in MAIN3)
            info["beats_live_roi_pooled"] = (C["2015-25"]["roi"] if C["2015-25"]["bets"] else -9) > L["2015-25"]["roi"]
        info["positive_all3"] = all(r["cells"][w]["units"] > 0 for w in MAIN3)
        info["min_bets_window"] = min(r["cells"][w]["bets"] for w in MAIN3) if all(w in r["cells"] for w in MAIN3) else np.nan
        # placebo: shuffle the selection within season inside the parent pool, 2015-25
        if r["parent"] is not None and not r["stake"]:
            dd = r["d"]; yr = dd.season.between(2015, 2025)
            m, par, u = r["mask"] & yr, r["parent"] & yr, r["u"]
            if (m & ~par).sum() == 0 and m.sum() > 0:
                target = float(u[m].sum()); tot = np.zeros(N_PLACEBO)
                for s in sorted(dd.season[m].unique()):
                    pool = u[par & (dd.season == s)].values; k_ = int((m & (dd.season == s)).sum())
                    if k_ == 0:
                        continue
                    if k_ >= len(pool):
                        tot += pool.sum(); continue
                    idx = rng.random((N_PLACEBO, len(pool))).argsort(axis=1)[:, :k_]
                    tot += pool[idx].sum(axis=1)
                info["placebo_p"] = round(float((tot >= target - 1e-9).mean()), 3)
                info["placebo_pool_mean_units"] = round(float(tot.mean()), 2)
        res[k] = info
    return res


# -------------------------------------------------------------------------------------------------------------- report
def esc(t: str) -> str:
    return t.replace("|", "\\|")


def fmt_cell(c: dict, ml=False) -> str:
    if not c or not c["bets"]:
        return "0 bets"
    return f"{c['w']}-{c['l']}-{c['p']}, {100 * c['win_pct']:.1f}%, {c['units']:+.1f}u"


def table(keys: list[str], title: str, extra_cols=("roi", "placebo")) -> str:
    h = f"\n### {title}\n\n| Rule | 2015-18 | 2019-22 | 2023-25 | 2015-25 ROI | Seasons up | Luck p (2015-25) | Placebo p | Beats live, all 3 (units / %) | 2026 |\n|---|---|---|---|---|---|---|---|---|---|\n"
    for k in keys:
        if k not in RULES:
            continue
        r = RULES[k]; C = r["cells"]; hx = HON.get(k, {})
        su = sum(C[w]["seasons_up"] for w in MAIN3); sb = sum(C[w]["seasons_with_bets"] for w in MAIN3)
        bl = "" if "beats_live_units_all3" not in hx else f"{'yes' if hx['beats_live_units_all3'] else 'no'} / {'yes' if hx['beats_live_pct_all3'] else 'no'}"
        pl = "" if "placebo_p" not in hx else f"{hx['placebo_p']:.2f}"
        roi = C["2015-25"]["roi"]
        h += (f"| {esc(r['rule'])} | {fmt_cell(C['2015-18'])} | {fmt_cell(C['2019-22'])} | {fmt_cell(C['2023-25'])} | "
              f"{'' if pd.isna(roi) else f'{100 * roi:+.1f}%'} | {su}/{sb} | {C['2015-25']['p_luck']:.3f} | {pl} | {bl} | {fmt_cell(C['2026'])} |\n")
    return h


def main():
    global D, G, HON
    D, G, pred = load()
    spread_rules(D); total_rules(D); sizing(D)
    HON = honesty()
    R = pd.DataFrame(ROWS)
    for col in ("beats_live_units_all3", "beats_live_pct_all3", "beats_live_roi_pooled", "positive_all3", "min_bets_window", "placebo_p", "placebo_pool_mean_units"):
        R[col] = R.key.map(lambda k: HON.get(k, {}).get(col, np.nan))
    LT, CLV, lt_notes = line_timing(D)
    KP = kelly_paths(D)
    R = pd.concat([R, LT], ignore_index=True)
    R.drop(columns=["key"]).to_csv(REP / "bet_rules_sweep.csv", index=False)
    KP.to_csv(REP / "bet_rules_sweep_kelly.csv", index=False); CLV.to_csv(REP / "bet_rules_sweep_clv.csv", index=False)
    globals().update(R_=R, LT_=LT, CLV_=CLV, KP_=KP, LTN_=lt_notes)
    write_md(R, LT, CLV, KP, lt_notes)
    print(f"{R.rule.nunique()} rules, {len(R)} rows -> reports/bet_rules_sweep.csv")


SPECIAL = {"4+ edge, last bet week 15": "passes every check, but it is one of nine cutoffs tried on a known late-season fade that the weeks 1-13 shadow already tracks",
           "under: weeks 1-3 need 57%+, else 55%+": "passes every check (the 59% version is stronger)",
           "under: weeks 1-3 need 59%+, else 55%+": "passes every check: the one new tracking-only candidate"}


def write_md(R, LT, CLV, KP, lt_notes):
    K = lambda fam, rule: f"{fam}|{rule}"   # noqa: E731

    def c(key, w):
        return RULES[key]["cells"][w]

    def rec(key, w):
        x = c(key, w); return f"{x['w']}-{x['l']}"

    def recs(key):
        return ", ".join(rec(key, w) for w in MAIN3)

    def pooled_pct(key):
        x = c(key, "2015-25"); return f"{100 * x['win_pct']:.1f}%"

    def u(key, w):
        return f"{c(key, w)['units']:+.1f}u"

    def lt(rule, w):
        x = LT[(LT.rule == rule) & (LT.window == w)].iloc[0]; return x

    def ltr(rule, w="2015-21"):
        x = lt(rule, w); return f"{int(x.w)}-{int(x.l)} ({100 * x.win_pct:.1f}%, {x.units:+.1f}u)"

    def kp(rule, w, st):
        return KP[(KP.rule == rule) & (KP.window == w) & (KP.staking == st)].iloc[0]

    live, lu = "live_spread", "live_under"
    T = lambda r: K("thresholds", r); TM = lambda r: K("timing", r); KG = lambda r: K("kinds of game", r)   # noqa: E731
    FD = lambda r: K("favourite/dog", r); BT = lambda r: K("bet type", r); SZ = lambda r: K("sizing", r)   # noqa: E731
    n_rules = int(R.rule.nunique()); plac = [h["placebo_p"] for h in HON.values() if "placebo_p" in h]
    n_plac, n_sig = len(plac), sum(p_ <= 0.05 for p_ in plac)
    band = {b: c(T(f"spread edge band {b}"), "2015-25") for b in ("3-4", "4-5", "5-6", "6+")}
    bstr = lambda b: f"{band[b]['w']}-{band[b]['l']} ({100 * band[b]['win_pct']:.1f}%)"   # noqa: E731
    ks = {st: kp("spread 4+ flag", "2016-25", st) for st in ("flat 1u", "quarter Kelly", "half Kelly")}
    ku = {st: kp("under 55%+", "2016-25", st) for st in ("flat 1u", "quarter Kelly")}
    clv_t = CLV[(CLV.model == "Tuesday model") & (CLV.window == "2015-21")].iloc[0]; clv_f = CLV[(CLV.model == "full model") & (CLV.window == "2015-21")].iloc[0]
    clv_all = CLV[(CLV.model == "Tuesday model (every game)")].iloc[0]
    ml4 = BT("moneyline on the 4+ spread side")
    roi = lambda key, w: 100 * c(key, w)["roi"]   # noqa: E731

    md = f"""# Bet rules sweep (30 Sep 2026)

Matt's question: were the thresholds, the timing, the kinds of game, the kind of bet, favourite against underdog and the stake sizes all tested? This sweep tests {n_rules} rules on the three windows (2015-18 never used for any choice, 2019-22 where 4 was chosen, 2023-25 held out), with 2026 to date shown apart. Research only: nothing here changes the site or the picks. Script `experiments/bet_rules_sweep.py`; every rule and window in `reports/bet_rules_sweep.csv` (plus `bet_rules_sweep_kelly.csv` and `bet_rules_sweep_clv.csv`).

The live rules for comparison: **spreads 4+ edge, weeks 1-17**: {recs(live)} ({u(live, '2015-18')}, {u(live, '2019-22')}, {u(live, '2023-25')}); 2026 so far {rec(live, '2026')}. **Unders at a 55%+ chance**: {recs(lu)} ({u(lu, '2015-18')}, {u(lu, '2019-22')}, {u(lu, '2023-25')}); 2026 so far {rec(lu, '2026')}.

## Headline: tested, then the outcome

- **Thresholds.** Spread cuts 2 to 8 by 0.5 and four edge bands; unders at 52% to 62%; point-edge cuts on totals, unders and overs separately; overs at the same cutoffs. **Result: 4 stays.** The 3-4 band loses on all three windows ({recs(T('spread edge band 3-4'))}). The 4-6 band holds the whole record ({recs(T('spread edge band 4-6'))}). No other cut beats 4 on all three windows. 6+ goes {recs(T('spread 6+ edge'))}, which overturns the 21 Sep finding that "6+ wins big". For unders, 55% holds. Cuts of 59% to 62% win more often on 2015-22 but earn fewer units than 55% on 2023-25 (61%+: {recs(T('under at 61%+ chance'))}). Overs lose at every chance cutoff and every point edge with a real sample, which confirms 25 Sep.
- **Timing.** Weeks 1-4, 5-8, 9-13, 14-17 and 18; every last bet week from 10 to 18; skipping weeks 1-2 or 1-3; a higher bar in weeks 1-3. **Result: the early weeks are the flag's best stretch, not its worst.** Weeks 1-4 go {recs(TM('4+ edge, weeks 1-4'))}. Skipping them, or needing 5+ or 6+ there, costs units on every window. This confirms docs section 14 and overturns the 22 Sep note that weeks 1-6 were weak. Weeks 14-17 are the weak stretch ({recs(TM('4+ edge, weeks 14-17'))}) and week 18 is {rec(TM('4+ edge, weeks 18-18'), '2019-22')} and {rec(TM('4+ edge, weeks 18-18'), '2023-25')}, so the week-18 skip stands. A last bet week of 15 beats live on all three windows in units and win % ({recs(TM('4+ edge, last bet week 15'))}, placebo {HON[TM('4+ edge, last bet week 15')]['placebo_p']:.2f}). But it is one of nine cutoffs tried on a pattern already known, and the weeks 1-13 shadow already tracks it. For unders, **needing 59%+ in weeks 1-3 (55% after)** beats the live unders rule on all three windows ({recs(TM('under: weeks 1-3 need 59%+, else 55%+'))}, placebo {HON[TM('under: weeks 1-3 need 59%+, else 55%+')]['placebo_p']:.2f}). The 57% version passes too. Most of the gain is on 2015-18, where early unders went {rec(TM('under 55%+, weeks 1-4'), '2015-18')} in weeks 1-4.
- **Kinds of game.** Division, primetime (and TNF / SNF / MNF / Sunday slots), dome, short rest, byes, rest edges, home or away side, big or small line, the line on 3 or 7, our number crossing 3 or 7, and high or low totals. **Result: for spreads it is mostly noise.** Crossing 3 or 7 adds nothing ({pooled_pct(KG('4+ edge, crosses 3 or 7'))} against {pooled_pct(KG('4+ edge, crosses neither 3 nor 7'))} for neither). Division, primetime, dome and rest all do no better than random subsets of the flag of the same size. The one strong split is the model's side on the road: {recs(KG('4+ edge, our side away'))} against {recs(KG('4+ edge, our side at home'))} at home, which is the road-dog split below. This overturns the first build's docs note (section 9) that away sides were the weaker ones. **For unders, primetime carries the rule.** Primetime unders go {recs(KG('under 55%+, primetime'))} ({pooled_pct(KG('under 55%+, primetime'))}). Every other under goes {recs(KG('under 55%+, not primetime'))}, near break-even. Blind primetime unders go {recs(KG('BLIND: every primetime under (no model), weeks 1-17'))} ({pooled_pct(KG('BLIND: every primetime under (no model), weeks 1-17'))}), so the gain comes from the model, not a lean in the market. It has only {c(KG('under 55%+, primetime'), '2023-25')['bets']} bets held out.
- **Favourite or underdog.** Our side the favourite, the underdog or a pick'em; home dog, road dog, home favourite, road favourite; at 3, 4, 5 and 6+ and in edge bands; blind market baselines alongside. **Result: the model's favourites never earn their keep, and its road dogs are the best subset in the sweep.** 4+ favourites go {recs(FD('4+ edge, our side the favourite'))}; 5+ favourites go {recs(FD('5+ edge, our side the favourite'))}. 4+ dogs, the existing shadow, go {recs(FD('4+ edge, our side the underdog'))}. Within the dogs, road dogs go {recs(FD('4+ edge, road dog'))} ({pooled_pct(FD('4+ edge, road dog'))}, placebo {HON[FD('4+ edge, road dog')]['placebo_p']:.2f}) and home dogs go {recs(FD('4+ edge, home dog'))}. Blind road dogs go {recs(FD('BLIND: every road dog ATS (no model), weeks 1-17'))}, so this is the model's pick and not a market angle. With only {c(FD('4+ edge, road dog'), '2023-25')['bets']} bets held out, it is too small to recommend.
- **Kind of bet.** Spread against moneyline on the same side; unders against overs; the model's win chance against the no-vig moneyline at 3, 5, 8 and 10%, calibrated and raw. **Result: nothing beats the spread flag.** The moneyline on the flag's side makes {u(ml4, '2015-18')}, {u(ml4, '2019-22')} and {u(ml4, '2023-25')} (ROI {roi(ml4, '2015-18'):.0f}%, {roi(ml4, '2019-22'):.0f}%, {roi(ml4, '2023-25'):.0f}% against the spread's {roi(live, '2015-18'):.0f}%, {roi(live, '2019-22'):.0f}%, {roi(live, '2023-25'):.0f}%), so it is better on one window only. This confirms 25 Sep. Win chance against the moneyline loses on 2019-22 and 2023-25 at 3% and 5%, and makes nothing on 2023-25 at any cut (best: {u(BT('moneyline, model win chance (cal) beats no-vig book by 10%'), '2023-25')} at 10%). This confirms 28 Sep's "not added". Model unders beat blind unders; overs lose every way.
- **Sizing.** Flat staking; 1 / 1.5 / 2u by edge band; a linear stake; the tiers reversed; quarter and half Kelly from the walk-forward calibrated chance. **Result: bigger edges do not earn bigger stakes.** Win % by band: 4-5 {bstr('4-5')}, 5-6 {bstr('5-6')}, 6+ {bstr('6+')}. Tiered staking makes ROI {100 * c(SZ('4+ flag, tiered stakes (1u 4-5, 1.5u 5-6, 2u 6+)'), '2015-25')['roi']:.1f}% against {100 * c(live, '2015-25')['roi']:.1f}% flat. On spreads, quarter Kelly grew the bankroll less than flat over 2016-25 at about the same average stake: {ks['quarter Kelly'].growth_pct:+.1f}% against {ks['flat 1u'].growth_pct:+.1f}%, with a worst fall of {ks['quarter Kelly'].max_drawdown_pct:.1f}% against {ks['flat 1u'].max_drawdown_pct:.1f}%. The 24 Sep log's "quarter Kelly's worst fall 8%" is stale: the current `sizing_backtest.csv` shows 19.3% on 2019-22. On unders, quarter Kelly beat flat ({ku['quarter Kelly'].growth_pct:+.1f}% against {ku['flat 1u'].growth_pct:+.1f}%) but trailed it on 2023-25.
- **Line timing (2015-21, openers).** The 4+ rule against the opening line, graded at the close and at the opener; how often the close moved our way; whether those bets did better. **Result: the value is in the price you get, not the pick.** Picking against the opener but taking the closing number is worse than the live rule on the same games. Full model: {ltr('full model, 4+ edge vs opener, graded at close')} against {ltr('full model, 4+ edge vs close, graded at close')}. Tuesday model: {ltr('Tuesday model, 4+ edge vs opener, graded at close')}. Taking the opener with the fair Tuesday model is about as good as the close: {ltr('Tuesday model, 4+ edge vs opener, graded at opener')} against {ltr('Tuesday model, 4+ edge vs close, graded at close')}. When the line moved, the close moved toward the opener bet's side {100 * clv_t.toward_pct_of_moves:.0f}% of the time for the Tuesday model and {100 * clv_f.toward_pct_of_moves:.0f}% for the full model, by {clv_t.mean_points_toward:.1f} and {clv_f.mean_points_toward:.1f} points on average (every game: {100 * clv_all.toward_pct_of_moves:.0f}%). So the model does see where the market goes. Bets where the close moved toward us did *worse*, not better: {ltr('Tuesday model, 4+ edge vs opener, graded at opener, close moved toward our side')} at the opener against {ltr('Tuesday model, 4+ edge vs opener, graded at opener, close moved away')} when it moved away. A move toward us is the market taking the edge.

**What to do with it**
- **Worth a live tracking-only rule (one):** unders needing 59%+ in weeks 1-3. It beats the live unders rule in units and win % on all three windows, has more than 100 bets in each, and its placebo is {HON[TM('under: weeks 1-3 need 59%+, else 55%+')]['placebo_p']:.2f}. Its gain is small after 2018 ({u(TM('under: weeks 1-3 need 59%+, else 55%+'), '2019-22')} against {u(lu, '2019-22')}; {u(TM('under: weeks 1-3 need 59%+, else 55%+'), '2023-25')} against {u(lu, '2023-25')}).
- **Real patterns that are too small to recommend (under 40 bets held out), to watch in the live log:** primetime unders; road dogs at 4+ (the existing dog shadow already holds them); spreads in weeks 1-4.
- **Already tracked; nothing to add:** the late-season fade (the weeks 1-13 shadow) and dogs (the dog shadow).
- **Noise:** every spread kind-of-game split except road or away; key numbers; the rest and bye splits; division; dome; spread cuts other than 4; stakes scaled by edge; moneyline value; overs.
- **Contradicts earlier notes:** 6+ as the best cut (21 Sep); weeks 1-6 weak (22 Sep); away sides weaker (docs section 9, first build); quarter Kelly's 8% worst fall (24 Sep); and the opener study's Tuesday 2019-21 record, which leans on bad archive rows (see Caveats).
"""
    md += "\n## Tables (the most useful rows)\n\nEach cell is W-L-P, win % and units at -110 (a win +1, a loss -1.1; moneylines risk 1 at the closing price). Luck p is the one-sided binomial against 52.38% on 2015-25 (for moneylines: simulated at the vig-free book chance). Placebo p is the share of 200 random same-size, same-season subsets of the rule's parent pool that earned at least as many units. The pool is the live flag for a filter of the flag, and every game the model has a side on for a new cut. 'Beats live' means more units / higher win % than the live rule on all three windows (for moneylines and stakes, ROI instead of win %).\n"
    md += table([live] + [T(r) for r in ("spread 3.5+ edge", "spread 4.5+ edge", "spread 5+ edge", "spread 6+ edge", "spread edge band 2-3", "spread edge band 3-4", "spread edge band 4-5", "spread edge band 5-6", "spread edge band 6+", "spread edge band 4-6")], "Spread thresholds")
    md += table([lu] + [T(r) for r in ("under at 53%+ chance", "under at 57%+ chance", "under at 59%+ chance", "under at 61%+ chance", "under chance band 53%-55%", "under chance band 55%-57%", "under chance band 57%-59%", "under chance band 59%+",
                                        "under at a 3+ point total edge", "over at 55%+ chance", "over at 60%+ chance", "over at a 3+ point total edge")] + [BT("every under (blind, weeks 1-17)"), BT("every over (blind, weeks 1-17)")], "Totals thresholds")
    md += table([live] + [TM(r) for r in ("4+ edge, weeks 1-4", "4+ edge, weeks 5-8", "4+ edge, weeks 9-13", "4+ edge, weeks 14-17", "4+ edge, weeks 18-18", "4+ edge, last bet week 13", "4+ edge, last bet week 15", "4+ edge, last bet week 16", "4+ edge, last bet week 18",
                                           "4+ edge, skip weeks 1-2", "4+ edge, skip weeks 1-3", "weeks 1-3 need 5+, else 4+", "weeks 1-3 need 6+, else 4+")], "Timing, spreads")
    md += table([lu] + [TM(r) for r in ("under 55%+, weeks 1-4", "under 55%+, weeks 5-8", "under 55%+, weeks 9-13", "under 55%+, weeks 14-17", "under 55%+, weeks 18-18", "BLIND: every under in weeks 9-13 (no model)", "under 55%+, skip weeks 1-3",
                                         "under: weeks 1-3 need 57%+, else 55%+", "under: weeks 1-3 need 59%+, else 55%+")], "Timing, unders")
    md += table([live] + [KG(r) for r in ("4+ edge, our side at home", "4+ edge, our side away", "BLIND: every away side ATS (no model), weeks 1-17", "4+ edge, division game", "4+ edge, non-division game", "4+ edge, primetime", "4+ edge, not primetime",
                                           "4+ edge, dome or closed roof", "4+ edge, outdoor or open roof", "4+ edge, a team on short rest (<=5 days)", "4+ edge, our side off a bye (rest >= 12)", "4+ edge, opponent off a bye", "4+ edge, big line |line| >= 7",
                                           "4+ edge, small line |line| < 7", "4+ edge, line on 3 exactly", "4+ edge, our number crosses 3", "4+ edge, our number crosses 7", "4+ edge, crosses neither 3 nor 7", "4+ edge, high total (>= 47)", "4+ edge, low total (<= 40)")], "Kinds of game, spreads (filters of the live flag)")
    md += table([lu] + [KG(r) for r in ("under 55%+, primetime", "under 55%+, not primetime", "BLIND: every primetime under (no model), weeks 1-17", "under 55%+, division game", "under 55%+, dome or closed roof", "under 55%+, outdoor or open roof",
                                         "under 55%+, a team on short rest (<=5 days)", "under 55%+, high total (>= 47)", "under 55%+, low total (<= 40)", "under 55%+, wind 15+ mph outdoors")], "Kinds of game, unders")
    md += table([live] + [FD(r) for r in ("4+ edge, our side the favourite", "4+ edge, our side the underdog", "4+ edge, home dog", "4+ edge, road dog", "4+ edge, home favourite", "4+ edge, road favourite", "3+ edge, road dog", "5+ edge, road dog",
                                           "5+ edge, our side the favourite", "model's side a road dog, any edge, weeks 1-17", "BLIND: every road dog ATS (no model), weeks 1-17", "BLIND: every home dog ATS (no model), weeks 1-17",
                                           "edge band 4-6, our side the favourite", "edge band 4-6, our side the underdog")], "Favourite or underdog")
    md += table([live] + [BT(r) for r in ("moneyline on the 4+ spread side", "moneyline on the 4+ spread side, our side the dog", "moneyline on the 4+ spread side, our side the favourite", "moneyline on the 5+ spread side",
                                           "moneyline, model win chance (cal) beats no-vig book by 3%", "moneyline, model win chance (cal) beats no-vig book by 5%", "moneyline, model win chance (cal) beats no-vig book by 8%",
                                           "moneyline, model win chance (cal) beats no-vig book by 10%", "moneyline, win chance (cal) beats book by 5%, dogs only", "moneyline, model win chance (raw) beats no-vig book by 5%")], "Kind of bet (moneylines: units risk 1 at the closing price)")
    md += "\n### Sizing\n\n| Stakes | 2015-18 | 2019-22 | 2023-25 | ROI 2015-25 (on the amount risked) |\n|---|---|---|---|---|\n"
    for key in [live, SZ("4+ flag, tiered stakes (1u 4-5, 1.5u 5-6, 2u 6+)"), SZ("4+ flag, linear stakes (edge/4 units, capped at 2u)"), SZ("4+ flag, inverse tiers (2u 4-5, 1.5u 5-6, 1u 6+)"),
                lu, SZ("under 55%+, tiered stakes (1u 55-57%, 1.5u 57-59%, 2u 59%+)"), SZ("under 55%+, linear stakes (1u + (chance-55%)/4%, capped 2u)")]:
        md += f"| {RULES[key]['rule']} | {u(key, '2015-18')} | {u(key, '2019-22')} | {u(key, '2023-25')} | {100 * c(key, '2015-25')['roi']:+.1f}% |\n"
    md += "\nKelly (bankroll 100 at the start of each window, each week's bets sized from the bankroll at the start of the week; flat = 1 unit = 1% of the starting 100; the calibrated chance is walk-forward, so 2015 has no fit and the first window is 2016-18):\n\n| Rule | Window | Staking | Record | Growth | Worst fall | Mean stake |\n|---|---|---|---|---|---|---|\n"
    for r in KP[KP.window != "2026"].itertuples():
        md += f"| {r.rule} | {r.window} | {r.staking} | {r.record} | {r.growth_pct:+.1f}% | {r.max_drawdown_pct:.1f}% | {r.mean_stake_pct:.2f}% |\n"
    md += f"\n### Line timing (2015-21, {lt_notes['games']} games with an archive opener; {lt_notes['dropped_suspect_openers']} rows dropped as bad archive rows)\n\n| Rule | 2015-18 | 2019-21 | 2015-21 |\n|---|---|---|---|\n"
    for rule in ["full model, 4+ edge vs close, graded at close", "full model, 4+ edge vs opener, graded at close", "full model, 4+ edge vs opener, graded at opener",
                 "Tuesday model, 4+ edge vs close, graded at close", "Tuesday model, 4+ edge vs opener, graded at close", "Tuesday model, 4+ edge vs opener, graded at opener",
                 "Tuesday model, 4+ edge vs opener, graded at opener, close moved toward our side", "Tuesday model, 4+ edge vs opener, graded at opener, close moved away", "Tuesday model, 4+ edge vs opener, graded at opener, close did not move",
                 "Tuesday model, 3+ edge vs opener, graded at opener", "Tuesday model, 3+ edge vs close, graded at close",
                 "Tuesday model, under at a 3+ point edge vs opener, graded at opener", "Tuesday model, under at a 3+ point edge vs close, graded at close"]:
        cells = []
        for w in OPEN_WINDOWS:
            x = lt(rule, w); cells.append(f"{int(x.w)}-{int(x.l)}-{int(x.p)}, {100 * x.win_pct:.1f}%, {x.units:+.1f}u")
        md += f"| {rule} | " + " | ".join(cells) + " |\n"
    md += "\nHow often the close moved toward the opener bet's side (4+ against the opener, weeks 1-17):\n\n| Model | Window | Bets | Toward | Away | No move | Toward, share of moves | Mean points toward |\n|---|---|---|---|---|---|---|---|\n"
    for r in CLV.itertuples():
        md += f"| {r.model} | {r.window} | {r.bets} | {r.close_moved_toward} | {r.moved_away} | {r.no_move} | {100 * r.toward_pct_of_moves:.0f}% | {r.mean_points_toward:+.2f} |\n"
    # every rule that beat the live rule on all three windows in units or in win %
    cand = [k for k, h in HON.items() if h.get("beats_live_units_all3") or h.get("beats_live_pct_all3")]
    md += "\n### Every rule that beat the live rule on all three windows (units or win %), with the checks\n\n| Rule | Beats in units / win % | Fewest bets in a window | Placebo p | Verdict |\n|---|---|---|---|---|\n"
    for k in cand:
        h = HON[k]; mb = int(h["min_bets_window"]); pl = h.get("placebo_p", np.nan)
        if RULES[k]["stake"]:
            v = "more units only because it stakes more; ROI barely moves"
        elif mb < MIN_BETS:
            v = f"too small (under {MIN_BETS} bets in a window)"
        elif not h.get("beats_live_units_all3"):
            v = "a subset: higher win % but fewer units; watch only"
        elif pd.notna(pl) and pl <= 0.05:
            v = SPECIAL.get(RULES[k]["rule"], "passes every check")
        else:
            v = "fails the placebo"
        md += f"| {esc(RULES[k]['rule'])} | {'yes' if h.get('beats_live_units_all3') else 'no'} / {'yes' if h.get('beats_live_pct_all3') else 'no'} | {mb} | {'' if pd.isna(pl) else f'{pl:.3f}'} | {v} |\n"
    md += f"""
## Caveats

- **Many tests.** {n_rules} rules were graded. {n_plac} of them have a placebo, and {n_sig} of those have a placebo p of 0.05 or less. With this many tries, several will look good by luck. Many of the low placebo values are the same few patterns counted several times: late weeks, dogs and road sides, and big unders. That is why a rule has to beat live on every window, pass the placebo and have 40 bets a window before it counts. Two families do: a last bet week of 15 on spreads, and a higher bar for unders in weeks 1-3. Both are small changes.
- **The windows are not all clean.** 2015-18 never set a choice. 2019-22 set the 4-point cut. 2023-25 has been used as a second test for model inputs since 22 Sep. Any rule found here was found by looking at all three windows, so its record describes the backtest; only live games can confirm it.
- **The placebo tests the filter, not the model.** For a filter of the flag it asks whether the filter picks better bets than random bets from the flag. The flag itself, against random picks from every game the model has a side on, has a placebo of {HON[live].get('placebo_p', float('nan')):.2f}; the unders rule's, against random unders, is {HON[lu].get('placebo_p', float('nan')):.2f}.
- **Moneyline results** are graded at nflverse's closing moneyline. The luck test for them is simulated at the vig-free book chance of each side, because a flat 52.4% break-even does not apply.
- **Openers.** The archive covers 2015-21 only. {lt_notes['dropped_suspect_openers']} rows were dropped because the archive's own close disagrees with nflverse's, a total is under 25, a 0 opener sits on a 7+ close, or the opener flips sign by more than 10 points (most are typing errors; a few may be real moves in week-17 rest games, such as CHI at MIN and TEN at HOU in 2019). On the Tuesday model, 4+ against the opener in 2019-21, those rows went {lt_notes['dropped_rows_tuesday_4plus_2019_21']}. That is why `reports/opener_study.md` shows 64-33 there against 50-28 here (it also counts week 18). The full model's number includes Sunday's injury report and weather, so grading it at the opener flatters it; the Tuesday model is the fair early number.
- **Kelly** reads the walk-forward calibrated cover chance. It says 51-55% for 4+ edges, but those edges won about 60%, and it rises with the edge while the win rate does not. So Kelly adds variance rather than edge on spreads.
- **2026** to date is {rec(live, '2026')} on the spread flag and {rec(lu, '2026')} on unders. It is shown in the CSV and the tables, and it is far too few games to move any conclusion.
"""
    (REP / "bet_rules_sweep.md").write_text(md)


if __name__ == "__main__":
    main()
