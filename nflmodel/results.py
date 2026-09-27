"""Live results (27 Sep 2026): what actually happened, as soon as ESPN posts it, graded against what the model said
before kickoff. nflverse posts scores hours later (the weekly run grades the tracker from them on Tuesday); until
then the page showed a finished game as unplayed. Every line-watch run:

  1. fetch the ESPN scoreboard for every week with an unplayed game that has kicked off or kicks off within a day
     (the picks week is the next one by Monday, so the Monday night final is in a week the line watch no longer
     pulls), saved to data/results/scoreboard_<season>_wk<week>.json; without network the saved files stand
  2. one row per game: status (scheduled, in progress, final), the clock, the score
  3. a final is graded against the model's numbers from the last run before kickoff (data/runs/pred_history.csv)
     and the closing line (the newest lines-log snapshot before kickoff; the schedule's line when none was logged):
     the model's side of the spread and of the total, its winner; the logged bets (the flag, the shadow rules,
     Matt's) through tracker.grade_rows at the same close, so the number here is the tracker's number later
  4. a cross-check: where nflverse already has the score it must equal ESPN's (the tie check fails otherwise)

Written to data/results/live_scores.csv and web/data/live.js (the cards, the Bets tab and the report display it).
Usage: python -m nflmodel.results [--no-fetch]
"""
from __future__ import annotations
import glob, json, sys
import numpy as np, pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT, LN, RUNS, TR, RES, WEB = ROOT / "data" / "processed", ROOT / "data" / "lines", ROOT / "data" / "runs", ROOT / "data" / "tracker", ROOT / "data" / "results", ROOT / "web" / "data"
ESPN_ABBR = {"WSH": "WAS", "JAC": "JAX", "LAR": "LA"}
STATE = {"pre": "scheduled", "in": "in_progress", "post": "final"}
LOOKBACK_DAYS = 8   # a week whose game kicked off this long ago and is still unscored in nflverse is still fetched


def clean(v):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return None
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating,)):
        return float(v)
    if isinstance(v, (pd.Timestamp,)):
        return str(v)[:16]
    return v


def weeks_to_fetch(games: pd.DataFrame, now: pd.Timestamp) -> list[tuple[int, int]]:
    """(season, week) of every regular-season week with an unscored game that kicked off inside LOOKBACK_DAYS or kicks
    off within a day, plus the picks week (so upcoming games show as scheduled)."""
    from . import lines as LNM
    g = games[(games.game_type == "REG") & games.home_score.isna() & (games.kickoff_et >= now - pd.Timedelta(days=LOOKBACK_DAYS)) & (games.kickoff_et <= now + pd.Timedelta(days=1))]
    ws = {(int(r.season), int(r.week)) for r in g.itertuples()}
    ws.add(tuple(int(x) for x in LNM.current_week(games)))
    return sorted(ws)


def fetch(season: int, week: int) -> dict:
    from . import lines as LNM
    j, _ = LNM._get_json(["https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard",
                          "https://site.web.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard",
                          "https://cdn.espn.com/core/nfl/scoreboard?xhr=1"], LNM.H, params={"week": week, "seasontype": 2, "dates": season})
    if "events" not in j and "content" in j:
        j = (j.get("content") or {}).get("sbData") or {}
    RES.mkdir(parents=True, exist_ok=True)
    (RES / f"scoreboard_{season}_wk{week}.json").write_text(json.dumps(j)[:5_000_000])
    return j


def saved(season: int, week: int) -> dict | None:
    """The saved scoreboard for the week: this module's file, else the newest line-watch pull of that week."""
    f = RES / f"scoreboard_{season}_wk{week}.json"
    if f.exists():
        return json.loads(f.read_text())
    for p in sorted(glob.glob(str(LN / "raw" / "*_espn.json")), reverse=True):
        try:
            j = json.loads(Path(p).read_text())
        except Exception:  # noqa
            continue
        ev = j.get("events") or []
        if ev and int((ev[0].get("season") or {}).get("year", 0)) == season and int((ev[0].get("week") or {}).get("number", 0)) == week:
            return j
    return None


