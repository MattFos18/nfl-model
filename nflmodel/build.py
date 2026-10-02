"""Build processed tables from raw nflverse data.

Outputs (data/processed/):
  games.parquet      one row per game: teams, scores, closing lines, situational fields
  team_games.parquet one row per team per game: offense/defense stats from play-by-play
  drives.parquet     one row per drive
"""
from __future__ import annotations
import logging
import numpy as np, pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW, OUT = ROOT / "data" / "raw", ROOT / "data" / "processed"
TEAM_FIX = {"OAK": "LV", "SD": "LAC", "STL": "LA"}
WX = ROOT / "data" / "weather"
WIND_GAP = 10.0   # mph: a schedule wind this far from the Open-Meteo archive's kickoff hour is checked against a second source
WIND_MAX = 40.0   # mph: the windiest real kickoff in the data is 35 (2020_08_LV_CLE, forecast 36.8); above this is a typo


def build_games() -> pd.DataFrame:
    from .venues import fix_venues
    g = pd.read_csv(RAW / "schedules" / "games.csv")
    for c in ["home_team", "away_team"]:
        g[c] = g[c].replace(TEAM_FIX)
    g = fix_venues(g)   # 2 Oct 2026: games the schedule lists at the wrong stadium or roof (nflmodel/venues.py)
    g["kickoff_et"] = pd.to_datetime(g.gameday + " " + g.gametime, errors="coerce")
    g["hour_et"] = g.kickoff_et.dt.hour
    g["slot"] = np.select(
        [g.weekday.eq("Thursday"), g.weekday.eq("Monday"), g.weekday.eq("Sunday") & g.hour_et.ge(19),
         g.weekday.eq("Sunday") & g.hour_et.ge(16), g.weekday.eq("Sunday"), g.weekday.eq("Saturday")],
        ["TNF", "MNF", "SNF", "SUN_LATE", "SUN_EARLY", "SAT"], "OTHER")
    g["primetime"] = g.slot.isin(["TNF", "MNF", "SNF"])
    g["dome"] = g.roof.isin(["dome", "closed"])
    g["neutral"] = g.location.eq("Neutral")
    # Vegas implied team totals from closing spread and total
    g["home_implied"] = (g.total_line + g.spread_line) / 2
    g["away_implied"] = (g.total_line - g.spread_line) / 2
    g["home_cover"] = np.sign(g.result - g.spread_line)  # 1 cover, -1 no, 0 push
    g["over"] = np.sign(g.total - g.total_line)
    g["home_win"] = np.sign(g.result)
    keep = ["game_id", "season", "game_type", "week", "gameday", "weekday", "gametime", "kickoff_et", "hour_et",
            "slot", "primetime", "away_team", "home_team", "away_score", "home_score", "result", "total",
            "overtime", "location", "neutral", "roof", "dome", "surface", "temp", "wind", "div_game",
            "away_rest", "home_rest", "away_moneyline", "home_moneyline", "spread_line", "away_spread_odds",
            "home_spread_odds", "total_line", "under_odds", "over_odds", "home_implied", "away_implied",
            "home_cover", "over", "home_win", "away_qb_id", "home_qb_id", "away_qb_name", "home_qb_name",
            "away_coach", "home_coach", "referee", "stadium_id", "stadium"]
    return fix_wind(g[keep])


