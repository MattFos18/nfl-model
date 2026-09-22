"""Player model phase 4 tests, both windows against the eighteen-input model:
  - defenders' impact value out (own defense and the opponent's), beside the snap-weighted absences already in;
  - offensive linemen's on/off value out (own and opponent);
  - availability-weighted skill offense: the value of every regular who is playing, not only who is out.
Output reports/positions.csv."""
import numpy as np, pandas as pd
from nflmodel import model as M, positions as P, players as PL
from nflmodel.model import OUT
from experiments.common import both
games = pd.read_parquet(OUT / "games.parquet"); seasons = range(2013, 2027)
dg = pd.read_parquet(OUT / "defender_games.parquet"); pg = pd.read_parquet(OUT / "player_games.parquet")
names = P.names_by_id(range(2012, 2027)); snaps = P.snaps_by_game(seasons); tg = pd.read_parquet(OUT / "team_games.parquet")
inj = PL.load_injuries(seasons); inj = inj[inj.report_status.isin(["Out", "Doubtful"])]
out_by = {k: set(g.gsis_id.dropna()) for k, g in inj.groupby(["season", "week", "team"])}
for k, ids in PL.unavailable_by_week(seasons).items():
    out_by[k] = out_by.get(k, set()) | ids
pv_def = PL.PlayerValues(dg, 0.99, 300.0); pv_skill = PL.PlayerValues(pg, PL.DEFAULT["decay"], PL.DEFAULT["k"]); _, by_player, by_team = PL._usage_frames(pg)
def_by = {pid: g for pid, g in dg.groupby("player_id")}
team_dsn = snaps.groupby(["game_id", "team"]).defense_snaps.max()
key_of = {pid: P.norm(v[0]) for pid, v in names.items()}
long = pd.concat([games[["game_id", "season", "week", "home_team"]].rename(columns={"home_team": "team"}), games[["game_id", "season", "week", "away_team"]].rename(columns={"away_team": "team"})])
long = long[long.season >= 2013]
# fast on/off for linemen who are out: per team, the game -> EPA per play map and, per lineman, the games he played 50%+
tg_epa = {t: g.sort_values(["season", "week"])[["game_id", "season", "week", "epa_play"]] for t, g in tg[tg.epa_play.notna()].groupby("team")}
ol_on = {k: set(g.game_id) for k, g in snaps[snaps.position.isin(P.OL_POS) & (snaps.offense_pct >= 0.5)].groupby(["team", "key"])}
ol_share = {k: float(g.sort_values(["season", "week"]).offense_pct.tail(8).mean()) for k, g in snaps[snaps.position.isin(P.OL_POS)].groupby(["team", "key"])}
val_cache = {}
def skill_val(pid, season, week):
    key = (pid, season, week)
    if key not in val_cache:
        val_cache[key] = PL.player_value_out(pv_skill, by_player, pid, season, week, 8)["value"]
    return val_cache[key]
rows = []
for r in long.itertuples():
    outs = out_by.get((r.season, r.week, r.team), set())
    dv = 0.0
    for pid in outs:
        g = def_by.get(pid)
        if g is None: continue
        h = g[(g.season < r.season) | ((g.season == r.season) & (g.week < r.week))].tail(8)
        if len(h) == 0: continue
        v, n = pv_def.value(pid, "defender", r.season, r.week); pr = pv_def.prior("defender", r.season)
        tsn = team_dsn.reindex([(gid, r.team) for gid in h.game_id]).mean()
        share = float(h.plays.mean() / tsn) if tsn and not np.isnan(tsn) else 0.0
        dv += (v - pr) * min(share, 1.0)
    olv = 0.0
    te = tg_epa.get(r.team)
    if te is not None and outs:
        win = te[(te.season < r.season) | ((te.season == r.season) & (te.week < r.week))].tail(34)
        for pid in outs:
            k_ = (r.team, key_of.get(pid)); on = ol_on.get(k_)
            if on is None: continue
            with_ = win[win.game_id.isin(on)].epa_play; without = win[~win.game_id.isin(on)].epa_play
            if len(with_) == 0 or len(without) == 0: continue
            n_eff = len(with_) * len(without) / (len(with_) + len(without))
            olv += float(with_.mean() - without.mean()) * n_eff / (n_eff + 8.0) * ol_share.get(k_, 0.0)
    g = by_team.get(r.team); av = 0.0
    if g is not None:
        h = g[(g.season < r.season) | ((g.season == r.season) & (g.week < r.week))]
        ids = h.game_id.drop_duplicates().tail(8); h = h[h.game_id.isin(ids)]
        for pid in h.player_id.unique():
            if pid in outs: continue
            av += skill_val(pid, r.season, r.week)
    rows.append({"game_id": r.game_id, "team": r.team, "def_value_out": dv, "ol_value_out": olv, "skill_avail_value": av})
    if len(rows) % 1000 == 0: print(len(rows), flush=True)
X = pd.DataFrame(rows); X.to_parquet(OUT / "positions_asof.parquet", index=False)
f = M.with_trends(pd.read_parquet(OUT / "features_asof.parquet")).merge(X, on=["game_id", "team"], how="left")
f = f.merge(X.rename(columns={"team": "opp", "def_value_out": "opp_def_value_out", "ol_value_out": "opp_ol_value_out", "skill_avail_value": "opp_skill_avail_value"}), on=["game_id", "opp"], how="left")
for c in ["def_value_out", "ol_value_out", "skill_avail_value", "opp_def_value_out", "opp_ol_value_out", "opp_skill_avail_value"]:
    f[c] = f[c].fillna(0.0)
B = M.FEATS.copy(); res = []
V = {"base (18)": B, "+ opponent defenders' value out": B + ["opp_def_value_out"], "+ own defenders' value out (for pa side, via opp)": B + ["def_value_out"],
     "+ own linemen on/off out": B + ["ol_value_out"], "+ opponent linemen out": B + ["opp_ol_value_out"],
     "+ availability-weighted skill offense": B + ["skill_avail_value"], "availability-weighted replacing value out": [c for c in B if c != "skill_out_value"] + ["skill_avail_value"],
     "+ opponent defenders' value out + own linemen out": B + ["opp_def_value_out", "ol_value_out"]}
for name, feats in V.items():
    M.FEATS = feats; rr = both(f); M.FEATS = B
    res.append({"variant": name, **{f"{k}_{w}": v for w, d in rr.items() for k, v in d.items()}}); print(name, {w: (rr[w]["team_mae"], rr[w]["margin_mae"], rr[w]["ats5"]) for w in rr}, flush=True)
pd.DataFrame(res).to_csv("reports/positions.csv", index=False); print("DONE")
