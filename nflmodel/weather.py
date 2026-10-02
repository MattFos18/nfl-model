"""Kickoff weather forecasts for upcoming outdoor games, from Open-Meteo (free, no key).

For every unplayed game in the next 10 days at an outdoor stadium, fetch the hourly forecast at the stadium
and take the hour of kickoff: temperature (F), wind (mph), precipitation probability. Written to
data/weather/forecast_latest.csv and appended to data/weather/forecast_log.csv, so the forecast the model
used for each game is kept. The weekly run patches games.parquet temp/wind for those games before pricing.

A game keeps its forecast after kickoff (27 Sep 2026): run() used to fetch only games still to kick off, so the file
lost a game the moment it started, and every re-price before nflverse posted the score (six weekly runs on one Sunday)
priced it as typical weather and the card said "Weather TBD" for a game that was played in 13 mph wind. Now the
fetch reaches back a day (Open-Meteo's past_days) for unplayed games that have kicked off, and a game older than that
and still unscored carries its last good row forward (status "carried") until the score arrives.

Note: this sandbox cannot reach api.open-meteo.com (egress policy); it runs in GitHub Actions.
Usage: python -m nflmodel.weather
"""
from __future__ import annotations
import datetime as dt
import numpy as np, pandas as pd, requests
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT, WX = ROOT / "data" / "processed", ROOT / "data" / "weather"

# stadium coordinates and every game's site (stadiums left behind, stadiums abroad, games the schedule lists at the wrong
# place) live in nflmodel/venues.py (2 Oct 2026); STADIUM is re-exported for older readers
from .venues import STADIUM, INTL, site as venue_site


WEATHER_BUDGET_S = 240.0   # the whole step's ceiling on fetching (23 Sep 2026): a dropped API once stalled a weekly run for forty minutes
_deadline = [None]


PAST_DAYS = 1   # the fetch covers yesterday too, so a game that kicked off keeps a kickoff reading until it is scored (27 Sep 2026)


def kickoff_forecast(lat, lon, kickoff: pd.Timestamp, tz="America/New_York"):
    import time
    if _deadline[0] is None:
        _deadline[0] = time.time() + WEATHER_BUDGET_S
    last = None
    for attempt in range(3):        # Open-Meteo drops a few of 15 quick requests from a runner; back off and retry, inside the budget
        if time.time() > _deadline[0]:
            raise RuntimeError(f"weather budget of {WEATHER_BUDGET_S:.0f}s spent; the earlier forecast stands")
        try:
            r = requests.get("https://api.open-meteo.com/v1/forecast", timeout=20, params={
                "latitude": lat, "longitude": lon, "hourly": "temperature_2m,wind_speed_10m,wind_gusts_10m,precipitation_probability,precipitation",
                "temperature_unit": "fahrenheit", "wind_speed_unit": "mph", "forecast_days": 10, "past_days": PAST_DAYS, "timezone": tz})
            r.raise_for_status()
            break
        except Exception as e:  # noqa
            last = e
            time.sleep(2 * (attempt + 1))
    else:
        raise last
    h = r.json()["hourly"]
    times = pd.to_datetime(h["time"])
    k = kickoff.floor("h")
    if k not in set(times):
        return None
    i = list(times).index(k)
    return {"temp": h["temperature_2m"][i], "wind": h["wind_speed_10m"][i], "gust": h["wind_gusts_10m"][i],
            "precip_prob": h["precipitation_probability"][i], "precip": h["precipitation"][i]}


