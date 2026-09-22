"""Player-level offense, phase 1 of the player model.

player_games.parquet   one row per (game, team, player, role) from the play-by-play: plays and EPA as passer, rusher or
                       receiver (targets), with the player's name. 2013 on.
PlayerValues           a decayed, shrunk EPA per play for any player and role as of a week: nothing from that week or
                       later. Same shape as the QB rating (ratings.QBRatings): value = (sum w*epa + k*prior) / (sum w*plays + k).
                       The prior is replacement level for the role: the 25th percentile of per-play EPA among players
                       with 100+ plays in the seasons before the one asked for.
injury_value()         per (game, team): the value the offense loses to skill players listed Out or Doubtful on the
                       final report, in EPA per team play: sum over those players of (value - replacement) x their usage
                       share, the player's own share of his team's touches over his last eight games on any team (so a
                       star who changed teams in the offseason keeps his usage). In the model since 22 Sep 2026
                       (skill_out_value, own and opponent); the QB is excluded because qb_out already covers it.
team_players()         every skill player valued as of the coming week with this week's injury status, for the page.

Usage: python -m nflmodel.players            builds player_games.parquet and player_injury.parquet
"""
from __future__ import annotations
import numpy as np, pandas as pd
from pathlib import Path
from .features import RAW, OUT, TEAM_FIX

ROLES = {"passer": ("passer_player_id", "passer_player_name", "qb_dropback"), "rusher": ("rusher_player_id", "rusher_player_name", "rush_attempt"),
         "receiver": ("receiver_player_id", "receiver_player_name", "pass_attempt")}
SKILL = {"rusher", "receiver"}
DEFAULT = {"decay": 0.985, "k": 80.0, "usage_games": 8}
PCOLS = ["game_id", "season", "week", "season_type", "posteam", "epa", "qb_epa", "qb_dropback", "rush_attempt", "pass_attempt", "play_type"] + [c for r in ROLES.values() for c in r[:2]]


def load(seasons) -> pd.DataFrame:
    frames = []
    for s in seasons:
        f = RAW / "pbp" / f"play_by_play_{s}.parquet"
        if f.exists():
            import pyarrow.parquet as pq
            have = set(pq.ParquetFile(f).schema.names)
            frames.append(pd.read_parquet(f, columns=[c for c in PCOLS if c in have]))
    p = pd.concat(frames, ignore_index=True)
    p["posteam"] = p.posteam.replace(TEAM_FIX)
    return p[p.posteam.notna() & p.play_type.isin(["pass", "run"])]


def player_box(p: pd.DataFrame) -> pd.DataFrame:
    out = []
    for role, (idc, namec, flag) in ROLES.items():
        d = p[(pd.to_numeric(p[flag], errors="coerce") == 1) & p[idc].notna()].copy()
        d["epa"] = pd.to_numeric(d.qb_epa if role == "passer" else d.epa, errors="coerce")
        g = d.groupby(["game_id", "season", "week", "posteam", idc]).agg(plays=("epa", "size"), epa=("epa", "sum"), name=(namec, "first")).reset_index()
        g = g.rename(columns={"posteam": "team", idc: "player_id"}); g["role"] = role
        out.append(g)
    return pd.concat(out, ignore_index=True).sort_values(["season", "week", "game_id", "team", "role"]).reset_index(drop=True)


class PlayerValues:
    def __init__(self, pg: pd.DataFrame, decay=DEFAULT["decay"], k=DEFAULT["k"]):
        self.pg = pg.sort_values(["season", "week"]); self.decay, self.k = decay, k
        self._cache, self._prior = {}, {}
        self.by = {key: g for key, g in self.pg.groupby(["player_id", "role"])}

    def prior(self, role: str, season: int) -> float:
        key = (role, season)
        if key not in self._prior:
            h = self.pg[(self.pg.role == role) & (self.pg.season < season)]
            tot = h.groupby("player_id").agg(plays=("plays", "sum"), epa=("epa", "sum"))
            tot = tot[tot.plays >= 100]
            self._prior[key] = float(np.percentile(tot.epa / tot.plays, 25)) if len(tot) else 0.0
        return self._prior[key]

    def value(self, pid: str, role: str, season: int, week: int) -> tuple[float, float]:
        """(value, weighted plays) as of (season, week)."""
        key = (pid, role, season, week)
        if key in self._cache:
            return self._cache[key]
        g = self.by.get((pid, role))
        pr = self.prior(role, season)
        if g is None:
            r = (pr, 0.0)
        else:
            h = g[(g.season < season) | ((g.season == season) & (g.week < week))]
            if len(h) == 0:
                r = (pr, 0.0)
            else:
                w = self.decay ** np.arange(len(h))[::-1]
                n = float((h.plays.values * w).sum()); e = float((h.epa.values * w).sum())
                r = ((e + self.k * pr) / (n + self.k), n)
        self._cache[key] = r
        return r


