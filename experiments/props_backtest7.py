"""Round seven (23 Sep 2026): defensive props. Tackles plus assists (the market the books post) per defender and game,
projected walk-forward from data/processed/def_games.parquet (every tackle, assist and tackle-with-assist credit in
the play-by-play since 2016): volume = the plays the defense will face (the opponent's plays per game over its last
17, moved by the game script from the opponent's side of the closing line) x his share of his team's tackles (flat
or decayed per game back); rate is one tackle per credited play by construction, so the share carries the player;
shrunk toward the team's positional average with K games of weight; median factor. Constants fitted on 2016 to 2018,
scored on both windows by absolute error. Sacks the same way (rate per play faced, shrunk hard), scored by absolute
error and Poisson log loss. Output reports/props_backtest7.csv."""
import numpy as np, pandas as pd
from scipy.special import gammaln
from nflmodel.model import OUT
from nflmodel import props as PR
N, MIN_G = 17, 3
WIN = {"2019-22": (2019, 2022), "2023-25": (2023, 2025)}
g = pd.read_parquet(OUT / "def_games.parquet"); games = pd.read_parquet(OUT / "games.parquet")[["game_id", "home_team", "away_team", "spread_line", "total_line"]]
d = pd.read_parquet(OUT / "scheme_plays.parquet", columns=["game_id", "season", "week", "posteam", "defteam", "play_type", "pass_play"]); d = d[d.play_type.isin(["pass", "run"])]
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
def pll(mu, k): mu = np.clip(mu, 1e-3, None); return float(np.mean(mu - k * np.log(mu) + gammaln(k + 1)))
def fit_grid(frame, make, grid, actual):
    fit = frame[frame.season <= 2018]; errs = [float((make(c)[fit.index] - fit[actual]).abs().mean()) for c in grid]; return float(grid[int(np.argmin(errs))])
# the offense's plays per game (pass + run) and the game-script line on it, from the team that will face this defense
tv = d.groupby(["posteam", "season", "week", "game_id"]).agg(tp=("pass_play", "sum"), tr=("play_type", lambda x: (x == "run").sum())).reset_index(); tv["plays"] = tv.tp + tv.tr
T17 = prev_sums(tv, ["posteam"], ["plays"]).rename(columns={"posteam": "opp", "plays": "opp_plays", "games_prev": "ogames"})
# team tackles per game (for the share) and the player's decayed share
tm = g.groupby(["defteam", "season", "week", "game_id"]).agg(team_tk=("tackles", "sum"), team_sk=("sacks", "sum"), faced=("plays_faced", "first")).reset_index()
p = g.merge(tm, on=["defteam", "season", "week", "game_id"])
R = prev_sums(p, ["pid"], ["tackles", "team_tk", "sacks", "faced", "solo"]); R85 = prev_sums(p, ["pid"], ["tackles", "team_tk", "sacks", "faced"], decay=0.85).rename(columns={c: c + "_85" for c in ["tackles", "team_tk", "sacks", "faced"]}); R90 = prev_sums(p, ["pid"], ["tackles", "team_tk"], decay=0.90).rename(columns={c: c + "_90" for c in ["tackles", "team_tk"]})
f = p[["pid", "defteam", "season", "week", "game_id", "tackles", "sacks"]].rename(columns={"tackles": "act_tk", "sacks": "act_sk"})
f = f.merge(R[["pid", "game_id", "games_prev", "tackles", "team_tk", "sacks", "faced"]], on=["pid", "game_id"]).merge(R85[["pid", "game_id", "tackles_85", "team_tk_85", "sacks_85", "faced_85"]], on=["pid", "game_id"]).merge(R90[["pid", "game_id", "tackles_90", "team_tk_90"]], on=["pid", "game_id"])
f = f.merge(games, on="game_id"); f["opp"] = np.where(f.defteam == f.home_team, f.away_team, f.home_team); f = f.merge(T17[["opp", "game_id", "opp_plays", "ogames"]], on=["opp", "game_id"])
f = f[(f.games_prev >= MIN_G) & (f.ogames >= 3) & (f.tackles >= 3)].copy()
f["me_opp"] = np.where(f.opp == f.home_team, f.spread_line, -f.spread_line).astype(float); f["me_opp"] = f.me_opp.fillna(0.0); f["tc"] = (f.total_line - PR.GS_TOTAL).fillna(0.0)
b = PR.GS["rec"], PR.GS["rush"]; gs_add = (b[0][0] + b[1][0]) + (b[0][1] + b[1][1]) * f.me_opp + (b[0][2] + b[1][2]) * f.tc
opp_pg = f.opp_plays / f.ogames; vol_flat = opp_pg; vol_gs = opp_pg + gs_add
share_flat = f.tackles / f.team_tk.replace(0, np.nan); share_85 = f.tackles_85 / f.team_tk_85.replace(0, np.nan); share_90 = f.tackles_90 / f.team_tk_90.replace(0, np.nan)
team_tk_per_play = f.team_tk / f.faced.replace(0, np.nan)   # the defense's tackles per play faced (about 0.95)
rows = []
def ev(col, act, count=False):
    out = {}
    for w, (a, bb) in WIN.items():
        x = f[f.season.between(a, bb)]; out[f"mae_{w}"] = round(float((x[col] - x[act]).abs().mean()), 3); out[f"ll_{w}"] = (round(pll(x[col].values, x[act].values), 4) if count else None); out[f"n_{w}"] = int(len(x))
    return out
