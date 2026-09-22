"""Tune the rating parameters and ridge strength on 2019 to 2022 only, then ablate features.

Judged on team points MAE (the plan's number one goal), with margin MAE and ATS record at 3 points shown
alongside. 2023 to 2025 is never touched here; the chosen settings are locked and reported in the backtest.

Usage: python -m nflmodel.tune [--grid] [--ablation] [--out reports/tuning.csv]
"""
from __future__ import annotations
import argparse, itertools, json, time
import numpy as np, pandas as pd
from pathlib import Path
from . import ratings, model, backtest

ROOT = Path(__file__).resolve().parent.parent
OUT, REP = ROOT / "data" / "processed", ROOT / "reports"
TUNE_SEASONS = range(2019, 2023)


def score(pred: pd.DataFrame, games: pd.DataFrame) -> dict:
    d = backtest.join(pred, games)
    d = d[(d.game_type == "REG") & d.season.isin(TUNE_SEASONS)]
    pm = backtest.points_miss(d).set_index("target")
    sp = backtest.summarize_bets(backtest.grade_spread(d, 5.0)).iloc[0]
    to = backtest.summarize_bets(backtest.grade_total(d, 4.0)).iloc[0]
    br = backtest.brier(d)
    return {"team_mae": pm.loc["team points", "model_mae"], "margin_mae": pm.loc["margin", "model_mae"],
            "total_mae": pm.loc["total", "model_mae"], "ats_bets": sp.bets, "ats_pct": sp.win_pct, "ats_roi": sp.roi,
            "ou_bets": to.bets, "ou_pct": to.win_pct, "ou_roi": to.roi, "brier": br["brier_model"], "n": len(d)}


def grid(out: Path):
    tg = pd.read_parquet(OUT / "team_games.parquet")
    games = pd.read_parquet(OUT / "games.parquet")
    qb = pd.read_parquet(OUT / "qb_games.parquet")
    rows = []
    combos = list(itertools.product([0.93, 0.96, 0.99], [0.3, 0.5, 0.8], [2.0, 4.0, 8.0]))
    combos += list(itertools.product([0.85, 0.90], [0.5], [8.0, 16.0, 32.0])) + [(0.93, 0.5, 16.0), (0.93, 0.5, 32.0)]
    if out.exists():
        done = pd.read_csv(out)
        rows = done.to_dict("records")
        combos = [c for c in combos if not ((done.decay == c[0]) & (done.prior == c[1]) & (done.alpha == c[2])).any()]
    for decay, prior, alpha in combos:
        p = {**ratings.DEFAULT, "decay": decay, "prior": prior, "alpha": alpha}
        t0 = time.time()
        f = ratings.build_features(p, seasons=range(2013, 2023), tg=tg, games=games, qb=qb)
        for ridge in [1.0, 3.0, 10.0]:
            pred = model.walk_forward(f, TUNE_SEASONS, ridge)
            r = {"decay": decay, "prior": prior, "alpha": alpha, "ridge": ridge, **score(pred, games)}
            rows.append(r)
            print(json.dumps({k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()}), flush=True)
        pd.DataFrame(rows).to_csv(out, index=False)
        print(f"  {time.time() - t0:.0f}s", flush=True)
    return pd.DataFrame(rows)


GROUPS = {
    "qb_rating": ["qb_rating", "opp_qb_rating"],
    "points ratings": ["off_pf", "def_pf"],
    "epa ratings": ["off_epa_play", "def_epa_play", "opp_off_epa_play", "own_def_epa_play"],
    "pass/rush split": ["off_pass_epa", "def_pass_epa", "off_rush_epa", "def_rush_epa"],
    "success rate": ["off_success", "def_success"],
    "pace": ["off_plays", "def_plays", "opp_off_plays"],
    "rest": ["rest_short", "rest_long", "opp_rest_short", "opp_rest_long"],
    "weather/dome": ["dome", "wind_out", "cold"],
    "division/primetime": ["div_game", "primetime"],
    "home": ["home", "neutral"],
}


