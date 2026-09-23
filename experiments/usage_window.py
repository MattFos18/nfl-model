"""Which window a player's usage (his share of the team's touches, behind the skill-out inputs) is measured on:
his own last eight games on any team (the original), the team's last eight games, or the window the team's ratings
are built on (this season and last, 0.94 per week of age, last season at 0.8: players.TEAM_WINDOW = "rating").
A star traded in and hurt was being taken out of a team whose ratings never had him (A.J. Brown, NE, Week 3 2026).
Both windows; adopt only if both improve or hold. Output reports/usage_window.csv."""
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
for name, flag in [("player's own last eight games, any team (original)", False), ("team's last eight games, his touches for that team", "last"), ("the ratings' window: this season and last, decayed 0.94 per week, last season at 0.8", "rating")]:
    PL.TEAM_WINDOW = flag
    iv = PL.injury_value(games, pg)[["game_id", "team", "skill_out_value"]]
    print(name, "games with a value", int((iv.skill_out_value > 0).sum()), "mean", round(float(iv.skill_out_value.mean()), 5), flush=True)
    r = both(with_iv(iv)); rows.append(row(name, r)); print(name, {w: (r[w]["team_mae"], r[w]["margin_mae"], r[w]["ats5"], r[w]["ats4"]) for w in r}, flush=True)
pd.DataFrame(rows).to_csv("reports/usage_window.csv", index=False); print("DONE")
