"""NFL Model 3.0: points for and against from opponent-adjusted ratings, walk-forward.

Pipeline
  1. ratings.build_features gives every team-game the ratings (EPA per play, pass and rush EPA, success rate,
     adjusted points, pace) each side carried into the game, the starting QB's rating, and the situation.
  2. A ridge regression turns those into expected points for the team. It is refit for every season on all
     seasons before it (2013 onward), so a 2023 prediction has never seen a 2023 game.
  3. The two expected scores give the margin and total. The margin distribution is a normal centred on the
     predicted margin, reshaped by key-number weights estimated from training games (3, 7, 6, 10 and so on
     get their real share), which gives win, cover and over probabilities at any line.
  4. Edges are model line minus closing line. Bet rules start at the sheet's 3 (spread) and 4 (total) and
     are tuned on 2019 to 2022 only; 2023 to 2025 is the held-out test.
"""
from __future__ import annotations
import numpy as np, pandas as pd
from pathlib import Path
from scipy.stats import norm
from sklearn.linear_model import Ridge
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from threadpoolctl import threadpool_limits
import hashlib, json

ROOT = Path(__file__).resolve().parent.parent
OUT, REP = ROOT / "data" / "processed", ROOT / "reports"
# The input set, 22 Sep 2026: twelve inputs, each with one plain meaning. The offense's EPA-per-play and points ratings, the
# opponent defense's two ratings, the starting QB (and whether last game's starter is out), and six situation inputs (home, neutral,
# dome, wind, cold, rain). The pass/rush
# splits, pace, the other-side-of-the-ball terms, the opponent's QB, rest, division and primetime were dropped after a walk-forward
# test showed the same accuracy without them (reports/input_set_experiments.csv); several of them could not be read on their own
# (the rest pair only ever appeared together; pass and rush EPA overlap EPA per play).
RATING_FEATS = [f"{s}_{st}" for st in ["epa_play", "pf"] for s in ["off", "def"]]
SIT_FEATS = ["home", "neutral", "dome", "wind_out", "cold", "rain", "warm_in_cold", "div_game"]   # rain, warm_in_cold and div_game added 22 Sep 2026 (each lowered the miss on both windows)
INJ_FEATS = ["skill_out_value", "opp_skill_out_value",   # player model, phase 2 (22 Sep 2026): value lost to RB/WR/TE listed out, own and opponent
             "off_snap_out", "opp_def_snap_out"]          # phase 3 (22 Sep 2026): share of last game's offensive snaps now out; the opponent's defensive snaps out
# teams whose home is warm or indoors, for the "warm or dome team playing in the cold" flag (static; a team's climate does not change)
WARM_OR_DOME = {"MIA", "TB", "JAX", "ARI", "LAC", "LA", "LV", "SF", "HOU", "NO", "ATL", "DAL", "CAR", "TEN", "DET", "MIN", "IND"}
CONT_FEATS = ["off_turnover_early", "opp_def_turnover_early"]   # offseason turnover, weeks 1 to 8 (23 Sep 2026): share of last season's snaps gone, own offense and the opponent's defense
EARLY_WEEKS = 8
LATE_FEATS = ["dead_late", "opp_dead_late"]   # out of the race (23 Sep 2026): from Week 12, a team whose win rate through the previous week is 40% or under, own and opponent
LATE_WEEK, DEAD_PCT = 12, 0.40
RAIN_FC = 50.0       # the totals equation's rain input: forecast chance of rain 50%+ (1 Oct 2026, see TOTAL_FEATS)
COLD_F = 35.0        # the cold flag: kickoff temperature under this, outdoors
RIDGE = 10.0         # the points regression's ridge penalty (reports/equation_checks.csv: 1 to 100 within 0.001)
TRAIN_FROM = 2013    # the first season every fit trains on
FEATS = RATING_FEATS + ["qb_rating"] + SIT_FEATS + ["qb_out"] + INJ_FEATS + CONT_FEATS + LATE_FEATS
# the wider set the model carried before, kept for the ablation and the experiments
FEATS_WIDE = [f"{s}_{st}" for st in ["epa_play", "pass_epa", "rush_epa", "pf", "plays"] for s in ["off", "def"]] + ["qb_rating", "opp_qb_rating", "opp_off_epa_play", "own_def_epa_play", "opp_off_plays"] + \
             ["home", "neutral", "rest_short", "rest_long", "opp_rest_short", "opp_rest_long", "dome", "wind_out", "cold", "div_game", "primetime", "qb_out"]
MARGIN_RANGE = np.arange(-60, 61)


TREND_FEATS = ["team_home_edge", "h2h_cover", "coach_ats", "qb_ats", "off_loss", "ref_over", "ref_tot", "ref_home_cover", "ref_pen", "sun_late",
               "body_clock_early", "cold_edge", "wind_edge", "off_home_split", "off_starters_out", "def_starters_out", "qb_out",
               "rain", "snow", "travel_miles", "tz_shift", "ol_out", "off_snap_out", "def_snap_out", "off_continuity", "def_continuity"]


