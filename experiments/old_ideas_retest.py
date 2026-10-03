"""Old ideas retested on the honest backtest (3 Oct 2026, Matt: test old ideas again "from everything we have learned").

Pre-registration, the inventory of every idea not adopted and the results: reports/old_ideas_retest.md (the
pre-registration was committed before any rerun). Thirteen ideas rejected before the 1-2 Oct fixes, each rerun exactly as
first specified on main's backtest (fixed starters, ids, venues and wind; forecast pricing; no referee input):

  V1  drop qb_out from the points equation            (round 3 re-check, experiments/situational_game.py)
  V2  drop cold from the totals equation              (round 3 re-check)
  V3  drop dome from the totals equation              (round 3 re-check)
  V4  drop dome from the points equation              (round 3 re-check)
  V5  qb_form (k 100) in the points equation          (experiments/qb_form.py)
  V6  temperature bands on the day-before GFS run, on top of the total, K 50   (experiments/weather_forecast_retest.py)
  V7  one band, rain chance 50+ or below 32 F, on top of the total, K 50       (experiments/weather_forecast_retest.py)
  V8  opponent defenders' value out                   (experiments/injury_retest.py D1)
  V9  usual snaps out, last 4 games played if he played in the team's last 4  (experiments/usual_snaps.py L4_G4)
  V10 wind learned from the forecast                  (experiments/forecast_weather_inputs.py W)
  V11 home edge x visitor's travel miles              (experiments/home_field.py)
  V12 home edge x visitor's time-zone change          (experiments/home_field.py)
  V13 neutral sites: home edge set to zero            (experiments/home_field.py)

Every run (base and variants) is the live walk-forward 2015-2025 (model.walk_forward) with its boosted trees fitted fresh
on this machine: data/processed/trees_cache.parquet is never written and is read only for the reference base row (base and variants like for like). Scored
through nflmodel.study_gate on 2015-18 / 2019-22 / 2023-25 (regular season): team points miss (points ideas) or total
miss (totals ideas); the spread flag (4+), totals flag (55%+ under) and wind under (10+ mph), weeks 1-17; the calibrated
home win chance's log loss (points ideas). 50 within-season shuffles (seed 20261003) for each variant passing parts 1-2.

V8 and V9 read the league injury files, weekly rosters and snap counts 2012-2025 (python -m nflmodel.pull --seasons
2012-2025 --only injuries,snap_counts,rosters,players). Scratch files go to OIR_SCRATCH (default: the system temp folder).

Rule part 5 (passers rerun together) had nothing to combine: no variant passed parts 1-2. V9 got an informational
placebo after the results (--informational V9).

    python -m experiments.old_ideas_retest --stage inputs|base|real|placebo|report [--jobs 10] [--names V1,..] [--informational V9]
"""
from __future__ import annotations
import argparse, json, os, pickle, sys, tempfile, time
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
SCR = Path(os.environ.get("OIR_SCRATCH", Path(tempfile.gettempdir()) / "old_ideas_retest")); SCR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("SG_SCRATCH", str(SCR / "sg")); os.environ.setdefault("US_SCRATCH", str(SCR / "us"))
from nflmodel import backtest as B, model as M, picks as P, study_gate as G
from nflmodel.features import OUT

REP = ROOT / "reports"
WIN = {"2015-18": (2015, 2018), "2019-22": (2019, 2022), "2023-25": (2023, 2025)}
SEED, DRAWS, K = 20261003, 50, 50.0
GAMES = pd.read_parquet(OUT / "games.parquet")
BASE_FEATS, BASE_TOTAL = list(M.FEATS), list(M.TOTAL_FEATS)
_PREP = M.prep
COLD_EDGES = [-99, 32, 45, 999]
VARIANTS = {   # name -> (label, equation, yardstick)
    "V1": ("Drop QB out (points)", "points", "team"), "V2": ("Drop cold (total)", "total", "total"),
    "V3": ("Drop dome (total)", "total", "total"), "V4": ("Drop dome (points)", "points", "team"),
    "V5": ("QB form in the points equation", "points", "team"), "V6": ("Temperature bands, day-before run", "total", "total"),
    "V7": ("Wet or cold band", "total", "total"), "V8": ("Opponent defenders' value out", "points", "team"),
    "V9": ("Usual snaps out (L4_G4)", "points", "team"), "V10": ("Wind learned from the forecast", "points", "team"),
    "V11": ("Home edge x visitor's travel miles", "points", "team"), "V12": ("Home edge x visitor's time-zone change", "points", "team"),
    "V13": ("Neutral sites: home edge zero", "points", "team")}
