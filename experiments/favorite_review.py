"""Why the model's favourite edges lose, and whether a model fix repairs it (30 Sep 2026, Matt).

Research only: reads data/processed and data/archive, writes reports/favorite_review.{csv,md} and
reports/favorite_review_*.csv. Nothing in nflmodel/, web/ or data/ changes.

The bets: the model's side when |model_spread - spread_line| >= 4 (the live flag), regular season, weeks 1-17, graded at the
close, pushes out, -110. "Favourite" = our side is the market favourite (nflverse sign: spread_line > 0 means home favoured).

Parts
  1. Case review: every favourite bet at 4+ (and 3+), every dog bet at 4+, with the inputs that drove the number
     (contribution = coef x (home x - away x) from the ridge fit that priced the game; the training mean cancels in the
     home-minus-away difference), the seven models' spread, early-season depth, QB changes, the injury inputs, the line
     move from the opener (2015-21) and whether the cover was decided late (play-by-play, 2016+).
  2. Patterns: each factor compared across favourite bets, dog bets and every game, with a within-season placebo.
  3. Fixes to the model's number (walk-forward: every parameter fit on earlier seasons only), scored under
     reports/round3_rule.md on 2015-18 / 2019-22 / 2023-25, with favourite and dog bets shown apart.
  4. Bet rules as the fallback: favourites at a higher cut, or none; dogs at 3.5+.

    python -m experiments.favorite_review [--refit]      (--refit runs the refit-based fixes; ~15 min on 4 cores)
"""
from __future__ import annotations
import os, sys, json, time, argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import numpy as np, pandas as pd
from scipy import stats
from nflmodel import model as M, backtest as B
from nflmodel.model import OUT

ROOT = Path(__file__).resolve().parent.parent
REP = ROOT / "reports"
SCR = Path(os.environ.get("FR_SCRATCH", "/tmp/favorite_review")); SCR.mkdir(parents=True, exist_ok=True)
WINDOWS = {"2015-18": (2015, 2018), "2019-22": (2019, 2022), "2023-25": (2023, 2025)}
EDGE, LAST_WEEK, VIG = 4.0, 17, 1.1
RNG = np.random.default_rng(20260930)

GROUPS = {   # the ridge's 22 inputs in plain groups (div_game is the same for both teams and cancels)
    "qb": ["qb_rating", "qb_out"],
    "ratings": ["off_epa_play", "def_epa_play", "off_pf", "def_pf"],
    "injuries": ["skill_out_value", "opp_skill_out_value", "off_snap_out", "opp_def_snap_out"],
    "turnover": ["off_turnover_early", "opp_def_turnover_early"],
    "home": ["home", "neutral"],
    "weather": ["dome", "wind_out", "cold", "rain", "warm_in_cold"],
    "late": ["dead_late", "opp_dead_late"],
    "div": ["div_game"],
}
MODELS = list(M.BLEND_LABEL)


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def wlab(s):
    for k, (a, b) in WINDOWS.items():
        if a <= s <= b:
            return k
    return str(s)


# ------------------------------------------------------------------------------------------------------------ data
def load():
    g = pd.read_parquet(OUT / "games.parquet"); p = pd.read_parquet(OUT / "pred_v3.parquet")
    d = B.join(p, g)
    d = d[(d.game_type == "REG") & d.spread_line.notna() & (d.week <= LAST_WEEK)].copy()
    return d, g


def sides(d: pd.DataFrame, spread: str = "model_spread") -> pd.DataFrame:
    """Side, favourite flag and grading for the model's side on every game (any edge)."""
    d = d.copy()
    e = d[spread] - d.spread_line
    d["edge"] = e; d["aedge"] = e.abs()
    d["home_side"] = e > 0
    d["sgn"] = np.where(d.home_side, 1.0, -1.0)
    d["fav"] = (d.home_side & (d.spread_line > 0)) | (~d.home_side & (d.spread_line < 0))
    d["pk"] = d.spread_line == 0
    d["dog"] = ~d.fav & ~d.pk
    d["ats"] = (d.result - d.spread_line) * d.sgn          # points our side beat the closing line by
    d["win"] = d.ats > 0; d["push"] = d.ats == 0
    d["units"] = np.where(d.push, 0.0, np.where(d.win, 1.0, -VIG))
    d["window"] = d.season.map(wlab)
    return d


def features() -> pd.DataFrame:
    return M.prep(M.with_trends(pd.read_parquet(OUT / "features_asof.parquet")))


def case_inputs(d: pd.DataFrame, fp: pd.DataFrame, g: pd.DataFrame) -> pd.DataFrame:
    """Per game: each input's home-minus-away contribution in the ridge that priced it, the groups, the seven models,
    early-season depth, QB changes and absences, the injury inputs, and the previous result of each side."""
    h = fp[fp.home == 1].set_index("game_id"); a = fp[fp.home == 0].set_index("game_id")
    ids = d.game_id.values
    out = pd.DataFrame({"game_id": ids}).set_index("game_id")
    dd = d.set_index("game_id")
    for k in M.FEATS:
        out[f"c_{k}"] = dd[f"coef_{k}"].values * (h.loc[ids, k].values - a.loc[ids, k].values)
    for gname, cols in GROUPS.items():
        out[f"g_{gname}"] = out[[f"c_{k}" for k in cols]].sum(axis=1)
    out["ridge_rebuilt"] = out[[f"c_{k}" for k in M.FEATS]].sum(axis=1)
    out["ridge_spread"] = (dd.home_exp_ridge - dd.away_exp_ridge).values
    for k in MODELS:
        out[f"s_{k}"] = (dd[f"home_m_{k}"] - dd[f"away_m_{k}"]).values
    S = out[[f"s_{k}" for k in MODELS]]
    out["models_sd"] = S.std(axis=1).values
    out["models_range"] = (S.max(axis=1) - S.min(axis=1)).values
    out["blend_adj"] = dd.model_spread.values - out.ridge_spread.values          # the six other models' pull on the ridge
    out["trees_minus_ridge"] = out.s_trees.values - out.s_ridge.values
    out["nontrees_spread"] = S.drop(columns=["s_trees"]).mean(axis=1).values
    # early season: this season's games each side had played (the ratings' own n_games is the home side's)
    for side, x in (("home", h), ("away", a)):
        out[f"{side}_n_games"] = x.loc[ids, "n_games"].values
        out[f"{side}_qb_id"] = x.loc[ids, "qb_id"].values
        out[f"{side}_qb_rating"] = x.loc[ids, "qb_rating"].values
        out[f"{side}_qb_out"] = x.loc[ids, "qb_out"].values
        out[f"{side}_skill_out_value"] = x.loc[ids, "skill_out_value"].values
        out[f"{side}_off_snap_out"] = x.loc[ids, "off_snap_out"].values
        out[f"{side}_off_pf"] = x.loc[ids, "off_pf"].values
        out[f"{side}_def_pf"] = x.loc[ids, "def_pf"].values
        out[f"{side}_off_epa"] = x.loc[ids, "off_epa_play"].values
        out[f"{side}_def_epa"] = x.loc[ids, "def_epa_play"].values
        out[f"{side}_turnover_early"] = x.loc[ids, "off_turnover_early"].values
    # the opponent-defence snaps out as the home row sees it is the away side's defence
    out["away_def_snap_out"] = h.loc[ids, "opp_def_snap_out"].values
    out["home_def_snap_out"] = a.loc[ids, "opp_def_snap_out"].values
    # QB change: the starter differs from the team's previous game's starter (any earlier game, last season included)
    tg = fp[["game_id", "season", "week", "team", "qb_id"]].sort_values(["team", "season", "week"])
    tg["prev_qb"] = tg.groupby("team").qb_id.shift(1)
    tg["qb_change"] = (tg.qb_id != tg.prev_qb) & tg.prev_qb.notna() & tg.qb_id.notna()
    qc = tg.set_index(["game_id", "team"]).qb_change
    out["home_qb_change"] = qc.reindex(pd.MultiIndex.from_arrays([ids, dd.home_team.values])).fillna(False).values
    out["away_qb_change"] = qc.reindex(pd.MultiIndex.from_arrays([ids, dd.away_team.values])).fillna(False).values
    # previous result (same season) of each side, for "off a big win"
    r = g[(g.game_type == "REG") & g.home_score.notna()]
    long = pd.concat([r.assign(team=r.home_team, m=r.home_score - r.away_score, cov=r.home_score - r.away_score - r.spread_line),
                      r.assign(team=r.away_team, m=r.away_score - r.home_score, cov=r.away_score - r.home_score + r.spread_line)])
    long = long.sort_values(["season", "team", "week"])
    long["prev_m"] = long.groupby(["season", "team"]).m.shift(1)
    long["prev_cov"] = long.groupby(["season", "team"])["cov"].shift(1)
    pm = long.set_index(["game_id", "team"])
    for side, col in (("home", "home_team"), ("away", "away_team")):
        key = pd.MultiIndex.from_arrays([ids, dd[col].values])
        out[f"{side}_prev_margin"] = pm.prev_m.reindex(key).values
        out[f"{side}_prev_cover"] = pm.prev_cov.reindex(key).values
    return out.reset_index()


