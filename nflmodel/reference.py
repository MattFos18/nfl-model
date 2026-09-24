"""Outside reference pages for the player-value checks (24 Sep 2026): the AP All-Pro teams from Wikipedia (one page a
season since 2016) and the published 2026 position rankings (ESPN's survey of executives, coaches and scouts, PFF,
FOX, SI). Saved raw under data/reference/ by .github/workflows/reference.yml, since the runner can reach them; the
parsers (allpro(), below) read the saved pages. Usage: python -m nflmodel.reference --fetch"""
from __future__ import annotations
import json, re, sys, time
import pandas as pd, requests
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REF = ROOT / "data" / "reference"
UA = {"User-Agent": "nfl-model/1.0 (https://github.com/MattFos18/nfl-model; reference pages for player-value checks)"}
CONSENSUS = {
    "cb_espn_2026": "https://www.espn.com/nfl/story/_/id/49232779/ranking-nfl-top-10-cornerbacks-2026-execs-coaches-scouts",
    "cb_pff_2026": "https://www.pff.com/news/pff-cornerback-rankings-the-top-32-players-entering-the-2026-nfl-season",
    "cb_fox_2026": "https://www.foxsports.com/stories/nfl/2026-nfl-top-10-cbs-which-cornerback-best-league",
    "s_espn_2026": "https://www.espn.com/nfl/story/_/id/49307927/ranking-nfl-top-10-safeties-2026-execs-coaches-scouts",
    "s_pff_2026": "https://www.pff.com/news/pff-safety-rankings-the-top-32-players-ahead-of-the-2026-nfl-season",
    "s_si_2026": "https://www.si.com/nfl/ranking-10-best-nfl-safeties-2026-talanoa-hufanga-kyle-hamilton",
    "lb_pff_2026": "https://www.pff.com/news/pff-linebacker-rankings-the-top-32-players-ahead-of-the-2026-nfl-season",
    "edge_pff_2026": "https://www.pff.com/news/pff-edge-defender-rankings-the-top-32-players-ahead-of-the-2026-nfl-season",
    "idl_pff_2026": "https://www.pff.com/news/pff-interior-defender-rankings-the-top-32-players-ahead-of-the-2026-nfl-season",
    "wr_pff_2026": "https://www.pff.com/news/nfl-wide-receiver-rankings-2006",
    "rb_pff_2026": "https://www.pff.com/news/pff-running-back-rankings-assessing-all-32-starters-ahead-of-the-2026-nfl-season",
    "te_pff_2026": "https://www.pff.com/news/pff-tight-end-rankings-the-top-32-players-ahead-of-the-2026-nfl-season",
    "olunit_pff_2026": "https://www.pff.com/news/nfl-offensive-line-rankings-2026",
}


def fetch(seasons=range(2016, 2026)) -> None:
    (REF / "allpro").mkdir(parents=True, exist_ok=True); (REF / "consensus").mkdir(parents=True, exist_ok=True)
    for s in seasons:
        f = REF / "allpro" / f"{s}.html"
        try:
            r = requests.get("https://en.wikipedia.org/w/api.php", params={"action": "parse", "page": f"{s} All-Pro Team", "prop": "text", "format": "json", "formatversion": 2, "redirects": 1}, headers=UA, timeout=30)
            r.raise_for_status(); html = r.json()["parse"]["text"]; f.write_text(html); print(s, "all-pro", len(html), flush=True)
        except Exception as e:  # noqa
            print(s, "all-pro failed", str(e)[:120], flush=True)
        time.sleep(1)
    for k, u in CONSENSUS.items():
        try:
            r = requests.get(u, headers={**UA, "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"}, timeout=30)
            print(k, r.status_code, len(r.text), flush=True)
            if r.ok:
                (REF / "consensus" / f"{k}.html").write_text(r.text)
        except Exception as e:  # noqa
            print(k, "failed", str(e)[:120], flush=True)


TEAMS = {"Arizona": "ARI", "Atlanta": "ATL", "Baltimore": "BAL", "Buffalo": "BUF", "Carolina": "CAR", "Chicago": "CHI", "Cincinnati": "CIN",
         "Cleveland": "CLE", "Dallas": "DAL", "Denver": "DEN", "Detroit": "DET", "Green Bay": "GB", "Houston": "HOU", "Indianapolis": "IND",
         "Jacksonville": "JAX", "Kansas City": "KC", "Las Vegas": "LV", "Oakland": "LV", "Los Angeles Chargers": "LAC", "San Diego": "LAC",
         "Los Angeles Rams": "LA", "Miami": "MIA", "Minnesota": "MIN", "New England": "NE", "New Orleans": "NO", "New York Giants": "NYG",
         "New York Jets": "NYJ", "Philadelphia": "PHI", "Pittsburgh": "PIT", "San Francisco": "SF", "Seattle": "SEA", "Tampa Bay": "TB",
         "Tennessee": "TEN", "Washington": "WAS"}
POS = {"Edge rusher": "EDGE", "Defensive end": "EDGE", "Outside linebacker": "EDGE", "Interior lineman": "IDL", "Defensive tackle": "IDL",
       "Interior lineman/Defensive tackle": "IDL", "Linebacker": "LB", "Inside linebacker": "LB", "Cornerback": "CB", "Defensive back": "CB",
       "Safety": "S", "Quarterback": "QB", "Running back": "RB", "Wide receiver": "WR", "Tight end": "TE", "Left tackle": "OL", "Right tackle": "OL",
       "Tackle": "OL", "Left guard": "OL", "Right guard": "OL", "Guard": "OL", "Center": "OL", "Placekicker": "K", "Punter": "P"}
