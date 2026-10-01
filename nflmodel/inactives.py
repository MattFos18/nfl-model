"""Game-day inactives, logged (1 Oct 2026, Matt: "why can't the model factor in later inactives"). Teams name their
inactives 90 minutes before kickoff; ESPN's game roster (core API, competitors/<team>/roster) marks them didNotPlay.
Before the list is out the same flag already sits on some players (on the Thursday of week 4 it marked Joey Porter Jr.,
who practiced in full), so the flag is logged, not priced, until a few game days show when it turns into the official list.
Every line watch in the six hours before a kickoff, both teams' game rosters; a row only when a player's flag changes.
Writes data/lines/inactives_log.csv (ts, game_id, espn_event, team, espn_player_id, name, did_not_play, starter).

    python -m nflmodel.inactives
"""
from __future__ import annotations
import datetime as dt
import pandas as pd, requests
from .features import OUT, ROOT

LN = ROOT / "data" / "lines"; F = LN / "inactives_log.csv"
CORE = "https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/events/{e}/competitions/{e}/competitors/{c}/roster"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"}
HOURS_BEFORE = 6
ABBR = {"WSH": "WAS", "JAC": "JAX", "LAR": "LA"}
KEY, COLS = ["espn_event", "team", "espn_player_id"], ["did_not_play", "starter"]


def run() -> int:
    """Log the game rosters of every game kicking off within HOURS_BEFORE hours; returns rows added."""
    from .lines import current_week
    from . import results as RS
    g = pd.read_parquet(OUT / "games.parquet"); season, week = current_week(g)
    now = pd.Timestamp.now(tz="America/New_York").tz_localize(None)
    soon = g[(g.season == season) & (g.week == week) & g.home_score.isna() & g.kickoff_et.notna()].copy()
    soon["ko"] = pd.to_datetime(soon.kickoff_et)
    soon = soon[(soon.ko > now) & (soon.ko <= now + pd.Timedelta(hours=HOURS_BEFORE))]
    if not len(soon):
        return 0
    j = RS.saved(season, week) or RS.fetch(season, week)
    ts = dt.datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%SZ"); rows = []
    for ev in (j or {}).get("events", []):
        comp = (ev.get("competitions") or [{}])[0]
        teams = {c.get("homeAway"): (ABBR.get(c["team"]["abbreviation"], c["team"]["abbreviation"]), c.get("id")) for c in comp.get("competitors", [])}
        if "home" not in teams or "away" not in teams:
            continue
        m = soon[(soon.home_team == teams["home"][0]) & (soon.away_team == teams["away"][0])]
        if not len(m):
            continue
        for ab, cid in teams.values():
            r = requests.get(CORE.format(e=ev["id"], c=cid), headers=UA, timeout=20)
            if not r.ok:
                continue
            for x in r.json().get("entries", []):
                rows.append({"ts": ts, "game_id": m.game_id.iloc[0], "espn_event": str(ev["id"]), "team": ab, "espn_player_id": str(x.get("playerId")),
                             "name": x.get("displayName"), "did_not_play": bool(x.get("didNotPlay")), "starter": bool(x.get("starter"))})
    df = pd.DataFrame(rows)
    if not len(df):
        return 0
    if F.exists():
        old = pd.read_csv(F, dtype={"espn_event": str, "espn_player_id": str})
        last = old.sort_values("ts").drop_duplicates(KEY, keep="last").set_index(KEY)[COLS]
        prev = last.reindex(df.set_index(KEY).index)
        same = (df.set_index(KEY)[COLS] == prev).all(axis=1).values
        df = df[~same]
    if len(df):
        LN.mkdir(parents=True, exist_ok=True); df.to_csv(F, mode="a", header=not F.exists(), index=False)
    return len(df)


if __name__ == "__main__":
    print(run())
