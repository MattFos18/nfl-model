"""Live refresh check (24 Sep 2026). Every line-watch run (every 30 minutes) also pulls everything else that can
change between model runs and that the model uses: the schedule's named starting QBs and kickoff times, the
league's injury reports (nflverse) and ESPN's same-day page, and the kickoff forecasts. It fingerprints what the
model would see for the week being priced and compares it with the fingerprint of the last model run
(data/runs/inputs_fingerprint.json, written by the weekly run). When something the model uses has changed, the
line watch starts the weekly run, which re-prices every game, prop, season odd and player total from the same
moment's data (it pulls lines first).

What counts as a change:
  starters     a named QB or a kickoff time changed for a game this week
  injuries     a player moved into or out of Out or Doubtful (the statuses the model counts), league or ESPN
  weather      inside the forecast window the model uses: wind moved 2 mph or more, or the cold (under 35F) or
               rain call flipped. Weather-only changes re-price at most once every two hours.

python -m nflmodel.refresh --check   pull, compare, print the reasons, and write reprice=1|0 to $GITHUB_OUTPUT
python -m nflmodel.refresh --write   write the fingerprint of what is on disk now (the weekly run, at its end)
"""
from __future__ import annotations
import json, os, sys, datetime as dt
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT, RAW, RUNS, WEB = ROOT / "data" / "processed", ROOT / "data" / "raw", ROOT / "data" / "runs", ROOT / "web" / "data"
FP = RUNS / "inputs_fingerprint.json"
WIND_STEP, WEATHER_GAP_H = 2.0, 2.0


def fingerprint() -> dict:
    """What the model would see for the week being priced, from the files on disk."""
    from .lines import current_week
    from . import players as PL, weather as WX
    games = pd.read_parquet(OUT / "games.parquet"); season, week = current_week(games)
    wk = games[(games.season == season) & (games.week == week)]
    teams = set(wk.home_team) | set(wk.away_team)
    fp = {"season": int(season), "week": int(week), "starters": {}, "injuries": [], "weather": {}}
    sf = RAW / "schedules" / "games.csv"
    if sf.exists():
        s = pd.read_csv(sf, usecols=["game_id", "season", "week", "gameday", "gametime", "home_qb_id", "away_qb_id"])
        s = s[(s.season == season) & (s.week == week)]
        fp["starters"] = {r.game_id: [str(r.home_qb_id) if isinstance(r.home_qb_id, str) else "", str(r.away_qb_id) if isinstance(r.away_qb_id, str) else "", f"{r.gameday} {r.gametime}"] for r in s.itertuples()}
    out_like = {"Out", "Doubtful"}
    inj = set()
    nf = RAW / "injuries" / f"injuries_{season}.parquet"
    if nf.exists():
        n = pd.read_parquet(nf, columns=["week", "team", "full_name", "report_status"])
        n = n[(n.week == week) & n.report_status.isin(out_like)]
        inj |= {(t, str(nm), st) for t, nm, st in zip(n.team, n.full_name, n.report_status)}
    ef = RAW / "injuries" / "espn_injuries.csv"
    if ef.exists():
        e = pd.read_csv(ef)
        if len(e):
            age = (pd.Timestamp.now("UTC").tz_localize(None) - pd.to_datetime(e.fetched_at, errors="coerce")).dt.total_seconds() / 86400
            e = e[(age <= PL.ESPN_MAX_AGE_DAYS) & e.team.isin(teams)]
            e = e.assign(st=e.status.map(PL.ESPN_STATUS)); e = e[e.st.isin(out_like)]
            inj |= {(t, str(nm), st) for t, nm, st in zip(e.team, e.name, e.st)}
    fp["injuries"] = sorted([list(x) for x in inj])
    try:
        fc = WX.usable_forecast()
        for gid in wk.game_id:
            if gid in fc.index:
                r = fc.loc[gid]
                fp["weather"][gid] = {"wind": round(float(r.wind), 1) if pd.notna(r.wind) else None, "cold": bool(pd.notna(r.temp) and r.temp < 35),
                                      "rain": bool(pd.notna(r.get("precip", None)) and float(r.get("precip", 0) or 0) > 0)}
    except Exception:  # noqa
        pass
    return fp


