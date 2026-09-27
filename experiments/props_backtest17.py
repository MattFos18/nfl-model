"""Round seventeen (27 Sep 2026): the active-games usage share on the yards and receptions lines. Round 14 found that
the usage share behind every volume (_share) decays a player's touches over his team's plays in HIS games with a touch
only, so a backup's share is that of his good days, and moved the touchdown volume to the same share over every game
he was ACTIVE for (snap counts; a game without a touch counts 0 over the team's plays: share_td). The receiving and
rushing yards lines, and the receptions line, kept the touch-games share because rounds one to thirteen had chosen it
on a frame that never graded an empty game. Here that share is tested on the yards and receptions lines, on both
frames, walk-forward, our own data only (no market), nothing fitted beyond a blend weight:

  frames.   touch: the by-season frame (props_by_season.build: player-games with a touch of the kind, projected from
            the previous games). active: the same plus every game a projected player played offensive snaps in with no
            touch of the kind, actual 0 (round 14's frame(kind, active=True); the population the live cards project).
            The team reconciliation sums the frame's rows per team-game, so on the active frame it sums the players who
            played snaps, closer to what the card adds up.
  variants. base: the touch-games share (the adopted rule); share_a: the active-games share; blend_w: (1 - w) x base
            + w x share_a for w in 0.25, 0.5, 0.75 (the weight chosen on 2017-18 on the active frame if one is taken);
            share_a_cap1: share_a scaled down when the frame's players' shares add to more than one in a team-game
            (round 14 tested the same cap on touchdowns; on the touch frame the sum is over the players who touched,
            hindsight; on the active frame over the players who played snaps, what the card can know from the roster).
            Everything after the volume is the live rule unchanged: rate shrunk toward the league and moved toward the
            defense, the round-15 median curve on the mean, the round-6 team reconciliation, the round-13 injury and
            snap factors on yards; receptions = volume x catch rate shrunk toward the league x MED_CATCH.
  scores.   mean absolute error per player-game (yards; catches), signed bias (line minus actual), the paired standard
            error of the difference from base, on 2019-22 and 2023-25 (2017-18 kept beside them as the fit window), and
            by tier of the base yards line (0-20, 20-40, 40-60, 60-80, 80+; receptions on the same rows, so a change that
            helps the average by hurting the stars is visible).
Decision rule, set before the run: a variant is adopted only if it beats base on both windows on the active frame and is
no worse than 0.05 yards (0.005 catches) on both windows on the touch frame.
Output reports/props_backtest17.csv (frame x stat x variant x window) and reports/props_backtest17_tiers.csv."""
import numpy as np, pandas as pd, pathlib
from nflmodel import props as PR
from nflmodel.features import OUT
src = pathlib.Path(__file__).with_name("props_by_season.py").read_text().split("by_season, by_pos, by_bucket = [], [], []")[0]
ns = {"__name__": "bys"}; exec(compile(src, "bys", "exec"), ns)
d, tv, T17, ALW, games, pred, feat = ns["d"], ns["tv"], ns["T17"], ns["ALW"], ns["games"], ns["pred"], ns["feat"]
prev_sums, fade_sums, lg_series = ns["prev_sums"], ns["fade_sums"], ns["lg_series"]
REP, SNAP, MIN_VOL = ns["_REP"], ns["_SNAP"], ns["MIN_VOL"]
WIN = {"2019-22": (2019, 2022), "2023-25": (2023, 2025)}; FIT = (2017, 2018); ALLW = {"2017-18": FIT, **WIN}
TIERS = [0, 20, 40, 60, 80, 10000]; BLENDS = (0.25, 0.5, 0.75); TOL = {"yards": 0.05, "catches": 0.005}
OUT_CSV, OUT_TIERS = "reports/props_backtest17.csv", "reports/props_backtest17_tiers.csv"
ACT = pd.read_parquet(OUT / "snap_exposure.parquet", columns=["player_id", "game_id", "season", "week", "team", "position", "off_pct"]).rename(columns={"player_id": "pid", "team": "posteam"})
ACT = ACT[(ACT.off_pct > 0) & (ACT.season >= 2016)].drop_duplicates(["pid", "game_id"])


