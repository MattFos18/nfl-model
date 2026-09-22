"""The inputs that helped on both windows one at a time (division, travel, pass/rush split, skill value out), combined,
so each is adopted only if it still helps with the others present. Output reports/combo.csv."""
import pandas as pd
from nflmodel import model as M
from nflmodel.model import OUT
from experiments.common import both
f = M.with_trends(pd.read_parquet(OUT / "features_asof.parquet"))
iv = pd.read_parquet(OUT / "player_injury.parquet")
f = f.merge(iv[["game_id", "team", "skill_out_value"]], on=["game_id", "team"], how="left")
opp = iv.rename(columns={"team": "opp", "skill_out_value": "opp_skill_out_value"})[["game_id", "opp", "opp_skill_out_value"]]
f = f.merge(opp, on=["game_id", "opp"], how="left")
f["skill_out_value"] = f.skill_out_value.fillna(0.0); f["opp_skill_out_value"] = f.opp_skill_out_value.fillna(0.0)
B = M.FEATS.copy(); PR = ["off_pass_epa", "def_pass_epa", "off_rush_epa", "def_rush_epa"]; SK = ["skill_out_value", "opp_skill_out_value"]
V = {"base": B, "+div": B + ["div_game"], "+div +travel": B + ["div_game", "travel_miles"], "+pass/rush": B + PR,
     "pass/rush replacing epa/play": [c for c in B if c not in ("off_epa_play", "def_epa_play")] + PR,
     "+div +pass/rush": B + ["div_game"] + PR, "+div +pass/rush +travel": B + ["div_game", "travel_miles"] + PR,
     "+div +pass/rush +skill out": B + ["div_game"] + PR + SK, "+div +pass/rush +travel +skill out": B + ["div_game", "travel_miles"] + PR + SK,
     "+div +skill out": B + ["div_game"] + SK}
rows = []
for name, feats in V.items():
    M.FEATS = feats; r = both(f); M.FEATS = B
    rows.append({"variant": name, "n_inputs": len(feats), **{f"{k}_{w}": v for w, d in r.items() for k, v in d.items()}})
    print(name, {w: (r[w]["team_mae"], r[w]["margin_mae"], r[w]["ats5"]) for w in r}, flush=True)
df = pd.DataFrame(rows); df.to_csv("reports/combo.csv", index=False)
print(df[["variant", "n_inputs", "team_mae_2019-22", "ats5_2019-22", "team_mae_2023-25", "ats5_2023-25"]].to_string()); print("DONE")
