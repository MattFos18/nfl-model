"""Team- and stadium-specific home field, under the round-3 rule (reports/round3_rule.md), 30 Sep 2026.

The live model carries one home-field input (`home`, 1 on the home team's row) fit by the ridge on every played game
since 2013, plus `neutral` (1 on both rows of a neutral-site game, so it cancels out of the margin). This asks whether
a home edge that differs by team, by stadium, by opponent or by the stage of the season beats that one number.

Engine: experiments/situational_game.py's `lean_walk_forward` / `finish` / `score` exactly (the live walk-forward,
seven-model blend, trees refit fresh on this machine, weekly refit from 2013, graded at the closing line, windows
2015-18 / 2019-22 / 2023-25). The one exception is angle 5 (partial pooling of 32+ team home dummies inside the ridges),
which needs a different penalty on the dummies than on the live inputs: `walk_forward_pp` is lean_walk_forward with the
ridges' scaler replaced by one that leaves the live inputs exactly as before and puts the dummies on their own penalty;
with no dummies it reproduces lean_walk_forward (checked in stage base).

Every idea is a *signed* home-edge column: +v on the home team's row, -v on the visitor's row, 0 at a neutral site
(so its fitted weight is half the margin effect in points per team). Every value is as of before the season (team
histories use prior seasons only) or a fixed fact of the game (stadium, week, division), never a market number.

Residuals ("after the model") are the base walk-forward's own margin miss for 2014-2026 regular-season games (actual
home-minus-away margin minus model_spread), and before 2014 the plain as-of scoring rating of experiments/
situational_feats.py (the same source round 3 used).

    HF_SCRATCH=/path python -m experiments.home_field --stage base|build|facts|real|placebo|report [--jobs 4]
Writes reports/home_field.csv and reports/home_field.md; everything else goes to HF_SCRATCH.
"""
from __future__ import annotations
import os, sys, time, json, argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
SCR = Path(os.environ.get("HF_SCRATCH", "/tmp/home_field")); SCR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("SG_SCRATCH", str(SCR / "sg"))   # the round-3 module makes its scratch dir on import; keep it in ours
import numpy as np, pandas as pd
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.ensemble import HistGradientBoostingRegressor
from nflmodel import model as M
from nflmodel.model import OUT
from experiments import situational_game as SG
from experiments.situational_game import lean_walk_forward, finish, score, flat, game_frame, _p_home, WINDOWS, GAMES, BASE_FEATS, BASE_TOTAL
from experiments import situational_feats as SF

ROOT = Path(__file__).resolve().parent.parent
REP = ROOT / "reports"
M.save_trees_cache = lambda: None   # never write the live trees' cache from here (lean_walk_forward never reads it)
N_PLACEBO, STOP_AT = 50, 6
LAST_SEASON = 2025                     # scored seasons end here; 2026 weeks played so far feed only the "now" readings


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


# ------------------------------------------------------------------------------------------------ partial pooling engine
class PPRidge:
    """StandardScaler + Ridge(alpha) on the first n_base columns (exactly the live pipeline), and the remaining columns
    (the team home dummies) left unscaled and multiplied by sqrt(alpha / pp_alpha), so each dummy's raw coefficient
    carries a ridge penalty of pp_alpha: a random effect with prior variance sigma^2 / pp_alpha."""

    def __init__(self, n_base, alpha, pp_alpha):
        self.n_base, self.alpha, self.pp_alpha = n_base, alpha, pp_alpha

    def _z(self, X):
        b = self.sc.transform(X[:, :self.n_base])
        if X.shape[1] == self.n_base:
            return b
        return np.hstack([b, X[:, self.n_base:] * np.sqrt(self.alpha / self.pp_alpha)])

    def fit(self, X, y):
        self.sc = StandardScaler().fit(X[:, :self.n_base])
        self.r = Ridge(alpha=self.alpha).fit(self._z(X), y)
        return self

    def predict(self, X):
        return self.r.predict(self._z(X))


def walk_forward_pp(fp, feats, pp_cols, pp_alpha, seasons=range(2015, LAST_SEASON + 1)):
    """lean_walk_forward's points half, with the dummies `pp_cols` in the six ridges on their own penalty. The trees
    get the live inputs only (a tree on 40 sparse +/-1 columns is not partial pooling)."""
    played = fp[fp.pf.notna() & (fp.season >= M.TRAIN_FROM)]
    blend_cols = {k: feats + extra for k, (extra, _) in M.BLEND.items()}
    allc = sorted(set(feats) | {c for cols in blend_cols.values() for c in cols})
    out = []
    for s in seasons:
        test_all = fp[fp.season == s]
        for wk in sorted(test_all.loc[test_all.game_type == "REG", "week"].unique()):
            tr = played[(played.season < s) | ((played.season == s) & (played.week < wk))]
            te = test_all[test_all.week == wk]
            hmask = (te.home == 1).values
            h_ids = te.game_id.values[hmask]; a_ids = te.game_id.values[~hmask]
            aset = set(a_ids); ids = [g for g in h_ids if g in aset]
            rec = pd.DataFrame({"game_id": ids, "season": s, "week": wk})
            trh = tr[tr.home == 1].set_index("game_id"); tra = tr[tr.home == 0].set_index("game_id")
            tid = trh.index.intersection(tra.index)
            y = tr.pf.values; X = tr[feats].values
            D_tr = tr[pp_cols].values if pp_cols else np.zeros((len(tr), 0)); D_te = te[pp_cols].values if pp_cols else np.zeros((len(te), 0))
            ridge = PPRidge(len(feats), M.RIDGE, pp_alpha).fit(np.hstack([X, D_tr]), y)
            mu = tr[allc].mean()
            preds = {"ridge": ridge.predict(np.hstack([te[feats].fillna(mu[feats]).values, D_te]))}
            for k, (extra, al) in M.BLEND.items():
                cols = blend_cols[k]
                m = PPRidge(len(cols), al, pp_alpha).fit(np.hstack([tr[cols].fillna(tr[cols].mean()).values, D_tr]), y)
                preds[k] = m.predict(np.hstack([te[cols].fillna(mu[cols]).values, D_te]))
            t = HistGradientBoostingRegressor(**M.TREES).fit(X, y)
            preds["trees"] = t.predict(te[feats].fillna(mu[feats]).values)
            bl = pd.Series(np.mean([preds[k] for k in M.BLEND_LABEL], axis=0), index=te.game_id.values + np.where(hmask, "|h", "|a"))
            rec["model_spread"] = bl.loc[[g + "|h" for g in ids]].values - bl.loc[[g + "|a" for g in ids]].values
            trp = ridge.predict(np.hstack([X, D_tr]))
            ph = pd.Series(trp[(tr.home == 1).values], index=trh.index); pa = pd.Series(trp[(tr.home == 0).values], index=tra.index)
            tr_margin = (trh.loc[tid, "pf"] - tra.loc[tid, "pf"]).values
            tr_mu = (ph.loc[tid] - pa.loc[tid]).values
            sigma_m = float(np.std(tr_margin - tr_mu))
            K = M.key_weights(tr_margin, tr_mu, sigma_m)
            rec["p_home"] = _p_home(rec.model_spread.values, sigma_m, K.values)
            out.append(rec)
    return pd.concat(out, ignore_index=True)


