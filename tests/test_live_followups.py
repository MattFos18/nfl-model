"""Follow-ups to the live-failure review (2 Oct 2026): ESPN names with suffixes match, a failed model step records no
bets, forecast gaps are counted, and every weather fallback says so (nflmodel/warnlog.py)."""
import pandas as pd
import pytest

from nflmodel import data_checks as DC, forecast_history as FH, lines as LN, model as M, players as PL, warnlog as W, weekly as WK, wind_live as WL


def _msgs():
    return [w["message"] for w in W.recent()]


# (a) ESPN names against the roster
# the seven Out players ESPN listed on 2 Oct 2026 that matched no roster player, with the roster's own name for each
SEVEN = [("CHI", "Anthony Johnson Jr.", "Anthony Johnson"), ("HOU", "Mario Edwards Jr.", "Mario Edwards"), ("LAC", "Trey Pipkins III", "Trey Pipkins"),
         ("MIA", "Robert Beal Jr.", "Rob Beal Jr."), ("NO", "Travis Etienne Jr.", "Travis Etienne"), ("NYJ", "Kiko Mauigoa", "Francisco Mauigoa"), ("PIT", "Gabriel Rubio", "Gabe Rubio")]


def test_name_key_drops_suffixes_and_punctuation():
    assert PL.name_key("Travis Etienne Jr.") == PL.name_key("Travis Etienne") == "travisetienne"
    assert PL.name_key("Trey Pipkins III") == PL.name_key("trey pipkins") and PL.name_key("T.J. Watt") == "tjwatt"
    assert PL.name_key("Vincent Anthony Jr.") == "vincentanthony"


def test_the_seven_misses_match_except_the_nicknames(tmp_path, monkeypatch):
    monkeypatch.setattr(LN, "current_week", lambda games: (2026, 4))
    now_et = pd.Timestamp.now(tz="America/New_York").tz_localize(None); now = pd.Timestamp.now("UTC").tz_localize(None)
    raw, out = tmp_path / "raw", tmp_path / "processed"; (raw / "injuries").mkdir(parents=True); (raw / "rosters").mkdir(); out.mkdir()
    pd.DataFrame({"game_id": ["2026_03_A_B", "2026_04_A_C"], "season": 2026, "week": [3, 4], "game_type": "REG", "home_team": ["B", "C"], "away_team": "A",
                  "kickoff_et": [now_et - pd.Timedelta(days=2), now_et + pd.Timedelta(days=2)]}).to_parquet(out / "games.parquet")
    pd.DataFrame({"season": [2026], "week": [4], "team": ["ZZZ"], "gsis_id": ["X0"], "full_name": ["Other"], "position": ["WR"], "report_status": [None],
                  "report_primary_injury": [None]}).to_parquet(raw / "injuries" / "injuries_2026.parquet")
    pd.DataFrame({"team": [t for t, _, _ in SEVEN], "gsis_id": [f"G{i}" for i in range(7)], "espn_id": None, "full_name": [r for _, _, r in SEVEN], "position": "LB", "week": 4}).to_parquet(raw / "rosters" / "roster_weekly_2026.parquet")
    pd.DataFrame({"team": [t for t, _, _ in SEVEN], "espn_id": None, "name": [e for _, e, _ in SEVEN], "position": "LB", "status": "Out", "date": "", "detail": "Knee", "return_date": "",
                  "fetched_at": (now - pd.Timedelta(hours=1)).isoformat()}).to_csv(raw / "injuries" / "espn_injuries.csv", index=False)
    monkeypatch.setattr(PL, "RAW", raw); monkeypatch.setattr(PL, "OUT", out)
    inj = PL.load_injuries([2026])
    assert sorted(inj[(inj.week == 4) & (inj.report_status == "Out")].gsis_id) == ["G0", "G1", "G2", "G4"]   # the four with a suffix on one side
    assert PL.ESPN_MERGE["unmatched"] == ["MIA Robert Beal Jr.", "NYJ Kiko Mauigoa", "PIT Gabriel Rubio"]   # nicknames: still listed for the health warning


# (b) a failed model step records nothing
def test_failed_model_step_skips_picks_and_records_no_bets(monkeypatch):
    from nflmodel import picks as P, tracker
    monkeypatch.setattr(P, "table", lambda *a: pytest.fail("priced on the previous run's predictions"))
    monkeypatch.setattr(tracker, "record_model_picks", lambda *a: pytest.fail("recorded bets"))
    monkeypatch.setitem(WK._RUN_AT, "run_at", None)
    log = [{"step": "model", "status": "error", "detail": "RuntimeError", "seconds": 1.0}]
    assert WK.pick_week(log, 2026, 4, "r1") is None
    assert [(r["step"], r["status"]) for r in log[1:]] == [(s, "skipped") for s in WK.PICK_STEPS]
    assert all("model step failed" in r["detail"] for r in log[1:])


def test_ok_model_step_still_picks(monkeypatch, tmp_path):
    from nflmodel import picks as P, tracker, refresh
    called = []
    monkeypatch.setattr(P, "table", lambda s, w: pd.DataFrame({"bet": [""]}))
    monkeypatch.setattr(P, "markdown", lambda *a: ""); monkeypatch.setattr(P, "log_run", lambda *a: called.append("log"))
    monkeypatch.setattr(tracker, "record_model_picks", lambda *a: called.append("record")); monkeypatch.setattr(refresh, "write", lambda: called.append("fp"))
    monkeypatch.setattr(WK, "REP", tmp_path); monkeypatch.setitem(WK._RUN_AT, "run_at", None)
    log = [{"step": "model", "status": "ok", "detail": "", "seconds": 1.0}]
    assert WK.pick_week(log, 2026, 4, "r1") is not None and called == ["log", "record", "fp"]


