"""Opponent-adjusted QB rating: a QB's EPA per dropback is taken against whatever defenses he faced. Add back the
opposing defense's pass-EPA rating (as of that game) before decaying, so a QB who faced good defenses is not
undersold. Features rebuilt, both windows. Output reports/qb_adjusted.csv."""
import numpy as np, pandas as pd
from nflmodel import ratings as R, model as M
from nflmodel.model import OUT
from experiments.common import both
tg = pd.read_parquet(OUT / "team_games.parquet"); games = pd.read_parquet(OUT / "games.parquet"); qb = pd.read_parquet(OUT / "qb_games.parquet")
feats = pd.read_parquet(OUT / "features_asof.parquet")
opp_def = feats.set_index(["game_id", "team"])["def_pass_epa"] if "def_pass_epa" in feats.columns else feats.set_index(["game_id", "team"])["def_epa_play"]
rows = []
for name, scale in [("raw (current)", 0.0), ("adjusted, full", 1.0), ("adjusted, half", 0.5)]:
    q = qb.copy()
    if scale:
        adj = q.set_index(["game_id", "team"]).index.map(lambda k: opp_def.get(k, 0.0))
        q["qb_epa"] = q.qb_epa + scale * np.nan_to_num(np.asarray(adj, dtype=float)) * q.dropbacks
    f = M.with_trends(R.build_features(R.DEFAULT, tg=tg, games=games, qb=q)); r = both(f)
    rows.append({"variant": name, **{f"{k}_{w}": v for w, d in r.items() for k, v in d.items()}}); print(name, {w: (r[w]["team_mae"], r[w]["margin_mae"], r[w]["ats5"]) for w in r}, flush=True)
pd.DataFrame(rows).to_csv("reports/qb_adjusted.csv", index=False); print("DONE")
