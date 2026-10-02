"""Same-game and post-kickoff leak tests (2 Oct 2026, reports/leak_fix_rescore.md).

Two leaks passed the old checks, which corrupted only future weeks' points and compared only team points:
  (a) the referee prior (ref_tot) counted the away row of the same game, this game's own total, among the home row's
      previous games; the totals equation reads ref_tot from the home row.
  (b) Japan's model wind (jma_wind_d0) came from runs issued at or after kickoff.
Each check below is shown to catch the leak when it is planted back in, and to pass on the fixed code.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from nflmodel import trends as T, forecast_history as FH, wind_live as WL

P = Path(__file__).resolve().parent.parent / "data" / "processed"


def _prior_mean_by_order(d, key, val, k, prior, window_seasons=None):
    """The pre-fix referee prior: every earlier row in `order`, which puts a game's away row before its home row."""
    res = pd.Series(np.nan, index=d.index)
    d = d.sort_values("order")
    for _, g in d.groupby(key, sort=False):
        v = g[val].values.astype(float); ok = ~np.isnan(v); vv = np.where(ok, v, 0.0)
        prev_s = np.concatenate([[0.0], np.cumsum(vv)[:-1]]); prev_n = np.concatenate([[0.0], np.cumsum(ok.astype(float))[:-1]])
        res.loc[g.index] = T.shrink(prev_s, prev_n, k, prior)
    return res


def _toy():
    """One referee, three games on three Sundays (two team rows each), and a fourth game at the same kickoff as game 3."""
    rows = []
    for i, (day, gid, tot) in enumerate([("2024-09-08", "g1", 40.0), ("2024-09-15", "g2", 50.0), ("2024-09-22", "g3", 44.0), ("2024-09-22", "g4", 60.0)]):
        for home in (False, True):
            rows.append({"game_id": gid, "gameday": day, "kickoff_et": pd.Timestamp(day + " 13:00"), "home": home, "referee": "R", "season": 2024, "tot": tot})
    d = pd.DataFrame(rows).sort_values(["gameday", "game_id", "home"]).reset_index(drop=True)
    d["order"] = np.arange(len(d))
    return d


def _own_game_moves(prior):
    """Largest change in any row's prior for game g3 when g3's own total is corrupted."""
    d = _toy(); bad = d.copy(); bad.loc[bad.game_id == "g3", "tot"] += 100
    a = prior(d, "referee", "tot", 0.0, 0.0); b = prior(bad, "referee", "tot", 0.0, 0.0)
    m = d.game_id == "g3"
    return float((a[m] - b[m]).abs().max())


def test_referee_prior_ignores_its_own_game_and_the_check_sees_the_old_leak():
    assert _own_game_moves(_prior_mean_by_order) > 10   # the planted (old) prior moves with the game's own total
    assert _own_game_moves(T._prior_mean) == 0.0         # the fixed one does not
    d = _toy(); r = T._prior_mean(d, "referee", "tot", 0.0, 0.0)
    # g3 and g4 share a kickoff: each sees only g1 and g2 (mean 45), both rows of a game read the same number
    assert np.allclose(r[d.game_id.isin(["g3", "g4"])], 45.0)
    assert r[d.game_id == "g2"].nunique() == 1 and np.isclose(r[d.game_id == "g2"].iloc[0], 40.0)


@pytest.mark.skipif(not (P / "games.parquet").exists() or not (P / "team_box.parquet").exists(), reason="processed tables not present")
def test_trend_table_rows_of_a_game_do_not_read_its_score():
    games = pd.read_parquet(P / "games.parquet"); tg = pd.read_parquet(P / "team_games.parquet")
    g = games[(games.season == 2023) & games.home_score.notna()]
    bad = games.copy(); m = bad.game_id.isin(g.game_id)
    bad.loc[m, "home_score"] += 30; bad.loc[m, "total"] += 30; bad.loc[m, "result"] += 30
    a = T.trend_table(games, tg).set_index(["game_id", "team"]); b = T.trend_table(bad, tg).set_index(["game_id", "team"])
    ids = a.index.get_level_values(0).isin(g.game_id)
    cols = ["ref_over", "ref_tot", "ref_home_cover", "ref_pen", "h2h_cover", "coach_ats", "qb_ats", "team_home_edge", "cold_edge", "wind_edge"]
    # a 2023 game's own priors must not move when 2023's scores change... except through earlier 2023 games, so compare
    # the season's first week only, which has no earlier 2023 game
    first = a.index.get_level_values(0).isin(g[g.week == g.week.min()].game_id)
    assert np.allclose(a.loc[first, cols].fillna(-9).values, b.loc[first, cols].fillna(-9).values)
    # and both rows of every game read the same referee prior
    t = T.trend_table(games, tg)
    assert (t.groupby("game_id").ref_tot.nunique() <= 1).all()
    assert ids.any()


