"""Pre-kickoff wind and gust forecasts for 2018-2023 (1 Oct 2026, Matt: "go", after the friend's-model wind test, which
only had the weather that happened before 2024; reports/friend_ideas.md section 3). Two free archives, both read from
GitHub's network (this sandbox cannot reach them), for every played outdoor or open-roof game at a US stadium:

  - Iowa Environmental Mesonet's MOS archive: the National Weather Service's model output statistics at the stadium's
    airport. GFS MOS (wind, every season) and the National Blend text product NBS (wind and gust, from 7 Nov 2018), each
    at two runs: the 12Z run the day before kickoff (d1) and the last run out before kickoff (d0: the newest 00/06/12/18Z
    run issued at least 5 hours before kickoff, about 4 to publish and 1 to bet). Knots converted to mph.
  - Open-Meteo's previous-runs archive, Japan's global model (jma_gsm, the one model it keeps back to 2018, wind only):
    the forecast one and two days before (d1, d2) and the latest (d0).

Each value is the mean over the first three hours from kickoff (gust: the largest), interpolated between forecast hours
(held flat past the run's first or last hour when that is within 2 hours).
Every row is printed as it lands ("ROW," prefix) so a probe run cut off by its 15-minute limit still hands over what it
fetched; --ingest reads those lines from a saved job log into data/weather/forecast_history.csv.

    python -m nflmodel.forecast_history --seasons 2018 --weeks 1-9          (on the runner, through probe.yml)
    python -m nflmodel.forecast_history --ingest job_log.txt                (here)
    python -m nflmodel.forecast_history --backfill                          (the weekly run: 10 minutes a run until 2018-2025 is in)
    python -m nflmodel.forecast_history --extend                            (here, 1 Oct 2026: GFS temperature and rain chance for stored games)
"""
from __future__ import annotations
import argparse, re, time
import numpy as np, pandas as pd, requests
from .features import OUT, ROOT
from .weather import STADIUM

WX = ROOT / "data" / "weather"; OUTF = WX / "forecast_history.csv"
MOS = "https://mesonet.agron.iastate.edu/api/1/mos.json"
OM = "https://previous-runs-api.open-meteo.com/v1/forecast"
KT = 1.15078
NBS_FROM = pd.Timestamp("2018-11-07", tz="UTC")
# the stadium's nearest MOS airport; stadiums a team has left are keyed by stadium name (checked against the airport list)
STATION = {"BUF": "KBUF", "GB": "KGRB", "CHI": "KMDW", "NE": "KOWD", "NYG": "KTEB", "NYJ": "KTEB", "PHI": "KPHL", "PIT": "KPIT",
           "CLE": "KBKL", "BAL": "KBWI", "WAS": "KDCA", "CIN": "KLUK", "KC": "KMCI", "DEN": "KDEN", "SEA": "KBFI", "SF": "KSJC",
           "TEN": "KBNA", "JAX": "KJAX", "MIA": "KMIA", "TB": "KTPA", "CAR": "KCLT", "ARI": "KPHX", "ATL": "KATL", "NO": "KMSY",
           "IND": "KIND", "DET": "KDTW", "MIN": "KMSP", "HOU": "KHOU", "DAL": "KDFW", "LAC": "KSNA", "LA": "KCQT"}
OLD_SITE = {"Los Angeles Memorial Coliseum": ("KCQT", (34.0141, -118.2879)), "StubHub Center": ("KTOA", (33.8644, -118.2611)),
            "Oakland-Alameda County Coliseum": ("KOAK", (37.7516, -122.2005)), "Hard Rock Stadium": ("KMIA", STADIUM.get("MIA")),
            "TIAA Bank Stadium": ("KJAX", STADIUM.get("JAX"))}
COLS = ["game_id", "season", "week", "home_team", "station", "kickoff_utc",
        "gfs_wind_d1", "gfs_wind_d0", "gfs_run_d0", "nbs_wind_d1", "nbs_gust_d1", "nbs_wind_d0", "nbs_gust_d0", "nbs_run_d0",
        "jma_wind_d2", "jma_wind_d1", "jma_wind_d0"]
# 1 Oct 2026 (experiments/weather_forecast_retest.py): the same two GFS MOS runs' temperature (deg F, mean over the first 3 h)
# and chance of precipitation (percent, the largest 6-hour p06 / 12-hour p12 whose period overlaps the first 3 h)
EXTRA = ["gfs_temp_d1", "gfs_pop_d1", "gfs_pop12_d1", "gfs_temp_d0", "gfs_pop_d0", "gfs_pop12_d0"]
OLD_COLS = COLS[:]
COLS = COLS + EXTRA