BANDS = ("V6", "V7")


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


# ------------------------------------------------------------------------------------------------------- the inputs
def stage_inputs():
    """Snapshot the model's rows and build every variant's input once (scratch)."""
    f = M.with_trends(pd.read_parquet(OUT / "features_asof.parquet")); f.to_parquet(SCR / "f0.parquet", index=False)
    # V8: injury_retest's build (cached in scratch, never in data/processed)
    from experiments import injury_retest as IR
    IR.CACHE = SCR / "injury_retest_inputs.parquet"
    X = IR.build()
    pi = pd.read_parquet(OUT / "player_injury.parquet").merge(X, on=["game_id", "team"])
    tr = pd.read_parquet(OUT / "trends_asof.parquet").merge(X, on=["game_id", "team"])
    chk = {"V8 rebuilt skill value out = live (share within 0.001)": float(((pi.skill_out_value - pi.base_skill).abs() < 1e-3).mean()),
           "V8 rebuilt offensive snaps out = live (share within 0.01)": float(((tr.off_snap_out - tr.base_off).abs() < 1e-2).mean()),
           "V8 team-games with a defender out valued (2018-25)": int((X[X.season >= 2018].def_value_out != 0).sum())}
    # V9: usual_snaps' build
    from experiments import usual_snaps as US
    US.SG.GAMES = GAMES
    V, _ = US.build_inputs()
    # as usual_snaps: only team-games the live trends table carries (playoff rows stay 0, as with_trends leaves them)
    V = V.merge(pd.read_parquet(OUT / "trends_asof.parquet", columns=["game_id", "team"]), on=["game_id", "team"], how="inner")
    V.to_parquet(SCR / "usual_snaps.parquet", index=False)
    t = pd.read_parquet(OUT / "trends_asof.parquet")[["game_id", "team", "off_snap_out", "def_snap_out"]].merge(V, on=["game_id", "team"])
    for c in ("off_snap_out", "def_snap_out"):
        chk[f"V9 'current' {c} = live (share within 1e-6)"] = float(((t[c].fillna(0) - t[f"{c}__current"].fillna(0)).abs() < 1e-6).mean())
    chk["V9 team-games where L4_G4 differs from live"] = int(((t["off_snap_out__L4_G4"].fillna(0) - t.off_snap_out.fillna(0)).abs().gt(1e-9) |
                                                             (t["def_snap_out__L4_G4"].fillna(0) - t.def_snap_out.fillna(0)).abs().gt(1e-9)).sum())
    # every scored season present (a builder skips a missing raw file without a word; fillna would then hide it)
    ok = ((t.off_snap_out.fillna(0) - t["off_snap_out__current"].fillna(0)).abs() < 1e-6) & ((t.def_snap_out.fillna(0) - t["def_snap_out__current"].fillna(0)).abs() < 1e-6)
    by = ok.groupby(t.season).mean(); n8 = X[X.def_value_out != 0].groupby("season").size()
    for s in range(2015, 2026):
        assert by.get(s, 0) >= 0.99, f"V9: season {s} reproduces the live snaps out on {by.get(s, 0):.3f} of team-games"
        assert s < 2018 or n8.get(s, 0) > 300, f"V8: season {s} has {n8.get(s, 0)} team-games with a defender out valued"
    chk["V9 worst season reproducing the live snaps out, 2015-25"] = float(by.loc[2015:2025].min())
    chk["V8 fewest team-games with a defender out valued in a season, 2018-25"] = int(n8.loc[2018:2025].min())
    # V11-V13: home_field's game facts on today's venues
    g = GAMES.copy(); g["gd"] = pd.to_datetime(g.gameday)
    from experiments import situational_feats as SF
    hg = g[(g.game_type == "REG") & (g.location == "Home")]
    hs = hg.groupby(["home_team", "season"]).stadium_id.agg(lambda s: s.value_counts().index[0]).to_dict()
    def st_of(tm, s):
        v = hs.get((tm, s))
        return v if v is not None else next((hs.get((tm, s - k)) for k in range(1, 4) if hs.get((tm, s - k)) is not None), None)
    nn = (g.location != "Neutral").astype(float).values
    miles, tz = [], []
    for vt, s, st, d in zip(g.away_team, g.season, g.stadium_id, g.gd):
        a, b = SF.STADIUMS.get(st_of(vt, s)), SF.STADIUMS.get(st)
        if a is None or b is None:
            miles.append(0.0); tz.append(0.0); continue
        miles.append(SF._hav(a[:2], b[:2]) / 1000.0); tz.append(abs(SF._tz(st, d) - SF._tz(st_of(vt, s), d)))
    gf = pd.DataFrame({"game_id": g.game_id, "season": g.season, "vis_miles": np.array(miles) * nn, "vis_tz": np.array(tz) * nn, "neutral_g": 1.0 - nn})
    gf.to_parquet(SCR / "game_flags.parquet", index=False)
    chk["V11-V13 neutral games 2015-25"] = int(gf[gf.season.between(2015, 2025)].neutral_g.sum())
    chk["V11-V13 games with no stadium coordinates"] = int(sum(1 for st in g.stadium_id if SF.STADIUMS.get(st) is None))
    (SCR / "input_checks.json").write_text(json.dumps(chk, indent=1)); log(json.dumps(chk, indent=1))