# ------------------------------------------------------------------------------------------------------------ stages
def load_fp():
    return M.prep(M.with_trends(pd.read_parquet(OUT / "features_asof.parquet")))


def stage_base():
    """The base walk-forward (fresh trees) for 2014-2025 and the 2026 weeks played, and the pp engine checked."""
    from threadpoolctl import threadpool_limits
    fp = load_fp()
    wk26 = int(fp[(fp.season == 2026) & fp.pf.notna()].week.max()) if ((fp.season == 2026) & fp.pf.notna()).any() else 0
    fp = fp[(fp.season < 2026) | (fp.week <= wk26)]
    with threadpool_limits(limits=1):
        G = game_frame(fp); G["total_line"] = G.index.map(GAMES.set_index("game_id").total_line)
        t0 = time.time()
        base = finish(lean_walk_forward(fp, G, BASE_FEATS, BASE_TOTAL, seasons=list(range(2014, LAST_SEASON + 1)) + ([2026] if wk26 else [])))
        log("base run", round(time.time() - t0), "s")
        # the partial-pooling engine with no dummies against lean_walk_forward, one season
        pp = walk_forward_pp(fp, BASE_FEATS, [], 1e9, seasons=[2019])
        j = pp.merge(base, on="game_id", suffixes=("", "_b"))
        chk = {"pp_engine_vs_lean_2019_spread_max": float((j.model_spread - j.model_spread_b).abs().max()),
               "pp_engine_vs_lean_2019_p_home_max": float((j.p_home - j.p_home_b).abs().max()), "games": int(len(j)), "weeks_2026_played": wk26}
    base.to_parquet(SCR / "base_all.parquet", index=False)
    base[base.season.between(2015, LAST_SEASON)].to_parquet(SCR / "base.parquet", index=False)
    (SCR / "engine_check.json").write_text(json.dumps(chk, indent=1))
    log("check", chk)


# ------------------------------------------------------------------------------------------------ team-season table
def long_resid() -> pd.DataFrame:
    """One row per (game, team) for regular-season, non-neutral, played games 1999-2026: the team's margin residual
    (model 2014 on, the scoring rating before), home flag, the home team's stadium that season."""
    base = pd.read_parquet(SCR / "base_all.parquet")
    L = SF.long_table(GAMES, base)
    L = L[(L.game_type == "REG") & L.pf.notna() & (L.location != "Neutral")].copy()
    return L


def home_stadiums() -> pd.Series:
    """(team, season) -> the team's most common stadium in its regular-season home games (non-neutral)."""
    g = GAMES[(GAMES.game_type == "REG") & (GAMES.location == "Home")]
    return g.groupby(["home_team", "season"]).stadium_id.agg(lambda s: s.value_counts().index[0])


def team_season_table(L: pd.DataFrame) -> pd.DataFrame:
    """Per team-season: mean margin residual at home (H, nH) and on the road (R, nR), the home-minus-road difference y
    (estimates the team's home edge beyond the league's: rating errors hit both and cancel), its sampling variance from
    the season's residual scale, and each centred on the season's league mean (the league value is what the model
    already carries)."""
    hs = home_stadiums()
    sig = L[L.home == 1].groupby("season").r_margin.std()
    rows = []
    for (t, s), x in L.groupby(["team", "season"]):
        h = x[x.home == 1]; r = x[x.home == 0]
        st = hs.get((t, s))
        h = h[h.stadium_id == st] if st is not None else h.iloc[:0]
        rows.append({"team": t, "season": s, "stadium": st, "H": h.r_margin.mean(), "nH": len(h), "R": r.r_margin.mean(), "nR": len(r),
                     "sig": sig.get(s, np.nan)})
    T = pd.DataFrame(rows)
    T = T[(T.nH >= 2) & (T.nR >= 2)].copy()
    T["y"] = T.H - T.R
    T["v"] = T.sig ** 2 * (1 / T.nH + 1 / T.nR)
    T["vR"] = T.sig ** 2 / T.nR
    for c in ["y", "H", "R"]:
        T[c + "_c"] = T[c] - T.groupby("season")[c].transform("mean")
    return T.reset_index(drop=True)


