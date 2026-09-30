"""Spread research (30 Sep 2026): buying the hook, team bias, underdogs / thresholds / matchups.

Research only: nothing here feeds the site or the picks. Reads the walk-forward backtest table the site grades
(backtest.join(pred_v3, games)), regular season, played, with a closing line.

Live rule (nflmodel/picks.py, graded as nflmodel/records.py): bet the model's side when |model_spread - spread_line| >= 4,
weeks 1-17, graded at the closing line, pushes out, -110 (a win +1, a loss -1.1).

Windows: 2015-18 (never used for any choice), 2019-22 (where 4 was chosen), 2023-25 (held out); 2026 to date apart.

Parts
  A  buying the hook: key-number landings on the 4+ bets, and buying half a point at typical prices
     (-120 on or off 3 and 7, -115 elsewhere; also -125 / -130 on or off 3)
  B  team bias: the model's margin miss by team, the model's ATS record by team, season-to-season persistence,
     and a walk-forward per-team bias correction (shrunk, prior seasons only)
  C  underdogs, thresholds and matchups: favourite / dog / pick'em at edge cuts 3-7, home / road x fav / dog, size of the
     dog, rating tiers, division / conference, rematches, off a 14+ win or loss, 2+ game streaks, dogs off a blowout

Honesty checks on every selection rule (spread bets on the model's side):
  p_luck        one-sided binomial of the record against 52.38% (break-even at -110)
  placebo_p     the rule's selection shuffled within season inside its parent pool (the live flag for a filter of the flag;
                every game the model has a side on for an every-game split; the cut's own pool for other cuts), 200 draws;
                the share of random same-size subsets whose units are at least the rule's. Pooled 2015-25 (placebo_p) and
                per window (placebo_p_window)
  beats_live_*  more units / higher win % than the live rule on every one of the three windows

Writes reports/spread_research.csv (one row per rule x window; team rows carry the team-error columns).
Usage: python experiments/spread_research.py
"""
from __future__ import annotations
import sys
import numpy as np, pandas as pd
from pathlib import Path
from scipy.stats import binom, pearsonr

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from nflmodel import backtest as B, picks as P          # noqa: E402
from nflmodel.season import DIV_OF, CONF_OF              # noqa: E402

OUT, REP = ROOT / "data" / "processed", ROOT / "reports"
BE = 110 / 210
WIN, RISK = 1.0, 1.1
EDGE, LAST = P.SPREAD_EDGE, P.LAST_BET_WEEK
WINDOWS = {"2015-18": (2015, 2018), "2019-22": (2019, 2022), "2023-25": (2023, 2025), "2015-25": (2015, 2025), "2026": (2026, 2026)}
MAIN3 = ["2015-18", "2019-22", "2023-25"]
N_PLACEBO, SEED = 200, 7
MIN_BETS = 40
BLOW = 14


