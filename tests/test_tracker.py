"""The tracker's record (28 Sep 2026): a pick recorded before kickoff must survive every run between kickoff and
nflverse's score. Three shadow Unders were dropped that way on 27 Sep (two winners, one loser)."""
import pandas as pd
import pytest
from nflmodel import tracker as T


def games(kick):
    return pd.DataFrame([{"game_id": "2026_04_A_B", "season": 2026, "week": 4, "home_team": "B", "away_team": "A", "kickoff_et": kick, "home_score": float("nan")}])


def picks(bet):
    return pd.DataFrame([{"season": 2026, "week": 4, "game_id": "2026_04_A_B", "home_team": "B", "bet": bet, "bet_odds": -110, "spread_edge": 4.5, "total_edge": 0.0, "p_cover_home": 0.6}])


@pytest.fixture
def tmp_tracker(tmp_path, monkeypatch):
    monkeypatch.setattr(T, "OUT", tmp_path); monkeypatch.setattr(T, "TR", tmp_path / "tracker")
    return tmp_path


def test_pick_survives_kickoff(tmp_tracker):
    now = pd.Timestamp.now(tz="America/New_York").tz_localize(None)
    games(now + pd.Timedelta(hours=3)).to_parquet(tmp_tracker / "games.parquet")
    T._record(picks("B -3"), "run 1", "bet", "model_picks.csv")
    assert list(pd.read_csv(tmp_tracker / "tracker" / "model_picks.csv").bet) == ["B -3"]
    # the next run, 20 minutes after kickoff, no score yet, the flag gone on the newest line: the recorded pick stands
    games(now - pd.Timedelta(minutes=20)).to_parquet(tmp_tracker / "games.parquet")
    T._record(picks(""), "run 2", "bet", "model_picks.csv")
    assert list(pd.read_csv(tmp_tracker / "tracker" / "model_picks.csv").bet) == ["B -3"]


def test_unplayed_pick_follows_the_newest_run(tmp_tracker):
    now = pd.Timestamp.now(tz="America/New_York").tz_localize(None)
    games(now + pd.Timedelta(hours=3)).to_parquet(tmp_tracker / "games.parquet")
    T._record(picks("B -3"), "run 1", "bet", "model_picks.csv")
    T._record(picks("B -3.5"), "run 2", "bet", "model_picks.csv")
    assert list(pd.read_csv(tmp_tracker / "tracker" / "model_picks.csv").bet) == ["B -3.5"]
    T._record(picks(""), "run 3", "bet", "model_picks.csv")
    assert len(pd.read_csv(tmp_tracker / "tracker" / "model_picks.csv")) == 0
