"""A player listed out was valued on his own last eight games, on any team. A star traded in and hurt was then
taken out of a team whose ratings never had him (A.J. Brown, NE, Week 3 2026). Usage over the team's last eight
games instead, only his touches for that team: both windows, against the same model with the old usage.
Output reports/traded_out.csv."""
import pandas as pd
from nflmodel import model as M, players as PL
from nflmodel.model import OUT
from experiments.common import both
f0 = M.with_trends(pd.read_parquet(OUT / "features_asof.parquet"))
games = pd.read_parquet(OUT / "games.parquet"); pg = pd.read_parquet(OUT / "player_games.parquet")
def with_iv(iv):
    f = f0.drop(columns=["skill_out_value", "opp_skill_out_value"]).merge(iv, on=["game_id", "team"], how="left")
    f = f.merge(iv.rename(columns={"team": "opp", "skill_out_value": "opp_skill_out_value"}), on=["game_id", "opp"], how="left")
    f[["skill_out_value", "opp_skill_out_value"]] = f[["skill_out_value", "opp_skill_out_value"]].fillna(0.0); return f
rows = []
def row(name, r): return {"variant": name, **{f"{k}_{w}": v for w, d in r.items() for k, v in d.items()}}
for name, flag in [("player's own last eight games, any team (today)", False), ("team's last eight games, his touches for that team", True)]:
    PL.TEAM_WINDOW = flag
    iv = PL.injury_value(games, pg)[["game_id", "team", "skill_out_value"]]
    print(name, "games with a value", int((iv.skill_out_value > 0).sum()), "mean", round(float(iv.skill_out_value.mean()), 5), flush=True)
    r = both(with_iv(iv)); rows.append(row(name, r)); print(name, {w: (r[w]["team_mae"], r[w]["margin_mae"], r[w]["ats5"], r[w]["ats4"]) for w in r}, flush=True)
pd.DataFrame(rows).to_csv("reports/traded_out.csv", index=False); print("DONE")
