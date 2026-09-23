"""Round four of the player-projection backtest (23 Sep 2026): layers a book adds that rounds two and three did not
test, each added to the adopted rule (usage decayed 0.85, game script, rate shrunk toward the league and moved toward
the defense, median factor): wind at kickoff on receiving and passing yards; the opponent's pace (its allowed plays
per game blended with the team's own); the quarterback's as-of rating for receivers, as a level and as the change
from the QBs he had over his window (a backup in for the starter); the player's own long-run rate as the shrinkage
prior instead of the league's; home and away; and a re-tune of the shrinkage weight K and the defense weight W on the
adopted rule. Every constant is fitted on 2016 to 2018 only; scored on both windows. Output reports/props_backtest4.csv."""
import numpy as np, pandas as pd
from nflmodel.model import OUT
N, MIN_VOL = 17, 8
WIN = {"2019-22": (2019, 2022), "2023-25": (2023, 2025)}
DECAY, MED = 0.85, {"rec": 0.88, "rush": 0.84, "pass": 0.90}
GS = {"tp": (-0.5969, -0.046, 0.1636), "tr": (0.3413, 0.103, -0.1713), "tdb": (-0.5967, -0.0461, 0.1638)}; GS_TOTAL = 43.5674
d = pd.read_parquet(OUT / "scheme_plays.parquet"); d = d[d.play_type.isin(["pass", "run"]) & (d.season >= 2016)].copy(); d["yards_gained"] = d.yards_gained.fillna(0.0)
games = pd.read_parquet(OUT / "games.parquet")[["game_id", "home_team", "away_team", "spread_line", "total_line"]]
feat = pd.read_parquet(OUT / "features_asof.parquet", columns=["game_id", "team", "qb_rating", "wind", "dome"]); feat["wind"] = np.where(feat.dome > 0, 0.0, feat.wind.fillna(0.0)); QB_MEAN = float(feat[feat.game_id.str[:4].astype(int).between(2016, 2018)].qb_rating.mean())
def prev_sums(a, keys, cols, decay=None):
    a = a.sort_values(keys + ["season", "week"]).reset_index(drop=True); out = a[keys + ["season", "week", "game_id"]].copy()
    if decay is None:
        out[cols] = a.groupby(keys)[cols].transform(lambda s: s.rolling(N, min_periods=1).sum().shift(1)).values
    else:
        vals = a[cols].values.astype(float); res = np.zeros_like(vals); gk = a[keys].astype(str).agg("|".join, axis=1).values; run = np.zeros(vals.shape[1]); last = None
        for i in range(len(a)):
            if gk[i] != last: run = np.zeros(vals.shape[1]); last = gk[i]
            res[i] = run; run = decay * run + vals[i]
        out[cols] = res
    out["games_prev"] = a.groupby(keys).cumcount().clip(upper=N).values; return out
def evaluate(frame, actual, variants):
    res = {}
    for w, (a, b) in WIN.items():
        x = frame[frame.season.between(a, b)]; res[w] = {k: round(float((x[k] - x[actual]).abs().mean()), 2) for k in variants}; res[w]["n"] = int(len(x))
    return res
def fit_grid(frame, make, grid, actual="act_yds"):
    """The grid value that minimises absolute error on 2016 to 2018; make(c) returns the projection column."""
    fit = frame[frame.season <= 2018]; errs = [float((make(c)[fit.index] - fit[actual]).abs().mean()) for c in grid]; return float(grid[int(np.argmin(errs))]), round(min(errs), 3)
rows = []
def rec(stat, names_, ev, extra=None):
    for k in names_: rows.append({"stat": stat, "variant": k, **{f"mae_{w}": ev[w][k] for w in WIN}, **{f"n_{w}": ev[w]["n"] for w in WIN}, **(extra or {})})
