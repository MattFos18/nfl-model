"""Export everything the model sees, per team, for the data room page (web/).

Writes web/data/meta.js (column dictionary, coefficients per season, teams, pull log, verification) and
web/data/<TEAM>.js, one per team, each `window.TEAMDATA["KC"] = {...}` with one row per game holding:
the box score counts (features.py), the EPA stats (build.py), the ratings the team carried into the game
(ratings.py), the trend readings (trends.py), and the model's prediction and the closing line.

Usage: python -m nflmodel.export_web
"""
from __future__ import annotations
import json
import numpy as np, pandas as pd
from pathlib import Path
from . import model as M

ROOT = Path(__file__).resolve().parent.parent
OUT, RAW, WEB = ROOT / "data" / "processed", ROOT / "data" / "raw", ROOT / "web" / "data"
REP = ROOT / "reports"

# name -> (group, definition, source, used by 3.0?, used by the old sheet?)
BASE = {
    "pf": ("Result", "Points scored", "schedule", True, True), "pa": ("Result", "Points allowed", "schedule", True, True),
    "margin": ("Result", "Points scored minus allowed", "schedule", False, False),
    "spread_line": ("Line", "Closing spread, home team's view (positive = home favoured)", "schedule (nflverse closing line)", False, True),
    "total_line": ("Line", "Closing total", "schedule", False, True), "implied_pf": ("Line", "Vegas implied points for this team from the spread and total", "schedule", False, False),
    "implied_pa": ("Line", "Vegas implied points against", "schedule", False, False), "team_spread": ("Line", "Closing spread from this team's view", "schedule", False, False),
    "rest": ("Situation", "Days since the previous game", "schedule", True, False), "dome": ("Situation", "Roof closed or dome", "schedule", True, False),
    "temp": ("Situation", "Temperature at kickoff, F (blank for domes)", "schedule", True, False), "wind": ("Situation", "Wind at kickoff, mph", "schedule", True, False),
    "div_game": ("Situation", "Division game", "schedule", True, False), "slot": ("Situation", "Kickoff window", "schedule", False, False),
    "primetime": ("Situation", "TNF, SNF or MNF", "schedule", True, False), "referee": ("Situation", "Referee", "schedule", False, True),
    "qb_name": ("Situation", "Starting quarterback", "schedule", True, False), "coach": ("Situation", "Head coach", "schedule", False, True),
    "plays": ("EPA stats", "Pass and run plays with an EPA value", "play-by-play", True, False),
    "epa_play": ("EPA stats", "Expected points added per play. The main rating stat", "play-by-play", True, False),
    "success": ("EPA stats", "Share of plays with positive EPA", "play-by-play", False, False),
    "pass_epa": ("EPA stats", "EPA per dropback", "play-by-play", True, False), "pass_success": ("EPA stats", "Success rate on passes", "play-by-play", False, False),
    "pass_plays": ("EPA stats", "Dropbacks", "play-by-play", False, False), "rush_epa": ("EPA stats", "EPA per designed run", "play-by-play", True, False),
    "rush_success": ("EPA stats", "Success rate on runs", "play-by-play", False, False), "rush_plays": ("EPA stats", "Designed runs", "play-by-play", False, False),
    "early_down_epa": ("EPA stats", "EPA per play on first and second down", "play-by-play", False, False), "early_down_success": ("EPA stats", "Success rate on early downs", "play-by-play", False, False),
    "explosive_rate": ("EPA stats", "Share of plays gaining 20+ passing or 12+ rushing", "play-by-play", False, False),
    "pass_rate": ("EPA stats", "Share of plays that were passes", "play-by-play", False, False), "pass_oe": ("EPA stats", "Pass rate over expected (nflverse xpass)", "play-by-play", False, False),
    "cpoe": ("EPA stats", "Completion % over expected", "play-by-play", False, False), "air_yards_att": ("EPA stats", "Air yards per attempt", "play-by-play", False, False),
    "sack_rate": ("EPA stats", "Sacks per dropback", "play-by-play", False, False), "int_rate": ("EPA stats", "Interceptions per pass", "play-by-play", False, False),
    "turnovers": ("EPA stats", "Interceptions plus fumbles lost on scrimmage plays", "play-by-play", False, False), "turnover_rate": ("EPA stats", "Turnovers per play", "play-by-play", False, False),
    "yards_play": ("EPA stats", "Yards per play", "play-by-play", False, True), "third_conv": ("EPA stats", "Third down conversion rate", "play-by-play", False, True),
    "rz_plays": ("EPA stats", "Plays inside the 20", "play-by-play", False, False), "rz_epa": ("EPA stats", "EPA per play inside the 20", "play-by-play", False, False),
    "drives": ("Drives", "Drives (kneel-only drives excluded, as PFR does)", "play-by-play", False, True), "score_rate": ("Drives", "Share of drives ending in a TD or FG (PFR Sc%)", "play-by-play", False, True),
    "td_rate": ("Drives", "Share of drives ending in a TD", "play-by-play", False, False), "drive_to_rate": ("Drives", "Share of drives ending in a turnover", "play-by-play", False, False),
    "rz_drive_rate": ("Drives", "Share of drives reaching the 20", "play-by-play", False, False), "rz_td_rate": ("Drives", "Share of red zone drives ending in a TD", "play-by-play", False, True),
    "sec_per_play": ("Drives", "Seconds per offensive play (pace)", "play-by-play", False, False), "fg_att": ("Drives", "Field goal attempts", "play-by-play", False, False),
    "fg_made": ("Drives", "Field goals made", "play-by-play", False, False), "avg_start_ytg": ("Drives", "Average drive start, yards to the goal line", "play-by-play", False, True),
    # box score
    "off_plays": ("Box score", "Scrimmage plays (pass + run, no two-point tries)", "play-by-play", False, True), "off_yards": ("Box score", "Scrimmage yards", "play-by-play", False, True),
    "off_pass_att": ("Box score", "Pass attempts (no sacks or two-point tries; spikes count). Matches PFR", "play-by-play", False, True),
    "off_completions": ("Box score", "Completions. Matches PFR", "play-by-play", False, True), "off_pass_yards": ("Box score", "Gross passing yards", "play-by-play", False, True),
    "off_pass_td": ("Box score", "Passing TDs. Matches PFR", "play-by-play", False, True), "off_interceptions": ("Box score", "Interceptions thrown. Matches PFR", "play-by-play", False, True),
    "off_sacks": ("Box score", "Sacks taken", "play-by-play", False, True), "off_sack_yards": ("Box score", "Yards lost on sacks", "play-by-play", False, True),
    "off_rush_att": ("Box score", "Rush attempts incl. kneels, no two-point tries", "play-by-play", False, True), "off_rush_yards": ("Box score", "Rushing yards", "play-by-play", False, True),
    "off_rush_td": ("Box score", "Rushing TDs. Matches PFR", "play-by-play", False, True), "off_fumbles_lost": ("Box score", "Fumbles lost by this team on any play", "play-by-play", False, True),
    "off_first_downs": ("Box score", "First downs: rush + pass + penalty", "play-by-play", False, True), "off_third_conv": ("Box score", "Third downs converted. Matches PFR", "play-by-play", False, True),
    "off_third_fail": ("Box score", "Third downs failed", "play-by-play", False, True), "off_fourth_conv": ("Box score", "Fourth downs converted", "play-by-play", False, True),
    "off_fourth_fail": ("Box score", "Fourth downs failed", "play-by-play", False, True), "off_penalties": ("Box score", "Penalties committed (offense and defense)", "play-by-play", False, True),
    "off_penalty_yards": ("Box score", "Penalty yards", "play-by-play", False, True), "off_kickoffs": ("Box score", "Kickoffs", "play-by-play", False, False),
    "off_ko_yards": ("Box score", "Kickoff distance, total", "play-by-play", False, True), "off_fg_att": ("Box score", "Field goal attempts", "play-by-play", False, False),
    "off_fg_made": ("Box score", "Field goals made", "play-by-play", False, False), "off_xp_made": ("Box score", "Extra points made", "play-by-play", False, False),
    "off_drives": ("Box score", "Drives", "play-by-play", False, True), "off_scoring_drives": ("Box score", "Drives ending in a TD or FG", "play-by-play", False, True),
    "off_td_drives": ("Box score", "Drives ending in a TD", "play-by-play", False, False), "off_rz_trips": ("Box score", "Red zone trips (drives reaching the 20)", "play-by-play", False, True),
    "off_rz_tds": ("Box score", "Red zone TDs", "play-by-play", False, True), "off_to_drives": ("Box score", "Drives ending in a turnover", "play-by-play", False, False),
    "off_start_own_sum": ("Box score", "Sum of drive start yardlines (own side)", "play-by-play", False, True), "off_start_n": ("Box score", "Drives with a known start", "play-by-play", False, False),
    # ratings
    "r_off_epa_play": ("Ratings into the game", "Offense EPA/play rating: how much better than average after opponents, decay and shrinkage", "ratings.py", True, False),
    "r_def_epa_play": ("Ratings into the game", "Opponent's defense EPA/play rating (positive = good defense)", "ratings.py", True, False),
    "r_own_def_epa_play": ("Ratings into the game", "This team's own defense EPA/play rating", "ratings.py", True, False),
    "r_opp_off_epa_play": ("Ratings into the game", "Opponent's offense EPA/play rating", "ratings.py", True, False),
    "r_off_pass_epa": ("Ratings into the game", "Offense pass EPA rating", "ratings.py", True, False), "r_def_pass_epa": ("Ratings into the game", "Opponent defense pass EPA rating", "ratings.py", True, False),
    "r_off_rush_epa": ("Ratings into the game", "Offense rush EPA rating", "ratings.py", True, False), "r_def_rush_epa": ("Ratings into the game", "Opponent defense rush EPA rating", "ratings.py", True, False),
    "r_off_pf": ("Ratings into the game", "Offense points rating (adjusted points per game above average)", "ratings.py", True, False),
    "r_def_pf": ("Ratings into the game", "Opponent defense points rating", "ratings.py", True, False),
    "r_off_plays": ("Ratings into the game", "Pace rating, plays above average", "ratings.py", True, False), "r_def_plays": ("Ratings into the game", "Opponent defense pace rating", "ratings.py", True, False),
    "r_opp_off_plays": ("Ratings into the game", "Opponent offense pace rating", "ratings.py", True, False),
    "r_off_success": ("Ratings into the game", "Offense success-rate rating (computed, dropped from the regression)", "ratings.py", False, False),
    "r_def_success": ("Ratings into the game", "Opponent defense success-rate rating (not used)", "ratings.py", False, False),
    "qb_rating": ("Ratings into the game", "Starting QB's career EPA per dropback, decayed and shrunk", "ratings.py", True, False),
    "opp_qb_rating": ("Ratings into the game", "Opponent's starting QB rating", "ratings.py", True, False),
    "n_games": ("Ratings into the game", "Games played this season before this one", "ratings.py", False, False),
    "opp_rest": ("Situation", "Opponent's days since its previous game", "schedule", True, False),
    # trends
    "team_home_edge": ("Trends (shown, not used)", "Home minus away margin over 3 seasons, halved, shrunk", "trends.py", False, True),
    "h2h_cover": ("Trends (shown, not used)", "Cover margin in the last 6 meetings, this team's view, shrunk. Persists, weak", "trends.py", False, True),
    "coach_ats": ("Trends (shown, not used)", "Coach's career cover margin per game, shrunk. Noise", "trends.py", False, True),
    "qb_ats": ("Trends (shown, not used)", "QB's career cover margin per game, shrunk. Noise", "trends.py", False, True),
    "off_loss": ("Trends (shown, not used)", "Lost the previous game", "trends.py", False, True),
    "ref_over": ("Trends (shown, not used)", "Referee's over rate before this game, shrunk to 0.5. Noise", "trends.py", False, True),
    "ref_home_cover": ("Trends (shown, not used)", "Referee's home cover rate, shrunk. Noise", "trends.py", False, True),
    "ref_pen": ("Trends (shown, not used)", "Referee's penalties per game vs league, shrunk", "trends.py", False, True),
    "ref_tot": ("Totals", "Referee's game totals against the league's mean total of the season before, previous games, shrunk (a reading; out of the total equation since 2 Oct 2026)", "trends.py", False, True),
    "sun_late": ("Trends (shown, not used)", "Sunday late window", "trends.py", False, True), "body_clock_early": ("Trends (shown, not used)", "West Coast team at 1pm ET on the road", "trends.py", False, True),
    "cold_edge": ("Trends (shown, not used)", "Team's cold-game margin edge, applied when cold", "trends.py", False, True),
    "rain": ("Situation", "Rain, showers or a storm at kickoff (play-by-play weather text; the forecast for unplayed games)", "play-by-play / Open-Meteo", True, False),
    "snow": ("Trends (shown, not used)", "Snow, flurries or sleet in the play-by-play weather text (outdoor games)", "play-by-play", False, False),
    "travel_miles": ("Trends (shown, not used)", "Miles from the team's home stadium to the venue (0 at home)", "trends.py", False, False),
    "tz_shift": ("Trends (shown, not used)", "Time zones crossed to reach the venue, hours (positive = east; 0 at home)", "trends.py", False, False),
    "wind_edge": ("Trends (shown, not used)", "Team's windy-game margin edge, applied when windy", "trends.py", False, True),
    "off_home_split": ("Trends (shown, not used)", "Home minus away EPA/play, shrunk", "trends.py", False, True),
    "off_starters_out": ("Injuries", "Offense starters (50%+ snaps last game) listed Out/Doubtful", "injuries + snap counts", False, True),
    "def_starters_out": ("Injuries", "Defense starters listed Out/Doubtful", "injuries + snap counts", False, True),
    "qb_out": ("Injuries", "Last game's starting QB listed Out/Doubtful", "injuries + snap counts", True, True),
    "ol_out": ("Injuries", "Last game's offensive line starters (T, G, C) listed Out/Doubtful or on IR", "injuries + rosters + snap counts", False, True),
    "off_snap_out": ("Injuries", "Share of last game's offensive snaps that belonged to players now out (sum of their snap %)", "injuries + rosters + snap counts", False, True),
    "def_snap_out": ("Injuries", "Share of last game's defensive snaps that belonged to players now out (sum of their snap %)", "injuries + rosters + snap counts", False, True),
    "opp_def_snap_out": ("Injuries", "The opponent's defensive snaps out (the same measure, other side)", "injuries + rosters + snap counts", True, True),
    "off_continuity": ("Situation", "Share of last season's offensive snaps taken by players on this week's active roster", "rosters + snap counts", False, True),
    "def_continuity": ("Situation", "Share of last season's defensive snaps taken by players on this week's active roster", "rosters + snap counts", False, True),
    "off_turnover_early": ("Situation", "Offseason turnover on offense (1 minus the continuity share), weeks 1 to 8", "rosters + snap counts", True, True),
    "opp_def_turnover_early": ("Situation", "The opponent's offseason turnover on defense, weeks 1 to 8", "rosters + snap counts", True, True),
    "skill_out_value": ("Injuries", "Value lost to RB/WR/TE listed Out/Doubtful: EPA per touch above replacement x touch share, summed (player model)", "injuries + play-by-play", True, True),
    "opp_skill_out_value": ("Injuries", "The opponent's value lost to its RB/WR/TE listed out", "injuries + play-by-play", True, True),
    # model
    "m_exp_pf": ("Model", "3.0 expected points for this team", "model.py", False, False), "m_exp_pa": ("Model", "3.0 expected points against", "model.py", False, False),
    "m_win": ("Model", "3.0 win probability: the raw chance (the card shows it calibrated, picks.home_calibration, 27 Sep 2026)", "model.py", False, False), "m_cover": ("Model", "3.0 probability of covering the closing spread", "model.py", False, False),
    "m_total_adj": ("Model", "the share-out that makes the two team scores add up to the game total's own equation: expected points = the equation + the blend's pull + this", "model.py", False, False),
    "m_blend_adj": ("Model", f"the other {len(M.BLEND_LABEL) - 1} models' average pull on this team's expected points (the blend, 25 Sep 2026): expected points = the equation's number + this", "model.py", False, False),
    "m_over": ("Model", "3.0 probability the game goes over the closing total, read off the training games' own total misses (pushes left out): the raw chance the totals flag reads (the card shows it calibrated, picks.over_calibration, 27 Sep 2026)", "model.py", False, False),
}


