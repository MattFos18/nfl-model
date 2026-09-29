"""Game-script variants and absorption when a starter is out (29 Sep 2026): one study, two parts, on the live
player-prop rule (nflmodel/props.py), walk-forward, as-of only, no market input anywhere (the game script reads the
game model's expected points from pred_v3: margin = own expected points minus the opponent's, total = their sum; the
closing spread and total are never read).

  frame.   props_by_season.build's inputs on the round-17 frames: touch (every player-game with a touch of the kind,
           the frame the rule's constants were chosen on and reports/props_by_season.csv grades) and active (plus every
           game a projected receiver or rusher played offensive snaps in without a touch, actual 0: the population the
           card projects). Passing has the touch frame only (a passer-game with 10+ dropbacks). Built once per kind and
           cached (PROPS_GS_CACHE, default the session scratchpad's props_gs/).
  part 1.  the VOLUME's game script (the team's pass plays, runs, dropbacks in the game, then the player's share of
           them). Every line fitted on 2016-18 team-games by least squares, the target being the team's plays of the
           kind in the game beyond its live base (its last-17 average, blended PACE toward the opponent's allowed):
             base      the live line (props.GS on the model's margin and total);
             refit     the same line refitted on today's frame (are the constants stale?);
             winprob   intercept + b1 x (p - 0.5) + b2 x (total - GS_TOTAL), p = Phi(margin / 13) the win chance;
             quad      the margin line plus margin^2 and margin x total terms;
             pace_w    the base blended w = 0.25 / 0.5 toward the opponent's allowed plays per game, the live line on
                       top (props.PACE is 0 for receiving and rushing, 0.25 for passing, so pace_0.25 = base there).
  part 2.  absorption when a teammate with a large share is absent, a different form from round ten (which handed the
           whole absent share pro rata and lost): only a teammate whose decayed share as of the game is >= 0.15
           (receivers) / 0.25 (rushers), seen in one of the team's last three games and absent from this one (no snap
           in snap_exposure.parquet, hindsight), gives the others a FITTED fraction f of his share, split among them in
           proportion to their own shares: same-position teammates or all teammates, f by the absent player's position
           (WR, TE, RB; QB for rushing), fitted on the frame's fit window by least squares of the teammates' actual
           share beyond their projected share on the absent share. Tested at the fitted f and at half of it, with the
           hindsight absence (the ceiling) and with the absence the live rule could know before the game (the injury
           report's Out / Doubtful, data/raw/injuries, or a weekly roster status other than active, data/raw/rosters:
           reserve / IR, PUP, suspended, cut).
  scores.  mean absolute error per player-game of the volume (targets, carries, dropbacks) and of the yards line (the
           live rule after the volume: rate shrunk toward the league and moved toward the defense, the wind, the
           round-15 median curve, the round-6 team reconciliation, the round-13 injury and snap factors), signed bias,
           the paired standard error of the difference from base, on 2019-22 and 2023-25 (2017-18 beside them as the
           fit window), and by tier of the base yards line.
Adoption rule, set before the run: on the touch frame a variant is adopted only if it lowers yards MAE on both windows
and does not raise volume MAE on either; the active frame is a check beside it (a variant that passes on the touch
frame but raises yards MAE on the active frame on either window is flagged, not adopted).
Output reports/props_gs_absorb.csv (part x frame x stat x variant x window x tier) and reports/props_gs_absorb.md."""
import numpy as np, pandas as pd, pathlib, time, os, sys
from scipy.stats import norm
from nflmodel import props as PR
from nflmodel.features import OUT, RAW
CACHE = pathlib.Path(os.environ.get("PROPS_GS_CACHE", "/tmp/claude-0/-home-user/c1e0d18e-681a-50ba-b0bb-6c809c2e3dee/scratchpad/props_gs")); CACHE.mkdir(parents=True, exist_ok=True)
WIN = {"2019-22": (2019, 2022), "2023-25": (2023, 2025)}; FIT = (2017, 2018); ALLW = {"2017-18": FIT, **WIN}; GS_FIT = (2016, 2018)
TIERS = {"rec": [0, 20, 40, 60, 80, 10000], "rush": [0, 20, 40, 60, 80, 10000], "pass": [0, 150, 200, 250, 300, 10000]}
VCOL = {"rec": "tp", "rush": "tr", "pass": "tdb"}; SIGMA = 13.0; PACE_W = (0.25, 0.5)
THR = {"rec": 0.15, "rush": 0.25}; LOOKBACK = 3; POSG = {"WR": "WR", "TE": "TE", "RB": "RB", "FB": "RB", "HB": "RB", "QB": "QB"}
ABS_POS = {"rec": ["WR", "TE", "RB"], "rush": ["RB", "QB", "WR", "TE"]}; MIN_ABS = 30   # a position's f is fitted when at least MIN_ABS fit-window team-games carry an absence of it, else 0
OUT_CSV, OUT_MD = "reports/props_gs_absorb.csv", "reports/props_gs_absorb.md"
T0 = time.time(); TIMES = {}
def log(*a): print(f"[{time.time() - T0:7.1f}s]", *a, flush=True)


# ----------------------------------------------------------------------------------------------------------------- frames
def _header():
    """props_by_season's module-level state (the charted plays, the team volumes, the previous-window sums, the reports,
    the snap trends), executed once when a frame has to be built."""
    src = pathlib.Path(__file__).with_name("props_by_season.py").read_text().split("by_season, by_pos, by_bucket = [], [], []")[0]
    ns = {"__name__": "bys"}; exec(compile(src, "bys", "exec"), ns); return ns


