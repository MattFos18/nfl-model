"""Historical player prop lines from The Odds API, for the props backtest against the market (23 Sep 2026).

The Odds API keeps player-prop snapshots from 3 May 2023 at five-minute intervals, on paid plans only. This pulls,
for every game from the 2023 season on, the closing snapshot (one hour before kickoff) of five markets: receiving
yards, receptions, rushing yards, passing yards, anytime touchdown, from every US book. One historical events call
per kickoff slot (1 credit) and one historical event-odds call per game (markets x regions credits; The Odds API
documents 10x that for the featured historical endpoint, so the budget below assumes the worse case).
Rows go to data/lines/props_history.csv in the props_log schema plus snapshot_ts; raw responses under
data/lines/raw/history/. Re-running skips games already pulled, so a stopped run can resume.

Usage: ODDS_API_KEY=... python -m nflmodel.props_history --seasons 2023 2024 2025 [--max-credits 18000] [--dry-run]
The GitHub Actions workflow props_history.yml runs it with the repo secret."""
from __future__ import annotations
import argparse, datetime as dt, json, os, time
import pandas as pd, requests
from .lines import LN, OUT, team_from_name
from .props_lines import MARKETS, SCHEMA, parse_event

API = "https://api.the-odds-api.com/v4/historical/sports/americanfootball_nfl"
HIST = LN / "props_history.csv"


def load() -> pd.DataFrame:
    return pd.read_csv(HIST) if HIST.exists() else pd.DataFrame(columns=SCHEMA + ["snapshot_ts"])


def slots(games: pd.DataFrame, seasons: list[int]) -> pd.DataFrame:
    """One row per distinct kickoff time (UTC) with the games in it: the snapshot is taken one hour before."""
    g = games[games.season.isin(seasons) & games.home_score.notna() & games.kickoff_et.notna()].copy()
    g["kick_utc"] = g.kickoff_et.dt.tz_localize("America/New_York", nonexistent="shift_forward", ambiguous="NaT").dt.tz_convert("UTC").dt.tz_localize(None)
    return g


def _get(url: str, key: str, params: dict, tries: int = 3) -> tuple[dict | list, int]:
    for i in range(tries):
        r = requests.get(url, timeout=60, params=dict(params, apiKey=key))
        if r.status_code == 429:
            time.sleep(5 * (i + 1)); continue
        r.raise_for_status()
        return r.json(), int(r.headers.get("x-requests-last", "0") or 0)
    r.raise_for_status()


def run(seasons: list[int], max_credits: int = 18000, dry_run: bool = False) -> pd.DataFrame:
    key = os.environ.get("ODDS_API_KEY", "").strip()
    if not key and not dry_run:
        raise SystemExit("ODDS_API_KEY is not set")
    games = pd.read_parquet(OUT / "games.parquet")
    g = slots(games, seasons); have = load(); done = set(have.game_id.dropna()) if len(have) else set()
    todo = g[~g.game_id.isin(done)]
    print(f"{len(todo)} games to pull across {todo.kick_utc.nunique()} kickoff slots ({len(done)} already pulled)", flush=True)
    if dry_run:
        return have
    (LN / "raw" / "history").mkdir(parents=True, exist_ok=True)
    spent, rows = 0, []
    for kick, grp in todo.groupby("kick_utc"):
        snap = (kick - pd.Timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
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
            j, c = _get(f"{API}/events/{e['id']}/odds", key, {"date": snap, "regions": "us", "markets": ",".join(MARKETS), "oddsFormat": "american"}); spent += c
            data = j.get("data", j) if isinstance(j, dict) else j
            (LN / "raw" / "history" / f"{gm.game_id}.json").write_text(json.dumps(j)[:5_000_000])
            ts = (j.get("timestamp") if isinstance(j, dict) else None) or snap
            for r in parse_event(data, int(gm.season), int(gm.week), snap):
                r["game_id"] = gm.game_id; r["snapshot_ts"] = ts; rows.append(r)
        print(f"{snap}: {len(grp)} games, {spent} credits so far", flush=True)
        if rows:
            out = pd.concat([load(), pd.DataFrame(rows).reindex(columns=SCHEMA + ["snapshot_ts"])], ignore_index=True); out.to_csv(HIST, index=False); rows = []
        if spent >= max_credits:
            print("credit budget reached; rerun to resume", flush=True); break
    return load()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--seasons", type=int, nargs="+", default=[2023, 2024, 2025]); ap.add_argument("--max-credits", type=int, default=18000); ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(); d = run(a.seasons, a.max_credits, a.dry_run); print(len(d), "rows in", HIST)
