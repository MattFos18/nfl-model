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
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline

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
FEATS = RATING_FEATS + ["qb_rating"] + SIT_FEATS + ["qb_out"] + INJ_FEATS + CONT_FEATS + LATE_FEATS
# the wider set the model carried before, kept for the ablation and the experiments
FEATS_WIDE = [f"{s}_{st}" for st in ["epa_play", "pass_epa", "rush_epa", "pf", "plays"] for s in ["off", "def"]] + ["qb_rating", "opp_qb_rating", "opp_off_epa_play", "own_def_epa_play", "opp_off_plays"] + \
             ["home", "neutral", "rest_short", "rest_long", "opp_rest_short", "opp_rest_long", "dome", "wind_out", "cold", "div_game", "primetime", "qb_out"]
MARGIN_RANGE = np.arange(-60, 61)


TREND_FEATS = ["team_home_edge", "h2h_cover", "coach_ats", "qb_ats", "off_loss", "ref_over", "ref_home_cover", "ref_pen", "sun_late",
               "body_clock_early", "cold_edge", "wind_edge", "off_home_split", "off_starters_out", "def_starters_out", "qb_out",
               "rain", "snow", "travel_miles", "tz_shift", "ol_out", "off_snap_out", "def_snap_out", "off_continuity", "def_continuity"]


def with_trends(f: pd.DataFrame) -> pd.DataFrame:
    """Merge the as-of trend and injury table (trends.py) onto the feature table; missing values become 0 / league."""
    t = pd.read_parquet(OUT / "trends_asof.parquet")
    t = t[["game_id", "team"] + TREND_FEATS]
    f = f.merge(t, on=["game_id", "team"], how="left")
    fill = {"ref_over": 0.5, "ref_home_cover": 0.5, "off_continuity": 0.83, "def_continuity": 0.83}   # continuity: league-typical share when unknown
    for c in TREND_FEATS:
        f[c] = f[c].fillna(fill.get(c, 0.0))
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
    rec = record_before(pd.read_parquet(OUT / "games.parquet"))
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
    f["cold"] = np.where(f.dome == 1, 0.0, (f.temp.fillna(60) < 35).astype(float))
    f["warm_in_cold"] = f["cold"] * f.team.isin(WARM_OR_DOME).astype(float)   # warm-climate or dome team outdoors under 35F
    return f


def fit_points(train: pd.DataFrame, alpha: float = 10.0):
    m = make_pipeline(StandardScaler(), Ridge(alpha=alpha))
    m.fit(train[FEATS].values, train.pf.values)
    return m


def key_weights(margins: np.ndarray, mu: np.ndarray, sigma: float) -> pd.Series:
    """K[m] = observed count of margin m / expected count under N(mu_g, sigma), over training games."""
    obs = pd.Series(margins).round().astype(int).value_counts()
    exp = pd.Series({m: norm.pdf((m - mu) / sigma).sum() / sigma for m in MARGIN_RANGE})
    K = (obs.reindex(MARGIN_RANGE).fillna(0) + 1.0) / (exp + 1.0)   # +1 smoothing
    return K


def margin_pmf(mu: float, sigma: float, K: pd.Series) -> np.ndarray:
    p = norm.pdf((MARGIN_RANGE - mu) / sigma) * K.values
    return p / p.sum()


def probs_from_margin(mu, sigma, K, line):
    """Home win, home cover (push excluded) for a home-minus-away margin at a home spread `line` (nflverse sign)."""
    pmf = margin_pmf(mu, sigma, K)
    win = pmf[MARGIN_RANGE > 0].sum() + 0.5 * pmf[MARGIN_RANGE == 0].sum()
    if np.isnan(line):
        return win, np.nan
    push = pmf[MARGIN_RANGE == line].sum() if float(line).is_integer() else 0.0
    cover = pmf[MARGIN_RANGE > line].sum()
    return win, cover / (1 - push) if push < 1 else np.nan


TOTAL_FEATS = ["off_sum", "def_sum", "pf_sum", "pa_sum", "qb_sum", "qb_out_sum", "wind_out", "rain", "cold", "dome"]


