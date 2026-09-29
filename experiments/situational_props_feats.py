"""Inputs for experiments/situational_props.py (the props side of round 3; experiments/situational_feats.py belongs to
the game-model study): per (game, team) situation, kickoff time, weather and injury readings, and the player-vs-player
readings (defender ratings, expected starters), every one as of before the game. Only data the weekly run already pulls:
schedules (games.parquet), the charted plays, participation, snap counts, the injury report and weekly rosters, PFR
advanced defense (via defender_games), the play-by-play credits, and trends_asof / features_asof (the game model's own
as-of situation table). The stadium table below (latitude, longitude, time zone) is static."""
import numpy as np, pandas as pd
from zoneinfo import ZoneInfo
import datetime as dt
from nflmodel import props as PR
from nflmodel.features import OUT, RAW
from nflmodel.model import WARM_OR_DOME

# stadium_id: (lat, lon, IANA time zone)
STAD = {"ATL00": (33.758, -84.401, "America/New_York"), "ATL97": (33.755, -84.401, "America/New_York"), "BAL00": (39.278, -76.623, "America/New_York"),
        "BOS00": (42.091, -71.264, "America/New_York"), "BUF00": (42.774, -78.787, "America/New_York"), "CAR00": (35.226, -80.853, "America/New_York"),
        "CHI98": (41.862, -87.617, "America/Chicago"), "CIN00": (39.095, -84.516, "America/New_York"), "CLE00": (41.506, -81.700, "America/New_York"),
        "DAL00": (32.748, -97.093, "America/Chicago"), "DEN00": (39.744, -105.020, "America/Denver"), "DET00": (42.340, -83.046, "America/Detroit"),
        "FRA00": (50.069, 8.645, "Europe/Berlin"), "GER00": (48.219, 11.625, "Europe/Berlin"), "GNB00": (44.501, -88.062, "America/Chicago"),
        "HOU00": (29.685, -95.411, "America/Chicago"), "IND00": (39.760, -86.164, "America/Indiana/Indianapolis"), "JAX00": (30.324, -81.637, "America/New_York"),
        "KAN00": (39.049, -94.484, "America/Chicago"), "LAX01": (33.953, -118.339, "America/Los_Angeles"), "LAX97": (33.864, -118.261, "America/Los_Angeles"),
        "LAX99": (34.014, -118.288, "America/Los_Angeles"), "LON00": (51.556, -0.280, "Europe/London"), "LON01": (51.456, -0.341, "Europe/London"),
        "LON02": (51.604, -0.066, "Europe/London"), "MAD01": (40.453, -3.688, "Europe/Madrid"), "MEL00": (-37.820, 144.983, "Australia/Melbourne"),
        "MEX00": (19.303, -99.150, "America/Mexico_City"), "MIA00": (25.958, -80.239, "America/New_York"), "MIN01": (44.974, -93.258, "America/Chicago"),
        "MIN98": (44.976, -93.225, "America/Chicago"), "MUN01": (48.219, 11.625, "Europe/Berlin"), "NAS00": (36.166, -86.771, "America/Chicago"),
        "NOR00": (29.951, -90.081, "America/Chicago"), "NYC01": (40.814, -74.074, "America/New_York"), "OAK00": (37.752, -122.201, "America/Los_Angeles"),
        "PAR00": (48.924, 2.360, "Europe/Paris"), "PHI00": (39.901, -75.168, "America/New_York"), "PHO00": (33.528, -112.263, "America/Phoenix"),
        "PIT00": (40.447, -80.016, "America/New_York"), "RIO00": (-22.912, -43.230, "America/Sao_Paulo"), "SAO00": (-23.545, -46.474, "America/Sao_Paulo"),
        "SDG00": (32.783, -117.120, "America/Los_Angeles"), "SEA00": (47.595, -122.332, "America/Los_Angeles"), "SFO01": (37.403, -121.970, "America/Los_Angeles"),
        "STL00": (38.633, -90.188, "America/Chicago"), "TAM00": (27.976, -82.503, "America/New_York"), "VEG00": (36.091, -115.184, "America/Los_Angeles"),
        "WAS00": (38.908, -76.864, "America/New_York")}
INTL = {"FRA00", "GER00", "LON00", "LON01", "LON02", "MAD01", "MEL00", "MEX00", "MUN01", "PAR00", "RIO00", "SAO00"}
EAST_TZ = {"America/New_York", "America/Detroit", "America/Indiana/Indianapolis"}; WEST_TZ = {"America/Los_Angeles", "America/Phoenix"}


