"""Standing checks (2 Oct 2026): every bug class found and fixed on 1-2 Oct 2026 checked again on every run, so a
recurrence fails or warns loudly instead of pricing quietly. Checks only: nothing here changes a reading, a price, a rule
or a threshold. The list of every check, the file that runs it and what it catches is docs/wiki/checks.md.

Two groups:
  cheap()  table and page checks (seconds): the tie check runs them on every weekly run and every line watch
           (tie_check.check_page); a FAIL fails the tie check, a WARN goes to the health page (warnlog).
  leaks()  the backtest leak tests (about a minute): audit.leakage_test (future weeks corrupted, Week 1-9 2024 ratings and
           predictions unchanged, a 2024 Week 9 game's own score corrupted) and audit.own_game_shift on the newest played
           week of the current season; and qt_isolated (the live total and chance the same with and without the
           Questionable-in-totals shadow). Weekly run only (step "standing checks").

Each check is a pure function of the tables it reads (tests/test_standing_checks.py plants a bad row in each) and
returns rows of (level, check, detail), level OK, WARN or FAIL.

Usage: python -m nflmodel.standing_checks [--no-leaks]   (writes reports/standing_checks.md, exits 1 on any FAIL)
"""
from __future__ import annotations
import csv, json, re, sys
import numpy as np, pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT, REP, WEB = ROOT / "data" / "processed", ROOT / "reports", ROOT / "web" / "data"
TR, RUNS, WX = ROOT / "data" / "tracker", ROOT / "data" / "runs", ROOT / "data" / "weather"
ROOFED = ("dome", "closed")
LIVE_BETS = {"model": "model_picks.csv", "shadowunder": "shadowunder_picks.csv", "windunder": "windunder_picks.csv"}   # the rules Matt bets (CLAUDE.md "Live rules")
WEATHER_BETS = ("windunder_bet", "shadowrain_bet", "shadowcold_bet", "shadowunderwind_bet")   # card bets read off a weather reading
TEMP_RANGE, POP_RANGE = (-40.0, 130.0), (0.0, 100.0)   # deg F, percent: outside is a sentinel (NWS MOS writes 999), never weather
MOS_LEAD_H = 5   # a GFS or NBS run is used only when issued at least this many hours before kickoff (forecast_history.last_run)


def _row(level, what, bad, n=None, extra=""):
    bad = list(bad)
    det = (f"{len(bad)} of {n}" if n is not None else f"{len(bad)}") + (f": {', '.join(map(str, bad[:6]))}" if bad else "") + (f"; {extra}" if extra else "")
    return (level if bad else "OK", what, det)


def _js(path: Path):
    s = path.read_text(encoding="utf-8"); return json.loads(s[s.index("=") + 1:].rstrip().rstrip(";"))


def _ko_utc(kickoff_et) -> pd.Series:
    """games.parquet kickoff_et (naive Eastern) -> UTC timestamps."""
    k = pd.to_datetime(pd.Series(kickoff_et), errors="coerce")
    return k.dt.tz_localize("America/New_York", ambiguous="NaT", nonexistent="NaT").dt.tz_convert("UTC")


# ---- the QB priced (2 Oct 2026: #376, #380, #390, #396) ----

def qb_priced_not_out(feats: pd.DataFrame, games: pd.DataFrame, out: dict, season: int, week: int) -> list:
    """No side of an unplayed picks-week game is priced at a QB ruled out (Out, Doubtful or off the active roster): the WAS
    card priced Jayden Daniels after ESPN ruled him Out (#376)."""
    up = set(games[(games.season == season) & (games.week == week) & games.home_score.isna()].game_id)
    f = feats[feats.game_id.isin(up)]
    bad = [f"{r.game_id} {r.team} {r.qb_id}" for r in f.itertuples() if isinstance(r.qb_id, str) and r.qb_id in out.get(r.team, set())]
    return [_row("FAIL", "QB priced on every unplayed picks-week side is not ruled out (Out, Doubtful, off the active roster)", bad, len(f))]


