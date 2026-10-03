"""The seven inputs dropped on 3 Oct 2026 (reports/drop_seven_inputs.md) stay out of the equations; the readings stay computed."""
from nflmodel import model as M, qtotals as QT

DROPPED_POINTS = {"neutral", "dome", "rain", "div_game", "qb_out"}
DROPPED_TOTAL = {"pf_sum", "qb_out_sum"}


def test_inputs_dropped():
    assert len(M.FEATS) == 17 and not DROPPED_POINTS & set(M.FEATS)
    assert len(M.TOTAL_FEATS) == 9 and not DROPPED_TOTAL & set(M.TOTAL_FEATS)
    assert "dome" in M.TOTAL_FEATS and "rain_fc" in M.TOTAL_FEATS   # the roof and the forecast rain stay in the total


def test_shadow_keeps_its_qb_term():
    cols = QT.feats()
    assert "qb_out_t_sum" in cols and "pf_sum" not in cols and "qb_out_sum" not in cols
