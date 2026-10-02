"""A played game with a stored forecast is priced on it, not on the weather that happened (2 Oct 2026,
experiments/forecast_weather_backtest.py); training rows, unplayed games and domes are untouched."""
import numpy as np
import pandas as pd

from nflmodel import model as M


def frame():
    # two team-rows per game: g1 played outdoors with a forecast, g2 played in a dome, g3 unplayed, g4 played with no
    # forecast, g5 played with a wind reading only
    rows = []
    for gid, pf, dome, wind, cold, rain in [("g1", 20, 0, 3.0, 0.0, 0.0), ("g2", 24, 1, np.nan, 0.0, 0.0), ("g3", np.nan, 0, np.nan, 0.0, 0.0),
                                            ("g4", 17, 0, 12.0, 1.0, 1.0), ("g5", 21, 0, 4.0, 1.0, 1.0)]:
        for team in ("MIA", "BUF"):
            rows.append({"game_id": gid, "team": team, "home": int(team == "MIA"), "pf": pf, "dome": dome, "wind": wind, "wind_out": 0.0 if dome else (wind if not np.isnan(wind) else 7.0),
                         "cold": cold, "warm_in_cold": cold * (team == "MIA"), "rain": rain})
    return pd.DataFrame(rows)


def patch(monkeypatch):
    monkeypatch.setattr(M, "_wind_readings", lambda: {"g1": 15.0, "g2": 20.0, "g3": 18.0, "g5": 9.0})
    monkeypatch.setattr(M, "_temp_readings", lambda: {"g1": 30.0, "g2": 20.0, "g3": 10.0})
    monkeypatch.setattr(M, "_rain_readings", lambda: {"g1": 70.0, "g2": 90.0, "g3": 90.0})


def test_played_outdoor_game_is_priced_on_its_forecast(monkeypatch):
    patch(monkeypatch); f = frame(); p = M.priced_weather(f).set_index(["game_id", "team"])
    assert p.loc[("g1", "BUF"), "wind_out"] == 15.0
    assert p.loc[("g1", "BUF"), "cold"] == 1.0 and p.loc[("g1", "BUF"), "rain"] == 1.0
    assert p.loc[("g1", "MIA"), "warm_in_cold"] == 1.0 and p.loc[("g1", "BUF"), "warm_in_cold"] == 0.0
    # a missing temperature or rain reading prices like a live game without a forecast: not cold, dry
    assert p.loc[("g5", "BUF"), "wind_out"] == 9.0 and p.loc[("g5", "BUF"), "cold"] == 0.0 and p.loc[("g5", "BUF"), "rain"] == 0.0
    assert p.loc[("g5", "MIA"), "warm_in_cold"] == 0.0


def test_domes_unplayed_and_unforecast_games_are_untouched(monkeypatch):
    patch(monkeypatch); f = frame(); p = M.priced_weather(f)
    cols = ["wind_out", "cold", "rain", "warm_in_cold"]
    for gid in ("g2", "g3", "g4"):
        pd.testing.assert_frame_equal(p[p.game_id == gid][cols], f[f.game_id == gid][cols])
    assert (f.wind_out[f.game_id == "g1"] == 3.0).all()   # the input frame (the training rows) keeps the recorded weather


def test_a_failed_reader_is_loud_not_a_quiet_return_to_recorded_weather(monkeypatch):
    import pytest
    from nflmodel import forecast_history as FH
    if not FH.OUTF.exists():
        pytest.skip("no stored forecast history")
    patch(monkeypatch); monkeypatch.setattr(M, "_temp_readings", lambda: {})
    with pytest.raises(RuntimeError):
        M.priced_weather(frame())


def test_walk_forward_trains_on_recorded_and_prices_on_forecast(monkeypatch):
    f = frame(); seen = {}
    monkeypatch.setattr(M, "prep", lambda x: x)
    monkeypatch.setattr(M, "priced_weather", lambda x: x.assign(wind_out=np.where(x.pf.notna() & (x.dome != 1), 99.0, x.wind_out)))
    def stop(train, alpha=None):
        seen["train"] = train; raise StopIteration
    monkeypatch.setattr(M, "fit_points", stop)
    f = f.assign(season=np.where(f.game_id == "g1", 2019, 2020), week=1)
    try:
        M.walk_forward(f, [2020])
    except StopIteration:
        pass
    tr = seen["train"]   # 2020's first fit trains on 2019: g1, played outdoors with a forecast, keeps its recorded wind
    assert set(tr.game_id) == {"g1"} and (tr.wind_out == 3.0).all()


def test_switch_off_restores_the_recorded_weather(monkeypatch):
    patch(monkeypatch); monkeypatch.setattr(M, "FORECAST_WEATHER", False); f = frame()
    pd.testing.assert_frame_equal(M.priced_weather(f), f)