def _usage_frames(pg: pd.DataFrame):
    """Skill rows with each game's team touch count attached, indexed for the usage lookups."""
    skill = pg[pg.role.isin(SKILL)]
    team_touch = skill.groupby(["game_id", "season", "week", "team"]).plays.sum().rename("team_plays").reset_index()
    skill = skill.merge(team_touch, on=["game_id", "season", "week", "team"]).sort_values(["season", "week"])
    by_player = {pid: g for pid, g in skill.groupby("player_id")}
    by_team = {t: g for t, g in skill.groupby("team")}
    return skill, by_player, by_team


def player_usage(by_player: dict, pid: str, season: int, week: int, n_games: int) -> tuple[float, float, int]:
    """The player's share of his team's touches over his own last n games before (season, week), on any team: a
    star traded in the offseason keeps the usage he had, instead of counting as nobody because his new team has
    not seen him yet. Returns (share, touches per game, games)."""
    g = by_player.get(pid)
    if g is None:
        return 0.0, 0.0, 0
    h = g[(g.season < season) | ((g.season == season) & (g.week < week))]
    ids = h.game_id.drop_duplicates().tail(n_games)
    h = h[h.game_id.isin(ids)]
    if len(h) == 0:
        return 0.0, 0.0, 0
    tot = float(h.groupby("game_id").team_plays.first().sum())
    return (float(h.plays.sum()) / tot if tot else 0.0), float(h.plays.sum()) / len(ids), int(len(ids))


def player_value_out(pv: PlayerValues, by_player: dict, pid: str, season: int, week: int, n_games: int) -> dict:
    """Value lost if this player is out: EPA per team play = sum over roles of (value - replacement) x role share."""
    g = by_player.get(pid)
    share, per_game, n = player_usage(by_player, pid, season, week, n_games)
    if g is None or n == 0:
        return {"value": 0.0, "share": 0.0, "per_game": 0.0, "games": 0, "epa_play": 0.0, "name": None}
    h = g[(g.season < season) | ((g.season == season) & (g.week < week))]
    ids = h.game_id.drop_duplicates().tail(n_games); h = h[h.game_id.isin(ids)]
    tot = float(h.groupby("game_id").team_plays.first().sum()) or 1.0
    val, epa = 0.0, 0.0
    for role in SKILL:
        hr = h[h.role == role]
        if len(hr) == 0:
            continue
        vv, _ = pv.value(pid, role, season, week)
        rs = float(hr.plays.sum()) / tot
        val += (vv - pv.prior(role, season)) * rs
        epa += vv * rs
    return {"value": val, "share": share, "per_game": per_game, "games": n, "epa_play": epa / share if share else 0.0, "name": str(h.name.iloc[-1])}


NOT_AVAILABLE = {"RES", "PUP", "SUS", "EXE", "NON", "RET"}   # roster statuses known before kickoff that mean the player cannot play: reserve/IR, PUP, suspended, exempt, non-football injury, retired
ROSTER_LABEL = {"RES": "IR", "PUP": "PUP", "SUS": "Suspended", "EXE": "Exempt", "NON": "NFI", "RET": "Retired"}


def load_rosters(seasons) -> pd.DataFrame:
    """Weekly rosters (nflverse): a row per player, team and week with his roster status that week."""
    fs = [RAW / "rosters" / f"roster_weekly_{s}.parquet" for s in seasons]
    fs = [f for f in fs if f.exists()]
    if not fs:
        return pd.DataFrame(columns=["season", "week", "team", "gsis_id", "status"])
    r = pd.concat([pd.read_parquet(f, columns=["season", "week", "team", "gsis_id", "status", "game_type"]) for f in fs], ignore_index=True)
    r["team"] = r.team.replace({"OAK": "LV", "SD": "LAC", "STL": "LA"})
    return r[r.gsis_id.notna()]


