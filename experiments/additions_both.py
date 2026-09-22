"""Every candidate input added to the current model one at a time, scored on both windows with the weekly refit.
Adopt only what lowers the points miss on both windows. Output reports/additions_both.csv."""
import pandas as pd
from nflmodel import model as M, tune as T
from nflmodel.model import OUT
from experiments.common import both
f = M.with_trends(pd.read_parquet(OUT / "features_asof.parquet"))
base_feats = M.FEATS.copy()
rows = []
def row(name, r):
    return {"added": name, **{f"{k}_{w}": v for w, d in r.items() for k, v in d.items()}}
base = both(f); rows.append(row("(none)", base)); print("base", base, flush=True)
cands = dict(T.ADDITIONS)
cands["all matchup history factors together"] = ["h2h_cover", "coach_ats", "qb_ats", "home_edge_in_play"]
for name, cols in cands.items():
    if any(c not in f.columns for c in cols):
        print("skip", name, flush=True); continue
    M.FEATS = base_feats + [c for c in cols if c not in base_feats]
    r = both(f); rows.append(row(name, r))
    print(name, {w: (round(r[w]["team_mae"] - base[w]["team_mae"], 4), r[w]["ats5"]) for w in r}, flush=True)
    M.FEATS = base_feats
df = pd.DataFrame(rows)
for w in ["2019-22", "2023-25"]:
    df[f"delta_{w}"] = df[f"team_mae_{w}"] - df.loc[0, f"team_mae_{w}"]
df["verdict"] = ["base" if i == 0 else ("helps both" if d1 < -0.001 and d2 < -0.001 else ("helps one" if d1 < -0.001 or d2 < -0.001 else "no")) for i, (d1, d2) in enumerate(zip(df["delta_2019-22"], df["delta_2023-25"]))]
df.to_csv("reports/additions_both.csv", index=False)
print(df[["added", "delta_2019-22", "ats5_2019-22", "delta_2023-25", "ats5_2023-25", "verdict"]].to_string())
print("DONE")
