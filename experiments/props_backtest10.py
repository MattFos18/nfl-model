"""Round ten (23 Sep 2026): three player-side claims, each on the adopted rule (rounds one to nine), walk-forward,
scored on 2019 to 2022 and 2023 to 2025.
  A. Target redistribution when a teammate is out. The page gives the share of every listed player who is out to the
     rest pro rata. Tested here with hindsight absences (a player with 5%+ of the team's usage who played in the
     team's last three games and not this one): no redistribution; pro rata in full and by half; to the same
     position group (WR, TE, RB) in full and by half. Scored on volume (targets, carries) and on the yards line.
  B. Red-zone role for touchdowns. Expected touchdowns per touch from where he is targeted or handed the ball
     (league scoring rate by yard line, 2016 to 2018) as the prior his own rate is shrunk toward, instead of the
     league average; and that expected rate on its own. Poisson log loss.
  C. Offseason fade. Usage share decayed across the season boundary by an extra factor (0.5, 0.25), and across a
     change of team (0.5, 0.25), so last year's role counts for less in September. Volume and yards.
Output reports/props_backtest10.csv."""
import numpy as np, pandas as pd, pathlib
from nflmodel import props as PR
src = pathlib.Path(__file__).with_name("props_by_season.py").read_text().split("by_season, by_pos, by_bucket = [], [], []")[0]
ns = {"__name__": "bys", "FADE_ON": False}; exec(compile(src, "bys", "exec"), ns); build = ns["build"]; pll = ns["pll"]; d = ns["d"]; tv = ns["tv"]; prev_sums = ns["prev_sums"]; pos_of = ns["pos_of"]
WIN = {"2019-22": (2019, 2022), "2023-25": (2023, 2025)}; N = 17
GRP = lambda p: "RB" if p in ("RB", "FB", "HB") else ("TE" if p == "TE" else ("QB" if p == "QB" else "WR"))
rows = []
def ev(f, col, act, count=False):
    out = {}
    for w, (a, b) in WIN.items():
        x = f[f.season.between(a, b)]; out[f"mae_{w}"] = round(float((x[col] - x[act]).abs().mean()), 3); out[f"ll_{w}"] = (round(pll(x[col].values, x[act].values), 4) if count else None); out[f"n_{w}"] = int(len(x))
    return out
def recon(f, col, kind, which):
    """Round six: the team's players scaled toward the team's expected yards or touchdowns from the game model."""
    fit, w = PR.TEAM_FIT[kind][which], PR.RECON_W[kind][which]
    tg = f.groupby(["game_id", "posteam"])[col].sum().rename("_sum").reset_index(); x = f[["game_id", "posteam"]].merge(tg, on=["game_id", "posteam"], how="left")["_sum"].values
    scale = np.clip((fit[0] + fit[1] * f.exp_pts.values) / np.where(x == 0, np.nan, x), 0.5, 2.0); ok = f.exp_pts.notna().values & ~np.isnan(scale)
    return np.where(ok, f[col].values * (1 + w * (scale - 1)), f[col].values)
def pieces(kind, f):
    lgp = {"rec": d[d.pass_play], "rush": d[d.play_type.eq("run")], "pass": d[d.dropback]}[kind]; lg = float(lgp.yards_gained.mean()); K, W = PR.K[kind], PR.W[kind]
    adj = np.where(f.d_rate.notna(), 1 + W * (f.d_rate / lg - 1), 1.0); wind = 1 + PR.WIND_C[kind] * np.maximum(f.wind - 10, 0); rate = (f.yds + K * lg) / (f.n + K)
    f["team_vol"] = f.vol / (f.n_85 / f.team_n_85.replace(0, np.nan)) if kind != "pass" else f.vol   # the team's plays with the game script
    def yline(vol): return PR.MED[kind] * vol * rate * adj * wind
    return yline
def played_table(kind):
    """Every player-game of the kind (no volume floor) with his usage share before and after the game."""
    if kind == "rec": t = d[d.pass_play & d.receiver_player_id.notna()].rename(columns={"receiver_player_id": "pid"}); vcol = "tp"
    else: t = d[d.play_type.eq("run") & d.rusher_player_id.notna()].rename(columns={"rusher_player_id": "pid"}); vcol = "tr"
    t = t.copy(); t["n"] = 1
    pg = t.groupby(["pid", "posteam", "season", "week", "game_id"]).agg(n=("n", "sum")).reset_index().merge(tv[["posteam", "season", "week", "game_id", vcol]].rename(columns={vcol: "team_n"}), on=["posteam", "season", "week", "game_id"], how="left")
    R85 = prev_sums(pg, ["pid"], ["n", "team_n"], decay=PR.DECAY).rename(columns={"n": "n_85", "team_n": "team_n_85"})
    pg = pg.merge(R85[["pid", "game_id", "n_85", "team_n_85", "games_prev"]], on=["pid", "game_id"])
    pg["share_pre"] = pg.n_85 / pg.team_n_85.replace(0, np.nan); pg["share_post"] = (PR.DECAY * pg.n_85 + pg.n) / (PR.DECAY * pg.team_n_85 + pg.team_n); pg["grp"] = pg.pid.map(pos_of).fillna("WR").map(GRP)
    return pg