def unavailable_by_week(seasons) -> dict:
    """(season, week, team) -> set of player ids on IR, PUP, suspended or otherwise off the active roster that week.
    A player on IR is not on the weekly injury report, so without this the model would count him as available."""
    r = load_rosters(seasons)
    r = r[r.status.isin(NOT_AVAILABLE)]
    return {k: set(g.gsis_id) for k, g in r.groupby(["season", "week", "team"])}


def load_injuries(seasons) -> pd.DataFrame:
    inj = pd.concat([pd.read_parquet(RAW / "injuries" / f"injuries_{s}.parquet") for s in seasons if (RAW / "injuries" / f"injuries_{s}.parquet").exists()], ignore_index=True)
    inj["team"] = inj.team.replace({"OAK": "LV", "SD": "LAC", "STL": "LA"})
    return inj


def injury_value(games: pd.DataFrame, pg: pd.DataFrame, seasons=range(2013, 2027), p=DEFAULT) -> pd.DataFrame:
    inj = load_injuries(seasons)
    inj = inj[inj.report_status.isin(["Out", "Doubtful"]) & (inj.position != "QB")]
    out_by = {k: set(g.gsis_id.dropna()) for k, g in inj.groupby(["season", "week", "team"])}
    for k, ids in unavailable_by_week(seasons).items():      # IR and the like: not on the injury report, still out
        out_by[k] = out_by.get(k, set()) | ids
    pv = PlayerValues(pg, p["decay"], p["k"])
    _, by_player, _ = _usage_frames(pg)
    names = {r.gsis_id: r.full_name for r in load_injuries(seasons).drop_duplicates("gsis_id").itertuples() if isinstance(r.full_name, str)}
    for s_ in seasons:
        rf = RAW / "rosters" / f"roster_weekly_{s_}.parquet"
        if rf.exists():
            rr = pd.read_parquet(rf, columns=["gsis_id", "full_name"]).dropna().drop_duplicates("gsis_id")
            names.update(dict(zip(rr.gsis_id, rr.full_name)))
    rows = []
    long = pd.concat([games[["game_id", "season", "week", "home_team"]].rename(columns={"home_team": "team"}), games[["game_id", "season", "week", "away_team"]].rename(columns={"away_team": "team"})])
    long = long[long.season.isin(seasons)]
    for r in long.itertuples():
        outs = out_by.get((r.season, r.week, r.team), set())
        val, share, n, detail = 0.0, 0.0, 0, []
        for pid in outs:
            d = player_value_out(pv, by_player, pid, r.season, r.week, p["usage_games"])
            if d["games"] == 0:
                continue
            val += d["value"]; share += d["share"]; n += 1
            detail.append(f"{names.get(pid, d['name'])}|{d['value']:.4f}|{d['share']:.3f}")
        rows.append({"game_id": r.game_id, "team": r.team, "skill_out_value": val, "skill_out_share": share, "n_skill_out": n, "skill_out_detail": ";".join(detail)})
    return pd.DataFrame(rows)


