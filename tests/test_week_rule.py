"""The picks week holds until the week before is in every source (lines.current_week, 28 Sep 2026)."""
import pandas as pd
from nflmodel import lines as LN


def _games():
    rows = []
    for w in (1, 2, 3):
        for i in range(2):
            rows.append({"game_id": f"2026_0{w}_A{i}_H{i}", "season": 2026, "week": w, "game_type": "REG", "home_score": 20.0 if w < 3 else None, "kickoff_et": pd.Timestamp("2026-09-01") + pd.Timedelta(days=7 * w)})
    return pd.DataFrame(rows)


def test_picks_week_waits_for_every_source(monkeypatch):
    g = _games()
    have = {"games.parquet": set(g[g.home_score.notna()].game_id), "team_box.parquet": set(g[g.week == 1].game_id) | {"2026_02_A0_H0"},
            "player_games.parquet": set(g[g.week <= 2].game_id), "snap_exposure.parquet": set(g[g.week <= 2].game_id), "scheme_plays.parquet": set(g[g.week <= 2].game_id)}
    monkeypatch.setattr(LN, "_source_games", lambda fname, season: have.get(fname, set()))
    ok, missing = LN.week_complete(g, 2026, 1)
    assert ok and missing == []
    ok, missing = LN.week_complete(g, 2026, 2)
    assert not ok and missing == ["play-by-play: 2026_02_A1_H1"]   # scored, but one game's play-by-play has not arrived
    assert LN.current_week(g) == (2026, 2)   # so week 2 is still the picks week, not week 3
    have["team_box.parquet"] = set(g[g.week <= 2].game_id)
    assert LN.current_week(g) == (2026, 3)   # every source in: the picks week moves on


def test_state_says_pending_only_after_the_last_kickoff(monkeypatch):
    g = _games()
    have = {k: set(g[g.week == 1].game_id) for _, k in LN.WEEK_SOURCES}
    monkeypatch.setattr(LN, "_source_games", lambda fname, season: have.get(fname, set()))
    st = LN.week_state(g)
    assert st["week"] == 2 and st["pending"] and st["all_kicked_off"]   # week 2 was played (kickoffs past) but nothing has arrived
    have["games.parquet"] = set(g[g.week <= 2].game_id)
    st = LN.week_state(g)
    assert st["week"] == 2 and st["pending"] and any(m.startswith("play-by-play") for m in st["missing"])
