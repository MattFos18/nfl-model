"""At the edge of a GFS MOS run's publication the newest run comes back empty; the pull falls back to the run before it
(2 Oct 2026: at 22:00Z the 18Z run was not out, so every game priced on Japan's wind alone)."""
import pandas as pd

from nflmodel import wind_live as W


def test_empty_newest_run_falls_back_to_the_previous_run(monkeypatch, tmp_path):
    now = pd.Timestamp.now(tz="UTC").floor("h")
    ko = now + pd.Timedelta(hours=40)
    games = pd.DataFrame({"game_id": ["G1"], "season": [2026], "week": [4], "station": ["KBUF"], "latlon": [(42.9, -78.7)],
                          "kickoff_et": [ko.tz_convert("America/New_York").tz_localize(None)]})
    newest = W.newest_run(ko, now)
    asked = []

    def mos(station, model, run, ko_):
        asked.append(run)
        return ({"wind": None, "gust": None, "temp": None, "pop": None, "pop12": None} if run == newest
                else {"wind": 9.0, "gust": None, "temp": 60.0, "pop": 20.0, "pop12": 20.0})
    monkeypatch.setattr(W.FH, "games", lambda seasons, weeks, played=False: games)
    monkeypatch.setattr(W.FH, "mos_all", mos)
    monkeypatch.setattr(W.FH, "jma", lambda lat, lon, ko_: (None, None, None))
    monkeypatch.setattr(W.FH, "jma_pre_kickoff", lambda *a, **k: 7.0)
    monkeypatch.setattr(W, "F", tmp_path / "wind_live.csv")
    import nflmodel.lines as LN
    monkeypatch.setattr(LN, "current_week", lambda g: (2026, 4))
    W.run()
    out = pd.read_csv(tmp_path / "wind_live.csv")
    assert asked == [newest, newest - pd.Timedelta(hours=6)]
    assert out.gfs_wind.iloc[-1] == 9.0 and out.wind_mean.iloc[-1] == 8.0
