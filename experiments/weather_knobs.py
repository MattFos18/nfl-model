"""The weather cutoffs were set by hand: cold is under 35F, a short week is 5 days or fewer, a long one 10 or more
(rest is not in the model). Sweep the cold cutoff (30, 35, 40, 45F) and a continuous cold term (degrees under 45,
capped) on both windows. Output reports/weather_knobs.csv."""
import numpy as np, pandas as pd
from nflmodel import model as M
from nflmodel.model import OUT
from experiments.common import both
f0 = M.with_trends(pd.read_parquet(OUT / "features_asof.parquet"))
orig_prep = M.prep; rows = []
def row(name, r): return {"variant": name, **{f"{k}_{w}": v for w, d in r.items() for k, v in d.items()}}
base = both(f0); rows.append(row("cold under 35F (today)", base)); print("base", base, flush=True)
for cut in [30, 40, 45]:
    def prep(f, _c=cut):
        f = orig_prep(f); f["cold"] = np.where(f.dome == 1, 0.0, (f.temp.fillna(60) < _c).astype(float)); f["warm_in_cold"] = f["cold"] * f.team.isin(M.WARM_OR_DOME).astype(float); return f
    M.prep = prep; r = both(f0); rows.append(row(f"cold under {cut}F", r)); print(cut, {w: (round(r[w]["team_mae"] - base[w]["team_mae"], 4), r[w]["ats5"]) for w in r}, flush=True); M.prep = orig_prep
def prep(f):
    f = orig_prep(f); f["cold"] = np.where(f.dome == 1, 0.0, ((45 - f.temp.fillna(60)).clip(0, 30) / 10.0)); f["warm_in_cold"] = f["cold"] * f.team.isin(M.WARM_OR_DOME).astype(float); return f
M.prep = prep; r = both(f0); rows.append(row("degrees under 45F (per 10F, capped at 30)", r)); print("linear", {w: (round(r[w]["team_mae"] - base[w]["team_mae"], 4), r[w]["ats5"]) for w in r}, flush=True); M.prep = orig_prep
df = pd.DataFrame(rows)
for w in ["2019-22", "2023-25"]: df[f"delta_{w}"] = df[f"team_mae_{w}"] - df.loc[0, f"team_mae_{w}"]
df["verdict"] = ["base" if i == 0 else ("helps both" if d1 < -0.001 and d2 < -0.001 else ("helps one" if d1 < -0.001 or d2 < -0.001 else "no")) for i, (d1, d2) in enumerate(zip(df["delta_2019-22"], df["delta_2023-25"]))]
df.to_csv("reports/weather_knobs.csv", index=False); print(df[["variant", "delta_2019-22", "delta_2023-25", "verdict"]].to_string()); print("DONE")
