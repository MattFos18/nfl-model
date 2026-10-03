"""Silent failures in the live pipeline (code review, 2 Oct 2026): the QB-out check fails loudly, the replacement QB is
on the team's current active roster, the card names the QB priced after a swap, ESPN statuses from before the week
change do not count, and the run logs keep their columns."""
import json

import pandas as pd
import pytest

from nflmodel import export_web as EW, features as F, lines as LN, picks as P, players as PL, ratings as R


def _games(now_et):
    """A week 3 played (last kickoff two days ago) and a week 4 to come."""
    return pd.DataFrame({"game_id": ["2026_03_A_B", "2026_03_C_D", "2026_04_A_C"], "season": 2026, "week": [3, 3, 4], "game_type": "REG",
                         "home_team": ["B", "D", "C"], "away_team": ["A", "C", "A"],
                         "kickoff_et": [now_et - pd.Timedelta(days=3), now_et - pd.Timedelta(days=2), now_et + pd.Timedelta(days=2)]})


@pytest.fixture
def week4(monkeypatch):
    monkeypatch.setattr(LN, "current_week", lambda games: (2026, 4))


# 1. the QB-out check
def test_qbs_out_now_fails_loudly_on_a_broken_injury_load(tmp_path, monkeypatch, week4, capsys):
    (tmp_path / "injuries").mkdir(); (tmp_path / "injuries" / "injuries_2026.parquet").write_bytes(b"")
    monkeypatch.setattr(F, "RAW", tmp_path)
    def boom(seasons):
        raise ValueError("corrupt parquet")
    monkeypatch.setattr(PL, "load_injuries", boom)
    monkeypatch.setattr(PL, "unavailable_by_week", lambda seasons: {(2026, 4, "WAS"): {"IR1"}})
    st = {}
    (s, w), out = R.qbs_out_now(pd.DataFrame(), status=st)
    assert st["status"] == "error" and "corrupt parquet" in st["detail"]
    assert out == {"WAS": {"IR1"}} and (s, w) == (2026, 4)   # the roster lists still count
    assert "WARNING" in capsys.readouterr().err


@pytest.mark.parametrize("status,code", [("error", 1), ("ok", 0), ("no injury file", 0)])
def test_ratings_step_fails_when_the_check_fails(tmp_path, monkeypatch, status, code):
    f = pd.DataFrame({"game_id": ["g1"], "team": ["WAS"], "qb_id": ["QB1"], "qb_swap_from": [None]})
    f.attrs["qb_out_status"] = {"status": status, "detail": "boom", "season": 2026, "week": 4}
    monkeypatch.setattr(R, "build_features", lambda **k: f)
    monkeypatch.setattr(R, "OUT", tmp_path); monkeypatch.setattr(R, "SWAPS", tmp_path / "qb_swaps.json")
    monkeypatch.setattr(R, "qb_names", lambda season=None: {})
    assert R.main() == code
    assert json.loads((tmp_path / "qb_swaps.json").read_text())["status"] == status and (tmp_path / "features_asof.parquet").exists()


def test_health_warns_on_a_stale_or_weak_swaps_file(tmp_path, monkeypatch):
    from nflmodel import health as H
    (tmp_path / "runs").mkdir()
    (tmp_path / "runs" / "qb_swaps.json").write_text(json.dumps({"status": "ok", "season": 2026, "week": 3, "espn_unmatched": ["NO Someone Jr."],
                                                                 "swaps": [{"team": "WAS", "from": "QB1", "from_name": "A", "to": None, "to_name": None, "source": "none"}]}))
    monkeypatch.setattr(H, "DATA", tmp_path); monkeypatch.setattr(H, "REP", tmp_path)
    monkeypatch.setattr(LN, "current_week", lambda games: (2026, 4))
    monkeypatch.setattr(pd, "read_parquet", lambda *a, **k: pd.DataFrame())
    H.main()
    txt = (tmp_path / "health.md").read_text()
    assert "| WARN | QB-out check loaded the injury reports (week 3) |" in txt and "the picks week is 2026 week 4" in txt
    assert "| WARN | QB swaps priced this week (week 3) | WAS A -> replacement-level prior" in txt
    assert "| WARN | ESPN Out/Doubtful players all matched to a roster player | 1 unmatched: NO Someone Jr." in txt


def test_qbs_out_now_missing_injury_file_is_the_quiet_case(tmp_path, monkeypatch, week4, capsys):
    monkeypatch.setattr(F, "RAW", tmp_path)
    monkeypatch.setattr(PL, "unavailable_by_week", lambda seasons: {(2026, 4, "WAS"): {"QB1"}})
    st = {}
    (_, _), out = R.qbs_out_now(pd.DataFrame(), status=st)
    assert st["status"] == "no injury file"
    assert out == {"WAS": {"QB1"}}                       # the roster lists still count
    assert "WARNING" not in capsys.readouterr().err


