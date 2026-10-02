"""The live wind forecast for the wind-under rule (1 Oct 2026, Matt: "build the best version"; experiments/wind_forecast.py).
For every unplayed outdoor or open-roof game at a US stadium within the forecast range, the same two forecasts the rule
was measured on: the NWS GFS MOS at the stadium's airport (the newest run out, issued at least 4 hours ago and at least 5
hours before kickoff) and Japan's global model from Open-Meteo (its day-before forecast, FH.jma_pre_kickoff), each the
mean over the game's first three hours; the
reading is their mean (nflmodel/forecast_history.py does the same for 2018-2025). The same GFS MOS run also gives the
chance of rain the totals equation reads (gfs_pop: the largest 6-hour chance overlapping the first three hours; 1 Oct
2026, experiments/rain_points.py) and the temperature the cold-under shadow reads (gfs_temp, mean over the first three hours;
2 Oct 2026, picks.COLD_UNDER). Run on every line watch and weekly run; a row is appended when a game's reading
changes. Writes data/weather/wind_live.csv.

    python -m nflmodel.wind_live
"""
from __future__ import annotations
import datetime as dt
import numpy as np, pandas as pd
from pathlib import Path
from . import forecast_history as FH
from .warnlog import warn

F = FH.WX / "wind_live.csv"
COLS = ["ts", "game_id", "season", "week", "kickoff_utc", "station", "gfs_run", "gfs_wind", "jma_wind", "wind_mean", "gfs_pop", "gfs_temp"]
RANGE_H = 66   # GFS MOS (MAV) runs 72 hours out; a reading needs the game's first three hours inside it
# 2 Oct 2026 (review of #399): by DUE_H hours before kickoff every run wind_live may read (issued 4 to 10 hours before now)
# reaches the game's first three hours (72 - 3 - 10 = 59); from RANGE_H to DUE_H the newest run may not reach it yet
# (the log has GFS blanks 63 to 66 hours out), so a game there with no MOS reading is expected, not a failure
DUE_H = 59
# 2 Oct 2026 (review of #399): a live reading for a game still to play counts only while its GFS run is at most one run
# (6 hours) behind the newest run wind_live would read for that game now (newest_run). One run of slack covers a late
# NWS posting or a skipped line watch; older than that, the pulls are failing and the reading is dropped (the game falls
# back to Open-Meteo, logged, and health.py fails it inside DUE_H)
MAX_RUN_LAG_H = 6


def newest_run(ko: pd.Timestamp, now: pd.Timestamp) -> pd.Timestamp:
    """The GFS MOS run wind_live reads for a game kicking off at `ko` (UTC): the newest 00/06/12/18Z run issued at least
    4 hours ago (so it is out) and at least 5 hours before kickoff (FH.last_run)."""
    return min(FH.last_run(ko), (now - pd.Timedelta(hours=4)).floor("6h"))


