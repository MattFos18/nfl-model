"""Round nine (23 Sep 2026): kickers. PrizePicks posts kicking points and field goals made; nothing on the card
projected them. Per kicker and game from the raw play-by-play since 2016: field goals made and tried, extra points
made and tried, kicking points (3 x field goals + extra points). Projected walk-forward from: his own points per
game (flat 17, the baseline; decayed 0.85 per game back); his team's points per game decayed (a new kicker inherits
the offense that feeds him); the team's implied total from the closing line ((total + expected margin) / 2); a
blend fitted on 2016 to 2018 of the decayed team rate and the implied total; a median factor. Scored on 2019 to
2022 and 2023 to 2025 by mean absolute error. Field goals made the same way. Output reports/props_backtest9.csv."""
import numpy as np, pandas as pd
from nflmodel.model import OUT
from nflmodel.features import RAW
N = 17
WIN = {"2019-22": (2019, 2022), "2023-25": (2023, 2025)}
games = pd.read_parquet(OUT / "games.parquet")[["game_id", "home_team", "away_team", "spread_line", "total_line"]]
parts = []
for s in range(2016, 2027):
    f = RAW / "pbp" / f"play_by_play_{s}.parquet"
    if not f.exists(): continue
    p = pd.read_parquet(f, columns=["game_id", "season", "week", "posteam", "field_goal_attempt", "field_goal_result", "extra_point_attempt", "extra_point_result", "kicker_player_id"])
    k = p[((p.field_goal_attempt == 1) | (p.extra_point_attempt == 1)) & p.kicker_player_id.notna()].copy()
    k["fgm"] = (k.field_goal_result == "made").astype(float); k["fga"] = (k.field_goal_attempt == 1).astype(float); k["xpm"] = (k.extra_point_result == "good").astype(float); k["xpa"] = (k.extra_point_attempt == 1).astype(float)
    parts.append(k.groupby(["game_id", "season", "week", "posteam", "kicker_player_id"]).agg(fgm=("fgm", "sum"), fga=("fga", "sum"), xpm=("xpm", "sum"), xpa=("xpa", "sum")).reset_index())
kg = pd.concat(parts, ignore_index=True).rename(columns={"kicker_player_id": "pid", "posteam": "team"}); kg["pts"] = 3 * kg.fgm + kg.xpm; kg["one"] = 1.0
# one kicker per team-game (the one with the most kicks) so team rows and player rows line up
kg["kicks"] = kg.fga + kg.xpa; kg = kg.sort_values("kicks", ascending=False).drop_duplicates(["game_id", "team"]).drop(columns="kicks")
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
P = prev_sums(kg, ["pid"], ["pts", "fgm", "fga", "xpm"]); P85 = prev_sums(kg, ["pid"], ["pts", "fgm", "fga", "one"], decay=0.85).rename(columns={"pts": "pts85", "fgm": "fgm85", "fga": "fga85", "one": "n85"})
T85 = prev_sums(kg, ["team"], ["pts", "fgm", "fga", "one"], decay=0.85).rename(columns={"pts": "tpts85", "fgm": "tfgm85", "fga": "tfga85", "one": "tn85", "games_prev": "tgames"})
f = kg[["pid", "team", "season", "week", "game_id", "pts", "fgm", "fga"]].rename(columns={"pts": "act_pts", "fgm": "act_fgm"})
f = f.merge(P[["pid", "game_id", "games_prev", "pts", "fgm", "fga"]].rename(columns={"pts": "pts17", "fgm": "fgm17", "fga": "fga17"}), on=["pid", "game_id"]).merge(P85[["pid", "game_id", "pts85", "fgm85", "fga85", "n85"]], on=["pid", "game_id"]).merge(T85[["team", "game_id", "tpts85", "tfgm85", "tfga85", "tn85", "tgames"]], on=["team", "game_id"])
f = f.merge(games, on="game_id"); f["me"] = np.where(f.team == f.home_team, f.spread_line, -f.spread_line).astype(float); f["tt"] = ((f.total_line + f.me) / 2).astype(float)
f = f[(f.games_prev >= 3) & (f.tgames >= 3) & f.tt.notna()].copy()
f["k_avg"] = f.pts17 / f.games_prev; f["k_85"] = f.pts85 / f.n85; f["k_team85"] = f.tpts85 / f.tn85
fit = f[f.season <= 2018]
def ols(cols, act):
    fit = f[f.season <= 2018]; X = np.column_stack([np.ones(len(fit))] + [fit[c].values for c in cols]); return np.linalg.lstsq(X, fit[act].values, rcond=None)[0]
