"""Two further uses of the scheme tags, both windows. (1) The QB under pressure and against the blitz: his own
decayed, shrunk EPA per dropback in each look, matched to the opponent's pressure and blitz rates (as of the game
from the opponent's previous 17 charted games), against his overall rating: does the fit help team points?
(2) Totals: tempo and tendency sums (no-huddle, pass rate over expected, motion, the defenses' pressure and man
rates) added to the totals equation. Output reports/scheme_qb_totals.csv."""
import numpy as np, pandas as pd
from nflmodel import model as M, scheme as S, backtest as B
from nflmodel.model import OUT
from experiments.common import both, WINDOWS, GAMES, score
games = pd.read_parquet(OUT / "games.parquet"); season = int(games.season.max())
d = S.load_plays(range(2016, season + 1)); d.to_parquet(OUT / "scheme_plays.parquet", index=False); print("plays", d.shape, flush=True)
d = d[d.play_type.isin(["pass", "run"])].copy(); db = d.dropback; ps = d.pass_play
# --- QB splits: per QB-game, dropbacks and EPA under pressure / clean, blitzed / not (known tags only) ---
q = d[db & d.passer_player_id.notna()].copy()
for name, m in {"press": q.pressure == 1, "clean": q.pressure == 0, "blitz": q.blitz == 1, "noblitz": q.blitz == 0}.items():
    q[f"{name}_n"] = m.astype(int); q[f"{name}_epa"] = np.where(m, q.epa, 0.0)
qg = q.groupby(["passer_player_id", "season", "week", "game_id"])[[c for c in q.columns if c.endswith("_n") or c.endswith("_epa")]].sum().reset_index().sort_values(["passer_player_id", "season", "week"])
lg = {k: float(q[f"{k}_epa"].sum() / max(q[f"{k}_n"].sum(), 1)) for k in ["press", "clean", "blitz", "noblitz"]}; print("league", {k: round(v, 3) for k, v in lg.items()}, flush=True)
K, DEC = 150.0, 0.985
def qb_split(pid, s_, w_, k):
    h = qg[(qg.passer_player_id == pid) & ((qg.season < s_) | ((qg.season == s_) & (qg.week < w_)))]
    if not len(h): return lg[k]
    wts = DEC ** np.arange(len(h))[::-1]; n = float((h[f"{k}_n"].values * wts).sum()); e = float((h[f"{k}_epa"].values * wts).sum())
    return (e + K * lg[k]) / (n + K)
# --- opponent rates and tempo sums per team-game, as of the game from the previous 17 games ---
N = 17
def per_game(side):
    team = d.posteam if side == "off" else d.defteam
    g = pd.DataFrame({"game_id": d.game_id, "season": d.season, "week": d.week, "team": team})
    g["cov_n"] = (ps & d.cov_known).astype(int); g["man"] = (ps & d.man).astype(int); g["press_n"] = (db & d.pressure.notna()).astype(int); g["press"] = (db & (d.pressure == 1)).astype(int)
    g["blitz_n"] = (db & d.blitz.notna()).astype(int); g["blitz"] = (db & (d.blitz == 1)).astype(int); g["nh_n"] = d.is_no_huddle.notna().astype(int); g["nh"] = (d.is_no_huddle == 1).astype(int)
    g["mo_n"] = d.is_motion.notna().astype(int); g["mo"] = (d.is_motion == 1).astype(int); g["neu_n"] = d.neutral.astype(int); g["neu_pass"] = (d.neutral & ps).astype(int); g["xp"] = np.where(d.neutral & d.xpass.notna(), d.xpass, 0.0); g["xp_n"] = (d.neutral & d.xpass.notna()).astype(int)
    g["plays"] = 1
    a = g.groupby(["team", "season", "week", "game_id"]).sum(numeric_only=True).reset_index().sort_values(["team", "season", "week"])
    cols = [c for c in a.columns if c not in ("team", "season", "week", "game_id")]
    prev = a.groupby("team")[cols].transform(lambda s: s.rolling(N, min_periods=1).sum().shift(1))
    return pd.concat([a[["team", "season", "week", "game_id"]], prev], axis=1)