def run() -> int:
    from .lines import current_week
    g0 = pd.read_parquet(FH.OUT / "games.parquet"); season, week = current_week(g0)
    g = FH.games([season], (week, week + 1), played=False)
    now = pd.Timestamp.now(tz="UTC")
    ts = dt.datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%SZ"); rows = []
    for r in g.itertuples():
        ko = pd.Timestamp(r.kickoff_et).tz_localize("America/New_York").tz_convert("UTC")
        if ko <= now or ko > now + pd.Timedelta(hours=RANGE_H):
            continue
        run_ = newest_run(ko, now)
        m = FH.mos_all(r.station, "GFS", run_, ko); gfs = m["wind"]
        # Japan's model under the stored rule (2 Oct 2026): the day-before value, never a run newer than the GFS cutoff
        jma = FH.jma_pre_kickoff(*FH.jma(r.latlon[0], r.latlon[1], ko)[1:], ko, now) if r.latlon else None
        vals = [v for v in (gfs, jma) if v is not None]
        # 2 Oct 2026 (code review): a pull that came back empty, and a two-model mean that became one model, were silent
        gone = [k for k, v in (("wind", gfs), ("rain chance", m["pop"]), ("temperature", m["temp"])) if v is None]
        if gone:
            warn("wind_live", f"{r.game_id}: GFS MOS run {run_:%Y-%m-%dT%HZ} at {r.station} gave no {', '.join(gone)}")
        if len(vals) == 1:
            warn("wind_live", f"{r.game_id}: wind reading from {'GFS MOS' if gfs is not None else 'the Japan model'} alone (the other forecast is missing), not the two-model mean")
        rows.append({"ts": ts, "game_id": r.game_id, "season": r.season, "week": r.week, "kickoff_utc": ko.strftime("%Y-%m-%dT%H:%MZ"), "station": r.station,
                     "gfs_run": run_.strftime("%Y-%m-%dT%HZ"), "gfs_wind": gfs, "jma_wind": jma, "wind_mean": round(float(np.mean(vals)), 1) if vals else None, "gfs_pop": m["pop"], "gfs_temp": m["temp"]})
    df = pd.DataFrame(rows, columns=COLS)
    if not len(df):
        return 0
    # 2 Oct 2026 (review of #399): the GFS pull fails without raising (a network error comes back empty), so a full outage
    # logged Japan-only readings and the line watch saw no error. Every game inside DUE_H coming back empty raises after
    # the rows are written: the line watch's errors (health.wind_pull_row) and the weekly step show it
    ko_ = pd.to_datetime(df.kickoff_utc.str.replace("Z", "")).dt.tz_localize("UTC")
    inside = df[ko_ <= now + pd.Timedelta(hours=DUE_H)]
    outage = len(inside) > 0 and bool(inside[["gfs_wind", "gfs_pop", "gfs_temp"]].isna().values.all())
    n = _append(df)
    if outage:
        raise RuntimeError(f"GFS MOS gave nothing for any of the {len(inside)} games within {DUE_H} hours of kickoff")
    return n


def _append(df: pd.DataFrame) -> int:
    """Append the rows whose reading or GFS run changed; returns how many."""
    # gfs_run too (2 Oct 2026, review of #399): a new run with the same values logs a row, so the log's run is the newest
    # one read and the age limit (_fresh) can tell a current reading from a stale one
    keys = ["gfs_run", "gfs_wind", "jma_wind", "gfs_pop", "gfs_temp"]
    if F.exists():
        old = pd.read_csv(F)
        if list(old.columns) != COLS:   # a log written before gfs_pop or gfs_temp: rewritten once with the new columns (empty for old rows)
            old = old.reindex(columns=COLS); old.to_csv(F, index=False)
        last = old.sort_values("ts").drop_duplicates("game_id", keep="last").set_index("game_id")[keys]
        prev = last.reindex(df.game_id)
        cur = df.set_index("game_id")[keys]
        same = ((cur == prev) | (cur.isna() & prev.isna())).all(axis=1).values
        df = df[~same]
    if len(df):
        FH.WX.mkdir(parents=True, exist_ok=True); df.to_csv(F, mode="a", header=not F.exists(), index=False)
    return len(df)


def due(now: pd.Timestamp | None = None, games: pd.DataFrame | None = None) -> set:
    """Games that must have a MOS reading now: unplayed, outdoor or open roof, at a US stadium with an airport station (the
    games run() reads; games abroad never get one) and kicking off within DUE_H hours. health.py fails such a game
    priced on Open-Meteo (2 Oct 2026, review of #399)."""
    now = pd.Timestamp.now(tz="UTC") if now is None else now
    if games is None:
        g0 = pd.read_parquet(FH.OUT / "games.parquet", columns=["season"])
        games = FH.games(sorted(int(x) for x in g0.season.unique()), played=False)
    ko = pd.to_datetime(games.kickoff_et).dt.tz_localize("America/New_York").dt.tz_convert("UTC")
    return set(games.game_id[(ko > now) & (ko <= now + pd.Timedelta(hours=DUE_H))])


