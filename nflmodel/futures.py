"""The books' season-long markets (24 Sep 2026): Super Bowl, conference and division winners, regular-season win totals
and player season totals (receiving, rushing and passing yards), to set beside the model's season odds and player totals.

Two sources, fetched once a day by the line watch (.github/workflows/lines.yml; the runner can reach them, this
repo's own machine cannot):
  ESPN's futures feed (sports.core.api.espn.com .../seasons/<season>/futures): every futures market ESPN shows, with
    the provider's price per team or player. Free, no key.
  The Odds API outright markets (americanfootball_nfl_*_winner): every US book's price on the Super Bowl winner and
    whatever other NFL outright markets the API lists; 1 credit a market, once a day (about 30 credits a month).
Raw answers are kept under data/lines/futures/<date>/ exactly as they came; parse() turns them into
data/lines/futures_log.csv (one row per market, subject and book, with the price and its implied chance).

Usage: python -m nflmodel.futures --fetch   (no-op if today's folder already exists, unless FUTURES_EVERY_RUN=1)
       python -m nflmodel.futures --parse"""
from __future__ import annotations
import datetime as dt, json, os, re, sys, time
import pandas as pd, requests
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIR = ROOT / "data" / "lines" / "futures"
LOG = ROOT / "data" / "lines" / "futures_log.csv"
H = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36",
     "Accept": "application/json, text/plain, */*", "Referer": "https://www.espn.com/"}
ESPN = "https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/seasons/{season}/futures"
ODDS = "https://api.the-odds-api.com/v4/sports"
ESPN_TEAM = {1: "ATL", 2: "BUF", 3: "CHI", 4: "CIN", 5: "CLE", 6: "DAL", 7: "DEN", 8: "DET", 9: "GB", 10: "TEN", 11: "IND", 12: "KC", 13: "LV", 14: "LA",
             15: "MIA", 16: "MIN", 17: "NE", 18: "NO", 19: "NYG", 20: "NYJ", 21: "PHI", 22: "ARI", 23: "PIT", 24: "LAC", 25: "SF", 26: "SEA", 27: "TB",
             28: "WAS", 29: "CAR", 30: "JAX", 33: "BAL", 34: "HOU"}


def _season(today: dt.date) -> int:
    return today.year if today.month >= 3 else today.year - 1


def fetch(force: bool = False) -> Path | None:
    today = dt.datetime.utcnow().date(); out = DIR / today.isoformat()
    if out.exists() and not (force or os.environ.get("FUTURES_EVERY_RUN")):
        print("futures: already fetched today", flush=True); return None
    out.mkdir(parents=True, exist_ok=True); season = _season(today)
    # ESPN: the list, then any item given only as a link
    try:
        r = requests.get(ESPN.format(season=season), params={"limit": 300, "lang": "en", "region": "us"}, headers=H, timeout=30); r.raise_for_status()
        j = r.json(); items = []
        for it in j.get("items", []):
            if set(it) == {"$ref"}:
                try:
                    it = requests.get(it["$ref"], headers=H, timeout=30).json(); time.sleep(0.2)
                except Exception as e:  # noqa
                    print("futures: espn item failed", str(e)[:100], flush=True); continue
            items.append(it)
        (out / "espn.json").write_text(json.dumps({"season": season, "count": j.get("count"), "items": items}))
        print("futures: espn", len(items), "markets:", [i.get("name") for i in items][:80], flush=True)
    except Exception as e:  # noqa
        print("futures: espn failed", str(e)[:160], flush=True)
    # The Odds API: the sports list is free; each NFL outright market is 1 credit
    key = os.environ.get("ODDS_API_KEY", "").strip()
    if key:
        try:
            sp = requests.get(ODDS, params={"apiKey": key, "all": "true"}, timeout=30).json()
            keys = [s["key"] for s in sp if s.get("has_outrights") and s.get("key", "").startswith("americanfootball_nfl")]
            print("futures: odds api outright markets", keys, flush=True)
            for k in keys:
                r = requests.get(f"{ODDS}/{k}/odds", params={"apiKey": key, "regions": "us", "markets": "outrights", "oddsFormat": "american"}, timeout=30)
                print("futures:", k, r.status_code, "credits left", r.headers.get("x-requests-remaining"), flush=True)
                if r.ok:
                    (out / f"oddsapi_{k}.json").write_text(r.text)
        except Exception as e:  # noqa
            print("futures: odds api failed", str(e)[:160], flush=True)
    return out


def implied(odds) -> float | None:
    try:
        o = float(str(odds).replace("+", ""))
    except ValueError:
        return None
    return 100 / (o + 100) if o > 0 else -o / (-o + 100)


def _ref_id(ref: str, kind: str) -> int | None:
    m = re.search(rf"/{kind}/(\d+)", ref or "")
    return int(m.group(1)) if m else None