def used_by_v3(col: str):
    """Whether a column feeds the current model, derived from model.FEATS so the page's markers follow the input set."""
    F = set(M.FEATS)
    if col.startswith("r_"):
        return col[2:] in F
    raw = {"pf": True, "pa": True, "home": True, "epa_play": True, "def_epa_play": True, "qb_name": True, "qb_rating": True, "qb_out": "qb_out" in F,
           "dome": "dome" in F or "dome" in M.TOTAL_FEATS, "wind": "wind_out" in F, "rain": "rain" in F, "snow": "snow" in F, "warm_in_cold": "warm_in_cold" in F, "temp": "cold" in F, "rest": "rest_short" in F or "rest_long" in F,
           "opp_rest": "opp_rest_short" in F or "opp_rest_long" in F, "div_game": "div_game" in F, "primetime": "primetime" in F,
           "pass_epa": "off_pass_epa" in F, "def_pass_epa": "def_pass_epa" in F, "rush_epa": "off_rush_epa" in F, "def_rush_epa": "def_rush_epa" in F,
           "plays": "off_plays" in F, "def_plays": "def_plays" in F, "opp_qb_rating": "opp_qb_rating" in F, "success": "off_success" in F, "def_success": "def_success" in F}
    return bool(raw.get(col, False))


def describe(col: str):
    if col.startswith("mf_"): return _describe_mf(col)
    out = _describe(col)
    out["used_v3"] = used_by_v3(col)
    return out


def _describe_mf(col: str):
    f = col[3:]; lab = {"off_epa_play": "offense EPA rating", "def_epa_play": "the opponent's defense EPA rating", "off_pf": "offense points rating", "def_pf": "the opponent's defense points rating", "qb_rating": "the starter's QB rating", "home": "home (1) or away (0)", "neutral": "neutral site", "dome": "dome or closed roof", "wind_out": "wind at kickoff, mph, outdoors", "cold": "under 35F outdoors", "rain": "rain at kickoff", "warm_in_cold": "warm-climate or dome team in the cold", "div_game": "division game", "qb_out": "starting QB out", "skill_out_value": "value of RB/WR/TE listed out", "opp_skill_out_value": "the opponent's", "off_snap_out": "offense snaps listed out", "opp_def_snap_out": "the opponent's defense snaps listed out", "off_turnover_early": "offseason turnover, offense (weeks 1 to 8)", "opp_def_turnover_early": "the opponent's, defense", "dead_late": "out of the race (week 12 on)", "opp_dead_late": "the opponent out of the race"}.get(f, f)
    return {"definition": f"Model input as the regression saw it: {lab}. The Game deep dive's rows use exactly these values.", "source": "model.prep on the as-of features", "group": "Model inputs", "used_v3": True}


def _describe(col: str):
    if col.startswith("box_"):
        return _describe(col[4:])
    if col in BASE:
        g, d, s, u3, uo = BASE[col]
        return {"group": g, "definition": d, "source": s, "used_v3": u3, "used_old": uo}
    if col.startswith("def_") and col[4:] in BASE:
        g, d, s, u3, uo = BASE[col[4:]]
        return {"group": g + " (allowed)", "definition": "Allowed by this team's defense: " + d[0].lower() + d[1:], "source": s, "used_v3": u3, "used_old": uo}
    if col.endswith("_ng") and col[:-3] in BASE:
        g, d, s, u3, uo = BASE[col[:-3]]
        return {"group": g + ", garbage time removed", "definition": d + " (win probability between 10% and 90% only)", "source": s, "used_v3": False, "used_old": False}
    if col.startswith("def_") and col.endswith("_ng") and col[4:-3] in BASE:
        g, d, s, u3, uo = BASE[col[4:-3]]
        return {"group": g + " (allowed), garbage time removed", "definition": "Allowed: " + d, "source": s, "used_v3": False, "used_old": False}
    return {"group": "Other", "definition": col, "source": "", "used_v3": False, "used_old": False}


def clean(v):
    if isinstance(v, (np.floating, float)):
        return None if np.isnan(v) else round(float(v), 3)
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.bool_, bool)):
        return bool(v)
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return None
    if isinstance(v, pd.Timestamp):
        return v.strftime("%Y-%m-%d")
    return v


def team_home_edges(tg: pd.DataFrame) -> dict:
    """Each team's raw home-minus-away margin, 2013 to the last full season, and how well the first half predicts the second.
    Shown beside the matchup tool; tested as an input (32 home-by-team terms) and rejected, so it is a reading."""
    t = tg[tg.pf.notna() & (tg.season >= 2013) & (tg.game_type == "REG")].copy()
    last = int(t.season.max())
    if t[t.season == last].week.max() < 18:
        last -= 1
    t = t[t.season <= last]
    t["mg"] = t.pf - t.pa
    def edges(x):
        h = x.groupby(["team", "home"]).mg.mean().unstack()
        return (h[1.0] - h[0.0]) if 1.0 in h.columns and 0.0 in h.columns else pd.Series(dtype=float)
    e = edges(t)
    mid = (2013 + last) // 2
    e1, e2 = edges(t[t.season <= mid]), edges(t[t.season > mid])
    return {"seasons": f"2013 to {last}", "league": round(float(e.mean()), 2), "corr_halves": round(float(e1.corr(e2)), 3),
            "teams": {k: round(float(v), 2) for k, v in e.items()}}


def situation_facts(feats: pd.DataFrame) -> dict:
    """Raw averages behind every situational input, recomputed on each export: points scored with the flag on vs off,
    2013 to the last completed season, regular season, plus wind in buckets. The page shows these next to the fitted
    coefficient so a reader can see the raw gap the regression started from."""
    f = M.prep(feats)
    last = int(f[f.pf.notna()].season.max())
    if (f[(f.season == last) & f.pf.notna()].week.max() or 0) < 18:
        last -= 1   # the season in progress is not a full season
    f = f[f.pf.notna() & (f.season >= 2013) & (f.season <= last) & (f.game_type == "REG")]
    out = {"seasons": f"2013 to {last}", "team_games": int(len(f)), "flags": {}, "wind": []}
    for k in M.SIT_FEATS:
        if k == "wind_out" or k not in f.columns:
            continue
        on, off = f[f[k] == 1], f[f[k] == 0]
        out["flags"][k] = {"n_on": int(len(on)), "on": round(float(on.pf.mean()), 2), "off": round(float(off.pf.mean()), 2), "diff": round(float(on.pf.mean() - off.pf.mean()), 2)}
    for lo, hi, lab in [(-1, 0, "0 (indoors or calm)"), (0, 5, "1 to 5"), (5, 10, "6 to 10"), (10, 15, "11 to 15"), (15, 99, "16+")]:
        x = f[(f.wind_out > lo) & (f.wind_out <= hi)]
        out["wind"].append({"bucket": lab, "n": int(len(x)), "pf": round(float(x.pf.mean()), 2)})
    # the tested-and-not-used situations, raw: points scored and the margin against the closing spread with the flag on vs off
    out["tested"] = {}
    for k in ["neutral", "dome", "rain", "div_game", "qb_out", "snow", "primetime", "rest_short", "rest_long", "body_clock_early"]:   # neutral, dome, rain, div_game, qb_out left the model 3 Oct 2026
        if k not in f.columns:
            continue
        on, off = f[f[k] == 1], f[f[k] == 0]
        out["tested"][k] = {"n_on": int(len(on)), "pf_on": round(float(on.pf.mean()), 2), "pf_off": round(float(off.pf.mean()), 2),
                            "ats_on": round(float(((on.pf - on.pa) > -on.spread_line * np.where(on.home == 1, 1, -1)).mean()), 3) if "spread_line" in f.columns else None}
    for k, edges, labs in [("travel_miles", [-1, 0, 500, 1000, 1500, 9000], ["home", "1 to 500", "501 to 1000", "1001 to 1500", "1500+"]),
                           ("tz_shift", [-9, -2.5, -0.5, 0.5, 2.5, 9], ["3 west", "1 to 2 west", "none", "1 to 2 east", "3 east"])]:
        if k not in f.columns:
            continue
        out[k] = []
        for lo, hi, lab in zip(edges[:-1], edges[1:], labs):
            x = f[(f[k] > lo) & (f[k] <= hi)]
            out[k].append({"bucket": lab, "n": int(len(x)), "pf": round(float(x.pf.mean()), 2) if len(x) else None})
    return out


def write_games_js(games: pd.DataFrame, since: int = 2013):
    """Every game since `since` (regular season and playoffs) with the score, closing line, coaches, starting QBs and
    stadium, for the page's head-to-head section: last meetings, the two coaches, the two QBs, this stadium, recent
    form. Names are interned so the file stays small. None of it feeds the model (all tested; see Inputs explained)."""
    g = games[games.season >= since].sort_values(["season", "week", "gameday"]).copy()
    names = {}
    def iid(v):
        if v is None or (isinstance(v, float) and np.isnan(v)):
            return None
        v = str(v)
        if v not in names:
            names[v] = len(names)
        return names[v]
    cols = ["game_id", "season", "week", "type", "gameday", "home", "away", "hs", "as", "spread", "total", "hcoach", "acoach", "hqb", "aqb", "stadium", "roof", "neutral"]
    rows = []
    for r in g.itertuples():
        rows.append([r.game_id, int(r.season), int(r.week), str(r.game_type), str(r.gameday)[:10], r.home_team, r.away_team, clean(r.home_score), clean(r.away_score),
                     clean(r.spread_line), clean(r.total_line), iid(r.home_coach), iid(r.away_coach), iid(r.home_qb_name), iid(r.away_qb_name), iid(r.stadium),
                     r.roof if isinstance(r.roof, str) else None, int(bool(getattr(r, "neutral", 0)))])
    (WEB / "games.js").write_text("window.GAMES=" + json.dumps({"cols": cols, "names": list(names), "rows": rows}, default=clean, separators=(",", ":")) + ";")
    print("games.js", len(rows), "games", (WEB / "games.js").stat().st_size / 1e6, "MB")


def noise_floor() -> dict:
    """The paired-bootstrap noise floor on the team points miss, as nflmodel/audit.py writes it into reports/audit.md
    (section 5): the half-width of the 90% interval, median on the tuning window, largest there, and median held out.
    The page quotes this one figure wherever it says a change is inside the noise."""
    import re
    f = REP / "audit.md"
    m = re.search(r"plus or minus ([\d.]+) points wide on the tuning window \(largest ([\d.]+)\) and ([\d.]+) on the held-out window", f.read_text()) if f.exists() else None
    return {"tune": float(m.group(1)), "tune_max": float(m.group(2)), "test": float(m.group(3)), "source": "reports/audit.md"} if m else {}


def props_payload(pj: Path) -> str:
    """props.json as the page reads it; the rule's constants a props run before 26 Sep 2026 did not write are added from
    nflmodel/props.py (the values that props run used), so the page never shows a stand-in."""
    from . import props as PR_
    d = json.loads(pj.read_text())
    d.setdefault("targetable", PR_.TARGETABLE); d.setdefault("wind_from", PR_.WIND_FROM); d.setdefault("med_tier", PR_.MED_TIER)   # 27 Sep 2026: the round-15 median curve
    return json.dumps(d, separators=(",", ":"))


def data_from() -> dict:
    """The first season each nflverse source has (nflmodel/pull.py DATASETS): the page says "since" these."""
    from . import pull as PL_
    return {k: v[1] for k, v in PL_.DATASETS.items()}


def model_constants(feats: pd.DataFrame) -> dict:
    """The model's fixed settings the page describes, from the modules that use them."""
    from . import weather as WX, trends as TR, season as SE
    return {"ridge": M.RIDGE, "train_from": M.TRAIN_FROM, "early_weeks": M.EARLY_WEEKS, "late_week": M.LATE_WEEK, "dead_pct": M.DEAD_PCT, "cold_f": M.COLD_F,
            "wind_fill": round(float(feats.wind.median()), 2),   # model.prep's stand-in for an unknown wind (the median wind in the features)
            "use_within_days": WX.USE_WITHIN_DAYS, "rain_prob": TR.RAIN_PROB, "rain_mm": TR.RAIN_MM, "zero_feats": M.SIT_FEATS + M.INJ_FEATS + M.CONT_FEATS + M.LATE_FEATS}   # the inputs a breakdown measures from zero, not from the league average


def player_model_constants() -> dict:
    """The player model's settings (players.py, positions.py, ratings.py): the skill value behind "points if out" and
    each group's replacement level behind "vs an average starter"."""
    from . import players as PL, positions as PO, ratings as RA
    return {"decay": PL.DEFAULT["decay"], "k": PL.DEFAULT["k"], "rank_k": PL.RANK["k"], "usage_games": PL.DEFAULT["usage_games"], "skill_pct": PL.DEFAULT["pct"], "repl_pct": PO.REPL_PCT,
            "qb_prior": RA.DEFAULT["qb_prior"], "edge_press": PO.EDGE_PRESS, "min_plays_prior": 100,
            "starters": PO.STARTERS, "starters_def": PO.STARTERS_DEF, "starter_qb_games": PO.STARTER_QB_GAMES}


def week_fit(pv: pd.DataFrame, season: int, week: int) -> dict | None:
    """The fit that priced the week (the regression refit before it): coefficient, training mean, intercept, the margin
    and total spreads, how many team-games it learned from. Every game of the week carries the same one; the page's
    week-context numbers (points if out, points a game, the inputs table) read it from here."""
    x = pv[(pv.season == season) & (pv.week == week)]
    if not len(x) or f"coef_{M.FEATS[0]}" not in x.columns:
        return None
    r = x.iloc[0]; p6 = lambda v: None if pd.isna(v) else round(float(v), 6)
    return {"season": season, "week": week, "per_unit": {f: p6(r[f"coef_{f}"]) for f in M.FEATS}, "mean": {f: p6(r[f"mean_{f}"]) for f in M.FEATS}, "intercept": p6(r["intercept"]),
            "sigma_margin": p6(r.get("sigma_margin")), "sigma_total": p6(r.get("sigma_total")), "n_train": int(r["n_train"]) if "n_train" in r.index and pd.notna(r["n_train"]) else None, "train_from": M.TRAIN_FROM}


def matchup_matrix(f2: pd.DataFrame, season: int, week: int, teams: dict) -> dict:
    """Every pair of teams on a neutral field going into (season, week), priced the model's full way: the seven-model
    blend on each team's points and the game total from its own equation, shared out by the spread (model.walk_forward).
    The ratings and QB are the Rankings table's (`teams`); the situation is neutral, outdoors, the typical wind, nobody
    out, no offseason turnover or out-of-the-race flag, a league-average referee and each QB at his career level."""
    played = f2[f2.pf.notna() & (f2.season >= M.TRAIN_FROM) & ((f2.season < season) | ((f2.season == season) & (f2.week < week)))]
    ms = M.fit_blend(played, M.fit_points(played, M.RIDGE), M.RIDGE)
    names = sorted(teams); wind = float(f2.wind.median()) if "wind" in f2.columns else 0.0
    rows = []
    for a in names:
        for b in names:
            if a == b: continue
            A, B = teams[a], teams[b]
            r = {f: 0.0 for f in M.FEATS} | {"off_epa_play": A["off_epa_play"], "off_pf": A["off_pf"], "def_epa_play": B["def_epa_play"], "def_pf": B["def_pf"], "qb_rating": A["qb_rating"],
                                            "neutral": 1.0, "wind_out": wind, "off_success": A.get("off_success"), "def_success": B.get("def_success"), "off_pass_epa": A.get("off_pass_epa"),
                                            "def_pass_epa": B.get("def_pass_epa"), "off_rush_epa": A.get("off_rush_epa"), "def_rush_epa": B.get("def_rush_epa"), "off_plays": A.get("off_plays"), "def_plays": B.get("def_plays")}
            rows.append({"team": a, "opp": b, **r})
    x = pd.DataFrame(rows)
    x["pts"] = M.predict_blend(ms, x)["blend"].values
    # the total's own equation: each pair once, a as the listed first side (its home flag only pairs the rows)
    g = x[x.team < x.opp].copy(); h = g.assign(game_id=g.team + "_" + g.opp, pf=np.nan, home=1.0, qb_out=0.0, qb_form=0.0, ref_over=0.5, ref_tot=0.0, rain=0.0, cold=0.0, dome=0.0, div_game=0.0,
                                                skill_out_value=0.0, off_snap_out=0.0, off_turnover_early=0.0)
    back = x.set_index(["team", "opp"])
    aw = pd.DataFrame([{**back.loc[(o, t)].to_dict(), "team": o, "opp": t} for t, o in zip(g.team, g.opp)]).assign(game_id=h.game_id.values, pf=np.nan, home=0.0, qb_out=0.0, qb_form=0.0, ref_over=0.5, ref_tot=0.0, rain=0.0, cold=0.0,
                                                                                                                 dome=0.0, div_game=0.0, skill_out_value=0.0, off_snap_out=0.0, off_turnover_early=0.0)
    test = pd.concat([h, aw], ignore_index=True)
    th, ta = test[test.home == 1].set_index("game_id"), test[test.home == 0].set_index("game_id")
    tot = pd.Series(M.total_model(played, test), index=th.index.intersection(ta.index))   # total_model's own row order
    pts = {t: {} for t in names}
    for t, o, gid in zip(h.team, h.opp, h.game_id):
        a_, b_ = float(back.loc[(t, o), "pts"]), float(back.loc[(o, t), "pts"]); T = float(tot[gid])
        pts[t][o] = round((T + (a_ - b_)) / 2, 2); pts[o][t] = round((T - (a_ - b_)) / 2, 2)
    return {"season": season, "week": week, "wind": round(wind, 2), "pts": pts}



