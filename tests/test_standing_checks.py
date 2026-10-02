"""Standing checks (2 Oct 2026, nflmodel/standing_checks.py): each check passes a clean row and catches a planted bad one,
the bug class it guards as it happened on 1-2 Oct 2026."""
import json

import pandas as pd
import pytest

from nflmodel import standing_checks as SC, forecast_history as FH, picks as P


def lv(rows):
    return [r[0] for r in rows]


def games(**kw):
    base = {"game_id": ["2026_04_DAL_HOU", "2026_04_GB_TB", "2026_04_IND_WAS"], "season": 2026, "week": 4,
            "home_team": ["HOU", "TB", "WAS"], "away_team": ["DAL", "GB", "IND"], "location": "Home", "stadium_id": ["HOU00", "TAM00", "WAS00"],
            "roof": ["closed", "outdoors", "outdoors"], "home_score": None, "kickoff_et": pd.to_datetime(["2026-10-04 13:00"] * 3),
            "spread_line": [-1.5, 3.0, -4.5], "total_line": [45.5, 44.5, 47.5]}
    base.update(kw); return pd.DataFrame(base)


def test_qb_priced_not_out_catches_a_ruled_out_starter():
    f = pd.DataFrame({"game_id": ["2026_04_IND_WAS"] * 2, "team": ["WAS", "IND"], "qb_id": ["daniels", "jones"]})
    assert lv(SC.qb_priced_not_out(f, games(), {"WAS": {"mariota"}}, 2026, 4)) == ["OK"]
    assert lv(SC.qb_priced_not_out(f, games(), {"WAS": {"daniels"}}, 2026, 4)) == ["FAIL"]   # #376: Daniels Out, still priced


def test_qb_out_only_when_last_games_starter_is_out():
    qb = pd.DataFrame({"game_id": ["w3_WAS", "w3_TB", "w3_TB"], "season": 2026, "week": 3, "team": ["WAS", "TB", "TB"],
                       "qb_id": ["mariota", "mayfield", "backup"], "dropbacks": [40, 42, 4]})
    t = pd.DataFrame({"game_id": ["2026_04_IND_WAS", "2026_04_GB_TB"], "team": ["WAS", "TB"], "qb_out": [0, 1]})
    out = {"WAS": {"daniels"}, "TB": {"mayfield"}}
    assert lv(SC.qb_out_is_last_starter(t, qb, games(), out, 2026, 4)) == ["OK", "OK"]   # TB: Mayfield started last game and is out
    t.loc[0, "qb_out"] = 1   # #396: WAS read 1 for Daniels, already replaced by Mariota
    assert lv(SC.qb_out_is_last_starter(t, qb, games(), out, 2026, 4))[0] == "FAIL"
    t2 = t.assign(qb_out=[0, 0])   # Mayfield out, qb_out 0: a warning
    assert lv(SC.qb_out_is_last_starter(t2, qb, games(), out, 2026, 4)) == ["OK", "WARN"]


def test_retractable_roof_blank_and_card_priced_outdoors():
    cards = [{"game_id": "2026_04_DAL_HOU", "home_score": None, "wx": {"s": "dome"}}]
    assert lv(SC.retractable_roofs(games(), cards)) == ["OK", "OK"]
    assert lv(SC.retractable_roofs(games(roof=[None, "outdoors", "outdoors"]), cards))[0] == "FAIL"   # #391: the blank roof read as outdoors
    assert lv(SC.retractable_roofs(games(), [{"game_id": "2026_04_DAL_HOU", "home_score": None, "wx": {"s": "forecast"}}]))[1] == "FAIL"
    assert lv(SC.retractable_roofs(games(roof=["open", "outdoors", "outdoors"]), [{"game_id": "2026_04_DAL_HOU", "home_score": None, "wx": {"s": "forecast"}}])) == ["OK", "OK"]   # announced open