def frame(kind, active):
    """The by-season frame's yards inputs, walk-forward, with (active=True) the zero-touch games of a projected player
    who played snaps. State columns (previous-window sums, the decayed usage) on a zero-touch game are those after his
    previous touch game, as the live rule would carry them; the active-games share has its own state on every row."""
    if kind == "rec":
        t = d[d.pass_play & d.receiver_player_id.notna()].rename(columns={"receiver_player_id": "pid"}); vcol = "tp"; ev = {"catch": "complete_pass"}; lgp = d[d.pass_play]
    else:
        t = d[d.play_type.eq("run") & d.rusher_player_id.notna()].rename(columns={"rusher_player_id": "pid"}); vcol = "tr"; ev = {}; lgp = t
    t = t.copy(); t["n"] = 1
    pg = t.groupby(["pid", "posteam", "season", "week", "game_id"]).agg(n=("n", "sum"), yds=("yards_gained", "sum"), **{k: (v, "sum") for k, v in ev.items()}).reset_index().merge(tv[["posteam", "season", "week", "game_id", vcol]].rename(columns={vcol: "team_n"}), on=["posteam", "season", "week", "game_id"], how="left")
    cols = ["n", "yds", "team_n"] + list(ev); zero = dict(n=0, yds=0.0, team_n=0.0, **{k: 0.0 for k in ev})
    last = pg.sort_values(["pid", "season", "week"]).groupby("pid").tail(1)[["pid", "posteam"]].assign(season=9999, week=0, game_id="dummy", **zero)   # a sentinel after his last touch game: the state a later zero-touch game reads
    pgd = pd.concat([pg, last], ignore_index=True); sf, tf = PR.FADE.get(kind, (1.0, 1.0))
    R = prev_sums(pgd, ["pid"], cols); R[cols] = R[cols].fillna(0.0)
    R["last_sn"] = pgd.sort_values(["pid", "season", "week"]).reset_index(drop=True).groupby("pid").season.shift(1).values   # the season of his previous touch game
    R85 = fade_sums(pgd, ["pid"], ["n", "team_n"], PR.DECAY, sf, tf).rename(columns={"n": "n_85", "team_n": "team_n_85"})
    # the active-games share (round 14, props.receivers/rushers share_td): every game he was active for at a position whose snaps count, a game without a touch as 0 over the team's plays
    za = ACT[ACT.pid.isin(pg.pid.unique()) & ACT.position.isin(PR.SKILL[kind])].merge(pg[["pid", "game_id"]].assign(has=1), on=["pid", "game_id"], how="left")
    za = za[za.has.isna()][["pid", "posteam", "season", "week", "game_id"]].merge(tv[["posteam", "season", "week", "game_id", vcol]].rename(columns={vcol: "team_n"}), on=["posteam", "season", "week", "game_id"], how="inner")
    R85a = fade_sums(pd.concat([pg, za.assign(**{k: v for k, v in zero.items() if k != "team_n"}), last], ignore_index=True), ["pid"], ["n", "team_n"], PR.DECAY, sf, tf).rename(columns={"n": "n_85a", "team_n": "team_n_85a"})
    f = pg.rename(columns={"n": "act_n", "yds": "act_yds", **{k: f"act_{k}" for k in ev}})[["pid", "posteam", "season", "week", "game_id", "act_n", "act_yds"] + [f"act_{k}" for k in ev]].assign(touch=1)
    zero_act = dict(act_n=0, act_yds=0.0, **{f"act_{k}": 0.0 for k in ev})
    if active:
        f = pd.concat([f, za[["pid", "posteam", "season", "week", "game_id"]].assign(**zero_act, touch=0)], ignore_index=True)
    f = pd.concat([f, last[["pid", "posteam", "season", "week", "game_id"]].assign(**zero_act, touch=1)], ignore_index=True)
    f = f.merge(R[["pid", "game_id", "games_prev", "last_sn"] + cols], on=["pid", "game_id"], how="left").merge(R85[["pid", "game_id", "n_85", "team_n_85"]], on=["pid", "game_id"], how="left").merge(R85a[["pid", "game_id", "n_85a", "team_n_85a"]], on=["pid", "game_id"], how="left").sort_values(["pid", "season", "week"])
    state = ["games_prev", "last_sn", "n_85", "team_n_85"] + cols; f[state] = f.groupby("pid")[state].bfill(); f = f[f.season < 9999].copy()
    dg = t.groupby(["defteam", "season", "week", "game_id"]).agg(d_n=("n", "sum"), d_yds=("yards_gained", "sum")).reset_index(); D = prev_sums(dg, ["defteam"], ["d_n", "d_yds"])
    f = f.merge(games, on="game_id").merge(d[["game_id", "posteam", "defteam"]].drop_duplicates(), on=["game_id", "posteam"]).merge(T17[["posteam", "game_id", vcol, "games_prev"]].rename(columns={vcol: "tv", "games_prev": "tgames"}), on=["posteam", "game_id"]).merge(D[["defteam", "game_id", "d_n", "d_yds"]], on=["defteam", "game_id"]).merge(ALW[["defteam", "game_id", "a_tdb", "agames"]], on=["defteam", "game_id"])
    f = f.merge(feat.rename(columns={"team": "posteam"})[["game_id", "posteam", "wind"]], on=["game_id", "posteam"], how="left"); f["wind"] = f.wind.fillna(0.0)
    f = f[(f.n >= MIN_VOL) & (f.games_prev >= 3) & (f.tgames >= 3) & (f.agames >= 3) & (f.season >= 2017)].copy()
    f = f[(f.touch == 1) | (f.last_sn >= f.season - 1)]   # a zero-touch game counts only while the live rule would carry him (a touch last season or this)
    f["me"] = pd.Series(np.where(f.posteam == f.home_team, f.spread_line, -f.spread_line), index=f.index).astype(float).fillna(0.0); f["tc"] = (f.total_line - PR.GS_TOTAL).fillna(0.0); b = PR.GS[kind]
    f["tplays"] = f.tv / f.tgames + b[0] + b[1] * f.me + b[2] * f.tc
    f["share"] = (f.n_85 / f.team_n_85.replace(0, np.nan)).fillna(0.0); f["share_a"] = (f.n_85a / f.team_n_85a.replace(0, np.nan)).fillna(f.share)
    lg = lg_series(f, lgp, "yards_gained", float(lgp.yards_gained.mean())); K, W = PR.K[kind], PR.W[kind]
    f["d_rate"] = np.where(f.d_n >= 100, f.d_yds / f.d_n.replace(0, np.nan), np.nan)
    f["rate"] = (f.yds + K * lg) / (f.n + K) * np.where(f.d_rate.notna(), 1 + W * (f.d_rate / lg - 1), 1.0) * (1 + PR.WIND_C[kind] * np.maximum(f.wind - 10, 0))   # yards per touch: shrunk, moved toward the defense, the wind
    if "catch" in ev:
        lgc = lg_series(f, t, "complete_pass", float(t.complete_pass.mean())); f["catch_rate"] = (f.catch + PR.K_CATCH * lgc) / (f.n + PR.K_CATCH)
    f = f.merge(pred, on="game_id", how="left"); f["exp_pts"] = np.where(f.posteam == f.home_team, f.home_exp, f.away_exp)
    f = f.merge(REP, on=["pid", "season", "week"], how="left").merge(SNAP, on=["pid", "game_id"], how="left")
    grp = [PR.inj_group(a_, b_) for a_, b_ in zip(f.report_status, f.practice_status)]
    f["inj"] = np.array([PR.INJ_F[kind].get(g_, 1.0) for g_ in grp]); f["sr"] = np.array([PR.snap_ratio(a_, b_) for a_, b_ in zip(f.s3, f.s10)])
    return f.reset_index(drop=True)


