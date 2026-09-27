"""Round fifteen (27 Sep 2026): is the yards line biased by tier? On the adopted rule (rounds one to thirteen), walk-forward,
scored on 2019 to 2022 and 2023 to 2025 by the mean miss of the yards line per player-game, with the signed miss by
decile of the line beside it. Our own data only (the books' lines are not read; the week's card, where established
starters sat well under their book lines and low-usage players over, was only the prompt).

  0. Tier bias of the current rule: mean signed error (line minus actual) and mean absolute error by decile of the line,
     per stat and window (reports/props_backtest15_tiers.csv; every variant below gets the same table, on the same
     rows, so a change that helps the average by hurting the stars is visible).
  A. A median factor that rises with volume. The flat factor (receivers 0.81, rushers 0.84, QBs 0.88) turns every
     player's mean into the line with one constant, but the median of a right-skewed yardage distribution sits far
     below the mean for a 3-target player and close to it for a 10-target one. Forms, each fitted on 2017-18 with the
     team reconciliation of round six applied at every candidate (the order the live rule uses), by mean absolute
     error: a step at a mean-yards threshold; a logistic curve in the mean; a straight line in the mean; five bins by
     quintile of the mean; and the step and logistic in projected touches instead of yards. Receptions the same on
     MED_CATCH, by projected targets.
  B. Shares that add to more than one, on top of A's winner. The decayed usage shares of a team's players are not
     normalised; round ten found that handing an absent teammate's share to the others (scaling up when the sum is
     under one) lost. Here the other side: every share scaled by 1 / sum when the sum exceeds one. The sum over the
     players who play (hindsight: a bound), over a roster proxy (anyone with a profile who played for the team in this
     game or one of its last three: what the card sums), and over that proxy less the players this week's report
     lists Out or Doubtful (what the card knows); in full and by half.
  C. Stale role, on top of A's and B's winners. The snap trend of round thirteen at half weight; the snap trend on the
     volume (targets, carries, so receptions move too, and before the team reconciliation) instead of on the yards
     line; and the usage decay itself faster (0.80, 0.75 against 0.85).
  D. Whatever won on both windows, together, against the current rule.
Beside each error the paired standard error of its difference from the current rule (a gain under one standard error
is inside the noise). Output reports/props_backtest15.csv (variant x window: mae, bias, n, se, the fitted constants)
and reports/props_backtest15_tiers.csv (the decile tables). Adopt only a variant better on both windows, by at least one
standard error. Adopted (nflmodel/props.py MED_TIER): receiving, the logistic in the mean with the scale fixed at 5 yards
(0.690 to 0.869 around 32.6 mean yards; 19.17 / 18.16 against 19.28 / 18.25); passing, the straight line in the mean
(0.630 + 0.00091 x mean yards; 56.56 / 56.06 against 56.74 / 56.21). Not adopted: rushing (every form inside one standard
error), the share caps (lost on rushing; inside the noise on receiving), the snap trend at half weight or on the volume, a
faster decay, and the receptions floor (a line of at least one catch: 1.428 / 1.346 against 1.435 / 1.355, but this backtest
scores only player-games with a target, so it cannot see the zero-target games a fringe player's floor is graded on). The
script fits every form from the mean the build keeps (mean_line, before any median factor), so it re-derives the adopted
curve each run and scores the flat factor as its baseline."""
import numpy as np, pandas as pd, pathlib
from scipy.optimize import minimize
from nflmodel import props as PR
src = pathlib.Path(__file__).with_name("props_by_season.py").read_text().split("by_season, by_pos, by_bucket = [], [], []")[0]
src = src.replace("    dg = t.groupby([\"defteam\", \"season\", \"week\", \"game_id\"])", "    globals()[\"_LAST\"] = (pg, R, R85)\n    dg = t.groupby([\"defteam\", \"season\", \"week\", \"game_id\"])", 1)
ns = {"__name__": "bys"}; exec(compile(src, "bys", "exec"), ns); build = ns["build"]
WIN = {"2019-22": (2019, 2022), "2023-25": (2023, 2025)}; FIT = (2017, 2018); MIN_VOL = 8
OUT_CSV, OUT_TIERS = "reports/props_backtest15.csv", "reports/props_backtest15_tiers.csv"


