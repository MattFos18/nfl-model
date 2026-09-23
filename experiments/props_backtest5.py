"""Round five of the player-projection backtest (23 Sep 2026): the other numbers on the props table, which rounds one
to four did not test: receptions, receiving and rushing touchdowns, passing touchdowns and interceptions. Volume is
the adopted rule's (usage decayed 0.85 x the team's plays moved by the game script; passing blended a quarter toward
the opponent's allowed dropbacks); the rate per touch is the player's over his last 17 games, raw (as the page had
it) or shrunk toward the league's with K touches of weight, and for touchdowns also moved by the game's expected
margin (favourites score more) with a coefficient fitted on 2016 to 2018. Scored on both windows by mean absolute
error on the count, and for touchdowns and interceptions also by the Poisson log loss (the fit of the whole
distribution, which is what an anytime-scorer price needs). A median factor is fitted for receptions only: for a
count that is usually 0 the absolute-error-best line is degenerate. Output reports/props_backtest5.csv."""
import numpy as np, pandas as pd
from scipy.special import gammaln as _gammaln
from nflmodel.model import OUT
N, MIN_VOL = 17, 8
WIN = {"2019-22": (2019, 2022), "2023-25": (2023, 2025)}
DECAY, PACE_PASS = 0.85, 0.25
GS = {"tp": (-0.5969, -0.046, 0.1636), "tr": (0.3413, 0.103, -0.1713), "tdb": (-0.5967, -0.0461, 0.1638)}; GS_TOTAL = 43.5674
d = pd.read_parquet(OUT / "scheme_plays.parquet"); d = d[d.play_type.isin(["pass", "run"]) & (d.season >= 2016)].copy()
for c in ["complete_pass", "pass_touchdown", "rush_touchdown", "interception"]: d[c] = d[c].fillna(0).astype(float)
games = pd.read_parquet(OUT / "games.parquet")[["game_id", "home_team", "away_team", "spread_line", "total_line"]]
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
def poisson_ll(mu, k): mu = np.clip(mu, 1e-3, None); return float(np.mean(mu - k * np.log(mu) + _gammaln(k + 1)))
def evaluate(frame, actual, variants, ll=False):
    res = {}
    for w, (a, b) in WIN.items():
        x = frame[frame.season.between(a, b)]; res[w] = {k: round(float((x[k] - x[actual]).abs().mean()), 3) for k in variants}; res[w]["n"] = int(len(x))
        if ll: res[w].update({f"ll_{k}": round(poisson_ll(x[k].values, x[actual].values), 4) for k in variants})
    return res
def fit_grid(frame, make, grid, actual, metric="mae"):
    fit = frame[frame.season <= 2018]
    errs = [float((make(c)[fit.index] - fit[actual]).abs().mean()) if metric == "mae" else poisson_ll(make(c)[fit.index].values, fit[actual].values) for c in grid]
    return float(grid[int(np.argmin(errs))])
rows = []
def rec(stat, names_, ev, extra=None):
    for k in names_: rows.append({"stat": stat, "variant": k, **{f"mae_{w}": ev[w][k] for w in WIN}, **{f"ll_{w}": ev[w].get(f"ll_{k}") for w in WIN}, **{f"n_{w}": ev[w]["n"] for w in WIN}, **(extra or {})})