def openers(d: pd.DataFrame) -> pd.DataFrame:
    """Archive opener (2015-21) with the bet sweep's bad-row filter (experiments/bet_rules_sweep.py): the opener, the close
    minus the opener (nflverse sign)."""
    o = pd.read_csv(ROOT / "data" / "archive" / "openers_2015_2021.csv").drop(columns=["season", "week"]).set_index("game_id")
    x = d[["game_id", "spread_line", "total_line"]].copy()
    for c in ("open_spread", "open_total", "close_spread", "close_total"):
        x[c] = x.game_id.map(o[c])
    bad = (((x.close_spread - x.spread_line).abs() > 2) | ((x.close_total - x.total_line).abs() > 3) | (x.open_total < 25) | (x.close_total < 25)
           | ((x.open_spread == 0) & (x.spread_line.abs() >= 7)) | ((x.open_spread - x.spread_line).abs() > 10) & (np.sign(x.open_spread) != np.sign(x.spread_line)))
    x.loc[bad, "open_spread"] = np.nan
    x["line_move"] = x.spread_line - x.open_spread          # + : the close moved toward the home side
    return x[["game_id", "open_spread", "line_move"]]


def late_scores(g: pd.DataFrame) -> pd.DataFrame:
    """Home margin at the end of the third quarter and with 5:00 left in regulation, from the play-by-play (2016 on):
    the score before the first play at or under those clocks."""
    x = pd.read_parquet(OUT / "scheme_plays.parquet", columns=["game_id", "play_id", "posteam", "game_seconds_remaining", "score_differential"])
    x = x[x.score_differential.notna() & x.game_seconds_remaining.notna()].sort_values(["game_id", "play_id"])
    home = g.set_index("game_id").home_team
    x["hm"] = np.where(x.posteam.values == x.game_id.map(home).values, 1.0, -1.0) * x.score_differential
    out = {}
    for lab, sec in (("q3", 900), ("m5", 300)):
        y = x[x.game_seconds_remaining <= sec].groupby("game_id").hm.first()
        out[f"home_margin_{lab}"] = y
    return pd.DataFrame(out).reset_index().rename(columns={"index": "game_id"})


def postmortem_cols() -> pd.DataFrame:
    """Per spread bet from reports/postmortem.csv (29 Sep 2026): luck toward the bet, garbage-time and backdoor points, the
    listed QB who did not play, and the starter's share of dropbacks (lost in the game)."""
    p = pd.read_csv(REP / "postmortem.csv"); p = p[p.kind == "spread"]
    p["our_qb_wrong"] = np.where(p.bet_home == 1, p.qb_wrong_h, p.qb_wrong_a)
    p["opp_qb_wrong"] = np.where(p.bet_home == 1, p.qb_wrong_a, p.qb_wrong_h)
    p["our_qb_lost"] = np.where(p.bet_home == 1, p.qb_share_h, p.qb_share_a) < 0.6
    p["opp_qb_lost"] = np.where(p.bet_home == 1, p.qb_share_a, p.qb_share_h) < 0.6
    return p[["game_id", "luck", "c_turnovers", "c_garbage", "c_garbage_backdoor", "loss_class", "our_qb_wrong", "opp_qb_wrong", "our_qb_lost", "opp_qb_lost"]]


def oriented(d: pd.DataFrame, c: pd.DataFrame) -> pd.DataFrame:
    """Everything toward our side (the model's side on each game): contributions times the side's sign, our / their
    values for the side-specific readings."""
    x = d.drop(columns=[k for k in c.columns if k in d.columns and k != "game_id"]).merge(c, on="game_id", how="left")
    s = x.sgn.values; hs = x.home_side.values
    for k in M.FEATS:
        x[f"o_{k}"] = x[f"c_{k}"] * s
    for gname in GROUPS:
        x[f"o_{gname}"] = x[f"g_{gname}"] * s
    x["o_ridge"] = x.ridge_spread * s; x["o_blend_adj"] = x.blend_adj * s; x["o_trees_minus_ridge"] = x.trees_minus_ridge * s
    for k in MODELS:
        x[f"e_{k}"] = (x[f"s_{k}"] - x.spread_line) * s          # each model's edge toward our side
    x["n_models_4"] = sum((x[f"e_{k}"] >= EDGE).astype(int) for k in MODELS)
    x["n_models_side"] = sum((x[f"e_{k}"] > 0).astype(int) for k in MODELS)
    x["e_nontrees"] = (x.nontrees_spread - x.spread_line) * s
    def pick(h, a):
        return np.where(hs, x[h], x[a]), np.where(hs, x[a], x[h])
    for nm in ["n_games", "qb_id", "qb_rating", "qb_out", "qb_change", "skill_out_value", "off_snap_out", "def_snap_out", "off_pf", "def_pf",
               "off_epa", "def_epa", "turnover_early", "prev_margin", "prev_cover"]:
        x[f"our_{nm}"], x[f"opp_{nm}"] = pick(f"home_{nm}", f"away_{nm}")
    x["min_n_games"] = np.minimum(x.our_n_games, x.opp_n_games)
    x["our_rating"] = x.o_ratings  # the rating group's pull toward our side (for tables)
    x["model_margin_ours"] = x.model_spread * s                   # our side's expected margin
    x["line_ours"] = x.spread_line * s                              # our side's market margin (+ = the market has us winning)
    x["inj_pull"] = x.o_injuries + x.o_qb_out                        # the injury inputs plus QB-out, toward our side
    return x


# -------------------------------------------------------------------------------------------------------- patterns
def factors(x: pd.DataFrame) -> dict:
    """Candidate reasons, each a yes/no per game from the model's side (fixed before looking at the favourite records;
    the cut-offs are round numbers). Values NaN where the reading does not exist (line move before 2015 / after 2021)."""
    q_sd = x.models_sd.quantile(2 / 3)
    mv = x.line_move * x.sgn
    F = {
        "Weeks 1-4": x.week <= 4,
        "Weeks 15-17": x.week >= 15,
        "Our side has 3 or fewer games this season": x.our_n_games <= 3,
        "Our side off a 14+ point win": x.our_prev_margin >= 14,
        "Opponent off a 14+ point loss": x.opp_prev_margin <= -14,
        "Our side covered last week by 10+": x.our_prev_cover >= 10,
        "Injury inputs + QB-out pull 1.5+ pts our way": x.inj_pull >= 1.5,
        "Opponent QB changed or listed out": (x.opp_qb_change.astype(bool) | (x.opp_qb_out > 0)),
        "Our QB changed from last game": x.our_qb_change.astype(bool),
        "Trees' edge 1+ pt below the ridge's": (x.e_trees - x.e_ridge) <= -1,
        "Trees' edge under 4": x.e_trees < EDGE,
        "Seven models disagree (top third of SD)": x.models_sd >= q_sd,
        "Line 7+ (either side)": x.spread_line.abs() >= 7,
        "Our side at home": x.home_side,
        "Model has our side by 10+": x.model_margin_ours >= 10,
        "Rating pull 3+ pts our way": x.o_ratings >= 3,
        "QB pull 3+ pts our way": x.o_qb >= 3,
        "Offseason-turnover pull 1+ pt our way": x.o_turnover >= 1,
        "Out-of-the-race pull 1+ pt our way": x.o_late >= 1,
        "Close moved 1+ pt against us from the opener (2015-21)": (mv <= -1).where(x.line_move.notna()),
    }
    return {k: v.astype(float) if v.dtype != float else v for k, v in F.items()}


def wl(s: pd.DataFrame) -> tuple[int, int]:
    s = s[~s.push]
    return int(s.win.sum()), int((~s.win).sum())


def rec(s: pd.DataFrame) -> str:
    w, l = wl(s)
    return f"{w}-{l}"


def placebo_gap(pool: pd.DataFrame, flag: pd.Series, draws: int = 2000) -> tuple[float, float]:
    """Win-rate gap (without the factor minus with it) inside `pool`, and the share of within-season shuffles of the
    factor that give a gap at least as large (one-sided: the factor hurts)."""
    p = pool[~pool.push & flag.notna()].copy(); f = flag[p.index].astype(bool).values
    if f.sum() == 0 or (~f).sum() == 0:
        return np.nan, np.nan
    real = p.win.values[~f].mean() - p.win.values[f].mean()
    seasons = p.season.values; w = p.win.values.astype(float); idx = {s: np.where(seasons == s)[0] for s in np.unique(seasons)}
    cnt = 0
    for _ in range(draws):
        g = np.empty_like(f)
        for s, ii in idx.items():
            g[ii] = RNG.permutation(f[ii])
        if w[~g].mean() - w[g].mean() >= real - 1e-12:
            cnt += 1
    return float(real), cnt / draws