class Frame:
    """One kind's player-games with the pieces of the live rule pulled apart so a variant can change one and re-apply
    the rest in the live order: mean (volume x rate x defense x wind, before the median factor) -> median factor ->
    team reconciliation -> injury report -> snap trend."""

    def __init__(self, kind, f):
        self.kind, self.f = kind, f.reset_index(drop=True)
        f = self.f; self.base = f.mean_line.values.astype(float); self.vol = f.vol.values.astype(float); self.act = f.act_yds.values.astype(float)
        self.codes = pd.factorize(f.game_id.astype(str) + "|" + f.posteam.astype(str))[0]; self.ngrp = self.codes.max() + 1
        fy = PR.TEAM_FIT[kind]["yds"]; self.exp_y = fy[0] + fy[1] * f.exp_pts.values.astype(float); self.ok = f.exp_pts.notna().values; self.wy = PR.RECON_W[kind]["yds"]
        if kind in PR.INJ_F:
            grp = [PR.inj_group(a, b) for a, b in zip(f.report_status, f.practice_status)]
            self.inj = np.array([PR.INJ_F[kind].get(g, 1.0) for g in grp]); self.sr = np.array([PR.snap_ratio(a, b) for a, b in zip(f.s3, f.s10)])
        else:
            self.inj = np.ones(len(f)); self.sr = np.ones(len(f))
        self.fit = (f.season.between(*FIT)).values; self.win = {w: f.season.between(a, b).values for w, (a, b) in WIN.items()}

    def recon(self, line):
        s = np.bincount(self.codes, weights=line, minlength=self.ngrp)[self.codes]
        with np.errstate(divide="ignore", invalid="ignore"):
            scale = np.clip(self.exp_y / np.where(s == 0, np.nan, s), 0.5, 2.0)
        ok = self.ok & ~np.isnan(scale)
        return np.where(ok, line * (1 + self.wy * (scale - 1)), line)

    def line(self, med, vol_scale=1.0, snap_w=None, snap_on_vol=False):
        """The full line from a median factor (a constant, a per-row array, or a Med), a scale on the volume, and the
        snap weight (the adopted SNAP_W when None) on the yards line, or on the volume."""
        med = med.of(self) if isinstance(med, Med) else med
        w = PR.SNAP_W.get(self.kind, 0.0) if snap_w is None else snap_w
        sf = 1 + w * (self.sr - 1)
        if snap_on_vol:
            return self.recon(med * self.base * vol_scale * sf) * self.inj
        return self.recon(med * self.base * vol_scale) * self.inj * sf

    def mae(self, line, mask):
        return float(np.abs(line[mask] - self.act[mask]).mean())


# ---------------- median-factor forms ----------------
def sigmoid(z):
    return 1 / (1 + np.exp(-np.clip(z, -50, 50)))


FORMS = {
    "step": lambda p, x: np.where(x < p[2], p[0], p[1]),                    # lo below the threshold, hi above
    "logistic": lambda p, x: p[0] + (p[1] - p[0]) * sigmoid((x - p[2]) / (p[3] if abs(p[3]) > 1e-3 else 1e-3)),   # lo to hi around the centre, over the scale
    "logistic5": lambda p, x: p[0] + (p[1] - p[0]) * sigmoid((x - p[2]) / 5.0),   # the scale fixed at 5 mean yards: no cliff on the card
    "linear": lambda p, x: np.clip(p[0] + p[1] * x, 0.5, 1.2),
    "floor": lambda p, x: np.ones_like(x),   # placeholder: the floor is built where it is scored
    "bins": lambda p, x: p[1][np.clip(np.searchsorted(p[0], x, side="right") - 1, 0, len(p[0]) - 2)],   # p = (edges, factors)
}


class Med:
    """A median factor as a function of a frame: the form, its constants and its input (mean yards or touches)."""

    def __init__(self, form, p, on):
        self.form, self.p, self.on = form, p, on

    def of(self, F):
        return FORMS[self.form](self.p, F.base if self.on == "mean" else F.vol)


def fit_form(F, form, on, init, mask, **kw):
    """Nelder-Mead on the mean absolute error of the full line over the fitting rows, several starts."""
    x = F.base if on == "mean" else F.vol; fn = FORMS[form]
    def obj(p):
        return F.mae(F.line(fn(p, x), **kw), mask)
    best = None
    for p0 in init:
        r = minimize(obj, np.array(p0, float), method="Nelder-Mead", options={"xatol": 1e-3, "fatol": 1e-4, "maxiter": 2000})
        if best is None or r.fun < best.fun: best = r
    return Med(form, best.x, on)