def parse(j: dict, season: int, week: int) -> pd.DataFrame:
    rows = []
    for ev in (j or {}).get("events", []):
        comp = (ev.get("competitions") or [{}])[0]
        st = (comp.get("status") or ev.get("status") or {}); ty = st.get("type") or {}
        home = away = None; hs = as_ = None
        for c in comp.get("competitors", []):
            ab = ESPN_ABBR.get(c["team"]["abbreviation"], c["team"]["abbreviation"])
            sc = c.get("score"); sc = int(float(sc)) if sc not in (None, "") else None
            if c.get("homeAway") == "home":
                home, hs = ab, sc
            else:
                away, as_ = ab, sc
        state = STATE.get(ty.get("state"), "scheduled")
        if ty.get("completed"):
            state = "final"
        rows.append({"season": season, "week": week, "home_team": home, "away_team": away, "status": state, "detail": ty.get("shortDetail") or ty.get("detail"),
                     "period": st.get("period"), "clock": st.get("displayClock"), "home_score": hs if state != "scheduled" else None, "away_score": as_ if state != "scheduled" else None, "espn_id": ev.get("id")})
    return pd.DataFrame(rows, columns=["season", "week", "home_team", "away_team", "status", "detail", "period", "clock", "home_score", "away_score", "espn_id"])


def _to_utc(kick_et) -> pd.Timestamp | None:
    if kick_et is None or pd.isna(kick_et):
        return None
    return pd.Timestamp(kick_et).tz_localize("America/New_York", ambiguous=True, nonexistent="shift_forward").tz_convert("UTC").tz_localize(None)


def priced_before_kickoff(gid: str, kick_utc, hist: pd.DataFrame) -> dict | None:
    """The model's numbers from the last run before kickoff (pred_history.csv); the last run when none was."""
    h = hist[hist.game_id == gid]
    if not len(h):
        return None
    h = h.assign(t=pd.to_datetime(h.run_at.str.replace(" UTC", ""), errors="coerce")).sort_values("t")
    b = h[h.t < kick_utc] if kick_utc is not None else h
    r = (b if len(b) else h).iloc[-1]
    return {"run_at": r.run_at, "model_spread": clean(r.model_spread), "model_total": clean(r.model_total), "after_kickoff": not len(b)}


def close_before_kickoff(gid: str, kick_utc, log: pd.DataFrame, sched) -> dict:
    """The closing consensus: the newest lines-log snapshot before kickoff (lines.latest on that slice); the schedule's
    line where nothing was logged. `source` says which."""
    from . import lines as LNM
    h = log[log.game_id == gid]
    if kick_utc is not None and len(h):
        t = pd.to_datetime(h.ts.str.replace("Z", ""), format="%Y-%m-%dT%H-%M-%S", errors="coerce")
        h = h[t < kick_utc]
    sp, ts1 = LNM.latest(h, "home_spread") if len(h) else (None, None)
    tl, ts2 = LNM.latest(h, "total") if len(h) else (None, None)
    out = {"spread": sp, "total": tl, "ts": ts1 or ts2, "source": "lines log"}
    if sp is None and sched is not None and pd.notna(sched.spread_line):
        out["spread"] = float(sched.spread_line); out["source"] = "schedule"
    if tl is None and sched is not None and pd.notna(sched.total_line):
        out["total"] = float(sched.total_line); out["source"] = "schedule" if sp is None else out["source"]
    return out


def _res(d: float) -> str:
    return "push" if abs(d) < 1e-9 else ("win" if d > 0 else "loss")


def calls(home: str, away: str, priced: dict | None, close: dict, hs, as_) -> dict:
    """The model's side of the spread (home when its spread beats the close's), of the total, and its winner, each
    graded at the close once the game is final. nflverse sign: spread_line positive = home favoured; the home side
    covers when the margin beats it."""
    out = {}
    if priced is None:
        return out
    ms, mt = priced["model_spread"], priced["model_total"]
    if close.get("spread") is not None and ms is not None:
        sl = close["spread"]; home_side = ms > sl
        c = {"side": home if home_side else away, "line": round(-sl if home_side else sl, 1), "edge": round(abs(ms - sl), 2)}
        if hs is not None:
            m = hs - as_; c["result"] = _res((m - sl) if home_side else (sl - m))
        out["spread"] = c
    if close.get("total") is not None and mt is not None:
        tl = close["total"]; over = mt > tl
        c = {"side": "Over" if over else "Under", "line": tl, "edge": round(abs(mt - tl), 2)}
        if hs is not None:
            t = hs + as_; c["result"] = _res((t - tl) if over else (tl - t))
        out["total"] = c
    if ms is not None:
        fav = home if ms > 0 else away
        c = {"side": fav}
        if hs is not None:
            m = hs - as_; c["result"] = "push" if m == 0 else ("win" if (m > 0) == (fav == home) else "loss")
        out["winner"] = c
    return out