def with_trends(f: pd.DataFrame, trends: pd.DataFrame | None = None, games: pd.DataFrame | None = None) -> pd.DataFrame:
    """Merge the as-of trend and injury table (trends.py) onto the feature table; missing values become 0 / league.
    trends / games stand in for the stored trends_asof and games tables (the leak checks pass corrupted copies)."""
    t = pd.read_parquet(OUT / "trends_asof.parquet") if trends is None else trends
    t = t[["game_id", "team"] + [c for c in TREND_FEATS if c in t.columns]]   # a column the table predates is filled below (28 Sep 2026: ref_tot)
    f = f.merge(t, on=["game_id", "team"], how="left")
    fill = {"ref_over": 0.5, "ref_home_cover": 0.5, "off_continuity": 0.83, "def_continuity": 0.83}   # continuity: league-typical share when unknown
    for c in TREND_FEATS:
        f[c] = f[c].fillna(fill.get(c, 0.0)) if c in f.columns else fill.get(c, 0.0)
    f["home_edge_in_play"] = f.team_home_edge * f.home            # own edge counts only at home
    # player model: value lost to skill players listed out (players.py), own offense and the opponent's
    pi = OUT / "player_injury.parquet"
    if pi.exists():
        iv = pd.read_parquet(pi)[["game_id", "team", "skill_out_value"]]
        f = f.merge(iv, on=["game_id", "team"], how="left")
        f = f.merge(iv.rename(columns={"team": "opp", "skill_out_value": "opp_skill_out_value"}), on=["game_id", "opp"], how="left")
    # the opponent's defensive absences (snap-weighted), from the same trends table joined on the opponent
    od = t.rename(columns={"team": "opp", "def_snap_out": "opp_def_snap_out"})[["game_id", "opp", "opp_def_snap_out"]] if "def_snap_out" in t.columns else None
    if od is not None:
        f = f.merge(od, on=["game_id", "opp"], how="left")
    if "def_continuity" in t.columns:
        f = f.merge(t.rename(columns={"team": "opp", "def_continuity": "opp_def_continuity"})[["game_id", "opp", "opp_def_continuity"]], on=["game_id", "opp"], how="left")
    f["opp_def_continuity"] = f["opp_def_continuity"].fillna(0.83) if "opp_def_continuity" in f.columns else 0.83
    for c in INJ_FEATS:
        f[c] = f[c].fillna(0.0) if c in f.columns else 0.0
    # record through the previous week, from the played regular-season games (for the out-of-the-race inputs)
    rec = record_before(pd.read_parquet(OUT / "games.parquet") if games is None else games)
    f["pct_before"] = [rec.get((k, t), 0.5) for k, t in zip(f.game_id, f.team)]
    f["opp_pct_before"] = [rec.get((k, t), 0.5) for k, t in zip(f.game_id, f.opp)]
    return f


def record_before(games: pd.DataFrame) -> dict:
    """(game_id, team) -> the team's win rate in that season's regular season before that game (0.5 before its first)."""
    r = games[(games.game_type == "REG") & games.home_score.notna()][["game_id", "season", "week", "home_team", "away_team", "home_score", "away_score"]]
    long = pd.concat([r.assign(team=r.home_team, win=(r.home_score > r.away_score).astype(float)), r.assign(team=r.away_team, win=(r.away_score > r.home_score).astype(float))]).sort_values(["season", "team", "week"])
    long["wb"] = long.groupby(["season", "team"]).win.cumsum() - long.win; long["gb"] = long.groupby(["season", "team"]).cumcount()
    long["pct"] = np.where(long.gb > 0, long.wb / long.gb.clip(lower=1), 0.5)
    played = dict(zip(zip(long.game_id, long.team), long.pct))
    # unplayed games (this week's): the team's record after its last played game of the season
    last = long.sort_values(["season", "team", "week"]).groupby(["season", "team"]).agg(wins=("win", "sum"), n=("win", "count"))
    up = games[games.home_score.isna() & (games.game_type == "REG")]
    for r2 in up.itertuples():
        for t in (r2.home_team, r2.away_team):
            if (r2.season, t) in last.index:
                w, n = last.loc[(r2.season, t)]; played[(r2.game_id, t)] = float(w / n) if n else 0.5
    return played


def prep(f: pd.DataFrame) -> pd.DataFrame:
    f = f.copy()
    early = (f.week <= EARLY_WEEKS).astype(float)
    late = (f.week >= LATE_WEEK).astype(float)
    f["dead_late"] = late * (f["pct_before"] <= DEAD_PCT).astype(float) if "pct_before" in f.columns else 0.0
    f["opp_dead_late"] = late * (f["opp_pct_before"] <= DEAD_PCT).astype(float) if "opp_pct_before" in f.columns else 0.0
    f["off_turnover_early"] = (1.0 - f["off_continuity"]) * early if "off_continuity" in f.columns else 0.0
    f["opp_def_turnover_early"] = (1.0 - f["opp_def_continuity"]) * early if "opp_def_continuity" in f.columns else 0.0
    f["rest_short"] = (f.rest <= 5).astype(float)          # Thursday game
    f["rest_long"] = (f.rest >= 10).astype(float)          # off a bye or long week
    f["opp_rest_short"] = (f.opp_rest <= 5).astype(float)
    f["opp_rest_long"] = (f.opp_rest >= 10).astype(float)
    f["wind_out"] = np.where(f.dome == 1, 0.0, f.wind.fillna(f.wind.median()))
    f["cold"] = np.where(f.dome == 1, 0.0, (f.temp.fillna(60) < COLD_F).astype(float))
    f["warm_in_cold"] = f["cold"] * f.team.isin(WARM_OR_DOME).astype(float)   # warm-climate or dome team outdoors under 35F
    f["qb_form"] = qb_form(f)
    pop = f.game_id.map(_rain_readings()).astype(float)   # the totals equation's rain: the GFS MOS chance 50%+ outdoors (see RAIN_FC)
    f["rain_fc"] = np.where((f.dome.fillna(0) == 0) & (pop >= RAIN_FC), 1.0, 0.0)
    return f


def fit_points(train: pd.DataFrame, alpha: float = RIDGE):
    m = make_pipeline(StandardScaler(), Ridge(alpha=alpha))
    m.fit(train[FEATS].values, train.pf.values)
    return m