def fit_bins(F, on, n, mask, init, **kw):
    """One factor per quantile bin of the fitting rows, coordinate descent on a 0.01 grid, three passes."""
    x = F.base if on == "mean" else F.vol; edges = np.quantile(x[mask], np.linspace(0, 1, n + 1)); edges[0], edges[-1] = -np.inf, np.inf
    b = np.clip(np.searchsorted(edges, x, side="right") - 1, 0, n - 1); fac = np.full(n, float(init)); grid = np.round(np.arange(0.55, 1.1501, 0.01), 2)
    for _ in range(3):
        for i in range(n):
            errs = []
            for g in grid:
                f2 = fac.copy(); f2[i] = g; errs.append(F.mae(F.line(f2[b], **kw), mask))
            fac[i] = grid[int(np.argmin(errs))]
    return Med("bins", (edges, fac), on)


def describe(m):
    p = m.p; unit = "mean yards" if m.on == "mean" else "touches"
    if m.form == "step": return f"lo {p[0]:.3f} below {p[2]:.1f} {unit}, hi {p[1]:.3f} above"
    if m.form == "logistic5": return f"lo {p[0]:.3f}, hi {p[1]:.3f}, centre {p[2]:.1f}, scale 5 {unit}"
    if m.form == "logistic": return f"lo {p[0]:.3f}, hi {p[1]:.3f}, centre {p[2]:.1f}, scale {p[3]:.2f} {unit}"
    if m.form == "linear": return f"{p[0]:.3f} + {p[1]:.5f} x {unit}, clipped 0.5 to 1.2"
    return f"quintiles of {unit} at " + ", ".join(f"{e:.1f}" for e in p[0][1:-1]) + ": " + ", ".join(f"{v:.2f}" for v in p[1])


# ---------------- share sums per team-game ----------------
def share_sums(kind, f, pg, R, R85, rep):
    """Per (game_id, posteam), the sum of the decayed usage shares of: the players who play with a profile (S1); a
    roster proxy, those plus anyone with a profile who played for the team in one of its last three games (S2); and
    the proxy less the absent players this week's report lists Out or Doubtful (S3, what the live card can know)."""
    x = pg[["pid", "posteam", "season", "week", "game_id", "n", "team_n"]].merge(R[["pid", "game_id", "n", "games_prev"]].rename(columns={"n": "n17"}), on=["pid", "game_id"]).merge(R85[["pid", "game_id", "n_85", "team_n_85"]], on=["pid", "game_id"])
    x["share_pre"] = (x.n_85 / x.team_n_85.replace(0, np.nan)).fillna(0.0); x["share_post"] = ((PR.DECAY * x.n_85 + x.n) / (PR.DECAY * x.team_n_85 + x.team_n).replace(0, np.nan)).fillna(0.0)
    x["elig"] = (x.n17 >= MIN_VOL) & (x.games_prev >= 3); x["elig_post"] = (x.n17 + x.n >= MIN_VOL) & (x.games_prev + 1 >= 3)
    od = rep[rep.report_status.isin(["Out", "Doubtful"])]; out = set(zip(od.season.astype(int), od.week.astype(int), od.pid))
    S1, S2, S3 = {}, {}, {}
    for team, g in x.groupby("posteam"):
        order = g.drop_duplicates("game_id").sort_values(["season", "week"])[["game_id", "season", "week"]].values.tolist(); by = {gid: h for gid, h in g.groupby("game_id")}; last = {}
        for i, (gid, sn, wk) in enumerate(order):
            h = by[gid]; present = set(h.pid); s1 = float(h.share_pre[h.elig].sum()); s2 = s3 = s1
            for pid, (j, sh, el) in last.items():
                if pid not in present and i - j <= 3 and el:
                    s2 += sh
                    if (int(sn), int(wk), pid) not in out: s3 += sh
            S1[(gid, team)] = s1; S2[(gid, team)] = s2; S3[(gid, team)] = s3
            for r in h.itertuples(): last[r.pid] = (i, r.share_post, bool(r.elig_post))
    keys = list(zip(f.game_id, f.posteam))
    return {"playing": np.array([S1.get(k, 1.0) for k in keys]), "roster": np.array([S2.get(k, 1.0) for k in keys]), "known": np.array([S3.get(k, 1.0) for k in keys])}


