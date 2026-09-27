"""Round fourteen (27 Sep 2026): the anytime-touchdown price. This week's cards had the players the book prices under
10% at a model average of 12% (backups with a stale role: Bam Knight 27%, Tyrone Tracy 28%) and the players it prices
at 30%+ at 37% against the book's 43%. Five suspected causes, each tested on the adopted rule (rounds one to thirteen),
walk-forward, our own data only (no market), fitted on 2017-18 and scored on 2019-22 and 2023-25 by the Poisson log
loss on the touchdown count, the log loss and Brier score of P(anytime) = 1 - exp(-mu) against scored-or-not, and a
calibration table (predicted P(anytime) bucketed, mean predicted against the actual rate):

  frame. The by-season frame (props_by_season.build, reused by rounds 5, 6 and 13) holds only player-games with a touch,
         so a healthy backup who played and got nothing is never graded and over-projecting him is invisible. The
         "active" frame adds every game a projected player (previous-window touches at the frame's minimum) played
         offensive snaps in (data/processed/snap_exposure.parquet) and had no touch of the kind, with 0 actual.
         Every variant is scored on both frames; the active frame, the population the live rule projects, decides.
  V1.   Volume: the round-13 injury-report factor and snap trend (his snap share over his last 3 games against his
         last 10), applied only to the yards lines so far, on the touchdown volume (w = 0.25, 0.5, 1; before or after
         the team scaling).
  V2.   Shares normalised: when the playing players' usage shares add up to more than 1 they are scaled down to 1
         (cap); always scaled to 1 (norm) for reference (round 10 found scaling up lost).
  V3.   The prior the per-touch rate is shrunk toward: the league rate x a factor by usage tier (touches per game, or
         decayed share) and/or by position (QB, RB, WR, TE), each factor = that group's touchdowns per touch over the
         league's on 2017-18.
  V4.   Team reconcile weight 0.75 and 1.0 (0.5 today for receiving and rushing), and the size and source of the
         players' over-sum against the team's expected touchdowns.
  V6.   The usage share itself: the live rule's _share decays his touches over the team's plays in HIS games with a
         touch, so a backup's games without one never enter it and his volume is that of his good days; here the
         share is over every game he was active for (snap counts), a game without a touch counting 0.
  V5.   The winners together, in two stages: V6 first when it wins on both windows, then every other family re-run on
         top of it and per family the best that still wins on both windows kept (V6+<variant> rows).
Output reports/props_backtest14.csv (one row per frame x stat x variant x window) and
reports/props_backtest14_calibration.csv (the bucket table per frame x stat x variant x window)."""
import numpy as np, pandas as pd, pathlib
from nflmodel import props as PR
from nflmodel.features import OUT
src = pathlib.Path(__file__).with_name("props_by_season.py").read_text().split("by_season, by_pos, by_bucket = [], [], []")[0]
ns = {"__name__": "bys"}; exec(compile(src, "bys", "exec"), ns)
d, tv, T17, ALW, games, pred, pos_of = ns["d"], ns["tv"], ns["T17"], ns["ALW"], ns["games"], ns["pred"], ns["pos_of"]
prev_sums, fade_sums, lg_series, pll = ns["prev_sums"], ns["fade_sums"], ns["lg_series"], ns["pll"]
REP, SNAP, MIN_VOL = ns["_REP"], ns["_SNAP"], ns["MIN_VOL"]
WIN = {"2019-22": (2019, 2022), "2023-25": (2023, 2025)}; FIT = (2017, 2018)
BUCKETS = [0, 0.05, 0.10, 0.20, 0.30, 0.40, 1.0001]
TIERS = {"rec": [3, 5, 7], "rush": [4, 8, 13]}            # touches per game: the edges of the usage tiers (last tier open)
SHARE_TIERS = {"rec": [0.08, 0.15, 0.22], "rush": [0.15, 0.35, 0.55]}
POS_GROUP = {"rec": {"WR": "WR", "TE": "TE", "RB": "RB", "FB": "RB", "HB": "RB"}, "rush": {"QB": "QB", "RB": "RB", "FB": "RB", "HB": "RB", "WR": "WR", "TE": "WR"}}
SKILL = {"rec": {"WR", "TE", "RB", "FB", "HB"}, "rush": {"RB", "FB", "HB", "QB", "WR", "TE"}}
ACT = pd.read_parquet(OUT / "snap_exposure.parquet", columns=["player_id", "game_id", "season", "week", "team", "position", "off_pct"]).rename(columns={"player_id": "pid", "team": "posteam"})
ACT = ACT[(ACT.off_pct > 0) & (ACT.season >= 2016)].drop_duplicates(["pid", "game_id"])
# every player's actual receiving and rushing touchdowns per game, whichever frame he is in (the anytime price covers both)
ACTTD = d[d.pass_play & d.receiver_player_id.notna()].groupby(["receiver_player_id", "game_id"]).pass_touchdown.sum().rename("rec").reset_index().rename(columns={"receiver_player_id": "pid"}).merge(
    d[d.play_type.eq("run") & d.rusher_player_id.notna()].groupby(["rusher_player_id", "game_id"]).rush_touchdown.sum().rename("rush").reset_index().rename(columns={"rusher_player_id": "pid"}), how="outer").fillna(0.0)
