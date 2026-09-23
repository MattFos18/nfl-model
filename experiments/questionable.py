"""Players listed Questionable are counted as available today. About half of them sit. Weight a Questionable
player's value out by 0.3 or 0.5, and a Questionable player who did not practice all week by 0.7, in the skill
value out (own and opponent). Both windows against the twenty-input model. Output reports/questionable.csv."""
import numpy as np, pandas as pd
from nflmodel import model as M, players as PL
from nflmodel.model import OUT
from experiments.common import both
games = pd.read_parquet(OUT / "games.parquet"); pg = pd.read_parquet(OUT / "player_games.parquet")
inj = PL.load_injuries(range(2013, 2027)); inj = inj[inj.position != "QB"]
out_by = {k: set(g.gsis_id.dropna()) for k, g in inj[inj.report_status.isin(["Out", "Doubtful"])].groupby(["season", "week", "team"])}
for k, ids in PL.unavailable_by_week(range(2013, 2027)).items():
    out_by[k] = out_by.get(k, set()) | ids
q = inj[inj.report_status == "Questionable"]
q_by = {k: set(g.gsis_id.dropna()) for k, g in q.groupby(["season", "week", "team"])}
qdnp_by = {k: set(g.gsis_id.dropna()) for k, g in q[q.practice_status.fillna("").str.startswith("Did Not")].groupby(["season", "week", "team"])}
pv = PL.PlayerValues(pg, PL.DEFAULT["decay"], PL.DEFAULT["k"]); _, by_player, _ = PL._usage_frames(pg)
cache = {}
def val(pid, s, w):
    k = (pid, s, w)
    if k not in cache: cache[k] = PL.player_value_out(pv, by_player, pid, s, w, 8)["value"]
    return cache[k]
long = pd.concat([games[["game_id", "season", "week", "home_team"]].rename(columns={"home_team": "team"}), games[["game_id", "season", "week", "away_team"]].rename(columns={"away_team": "team"})]); long = long[long.season >= 2013]
rows = []
for r in long.itertuples():
    k = (r.season, r.week, r.team); outs = out_by.get(k, set()); qs = q_by.get(k, set()) - outs; qd = qdnp_by.get(k, set()) - outs
    base = sum(val(p, r.season, r.week) for p in outs); qv = sum(val(p, r.season, r.week) for p in qs); qdv = sum(val(p, r.season, r.week) for p in qd)
    rows.append({"game_id": r.game_id, "team": r.team, "v0": base, "vq": qv, "vqd": qdv})
X = pd.DataFrame(rows)
f = M.with_trends(pd.read_parquet(OUT / "features_asof.parquet")).drop(columns=["skill_out_value", "opp_skill_out_value"])
f = f.merge(X, on=["game_id", "team"], how="left").merge(X.rename(columns={"team": "opp", "v0": "o0", "vq": "oq", "vqd": "oqd"}), on=["game_id", "opp"], how="left")
for c in ["v0", "vq", "vqd", "o0", "oq", "oqd"]: f[c] = f[c].fillna(0.0)
B = M.FEATS.copy(); res = []
for name, wq, wd in [("Questionable = available (current)", 0.0, 0.0), ("Questionable x 0.3", 0.3, 0.0), ("Questionable x 0.5", 0.5, 0.0), ("Questionable x 0.3, DNP all week x 0.7", 0.3, 0.4), ("Questionable x 0.5, DNP x 0.8", 0.5, 0.3)]:
    f["skill_out_value"] = f.v0 + wq * f.vq + wd * f.vqd; f["opp_skill_out_value"] = f.o0 + wq * f.oq + wd * f.oqd
    r = both(f); res.append({"variant": name, **{f"{k}_{w}": v for w, d in r.items() for k, v in d.items()}}); print(name, {w: (r[w]["team_mae"], r[w]["margin_mae"], r[w]["ats5"]) for w in r}, flush=True)
pd.DataFrame(res).to_csv("reports/questionable.csv", index=False); print("DONE")
