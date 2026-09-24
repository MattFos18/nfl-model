"""The scheduled paths (24 Sep 2026): the paid pulls ran late or twice when their timing rules broke (props skipped for
11 hours; The Odds API pulled twice near 12:00), and nothing tested them. These pin the rules down."""
import datetime as dt
import pandas as pd
import pytest
from nflmodel import props_lines as P, lines as L

THU = dt.datetime(2026, 9, 24)          # a Thursday


def ts(t: dt.datetime) -> str:
    return t.strftime("%Y-%m-%dT%H-%M-%SZ")


def plog(*rows):
    return pd.DataFrame([{"ts": ts(t), "book": b} for t, b in rows], columns=["ts", "book"])


@pytest.fixture(autouse=True)
def no_state(tmp_path, monkeypatch):
    monkeypatch.setattr(P, "STATE", tmp_path / "pull_state.json")


def test_anchors():
    assert P.last_anchor(THU.replace(hour=20, minute=30), P.PROP_ANCHORS) == (THU.replace(hour=20), 30.0)
    assert P.last_anchor(THU.replace(hour=19), P.PROP_ANCHORS)[0] == dt.datetime(2026, 9, 20, 14)   # Sunday before
    assert P.next_anchor(THU.replace(hour=20, minute=5), P.PROP_ANCHORS) == dt.datetime(2026, 9, 27, 14)
    assert P.last_anchor(THU.replace(hour=11), [(None, 12, 0.0)])[0] == dt.datetime(2026, 9, 23, 12)


def test_props_due_first_run_after_anchor():
    now = THU.replace(hour=20, minute=40)
    assert P.due(now, plog()) == 30.0
    assert P.due(now, plog((dt.datetime(2026, 9, 21, 14, 5), "fanduel"))) == 30.0      # last pull was Sunday's


def test_props_not_twice():
    now = THU.replace(hour=21)
    assert P.due(now, plog((THU.replace(hour=20, minute=10), "fanduel"))) is None       # pulled since the anchor
    assert P.due(now, plog((THU.replace(hour=16), "fanduel"))) is None                  # inside six hours
    P.mark("props", THU.replace(hour=20, minute=20))
    assert P.due(now, plog()) is None                                                  # a failed attempt counts


def test_props_pickem_rows_do_not_block():
    now = THU.replace(hour=20, minute=40)
    assert P.due(now, plog((THU.replace(hour=20, minute=30), "prizepicks"), (THU.replace(hour=20, minute=30), "underdog"))) == 30.0


def test_props_gives_up_after_a_day():
    assert P.due(dt.datetime(2026, 9, 25, 21), plog()) is None


def test_pickem_every_six_hours():
    lg = plog((THU.replace(hour=6), "prizepicks"))
    assert not P.dfs_due(THU.replace(hour=11, minute=59), False, lg)
    assert P.dfs_due(THU.replace(hour=12), False, lg)
    assert P.dfs_due(THU.replace(hour=7), True, lg)
    assert P.dfs_due(THU, False, plog())


def glog(*times):
    return pd.DataFrame([{"ts": ts(t), "source": "oddsapi:draftkings"} for t in times], columns=["ts", "source"])


@pytest.mark.parametrize("pulls,now,want", [
    ([], THU.replace(hour=12, minute=20), True),                                                    # first run after 12:00
    ([THU.replace(hour=12, minute=5)], THU.replace(hour=13), False),                                # pulled today
    ([THU.replace(hour=11, minute=40)], THU.replace(hour=12, minute=10), False),                     # a catch-up pull just before
    ([dt.datetime(2026, 9, 23, 12, 5)], THU.replace(hour=12, minute=30), True),                     # yesterday's
    ([dt.datetime(2026, 9, 23, 12, 5)], THU.replace(hour=11, minute=50), False),                    # not yet 12:00
])
def test_odds_api_once_a_day(monkeypatch, pulls, now, want):
    monkeypatch.setattr(L, "load_log", lambda: glog(*pulls))
    assert L.odds_api_due(now) is want


def test_book_names_resolve():
    canon = {"exact": {"joshua palmer": "joshua palmer", "josh palmer": "joshua palmer", "marquise brown": "marquise brown", "amon-ra st. brown": "amon-ra st. brown"},
             "last": {"palmer": "joshua palmer"}}
    canon["exact"] = {P.norm_name(k): v for k, v in canon["exact"].items()}
    assert P.resolve_name("Josh Palmer", canon) == "joshua palmer"
    assert P.resolve_name("Hollywood Brown", canon) == "marquise brown"
    assert P.resolve_name("Palmer Joshua", canon) == "joshua palmer"
    assert P.resolve_name("Unknown Player", canon) == P.norm_name("Unknown Player")


def test_closing_has_every_column_the_cards_read(monkeypatch):
    """props.attach_all_markets and reattach_markets read these columns (24 Sep 2026: pulls went missing and the
    line watch failed for hours)."""
    monkeypatch.setattr(P, "roster_keys", lambda season, teams: {"exact": {}, "last": {}})
    lg = pd.DataFrame([{"game_id": "g1", "season": 2026, "home": "BUF", "away": "MIA", "ts": ts(THU.replace(hour=h)), "book": b, "stat": "rec_yards", "player": "Tyreek Hill", "line": ln, "over_price": -110, "under_price": -110}
                       for h, b, ln in [(10, "fanduel", 70.5), (12, "fanduel", 72.5), (12, "draftkings", 71.5)]])
    out = P.closing(lg, "g1")
    need = {"stat", "player", "key", "line", "books", "over_price", "under_price", "open_line", "open_over", "ts", "open_ts", "pulls"}
    assert need <= set(out.columns) and need <= set(P.closing(lg, "none").columns)
    r = out.iloc[0]
    assert (r.line, r.books, r.open_line, r.pulls) == (72.0, 2, 71.0, 2)   # open: the median of each book's first line
