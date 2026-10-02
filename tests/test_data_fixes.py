"""The 2 Oct 2026 data fixes catch and correct each planted bad row: a listed starter who took no dropback, a game abroad
listed at a US stadium or under a dome, a schedule wind far from the archive, a line snapshot after kickoff."""
import numpy as np
import pandas as pd

from nflmodel import build as B, data_checks as DC, lines as LN, venues as V


def games(**over):
    g = pd.DataFrame({
        "game_id": ["2025_07_LA_JAX", "2016_13_NYG_PIT", "2024_15_IND_DEN", "2024_17_DAL_PHI", "2026_10_NE_DET"],
        "season": [2025, 2016, 2024, 2024, 2026], "game_type": "REG", "week": [7, 13, 15, 17, 10],
        "home_team": ["JAX", "PIT", "DEN", "PHI", "DET"], "away_team": ["LA", "NYG", "IND", "DAL", "NE"],
        "home_score": [7.0, 24.0, 31.0, 41.0, np.nan], "away_score": [35.0, 14.0, 13.0, 7.0, np.nan],
        "location": ["Neutral", "Home", "Home", "Home", "Neutral"],
        "stadium_id": ["JAX00", "PIT00", "DEN00", "PHI00", "MUN01"],
        "stadium": ["TIAA Bank Stadium", "Heinz Field", "Empower Field at Mile High", "Lincoln Financial Field", "FC Bayern Munich Stadium"],
        "roof": ["outdoors", "outdoors", "outdoors", "outdoors", "dome"],
        "wind": [9.0, 71.0, 15.0, 8.0, np.nan],
        "home_qb_id": ["Q_JAX", "Q_PIT", "Q_DEN", "Q_HURTS", "Q_DET"], "away_qb_id": ["Q_LA", "Q_NYG", "Q_IND", "Q_DAL", "Q_NE"],
        "home_qb_name": ["J", "P", "D", "Jalen Hurts", "De"], "away_qb_name": ["L", "N", "I", "Da", "Ne"],
    })
    g["dome"] = g.roof.isin(["dome", "closed"]); g["neutral"] = g.location.eq("Neutral")
    return g.assign(**over)


def failed(rows):
    return [w for w, ok, _ in rows if not ok]


def test_venues_caught_and_fixed():
    g = games()
    assert set(V.venue_problems(g)) == {"2025_07_LA_JAX", "2026_10_NE_DET"}   # London listed at TIAA Bank; Munich marked dome
    f = V.fix_venues(g)
    assert V.venue_problems(f) == []
    r = f.set_index("game_id")
    assert r.at["2025_07_LA_JAX", "stadium_id"] == "LON00" and r.at["2026_10_NE_DET", "roof"] == "outdoors" and not r.at["2026_10_NE_DET", "dome"]
    s = V.sites(f).set_index(f.game_id)
    assert s.at["2025_07_LA_JAX", "site"] == "London Wembley" and pd.isna(s.at["2025_07_LA_JAX", "station"])
    assert s.at["2016_13_NYG_PIT", "station"] == "KPIT"
    # a shared stadium keeps the home team's key; a stadium left behind has its own coordinates
    assert V.site("NYC01", "NYJ")["site"] == "NYJ" and V.site("OAK00", "LV")["site"] == "Oakland"


def test_wind_replaced_only_where_a_second_source_agrees():
    g = games()
    arch = pd.DataFrame({"game_id": ["2016_13_NYG_PIT", "2024_15_IND_DEN", "2024_17_DAL_PHI", "2025_07_LA_JAX"],
                         "site": ["PIT", "DEN", "PHI", "JAX"], "wind": [6.4, 4.9, 30.0, 25.0]})
    fc = pd.DataFrame({"game_id": ["2024_15_IND_DEN"], "gfs_wind_d0": [20.9]})
    w = B.fix_wind(V.fix_venues(g), arch, fc).set_index("game_id")
    assert w.at["2016_13_NYG_PIT", "wind"] == 6.4 and w.at["2016_13_NYG_PIT", "wind_listed"] == 71.0   # no forecast: the archive
    assert w.at["2024_15_IND_DEN", "wind"] == 15.0          # the forecast (20.9) sides with the schedule: kept
    assert w.at["2024_17_DAL_PHI", "wind"] == 30.0          # no forecast, archive 22 off: the archive
    assert w.at["2025_07_LA_JAX", "wind"] == 9.0            # an archive row from the wrong site (Jacksonville for London) is ignored
    nothing = B.fix_wind(g, arch.iloc[:0], fc.iloc[:0]).set_index("game_id")
    assert np.isnan(nothing.at["2016_13_NYG_PIT", "wind"])  # above WIND_MAX with nothing to replace it: blank


