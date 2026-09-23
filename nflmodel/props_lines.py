"""Player prop lines from The Odds API, logged for the props record (23 Sep 2026).

Free tier: 500 usage credits a month. Player props come one game at a time from the event-odds endpoint, and each
call costs (markets x regions) credits, so a full slate of 16 games at six markets is 96 credits. The budget is
spent as: one pull on Thursday 20:00 UTC for the games kicking off within 30 hours (the Thursday game: 6 credits),
one pull on Sunday 14:00 UTC for the rest of the week (Sunday and Monday games, near their closing lines: ~90),
about 415 a month, beside the game-line pull once a day (~30; ESPN carries the game lines every half hour anyway). PROPS_EVERY_RUN=1 forces a pull.
Markets: receiving yards, receptions, rushing yards, passing yards, anytime touchdown, tackles plus assists on the
free tier; the full menu (passing touchdowns, completions, attempts, interceptions, rush attempts, rush plus
reception yards, longest reception, rush and completion, sacks, solo tackles, defensive interceptions, kicking
points, field goals) once the key holds at least 5,000 credits, which a paid plan does. Every row of every book is
appended to data/lines/props_log.csv; the raw response is saved under data/lines/raw/. Nothing here is bet: the
lines are what the projections are graded against (nflmodel/props.py) and what the cards show beside them."""
from __future__ import annotations
import datetime as dt, os, re
import pandas as pd, requests
from .lines import LN, OUT, _save_raw, team_from_name, current_week

MARKETS = {"player_reception_yds": "rec_yards", "player_receptions": "rec_catches", "player_rush_yds": "rush_yards", "player_pass_yds": "pass_yards", "player_anytime_td": "anytime_td", "player_tackles_assists": "def_tackles"}   # the core six: what the free 500 credits a month afford
MARKETS_FULL = dict(MARKETS, **{"player_pass_tds": "pass_td", "player_pass_completions": "pass_completions", "player_pass_attempts": "pass_attempts", "player_pass_interceptions": "pass_int", "player_rush_attempts": "rush_attempts", "player_rush_reception_yds": "rush_rec_yards",
                                 "player_reception_longest": "rec_longest", "player_rush_longest": "rush_longest", "player_sacks": "def_sacks", "player_solo_tackles": "def_solo_tackles", "player_defensive_interceptions": "def_int", "player_kicking_points": "kick_points", "player_field_goals": "field_goals", "player_pass_longest_completion": "pass_longest"})   # every NFL player market The Odds API lists; pulled when the key has the credits (a paid plan)
FULL_MENU_MIN_CREDITS = 5000                          # pull the full menu only when at least this many credits remain: 20 markets x 16 games x 2 pulls a week needs about 2,800 a month
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
            stat = MARKETS_FULL.get(m.get("key"))
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
    evr = requests.get(f"{API}/events", timeout=30, params={"apiKey": key}); ev = evr.json()   # the events list costs nothing
    remaining = float(evr.headers.get("x-requests-remaining", "0") or 0); menu = MARKETS_FULL if remaining >= FULL_MENU_MIN_CREDITS else MARKETS
    print({"credits_remaining": remaining, "markets": len(menu)}, flush=True)
    now = dt.datetime.utcnow()
    rows, raw = [], []
    for e in ev:
        start = pd.Timestamp(e.get("commence_time")).tz_convert(None) if e.get("commence_time") else None
        if start is None or start < now - pd.Timedelta(hours=1):
            continue
        if within_hours is not None and start > now + pd.Timedelta(hours=within_hours):
            continue
        r = requests.get(f"{API}/events/{e['id']}/odds", timeout=30, params={"apiKey": key, "regions": "us", "markets": ",".join(menu), "oddsFormat": "american"})
        r.raise_for_status(); j = r.json(); raw.append(j)
        rows += parse_event(j, season, week, ts)
    _save_raw("oddsapi_props", raw, ts)
    return rows


# DFS pick'em lines (no key, no credits): every market at even odds by construction. Their lines sit close to the
# books' and cover markets the free Odds API tier cannot afford, so they are logged as books of their own.
PP_STATS = {"Pass Yards": "pass_yards", "Pass TDs": "pass_td", "Pass Completions": "pass_completions", "Pass Attempts": "pass_attempts", "INT": "pass_int", "Rush Yards": "rush_yards", "Rush Attempts": "rush_attempts", "Receiving Yards": "rec_yards", "Receptions": "rec_catches", "Rush+Rec Yds": "rush_rec_yards",
            "Longest Reception": "rec_longest", "Longest Rush": "rush_longest", "Longest Pass Completion": "pass_longest", "Longest Completion": "pass_longest", "Tackles+Ast": "def_tackles", "Sacks": "def_sacks", "Solo Tackles": "def_solo_tackles", "Kicking Points": "kick_points", "FG Made": "field_goals", "Pass+Rush Yds": "pass_rush_yards", "Rec Targets": "rec_targets"}
