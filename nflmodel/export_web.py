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
    "wind_edge": ("Trends (shown, not used)", "Team's windy-game margin edge, applied when windy", "trends.py", False, True),
    "off_home_split": ("Trends (shown, not used)", "Home minus away EPA/play, shrunk", "trends.py", False, True),
    "off_starters_out": ("Injuries", "Offense starters (50%+ snaps last game) listed Out/Doubtful", "injuries + snap counts", False, True),
    "def_starters_out": ("Injuries", "Defense starters listed Out/Doubtful", "injuries + snap counts", False, True),
    "qb_out": ("Injuries", "Last game's starting QB listed Out/Doubtful", "injuries + snap counts", True, True),
    # model
    "m_exp_pf": ("Model", "3.0 expected points for this team", "model.py", False, False), "m_exp_pa": ("Model", "3.0 expected points against", "model.py", False, False),
    "m_win": ("Model", "3.0 win probability", "model.py", False, False), "m_cover": ("Model", "3.0 probability of covering the closing spread", "model.py", False, False),
    "m_over": ("Model", "3.0 probability the game goes over the closing total", "model.py", False, False),
    "old_exp_pf": ("Model", "Old sheet model's expected points for this team", "baseline.py", False, False),
}


def describe(col: str):
    if col.startswith("box_"):
        return describe(col[4:])
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


