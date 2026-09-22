"""Totals, the weakest market: candidate inputs for the totals equation on both windows. The rating gap (a mismatch
runs short: fewer possessions for the leader), the market total itself (the equation learns how far to trust the
model against the line), pace, and both. Output reports/totals_inputs.csv."""
import numpy as np, pandas as pd
from nflmodel import model as M
from nflmodel.model import OUT
from experiments.common import both
f = M.with_trends(pd.read_parquet(OUT / "features_asof.parquet"))
orig = M._game_frame
def frame(df):
    g = orig(df)
    h = df[df.home == 1].set_index("game_id"); a = df[df.home == 0].set_index("game_id"); ids = g.index
    g["gap"] = np.abs((h.loc[ids, "off_epa_play"] + h.loc[ids, "def_epa_play"]) - (a.loc[ids, "off_epa_play"] + a.loc[ids, "def_epa_play"])).values
    g["market_total"] = h.loc[ids, "total_line"].fillna(h.loc[ids, "total_line"].median()).values
    g["pace"] = (h.loc[ids, "off_plays"] + a.loc[ids, "off_plays"]).values if "off_plays" in df.columns else 0.0
    return g
M._game_frame = frame
B = M.TOTAL_FEATS.copy(); rows = []
for name, tf in {"current": B, "+ rating gap": B + ["gap"], "+ market total": B + ["market_total"], "+ pace": B + ["pace"], "+ gap + market total": B + ["gap", "market_total"], "+ gap + market + pace": B + ["gap", "market_total", "pace"]}.items():
    M.TOTAL_FEATS = tf; r = both(f); M.TOTAL_FEATS = B
    rows.append({"variant": name, **{f"{k}_{w}": v for w, d in r.items() for k, v in d.items()}}); print(name, {w: r[w]["total_mae"] for w in r}, flush=True)
pd.DataFrame(rows).to_csv("reports/totals_inputs.csv", index=False); print("DONE")
