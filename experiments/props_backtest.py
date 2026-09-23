"""Backtest of the player projections (nflmodel/props.py), walk-forward 2019 to 2025, both windows. For every
player-game with at least one touch, the projection built only from the previous 17 games of the player, his team
and the opponent, against the actual yards. Baselines: his plain yards per game; volume x his overall rate (no
matchup). Then the matchup steps one at a time: yards per touch in the opponent's mix; moved toward what the
defense allows at weights 0.25, 0.5 (the page today), 1.0. Mean absolute error in yards per player-game, and the
error of a trivial "league average per touch" projection for scale. Output reports/props_backtest.csv."""
import numpy as np, pandas as pd
from nflmodel.model import OUT
N, MIN_SPLIT, MIN_VOL = 17, 15, 8
d = pd.read_parquet(OUT / "scheme_plays.parquet"); d = d[d.play_type.isin(["pass", "run"]) & (d.season >= 2016)].copy()
d["yards_gained"] = d.yards_gained.fillna(0.0)
def roll(df, keys, cols):
    """Per group, the sum over the previous N games (game rows sorted by season, week), nothing from the current one."""
    a = df.groupby(keys + ["season", "week", "game_id"])[cols].sum().reset_index().sort_values(keys + ["season", "week"])
    prev = a.groupby(keys)[cols].transform(lambda s: s.rolling(N, min_periods=1).sum().shift(1))
    cnt = a.groupby(keys).cumcount().clip(upper=N)   # games in the window
    return pd.concat([a[keys + ["season", "week", "game_id"]], prev, cnt.rename("games_prev")], axis=1)
WIN = {"2019-22": (2019, 2022), "2023-25": (2023, 2025)}
def evaluate(frame, actual, variants):
    out = {}
    for w, (a, b) in WIN.items():
        x = frame[frame.season.between(a, b)]
        out[w] = {k: round(float((x[k] - x[actual]).abs().mean()), 2) for k in variants}; out[w]["n"] = int(len(x))
    return out
