"""Tie-breaker for the QB replacement level on the window nobody tuned on (2015 to 2018): team points miss,
spread miss and the flag record at cuts 4 and 5 at the current level and the two candidates.
Output reports/qb_third.csv."""
import os, numpy as np, pandas as pd
from nflmodel import ratings as R, model as M, backtest as B
from nflmodel.features import OUT
tg = pd.read_parquet(OUT / "team_games.parquet"); games = pd.read_parquet(OUT / "games.parquet"); qb = pd.read_parquet(OUT / "qb_games.parquet")
LEVELS = [float(x) for x in os.environ["LEVELS"].split(",")] if os.environ.get("LEVELS") else [-0.05, -0.12, -0.16]
orig = R.QBRatings.__init__; rows = []
for lvl in LEVELS:
    def init(self, q, k, decay, prior_epa=lvl, _o=orig): _o(self, q, k, decay, prior_epa)
    R.QBRatings.__init__ = init
    f = M.with_trends(R.build_features(R.DEFAULT, tg=tg, games=games, qb=qb))
    p3 = M.walk_forward(f, range(2015, 2019)); d = B.join(p3, games)
    d = d[(d.game_type == "REG") & d.season.isin(range(2015, 2019)) & (d.week < 18) & d.spread_line.notna() & d.home_score.notna()]
    pm = B.points_miss(d).set_index("target")
    e = d.model_spread - d.spread_line; res = np.sign(d.home_score - d.away_score - d.spread_line)
    row = {"variant": f"replacement level {lvl:+.2f}", "team_mae": round(float(pm.loc["team points", "model_mae"]), 4), "margin_mae": round(float(pm.loc["margin", "model_mae"]), 4), "n": int(len(d))}
    for cut in [4, 5]:
        m = (np.abs(e) >= cut) & (res != 0); w = int((np.sign(e[m]) == res[m]).sum()); l = int(m.sum() - w)
        row[f"ats{cut}"] = f"{w}-{l}"; row[f"ats{cut}_pct"] = round(w / (w + l), 3) if w + l else None
    rows.append(row); print(row, flush=True)
R.QBRatings.__init__ = orig
pd.DataFrame(rows).to_csv("reports/qb_third.csv", index=False); print("DONE")