def test_no_weather_reading_or_weather_bet_under_a_roof():
    card = {"game_id": "2026_04_DAL_HOU", "home_score": None, "sides": {"HOU": {"wind": None}, "DAL": {"wind": None}}, "windunder_bet": ""}
    assert lv(SC.no_weather_under_roof(games(), {"2026_04_GB_TB": 12.0}, {}, {}, [card])) == ["OK", "OK"]
    assert lv(SC.no_weather_under_roof(games(), {"2026_04_DAL_HOU": 11.4}, {}, {}, [card]))[0] == "FAIL"   # #391: 11.4 mph at Houston
    assert lv(SC.no_weather_under_roof(games(), {}, {}, {}, [dict(card, windunder_bet="Under 45.5")]))[1] == "FAIL"


def test_forecast_runs_before_kickoff():
    hist = pd.DataFrame({"game_id": ["g1"], "kickoff_utc": ["2025-10-05T17:00Z"], "gfs_wind_d0": [8.0], "gfs_run_d0": ["2025-10-05T06Z"],
                         "nbs_wind_d0": [None], "nbs_run_d0": [None]})
    live = pd.DataFrame({"game_id": ["g2"], "ts": ["2026-10-03T12-00-00Z"], "kickoff_utc": ["2026-10-04T17:00Z"], "gfs_run": ["2026-10-03T06Z"]})
    assert lv(SC.forecasts_before_kickoff(hist, live)) == ["OK"] * 3
    assert lv(SC.forecasts_before_kickoff(hist.assign(gfs_run_d0="2025-10-05T18Z"), live))[1] == "FAIL"   # an 18Z run for a 17Z kickoff
    assert lv(SC.forecasts_before_kickoff(hist, live.assign(ts="2026-10-04T17-01-00Z")))[2] == "FAIL"   # fetched after kickoff


def test_post_kickoff_column_never_read(monkeypatch):
    monkeypatch.setattr(FH, "PRE_KICKOFF_WIND", FH.PRE_KICKOFF_WIND + ["jma_wind_d0"])   # #384: Japan's run at or after kickoff
    assert lv(SC.forecasts_before_kickoff(pd.DataFrame(), pd.DataFrame()))[0] == "FAIL"


def test_implausible_weather():
    assert lv(SC.plausible_weather({"g": 12.0}, {"g": 40.0}, {"g": 55.0})) == ["OK"]
    assert lv(SC.plausible_weather({"g": 99.0}, {}, {})) == ["FAIL"]   # #365: NWS MOS 99 = missing
    assert lv(SC.plausible_weather({}, {}, {"g": 999.0})) == ["FAIL"]
    assert lv(SC.plausible_weather({}, {}, {}, pd.DataFrame({"game_id": ["g"], "status": ["ok"], "wind": [71.0], "temp": [60.0]}))) == ["FAIL"]   # 71 mph at Pittsburgh


def test_bets_logged_before_kickoff():
    b = pd.DataFrame({"run_at": ["2026-10-02 19:24 UTC"], "game_id": ["2026_04_IND_WAS"]})
    assert lv(SC.bets_before_kickoff({"model": b}, games())) == ["OK"]
    late = b.assign(run_at="2026-10-04 17:02 UTC")   # 13:00 ET = 17:00 UTC: a bet logged after kickoff (#381)
    assert lv(SC.bets_before_kickoff({"model": late}, games())) == ["FAIL"]


def test_no_chance_at_a_moved_line_without_the_fit():
    c = {"game_id": "2026_04_GB_TB", "priced_live": False, "spread_line": 3.0, "total_line": 44.5, "p_over_emp": 0.44, "p_home": 0.4}
    assert lv(SC.chances_at_card_line([c], games())) == ["OK"]
    assert lv(SC.chances_at_card_line([dict(c, total_line=47.5)], games())) == ["FAIL"]   # #395: chance stayed at the schedule's 44.5
    assert lv(SC.chances_at_card_line([dict(c, total_line=47.5, p_over_emp=None, p_over=None)], games())) == ["OK"]
    assert lv(SC.chances_at_card_line([dict(c, total_line=47.5, priced_live=True)], games())) == ["OK"]   # with the fit: the tie check's row


