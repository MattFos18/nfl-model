"""Totals equation with the offseason-turnover inputs (both teams' offensive and defensive turnover, early season). Both windows. Output reports/totals_turnover.csv."""
import pandas as pd
from nflmodel import model as M
from nflmodel.model import OUT
from experiments.common import both
f = M.with_trends(pd.read_parquet(OUT / "features_asof.parquet"))
orig = M._game_frame
def frame(df):
    g = orig(df); h = df[df.home == 1].set_index("game_id"); a = df[df.home == 0].set_index("game_id"); ids = g.index
    g["turnover_sum"] = (h.loc[ids, "off_turnover_early"] + a.loc[ids, "off_turnover_early"] + h.loc[ids, "opp_def_turnover_early"] + a.loc[ids, "opp_def_turnover_early"]).values
    return g
M._game_frame = frame
B = M.TOTAL_FEATS.copy(); rows = []
for name, tf in {"current": B, "+ turnover (both teams, both sides)": B + ["turnover_sum"]}.items():
    M.TOTAL_FEATS = tf; r = both(f); M.TOTAL_FEATS = B
    rows.append({"variant": name, **{f"{k}_{w}": v for w, d in r.items() for k, v in d.items()}}); print(name, {w: r[w]["total_mae"] for w in r}, flush=True)
pd.DataFrame(rows).to_csv("reports/totals_turnover.csv", index=False); print("DONE")
