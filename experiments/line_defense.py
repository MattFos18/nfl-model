"""Next player-model steps: offensive line continuity (linemen from last game now out) and snap-weighted absences on
both sides of the ball, from snap counts, injury reports and rosters. Added to the current sixteen-input model on both
windows, one at a time and combined. Output reports/line_defense.csv."""
import pandas as pd
from nflmodel import model as M
from nflmodel.model import OUT
from experiments.common import both
f = M.with_trends(pd.read_parquet(OUT / "features_asof.parquet"))
t = pd.read_parquet(OUT / "trends_asof.parquet")[["game_id", "team", "ol_out", "off_snap_out", "def_snap_out"]]
opp = t.rename(columns={"team": "opp", "ol_out": "opp_ol_out", "off_snap_out": "opp_off_snap_out", "def_snap_out": "opp_def_snap_out"})
f = f.merge(opp, on=["game_id", "opp"], how="left")
for c in ["opp_ol_out", "opp_off_snap_out", "opp_def_snap_out"]:
    f[c] = f[c].fillna(0.0)
B = M.FEATS.copy(); rows = []
V = {"base": B, "+ own OL out (count)": B + ["ol_out"], "+ own offensive snaps out": B + ["off_snap_out"], "+ opponent OL out": B + ["opp_ol_out"],
     "+ opponent defensive snaps out": B + ["opp_def_snap_out"], "+ own OL out + opponent defensive snaps out": B + ["ol_out", "opp_def_snap_out"],
     "+ all four": B + ["ol_out", "off_snap_out", "opp_ol_out", "opp_def_snap_out"]}
for name, feats in V.items():
    M.FEATS = feats; r = both(f); M.FEATS = B
    rows.append({"variant": name, **{f"{k}_{w}": v for w, d in r.items() for k, v in d.items()}})
    print(name, {w: (r[w]["team_mae"], r[w]["margin_mae"], r[w]["ats5"]) for w in r}, flush=True)
df = pd.DataFrame(rows); df.to_csv("reports/line_defense.csv", index=False)
print(df[["variant", "team_mae_2019-22", "margin_mae_2019-22", "ats5_2019-22", "team_mae_2023-25", "margin_mae_2023-25", "ats5_2023-25"]].to_string()); print("DONE")