def diff(old: dict, new: dict) -> list[tuple[str, str]]:
    """(kind, what) for every model-relevant change."""
    if not old or (old.get("season"), old.get("week")) != (new["season"], new["week"]):
        return [("week", f"week {new['week']} of {new['season']} has no model run on record")]
    out = []
    for gid, v in new["starters"].items():
        o = old.get("starters", {}).get(gid)
        if o and o[:2] != v[:2]:
            out.append(("starters", f"{gid}: named QB changed"))
        if o and o[2] != v[2]:
            out.append(("starters", f"{gid}: kickoff moved to {v[2]}"))
    a, b = {tuple(x) for x in old.get("injuries", [])}, {tuple(x) for x in new["injuries"]}
    for t, nm, st in sorted(b - a):
        out.append(("injuries", f"{t} {nm} now {st}"))
    for t, nm, st in sorted(a - b):
        if not any((t, nm) == (x[0], x[1]) for x in b):
            out.append(("injuries", f"{t} {nm} no longer {st}"))
    for gid, w in new["weather"].items():
        o = old.get("weather", {}).get(gid)
        if o is None:
            out.append(("weather", f"{gid}: forecast now inside the window the model uses"))
            continue
        if w["wind"] is not None and o.get("wind") is not None and abs(w["wind"] - o["wind"]) >= WIND_STEP:
            out.append(("weather", f"{gid}: wind {o['wind']:.0f} to {w['wind']:.0f} mph"))
        if w["cold"] != o.get("cold") or w["rain"] != o.get("rain"):
            out.append(("weather", f"{gid}: cold or rain call changed"))
    return out


def _pulls(checked: str, errors: list[str]) -> list[dict]:
    """Every line source's last pull time for the page's This week strip (nflmodel/pulls.py); never fails the check."""
    try:
        from . import pulls
        return pulls.status(checked, errors)
    except Exception as e:  # noqa
        return [{"key": "error", "label": "Pull times", "last": None, "every": "", "late_after": None, "error": str(e)[:120]}]


def write() -> dict:
    fp = fingerprint(); fp["written_at"] = pd.Timestamp.now("UTC").strftime("%Y-%m-%d %H:%M UTC")
    RUNS.mkdir(parents=True, exist_ok=True); FP.write_text(json.dumps(fp, indent=0))
    WEB.mkdir(parents=True, exist_ok=True)
    (WEB / "fresh.js").write_text("window.FRESH=" + json.dumps({"checked": fp["written_at"], "season": fp["season"], "week": fp["week"], "reprice": False, "changes": [], "errors": [], "note": "the model run pulled and priced with these", "pulls": _pulls(fp["written_at"], [])}) + ";")
    return fp


def check() -> bool:
    """Pull the live sources, compare with the last model run, say whether to re-price."""
    from . import pull, weather
    games = pd.read_parquet(OUT / "games.parquet"); season = int(games.season.max())
    errors = []
    for name, rel in (("schedules", "schedules/games.csv"), ("injuries", f"injuries/injuries_{season}.parquet")):
        try:
            dest = RAW / name / Path(rel).name; dest.parent.mkdir(parents=True, exist_ok=True)
            pull.fetch(f"{pull.BASE}/{rel}", dest, force=True)
        except Exception as e:  # noqa
            errors.append(f"{name}: {str(e)[:80]}")
    try:
        pull.espn_injuries()
    except Exception as e:  # noqa
        errors.append(f"espn: {str(e)[:80]}")
    try:
        weather.run()
    except Exception as e:  # noqa
        errors.append(f"weather: {str(e)[:80]}")
    new = fingerprint()
    old = json.loads(FP.read_text()) if FP.exists() else {}
    changes = diff(old, new)
    kinds = {k for k, _ in changes}
    last_run = None
    rl = RUNS / "run_log.csv"
    if rl.exists():
        t = pd.to_datetime(pd.read_csv(rl, usecols=["run_at"]).run_at.str.replace(" UTC", ""), errors="coerce").max()
        last_run = (pd.Timestamp.now("UTC").tz_localize(None) - t).total_seconds() / 3600 if pd.notna(t) else None
    reprice = bool(kinds - {"weather"}) or (("weather" in kinds) and (last_run is None or last_run >= WEATHER_GAP_H))
    now = pd.Timestamp.now("UTC").strftime("%Y-%m-%d %H:%M UTC")
    status = {"checked": now, "season": new["season"], "week": new["week"], "reprice": reprice, "changes": [w for _, w in changes][:40], "errors": errors,
              "sources": ["lines and props (books, PrizePicks, Underdog)", "named starters and kickoffs (nflverse schedule)", "injury reports (league and ESPN)", "kickoff forecasts (Open-Meteo)"],
              "pulls": _pulls(now, errors)}
    WEB.mkdir(parents=True, exist_ok=True); (WEB / "fresh.js").write_text("window.FRESH=" + json.dumps(status) + ";")
    (RUNS / "refresh_log.csv").parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([{"checked": now, "reprice": reprice, "changes": " | ".join(w for _, w in changes)[:1000], "errors": " | ".join(errors)}]).to_csv(RUNS / "refresh_log.csv", mode="a", header=not (RUNS / "refresh_log.csv").exists(), index=False)
    print(f"refresh check {now}: {'re-price' if reprice else 'no re-price'}; {len(changes)} changes" + (": " + "; ".join(w for _, w in changes[:8]) if changes else "") + (f"; errors: {errors}" if errors else ""), flush=True)
    go = os.environ.get("GITHUB_OUTPUT")
    if go:
        with open(go, "a") as fh:
            fh.write(f"reprice={1 if reprice else 0}\n")
    return reprice


if __name__ == "__main__":
    if "--write" in sys.argv:
        print(json.dumps(write())[:400])
    else:
        check()