off, dfn = per_game("off"), per_game("def")
r = lambda x, a, b, mn=30: np.where(x[b] >= mn, x[a] / x[b].replace(0, np.nan), np.nan)
D = dfn[["game_id", "team"]].copy(); D["d_press"] = r(dfn, "press", "press_n"); D["d_blitz"] = r(dfn, "blitz", "blitz_n"); D["d_man"] = r(dfn, "man", "cov_n")
O = off[["game_id", "team"]].copy(); O["o_nh"] = r(off, "nh", "nh_n"); O["o_mo"] = r(off, "mo", "mo_n"); O["o_poe"] = r(off, "neu_pass", "neu_n") - np.where(off.xp_n >= 30, off.xp / off.xp_n.replace(0, np.nan), np.nan)
f0 = M.with_trends(pd.read_parquet(OUT / "features_asof.parquet"))
f = f0.merge(O, on=["game_id", "team"], how="left").merge(D.rename(columns={"team": "opp"}), on=["game_id", "opp"], how="left")
qid = f.qb_id if "qb_id" in f.columns else None
print("qb ids present", qid is not None and qid.notna().mean() > 0.5, flush=True)
f["qb_press"] = [qb_split(p_, s_, w_, "press") for p_, s_, w_ in zip(f.qb_id, f.season, f.week)]
f["qb_clean"] = [qb_split(p_, s_, w_, "clean") for p_, s_, w_ in zip(f.qb_id, f.season, f.week)]
f["qb_blitz"] = [qb_split(p_, s_, w_, "blitz") for p_, s_, w_ in zip(f.qb_id, f.season, f.week)]
f["qb_noblitz"] = [qb_split(p_, s_, w_, "noblitz") for p_, s_, w_ in zip(f.qb_id, f.season, f.week)]
lp, lb = float(D.d_press.mean()), float(D.d_blitz.mean())
f["qb_press_fit"] = (f.qb_press * f.d_press.fillna(lp) + f.qb_clean * (1 - f.d_press.fillna(lp))) - (f.qb_press * lp + f.qb_clean * (1 - lp))   # the opponent's pressure rate against an average one, for this QB
f["qb_blitz_fit"] = (f.qb_blitz * f.d_blitz.fillna(lb) + f.qb_noblitz * (1 - f.d_blitz.fillna(lb))) - (f.qb_blitz * lb + f.qb_noblitz * (1 - lb))
f["qb_press_gap"] = f.qb_press - f.qb_clean   # how much pressure hurts this QB
print("fit spread", f[["qb_press_fit", "qb_blitz_fit", "qb_press_gap"]].describe().round(4).to_string(), flush=True)
rows = []; base_feats = M.FEATS.copy()
def row(name, res): return {"added": name, **{f"{k}_{w}": v for w, dd in res.items() for k, v in dd.items()}}
base = both(f); rows.append(row("(none)", base)); print("base", {w: (base[w]["team_mae"], base[w]["total_mae"], base[w]["ats4"]) for w in base}, flush=True)
def run(name, cols):
    M.FEATS = base_feats + cols; res = both(f); M.FEATS = base_feats; rows.append(row(name, res))
    print(name, {w: (round(res[w]["team_mae"] - base[w]["team_mae"], 4), round(res[w]["margin_mae"] - base[w]["margin_mae"], 4), res[w]["ats4"]) for w in res}, flush=True)
run("QB pressure fit (his pressure and clean EPA x the opponent's pressure rate)", ["qb_press_fit"])
run("QB blitz fit", ["qb_blitz_fit"])
run("QB pressure gap (pressure EPA minus clean)", ["qb_press_gap"])
run("QB pressure and blitz fits", ["qb_press_fit", "qb_blitz_fit"])
# --- totals: tempo and tendency sums in the totals equation ---
orig_frame, orig_feats = M._game_frame, list(M.TOTAL_FEATS)
for c in ["o_nh", "o_mo", "o_poe", "d_press", "d_man"]:
    f[c] = f[c].fillna(f[c].mean())
def frame_plus(ff):
    g = orig_frame(ff); h = ff[ff.home == 1].set_index("game_id"); a = ff[ff.home == 0].set_index("game_id"); ids = g.index
    for c in ["o_nh", "o_mo", "o_poe", "d_press", "d_man"]:
        g[f"{c}_sum"] = (h.loc[ids, c] + a.loc[ids, c]).values
    return g
M._game_frame = frame_plus
def run_total(name, cols):
    M.TOTAL_FEATS = orig_feats + cols; res = both(f); M.TOTAL_FEATS = orig_feats; rows.append(row(name, res))
    print(name, {w: (round(res[w]["total_mae"] - base[w]["total_mae"], 4)) for w in res}, flush=True)
run_total("totals: no-huddle sum", ["o_nh_sum"]); run_total("totals: pass rate over expected sum", ["o_poe_sum"]); run_total("totals: motion sum", ["o_mo_sum"])
run_total("totals: defenses' pressure rate sum", ["d_press_sum"]); run_total("totals: defenses' man rate sum", ["d_man_sum"]); run_total("totals: all five", ["o_nh_sum", "o_poe_sum", "o_mo_sum", "d_press_sum", "d_man_sum"])
M._game_frame = orig_frame
df = pd.DataFrame(rows)
for w in ["2019-22", "2023-25"]:
    df[f"delta_{w}"] = (df[f"team_mae_{w}"] - df.loc[0, f"team_mae_{w}"]).round(4); df[f"delta_total_{w}"] = (df[f"total_mae_{w}"] - df.loc[0, f"total_mae_{w}"]).round(4)
df["verdict"] = ["base" if i == 0 else ("helps both" if a < -0.001 and b < -0.001 else ("helps one" if a < -0.001 or b < -0.001 else "no")) for i, (a, b) in enumerate(zip(np.where(df.added.str.startswith("totals"), df["delta_total_2019-22"], df["delta_2019-22"]), np.where(df.added.str.startswith("totals"), df["delta_total_2023-25"], df["delta_2023-25"])))]
df.to_csv("reports/scheme_qb_totals.csv", index=False); print(df[["added", "delta_2019-22", "delta_2023-25", "delta_total_2019-22", "delta_total_2023-25", "verdict"]].to_string()); print("DONE")
