"""Follow-ups to #399 (review of 2 Oct 2026): a weather source change re-prices, a missing MOS reading inside its window
fails the health check while expected fallbacks warn, stale MOS readings are dropped, a failed live forecast pull is a
health row, and the re-price fingerprint calls rain as trends does."""
import pandas as pd
import pytest

from nflmodel import forecast_history as FH, health as H, refresh as RF, warnlog, weather as WX, wind_live as WL


def _fp(weather):
    return {"season": 2026, "week": 4, "starters": {}, "injuries": [], "reports": [], "weather": weather}


def _w(wind=9.0, src="open-meteo", temp_src="open-meteo", rain_src="open-meteo", cold=False, rain=False):
    return {"wind": wind, "cold": cold, "rain": rain, "src": src, "temp_src": temp_src, "rain_src": rain_src}


# 1. a source change re-prices
def test_a_move_from_open_meteo_to_mos_reprices_even_with_a_small_wind_change():
    ch = RF.diff(_fp({"g": _w(9.0)}), _fp({"g": _w(9.5, "mos", "mos", "mos")}))
    assert [k for k, _ in ch] == ["weather"] and "source changed" in ch[0][1]
    # temperature or rain alone moving to MOS counts too
    assert RF.diff(_fp({"g": _w(9.0)}), _fp({"g": _w(9.0, rain_src="mos")}))
    # nothing moved: no change
    assert RF.diff(_fp({"g": _w(9.0)}), _fp({"g": _w(9.0)})) == []


def test_an_old_fingerprint_compares_the_wind_source_only():
    old = {"wind": 9.0, "cold": False, "rain": False, "src": "mos"}   # written before temp_src and rain_src were kept
    assert RF.diff(_fp({"g": old}), _fp({"g": _w(9.0, "mos")})) == []
    assert RF.diff(_fp({"g": old}), _fp({"g": _w(9.0, "open-meteo")}))


# 4. the rain call matches trends
def test_rain_call_matches_trends_rule():
    om = lambda prob, mm: {"rain_src": "open-meteo", "pop": None, "precip_prob": prob, "precip": mm}
    assert not WX.rain_call(om(30.0, 0.4))   # the old fingerprint rule (any precipitation) called this rain
    assert WX.rain_call(om(50.0, 0.0)) and WX.rain_call(om(10.0, 1.0))
    assert WX.rain_call({"rain_src": "mos", "pop": 55.0}) and not WX.rain_call({"rain_src": "mos", "pop": 45.0})
    assert not WX.rain_call({"rain_src": None, "pop": None, "precip_prob": None, "precip": None})


# 2. health: a real MOS failure fails, an expected fallback warns
def _src(w, t, r):
    return {"wind": 1.0, "temp": 50.0, "pop": 10.0, "precip_prob": 0.0, "precip": 0.0, "wind_src": w, "temp_src": t, "rain_src": r}


def test_missing_mos_inside_its_window_fails_and_expected_fallbacks_warn():
    src = {"us_due": _src("open-meteo", "open-meteo", "open-meteo"), "london": _src("open-meteo", "open-meteo", "open-meteo"),
           "far": _src("open-meteo", "open-meteo", "open-meteo"), "ok": _src("mos", "mos", "mos"), "part": _src("mos", "open-meteo", "open-meteo")}
    rows = H.weather_source_rows(src, {"us_due", "ok", "part"})
    fail = next(r for r in rows if r[0] == "FAIL")
    assert "us_due" in fail[2] and "part" in fail[2] and "london" not in fail[2] and "ok" not in fail[2]
    warn = next(r for r in rows if r[1].startswith("live weather priced"))
    assert warn[0] == "WARN" and "london" in warn[2] and "far" in warn[2] and "us_due" not in warn[2]
    rows = H.weather_source_rows({"ok": _src("mos", "mos", "mos"), "london": _src("open-meteo", "open-meteo", "open-meteo")}, {"ok"})
    assert [r[0] for r in rows] == ["OK", "WARN"]