def build_frames():
    ns = _header(); log("header loaded")
    d, tv, T17, games, pred, feat = ns["d"], ns["tv"], ns["T17"], ns["games"], ns["pred"], ns["feat"]
    prev_sums, fade_sums, lg_series, REP, SNAP, MIN_VOL, pos_of = ns["prev_sums"], ns["fade_sums"], ns["lg_series"], ns["_REP"], ns["_SNAP"], ns["MIN_VOL"], ns["pos_of"]
    ALW3 = prev_sums(tv.rename(columns={"tp": "a_tp", "tr": "a_tr", "tdb": "a_tdb"}), ["defteam"], ["a_tp", "a_tr", "a_tdb"]).rename(columns={"games_prev": "agames"})
    ACT = pd.read_parquet(OUT / "snap_exposure.parquet", columns=["player_id", "game_id", "season", "week", "team", "position", "off_pct"]).rename(columns={"player_id": "pid", "team": "posteam"})
    ACT = ACT[(ACT.off_pct > 0) & (ACT.season >= 2016)].drop_duplicates(["pid", "game_id"])
    # the team-game table for part 1's fits: the team's plays of each kind in the game, its last-17 average, the opponent's allowed, the model's margin and total
    tg = tv.merge(T17.rename(columns={"tp": "p_tp", "tr": "p_tr", "tdb": "p_tdb", "games_prev": "tgames"})[["posteam", "game_id", "p_tp", "p_tr", "p_tdb", "tgames"]], on=["posteam", "game_id"]).merge(ALW3[["defteam", "game_id", "a_tp", "a_tr", "a_tdb", "agames"]], on=["defteam", "game_id"])
    tg = tg.merge(games[["game_id", "home_team", "away_team"]], on="game_id").merge(pred, on="game_id", how="left")
    tg["exp_pts"] = np.where(tg.posteam == tg.home_team, tg.home_exp, tg.away_exp); tg["exp_opp"] = np.where(tg.posteam == tg.home_team, tg.away_exp, tg.home_exp)
    tg["me"] = (tg.exp_pts - tg.exp_opp).fillna(0.0); tg["tc"] = (tg.home_exp + tg.away_exp - PR.GS_TOTAL).fillna(0.0)
    tg.to_parquet(CACHE / "teams.parquet"); log("team table", len(tg))
    ACT.to_parquet(CACHE / "act.parquet")
    for kind in ("rec", "rush", "pass"):
        t1 = time.time(); vcol = VCOL[kind]; active = kind != "pass"
        if kind == "rec":
            t = d[d.pass_play & d.receiver_player_id.notna()].rename(columns={"receiver_player_id": "pid"}); ev = {"catch": "complete_pass"}; lgp = d[d.pass_play]
        elif kind == "rush":
            t = d[d.play_type.eq("run") & d.rusher_player_id.notna()].rename(columns={"rusher_player_id": "pid"}); ev = {}; lgp = t
        else:
            pdb = d[d.dropback & d.passer_player_id.notna()].assign(yards_gained=lambda x: x.pass_yds); t = pdb.rename(columns={"passer_player_id": "pid"}); ev = {}; lgp = pdb   # passing yards gross, as the books settle them
        t = t.copy(); t["n"] = 1
        pg = t.groupby(["pid", "posteam", "season", "week", "game_id"]).agg(n=("n", "sum"), yds=("yards_gained", "sum"), **{k: (v, "sum") for k, v in ev.items()}).reset_index().merge(tv[["posteam", "season", "week", "game_id", vcol]].rename(columns={vcol: "team_n"}), on=["posteam", "season", "week", "game_id"], how="left")
        cols = ["n", "yds", "team_n"] + list(ev); zero = dict(n=0, yds=0.0, team_n=0.0, **{k: 0.0 for k in ev})
        last = pg.sort_values(["pid", "season", "week"]).groupby("pid").tail(1)[["pid", "posteam"]].assign(season=9999, week=0, game_id="dummy", **zero)   # a sentinel after his last touch game: the state a later zero-touch game reads
        pgd = pd.concat([pg, last], ignore_index=True); sf, tf = PR.FADE.get(kind, (1.0, 1.0))
        R = prev_sums(pgd, ["pid"], cols); R[cols] = R[cols].fillna(0.0)
        R["last_sn"] = pgd.sort_values(["pid", "season", "week"]).reset_index(drop=True).groupby("pid").season.shift(1).values
        R85 = fade_sums(pgd, ["pid"], ["n", "team_n"], PR.DECAY, sf, tf).rename(columns={"n": "n_85", "team_n": "team_n_85"})
        if active:
            za = ACT[ACT.pid.isin(pg.pid.unique()) & ACT.position.isin(PR.SKILL[kind])].merge(pg[["pid", "game_id"]].assign(has=1), on=["pid", "game_id"], how="left")
            za = za[za.has.isna()][["pid", "posteam", "season", "week", "game_id"]].merge(tv[["posteam", "season", "week", "game_id", vcol]].rename(columns={vcol: "team_n"}), on=["posteam", "season", "week", "game_id"], how="inner")
            R85a = fade_sums(pd.concat([pg, za.assign(**{k: v for k, v in zero.items() if k != "team_n"}), last], ignore_index=True), ["pid"], ["n", "team_n"], PR.DECAY, sf, tf).rename(columns={"n": "n_85a", "team_n": "team_n_85a"})
            # part 2: every player's decayed share AFTER each of his games (the share a later game he misses reads), touch games and active games
            for R_, a, b, name in ((R85, "n_85", "team_n_85", "touch"), (R85a, "n_85a", "team_n_85a", "active")):
                s = R_.sort_values(["pid", "season", "week"]).reset_index(drop=True); s["pre"] = (s[a] / s[b].replace(0, np.nan)); s["post"] = s.groupby("pid").pre.shift(-1); s["n_post"] = s.groupby("pid")[a].shift(-1)
                s = s[s.season < 9999][["pid", "season", "week", "game_id", "post", "n_post"]].dropna(subset=["post"]); s.to_parquet(CACHE / f"share_{name}_{kind}.parquet")
        f = pg.rename(columns={"n": "act_n", "yds": "act_yds", **{k: f"act_{k}" for k in ev}})[["pid", "posteam", "season", "week", "game_id", "act_n", "act_yds"] + [f"act_{k}" for k in ev]].assign(touch=1)
        zero_act = dict(act_n=0, act_yds=0.0, **{f"act_{k}": 0.0 for k in ev})
        if active: f = pd.concat([f, za[["pid", "posteam", "season", "week", "game_id"]].assign(**zero_act, touch=0)], ignore_index=True)
        f = pd.concat([f, last[["pid", "posteam", "season", "week", "game_id"]].assign(**zero_act, touch=1)], ignore_index=True)
        f = f.merge(R[["pid", "game_id", "games_prev", "last_sn"] + cols], on=["pid", "game_id"], how="left").merge(R85[["pid", "game_id", "n_85", "team_n_85"]], on=["pid", "game_id"], how="left")
        if active: f = f.merge(R85a[["pid", "game_id", "n_85a", "team_n_85a"]], on=["pid", "game_id"], how="left")
        f = f.sort_values(["pid", "season", "week"]); state = ["games_prev", "last_sn", "n_85", "team_n_85"] + cols; f[state] = f.groupby("pid")[state].bfill(); f = f[f.season < 9999].copy()
        dg = t.groupby(["defteam", "season", "week", "game_id"]).agg(d_n=("n", "sum"), d_yds=("yards_gained", "sum")).reset_index(); D = prev_sums(dg, ["defteam"], ["d_n", "d_yds"])
        f = f.merge(games[["game_id", "home_team", "away_team"]], on="game_id").merge(d[["game_id", "posteam", "defteam"]].drop_duplicates(), on=["game_id", "posteam"]).merge(T17[["posteam", "game_id", vcol, "games_prev"]].rename(columns={vcol: "tv", "games_prev": "tgames"}), on=["posteam", "game_id"]).merge(D[["defteam", "game_id", "d_n", "d_yds"]], on=["defteam", "game_id"]).merge(ALW3[["defteam", "game_id", "a_tp", "a_tr", "a_tdb", "agames"]], on=["defteam", "game_id"])
        f = f.merge(tv[["posteam", "game_id", vcol]].rename(columns={vcol: "team_act"}), on=["posteam", "game_id"], how="left")   # the team's plays of the kind in the game (part 2's fit)
        f = f.merge(feat.rename(columns={"team": "posteam"})[["game_id", "posteam", "wind"]], on=["game_id", "posteam"], how="left"); f["wind"] = f.wind.fillna(0.0)
        minv = MIN_VOL * (3 if kind == "pass" else 1); f = f[(f.n >= minv) & (f.games_prev >= 3) & (f.tgames >= 3) & (f.agames >= 3) & (f.season >= 2017)].copy()
        f = f[(f.touch == 1) | (f.last_sn >= f.season - 1)]
        if kind == "pass": f = f[f.act_n >= 10]
        f = f.merge(pred, on="game_id", how="left"); f["exp_pts"] = np.where(f.posteam == f.home_team, f.home_exp, f.away_exp); f["exp_opp"] = np.where(f.posteam == f.home_team, f.away_exp, f.home_exp)
        f["me"] = (f.exp_pts - f.exp_opp).fillna(0.0); f["tc"] = (f.home_exp + f.away_exp - PR.GS_TOTAL).fillna(0.0)   # the model's margin from the team's side and its total; never a line
        f["team_pg"] = f.tv / f.tgames; f["opp_pg"] = f[f"a_{vcol}"] / f.agames
        f["share"] = 1.0 if kind == "pass" else (f.n_85 / f.team_n_85.replace(0, np.nan)).fillna(0.0)
        f["share_a"] = 1.0 if kind == "pass" else (f.n_85a / f.team_n_85a.replace(0, np.nan)).fillna(f.share)
        f["share_y"] = 1.0 if kind == "pass" else PR.share_blend(kind, f.share, f.share_a)   # the share behind the yards line (round 17)
        lgp = lgp.assign(yards_gained=lgp.yards_gained.fillna(0.0)); lg = lg_series(f, lgp, "yards_gained", float(lgp.yards_gained.mean())); K, W = PR.K[kind], PR.W[kind]
        f["d_rate"] = np.where(f.d_n >= 100, f.d_yds / f.d_n.replace(0, np.nan), np.nan)
        f["rate"] = (f.yds + K * lg) / (f.n + K) * np.where(f.d_rate.notna(), 1 + W * (f.d_rate / lg - 1), 1.0) * (1 + PR.WIND_C[kind] * np.maximum(f.wind - 10, 0))
        if active:
            f = f.merge(REP, on=["pid", "season", "week"], how="left").merge(SNAP, on=["pid", "game_id"], how="left")
            grp = [PR.inj_group(a_, b_) for a_, b_ in zip(f.report_status, f.practice_status)]
            f["inj"] = np.array([PR.INJ_F[kind].get(g_, 1.0) for g_ in grp]); f["sr"] = np.array([PR.snap_ratio(a_, b_) for a_, b_ in zip(f.s3, f.s10)])
            f = f.merge(ACT[["pid", "game_id", "position"]], on=["pid", "game_id"], how="left"); f["pos"] = f.position.fillna(f.pid.map(pos_of)).fillna("?").map(lambda p: POSG.get(p, p))
        else:
            f["inj"] = 1.0; f["sr"] = 1.0; f["pos"] = "QB"
        keep = ["pid", "posteam", "defteam", "season", "week", "game_id", "touch", "act_n", "act_yds", "n", "games_prev", "team_act", "tv", "tgames", "team_pg", "opp_pg", "me", "tc", "exp_pts", "share", "share_a", "share_y", "rate", "inj", "sr", "pos"]
        f = f[keep].reset_index(drop=True); f.to_parquet(CACHE / f"frame_{kind}.parquet")
        TIMES[f"frame_{kind}"] = time.time() - t1; log(kind, "frame rows", len(f), "zero-touch", int((f.touch == 0).sum()), f"{TIMES[f'frame_{kind}']:.0f}s")
    # part 2's as-of absence: the injury report's Out / Doubtful and a weekly roster status other than active
    rep = REP[REP.report_status.isin(["Out", "Doubtful"])][["season", "week", "pid"]].drop_duplicates().assign(rep_out=1)
    ro = []
    for s_ in range(2016, 2027):
        p_ = RAW / "rosters" / f"roster_weekly_{s_}.parquet"
        if p_.exists():
            x = pd.read_parquet(p_, columns=["season", "week", "gsis_id", "status", "game_type"]); ro.append(x[(x.game_type == "REG") & x.gsis_id.notna()][["season", "week", "gsis_id", "status"]])
    ro = pd.concat(ro).rename(columns={"gsis_id": "pid"}); ro["act"] = ro.status.eq("ACT").astype(int)
    ro = ro.groupby(["season", "week", "pid"]).act.max().reset_index(); ro = ro[ro.act == 0][["season", "week", "pid"]].assign(ros_out=1)   # no active listing that week (reserve / IR, PUP, suspended, cut, ...)
    rep.merge(ro, on=["season", "week", "pid"], how="outer").fillna(0).to_parquet(CACHE / "known_out.parquet"); log("known-out table", len(rep), "report", len(ro), "roster")