def cap(S, half=False):
    c = np.minimum(1.0, 1.0 / np.where(S > 0, S, 1.0)); return 1 + 0.5 * (c - 1) if half else c


# ---------------- scoring ----------------
def deciles(F, line):
    """Decile of the line within each window (1 = the lowest lines, 10 the highest), by the current rule; -1 outside."""
    dec = np.full(len(line), -1)
    for w, mk in F.win.items():
        r = pd.Series(line[mk]).rank(method="first"); dec[mk] = np.minimum((r * 10 / mk.sum()).astype(int).values, 9)
    return dec


class Scorer:
    def __init__(self, stat, F, act, dec, rows, tiers):
        self.stat, self.F, self.act, self.dec, self.rows, self.tiers = stat, F, act, dec, rows, tiers; self.cur = None; self.se = {}; self.lines = {}

    def __call__(self, variant, line, fitted="", against=None):
        F, act = self.F, self.act; out = {}; ref = self.lines.get(against, self.cur); self.se[variant] = {}
        for w, mk in F.win.items():
            e = line[mk] - act[mk]; out[w] = float(np.abs(e).mean())
            d = np.abs(e) - np.abs(self.cur[mk] - act[mk]) if self.cur is not None else np.zeros(mk.sum()); dr = np.abs(e) - np.abs(ref[mk] - act[mk]) if ref is not None else d
            self.se[variant][w] = float(dr.std(ddof=1) / np.sqrt(len(dr))) if ref is not None else 0.0
            self.rows.append({"stat": self.stat, "variant": variant, "window": w, "n": int(mk.sum()), "mae": round(out[w], 4), "bias": round(float(e.mean()), 3), "se_vs_current": round(float(d.std(ddof=1) / np.sqrt(len(d))), 4), "mean_line": round(float(line[mk].mean()), 2), "mean_actual": round(float(act[mk].mean()), 2), "fitted": fitted, "against": against or ""})
            for d_ in range(10):
                m = mk & (self.dec == d_); ee = line[m] - act[m]
                self.tiers.append({"stat": self.stat, "variant": variant, "window": w, "decile": d_ + 1, "n": int(m.sum()), "mean_line": round(float(line[m].mean()), 2), "mean_actual": round(float(act[m].mean()), 2), "bias": round(float(ee.mean()), 3), "mae": round(float(np.abs(ee).mean()), 3)})
        if self.cur is None: self.cur = line
        self.lines[variant] = line
        dp = 4 if self.stat.endswith("catches") else 3
        print(f"{self.stat:11s} {variant:28s} " + "  ".join(f"{w} {v:.{dp}f}" for w, v in out.items()) + (f"   [{fitted}]" if fitted else "") + (f"  vs {against}" if against else ""), flush=True); return out


def better(m, ref):
    return all(m[w] < ref[w] for w in WIN)


def pick(cands, ref, se=None):
    """The candidates better than the reference on both windows, by at least one paired standard error when `se` gives
    each candidate's (a gain inside the noise is not a gain); the best by the two errors summed, or None."""
    won = {k: v for k, v in cands.items() if better(v, ref) and (se is None or all(ref[w] - v[w] >= se[k][w] for w in WIN))}
    return min(won, key=lambda k: sum(won[k].values())) if won else None


