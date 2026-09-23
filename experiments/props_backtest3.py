"""Round three: combine what round two found (decayed usage, game script from the spread and total), add a median
factor (yards are right-skewed, so the line that minimises absolute error sits below the mean, as a book's over/under
does), and run the same layers for rushing and passing yards. Every constant is fitted on 2016 to 2018 only and
applied forward; scored on both windows. Output reports/props_backtest3.csv (the game_script rows carry the fitted
constants: league_total in the first column; per stat the intercept, the coefficient per point of expected margin and
the coefficient per point of total above the league mean, in the first three numeric columns)."""
import numpy as np, pandas as pd
from nflmodel.model import OUT
N, MIN_VOL = 17, 8
WIN = {"2019-22": (2019, 2022), "2023-25": (2023, 2025)}
d = pd.read_parquet(OUT / "scheme_plays.parquet"); d = d[d.play_type.isin(["pass", "run"]) & (d.season >= 2016)].copy(); d["yards_gained"] = d.yards_gained.fillna(0.0)
games = pd.read_parquet(OUT / "games.parquet")[["game_id", "home_team", "spread_line", "total_line"]]; lg_total = float(games.total_line.mean())
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
def median_factor(frame, col, actual):
    """The multiplier c on the projection that minimises absolute error on the fit seasons (2016 to 2018), 0.02 steps."""
    fit = frame[frame.season <= 2018]; grid = np.arange(0.70, 1.06, 0.02)
    return round(float(grid[np.argmin([float((c * fit[col] - fit[actual]).abs().mean()) for c in grid])]), 2)
rows = []
def rec(stat, names_, ev, extra=None):
    for k in names_: rows.append({"stat": stat, "variant": k, **{f"mae_{w}": ev[w][k] for w in WIN}, **{f"n_{w}": ev[w]["n"] for w in WIN}, **(extra or {})})