def load(kind):
    return pd.read_parquet(CACHE / f"frame_{kind}.parquet")


# ----------------------------------------------------------------------------------------------------------------- scoring
class Lines:
    """One frame's rows with the live rule after the volume: mean -> median curve -> team reconciliation -> injury and
    snap factors (yards). A variant supplies the share and the team's plays."""
    def __init__(self, kind, f):
        self.kind, self.f = kind, f; self.codes = pd.factorize(f.game_id.astype(str) + "|" + f.posteam.astype(str))[0]; self.ngrp = self.codes.max() + 1
        fy = PR.TEAM_FIT[kind]["yds"]; self.exp_y = fy[0] + fy[1] * f.exp_pts.values.astype(float); self.ok = f.exp_pts.notna().values; self.wy = PR.RECON_W[kind]["yds"]
        self.r13 = f.inj.values * (1 + PR.SNAP_W.get(kind, 0.0) * (f.sr.values - 1)); self.rate = f.rate.values
    def yards(self, share, tplays):
        mean = share * tplays * self.rate; line = PR.med_factor(self.kind, mean) * mean
        s = np.bincount(self.codes, weights=line, minlength=self.ngrp)[self.codes]
        with np.errstate(divide="ignore", invalid="ignore"):
            scale = np.clip(self.exp_y / np.where(s == 0, np.nan, s), 0.5, 2.0)
        return np.where(self.ok & ~np.isnan(scale), line * (1 + self.wy * (scale - 1)), line) * self.r13


ROWS = []
def score(part, fr, stat, variant, f, line, act, base, tier, kind, note=""):
    out = {}
    for w, (a, b) in ALLW.items():
        m = f.season.between(a, b).values; e = line[m] - act[m]; dd = np.abs(e) - np.abs(base[m] - act[m])
        r = {"part": part, "frame": fr, "stat": stat, "variant": variant, "window": w, "tier": "all", "n": int(m.sum()), "mae": round(float(np.abs(e).mean()), 4), "bias": round(float(e.mean()), 3), "se_vs_base": round(float(dd.std(ddof=1) / np.sqrt(len(dd))), 4) if len(dd) > 1 else 0.0, "mean_line": round(float(line[m].mean()), 3), "mean_actual": round(float(act[m].mean()), 3), "note": note}
        ROWS.append(r); out[w] = r; T = TIERS[kind]
        for i in range(len(T) - 1):
            mt = m & (tier == i); ee = line[mt] - act[mt]; dd2 = np.abs(ee) - np.abs(base[mt] - act[mt])
            if mt.sum(): ROWS.append({"part": part, "frame": fr, "stat": stat, "variant": variant, "window": w, "tier": f"{T[i]}-{T[i + 1]}" if i < len(T) - 2 else f"{T[i]}+", "n": int(mt.sum()), "mae": round(float(np.abs(ee).mean()), 4), "bias": round(float(ee.mean()), 3), "se_vs_base": round(float(dd2.std(ddof=1) / np.sqrt(len(dd2))), 4) if len(dd2) > 1 else 0.0, "mean_line": round(float(line[mt].mean()), 3), "mean_actual": round(float(act[mt].mean()), 3), "note": ""})
    dp = 3 if stat.endswith("yards") else 4
    print(f"  {fr:6s} {stat:12s} {variant:16s} " + "  ".join(f"{w} {out[w]['mae']:.{dp}f} ({out[w]['bias']:+.2f})" for w in ALLW) + (f"   [{note}]" if note else ""), flush=True)
    return out


