"""The Questionable-in-totals shadow (2 Oct 2026, nflmodel/qtotals.py, hidden shadow shadowqtotals): the live totals
equation is the same with and without it, its chance is model.price_at's at its own total, its rule reads only its own
column, its listings count the way experiments/injury_retest.py counts them, and it never reaches the page or the bets."""
import json

import numpy as np
import pandas as pd
import pytest

from nflmodel import model as M, picks as P, qtotals as QT, standing_checks as SC, export_web as EW


def _team_games(n_games=60, seed=0):
    """A planted league: home and away rows with every column model._game_frame and the shadow's frame read."""
    rng = np.random.default_rng(seed); rows = []
    for i in range(n_games):
        gid = f"2025_{1 + i // 10:02d}_A{i}_H{i}"
        for home in (1, 0):
            rows.append({"game_id": gid, "season": 2025, "week": 1 + i // 10, "home": home, "team": f"{'H' if home else 'A'}{i}",
                         "pf": float(rng.integers(10, 35)), "off_epa_play": rng.normal(), "def_epa_play": rng.normal(), "off_pf": rng.normal(22, 3),
                         "def_pf": rng.normal(22, 3), "qb_rating": rng.normal(), "qb_out": float(rng.random() < 0.05), "qb_form": rng.normal(),
                         "wind_out": rng.uniform(0, 15), "rain": 0.0, "rain_fc": float(rng.random() < 0.1), "cold": float(rng.random() < 0.1),
                         "dome": float(rng.random() < 0.3), "div_game": 0.0, "skill_out_value": rng.uniform(0, 0.3), "off_snap_out": rng.uniform(0, 1),
                         "off_turnover_early": 0.0, "q_skill": rng.uniform(0, 0.1), "q_off": rng.uniform(0, 0.5), "q_def": rng.uniform(0, 0.5),
                         "q_qb": float(rng.random() < 0.05) * 0.3})
    f = pd.DataFrame(rows); f["qb_out_t"] = np.maximum(f.qb_out, f.q_qb)
    return f


def test_live_totals_identical_with_and_without_the_shadow():
    f = _team_games(); train, test = f[f.week <= 5], f[f.week == 6]
    feats0, gf0 = list(M.TOTAL_FEATS), M._game_frame
    live_before = M.total_model(train, test)
    raw, tres = QT.fit_week(train, test)
    live_after = M.total_model(train, test)
    assert np.array_equal(live_before, live_after) and M.TOTAL_FEATS == feats0 and M._game_frame is gf0
    plain = [c for c in f.columns if not c.startswith("q_") and c != "qb_out_t"]
    assert np.array_equal(live_before, M.total_model(train[plain], test[plain]))   # the shadow's columns on the table change nothing live
    assert len(raw) == len(live_before) and len(tres) == train.game_id.nunique() and not np.allclose(raw, live_before)


def test_shadow_inputs_are_the_live_equation_plus_t2():
    cols = QT.feats()
    assert "qb_out_sum" not in cols and "qb_out_t_sum" in cols and cols[-3:] == ["q_skill_sum", "q_off_sum", "q_def_sum"]
    assert [c for c in cols if c not in ("qb_out_t_sum", "q_skill_sum", "q_off_sum", "q_def_sum")] == [c for c in M.TOTAL_FEATS if c != "qb_out_sum"]


def test_chance_is_price_at_on_the_shadow_total():
    rng = np.random.default_rng(3); tres = rng.normal(0, 13, 400).round()
    dist = {"K": np.ones(len(M.MARGIN_RANGE)), "tres": tres, "sigma_margin": 13.0, "sigma_total": 13.0}
    for mt, tl in [(44.3, 45.5), (47.0, 44.0), (40.0, 40.0)]:
        assert QT.p_over_emp(mt, tl, tres) == M.price_at(1.0, mt, -1.0, tl, dist)["p_over_emp"]
    assert np.isnan(QT.p_over_emp(44.0, None, tres))


def _rows(**kw):
    base = {"game_id": ["g1", "g2", "g3", "g4"], "week": [3, 3, 18, 3], "total_line": [44.0, 44.0, 44.0, np.nan],
            "p_over_emp": [0.60, 0.40, 0.40, 0.40], "qt_p_over_emp": [0.40, 0.60, 0.40, 0.40],
            "home_score": [20, 20, 20, 20], "away_score": [20, 30, 20, 20], "home_team": "HOM", "away_team": "AWY"}
    base.update(kw); return pd.DataFrame(base)


def test_rule_reads_only_the_shadow_chance_weeks_1_to_17():
    d = _rows()
    assert list(P.rule_mask(d, P.QT_UNDER["prob"], "qt_under")) == [True, False, False, False]   # the live chance (p_over_emp) plays no part
    assert list(P.rule_mask(d, P.TOTAL_SHADOW["prob"], "under_prob")) == [False, True, False, False]   # the live flag reads its own
    assert P._mask_bets(d, P.QT_UNDER["prob"], "qt_under") == ["Under 44", "", "", ""]
    assert P.record(d, pd.Series([True, True, False, False]), "qt_under") == (1, 1)   # 40 under 44 wins, 50 loses
    assert list(P.rule_mask(d.drop(columns=["qt_p_over_emp"]).assign(qt_p_over_emp=np.nan), 0.55, "qt_under")) == [False] * 4


def test_registered_as_a_hidden_totals_shadow():
    edge, sr, _ = P.SHADOWS["shadowqtotals"]
    assert edge == P.QT_UNDER["prob"] == 0.55 and sr == "qt_under"
    assert "shadowqtotals" in P.HIDDEN_SHADOWS and sr in P.MASK_RULES and sr in P.UNDER_RULES and sr in P.TOTAL_RULES and sr not in P.BLIND_RULES
    assert "shadowqtotals" not in SC.LIVE_BETS
    from nflmodel.clv import RULE_FILES
    assert "shadowqtotals" not in RULE_FILES