def run(days_ahead=10) -> pd.DataFrame:
    games = pd.read_parquet(OUT / "games.parquet")
    now = pd.Timestamp.now(tz="America/New_York").tz_localize(None)
    # every unplayed game from a day ago (a kicked-off game keeps its kickoff reading) to days_ahead out
    up = games[games.home_score.isna() & (games.kickoff_et >= now - pd.Timedelta(days=PAST_DAYS)) & (games.kickoff_et <= now + pd.Timedelta(days=days_ahead))]
    prev = last_good()
    rows = []
    for g in up.itertuples():
        if g.roof in ("dome", "closed"):
            continue
        st = venue_site(getattr(g, "stadium_id", None), g.home_team)   # 2 Oct 2026: the old city-name match never found Wembley or Azteca, so those games read the home team's US stadium
        loc = (st["lat"], st["lon"]) if st["lat"] is not None else None
        if loc is None:
            continue
        try:
            f = kickoff_forecast(loc[0], loc[1], g.kickoff_et)
        except Exception as e:  # noqa
            rows.append({"game_id": g.game_id, "kickoff_et": g.kickoff_et, "status": f"error:{str(e)[:60]}"})
            continue
        if f is None:
            rows.append({"game_id": g.game_id, "kickoff_et": g.kickoff_et, "status": "beyond forecast range"})
            continue
        rows.append({"game_id": g.game_id, "kickoff_et": g.kickoff_et, "status": "ok", **f})
    df = pd.DataFrame(rows)
    df["fetched_at"] = now.strftime("%Y-%m-%d %H:%M")
    df = carry_forward(df, prev, games, now)
    WX.mkdir(parents=True, exist_ok=True)
    df.to_csv(WX / "forecast_latest.csv", index=False)
    log = WX / "forecast_log.csv"
    df[df.status != "carried"].to_csv(log, mode="a", header=not log.exists(), index=False)   # the log holds fetches, never a copy
    return df


def last_good() -> pd.DataFrame:
    """The last good reading of every game fetched so far: the latest file and the log (the log, so a game the old
    run() had already dropped from the latest file gets its reading back), newest fetch per game."""
    fr = [pd.read_csv(f) for f in (WX / "forecast_latest.csv", WX / "forecast_log.csv") if f.exists()]
    if not fr:
        return pd.DataFrame(columns=["game_id", "status", "fetched_at"])
    x = pd.concat(fr, ignore_index=True)
    x = x[x.status.isin(["ok", "carried"]) & x.fetched_at.notna()]
    return x.sort_values("fetched_at").drop_duplicates("game_id", keep="last")


def carry_forward(df: pd.DataFrame, prev: pd.DataFrame, games: pd.DataFrame, now: pd.Timestamp) -> pd.DataFrame:
    """Keep the last good reading of every unplayed game this fetch did not get a good row for (kicked off more than
    PAST_DAYS ago, or the API dropped it this run): the game is priced with the forecast it had, never with nothing.
    The carried row keeps its own fetched_at (the tie check reads how old it is) and the status "carried"."""
    if not len(prev) or "status" not in prev.columns:
        return df
    unplayed = set(games[games.home_score.isna()].game_id)
    good = set(df[df.status == "ok"].game_id) if len(df) else set()
    keep = prev[prev.status.isin(["ok", "carried"]) & prev.game_id.isin(unplayed) & ~prev.game_id.isin(good)].copy()
    if not len(keep):
        return df
    keep["status"] = "carried"
    df = df[~df.game_id.isin(keep.game_id)] if len(df) else df   # a failed fetch this run gives way to the carried reading
    return pd.concat([df, keep], ignore_index=True)


USE_WITHIN_DAYS = 4   # a kickoff forecast is used only this close to the game; further out the league-typical weather stands in


def usable_forecast() -> pd.DataFrame:
    """The latest forecast rows the model may use: fetched without error (or carried forward from the last good fetch
    once the game has kicked off) and within USE_WITHIN_DAYS of kickoff.
    A forecast five or more days out is too loose to move a line on, so those games are priced as typical weather
    (7 mph, not cold, no rain) until a later run, Thursday for Sunday games, is close enough."""
    f = WX / "forecast_latest.csv"
    if not f.exists():
        return pd.DataFrame(columns=["game_id", "temp", "wind", "precip_prob", "precip", "days_out"]).set_index("game_id")
    fc = pd.read_csv(f)
    fc = fc[fc.status.isin(["ok", "carried"])].copy()   # carried: the last good reading of a game that has kicked off (run)
    fc["days_out"] = (pd.to_datetime(fc.kickoff_et) - pd.to_datetime(fc.fetched_at)).dt.total_seconds() / 86400
    return fc[fc.days_out <= USE_WITHIN_DAYS].set_index("game_id")