# ------------------------------------------------------------------------------------------------------------------ data
def load() -> pd.DataFrame:
    g = pd.read_parquet(OUT / "games.parquet"); p = pd.read_parquet(OUT / "pred_v3.parquet")
    d = B.join(p, g)
    d = d[(d.game_type == "REG") & d.home_score.notna() & d.spread_line.notna()].copy()
    d["div_game"] = d.game_id.map(g.set_index("game_id").div_game)
    d = d.sort_values(["season", "week", "game_id"]).reset_index(drop=True)

    d["edge"] = d.model_spread - d.spread_line
    d["ae"] = d.edge.abs()
    d["sp_ok"] = d.edge != 0
    d["home_side"] = d.edge > 0
    hs = d.home_side
    d["our"] = np.where(hs, d.home_team, d.away_team); d["opp"] = np.where(hs, d.away_team, d.home_team)
    d["our_get"] = np.where(hs, -d.spread_line, d.spread_line)          # points our side gets (+ = dog)
    d["our_margin"] = np.where(hs, d.result, -d.result)
    d["cmS"] = d.our_margin + d.our_get                                   # > 0 our side covers
    d["sp_push"] = d.cmS == 0
    d["sp_won"] = d.cmS > 0
    d["sp_u"] = np.where(d.sp_push, 0.0, np.where(d.sp_won, WIN, -RISK))
    d["dog"] = d.our_get > 0; d["fav"] = d.our_get < 0; d["pk"] = d.our_get == 0
    lo_, hi_ = np.minimum(d.spread_line, d.model_spread), np.maximum(d.spread_line, d.model_spread)
    d["cross3"] = ((lo_ < 3) & (hi_ > 3)) | ((lo_ < -3) & (hi_ > -3))
    d["cross7"] = ((lo_ < 7) & (hi_ > 7)) | ((lo_ < -7) & (hi_ > -7))
    d["wk17"] = d.week <= LAST
    d["flag"] = (d.ae >= EDGE) & d.wk17 & d.sp_ok
    d["every"] = d.sp_ok & d.wk17

    # conference / division
    d["same_div"] = [DIV_OF.get(a) == DIV_OF.get(b) for a, b in zip(d.home_team, d.away_team)]
    d["same_conf"] = [CONF_OF.get(a) == CONF_OF.get(b) for a, b in zip(d.home_team, d.away_team)]

    # within-season history from every played regular-season game (games.parquet), before this game
    gg = g[(g.game_type == "REG") & g.home_score.notna()].copy()
    tg = pd.concat([pd.DataFrame({"game_id": gg.game_id, "season": gg.season, "week": gg.week, "team": gg.home_team, "opp": gg.away_team,
                                  "m": gg.home_score - gg.away_score}),
                    pd.DataFrame({"game_id": gg.game_id, "season": gg.season, "week": gg.week, "team": gg.away_team, "opp": gg.home_team,
                                  "m": gg.away_score - gg.home_score})]).sort_values(["team", "season", "week"]).reset_index(drop=True)
    tg["prev_m"] = tg.groupby(["team", "season"]).m.shift(1)
    res = np.sign(tg.m)
    streak = []
    last_key, cur = None, 0
    for (t, s, r) in zip(tg.team, tg.season, res):
        k = (t, s)
        if k != last_key:
            cur = 0; last_key = k
        streak.append(cur)                                                 # streak through the previous game
        cur = (cur + 1 if cur > 0 else 1) if r > 0 else ((cur - 1 if cur < 0 else -1) if r < 0 else 0)
    tg["streak"] = streak
    tg["pair"] = [tuple(sorted(x)) for x in zip(tg.team, tg.opp)]
    tg = tg.sort_values(["season", "week"]).reset_index(drop=True)
    tg["meet_no"] = tg.groupby(["season", "pair", "team"]).cumcount()     # earlier meetings this season
    tg["first_m"] = tg.groupby(["season", "pair", "team"]).m.shift(1)     # our margin in the previous meeting this season
    key = tg.set_index(["game_id", "team"])
    for side, col in (("our", "our"), ("opp", "opp")):
        idx = pd.MultiIndex.from_arrays([d.game_id, d[col]])
        for c in ("prev_m", "streak", "meet_no", "first_m"):
            d[f"{side}_{c}"] = key[c].reindex(idx).values

    # the model's own pre-game rating: its points equation's weights (this game's refit) on the as-of rating inputs.
    # rating = own offense's pull on own points (EPA and points ratings, QB) minus own defense's pull on the opponent's points
    f = pd.read_parquet(OUT / "features_asof.parquet")[["game_id", "team", "off_epa_play", "off_pf", "qb_rating", "own_def_epa_play", "own_def_pf"]]
    cf = p.set_index("game_id")[["coef_off_epa_play", "coef_off_pf", "coef_qb_rating", "coef_def_epa_play", "coef_def_pf"]]
    f = f.join(cf, on="game_id")
    f["rating"] = (f.coef_off_epa_play * f.off_epa_play + f.coef_off_pf * f.off_pf + f.coef_qb_rating * f.qb_rating
                   - (f.coef_def_epa_play * f.own_def_epa_play + f.coef_def_pf * f.own_def_pf))
    f = f.set_index(["game_id", "team"]).rating
    d["home_rating"] = f.reindex(pd.MultiIndex.from_arrays([d.game_id, d.home_team])).values
    d["away_rating"] = f.reindex(pd.MultiIndex.from_arrays([d.game_id, d.away_team])).values
    # tiers: thirds of the teams playing that season-week, by rating
    long = pd.concat([d[["season", "week", "game_id", "home_team", "home_rating"]].set_axis(["season", "week", "game_id", "team", "rating"], axis=1),
                      d[["season", "week", "game_id", "away_team", "away_rating"]].set_axis(["season", "week", "game_id", "team", "rating"], axis=1)])
    long["pct"] = long.groupby(["season", "week"]).rating.rank(pct=True)
    long["tier"] = np.where(long.pct.isna(), None, np.select([long.pct > 2 / 3, long.pct > 1 / 3], ["top", "mid"], "bot"))
    tier = long.set_index(["game_id", "team"]).tier
    d["our_tier"] = tier.reindex(pd.MultiIndex.from_arrays([d.game_id, d.our])).values
    d["opp_tier"] = tier.reindex(pd.MultiIndex.from_arrays([d.game_id, d.opp])).values
    return d


# --------------------------------------------------------------------------------------------------------------- grading
ROWS: list[dict] = []
RULES: dict[str, dict] = {}
rng = np.random.default_rng(SEED)


