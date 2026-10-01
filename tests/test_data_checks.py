"""The data checks pass on the stored tables and catch each planted error (1 Oct 2026)."""
from pathlib import Path

import pandas as pd
import pytest

from nflmodel import data_checks as DC

OUT = Path(__file__).resolve().parent.parent / "data" / "processed"
pytestmark = pytest.mark.skipif(not (OUT / "games.parquet").exists(), reason="processed tables not present")


@pytest.fixture(scope="module")
def tables():
    return pd.read_parquet(OUT / "games.parquet"), pd.read_parquet(OUT / "team_games.parquet"), pd.read_parquet(OUT / "pred_v3.parquet")


def failed(rows):
    return [w for w, ok, _ in rows if not ok]


def test_stored_tables_pass(tables):
    assert failed(DC.check(*tables)) == []


def test_planted_errors_are_caught(tables):
    g, tg, p = tables
    played = g[(g.game_type == "REG") & (g.season == 2024)].index
    plants = {
        "games: one row per game": (pd.concat([g, g.loc[played[:1]]]), tg, p),
        "games: every team's full regular season (finished seasons)": (g.drop(played[:1]), tg, p),
        "games: result and total add up from the scores": (g.assign(result=g.result.where(g.index != played[0], 99)), tg, p),
        "team games: each side's points mirror the other's": (g, tg.assign(pf=tg.pf.where(tg.index != tg[tg.season == 2024].index[0], 0)), p),
        "predictions: every played regular-season game priced": (g, tg, p[p.game_id != g.loc[played[0], "game_id"]]),
    }
    for check, args in plants.items():
        assert check in failed(DC.check(*args)), check