# The blend (25 Sep 2026, experiments/bet_wins.py): team points are the average of seven models refit every week on the same
# games. The live ridge equation (the one every breakdown shows), three ridges with one more set of ratings each, the live
# inputs with less and with more shrinkage, and gradient-boosted trees on the live inputs, which catch interactions a line
# cannot. Averaging models that err differently cut the margin miss on 2015-18, 2019-22 and 2023-25 and won more spread
# bets at the 4-point flag in all three windows (68-55, 80-50, 40-21 against 61-58, 81-55, 40-23), whichever tree
# settings were used (reports/bet_wins.csv, reports/bet_wins_gbm.csv). The breakdowns show the ridge equation plus one
# line: the other six models' average pull.
BLEND = {"success": (["off_success", "def_success"], 10.0), "split": (["off_pass_epa", "def_pass_epa", "off_rush_epa", "def_rush_epa"], 10.0),
         "plays": (["off_plays", "def_plays"], 10.0), "alpha3": ([], 3.0), "alpha30": ([], 30.0)}
BLEND_LABEL = {"ridge": "The equation shown", "success": "+ success rate", "split": "+ pass and rush ratings", "plays": "+ plays per game",
               "alpha3": "Less shrinkage", "alpha30": "More shrinkage", "trees": "Boosted trees"}


TREES = dict(max_iter=300, learning_rate=0.03, max_leaf_nodes=8, min_samples_leaf=60, l2_regularization=1.0, random_state=0)
# The trees' predictions are kept (28 Sep 2026): the boosted trees did not reproduce across GitHub's runners on identical
# inputs (the same library versions, the same features to 1e-14, one thread: two runs still moved a third of the games
# before 2026 by up to a point; identical on one machine, so the runner's hardware decides the rounding somewhere inside
# the fit). So a fit's predictions are stored under a key of its inputs (the training rows' features and points and the
# test rows' features, rounded to nine decimals, in a fixed row order, plus the parameters), and a later run with the same
# inputs reads them back instead of refitting: a game's number is the number the first fit gave it, on any machine, until
# its inputs change. Keys not touched by a run are dropped, so the file holds exactly the fits behind pred_v3.
TREES_CACHE = OUT / "trees_cache.parquet"
_TC: dict = {"df": None, "used": set(), "new": []}


def _trees_cache() -> pd.DataFrame:
    if _TC["df"] is None:
        _TC["df"] = pd.read_parquet(TREES_CACHE) if TREES_CACHE.exists() else pd.DataFrame({"key": pd.Series(dtype=str), "game_id": pd.Series(dtype=str), "team": pd.Series(dtype=str), "pred": pd.Series(dtype=float)})
    return _TC["df"]


def trees_key(train: pd.DataFrame, test: pd.DataFrame) -> str:
    """sha1 of everything the trees' fit and prediction depend on, robust to row order and to last-digit noise."""
    h = hashlib.sha1(json.dumps(TREES, sort_keys=True).encode() + ",".join(FEATS).encode())
    tr = train.sort_values(["game_id", "team"]); te = test.sort_values(["game_id", "team"])
    h.update(np.ascontiguousarray(np.round(tr[FEATS].values.astype(float), 9)).tobytes()); h.update(np.round(tr.pf.values.astype(float), 9).tobytes())
    h.update(np.ascontiguousarray(np.round(te[FEATS].values.astype(float), 9)).tobytes()); h.update("|".join(te.game_id.astype(str) + ":" + te.team.astype(str)).encode())
    return h.hexdigest()


def save_trees_cache() -> None:
    """Write the fits this run read or made (walk_forward calls it once at the end)."""
    df = _trees_cache()
    parts = [df[df.key.isin(_TC["used"])]] + _TC["new"]
    out = pd.concat(parts, ignore_index=True).drop_duplicates(["key", "game_id", "team"], keep="last").sort_values(["key", "game_id", "team"]).reset_index(drop=True)
    out.to_parquet(TREES_CACHE, index=False); _TC["df"] = out; _TC["new"] = []


class trees_cache_read_only:
    """`with M.trees_cache_read_only(): M.walk_forward(...)`: a check or test reads the stored fits but never rewrites
    data/processed/trees_cache.parquet, and the fits it made are dropped when it ends, so a later real run in the same
    process saves only its own (2 Oct 2026, re-audit item 6: the leak checks left the file holding 2024's 71 keys)."""
    def __enter__(self):
        global save_trees_cache
        self._save, self._tc = save_trees_cache, {"used": set(_TC["used"]), "new": list(_TC["new"])}
        save_trees_cache = lambda: None
        return self

    def __exit__(self, *exc):
        global save_trees_cache
        save_trees_cache = self._save
        _TC["used"], _TC["new"] = self._tc["used"], self._tc["new"]
        return False


def fit_blend(train: pd.DataFrame, ridge_model=None, alpha: float = 10.0, test: pd.DataFrame | None = None) -> dict:
    """The seven fitted models; ridge_model is the live equation if already fitted. With `test` (the rows the fit will
    price, carrying game_id and team), the trees' predictions come from the cache when this fit was made before."""
    ms = {"ridge": (ridge_model or fit_points(train, alpha), list(FEATS))}
    for k, (extra, al) in BLEND.items():
        cols = list(FEATS) + extra
        m = make_pipeline(StandardScaler(), Ridge(alpha=al)); m.fit(train[cols].fillna(train[cols].mean()).values, train.pf.values); ms[k] = (m, cols)
    key = trees_key(train, test) if test is not None and "game_id" in test.columns else None
    if key is not None:
        c = _trees_cache(); c = c[c.key == key]
        want = set(zip(test.game_id.astype(str), test.team.astype(str)))
        if want and want <= set(zip(c.game_id, c.team)):
            _TC["used"].add(key)
            ms["trees"] = ("cache", dict(zip(zip(c.game_id, c.team), c.pred))); ms["_trees_key"] = None
            ms["_means"] = train[sorted({c_ for k_ in BLEND_LABEL if k_ in ms and k_ != "trees" for c_ in ms[k_][1]})].mean()
            return ms
    t = HistGradientBoostingRegressor(**TREES)
    with threadpool_limits(limits=1):   # one thread: sequential sums, the same on any core count
        t.fit(train[FEATS].values, train.pf.values)
    ms["trees"] = (t, list(FEATS)); ms["_trees_key"] = key
    ms["_means"] = train[sorted({c for k_ in BLEND_LABEL if k_ in ms for c in ms[k_][1]})].mean()
    return ms