def cell(won, push, units, risk, seasons) -> dict:
    won, push = np.asarray(won, bool), np.asarray(push, bool)
    w = int((won & ~push).sum()); pu = int(push.sum()); l = int((~won & ~push).sum()); n = w + l
    u = float(np.sum(units))
    # ROI on the amount risked: a bet at -1xx risks 1.xx to win 1
    risked = float(np.sum(np.where(push, 0.0, risk)))
    s_units = pd.Series(np.asarray(units)).groupby(np.asarray(seasons)).sum()
    return {"bets": n, "w": w, "l": l, "p": pu, "win_pct": round(w / n, 4) if n else np.nan, "units": round(u, 2),
            "roi": round(u / risked, 4) if risked else np.nan, "seasons_up": int((s_units > 0).sum()), "seasons_with_bets": int(len(s_units)),
            "p_luck": round(float(binom.sf(w - 1, n, BE)), 4) if n else np.nan}


def add(part: str, family: str, rule: str, mask, d: pd.DataFrame, parent=None, bet_home=None, note: str = "", key=None):
    """Grade a spread rule. bet_home None = the model's side; else a boolean Series (True = bet the home side)."""
    m = pd.Series(mask, index=d.index).fillna(False).astype(bool)
    if bet_home is None:
        won, push, u = d.sp_won, d.sp_push, d.sp_u
        m &= d.sp_ok
    else:
        bh = pd.Series(bet_home, index=d.index).astype(bool)
        cm = d.result - d.spread_line
        won = pd.Series(np.where(bh, cm > 0, cm < 0), index=d.index); push = cm == 0
        u = pd.Series(np.where(push, 0.0, np.where(won, WIN, -RISK)), index=d.index)
    key = key or f"{part}|{family}|{rule}"
    RULES[key] = {"part": part, "family": family, "rule": rule, "mask": m, "u": u, "parent": None if parent is None else pd.Series(parent, index=d.index).fillna(False).astype(bool),
                  "cells": {}, "note": note, "model_side": bet_home is None}
    for wn, (a, b) in WINDOWS.items():
        sel = m & d.season.between(a, b)
        c = cell(won[sel], push[sel], u[sel], np.full(int(sel.sum()), RISK), d.season[sel])
        RULES[key]["cells"][wn] = c
        ROWS.append({"part": part, "family": family, "rule": rule, "window": wn, **c, "note": note, "key": key})
    return key


def honesty(d: pd.DataFrame, live_key: str) -> None:
    L = RULES[live_key]["cells"]
    for k, r in RULES.items():
        C = r["cells"]; info = {}
        if k != live_key and r["model_side"]:
            info["beats_live_units_all3"] = all(C[w]["units"] > L[w]["units"] for w in MAIN3)
            info["beats_live_pct_all3"] = all((C[w]["win_pct"] if C[w]["bets"] else 0) > L[w]["win_pct"] for w in MAIN3)
        info["positive_all3"] = all(C[w]["units"] > 0 for w in MAIN3)
        info["min_bets_window"] = min(C[w]["bets"] for w in MAIN3)
        par = r["parent"]
        if par is not None:
            m, u = r["mask"], r["u"]
            if (m & ~par).sum() == 0 and m.sum() > 0:
                per_season = {}
                for s in sorted(d.season[m].unique()):
                    pool = u[par & (d.season == s)].values; k_ = int((m & (d.season == s)).sum())
                    if k_ >= len(pool):
                        per_season[s] = np.full(N_PLACEBO, pool.sum()); continue
                    idx = rng.random((N_PLACEBO, len(pool))).argsort(axis=1)[:, :k_]
                    per_season[s] = pool[idx].sum(axis=1)
                for wn, (a, b) in WINDOWS.items():
                    ss = [s for s in per_season if a <= s <= b]
                    if not ss:
                        continue
                    tot = np.sum([per_season[s] for s in ss], axis=0)
                    target = float(u[m & d.season.between(a, b)].sum())
                    info[f"placebo_{wn}"] = round(float((tot >= target - 1e-9).mean()), 3)
        for row in ROWS:
            if row.get("key") == k:
                row.update({kk: vv for kk, vv in info.items() if not kk.startswith("placebo_")})
                row["placebo_p"] = info.get("placebo_2015-25", np.nan)
                row["placebo_p_window"] = info.get(f"placebo_{row['window']}", np.nan)
        r["info"] = info


# ------------------------------------------------------------------------------------------------------------ part A hook
def price_touch(get_before: np.ndarray, p3: float, p7: float = 120, pelse: float = 115) -> np.ndarray:
    """Risk (to win 1) for buying half a point from get_before to get_before + 0.5 points: -p3 when the half point
    moves on or off 3 (either sign), -p7 on or off 7, -pelse elsewhere."""
    a, b = get_before, get_before + 0.5
    touch3 = (np.abs(a) == 3) | (np.abs(b) == 3)
    touch7 = (np.abs(a) == 7) | (np.abs(b) == 7)
    return np.where(touch3, p3 / 100, np.where(touch7, p7 / 100, pelse / 100))