def absences(pg):
    """Per team-game: the usage share of players out (5%+ of usage, seen in the team's last three games, not in this one),
    in total and by position group; the sum of the present players' shares, in total and by group."""
    out = {}
    for team, g in pg.groupby("posteam"):
        gl = g.drop_duplicates("game_id").sort_values(["season", "week"]).game_id.tolist(); by_game = {gid: x for gid, x in g.groupby("game_id")}
        last = {}   # pid -> (game index, share_post, games_prev + 1, grp)
        for i, gid in enumerate(gl):
            x = by_game[gid]; present = set(x.pid)
            o_all, o_grp, a_all, a_grp = 0.0, {}, 0.0, {}
            for pid, (j, sh, gp, grp) in last.items():
                if pid in present or i - j > 3 or sh < 0.05 or gp < 3: continue
                o_all += sh; o_grp[grp] = o_grp.get(grp, 0.0) + sh
            for r in x.itertuples():
                if r.games_prev >= 1 and not np.isnan(r.share_pre): a_all += r.share_pre; a_grp[r.grp] = a_grp.get(r.grp, 0.0) + r.share_pre
            out[(gid, team)] = (o_all, o_grp, a_all, a_grp)
            for r in x.itertuples(): last[r.pid] = (i, r.share_post, r.games_prev + 1, r.grp)
    return out
def fade_sums(a, keys, cols, decay, season_f, team_f):
    """prev_sums with an extra factor on the running sums when the season changes and when the player's team changes."""
    a = a.sort_values(keys + ["season", "week"]).reset_index(drop=True); out = a[keys + ["season", "week", "game_id"]].copy()
    vals = a[cols].values.astype(float); res = np.zeros_like(vals); gk = a[keys].astype(str).agg("|".join, axis=1).values; sn = a.season.values; tm = a.posteam.values; run = np.zeros(vals.shape[1]); last = None; ls = None; lt = None
    for i in range(len(a)):
        if gk[i] != last: run = np.zeros(vals.shape[1]); last = gk[i]; ls = sn[i]; lt = tm[i]
        if sn[i] != ls: run = run * season_f; ls = sn[i]
        if tm[i] != lt: run = run * team_f; lt = tm[i]
        res[i] = run; run = decay * run + vals[i]
    out[cols] = res; return out
def xtd_table(kind):
    """Expected touchdowns per touch from the yard line: league scoring rate by bucket on 2016 to 2018, summed per player-game."""
    if kind == "rec": t = d[d.pass_play & d.receiver_player_id.notna()].rename(columns={"receiver_player_id": "pid"}); tdc = "pass_touchdown"
    elif kind == "rush": t = d[d.play_type.eq("run") & d.rusher_player_id.notna()].rename(columns={"rusher_player_id": "pid"}); tdc = "rush_touchdown"
    else: t = d[d.dropback & d.passer_player_id.notna()].rename(columns={"passer_player_id": "pid"}); tdc = "pass_touchdown"
    t = t.copy(); t["bkt"] = pd.cut(t.yardline_100, [0, 3, 10, 20, 40, 100], labels=False); fit = t[t.season <= 2018]
    rate = fit.groupby("bkt")[tdc].mean().to_dict(); t["xtd"] = t.bkt.map(rate).astype(float); t["one"] = 1
    pg = t.groupby(["pid", "posteam", "season", "week", "game_id"]).agg(xtd=("xtd", "sum"), rz=("one", lambda s: int((t.loc[s.index, "yardline_100"] <= 20).sum()))).reset_index()
    X = prev_sums(pg, ["pid"], ["xtd", "rz"]); return X[["pid", "game_id", "xtd", "rz"]], {int(k): round(float(v), 4) for k, v in rate.items()}