def _record(results) -> dict:
    w = sum(1 for r in results if r == "win"); l = sum(1 for r in results if r == "loss"); p = sum(1 for r in results if r == "push")
    return {"w": w, "l": l, "p": p, "text": f"{w}-{l}" + (f"-{p}" if p else "")}


def bets_for(gids: set, games_live: pd.DataFrame) -> pd.DataFrame:
    """Every logged bet on these games (the flag, the shadow rules, Matt's), graded by the tracker's own grader on a
    games frame that carries ESPN's finals and the close, so a live grade is the tracker's grade later."""
    from . import tracker as TK
    from .picks import SHADOWS
    parts = []
    for who, fn in [("model", "model_picks.csv"), ("matt", "my_bets.csv")] + [(s, f"{s}_picks.csv") for s in SHADOWS]:
        f = TR / fn
        if not f.exists():
            continue
        t = pd.read_csv(f); t = t[t.game_id.isin(gids)]
        if len(t):
            parts.append(TK.grade_rows(t, games_live).assign(who=who))
    if not parts:
        return pd.DataFrame(columns=["game_id", "who", "bet", "odds", "result", "units"])
    return pd.concat(parts, ignore_index=True)


def build(fetch_live: bool = True) -> dict:
    games = pd.read_parquet(OUT / "games.parquet")
    now = pd.Timestamp.now(tz="America/New_York").tz_localize(None)
    from . import lines as LNM
    season, week = LNM.current_week(games)
    sb = []; errors = []
    for s, w in weeks_to_fetch(games, now):
        j = None
        if fetch_live:
            try:
                j = fetch(s, w)
            except Exception as e:  # noqa
                errors.append(f"week {w}: {str(e)[:100]}")
        if j is None:
            j = saved(s, w)
        if j is not None:
            sb.append(parse(j, s, w))
    sb = pd.concat(sb, ignore_index=True) if sb else parse({}, season, week)
    key = games.set_index(["season", "week", "home_team", "away_team"]).game_id
    sb["game_id"] = [key.get((r.season, r.week, r.home_team, r.away_team)) for r in sb.itertuples()]
    sb = sb[sb.game_id.notna()].copy()
    g = games.set_index("game_id")
    hist = pd.read_csv(RUNS / "pred_history.csv") if (RUNS / "pred_history.csv").exists() else pd.DataFrame(columns=["run_at", "game_id", "model_spread", "model_total"])
    log = LNM.load_log()
    out_games, mismatch = {}, []
    live = g.loc[sb.game_id].copy()   # the games frame with ESPN's finals and the close, for the tracker's grader
    for r in sb.itertuples():
        x = g.loc[r.game_id]; kick_utc = _to_utc(x.kickoff_et)
        priced = priced_before_kickoff(r.game_id, kick_utc, hist)
        close = close_before_kickoff(r.game_id, kick_utc, log, x)
        hs, as_ = (int(r.home_score), int(r.away_score)) if r.status == "final" and r.home_score is not None and not pd.isna(r.home_score) else (None, None)
        if hs is not None and pd.notna(x.home_score) and (int(x.home_score) != hs or int(x.away_score) != as_):
            mismatch.append(f"{r.game_id}: ESPN {as_}-{hs}, nflverse {int(x.away_score)}-{int(x.home_score)}")
        if hs is not None:
            live.loc[r.game_id, ["home_score", "away_score", "result", "total"]] = [hs, as_, hs - as_, hs + as_]
        if close.get("spread") is not None: live.loc[r.game_id, "spread_line"] = close["spread"]
        if close.get("total") is not None: live.loc[r.game_id, "total_line"] = close["total"]
        out_games[r.game_id] = {"season": int(x.season), "week": int(x.week), "status": r.status, "detail": r.detail, "period": clean(r.period), "clock": r.clock, "kickoff": clean(x.kickoff_et),
                                "home_team": x.home_team, "away_team": x.away_team,
                                "home_score": None if r.status == "scheduled" or pd.isna(r.home_score) else int(r.home_score), "away_score": None if r.status == "scheduled" or pd.isna(r.away_score) else int(r.away_score),
                                "nflverse_scored": bool(pd.notna(x.home_score)), "priced": priced, "close": {k: clean(v) for k, v in close.items()},
                                "calls": calls(x.home_team, x.away_team, priced, close, hs, as_), "bets": []}
    gr = bets_for(set(out_games), live.reset_index())
    for b in gr.itertuples():
        out_games[b.game_id]["bets"].append({"who": b.who, "bet": b.bet, "odds": clean(getattr(b, "odds", None)), "result": b.result, "units": clean(round(float(b.units), 3)) if pd.notna(getattr(b, "units", np.nan)) else None,
                                             "close": clean(getattr(b, "close", None)), "clv": clean(getattr(b, "clv", None))})
    # the records: the week being played (the latest week with a game under way or final; the picks week when none),
    # the model's side of each market and each rule's bets. The picks week moves on once every game has kicked off
    # (lines.current_week), so during Monday night the record is still this week's
    started = [(int(g.loc[k].season), int(g.loc[k].week)) for k, v in out_games.items() if v["status"] != "scheduled"]
    rs, rw = max(started) if started else (season, week)
    wk = {k: v for k, v in out_games.items() if g.loc[k].season == rs and g.loc[k].week == rw}
    fin = [v for v in wk.values() if v["status"] == "final"]
    rec = {"season": rs, "week": rw, "games": len(wk), "finals": len(fin), "in_progress": sum(1 for v in wk.values() if v["status"] == "in_progress"),
           "spread": _record([v["calls"]["spread"]["result"] for v in fin if v["calls"].get("spread", {}).get("result")]),
           "total": _record([v["calls"]["total"]["result"] for v in fin if v["calls"].get("total", {}).get("result")]),
           "winner": _record([v["calls"]["winner"]["result"] for v in fin if v["calls"].get("winner", {}).get("result")]),
           "bets": {}}
    for who in sorted({b["who"] for v in wk.values() for b in v["bets"]}):
        bs = [b for v in wk.values() for b in v["bets"] if b["who"] == who]
        st = [b for b in bs if b["result"] in ("win", "loss", "push")]
        rec["bets"][who] = {**_record([b["result"] for b in st]), "n": len(bs), "units": round(sum(b["units"] or 0 for b in st), 2)}
    checked = pd.Timestamp.now("UTC").strftime("%Y-%m-%d %H:%M UTC")
    RES.mkdir(parents=True, exist_ok=True)
    rows = [{"game_id": k, **{c: v.get(c) for c in ("status", "detail", "home_score", "away_score")}, "close_spread": v["close"].get("spread"), "close_total": v["close"].get("total"),
             "model_spread": (v["priced"] or {}).get("model_spread"), "model_total": (v["priced"] or {}).get("model_total"), "priced_at": (v["priced"] or {}).get("run_at"),
             "spread_call": v["calls"].get("spread", {}).get("side"), "spread_result": v["calls"].get("spread", {}).get("result"), "total_call": v["calls"].get("total", {}).get("side"), "total_result": v["calls"].get("total", {}).get("result"),
             "winner_call": v["calls"].get("winner", {}).get("side"), "winner_result": v["calls"].get("winner", {}).get("result"), "checked": checked} for k, v in out_games.items()]
    pd.DataFrame(rows).to_csv(RES / "live_scores.csv", index=False)
    payload = {"checked": checked, "season": season, "week": week, "games": out_games, "record": rec, "mismatch": mismatch, "errors": errors,
               "note": "scores from the ESPN scoreboard, graded at the model's numbers from the last run before kickoff and the closing line; nflverse's scores replace them on the weekly run"}
    WEB.mkdir(parents=True, exist_ok=True)
    (WEB / "live.js").write_text("window.LIVE=" + json.dumps(payload, default=clean, separators=(",", ":")) + ";")
    return payload


if __name__ == "__main__":
    p = build(fetch_live="--no-fetch" not in sys.argv)
    r = p["record"]
    print(f"live results: week {r['week']}, {r['finals']} final of {r['games']}, {r['in_progress']} in progress; spread {r['spread']['text']}, total {r['total']['text']}, winner {r['winner']['text']}"
          + (f"; mismatch: {p['mismatch']}" if p["mismatch"] else "") + (f"; errors: {p['errors']}" if p["errors"] else ""))
