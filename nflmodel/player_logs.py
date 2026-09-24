"""Player game logs for the Players tab (24 Sep 2026): every stat the model's data holds for every player and game,
2016 on, one file per season (web/data/plogs/<season>.js, loaded when a season is opened) and a small career file
(web/data/player_careers.js, each player's season totals, loaded with the tab).

Sources, joined per player and game:
  play-by-play (nflverse)    targets, catches, yards, touchdowns, longest, air yards, yards after catch, first
                             downs, red-zone touches (inside the 20), fumbles lost, EPA; carries; dropbacks,
                             attempts, completions, interceptions, sacks
  charted plays              the looks: against man and zone coverage, under pressure (nflverse participation,
                             2016 to the last published season); runs into light and heavy boxes (FTN, 2022 on)
  snap counts (nflverse)     offensive and defensive snaps and share
  Pro Football Reference     receivers: drops, broken tackles, passer rating when targeted; rushers: yards before
                             and after contact, broken tackles; passers: bad throws, pressured, blitzed, hit,
                             receivers' drops; defenders: targets, completions and yards allowed, passer rating
                             allowed, pressures, sacks, missed tackles (2018 on)
  defender and kicker games  tackles, solo tackles, sacks, interceptions, passes defended, plays faced; field goals
                             and extra points made and tried, kicking points
EPA is nflverse's: the expected points before a play (from down, distance, field position, time and score) against
the expected points after it; a player's EPA is the sum over the plays that are his (targets, carries, dropbacks).
"""
from __future__ import annotations
import json
import numpy as np, pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW, OUT, WEB = ROOT / "data" / "raw", ROOT / "data" / "processed", ROOT / "web" / "data"

COLS = {
    "rec": ["week", "game_id", "team", "opp", "snaps", "snap_pct", "targets", "catches", "yards", "td", "longest", "air_yds", "yac", "first_downs", "rz_targets", "fumbles_lost", "epa",
            "drops", "broken_tackles", "rating_when_targeted", "man_n", "man_yds", "zone_n", "zone_yds", "press_n", "press_yds"],
    "rush": ["week", "game_id", "team", "opp", "snaps", "snap_pct", "carries", "yards", "td", "longest", "first_downs", "rz_carries", "fumbles_lost", "epa",
             "yds_before_contact", "yds_after_contact", "broken_tackles", "light_n", "light_yds", "heavy_n", "heavy_yds"],
    "pass": ["week", "game_id", "team", "opp", "snaps", "snap_pct", "dropbacks", "attempts", "completions", "yards", "td", "int", "sacks", "longest", "air_yds", "first_downs", "epa",
             "bad_throws", "pressured", "blitzed", "hit", "drops_by_receivers", "man_n", "man_yds", "zone_n", "zone_yds", "press_n", "press_yds"],
    "def": ["week", "game_id", "team", "opp", "snaps", "snap_pct", "tackles", "solo", "sacks", "ints", "passes_defended", "plays_faced",
            "targets_allowed", "completions_allowed", "yards_allowed", "td_allowed", "rating_allowed", "pressures", "missed_tackles"],
    "kick": ["week", "game_id", "team", "opp", "fgm", "fga", "xpm", "xpa", "points"],
}


# the full box score's columns: the official stat line (nflverse player_stats) less what the tables above carry, the
# PFR advanced columns they do not show, special-teams snaps
_IN_TABLES = {"completions", "attempts", "passing_yards", "passing_tds", "passing_interceptions", "sacks_suffered", "passing_air_yards", "passing_first_downs", "passing_epa",
              "carries", "rushing_yards", "rushing_tds", "rushing_first_downs", "rushing_epa", "receptions", "targets", "receiving_yards", "receiving_tds", "receiving_air_yards",
              "receiving_yards_after_catch", "receiving_first_downs", "receiving_epa", "def_tackles_solo", "def_sacks", "def_interceptions", "def_pass_defended", "fg_made", "fg_att", "pat_made", "pat_att"}
