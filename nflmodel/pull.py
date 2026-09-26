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
    "players":       ("players/players.parquet", 1999, True),
    "ngs":           ("nextgen_stats/ngs_passing.parquet", 2016, True),     # 24 Sep 2026: NFL Next Gen Stats, weekly per player (time to throw, air yards, CPOE)
    "ngs_rec":       ("nextgen_stats/ngs_receiving.parquet", 2016, True),   # separation, cushion, YAC over expected
    "ngs_rush":      ("nextgen_stats/ngs_rushing.parquet", 2016, True),     # rush yards over expected, 8+ box rate, time to the line       # 24 Sep 2026: every player's ids (gsis, PFR, ESPN, PFF...): the rosters carry no PFR id for linemen
    "pbp":           ("pbp/play_by_play_{s}.parquet", 1999, False),
    "injuries":      ("injuries/injuries_{s}.parquet", 2009, False),
    "snap_counts":   ("snap_counts/snap_counts_{s}.parquet", 2012, False),
    "depth_charts":  ("depth_charts/depth_charts_{s}.parquet", 2001, False),
    "rosters":       ("weekly_rosters/roster_weekly_{s}.parquet", 2002, False),
    "ftn":           ("ftn_charting/ftn_charting_{s}.parquet", 2022, False),
    "pfr_advstats":  ("pfr_advstats/advstats_week_def_{s}.parquet", 2018, False),
    "pfr_pass":      ("pfr_advstats/advstats_week_pass_{s}.parquet", 2018, False),   # 24 Sep 2026: the passing, rushing and receiving weekly files too (bad throws,
    "pfr_rush":      ("pfr_advstats/advstats_week_rush_{s}.parquet", 2018, False),   # pressures, drops, broken tackles, yards before and after contact) for the
    "pfr_rec":       ("pfr_advstats/advstats_week_rec_{s}.parquet", 2018, False),    # player game logs
    "player_stats":  ("stats_player/stats_player_week_{s}.parquet", 2016, False),     # nflverse's official box score per player and game: the tie check holds the props grading and the game logs to it
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
    if not only or "injuries" in only or "rosters" in only:
        reserve_reasons()
    _log(rows)
    return rows


ESPN_INJ = ["https://site.api.espn.com/apis/site/v2/sports/football/nfl/injuries",
            "https://site.web.api.espn.com/apis/site/v2/sports/football/nfl/injuries",
            "https://cdn.espn.com/core/nfl/injuries?xhr=1"]
ESPN_TEAM = {"WSH": "WAS", "LAR": "LA", "JAC": "JAX"}
TEAMS = ["ARI", "ATL", "BAL", "BUF", "CAR", "CHI", "CIN", "CLE", "DAL", "DEN", "DET", "GB", "HOU", "IND", "JAX", "KC", "LA", "LAC", "LV", "MIA", "MIN", "NE", "NO", "NYG", "NYJ", "PHI", "PIT", "SEA", "SF", "TB", "TEN", "WAS"]
ESPN_COLS = ["team", "espn_id", "name", "position", "status", "date", "detail", "return_date", "fetched_at"]


def espn_injuries() -> pd.DataFrame:
    """ESPN's injury page for every team, as posted (same day as the team's report), saved beside the nflverse file:
    data/raw/injuries/espn_injuries.csv with team, name, position, status, date, detail. nflverse's file follows the
    league's reports with a lag of hours to a day; this fills the current week until it does (players.load_injuries).
    Fetched the way the line watch fetches ESPN's scoreboard (browser headers, three hosts in turn). When every host
    refuses, the previous file is kept and its age printed; the pull never fails on it."""
    from .lines import H, _get_json, team_from_name
    dest = RAW / "injuries" / "espn_injuries.csv"; dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        j, used = _get_json(ESPN_INJ, H)
        teams = j.get("injuries") if isinstance(j.get("injuries"), list) else ((j.get("content") or {}).get("injuries") or [])
        rows = []
        for t in teams:
            abbr = ((t.get("team") or {}).get("abbreviation")) or ""
            if not (2 <= len(abbr) <= 3):     # some hosts give the team's full name only ("Arizona Cardinals")
                abbr = team_from_name(t.get("displayName") or ((t.get("team") or {}).get("displayName")) or "") or (t.get("displayName") or "")
            for a in t.get("injuries", []):
                ath = a.get("athlete") or {}; det = a.get("details") or {}
                rows.append({"team": ESPN_TEAM.get(abbr, abbr), "espn_id": str(ath.get("id") or ""), "name": ath.get("displayName"), "position": (ath.get("position") or {}).get("abbreviation"), "status": a.get("status"), "date": a.get("date"), "detail": det.get("type") or "", "return_date": det.get("returnDate") or "", "fetched_at": dt.datetime.utcnow().isoformat(timespec="seconds")})
        if not rows:
            raise RuntimeError(f"no injuries in the answer from {used.split('/')[2]}")
        out = pd.DataFrame(rows, columns=ESPN_COLS)
        odd = sorted(set(out.team) - set(TEAMS))
        if odd:
            raise RuntimeError(f"teams not recognised: {odd[:5]}")
        out.to_csv(dest, index=False)
        (RAW / "injuries" / "espn_injuries.json").write_text(json.dumps(j)[:5_000_000])
        print(f"espn injuries {len(out)} rows, {out.team.nunique()} teams, from {used.split('/')[2]}", flush=True)
        return out
    except Exception as e:  # noqa
        prev = pd.read_csv(dest) if dest.exists() else pd.DataFrame(columns=ESPN_COLS)
        kept = f"kept the file from {prev.fetched_at.max()}" if len(prev) else "no file to keep; the nflverse report alone"
        print(f"espn injuries: {str(e)[:160]}; {kept}", flush=True)
        return prev