class Lines:
    """One frame's rows with the live rule after the volume: mean -> median curve -> team reconciliation -> injury and
    snap factors (yards); volume x catch rate x MED_CATCH (receptions). A variant supplies the share."""

    def __init__(self, kind, f):
        self.kind, self.f = kind, f; self.codes = pd.factorize(f.game_id.astype(str) + "|" + f.posteam.astype(str))[0]; self.ngrp = self.codes.max() + 1
        fy = PR.TEAM_FIT[kind]["yds"]; self.exp_y = fy[0] + fy[1] * f.exp_pts.values.astype(float); self.ok = f.exp_pts.notna().values; self.wy = PR.RECON_W[kind]["yds"]
        self.r13 = f.inj.values * (1 + PR.SNAP_W[kind] * (f.sr.values - 1))

    def cap1(self, share):
        s = np.bincount(self.codes, weights=share, minlength=self.ngrp)[self.codes]
        return np.where(s > 1, share / s, share)

    def yards(self, share):
        mean = share * self.f.tplays.values * self.f.rate.values; line = PR.med_factor(self.kind, mean) * mean
        s = np.bincount(self.codes, weights=line, minlength=self.ngrp)[self.codes]
        with np.errstate(divide="ignore", invalid="ignore"):
            scale = np.clip(self.exp_y / np.where(s == 0, np.nan, s), 0.5, 2.0)
        return np.where(self.ok & ~np.isnan(scale), line * (1 + self.wy * (scale - 1)), line) * self.r13

    def catches(self, share):
        return PR.MED_CATCH * share * self.f.tplays.values * self.f.catch_rate.values