ACTTD["any"] = ACTTD.rec + ACTTD.rush


def frame(kind, active):
    """The by-season frame's touchdown inputs, walk-forward, with (active=True) the zero-touch games of a projected player
    who played snaps. State columns (previous-window sums, the decayed usage) are those after his previous touch game."""
    if kind == "rec":
        t = d[d.pass_play & d.receiver_player_id.notna()].rename(columns={"receiver_player_id": "pid"}); vcol, tdcol = "tp", "pass_touchdown"
    elif kind == "rush":
        t = d[d.play_type.eq("run") & d.rusher_player_id.notna()].rename(columns={"rusher_player_id": "pid"}); vcol, tdcol = "tr", "rush_touchdown"
    else:
        t = d[d.dropback & d.passer_player_id.notna()].rename(columns={"passer_player_id": "pid"}); vcol, tdcol = "tdb", "pass_touchdown"; active = False
    t = t.copy(); t["n"] = 1
    pg = t.groupby(["pid", "posteam", "season", "week", "game_id"]).agg(n=("n", "sum"), td=(tdcol, "sum")).reset_index().merge(tv[["posteam", "season", "week", "game_id", vcol]].rename(columns={vcol: "team_n"}), on=["posteam", "season", "week", "game_id"], how="left")
    last = pg.sort_values(["pid", "season", "week"]).groupby("pid").tail(1)[["pid", "posteam"]].assign(season=9999, week=0, game_id="dummy", n=0, td=0.0, team_n=0.0)   # a sentinel after his last touch game: the state a later zero-touch game reads
    pgd = pd.concat([pg, last], ignore_index=True); sf, tf = PR.FADE.get(kind, (1.0, 1.0))
    R = prev_sums(pgd, ["pid"], ["n", "team_n", "td"]); R[["n", "team_n", "td"]] = R[["n", "team_n", "td"]].fillna(0.0)
    R["last_sn"] = pgd.sort_values(["pid", "season", "week"]).reset_index(drop=True).groupby("pid").season.shift(1).values   # the season of his previous touch game
    R85 = fade_sums(pgd, ["pid"], ["n", "team_n"], PR.DECAY, sf, tf).rename(columns={"n": "n_85", "team_n": "team_n_85"})
    # V6: the same decayed usage over every game he was active for, a game he played without a touch counting 0 over the team's plays
    za = ACT[ACT.pid.isin(pg.pid.unique()) & ACT.position.isin(SKILL.get(kind, set()))].merge(pg[["pid", "game_id"]].assign(has=1), on=["pid", "game_id"], how="left")
    za = za[za.has.isna()][["pid", "posteam", "season", "week", "game_id"]].merge(tv[["posteam", "season", "week", "game_id", vcol]].rename(columns={vcol: "team_n"}), on=["posteam", "season", "week", "game_id"], how="inner").assign(n=0, td=0.0)
    R85a = fade_sums(pd.concat([pg, za, last], ignore_index=True), ["pid"], ["n", "team_n"], PR.DECAY, sf, tf).rename(columns={"n": "n_85a", "team_n": "team_n_85a"})
    f = pg.rename(columns={"n": "act_n", "td": "act_td"})[["pid", "posteam", "season", "week", "game_id", "act_n", "act_td"]].assign(touch=1)
    if active:
        zt = ACT[ACT.pid.isin(pg.pid.unique()) & ACT.position.isin(SKILL[kind])].merge(pg[["pid", "game_id"]].assign(has=1), on=["pid", "game_id"], how="left")
        zt = zt[zt.has.isna()][["pid", "posteam", "season", "week", "game_id"]].assign(act_n=0, act_td=0.0, touch=0)
        f = pd.concat([f, zt], ignore_index=True)
    f = pd.concat([f, last[["pid", "posteam", "season", "week", "game_id"]].assign(act_n=0, act_td=0.0, touch=1)], ignore_index=True)
    f = f.merge(R[["pid", "game_id", "games_prev", "n", "team_n", "td", "last_sn"]], on=["pid", "game_id"], how="left").merge(R85[["pid", "game_id", "n_85", "team_n_85"]], on=["pid", "game_id"], how="left").merge(R85a[["pid", "game_id", "n_85a", "team_n_85a"]], on=["pid", "game_id"], how="left").sort_values(["pid", "season", "week"])
    state = ["games_prev", "n", "team_n", "td", "last_sn", "n_85", "team_n_85"]; f[state] = f.groupby("pid")[state].bfill(); f = f[f.season < 9999].copy()
    f = f.merge(games, on="game_id").merge(d[["game_id", "posteam", "defteam"]].drop_duplicates(), on=["game_id", "posteam"]).merge(T17[["posteam", "game_id", vcol, "games_prev"]].rename(columns={vcol: "tv", "games_prev": "tgames"}), on=["posteam", "game_id"]).merge(ALW[["defteam", "game_id", "a_tdb", "agames"]], on=["defteam", "game_id"])
    minv = MIN_VOL * (3 if kind == "pass" else 1); f = f[(f.n >= minv) & (f.games_prev >= 3) & (f.tgames >= 3) & (f.agames >= 3) & (f.season >= 2017)].copy()
    f = f[(f.touch == 1) | (f.last_sn >= f.season - 1)]   # a zero-touch game counts only while the live rule would carry him (a touch last season or this)
    if kind == "pass": f = f[f.act_n >= 10]
    f["me"] = pd.Series(np.where(f.posteam == f.home_team, f.spread_line, -f.spread_line), index=f.index).astype(float).fillna(0.0); f["tc"] = (f.total_line - PR.GS_TOTAL).fillna(0.0); b = PR.GS[kind]
    team_pg = f.tv / f.tgames
    if kind == "pass": team_pg = (1 - PR.PACE["pass"]) * team_pg + PR.PACE["pass"] * f.a_tdb / f.agames
    f["tplays"] = team_pg + b[0] + b[1] * f.me + b[2] * f.tc
    f["share"] = 1.0 if kind == "pass" else (f.n_85 / f.team_n_85.replace(0, np.nan)).fillna(0.0); f["share_a"] = 1.0 if kind == "pass" else (f.n_85a / f.team_n_85a.replace(0, np.nan)).fillna(0.0)
    f["lg"] = lg_series(f, t, tdcol, float(t[tdcol].mean())); f["mf"] = 1 + PR.TD_MARGIN[kind] * f.me
    f = f.merge(pred, on="game_id", how="left"); f["exp_pts"] = np.where(f.posteam == f.home_team, f.home_exp, f.away_exp)
    f = f.merge(REP, on=["pid", "season", "week"], how="left").merge(SNAP, on=["pid", "game_id"], how="left")
    f["grp"] = [PR.inj_group(a_, b_) for a_, b_ in zip(f.report_status, f.practice_status)]; f["sr"] = [PR.snap_ratio(a_, b_) for a_, b_ in zip(f.s3, f.s10)]
    f["pos"] = f.pid.map(pos_of).fillna("?"); f["tpg"] = f.n / f.games_prev.replace(0, np.nan)
    return f.reset_index(drop=True)