def team_players(games: pd.DataFrame, pg: pd.DataFrame, season: int, week: int, p=DEFAULT) -> pd.DataFrame:
    """Every skill player with a touch in his last eight games, valued as of (season, week), with this week's injury
    status: what the page shows under Team -> Players and what the card lists when someone is out."""
    pv = PlayerValues(pg, p["decay"], p["k"])
    skill, by_player, by_team = _usage_frames(pg)
    inj = load_injuries([season]); inj = inj[(inj.season == season) & (inj.week == week)]
    status = {(r.team, r.gsis_id): (r.report_status if isinstance(r.report_status, str) else (r.practice_status if isinstance(r.practice_status, str) else "")) for r in inj.itertuples()}
    ros = load_rosters([season]); ros = ros[(ros.week == week) & ros.status.isin(NOT_AVAILABLE)]
    for r in ros.itertuples():                                # roster status wins: IR is definite
        status[(r.team, r.gsis_id)] = ROSTER_LABEL.get(r.status, r.status)
    ref = load_injuries(range(season - 2, season + 1)).drop_duplicates("gsis_id")
    pos = {r.gsis_id: r.position for r in ref.itertuples()}
    full = {r.gsis_id: r.full_name for r in ref.itertuples() if isinstance(r.full_name, str)}
    rf = RAW / "rosters" / f"roster_weekly_{season}.parquet"
    if rf.exists():
        rr = pd.read_parquet(rf, columns=["gsis_id", "full_name", "position"]).dropna(subset=["gsis_id"]).drop_duplicates("gsis_id")
        full.update({r.gsis_id: r.full_name for r in rr.itertuples() if isinstance(r.full_name, str)})
        for r in rr.itertuples():
            pos.setdefault(r.gsis_id, r.position)
    passers = set(pg[(pg.role == "passer") & (pg.season >= season - 1)].player_id)
    rows = []
    for t, g in by_team.items():
        h = g[(g.season < season) | ((g.season == season) & (g.week < week))]
        ids = h.game_id.drop_duplicates().tail(p["usage_games"])
        for pid in h[h.game_id.isin(ids)].player_id.unique():
            d = player_value_out(pv, by_player, pid, season, week, p["usage_games"])
            last_team = by_player[pid].iloc[-1].team
            if last_team != t or pos.get(pid) == "QB" or (pid in passers and pos.get(pid, "") == ""):
                continue    # he has moved on, or he is the quarterback (qb_out covers him)
            rows.append({"team": t, "player_id": pid, "name": full.get(pid, d["name"]), "position": pos.get(pid, ""), "games": d["games"], "touches_per_game": round(d["per_game"], 1),
                         "share": round(d["share"], 3), "epa_per_touch": round(d["epa_play"], 3), "value_above_replacement": round(d["value"], 4),
                         "status": status.get((t, pid), "")})
    return pd.DataFrame(rows).sort_values(["team", "value_above_replacement"], ascending=[True, False])


DEPTH_ORDER = ["QB", "RB", "FB", "WR", "TE", "LT", "LG", "C", "RG", "RT", "T", "G", "OL",
               "DE", "DT", "NT", "DL", "EDGE", "OLB", "ILB", "MLB", "LB", "CB", "NB", "S", "FS", "SS", "DB", "K", "P", "LS", "KR", "PR"]


