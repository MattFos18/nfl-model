"""The hidden shadows added 2 Oct 2026 (picks.SHADOWS, reports/more_shadows.md): each rule's mask on planted rows, its
cutoff inclusive or exclusive as defined, its grading, its live bet text, and that the page never lists a hidden rule."""
import re
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from nflmodel import picks as P

ROOT = Path(__file__).resolve().parent.parent
COLS = ["game_id", "home_team", "away_team", "week", "model_spread", "spread_line", "model_total", "total_line", "p_over_emp",
        "home_m_trees", "away_m_trees", "home_score", "away_score"]


def _rows(rows):
    return pd.DataFrame(rows, columns=COLS)


def _g(gid, week=1, ms=0.0, sl=3.0, mt=44.0, tl=44.0, po=0.5, ht=22.0, at=22.0, hs=0.0, as_=0.0):
    return [gid, "HOM", "AWY", week, ms, sl, mt, tl, po, ht, at, hs, as_]


@pytest.fixture
def readings(monkeypatch):
    monkeypatch.setattr(P, "_RAIN", {"g1": 50.0, "g2": 49.9, "g3": 80.0, "g4": 90.0})
    monkeypatch.setattr(P, "_COLD", {"g1": 31.9, "g2": 32.0, "g3": 10.0, "g4": 20.0})
    monkeypatch.setattr(P, "_WIND", {"g1": 10.0, "g2": 9.9, "g3": 15.0})
    monkeypatch.setattr(P, "_WEST", {"g1", "g3", "g4"})


def test_every_new_shadow_is_hidden_and_has_a_branch():
    new = {"shadowrain", "shadowcold", "shadowunder3", "shadowunderwind", "shadowtreestotal", "shadowwestcoast", "shadowroaddog",
           "shadowsmalldog", "shadowdog35", "shadowwk4", "shadowwk15", "shadow6"}
    assert new <= set(P.SHADOWS) and new <= P.HIDDEN_SHADOWS
    assert all(P.SHADOWS[n][1] in P.MASK_RULES for n in new)


def test_rain_under_50_inclusive(readings):
    d = _rows([_g("g1"), _g("g2"), _g("g3", week=18), _g("g4", tl=np.nan), _g("g5")])   # 50: in; 49.9: out; week 18; no total; no reading
    assert list(P.rule_mask(d, P.RAIN_UNDER["pop"], "rain_under")) == [True, False, False, False, False]


def test_cold_under_below_32_exclusive(readings):
    d = _rows([_g("g1"), _g("g2"), _g("g3", week=17), _g("g5")])   # 31.9: in; 32.0: out; week 17: in; no reading: out
    assert list(P.rule_mask(d, P.COLD_UNDER["temp"], "cold_under")) == [True, False, True, False]


def test_under_edge_3_inclusive():
    d = _rows([_g("a", mt=41.0, tl=44.0), _g("b", mt=41.01, tl=44.0), _g("c", mt=50.0, tl=44.0), _g("d", mt=30.0, tl=44.0, week=18)])
    assert list(P.rule_mask(d, P.UNDER_EDGE, "under_edge")) == [True, False, False, False]


def test_under_wind_needs_both(readings):
    d = _rows([_g("g1", po=0.45), _g("g2", po=0.30), _g("g3", po=0.4501), _g("g5", po=0.30)])   # 55% and wind 10: in; wind 9.9; 54.99%; no wind
    assert list(P.rule_mask(d, P.TOTAL_SHADOW["prob"], "under_wind")) == [True, False, False, False]


def test_trees_total_share_of_line_both_sides():
    # line 40: the cut is 3.8 points; trees total 43.85 (over, in), 36.15 (under, in), 43.75 (out), 40 (zero edge, out)
    d = _rows([_g("a", tl=40.0, ht=22.0, at=21.85), _g("b", tl=40.0, ht=18.0, at=18.15), _g("c", tl=40.0, ht=22.0, at=21.75), _g("d", tl=40.0, ht=20.0, at=20.0)])
    m = P.rule_mask(d, P.TREES_TOTAL, "trees_total")
    assert list(m) == [True, True, False, False]
    assert P._mask_bets(d, P.TREES_TOTAL, "trees_total")[:2] == ["Over 40", "Under 40"]
    g = d.assign(home_score=[30.0, 30.0, 0, 0], away_score=[20.0, 20.0, 0, 0])   # total 50: the over wins, the under loses
    assert P.record(g, m, "trees_total") == (1, 1)