def main():
    rows, tiers, adopted = [], [], {}
    for kind in ("rec", "rush", "pass"):
        f, _ = build(kind); pg, R, R85 = ns["_LAST"]; F = Frame(kind, f); stat = f"{kind}_yards"; fit = F.fit
        assert np.allclose(F.line(PR.med_factor(kind, F.base)), F.f.yds_line.values, atol=1e-6), "the pulled-apart rule must reproduce the live line"
        cur = F.line(PR.MED[kind]); sc = Scorer(stat, F, F.act, deciles(F, cur), rows, tiers); base = sc("flat", cur, f"MED {PR.MED[kind]}, the flat factor (the rule before this round)"); ref, ref_name = base, "flat"
        # ---- A. the median factor by tier ----
        q = lambda on, p_: float(np.quantile((F.base if on == "mean" else F.vol)[fit], p_)); sd = lambda on: float(np.std((F.base if on == "mean" else F.vol)[fit]))
        meds = {"A_step_mean": fit_form(F, "step", "mean", [(0.78, 0.9, q("mean", p_)) for p_ in (0.3, 0.5, 0.7)], fit),
                "A_logistic_mean": fit_form(F, "logistic", "mean", [(0.78, 0.9, q("mean", 0.5), sd("mean") / 4), (0.75, 0.95, q("mean", 0.6), sd("mean") / 2)], fit),
                "A_logistic_mean_s5": fit_form(F, "logistic5", "mean", [(0.72, 0.86, q("mean", 0.5)), (0.75, 0.9, q("mean", 0.6))], fit),
                "A_linear_mean": fit_form(F, "linear", "mean", [(PR.MED[kind], 0.0), (0.7, 0.1 / sd("mean"))], fit),
                "A_bins5_mean": fit_bins(F, "mean", 5, fit, PR.MED[kind]),
                "A_step_touches": fit_form(F, "step", "touches", [(0.78, 0.9, q("touches", p_)) for p_ in (0.3, 0.5, 0.7)], fit),
                "A_logistic_touches": fit_form(F, "logistic", "touches", [(0.78, 0.9, q("touches", 0.5), sd("touches") / 4), (0.75, 0.95, q("touches", 0.6), sd("touches") / 2)], fit)}
        cands = {k: sc(k, F.line(m), describe(m)) for k, m in meds.items()}
        kA = pick(cands, base, sc.se); med = meds[kA] if kA else PR.MED[kind]
        if kA: ref, ref_name = cands[kA], kA; adopted[stat] = {"median": kA}
        # ---- B. shares capped at one, on top of A ----
        vs = 1.0
        if kind != "pass":
            S = share_sums(kind, F.f, pg, R, R85, ns["_REP"])
            print(f"{stat}: share sums, mean and share of rows over one: " + "; ".join(f"{k} {v.mean():.3f}, {(v > 1).mean():.1%}" for k, v in S.items()), flush=True)
            cB = {}
            for name in ("playing", "roster", "known"):
                for half in (False, True):
                    k = f"B_cap_{name}" + ("_half" if half else ""); cB[k] = sc(k, F.line(med, vol_scale=cap(S[name], half)), f"shares x {'half of ' if half else ''}min(1, 1/sum), sum over {name}", ref_name)
            kB = pick({k: v for k, v in cB.items() if "known" in k}, ref, sc.se)   # only the sum the card can know is adoptable
            if kB: vs = cap(S["known"], kB.endswith("half")); ref, ref_name = cB[kB], kB; adopted.setdefault(stat, {})["cap"] = kB
        # ---- C. stale role, on top of A and B ----
        snap_w, snap_vol = None, False
        if kind in PR.SNAP_W:
            cC = {"C_snap_w0.5": sc("C_snap_w0.5", F.line(med, vol_scale=vs, snap_w=0.5), "snap trend half way, on the yards line", ref_name)}
            for w in (0.25, 0.5):
                cC[f"C_snap_vol_w{w}"] = sc(f"C_snap_vol_w{w}", F.line(med, vol_scale=vs, snap_w=w, snap_on_vol=True), f"snap trend {w} of the way on the volume, before the team reconciliation", ref_name)
            for dc in (0.80, 0.75):
                PR.DECAY = dc; f2, _ = build(kind); PR.DECAY = 0.85; F2 = Frame(kind, f2); assert (F2.f.pid.values == F.f.pid.values).all() and (F2.f.game_id.values == F.f.game_id.values).all()
                cC[f"C_decay_{dc}"] = sc(f"C_decay_{dc}", F2.line(med, vol_scale=vs), f"usage decayed {dc} per game back (0.85 today)", ref_name)
            kC = pick({k: v for k, v in cC.items() if not k.startswith("C_decay")}, ref, sc.se)
            if kC: snap_w = 0.5 if "w0.5" in kC else 0.25; snap_vol = "vol" in kC; ref, ref_name = cC[kC], kC; adopted.setdefault(stat, {})["snap"] = kC
            if pick({k: v for k, v in cC.items() if k.startswith("C_decay")}, ref, sc.se): adopted.setdefault(stat, {})["decay"] = "faster decay won: rebuild needed"
        # ---- D. together ----
        if len(adopted.get(stat, {})) >= 2:
            sc("D_together (" + ", ".join(adopted[stat].values()) + ")", F.line(med, vol_scale=vs, snap_w=snap_w, snap_on_vol=snap_vol), "", "flat")
        # ---- receptions: MED_CATCH by projected targets (no reconciliation on catches) ----
        if kind == "rec":
            cb = F.f.catch_line.values / PR.MED_CATCH; actc = F.f.act_catch.values.astype(float); tg = F.vol
            scc = Scorer("rec_catches", F, actc, deciles(F, PR.MED_CATCH * cb), rows, tiers); basec = scc("flat", PR.MED_CATCH * cb, f"MED_CATCH {PR.MED_CATCH}, the flat factor")
            def objc(form, p): return float(np.abs((FORMS[form](p, tg) * cb - actc)[fit]).mean())
            mc = {"A_step_targets": Med("step", min((minimize(lambda p: objc("step", p), np.array(p0, float), method="Nelder-Mead") for p0 in [(0.85, 0.95, q("touches", p_)) for p_ in (0.3, 0.5, 0.7)]), key=lambda r: r.fun).x, "touches"),
                  "A_logistic_targets": Med("logistic", min((minimize(lambda p: objc("logistic", p), np.array(p0, float), method="Nelder-Mead") for p0 in [(0.85, 0.95, q("touches", 0.5), sd("touches") / 4), (0.8, 1.0, q("touches", 0.6), sd("touches") / 2)]), key=lambda r: r.fun).x, "touches")}
            edges = np.quantile(tg[fit], np.linspace(0, 1, 6)); edges[0], edges[-1] = -np.inf, np.inf; b5 = np.clip(np.searchsorted(edges, tg, side="right") - 1, 0, 4); fac5 = np.full(5, PR.MED_CATCH); grid = np.round(np.arange(0.6, 1.2001, 0.01), 2)
            for _ in range(3):
                for i in range(5):
                    errs = []
                    for g_ in grid:
                        f5 = fac5.copy(); f5[i] = g_; errs.append(float(np.abs((f5[b5] * cb - actc)[fit]).mean()))
                    fac5[i] = grid[int(np.argmin(errs))]
            mc["A_bins5_targets"] = Med("bins", (edges, fac5), "touches")
            cc = {k: scc(k, m.of(F) * cb, describe(m).replace("touches", "targets")) for k, m in mc.items()}
            c0 = min(np.round(np.arange(0.4, 1.501, 0.05), 2), key=lambda c: float(np.abs((np.where(cb >= c, np.maximum(PR.MED_CATCH * cb, 1.0), PR.MED_CATCH * cb) - actc)[fit]).mean()))
            mc["A_floor1"] = Med("floor", c0, "touches"); cc["A_floor1"] = scc("A_floor1", np.where(cb >= c0, np.maximum(PR.MED_CATCH * cb, 1.0), PR.MED_CATCH * cb), f"at least 1 when the mean catches are {c0:.2f} or more (the median of a count that is 0 less than half the time is 1)")
            kAc = pick(cc, basec, scc.se); medc = (scc.lines[kAc] / cb if kAc else PR.MED_CATCH); refc, refc_name = (cc[kAc], kAc) if kAc else (basec, "flat")
            if kAc: adopted["rec_catches"] = {"median": kAc}
            c2 = {f"C_snap_vol_w{w}": scc(f"C_snap_vol_w{w}", medc * cb * (1 + w * (F.sr - 1)), f"snap trend {w} of the way on the targets", refc_name) for w in (0.25, 0.5)}
            kCc = pick(c2, refc, scc.se)
            if kCc: adopted.setdefault("rec_catches", {})["snap"] = kCc
    o = pd.DataFrame(rows); cur = o[o.variant == "flat"].set_index(["stat", "window"]).mae
    def verdict(r):
        if r.variant == "flat": return "the rule before this round"
        g = {w: (cur[(r.stat, w)] - o[(o.stat == r.stat) & (o.variant == r.variant) & (o.window == w)].mae.iloc[0], o[(o.stat == r.stat) & (o.variant == r.variant) & (o.window == w)].se_vs_current.iloc[0]) for w in WIN}
        if not all(a > 0 for a, _ in g.values()): return "not adopted"
        return "better on both windows" if all(a >= b for a, b in g.values()) else "better on both windows, inside the noise"
    o["verdict"] = [verdict(r) for r in o.itertuples()]
    o.to_csv(OUT_CSV, index=False); pd.DataFrame(tiers).to_csv(OUT_TIERS, index=False)
    print(o.pivot_table(index=["stat", "variant"], columns="window", values="mae", sort=False).to_string()); print("won at each stage:", adopted); print("DONE")


if __name__ == "__main__":
    main()
