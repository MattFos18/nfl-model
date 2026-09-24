"""Line watch: log spreads, totals and moneylines from free sources every run.

Sources
  ESPN public scoreboard (site.api.espn.com, with fallbacks): one consensus line per game with the provider named.
  The Odds API (free tier, key in ODDS_API_KEY): every US book's spread, total and moneyline, once a day; player prop
  lines twice a week (nflmodel/props_lines.py) inside the same 500-credit month.
  DraftKings sportsbook public event-group feed (event group 88808 = NFL): spread, total, moneyline per game.
  DraftKings betting splits: no stable public endpoint found yet; the hook is here and returns nothing until
  one is confirmed. The report says so rather than pretending.

Every run appends one row per (game, book, market) to data/lines/lines_log.csv and saves the raw responses
under data/lines/raw/<timestamp>_<source>.json so a parsing mistake never loses data. Games are keyed to
nflverse game_ids by season, week and team abbreviations.

This sandbox cannot reach either host (egress policy); the GitHub Actions workflow runs it every 10 minutes.
Usage: python -m nflmodel.lines [--season 2026 --week 3]
"""
from __future__ import annotations
import argparse, json, re, datetime as dt
import numpy as np, pandas as pd, requests
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT, LN = ROOT / "data" / "processed", ROOT / "data" / "lines"
H = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36",
     "Accept": "application/json, text/plain, */*", "Accept-Language": "en-US,en;q=0.9", "Referer": "https://www.espn.com/", "Origin": "https://www.espn.com"}
HDK = {**H, "Referer": "https://sportsbook.draftkings.com/", "Origin": "https://sportsbook.draftkings.com"}


def _get_json(urls, headers, params=None):
    """Try each URL in turn; the first that answers with JSON wins. Every failure is kept for the log."""
    errs = []
    for u in urls:
        try:
            r = requests.get(u, headers=headers, timeout=30, params=params)
            r.raise_for_status()
            return r.json(), u
        except Exception as e:  # noqa
            errs.append(f"{u.split('/')[2]}: {str(e)[:60]}")
    raise RuntimeError(" | ".join(errs))
ESPN_ABBR = {"WSH": "WAS", "JAC": "JAX", "LAR": "LA"}
DK_NAME = {"Arizona": "ARI", "Atlanta": "ATL", "Baltimore": "BAL", "Buffalo": "BUF", "Carolina": "CAR", "Chicago": "CHI", "Cincinnati": "CIN",
           "Cleveland": "CLE", "Dallas": "DAL", "Denver": "DEN", "Detroit": "DET", "Green Bay": "GB", "Houston": "HOU", "Indianapolis": "IND",
           "Jacksonville": "JAX", "Kansas City": "KC", "Las Vegas": "LV", "LA Chargers": "LAC", "Los Angeles Chargers": "LAC", "LA Rams": "LA",
           "Los Angeles Rams": "LA", "Miami": "MIA", "Minnesota": "MIN", "New England": "NE", "New Orleans": "NO", "NY Giants": "NYG",
           "New York Giants": "NYG", "NY Jets": "NYJ", "New York Jets": "NYJ", "Philadelphia": "PHI", "Pittsburgh": "PIT", "San Francisco": "SF",
           "Seattle": "SEA", "Tampa Bay": "TB", "Tennessee": "TEN", "Washington": "WAS"}
NICK = {"Cardinals": "ARI", "Falcons": "ATL", "Ravens": "BAL", "Bills": "BUF", "Panthers": "CAR", "Bears": "CHI", "Bengals": "CIN", "Browns": "CLE",
        "Cowboys": "DAL", "Broncos": "DEN", "Lions": "DET", "Packers": "GB", "Texans": "HOU", "Colts": "IND", "Jaguars": "JAX", "Chiefs": "KC",
        "Raiders": "LV", "Chargers": "LAC", "Rams": "LA", "Dolphins": "MIA", "Vikings": "MIN", "Patriots": "NE", "Saints": "NO", "Giants": "NYG",
        "Jets": "NYJ", "Eagles": "PHI", "Steelers": "PIT", "49ers": "SF", "Seahawks": "SEA", "Buccaneers": "TB", "Titans": "TEN", "Commanders": "WAS"}


