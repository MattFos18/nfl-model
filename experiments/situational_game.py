"""Every situational idea for the game model, under the round-3 rule (reports/round3_rule.md), 29 Sep 2026.

Families: situational (coaches, stadiums, surface, travel, time zones, rest, standings), primetime and kickoff time,
referees, weather and injuries (the live terms re-checked, then their interactions), and coaching matchups (the scheme
stand-in the pulled data supports). Every input is as of before its game (an earlier week; see
experiments/situational_feats.py), none reads a market number, none needs a source the weekly run does not pull.

How an idea is scored. Each idea is added on its own to the live model exactly as it runs: a points idea goes into
M.FEATS, so the live ridge, the five blend ridges and the boosted trees all carry it (as every live input is carried);
a total idea goes into M.TOTAL_FEATS. The live walk-forward is reproduced step for step (`lean_walk_forward`, checked
against M.walk_forward to 1e-9 on a candidate): refit before every regular-season week on every played game since
2013, the blend spread, the total equation, the displayed team points (total +/- spread) / 2, the win chance from the
ridge's residual scale and key-number weights, the over chance from the training games' own total misses. The trees
are refit fresh for the base and for every idea on this machine (the trees' cache is not read or written), so base
and idea are compared like for like. Windows 2015-18 (never used for a choice), 2019-22 and 2023-25, regular season.

Scores per window: team points miss (the rule's miss), margin and total miss; the spread flag on the live rule (4+
points off the line, weeks 1-17, pushes out); the totals flag on the live rule (under at a 55%+ raw chance,
p_over_emp, weeks 1-17); the win chance's log loss and Brier score, raw and calibrated the live way
(picks.home_calibration, fit on the variant's own earlier seasons); and the moneyline record of the model's side (the
side whose calibrated chance beats the no-vig closing moneyline chance), units at the closing price. Lines are used
only to grade.

Rule (reports/round3_rule.md). 1: the miss lower on all three windows (team points; for a total idea the total miss
too). 2: spread-flag and totals-flag wins minus losses not below the base on any window, calibrated win-chance log
loss not above it. 3: the idea's columns shuffled within season, 50 draws; the real gain must beat the draw's gain on
every window in at least 45 of 50 (a draw "beats" the real idea if its gain is at least the real gain on any window).
Run for ideas passing 1 and 2 (the rule's gate); stopped early once 6 draws beat the real one (the outcome is then
settled). 4: holds by construction, except where the report says otherwise. 5: the passing pieces run together.

    SG_SCRATCH=/path python -m experiments.situational_game --stage base|build|real|placebo|combo|report [--jobs 4]
Writes reports/situational_game.csv and reports/situational_game.md; everything else goes to SG_SCRATCH.
"""
from __future__ import annotations
import os, sys, time, json, argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import numpy as np, pandas as pd
from scipy.stats import norm
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.ensemble import HistGradientBoostingRegressor
from nflmodel import model as M, picks as PK
from nflmodel.model import OUT

ROOT = Path(__file__).resolve().parent.parent
REP = ROOT / "reports"
SCR = Path(os.environ.get("SG_SCRATCH", "/tmp/situational_game")); SCR.mkdir(parents=True, exist_ok=True)
WINDOWS = {"2015-18": (2015, 2018), "2019-22": (2019, 2022), "2023-25": (2023, 2025)}
SEASONS = range(2015, 2026)
BASE_FEATS, BASE_TOTAL = list(M.FEATS), list(M.TOTAL_FEATS)
N_PLACEBO, STOP_AT = 50, 6
M.save_trees_cache = lambda: None   # never write the live trees' cache from here


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


# ----------------------------------------------------------------------------------------------------------- engine
def game_frame(fp: pd.DataFrame) -> pd.DataFrame:
    """M._game_frame on every game at once (its rows are per game and as of each game, so slicing it by week is the
    same as building it on the week's training rows), plus season and week."""
    G = M._game_frame(fp)
    h = fp[fp.home == 1].set_index("game_id")
    G["season"] = h.loc[G.index, "season"].values; G["week"] = h.loc[G.index, "week"].values
    return G


def _p_home(mu, sigma, K):
    R = M.MARGIN_RANGE.astype(float)
    p = norm.pdf((R[None, :] - np.asarray(mu)[:, None]) / sigma) * np.asarray(K)[None, :]
    p = p / p.sum(axis=1, keepdims=True)
    return p[:, R > 0].sum(axis=1) + 0.5 * p[:, R == 0].sum(axis=1)


def lean_walk_forward(fp: pd.DataFrame, G: pd.DataFrame, feats: list, tfeats: list, seasons=SEASONS, points=True, total=True) -> pd.DataFrame:
    """M.walk_forward's numbers for the regular-season weeks of `seasons` (see the module docstring)."""
    played = fp[fp.pf.notna() & (fp.season >= M.TRAIN_FROM)]
    blend_cols = {k: feats + extra for k, (extra, _) in M.BLEND.items()}
    allc = sorted(set(feats) | {c for cols in blend_cols.values() for c in cols})
    out = []
    for s in seasons:
        test_all = fp[fp.season == s]
        for wk in sorted(test_all.loc[test_all.game_type == "REG", "week"].unique()):
            tr = played[(played.season < s) | ((played.season == s) & (played.week < wk))]
            te = test_all[test_all.week == wk]
            hmask = (te.home == 1).values
            h_ids = te.game_id.values[hmask]; a_ids = te.game_id.values[~hmask]
            aset = set(a_ids); ids = [g for g in h_ids if g in aset]
            rec = pd.DataFrame({"game_id": ids, "season": s, "week": wk})
            trh = tr[tr.home == 1].set_index("game_id"); tra = tr[tr.home == 0].set_index("game_id")
            tid = trh.index.intersection(tra.index)
            if points:
                y = tr.pf.values; X = tr[feats].values
                ridge = make_pipeline(StandardScaler(), Ridge(alpha=M.RIDGE)).fit(X, y)
                mu = tr[allc].mean()
                preds = {"ridge": ridge.predict(te[feats].fillna(mu[feats]).values)}
                for k, (extra, al) in M.BLEND.items():
                    cols = blend_cols[k]
                    m = make_pipeline(StandardScaler(), Ridge(alpha=al)).fit(tr[cols].fillna(tr[cols].mean()).values, y)
                    preds[k] = m.predict(te[cols].fillna(mu[cols]).values)
                t = HistGradientBoostingRegressor(**M.TREES).fit(X, y)
                preds["trees"] = t.predict(te[feats].fillna(mu[feats]).values)
                bl = pd.Series(np.mean([preds[k] for k in M.BLEND_LABEL], axis=0), index=te.game_id.values + np.where(hmask, "|h", "|a"))
                rec["model_spread"] = bl.loc[[g + "|h" for g in ids]].values - bl.loc[[g + "|a" for g in ids]].values
                trp = ridge.predict(X)
                ph = pd.Series(trp[(tr.home == 1).values], index=trh.index); pa = pd.Series(trp[(tr.home == 0).values], index=tra.index)
                tr_margin = (trh.loc[tid, "pf"] - tra.loc[tid, "pf"]).values
                tr_mu = (ph.loc[tid] - pa.loc[tid]).values
                sigma_m = float(np.std(tr_margin - tr_mu))
                K = M.key_weights(tr_margin, tr_mu, sigma_m)
                rec["p_home"] = _p_home(rec.model_spread.values, sigma_m, K.values)
            if total:
                trG = G.loc[tid]
                m = make_pipeline(StandardScaler(), Ridge(alpha=10.0)).fit(trG[tfeats].values, trG.total.values)
                rec["model_total"] = m.predict(G.loc[ids, tfeats].values)
                tres = trG.total.values - m.predict(trG[tfeats].values)
                rec["tres_n"] = len(tres)
                rec["_tres"] = [tres] * len(rec)
            out.append(rec)
    P = pd.concat(out, ignore_index=True)
    if total:
        P = P.merge(G[["total_line"]], left_on="game_id", right_index=True, how="left")
        pe = []
        for mt, tl, tres in zip(P.model_total, P.total_line, P._tres):
            if pd.isna(tl):
                pe.append(np.nan); continue
            v = mt + tres
            pe.append(float(np.mean(v > tl) / max(1e-9, np.mean(v != tl))))
        P["p_over_emp"] = pe
        P = P.drop(columns=["_tres", "total_line", "tres_n"])
    return P