def fix_wind(g: pd.DataFrame, archive: pd.DataFrame | None = None, forecast: pd.DataFrame | None = None) -> pd.DataFrame:
    """Kickoff wind the schedule got wrong (2 Oct 2026, data audit: 2016_13_NYG_PIT 71 mph against 6.4 measured, 2023_13_SF_PHI
    44 against 4.6 and a 5.0 forecast). A played outdoor game's schedule wind more than WIND_GAP from the Open-Meteo archive's
    kickoff hour (data/weather/archive_kickoff.csv, fetched at the game's real site) is replaced by the archive when no
    pre-game forecast exists (before 2018) or the GFS MOS forecast (forecast_history.csv) sits closer to the archive than to
    the schedule; where the forecast sides with the schedule (Denver's downslope winds the reanalysis smooths over) the
    schedule stands. A reading above WIND_MAX with nothing to replace it is blanked (the model fills the median).
    The schedule's figure is kept as wind_listed."""
    from .venues import sites
    g = g.copy(); g["wind_listed"] = g["wind"]
    if archive is None:
        f = WX / "archive_kickoff.csv"; archive = pd.read_csv(f) if f.exists() else pd.DataFrame(columns=["game_id", "site", "wind"])
        if not f.exists():
            logging.warning("build.fix_wind: %s is missing; the schedule's wind is only checked against WIND_MAX", f)
    if forecast is None:
        f = WX / "forecast_history.csv"; forecast = pd.read_csv(f, usecols=["game_id", "gfs_wind_d0"]) if f.exists() else pd.DataFrame(columns=["game_id", "gfs_wind_d0"])
    st = sites(g)
    a = archive.drop_duplicates("game_id").set_index("game_id")
    arch = pd.Series([a.at[i, "wind"] if i in a.index and a.at[i, "site"] == s_ else np.nan for i, s_ in zip(g.game_id, st.site)], index=g.index, dtype=float)
    fc = g.game_id.map(forecast.drop_duplicates("game_id").set_index("game_id").gfs_wind_d0).astype(float)
    fc[st.abroad.astype(bool).values] = np.nan   # a forecast row for a game abroad was read at a US airport
    outdoor = ~g.roof.isin(["dome", "closed"]) & g.home_score.notna()
    w = g.wind.astype(float)
    off = outdoor & w.notna() & arch.notna() & ((w - arch).abs() > WIND_GAP)
    sides_with_archive = fc.isna() | ((fc - arch).abs() < (fc - w).abs())
    rep = off & sides_with_archive
    g.loc[rep, "wind"] = arch[rep].round(1)
    hi = outdoor & (g.wind.astype(float) > WIND_MAX)
    g.loc[hi, "wind"] = np.nan
    print(f"fix_wind: {int(rep.sum())} schedule winds replaced by the archive, {int(hi.sum())} above {WIND_MAX:g} mph blanked"
          + (f" ({', '.join(g.game_id[hi].head(5))})" if hi.any() else ""), flush=True)
    return g


def observed_starters(p: pd.DataFrame) -> pd.DataFrame:
    """(game_id, team) -> the QB who started, from the play-by-play: the passer (passer_id, which carries scrambles too) on
    the team's first dropback among passers with 3+ dropbacks in the game (so a receiver's or punter's trick throw is not a
    start; with none, the passer with the most dropbacks), his name, and every passer's dropback count."""
    d = p[p.posteam.notna() & (pd.to_numeric(p.qb_dropback, errors="coerce") == 1) & p.passer_id.notna()]
    d = d.assign(order=np.arange(len(d)))
    n = d.groupby(["game_id", "posteam", "passer_id"]).agg(db=("order", "size"), first=("order", "min"),
                                                            name=("passer", "first") if "passer" in d.columns else ("passer_player_name", "first")).reset_index()
    real = n[n.db >= 3].sort_values("first").drop_duplicates(["game_id", "posteam"])
    most = n.sort_values("db", ascending=False).drop_duplicates(["game_id", "posteam"])
    s = pd.concat([real, most[~most.set_index(["game_id", "posteam"]).index.isin(real.set_index(["game_id", "posteam"]).index)]])
    return s.rename(columns={"posteam": "team", "passer_id": "qb_id", "name": "qb_name"})[["game_id", "team", "qb_id", "qb_name"]], \
        n.rename(columns={"posteam": "team", "passer_id": "qb_id"})[["game_id", "team", "qb_id", "db"]]


