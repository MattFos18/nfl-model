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


def _pbp(season: int) -> pd.DataFrame:
    f = RAW / "pbp" / f"play_by_play_{season}.parquet"
    cols = ["game_id", "play_id", "season", "week", "season_type", "posteam", "defteam", "play_type", "pass_attempt", "qb_dropback", "sack", "complete_pass", "interception",
            "receiver_player_id", "rusher_player_id", "passer_player_id", "yards_gained", "air_yards", "yards_after_catch", "first_down_pass", "first_down_rush", "yardline_100",
            "pass_touchdown", "rush_touchdown", "fumble_lost", "fumbled_1_player_id", "epa", "two_point_attempt"]
    import pyarrow.parquet as pq
    have = set(pq.ParquetFile(f).schema.names)
    p = pd.read_parquet(f, columns=[c for c in cols if c in have])
    from .features import TEAM_FIX
    p["posteam"] = p.posteam.replace(TEAM_FIX); p["defteam"] = p.defteam.replace(TEAM_FIX)
    p = p[p.season_type.eq("REG") | p.season_type.eq("POST")] if "season_type" in p.columns else p
    return p[p.play_type.isin(["pass", "run"]) & (p.two_point_attempt.fillna(0) == 0)].copy()


def _looks(season: int) -> pd.DataFrame:
    s = pd.read_parquet(OUT / "scheme_plays.parquet", columns=["game_id", "play_id", "season", "man", "zone", "pressure", "box"])
    s = s[s.season == season].drop(columns="season")
    s["man_f"] = s.man.fillna(False).astype(float); s["zone_f"] = s.zone.fillna(False).astype(float); s["press_f"] = (s.pressure == 1).astype(float)
    s["light_f"] = (s.box <= 6).astype(float); s["heavy_f"] = (s.box >= 8).astype(float)
    return s[["game_id", "play_id", "man_f", "zone_f", "press_f", "light_f", "heavy_f"]]


def _pfr_map(seasons) -> dict:
    out = {}
    for s in seasons:
        f = RAW / "rosters" / f"roster_weekly_{s}.parquet"
        if f.exists():
            r = pd.read_parquet(f, columns=["gsis_id", "pfr_id"]).dropna().drop_duplicates()
            out.update(dict(zip(r.pfr_id, r.gsis_id)))
    return out


def _pfr(kind: str, season: int, pmap: dict) -> pd.DataFrame:
    f = RAW / f"pfr_{kind}" / f"advstats_week_{kind}_{season}.parquet"
    if kind == "def":
        f = RAW / "pfr_advstats" / f"advstats_week_def_{season}.parquet"
    if not f.exists():
        return pd.DataFrame(columns=["game_id", "player_id"])
    d = pd.read_parquet(f); d["player_id"] = d.pfr_player_id.map(pmap)
    return d[d.player_id.notna()]


def _snaps(season: int, pmap: dict) -> pd.DataFrame:
    f = RAW / "snap_counts" / f"snap_counts_{season}.parquet"
    if not f.exists():
        return pd.DataFrame(columns=["game_id", "player_id", "off_snaps", "off_pct", "def_snaps", "def_pct"])
    d = pd.read_parquet(f, columns=["game_id", "pfr_player_id", "offense_snaps", "offense_pct", "defense_snaps", "defense_pct"])
    d["player_id"] = d.pfr_player_id.map(pmap)
    return d[d.player_id.notna()].rename(columns={"offense_snaps": "off_snaps", "offense_pct": "off_pct", "defense_snaps": "def_snaps", "defense_pct": "def_pct"}).drop(columns="pfr_player_id").drop_duplicates(["game_id", "player_id"])


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
    u = p[(p.play_type == "run") & p.rusher_player_id.notna()].copy()
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
    q = p[(p.qb_dropback == 1) & p.passer_player_id.notna()].copy()
    q["att"] = ((q.pass_attempt == 1) & (q.sack == 0)).astype(float); q["lg"] = np.where(q.complete_pass == 1, q.yards_gained, 0.0); q["ay"] = q.air_yards.fillna(0.0) * q.att
    for c, f in (("man", "man_f"), ("zone", "zone_f"), ("press", "press_f")):
        q[f"{c}_n"] = q[f]; q[f"{c}_yds"] = q.yards_gained * q[f]
    g = q.groupby(["passer_player_id", "week", "game_id", "posteam", "defteam"]).agg(dropbacks=("play_id", "size"), attempts=("att", "sum"), completions=("complete_pass", "sum"),
        yards=("yards_gained", "sum"), td=("pass_touchdown", "sum"), int_=("interception", "sum"), sacks=("sack", "sum"), longest=("lg", "max"), air_yds=("ay", "sum"), first_downs=("first_down_pass", "sum"), epa=("epa", "sum"),
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
    for r in dg.itertuples():
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
    for pid in out:
        for k in out[pid]:
            out[pid][k].sort(key=lambda r: r[0])
    return out


def careers(all_logs: dict) -> dict:
    """{player_id: [[season, kind, games, key totals...]]} from the season logs."""
    idx = {k: {c: i for i, c in enumerate(v)} for k, v in COLS.items()}
    SUM = {"rec": ["targets", "catches", "yards", "td", "epa"], "rush": ["carries", "yards", "td", "epa"], "pass": ["attempts", "completions", "yards", "td", "int", "sacks", "epa"],
           "def": ["tackles", "sacks", "ints", "passes_defended"], "kick": ["fgm", "fga", "xpm", "xpa", "points"]}
    out = {}
    for season, logs in all_logs.items():
        for pid, kinds in logs.items():
            for k, rows in kinds.items():
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
    meta = {"cols": COLS, "seasons": seasons, "names": names, "careers": car,
            "last_charted": int(pd.read_parquet(OUT / "scheme_plays.parquet", columns=["season", "man"]).dropna().season.max())}
    (WEB / "player_careers.js").write_text("window.PCAREER=" + json.dumps(meta, separators=(",", ":")) + ";")
    print(f"player logs: {len(ids)} players, seasons {seasons[0]} to {seasons[-1]}, files " + ", ".join(f"{s} {v / 1e6:.1f} MB" for s, v in sizes.items()) + f"; careers {(WEB / 'player_careers.js').stat().st_size / 1e6:.1f} MB", flush=True)
    return meta


if __name__ == "__main__":
    export()