def qb_out_is_last_starter(trends: pd.DataFrame, qb: pd.DataFrame, games: pd.DataFrame, out: dict, season: int, week: int) -> list:
    """qb_out means "last game's starting QB is out" (the backtest's meaning, #396): set on a picks-week side only when a QB
    who dropped back in the team's last game (qb_games) is ruled out (FAIL: WAS read 1 for Daniels, already replaced by
    Mariota); last game's starter (most dropbacks) ruled out with qb_out 0 is a WARN (the snap rows may name another QB)."""
    up = games[(games.season == season) & (games.week == week) & games.home_score.isna()]
    t = trends[trends.game_id.isin(set(up.game_id))]
    q = qb[(qb.season < season) | ((qb.season == season) & (qb.week < week))].sort_values(["season", "week", "dropbacks"])
    last = q.groupby("team").tail(1).set_index("team")   # each team's newest played game, its starter the last row (most dropbacks)
    played = {tm: set(q[(q.team == tm) & (q.game_id == r.game_id)].qb_id) for tm, r in last.iterrows()}
    wrong, missed = [], []
    for r in t.itertuples():
        o = out.get(r.team, set())
        if r.qb_out == 1 and not (played.get(r.team, set()) & o):
            wrong.append(f"{r.game_id} {r.team}")
        if r.qb_out == 0 and r.team in last.index and last.loc[r.team, "qb_id"] in o:
            missed.append(f"{r.game_id} {r.team}")
    return [_row("FAIL", "qb_out = 1 only when last game's starting QB is ruled out (picks week)", wrong, len(t)),
            _row("WARN", "last game's starting QB ruled out and qb_out = 1 (picks week)", missed, len(t))]


# ---- roofs and weather (2 Oct 2026: #391 retractable roofs, #384 Japan's post-kickoff run, #365 MOS sentinels) ----

def retractable_roofs(games: pd.DataFrame, cards: list | None = None) -> list:
    """No unplayed game at a retractable-roof home stadium (or the Bernabeu) with the roof blank, and no such game priced
    outdoors on its card (2026_04_DAL_HOU fired the wind under at Houston, #391). An announced "open" roof stays outdoors."""
    from .build import RETRACTABLE_HOME
    roof = games.roof.astype(object).where(games.roof.notna(), "").astype(str).str.strip()
    at = (games.home_team.isin(RETRACTABLE_HOME) & ~games.location.eq("Neutral")) | (games.get("stadium_id", pd.Series("", index=games.index)) == "MAD01")
    up = games[at & games.home_score.isna()]
    blank = up.game_id[roof[up.index].eq("")].tolist()
    rows = [_row("FAIL", "unplayed games at retractable-roof stadiums have a roof (blank counts as closed: build.RETRACTABLE_HOME)", blank, len(up))]
    if cards is not None:
        closed = set(up.game_id[~roof[up.index].isin(["open", "outdoors"])])
        bad = [c["game_id"] for c in cards if c["game_id"] in closed and c.get("home_score") is None and (c.get("wx") or {}).get("s") not in (None, "dome")]
        rows.append(_row("FAIL", "cards price unplayed retractable-roof games (roof not announced open) as roofed, not outdoors", bad, len(closed)))
    return rows


def no_weather_under_roof(games: pd.DataFrame, wind: dict, rain: dict, temp: dict, cards: list | None = None) -> list:
    """No forecast reading for a game under a roof (dome or closed), and no card weather or weather bet on one."""
    roofed = set(games.game_id[games.roof.isin(ROOFED)])
    bad = sorted({g for d in (wind, rain, temp) for g in d if g in roofed})
    rows = [_row("FAIL", "no wind, rain or temperature reading for a game under a roof (wind_live readings)", bad, len(roofed))]
    if cards is not None:
        cb = []
        for c in cards:
            if c["game_id"] not in roofed or c.get("home_score") is not None:
                continue
            if any((sd.get("wind") is not None) for sd in (c.get("sides") or {}).values()):
                cb.append(f"{c['game_id']} wind")
            cb += [f"{c['game_id']} {k}" for k in WEATHER_BETS if c.get(k)]
        rows.append(_row("FAIL", "cards of roofed games carry no wind and no weather bet (wind under, rain, cold)", cb))
    return rows