@pytest.mark.skipif(not (P / "features_asof.parquet").exists() or not (P / "trends_asof.parquet").exists(), reason="processed tables not present")
def test_own_game_score_never_moves_its_prediction_and_the_planted_referee_leak_is_caught(monkeypatch):
    from nflmodel import audit as A
    assert A.own_game_shift(2024, 9) == 0.0
    monkeypatch.setattr(T, "_prior_mean", _prior_mean_by_order)   # put the old referee prior back
    from nflmodel import model as M_
    if "ref_tot" not in M_.TOTAL_FEATS:   # ref_tot left the totals equation on 2 Oct 2026; plant it back with its old leak
        monkeypatch.setattr(M_, "TOTAL_FEATS", M_.TOTAL_FEATS + ["ref_tot"])
    assert A.own_game_shift(2024, 9) > 0.05


# ---- (b) forecasts issued after kickoff

def test_run_rule_matches_gfs_and_rejects_a_post_kickoff_run():
    ko = pd.Timestamp("2024-12-08T18:00Z")
    assert FH.last_run(ko) == pd.Timestamp("2024-12-08T12:00Z")
    assert FH.run_ok(FH.last_run(ko), ko)
    assert not FH.run_ok(ko, ko)                                  # a run at kickoff is planted leak: caught
    assert not FH.run_ok(pd.Timestamp("2024-12-08T18:00Z") - pd.Timedelta(hours=4), ko)
    assert "jma_wind_d0" not in FH.PRE_KICKOFF_WIND and "jma_wind_d0" in FH.POST_KICKOFF


def test_live_japan_reading_uses_the_day_before_run():
    ko = pd.Timestamp("2024-12-08T18:00Z")
    assert FH.jma_pre_kickoff(7.0, 99.0, ko, ko - pd.Timedelta(hours=1)) == 7.0
    assert FH.jma_pre_kickoff(None, 99.0, ko, ko - pd.Timedelta(hours=1)) is None      # the newest run could be past the cutoff
    assert FH.jma_pre_kickoff(None, 8.0, ko, ko - pd.Timedelta(days=2)) == 8.0          # two days out, the newest run is early enough


def _stored(tmp_path, jma_d0):
    f = tmp_path / "fh.csv"
    pd.DataFrame([{"game_id": "2024_14_X_Y", "season": 2024, "gfs_wind_d0": 10.0, "nbs_wind_d0": np.nan, "jma_wind_d1": 12.0, "jma_wind_d0": jma_d0}]).to_csv(f, index=False)
    return f


def test_stored_wind_reading_ignores_the_post_kickoff_run_and_the_check_sees_one(tmp_path, monkeypatch):
    monkeypatch.setattr(WL, "F", tmp_path / "none.csv")
    def reading(jma_d0, cols=None):
        monkeypatch.setattr(FH, "OUTF", _stored(tmp_path, jma_d0))
        if cols is not None:
            monkeypatch.setattr(FH, "PRE_KICKOFF_WIND", cols)
        return WL.readings()["2024_14_X_Y"]
    assert reading(5.0) == reading(40.0) == 11.0                   # corrupting the post-kickoff run moves nothing
    planted = ["gfs_wind_d0", "nbs_wind_d0", "jma_wind_d0"]        # the pre-fix reading
    assert reading(5.0, planted) != reading(40.0, planted)         # the same check catches it
