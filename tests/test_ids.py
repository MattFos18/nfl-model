"""Player ids (24 Sep 2026): a PFR table row gets its gsis id by PFR id, else by a name unique on that team's roster
that season, never by the name league-wide (one Connor McGovern's games once went to the other)."""
import pandas as pd
from nflmodel import ids


def test_map_pfr(monkeypatch):
    monkeypatch.setattr(ids, "_PFR_IDS", {"McGoCo00": "00-0033011", "McGoCo01": "00-0035679"})
    monkeypatch.setattr(ids, "_ROSTER_NAMES", {(2025, "LV", "codywhite"): "00-0035891"})
    df = pd.DataFrame({"pfr_player_id": ["McGoCo01", "McGoCo00", "WhitCo05", "WhitCo05", "NoneXx00"],
                       "player": ["Connor McGovern", "Connor McGovern", "Cody White", "Cody White", "Nobody"],
                       "team": ["BUF", "NYJ", "LV", "HOU", "BUF"], "season": [2025, 2023, 2025, 2025, 2025]})
    got = ids.map_pfr(df).tolist()
    assert got[:3] == ["00-0035679", "00-0033011", "00-0035891"]
    assert pd.isna(got[3]) and pd.isna(got[4])       # same name on another team: no match, not a guess
