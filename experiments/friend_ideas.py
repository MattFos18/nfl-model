"""Five ideas from a friend's model, under the round-3 adoption rule (reports/round3_rule.md), 1 Oct 2026.

Research only: reads data/processed and data/weather, writes reports/friend_ideas.{md,csv}. Nothing in nflmodel/, web/
or data/ changes. Windows 2015-18 (never used for a choice), 2019-22 and 2023-25; regular season; the live bet rules of
nflmodel/picks.py (spread flag 4+ off the line, totals flag unders at a raw 55%+ chance, p_over_emp, weeks 1 to 17).
Bets graded at the schedule's closing line, pushes out; a straight bet at -110 wins 1 unit and loses 1.1; ROI is units
over the amount risked.

1. Wind / gust unders. Bet the under in outdoor games (roof outdoors or open) when the wind or the gust passes a cut:
   blind (every qualifying game) and with the totals flag (flag AND windy; or windy games at a lower chance, 50% / 52%).
   Three readings of the weather: the schedule's wind (nflverse, the game-day reading the model trains on), and the
   kickoff-hour wind and gust from Open-Meteo's ERA5 archive (data/weather/archive_kickoff.csv). All three are the
   weather that happened: look-ahead, graded as such. The forecast made the day before (data/weather/forecast_archive.csv,
   Open-Meteo previous runs) has wind and gust only from 2024, so it is graded on 2024-25 beside the observed readings
   on the same games (idea 3). Placebo: the weather reading shuffled within season among outdoor games, 50 draws; a
   rule passes it when at most 5 draws earn at least its units (blind) or its gain over the live flag (combined) on
   any window.
2. Gusts in the total equation. The kickoff gust (outdoor, 0 under a roof), the gust over the sustained wind, or the
   gust in place of the wind, added to M.TOTAL_FEATS; the total walk-forward reproduced (refit before every regular-
   season week on every played game since 2013, the over chance from the training games' own misses). Scored on the
   total miss per window and the totals-flag record; placebo the gust column shuffled within season among outdoor games.
   A forecast check prices 2024-25 with the day-before forecast gust (trained on the archive) to see what survives.
3. Forecast history back to 2018. What exists, what the free sources cover (see the report), and idea 1 on the
   forecast years we have, forecast against observed on the same games. `--stage plan` prints the request counts.
4. Teasers. Six-point two-team teasers on the basic-strategy legs (dogs +1.5 to +2.5 teased to +7.5 to +8.5, favorites
   -7.5 to -8.5 teased to -1.5 to -2.5), blind and filtered by the model (its side agrees with the leg, or agrees by
   1 / 2 / 3+ points). Legs paired within each week in kickoff order; a pushed leg with a winning partner is no action,
   with a losing partner a loss. Priced at -110, -120 and -130 (the common book price now runs -120 to -140). Placebo
   for the filter: the model's edges shuffled within season, 50 draws, the gain being the leg win rate over blind.
5. Points per drive. A team offense and defense rating from offensive points per drive (7 per touchdown drive, 3 per
   field-goal drive, over the drives in data/processed/team_box.parquet), opponent-adjusted and decayed exactly like
   the live ratings (nflmodel.ratings.solve and window, decay 0.94, last season at 0.8, alpha 16). Added to the points
   equation (all seven blend models carry it, as every live input), to the points and total equations, or swapped in
   for the EPA-per-play pair or the points pair. Full walk-forward with fresh trees (experiments/situational_game.py's
   engine). Placebo: the two ratings shuffled within season, 50 draws, stopped once 6 draws beat the real one.

    FI_SCRATCH=/path python -m experiments.friend_ideas [--stage all|wind|teaser|gust|ppd|plan|report] [--jobs 4]
"""
from __future__ import annotations
import os, sys, time, json, argparse
from pathlib import Path
os.environ.setdefault("OMP_NUM_THREADS", "1")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
SCR = Path(os.environ.get("FI_SCRATCH", "/tmp/friend_ideas")); SCR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("SG_SCRATCH", str(SCR / "sg"))
import numpy as np, pandas as pd
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from threadpoolctl import threadpool_limits
from nflmodel import model as M, backtest as B, picks as PK, ratings as RT
from nflmodel.model import OUT
from experiments import situational_game as SG

ROOT = Path(__file__).resolve().parent.parent
REP, WX = ROOT / "reports", ROOT / "data" / "weather"
W = PK.WINDOWS
WK = list(W)
VIG = 1.1
FLAG = PK.TOTAL_SHADOW["prob"]          # 0.55
N_PLACEBO, STOP_AT, PASS_MAX_BEATEN = 50, 6, 5
RNG_SEED = 20261001


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def wsel(d, w):
    a, b = W[w]
    return d.season.between(a, b)


def units(wn, ls, odds=-110.0):
    return wn - ls * abs(odds) / 100.0 if odds < 0 else wn * odds / 100.0 - ls


def rec_str(wn, ls):
    return f"{wn}-{ls}"


def shuffle_within(values: np.ndarray, groups: np.ndarray, rng, mask: np.ndarray | None = None) -> np.ndarray:
    """values permuted within each group (season), only among rows where mask holds (the rest kept)."""
    out = values.copy()
    m = np.ones(len(values), bool) if mask is None else mask
    for s in np.unique(groups[m]):
        ix = np.where((groups == s) & m)[0]
        out[ix] = values[rng.permutation(ix)]
    return out


# =========================================================================================== the bet table (ideas 1, 3, 4)
def bet_table() -> pd.DataFrame:
    g = pd.read_parquet(OUT / "games.parquet")
    d = B.join(pd.read_parquet(OUT / "pred_v3.parquet"), g)
    d = d[(d.game_type == "REG") & d.home_score.notna() & (d.season <= 2025) & (d.week <= PK.LAST_BET_WEEK)].copy()
    gi = g.set_index("game_id")
    d["roof"] = d.game_id.map(gi.roof); d["kickoff_et"] = d.game_id.map(gi.kickoff_et)
    d["outdoor"] = d.roof.isin(["outdoors", "open"])
    d["wind_s"] = d.game_id.map(gi.wind)
    a = pd.read_csv(WX / "archive_kickoff.csv").drop_duplicates("game_id").set_index("game_id")
    d["wind_r"] = d.game_id.map(a.wind); d["gust_r"] = d.game_id.map(a.gust)
    fa = pd.read_csv(WX / "forecast_archive.csv").drop_duplicates("game_id").set_index("game_id")
    d["wind_f"] = d.game_id.map(fa.wind_d1); d["gust_f"] = d.game_id.map(fa.gust_d1)
    for c in ["wind_s", "wind_r", "gust_r", "wind_f", "gust_f"]:
        d.loc[~d.outdoor, c] = np.nan
    d["p_under"] = 1 - d.p_over_emp
    d["cm_t"] = d.home_score + d.away_score - d.total_line          # under wins when < 0
    d["flag"] = (d.p_under >= FLAG) & d.total_line.notna()
    return d.reset_index(drop=True)


SRC_LABEL = {"wind_s": "schedule wind (observed)", "wind_r": "kickoff wind, ERA5 archive (observed)", "gust_r": "kickoff gust, ERA5 archive (observed)",
             "wind_f": "wind forecast the day before", "gust_f": "gust forecast the day before"}


def under_wl(d, m):
    f = m & d.total_line.notna() & (d.cm_t != 0)
    wn = int((d.cm_t[f] < 0).sum())
    return wn, int(f.sum()) - wn


# ------------------------------------------------------------------------------------------------------------ idea 1
def wind_rules():
    """name, kind (blind / and / lower), source, cut, lowered chance."""
    R = []
    for src, cuts in [("wind_s", [10, 12, 15, 20]), ("wind_r", [10, 12, 15, 20]), ("gust_r", [15, 20, 25, 30])]:
        for c in cuts:
            R.append(("blind", src, c, None))
    for src, cuts in [("wind_s", [10, 12, 15]), ("wind_r", [10, 12, 15]), ("gust_r", [20, 25])]:
        for c in cuts:
            R.append(("and", src, c, None))
            for L in (0.50, 0.52):
                R.append(("lower", src, c, L))
    return R


def rule_name(kind, src, cut, L):
    var = "gust" if src.startswith("gust") else "wind"
    if kind == "blind":
        return f"Under, {var} {cut}+ mph ({SRC_LABEL[src]})"
    if kind == "and":
        return f"Totals flag AND {var} {cut}+ ({SRC_LABEL[src]})"
    return f"Totals flag, or {var} {cut}+ at a {100 * L:.0f}%+ chance ({SRC_LABEL[src]})"


def rule_mask(d, kind, src, cut, L, vals=None):
    v = d[src].values if vals is None else vals
    windy = pd.Series(np.nan_to_num(v, nan=-1.0) >= cut, index=d.index) & d.outdoor
    if kind == "blind":
        return windy & d.total_line.notna()
    if kind == "and":
        return windy & d.flag
    return d.flag | (windy & (d.p_under >= L) & d.total_line.notna())


