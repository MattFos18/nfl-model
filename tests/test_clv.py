"""Closing line value (nflmodel/clv.py): the sign from each side, the close taken strictly before kickoff, no-vig prices."""
import numpy as np
import pandas as pd
import pytest
from nflmodel import clv as C

KICK = pd.Timestamp("2026-10-04 13:00")   # Eastern; 17:00 UTC
NOW = pd.Timestamp("2026-10-05 12:00", tz="UTC")   # after the game
HOME, AWAY = "BUF", "LAC"


def snap(ts, home_spread=None, total=None, sh=-110, sa=-110, ov=-110, un=-110, source="espn:DraftKings"):
    return {"ts": ts, "source": source, "game_id": "2026_05_A_B", "home": HOME, "away": AWAY, "home_spread": home_spread, "total": total,
            "spread_odds_home": sh, "spread_odds_away": sa, "over_odds": ov, "under_odds": un}


def log(*rows):
    d = pd.DataFrame(list(rows))
    for c in ["home_spread", "total", "spread_odds_home", "spread_odds_away", "over_odds", "under_odds"]:
        d[c] = pd.to_numeric(d[c])
    return d


def g(bet, hist, run_at="2026-10-04 12:00 UTC", now=NOW):
    return C.grade_bet(bet, run_at, HOME, AWAY, KICK, hist, now)


# the home team BUF closes favoured by 3 (home_spread +3, the schedule's sign): BUF -3, LAC +3
CLOSE3 = log(snap("2026-10-04T12-05-00Z", 2.5, 44.5), snap("2026-10-04T16-30-00Z", 3.0, 44.5))


def test_spread_home_side_sign():
    r = g("BUF -2.5", CLOSE3)    # took BUF -2.5, it closed BUF -3: half a point better
    assert r["status"] == "closed" and r["close"] == -3.0 and r["clv_pts"] == pytest.approx(0.5) and r["beat"]
    r = g("BUF -3.5", CLOSE3)    # laid more than the close: worse
    assert r["clv_pts"] == pytest.approx(-0.5) and not r["beat"]


def test_spread_away_side_sign():
    r = g("LAC +3.5", CLOSE3)    # took LAC +3.5, it closed LAC +3: better
    assert r["close"] == 3.0 and r["clv_pts"] == pytest.approx(0.5) and r["beat"]
    r = g("LAC +2.5", CLOSE3)
    assert r["clv_pts"] == pytest.approx(-0.5) and not r["beat"]


def test_spread_side_sign_is_not_symmetric_by_accident():
    # planted-bug guard: if the side's handicap were not flipped for the home team, BUF -2.5 against a BUF -3 close would grade
    # -5.5 (or +5.5), not +0.5; and both sides of the same game can never beat the same close by taking the same number
    assert g("BUF -2.5", CLOSE3)["clv_pts"] == pytest.approx(0.5)
    assert g("LAC +2.5", CLOSE3)["clv_pts"] == pytest.approx(-0.5)
    assert C.side_handicap(3.0, HOME, HOME) == -3.0 and C.side_handicap(3.0, AWAY, HOME) == 3.0


def test_totals_over_under_sign():
    h = log(snap("2026-10-04T16-30-00Z", 3.0, 44.5))
    assert g("Under 45.5", h)["clv_pts"] == pytest.approx(1.0)    # under at a higher number than the close: better
    assert g("Under 43.5", h)["clv_pts"] == pytest.approx(-1.0)
    assert g("Over 43.5", h)["clv_pts"] == pytest.approx(1.0)     # over at a lower number: better
    assert g("Over 45.5", h)["clv_pts"] == pytest.approx(-1.0)


def test_push_on_the_number():
    h = log(snap("2026-10-04T16-30-00Z", 3.0, 44.5))
    for bet in ("Under 44.5", "Over 44.5", "BUF -3", "LAC +3"):
        r = g(bet, h)
        assert r["status"] == "closed" and r["clv_pts"] == 0 and r["beat"] is False
    gr = pd.DataFrame([{"rule": "shadowunder", "status": "closed", "clv_pts": 0.0, "clv_prob": np.nan},
                       {"rule": "shadowunder", "status": "closed", "clv_pts": 1.0, "clv_prob": np.nan}])
    a = C.aggregate(gr).set_index("rule")
    assert a.loc["shadowunder", "bets"] == 2 and a.loc["shadowunder", "beat_share"] == 0.5 and a.loc["shadowunder", "same"] == 1


def test_no_snapshot_after_kickoff():
    # a live in-game line at 17:05 UTC (five minutes after a 13:00 ET kickoff), and one exactly at kickoff: both ignored
    h = log(snap("2026-10-04T16-30-00Z", 3.0, 44.5), snap("2026-10-04T17-00-00Z", 7.0, 38.5), snap("2026-10-04T17-05-00Z", 10.0, 30.5))
    r = g("Under 44.5", h)
    assert r["close"] == 44.5 and r["close_ts"] == "2026-10-04 16:30 UTC" and r["clv_pts"] == 0
    assert g("LAC +3", h)["close"] == 3.0
    # only post-kickoff snapshots: no close at all, never a live line
    assert g("Under 44.5", log(snap("2026-10-04T17-05-00Z", 10.0, 30.5)))["status"] == "no line logged"


def test_pending_before_kickoff():
    r = g("Under 44.5", CLOSE3, now=pd.Timestamp("2026-10-04 16:59", tz="UTC"))
    assert r["status"] == "pending" and np.isnan(r["clv_pts"])
    a = C.aggregate(pd.DataFrame([{"rule": "windunder", "status": "pending", "clv_pts": np.nan, "clv_prob": np.nan}])).set_index("rule")
    assert a.loc["windunder", "bets"] == 0 and a.loc["windunder", "pending"] == 1 and np.isnan(a.loc["windunder", "avg_clv_pts"])


