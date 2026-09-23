"""Second round of the player-projection backtest (23 Sep 2026), after reading how books and projection shops build
prop lines: baseline from long-term and recent form, role and usage, the game's expected plays and pass rate from
the spread and total (game script), then matchup adjustments by position and scheme. Each layer is added to the
rule that won round one (rate shrunk toward the league, moved a little toward the defense; volume from usage share
x the team's plays per game) and judged on both windows by mean absolute error in yards per player-game.
Layers: A recency (decayed windows instead of flat 17 games); B game script (expected pass plays and runs from the
closing spread and total); C defense by position (yards allowed per target to WR, TE, RB); D coverage-specific
usage (target share against man and zone weighted by the defense's man rate); E route mix x what the defense allows
per route; F the head coach's pass rate over expected; G yards per target split into catch rate, depth of target
and yards after catch, each shrunk on its own. Output reports/props_backtest2.csv."""
import numpy as np, pandas as pd
from nflmodel.model import OUT
from nflmodel.features import RAW
N, MIN_SPLIT, MIN_VOL = 17, 15, 8
WIN = {"2019-22": (2019, 2022), "2023-25": (2023, 2025)}
d = pd.read_parquet(OUT / "scheme_plays.parquet"); d = d[d.play_type.isin(["pass", "run"]) & (d.season >= 2016)].copy(); d["yards_gained"] = d.yards_gained.fillna(0.0)
games = pd.read_parquet(OUT / "games.parquet")[["game_id", "season", "week", "home_team", "away_team", "spread_line", "total_line", "home_coach", "away_coach"]]
# routes and position
part = pd.concat([pd.read_parquet(f, columns=["nflverse_game_id", "play_id", "route"]) for f in sorted(RAW.glob("participation/pbp_participation_*.parquet"))]).rename(columns={"nflverse_game_id": "game_id"}).drop_duplicates(["game_id", "play_id"])
d = d.merge(part, on=["game_id", "play_id"], how="left"); d["route"] = d.route.fillna("").replace("", "NONE")
from nflmodel.positions import names_by_id
names = names_by_id(range(2014, 2027)); pos_of = {pid: v[1] for pid, v in names.items()}
def prev_sums(a, keys, cols, decay=None):
    """Per group in game order, the sum over the previous N games (flat) or decayed sums over every previous game."""
    a = a.sort_values(keys + ["season", "week"]).reset_index(drop=True)
    out = a[keys + ["season", "week", "game_id"]].copy()
    if decay is None:
        prev = a.groupby(keys)[cols].transform(lambda s: s.rolling(N, min_periods=1).sum().shift(1)); out[cols] = prev.values
    else:
        vals = a[cols].values.astype(float); res = np.zeros_like(vals); gk = a[keys].astype(str).agg("|".join, axis=1).values
        run = np.zeros(vals.shape[1]); last = None
        for i in range(len(a)):
            if gk[i] != last: run = np.zeros(vals.shape[1]); last = gk[i]
            res[i] = run; run = decay * run + vals[i]
        out[cols] = res
    out["games_prev"] = a.groupby(keys).cumcount().clip(upper=N).values
    return out
def evaluate(frame, actual, variants):
    res = {}
    for w, (a, b) in WIN.items():
        x = frame[frame.season.between(a, b)]; res[w] = {k: round(float((x[k] - x[actual]).abs().mean()), 2) for k in variants}; res[w]["n"] = int(len(x))
    return res
rows = []
def rec(stat, names_, ev):
    for k in names_: rows.append({"stat": stat, "variant": k, **{f"mae_{w}": ev[w][k] for w in WIN}, **{f"n_{w}": ev[w]["n"] for w in WIN}})
