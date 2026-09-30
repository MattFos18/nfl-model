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