def _get(url, params, tries=3):
    for a in range(tries):
        try:
            r = requests.get(url, params=params, timeout=15)
            if r.status_code == 404:
                return None
            r.raise_for_status(); return r.json()
        except Exception as e:  # noqa
            if a == tries - 1:
                print("failed", url, params.get("station") or params.get("latitude"), params.get("runtime") or params.get("start_date"), str(e)[:80], flush=True)
                return None
            time.sleep(2 * (a + 1))


def _window(t: pd.Series, v: pd.Series, ko: pd.Timestamp, how="mean"):
    """The value over kickoff to kickoff + 3 h, interpolated between forecast hours (None when the forecast does not span it)."""
    ok = v.notna() & t.notna()
    t, v = t[ok], v[ok].astype(float)
    if len(t) < 2 or t.min() > ko + pd.Timedelta(hours=2) or t.max() < ko + pd.Timedelta(hours=1):
        return None   # a run whose first hour lands up to 2 h after kickoff (MOS starts 6 h after the run) is held flat back to kickoff
    x = (t - ko).dt.total_seconds().values / 3600; grid = np.arange(0, 3.01, 0.5)
    y = np.interp(grid, x, v.values)
    return round(float(y.max() if how == "max" else y.mean()), 1)


def _period_max(t: pd.Series, v: pd.Series, ko: pd.Timestamp, hours: int):
    """The largest value whose period (the `hours` before its valid time, as MOS reports p06 / p12) overlaps kickoff to kickoff + 3 h."""
    ok = v.notna() & t.notna() & (t > ko) & (t - pd.Timedelta(hours=hours) < ko + pd.Timedelta(hours=3))
    return round(float(v[ok].max()), 1) if ok.any() else None


def mos_all(station, model, run: pd.Timestamp, ko: pd.Timestamp) -> dict:
    """One MOS run over the game's first 3 h: wind (mph, mean), gust (mph, largest), temperature (deg F, mean) and the chance
    of precipitation (percent, the largest 6-hour and 12-hour chance whose period overlaps the game)."""
    out = dict.fromkeys(["wind", "gust", "temp", "pop", "pop12"])
    j = _get(MOS, {"station": station, "model": model, "runtime": run.strftime("%Y-%m-%dT%H:%MZ")})
    rows = (j or {}).get("data") or []
    if not rows:
        return out
    df = pd.DataFrame(rows); df.columns = [c.lower() for c in df.columns]
    if "ftime" not in df:
        return out
    t = pd.to_datetime(df.ftime, utc=True)
    num = lambda c, k=1.0: pd.to_numeric(df[c], errors="coerce") * k if c in df else pd.Series(np.nan, index=df.index)
    # MOS writes 999 (temperature) and 99 (wind, gust) for a missing hour (KTOA overnight, 2018): read as missing; the one stored
    # game it had hit, 2018_16_BAL_LAC, was refetched (1 Oct 2026)
    tmp, pct = num("tmp").where(lambda x: x < 900), lambda c: num(c).where(lambda x: x <= 100)
    kn = lambda c: num(c).where(lambda x: x < 99) * KT
    out.update(wind=_window(t, kn("wsp"), ko), gust=_window(t, kn("gst"), ko, "max"), temp=_window(t, tmp, ko),
               pop=_period_max(t, pct("p06"), ko, 6), pop12=_period_max(t, pct("p12"), ko, 12))
    return out


def mos(station, model, run: pd.Timestamp, ko: pd.Timestamp):
    """Wind (mph, mean over the game's first 3 h) and gust (mph, largest) from one MOS run."""
    m = mos_all(station, model, run, ko)
    return m["wind"], m["gust"]


def last_run(ko: pd.Timestamp) -> pd.Timestamp:
    """The newest 00/06/12/18Z run issued at least 5 hours before kickoff."""
    r = (ko - pd.Timedelta(hours=5)).floor("6h")
    return r