def test_listings_count_like_injury_retest():
    inj = pd.DataFrame({"season": 2025, "week": [3, 3, 3, 4, 5], "team": ["PIT", "PIT", "PIT", "PIT", "PIT"], "game_type": "REG",
                        "gsis_id": ["a", "b", "c", "a", "a"], "report_status": ["Questionable", "Questionable", "Questionable", "Questionable", "Questionable"],
                        "position": ["WR", "QB", "T", "WR", "WR"], "practice_status": ["Limited Participation in Practice", "Did Not Participate In Practice", None, "Full", None]})
    sn = pd.DataFrame({"season": 2025, "week": [3, 3], "team": "PIT", "key": ["a", "x"]})
    graded, priced = QT.listings(inj, sn, {(2025, 3, "PIT"): {"c"}}, unplayed={(2025, 5, "PIT")})
    # week 3: a played (snap), b sat, c ruled out elsewhere (dropped); week 4: no snap counts and played, dropped; week 5: unplayed, priced
    assert sorted(zip(graded.week, graded.gsis_id, graded.sat)) == [(3, "a", 0.0), (3, "b", 1.0)]
    assert sorted(zip(priced.week, priced.gsis_id)) == [(3, "a"), (3, "b"), (5, "a")]
    assert list(graded.prac) == ["limited", "dnp"]
    rates = QT.sit_rates(graded.assign(season=2024), [2024, 2025])
    assert set(rates) == {2025} and QT.chance(rates, 2025, "QB", "dnp") == pytest.approx((1 + 20 * 1.0) / (1 + 20))


def test_live_reprices_at_the_live_line_or_blanks(tmp_path, monkeypatch):
    monkeypatch.setattr(QT, "PRED", tmp_path / "qt_pred.parquet"); monkeypatch.setattr(QT, "DIST", tmp_path / "qt_dist.json")
    pd.DataFrame({"game_id": ["g1", "g2"], "season": 2026, "week": 4, "total_line": [44.0, 47.0], "qt_model_total": [42.0, 49.0],
                  "qt_p_over_emp": [0.40, 0.58]}).to_parquet(QT.PRED, index=False)
    p = pd.DataFrame({"game_id": ["g1", "g2"], "total_line": [44.0, 48.0]})
    no_fit = QT.live(p, 2026, 4)   # no stored fit: the stored chance where the line held, blank where it moved
    assert no_fit.qt_p_over_emp.iloc[0] == 0.40 and np.isnan(no_fit.qt_p_over_emp.iloc[1]) and list(no_fit.qt_model_total) == [42.0, 49.0]
    tres = [-10.0, -3.0, 0.0, 4.0, 9.0]
    QT.DIST.write_text(json.dumps({"season": 2026, "weeks": {"4": tres}}))
    fit = QT.live(p, 2026, 4)
    assert list(fit.qt_p_over_emp) == [QT.p_over_emp(42.0, 44.0, tres), QT.p_over_emp(49.0, 48.0, tres)]


def test_cards_drop_the_shadow_columns():
    assert all(k.startswith(EW.QT_KEYS) for k in ("qt_model_total", "qt_p_over_emp", "shadowqtotals_bet"))
    assert not any(k.startswith(EW.QT_KEYS) for k in ("model_total", "p_over_emp", "shadowunder_bet", "windunder_bet"))


def test_standing_check_catches_the_shadow_on_the_page_or_writing_the_live_table():
    lv = lambda rows: [r[0] for r in rows]
    meta = {"pred_v3_sha_before": "abc", "pred_v3_sha_after": "abc"}
    web = {"week.js": "window.WEEK={\"shadowunder_bet\": \"Under 44\"}"}
    cards = [{"game_id": "g1", "model_total": 44.0}]
    assert lv(SC.qt_stays_off("<html></html>", web, cards, meta, "abc")) == ["OK", "OK", "OK"]
    assert lv(SC.qt_stays_off("<html></html>", dict(web, **{"live.js": "qt_p_over_emp"}), cards, meta, "abc"))[0] == "FAIL"
    assert lv(SC.qt_stays_off("g.shadowqtotals_bet", web, cards, meta, "abc"))[0] == "FAIL"
    assert lv(SC.qt_stays_off("", web, [dict(cards[0], qt_model_total=43.0)], meta, "abc"))[0] == "FAIL"
    assert lv(SC.qt_stays_off("", web, cards, dict(meta, pred_v3_sha_after="def"), "def"))[1] == "FAIL"   # the shadow wrote pred_v3
    assert lv(SC.qt_stays_off("", web, cards, meta, "def"))[2] == "WARN"   # the model re-ran without the shadow
    assert lv(SC.qt_stays_off("", web, cards, None, "abc")) == ["OK", "WARN"]


def test_isolation_check_on_the_stored_tables(monkeypatch):
    """standing_checks.qt_isolated on the committed tables: OK as stored, FAIL when the shadow's fit replaces a live object."""
    assert [r[0] for r in SC.qt_isolated()] == ["OK"]
    def leaky(train, test, cols=None):   # a shadow that swaps the live game frame for one that drops the roof
        monkeypatch.setattr(M, "_game_frame", lambda f, _g=M._game_frame: _g(f).assign(dome=0.0))
    monkeypatch.setattr(QT, "fit_week", leaky)
    rows = SC.qt_isolated()
    assert rows[0][0] == "FAIL" and "moved" in rows[0][2] and "replaced" in rows[0][2]