# ======================= receivers =======================
t = d[d.pass_play & d.receiver_player_id.notna()].copy(); t["tgt"] = 1; t["catch"] = t.complete_pass.fillna(0).astype(float); t["ay"] = t.air_yards.fillna(0.0); t["yac"] = np.where(t.complete_pass.fillna(0) == 1, t.yards_gained - t.air_yards.fillna(0.0), 0.0)
t["man_t"] = t.man.astype(int); t["zone_t"] = t.zone.astype(int)
pg = t.groupby(["receiver_player_id", "posteam", "season", "week", "game_id"]).agg(tgt=("tgt", "sum"), yds=("yards_gained", "sum"), catch=("catch", "sum"), ay=("ay", "sum"), yac=("yac", "sum"), man_t=("man_t", "sum"), zone_t=("zone_t", "sum")).reset_index().rename(columns={"receiver_player_id": "pid"})
tp = d[d.pass_play].groupby(["posteam", "season", "week", "game_id"]).agg(team_pass=("play_id", "size")).reset_index()
tcov = d[d.pass_play & d.cov_known].groupby(["posteam", "season", "week", "game_id"]).agg(team_man=("man", "sum"), team_zone=("zone", "sum")).reset_index()
pg = pg.merge(tp, on=["posteam", "season", "week", "game_id"], how="left").merge(tcov, on=["posteam", "season", "week", "game_id"], how="left").fillna({"team_man": 0, "team_zone": 0})
cols = ["tgt", "yds", "catch", "ay", "yac", "man_t", "zone_t", "team_pass", "team_man", "team_zone"]
R17 = prev_sums(pg, ["pid"], cols); R90 = prev_sums(pg, ["pid"], cols, decay=0.90); R95 = prev_sums(pg, ["pid"], cols, decay=0.95)
tpg = d[d.pass_play].groupby(["posteam", "season", "week", "game_id"]).size().rename("tp").reset_index(); trg = d[d.play_type.eq("run")].groupby(["posteam", "season", "week", "game_id"]).size().rename("tr").reset_index()
tv = tpg.merge(trg, on=["posteam", "season", "week", "game_id"], how="outer").fillna(0); T17 = prev_sums(tv, ["posteam"], ["tp", "tr"]).rename(columns={"posteam": "team"})
# defense: overall and by position of the target; by route
t["pos"] = t.receiver_player_id.map(pos_of).fillna("WR"); t["pos"] = np.where(t.pos.isin(["WR", "TE", "RB"]), t.pos, np.where(t.pos.isin(["FB", "HB"]), "RB", "WR"))
dg = t.groupby(["defteam", "season", "week", "game_id"]).agg(d_tgt=("tgt", "sum"), d_yds=("yards_gained", "sum")).reset_index()
for p_ in ["WR", "TE", "RB"]:
    x = t[t.pos == p_].groupby(["defteam", "season", "week", "game_id"]).agg(**{f"d_tgt_{p_}": ("tgt", "sum"), f"d_yds_{p_}": ("yards_gained", "sum")}).reset_index(); dg = dg.merge(x, on=["defteam", "season", "week", "game_id"], how="left")
ROUTES = ["QUICK OUT", "HITCH/CURL", "GO", "SCREEN", "IN/DIG", "DEEP OUT", "SHALLOW CROSS/DRAG", "SLANT", "POST", "SWING", "CORNER"]
for r_ in ROUTES:
    x = t[t.route == r_].groupby(["defteam", "season", "week", "game_id"]).agg(**{f"dr_n_{r_}": ("tgt", "sum"), f"dr_y_{r_}": ("yards_gained", "sum")}).reset_index(); dg = dg.merge(x, on=["defteam", "season", "week", "game_id"], how="left")
dg = dg.fillna(0); D17 = prev_sums(dg, ["defteam"], [c for c in dg.columns if c.startswith("d_") or c.startswith("dr_")])
dcov = d[d.pass_play & d.cov_known].groupby(["defteam", "season", "week", "game_id"]).agg(cov_n=("man", "size"), man_calls=("man", "sum")).reset_index(); DC = prev_sums(dcov, ["defteam"], ["cov_n", "man_calls"])
# player route mix
for r_ in ROUTES:
    pg[f"pr_n_{r_}"] = 0