def ols(X, y):
    return np.linalg.lstsq(np.column_stack(X), y, rcond=None)[0]


# ----------------------------------------------------------------------------------------------------------------- part 1
def part1():
    tg = pd.read_parquet(CACHE / "teams.parquet"); tg = tg[(tg.tgames >= 3) & (tg.agames >= 3)]; fit_rows = tg[tg.season.between(*GS_FIT)]; consts = {}
    log(f"part 1: {len(fit_rows)} team-games in the fit window {GS_FIT[0]}-{GS_FIT[1]}, mean model total {float(tg.tc.mean() + PR.GS_TOTAL):.2f} (GS_TOTAL {PR.GS_TOTAL})")
    for kind in ("rec", "rush", "pass"):
        vcol = VCOL[kind]; x = fit_rows; pace = PR.PACE[kind]
        base_pg = (1 - pace) * (x[f"p_{vcol}"] / x.tgames) + pace * (x[f"a_{vcol}"] / x.agames); y = (x[vcol] - base_pg).values; me, tc = x.me.values, x.tc.values
        p = norm.cdf(me / SIGMA) - 0.5
        consts[kind] = {"base": tuple(PR.GS[kind]), "refit": tuple(ols([np.ones(len(y)), me, tc], y)), "winprob": tuple(ols([np.ones(len(y)), p, tc], y)), "quad": tuple(ols([np.ones(len(y)), me, tc, me ** 2, me * tc], y)), "n_fit": int(len(y)), "sd_y": float(y.std())}
        for name, fn in (("base", lambda b: b[0] + b[1] * me + b[2] * tc), ("refit", lambda b: b[0] + b[1] * me + b[2] * tc), ("winprob", lambda b: b[0] + b[1] * p + b[2] * tc), ("quad", lambda b: b[0] + b[1] * me + b[2] * tc + b[3] * me ** 2 + b[4] * me * tc)):
            consts[kind][f"fit_mae_{name}"] = float(np.abs(y - fn(consts[kind][name])).mean())
        log(kind, {k: (np.round(v, 4).tolist() if isinstance(v, tuple) else round(v, 4)) for k, v in consts[kind].items()})
    def tplays(kind, f, variant):
        c = consts[kind]; pace = PR.PACE[kind]; me, tc = f.me.values, f.tc.values; base_pg = (1 - pace) * f.team_pg.values + pace * f.opp_pg.values
        if variant.startswith("pace_"):
            w = float(variant.split("_")[1]); b = c["base"]; return np.maximum((1 - w) * f.team_pg.values + w * f.opp_pg.values + b[0] + b[1] * me + b[2] * tc, 0.0)
        b = c[variant]
        if variant == "winprob": return np.maximum(base_pg + b[0] + b[1] * (norm.cdf(me / SIGMA) - 0.5) + b[2] * tc, 0.0)
        if variant == "quad": return np.maximum(base_pg + b[0] + b[1] * me + b[2] * tc + b[3] * me ** 2 + b[4] * me * tc, 0.0)
        return np.maximum(base_pg + b[0] + b[1] * me + b[2] * tc, 0.0)
    variants = ["base", "refit", "winprob", "quad"] + [f"pace_{w}" for w in PACE_W]
    for kind in ("rec", "rush", "pass"):
        fa = load(kind); vol_name = {"rec": "targets", "rush": "carries", "pass": "dropbacks"}[kind]
        for fr in (("touch", "active") if kind != "pass" else ("touch",)):
            f = fa[fa.touch == 1].reset_index(drop=True) if fr == "touch" else fa; L = Lines(kind, f); share = f.share_y.values
            base_t = tplays(kind, f, "base"); base_v = share * base_t; base_y = L.yards(share, base_t); tier = np.digitize(base_y, TIERS[kind][1:-1])
            print(f"part 1 {kind} {fr}: {len(f)} rows", flush=True)
            for v in variants:
                t = tplays(kind, f, v); note = "the live line" if v == "base" else ("= base (props.PACE is 0.25 for passing)" if v == "pace_0.25" and kind == "pass" else "")
                score(1, fr, f"{kind}_{vol_name}", v, f, share * t, f.act_n.values.astype(float), base_v, tier, kind, note)
                score(1, fr, f"{kind}_yards", v, f, L.yards(share, t), f.act_yds.values.astype(float), base_y, tier, kind, note)
    return consts


# ----------------------------------------------------------------------------------------------------------------- part 2
def absences(kind):
    """Every (team-game, absent player) for the kind: a player with a snap at a skill position in one of the team's last
    LOOKBACK games, his decayed share as of the game (the blend props.share_blend of his touch-games and active-games
    shares after his last game) >= THR, with hind = 1 when he had no snap that week (hindsight) and asof = 1 when the
    injury report or the weekly roster said before the game he would not play."""
    ACT = pd.read_parquet(CACHE / "act.parquet"); tg = pd.read_parquet(CACHE / "teams.parquet")[["posteam", "season", "week", "game_id"]].sort_values(["posteam", "season", "week"]).reset_index(drop=True)
    tg["k"] = tg.groupby("posteam").cumcount()
    A = ACT[ACT.position.isin(PR.SKILL[kind])][["pid", "posteam", "game_id", "position"]].merge(tg[["posteam", "game_id", "k"]], on=["posteam", "game_id"])
    C = pd.concat([A.assign(k=A.k + off, off=off) for off in range(1, LOOKBACK + 1)]).sort_values("off").drop_duplicates(["pid", "posteam", "k"])
    C = C.drop(columns=["game_id"]).merge(tg, on=["posteam", "k"])   # the team's later game this player is a candidate absentee for
    played = ACT[["pid", "season", "week"]].drop_duplicates().assign(played=1)
    C = C.merge(played, on=["pid", "season", "week"], how="left"); C["hind"] = C.played.isna().astype(int)
    ko = pd.read_parquet(CACHE / "known_out.parquet"); C = C.merge(ko, on=["pid", "season", "week"], how="left").fillna({"rep_out": 0, "ros_out": 0}); C["asof"] = ((C.rep_out > 0) | (C.ros_out > 0)).astype(int)
    C = C[(C.hind == 1) | (C["asof"] == 1)].copy(); C["key"] = (C.season.astype("int64") * 100 + C.week.astype("int64"))
    for name in ("touch", "active"):
        s = pd.read_parquet(CACHE / f"share_{name}_{kind}.parquet"); s["key"] = (s.season.astype("int64") * 100 + s.week.astype("int64"))
        C = pd.merge_asof(C.sort_values("key"), s[["pid", "key", "post", "n_post"]].rename(columns={"post": f"s_{name}", "n_post": f"n_{name}"}).sort_values("key"), on="key", by="pid", direction="backward", allow_exact_matches=False)
    C = C.dropna(subset=["s_touch"]); C["s_active"] = C.s_active.fillna(C.s_touch); C["share_abs"] = PR.share_blend(kind, C.s_touch, C.s_active)
    C = C[C.share_abs >= THR[kind]].copy(); C["pos"] = C.position.map(lambda p: POSG.get(p, p)); C = C[C.pos.isin(ABS_POS[kind])]
    return C[["pid", "posteam", "season", "week", "game_id", "pos", "off", "share_abs", "hind", "asof", "rep_out", "ros_out", "played"]].reset_index(drop=True)