def main():
    WEB.mkdir(parents=True, exist_ok=True)
    tg = pd.read_parquet(OUT / "team_games.parquet")
    box = pd.read_parquet(OUT / "team_box.parquet")
    feats = M.with_trends(pd.read_parquet(OUT / "features_asof.parquet"))
    pred = pd.read_parquet(OUT / "pred_v3.parquet")
    base = pd.read_parquet(OUT / "pred_baseline.parquet")
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
    bv = base.set_index("game_id")
    d["gameday"] = d.game_id.map(games.gameday)
    d["m_exp_pf"] = [pv.home_exp.get(g, np.nan) if h else pv.away_exp.get(g, np.nan) for g, h in zip(d.game_id, d.home)]
    d["m_exp_pa"] = [pv.away_exp.get(g, np.nan) if h else pv.home_exp.get(g, np.nan) for g, h in zip(d.game_id, d.home)]
    d["m_win"] = [pv.p_home.get(g, np.nan) if h else 1 - pv.p_home.get(g, np.nan) for g, h in zip(d.game_id, d.home)]
    d["m_cover"] = [pv.p_cover_home.get(g, np.nan) if h else 1 - pv.p_cover_home.get(g, np.nan) for g, h in zip(d.game_id, d.home)]
    d["m_over"] = d.game_id.map(pv.p_over)
    d["old_exp_pf"] = [bv.home_exp.get(g, np.nan) if h else bv.away_exp.get(g, np.nan) for g, h in zip(d.game_id, d.home)]
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
    teams = sorted(d[d.season == 2026].team.unique())
    REPD = ROOT / "reports"
    def csv_rows(name):
        f = REPD / name
        return pd.read_csv(f).round(4).to_dict("records") if f.exists() else []
    def txt(name):
        f = REPD / name
        return f.read_text() if f.exists() else ""
    tun = pd.read_csv(REPD / "tuning_ratings.csv") if (REPD / "tuning_ratings.csv").exists() else pd.DataFrame()
    analysis = {"correlations": csv_rows("lab_stat_correlations.csv"), "reliability": csv_rows("lab_stat_reliability.csv"),
                "ablation": csv_rows("ablation.csv"), "additions": csv_rows("additions.csv"), "persistence": csv_rows("trend_persistence.csv"),
                "tuning_best": tun.sort_values("team_mae").head(10).round(4).to_dict("records") if len(tun) else [],
                "tuning_by": {k: tun.groupby(k).team_mae.mean().round(4).to_dict() for k in ["decay", "prior", "alpha", "ridge"]} if len(tun) else {},
                "decision_log": txt("decision_log.md"), "audit": txt("audit.md"), "backtest_report": txt("backtest_v3.md"), "verification": txt("verification.md"),
                "how_it_works": (ROOT / "docs" / "how_it_works.md").read_text() if (ROOT / "docs" / "how_it_works.md").exists() else ""}
    meta = {"columns": cols, "dictionary": dictionary, "coefs": coefs, "feats": M.FEATS, "teams": teams, "analysis": analysis,
            "pull_log": pull.to_dict("records"), "verification": ver, "built": pd.Timestamp.now("UTC").strftime("%Y-%m-%d %H:%M UTC")}
    (WEB / "meta.js").write_text("window.META=" + json.dumps(meta, default=clean, separators=(",", ":")) + ";")
    for t in teams:
        rows = d[d.team == t]
        allc = ["game_id"] + cols
        recs = [[clean(v) for v in r] for r in rows[allc].itertuples(index=False, name=None)]
        (WEB / f"{t}.js").write_text(f'window.TEAMDATA=window.TEAMDATA||{{}};window.TEAMDATA["{t}"]=' + json.dumps({"cols": allc, "rows": recs}, separators=(",", ":")) + ";")
    # this week's picks and the track record for the dashboard tabs
    from . import lines as LN, picks as P, tracker as TK
    cur_season, cur_week = LN.current_week(pd.read_parquet(OUT / "games.parquet"))
    try:
        pk = P.table(cur_season, cur_week)
        bl = pd.read_parquet(OUT / "pred_baseline.parquet").set_index("game_id")
        fp = M.prep(feats).set_index(["game_id", "team"])
        side_cols = M.FEATS + ["r_" + c for c in rcols if c in feats.columns] + ["qb_name", "rest", "temp", "wind", "dome"] + M.TREND_FEATS
        wk = []
        for r in pk.itertuples():
            h = LN.history(r.game_id)
            comp = {}
            if r.game_id in bl.index:
                for k in ["overall", "two", "last3", "homeaway", "pfpa", "lastyear", "lastyear2"]:
                    comp[k] = [clean(bl.loc[r.game_id, f"{k}_away"]), clean(bl.loc[r.game_id, f"{k}_home"])]
                comp["old"] = [clean(bl.loc[r.game_id, "away_exp"]), clean(bl.loc[r.game_id, "home_exp"])]
            sides = {}
            for tm in [r.home_team, r.away_team]:
                if (r.game_id, tm) in fp.index:
                    row = fp.loc[(r.game_id, tm)]
                    sides[tm] = {c: clean(row[c]) for c in M.FEATS + ["qb_name", "rest", "temp", "wind", "dome"] + M.TREND_FEATS if c in row.index}
            gmeta = games.loc[r.game_id] if r.game_id in games.index else None
            wk.append({k: clean(v) for k, v in r._asdict().items() if k != "Index"} | {"season": cur_season, "week": cur_week, "methods": comp, "sides": sides,
                       "kickoff": str(gmeta.kickoff_et)[:16] if gmeta is not None else None, "roof": gmeta.roof if gmeta is not None else None,
                       "referee": gmeta.referee if gmeta is not None else None, "stadium": gmeta.stadium if gmeta is not None else None,
                      "line_history": [{"ts": t, "source": src, "home_spread": clean(hs), "total": clean(tt)} for t, src, hs, tt in
                                       zip(h.ts, h.source, h.home_spread, h.total)] if len(h) else []})
        (WEB / "week.js").write_text("window.WEEK=" + json.dumps({"season": cur_season, "week": cur_week, "games": wk, "spread_edge": P.SPREAD_EDGE, "total_edge": P.TOTAL_EDGE}, default=clean, separators=(",", ":")) + ";")
    except Exception as e:  # noqa
        (WEB / "week.js").write_text("window.WEEK=" + json.dumps({"error": str(e)[:200]}) + ";")
    gr = TK.TR / "graded.csv"
    g = pd.read_csv(gr).to_dict("records") if gr.exists() else []
    (WEB / "track.js").write_text("window.TRACK=" + json.dumps(g, default=clean, separators=(",", ":")) + ";")
    sizes = sum(f.stat().st_size for f in WEB.glob("*.js"))
    print(f"{len(teams)} teams, {len(cols)} columns, {sizes/1e6:.1f} MB")


if __name__ == "__main__":
    main()