tv = d[d.pass_play].groupby(["posteam", "season", "week", "game_id"]).size().rename("tp").reset_index().merge(d[d.play_type.eq("run")].groupby(["posteam", "season", "week", "game_id"]).size().rename("tr").reset_index(), how="outer").merge(d[d.dropback].groupby(["posteam", "season", "week", "game_id"]).size().rename("tdb").reset_index(), how="outer").fillna(0)
T17 = prev_sums(tv, ["posteam"], ["tp", "tr", "tdb"])
# game script coefficients on 2016 to 2018
tvf = tv.merge(games, on="game_id").merge(T17[["posteam", "game_id", "tp", "tr", "tdb", "games_prev"]].rename(columns={"tp": "tp_p", "tr": "tr_p", "tdb": "tdb_p"}), on=["posteam", "game_id"])
tvf = tvf[(tvf.games_prev >= 3) & tvf.spread_line.notna() & tvf.total_line.notna()].copy(); tvf["me"] = np.where(tvf.posteam == tvf.home_team, tvf.spread_line, -tvf.spread_line); tvf["tc"] = tvf.total_line - lg_total
fit = tvf[tvf.season <= 2018]; X = np.c_[np.ones(len(fit)), fit.me, fit.tc]
GS = {k: np.linalg.lstsq(X, fit[k] - fit[f"{k}_p"] / fit.games_prev, rcond=None)[0] for k in ["tp", "tr", "tdb"]}; print("game script", {k: list(np.round(v, 4)) for k, v in GS.items()}, "league total", round(lg_total, 4), flush=True)
rows.append({"stat": "game_script", "variant": "league_total", "mae_2019-22": round(lg_total, 4)})
for k, v in GS.items(): rows.append({"stat": "game_script", "variant": k, "mae_2019-22": round(float(v[0]), 4), "mae_2023-25": round(float(v[1]), 4), "n_2019-22": round(float(v[2]), 4)})
def build(kind):
    """kind: rec (targets), rush (carries), pass (dropbacks). Returns the player-game frame with volume and rate pieces."""
    if kind == "rec":
        t = d[d.pass_play & d.receiver_player_id.notna()].rename(columns={"receiver_player_id": "pid"}); vcol, tcol = "tp", "tp"; lg = float(d[d.pass_play].yards_gained.mean()); K = 100
    elif kind == "rush":
        t = d[d.play_type.eq("run") & d.rusher_player_id.notna()].rename(columns={"rusher_player_id": "pid"}); vcol, tcol = "tr", "tr"; lg = float(d[d.play_type.eq("run")].yards_gained.mean()); K = 25
    else:
        t = d[d.dropback & d.passer_player_id.notna()].rename(columns={"passer_player_id": "pid"}); vcol, tcol = "tdb", "tdb"; lg = float(d[d.dropback].yards_gained.mean()); K = 50
    t = t.copy(); t["n"] = 1
    pg = t.groupby(["pid", "posteam", "season", "week", "game_id"]).agg(n=("n", "sum"), yds=("yards_gained", "sum")).reset_index().merge(tv[["posteam", "season", "week", "game_id", tcol]].rename(columns={tcol: "team_n"}), on=["posteam", "season", "week", "game_id"], how="left")
    cols = ["n", "yds", "team_n"]; R = prev_sums(pg, ["pid"], cols); R90 = prev_sums(pg, ["pid"], cols, decay=0.90).rename(columns={c: c + "_90" for c in cols}); R85 = prev_sums(pg, ["pid"], cols, decay=0.85).rename(columns={c: c + "_85" for c in cols})
    dg = t.groupby(["defteam", "season", "week", "game_id"]).agg(d_n=("n", "sum"), d_yds=("yards_gained", "sum")).reset_index(); D = prev_sums(dg, ["defteam"], ["d_n", "d_yds"])
    f = pg[["pid", "posteam", "season", "week", "game_id", "n", "yds"]].rename(columns={"n": "act_n", "yds": "act_yds"})
    f = f.merge(R[["pid", "game_id", "games_prev"] + cols], on=["pid", "game_id"]).merge(R90[["pid", "game_id"] + [c + "_90" for c in cols]], on=["pid", "game_id"]).merge(R85[["pid", "game_id"] + [c + "_85" for c in cols]], on=["pid", "game_id"])
    f = f.merge(games, on="game_id").merge(d[["game_id", "posteam", "defteam"]].drop_duplicates(), on=["game_id", "posteam"]).merge(T17[["posteam", "game_id", vcol, "games_prev"]].rename(columns={vcol: "tv", "games_prev": "tgames"}), on=["posteam", "game_id"]).merge(D[["defteam", "game_id", "d_n", "d_yds"]], on=["defteam", "game_id"])
    minv = MIN_VOL * (3 if kind == "pass" else 1); f = f[(f.n >= minv) & (f.games_prev >= 3) & (f.tgames >= 3)].copy()
    if kind == "pass": f = f[f.act_n >= 10]
    f["me"] = np.where(f.posteam == f.home_team, f.spread_line, -f.spread_line); f["tc"] = f.total_line - lg_total
    f["d_rate"] = np.where(f.d_n >= 100, f.d_yds / f.d_n.replace(0, np.nan), np.nan); w = {"rec": 0.25, "rush": 0.25, "pass": 0.5}[kind]
    adj = lambda base: base * np.where(f.d_rate.notna(), 1 + w * (f.d_rate / lg - 1), 1.0)
    rate = (f.yds + K * lg) / (f.n + K)
    if kind == "pass":
        vol_flat = f.tv / f.tgames; vol_90 = vol_flat; vol_85 = vol_flat   # the starter takes the team's dropbacks
    else:
        vol_flat = f.n / f.team_n.replace(0, np.nan) * f.tv / f.tgames; vol_90 = f.n_90 / f.team_n_90.replace(0, np.nan) * f.tv / f.tgames; vol_85 = f.n_85 / f.team_n_85.replace(0, np.nan) * f.tv / f.tgames
    b = GS[vcol]; gs_mult = (f.tv / f.tgames + b[0] + b[1] * f.me.fillna(0) + b[2] * f.tc.fillna(0)) / (f.tv / f.tgames)
    f["v1"] = adj(vol_flat * rate); f["A90"] = adj(vol_90 * rate); f["A85"] = adj(vol_85 * rate); f["B"] = adj(vol_flat * gs_mult * rate); f["A90B"] = adj(vol_90 * gs_mult * rate); f["A85B"] = adj(vol_85 * gs_mult * rate)
    for c in ["v1", "A90B", "A85B"]:
        cf = median_factor(f, c, "act_yds"); f[f"{c}_med"] = cf * f[c]; f.attrs[f"{c}_med"] = cf
    f["vol_flat"] = vol_flat; f["vol_90"] = vol_90; f["vol_gs"] = vol_90 * gs_mult
    return f
for kind, stat in [("rec", "rec_yards"), ("rush", "rush_yards"), ("pass", "pass_yards")]:
    f = build(kind); V = ["v1", "A90", "A85", "B", "A90B", "A85B", "v1_med", "A90B_med", "A85B_med"]
    ev = evaluate(f, "act_yds", V); print(stat, ev, "median factors", {k: f.attrs[k] for k in ["v1_med", "A90B_med", "A85B_med"]}, flush=True); rec(stat, V, ev, {"median_factor_v1": f.attrs["v1_med"], "median_factor_A90B": f.attrs["A90B_med"], "median_factor_A85B": f.attrs["A85B_med"]})
    if kind != "pass":
        ev2 = evaluate(f, "act_n", ["vol_flat", "vol_90", "vol_gs"]); print(stat, "volume", ev2, flush=True); rec(stat.replace("_yards", "_volume"), ["vol_flat", "vol_90", "vol_gs"], ev2)
pd.DataFrame(rows).to_csv("reports/props_backtest3.csv", index=False); print(pd.DataFrame(rows).to_string()); print("DONE")