def fit_f(kind, f, C, positions):
    """Least squares on the fit window's team-games of the active frame: for each recipient position group (and all
    together), the frame's players' actual share of the team's plays beyond their projected share, on an intercept and
    the absent share by the absent player's position (hindsight absences). Returns the matrix recipient x absent."""
    x = f[f.season.between(*FIT)].copy(); x["excess"] = x.act_n / x.team_act.replace(0, np.nan) - x.share_y; x = x.dropna(subset=["excess"])
    S = C[(C.hind == 1) & C.season.between(*FIT)].groupby(["game_id", "posteam", "pos"]).share_abs.sum().unstack(fill_value=0.0).reindex(columns=positions, fill_value=0.0).reset_index()
    per = x.groupby(["game_id", "posteam", "pos"]).excess.sum().unstack(fill_value=0.0).reset_index(); tot = x.groupby(["game_id", "posteam"]).excess.sum().rename("all").reset_index()
    g = per.merge(tot, on=["game_id", "posteam"]).merge(S, on=["game_id", "posteam"], how="left", suffixes=("", "_abs")).fillna(0.0)
    cols = [p for p in positions if (S[p] > 0).sum() >= MIN_ABS]; counts = {p: int((S[p] > 0).sum()) for p in positions}
    X = [np.ones(len(g))] + [g[f"{p}_abs"].values if f"{p}_abs" in g else g[p].values for p in cols]
    out = {}
    for rec in [p for p in positions if p in per.columns] + ["all"]:
        b = ols(X, g[rec].values); out[rec] = {"intercept": float(b[0]), **{p: float(b[i + 1]) for i, p in enumerate(cols)}}
    return out, cols, counts, int(len(g))


def part2():
    for kind in ("rec", "rush"):
        t1 = time.time(); fa = load(kind); C = absences(kind); positions = ABS_POS[kind]
        C.to_parquet(CACHE / f"absences_{kind}.parquet")
        nteam = fa.drop_duplicates(["game_id", "posteam"]).shape[0]
        info = {"rows": int(len(C)), "hind": int(C.hind.sum()), "asof": int(C["asof"].sum()), "both": int(((C.hind == 1) & (C["asof"] == 1)).sum()), "asof_played": int(((C["asof"] == 1) & (C.hind == 0)).sum()), "team_games_frame": nteam,
                "team_games_with_hind": int(C[C.hind == 1].drop_duplicates(["game_id", "posteam"]).shape[0]), "by_pos_hind": C[C.hind == 1].pos.value_counts().to_dict(), "mean_share_hind": round(float(C[C.hind == 1].share_abs.mean()), 3)}
        F, cols, counts, ng = fit_f(kind, fa, C, positions); info.update({"fit_team_games": ng, "fit_absences_by_pos": counts, "fitted_positions": cols})
        log(f"part 2 {kind}: absences {info}"); print(pd.DataFrame(F).T.round(3).to_string(), flush=True)
        PART2_FIT[kind] = {"F": F, "cols": cols, "info": info}
        f_same = {p: F[p][p] for p in cols if p in F}; f_all = {p: F["all"][p] for p in cols}
        vol_name = {"rec": "targets", "rush": "carries"}[kind]; b = PR.GS[kind]
        for fr in ("touch", "active"):
            f = fa[fa.touch == 1].reset_index(drop=True) if fr == "touch" else fa; L = Lines(kind, f); share = f.share_y.values
            tpl = np.maximum(f.team_pg.values + b[0] + b[1] * f.me.values + b[2] * f.tc.values, 0.0)
            base_v = share * tpl; base_y = L.yards(share, tpl); tier = np.digitize(base_y, TIERS[kind][1:-1])
            key = f.game_id.astype(str) + "|" + f.posteam.astype(str); codes, uniq = pd.factorize(key); ngrp = len(uniq)
            pcodes = pd.factorize(key + "|" + f.pos.astype(str))[0]; npg = pcodes.max() + 1
            sum_all = np.bincount(codes, weights=share, minlength=ngrp)[codes]; sum_pos = np.bincount(pcodes, weights=share, minlength=npg)[pcodes]
            print(f"part 2 {kind} {fr}: {len(f)} rows", flush=True)
            score(2, fr, f"{kind}_{vol_name}", "base", f, base_v, f.act_n.values.astype(float), base_v, tier, kind, "the live rule: an absent share is not projected")
            score(2, fr, f"{kind}_yards", "base", f, base_y, f.act_yds.values.astype(float), base_y, tier, kind, "the live rule: an absent share is not projected")
            for mode in ("hind", "asof"):
                Cm = C[C[mode] == 1]; S = Cm.groupby(["game_id", "posteam", "pos"]).share_abs.sum().unstack(fill_value=0.0).reindex(columns=positions, fill_value=0.0)
                S = S.reindex(pd.MultiIndex.from_tuples([tuple(u.split("|")) for u in uniq], names=["game_id", "posteam"]), fill_value=0.0)   # absent share by position, per frame team-game
                Sg = S.values[codes]   # rows x positions
                pos_idx = np.array([positions.index(p) if p in positions else -1 for p in f.pos])
                for group in ("same", "all"):
                    for half in (1.0, 0.5):
                        if group == "same":
                            fvec = np.array([f_same.get(p, 0.0) for p in positions]); own = np.where(pos_idx >= 0, Sg[np.arange(len(f)), np.clip(pos_idx, 0, None)] * fvec[np.clip(pos_idx, 0, None)], 0.0)
                            with np.errstate(divide="ignore", invalid="ignore"): add = np.where(sum_pos > 0, share / sum_pos * own * half, 0.0)
                        else:
                            fvec = np.array([f_all.get(p, 0.0) for p in positions]); tot = Sg @ fvec
                            with np.errstate(divide="ignore", invalid="ignore"): add = np.where(sum_all > 0, share / sum_all * tot * half, 0.0)
                        sh = share + add; v = f"{mode}_{group}" + ("" if half == 1.0 else "_half")
                        note = ("hindsight absence (ceiling)" if mode == "hind" else "absence the rule could know (report Out/Doubtful, roster not active)") + f"; rows touched {int((add > 0).sum())}"
                        score(2, fr, f"{kind}_{vol_name}", v, f, sh * tpl, f.act_n.values.astype(float), base_v, tier, kind, note)
                        score(2, fr, f"{kind}_yards", v, f, L.yards(sh, tpl), f.act_yds.values.astype(float), base_y, tier, kind, note)
        TIMES[f"part2_{kind}"] = time.time() - t1