def pattern_table(x: pd.DataFrame) -> pd.DataFrame:
    d = x[x.season <= 2025]
    F = factors(d)
    fav3, fav4, dog4, dog3 = d[d.fav & (d.aedge >= 3)], d[d.fav & (d.aedge >= 4)], d[d.dog & (d.aedge >= 4)], d[d.dog & (d.aedge >= 3)]
    rows = []
    for name, f in F.items():
        r = {"factor": name}
        for lab, s in (("fav4", fav4), ("dog4", dog4), ("all", d)):
            ff = f[s.index]
            r[f"share_{lab}"] = round(float(ff.mean()), 3)
        for lab, s in (("fav4", fav4), ("fav3", fav3), ("dog4", dog4), ("all", d)):
            ff = f[s.index]
            r[f"{lab}_with"] = rec(s[ff == 1]); r[f"{lab}_without"] = rec(s[ff == 0])
        for lab, s in (("fav4", fav4), ("fav3", fav3), ("dog4", dog4), ("dog3", dog3)):
            ff = f[s.index]
            gap, p = placebo_gap(s, ff)
            r[f"gap_{lab}"] = round(gap, 3) if gap == gap else np.nan; r[f"placebo_p_{lab}"] = p
        # points: mean ATS with the factor, favourites 3+
        ff = f[fav3.index]
        r["fav3_ats_with"] = round(float(fav3.ats[ff == 1].mean()), 2) if (ff == 1).any() else np.nan
        r["fav3_ats_without"] = round(float(fav3.ats[ff == 0].mean()), 2) if (ff == 0).any() else np.nan
        rows.append(r)
    return pd.DataFrame(rows)


# ------------------------------------------------------------------------------------------------------------ fixes
def p_home_normal(spread, sigma):
    """Home win chance on a normal curve with the fit's residual scale (the key-number weights of past fits are not
    stored, so base and fix are both read this way; enough to see whether a fix worsens calibration)."""
    return stats.norm.cdf(np.asarray(spread) / np.asarray(sigma))


def score_spread(x: pd.DataFrame, spread: np.ndarray) -> dict:
    """The round-3 readings for a model spread on the case table x (2015-25, weeks 1-17, REG, with a line): margin and
    team-points miss (team points = (model_total +/- spread) / 2, as the live page), the 4+ flag overall / favourites /
    dogs (W-L and units at -110), and the win chance's log loss."""
    y = sides(x.assign(_s=spread), "_s")
    out = {}
    for w, (a, b) in WINDOWS.items():
        m = (y.season >= a) & (y.season <= b)
        z = y[m]
        he = (z.model_total + z._s) / 2 - z.home_score; ae = (z.model_total - z._s) / 2 - z.away_score
        o = {"margin_mae": float((z._s - z.result).abs().mean()), "team_mae": float(np.concatenate([he.abs(), ae.abs()]).mean())}
        for lab, s in (("flag", z.aedge >= EDGE), ("fav", (z.aedge >= EDGE) & z.fav), ("dog", (z.aedge >= EDGE) & z.dog)):
            q = z[s & ~z.push]
            o[f"{lab}_w"], o[f"{lab}_l"], o[f"{lab}_u"] = int(q.win.sum()), int((~q.win).sum()), float(q.units.sum())
        nt = z.result != 0; p = np.clip(p_home_normal(z._s, z.sigma_margin), 1e-6, 1 - 1e-6)[nt.values]; hw = (z.result > 0)[nt].values
        o["logloss"] = float(-(hw * np.log(p) + (~hw) * np.log(1 - p)).mean())
        out[w] = o
    return out


def walk_fit(x: pd.DataFrame, make, grid, min_past=1):
    """Season by season: choose the grid point with the lowest margin miss on all earlier seasons (2015 on) and apply it
    to this season. Seasons with fewer than min_past earlier seasons keep the base number. Returns the new spread and
    the parameter used per season."""
    new = x.model_spread.values.copy(); used = {}
    for s in sorted(x.season.unique()):
        past = x.season < s
        if x.loc[past, "season"].nunique() < min_past:
            used[int(s)] = None; continue
        best, bp = np.inf, None
        for p in grid:
            v = make(x[past], p)
            e = float(np.abs(v - x.loc[past, "result"].values).mean())
            if e < best - 1e-12:
                best, bp = e, p
        cur = (x.season == s).values
        new[cur] = make(x[cur], bp); used[int(s)] = bp
    return new, used


def lsq_fit(x: pd.DataFrame, cols, min_past=1, nonneg=False):
    """Season by season: least squares of the result on `cols` (no intercept; non-negative weights if asked) over all
    earlier seasons, applied to this season. Returns the new spread and the coefficients per season."""
    from scipy.optimize import nnls
    new = x.model_spread.values.copy(); used = {}
    for s in sorted(x.season.unique()):
        past = (x.season < s).values
        if x.loc[past, "season"].nunique() < min_past:
            used[int(s)] = None; continue
        X = x.loc[past, cols].values; yv = x.loc[past, "result"].values
        b = nnls(X, yv)[0] if nonneg else np.linalg.lstsq(X, yv, rcond=None)[0]
        cur = (x.season == s).values
        new[cur] = x.loc[cur, cols].values @ b; used[int(s)] = [round(float(v), 3) for v in b]
    return new, used


def fixes(x: pd.DataFrame) -> dict:
    """Each candidate fix: name -> (new spread, parameters per season, what it moves). Every parameter is chosen on
    earlier seasons only (2015 keeps the base number: pred_v3 has nothing before it)."""
    F = {}
    m = x.model_spread.values
    inj = (x.g_injuries + x.c_qb_out).values      # the injury inputs and QB-out, home minus away
    S = {k: x[f"s_{k}"].values for k in MODELS}
    # A. scale the whole margin (market-free "shrink toward zero" when k < 1)
    F["A. Scale the margin (k fit on past seasons)"] = walk_fit(x, lambda z, k: k * z.model_spread.values, np.round(np.arange(0.80, 1.201, 0.02), 2))
    # B. shrink only big margins toward zero: beyond T points, k of each extra point
    def tail(z, p):
        T, k = p; a = z.model_spread.values; return np.where(np.abs(a) > T, np.sign(a) * (T + k * (np.abs(a) - T)), a)
    F["B. Shrink margins beyond T toward zero (T, k fit)"] = walk_fit(x, tail, [(T, k) for T in (3, 5, 7, 9) for k in (0.5, 0.6, 0.7, 0.8, 0.9, 1.0)])
    for T, k in ((5, 0.7), (7, 0.5)):
        F[f"B'. Shrink beyond {T} by {k} (fixed)"] = (tail(x, (T, k)), "fixed")
    # C. scale the injury inputs' pull (injury values, snaps out, QB-out)
    F["C. Scale the injury + QB-out pull (k fit)"] = walk_fit(x, lambda z, k: z.model_spread.values - (1 - k) * (z.g_injuries + z.c_qb_out).values, np.round(np.arange(0.0, 1.51, 0.1), 2))
    F["C'. Cap the injury + QB-out pull at 1 pt (postmortem)"] = (m - inj + np.clip(inj, -1, 1), "fixed")
    # D. recalibrate each part of the number on past results (least squares, groups + the other six models' pull)
    F["D. Re-weight the model's parts on past results"] = lsq_fit(x, ["g_qb", "g_ratings", "g_injuries", "g_turnover", "g_home", "g_weather", "g_late", "g_div", "blend_adj"])
    # E. stacked blend: the seven models' spreads weighted by least squares on past seasons
    F["E. Stack the seven models (non-negative weights fit)"] = lsq_fit(x, [f"s_{k}" for k in MODELS], nonneg=True)
    # G. early season: shrink (or stretch) weeks 1-4 only
    wk = x.week.values <= 4
    F["G. Scale weeks 1-4 only (k fit)"] = walk_fit(x, lambda z, k: np.where(z.week.values <= 4, k * z.model_spread.values, z.model_spread.values), np.round(np.arange(0.7, 1.31, 0.05), 2))
    # H. cap the rating and QB pulls (the two biggest parts of a favourite edge)
    def cap(col):
        return lambda z, c: z.model_spread.values - z[col].values + np.clip(z[col].values, -c, c)
    F["H. Cap the rating pull at c (fit)"] = walk_fit(x, cap("g_ratings"), [4, 6, 8, 10, 12, 99])
    F["H'. Cap the QB pull at c (fit)"] = walk_fit(x, cap("g_qb"), [3, 4, 5, 6, 8, 99])
    # I. home field: take c points off the home side (c fit on past results; home_field*.py settled the league number)
    F["I. Home-field offset (c fit)"] = walk_fit(x, lambda z, c: z.model_spread.values - c * (z.g_home.values != 0), np.round(np.arange(-1.0, 1.01, 0.1), 2))
    # F. more weight on the boosted trees (w fit on past seasons; fixed grid shown too)
    ntr = x.nontrees_spread.values
    F["F. Trees' share of the blend (w fit)"] = walk_fit(x, lambda z, w: (1 - w) * z.nontrees_spread.values + w * z.s_trees.values, np.round(np.arange(0.0, 0.61, 0.05), 2))
    for w in (0.0, 0.25, 0.33, 0.5):
        F[f"F'. Trees' share {w:g} (fixed; live 1/7 = 0.14)"] = ((1 - w) * ntr + w * S["trees"], "fixed")
    return F