def test_hidden_shadows_stay_off_the_page_and_out_of_bets():
    rules = [{"rule": n, "hidden": True} for n in P.HIDDEN_SHADOWS]
    html = "const sh = PK.rules.filter(r => !r.hidden);"
    files = {"model": "a", "shadowunder": "b", "windunder": "c"}
    assert lv(SC.shadows_stay_off(html, rules, files)) == ["OK"] * 3
    assert lv(SC.shadows_stay_off(html + " shadowrain", rules, files))[0] == "FAIL"
    assert lv(SC.shadows_stay_off("PK.rules.map(r => r.label)", rules, files))[0] == "FAIL"
    assert lv(SC.shadows_stay_off(html, rules[1:], files))[1] == "FAIL"
    assert lv(SC.shadows_stay_off(html, rules, dict(files, shadowrain="d")))[2] == "FAIL"


def test_one_unit_no_kelly_stake():
    ok = 'set("d_stake", `One unit on every bet`);   // the quarter-Kelly stake retired from the page'
    assert lv(SC.one_unit(ok, "| Stake | 1 unit at -110 |")) == ["OK"]
    assert lv(SC.one_unit(ok + '\n${r.stake_pct != null ? " · stake " + r.stake_pct + "%" : ""}')) == ["FAIL"]   # #385's chip
    assert lv(SC.one_unit('<th title="bankroll growth at a quarter Kelly">')) == ["FAIL"]
    assert lv(SC.one_unit(ok, "| Stake | 1.8% at -105 |")) == ["FAIL"]


def test_page_shows_no_stake_now():
    html = (SC.ROOT / "web" / "index.html").read_text(encoding="utf-8")
    assert lv(SC.one_unit(html)) == ["OK"]


def test_logs_appended_by_column(tmp_path):
    good = tmp_path / "rule_history.csv"; good.write_text("run_at,game_id,shadowunder_bet\n1,g,\n2,h,Under 40\n")
    bad = tmp_path / "pred_history.csv"; bad.write_text("run_at,game_id\n1,g\n2,h,Under 40\n")   # a new column appended by position
    assert lv(SC.logs_by_column([good])) == ["OK"]
    assert lv(SC.logs_by_column([good, bad])) == ["FAIL"]


def test_leaks_fail_on_any_change(monkeypatch):
    from nflmodel import audit as A
    clean = {"rating_rows_compared": 1, "max_rating_change_after_corrupting_future": 0.0, "max_prediction_change_after_corrupting_targets": 0.0,
             "max_prediction_change_after_corrupting_own_game": 0.0}
    monkeypatch.setattr(A, "leakage_test", lambda: clean)
    monkeypatch.setattr(A, "own_game_shift", lambda s, w: 0.0)
    assert lv(SC.leaks(2026, 3)) == ["OK"] * 4
    monkeypatch.setattr(A, "own_game_shift", lambda s, w: 0.42)   # #384: the referee prior counted the game's own total
    assert lv(SC.leaks(2026, 3))[-1] == "FAIL"
    monkeypatch.setattr(A, "leakage_test", lambda: dict(clean, max_rating_change_after_corrupting_future=0.1))
    assert lv(SC.leaks(2026, 3))[0] == "FAIL"


def test_a_check_that_cannot_run_fails_the_tie_check(monkeypatch):
    monkeypatch.setattr(SC, "cheap", lambda: [("OK", "a", "0"), ("WARN", "b", "1: x"), ("FAIL", "c", "1: y")])
    monkeypatch.setattr("nflmodel.warnlog.warn", lambda *a, **k: None)
    rows = []; SC.tie_rows(rows)
    assert [r[3] for r in rows] == [True, True, False]