def test_qbs_out_now_espn_merge_error_keeps_the_league_report_and_flags(tmp_path, monkeypatch, week4):
    (tmp_path / "injuries").mkdir(); (tmp_path / "injuries" / "injuries_2026.parquet").write_bytes(b"")
    monkeypatch.setattr(F, "RAW", tmp_path)
    def load(seasons):
        PL.ESPN_MERGE["error"] = "KeyError: espn_id"
        return pd.DataFrame({"season": [2026], "week": [4], "team": ["WAS"], "gsis_id": ["QB1"], "report_status": ["Out"]})
    monkeypatch.setattr(PL, "load_injuries", load)
    monkeypatch.setattr(PL, "unavailable_by_week", lambda seasons: {})
    st = {}
    (_, _), out = R.qbs_out_now(pd.DataFrame(), status=st)
    PL.ESPN_MERGE["error"] = None
    assert out == {"WAS": {"QB1"}} and st["status"] == "error" and "espn_id" in st["detail"]


def test_swaps_file_lists_the_swap_and_the_status(tmp_path, monkeypatch):
    monkeypatch.setattr(R, "SWAPS", tmp_path / "qb_swaps.json")
    monkeypatch.setattr(R, "qb_names", lambda season=None: {"QB1": "Starter", "QB2": "Backup"})
    f = pd.DataFrame({"game_id": ["g1", "g1"], "team": ["WAS", "NYG"], "qb_id": ["QB2", "QB9"], "qb_swap_from": ["QB1", None]})
    f.attrs["qb_out_status"] = {"status": "error", "detail": "x", "season": 2026, "week": 4}; f.attrs["qb_swap_source"] = {"WAS": "depth chart"}
    R.write_swaps(f)
    d = json.loads((tmp_path / "qb_swaps.json").read_text())
    assert d["status"] == "error" and d["week"] == 4
    assert d["swaps"] == [{"game_id": "g1", "team": "WAS", "from": "QB1", "from_name": "Starter", "to": "QB2", "to_name": "Backup", "source": "depth chart"}]


# 2. the replacement QB
def _rosters(tmp_path, monkeypatch, weekly):
    out = tmp_path / "processed"; out.mkdir(); raw = tmp_path / "raw"; (raw / "rosters").mkdir(parents=True)
    pd.DataFrame({"team": "WAS", "player_id": ["QB1", "QB2", "QB3"], "position": "QB", "depth": [1.0, 2.0, 3.0]}).to_parquet(out / "roster_now.parquet")
    if weekly is not None:
        pd.DataFrame(weekly).to_parquet(raw / "rosters" / "roster_weekly_2026.parquet")
    monkeypatch.setattr(R, "OUT", out); monkeypatch.setattr(F, "RAW", raw)


QB = pd.DataFrame({"season": 2026, "team": "WAS", "qb_id": ["QB1", "QB3", "QB4"], "dropbacks": [100, 30, 60]})


def test_replacement_skips_a_backup_released_since_the_depth_chart(tmp_path, monkeypatch):
    _rosters(tmp_path, monkeypatch, {"team": "WAS", "gsis_id": ["QB1", "QB2", "QB3", "QB2"], "status": ["ACT", "ACT", "ACT", "CUT"], "week": [4, 3, 4, 4]})
    assert R.replacement_qb("WAS", {"QB1"}, 2026, QB, week=4) == ("QB3", "depth chart")


def test_replacement_falls_back_to_dropbacks_when_no_depth_qb_is_active(tmp_path, monkeypatch):
    _rosters(tmp_path, monkeypatch, {"team": "WAS", "gsis_id": ["QB1", "QB2", "QB3", "QB4"], "status": ["ACT", "INA", "CUT", "ACT"], "week": 4})
    pid, src = R.replacement_qb("WAS", {"QB1"}, 2026, QB, week=4)
    assert pid == "QB4" and src.startswith("most dropbacks") and "QB2, QB3" in src   # QB3 has fewer dropbacks and is gone anyway


def test_replacement_without_a_weekly_roster_says_so(tmp_path, monkeypatch):
    _rosters(tmp_path, monkeypatch, None)
    assert R.replacement_qb("WAS", {"QB1"}, 2026, QB, week=4) == ("QB2", "depth chart (no weekly roster to check)")


# 3. the card's QB after a swap
def test_card_names_the_qb_priced_not_the_starter_ruled_out():
    side = EW.card_qb({}, pd.Series({"qb_id": "QB2", "qb_swap_from": "QB1"}), "Jayden Daniels", {"QB1": "Jayden Daniels"}, {"QB1": "Jayden Daniels", "QB2": "Marcus Mariota"})
    assert side["qb_name"] == "Marcus Mariota" and side["qb_swap_from"] == "Jayden Daniels" and "qb_priced" not in side


def test_card_still_follows_a_new_named_starter():
    side = EW.card_qb({}, pd.Series({"qb_id": "QB1", "qb_swap_from": None}), "Marcus Mariota", {"QB1": "Jayden Daniels"}, {})
    assert side["qb_name"] == "Marcus Mariota" and side["qb_priced"] == "Jayden Daniels"


