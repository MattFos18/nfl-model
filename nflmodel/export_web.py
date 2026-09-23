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
    "m_win": ("Model", "3.0 win probability", "model.py", False, False), "m_cover": ("Model", "3.0 probability of covering the closing spread", "model.py", False, False),
    "m_over": ("Model", "3.0 probability the game goes over the closing total", "model.py", False, False),
}


def used_by_v3(col: str):
    """Whether a column feeds the current model, derived from model.FEATS so the page's markers follow the input set."""
    F = set(M.FEATS)
    if col.startswith("r_"):
        return col[2:] in F
    raw = {"pf": True, "pa": True, "home": True, "epa_play": True, "def_epa_play": True, "qb_name": True, "qb_rating": True, "qb_out": "qb_out" in F,
           "dome": "dome" in F, "wind": "wind_out" in F, "rain": "rain" in F, "snow": "snow" in F, "warm_in_cold": "warm_in_cold" in F, "temp": "cold" in F, "rest": "rest_short" in F or "rest_long" in F,
           "opp_rest": "opp_rest_short" in F or "opp_rest_long" in F, "div_game": "div_game" in F, "primetime": "primetime" in F,
           "pass_epa": "off_pass_epa" in F, "def_pass_epa": "def_pass_epa" in F, "rush_epa": "off_rush_epa" in F, "def_rush_epa": "def_rush_epa" in F,
           "plays": "off_plays" in F, "def_plays": "def_plays" in F, "opp_qb_rating": "opp_qb_rating" in F, "success": "off_success" in F, "def_success": "def_success" in F}
    return bool(raw.get(col, False))