def team_from_name(name: str):
    if not isinstance(name, str):
        return None
    for k, v in DK_NAME.items():
        if name.startswith(k):
            return v
    for k, v in NICK.items():
        if k.lower() in name.lower():
            return v
    return None


def _save_raw(source, obj, ts):
    (LN / "raw").mkdir(parents=True, exist_ok=True)
    (LN / "raw" / f"{ts}_{source}.json").write_text(json.dumps(obj)[:5_000_000])


def espn(season: int, week: int, ts: str) -> list[dict]:
    j, _ = _get_json(["https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard",
                      "https://site.web.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard",
                      "https://cdn.espn.com/core/nfl/scoreboard?xhr=1"], H, params={"week": week, "seasontype": 2, "dates": season})
    if "events" not in j and "content" in j:      # the cdn shape wraps the same scoreboard
        j = (j.get("content") or {}).get("sbData") or {}
    _save_raw("espn", j, ts)
    return _parse_espn(j, season, week, ts)


def _am(x):
    """American odds from ESPN's strings ("-250", "+205", "EVEN") or numbers; None when absent."""
    if x is None or x == "":
        return None
    if isinstance(x, (int, float)):
        return float(x)
    t = str(x).strip().upper()
    if t in ("EVEN", "EV", "PK"):
        return 100.0
    try:
        return float(t.replace("+", ""))
    except ValueError:
        return None


def _close(o, *path):
    """ESPN's newer odds shape (since Sep 2026): o["moneyline"]["home"]["close"]["odds"] and the like; the current price."""
    for k in path:
        o = (o or {}).get(k) if isinstance(o, dict) else None
    return o


def _parse_espn(j: dict, season: int, week: int, ts: str) -> list[dict]:
    rows = []
    for ev in j.get("events", []):
        comp = (ev.get("competitions") or [{}])[0]
        home = away = None
        for c in comp.get("competitors", []):
            ab = ESPN_ABBR.get(c["team"]["abbreviation"], c["team"]["abbreviation"])
            if c.get("homeAway") == "home":
                home = ab
            else:
                away = ab
        for o in comp.get("odds", []) or []:
            provider = (o.get("provider") or {}).get("name", "ESPN")
            details = o.get("details")            # e.g. "KC -3.5"
            spread = o.get("spread")              # ESPN: the home team's handicap (positive = home underdog), checked 21 Sep 2026
            home_spread = None
            if spread is not None:
                home_spread = -float(spread)      # nflverse sign: positive = home favoured
            elif isinstance(details, str):
                m = re.match(r"^([A-Z]{2,3})\s*([+-]?[\d.]+)$", details.strip())
                if m:
                    fav = ESPN_ABBR.get(m.group(1), m.group(1))
                    home_spread = -float(m.group(2)) if fav == home else float(m.group(2))
            # the moneyline and the prices moved to o["moneyline"], o["pointSpread"], o["total"] (current price under "close");
            # the older keys are read first so either shape works
            hml = _am((o.get("homeTeamOdds") or {}).get("moneyLine")) or _am(_close(o, "moneyline", "home", "close", "odds"))
            aml = _am((o.get("awayTeamOdds") or {}).get("moneyLine")) or _am(_close(o, "moneyline", "away", "close", "odds"))
            rows.append({"ts": ts, "source": "espn:" + provider, "season": season, "week": week, "home": home, "away": away,
                         "home_spread": home_spread, "total": o.get("overUnder"), "home_ml": hml, "away_ml": aml,
                         "spread_odds_home": _am((o.get("homeTeamOdds") or {}).get("spreadOdds")) or _am(_close(o, "pointSpread", "home", "close", "odds")),
                         "spread_odds_away": _am((o.get("awayTeamOdds") or {}).get("spreadOdds")) or _am(_close(o, "pointSpread", "away", "close", "odds")),
                         "over_odds": _am(_close(o, "total", "over", "close", "odds")), "under_odds": _am(_close(o, "total", "under", "close", "odds"))})
    return rows