def predict_blend(ms: dict, x: pd.DataFrame) -> pd.DataFrame:
    """Each model's expected points for the rows of x, and their average ("blend")."""
    mu = ms["_means"]; out = pd.DataFrame(index=x.index)
    for k in BLEND_LABEL:
        m, cols = ms[k]
        if isinstance(m, str):   # the trees' stored predictions for these rows
            out[k] = [cols[(g, t)] for g, t in zip(x.game_id.astype(str), x.team.astype(str))]
            continue
        with threadpool_limits(limits=1):
            out[k] = m.predict(x[cols].fillna(mu[cols]).values)
        if k == "trees" and ms.get("_trees_key") and "game_id" in x.columns:   # a fresh fit on its test rows: kept for the next run
            _TC["used"].add(ms["_trees_key"]); _TC["new"].append(pd.DataFrame({"key": ms["_trees_key"], "game_id": x.game_id.astype(str).values, "team": x.team.astype(str).values, "pred": out[k].values.astype(float)}))
    out["blend"] = out[list(BLEND_LABEL)].mean(axis=1)
    return out


def key_weights(margins: np.ndarray, mu: np.ndarray, sigma: float) -> pd.Series:
    """K[m] = observed count of margin m / expected count under N(mu_g, sigma), over training games."""
    obs = pd.Series(margins).round().astype(int).value_counts()
    exp = pd.Series({m: norm.pdf((m - mu) / sigma).sum() / sigma for m in MARGIN_RANGE})
    K = (obs.reindex(MARGIN_RANGE).fillna(0) + 1.0) / (exp + 1.0)   # +1 smoothing
    return K


def margin_pmf(mu: float, sigma: float, K: pd.Series) -> np.ndarray:
    p = norm.pdf((MARGIN_RANGE - mu) / sigma) * K.values
    return p / p.sum()


DIST: dict = {}   # (season, week) -> the fit's key-number weights, training total misses and residual scales (walk_forward fills it)


def price_at(mu: float, model_total: float, spread_line, total_line, dist: dict) -> dict:
    """The model's chances for one game at a given line, from its fit's distribution (dist: K, tres, sigma_margin,
    sigma_total): home win (key-number weighting), home cover (push excluded), over on a normal curve, and over read
    off the training games' own total misses (pushes left out). The model run prices the schedule's line with it; the
    picks re-price the live consensus line with the same function and the same fit."""
    K = pd.Series(np.asarray(dist["K"], dtype=float), index=MARGIN_RANGE); tres = np.asarray(dist["tres"], dtype=float)
    sl = np.nan if spread_line is None or pd.isna(spread_line) else float(spread_line)
    tl = np.nan if total_line is None or pd.isna(total_line) else float(total_line)
    win, cover = probs_from_margin(mu, dist["sigma_margin"], K, sl)
    p_over = float(1 - norm.cdf((tl - model_total) / dist["sigma_total"])) if pd.notna(tl) else np.nan
    p_emp = float(np.mean(model_total + tres > tl) / max(1e-9, np.mean(model_total + tres != tl))) if pd.notna(tl) else np.nan
    return {"p_home": float(win), "p_cover_home": float(cover) if pd.notna(cover) else np.nan, "p_over": p_over, "p_over_emp": p_emp}


def save_dist(season: int, path=None) -> None:
    """Write the fits of `season` (DIST) to data/processed/pred_v3_dist.json, beside pred_v3, so the picks can re-price a
    moved line with exactly the fit that priced the game. Floats in full (json's repr round-trips them)."""
    import json
    path = OUT / "pred_v3_dist.json" if path is None else path
    wk = {str(w): {"K": [float(v) for v in d["K"]], "tres": [float(v) for v in d["tres"]], "sigma_margin": float(d["sigma_margin"]), "sigma_total": float(d["sigma_total"])}
          for (s, w), d in DIST.items() if s == season}
    path.write_text(json.dumps({"season": int(season), "margin_range": [int(MARGIN_RANGE[0]), int(MARGIN_RANGE[-1])], "weeks": wk}, separators=(",", ":")))


def load_dist(season: int, week: int, path=None) -> dict | None:
    """The fit's distribution for (season, week) from pred_v3_dist.json; None when the file does not hold it."""
    import json
    path = OUT / "pred_v3_dist.json" if path is None else path
    if not path.exists():
        return None
    j = json.loads(path.read_text())
    if int(j.get("season", -1)) != int(season) or str(week) not in j.get("weeks", {}):
        return None
    return j["weeks"][str(week)]


def probs_from_margin(mu, sigma, K, line):
    """Home win, home cover (push excluded) for a home-minus-away margin at a home spread `line` (nflverse sign)."""
    pmf = margin_pmf(mu, sigma, K)
    win = pmf[MARGIN_RANGE > 0].sum() + 0.5 * pmf[MARGIN_RANGE == 0].sum()
    if np.isnan(line):
        return win, np.nan
    push = pmf[MARGIN_RANGE == line].sum() if float(line).is_integer() else 0.0
    cover = pmf[MARGIN_RANGE > line].sum()
    return win, cover / (1 - push) if push < 1 else np.nan


