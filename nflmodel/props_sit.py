"""The inputs of the situational props factors (props.SIT; round 3 of the props, 29 Sep 2026: experiments/situational_props.py,
reports/situational_props.md). Every input is as of before kickoff and comes from data the weekly run already builds: the
schedule (games.parquet, with the kickoff forecast in use), the game model's as-of tables (features_asof: rest and the
starter's QB rating; trends_asof: the rain call), the snap counts (snap_exposure), the defender game table
(defender_games, PFR coverage from 2018) and the injury report and weekly rosters (the known-out table). No market input.

Per (game, team): days of rest, the starter's QB rating, rain at kickoff (outdoors), cold (under 35 F outdoors), mph of
kickoff wind above 10 on turf; per (game, defence): this week's expected starting corners' rating (the top three by snap
share over the team's last three games, less the known-out, rated by the positions.py corner recipe) and that minus the
corners who played the defence's last eight games. The known-out starters' shares at a receiver's position group are
the absorb step's (props.absorb live, experiments/props_by_season.absorb_shares in the backtest).

centred(): an input less the player's own 0.85-decayed mean of it over his earlier player-games (weight 1 on his latest),
the q of the factor exp(b x (z - q)); the backtest writes each player's q for his next game to
data/processed/props_sit_state.parquet, which the live card reads."""
from __future__ import annotations
import numpy as np, pandas as pd
from .features import OUT, RAW

DECAY = 0.85          # the decay of a player's own history of an input (props.DECAY)
COLD_F = 35.0         # cold: under 35 F outdoors (the game model's cold call)
RAIN_PROB, RAIN_MM = 50, 1.0   # an unplayed game's forecast calls rain at a 50%+ chance or 1 mm+ in the kickoff hour (trends.py)
CB_N, CB_LAST, CB_BASE = 3, 3, 8   # expected starting corners: top 3 by snap share over the last 3 games; the base: the last 8 games' corners
DEF_ROLE_SNAP = {"CB": "CB", "DB": "CB", "NB": "CB", "S": "S", "SS": "S", "FS": "S", "LB": "LB", "ILB": "LB", "MLB": "LB", "OLB": "LB",
                 "DE": "EDGE", "EDGE": "EDGE", "DT": "IDL", "NT": "IDL", "DL": "IDL"}
STATE = OUT / "props_sit_state.parquet"


def seg_decayed(keys, vals, decay):
    """For rows sorted by key then time: the decayed sums INCLUDING each row, weight 1 on the row and `decay` per earlier
    row of the same key."""
    keys = np.asarray(keys); n = len(keys)
    start = np.r_[True, keys[1:] != keys[:-1]]; grp = np.cumsum(start) - 1; first = np.flatnonzero(start); idx = np.arange(n) - first[grp]
    E = np.exp(-idx * np.log(decay)); V = np.asarray(vals, float); one = V.ndim == 1
    if one: V = V[:, None]
    C = pd.DataFrame(V * E[:, None]).groupby(grp).cumsum().values / E[:, None]
    return C[:, 0] if one else C


def centred(pid, season, week, z, fallback=None):
    """z less q, q the player's 0.85-decayed mean of z over his earlier rows (a missing z counts neither way; the decay still
    steps per row); `fallback` (default the mean of z) where he has none; 0 where z is missing. Returns (z - q per row,
    {pid: q for his next game}), the second NaN where he has no reading."""
    z = np.asarray(z, float); ok = ~np.isnan(z); pid = np.asarray(pid)
    order = np.lexsort((np.asarray(week), np.asarray(season), pid)); inv = np.empty(len(z), dtype=np.int64); inv[order] = np.arange(len(z))
    zz = np.where(ok, z, 0.0)[order]; vs = ok[order].astype(float); ps = pid[order]
    S = seg_decayed(ps, np.c_[zz * vs, vs], DECAY); P = S - np.c_[zz * vs, vs]
    q = np.where(P[:, 1] > 1e-9, P[:, 0] / np.where(P[:, 1] > 1e-9, P[:, 1], 1.0), np.nan)[inv]
    fb = (float(np.nanmean(z)) if ok.any() else 0.0) if fallback is None else fallback
    q = np.where(np.isnan(q), fb, q)
    last = np.r_[ps[1:] != ps[:-1], True]
    nxt = {p: (s0 / s1 if s1 > 1e-9 else np.nan) for p, s0, s1 in zip(ps[last], S[last, 0], S[last, 1])}
    return np.where(ok, z - q, 0.0), nxt


