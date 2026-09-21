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
RATING_FEATS = [f"{s}_{st}" for st in ["epa_play", "pass_epa", "rush_epa", "success", "pf", "plays"] for s in ["off", "def"]]
SIT_FEATS = ["home", "neutral", "rest_short", "rest_long", "opp_rest_short", "opp_rest_long", "dome", "wind_out", "cold", "div_game", "primetime"]
FEATS = RATING_FEATS + ["qb_rating", "opp_qb_rating", "opp_off_epa_play", "own_def_epa_play", "opp_off_plays"] + SIT_FEATS
MARGIN_RANGE = np.arange(-60, 61)


def prep(f: pd.DataFrame) -> pd.DataFrame:
    f = f.copy()
    f["rest_short"] = (f.rest <= 5).astype(float)          # Thursday game
    f["rest_long"] = (f.rest >= 10).astype(float)          # off a bye or long week
    f["opp_rest_short"] = (f.opp_rest <= 5).astype(float)
    f["opp_rest_long"] = (f.opp_rest >= 10).astype(float)
    f["wind_out"] = np.where(f.dome == 1, 0.0, f.wind.fillna(f.wind.median()))
    f["cold"] = np.where(f.dome == 1, 0.0, (f.temp.fillna(60) < 35).astype(float))
    return f


def fit_points(train: pd.DataFrame, alpha: float = 3.0):
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


def walk_forward(f: pd.DataFrame, test_seasons, ridge_alpha=3.0, min_train_season=2013, verbose=False) -> pd.DataFrame:
    """Refit on every season before each test season; return one row per game."""
    f = prep(f)
    played = f[f.pf.notna()]
    out = []
    for s in test_seasons:
        train = played[(played.season < s) & (played.season >= min_train_season)]
        m = fit_points(train, ridge_alpha)
        tr_pred = m.predict(train[FEATS].values)
        test = f[f.season == s].copy()
        test["exp"] = m.predict(test[FEATS].values)
        # per-game rows
        h = test[test.home == 1].set_index("game_id")
        a = test[test.home == 0].set_index("game_id")
        ids = h.index.intersection(a.index)
        g = pd.DataFrame({"game_id": ids, "season": s, "week": h.loc[ids, "week"].values, "game_type": h.loc[ids, "game_type"].values,
                          "home_team": h.loc[ids, "team"].values, "away_team": a.loc[ids, "team"].values,
                          "home_exp": h.loc[ids, "exp"].values, "away_exp": a.loc[ids, "exp"].values,
                          "spread_line": h.loc[ids, "spread_line"].values, "total_line": h.loc[ids, "total_line"].values,
                          "home_qb_rating": h.loc[ids, "qb_rating"].values, "away_qb_rating": a.loc[ids, "qb_rating"].values,
                          "home_n_games": h.loc[ids, "n_games"].values})
        g["model_spread"] = g.home_exp - g.away_exp
        g["model_total"] = g.home_exp + g.away_exp
        # residual scale and key numbers from the training games (game level)
        trg = train.assign(pred=tr_pred)
        th = trg[trg.home == 1].set_index("game_id")
        ta = trg[trg.home == 0].set_index("game_id")
        tid = th.index.intersection(ta.index)
        tr_margin = (th.loc[tid, "pf"] - ta.loc[tid, "pf"]).values
        tr_mu = (th.loc[tid, "pred"] - ta.loc[tid, "pred"]).values
        tr_total = (th.loc[tid, "pf"] + ta.loc[tid, "pf"]).values
        tr_tmu = (th.loc[tid, "pred"] + ta.loc[tid, "pred"]).values
        sigma_m = float(np.std(tr_margin - tr_mu))
        sigma_t = float(np.std(tr_total - tr_tmu))
        K = key_weights(tr_margin, tr_mu, sigma_m)
        wc = [probs_from_margin(mu, sigma_m, K, line) for mu, line in zip(g.model_spread, g.spread_line)]
        g["p_home"] = [w for w, c in wc]
        g["p_cover_home"] = [c for w, c in wc]
        g["p_over"] = 1 - norm.cdf((g.total_line - g.model_total) / sigma_t)
        g["sigma_margin"], g["sigma_total"] = sigma_m, sigma_t
        # what each adjustment was worth this season (points, home team's view), for the game card
        coefs = dict(zip(FEATS, m[-1].coef_ / m[0].scale_))
        for k in SIT_FEATS:
            g[f"coef_{k}"] = coefs[k]
        out.append(g)
        if verbose:
            print(f"season {s}: trained on {len(train)} team-games, sigma margin {sigma_m:.2f}, total {sigma_t:.2f}, hfa {coefs['home']:.2f}", flush=True)
    return pd.concat(out, ignore_index=True)


def coefficient_table(f: pd.DataFrame, train_seasons, ridge_alpha=3.0) -> pd.DataFrame:
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
    ap.add_argument("--alpha", type=float, default=3.0)
    a = ap.parse_args()
    lo, hi = a.seasons.split("-")
    f = pd.read_parquet(a.features)
    pred = walk_forward(f, range(int(lo), int(hi) + 1), a.alpha, verbose=True)
    pred.to_parquet(OUT / "pred_v3.parquet", index=False)
    print(pred.shape)
    ct = coefficient_table(f, range(2013, 2023), a.alpha)
    print(ct.round(3).to_string(index=False))