def test_westcoast_road_team(readings):
    d = _rows([_g("g1", sl=3.0), _g("g2"), _g("g3", week=18), _g("g4", sl=np.nan)])
    m = P.rule_mask(d, 0.0, "westcoast")
    assert list(m) == [True, False, False, False]
    assert P._mask_bets(d, 0.0, "westcoast")[0] == "AWY +3"
    g = _rows([_g("g1", sl=3.0, hs=20, as_=18), _g("g1", sl=3.0, hs=24, as_=20), _g("g1", sl=3.0, hs=23, as_=20)])   # home by 2 (road covers), by 4 (loses), by 3 (push)
    assert P.record(g, pd.Series([True] * 3), "westcoast") == (1, 1)


def test_road_dog_small_dog_dog35():
    # spread_line is the home side's points given: 3 means the home side lays 3, the away side gets 3
    d = _rows([_g("a", ms=-1.0, sl=3.0),     # edge -4, the away side getting 3: a road dog, a small dog
               _g("b", ms=-0.5, sl=3.5),     # edge -4, the away side getting 3.5: a road dog, not small
               _g("c", ms=-7.0, sl=-3.0),    # edge -4, the away side laying 3: a favourite
               _g("d", ms=7.0, sl=3.0),      # edge +4, the home side laying 3: a favourite
               _g("e", ms=0.5, sl=-3.0),     # edge +3.5, the home side getting 3: a home dog at 3.5
               _g("f", ms=6.99, sl=3.5)])    # edge +3.49 on a favourite
    assert list(P.rule_mask(d, P.SPREAD_EDGE, "roaddog")) == [True, True, False, False, False, False]
    assert list(P.rule_mask(d, P.SPREAD_EDGE, "smalldog")) == [True, False, False, False, False, False]
    assert list(P.rule_mask(d, P.DOG_EDGE, "dog35")) == [True, True, True, True, True, False]
    assert P._mask_bets(d, P.DOG_EDGE, "dog35")[:5] == ["AWY +3", "AWY +3.5", "AWY -3", "HOM -3", "HOM +3"]


def test_week_cuts_and_big_edge():
    d = _rows([_g("a", ms=7.0, week=4), _g("b", ms=7.0, week=5), _g("c", ms=7.0, week=15), _g("d", ms=7.0, week=16)])
    assert list(P.rule_mask(d, P.SPREAD_EDGE, "wk4")) == [True, False, False, False]
    assert list(P.rule_mask(d, P.SPREAD_EDGE, "wk15")) == [True, True, True, False]
    e = _rows([_g("a", ms=9.0), _g("b", ms=8.99), _g("c", ms=-3.0, week=18)])   # edge 6: in; 5.99: out; week 18: out
    assert list(P.rule_mask(e, P.BIG_EDGE, "big")) == [True, False, False]


def test_new_unders_graded_as_unders(readings):
    d = _rows([_g("g1", tl=44.0, hs=20, as_=20), _g("g1", tl=44.0, hs=24, as_=20), _g("g1", tl=44.0, hs=30, as_=20)])   # under, push, over
    for sr in ("rain_under", "cold_under", "under_edge", "under_wind"):
        assert sr in P.UNDER_RULES and P.record(d, pd.Series([True] * 3), sr) == (1, 1)


def test_shadow_watch_bases():
    """Rules that ignore the model are measured against break-even, totals rules against the totals flag, the rest against the spread flag."""
    assert {P.SHADOWS[n][1] for n in ("shadowrain", "shadowcold", "shadowwestcoast", "windunder", "shadowteasedog")} <= set(P.BLIND_RULES)
    assert {P.SHADOWS[n][1] for n in ("shadowunder3", "shadowunderwind", "shadowtreestotal", "shadowunder60")} <= set(P.TOTAL_RULES)
    assert not {P.SHADOWS[n][1] for n in ("shadowroaddog", "shadowdog35", "shadow6")} & set(P.TOTAL_RULES + P.BLIND_RULES)


def test_page_never_lists_a_hidden_shadow(readings):
    """page_rules marks every hidden shadow hidden, the page drops hidden rules wherever it reads them, and no hidden rule is named on it."""
    d = _rows([_g("a", ms=7.0, hs=24, as_=20)]).assign(season=2024, game_type="REG")
    rules = {r["rule"]: r for r in P.page_rules(d)["rules"]}
    assert all(rules[n]["hidden"] for n in P.HIDDEN_SHADOWS) and not rules["model"]["hidden"]
    html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
    lists = [ln for ln in html.splitlines() if "PK.rules" in ln and ".find(" not in ln]   # a .find picks the flag or the totals flag by name
    assert lists and all("!r.hidden" in ln for ln in lists)
    assert not [n for n in P.HIDDEN_SHADOWS if re.search(rf"\b{n}\b", html)]