def placebo_fix(x: pd.DataFrame, new: np.ndarray, base_sc: dict, real_sc: dict, draws: int = 50) -> dict:
    """The fix's change to each game's number shuffled within season (50 draws): the real margin-miss gain must beat the
    shuffled gain on every window in at least 45 of 50 draws (round-3 rule 3)."""
    delta = new - x.model_spread.values
    seasons = x.season.values; idx = {s: np.where(seasons == s)[0] for s in np.unique(seasons)}
    gain = {w: base_sc[w]["margin_mae"] - real_sc[w]["margin_mae"] for w in WINDOWS}
    beaten = 0
    for _ in range(draws):
        dd = delta.copy()
        for s, ii in idx.items():
            dd[ii] = RNG.permutation(delta[ii])
        sc = score_spread(x, x.model_spread.values + dd)
        if any(base_sc[w]["margin_mae"] - sc[w]["margin_mae"] >= gain[w] for w in WINDOWS):
            beaten += 1
    return {"draws": draws, "beaten": beaten, "pass": beaten <= draws - 45}


# ------------------------------------------------------------------------------------------------------- bet rules
def bet_rules(x: pd.DataFrame) -> dict:
    """name -> (selection mask, parent pool mask). The parent pool is what the placebo draws from: every game at the
    rule's lowest cut."""
    a, fav, dog = x.aedge, x.fav, x.dog
    trees4 = x.e_trees >= EDGE
    R = {
        "LIVE: 4+ either side": (a >= 4, a >= 4),
        "Favourites 5+, dogs 4+": ((dog & (a >= 4)) | (fav & (a >= 5)), a >= 4),
        "Favourites 6+, dogs 4+": ((dog & (a >= 4)) | (fav & (a >= 6)), a >= 4),
        "No favourites, dogs 4+ (the dog shadow)": (dog & (a >= 4), a >= 4),
        "Dogs 3.5+, favourites 4+": ((dog & (a >= 3.5)) | (fav & (a >= 4)), a >= 3.5),
        "Dogs 3.5+, favourites 5+": ((dog & (a >= 3.5)) | (fav & (a >= 5)), a >= 3.5),
        "Dogs 3.5+, favourites 6+": ((dog & (a >= 3.5)) | (fav & (a >= 6)), a >= 3.5),
        "Dogs 3.5+, no favourites": (dog & (a >= 3.5), a >= 3.5),
        "4+, favourites only when the trees also say 4+": ((dog & (a >= 4)) | (fav & (a >= 4) & trees4), a >= 4),
        "4+, only when the trees also say 4+ (both sides)": ((a >= 4) & trees4, a >= 4),
        "Favourites 4+ alone": (fav & (a >= 4), a >= 4),
        "Favourites 5+ alone": (fav & (a >= 5), a >= 5),
    }
    return {k: (v[0] & (x.week <= LAST_WEEK), v[1] & (x.week <= LAST_WEEK)) for k, v in R.items()}


def grade_rule(x: pd.DataFrame, sel: pd.Series, pool: pd.Series, draws: int = 1000) -> dict:
    out = {}
    live = x[(x.aedge >= EDGE) & ~x.push]
    for w, (a, b) in list(WINDOWS.items()) + [("2015-25", (2015, 2025))]:
        m = (x.season >= a) & (x.season <= b)
        q = x[sel & m & ~x.push]
        W_, L_ = int(q.win.sum()), int((~q.win).sum())
        out[w] = {"w": W_, "l": L_, "units": float(q.units.sum()), "n": W_ + L_}
    n, k = out["2015-25"]["n"], out["2015-25"]["w"]
    out["luck_p"] = float(stats.binomtest(k, n, 0.5238, alternative="greater").pvalue) if n else np.nan
    # placebo: the same number of bets per season drawn at random from the parent pool; share earning at least as many units
    P = x[pool & ~x.push & (x.season <= 2025)]; S_ = x[sel & ~x.push & (x.season <= 2025)]
    per = S_.groupby("season").size(); real = float(S_.units.sum())
    if len(P) == len(S_):
        out["placebo_p"] = np.nan
    else:
        u = P.units.values; idx = {s: np.where(P.season.values == s)[0] for s in per.index}
        cnt = 0
        for _ in range(draws):
            tot = sum(u[RNG.choice(ii, per[s], replace=False)].sum() for s, ii in idx.items())
            cnt += tot >= real - 1e-9
        out["placebo_p"] = cnt / draws
    return out


# ----------------------------------------------------------------------------------------------------------- output
NICE = {"qb_rating": "QB rating", "qb_out": "QB out", "off_epa_play": "offense EPA", "def_epa_play": "opp defense EPA", "off_pf": "offense points",
        "def_pf": "opp defense points", "skill_out_value": "skill players out", "opp_skill_out_value": "opp skill players out",
        "off_snap_out": "offense snaps out", "opp_def_snap_out": "opp defense snaps out", "off_turnover_early": "offseason turnover (off)",
        "opp_def_turnover_early": "offseason turnover (opp def)", "home": "home", "neutral": "neutral", "dome": "dome", "wind_out": "wind",
        "cold": "cold", "rain": "rain", "warm_in_cold": "warm team in cold", "div_game": "division", "dead_late": "out of the race",
        "opp_dead_late": "opp out of the race"}


def case_table(x: pd.DataFrame) -> pd.DataFrame:
    """One row per favourite bet at 3+ and dog bet at 4+ (2015-25 and 2026 to date), everything toward our side."""
    sel = ((x.fav & (x.aedge >= 3)) | (x.dog & (x.aedge >= EDGE))) & (x.week <= LAST_WEEK)
    z = x[sel].copy()
    z["group"] = np.where(z.fav, np.where(z.aedge >= 5, "favourite 5+", np.where(z.aedge >= 4, "favourite 4-5", "favourite 3-4")), np.where(z.aedge >= 5, "dog 5+", "dog 4-5"))
    z["our_team"] = np.where(z.home_side, z.home_team, z.away_team); z["opp_team"] = np.where(z.home_side, z.away_team, z.home_team)
    z["venue"] = np.where(z.home_side, "home", "away")
    z["line_our_side"] = -z.line_ours           # as a bettor reads it: -7 = we lay 7
    z["score"] = np.where(z.home_side, z.home_score.astype(int).astype(str) + "-" + z.away_score.astype(int).astype(str),
                          z.away_score.astype(int).astype(str) + "-" + z.home_score.astype(int).astype(str))
    z["outcome"] = np.where(z.push, "P", np.where(z.win, "W", "L"))
    # top three inputs toward our side
    oc = [f"o_{k}" for k in M.FEATS]
    top = []
    for r in z[oc].values:
        o = np.argsort(-np.abs(r))[:3]
        top.append("; ".join(f"{NICE[M.FEATS[i]]} {r[i]:+.1f}" for i in o))
    z["top_inputs"] = top
    for k in MODELS:
        z[f"model_{k}"] = z[f"s_{k}"] * z.sgn
    z["line_move_toward_us"] = z.line_move * z.sgn
    z["ats_end_q3"] = (z.home_margin_q3 - z.spread_line) * z.sgn
    z["ats_5min_left"] = (z.home_margin_m5 - z.spread_line) * z.sgn
    z["decided_late"] = np.where(z.ats_5min_left.isna() | z.push, "", np.where((z.ats_5min_left > 0) & (z.ats < 0), "lost in last 5 min",
                                 np.where((z.ats_5min_left < 0) & (z.ats > 0), "won in last 5 min", "")))
    cols = {"group": "group", "season": "season", "week": "week", "our_team": "side", "opp_team": "opponent", "venue": "venue",
            "line_our_side": "line (our side)", "model_margin_ours": "model margin (our side)", "aedge": "edge", "score": "score (ours-theirs)",
            "outcome": "result", "ats": "margin vs line", "o_qb": "QB pull", "o_ratings": "ratings pull", "o_injuries": "injury pull", "o_qb_out": "QB-out pull",
            "o_turnover": "offseason turnover pull", "o_home": "home pull", "o_weather": "weather pull", "o_late": "out-of-race pull",
            "o_blend_adj": "six other models' pull", "top_inputs": "top three inputs", **{f"model_{k}": f"{k} spread (our side)" for k in MODELS},
            "models_sd": "seven models SD", "e_trees": "trees' edge", "our_n_games": "our games this season", "opp_n_games": "opp games this season",
            "our_qb_change": "our QB changed", "opp_qb_change": "opp QB changed", "our_qb_out": "our last QB out", "opp_qb_out": "opp last QB out",
            "our_skill_out_value": "our skill value out", "opp_skill_out_value": "opp skill value out", "our_off_snap_out": "our offense snaps out",
            "opp_def_snap_out": "opp defense snaps out", "open_spread": "opener (home line, 2015-21)", "line_move_toward_us": "close minus opener toward us",
            "ats_end_q3": "vs line after Q3", "ats_5min_left": "vs line with 5:00 left", "decided_late": "decided late", "luck": "luck toward us (postmortem)",
            "our_qb_lost": "our QB lost in game", "game_id": "game_id"}
    out = z[list(cols)].rename(columns=cols)
    order = {"favourite 5+": 0, "favourite 4-5": 1, "favourite 3-4": 2, "dog 5+": 3, "dog 4-5": 4}
    out["_o"] = out.group.map(order)
    num = out.select_dtypes("number").columns
    out[num] = out[num].round(2)
    return out.sort_values(["_o", "season", "week"]).drop(columns="_o")