def jma(lat, lon, ko: pd.Timestamp):
    day = ko.strftime("%Y-%m-%d"); nxt = (ko + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    j = _get(OM, {"latitude": lat, "longitude": lon, "start_date": day, "end_date": nxt, "models": "jma_gsm", "timezone": "GMT", "wind_speed_unit": "mph",
                  "hourly": "wind_speed_10m,wind_speed_10m_previous_day1,wind_speed_10m_previous_day2"})
    h = (j or {}).get("hourly")
    if not h:
        return None, None, None
    t = pd.to_datetime(pd.Series(h["time"])).dt.tz_localize("UTC")
    s = lambda k: pd.to_numeric(pd.Series(h.get(k, [None] * len(t))), errors="coerce")
    return _window(t, s("wind_speed_10m_previous_day2"), ko), _window(t, s("wind_speed_10m_previous_day1"), ko), _window(t, s("wind_speed_10m"), ko)


def games(seasons, weeks=None, played=True) -> pd.DataFrame:
    g = pd.read_parquet(OUT / "games.parquet")
    g = g[g.season.isin(seasons) & g.kickoff_et.notna() & (g.home_score.notna() if played else g.home_score.isna()) & g.roof.fillna("outdoors").isin(["outdoors", "open"])].copy()
    if weeks:
        g = g[g.week.between(*weeks)]
    st = g.stadium.fillna("")
    g["station"] = [OLD_SITE[s][0] if s in OLD_SITE else STATION.get(t) for s, t in zip(st, g.home_team)]
    g["latlon"] = [OLD_SITE[s][1] if s in OLD_SITE else STADIUM.get(t) for s, t in zip(st, g.home_team)]
    abroad = g.location.eq("Neutral") & ~st.isin(list(OLD_SITE))   # London, Munich, Frankfurt, Mexico City: no US airport forecast
    return g[~abroad & g.station.notna()].sort_values("kickoff_et")


def one(r) -> dict:
    """Every forecast for one game (a row of games())."""
    ko = pd.Timestamp(r.kickoff_et).tz_localize("America/New_York").tz_convert("UTC")
    d1, d0 = _runs(ko)
    row = {"game_id": r.game_id, "season": r.season, "week": r.week, "home_team": r.home_team, "station": r.station, "kickoff_utc": ko.strftime("%Y-%m-%dT%H:%MZ")}
    row.update(_gfs(r.station, d1, d0, ko)); row["gfs_run_d0"] = d0.strftime("%Y-%m-%dT%HZ")
    if ko >= NBS_FROM:
        row["nbs_wind_d1"], row["nbs_gust_d1"] = mos(r.station, "NBS", d1, ko)
        row["nbs_wind_d0"], row["nbs_gust_d0"] = mos(r.station, "NBS", d0, ko); row["nbs_run_d0"] = d0.strftime("%Y-%m-%dT%HZ")
    if r.latlon:
        row["jma_wind_d2"], row["jma_wind_d1"], row["jma_wind_d0"] = jma(r.latlon[0], r.latlon[1], ko)
    return row


def _runs(ko: pd.Timestamp):
    """The two runs: 12Z the day before kickoff (Eastern date) and the last run out at least 5 hours before kickoff."""
    d1 = (ko.tz_convert("America/New_York").normalize() - pd.Timedelta(days=1)).tz_convert("UTC").floor("D") + pd.Timedelta(hours=12)
    return d1, last_run(ko)


def _gfs(station, d1, d0, ko) -> dict:
    row = {}
    for tag, run in (("d1", d1), ("d0", d0)):
        m = mos_all(station, "GFS", run, ko)
        row.update({f"gfs_wind_{tag}": m["wind"], f"gfs_temp_{tag}": m["temp"], f"gfs_pop_{tag}": m["pop"], f"gfs_pop12_{tag}": m["pop12"]})
    return row


def extend(threads=8) -> str:
    """Fill the GFS temperature and precipitation-chance columns (EXTRA) for stored games that lack them, `threads` games at
    a time; wind already stored is kept as it was."""
    from concurrent.futures import ThreadPoolExecutor
    h = pd.read_csv(OUTF, dtype=str).astype(object)
    for c in EXTRA:
        h[c] = h[c] if c in h else None
    todo = h.index[h[EXTRA].isna().all(axis=1)]

    def job(i):
        r = h.loc[i]; ko = pd.Timestamp(r.kickoff_utc)
        d1, d0 = _runs(ko)
        return i, {k: v for k, v in _gfs(r.station, d1, d0, ko).items() if k in EXTRA}
    t0 = time.time()
    with ThreadPoolExecutor(threads) as ex:
        for n, (i, row) in enumerate(ex.map(job, todo), 1):
            for k, v in row.items():
                h.at[i, k] = None if v is None else str(v)
            if n % 100 == 0:
                print(n, "of", len(todo), f"{time.time() - t0:.0f}s", flush=True)
    h[COLS].to_csv(OUTF, index=False)
    return f"{len(todo)} games extended in {time.time() - t0:.0f}s; " + ", ".join(f"{c} {int(h[c].notna().sum())}" for c in EXTRA)


def _line(row) -> str:
    return "ROW," + ",".join("" if row.get(c) is None or (isinstance(row.get(c), float) and np.isnan(row[c])) else str(row[c]) for c in COLS)


def main(seasons, weeks=None):
    print("ROWHEAD," + ",".join(COLS), flush=True)
    for r in games(seasons, weeks).itertuples():
        print(_line(one(r)), flush=True)


def backfill(seasons=range(2018, 2026), budget=600, threads=8) -> str:
    """The weekly run's step: fetch the games the stored history lacks, several at a time, for at most budget seconds, and
    store them; a no-op once every game is in. Never raises (a source being down only leaves games for next week)."""
    from concurrent.futures import ThreadPoolExecutor, as_completed
    try:
        old = pd.read_csv(OUTF, dtype=str) if OUTF.exists() else pd.DataFrame(columns=COLS)
        g = games(list(seasons)); g = g[~g.game_id.isin(set(old.game_id))]
        if not len(g):
            return f"complete: {len(old)} games stored"
        t0, rows = time.time(), []
        with ThreadPoolExecutor(threads) as ex:
            futs = {}
            it = iter(g.itertuples())
            for r in it:   # keep `threads` games in flight; stop handing out new ones once the budget is spent
                futs[ex.submit(one, r)] = r.game_id
                if len(futs) >= threads:
                    break
            while futs:
                done = next(as_completed(list(futs)))
                futs.pop(done)
                try:
                    rows.append(done.result())
                except Exception as e:  # noqa
                    print("game failed", e, flush=True)
                if time.time() - t0 < budget:
                    nxt = next(it, None)
                    if nxt is not None:
                        futs[ex.submit(one, nxt)] = nxt.game_id
        new = pd.DataFrame(rows, columns=COLS).astype(str).replace({"None": np.nan, "nan": np.nan})
        vals = [c for c in COLS[6:] if "_run_" not in c]
        if not new[vals].notna().any().any():
            return f"no forecast came back for {len(new)} games (sources down?): nothing stored"   # kept for next week rather than stored blank
        out = pd.concat([old, new]).drop_duplicates("game_id", keep="last").sort_values(["season", "kickoff_utc"])
        WX.mkdir(parents=True, exist_ok=True); out.to_csv(OUTF, index=False)
        return f"{len(new)} games fetched in {time.time() - t0:.0f}s, {len(out)} stored, {len(g) - len(new)} left"
    except Exception as e:  # noqa
        return f"skipped: {type(e).__name__}: {str(e)[:120]}"


def ingest(path) -> pd.DataFrame:
    """ROW lines from saved probe job logs (any number of files) into the stored history; a later fetch of a game wins."""
    rows = []
    for p in ([path] if isinstance(path, str) else path):
        for line in open(p, encoding="utf-8", errors="ignore"):
            m = re.search(r"\bROW,(.*)$", line.rstrip("\n"))
            if m:
                v = m.group(1).split(",")
                if len(v) == len(OLD_COLS):   # a log from before the temperature and rain columns
                    v = v + [""] * len(EXTRA)
                if len(v) == len(COLS):
                    rows.append(v)
    new = pd.DataFrame(rows, columns=COLS).replace("", np.nan)
    old = pd.read_csv(OUTF, dtype=str) if OUTF.exists() else pd.DataFrame(columns=COLS)
    out = pd.concat([old, new]).drop_duplicates("game_id", keep="last").sort_values(["season", "kickoff_utc"])
    WX.mkdir(parents=True, exist_ok=True); out.to_csv(OUTF, index=False)
    print(f"{len(new)} rows read, {len(out)} games stored")
    print(out.drop(columns=["game_id", "home_team", "station", "kickoff_utc", "week", "gfs_run_d0", "nbs_run_d0"]).astype({"season": int}).groupby("season").agg(lambda s: int(s.notna().sum())).to_string())
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--seasons", default="2018-2023"); ap.add_argument("--weeks", default=""); ap.add_argument("--ingest", nargs="*")
    ap.add_argument("--backfill", action="store_true"); ap.add_argument("--extend", action="store_true")
    a = ap.parse_args()
    if a.extend:
        print(extend())
    elif a.backfill:
        print(backfill())
    elif a.ingest:
        ingest(a.ingest)
    else:
        lo, hi = (a.seasons.split("-") + [None])[:2]
        wk = tuple(int(x) for x in (a.weeks.split("-") * 2)[:2]) if a.weeks else None
        main(list(range(int(lo), int(hi or lo) + 1)), wk)