def _km(a, b):
    la1, lo1, la2, lo2 = map(np.radians, [a[0], a[1], b[0], b[1]])
    h = np.sin((la2 - la1) / 2) ** 2 + np.cos(la1) * np.cos(la2) * np.sin((lo2 - lo1) / 2) ** 2
    return 6371.0 * 2 * np.arcsin(np.sqrt(h))


def game_table() -> pd.DataFrame:
    """One row per (game_id, team): every situation, kickoff and weather reading the ideas use, as of before kickoff.
    The weather is the recorded kickoff reading (schedule wind and temperature, the play-by-play weather text for rain and
    snow): the backtest has no archive of the kickoff forecast, the same stand-in the game model's backtest and the props'
    wind rule use; live, the Open-Meteo kickoff forecast takes its place."""
    g = pd.read_parquet(OUT / "games.parquet"); g = g[(g.season >= 2015) & (g.game_type == "REG")].copy()
    g["surface"] = g.surface.fillna("").str.strip().replace("", np.nan)
    g = g.sort_values(["season", "week"]); g["surface"] = g.groupby("stadium_id").surface.transform(lambda s: s.ffill().bfill()).fillna("grass")   # a missing surface: the stadium's known one, else grass (international)
    home_std = g[g.location.eq("Home") & ~g.stadium_id.isin(INTL)].groupby(["season", "home_team"]).stadium_id.agg(lambda s: s.mode().iloc[0]).to_dict()
    tr = pd.read_parquet(OUT / "trends_asof.parquet")[["game_id", "team", "body_clock_early", "rain", "snow", "travel_miles", "tz_shift", "qb_out", "ol_out", "off_starters_out", "def_starters_out", "off_snap_out", "def_snap_out", "is_cold"]]
    fa = pd.read_parquet(OUT / "features_asof.parquet", columns=["game_id", "team", "rest", "opp_rest", "dome", "temp", "wind", "qb_rating", "opp_qb_rating", "qb_id"])
    rows = []
    for r in g.itertuples():
        for side, opp in (("home", "away"), ("away", "home")):
            t = getattr(r, f"{side}_team"); o = getattr(r, f"{opp}_team")
            hs = home_std.get((r.season, t)) or home_std.get((r.season - 1, t)); hv = STAD.get(hs); gv = STAD.get(r.stadium_id, hv)
            is_home = float(side == "home" and r.location == "Home")
            body = np.nan; tzs = 0.0
            try:
                hh, mm = (int(x) for x in str(r.gametime).split(":")); d_ = dt.date.fromisoformat(str(r.gameday)[:10])
                ko = dt.datetime(d_.year, d_.month, d_.day, hh, mm, tzinfo=ZoneInfo("America/New_York"))
                if hv: bl = ko.astimezone(ZoneInfo(hv[2])); body = bl.hour + bl.minute / 60
                if hv and gv: tzs = (ko.astimezone(ZoneInfo(gv[2])).utcoffset() - ko.astimezone(ZoneInfo(hv[2])).utcoffset()).total_seconds() / 3600
            except (ValueError, TypeError):
                pass
            gd = pd.Timestamp(str(r.gameday)[:10]); thanks = gd.month == 11 and gd.weekday() in (3, 4) and 22 <= gd.day - (gd.weekday() - 3) <= 28
            rows.append({"game_id": r.game_id, "team": t, "opp": o, "home": is_home, "neutral": float(r.location != "Home"), "turf": float(r.surface != "grass"),
                         "indoor": float(r.roof in ("dome", "closed")), "dome_fixed": float(r.roof == "dome"), "stadium_id": r.stadium_id, "opp_coach": getattr(r, f"{opp}_coach"),
                         "primetime": float(bool(r.primetime)), "slot": r.slot, "weekday": r.weekday, "hour_et": r.hour_et, "div": float(r.div_game == 1),
                         "km": 0.0 if (is_home and hv) else (_km(hv, gv) if (hv and gv) else np.nan), "tz_signed": tzs, "body_hour": body,
                         "home_tz": hv[2] if hv else "", "game_tz": gv[2] if gv else "", "altitude": float(r.stadium_id == "DEN00" and t != "DEN"),
                         "holiday": float(thanks or (gd.month == 12 and gd.day == 25)), "international": float(r.stadium_id in INTL), "roof": r.roof})
    G = pd.DataFrame(rows).merge(tr, on=["game_id", "team"], how="left").merge(fa, on=["game_id", "team"], how="left")
    G["outdoor"] = 1.0 - G.indoor
    G["wind_mph"] = np.where(G.indoor > 0, 0.0, G.wind.fillna(0.0).clip(upper=40)); G["wind10"] = np.maximum(G.wind_mph - PR.WIND_FROM, 0.0)
    G["windy"] = (G.wind_mph >= 15).astype(float); G["rain"] = G.rain.fillna(0.0) * G.outdoor; G["snow"] = G.snow.fillna(0.0) * G.outdoor
    G["cold"] = ((G.outdoor > 0) & (G.temp.fillna(60) < 35)).astype(float)
    G["bad"] = ((G.windy + G.rain + G.snow + G.cold) > 0).astype(float)
    G["warm_in_cold"] = G.cold * G.team.isin(WARM_OR_DOME).astype(float)
    G["night"] = ((G.hour_et >= 19) | G.slot.isin(["SNF", "MNF", "TNF"])).astype(float)
    G["early"] = G.slot.eq("SUN_EARLY").astype(float); G["late"] = G.slot.eq("SUN_LATE").astype(float)
    for s_ in ("SNF", "MNF", "TNF"): G[s_.lower()] = G.slot.eq(s_).astype(float)
    for w_, c_ in (("Thursday", "thu"), ("Saturday", "sat"), ("Sunday", "sun"), ("Monday", "mon")): G[c_] = G.weekday.eq(w_).astype(float)
    G["rest_days"] = G.rest.clip(4, 14).fillna(7.0); G["short_week"] = (G.rest <= 5).astype(float); G["off_bye"] = (G.rest >= 13).astype(float)
    G["rest_diff"] = (G.rest - G.opp_rest).clip(-7, 7).fillna(0.0); G["opp_off_bye"] = (G.opp_rest >= 13).astype(float)
    G["travel"] = G.km.fillna(0.0) / 1000.0; G["tz_abs"] = G.tz_signed.abs()
    G["west_1pm"] = G.body_clock_early.fillna(0.0)
    G["east_late_west"] = (G.home_tz.isin(EAST_TZ) & G.game_tz.isin(WEST_TZ) & (G.hour_et >= 20)).astype(float)
    G["body_hour"] = G.body_hour.fillna(13.0)
    G["bad_turf"] = G.bad * G.turf; G["bad_grass"] = G.bad * (1 - G.turf); G["bad_night"] = G.bad * G.night; G["wind_turf"] = G.wind10 * G.turf
    for c in ("qb_out", "ol_out", "off_starters_out", "def_starters_out", "off_snap_out", "def_snap_out"): G[c] = G[c].fillna(0.0)
    opp = G[["game_id", "team", "def_starters_out", "def_snap_out", "off_starters_out"]].rename(columns={"team": "opp", "def_starters_out": "opp_def_starters_out", "def_snap_out": "opp_def_snap_out", "off_starters_out": "opp_off_starters_out"})
    G = G.merge(opp, on=["game_id", "opp"], how="left")
    G["inj_x_bad"] = G.off_starters_out * G.bad; G["qbout_x_bad"] = G.qb_out * G.bad; G["inj_x_short"] = G.off_starters_out * G.short_week
    return G


