"""The adopted player-projection rule (nflmodel/props.py, rounds one to five), run walk-forward over every season the
charted plays cover, 2017 on (2016 is the first charted season, so its players have no history), and scored the
way the game backtest is: by season, by position and by size of the line. Every player-game with a touch is projected
from the previous games of the player, his team and the opponent, nothing from the game itself. For each stat the
rule's error is set against the raw rule the page carried before the backtests (flat 17-game rates, no game script,
no shrinkage, no median factor). Over rate = share of player-games where the actual beat the line (a line set at the
median should sit near half; below half means the line is high). Touchdowns and interceptions also carry the Poisson
log loss and the anytime rate: predicted P(at least one) against how often one came.
Output reports/props_by_season.csv, props_by_position.csv, props_by_bucket.csv."""
import numpy as np, pandas as pd
from scipy.special import gammaln
from nflmodel.model import OUT
from nflmodel.positions import names_by_id
from nflmodel import props as PR
N, MIN_VOL = 17, 8
d = PR.official(pd.read_parquet(OUT / "scheme_plays.parquet")); d = d[d.season >= 2016].copy(); d["yards_gained"] = d.yards_gained.fillna(0.0)   # official box-score terms (props.official), 24 Sep 2026
for c in ["complete_pass", "pass_touchdown", "rush_touchdown", "interception"]: d[c] = d[c].fillna(0).astype(float)
games = pd.read_parquet(OUT / "games.parquet")[["game_id", "home_team", "away_team", "spread_line", "total_line"]]
feat = pd.read_parquet(OUT / "features_asof.parquet", columns=["game_id", "team", "wind", "dome"]); feat["wind"] = np.where(feat.dome > 0, 0.0, feat.wind.fillna(0.0))
pred = pd.read_parquet(OUT / "pred_v3.parquet", columns=["game_id", "home_exp", "away_exp"])   # the game model's expected points, priced before each game (round 6)
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
def fade_sums(a, keys, cols, decay, season_f, team_f):
    """prev_sums, decayed, with an extra factor on the running sums at a season boundary and at a change of team (round 10)."""
    a = a.sort_values(keys + ["season", "week"]).reset_index(drop=True); out = a[keys + ["season", "week", "game_id"]].copy()
    vals = a[cols].values.astype(float); res = np.zeros_like(vals); gk = a[keys].astype(str).agg("|".join, axis=1).values; sn = a.season.values; tm = a.posteam.values; run = np.zeros(vals.shape[1]); last = None; ls = None; lt = None
    for i in range(len(a)):
        if gk[i] != last: run = np.zeros(vals.shape[1]); last = gk[i]; ls = sn[i]; lt = tm[i]
        if sn[i] != ls: run = run * season_f; ls = sn[i]
        if tm[i] != lt: run = run * team_f; lt = tm[i]
        res[i] = run; run = decay * run + vals[i]
    out[cols] = res; out["games_prev"] = a.groupby(keys).cumcount().clip(upper=N).values; return out
LEAGUE_ASOF = True   # 23 Sep 2026: the league averages a player is shrunk toward are as of the game (last season + this season before the week, as the live rule's props._asof frame); they had been the mean over every season, future ones included
def asof_mean(frame, col):
    """(season, week) -> the mean of col over last season and this season's weeks before `week`, as props._asof sees it."""
    g = frame.groupby(["season", "week"])[col].agg(["sum", "count"]).reset_index().sort_values(["season", "week"])
    tot = g.groupby("season")[["sum", "count"]].sum(); out = {}
    for s_, gs in g.groupby("season"):
        ps, pn = (tot.loc[s_ - 1, "sum"], tot.loc[s_ - 1, "count"]) if (s_ - 1) in tot.index else (0.0, 0)
        cs, cn = gs["sum"].cumsum().shift(1, fill_value=0.0).values, gs["count"].cumsum().shift(1, fill_value=0).values
        for w_, a_, b_ in zip(gs.week.values, cs, cn):
            out[(int(s_), int(w_))] = (ps + a_) / (pn + b_) if (pn + b_) else np.nan
    return out