rows = []
# ---------------- receivers ----------------
t = d[d.pass_play & d.receiver_player_id.notna()].copy()
t["tgt"] = 1; t["man_n"] = t.man.astype(int); t["man_y"] = np.where(t.man, t.yards_gained, 0.0); t["zone_n"] = t.zone.astype(int); t["zone_y"] = np.where(t.zone, t.yards_gained, 0.0)
pg = t.groupby(["receiver_player_id", "posteam", "season", "week", "game_id"]).agg(tgt=("tgt", "sum"), yds=("yards_gained", "sum"), man_n=("man_n", "sum"), man_y=("man_y", "sum"), zone_n=("zone_n", "sum"), zone_y=("zone_y", "sum")).reset_index()
R = roll(pg.rename(columns={"receiver_player_id": "pid"}), ["pid"], ["tgt", "yds", "man_n", "man_y", "zone_n", "zone_y"])
tp = d[d.pass_play].groupby(["posteam", "season", "week", "game_id"]).size().rename("team_pass").reset_index()
T = roll(tp, ["posteam"], ["team_pass"]).rename(columns={"posteam": "team"})
# the player's share = his targets over his teams' pass plays in his games: approximate with his targets over his own team's pass plays in the same window games (same team in nearly every case)
pg2 = pg.merge(tp.rename(columns={"team_pass": "tp_game"}), on=["posteam", "season", "week", "game_id"], how="left")
S = roll(pg2.rename(columns={"receiver_player_id": "pid"}), ["pid"], ["tgt", "tp_game"]).rename(columns={"tgt": "tgt_s", "tp_game": "tp_s"})
dp = d[d.pass_play].copy(); dp["cov_n"] = dp.cov_known.astype(int); dp["man_calls"] = dp.man.astype(int); dp["tgt"] = 1
dg = dp.groupby(["defteam", "season", "week", "game_id"]).agg(tgt=("tgt", "sum"), yds=("yards_gained", "sum"), cov_n=("cov_n", "sum"), man_calls=("man_calls", "sum")).reset_index()
D = roll(dg, ["defteam"], ["tgt", "yds", "cov_n", "man_calls"]).rename(columns={"tgt": "d_tgt", "yds": "d_yds"})
g = d[["game_id", "posteam", "defteam"]].drop_duplicates()
f = pg.rename(columns={"receiver_player_id": "pid"})[["pid", "posteam", "season", "week", "game_id", "tgt", "yds"]].rename(columns={"tgt": "act_tgt", "yds": "act_yds"})
f = f.merge(R[["pid", "game_id", "tgt", "yds", "man_n", "man_y", "zone_n", "zone_y", "games_prev"]], on=["pid", "game_id"]).merge(S[["pid", "game_id", "tgt_s", "tp_s"]], on=["pid", "game_id"])
f = f.merge(g, on=["game_id", "posteam"]).merge(T[["team", "game_id", "team_pass", "games_prev"]].rename(columns={"team": "posteam", "games_prev": "tgames"}), on=["posteam", "game_id"]).merge(D[["defteam", "game_id", "d_tgt", "d_yds", "cov_n", "man_calls"]], on=["defteam", "game_id"])
f = f[(f.tgt >= MIN_VOL) & (f.games_prev >= 3) & (f.tgames >= 3)].copy()
lg_ypt = float(d[d.pass_play].yards_gained.mean())
f["ypt"] = f.yds / f.tgt; f["ypg"] = f.yds / f.games_prev; f["share"] = f.tgt_s / f.tp_s.replace(0, np.nan); f["vol"] = f.share * f.team_pass / f.tgames
f["ypt_man"] = np.where(f.man_n >= MIN_SPLIT, f.man_y / f.man_n.replace(0, np.nan), np.nan); f["ypt_zone"] = np.where(f.zone_n >= MIN_SPLIT, f.zone_y / f.zone_n.replace(0, np.nan), np.nan)
f["d_man"] = np.where(f.cov_n >= 50, f.man_calls / f.cov_n.replace(0, np.nan), np.nan); f["d_ypt"] = np.where(f.d_tgt >= 100, f.d_yds / f.d_tgt.replace(0, np.nan), np.nan)
mix = f.ypt_man * f.d_man + f.ypt_zone * (1 - f.d_man); f["ypt_mix"] = np.where(mix.notna(), mix, f.ypt)
adj = lambda base, w: base * np.where(f.d_ypt.notna(), 1 + w * (f.d_ypt / lg_ypt - 1), 1.0)
f["p_league"] = f.vol * lg_ypt; f["p_avg"] = f.ypg; f["p_vol_rate"] = f.vol * f.ypt; f["p_mix"] = f.vol * f.ypt_mix
f["p_mix_d25"] = adj(f.vol * f.ypt_mix, 0.25); f["p_mix_d50"] = adj(f.vol * f.ypt_mix, 0.5); f["p_mix_d100"] = adj(f.vol * f.ypt_mix, 1.0); f["p_rate_d50"] = adj(f.vol * f.ypt, 0.5)
V = ["p_league", "p_avg", "p_vol_rate", "p_mix", "p_rate_d50", "p_mix_d25", "p_mix_d50", "p_mix_d100"]
ev = evaluate(f, "act_yds", V); print("receiving yards MAE", ev, flush=True)
for k in V: rows.append({"stat": "rec_yards", "variant": k, **{f"mae_{w}": ev[w][k] for w in WIN}, **{f"n_{w}": ev[w]["n"] for w in WIN}})
# volume alone: projected targets against actual targets
f["p_tgt_share"] = f.vol; f["p_tgt_avg"] = f.tgt / f.games_prev
ev = evaluate(f, "act_tgt", ["p_tgt_avg", "p_tgt_share"]); print("targets MAE", ev, flush=True)
for k in ["p_tgt_avg", "p_tgt_share"]: rows.append({"stat": "targets", "variant": k, **{f"mae_{w}": ev[w][k] for w in WIN}, **{f"n_{w}": ev[w]["n"] for w in WIN}})
# ---------------- rushers ----------------
r = d[d.play_type.eq("run") & d.rusher_player_id.notna()].copy(); r["car"] = 1
r["heavy_n"] = (r.box >= 8).astype(int); r["heavy_y"] = np.where(r.box >= 8, r.yards_gained, 0.0); r["light_n"] = (r.box <= 6).astype(int); r["light_y"] = np.where(r.box <= 6, r.yards_gained, 0.0); r["known"] = r.box.notna().astype(int)
pr = r.groupby(["rusher_player_id", "posteam", "season", "week", "game_id"]).agg(car=("car", "sum"), yds=("yards_gained", "sum"), heavy_n=("heavy_n", "sum"), heavy_y=("heavy_y", "sum"), light_n=("light_n", "sum"), light_y=("light_y", "sum")).reset_index()
RR = roll(pr.rename(columns={"rusher_player_id": "pid"}), ["pid"], ["car", "yds", "heavy_n", "heavy_y", "light_n", "light_y"])
tr = r.groupby(["posteam", "season", "week", "game_id"]).size().rename("team_run").reset_index(); TR_ = roll(tr, ["posteam"], ["team_run"])
pr2 = pr.merge(tr.rename(columns={"team_run": "tr_game"}), on=["posteam", "season", "week", "game_id"], how="left"); SR = roll(pr2.rename(columns={"rusher_player_id": "pid"}), ["pid"], ["car", "tr_game"]).rename(columns={"car": "car_s", "tr_game": "tr_s"})
drg = r.groupby(["defteam", "season", "week", "game_id"]).agg(car=("car", "sum"), yds=("yards_gained", "sum"), heavy_n=("heavy_n", "sum"), known=("known", "sum")).reset_index(); DR = roll(drg, ["defteam"], ["car", "yds", "heavy_n", "known"]).rename(columns={"car": "d_car", "yds": "d_yds"})
h = pr.rename(columns={"rusher_player_id": "pid"})[["pid", "posteam", "season", "week", "game_id", "car", "yds"]].rename(columns={"car": "act_car", "yds": "act_yds"})
h = h.merge(RR[["pid", "game_id", "car", "yds", "heavy_n", "heavy_y", "light_n", "light_y", "games_prev"]], on=["pid", "game_id"]).merge(SR[["pid", "game_id", "car_s", "tr_s"]], on=["pid", "game_id"])
h = h.merge(g, on=["game_id", "posteam"]).merge(TR_[["posteam", "game_id", "team_run", "games_prev"]].rename(columns={"games_prev": "tgames"}), on=["posteam", "game_id"]).merge(DR[["defteam", "game_id", "d_car", "d_yds", "heavy_n", "known"]].rename(columns={"heavy_n": "d_heavy", "known": "d_known"}), on=["defteam", "game_id"])
h = h[(h.car >= MIN_VOL) & (h.games_prev >= 3) & (h.tgames >= 3)].copy()
lg_ypc = float(r.yards_gained.mean())
h["ypc"] = h.yds / h.car; h["ypg"] = h.yds / h.games_prev; h["vol"] = (h.car_s / h.tr_s.replace(0, np.nan)) * h.team_run / h.tgames
h["ypc_heavy"] = np.where(h.heavy_n >= MIN_SPLIT, h.heavy_y / h.heavy_n.replace(0, np.nan), np.nan); h["ypc_light"] = np.where(h.light_n >= MIN_SPLIT, h.light_y / h.light_n.replace(0, np.nan), np.nan)
h["d_hv"] = np.where(h.d_known >= 30, h.d_heavy / h.d_known.replace(0, np.nan), np.nan); h["d_ypc"] = np.where(h.d_car >= 100, h.d_yds / h.d_car.replace(0, np.nan), np.nan)
mixr = h.ypc_heavy * h.d_hv + h.ypc_light * (1 - h.d_hv); h["ypc_mix"] = np.where(mixr.notna(), mixr, h.ypc)
adjr = lambda base, w: base * np.where(h.d_ypc.notna(), 1 + w * (h.d_ypc / lg_ypc - 1), 1.0)
h["p_league"] = h.vol * lg_ypc; h["p_avg"] = h.ypg; h["p_vol_rate"] = h.vol * h.ypc; h["p_mix"] = h.vol * h.ypc_mix; h["p_rate_d50"] = adjr(h.vol * h.ypc, 0.5); h["p_mix_d25"] = adjr(h.vol * h.ypc_mix, 0.25); h["p_mix_d50"] = adjr(h.vol * h.ypc_mix, 0.5); h["p_mix_d100"] = adjr(h.vol * h.ypc_mix, 1.0)
ev = evaluate(h, "act_yds", V); print("rushing yards MAE", ev, flush=True)
for k in V: rows.append({"stat": "rush_yards", "variant": k, **{f"mae_{w}": ev[w][k] for w in WIN}, **{f"n_{w}": ev[w]["n"] for w in WIN}})
# ---------------- passers ----------------
q = d[d.dropback & d.passer_player_id.notna()].copy(); q["db"] = 1; q["pr_n"] = (q.pressure == 1).astype(int); q["pr_y"] = np.where(q.pressure == 1, q.yards_gained, 0.0); q["cl_n"] = (q.pressure == 0).astype(int); q["cl_y"] = np.where(q.pressure == 0, q.yards_gained, 0.0)
pq = q.groupby(["passer_player_id", "posteam", "season", "week", "game_id"]).agg(db=("db", "sum"), yds=("yards_gained", "sum"), pr_n=("pr_n", "sum"), pr_y=("pr_y", "sum"), cl_n=("cl_n", "sum"), cl_y=("cl_y", "sum")).reset_index()
RQ = roll(pq.rename(columns={"passer_player_id": "pid"}), ["pid"], ["db", "yds", "pr_n", "pr_y", "cl_n", "cl_y"])
td = q.groupby(["posteam", "season", "week", "game_id"]).size().rename("team_db").reset_index(); TQ = roll(td, ["posteam"], ["team_db"])
dq = q.groupby(["defteam", "season", "week", "game_id"]).agg(db=("db", "sum"), yds=("yards_gained", "sum"), pr_n=("pr_n", "sum"), known=("pressure", "count")).reset_index(); DQ = roll(dq, ["defteam"], ["db", "yds", "pr_n", "known"]).rename(columns={"db": "d_db", "yds": "d_yds", "pr_n": "d_pr"})
k = pq.rename(columns={"passer_player_id": "pid"})[["pid", "posteam", "season", "week", "game_id", "db", "yds"]].rename(columns={"db": "act_db", "yds": "act_yds"})
k = k.merge(RQ[["pid", "game_id", "db", "yds", "pr_n", "pr_y", "cl_n", "cl_y", "games_prev"]], on=["pid", "game_id"]).merge(g, on=["game_id", "posteam"]).merge(TQ[["posteam", "game_id", "team_db", "games_prev"]].rename(columns={"games_prev": "tgames"}), on=["posteam", "game_id"]).merge(DQ[["defteam", "game_id", "d_db", "d_yds", "d_pr", "known"]], on=["defteam", "game_id"])
k = k[(k.db >= MIN_VOL * 3) & (k.games_prev >= 3) & (k.tgames >= 3) & (k.act_db >= 10)].copy()
lg_ypd = float(q.yards_gained.mean())
k["ypd"] = k.yds / k.db; k["ypg"] = k.yds / k.games_prev; k["vol"] = k.team_db / k.tgames
k["ypd_pr"] = np.where(k.pr_n >= MIN_SPLIT, k.pr_y / k.pr_n.replace(0, np.nan), np.nan); k["ypd_cl"] = np.where(k.cl_n >= MIN_SPLIT, k.cl_y / k.cl_n.replace(0, np.nan), np.nan)
k["d_prr"] = np.where(k.known >= 50, k.d_pr / k.known.replace(0, np.nan), np.nan); k["d_ypd"] = np.where(k.d_db >= 100, k.d_yds / k.d_db.replace(0, np.nan), np.nan)
mixq = k.ypd_pr * k.d_prr + k.ypd_cl * (1 - k.d_prr); k["ypd_mix"] = np.where(mixq.notna(), mixq, k.ypd)
adjq = lambda base, w: base * np.where(k.d_ypd.notna(), 1 + w * (k.d_ypd / lg_ypd - 1), 1.0)
k["p_league"] = k.vol * lg_ypd; k["p_avg"] = k.ypg; k["p_vol_rate"] = k.vol * k.ypd; k["p_mix"] = k.vol * k.ypd_mix; k["p_rate_d50"] = adjq(k.vol * k.ypd, 0.5); k["p_mix_d25"] = adjq(k.vol * k.ypd_mix, 0.25); k["p_mix_d50"] = adjq(k.vol * k.ypd_mix, 0.5); k["p_mix_d100"] = adjq(k.vol * k.ypd_mix, 1.0)
ev = evaluate(k, "act_yds", V); print("passing yards MAE", ev, flush=True)
for k_ in V: rows.append({"stat": "pass_yards", "variant": k_, **{f"mae_{w}": ev[w][k_] for w in WIN}, **{f"n_{w}": ev[w]["n"] for w in WIN}})
pd.DataFrame(rows).to_csv("reports/props_backtest.csv", index=False); print(pd.DataFrame(rows).to_string()); print("DONE")