_IN: dict = {}


def inputs():
    if not _IN:
        _IN["f0"] = pd.read_parquet(SCR / "f0.parquet")
        _IN["X"] = pd.read_parquet(SCR / "injury_retest_inputs.parquet") if (SCR / "injury_retest_inputs.parquet").exists() else None
        _IN["US"] = pd.read_parquet(SCR / "usual_snaps.parquet") if (SCR / "usual_snaps.parquet").exists() else None
        _IN["gf"] = pd.read_parquet(SCR / "game_flags.parquet").set_index("game_id") if (SCR / "game_flags.parquet").exists() else None
        _IN["wind"] = pd.Series(M._wind_readings(), dtype=float)
    return _IN


def _shuffle_games(vals: pd.Series, rng) -> pd.Series:
    """A game-level value shuffled among the games of each season that carry it."""
    v = vals.dropna(); seas = v.index.str[:4].astype(int).values
    return pd.Series(G.shuffle_within_season(v.values, seas, rng), index=v.index)


def _signed(f, gv: pd.Series) -> np.ndarray:
    return gv.reindex(f.game_id.values).fillna(0.0).values * np.where(f.home.values == 1, 1.0, -1.0)


def variant(v: str, rng=None):
    """(rows, points inputs, totals inputs, post-prep hook) for variant v; rng shuffles its values (the placebo)."""
    I = inputs(); f = I["f0"].copy(); feats, tot, hook = list(BASE_FEATS), list(BASE_TOTAL), None
    if v == "V1":
        feats.remove("qb_out")
    elif v == "V2":
        tot.remove("cold")
    elif v == "V3":
        tot.remove("dome")
    elif v == "V4":
        feats.remove("dome")
    elif v == "V5":
        if rng is None:
            feats.append("qb_form")
        else:   # the shuffled copy feeds the points equations only; qb_form itself stays for the totals' qb_form_sum
            feats.append("qb_form_pl"); seed = int(rng.integers(1 << 31))
            def hook(x, seed=seed):
                x["qb_form_pl"] = G.shuffle_within_season(x.qb_form.values, x.season.values, np.random.default_rng(seed)); return x
    elif v == "V8":
        X = I["X"].copy()
        if rng is not None:
            X["def_value_out"] = G.shuffle_within_season(X.def_value_out.values, X.season.values, rng)
        x = X.set_index(["game_id", "team"]).def_value_out
        f["opp_def_value_out"] = x.reindex(pd.MultiIndex.from_arrays([f.game_id, f.opp])).fillna(0.0).values; feats.append("opp_def_value_out")
    elif v == "V9":
        U = f[["game_id", "team", "season", "off_snap_out", "def_snap_out"]].merge(
            I["US"][["game_id", "team", "off_snap_out__L4_G4", "def_snap_out__L4_G4"]], on=["game_id", "team"], how="left")
        assert len(U) == len(f)
        cur_o, cur_d = U.off_snap_out.fillna(0.0).values, U.def_snap_out.fillna(0.0).values
        new_o = U["off_snap_out__L4_G4"].fillna(U.off_snap_out).fillna(0.0).values; new_d = U["def_snap_out__L4_G4"].fillna(U.def_snap_out).fillna(0.0).values
        if rng is not None:   # usual_snaps' placebo: the variant's change landed on other team-games of the season
            seas = U.season.values; perm = np.empty(len(seas), int)
            for s in np.unique(seas):
                ix = np.flatnonzero(seas == s); perm[ix] = rng.permutation(ix)
            new_o = np.clip(cur_o + (new_o - cur_o)[perm], 0, None); new_d = np.clip(cur_d + (new_d - cur_d)[perm], 0, None)
        f["off_snap_out"] = new_o
        d = pd.Series(new_d, index=pd.MultiIndex.from_arrays([f.game_id, f.team]))
        f["opp_def_snap_out"] = d.reindex(pd.MultiIndex.from_arrays([f.game_id, f.opp])).fillna(0.0).values
    elif v == "V10":
        w = I["wind"]
        played = f.pf.notna() & f.game_id.isin(w.index)
        if rng is not None:
            ids = f.game_id[played].unique(); w = _shuffle_games(w.reindex(ids), rng)
        f.loc[played, "wind"] = f.game_id[played].map(w).values
    elif v in ("V11", "V12"):
        c = "vis_miles" if v == "V11" else "vis_tz"; gv = I["gf"][c]
        if rng is not None:
            gv = _shuffle_games(gv, rng)
        f["hf_" + c] = _signed(f, gv); feats.append("hf_" + c)
    elif v == "V13":
        ng = I["gf"].neutral_g
        if rng is not None:
            ng = _shuffle_games(ng, rng)
        f["home_nn"] = f.home.values * (1 - ng.reindex(f.game_id.values).fillna(0.0).values)
        feats = ["home_nn" if c == "home" else c for c in feats]
    return f, feats, tot, hook


