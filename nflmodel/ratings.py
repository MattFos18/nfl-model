"""Opponent-adjusted, time-decayed team ratings, and the as-of feature table for the points model.

For a stat y (EPA per play, pass EPA, rush EPA, success rate, points, plays) observed for team i's
offense against team j's defense in game g, the rating solve is a weighted ridge regression

    y_g = mu + O_i - D_j + h * home_g + e_g,   weight w_g,   penalty alpha * (sum O^2 + sum D^2)

so O_i is how much better than average team i's offense is after accounting for who it played, and
D_j is how much a defense takes away. Weights decay with age (decay ** weeks_ago); last season's games
carry an extra multiplier `prior` (the offseason reset) and are aged from the end of that season. The
ridge penalty pulls thin samples toward the league average, which is what makes Week 1 ratings mostly
last year's rating shrunk toward zero.

The QB rating is a decayed, shrunk average of the starting quarterback's own EPA per dropback over every
game he has played (any team), so a QB change moves the team the moment the schedule names the starter.

`build_features(params)` walks every (season, week) from 2013 on and returns one row per team-game with the
ratings each team carried into that game plus the situational fields. Nothing in a row uses that game or
any later game.
"""
from __future__ import annotations
import numpy as np, pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "processed"

STATS = ["epa_play", "pass_epa", "rush_epa", "success", "pf", "plays"]
DEFAULT = {"decay": 0.90, "prior": 0.5, "alpha": 16.0, "qb_k": 150.0, "qb_decay": 0.985}  # tuned on 2019-2022, reports/tuning_ratings.csv


def solve(rows: pd.DataFrame, y: np.ndarray, w: np.ndarray, teams: list, alpha: float):
    """Weighted ridge for mu, h, O_i, D_j. rows has columns team, opp, home. Returns (O, D, mu, h) as Series/floats."""
    n, T = len(rows), len(teams)
    idx = {t: k for k, t in enumerate(teams)}
    X = np.zeros((n, 2 + 2 * T))
    X[:, 0] = 1.0
    X[:, 1] = rows.home.values.astype(float)
    ti = rows.team.map(idx).values
    oi = rows.opp.map(idx).values
    X[np.arange(n), 2 + ti] = 1.0
    X[np.arange(n), 2 + T + oi] = -1.0
    ok = ~np.isnan(y)
    X, yv, wv = X[ok], y[ok], w[ok]
    P = np.zeros(2 + 2 * T)
    P[2:] = alpha
    A = X.T @ (X * wv[:, None]) + np.diag(P)
    b = X.T @ (yv * wv)
    beta = np.linalg.solve(A, b)
    O = pd.Series(beta[2:2 + T], index=teams)
    D = pd.Series(beta[2 + T:], index=teams)
    return O, D, beta[0], beta[1]


def window(tg: pd.DataFrame, season: int, week: int, decay: float, prior: float):
    """Games visible before (season, week) with their weights."""
    cur = tg[(tg.season == season) & (tg.week < week)]
    last = tg[tg.season == season - 1]
    age_cur = (week - cur.week).values.astype(float)
    last_end = last.week.max() if len(last) else 18
    age_last = (week + (last_end + 1 - last.week)).values.astype(float)
    w = np.concatenate([decay ** age_cur, prior * decay ** age_last])
    return pd.concat([cur, last]), w


def window_variant(tg: pd.DataFrame, season: int, week: int, p: dict, kind: str):
    """Alternative windows for the Rankings tab. "model" is the real one (decay, last season at half weight). The others
    answer "who is playing well lately" without decay or last season: "season" = this season's games, equal weight;
    "last3" = the last three weeks; "last1" = last week only; "lastseason" = all of last season, equal weight."""
    if kind == "model":
        return window(tg, season, week, p["decay"], p["prior"])
    if kind == "lastseason":
        last = tg[tg.season == season - 1]
        return last, np.ones(len(last))
    cur = tg[(tg.season == season) & (tg.week < week)]
    if kind == "season":
        return cur, np.ones(len(cur))
    if kind == "last3":
        cur = cur[cur.week >= week - 3]
        return cur, np.ones(len(cur))
    if kind == "last1":
        cur = cur[cur.week == week - 1]
        return cur, np.ones(len(cur))
    raise ValueError(kind)


def team_ratings(tg: pd.DataFrame, season: int, week: int, p: dict, kind: str = "model") -> pd.DataFrame:
    rows, w = window_variant(tg, season, week, p, kind)
    teams = sorted(set(tg[tg.season == season].team) | set(rows.team))
    out = pd.DataFrame(index=teams)
    for s in STATS:
        O, D, mu, h = solve(rows, rows[s].values.astype(float), w, teams, p["alpha"])
        out[f"off_{s}"] = O
        out[f"def_{s}"] = D
        out.attrs[f"mu_{s}"] = mu
        out.attrs[f"hfa_{s}"] = h
    out["n_games"] = tg[(tg.season == season) & (tg.week < week)].groupby("team").size().reindex(teams).fillna(0)
    return out