_norm = lambda v: "".join(ch for ch in str(v).lower() if ch.isalpha())
_bare = lambda v: re.sub(r"\s+(jr\.?|sr\.?|ii|iii|iv|v)$", "", str(v).strip(), flags=re.I)   # without a suffix


def allpro() -> pd.DataFrame:
    """The AP's All-Pro first and second teams since 2016, one row per player: season, group (EDGE, IDL, LB, CB, S, QB,
    RB, WR, TE, OL, K, P), team (1 or 2), name, club, gsis id (matched by name inside that season's rosters)."""
    import io
    rows = []
    for f in sorted((REF / "allpro").glob("*.html")):
        season = int(f.stem)
        for t in pd.read_html(io.StringIO(f.read_text())):
            if not (isinstance(t.columns, pd.MultiIndex) and t.columns[0][0] in ("Offense", "Defense", "Special teams")):
                continue
            for _, r in t.iterrows():
                grp = POS.get(str(r.iloc[0]).strip())
                if not grp:
                    continue
                for col, level in ((1, 1), (2, 2)):
                    cell = str(r.iloc[col]) if pd.notna(r.iloc[col]) else ""
                    for name, club, tags in re.findall(r"\s*([^,()]+?), ([^()]+?) \(([^)]*)\)", cell):
                        tags = [x.strip() for x in tags.split(",")]
                        if ("AP" in tags and level == 1) or ("AP-2" in tags and level == 2):
                            rows.append({"season": season, "group": grp, "level": level, "name": name.strip(), "club": TEAMS.get(club.strip(), club.strip())})
    a = pd.DataFrame(rows).drop_duplicates(["season", "group", "name"])
    ids = []
    for s_, g in a.groupby("season"):
        rf = ROOT / "data" / "raw" / "rosters" / f"roster_weekly_{s_}.parquet"
        if not rf.exists():
            ids += [None] * len(g); continue
        rr = pd.read_parquet(rf, columns=["full_name", "football_name", "last_name", "team", "gsis_id"]).dropna(subset=["gsis_id"]).drop_duplicates(["gsis_id", "team"])
        by, last = {}, {}
        for x in rr.itertuples():
            for nm in {x.full_name, f"{x.football_name} {x.last_name}"}:
                by.setdefault(_norm(nm), set()).add((x.team, x.gsis_id)); by.setdefault(_norm(_bare(nm)), set()).add((x.team, x.gsis_id))
            last.setdefault((_norm(_bare(str(x.last_name))), x.team), set()).add(x.gsis_id)
        for x in g.itertuples():
            c = by.get(_norm(x.name), set()) or by.get(_norm(_bare(x.name)), set())
            if not c:   # a first-name variant (Patrick / Pat): the last name on his club
                c = {(x.club, pid) for pid in last.get((_norm(_bare(x.name.split()[-1] if _bare(x.name) == x.name else _bare(x.name).split()[-1])), x.club), set())}
            pick = [pid for tm, pid in c if tm == x.club] or [pid for _, pid in c]
            ids.append(pick[0] if len(set(pick)) == 1 else (pick[0] if pick else None))
    a["gsis_id"] = ids
    return a


def consensus() -> pd.DataFrame:
    """The saved 2026 position rankings as rows (source, group, rank, name, gsis id): the numbered lists in each page."""
    import html as H
    rows = []
    for f in sorted((REF / "consensus").glob("*.html")):
        grp, src, yr = f.stem.split("_"); t = f.read_text()
        if not t:
            continue
        txt = H.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t)))
        seen = set()
        for n, name in re.findall(r"(?:^| )(\d{1,2})\. ([A-Z][A-Za-z.'\-]+(?: [A-Z][A-Za-z.'\-]+){1,3})", txt):
            if int(n) <= 32 and int(n) not in seen:
                seen.add(int(n)); rows.append({"source": src, "season": int(yr), "group": grp.upper(), "rank": int(n), "name": name})
    c = pd.DataFrame(rows)
    if not len(c):
        return c
    rr = pd.read_parquet(ROOT / "data" / "raw" / "rosters" / f"roster_weekly_{int(c.season.max())}.parquet", columns=["full_name", "football_name", "last_name", "gsis_id"]).dropna().drop_duplicates("gsis_id")
    by = {}
    for x in rr.itertuples():
        for nm in {x.full_name, f"{x.football_name} {x.last_name}", _bare(x.full_name)}:
            by.setdefault(_norm(nm), x.gsis_id)
    def match(n):   # some pages run the club into the name ("Pat Surtain II Denver"): try the first 4, 3, 2 words
        w = n.split()
        for k in (len(w), 4, 3, 2):
            nm = " ".join(w[:k])
            pid = by.get(_norm(nm)) or by.get(_norm(_bare(nm)))
            if pid:
                return nm, pid
        return n, None
    m = [match(n) for n in c.name]
    c["name"] = [x[0] for x in m]; c["gsis_id"] = [x[1] for x in m]
    return c


if __name__ == "__main__":
    if "--fetch" in sys.argv:   # the workflow only fetches (it has no roster files); parsing runs where the rosters are
        fetch(); sys.exit(0)
    c = consensus(); c.to_csv(REF / "consensus_2026.csv", index=False); print("consensus rows", len(c), "unmatched", int(c.gsis_id.isna().sum()) if len(c) else 0)
    a = allpro(); a.to_csv(REF / "allpro.csv", index=False); print("all-pro rows", len(a), "unmatched", int(a.gsis_id.isna().sum()))
