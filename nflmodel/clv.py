"""Closing line value (CLV) on the live bets: did the number we took beat the market's last number before kickoff?

Grading only. Nothing here feeds the model, the bet rules or which games are flagged; it reads the tracker's recorded
bets and the lines log after the fact.

The bets: every bet the live rules recorded (nflmodel/tracker.py record_model_picks), one file per rule:
  model        data/tracker/model_picks.csv        the spread flag (picks.SPREAD_EDGE), bet at the best number
  shadowunder  data/tracker/shadowunder_picks.csv  the totals flag (unders at a picks.TOTAL_SHADOW chance)
  windunder    data/tracker/windunder_picks.csv    the wind under (picks.WIND_UNDER)
The tracker keeps one row per game: the flag at the last weekly run before kickoff (an earlier run's row is replaced or
dropped, tracker._record). So "the line taken" is the number in that row's bet (e.g. "WAS +3.5", "Under 38.5"), as
recorded at that run, and CLV here is measured from the last run before kickoff, not from the first time a game flagged.

The closing line: the consensus (lines.consensus: the median across sources, to the half point) of the last lines-log
snapshot (data/lines/lines_log.csv) taken strictly before kickoff (games.parquet kickoff_et, Eastern) that has the
market's line. That is the same consensus the picks are priced on (lines.latest). A snapshot at or after kickoff (the
log keeps pulling during the game: live lines) is never used. A bet is graded once its game has kicked off; before that
it is pending and left out of every average.

CLV in points, from the bet's side (positive = we beat the close):
  spread  the side's handicap taken minus the side's closing handicap (the log's home_spread is positive when the home
          team is favoured, so the home side's handicap is -home_spread and the away side's is +home_spread)
  over    close minus line taken;  under  line taken minus close
A bet taken on the closing number has CLV 0 and does not count as beating the close.

CLV in probability, where both prices are logged: the no-vig chance of our side at the close minus the no-vig chance at
the time the bet was recorded, both at the consensus number (each source's two prices with the vig removed, averaged
over the sources posting the consensus number). The "taken" snapshot is the one the recording run priced on: the run's
own line pull (its "lines" step in data/runs/run_log.csv names the snapshot), else the last snapshot no later than
RUN_WINDOW after run_at (the weekly run stamps run_at as it starts and pulls its lines about five minutes in); always
before kickoff.
Computed only when the consensus number at the taken snapshot equals the closing number; when the number itself moved,
the points CLV carries it and the probability is left blank.

Usage: python -m nflmodel.clv   (writes reports/clv.csv and reports/clv.md)
"""
from __future__ import annotations
import numpy as np, pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT, TR, REP = ROOT / "data" / "processed", ROOT / "data" / "tracker", ROOT / "reports"
RUN_WINDOW = pd.Timedelta(minutes=15)   # when the run log has no line pull for a run: how long after run_at its pull lands (grading only)
RULE_FILES = {"model": "model_picks.csv", "shadowunder": "shadowunder_picks.csv", "windunder": "windunder_picks.csv"}


def rule_labels() -> dict:
    from . import picks as P
    return {"model": f"Spreads, {P.SPREAD_EDGE:g}+ edge", "shadowunder": f"Unders, {100 * P.TOTAL_SHADOW['prob']:.0f}%+ chance",
            "windunder": f"Wind unders, {P.WIND_UNDER['mph']:g}+ mph"}


def log_ts(s) -> pd.Timestamp:
    """'2026-09-22T15-29-26Z' (the lines log's stamp) -> UTC timestamp."""
    return pd.to_datetime(s, format="%Y-%m-%dT%H-%M-%SZ", utc=True)


def run_ts(s) -> pd.Timestamp:
    """'2026-10-01 23:22 UTC' (the tracker's run_at) -> UTC timestamp."""
    return pd.to_datetime(str(s).replace(" UTC", ""), utc=True)


def kickoff_utc(kickoff_et) -> pd.Timestamp:
    """games.parquet kickoff_et (naive Eastern) -> UTC."""
    return pd.Timestamp(kickoff_et).tz_localize("America/New_York").tz_convert("UTC")


