"""Live games are priced on the same weather readings as the backtest, and checks never rewrite the stored fits
(2 Oct 2026, re-audit items 3, 5 and 6; reports/live_weather_match.md)."""
import ast
import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

from nflmodel import model as M, weather as WX, players as PL, warnlog

ROOT = Path(__file__).resolve().parent.parent


def _games():
    # g1 unplayed outdoors with a MOS reading and an Open-Meteo forecast, g2 unplayed outdoors with Open-Meteo only,
    # g3 unplayed under a closed roof, g4 played, g5 unplayed outdoors with no forecast at all
    return pd.DataFrame({"game_id": ["g1", "g2", "g3", "g4", "g5"], "home_score": [np.nan, np.nan, np.nan, 20.0, np.nan],
                         "roof": ["outdoors", "outdoors", "closed", "outdoors", "outdoors"],
                         "temp": [np.nan, np.nan, np.nan, 50.0, np.nan], "wind": [np.nan, np.nan, np.nan, 3.0, np.nan]})


def _fc():
    return pd.DataFrame({"game_id": ["g1", "g2", "g3"], "temp": [60.0, 40.0, 70.0], "wind": [9.9, 6.0, 1.0],
                         "precip_prob": [10.0, 80.0, 0.0], "precip": [0.0, 2.0, 0.0], "days_out": [2.0, 3.5, 2.0]}).set_index("game_id")


def _mos():
    return ({"g1": 11.4, "g4": 15.0}, {"g1": 30.0, "g4": 20.0}, {"g1": 70.0, "g4": 90.0})


def test_live_source_prefers_mos_and_falls_back_to_open_meteo():
    src = WX.live_source(_games(), _fc(), _mos())
    assert set(src) == {"g1", "g2", "g5"}   # no roofed game, no played game
    assert src["g1"]["wind"] == 11.4 and src["g1"]["temp"] == 30.0 and src["g1"]["pop"] == 70.0
    assert (src["g1"]["wind_src"], src["g1"]["temp_src"], src["g1"]["rain_src"]) == ("mos", "mos", "mos")
    assert src["g2"]["wind"] == 6.0 and src["g2"]["temp"] == 40.0 and src["g2"]["wind_src"] == "open-meteo" and src["g2"]["rain_src"] == "open-meteo"
    assert src["g5"]["wind"] is None and src["g5"]["wind_src"] is None and src["g5"]["rain_src"] is None


def test_apply_to_games_prices_unplayed_games_on_mos_and_logs_each_fallback(monkeypatch):
    monkeypatch.setattr(WX, "usable_forecast", _fc)
    monkeypatch.setattr(WX, "mos_readings", _mos)
    monkeypatch.setattr(WX, "last_good", lambda: pd.DataFrame(columns=["game_id", "temp", "wind"]))
    g = WX.apply_to_games(_games()).set_index("game_id")
    assert g.loc["g1", "wind"] == 11.4 and g.loc["g1", "temp"] == 30.0   # the MOS reading, not Open-Meteo's 9.9 mph and 60F
    assert g.loc["g2", "wind"] == 6.0 and g.loc["g2", "temp"] == 40.0     # no MOS reading: Open-Meteo
    assert g.loc["g4", "wind"] == 3.0 and g.loc["g4", "temp"] == 50.0     # a played game keeps its recorded weather
    assert pd.isna(g.loc["g5", "wind"])                                   # no forecast: typical weather
    msgs = [w["message"] for w in warnlog.recent()]
    assert any(m.startswith("g2:") and "Open-Meteo" in m for m in msgs) and not any(m.startswith("g1:") for m in msgs)
    # the props keep Open-Meteo
    gp = WX.apply_to_games(_games(), mos=False).set_index("game_id")
    assert gp.loc["g1", "wind"] == 9.9 and gp.loc["g1", "temp"] == 60.0


def test_a_failed_mos_reader_warns_and_falls_back(monkeypatch):
    from nflmodel import wind_live as WL
    def boom():
        raise OSError("disk")
    monkeypatch.setattr(WL, "readings", boom)
    monkeypatch.setattr(WL, "temp_readings", lambda: {})
    monkeypatch.setattr(WL, "rain_readings", lambda: {})
    wind, temp, pop = WX.mos_readings()
    assert wind == {} and any("wind readings failed" in w["message"] for w in warnlog.recent())


def test_opponent_strength_centres_on_weeks_before_only():
    tg = pd.DataFrame({"season": [2023] * 4 + [2024] * 6, "week": [1, 1, 2, 2, 1, 1, 2, 2, 3, 3],
                       "x": [1.0, 3.0, 5.0, 7.0, 10.0, 20.0, 30.0, 40.0, 50.0, 60.0]})
    m = PL.league_mean_before(tg, "x").tolist()
    # 2023 week 1: no season before, 0; week 2: week 1's mean; 2024 week 1: 2023's mean; week 3: weeks 1-2 only
    assert m == [0.0, 0.0, 2.0, 2.0, 4.0, 4.0, 15.0, 15.0, 25.0, 25.0]
    tg2 = tg.copy(); tg2.loc[tg2.week == 3, "x"] += 1000   # a later week never moves an earlier week's centre
    assert PL.league_mean_before(tg2, "x").tolist()[:8] == m[:8]


def _sha(p):
    return hashlib.sha1(p.read_bytes()).hexdigest() if p.exists() else None


def test_read_only_trees_cache_never_writes_and_restores_state(tmp_path, monkeypatch):
    f = tmp_path / "trees_cache.parquet"
    pd.DataFrame({"key": ["k"], "game_id": ["g"], "team": ["T"], "pred": [1.0]}).to_parquet(f, index=False)
    monkeypatch.setattr(M, "TREES_CACHE", f)
    monkeypatch.setitem(M._TC, "df", None); monkeypatch.setitem(M._TC, "used", set()); monkeypatch.setitem(M._TC, "new", [])
    before = _sha(f)
    with M.trees_cache_read_only():
        M._TC["new"].append(pd.DataFrame({"key": ["k2"], "game_id": ["g"], "team": ["T"], "pred": [2.0]}))
        M.save_trees_cache()   # what walk_forward calls at its end
    assert _sha(f) == before and M._TC["new"] == []
    M.save_trees_cache()   # outside the block the real save is back (it drops the unused key, so the file changes)
    assert _sha(f) != before


def test_every_walk_forward_in_the_audit_is_read_only():
    tree = ast.parse((ROOT / "nflmodel" / "audit.py").read_text(encoding="utf-8"))
    guarded = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.With) and any("trees_cache_read_only" in ast.unparse(i.context_expr) for i in node.items):
            guarded |= {id(n) for n in ast.walk(node)}
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and ast.unparse(n.func) == "M.walk_forward"]
    fns = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    inner = {id(x) for x in ast.walk(fns["_decision_confidence"])}   # called only from decision_confidence's with-block
    assert calls and all(id(c) in guarded or id(c) in inner for c in calls)