# ---------------------------------------------------------------------------------------------------------- defenders
DEF_ROLE_SNAP = {"CB": "CB", "DB": "CB", "NB": "CB", "S": "S", "SS": "S", "FS": "S", "LB": "LB", "ILB": "LB", "MLB": "LB", "OLB": "LB",
                 "DE": "EDGE", "EDGE": "EDGE", "DT": "IDL", "NT": "IDL", "DL": "IDL"}
N_START = {"CB": 3, "S": 2, "LB": 2, "EDGE": 2, "IDL": 2}


def _seg_decayed(keys, vals, decay, seasons=None, fade=1.0):
    """For rows sorted by key then time: the decayed sums INCLUDING each row (the post-row state): weight 1 on the row,
    decay per earlier row of the same key, and fade per season back (referenced to the row's season)."""
    keys = np.asarray(keys); n = len(keys)
    start = np.r_[True, keys[1:] != keys[:-1]]; grp = np.cumsum(start) - 1; first = np.flatnonzero(start); idx = np.arange(n) - first[grp]
    lw = -idx * np.log(decay)
    if seasons is not None and fade != 1.0:
        sv = np.asarray(seasons, float); lw = lw - (sv - sv[first[grp]]) * np.log(fade)
    V = np.asarray(vals, float); one = V.ndim == 1
    if one: V = V[:, None]
    E = np.exp(lw)
    C = pd.DataFrame(V * E[:, None]).groupby(grp).cumsum().values / E[:, None]
    return C[:, 0] if one else C