def pbp():
    rows = []   # (game_id, posteam, passer_id, passer, dropback)
    rows += [("2024_17_DAL_PHI", "PHI", "Q_WR", "Receiver", 1)]                     # a trick throw comes first
    rows += [("2024_17_DAL_PHI", "PHI", "Q_PICKETT", "Kenny Pickett", 1)] * 20
    rows += [("2024_17_DAL_PHI", "PHI", "Q_TANNER", "Tanner McKee", 1)] * 5
    rows += [("2024_17_DAL_PHI", "DAL", "Q_DAL", "Da", 1)] * 30
    rows += [("2024_15_IND_DEN", "DEN", "Q_DEN", "D", 1)] * 2 + [("2024_15_IND_DEN", "DEN", "Q_BACKUP", "B", 1)] * 30   # listed QB hurt early: started
    rows += [("2024_15_IND_DEN", "IND", "Q_IND", "I", 1)] * 30
    p = pd.DataFrame(rows, columns=["game_id", "posteam", "passer_id", "passer", "qb_dropback"])
    return p


def test_starter_who_took_no_dropback_is_replaced():
    g = B.fix_starters(games(), pbp()).set_index("game_id")
    assert g.at["2024_17_DAL_PHI", "home_qb_id"] == "Q_PICKETT" and g.at["2024_17_DAL_PHI", "home_qb_name"] == "Kenny Pickett"
    assert g.at["2024_17_DAL_PHI", "home_qb_id_listed"] == "Q_HURTS"
    assert g.at["2024_17_DAL_PHI", "away_qb_id"] == "Q_DAL"
    assert g.at["2024_15_IND_DEN", "home_qb_id"] == "Q_DEN"       # dropped back twice: he started, he stays
    assert g.at["2026_10_NE_DET", "home_qb_id"] == "Q_DET"        # unplayed: the announced starter
    assert g.at["2016_13_NYG_PIT", "home_qb_id"] == "Q_PIT"       # no play-by-play for the game: unchanged


def test_input_checks_catch_planted_rows():
    p = pbp()
    qb = p.groupby(["game_id", "posteam", "passer_id"]).size().reset_index().rename(columns={"posteam": "team", "passer_id": "qb_id"})
    qb = pd.concat([qb, pd.DataFrame({"game_id": ["2016_13_NYG_PIT", "2016_13_NYG_PIT", "2025_07_LA_JAX", "2025_07_LA_JAX"],
                                      "team": ["PIT", "NYG", "JAX", "LA"], "qb_id": ["Q_PIT", "Q_NYG", "Q_JAX", "Q_LA"]})])   # the listed QBs played
    clean = B.fix_wind(V.fix_venues(games()), pd.DataFrame({"game_id": ["2016_13_NYG_PIT"], "site": ["PIT"], "wind": [6.4]}), pd.DataFrame(columns=["game_id", "gfs_wind_d0"]))
    clean = B.fix_starters(clean, p)
    assert failed(DC.check_inputs(clean, qb)) == []
    assert failed(DC.check_inputs(games(), qb)) == ["games: every played game's starting QB dropped back in it",
                                                    "games: neutral-site and overseas games at their real stadium and roof (venues.py)",
                                                    "games: kickoff wind 40 mph or under"]