def _surface(g: pd.DataFrame) -> pd.Series:
    """The schedule's surface, a missing one filled with the stadium's known one, else grass (international venues)."""
    s = g.surface.fillna("").astype(str).str.strip().replace("", np.nan)
    o = g.assign(_s=s).sort_values(["season", "week"])
    return o.groupby("stadium_id")._s.transform(lambda x: x.ffill().bfill()).fillna("grass").reindex(g.index)


def game_inputs(games: pd.DataFrame | None = None) -> pd.DataFrame:
    """One row per (game_id, team), regular season from 2015: rest_days (4 to 14, 7 when unknown), qb_rating (the game
    model's, this week's starter), rain (the rain call, outdoors), cold (under 35 F outdoors), wind_turf (mph of kickoff
    wind above 10 on an artificial surface, outdoors). A played game's weather is the recorded kickoff reading, an
    unplayed one's the kickoff forecast the run has (as the game model reads it)."""
    from .props import WIND_FROM
    g = pd.read_parquet(OUT / "games.parquet") if games is None else games
    g = g[(g.season >= 2015) & (g.game_type == "REG")].copy(); g["surface"] = _surface(g)
    tr = pd.read_parquet(OUT / "trends_asof.parquet", columns=["game_id", "team", "rain"])
    fa = pd.read_parquet(OUT / "features_asof.parquet", columns=["game_id", "team", "rest", "temp", "wind", "qb_rating"])
    side = []
    for s_ in ("home", "away"):
        side.append(g[["game_id", "roof", "surface", f"{s_}_team"]].rename(columns={f"{s_}_team": "team"}))
    G = pd.concat(side, ignore_index=True).merge(tr, on=["game_id", "team"], how="left").merge(fa, on=["game_id", "team"], how="left")
    indoor = G.roof.isin(["dome", "closed"]).astype(float); outdoor = 1.0 - indoor; turf = (G.surface != "grass").astype(float)
    wind = np.where(indoor > 0, 0.0, G.wind.fillna(0.0).clip(upper=40))
    G["wind_turf"] = np.maximum(wind - WIND_FROM, 0.0) * turf
    G["rain"] = G.rain.fillna(0.0) * outdoor
    G["cold"] = ((outdoor > 0) & (G.temp.fillna(60) < COLD_F)).astype(float)
    G["rest_days"] = G.rest.clip(4, 14).fillna(7.0)
    return G[["game_id", "team", "rest_days", "qb_rating", "rain", "cold", "wind_turf"]]


def live_weather(g, forecast: pd.DataFrame | None = None, surface: str | None = None) -> dict:
    """This game's weather inputs from the kickoff forecast in use (games.parquet after weather.apply_to_games carries its
    temperature and wind; the rain call as trends.py makes it for an unplayed game: a 50%+ chance or 1 mm+ in the kickoff
    hour; no usable forecast: dry, still, not cold)."""
    from .props import WIND_FROM
    indoor = getattr(g, "roof", None) in ("dome", "closed"); surf = surface or str(getattr(g, "surface", "") or "").strip() or "grass"
    temp = getattr(g, "temp", None); wind = getattr(g, "wind", None)
    temp = 60.0 if temp is None or pd.isna(temp) else float(temp); wind = 0.0 if (indoor or wind is None or pd.isna(wind)) else min(float(wind), 40.0)
    rain = 0.0
    if not indoor and forecast is not None and g.game_id in forecast.index:
        r = forecast.loc[g.game_id]; pp = float(r.precip_prob) if pd.notna(r.precip_prob) else 0.0; mm = float(r.precip) if pd.notna(r.precip) else 0.0
        rain = float(pp >= RAIN_PROB or mm >= RAIN_MM)
    return {"rain": rain, "cold": float(not indoor and temp < COLD_F), "wind_turf": max(wind - WIND_FROM, 0.0) * float(surf != "grass")}