def defender_ratings():
    """Every defender's rating after each of his games (the positions.py recipes: CB coverage per target at the league's
    corner targets per snap; S and IDL the same plus half his other value per snap; EDGE and LB all value per snap, LB
    with 0.75 per credited play; decays 0.99 / 0.98 per game, EDGE and LB 0.9 a season back), 2018 on (PFR coverage).
    Rows: player_id, season, week, key, role, rating (the post-game state; a later game reads the last one before it)."""
    from nflmodel.positions import DEF_W, defender_roles
    dg = pd.read_parquet(OUT / "defender_games.parquet")
    roles = defender_roles(dg)
    d = dg[dg.season >= 2018].copy(); d["role"] = d.player_id.map(roles); d = d[d.role.isin(["CB", "S", "IDL", "EDGE", "LB"])]
    d = d.sort_values(["player_id", "season", "week"]).reset_index(drop=True)
    cov = DEF_W["cov_yds"] * d.cov_yds.values + DEF_W["cov_int"] * d.cov_int.values; rush = DEF_W["sacks"] * d.sacks.values + DEF_W["press_ns"] * d.press_ns.values
    d["cov_v"] = cov; d["other_v"] = rush + d.run_stop.values; d["all_v"] = cov + rush + d.run_stop.values + d.ff_epa.values + np.where(d.role.eq("LB"), 0.75 * d.credited.values, 0.0)
    cbs = d[d.role.eq("CB")]; t_snap = cbs.groupby("season").targets.sum() / cbs.groupby("season").plays.sum()
    out = []
    for role, g in d.groupby("role"):
        g = g.reset_index(drop=True); snap = role in ("EDGE", "LB"); dec, fade = (0.98, 0.9) if snap else (0.99, 1.0)
        S = _seg_decayed(g.player_id.values, g[["cov_v", "targets", "plays", "other_v", "all_v"]].values, dec, g.season.values, fade)
        ts = g.season.map(lambda s: t_snap.get(s - 1, t_snap.get(s, 0.09))).values
        if snap:
            rt = S[:, 4] / (S[:, 2] + 300.0)
        else:
            rt = S[:, 0] / (S[:, 1] + 150.0) * ts + (0.0 if role == "CB" else 0.5) * S[:, 3] / (S[:, 2] + 300.0)
        out.append(pd.DataFrame({"player_id": g.player_id, "season": g.season, "week": g.week, "role": role, "rating": rt, "fade": fade}))
    R = pd.concat(out, ignore_index=True); R["key"] = R.season.astype("int64") * 100 + R.week.astype("int64")
    return R, roles


