"""Betting splits: the share of bets and the share of money on each side of every NFL game's spread, total and moneyline,
from DraftKings Network's public splits page (29 Sep 2026, Matt: show them on the Breakdown cards). The page is server
rendered: one block per game ("PIT Steelers @ CLE Browns", kickoff), then a block per market with a row per side (side,
odds, % handle, % bets). The line watch calls run() every snapshot; each run appends to data/lines/splits_log.csv and
rewrites data/lines/splits_latest.csv. Display only: no split is an input to any projection (market numbers stay out of
the model), and the log is kept so the splits can be studied once a season of it, or a bought history, exists.
The retired Covers attempt (lines.draftkings_splits) matched percentages near abbreviations and failed 59 of 62 runs."""
from __future__ import annotations
import argparse, datetime as dt, html as H, re, time
import pandas as pd, requests
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LN = ROOT / "data" / "lines"
OUT = ROOT / "data" / "processed"
URL = "https://dknetwork.draftkings.com/draftkings-sportsbook-betting-splits/"
NFL_GROUP = "88808"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"}
NICK = {"Cardinals": "ARI", "Falcons": "ATL", "Ravens": "BAL", "Bills": "BUF", "Panthers": "CAR", "Bears": "CHI", "Bengals": "CIN", "Browns": "CLE",
        "Cowboys": "DAL", "Broncos": "DEN", "Lions": "DET", "Packers": "GB", "Texans": "HOU", "Colts": "IND", "Jaguars": "JAX", "Chiefs": "KC",
        "Raiders": "LV", "Chargers": "LAC", "Rams": "LA", "Dolphins": "MIA", "Vikings": "MIN", "Patriots": "NE", "Saints": "NO", "Giants": "NYG",
        "Jets": "NYJ", "Eagles": "PHI", "Steelers": "PIT", "Seahawks": "SEA", "49ers": "SF", "Buccaneers": "TB", "Titans": "TEN", "Commanders": "WAS"}
MARKETS = {"moneyline": "ml", "spread": "spread", "total": "total"}


def _team(label: str):
    for w in reversed(label.split()):
        if w in NICK:
            return NICK[w]
    return None


def _texts(fragment: str) -> list[str]:
    frag = re.sub(r"<(script|style)\b.*?</\1>", "", fragment, flags=re.S)
    return [t for t in (H.unescape(x).strip() for x in re.findall(r">([^<>]+)<", frag)) if t]


def parse(page: str) -> list[dict]:
    """Every (game, market, side) row on one page of the splits table."""
    rows = []
    for block in re.split(r'class="tb-se\s', page)[1:]:
        head = re.search(r"<h5[^>]*>(.*?)</h5>", block, flags=re.S)
        title = " ".join(_texts(head.group(0))) if head else ""
        if "@" not in title:
            continue
        away_l, home_l = [s.strip() for s in title.split("@", 1)]
        away, home = _team(away_l), _team(home_l)
        if not (away and home):
            continue
        after = block[head.end():] if head else block
        when = _texts(after[:400])[:1]
        for seg in re.split(r'class="tb-se-head\b', after)[1:]:
            hdr = _texts(seg[:600])
            market = MARKETS.get((hdr[0] if hdr else "").lower())
            if market is None:
                continue
            for row in re.split(r'class="tb-sodd\b', seg)[1:]:
                tok = _texts(row.split('class="tb-sodd')[0])
                pcts = [int(t[:-1]) for t in tok if re.fullmatch(r"\d{1,3}%", t)]
                if len(pcts) < 2:
                    continue
                side = tok[0]
                odds = next((t for t in tok[1:] if re.fullmatch(r"[+\-−]\d{3,4}|EVEN|even", t)), None)
                line = re.search(r"([+\-−]?\d+(?:\.\d)?)\s*$", side) if market != "ml" else None
                rows.append({"away": away, "home": home, "kickoff_text": when[0] if when else "", "market": market, "side_label": side,
                             "side": ("over" if side.lower().startswith("over") else "under" if side.lower().startswith("under") else _team(side)),
                             "line": float(line.group(1).replace("−", "-")) if line else None,
                             "odds": int(odds.replace("−", "-")) if odds and odds.lower() != "even" else (100 if odds else None),
                             "handle_pct": pcts[0], "bets_pct": pcts[1]})
    return rows


def fetch(max_pages: int = 6) -> list[dict]:
    rows, seen = [], set()
    for p in range(1, max_pages + 1):
        r = requests.get(URL, params={"tb_eg": NFL_GROUP, "tb_edate": "n7days", "tb_emt": "0", "tb_page": p}, headers=UA, timeout=30)
        r.raise_for_status()
        got = [x for x in parse(r.text) if (x["away"], x["home"], x["market"], x["side_label"]) not in seen]
        if not got:
            break
        seen |= {(x["away"], x["home"], x["market"], x["side_label"]) for x in got}
        rows += got
        time.sleep(1.0)
    return rows


def attach(rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    if not len(df):
        return df
    g = pd.read_parquet(OUT / "games.parquet")
    g = g[g.home_score.isna()][["game_id", "away_team", "home_team", "kickoff_et"]].sort_values("kickoff_et")
    first = g.drop_duplicates(["away_team", "home_team"])   # the next meeting of this pair
    df = df.merge(first.rename(columns={"away_team": "away", "home_team": "home"})[["game_id", "away", "home"]], on=["away", "home"], how="left")
    return df


def run() -> pd.DataFrame:
    ts = dt.datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%SZ")
    df = attach(fetch())
    if not len(df):
        raise RuntimeError("splits page fetched but no rows recognised")
    df.insert(0, "ts", ts); df.insert(1, "source", "dknetwork")
    LN.mkdir(parents=True, exist_ok=True)
    log = LN / "splits_log.csv"
    df.to_csv(log, mode="a", header=not log.exists(), index=False)
    df.to_csv(LN / "splits_latest.csv", index=False)
    return df


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--dry", action="store_true", help="fetch and print, write nothing"); a = ap.parse_args()
    if a.dry:
        df = attach(fetch())
        pd.set_option("display.width", 220); pd.set_option("display.max_rows", 200)
        print(df.to_string(index=False) if len(df) else "no rows")
        print("games:", df.game_id.nunique() if len(df) else 0, "| rows:", len(df), "| unmatched:", int(df.game_id.isna().sum()) if len(df) else 0)
    else:
        print(run().shape)