def setup(read_fresh=True):
    """Fresh trees on this machine, never the stored fits; nothing written to data/processed."""
    M.TREES_CACHE = SCR / ("trees_fresh.parquet" if read_fresh else "trees_none.parquet")
    M._TC.update({"df": None, "used": set(), "new": []})
    M.save_trees_cache = lambda: None
    from threadpoolctl import threadpool_limits
    threadpool_limits(limits=1)


def run(f, feats, tot, hook=None):
    M.FEATS, M.TOTAL_FEATS = list(feats), list(tot); M.DIST.clear()
    if hook is not None:
        M.prep = lambda x, h=hook: h(_PREP(x))
    try:
        p = M.walk_forward(f, range(2015, 2026), M.RIDGE)
    finally:
        M.FEATS, M.TOTAL_FEATS, M.prep = list(BASE_FEATS), list(BASE_TOTAL), _PREP
    M._TC["new"] = []   # a variant's own fits are dropped
    return p, {k: np.asarray(v["tres"], dtype=float) for k, v in M.DIST.items()}


# ------------------------------------------------------------------------------------------------------- scoring
def logloss_cal(p: pd.DataFrame) -> dict:
    cal = P.home_calibrations(p, GAMES); g = GAMES.set_index("game_id")
    d = p[(p.game_type == "REG") & p.season.between(2015, 2025)].copy()
    d["res"] = d.game_id.map(g.home_score) - d.game_id.map(g.away_score); d = d[d.res.notna() & (d.res != 0)]
    q = np.array([P.home_cal_p(cal[int(s)], ph) for s, ph in zip(d.season, d.p_home)]); y = (d.res > 0).values
    ll = -(y * np.log(q) + (1 - y) * np.log(1 - q))
    return {w: float(ll[d.season.between(lo, hi).values].mean()) for w, (lo, hi) in WIN.items()}


def score(p: pd.DataFrame, cal=True) -> dict:
    d = B.join(p, GAMES); d = d[(d.game_type == "REG") & d.season.between(2015, 2025)]
    ll = logloss_cal(p) if cal else {}
    out = {}
    for w, (lo, hi) in WIN.items():
        x = d[d.season.between(lo, hi)]
        out[w] = {"team": float(np.r_[x.home_err.abs(), x.away_err.abs()].mean()), "total": float(x.total_err.abs().mean()),
                  "margin": float(x.margin_err.abs().mean()), "logloss": ll.get(w, np.nan),
                  "spread": P.record(x, P.rule_mask(x, P.SPREAD_EDGE)),
                  "totals": P.record(x, P.rule_mask(x, P.TOTAL_SHADOW["prob"], "under_prob"), "under_prob"),
                  "wind": P.record(x, P.rule_mask(x, P.WIND_UNDER["mph"], "wind_under"), "wind_under")}
    return out