def expected_defense(known_out: pd.DataFrame, ratings: pd.DataFrame, roles: dict) -> pd.DataFrame:
    """Per (game_id, defteam): the defense this week's report and roster can know. Candidates: every defender with a
    defensive snap for the team in one of its last 3 games; expected share = his mean snap share over those 3; starters per
    role = the top N (CB 3, S 2, LB 2, EDGE 2, IDL 2) of those not known out (report Out / Doubtful, or no active roster
    listing). Returns per role: the snap-weighted rating of the expected starters (<role>_r), of the players who actually
    played the team's last 8 games at their ratings now (<role>_base), and the expected share of the top-N who are known
    out (<role>_out); plus the expected corners (cb_list: id, share, rating) for the pair histories."""
    sx = pd.read_parquet(OUT / "snap_exposure.parquet", columns=["player_id", "game_id", "season", "week", "team", "position", "def_pct"])
    sx = sx[(sx.season >= 2015) & (sx.def_pct > 0)].copy(); sx["role"] = sx.player_id.map(roles).fillna(sx.position.map(DEF_ROLE_SNAP))
    sx = sx[sx.role.isin(list(N_START))]
    tg = sx[["team", "game_id", "season", "week"]].drop_duplicates().sort_values(["team", "season", "week"]).reset_index(drop=True); tg["k"] = tg.groupby("team").cumcount()
    # the team-games still to be priced after the last one with snaps (2026 upcoming games are not scored; not needed)
    sx = sx.merge(tg[["team", "game_id", "k"]], on=["team", "game_id"])
    C = pd.concat([sx.assign(k=sx.k + o) for o in (1, 2, 3)])
    C = C.groupby(["team", "k", "player_id", "role"]).def_pct.sum().div(3.0).rename("share").reset_index().merge(tg, on=["team", "k"])
    ko = known_out.rename(columns={"pid": "player_id"}); C = C.merge(ko, on=["player_id", "season", "week"], how="left"); C["known_out"] = C.known_out.fillna(0)
    C["key"] = C.season.astype("int64") * 100 + C.week.astype("int64")
    Rt = ratings[["player_id", "key", "rating", "season", "fade"]].rename(columns={"season": "r_season"}).sort_values("key")
    C = pd.merge_asof(C.sort_values("key"), Rt, on="key", by="player_id", direction="backward", allow_exact_matches=False)
    C["rating"] = C.rating * np.where(C.r_season.notna(), C.fade.fillna(1.0) ** (C.season - C.r_season.fillna(C.season)), 1.0)
    C = C.sort_values(["team", "k", "role", "share"], ascending=[True, True, True, False])
    avail = C[C.known_out == 0].copy(); avail["rk"] = avail.groupby(["team", "k", "role"]).cumcount(); st = avail[avail.rk < avail.role.map(N_START)]
    allrk = C.copy(); allrk["rk"] = allrk.groupby(["team", "k", "role"]).cumcount(); top = allrk[allrk.rk < allrk.role.map(N_START)]
    res = tg[["team", "game_id", "season", "week", "k"]].copy()
    for role in N_START:
        s_ = st[st.role.eq(role) & st.rating.notna()]
        wr = s_.assign(w=s_.share * s_.rating).groupby(["team", "k"]).agg(w=("w", "sum"), s=("share", "sum"))
        res = res.merge((wr.w / wr.s).rename(f"{role}_r").reset_index(), on=["team", "k"], how="left")
        o_ = top[top.role.eq(role) & (top.known_out == 1)].groupby(["team", "k"]).share.sum().rename(f"{role}_out").reset_index()
        res = res.merge(o_, on=["team", "k"], how="left"); res[f"{role}_out"] = res[f"{role}_out"].fillna(0.0)
    B = pd.concat([sx.assign(k=sx.k + o) for o in range(1, 9)]).groupby(["team", "k", "player_id", "role"]).def_pct.sum().rename("snaps").reset_index().merge(tg[["team", "k", "season", "week"]], on=["team", "k"])
    B["key"] = B.season.astype("int64") * 100 + B.week.astype("int64")
    B = pd.merge_asof(B.sort_values("key"), Rt, on="key", by="player_id", direction="backward", allow_exact_matches=False).dropna(subset=["rating"])
    for role in N_START:
        b_ = B[B.role.eq(role)].assign(w=lambda x: x.snaps * x.rating).groupby(["team", "k"]).agg(w=("w", "sum"), s=("snaps", "sum"))
        res = res.merge((b_.w / b_.s).rename(f"{role}_base").reset_index(), on=["team", "k"], how="left")
    cb = st[st.role.eq("CB")].groupby(["team", "k"]).apply(lambda x: list(zip(x.player_id, x.share, x.rating))).rename("cb_list").reset_index()
    res = res.merge(cb, on=["team", "k"], how="left")
    return res.rename(columns={"team": "defteam"}).drop(columns=["k"])


# ------------------------------------------------------------------------------------------------ pbp-based readings
def pass_plays_with_defenders(seasons=range(2016, 2026)):
    """Every targeted pass play with the targeted receiver, the defense on the field (participation) and the defenders
    credited on the play (solo / assist tackles, passes defensed, interceptions; the play-by-play)."""
    cols = ["game_id", "play_id", "season", "week", "posteam", "defteam", "receiver_player_id", "yards_gained", "pass_attempt", "sack", "season_type",
            "solo_tackle_1_player_id", "solo_tackle_2_player_id", "assist_tackle_1_player_id", "assist_tackle_2_player_id", "pass_defense_1_player_id", "pass_defense_2_player_id", "interception_player_id"]
    out = []
    for s in seasons:
        p = pd.read_parquet(RAW / "pbp" / f"play_by_play_{s}.parquet", columns=cols); p = p[(p.season_type == "REG") & p.receiver_player_id.notna() & (p.pass_attempt == 1)]
        pa = pd.read_parquet(RAW / "participation" / f"pbp_participation_{s}.parquet", columns=["nflverse_game_id", "play_id", "defense_players"]).rename(columns={"nflverse_game_id": "game_id"})
        p = p.merge(pa, on=["game_id", "play_id"], how="left"); out.append(p)
    return pd.concat(out, ignore_index=True)