def fix_starters(g: pd.DataFrame, p: pd.DataFrame) -> pd.DataFrame:
    """Played games whose listed starter took no dropback get the QB who did start (2 Oct 2026, data audit: nflverse's
    schedule carried a projected starter that was never reconciled with who played in 44 team-games 2022-2025, 33 of them
    in 2024: Mariota for Washington in Weeks 9-13, Hurts in 2024_17_DAL_PHI where Pickett started, Dalton for Carolina,
    Flacco for Indianapolis). A listed QB who dropped back at all keeps his game (a starter hurt in the first quarter
    started). Unplayed games keep the announced starter. nflverse's ids are kept as *_qb_id_listed."""
    need = {"passer_id", "qb_dropback", "posteam", "game_id"}
    if not need <= set(p.columns):   # loud (review of #381): without these the listed starters stand unchecked
        logging.warning("build.fix_starters did not run: the play-by-play lacks %s; nflverse's listed starters stand", sorted(need - set(p.columns)))
        return g
    start, n = observed_starters(p)
    st = start.set_index(["game_id", "team"]); db = n.set_index(["game_id", "team", "qb_id"]).db
    teams_db = set(zip(n.game_id, n.team))
    g = g.copy()
    full = {}   # the schedule's own full name for a QB id wherever it lists him (the play-by-play has "K.Pickett")
    for side in ("home", "away"):
        full.update({q: n for q, n in zip(g[f"{side}_qb_id"], g[f"{side}_qb_name"]) if isinstance(q, str) and isinstance(n, str)})
    for side in ("home", "away"):
        g[f"{side}_qb_id_listed"] = g[f"{side}_qb_id"]
        key = list(zip(g.game_id, g[f"{side}_team"]))
        none = [k in teams_db and (not isinstance(q, str) or (k[0], k[1], q) not in db.index) for k, q in zip(key, g[f"{side}_qb_id"])]
        m = pd.Series(none, index=g.index) & g.home_score.notna()
        idx = [k for k, x in zip(key, m) if x]
        g.loc[m, f"{side}_qb_id"] = [st.at[k, "qb_id"] for k in idx]
        g.loc[m, f"{side}_qb_name"] = [full.get(st.at[k, "qb_id"], st.at[k, "qb_name"]) for k in idx]
    return g


PBP_COLS = ["game_id", "season", "week", "season_type", "home_team", "away_team", "posteam", "defteam",
            "play_type", "pass", "rush", "special", "qb_dropback", "qb_kneel", "qb_spike", "qb_scramble",
            "epa", "qb_epa", "success", "wp", "vegas_wp", "down", "ydstogo", "yardline_100", "yards_gained",
            "air_yards", "cpoe", "xpass", "pass_oe", "complete_pass", "incomplete_pass", "sack", "qb_hit",
            "interception", "fumble_lost", "touchdown", "pass_touchdown", "rush_touchdown", "first_down",
            "third_down_converted", "third_down_failed", "fourth_down_converted", "fourth_down_failed",
            "penalty", "penalty_team", "penalty_yards", "field_goal_attempt", "field_goal_result",
            "punt_attempt", "kickoff_attempt", "fixed_drive", "fixed_drive_result", "drive_start_yard_line",
            "drive_play_count", "drive_inside20", "drive_ended_with_score", "game_seconds_remaining",
            "half_seconds_remaining", "score_differential", "passer_player_id", "passer_player_name", "passer_id", "passer",
            "rusher_player_id", "receiver_player_id", "posteam_score", "defteam_score"]


def load_pbp(seasons):
    frames = []
    for s in seasons:
        f = RAW / "pbp" / f"play_by_play_{s}.parquet"
        if not f.exists():
            continue
        cols = [c for c in PBP_COLS if c in pd.read_parquet(f, columns=None).columns[:0].tolist() or True]
        p = pd.read_parquet(f)
        p = p[[c for c in PBP_COLS if c in p.columns]]
        frames.append(p)
    p = pd.concat(frames, ignore_index=True)
    for c in ["posteam", "defteam", "home_team", "away_team"]:
        p[c] = p[c].replace(TEAM_FIX)
    return p