BOX_OFFICIAL = [c for c in [
    "sack_yards_lost", "sack_fumbles", "sack_fumbles_lost", "passing_yards_after_catch", "passing_cpoe", "passing_2pt_conversions", "pacr", "passing_10", "passing_16", "passing_20", "passing_40",
    "rushing_fumbles", "rushing_fumbles_lost", "rushing_2pt_conversions", "rushing_10", "rushing_12", "rushing_20", "rushing_40",
    "receiving_fumbles", "receiving_fumbles_lost", "receiving_2pt_conversions", "receiving_10", "receiving_16", "receiving_20", "receiving_40", "racr", "target_share", "air_yards_share", "wopr",
    "special_teams_tds", "def_tackles_with_assist", "def_tackle_assists", "def_tackles_for_loss", "def_tackles_for_loss_yards", "def_fumbles_forced", "def_sack_yards", "def_qb_hits",
    "def_interception_yards", "def_tds", "def_fumbles", "def_safeties", "def_punt_blocks", "def_pat_blocks", "def_fg_blocks", "def_2pt_atts", "def_2pt_made", "misc_yards",
    "fumble_recovery_own", "fumble_recovery_yards_own", "fumble_recovery_opp", "fumble_recovery_yards_opp", "fumble_recovery_tds", "penalties", "penalty_yards",
    "fumbles_forced_by_opp", "fumbles_not_forced", "fumbles_out_of_bounds", "fumbles_total", "fumbles_lost_total", "punt_returns", "punt_return_yards", "kickoff_returns", "kickoff_return_yards",
    "fg_missed", "fg_blocked", "fg_long", "fg_pct", "fg_made_0_19", "fg_made_20_29", "fg_made_30_39", "fg_made_40_49", "fg_made_50_59", "fg_made_60_",
    "fg_missed_0_19", "fg_missed_20_29", "fg_missed_30_39", "fg_missed_40_49", "fg_missed_50_59", "fg_missed_60_", "pat_missed", "pat_blocked", "pat_pct",
    "gwfg_made", "gwfg_att", "gwfg_missed", "gwfg_blocked", "pt_att", "pt_blocked", "pt_long", "pt_yards", "pt_inside_20", "pt_out_of_bounds", "pt_downed", "pt_touchback",
    "pt_fair_caught", "pt_returned", "pt_return_yards", "pt_return_tds", "pt_net_yards", "fantasy_points", "fantasy_points_ppr"] if c not in _IN_TABLES]
BOX_PFR = {"def": ["def_adot", "def_air_yards_completed", "def_yards_after_catch", "def_times_blitzed", "def_times_hurried", "def_times_hitqb", "def_completion_pct", "def_yards_allowed_per_tgt", "def_missed_tackle_pct"],
           "rec": ["receiving_int", "receiving_drop_pct"], "rush": ["rushing_yards_before_contact_avg", "rushing_yards_after_contact_avg"],
           "pass": ["passing_drop_pct", "passing_bad_throw_pct", "times_hurried", "times_pressured_pct", "times_sacked"]}
BOX_COLS = BOX_OFFICIAL + [f"pfr_{c}" for v in BOX_PFR.values() for c in v] + ["st_snaps"]


def _pbp(season: int) -> pd.DataFrame:
    f = RAW / "pbp" / f"play_by_play_{season}.parquet"
    cols = ["game_id", "play_id", "season", "week", "season_type", "posteam", "defteam", "play_type", "pass_attempt", "qb_dropback", "sack", "complete_pass", "interception",
            "receiver_player_id", "rusher_player_id", "passer_player_id", "yards_gained", "air_yards", "yards_after_catch", "first_down_pass", "first_down_rush", "yardline_100",
            "pass_touchdown", "rush_touchdown", "fumble_lost", "fumbled_1_player_id", "epa", "qb_epa", "two_point_attempt"]
    import pyarrow.parquet as pq
    have = set(pq.ParquetFile(f).schema.names)
    p = pd.read_parquet(f, columns=[c for c in cols if c in have])
    from .features import TEAM_FIX
    p["posteam"] = p.posteam.replace(TEAM_FIX); p["defteam"] = p.defteam.replace(TEAM_FIX)
    p = p[p.season_type.eq("REG") | p.season_type.eq("POST")] if "season_type" in p.columns else p
    # passes, runs, kneel-downs (a carry in the official box score) and spikes (a pass attempt); two-point tries are not plays
    return p[p.play_type.isin(["pass", "run", "qb_kneel", "qb_spike"]) & (p.two_point_attempt.fillna(0) == 0)].copy()