tv = d[d.pass_play].groupby(["posteam", "defteam", "season", "week", "game_id"]).size().rename("tp").reset_index().merge(d[d.play_type.eq("run")].groupby(["posteam", "defteam", "season", "week", "game_id"]).size().rename("tr").reset_index(), how="outer").merge(d[d.dropback].groupby(["posteam", "defteam", "season", "week", "game_id"]).size().rename("tdb").reset_index(), how="outer").fillna(0)
T17 = prev_sums(tv, ["posteam"], ["tp", "tr", "tdb"]); ALW = prev_sums(tv.rename(columns={"tdb": "a_tdb"}), ["defteam"], ["a_tdb"]).rename(columns={"games_prev": "agames"})
def build(kind):
    if kind == "rec":
        t = d[d.pass_play & d.receiver_player_id.notna()].rename(columns={"receiver_player_id": "pid"}); vcol = "tp"; ev = {"catch": "complete_pass", "td": "pass_touchdown"}
    elif kind == "rush":
        t = d[d.play_type.eq("run") & d.rusher_player_id.notna()].rename(columns={"rusher_player_id": "pid"}); vcol = "tr"; ev = {"td": "rush_touchdown"}
    else:
        t = d[d.dropback & d.passer_player_id.notna()].rename(columns={"passer_player_id": "pid"}); vcol = "tdb"; ev = {"td": "pass_touchdown", "int": "interception"}
    t = t.copy(); t["n"] = 1
    pg = t.groupby(["pid", "posteam", "season", "week", "game_id"]).agg(n=("n", "sum"), **{k: (v, "sum") for k, v in ev.items()}).reset_index().merge(tv[["posteam", "season", "week", "game_id", vcol]].rename(columns={vcol: "team_n"}), on=["posteam", "season", "week", "game_id"], how="left")
    cols = ["n", "team_n"] + list(ev); R = prev_sums(pg, ["pid"], cols); R85 = prev_sums(pg, ["pid"], ["n", "team_n"], decay=DECAY).rename(columns={"n": "n_85", "team_n": "team_n_85"})
    f = pg[["pid", "posteam", "season", "week", "game_id", "n"] + list(ev)].rename(columns={"n": "act_n", **{k: f"act_{k}" for k in ev}})
    f = f.merge(R[["pid", "game_id", "games_prev"] + cols], on=["pid", "game_id"]).merge(R85[["pid", "game_id", "n_85", "team_n_85"]], on=["pid", "game_id"])
    f = f.merge(games, on="game_id").merge(d[["game_id", "posteam", "defteam"]].drop_duplicates(), on=["game_id", "posteam"]).merge(T17[["posteam", "game_id", vcol, "games_prev"]].rename(columns={vcol: "tv", "games_prev": "tgames"}), on=["posteam", "game_id"]).merge(ALW[["defteam", "game_id", "a_tdb", "agames"]], on=["defteam", "game_id"])
    minv = MIN_VOL * (3 if kind == "pass" else 1); f = f[(f.n >= minv) & (f.games_prev >= 3) & (f.tgames >= 3) & (f.agames >= 3)].copy()
    if kind == "pass": f = f[f.act_n >= 10]
    f["me"] = np.where(f.posteam == f.home_team, f.spread_line, -f.spread_line).astype(float); f["tc"] = f.total_line - GS_TOTAL
    b = GS[vcol]; team_pg = f.tv / f.tgames
    if kind == "pass": team_pg = (1 - PACE_PASS) * team_pg + PACE_PASS * f.a_tdb / f.agames
    gs_add = b[0] + b[1] * f.me.fillna(0) + b[2] * f.tc.fillna(0)
    share = 1.0 if kind == "pass" else f.n_85 / f.team_n_85.replace(0, np.nan)
    f["vol"] = share * (team_pg + gs_add)
    lg = {k: float(t[v].mean()) for k, v in ev.items()}; f.attrs["league"] = lg
    return f, ev, lg
for kind, stat in [("rec", "rec"), ("rush", "rush"), ("pass", "pass")]:
    f, ev, lg = build(kind)
    for k in ev:
        V = []; raw = f[k] / f.n; f[f"{k}_raw"] = f.vol * raw; V.append(f"{k}_raw")
        f[f"{k}_league"] = f.vol * lg[k]; V.append(f"{k}_league")
        KS = [25, 50, 100, 200] if k == "catch" else [50, 100, 200, 400, 800]
        for K in KS: f[f"{k}_K{K}"] = f.vol * (f[k] + K * lg[k]) / (f.n + K); V.append(f"{k}_K{K}")
        extra = {}
        if k == "catch":
            best = min(KS, key=lambda K: float((f[f"{k}_K{K}"] - f[f"act_{k}"])[f.season <= 2018].abs().mean()))
            cm = fit_grid(f, lambda c: c * f[f"{k}_K{best}"], np.arange(0.80, 1.06, 0.02), f"act_{k}"); f[f"{k}_K{best}_med"] = cm * f[f"{k}_K{best}"]; V.append(f"{k}_K{best}_med"); extra = {"fitted": f"K {best}, median factor {cm:.2f}"}
        if k == "td":
            best = min(KS, key=lambda K: poisson_ll(f[f"{k}_K{K}"][f.season <= 2018].values, f[f"act_{k}"][f.season <= 2018].values))
            cme = fit_grid(f, lambda c: f[f"{k}_K{best}"] * (1 + c * f.me.fillna(0)), np.arange(0.0, 0.061, 0.005), f"act_{k}", metric="ll"); f[f"{k}_K{best}_gs"] = f[f"{k}_K{best}"] * (1 + cme * f.me.fillna(0)); V.append(f"{k}_K{best}_gs"); extra = {"fitted": f"K {best}, margin coefficient {cme:.3f} per point"}
        e = evaluate(f, f"act_{k}", V, ll=(k != "catch")); print(stat, k, e, extra, "league rate", round(lg[k], 4), flush=True); rec(f"{stat}_{k}", V, e, dict(extra, league_rate=round(lg[k], 4)))
pd.DataFrame(rows).to_csv("reports/props_backtest5.csv", index=False); print(pd.DataFrame(rows).to_string()); print("DONE")
