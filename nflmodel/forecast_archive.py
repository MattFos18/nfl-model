"""What the forecast said the day before (and two days before) for every played outdoor game's kickoff hour, from
Open-Meteo's previous-runs archive (29 Sep 2026, Matt: wire in the free historical forecasts). The live cards price
weather from a forecast, while the backtest's weather inputs are the kickoff weather that happened; this archive lets
the weather terms be scored on what was knowable before kickoff. The archive's forecasts start in 2022 (temperature)
and about 2024 (wind and rain); earlier hours come back empty and are written as blanks. One request per game;
--weeks splits a season so each piece fits a 15-minute probe run. Writes data/weather/forecast_archive.csv and prints it between CSV markers, so a probe run can hand it over from
GitHub's network (this sandbox cannot reach api.open-meteo.com).
Usage: python -m nflmodel.forecast_archive --seasons 2022-2026 [--weeks 1-9]"""
from __future__ import annotations
import argparse, time
import pandas as pd, requests
from .features import OUT, ROOT
from .weather import STADIUM, INTL
from .weather_archive import _tz

WX = ROOT / "data" / "weather"; OUTF = WX / "forecast_archive.csv"
URL = "https://previous-runs-api.open-meteo.com/v1/forecast"
VARS = {"temp": "temperature_2m", "wind": "wind_speed_10m", "gust": "wind_gusts_10m", "precip": "precipitation"}
LEADS = [1, 2]


def fetch(lat, lon, start, end, tz):
    hourly = ",".join(f"{v}_previous_day{d}" for v in VARS.values() for d in LEADS)
    for attempt in range(4):
        try:
            r = requests.get(URL, timeout=60, params={"latitude": lat, "longitude": lon, "start_date": start, "end_date": end, "hourly": hourly,
                                                      "temperature_unit": "fahrenheit", "wind_speed_unit": "mph", "precipitation_unit": "inch", "timezone": tz})
            r.raise_for_status(); j = r.json()["hourly"]
            df = pd.DataFrame({"t": pd.to_datetime(j["time"])})
            for k, v in VARS.items():
                for d in LEADS:
                    df[f"{k}_d{d}"] = j.get(f"{v}_previous_day{d}", [None] * len(df))
            return df
        except Exception as e:  # noqa
            if attempt == 3:
                print("failed", lat, lon, start, end, e, flush=True); return None
            time.sleep(3 * (attempt + 1))


def main(seasons, weeks=None):
    g = pd.read_parquet(OUT / "games.parquet")
    g = g[g.season.isin(seasons) & g.kickoff_et.notna() & g.home_score.notna() & g.roof.fillna("outdoors").isin(["outdoors", "open"])].copy()
    if weeks:
        g = g[g.week.between(*weeks)]
    g["site"] = g.home_team
    intl = g.location.fillna("").str.contains("Neutral", case=False) & g.stadium.fillna("").str.contains("|".join(INTL), case=False)
    for name in INTL:
        g.loc[intl & g.stadium.fillna("").str.contains(name, case=False), "site"] = name
    rows, cols = [], None
    # one request per game day (a season-long range was too slow for a 15-minute probe, 29 Sep 2026); every row is printed
    # as it lands ("ROW," prefix) so a run cut off by its time limit still hands over what it fetched
    for r in g.sort_values("kickoff_et").itertuples():
        lat, lon = STADIUM.get(r.site) or INTL.get(r.site) or (None, None)
        if lat is None:
            continue
        k = pd.Timestamp(r.kickoff_et).floor("h")
        try:
            local = k.tz_localize("America/New_York").tz_convert(_tz(r.site)).tz_localize(None)
        except Exception:  # noqa
            local = k
        day = local.strftime("%Y-%m-%d")
        h = fetch(lat, lon, day, day, _tz(r.site))
        if h is None:
            continue
        m = h[h.t == local]
        if not len(m):
            continue
        row = {"game_id": r.game_id, "season": r.season, "week": r.week, "site": r.site, "kickoff_local": local, **{c: m.iloc[0][c] for c in h.columns if c != "t"}}
        rows.append(row)
        if cols is None:
            cols = list(row); print("ROWHEAD," + ",".join(cols), flush=True)
        print("ROW," + ",".join("" if pd.isna(row[c]) else str(row[c]) for c in cols), flush=True)
        time.sleep(0.15)
    out = pd.DataFrame(rows)
    WX.mkdir(parents=True, exist_ok=True); out.to_csv(OUTF, index=False)
    cov = out.drop(columns=["game_id", "site", "kickoff_local", "week"]).groupby("season").agg(lambda s: int(s.notna().sum())) if len(out) else out
    print("coverage (games with a value):"); print(cov.to_string())
    print("===CSV START==="); print(out.to_csv(index=False), end=""); print("===CSV END===")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--seasons", default="2022-2026"); ap.add_argument("--weeks", default="")
    a = ap.parse_args()
    lo, hi = (a.seasons.split("-") + [None])[:2]
    wk = tuple(int(x) for x in (a.weeks.split("-") * 2)[:2]) if a.weeks else None
    main(list(range(int(lo), int(hi or lo) + 1)), wk)