def round3_tests() -> dict:
    """The round-3 studies (reports/round3_rule.md) for the Model tab's Tested and not used: every game-model idea, and
    every props idea that got past rule 1, with the tally of the rest (29 Sep 2026, Matt: every finding on the site)."""
    R = ROOT / "reports"; W = ["2015-18", "2019-22", "2023-25"]; PW = ["2017-18", "2019-22", "2023-25"]
    num = lambda v, k=4: None if pd.isna(v) else round(float(v), k)
    out = {"game": [], "props": [], "props_tally": [], "weather": []}
    def short(v):   # the plain reason, first rule failed; the full text stays in the report
        v = str(v)
        if v.startswith("stays"): return "kept in the model"
        if v.startswith("passes"): return "passes every rule"
        rule = next((c for c in v if c in "12345"), "")
        return {"1": "no: not better on every window", "2": "no: costs bets or calibration", "3": "no: shuffled input did as well",
                "4": "no: data not available", "5": "no: fails when combined"}.get(rule, v)
    if (R / "situational_game.csv").exists():
        g = pd.read_csv(R / "situational_game.csv", low_memory=False)
        for r in g.to_dict("records"):
            tot = str(r["equation"]).startswith("total")
            out["game"].append({"family": r["family"], "idea": r["idea"], "eq": r["equation"],
                                "miss": [num(r.get(f"d_{'total' if tot else 'team'}_miss_{w}")) for w in W],
                                "bets": [num(r.get(f"d_{'totals' if tot else 'spread'}_wl_{w}"), 0) for w in W],
                                "placebo": None if pd.isna(r.get("placebo_draws")) or pd.isna(r.get("placebo_beaten")) else f"{int(r['placebo_beaten'])} of {int(r['placebo_draws'])}",
                                "verdict": short(r["verdict"])})
    if (R / "situational_props.csv").exists():
        p = pd.read_csv(R / "situational_props.csv", low_memory=False)
        p = p[p.family != "Together"]
        ok = p.rule1.astype(str).str.lower() == "true"
        out["props_tally"] = [{"family": f, "tests": int(len(d)), "rule1": int(ok[d.index].sum()), "all": int(d.verdict.astype(str).str.startswith("passes 1-3").sum())}
                              for f, d in p.groupby("family", sort=False)]
        for r in p[ok].to_dict("records"):
            out["props"].append({"family": r["family"], "idea": r["idea"], "variant": r["variant"], "stat": r["stat"],
                                 "miss": [num(r.get(f"diff_{w}")) for w in PW], "verdict": short(r["verdict"])})
    if (R / "weather_forecast.csv").exists():   # the forecast-weather candidates (30 Sep 2026), scored on the seasons the archive covers
        wf = pd.read_csv(R / "weather_forecast.csv", low_memory=False)
        for r in wf[wf.section == "candidate"].to_dict("records"):
            ok = lambda k: str(r.get(k)).lower() == "true"
            v = "passes every rule" if ok("rule1") and ok("rule2") and ok("rule3") else ("no: not better on every season" if not ok("rule1") else ("no: costs bets or calibration" if not ok("rule2") else "no: shuffled input did as well"))
            out["weather"].append({"idea": r["label"], "miss": [num(r.get(f"d_team_{y}")) for y in (2022, 2023, 2024, 2025)], "verdict": v})
    return out


def model_lineup(pred: pd.DataFrame, games: pd.DataFrame, f2: pd.DataFrame) -> dict:
    """Model tab, the seven models and the total model (29 Sep 2026, Matt: the tab showed only the one equation). Each
    model's own miss on every backtest window, read from the per-game predictions the walk-forward stored (pred_v3: every
    game priced with only earlier games), and the total equation as fitted on every game played so far."""
    from . import picks as P_
    ks = list(M.BLEND_LABEL)
    g = games.reset_index()[["game_id", "home_score", "away_score"]]
    d = pred.merge(g, on="game_id", how="left")
    d = d[(d.game_type == "REG") & d.home_score.notna() & d.away_score.notna()].copy()
    for s in ["home", "away"]:
        d[f"{s}_m_blend"] = d[[f"{s}_m_{k}" for k in ks]].mean(axis=1)
        d[f"{s}_pre"] = d[f"{s}_exp"] - d[f"{s}_total_adj"].fillna(0.0)
    wins = [(k, a, b) for k, (a, b) in P_.WINDOWS.items()]
    cur = int(d.season.max()); wins.append((str(cur), cur, cur))

    def miss(x, hcol, acol):
        pts = np.abs(np.r_[x[hcol] - x.home_score, x[acol] - x.away_score]).mean()
        mar = np.abs((x[hcol] - x[acol]) - (x.home_score - x.away_score)).mean()
        return round(float(pts), 3), round(float(mar), 3)

    what = {"ridge": f"The {len(M.FEATS)} inputs above, shrinkage {M.RIDGE:g}",
            "alpha3": f"The same inputs, less shrinkage ({M.BLEND['alpha3'][1]:g})", "alpha30": f"The same inputs, more shrinkage ({M.BLEND['alpha30'][1]:g})",
            "trees": f"Boosted trees on the same inputs ({M.TREES['max_iter']} trees, {M.TREES['max_leaf_nodes']} leaves each)"}
    extra_lab = {"off_success": "offense success rate", "def_success": "defense success rate allowed", "off_pass_epa": "offense pass EPA",
                 "def_pass_epa": "defense pass EPA allowed", "off_rush_epa": "offense rush EPA", "def_rush_epa": "defense rush EPA allowed",
                 "off_plays": "offense plays per game", "def_plays": "defense plays per game allowed"}
    for k, (extra, al) in M.BLEND.items():
        if extra:
            what[k] = "The same inputs plus " + ", ".join(extra_lab.get(c, c) for c in extra)
    rows = []
    for k in ks + ["blend"]:
        r = {"key": k, "label": "Average of the seven (used)" if k == "blend" else M.BLEND_LABEL[k].lstrip("+ ").capitalize(), "what": what.get(k, "")}
        for w, a, b in wins:
            x = d[(d.season >= a) & (d.season <= b)]
            r[f"pts_{w}"], r[f"margin_{w}"] = miss(x, f"home_m_{k}", f"away_m_{k}") if len(x) else (None, None)
            r[f"n_{w}"] = int(len(x))
        rows.append(r)
    tot = []
    for lab, fn in [("Total model (used)", lambda x: x.model_total), ("The two blend scores added", lambda x: x.home_pre + x.away_pre)]:
        r = {"label": lab}
        for w, a, b in wins:
            x = d[(d.season >= a) & (d.season <= b)]
            r[f"miss_{w}"] = round(float(np.abs(fn(x) - (x.home_score + x.away_score)).mean()), 3) if len(x) else None
        tot.append(r)
    played = f2[f2.pf.notna() & (f2.season >= M.TRAIN_FROM)]
    tr = M._game_frame(played)
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    from sklearn.linear_model import Ridge
    m = make_pipeline(StandardScaler(), Ridge(alpha=M.RIDGE)).fit(tr[M.TOTAL_FEATS].values, tr.total.values)
    lab = {"off_sum": "Both offenses' EPA ratings, added", "def_sum": "Both defenses' EPA ratings, added", "pf_sum": "Both offenses' points ratings, added",
           "pa_sum": "Both defenses' points ratings, added", "qb_sum": "Both starting QBs' ratings, added", "qb_out_sum": "Starting QBs out (0, 1 or 2)",
           "wind_out": "Wind, mph (0 in a dome)", "rain": "Rain at kickoff (1 or 0)", "rain_fc": "Forecast chance of rain 50%+ outdoors (1 or 0)", "cold": f"Below {M.COLD_F:g}°F outdoors (1 or 0)", "dome": "Dome or closed roof (1 or 0)",
           "ref_tot": "The referee's past game totals against the league, shrunk", "qb_form_sum": "Both QBs' form this season against their career rating"}
    coefs = [{"input": c, "label": lab.get(c, c), "per_unit": round(float(pu), 4), "mean": round(float(mu), 4), "per_sd": round(float(ps), 3)}
             for c, pu, mu, ps in zip(M.TOTAL_FEATS, m[-1].coef_ / m[0].scale_, m[0].mean_, m[-1].coef_)]
    last = played.sort_values(["season", "week"]).iloc[-1]
    return {"windows": [w for w, _, _ in wins], "models": rows, "totals": tot, "total_coefs": coefs, "total_intercept": round(float(tr.total.mean()), 3),
            "total_n": int(len(tr)), "total_through": f"{int(last.season)} Week {int(last.week)}", "total_ridge": M.RIDGE, "train_from": M.TRAIN_FROM}



def _add_splits(wk: list) -> None:
    """Each card's newest betting splits (data/lines/splits_latest.csv, written by splits.run every line watch): per market
    the share of bets and of money on each side, the side's line and odds, and when they were read. Display only: no split
    reaches the model. A game the page does not list has none."""
    f = ROOT / "data" / "lines" / "splits_latest.csv"
    if not f.exists():
        return
    try:
        s = pd.read_csv(f)
    except Exception:  # noqa
        return
    s = s[s.game_id.notna()]
    for g in wk:
        x = s[s.game_id == g["game_id"]]
        if not len(x):
            continue
        out = {"ts": str(x.ts.iloc[0]), "source": "DraftKings"}
        for m in ("spread", "total", "ml"):
            y = x[x.market == m]
            if len(y):
                out[m] = {str(r.side): {"bets": int(r.bets_pct), "money": int(r.handle_pct), "line": clean(r.line), "odds": clean(r.odds)} for r in y.itertuples()}
        g["splits"] = out


def _an_ts(x) -> str:
    """An Action Network time ('2026-09-28T05:30:36.5+00:00') in the line logs' format ('2026-09-28T05-30-36Z')."""
    return pd.to_datetime(x, utc=True).strftime("%Y-%m-%dT%H-%M-%SZ")


# a moneyline reverse move: the no-vig win chance moved this many percentage points from the open (2 Oct 2026, Matt:
# "track moneyline movement like we do for the total and the spread"); a 10-cent price change (-150 to -160) moves it
# about 1.5 to 2 points, so 3 marks a real move, not a price tweak. Display only
ML_MOVE_PTS = 3.0
RLM_PUBLIC = 70   # 3 Oct 2026 (Matt): a reverse line move needs 70%+ of bets on one side; at 59% there is no public side to move against


def _novig_home(hml, aml):
    """The home side's win chance in percent (one decimal) from the two moneylines with the vig removed; None without both
    or for an impossible price (between -100 and +100)."""
    def imp(m):
        return None if m is None or -100 < m < 100 else (-m / (-m + 100) if m < 0 else 100 / (m + 100))
    a, b = imp(hml), imp(aml)
    return None if a is None or b is None or a + b <= 0 else round(100 * a / (a + b), 1)


def _add_consensus(wk: list) -> None:
    """The market-wide picture on each card (1 Oct 2026, Matt: "just show consensus"), display only, never in the model:
    - consensus_history: Action Network's consensus line from its opening line to now (data/lines/books_log.csv, the
      line watch, a row whenever a book's number changes), home_spread in the schedule's sign (home favored > 0; Action
      Network's own sign is the other way), carried to the newest pull for the game so the chart runs to now;
    - splits: ScoresAndOdds' consensus bets and money shares (data/lines/splits_consensus_log.csv) replace DraftKings'
      where the game has them (DraftKings' stay for a game without);
      Each point also carries home_win, the home side's no-vig win chance from its two moneylines (the Win block's chart);
    - moves: the line moved from the open toward the side with fewer bets (half a point or more on the spread and total;
      ML_MOVE_PTS percentage points of no-vig win chance on the moneyline), the usual mark of bigger, sharper bets on the
      other side."""
    lnd = ROOT / "data" / "lines"
    fb, fs = lnd / "books_log.csv", lnd / "splits_consensus_log.csv"
    b = pd.read_csv(fb) if fb.exists() else pd.DataFrame(columns=["game_id", "book"])
    b = b[b.game_id.notna() & b.book.isin(["Consensus", "Open"])] if len(b) else b
    s = pd.read_csv(fs) if fs.exists() else pd.DataFrame(columns=["game_id"])
    s = s[s.game_id.notna()].sort_values("ts").drop_duplicates(["game_id", "market"], keep="last") if len(s) else s
    allb = pd.read_csv(fb, usecols=["ts", "game_id"]) if fb.exists() else pd.DataFrame(columns=["ts", "game_id"])

    def pt(t, src, r):
        hs = None if pd.isna(r.home_spread) else -float(r.home_spread)
        hm, am = clean(r.home_ml), clean(r.away_ml)
        return {"ts": t, "source": src, "home_spread": clean(hs), "total": clean(r.total), "home_ml": hm, "away_ml": am, "home_win": _novig_home(hm, am)}
    for g in wk:
        gid = g["game_id"]; x = b[b.game_id == gid].sort_values("ts") if len(b) else b
        cons = x[x.book == "Consensus"] if len(x) else x
        if len(cons):
            hist = []
            op = x[x.book == "Open"]
            if len(op):
                hist.append(pt(_an_ts(op.book_updated.iloc[-1]), "Open", op.iloc[-1]))
            hist += [pt(r.ts, "Consensus", r) for r in cons.itertuples()]
            newest = str(allb[allb.game_id == gid].ts.max())
            if newest > hist[-1]["ts"]:
                hist.append(dict(hist[-1], ts=newest))
            g["consensus_history"] = hist
        y = s[s.game_id == gid] if len(s) else s
        if len(y):
            out = {"ts": str(y.ts.max()), "source": "Consensus"}
            for r in y.itertuples():
                a, h = ("over", "under") if r.market == "total" else (str(r.away), str(r.home))
                out[r.market] = {a: {"bets": int(r.bets_a), "money": int(r.money_a), "line": clean(r.line_a), "odds": None},
                                 h: {"bets": int(r.bets_b), "money": int(r.money_b), "line": clean(r.line_b), "odds": None}}
            # the moneyline splits read against each side's price (3 Oct 2026, Matt): the newest consensus point with both
            # moneylines; none when the history has none
            mlp = [p for p in g.get("consensus_history") or [] if p.get("home_win") is not None]   # both prices, both possible
            if "ml" in out and mlp and str(g["home_team"]) in out["ml"] and str(g["away_team"]) in out["ml"]:
                out["ml"][str(g["home_team"])]["odds"] = mlp[-1]["home_ml"]; out["ml"][str(g["away_team"])]["odds"] = mlp[-1]["away_ml"]
            g["splits"] = out
        moves = []
        hist = g.get("consensus_history") or []; sp = g.get("splits") or {}
        if hist and hist[0]["source"] == "Open" and sp.get("source") == "Consensus":
            o, n = hist[0], hist[-1]; H, A = g["home_team"], g["away_team"]
            if o["home_spread"] is not None and n["home_spread"] is not None and "spread" in sp and H in sp["spread"] and A in sp["spread"]:
                mv = n["home_spread"] - o["home_spread"]; pub = H if sp["spread"][H]["bets"] >= RLM_PUBLIC else (A if sp["spread"][A]["bets"] >= RLM_PUBLIC else None)
                toward = H if mv > 0 else A
                if pub and abs(mv) >= 0.5 and toward != pub:
                    moves.append({"market": "spread", "toward": toward, "public": pub, "bets": sp["spread"][pub]["bets"], "open": o["home_spread"], "now": n["home_spread"]})
            if o["total"] is not None and n["total"] is not None and "total" in sp:
                mv = n["total"] - o["total"]; pub = "over" if sp["total"]["over"]["bets"] >= RLM_PUBLIC else ("under" if sp["total"]["under"]["bets"] >= RLM_PUBLIC else None)
                toward = "over" if mv > 0 else "under"
                if pub and abs(mv) >= 0.5 and toward != pub:
                    moves.append({"market": "total", "toward": toward, "public": pub, "bets": sp["total"][pub]["bets"], "open": o["total"], "now": n["total"]})
            # the moneyline from the oldest to the newest point that has one, as the Win block's chart reads it
            wp = [p for p in hist if p.get("home_win") is not None]; o, n = (wp[0], wp[-1]) if wp else (o, n)
            if wp and "ml" in sp and H in sp["ml"] and A in sp["ml"]:
                mv = n["home_win"] - o["home_win"]; pub = H if sp["ml"][H]["bets"] >= RLM_PUBLIC else (A if sp["ml"][A]["bets"] >= RLM_PUBLIC else None)
                toward = H if mv > 0 else A
                if pub and abs(mv) >= ML_MOVE_PTS and toward != pub:
                    # open and now: the side moved toward's no-vig win chance (percent) and its moneyline
                    sd = (lambda p: p) if toward == H else (lambda p: round(100 - p, 1)); k = "home_ml" if toward == H else "away_ml"
                    moves.append({"market": "ml", "toward": toward, "public": pub, "bets": sp["ml"][pub]["bets"], "open": sd(o["home_win"]), "now": sd(n["home_win"]),
                                  "open_ml": o[k], "now_ml": n[k]})
        g["moves"] = moves