def consensus(values):
    from . import lines as LN
    return LN.consensus(values)


def snapshot(hist: pd.DataFrame, key: str, before: pd.Timestamp, through: pd.Timestamp | None = None):
    """(ts, consensus, rows) of the newest snapshot of one game's log with `key` set, taken strictly before `before`
    (kickoff) and, if `through` is given, at or before it. (None, None, empty) when there is none."""
    if hist is None or not len(hist):
        return None, None, hist
    h = hist[hist[key].notna()].copy()
    t = h["_t"] if "_t" in h.columns else log_ts(h.ts)
    m = t < before
    if through is not None:
        m &= t <= through
    h, t = h[m], t[m]
    if not len(h):
        return None, None, h.iloc[0:0]
    last = t.max()
    rows = h[t == last]
    return last, consensus(rows[key].tolist()), rows


def _imp(odds) -> float:
    o = float(odds)
    return -o / (-o + 100) if o < 0 else 100 / (o + 100)


def novig(rows: pd.DataFrame, kind: str, our_first: bool, line: float):
    """Our side's no-vig chance at `line`: each source posting that number with both prices, the vig removed, averaged.
    Spread: home price first (our_first = our side is home); total: over first (our_first = we bet the over)."""
    if rows is None or not len(rows) or line is None:
        return np.nan
    key, a, b = ("home_spread", "spread_odds_home", "spread_odds_away") if kind == "spread" else ("total", "over_odds", "under_odds")
    r = rows[(rows[key] - line).abs() < 1e-9]
    r = r[r[a].notna() & r[b].notna()] if a in r.columns and b in r.columns else r.iloc[0:0]
    if not len(r):
        return np.nan
    p = [(_imp(x) / (_imp(x) + _imp(y))) for x, y in zip(r[a], r[b])]
    q = float(np.mean(p))
    return q if our_first else 1 - q


def clv_points(kind: str, side: str, line: float, close: float) -> float:
    """CLV in points from the bet's side; `line` and `close` are both the side's own number (spread: its handicap)."""
    if line is None or close is None or pd.isna(line) or pd.isna(close):
        return np.nan
    if kind == "spread":
        return float(line - close)
    if side == "over":
        return float(close - line)
    return float(line - close)


def side_handicap(home_spread: float, side: str, home: str) -> float:
    """The side's handicap from the log's home_spread (positive = home favoured)."""
    return -home_spread if side == home else home_spread


def run_lines_ts() -> dict:
    """run_at -> UTC time of the snapshot that weekly run pulled (its "lines" step detail in data/runs/run_log.csv)."""
    import ast
    f = ROOT / "data" / "runs" / "run_log.csv"
    if not f.exists():
        return {}
    d = pd.read_csv(f, usecols=["step", "status", "detail", "run_at"])
    out = {}
    for r in d[(d.step == "lines") & (d.status == "ok")].itertuples():
        try:
            out[r.run_at] = log_ts(ast.literal_eval(r.detail)["ts"])
        except Exception:  # noqa: a truncated or older detail: the RUN_WINDOW fallback applies
            pass
    return out