def describe(col: str):
    out = _describe(col)
    out["used_v3"] = used_by_v3(col)
    return out


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
    for k in M.SIT_FEATS + ["qb_out"]:
        if k == "wind_out" or k not in f.columns:
            continue
        on, off = f[f[k] == 1], f[f[k] == 0]
        out["flags"][k] = {"n_on": int(len(on)), "on": round(float(on.pf.mean()), 2), "off": round(float(off.pf.mean()), 2), "diff": round(float(on.pf.mean() - off.pf.mean()), 2)}
    for lo, hi, lab in [(-1, 0, "0 (indoors or calm)"), (0, 5, "1 to 5"), (5, 10, "6 to 10"), (10, 15, "11 to 15"), (15, 99, "16+")]:
        x = f[(f.wind_out > lo) & (f.wind_out <= hi)]
        out["wind"].append({"bucket": lab, "n": int(len(x)), "pf": round(float(x.pf.mean()), 2)})
    # the tested-and-not-used situations, raw: points scored and the margin against the closing spread with the flag on vs off
    out["tested"] = {}
    for k in ["snow", "primetime", "div_game", "rest_short", "rest_long", "body_clock_early"]:
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
    # model prediction from this team's view
    pv = pred.set_index("game_id")
    d["gameday"] = d.game_id.map(games.gameday)
    # beyond the week holding the next unplayed game, an "as-of" rating is just this week's number decayed and the starter is a
    # guess, so those rows carry no ratings, QB or model columns: the page shows them blank rather than as a forecast
    cur_s = int(games.season.max())
    played_w = games[(games.season == cur_s) & games.home_score.notna()].week.max()
    cutoff = int(played_w) + 1 if pd.notna(played_w) else 1
    future = (d.season == cur_s) & (d.week > cutoff)
    d.loc[future, ["r_" + c for c in rcols] + ["qb_rating", "opp_qb_rating"]] = np.nan
    pv = pv[~((pv.season == cur_s) & (pv.week > cutoff))]
    d["m_exp_pf"] = [pv.home_exp.get(g, np.nan) if h else pv.away_exp.get(g, np.nan) for g, h in zip(d.game_id, d.home)]
    d["m_exp_pa"] = [pv.away_exp.get(g, np.nan) if h else pv.home_exp.get(g, np.nan) for g, h in zip(d.game_id, d.home)]
    d["m_win"] = [pv.p_home.get(g, np.nan) if h else 1 - pv.p_home.get(g, np.nan) for g, h in zip(d.game_id, d.home)]
    d["m_cover"] = [pv.p_cover_home.get(g, np.nan) if h else 1 - pv.p_cover_home.get(g, np.nan) for g, h in zip(d.game_id, d.home)]
    d["m_over"] = d.game_id.map(pv.p_over)
    d["team_spread"] = np.where(d.home, d.spread_line, -d.spread_line)
    d = d.sort_values(["season", "week"])
    cols = [c for c in d.columns if c not in ("game_id",)]
    dictionary = {c: describe(c) for c in cols if c not in ("season", "week", "game_type", "team", "opp", "home", "gameday", "qb_id")}
    # coefficients per season, in points per unit and the training means (for the contribution view)
    f2 = M.prep(feats)
    coefs = {}
    for s in range(2019, 2027):
        train = f2[f2.pf.notna() & (f2.season < s) & (f2.season >= 2013)]
        m = M.fit_points(train, 10.0)
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
                "situation_facts": situation_facts(feats)}
    analysis["home_edges"] = team_home_edges(tg)
    meta = {"columns": cols, "dictionary": dictionary, "coefs": coefs, "feats": M.FEATS, "teams": teams, "analysis": analysis, "warm_or_dome": sorted(M.WARM_OR_DOME),
            "pull_log": pull.to_dict("records"), "verification": ver, "built": pd.Timestamp.now("UTC").strftime("%Y-%m-%d %H:%M UTC")}
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
        (WEB / "players.js").write_text("window.PLAYERS=" + json.dumps({"season": int(ph.season.max()), "values": [{k: clean(v) for k, v in r.items()} for r in pvals.drop(columns=[c for c in ["basis"] if c in pvals.columns]).to_dict("records")], "basis": {g: b for g, b in pvals.groupby("group").basis.first().items()} if "basis" in pvals.columns else {},
                                                                          "history": hist, "names": names, "hist_cols": ["season", "team", "role", "games", "plays", "epa_play"]}, default=clean, separators=(",", ":")) + ";")
    pj = OUT / "props.json"
    if pj.exists():   # player-against-scheme projections for the week (nflmodel/props.py)
        (WEB / "props.js").write_text("window.PROPS=" + pj.read_text() + ";")
    (WEB / "props_backtest.js").write_text("window.PROPS_BT=" + json.dumps(props_backtest_export(csv_rows), default=clean) + ";")   # the five backtest rounds and the by-season run (Results -> Player projections)
    sp = OUT / "scheme_profiles.json"
    if sp.exists():   # scheme and play-calling profiles (nflmodel/scheme.py), as of the current week
        (WEB / "scheme.js").write_text("window.SCHEME=" + sp.read_text() + ";")
    for t in teams:
        rows = d[d.team == t]
        allc = ["game_id"] + cols
        recs = [[clean(v) for v in r] for r in rows[allc].itertuples(index=False, name=None)]
        players = [{k: clean(v) for k, v in r.items()} for r in pvals[pvals.team == t].drop(columns=["team"]).to_dict("records")]
        roster = [{k: clean(v) for k, v in r.items()} for r in rnow[rnow.team == t].drop(columns=["team"]).to_dict("records")] if len(rnow) else []
        (WEB / f"{t}.js").write_text(f'window.TEAMDATA=window.TEAMDATA||{{}};window.TEAMDATA["{t}"]=' + json.dumps({"cols": allc, "rows": recs, "players": players, "roster": roster}, default=clean, separators=(",", ":")) + ";")
    # this week's picks and the track record for the dashboard tabs
    from . import lines as LN, picks as P, tracker as TK
    cur_season, cur_week = LN.current_week(pd.read_parquet(OUT / "games.parquet"))
    try:
        pk = P.table(cur_season, cur_week)
        fp = M.prep(feats).set_index(["game_id", "team"])
        side_cols = M.FEATS + ["r_" + c for c in rcols if c in feats.columns] + ["qb_name", "rest", "temp", "wind", "dome"] + M.TREND_FEATS
        from . import weather as WX
        wxs = WX.status_by_game(games.reset_index())
        # the coming week's starters are carried forward by id (ratings.py); give the card the name
        gq = games.reset_index()
        qb_names = {**dict(zip(gq.home_qb_id, gq.home_qb_name)), **dict(zip(gq.away_qb_id, gq.away_qb_name))}
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
        wk = []
        for r in pk.itertuples():
            h = LN.history(r.game_id)
            sides = {}
            for tm in [r.home_team, r.away_team]:
                if (r.game_id, tm) in fp.index:
                    row = fp.loc[(r.game_id, tm)]
                    sides[tm] = {c: clean(row[c]) for c in M.FEATS + ["qb_name", "rest", "temp", "wind", "dome"] + M.TREND_FEATS if c in row.index}
                    sides[tm]["skill_out_players"] = out_detail(r.game_id, tm)
                    if not sides[tm].get("qb_name") and "qb_id" in row.index and isinstance(row["qb_id"], str):
                        sides[tm]["qb_name"] = qb_names.get(row["qb_id"])
                        sides[tm]["qb_carried"] = True
            gmeta = games.loc[r.game_id] if r.game_id in games.index else None
            wk.append({k: clean(v) for k, v in r._asdict().items() if k != "Index"} | {"season": cur_season, "week": cur_week, "sides": sides,
                       "kickoff": str(gmeta.kickoff_et)[:16] if gmeta is not None else None, "roof": gmeta.roof if gmeta is not None else None,
                       "referee": gmeta.referee if gmeta is not None else None, "stadium": gmeta.stadium if gmeta is not None else None,
                       "wx": wxs.get(r.game_id), "runs": [{"run_at": x.run_at, "model_spread": clean(x.model_spread), "model_total": clean(x.model_total), "spread_line": clean(x.spread_line), "total_line": clean(x.total_line), "bet": x.bet if isinstance(x.bet, str) else ""} for x in hist_runs[hist_runs.game_id == r.game_id].itertuples()], "home_coach": gmeta.home_coach if gmeta is not None else None, "away_coach": gmeta.away_coach if gmeta is not None else None,
                       "home_ml": clean(gmeta.home_moneyline) if gmeta is not None else None, "away_ml": clean(gmeta.away_moneyline) if gmeta is not None else None,
                      "line_history": [{"ts": t, "source": src, "home_spread": clean(hs), "total": clean(tt), "home_ml": clean(hm), "away_ml": clean(am)}
                                       for t, src, hs, tt, hm, am in zip(h.ts, h.source, h.home_spread, h.total, h.get("home_ml", pd.Series([None] * len(h))), h.get("away_ml", pd.Series([None] * len(h))))] if len(h) else []})
        (WEB / "week.js").write_text("window.WEEK=" + json.dumps({"season": cur_season, "week": cur_week, "games": wk, "spread_edge": P.SPREAD_EDGE, "total_edge": P.TOTAL_EDGE}, default=clean, separators=(",", ":")) + ";")
    except Exception as e:  # noqa
        (WEB / "week.js").write_text("window.WEEK=" + json.dumps({"error": str(e)[:200]}) + ";")
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
        train = f2[f2.pf.notna() & (f2.season < s) & (f2.season >= 2013)]
        m = M.fit_points(train, 10.0)
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
    (WEB / "rankings.js").write_text("window.RANK=" + json.dumps({"params": p, "season_end": season_end, "plays_fill": round(float(played.plays.mean()), 4), "seasons": out}, default=clean, separators=(",", ":")) + ";")
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
    bk["gameday"] = bk.game_id.map(gd)
    # situational readings for the "when we were wrong" section: both sides' QB-out flag and starters out, weather, the slot
    fx = M.prep(feats).set_index(["game_id", "team"])
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
    recs = [[clean(v) for v in r] for r in bk.itertuples(index=False, name=None)]
    (WEB / "backtest.js").write_text("window.BACKTEST=" + json.dumps({"cols": list(bk.columns), "rows": recs}, default=clean, separators=(",", ":")) + ";")
    print("backtest.js", len(recs), "games", flush=True)