def project(f, kind, cap=None, prior=None, wt=None, inj=False, snap_w=0.0, pre=False, share_col="share"):
    """mu, the expected touchdowns of the kind: share (capped or normalised over the team's playing players when asked)
    x the team's game-script plays, x his rate shrunk toward the prior (league x factor) with K_TD touches of weight
    and moved TD_MARGIN per point of margin, scaled wt of the way toward the team's expected touchdowns from the game
    model's points; the round-13 factors (injury report, snap trend w) before (pre) or after the team scaling."""
    wt = PR.RECON_W[kind]["td"] if wt is None else wt; K = PR.K_TD[kind]; ft = PR.TEAM_FIT[kind]["td"]
    share = f[share_col].values.copy()
    if cap is not None and kind != "pass":
        s = f.groupby(["game_id", "posteam"])[share_col].transform("sum").values
        share = np.where(s > 1, share / s, share) if cap == "cap" else np.where(s > 0, share / s, share)
    vol = share * f.tplays.values
    fac = np.ones(len(f))
    if inj: fac = fac * np.array([PR.INJ_F.get(kind, {}).get(g_, 1.0) for g_ in f.grp])
    if snap_w: fac = fac * (1 + snap_w * (f.sr.values - 1))
    if pre: vol = vol * fac
    pr = f.lg.values * (prior if prior is not None else 1.0)
    mu0 = vol * (f.td.values + K * pr) / (f.n.values + K) * f.mf.values
    sum_t = pd.Series(mu0, index=f.index).groupby([f.game_id, f.posteam]).transform("sum").values
    with np.errstate(divide="ignore", invalid="ignore"):
        scale = np.clip((ft[0] + ft[1] * f.exp_pts.values) / np.where(sum_t > 0, sum_t, np.nan), 0.5, 2.0)
    mu = np.where(np.isfinite(scale), mu0 * (1 + wt * (scale - 1)), mu0)
    if not pre: mu = mu * fac
    return np.clip(mu, 1e-4, None)