def finish(P: pd.DataFrame, base: pd.DataFrame | None = None) -> pd.DataFrame:
    """Fill the half an idea did not touch from the base, then the displayed team points."""
    if base is not None:
        b = base.set_index("game_id")
        for c in ["model_spread", "p_home", "model_total", "p_over_emp"]:
            if c not in P.columns:
                P[c] = P.game_id.map(b[c]).values
    P["home_exp"] = (P.model_total + P.model_spread) / 2
    P["away_exp"] = (P.model_total - P.model_spread) / 2
    P["game_type"] = "REG"
    return P


# ---------------------------------------------------------------------------------------------------------- scoring
GAMES = pd.read_parquet(OUT / "games.parquet")


def _ml_payout(odds):
    odds = np.asarray(odds, float)
    return np.where(odds > 0, odds / 100.0, 100.0 / np.abs(odds))


def score(P: pd.DataFrame) -> dict:
    g = GAMES.set_index("game_id")
    d = P.copy()
    for c in ["home_score", "away_score", "spread_line", "total_line", "home_moneyline", "away_moneyline"]:
        d[c] = d.game_id.map(g[c]).values
    d = d[d.home_score.notna()].copy()
    cal = PK.home_calibrations(d.assign(game_type="REG"), GAMES)
    d["p_cal"] = [PK.home_cal_p(cal[int(s)], p) for s, p in zip(d.season, d.p_home)]
    res = d.home_score - d.away_score; tot = d.home_score + d.away_score
    out = {}
    for w, (a, b) in WINDOWS.items():
        x = d[d.season.between(a, b)]; r = res[x.index]; t = tot[x.index]
        e = np.concatenate([(x.home_exp - x.home_score).values, (x.away_exp - x.away_score).values])
        o = {"team_mae": float(np.abs(e).mean()), "margin_mae": float(np.abs(x.model_spread - r).mean()), "total_mae": float(np.abs(x.model_total - t).mean())}
        # spread flag (live rule)
        ed = x.model_spread - x.spread_line; cm = r - x.spread_line
        m = (ed.abs() >= PK.SPREAD_EDGE) & (x.week <= PK.LAST_BET_WEEK) & x.spread_line.notna() & (cm != 0)
        wn = int((((ed > 0) & (cm > 0)) | ((ed < 0) & (cm < 0)))[m].sum()); o["sp_w"], o["sp_l"] = wn, int(m.sum()) - wn
        # totals flag (live rule)
        ct = t - x.total_line
        m2 = ((1 - x.p_over_emp) >= PK.TOTAL_SHADOW["prob"]) & (x.week <= PK.LAST_BET_WEEK) & x.total_line.notna() & (ct != 0)
        wn2 = int((ct < 0)[m2].sum()); o["to_w"], o["to_l"] = wn2, int(m2.sum()) - wn2
        # win chance
        nt = r != 0; hw = (r > 0).astype(float)[nt]
        for lab, p in [("raw", x.p_home), ("cal", x.p_cal)]:
            q = p[nt].clip(1e-6, 1 - 1e-6)
            o[f"ll_{lab}"] = float(-(hw * np.log(q) + (1 - hw) * np.log(1 - q)).mean()); o[f"brier_{lab}"] = float(((q - hw) ** 2).mean())
        # moneyline: the model's side where its calibrated chance beats the no-vig closing chance
        ml = x.home_moneyline.notna() & x.away_moneyline.notna() & nt
        ph = 1 / (1 + _ml_payout(x.home_moneyline)); pa = 1 / (1 + _ml_payout(x.away_moneyline))
        qh = ph / (ph + pa)
        home_side = x.p_cal > qh; away_side = x.p_cal < qh
        bet = ml & (home_side | away_side)
        won = np.where(home_side, r > 0, r < 0)
        pay = np.where(home_side, _ml_payout(x.home_moneyline), _ml_payout(x.away_moneyline))
        o["ml_w"] = int((won & bet).sum()); o["ml_l"] = int((~won & bet).sum())
        o["ml_units"] = float(np.where(won, pay, -1.0)[bet.values].sum())
        o["n"] = int(len(x))
        out[w] = o
    return out


def flat(res: dict) -> dict:
    return {f"{k}_{w}": v for w, o in res.items() for k, v in o.items()}