class QBRatings:
    """Starting QB EPA per dropback, decayed by games and shrunk to a replacement-level prior."""

    def __init__(self, qb: pd.DataFrame, k: float, decay: float, prior_epa: float = -0.05):
        self.qb = qb.sort_values(["season", "week"])
        self.k, self.decay, self.prior = k, decay, prior_epa
        self._cache = {}

    def rating(self, qb_id: str, season: int, week: int) -> float:
        key = (qb_id, season, week)
        if key in self._cache:
            return self._cache[key]
        h = self.qb[(self.qb.qb_id == qb_id) & ((self.qb.season < season) | ((self.qb.season == season) & (self.qb.week < week)))]
        if len(h) == 0:
            r = self.prior
        else:
            age = np.arange(len(h))[::-1]
            w = self.decay ** age
            db = (h.dropbacks.values * w).sum()
            ep = (h.qb_epa.values * w).sum()
            r = (ep + self.k * self.prior) / (db + self.k)
        self._cache[key] = r
        return r


SITUATION = ["home", "rest", "dome", "temp", "wind", "div_game", "primetime"]


def build_features(p: dict = DEFAULT, seasons=range(2013, 2027), tg=None, games=None, qb=None, verbose=False) -> pd.DataFrame:
    tg = pd.read_parquet(OUT / "team_games.parquet") if tg is None else tg
    games = pd.read_parquet(OUT / "games.parquet") if games is None else games
    qb = pd.read_parquet(OUT / "qb_games.parquet") if qb is None else qb
    played = tg[tg.pf.notna()].copy()
    played["plays"] = played.plays.fillna(played.plays.mean())
    qbr = QBRatings(qb, p["qb_k"], p["qb_decay"])
    # each team's most recent named starter, in schedule order (played games and the coming week carry ids)
    named = games[games.home_qb_id.notna() | games.away_qb_id.notna()].sort_values(["season", "week"])
    last_qb = {}
    feats = []
    for s in seasons:
        weeks = sorted(games[games.season == s].week.unique())
        for wk in weeks:
            gw = games[(games.season == s) & (games.week == wk)]
            if len(gw) == 0:
                continue
            for g in named[(named.season == s) & (named.week == wk)].itertuples():
                if isinstance(g.home_qb_id, str):
                    last_qb[g.home_team] = g.home_qb_id
                if isinstance(g.away_qb_id, str):
                    last_qb[g.away_team] = g.away_qb_id
            R = team_ratings(played, s, wk, p)
            hfa = R.attrs.get("hfa_pf", 0.0)
            for g in gw.itertuples():
                for side, opp in [("home", "away"), ("away", "home")]:
                    t, o = getattr(g, f"{side}_team"), getattr(g, f"{opp}_team")
                    if t not in R.index or o not in R.index:
                        continue
                    row = {"game_id": g.game_id, "season": s, "week": wk, "game_type": g.game_type, "team": t, "opp": o,
                           "home": float(side == "home"), "pf": getattr(g, f"{side}_score"), "pa": getattr(g, f"{opp}_score"),
                           "rest": getattr(g, f"{side}_rest"), "opp_rest": getattr(g, f"{opp}_rest"),
                           "dome": float(bool(g.dome)), "temp": g.temp, "wind": g.wind, "div_game": float(g.div_game),
                           "primetime": float(bool(g.primetime)), "neutral": float(bool(g.neutral)),
                           "spread_line": g.spread_line, "total_line": g.total_line, "implied": getattr(g, f"{side}_implied"),
                           "n_games": R.n_games[t], "hfa_fit": hfa}
                    for st in STATS:
                        row[f"off_{st}"] = R.loc[t, f"off_{st}"]
                        row[f"def_{st}"] = R.loc[o, f"def_{st}"]          # the defense this offense faces
                        row[f"own_def_{st}"] = R.loc[t, f"def_{st}"]
                        row[f"opp_off_{st}"] = R.loc[o, f"off_{st}"]
                    # nflverse names the starters only for played games and the coming week. For a later unplayed game
                    # carry each team's most recent starter forward rather than pricing a replacement-level QB.
                    qid = getattr(g, f"{side}_qb_id")
                    if not isinstance(qid, str) and pd.isna(getattr(g, f"{side}_score")):
                        qid = last_qb.get(t)
                    row["qb_id"] = qid
                    row["qb_rating"] = qbr.rating(qid, s, wk) if isinstance(qid, str) else qbr.prior
                    oqid = getattr(g, f"{opp}_qb_id")
                    if not isinstance(oqid, str) and pd.isna(getattr(g, f"{side}_score")):
                        oqid = last_qb.get(o)
                    row["opp_qb_rating"] = qbr.rating(oqid, s, wk) if isinstance(oqid, str) else qbr.prior
                    feats.append(row)
        if verbose:
            print("features", s, len(feats), flush=True)
    return pd.DataFrame(feats)


if __name__ == "__main__":
    f = build_features(verbose=True)
    f.to_parquet(OUT / "features_asof.parquet", index=False)
    print(f.shape)