def known_out(seasons=range(2016, 2027)) -> pd.DataFrame:
    """(season, week, pid) of every absence the card can know before a game: this week's report Out / Doubtful, or no active
    listing on the weekly roster (experiments/props_by_season._known_out's definition)."""
    rep, ro = [], []
    for s_ in seasons:
        p_ = RAW / "injuries" / f"injuries_{s_}.parquet"
        if p_.exists():
            x = pd.read_parquet(p_); col = "season_type" if "season_type" in x.columns else "game_type"
            rep.append(x[x[col] == "REG"][["season", "week", "gsis_id", "report_status"]])
        p_ = RAW / "rosters" / f"roster_weekly_{s_}.parquet"
        if p_.exists():
            x = pd.read_parquet(p_, columns=["season", "week", "gsis_id", "status", "game_type"]); ro.append(x[(x.game_type == "REG") & x.gsis_id.notna()][["season", "week", "gsis_id", "status"]])
    out = []
    if rep:
        r = pd.concat(rep).dropna(subset=["gsis_id"]).drop_duplicates(["season", "week", "gsis_id"], keep="last").rename(columns={"gsis_id": "pid"})
        out.append(r[r.report_status.isin(["Out", "Doubtful"])][["season", "week", "pid"]])
    if ro:
        r = pd.concat(ro).rename(columns={"gsis_id": "pid"}); r["act"] = r.status.eq("ACT").astype(int)
        r = r.groupby(["season", "week", "pid"]).act.max().reset_index(); out.append(r[r.act == 0][["season", "week", "pid"]])
    return (pd.concat(out) if out else pd.DataFrame(columns=["season", "week", "pid"])).drop_duplicates().assign(known_out=1)


def roster_out(roster: pd.DataFrame, season: int, week: int) -> pd.DataFrame:
    """This week's known-out from the card's roster (roster_now): not on the active roster, or listed Out / Doubtful."""
    if roster is None or not len(roster):
        return pd.DataFrame(columns=["season", "week", "pid", "known_out"])
    rs = roster.roster.fillna("Active").astype(str); rp = roster.report.fillna("").astype(str)
    m = ~rs.eq("Active") | rp.str.startswith("Out") | rp.str.startswith("Doubtful")
    return pd.DataFrame({"season": season, "week": week, "pid": roster.player_id[m].values, "known_out": 1}).drop_duplicates(["season", "week", "pid"])


def cb_ratings(dg: pd.DataFrame | None = None):
    """Every corner's rating after each of his games, 2018 on (PFR coverage): the positions.py CB recipe, coverage (yards
    saved and interceptions, in EPA) per target over targets + 150 at the league's corner targets per snap last season,
    decayed 0.99 a game. Returns (rows player_id, key = season x 100 + week, rating; the defender roles)."""
    from .positions import DEF_W, defender_roles
    dg = pd.read_parquet(OUT / "defender_games.parquet") if dg is None else dg
    roles = defender_roles(dg)
    d = dg[dg.season >= 2018].copy(); d["role"] = d.player_id.map(roles); d = d[d.role.eq("CB")].sort_values(["player_id", "season", "week"], kind="stable").reset_index(drop=True)
    d["cov_v"] = DEF_W["cov_yds"] * d.cov_yds.values + DEF_W["cov_int"] * d.cov_int.values
    t_snap = d.groupby("season").targets.sum() / d.groupby("season").plays.sum()
    S = seg_decayed(d.player_id.values, d[["cov_v", "targets"]].values, 0.99)
    ts = d.season.map(lambda s: t_snap.get(s - 1, t_snap.get(s, 0.09))).values
    R = pd.DataFrame({"player_id": d.player_id, "key": d.season.astype("int64") * 100 + d.week.astype("int64"), "rating": S[:, 0] / (S[:, 1] + 150.0) * ts})
    return R, roles