# tackles: his per-game average; share x plays faced; decayed share; game script; shrink of the share toward the team-role prior (K games); median factor
f["tk_avg"] = f.tackles / f.games_prev
f["tk_flat"] = share_flat * team_tk_per_play * vol_flat; f["tk_85"] = share_85 * team_tk_per_play * vol_flat; f["tk_90"] = share_90 * team_tk_per_play * vol_flat; f["tk_85gs"] = share_85 * team_tk_per_play * vol_gs
for K in [2, 4, 8]:
    prior = f.tackles / f.games_prev   # his own flat average as the prior the decayed share is shrunk toward (in games of weight)
    f[f"tk_85gs_K{K}"] = (f.tk_85gs * f.games_prev + K * prior) / (f.games_prev + K)
med = fit_grid(f, lambda c: c * f.tk_85gs, np.arange(0.80, 1.06, 0.02), "act_tk"); f["tk_85gs_med"] = med * f.tk_85gs
for c in ["tk_avg", "tk_flat", "tk_85", "tk_90", "tk_85gs", "tk_85gs_K2", "tk_85gs_K4", "tk_85gs_K8", "tk_85gs_med"]: rows.append({"stat": "def_tackles", "variant": c, **ev(c, "act_tk"), "fitted": f"median factor {med:.2f}"})
# sacks: his rate per play faced shrunk toward the league (K plays), x plays faced with the game script
lg_sk = float(g.sacks.sum() / g.plays_faced.sum()); f["sk_avg"] = f.sacks / f.games_prev   # a defender's sacks per play his defense faced, league-wide (every credited defender's game counts)
for K in [100, 300, 600, 1000]: f[f"sk_K{K}"] = (f.sacks + K * lg_sk) / (f.faced + K) * vol_gs
f["sk_league"] = lg_sk * vol_gs
for c in ["sk_avg", "sk_league", "sk_K100", "sk_K300", "sk_K600", "sk_K1000"]: rows.append({"stat": "def_sacks", "variant": c, **ev(c, "act_sk", True), "league_rate": round(lg_sk, 5)})
S = pd.DataFrame(rows); S.to_csv("reports/props_backtest7.csv", index=False); print(S.to_string()); print("median", med, "league sack rate per play faced", round(lg_sk, 5)); print("DONE")