def _looks(season: int) -> pd.DataFrame:
    s = pd.read_parquet(OUT / "scheme_plays.parquet", columns=["game_id", "play_id", "season", "man", "zone", "pressure", "box"])
    s = s[s.season == season].drop(columns="season")
    s["man_f"] = s.man.fillna(False).astype(float); s["zone_f"] = s.zone.fillna(False).astype(float); s["press_f"] = (s.pressure == 1).astype(float)
    s["light_f"] = (s.box <= 6).astype(float); s["heavy_f"] = (s.box >= 8).astype(float)
    return s[["game_id", "play_id", "man_f", "zone_f", "press_f", "light_f", "heavy_f"]]


def _pfr_map(seasons) -> dict:
    from .ids import pfr_ids
    return pfr_ids()


def _pfr(kind: str, season: int, pmap: dict) -> pd.DataFrame:
    f = RAW / f"pfr_{kind}" / f"advstats_week_{kind}_{season}.parquet"
    if kind == "def":
        f = RAW / "pfr_advstats" / f"advstats_week_def_{season}.parquet"
    if not f.exists():
        return pd.DataFrame(columns=["game_id", "player_id"])
    from .ids import map_pfr
    d = pd.read_parquet(f); d["player_id"] = map_pfr(d, name="pfr_player_name")
    return d[d.player_id.notna()]


def _snaps(season: int, pmap: dict) -> pd.DataFrame:
    f = RAW / "snap_counts" / f"snap_counts_{season}.parquet"
    if not f.exists():
        return pd.DataFrame(columns=["game_id", "player_id", "off_snaps", "off_pct", "def_snaps", "def_pct", "st_snaps"])
    from .ids import map_pfr
    d = pd.read_parquet(f, columns=["game_id", "season", "team", "player", "pfr_player_id", "offense_snaps", "offense_pct", "defense_snaps", "defense_pct", "st_snaps"])
    d["player_id"] = map_pfr(d)
    return d[d.player_id.notna()].rename(columns={"offense_snaps": "off_snaps", "offense_pct": "off_pct", "defense_snaps": "def_snaps", "defense_pct": "def_pct"}).drop(columns=["pfr_player_id", "season", "team", "player"]).drop_duplicates(["game_id", "player_id"])