# ------------------------------------------------------------------------------------------------------------ ideas
def ideas() -> list[dict]:
    """name, family, eq (P points / T total / DP drop from points / DT drop from total), level (team / game), cols,
    opp (add the opponent's value as opp_<col>), mode for game-level points ideas (same / home / sign), note."""
    I = []
    def add(name, fam, eq, cols, level="team", opp=False, mode="same", note=""):
        I.append({"name": name, "family": fam, "eq": eq, "cols": list(cols), "level": level, "opp": opp, "mode": mode, "note": note})
    S = "Situational"
    add("Coach vs coach (residual history)", S, "P", ["cvc"])
    add("Coach vs this opponent team", S, "P", ["coach_vs_team"], opp=True)
    add("Team vs team (residual history)", S, "P", ["team_vs_team"])
    add("QB vs this opponent (points residual)", S, "P", ["qb_vs_team"], opp=True)
    add("Coach career residual", S, "P", ["coach_career"], opp=True)
    add("Coach at this stadium", S, "P", ["coach_at_stadium"], opp=True)
    add("Team at this stadium", S, "P", ["team_at_stadium"], opp=True)
    add("Team on the road at this stadium", S, "P", ["road_at_stadium"], opp=True)
    add("Team on this surface", S, "P", ["team_on_surface"], opp=True)
    add("Turf (points)", S, "P", ["turf"], level="game", mode="same")
    add("Home edge on turf", S, "P", ["turf"], level="game", mode="home")
    add("Turf (total)", S, "T", ["turf"], level="game")
    add("Away team's home surface differs", S, "P", ["surf_mismatch"], opp=True)
    add("Surface mismatch (total)", S, "T", ["surf_mismatch_sum"], level="game")
    add("Dome team outdoors", S, "P", ["dome_team_out"], opp=True)
    add("Dome team outdoors (total)", S, "T", ["dome_team_out_sum"], level="game")
    add("Outdoor team in a dome", S, "P", ["out_team_in_dome"], opp=True)
    add("Outdoor team in a dome (total)", S, "T", ["out_team_in_dome_sum"], level="game")
    add("Roof open / closed (total)", S, "T", ["roof_open", "roof_closed"], level="game")
    add("Travel miles", S, "P", ["miles"], opp=True)
    add("Travel miles (total)", S, "T", ["miles_sum"], level="game")
    add("Time-zone shift, east- and west-bound", S, "P", ["tz_east", "tz_west"], opp=True)
    add("Time-zone shift (total)", S, "T", ["tz_abs_sum"], level="game")
    add("Consecutive road games", S, "P", ["road_streak"], opp=True)
    add("Miles over the last two weeks", S, "P", ["miles_2wk"], opp=True)
    add("Altitude (visitor at Denver or Mexico City)", S, "P", ["altitude"], opp=True)
    add("Altitude (total)", S, "T", ["altitude_game"], level="game")
    add("Rest difference (days)", S, "P", ["rest_diff"])
    add("Off a bye", S, "P", ["off_bye"], opp=True)
    add("Short week", S, "P", ["short_week"], opp=True)
    add("Short week (total)", S, "T", ["short_week_sum"], level="game")
    add("Off a bye (total)", S, "T", ["off_bye_sum"], level="game")
    add("Division game (total)", S, "T", ["div_game"], level="game")
    add("International game (total)", S, "T", ["intl"], level="game")
    add("Home edge at an international game", S, "P", ["intl"], level="game", mode="home")
    add("Coach tenure with the team", S, "P", ["coach_tenure_l"], opp=True)
    add("First-year head coach", S, "P", ["first_year_coach"], opp=True)
    add("Head coach experience (games)", S, "P", ["coach_exp_l"], opp=True)
    add("Coach's 4th-down aggressiveness", S, "P", ["coach_go4"], opp=True)
    add("Coach's 4th-down aggressiveness (total)", S, "T", ["go4_sum"], level="game")
    add("Clinched a playoff spot", S, "P", ["clinched"], opp=True)
    add("Clinched, final week", S, "P", ["clinched_final"], opp=True)
    add("Mathematically eliminated", S, "P", ["eliminated"], opp=True)
    add("Rematch: first meeting's residual", S, "P", ["rematch_r"])
    add("Coach against his former team", S, "P", ["coach_vs_former"], opp=True)
    add("QB against his former team", S, "P", ["qb_vs_former"], opp=True)
    add("Look-ahead: next game in primetime", S, "P", ["next_prime"], opp=True)
    add("Stadium scoring (park factor, total residual)", S, "T", ["stadium_total_r"], level="game")
    add("Coach pair scoring (total residual)", S, "T", ["coach_pair_total_r"], level="game")
    K = "Primetime and kickoff time"
    add("Kickoff slot: late, night (total)", K, "T", ["slot_late", "slot_night"], level="game")
    add("Day of week: Thu, Sat, Mon (total)", K, "T", ["thu", "sat", "mon"], level="game")
    add("SNF, MNF, TNF separately (total)", K, "T", ["snf", "mnf", "tnf"], level="game")
    add("Home edge in SNF, MNF, TNF", K, "P", ["snf", "mnf", "tnf"], level="game", mode="home")
    add("Home edge by slot (late, night)", K, "P", ["slot_late", "slot_night"], level="game", mode="home")
    add("Home edge by day (Thu, Sat, Mon)", K, "P", ["thu", "sat", "mon"], level="game", mode="home")
    add("Team's primetime residual history", K, "P", ["team_prime_r"], opp=True)
    add("Team's residual in this slot", K, "P", ["team_slot_r"], opp=True)
    add("Coach's primetime residual history", K, "P", ["coach_prime_r"], opp=True)
    add("Coach's residual in this slot", K, "P", ["coach_slot_r"], opp=True)
    add("QB's primetime residual history", K, "P", ["qb_prime_r"], opp=True)
    add("QB's residual in this slot", K, "P", ["qb_slot_r"], opp=True)
    add("Holidays: Thanksgiving, Christmas (total)", K, "T", ["thanksgiving", "christmas"], level="game")
    add("Home edge on Thanksgiving", K, "P", ["thanksgiving"], level="game", mode="home")
    add("Saturday late-season games (total)", K, "T", ["sat_late"], level="game")
    add("Home edge in Saturday late-season games", K, "P", ["sat_late"], level="game", mode="home")
    add("Body clock: West Coast team at 1pm ET", K, "P", ["bc_early_west"], opp=True)
    add("Body clock: East Coast team late at night vs a western team", K, "P", ["bc_late_east"], opp=True)
    add("Body clock: night-game time-zone edge", K, "P", ["bc_night_edge"])
    add("Primetime road team off a short week", K, "P", ["prime_road_short"], opp=True)
    add("First game after SNF or MNF", K, "P", ["after_prime"], opp=True)
    add("Night game outdoors (total)", K, "T", ["night_outdoor"], level="game")
    add("Night and cold (total)", K, "T", ["night_cold"], level="game")
    add("Night and wind (total)", K, "T", ["night_wind"], level="game")
    R = "Referees"
    add("Referee x team (margin residual)", R, "P", ["ref_team_r"], opp=True)
    add("Referee x team (points residual)", R, "P", ["ref_team_pts"], opp=True)
    add("Referee x team at home / on the road", R, "P", ["ref_team_venue"], opp=True)
    add("Referee home-team residual (market-free home cover)", R, "P", ["ref_home_r"])
    add("Referee x model favourite", R, "P", ["ref_fav_r"])
    add("Referee x division game (home residual)", R, "P", ["ref_div_home"])
    add("Referee total residual (vs the model, total)", R, "T", ["ref_total_r"], level="game")
    add("Referee flags per game (total)", R, "T", ["ref_flags"], level="game")
    add("Referee penalty yards per game (total)", R, "T", ["ref_yards"], level="game")
    add("Referee pace: plays per game (total)", R, "T", ["ref_pace"], level="game")
    add("Referee x primetime (total residual)", R, "T", ["ref_prime_total_r"], level="game")
    add("First-year referee (total)", R, "T", ["ref_new"], level="game")
    add("Home edge with a first-year referee", R, "P", ["ref_new"], level="game", mode="home")
    W = "Weather"
    add("Re-check: drop rain (points)", W, "DP", ["rain"]); add("Re-check: drop wind (points)", W, "DP", ["wind_out"])
    add("Re-check: drop cold (points)", W, "DP", ["cold"]); add("Re-check: drop warm-or-dome team in cold", W, "DP", ["warm_in_cold"])
    add("Re-check: drop dome (points)", W, "DP", ["dome"])
    add("Re-check: drop rain (total)", W, "DT", ["rain"]); add("Re-check: drop wind (total)", W, "DT", ["wind_out"])
    add("Re-check: drop cold (total)", W, "DT", ["cold"]); add("Re-check: drop dome (total)", W, "DT", ["dome"])
    add("Snow (total)", W, "T", ["snow"], level="game")
    add("Snow (points)", W, "P", ["snow"], level="game", mode="same")
    add("Temperature, open air (total)", W, "T", ["temp_out"], level="game")
    add("Rain on grass / rain on turf (total)", W, "T", ["rain_grass", "rain_turf"], level="game")
    add("Warm-or-dome team in wind", W, "P", ["wd_wind"], opp=True)
    add("Warm-or-dome team in rain", W, "P", ["wd_rain"], opp=True)
    add("Warm-or-dome team in snow", W, "P", ["wd_snow"], opp=True)
    add("Cold-weather team in a dome in December+", W, "P", ["cold_team_dome"], opp=True)
    add("Travel x cold", W, "P", ["miles_cold"], opp=True)
    add("Time-zone shift x cold", W, "P", ["tz_cold"], opp=True)
    add("Pass-heavy team in wind", W, "P", ["passoe_wind"], opp=True)
    add("Pass-heavy teams in wind (total)", W, "T", ["passoe_wind_sum"], level="game")
    add("QB's bad-weather residual history", W, "P", ["qb_badwx_r"], opp=True)
    add("Wind x referee flag rate (total)", W, "T", ["wind_refflags"], level="game")
    J = "Injuries"
    add("Re-check: drop QB out", J, "DP", ["qb_out"]); add("Re-check: drop skill value out (both)", J, "DP", ["skill_out_value", "opp_skill_out_value"])
    add("Re-check: drop snaps out (both)", J, "DP", ["off_snap_out", "opp_def_snap_out"]); add("Re-check: drop QB out (total)", J, "DT", ["qb_out_sum"])
    add("Injuries x bye / short week", J, "P", ["inj_bye", "inj_short"])
    add("Injuries x travel", J, "P", ["inj_miles"])
    add("Injuries x wind (OL out, skill value out)", J, "P", ["ol_wind", "skill_wind"])
    add("Injuries x primetime", J, "P", ["inj_prime"])
    add("OL starters out x opponent pass rush", J, "P", ["ol_x_rush"])
    add("Opponent secondary starters out (and x own passing)", J, "P", ["opp_db_out", "opp_db_x_pass"])
    add("Opponent front-seven starters out (and x own rushing)", J, "P", ["opp_front_out", "opp_front_x_rush"])
    add("Top two receivers both out", J, "P", ["wr12_out"])
    add("Backup QB: QB out x his rating, x his experience", J, "P", ["qbout_x_rating", "qbout_x_exp"])
    add("Injuries on both sides (own defense, opponent offense)", J, "P", ["def_snap_out", "opp_off_snap_out"])
    add("Coach's residual when missing starters", J, "P", ["coach_inj_r"], opp=True)
    add("Injuries on both teams (total)", J, "T", ["snap_out_all"], level="game")
    C = "Coaching matchups"
    add("Scheme: pass rate over expected, shotgun, no-huddle; opponent sack rate", C, "P", ["pass_oe_r", "shotgun_r", "nohuddle_r", "opp_def_sack_r"])
    add("Pass rate over expected x opponent sack rate", C, "P", ["passoe_x_rush"], opp=True)
    add("Offense vs man/zone, weighted by the defense's man rate (last season)", C, "P", ["cov_match"], opp=True)
    add("Offense vs blitz, weighted by the defense's blitz rate (last season)", C, "P", ["blitz_match"], opp=True)
    add("Run offense vs light box, weighted by the defense's light-box rate (last season)", C, "P", ["box_match"], opp=True)
    add("Head coach vs the defense's coverage family (residual history)", C, "P", ["coach_vs_family"], opp=True)
    add("Scheme pace: shotgun and no-huddle (total)", C, "T", ["shotgun_sum", "nohuddle_sum"], level="game")
    return I