def grade_windows(d, m):
    out = {}
    for w in WK:
        s = wsel(d, w); wn, ls = under_wl(d, m & s)
        out[w] = {"w": wn, "l": ls, "units": units(wn, ls), "n": wn + ls}
    return out


def stage_wind():
    d = bet_table(); rng = np.random.default_rng(RNG_SEED)
    live = grade_windows(d, d.flag)
    rows = []
    seasons = d.season.values
    for kind, src, cut, L in wind_rules():
        real = grade_windows(d, rule_mask(d, kind, src, cut, L))
        gain = {w: real[w]["units"] - (0.0 if kind == "blind" else live[w]["units"]) for w in WK}
        has = d[src].notna().values
        beaten = 0; draws = []
        for _ in range(N_PLACEBO):
            v = shuffle_within(d[src].values, seasons, rng, has)
            p = grade_windows(d, rule_mask(d, kind, src, cut, L, v))
            pg = {w: p[w]["units"] - (0.0 if kind == "blind" else live[w]["units"]) for w in WK}
            draws.append(pg)
            beaten += any(pg[w] >= gain[w] for w in WK)
        p90 = {w: float(np.percentile([x[w] for x in draws], 90)) for w in WK}
        better = all(gain[w] > 0 for w in WK) if kind == "blind" else all(real[w]["units"] > live[w]["units"] and real[w]["w"] - real[w]["l"] >= live[w]["w"] - live[w]["l"] for w in WK)
        r = {"idea": "1 wind unders", "kind": kind, "source": src, "cut": cut, "lowered": L, "rule": rule_name(kind, src, cut, L),
             "beaten": beaten, "placebo_pass": beaten <= PASS_MAX_BEATEN, "better_all3": better, "look_ahead": True}
        for w in WK:
            o = real[w]
            r[f"rec_{w}"] = rec_str(o["w"], o["l"]); r[f"pct_{w}"] = o["w"] / max(o["n"], 1); r[f"units_{w}"] = o["units"]
            r[f"roi_{w}"] = o["units"] / max(VIG * o["n"], 1e-9); r[f"gain_{w}"] = gain[w]; r[f"p90_{w}"] = p90[w]
        rows.append(r)
    R = pd.DataFrame(rows)
    # the model inside windy games: windy games split by the model's under chance (pooled 2015-25 and by window)
    split = []
    for src, cut in [("wind_s", 10), ("wind_r", 12), ("gust_r", 25)]:
        windy = d.outdoor & (d[src] >= cut) & d.total_line.notna()
        for lab, m in [("model under chance under 50%", d.p_under < 0.50), ("50% to 55%", d.p_under.between(0.50, FLAG, inclusive="left")),
                       ("55%+ (the flag)", d.p_under >= FLAG), ("all windy games", d.p_under.notna())]:
            r = {"source": src, "cut": cut, "band": lab}
            for w in WK + ["2015-25"]:
                s = wsel(d, w) if w in W else d.season.between(2015, 2025)
                wn, ls = under_wl(d, windy & m & s); r[f"rec_{w}"] = rec_str(wn, ls); r[f"pct_{w}"] = wn / max(wn + ls, 1)
            split.append(r)
        # the flag in calm games
        r = {"source": src, "cut": cut, "band": "flag in the other games (calm or under a roof)"}
        for w in WK + ["2015-25"]:
            s = wsel(d, w) if w in W else d.season.between(2015, 2025)
            wn, ls = under_wl(d, d.flag & ~windy & s); r[f"rec_{w}"] = rec_str(wn, ls); r[f"pct_{w}"] = wn / max(wn + ls, 1)
        split.append(r)
    S = pd.DataFrame(split)
    # how much of each reading exists, by season (outdoor games, weeks 1-17)
    cov = d[d.outdoor].groupby("season")[["game_id", "wind_s", "wind_r", "gust_r", "wind_f", "gust_f"]].count().rename(columns={"game_id": "outdoor games"})
    R.to_csv(SCR / "wind.csv", index=False); S.to_csv(SCR / "wind_split.csv", index=False); cov.to_csv(SCR / "wind_cov.csv")
    json.dump({w: {"rec": rec_str(live[w]["w"], live[w]["l"]), "units": live[w]["units"]} for w in WK}, open(SCR / "live_flag.json", "w"))
    stage_forecast(d)
    log("wind done", len(R))


# ------------------------------------------------------------------------------------------------------------ idea 3
def stage_forecast(d=None):
    """Idea 1 on the games that have the day-before forecast (2024-25): forecast against observed on the same games."""
    d = bet_table() if d is None else d
    x = d[d.outdoor & d.wind_f.notna() & d.total_line.notna()].copy()
    rows = []
    corr = {"wind_f~wind_s": x[["wind_f", "wind_s"]].dropna().corr().iloc[0, 1], "wind_f~wind_r": x[["wind_f", "wind_r"]].dropna().corr().iloc[0, 1],
            "gust_f~gust_r": x[["gust_f", "gust_r"]].dropna().corr().iloc[0, 1], "n": int(len(x)),
            "mae_wind_f_vs_r": float((x.wind_f - x.wind_r).abs().mean()), "mae_gust_f_vs_r": float((x.gust_f - x.gust_r).abs().mean()),
            "bias_wind_f_vs_r": float((x.wind_f - x.wind_r).mean()), "bias_gust_f_vs_r": float((x.gust_f - x.gust_r).mean())}
    for var, cuts, srcs in [("wind", [10, 12, 15, 20], ["wind_f", "wind_s", "wind_r"]), ("gust", [15, 20, 25, 30], ["gust_f", "gust_r"])]:
        for c in cuts:
            sel = {s: (x[s] >= c) for s in srcs}
            for s in srcs:
                for kind, L in [("blind", None), ("and", None), ("lower", 0.52)]:
                    m = sel[s] if kind == "blind" else (sel[s] & x.flag if kind == "and" else (x.flag | (sel[s] & (x.p_under >= L))))
                    r = {"var": var, "cut": c, "source": s, "kind": kind}
                    for yr in [2024, 2025, "2024-25"]:
                        yy = x.season.between(2024, 2025) if yr == "2024-25" else (x.season == yr)
                        wn, ls = under_wl(x, m & yy); r[f"rec_{yr}"] = rec_str(wn, ls); r[f"units_{yr}"] = units(wn, ls); r[f"pct_{yr}"] = wn / max(wn + ls, 1)
                    if s != srcs[0]:
                        a, b = sel[srcs[0]], sel[s]
                        r["overlap_with_forecast"] = float((a & b).sum() / max((a | b).sum(), 1))
                    rows.append(r)
    for yr in [2024, 2025, "2024-25"]:
        yy = x.season.between(2024, 2025) if yr == "2024-25" else (x.season == yr)
        wn, ls = under_wl(x, x.flag & yy); corr[f"flag_{yr}"] = rec_str(wn, ls); corr[f"flag_units_{yr}"] = units(wn, ls)
    pd.DataFrame(rows).to_csv(SCR / "forecast.csv", index=False); json.dump(corr, open(SCR / "forecast.json", "w"), default=float)


# STADIUM -> a nearby airport with GFS MOS / NBM text guidance (a suggestion for the fetch; check each before use)
MOS_STATION = {"BUF": "KBUF", "GB": "KGRB", "CHI": "KMDW", "NE": "KOWD", "NYG": "KTEB", "NYJ": "KTEB", "PHI": "KPHL", "PIT": "KPIT", "CLE": "KBKL",
               "BAL": "KBWI", "WAS": "KDCA", "CIN": "KLUK", "KC": "KMCI", "DEN": "KDEN", "SEA": "KBFI", "SF": "KSJC", "TEN": "KBNA",
               "JAX": "KJAX", "MIA": "KMIA", "TB": "KTPA", "CAR": "KCLT", "LAC": "KSNA", "LA": "KLAX", "ARI": "KPHX", "LV": "KLAS",
               "OAK": "KOAK", "ATL": "KATL", "NO": "KMSY", "IND": "KIND", "DET": "KDTW", "MIN": "KMSP", "HOU": "KHOU", "DAL": "KDFW"}


def stage_plan():
    """Request counts for a forecast history 2018-2023 (idea 3): outdoor and open-roof regular-season and playoff games."""
    g = pd.read_parquet(OUT / "games.parquet")
    g = g[g.season.between(2018, 2023) & g.home_score.notna() & g.roof.fillna("outdoors").isin(["outdoors", "open"])].copy()
    fa = pd.read_csv(WX / "forecast_archive.csv")
    have = set(fa.game_id[fa.wind_d1.notna()])
    g["have_wind_fc"] = g.game_id.isin(have)
    by = g.groupby("season").agg(games=("game_id", "size"), sites=("home_team", "nunique"), have_wind_forecast=("have_wind_fc", "sum"))
    by["site_seasons"] = g.groupby("season").home_team.nunique()
    by["nbm_text_from_2018-11-07"] = g.assign(k=pd.to_datetime(g.kickoff_et)).groupby("season").k.apply(lambda s: int((s >= "2018-11-07").sum()))
    by.to_csv(SCR / "plan.csv")
    print(by.to_string()); print("total games", int(by.games.sum()), "site-seasons", int(by.site_seasons.sum()))
    return by