def part_a(d: pd.DataFrame) -> pd.DataFrame:
    out = []
    fl = d[d.flag]
    # how often the final margin landed on the key numbers against our side
    for wn, (a, b) in WINDOWS.items():
        x = fl[fl.season.between(a, b)]
        lost = x.cmS < 0
        fm = x.result.abs()
        out.append({"window": wn, "bets_incl_push": len(x), "losses": int(lost.sum()), "pushes": int(x.sp_push.sum()),
                    "loss_game_margin_3": int((lost & (fm == 3)).sum()), "loss_game_margin_7": int((lost & (fm == 7)).sum()),
                    "loss_by_half": int((x.cmS == -0.5).sum()),
                    "loss_by_half_on3": int(((x.cmS == -0.5) & (x.our_margin.abs() == 3)).sum()),
                    "loss_by_half_on7": int(((x.cmS == -0.5) & (x.our_margin.abs() == 7)).sum()),
                    "loss_by_one": int((x.cmS == -1).sum()),
                    "push_on3": int((x.sp_push & (x.our_get.abs() == 3)).sum()), "push_on7": int((x.sp_push & (x.our_get.abs() == 7)).sum()),
                    "win_by_half": int((x.cmS == 0.5).sum())})
    keys = pd.DataFrame(out)

    # simulate buying half a point on subsets of the 4+ bets
    gb = d.our_get.values
    new_cm = d.cmS.values + 0.5
    t3 = (np.abs(gb) == 3) | (np.abs(gb + 0.5) == 3); t7 = (np.abs(gb) == 7) | (np.abs(gb + 0.5) == 7)
    subsets = {
        "every 4+ bet": np.ones(len(d), bool),
        "line on 2.5 / 3.5 / 6.5 / 7.5": np.isin(d.spread_line.abs().values, [2.5, 3.5, 6.5, 7.5]),
        "our number crosses 3 or 7": (d.cross3 | d.cross7).values,
        "half point moves on or off 3 or 7": t3 | t7,
        "on or off 3 only": t3,
        "onto 3 or 7 only (our line -3.5, +2.5, -7.5, +6.5)": np.isin(gb, [-3.5, 2.5, -7.5, 6.5]),
        "off 3 or 7 only (our line -3, +3, -7, +7)": np.isin(np.abs(gb), [3, 7]),
        "on or off 7 only": t7,
        "half point touches neither 3 nor 7": ~(t3 | t7),
    }
    for p3 in (120, 125, 130):
        risk_b = price_touch(gb, p3)
        for lab, sub in subsets.items():
            buy = sub & d.flag.values
            won = np.where(buy, new_cm > 0, d.cmS.values > 0)
            push = np.where(buy, new_cm == 0, d.cmS.values == 0)
            risk = np.where(buy, risk_b, RISK)
            units = np.where(push, 0.0, np.where(won, WIN, -risk))
            m = d.flag.values
            rule = f"buy half a point: {lab} (off 3 at -{p3}, off 7 at -120, else -115)"
            key = f"A|hook|{rule}"
            RULES[key] = {"part": "A", "family": "hook", "rule": rule, "cells": {}, "model_side": False, "parent": None, "mask": d.flag, "u": pd.Series(units, index=d.index)}
            for wn, (a, b) in WINDOWS.items():
                sel = m & d.season.between(a, b).values
                c = cell(won[sel], push[sel], units[sel], risk[sel], d.season.values[sel])
                c["bought"] = int((buy & sel).sum())
                # units on the bought bets only, against the same bets at -110 unbought
                bs = buy & sel
                base_u = np.where(d.cmS.values == 0, 0.0, np.where(d.cmS.values > 0, WIN, -RISK))
                c["bought_units"] = round(float(units[bs].sum()), 2); c["bought_units_at_110"] = round(float(base_u[bs].sum()), 2)
                c["gain_vs_live"] = round(c["bought_units"] - c["bought_units_at_110"], 2)
                c["flips_push_to_win"] = int((bs & (d.cmS.values == 0)).sum()); c["flips_loss_to_push"] = int((bs & (d.cmS.values == -0.5)).sum())
                RULES[key]["cells"][wn] = c
                ROWS.append({"part": "A", "family": "hook", "rule": rule, "window": wn, **c, "key": key, "price_off3": p3})

    # the same half point on every game the model has a side on (weeks 1-17), by where our line sits: a bigger sample for
    # what the hook is worth at each number. Gain = units bought at the price minus units at -110 on the same bets.
    groups = {"our line -3 (buy to -2.5, off 3)": gb == -3, "our line +3 (buy to +3.5, off 3)": gb == 3,
              "our line +2.5 (buy to +3, onto 3)": gb == 2.5, "our line -3.5 (buy to -3, onto 3)": gb == -3.5,
              "our line -7 (buy to -6.5, off 7)": gb == -7, "our line +7 (buy to +7.5, off 7)": gb == 7,
              "our line +6.5 (buy to +7, onto 7)": gb == 6.5, "our line -7.5 (buy to -7, onto 7)": gb == -7.5,
              "any other line": ~(t3 | t7), "every game": np.ones(len(d), bool)}
    base_u = np.where(d.cmS.values == 0, 0.0, np.where(d.cmS.values > 0, WIN, -RISK))
    ev = d.every.values
    for lab, sub in groups.items():
        sel0 = sub & ev
        for wn, (a, b) in WINDOWS.items():
            sel = sel0 & d.season.between(a, b).values
            row = {"part": "A", "family": "hook, every game", "rule": f"every game, {lab}", "window": wn, "bets": int(sel.sum()),
                   "units": round(float(base_u[sel].sum()), 2), "flips_push_to_win": int((sel & (d.cmS.values == 0)).sum()),
                   "flips_loss_to_push": int((sel & (d.cmS.values == -0.5)).sum())}
            for p3 in (120, 125, 130):
                rb = price_touch(gb, p3)
                won = new_cm > 0; push = new_cm == 0
                ub = np.where(push, 0.0, np.where(won, WIN, -rb))
                row[f"gain_vs_110_off3_{p3}"] = round(float(ub[sel].sum() - base_u[sel].sum()), 2)
                row[f"gain_per_100_off3_{p3}"] = round(100 * float(ub[sel].sum() - base_u[sel].sum()) / max(int(sel.sum()), 1), 2)
            ROWS.append(row)
    return keys


