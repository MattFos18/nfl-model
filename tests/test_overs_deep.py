"""The low-total over shadow (2 Oct 2026, reports/overs_deep.md rule O9): its mask on planted rows (total 41 or lower and a
55%+ raw chance, both inclusive; weeks 1-17; a line needed), graded as an over, its live bet text, hidden, measured against
the totals flag."""
import numpy as np
import pandas as pd

from nflmodel import picks as P

COLS = ["game_id", "home_team", "away_team", "week", "model_spread", "spread_line", "model_total", "total_line", "p_over_emp",
        "home_m_trees", "away_m_trees", "home_score", "away_score"]


def _g(gid, week=1, tl=41.0, po=0.55, hs=0.0, as_=0.0):
    return [gid, "HOM", "AWY", week, 0.0, 3.0, 44.0, tl, po, 22.0, 22.0, hs, as_]


def test_over_low_mask_cutoffs():
    d = pd.DataFrame([_g("a"), _g("b", tl=41.5), _g("c", po=0.5499), _g("d", tl=37.0, po=0.70), _g("e", week=18), _g("f", tl=np.nan),
                      _g("g", week=17, tl=40.5, po=0.56)], columns=COLS)
    assert list(P.rule_mask(d, P.OVER_LOW["prob"], "over_low")) == [True, False, False, True, False, False, True]


def test_over_low_needs_a_chance():
    d = pd.DataFrame([_g("a")], columns=COLS).drop(columns="p_over_emp")
    assert not P.rule_mask(d, P.OVER_LOW["prob"], "over_low").any()


def test_over_low_graded_as_over_with_its_bet_text():
    d = pd.DataFrame([_g("a", hs=24, as_=20), _g("b", hs=21, as_=20), _g("c", hs=20, as_=20)], columns=COLS)   # 44 over 41, 41 push, 40 under
    assert "over_low" in P.OVER_RULES and P.record(d, pd.Series([True] * 3), "over_low") == (1, 1)
    assert P._mask_bets(d, P.OVER_LOW["prob"], "over_low") == ["Over 41", "Over 41", "Over 41"]


def test_over_low_is_a_hidden_totals_shadow():
    assert P.SHADOWS["shadowoverlow"][1] == "over_low" and "shadowoverlow" in P.HIDDEN_SHADOWS
    assert "over_low" in P.MASK_RULES and "over_low" in P.TOTAL_RULES and "over_low" not in P.BLIND_RULES + P.UNDER_RULES
