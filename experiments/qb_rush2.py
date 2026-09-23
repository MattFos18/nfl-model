"""Clean version of the QB rushing test: scrambles are already dropbacks (qb_dropback = 1), so only designed QB runs
(rush by the QB with qb_dropback = 0) are added, EPA and plays. Both windows. Output reports/qb_rush2.csv."""
import numpy as np, pandas as pd, pyarrow.parquet as pq
from nflmodel import ratings as R, model as M
from nflmodel.features import RAW, OUT, TEAM_FIX
from experiments.common import both
tg = pd.read_parquet(OUT / "team_games.parquet"); games = pd.read_parquet(OUT / "games.parquet"); qb = pd.read_parquet(OUT / "qb_games.parquet")
qb_ids = set(qb.qb_id)
frames = []
for s in range(2012, 2027):
    f = RAW / "pbp" / f"play_by_play_{s}.parquet"
    if f.exists(): frames.append(pd.read_parquet(f, columns=["game_id", "season", "week", "posteam", "rush_attempt", "qb_dropback", "rusher_player_id", "epa"]))
p = pd.concat(frames, ignore_index=True); p["posteam"] = p.posteam.replace(TEAM_FIX)
d = p[(pd.to_numeric(p.rush_attempt, errors="coerce") == 1) & (pd.to_numeric(p.qb_dropback, errors="coerce") != 1) & p.rusher_player_id.isin(qb_ids)]
runs = d.groupby(["game_id", "season", "week", "posteam", "rusher_player_id"]).agg(rplays=("epa", "size"), repa=("epa", "sum")).reset_index().rename(columns={"posteam": "team", "rusher_player_id": "qb_id"})
print("designed QB runs per season", runs.groupby("season").rplays.sum().to_dict(), flush=True)
q2 = qb.merge(runs[["game_id", "team", "qb_id", "rplays", "repa"]], on=["game_id", "team", "qb_id"], how="left"); q2["rplays"] = q2.rplays.fillna(0); q2["repa"] = q2.repa.fillna(0.0)
rows = []
def run(name, qtab):
    f = M.with_trends(R.build_features(R.DEFAULT, tg=tg, games=games, qb=qtab)); r = both(f)
    rows.append({"variant": name, **{f"{k}_{w}": v for w, dd in r.items() for k, v in dd.items()}}); print(name, {w: (r[w]["team_mae"], r[w]["margin_mae"], r[w]["ats5"]) for w in r}, flush=True)
run("current (dropbacks only)", qb)
qa = q2.copy(); qa["qb_epa"] = qa.qb_epa + qa.repa; qa["dropbacks"] = qa.dropbacks + qa.rplays; run("+ designed QB runs (EPA and plays)", qa)
pd.DataFrame(rows).to_csv("reports/qb_rush2.csv", index=False); print("DONE")
