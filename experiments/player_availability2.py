"""Availability follow-up (29 Sep 2026): the midweek roster and a pre-registered passer logit.

1. Harness look-ahead. nflmodel.player_season.roster_at keeps players with weekly roster status ACT at the as-of
   week. From 2019 nflverse marks game-day inactives INA (2016-18 have no INA: they are ACT), so the 2019-25 rows
   drop players ruled inactive for the as-of week's game, which the live page cannot know midweek. Here the rows are
   rebuilt with the roster as the page sees it midweek: status ACT or INA (on the 53, not on a reserve list), ACT
   first when a player has two rows in a week. 2016-18 rows are identical (no INA), so their part files are copied
   from today's build after the check; every constant fitted on 2016-18 is unchanged.
   Scored on the old rows (today's build, ACT only) and the corrected rows: flat (AVAIL/BLEND refit on 2016-18) and
   today's adopted pooled-logit mult, for rec, rush and pass, both windows, pooled and by as-of week.
2. Passers: a separate logit on the 2016-18 passer rows (same features and fit), variants mult and share, blend
   refit on 2016-18; the rule in reports/player_availability2.md (written before the run).
Also the calibration of p on the corrected rows by kind.

  python experiments/player_availability2.py build [--jobs N]
  python experiments/player_availability2.py study
Output: reports/player_availability2.csv (+ results appended to reports/player_availability2.md by `report`).
"""
from __future__ import annotations
import sys, time, os, shutil
import numpy as np, pandas as pd
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from nflmodel import player_season as PS
from experiments import player_season_backtest as BT
from experiments import player_availability as PA

RAW, OUT, REP = PS.RAW, PS.OUT, PS.REP
SCR = Path(os.environ.get("AVAIL2_SCRATCH", "/tmp/claude-0/-home-user/c1e0d18e-681a-50ba-b0bb-6c809c2e3dee/scratchpad/availability2"))
PARTS = SCR / "parts"; ROWS = SCR / "rows.csv"
OLD_ROWS = PA.ROWS; OLD_PARTS = PA.PARTS
KEEP = ("ACT", "INA")          # the midweek roster: on the 53 (active or game-day inactive), not on a reserve list
KINDS = PA.KINDS; WINDOWS = PA.WINDOWS


# ---------------------------------------------------------------- the roster as the page sees it midweek
def roster_mid(season: int, week: int) -> pd.DataFrame:
    """roster_at with status ACT or INA (ACT first on a duplicate)."""
    f = RAW / "rosters" / f"roster_weekly_{season}.parquet"
    if not f.exists():
        return pd.DataFrame(columns=["team", "player_id", "position", "name"])
    r = pd.read_parquet(f, columns=["team", "gsis_id", "status", "week", "position", "full_name"]).dropna(subset=["gsis_id"])
    wk = r[r.week <= week].week.max() if (r.week <= week).any() else r.week.min()
    r = r[(r.week == wk) & r.status.isin(KEEP)].assign(o=lambda x: (x.status != "ACT").astype(int)).sort_values("o", kind="stable")
    return r.rename(columns={"gsis_id": "player_id", "full_name": "name"})[["team", "player_id", "position", "name"]].drop_duplicates("player_id")


def rows_for(d, games, names, season, week):
    """experiments/player_season_backtest.rows_for with the midweek roster."""
    p = PS.project(d, names, games, season, week, mode="asof", avail={"rec": 1.0, "rush": 1.0, "pass": 1.0}, roster=roster_mid(season, week))
    act = PS.season_actuals(d, season).set_index(["kind", "player_id"])
    key = list(zip(p.kind, p.player_id))
    p["actual_yards"] = [float(act.yards.get(k, 0.0)) if k in act.index else 0.0 for k in key]
    p["actual_td"] = [float(act.td.get(k, 0.0)) if k in act.index else 0.0 for k in key]
    p["actual_games"] = [int(act.games.get(k, 0)) if k in act.index else 0 for k in key]
    p["games_left_played"] = (p.actual_games - p.games_so_far).clip(lower=0)
    p["actual_rank"] = p.groupby("kind").actual_yards.rank(ascending=False, method="first").astype(int)
    p["actual_pg"] = p.actual_yards / p.actual_games.clip(lower=1)
    return p