def forecasts_before_kickoff(hist: pd.DataFrame, live: pd.DataFrame) -> list:
    """Every forecast run a reading uses was issued before kickoff: the stored history's GFS and NBS runs at least
    MOS_LEAD_H hours before; Japan's post-kickoff run (jma_wind_d0) never read (#384); the live log's rows fetched before
    kickoff on a GFS run at least MOS_LEAD_H hours before."""
    from . import forecast_history as FH
    rows = [_row("FAIL", "forecast columns read for a reading are all pre-kickoff runs (forecast_history.PRE_KICKOFF_WIND has no POST_KICKOFF column)",
                 sorted(set(FH.PRE_KICKOFF_WIND) & set(FH.POST_KICKOFF)))]
    bad, n = [], 0
    if len(hist):
        ko = pd.to_datetime(hist.kickoff_utc.str.replace("Z", ""), errors="coerce")
        for val, run in (("gfs_wind_d0", "gfs_run_d0"), ("nbs_wind_d0", "nbs_run_d0")):
            if val in hist and run in hist:
                used = hist[val].notna(); n += int(used.sum())
                r_ = pd.to_datetime(hist[run].astype(str).str.replace("Z", ""), format="%Y-%m-%dT%H", errors="coerce")
                late = used & (r_.isna() | (r_ > ko - pd.Timedelta(hours=MOS_LEAD_H)))
                bad += [f"{g} {run}" for g in hist.game_id[late]]
    rows.append(_row("FAIL", f"stored forecasts: every GFS and NBS run read was issued {MOS_LEAD_H}+ hours before kickoff", bad, n))
    bad = []
    if len(live):
        ko = pd.to_datetime(live.kickoff_utc.astype(str).str.replace("Z", ""), errors="coerce")
        ts = pd.to_datetime(live.ts.astype(str).str.replace("Z", ""), format="%Y-%m-%dT%H-%M-%S", errors="coerce")
        run = pd.to_datetime(live.gfs_run.astype(str).str.replace("Z", ""), format="%Y-%m-%dT%H", errors="coerce")
        late = ts.isna() | ko.isna() | (ts >= ko) | (live.gfs_run.notna() & (run > ko - pd.Timedelta(hours=MOS_LEAD_H)))
        bad = [f"{g} {t}" for g, t in zip(live.game_id[late], live.ts[late])]
    rows.append(_row("FAIL", f"live forecasts (wind_live.csv): every row fetched before kickoff on a GFS run {MOS_LEAD_H}+ hours before", bad, len(live)))
    return rows


def plausible_weather(wind: dict, rain: dict, temp: dict, latest: pd.DataFrame | None = None) -> list:
    """Readings inside what weather does: wind at or under data_checks.WIND_MAX mph, temperature and rain chance in range
    (NWS MOS writes 99 or 999 for a missing hour: 2018_16_BAL_LAC had a 20 mph forecast built from it, #365)."""
    from .data_checks import WIND_MAX
    bad = [f"{g} wind {v:g}" for g, v in wind.items() if not (0 <= v <= WIND_MAX)]
    bad += [f"{g} rain {v:g}" for g, v in rain.items() if not (POP_RANGE[0] <= v <= POP_RANGE[1])]
    bad += [f"{g} temp {v:g}" for g, v in temp.items() if not (TEMP_RANGE[0] <= v <= TEMP_RANGE[1])]
    if latest is not None and len(latest):
        ok = latest[latest.status.isin(["ok", "carried"])] if "status" in latest else latest
        w = pd.to_numeric(ok.get("wind"), errors="coerce"); t = pd.to_numeric(ok.get("temp"), errors="coerce")
        bad += [f"{g} kickoff wind {v:g}" for g, v in zip(ok.game_id, w) if pd.notna(v) and not 0 <= v <= WIND_MAX]
        bad += [f"{g} kickoff temp {v:g}" for g, v in zip(ok.game_id, t) if pd.notna(v) and not TEMP_RANGE[0] <= v <= TEMP_RANGE[1]]
    return [_row("FAIL", f"forecast readings plausible (wind 0 to {WIND_MAX:g} mph, rain chance 0 to 100, temperature {TEMP_RANGE[0]:g} to {TEMP_RANGE[1]:g} F)", bad, len(wind) + len(rain) + len(temp))]


