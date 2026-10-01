"""Planted-leak test (1 Oct 2026): proves the look-ahead check in nflmodel.audit can catch a leak.

The check corrupts 2024 Week 10 on and requires the Week 1 to 9 predictions not to move. A check that never fails proves
nothing, so this test plants a real leak (each team's points rating replaced by its NEXT game's points, data from the
future) and requires the same check to see it. The clean model must still move by exactly zero.
"""
from pathlib import Path

import pandas as pd
import pytest

from nflmodel import model as M

F = Path(__file__).resolve().parent.parent / "data" / "processed" / "features_asof.parquet"


def _corrupt_future(f):
    f = f.copy()
    m = (f.season > 2024) | ((f.season == 2024) & (f.week >= 10))
    f.loc[m, "pf"] = f.loc[m, "pf"] + 20
    return f


def _plant_next_game_points(f):
    f = f.sort_values(["team", "season", "week"]).copy()
    nxt = f.groupby(["team", "season"]).pf.shift(-1)
    f["off_pf"] = nxt.fillna(f.off_pf)
    return f.sort_index()


def _week1_9_shift(f):
    p1 = M.walk_forward(f, [2024]); p1 = p1[p1.week <= 9].reset_index(drop=True)
    p2 = M.walk_forward(_corrupt_future(f), [2024]); p2 = p2[p2.week <= 9].reset_index(drop=True)
    return float((p1.home_exp - p2.home_exp).abs().max() + (p1.away_exp - p2.away_exp).abs().max())


@pytest.mark.skipif(not F.exists(), reason="features_asof.parquet not present")
def test_clean_model_has_no_lookahead_and_a_planted_leak_is_caught():
    f = M.with_trends(pd.read_parquet(F))
    assert _week1_9_shift(f) == 0.0
    # the plant reads the corrupted future, so it must be applied after corrupting: rebuild it inside the check
    def shift_planted(f):
        p1 = M.walk_forward(_plant_next_game_points(f), [2024]); p1 = p1[p1.week <= 9].reset_index(drop=True)
        p2 = M.walk_forward(_plant_next_game_points(_corrupt_future(f)), [2024]); p2 = p2[p2.week <= 9].reset_index(drop=True)
        return float((p1.home_exp - p2.home_exp).abs().max() + (p1.away_exp - p2.away_exp).abs().max())
    assert shift_planted(f) > 0.5