def yard(v, sc):
    return {w: sc[w][VARIANTS[v][2]] for w in WIN}


# ---------------------------------------------------------------------------------- band points on top of the total
_FH: dict = {}


def readings():
    if not _FH:
        from nflmodel import wind_live as WL   # the stored forecasts as the live readers see them: no games abroad, none under a roof
        h = WL._history(); h = h[~h.game_id.isin(WL._roofed())].set_index("game_id")
        _FH["temp_d1"] = h.gfs_temp_d1.astype(float)
        _FH["pop"] = h.gfs_pop_d0.fillna(h.gfs_pop_d1).astype(float); _FH["temp"] = h.gfs_temp_d0.fillna(h.gfs_temp_d1).astype(float)
    return _FH


def band_labels(v, gid: pd.Series, rd: dict) -> pd.Series:
    if v == "V6":
        t = gid.map(rd["temp_d1"])
        return pd.cut(t, COLD_EDGES, right=False).astype(str).where(t.notna())
    pop, t = gid.map(rd["pop"]), gid.map(rd["temp"])
    return ((pop >= 50) | (t < 32)).astype(str).where(pop.notna() & t.notna())


def band_pred(v, p, dist, rng=None) -> pd.DataFrame:
    """weather_forecast_retest's band points: each season's band amounts from the earlier seasons' regular-season forecast
    games (band mean miss minus the pool's mean miss, shrunk by K), added to the total; team points +half each; the over
    chance re-priced with the fit's own training misses."""
    rd = readings()
    if rng is not None:   # the readings shuffled within season among the games that carry them (all columns together)
        cols = ["temp_d1"] if v == "V6" else ["pop", "temp"]
        fr = pd.DataFrame({c: rd[c] for c in cols}).dropna(); seas = fr.index.str[:4].astype(int).values
        perm = np.arange(len(fr))
        for s in np.unique(seas):
            ix = np.flatnonzero(seas == s); perm[ix] = ix[rng.permutation(len(ix))]
        rd = {c: pd.Series(fr[c].values[perm], index=fr.index) for c in cols}
    d = B.join(p, GAMES)
    pool = (d.game_type == "REG") & d.total_line.notna() & d.season.between(2015, 2025)
    lab = band_labels(v, d.game_id, rd); r = d.total - d.model_total
    a = pd.Series(0.0, index=d.index)
    for s in range(2016, 2026):
        tr = pool & lab.notna() & (d.season < s); te = lab.notna() & (d.season == s) & pool
        if tr.any() and te.any():
            base = r[tr].mean(); e = r[tr].groupby(lab[tr]).agg(["sum", "size"]); e = (e["sum"] - base * e["size"]) / (e["size"] + K)
            te_ = te.values
            a[te_] = lab[te_].map(e).astype(float).fillna(0.0).values
    amt = pd.Series(a.values, index=d.game_id.values)
    q = p.copy(); add = q.game_id.map(amt).fillna(0.0).values
    q["model_total"] = q.model_total + add; q["home_exp"] = q.home_exp + add / 2; q["away_exp"] = q.away_exp + add / 2
    po = q.p_over_emp.values.copy()
    for i in np.flatnonzero(add != 0):
        if pd.isna(q.total_line.iat[i]):
            continue
        tres = dist[(int(q.season.iat[i]), int(q.week.iat[i]))]; x = q.model_total.iat[i] + tres; tl = q.total_line.iat[i]
        po[i] = float(np.mean(x > tl) / max(1e-9, np.mean(x != tl)))
    q["p_over_emp"] = po; q["band_pts"] = add
    return q