def ablation(features_path: Path, ridge: float, out: Path):
    f = model.with_trends(pd.read_parquet(features_path))
    games = pd.read_parquet(OUT / "games.parquet")
    full = model.FEATS.copy()
    rows = []
    base = score(model.walk_forward(f, TUNE_SEASONS, ridge), games)
    rows.append({"dropped": "(none)", **base})
    print("full", round(base["team_mae"], 4), flush=True)
    for name, cols in GROUPS.items():
        if not any(c in model.FEATS for c in cols):
            continue
        model.FEATS = [c for c in full if c not in cols]
        r = score(model.walk_forward(f, TUNE_SEASONS, ridge), games)
        rows.append({"dropped": name, **r})
        print(name, round(r["team_mae"], 4), round(r["team_mae"] - base["team_mae"], 4), flush=True)
    model.FEATS = full
    df = pd.DataFrame(rows)
    df["delta_team_mae"] = df.team_mae - base["team_mae"]
    df.to_csv(out, index=False)
    return df


ADDITIONS = {
    "team home edge": ["home_edge_in_play"],
    "head-to-head": ["h2h_cover"],
    "coach ATS": ["coach_ats"],
    "QB ATS": ["qb_ats"],
    "off a loss": ["off_loss"],
    "referee over/under": ["ref_over"],
    "referee home cover": ["ref_home_cover"],
    "referee penalties": ["ref_pen"],
    "late slot / body clock": ["sun_late", "body_clock_early"],
    "cold and wind team edges": ["cold_edge", "wind_edge"],
    "home/away EPA split": ["off_home_split"],
    "injuries: starters out": ["off_starters_out", "def_starters_out"],
    "primetime": ["primetime"],
    "division game": ["div_game"],
    "rest: short week and bye (both teams)": ["rest_short", "rest_long", "opp_rest_short", "opp_rest_long"],
    "snow": ["snow"],
    "travel distance (miles)": ["travel_miles"],
    "time-zone shift (hours)": ["tz_shift"],
    "West Coast team at 1pm ET": ["body_clock_early"],
    "pass/rush EPA split": ["off_pass_epa", "def_pass_epa", "off_rush_epa", "def_rush_epa"],
    "pace (plays per game)": ["off_plays", "def_plays"],
    "opponent QB and other side of the ball": ["opp_qb_rating", "opp_off_epa_play", "own_def_epa_play"],
}


def additions(features_path: Path, ridge: float, out: Path, test_seasons=None):
    """Add each candidate group to the locked model, one at a time; keep what lowers the tuning-window miss."""
    f = model.with_trends(pd.read_parquet(features_path))
    games = pd.read_parquet(OUT / "games.parquet")
    base_feats = model.FEATS.copy()
    rows = []
    base = score(model.walk_forward(f, TUNE_SEASONS, ridge), games)
    rows.append({"added": "(none)", **base})
    print("base", round(base["team_mae"], 4), flush=True)
    for name, cols in ADDITIONS.items():
        model.FEATS = base_feats + cols
        r = score(model.walk_forward(f, TUNE_SEASONS, ridge), games)
        rows.append({"added": name, **r})
        print(name, round(r["team_mae"], 4), round(r["team_mae"] - base["team_mae"], 4), "ats5", round(r["ats_pct"], 3), flush=True)
    model.FEATS = base_feats
    df = pd.DataFrame(rows)
    df["delta_team_mae"] = df.team_mae - base["team_mae"]
    df.to_csv(out, index=False)
    return df


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--grid", action="store_true")
    ap.add_argument("--ablation", action="store_true")
    ap.add_argument("--additions", action="store_true")
    ap.add_argument("--features", default=str(OUT / "features_asof.parquet"))
    ap.add_argument("--ridge", type=float, default=3.0)
    a = ap.parse_args()
    REP.mkdir(exist_ok=True)
    if a.grid:
        grid(REP / "tuning_ratings.csv")
    if a.ablation:
        ablation(Path(a.features), a.ridge, REP / "ablation.csv")
    if a.additions:
        additions(Path(a.features), a.ridge, REP / "additions.csv")