def test_due_is_us_outdoor_games_inside_the_mos_window():
    now = pd.Timestamp("2026-10-02 20:00", tz="UTC")
    et = lambda h: (now + pd.Timedelta(hours=h)).tz_convert("America/New_York").tz_localize(None)
    g = pd.DataFrame({"game_id": ["near", "edge", "past"], "kickoff_et": [et(40), et(WL.DUE_H + 3), et(-1)]})
    assert WL.due(now, g) == {"near"}


# 3. stale readings are dropped
def _lv(now, hours_out, run):
    ko = now + pd.Timedelta(hours=hours_out)
    return {"ts": "2026-10-02T12-00-00Z", "game_id": f"g{hours_out}_{run:%d%H}", "kickoff_utc": ko.strftime("%Y-%m-%dT%H:%MZ"), "gfs_run": run.strftime("%Y-%m-%dT%HZ"),
            "wind_mean": 10.0, "gfs_pop": 60.0, "gfs_temp": 40.0}


def test_fresh_drops_readings_more_than_one_run_behind():
    now = pd.Timestamp("2026-10-02 20:30", tz="UTC")   # newest run out: 12Z (issued 4+ hours ago)
    rows = [_lv(now, 40, pd.Timestamp("2026-10-02 12:00")), _lv(now, 40, pd.Timestamp("2026-10-02 06:00")),
            _lv(now, 40, pd.Timestamp("2026-10-02 00:00")), _lv(now, -2, pd.Timestamp("2026-09-30 00:00"))]
    lv = pd.DataFrame(rows)
    kept = set(WL._fresh(lv, now).game_id)
    assert kept == {rows[0]["game_id"], rows[1]["game_id"], rows[3]["game_id"]}   # current, one run behind, and a game that has kicked off
    assert any(rows[2]["game_id"] in w["message"] and "not used" in w["message"] for w in warnlog.recent())


def test_readings_skip_a_stale_live_reading(tmp_path, monkeypatch):
    now = pd.Timestamp.now(tz="UTC")
    new, old = WL.newest_run(now + pd.Timedelta(hours=40), now), WL.newest_run(now + pd.Timedelta(hours=40), now) - pd.Timedelta(hours=12)
    a, b = _lv(now, 40, new), _lv(now, 41, old)
    f = tmp_path / "wind_live.csv"; pd.DataFrame([a, b]).reindex(columns=WL.COLS).assign(wind_mean=10.0).to_csv(f, index=False)
    monkeypatch.setattr(WL, "F", f)
    monkeypatch.setattr(FH, "OUTF", tmp_path / "none.csv")
    monkeypatch.setattr(WL, "_roofed", lambda: set())
    assert set(WL.readings()) == {a["game_id"]}
    assert set(WL.rain_readings()) == {a["game_id"]} and set(WL.temp_readings()) == {a["game_id"]}


def test_run_logs_a_new_gfs_run_even_when_the_values_hold(tmp_path, monkeypatch):
    now = pd.Timestamp.now(tz="UTC")
    ko_et = (now + pd.Timedelta(hours=40)).tz_convert("America/New_York").tz_localize(None).floor("min")
    g = pd.DataFrame({"game_id": ["2026_04_A_B"], "season": [2026], "week": [4], "kickoff_et": [ko_et], "station": ["KXXX"], "latlon": [(40.0, -75.0)]})
    pd.DataFrame({"season": [2026], "week": [4]}).to_parquet(tmp_path / "games.parquet")
    monkeypatch.setattr(FH, "OUT", tmp_path)
    monkeypatch.setattr("nflmodel.lines.current_week", lambda games: (2026, 4))
    monkeypatch.setattr(FH, "games", lambda *a, **k: g)
    monkeypatch.setattr(FH, "mos_all", lambda *a, **k: {"wind": 8.0, "gust": None, "temp": 55.0, "pop": 20.0, "pop12": None})
    monkeypatch.setattr(FH, "jma", lambda *a, **k: (None, 6.0, 6.0))
    monkeypatch.setattr(WL, "F", tmp_path / "wind_live.csv")
    runs = iter([pd.Timestamp("2026-10-02 06:00", tz="UTC"), pd.Timestamp("2026-10-02 06:00", tz="UTC"), pd.Timestamp("2026-10-02 12:00", tz="UTC")])
    monkeypatch.setattr(WL, "newest_run", lambda ko, now: next(runs))
    assert WL.run() == 1 and WL.run() == 0 and WL.run() == 1   # same run, same values: no row; a new run: a row
    assert list(pd.read_csv(WL.F).gfs_run) == ["2026-10-02T06Z", "2026-10-02T12Z"]


