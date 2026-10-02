"""Forecast history back to 2015 (2 Oct 2026): GFS MOS reaches 2015, Open-Meteo's Japan archive starts 1 Jan 2016, the
National Blend 7 Nov 2018. A game before an archive's start is not asked of it, and its wind reading is the mean of the
pre-kickoff forecasts that exist (GFS alone in 2015's regular season)."""
import numpy as np
import pandas as pd

from nflmodel import forecast_history as FH, wind_live as WL


def _row(ko_et, season):
    return pd.Series({"game_id": f"{season}_01_X_Y", "season": season, "week": 1, "home_team": "Y", "station": "KPHL",
                      "kickoff_et": pd.Timestamp(ko_et), "latlon": (39.9, -75.2)})


def _fake(monkeypatch):
    calls = {"jma": 0, "mos": []}
    def mos_all(station, model, run, ko):
        calls["mos"].append(model); return {"wind": 9.0, "gust": 15.0, "temp": 60.0, "pop": 20.0, "pop12": 30.0}
    def jma(lat, lon, ko):
        calls["jma"] += 1; return 7.0, 8.0, 99.0
    monkeypatch.setattr(FH, "mos_all", mos_all); monkeypatch.setattr(FH, "jma", jma)
    return calls


def test_a_2015_game_reads_gfs_only(monkeypatch):
    calls = _fake(monkeypatch)
    r = FH.one(_row("2015-09-13 13:00", 2015))
    assert calls["jma"] == 0 and set(calls["mos"]) == {"GFS"}       # no Japan (archive from 2016), no NBS (from Nov 2018)
    assert r["gfs_wind_d0"] == 9.0 and "jma_wind_d1" not in r and "nbs_wind_d0" not in r
    assert r["kickoff_utc"] == "2015-09-13T17:00Z" and r["gfs_run_d0"] == "2015-09-13T12Z"   # the last run 5+ hours before


def test_a_2016_game_reads_gfs_and_japan(monkeypatch):
    calls = _fake(monkeypatch)
    r = FH.one(_row("2016-01-03 13:00", 2015))                        # the 2015 season's last week: inside Japan's archive
    assert calls["jma"] == 1 and r["jma_wind_d1"] == 8.0 and "nbs_wind_d0" not in r


def test_backfill_starts_in_2015():
    assert FH.FIRST == 2015
    import inspect
    assert "range(FIRST," in inspect.getsource(FH.backfill)


def test_wind_reading_is_the_mean_of_what_exists(tmp_path, monkeypatch):
    f = tmp_path / "fh.csv"
    pd.DataFrame([{"game_id": "2015_01_A_B", "season": 2015, "gfs_wind_d0": 12.0, "nbs_wind_d0": np.nan, "jma_wind_d1": np.nan, "jma_wind_d0": np.nan},
                  {"game_id": "2016_01_A_B", "season": 2016, "gfs_wind_d0": 12.0, "nbs_wind_d0": np.nan, "jma_wind_d1": 8.0, "jma_wind_d0": 30.0}]).to_csv(f, index=False)
    monkeypatch.setattr(FH, "OUTF", f); monkeypatch.setattr(WL, "F", tmp_path / "none.csv")
    monkeypatch.setattr(FH, "abroad_ids", lambda: set()); monkeypatch.setattr(WL, "_roofed", lambda: set())
    r = WL.readings()
    assert r["2015_01_A_B"] == 12.0 and r["2016_01_A_B"] == 10.0