def grade_bet(bet: str, run_at, home: str, away: str, kickoff_et, hist: pd.DataFrame, now: pd.Timestamp, taken_through=None) -> dict:
    """One recorded bet against the closing line. `hist` is that game's lines-log rows; `now` is UTC; `taken_through`
    is the recording run's own snapshot time (default: run_at + RUN_WINDOW)."""
    from .tracker import parse_bet
    kind, side, line = parse_bet(bet, home, away)
    out = {"kind": kind, "side": side, "line": line, "close": np.nan, "close_ts": None, "clv_pts": np.nan, "beat": np.nan,
           "p_taken": np.nan, "p_close": np.nan, "clv_prob": np.nan, "status": "pending"}
    if kind not in ("spread", "total") or kickoff_et is None or pd.isna(kickoff_et):
        out["status"] = "not graded"
        return out
    ko = kickoff_utc(kickoff_et)
    if now < ko:
        return out   # the close is not known until kickoff
    key = "home_spread" if kind == "spread" else "total"
    ts, cons, rows = snapshot(hist, key, ko)
    if ts is None:
        out["status"] = "no line logged"
        return out
    close = side_handicap(cons, side, home) if kind == "spread" else cons
    c = clv_points(kind, side, line, close)
    out.update({"close": close, "close_ts": ts.strftime("%Y-%m-%d %H:%M UTC"), "clv_pts": c, "beat": bool(c > 0), "status": "closed"})
    ours_first = (side == home) if kind == "spread" else (side == "over")
    t2, cons2, rows2 = snapshot(hist, key, ko, taken_through if taken_through is not None else run_ts(run_at) + RUN_WINDOW)
    if t2 is not None and cons2 == cons:
        pt, pc = novig(rows2, kind, ours_first, cons), novig(rows, kind, ours_first, cons)
        out.update({"p_taken": pt, "p_close": pc, "clv_prob": (pc - pt) if pd.notna(pt) and pd.notna(pc) else np.nan})
    return out


def grade(bets: pd.DataFrame, games: pd.DataFrame, log: pd.DataFrame, now: pd.Timestamp, run_lines: dict | None = None) -> pd.DataFrame:
    """Every recorded bet (columns rule, run_at, season, week, game_id, bet, odds) graded against the closing line;
    `run_lines` maps a run_at to the snapshot that run pulled (run_lines_ts)."""
    run_lines = run_lines or {}
    g = games.set_index("game_id")
    log = log.copy()
    log["_t"] = log_ts(log.ts)
    by = {k: v for k, v in log.groupby("game_id")}
    rows = []
    for r in bets.itertuples():
        if r.game_id not in g.index:
            continue
        x = g.loc[r.game_id]
        res = grade_bet(r.bet, r.run_at, x.home_team, x.away_team, x.kickoff_et, by.get(r.game_id), now, run_lines.get(r.run_at))
        rows.append({"rule": r.rule, "season": int(r.season), "week": int(r.week), "game_id": r.game_id, "bet": r.bet,
                     "odds": getattr(r, "odds", np.nan), "run_at": r.run_at, "kickoff_et": str(x.kickoff_et)[:16], **res})
    cols = ["rule", "season", "week", "game_id", "bet", "odds", "run_at", "kickoff_et", "kind", "side", "line", "close", "close_ts",
            "clv_pts", "beat", "p_taken", "p_close", "clv_prob", "status"]
    return pd.DataFrame(rows, columns=cols)


def aggregate(gr: pd.DataFrame) -> pd.DataFrame:
    """Per rule and overall, closed bets only: bets, average CLV in points, share beating the close (CLV > 0), pending
    bets, and the average probability CLV where it could be computed."""
    labels = rule_labels()
    out = []
    for rule in list(RULE_FILES) + ["all"]:
        x = gr if rule == "all" else gr[gr.rule == rule]
        c = x[x.status == "closed"]
        pr = c.clv_prob.dropna()
        out.append({"rule": rule, "label": "All live bets" if rule == "all" else labels.get(rule, rule), "bets": int(len(c)),
                    "avg_clv_pts": float(c.clv_pts.mean()) if len(c) else np.nan,
                    "beat_share": float((c.clv_pts > 0).mean()) if len(c) else np.nan,
                    "beat": int((c.clv_pts > 0).sum()), "same": int((c.clv_pts == 0).sum()), "worse": int((c.clv_pts < 0).sum()),
                    "pending": int((x.status == "pending").sum()), "prob_bets": int(len(pr)),
                    "avg_clv_prob": float(pr.mean()) if len(pr) else np.nan})
    return pd.DataFrame(out)


def load_bets(season: int | None = None) -> pd.DataFrame:
    parts = []
    for rule, f in RULE_FILES.items():
        p = TR / f
        if p.exists():
            d = pd.read_csv(p)
            if len(d):
                parts.append(d.assign(rule=rule))
    if not parts:
        return pd.DataFrame(columns=["rule", "run_at", "season", "week", "game_id", "bet", "odds"])
    b = pd.concat(parts, ignore_index=True)
    return b[b.season == season] if season is not None else b