def metrics(mu, k):
    p = np.clip(1 - np.exp(-mu), 1e-4, 1 - 1e-4); y = (k >= 1).astype(float)
    return {"n": int(len(k)), "ll_pois": round(pll(mu, k), 4), "ll_any": round(float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))), 4), "brier": round(float(np.mean((p - y) ** 2)), 4), "mean_p": round(float(p.mean()), 4), "act_rate": round(float(y.mean()), 4), "mean_mu": round(float(mu.mean()), 4), "mean_k": round(float(k.mean()), 4)}


def calib(mu, k):
    p = 1 - np.exp(-mu); y = (k >= 1).astype(float); idx = np.digitize(p, BUCKETS[1:-1]); out = []
    for i in range(len(BUCKETS) - 1):
        m = idx == i
        if m.sum(): out.append({"bucket": f"{BUCKETS[i]:.0%}-{BUCKETS[i + 1]:.0%}" if i < len(BUCKETS) - 2 else f"{BUCKETS[i]:.0%}+", "n": int(m.sum()), "mean_pred": round(float(p[m].mean()), 4), "actual_rate": round(float(y[m].mean()), 4)})
    return out


def tier_factors(f, edges, col):
    """Touchdowns per touch of each usage tier (by col: touches per game or decayed share) over the league's, 2017-18."""
    x = f[f.season.between(*FIT) & (f.act_n > 0)]; lg = x.act_td.sum() / x.act_n.sum(); idx = np.digitize(x[col].values, edges); out = []
    for i in range(len(edges) + 1):
        m = idx == i; out.append(round(float((x.act_td[m].sum() / x.act_n[m].sum()) / lg), 3) if m.sum() else 1.0)
    return out


def pos_factors(f, groups):
    x = f[f.season.between(*FIT) & (f.act_n > 0)]; lg = x.act_td.sum() / x.act_n.sum(); g = x.pos.map(groups).fillna("other")
    return {p_: round(float((x.act_td[g == p_].sum() / x.act_n[g == p_].sum()) / lg), 3) for p_ in g.unique() if (g == p_).sum() >= 200}