PP_TEAM = {"LAR": "LA", "JAC": "JAX", "WSH": "WAS", "ARZ": "ARI", "BLT": "BAL", "CLV": "CLE", "HST": "HOU"}
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36", "Accept": "application/json"}


def prizepicks(season: int, week: int, ts: str, games: pd.DataFrame) -> list[dict]:
    """PrizePicks projections for the NFL (league 9): standard lines only (no demon or goblin, no promo copies), one row per player and market.
    Touchdown markets are left out: a pick'em 0.5 line carries no price, so it says nothing about the chance."""
    j = None; errs = []
    for url, hdr in [("https://partner-api.prizepicks.com/projections", UA), ("https://api.prizepicks.com/projections", dict(UA, **{"Referer": "https://app.prizepicks.com/", "Origin": "https://app.prizepicks.com", "Accept-Language": "en-US,en;q=0.9"}))]:
        try:
            r = requests.get(url, timeout=30, headers=hdr, params={"league_id": 9, "per_page": 1000, "single_stat": "true"}); r.raise_for_status(); j = r.json(); break
        except Exception as e:  # noqa
            errs.append(f"{url.split('/')[2]}: {str(e)[:80]}")
    if j is None:
        raise RuntimeError(" | ".join(errs))
    _save_raw("prizepicks", j, ts)
    players = {p["id"]: p["attributes"] for p in j.get("included", []) if p.get("type") == "new_player"}
    wk = games[(games.season == season) & (games.week == week)]; team_game = {}
    for g in wk.itertuples(): team_game[g.home_team] = (g.game_id, g.home_team, g.away_team); team_game[g.away_team] = (g.game_id, g.home_team, g.away_team)
    rows = {}
    for d in sorted(j.get("data", []), key=lambda d: bool((d.get("attributes") or {}).get("is_promo"))):   # a promo copy of a line (discounted "flash sale") sits behind the regular one
        a = d.get("attributes", {}); stat = PP_STATS.get(a.get("stat_type"))
        if not stat or a.get("odds_type", "standard") != "standard" or a.get("line_score") is None or a.get("adjusted_odds"): continue   # adjusted-odds lines (a 0.5-yard "line" at a cut payout) are not even-odds lines
        pl = players.get(((d.get("relationships") or {}).get("new_player") or {}).get("data", {}).get("id"), {}); team = PP_TEAM.get(pl.get("team"), pl.get("team")); tg = team_game.get(team)
        if not tg or (pl.get("name"), stat) in rows: continue
        rows[(pl.get("name"), stat)] = {"ts": ts, "season": season, "week": week, "game_id": tg[0], "home": tg[1], "away": tg[2], "start": a.get("start_time"), "book": "prizepicks", "market": a.get("stat_type"), "stat": stat, "player": pl.get("name"), "line": float(a["line_score"]), "over_price": -119, "under_price": -119}
    return list(rows.values())


def underdog(season: int, week: int, ts: str, games: pd.DataFrame) -> list[dict]:
    """Underdog pick'em lines from the pick'em search (v2): over_under_lines with their appearances, players and teams,
    paged until a page adds nothing. Standard ("balanced") lines only, with Underdog's own higher/lower prices."""
    hdr = dict(UA, **{"Client-Type": "web", "Client-Version": "20260901", "Client-Request-Id": "nfl-model", "Referer": "https://underdogfantasy.com/", "Origin": "https://underdogfantasy.com"})
    lines, apps, players, teams, seen, errs = [], {}, {}, {}, set(), []
    for page in range(1, 31):
        url = f"https://api.underdogfantasy.com/v2/pickem_search/search_results?sport_id=NFL&page={page}&per_page=250"
        try:
            r = requests.get(url, timeout=30, headers=hdr); r.raise_for_status(); j = r.json()
        except Exception as e:  # noqa
            errs.append(f"page {page}: {str(e)[:60]}"); break
        new = [ln for ln in j.get("over_under_lines", []) if ln.get("id") not in seen]
        for ln in new: seen.add(ln.get("id"))
        lines += new; apps.update({a["id"]: a for a in j.get("appearances", [])}); players.update({p["id"]: p for p in j.get("players", [])}); teams.update({t["id"]: t.get("abbr") for t in j.get("teams", [])})
        if page == 1: _save_raw("underdog", j, ts)
        if not new: break
    if not lines:
        raise RuntimeError(" | ".join(errs) or "no lines")
    UD = {"passing_yds": "pass_yards", "passing_tds": "pass_td", "passing_comps": "pass_completions", "completions": "pass_completions", "passing_att": "pass_attempts", "pass_attempts": "pass_attempts", "passing_ints": "pass_int", "interceptions": "pass_int",
          "rushing_yds": "rush_yards", "rushing_att": "rush_attempts", "rush_attempts": "rush_attempts", "receiving_yds": "rec_yards", "receiving_rec": "rec_catches", "receptions": "rec_catches", "receiving_tgts": "rec_targets", "rush_rec_yds": "rush_rec_yards",
          "receiving_long": "rec_longest", "longest_reception": "rec_longest", "rushing_long": "rush_longest", "longest_rush": "rush_longest", "passing_long": "pass_longest", "passing_and_rushing_yds": "pass_rush_yards", "tackles_assists": "def_tackles", "sacks": "def_sacks", "kicking_points": "kick_points", "field_goals_made": "field_goals"}
    wk = games[(games.season == season) & (games.week == week)]; team_game = {}
    for g in wk.itertuples(): team_game[g.home_team] = (g.game_id, g.home_team, g.away_team); team_game[g.away_team] = (g.game_id, g.home_team, g.away_team)
    rows = {}
    for ln in lines:
        if ln.get("line_type", "balanced") != "balanced" or ln.get("status", "active") != "active": continue
        ou = ln.get("over_under") or {}; ast = ou.get("appearance_stat") or {}; stat = UD.get(ast.get("stat") or "")
        if not stat or ln.get("stat_value") is None: continue
        ap = apps.get(ast.get("appearance_id")) or {}; pl = players.get(ap.get("player_id")) or {}
        if pl.get("sport_id") not in (None, "NFL"): continue
        team = teams.get(ap.get("team_id") or pl.get("team_id")); team = PP_TEAM.get(team, team); tg = team_game.get(team)
        if not tg: continue
        name = f"{pl.get('first_name', '')} {pl.get('last_name', '')}".strip()
        if (name, stat) in rows: continue
        prices = {(o.get("choice") or ""): o.get("american_price") for o in ln.get("options", [])}
        def _p(v):
            try: return int(float(v))
            except Exception: return -119   # noqa
        rows[(name, stat)] = {"ts": ts, "season": season, "week": week, "game_id": tg[0], "home": tg[1], "away": tg[2], "start": None, "book": "underdog", "market": ast.get("display_stat") or ast.get("stat"), "stat": stat, "player": name, "line": float(ln["stat_value"]), "over_price": _p(prices.get("higher")), "under_price": _p(prices.get("lower"))}
    return list(rows.values())