def test_a_due_game_with_japan_only_wind_fails():
    rows = H.weather_source_rows({"g": _src("mos", "mos", "mos")}, {"g"}, gfs_missing={"g"})
    assert rows[0][0] == "FAIL" and "g" in rows[0][2]
    assert H.weather_source_rows({"g": _src("mos", "mos", "mos")}, set(), gfs_missing={"g"})[0][0] == "OK"   # further out: expected


def test_fresh_drops_an_unplayed_game_with_no_gfs_run():
    now = pd.Timestamp("2026-10-02 20:30", tz="UTC")
    r = _lv(now, 40, pd.Timestamp("2026-10-02 12:00")); r["gfs_run"] = None
    assert WL._fresh(pd.DataFrame([r]), now).empty
    assert any("GFS run unknown" in w["message"] for w in warnlog.recent())


def test_a_full_gfs_outage_inside_the_window_raises_after_logging(tmp_path, monkeypatch):
    now = pd.Timestamp.now(tz="UTC")
    ko_et = (now + pd.Timedelta(hours=30)).tz_convert("America/New_York").tz_localize(None).floor("min")
    g = pd.DataFrame({"game_id": ["2026_04_A_B"], "season": [2026], "week": [4], "kickoff_et": [ko_et], "station": ["KXXX"], "latlon": [(40.0, -75.0)]})
    pd.DataFrame({"season": [2026], "week": [4]}).to_parquet(tmp_path / "games.parquet")
    monkeypatch.setattr(FH, "OUT", tmp_path)
    monkeypatch.setattr("nflmodel.lines.current_week", lambda games: (2026, 4))
    monkeypatch.setattr(FH, "games", lambda *a, **k: g)
    monkeypatch.setattr(FH, "mos_all", lambda *a, **k: dict.fromkeys(["wind", "gust", "temp", "pop", "pop12"]))   # what a network error returns
    monkeypatch.setattr(FH, "jma", lambda *a, **k: (None, 6.0, 6.0))
    monkeypatch.setattr(WL, "F", tmp_path / "wind_live.csv")
    with pytest.raises(RuntimeError, match="GFS MOS gave nothing"):
        WL.run()
    assert len(pd.read_csv(WL.F)) == 1 and WL.gfs_missing() == {"2026_04_A_B"}


# 3b. a failed live forecast pull is a health row
def _watch(errs, now):
    t = [now - pd.Timedelta(minutes=30 * (len(errs) - i)) for i in range(len(errs))]
    return pd.DataFrame({"t": t, "errors": errs})


@pytest.mark.parametrize("errs,level", [
    ([None, None, None], "OK"),
    ([None, "wind: HTTP 503", None], "WARN"),
    ([None, "wind: HTTP 503", "props: x; wind: HTTP 503"], "FAIL"),
    ([None, None, "windy: no"], "OK"),
])
def test_wind_pull_row(errs, level):
    now = pd.Timestamp("2026-10-02 20:00")
    lv, what, detail = H.wind_pull_row(_watch(errs, now), now)
    assert lv == level and "wind_live" in what
    if level != "OK":
        assert "HTTP 503" in detail