def main():
    rows, tiers = [], []
    def score(fr, stat, variant, f, line, act, base, tier, note=""):
        for w, (a, b) in ALLW.items():
            m = f.season.between(a, b).values; e = line[m] - act[m]; dd = np.abs(e) - np.abs(base[m] - act[m])
            rows.append({"frame": fr, "stat": stat, "variant": variant, "window": w, "n": int(m.sum()), "mae": round(float(np.abs(e).mean()), 4), "bias": round(float(e.mean()), 3), "se_vs_base": round(float(dd.std(ddof=1) / np.sqrt(len(dd))), 4) if len(dd) > 1 else 0.0,
                         "mean_line": round(float(line[m].mean()), 3), "mean_actual": round(float(act[m].mean()), 3), "note": note})
            for i in range(len(TIERS) - 1):
                mt = m & (tier == i); ee = line[mt] - act[mt]
                if mt.sum(): tiers.append({"frame": fr, "stat": stat, "variant": variant, "window": w, "tier": f"{TIERS[i]}-{TIERS[i + 1]}" if i < len(TIERS) - 2 else f"{TIERS[i]}+", "n": int(mt.sum()), "mean_line": round(float(line[mt].mean()), 2), "mean_actual": round(float(act[mt].mean()), 2), "bias": round(float(ee.mean()), 3), "mae": round(float(np.abs(ee).mean()), 3)})
        dp = 4 if stat.endswith("catches") else 3
        print(f"{fr:6s} {stat:11s} {variant:14s} " + "  ".join(f"{r['window']} {r['mae']:.{dp}f} ({r['bias']:+.2f})" for r in rows[-3:]) + (f"   [{note}]" if note else ""), flush=True)
    for kind in ("rec", "rush"):
        for active in (False, True):
            fr = "active" if active else "touch"; f = frame(kind, active); L = Lines(kind, f)
            print(fr, kind, "rows", len(f), "zero-touch", int((f.touch == 0).sum()), f"mean share {f.share.mean():.3f} -> active {f.share_a.mean():.3f}", flush=True)
            shares = {"base": f.share.values, "share_a": f.share_a.values, **{f"blend_{w}": (1 - w) * f.share.values + w * f.share_a.values for w in BLENDS}, "share_a_cap1": L.cap1(f.share_a.values)}
            base_y = L.yards(shares["base"]); tier = np.digitize(base_y, TIERS[1:-1])
            stats = [("yards", L.yards, f.act_yds.values)] + ([("catches", L.catches, f.act_catch.values)] if kind == "rec" else [])
            for name, fn, act in stats:
                base = fn(shares["base"])
                for v, sh in shares.items():
                    note = "the adopted rule" if v == "base" else ("cap over the frame's players: " + ("who touched (hindsight)" if fr == "touch" else "who played snaps") if v == "share_a_cap1" else "")
                    score(fr, f"{kind}_{name}", v, f, fn(sh), act, base, tier, note)
    o = pd.DataFrame(rows); o.to_csv(OUT_CSV, index=False); pd.DataFrame(tiers).to_csv(OUT_TIERS, index=False)
    # the decision, as set before the run: better than base on both windows on the active frame, within the tolerance on the touch frame
    print("\nmean absolute error by variant (rows) and frame x window (columns); 2017-18 is the fit window, the blend weight is chosen there on the active frame")
    for stat, g in o.groupby("stat", sort=False):
        p = g.pivot_table(index="variant", columns=["frame", "window"], values="mae", sort=False)[[("touch", "2017-18"), ("touch", "2019-22"), ("touch", "2023-25"), ("active", "2017-18"), ("active", "2019-22"), ("active", "2023-25")]]
        print(f"\n{stat}\n" + p.round(4 if stat.endswith("catches") else 3).to_string())
        get = lambda v, fr, w: float(g[(g.variant == v) & (g.frame == fr) & (g.window == w)].mae.iloc[0])
        wbest = min(BLENDS, key=lambda w: get(f"blend_{w}", "active", "2017-18")); tol = TOL[stat.split("_")[1]]
        for v in ("share_a", f"blend_{wbest}", "share_a_cap1"):
            act_ok = all(get(v, "active", w) < get("base", "active", w) for w in WIN); touch_ok = all(get(v, "touch", w) <= get("base", "touch", w) + tol for w in WIN)
            print(f"  {v:14s}: active {'better' if act_ok else 'not better'} on both windows, touch {'within' if touch_ok else 'outside'} {tol} on both -> {'ADOPT' if act_ok and touch_ok else 'not adopted'}" + (f"  (blend weight chosen on 2017-18 active: {wbest})" if v.startswith("blend") else ""))
    print("DONE")


if __name__ == "__main__":
    main()
