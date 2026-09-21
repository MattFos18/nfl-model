"""Counting stats per team per game, from play-by-play.

These are the box-score style inputs the spreadsheet model (2.0) used: points, drives,
scoring %, red zone trips and TDs, completions, attempts, yards, TDs, INTs, sacks, first
downs, third and fourth downs, penalties, rush attempts, kickoff yards, average drive start.
Every stat is kept as a raw count so it can be summed over any window (season to date, last 3,
home only, last season) and turned into a rate afterwards, exactly as the sheet's tables did.

Output: data/processed/team_box.parquet, one row per (game_id, team), with `off_*` = what the
team's offense did and `def_*` = what the team's defense allowed (the opponent's offense).
"""
from __future__ import annotations
import numpy as np, pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW, OUT = ROOT / "data" / "raw", ROOT / "data" / "processed"
TEAM_FIX = {"OAK": "LV", "SD": "LAC", "STL": "LA"}

COLS = ["game_id", "season", "week", "season_type", "home_team", "away_team", "posteam", "defteam",
        "play_type", "pass", "rush", "qb_dropback", "qb_kneel", "qb_spike", "qb_scramble", "sack",
        "complete_pass", "incomplete_pass", "passing_yards", "rushing_yards", "pass_attempt", "rush_attempt",
        "interception", "fumble_lost", "pass_touchdown", "rush_touchdown", "touchdown", "td_team",
        "first_down", "third_down_converted", "third_down_failed", "fourth_down_converted", "fourth_down_failed",
        "penalty", "penalty_team", "penalty_yards", "yards_gained", "fixed_drive", "fixed_drive_result",
        "drive_inside20", "drive_start_yard_line", "kickoff_attempt", "kick_distance", "punt_attempt",
        "field_goal_attempt", "field_goal_result", "extra_point_result", "two_point_conv_result", "safety",
        "epa", "success", "wp", "qb_epa", "passer_player_id", "down", "yardline_100", "game_seconds_remaining", "return_team", "return_yards"]


def load_pbp(seasons) -> pd.DataFrame:
    frames = []
    for s in seasons:
        f = RAW / "pbp" / f"play_by_play_{s}.parquet"
        if not f.exists():
            continue
        p = pd.read_parquet(f)
        p = p[[c for c in COLS if c in p.columns]]
        frames.append(p)
    p = pd.concat(frames, ignore_index=True)
    for c in ["posteam", "defteam", "home_team", "away_team", "penalty_team", "td_team", "return_team"]:
        if c in p.columns:
            p[c] = p[c].replace(TEAM_FIX)
    return p


def _num(s):
    return pd.to_numeric(s, errors="coerce").fillna(0)