def parse() -> pd.DataFrame:
    """Every saved day into one table: ts (the folder's date), source, market, subject (team or player), line (for an
    over/under), side, price, implied chance with the book's margin in, and no_vig (the chance with the margin taken
    out across the market: each subject's implied chance over the market's sum, for one-winner markets)."""
    rows = []
    for d in sorted(p for p in DIR.glob("*") if p.is_dir()):
        f = d / "espn.json"
        if f.exists():
            j = json.loads(f.read_text())
            for it in j.get("items", []):
                market = it.get("name") or it.get("displayName") or str(it.get("id"))
                for fu in it.get("futures", []) or []:
                    prov = ((fu.get("provider") or {}).get("name")) or "espn"
                    for b in fu.get("books", []) or []:
                        team = ESPN_TEAM.get(_ref_id((b.get("team") or {}).get("$ref", ""), "teams"))
                        ath = _ref_id((b.get("athlete") or {}).get("$ref", ""), "athletes")
                        rows.append({"ts": d.name, "source": "espn:" + prov, "market": market, "team": team, "espn_athlete_id": ath,
                                     "line": b.get("line") or b.get("overUnder"), "side": b.get("side") or b.get("type"), "price": b.get("value") or b.get("odds")})
        for f in d.glob("oddsapi_*.json"):
            for ev in json.loads(f.read_text()):
                for bk in ev.get("bookmakers", []):
                    for m in bk.get("markets", []):
                        for oc in m.get("outcomes", []):
                            from .lines import team_from_name
                            rows.append({"ts": d.name, "source": "oddsapi:" + bk.get("key", ""), "market": ev.get("sport_title") or f.stem[8:], "team": team_from_name(oc.get("name")),
                                         "espn_athlete_id": None, "name": oc.get("name"), "line": oc.get("point"), "side": None, "price": oc.get("price")})
    x = pd.DataFrame(rows)
    if len(x):
        x["implied"] = [implied(p) for p in x.price]
        x["no_vig"] = x.implied / x.groupby(["ts", "source", "market"]).implied.transform("sum")
    return x


CONF = {"(A)": "AFC", "(N)": "NFC"}
LEAD = {"passing": "pass", "rushing": "rush", "receiving": "rec"}


def market_key(name: str) -> str | None:
    """ESPN's market names to the page's keys: sb, conf, div, lead_<kind>; None for the rest (awards, most wins)."""
    n = " ".join(str(name).split())
    if re.search(r"super bowl winner", n, re.I):
        return "sb"
    m = re.search(r"\((A|N)\) Conference", n)
    if m:
        return "conf"
    m = re.search(r"\((A|N)\) (East|West|North|South) Division", n)
    if m:
        return "div"
    m = re.search(r"Most Regular Season (Passing|Rushing|Receiving) Yards", n, re.I)
    if m:
        return "lead_" + LEAD[m.group(1).lower()]
    return None


def latest(season: int | None = None) -> dict | None:
    """The newest day's markets as chances with the book's margin taken out: {ts, sources, sb, conf, div: {team: p},
    lead: {kind: {player_id: p}}, books: {market: {team: {book: p}}}}. Team markets average the books that price them
    (DraftKings through ESPN; the Odds API's books for the Super Bowl); each book's chances are its implied chances
    over their sum in that market."""
    x = parse()
    if not len(x):
        return None
    x = x[x.ts == x.ts.max()].copy()
    x["key"] = [("sb" if str(s).startswith("oddsapi") and "Super Bowl" in str(m) else market_key(m)) for s, m in zip(x.source, x.market)]
    x = x[x.key.notna() & x.implied.notna()]
    if (x.source == "oddsapi:draftkings").any():   # DraftKings comes through both sources: count it once
        x = x[~((x.source == "espn:DraftKings") & (x.key == "sb"))]
    x["book"] = x.source.str.split(":").str[1]
    x["p"] = x.implied / x.groupby(["source", "market"]).implied.transform("sum")
    pl = pd.read_parquet(ROOT / "data" / "raw" / "players" / "players.parquet", columns=["gsis_id", "espn_id"]).dropna()
    gs = dict(zip(pd.to_numeric(pl.espn_id, errors="coerce"), pl.gsis_id))
    out = {"ts": str(x.ts.iloc[0]), "sources": sorted(set(x.source)), "lead": {}, "books": {}}
    for k in ("sb", "conf", "div"):
        t = x[(x.key == k) & x.team.notna()]
        out[k] = {tm: round(float(g.p.mean()), 4) for tm, g in t.groupby("team")}
        out["books"][k] = {tm: {b: round(float(v), 4) for b, v in zip(g.book, g.p)} for tm, g in t.groupby("team")}
    for k in ("pass", "rush", "rec"):
        t = x[x.key == "lead_" + k].copy(); t["pid"] = t.espn_athlete_id.map(lambda a: gs.get(a) if pd.notna(a) else None)
        out["lead"][k] = {pid: round(float(g.p.mean()), 4) for pid, g in t[t.pid.notna()].groupby("pid")}
    return out


if __name__ == "__main__":
    if "--fetch" in sys.argv:
        fetch(force="--force" in sys.argv)
    if "--parse" in sys.argv:
        x = parse(); x.to_csv(LOG, index=False); print(len(x), "rows"); print(x.groupby(["source", "market"]).size().to_string() if len(x) else "")