# (c) forecast coverage
def test_forecast_gaps_are_counted_as_warnings():
    now = pd.Timestamp("2026-10-02 12:00")
    played = pd.DataFrame({"game_id": ["g1", "g2", "2026_04_PIT_CLE"]})
    up = pd.DataFrame({"game_id": ["u1", "u2", "u_far"], "kickoff_et": [now + pd.Timedelta(hours=10), now + pd.Timedelta(hours=20), now + pd.Timedelta(days=5)]})
    wind = {"g1": 5, "2026_04_PIT_CLE": 8, "u1": 4, "u2": 3}; temp = {"g1": 60, "u1": 50}; rain = {"g1": 10, "2026_04_PIT_CLE": 20, "u1": 0, "u2": 0}
    rows = DC.check_forecasts(played, up, wind, temp, rain, now)
    assert all(ok for _, ok, _ in rows)                                   # warnings, never failures
    assert "1 partial (no temperature 1), 1 missing (warning)" in rows[0][2] and "2026_04_PIT_CLE" in rows[0][2]
    assert "1 short (warning): u2 (no temperature)" in rows[1][2] and "u_far" not in rows[1][2]
    assert len(_msgs()) == 2


# (d) wind_live's fallbacks
def test_live_rain_from_an_older_pull_is_warned(tmp_path, monkeypatch):
    f = tmp_path / "wind_live.csv"; ko = (pd.Timestamp.now("UTC") + pd.Timedelta(days=1)).strftime("%Y-%m-%dT%H:%MZ")
    pd.DataFrame({"ts": ["2026-10-02T10-00-00Z", "2026-10-02T12-00-00Z"], "game_id": "g1", "kickoff_utc": ko, "wind_mean": [9.0, 9.5],
                  "gfs_pop": [40.0, None], "gfs_temp": [50.0, None]}).to_csv(f, index=False)
    monkeypatch.setattr(WL, "F", f); monkeypatch.setattr(FH, "OUTF", tmp_path / "none.csv")
    assert WL.rain_readings() == {"g1": 40.0} and WL.temp_readings() == {"g1": 50.0}   # the reading is unchanged
    m = _msgs()
    assert any("g1: newest pull (2026-10-02T12-00-00Z) has no rain chance" in x for x in m) and any("no temperature" in x for x in m)


def test_one_model_wind_and_an_empty_pull_are_warned(tmp_path, monkeypatch):
    ko = pd.Timestamp.now(tz="America/New_York").tz_localize(None) + pd.Timedelta(hours=30)
    g = pd.DataFrame({"game_id": ["g1"], "season": [2026], "week": [4], "kickoff_et": [ko], "station": ["KPIT"], "latlon": [(40.4, -80.0)]})
    monkeypatch.setattr(LN, "current_week", lambda games: (2026, 4))
    monkeypatch.setattr(pd, "read_parquet", lambda *a, **k: pd.DataFrame())
    monkeypatch.setattr(FH, "games", lambda *a, **k: g)
    monkeypatch.setattr(FH, "mos_all", lambda *a: {"wind": None, "pop": None, "temp": 55.0})
    monkeypatch.setattr(FH, "jma", lambda *a: (None, 7.0, 6.0)); monkeypatch.setattr(FH, "jma_pre_kickoff", lambda *a: 7.0)
    monkeypatch.setattr(WL, "F", tmp_path / "wind_live.csv")
    assert WL.run() == 1
    m = _msgs()
    assert any("gave no wind, rain chance" in x for x in m) and any("the Japan model alone" in x for x in m)
    assert pd.read_csv(tmp_path / "wind_live.csv").wind_mean.tolist() == [7.0]   # the reading is unchanged


def test_games_table_failure_keeps_games_abroad_and_says_so(tmp_path, monkeypatch):
    h = tmp_path / "fh.csv"; pd.DataFrame({"game_id": ["2025_01_KC_LAC"], "gfs_wind_d0": [5.0]}).to_csv(h, index=False)
    monkeypatch.setattr(FH, "OUTF", h)
    monkeypatch.setattr(FH, "abroad_ids", lambda: (_ for _ in ()).throw(FileNotFoundError("games.parquet")))
    assert list(WL._history().game_id) == ["2025_01_KC_LAC"]
    assert any("keep the games abroad" in x for x in _msgs())


# (e) the model's weather readers
@pytest.mark.parametrize("fn,name", [("_rain_readings", "rain_readings"), ("_wind_readings", "readings"), ("_temp_readings", "temp_readings")])
def test_model_weather_reader_failure_is_a_warning(monkeypatch, fn, name):
    monkeypatch.setattr(WL, name, lambda: (_ for _ in ()).throw(ValueError("bad csv")))
    assert getattr(M, fn)() == {}
    assert any("readings failed (ValueError: bad csv)" in x for x in _msgs())


def test_health_shows_recent_warnings(tmp_path, monkeypatch):
    from nflmodel import health as H
    W.warn("wind_live", "g1: wind reading from GFS MOS alone")
    monkeypatch.setattr(H, "DATA", tmp_path); monkeypatch.setattr(H, "REP", tmp_path)
    monkeypatch.setattr(pd, "read_parquet", lambda *a, **k: pd.DataFrame())
    H.main()
    assert "| WARN | warnings from wind_live (last 36 hours) | 1: g1: wind reading from GFS MOS alone |" in (tmp_path / "health.md").read_text()