# ---------------------------------------------------------------------------------------------
# Rankings, rating walkthrough tables, and methods comparison (added for the sheet-style views)
# ---------------------------------------------------------------------------------------------
def export_rankings_and_methods():
    from . import ratings as R, baseline as B, backtest as bt
    tg = pd.read_parquet(OUT / "team_games.parquet")
    played = tg[tg.pf.notna()].copy()
    played["plays"] = played.plays.fillna(played.plays.mean())
    games = pd.read_parquet(OUT / "games.parquet")
    feats = M.with_trends(pd.read_parquet(OUT / "features_asof.parquet"))
    f2 = M.prep(feats)
    p = R.DEFAULT
    own = ["off_epa_play", "off_pass_epa", "off_rush_epa", "off_pf", "off_plays", "qb_rating", "own_def_epa_play"]
    opp = ["def_epa_play", "def_pass_epa", "def_rush_epa", "def_pf", "def_plays", "opp_qb_rating", "opp_off_epa_play", "opp_off_plays"]
    own_of = {"def_epa_play": "def_epa_play", "def_pass_epa": "def_pass_epa", "def_rush_epa": "def_rush_epa", "def_pf": "def_pf", "def_plays": "def_plays",
              "opp_qb_rating": "qb_rating", "opp_off_epa_play": "off_epa_play", "opp_off_plays": "off_plays"}
    out = {}
    qb_by = feats.set_index(["season", "week", "team"]).qb_rating
    for s in range(2014, 2027):
        train = f2[f2.pf.notna() & (f2.season < s) & (f2.season >= 2013)]
        m = M.fit_points(train, 10.0)
        per_unit = dict(zip(M.FEATS, m[-1].coef_ / m[0].scale_))
        mean = dict(zip(M.FEATS, m[0].mean_))
        intercept = float(train.pf.mean())
        weeks = sorted(games[(games.season == s) & (games.game_type == "REG")].week.unique())
        # include the week after the last played week so the current standings show
        out[str(s)] = {}
        for w in weeks:
            Rt = R.team_ratings(played, s, w, p)
            teams = {}
            for t in Rt.index:
                row = {}
                for st in R.STATS:
                    row["off_" + st] = round(float(Rt.loc[t, "off_" + st]), 5)
                    row["def_" + st] = round(float(Rt.loc[t, "def_" + st]), 5)
                q = qb_by.get((s, w, t), np.nan)
                if pd.isna(q):
                    prev = feats[(feats.team == t) & ((feats.season < s) | ((feats.season == s) & (feats.week < w)))]
                    q = prev.qb_rating.iloc[-1] if len(prev) else -0.05
                row["qb_rating"] = round(float(q), 4)
                # power: points for vs an average opponent at a neutral site, and points allowed to that opponent
                x_own = {"off_epa_play": row["off_epa_play"], "off_pass_epa": row["off_pass_epa"], "off_rush_epa": row["off_rush_epa"], "off_pf": row["off_pf"],
                         "off_plays": row["off_plays"], "qb_rating": row["qb_rating"], "own_def_epa_play": row["def_epa_play"]}
                pf = intercept + sum(per_unit[k] * (x_own[k] - mean[k]) for k in own)
                x_opp = {"def_epa_play": row["def_epa_play"], "def_pass_epa": row["def_pass_epa"], "def_rush_epa": row["def_rush_epa"], "def_pf": row["def_pf"],
                         "def_plays": row["def_plays"], "opp_qb_rating": row["qb_rating"], "opp_off_epa_play": row["off_epa_play"], "opp_off_plays": row["off_plays"]}
                pa = intercept + sum(per_unit[k] * (x_opp[k] - mean[k]) for k in opp)
                row["power_pf"], row["power_pa"], row["power"] = round(pf, 2), round(pa, 2), round(pf - pa, 2)
                row["n_games"] = int(Rt.n_games.get(t, 0))
                teams[t] = row
            out[str(s)][str(w)] = {"mu": {st: round(float(Rt.attrs[f"mu_{st}"]), 5) for st in R.STATS},
                                   "h": {st: round(float(Rt.attrs[f"hfa_{st}"]), 5) for st in R.STATS}, "teams": teams}
        print("rankings", s, flush=True)
    # old-sheet strength indexes for the current season's weeks (the sheet's methods rank teams too)
    box = pd.read_parquet(OUT / "team_box.parquet")
    s = int(games.season.max())
    old = {}
    for w in sorted(games[(games.season == s) & (games.game_type == "REG")].week.unique()):
        try:
            win = B.Windows(box, s, w)
            X = {k: B.ratio(getattr(win, k + "_rates")) for k in ["season", "last3", "home", "away"]}
            S_ = {"overall": B.ts_strength(X["season"]), "two": B.two_strength(X["season"]), "last3": B.ts_strength(X["last3"]),
                  "home": B.ts_strength(X["home"], "homeaway"), "away": B.ts_strength(X["away"], "homeaway")}
            old[str(w)] = {t: {f"{k}_off": round(float(v["off"].get(t, np.nan)), 4), f"{k}_def": round(float(v["def"].get(t, np.nan)), 4)}
                           for t in win.teams for k, v in [(k, S_[k]) for k in S_]}
            # merge dict comprehension above produced only last k; rebuild properly
            old[str(w)] = {t: {f"{k}_{side}": round(float(S_[k][side].get(t, np.nan)), 4) for k in S_ for side in ["off", "def"]} for t in win.teams}
        except Exception as e:  # noqa
            old[str(w)] = {"error": str(e)[:100]}
    # methods comparison: every method's miss on 2019 to 2025 regular season
    base = bt.join(pd.read_parquet(OUT / "pred_baseline.parquet"))
    base = base[(base.game_type == "REG") & base.season.between(2019, 2025)]
    v3 = bt.join(pd.read_parquet(OUT / "pred_v3.parquet"))
    v3 = v3[(v3.game_type == "REG") & v3.season.between(2019, 2025)]
    methods = []
    for k, name, wgt in [("overall", "OVERALL|Old sheet tab: the teamrankings.com strength index (3 PPG + red zone TD + passer rating - 2 giveaways + ...), season to date, times opponent's index times league scoring", 10),
                         ("two", "2.0|Old sheet tab: the Pro-Football-Reference index, ten stats weighted by their same-season correlation with points", 35),
                         ("last3", "LAST 3|Old sheet tab: the teamrankings index on the last three games only", 35), ("homeaway", "HOME/AWAY|Old sheet tab: the same index on home-only and away-only splits", 15),
                         ("pfpa", "PF/PA|Old sheet tab: the season index scaled by the team's own points for and against instead of the league average", 5),
                         ("lastyear", "LAST YEAR|Old sheet tab: OVERALL on last season's stats", 0), ("lastyear2", "LAST YEAR 2.0|Old sheet tab: 2.0 on last season's stats", 0)]:
        e = np.concatenate([(base[f"{k}_home"] - base.home_score).values, (base[f"{k}_away"] - base.away_score).values])
        mg = (base[f"{k}_home"] - base[f"{k}_away"] - base.result).values
        short, desc = name.split("|")
        methods.append({"key": k, "name": name, "short": short, "desc": desc, "weight": wgt, "team_mae": round(float(np.nanmean(np.abs(e))), 2), "margin_mae": round(float(np.nanmean(np.abs(mg))), 2)})
    e = np.concatenate([base.home_err.values, base.away_err.values])
    methods.append({"key": "old", "short": "Sheet blend", "desc": "The old sheet's final number: weighted average of the tabs above (10/35/35/15/5, last-year tabs 0), then a Poisson grid for the odds", "name": "Sheet blend", "weight": None, "team_mae": round(float(np.abs(e).mean()), 2), "margin_mae": round(float(np.abs(base.margin_err).mean()), 2)})
    e = np.concatenate([v3.home_err.values, v3.away_err.values])
    methods.append({"key": "v3", "short": "3.0", "desc": "One method: opponent-adjusted decayed ratings and the situation, through a regression refit each season; the fitted coefficients are the weights (Inputs tab)", "name": "3.0", "weight": None, "team_mae": round(float(np.abs(e).mean()), 2), "margin_mae": round(float(np.abs(v3.margin_err).mean()), 2)})
    e = np.concatenate([v3.v_home_err.values, v3.v_away_err.values])
    methods.append({"key": "vegas", "short": "Vegas close", "desc": "Implied team totals from the closing spread and total", "name": "Vegas", "weight": None, "team_mae": round(float(np.abs(e).mean()), 2), "margin_mae": round(float(np.abs(v3.v_margin_err).mean()), 2)})
    # backtest: every priced game 2019 to now with model, Vegas and actual, plus the old sheet's score
    allv = bt.join(pd.read_parquet(OUT / "pred_v3.parquet"))
    allv = allv[allv.game_type == "REG"].sort_values(["season", "week", "game_id"])
    bl = pd.read_parquet(OUT / "pred_baseline.parquet").set_index("game_id")
    gd = games.set_index("game_id").gameday
    cols = ["game_id", "season", "week", "away_team", "home_team", "away_exp", "home_exp", "away_implied", "home_implied", "away_score", "home_score",
            "spread_line", "total_line", "p_home", "p_cover_home", "p_over"]
    bk = allv[cols].copy()
    bk["gameday"] = bk.game_id.map(gd)
    bk["old_away"] = bk.game_id.map(bl.away_exp)
    bk["old_home"] = bk.game_id.map(bl.home_exp)
    recs = [[clean(v) for v in r] for r in bk.itertuples(index=False, name=None)]
    (WEB / "backtest.js").write_text("window.BACKTEST=" + json.dumps({"cols": list(bk.columns), "rows": recs}, default=clean, separators=(",", ":")) + ";")
    season_end = {str(k): int(v) for k, v in played.groupby("season").week.max().items()}
    (WEB / "rankings.js").write_text("window.RANK=" + json.dumps({"params": p, "season_end": season_end, "plays_fill": round(float(played.plays.mean()), 4), "seasons": out, "old_sheet": {"season": s, "weeks": old}, "methods": methods}, default=clean, separators=(",", ":")) + ";")
    print("rankings.js", (WEB / "rankings.js").stat().st_size / 1e6, "MB")


if __name__ == "__main__" and "--rankings" in __import__("sys").argv:
    export_rankings_and_methods()