REASONS_COLS = ["gsis_id", "team", "name", "reason", "source", "date", "fetched_at"]
SLEEPER_PLAYERS = "https://api.sleeper.app/v1/players/nfl"
ESPN_ATHLETE_INJ = "https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/athletes/{id}/injuries?limit=3"


def reserve_reasons(max_age_h: float = 12.0) -> pd.DataFrame:
    """The injury behind each player on a reserve list (IR, PUP, NFI), 26 Sep 2026: the league's report stops listing a
    player once he goes on IR and ESPN's league page keeps only recent ones (A.J. Brown, IR from Week 2, was on neither),
    so this asks two sources that keep every player's current injury, matched by id from nflverse's weekly roster:
    Sleeper's player file (one request, injury_body_part, only when Sleeper lists an injury status) and, for anyone
    left, ESPN's injury record for the athlete (the newest entry dated this season). Writes
    data/raw/injuries/reserve_reasons.csv; re-fetched at most every max_age_h hours (Sleeper asks for about one pull a
    day); never fails the pull."""
    import requests
    from .lines import H
    dest = RAW / "injuries" / "reserve_reasons.csv"; dest.parent.mkdir(parents=True, exist_ok=True)
    prev = pd.read_csv(dest) if dest.exists() else pd.DataFrame(columns=REASONS_COLS)
    if len(prev) and (dt.datetime.utcnow() - pd.to_datetime(prev.fetched_at.max())).total_seconds() < max_age_h * 3600:
        return prev
    try:
        cur = max(int(f.stem.split("_")[-1]) for f in (RAW / "rosters").glob("roster_weekly_*.parquet"))
        r = pd.read_parquet(RAW / "rosters" / f"roster_weekly_{cur}.parquet")
        r = r[r.week == r.week.max()]
        from .players import NOT_AVAILABLE
        r = r[r.status.isin(NOT_AVAILABLE) & r.gsis_id.notna()].drop_duplicates("gsis_id")
        now = dt.datetime.utcnow().isoformat(timespec="seconds"); rows = {}; season_start = f"{cur}-08-01"
        try:   # Sleeper: every player in one file
            sj = requests.get(SLEEPER_PLAYERS, headers=H, timeout=60).json()
            by_sl = {str(k): v for k, v in sj.items()}; by_gsis = {str(v.get("gsis_id")).strip(): v for v in sj.values() if v.get("gsis_id")}
            for x in r.itertuples():
                v = by_sl.get(str(x.sleeper_id).replace(".0", "")) if isinstance(x.sleeper_id, (str, float, int)) and str(x.sleeper_id) not in ("nan", "None", "") else None
                v = v or by_gsis.get(str(x.gsis_id))
                if v and v.get("injury_status") and v.get("injury_body_part"):
                    rows[x.gsis_id] = {"gsis_id": x.gsis_id, "team": x.team, "name": x.full_name, "reason": str(v["injury_body_part"]), "source": "Sleeper", "date": v.get("injury_start_date") or "", "fetched_at": now}
            print(f"reserve reasons: Sleeper named {len(rows)} of {len(r)}", flush=True)
        except Exception as e:  # noqa
            print(f"reserve reasons: Sleeper not read ({str(e)[:120]})", flush=True)
        n_espn = 0
        for x in r.itertuples():   # ESPN's record for anyone Sleeper did not name
            if x.gsis_id in rows or not isinstance(x.espn_id, (str, float, int)) or str(x.espn_id) in ("nan", "None", ""):
                continue
            try:
                lst = requests.get(ESPN_ATHLETE_INJ.format(id=str(x.espn_id).replace(".0", "")), headers=H, timeout=15).json()
                for it in lst.get("items", [])[:3]:
                    d = requests.get(it["$ref"].replace("http://", "https://"), headers=H, timeout=15).json()
                    date = str(d.get("date") or "")[:10]; typ = ((d.get("details") or {}).get("type")) or ((d.get("type") or {}).get("description"))
                    if typ and date >= season_start and typ.lower() not in ("injured reserve", "out", "questionable", "doubtful"):
                        rows[x.gsis_id] = {"gsis_id": x.gsis_id, "team": x.team, "name": x.full_name, "reason": str(typ), "source": "ESPN player page", "date": date, "fetched_at": now}; n_espn += 1; break
            except Exception:  # noqa
                continue
        print(f"reserve reasons: ESPN player pages named {n_espn} more; {len(r) - len(rows)} of {len(r)} without a reason", flush=True)
        out = pd.DataFrame(list(rows.values()), columns=REASONS_COLS)
        if len(out) or not len(prev):
            out.to_csv(dest, index=False)
        return out if len(out) else prev
    except Exception as e:  # noqa
        print(f"reserve reasons: {str(e)[:160]}; kept the previous file", flush=True)
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