# ---------------------------------------------------------------------------------------------- building the inputs
def hist_ratio(L, keys, num, den, k, prior):
    """(sum num + k prior) / (sum den + k) over the key's earlier weeks."""
    from experiments.situational_feats import hist
    a, n = hist(L, keys, num, k=0.0, return_n=True)       # a = sum/n when k=0
    b, _ = hist(L, keys, den, k=0.0, return_n=True)
    sn, sd = np.nan_to_num(a * n), np.nan_to_num(b * n)
    return (sn + k * prior) / (sd + k)


def build_long():
    from experiments import situational_feats as SF
    games = GAMES
    bp = pd.read_parquet(SCR / "base_2014.parquet")
    f0 = M.with_trends(pd.read_parquet(OUT / "features_asof.parquet"))
    fp = M.prep(f0)
    L, notes = SF.build(games, bp, fp, log=log)
    log("long table", L.shape)
    played = L.pf.notna(); reg = L.game_type == "REG"
    # trends (injuries, rain/snow) onto the long table
    tr = pd.read_parquet(OUT / "trends_asof.parquet")[["game_id", "team", "rain", "snow", "off_snap_out", "def_snap_out", "ol_out"]]
    L = L.merge(tr, on=["game_id", "team"], how="left")
    # play-by-play per team-game
    pb = SF.pbp_team_game(); log("pbp", pb.shape)
    L = L.merge(pb, on=["game_id", "team"], how="left")
    tg = pd.read_parquet(OUT / "team_games.parquet", columns=["game_id", "team", "pass_oe", "def_sack_rate", "plays"])
    L = L.merge(tg, on=["game_id", "team"], how="left")
    L = L.reset_index(drop=True)
    L["shotgun_r"] = SF._roll_prior(L, "shotgun"); L["nohuddle_r"] = SF._roll_prior(L, "no_huddle")
    L["pass_oe_r"] = SF._roll_prior(L, "pass_oe"); L["def_sack_r"] = SF._roll_prior(L, "def_sack_rate")
    for c in ["shotgun_r", "nohuddle_r", "pass_oe_r", "def_sack_r"]:
        L[c] = (L[c] - L.groupby("season")[c].transform("mean")).fillna(0.0)   # against the league that season (a level shift only)
    # coach 4th-down go rate, shrunk (K = 40 opportunities) to the previous season's league rate
    lg4 = L[played & (L.season >= 2012)].groupby("season").apply(lambda x: x.go4.sum() / max(1.0, x.opp4.sum()), include_groups=False)
    prior4 = L.season.map(lambda s: lg4.get(s - 1, lg4.get(2012)))
    L["go4"], L["opp4"] = L.go4.fillna(0.0), L.opp4.fillna(0.0)
    from experiments.situational_feats import hist
    sg, ng = hist(L, ["coach"], "go4", k=0.0, contrib=played & (L.season >= 2012), return_n=True)
    so, _ = hist(L, ["coach"], "opp4", k=0.0, contrib=played & (L.season >= 2012), return_n=True)
    L["coach_go4"] = (np.nan_to_num(sg * ng) + 40 * prior4) / (np.nan_to_num(so * ng) + 40) - prior4
    # injuries by position
    ig = SF.injury_groups(games); log("injury groups", ig.shape)
    L = L.merge(ig, on=["game_id", "team"], how="left")
    # participation, last season only
    pp = SF.participation_prev(); log("participation", pp.shape)
    pn = pp.assign(season=pp.season + 1)
    Lo = L[["season", "team"]].merge(pn, on=["season", "team"], how="left")
    Ld = L[["season", "opp"]].merge(pn.rename(columns={"team": "opp"}), on=["season", "opp"], how="left")
    cov = Lo.epa_man * Ld.man_rate + Lo.epa_zone * (1 - Ld.man_rate) - Lo.epa_pass
    bl = Lo.epa_blitz * Ld.blitz_rate + Lo.epa_noblitz * (1 - Ld.blitz_rate) - Lo.epa_db
    bx = Lo.epa_light * Ld.light_rate + Lo.epa_heavy * (1 - Ld.light_rate) - Lo.epa_run
    L["cov_match"], L["blitz_match"], L["box_match"] = cov.fillna(0.0).values, bl.fillna(0.0).values, bx.fillna(0.0).values
    med = pn.groupby("season").man_rate.median()
    fam = np.where(Ld.man_rate.isna(), None, np.where(Ld.man_rate.values > L.season.map(med).values, "man", "zone"))
    L["opp_family"] = fam
    L["coach_vs_family"] = hist(L, ["coach", "opp_family"], "r_pf", contrib=played)
    notes["participation_seasons"] = sorted(pp.dropna(subset=["man_rate"]).season.unique().tolist())
    # weather history for QBs: open-air games under 35F, 15+ mph, rain or snow
    outdoor = L.roof.fillna("outdoors").isin(["outdoors", "open"])
    bad = outdoor & ((L.temp < 35) | (L.wind >= 15) | (L.rain == 1) | (L.snow == 1))
    L["badwx"] = bad.astype(float)
    L["qb_badwx_hist"] = hist(L, ["qb"], "r_pf", contrib=played & bad)
    L["coach_inj_hist"] = hist(L, ["coach"], "r_pf", contrib=played & (L.off_snap_out >= 1.0))
    # referee game-level readings (home rows contribute once per game; deviations from the previous season's league mean)
    box = pd.read_parquet(OUT / "team_box.parquet", columns=["game_id", "team", "off_penalties", "off_penalty_yards"])
    L = L.merge(box, on=["game_id", "team"], how="left")
    gsum = L.groupby("game_id")[["off_penalties", "off_penalty_yards", "plays"]].transform("sum", min_count=2)
    for c, src in [("g_flags", "off_penalties"), ("g_yards", "off_penalty_yards"), ("g_plays", "plays")]:
        L[c] = gsum[src]
        lgm = L[L.home == 1].groupby("season")[c].mean()
        L[c + "_dev"] = L[c] - L.season.map(lambda s: lgm.get(s - 1, np.nan))
    hrow = (L.home == 1) & played
    L["ref_total_r"] = hist(L, ["referee"], "r_total", contrib=hrow)
    L["ref_flags"] = hist(L, ["referee"], "g_flags_dev", contrib=hrow)
    L["ref_yards"] = hist(L, ["referee"], "g_yards_dev", contrib=hrow)
    L["ref_pace"] = hist(L, ["referee"], "g_plays_dev", contrib=hrow)
    L["ref_prime_total_r"] = hist(L, ["referee"], "r_total", contrib=hrow & (L.prime == 1)) * L.prime
    first_season = L[L.referee.notna()].groupby("referee").season.min()
    L["ref_new"] = (L.referee.map(first_season) == L.season).astype(float) * (L.season > 1999)
    L["stadium_total_r"] = hist(L, ["stadium_id"], "r_total", contrib=hrow)
    L["pair"] = [("|".join(sorted([a, b])) if isinstance(a, str) and isinstance(b, str) else None) for a, b in zip(L.coach, L.opp_coach)]
    L["coach_pair_total_r"] = hist(L, ["pair"], "r_total", contrib=hrow)
    L = L.copy(); L.to_parquet(SCR / "long.parquet", index=False); (SCR / "notes.json").write_text(json.dumps(notes, default=str))
    log("long saved", L.shape)
    return L, fp, notes