def build(season: int | None = None, now: pd.Timestamp | None = None):
    """(graded rows, summary) for one season (default: the newest season with a recorded bet, else the schedule's)."""
    from . import lines as LN
    now = pd.Timestamp.now("UTC") if now is None else pd.Timestamp(now)
    games = pd.read_parquet(OUT / "games.parquet")
    bets = load_bets()
    if season is None:
        season = int(bets.season.max()) if len(bets) else int(games.season.max())
    bets = bets[bets.season == season]
    gr = grade(bets, games, LN.load_log(), now, run_lines_ts())
    return gr, aggregate(gr), season


def _r(v, n):
    return None if v is None or (isinstance(v, float) and np.isnan(v)) else round(float(v), n)


def page_payload(season: int | None = None, now: pd.Timestamp | None = None) -> dict:
    """week.js 'clv': the season summary and the closed bets, rounded as the page shows them."""
    now = pd.Timestamp.now("UTC").floor("s") if now is None else pd.Timestamp(now)
    gr, sm, season = build(season, now)
    rules = [{"rule": r.rule, "label": r.label, "bets": r.bets, "avg_clv_pts": _r(r.avg_clv_pts, 2), "beat_share": _r(r.beat_share, 3),
              "beat": r.beat, "pending": r.pending, "prob_bets": r.prob_bets, "avg_clv_prob": _r(r.avg_clv_prob, 4)} for r in sm.itertuples()]
    c = gr[gr.status == "closed"]
    bets = [{"rule": r.rule, "week": r.week, "game_id": r.game_id, "bet": r.bet, "line": _r(r.line, 1), "close": _r(r.close, 1),
             "clv_pts": _r(r.clv_pts, 1), "clv_prob": _r(r.clv_prob, 4), "close_ts": r.close_ts} for r in c.itertuples()]
    return {"season": season, "as_of": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "rules": rules, "bets": bets}


def markdown(gr: pd.DataFrame, sm: pd.DataFrame, season: int) -> str:
    fmt = lambda v, f: "" if v is None or (isinstance(v, float) and np.isnan(v)) else f.format(v)
    L = [f"# Closing line value, {season}", "",
         "The number each live bet was recorded at against the consensus line at the last lines-log snapshot before kickoff "
         "(nflmodel/clv.py). Positive CLV means the bet beat the close. Grading only: nothing here changes a rule or a pick.", "",
         "| Rule | Closed bets | Avg CLV (pts) | Beat the close | Same | Worse | Pending | Avg CLV (no-vig prob) |", "|---|---|---|---|---|---|---|---|"]
    for r in sm.itertuples():
        L.append(f"| {r.label} | {r.bets} | {fmt(r.avg_clv_pts, '{:+.2f}')} | {fmt(r.beat_share, '{:.0%}')} | {r.same} | {r.worse} | {r.pending} | "
                 f"{fmt(r.avg_clv_prob, '{:+.1%}')}{f' ({r.prob_bets})' if r.prob_bets else ''} |")
    L += ["", "## Every bet", ""]
    if len(gr):
        t = gr[["rule", "week", "game_id", "bet", "line", "close", "clv_pts", "clv_prob", "close_ts", "status"]].copy()
        t["clv_prob"] = t.clv_prob.map(lambda v: fmt(v, "{:+.1%}"))
        L.append(t.to_markdown(index=False))
    else:
        L.append("No bets recorded this season.")
    return "\n".join(L) + "\n"


def main():
    gr, sm, season = build()
    REP.mkdir(parents=True, exist_ok=True)
    gr.to_csv(REP / "clv.csv", index=False)
    (REP / "clv.md").write_text(markdown(gr, sm, season))
    a = sm[sm.rule == "all"].iloc[0]
    msg = f"CLV {season}: {a.bets} closed, {a.pending} pending" + (f", avg {a.avg_clv_pts:+.2f} pts, {a.beat_share:.0%} beat the close" if a.bets else "")
    print(msg)
    return msg


if __name__ == "__main__":
    main()