def status_by_game(games: pd.DataFrame) -> dict:
    """What the card should say about the weather for each unplayed game: dome, forecast in use (and how many days
    out it was fetched), too far out to use, fetch failed, beyond the forecast range, or never fetched."""
    f = WX / "forecast_latest.csv"
    fc = pd.read_csv(f).set_index("game_id") if f.exists() else pd.DataFrame()
    now = pd.Timestamp.now(tz="America/New_York").tz_localize(None)
    out = {}
    for g in games[games.home_score.isna()].itertuples():
        if g.roof in ("dome", "closed"):
            out[g.game_id] = {"s": "dome"}
            continue
        if len(fc) and g.game_id in fc.index:
            r = fc.loc[g.game_id]
            fetched = pd.to_datetime(r.fetched_at)
            days = (pd.to_datetime(r.kickoff_et) - fetched).total_seconds() / 86400
            st = str(r.status)
            s = "far" if days > USE_WITHIN_DAYS else ("forecast" if st in ("ok", "carried") else ("range" if st.startswith("beyond") else "failed"))
            out[g.game_id] = {"s": s, "days": round(days, 1), "fetched": fetched.strftime("%Y-%m-%d %H:%M"), "use_within": USE_WITHIN_DAYS}
        else:
            days = (g.kickoff_et - now).total_seconds() / 86400 if pd.notna(g.kickoff_et) else None
            out[g.game_id] = {"s": "none", "days": None if days is None else round(days, 1), "use_within": USE_WITHIN_DAYS}
    return out


def mos_readings() -> tuple[dict, dict, dict]:
    """(wind, temperature, rain chance) by game_id from nflmodel/wind_live.py: the GFS MOS and Japan model readings the
    backtest prices played games on (model.priced_weather), roofed games left out. A reader that fails gives {} and a
    warning (every game then falls back to Open-Meteo, each one logged)."""
    from . import wind_live as WL
    from .warnlog import warn
    out = []
    for name, fn in (("wind", WL.readings), ("temperature", WL.temp_readings), ("rain", WL.rain_readings)):
        try:
            out.append(fn())
        except Exception as e:  # noqa
            warn("live weather", f"GFS MOS {name} readings failed ({type(e).__name__}: {str(e)[:100]}): unplayed games priced on Open-Meteo")
            out.append({})
    return tuple(out)


def live_source(games: pd.DataFrame, fc: pd.DataFrame | None = None, mos: tuple | None = None) -> dict:
    """game_id -> what each unplayed outdoor game's weather is priced on now: {"wind", "temp", "pop" (MOS chance of rain,
    %), "precip_prob", "precip" (Open-Meteo's), and "wind_src", "temp_src", "rain_src"}, each source "mos" (the
    wind_live reading, the one the backtest prices on), "open-meteo" (the fallback: no MOS reading yet, as 66 to 96
    hours out) or None (typical weather). Domes and closed roofs are left out. One rule for the model's inputs
    (apply_to_games, trends' rain), the card and the re-price fingerprint (2 Oct 2026, re-audit item 3)."""
    fc = usable_forecast() if fc is None else fc
    wind, temp, pop = mos_readings() if mos is None else mos
    out = {}
    for r in games[games.home_score.isna() & ~games.roof.isin(["dome", "closed"])].itertuples():
        gid = r.game_id; o = fc.loc[gid] if gid in fc.index else None
        om = lambda c: None if o is None or c not in o.index or pd.isna(o[c]) else float(o[c])
        d = {"precip_prob": om("precip_prob"), "precip": om("precip")}
        for k, rd in (("wind", wind), ("temp", temp)):
            d[k], d[f"{k}_src"] = (float(rd[gid]), "mos") if gid in rd else ((om(k), "open-meteo") if om(k) is not None else (None, None))
        d["pop"] = float(pop[gid]) if gid in pop else None
        d["rain_src"] = "mos" if gid in pop else ("open-meteo" if o is not None else None)
        out[gid] = d
    return out


