"""In-game QB injuries: a game the named starter left early is a weak reading of the team's offense. Weight each
game's offense/defense observation in the ratings by the starter's share of dropbacks (variants), rebuild the
features, score both windows. Output reports/starter_share.csv."""
import numpy as np, pandas as pd
from nflmodel import ratings as R, model as M
from nflmodel.model import OUT
from experiments.common import both
tg = pd.read_parquet(OUT / "team_games.parquet"); games = pd.read_parquet(OUT / "games.parquet"); qb = pd.read_parquet(OUT / "qb_games.parquet")
# starter share: the schedule's named starter's dropbacks over the team's dropbacks in that game
long = pd.concat([games[["game_id", "home_team", "home_qb_id"]].rename(columns={"home_team": "team", "home_qb_id": "qb_id"}),
                  games[["game_id", "away_team", "away_qb_id"]].rename(columns={"away_team": "team", "away_qb_id": "qb_id"})])
tot = qb.groupby(["game_id", "team"]).dropbacks.sum().rename("db_total")
st = long.merge(qb, on=["game_id", "team", "qb_id"], how="left").merge(tot, on=["game_id", "team"], how="left")
st["starter_share"] = (st.dropbacks / st.db_total).clip(0, 1)
tg = tg.merge(st[["game_id", "team", "starter_share"]], on=["game_id", "team"], how="left")
tg["starter_share"] = tg.starter_share.fillna(1.0)
print("games with starter share under 0.5:", int((tg.starter_share < 0.5).sum()), "of", int(tg.pf.notna().sum()), flush=True)
orig = R.window
def make(kind):
    def window(t, season, week, decay, prior):
        rows, w = orig(t, season, week, decay, prior)
        s = rows.starter_share.values if "starter_share" in rows.columns else np.ones(len(rows))
        if kind == "share":
            w = w * s
        elif kind == "half":
            w = w * np.where(s >= 0.5, 1.0, 0.25)
        elif kind == "both_sides":  # the game also tells less about the opponent's defense: same weight (already the case, one row per side)
            w = w * np.sqrt(s)
        return rows, w
    return window
rows = []
for kind in ["baseline", "share", "half", "both_sides"]:
    R.window = make(kind)
    f = M.with_trends(R.build_features(tg=tg, games=games, qb=qb))
    r = both(f)
    rows.append({"variant": kind, **{f"{k}_{w}": v for w, d in r.items() for k, v in d.items()}})
    print(kind, {w: (r[w]["team_mae"], r[w]["ats5"]) for w in r}, flush=True)
R.window = orig
pd.DataFrame(rows).to_csv("reports/starter_share.csv", index=False)
print("DONE")
