"""The player model's knobs were set by hand: decay 0.985 per game, 80 touches of prior weight, replacement level
at the 25th percentile. Rebuild the skill-out values at other settings and score the twenty-input model on both
windows. Output reports/player_knobs.csv."""
import numpy as np, pandas as pd
from nflmodel import model as M, players as PL
from nflmodel.model import OUT
from experiments.common import both
f0 = M.with_trends(pd.read_parquet(OUT / "features_asof.parquet"))
games = pd.read_parquet(OUT / "games.parquet"); pg = pd.read_parquet(OUT / "player_games.parquet")
rows = []
def row(name, r): return {"variant": name, **{f"{k}_{w}": v for w, d in r.items() for k, v in d.items()}}
base = both(f0); rows.append(row("decay 0.985, k 80, 25th percentile (today)", base)); print("base", base, flush=True)
orig_prior = PL.PlayerValues.prior
def run(name, p, pct=25):
    def prior(self, role, season, _p=pct):
        key = (role, season)
        if key not in self._prior:
            h = self.pg[(self.pg.role == role) & (self.pg.season < season)]
            tot = h.groupby("player_id").agg(plays=("plays", "sum"), epa=("epa", "sum")); tot = tot[tot.plays >= 100]
            self._prior[key] = float(np.percentile(tot.epa / tot.plays, _p)) if len(tot) else 0.0
        return self._prior[key]
    PL.PlayerValues.prior = prior
    iv = PL.injury_value(games, pg, p=p)[["game_id", "team", "skill_out_value"]]
    PL.PlayerValues.prior = orig_prior
    f = f0.drop(columns=["skill_out_value", "opp_skill_out_value"]).merge(iv, on=["game_id", "team"], how="left")
    f = f.merge(iv.rename(columns={"team": "opp", "skill_out_value": "opp_skill_out_value"}), on=["game_id", "opp"], how="left")
    f[["skill_out_value", "opp_skill_out_value"]] = f[["skill_out_value", "opp_skill_out_value"]].fillna(0.0)
    r = both(f); rows.append(row(name, r)); print(name, {w: (round(r[w]["team_mae"] - base[w]["team_mae"], 4), r[w]["ats5"]) for w in r}, flush=True)
D = PL.DEFAULT
run("k 40", dict(D, k=40.0)); run("k 160", dict(D, k=160.0))
run("10th percentile", D, pct=10); run("40th percentile", D, pct=40)
run("decay 0.97", dict(D, decay=0.97)); run("decay 0.995", dict(D, decay=0.995))
df = pd.DataFrame(rows)
for w in ["2019-22", "2023-25"]: df[f"delta_{w}"] = df[f"team_mae_{w}"] - df.loc[0, f"team_mae_{w}"]
df["verdict"] = ["base" if i == 0 else ("helps both" if d1 < -0.001 and d2 < -0.001 else ("helps one" if d1 < -0.001 or d2 < -0.001 else "no")) for i, (d1, d2) in enumerate(zip(df["delta_2019-22"], df["delta_2023-25"]))]
df.to_csv("reports/player_knobs.csv", index=False); print(df[["variant", "delta_2019-22", "delta_2023-25", "verdict"]].to_string()); print("DONE")
