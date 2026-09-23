"""Download raw nflverse data. Every pull is logged to data/raw/pull_log.csv.

Usage: python -m nflmodel.pull [--seasons 2012-2026] [--only pbp,schedules,...]
"""
from __future__ import annotations
import json
import argparse, datetime as dt, hashlib, os, sys, time
from pathlib import Path
import pandas as pd, requests

BASE = "https://github.com/nflverse/nflverse-data/releases/download"
RAW = Path(__file__).resolve().parent.parent / "data" / "raw"

# dataset -> (url template, first season available, one file for all seasons?)
DATASETS = {
    "schedules":     ("schedules/games.csv", 1999, True),
    "pbp":           ("pbp/play_by_play_{s}.parquet", 1999, False),
    "injuries":      ("injuries/injuries_{s}.parquet", 2009, False),
    "snap_counts":   ("snap_counts/snap_counts_{s}.parquet", 2012, False),
    "depth_charts":  ("depth_charts/depth_charts_{s}.parquet", 2001, False),
    "rosters":       ("weekly_rosters/roster_weekly_{s}.parquet", 2002, False),
    "ftn":           ("ftn_charting/ftn_charting_{s}.parquet", 2022, False),
    "pfr_advstats":  ("pfr_advstats/advstats_week_def_{s}.parquet", 2018, False),
    "participation": ("pbp_participation/pbp_participation_{s}.parquet", 2016, False),   # every play: formation, personnel, box, rushers, pressure, man/zone and coverage family, players on the field   # coverage: targets, completions, yards and TDs allowed per defender (Pro Football Reference via nflverse)
}

PBP_COLS = None  # keep everything; we subset when building features


def _log(rows):
    p = RAW / "pull_log.csv"
    new = not p.exists()
    with open(p, "a") as f:
        if new:
            f.write("pulled_at,dataset,season,url,status,bytes,sha256\n")
        for r in rows:
            f.write(",".join(str(x) for x in r) + "\n")


def fetch(url: str, dest: Path, force=False) -> tuple[str, int, str]:
    if dest.exists() and not force:
        return "cached", dest.stat().st_size, ""
    for attempt in range(3):
        try:
            r = requests.get(url, timeout=120)
            if r.status_code == 404:
                return "missing", 0, ""
            r.raise_for_status()
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(r.content)
            return "ok", len(r.content), hashlib.sha256(r.content).hexdigest()[:12]
        except Exception as e:  # noqa
            time.sleep(2 * (attempt + 1))
            err = str(e)
    return f"error:{err[:60]}", 0, ""


def pull(seasons, only=None, force_current=True):
    now = dt.datetime.utcnow().isoformat(timespec="seconds")
    cur = max(seasons)
    rows = []
    for name, (tmpl, first, single) in DATASETS.items():
        if only and name not in only:
            continue
        targets = [(None, tmpl)] if single else [(s, tmpl.format(s=s)) for s in seasons if s >= first]
        for s, path in targets:
            url = f"{BASE}/{path}"
            dest = RAW / name / Path(path).name
            # always refresh the current season and single files (they change in season)
            force = force_current and (single or s == cur)
            status, nbytes, sha = fetch(url, dest, force=force)
            rows.append((now, name, s or "all", url, status, nbytes, sha))
            print(f"{name:12} {s or 'all':>5} {status:8} {nbytes/1e6:7.1f} MB", flush=True)
    if not only or "injuries" in only:
        espn_injuries()
    _log(rows)
    return rows


ESPN_INJ = ["https://site.api.espn.com/apis/site/v2/sports/football/nfl/injuries",
            "https://site.web.api.espn.com/apis/site/v2/sports/football/nfl/injuries",
            "https://cdn.espn.com/core/nfl/injuries?xhr=1"]
ESPN_TEAM = {"WSH": "WAS", "LAR": "LA", "JAC": "JAX"}
ESPN_COLS = ["team", "name", "position", "status", "date", "detail", "return_date", "fetched_at"]


def espn_injuries() -> pd.DataFrame:
    """ESPN's injury page for every team, as posted (same day as the team's report), saved beside the nflverse file:
    data/raw/injuries/espn_injuries.csv with team, name, position, status, date, detail. nflverse's file follows the
    league's reports with a lag of hours to a day; this fills the current week until it does (players.load_injuries).
    Fetched the way the line watch fetches ESPN's scoreboard (browser headers, three hosts in turn). When every host
    refuses, the previous file is kept and its age printed; the pull never fails on it."""
    from .lines import H, _get_json
    dest = RAW / "injuries" / "espn_injuries.csv"; dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        j, used = _get_json(ESPN_INJ, H)
        teams = j.get("injuries") if isinstance(j.get("injuries"), list) else ((j.get("content") or {}).get("injuries") or [])
        rows = []
        for t in teams:
            abbr = ((t.get("team") or {}).get("abbreviation")) or (t.get("displayName") or "")
            for a in t.get("injuries", []):
                ath = a.get("athlete") or {}; det = a.get("details") or {}
                rows.append({"team": ESPN_TEAM.get(abbr, abbr), "name": ath.get("displayName"), "position": (ath.get("position") or {}).get("abbreviation"), "status": a.get("status"), "date": a.get("date"), "detail": det.get("type") or "", "return_date": det.get("returnDate") or "", "fetched_at": dt.datetime.utcnow().isoformat(timespec="seconds")})
        if not rows:
            raise RuntimeError(f"no injuries in the answer from {used.split('/')[2]}")
        out = pd.DataFrame(rows, columns=ESPN_COLS); out.to_csv(dest, index=False)
        (RAW / "injuries" / "espn_injuries.json").write_text(json.dumps(j)[:5_000_000])
        print(f"espn injuries {len(out)} rows, {out.team.nunique()} teams, from {used.split('/')[2]}", flush=True)
        return out
    except Exception as e:  # noqa
        prev = pd.read_csv(dest) if dest.exists() else pd.DataFrame(columns=ESPN_COLS)
        kept = f"kept the file from {prev.fetched_at.max()}" if len(prev) else "no file to keep; the nflverse report alone"
        print(f"espn injuries: {str(e)[:160]}; {kept}", flush=True)
        return prev


def parse_seasons(s: str):
    a, b = s.split("-") if "-" in s else (s, s)
    return list(range(int(a), int(b) + 1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seasons", default="2012-2026")
    ap.add_argument("--only", default=None)
    ap.add_argument("--no-force", action="store_true")
    a = ap.parse_args()
    pull(parse_seasons(a.seasons), a.only.split(",") if a.only else None, not a.no_force)