def _one(sw):
    s, w = sw
    f = PARTS / f"rows_{s}_{w:02d}.csv"
    if f.exists():
        return s, w, -1.0, 0
    ro = pd.read_parquet(RAW / "rosters" / f"roster_weekly_{s}.parquet", columns=["status"])
    old = OLD_PARTS / f.name
    if not (ro.status == "INA").any() and old.exists():      # no INA that season: the rows are today's
        shutil.copy(old, f); return s, w, -2.0, 0
    t = time.time(); D = PA._load(); t_load = time.time() - t
    p = rows_for(D["d"], D["games"], D["names"], s, w)
    tmp = f.with_suffix(".tmp"); p.round(3).to_csv(tmp, index=False); tmp.rename(f)
    return s, w, time.time() - t - t_load, len(p)


def build(jobs=1):
    PARTS.mkdir(parents=True, exist_ok=True)
    todo = [(s, w) for s in BT.FIT_SEASONS + BT.TEST_SEASONS for w in BT.WEEKS if not (s == 2016 and w == 1)]
    t0 = time.time()
    msg = lambda s, w, dt, n: f"{s} week {w}: " + ("cached" if dt == -1 else "copied (no INA)" if dt == -2 else f"{n} players, {dt:.1f}s") + f" (elapsed {time.time() - t0:.0f}s)"
    if jobs <= 1:
        for sw in todo:
            print(msg(*_one(sw)), flush=True)
    else:
        from multiprocessing import Pool
        with Pool(jobs) as pool:
            for r in pool.imap_unordered(_one, todo):
                print(msg(*r), flush=True)
    R = pd.concat([pd.read_csv(f) for f in sorted(PARTS.glob("rows_*.csv"))], ignore_index=True)
    R.to_csv(ROWS, index=False); print(f"rows: {len(R)} -> {ROWS} ({time.time() - t0:.0f}s)", flush=True)


# ---------------------------------------------------------------- study
def pooled_p(R):
    """Today's pooled logit: out-of-season p on 2016-18, the full 2016-18 fit after."""
    fitm = R.season.isin(BT.FIT_SEASONS); p = pd.Series(np.nan, index=R.index)
    for s in BT.FIT_SEASONS:
        m = PA.fit_logit(R[fitm & (R.season != s)]); p[fitm & (R.season == s)] = PA.predict(m, R[fitm & (R.season == s)])
    M = PA.fit_logit(R[fitm]); p[~fitm] = PA.predict(M, R[~fitm])
    return p, M


def passer_p(R):
    """The passer logit: fitted on the 2016-18 passer rows only (out-of-season on 2016-18)."""
    Q = R[R.kind == "pass"]; fq = Q.season.isin(BT.FIT_SEASONS); p = pd.Series(np.nan, index=R.index)
    for s in BT.FIT_SEASONS:
        m = PA.fit_logit(Q[fq & (Q.season != s)]); idx = Q.index[fq & (Q.season == s)]; p[idx] = PA.predict(m, Q.loc[idx])
    M = PA.fit_logit(Q[fq]); idx = Q.index[~fq]; p[idx] = PA.predict(M, Q.loc[idx])
    return p, M


def prep(path, tag):
    t0 = time.time()
    R = pd.read_csv(path); R = R[R.team_games_left > 0].reset_index(drop=True)
    print(f"[{tag}] rows {len(R)}", flush=True)
    R = PA.features(R)
    R["p"], M = pooled_p(R)
    R["p_pass"], MQ = passer_p(R)
    R["win"] = np.where(R.season.isin(BT.FIT_SEASONS), "2016-18", np.where(R.season <= 2022, "2019-22", "2023-25"))
    print(f"[{tag}] features and logits ({time.time() - t0:.0f}s)", flush=True)
    return R, M, MQ