# ------------------------------------------------------------------------------------------------------- part B team bias
def team_long(d: pd.DataFrame) -> pd.DataFrame:
    h = pd.DataFrame({"game_id": d.game_id, "season": d.season, "week": d.week, "team": d.home_team, "opp": d.away_team,
                      "model": d.model_spread, "line": d.spread_line, "actual": d.result})
    a = pd.DataFrame({"game_id": d.game_id, "season": d.season, "week": d.week, "team": d.away_team, "opp": d.home_team,
                      "model": -d.model_spread, "line": -d.spread_line, "actual": -d.result})
    L = pd.concat([h, a], ignore_index=True)
    L["err"] = L.model - L.actual            # + = the model rated the team too high
    L["mkt_err"] = L.line - L.actual
    L["lean"] = L.model - L.line             # + = the model likes the team more than the market
    return L


def part_b(d: pd.DataFrame) -> dict:
    L = team_long(d)
    res = {}
    # per team, per window: bias (mean err), t, market bias, model lean; model's side ATS in games with the team
    trows = []
    for wn, (a, b) in WINDOWS.items():
        x = L[L.season.between(a, b)]
        for t, y in x.groupby("team"):
            n = len(y); se = y.err.std(ddof=1) / np.sqrt(n) if n > 1 else np.nan
            gm = d[d.season.between(a, b) & ((d.home_team == t) | (d.away_team == t))]
            ev = gm[gm.every]; fl = gm[gm.flag]
            def rec(z):
                w = int((z.sp_won & ~z.sp_push).sum()); l = int((~z.sp_won & ~z.sp_push).sum()); p_ = int(z.sp_push.sum())
                return w, l, p_, round(w - RISK * l, 2)
            e_ = rec(ev); f_ = rec(fl); fo = rec(fl[fl.our == t]); fa = rec(fl[fl.opp == t])
            trows.append({"part": "B", "family": "team error", "rule": t, "window": wn, "n_games": n,
                          "bias": round(y.err.mean(), 3), "bias_t": round(y.err.mean() / se, 2) if se else np.nan,
                          "mae": round(y.err.abs().mean(), 3), "mkt_bias": round(y.mkt_err.mean(), 3), "lean": round(y.lean.mean(), 3),
                          "every_w": e_[0], "every_l": e_[1], "every_p": e_[2], "every_units": e_[3],
                          "flag_w": f_[0], "flag_l": f_[1], "flag_p": f_[2], "flag_units": f_[3],
                          "flag_on_w": fo[0], "flag_on_l": fo[1], "flag_on_units": fo[3], "flag_against_w": fa[0], "flag_against_l": fa[1], "flag_against_units": fa[3]})
    T = pd.DataFrame(trows); ROWS.extend(T.to_dict("records")); res["teams"] = T

    # season-to-season persistence of team-season mean residuals
    ts = L[L.season <= 2025].groupby(["team", "season"]).agg(err=("err", "mean"), mkt=("mkt_err", "mean"), lean=("lean", "mean"), n=("err", "size")).reset_index()
    nxt = ts.copy(); nxt["season"] -= 1
    pr = ts.merge(nxt, on=["team", "season"], suffixes=("", "_next"))
    per = []
    for col in ("err", "mkt", "lean"):
        r, pv = pearsonr(pr[col], pr[f"{col}_next"]); slope = np.polyfit(pr[col], pr[f"{col}_next"], 1)[0]
        per.append({"series": col, "pairs": len(pr), "corr": round(r, 3), "p": round(pv, 3), "slope": round(slope, 3)})
    # the same by window of the "next" season
    for wn, (a, b) in list(WINDOWS.items())[:3]:
        z = pr[pr.season.between(a - 1, b - 1)]
        r, pv = pearsonr(z.err, z.err_next)
        per.append({"series": f"err, next season in {wn}", "pairs": len(z), "corr": round(r, 3), "p": round(pv, 3), "slope": round(np.polyfit(z.err, z.err_next, 1)[0], 3)})
    # two prior seasons pooled against the next
    two = ts.copy()
    two["err_prev2"] = two.groupby("team").err.transform(lambda s: s.shift(1).rolling(2).mean())
    two = two.dropna(subset=["err_prev2"])
    r, pv = pearsonr(two.err_prev2, two.err)
    per.append({"series": "mean of 2 prior seasons vs this season", "pairs": len(two), "corr": round(r, 3), "p": round(pv, 3), "slope": round(np.polyfit(two.err_prev2, two.err, 1)[0], 3)})
    # noise vs signal: observed spread of team-season biases against pure sampling noise
    noise_var = float((L[L.season <= 2025].err.var() / ts.n).mean()); obs_var = float(ts.err.var())
    per.append({"series": "reliability of one team-season bias: 1 - noise var / observed var", "pairs": len(ts), "corr": round(1 - noise_var / obs_var, 3),
                "p": np.nan, "slope": np.nan, "obs_sd": round(np.sqrt(obs_var), 2), "noise_sd": round(np.sqrt(noise_var), 2)})
    res["persist"] = pd.DataFrame(per)
    # split halves: 2015-19 against 2020-25 team biases
    h1 = L[L.season.between(2015, 2019)].groupby("team").err.mean(); h2 = L[L.season.between(2020, 2025)].groupby("team").err.mean()
    r, pv = pearsonr(h1, h2.reindex(h1.index)); res["halves"] = (round(r, 3), round(pv, 3))

    # walk-forward per-team bias correction, prior seasons only, shrunk: b = sum(w * err) / (sum(w) + k)
    cors = []
    variants = [(1, 1.0, k) for k in (17, 34, 68)] + [(3, 0.5, k) for k in (17, 34, 68)]
    for look, dec, k in variants:
        b_home = np.zeros(len(d)); b_away = np.zeros(len(d))
        for s in sorted(d.season.unique()):
            prior = L[(L.season < s) & (L.season >= s - look)]
            if prior.empty:
                continue
            w = dec ** (s - 1 - prior.season)
            num = (w * prior.err).groupby(prior.team).sum(); den = w.groupby(prior.team).sum() + k
            bb = num / den
            idx = (d.season == s).values
            b_home[idx] = d.home_team[idx].map(bb).fillna(0).values; b_away[idx] = d.away_team[idx].map(bb).fillna(0).values
        ms = d.model_spread - b_home + b_away
        lab = f"prior {look} season{'s' if look > 1 else ''}{' (decay 0.5)' if look > 1 else ''}, shrink k={k}"
        e2 = ms - d.spread_line
        flag2 = (e2.abs() >= EDGE) & d.wk17 & (e2 != 0)
        cm = d.result - d.spread_line
        won2 = ((e2 > 0) & (cm > 0)) | ((e2 < 0) & (cm < 0)); push2 = cm == 0
        u2 = np.where(push2, 0.0, np.where(won2, WIN, -RISK))
        for wn, (a, b) in WINDOWS.items():
            sel = d.season.between(a, b)
            base_mae = float((d.model_spread - d.result)[sel].abs().mean()); new_mae = float((ms - d.result)[sel].abs().mean())
            s2 = sel & flag2
            c = cell(won2[s2], push2[s2], u2[s2], np.full(int(s2.sum()), RISK), d.season[s2])
            c0 = RULES["live"]["cells"][wn]
            cors.append({"part": "B", "family": "team bias correction", "rule": lab, "window": wn, "margin_mae_base": round(base_mae, 4), "margin_mae_corr": round(new_mae, 4),
                         "mae_gain": round(base_mae - new_mae, 4), **c, "live_units": c0["units"], "live_w": c0["w"], "live_l": c0["l"],
                         "mean_abs_adj": round(float(np.abs(b_home - b_away)[sel.values].mean()), 3), "key": f"B|corr|{lab}"})
    C = pd.DataFrame(cors); ROWS.extend(C.to_dict("records")); res["corr"] = C
    return res