def dfs_due(now: dt.datetime, force: bool) -> bool:
    """Free lines: every six hours on the half-hour watch, and on a forced run."""
    return force or (now.hour % 6 == 0 and now.minute < 30)


YARD_STATS = {"rec_yards", "rush_yards", "pass_yards", "rush_rec_yards", "pass_rush_yards", "rec_longest", "rush_longest", "pass_longest"}


def load_log() -> pd.DataFrame:
    """The log as appended, minus pick'em rows that cannot be even-odds lines (a yardage line under 2: PrizePicks'
    adjusted-odds board before the parser dropped it)."""
    f = LN / "props_log.csv"
    if not f.exists(): return pd.DataFrame(columns=SCHEMA)
    g = pd.read_csv(f).reindex(columns=SCHEMA)
    return g[~(g.book.isin(["prizepicks", "underdog"]) & g.stat.isin(YARD_STATS) & (g.line < 2))].reset_index(drop=True)


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


def run(season=None, week=None, force: bool = False, dfs_only: bool = False) -> pd.DataFrame:
    games = pd.read_parquet(OUT / "games.parquet")
    if season is None:
        season, week = current_week(games)
    now = dt.datetime.utcnow(); ts = now.strftime("%Y-%m-%dT%H-%M-%SZ")
    log = load_log()
    window = None if dfs_only else (168.0 if force else due(now, log))   # a forced pull takes the whole week ahead
    rows = pull(season, week, ts, within_hours=window) if window is not None else []
    if dfs_due(now, force or dfs_only):
        for name, fn in [("prizepicks", prizepicks), ("underdog", underdog)]:
            try:
                got = fn(season, week, ts, games); rows += got; print({"source": name, "rows": len(got)}, flush=True)
            except Exception as e:  # noqa
                print({"source": name, "error": str(e)[:160]}, flush=True)
    if not rows:
        return pd.DataFrame(columns=SCHEMA)
    df = pd.DataFrame(rows)
    if len(df):
        key = games.set_index(["season", "week", "home_team", "away_team"]).game_id
        df["game_id"] = [gid if isinstance(gid, str) else key.get((s, w, h, a)) for gid, s, w, h, a in zip(df.game_id if "game_id" in df else [None] * len(df), df.season, df.week, df.home, df.away)]
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
    g = g.sort_values("ts"); last = g.ts.max(); first = g.ts.min()
    cur = g.drop_duplicates(["book", "stat", "player"], keep="last")     # each book's latest line (the sources pull on different clocks)
    out = cur.groupby(["stat", "player"]).agg(line=("line", "median"), books=("book", "nunique"), over_price=("over_price", "mean"), under_price=("under_price", "mean")).reset_index()
    op = g.drop_duplicates(["book", "stat", "player"], keep="first").groupby(["stat", "player"]).agg(open_line=("line", "median"), open_over=("over_price", "mean")).reset_index()
    out = out.merge(op, on=["stat", "player"], how="left"); out["key"] = out.player.map(norm_name); out["ts"] = last; out["open_ts"] = first; out["pulls"] = int(g.ts.nunique())
    return out