def eb_estimates(T: pd.DataFrame, S: int, hl: float, stat="y_c", var="v", reset=True, skip=(), stadium_now=None, tau_fixed=None) -> pd.DataFrame:
    """Empirical-Bayes home edge for every team as of the start of season S, from seasons before S only.
    Recency weights w = 0.5 ** ((S - 1 - s) / hl) (last season counts fully); a season from a different home stadium
    than the team's stadium in S is dropped (reset on a move). Weighted mean yhat = sum(a y) / sum(a), a = w / v, its
    sampling variance Vs = sum(a^2 v) / sum(a)^2 (so recency costs precision honestly). Between-team variance by
    moments, tau^2 = max(0, mean(yhat^2) - mean(Vs)) across teams (the league value is 0 after centring);
    shrunk u = tau^2 / (tau^2 + Vs) * yhat, standard error sqrt(tau^2 Vs / (tau^2 + Vs))."""
    hs = home_stadiums() if stadium_now is None else stadium_now
    P = T[(T.season < S) & ~T.season.isin(skip)]
    out = []
    for t, x in P.groupby("team"):
        st = hs.get((t, S))
        if st is None:   # no home games yet in S (a future season): the last known stadium
            st = x.sort_values("season").stadium.iloc[-1]
        if reset:
            x = x[x.stadium == st]
        x = x[x[stat].notna() & (x[var] > 0)]
        if not len(x):
            out.append({"team": t, "stadium": st, "yhat": 0.0, "Vs": np.inf, "seasons": 0}); continue
        w = 0.5 ** ((S - 1 - x.season.values) / hl) if np.isfinite(hl) else np.ones(len(x))
        a = w / x[var].values
        yhat = float((a * x[stat].values).sum() / a.sum()); Vs = float((a ** 2 * x[var].values).sum() / a.sum() ** 2)
        out.append({"team": t, "stadium": st, "yhat": yhat, "Vs": Vs, "seasons": int(len(x))})
    E = pd.DataFrame(out)
    ok = np.isfinite(E.Vs)
    tau2 = max(0.0, float((E.yhat[ok] ** 2).mean() - E.Vs[ok].mean())) if ok.sum() >= 8 else 0.0
    E["tau2_est"] = tau2
    if tau_fixed is not None:   # a forced between-team sd (margin points), for when the estimate says zero
        tau2 = tau_fixed ** 2
    E["tau2"] = tau2
    E["B"] = np.where(ok, tau2 / (tau2 + E.Vs.where(ok, 1.0)), 0.0)
    E["u"] = E.B * E.yhat
    E["se"] = np.where(ok, np.sqrt(np.where(tau2 > 0, tau2 * E.Vs.where(ok, 1.0) / (tau2 + E.Vs.where(ok, 1.0)), 0.0)), np.sqrt(tau2))
    E["season"] = S
    return E


def team_values(T, hl, stat="y_c", var="v", reset=True, skip=(), seasons=range(2013, 2027), tau_fixed=None) -> pd.DataFrame:
    return pd.concat([eb_estimates(T, S, hl, stat, var, reset, skip, tau_fixed=tau_fixed) for S in seasons], ignore_index=True)


# ------------------------------------------------------------------------------------------------------------ ideas
def ideas() -> list[dict]:
    """name, angle, kind: team (a per-team value for the home team, or the visitor with who='away'), game (fixed
    per-game flags), neutral (replace/extend the live home input at neutral sites), pp (partial pooling dummies)."""
    I = []
    def add(name, angle, kind, **kw):
        I.append({"name": name, "angle": angle, "kind": kind, **kw})
    A1 = "1 Per-team home edge (empirical Bayes)"
    add("Team home edge, EB (estimated tau), half-life 2", A1, "team", key="eb_hl2")
    add("Team home edge, EB (estimated tau), half-life 3", A1, "team", key="eb_hl3")
    add("Team home edge, EB (estimated tau), half-life 4", A1, "team", key="eb_hl4")
    add("Team home edge, EB (tau forced to 1 pt), half-life 2", A1, "team", key="eb_hl2_t1")
    add("Team home edge, EB (tau forced to 1 pt), half-life 3", A1, "team", key="eb_hl3_t1")
    add("Team home edge, EB (tau forced to 1 pt), half-life 4", A1, "team", key="eb_hl4_t1")
    add("Team home edge, EB (tau 1 pt), half-life 3, 2020 left out", A1, "team", key="eb_hl3_no2020_t1")
    add("Team home edge, EB (tau 1 pt), half-life 3, x visitor travel", A1, "team", key="eb_hl3_t1", scale="miles")
    A2 = "2 Stadium features"
    add("Home edge at altitude (Denver)", A2, "game", cols=["den_home"])
    add("Home edge in a dome or closed roof", A2, "game", cols=["dome_home"])
    add("Home edge x visitor's travel miles", A2, "game", cols=["vis_miles"])
    add("Home edge x visitor's time-zone change", A2, "game", cols=["vis_tz"])
    add("Neutral sites: home edge set to zero", A2, "neutral", mode="zero")
    add("Neutral sites: own home-edge term", A2, "neutral", mode="add")
    A3 = "3 Home edge vs the visitor"
    add("Home edge in division games", A3, "game", cols=["div_home"])
    add("Visitor travels well (road residual, EB estimated tau, half-life 3)", A3, "team", key="road_hl3", who="away")
    add("Visitor travels well (road residual, EB tau 1 pt, half-life 3)", A3, "team", key="road_hl3_t1", who="away")
    A4 = "4 Home edge by season stage"
    add("Home edge early (weeks 1-4) and late (week 13 on)", A4, "game", cols=["early_home", "late_home"])
    add("Cold-weather home team in December on", A4, "game", cols=["colddec_home"])
    A5 = "5 Partial pooling in the ridge"
    add("Team home dummies, partial pooling (prior sd 0.5 pt)", A5, "pp", tau=0.5)
    add("Team home dummies, partial pooling (prior sd 1 pt)", A5, "pp", tau=1.0)
    return I


