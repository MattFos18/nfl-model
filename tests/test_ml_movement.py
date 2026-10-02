"""Moneyline movement on the cards (2 Oct 2026, Matt: "track moneyline movement like we do for the total and the
spread"): each consensus point carries the home side's no-vig win chance, and a reverse move needs the chance to move
ML_MOVE_PTS points from the open toward the side with fewer moneyline bets. Display only."""
import pandas as pd
import pytest

from nflmodel import export_web as E

GID = "2026_04_PIT_CLE"
BOOK_COLS = ["ts", "game_id", "book", "home_spread", "total", "home_ml", "away_ml", "book_updated"]


def _write(tmp_path, books, ml_bets):
    d = tmp_path / "data" / "lines"; d.mkdir(parents=True)
    pd.DataFrame(books, columns=BOOK_COLS).to_csv(d / "books_log.csv", index=False)
    a, h = ml_bets   # PIT (away), CLE (home) share of moneyline bets
    pd.DataFrame([{"ts": "2026-10-01T12-00-00Z", "game_id": GID, "market": "ml", "away": "PIT", "home": "CLE", "line_a": None, "line_b": None,
                   "bets_a": a, "bets_b": h, "money_a": 50, "money_b": 50}]).to_csv(d / "splits_consensus_log.csv", index=False)


def _card(tmp_path, monkeypatch, books, ml_bets=(79, 21)):
    _write(tmp_path, books, ml_bets)
    monkeypatch.setattr(E, "ROOT", tmp_path)
    wk = [{"game_id": GID, "home_team": "CLE", "away_team": "PIT"}]
    E._add_consensus(wk)
    return wk[0]


def _books(open_ml, now_ml):
    return [["2026-09-29T10-00-00Z", GID, "Open", 2.5, 38.5, open_ml[0], open_ml[1], "2026-09-28T10:00:00+00:00"],
            ["2026-09-30T10-00-00Z", GID, "Consensus", 2.5, 38.5, open_ml[0], open_ml[1], "2026-09-30T10:00:00+00:00"],
            ["2026-10-01T10-00-00Z", GID, "Consensus", 2.5, 38.5, now_ml[0], now_ml[1], "2026-10-01T10:00:00+00:00"]]


def test_novig_home():
    assert E._novig_home(-110, -110) == 50.0
    assert E._novig_home(124, -149) == pytest.approx(42.7, abs=0.1)
    assert E._novig_home(None, -149) is None


def test_every_point_carries_the_home_win_chance_from_open_to_now(tmp_path, monkeypatch):
    g = _card(tmp_path, monkeypatch, _books((124, -149), (150, -180)))
    h = g["consensus_history"]
    assert h[0]["source"] == "Open" and (h[0]["home_ml"], h[0]["away_ml"]) == (124, -149)
    assert [p["home_win"] for p in h] == [E._novig_home(p["home_ml"], p["away_ml"]) for p in h]
    assert h[-1]["home_win"] == E._novig_home(150, -180)


def test_ml_reverse_move_toward_the_side_with_fewer_bets(tmp_path, monkeypatch):
    # 79% of moneyline bets on PIT, but CLE's chance rose from about 38% to 43%: a reverse move toward CLE
    g = _card(tmp_path, monkeypatch, _books((150, -180), (124, -149)))
    m = [x for x in g["moves"] if x["market"] == "ml"]
    assert len(m) == 1
    m = m[0]
    assert (m["toward"], m["public"], m["bets"]) == ("CLE", "PIT", 79)
    assert m["open"] == E._novig_home(150, -180) and m["now"] == E._novig_home(124, -149)
    assert (m["open_ml"], m["now_ml"]) == (150, 124)


def test_ml_move_reads_the_away_side_when_it_moves_toward_the_away_team(tmp_path, monkeypatch):
    g = _card(tmp_path, monkeypatch, _books((124, -149), (150, -180)), ml_bets=(21, 79))
    m = [x for x in g["moves"] if x["market"] == "ml"][0]
    assert (m["toward"], m["public"]) == ("PIT", "CLE")
    assert m["open"] == round(100 - E._novig_home(124, -149), 1) and (m["open_ml"], m["now_ml"]) == (-149, -180)


def test_no_ml_move_toward_the_public_side(tmp_path, monkeypatch):
    # the move is toward PIT, where the bets are: not a reverse move
    g = _card(tmp_path, monkeypatch, _books((124, -149), (150, -180)), ml_bets=(79, 21))
    assert not [x for x in g["moves"] if x["market"] == "ml"]


def test_no_ml_move_under_the_threshold(tmp_path, monkeypatch):
    # -149 to -155 is under ML_MOVE_PTS
    g = _card(tmp_path, monkeypatch, _books((124, -149), (128, -155)), ml_bets=(21, 79))
    o, n = g["consensus_history"][0]["home_win"], g["consensus_history"][-1]["home_win"]
    assert abs(n - o) < E.ML_MOVE_PTS
    assert not [x for x in g["moves"] if x["market"] == "ml"]


def test_impossible_prices_give_no_chance():
    assert E._novig_home(0, -150) is None and E._novig_home(-150, 50) is None


def test_open_without_ml_starts_at_the_first_consensus_moneyline(tmp_path, monkeypatch):
    b = _books((124, -149), (150, -180)); b[0][5] = b[0][6] = None
    g = _card(tmp_path, monkeypatch, b, ml_bets=(21, 79))
    h = g["consensus_history"]
    assert h[0]["source"] == "Open" and h[0]["home_win"] is None
    m = [x for x in g["moves"] if x["market"] == "ml"][0]
    assert (m["open_ml"], m["now_ml"]) == (-149, -180)   # the first consensus moneyline, not the empty open


def test_newest_without_ml_reads_the_last_point_that_has_one(tmp_path, monkeypatch):
    b = _books((124, -149), (150, -180)) + [["2026-10-01T12-00-00Z", GID, "Consensus", 2.5, 38.5, None, None, "2026-10-01T12:00:00+00:00"]]
    g = _card(tmp_path, monkeypatch, b, ml_bets=(21, 79))
    m = [x for x in g["moves"] if x["market"] == "ml"][0]
    assert m["now_ml"] == -180


def test_no_ml_move_at_even_bets(tmp_path, monkeypatch):
    g = _card(tmp_path, monkeypatch, _books((124, -149), (150, -180)), ml_bets=(50, 50))
    assert not [x for x in g["moves"] if x["market"] == "ml"]


def test_tie_check_ml_chart_ends(tmp_path, monkeypatch):
    from nflmodel import tie_check as T
    b = _books((124, -149), (150, -180))
    g = _card(tmp_path, monkeypatch, b)
    books = pd.DataFrame(b, columns=BOOK_COLS)
    have, want = T.ml_chart_ends([g], books)
    assert have == want == {GID: [124, -149, E._novig_home(124, -149), 150, -180, E._novig_home(150, -180)]}
    # a chart that goes missing, or ends on a different price, fails the tie
    have, want = T.ml_chart_ends([dict(g, consensus_history=[])], books)
    assert have != want
    h = [dict(p) for p in g["consensus_history"]]; h[-1].update(home_ml=200, home_win=E._novig_home(200, h[-1]["away_ml"]))
    have, want = T.ml_chart_ends([dict(g, consensus_history=h)], books)
    assert have != want