# 4. ESPN statuses at the week change
def test_espn_status_fetched_before_last_weeks_final_kickoff_does_not_count(monkeypatch, week4):
    now_et = pd.Timestamp.now(tz="America/New_York").tz_localize(None); now = pd.Timestamp.now("UTC").tz_localize(None)
    g = _games(now_et)
    es = pd.DataFrame({"fetched_at": [(now - pd.Timedelta(days=3)).isoformat(), (now - pd.Timedelta(hours=1)).isoformat(), (now - pd.Timedelta(days=5)).isoformat()]})
    assert PL.espn_fresh(es, g).tolist() == [False, True, False]   # last Sunday's page (inside four days), this week's, too old


def test_load_injuries_ignores_last_weeks_espn_page(tmp_path, monkeypatch, week4):
    now_et = pd.Timestamp.now(tz="America/New_York").tz_localize(None); now = pd.Timestamp.now("UTC").tz_localize(None)
    raw, out = tmp_path / "raw", tmp_path / "processed"; (raw / "injuries").mkdir(parents=True); (raw / "rosters").mkdir(); out.mkdir()
    _games(now_et).to_parquet(out / "games.parquet")
    pd.DataFrame({"season": [2026], "week": [4], "team": ["C"], "gsis_id": ["X0"], "full_name": ["Other Guy"], "position": ["WR"], "report_status": [None],
                  "report_primary_injury": [None]}).to_parquet(raw / "injuries" / "injuries_2026.parquet")
    pd.DataFrame({"team": "A", "gsis_id": ["P1", "P2"], "espn_id": ["11", "12"], "full_name": ["Old Status", "New Status"], "position": "QB", "week": 4}).to_parquet(raw / "rosters" / "roster_weekly_2026.parquet")
    pd.DataFrame({"team": "A", "espn_id": ["11", "12", None], "name": ["Old Status", "New Status", "Nobody Jr."], "position": "QB", "status": "Out", "date": "", "detail": "Knee", "return_date": "",
                  "fetched_at": [(now - pd.Timedelta(days=3)).isoformat(), (now - pd.Timedelta(hours=1)).isoformat(), (now - pd.Timedelta(hours=1)).isoformat()]}).to_csv(raw / "injuries" / "espn_injuries.csv", index=False)
    monkeypatch.setattr(PL, "RAW", raw); monkeypatch.setattr(PL, "OUT", out)
    inj = PL.load_injuries([2026])
    assert PL.ESPN_MERGE["error"] is None
    assert PL.ESPN_MERGE["unmatched"] == ["A Nobody Jr."]   # an Out row with no roster match is listed, not dropped silently
    assert sorted(inj[(inj.week == 4) & (inj.report_status == "Out")].gsis_id) == ["P2"]


# 5. the run logs' columns
def test_rule_history_appends_by_column_name(tmp_path):
    f = tmp_path / "rule_history.csv"
    P.append_csv(pd.DataFrame({"run_at": ["r1"], "game_id": ["g1"], "shadowunder_bet": ["Under 40"], "windunder_bet": [""]}), f)
    P.append_csv(pd.DataFrame({"windunder_bet": ["Under 41"], "game_id": ["g2"], "run_at": ["r2"]}), f)          # reordered, one rule missing
    P.append_csv(pd.DataFrame({"run_at": ["r3"], "game_id": ["g3"], "windunder_bet": [""], "rainunder_bet": ["Under 39"]}), f)   # a new rule
    d = pd.read_csv(f, dtype=str, keep_default_na=False)
    assert list(d.columns) == ["run_at", "game_id", "shadowunder_bet", "windunder_bet", "rainunder_bet"]
    assert d.to_dict("records") == [
        {"run_at": "r1", "game_id": "g1", "shadowunder_bet": "Under 40", "windunder_bet": "", "rainunder_bet": ""},
        {"run_at": "r2", "game_id": "g2", "shadowunder_bet": "", "windunder_bet": "Under 41", "rainunder_bet": ""},
        {"run_at": "r3", "game_id": "g3", "shadowunder_bet": "", "windunder_bet": "", "rainunder_bet": "Under 39"}]


def test_card_names_last_starter_when_schedule_is_stale():
    """3 Oct 2026: the schedule named Drew Lock for SEA week 4; Sam Darnold started week 3 and was healthy."""
    side = EW.card_qb({}, pd.Series({"qb_id": "DAR", "qb_swap_from": None, "qb_named_over": "LOCK"}), "Drew Lock",
                      {"DAR": "Sam Darnold", "LOCK": "Drew Lock"}, {"DAR": "Sam Darnold", "LOCK": "Drew Lock"})
    assert side["qb_name"] == "Sam Darnold" and side["qb_named_over"] == "Drew Lock" and "qb_priced" not in side
