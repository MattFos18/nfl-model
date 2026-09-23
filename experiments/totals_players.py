"""The totals equation has never used the player model. With the skill-out values rebuilt (480 touches, 10th
percentile), try the summed skill value out, the summed offensive snaps out and the summed offseason turnover as
inputs to the total, on both windows. Output reports/totals_players.csv."""
import pandas as pd
from nflmodel import model as M
from nflmodel.model import OUT
from experiments.common import both
f = M.with_trends(pd.read_parquet(OUT / "features_asof.parquet"))
base_t = M.TOTAL_FEATS.copy(); rows = []
def row(name, r): return {"variant": name, **{f"{k}_{w}": v for w, d in r.items() for k, v in d.items()}}
base = both(f); rows.append(row("(today)", base)); print("base", {w: base[w]["total_mae"] for w in base}, flush=True)
for name, cols in [("skill value out, both teams", ["skill_out_sum"]), ("offensive snaps out, both teams", ["snap_out_sum"]), ("offseason turnover, both teams", ["turnover_early_sum"]),
                   ("skill value out + snaps out", ["skill_out_sum", "snap_out_sum"]), ("all three", ["skill_out_sum", "snap_out_sum", "turnover_early_sum"])]:
    M.TOTAL_FEATS = base_t + cols; r = both(f); rows.append(row(name, r)); M.TOTAL_FEATS = base_t
    print(name, {w: round(r[w]["total_mae"] - base[w]["total_mae"], 4) for w in r}, flush=True)
df = pd.DataFrame(rows)
for w in ["2019-22", "2023-25"]: df[f"delta_total_{w}"] = (df[f"total_mae_{w}"] - df.loc[0, f"total_mae_{w}"]).round(4)
df["verdict"] = ["base" if i == 0 else ("helps both" if d1 < -0.001 and d2 < -0.001 else ("helps one" if d1 < -0.001 or d2 < -0.001 else "no")) for i, (d1, d2) in enumerate(zip(df["delta_total_2019-22"], df["delta_total_2023-25"]))]
df.to_csv("reports/totals_players.csv", index=False); print(df[["variant", "delta_total_2019-22", "delta_total_2023-25", "verdict"]].to_string()); print("DONE")