def offense_box(p: pd.DataFrame) -> pd.DataFrame:
    """One row per (game_id, posteam): raw counts for that team's offense."""
    d = p[p.posteam.notna()].copy()
    for c in ["pass", "rush", "qb_dropback", "sack", "complete_pass", "pass_attempt", "rush_attempt", "interception",
              "fumble_lost", "pass_touchdown", "rush_touchdown", "first_down", "third_down_converted",
              "third_down_failed", "fourth_down_converted", "fourth_down_failed", "penalty", "passing_yards",
              "rushing_yards", "yards_gained", "kickoff_attempt", "kick_distance", "qb_scramble", "qb_kneel", "qb_spike"]:
        d[c] = _num(d[c])
    scrim = d.play_type.isin(["pass", "run"])
    d["scrim_play"] = scrim.astype(int)
    d["scrim_yards"] = np.where(scrim, d.yards_gained, 0)
    d["sack_yards"] = np.where(d.sack == 1, -d.yards_gained, 0)
    d["ko_yards"] = np.where(d.kickoff_attempt == 1, d.kick_distance, 0)
    d["rush_td"] = d.rush_touchdown
    d["pass_td"] = d.pass_touchdown
    d["fg_made"] = (d.field_goal_result == "made").astype(int)
    d["fg_att"] = _num(d.field_goal_attempt)
    d["xp_made"] = (d.extra_point_result == "good").astype(int)
    g = d.groupby(["game_id", "posteam"])
    box = g.agg(plays=("scrim_play", "sum"), yards=("scrim_yards", "sum"),
                pass_att=("pass_attempt", "sum"), completions=("complete_pass", "sum"), pass_yards=("passing_yards", "sum"),
                pass_td=("pass_td", "sum"), interceptions=("interception", "sum"), sacks=("sack", "sum"),
                sack_yards=("sack_yards", "sum"), rush_att=("rush_attempt", "sum"), rush_yards=("rushing_yards", "sum"),
                rush_td=("rush_td", "sum"), fumbles_lost=("fumble_lost", "sum"), first_downs=("first_down", "sum"),
                third_conv=("third_down_converted", "sum"), third_fail=("third_down_failed", "sum"),
                fourth_conv=("fourth_down_converted", "sum"), fourth_fail=("fourth_down_failed", "sum"),
                kickoffs=("kickoff_attempt", "sum"), ko_yards=("ko_yards", "sum"),
                fg_att=("fg_att", "sum"), fg_made=("fg_made", "sum"), xp_made=("xp_made", "sum"))
    # penalties by the team that committed them, on offense or defense
    pen = p[(_num(p.penalty) == 1) & p.penalty_team.notna()].copy()
    pen["penalty_yards"] = _num(pen.penalty_yards)
    pen = pen.groupby(["game_id", "penalty_team"]).agg(penalties=("penalty", "size"), penalty_yards=("penalty_yards", "sum"))
    pen.index.names = ["game_id", "posteam"]
    box = box.join(pen).fillna({"penalties": 0, "penalty_yards": 0})
    # drives: one row per (game, team, fixed_drive)
    dr = d[d.fixed_drive.notna()].drop_duplicates(["game_id", "posteam", "fixed_drive"]).copy()
    dr["score"] = dr.fixed_drive_result.isin(["Touchdown", "Field goal"]).astype(int)
    dr["td"] = dr.fixed_drive_result.eq("Touchdown").astype(int)
    dr["rz"] = _num(dr.drive_inside20).astype(int)
    dr["rz_td"] = ((dr.rz == 1) & (dr.td == 1)).astype(int)
    dr["turnover"] = dr.fixed_drive_result.isin(["Turnover", "Interception", "Fumble", "Turnover on downs", "Opp touchdown"]).astype(int)
    yd = pd.to_numeric(dr.drive_start_yard_line.str.extract(r"(\d+)")[0], errors="coerce")
    own = dr.drive_start_yard_line.str[:3].str.strip() == dr.posteam
    # start measured from own goal line (PFR 'Start' = Own 30.1)
    dr["start_own"] = np.where(own, yd, 100 - yd)
    dd = dr.groupby(["game_id", "posteam"]).agg(drives=("fixed_drive", "size"), scoring_drives=("score", "sum"),
                                                 td_drives=("td", "sum"), rz_trips=("rz", "sum"), rz_tds=("rz_td", "sum"),
                                                 to_drives=("turnover", "sum"), start_own_sum=("start_own", "sum"),
                                                 start_n=("start_own", "count"))
    box = box.join(dd)
    box = box.reset_index().rename(columns={"posteam": "team"})
    return box


def qb_box(p: pd.DataFrame) -> pd.DataFrame:
    """One row per (game_id, team, passer): dropbacks and total qb_epa, for the QB rating."""
    d = p[p.posteam.notna() & (_num(p.qb_dropback) == 1) & p.passer_player_id.notna()].copy()
    d["qb_epa"] = _num(d.qb_epa)
    q = d.groupby(["game_id", "season", "week", "posteam", "passer_player_id"]).agg(dropbacks=("qb_epa", "size"), qb_epa=("qb_epa", "sum")).reset_index()
    return q.rename(columns={"posteam": "team", "passer_player_id": "qb_id"})


def build(seasons, games: pd.DataFrame) -> pd.DataFrame:
    p = load_pbp(seasons)
    qb_box(p).to_parquet(OUT / "qb_games.parquet", index=False)
    off = offense_box(p)
    stat_cols = [c for c in off.columns if c not in ("game_id", "team")]
    gi = games.set_index("game_id")
    de = off.copy()
    de["team"] = [gi.loc[g, "away_team"] if t == gi.loc[g, "home_team"] else gi.loc[g, "home_team"]
                  for g, t in zip(de.game_id, de.team)]
    off = off.rename(columns={c: "off_" + c for c in stat_cols})
    de = de.rename(columns={c: "def_" + c for c in stat_cols})
    box = off.merge(de, on=["game_id", "team"], how="outer")
    meta = []
    for side, opp in [("home", "away"), ("away", "home")]:
        m = games[["game_id", "season", "week", "game_type", "gameday", f"{side}_team", f"{opp}_team",
                   f"{side}_score", f"{opp}_score"]].copy()
        m.columns = ["game_id", "season", "week", "game_type", "gameday", "team", "opp", "pf", "pa"]
        m["home"] = side == "home"
        meta.append(m)
    meta = pd.concat(meta)
    box = meta.merge(box, on=["game_id", "team"], how="inner")
    return box.sort_values(["season", "week", "game_id", "home"]).reset_index(drop=True)


if __name__ == "__main__":
    seasons = range(2012, 2027)
    games = pd.read_parquet(OUT / "games.parquet")
    games = games[games.season.isin(seasons) & games.home_score.notna()]
    box = build(seasons, games)
    box.to_parquet(OUT / "team_box.parquet", index=False)
    print("team_box", box.shape, box.season.min(), box.season.max())
    print(box[box.season == 2024].describe().T.head(40))
