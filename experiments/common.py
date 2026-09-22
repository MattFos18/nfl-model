"""Shared scoring for the experiments: both windows, weekly refit, the model's own ridge alpha."""
import numpy as np, pandas as pd
from nflmodel import model as M, backtest as B
from nflmodel.model import OUT
WINDOWS = {"2019-22": range(2019, 2023), "2023-25": range(2023, 2026)}
GAMES = pd.read_parquet(OUT / "games.parquet")


def score(pred: pd.DataFrame, seasons) -> dict:
    d = B.join(pred, GAMES)
    d = d[(d.game_type == "REG") & d.season.isin(seasons)]
    pm = B.points_miss(d).set_index("target")
    sp = B.summarize_bets(B.grade_spread(d, 5.0)).iloc[0]
    sp4 = B.summarize_bets(B.grade_spread(d, 4.0)).iloc[0]
    return {"team_mae": round(float(pm.loc["team points", "model_mae"]), 4), "margin_mae": round(float(pm.loc["margin", "model_mae"]), 4),
            "total_mae": round(float(pm.loc["total", "model_mae"]), 4), "ats5": f"{int(sp.wins)}-{int(sp.losses)}", "ats5_pct": round(float(sp.win_pct), 3),
            "ats4": f"{int(sp4.wins)}-{int(sp4.losses)}", "n": int(len(d))}


def both(f: pd.DataFrame, alpha=10.0, refit="week") -> dict:
    out = {}
    for name, seasons in WINDOWS.items():
        out[name] = score(M.walk_forward(f, seasons, alpha, refit=refit), seasons)
    return out
