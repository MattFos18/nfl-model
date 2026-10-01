"""The live wind forecast for the wind-under rule (1 Oct 2026, Matt: "build the best version"; experiments/wind_forecast.py).
For every unplayed outdoor or open-roof game at a US stadium within the forecast range, the same two forecasts the rule
was measured on: the NWS GFS MOS at the stadium's airport (the newest run out, issued at least 4 hours ago and at least 5
hours before kickoff) and Japan's global model from Open-Meteo, each the mean over the game's first three hours; the
reading is their mean (nflmodel/forecast_history.py does the same for 2018-2025). Run on every line watch and weekly run;
a row is appended when a game's reading changes. Writes data/weather/wind_live.csv.

    python -m nflmodel.wind_live
"""
from __future__ import annotations
import datetime as dt
import numpy as np, pandas as pd
from . import forecast_history as FH

F = FH.WX / "wind_live.csv"
COLS = ["ts", "game_id", "season", "week", "kickoff_utc", "station", "gfs_run", "gfs_wind", "jma_wind", "wind_mean"]
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
        gfs, _ = FH.mos(r.station, "GFS", run_, ko)
        jma = FH.jma(r.latlon[0], r.latlon[1], ko)[2] if r.latlon else None
        vals = [v for v in (gfs, jma) if v is not None]
        rows.append({"ts": ts, "game_id": r.game_id, "season": r.season, "week": r.week, "kickoff_utc": ko.strftime("%Y-%m-%dT%H:%MZ"), "station": r.station,
                     "gfs_run": run_.strftime("%Y-%m-%dT%HZ"), "gfs_wind": gfs, "jma_wind": jma, "wind_mean": round(float(np.mean(vals)), 1) if vals else None})
    df = pd.DataFrame(rows, columns=COLS)
    if not len(df):
        return 0
    if F.exists():
        old = pd.read_csv(F)
        last = old.sort_values("ts").drop_duplicates("game_id", keep="last").set_index("game_id")[["gfs_wind", "jma_wind"]]
        prev = last.reindex(df.game_id)
        cur = df.set_index("game_id")[["gfs_wind", "jma_wind"]]
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


if __name__ == "__main__":
    print(run())
    if F.exists():
        print(pd.read_csv(F).tail(20).to_string())
