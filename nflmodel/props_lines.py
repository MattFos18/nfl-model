"""Player prop lines from The Odds API, logged for the props record (23 Sep 2026).

Free tier: 500 usage credits a month. Player props come one game at a time from the event-odds endpoint, and each
call costs (markets x regions) credits, so a full slate of 16 games at five markets is 80 credits. The budget is
spent as: one pull on Thursday 20:00 UTC for the games kicking off within 30 hours (the Thursday game: 5 credits),
one pull on Sunday 14:00 UTC for the rest of the week (Sunday and Monday games, near their closing lines: ~75),
about 345 a month, beside the game-line pull every eight hours (~90). PROPS_EVERY_RUN=1 forces a pull.
Markets: receiving yards, receptions, rushing yards, passing yards, anytime touchdown. Every row of every book is
appended to data/lines/props_log.csv; the raw response is saved under data/lines/raw/. Nothing here is bet: the
lines are what the projections are graded against (nflmodel/props.py) and what the cards show beside them."""
from __future__ import annotations
import datetime as dt, os, re
import pandas as pd, requests
from .lines import LN, OUT, _save_raw, team_from_name, current_week

MARKETS = {"player_reception_yds": "rec_yards", "player_receptions": "rec_catches", "player_rush_yds": "rush_yards", "player_pass_yds": "pass_yards", "player_anytime_td": "anytime_td"}
SCHEMA = ["ts", "season", "week", "game_id", "home", "away", "start", "book", "market", "stat", "player", "line", "over_price", "under_price"]
API = "https://api.the-odds-api.com/v4/sports/americanfootball_nfl"


def norm_name(s: str) -> str:
    """'A.J. Brown Jr.' -> 'aj brown': lower case, letters only, suffixes dropped, so book names meet roster names."""
    if not isinstance(s, str):
        return ""
    s = re.sub(r"[^a-z ]", "", s.lower().replace(".", "").replace("-", " ").replace("'", ""))
    parts = [p for p in s.split() if p not in ("jr", "sr", "ii", "iii", "iv", "v")]
    return " ".join(parts)


def parse_event(ev: dict, season: int, week: int, ts: str) -> list[dict]:
    home, away = team_from_name(ev.get("home_team")), team_from_name(ev.get("away_team"))
    rows = {}
    if not home or not away:
        return []
    for bk in ev.get("bookmakers", []):
        for m in bk.get("markets", []):
            stat = MARKETS.get(m.get("key"))
            if not stat:
                continue
            for oc in m.get("outcomes", []):
                player = oc.get("description") or ""
                k = (bk.get("key"), m["key"], player)
                r = rows.setdefault(k, {"ts": ts, "season": season, "week": week, "game_id": None, "home": home, "away": away, "start": ev.get("commence_time"), "book": bk.get("key"), "market": m["key"], "stat": stat, "player": player, "line": None, "over_price": None, "under_price": None})
                side = str(oc.get("name", "")).lower()
                if side in ("over", "yes"):
                    r["over_price"] = oc.get("price"); r["line"] = oc.get("point", r["line"])
                elif side in ("under", "no"):
                    r["under_price"] = oc.get("price"); r["line"] = oc.get("point", r["line"])
    return list(rows.values())


def pull(season: int, week: int, ts: str, within_hours: float | None = None) -> list[dict]:
    key = os.environ.get("ODDS_API_KEY", "").strip()
    if not key:
        return []
    ev = requests.get(f"{API}/events", timeout=30, params={"apiKey": key}).json()   # the events list costs nothing
    now = dt.datetime.utcnow()
    rows, raw = [], []
    for e in ev:
        start = pd.Timestamp(e.get("commence_time")).tz_convert(None) if e.get("commence_time") else None
        if start is None or start < now - pd.Timedelta(hours=1):
            continue
        if within_hours is not None and start > now + pd.Timedelta(hours=within_hours):
            continue
        r = requests.get(f"{API}/events/{e['id']}/odds", timeout=30, params={"apiKey": key, "regions": "us", "markets": ",".join(MARKETS), "oddsFormat": "american"})
        r.raise_for_status(); j = r.json(); raw.append(j)
        rows += parse_event(j, season, week, ts)
    _save_raw("oddsapi_props", raw, ts)
    return rows


def load_log() -> pd.DataFrame:
    f = LN / "props_log.csv"
    return pd.read_csv(f).reindex(columns=SCHEMA) if f.exists() else pd.DataFrame(columns=SCHEMA)


def due(now: dt.datetime, log: pd.DataFrame) -> float | None:
    """The window to pull for at this run, or None: Thursday 20:00 UTC for kickoffs within 30 hours, Sunday 14:00 UTC for
    everything left in the week; never twice inside six hours."""
    if len(log):
        last = pd.to_datetime(log.ts.str.replace(r"T(\d\d)-(\d\d)-(\d\d)Z", r"T\1:\2:\3Z", regex=True), errors="coerce").max()
        if pd.notna(last) and (now - last.to_pydatetime()) < dt.timedelta(hours=6):
            return None
    if now.weekday() == 3 and now.hour == 20:
        return 30.0
    if now.weekday() == 6 and now.hour == 14:
        return 48.0
    return None


def run(season=None, week=None, force: bool = False) -> pd.DataFrame:
    games = pd.read_parquet(OUT / "games.parquet")
    if season is None:
        season, week = current_week(games)
    now = dt.datetime.utcnow(); ts = now.strftime("%Y-%m-%dT%H-%M-%SZ")
    log = load_log()
    window = 48.0 if force else due(now, log)
    if window is None:
        return pd.DataFrame(columns=SCHEMA)
    rows = pull(season, week, ts, within_hours=window)
    df = pd.DataFrame(rows)
    if len(df):
        key = games.set_index(["season", "week", "home_team", "away_team"]).game_id
        df["game_id"] = [key.get((s, w, h, a)) for s, w, h, a in zip(df.season, df.week, df.home, df.away)]
        df = df.reindex(columns=SCHEMA)
        LN.mkdir(parents=True, exist_ok=True)
        pd.concat([log, df], ignore_index=True).to_csv(LN / "props_log.csv", index=False)
    print({"ts": ts, "season": season, "week": week, "prop_rows": len(df), "window_hours": window})
    return df


def closing(log: pd.DataFrame, game_id: str) -> pd.DataFrame:
    """The last logged line per (player, stat) for a game: the median line across books at the latest pull, with the
    number of books and the mean over/under prices. Used by the props builder for the card and the grading."""
    g = log[log.game_id == game_id]
    if not len(g):
        return pd.DataFrame(columns=["stat", "player", "key", "line", "books", "over_price", "under_price", "ts"])
    last = g.ts.max(); g = g[g.ts == last]
    out = g.groupby(["stat", "player"]).agg(line=("line", "median"), books=("book", "nunique"), over_price=("over_price", "mean"), under_price=("under_price", "mean")).reset_index()
    out["key"] = out.player.map(norm_name); out["ts"] = last
    return out