# ------------------------------------------------------------------------------------------------------------ idea 4
TEASE = 6.0
TEASER_PRICES = [-110.0, -120.0, -130.0]


def teaser_legs(d: pd.DataFrame) -> pd.DataFrame:
    """Every basic-strategy leg: the team's line (its own sign), the teased line, the result at it, and the model's lean."""
    x = d[d.spread_line.notna()].copy()
    x["edge"] = x.model_spread - x.spread_line                     # > 0: the model likes the home side more than the line
    legs = []
    for side in ("home", "away"):
        line = -x.spread_line if side == "home" else x.spread_line   # the side's own line (+ = getting points)
        marg = (x.home_score - x.away_score) if side == "home" else (x.away_score - x.home_score)
        dog = line.between(1.5, 2.5); fav = line.between(-8.5, -7.5)
        for kind, m in [("dog +1.5 to +2.5", dog), ("favorite -7.5 to -8.5", fav)]:
            y = x[m].copy()
            y["side"] = side; y["kind"] = kind; y["line"] = line[m]; y["teased"] = line[m] + TEASE
            y["res"] = marg[m] + y.teased                              # > 0 the leg wins
            y["lean"] = np.where(side == "home", y.edge, -y.edge)      # > 0: the model leans to this leg's side
            legs.append(y)
    L = pd.concat(legs, ignore_index=True)
    return L[["game_id", "season", "week", "kickoff_et", "side", "kind", "line", "teased", "res", "lean", "edge"]].sort_values(["season", "week", "kickoff_et", "game_id"]).reset_index(drop=True)


TEASE_FILTERS = {"blind": None, "model agrees": 0.0, "model agrees by 1+": 1.0, "model agrees by 2+": 2.0, "model agrees by 3+": 3.0}


def leg_mask(L, cut, lean=None):
    lean = L.lean.values if lean is None else lean
    return np.ones(len(L), bool) if cut is None else (lean > cut) if cut == 0.0 else (lean >= cut)


def pair_teasers(L: pd.DataFrame, m: np.ndarray) -> pd.DataFrame:
    """Two-team teasers: the week's qualifying legs in kickoff order, paired 1-2, 3-4, ...; an odd leg is left out."""
    x = L[m]
    out = []
    for (s, wk), q in x.groupby(["season", "week"], sort=False):
        r = q.res.values
        for i in range(0, len(r) - 1, 2):
            a, b = r[i], r[i + 1]
            if a < 0 or b < 0:
                o = "L"
            elif a == 0 or b == 0:
                o = "P"
            else:
                o = "W"
            out.append((s, wk, o))
    return pd.DataFrame(out, columns=["season", "week", "o"])


def teaser_scores(L, m) -> dict:
    out = {}
    T = pair_teasers(L, m)
    for w in WK:
        a, b = W[w]
        s = L.season.between(a, b).values & m
        r = L.res.values[s]; wn, ls, pu = int((r > 0).sum()), int((r < 0).sum()), int((r == 0).sum())
        p = wn / max(wn + ls, 1)
        t = T[T.season.between(a, b)]; tw, tl, tp = int((t.o == "W").sum()), int((t.o == "L").sum()), int((t.o == "P").sum())
        o = {"legs": f"{wn}-{ls}" + (f"-{pu}" if pu else ""), "leg_pct": p, "leg_n": wn + ls, "teasers": f"{tw}-{tl}" + (f"-{tp}" if tp else ""), "t_n": tw + tl}
        for pr in TEASER_PRICES:
            o[f"units{int(pr)}"] = units(tw, tl, pr)
            o[f"ev{int(pr)}"] = (p * p) * 1.0 - (1 - p * p) * abs(pr) / 100.0     # per teaser, legs independent at this window's leg rate
        out[w] = o
    return out


def stage_teaser():
    d = bet_table(); L = teaser_legs(d); rng = np.random.default_rng(RNG_SEED + 4)
    rows = []
    blind = teaser_scores(L, leg_mask(L, None))
    for kinds_lab, kinds in [("both leg kinds", None), ("dogs only", "dog +1.5 to +2.5"), ("favorites only", "favorite -7.5 to -8.5")]:
        km = np.ones(len(L), bool) if kinds is None else (L.kind == kinds).values
        base = teaser_scores(L, km)
        for fname, cut in TEASE_FILTERS.items():
            m = km & leg_mask(L, cut)
            sc = teaser_scores(L, m)
            r = {"idea": "4 teasers", "legs_used": kinds_lab, "filter": fname}
            for w in WK:
                for k, v in sc[w].items():
                    r[f"{k}_{w}"] = v
            if cut is not None:
                gain = {w: sc[w]["leg_pct"] - base[w]["leg_pct"] for w in WK}
                beaten = 0; draws = []
                for _ in range(N_PLACEBO):
                    lean = shuffle_within(L.lean.values, L.season.values, rng)
                    ps = teaser_scores(L, km & leg_mask(L, cut, lean))
                    pg = {w: ps[w]["leg_pct"] - base[w]["leg_pct"] for w in WK}
                    draws.append(pg); beaten += any(pg[w] >= gain[w] for w in WK)
                r["beaten"] = beaten; r["placebo_pass"] = beaten <= PASS_MAX_BEATEN
                for w in WK:
                    r[f"gain_{w}"] = gain[w]; r[f"p90_{w}"] = float(np.percentile([x[w] for x in draws], 90))
            rows.append(r)
    pd.DataFrame(rows).to_csv(SCR / "teaser.csv", index=False)
    # context: the same six points on other lines (is it the key numbers, or any dog?)
    x = d[d.spread_line.notna()]
    band = []
    for lab, lo, hi in [("dog +0.5 to +1", 0.5, 1.0), ("dog +1.5 to +2.5 (basic strategy)", 1.5, 2.5), ("dog +3 to +3.5", 3.0, 3.5), ("dog +4 to +6.5", 4.0, 6.5),
                        ("dog +7 to +10", 7.0, 10.0), ("favorite -1 to -2.5", -2.5, -1.0), ("favorite -3 to -6.5", -6.5, -3.0), ("favorite -7", -7.0, -7.0),
                        ("favorite -7.5 to -8.5 (basic strategy)", -8.5, -7.5), ("favorite -9 to -10.5", -10.5, -9.0)]:
        r = {"line": lab}
        for w in WK:
            q = x[wsel(x, w)]
            res = []
            for side in ("home", "away"):
                line = -q.spread_line if side == "home" else q.spread_line
                marg = (q.home_score - q.away_score) if side == "home" else (q.away_score - q.home_score)
                m = line.between(lo, hi); res.append((marg + line + TEASE)[m])
            v = pd.concat(res); wn, ls = int((v > 0).sum()), int((v < 0).sum())
            r[w] = f"{wn}-{ls} ({100 * wn / max(wn + ls, 1):.1f}%)"
        band.append(r)
    pd.DataFrame(band).to_csv(SCR / "teaser_bands.csv", index=False)
    log("teaser done")


# ===================================================================================== the walk-forward (ideas 2 and 5)
_E: dict = {}


def ppd_ratings(fp: pd.DataFrame) -> pd.DataFrame:
    """(game_id, team) -> off_ppd (the team's offense) and def_ppd (the opponent's defense), as of before the game:
    offensive points per drive, opponent-adjusted and decayed like the live ratings (ratings.solve, ratings.window)."""
    tb = pd.read_parquet(OUT / "team_box.parquet")
    tb = tb[tb.pf.notna() & (tb.off_drives > 0)].copy()
    tb["ppd"] = (7.0 * tb.off_td_drives + 3.0 * (tb.off_scoring_drives - tb.off_td_drives)) / tb.off_drives
    tg = pd.read_parquet(OUT / "team_games.parquet", columns=["game_id", "team", "season", "week", "opp", "home", "pf"])
    tg = tg[tg.pf.notna()].merge(tb[["game_id", "team", "ppd"]], on=["game_id", "team"], how="left")
    p = RT.DEFAULT
    out = []
    for (s, wk), q in fp.groupby(["season", "week"]):
        rows, w = RT.window(tg, s, wk, p["decay"], p["prior"])
        teams = sorted(set(tg[tg.season == s].team) | set(rows.team) | set(q.team) | set(q.opp))
        if len(rows) == 0:
            continue
        O, D, mu, h = RT.solve(rows, rows.ppd.values.astype(float), w, teams, p["alpha"])
        out.append(pd.DataFrame({"game_id": q.game_id.values, "team": q.team.values, "off_ppd": O.reindex(q.team).values, "def_ppd": D.reindex(q.opp).values}))
    return pd.concat(out, ignore_index=True)