for kind in ["rec", "rush", "pass"]:
    f, evs = build(kind); yline = pieces(kind, f); base_y = f.yds_line.values; f["act_vol"] = f.act_n
    # ---------------- A. redistribution (receivers and rushers) ----------------
    if kind != "pass":
        pg = played_table(kind); ab = absences(pg); f["grp"] = f.pid.map(pos_of).fillna("WR").map(GRP)
        o_all = np.array([ab.get((g, t), (0, {}, 0, {}))[0] for g, t in zip(f.game_id, f.posteam)]); o_grp = np.array([ab.get((g, t), (0, {}, 0, {}))[1].get(gr, 0.0) for g, t, gr in zip(f.game_id, f.posteam, f.grp)])
        a_all = np.array([ab.get((g, t), (0, {}, 0, {}))[2] for g, t in zip(f.game_id, f.posteam)]); a_grp = np.array([ab.get((g, t), (0, {}, 1, {}))[3].get(gr, 0.0) for g, t, gr in zip(f.game_id, f.posteam, f.grp)])
        F_pro = np.clip(1.0 / np.maximum(1.0 - o_all, 0.5), 1.0, 1.5); F_pos = np.clip(1.0 + o_grp / np.where(a_grp > 0, a_grp, np.nan), 1.0, 1.5); F_pos = np.where(np.isnan(F_pos), 1.0, F_pos)
        V = {"none": 1.0, "pro_rata": F_pro, "pro_rata_half": 1 + 0.5 * (F_pro - 1), "same_pos": F_pos, "same_pos_half": 1 + 0.5 * (F_pos - 1)}
        print(kind, "absences: share of team-games with someone out", round(float((o_all > 0).mean()), 3), "mean out share when out", round(float(o_all[o_all > 0].mean()), 3), flush=True)
        for name, F in V.items():
            f["_v"] = f.vol * F; f["_y"] = yline(f["_v"]); f["_yr"] = recon(f, "_y", kind, "yds")
            rows.append({"stat": f"{kind}_redistribution", "variant": name, **{k.replace("mae", "vol_mae"): v for k, v in ev(f, "_v", "act_vol").items() if k.startswith("mae")}, **ev(f, "_yr", "act_yds"), "fitted": "hindsight absences: 5%+ usage, seen in the team's last three games, not this one"})
    # ---------------- B. red-zone role (touchdowns) ----------------
    X, rate = xtd_table(kind); f = f.merge(X, on=["pid", "game_id"], how="left"); lgc = float({"rec": d[d.pass_play & d.receiver_player_id.notna()].pass_touchdown, "rush": d[d.play_type.eq("run") & d.rusher_player_id.notna()].rush_touchdown, "pass": d[d.dropback & d.passer_player_id.notna()].pass_touchdown}[kind].mean())
    margin = 1 + PR.TD_MARGIN[kind] * f.me; K0 = PR.K_TD[kind]; rate_x = (f.xtd / f.n).fillna(lgc)
    TV = {"league_prior": f.vol * (f.td + K0 * lgc) / (f.n + K0) * margin, "xtd_only": f.vol * rate_x * margin}
    for K in [100, 200, 400, 800]: TV[f"xtd_prior_K{K}"] = f.vol * (f.td + K * rate_x) / (f.n + K) * margin
    TV["xtd_prior_shrunk"] = f.vol * (f.td + K0 * ((f.xtd + 50 * lgc) / (f.n + 50))) / (f.n + K0) * margin   # the expected rate itself shrunk toward the league with 50 touches
    for name, col in TV.items():
        f["_t"] = col; f["_tr"] = recon(f, "_t", kind, "td")
        rows.append({"stat": f"{kind}_td_redzone", "variant": name, **ev(f, "_tr", "act_td", count=True), "fitted": "scoring rate by yard line (0-3, 4-10, 11-20, 21-40, 41+) on 2016 to 2018: " + ", ".join(f"{v:.3f}" for v in rate.values())})
    # ---------------- C. offseason fade (usage share; receivers and rushers) ----------------
    if kind != "pass":
        pgv = pg[["pid", "posteam", "season", "week", "game_id", "n", "team_n"]]
        for name, sf, tf in [("none", 1.0, 1.0), ("season_0.5", 0.5, 1.0), ("season_0.25", 0.25, 1.0), ("team_0.5", 1.0, 0.5), ("team_0.25", 1.0, 0.25), ("both_0.5", 0.5, 0.5), ("both_0.25", 0.25, 0.25), ("season_0.25_team_0.5", 0.25, 0.5), ("season_0.5_team_0.25", 0.5, 0.25)]:
            S = fade_sums(pgv, ["pid"], ["n", "team_n"], PR.DECAY, sf, tf).rename(columns={"n": "n_f", "team_n": "team_n_f"})
            g = f.merge(S[["pid", "game_id", "n_f", "team_n_f"]], on=["pid", "game_id"], how="left"); share = g.n_f / g.team_n_f.replace(0, np.nan)
            f["_v"] = (share * g.team_vol).values; f["_y"] = yline(f["_v"]); f["_yr"] = recon(f, "_y", kind, "yds")
            e = f[f.week <= 8]; early = {f"early_mae_{w}": round(float((e[e.season.between(a, b)]["_yr"] - e[e.season.between(a, b)].act_yds).abs().mean()), 3) for w, (a, b) in WIN.items()}
            rows.append({"stat": f"{kind}_fade", "variant": name, **{k.replace("mae", "vol_mae"): v for k, v in ev(f, "_v", "act_vol").items() if k.startswith("mae")}, **ev(f, "_yr", "act_yds"), **early, "fitted": f"season factor {sf}, team-change factor {tf}"})
    print(pd.DataFrame(rows)[pd.DataFrame(rows).stat.str.startswith(kind)].drop(columns=["fitted"]).to_string(), flush=True)
out = pd.DataFrame(rows); out.to_csv("reports/props_backtest10.csv", index=False); print("DONE")