def expected_corners(known: pd.DataFrame, ratings: pd.DataFrame, roles: dict, upcoming: pd.DataFrame | None = None, since: int = 2015) -> pd.DataFrame:
    """Per (game_id, defteam): cb_r, the snap-weighted rating of this week's expected starting corners (candidates: every
    defender with a snap for the team in one of its last 3 games, at his mean snap share over them; the top 3 corners not
    known out); cb_base, the corners who played the team's last 8 games at their ratings now; cb_chg = cb_r - cb_base.
    `upcoming` (game_id, team, season, week): games to price after each team's last one with snaps (the live week)."""
    sx = pd.read_parquet(OUT / "snap_exposure.parquet", columns=["player_id", "game_id", "season", "week", "team", "position", "def_pct"])
    sx = sx[(sx.season >= since) & (sx.def_pct > 0)].copy(); sx["role"] = sx.player_id.map(roles).fillna(sx.position.map(DEF_ROLE_SNAP))
    sx = sx[sx.role.isin(["CB", "S", "LB", "EDGE", "IDL"])]
    tg = sx[["team", "game_id", "season", "week"]].drop_duplicates().sort_values(["team", "season", "week"]).reset_index(drop=True); tg["k"] = tg.groupby("team").cumcount()
    if upcoming is not None and len(upcoming):
        up = upcoming[~upcoming.game_id.isin(tg.game_id)][["team", "game_id", "season", "week"]].copy()
        up["k"] = up.team.map(tg.groupby("team").k.max() + 1); up = up.dropna(subset=["k"]).astype({"k": "int64"})
        tg = pd.concat([tg, up], ignore_index=True)
    sx = sx.merge(tg[["team", "game_id", "k"]], on=["team", "game_id"]); sx = sx[sx.role.eq("CB")]
    C = pd.concat([sx.assign(k=sx.k + o) for o in range(1, CB_LAST + 1)])
    C = C.groupby(["team", "k", "player_id", "role"]).def_pct.sum().div(float(CB_LAST)).rename("share").reset_index().merge(tg, on=["team", "k"])
    ko = known.rename(columns={"pid": "player_id"})[["player_id", "season", "week", "known_out"]].drop_duplicates(["player_id", "season", "week"])
    C = C.merge(ko, on=["player_id", "season", "week"], how="left"); C["known_out"] = C.known_out.fillna(0)
    C["key"] = C.season.astype("int64") * 100 + C.week.astype("int64")
    Rt = ratings[["player_id", "key", "rating"]].sort_values("key", kind="stable")   # a key twice (a duplicated game row): the state after both
    C = pd.merge_asof(C.sort_values("key"), Rt, on="key", by="player_id", direction="backward", allow_exact_matches=False)
    C = C.sort_values(["team", "k", "share", "player_id"], ascending=[True, True, False, True], kind="stable")   # equal shares: by player id (the study's order among ties was the sort's)
    av = C[C.known_out == 0].copy(); av["rk"] = av.groupby(["team", "k"]).cumcount(); st = av[(av.rk < CB_N) & av.rating.notna()]
    wr = st.assign(w=st.share * st.rating).groupby(["team", "k"]).agg(w=("w", "sum"), s=("share", "sum"))
    res = tg[["team", "game_id", "season", "week", "k"]].merge((wr.w / wr.s).rename("cb_r").reset_index(), on=["team", "k"], how="left")
    B = pd.concat([sx.assign(k=sx.k + o) for o in range(1, CB_BASE + 1)]).groupby(["team", "k", "player_id"]).def_pct.sum().rename("snaps").reset_index().merge(tg[["team", "k", "season", "week"]], on=["team", "k"])
    B["key"] = B.season.astype("int64") * 100 + B.week.astype("int64")
    B = pd.merge_asof(B.sort_values("key"), Rt, on="key", by="player_id", direction="backward", allow_exact_matches=False).dropna(subset=["rating"])
    b_ = B.assign(w=B.snaps * B.rating).groupby(["team", "k"]).agg(w=("w", "sum"), s=("snaps", "sum"))
    res = res.merge((b_.w / b_.s).rename("cb_base").reset_index(), on=["team", "k"], how="left")
    res["cb_chg"] = res.cb_r - res.cb_base
    return res.rename(columns={"team": "defteam"})[["game_id", "defteam", "season", "week", "cb_r", "cb_base", "cb_chg"]]


