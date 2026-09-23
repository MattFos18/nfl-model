"""A new head coach early in the season, on the same logic as roster turnover: last year's rating describes a
different regime. Flag = head coach differs from the team's coach in last season's final game, weeks 1 to 8; own
and opponent. Both windows against the twenty-input model. Output reports/new_coach.csv."""
import pandas as pd
from nflmodel import model as M
from nflmodel.model import OUT
from experiments.common import both
games = pd.read_parquet(OUT / "games.parquet")
long = pd.concat([games[["game_id", "season", "week", "home_team", "home_coach"]].rename(columns={"home_team": "team", "home_coach": "coach"}),
                  games[["game_id", "season", "week", "away_team", "away_coach"]].rename(columns={"away_team": "team", "away_coach": "coach"})]).sort_values(["season", "week"])
last_coach = long[long.game_id.map(games.set_index("game_id").home_score).notna()].groupby(["season", "team"]).coach.last()
long["new_coach"] = [float(isinstance(c, str) and last_coach.get((s - 1, t)) is not None and c != last_coach.get((s - 1, t))) for s, t, c in zip(long.season, long.team, long.coach)]
f = M.with_trends(pd.read_parquet(OUT / "features_asof.parquet")).merge(long[["game_id", "team", "new_coach"]], on=["game_id", "team"], how="left")
f = f.merge(long[["game_id", "team", "new_coach"]].rename(columns={"team": "opp", "new_coach": "opp_new_coach"}), on=["game_id", "opp"], how="left")
early = (f.week <= 8).astype(float); f["new_coach_early"] = f.new_coach.fillna(0) * early; f["opp_new_coach_early"] = f.opp_new_coach.fillna(0) * early
print("team-games with a new coach, weeks 1-8:", int(f.new_coach_early.sum()), flush=True)
B = M.FEATS.copy(); rows = []
for name, feats in {"base (20)": B, "+ own new coach": B + ["new_coach_early"], "+ opponent new coach": B + ["opp_new_coach_early"], "+ both": B + ["new_coach_early", "opp_new_coach_early"]}.items():
    M.FEATS = feats; r = both(f); M.FEATS = B
    rows.append({"variant": name, **{f"{k}_{w}": v for w, d in r.items() for k, v in d.items()}}); print(name, {w: (r[w]["team_mae"], r[w]["margin_mae"], r[w]["ats5"]) for w in r}, flush=True)
pd.DataFrame(rows).to_csv("reports/new_coach.csv", index=False); print("DONE")
