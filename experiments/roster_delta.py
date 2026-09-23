"""Trades both ways. A player listed out is now valued on the team's window (experiments/traded_out.py); this tests
the other side: crediting skill players the team's ratings have not seen yet (arrivals, faded as they play) and
taking out players who played in the window but are gone (traded, cut). Both windows, adopt only if both improve.
Output reports/roster_delta.csv."""
import pandas as pd
from nflmodel import model as M, players as PL
from nflmodel.model import OUT
from experiments.common import both
f0 = M.with_trends(pd.read_parquet(OUT / "features_asof.parquet"))
games = pd.read_parquet(OUT / "games.parquet"); pg = pd.read_parquet(OUT / "player_games.parquet")
PL.TEAM_WINDOW = True
iv = PL.injury_value(games, pg)[["game_id", "team", "skill_out_value"]]; print("out values built", flush=True)
rd = PL.roster_delta(games, pg); print("roster delta built", "new>0", int((rd.skill_new_value > 0).sum()), "gone>0", int((rd.skill_gone_value > 0).sum()), rd[["skill_new_value", "skill_gone_value"]].describe().round(4).to_string(), flush=True)
rd.to_parquet("reports/roster_delta_values.parquet", index=False)
def frame(out_extra=None, new=False):
    v = iv.copy()
    if out_extra is not None:
        v = v.merge(out_extra, on=["game_id", "team"], how="left"); v["skill_out_value"] = v.skill_out_value + v.skill_gone_value.fillna(0.0); v = v[["game_id", "team", "skill_out_value"]]
    f = f0.drop(columns=["skill_out_value", "opp_skill_out_value"]).merge(v, on=["game_id", "team"], how="left")
    f = f.merge(v.rename(columns={"team": "opp", "skill_out_value": "opp_skill_out_value"}), on=["game_id", "opp"], how="left")
    f[["skill_out_value", "opp_skill_out_value"]] = f[["skill_out_value", "opp_skill_out_value"]].fillna(0.0)
    if new:
        nv = rd[["game_id", "team", "skill_new_value"]]
        f = f.merge(nv, on=["game_id", "team"], how="left").merge(nv.rename(columns={"team": "opp", "skill_new_value": "opp_skill_new_value"}), on=["game_id", "opp"], how="left")
        f[["skill_new_value", "opp_skill_new_value"]] = f[["skill_new_value", "opp_skill_new_value"]].fillna(0.0)
    return f
rows = []; base_feats = M.FEATS.copy()
def row(name, r): return {"variant": name, **{f"{k}_{w}": v for w, d in r.items() for k, v in d.items()}}
def run(name, f, cols=()):
    M.FEATS = base_feats + list(cols); r = both(f); M.FEATS = base_feats
    rows.append(row(name, r)); print(name, {w: (r[w]["team_mae"], r[w]["margin_mae"], r[w]["ats5"], r[w]["ats4"]) for w in r}, flush=True)
run("out on the team's window (traded_out)", frame())
run("+ players gone folded into out", frame(rd[["game_id", "team", "skill_gone_value"]]))
run("+ arrivals as an input (own and opponent)", frame(new=True), ["skill_new_value", "opp_skill_new_value"])
run("+ both", frame(rd[["game_id", "team", "skill_gone_value"]], new=True), ["skill_new_value", "opp_skill_new_value"])
pd.DataFrame(rows).to_csv("reports/roster_delta.csv", index=False); print("DONE")
