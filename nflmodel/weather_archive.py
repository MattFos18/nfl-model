"""Kickoff-hour weather for every priced game, from the Open-Meteo archive, so the backtest's wind, temperature and
rain inputs are measured the same way the live forecast is (the schedule's readings are a game-day figure of
uncertain hour). One request per stadium per season (hourly, the season's date span); the kickoff hour is picked
out per game. Outdoor and open-roof games only; international sites use their own coordinates. Writes
data/weather/archive_kickoff.csv. Runs in GitHub Actions (this sandbox cannot reach api.open-meteo.com).
Usage: python -m nflmodel.weather_archive [--seasons 2013-2025]"""
from __future__ import annotations
import argparse, sys, time
import pandas as pd, requests
from .features import OUT, ROOT
from .weather import STADIUM, INTL
WX = ROOT / "data" / "weather"; OUTF = WX / "archive_kickoff.csv"
URL = "https://archive-api.open-meteo.com/v1/archive"


def fetch(lat, lon, start, end, tz="auto"):
    for attempt in range(4):
        try:
            r = requests.get(URL, timeout=60, params={"latitude": lat, "longitude": lon, "start_date": start, "end_date": end,
                                                      "hourly": "temperature_2m,wind_speed_10m,wind_gusts_10m,precipitation", "temperature_unit": "fahrenheit",
                                                      "wind_speed_unit": "mph", "precipitation_unit": "inch", "timezone": tz})
            r.raise_for_status(); j = r.json()["hourly"]
            return pd.DataFrame({"t": pd.to_datetime(j["time"]), "temp": j["temperature_2m"], "wind": j["wind_speed_10m"], "gust": j["wind_gusts_10m"], "precip": j["precipitation"]})
        except Exception as e:  # noqa
            if attempt == 3:
                print("failed", lat, lon, start, end, e, flush=True); return None
            time.sleep(3 * (attempt + 1))


def main(seasons):
    g = pd.read_parquet(OUT / "games.parquet")
    g = g[g.season.isin(seasons) & g.kickoff_et.notna() & (g.roof.fillna("outdoors").isin(["outdoors", "open"]))].copy()
    g["site"] = g.home_team
    intl = g.location.fillna("").str.contains("Neutral", case=False) & g.stadium.fillna("").str.contains("|".join(INTL), case=False)
    for name in INTL:
        g.loc[intl & g.stadium.fillna("").str.contains(name, case=False), "site"] = name
    done = pd.read_csv(OUTF) if OUTF.exists() else pd.DataFrame(columns=["game_id"])
    g = g[~g.game_id.isin(done.game_id)]
    rows = []
    for (site, season), x in g.groupby(["site", "season"]):
        lat, lon = STADIUM.get(site) or INTL.get(site) or (None, None)
        if lat is None:
            continue
        days = pd.to_datetime(x.kickoff_et)
        h = fetch(lat, lon, (days.min() - pd.Timedelta(days=1)).strftime("%Y-%m-%d"), (days.max() + pd.Timedelta(days=1)).strftime("%Y-%m-%d"))
        if h is None:
            continue
        # kickoff_et is Eastern; the archive hours are the site's local time. Shift by the site's offset from Eastern.
        for r in x.itertuples():
            k = pd.Timestamp(r.kickoff_et).floor("h")
            # local-time difference: use the API's own timezone by matching the nearest hour after converting Eastern to the site's zone
            try:
                local = k.tz_localize("America/New_York").tz_convert(_tz(site)).tz_localize(None)
            except Exception:  # noqa
                local = k
            m = h[h.t == local]
            if len(m) == 0:
                continue
            m = m.iloc[0]
            rows.append({"game_id": r.game_id, "season": r.season, "week": r.week, "site": site, "kickoff_local": local, "temp": m.temp, "wind": m.wind, "gust": m.gust, "precip": m.precip})
        print(site, season, len(x), "games", flush=True); time.sleep(0.3)
        # write after every stadium-season so a timed-out run keeps its progress (the workflow commits on any outcome)
        new = pd.DataFrame(rows); out = pd.concat([done, new], ignore_index=True) if len(done) else new
        WX.mkdir(parents=True, exist_ok=True); out.drop_duplicates("game_id").to_csv(OUTF, index=False)
    print("wrote", len(pd.read_csv(OUTF)) if OUTF.exists() else 0, "rows", flush=True)


_TZ = {"ARI": "America/Phoenix", "DEN": "America/Denver", "KC": "America/Chicago", "DAL": "America/Chicago", "HOU": "America/Chicago", "CHI": "America/Chicago", "GB": "America/Chicago",
       "MIN": "America/Chicago", "NO": "America/Chicago", "TEN": "America/Chicago", "LV": "America/Los_Angeles", "LAC": "America/Los_Angeles", "LA": "America/Los_Angeles", "SF": "America/Los_Angeles", "SEA": "America/Los_Angeles",
       "London": "Europe/London", "Dublin": "Europe/Dublin", "Munich": "Europe/Berlin", "Frankfurt": "Europe/Berlin", "Madrid": "Europe/Madrid", "Mexico City": "America/Mexico_City", "Sao Paulo": "America/Sao_Paulo", "Melbourne": "Australia/Melbourne"}
def _tz(site): return _TZ.get(site, "America/New_York")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--seasons", default="2013-2025"); a = ap.parse_args()
    lo, hi = a.seasons.split("-"); main(range(int(lo), int(hi) + 1))
