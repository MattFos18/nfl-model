"""Special teams and the kicking game as inputs, both windows against the eighteen-input model:
  - team special-teams EPA rating (kickoffs, punts, field goals, extra points; the play's EPA to the team it helped),
    decayed like the other ratings, own and opponent;
  - the kicker's and punter's value above replacement (positions.py handles), own.
Output reports/special_teams.csv."""
import numpy as np, pandas as pd, pyarrow.parquet as pq
from nflmodel import model as M, ratings as R, players as PL
from nflmodel.features import RAW, OUT, TEAM_FIX
from experiments.common import both
# special-teams EPA per team-game
frames = []
for s in range(2012, 2027):
    f = RAW / "pbp" / f"play_by_play_{s}.parquet"
    if f.exists():
        frames.append(pd.read_parquet(f, columns=["game_id", "season", "week", "posteam", "defteam", "play_type", "epa"]))
p = pd.concat(frames, ignore_index=True); p = p[p.play_type.isin(["kickoff", "punt", "field_goal", "extra_point"]) & p.posteam.notna() & p.defteam.notna()].copy()
for c in ["posteam", "defteam"]: p[c] = p[c].replace(TEAM_FIX)
p["epa"] = pd.to_numeric(p.epa, errors="coerce").fillna(0.0)
a = p.groupby(["game_id", "season", "week", "posteam"]).epa.sum().rename("st").reset_index().rename(columns={"posteam": "team"})
b = p.groupby(["game_id", "season", "week", "defteam"]).epa.sum().rename("st").reset_index().rename(columns={"defteam": "team"}); b["st"] = -b.st
st = pd.concat([a, b]).groupby(["game_id", "season", "week", "team"]).st.sum().reset_index()
print("team-games with ST EPA", len(st), "mean", round(st.st.mean(), 3), "sd", round(st.st.std(), 3), flush=True)
# as-of rating: the same window as the other ratings (decay per week, last season at half weight), plain weighted mean
def st_rating(season, week):
    rows, w = R.window(st, season, week, R.DEFAULT["decay"], R.DEFAULT["prior"])
    if len(rows) == 0: return {}
    d = rows.assign(w=w); g = d.groupby("team").apply(lambda x: (x.st * x.w).sum() / (x.w.sum() + 4.0))   # +4 games of pull toward 0
    return g.to_dict()
f = M.with_trends(pd.read_parquet(OUT / "features_asof.parquet"))
cache = {}; own, opp = [], []
for r in f[["season", "week", "team", "opp"]].itertuples():
    k = (r.season, r.week)
    if k not in cache: cache[k] = st_rating(r.season, r.week)
    own.append(cache[k].get(r.team, 0.0)); opp.append(cache[k].get(r.opp, 0.0))
f["st_rating"] = own; f["opp_st_rating"] = opp
# kicker and punter value as of each game (positions.py values need the kicking table)
kg = pd.read_parquet(OUT / "kicking_games.parquet"); pv = PL.PlayerValues(kg, 0.99, 40.0)
last_k = {}
kk = kg.sort_values(["season", "week"])
for r in f[["game_id", "season", "week", "team"]].itertuples():
    pass
# team's kicker for a game: the one who kicked most in the team's previous game with kicks
kt = kk[kk.role == "kicker"].groupby(["team", "season", "week"]).apply(lambda x: x.sort_values("plays").player_id.iloc[-1]).rename("kid").reset_index()
pt = kk[kk.role == "punter"].groupby(["team", "season", "week"]).apply(lambda x: x.sort_values("plays").player_id.iloc[-1]).rename("pid").reset_index()
def prev_id(tbl, col, team, season, week):
    h = tbl[(tbl.team == team) & ((tbl.season < season) | ((tbl.season == season) & (tbl.week < week)))]
    return h[col].iloc[-1] if len(h) else None
kv, pvv = [], []
for r in f[["season", "week", "team"]].itertuples():
    kid = prev_id(kt, "kid", r.team, r.season, r.week); pid = prev_id(pt, "pid", r.team, r.season, r.week)
    kv.append(pv.value(kid, "kicker", r.season, r.week)[0] - pv.prior("kicker", r.season) if kid else 0.0)
    pvv.append(pv.value(pid, "punter", r.season, r.week)[0] - pv.prior("punter", r.season) if pid else 0.0)
f["kicker_value"] = kv; f["punter_value"] = pvv
f.to_parquet(OUT / "special_teams_asof.parquet", index=False)
B = M.FEATS.copy(); rows = []
for name, feats in {"base (18)": B, "+ own special-teams rating": B + ["st_rating"], "+ own and opponent special-teams rating": B + ["st_rating", "opp_st_rating"],
                    "+ kicker value": B + ["kicker_value"], "+ punter value": B + ["punter_value"], "+ kicker + punter": B + ["kicker_value", "punter_value"],
                    "+ special teams (own, opp) + kicker": B + ["st_rating", "opp_st_rating", "kicker_value"]}.items():
    M.FEATS = feats; rr = both(f); M.FEATS = B
    rows.append({"variant": name, **{f"{k}_{w}": v for w, d in rr.items() for k, v in d.items()}}); print(name, {w: (rr[w]["team_mae"], rr[w]["margin_mae"], rr[w]["ats5"]) for w in rr}, flush=True)
pd.DataFrame(rows).to_csv("reports/special_teams.csv", index=False); print("DONE")