def draftkings(season: int, week: int, ts: str) -> list[dict]:
    j, _ = _get_json(["https://sportsbook.draftkings.com/sites/US-SB/api/v5/eventgroups/88808",
                      "https://sportsbook-nash.draftkings.com/sites/US-SB/api/v5/eventgroups/88808",
                      "https://sportsbook-us-ny.draftkings.com/sites/US-NY/api/v5/eventgroups/88808"], HDK, params={"format": "json"})
    _save_raw("draftkings", j, ts)
    eg = j.get("eventGroup", {})
    events = {e["eventId"]: e for e in eg.get("events", [])}
    rows = {}
    for cat in eg.get("offerCategories", []):
        if cat.get("name") not in ("Game Lines",):
            continue
        for sub in cat.get("offerSubcategoryDescriptors", []):
            if sub.get("name") != "Game":
                continue
            for offer_list in (sub.get("offerSubcategory") or {}).get("offers", []):
                for offer in offer_list:
                    ev = events.get(offer.get("eventId"))
                    if not ev:
                        continue
                    name = ev.get("name", "")
                    m = re.match(r"^(.*?)\s+@\s+(.*)$", name)
                    away = team_from_name(m.group(1)) if m else team_from_name(ev.get("teamName1"))
                    home = team_from_name(m.group(2)) if m else team_from_name(ev.get("teamName2"))
                    key = (home, away)
                    row = rows.setdefault(key, {"ts": ts, "source": "draftkings", "season": season, "week": week, "home": home, "away": away,
                                               "home_spread": None, "total": None, "home_ml": None, "away_ml": None, "spread_odds_home": None, "spread_odds_away": None,
                                               "start": ev.get("startDate")})
                    label = offer.get("label", "")
                    for oc in offer.get("outcomes", []):
                        t = team_from_name(oc.get("label", ""))
                        line = oc.get("line")
                        odds = oc.get("oddsAmerican")
                        odds = int(str(odds).replace("+", "")) if odds not in (None, "") else None
                        if label == "Spread" and t == home and line is not None:
                            row["home_spread"], row["spread_odds_home"] = -float(line), odds
                        elif label == "Spread" and t == away:
                            row["spread_odds_away"] = odds
                        elif label == "Total" and str(oc.get("label", "")).lower().startswith("over") and line is not None:
                            row["total"], row["over_odds"] = float(line), odds
                        elif label == "Total" and str(oc.get("label", "")).lower().startswith("under"):
                            row["under_odds"] = odds
                        elif label == "Moneyline" and t == home:
                            row["home_ml"] = odds
                        elif label == "Moneyline" and t == away:
                            row["away_ml"] = odds
    return list(rows.values())


