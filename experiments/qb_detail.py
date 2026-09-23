"""The QB in more detail: today's QB rating is EPA per dropback with sacks included. Rebuild the QB table from the
play-by-play with sacks taken out (EPA on non-sack dropbacks, per non-sack dropback), so the rating measures
throwing and scrambling rather than protection, and score both windows with the features rebuilt.
Output reports/qb_detail.csv."""
import pandas as pd, numpy as np
from nflmodel import ratings as R, model as M
from nflmodel.features import RAW, OUT, TEAM_FIX
from experiments.common import both
tg = pd.read_parquet(OUT / "team_games.parquet"); games = pd.read_parquet(OUT / "games.parquet"); qb = pd.read_parquet(OUT / "qb_games.parquet")
frames = []
for s in range(2012, 2027):
    f = RAW / "pbp" / f"play_by_play_{s}.parquet"
    if f.exists(): frames.append(pd.read_parquet(f, columns=["game_id", "season", "week", "posteam", "passer_player_id", "qb_dropback", "sack", "qb_epa", "epa"]))
p = pd.concat(frames, ignore_index=True); p = p[(p.qb_dropback == 1) & p.passer_player_id.notna()].copy(); p["posteam"] = p.posteam.replace(TEAM_FIX)
p["e"] = pd.to_numeric(p.qb_epa, errors="coerce").fillna(pd.to_numeric(p.epa, errors="coerce")); p["sk"] = pd.to_numeric(p.sack, errors="coerce").fillna(0) == 1
alt = p.groupby(["game_id", "season", "week", "posteam", "passer_player_id"]).apply(lambda x: pd.Series({"dropbacks": int((~x.sk).sum()), "qb_epa": float(x.e[~x.sk].sum())})).reset_index().rename(columns={"posteam": "team", "passer_player_id": "qb_id"})
alt = alt[alt.dropbacks > 0]
rows = []
for name, q in [("EPA per dropback, sacks included (today)", qb), ("EPA per dropback, sacks excluded", alt)]:
    f = M.with_trends(R.build_features(R.DEFAULT, tg=tg, games=games, qb=q)); r = both(f)
    rows.append({"variant": name, **{f"{k}_{w}": v for w, d in r.items() for k, v in d.items()}}); print(name, {w: (r[w]["team_mae"], r[w]["margin_mae"], r[w]["ats5"]) for w in r}, flush=True)
pd.DataFrame(rows).to_csv("reports/qb_detail.csv", index=False); print("DONE")