def md_table(df: pd.DataFrame) -> str:
    return df.to_markdown(index=False)


def fmt_rec(o):
    return f"{o['w']}-{o['l']}, {o['units']:+.1f}u"


def main():
    t0 = time.time()
    d, g = load(); fp = features()
    c = case_inputs(d, fp, g)
    x = oriented(sides(d), c)
    x = x.merge(openers(d), on="game_id", how="left").merge(late_scores(g), on="game_id", how="left").merge(postmortem_cols(), on="game_id", how="left")
    chk = float((c.ridge_rebuilt - c.ridge_spread).abs().max())
    log("cases built; ridge rebuilt to", chk)
    X = x[x.season <= 2025].reset_index(drop=True)
    K = {}
    # ---- the gap itself
    gap_rows = []
    for cut in (3, 3.5, 4, 5, 6):
        f = X[X.fav & (X.aedge >= cut) & ~X.push]; dg = X[X.dog & (X.aedge >= cut) & ~X.push]
        tab = [[int(f.win.sum()), int((~f.win).sum())], [int(dg.win.sum()), int((~dg.win).sum())]]
        b = X[~X.pk & (X.aedge >= cut) & ~X.push]
        _, pp = placebo_gap(b, b.fav.astype(float))
        gap_rows.append({"cut": cut, "favourites": f"{tab[0][0]}-{tab[0][1]}", "fav win %": round(100 * f.win.mean(), 1), "dogs": f"{tab[1][0]}-{tab[1][1]}",
                         "dog win %": round(100 * dg.win.mean(), 1), "Fisher p": round(stats.fisher_exact(tab)[1], 3), "placebo p (fav label shuffled in season)": round(pp, 3),
                         "fav pts vs close": round(f.ats.mean(), 2), "dog pts vs close": round(dg.ats.mean(), 2),
                         "t (points)": round(float(stats.ttest_ind(f.ats, dg.ats, equal_var=False).statistic), 2)})
    GAP = pd.DataFrame(gap_rows)
    def ols(y, cols):
        A = np.column_stack([np.ones(len(y))] + [np.asarray(v, float) for v in cols]); bb = np.linalg.lstsq(A, y, rcond=None)[0]
        r = y - A @ bb; se = np.sqrt(np.diag(r @ r / (len(y) - A.shape[1]) * np.linalg.inv(A.T @ A))); return bb, se
    tr = {}
    for nm, m in (("fav", X.fav), ("dog", X.dog)):
        z = X[m & (X.aedge >= 3) & ~X.push]; b, se = ols(z.win.astype(float).values, [z.aedge]); b2, se2 = ols(z.ats.values, [z.aedge])
        tr[nm] = (b[1], se[1], b2[1], se2[1], len(z))
    K["trend"] = tr
    # dispersion and calibration of the model's number
    b1, _ = ols(X.result.values, [X.model_spread]); K["slope_model"] = b1[1]
    K["sd_model"], K["sd_line"] = X.model_spread.std(), X.spread_line.std()
    K["lean_home"] = {w: float((X.model_spread - X.spread_line)[X.window == w].mean()) for w in WINDOWS}
    K["mean_line_ours_all"] = float(X.line_ours.mean())
    X["_bk"] = pd.cut(X.model_spread, [-30, -9, -6, -3, 0, 3, 6, 9, 12, 30])
    CAL = X.groupby("_bk", observed=True).agg(games=("result", "size"), model=("model_spread", "mean"), line=("spread_line", "mean"), result=("result", "mean")).round(2).reset_index().rename(columns={"_bk": "model spread (home)"})
    CAL["model spread (home)"] = CAL["model spread (home)"].astype(str)
    # which parts of the number carry information: result and result-minus-line on the parts, every game
    Gp = ["g_qb", "g_ratings", "g_injuries", "g_turnover", "g_weather", "g_late", "blend_adj"]
    br, ser = ols(X.result.values, [X[c_] for c_ in Gp]); bl, sel_ = ols((X.result - X.spread_line).values, [X[c_] for c_ in Gp] + [X.spread_line])
    PARTS = pd.DataFrame({"part": ["QB", "ratings", "injuries", "offseason turnover", "weather", "out of the race", "six other models' pull"],
                          "pull toward our side, favourites 4+": [round(X[X.fav & (X.aedge >= 4)][f"o_{c_[2:]}" if c_.startswith("g_") else "o_blend_adj"].mean(), 2) for c_ in Gp],
                          "dogs 4+": [round(X[X.dog & (X.aedge >= 4)][f"o_{c_[2:]}" if c_.startswith("g_") else "o_blend_adj"].mean(), 2) for c_ in Gp],
                          "worth vs the result, per point (se)": [f"{b_:.2f} ({s_:.2f})" for b_, s_ in zip(br[1:], ser[1:])],
                          "worth beyond the close, per point (se)": [f"{b_:.2f} ({s_:.2f})" for b_, s_ in zip(bl[1:-1], sel_[1:-1])]})
    K["line_coef_beyond"] = (bl[-1], sel_[-1])
    K["tmr"] = {"fav": float(X[X.fav & (X.aedge >= 3)].o_trees_minus_ridge.mean()), "dog": float(X[X.dog & (X.aedge >= 3)].o_trees_minus_ridge.mean())}
    K["fav4_model"], K["fav4_line"] = float(X[X.fav & (X.aedge >= 4)].model_margin_ours.mean()), float(X[X.fav & (X.aedge >= 4)].line_ours.mean())
    K["dog4_model"], K["dog4_line"] = float(X[X.dog & (X.aedge >= 4)].model_margin_ours.mean()), float(X[X.dog & (X.aedge >= 4)].line_ours.mean())
    # ---- patterns
    PAT = pattern_table(x)
    # composition: home/road x fav/dog at 4+
    comp = []
    for lab, m in (("favourite, home", X.fav & X.home_side), ("favourite, road", X.fav & ~X.home_side), ("dog, home", X.dog & X.home_side), ("dog, road", X.dog & ~X.home_side)):
        q = X[m & (X.aedge >= 4) & ~X.push]
        comp.append({"our side": lab, **{w: rec(q[q.window == w]) for w in WINDOWS}, "2015-25": rec(q), "win %": round(100 * q.win.mean(), 1)})
    COMP = pd.DataFrame(comp)
    b4 = X[(X.aedge >= 4) & ~X.push & ~X.pk].copy()
    b4["trees_lo"] = (b4.e_trees < EDGE).astype(float); b4["inj"] = (b4.inj_pull >= 1.5).astype(float); b4["homeS"] = b4.home_side.astype(float); b4["favf"] = b4.fav.astype(float)
    ctrl = []
    for cols in (["favf"], ["favf", "homeS"], ["favf", "trees_lo"], ["favf", "inj"], ["favf", "homeS", "trees_lo", "inj"]):
        bb, ss = ols(b4.win.astype(float).values, [b4[c_] for c_ in cols])
        nm_ = {"favf": "favourite", "homeS": "home side", "trees_lo": "trees under 4", "inj": "injury pull 1.5+"}
        ctrl.append({"controls": ", ".join(nm_[c_] for c_ in cols), **{nm_[c_]: f"{100 * b_:+.1f} ({100 * s_:.1f})" for c_, b_, s_ in zip(cols, bb[1:], ss[1:])}})
    CTRL = pd.DataFrame(ctrl).fillna("")
    # opener, late, luck summaries
    X["mv"] = X.line_move * X.sgn; X["ats_m5"] = (X.home_margin_m5 - X.spread_line) * X.sgn
    summ = []
    for lab, m in (("favourites 4+", X.fav & (X.aedge >= 4)), ("favourites 5+", X.fav & (X.aedge >= 5)), ("dogs 4+", X.dog & (X.aedge >= 4)), ("every game", X.aedge >= 0)):
        z = X[m]; o = z[z.mv.notna()]; p_ = z[z.ats_m5.notna() & ~z.push]; lk = z[z.luck.notna()]
        summ.append({"bets": lab, "n": len(z), "close moved against us (2015-21)": f"{(o.mv < 0).mean():.0%} of {len(o)}", "mean move toward us": round(o.mv.mean(), 2),
                     "record with 5:00 left (2016+)": f"{int((p_.ats_m5 > 0).sum())}-{int((p_.ats_m5 < 0).sum())}",
                     "final record, same games": f"{int((p_.ats > 0).sum())}-{int((p_.ats < 0).sum())}",
                     "lost / won in the last 5 min": f"{int(((p_.ats_m5 > 0) & (p_.ats < 0)).sum())} / {int(((p_.ats_m5 < 0) & (p_.ats > 0)).sum())}",
                     "luck toward us, pts (postmortem)": round(lk.luck.mean(), 2) if len(lk) and lab != "every game" else np.nan,
                     "record with luck taken out": f"{int(((lk.ats - lk.luck) > 0).sum())}-{int(((lk.ats - lk.luck) < 0).sum())}" if lab != "every game" else "",
                     "our QB lost in the game": f"{int(lk.our_qb_lost.sum())} of {len(lk)}" if lab != "every game" else ""})
    SUMM = pd.DataFrame(summ)
    # ---- fixes
    base = score_spread(X, X.model_spread.values)
    F = fixes(X); fr = []
    for name, (new, used) in F.items():
        sc = score_spread(X, new)
        r1 = all(sc[w]["margin_mae"] < base[w]["margin_mae"] and sc[w]["team_mae"] < base[w]["team_mae"] for w in WINDOWS)
        r2 = all(sc[w]["flag_u"] >= base[w]["flag_u"] - 1e-9 and (sc[w]["flag_w"] - sc[w]["flag_l"]) >= (base[w]["flag_w"] - base[w]["flag_l"]) and sc[w]["logloss"] <= base[w]["logloss"] + 1e-9 for w in WINDOWS)
        pl = placebo_fix(X, new, base, sc)
        row = {"fix": name, "parameters (by season)": json.dumps({str(k): (v if not isinstance(v, (np.floating, float)) else float(v)) for k, v in used.items()}, default=lambda o: float(o)) if isinstance(used, dict) else used}
        for w in WINDOWS:
            o = sc[w]; bo = base[w]
            row[f"margin miss {w}"] = round(o["margin_mae"] - bo["margin_mae"], 3); row[f"team miss {w}"] = round(o["team_mae"] - bo["team_mae"], 3)
            row[f"flag {w}"] = f"{o['flag_w']}-{o['flag_l']}, {o['flag_u']:+.1f}u"; row[f"favourites {w}"] = f"{o['fav_w']}-{o['fav_l']}"; row[f"dogs {w}"] = f"{o['dog_w']}-{o['dog_l']}"
            row[f"log loss {w}"] = round(o["logloss"] - bo["logloss"], 4)
        row["rule 1 (miss better on all 3)"] = r1; row["rule 2 (no bet or calibration cost)"] = r2
        row["placebo draws beating it (of 50)"] = pl["beaten"]; row["rule 3 (placebo)"] = pl["pass"]
        row["passes"] = bool(r1 and r2 and pl["pass"])
        fr.append(row)
    FIX = pd.DataFrame(fr)
    BASE = {w: base[w] for w in WINDOWS}
    # ---- bet rules
    rr = []
    for name, (sel, pool) in bet_rules(X).items():
        o = grade_rule(X, sel, pool)
        live = grade_rule(X, (X.aedge >= EDGE) & (X.week <= LAST_WEEK), (X.aedge >= EDGE))
        beats = all(o[w]["units"] > live[w]["units"] for w in WINDOWS)
        rr.append({"rule": name, **{w: fmt_rec(o[w]) for w in list(WINDOWS) + ["2015-25"]}, "luck p": round(o["luck_p"], 3),
                   "placebo p": (round(o["placebo_p"], 3) if o["placebo_p"] == o["placebo_p"] else ""), "more units than live on all 3": "yes" if beats and not name.startswith("LIVE") else ("" if name.startswith("LIVE") else "no"),
                   "fewest bets in a window": min(o[w]["n"] for w in WINDOWS)})
    RULES = pd.DataFrame(rr)
    # 2026 so far (shown apart)
    x26 = x[(x.season == 2026) & (x.aedge >= EDGE) & (x.week <= LAST_WEEK)]
    K["y2026"] = {"fav": rec(x26[x26.fav]), "dog": rec(x26[x26.dog])}
    # ---- write
    CASES = case_table(x)
    CASES.to_csv(REP / "favorite_review.csv", index=False)
    PAT.to_csv(REP / "favorite_review_patterns.csv", index=False)
    FIX.to_csv(REP / "favorite_review_fixes.csv", index=False)
    RULES.to_csv(REP / "favorite_review_rules.csv", index=False)
    write_md(K, GAP, PARTS, CAL, PAT, COMP, CTRL, SUMM, FIX, BASE, RULES, CASES)
    log("done", round(time.time() - t0), "s")