def stage_build():
    if (SCR / "long.parquet").exists() and os.environ.get("SG_REUSE_LONG"):
        L = pd.read_parquet(SCR / "long.parquet"); fp = M.prep(M.with_trends(pd.read_parquet(OUT / "features_asof.parquet")))
        notes = json.loads((SCR / "notes.json").read_text()) if (SCR / "notes.json").exists() else {}
    else:
        L, fp, notes = build_long()

    # ---------- onto the model's team rows (fp) and the game frame
    keep = ["cvc", "coach_vs_team", "team_vs_team", "qb_vs_team", "coach_career", "coach_at_stadium", "team_at_stadium", "road_at_stadium", "team_on_surface",
            "surf_mismatch", "dome_team_out", "out_team_in_dome", "miles", "tz_east", "tz_west", "road_streak", "miles_2wk", "altitude", "coach_tenure_l",
            "first_year_coach", "coach_exp_l", "coach_go4", "clinched", "clinched_final", "eliminated", "rematch_r", "coach_vs_former", "qb_vs_former", "next_prime",
            "team_prime_r", "team_slot_r", "coach_prime_r", "coach_slot_r", "qb_prime_r", "qb_slot_r", "bc_early_west", "bc_late_east", "bc_night_edge", "after_prime",
            "ref_team_r", "ref_team_pts", "ref_team_venue", "ref_home_r", "ref_fav_r", "ref_div_home", "shotgun_r", "nohuddle_r", "pass_oe_r", "def_sack_r",
            "cov_match", "blitz_match", "box_match", "coach_vs_family", "db_out", "front_out", "wr12_out", "qb_badwx_hist", "coach_inj_hist", "prime", "go4", "opp4",
            "tz_shift_v", "gd", "badwx"]
    L["tz_shift_v"] = L.tz_shift
    clash = [c for c in keep if c in fp.columns]
    assert not clash, clash
    X = L[["game_id", "team"] + keep].drop_duplicates(["game_id", "team"])
    fpx = fp.merge(X, on=["game_id", "team"], how="left")
    assert len(fpx) == len(fp)
    num = [c for c in keep if c != "gd"]
    fpx[num] = fpx[num].astype(float).fillna(0.0)
    # derived team-level columns (on the prepped rows, so the live weather readings are used as the model reads them)
    fpx["rest_diff"] = (fpx.rest - fpx.opp_rest).clip(-7, 7)
    fpx["off_bye"] = (fpx.rest >= 13).astype(float); fpx["short_week"] = (fpx.rest <= 5).astype(float)
    away = (fpx.home == 0) | (fpx.neutral == 1)
    fpx["prime_road_short"] = ((fpx.home == 0) & (fpx.prime == 1) & (fpx.rest <= 6)).astype(float)
    wd = fpx.team.isin(M.WARM_OR_DOME).astype(float)
    fpx["wd_wind"] = wd * fpx.wind_out; fpx["wd_rain"] = wd * fpx.rain; fpx["wd_snow"] = wd * fpx.snow
    month = pd.to_datetime(fpx.gd).dt.month.fillna(9)
    fpx["cold_team_dome"] = ((1 - wd) * (fpx.home == 0) * (fpx.dome == 1) * ((month >= 12) | (month <= 2))).astype(float)
    fpx["miles_cold"] = fpx.miles * fpx.cold; fpx["tz_cold"] = fpx.tz_shift_v.abs() * fpx.cold
    fpx["passoe_wind"] = fpx.pass_oe_r * fpx.wind_out
    bad_now = ((fpx.dome == 0) & ((fpx.cold == 1) | (fpx.wind_out >= 15) | (fpx.rain == 1) | (fpx.snow == 1))).astype(float)
    fpx["qb_badwx_r"] = fpx.qb_badwx_hist * bad_now
    fpx["coach_inj_r"] = fpx.coach_inj_hist * (fpx.off_snap_out >= 1.0)
    fpx["inj_bye"] = fpx.off_snap_out * fpx.off_bye; fpx["inj_short"] = fpx.off_snap_out * fpx.short_week
    fpx["inj_miles"] = fpx.off_snap_out * fpx.miles; fpx["inj_prime"] = fpx.off_snap_out * fpx.prime
    fpx["ol_wind"] = fpx.ol_out * fpx.wind_out; fpx["skill_wind"] = fpx.skill_out_value * fpx.wind_out
    def opp_of(col):
        m = fpx.set_index(["game_id", "team"])[col]
        return m.reindex(pd.MultiIndex.from_arrays([fpx.game_id, fpx.opp])).fillna(0.0).values
    fpx["opp_def_sack_r"] = opp_of("def_sack_r")
    fpx["ol_x_rush"] = fpx.ol_out * fpx.opp_def_sack_r
    fpx["opp_db_out"] = opp_of("db_out"); fpx["opp_db_x_pass"] = fpx.opp_db_out * (fpx.off_pass_epa - fpx.off_pass_epa.mean())
    fpx["opp_front_out"] = opp_of("front_out"); fpx["opp_front_x_rush"] = fpx.opp_front_out * (fpx.off_rush_epa - fpx.off_rush_epa.mean())
    fpx["opp_off_snap_out"] = opp_of("off_snap_out")
    # the starter's career dropbacks before this game
    q = pd.read_parquet(OUT / "qb_games.parquet", columns=["qb_id", "season", "week", "dropbacks"]).sort_values(["season", "week"])
    q["cum"] = q.groupby("qb_id").dropbacks.cumsum() - q.dropbacks
    qd = {k: (x.season.values * 100 + x.week.values, x.cum.values, x.dropbacks.values) for k, x in q.groupby("qb_id")}
    def prior_db(qid, s, w):
        v = qd.get(qid)
        if v is None:
            return 0.0
        i = np.searchsorted(v[0], s * 100 + w)   # games strictly before
        return float(v[1][i - 1] + v[2][i - 1]) if i > 0 else 0.0
    fpx["qb_exp_l"] = [np.log1p(prior_db(a, s, w)) for a, s, w in zip(fpx.qb_id, fpx.season, fpx.week)]
    fpx["qbout_x_rating"] = fpx.qb_out * fpx.qb_rating.fillna(0.0); fpx["qbout_x_exp"] = fpx.qb_out * fpx.qb_exp_l
    fpx["passoe_x_rush"] = fpx.pass_oe_r * fpx.opp_def_sack_r
    fpx = fpx.drop(columns=["gd"])
    # ---------- game-level raw values (from the home row; sums over both teams where named _sum)
    Lh = L[L.home == 1].drop_duplicates("game_id").set_index("game_id")
    GC = pd.DataFrame(index=fpx.loc[fpx.home == 1, "game_id"].values)
    for c in ["turf", "roof_open", "roof_closed", "intl", "slot_late", "slot_night", "thu", "sat", "mon", "snf", "mnf", "tnf", "thanksgiving", "christmas", "sat_late",
              "ref_total_r", "ref_flags", "ref_yards", "ref_pace", "ref_prime_total_r", "ref_new", "stadium_total_r", "coach_pair_total_r", "night"]:
        GC[c] = Lh[c].reindex(GC.index).astype(float).fillna(0.0).values
    GC["altitude_game"] = Lh.elev.reindex(GC.index).ge(4000).astype(float).values
    fh = fpx[fpx.home == 1].set_index("game_id"); fa = fpx[fpx.home == 0].set_index("game_id")
    ids = GC.index.intersection(fa.index); GC = GC.loc[ids]
    def both(c):
        return (fh.loc[ids, c] + fa.loc[ids, c]).values
    for c in ["surf_mismatch", "dome_team_out", "out_team_in_dome", "miles", "short_week", "off_bye"]:
        GC[c + "_sum"] = both(c)
    GC["tz_abs_sum"] = (fh.loc[ids, "tz_shift_v"].abs() + fa.loc[ids, "tz_shift_v"].abs()).values
    GC["go4_sum"] = both("coach_go4")
    GC["div_game"] = fh.loc[ids, "div_game"].values
    GC["snow"] = fh.loc[ids, "snow"].values
    GC["temp_out"] = np.where(fh.loc[ids, "dome"] == 1, 0.0, fh.loc[ids, "temp"].fillna(60.0) - 60.0)
    rain = fh.loc[ids, "rain"].values; turf = GC.turf.values
    GC["rain_grass"] = rain * (1 - turf); GC["rain_turf"] = rain * turf
    outdoor = (fh.loc[ids, "dome"] == 0).astype(float).values
    GC["night_outdoor"] = GC.night.values * outdoor; GC["night_cold"] = GC.night.values * fh.loc[ids, "cold"].values
    GC["night_wind"] = GC.night.values * fh.loc[ids, "wind_out"].values
    GC["passoe_wind_sum"] = both("pass_oe_r") * fh.loc[ids, "wind_out"].values
    GC["wind_refflags"] = fh.loc[ids, "wind_out"].values * GC.ref_flags.values
    GC["snap_out_all"] = both("off_snap_out") + both("def_snap_out") if "def_snap_out" in fh.columns else both("off_snap_out")
    GC["shotgun_sum"] = both("shotgun_r"); GC["nohuddle_sum"] = both("nohuddle_r")
    GC["season"] = fh.loc[ids, "season"].values
    GC.index.name = "game_id"
    fpx.to_parquet(SCR / "fp.parquet", index=False); GC.to_parquet(SCR / "gc.parquet")
    (SCR / "notes.json").write_text(json.dumps(notes, default=str))
    log("built", fpx.shape, GC.shape)


