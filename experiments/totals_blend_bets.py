"""Does a totals equation that also sees the market total leave anything to bet? Walk-forward both windows with the
market total as an input, then over/under records at small cuts on the residual edge. Output reports/totals_blend_bets.csv."""
import numpy as np, pandas as pd
from nflmodel import model as M, backtest as B
from nflmodel.model import OUT
f = M.with_trends(pd.read_parquet(OUT / "features_asof.parquet")); games = pd.read_parquet(OUT / "games.parquet")
orig = M._game_frame
def frame(df):
    g = orig(df); h = df[df.home == 1].set_index("game_id"); ids = g.index
    g["market_total"] = h.loc[ids, "total_line"].fillna(h.loc[ids, "total_line"].median()).values; return g
M._game_frame = frame; M.TOTAL_FEATS = M.TOTAL_FEATS + ["market_total"]
rows = []
for win, seasons in {"2019-22": range(2019, 2023), "2023-25": range(2023, 2026)}.items():
    p = M.walk_forward(f, seasons); d = B.join(p, games); d = d[(d.game_type == "REG") & d.home_score.notna() & d.total_line.notna()]
    e = d.model_total - d.total_line; res = np.sign(d.home_score + d.away_score - d.total_line)
    for cut in [0.5, 1, 1.5, 2, 3]:
        m = (np.abs(e) >= cut) & (res != 0); w = int((np.sign(e[m]) == res[m]).sum()); l = int(m.sum() - w)
        rows.append({"window": win, "cut": cut, "wins": w, "losses": l, "pct": round(w / (w + l), 3) if w + l else np.nan, "total_mae": round(float(np.abs(e).mean()), 3)})
        print(win, cut, w, l, flush=True)
pd.DataFrame(rows).to_csv("reports/totals_blend_bets.csv", index=False); print("DONE")