def odds_api(season: int, week: int, ts: str) -> list[dict]:
    """The Odds API (the-odds-api.com), free tier: 500 requests a month, one request returns every NFL game across the US books.
    Needs ODDS_API_KEY in the environment (a GitHub Actions secret); silently skipped without it. Called once a day by the
    workflow (about 30 credits a month) so the player-prop pulls fit in the same free allowance."""
    import os
    key = os.environ.get("ODDS_API_KEY", "").strip()
    if not key:
        return []
    r = requests.get("https://api.the-odds-api.com/v4/sports/americanfootball_nfl/odds", timeout=30,
                     params={"regions": "us", "markets": "spreads,totals,h2h", "oddsFormat": "american", "apiKey": key})
    r.raise_for_status()
    j = r.json()
    _save_raw("oddsapi", j, ts)
    rows = []
    for ev in j:
        home, away = team_from_name(ev.get("home_team")), team_from_name(ev.get("away_team"))
        if not home or not away:
            continue
        for bk in ev.get("bookmakers", []):
            row = {"ts": ts, "source": "oddsapi:" + bk.get("key", ""), "season": season, "week": week, "home": home, "away": away,
                   "home_spread": None, "total": None, "home_ml": None, "away_ml": None, "spread_odds_home": None, "spread_odds_away": None,
                   "start": ev.get("commence_time")}
            for m in bk.get("markets", []):
                for oc in m.get("outcomes", []):
                    t = team_from_name(oc.get("name")) if m["key"] != "totals" else None
                    if m["key"] == "spreads" and t == home and oc.get("point") is not None:
                        row["home_spread"], row["spread_odds_home"] = -float(oc["point"]), oc.get("price")
                    elif m["key"] == "spreads" and t == away:
                        row["spread_odds_away"] = oc.get("price")
                    elif m["key"] == "totals" and str(oc.get("name", "")).lower() == "over" and oc.get("point") is not None:
                        row["total"], row["over_odds"] = float(oc["point"]), oc.get("price")
                    elif m["key"] == "totals" and str(oc.get("name", "")).lower() == "under":
                        row["under_odds"] = oc.get("price")
                    elif m["key"] == "h2h" and t == home:
                        row["home_ml"] = oc.get("price")
                    elif m["key"] == "h2h" and t == away:
                        row["away_ml"] = oc.get("price")
            rows.append(row)
    return rows


STADIUM_TEAMS = {"ARI", "ATL", "BAL", "BUF", "CAR", "CHI", "CIN", "CLE", "DAL", "DEN", "DET", "GB", "HOU", "IND", "JAX", "KC", "LV", "LAC", "LA",
                 "MIA", "MIN", "NE", "NO", "NYG", "NYJ", "PHI", "PIT", "SF", "SEA", "TB", "TEN", "WAS"}


def draftkings_splits(season: int, week: int, ts: str) -> list[dict]:
    """Bets % and money % per side. No free API exists; this tries the public Covers consensus page and parses whatever team
    abbreviations and percentages it can find near each other. Best effort: it logs rows when it works and an error when the
    page changes, and nothing downstream depends on it."""
    r = requests.get("https://www.covers.com/sports/nfl/matchups", headers={**H, "Referer": "https://www.covers.com/"}, timeout=30)
    r.raise_for_status()
    html = r.text
    (LN / "raw").mkdir(parents=True, exist_ok=True)
    (LN / "raw" / f"{ts}_covers.html").write_text(html[:3_000_000])
    rows = []
    for m in re.finditer(r"([A-Z]{2,3})[^%<]{0,80}?(\d{1,3})%", html):
        ab = ESPN_ABBR.get(m.group(1), m.group(1))
        if ab in STADIUM_TEAMS:
            rows.append({"ts": ts, "source": "covers:consensus", "season": season, "week": week, "team": ab, "bets_pct": int(m.group(2))})
    if not rows:
        raise RuntimeError("covers page fetched but no consensus percentages recognised")
    pd.DataFrame(rows).to_csv(LN / "splits_log.csv", mode="a", header=not (LN / "splits_log.csv").exists(), index=False)
    return []   # splits go to their own log; the lines log keeps one shape


# one fixed column order for the log, whatever a source happens to return; readers never depend on a row's field count
SCHEMA = ["ts", "source", "season", "week", "home", "away", "home_spread", "total", "home_ml", "away_ml",
          "spread_odds_home", "spread_odds_away", "over_odds", "under_odds", "start", "game_id"]
_LEGACY_13 = SCHEMA[:12] + ["game_id"]
_LEGACY_16 = SCHEMA[:12] + ["start", "over_odds", "under_odds", "game_id"]