def _game_frame(f: pd.DataFrame) -> pd.DataFrame:
    h = f[f.home == 1].set_index("game_id")
    a = f[f.home == 0].set_index("game_id")
    ids = h.index.intersection(a.index)
    return pd.DataFrame({"total": (h.loc[ids, "pf"] + a.loc[ids, "pf"]).values,
                         "off_sum": (h.loc[ids, "off_epa_play"] + a.loc[ids, "off_epa_play"]).values, "def_sum": (h.loc[ids, "def_epa_play"] + a.loc[ids, "def_epa_play"]).values,
                         "pf_sum": (h.loc[ids, "off_pf"] + a.loc[ids, "off_pf"]).values, "pa_sum": (h.loc[ids, "def_pf"] + a.loc[ids, "def_pf"]).values,
                         "qb_sum": (h.loc[ids, "qb_rating"] + a.loc[ids, "qb_rating"]).values, "qb_out_sum": (h.loc[ids, "qb_out"] + a.loc[ids, "qb_out"]).values,
                         "wind_out": h.loc[ids, "wind_out"].values, "rain": h.loc[ids, "rain"].values, "cold": h.loc[ids, "cold"].values, "dome": h.loc[ids, "dome"].values,
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


def walk_forward(f: pd.DataFrame, test_seasons, ridge_alpha=10.0, min_train_season=2013, verbose=False, refit="week") -> pd.DataFrame:
    """One row per game, priced with only earlier games. refit="week": the regression is refit before every week on every
    played game so far, this season's included (the model keeps learning as the season goes). refit="season": refit once per
    season on prior seasons only (the original 3.0 rule; same accuracy, kept for comparison). The ratings inside f are as-of
    each game already (ratings.build_features), so nothing from a game's own week or later reaches its prediction."""
    f = prep(f)
    played = f[f.pf.notna()]
    out = []
    for s in test_seasons:
        test_all = f[f.season == s]
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
            test["exp"] = m.predict(test[FEATS].values)
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
                              "home_n_games": h.loc[ids, "n_games"].values})
            g["model_spread"] = g.home_exp - g.away_exp
            # the total from its own equation (22 Sep 2026): both teams' ratings summed, plus the game's weather and roof, fit
            # to the game total. Marginally more accurate than adding the two team scores on both backtest windows
            # (reports/totals_experiments.csv); the team scores above still drive the spread and the points shown.
            g["model_total"] = total_model(train, test)
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
            wc = [probs_from_margin(mu, sigma_m, K, line) for mu, line in zip(g.model_spread, g.spread_line)]
            g["p_home"] = [w for w, c in wc]
            g["p_cover_home"] = [c for w, c in wc]
            g["p_over"] = 1 - norm.cdf((g.total_line - g.model_total) / sigma_t)
            g["sigma_margin"], g["sigma_total"] = sigma_m, sigma_t
            g["n_train"] = len(train)
            coefs = dict(zip(FEATS, m[-1].coef_ / m[0].scale_))
            for i, k in enumerate(FEATS):   # this fit's coefficient, training mean and intercept, so any game's expected points can be rebuilt to the cent (the page's deep dive and card breakdowns)
                g[f"coef_{k}"] = coefs[k]; g[f"mean_{k}"] = float(m[0].mean_[i])
            g["intercept"] = float(train.pf.mean())
            out.append(g)
            if verbose and (wk is None or wk == weeks[-1]):
                print(f"season {s}: last fit on {len(train)} team-games, sigma margin {sigma_m:.2f}, total {sigma_t:.2f}, hfa {coefs['home']:.2f}", flush=True)
    return pd.concat(out, ignore_index=True)


def coefficient_table(f: pd.DataFrame, train_seasons, ridge_alpha=10.0) -> pd.DataFrame:
    f = prep(f)
    train = f[f.pf.notna() & f.season.isin(train_seasons)]
    m = fit_points(train, ridge_alpha)
    coef = m[-1].coef_ / m[0].scale_
    sd = m[0].scale_
    return pd.DataFrame({"feature": FEATS, "points_per_unit": coef, "feature_sd": sd, "points_per_sd": coef * sd}).sort_values("points_per_sd", key=abs, ascending=False)


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
    print(pred.shape)
    ct = coefficient_table(f, range(2013, 2023), a.alpha)
    print(ct.round(3).to_string(index=False))
