"""Team logos for the page (24 Sep 2026): the 32 NFL logos from ESPN's image server, resized to 64 px, saved as
web/logos/<TEAM>.png under the model's team codes. The page cannot load images from other sites, so the logos are
published with it. Run on GitHub's network (the logos workflow); a logo that fails keeps the previous file.
"""
from __future__ import annotations
import time
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parent.parent
DEST = ROOT / "web" / "logos"
TEAMS = ["ARI", "ATL", "BAL", "BUF", "CAR", "CHI", "CIN", "CLE", "DAL", "DEN", "DET", "GB", "HOU", "IND", "JAX", "KC", "LA", "LAC", "LV", "MIA", "MIN", "NE", "NO", "NYG", "NYJ", "PHI", "PIT", "SEA", "SF", "TB", "TEN", "WAS"]
ESPN = {"LA": "lar", "WAS": "wsh"}
H = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36", "Referer": "https://www.espn.com/"}


def fetch() -> dict:
    DEST.mkdir(parents=True, exist_ok=True); out = {}
    for t in TEAMS:
        code = ESPN.get(t, t.lower())
        urls = [f"https://a.espncdn.com/combiner/i?img=/i/teamlogos/nfl/500/{code}.png&h=64&w=64",
                f"https://a.espncdn.com/i/teamlogos/nfl/500/{code}.png"]
        ok = False
        for u in urls:
            try:
                r = requests.get(u, headers=H, timeout=30); r.raise_for_status()
                if r.content[:8] == b"\x89PNG\r\n\x1a\n" and len(r.content) > 500:
                    (DEST / f"{t}.png").write_bytes(r.content); out[t] = len(r.content); ok = True; break
            except Exception as e:  # noqa
                last = str(e)[:80]
        if not ok:
            out[t] = "failed"
        time.sleep(0.2)
    print(out, flush=True)
    return out


if __name__ == "__main__":
    fetch()