prt = t.groupby(["receiver_player_id", "game_id", "route"]).size().unstack(fill_value=0); prt.columns = [f"pr_n_{c}" for c in prt.columns]; prt = prt.reset_index().rename(columns={"receiver_player_id": "pid"})
pgr = pg[["pid", "posteam", "season", "week", "game_id"]].merge(prt, on=["pid", "game_id"], how="left").fillna(0); PR17 = prev_sums(pgr, ["pid"], [c for c in pgr.columns if c.startswith("pr_n_") and c[5:] in ROUTES])
# head coach pass rate over expected (season-to-date and last season, by coach)
g2 = games.copy(); hc = pd.concat([g2[["game_id", "home_team", "home_coach"]].rename(columns={"home_team": "posteam", "home_coach": "coach"}), g2[["game_id", "away_team", "away_coach"]].rename(columns={"away_team": "posteam", "away_coach": "coach"})])
neu = d[d.neutral & d.xpass.notna()].copy(); neu["p"] = neu.pass_play.astype(float); cg = neu.groupby(["posteam", "season", "week", "game_id"]).agg(np_=("p", "size"), pr=("p", "sum"), xp=("xpass", "sum")).reset_index().merge(hc, on=["game_id", "posteam"], how="left")
cg["coach"] = cg.coach.fillna(cg.posteam); CH = prev_sums(cg, ["coach"], ["np_", "pr", "xp"], decay=0.97).rename(columns={"np_": "c_n", "pr": "c_pr", "xp": "c_xp"})
# the frame
f = pg[["pid", "posteam", "season", "week", "game_id", "tgt", "yds"]].rename(columns={"tgt": "act_tgt", "yds": "act_yds"})
f = f.merge(R17[["pid", "game_id", "games_prev"] + cols], on=["pid", "game_id"]).merge(games[["game_id", "home_team", "spread_line", "total_line"]], on="game_id")
f = f.merge(d[["game_id", "posteam", "defteam"]].drop_duplicates(), on=["game_id", "posteam"]).merge(T17[["team", "game_id", "tp", "tr", "games_prev"]].rename(columns={"team": "posteam", "games_prev": "tgames"}), on=["posteam", "game_id"])
f = f.merge(D17.drop(columns=["season", "week", "games_prev"]), on=["defteam", "game_id"]).merge(DC[["defteam", "game_id", "cov_n", "man_calls"]], on=["defteam", "game_id"])
f = f.merge(R90[["pid", "game_id"] + cols].rename(columns={c: c + "_90" for c in cols}), on=["pid", "game_id"]).merge(R95[["pid", "game_id"] + cols].rename(columns={c: c + "_95" for c in cols}), on=["pid", "game_id"])
f = f.merge(PR17.drop(columns=["season", "week", "games_prev"]), on=["pid", "game_id"], how="left").merge(cg[["game_id", "posteam", "coach"]], on=["game_id", "posteam"], how="left").merge(CH[["coach", "game_id", "c_n", "c_pr", "c_xp"]], on=["coach", "game_id"], how="left")
f = f[(f.tgt >= MIN_VOL) & (f.games_prev >= 3) & (f.tgames >= 3)].copy(); f["pos"] = f.pid.map(pos_of).fillna("WR"); f["pos"] = np.where(f.pos.isin(["WR", "TE", "RB"]), f.pos, "WR")
lg_ypt = float(t.yards_gained.mean()); lg_catch = float(t.catch.mean()); lg_ay = float(t.ay.mean()); lg_yac_pc = float(t.yac.sum() / max(t.catch.sum(), 1))
f["home"] = (f.posteam == f.home_team).astype(int); f["margin_exp"] = np.where(f.home == 1, f.spread_line, -f.spread_line)
f["share"] = f.tgt / f.team_pass.replace(0, np.nan); f["vol"] = f.share * f.tp / f.tgames
f["d_ypt"] = np.where(f.d_tgt >= 100, f.d_yds / f.d_tgt.replace(0, np.nan), np.nan)
base_rate = (f.yds + 100 * lg_ypt) / (f.tgt + 100); adjD = lambda base, w: base * np.where(f.d_ypt.notna(), 1 + w * (f.d_ypt / lg_ypt - 1), 1.0)
f["v1"] = adjD(f.vol * base_rate, 0.25)
# A: recency
for tag in ["90", "95"]:
    sh = f[f"tgt_{tag}"] / f[f"team_pass_{tag}"].replace(0, np.nan); rate = (f[f"yds_{tag}"] + 100 * lg_ypt) / (f[f"tgt_{tag}"] + 100)
    f[f"A_{tag}"] = adjD(sh * f.tp / f.tgames * rate, 0.25)
    f[f"A_{tag}_vol"] = adjD(sh * f.tp / f.tgames * base_rate, 0.25)   # decayed usage only
# B: game script. Fit team pass plays per game = rolling avg + b1 * expected margin + b2 * (total - league total), on 2016 to 2018 only, then apply forward
tvf = tv.merge(games[["game_id", "home_team", "spread_line", "total_line"]], on="game_id").merge(T17[["team", "game_id", "tp", "tr", "games_prev"]].rename(columns={"team": "posteam", "tp": "tp_prev", "tr": "tr_prev"}), on=["posteam", "game_id"])
tvf = tvf[(tvf.games_prev >= 3) & tvf.spread_line.notna() & tvf.total_line.notna()].copy(); tvf["me"] = np.where(tvf.posteam == tvf.home_team, tvf.spread_line, -tvf.spread_line); lg_total = float(games.total_line.mean())
tvf["tot_c"] = tvf.total_line - lg_total; tvf["tp_avg"] = tvf.tp_prev / tvf.games_prev; tvf["tr_avg"] = tvf.tr_prev / tvf.games_prev
fit = tvf[tvf.season <= 2018]; X = np.c_[np.ones(len(fit)), fit.me, fit.tot_c]; bp = np.linalg.lstsq(X, fit.tp - fit.tp_avg, rcond=None)[0]; br = np.linalg.lstsq(X, fit.tr - fit.tr_avg, rcond=None)[0]
print("game script fit on 2016-18: pass plays = avg", np.round(bp, 3), "(per point of expected margin, per point of total); runs", np.round(br, 3), flush=True)
f["tot_c"] = f.total_line - lg_total; f["tp_gs"] = f.tp / f.tgames + bp[0] + bp[1] * f.margin_exp.fillna(0) + bp[2] * f.tot_c.fillna(0)
f["B"] = adjD(f.share * f.tp_gs * base_rate, 0.25)
# C: defense by position
for p_ in ["WR", "TE", "RB"]:
    f[f"d_ypt_{p_}"] = np.where(f[f"d_tgt_{p_}"] >= 60, f[f"d_yds_{p_}"] / f[f"d_tgt_{p_}"].replace(0, np.nan), np.nan)
