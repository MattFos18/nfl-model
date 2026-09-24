"""Partial games (24 Sep 2026, Matt: a 5-play injury exit or a 1-play cameo should not count as a game). A regular
skill player plays under half his usual snaps in about 8% of his games (2.6 touches in them against 7.6 usually), so
an eight-game usage window holds one such game on average and his share of the team's touches reads low.

Part A, the game model's skill-out inputs (players.USAGE_MODE, the player's own last eight games):
  none     every game he appeared in counts as a full game (the rule until now)
  exclude  games he played under half his usual snap share are dropped
  weight   each game counts by his snap share over his usual, capped at 1 (a first-drive exit is about a tenth of a game)
Both windows and 2015 to 2018; adopt only if it helps both windows. Output reports/partial_games.csv."""
import os, numpy as np, pandas as pd
from nflmodel import model as M, players as PL, backtest as B
from nflmodel.model import OUT
from experiments.common import both
f0 = M.with_trends(pd.read_parquet(OUT / "features_asof.parquet"))
games = pd.read_parquet(OUT / "games.parquet"); pg = pd.read_parquet(OUT / "player_games.parquet")
def with_iv(iv):
    f = f0.drop(columns=["skill_out_value", "opp_skill_out_value"]).merge(iv, on=["game_id", "team"], how="left")
    f = f.merge(iv.rename(columns={"team": "opp", "skill_out_value": "opp_skill_out_value"}), on=["game_id", "opp"], how="left")
    f[["skill_out_value", "opp_skill_out_value"]] = f[["skill_out_value", "opp_skill_out_value"]].fillna(0.0); return f
def third(f):
    p3 = M.walk_forward(f, range(2015, 2019)); d = B.join(p3, games)
    d = d[(d.game_type == "REG") & d.season.isin(range(2015, 2019)) & (d.week < 18) & d.spread_line.notna() & d.home_score.notna()]
    pm = B.points_miss(d).set_index("target"); return round(float(pm.loc["team points", "model_mae"]), 4), round(float(pm.loc["margin", "model_mae"]), 4)
rows = []
for mode in (os.environ.get("MODES") or "none,exclude,weight").split(","):
    PL.USAGE_MODE = None if mode == "none" else mode
    iv = PL.injury_value(games, pg)[["game_id", "team", "skill_out_value"]]
    f = with_iv(iv); r = both(f); t = third(f)
    rows.append({"part": "A game model skill-out", "variant": mode, "mean_value": round(float(iv.skill_out_value.mean()), 5), **{f"{k}_{w}": v for w, d in r.items() for k, v in d.items()}, "team_mae_2015-18": t[0], "margin_mae_2015-18": t[1]})
    print(mode, {w: (r[w]["team_mae"], r[w]["margin_mae"], r[w]["ats4"]) for w in r}, "2015-18", t, flush=True)
out = "reports/partial_games.csv"; old = pd.read_csv(out) if os.path.exists(out) else pd.DataFrame()
pd.concat([old, pd.DataFrame(rows)], ignore_index=True).drop_duplicates(["part", "variant"], keep="last").to_csv(out, index=False); print("DONE")