# ---- bets and lines (2 Oct 2026: #381 the line before kickoff, #395 stale chances) ----

def bets_before_kickoff(bets: dict, games: pd.DataFrame) -> list:
    """Every recorded live bet (spread flag, totals flag, wind under) was logged by a run before its game's kickoff: a
    snapshot after kickoff once became 2026_03_LA_DEN's line (#381)."""
    ko = dict(zip(games.game_id, _ko_utc(games.kickoff_et)))
    bad, n = [], 0
    for rule, t in bets.items():
        if t is None or not len(t):
            continue
        n += len(t)
        at = pd.to_datetime(t.run_at.astype(str).str.replace(" UTC", ""), errors="coerce").dt.tz_localize("UTC")
        for gid, a in zip(t.game_id, at):
            k = ko.get(gid)
            if pd.isna(a) or k is None or pd.isna(k) or a >= k:
                bad.append(f"{rule} {gid} {a}")
    return [_row("FAIL", "every recorded live bet was logged before its game kicked off", bad, n)]


def chances_at_card_line(cards: list, games: pd.DataFrame) -> list:
    """A card priced without the stored fit (priced_live false) carries no chance where its line moved off the schedule's
    (#395: the chances stayed at the schedule's line while the rules read the live one). With the fit, the tie check's
    "card chances = the model's fit priced at the card's line" row covers it."""
    g = games.set_index("game_id"); bad = []
    for c in cards:
        if c.get("priced_live") or c["game_id"] not in g.index:
            continue
        s0, t0 = g.loc[c["game_id"], "spread_line"], g.loc[c["game_id"], "total_line"]
        if c.get("total_line") is not None and c["total_line"] != t0:
            bad += [f"{c['game_id']} {k}" for k in ("p_over", "p_over_emp") if c.get(k) is not None]
        if c.get("spread_line") is not None and c["spread_line"] != s0:
            bad += [f"{c['game_id']} {k}" for k in ("p_home", "p_cover_home") if c.get(k) is not None]
    return [_row("FAIL", "no card chance priced at a line other than the card's (no stored fit: chances cleared where the line moved)", bad, len(cards))]


# ---- shadows and stakes (2 Oct 2026: #379 hidden shadows, #385 one unit a bet) ----

def shadows_stay_off(html: str, page_rules: list, bet_files: dict) -> list:
    """Hidden shadows never reach the page, and only the live rules are bets: index.html names no hidden shadow and drops
    hidden rules wherever it lists PK.rules; meta.js marks every hidden shadow hidden; the bet files the cards and the
    closing-line grading read are the live rules' only."""
    from .picks import HIDDEN_SHADOWS
    named = sorted(n for n in HIDDEN_SHADOWS if re.search(rf"\b{n}\b", html))
    lists = [ln.strip()[:60] for ln in html.splitlines() if "PK.rules" in ln and ".find(" not in ln and "!r.hidden" not in ln]
    unhid = sorted(n for n in HIDDEN_SHADOWS if not any(r.get("rule") == n and r.get("hidden") for r in page_rules))
    extra = sorted(set(bet_files) - set(LIVE_BETS)) + sorted(n for n in bet_files if n in HIDDEN_SHADOWS)
    return [_row("FAIL", "index.html names no hidden shadow and every PK.rules list drops hidden rules", named + lists),
            _row("FAIL", "meta.js marks every hidden shadow hidden", unhid, len(HIDDEN_SHADOWS)),
            _row("FAIL", "the bet files graded as live bets (clv.RULE_FILES) are the live rules only (spread flag, totals flag, wind under)", extra, len(bet_files))]