PART2_FIT = {}


# ----------------------------------------------------------------------------------------------------------------- report
def verdicts(o):
    """Per part and stat kind: the adoption rule on the touch frame, the active frame as a check."""
    out = []
    for part in (1, 2):
        g = o[(o.part == part) & (o.tier == "all")]
        for kind in ("rec", "rush", "pass"):
            ys = f"{kind}_yards"; vs = [s for s in g.stat.unique() if s.startswith(kind) and not s.endswith("yards")]
            if not vs: continue
            vs = vs[0]; get = lambda st, v, fr, w: float(g[(g.stat == st) & (g.variant == v) & (g.frame == fr) & (g.window == w)].mae.iloc[0]) if len(g[(g.stat == st) & (g.variant == v) & (g.frame == fr) & (g.window == w)]) else np.nan
            for v in [v for v in g[g.stat == ys].variant.unique() if v != "base"]:
                y_ok = all(get(ys, v, "touch", w) < get(ys, "base", "touch", w) for w in WIN); v_ok = all(get(vs, v, "touch", w) <= get(vs, "base", "touch", w) for w in WIN)
                has_act = len(g[(g.stat == ys) & (g.variant == v) & (g.frame == "active")]) > 0
                a_ok = all(get(ys, v, "active", w) <= get(ys, "base", "active", w) for w in WIN) if has_act else True
                out.append({"part": part, "kind": kind, "variant": v, "yards_better_both": y_ok, "volume_not_worse_both": v_ok, "active_check": ("n/a" if not has_act else ("passes" if a_ok else "fails")), "verdict": "ADOPT" if (y_ok and v_ok and a_ok) else "not adopted"})
    return pd.DataFrame(out)


def table(o, part, stat, fr):
    g = o[(o.part == part) & (o.stat == stat) & (o.frame == fr) & (o.tier == "all")]
    if not len(g): return ""
    p = g.pivot_table(index="variant", columns="window", values=["mae", "bias", "se_vs_base"], sort=False)
    dp = 3 if stat.endswith("yards") else 4; lines = ["| variant | " + " | ".join(f"{w} MAE | bias | SE vs base" for w in ALLW) + " |", "|:--|" + "--:|" * (3 * len(ALLW))]
    for v in g.variant.unique():
        lines.append(f"| {v} | " + " | ".join(f"{p.loc[v, ('mae', w)]:.{dp}f} | {p.loc[v, ('bias', w)]:+.2f} | {p.loc[v, ('se_vs_base', w)]:.{dp}f}" for w in ALLW) + " |")
    return "\n".join(lines)


def tier_table(o, part, stat, fr, variants):
    g = o[(o.part == part) & (o.stat == stat) & (o.frame == fr) & (o.tier != "all") & o.variant.isin(variants)]
    if not len(g): return ""
    tiers = list(dict.fromkeys(g.tier)); lines = ["| variant | window | " + " | ".join(f"{t} (n)" for t in tiers) + " |", "|:--|:--|" + "--:|" * len(tiers)]
    for v in variants:
        for w in WIN:
            gg = g[(g.variant == v) & (g.window == w)].set_index("tier")
            lines.append(f"| {v} | {w} | " + " | ".join((f"{gg.loc[t, 'mae']:.3f} ({int(gg.loc[t, 'n'])})" if t in gg.index else "") for t in tiers) + " |")
    return "\n".join(lines)

