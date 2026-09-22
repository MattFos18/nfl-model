"""Download raw nflverse data. Every pull is logged to data/raw/pull_log.csv.

Usage: python -m nflmodel.pull [--seasons 2012-2026] [--only pbp,schedules,...]
"""
from __future__ import annotations
import argparse, datetime as dt, hashlib, os, sys, time
from pathlib import Path
import requests

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
    _log(rows)
    return rows


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