def one_unit(html: str, picks_md: str | None = None) -> list:
    """One unit a bet (#385, Matt): the page shows no Kelly stake. index.html renders no stake_pct and says no "Kelly"
    outside a code comment; the week's picks file says no Kelly either."""
    code = "\n".join(re.sub(r"(^|\s)//.*$", "", ln) for ln in html.splitlines())   # comments may name the retired stake
    bad = [f"stake_pct x{len(re.findall('stake_pct', code))}"] if "stake_pct" in code else []
    bad += [f"Kelly x{len(re.findall('(?i)kelly', code))}"] if re.search(r"(?i)kelly", code) else []
    if picks_md is not None and re.search(r"(?i)kelly|\d% at [+-]\d", picks_md):
        bad.append("picks file stake")
    return [_row("FAIL", "one unit a bet: no Kelly stake or stake_pct on the page or in the picks file", bad)]


# ---- the Questionable-in-totals shadow (2 Oct 2026: hidden shadow shadowqtotals, nflmodel/qtotals.py) ----

QT_NAMES = ("qt_model_total", "qt_p_over_emp", "qt_model_total_raw", "shadowqtotals_bet", "qt_pred", "qt_dist")   # the shadow's columns, bet and files: never page data


def qt_stays_off(html: str, web: dict, cards: list | None, meta: dict | None, pred_sha: str) -> list:
    """The shadow never reaches the page or the bets, and never writes the live table: no page file (index.html, web/data)
    names its columns or its bet, no card carries a qt_ or shadowqtotals_ key, it is a hidden shadow and no live bet file;
    the shadow's last run left pred_v3.parquet as it found it (qt_dist.json's hashes before and after), and the live table
    now is the one it ran beside (WARN otherwise: the model re-ran without the shadow)."""
    from .picks import HIDDEN_SHADOWS, SHADOWS
    named = sorted(f"{n} in {f}" for f, txt in [("index.html", html)] + sorted(web.items()) for n in QT_NAMES if n in txt)
    keys = sorted({f"{c.get('game_id')} {k}" for c in (cards or []) for k in c if k.startswith(("qt_", "shadowqtotals_"))})
    rule = [] if "shadowqtotals" in SHADOWS and "shadowqtotals" in HIDDEN_SHADOWS and "shadowqtotals" not in LIVE_BETS else ["shadowqtotals not a hidden, unbet shadow"]
    rows = [_row("FAIL", "qtotals shadow: no page file names its columns or bet, no card carries them, hidden and never a live bet", named + keys + rule)]
    if meta is None:
        rows.append(("WARN", "qtotals shadow: its last run left the live table (pred_v3) unchanged", "qt_dist.json missing: the shadow has not run on this machine"))
        return rows
    b, a = meta.get("pred_v3_sha_before"), meta.get("pred_v3_sha_after")
    rows.append(_row("FAIL", "qtotals shadow: its last run left the live table (pred_v3) unchanged", [f"before {b}, after {a}"] if b != a or not b else []))
    rows.append(_row("WARN", "qtotals shadow: priced beside the live table there now (pred_v3 not re-run since)", [f"shadow ran beside {a}, pred_v3 now {pred_sha}"] if a != pred_sha else []))
    return rows