def lg_series(f, frame, col, fallback):
    if not LEAGUE_ASOF:
        return pd.Series(fallback, index=f.index)
    m = asof_mean(frame, col); return pd.Series([m.get((int(a), int(b)), fallback) for a, b in zip(f.season, f.week)], index=f.index).fillna(fallback)
def pll(mu, k): mu = np.clip(mu, 1e-3, None); return float(np.mean(mu - k * np.log(mu) + gammaln(k + 1)))
tv = d[d.pass_play].groupby(["posteam", "defteam", "season", "week", "game_id"]).size().rename("tp").reset_index().merge(d[d.play_type.eq("run")].groupby(["posteam", "defteam", "season", "week", "game_id"]).size().rename("tr").reset_index(), how="outer").merge(d[d.dropback].groupby(["posteam", "defteam", "season", "week", "game_id"]).size().rename("tdb").reset_index(), how="outer").fillna(0)
T17 = prev_sums(tv, ["posteam"], ["tp", "tr", "tdb"]); ALW = prev_sums(tv.rename(columns={"tdb": "a_tdb"}), ["defteam"], ["a_tdb"]).rename(columns={"games_prev": "agames"})
def build(kind):
    if kind == "rec":
        t = d[d.pass_play & d.receiver_player_id.notna()].rename(columns={"receiver_player_id": "pid"}); vcol = "tp"; ev = {"catch": "complete_pass", "td": "pass_touchdown"}; lgp = d[d.pass_play]
    elif kind == "rush":
        t = d[d.play_type.eq("run") & d.rusher_player_id.notna()].rename(columns={"rusher_player_id": "pid"}); vcol = "tr"; ev = {"td": "rush_touchdown"}; lgp = t
    else:
        pdb = d[d.dropback & d.passer_player_id.notna()].assign(yards_gained=lambda x: x.pass_yds)   # passing yards: the yards on completions, not net of sacks (24 Sep 2026)
        t = pdb.rename(columns={"passer_player_id": "pid"}); vcol = "tdb"; ev = {"td": "pass_touchdown", "int": "interception"}; lgp = pdb
    t = t.copy(); t["n"] = 1
    pg = t.groupby(["pid", "posteam", "season", "week", "game_id"]).agg(n=("n", "sum"), yds=("yards_gained", "sum"), **{k: (v, "sum") for k, v in ev.items()}).reset_index().merge(tv[["posteam", "season", "week", "game_id", vcol]].rename(columns={vcol: "team_n"}), on=["posteam", "season", "week", "game_id"], how="left")
    cols = ["n", "yds", "team_n"] + list(ev); R = prev_sums(pg, ["pid"], cols); sf, tf = (PR.FADE.get(kind, (1.0, 1.0)) if globals().get("FADE_ON", True) else (1.0, 1.0))
    PARTIAL = globals().get("PARTIAL_MODE") or __import__("os").environ.get("PARTIAL")   # 24 Sep 2026, experiments/partial_games.py
    if PARTIAL in ("exclude", "weight") and kind in ("rec", "rush"):
        from nflmodel.exposure import load as _exp
        ex = _exp()[["player_id", "game_id", "off_pct"]].rename(columns={"player_id": "pid"})
        pgx = pg.merge(ex, on=["pid", "game_id"], how="left").sort_values(["pid", "season", "week"])
        med = pgx.groupby("pid").off_pct.transform(lambda v: v.shift(1).rolling(8, min_periods=3).median())
        e = (pgx.off_pct / med).clip(upper=1.0).fillna(1.0)
        if PARTIAL == "exclude":
            keep = (e >= 0.5).astype(float); pgx["n"] = pgx.n * keep; pgx["team_n"] = pgx.team_n * keep
        else:
            pgx["team_n"] = pgx.team_n * e
        R85 = fade_sums(pgx, ["pid"], ["n", "team_n"], PR.DECAY, sf, tf).rename(columns={"n": "n_85", "team_n": "team_n_85"})
    else:
        R85 = fade_sums(pg, ["pid"], ["n", "team_n"], PR.DECAY, sf, tf).rename(columns={"n": "n_85", "team_n": "team_n_85"})
    dg = t.groupby(["defteam", "season", "week", "game_id"]).agg(d_n=("n", "sum"), d_yds=("yards_gained", "sum")).reset_index(); D = prev_sums(dg, ["defteam"], ["d_n", "d_yds"])
    f = pg[["pid", "posteam", "season", "week", "game_id", "n", "yds"] + list(ev)].rename(columns={"n": "act_n", "yds": "act_yds", **{k: f"act_{k}" for k in ev}})
    f = f.merge(R[["pid", "game_id", "games_prev"] + cols], on=["pid", "game_id"]).merge(R85[["pid", "game_id", "n_85", "team_n_85"]], on=["pid", "game_id"])
    f = f.merge(games, on="game_id").merge(d[["game_id", "posteam", "defteam"]].drop_duplicates(), on=["game_id", "posteam"]).merge(T17[["posteam", "game_id", vcol, "games_prev"]].rename(columns={vcol: "tv", "games_prev": "tgames"}), on=["posteam", "game_id"]).merge(D[["defteam", "game_id", "d_n", "d_yds"]], on=["defteam", "game_id"]).merge(ALW[["defteam", "game_id", "a_tdb", "agames"]], on=["defteam", "game_id"])
    f = f.merge(feat.rename(columns={"team": "posteam"})[["game_id", "posteam", "wind"]], on=["game_id", "posteam"], how="left"); f["wind"] = f.wind.fillna(0.0)
    minv = MIN_VOL * (3 if kind == "pass" else 1); f = f[(f.n >= minv) & (f.games_prev >= 3) & (f.tgames >= 3) & (f.agames >= 3) & (f.season >= 2017)].copy()
    if kind == "pass": f = f[f.act_n >= 10]
    f["me"] = pd.Series(np.where(f.posteam == f.home_team, f.spread_line, -f.spread_line), index=f.index).astype(float).fillna(0.0); f["tc"] = (f.total_line - PR.GS_TOTAL).fillna(0.0)
    lg = lg_series(f, lgp.assign(yards_gained=lgp.yards_gained.fillna(0.0)), "yards_gained", float(lgp.yards_gained.mean())); K, W = PR.K[kind], PR.W[kind]; b = PR.GS[kind]
    f["d_rate"] = np.where(f.d_n >= 100, f.d_yds / f.d_n.replace(0, np.nan), np.nan); adj = lambda base, w=W: base * np.where(f.d_rate.notna(), 1 + w * (f.d_rate / lg - 1), 1.0)
    team_pg = f.tv / f.tgames
    if kind == "pass": team_pg = (1 - PR.PACE["pass"]) * team_pg + PR.PACE["pass"] * f.a_tdb / f.agames
    share = 1.0 if kind == "pass" else f.n_85 / f.team_n_85.replace(0, np.nan); share_flat = 1.0 if kind == "pass" else f.n / f.team_n.replace(0, np.nan)
    f["vol"] = share * (team_pg + b[0] + b[1] * f.me + b[2] * f.tc); vol_raw = share_flat * f.tv / f.tgames
    wind = 1 + PR.WIND_C[kind] * np.maximum(f.wind - 10, 0)
    f["yds_line"] = PR.MED[kind] * adj(f.vol * (f.yds + K * lg) / (f.n + K)) * wind; f["yds_raw"] = vol_raw * f.yds / f.n
    lgc = {k: lg_series(f, t, v, float(t[v].mean())) for k, v in ev.items()}
    for k in ev:
        if k == "catch": f["catch_line"] = PR.MED_CATCH * f.vol * (f[k] + PR.K_CATCH * lgc[k]) / (f.n + PR.K_CATCH)
        elif k == "td": f["td_line"] = f.vol * (f[k] + PR.K_TD[kind] * lgc[k]) / (f.n + PR.K_TD[kind]) * (1 + PR.TD_MARGIN[kind] * f.me)
        else: f["int_line"] = f.vol * lgc[k]
        f[f"{k}_raw"] = vol_raw * f[k] / f.n
    # round 6: the team's players moved toward the team's expected yards and touchdowns from the game model's expected points
    f = f.merge(pred, on="game_id", how="left"); f["exp_pts"] = np.where(f.posteam == f.home_team, f.home_exp, f.away_exp)
    fy, ft = PR.TEAM_FIT[kind]["yds"], PR.TEAM_FIT[kind]["td"]; wy, wt = PR.RECON_W[kind]["yds"], PR.RECON_W[kind]["td"]
    tg = f.groupby(["game_id", "posteam"]).agg(sum_y=("yds_line", "sum"), sum_t=("td_line", "sum")).reset_index(); f = f.merge(tg, on=["game_id", "posteam"], how="left")
    ok = f.exp_pts.notna()
    scale_y = ((fy[0] + fy[1] * f.exp_pts) / f.sum_y.replace(0, np.nan)).clip(0.5, 2.0); scale_t = ((ft[0] + ft[1] * f.exp_pts) / f.sum_t.replace(0, np.nan)).clip(0.5, 2.0)
    f["yds_line"] = np.where(ok & scale_y.notna(), f.yds_line * (1 + wy * (scale_y - 1)), f.yds_line); f["td_line"] = np.where(ok & scale_t.notna(), f.td_line * (1 + wt * (scale_t - 1)), f.td_line)
    f["pos"] = f.pid.map(pos_of).fillna("?"); return f, ev
