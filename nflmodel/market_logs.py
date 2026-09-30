"""More books and more splits, stored for study (30 Sep 2026, Matt: "can we pull more than just DraftKings betting
splits and lines, and store this data"). Both are free, both run from the line watch, both are display-and-study only:
no number here feeds the model, the picks' line or the page (the picks keep pricing on lines_log.csv).

  - books_log.csv: Action Network's public scoreboard, every book it carries (DraftKings, FanDuel, BetMGM, BetRivers,
    Caesars, bet365 and others, plus its "Open" opening line and its consensus), spread, total and moneyline with prices
    and the book's own change time. A row is written only when a book's numbers change, so the log holds every move
    without a row per pull.
  - splits_consensus_log.csv: ScoresAndOdds' consensus splits page (Action Network's; bets across its partner books,
    not DraftKings' alone), % of bets and % of money for each side of the spread, total and moneyline. A row only when a
    game's split changes. DraftKings' own splits stay in splits_log.csv.

Tried and not usable on 30 Sep 2026 (probe from the runner): VSIN's DraftKings and Circa splits (subscriber-locked),
Action Network's own bet and money shares (empty without a paid login), SportsBettingDime (drawn by script, not in the
page), Covers (404), ESPN (DraftKings only).
"""
from __future__ import annotations
import datetime as dt, re
import pandas as pd, requests
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LN, OUT = ROOT / "data" / "lines", ROOT / "data" / "processed"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"}
AN = "https://api.actionnetwork.com/web/v1"
AN_BOOKS = "15,30,68,69,71,75,79,247,123,972,76,49,1006,2194,3614"   # consensus, open, and the US books it lists; unknown ids return nothing
SAO = "https://www.scoresandodds.com/nfl/consensus-picks"
ABBR = {"LAR": "LA", "WSH": "WAS", "JAC": "JAX", "LVR": "LV", "OAK": "LV", "SD": "LAC", "STL": "LA"}
BOOK_COLS = ["home_spread", "spread_odds_home", "spread_odds_away", "total", "over_odds", "under_odds", "home_ml", "away_ml"]
SPLIT_COLS = ["line_a", "line_b", "bets_a", "bets_b", "money_a", "money_b"]


def _ab(x) -> str:
    x = str(x or "").strip().upper()
    return ABBR.get(x, x)


def _next_games() -> pd.DataFrame:
    g = pd.read_parquet(OUT / "games.parquet")
    g = g[g.home_score.isna()][["game_id", "season", "week", "away_team", "home_team", "kickoff_et"]].sort_values("kickoff_et")
    return g.drop_duplicates(["away_team", "home_team"]).rename(columns={"away_team": "away", "home_team": "home"})   # the next meeting of each pair


def _append_changes(df: pd.DataFrame, fname: str, key: list[str], cols: list[str]) -> int:
    """Append the rows of df whose values in cols differ from the last logged row with the same key (all rows the first time)."""
    if not len(df):
        return 0
    f = LN / fname
    if f.exists():
        old = pd.read_csv(f)
        last = old.sort_values("ts").drop_duplicates(key, keep="last").set_index(key)[cols]
        cur = df.set_index(key)[cols]
        prev = last.reindex(cur.index)
        same = ((cur == prev) | (cur.isna() & prev.isna())).all(axis=1)
        df = df[~same.values]
    if len(df):
        LN.mkdir(parents=True, exist_ok=True)
        df.to_csv(f, mode="a", header=not f.exists(), index=False)
    return len(df)