def _code_sha() -> str:
    """The commit this code is at: GITHUB_SHA on the runner, else git's HEAD."""
    import os, subprocess
    if os.environ.get("GITHUB_SHA"):
        return os.environ["GITHUB_SHA"]
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, timeout=10).stdout.strip()
    except Exception:  # noqa
        return ""


def main():
    WEB.mkdir(parents=True, exist_ok=True)
    tg = pd.read_parquet(OUT / "team_games.parquet")
    box = pd.read_parquet(OUT / "team_box.parquet")
    feats = M.with_trends(pd.read_parquet(OUT / "features_asof.parquet"))
    pred = pd.read_parquet(OUT / "pred_v3.parquet")
    games = pd.read_parquet(OUT / "games.parquet").set_index("game_id")
    tg = tg.drop(columns=[c for c in ["kickoff_et"] if c in tg.columns])
    box_cols = [c for c in box.columns if c.startswith("off_") or c.startswith("def_")]
    bx = box[["game_id", "team"] + box_cols].rename(columns={c: "box_" + c for c in box_cols})   # no name clashes with the EPA table
    d = tg.merge(bx, on=["game_id", "team"], how="left")
    rcols = [f"{s}_{st}" for st in ["epa_play", "pass_epa", "rush_epa", "pf", "plays", "success"] for s in ["off", "def", "own_def", "opp_off"]]
    rcols = [c for c in rcols if c in feats.columns]
    fe = feats[["game_id", "team"] + rcols + ["qb_rating", "opp_qb_rating", "n_games", "opp_rest"] + M.TREND_FEATS].copy()
    fe = fe.rename(columns={c: "r_" + c for c in rcols})
    d = d.merge(fe, on=["game_id", "team"], how="left")
    # the exact inputs the points regression saw for this team-game (model.prep on the as-of features), as mf_<input>: the game
    # deep dive reads them first, so its sum is the model's expected points to the cent; the game log shows them under Model inputs
    # (a played game's weather as priced: the stored forecast, model.priced_weather, 2 Oct 2026)
    pf_ = M.priced_weather(M.prep(feats)); mf = pf_[["game_id", "team"] + [f for f in M.FEATS if f in pf_.columns]].rename(columns={f: "mf_" + f for f in M.FEATS})
    d = d.merge(mf, on=["game_id", "team"], how="left")
    # model prediction from this team's view
    pv = pred.set_index("game_id")
    d["gameday"] = d.game_id.map(games.gameday)
    # beyond the week holding the next unplayed game, an "as-of" rating is just this week's number decayed and the starter is a
    # guess, so those rows carry no ratings, QB or model columns: the page shows them blank rather than as a forecast
    cur_s = int(games.season.max())
    played_w = games[(games.season == cur_s) & games.home_score.notna()].week.max()
    cutoff = int(played_w) + 1 if pd.notna(played_w) else 1
    future = (d.season == cur_s) & (d.week > cutoff)
    d.loc[future, ["r_" + c for c in rcols] + ["qb_rating", "opp_qb_rating"] + [c for c in d.columns if c.startswith("mf_")]] = np.nan
    pv = pv[~((pv.season == cur_s) & (pv.week > cutoff))]
    d["m_exp_pf"] = [pv.home_exp.get(g, np.nan) if h else pv.away_exp.get(g, np.nan) for g, h in zip(d.game_id, d.home)]
    d["m_exp_pa"] = [pv.away_exp.get(g, np.nan) if h else pv.home_exp.get(g, np.nan) for g, h in zip(d.game_id, d.home)]
    d["m_win"] = [pv.p_home.get(g, np.nan) if h else 1 - pv.p_home.get(g, np.nan) for g, h in zip(d.game_id, d.home)]
    d["m_cover"] = [pv.p_cover_home.get(g, np.nan) if h else 1 - pv.p_cover_home.get(g, np.nan) for g, h in zip(d.game_id, d.home)]
    d["m_over"] = d.game_id.map(pv.p_over_emp if "p_over_emp" in pv.columns else pv.p_over)   # the one total chance (26 Sep 2026: read off the real, skewed spread of totals, as the flag and the card)
    if "home_blend_adj" in pv.columns:
        d["m_blend_adj"] = [pv.home_blend_adj.get(g, np.nan) if h else pv.away_blend_adj.get(g, np.nan) for g, h in zip(d.game_id, d.home)]
    if "home_total_adj" in pv.columns:
        d["m_total_adj"] = [pv.home_total_adj.get(g, np.nan) if h else pv.away_total_adj.get(g, np.nan) for g, h in zip(d.game_id, d.home)]
    d["team_spread"] = np.where(d.home, d.spread_line, -d.spread_line)
    d = d.sort_values(["season", "week"])
    cols = [c for c in d.columns if c not in ("game_id",)]
    dictionary = {c: describe(c) for c in cols if c not in ("season", "week", "game_type", "team", "opp", "home", "gameday", "qb_id")}
    # coefficients per season, in points per unit and the training means (for the contribution view)
    f2 = M.prep(feats)
    coefs = {}
    for s in range(2019, 2027):
        train = f2[f2.pf.notna() & (f2.season < s) & (f2.season >= M.TRAIN_FROM)]
        m = M.fit_points(train, M.RIDGE)
        coefs[str(s)] = {"per_unit": dict(zip(M.FEATS, (m[-1].coef_ / m[0].scale_).round(5).tolist())),
                         "mean": dict(zip(M.FEATS, m[0].mean_.round(5).tolist())), "intercept": float(np.mean(train.pf))}
    pull = pd.read_csv(RAW / "pull_log.csv").tail(120)
    ver = (ROOT / "reports" / "verification.md").read_text() if (ROOT / "reports" / "verification.md").exists() else ""
    for name in ["health.md", "weekly_audit.md"]:   # the Monday audit and its health table go first
        if (ROOT / "reports" / name).exists():
            ver = (ROOT / "reports" / name).read_text() + "\n\n" + ver
    if (ROOT / "reports" / "tie_check.md").exists():
        ver += "\n\n" + (ROOT / "reports" / "tie_check.md").read_text()   # the tie-out written before this export (sources); the page part is checked after it
    teams = sorted(d[d.season == 2026].team.unique())
    REPD = ROOT / "reports"
    def csv_rows(name):
        f = REPD / name
        if not f.exists():
            return []
        d = pd.read_csv(f).round(4)
        return [{k: (None if isinstance(v, float) and np.isnan(v) else v) for k, v in r.items()} for r in d.to_dict("records")]   # NaN would reach the page as NaN
    def txt(name):
        f = REPD / name
        return f.read_text() if f.exists() else ""
    tun = pd.read_csv(REPD / "tuning_ratings.csv") if (REPD / "tuning_ratings.csv").exists() else pd.DataFrame()
    analysis = {"correlations": csv_rows("lab_stat_correlations.csv"), "reliability": csv_rows("lab_stat_reliability.csv"),
                "ablation": csv_rows("ablation.csv"), "additions": csv_rows("additions.csv"), "additions_both": csv_rows("additions_both.csv"), "combo": csv_rows("combo.csv"),
                "equation_checks": csv_rows("equation_checks.csv"), "starter_share": csv_rows("starter_share.csv"), "player_injury": csv_rows("player_injury.csv"), "line_defense": csv_rows("line_defense.csv"), "snap_pair": csv_rows("snap_pair.csv"), "positions": csv_rows("positions.csv"), "special_teams": csv_rows("special_teams.csv"), "third_window": csv_rows("third_window.csv"), "recency": csv_rows("recency.csv"), "luck": csv_rows("luck.csv"), "rest_more": csv_rows("rest_more.csv"), "qb_replacement": csv_rows("qb_replacement.csv"), "qb_k": csv_rows("qb_k.csv"), "weather_knobs": csv_rows("weather_knobs.csv"), "scheme_inputs": csv_rows("scheme_inputs.csv"), "scheme_qb_totals": csv_rows("scheme_qb_totals.csv"), "player_knobs": csv_rows("player_knobs.csv"), "totals_players": csv_rows("totals_players.csv"), "legitimacy": csv_rows("legitimacy.csv"), "legitimacy_md": txt("legitimacy.md"), "persistence": csv_rows("trend_persistence.csv"),
                "tuning_best": tun.sort_values("team_mae").head(10).round(4).to_dict("records") if len(tun) else [],
                "tuning_by": {k: tun.groupby(k).team_mae.mean().round(4).to_dict() for k in ["decay", "prior", "alpha", "ridge"]} if len(tun) else {},
                "decision_log": txt("decision_log.md"), "audit": txt("audit.md"), "backtest_report": txt("backtest_v3.md"), "verification": txt("verification.md"),
                "how_it_works": (ROOT / "docs" / "how_it_works.md").read_text() if (ROOT / "docs" / "how_it_works.md").exists() else "",
                "situation_facts": situation_facts(feats), "qb_overlap": M.qb_overlap(f2, max(int(k) for k in coefs)), "noise": noise_floor()}
    analysis["home_edges"] = team_home_edges(tg)
    analysis["lineup"] = model_lineup(pred, games, f2)
    analysis["round3"] = round3_tests()
    from . import picks as P_, backtest as B_, records as R3_
    _bj = B_.join(pred, games.reset_index()); _bj = _bj[(_bj.game_type == "REG") & _bj.home_score.notna() & _bj.spread_line.notna()]
    meta = {"columns": cols, "dictionary": dictionary, "coefs": coefs, "feats": M.FEATS, "blend_label": M.BLEND_LABEL, "teams": teams, "analysis": analysis, "warm_or_dome": sorted(M.WARM_OR_DOME),
            "picks": P_.page_rules(_bj), "standard": R3_.standard_records(_bj, int(games.season.max())), "appendix": R3_.appendix(_bj, int(games.season.max())), "bet_stats": R3_.bet_stats(_bj, int(games.season.max())), "model": model_constants(feats), "player_model": player_model_constants(), "data_from": data_from(),
            "pull_log": pull.to_dict("records"), "verification": ver, "built": pd.Timestamp.now("UTC").strftime("%Y-%m-%d %H:%M UTC"),
            "code_sha": _code_sha()}   # the commit whose code built these files (nflmodel/publish_check.py)
    (WEB / "meta.js").write_text("window.META=" + json.dumps(meta, default=clean, separators=(",", ":")) + ";")
    pvf = OUT / "player_values_all.parquet"
    pvals = pd.read_parquet(pvf) if pvf.exists() else pd.DataFrame(columns=["team"])
    if len(pvals):
        pvals = pvals[pvals.value_above_replacement.notna()].copy()
    rnf = OUT / "roster_now.parquet"
    rnow = pd.read_parquet(rnf) if rnf.exists() else pd.DataFrame(columns=["team"])
    # players.js: every valued skill player league-wide, and each player's history across seasons and teams
    phf = OUT / "player_history.parquet"
    if phf.exists():
        ph = pd.read_parquet(phf)
        hist = {}
        for r in ph.itertuples():
            hist.setdefault(r.player_id, []).append([int(r.season), r.team, r.role, int(r.games), int(r.plays), clean(r.epa_play)])
        names = {r.player_id: r.name for r in ph.drop_duplicates("player_id", keep="last").itertuples()}
        if len(pvals):
            names.update({r.player_id: r.name for r in pvals.itertuples()})
        def _team_plays_pg():   # scrimmage plays a team runs a game, last season and this one (24 Sep 2026): the page's "points a game" for values in EPA per team play
            sp = pd.read_parquet(OUT / "scheme_plays.parquet", columns=["season", "game_id", "posteam", "play_type"]); sp = sp[sp.play_type.isin(["pass", "run"]) & (sp.season >= sp.season.max() - 1)]
            return round(len(sp) / max(sp.groupby(["game_id", "posteam"]).ngroups, 1), 1)
        if len(pvals) and "group" in pvals.columns and (OUT / "qb_games.parquet").exists():   # a QB's EPA per dropback this season beside the career rating (25 Sep 2026)
            qg = pd.read_parquet(OUT / "qb_games.parquet"); cs = int(qg.season.max()); qs = qg[qg.season == cs].groupby("qb_id").agg(db=("dropbacks", "sum"), epa=("qb_epa", "sum"))
            isq = pvals.group == "QB"
            pvals.loc[isq, "season_db"] = pvals.loc[isq, "player_id"].map(qs.db); pvals.loc[isq, "season_epa_db"] = pvals.loc[isq, "player_id"].map((qs.epa / qs.db.where(qs.db > 0)).round(3))
        (WEB / "players.js").write_text("window.PLAYERS=" + json.dumps({"season": int(ph.season.max()), "values": [{k: clean(v) for k, v in r.items()} for r in pvals.drop(columns=[c for c in ["basis"] if c in pvals.columns]).to_dict("records")], "basis": {g: b for g, b in pvals.groupby("group").basis.first().items()} if "basis" in pvals.columns else {},
                                                                          "basis_role": {r: b for r, b in pvals[pvals.group == "Defense"].groupby("def_role").basis.first().items()} if "basis" in pvals.columns and "def_role" in pvals.columns else {},
                                                                          "history": hist, "names": names, "hist_cols": ["season", "team", "role", "games", "plays", "epa_play"], "team_plays_pg": _team_plays_pg()}, default=clean, separators=(",", ":")) + ";")
    pj = OUT / "props.json"
    if pj.exists():   # player-against-scheme projections for the week (nflmodel/props.py)
        (WEB / "props.js").write_text("window.PROPS=" + props_payload(pj) + ";")
    (WEB / "props_backtest.js").write_text("window.PROPS_BT=" + json.dumps(props_backtest_export(csv_rows), default=clean) + ";")   # the five backtest rounds and the by-season run (Results -> Player projections)
    pp = OUT / "props_profiles.json"
    if pp.exists():   # every player's last-17 profile with splits, every defense, the league (Players tab)
        (WEB / "player_profiles.js").write_text("window.PROFILES=" + pp.read_text() + ";")
    from . import player_logs as PLG
    PLG.export()   # every player's game log since 2016, one file a season (web/data/plogs), and the career totals (web/data/player_careers.js)
    rec_rows = {"graded": csv_rows("../data/tracker/props_graded.csv"), "market": csv_rows("../data/tracker/props_vs_market.csv"), "projections": []}
    if (ROOT / "data" / "tracker" / "props_vs_market.csv").exists():   # the record by stat and edge, the one summary the page reads (props.market_summary)
        from .props import market_summary as _ms
        rec_rows["summary"] = _ms(pd.read_csv(ROOT / "data" / "tracker" / "props_vs_market.csv"))
    for f in sorted((ROOT / "reports").glob("props_*_wk*.csv")):
        rec_rows["projections"] += [{k: (None if isinstance(v, float) and np.isnan(v) else v) for k, v in r.items()} for r in pd.read_csv(f).to_dict("records")]
    # every projection written, every grade, every line graded (Players tab, Results); packed as columns and rows (28 Sep 2026:
    # the same rows as objects were 4.7 MB of a 60 MB page), the page unpacks it right after loading it, tie_check._unpack too
    (WEB / "props_record.js").write_text("window.PROPS_REC=" + json.dumps(pack_rows(rec_rows), default=clean, separators=(",", ":")) + ";")
    sp = OUT / "scheme_profiles.json"
    if sp.exists():   # scheme and play-calling profiles (nflmodel/scheme.py), as of the current week
        from . import scheme as SC_
        _sj = json.loads(sp.read_text()); _sj.setdefault("min_n", SC_.MIN_N)   # the play count under which a look's EPA is left blank (scheme._epa)
        (WEB / "scheme.js").write_text("window.SCHEME=" + json.dumps(_sj, separators=(",", ":")) + ";")
    for t in teams:
        rows = d[d.team == t]
        allc = ["game_id"] + cols
        recs = [[(None if (isinstance(v, float) and np.isnan(v)) else round(float(v), 6)) if (c.startswith("mf_") and isinstance(v, (float, np.floating))) else clean(v) for c, v in zip(allc, r)] for r in rows[allc].itertuples(index=False, name=None)]
        recs = [[int(v) if isinstance(v, float) and v == v and v == int(v) and abs(v) < 1e15 else v for v in r] for r in recs]   # 41.0 -> 41: whole numbers without the ".0" (the page files are near the 64 MB cap)   # model inputs at six decimals so a breakdown rebuilds the expected points
        players = [{k: clean(v) for k, v in r.items()} for r in pvals[pvals.team == t].drop(columns=["team"]).to_dict("records")]
        roster = [{k: clean(v) for k, v in r.items()} for r in rnow[rnow.team == t].drop(columns=["team"]).to_dict("records")] if len(rnow) else []
        (WEB / f"{t}.js").write_text(f'window.TEAMDATA=window.TEAMDATA||{{}};window.TEAMDATA["{t}"]=' + json.dumps({"cols": allc, "rows": recs, "players": players, "roster": roster}, default=clean, separators=(",", ":")) + ";")
    export_week(feats, games, pred)
    from . import lines as LN, picks as P, tracker as TK
    cur_season, cur_week = LN.current_week(pd.read_parquet(OUT / "games.parquet"))
    write_games_js(games.reset_index())
    gr = TK.TR / "graded.csv"
    g = pd.read_csv(gr).to_dict("records") if gr.exists() else []
    (WEB / "track.js").write_text("window.TRACK=" + json.dumps(g, default=clean, separators=(",", ":")) + ";")
    sizes = sum(f.stat().st_size for f in WEB.glob("*.js"))
    print(f"{len(teams)} teams, {len(cols)} columns, {sizes/1e6:.1f} MB")
    export_rankings_and_methods()   # rankings.js and backtest.js, on every export (about 75 seconds)