# ------------------------------------------------------------------------------------------------- running an idea
_W = {}


def _load():
    if not _W:
        from threadpoolctl import threadpool_limits
        _W["tl"] = threadpool_limits(limits=1)
        _W["fp"] = pd.read_parquet(SCR / "fp.parquet")
        _W["gc"] = pd.read_parquet(SCR / "gc.parquet")
        _W["G0"] = game_frame(_W["fp"])
        _W["G0"]["total_line"] = _W["G0"].index.map(GAMES.set_index("game_id").total_line)
        _W["base"] = pd.read_parquet(SCR / "base.parquet")
    return _W


def _shuffle_within_season(values: np.ndarray, seasons: np.ndarray, rng) -> np.ndarray:
    out = values.copy()
    for s in np.unique(seasons):
        ix = np.where(seasons == s)[0]
        out[ix] = values[rng.permutation(ix)]
    return out


def materialise(idea: dict, fp: pd.DataFrame, gc: pd.DataFrame, seed=None):
    """The idea's columns on the team rows (points) or the game frame (total); shuffled within season if seed."""
    rng = np.random.default_rng(seed) if seed is not None else None
    fp = fp.copy(); newcols = []
    if idea["eq"] in ("DP", "DT"):
        return fp, None, []
    if idea["eq"] == "P" and idea["level"] == "team":
        vals = fp[idea["cols"]].values.astype(float)
        if rng is not None:
            perm_rows = np.empty(len(fp), int)
            for s in np.unique(fp.season.values):
                ix = np.where(fp.season.values == s)[0]; perm_rows[ix] = rng.permutation(ix)
            vals = vals[perm_rows]
        for j, c in enumerate(idea["cols"]):
            fp[c] = vals[:, j]; newcols.append(c)
        if idea["opp"]:
            m = fp.set_index(["game_id", "team"])[idea["cols"]]
            o = m.reindex(pd.MultiIndex.from_arrays([fp.game_id, fp.opp])).fillna(0.0)
            for c in idea["cols"]:
                fp["opp_" + c] = o[c].values; newcols.append("opp_" + c)
        return fp, None, newcols
    g = gc[idea["cols"]].copy()
    if rng is not None:
        g[:] = _shuffle_within_season(g.values.astype(float), gc.season.values, rng)
    if idea["eq"] == "P":
        v = g.reindex(fp.game_id.values).fillna(0.0).values
        mult = {"same": np.ones(len(fp)), "home": fp.home.values.astype(float), "sign": np.where(fp.home.values == 1, 1.0, -1.0)}[idea["mode"]]
        for j, c in enumerate(idea["cols"]):
            name = f"{c}_{idea['mode']}"; fp[name] = v[:, j] * mult; newcols.append(name)
        return fp, None, newcols
    return fp, g, [f"x_{c}" for c in idea["cols"]]