def main():
    rows, cal = [], []; ANY = {}   # (frame, variant) -> {kind: (f, mu)} for the combined anytime price
    def score(fr, stat, variant, f, mu, note=""):
        for w, (a, b) in WIN.items():
            m = f.season.between(a, b).values; rows.append({"frame": fr, "stat": stat, "variant": variant, "window": w, **metrics(mu[m], f.act_td.values[m]), "note": note})
            for c in calib(mu[m], f.act_td.values[m]): cal.append({"frame": fr, "stat": stat, "variant": variant, "window": w, **c})
        print(fr, stat, variant, {w: (r["ll_pois"], r["ll_any"], r["brier"]) for w, r in zip(WIN, rows[-2:])}, note, flush=True)
    for active in (False, True):
        fr = "active" if active else "touch"; F = {}
        for kind in ("rec", "rush", "pass"):
            f = frame(kind, active); F[kind] = f; stat = f"{kind}_td"; K = PR.K_TD[kind]
            print(fr, kind, "rows", len(f), "zero-touch", int((f.touch == 0).sum()), flush=True)
            base = project(f, kind); score(fr, stat, "base", f, base)
            # V4 diagnostics on the fit years: the playing players' shares and their touchdowns before the team scaling against the team's actual
            x = f.assign(mu0=project(f, kind, wt=0.0)); x = x[x.season.between(*FIT)]
            if kind != "pass":
                tg = x.groupby(["game_id", "posteam"]).agg(sh=("share", "sum"), mu0=("mu0", "sum"), act=("act_td", "sum"), exp=("exp_pts", "first")); ft = PR.TEAM_FIT[kind]["td"]
                note = f"fit years: mean share sum {tg.sh.mean():.3f} (share of team-games over 1: {(tg.sh > 1).mean():.2f}); players' sum / actual {tg.mu0.sum() / tg.act.sum():.3f}; TEAM_FIT exp / actual {(ft[0] + ft[1] * tg.exp).sum() / tg.act.sum():.3f}"
                rows.append({"frame": fr, "stat": stat, "variant": "diag", "window": "2017-18", "n": int(len(tg)), "note": note}); print(fr, kind, note, flush=True)
            if kind == "pass":
                ANY.setdefault((fr, "base"), {})
                continue
            # V1. the round-13 factors on the touchdown volume
            score(fr, stat, "V1_inj", f, project(f, kind, inj=True))
            for w in (0.25, 0.5, 1.0): score(fr, stat, f"V1_snap_w{w}", f, project(f, kind, snap_w=w))
            score(fr, stat, "V1_snap_w0.5_pre", f, project(f, kind, snap_w=0.5, pre=True))
            score(fr, stat, "V1_inj_snap_w0.5", f, project(f, kind, inj=True, snap_w=0.5))
            # V2. shares normalised over the playing players
            score(fr, stat, "V2_cap1", f, project(f, kind, cap="cap")); score(fr, stat, "V2_norm", f, project(f, kind, cap="norm"))
            # V3. the prior by usage tier and by position
            tf_ = tier_factors(f, TIERS[kind], "tpg"); pt = np.array(tf_)[np.digitize(f.tpg.values, TIERS[kind])]
            score(fr, stat, "V3_tier_tpg", f, project(f, kind, prior=pt), f"tiers per game {TIERS[kind]}: {tf_}")
            sf_ = tier_factors(f, SHARE_TIERS[kind], "share"); ps = np.array(sf_)[np.digitize(f.share.values, SHARE_TIERS[kind])]
            score(fr, stat, "V3_tier_share", f, project(f, kind, prior=ps), f"share tiers {SHARE_TIERS[kind]}: {sf_}")
            pf_ = pos_factors(f, POS_GROUP[kind]); pp = f.pos.map(POS_GROUP[kind]).fillna("other").map(pf_).fillna(1.0).values
            score(fr, stat, "V3_pos", f, project(f, kind, prior=pp), f"position factors {pf_}")
            score(fr, stat, "V3_pos_tier_tpg", f, project(f, kind, prior=pp * pt), "position x per-game tier")
            # V4. the team reconcile weight
            for w in (0.75, 1.0): score(fr, stat, f"V4_recon{w}", f, project(f, kind, wt=w))
            # V6. the usage share over every game he was active for (a game without a touch counts 0), not his touch games alone
            score(fr, stat, "V6_share_active", f, project(f, kind, share_col="share_a"), f"mean share {f.share.mean():.3f} -> {f.share_a.mean():.3f}")
            score(fr, stat, "V6_share_active_cap1", f, project(f, kind, share_col="share_a", cap="cap"))
            score(fr, stat, "V6_share_active_snap_w0.25", f, project(f, kind, share_col="share_a", snap_w=0.25))
            # V5. the winners together, in two stages: the share (V6) first when it wins on both windows; then every other
            # family's options re-run on top of it, and per family the best that still wins on both windows (Poisson log loss
            # lower on both, anytime log loss no worse) is kept
            def res(v): return {x_["window"]: x_ for x_ in rows if x_["frame"] == fr and x_["stat"] == stat and x_["variant"] == v}
            def wins(v, ref): r, b_ = res(v), res(ref); return all(r[w]["ll_pois"] < b_[w]["ll_pois"] and r[w]["ll_any"] <= b_[w]["ll_any"] for w in WIN)
            def total(v): r = res(v); return r["2019-22"]["ll_pois"] + r["2023-25"]["ll_pois"]
            kw = {"share_col": "share_a"} if wins("V6_share_active", "base") else {}; ref = "V6_share_active" if kw else "base"; taken = ["V6_share_active"] if kw else []
            opts = {"V1": {"V1_inj": dict(inj=True), "V1_snap_w0.25": dict(snap_w=0.25), "V1_snap_w0.5": dict(snap_w=0.5), "V1_snap_w1.0": dict(snap_w=1.0), "V1_snap_w0.5_pre": dict(snap_w=0.5, pre=True), "V1_inj_snap_w0.5": dict(inj=True, snap_w=0.5)},
                    "V2": {"V2_cap1": dict(cap="cap"), "V2_norm": dict(cap="norm")}, "V3": {"V3_tier_tpg": dict(prior=pt), "V3_tier_share": dict(prior=ps), "V3_pos": dict(prior=pp), "V3_pos_tier_tpg": dict(prior=pp * pt)}, "V4": {"V4_recon0.75": dict(wt=0.75), "V4_recon1.0": dict(wt=1.0)}}
            stage2, base_kw = bool(kw), dict(kw)
            for fam, vs in opts.items():
                ok = []
                for v, o in vs.items():
                    name = v
                    if stage2: name = f"V6+{v}"; score(fr, stat, name, f, project(f, kind, **base_kw, **o))
                    if wins(name, ref): ok.append((total(name), v, o))
                if ok: _, v, o = min(ok); kw.update(o); taken.append(v)
            combo = project(f, kind, **kw) if kw else base
            score(fr, stat, "V5_combo", f, combo, "together: " + (", ".join(taken) if taken else "nothing won on both windows"))
            for v, mu in (("base", base), ("V5_combo", combo)): ANY.setdefault((fr, v), {})[kind] = (f, mu)
        # the anytime price the book posts: receiving plus rushing per player-game, over the union of the two frames
        for (fr_, v), parts in list(ANY.items()):
            if fr_ != fr or not parts: continue
            u = None
            for kind, (f, mu) in parts.items():
                x = f[["pid", "game_id", "season"]].assign(**{f"mu_{kind}": mu}); u = x if u is None else u.merge(x, on=["pid", "game_id", "season"], how="outer")
            u = u.fillna(0.0); u["mu"] = u.get("mu_rec", 0.0) + u.get("mu_rush", 0.0); u["act_td"] = u[["pid", "game_id"]].merge(ACTTD, on=["pid", "game_id"], how="left")["any"].fillna(0.0).values
            score(fr, "any_td", v, u, u.mu.values)
    o = pd.DataFrame(rows); o.to_csv("reports/props_backtest14.csv", index=False); c = pd.DataFrame(cal); c.to_csv("reports/props_backtest14_calibration.csv", index=False)
    print(o.drop(columns=["note"]).to_string(index=False)); print(c[c.variant.isin(["base", "V5_combo"])].to_string(index=False)); print("DONE")


if __name__ == "__main__":
    main()