# ---------------------------------------------------------------------------------------------
# Rankings, rating walkthrough tables, and methods comparison (added for the sheet-style views)
# ---------------------------------------------------------------------------------------------
    export_season()
    # is the edge real: staking, luck, calibration and the tests that did not pass (Bets tab), straight from the reports
    lg = {}
    for key, fn in (("sizing", "sizing_backtest.csv"), ("seasons", "sizing_seasons.csv"), ("cover_cal", "cover_calibration.csv"), ("cal_start", "calibration_start.csv"), ("robust", "robust_loss.csv")):
        f_ = REP / fn
        if f_.exists():
            lg[key] = [{k: clean(v) for k, v in r.items()} for r in pd.read_csv(f_).to_dict("records")]
    (WEB / "legit.js").write_text("window.LEGIT=" + json.dumps(lg, default=clean, separators=(",", ":")) + ";")
    from . import catalog as CAT
    (WEB / "catalog.js").write_text("window.CATALOG=" + json.dumps(CAT.build(), default=clean, separators=(",", ":")) + ";")   # every data store, from the files themselves (Model -> Every data store)


def export_season() -> dict:
    """season.js: the season simulation for the week being priced (win totals, division, playoff and Super Bowl odds),
    the player season totals with the breakout watch, and both backtests (reports/season_backtest.csv and
    reports/player_season_backtest.csv). Also writes reports/season_odds.csv and reports/player_season_totals.csv, the
    same rows, for the tie check and the record."""
    from . import season as SE, player_season as PS
    built = pd.Timestamp.now("UTC").strftime("%Y-%m-%d %H:%M UTC")
    sim = SE.run_now(10000)
    teams = sorted(sim["teams"], key=lambda t: -t["p_sb"])
    for t in teams:
        for k in ("wins", "wins_sd", "wins_p10", "wins_p90", "p_div", "p_playoffs", "p_bye", "p_conf", "p_sb"):
            t[k] = round(t[k], 4)
    out = {"season": sim["season"], "week": sim["week"], "built": built, "n_sims": sim["n_sims"], "games_left": sim["games_left"], "sigma": round(sim["sigma"], 4), "fit_week": sim["fit_week"], "format": sim["format"],
           "shrink": SE.SHRINK, "sigma_mult": SE.SIGMA_MULT, "tie_band": SE.TIE_BAND, "wind_far": SE.WIND_FAR, "divisions": SE.DIV, "teams": teams, "ratings": sim["ratings"],
           "tie_rate": sim.get("tie_rate"), "tie_rate_league": SE.league_tie_rate(pd.read_parquet(OUT / "games.parquet"))}
    bg = REP / "season_by_game.csv"
    if bg.exists():   # the game-by-game projection tested against the rule (experiments/season_by_game.py): every variant, kind and window
        out["by_game"] = pd.read_csv(bg).to_dict("records")
    pd.DataFrame(teams).to_csv(REP / "season_odds.csv", index=False)
    # each team's games left with its chance in each (the draws' mean: the page's wins = record + the sum of these, near enough)
    left = {t["team"]: [] for t in teams}
    for g in sim.get("left_games", []):
        left[g["home"]].append([g["week"], g["away"], 1, round(g["p_home"], 3)]); left[g["away"]].append([g["week"], g["home"], 0, round(1 - g["p_home"], 3)])
    out["left"] = left
    bt = REP / "season_backtest.csv"
    if bt.exists():
        b = pd.read_csv(bt); m = b[b.season.astype(str) == "mean"]
        base = m[(m.shrink == 0.0) & (m.sigma_mult == 1.0)]
        out["backtest"] = {"windows": base[base.asof_week.astype(str) == "all"].to_dict("records"), "by_week": base[base.asof_week.astype(str) != "all"].to_dict("records"),
                           "variants": m[m.asof_week.astype(str) == "all"].to_dict("records"), "seasons": b[(b.season.astype(str) != "mean") & (b.shrink == 0.0) & (b.sigma_mult == 1.0)].to_dict("records")}
    sto = REP / "season_team_odds.csv"
    if sto.exists():   # accuracy in plain shares (24 Sep 2026): wins within 1 and 2, the playoff call right, the division favorite, by window and as-of week
        to = pd.read_csv(sto); to["div"] = to.team.map(SE.DIV_OF); acc = []
        def _acc(g):
            fav = g.sort_values("p_div", ascending=False).groupby(["season", "asof_week", "div"]).head(1)
            sure = g[g.p_playoffs >= 0.75]
            return {"n": int(len(g)), "wins_within1": round(float(((g.wins - g.actual_wins).abs() <= 1).mean()), 3), "wins_within2": round(float(((g.wins - g.actual_wins).abs() <= 2).mean()), 3),
                    "playoff_call": round(float(((g.p_playoffs >= 0.5) == (g.made_playoffs == 1)).mean()), 3), "playoff_75_made": round(float(sure.made_playoffs.mean()), 3) if len(sure) else None, "playoff_75_n": int(len(sure)),
                    "div_fav_won": round(float(fav.won_div.mean()), 3)}
        for (w, wk), g in to.groupby(["window", "asof_week"]):
            acc.append({"window": w, "asof_week": int(wk), **_acc(g)})
        for w, g in to.groupby("window"):
            acc.append({"window": w, "asof_week": "all", **_acc(g)})
        out["accuracy"] = acc
    try:   # the books' preseason win totals: this season's beside the model's, and every backtest season scored (nflmodel/wintotals.py)
        from . import wintotals as WT
        wt = WT.parse(); x_, s_ = WT.compare(wt); x_.to_csv(REP / "win_totals_vs_vegas.csv", index=False)
        cur = wt[wt.season == out["season"]][["team", "line", "vegas_wins", "p_over"]]
        out["vegas"] = {"source": "Sports Odds History's archive of the books' preseason win totals", "windows": s_.to_dict("records"),
                        "current": {r.team: [float(r.line), float(r.vegas_wins), float(r.p_over)] for r in cur.itertuples()}, "win_sd": WT.WIN_SD,
                        "within2": {w: {"model": round(float(((g.model_wins - g.actual).abs() <= 2).mean()), 3), "books": round(float(((g.vegas_wins - g.actual).abs() <= 2).mean()), 3), "n": int(len(g))}
                                    for w, g in list(x_.groupby("window")) + [("2019-25", x_)]},
                        "summary": (lambda a, b: f"before Week 1, the books' number missed a team's final wins by {a.vegas_miss:.2f} / {b.vegas_miss:.2f} games (2019-22 / 2023-25), the model's by {a.model_miss:.2f} / {b.model_miss:.2f}; the two agree closely (correlation {a.corr_model_vegas:.2f} / {b.corr_model_vegas:.2f}), averaging them does not beat the books alone, and taking the model's side where it differs from the line by a win or more went {a.model_side_1win} and {b.model_side_1win}. The market is the better preseason number; in season the model re-prices every week, which the archive cannot be compared against (it keeps only the preseason line).")(
                            s_[s_.window == "2019-22"].iloc[0], s_[s_.window == "2023-25"].iloc[0])}
    except Exception as e:  # noqa
        print("win totals not compared:", str(e)[:200], flush=True)
    try:   # the books' season-long markets as chances (nflmodel/futures.py), beside the model's
        from . import futures as FU
        out["books"] = FU.latest()
    except Exception as e:  # noqa
        print("futures not read:", str(e)[:200], flush=True)
    pl = PS.run_now()
    try:   # the same totals as projected at points in time, with what happened (Season -> Player totals, "As projected")
        from .lines import current_week as _cw
        from .positions import names_by_id as _nb
        from .props import official as _off
        _g = pd.read_parquet(OUT / "games.parquet"); _s, _w = _cw(_g)
        out["snapshots"] = PS.snapshots(_off(pd.read_parquet(OUT / "scheme_plays.parquet")), _nb(range(_s - 2, _s + 1)), _g, _s, _w)
    except Exception as e:  # noqa
        print("season snapshots failed:", str(e)[:200], flush=True); out["snapshots"] = {"error": str(e)[:200]}
    keep = ["kind", "player_id", "name", "pos", "team", "rank", "games_so_far", "yards_so_far", "td_so_far", "catches_so_far", "volume_pg", "rate", "yards_pg", "td_pg", "catches_pg", "team_games_left", "team_games_played", "team_games", "avail", "blend", "own_yards", "proj_yards", "proj_td", "proj_catches", "prev_yards", "prev_td", "prev_games", "pace_yards", "proj_pg", "prev_pg", "breakout", "new_top", "profile_games"]
    pl = pl[keep].copy()
    for c in ("volume_pg", "rate", "yards_pg", "td_pg", "catches_pg", "own_yards", "proj_yards", "proj_td", "proj_catches", "pace_yards", "proj_pg", "prev_pg"):
        pl[c] = pl[c].astype(float).round(2)
    pl.to_csv(REP / "player_season_totals.csv", index=False)
    out["players"] = {"rows": pl.to_dict("records"), "avail": PS.AVAIL, "blend": PS.BLEND, "min_pg": PS.MIN_PG, "top_n": PS.TOP_N, "break_up": PS.BREAK_UP, "topw": PS.TOPW}
    sc = REP / "season_calibration.csv"
    if sc.exists():
        out["calibration"] = pd.read_csv(sc).to_dict("records")
    pbt = REP / "player_season_backtest.csv"
    if pbt.exists():
        out["player_backtest"] = pd.read_csv(pbt).to_dict("records")
    (WEB / "season.js").write_text("window.SEASON=" + json.dumps(out, default=clean, separators=(",", ":")) + ";")
    print(f"season.js {len(teams)} teams, {len(pl)} player totals, {out['games_left']} games left", flush=True)
    return out


INJ_REPORT = ("Out", "Doubtful", "Questionable")
PRACTICE = {"Did Not Participate In Practice": "Did not practice", "Limited Participation in Practice": "Limited practice", "Full Participation in Practice": "Full practice"}   # the week's practice report, before a game status
PRICED = ("Out", "Doubtful")   # the model counts Out and Doubtful on the report and the reserve lists; Questionable plays


def _add_injuries(wk: list, cur_week: int, cur_season: int | None = None) -> None:
    """Each side's injury report for the week (26 Sep 2026, for the weekly report): everyone Out, Doubtful or Questionable
    on the league's report, and anyone on a reserve list who played last game or went on it this week, with his share of
    last game's snaps and what the model's equation takes off the spread for him: his offensive snaps times the snaps-out
    coefficient and his skill value times the skill-out coefficient on his side, his defensive snaps and skill value in the
    opponent's equation. The same fit that priced the game (the week's coefficients), so the lines add up to the card's
    injury inputs; Questionable players are listed but not priced, as in the model."""
    rnf = OUT / "roster_now.parquet"
    if not rnf.exists():
        return
    rn = pd.read_parquet(rnf)
    _pvf = OUT / "player_values.parquet"   # every skill player's value as of the coming week, for an undecided player's if-out
    skill_val = dict(zip(*[pd.read_parquet(_pvf, columns=["player_id", "value_above_replacement"]).dropna()[c] for c in ("player_id", "value_above_replacement")])) if _pvf.exists() else {}
    # the starting QB listed Out is priced through the quarterback inputs, not the snaps-out line (28 Sep 2026, Matt: "how is
    # Caleb Williams only -0.2"): his row also carries the swap, the backup's rating minus his own times the rating's points
    # per unit, plus the QB-out term (none since qb_out left the model, 3 Oct 2026), from the same QB rater the features used (ratings.QBRatings, live settings); shown
    # only when the rater reproduces the priced starter's rating to 1e-4, so the card's number is the equation's
    qbr = None
    qbg = OUT / "qb_games.parquet"
    if cur_season is not None and qbg.exists():
        from . import ratings as RT
        pr = RT.DEFAULT; qbr = RT.QBRatings(pd.read_parquet(qbg), pr["qb_k"], pr["qb_decay"], pr.get("qb_prior", -0.12), pr.get("qb_season_fade", 1.0))
    # a played game keeps the report as it stood at the last export before it was scored (28 Sep 2026, Matt: the injury report
    # stays on the card after the game); data/runs/injury_reports.json holds each game's last pre-score report
    cache_f = OUT.parent / "runs" / "injury_reports.json"
    cache = json.loads(cache_f.read_text()) if cache_f.exists() else {}
    # his usual snap share (30 Sep 2026, Matt: last game's share reads 0 for anyone who missed it, which says nothing about his
    # role): the larger of his offense and defense share, averaged over the last 4 games he played before this week, this
    # season or last; last game's share stays on the row because the model's snaps-out inputs price that
    usual = {}
    sef = OUT / "snap_exposure.parquet"
    if sef.exists() and cur_season is not None:
        se = pd.read_parquet(sef, columns=["player_id", "season", "week", "off_pct", "def_pct"])
        se = se.assign(pct=se[["off_pct", "def_pct"]].fillna(0).max(axis=1))
        se = se[(se.pct > 0) & (se.season >= cur_season - 1) & ((se.season < cur_season) | (se.week < cur_week))].sort_values(["season", "week"])
        for pid, g in se.groupby("player_id"):
            # this season's games when he has any (30 Sep 2026, Matt: DeShon Elliott read 84% from last season's games while
            # out all of this one); otherwise last season's, and the row says which season
            cur = g[g.season == cur_season]; t = (cur if len(cur) else g).tail(4)
            usual[pid] = (round(float(t.pct.mean()), 2), int(len(t)), int(t.season.iloc[-1]))
    for g in wk:
        co = (g.get("coefs") or {}).get("per_unit") or {}
        teams = [g["home_team"], g["away_team"]]
        if g.get("home_score") is not None:   # played: today's roster is not the one the game was priced with; the cached report stands
            for tm in teams:
                sd = (g.get("sides") or {}).get(tm)
                if sd is not None and tm in (cache.get(g["game_id"]) or {}):
                    sd["injuries"] = cache[g["game_id"]][tm]
            continue
        for tm in teams:
            sd = (g.get("sides") or {}).get(tm)
            if sd is None:
                continue
            skill = {x["name"]: x["value"] for x in sd.get("skill_out_players", [])}
            und = 0.0
            r = rn[rn.team == tm]
            res = ~r.roster.isin(["Active", "Practice squad", "Cut", "Inactive"])
            played = (r.off_pct.fillna(0) > 0) | (r.def_pct.fillna(0) > 0)
            # the full report (30 Sep 2026, Matt: "they should show even if 0 injuries ... this should be the full report regardless";
            # PIT's card was empty because its reserve players had not played last game and its injured starters had no status
            # yet): every reserve list, and anyone with an injury listed even before the week's game status; pricing is unchanged,
            # a reserve player who missed last game has no snaps to take and is already out of the ratings
            hurt = (r.roster == "Active") & (r.injury.fillna("").astype(str).str.strip() != "")
            keep = r[r.report.isin(INJ_REPORT) | (res & (played | (r.since == cur_week) | ~r.roster.isin(["Retired"]))) | hurt | r.name.isin(list(skill))]   # everyone the skill value counts, even off a reserve list
            rows = []
            for p in keep.itertuples():
                priced = p.report in PRICED or (p.report not in INJ_REPORT and p.roster not in ("Active", "Practice squad", "Cut", "Inactive"))
                off, dfn, v = float(p.off_pct or 0) if pd.notna(p.off_pct) else 0.0, float(p.def_pct or 0) if pd.notna(p.def_pct) else 0.0, float(skill.get(p.name, 0.0))
                own = (co.get("off_snap_out", 0) * off + co.get("skill_out_value", 0) * v) if priced else 0.0
                opp = (co.get("opp_def_snap_out", 0) * dfn + co.get("opp_skill_out_value", 0) * v) if priced else 0.0
                row = {"name": p.name, "pos": p.position, "status": p.report or (PRACTICE.get(clean(p.practice), clean(p.practice)) or "No game status yet" if p.roster == "Active" else p.roster), "injury": clean(p.injury) or clean(p.why) or "",
                       "off": round(off, 2), "def": round(dfn, 2), "priced": bool(priced), "own_pts": round(own, 3), "opp_pts": round(opp, 3), "spread_pts": round(own - opp, 3),
                       "back": clean(p.back), "usual": usual.get(p.player_id, (None, 0, None))[0], "usual_n": usual.get(p.player_id, (None, 0, None))[1],
                       "usual_season": usual.get(p.player_id, (None, 0, None))[2]}
                # 1 Oct 2026 (Matt: "show me on the injury report the total move, worst case either way"): a player still undecided
                # (Questionable, or no game status yet) is not counted; if_out is what the same terms would move the line if he sat,
                # his last-game snaps and, for a skill player, his value (player_values.parquet)
                if not priced and p.roster == "Active" and p.report not in PRICED:
                    vs = float(skill_val.get(p.player_id, 0.0)) if isinstance(p.player_id, str) else 0.0
                    row["if_out"] = round((co.get("off_snap_out", 0) * off + co.get("skill_out_value", 0) * vs) - (co.get("opp_def_snap_out", 0) * dfn + co.get("opp_skill_out_value", 0) * vs), 3)
                    und += row["if_out"]
                if qbr is not None and priced and p.position == "QB" and sd.get("qb_out") and sd.get("qb_rating") is not None and sd.get("qb_name") and p.name != sd.get("qb_name") and isinstance(p.player_id, str):
                    st = r[r.name == sd["qb_name"]]
                    if len(st) and isinstance(st.iloc[0].player_id, str):
                        priced_r = qbr.rating(st.iloc[0].player_id, cur_season, cur_week); his = qbr.rating(p.player_id, cur_season, cur_week)
                        if abs(priced_r - float(sd["qb_rating"])) < 1e-4:
                            row["qb_pts"] = round(co.get("qb_rating", 0) * (priced_r - his) + co.get("qb_out", 0) * float(sd.get("qb_out") or 0), 3)
                            row["qb_swap"] = {"to": sd["qb_name"], "his_rating": round(his, 4), "to_rating": round(priced_r, 4)}
                rows.append(row)
            # the ones that move the line, then the week's report (Out, Doubtful, Questionable), then no status yet, then the reserve lists
            grp = lambda x: 0 if x["priced"] and (abs(x["spread_pts"]) >= 0.005 or x.get("qb_pts")) else 1 + INJ_REPORT.index(x["status"]) if x["status"] in INJ_REPORT else 4 if not x["priced"] else 5
            sd["injuries"] = sorted(rows, key=lambda x: (grp(x), x["spread_pts"], x["name"]))
            sd["undecided_pts"] = round(und, 3)   # the team's margin if every undecided player sits
            # whether the week's league report (practice or game status) is out for this team yet (30 Sep 2026, Matt: an empty
            # list should say whether nobody is hurt or the report is not out)
            sd["report_out"] = bool(((r.report.fillna("") != "") | (r.practice.fillna("") != "")).any())
            cache.setdefault(g["game_id"], {})[tm] = sd["injuries"]   # the last pre-score report, for the card after the game
    keep_ids = {g["game_id"] for g in wk}
    cache = {k: v for k, v in cache.items() if k in keep_ids}   # the week's games alone
    cache_f.parent.mkdir(parents=True, exist_ok=True); cache_f.write_text(json.dumps(cache, separators=(",", ":"), default=clean))