def qt_isolated(season: int | None = None, week: int | None = None) -> list:
    """The live total and chance are the same with and without the shadow: for the newest week of the current season with
    every game played (else the newest priced week), the live totals equation's numbers (model.total_model, and the
    in-sample training misses that price p_over_emp) recomputed from the stored tables before the shadow's fit for that
    week, after it, and on the table carrying the shadow's columns, all equal, and equal to pred_v3's model_total and
    p_over_emp; model.TOTAL_FEATS and model._game_frame untouched; pred_v3 holds no qt_ column."""
    from . import model as M, qtotals as QT, lines as LN
    pred = pd.read_parquet(OUT / "pred_v3.parquet"); g = pd.read_parquet(OUT / "games.parquet")
    if season is None:
        s, w = LN.current_week(g); reg = g[(g.season == s) & (g.game_type == "REG")]
        done = [k for k, x in reg.groupby("week") if x.home_score.notna().all()]
        season, week = (s, int(max(done))) if done else (s, int(pred[pred.season == s].week.max()))
    feats0, gf0 = list(M.TOTAL_FEATS), M._game_frame
    f0 = M.with_trends(pd.read_parquet(OUT / "features_asof.parquet"))
    X = pd.read_parquet(QT.INPUTS) if QT.INPUTS.exists() else pd.DataFrame(columns=["game_id", "team"] + list(QT.PIECES.values()))
    fq = QT.attach(f0, X)

    def live(f):
        fp = M.prep(f); played = fp[fp.pf.notna()]; fpr = M.priced_weather(fp)
        train = played[(played.season >= M.TRAIN_FROM) & ((played.season < season) | ((played.season == season) & (played.week < week)))]
        test = fpr[(fpr.season == season) & (fpr.week == week)]
        th, ta = train[train.home == 1].set_index("game_id"), train[train.home == 0].set_index("game_id"); tid = th.index.intersection(ta.index)
        tres = (th.loc[tid, "pf"] + ta.loc[tid, "pf"]).values - M.total_model(train, train)
        ids = test[test.home == 1].set_index("game_id").index.intersection(test[test.home == 0].set_index("game_id").index)
        return train, test, pd.Series(M.total_model(train, test), index=ids), tres

    _, _, before, tres0 = live(f0)
    trq, teq, with_cols, tres1 = live(fq)
    QT.fit_week(trq, teq)   # the shadow's own fit for the week, between two live fits
    _, _, after, tres2 = live(f0)
    pw = pred[(pred.season == season) & (pred.week == week)].set_index("game_id")
    mt = before.reindex(pw.index) + pw.wind_pts.fillna(0.0)
    pe = pd.Series([QT.p_over_emp(m_, tl, tres0) for m_, tl in zip(mt, pw.total_line)], index=pw.index)
    same = lambda a, b: len(a) == len(b) and bool(np.array_equal(np.asarray(a, float), np.asarray(b, float), equal_nan=True))
    bad = []
    if not (same(before, after) and same(before, with_cols) and same(tres0, tres1) and same(tres0, tres2)):
        bad.append("the live totals equation moved when the shadow ran")
    if list(M.TOTAL_FEATS) != feats0 or M._game_frame is not gf0:
        bad.append("model.TOTAL_FEATS or model._game_frame replaced")
    bad += [f"pred_v3 column {c}" for c in pred.columns if c.startswith("qt_")]
    out = [_row("FAIL", f"live model_total and p_over_emp the same with and without the qtotals shadow ({season} Week {week})", bad, len(pw))]
    # 2 Oct 2026: recomputing a played week from today's stored tables can drift from the pred_v3 that priced it (the tables
    # move after the week: forecast history extended, weather readings refreshed); that is not the shadow, so it warns apart
    gap = float((mt - pw.model_total).abs().max()) if len(pw) else float("nan")
    drift = [] if (len(pw) and gap <= 1e-9 and np.allclose(pe.values, pw.p_over_emp.values, atol=1e-12, rtol=0, equal_nan=True)) else [f"recomputed model_total / p_over_emp differ from pred_v3 (largest total gap {gap:.3g})"]
    out.append(_row("WARN", f"the stored tables still reproduce pred_v3's totals ({season} Week {week})", drift, len(pw)))
    return out


# ---- logs (2 Oct 2026: rule_history appended by position) ----