def test_close_is_consensus_of_last_snapshot():
    # three sources at the last pre-kickoff snapshot: the median to the half point (lines.consensus), not the first source
    h = log(snap("2026-10-04T16-30-00Z", 3.0, 44.0, source="a"), snap("2026-10-04T16-30-00Z", 3.5, 45.0, source="b"), snap("2026-10-04T16-30-00Z", 3.5, 44.5, source="c"))
    r = g("Under 45.5", h)
    assert r["close"] == 44.5 and r["clv_pts"] == pytest.approx(1.0)
    assert g("LAC +3", h)["close"] == 3.5


def test_novig_probability_clv():
    # under 44.5 at -110/-110 when recorded (12:05 snapshot, the run's pull), -125 under / +105 over at the close: our side got dearer
    h = log(snap("2026-10-04T12-05-00Z", 3.0, 44.5), snap("2026-10-04T16-30-00Z", 3.0, 44.5, ov=105, un=-125))
    r = g("Under 44.5", h)
    pu, po = 125 / 225, 100 / 205
    assert r["p_taken"] == pytest.approx(0.5) and r["p_close"] == pytest.approx(pu / (pu + po)) and r["clv_prob"] > 0
    assert g("Over 44.5", h)["clv_prob"] == pytest.approx(-r["clv_prob"])
    # the number itself moved: probability left blank, the points carry it
    h2 = log(snap("2026-10-04T12-05-00Z", 3.0, 45.5), snap("2026-10-04T16-30-00Z", 3.0, 44.5))
    assert np.isnan(g("Under 45.5", h2)["clv_prob"]) and g("Under 45.5", h2)["clv_pts"] == pytest.approx(1.0)


def _grade_one(rule, bet, run_at, hist_rows, lines):
    games = pd.DataFrame([{"game_id": "2026_05_A_B", "home_team": HOME, "away_team": AWAY, "kickoff_et": KICK}])
    bets = pd.DataFrame([{"rule": rule, "run_at": run_at, "season": 2026, "week": 5, "game_id": "2026_05_A_B", "bet": bet, "odds": -110}])
    history = {r: pd.DataFrame(hist_rows if r == rule else [], columns=["run_at", "game_id", "bet", "line"]) for r in C.HIST}
    return C.grade(bets, games, lines, NOW, {}, history).iloc[0]


def test_first_flag_line_is_the_line_taken():
    # LAC flagged at +4.5 on Sunday (consensus home_spread 4.5), then +3.5; the tracker row is the last run's LAC +3.5 at the best
    # book. The close is LAC +3: CLV is from the first flag's consensus +4.5 (+1.5), not the tracker's +3.5 (+0.5)
    hist = [{"run_at": "2026-09-27 20:12 UTC", "game_id": "2026_05_A_B", "bet": "LAC +4.5", "line": 4.5},
            {"run_at": "2026-10-03 20:00 UTC", "game_id": "2026_05_A_B", "bet": "LAC +3.5", "line": 3.5}]
    r = _grade_one("model", "LAC +3.5", "2026-10-04 15:00 UTC", hist, log(snap("2026-10-04T16-30-00Z", 3.0, 44.5)))
    assert r.taken_from == "first flag" and r.taken_at == "2026-09-27 20:12 UTC"
    assert r.line == 4.5 and r.line_best == 3.5 and r.clv_pts == pytest.approx(1.5)


def test_first_flag_survives_unflag_and_reflag_and_uses_consensus_not_best_book():
    # flagged BUF at consensus -2.5 (bet at the best book's -2), unflagged, flagged again at -3: the first flag counts, at -2.5
    hist = [{"run_at": "2026-09-28 12:00 UTC", "game_id": "2026_05_A_B", "bet": "BUF -2", "line": 2.5},
            {"run_at": "2026-09-29 12:00 UTC", "game_id": "2026_05_A_B", "bet": np.nan, "line": 3.0},
            {"run_at": "2026-09-30 12:00 UTC", "game_id": "2026_05_A_B", "bet": "BUF -3", "line": 3.0}]
    r = _grade_one("model", "BUF -3", "2026-09-30 12:00 UTC", hist, log(snap("2026-10-04T16-30-00Z", 3.5, 44.5)))
    assert r.taken_at == "2026-09-28 12:00 UTC" and r.line == -2.5 and r.clv_pts == pytest.approx(1.0)


def test_flag_after_kickoff_is_not_a_first_flag():
    hist = [{"run_at": "2026-10-04 17:30 UTC", "game_id": "2026_05_A_B", "bet": "BUF -1", "line": 1.0}]   # 13:30 ET, after kickoff
    r = _grade_one("model", "BUF -3", "2026-10-04 15:00 UTC", hist, log(snap("2026-10-04T16-30-00Z", 3.0, 44.5)))
    assert r.taken_from == "tracker row" and r.line == -3.0 and r.clv_pts == 0


def test_unders_first_flag_and_fallback_marked():
    hist = [{"run_at": "2026-09-30 12:00 UTC", "game_id": "2026_05_A_B", "bet": "Under 46.5", "line": 46.5}]
    lines = log(snap("2026-10-04T16-30-00Z", 3.0, 44.5))
    r = _grade_one("shadowunder", "Under 44.5", "2026-10-04 15:00 UTC", hist, lines)
    assert r.taken_from == "first flag" and r.line == 46.5 and r.clv_pts == pytest.approx(2.0)
    r = _grade_one("windunder", "Under 44.5", "2026-10-04 15:00 UTC", [], lines)   # no run history: the tracker row, marked
    assert r.taken_from == "tracker row" and r.taken_at == "2026-10-04 15:00 UTC" and r.clv_pts == 0
