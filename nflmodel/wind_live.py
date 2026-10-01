"""The live wind forecast for the wind-under rule (1 Oct 2026, Matt: "build the best version"; experiments/wind_forecast.py).
For every unplayed outdoor or open-roof game at a US stadium within the forecast range, the same two forecasts the rule
was measured on: the NWS GFS MOS at the stadium's airport (the newest run out, issued at least 4 hours ago and at least 5
hours before kickoff) and Japan's global model from Open-Meteo, each the mean over the game's first three hours; the
reading is their mean (nflmodel/forecast_history.py does the same for 2018-2025). The same GFS MOS run also gives the
chance of rain the totals equation reads (gfs_pop: the largest 6-hour chance overlapping the first three hours; 1 Oct
2026, experiments/rain_points.py). Run on every line watch and weekly run; a row is appended when a game's reading
changes. Writes data/weather/wind_live.csv.

    python -m nflmodel.wind_live
"""
from __future__ import annotations
import datetime as dt
import numpy as np, pandas as pd
from . import forecast_history as FH

F = FH.WX / "wind_live.csv"
COLS = ["ts", "game_id", "season", "week", "kickoff_utc", "station", "gfs_run", "gfs_wind", "jma_wind", "wind_mean", "gfs_pop"]
RANGE_H = 66   # GFS MOS (MAV) runs 72 hours out; a reading needs the game's first three hours inside it


def run() -> int:
    from .lines import current_week
    g0 = pd.read_parquet(FH.OUT / "games.parquet"); season, week = current_week(g0)
    g = FH.games([season], (week, week + 1), played=False)
    now = pd.Timestamp.now(tz="UTC"); issued = (now - pd.Timedelta(hours=4)).floor("6h")
    ts = dt.datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%SZ"); rows = []
    for r in g.itertuples():
        ko = pd.Timestamp(r.kickoff_et).tz_localize("America/New_York").tz_convert("UTC")
        if ko <= now or ko > now + pd.Timedelta(hours=RANGE_H):
            continue
        run_ = min(FH.last_run(ko), issued)
        m = FH.mos_all(r.station, "GFS", run_, ko); gfs = m["wind"]
        jma = FH.jma(r.latlon[0], r.latlon[1], ko)[2] if r.latlon else None
        vals = [v for v in (gfs, jma) if v is not None]
        rows.append({"ts": ts, "game_id": r.game_id, "season": r.season, "week": r.week, "kickoff_utc": ko.strftime("%Y-%m-%dT%H:%MZ"), "station": r.station,
                     "gfs_run": run_.strftime("%Y-%m-%dT%HZ"), "gfs_wind": gfs, "jma_wind": jma, "wind_mean": round(float(np.mean(vals)), 1) if vals else None, "gfs_pop": m["pop"]})
    df = pd.DataFrame(rows, columns=COLS)
    if not len(df):
        return 0
    keys = ["gfs_wind", "jma_wind", "gfs_pop"]
    if F.exists():
        old = pd.read_csv(F)
        if list(old.columns) != COLS:   # the log written before gfs_pop: rewritten once with the new column (empty for old rows)
            old = old.reindex(columns=COLS); old.to_csv(F, index=False)
        last = old.sort_values("ts").drop_duplicates("game_id", keep="last").set_index("game_id")[keys]
        prev = last.reindex(df.game_id)
        cur = df.set_index("game_id")[keys]
        same = ((cur == prev) | (cur.isna() & prev.isna())).all(axis=1).values
        df = df[~same]
    if len(df):
        FH.WX.mkdir(parents=True, exist_ok=True); df.to_csv(F, mode="a", header=not F.exists(), index=False)
    return len(df)


def readings() -> dict:
    """game_id -> the wind reading the rule uses: the live log's newest for games still to play, the stored history for
    2018-2025 (the mean of the last-run forecasts there, as the study measured)."""
    out = {}
    hf = FH.OUTF
    if hf.exists():
        h = pd.read_csv(hf)
        m = h[[c for c in ["gfs_wind_d0", "nbs_wind_d0", "jma_wind_d0"] if c in h]].apply(pd.to_numeric, errors="coerce").mean(axis=1)
        out.update({gid: float(v) for gid, v in zip(h.game_id, m) if pd.notna(v)})
    if F.exists():
        lv = pd.read_csv(F).sort_values("ts").drop_duplicates("game_id", keep="last")
        out.update({gid: float(v) for gid, v in zip(lv.game_id, lv.wind_mean) if pd.notna(v)})
    return out


def rain_readings() -> dict:
    """game_id -> the GFS MOS chance of rain (percent) the totals equation reads: the stored history's last run (the
    day-before run where it is missing) for played games, the live log's newest for games still to play."""
    out = {}
    if FH.OUTF.exists():
        h = pd.read_csv(FH.OUTF)
        v = pd.to_numeric(h.get("gfs_pop_d0"), errors="coerce").fillna(pd.to_numeric(h.get("gfs_pop_d1"), errors="coerce"))
        out.update({gid: float(x) for gid, x in zip(h.game_id, v) if pd.notna(x)})
    if F.exists():
        lv = pd.read_csv(F)
        if "gfs_pop" in lv:
            lv = lv[lv.gfs_pop.notna()].sort_values("ts").drop_duplicates("game_id", keep="last")
            out.update({gid: float(x) for gid, x in zip(lv.game_id, lv.gfs_pop) if gid not in out})
    return out


if __name__ == "__main__":
    print(run())
    if F.exists():
        print(pd.read_csv(F).tail(20).to_string())
