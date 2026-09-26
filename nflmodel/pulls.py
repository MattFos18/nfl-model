"""When every line source was last pulled (24 Sep 2026). Read from the logs themselves, so the times on the page are
the times the rows were written: the game-line log (ESPN every line-watch run; The Odds API's sportsbooks once a
day), the prop-line log (The Odds API's sportsbooks on Thursday and Sunday; PrizePicks and Underdog every six hours),
the kickoff forecasts and the live check of injuries and starters. Each row carries the time after which the page
calls it late (its cadence plus slack), and the newest line-watch error for that source, if any.

Written into web/data/fresh.js by nflmodel/refresh.py (every line-watch run and the end of every model run)."""
from __future__ import annotations
import datetime as dt
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LN, WX = ROOT / "data" / "lines", ROOT / "data" / "weather"
ODDS_ANCHOR = [(None, 12, 0.0)]      # The Odds API game lines: once a day at 12:00 UTC (lines.py)
EVERY_RUN_LATE_H = 2.0               # a source pulled on every line-watch run is late after two hours
MODEL_LATE_H = 96.0                  # the model run re-prices on every input change and at least four times a week
LATE_H = {"every_run": EVERY_RUN_LATE_H, "model": MODEL_LATE_H}   # the page's freshness limits for what is not a pull (tie checks, the model run)


def _z(t) -> str | None:
    return None if t is None or pd.isna(t) else pd.Timestamp(t).strftime("%Y-%m-%dT%H:%MZ")


def _errors() -> dict:
    """The newest line-watch run's errors by source prefix."""
    f = LN / "watch_log.csv"
    if not f.exists():
        return {}
    last = pd.read_csv(f).tail(1)
    txt = str(last.errors.iloc[0]) if len(last) and pd.notna(last.errors.iloc[0]) else ""
    return {e.split(":", 1)[0].strip(): e.split(":", 1)[1].strip() for e in txt.split(";") if ":" in e}


def status(checked: str | None = None, check_errors: list[str] | None = None) -> list[dict]:
    """One row per source: label, last (UTC), every (cadence), late_after (UTC), error. `checked` is the live check's
    time (injuries, starters) and `check_errors` its errors."""
    from . import lines as L, props_lines as P
    err = _errors(); rows = []
    short = {"espn": "ESPN lines", "oddsapi": "Book lines", "props": "Book props", "prizepicks": "PrizePicks", "underdog": "Underdog", "weather": "Forecasts", "injuries": "Injuries, starters"}
    def add(key, label, last, every, late_after, error=""):
        rows.append({"key": key, "short": short[key], "label": label, "last": _z(last), "every": every, "late_after": _z(late_after), "error": error})
    g = L.load_log()
    if len(g):
        g = g.assign(t=P.log_times(g))
        espn = g[g.source.str.startswith("espn:")].t.max()
        add("espn", "Game lines · ESPN (DraftKings)", espn, "every line-watch run", espn + pd.Timedelta(hours=EVERY_RUN_LATE_H) if pd.notna(espn) else None, err.get("espn", ""))
        oa = g[g.source.str.startswith("oddsapi:")]
        t = oa.t.max()
        n = oa[oa.t == t].source.nunique() if pd.notna(t) else 0
        add("oddsapi", f"Game lines · {n} sportsbooks (The Odds API)" if n else "Game lines · sportsbooks (The Odds API)", t, "once a day, 8:00 AM ET",
            P.next_anchor(t.to_pydatetime(), ODDS_ANCHOR) + dt.timedelta(hours=3) if pd.notna(t) else None, err.get("oddsapi", ""))
    p = P.load_log()
    if len(p):
        p = p.assign(t=P.log_times(p))
        bk = p[~p.book.isin(P.PICKEM)]; t = bk.t.max()
        n = bk[bk.t == t].book.nunique() if pd.notna(t) else 0
        add("props", f"Player props · {n} sportsbooks (The Odds API)" if n else "Player props · sportsbooks (The Odds API)", t, "Thursday 4:00 PM and Sunday 10:00 AM ET",
            P.next_anchor(t.to_pydatetime(), P.PROP_ANCHORS) + dt.timedelta(hours=3) if pd.notna(t) else None, err.get("props", ""))
        for b, lab in [("prizepicks", "PrizePicks"), ("underdog", "Underdog")]:
            t = p[p.book == b].t.max()
            add(b, f"Player props · {lab}", t, "every 6 hours", t + pd.Timedelta(hours=8) if pd.notna(t) else None, err.get("props", ""))
    fl = WX / "forecast_latest.csv"
    if fl.exists():
        t = pd.to_datetime(pd.read_csv(fl, usecols=["fetched_at"]).fetched_at, errors="coerce").max()   # written in ET
        t = t.tz_localize("America/New_York").tz_convert("UTC").tz_localize(None) if pd.notna(t) else t
        add("weather", "Kickoff forecasts (Open-Meteo)", t, "every line-watch run", t + pd.Timedelta(hours=EVERY_RUN_LATE_H) if pd.notna(t) else None,
            next((e.split(":", 1)[1].strip() for e in (check_errors or []) if e.startswith("weather")), ""))
    if checked:
        t = pd.Timestamp(checked.replace(" UTC", ""))
        add("injuries", "Injury reports and named starters", t, "every line-watch run", t + pd.Timedelta(hours=EVERY_RUN_LATE_H),
            "; ".join(e for e in (check_errors or []) if not e.startswith("weather")))
    return rows


if __name__ == "__main__":
    import json
    print(json.dumps(status(pd.Timestamp.now("UTC").strftime("%Y-%m-%d %H:%M UTC")), indent=1))