def load_log() -> pd.DataFrame:
    """The lines log as a clean table. Rows written before the fixed schema (13 or 16 fields in an older order) are mapped
    by field count, and the file is rewritten in the fixed order the first time that happens."""
    f = LN / "lines_log.csv"
    if not f.exists():
        return pd.DataFrame(columns=SCHEMA)
    lines = [l.rstrip("\n") for l in f.read_text().splitlines() if l.strip()]
    header = lines[0].split(",")
    rows, legacy = [], False
    for l in lines[1:]:
        parts = l.split(",")
        if header == SCHEMA and len(parts) == len(SCHEMA):
            names = SCHEMA
        elif len(parts) == 13:
            names, legacy = _LEGACY_13, True
        elif len(parts) == 16 and header != SCHEMA:
            names, legacy = _LEGACY_16, True
        elif len(parts) == len(header):
            names = header
        else:
            continue
        rows.append({k: (v if v != "" else None) for k, v in zip(names, parts)})
    d = pd.DataFrame(rows).reindex(columns=SCHEMA)
    for c in ["season", "week", "home_spread", "total", "home_ml", "away_ml", "spread_odds_home", "spread_odds_away", "over_odds", "under_odds"]:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    if legacy or header != SCHEMA:
        d.to_csv(f, index=False)
    return d


def attach_game_ids(rows: list[dict]) -> pd.DataFrame:
    games = pd.read_parquet(OUT / "games.parquet")
    df = pd.DataFrame(rows)
    if len(df) == 0:
        return df
    key = games.set_index(["season", "week", "home_team", "away_team"]).game_id
    df["game_id"] = [key.get((s, w, h, a)) for s, w, h, a in zip(df.season, df.week, df.home, df.away)]
    # a book that posts lines for later weeks (lookahead lines) is matched by teams and kickoff date, and the row takes
    # that game's week, so the log carries a line's whole life from the first post to the close
    if "start" in df.columns:
        miss = df.game_id.isna() & df.start.notna()
        if miss.any():
            gd = games[games.gameday.notna()].copy(); gd["day"] = pd.to_datetime(gd.gameday).dt.date
            for i in df.index[miss]:
                try: d0 = pd.Timestamp(df.at[i, "start"]).tz_convert("America/New_York").date()
                except Exception: continue
                hit = gd[(gd.home_team == df.at[i, "home"]) & (gd.away_team == df.at[i, "away"]) & ((pd.to_datetime(gd.day) - pd.Timestamp(d0)).abs() <= pd.Timedelta(days=1))]
                if len(hit): df.at[i, "game_id"] = hit.iloc[0].game_id; df.at[i, "week"] = int(hit.iloc[0].week); df.at[i, "season"] = int(hit.iloc[0].season)
    return df


def backfill_espn_prices() -> int:
    """Re-read every saved ESPN snapshot (data/lines/raw/*_espn.json) and fill the moneylines and prices the log is
    missing on its ESPN rows (the parser missed ESPN's newer odds shape until 24 Sep 2026). Returns rows filled."""
    f = LN / "lines_log.csv"
    if not f.exists():
        return 0
    d = load_log(); fill = ["home_ml", "away_ml", "spread_odds_home", "spread_odds_away", "over_odds", "under_odds"]
    need = d.source.astype(str).str.startswith("espn") & d.home_ml.isna()
    if not need.any():
        return 0
    n = 0
    for ts in sorted(d.loc[need, "ts"].unique()):
        rf = LN / "raw" / f"{ts}_espn.json"
        if not rf.exists():
            continue
        try:
            j = json.loads(rf.read_text())
        except Exception:  # noqa
            continue
        if "events" not in j and "content" in j:
            j = (j.get("content") or {}).get("sbData") or {}
        for r in _parse_espn(j, None, None, ts):
            m = need & (d.ts == ts) & (d.home == r["home"]) & (d.away == r["away"]) & (d.source == r["source"])
            if m.any() and r["home_ml"] is not None:
                for c in fill:
                    if r.get(c) is not None:
                        d.loc[m & d[c].isna(), c] = r[c]
                n += int(m.sum())
    if n:
        d.to_csv(f, index=False)
    return n