def season_logs(season: int, pmap: dict) -> dict:
    """{player_id: {kind: [[row], ...]}} for one season."""
    p = _pbp(season); lk = _looks(season)
    p = p.merge(lk, on=["game_id", "play_id"], how="left")
    for c in ["man_f", "zone_f", "press_f", "light_f", "heavy_f", "complete_pass", "interception", "sack", "pass_touchdown", "rush_touchdown", "first_down_pass", "first_down_rush", "fumble_lost"]:
        p[c] = p[c].fillna(0).astype(float)
    p["yards_gained"] = p.yards_gained.fillna(0.0); p["rz"] = (p.yardline_100 <= 20).astype(float)
    p["epa"] = p.epa.fillna(0.0)
    sn = _snaps(season, pmap)
    out: dict = {}

    def put(pid, kind, row):
        out.setdefault(pid, {}).setdefault(kind, []).append(row)

    snapd = {(r.player_id, r.game_id): r for r in sn.itertuples()}
    rnd = lambda v, d=1: None if v is None or (isinstance(v, float) and np.isnan(v)) else round(float(v), d)

    # receiving: targets are pass attempts with a receiver
    t = p[(p.pass_attempt == 1) & p.receiver_player_id.notna() & (p.sack == 0)].copy()
    t["lg"] = np.where(t.complete_pass == 1, t.yards_gained, 0.0); t["yac"] = t.yards_after_catch.fillna(0.0) * t.complete_pass
    t["fl_mine"] = ((t.fumble_lost == 1) & (t.fumbled_1_player_id == t.receiver_player_id)).astype(float)
    for c, f in (("man", "man_f"), ("zone", "zone_f"), ("press", "press_f")):
        t[f"{c}_n"] = t[f]; t[f"{c}_yds"] = t.yards_gained * t[f]
    g = t.groupby(["receiver_player_id", "week", "game_id", "posteam", "defteam"]).agg(targets=("play_id", "size"), catches=("complete_pass", "sum"), yards=("yards_gained", "sum"), td=("pass_touchdown", "sum"),
        longest=("lg", "max"), air_yds=("air_yards", "sum"), yac=("yac", "sum"), first_downs=("first_down_pass", "sum"), rz_targets=("rz", "sum"), fumbles_lost=("fl_mine", "sum"), epa=("epa", "sum"),
        man_n=("man_n", "sum"), man_yds=("man_yds", "sum"), zone_n=("zone_n", "sum"), zone_yds=("zone_yds", "sum"), press_n=("press_n", "sum"), press_yds=("press_yds", "sum")).reset_index()
    pr = _pfr("rec", season, pmap).set_index(["game_id", "player_id"])
    for r in g.itertuples():
        s_ = snapd.get((r.receiver_player_id, r.game_id)); x = pr.loc[(r.game_id, r.receiver_player_id)] if (r.game_id, r.receiver_player_id) in pr.index else None
        if x is not None and isinstance(x, pd.DataFrame): x = x.iloc[0]
        put(r.receiver_player_id, "rec", [int(r.week), r.game_id, r.posteam, r.defteam, (int(s_.off_snaps) if s_ is not None and pd.notna(s_.off_snaps) else None), (rnd(s_.off_pct, 2) if s_ is not None else None),
            int(r.targets), int(r.catches), int(r.yards), int(r.td), int(r.longest), int(r.air_yds) if pd.notna(r.air_yds) else None, int(r.yac), int(r.first_downs), int(r.rz_targets), int(r.fumbles_lost), rnd(r.epa, 2),
            (int(x.receiving_drop) if x is not None and pd.notna(x.receiving_drop) else None), (int(x.receiving_broken_tackles) if x is not None and pd.notna(x.receiving_broken_tackles) else None), (rnd(x.receiving_rat, 1) if x is not None and pd.notna(x.receiving_rat) else None),
            int(r.man_n), int(r.man_yds), int(r.zone_n), int(r.zone_yds), int(r.press_n), int(r.press_yds)])
    # rushing
    u = p[p.play_type.isin(["run", "qb_kneel"]) & p.rusher_player_id.notna()].copy()
    u["fl_mine"] = ((u.fumble_lost == 1) & (u.fumbled_1_player_id == u.rusher_player_id)).astype(float)
    for c, f in (("light", "light_f"), ("heavy", "heavy_f")):
        u[f"{c}_n"] = u[f]; u[f"{c}_yds"] = u.yards_gained * u[f]
    g = u.groupby(["rusher_player_id", "week", "game_id", "posteam", "defteam"]).agg(carries=("play_id", "size"), yards=("yards_gained", "sum"), td=("rush_touchdown", "sum"), longest=("yards_gained", "max"),
        first_downs=("first_down_rush", "sum"), rz_carries=("rz", "sum"), fumbles_lost=("fl_mine", "sum"), epa=("epa", "sum"), light_n=("light_n", "sum"), light_yds=("light_yds", "sum"), heavy_n=("heavy_n", "sum"), heavy_yds=("heavy_yds", "sum")).reset_index()
    pr = _pfr("rush", season, pmap).set_index(["game_id", "player_id"])
    for r in g.itertuples():
        s_ = snapd.get((r.rusher_player_id, r.game_id)); x = pr.loc[(r.game_id, r.rusher_player_id)] if (r.game_id, r.rusher_player_id) in pr.index else None
        if x is not None and isinstance(x, pd.DataFrame): x = x.iloc[0]
        put(r.rusher_player_id, "rush", [int(r.week), r.game_id, r.posteam, r.defteam, (int(s_.off_snaps) if s_ is not None and pd.notna(s_.off_snaps) else None), (rnd(s_.off_pct, 2) if s_ is not None else None),
            int(r.carries), int(r.yards), int(r.td), int(r.longest), int(r.first_downs), int(r.rz_carries), int(r.fumbles_lost), rnd(r.epa, 2),
            (int(x.rushing_yards_before_contact) if x is not None and pd.notna(x.rushing_yards_before_contact) else None), (int(x.rushing_yards_after_contact) if x is not None and pd.notna(x.rushing_yards_after_contact) else None), (int(x.rushing_broken_tackles) if x is not None and pd.notna(x.rushing_broken_tackles) else None),
            int(r.light_n), int(r.light_yds), int(r.heavy_n), int(r.heavy_yds)])
    # passing: every dropback is the passer's (sacks included)
    # passing yards are the yards on completions (a sack's yards are not passing yards); passing EPA is nflverse's qb_epa,
    # as its official passing_epa is (24 Sep 2026: held to nflverse's player stats by the tie check)
    q = p[((p.qb_dropback == 1) | (p.play_type == "qb_spike")) & p.passer_player_id.notna()].copy()
    q["att"] = ((q.pass_attempt == 1) & (q.sack == 0)).astype(float); q["lg"] = np.where(q.complete_pass == 1, q.yards_gained, 0.0); q["ay"] = q.air_yards.fillna(0.0) * q.att
    q["pyds"] = np.where((q.complete_pass == 1) & (q.sack == 0), q.yards_gained, 0.0); q["qepa"] = q.qb_epa.fillna(0.0); q["db1"] = (q.qb_dropback == 1).astype(float)
    for c, f in (("man", "man_f"), ("zone", "zone_f"), ("press", "press_f")):
        q[f"{c}_n"] = q[f]; q[f"{c}_yds"] = q.yards_gained * q[f]
    g = q.groupby(["passer_player_id", "week", "game_id", "posteam", "defteam"]).agg(dropbacks=("db1", "sum"), attempts=("att", "sum"), completions=("complete_pass", "sum"),
        yards=("pyds", "sum"), td=("pass_touchdown", "sum"), int_=("interception", "sum"), sacks=("sack", "sum"), longest=("lg", "max"), air_yds=("ay", "sum"), first_downs=("first_down_pass", "sum"), epa=("qepa", "sum"),
        man_n=("man_n", "sum"), man_yds=("man_yds", "sum"), zone_n=("zone_n", "sum"), zone_yds=("zone_yds", "sum"), press_n=("press_n", "sum"), press_yds=("press_yds", "sum")).reset_index()
    pr = _pfr("pass", season, pmap).set_index(["game_id", "player_id"])
    for r in g.itertuples():
        s_ = snapd.get((r.passer_player_id, r.game_id)); x = pr.loc[(r.game_id, r.passer_player_id)] if (r.game_id, r.passer_player_id) in pr.index else None
        if x is not None and isinstance(x, pd.DataFrame): x = x.iloc[0]
        gv = lambda col: (int(x[col]) if x is not None and col in x and pd.notna(x[col]) else None)
        put(r.passer_player_id, "pass", [int(r.week), r.game_id, r.posteam, r.defteam, (int(s_.off_snaps) if s_ is not None and pd.notna(s_.off_snaps) else None), (rnd(s_.off_pct, 2) if s_ is not None else None),
            int(r.dropbacks), int(r.attempts), int(r.completions), int(r.yards), int(r.td), int(r.int_), int(r.sacks), int(r.longest), int(r.air_yds), int(r.first_downs), rnd(r.epa, 2),
            gv("passing_bad_throws"), gv("times_pressured"), gv("times_blitzed"), gv("times_hit"), gv("passing_drops"),
            int(r.man_n), int(r.man_yds), int(r.zone_n), int(r.zone_yds), int(r.press_n), int(r.press_yds)])
    # defenders
    dg = pd.read_parquet(OUT / "def_games.parquet"); dg = dg[dg.season == season]
    opp = pd.concat([p[["game_id", "posteam", "defteam"]].drop_duplicates().rename(columns={"defteam": "t", "posteam": "o"})])
    om = {(a, b): c for a, b, c in zip(opp.game_id, opp.t, opp.o)}
    pr = _pfr("def", season, pmap).set_index(["game_id", "player_id"])
    # tackles, solo tackles, sacks, interceptions and passes defended as the official box score has them (nflverse's
    # player stats: special-teams tackles included, as ESPN and the league show them). The props' tackle projections
    # count defensive plays only; that is labelled where they are shown.
    off = {}
    sf = RAW / "player_stats" / f"stats_player_week_{season}.parquet"
    if sf.exists():
        st = pd.read_parquet(sf, columns=["player_id", "game_id", "week", "team", "opponent_team", "position_group", "def_tackles_solo", "def_tackle_assists", "def_tackles_with_assist", "def_sacks", "def_interceptions", "def_pass_defended"])
        st = st.fillna({c: 0 for c in ["def_tackles_solo", "def_tackle_assists", "def_tackles_with_assist", "def_sacks", "def_interceptions", "def_pass_defended"]})
        off = {(r.player_id, r.game_id): r for r in st.itertuples()}
        have = set(zip(dg.pid, dg.game_id))
        # defenders whose only tackles in a game came on special teams: a row with no defensive plays faced
        extra = st[st.position_group.isin(["DL", "LB", "DB"]) & ((st.def_tackles_solo + st.def_tackle_assists + st.def_tackles_with_assist) > 0)]
        extra = extra[[(a_, b_) not in have for a_, b_ in zip(extra.player_id, extra.game_id)]]
        if len(extra):
            dg = pd.concat([dg, pd.DataFrame({"pid": extra.player_id.values, "game_id": extra.game_id.values, "week": extra.week.values, "defteam": extra.team.values,
                                               "tackles": 0.0, "solo": 0, "sacks": 0.0, "ints": 0, "pd": 0, "plays_faced": 0})], ignore_index=True)
    for r in dg.itertuples():
        o = off.get((r.pid, r.game_id))
        if o is not None:
            r = r._replace(tackles=float(o.def_tackles_solo + o.def_tackle_assists + o.def_tackles_with_assist), solo=int(o.def_tackles_solo), sacks=float(o.def_sacks), ints=int(o.def_interceptions), pd=int(o.def_pass_defended))
        s_ = snapd.get((r.pid, r.game_id)); x = pr.loc[(r.game_id, r.pid)] if (r.game_id, r.pid) in pr.index else None
        if x is not None and isinstance(x, pd.DataFrame): x = x.iloc[0]
        gv = lambda col, d=0: (rnd(x[col], d) if d else int(x[col])) if x is not None and col in x and pd.notna(x[col]) else None
        put(r.pid, "def", [int(r.week), r.game_id, r.defteam, om.get((r.game_id, r.defteam)), (int(s_.def_snaps) if s_ is not None and pd.notna(s_.def_snaps) else None), (rnd(s_.def_pct, 2) if s_ is not None else None),
            rnd(r.tackles, 1), int(r.solo), rnd(r.sacks, 1), int(r.ints), int(r.pd), int(r.plays_faced),
            gv("def_targets"), gv("def_completions_allowed"), gv("def_yards_allowed"), gv("def_receiving_td_allowed"), gv("def_passer_rating_allowed", 1), gv("def_pressures"), gv("def_missed_tackles")])
    # kickers
    from .props import kicker_games
    kg = kicker_games([season])
    om_off = {(a, b): c for a, b, c in zip(opp.game_id, opp.o, opp.t)}   # the kicking team's opponent
    for r in kg.itertuples():
        put(r.player_id, "kick", [int(r.week), r.game_id, r.team, om_off.get((r.game_id, r.team)), int(r.fgm), int(r.fga), int(r.xpm), int(r.xpa), int(r.pts)])
    # the full box score (24 Sep 2026, Matt: every piece of player data on the site): every official stat for the game
    # that the tables above do not already carry, the PFR advanced columns they do not show, and special-teams snaps;
    # nonzero values only, as [column index, value] pairs keyed by week (the column list is BOX_COLS in player_careers.js)
    sf = RAW / "player_stats" / f"stats_player_week_{season}.parquet"
    if sf.exists():
        st = pd.read_parquet(sf)
        st = st[[c for c in ["player_id", "week", "game_id"] + BOX_OFFICIAL if c in st.columns]]
        num = st[[c for c in BOX_OFFICIAL if c in st.columns]].apply(pd.to_numeric, errors="coerce")
        adv = {}
        for kind, cols in BOX_PFR.items():
            a = _pfr(kind, season, pmap)
            if len(a):
                for r in a.itertuples():
                    d = adv.setdefault((r.player_id, r.game_id), {})
                    for c in cols:
                        v = getattr(r, c, None)
                        if v is not None and pd.notna(v) and v != 0:
                            d[f"pfr_{c}"] = float(v)
        bidx = {c: i for i, c in enumerate(BOX_COLS)}
        seen = set()
        for i, r in enumerate(st.itertuples()):
            row = num.iloc[i]; pairs = []
            for c, v in row.items():
                if pd.notna(v) and v != 0:
                    pairs.append([bidx[c], _clean(v)])
            for c, v in adv.get((r.player_id, r.game_id), {}).items():
                pairs.append([bidx[c], _clean(v)])
            s_ = snapd.get((r.player_id, r.game_id))
            if s_ is not None and "st_snaps" in s_._fields and pd.notna(s_.st_snaps) and s_.st_snaps:
                pairs.append([bidx["st_snaps"], int(s_.st_snaps)])
            if pairs:
                out.setdefault(r.player_id, {}).setdefault("box", []).append([int(r.week), pairs]); seen.add((r.player_id, r.game_id))
    for pid in out:
        for k in out[pid]:
            out[pid][k].sort(key=lambda r: r[0])
    return out