def engine():
    """fp (the live inputs, prep()'d, plus the gust and ppd columns) and G (one row per game, plus the extra totals)."""
    if _E:
        return _E["fp"], _E["G"]
    fp = M.prep(M.with_trends(pd.read_parquet(OUT / "features_asof.parquet")))
    pr = SCR / "ppd.parquet"
    if not pr.exists():
        ppd_ratings(fp).to_parquet(pr, index=False)
    fp = fp.merge(pd.read_parquet(pr), on=["game_id", "team"], how="left")
    for c in ["off_ppd", "def_ppd"]:
        fp[c] = fp[c].fillna(0.0)
    G = SG.game_frame(fp)
    g = pd.read_parquet(OUT / "games.parquet").set_index("game_id")
    G["total_line"] = g.total_line.reindex(G.index).values
    G["roof"] = g.roof.reindex(G.index).values
    h = fp[fp.home == 1].set_index("game_id"); a = fp[fp.home == 0].set_index("game_id")
    G["ppd_sum"] = (h.off_ppd + a.off_ppd).reindex(G.index).values
    G["dppd_sum"] = (h.def_ppd + a.def_ppd).reindex(G.index).values
    # kickoff gust: archive (observed) for training and the backtest; the day-before forecast for the 2024-25 check
    arc = pd.read_csv(WX / "archive_kickoff.csv").drop_duplicates("game_id").set_index("game_id")
    fa = pd.read_csv(WX / "forecast_archive.csv").drop_duplicates("game_id").set_index("game_id")
    out = G.dome.values != 1
    G["outdoor"] = out
    gust = G.index.map(arc.gust).astype(float).values; wind = G.index.map(arc.wind).astype(float).values
    early = G.season.values <= 2014
    med_g = float(np.nanmedian(gust[out & early])); med_w = float(np.nanmedian(wind[out & early]))   # the fill for an outdoor game the archive lacks, from 2013-14
    gust = np.where(out, np.where(np.isnan(gust), med_g, gust), 0.0); wind = np.where(out, np.where(np.isnan(wind), med_w, wind), 0.0)
    G["gust_out"] = gust; G["gust_excess"] = np.clip(gust - wind, 0, None)
    gf = G.index.map(fa.gust_d1).astype(float).values; wf = G.index.map(fa.wind_d1).astype(float).values
    has_f = out & ~np.isnan(gf) & ~np.isnan(wf)
    G["has_fc"] = has_f
    G["gust_out_fc"] = np.where(has_f, gf, G.gust_out.values)
    G["gust_excess_fc"] = np.where(has_f, np.clip(gf - wf, 0, None), G.gust_excess.values)
    G["wind_out_fc"] = np.where(has_f, wf, G.wind_out.values)
    _E["fp"], _E["G"] = fp, G
    return fp, G


def total_wf(G: pd.DataFrame, tfeats: list, Gtest: pd.DataFrame | None = None, seasons=SG.SEASONS) -> pd.DataFrame:
    """The live total walk-forward (as SG.lean_walk_forward's total half): refit before every regular-season week on every
    played game since 2013; Gtest (default G) supplies the priced week's inputs."""
    Gt = G if Gtest is None else Gtest
    played = G[G.total.notna() & (G.season >= M.TRAIN_FROM)]
    out = []
    for s in seasons:
        gs = G[(G.season == s)]
        reg = SG.GAMES.set_index("game_id").game_type.reindex(gs.index).eq("REG")
        for wk in sorted(gs[reg.values].week.unique()):
            tr = played[(played.season < s) | ((played.season == s) & (played.week < wk))]
            ids = gs.index[(gs.week == wk).values]
            m = make_pipeline(StandardScaler(), Ridge(alpha=10.0)).fit(tr[tfeats].values, tr.total.values)
            mt = m.predict(Gt.loc[ids, tfeats].values)
            tres = tr.total.values - m.predict(tr[tfeats].values)
            tl = G.loc[ids, "total_line"].values
            pe = [np.nan if np.isnan(l) else float(np.mean(t + tres > l) / max(1e-9, np.mean(t + tres != l))) for t, l in zip(mt, tl)]
            out.append(pd.DataFrame({"game_id": ids, "season": s, "week": wk, "model_total": mt, "p_over_emp": pe}))
    return pd.concat(out, ignore_index=True)


def base_full() -> pd.DataFrame:
    f = SCR / "base.parquet"
    if f.exists():
        return pd.read_parquet(f)
    fp, G = engine()
    with threadpool_limits(limits=int(os.environ.get("FI_THREADS", "4"))):
        P = SG.lean_walk_forward(fp, G, list(M.FEATS), list(M.TOTAL_FEATS))
    P = SG.finish(P); P.to_parquet(f, index=False)
    return P


def flat_score(P) -> dict:
    return SG.flat(SG.score(P))


# ------------------------------------------------------------------------------------------------------------ idea 2
GUST_VARIANTS = {"gust (outdoor kickoff gust, 0 under a roof)": (["gust_out"], []),
                 "gust over the sustained wind": (["gust_excess"], []),
                 "gust in place of the wind": (["gust_out"], ["wind_out"])}


def _tf(add, drop):
    return [c for c in M.TOTAL_FEATS if c not in drop] + add


def _with_total(base: pd.DataFrame, T: pd.DataFrame) -> pd.DataFrame:
    P = base.drop(columns=["model_total", "p_over_emp", "home_exp", "away_exp"]).merge(T[["game_id", "model_total", "p_over_emp"]], on="game_id", how="left")
    return SG.finish(P)


def stage_gust():
    fp, G = engine(); base = base_full(); rng = np.random.default_rng(RNG_SEED + 2)
    b0 = flat_score(base)
    # the total walk-forward alone must give the base's totals
    T0 = total_wf(G, list(M.TOTAL_FEATS)); chk = float(np.nanmax(np.abs(T0.set_index("game_id").model_total - base.set_index("game_id").model_total.reindex(T0.game_id).values)))
    rows = [{"idea": "2 gust input", "variant": "(base: the live total equation)", **b0, "engine_check_total_max_diff": chk}]
    seasons = G.season.values
    for name, (add, drop) in GUST_VARIANTS.items():
        tf = _tf(add, drop)
        T = total_wf(G, tf); sc = flat_score(_with_total(base, T))
        gain = {w: tmae(T0, w) - tmae(T, w) for w in WK}
        beaten = 0; draws = []
        for i in range(N_PLACEBO):
            Gp = G.copy()
            for c in add:
                Gp[c] = shuffle_within(G[c].values, seasons, rng, G.outdoor.values)
            Tp = total_wf(Gp, tf)
            pg = {w: tmae(T0, w) - tmae(Tp, w) for w in WK}
            draws.append(pg); beaten += any(pg[w] >= gain[w] for w in WK)
        r = {"idea": "2 gust input", "variant": name, **sc, "beaten": beaten, "placebo_pass": beaten <= PASS_MAX_BEATEN}
        for w in WK:
            r[f"gain_{w}"] = gain[w]; r[f"p90_{w}"] = float(np.percentile([x[w] for x in draws], 90))
        # the forecast check: trained on the archive, the 2024 and 2025 games priced with the day-before forecast gust
        Gt = G.copy()
        for c in add:
            Gt[c] = G[c + "_fc"]
        Tf = total_wf(G, tf, Gtest=Gt, seasons=[2024, 2025]); Tb = T0[T0.season.isin([2024, 2025])]; Tr = T[T.season.isin([2024, 2025])]
        for lab, X in [("fc", Tf), ("obs", Tr), ("base", Tb)]:
            for s in (2024, 2025):
                q = X[X.season == s]; act = _act_total().reindex(q.game_id).values; ok = ~np.isnan(act)
                r[f"y{s}_{lab}_total_mae"] = float(np.abs(q.model_total.values - act)[ok].mean())
        rows.append(r); log("gust", name, {w: round(gain[w], 4) for w in WK}, "beaten", beaten)
    pd.DataFrame(rows).to_csv(SCR / "gust.csv", index=False)


_ACT: dict = {}


def _act_total() -> pd.Series:
    if "t" not in _ACT:
        g = SG.GAMES.set_index("game_id"); _ACT["t"] = g.home_score + g.away_score
    return _ACT["t"]


def tmae(T, w) -> float:
    """Total miss over the window's played games of a total walk-forward."""
    a, b = W[w]
    act = _act_total().reindex(T.game_id).values
    m = T.season.between(a, b).values & ~np.isnan(act)
    return float(np.abs(T.model_total.values - act)[m].mean())


# ------------------------------------------------------------------------------------------------------------ idea 5
PPD_VARIANTS = {
    "PPD added to the points equation": (["off_ppd", "def_ppd"], [], [], []),
    "PPD added to the points and total equations": (["off_ppd", "def_ppd"], [], ["ppd_sum", "dppd_sum"], []),
    "PPD in place of EPA per play (points and total)": (["off_ppd", "def_ppd"], ["off_epa_play", "def_epa_play"], ["ppd_sum", "dppd_sum"], ["off_sum", "def_sum"]),
    "PPD in place of the points rating (points and total)": (["off_ppd", "def_ppd"], ["off_pf", "def_pf"], ["ppd_sum", "dppd_sum"], ["pf_sum", "pa_sum"]),
}