def team_roster(games: pd.DataFrame, season: int, week: int) -> pd.DataFrame:
    """Every player on each team's weekly roster for (season, week) with: roster status (active, IR, PUP, practice
    squad...), depth chart slot and rank from the latest chart, this week's injury report (status, practice, injury),
    last game's snap share, and the skill value when he has one. What the page shows under Team -> Roster."""
    rf = RAW / "rosters" / f"roster_weekly_{season}.parquet"
    if not rf.exists():
        return pd.DataFrame()
    ros = pd.read_parquet(rf, columns=["season", "week", "team", "gsis_id", "full_name", "position", "status", "jersey_number", "years_exp"])
    ros["team"] = ros.team.replace({"OAK": "LV", "SD": "LAC", "STL": "LA"})
    wk = ros[ros.week == week] if (ros.week == week).any() else ros[ros.week == ros.week.max()]
    wk = wk.dropna(subset=["gsis_id"]).drop_duplicates(["team", "gsis_id"]).copy()
    # depth chart: the latest chart per team
    df_ = RAW / "depth_charts" / f"depth_charts_{season}.parquet"
    depth = {}
    if df_.exists():
        d = pd.read_parquet(df_, columns=["dt", "team", "gsis_id", "pos_grp", "pos_abb", "pos_rank"])
        d["team"] = d.team.replace({"OAK": "LV", "SD": "LAC", "STL": "LA"})
        d = d[d.dt == d.groupby("team").dt.transform("max")]
        d = d[d.pos_grp != "Special Teams"].sort_values("pos_rank").drop_duplicates(["team", "gsis_id"])
        depth = {(r.team, r.gsis_id): (r.pos_abb, int(r.pos_rank), "Defense" if str(r.pos_grp).endswith("D") else "Offense") for r in d.itertuples()}
    inj = load_injuries([season]); inj = inj[(inj.season == season) & (inj.week == week)]
    injd = {(r.team, r.gsis_id): (r.report_status if isinstance(r.report_status, str) else "", r.practice_status if isinstance(r.practice_status, str) else "",
                                  r.report_primary_injury if isinstance(r.report_primary_injury, str) else (r.practice_primary_injury if isinstance(r.practice_primary_injury, str) else "")) for r in inj.itertuples()}
    # last game's snap share, by name (snap counts carry no gsis id)
    sf = RAW / "snap_counts" / f"snap_counts_{season}.parquet"
    snap = {}
    if sf.exists():
        sn = pd.read_parquet(sf); sn["team"] = sn.team.replace({"OAK": "LV", "SD": "LAC", "STL": "LA"})
        sn = sn[sn.week == sn.groupby("team").week.transform("max")]
        norm = lambda v: "".join(ch for ch in str(v).lower() if ch.isalpha())
        snap = {(r.team, norm(r.player)): (float(r.offense_pct), float(r.defense_pct), float(r.st_pct), int(r.week)) for r in sn.itertuples()}
    vf = OUT / "player_values.parquet"
    vals = pd.read_parquet(vf).set_index(["team", "player_id"]) if vf.exists() else None
    norm = lambda v: "".join(ch for ch in str(v).lower() if ch.isalpha())
    rows = []
    for r in wk.itertuples():
        dp = depth.get((r.team, r.gsis_id), (None, None, None)); ij = injd.get((r.team, r.gsis_id), ("", "", "")); sp = snap.get((r.team, norm(r.full_name)))
        v = vals.loc[(r.team, r.gsis_id)] if vals is not None and (r.team, r.gsis_id) in vals.index else None
        rows.append({"team": r.team, "player_id": r.gsis_id, "name": r.full_name, "position": r.position, "number": r.jersey_number, "exp": r.years_exp,
                     "roster": ROSTER_LABEL.get(r.status, {"ACT": "Active", "DEV": "Practice squad", "INA": "Inactive", "CUT": "Cut"}.get(r.status, r.status)),
                     "unit": dp[2], "slot": dp[0], "depth": dp[1], "report": ij[0], "practice": ij[1], "injury": ij[2],
                     "off_pct": sp[0] if sp else None, "def_pct": sp[1] if sp else None, "st_pct": sp[2] if sp else None,
                     "value": float(v.value_above_replacement) if v is not None else None, "epa_per_touch": float(v.epa_per_touch) if v is not None else None, "share": float(v.share) if v is not None else None})
    out = pd.DataFrame(rows)
    out["order"] = out.slot.map({p: i for i, p in enumerate(DEPTH_ORDER)}).fillna(99)
    return out.sort_values(["team", "unit", "order", "depth", "name"], na_position="last").drop(columns=["order"])


def player_history(pg: pd.DataFrame) -> pd.DataFrame:
    """One row per player, season, team and role: games, plays, EPA per play. The Players tab's history, which follows
    a player across teams."""
    h = pg.groupby(["player_id", "season", "team", "role"]).agg(games=("game_id", "nunique"), plays=("plays", "sum"), epa=("epa", "sum"), name=("name", "last")).reset_index()
    h["epa_play"] = (h.epa / h.plays).round(3)
    return h.sort_values(["player_id", "season", "role"])


if __name__ == "__main__":
    games = pd.read_parquet(OUT / "games.parquet")
    pg = player_box(load(range(2013, 2027)))
    pg.to_parquet(OUT / "player_games.parquet", index=False)
    print("player_games", pg.shape, pg.player_id.nunique(), "players")
    iv = injury_value(games, pg)
    iv.to_parquet(OUT / "player_injury.parquet", index=False)
    from .lines import current_week
    cs, cw = current_week(games)
    tp = team_players(games, pg, cs, cw)
    tp.to_parquet(OUT / "player_values.parquet", index=False)
    print("player_values", tp.shape, "as of", cs, cw)
    ro = team_roster(games, cs, cw)
    ro.to_parquet(OUT / "roster_now.parquet", index=False)
    player_history(pg).to_parquet(OUT / "player_history.parquet", index=False)
    print("roster_now", ro.shape)
    print("player_injury", iv.shape, "rows with a skill player out:", int((iv.n_skill_out > 0).sum()))
    print(iv[iv.n_skill_out > 0].describe().to_string())