def pack_rows(d: dict) -> dict:
    """Each list of same-keyed dicts becomes {cols, rows}; everything else stays. The page and tie_check unpack it."""
    out = {}
    for k, v in d.items():
        if isinstance(v, list) and v and all(isinstance(x, dict) for x in v) and all(list(x.keys()) == list(v[0].keys()) for x in v):
            cols = list(v[0].keys()); out[k] = {"cols": cols, "rows": [[x[c] for c in cols] for x in v]}
        else:
            out[k] = v
    return out


def export_week(feats=None, games=None, pred=None):
    """week.js: this week's games with the picks, the inputs, the line log and the fit that priced each game. Runs on its
    own (python -m nflmodel.export_web --week) so the page's cards can follow the line log between weekly runs."""
    feats = M.with_trends(pd.read_parquet(OUT / "features_asof.parquet")) if feats is None else feats
    games = pd.read_parquet(OUT / "games.parquet").set_index("game_id") if games is None else games
    pred = pd.read_parquet(OUT / "pred_v3.parquet") if pred is None else pred
    rcols = [f"{s}_{st}" for st in ["epa_play", "pass_epa", "rush_epa", "pf", "plays", "success"] for s in ["off", "def", "own_def", "opp_off"]]
    pj = OUT / "props.json"
    if pj.exists():   # the props panel, re-projected on the live line by props --live just before this export
        (WEB / "props.js").write_text("window.PROPS=" + props_payload(pj) + ";")
    # this week's picks and the track record for the dashboard tabs
    from . import lines as LN, picks as P, tracker as TK
    cur_season, cur_week = LN.current_week(pd.read_parquet(OUT / "games.parquet"))
    refresh_books()   # the books' season-long markets on the Season tab follow the daily futures pull (line watch)
    try:
        pk = P.table(cur_season, cur_week)   # priced against the newest line snapshot: the card only displays these numbers
        fp = M.priced_weather(M.prep(feats)).set_index(["game_id", "team"])   # a played game's weather as priced (model.priced_weather)
        from . import weather as WX
        wxs = WX.status_by_game(games.reset_index())
        # the kickoff forecast in use now (the line watch pulls it every run): the card's temperature and wind follow it
        # (26 Sep 2026: the status said "forecast" while temp and wind held the weekly run's blank); the model's own
        # weather inputs stay as priced, and a forecast change inside the window starts a re-price (nflmodel/refresh.py)
        fc_now = WX.usable_forecast()
        # the weather each unplayed game is priced on now (weather.live_source, 2 Oct 2026): the GFS MOS / Japan reading where
        # wind_live has one (the backtest's source), else Open-Meteo; the card's temperature, wind and status follow it
        wx_now = WX.live_source(games.reset_index(), fc_now)
        for gid_, d_ in wx_now.items():
            if gid_ in wxs and d_["wind_src"] is not None:
                wxs[gid_] = {**wxs[gid_], "src": d_["wind_src"]} | ({"s": "forecast"} if d_["wind_src"] == "mos" else {})
        # the named starters and kickoff times from the schedule the line watch pulls every run (nflmodel/refresh.py),
        # so a flexed kickoff or a new starter shows before the re-price it starts has finished
        sched = _schedule_now(cur_season, cur_week)
        # the coming week's starters are carried forward by id (ratings.py); give the card the name
        gq = games.reset_index()
        qb_names = {**dict(zip(gq.home_qb_id, gq.home_qb_name)), **dict(zip(gq.away_qb_id, gq.away_qb_name))}
        from .ratings import qb_names as _qb_names
        all_qb_names = _qb_names(cur_season)   # a backup who has never started is on the rosters only
        # what was actually logged: the tracker's flagged pick for each game (recorded at the weekly run that flagged it),
        # shown beside the live flag state, which follows the line
        rec = _recorded(cur_season, cur_week)
        pif = OUT / "player_injury.parquet"
        pinj = pd.read_parquet(pif).set_index(["game_id", "team"]) if pif.exists() else None
        def out_detail(gid, tm):
            if pinj is None or (gid, tm) not in pinj.index:
                return []
            d = pinj.loc[(gid, tm), "skill_out_detail"]
            return [dict(zip(["name", "value", "share"], [x.split("|")[0], float(x.split("|")[1]), float(x.split("|")[2])])) for x in str(d).split(";") if x and "|" in x]
        hf = OUT.parent / "runs" / "pred_history.csv"
        hist_runs = pd.read_csv(hf) if hf.exists() else pd.DataFrame(columns=["game_id"])
        hist_runs = hist_runs[(hist_runs.season == cur_season) & (hist_runs.week == cur_week)] if len(hist_runs) else hist_runs
        wk = []; pv_coef = pd.read_parquet(OUT / "pred_v3.parquet").set_index("game_id"); log = LN.load_log()
        for r in pk.itertuples():
            h = LN.history(r.game_id, log)
            sides = {}
            for tm in [r.home_team, r.away_team]:
                if (r.game_id, tm) in fp.index:
                    row = fp.loc[(r.game_id, tm)]
                    sides[tm] = {c: ((None if pd.isna(row[c]) else round(float(row[c]), 6)) if c in M.FEATS and isinstance(row[c], (float, np.floating)) else clean(row[c])) for c in M.FEATS + ["qb_name", "rest", "temp", "wind", "dome", "qb_out"] + M.TREND_FEATS if c in row.index}   # qb_out: a reading since 3 Oct 2026 (chip, QB swap row)
                    sides[tm]["skill_out_players"] = out_detail(r.game_id, tm)
                    if r.game_id in pv_coef.index and "home_blend_adj" in pv_coef.columns:   # the blend: the other six models' pull and each model's number
                        sd_ = "home" if tm == r.home_team else "away"; prw = pv_coef.loc[r.game_id]
                        sides[tm]["blend_adj"] = round(float(prw[f"{sd_}_blend_adj"]), 6)
                        if f"{sd_}_total_adj" in prw.index: sides[tm]["total_adj"] = round(float(prw[f"{sd_}_total_adj"]), 6)   # the share-out to the game total
                        if "wind_pts" in prw.index and pd.notna(prw["wind_pts"]): sides[tm]["total_wind"] = round(float(prw["wind_pts"]) / 2, 6)   # each team's half of the wind points, part of the share-out (shown as its own row, 1 Oct 2026, Matt)
                        sides[tm]["models"] = {k: round(float(prw[f"{sd_}_m_{k}"]), 3) for k in M.BLEND_LABEL}
                    card_qb(sides[tm], row, sched.get(r.game_id, {}).get("home_qb" if tm == r.home_team else "away_qb"), qb_names, all_qb_names)
                    if r.home_score is None or pd.isna(r.home_score):   # unplayed: the forecast in use now (blank = typical weather)
                        f_ = wx_now.get(r.game_id) if not sides[tm].get("dome") else None
                        sides[tm]["temp"] = None if f_ is None or f_["temp"] is None else round(float(f_["temp"]), 1)
                        sides[tm]["wind"] = None if f_ is None or f_["wind"] is None else round(float(f_["wind"]), 1)
            gmeta = games.loc[r.game_id] if r.game_id in games.index else None
            pr_ = pv_coef.loc[r.game_id] if r.game_id in pv_coef.index else None   # the fit that priced this game: coefficient, training mean, intercept
            _p6 = lambda v: None if v is None or (isinstance(v, float) and np.isnan(v)) else round(float(v), 6)   # full precision: three decimals on the means and coefficients moved a card's rebuilt points by up to 0.02 once the QB coefficient passed 17
            coefs_g = None if pr_ is None or f"coef_{M.FEATS[0]}" not in pr_.index else {"per_unit": {f: _p6(pr_[f"coef_{f}"]) for f in M.FEATS}, "mean": {f: _p6(pr_[f"mean_{f}"]) for f in M.FEATS}, "intercept": _p6(pr_["intercept"])}
            kick = sched.get(r.game_id, {}).get("kickoff") or (str(gmeta.kickoff_et)[:16] if gmeta is not None else None)
            wk.append({k: clean(v) for k, v in r._asdict().items() if k != "Index" and not k.startswith(QT_KEYS)} | {"season": cur_season, "week": cur_week, "sides": sides, "coefs": coefs_g,
                       "p_over_cal": _p6(getattr(r, "p_over_cal", None)),   # six decimals (27 Sep 2026): the tie check rebuilds it from the card's three-decimal p_over_emp, whose rounding alone is worth 0.0002
                       "p_home_cal": _p6(getattr(r, "p_home_cal", None)),   # the calibrated win chance the card shows (27 Sep 2026, picks.home_calibration); p_home stays the raw one the season file is tied to
                       "p_home": _p6(getattr(r, "p_home", None)),   # six decimals too: the mapping's slope (1.19) stretches three-decimal rounding to the tie check's whole 0.0006 allowance
                       **{k: _p6(getattr(r, k, None)) for k in ("tease_spread_raw", "tease_spread_cal", "tease_total_raw", "tease_total_cal")},   # the 6-point teaser legs (28 Sep 2026), six decimals for the tie check
                       "kickoff": kick, "roof": gmeta.roof if gmeta is not None else None,
                       "referee": gmeta.referee if gmeta is not None else None, "stadium": gmeta.stadium if gmeta is not None else None,
                       "wx": wxs.get(r.game_id), "runs": [{"run_at": x.run_at, "model_spread": clean(x.model_spread), "model_total": clean(x.model_total), "spread_line": clean(x.spread_line), "total_line": clean(x.total_line), "bet": x.bet if isinstance(x.bet, str) else ""} for x in hist_runs[hist_runs.game_id == r.game_id].itertuples()], "home_coach": gmeta.home_coach if gmeta is not None else None, "away_coach": gmeta.away_coach if gmeta is not None else None,
                       "bet_recorded": rec["bet"].get(r.game_id, []), "shadowunder_recorded": rec["shadowunder"].get(r.game_id, []),
                      "line_history": [{"ts": t, "source": src, "home_spread": clean(hs), "total": clean(tt), "home_ml": clean(hm), "away_ml": clean(am)}
                                       for t, src, hs, tt, hm, am in zip(h.ts, h.source, h.home_spread, h.total, h.get("home_ml", pd.Series([None] * len(h))), h.get("away_ml", pd.Series([None] * len(h))))] if len(h) else []})
        _add_injuries(wk, cur_week, cur_season)
        _add_splits(wk)
        _add_consensus(wk)
        cal_s, _ = P.calibration(pred, games.reset_index(), cur_season)   # the spread calibration the cover odds used (the tie check re-prices each card's edge with it)
        cal_o = P.over_calibration(pred, games.reset_index(), cur_season)   # the over calibration the cards' total chance used (27 Sep 2026; the tie check rebuilds each card's p_over_cal with it)
        cal_h = P.home_calibration(pred, games.reset_index(), cur_season)   # the home win calibration the cards' win chance used (27 Sep 2026; the tie check rebuilds each card's p_home_cal with it)
        cal_t = P.tease_calibration(pred, games.reset_index(), cur_season)   # the 6-point teaser legs' calibration (28 Sep 2026; the tie check rebuilds each card's tease_*_cal with it)
        from . import clv as CLV
        try:   # closing line value on the live bets (Bets tab, 1 Oct 2026): grading only; a failure blanks the table, never the cards
            clv_js = CLV.page_payload()
        except Exception as e:  # noqa
            clv_js = {"error": f"{type(e).__name__}: {str(e)[:160]}"}
        (WEB / "week.js").write_text("window.WEEK=" + json.dumps({"season": cur_season, "week": cur_week, "games": wk, "spread_edge": P.SPREAD_EDGE, "total_edge": P.TOTAL_EDGE, "total_shadow": P.TOTAL_SHADOW, "wind_mph": P.WIND_UNDER["mph"],
                                                                  "rule_records": _rule_records_js(), "report_records": _report_records_js(), "clv": clv_js, "built": pd.Timestamp.now("UTC").strftime("%Y-%m-%d %H:%M UTC"),
                                                                  "cal": {"spread": [round(cal_s[0], 6), round(cal_s[1], 6)], "cap": P.CAL_CAP, "from": P.CAL_FROM, "before": cur_season,
                                                                          "over": {"a": round(cal_o[0], 6), "b": round(cal_o[1], 6), "from": P.OVER_CAL_FROM, "before": cur_season, "n": cal_o[2], "clip": P.OVER_CAL_CLIP},
                                                                          "home": {"a": round(cal_h[0], 6), "b": round(cal_h[1], 6), "from": P.HOME_CAL_FROM, "before": cur_season, "n": cal_h[2], "clip": P.HOME_CAL_CLIP},
                                                                          "tease": {k: {"a": round(v[0], 6), "b": round(v[1], 6), "n": v[2]} for k, v in cal_t.items()} | {"pts": P.TEASE_PTS, "from": P.TEASE_FROM, "before": cur_season, "clip": P.TEASE_CLIP}},
                                                                  "fit": week_fit(pv_coef, cur_season, cur_week)}, default=clean, separators=(",", ":")) + ";")
    except Exception as e:  # noqa
        (WEB / "week.js").write_text("window.WEEK=" + json.dumps({"error": str(e)[:200]}) + ";")
        raise   # a failed export fails its step (and the line watch), never a silent stale page