# rain_fc (1 Oct 2026, Matt: "add rain to the model"; experiments/rain_points.py): the totals equation's rain was the weather
# that happened (the play-by-play text), but an upcoming game is priced on the forecast, so the equation under-counted rain:
# games with a GFS MOS chance of 50%+ finished 2.9 points under the line while the model had them 0.3 under. Learned from the
# same forecast it is priced on (the stored last run, 2015 on since 2 Oct 2026, 2018 on before; 0 without a forecast and indoors; the live
# reading from nflmodel/wind_live.py): total miss 10.744 -> 10.738 / 10.509 -> 10.493 / 10.125 -> 10.108, the totals flag
# 135-127 -> 137-127 / 182-129 -> 202-146 / 81-62 -> 98-73; the input is worth about -4.2 points (rain_pts, the card's "rain
# -X"), those games' totals moved about -2.9 from the old model (which took some rain off through the weather text); 20 of 20
# shuffles beaten.
# The points equations keep the weather text in training; a played game is priced on the forecast (priced_weather, 2 Oct 2026).
TOTAL_FEATS = ["off_sum", "def_sum", "pf_sum", "pa_sum", "qb_sum", "qb_out_sum", "wind_out", "rain_fc", "cold", "dome", "qb_form_sum"]   # ref_tot dropped 2 Oct 2026: with the same-game leak fixed it fails the round-3 rule (reports/leak_fix_rescore.md: total miss worse on 2015-18 and 2019-22, totals flag worse on 2015-18 and 2023-25, placebo 25/31/29 of 50; Matt's standing yes to drop what fails). Was: ref_tot (28 Sep 2026): the referee read without the market, see below;   # qb_form_sum (both starters' this-season form, 25 Sep 2026): total miss 10.71 / 10.53 / 10.18 against 10.77 / 10.58 / 10.25 (reports/qb_form_totals.csv); not in the points equation, where it hurt the spread on 2019-22 (reports/qb_form.csv)
QB_FORM_K = 100.0


def qb_form(f: pd.DataFrame) -> pd.Series:
    """The starter's EPA per dropback this season before the game, shrunk toward his career rating with QB_FORM_K
    dropbacks of weight, minus the rating: how far this season is pulling him from his career number."""
    if "qb_id" not in f.columns or not (OUT / "qb_games.parquet").exists():
        return pd.Series(0.0, index=f.index)
    q = pd.read_parquet(OUT / "qb_games.parquet", columns=["qb_id", "season", "week", "dropbacks", "qb_epa"])
    qd = {k: (x.week.values, x.dropbacks.values, x.qb_epa.values) for k, x in q.sort_values("week").groupby(["qb_id", "season"])}
    out = []
    for qid, s, w, r in zip(f.qb_id, f.season, f.week, f.qb_rating):
        v = qd.get((qid, s)) if isinstance(qid, str) else None
        if v is None or pd.isna(r):
            out.append(0.0); continue
        m = v[0] < w; db, ep = float(v[1][m].sum()), float(v[2][m].sum())
        out.append((ep + QB_FORM_K * r) / (db + QB_FORM_K) - r)
    return pd.Series(out, index=f.index)
# The referee (25 Sep 2026: ref_over, his over rate against the closing total in previous games, lowered the total miss on
# every window). 28 Sep 2026, Matt: no market line in any input, so ref_over gave way to ref_tot, the same reading built
# without a line (each previous game's total minus the league's mean total of the season before, averaged and shrunk;
# trends.py). experiments/ref_noline.py, reports/ref_noline.csv, total miss on 2015-18 / 2019-22 / 2023-25:
# no referee input 10.761 / 10.566 / 10.200; ref_tot 10.744 / 10.541 / 10.177; ref_over 10.707 / 10.528 / 10.182.
# ref_tot beats no input on all three windows and is adopted; ref_over stays a trend reading (shown, not used).
# 2 Oct 2026: those numbers carried a same-game leak (the home row's prior counted this game's own total; trends._prior_mean
# fixed). Rescored clean, ref_tot fails the round-3 rule (experiments/leak_fix_rescore.py); dropped from TOTAL_FEATS the same day (#387).


def _game_frame(f: pd.DataFrame) -> pd.DataFrame:
    h = f[f.home == 1].set_index("game_id")
    a = f[f.home == 0].set_index("game_id")
    ids = h.index.intersection(a.index)
    return pd.DataFrame({"total": (h.loc[ids, "pf"] + a.loc[ids, "pf"]).values,
                         "off_sum": (h.loc[ids, "off_epa_play"] + a.loc[ids, "off_epa_play"]).values, "def_sum": (h.loc[ids, "def_epa_play"] + a.loc[ids, "def_epa_play"]).values,
                         "pf_sum": (h.loc[ids, "off_pf"] + a.loc[ids, "off_pf"]).values, "pa_sum": (h.loc[ids, "def_pf"] + a.loc[ids, "def_pf"]).values,
                         "qb_sum": (h.loc[ids, "qb_rating"] + a.loc[ids, "qb_rating"]).values, "qb_out_sum": (h.loc[ids, "qb_out"] + a.loc[ids, "qb_out"]).values,
                         "qb_form_sum": ((h.loc[ids, "qb_form"] + a.loc[ids, "qb_form"]).values if "qb_form" in h.columns else np.zeros(len(ids))), "ref_over": (h.loc[ids, "ref_over"].values if "ref_over" in h.columns else np.full(len(ids), 0.5)), "ref_tot": (h.loc[ids, "ref_tot"].values if "ref_tot" in h.columns else np.zeros(len(ids))), "wind_out": h.loc[ids, "wind_out"].values, "rain": h.loc[ids, "rain"].values, "rain_fc": (h.loc[ids, "rain_fc"].values if "rain_fc" in h.columns else np.zeros(len(ids))), "cold": h.loc[ids, "cold"].values, "dome": h.loc[ids, "dome"].values,
                         "div_game": h.loc[ids, "div_game"].values, "skill_out_sum": (h.loc[ids, "skill_out_value"] + a.loc[ids, "skill_out_value"]).values,
                         "snap_out_sum": (h.loc[ids, "off_snap_out"] + a.loc[ids, "off_snap_out"]).values,
                         "turnover_early_sum": (h.loc[ids, "off_turnover_early"] + a.loc[ids, "off_turnover_early"]).values}, index=ids)