DECISION = [
    "**Part 1.** The live line is not stale: refit on 2016-18 with today's frame (the model's margin and total) the constants move a little (the passing margin slope halves, -0.046 to -0.023) and the in-sample fit improves by hundredths of a play, but on the held-out windows the refit, the win-probability form and the quadratic form are each within one paired standard error of base on yards for every kind, and none lowers yards MAE on both windows for receiving or passing. Rushing: quad lowers yards on both windows (17.7805 / 17.0413 -> 17.7804 / 17.0337) but raises carries on both, so it fails the rule. Opponent pace at a quarter (pace_0.25) is the one game-script change that passes: rushing carries 2.9828 / 2.8765 -> 2.9677 / 2.8657 (4 and 3 paired standard errors) and rushing yards 17.7805 / 17.0413 -> 17.7669 / 17.0356 (1.3 and 0.5 standard errors), the active frame agreeing (carries 2.3925 / 2.1748 -> 2.3822 / 2.1668, yards 13.5611 / 12.3205 -> 13.5507 / 12.3160). Adopted by the rule as set; the yards gain is inside the noise, the carries gain is not. For receiving pace_0.25 lowers targets on both windows by 4 standard errors (1.8302 / 1.7186 -> 1.8264 / 1.7142) and yards on both (19.1565 / 18.1573 -> 19.1543 / 18.1419), but the active-frame check is a tie on 2019-22 (16.8346 -> 16.8349, +0.0003 yards, 0.07 standard errors), which the rule as written counts as a fail: flagged, not adopted by the letter of the rule; Matt's call whether a tie at the fourth decimal should block it (round 4 had found nothing for receiving pace on its frame). pace_0.5 loses to pace_0.25 everywhere. Passing keeps its 0.25 (pace_0.5 raises dropbacks and yards on 2019-22).",
    "",
    "**Part 2.** Absorption at a fitted fraction works where round ten's pro rata did not, and only to the same position: the fitted fractions say an absent wideout's share goes 0.42 to the other wideouts and 0.03 to the tight ends, an absent tight end's 0.25 to the tight ends and 0.29 to the wideouts, an absent back's 0.35 to the other backs, with negative intercepts (the frame's players' projected shares already add to more than what happens); handing the fraction to all teammates (hind_all, asof_all) raises volume MAE and fails on both kinds. The as-of absence (the injury report's Out / Doubtful or a roster status other than active, what the live rule can know) is as good as or better than the hindsight ceiling: the absences the report does not flag (a healthy scratch, a demoted player) are not worth absorbing. Rushing: asof_same (f = 0.348) lowers carries 2.9828 / 2.8765 -> 2.9411 / 2.8415 (4 standard errors each) and yards 17.7805 / 17.0413 -> 17.6997 / 16.9723 (2.3 and 2.1), the active frame 13.5611 / 12.3205 -> 13.5282 / 12.2792; asof_same_half (f = 0.174) the same yards at half the standard error (17.7020 / 16.9729, 4.2 and 3.9 standard errors; active 13.5232 / 12.2794) and carries 2.9484 / 2.8494. Receiving: asof_same at the fitted f raises targets on 2019-22 and yards on the active frame and fails; asof_same_half (f = 0.211 WR, 0.125 TE) passes everything: targets 1.8302 / 1.7186 -> 1.8258 / 1.7128 (3.4 and 4 standard errors), yards 19.1565 / 18.1573 -> 19.1328 / 18.1454 (2.6 and 1.2), active 16.8346 / 15.6969 -> 16.8210 / 15.6936. Both multipliers pass for rushing; the multiplier is chosen on the fit window, as round 17 chose its blend weight: on 2017-18 the half is better on both kinds (rushing yards 18.053 against 18.067, carries 3.094 against 3.100; receiving 19.691 against 19.694, targets 1.875 against 1.878), so the half is adopted for both. By tier the gains sit in the 0-60 tiers; the 80+ tier of the base line is 0.1 to 0.2 yards worse on both kinds (its lines rise), a small cost inside a small tier. Receptions were not scored here; they follow the targets figure (round 17), which improved.",
    "",
    "**Adopted (rule as set):** part 1, PACE['rush'] 0 -> 0.25 (the live line on top, as passing already does); part 2, same-position absorption at half the fitted fraction for an absent teammate the injury report or roster says is out. Flagged for Matt: receiving pace_0.25 (a tie at the fourth decimal on the active check). Constants and the change to nflmodel/props.py:",
    "",
    "```python",
    "PACE = {\"rec\": 0.0, \"rush\": 0.25, \"pass\": 0.25}   # round 18: rushing a quarter toward the opponent's allowed runs per game (reports/props_gs_absorb.csv, part 1 pace_0.25)",
    "# round 18 (29 Sep 2026, reports/props_gs_absorb.csv, part 2): when a teammate the report or roster says is out (project_game's OUT_WORDS) was",
    "# active in one of the team's last ABSORB_LOOKBACK games and his share behind the yards line is >= ABSORB_THR, the players of his position",
    "# group who play get ABSORB[kind][group] x his share, split in proportion to their own shares (half the least-squares fraction absorbed by",
    "# the same position, fitted on 2017-18: WR 0.422, TE 0.249, RB 0.348; the half chosen on the fit window). Not to other positions, not",
    "# to the touchdown share (untested), never pro rata of the whole (round ten).",
    "ABSORB = {\"rec\": {\"WR\": 0.211, \"TE\": 0.125}, \"rush\": {\"RB\": 0.174}}",
    "ABSORB_THR = {\"rec\": 0.15, \"rush\": 0.25}; ABSORB_LOOKBACK = 3",
    "ABSORB_GROUP = {\"WR\": \"WR\", \"TE\": \"TE\", \"RB\": \"RB\", \"FB\": \"RB\", \"HB\": \"RB\"}",
    "",
    "",
    "def recent_players(active: pd.DataFrame | None, team: str, n: int = ABSORB_LOOKBACK) -> set:",
    "    \"\"\"The players with a snap in one of the team's last n games (snap counts as of the week; props.active_games).\"\"\"",
    "    if active is None or not len(active): return set()",
    "    a = active[active.posteam == team]; last = a.drop_duplicates(\"game_id\").sort_values([\"season\", \"week\"]).game_id.tail(n)",
    "    return set(a[a.game_id.isin(last)].player_id)",
    "",
    "",
    "def absorb(rows: list, kind: str, recent: set) -> None:",
    "    \"\"\"Round 18: part of an absent starter's share_yds to his same-position teammates who play, in proportion to their shares.\"\"\"",
    "    for a in [r for r in rows if r[\"out\"] and r[\"player_id\"] in recent and r[\"share_yds\"] >= ABSORB_THR[kind] and ABSORB_GROUP.get(r[\"pos\"], \"\") in ABSORB[kind]]:",
    "        grp = ABSORB_GROUP[a[\"pos\"]]; to = [r for r in rows if not r[\"out\"] and ABSORB_GROUP.get(r[\"pos\"], \"\") == grp]; tot = sum(r[\"share_yds\"] for r in to)",
    "        if tot <= 0: continue",
    "        for r in to: r[\"absorbed\"] = round(r.get(\"absorbed\", 0.0) + ABSORB[kind][grp] * a[\"share_yds\"] * r[\"share_yds\"] / tot, 4); r[\"share_yds\"] = round(r[\"share_yds\"] + ABSORB[kind][grp] * a[\"share_yds\"] * r[\"share_yds\"] / tot, 3)",
    "```",
    "",
    "In project_game (which needs the as-of snap counts: add a `recent: set | None = None` argument and pass `recent_players(AG, team)` from main, AG being the active_games frame main already loads for round 14), call `absorb(rec, \"rec\", recent or set())` just before the loop that sets proj_targets from share_yds, and `absorb(rus, \"rush\", recent or set())` before the loop that sets proj_carries. The touchdown share (share_td) is untouched. The backtest's absent player is one with no active listing or an Out / Doubtful report; the live rule sees the roster's Out, Doubtful, IR, PUP, Suspended, Exempt, NFI, Retired (project_game's OUT_WORDS), the same set, and cannot see a player cut off the roster (his row is gone), a small under-count of the backtest's as-of set. PACE is already in the props.json header; add ABSORB and ABSORB_THR beside it. The two rushing changes were scored one at a time, not together; once both are in, the by-season run sets BACKTEST (about 19.13 / 18.15 receiving from 19.16 / 18.16, 17.70 / 16.97 rushing from 17.77 / 17.04, if they add).",
]


