"""An ESPN Out or Doubtful overrides an older league Questionable, never the other way (3 Oct 2026: Keenan Allen and
Terry McLaurin were Questionable on the Friday report, Out / Doubtful on ESPN on Saturday, and were not counted)."""
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "nflmodel" / "players.py"


def test_downgrade_rule_is_in_the_merge():
    s = SRC.read_text(encoding="utf-8")
    assert 'ESPN_STATUS.get(st) in ("Out", "Doubtful") and off_st.get((t, g)) not in ("Out", "Doubtful")' in s
    assert "(t, g) not in official or worse(t, g, st)" in s


def test_worse_only_moves_toward_out():
    ESPN_STATUS = {"Out": "Out", "Doubtful": "Doubtful", "Questionable": "Questionable"}
    off_st = {("IND", "a"): "Questionable", ("WAS", "b"): "Out", ("KC", "c"): ""}
    worse = lambda t, g, st: ESPN_STATUS.get(st) in ("Out", "Doubtful") and off_st.get((t, g)) not in ("Out", "Doubtful")
    assert worse("IND", "a", "Out")            # league Questionable, ESPN Out: ESPN wins
    assert not worse("WAS", "b", "Questionable")  # league Out, ESPN Questionable: league wins
    assert not worse("IND", "a", "Questionable")  # same status: nothing to change
    assert worse("KC", "c", "Doubtful")        # no league game status: ESPN fills