def gfs_missing() -> set:
    """Games whose newest live row has no GFS MOS wind: the wind reading is Japan's model alone (the GFS pull came back
    empty; expected only further out than DUE_H). health.py fails such a game inside DUE_H (2 Oct 2026, review of #399)."""
    if not F.exists():
        return set()
    lv = pd.read_csv(F).sort_values("ts").drop_duplicates("game_id", keep="last")
    return set(lv.game_id[lv.gfs_wind.isna()])


def _history() -> pd.DataFrame:
    """The stored 2018-2025 forecasts, less games played abroad (2 Oct 2026: the 2025 London and Madrid games had been
    read at Jacksonville's and Miami's airports because the schedule listed them at those stadiums)."""
    h = pd.read_csv(FH.OUTF)
    try:
        return h[~h.game_id.isin(FH.abroad_ids())]
    except Exception as e:  # noqa  (no games table: the history as stored, and say so: games abroad are back in)
        warn("wind_live", f"games table not read ({type(e).__name__}: {str(e)[:100]}): the stored forecasts keep the games abroad")
        return h


def _roofed() -> set:
    """Games now known or assumed to be under a roof (games.parquet roof dome or closed): no weather reading applies to
    them, even one logged before the roof was known (2 Oct 2026: 2026_04_DAL_HOU at Houston fired the wind under)."""
    try:
        g = pd.read_parquet(Path(__file__).resolve().parent.parent / "data" / "processed" / "games.parquet", columns=["game_id", "roof"])
        return set(g.game_id[g.roof.isin(["dome", "closed"])])
    except Exception as e:  # noqa
        warn("wind_live", f"could not read roofs ({type(e).__name__}: {str(e)[:100]}); readings not filtered by roof")
        return set()


def _fresh(lv: pd.DataFrame, now: pd.Timestamp | None = None) -> pd.DataFrame:
    """Live rows less those of games still to play whose GFS run is more than MAX_RUN_LAG_H behind the newest run for that
    game (newest_run); each dropped game warns. Games that have kicked off keep their last reading (the one they were
    priced on). 2 Oct 2026 (review of #399): readings had no age limit, so a failing pull kept pricing an old run."""
    now = pd.Timestamp.now(tz="UTC") if now is None else now
    if not len(lv):
        return lv
    ko = pd.to_datetime(lv.kickoff_utc.astype(str).str.replace("Z", ""), errors="coerce").dt.tz_localize("UTC")
    run = pd.to_datetime(lv.get("gfs_run", pd.Series(None, index=lv.index, dtype=object)).astype(str).str.replace("Z", ""), format="%Y-%m-%dT%H", errors="coerce").dt.tz_localize("UTC")
    keep = []
    for gid, k, r_, ts in zip(lv.game_id, ko, run, lv.ts):
        if pd.isna(k) or k <= now:
            keep.append(True); continue
        due = newest_run(k, now)
        ok = pd.notna(r_) and r_ >= due - pd.Timedelta(hours=MAX_RUN_LAG_H)
        if not ok:
            warn("wind_live", f"{gid}: reading from GFS run {'unknown' if pd.isna(r_) else f'{r_:%Y-%m-%dT%HZ}'} (logged {ts}) is more than {MAX_RUN_LAG_H} hours behind the newest run ({due:%Y-%m-%dT%HZ}); not used")
        keep.append(bool(ok))
    return lv[keep]