def stage_build():
    """Every idea's raw values: team-season values (per key) and game-level signed flags; the team-season table."""
    L = long_resid()
    T = team_season_table(L)
    T.to_parquet(SCR / "team_season.parquet", index=False)
    vals = {}
    vals["eb_hl2"] = team_values(T, 2.0); vals["eb_hl3"] = team_values(T, 3.0); vals["eb_hl4"] = team_values(T, 4.0)
    vals["eb_hl3_no2020"] = team_values(T, 3.0, skip=(2020,))
    vals["eb_inf"] = team_values(T, np.inf)
    vals["road_hl3"] = team_values(T, 3.0, stat="R_c", var="vR", reset=False)
    for h in (2.0, 3.0, 4.0):
        vals[f"eb_hl{int(h)}_t1"] = team_values(T, h, tau_fixed=1.0)
    vals["eb_hl3_no2020_t1"] = team_values(T, 3.0, skip=(2020,), tau_fixed=1.0)
    vals["road_hl3_t1"] = team_values(T, 3.0, stat="R_c", var="vR", reset=False, tau_fixed=1.0)
    for k, v in vals.items():
        v.to_parquet(SCR / f"tv_{k}.parquet", index=False)
    # game-level facts, one row per game
    g = GAMES.copy(); g["gd"] = pd.to_datetime(g.gameday)
    hs = home_stadiums()
    def st_of(t, s):
        v = hs.get((t, s))
        if v is None:
            prev = [hs.get((t, s - k)) for k in range(1, 4)]
            v = next((p for p in prev if p is not None), None)
        return v
    nn = (g.location != "Neutral").astype(float)
    g["vis_st"] = [st_of(t, s) for t, s in zip(g.away_team, g.season)]
    g["home_st"] = [st_of(t, s) for t, s in zip(g.home_team, g.season)]
    miles, tz = [], []
    for vs, st, d in zip(g.vis_st, g.stadium_id, g.gd):
        a, b = SF.STADIUMS.get(vs), SF.STADIUMS.get(st)
        if a is None or b is None:
            miles.append(0.0); tz.append(0.0); continue
        miles.append(SF._hav(a[:2], b[:2]) / 1000.0); tz.append(abs(SF._tz(st, d) - SF._tz(vs, d)))
    g["vis_miles"] = np.array(miles) * nn; g["vis_tz"] = np.array(tz) * nn
    elev = g.stadium_id.map(lambda s: SF.STADIUMS.get(s, (0, 0, 0, 0, "US"))[2])
    g["den_home"] = ((elev >= 4000) & (nn == 1)).astype(float)
    g["dome_home"] = (g.roof.isin(["dome", "closed"]) & (nn == 1)).astype(float)
    g["div_home"] = (g.div_game.astype(float) * nn)
    g["early_home"] = ((g.game_type == "REG") & (g.week <= 4)).astype(float) * nn
    g["late_home"] = (g.week >= 13).astype(float) * nn
    month = g.gd.dt.month
    g["colddec_home"] = ((~g.home_team.isin(M.WARM_OR_DOME)) & ((month >= 12) | (month <= 2))).astype(float) * nn
    g["neutral_g"] = 1.0 - nn
    keep = ["game_id", "season", "week", "home_team", "away_team", "home_st", "vis_st", "neutral_g", "vis_miles", "vis_tz", "den_home", "dome_home",
            "div_home", "early_home", "late_home", "colddec_home"]
    g[keep].to_parquet(SCR / "game_flags.parquet", index=False)
    log("built", T.shape, {k: v.shape for k, v in vals.items()})


# ---------------------------------------------------------------------------------------------- materialising ideas
_W: dict = {}


def _load():
    if not _W:
        from threadpoolctl import threadpool_limits
        _W["tl"] = threadpool_limits(limits=1)
        fp = load_fp(); fp = fp[fp.season <= LAST_SEASON].reset_index(drop=True)
        _W["fp"] = fp
        _W["G0"] = game_frame(fp); _W["G0"]["total_line"] = _W["G0"].index.map(GAMES.set_index("game_id").total_line)
        _W["gf"] = pd.read_parquet(SCR / "game_flags.parquet").set_index("game_id")
        _W["base"] = pd.read_parquet(SCR / "base.parquet")
        _W["T"] = pd.read_parquet(SCR / "team_season.parquet")
    return _W


def _signed(fp, gvals: pd.Series) -> np.ndarray:
    """A per-game home-edge value onto the team rows: +v on the home row, -v on the visitor's."""
    v = gvals.reindex(fp.game_id.values).fillna(0.0).values
    return v * np.where(fp.home.values == 1, 1.0, -1.0)


def _perm_teams(tv: pd.DataFrame, rng) -> pd.DataFrame:
    """Placebo for a per-team value: the team labels shuffled within each season."""
    tv = tv.copy()
    for s, ix in tv.groupby("season").groups.items():
        ix = np.asarray(ix); tv.loc[ix, "u"] = tv.loc[rng.permutation(ix), "u"].values
    return tv