def _clean(v):
    v = float(v)
    return int(v) if abs(v - round(v)) < 1e-9 else round(v, 2)


def careers(all_logs: dict) -> dict:
    """{player_id: [[season, kind, games, key totals...]]} from the season logs."""
    idx = {k: {c: i for i, c in enumerate(v)} for k, v in COLS.items()}
    SUM = {"rec": ["targets", "catches", "yards", "td", "epa"], "rush": ["carries", "yards", "td", "epa"], "pass": ["attempts", "completions", "yards", "td", "int", "sacks", "epa"],
           "def": ["tackles", "sacks", "ints", "passes_defended"], "kick": ["fgm", "fga", "xpm", "xpa", "points"]}
    out = {}
    for season, logs in all_logs.items():
        for pid, kinds in logs.items():
            for k, rows in kinds.items():
                if k not in SUM:   # the full box score has its own columns
                    continue
                tot = [round(sum((r[idx[k][c]] or 0) for r in rows), 2) for c in SUM[k]]
                teams = sorted({r[2] for r in rows if r[2]})
                out.setdefault(pid, []).append([season, k, len(rows), "/".join(teams)] + tot)
    return {"sum_cols": SUM, "rows": out}


def export(seasons=range(2016, 2027)) -> dict:
    from .positions import names_by_id
    seasons = [s for s in seasons if (RAW / "pbp" / f"play_by_play_{s}.parquet").exists()]
    pmap = _pfr_map(seasons)
    (WEB / "plogs").mkdir(parents=True, exist_ok=True)
    all_logs, sizes = {}, {}
    for s in seasons:
        lg = season_logs(s, pmap); all_logs[s] = lg
        txt = f"window.PLOGS_S=window.PLOGS_S||{{}};window.PLOGS_S[{s}]=" + json.dumps(lg, separators=(",", ":")) + ";"
        (WEB / "plogs" / f"{s}.js").write_text(txt); sizes[s] = len(txt)
    nm = names_by_id(range(2014, 2027))
    ids = {pid for lg in all_logs.values() for pid in lg}
    car = careers(all_logs)
    full = {}
    for s_ in seasons:   # the rosters' full names and positions, newest season last so it wins; the play-by-play's short names fill any gap
        f = RAW / "rosters" / f"roster_weekly_{s_}.parquet"
        if f.exists():
            r = pd.read_parquet(f, columns=["gsis_id", "full_name", "position"]).dropna(subset=["gsis_id", "full_name"]).drop_duplicates("gsis_id", keep="last")
            full.update({g: [n, pos] for g, n, pos in zip(r.gsis_id, r.full_name, r.position)})
    names = {pid: (full.get(pid) or [nm[pid][0], nm[pid][1]]) for pid in ids if pid in full or pid in nm}
    # bio (24 Sep 2026): the newest roster row per player (size, birth date, college, experience, jersey, draft) and the
    # draft table's round, pick and club; injury history: every weekly report line (status, practice, injury)
    bio = {}
    for s_ in seasons:
        f = RAW / "rosters" / f"roster_weekly_{s_}.parquet"
        if f.exists():
            r = pd.read_parquet(f).sort_values("week").drop_duplicates("gsis_id", keep="last")
            for x in r.itertuples():
                if isinstance(x.gsis_id, str) and x.gsis_id in ids:
                    bio[x.gsis_id] = [getattr(x, "height", None), getattr(x, "weight", None), str(getattr(x, "birth_date", "") or "")[:10], getattr(x, "college", None),
                                      getattr(x, "entry_year", None), getattr(x, "rookie_year", None), getattr(x, "draft_club", None), getattr(x, "draft_number", None),
                                      getattr(x, "years_exp", None), getattr(x, "jersey_number", None), getattr(x, "team", None), getattr(x, "status", None)]
    df_ = RAW / "draft" / "draft_picks.parquet"
    if df_.exists():
        dr = pd.read_parquet(df_, columns=["gsis_id", "season", "round", "pick", "team"]).dropna(subset=["gsis_id"]).drop_duplicates("gsis_id")
        for x in dr.itertuples():
            if x.gsis_id in bio:
                bio[x.gsis_id][4], bio[x.gsis_id][6], bio[x.gsis_id][7] = int(x.season), x.team, int(x.pick)
                bio[x.gsis_id].append(int(x.round))
    clean = lambda v: None if v is None or (isinstance(v, float) and v != v) else (int(v) if isinstance(v, float) and v == int(v) else v)
    bio = {k: [clean(v) for v in vs] for k, vs in bio.items()}
    inj = []
    for s_ in seasons:
        f = RAW / "injuries" / f"injuries_{s_}.parquet"
        if f.exists():
            r = pd.read_parquet(f, columns=["season", "week", "gsis_id", "report_status", "practice_status", "report_primary_injury", "practice_primary_injury"])
            inj.append(r[r.gsis_id.isin(ids)])
    injh, codes = {}, {"": 0}
    code = lambda v: codes.setdefault(v, len(codes))   # statuses, practice notes and injuries repeat: one table, small numbers
    if inj:
        r = pd.concat(inj, ignore_index=True)
        for x in r.itertuples():
            st_ = x.report_status if isinstance(x.report_status, str) else ""; pr_ = x.practice_status if isinstance(x.practice_status, str) else ""
            what = x.report_primary_injury if isinstance(x.report_primary_injury, str) else (x.practice_primary_injury if isinstance(x.practice_primary_injury, str) else "")
            if st_ or pr_ or what:
                injh.setdefault(x.gsis_id, []).append([int(x.season) - 2000, int(x.week), code(st_), code(pr_), code(what)])
    (WEB / "player_injuries.js").write_text("window.PINJ=" + json.dumps({"codes": sorted(codes, key=codes.get), "rows": injh}, separators=(",", ":")) + ";")
    meta = {"cols": COLS, "box_cols": BOX_COLS, "bio": bio, "bio_cols": ["height", "weight", "birth_date", "college", "draft_year", "rookie_year", "draft_team", "draft_pick", "years_exp", "jersey", "team", "roster_status", "draft_round"],
            "seasons": seasons, "names": names, "careers": car,
            "last_charted": int(pd.read_parquet(OUT / "scheme_plays.parquet", columns=["season", "man"]).dropna().season.max())}
    (WEB / "player_careers.js").write_text("window.PCAREER=" + json.dumps(meta, separators=(",", ":")) + ";")
    print(f"player logs: {len(ids)} players, seasons {seasons[0]} to {seasons[-1]}, files " + ", ".join(f"{s} {v / 1e6:.1f} MB" for s, v in sizes.items()) + f"; careers {(WEB / 'player_careers.js').stat().st_size / 1e6:.1f} MB", flush=True)
    return meta


if __name__ == "__main__":
    export()