def week_inputs(wk: pd.DataFrame, season: int, week: int, roster: pd.DataFrame | None = None, backfill: bool = False) -> dict:
    """{(game_id, team): the SIT inputs for the team in this week's game}: rest_days and qb_rating from the game model's
    as-of row; rain, cold and wind_turf from the kickoff forecast in use for an unplayed game (wk: games.parquet after
    weather.apply_to_games), the recorded kickoff reading once played; opp_cb_r and opp_cb_chg, the opponent's expected
    corners with this week's known-out (the report and weekly rosters, and live the card's roster: not active, or Out /
    Doubtful). The same_out and rb_out shares come from project_game's absorb step."""
    from .weather import usable_forecast
    games = pd.read_parquet(OUT / "games.parquet"); games = games[(games.season >= 2015) & (games.game_type == "REG")]
    surf = dict(zip(games.game_id, _surface(games)))
    gi = game_inputs().drop_duplicates(["game_id", "team"]).set_index(["game_id", "team"])
    fc = None if backfill else usable_forecast()
    ko = known_out(range(season - 1, season + 1))
    if not backfill:
        ko = pd.concat([ko, roster_out(roster, season, week)]).drop_duplicates(["season", "week", "pid"])
    R, roles = cb_ratings()
    up = pd.concat([wk[["game_id", "season", "week"]].assign(team=wk.home_team.values), wk[["game_id", "season", "week"]].assign(team=wk.away_team.values)])
    E = expected_corners(ko, R, roles, upcoming=up, since=season - 1).drop_duplicates(["game_id", "defteam"]).set_index(["game_id", "defteam"])
    out = {}
    for g in wk.itertuples():
        played = pd.notna(getattr(g, "home_score", np.nan))
        for team, opp in ((g.home_team, g.away_team), (g.away_team, g.home_team)):
            row = gi.loc[(g.game_id, team)] if (g.game_id, team) in gi.index else None
            z = {"rest_days": float(row.rest_days) if row is not None else 7.0, "qb_rating": float(row.qb_rating) if row is not None and pd.notna(row.qb_rating) else None}
            if played and row is not None:
                z.update({k: float(row[k]) for k in ("rain", "cold", "wind_turf")})
            else:
                z.update(live_weather(g, fc, surf.get(g.game_id)))
            e = E.loc[(g.game_id, opp)] if (g.game_id, opp) in E.index else None
            z["opp_cb_r"] = float(e.cb_r) if e is not None and pd.notna(e.cb_r) else None
            z["opp_cb_chg"] = float(e.cb_chg) if e is not None and pd.notna(e.cb_chg) else None
            out[(g.game_id, team)] = z
    return out


def write_state(rows: list) -> None:
    """rows: dicts kind, input, pid, q (pid "" = the fallback for a player with no reading). The backtest's q for each
    player's next game, read by the live card."""
    pd.DataFrame(rows, columns=["kind", "input", "pid", "q"]).to_parquet(STATE, index=False)


def load_state() -> dict | None:
    """{(kind, input): ({pid: q}, fallback)} from the backtest's state file; None when it has not been written."""
    if not STATE.exists():
        return None
    s = pd.read_parquet(STATE); out = {}
    for (k, i), g in s.groupby(["kind", "input"]):
        fb = g[g.pid == ""].q; qq = g[(g.pid != "") & g.q.notna()]
        out[(k, i)] = (dict(zip(qq.pid, qq.q)), float(fb.iloc[0]) if len(fb) else 0.0)
    return out
