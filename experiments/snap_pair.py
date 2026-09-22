"""The two snap-weighted absence inputs together (own offensive snaps out, opponent defensive snaps out), against all four. Output reports/snap_pair.csv."""
import pandas as pd
from nflmodel import model as M
from nflmodel.model import OUT
from experiments.common import both
f = M.with_trends(pd.read_parquet(OUT / "features_asof.parquet"))
t = pd.read_parquet(OUT / "trends_asof.parquet")[["game_id", "team", "ol_out", "off_snap_out", "def_snap_out"]]
f = f.merge(t.rename(columns={"team": "opp", "ol_out": "opp_ol_out", "off_snap_out": "opp_off_snap_out", "def_snap_out": "opp_def_snap_out"}), on=["game_id", "opp"], how="left")
for c in ["opp_ol_out", "opp_off_snap_out", "opp_def_snap_out"]:
    f[c] = f[c].fillna(0.0)
B = M.FEATS.copy(); rows = []
for name, feats in {"base": B, "+ own offensive snaps out + opponent defensive snaps out": B + ["off_snap_out", "opp_def_snap_out"], "+ the pair + own OL out": B + ["off_snap_out", "opp_def_snap_out", "ol_out"], "+ all four": B + ["ol_out", "off_snap_out", "opp_ol_out", "opp_def_snap_out"]}.items():
    M.FEATS = feats; r = both(f); M.FEATS = B
    rows.append({"variant": name, **{f"{k}_{w}": v for w, d in r.items() for k, v in d.items()}}); print(name, {w: (r[w]["team_mae"], r[w]["margin_mae"], r[w]["ats5"]) for w in r}, flush=True)
pd.DataFrame(rows).to_csv("reports/snap_pair.csv", index=False); print("DONE")
