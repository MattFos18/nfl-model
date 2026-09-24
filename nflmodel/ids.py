"""Player ids (24 Sep 2026): one map from Pro Football Reference ids (snap counts, PFR advanced stats) to gsis ids
(play-by-play, rosters, injury reports, official stats), used everywhere a PFR table is joined. Built from the weekly
rosters and nflverse's players table; see pfr_ids()."""
from __future__ import annotations
import pandas as pd
from .features import RAW

norm = lambda v: "".join(ch for ch in str(v).lower() if ch.isalpha())


_PFR_IDS: dict = {}


def pfr_ids() -> dict:
    """PFR id -> gsis id. The weekly rosters first (season by season, newest last), then nflverse's players table for
    the ids the rosters lack (24 Sep 2026: the rosters carry no PFR id for any offensive lineman, so linemen were
    matched by name). Where the two disagree (six ids, e.g. two Jonah Williamses, Kwamie Lassiter and his son), the
    one whose name matches the snap counts' name for that PFR id wins."""
    if _PFR_IDS:
        return _PFR_IDS
    ids, rname = {}, {}
    for f in sorted((RAW / "rosters").glob("roster_weekly_*.parquet")):
        rr = pd.read_parquet(f, columns=["gsis_id", "pfr_id", "full_name"]).dropna(subset=["gsis_id", "pfr_id"]).drop_duplicates("pfr_id")
        ids.update(dict(zip(rr.pfr_id, rr.gsis_id))); rname.update(dict(zip(rr.gsis_id, rr.full_name)))
    pf = RAW / "players" / "players.parquet"
    if pf.exists():
        pl = pd.read_parquet(pf, columns=["gsis_id", "pfr_id", "display_name"]).dropna(subset=["gsis_id", "pfr_id"])
        pl = pl[pl.gsis_id.str.startswith("00-")].drop_duplicates("pfr_id")
        pname = dict(zip(pl.gsis_id, pl.display_name))
        conflicts = {p: g for p, g in zip(pl.pfr_id, pl.gsis_id) if p in ids and ids[p] != g}
        if conflicts:
            snap = {}
            for f in sorted((RAW / "snap_counts").glob("snap_counts_*.parquet")):
                s = pd.read_parquet(f, columns=["pfr_player_id", "player"]); s = s[s.pfr_player_id.isin(conflicts)]
                snap.update(dict(zip(s.pfr_player_id, s.player)))
            for p, g in conflicts.items():
                if p in snap and norm(pname.get(g, "")) == norm(snap[p]) != norm(rname.get(ids[p], "")):
                    ids[p] = g
        for p, g in zip(pl.pfr_id, pl.gsis_id):
            ids.setdefault(p, g)
    _PFR_IDS.update(ids)
    return _PFR_IDS


_ROSTER_NAMES: dict = {}


def roster_name_ids() -> dict:
    """(season, team, normalized name) -> gsis id from the weekly rosters, only where that name is unique on that
    team that season: the fallback for a PFR id that no table maps (a player PFR added after the players table)."""
    if _ROSTER_NAMES:
        return _ROSTER_NAMES
    from .features import TEAM_FIX
    seen: dict = {}
    for f in sorted((RAW / "rosters").glob("roster_weekly_*.parquet")):
        r = pd.read_parquet(f, columns=["season", "team", "gsis_id", "full_name"]).dropna().drop_duplicates(["gsis_id", "team"])
        r["team"] = r.team.replace(TEAM_FIX)
        for s, t, g, n in zip(r.season, r.team, r.gsis_id, r.full_name):
            seen.setdefault((int(s), t, norm(n)), set()).add(g)
    _ROSTER_NAMES.update({k: next(iter(v)) for k, v in seen.items() if len(v) == 1})
    return _ROSTER_NAMES


def map_pfr(df: pd.DataFrame, pfr: str = "pfr_player_id", name: str = "player", team: str = "team", season: str = "season") -> pd.Series:
    """The gsis id of each row of a PFR table (snap counts, PFR advanced stats): by PFR id, else by the name if it is
    unique on that team's roster that season. Never by the name alone league-wide (two Cody Whites, two Connor
    McGoverns)."""
    out = df[pfr].map(pfr_ids())
    miss = out.isna()
    if miss.any() and all(c in df.columns for c in (name, team, season)):
        from .features import TEAM_FIX
        rn = roster_name_ids(); m = df[miss]
        out.loc[miss] = [rn.get((int(s), TEAM_FIX.get(t, t), norm(n))) for s, t, n in zip(m[season], m[team], m[name])]
    return out