def books(weeks: list[int] | None = None) -> int:
    """Every book's number for this week's (and, when given, next week's) games from Action Network; returns rows added."""
    ts = dt.datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%SZ")
    try:
        bl = requests.get(f"{AN}/books", headers=UA, timeout=30).json()
        names = {int(b["id"]): (b.get("display_name") or b.get("name") or str(b["id"])) for b in (bl.get("books", bl) if isinstance(bl, dict) else bl)}
    except Exception:  # noqa  (names are a convenience; the id is kept either way)
        names = {}
    games = []
    for w in (weeks or [None]):
        p = {"period": "game", "bookIds": AN_BOOKS}
        if w is not None:
            p["week"] = w
        r = requests.get(f"{AN}/scoreboard/nfl", params=p, headers=UA, timeout=30); r.raise_for_status()
        games += r.json().get("games", [])
    rows = []
    for g in games:
        tm = {t["id"]: _ab(t.get("abbr")) for t in g.get("teams", [])}
        home, away = tm.get(g.get("home_team_id")), tm.get(g.get("away_team_id"))
        for o in g.get("odds") or []:
            bid = int(o.get("book_id") or 0)
            rows.append({"ts": ts, "source": "actionnetwork", "book_id": bid, "book": names.get(bid, str(bid)), "away": away, "home": home,
                         "kickoff": g.get("start_time"), "home_spread": o.get("spread_home"), "spread_odds_home": o.get("spread_home_line"),
                         "spread_odds_away": o.get("spread_away_line"), "total": o.get("total"), "over_odds": o.get("over"), "under_odds": o.get("under"),
                         "home_ml": o.get("ml_home"), "away_ml": o.get("ml_away"), "book_updated": o.get("inserted")})
    df = pd.DataFrame(rows)
    if not len(df):
        raise RuntimeError("Action Network scoreboard returned no odds")
    df = df.drop_duplicates(["away", "home", "book_id"]).merge(_next_games(), on=["away", "home"], how="left")
    return _append_changes(df, "books_log.csv", ["away", "home", "book_id"], BOOK_COLS)


def parse_sao(html: str) -> list[dict]:
    """One row per game and market from the consensus page: side a is the left (away, or over) side."""
    rows = []
    for chunk in html.split('<div class="trend-card consensus consensus-table-')[1:]:
        m = re.match(r"(spread|total|moneyline)--", chunk)
        if not m:
            continue
        sides = re.findall(r"<strong>\s*([A-Za-z]+)\s*(?:<span>\s*)?(?:\(([^)]*)\))?\s*(?:</span>\s*)?</strong>", chunk)[:2]   # the total card wraps its line: Over <span>(o38.5)</span>
        pct = [int(x) for x in re.findall(r'class="percentage-[ab]"[^>]*>\s*(\d+)%', chunk)[:4]]
        teams = re.findall(r'class="team-flag"\s*([A-Z]{2,3})', chunk) or re.findall(r'teamlogos/nfl/\d+/([a-z]{2,3})\.png', chunk)
        ko = re.search(r'data-role="localtime" data-value="([^"]+)"', chunk)
        ev = re.search(r'data-event="nfl/(\d+)"', chunk)
        if len(sides) < 2 or len(pct) < 4:
            continue
        num = lambda s: float(s.replace("+", "").replace("o", "").replace("u", "")) if s and re.fullmatch(r"[+\-ou]?\d+(\.\d)?", s.strip()) else None
        rows.append({"market": {"moneyline": "ml"}.get(m.group(1), m.group(1)), "event": ev.group(1) if ev else None, "kickoff": ko.group(1) if ko else None,
                     "side_a": _ab(sides[0][0]), "side_b": _ab(sides[1][0]), "line_a": num(sides[0][1]), "line_b": num(sides[1][1]),
                     "bets_a": pct[0], "bets_b": pct[1], "money_a": pct[2], "money_b": pct[3],
                     "away": _ab(teams[0]) if teams else None, "home": _ab(teams[1]) if len(teams) > 1 else None})
    return rows


def consensus_splits() -> int:
    """ScoresAndOdds' consensus bets and money shares; returns rows added."""
    ts = dt.datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%SZ")
    r = requests.get(SAO, headers=UA, timeout=30); r.raise_for_status()
    rows = parse_sao(r.text)
    if not rows:
        raise RuntimeError("consensus splits page fetched but no rows recognised")
    df = pd.DataFrame(rows)
    df["away"] = df.away.fillna(df.side_a.where(df.market != "total")); df["home"] = df.home.fillna(df.side_b.where(df.market != "total"))
    df = df.merge(_next_games(), on=["away", "home"], how="left")
    df.insert(0, "ts", ts); df.insert(1, "source", "scoresandodds")
    return _append_changes(df, "splits_consensus_log.csv", ["away", "home", "market"], SPLIT_COLS)


def run(weeks: list[int] | None = None) -> dict:
    out, errors = {}, []
    for name, fn in [("books", lambda: books(weeks)), ("consensus splits", consensus_splits)]:
        try:
            out[name] = fn()
        except Exception as e:  # noqa  (one source failing never stops the other or the line watch)
            errors.append(f"{name}: {str(e)[:120]}")
    out["errors"] = errors
    return out


if __name__ == "__main__":
    print(run())
