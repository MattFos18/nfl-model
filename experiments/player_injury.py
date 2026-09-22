"""Phase 2 of the player model: does the value lost to injured skill players (players.injury_value) improve the
points model? Added as an input, and as an adjustment to the offense rating. Both windows. Output reports/player_injury.csv."""
import pandas as pd
from nflmodel import model as M
from nflmodel.model import OUT
from experiments.common import both
f = M.with_trends(pd.read_parquet(OUT / "features_asof.parquet"))
iv = pd.read_parquet(OUT / "player_injury.parquet")
f = f.merge(iv, on=["game_id", "team"], how="left")
for c in ["skill_out_value", "skill_out_share", "n_skill_out"]:
    f[c] = f[c].fillna(0.0)
# the opponent's loss, for the defense side of the row
opp = iv.rename(columns={"team": "opp", "skill_out_value": "opp_skill_out_value"})[["game_id", "opp", "opp_skill_out_value"]]
f = f.merge(opp, on=["game_id", "opp"], how="left"); f["opp_skill_out_value"] = f.opp_skill_out_value.fillna(0.0)
f["off_epa_adj"] = f.off_epa_play - f.skill_out_value
base_feats = M.FEATS.copy(); rows = []
def run(name, feats, frame):
    M.FEATS = feats; r = both(frame); M.FEATS = base_feats
    rows.append({"variant": name, **{f"{k}_{w}": v for w, d in r.items() for k, v in d.items()}}); print(name, {w: (r[w]["team_mae"], r[w]["ats5"]) for w in r}, flush=True)
run("baseline", base_feats, f)
run("+ skill value out (EPA per play lost)", base_feats + ["skill_out_value"], f)
run("+ skill value out + touch share out", base_feats + ["skill_out_value", "skill_out_share"], f)
run("+ own and opponent skill value out", base_feats + ["skill_out_value", "opp_skill_out_value"], f)
g = f.copy(); g["off_epa_play"] = g.off_epa_adj
run("offense rating minus the value out", base_feats, g)
pd.DataFrame(rows).to_csv("reports/player_injury.csv", index=False)
print("DONE")