def total_model(train: pd.DataFrame, test: pd.DataFrame, ridge_alpha=10.0):
    """Predicted game total for every game in test (aligned to test's home rows in game_id order), fit on train."""
    tr, te = _game_frame(train), _game_frame(test)
    m = make_pipeline(StandardScaler(), Ridge(alpha=ridge_alpha)).fit(tr[TOTAL_FEATS].values, tr.total.values)
    pred = pd.Series(m.predict(te[TOTAL_FEATS].values), index=te.index)
    h = test[test.home == 1].set_index("game_id")
    a = test[test.home == 0].set_index("game_id")
    ids = h.index.intersection(a.index)
    return pred.reindex(ids).values


# Wind points (1 Oct 2026, Matt: "have the wind impact the total score instead of just saying under"; reports/wind_forecast.md,
# experiments/wind_forecast.py): outdoor games whose forecast wind (GFS MOS and Japan's model, mean over the first three
# hours; nflmodel/wind_live.readings) sits in a band finish off the model's total by a band amount, learned each season from
# the seasons before it only: each band's mean miss against the mean miss of every forecast game, shrunk toward zero by
# WIND_K games. Bands [0, 10), [10, 15), 15+ mph. Rerun 2015-2026: total miss 10.541 -> 10.509 (2019-22) and 10.177 -> 10.125
# (2023-25), 2015-18 and the spread unchanged; no within-season shuffle of the forecast (50) as good (experiments/wind_points.py);
# the totals flag 175-128 -> 182-129 and 71-59 -> 81-62 (forecasts start in 2018).
WIND_BANDS, WIND_K = [0.0, 10.0, 15.0, float("inf")], 50.0


def _reader_failed(what: str, priced: str, e: Exception) -> dict:
    """2 Oct 2026 (code review): a reader that raised used to price every game calm with no sign; it still does (no
    reading = no forecast), but says so on stderr and as a health warning (nflmodel/warnlog.py). A store that does not
    exist is not an error: the readers return {} for it."""
    from .warnlog import warn
    warn("model weather", f"{what} readings failed ({type(e).__name__}: {str(e)[:120]}): games {priced}")
    return {}


def _rain_readings() -> dict:
    try:
        from .wind_live import rain_readings
        return rain_readings()
    except Exception as e:  # noqa
        return _reader_failed("rain", "priced dry", e)


def _wind_readings() -> dict:
    try:
        from .wind_live import readings
        return readings()
    except Exception as e:  # noqa
        return _reader_failed("wind", "priced with no wind points", e)


def _temp_readings() -> dict:
    try:
        from .wind_live import temp_readings
        return temp_readings()
    except Exception as e:  # noqa
        return _reader_failed("temperature", "priced on the recorded temperature or not cold", e)


# Live-style weather in the backtest (2 Oct 2026, Matt: "100% accurate, no cheating"; experiments/forecast_weather_backtest.py).
# An upcoming game is priced on a forecast, but the backtest priced every played game with the weather that happened (the
# schedule's wind and temperature, the play-by-play's rain), a small look-ahead. Now a played game with a stored pre-kickoff
# forecast (2015 on since 2 Oct 2026, 2018 on before: data/weather/forecast_history.csv, and the live log) is priced, not trained, on it: wind_out = the wind
# reading the wind points and the wind under use, cold (and warm_in_cold) = the GFS MOS kickoff temperature under COLD_F,
# the points equations' rain = the totals' rain reading (RAIN_FC). Training rows keep the recorded weather, as a live fit
# does. A missing reading prices as a live game with no forecast (league-median wind, not cold, dry). For games abroad no
# forecast is stored and the recorded weather stays (before 2015 too: nothing is backtested there). 2015 has GFS MOS only,
# 2016-2017 GFS and Japan's model (reports/forecast_history_2015.md).
# An unplayed game gets the same readings upstream
# (2 Oct 2026, re-audit item 3): weather.apply_to_games sets its wind and temperature from wind_live's GFS MOS / Japan
# reading and trends.situation_extras its rain from the MOS chance, Open-Meteo only where no reading exists yet (logged).
FORECAST_WEATHER = True


def priced_weather(f: pd.DataFrame) -> pd.DataFrame:
    """prep()'d rows with the weather a played game is priced on: the stored forecast where there is one (see above)."""
    if not FORECAST_WEATHER or "pf" not in f.columns:
        return f
    wind, temp, pop = _wind_readings(), _temp_readings(), _rain_readings()
    from .forecast_history import OUTF
    if OUTF.exists() and not (wind and temp and pop):   # a reader failed: never fall back quietly to the weather that happened
        raise RuntimeError(f"forecast readings incomplete (wind {len(wind)}, temperature {len(temp)}, rain {len(pop)}) though {OUTF.name} exists")
    m = (f.pf.notna() & f.game_id.isin(set(wind) | set(temp) | set(pop)) & (f.dome.fillna(0) != 1)).values
    if not m.any():
        return f
    f = f.copy(); g = f.game_id[m]
    f.loc[m, "wind_out"] = g.map(wind).astype(float).fillna(float(f.wind.median())).values
    f.loc[m, "cold"] = (g.map(temp).astype(float).fillna(60.0) < COLD_F).astype(float).values
    f.loc[m, "warm_in_cold"] = f.loc[m, "cold"].values * f.team[m].isin(WARM_OR_DOME).astype(float).values
    f.loc[m, "rain"] = (g.map(pop).astype(float) >= RAIN_FC).astype(float).values
    return f