if __name__ == "__main__":
    main()


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
    rounds = [(1, "Round one: rate, splits and shrinkage", "props_backtest.csv", r1, "Each stat's volume from usage share; the rate his own, the league's, or his look-by-look split weighted by the defense's mix, then shrunk toward the league and moved toward the defense."),
              (2, "Round two: what a book adds, one layer at a time (receiving yards)", "props_backtest2.csv", r2, "Each layer on round one's rule. Recency and game script were carried into round three; the rest tested worse or no better."),
              (3, "Round three: recency, game script and the median factor", "props_backtest3.csv", r3, "Constants fitted on 2016 to 2018 and applied forward. The bottom row is the rule adopted for every stat."),
              (4, "Round four: wind, pace, the quarterback, own prior, home, and the weights re-tuned", "props_backtest4.csv", r4, "Each on round three's rule. Only passing moved on both windows (pace and wind); receiving and rushing stayed."),
              (5, "Round five: receptions, touchdowns and interceptions", "props_backtest5.csv", r5, "Absolute error for receptions; Poisson log loss (lower is better) for scores and picks, where predicting none is trivially best by absolute error.")]
    out = {"rounds": [], "by_season": csv_rows("props_by_season.csv"), "by_position": csv_rows("props_by_position.csv"), "by_bucket": csv_rows("props_by_bucket.csv"), "market_backtest": csv_rows("props_vs_market_backtest.csv")}
    for n, title, src, labels, note in rounds:
        rows = csv_rows(src); stats = {}
        for r in rows:
            if r["stat"] == "game_script":
                continue
            r = dict(r); r["label"] = labels.get(r["variant"], r["variant"]); r["adopted"] = adopted[n].get(r["stat"]) == r["variant"]; stats.setdefault(r["stat"], []).append(r)
        out["rounds"].append({"round": n, "title": title, "source": "reports/" + src, "note": note, "stats": stats, "n_rows": len(rows)})
    return out