def current_week(games: pd.DataFrame):
    """The week to price: the one holding the next unplayed kickoff, unless fewer than four of its games are still
    to come (Monday night, say), in which case the following week."""
    now = pd.Timestamp.now(tz="America/New_York").tz_localize(None)
    up = games[(games.kickoff_et >= now) & games.home_score.isna() & (games.game_type == "REG")].sort_values("kickoff_et")
    if len(up) == 0:
        return int(games.season.max()), int(games.week.max())
    s, w = int(up.iloc[0].season), int(up.iloc[0].week)
    if len(up[(up.season == s) & (up.week == w)]) < 4:
        later = up[(up.season > s) | ((up.season == s) & (up.week > w))]
        if len(later):
            s, w = int(later.iloc[0].season), int(later.iloc[0].week)
    return s, w


def odds_api_due(now: dt.datetime) -> bool:
    """The daily sportsbook pull is due at the first line-watch run after 12:00 UTC (GitHub's cron is irregular, so
    it cannot wait for a run inside 12:00 to 12:30), once: not when a pull or an attempt has happened since."""
    from .props_lines import last_anchor, log_times, tried
    anchor, _ = last_anchor(now, [(None, 12, 0.0)])
    g = load_log(); g = g[g.source.astype(str).str.startswith("oddsapi:")]
    last = log_times(g).max() if len(g) else pd.NaT
    t = tried("oddsapi")
    return not ((pd.notna(last) and last.to_pydatetime() >= anchor) or (t is not None and t >= anchor))


def run(season=None, week=None) -> pd.DataFrame:
    games = pd.read_parquet(OUT / "games.parquet")
    if season is None:
        season, week = current_week(games)
    ts = dt.datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%SZ")
    rows, errors = [], []
    import os
    sources = [("espn", espn), ("draftkings", draftkings), ("dk_splits", draftkings_splits)]
    if os.environ.get("ODDS_API_KEY") and (os.environ.get("ODDS_API_EVERY_RUN") or odds_api_due(dt.datetime.utcnow())):
        sources.append(("oddsapi", odds_api))     # once a day from 12:00 UTC: ~30 credits a month, leaving the free 500 for the player props (props_lines.py); ESPN carries the game lines every run
        from .props_lines import mark
        mark("oddsapi", dt.datetime.utcnow())
    for name, fn in sources:
        try:
            rows += fn(season, week, ts)
        except Exception as e:  # noqa
            errors.append(f"{name}: {str(e)[:120]}")
    df = attach_game_ids(rows)
    LN.mkdir(parents=True, exist_ok=True)
    log = LN / "lines_log.csv"
    if len(df):
        df = df.reindex(columns=SCHEMA)
        old = load_log()          # also normalises any older rows to the fixed schema
        pd.concat([old, df], ignore_index=True).to_csv(log, index=False)
    try:
        backfill_espn_prices()    # no-op once every saved ESPN snapshot's prices are in the log
    except Exception as e:  # noqa
        errors.append(f"espn backfill: {str(e)[:120]}")
    try:
        from . import props_lines
        props_lines.run(season, week, force=bool(os.environ.get("PROPS_EVERY_RUN")), dfs_only=bool(os.environ.get("DFS_EVERY_RUN")))   # player props, on its own budgeted cadence; DFS_EVERY_RUN pulls only the free pick'em lines
    except Exception as e:  # noqa
        errors.append(f"props: {str(e)[:120]}")
    status = {"ts": ts, "season": season, "week": week, "rows": len(df), "errors": "; ".join(errors)}
    pd.DataFrame([status]).to_csv(LN / "watch_log.csv", mode="a", header=not (LN / "watch_log.csv").exists(), index=False)
    print(status)
    return df


def history(game_id: str) -> pd.DataFrame:
    """Every logged line for one game, oldest first (for the game card's movement chart and CLV)."""
    d = load_log()
    return d[d.game_id == game_id].sort_values("ts")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", type=int)
    ap.add_argument("--week", type=int)
    a = ap.parse_args()
    run(a.season, a.week)