def _live_latest(lv: pd.DataFrame, col: str, what: str) -> pd.DataFrame:
    """Each game's newest live row with a value in `col`. Where the newest pull had none, the older value stands (as
    before) and a warning says so (2 Oct 2026, code review: a failed MOS pull quietly kept an older reading)."""
    newest = lv.sort_values("ts").drop_duplicates("game_id", keep="last")
    have = lv[lv[col].notna()].sort_values("ts").drop_duplicates("game_id", keep="last")
    ko = pd.to_datetime(newest.kickoff_utc.str.replace("Z", ""), errors="coerce") if "kickoff_utc" in newest else pd.Series(pd.NaT, index=newest.index)
    live = newest[col].isna() & ~(ko < pd.Timestamp.now("UTC").tz_localize(None) - pd.Timedelta(days=2))   # games still to play or just played
    for gid, ts in zip(newest.game_id[live], newest.ts[live]):
        old = have[have.game_id == gid]
        if len(old):
            warn("wind_live", f"{gid}: newest pull ({ts}) has no {what}; using the {old.ts.iloc[0]} reading")
    return _fresh(have)


def readings() -> dict:
    """game_id -> the wind reading the rule uses: the live log's newest for games still to play (dropped when its GFS run
    is stale: _fresh), the stored history for 2018-2025 (the mean of the pre-kickoff forecasts there: GFS and NBS last run, Japan's day-before run)."""
    out = {}
    hf = FH.OUTF
    if hf.exists():
        h = _history()
        # runs issued before kickoff only (FH.PRE_KICKOFF_WIND; 2 Oct 2026: Japan's d1, its d0 was issued at or after kickoff)
        m = h[[c for c in FH.PRE_KICKOFF_WIND if c in h]].apply(pd.to_numeric, errors="coerce").mean(axis=1)
        out.update({gid: float(v) for gid, v in zip(h.game_id, m) if pd.notna(v)})
    if F.exists():
        lv = _fresh(pd.read_csv(F).sort_values("ts").drop_duplicates("game_id", keep="last"))
        out.update({gid: float(v) for gid, v in zip(lv.game_id, lv.wind_mean) if pd.notna(v)})
    r = _roofed()
    return {k: v for k, v in out.items() if k not in r}


def rain_readings() -> dict:
    """game_id -> the GFS MOS chance of rain (percent) the totals equation reads: the stored history's last run (the
    day-before run where it is missing) for played games, the live log's newest for games still to play."""
    out = {}
    if FH.OUTF.exists():
        h = _history()
        v = pd.to_numeric(h.get("gfs_pop_d0"), errors="coerce").fillna(pd.to_numeric(h.get("gfs_pop_d1"), errors="coerce"))
        out.update({gid: float(x) for gid, x in zip(h.game_id, v) if pd.notna(x)})
    if F.exists():
        lv = pd.read_csv(F)
        if "gfs_pop" in lv:
            lv = _live_latest(lv, "gfs_pop", "rain chance")
            out.update({gid: float(x) for gid, x in zip(lv.game_id, lv.gfs_pop) if gid not in out})
    r = _roofed()
    return {k: v for k, v in out.items() if k not in r}


def temp_readings() -> dict:
    """game_id -> the GFS MOS temperature (deg F, mean over the first three hours) the cold-under shadow reads (2 Oct 2026,
    picks.COLD_UNDER): the stored history's last run (the day-before run where it is missing) for played games, the live
    log's newest for games still to play (logged from 2 Oct 2026), the same order as rain_readings."""
    out = {}
    if FH.OUTF.exists():
        h = _history()
        v = pd.to_numeric(h.get("gfs_temp_d0"), errors="coerce").fillna(pd.to_numeric(h.get("gfs_temp_d1"), errors="coerce"))
        out.update({gid: float(x) for gid, x in zip(h.game_id, v) if pd.notna(x)})
    if F.exists():
        lv = pd.read_csv(F)
        if "gfs_temp" in lv:
            lv = _live_latest(lv, "gfs_temp", "temperature")
            out.update({gid: float(x) for gid, x in zip(lv.game_id, lv.gfs_temp) if gid not in out})
    r = _roofed()
    return {k: v for k, v in out.items() if k not in r}


if __name__ == "__main__":
    print(run())
    if F.exists():
        print(pd.read_csv(F).tail(20).to_string())