def _slug(name: str) -> str:
    import hashlib
    return hashlib.md5(name.encode()).hexdigest()[:12]


def run_idea(idea: dict, seed=None, keep_pred=False) -> dict:
    W = _load(); t0 = time.time()
    fp, g, cols = materialise(idea, W["fp"], W["gc"], seed)
    eq = idea["eq"]
    if eq in ("P", "DP"):
        feats = BASE_FEATS + cols if eq == "P" else [c for c in BASE_FEATS if c not in idea["cols"]]
        P = lean_walk_forward(fp, W["G0"], feats, BASE_TOTAL, points=True, total=False)
    else:
        G = W["G0"].copy()
        if eq == "T":
            for c, n in zip(idea["cols"], cols):
                G[n] = g[c].reindex(G.index).fillna(0.0).values
            tf = BASE_TOTAL + cols
        else:
            tf = [c for c in BASE_TOTAL if c not in idea["cols"]]
        P = lean_walk_forward(fp, G, BASE_FEATS, tf, points=False, total=True)
    P = finish(P, W["base"])
    out = {"name": idea["name"], "seed": -1 if seed is None else seed, "secs": round(time.time() - t0, 1), **flat(score(P))}
    if seed is None:
        out.update(reading(idea, fp, g, cols))
        if keep_pred:
            P.to_parquet(SCR / "preds" / f"{_slug(idea['name'])}.parquet", index=False)
    return out


def reading(idea, fp, g, cols) -> dict:
    """Effect sizes, for the report: each column's points per unit and per standard deviation in the live equation fit
    on every regular-season game 2013-2025 with the idea added, and the share of games where it is not zero."""
    if idea["eq"] in ("DP", "DT") or not cols:
        return {}
    tr = fp[fp.pf.notna() & (fp.game_type == "REG") & fp.season.between(2013, 2025)]
    if idea["eq"] == "P":
        feats = BASE_FEATS + cols
        m = make_pipeline(StandardScaler(), Ridge(alpha=M.RIDGE)).fit(tr[feats].values, tr.pf.values)
        coef = m[-1].coef_ / m[0].scale_; sd = m[0].scale_
        nz = {c: float((tr[c] != 0).mean()) for c in cols}
    else:
        G = _W["G0"].copy()
        for c, n in zip(idea["cols"], cols):
            G[n] = g[c].reindex(G.index).fillna(0.0).values
        G = G[G.total.notna() & G.season.between(2013, 2025)]
        feats = BASE_TOTAL + cols
        m = make_pipeline(StandardScaler(), Ridge(alpha=10.0)).fit(G[feats].values, G.total.values)
        coef = m[-1].coef_ / m[0].scale_; sd = m[0].scale_
        nz = {c: float((G[c] != 0).mean()) for c in cols}
    d = dict(zip(feats, zip(coef, sd)))
    return {"coefs": "; ".join(f"{c}: {d[c][0]:+.3f}/unit, {d[c][0] * d[c][1]:+.3f}/sd, nonzero {nz[c]:.0%}" for c in cols)}


# ------------------------------------------------------------------------------------------------------------ stages
def stage_base():
    """The base walk-forward, fresh trees, 2014-2025 (2014 feeds the residual histories; 2015-2025 is scored), and the
    engine checked against M.walk_forward."""
    f0 = M.with_trends(pd.read_parquet(OUT / "features_asof.parquet")); fp = M.prep(f0)
    from threadpoolctl import threadpool_limits
    with threadpool_limits(limits=1):
        G = game_frame(fp); G["total_line"] = G.index.map(GAMES.set_index("game_id").total_line)
        # check 1: a random candidate, one season, against M.walk_forward (fresh trees in both)
        rng = np.random.default_rng(7); fp["_chk"] = rng.normal(size=len(fp))
        M.FEATS = BASE_FEATS + ["_chk"]
        try:
            ref = M.walk_forward(fp, [2019])   # prep() is idempotent on prepped rows
        finally:
            M.FEATS = list(BASE_FEATS)
        mine = lean_walk_forward(fp, G, BASE_FEATS + ["_chk"], BASE_TOTAL, seasons=[2019])
        j = mine.merge(ref[ref.game_type == "REG"][["game_id", "model_spread", "model_total", "p_home", "p_over_emp"]], on="game_id", suffixes=("", "_ref"))
        chk = {c: float((j[c] - j[c + "_ref"]).abs().max()) for c in ["model_spread", "model_total", "p_home", "p_over_emp"]}
        chk["games"] = int(len(j)); log("engine check vs M.walk_forward (2019, random candidate):", chk)
        fp = fp.drop(columns=["_chk"])
        t0 = time.time()
        base = finish(lean_walk_forward(fp, G, BASE_FEATS, BASE_TOTAL, seasons=range(2014, 2026)))
        log("base run", round(time.time() - t0), "s")
    base.to_parquet(SCR / "base_2014.parquet", index=False)
    base[base.season >= 2015].to_parquet(SCR / "base.parquet", index=False)
    live = pd.read_parquet(OUT / "pred_v3.parquet")
    j = base.merge(live[["game_id", "model_spread", "model_total"]], on="game_id", suffixes=("", "_live"))
    chk["fresh_vs_cached_trees_spread_max"] = float((j.model_spread - j.model_spread_live).abs().max())
    chk["fresh_vs_cached_trees_spread_mean"] = float((j.model_spread - j.model_spread_live).abs().mean())
    chk["total_vs_live_max"] = float((j.model_total - j.model_total_live).abs().max())
    live_s = score(finish(live[(live.game_type == "REG") & live.season.between(2015, 2025)][["game_id", "season", "week", "model_spread", "model_total", "p_home", "p_over_emp"]].copy()))
    chk["live_pred_v3_scores"] = live_s
    (SCR / "engine_check.json").write_text(json.dumps(chk, default=float, indent=1))
    log("check", json.dumps({k: v for k, v in chk.items() if k != "live_pred_v3_scores"}))


def _done(path, key="name"):
    if not path.exists():
        return set()
    d = pd.read_csv(path)
    return set(d[key]) if key == "name" else set(zip(d.name, d.seed))


def _append(path, rows):
    df = pd.DataFrame(rows)
    df.to_csv(path, mode="a", header=not path.exists(), index=False)


def stage_real(jobs, only=None):
    from joblib import Parallel, delayed
    (SCR / "preds").mkdir(exist_ok=True)
    path = SCR / "real.csv"
    todo = [i for i in ideas() if i["name"] not in _done(path) and (only is None or i["name"] in only)]
    if "(base)" not in _done(path):
        b = {"name": "(base)", "seed": -1, "secs": 0.0, **flat(score(pd.read_parquet(SCR / "base.parquet"))), "coefs": ""}; _append(path, [b])
    # the slow ones (points ideas refit the trees) first, so the pool stays full
    todo.sort(key=lambda i: 0 if i["eq"] in ("P", "DP") else 1)
    log("real runs to do:", len(todo))
    for k in range(0, len(todo), jobs * 2):
        chunk = todo[k:k + jobs * 2]
        from experiments.situational_game import run_idea as RI   # by reference, not the __main__ copy
        rows = Parallel(n_jobs=jobs, backend="loky")(delayed(RI)(i, None, True) for i in chunk)
        _append(path, rows)
        for r in rows:
            log("done", r["name"], r["secs"], "s")


