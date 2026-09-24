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


if __name__ == "__main__":
    if "--fetch" in sys.argv:
        fetch()