def score(R, tag, out):
    """Constants on 2016-18, then MAE by kind x variant x window x as-of week. Returns the constants."""
    fitm = R.season.isin(BT.FIT_SEASONS); consts = {}
    todo = [(k, v, "p") for k in KINDS for v in ("flat", "mult")] + [("pass", "pmult", "p_pass"), ("pass", "pshare", "p_pass")]
    for k, v, pc in todo:
        F = R[fitm & (R.kind == k)].assign(p=lambda x: x[pc])
        e, c = PA.fit_variant({"pmult": "mult", "pshare": "share"}.get(v, v), F, k); consts[(k, v)] = c
        out.append({"rows": tag, "row": "fit", "kind": k, "variant": v, "window": "2016-18", "asof_week": "all", "n": len(F), "mae": e, "constants": str(c)})
        print(f"[{tag}] fit {k} {v}: {c} error {e:.2f}", flush=True)
    T = R[~fitm]
    for k, v, pc in todo:
        c = consts[(k, v)]; vv = {"pmult": "mult", "pshare": "share"}.get(v, v)
        X = T[T.kind == k].assign(p=lambda x: x[pc])
        for (w, wk), g in X.groupby(["win", "week"]):
            out.append({"rows": tag, "row": "mae", "kind": k, "variant": v, "window": w, "asof_week": str(wk), **PA.stats(g, PA.share_of(vv, g, c), c["blend"])})
        for w, g in X.groupby("win"):
            out.append({"rows": tag, "row": "mae", "kind": k, "variant": v, "window": w, "asof_week": "all", **PA.stats(g, PA.share_of(vv, g, c), c["blend"])})
    return consts


def calib(R, tag, out):
    bands = [0, 0.3, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0001]; lab = ["<0.3", "0.3-0.5", "0.5-0.6", "0.6-0.7", "0.7-0.8", "0.8-0.9", "0.9-1"]
    for model, pc, sub in (("pooled", "p", R), ("passer", "p_pass", R[R.kind == "pass"])):
        sub = sub.assign(band=pd.cut(sub[pc], bands, labels=lab, right=False))
        y = sub.games_left_played.clip(upper=sub.team_games_left); n = sub.team_games_left
        sub = sub.assign(y=y, pw=sub[pc] * n)
        for (w, k, bd), g in sub.groupby(["win", "kind", "band"], observed=True):
            out.append({"rows": tag, "row": "calib", "variant": model, "kind": k, "window": w, "asof_week": "all", "band": str(bd), "n": len(g),
                        "pred": float(g.pw.sum() / g.team_games_left.sum()), "real": float(g.y.sum() / g.team_games_left.sum())})
        for (w, k), g in sub.groupby(["win", "kind"]):
            ll = float(-(g.y * np.log(g[pc].clip(1e-4, 1 - 1e-4)) + (g.team_games_left - g.y) * np.log(1 - g[pc].clip(1e-4, 1 - 1e-4))).sum() / g.team_games_left.sum())
            out.append({"rows": tag, "row": "calib", "variant": model, "kind": k, "window": w, "asof_week": "all", "band": "all", "n": len(g),
                        "pred": float(g.pw.sum() / g.team_games_left.sum()), "real": float(g.y.sum() / g.team_games_left.sum()), "logloss": ll,
                        "games_miss": float((g[pc] * g.team_games_left - g.y).abs().mean())})