b_tt = ols(["tt"], "act_pts"); f["k_tt"] = b_tt[0] + b_tt[1] * f.tt
b_own = ols(["k_85", "tt"], "act_pts"); f["k_blend_own"] = b_own[0] + b_own[1] * f.k_85 + b_own[2] * f.tt
b_tm = ols(["k_team85", "tt"], "act_pts"); f["k_blend_team"] = b_tm[0] + b_tm[1] * f.k_team85 + b_tm[2] * f.tt
fit = f[f.season <= 2018]; best = min(["k_blend_own", "k_blend_team"], key=lambda c: float((fit[c] - fit.act_pts).abs().mean())); med = fit_grid(f, lambda c: c * f[best], np.arange(0.70, 1.10, 0.02), "act_pts"); f["k_blend_med"] = med * f[best]
rows = []
for c in ["k_avg", "k_85", "k_team85", "k_tt", "k_blend_own", "k_blend_team", "k_blend_med"]:
    rows.append({"stat": "kick_points", "variant": c, **ev(f, c, "act_pts"), "fitted": f"own blend {b_own[0]:.4f} + {b_own[1]:.4f} x decayed own + {b_own[2]:.4f} x implied total; team blend {b_tm[0]:.4f} + {b_tm[1]:.4f} x decayed team + {b_tm[2]:.4f} x implied total; median factor {med:.2f} on {best}"})
# field goals made
f["g_avg"] = f.fgm17 / f.games_prev; f["g_85"] = f.fgm85 / f.n85; f["g_team85"] = f.tfgm85 / f.tn85
g_tt = ols(["tt"], "act_fgm"); f["g_tt"] = g_tt[0] + g_tt[1] * f.tt
g_own = ols(["g_85", "tt"], "act_fgm"); f["g_blend_own"] = g_own[0] + g_own[1] * f.g_85 + g_own[2] * f.tt
g_tm = ols(["g_team85", "tt"], "act_fgm"); f["g_blend_team"] = g_tm[0] + g_tm[1] * f.g_team85 + g_tm[2] * f.tt
fit = f[f.season <= 2018]; gbest = min(["g_blend_own", "g_blend_team"], key=lambda c: float((fit[c] - fit.act_fgm).abs().mean())); gmed = fit_grid(f, lambda c: c * f[gbest], np.arange(0.70, 1.10, 0.02), "act_fgm"); f["g_blend_med"] = gmed * f[gbest]
for c in ["g_avg", "g_85", "g_team85", "g_tt", "g_blend_own", "g_blend_team", "g_blend_med"]:
    rows.append({"stat": "field_goals", "variant": c, **ev(f, c, "act_fgm"), "fitted": f"own blend {g_own[0]:.4f} + {g_own[1]:.4f} x decayed own + {g_own[2]:.4f} x implied total; team blend {g_tm[0]:.4f} + {g_tm[1]:.4f} x decayed team + {g_tm[2]:.4f} x implied total; median factor {gmed:.2f} on {gbest}"})
out = pd.DataFrame(rows); out.to_csv("reports/props_backtest9.csv", index=False); print(out.drop(columns="fitted").to_string()); print(out.fitted.iloc[0]); print(out.fitted.iloc[-1]); print("n", len(f))