# ---------------------------------------------------------------------------------------------- part C dogs and matchups
def part_c(d: pd.DataFrame) -> None:
    sides = [("our side the favourite", d.fav), ("our side the underdog", d.dog), ("pick'em", d.pk), ("underdog or pick'em", d.dog | d.pk),
             ("home dog", d.dog & d.home_side), ("road dog", d.dog & ~d.home_side), ("home favourite", d.fav & d.home_side), ("road favourite", d.fav & ~d.home_side),
             ("dog +0.5 to +3", d.dog & (d.our_get <= 3)), ("dog +3.5 to +6.5", d.our_get.between(3.5, 6.5)), ("dog +7 and up", d.our_get >= 7)]
    for t in (3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 7.0):
        base = (d.ae >= t) & d.wk17 & d.sp_ok
        if t != EDGE:
            add("C", "thresholds", f"{t:g}+ edge (all)", base, d, parent=d.every if t < EDGE else d.flag)
        for lab, k in sides:
            add("C", "favourite/dog", f"{t:g}+ edge, {lab}", base & k, d, parent=base)
    # every game, the model's side
    add("C", "favourite/dog", "every game (all), the model's side", d.every, d)
    for lab, k in sides:
        add("C", "favourite/dog", f"every game, {lab}", d.every & k, d, parent=d.every)
    # blind market baselines
    rd, hd = d.spread_line > 0, d.spread_line < 0
    add("C", "favourite/dog", "BLIND: every road dog ATS", rd & d.wk17, d, bet_home=pd.Series(False, index=d.index))
    add("C", "favourite/dog", "BLIND: every home dog ATS", hd & d.wk17, d, bet_home=pd.Series(True, index=d.index))

    # matchups, at 4+ and on every game
    tiers = ["top", "mid", "bot"]
    prev_our, prev_opp = d.our_prev_m, d.opp_prev_m
    m_list = []
    for a in tiers:
        for b in tiers:
            m_list.append(("rating tiers", f"our side {a} third vs opponent {b} third", (d.our_tier == a) & (d.opp_tier == b)))
    m_list += [("rating tiers", "same third (top-top, mid-mid, bot-bot)", d.our_tier == d.opp_tier),
               ("rating tiers", "our side the higher third", d.our_tier.map({"top": 3, "mid": 2, "bot": 1}) > d.opp_tier.map({"top": 3, "mid": 2, "bot": 1})),
               ("rating tiers", "our side the lower third", d.our_tier.map({"top": 3, "mid": 2, "bot": 1}) < d.opp_tier.map({"top": 3, "mid": 2, "bot": 1})),
               ("rating tiers", "top vs bottom, either side", ((d.our_tier == "top") & (d.opp_tier == "bot")) | ((d.our_tier == "bot") & (d.opp_tier == "top")))]
    m_list += [("division/conference", "division game", d.same_div), ("division/conference", "conference, not division", d.same_conf & ~d.same_div),
               ("division/conference", "non-conference", ~d.same_conf)]
    m_list += [("rematch", "second meeting this season", d.our_meet_no >= 1), ("rematch", "first meeting (division teams)", d.same_div & (d.our_meet_no == 0)),
               ("rematch", "rematch, our side lost the first meeting", (d.our_meet_no >= 1) & (d.our_first_m < 0)),
               ("rematch", "rematch, our side won the first meeting", (d.our_meet_no >= 1) & (d.our_first_m > 0))]
    m_list += [("off a big result", f"our side off a {BLOW}+ loss", prev_our <= -BLOW), ("off a big result", f"our side off a {BLOW}+ win", prev_our >= BLOW),
               ("off a big result", f"opponent off a {BLOW}+ loss", prev_opp <= -BLOW), ("off a big result", f"opponent off a {BLOW}+ win", prev_opp >= BLOW)]
    m_list += [("streaks", "our side on a 2+ game win streak", d.our_streak >= 2), ("streaks", "our side on a 2+ game losing streak", d.our_streak <= -2),
               ("streaks", "opponent on a 2+ game win streak", d.opp_streak >= 2), ("streaks", "opponent on a 2+ game losing streak", d.opp_streak <= -2),
               ("streaks", "our side on a 3+ game losing streak", d.our_streak <= -3), ("streaks", "opponent on a 3+ game win streak", d.opp_streak >= 3)]
    m_list += [("dog off a blowout", f"our side a dog off a {BLOW}+ loss", d.dog & (prev_our <= -BLOW)),
               ("dog off a blowout", f"our side a favourite, opponent a dog off a {BLOW}+ loss", d.fav & (prev_opp <= -BLOW)),
               ("dog off a blowout", f"our side a dog off a {BLOW}+ win", d.dog & (prev_our >= BLOW))]
    for fam, lab, k in m_list:
        k = pd.Series(k, index=d.index).fillna(False).astype(bool)
        add("C", fam, f"4+ edge, {lab}", d.flag & k, d, parent=d.flag)
        add("C", fam, f"every game, {lab}", d.every & k, d, parent=d.every)
    # blind: every dog off a blowout loss (the market angle), home / away as the dog
    home_prev = pd.Series(np.where(d.home_side, d.our_prev_m, d.opp_prev_m), index=d.index)
    away_prev = pd.Series(np.where(d.home_side, d.opp_prev_m, d.our_prev_m), index=d.index)
    hd_blow = hd & (home_prev <= -BLOW); ad_blow = rd & (away_prev <= -BLOW)
    bh = hd_blow.copy()
    add("C", "dog off a blowout", f"BLIND: every dog off a {BLOW}+ loss ATS", (hd_blow | ad_blow) & d.wk17, d, bet_home=bh)