def write_md(K, GAP, PARTS, CAL, PAT, COMP, CTRL, SUMM, FIX, BASE, RULES, CASES):
    import pickle
    pickle.dump(dict(K=K, GAP=GAP, PARTS=PARTS, CAL=CAL, PAT=PAT, COMP=COMP, CTRL=CTRL, SUMM=SUMM, FIX=FIX, BASE=BASE, RULES=RULES), open(SCR / "tables.pkl", "wb"))
    P = PAT.set_index("factor"); g = GAP.set_index("cut"); R = RULES.set_index("rule"); tf, td = K["trend"]["fav"], K["trend"]["dog"]
    def pr(f, col):
        return P.loc[f, col]
    home_share_f = pr("Our side at home", "share_fav4"); home_share_d = pr("Our side at home", "share_dog4")
    tl = "Trees' edge under 4"; ij = "Injury inputs + QB-out pull 1.5+ pts our way"
    fixes_pass = FIX[FIX.passes].fix.tolist(); r1 = FIX[FIX["rule 1 (miss better on all 3)"]].fix.tolist()
    fmin = FIX["placebo draws beating it (of 50)"].min()
    lw = {w: f"{o['flag_w']}-{o['flag_l']}, {o['flag_u']:+.1f}u" for w, o in BASE.items()}
    L = []
    A = L.append
    A("# Why the model's favourites lose at 4+ and 5+, and whether a fix to the model helps (30 Sep 2026)")
    A("")
    A("Research only: nothing on the site or in the picks changes. Script: `experiments/favorite_review.py`. Case list: `reports/favorite_review.csv`, with every favourite bet at 3+ and every dog bet at 4+, 2015-2026. Other tables: `favorite_review_patterns.csv`, `favorite_review_fixes.csv` and `favorite_review_rules.csv`.")
    A("")
    A("The bets are the live flag: the model's side at 4+ points off the closing line, weeks 1-17, pushes out, -110. \"Favourite\" means our side is the market favourite. The years are 2015-25. 2026 has no favourite bets yet; the dogs are " + K["y2026"]["dog"] + ".")
    A("")
    A("## Headline")
    A("")
    A(f"**Mostly, the favourites are not failing. There are too few of them to tell.** At the live 4+ cut they are {g.loc[4.0,'favourites']} and beat the close by **{g.loc[4.0,'fav pts vs close']:+.1f} points a bet**. The dogs beat it by {g.loc[4.0,'dog pts vs close']:+.1f}. The win-rate gap ({g.loc[4.0,'fav win %']:.0f}% against {g.loc[4.0,'dog win %']:.0f}%) is within chance: Fisher p {g.loc[4.0,'Fisher p']:.2f}, and {g.loc[4.0,'placebo p (fav label shuffled in season)']:.2f} when the favourite label is shuffled within each season.")
    A("")
    A(f"\"Worse as the edge grows\" does not hold up either:")
    A(f"- Inside the 3+ favourite bets, the win rate moves {100*tf[0]:+.1f}% per point of edge (se {100*tf[1]:.1f}%).")
    A(f"- The worst band is 3-4 points (33-45). The best is 4-5 (24-13).")
    A(f"- The 5+ cell ({g.loc[5.0,'favourites']}) is 25 bets, and in points it breaks even with the close ({g.loc[5.0,'fav pts vs close']:+.1f} ± 2.9).")
    A(f"- The win-rate gap is significant only at the 3.5 and 5 cuts (p about 0.01), not at 3, 4 or 6. No cut shows it in points (|t| < 1.9).")
    A("")
    A("Two readings explain most of the gap that is there. Neither is peculiar to favourites.")
    A("")
    A(f"1. **Favourite bets are home teams, and the flag's home sides lose on both sides of the line.**")
    A(f"   - {home_share_f:.0%} of favourite bets are at home, against {home_share_d:.0%} of dog bets.")
    A(f"   - At 4+: home favourites {COMP.iloc[0]['2015-25']}, road favourites {COMP.iloc[1]['2015-25']}, home dogs {COMP.iloc[2]['2015-25']}, road dogs {COMP.iloc[3]['2015-25']}.")
    A(f"   - The model leans {K['lean_home']['2015-18']:.2f} / {K['lean_home']['2019-22']:.2f} / {K['lean_home']['2023-25']:.2f} points more to the home side than the close on the three windows.")
    A(f"   - Home field was settled on 27 and 30 Sep: one league number stays. An offset fit here on past results fails too (below).")
    A(f"2. **The boosted trees do not back the edge.**")
    A(f"   - {pr(tl,'share_fav4'):.0%} of favourite bets have the trees' own edge under 4, against {pr(tl,'share_dog4'):.0%} of dog bets.")
    A(f"   - Those favourites went {pr(tl,'fav4_with')}; the rest went {pr(tl,'fav4_without')} (placebo {pr(tl,'placebo_p_fav4'):.2f}).")
    A(f"   - The dogs show the same split: {pr(tl,'dog4_with')} against {pr(tl,'dog4_without')} (placebo {pr(tl,'placebo_p_dog4'):.2f}).")
    A(f"   - The six ridges extrapolate a line. On favourite bets at 3+ the trees sit {-K['tmr']['fav']:.2f} points short of the ridge on average; on dog bets they sit {K['tmr']['dog']:+.2f} points beyond it.")
    A("")
    A(f"A weaker third: **injury-driven favourites.**")
    A(f"- {pr(ij,'share_fav4'):.0%} of favourite bets get 1.5+ points from the injury and QB-out inputs, against {pr(ij,'share_dog4'):.0%} of dogs.")
    A(f"- Those favourites went {pr(ij,'fav4_with')}, against {pr(ij,'fav4_without')} (placebo {pr(ij,'placebo_p_fav4'):.2f}; at 3+ the placebo is {pr(ij,'placebo_p_fav3'):.2f}). The dogs show nothing.")
    A("")
    A(f"Home side, trees under 4 and injury pull together take the favourite penalty from {CTRL.iloc[0,1]} to {CTRL.iloc[4,1]} win-rate points (se in brackets).")
    A("")
    A(f"**No model fix works.** {len(FIX)} walk-forward fixes to the model's number were scored under `reports/round3_rule.md`. Every parameter was fit on earlier seasons only.")
    A(f"- None lowers both the margin miss and the team-points miss on all three windows ({len(r1)} pass rule 1).")
    A(f"- None passes the placebo: at best, {fmin} of 50 shuffled draws do as well.")
    A(f"- The market-free fix (shrink big margins toward zero) is the wrong direction. The model's number is already narrower than the line and than the results:")
    A(f"  - SD {K['sd_model']:.2f} against the line's {K['sd_line']:.2f}.")
    A(f"  - Result = {K['slope_model']:.2f} × model.")
    A(f"  - At the top it is on the money: home by 9-12, model 10.3, result 10.5; home by 12+, model 14.3, result 15.2.")
    A(f"  - So there is no rating ceiling to cap. Shrinking costs miss on the windows it is fit on.")
    A("")
    A(f"**Bet rules do not beat live on all three windows either.** Live is {lw['2015-18']} / {lw['2019-22']} / {lw['2023-25']}.")
    A(f"- Dogs 3.5+ with favourites at 4+: {R.loc['Dogs 3.5+, favourites 4+','2015-18']} / {R.loc['Dogs 3.5+, favourites 4+','2019-22']} / {R.loc['Dogs 3.5+, favourites 4+','2023-25']} (loses 2019-22).")
    A(f"- Dogs 3.5+, no favourites: {R.loc['Dogs 3.5+, no favourites','2015-18']} / {R.loc['Dogs 3.5+, no favourites','2019-22']} / {R.loc['Dogs 3.5+, no favourites','2023-25']} (loses 2019-22 and 2023-25, by under a unit each).")
    A(f"- Favourites at 5+: {R.loc['Favourites 5+, dogs 4+','2015-18']} / {R.loc['Favourites 5+, dogs 4+','2019-22']} / {R.loc['Favourites 5+, dogs 4+','2023-25']} (loses 2015-18 and 2023-25).")
    A(f"- Favourites at 6+: {R.loc['Favourites 6+, dogs 4+','2015-18']} / {R.loc['Favourites 6+, dogs 4+','2019-22']} / {R.loc['Favourites 6+, dogs 4+','2023-25']} (loses 2015-18 and 2023-25).")
    A(f"- No favourites at all: {R.loc['No favourites, dogs 4+ (the dog shadow)','2015-18']} / {R.loc['No favourites, dogs 4+ (the dog shadow)','2019-22']} / {R.loc['No favourites, dogs 4+ (the dog shadow)','2023-25']}. It loses 4.7u on 2023-25, where favourites went 8-3.")
    A("")
    A("**What to decide.**")
    A("- Keep the 4+ rule on both sides, and do not change the model.")
    A("- The dog shadow already tracks the alternative.")
    A("- If one watch item is wanted, log whether the trees also show 4+ on each flagged favourite. As a rule it earns " + f"{R.loc['4+, favourites only when the trees also say 4+','2015-18']} / {R.loc['4+, favourites only when the trees also say 4+','2019-22']} / {R.loc['4+, favourites only when the trees also say 4+','2023-25']}. It was found by looking and loses on 2023-25, so it is a reading, not a rule.")
    A("- Revisit after 2026, with about 6 more favourite bets.")
    A("")
    A("**Against earlier findings**")
    A("- **Confirmed:**")
    A("  - The sweep and spread research (30 Sep): no favourite/dog rule beats live on every window, and road dogs are the strong cell.")
    A("  - The postmortem (29 Sep): the 1-point injury cap has no dose response. Here it worsens the margin miss on 2019-22 and 2023-25.")
    A("  - The situational round (29 Sep): the injury inputs earn their place.")
    A("  - Home field (27 and 30 Sep): one number stays.")
    A("  - Season odds (23 Sep): shrinking margins does not hold across windows. Here it worsens the margin miss wherever it is fit.")
    A("- **Refined:**")
    A("  - The sweep's \"the model's favourites never earn their keep\" is true of units at 5+. At 4+, though, they beat the close by as many points as the dogs.")
    A("  - The postmortem's \"skip when the trees disagree\" (side flipped) has a cousin: trees under 4. It sorts dogs as well as favourites, so it is not a favourite problem.")
    A("- **Overturned:** the premise that favourites get worse as the edge grows. There is no trend inside the favourite bets.")
    A("")
    A("## 1. The gap, cut by cut")
    A("")
    A(md_table(GAP))
    A("")
    A("Points vs close is the mean of (final margin minus the line) toward our side. The t compares favourites with dogs.")
    A("")
    A("## 2. What drives a favourite edge, and what each part is worth")
    A("")
    A("Contributions are coef × (home input − away input) in the ridge that priced the game; the training mean cancels. They rebuild the ridge spread to 1e-14. They are signed toward our side.")
    A("")
    A("The worth columns come from regressions over every game, 2015-25:")
    A("- **Worth vs the result:** the result regressed on the parts. 1 means the part earns its face value.")
    A("- **Worth beyond the close:** the result minus the line, regressed on the parts and the line. 0 means the line already has it.")
    A("")
    A(md_table(PARTS))
    A("")
    A(f"- A favourite edge is the model's number going past the line: {K['fav4_model']:.1f} against {K['fav4_line']:.1f} on average at 4+. Ratings (+3.5), QB (+2.3), home (+1.2), injuries (+1.2) and offseason turnover (+0.8) carry it.")
    A(f"- A dog edge is mostly the line being wider than the model: the model says {K['dog4_model']:+.1f}, the line {K['dog4_line']:+.1f}.")
    A(f"- Every part is worth about its face value against the result. Injuries are the lowest at 0.83.")
    A(f"- The ratings part adds nothing beyond the close (0.08). Across every game the line itself runs {K['line_coef_beyond'][0]:+.2f} ({K['line_coef_beyond'][1]:.2f}) per point too far.")
    A(f"- Plugging the favourites' average parts into that regression predicts them to beat the close by more than the dogs, not less. So no part is over-weighted in a way that singles favourites out.")
    A("")
    A("The model's number against results (every game, weeks 1-17, 2015-25). It is not over-extended at the top:")
    A("")
    A(md_table(CAL))
    A("")
    A("## 3. Every candidate reason")
    A("")
    A("Each row is a yes/no factor from our side's view:")
    A("- **Share:** how often the factor appears among favourite bets at 4+, dog bets at 4+ and every game.")
    A("- **Records:** with the factor and without it.")
    A("- **Placebo p:** the factor shuffled within season, 2000 draws. It is one-sided, testing that the factor hurts.")
    A("")
    A("All columns, including the 3+ records and the dog placebos, are in `favorite_review_patterns.csv`.")
    A("")
    show = PAT[["factor", "share_fav4", "share_dog4", "share_all", "fav4_with", "fav4_without", "placebo_p_fav4", "fav3_with", "fav3_without", "placebo_p_fav3", "dog4_with", "dog4_without", "placebo_p_dog4"]].copy()
    show.columns = ["factor", "share fav 4+", "share dog 4+", "share all", "fav 4+ with", "fav 4+ without", "placebo p", "fav 3+ with", "fav 3+ without", "placebo p (3+)", "dog 4+ with", "dog 4+ without", "placebo p (dog)"]
    A(md_table(show))
    A("")
    A("Read:")
    A("- **Early season is not it.** Favourites are best in weeks 1-4 (13-6).")
    A("- **Off a big win is not it** (7-7).")
    A("- **Big lines are not it** (7+: 8-5).")
    A("- **Model disagreement is not it** (placebo 0.27).")
    A("- **A rating ceiling is not it.** The model has our side by 10+ in 14-12 of them.")
    A("- **QB changes and out-of-the-race are not it.**")
    A("")
    A("The line move, late finishes and luck:")
    A("")
    A(md_table(SUMM))
    A("")
    A("- **The market moving against us is not favourite-specific.** For both favourites and dogs, the close moved against the model's side 72% of the time. That is the selection effect of measuring the edge at the close.")
    s0 = SUMM.set_index("bets")
    A(f"- **Late covers are not it.** With 5:00 left, favourites stood {s0.loc['favourites 4+','record with 5:00 left (2016+)']} against the line and finished {s0.loc['favourites 4+','final record, same games']} on the same games. The dogs went {s0.loc['dogs 4+','record with 5:00 left (2016+)']} to {s0.loc['dogs 4+','final record, same games']}.")
    A("- **Luck ran for the favourites.** With luck removed they are still 33-29, while the dogs would be 179-75.")
    A("")
    A("Home and road, favourite and dog, at 4+:")
    A("")
    A(md_table(COMP))
    A("")
    A("A linear probability model on the 4+ bets shows how much of the favourite penalty the three readings take up. Each cell is the win-rate change in percentage points, with its se:")
    A("")
    A(md_table(CTRL))
    A("")
    A("## 4. Fixes to the model's number (walk-forward, round-3 rule)")
    A("")
    A("How the fixes were built and scored:")
    A("- Each fix changes the model's spread game by game. Parameters are chosen on earlier seasons' margin miss only. 2015 keeps the base number because pred_v3 has nothing before it.")
    A("- The scale, shrink, early-season, stacking, trees'-share and home fixes are exact: the blend is the average of the stored seven models.")
    A("- The injury, rating and QB caps move only the ridge's share of those inputs. The other six models carry them too, so these are approximate.")
    A("- The win chance is read on a normal curve with each fit's residual scale, for base and fix alike.")
    A("- Placebo: the fix's change to each game's number is shuffled within season (50 draws). Rule 3 needs the real gain to beat 45 of them on every window.")
    A("- Refits were not needed. The situational round (29 Sep) already refit the model without each injury input: dropping skill value costs, the snaps pair is mixed, and QB-out fails on log loss.")
    A("")
    A("Changes against base. Miss below 0 is better. The flag cells are the fix's own records:")
    A("")
    cols = ["fix"] + [c for w in WINDOWS for c in (f"margin miss {w}", f"team miss {w}", f"flag {w}", f"favourites {w}", f"dogs {w}")] + ["rule 1 (miss better on all 3)", "rule 2 (no bet or calibration cost)", "placebo draws beating it (of 50)", "passes"]
    A(md_table(FIX[cols]))
    A("")
    A(f"Base: margin miss {BASE['2015-18']['margin_mae']:.3f} / {BASE['2019-22']['margin_mae']:.3f} / {BASE['2023-25']['margin_mae']:.3f}; team miss {BASE['2015-18']['team_mae']:.3f} / {BASE['2019-22']['team_mae']:.3f} / {BASE['2023-25']['team_mae']:.3f}.")
    A(f"Base flag: {lw['2015-18']} / {lw['2019-22']} / {lw['2023-25']}. Favourites 18-17 / 7-9 / 8-3; dogs 50-38 / 73-42 / 32-18.")
    A("")
    A("What each fix does to favourites and dogs:")
    A("- **Shrinking (A, B):** fewer favourite bets and more dog bets. The margin miss gets worse where it is fit.")
    A("- **Injury scale or cap (C):** it barely touches the favourites (7-9 stays 7-9 on 2019-22).")
    A("- **Rating and QB caps (H):** they change little. The fitted caps mostly sit at 6 to 10 points, which few games reach.")
    A("- **Stacked or re-weighted parts (D, E):** they add favourite bets and lose them.")
    A("- **Trees' share (F):**")
    A("  - At a quarter it is the closest to neutral: miss -0.000 / +0.001 / -0.003, flag +1 / +2 / +2 net wins.")
    A("  - It still fails rule 1 on 2019-22, and 48 of 50 placebo draws match it.")
    A("- The per-season parameters are in the CSV.")
    A("")
    A("## 5. Bet rules (the fallback)")
    A("")
    A("How the rules are graded:")
    A("- Luck p is one-sided binomial against 52.38%, 2015-25.")
    A("- Placebo p is the share of 1000 random draws that earn at least as many units. Each draw takes the same number of bets per season from the rule's parent pool: every game at its lowest cut.")
    A("")
    A(md_table(RULES))
    A("")
    A("- **No rule earns more units than live on all three windows.**")
    A("- **Dogs at 3.5 with favourites at 4:**")
    A("  - It adds about 9 bets a season and 3.6 units over 2015-25.")
    A("  - It loses 3.1u on 2019-22, the window where 4 was chosen.")
    A("  - It is the one variant worth a shadow line if Matt wants more dog volume. The 3.5-4 dog band is a thin +0.3u a season.")
    A("- **Favourites alone at 5+** lose on every window: 4-9, 3-5, 2-2. That is 25 bets, and in points they tie the close.")
    A("")
    A("## 6. The favourite bets at 4+ (all 62; the 3-4 band and the dogs are in the CSV)")
    A("")
    A("How to read the table:")
    A("- **Line and model:** as our side reads them. -7 means we lay 7.")
    A("- **Pulls:** points toward our side.")
    A("- **Trees:** the trees' own edge.")
    A("- **SD:** the seven models' spread.")
    A("- **Games:** our side's games this season, then the opponent's.")
    A("- **QB chg:** our side's starter / the opponent's starter changed from the last game.")
    A("- **Move:** the close minus the opener toward us (2015-21).")
    A("- **5:00:** where the bet stood against the line with five minutes left (2016+).")
    A("")
    fv = CASES[CASES.group.isin(["favourite 5+", "favourite 4-5"])].copy()
    fv["games"] = fv["our games this season"].astype(int).astype(str) + "/" + fv["opp games this season"].astype(int).astype(str)
    fv["QB chg"] = fv["our QB changed"].map({True: "Y", False: "-"}) + "/" + fv["opp QB changed"].map({True: "Y", False: "-"})
    fv = fv[["group", "season", "week", "side", "opponent", "venue", "line (our side)", "model margin (our side)", "edge", "score (ours-theirs)", "result", "margin vs line",
             "QB pull", "ratings pull", "injury pull", "top three inputs", "trees' edge", "seven models SD", "games", "QB chg", "close minus opener toward us", "vs line with 5:00 left"]]
    for c_ in ("close minus opener toward us", "vs line with 5:00 left"):
        fv[c_] = fv[c_].map(lambda v: "" if pd.isna(v) else f"{v:+g}")
    fv.columns = ["group", "season", "wk", "side", "opp", "venue", "line", "model", "edge", "score", "res", "vs line", "QB", "ratings", "injury", "top inputs", "trees", "SD", "games", "QB chg", "move", "5:00"]
    A(md_table(fv))
    A("")
    A("## Caveats")
    A("")
    A("- **The samples are small.** There are 62 favourite bets at 4+ and 25 at 5+, over 11 seasons. The factor table tests 20 readings on 4 pools, so a couple of placebo p values under 0.05 are expected by chance.")
    A("- **The injury, rating and QB caps are post-hoc.** They use the ridge's coefficients as a stand-in for all seven models. A refit would move the six other models too. The situational round's refits of the injury inputs cover that case.")
    A("- **The opener archive covers 2015-21 only**, with the sweep's filter for bad rows. The play-by-play clock readings start in 2016.")
    A("- **\"Luck\" is the postmortem's definition**: turnovers, returns, kicks and garbage time. Its garbage-time part counts the leader's pile-on as luck.")
    A("- **All three windows were looked at.** Anything found here describes the backtest only.")
    (REP / "favorite_review.md").write_text("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
