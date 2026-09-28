"""The referee in the totals equation without the market (28 Sep 2026, Matt: no Vegas line in any input). The live
total equation carries ref_over, the referee's over rate against the closing total in his previous games (adopted
25 Sep 2026: lower total miss on all three windows). Tested here against (a) no referee input and (b) ref_tot, the
same reading built without a line: each previous game's total minus the league's mean total of the season before,
averaged and shrunk (nflmodel/trends.py). Every game 2015-2025 priced by the live pipeline with its own trees cache;
margin, total and team misses and the 4+ spread flag on 2015-18, 2019-22 and 2023-25. Output reports/ref_noline.csv."""
import os, pandas as pd
from nflmodel import model as M
from nflmodel.model import OUT
from experiments.common import both
S = os.environ.get("REF_SCRATCH", "/tmp/ref_noline")
os.makedirs(S, exist_ok=True)
M.TREES_CACHE = type(OUT)(S) / "trees_cache_ref.parquet"; M._TC = {"df": None, "used": set(), "new": []}
f = M.with_trends(pd.read_parquet(OUT / "features_asof.parquet"))
B = M.TOTAL_FEATS.copy(); rows = []
for name, tf in {"live: ref_over (vs the closing total)": B, "no referee input": [c for c in B if c != "ref_over"], "ref_tot (no line)": [c if c != "ref_over" else "ref_tot" for c in B]}.items():
    M.TOTAL_FEATS = tf; r = both(f); M.TOTAL_FEATS = B
    row = {"variant": name, **{f"{k}_{w}": v for w, d in r.items() for k, v in d.items()}}; rows.append(row); print(row, flush=True)
    pd.DataFrame(rows).to_csv("reports/ref_noline.csv", index=False)
print("DONE")