def materialise(idea, seed=None):
    """(fp with the idea's columns, feature list, pp columns). Placebo (seed): per-team values have their team labels
    shuffled within season; game flags are shuffled across games within season (round 3's placebo)."""
    W = _load(); fp = W["fp"].copy(); gf = W["gf"]
    rng = np.random.default_rng(seed) if seed is not None else None
    feats = list(BASE_FEATS)
    if idea["kind"] == "team":
        tv = pd.read_parquet(SCR / f"tv_{idea['key']}.parquet")
        if rng is not None:
            tv = _perm_teams(tv, rng)
        u = dict(zip(zip(tv.team, tv.season), tv.u))
        who = gf.away_team if idea.get("who") == "away" else gf.home_team
        gv = pd.Series([u.get((t, s), 0.0) for t, s in zip(who, gf.season)], index=gf.index) * (1 - gf.neutral_g)
        if idea.get("who") == "away":
            gv = -gv                       # a visitor that travels well lowers the home side's margin
        if idea.get("scale") == "miles":
            gv = gv * gf.vis_miles / max(1e-9, float(gf.vis_miles[gf.neutral_g == 0].mean()))   # the edge scaled by the visitor's trip, mean 1
        fp["hf_x"] = _signed(fp, gv); feats.append("hf_x")
        return fp, feats, []
    if idea["kind"] == "game":
        g = gf[idea["cols"]].copy()
        if rng is not None:
            g[:] = SG._shuffle_within_season(g.values.astype(float), gf.season.values, rng)
        for c in idea["cols"]:
            fp["hf_" + c] = _signed(fp, g[c]); feats.append("hf_" + c)
        return fp, feats, []
    if idea["kind"] == "neutral":
        ng = gf.neutral_g.copy()
        if rng is not None:
            ng[:] = SG._shuffle_within_season(ng.values.astype(float)[:, None], gf.season.values, rng)[:, 0]
        nrow = ng.reindex(fp.game_id.values).fillna(0.0).values
        if idea["mode"] == "zero":
            fp["home_nn"] = fp.home.values * (1 - nrow)
            feats = ["home_nn" if c == "home" else c for c in feats]
        else:
            fp["hf_neutral"] = nrow * np.where(fp.home.values == 1, 1.0, -1.0); feats.append("hf_neutral")
        return fp, feats, []
    if idea["kind"] == "pp":
        # one signed dummy per (team, home stadium); only at non-neutral games at the home team's home stadium
        key = pd.Series([f"{t}|{st}" for t, st in zip(gf.home_team, gf.home_st)], index=gf.index)
        if rng is not None:   # team labels shuffled within season: each season's home teams get another team's key
            key = key.copy()
            for s in np.unique(gf.season.values):
                m = (gf.season.values == s)
                teams = sorted(set(gf.home_team.values[m])); perm = dict(zip(teams, rng.permutation(teams)))
                st_of = dict(zip(gf.home_team.values[m], gf.home_st.values[m]))
                key.values[m] = [f"{perm[t]}|{st_of.get(perm[t])}" for t in gf.home_team.values[m]]
        key = key.where(gf.neutral_g == 0)
        keys = sorted(k for k in key.dropna().unique())
        kr = key.reindex(fp.game_id.values).values
        sgn = np.where(fp.home.values == 1, 1.0, -1.0)
        cols = []
        D = np.zeros((len(fp), len(keys)))
        pos = {k: i for i, k in enumerate(keys)}
        for r, k in enumerate(kr):
            if isinstance(k, str):
                D[r, pos[k]] = sgn[r]
        cols = [f"pp_{i}" for i in range(len(keys))]
        fp = pd.concat([fp, pd.DataFrame(D, columns=cols, index=fp.index)], axis=1)
        return fp, feats, cols
    raise ValueError(idea)


def pp_alpha(idea) -> float:
    """The dummies' penalty for a prior sd tau of a team's home edge in margin points (the variance-components estimate
    is zero in the model era, which would be an infinite penalty, i.e. the base; so tau is set at 0.5 and 1 point),
    sigma the team-points residual sd of the live ridge fit on 2013-14. A signed dummy moves the margin by 2 beta, so
    its prior sd is tau/2 and the penalty sigma^2 / (tau/2)^2."""
    tau = float(idea["tau"])
    W = _load(); tr = W["fp"][W["fp"].pf.notna() & W["fp"].season.between(2013, 2014)]
    m = make_pipeline(StandardScaler(), Ridge(alpha=M.RIDGE)).fit(tr[BASE_FEATS].values, tr.pf.values)
    sig = float(np.std(tr.pf.values - m.predict(tr[BASE_FEATS].values)))
    return sig ** 2 / max(1e-6, (tau / 2) ** 2), tau, sig


def run_idea(idea, seed=None) -> dict:
    W = _load(); t0 = time.time()
    fp, feats, ppc = materialise(idea, seed)
    if idea["kind"] == "pp":
        al, tau, sig = pp_alpha(idea)
        P = walk_forward_pp(fp, feats, ppc, al)
    else:
        P = lean_walk_forward(fp, W["G0"], feats, BASE_TOTAL, points=True, total=False)
    P = finish(P, W["base"])
    out = {"name": idea["name"], "seed": -1 if seed is None else seed, "secs": round(time.time() - t0, 1), **flat(score(P))}
    if seed is None:
        out["coefs"] = reading(idea, fp, feats, ppc)
        P.to_parquet(SCR / "preds" / f"{abs(hash(idea['name'])) % 10**10}.parquet", index=False)
    return out


