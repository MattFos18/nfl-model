"""Historical player prop lines from The Odds API, for the props backtest against the market (23 Sep 2026).

The Odds API keeps player-prop snapshots from 3 May 2023 at five-minute intervals, on paid plans only. This pulls,
for every game from the 2023 season on, a snapshot of five markets: receiving yards, receptions, rushing yards,
passing yards, anytime touchdown, from every US book. Two snapshots are offered: "close" (one hour before kickoff)
and "open" (Tuesday 16:00 UTC of the game's week, the earliest most books have the full slate up). One historical
events call per kickoff slot (1 credit) and one historical event-odds call per game, which the docs price at
10 x markets x regions = 50 credits with five markets and one region. 887 games (2023 to Week 2 of 2026) x 50 +
425 slots = about 44,800 credits per snapshot: the 100K plan ($59, one month) covers the close and the open both.
--probe pulls one slot and one game and prints what it cost and what remains, so the plan is proven before the
run. Rows go to data/lines/props_history.csv in the props_log schema plus snapshot and snapshot_ts; raw responses
under data/lines/raw/history/. Re-running skips games already pulled for that snapshot, so a stopped run resumes.

Usage: ODDS_API_KEY=... python -m nflmodel.props_history --seasons 2023 2024 2025 2026 [--snapshot close|open]
       [--max-credits 90000] [--probe] [--dry-run]
The GitHub Actions workflow props_history.yml runs it with the repo secret."""
from __future__ import annotations
import argparse, datetime as dt, json, os, time
import pandas as pd, requests
from .lines import LN, OUT, team_from_name
from .props_lines import MARKETS, SCHEMA, parse_event

API = "https://api.the-odds-api.com/v4/historical/sports/americanfootball_nfl"
HIST = LN / "props_history.csv"


COLS = SCHEMA + ["snapshot", "snapshot_ts"]


def load() -> pd.DataFrame:
    return pd.read_csv(HIST).reindex(columns=COLS) if HIST.exists() else pd.DataFrame(columns=COLS)


def slots(games: pd.DataFrame, seasons: list[int], snapshot: str = "close") -> pd.DataFrame:
    """Played games of the seasons with the snapshot time to query: close = one hour before kickoff; open = the Tuesday
    of the game's week at 16:00 UTC (the Thursday game included: its Tuesday is the same one)."""
    g = games[games.season.isin(seasons) & games.home_score.notna() & games.kickoff_et.notna()].copy()
    g["kick_utc"] = g.kickoff_et.dt.tz_localize("America/New_York", nonexistent="shift_forward", ambiguous="NaT").dt.tz_convert("UTC").dt.tz_localize(None)
    if snapshot == "close":
        g["snap_utc"] = g.kick_utc - pd.Timedelta(hours=1)
    else:
        wk_tue = g.kickoff_et.dt.normalize() - pd.to_timedelta((g.kickoff_et.dt.weekday - 1) % 7, unit="D")   # the Tuesday on or before kickoff, Eastern date (Monday night's is six days back)
        g["snap_utc"] = wk_tue + pd.Timedelta(hours=16)
        g.loc[g.snap_utc >= g.kick_utc - pd.Timedelta(hours=1), "snap_utc"] = g.kick_utc - pd.Timedelta(hours=1)
    return g


def _get(url: str, key: str, params: dict, tries: int = 3, with_remaining: bool = False):
    for i in range(tries):
        r = requests.get(url, timeout=60, params=dict(params, apiKey=key))
        if r.status_code == 429:
            time.sleep(5 * (i + 1)); continue
        r.raise_for_status()
        cost = int(float(r.headers.get("x-requests-last", "0") or 0)); rem = r.headers.get("x-requests-remaining")
        return (r.json(), cost, rem) if with_remaining else (r.json(), cost)
    r.raise_for_status()


def run(seasons: list[int], max_credits: int = 90000, dry_run: bool = False, snapshot: str = "close", probe: bool = False) -> pd.DataFrame:
    key = os.environ.get("ODDS_API_KEY", "").strip()
    if not key and not dry_run:
        raise SystemExit("ODDS_API_KEY is not set")
    games = pd.read_parquet(OUT / "games.parquet")
    g = slots(games, seasons, snapshot); have = load(); done = set(have[have.snapshot == snapshot].game_id.dropna()) if len(have) else set()
    todo = g[~g.game_id.isin(done)]
    print(f"{snapshot}: {len(todo)} games to pull across {todo.snap_utc.nunique()} snapshot slots ({len(done)} already pulled); about {len(todo) * 50 + todo.snap_utc.nunique()} credits", flush=True)
    if dry_run:
        return have
    (LN / "raw" / "history").mkdir(parents=True, exist_ok=True)
    spent, rows, remaining = 0, [], None
    for kick, grp in todo.groupby("snap_utc"):
        snap = kick.strftime("%Y-%m-%dT%H:%M:%SZ")
        if probe:
            grp = grp.head(1)
        ev, c = _get(f"{API}/events", key, {"date": snap}); spent += c
        events = ev.get("data", ev) if isinstance(ev, dict) else ev
        by_pair = {}
        for e in events:
            h, a = team_from_name(e.get("home_team")), team_from_name(e.get("away_team"))
            if h and a: by_pair[(h, a)] = e
        for gm in grp.itertuples():
            e = by_pair.get((gm.home_team, gm.away_team))
            if e is None:
                print("no event for", gm.game_id, "at", snap, flush=True); continue
            j, c, remaining = _get(f"{API}/events/{e['id']}/odds", key, {"date": snap, "regions": "us", "markets": ",".join(MARKETS), "oddsFormat": "american"}, with_remaining=True); spent += c
            data = j.get("data", j) if isinstance(j, dict) else j
            (LN / "raw" / "history" / f"{gm.game_id}_{snapshot}.json").write_text(json.dumps(j)[:5_000_000])
            ts = (j.get("timestamp") if isinstance(j, dict) else None) or snap
            n0 = len(rows)
            for r in parse_event(data, int(gm.season), int(gm.week), snap):
                r["game_id"] = gm.game_id; r["snapshot"] = snapshot; r["snapshot_ts"] = ts; rows.append(r)
            if probe:
                print(f"PROBE {gm.game_id} at {snap}: {len(rows) - n0} rows, this call cost {c} credits, {remaining} remaining", flush=True)
        print(f"{snap}: {len(grp)} games, {spent} credits so far, {remaining} remaining", flush=True)
        if rows:
            out = pd.concat([load(), pd.DataFrame(rows).reindex(columns=COLS)], ignore_index=True); out.to_csv(HIST, index=False); rows = []
        if probe:
            break
        if spent >= max_credits:
            print("credit budget reached; rerun to resume", flush=True); break
    return load()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--seasons", type=int, nargs="+", default=[2023, 2024, 2025, 2026]); ap.add_argument("--max-credits", type=int, default=90000); ap.add_argument("--dry-run", action="store_true"); ap.add_argument("--snapshot", choices=["close", "open"], default="close"); ap.add_argument("--probe", action="store_true")
    a = ap.parse_args(); d = run(a.seasons, a.max_credits, a.dry_run, a.snapshot, a.probe); print(len(d), "rows in", HIST)
