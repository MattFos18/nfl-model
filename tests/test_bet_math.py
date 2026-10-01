"""Bet math (1 Oct 2026): payouts, break-even, Kelly, grading and the live cutoffs, checked on exact edge cases and on
thousands of random inputs. If any of these are wrong, every record downstream is wrong."""
import numpy as np
import pandas as pd
import pytest

from nflmodel import backtest as B, picks as P, tracker as T

RNG = np.random.default_rng(7)
ODDS = np.concatenate([-RNG.uniform(100, 1000, 500), RNG.uniform(100, 1000, 500)])


# ---- payout, break-even, parlay, Kelly ----
def test_payout_fixed_cases():
    assert T.payout(-110, True, False) == pytest.approx(100 / 110)
    assert T.payout(+150, True, False) == pytest.approx(1.5)
    assert T.payout(-110, False, False) == -1.0
    assert T.payout(-110, True, True) == 0.0 and T.payout(+300, False, True) == 0.0   # a push pays nothing either way


def test_payout_never_beats_the_price_and_break_even_is_zero_ev():
    for o in ODDS:
        win = T.payout(o, True, False)
        assert 0 < win <= max(o / 100, 100 / -o if o < 0 else 0) + 1e-12
        be = P.break_even(o)
        assert be * win + (1 - be) * T.payout(o, False, False) == pytest.approx(0.0, abs=1e-12)


def test_break_even_at_minus_110():
    assert P.break_even(-110) == pytest.approx(110 / 210)


def test_parlay_odds():
    assert P.parlay_odds([-110, -110]) == pytest.approx(264.5, abs=0.1)
    for o in RNG.choice(ODDS, 50):
        assert P.parlay_odds([o]) == pytest.approx(round(o, 1), abs=0.11)   # one leg is the leg itself


def test_kelly_zero_at_or_below_break_even_and_positive_above():
    for o in RNG.choice(ODDS, 200):
        be = P.break_even(o)
        assert P.kelly_stake(be - 0.01, o) == 0.0
        assert P.kelly_stake(min(be + 0.05, 0.99), o) > 0.0
    assert P.kelly_stake(0.55, -110, 1.0) == pytest.approx(5.5, abs=0.01)   # (0.55 x 0.909 - 0.45) / 0.909 = 5.5%


# ---- grading (nflverse: spread_line = points the home side gives; result = home minus away) ----
def _games(rows):
    return pd.DataFrame(rows, columns=["spread_edge", "result", "spread_line", "total_edge", "total", "total_line"])


def test_grade_spread_sides_cutoff_and_push():
    d = _games([[4.0, 10, 3, 0, 0, 0],      # home side at exactly the cutoff, home won by 10 giving 3: win
                [-4.0, 10, 3, 0, 0, 0],     # away side, home covered: loss
                [4.0, 3, 3, 0, 0, 0],       # landed on the number: push
                [3.999, 10, 3, 0, 0, 0],    # under the cutoff: no bet
                [-6.0, -2, -1.5, 0, 0, 0]])  # away side, away won by 2 getting 1.5 the other way: win
    b = B.grade_spread(d, 4.0)
    assert list(b.index) == [0, 1, 2, 4]
    assert list(b.side) == ["home", "away", "home", "away"]
    assert list(b.win) == [True, False, False, True] and list(b.push) == [False, False, True, False]
    assert list(b.units) == [1.0, -B.VIG, 0.0, 1.0]


def test_grade_total_sides_and_push():
    d = _games([[0, 0, 0, -4.0, 40, 44.5], [0, 0, 0, -4.0, 47, 44.5], [0, 0, 0, 4.0, 44, 44.0], [0, 0, 0, 4.5, 50, 44.5]])
    b = B.grade_total(d, 4.0)
    assert list(b.side) == ["under", "under", "over", "over"]
    assert list(b.win) == [True, False, False, True] and list(b.push) == [False, False, True, False]


def test_random_spreads_grade_consistently():
    n = 5000
    d = _games(np.column_stack([RNG.uniform(-12, 12, n), RNG.integers(-30, 31, n), RNG.choice(np.arange(-14, 14.5, 0.5), n),
                                np.zeros(n), np.zeros(n), np.zeros(n)]))
    b = B.grade_spread(d, 4.0)
    assert (b.spread_edge.abs() >= 4.0).all() and len(b) == int((d.spread_edge.abs() >= 4.0).sum())
    cover = b.result - b.spread_line
    assert ((cover == 0) == b.push).all()
    assert (b.win & b.push).sum() == 0
    flipped = B.grade_spread(d.assign(spread_edge=-d.spread_edge), 4.0)   # the other side wins exactly when this one loses
    assert ((b.win | b.push) | flipped.win).all() and (b.win & flipped.win).sum() == 0


# ---- the live rules' cutoffs (picks.rule_mask, picks.record) ----
def _rule_rows(rows):
    return pd.DataFrame(rows, columns=["model_spread", "spread_line", "week", "p_over_emp", "total_line", "home_score", "away_score"])


def test_spread_flag_cutoff_and_weeks():
    d = _rule_rows([[7.0, 3.0, 1, .5, 44, 0, 0],     # edge exactly 4: flagged
                    [6.99, 3.0, 1, .5, 44, 0, 0],    # 3.99: not
                    [-1.0, 3.0, 17, .5, 44, 0, 0],   # -4 (the away side) in week 17: flagged
                    [7.0, 3.0, 18, .5, 44, 0, 0],    # week 18: never
                    [7.0, np.nan, 1, .5, 44, 0, 0]])  # no line: never
    assert list(P.rule_mask(d, P.SPREAD_EDGE)) == [True, False, True, False, False]


def test_under_flag_cutoff():
    d = _rule_rows([[0, 0, 1, .45, 44, 0, 0],      # a 55% under chance: flagged
                    [0, 0, 1, .4501, 44, 0, 0],    # 54.99%: not
                    [0, 0, 1, .30, np.nan, 0, 0],  # no total line: never
                    [0, 0, 18, .30, 44, 0, 0]])    # week 18: never
    assert list(P.rule_mask(d, P.TOTAL_SHADOW["prob"], "under_prob")) == [True, False, False, False]


def test_record_counts_pushes_as_neither():
    d = _rule_rows([[7.0, 3.0, 1, .4, 44, 24, 20],   # home by 4 giving 3: win
                    [7.0, 3.0, 1, .4, 44, 23, 20],   # home by 3: push, dropped
                    [7.0, 3.0, 1, .4, 44, 20, 20]])  # loss
    assert P.record(d, pd.Series([True] * 3)) == (1, 1)
    u = d.assign(total_line=[44.0, 43.0, 41.0])     # totals 44, 43, 40: push, push, under
    assert P.record(u, pd.Series([True] * 3), "under_prob") == (1, 0)