def team_game_stats(p: pd.DataFrame) -> pd.DataFrame:
    """Offense stats per (game, posteam). Defense = same table joined on defteam."""
    d = p[p.posteam.notna() & p.play_type.isin(["pass", "run"]) & p.epa.notna()].copy()
    d["garbage"] = (d.wp < 0.10) | (d.wp > 0.90)
    d["explosive"] = ((d["pass"] == 1) & (d.yards_gained >= 20)) | ((d.rush == 1) & (d.yards_gained >= 12))
    d["early_down"] = d.down.isin([1, 2])
    d["rz"] = d.yardline_100 <= 20
    d["turnover"] = (d.interception == 1) | (d.fumble_lost == 1)
    d["dropback"] = d.qb_dropback == 1
    d["is_pass"] = d["pass"] == 1
    d["is_rush"] = (d.rush == 1) & (d.qb_scramble != 1)

    def agg(x, suffix=""):
        n = len(x)
        ps, rs = x[x.is_pass], x[x.is_rush]
        ed = x[x.early_down]
        out = {
            f"plays{suffix}": n,
            f"epa_play{suffix}": x.epa.mean(),
            f"success{suffix}": x.success.mean(),
            f"pass_epa{suffix}": ps.epa.mean(), f"pass_success{suffix}": ps.success.mean(), f"pass_plays{suffix}": len(ps),
            f"rush_epa{suffix}": rs.epa.mean(), f"rush_success{suffix}": rs.success.mean(), f"rush_plays{suffix}": len(rs),
            f"early_down_epa{suffix}": ed.epa.mean(), f"early_down_success{suffix}": ed.success.mean(),
            f"explosive_rate{suffix}": x.explosive.mean(),
            f"pass_rate{suffix}": x.is_pass.mean(), f"pass_oe{suffix}": x.pass_oe.mean(),
            f"cpoe{suffix}": ps.cpoe.mean(), f"air_yards_att{suffix}": ps.air_yards.mean(),
            f"sack_rate{suffix}": (ps.sack.sum() / max(x.dropback.sum(), 1)),
            f"int_rate{suffix}": ps.interception.sum() / max(len(ps), 1),
            f"turnovers{suffix}": x.turnover.sum(), f"turnover_rate{suffix}": x.turnover.mean(),
            f"yards_play{suffix}": x.yards_gained.mean(),
            f"third_conv{suffix}": x.third_down_converted.sum() / max(x.third_down_converted.sum() + x.third_down_failed.sum(), 1),
            f"rz_plays{suffix}": x.rz.sum(), f"rz_epa{suffix}": x[x.rz].epa.mean() if x.rz.any() else np.nan,
        }
        return pd.Series(out)

    full = d.groupby(["game_id", "posteam"]).apply(agg, include_groups=False)
    ng = d[~d.garbage].groupby(["game_id", "posteam"]).apply(agg, "_ng", include_groups=False)
    stats = full.join(ng)

    # drives and points per drive from play-level drive fields
    dr = p[p.posteam.notna() & p.fixed_drive.notna()].drop_duplicates(["game_id", "posteam", "fixed_drive"])
    dr = dr.assign(score=dr.fixed_drive_result.isin(["Touchdown", "Field goal"]),
                   td=dr.fixed_drive_result.eq("Touchdown"), to=dr.fixed_drive_result.isin(["Turnover", "Interception", "Fumble"]),
                   rz=dr.drive_inside20.eq(1))
    dd = dr.groupby(["game_id", "posteam"]).agg(drives=("fixed_drive", "size"), score_rate=("score", "mean"),
                                                 td_rate=("td", "mean"), drive_to_rate=("to", "mean"),
                                                 rz_drive_rate=("rz", "mean"), rz_td_rate=("td", lambda s: np.nan))
    rz = dr[dr.rz].groupby(["game_id", "posteam"]).td.mean().rename("rz_td_rate")
    dd = dd.drop(columns="rz_td_rate").join(rz)
    stats = stats.join(dd)

    # pace: seconds per play on offense, from non-special plays
    sp = p[p.posteam.notna() & p.play_type.isin(["pass", "run"])].sort_values(["game_id", "posteam", "game_seconds_remaining"], ascending=[True, True, False])
    sp["gap"] = -sp.groupby(["game_id", "posteam"]).game_seconds_remaining.diff()
    pace = sp[(sp.gap > 0) & (sp.gap < 60)].groupby(["game_id", "posteam"]).gap.mean().rename("sec_per_play")
    stats = stats.join(pace)

    # special teams: field goals and average start position
    fg = p[p.field_goal_attempt == 1].groupby(["game_id", "posteam"]).field_goal_result.agg(
        fg_att="size", fg_made=lambda s: (s == "made").sum())
    stats = stats.join(fg)
    start = dr.copy()
    start["start_yd"] = pd.to_numeric(start.drive_start_yard_line.str.extract(r"(\d+)")[0], errors="coerce")
    # drive_start_yard_line like 'KC 25' = own 25 -> 75 from goal; opponent side = yards to goal
    own = start.drive_start_yard_line.str[:3].str.strip() == start.posteam
    start["start_ytg"] = np.where(own, 100 - start.start_yd, start.start_yd)
    stats = stats.join(start.groupby(["game_id", "posteam"]).start_ytg.mean().rename("avg_start_ytg"))

    # points scored, from schedule fields on the plays
    pts = p.drop_duplicates("game_id").set_index("game_id")[["home_team", "away_team", "posteam"]]
    stats = stats.reset_index().rename(columns={"posteam": "team"})
    return stats