def study():
    t0 = time.time(); out = []
    Rn, Mn, MQn = prep(ROWS, "new")
    Ro, Mo, MQo = prep(OLD_ROWS, "old")
    # the 2016-18 rows and fits must be identical
    same = np.allclose(Mn.coef_, Mo.coef_) and np.allclose(MQn.coef_, MQo.coef_)
    print(f"2016-18 fits identical on old and new rows: {same}", flush=True)
    for f, c in zip(["intercept"] + PA.FEATS, np.r_[MQn.intercept_, MQn.coef_[0]]):
        out.append({"rows": "new", "row": "coef", "variant": "passer", "kind": "pass", "window": "2016-18", "asof_week": "all", "band": f, "value": float(c)})
    for f, c in zip(["intercept"] + PA.FEATS, np.r_[Mn.intercept_, Mn.coef_[0]]):
        out.append({"rows": "new", "row": "coef", "variant": "pooled", "kind": "all", "window": "2016-18", "asof_week": "all", "band": f, "value": float(c)})
    cn = score(Rn, "new", out); co = score(Ro, "old", out)
    print(f"scored ({time.time() - t0:.0f}s)", flush=True)
    # the rows added by the fix (in the new rows, not in the old): who they are and how flat / mult do on them
    key = ["kind", "player_id", "season", "week"]
    Ro_k = set(map(tuple, Ro[key].values))
    Rn["added"] = [tuple(x) not in Ro_k for x in Rn[key].values]
    Rn_k = set(map(tuple, Rn[key].values))
    Ro["dropped"] = [tuple(x) not in Rn_k for x in Ro[key].values]
    T = Rn[Rn.win != "2016-18"]
    for (k, w), g in T.groupby(["kind", "win"]):
        a = g[g.added]
        out.append({"rows": "new", "row": "added", "kind": k, "variant": "", "window": w, "asof_week": "all", "n": int(len(a)), "value": float(len(a) / len(g)),
                    "dropped": int(Ro[(Ro.kind == k) & (Ro.win == w) & Ro.dropped].shape[0])})
        for v in ("flat", "mult"):
            c = cn[(k, v)]
            for part, x in (("added", a), ("kept", g[~g.added])):
                if len(x):
                    out.append({"rows": "new", "row": f"mae_{part}", "kind": k, "variant": v, "window": w, "asof_week": "all", **PA.stats(x, PA.share_of(v, x, c), c["blend"])})
    # feature prevalence (report Out etc.) by window and rowset
    for tag, R in (("old", Ro), ("new", Rn)):
        for w, g in R.groupby("win"):
            for f in ["rep_out", "rep_doubt", "rep_q", "prac_dnp", "prac_lim", "miss_last", "share_now"]:
                out.append({"rows": tag, "row": "prevalence", "kind": "all", "variant": "", "window": w, "asof_week": "all", "band": f, "value": float(g[f].mean())})
            out.append({"rows": tag, "row": "prevalence", "kind": "all", "variant": "", "window": w, "asof_week": "all", "band": "status_INA", "value": float((g.status_now == "INA").mean())})
    calib(Rn, "new", out)
    o = pd.DataFrame(out); o.to_csv(REP / "player_availability2.csv", index=False)
    Rn[["kind", "player_id", "season", "week", "added", "status_now", "p", "p_pass", "team_games_left", "games_left_played"]].to_csv(SCR / "pred.csv", index=False)
    print(f"done ({time.time() - t0:.0f}s)", flush=True)
    return o


# ---------------------------------------------------------------- report
def rule(o, rows, kind, variants, base="flat"):
    m = o[(o.row == "mae") & (o.rows == rows) & (o.kind == kind)]
    b = m[m.variant == base].set_index(["window", "asof_week"]).mae; res = []
    for v in variants:
        x = m[m.variant == v].set_index(["window", "asof_week"]).mae
        gains = {w: float(b[(w, "all")] - x[(w, "all")]) for w in WINDOWS}; g = min(gains.values())
        wk = [i for i in x.index if i[1] != "all"]; wi = max(wk, key=lambda i: float(x[i] - b[i])); worst = float(x[wi] - b[wi])
        res.append({"kind": kind, "variant": v, "rows": rows, "gain_2019-22": gains["2019-22"], "gain_2023-25": gains["2023-25"], "smaller_gain": g,
                    "worst_week": f"{wi[0]} wk {wi[1]}", "worst_week_loss": worst, "passes": "yes" if (g > 0 and worst <= g) else "no"})
    return res


