"""Warnings a step raises without failing (2 Oct 2026, code review): a forecast reading that fell back to an older pull or
to one model, a store missing values, a weather reader that failed and priced a game calm. Each prints to stderr and is
kept in data/weather/warnings.json (the weekly run and the line watch both commit data/weather), one entry per distinct
message with when it was first and last seen; health.py shows every message seen in the last WINDOW_H hours as a WARN.
Nothing here changes a reading, a rule or a price."""
from __future__ import annotations
import json, sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
F = ROOT / "data" / "weather" / "warnings.json"
KEEP_DAYS, WINDOW_H = 14, 36
_SEEN: set = set()   # once per process: the readers run many times a run


def warn(source: str, msg: str) -> None:
    key = f"{source}|{msg}"
    if key in _SEEN:
        return
    _SEEN.add(key)
    print(f"WARNING {source}: {msg}", file=sys.stderr, flush=True)
    try:
        d = json.loads(F.read_text()) if F.exists() else {}
        now = pd.Timestamp.now("UTC").strftime("%Y-%m-%d %H:%M UTC")
        e = d.get(key) or {"source": source, "message": msg, "first": now, "count": 0}
        e["last"] = now; e["count"] = int(e.get("count", 0)) + 1; d[key] = e
        cut = (pd.Timestamp.now("UTC") - pd.Timedelta(days=KEEP_DAYS)).strftime("%Y-%m-%d %H:%M UTC")
        d = {k: v for k, v in d.items() if v.get("last", "") >= cut}
        F.parent.mkdir(parents=True, exist_ok=True); F.write_text(json.dumps(d, indent=1, sort_keys=True))
    except Exception as ex:  # noqa  (the warning is already on stderr)
        print(f"WARNING warnlog: could not record the warning above ({type(ex).__name__}: {ex})", file=sys.stderr, flush=True)


def recent(hours: float = WINDOW_H) -> list[dict]:
    """Every warning last seen in the past `hours`, newest first."""
    if not F.exists():
        return []
    d = json.loads(F.read_text())
    cut = (pd.Timestamp.now("UTC") - pd.Timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M UTC")
    return sorted([v for v in d.values() if v.get("last", "") >= cut], key=lambda v: v["last"], reverse=True)
