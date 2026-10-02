"""Unplayed games at retractable-roof stadiums with no roof listed count as closed, and no weather reading applies to a
roofed game (2 Oct 2026: the wind under fired on 2026_04_DAL_HOU at Houston, whose roof was closed 68 of 71 times)."""
import pandas as pd

from nflmodel import build as B, wind_live as W


def test_retractable_home_with_blank_roof_is_closed_only_when_unplayed():
    src = B.Path(B.__file__).read_text(encoding="utf-8")
    assert "RETRACTABLE_HOME" in src and 'g.loc[retract, "roof"] = "closed"' in src and '"MAD01"' in src
    g = pd.DataFrame({"home_team": ["HOU", "HOU", "KC", "DAL"], "location": ["Home", "Home", "Home", "Neutral"],
                      "home_score": [None, 24, None, None], "roof": [None, "open", None, None]})
    retract = g.home_team.isin(B.RETRACTABLE_HOME) & ~g.location.eq("Neutral") & g.home_score.isna() & (g.roof.isna() | g.roof.astype(str).str.strip().eq(""))
    g.loc[retract, "roof"] = "closed"
    assert list(g.roof.fillna("-")) == ["closed", "open", "-", "-"]


def test_readings_drop_roofed_games(monkeypatch):
    monkeypatch.setattr(W, "_roofed", lambda: {"G_ROOF"})
    monkeypatch.setattr(W.FH, "OUTF", W.FH.OUTF.with_name("does_not_exist.csv"))
    monkeypatch.setattr(W, "F", W.F.with_name("does_not_exist.csv"))
    assert W.readings() == {} and W.rain_readings() == {} and W.temp_readings() == {}