def card_qb(side: dict, row, now_qb, sched_names: dict, all_names: dict) -> dict:
    """The card's QB for one side, in place. row: the side's feature row (qb_id, qb_swap_from); now_qb: the schedule's
    named starter now; sched_names: id -> name from the schedule; all_names: ratings.qb_names (rosters too).
    2 Oct 2026 (code review): when ratings swapped a ruled-out starter for his replacement, the card showed the starter
    (the backup has no schedule name, and the schedule's starter then overrode the blank); it names the QB priced now,
    with the starter in qb_swap_from."""
    qid = row.get("qb_id") if hasattr(row, "get") else None
    swap_from = row.get("qb_swap_from") if hasattr(row, "get") else None
    if isinstance(swap_from, str) and isinstance(qid, str):
        side["qb_name"] = all_names.get(qid, qid)
        side["qb_swap_from"] = all_names.get(swap_from, swap_from)
    named_over = row.get("qb_named_over") if hasattr(row, "get") else None
    if isinstance(named_over, str) and isinstance(qid, str):   # 3 Oct 2026: the schedule named a stale starter; the last starter is priced
        side["qb_name"] = all_names.get(qid, sched_names.get(qid, qid))
        stale = all_names.get(named_over, sched_names.get(named_over, named_over))
        side["qb_named_over"] = stale
        if now_qb == stale:
            now_qb = None
    if not side.get("qb_name") and isinstance(qid, str):
        side["qb_name"] = sched_names.get(qid)
        side["qb_carried"] = True
    if now_qb and now_qb != side.get("qb_name") and now_qb != side.get("qb_swap_from"):   # a new named starter: shown now, priced by the re-price it starts
        side["qb_priced"] = side.get("qb_name"); side["qb_name"] = now_qb; side.pop("qb_carried", None)
    return side


def _schedule_now(season: int, week: int) -> dict:
    """game_id -> {kickoff, home_qb, away_qb} from the raw schedule the line watch pulls every run (refresh.check)."""
    f = RAW / "schedules" / "games.csv"
    if not f.exists():
        return {}
    s = pd.read_csv(f, usecols=["game_id", "season", "week", "gameday", "gametime", "home_qb_name", "away_qb_name"])
    s = s[(s.season == season) & (s.week == week)]
    return {r.game_id: {"kickoff": f"{r.gameday} {r.gametime}" if isinstance(r.gameday, str) and isinstance(r.gametime, str) else None,
                        "home_qb": r.home_qb_name if isinstance(r.home_qb_name, str) else None, "away_qb": r.away_qb_name if isinstance(r.away_qb_name, str) else None} for r in s.itertuples()}


def _recorded(season: int, week: int) -> dict:
    """The tracker's logged picks for the week: {"bet": {game_id: [...]}, "shadowunder": {...}}, each with the line
    as logged, the price, the book, the stake and when the run logged it."""
    from . import tracker as TK
    out = {}
    for key, fn in (("bet", "model_picks.csv"), ("shadowunder", "shadowunder_picks.csv")):
        f = TK.TR / fn; out[key] = {}
        if not f.exists():
            continue
        t = pd.read_csv(f); t = t[(t.season == season) & (t.week == week)]
        for x in t.itertuples():
            num = x.bet.split()[-1] if isinstance(x.bet, str) else None
            out[key].setdefault(x.game_id, []).append({"bet": x.bet, "line": clean(float(num)) if num not in (None, "") else None, "odds": clean(x.odds), "book": x.book if isinstance(x.book, str) else None,
                                                       "stake_pct": clean(x.stake_pct), "spread_edge": clean(x.spread_edge), "total_edge": clean(x.total_edge), "run_at": x.run_at})
    return out


QT_KEYS = ("qt_", "shadowqtotals_")   # 2 Oct 2026: the Questionable-in-totals shadow's columns (nflmodel/qtotals.py) never reach the cards (standing_checks.qt_stays_off)


def _rule_records_js() -> dict:
    """The flag's and the shadow rules' records on the three backtest windows (picks.rule_records, regular season,
    weeks 1 to 17): the card's tooltips quote these, the same rows as the Bets scorecard and docs section 9."""
    from . import backtest as B, picks as P
    d = B.join(pd.read_parquet(OUT / "pred_v3.parquet"), pd.read_parquet(OUT / "games.parquet"))
    d = d[(d.game_type == "REG") & d.home_score.notna() & d.spread_line.notna()]
    return {r["rule"]: {w: r[w] for w in P.WINDOWS} for r in P.rule_records(d).to_dict("records")}


SPREAD_BANDS = [0, 1, 2, 3, 4, 5, 6, 7]   # edge bands, points: 0-1, 1-2, ... 7+
TOTAL_BANDS = [0.5, 0.525, 0.55, 0.575, 0.6]   # chance bands for the side the total's chance favors: 50-52.5%, ... 60%+


def _report_records_js() -> dict:
    """The report's records (26 Sep 2026): every backtest game 2015 to the last full season, regular season weeks 1 to 17
    (the same games and grading as picks.rule_records), on the model's side of the spread and of the total, all games
    and the flagged ones, and by edge band for the spread and by chance band for the total, so each game can say how
    often an edge its size has hit."""
    from . import backtest as B, picks as P
    d = B.join(pd.read_parquet(OUT / "pred_v3.parquet"), pd.read_parquet(OUT / "games.parquet"))
    lo, hi = min(a for a, _ in P.WINDOWS.values()), max(b for _, b in P.WINDOWS.values())
    d = d[(d.game_type == "REG") & d.home_score.notna() & d.spread_line.notna() & (d.week < 18) & d.season.between(lo, hi)].copy()
    e = d.model_spread - d.spread_line; cm = d.home_score - d.away_score - d.spread_line
    sp = d[(e != 0) & (cm != 0)].assign(win=lambda x: np.sign(x.model_spread - x.spread_line) == np.sign(x.home_score - x.away_score - x.spread_line), edge=lambda x: (x.model_spread - x.spread_line).abs())
    t = d[d.total_line.notna() & d.p_over_emp.notna() & (d.home_score + d.away_score != d.total_line)].copy()
    t["over"] = t.p_over_emp >= 0.5; t["chance"] = np.where(t.over, t.p_over_emp, 1 - t.p_over_emp)
    t["win"] = np.where(t.over, t.home_score + t.away_score > t.total_line, t.home_score + t.away_score < t.total_line)
    wl = lambda x: [int(x.win.sum()), int((~x.win.astype(bool)).sum())]
    sb = [{"lo": a, "hi": (SPREAD_BANDS[i + 1] if i + 1 < len(SPREAD_BANDS) else None), "wl": wl(sp[(sp.edge >= a) & ((sp.edge < SPREAD_BANDS[i + 1]) if i + 1 < len(SPREAD_BANDS) else True)])} for i, a in enumerate(SPREAD_BANDS)]
    tb = [{"lo": a, "hi": (TOTAL_BANDS[i + 1] if i + 1 < len(TOTAL_BANDS) else None), "wl": wl(t[(t.chance >= a) & ((t.chance < TOTAL_BANDS[i + 1]) if i + 1 < len(TOTAL_BANDS) else True)])} for i, a in enumerate(TOTAL_BANDS)]
    ts = P.TOTAL_SHADOW; tflag = t[(t.chance >= ts["prob"]) & (t.over == (ts["side"] == "over"))]
    return {"seasons": f"{lo}-{str(hi)[2:]}", "spread": {"edge": P.SPREAD_EDGE, "flag": wl(sp[sp.edge >= P.SPREAD_EDGE]), "all": wl(sp), "bands": sb},
            "total": {"prob": ts["prob"], "side": ts["side"], "flag": wl(tflag), "all": wl(t), "bands": tb}}


def refresh_books() -> None:
    """Rewrite season.js's books block (the season-long markets) from the newest futures pull, leaving the simulation as
    the weekly run wrote it (26 Sep 2026: futures were fetched daily in the line watch but reached the page weekly)."""
    f = WEB / "season.js"
    if not f.exists():
        return
    from . import futures as FU
    try:
        books = FU.latest()
    except Exception as e:  # noqa  (no futures pulled yet: the block stays as it is)
        print("futures not read:", str(e)[:200], flush=True); return
    s = f.read_text(); j = json.loads(s[s.index("=") + 1:].rstrip().rstrip(";"))
    if j.get("books") != books:
        j["books"] = books
        f.write_text("window.SEASON=" + json.dumps(j, default=clean, separators=(",", ":")) + ";")



def export_rankings_and_methods():
    from . import ratings as R, backtest as bt
    tg = pd.read_parquet(OUT / "team_games.parquet")
    played = tg[tg.pf.notna()].copy()
    played["plays"] = played.plays.fillna(played.plays.mean())
    games = pd.read_parquet(OUT / "games.parquet")
    feats = M.with_trends(pd.read_parquet(OUT / "features_asof.parquet"))
    f2 = M.prep(feats)
    p = R.DEFAULT
    # power uses the ratings only (offense and defense ratings, QB); situation and injury inputs sit at zero
    own = [k for k in M.RATING_FEATS if k.startswith("off_")] + ["qb_rating"]
    opp = [k for k in M.RATING_FEATS if k.startswith("def_")]
    out = {}
    qb_by = feats.set_index(["season", "week", "team"]).qb_rating
    for s in range(2014, 2027):
        train = f2[f2.pf.notna() & (f2.season < s) & (f2.season >= M.TRAIN_FROM)]
        m = M.fit_points(train, M.RIDGE)
        per_unit = dict(zip(M.FEATS, m[-1].coef_ / m[0].scale_))
        mean = dict(zip(M.FEATS, m[0].mean_))
        intercept = float(train.pf.mean())
        # regular-season weeks through the one holding the next unplayed game; a later "going into" is this table decayed
        last_played = int(played[played.season == s].week.max()) if (played.season == s).any() else 0
        weeks = [int(w) for w in sorted(games[(games.season == s) & (games.game_type == "REG")].week.unique()) if w <= last_played + 1]
        out[str(s)] = {}
        for w in weeks:
            Rt = R.team_ratings(played, s, w, p)
            # alternative windows for the current season only: this season equal-weight, last three weeks, last week, last season
            variants = {}
            if s == max(range(2014, 2027)) or s == int(games.season.max()):
                for kind in ["season", "last3", "last1", "lastseason"]:
                    try:
                        Rv = R.team_ratings(played, s, w, p, kind)
                    except Exception:  # noqa
                        continue
                    if len(Rv) == 0:
                        continue
                    vt = {}
                    for t in Rv.index:
                        if t not in Rt.index:
                            continue
                        row = {"off_" + st: round(float(Rv.loc[t, "off_" + st]), 5) for st in R.STATS} | {"def_" + st: round(float(Rv.loc[t, "def_" + st]), 5) for st in R.STATS}
                        row["qb_rating"] = None   # filled below from the model's QB rating
                        row["n_games"] = int(Rv.n_games.get(t, 0)) if kind != "lastseason" else 0
                        vt[t] = row
                    variants[kind] = vt
            teams = {}
            for t in Rt.index:
                row = {}
                for st in R.STATS:
                    row["off_" + st] = round(float(Rt.loc[t, "off_" + st]), 5)
                    row["def_" + st] = round(float(Rt.loc[t, "def_" + st]), 5)
                q = qb_by.get((s, w, t), np.nan)
                if pd.isna(q):
                    prev = feats[(feats.team == t) & ((feats.season < s) | ((feats.season == s) & (feats.week < w)))]
                    q = prev.qb_rating.iloc[-1] if len(prev) else R.DEFAULT.get("qb_prior", -0.12)
                row["qb_rating"] = round(float(q), 4)
                # power: points for vs an average opponent at a neutral site, and points allowed to that opponent
                # power: points for vs an average opponent at a neutral site, and points allowed to that opponent
                x_own = {k: row[k] for k in own}
                pf = intercept + sum(per_unit[k] * (x_own[k] - mean[k]) for k in own)
                x_opp = {k: row[k] for k in opp}
                pa = intercept + sum(per_unit[k] * (x_opp[k] - mean[k]) for k in opp)
                row["power_pf"], row["power_pa"], row["power"] = round(pf, 2), round(pa, 2), round(pf - pa, 2)
                row["n_games"] = int(Rt.n_games.get(t, 0))
                teams[t] = row
                for kind, vt in variants.items():
                    if t not in vt:
                        continue
                    v = vt[t]; v["qb_rating"] = row["qb_rating"]
                    xo = {k: v[k] for k in own if k in v} | {"qb_rating": row["qb_rating"]}
                    xd = {k: v[k] for k in opp if k in v}
                    vpf = intercept + sum(per_unit[k] * (xo[k] - mean[k]) for k in own)
                    vpa = intercept + sum(per_unit[k] * (xd[k] - mean[k]) for k in opp)
                    v["power_pf"], v["power_pa"], v["power"] = round(vpf, 2), round(vpa, 2), round(vpf - vpa, 2)
            out[str(s)][str(w)] = {"mu": {st: round(float(Rt.attrs[f"mu_{st}"]), 5) for st in R.STATS},
                                   "h": {st: round(float(Rt.attrs[f"hfa_{st}"]), 5) for st in R.STATS}, "teams": teams,
                                   "windows": {k: v for k, v in variants.items() if v}}
        print("rankings", s, flush=True)
    season_end = {str(k): int(v) for k, v in played.groupby("season").week.max().items()}
    try:   # the Rankings matchup for the week being priced, on the model's full path (the blend and the total's share-out)
        ls = str(max(int(k) for k in out)); lw = str(max(int(k) for k in out[ls])); mu_ = matchup_matrix(f2, int(ls), int(lw), out[ls][lw]["teams"])
    except Exception as e:  # noqa
        print("matchup matrix failed:", str(e)[:200], flush=True); mu_ = {"error": str(e)[:200]}
    (WEB / "rankings.js").write_text("window.RANK=" + json.dumps({"params": p, "season_end": season_end, "plays_fill": round(float(played.plays.mean()), 4), "seasons": out, "matchup": mu_}, default=clean, separators=(",", ":")) + ";")
    print("rankings.js", (WEB / "rankings.js").stat().st_size / 1e6, "MB")
    export_backtest_js(games, feats)