def wind_points(pool: list, fw) -> float:
    """The band amount for a forecast wind fw from pool [(wind, miss), ...] of earlier seasons' forecast games."""
    if fw is None or pd.isna(fw) or not pool:
        return 0.0
    w = np.array([x[0] for x in pool], dtype=float); r = np.array([x[1] for x in pool], dtype=float)
    b = int(np.searchsorted(WIND_BANDS, fw, side="right") - 1); lo, hi = WIND_BANDS[b], WIND_BANDS[b + 1]
    m = (w >= lo) & (w < hi)
    return float((r[m].sum() - r.mean() * m.sum()) / (m.sum() + WIND_K))


def walk_forward(f: pd.DataFrame, test_seasons, ridge_alpha=RIDGE, min_train_season=TRAIN_FROM, verbose=False, refit="week") -> pd.DataFrame:
    """One row per game, priced with only earlier games. refit="week": the regression is refit before every week on every
    played game so far, this season's included (the model keeps learning as the season goes). refit="season": refit once per
    season on prior seasons only (the original 3.0 rule; same accuracy, kept for comparison). The ratings inside f are as-of
    each game already (ratings.build_features), so nothing from a game's own week or later reaches its prediction."""
    f = prep(f)
    played = f[f.pf.notna()]   # trained on the weather that happened
    fpr = priced_weather(f)    # priced on the forecast where one is stored (FORECAST_WEATHER)
    out = []
    wind = _wind_readings(); wpool = {}   # season -> [(forecast wind, actual total minus the model's total before wind points)]
    _h, _a = played[played.home == 1].set_index("game_id"), played[played.home == 0].set_index("game_id")
    actual_total = (_h.pf + _a.pf.reindex(_h.index)).dropna().to_dict()
    for s in test_seasons:
        test_all = fpr[fpr.season == s]
        weeks = sorted(test_all.week.unique()) if refit == "week" else [None]
        for wk in weeks:
            if wk is None:
                train = played[(played.season < s) & (played.season >= min_train_season)]
                test = test_all.copy()
            else:
                train = played[(played.season >= min_train_season) & ((played.season < s) | ((played.season == s) & (played.week < wk)))]
                test = test_all[test_all.week == wk].copy()
            m = fit_points(train, ridge_alpha)
            tr_pred = m.predict(train[FEATS].values)
            bl = predict_blend(fit_blend(train, m, ridge_alpha, test=test), test)
            test["exp_ridge"] = bl["ridge"].values
            test["exp"] = bl["blend"].values
            for k in BLEND_LABEL:
                test[f"m_{k}"] = bl[k].values
            h = test[test.home == 1].set_index("game_id")
            a = test[test.home == 0].set_index("game_id")
            ids = h.index.intersection(a.index)
            if len(ids) == 0:
                continue
            g = pd.DataFrame({"game_id": ids, "season": s, "week": h.loc[ids, "week"].values, "game_type": h.loc[ids, "game_type"].values,
                              "home_team": h.loc[ids, "team"].values, "away_team": a.loc[ids, "team"].values,
                              "home_exp": h.loc[ids, "exp"].values, "away_exp": a.loc[ids, "exp"].values,
                              "spread_line": h.loc[ids, "spread_line"].values, "total_line": h.loc[ids, "total_line"].values,
                              "home_qb_rating": h.loc[ids, "qb_rating"].values, "away_qb_rating": a.loc[ids, "qb_rating"].values,
                              "home_n_games": h.loc[ids, "n_games"].values,
                              "home_exp_ridge": h.loc[ids, "exp_ridge"].values, "away_exp_ridge": a.loc[ids, "exp_ridge"].values})
            g["home_blend_adj"], g["away_blend_adj"] = g.home_exp - g.home_exp_ridge, g.away_exp - g.away_exp_ridge
            for k in BLEND_LABEL:
                g[f"home_m_{k}"], g[f"away_m_{k}"] = h.loc[ids, f"m_{k}"].values, a.loc[ids, f"m_{k}"].values
            g["model_spread"] = g.home_exp - g.away_exp
            # the total from its own equation (22 Sep 2026): both teams' ratings summed, plus the game's weather and roof, fit
            # to the game total. Marginally more accurate than adding the two team scores on both backtest windows
            # (reports/totals_experiments.csv); the team scores above still drive the spread and the points shown.
            g["model_total"] = total_model(train, test)
            g["rain_pts"] = g.model_total - total_model(train, test.assign(rain_fc=0.0))   # what the forecast rain put on the total (shown on the card)
            g["model_total_raw"] = g.model_total
            pool_ = [x for s_, v in wpool.items() if s_ < s for x in v]
            g["wind_fc"] = g.game_id.map(wind).astype(float)
            g["wind_pts"] = [wind_points(pool_, fw) for fw in g.wind_fc]
            g["model_total"] = g.model_total + g.wind_pts
            # the two team scores add up to the game total (25 Sep 2026, Matt): the spread from the points equations (the
            # blend) and the total from its own equation are the two numbers bet and graded; each team's expected points
            # are the total shared out by the spread, home = (total + spread) / 2. The points equation's own number for
            # each team stays as home_pts_eq, and the share-out is one more line on the breakdown (home_total_adj). Team
            # points miss 7.398 / 7.353 / 7.259 against 7.381 / 7.340 / 7.268 before; the spread and total are unchanged
            g["home_pts_eq"], g["away_pts_eq"] = g.home_exp.values, g.away_exp.values
            g["home_exp"] = (g.model_total + g.model_spread) / 2
            g["away_exp"] = (g.model_total - g.model_spread) / 2
            g["home_total_adj"], g["away_total_adj"] = g.home_exp - g.home_pts_eq, g.away_exp - g.away_pts_eq
            # residual scale and key numbers from the training games (game level)
            trg = train.assign(pred=tr_pred)
            th = trg[trg.home == 1].set_index("game_id")
            ta = trg[trg.home == 0].set_index("game_id")
            tid = th.index.intersection(ta.index)
            tr_margin = (th.loc[tid, "pf"] - ta.loc[tid, "pf"]).values
            tr_mu = (th.loc[tid, "pred"] - ta.loc[tid, "pred"]).values
            tr_total = (th.loc[tid, "pf"] + ta.loc[tid, "pf"]).values
            tr_tmu = total_model(train, train)   # in-sample totals fit, same game order as tid
            sigma_m = float(np.std(tr_margin - tr_mu))
            sigma_t = float(np.std(tr_total - tr_tmu))
            K = key_weights(tr_margin, tr_mu, sigma_m)
            # 25 Sep 2026 (experiments/totals_fix.py): totals are right-skewed, so the chance of the over is read off the
            # training games' own misses (actual minus predicted) shifted to this game's total, not a normal curve;
            # pushes left out. Unders at a 55%+ chance won on 2015-18, 2019-22 and 2023-25 (the totals flag)
            tres = tr_total - tr_tmu
            dist = {"K": K.values, "tres": tres, "sigma_margin": sigma_m, "sigma_total": sigma_t}
            DIST[(int(s), int(wk) if wk is not None else 0)] = dist   # what prices a line for this fit (the picks re-price the live line with it)
            pr = [price_at(mu, mt, sl, tl, dist) for mu, mt, sl, tl in zip(g.model_spread, g.model_total, g.spread_line, g.total_line)]
            for k in ("p_home", "p_cover_home", "p_over", "p_over_emp"):
                g[k] = [x[k] for x in pr]
            g["sigma_margin"], g["sigma_total"] = sigma_m, sigma_t
            g["n_train"] = len(train)
            coefs = dict(zip(FEATS, m[-1].coef_ / m[0].scale_))
            for i, k in enumerate(FEATS):   # this fit's coefficient, training mean and intercept, so any game's expected points can be rebuilt to the cent (the page's deep dive and card breakdowns)
                g[f"coef_{k}"] = coefs[k]; g[f"mean_{k}"] = float(m[0].mean_[i])
            g["intercept"] = float(train.pf.mean())
            out.append(g)
            for gid, fw, raw, gt in zip(g.game_id, g.wind_fc, g.model_total_raw, g.game_type):
                if pd.notna(fw) and gt == "REG" and gid in actual_total:
                    wpool.setdefault(s, []).append((float(fw), float(actual_total[gid]) - float(raw)))
            if verbose and (wk is None or wk == weeks[-1]):
                print(f"season {s}: last fit on {len(train)} team-games, sigma margin {sigma_m:.2f}, total {sigma_t:.2f}, hfa {coefs['home']:.2f}", flush=True)
    save_trees_cache()
    return pd.concat(out, ignore_index=True)