def report():
    o = pd.read_csv(REP / "player_availability2.csv", dtype={"asof_week": str})
    md_path = REP / "player_availability2.md"; full = md_path.read_text()
    tail = ("\n## Verdict" + full.split("\n## Verdict", 1)[1]) if "\n## Verdict" in full else ""
    md = full.split("\n## Results")[0].rstrip() + "\n\n## Results\n"
    _md = PA._md
    m = o[o.row == "mae"]
    # 1. look-ahead: old vs new, flat and mult, by kind and window
    t = m[(m.asof_week == "all") & m.variant.isin(["flat", "mult"])].pivot_table(index=["kind", "variant", "window"], columns="rows", values=["n", "mae", "within20", "bias"]).reset_index()
    t.columns = [a if not b else f"{a}_{b}" for a, b in t.columns]
    t["mae_change"] = t.mae_new - t.mae_old
    for c in ("n_old", "n_new"):
        t[c] = t[c].astype(int)
    md += "\n### 1. Look-ahead: old rows (ACT only) against corrected rows (ACT or INA), season-total error\n\n"
    md += "Every projected player, as of weeks 1, 5, 9, 13 pooled. `mult` for pass is today's pooled logit (recorded, never adopted).\n\n"
    md += _md(t[["kind", "variant", "window", "n_old", "n_new", "mae_old", "mae_new", "mae_change", "bias_old", "bias_new", "within20_old", "within20_new"]]) + "\n"
    ad = o[o.row == "added"][["kind", "window", "n", "value", "dropped"]].rename(columns={"n": "rows_added", "value": "share_of_rows", "dropped": "old_rows_gone"})
    ad["rows_added"] = ad.rows_added.astype(int); ad["old_rows_gone"] = ad.old_rows_gone.astype(int)
    md += "\nRows added by the fix (in the corrected rows, not in the old; `old_rows_gone`: old rows no longer present, e.g. a team's starting QB by dropbacks changes when the inactive starter comes back into the roster):\n\n" + _md(ad) + "\n"
    ma = o[o.row.isin(["mae_added", "mae_kept"])][["kind", "variant", "window", "row", "n", "mae", "bias", "games_miss"]].copy(); ma["n"] = ma.n.astype(int)
    ma["row"] = ma.row.str.replace("mae_", "")
    md += "\nOn the corrected rows, split into the rows the fix added and the rest:\n\n" + _md(ma.sort_values(["kind", "window", "variant", "row"])) + "\n"
    pv = o[o.row == "prevalence"].pivot_table(index="band", columns=["rows", "window"], values="value").reset_index()
    pv.columns = ["feature"] + [f"{a}_{b}" for a, b in pv.columns[1:]]
    md += "\nFeature means (all kinds) by window, old and corrected rows:\n\n" + _md(pv) + "\n"
    # rule for rec / rush on the corrected rows, and the old for reference
    V = pd.DataFrame(rule(o, "old", "rec", ["mult"]) + rule(o, "new", "rec", ["mult"]) + rule(o, "old", "rush", ["mult"]) + rule(o, "new", "rush", ["mult"]))
    md += "\n### Today's rule for the adopted `mult` (rec, rush), old and corrected rows\n\n" + _md(V) + "\n"
    wk = m[(m.asof_week != "all") & m.variant.isin(["flat", "mult"]) & m.kind.isin(["rec", "rush"])].pivot_table(index=["kind", "window", "asof_week"], columns=["variant", "rows"], values="mae").reset_index()
    wk.columns = ["kind", "window", "asof_week"] + [f"{a}_{b}" for a, b in wk.columns[3:]]
    wk["mult-flat_old"] = wk.mult_old - wk.flat_old; wk["mult-flat_new"] = wk.mult_new - wk.flat_new
    wk["asof_week"] = wk.asof_week.astype(int); wk = wk.sort_values(["kind", "window", "asof_week"])
    md += "\nPer as-of week (rec, rush):\n\n" + _md(wk[["kind", "window", "asof_week", "flat_old", "flat_new", "mult_old", "mult_new", "mult-flat_old", "mult-flat_new"]]) + "\n"
    fc = o[(o.row == "fit") & (o.rows == "new")][["kind", "variant", "constants", "mae"]].rename(columns={"mae": "fit_mae_2016-18"})
    md += "\nConstants fitted on 2016-18 (identical on old and corrected rows; `pmult` / `pshare` use the passer logit):\n\n" + _md(fc) + "\n"
    # 2. passers
    P = pd.DataFrame(rule(o, "new", "pass", ["pmult", "pshare", "mult"]))
    P["adopted"] = ""
    ok = P[(P.passes == "yes") & P.variant.isin(["pmult", "pshare"])]
    if len(ok):
        P.loc[(ok["gain_2019-22"] + ok["gain_2023-25"]).idxmax(), "adopted"] = "ADOPT"
    md += "\n### 2. Passers: the pre-registered rule on the corrected rows (`mult` = today's pooled logit, for reference)\n\n" + _md(P) + "\n"
    tp = m[(m.kind == "pass") & (m.rows == "new") & (m.asof_week == "all")][["variant", "window", "n", "mae", "pace_mae", "bias", "within10", "within20", "within20_top", "games_miss"]].copy()
    tp["n"] = tp.n.astype(int)
    md += "\nPassing season-total error on the corrected rows:\n\n" + _md(tp.sort_values(["window", "variant"])) + "\n"
    pw = m[(m.kind == "pass") & (m.rows == "new") & (m.asof_week != "all")].pivot_table(index=["window", "asof_week"], columns="variant", values="mae").reset_index()
    pw["asof_week"] = pw.asof_week.astype(int); pw = pw.sort_values(["window", "asof_week"])
    for v in ("pmult", "pshare", "mult"):
        pw[f"{v}-flat"] = pw[v] - pw.flat
    md += "\nPassing per as-of week (corrected rows):\n\n" + _md(pw[["window", "asof_week", "flat", "pmult", "pshare", "pmult-flat", "pshare-flat", "mult-flat"]]) + "\n"
    cf = o[(o.row == "coef")].pivot_table(index="band", columns="variant", values="value", sort=False).reset_index().rename(columns={"band": "feature"})
    md += "\nLogit coefficients (fitted on 2016-18): the pooled model (today's) and the passer model:\n\n" + _md(cf) + "\n"
    # 3. calibration
    c = o[(o.row == "calib") & (o.band == "all")][["variant", "kind", "window", "n", "pred", "real", "logloss", "games_miss"]].copy(); c["n"] = c.n.astype(int)
    md += "\n### 3. Calibration of p on the corrected rows (weighted by team games left; 2016-18 out of season)\n\nOverall by kind:\n\n" + _md(c.sort_values(["variant", "kind", "window"])) + "\n"
    cb = o[(o.row == "calib") & (o.band != "all")].copy()
    cw = cb.pivot_table(index=["variant", "kind", "band"], columns="window", values=["n", "pred", "real"], sort=False)
    cw.columns = [f"{a}_{b}" for a, b in cw.columns]; cw = cw.reset_index()
    order_b = {b: i for i, b in enumerate(["<0.3", "0.3-0.5", "0.5-0.6", "0.6-0.7", "0.7-0.8", "0.8-0.9", "0.9-1"])}
    cw = cw.sort_values(["variant", "kind", "band"], key=lambda s: s.map(order_b) if s.name == "band" else s)
    cols = ["variant", "kind", "band"] + [f"{a}_{w}" for w in ["2016-18", "2019-22", "2023-25"] for a in ("n", "pred", "real") if f"{a}_{w}" in cw.columns]
    cw = cw[cols]
    for cc in cw.columns:
        if cc.startswith("n_"):
            cw[cc] = cw[cc].fillna(0).astype(int)
    md += "\nBy band:\n\n" + _md(cw) + "\n"
    md_path.write_text(md.rstrip() + "\n" + tail)
    return V, P


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "build":
        build(int(a[a.index("--jobs") + 1]) if "--jobs" in a else 1)
    elif a and a[0] == "study":
        study()
    elif a and a[0] == "report":
        V, P = report(); print(V.to_string(index=False)); print(P.to_string(index=False))
    else:
        print(__doc__)