def export_backtest_js(games=None, feats=None):
    """backtest.js: every priced regular-season game 2019 to now with the model's numbers, Vegas and the result; the
    Results tab grades everything from this file, so it is rewritten on every export (it was only written with
    --rankings until 23 Sep 2026, which left the Results tab on a stale model)."""
    from . import backtest as bt
    games = pd.read_parquet(OUT / "games.parquet") if games is None else games
    feats = M.with_trends(pd.read_parquet(OUT / "features_asof.parquet")) if feats is None else feats
    gd = games.set_index("game_id").gameday
    allv = bt.join(pd.read_parquet(OUT / "pred_v3.parquet"))
    allv = allv[allv.game_type.isin(["REG", "WC", "DIV", "CON", "SB"])].sort_values(["season", "week", "game_id"])   # playoffs kept for the by-week table; the page filters REG elsewhere
    gd = games.set_index("game_id").gameday
    cols = ["game_id", "season", "week", "game_type", "away_team", "home_team", "away_exp", "home_exp", "away_implied", "home_implied", "away_score", "home_score",
            "spread_line", "total_line", "p_home", "p_cover_home", "p_over", "model_spread", "model_total"]
    bk = allv[cols + ["sigma_margin"]].copy()
    if f"coef_{M.FEATS[0]}" in allv.columns:   # the fit that priced each game, so the deep dive rebuilds its expected points exactly
        bk["coef"] = allv[[f"coef_{f}" for f in M.FEATS]].round(5).values.tolist(); bk["mean"] = allv[[f"mean_{f}" for f in M.FEATS]].round(5).values.tolist(); bk["intercept"] = allv["intercept"].round(5)
    if "home_blend_adj" in allv.columns:
        bk["home_adj"] = allv["home_blend_adj"].round(6); bk["away_adj"] = allv["away_blend_adj"].round(6)
        bk["tree_spread"] = (allv["home_m_trees"] - allv["away_m_trees"]).round(4)   # the trees shadow rule's number (Bets -> Rules compared)
    if "p_over_emp" in allv.columns:
        bk["p_over_emp"] = allv["p_over_emp"].round(6)   # the totals flag's chance (Backtest -> Totals): six decimals, since four put games at 0.450044 on the flag's 0.55 line and the page's record parted from picks.rule_records
        # the calibrated over chance the cards show (27 Sep 2026), with the fit that was in force for each season (picks.over_calibrations:
        # seasons before, from OVER_CAL_FROM; the identity where none), so the tab can grade it walk-forward; the flag rule stays on p_over_emp
        from . import picks as P
        co = P.over_calibrations(pd.read_parquet(OUT / "pred_v3.parquet"), games)
        bk["p_over_cal"] = [P.over_cal_p(co[int(s_)], p_) if pd.notna(p_) and int(s_) in co else np.nan for s_, p_ in zip(allv.season, allv.p_over_emp)]
    # the calibrated win chance the cards show (27 Sep 2026), with the fit in force for each season (picks.home_calibrations: seasons before,
    # from HOME_CAL_FROM; the identity where none), so the Backtest tab's win table grades what the reader sees; p_home stays the raw chance
    from . import picks as P_
    ch = P_.home_calibrations(pd.read_parquet(OUT / "pred_v3.parquet"), games)
    bk["p_home_cal"] = [P_.home_cal_p(ch[int(s_)], p_) if pd.notna(p_) and int(s_) in ch else np.nan for s_, p_ in zip(allv.season, allv.p_home)]
    bk["gameday"] = bk.game_id.map(gd)
    ml = games.set_index("game_id"); bk["home_ml"] = bk.game_id.map(ml.home_moneyline); bk["away_ml"] = bk.game_id.map(ml.away_moneyline)   # closing moneylines, for the win-probability check
    # situational readings for the "when we were wrong" section: both sides' QB-out flag and starters out, weather, the slot
    fx = M.priced_weather(M.prep(feats)).set_index(["game_id", "team"])   # the weather each game was priced on (model.priced_weather)
    def side_val(col, which):
        out = []
        for g, h, a in zip(bk.game_id, bk.home_team, bk.away_team):
            t = h if which == "home" else a
            out.append(fx[col].get((g, t), np.nan) if (g, t) in fx.index else np.nan)
        return out
    for col in ["qb_out", "off_starters_out", "def_starters_out", "rest"]:
        bk["home_" + col] = side_val(col, "home")
        bk["away_" + col] = side_val(col, "away")
    for col in ["wind_out", "rain", "cold", "dome", "primetime", "div_game"]:
        bk[col] = side_val(col, "home")
    full = {i for i, c in enumerate(bk.columns) if c in ("p_over_emp", "p_over_cal", "p_home", "p_home_cal", "model_spread", "model_total")}   # p_home too (27 Sep 2026): the tie check rebuilds p_home_cal from it   # unrounded (clean() keeps three): 26 Sep 2026, 2022_01_TB_DAL's edge of 3.99994 rounded to 4.000 and the page flagged a game the flag rule does not
    recs = [[(None if pd.isna(v) else float(v)) if i in full else clean(v) for i, v in enumerate(r)] for r in bk.itertuples(index=False, name=None)]
    (WEB / "backtest.js").write_text("window.BACKTEST=" + json.dumps({"cols": list(bk.columns), "rows": recs}, default=clean, separators=(",", ":")) + ";")
    print("backtest.js", len(recs), "games", flush=True)






# Labels for every variant in the player-projection backtests (experiments/props_backtest*.py), so the page can show
# each round's table in words. "adopted" marks the row the page's rule took from that round.
def props_backtest_export(csv_rows):
    r1 = {"p_league": "League average per touch x his volume", "p_avg": "His yards per game, plain", "p_vol_rate": "His own rate x volume", "p_mix": "His man/zone (box, pressure) split weighted by the defense's mix", "p_rate_d50": "His rate, moved half way toward the defense",
          "p_mix_d25": "The split mix, moved a quarter toward the defense", "p_mix_d50": "The split mix, moved half way toward the defense (the first version on the page)", "p_mix_d100": "The split mix, moved all the way to the defense", "p_tgt_avg": "His targets per game", "p_tgt_share": "His share of the team's pass plays x the team's pass plays"}
    for k in [25, 50, 100, 200, 400, 800]:
        r1[f"s{k}"] = f"His rate shrunk toward the league, {k} touches of weight"; r1[f"s{k}_d25"] = f"Shrunk ({k}), moved a quarter toward the defense"; r1[f"s{k}_d50"] = f"Shrunk ({k}), moved half way toward the defense"
    r2 = {"v1": "Round one's rule (baseline)", "A_90": "Usage and rate decayed 0.90 per game back", "A_95": "Usage and rate decayed 0.95", "A_90_vol": "Usage decayed 0.90, rate flat", "A_95_vol": "Usage decayed 0.95, rate flat", "B": "Game script: the team's pass plays from the closing spread and total",
          "C25": "Defense by position (WR, TE, RB), a quarter of the way", "C50": "Defense by position, half of the way", "D": "Coverage-specific usage: his target share against man and zone, weighted by the defense's man rate", "D_half": "Half coverage-specific usage, half plain",
          "E25": "Route mix x what the defense allows per route, a quarter", "E50": "Route mix, half", "E100": "Route mix, fully", "F": "The head coach's pass rate over expected", "G": "Yards per target rebuilt from catch rate, depth of target and yards after catch",
          "vol_v1": "Targets from usage share (baseline)", "vol_B": "Targets with the game script", "vol_A95": "Targets from usage decayed 0.95"}
    r3 = {"v1": "Round one's rule, flat 17 games (baseline)", "A90": "Usage decayed 0.90", "A85": "Usage decayed 0.85", "B": "Game script only", "A90B": "Decayed 0.90 and game script", "A85B": "Decayed 0.85 and game script", "v1_med": "Round one's rule x median factor", "A90B_med": "Decayed 0.90, game script, median factor", "A85B_med": "Decayed 0.85, game script, median factor",
          "vol_flat": "Volume from flat usage", "vol_90": "Volume from usage decayed 0.90", "vol_gs": "Volume decayed 0.90 with the game script"}
    r4 = {"base": "Round three's rule (baseline)", "wind10": "Wind: the line cut per mph above 10 at kickoff", "windlin": "Wind, linear in every mph", "pace25": "Opponent pace: its allowed plays per game blended in, a quarter", "pace50": "Opponent pace, half", "qb_level": "The QB's as-of rating, as a level", "qb_change": "The QB's rating as the change from the QBs he had over his window",
          "own_prior": "His own long-run rate (decayed 0.95) as the shrinkage prior", "home": "Home and away", "combo": "Opponent pace a quarter and wind together"}
    for k in [15, 25, 50, 100, 200, 400]:
        for w in ["0.0", "0.25", "0.5"]:
            r4[f"K{k}_W{w}"] = f"Shrinkage {k} touches, defense weight {w}"
    r5 = {"catch_raw": "His raw catch rate (as the page had it)", "catch_league": "League catch rate", "catch_K25_med": "Shrunk 25 x median factor 0.88", "td_raw": "His raw touchdown rate (as the page had it)", "td_league": "League touchdown rate", "td_K200_gs": "Shrunk 200 x (1 + 0.020 x expected margin)", "td_K400_gs": "Shrunk 400 x (1 + 0.020 x expected margin)",
          "int_raw": "His raw interception rate (as the page had it)", "int_league": "League interception rate"}
    for k in [25, 50, 100, 200, 400, 800]:
        for pre in ["catch", "td", "int"]:
            r5.setdefault(f"{pre}_K{k}", f"Shrunk toward the league, {k} touches of weight")
    adopted = {1: {"rec_yards": "s100_d25", "rush_yards": "s25_d25", "pass_yards": "s50_d50", "targets": "p_tgt_share"}, 2: {"rec_yards": "A_90_vol", "targets": "vol_B"}, 3: {"rec_yards": "A85B_med", "rush_yards": "A85B_med", "pass_yards": "A85B_med", "rec_volume": "vol_gs", "rush_volume": "vol_gs"},
               4: {"rec_yards": "base", "rush_yards": "base", "pass_yards": "combo"}, 5: {"rec_catch": "catch_K25_med", "rec_td": "td_K200_gs", "rush_td": "td_K200", "pass_td": "td_K400_gs", "pass_int": "int_league"}}
    r7 = {"tk_avg": "His tackles a game, plain", "tk_flat": "His flat share of the team's tackles x tackles per play x opponent plays", "tk_85": "Share decayed 0.85", "tk_90": "Share decayed 0.90", "tk_85gs": "Share decayed 0.85, opponent plays with the game script", "tk_85gs_K2": "That, shrunk toward his own average (2 games of weight)", "tk_85gs_K4": "Shrunk toward his own average (4 games)", "tk_85gs_K8": "Shrunk toward his own average (8 games)", "tk_85gs_med": "Share decayed 0.85, game script, x median factor 0.90",
          "sk_avg": "His sacks a game, plain", "sk_league": "League sack rate per play x opponent plays", "sk_K100": "His rate per play faced shrunk to the league, 100 plays of weight", "sk_K300": "Shrunk, 300 plays", "sk_K600": "Shrunk, 600 plays", "sk_K1000": "Shrunk, 1,000 plays"}
    adopted[7] = {"def_tackles": "tk_85gs_med", "def_sacks": "sk_K300"}
    r8 = {"l_avg": "His game-longest, plain average of his last 17 (baseline)", "l_85": "Decayed 0.85 per game back", "l_90": "Decayed 0.90", "l_85_K2": "Decayed 0.85, shrunk toward his position's league average (2 games of weight)", "l_85_K4": "Shrunk, 4 games", "l_85_K8": "Shrunk, 8 games", "l_85_K16": "Shrunk, 16 games",
          "l_blend": "Blend: a + b x decayed longest + c x his yards per game (fitted 2016 to 2018)", "l_85_K_med": "Shrunk (best K) x median factor", "l_blend_med": "The blend x median factor"}
    adopted[8] = {"rec_longest": "l_blend_med", "rush_longest": "l_blend_med", "pass_longest": "l_blend_med"}
    r9 = {"k_avg": "His kicking points a game, plain average of his last 17 (baseline)", "k_85": "His own, decayed 0.85 per game back", "k_team85": "His team's kicking points a game, decayed 0.85 (any kicker)", "k_tt": "a + b x the team's implied total from the closing line", "k_blend_own": "Blend: his own decayed rate and the implied total", "k_blend_team": "Blend: the team's decayed rate and the implied total", "k_blend_med": "The better blend x median factor",
          "g_avg": "His field goals made a game, plain average (baseline)", "g_85": "His own, decayed 0.85", "g_team85": "His team's field goals a game, decayed 0.85", "g_tt": "a + b x the team's implied total", "g_blend_own": "Blend: his own decayed rate and the implied total", "g_blend_team": "Blend: the team's decayed rate and the implied total", "g_blend_med": "The better blend x median factor"}
    adopted[9] = {"kick_points": "k_blend_team", "field_goals": "g_blend_team"}
    r10 = {"none": "No redistribution: his share x the team's plays (baseline)", "pro_rata": "An absent teammate's share handed to the rest pro rata (as the page did)", "pro_rata_half": "Half of it pro rata", "same_pos": "To the same position group in full", "same_pos_half": "To the same position group by half",
           "league_prior": "His rate shrunk toward the league average (the rule)", "xtd_only": "Expected touchdowns from where he is targeted or handed the ball, alone", "xtd_prior_K100": "His rate shrunk toward his expected rate, 100 touches", "xtd_prior_K200": "Shrunk toward his expected rate, 200 touches", "xtd_prior_K400": "Shrunk toward his expected rate, 400 touches", "xtd_prior_K800": "Shrunk toward his expected rate, 800 touches", "xtd_prior_shrunk": "Shrunk toward his expected rate, itself shrunk toward the league (50 touches)",
           "season_0.5": "Usage before a season boundary at half weight", "season_0.25": "Usage before a season boundary at a quarter", "team_0.5": "Usage with a previous team at half weight", "team_0.25": "Usage with a previous team at a quarter", "both_0.5": "Season boundary and team change both at half", "both_0.25": "Both at a quarter", "season_0.25_team_0.5": "Season boundary a quarter, team change half", "season_0.5_team_0.25": "Season boundary half, team change a quarter"}
    r10["none_fade"] = "No fade (the rule before round ten)"
    adopted[10] = {"rec_redistribution": "none", "rush_redistribution": "none", "rec_fade": "both_0.5", "rush_fade": "season_0.25_team_0.5"}
    rounds = [(1, "Round one: rate, splits and shrinkage", "props_backtest.csv", r1, "Each stat's volume from usage share; the rate his own, the league's, or his look-by-look split weighted by the defense's mix, then shrunk toward the league and moved toward the defense."),
              (2, "Round two: what a book adds, one layer at a time (receiving yards)", "props_backtest2.csv", r2, "Each layer on round one's rule. Recency and game script were carried into round three; the rest tested worse or no better."),
              (3, "Round three: recency, game script and the median factor", "props_backtest3.csv", r3, "Constants fitted on 2016 to 2018 and applied forward. The bottom row is the rule adopted for every stat."),
              (4, "Round four: wind, pace, the quarterback, own prior, home, and the weights re-tuned", "props_backtest4.csv", r4, "Each on round three's rule. Only passing moved on both windows (pace and wind); receiving and rushing stayed."),
              (5, "Round five: receptions, touchdowns and interceptions", "props_backtest5.csv", r5, "Absolute error for receptions; Poisson log loss (lower is better) for scores and picks, where predicting none is trivially best by absolute error."),
              (6, "Round six: tied to the game model's expected points", "props_backtest6.csv", {"yds_vegas": "As adopted (closing spread and total)", "yds_model": "Game script from the model's margin and total", "yds_blend": "Half and half with the closing line", "yds_recon25": "Reconciled to the team's expected points, a quarter of the way", "yds_recon50": "Reconciled, half", "yds_recon100": "Reconciled, all the way", "td_vegas": "As adopted", "td_model": "Game script from the model's margin", "td_blend": "Half and half", "td_recon25": "Reconciled, a quarter", "td_recon50": "Reconciled, half", "td_recon100": "Reconciled, all the way"}, "Each team's players scaled toward the yards and touchdowns its expected points imply (fitted 2016 to 2018). The model's margin in place of the line changed nothing; the reconciliation helped every stat."),
              (7, "Round seven: defenders (tackles plus assists, sacks)", "props_backtest7.csv", r7, "From every tackle and assist credit in the play-by-play since 2016. Tackles by absolute error; sacks by Poisson log loss as well."),
              (8, "Round eight: longest reception, rush and completion", "props_backtest8.csv", r8, "The longest gain of the game per player (0 when none), from his previous games. Absolute error in yards; constants fitted on 2016 to 2018."),
              (9, "Round nine: kickers (kicking points, field goals made)", "props_backtest9.csv", r9, "One kicker per team and game from the raw play-by-play since 2016. Absolute error; blends fitted on 2016 to 2018. The median factor did not help on both windows, so the plain blend is the rule."),
              (10, "Round ten: redistribution when a teammate is out, red-zone role, offseason fade", "props_backtest10.csv", r10, "Three player-side claims on the adopted rule. Redistribution: absolute error on the yards line (volume error in the source file). Red-zone role: Poisson log loss on touchdowns. Fade: absolute error on the yards line.")]
    adopted[6] = {"rec_yards": "yds_recon25", "rush_yards": "yds_recon25", "pass_yards": "yds_recon50", "rec_td": "td_recon50", "rush_td": "td_recon50", "pass_td": "td_recon100"}
    out = {"rounds": [], "by_season": csv_rows("props_by_season.csv"), "by_position": csv_rows("props_by_position.csv"), "by_bucket": csv_rows("props_by_bucket.csv"), "market_backtest": csv_rows("props_vs_market_backtest.csv")}
    for n, title, src, labels, note in rounds:
        rows = csv_rows(src); stats = {}
        for r in rows:
            if r["stat"] == "game_script" or str(r["stat"]).endswith("_team_fit"):
                continue
            r = dict(r); r["label"] = labels.get(r["variant"], r["variant"]); r["adopted"] = adopted[n].get(r["stat"]) == r["variant"]; stats.setdefault(r["stat"], []).append(r)
        out["rounds"].append({"round": n, "title": title, "source": "reports/" + src, "note": note, "stats": stats, "n_rows": len(rows)})
    return out


if __name__ == "__main__":
    import sys
    export_week() if "--week" in sys.argv else main()
