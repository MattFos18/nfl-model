"""Totals equation: does the division flag or the skill value lost belong in it? Both windows. Output reports/totals_div.csv."""
import pandas as pd
from nflmodel import model as M
from nflmodel.model import OUT
from experiments.common import both
f = M.with_trends(pd.read_parquet(OUT / "features_asof.parquet"))
B = M.TOTAL_FEATS.copy(); rows = []
for name, tf in {"current": B, "+ division": B + ["div_game"], "+ skill value out (both teams)": B + ["skill_out_sum"], "+ both": B + ["div_game", "skill_out_sum"]}.items():
    M.TOTAL_FEATS = tf; r = both(f); M.TOTAL_FEATS = B
    rows.append({"variant": name, **{f"{k}_{w}": v for w, d in r.items() for k, v in d.items()}}); print(name, {w: r[w]["total_mae"] for w in r}, flush=True)
pd.DataFrame(rows).to_csv("reports/totals_div.csv", index=False); print("DONE")