def _ppd_run(args):
    name, seed = args
    add, drop, tadd, tdrop = PPD_VARIANTS[name]
    fp, G = engine()
    feats = [c for c in M.FEATS if c not in drop] + add
    tf = [c for c in M.TOTAL_FEATS if c not in tdrop] + tadd
    if seed is not None:
        rng = np.random.default_rng(seed)
        fp = fp.copy(); G = G.copy()
        # one permutation within season for both columns (the pair moves together)
        v = fp[["off_ppd", "def_ppd"]].values.copy(); s = fp.season.values; nv = v.copy()
        for ss in np.unique(s):
            k = np.where(s == ss)[0]; nv[k] = v[rng.permutation(k)]
        fp[["off_ppd", "def_ppd"]] = nv
        h = fp[fp.home == 1].set_index("game_id"); a = fp[fp.home == 0].set_index("game_id")
        G["ppd_sum"] = (h.off_ppd + a.off_ppd).reindex(G.index).values; G["dppd_sum"] = (h.def_ppd + a.def_ppd).reindex(G.index).values
    t0 = time.time()
    with threadpool_limits(limits=1):
        P = SG.lean_walk_forward(fp, G, feats, tf, total=bool(tadd))
    P = SG.finish(P, None if tadd else _E["base"])
    sc = flat_score(P)
    if seed is None:
        P.to_parquet(SCR / f"ppd_{abs(hash(name)) % 10**8}.parquet", index=False)
    return {"variant": name, "seed": -1 if seed is None else seed, "secs": time.time() - t0, **sc}


def stage_ppd(jobs=4):
    import multiprocessing as mp
    fp, G = engine(); base = base_full(); _E["base"] = base
    b0 = flat_score(base)
    path = SCR / "ppd_runs.csv"
    done = pd.read_csv(path) if path.exists() else pd.DataFrame(columns=["variant", "seed"])
    def save(rs):
        nonlocal done
        done = pd.concat([done, pd.DataFrame(rs)], ignore_index=True); done.to_csv(path, index=False)
    todo = [(n, None) for n in PPD_VARIANTS if not ((done.variant == n) & (done.seed == -1)).any()]
    ctx = mp.get_context("fork")
    with ctx.Pool(jobs) as pool:
        if todo:
            save(pool.map(_ppd_run, todo)); log("ppd real done")
        for n in PPD_VARIANTS:
            real = done[(done.variant == n) & (done.seed == -1)].iloc[0]
            gain = {w: b0[f"team_mae_{w}"] - real[f"team_mae_{w}"] for w in WK}
            seeds = [RNG_SEED + 500 + i for i in range(N_PLACEBO)]
            while True:
                have = done[(done.variant == n) & (done.seed >= 0)]
                beaten = sum(any(b0[f"team_mae_{w}"] - r[f"team_mae_{w}"] >= gain[w] for w in WK) for _, r in have.iterrows())
                left = [s for s in seeds if s not in set(have.seed.astype(int))]
                if beaten >= STOP_AT or not left:
                    break
                save(pool.map(_ppd_run, [(n, s) for s in left[:jobs]]))
            log("ppd placebo", n, "draws", len(done[(done.variant == n) & (done.seed >= 0)]), "beaten", beaten)
    json.dump(b0, open(SCR / "ppd_base.json", "w"), default=float)


# =================================================================================================== the report
def f1(x, n=1):
    return "" if x is None or (isinstance(x, float) and np.isnan(x)) else f"{x:+.{n}f}"


def pct(x):
    return "" if x is None or (isinstance(x, float) and np.isnan(x)) else f"{100 * x:.1f}%"