lg_pos = {p_: float(t[t.pos == p_].yards_gained.mean()) for p_ in ["WR", "TE", "RB"]}
dpos = np.select([f.pos == "WR", f.pos == "TE", f.pos == "RB"], [f.d_ypt_WR / lg_pos["WR"], f.d_ypt_TE / lg_pos["TE"], f.d_ypt_RB / lg_pos["RB"]], np.nan)
f["C25"] = f.vol * base_rate * np.where(np.isnan(dpos), 1.0, 1 + 0.25 * (dpos - 1)); f["C50"] = f.vol * base_rate * np.where(np.isnan(dpos), 1.0, 1 + 0.5 * (dpos - 1))
# D: coverage-specific usage: his share of his team's man-covered targets and zone-covered targets, weighted by the defense's man rate
f["d_man"] = np.where(f.cov_n >= 50, f.man_calls / f.cov_n.replace(0, np.nan), np.nan)
sh_man = np.where(f.team_man >= 40, f.man_t / f.team_man.replace(0, np.nan), np.nan); sh_zone = np.where(f.team_zone >= 40, f.zone_t / f.team_zone.replace(0, np.nan), np.nan)
sh_cov = sh_man * f.d_man + sh_zone * (1 - f.d_man); f["D"] = adjD(np.where(np.isnan(sh_cov), f.share, sh_cov) * f.tp / f.tgames * base_rate, 0.25)
f["D_half"] = adjD(np.where(np.isnan(sh_cov), f.share, 0.5 * sh_cov + 0.5 * f.share) * f.tp / f.tgames * base_rate, 0.25)
# E: route mix x what the defense allows per route (relative to the league per route), as the rate multiplier
lg_route = {r_: float(t[t.route == r_].yards_gained.mean()) for r_ in ROUTES}
num = np.zeros(len(f)); den = np.zeros(len(f))
for r_ in ROUTES:
    n_ = f[f"pr_n_{r_}"].fillna(0).values; dn = f[f"dr_n_{r_}"].values; dy = f[f"dr_y_{r_}"].values
    d_rel = np.where(dn >= 40, (dy / np.where(dn == 0, 1, dn)) / lg_route[r_], 1.0); num += n_ * d_rel; den += n_
route_mult = np.where(den >= 20, num / np.where(den == 0, 1, den), 1.0)
f["E25"] = f.vol * base_rate * (1 + 0.25 * (route_mult - 1)); f["E50"] = f.vol * base_rate * (1 + 0.5 * (route_mult - 1)); f["E100"] = f.vol * base_rate * route_mult
# F: coach pass rate over expected shifts the team's pass plays
f["c_proe"] = np.where(f.c_n >= 200, (f.c_pr - f.c_xp) / f.c_n.replace(0, np.nan), np.nan)
f["F"] = adjD(f.share * (f.tp / f.tgames) * (1 + np.where(np.isnan(f.c_proe), 0.0, f.c_proe)) * base_rate, 0.25)
# G: yards per target = catch rate x (depth + yards after catch per catch), each shrunk
catch_s = (f.catch + 60 * lg_catch) / (f.tgt + 60); ay_s = (f.ay + 40 * lg_ay) / (f.tgt + 40); yac_s = (f.yac + 60 * lg_yac_pc) / (f.catch + 60)
f["G"] = adjD(f.vol * (catch_s * ay_s + catch_s * yac_s), 0.25)
f["G2"] = adjD(f.vol * (catch_s * (ay_s + yac_s)), 0.25) if False else f["G"]
# combos of what helps
V = ["v1", "A_90", "A_95", "A_90_vol", "A_95_vol", "B", "C25", "C50", "D", "D_half", "E25", "E50", "E100", "F", "G"]
ev = evaluate(f, "act_yds", V); print("receiving", ev, flush=True); rec("rec_yards", V, ev)
ev2 = evaluate(f.assign(vol_v1=f.vol, vol_B=f.share * f.tp_gs, vol_A95=f.tgt_95 / f.team_pass_95.replace(0, np.nan) * f.tp / f.tgames), "act_tgt", ["vol_v1", "vol_B", "vol_A95"]); print("targets", ev2, flush=True); rec("targets", ["vol_v1", "vol_B", "vol_A95"], ev2)
pd.DataFrame(rows).to_csv("reports/props_backtest2.csv", index=False); print(pd.DataFrame(rows).to_string()); print("DONE")
