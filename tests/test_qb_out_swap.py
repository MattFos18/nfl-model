"""A starting QB ruled out for the week being priced is swapped for his replacement on unplayed games only (2 Oct 2026:
the WAS card priced Jayden Daniels after ESPN ruled him Out)."""
from pathlib import Path

import pandas as pd
import pytest

from nflmodel import ratings as R

OUT = Path(__file__).resolve().parent.parent / "data" / "processed"
pytestmark = pytest.mark.skipif(not (OUT / "features_asof.parquet").exists(), reason="processed tables not present")


def test_unplayed_starter_out_is_swapped_and_played_games_are_not(monkeypatch):
    games = pd.read_parquet(OUT / "games.parquet")
    up = games[games.home_score.isna() & (games.game_type == "REG") & games.home_qb_id.notna()].sort_values(["season", "week"])
    if not len(up):
        pytest.skip("no unplayed game with a named starter")
    g = up.iloc[0]; s, w, team, starter = int(g.season), int(g.week), g.home_team, g.home_qb_id
    monkeypatch.setattr(R, "qbs_out_now", lambda games_: ((s, w), {team: {starter}}))
    monkeypatch.setattr(R, "replacement_qb", lambda t, out, season, qb: "BACKUP-ID" if t == team else None)
    f = R.build_features(R.DEFAULT, seasons=[s])
    row = f[(f.game_id == g.game_id) & (f.team == team)].iloc[0]
    assert row.qb_id == "BACKUP-ID"
    opp = f[(f.game_id == g.game_id) & (f.team != team)].iloc[0]
    assert opp.opp_qb_rating == row.qb_rating            # the opponent faces the replacement too
    played = f[f.pf.notna() & (f.team == team)]
    assert not (played.qb_id == "BACKUP-ID").any()        # the backtest's games keep the QB who started


def test_no_injury_data_keeps_the_named_starter(monkeypatch):
    monkeypatch.setattr(R, "qbs_out_now", lambda games_: ((None, None), {}))
    games = pd.read_parquet(OUT / "games.parquet"); s = int(games.season.max())
    f = R.build_features(R.DEFAULT, seasons=[s])
    named = games[(games.season == s) & games.home_qb_id.notna()].set_index("game_id").home_qb_id
    h = f[f.home == 1].set_index("game_id").qb_id
    common = named.index.intersection(h.index)
    assert (h[common] == named[common]).all()