# ---------------- second pass: the player's rate shrunk toward the league, with and without the defense (23 Sep 2026) ----------------
rows2 = []
def shrink_pass(frame, n_col, y_col, lg, adjf, actual, stat, ks):
    for kk in ks:
        rate = (frame[y_col] + kk * lg) / (frame[n_col] + kk)
        frame[f"s{kk}"] = frame.vol * rate; frame[f"s{kk}_d25"] = adjf(frame.vol * rate, 0.25); frame[f"s{kk}_d50"] = adjf(frame.vol * rate, 0.5)
    names = [f"s{kk}{sfx}" for kk in ks for sfx in ("", "_d25", "_d50")]
    ev = evaluate(frame, actual, names); print(stat, "shrunk", ev, flush=True)
    for nm in names: rows2.append({"stat": stat, "variant": nm, **{f"mae_{w}": ev[w][nm] for w in WIN}})
shrink_pass(f, "tgt", "yds", lg_ypt, adj, "act_yds", "rec_yards", [25, 50, 100, 200, 400])
shrink_pass(h, "car", "yds", lg_ypc, adjr, "act_yds", "rush_yards", [25, 50, 100, 200, 400])
shrink_pass(k, "db", "yds", lg_ypd, adjq, "act_yds", "pass_yards", [50, 100, 200, 400, 800])
pd.concat([pd.DataFrame(rows), pd.DataFrame(rows2)], ignore_index=True).to_csv("reports/props_backtest.csv", index=False); print(pd.DataFrame(rows2).to_string()); print("DONE2")