def reading(idea, fp, feats, ppc) -> str:
    """The fitted weight of the idea's columns in the live ridge on every regular-season game 2013-2025."""
    tr = fp[fp.pf.notna() & (fp.game_type == "REG") & fp.season.between(2013, LAST_SEASON)]
    if idea["kind"] == "pp":
        al, tau, sig = pp_alpha(idea)
        m = PPRidge(len(feats), M.RIDGE, al).fit(np.hstack([tr[feats].values, tr[ppc].values]), tr.pf.values)
        b = m.r.coef_[len(feats):] * np.sqrt(M.RIDGE / al)
        return f"penalty {al:.0f} (tau {tau:.2f} margin pts, sigma {sig:.2f}); dummy margin effects sd {2 * b.std():.3f}, range {2 * b.min():+.2f} to {2 * b.max():+.2f}"
    m = make_pipeline(StandardScaler(), Ridge(alpha=M.RIDGE)).fit(tr[feats].values, tr.pf.values)
    coef = dict(zip(feats, m[-1].coef_ / m[0].scale_)); sd = dict(zip(feats, m[0].scale_))
    new = [c for c in feats if c not in BASE_FEATS]
    s = "; ".join(f"{c}: {coef[c]:+.3f}/unit (margin {2 * coef[c]:+.3f}), {coef[c] * sd[c]:+.3f}/sd, nonzero {float((tr[c] != 0).mean()):.0%}" for c in new)
    if "home" in coef:
        s += f"; home: {coef['home']:+.3f}"
    return s


# ------------------------------------------------------------------------------------------------------ run stages
def _done(path, key="name"):
    if not path.exists():
        return set()
    d = pd.read_csv(path)
    return set(d[key]) if key == "name" else set(zip(d.name, d.seed))


def _append(path, rows):
    pd.DataFrame(rows).to_csv(path, mode="a", header=not path.exists(), index=False)


def stage_real(jobs, only=None):
    from joblib import Parallel, delayed
    (SCR / "preds").mkdir(exist_ok=True)
    path = SCR / "real.csv"
    if "(base)" not in _done(path):
        _append(path, [{"name": "(base)", "seed": -1, "secs": 0.0, **flat(score(pd.read_parquet(SCR / "base.parquet"))), "coefs": ""}])
    todo = [i for i in ideas() if i["name"] not in _done(path) and (only is None or i["name"] in only)]
    log("real runs to do:", len(todo))
    for k in range(0, len(todo), jobs):
        chunk = todo[k:k + jobs]
        from experiments.home_field import run_idea as RI
        rows = Parallel(n_jobs=jobs, backend="loky")(delayed(RI)(i, None) for i in chunk)
        _append(path, rows)
        for r in rows:
            log("done", r["name"], r["secs"], "s")


def verdicts(real: pd.DataFrame) -> pd.DataFrame:
    """Rule 1 (team points miss AND margin miss lower on all three windows) and rule 2 (spread flag and totals flag
    wins minus losses not below base on any window, calibrated win-chance log loss not above base)."""
    b = real[real.name == "(base)"].iloc[0]
    rows = []
    for _, r in real[real.name != "(base)"].iterrows():
        v = {"name": r["name"]}
        for w in WINDOWS:
            v[f"d_team_{w}"] = r[f"team_mae_{w}"] - b[f"team_mae_{w}"]
            v[f"d_margin_{w}"] = r[f"margin_mae_{w}"] - b[f"margin_mae_{w}"]
            v[f"d_sp_{w}"] = (r[f"sp_w_{w}"] - r[f"sp_l_{w}"]) - (b[f"sp_w_{w}"] - b[f"sp_l_{w}"])
            v[f"d_to_{w}"] = (r[f"to_w_{w}"] - r[f"to_l_{w}"]) - (b[f"to_w_{w}"] - b[f"to_l_{w}"])
            v[f"d_ll_{w}"] = r[f"ll_cal_{w}"] - b[f"ll_cal_{w}"]
            v[f"d_brier_{w}"] = r[f"brier_cal_{w}"] - b[f"brier_cal_{w}"]
            v[f"d_mlu_{w}"] = r[f"ml_units_{w}"] - b[f"ml_units_{w}"]
            v[f"sp_{w}"] = f"{int(r[f'sp_w_{w}'])}-{int(r[f'sp_l_{w}'])}"
        v["rule1"] = all(v[f"d_team_{w}"] < 0 and v[f"d_margin_{w}"] < 0 for w in WINDOWS)
        v["rule1_team_only"] = all(v[f"d_team_{w}"] < 0 for w in WINDOWS)
        v["rule2"] = all(v[f"d_sp_{w}"] >= 0 and v[f"d_to_{w}"] >= 0 and v[f"d_ll_{w}"] <= 1e-9 for w in WINDOWS)
        v["coefs"] = r.get("coefs", "")
        rows.append(v)
    return pd.DataFrame(rows)


def placebo_summary(name, real, pl) -> dict:
    b = real[real.name == "(base)"].iloc[0]; r = real[real.name == name].iloc[0]
    gain = {w: b[f"team_mae_{w}"] - r[f"team_mae_{w}"] for w in WINDOWS}
    x = pl[pl.name == name] if len(pl) else pl
    if not len(x):
        return {"draws": 0, "beaten": None, "pct": {}, "pass": False}
    pg = {w: (b[f"team_mae_{w}"] - x[f"team_mae_{w}"]).values for w in WINDOWS}
    beaten = int(sum(any(pg[w][k] >= gain[w] for w in WINDOWS) for k in range(len(x))))
    pct = {w: float((pg[w] < gain[w]).mean()) for w in WINDOWS}
    return {"draws": int(len(x)), "beaten": beaten, "pct": pct, "pass": bool(len(x) >= N_PLACEBO and beaten <= N_PLACEBO - 45)}