def coefficient_table(f: pd.DataFrame, train_seasons, ridge_alpha=10.0) -> pd.DataFrame:
    f = prep(f)
    train = f[f.pf.notna() & f.season.isin(train_seasons)]
    m = fit_points(train, ridge_alpha)
    coef = m[-1].coef_ / m[0].scale_
    sd = m[0].scale_
    return pd.DataFrame({"feature": FEATS, "points_per_unit": coef, "feature_sd": sd, "points_per_sd": coef * sd}).sort_values("points_per_sd", key=abs, ascending=False)


def qb_overlap(fp: pd.DataFrame, season: int) -> dict:
    """How the QB rating and the offense EPA rating share credit in the fit before `season` (fp: prep()'d features):
    their correlation over the training team-games, each one's points per standard deviation with everything fitted
    at once, and the offense's when the QB rating is left out and the equation refit. The page and the docs quote these."""
    train = fp[fp.pf.notna() & (fp.season < season) & (fp.season >= TRAIN_FROM)]
    per_sd = dict(zip(FEATS, fit_points(train)[-1].coef_))
    cols = [c for c in FEATS if c != "qb_rating"]
    m2 = make_pipeline(StandardScaler(), Ridge(alpha=RIDGE)).fit(train[cols].values, train.pf.values)
    return {"seasons": f"{int(train.season.min())} to {int(train.season.max())}", "n": int(len(train)), "corr": round(float(train.qb_rating.corr(train.off_epa_play)), 3),
            "qb_per_sd": round(float(per_sd["qb_rating"]), 3), "off_per_sd": round(float(per_sd["off_epa_play"]), 3),
            "off_per_sd_no_qb": round(float(dict(zip(cols, m2[-1].coef_))["off_epa_play"]), 3)}


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--features", default=str(OUT / "features_asof.parquet"))
    ap.add_argument("--seasons", default="2019-2026")
    ap.add_argument("--alpha", type=float, default=10.0)
    a = ap.parse_args()
    lo, hi = a.seasons.split("-")
    f = with_trends(pd.read_parquet(a.features))
    pred = walk_forward(f, range(int(lo), int(hi) + 1), a.alpha, verbose=True)
    pred.to_parquet(OUT / "pred_v3.parquet", index=False)
    save_dist(int(hi))   # the fits' distributions for the season being priced, written with the table they priced
    print(pred.shape)
    ct = coefficient_table(f, range(2013, 2023), a.alpha)
    print(ct.round(3).to_string(index=False))