def md(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        out.append("| " + " | ".join(str(r[c]) for c in cols) + " |")
    return "\n".join(out)


VERDICTS = {}


def stage_report():
    L, C = [], []        # markdown lines, csv rows
    live = json.load(open(SCR / "live_flag.json"))
    R = pd.read_csv(SCR / "wind.csv"); S = pd.read_csv(SCR / "wind_split.csv"); cov = pd.read_csv(SCR / "wind_cov.csv")
    FC = pd.read_csv(SCR / "forecast.csv"); fcj = json.load(open(SCR / "forecast.json"))
    TZ = pd.read_csv(SCR / "teaser.csv"); GU = pd.read_csv(SCR / "gust.csv")
    PP = pd.read_csv(SCR / "ppd_runs.csv"); pb = json.load(open(SCR / "ppd_base.json")); plan = pd.read_csv(SCR / "plan.csv")

    def wcells(r, pre="rec", u="units", p="pct"):
        return {w: f"{r[f'{pre}_{w}']} ({pct(r[f'{p}_{w}'])}, {r[f'{u}_{w}']:+.1f}u)" for w in WK}

    # ---- idea 1
    blind = R[R.kind == "blind"]
    t1 = pd.DataFrame([{"rule": r.rule, **wcells(r), "ROI 2015-18 / 19-22 / 23-25": " / ".join(pct(r[f"roi_{w}"]) for w in WK),
                        "placebo (draws of 50 that matched it)": f"{r.beaten} ({'pass' if r.placebo_pass else 'fail'})"} for _, r in blind.iterrows()])
    comb = R[R.kind != "blind"]
    t1b = pd.DataFrame([{"rule": r.rule, **wcells(r), "units vs the flag": " / ".join(f1(r[f"gain_{w}"]) for w in WK),
                         "placebo": f"{r.beaten} ({'pass' if r.placebo_pass else 'fail'})", "all 3 better": "yes" if r.better_all3 else "no"} for _, r in comb.iterrows()])
    t1s = pd.DataFrame([{"windy games": f"{r.source} {r.cut}+", "model's under chance": r.band, **{w: f"{r[f'rec_{w}']} ({pct(r[f'pct_{w}'])})" for w in WK + ['2015-25']}} for _, r in S.iterrows()])
    for _, r in R.iterrows():
        for w in WK:
            C.append({"idea": "1 wind/gust unders", "variant": r.rule, "window": w, "record": r[f"rec_{w}"], "win_pct": round(r[f"pct_{w}"], 4),
                      "units_-110": round(r[f"units_{w}"], 2), "roi": round(r[f"roi_{w}"], 4), "gain": round(r[f"gain_{w}"], 2),
                      "placebo_p90": round(r[f"p90_{w}"], 2), "placebo_beaten_of_50": r.beaten, "note": "observed weather: look-ahead"})
    # headline numbers
    def g(rule_kind, src, cut, L_=None):
        q = R[(R.kind == rule_kind) & (R.source == src) & (R.cut == cut) & ((R.lowered.isna()) if L_ is None else (R.lowered == L_))]
        return q.iloc[0]
    ws10 = g("blind", "wind_s", 10); gr25 = g("blind", "gust_r", 25); wr12 = g("blind", "wind_r", 12)
    n_blind_pass = int((blind.placebo_pass & blind.better_all3).sum()); n_comb_pass = int((comb.placebo_pass & comb.better_all3).sum())
    best_comb = comb.assign(tot=comb[[f"gain_{w}" for w in WK]].min(axis=1)).sort_values("tot", ascending=False).iloc[0]

    # ---- forecast
    fcb = FC[FC.kind == "blind"]
    t3 = pd.DataFrame([{"rule": f"Under, {r['var']} {r.cut}+ mph", "reading": SRC_LABEL[r.source], "2024": f"{r.rec_2024} ({r.units_2024:+.1f}u)", "2025": f"{r.rec_2025} ({r.units_2025:+.1f}u)",
                        "2024-25": f"{r['rec_2024-25']} ({pct(r['pct_2024-25'])}, {r['units_2024-25']:+.1f}u)",
                        "same games as the forecast picks": "" if pd.isna(r.get("overlap_with_forecast")) else pct(r.overlap_with_forecast)} for _, r in fcb.iterrows()])
    fcc = FC[(FC.kind != "blind") & FC.source.isin(["wind_f", "gust_f", "wind_r", "gust_r"])]
    t3b = pd.DataFrame([{"rule": ("Flag AND " if r.kind == "and" else "Flag, or windy at 52%+: ") + f"{r['var']} {r.cut}+", "reading": SRC_LABEL[r.source],
                         "2024-25": f"{r['rec_2024-25']} ({r['units_2024-25']:+.1f}u)"} for _, r in fcc.iterrows()])
    for _, r in FC.iterrows():
        C.append({"idea": "3 forecast vs observed (2024-25)", "variant": f"{r.kind} {r['var']} {r.cut}+ {r.source}", "window": "2024-25", "record": r["rec_2024-25"],
                  "win_pct": round(r["pct_2024-25"], 4), "units_-110": round(r["units_2024-25"], 2), "note": "forecast known before kickoff" if r.source.endswith("_f") else "observed: look-ahead"})
    fw10 = FC[(FC.kind == "blind") & (FC["var"] == "wind") & (FC.cut == 10)].set_index("source")
    fg25 = FC[(FC.kind == "blind") & (FC["var"] == "gust") & (FC.cut == 25)].set_index("source")

    # ---- idea 2
    b = GU.iloc[0]
    t2 = [{"variant": "live total equation (base)", **{w: f"{b[f'total_mae_{w}']:.4f}" for w in WK}, "totals flag": " / ".join(f"{int(b[f'to_w_{w}'])}-{int(b[f'to_l_{w}'])}" for w in WK), "placebo": ""}]
    for _, r in GU.iloc[1:].iterrows():
        t2.append({"variant": r.variant, **{w: f"{r[f'total_mae_{w}']:.4f} ({r[f'gain_{w}'] * -1:+.4f})" for w in WK},
                   "totals flag": " / ".join(f"{int(r[f'to_w_{w}'])}-{int(r[f'to_l_{w}'])}" for w in WK),
                   "placebo": f"{int(r.beaten)} (not a test of the gust: see below)" if "in place" in r.variant else f"{int(r.beaten)} ({'pass' if r.placebo_pass else 'fail'})"})
        for w in WK:
            C.append({"idea": "2 gust in the total", "variant": r.variant, "window": w, "total_miss": round(r[f"total_mae_{w}"], 4), "gain": round(r[f"gain_{w}"], 4),
                      "record": f"{int(r[f'to_w_{w}'])}-{int(r[f'to_l_{w}'])}", "placebo_p90": round(r[f"p90_{w}"], 4), "placebo_beaten_of_50": int(r.beaten),
                      "note": "totals flag record; gust observed (ERA5 archive)"})
    t2 = pd.DataFrame(t2)
    t2f = pd.DataFrame([{"variant": r.variant, **{f"{s} {lab}": f"{r[f'y{s}_{k}_total_mae']:.4f}" for s in (2024, 2025) for lab, k in [("base", "base"), ("gust observed", "obs"), ("gust forecast", "fc")]}} for _, r in GU.iloc[1:].iterrows()])

    # ---- idea 4
    def tz(r, w):
        return f"legs {r[f'legs_{w}']} ({pct(r[f'leg_pct_{w}'])}); teasers {r[f'teasers_{w}']}: {r[f'units-110_{w}']:+.1f} / {r[f'units-120_{w}']:+.1f} / {r[f'units-130_{w}']:+.1f}u"
    t4 = pd.DataFrame([{"legs": r.legs_used, "filter": r["filter"], **{w: tz(r, w) for w in WK},
                        "placebo (leg rate over blind)": "" if r["filter"] == "blind" else f"{int(r.beaten)} ({'pass' if r.placebo_pass else 'fail'})"} for _, r in TZ.iterrows()])
    for _, r in TZ.iterrows():
        for w in WK:
            C.append({"idea": "4 teasers", "variant": f"{r.legs_used}, {r['filter']}", "window": w, "record": r[f"teasers_{w}"], "legs": r[f"legs_{w}"], "win_pct": round(r[f"leg_pct_{w}"], 4),
                      "units_-110": round(r[f"units-110_{w}"], 2), "units_-120": round(r[f"units-120_{w}"], 2), "units_-130": round(r[f"units-130_{w}"], 2),
                      "gain": None if r["filter"] == "blind" else round(r[f"gain_{w}"], 4), "placebo_p90": None if r["filter"] == "blind" else round(r[f"p90_{w}"], 4),
                      "placebo_beaten_of_50": None if r["filter"] == "blind" else int(r.beaten), "note": "legs W-L(-P); teasers W-L(-no action); units at -110 / -120 / -130"})
    tb_ = TZ[(TZ.legs_used == "both leg kinds") & (TZ["filter"] == "blind")].iloc[0]

    # ---- idea 5
    real = PP[PP.seed == -1]
    t5 = [{"variant": "live model (base)", **{w: f"{pb[f'team_mae_{w}']:.4f} / {pb[f'margin_mae_{w}']:.3f} / {pb[f'total_mae_{w}']:.3f}" for w in WK},
           "spread flag": " / ".join(f"{int(pb[f'sp_w_{w}'])}-{int(pb[f'sp_l_{w}'])}" for w in WK), "totals flag": " / ".join(f"{int(pb[f'to_w_{w}'])}-{int(pb[f'to_l_{w}'])}" for w in WK),
           "cal. log loss": " / ".join(f"{pb[f'll_cal_{w}']:.4f}" for w in WK), "placebo": ""}]
    ppd_rows = []
    for _, r in real.iterrows():
        pl = PP[(PP.variant == r.variant) & (PP.seed >= 0)]
        gain = {w: pb[f"team_mae_{w}"] - r[f"team_mae_{w}"] for w in WK}
        beaten = int(sum(any(pb[f"team_mae_{w}"] - q[f"team_mae_{w}"] >= gain[w] for w in WK) for _, q in pl.iterrows()))
        better = all(gain[w] > 0 for w in WK)
        nocost = all((r[f"sp_w_{w}"] - r[f"sp_l_{w}"] >= pb[f"sp_w_{w}"] - pb[f"sp_l_{w}"]) and (r[f"to_w_{w}"] - r[f"to_l_{w}"] >= pb[f"to_w_{w}"] - pb[f"to_l_{w}"]) and r[f"ll_cal_{w}"] <= pb[f"ll_cal_{w}"] + 1e-12 for w in WK)
        ppd_rows.append({"variant": r.variant, "gain": gain, "beaten": beaten, "draws": len(pl), "better": better, "nocost": nocost})
        t5.append({"variant": r.variant, **{w: f"{r[f'team_mae_{w}']:.4f} ({-gain[w]:+.4f}) / {r[f'margin_mae_{w}']:.3f} / {r[f'total_mae_{w}']:.3f}" for w in WK},
                   "spread flag": " / ".join(f"{int(r[f'sp_w_{w}'])}-{int(r[f'sp_l_{w}'])}" for w in WK), "totals flag": " / ".join(f"{int(r[f'to_w_{w}'])}-{int(r[f'to_l_{w}'])}" for w in WK),
                   "cal. log loss": " / ".join(f"{r[f'll_cal_{w}']:.4f}" for w in WK), "placebo": f"{beaten} of {len(pl)} draws{' (stopped)' if len(pl) < N_PLACEBO else ''} ({'pass' if beaten <= PASS_MAX_BEATEN and len(pl) == N_PLACEBO else 'fail'})"})
        for w in WK:
            C.append({"idea": "5 points per drive", "variant": r.variant, "window": w, "team_miss": round(r[f"team_mae_{w}"], 4), "margin_miss": round(r[f"margin_mae_{w}"], 4),
                      "total_miss": round(r[f"total_mae_{w}"], 4), "gain": round(gain[w], 4), "record": f"{int(r[f'sp_w_{w}'])}-{int(r[f'sp_l_{w}'])}",
                      "totals_record": f"{int(r[f'to_w_{w}'])}-{int(r[f'to_l_{w}'])}", "placebo_beaten_of_50": beaten, "note": f"spread flag record; placebo draws run {len(pl)}"})
    t5 = pd.DataFrame(t5)

    # ---- verdicts (one sentence each)
    any_ppd = [x for x in ppd_rows if x["better"] and x["nocost"] and x["beaten"] <= PASS_MAX_BEATEN]
    gpass = GU.iloc[1:][(GU.iloc[1:][[f"gain_{w}" for w in WK]] > 0).all(axis=1)]
    t_mod = TZ[(TZ["filter"] != "blind") & (TZ.placebo_pass == True)]
    V = {
        1: ("track as a hidden shadow" if n_blind_pass else "reject",
            f"Unders in windy outdoor games do win on the weather that happened ({n_blind_pass} blind rules beat the placebo and made money on all three windows), "
            f"but that weather is look-ahead, the one forecast check we can run (2024-25) is too thin to confirm it, and adding wind to the totals flag "
            f"{'never' if n_comb_pass == 0 else 'only sometimes'} beats the flag on every window; "
            f"so it stays off the bets{', tracked as a hidden shadow priced from the live kickoff forecast' if n_blind_pass else ''}."),
        2: ("adopt" if len(gpass) and (gpass.placebo_pass == True).any() else "reject",
            "The gust " + ("lowers the total miss on all three windows and beats its placebo" if len(gpass) and (gpass.placebo_pass == True).any() else "does not lower the total miss on all three windows beyond what its own placebo does") + "."),
        3: ("reject for now (needs data)","Our day-before forecasts carry wind and gusts only from Jan 2024, and the free sources that reach 2018 are a coarse wind-only model (Open-Meteo previous runs, JMA GSM) or airport station guidance (Iowa Mesonet MOS archive), so a three-window forecast test needs a fetch from GitHub's network first."),
        4: ("reject" if not len(t_mod) else "track as a hidden shadow", ""),
        5: ("adopt" if any_ppd else "reject", "")}
    VERDICTS.update(V)
    json.dump({str(k): v for k, v in V.items()}, open(SCR / "verdicts.json", "w"))

    L += ["# Five ideas from a friend's model (1 Oct 2026)", "",
          "`experiments/friend_ideas.py`; every row in `reports/friend_ideas.csv`. Rule: `reports/round3_rule.md` (better on 2015-18, 2019-22 and 2023-25; "
          "no bet cost; beats its own placebo, 50 within-season shuffles, at most 5 matching it on any window; no market input, no look-ahead, no new source). "
          "Regular season, weeks 1 to 17, graded at the closing line, pushes out. Straight bets at -110: a win is +1 unit, a loss -1.1; ROI is units over the amount risked.", "",
          f"The live totals flag (unders at a raw 55%+ chance) for reference: {live['2015-18']['rec']} ({live['2015-18']['units']:+.1f}u), "
          f"{live['2019-22']['rec']} ({live['2019-22']['units']:+.1f}u), {live['2023-25']['rec']} ({live['2023-25']['units']:+.1f}u).", ""]
    L += ["## Verdicts", "", "| idea | verdict | why |", "|---|---|---|"]
    vlab = {1: "1. Wind/gust under rule", 2: "2. Gusts in the total equation", 3: "3. Forecast history to 2018", 4: "4. Fixed teaser rule", 5: "5. Points-per-drive rating"}
    vpos = len(L)
    L += ["", "## 1. Wind and gust unders", "",
          "Outdoor and open-roof games. Every weather reading here is the weather that happened (look-ahead): the market closed on a forecast, "
          "so a record on observed wind overstates what a bettor could have had. Readings by season (outdoor games, weeks 1-17):", "", md(cov), "",
          "The schedule's wind is missing for half the 2022 and a fifth of the 2023 outdoor games (the model fills them with the median); the ERA5 kickoff archive covers every season.", "",
          "### Blind: the under in every qualifying game", "", "W-L (win %, units at -110) per window.", "", md(t1), "",
          f"The claim checks out on the schedule's wind: unders at 10+ mph went {ws10['rec_2015-18']}, {ws10['rec_2019-22']}, {ws10['rec_2023-25']} "
          f"({pct(ws10['pct_2015-18'])}, {pct(ws10['pct_2019-22'])}, {pct(ws10['pct_2023-25'])}), a little better than 55%. "
          f"On the kickoff archive the cleanest split is the gust: 25+ mph went {gr25['rec_2015-18']}, {gr25['rec_2019-22']}, {gr25['rec_2023-25']} "
          f"({gr25['units_2015-18']:+.1f}, {gr25['units_2019-22']:+.1f}, {gr25['units_2023-25']:+.1f} units).", "",
          "### Does the model add anything in windy games?", "", "Windy games split by the model's raw under chance (W-L, under win %):", "", md(t1s), "",
          "No. Inside windy games the under wins about as often whatever the model says (schedule wind 10+, 2015-25: " + ", ".join(
              f"{q.band.split(' (')[0].replace('model under chance ', '')} {pct(q['pct_2015-25'])}" for _, q in S[(S.source == 'wind_s') & ~S.band.str.startswith(('all', 'flag in'))].iterrows())
          + "); with the gust at 25+ the games the model leaned over won the under most often. Outside windy games the totals flag wins "
          + pct(S[(S.source == 'wind_s') & S.band.str.startswith('flag in')].iloc[0]['pct_2015-25']) + ", so part of the flag's record is windy games it would have won blind.", "",
          "### With the totals flag", "", "AND: the flag's bets in windy games only. Or: the flag plus windy games at a lower chance. Units against the live flag per window.", "", md(t1b), "",
          f"Best combination by its worst window: {best_comb.rule} ({' / '.join(f1(best_comb[f'gain_{w}']) for w in WK)} units against the flag).", ""]
    L += ["## 2. Gusts in the total equation", "",
          "Total miss per window (change against the live total equation in brackets); totals-flag W-L 2015-18 / 2019-22 / 2023-25. "
          "The spread and the win chance do not move (the total has its own equation). The gust is the ERA5 kickoff reading (observed), as the "
          "model's wind is the schedule's observed reading; outdoor games the archive lacks take the 2013-14 outdoor median, games under a roof 0.", "",
          f"Engine check: the total walk-forward here reproduces the live total equation to {b.engine_check_total_max_diff:.1e} points.", "", md(t2), "",
          "The placebo shuffles the gust among outdoor games only, so a shuffled column still says outdoors (some gust) or under a roof (0). That the shuffled "
          "column gains about as much as the real one says the small gain is the roof split, which the equation's dome input only partly holds, not the gust itself. "
          "The gust-for-wind placebo is not a test of the gust (shuffling it removes all wind), and that form fails rule 1 anyway.", "",
          "What survives a forecast: the same fits, the 2024 and 2025 games priced with the day-before forecast gust instead of the archive's (total miss):", "", md(t2f), ""]
    L += ["## 3. Forecast history back to 2018", "",
          "**What we have.** `data/weather/forecast_archive.csv` (Open-Meteo Previous Runs API, `nflmodel/forecast_archive.py`): the forecast one and two days "
          "before each played outdoor kickoff hour. Temperature from 2022 (GFS 2 m temperature is archived from March 2021); wind, gust and precipitation only from "
          "2024-01-20 (the Previous Runs API keeps most models from January 2024). So 2024 and 2025 are the only seasons with a pre-kickoff wind or gust; "
          "the 2026 live log (`data/weather/forecast_log.csv`) adds 2026 from here on. The ERA5 archive (`archive_kickoff.csv`, 2013-2025) is the weather that happened.", "",
          "**What the free sources cover (docs read 1 Oct 2026; this sandbox cannot reach open-meteo.com or mesonet.agron.iastate.edu, so nothing was fetched):**", "",
          "| source | what it is | wind | gust | from | pre-kickoff? |", "|---|---|---|---|---|---|",
          "| Open-Meteo Previous Runs API (`previous-runs-api.open-meteo.com/v1/forecast`, `<var>_previous_day1`) | each model's value at a fixed 1-7 day lead | yes | yes (most models) | Jan 2024 (most models); GFS temperature Mar 2021; **JMA GSM and MSM 2018** | yes |",
          "| same, `models=jma_gsm` | Japan's global model, 0.5 deg (~55 km), 6-hourly interpolated | yes | **no** (JMA publishes no gusts) | 2018 | yes |",
          "| Open-Meteo Historical Forecast API (`historical-forecast-api.open-meteo.com/v1/forecast`) | the first hours of each run stitched into one series | yes | yes | ~2021-22 (GFS 2021-03-23; ECMWF IFS HRES 2017; HRRR 2018-01-01) | **no**: the first hours of each run track what happened, so it is close to an analysis, not a forecast |",
          "| Open-Meteo Single Runs API (`run=` an init time) | a whole run as issued | yes | yes | ECMWF IFS HRES Mar 2024; others Apr 2026 | yes, but too late |",
          "| Iowa Environmental Mesonet MOS archive (`mesonet.agron.iastate.edu/api/1/mos.json?station=KBUF&model=GFS&runtime=2018-12-01%2012:00Z`) | NWS model output statistics at airports, runs 00/06/12/18Z, 3-hourly to 72 h | yes (knots) | GFS MOS no; **NBM text (NBS) yes, from 7 Nov 2018**; LAMP from Jul 2020 | GFS MOS Dec 2003; NAM MOS Dec 2008 | yes |",
          "| NOAA NDFD (NCEI THREDDS, NetcdfSubset by point; AWS `noaa-ndfd-pds` from Apr 2020) | the official NWS gridded forecast | yes | yes | about ten years online (AIRS orders back to 2004) | yes, but GRIB2 grids and slow |",
          "", "**What would be fetched (from GitHub's network, as `nflmodel/forecast_archive.py` already does):**", "",
          "1. Open-Meteo Previous Runs, `models=jma_gsm`, `hourly=wind_speed_10m_previous_day1,wind_speed_10m_previous_day2,temperature_2m_previous_day1`, "
          "`wind_speed_unit=mph`, one request per stadium-season over the season's date span (the site's local time zone), the kickoff hour picked out per game. Wind only.",
          "2. Iowa Mesonet MOS: per game, the GFS MOS run issued at 12Z the day before kickoff (`model=GFS`) at the stadium's airport, the 3-hourly wind speed (knots, x 1.151 for mph) "
          "at the forecast hours around kickoff, interpolated; and the NBM text run (`model=NBS`) for the gust (GST) from 7 Nov 2018. One request per game per model. "
          "A stadium-to-airport table is drafted in `MOS_STATION` (check each before use).",
          "3. Ask Open-Meteo to reconstruct wind and gust Previous Runs (GFS or ECMWF) for 2018-2023 at the 31 sites (their docs offer this on request).", "",
          "Request counts (outdoor and open-roof games, regular season and playoffs):", "", md(plan), "",
          f"About {int(plan.games.sum())} games and {int(plan.site_seasons.sum())} site-seasons: ~{int(plan.site_seasons.sum())} requests for option 1, "
          f"~{int(plan.games.sum())} GFS MOS requests plus ~{int(plan['nbm_text_from_2018-11-07'].sum())} NBM text requests for option 2. "
          "None of these is a source the weekly run pulls (it reads Open-Meteo's best-match forecast), so a rule trained on them would also need the live run to read the same model (rule 4).", "",
          "**Does forecast wind behave like observed wind?** On the 2024-25 outdoor games that have the day-before forecast "
          f"({fcj['n']} games): forecast and ERA5 wind correlate {fcj['wind_f~wind_r']:.2f} (mean absolute gap {fcj['mae_wind_f_vs_r']:.1f} mph, forecast {fcj['bias_wind_f_vs_r']:+.1f} mph), "
          f"gusts {fcj['gust_f~gust_r']:.2f} (gap {fcj['mae_gust_f_vs_r']:.1f} mph, {fcj['bias_gust_f_vs_r']:+.1f}); schedule wind against forecast {fcj['wind_f~wind_s']:.2f}. "
          f"The totals flag on these games: {fcj['flag_2024-25']} ({fcj['flag_units_2024-25']:+.1f}u).", "",
          "Blind unders on the same games, by reading (the last column: the share of the forecast rule's and this reading's games they have in common):", "", md(t3), "",
          "With the flag, 2024-25:", "", md(t3b), ""]
    L += ["## 4. Six-point two-team teasers", "",
          "Legs: dogs at +1.5 to +2.5 teased to +7.5 to +8.5, favorites at -7.5 to -8.5 teased to -1.5 to -2.5 (both through 3 and 7), at the closing line. "
          "The model filter keeps a leg when the model's spread leans to that side (by more than 0, or by 1, 2, 3+ points). Teasers pair each week's legs in kickoff order; "
          "units per teaser at -110 / -120 / -130. Break-even per leg (legs independent): -110 72.4%, -120 73.9%, -130 75.2%. Six-point two-teamers run -120 at most books now, "
          "-125 at Caesars, -130 to -140 at several. Placebo: the model's edges shuffled within season (50 draws); the gain is the leg win rate over the same legs blind.", "",
          md(t4), "",
          f"Blind, both kinds: legs {tb_['leg_pct_2015-18'] * 100:.1f}%, {tb_['leg_pct_2019-22'] * 100:.1f}%, {tb_['leg_pct_2023-25'] * 100:.1f}%.", "",
          "The same six points on other lines (legs W-L, win %), to show the key numbers doing the work:", "", md(pd.read_csv(SCR / "teaser_bands.csv")), ""]
    L += ["## 5. Points-per-drive rating", "",
          "Offensive points per drive (7 a touchdown drive, 3 a field-goal drive, kneel-only drives out, from `team_box.parquet`, which the weekly run builds from the "
          "play-by-play it already pulls), opponent-adjusted and decayed like the live ratings. Full walk-forward, fresh trees, every blend model carries the inputs. "
          "Cells: team points miss (change) / margin miss / total miss. The placebo stops once 6 draws match the real gain (the outcome is then settled).", "",
          md(t5), ""]
    # verdict rows (fill in the sentences that depend on the numbers)
    fw = fw10.loc["wind_f"]; fg = FC[(FC.kind == "blind") & (FC["var"] == "gust") & (FC.cut == 20)].set_index("source").loc["gust_f"]
    if n_blind_pass:
        passing = blind[blind.placebo_pass & blind.better_all3]
        V[1] = ("track as a hidden shadow",
                "On the weather that happened, " + "; ".join(f"{r.rule.split(' (')[0].lower().replace('under, ', 'unders at ')} ({SRC_LABEL[r.source].split(' (')[0]}) went "
                                                              f"{r['rec_2015-18']}, {r['rec_2019-22']}, {r['rec_2023-25']} ({r['units_2015-18'] + r['units_2019-22'] + r['units_2023-25']:+.1f}u) and beat its placebo ({r.beaten} of 50)" for _, r in passing.iterrows())
                + f", but that weather is look-ahead; the day-before forecast, the only reading known before kickoff, exists for 2024-25 only (wind 10+: {fw['rec_2024-25']}, {fw['units_2024-25']:+.1f}u; "
                f"gust 20+: {fg['rec_2024-25']}, {fg['units_2024-25']:+.1f}u); the model adds nothing inside windy games, and no wind-plus-flag rule beats the flag on every window. "
                "Not bet; worth wiring in as a hidden shadow on the live forecast (outdoor unders at forecast wind 10+ mph) so it earns a forecast record.")
    else:
        V[1] = ("reject", "No blind wind or gust rule both makes money on every window and beats its placebo, the readings are look-ahead, and no wind-plus-flag rule beats the flag on every window.")
    g1 = GU[GU.variant.str.startswith("gust (outdoor")].iloc[0]
    flag_cost = [w for w in WK if g1[f"to_w_{w}"] - g1[f"to_l_{w}"] < b[f"to_w_{w}"] - b[f"to_l_{w}"]]
    V[2] = ("reject", f"The outdoor kickoff gust lowers the total miss on every window ({' / '.join('%+.4f' % -g1['gain_' + w] for w in WK)}) but no more than the same column shuffled "
                      f"within season ({int(g1.beaten)} of 50 draws match it: the gain is the outdoor-or-roof split, not the gust), it costs totals-flag wins on {', '.join(flag_cost) or 'no window'}, "
                      "the gust-over-wind and gust-for-wind forms are worse on at least one window, and the gust is observed weather.")
    blind_both = TZ[(TZ["filter"] == "blind")]
    tdog = blind_both[blind_both.legs_used == "dogs only"].iloc[0]; tfav = blind_both[blind_both.legs_used == "favorites only"].iloc[0]
    prof130 = [r.legs_used for _, r in blind_both.iterrows() if all(r[f"units-130_{w}"] > 0 for w in WK)]
    V[4] = ("track as a hidden shadow (dog legs only, blind)" if "dogs only" in prof130 else "reject",
            f"Dog legs (+1.5 to +2.5) won {pct(tdog['leg_pct_2015-18'])}, {pct(tdog['leg_pct_2019-22'])} and {pct(tdog['leg_pct_2023-25'])} and their teasers made "
            f"{tdog['units-130_2015-18']:+.1f}, {tdog['units-130_2019-22']:+.1f}, {tdog['units-130_2023-25']:+.1f} units even at -130, but favorite legs fell to {pct(tfav['leg_pct_2023-25'])} on 2023-25 "
            + ("and the model filter does not beat its placebo on any leg set" if not len(t_mod) else "and the model filter beats its placebo only for " + ", ".join(f"{r.legs_used} ({r['filter']})" for _, r in t_mod.iterrows()))
            + "; a known market angle on the closing line, so tracked, not bet.")
    if any_ppd:
        V[5] = ("adopt", f"{', '.join(x['variant'] for x in any_ppd)} lowers the team points miss on all three windows, costs no bets and beats its placebo.")
    else:
        why = [f"{x['variant'].replace('PPD ', '').split(' (')[0]} {' / '.join('%+.4f' % -x['gain'][w] for w in WK)}" for x in ppd_rows]
        cf = pd.read_parquet(OUT / "features_asof.parquet", columns=["game_id", "team", "off_pf", "off_epa_play"]).merge(pd.read_parquet(SCR / "ppd.parquet"), on=["game_id", "team"])
        c_pf, c_epa = cf.off_ppd.corr(cf.off_pf), cf.off_ppd.corr(cf.off_epa_play)
        V[5] = ("reject", f"Points per drive is close to the ratings already in (correlation {c_pf:.2f} with the offense's points rating, {c_epa:.2f} with its EPA per play); "
                          "no form lowers the team points miss on all three windows (" + "; ".join(why) + f"), {sum(not x['nocost'] for x in ppd_rows)} of {len(ppd_rows)} cost "
                          "flag wins or calibration, and " + (lambda p: "none beats its placebo." if not p else
                          "only " + ", ".join(x["variant"].replace("PPD ", "").split(" (")[0] + f" ({x['beaten']} of 50)" for x in p)
                          + " beats its placebo, and only because a shuffled rating in place of a live one is worse still.")([x for x in ppd_rows if x["beaten"] <= PASS_MAX_BEATEN and x["draws"] == N_PLACEBO]))
    L[vpos:vpos] = [f"| {vlab[k]} | **{v[0]}** | {v[1]} |" for k, v in V.items()]
    (REP / "friend_ideas.md").write_text("\n".join(L) + "\n")
    pd.DataFrame(C).to_csv(REP / "friend_ideas.csv", index=False)
    json.dump({str(k): v for k, v in V.items()}, open(SCR / "verdicts.json", "w"), indent=1)
    print("\n".join(L[:vpos + 6]))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--stage", default="all"); ap.add_argument("--jobs", type=int, default=4)
    a = ap.parse_args()
    st = a.stage
    if st in ("all", "wind"):
        stage_wind()
    if st in ("all", "plan"):
        stage_plan()
    if st in ("all", "teaser"):
        stage_teaser()
    if st in ("all", "gust"):
        stage_gust()
    if st in ("all", "ppd"):
        stage_ppd(a.jobs)
    if st in ("all", "report"):
        stage_report()