def stage_placebo(jobs, names=None, draws=N_PLACEBO, stop_at=STOP_AT):
    from joblib import Parallel, delayed
    real = pd.read_csv(SCR / "real.csv"); V = verdicts(real)
    if names is None:
        names = list(V[V.rule1_team_only & V.rule2].name)   # the rule's gate (team points miss, as round 3); margin reported
    I = {i["name"]: i for i in ideas()}
    path = SCR / "placebo.csv"
    b = real[real.name == "(base)"].iloc[0]
    log("placebo for", names)
    for name in names:
        r = real[real.name == name].iloc[0]
        gain = {w: b[f"team_mae_{w}"] - r[f"team_mae_{w}"] for w in WINDOWS}
        done = pd.read_csv(path) if path.exists() else pd.DataFrame(columns=["name", "seed"])
        have = done[done.name == name]
        seeds = [s for s in range(1000, 1000 + draws) if s not in set(have.seed)]
        def beaten(df):
            return int(sum(any(b[f"team_mae_{w}"] - x[f"team_mae_{w}"] >= gain[w] for w in WINDOWS) for _, x in df.iterrows()))
        nb = beaten(have) if len(have) else 0
        for k in range(0, len(seeds), jobs):
            if nb >= stop_at:
                break
            from experiments.home_field import run_idea as RI
            rows = Parallel(n_jobs=jobs, backend="loky")(delayed(RI)(I[name], s) for s in seeds[k:k + jobs])
            _append(path, rows); nb += beaten(pd.DataFrame(rows))
            log("  ", name, "draws", len(have) + k + len(rows), "beaten", nb)


# ------------------------------------------------------------------------------------------------------- the facts
def stage_facts():
    """The raw readings: each team's shrunk home edge now (as of the 2026 season, prior seasons only, and with 2026's
    played weeks added), which teams differ from the league once shrunk, and how persistent a team's home edge is."""
    T = pd.read_parquet(SCR / "team_season.parquet")
    facts = {}
    M_ = T[T.season >= 2014]   # model residuals only
    # persistence: consecutive seasons, same stadium, centred home-minus-road residual
    a = M_.merge(M_.assign(season=M_.season - 1), on=["team", "season"], suffixes=("", "_next"))
    a = a[a.stadium == a.stadium_next]
    facts["consec_r"] = float(np.corrcoef(a.y_c, a.y_c_next)[0, 1]); facts["consec_n"] = int(len(a))
    a2 = a[(a.season != 2020) & (a.season != 2019)]   # pairs touching 2020 left out
    facts["consec_r_no2020"] = float(np.corrcoef(a2.y_c, a2.y_c_next)[0, 1]); facts["consec_n_no2020"] = int(len(a2))
    # raw (not residual) for comparison
    rawL = GAMES[(GAMES.game_type == "REG") & GAMES.home_score.notna() & (GAMES.location == "Home") & (GAMES.season >= 2014)]
    # halves: odd vs even seasons 2014-2025, per team at its current stadium, precision-weighted means
    def half(x):
        a_ = 1 / x.v; return float((a_ * x.y_c).sum() / a_.sum()), float(1 / a_.sum())
    hs_now = home_stadiums()
    rows = []
    for t, x in M_[M_.season <= 2025].groupby("team"):
        st = hs_now.get((t, 2025)); x = x[x.stadium == st]
        o, e = x[x.season % 2 == 1], x[x.season % 2 == 0]
        if len(o) >= 2 and len(e) >= 2:
            rows.append((t, *half(o), *half(e), len(o), len(e)))
    H = pd.DataFrame(rows, columns=["team", "odd", "v_odd", "even", "v_even", "n_odd", "n_even"])
    facts["halves_r"] = float(np.corrcoef(H.odd, H.even)[0, 1]); facts["halves_teams"] = int(len(H))
    # single-season variance components (2014-2025): observed variance of y_c vs mean sampling variance
    s1 = M_[M_.season <= 2025]
    facts["single_var_obs"] = float(s1.y_c.var()); facts["single_var_noise"] = float(s1.v.mean())
    facts["single_tau2"] = max(0.0, facts["single_var_obs"] - facts["single_var_noise"])
    facts["single_reliability"] = facts["single_tau2"] / facts["single_var_obs"]
    facts["sigma_margin_resid"] = float(M_.sig.mean())
    # the league home edge the model carries now, and the realised
    base = pd.read_parquet(SCR / "base_all.parquet")
    g = GAMES.set_index("game_id")
    b = base[base.game_id.map(g.location) == "Home"].copy()
    b["margin"] = b.game_id.map(g.home_score) - b.game_id.map(g.away_score)
    facts["league_by_season"] = {int(s): {"raw_home_margin": float(x.margin.mean()), "resid_home_margin": float((x.margin - x.model_spread).mean()), "n": int(x.margin.notna().sum())}
                                 for s, x in b[b.margin.notna()].groupby("season")}
    # now: as of the 2026 season (prior seasons only, as the input would be built), half-life 3 and all seasons
    now3 = eb_estimates(T, 2026, 3.0); nowinf = eb_estimates(T, 2026, np.inf)
    tab = now3[["team", "stadium", "seasons", "yhat", "Vs", "u", "se", "tau2"]].merge(nowinf[["team", "u", "se", "yhat", "Vs", "seasons", "tau2"]].rename(
        columns={"u": "u_all", "se": "se_all", "yhat": "yhat_all", "Vs": "Vs_all", "seasons": "seasons_all", "tau2": "tau2_all"}), on="team")
    # raw home-minus-away margin per team at its current stadium 2014-2025 (not after the model), for reference
    raw = []
    for t in tab.team:
        st = hs_now.get((t, 2025))
        hh = rawL[(rawL.home_team == t) & (rawL.stadium_id == st) & (rawL.season <= 2025)]
        aa = rawL[(rawL.away_team == t) & (rawL.season <= 2025) & (rawL.season >= (hh.season.min() if len(hh) else 2014))]
        raw.append(float((hh.home_score - hh.away_score).mean() - (aa.home_score - aa.away_score).mul(-1).mean()) / 2 if len(hh) and len(aa) else np.nan)
    tab["raw_half_home_minus_road"] = raw
    tab["z"] = tab.u / tab.se.replace(0, np.nan)
    tab["z_raw"] = tab.yhat / np.sqrt(tab.Vs)
    tab["z_raw_all"] = tab.yhat_all / np.sqrt(tab.Vs_all)
    tab["z_all"] = tab.u_all / tab.se_all.replace(0, np.nan)
    tab = tab.sort_values("u", ascending=False)
    tab.to_parquet(SCR / "facts_teams.parquet", index=False)
    # tau over time (as-of, half-life 3 and all seasons)
    tv3 = pd.read_parquet(SCR / "tv_eb_hl3.parquet"); tvi = pd.read_parquet(SCR / "tv_eb_inf.parquet")
    facts["tau_by_season_hl3"] = {int(s): float(np.sqrt(x.tau2.iloc[0])) for s, x in tv3.groupby("season")}
    facts["tau_by_season_all"] = {int(s): float(np.sqrt(x.tau2.iloc[0])) for s, x in tvi.groupby("season")}
    # does last seasons' shrunk edge predict this season's home-minus-road residual? (the direct test, 2015-2025)
    j = T[T.season.between(2015, 2025)].merge(tv3[["team", "season", "u"]], on=["team", "season"])
    facts["pred_slope_hl3"] = float(np.polyfit(j.u, j.y_c, 1)[0]) if j.u.std() > 0 else float("nan")
    facts["pred_r_hl3"] = float(np.corrcoef(j.u, j.y_c)[0, 1]) if j.u.std() > 0 else float("nan"); facts["pred_n"] = int(len(j))
    ji = T[T.season.between(2015, 2025)].merge(tvi[["team", "season", "yhat"]], on=["team", "season"])
    facts["pred_r_unshrunk_all"] = float(np.corrcoef(ji.yhat, ji.y_c)[0, 1])
    (SCR / "facts.json").write_text(json.dumps(facts, indent=1, default=float))
    log("facts", {k: v for k, v in facts.items() if not isinstance(v, dict)})
    print(tab.round(2).to_string(index=False))