def rain_call(d: dict) -> bool:
    """The rain call the model makes from one live_source entry, as trends.py makes it: the MOS chance at model.RAIN_FC
    (50%+), else Open-Meteo's chance at trends.RAIN_PROB (50%+) or trends.RAIN_MM (1 mm+) in the kickoff hour. 2 Oct
    2026 (review of #399): the re-price fingerprint called any Open-Meteo precipitation above 0 rain."""
    from .model import RAIN_FC
    from .trends import RAIN_PROB, RAIN_MM
    if d.get("rain_src") == "mos":
        return bool(d["pop"] is not None and d["pop"] >= RAIN_FC)
    if d.get("rain_src") == "open-meteo":
        return bool((d.get("precip_prob") or 0.0) >= RAIN_PROB or (d.get("precip") or 0.0) >= RAIN_MM)
    return False


def log_fallbacks(src: dict) -> list:
    """Warn (stderr and a health warning, nflmodel/warnlog.py) for every unplayed game priced on Open-Meteo because no
    MOS reading exists; returns those game ids."""
    from .warnlog import warn
    fell = []
    for gid, d in sorted(src.items()):
        parts = [k for k in ("wind", "temp", "rain") if d[f"{k}_src"] == "open-meteo"]
        if parts:
            fell.append(gid)
            warn("live weather", f"{gid}: no GFS MOS reading for {', '.join(parts)}; priced on Open-Meteo")
    return fell


def apply_to_games(games: pd.DataFrame, mos: bool = True) -> pd.DataFrame:
    """Fill temp/wind for unplayed outdoor games with the weather they are priced on (live_source): the GFS MOS / Japan
    reading wind_live keeps (the same readings the backtest prices played games on, model.priced_weather), else the
    latest usable Open-Meteo forecast (within USE_WITHIN_DAYS of kickoff; each such fallback logged); everything else
    unplayed is left blank so the model uses the league-typical weather. mos=False: Open-Meteo only (the props, whose
    passing-wind factor reads it). A played game whose game-time weather nflverse has not posted yet keeps the kickoff
    reading it was priced with.
    2 Oct 2026 (re-audit item 3): unplayed games took wind and temperature from Open-Meteo while the backtest prices on
    GFS MOS; for 2026_04_DAL_HOU that was 9.9 against 11.4 mph."""
    fc = usable_forecast()
    g = games.copy()
    un = g.home_score.isna()
    g.loc[un, "temp"] = np.nan
    g.loc[un, "wind"] = np.nan
    m = g.game_id.isin(fc.index) & un
    g.loc[m, "temp"] = g.loc[m, "game_id"].map(fc.temp)
    g.loc[m, "wind"] = g.loc[m, "game_id"].map(fc.wind)
    if mos:
        src = live_source(g, fc)
        log_fallbacks(src)
        for k in ("wind", "temp"):
            ids = {gid for gid, d in src.items() if d[f"{k}_src"] == "mos"}
            mm = un & g.game_id.isin(ids)
            g.loc[mm, k] = g.loc[mm, "game_id"].map({gid: src[gid][k] for gid in ids})
    # a played game nflverse has not given its game-time weather yet (the schedule posts scores within hours and the
    # weather days later: Week 3 of 2026 had 1 of 8 outdoor games filled the Sunday evening) keeps the kickoff reading
    # it was priced with, from the last good fetch; nflverse's reading replaces it when it lands (27 Sep 2026)
    lg = last_good().set_index("game_id")
    pl = ~un & g.temp.isna() & ~g.roof.isin(["dome", "closed"]) & g.game_id.isin(lg.index)
    g.loc[pl, "temp"] = g.loc[pl, "game_id"].map(lg.temp)
    g.loc[pl, "wind"] = g.loc[pl, "game_id"].map(lg.wind)
    return g


if __name__ == "__main__":
    df = run()
    print(df.to_string())
