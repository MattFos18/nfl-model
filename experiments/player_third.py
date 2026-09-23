"""Tie-breaker on the window nobody tuned on (2015 to 2018) for the player-model knobs: today's setting against the
two best combinations from the sweep. The skill-out values are rebuilt at each setting, the twenty-input model is
walked forward over 2015 to 2018, and the team points miss, spread miss and flag records are reported.
Output reports/player_third.csv."""
import numpy as np, pandas as pd
from nflmodel import model as M, players as PL, backtest as B
from nflmodel.model import OUT
f0 = M.with_trends(pd.read_parquet(OUT / "features_asof.parquet"))
games = pd.read_parquet(OUT / "games.parquet"); pg = pd.read_parquet(OUT / "player_games.parquet")
orig_prior = PL.PlayerValues.prior; rows = []
def run(name, p, pct=25):
    def prior(self, role, season, _p=pct):
        key = (role, season)
        if key not in self._prior:
            h = self.pg[(self.pg.role == role) & (self.pg.season < season)]
            tot = h.groupby("player_id").agg(plays=("plays", "sum"), epa=("epa", "sum")); tot = tot[tot.plays >= 100]
            self._prior[key] = float(np.percentile(tot.epa / tot.plays, _p)) if len(tot) else 0.0
        return self._prior[key]
    PL.PlayerValues.prior = prior
    if p is None:
        f = f0
    else:
        iv = PL.injury_value(games, pg, p=p)[["game_id", "team", "skill_out_value"]]
        f = f0.drop(columns=["skill_out_value", "opp_skill_out_value"]).merge(iv, on=["game_id", "team"], how="left")
        f = f.merge(iv.rename(columns={"team": "opp", "skill_out_value": "opp_skill_out_value"}), on=["game_id", "opp"], how="left")
        f[["skill_out_value", "opp_skill_out_value"]] = f[["skill_out_value", "opp_skill_out_value"]].fillna(0.0)
    PL.PlayerValues.prior = orig_prior
    p3 = M.walk_forward(f, range(2015, 2019)); d = B.join(p3, games)
    d = d[(d.game_type == "REG") & d.season.isin(range(2015, 2019)) & (d.week < 18) & d.spread_line.notna() & d.home_score.notna()]
    pm = B.points_miss(d).set_index("target"); e = d.model_spread - d.spread_line; res = np.sign(d.home_score - d.away_score - d.spread_line)
    row = {"variant": name, "team_mae": round(float(pm.loc["team points", "model_mae"]), 4), "margin_mae": round(float(pm.loc["margin", "model_mae"]), 4), "n": int(len(d))}
    for cut in [4, 5]:
        m = (np.abs(e) >= cut) & (res != 0); w = int((np.sign(e[m]) == res[m]).sum()); l = int(m.sum() - w); row[f"ats{cut}"] = f"{w}-{l}"
    rows.append(row); print(row, flush=True)
D = PL.DEFAULT
run("decay 0.985, k 80, 25th percentile (today)", None)
run("k 480, 10th percentile", dict(D, k=480.0), pct=10)
run("k 640, 10th percentile", dict(D, k=640.0), pct=10)
run("k 640", dict(D, k=640.0))
pd.DataFrame(rows).to_csv("reports/player_third.csv", index=False); print("DONE")
