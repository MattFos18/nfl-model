"""The usage-window sweep (reports/usage_window.csv) kept the original window: a player's own last eight games on
any team. This tests the narrow fix on its own: the same window, but nothing taken out for a player who has never
played for this team in its ratings' window (players.TEAM_WINDOW = "gate"). Output reports/usage_gate.csv."""
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
old = pd.read_csv("reports/usage_window.csv"); rows.append(old.iloc[0].to_dict())
PL.TEAM_WINDOW = "gate"
for gm, name in [(0.0001, "gated: nothing for a player who has never played for the team"), (0.25, "gated: nothing under a quarter of the ratings window played"), (0.5, "gated: nothing under half of the ratings window played")]:
    PL.GATE_MIN = gm
    iv = PL.injury_value(games, pg)[["game_id", "team", "skill_out_value"]]
    print(name, "games with a value", int((iv.skill_out_value > 0).sum()), "mean", round(float(iv.skill_out_value.mean()), 5), flush=True)
    r = both(with_iv(iv)); rows.append(row(name, r)); print(name, {w: (r[w]["team_mae"], r[w]["margin_mae"], r[w]["ats5"], r[w]["ats4"]) for w in r}, flush=True)
pd.DataFrame(rows).to_csv("reports/usage_gate.csv", index=False); print("DONE")