def logs_by_column(paths: list) -> list:
    """Every appended log's rows have as many fields as its header (picks.append_csv widens the header for a new
    column; an append by position shifts every later row)."""
    bad, n = [], 0
    for p in paths:
        if not Path(p).exists():
            continue
        with open(p, newline="", encoding="utf-8") as fh:
            rd = csv.reader(fh); head = next(rd, None)
            if head is None:
                continue
            for i, r in enumerate(rd, start=2):
                n += 1
                if len(r) != len(head):
                    bad.append(f"{Path(p).name} line {i} ({len(r)} fields, header {len(head)})"); break
    return [_row("FAIL", "appended logs: every row has the header's fields (rule_history, pred_history, the bet trackers)", bad, n)]


# ---- the leak tests (2 Oct 2026: #384 same-game referee prior) ----

def leaks(season: int | None = None, week: int | None = None) -> list:
    """audit.leakage_test (2024: future weeks corrupted, the 2024 Week 9 games' own scores corrupted) and audit.own_game_shift
    on the newest played week of the current season. Every change must be 0. The stored tree fits are never rewritten."""
    from . import audit as A, model as M, lines as LN
    with M.trees_cache_read_only():
        lk = A.leakage_test()
        if season is None:
            g = pd.read_parquet(OUT / "games.parquet"); s, w = LN.current_week(g)
            played = g[(g.season == s) & (g.week < w) & (g.game_type == "REG") & g.home_score.notna()]
            season, week = (s, int(played.week.max())) if len(played) else (None, None)
        own = A.own_game_shift(season, week) if season is not None else None
    rows = []
    for k, what in (("max_rating_change_after_corrupting_future", "ratings for 2024 Weeks 1-9 unchanged when later games are corrupted"),
                    ("max_prediction_change_after_corrupting_targets", "2024 Weeks 1-9 predictions unchanged when later targets are corrupted"),
                    ("max_prediction_change_after_corrupting_own_game", "2024 Week 9 games' own predictions unchanged when their own scores are corrupted")):
        v = float(lk[k]); rows.append(("FAIL" if v > 1e-9 else "OK", f"future-data leak: {what} (audit.leakage_test)", f"largest change {v:.6g}"))
    if own is None:
        rows.append(("WARN", "same-game leak: newest played week's own predictions unchanged (audit.own_game_shift)", "no played week this season yet"))
    else:
        rows.append(("FAIL" if own > 1e-9 else "OK", f"same-game leak: {season} Week {week} games' own predictions unchanged when their own scores are corrupted (audit.own_game_shift)", f"largest change {own:.6g}"))
    return rows


# ---- runners ----