def score(x, line, actual, count=False):
    e = x[line] - x[actual]; out = {"n": int(len(x)), "mae": round(float(e.abs().mean()), 3 if count else 2), "bias": round(float(e.mean()), 3 if count else 2), "mean_line": round(float(x[line].mean()), 3 if count else 1), "mean_actual": round(float(x[actual].mean()), 3 if count else 1)}
    if count:
        out.update({"ll": round(pll(x[line].values, x[actual].values), 4), "anytime_pred": round(float((1 - np.exp(-np.clip(x[line], 1e-3, None))).mean()), 3), "anytime_actual": round(float((x[actual] >= 1).mean()), 3)})
    else:
        nz = x[x[actual] != x[line]]; out["over_rate"] = round(float((nz[actual] > nz[line]).mean()), 3)
    return out
by_season, by_pos, by_bucket = [], [], []
for kind, stat in [("rec", "rec"), ("rush", "rush"), ("pass", "pass")]:
    f, ev = build(kind); print(stat, len(f), flush=True)
    stats = [("yards", "yds_line", "yds_raw", "act_yds", False)] + [(k, f"{k}_line", f"{k}_raw", f"act_{k}", k != "catch") for k in ev]
    for name, line, raw, act, count in stats:
        sname = f"{stat}_{ 'catches' if name == 'catch' else name}"
        for s, g in f.groupby("season"):
            by_season.append({"stat": sname, "season": int(s), **score(g, line, act, count), **{f"raw_{k}": v for k, v in score(g, raw, act, count).items() if k in ("mae", "bias", "ll", "over_rate")}})
        for win, (a, bb) in {"2019-22": (2019, 2022), "2023-25": (2023, 2025), "all": (2017, 2025)}.items():
            g = f[f.season.between(a, bb)]
            by_season.append({"stat": sname, "season": win, **score(g, line, act, count), **{f"raw_{k}": v for k, v in score(g, raw, act, count).items() if k in ("mae", "bias", "ll", "over_rate")}})
            if kind != "pass":
                for p, gp in g.groupby("pos"):
                    if len(gp) >= 200: by_pos.append({"stat": sname, "window": win, "position": p, **score(gp, line, act, count)})
            if not count:
                edges = [0, 20, 40, 60, 80, 1000] if kind != "pass" else [0, 150, 200, 250, 300, 1000]
                g2 = g.assign(bucket=pd.cut(g[line], edges, right=False))
                for bk, gb in g2.groupby("bucket", observed=True):
                    if len(gb) >= 50: by_bucket.append({"stat": sname, "window": win, "line_from": int(bk.left), "line_to": int(bk.right) if bk.right < 1000 else None, **score(gb, line, act)})
pd.DataFrame(by_season).to_csv("reports/props_by_season.csv", index=False); pd.DataFrame(by_pos).to_csv("reports/props_by_position.csv", index=False); pd.DataFrame(by_bucket).to_csv("reports/props_by_bucket.csv", index=False)
print(pd.DataFrame(by_season).to_string()); print("DONE")
