"""A third window nobody tuned on: 2015 to 2018. Every input and knob was chosen on 2019 to 2022 and checked on
2023 to 2025; the older seasons were never looked at. If today's model (eighteen inputs, decay 0.94, last season
0.8) also beats the original (thirteen inputs, 0.90, 0.5) there, the gains are real and not window-fitting.
Output reports/third_window.csv."""
import pandas as pd
from nflmodel import ratings as R, model as M, backtest as B
from nflmodel.model import OUT
tg = pd.read_parquet(OUT / "team_games.parquet"); games = pd.read_parquet(OUT / "games.parquet"); qb = pd.read_parquet(OUT / "qb_games.parquet")
def score(pred, seasons):
    d = B.join(pred, games); d = d[(d.game_type == "REG") & d.season.isin(seasons)]
    pm = B.points_miss(d).set_index("target"); sp = B.summarize_bets(B.grade_spread(d, 5.0)).iloc[0]
    return {"team_mae": round(float(pm.loc["team points", "model_mae"]), 4), "margin_mae": round(float(pm.loc["margin", "model_mae"]), 4), "vegas_margin": round(float(pm.loc["margin", "vegas_mae"]), 4) if "vegas_mae" in pm.columns else None,
            "ats5": f"{int(sp.wins)}-{int(sp.losses)}", "n": int(len(d))}
FULL = M.FEATS.copy(); THIRTEEN = [f for f in FULL if f not in ("div_game",) + tuple(M.INJ_FEATS)]
rows = []
for kname, knobs in [("knobs 0.94 / 0.8 (today)", {}), ("knobs 0.90 / 0.5 (original)", {"decay": 0.90, "prior": 0.5})]:
    f = M.with_trends(R.build_features({**R.DEFAULT, **knobs}, tg=tg, games=games, qb=qb))
    for iname, feats in [("twenty inputs (today)", FULL), ("13 inputs (before the player model)", THIRTEEN)]:
        M.FEATS = feats
        r = score(M.walk_forward(f, range(2015, 2019)), range(2015, 2019)); M.FEATS = FULL
        rows.append({"variant": f"{iname}, {kname}", **r}); print(rows[-1], flush=True)
pd.DataFrame(rows).to_csv("reports/third_window.csv", index=False); print("DONE")