tv = d[d.pass_play].groupby(["posteam", "defteam", "season", "week", "game_id"]).size().rename("tp").reset_index().merge(d[d.play_type.eq("run")].groupby(["posteam", "defteam", "season", "week", "game_id"]).size().rename("tr").reset_index(), how="outer").merge(d[d.dropback].groupby(["posteam", "defteam", "season", "week", "game_id"]).size().rename("tdb").reset_index(), how="outer").fillna(0)
T17 = prev_sums(tv, ["posteam"], ["tp", "tr", "tdb"])
ALW = prev_sums(tv.rename(columns={"tp": "a_tp", "tr": "a_tr", "tdb": "a_tdb"}), ["defteam"], ["a_tp", "a_tr", "a_tdb"]).rename(columns={"games_prev": "agames"})
def build(kind):
    if kind == "rec":
        t = d[d.pass_play & d.receiver_player_id.notna()].rename(columns={"receiver_player_id": "pid"}); vcol = "tp"; lg = float(d[d.pass_play].yards_gained.mean()); K = 100; W = 0.25
    elif kind == "rush":
        t = d[d.play_type.eq("run") & d.rusher_player_id.notna()].rename(columns={"rusher_player_id": "pid"}); vcol = "tr"; lg = float(d[d.play_type.eq("run")].yards_gained.mean()); K = 25; W = 0.25
    else:
        t = d[d.dropback & d.passer_player_id.notna()].rename(columns={"passer_player_id": "pid"}); vcol = "tdb"; lg = float(d[d.dropback].yards_gained.mean()); K = 50; W = 0.5
    t = t.copy(); t["n"] = 1
    pg = t.groupby(["pid", "posteam", "season", "week", "game_id"]).agg(n=("n", "sum"), yds=("yards_gained", "sum")).reset_index().merge(tv[["posteam", "season", "week", "game_id", vcol]].rename(columns={vcol: "team_n"}), on=["posteam", "season", "week", "game_id"], how="left")
    pg = pg.merge(feat.rename(columns={"team": "posteam"})[["game_id", "posteam", "qb_rating"]], on=["game_id", "posteam"], how="left"); pg["qbr"] = pg.qb_rating.fillna(QB_MEAN); pg["one"] = 1.0
    cols = ["n", "yds", "team_n"]; R = prev_sums(pg, ["pid"], cols); R85 = prev_sums(pg, ["pid"], cols + ["qbr", "one"], decay=DECAY).rename(columns={c: c + "_85" for c in cols + ["qbr", "one"]}); R95 = prev_sums(pg, ["pid"], ["n", "yds"], decay=0.95).rename(columns={"n": "n_95", "yds": "yds_95"})
    dg = t.groupby(["defteam", "season", "week", "game_id"]).agg(d_n=("n", "sum"), d_yds=("yards_gained", "sum")).reset_index(); D = prev_sums(dg, ["defteam"], ["d_n", "d_yds"])
    f = pg[["pid", "posteam", "season", "week", "game_id", "n", "yds", "qbr"]].rename(columns={"n": "act_n", "yds": "act_yds", "qbr": "qb_now"})
    f = f.merge(R[["pid", "game_id", "games_prev"] + cols], on=["pid", "game_id"]).merge(R85[["pid", "game_id"] + [c + "_85" for c in cols + ["qbr", "one"]]], on=["pid", "game_id"]).merge(R95[["pid", "game_id", "n_95", "yds_95"]], on=["pid", "game_id"])
    f = f.merge(games, on="game_id").merge(d[["game_id", "posteam", "defteam"]].drop_duplicates(), on=["game_id", "posteam"]).merge(T17[["posteam", "game_id", vcol, "games_prev"]].rename(columns={vcol: "tv", "games_prev": "tgames"}), on=["posteam", "game_id"]).merge(D[["defteam", "game_id", "d_n", "d_yds"]], on=["defteam", "game_id"]).merge(ALW[["defteam", "game_id", "a_" + vcol, "agames"]].rename(columns={"a_" + vcol: "alw"}), on=["defteam", "game_id"])
    f = f.merge(feat.rename(columns={"team": "posteam"})[["game_id", "posteam", "wind"]], on=["game_id", "posteam"], how="left"); f["wind"] = f.wind.fillna(0.0); f["home"] = (f.posteam == f.home_team).astype(float)
    minv = MIN_VOL * (3 if kind == "pass" else 1); f = f[(f.n >= minv) & (f.games_prev >= 3) & (f.tgames >= 3) & (f.agames >= 3)].copy()
    if kind == "pass": f = f[f.act_n >= 10]
    f["me"] = np.where(f.posteam == f.home_team, f.spread_line, -f.spread_line).astype(float); f["tc"] = f.total_line - GS_TOTAL
    f["d_rate"] = np.where(f.d_n >= 100, f.d_yds / f.d_n.replace(0, np.nan), np.nan)
    def adj(base, w=W): return base * np.where(f.d_rate.notna(), 1 + w * (f.d_rate / lg - 1), 1.0)
    def rate_k(k): return (f.yds + k * lg) / (f.n + k)
    b = GS[vcol]; team_pg = f.tv / f.tgames; gs_add = b[0] + b[1] * f.me.fillna(0) + b[2] * f.tc.fillna(0)
    share = 1.0 if kind == "pass" else f.n_85 / f.team_n_85.replace(0, np.nan)
    def vol(team_vol): return share * (team_vol + gs_add)
    base = adj(vol(team_pg) * rate_k(K)); f["base"] = MED[kind] * base
    # wind (receiving and passing only)
    if kind != "rush":
        wx = np.maximum(f.wind - 10, 0); cw, ew = fit_grid(f, lambda c: f.base * (1 + c * wx), np.arange(-0.03, 0.0001, 0.0025)); f["wind10"] = f.base * (1 + cw * wx); f.attrs["wind_c"] = cw
        wl, el = fit_grid(f, lambda c: f.base * (1 + c * f.wind), np.arange(-0.02, 0.0001, 0.002)); f["windlin"] = f.base * (1 + wl * f.wind); f.attrs["windlin_c"] = wl
    # opponent pace: blend the opponent's allowed plays per game into the team's
    for p in [0.25, 0.5]:
        f[f"pace{int(p*100)}"] = MED[kind] * adj(vol((1 - p) * team_pg + p * f.alw / f.agames) * rate_k(K))
    # QB for receivers: level, and change from the QBs he had over his window
    if kind == "rec":
        cq, eq = fit_grid(f, lambda c: f.base * (1 + c * (f.qb_now - QB_MEAN)), np.arange(0, 3.01, 0.25)); f["qb_level"] = f.base * (1 + cq * (f.qb_now - QB_MEAN)); f.attrs["qb_level_c"] = cq
        qb_then = f.qbr_85 / f.one_85.replace(0, np.nan); dq = (f.qb_now - qb_then).fillna(0.0)
        cc, ec = fit_grid(f, lambda c: f.base * (1 + c * dq), np.arange(0, 3.01, 0.25)); f["qb_change"] = f.base * (1 + cc * dq); f.attrs["qb_change_c"] = cc
    # own long-run prior: shrink the 17-game rate toward his decayed 0.95 rate (itself shrunk toward the league with K)
    own = (f.yds_95 + K * lg) / (f.n_95 + K); f["own_prior"] = MED[kind] * adj(vol(team_pg) * (f.yds + K * own) / (f.n + K))
    # home and away
    ch, eh = fit_grid(f, lambda c: f.base * (1 + c * (f.home - 0.5)), np.arange(-0.1, 0.101, 0.02)); f["home"] = f.base * (1 + ch * (f.home - 0.5)); f.attrs["home_c"] = ch
    # the layers that helped on both windows, combined: opponent pace at a quarter, and the wind factor where fitted
    if kind != "rush":
        f["combo"] = f.pace25 * (1 + cw * wx)
    # re-tune K and W on the adopted rule
    KS = {"rec": [50, 100, 200, 400], "rush": [15, 25, 50, 100], "pass": [25, 50, 100, 200]}[kind]
    for k in KS:
        for w in [0.0, 0.25, 0.5]:
            f[f"K{k}_W{w}"] = MED[kind] * adj(vol(team_pg) * rate_k(k), w)
    return f
for kind, stat in [("rec", "rec_yards"), ("rush", "rush_yards"), ("pass", "pass_yards")]:
    f = build(kind); V = [c for c in ["base", "wind10", "windlin", "pace25", "pace50", "qb_level", "qb_change", "own_prior", "home", "combo"] if c in f.columns] + [c for c in f.columns if c.startswith("K") and "_W" in c]
    ev = evaluate(f, "act_yds", V); print(stat, ev, "fitted", dict(f.attrs), flush=True); rec(stat, V, ev, {"fitted": str(dict(f.attrs))})
pd.DataFrame(rows).to_csv("reports/props_backtest4.csv", index=False); print(pd.DataFrame(rows).to_string()); print("DONE")
