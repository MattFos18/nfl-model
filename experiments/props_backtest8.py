"""Round eight (23 Sep 2026): the longest-play markets PrizePicks posts (longest reception, longest rush, longest
completion), which had a line on the card and no projection. Per player and game the longest gain of his kind from
the play-by-play since 2016 (0 when he had none), projected walk-forward from his previous games: flat average of
his game-longest over his last 17 (the baseline); decayed averages (0.85, 0.90 per game back); shrunk toward the
league average for his position from the previous season with K games of weight; a linear blend with his yards per
game (the line the rest of the rule already projects); a median factor. Constants fitted on 2016 to 2018, scored on
2019 to 2022 and 2023 to 2025 by mean absolute error in yards. Output reports/props_backtest8.csv."""
import numpy as np, pandas as pd
from nflmodel.model import OUT
from nflmodel.positions import names_by_id
N = 17
WIN = {"2019-22": (2019, 2022), "2023-25": (2023, 2025)}
d = pd.read_parquet(OUT / "scheme_plays.parquet", columns=["game_id", "play_id", "season", "week", "posteam", "play_type", "pass_play", "dropback", "complete_pass", "yards_gained", "passer_player_id", "receiver_player_id", "rusher_player_id"])
d = d[d.play_type.isin(["pass", "run"]) & (d.season >= 2016)].copy(); d["yards_gained"] = d.yards_gained.fillna(0.0); d["comp"] = d.complete_pass.fillna(0).astype(float)
names = names_by_id(range(2014, 2027)); pos_of = {pid: v[1] for pid, v in names.items()}
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
def fit_grid(frame, make, grid, actual):
    fit = frame[frame.season <= 2018]; errs = [float((make(c)[fit.index] - fit[actual]).abs().mean()) for c in grid]; return float(grid[int(np.argmin(errs))])
def ev(f, col, act):
    out = {}
    for w, (a, b) in WIN.items():
        x = f[f.season.between(a, b)]; out[f"mae_{w}"] = round(float((x[col] - x[act]).abs().mean()), 3); out[f"n_{w}"] = int(len(x))
    return out
rows = []
def run(kind, pg, vol_col, min_vol, pos_groups):
    """pg: one row per player-game with longest, yds, vol_col, pos. Builds the walk-forward frame and scores every variant."""
    pg = pg.copy(); pg["one"] = 1.0
    F = prev_sums(pg, ["pid"], ["longest", "yds", vol_col])
    D85 = prev_sums(pg, ["pid"], ["longest", "one"], decay=0.85).rename(columns={"longest": "l85", "one": "n85"}); D90 = prev_sums(pg, ["pid"], ["longest", "one"], decay=0.90).rename(columns={"longest": "l90", "one": "n90"})
    f = pg[["pid", "pos", "season", "week", "game_id", "longest"]].rename(columns={"longest": "act"}).merge(F[["pid", "game_id", "games_prev", "longest", "yds", vol_col]], on=["pid", "game_id"]).merge(D85[["pid", "game_id", "l85", "n85"]], on=["pid", "game_id"]).merge(D90[["pid", "game_id", "l90", "n90"]], on=["pid", "game_id"])
    f = f[(f.games_prev >= 3) & (f[vol_col] / f.games_prev >= min_vol)].copy()
    # league prior: the previous season's mean game-longest for his position group among qualifying player-games
    f["grp"] = f.pos.map(pos_groups).fillna(list(pos_groups.values())[0])
    pri = f.groupby(["season", "grp"]).act.mean().rename("prior").reset_index(); pri["season"] += 1; f = f.merge(pri, on=["season", "grp"], how="left"); f["prior"] = f.prior.fillna(f.act[f.season <= 2018].mean())
    f["l_avg"] = f.longest / f.games_prev; f["l_85"] = f.l85 / f.n85; f["l_90"] = f.l90 / f.n90
    for K in [2, 4, 8, 16]: f[f"l_85_K{K}"] = (f.l_85 * f.games_prev + K * f.prior) / (f.games_prev + K)
    fit = f[f.season <= 2018]; ypg = f.yds / f.games_prev
    X = np.column_stack([np.ones(len(fit)), fit.l_85.values, (fit.yds / fit.games_prev).values]); beta = np.linalg.lstsq(X, fit.act.values, rcond=None)[0]
    f["l_blend"] = beta[0] + beta[1] * f.l_85 + beta[2] * ypg
    best_k = min([2, 4, 8, 16], key=lambda K: float((fit[f"l_85_K{K}"] - fit.act).abs().mean())); base = f[f"l_85_K{best_k}"]
    med = fit_grid(f, lambda c: c * base, np.arange(0.70, 1.06, 0.02), "act"); f["l_85_K_med"] = med * base
    med_b = fit_grid(f, lambda c: c * f.l_blend, np.arange(0.70, 1.06, 0.02), "act"); f["l_blend_med"] = med_b * f.l_blend
    for c in ["l_avg", "l_85", "l_90"] + [f"l_85_K{K}" for K in [2, 4, 8, 16]] + ["l_blend", "l_85_K_med", "l_blend_med"]:
        rows.append({"stat": kind, "variant": c, **ev(f, c, "act"), "fitted": f"blend {beta[0]:.4f} + {beta[1]:.4f} x decayed longest + {beta[2]:.4f} x yards per game (median factor {med_b:.2f}); median factor {med:.2f} on K{best_k}"})
    print(kind, "K", best_k, "median", med, "blend", np.round(beta, 3), "median on blend", med_b, "n", len(f))
    return f
# receivers: longest reception (completed passes to him), targets as volume
t = d[d.pass_play & d.receiver_player_id.notna()].copy(); t["lg"] = np.where(t.comp == 1, t.yards_gained, 0.0)
pg = t.groupby(["receiver_player_id", "season", "week", "game_id"]).agg(longest=("lg", "max"), yds=("yards_gained", "sum"), tgt=("play_id", "size")).reset_index().rename(columns={"receiver_player_id": "pid"}); pg["pos"] = pg.pid.map(pos_of).fillna("WR")
pg = pg[pg.pos != "QB"]; run("rec_longest", pg, "tgt", 3.0, {"WR": "WR", "TE": "TE", "RB": "RB", "FB": "RB", "HB": "RB"})
# rushers: longest rush
r = d[d.play_type.eq("run") & d.rusher_player_id.notna()].copy()
pg = r.groupby(["rusher_player_id", "season", "week", "game_id"]).agg(longest=("yards_gained", "max"), yds=("yards_gained", "sum"), car=("play_id", "size")).reset_index().rename(columns={"rusher_player_id": "pid"}); pg["pos"] = pg.pid.map(pos_of).fillna("RB")
run("rush_longest", pg, "car", 5.0, {"RB": "RB", "FB": "RB", "HB": "RB", "QB": "QB", "WR": "WR"})
# passers: longest completion
q = d[d.pass_play & d.passer_player_id.notna()].copy(); q["lg"] = np.where(q.comp == 1, q.yards_gained, 0.0)
pg = q.groupby(["passer_player_id", "season", "week", "game_id"]).agg(longest=("lg", "max"), yds=("yards_gained", "sum"), att=("play_id", "size")).reset_index().rename(columns={"passer_player_id": "pid"}); pg["pos"] = "QB"
run("pass_longest", pg, "att", 15.0, {"QB": "QB"})
out = pd.DataFrame(rows); out.to_csv("reports/props_backtest8.csv", index=False); print(out.to_string())
