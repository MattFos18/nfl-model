"""Two refinements of the offseason-turnover inputs: (a) a QB change early in the season (this week's starter is not
last season's main starter), since the team's offense rating still carries last year's QB; (b) turnover weighted
by value (the skill players' EPA per touch above replacement) instead of raw snaps. Both windows against the
twenty-input model. Output reports/turnover2.csv."""
import numpy as np, pandas as pd
from nflmodel import model as M, players as PL
from nflmodel.model import OUT
from experiments.common import both
games = pd.read_parquet(OUT / "games.parquet"); qb = pd.read_parquet(OUT / "qb_games.parquet")
f = M.with_trends(pd.read_parquet(OUT / "features_asof.parquet"))
# (a) last season's main starter per team = most dropbacks; this week's starter = features qb_id (schedule's or carried)
main_qb = qb.groupby(["season", "team", "qb_id"]).dropbacks.sum().reset_index().sort_values("dropbacks").groupby(["season", "team"]).qb_id.last()
f["qb_changed"] = [float(isinstance(q, str) and main_qb.get((s - 1, t)) is not None and q != main_qb.get((s - 1, t))) for s, t, q in zip(f.season, f.team, f.qb_id)]
f["qb_changed_early"] = f.qb_changed * (f.week <= 8).astype(float)
print("team-games with a changed QB, weeks 1-8:", int(f.qb_changed_early.sum()), flush=True)
# (b) value-weighted turnover: share of last season's skill value (EPA per touch above replacement x touches) still on the roster
pg = pd.read_parquet(OUT / "player_games.parquet"); pv = PL.PlayerValues(pg, PL.DEFAULT["decay"], PL.DEFAULT["k"])
from nflmodel.positions import norm
from nflmodel.features import RAW, TEAM_FIX
ros = []
for s in range(2013, 2027):
    rf = RAW / "rosters" / f"roster_weekly_{s}.parquet"
    if rf.exists():
        r = pd.read_parquet(rf, columns=["season", "week", "team", "gsis_id", "status"]); r["team"] = r.team.replace(TEAM_FIX); ros.append(r[r.status == "ACT"])
ros = pd.concat(ros, ignore_index=True); roster_ids = {k: set(g.gsis_id.dropna()) for k, g in ros.groupby(["season", "week", "team"])}
skill = pg[pg.role.isin(PL.SKILL)]
val_cache = {}
def value_share(season, week, team):
    ids = roster_ids.get((season, week, team)); last = skill[(skill.season == season - 1) & (skill.team == team)]
    if ids is None or len(last) == 0: return np.nan
    tot, kept = 0.0, 0.0
    for pid, g in last.groupby("player_id"):
        key = (pid, season)
        if key not in val_cache:
            v = 0.0
            for role in PL.SKILL:
                gr = g[g.role == role]
                if len(gr): v += max(pv.value(pid, role, season, 1)[0] - pv.prior(role, season), 0.0) * float(gr.plays.sum())
            val_cache[key] = v
        tot += val_cache[key]; kept += val_cache[key] if pid in ids else 0.0
    return kept / tot if tot > 0 else np.nan
f["val_cont"] = [value_share(r.season, r.week, r.team) if r.week <= 8 else 1.0 for r in f[["season", "week", "team"]].itertuples()]
f["val_cont"] = f.val_cont.fillna(f.val_cont.median()); f["off_value_turnover_early"] = (1 - f.val_cont) * (f.week <= 8).astype(float)
print("value turnover", f[f.week <= 8].off_value_turnover_early.describe().round(3).to_dict(), flush=True)
B = M.FEATS.copy(); rows = []
for name, feats in {"base (20)": B, "+ QB changed early": B + ["qb_changed_early"], "+ value-weighted offensive turnover": B + ["off_value_turnover_early"],
                    "value-weighted replacing snap turnover": [c for c in B if c != "off_turnover_early"] + ["off_value_turnover_early"]}.items():
    M.FEATS = feats; r = both(f); M.FEATS = B
    rows.append({"variant": name, **{f"{k}_{w}": v for w, d in r.items() for k, v in d.items()}}); print(name, {w: (r[w]["team_mae"], r[w]["margin_mae"], r[w]["ats5"]) for w in r}, flush=True)
pd.DataFrame(rows).to_csv("reports/turnover2.csv", index=False); print("DONE")