def test_line_after_kickoff_is_not_the_line():
    log = pd.DataFrame({"ts": ["2026-09-27T20-00-00Z", "2026-09-27T20-26-41Z"], "source": "espn:DraftKings", "game_id": "G",
                        "home_spread": [3.0, 7.5], "total": [44.5, 40.5], "home_ml": np.nan, "away_ml": np.nan})
    # kickoff 4:25 pm Eastern = 20:25 UTC: the 20:26:41 snapshot is in-game
    g = pd.DataFrame({"game_id": ["G"], "spread_line": [2.5], "total_line": [45.0], "kickoff_et": [pd.Timestamp("2026-09-27 16:25")]})
    r = LN.live_lines(g, log).iloc[0]
    assert r.spread_line == 3.0 and r.total_line == 44.5
    early = g.assign(kickoff_et=pd.Timestamp("2026-09-27 18:00"))
    assert LN.live_lines(early, log).iloc[0].spread_line == 7.5   # before kickoff every snapshot counts
    assert len(LN.before_kickoff(log, None)) == 2


# hardening after the review of #381: each gap fails loudly

def test_unparseable_line_timestamps_are_loud():
    import pytest
    log = pd.DataFrame({"ts": ["garbage", "2026-09-27T20-00-00Z"], "game_id": "G", "home_spread": [9.0, 3.0], "total": [40.0, 44.5]})
    n0 = LN.BAD_TS[0]
    assert len(LN.before_kickoff(log, pd.Timestamp("2026-09-27 16:25"))) == 1 and LN.BAD_TS[0] == n0 + 1
    with pytest.raises(ValueError):
        LN.before_kickoff(log.iloc[:1], pd.Timestamp("2026-09-27 16:25"))


def test_schedule_fallback_with_log_rows_is_reported():
    live = pd.DataFrame({"game_id": ["G", "H", "I"], "line_source": ["schedule", "log", "schedule"]})
    log = pd.DataFrame({"game_id": ["G", "H"], "ts": "2026-09-27T20-00-00Z"})
    assert LN.schedule_fallbacks(live, log) == ["G"]   # I has no log rows: the schedule is all there is


def test_unknown_stadium_at_a_neutral_site_fails():
    g = V.fix_venues(games())
    assert V.venue_problems(g) == []
    j = g.game_id == "2025_07_LA_JAX"
    bad = g.assign(stadium_id=g.stadium_id.where(~j, "XYZ99"), stadium=g.stadium.where(~j, "New Stadium"))
    assert V.venue_problems(bad) == ["2025_07_LA_JAX"]
    assert V.venue_problems(bad.assign(game_type=np.where(j, "SB", "REG"))) == []   # a Super Bowl is exempt


def test_played_game_without_play_by_play_warns_then_fails():
    p = pbp()
    qb = p.groupby(["game_id", "posteam", "passer_id"]).size().reset_index().rename(columns={"posteam": "team", "passer_id": "qb_id"})
    g = B.fix_starters(V.fix_venues(games()), p).assign(wind=8.0, kickoff_et=pd.Timestamp("2024-12-29 13:00"))
    g = g[g.game_id.isin(["2024_17_DAL_PHI", "2024_15_IND_DEN", "2025_07_LA_JAX"])]   # 2025_07_LA_JAX has no play-by-play here
    row = lambda now: [r for r in DC.check_inputs(g, qb, now=now) if "play-by-play" in r[0]][0]
    soon = row(pd.Timestamp("2024-12-30 12:00"))
    assert soon[1] and "within it (warning): 2025_07_LA_JAX" in soon[2]
    late = row(pd.Timestamp("2025-01-02 12:00"))
    assert not late[1] and "2025_07_LA_JAX" in late[2]


def test_fix_starters_says_when_it_cannot_run(caplog):
    g = games()
    with caplog.at_level("WARNING"):
        out = B.fix_starters(g, pbp().drop(columns=["passer_id"]))
    assert out.equals(g) and "fix_starters did not run" in caplog.text


def test_fix_wind_counts_and_warns(capsys):
    B.fix_wind(games(), pd.DataFrame(columns=["game_id", "site", "wind"]), pd.DataFrame(columns=["game_id", "gfs_wind_d0"]))
    assert "1 above 40 mph blanked (2016_13_NYG_PIT)" in capsys.readouterr().out