def cheap() -> list:
    """Every check but the leak tests, on the tables, the forecasts, the trackers and the page as they are now."""
    from . import lines as LN, wind_live as WL, ratings as R
    rows = []
    def run(name, fn):
        try:
            rows.extend(fn())
        except Exception as e:  # noqa  (a check that cannot run is a failure, never a pass)
            rows.append(("FAIL", f"{name}: check ran", f"{type(e).__name__}: {str(e)[:120]}"))
    g = pd.read_parquet(OUT / "games.parquet"); season, week = LN.current_week(g)
    wk = _js(WEB / "week.js") if (WEB / "week.js").exists() else {}
    cards = wk.get("games") if [wk.get("season"), wk.get("week")] == [season, week] else None
    st = {}
    out = R.qbs_out_now(g, st)[1]   # {team: QB ids ruled out this week}, the set the swap and qb_out read
    # (a failed injury load is health.py's FAIL row "QB-out check loaded the injury reports"; the swap reads the same set)
    run("QB priced", lambda: qb_priced_not_out(pd.read_parquet(OUT / "features_asof.parquet", columns=["game_id", "team", "qb_id"]), g, out, season, week))
    if st.get("status") == "no injury file":   # a machine without the league's report (Matt's laptop) cannot see who the run counted out
        rows.append(("OK", "qb_out = 1 only when last game's starting QB is ruled out (picks week)", "skipped: the league injury file is not on this machine (the weekly run checks it)"))
    else:
        run("qb_out", lambda: qb_out_is_last_starter(pd.read_parquet(OUT / "trends_asof.parquet", columns=["game_id", "team", "qb_out"]),
                                                     pd.read_parquet(OUT / "qb_games.parquet", columns=["game_id", "season", "week", "team", "qb_id", "dropbacks"]), g, out, season, week))
    wind, rain, temp = WL.readings(), WL.rain_readings(), WL.temp_readings()
    run("retractable roofs", lambda: retractable_roofs(g, cards))
    run("weather under a roof", lambda: no_weather_under_roof(g, wind, rain, temp, cards))
    run("forecast timing", lambda: forecasts_before_kickoff(pd.read_csv(WX / "forecast_history.csv") if (WX / "forecast_history.csv").exists() else pd.DataFrame(),
                                                            pd.read_csv(WX / "wind_live.csv") if (WX / "wind_live.csv").exists() else pd.DataFrame()))
    run("plausible weather", lambda: plausible_weather(wind, rain, temp, pd.read_csv(WX / "forecast_latest.csv") if (WX / "forecast_latest.csv").exists() else None))
    run("bets before kickoff", lambda: bets_before_kickoff({k: pd.read_csv(TR / f) if (TR / f).exists() else None for k, f in LIVE_BETS.items()}, g))
    if cards is not None:
        run("stale chances", lambda: chances_at_card_line(cards, g))
    html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
    from .clv import RULE_FILES
    meta = _js(WEB / "meta.js") if (WEB / "meta.js").exists() else {}
    run("shadows", lambda: shadows_stay_off(html, (meta.get("picks") or {}).get("rules", []), RULE_FILES))
    from .qtotals import DIST as QT_DIST, _sha as qt_sha
    web = {f.name: f.read_text(encoding="utf-8") for f in sorted(WEB.glob("*.js"))}
    run("qt shadow", lambda: qt_stays_off(html, web, cards, json.loads(QT_DIST.read_text()) if QT_DIST.exists() else None, qt_sha(OUT / "pred_v3.parquet")))
    pm = REP / f"picks_{season}_wk{week}.md"
    run("one unit", lambda: one_unit(html, pm.read_text(encoding="utf-8") if pm.exists() else None))
    run("logs", lambda: logs_by_column([RUNS / "rule_history.csv", RUNS / "pred_history.csv"] + [TR / f for f in LIVE_BETS.values()]))
    return rows


def tie_rows(rows: list) -> None:
    """The cheap checks as tie-check rows (tie_check.check_page): a FAIL does not tie; a WARN ties and goes to the health
    page through warnlog."""
    from .warnlog import warn
    for lv, what, det in cheap():
        if lv == "WARN":
            warn("standing checks", f"{what}: {det}")
        rows.append((f"standing check: {what}", det if lv != "OK" else "ok", "ok" if lv != "WARN" else det, lv != "FAIL"))


def main(with_leaks: bool = True) -> bool:
    rows = cheap() + (leaks() if with_leaks else [])
    if with_leaks:   # the weekly run's standing step: the live totals recomputed with and without the shadow (seconds)
        try:
            rows += qt_isolated()
        except Exception as e:  # noqa  (a check that cannot run is a failure, never a pass)
            rows.append(("FAIL", "qt isolated: check ran", f"{type(e).__name__}: {str(e)[:120]}"))
    from .warnlog import warn
    for lv, what, det in rows:
        if lv == "WARN":
            warn("standing checks", f"{what}: {det}")
    fails = [r for r in rows if r[0] == "FAIL"]
    L = ["# Standing checks", "", "Every bug class fixed on 1-2 Oct 2026, checked again (nflmodel/standing_checks.py; the list: docs/wiki/checks.md).", "",
         "| Level | Check | Detail |", "|---|---|---|"] + [f"| {lv} | {w} | {d} |" for lv, w, d in rows] + ["", f"Result: {'FAIL' if fails else 'PASS'} ({len(rows) - len(fails)} of {len(rows)})"]
    REP.mkdir(exist_ok=True); (REP / "standing_checks.md").write_text("\n".join(L) + "\n", encoding="utf-8"); print("\n".join(L))
    return not fails


if __name__ == "__main__":
    sys.exit(0 if main("--no-leaks" not in sys.argv) else 1)