# ------------------------------------------------------------------------------------------------------- stages
def stage_base():
    # the base with fresh fits, kept in scratch so the totals-only variants reuse the base's trees
    setup(read_fresh=False); M.FEATS, M.TOTAL_FEATS = list(BASE_FEATS), list(BASE_TOTAL); M.DIST.clear()
    pb = M.walk_forward(pd.read_parquet(SCR / "f0.parquet"), range(2015, 2026), M.RIDGE); db = {k: np.asarray(v["tres"], dtype=float) for k, v in M.DIST.items()}
    pd.concat(M._TC["new"], ignore_index=True).drop_duplicates(["key", "game_id", "team"]).to_parquet(SCR / "trees_fresh.parquet", index=False)
    pb.to_parquet(SCR / "pred_base.parquet", index=False); pickle.dump(db, open(SCR / "dist_base.pkl", "wb"))
    # reference: the base on the stored (GitHub) fits, read only
    M.TREES_CACHE = OUT / "trees_cache.parquet"; M._TC.update({"df": None, "used": set(), "new": []})
    with M.trees_cache_read_only():
        M.DIST.clear(); ps = M.walk_forward(pd.read_parquet(SCR / "f0.parquet"), range(2015, 2026), M.RIDGE)
    ps.to_parquet(SCR / "pred_stored.parquet", index=False)
    log("base done", {w: round(s["team"], 4) for w, s in score(pb).items()})


def _job(args):
    v, seed = args
    setup(read_fresh=True)
    if v in BANDS:
        pb = pd.read_parquet(SCR / "pred_base.parquet"); db = pickle.load(open(SCR / "dist_base.pkl", "rb"))
        q = band_pred(v, pb, db, None if seed is None else np.random.default_rng(seed))
        return v, seed, score(q, cal=False), (q if seed is None else None)
    rng = None if seed is None else np.random.default_rng(seed)
    f, feats, tot, hook = variant(v, rng)
    p, _ = run(f, feats, tot, hook)
    return v, seed, score(p, cal=(VARIANTS[v][1] == "points") and seed is None), (p if seed is None else None)


def stage_real(jobs, names):
    from concurrent.futures import ProcessPoolExecutor
    done = pickle.load(open(SCR / "real.pkl", "rb")) if (SCR / "real.pkl").exists() else {}
    todo = [v for v in names if v not in done]
    with ProcessPoolExecutor(jobs) as ex:
        for v, _, sc, p in ex.map(_job, [(v, None) for v in todo]):
            done[v] = sc; p.to_parquet(SCR / f"pred_{v}.parquet", index=False); pickle.dump(done, open(SCR / "real.pkl", "wb"))
            log(v, {w: round(sc[w][VARIANTS[v][2]], 4) for w in WIN})


def gate_rows(v, base, new, placebo=None):
    cal = {w: (base[w]["logloss"], new[w]["logloss"]) for w in WIN} if VARIANTS[v][1] == "points" else None
    return G.gate({w: (base[w][VARIANTS[v][2]], new[w][VARIANTS[v][2]]) for w in WIN},
                  {w: {"spread flag": (base[w]["spread"], new[w]["spread"]), "totals flag": (base[w]["totals"], new[w]["totals"]),
                       "wind under": (base[w]["wind"], new[w]["wind"])} for w in WIN}, placebo, cal)


def p12(rows) -> bool:
    return all(ok for what, ok, _ in rows if not what.startswith("beats"))


def stage_placebo(jobs, names, extra=()):
    from concurrent.futures import ProcessPoolExecutor
    base = score(pd.read_parquet(SCR / "pred_base.parquet")); real = pickle.load(open(SCR / "real.pkl", "rb"))
    pl = pickle.load(open(SCR / "placebo.pkl", "rb")) if (SCR / "placebo.pkl").exists() else {}
    todo = [v for v in names if v in real and v not in pl and (p12(gate_rows(v, base, real[v])) or v in extra)]
    for v in todo:
        if v in ("V1", "V2", "V3", "V4"):
            continue   # removals: decided by parts 1 and 2 (pre-registration)
        seeds = [SEED * 100 + int(v[1:]) * 1000 + i for i in range(DRAWS)]
        part = SCR / f"placebo_{v}_partial.pkl"   # each draw saved as it lands, so a stopped run resumes
        got = pickle.load(open(part, "rb")) if part.exists() else {}
        with ProcessPoolExecutor(jobs) as ex:
            for i, (_, s, sc, _) in enumerate(ex.map(_job, [(v, s) for s in seeds if s not in got])):
                got[s] = {w: base[w][VARIANTS[v][2]] - sc[w][VARIANTS[v][2]] for w in WIN}; pickle.dump(got, open(part, "wb"))
                log(v, "placebo", len(got), {w: round(got[s][w], 4) for w in WIN})
        pl[v] = {w: [got[s][w] for s in seeds] for w in WIN}; pickle.dump(pl, open(SCR / "placebo.pkl", "wb"))


