"""The study gate encodes reports/round3_rule.md (1 Oct 2026): a clean pass, and each part failing on its own."""
import numpy as np

from nflmodel import study_gate as G

MISS = {"2015-18": (10.50, 10.48), "2019-22": (10.40, 10.37), "2023-25": (10.10, 10.06)}
REC = {w: {"totals flag": ((130, 120), (131, 120))} for w in G.WINDOWS}
PLACEBO = {w: np.full(50, 0.001) for w in G.WINDOWS}


def names_failed(rows):
    return [w for w, ok, _ in rows if not ok]


def test_clean_pass():
    rows = G.gate(MISS, REC, PLACEBO)
    assert G.passes(rows) and "Gate: PASS" in G.markdown(rows)


def test_worse_on_one_window_fails():
    m = dict(MISS, **{"2015-18": (10.50, 10.51)})
    assert "better on 2015-18" in names_failed(G.gate(m, REC, PLACEBO))
    assert names_failed(G.gate(m, REC)) == ["better on 2015-18"]


def test_tie_only_allowed_on_the_fit_window():
    m = dict(MISS, **{"2019-22": (10.40, 10.40)})
    assert not G.passes(G.gate(m, REC))
    assert G.passes(G.gate(m, REC, fit_window="2019-22"))


def test_missing_window_fails():
    m = {k: v for k, v in MISS.items() if k != "2023-25"}
    assert "better on 2023-25" in names_failed(G.gate(m))


def test_bet_cost_fails():
    r = dict(REC, **{"2023-25": {"totals flag": ((81, 62), (80, 62))}})
    assert names_failed(G.gate(MISS, r, PLACEBO)) == ["no bet cost: totals flag, 2023-25"]


def test_placebo_needs_45_of_50():
    real = MISS["2019-22"][0] - MISS["2019-22"][1]
    p44 = np.r_[np.full(44, 0.0), np.full(6, real + 1)]; p45 = np.r_[np.full(45, 0.0), np.full(5, real + 1)]
    assert names_failed(G.gate(MISS, REC, dict(PLACEBO, **{"2019-22": p44}))) == ["beats its placebo on 2019-22"]
    assert G.passes(G.gate(MISS, REC, dict(PLACEBO, **{"2019-22": p45})))
    assert not G.passes(G.gate(MISS, REC, dict(PLACEBO, **{"2019-22": np.zeros(20)})))   # too few draws


def test_shuffle_keeps_each_season_s_values():
    v = np.arange(12.0); s = np.repeat([2019, 2020, 2021], 4)
    out = G.shuffle_within_season(v, s, np.random.default_rng(0))
    for y in (2019, 2020, 2021):
        assert sorted(out[s == y]) == sorted(v[s == y])


def test_paperwork_on_a_written_up_study():
    assert G.passes(G.paperwork("rain_points"))
    assert not G.passes(G.paperwork("no_such_study"))
