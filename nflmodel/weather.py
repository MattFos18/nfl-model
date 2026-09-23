"""Kickoff weather forecasts for upcoming outdoor games, from Open-Meteo (free, no key).

For every unplayed game in the next 10 days at an outdoor stadium, fetch the hourly forecast at the stadium
and take the hour of kickoff: temperature (F), wind (mph), precipitation probability. Written to
data/weather/forecast_latest.csv and appended to data/weather/forecast_log.csv, so the forecast the model
used for each game is kept. The weekly run patches games.parquet temp/wind for those games before pricing.

Note: this sandbox cannot reach api.open-meteo.com (egress policy); it runs in GitHub Actions.
Usage: python -m nflmodel.weather
"""
from __future__ import annotations
import datetime as dt
import numpy as np, pandas as pd, requests
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT, WX = ROOT / "data" / "processed", ROOT / "data" / "weather"

# home stadium coordinates (lat, lon); dome/closed-roof teams are skipped by the roof field anyway
STADIUM = {"ARI": (33.5276, -112.2626), "ATL": (33.7554, -84.4010), "BAL": (39.2780, -76.6227), "BUF": (42.7738, -78.7870),
           "CAR": (35.2258, -80.8528), "CHI": (41.8623, -87.6167), "CIN": (39.0955, -84.5161), "CLE": (41.5061, -81.6995),
           "DAL": (32.7473, -97.0945), "DEN": (39.7439, -105.0201), "DET": (42.3400, -83.0456), "GB": (44.5013, -88.0622),
           "HOU": (29.6847, -95.4107), "IND": (39.7601, -86.1639), "JAX": (30.3240, -81.6373), "KC": (39.0489, -94.4839),
           "LV": (36.0909, -115.1833), "LAC": (33.9535, -118.3392), "LA": (33.9535, -118.3392), "MIA": (25.9580, -80.2389),
           "MIN": (44.9736, -93.2575), "NE": (42.0909, -71.2643), "NO": (29.9511, -90.0812), "NYG": (40.8135, -74.0745),
           "NYJ": (40.8135, -74.0745), "PHI": (39.9008, -75.1675), "PIT": (40.4468, -80.0158), "SF": (37.4032, -121.9698),
           "SEA": (47.5952, -122.3316), "TB": (27.9759, -82.5033), "TEN": (36.1665, -86.7713), "WAS": (38.9076, -76.8645)}
INTL = {"London": (51.5560, -0.2795), "Munich": (48.2188, 11.6247), "Frankfurt": (50.0686, 8.6455), "Mexico City": (19.3029, -99.1505),
        "Sao Paulo": (-23.5453, -46.4742), "Madrid": (40.4361, -3.5886), "Dublin": (53.3607, -6.2512), "Melbourne": (-37.8200, 144.9834)}


WEATHER_BUDGET_S = 240.0   # the whole step's ceiling on fetching (23 Sep 2026): a dropped API once stalled a weekly run for forty minutes
_deadline = [None]


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
                "temperature_unit": "fahrenheit", "wind_speed_unit": "mph", "forecast_days": 10, "timezone": tz})
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
    up = games[games.home_score.isna() & (games.kickoff_et >= now) & (games.kickoff_et <= now + pd.Timedelta(days=days_ahead))]
    rows = []
    for g in up.itertuples():
        if g.roof in ("dome", "closed"):
            continue
        loc = STADIUM.get(g.home_team)
        if g.location == "Neutral":
            for city, ll in INTL.items():
                if isinstance(g.stadium, str) and city.split()[0].lower() in g.stadium.lower():
                    loc = ll
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
    WX.mkdir(parents=True, exist_ok=True)
    df.to_csv(WX / "forecast_latest.csv", index=False)
    log = WX / "forecast_log.csv"
    df.to_csv(log, mode="a", header=not log.exists(), index=False)
    return df


USE_WITHIN_DAYS = 4   # a kickoff forecast is used only this close to the game; further out the league-typical weather stands in


def usable_forecast() -> pd.DataFrame:
    """The latest forecast rows the model may use: fetched without error and within USE_WITHIN_DAYS of kickoff.
    A forecast five or more days out is too loose to move a line on, so those games are priced as typical weather
    (7 mph, not cold, no rain) until a later run, Thursday for Sunday games, is close enough."""
    f = WX / "forecast_latest.csv"
    if not f.exists():
        return pd.DataFrame(columns=["game_id", "temp", "wind", "precip_prob", "precip", "days_out"]).set_index("game_id")
    fc = pd.read_csv(f)
    fc = fc[fc.status == "ok"].copy()
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
            s = "far" if days > USE_WITHIN_DAYS else ("forecast" if st == "ok" else ("range" if st.startswith("beyond") else "failed"))
            out[g.game_id] = {"s": s, "days": round(days, 1), "fetched": fetched.strftime("%Y-%m-%d %H:%M"), "use_within": USE_WITHIN_DAYS}
        else:
            days = (g.kickoff_et - now).total_seconds() / 86400 if pd.notna(g.kickoff_et) else None
            out[g.game_id] = {"s": "none", "days": None if days is None else round(days, 1), "use_within": USE_WITHIN_DAYS}
    return out


def apply_to_games(games: pd.DataFrame) -> pd.DataFrame:
    """Fill temp/wind for unplayed outdoor games from the latest usable forecast (within USE_WITHIN_DAYS of kickoff);
    everything else unplayed is left blank so the model uses the league-typical weather."""
    fc = usable_forecast()
    g = games.copy()
    un = g.home_score.isna()
    g.loc[un, "temp"] = np.nan
    g.loc[un, "wind"] = np.nan
    m = g.game_id.isin(fc.index) & un
    g.loc[m, "temp"] = g.loc[m, "game_id"].map(fc.temp)
    g.loc[m, "wind"] = g.loc[m, "game_id"].map(fc.wind)
    return g


if __name__ == "__main__":
    df = run()
    print(df.to_string())
