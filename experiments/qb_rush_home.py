"""Two more: (1) the QB rating counts only dropbacks; add the QB's own rushing EPA (designed runs and scrambles the
play-by-play credits to him as rusher) so mobile QBs are not undersold; (2) home-field interactions: home x division
game and home x short week. Both windows against the twenty-input model. Output reports/qb_rush_home.csv."""
import numpy as np, pandas as pd
from nflmodel import ratings as R, model as M
from nflmodel.model import OUT
from experiments.common import both
tg = pd.read_parquet(OUT / "team_games.parquet"); games = pd.read_parquet(OUT / "games.parquet"); qb = pd.read_parquet(OUT / "qb_games.parquet")
pg = pd.read_parquet(OUT / "player_games.parquet")
rush = pg[(pg.role == "rusher") & pg.player_id.isin(set(qb.qb_id))].groupby(["game_id", "team", "player_id"]).agg(rplays=("plays", "sum"), repa=("epa", "sum")).reset_index().rename(columns={"player_id": "qb_id"})
q2 = qb.merge(rush, on=["game_id", "team", "qb_id"], how="left"); q2["rplays"] = q2.rplays.fillna(0); q2["repa"] = q2.repa.fillna(0.0)
rows = []
def run(name, qtab, extra=None):
    f = M.with_trends(R.build_features(R.DEFAULT, tg=tg, games=games, qb=qtab)); f = M.prep(f)
    B = M.FEATS.copy()
    if extra:
        f["home_div"] = f.home * f.div_game; f["home_short"] = f.home * f.rest_short; M.FEATS = B + extra
    r = both(f); M.FEATS = B
    rows.append({"variant": name, **{f"{k}_{w}": v for w, d in r.items() for k, v in d.items()}}); print(name, {w: (r[w]["team_mae"], r[w]["margin_mae"], r[w]["ats5"]) for w in r}, flush=True)
run("current", qb)
qa = q2.copy(); qa["qb_epa"] = qa.qb_epa + qa.repa; qa["dropbacks"] = qa.dropbacks + qa.rplays; run("QB rating with his rushing (per dropback + carry)", qa)
qb_ = q2.copy(); qb_["qb_epa"] = qb_.qb_epa + 0.5 * qb_.repa; run("QB rating with half his rushing", qb_)
run("+ home x division", qb, ["home_div"]); run("+ home x short week", qb, ["home_short"])
pd.DataFrame(rows).to_csv("reports/qb_rush_home.csv", index=False); print("DONE")