# ------------------------------------------------------------------------------------------------------------ report
def _f(x, nd=3, sign=True):
    return f"{x:+.{nd}f}" if sign else f"{x:.{nd}f}"


def results_table() -> pd.DataFrame:
    real = pd.read_csv(SCR / "real.csv"); V = verdicts(real)
    pl = pd.read_csv(SCR / "placebo.csv") if (SCR / "placebo.csv").exists() else pd.DataFrame()
    I = {i["name"]: i for i in ideas()}
    rows = []
    for _, v in V.iterrows():
        ps = placebo_summary(v["name"], real, pl)
        r = {"angle": I[v["name"]]["angle"], "idea": v["name"]}
        for w in WINDOWS:
            for k in ["team", "margin"]:
                r[f"d_{k}_miss_{w}"] = v[f"d_{k}_{w}"]
            r[f"spread_flag_{w}"] = v[f"sp_{w}"]; r[f"d_spread_wl_{w}"] = v[f"d_sp_{w}"]; r[f"d_totals_wl_{w}"] = v[f"d_to_{w}"]
            r[f"d_logloss_cal_x1000_{w}"] = 1000 * v[f"d_ll_{w}"]; r[f"d_brier_cal_x1000_{w}"] = 1000 * v[f"d_brier_{w}"]; r[f"d_ml_units_{w}"] = v[f"d_mlu_{w}"]
        r["rule1_team_and_margin"] = bool(v.rule1); r["rule1_team_only"] = bool(v.rule1_team_only); r["rule2"] = bool(v.rule2)
        r["placebo_draws"] = ps["draws"]; r["placebo_beaten"] = ps["beaten"]
        for w in WINDOWS:
            r[f"placebo_pct_{w}"] = ps["pct"].get(w, np.nan)
        fails = []
        bad1 = [w for w in WINDOWS if not (v[f"d_team_{w}"] < 0 and v[f"d_margin_{w}"] < 0)]
        if bad1:
            fails.append("rule 1 (" + ", ".join(bad1) + ")")
        bad2 = [w + " " + "/".join(x for x, ok in [("spread", v[f"d_sp_{w}"] >= 0), ("totals", v[f"d_to_{w}"] >= 0), ("log loss", v[f"d_ll_{w}"] <= 1e-9)] if not ok)
                for w in WINDOWS if not (v[f"d_sp_{w}"] >= 0 and v[f"d_to_{w}"] >= 0 and v[f"d_ll_{w}"] <= 1e-9)]
        if bad2:
            fails.append("rule 2 (" + "; ".join(bad2) + ")")
        if not fails and ps["draws"] and not ps["pass"]:
            fails.append(f"rule 3 ({ps['beaten']} of {ps['draws']} shuffles matched it)")
        r["verdict"] = "passes" if (not fails and ps["pass"]) else ("not adopted: " + "; ".join(fails) if fails else "not adopted: placebo not run")
        r["effect"] = v["coefs"]
        rows.append(r)
    return pd.DataFrame(rows)


def write_report():
    R = results_table()
    R.to_csv(REP / "home_field.csv", index=False)
    log("wrote", REP / "home_field.csv", R.shape)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", required=True)
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--names", default=None)
    ap.add_argument("--draws", type=int, default=N_PLACEBO)
    ap.add_argument("--stop", type=int, default=STOP_AT)
    a = ap.parse_args()
    names = a.names.split("||") if a.names else None
    {"base": stage_base, "build": stage_build, "facts": stage_facts}.get(a.stage, lambda: None)()
    if a.stage == "real":
        stage_real(a.jobs, names)
    elif a.stage == "placebo":
        stage_placebo(a.jobs, names, a.draws, a.stop)
    elif a.stage == "report":
        write_report()
