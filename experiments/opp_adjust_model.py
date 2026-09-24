"""Opponent-adjusted player values in the game model (24 Sep 2026). experiments/opp_adjust.py found each player's
value predicts his next game better on every role and window when his past games are adjusted for the defenses he
faced. The skill values also feed the game model (skill_out_value, own and opponent: the value of RB/WR/TE listed
out). Same test as every input: points and margin miss on 2019-22 and 2023-25 (and 2015-18), adjusted against not.
Writes reports/opp_adjust_model.csv."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pandas as pd
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
for adj in (False, True):
    PL.OPP_ADJUST = adj
    iv = PL.injury_value(games, pg)[["game_id", "team", "skill_out_value"]]
    f = with_iv(iv); r = both(f); t = third(f)
    rows.append({"variant": "opponent-adjusted" if adj else "raw (now)", **{f"{k}_{w}": v for w, d in r.items() for k, v in d.items()}, "team_mae_2015-18": t[0], "margin_mae_2015-18": t[1]})
    print(rows[-1], flush=True)
pd.DataFrame(rows).to_csv(Path(__file__).resolve().parent.parent / "reports" / "opp_adjust_model.csv", index=False)