def build_team_games(games: pd.DataFrame, seasons, p: pd.DataFrame | None = None) -> pd.DataFrame:
    p = load_pbp(seasons) if p is None else p
    off = team_game_stats(p)
    # defense view: what the opponent's offense did against this team
    de = off.copy()
    de.columns = ["game_id", "team"] + ["def_" + c for c in off.columns[2:]]
    gi = games.set_index("game_id")
    de["team"] = [gi.loc[g, "away_team"] if t == gi.loc[g, "home_team"] else gi.loc[g, "home_team"]
                  for g, t in zip(de.game_id, de.team)]
    tg = off.merge(de, on=["game_id", "team"], how="outer")
    meta = []
    for side, opp in [("home", "away"), ("away", "home")]:
        m = games[["game_id", "season", "week", "game_type", f"{side}_team", f"{opp}_team", f"{side}_score", f"{opp}_score",
                   "spread_line", "total_line", f"{side}_implied", f"{opp}_implied", f"{side}_rest", f"{side}_qb_id", f"{side}_qb_name",
                   f"{side}_coach", "dome", "temp", "wind", "div_game", "slot", "primetime", "referee"]].copy()
        m.columns = ["game_id", "season", "week", "game_type", "team", "opp", "pf", "pa", "spread_line", "total_line",
                     "implied_pf", "implied_pa", "rest", "qb_id", "qb_name", "coach", "dome", "temp", "wind", "div_game",
                     "slot", "primetime", "referee"]
        m["home"] = side == "home"
        m["margin"] = m.pf - m.pa
        # spread from this team's view: positive = this team favored by that much
        m["team_spread"] = np.where(m.home, m.spread_line, -m.spread_line)
        meta.append(m)
    meta = pd.concat(meta)
    tg = meta.merge(tg, on=["game_id", "team"], how="left")
    return tg.sort_values(["season", "week", "game_id", "home"]).reset_index(drop=True)


if __name__ == "__main__":
    import sys
    seasons = range(2012, 2027)
    OUT.mkdir(parents=True, exist_ok=True)
    games = build_games()
    p = load_pbp(seasons)
    games = fix_starters(games, p)
    games.to_parquet(OUT / "games.parquet", index=False)
    print("games", games.shape, games.season.min(), games.season.max())
    tg = build_team_games(games[games.season.isin(seasons)], seasons, p)
    tg.to_parquet(OUT / "team_games.parquet", index=False)
    print("team_games", tg.shape)