def verdicts(real: pd.DataFrame) -> pd.DataFrame:
    """Rules 1 and 2 against the base row."""
    b = real[real.name == "(base)"].iloc[0]; I = {i["name"]: i for i in ideas()}
    rows = []
    for _, r in real[real.name != "(base)"].iterrows():
        i = I.get(r["name"]); eq = i["eq"] if i else "P"
        v = {"name": r["name"]}
        for w in WINDOWS:
            v[f"d_team_{w}"] = r[f"team_mae_{w}"] - b[f"team_mae_{w}"]
            v[f"d_total_{w}"] = r[f"total_mae_{w}"] - b[f"total_mae_{w}"]
            v[f"d_margin_{w}"] = r[f"margin_mae_{w}"] - b[f"margin_mae_{w}"]
            v[f"d_sp_{w}"] = (r[f"sp_w_{w}"] - r[f"sp_l_{w}"]) - (b[f"sp_w_{w}"] - b[f"sp_l_{w}"])
            v[f"d_to_{w}"] = (r[f"to_w_{w}"] - r[f"to_l_{w}"]) - (b[f"to_w_{w}"] - b[f"to_l_{w}"])
            v[f"d_ll_{w}"] = r[f"ll_cal_{w}"] - b[f"ll_cal_{w}"]
            v[f"d_llraw_{w}"] = r[f"ll_raw_{w}"] - b[f"ll_raw_{w}"]
            v[f"d_brier_{w}"] = r[f"brier_cal_{w}"] - b[f"brier_cal_{w}"]
            v[f"d_mlu_{w}"] = r[f"ml_units_{w}"] - b[f"ml_units_{w}"]
        tot = eq in ("T", "DT")
        v["rule1"] = all(v[f"d_team_{w}"] < 0 for w in WINDOWS) and (not tot or all(v[f"d_total_{w}"] < 0 for w in WINDOWS))
        v["rule2"] = all(v[f"d_sp_{w}"] >= 0 and v[f"d_to_{w}"] >= 0 and v[f"d_ll_{w}"] <= 1e-9 for w in WINDOWS)
        rows.append(v)
    return pd.DataFrame(rows)


def stage_placebo(jobs, names=None, draws=N_PLACEBO, stop_at=STOP_AT, tag="placebo"):
    """Within-season shuffles of the idea's columns; stops an idea once `stop_at` draws beat it on some window."""
    from joblib import Parallel, delayed
    real = pd.read_csv(SCR / "real.csv"); V = verdicts(real)
    if names is None:
        names = list(V[V.rule1 & V.rule2].name)
    I = {i["name"]: i for i in ideas()}
    path = SCR / f"{tag}.csv"
    b = real[real.name == "(base)"].iloc[0]
    for name in names:
        i = I[name]; key = "total_mae" if i["eq"] == "T" else "team_mae"
        r = real[real.name == name].iloc[0]
        gain = {w: b[f"{key}_{w}"] - r[f"{key}_{w}"] for w in WINDOWS}
        done = pd.read_csv(path) if path.exists() else pd.DataFrame(columns=["name", "seed"])
        have = done[done.name == name]
        seeds = [s for s in range(1000, 1000 + draws) if s not in set(have.seed)]
        def beaten(df):
            return int(sum(any(b[f"{key}_{w}"] - x[f"{key}_{w}"] >= gain[w] for w in WINDOWS) for _, x in df.iterrows()))
        nb = beaten(have) if len(have) else 0
        log("placebo", name, "draws to run", len(seeds), "beaten so far", nb)
        for k in range(0, len(seeds), jobs):
            if nb >= stop_at:
                break
            from experiments.situational_game import run_idea as RI
            rows = Parallel(n_jobs=jobs, backend="loky")(delayed(RI)(i, s) for s in seeds[k:k + jobs])
            _append(path, rows); nb += beaten(pd.DataFrame(rows))
            log("  ", name, "draws", len(have) + k + len(rows), "beaten", nb)


def stage_combo(jobs):
    real = pd.read_csv(SCR / "real.csv"); V = verdicts(real)
    pl = pd.read_csv(SCR / "placebo.csv") if (SCR / "placebo.csv").exists() else pd.DataFrame()
    passed = [n for n in V[V.rule1 & V.rule2].name if placebo_summary(n, real, pl)["pass"]]
    log("passing all three:", passed)
    if not passed:
        (SCR / "combo.json").write_text(json.dumps({"passed": []})); return
    I = {i["name"]: i for i in ideas()}
    W = _load(); fp, G = W["fp"].copy(), W["G0"].copy(); pcols, tcols = [], []
    for n in passed:
        i = I[n]; fp2, g, cols = materialise(i, fp, W["gc"])
        if i["eq"] == "P":
            for c in cols:
                fp[c] = fp2[c]
            pcols += cols
        else:
            for c, nn in zip(i["cols"], cols):
                G[nn] = g[c].reindex(G.index).fillna(0.0).values
            tcols += cols
    P = lean_walk_forward(fp, G, BASE_FEATS + pcols, BASE_TOTAL + tcols, points=bool(pcols), total=bool(tcols))
    P = finish(P, W["base"])
    res = {"name": "All passing ideas together", "seed": -1, **flat(score(P))}
    (SCR / "combo.json").write_text(json.dumps({"passed": passed, "result": res}, default=float))
    log("combo", res)


def placebo_summary(name, real, pl) -> dict:
    I = {i["name"]: i for i in ideas()}; i = I[name]; key = "total_mae" if i["eq"] == "T" else "team_mae"
    b = real[real.name == "(base)"].iloc[0]; r = real[real.name == name].iloc[0]
    gain = {w: b[f"{key}_{w}"] - r[f"{key}_{w}"] for w in WINDOWS}
    x = pl[pl.name == name] if len(pl) else pl
    if not len(x):
        return {"draws": 0, "beaten": None, "pct": {}, "pass": False}
    pg = {w: (b[f"{key}_{w}"] - x[f"{key}_{w}"]).values for w in WINDOWS}
    beaten = int(sum(any(pg[w][k] >= gain[w] for w in WINDOWS) for k in range(len(x))))
    pct = {w: float((pg[w] < gain[w]).mean()) for w in WINDOWS}
    ok = len(x) >= N_PLACEBO and beaten <= N_PLACEBO - 45
    return {"draws": int(len(x)), "beaten": beaten, "pct": pct, "pass": bool(ok)}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", required=True)
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--names", default=None)
    ap.add_argument("--draws", type=int, default=N_PLACEBO)
    ap.add_argument("--tag", default="placebo")
    a = ap.parse_args()
    names = a.names.split("||") if a.names else None
    if a.stage == "base":
        stage_base()
    elif a.stage == "build":
        stage_build()
    elif a.stage == "real":
        stage_real(a.jobs, names)
    elif a.stage == "placebo":
        stage_placebo(a.jobs, names, a.draws, tag=a.tag)
    elif a.stage == "combo":
        stage_combo(a.jobs)
    elif a.stage == "report":
        from experiments.situational_report import write_report
        write_report()