def write_md(o, consts, V):
    t = ["# Game-script variants and absorption when a starter is out", "", "29 Sep 2026. experiments/props_gs_absorb.py, reports/props_gs_absorb.csv. Two claims on the live player-prop rule (nflmodel/props.py), walk-forward, as-of only, no market input: part 1, the game script on the team's plays (the live line, a refit, a win-probability form, a quadratic form, opponent pace); part 2, absorption of an absent starter's share by his teammates at a fitted fraction, a different form from round ten's pro rata (which lost on both windows). Scores: mean absolute error per player-game of the volume (targets, carries, dropbacks) and of the yards line, signed bias, the paired standard error against base, 2019-22 and 2023-25 with 2017-18 beside them as the fit window, and by tier of the base yards line.", "",
         "## Adoption rule (set before the run)", "",
         "On the touch frame (every player-game with a touch of the kind; the frame the rule's constants were chosen on and reports/props_by_season.csv grades), a variant is adopted only if it lowers yards MAE on both windows (2019-22 and 2023-25) and does not raise volume MAE (targets, carries, dropbacks) on either. The active frame (plus every game a projected receiver or rusher played snaps in without a touch, actual 0: the population the card projects) is a check beside it: a variant that passes on the touch frame but raises yards MAE on the active frame on either window is flagged, not adopted. Every constant is fitted on the fit window only (part 1: team-games 2016-18; part 2: the frame's 2017-18, since 2016 is the first charted season and its players have no history). No market input anywhere: the game script reads the game model's expected points (pred_v3; margin = own minus the opponent's, total = their sum), never the closing spread or total.", "",
         "## Frames", ""]
    for kind in ("rec", "rush", "pass"):
        f = load(kind); tt = f[f.touch == 1]
        t.append(f"- {kind}: touch frame {len(tt)} player-games 2017-25 ({int(tt.season.between(*FIT).sum())} in 2017-18, {int(tt.season.between(*WIN['2019-22']).sum())} in 2019-22, {int(tt.season.between(*WIN['2023-25']).sum())} in 2023-25)" + (f"; active frame {len(f)} ({int((f.touch == 0).sum())} zero-touch games)." if kind != "pass" else "."))
    t += ["", "## Part 1: the game script on the team's plays", "", f"Fitted on {consts['rec']['n_fit']} team-games of 2016-18 (each team in each game, with 3+ previous games for the team and the opponent). The target is the team's plays of the kind in the game minus its live base (its last-17 average, blended props.PACE toward the opponent's allowed per game: 0 for pass plays and runs, 0.25 for dropbacks); the model's margin is from the team's side, the total is the model's, centred on GS_TOTAL = {PR.GS_TOTAL} (the model's mean total over the frame is about 45.5, so the intercept of a refit absorbs the two-point difference from the closing-total mean the live line was centred on). The line is constant + b1 x margin + b2 x (total - GS_TOTAL); winprob replaces the margin by p - 0.5 with p = Phi(margin / {SIGMA:.0f}); quad adds b3 x margin^2 + b4 x margin x total. In-sample MAE of the plays beyond the base, 2016-18, beside each.", "",
          "| kind | variant | constants | fit MAE (plays) |", "|:--|:--|:--|--:|"]
    for kind in ("rec", "rush", "pass"):
        c = consts[kind]
        for v in ("base", "refit", "winprob", "quad"):
            t.append(f"| {kind} ({VCOL[kind]}) | {v} | " + ", ".join(f"{x:.4f}" for x in c[v]) + f" | {c['fit_mae_' + v]:.3f} |")
    t += ["", "The standard deviation of the target (plays beyond the base) is " + ", ".join(f"{k} {consts[k]['sd_y']:.2f}" for k in consts) + ". pace_w: the team's last-17 average blended w toward the opponent's allowed plays per game (w = 0.25, 0.5), the live line on top.", ""]
    for kind in ("rec", "rush", "pass"):
        vol = {"rec": "targets", "rush": "carries", "pass": "dropbacks"}[kind]
        for fr in (("touch", "active") if kind != "pass" else ("touch",)):
            t += [f"### {kind}, {fr} frame", "", f"{vol} (volume)", "", table(o, 1, f"{kind}_{vol}", fr), "", "yards", "", table(o, 1, f"{kind}_yards", fr), ""]
    t += ["### Part 1 by tier of the base yards line (yards MAE, n), touch frame", ""]
    for kind in ("rec", "rush", "pass"):
        t += [f"{kind}", "", tier_table(o, 1, f"{kind}_yards", "touch", ["base", "refit", "winprob", "quad", "pace_0.25", "pace_0.5"]), ""]
    t += ["## Part 2: absorption when a starter is out", "", f"Absent = a player with a snap at a skill position in one of the team's last {LOOKBACK} games and none this week (hindsight), whose decayed share as of the game (props.share_blend of his touch-games and active-games shares after his last game) is >= {THR['rec']} for receivers, >= {THR['rush']} for rushers. As-of = the same candidates the live rule could know were out before the game: listed Out or Doubtful on the week's injury report, or without an active listing on the week's roster (reserve / IR, PUP, suspended, cut), whether or not they then played. The teammates' added share = f x the absent share, split among the remaining players of the frame in proportion to their own shares (same-position teammates, or all teammates); f fitted on 2017-18 team-games of the active frame by least squares of the frame's players' actual share of the team's plays beyond their projected share on an intercept and the absent share by the absent player's position (only positions with {MIN_ABS}+ fit-window absences get an f; the rest 0). The matrix below is recipient position (rows) by absent position (columns): the same-position f is the diagonal, the all-teammates f the 'all' row.", ""]
    for kind in ("rec", "rush"):
        P = PART2_FIT[kind]; F, cols, info = P["F"], P["cols"], P["info"]
        t += [f"### {kind}", "", f"Absences: {info['team_games_with_hind']} of {info['team_games_frame']} frame team-games have a hindsight absence ({info['hind']} player-games, by position {info['by_pos_hind']}, mean absent share {info['mean_share_hind']}); {info['asof']} as-of absences, {info['both']} of them also absent in hindsight, {info['asof_played']} listed out who then played. Fit: {info['fit_team_games']} team-games 2017-18, absences by position {info['fit_absences_by_pos']}, fitted positions {cols}.", "",
              "| recipient \\ absent | intercept | " + " | ".join(cols) + " |", "|:--|--:|" + "--:|" * len(cols)]
        for rec_, row in F.items():
            t.append(f"| {rec_} | {row['intercept']:+.3f} | " + " | ".join(f"{row.get(p, 0.0):+.3f}" for p in cols) + " |")
        t.append("")
        vol = {"rec": "targets", "rush": "carries"}[kind]
        for fr in ("touch", "active"):
            t += [f"#### {kind}, {fr} frame", "", f"{vol} (volume)", "", table(o, 2, f"{kind}_{vol}", fr), "", "yards", "", table(o, 2, f"{kind}_yards", fr), ""]
        t += [f"#### {kind} by tier of the base yards line (yards MAE, n), touch frame", "", tier_table(o, 2, f"{kind}_yards", "touch", ["base", "hind_same", "hind_same_half", "hind_all", "hind_all_half", "asof_same", "asof_same_half", "asof_all", "asof_all_half"]), ""]
    t += ["## Verdicts", "", "| part | kind | variant | yards better on both (touch) | volume not worse on both (touch) | active-frame check | verdict |", "|--:|:--|:--|:--|:--|:--|:--|"]
    for r in V.itertuples():
        t.append(f"| {r.part} | {r.kind} | {r.variant} | {r.yards_better_both} | {r.volume_not_worse_both} | {r.active_check} | {r.verdict} |")
    t += ["", "## Decision", ""] + DECISION + ["", "## Runtime", "", ", ".join(f"{k} {v:.0f}s" for k, v in TIMES.items()) + f"; total {time.time() - T0:.0f}s (4 cores shared with other studies). The frames are built once and cached ({CACHE}): the first run loaded props_by_season's state in 10s and built the receiving, rushing and passing frames in 13s, 9s and 3s; a run from the cache scores everything in about 6s (--rebuild forces a rebuild)."]
    pathlib.Path(OUT_MD).write_text("\n".join(t) + "\n")


def main():
    need = [CACHE / f"frame_{k}.parquet" for k in ("rec", "rush", "pass")] + [CACHE / "teams.parquet", CACHE / "act.parquet", CACHE / "known_out.parquet"] + [CACHE / f"share_{n}_{k}.parquet" for n in ("touch", "active") for k in ("rec", "rush")]
    if "--rebuild" in sys.argv or not all(p.exists() for p in need):
        t1 = time.time(); build_frames(); TIMES["build"] = time.time() - t1
    else:
        log("frames from cache", CACHE)
    t1 = time.time(); consts = part1(); TIMES["part1"] = time.time() - t1
    part2()
    o = pd.DataFrame(ROWS); o.to_csv(OUT_CSV, index=False); V = verdicts(o); print("\n" + V.to_string(), flush=True)
    write_md(o, consts, V); log("DONE", OUT_CSV, OUT_MD)


if __name__ == "__main__":
    main()