# ------------------------------------------------------------------------------------------------------------------ main
def fmt(c: dict) -> str:
    return "0 bets" if not c["bets"] else f"{c['w']}-{c['l']}-{c['p']}, {100 * c['win_pct']:.1f}%, {c['units']:+.1f}u"


def main():
    d = load()
    add("live", "live", "LIVE: 4+ edge, weeks 1-17", d.flag, d, parent=d.every, key="live")
    keys = part_a(d)
    b = part_b(d)
    part_c(d)
    honesty(d, "live")

    R = pd.DataFrame(ROWS)
    lead = ["part", "family", "rule", "window", "bets", "w", "l", "p", "win_pct", "units", "roi", "p_luck", "placebo_p", "placebo_p_window",
            "beats_live_units_all3", "beats_live_pct_all3", "min_bets_window", "positive_all3", "seasons_up", "seasons_with_bets"]
    R = R[[c for c in lead if c in R.columns] + [c for c in R.columns if c not in lead and c != "key"]]
    R.to_csv(REP / "spread_research.csv", index=False)

    # ---------------------------------------------------------------------------------------- printed tables for the report
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 500); pd.set_option("display.max_columns", 40)
    print("\n== A: key numbers on the 4+ bets\n", keys.to_string(index=False))
    print("\n== A: buying the hook (units over every 4+ bet; live -110 alongside)")
    for k, r in RULES.items():
        if r["part"] == "A":
            C = r["cells"]
            print(f"| {r['rule']} | " + " | ".join(f"{fmt(C[w])} (bought {C[w]['bought']}, {C[w]['gain_vs_live']:+.1f}u vs -110)" for w in MAIN3 + ['2026']) + " |")
    print("| LIVE | " + " | ".join(fmt(RULES['live']['cells'][w]) for w in MAIN3 + ['2026']) + " |")
    R0 = pd.DataFrame([r for r in ROWS if r.get("family") == "hook, every game"])
    print("\n== A: hook on every game\n", R0[R0.window.isin(MAIN3 + ["2015-25"])][["rule", "window", "bets", "units", "flips_push_to_win", "flips_loss_to_push",
                                                                                   "gain_vs_110_off3_120", "gain_per_100_off3_120", "gain_per_100_off3_125", "gain_per_100_off3_130"]].to_string(index=False))

    print("\n== B: persistence\n", b["persist"].to_string(index=False), "\nsplit halves 2015-19 vs 2020-25:", b["halves"])
    T = b["teams"]; T15 = T[T.window == "2015-25"].sort_values("bias")
    print("\n== B: teams 2015-25 by bias\n", T15[["rule", "n_games", "bias", "bias_t", "mkt_bias", "lean", "every_w", "every_l", "every_units", "flag_w", "flag_l", "flag_units",
                                               "flag_on_w", "flag_on_l", "flag_against_w", "flag_against_l"]].to_string(index=False))
    piv = T[T.window.isin(MAIN3)].pivot(index="rule", columns="window", values="bias")
    print("\n== B: bias by window\n", piv.round(2).to_string())
    print("corr of team bias across windows:\n", piv.corr().round(3).to_string())
    for col in ("every_units", "flag_units", "lean", "mkt_bias"):
        pv = T[T.window.isin(MAIN3)].pivot(index="rule", columns="window", values=col)
        print(f"corr across windows of team {col}:", pv.corr().round(3).values[np.triu_indices(3, 1)])
    print("corr across teams, 2015-25, model bias vs market bias:", round(T15.bias.corr(T15.mkt_bias), 3))
    print("\n== B: correction\n", b["corr"][["rule", "window", "margin_mae_base", "margin_mae_corr", "mae_gain", "mean_abs_adj", "w", "l", "p", "units", "live_w", "live_l", "live_units"]].to_string(index=False))

    print("\n== C and live: every rule (3 windows, 2026, luck, placebo)")
    for k, r in RULES.items():
        if r["part"] in ("C", "live"):
            C = r["cells"]; inf = r.get("info", {})
            pw = "/".join("%.2f" % inf.get("placebo_" + w, float("nan")) for w in MAIN3)
            print(f"| {r['family']} | {r['rule']} | " + " | ".join(fmt(C[w]) for w in MAIN3) + f" | {100 * C['2015-25']['roi']:+.1f}% | {C['2015-25']['p_luck']:.3f} | "
                  f"{inf.get('placebo_2015-25', float('nan')):.2f} | {pw} | "
                  f"{'yes' if inf.get('beats_live_units_all3') else 'no'} / {'yes' if inf.get('beats_live_pct_all3') else 'no'} | {inf.get('min_bets_window')} | {fmt(C['2026'])} |")


if __name__ == "__main__":
    main()
