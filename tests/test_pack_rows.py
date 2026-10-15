"""export_web.pack_rows and tie_check._unpack (15 Oct 2026): repeated text columns are stored once and come back unchanged."""
from nflmodel import export_web as E, tie_check as T


def test_pack_then_unpack_round_trips_and_shrinks():
    rows = [{"game": f"g{i % 3}", "n": i, "who": "a" if i % 2 else "b", "u": f"x{i}"} for i in range(40)]
    p = E.pack_rows({"graded": rows, "other": [1, 2]})
    assert set(p["graded"]["dict"]) == {"game", "who"}     # repeats go to the dictionary; unique text and numbers stay
    assert T._unpack(p) == {"graded": rows, "other": [1, 2]}


def test_small_or_unique_tables_are_not_encoded():
    rows = [{"a": "x", "b": 1}, {"a": "y", "b": 2}]
    assert "dict" not in E.pack_rows({"t": rows})["t"]


def test_snap_name_fallback_ignores_generational_suffixes():
    from nflmodel.ids import name_key
    assert name_key("James Thompson") == name_key("James Thompson Jr.") == "jamesthompson"
    assert name_key("Vic Beasley") == "vicbeasley"   # a v inside a name stays


def test_map_pfr_tries_exact_name_before_the_suffix_free_one(monkeypatch):
    import pandas as pd
    from nflmodel import ids
    monkeypatch.setattr(ids, "pfr_ids", lambda: {"nobody": "Q"})   # a non-empty map keeps the result column text
    monkeypatch.setattr(ids, "roster_name_ids", lambda: {(2026, "SF", "jamesthompson"): "A", (2026, "SF", "~jamesthompson"): "A",
                                                          (2026, "SF", "marvinharrison"): "B", (2026, "SF", "marvinharrisonjr"): "C", (2026, "SF", "~marvinharrison"): None})
    df = pd.DataFrame({"pfr_player_id": ["x", "y", "z"], "player": ["James Thompson Jr.", "Marvin Harrison", "Marvin Harrison Jr."], "team": "SF", "season": 2026})
    assert list(ids.map_pfr(df)) == ["A", "B", "C"]
