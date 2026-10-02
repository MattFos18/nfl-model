"""Without the stored fit, the chances of a game whose live line moved are cleared, so no chance-based rule fires on a
number the chance was not priced at (2 Oct 2026, overs study review)."""
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from nflmodel import model as M, picks as P, lines as LN

OUT = Path(__file__).resolve().parent.parent / "data" / "processed"
pytestmark = pytest.mark.skipif(not (OUT / "pred_v3.parquet").exists(), reason="processed tables not present")


def test_missing_fit_clears_chances_where_the_line_moved(monkeypatch):
    g = pd.read_parquet(OUT / "games.parquet")
    season, week = LN.current_week(g)
    monkeypatch.setattr(M, "load_dist", lambda s, w, path=None: None)
    real = LN.live_lines
    def moved_lines(games_, log):   # every live total 3 points off the schedule's, so every game's line has moved
        out = real(games_, log).copy(); out["total_line"] = out["total_line"] + 3.0; return out
    monkeypatch.setattr(LN, "live_lines", moved_lines)
    t = P.table(season, week)
    sched = g.set_index("game_id")
    moved = t.total_line.ne(t.game_id.map(sched.total_line)) & t.total_line.notna()
    assert moved.any() and t.loc[moved, "p_over_emp"].isna().all()
    assert not t.priced_live.any()
    if "shadowunder_bet" in t:
        assert (t.loc[moved, "shadowunder_bet"].fillna("") == "").all()