def rec(t):
    return "%d-%d" % t


def stage_report():
    base = score(pd.read_parquet(SCR / "pred_base.parquet")); stored = score(pd.read_parquet(SCR / "pred_stored.parquet"))
    real = pickle.load(open(SCR / "real.pkl", "rb"))
    pl = pickle.load(open(SCR / "placebo.pkl", "rb")) if (SCR / "placebo.pkl").exists() else {}
    chk = json.loads((SCR / "input_checks.json").read_text())
    rows = [{"variant": "base (stored fits, reference)", "window": w, **{k: (rec(v) if isinstance(v, tuple) else round(v, 5)) for k, v in stored[w].items()}} for w in WIN]
    rows += [{"variant": "base", "window": w, **{k: (rec(v) if isinstance(v, tuple) else round(v, 5)) for k, v in base[w].items()}} for w in WIN]
    for v in VARIANTS:
        if v in real:
            rows += [{"variant": v, "label": VARIANTS[v][0], "window": w, **{k: (rec(x) if isinstance(x, tuple) else round(x, 5)) for k, x in real[v][w].items()}} for w in WIN]
    df = pd.DataFrame(rows); df.to_csv(REP / "old_ideas_retest.csv", index=False)
    gates = {v: gate_rows(v, base, real[v], pl.get(v)) for v in VARIANTS if v in real}
    md = REP / "old_ideas_retest.md"; head = md.read_text(encoding="utf-8").split("\n## Results")[0]
    L = [head.rstrip(), "", "## Results", "", "Input checks: " + "; ".join(f"{k}: {v:.4f}" if isinstance(v, float) else f"{k}: {v}" for k, v in chk.items()) + ".", "",
         "Every run is the live walk-forward 2015-2025 with fresh trees; regular season scored; flags weeks 1-17 at the close; "
         "log loss = the calibrated home win chance.", "",
         "| Variant | Window | Team miss | Total miss | Margin miss | Log loss | Spread flag | Totals flag | Wind under |", "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        L.append(f"| {r['variant']} | {r['window']} | {r['team']:.4f} | {r['total']:.4f} | {r['margin']:.4f} | {r['logloss']:.5f} | {r['spread']} | {r['totals']} | {r['wind']} |")
    L += ["", "| Variant | Idea | Parts 1-2 | Placebo | Gate |", "|---|---|---|---|---|"]
    for v, g_ in gates.items():
        bt = [d for c, o, d in g_ if c.startswith("beats")]
        pv = "removal: parts 1-2 decide" if v in ("V1", "V2", "V3", "V4") else (
            ("; ".join(bt) + ("" if p12(g_) else " (informational, added after results)")) if v in pl else "not run (fails 1 or 2)")
        ok = p12(g_) and (v in ("V1", "V2", "V3", "V4") or (v in pl and G.passes(g_)))
        L.append(f"| {v} | {VARIANTS[v][0]} | {'pass' if p12(g_) else 'fail: ' + ', '.join(c for c, o, _ in g_ if not o and not c.startswith('beats'))} | {pv} | {'PASS' if ok else 'FAIL'} |")
    for v, g_ in gates.items():
        L += ["", f"### Gate, {v}: {VARIANTS[v][0]} ({'team points' if VARIANTS[v][2] == 'team' else 'total'} miss)", "", G.markdown(g_)]
    md.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L[len(head.splitlines()):]))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--stage", required=True); ap.add_argument("--jobs", type=int, default=10)
    ap.add_argument("--names", default=",".join(VARIANTS))
    ap.add_argument("--informational", default="", help="variants given a placebo though they fail parts 1-2 (labelled in the report)")
    a = ap.parse_args(); names = a.names.split(",")
    {"inputs": stage_inputs, "base": stage_base, "report": stage_report}.get(a.stage, lambda: None)()
    if a.stage == "real":
        stage_real(a.jobs, names)
    elif a.stage == "placebo":
        stage_placebo(a.jobs, names, [x for x in a.informational.split(",") if x])
