"""Season totals with a fitted rest-of-season rate (24 Sep 2026). Where do the season-total misses come from? Split
the total into the games a player goes on to play and his yards per game in them: among players who played at least
80% of their team's remaining games the total landed within 20% of the final 58% (receiving), 59% (rushing) and 80%
(passing) of the time; the misses are mostly games lost to injury and role changes, which nothing here can see. The
part that can be improved is the per-game rate for the rest of the season.

Today's rate blends the props engine's per-game mean (his share x the team's plays x his yards per touch, shrunk)
with his pace so far at a fixed weight. This test fits the rest-of-season yards per game played on 2016-18 as a
linear combination of: the props engine's per-game mean, his per-game so far weighted by games so far (n / (n + 4)),
last season's per-game, and the engine's mean weighted the same way (so the fit can move weight between the engine
and the season so far as games come in). The season total is then yards so far + that rate x the team's games left x
a refit availability share. Scored on 2019-22 and 2023-25: mean miss and the share within 10% and 20% of the final,
against today's. Adopt a kind only if better on both windows. Writes reports/season_rate.csv (and the coefficients).

Result: worse on the season total in both windows (the pace blend already carries the games players miss). The fitted
rate does beat the blend for the players who went on to play every game left (receiving within 20%: 67% / 69%
against 65% / 67%), but no one knows beforehand who that will be, and shown beside the expected total it read lower
than it for hot starts. Kept here as a finding (full_rate), not on the page.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import numpy as np, pandas as pd
from experiments import player_season_backtest as BT
from nflmodel import player_season as PS

N0 = 4.0
BLEND = PS.BLEND
# if he plays every game left (24 Sep 2026, experiments/season_rate.py): his yards per game for the rest of the season,
# fitted on 2016-18 from the engine's per-game mean (a), his per game so far (b) and last season's (c), with n games so
# far: rate = k0 + k1 a + k2 b n/(n+4) + k3 c + k4 a n/(n+4). Better than the blend on both windows for receiving and
# rushing (share within 20% of the final among players who played every game left); passing keeps the blend's rate
RATE_FIT = {"rec": (4.8365, 0.6521, 0.5037, 0.2028, -0.5303), "rush": (10.3504, 0.5795, 0.2759, 0.114, -0.1376)}
N0 = 4.0


def full_rate(d: pd.DataFrame) -> pd.Series:
    """Yards per game for the rest of the season if he plays every game: the fitted rate (receiving, rushing) or the
    blend's per-game mix of the engine and his pace (passing)."""
    n = d.games_so_far.astype(float); w = n / (n + N0)
    so = (d.yards_so_far / d.games_so_far.replace(0, np.nan)).fillna(d.prev_yards / d.prev_games.replace(0, np.nan)).fillna(d.yards_pg)
    prev = (d.prev_yards / d.prev_games.replace(0, np.nan)).fillna(d.yards_pg)
    out = pd.Series(np.nan, index=d.index, dtype=float)
    for k, c in RATE_FIT.items():
        m = d.kind == k
        out[m] = (c[0] + c[1] * d.yards_pg + c[2] * so * w + c[3] * prev + c[4] * d.yards_pg * w)[m]
    m = ~d.kind.isin(list(RATE_FIT))
    b = d.kind.map(BLEND).astype(float)
    out[m] = ((1 - b) * d.yards_pg + b * so)[m]
    return out.clip(lower=0)




def design(d: pd.DataFrame) -> np.ndarray:
    n = d.games_so_far.astype(float); w = n / (n + N0)
    so = (d.yards_so_far / d.games_so_far.replace(0, np.nan)).fillna(d.yards_pg)
    prev = (d.prev_yards / d.prev_games.replace(0, np.nan)).fillna(d.yards_pg)
    return np.column_stack([np.ones(len(d)), d.yards_pg, so * w, prev, d.yards_pg * w])


def fit_rate(fit: pd.DataFrame) -> np.ndarray:
    g = fit[fit.games_left_played >= 1]
    y = (g.actual_yards - g.yards_so_far) / g.games_left_played
    wt = np.sqrt(g.games_left_played.astype(float))
    X = design(g)
    return np.linalg.lstsq(X * wt.values[:, None], y.values * wt.values, rcond=None)[0]


def main():
    R = pd.read_csv(BT.CACHE); R = R[R.team_games_left > 0].copy()
    res, coefs = [], {}
    for k in ("rec", "rush", "pass"):
        g = R[R.kind == k].copy(); fit = g[g.season.isin(BT.FIT_SEASONS)]
        beta = fit_rate(fit); coefs[k] = beta
        g["rate"] = np.clip(design(g) @ beta, 0, None)
        fk = g[g.season.isin(BT.FIT_SEASONS)]
        best = min((float(((fk.yards_so_far + fk.rate * fk.team_games_left * a) - fk.actual_yards).abs().mean()), a) for a in np.round(np.arange(0.3, 1.2001, 0.025), 3))
        av = best[1]
        g["new"] = g.yards_so_far + g.rate * g.team_games_left * av
        a0, b0 = PS.AVAIL[k], PS.BLEND[k]
        g["old"] = (1 - b0) * (g.yards_so_far + g.yards_pg * g.team_games_left * a0) + b0 * g.pace_yards
        for w, (s0, s1) in {"2019-22": (2019, 2022), "2023-25": (2023, 2025)}.items():
            t = g[g.season.between(s0, s1)]
            for v in ("old", "new"):
                rel = (t[v] - t.actual_yards).abs() / t.actual_yards.clip(lower=1)
                res.append({"kind": k, "window": w, "variant": v, "avail": av if v == "new" else a0, "n": len(t), "mae": round(float((t[v] - t.actual_yards).abs().mean()), 1),
                            "within10": round(float((rel <= 0.1).mean()), 3), "within20": round(float((rel <= 0.2).mean()), 3)})
        print(k, "rate =", " + ".join(f"{c:.3f}" for c in beta), "availability", av, flush=True)
    o = pd.DataFrame(res); o.to_csv(PS.REP / "season_rate.csv", index=False)
    pd.DataFrame({k: list(v) for k, v in coefs.items()}, index=["intercept", "engine", "so_far_w", "last_season", "engine_w"]).to_csv(PS.REP / "season_rate_coefs.csv")
    pd.set_option("display.width", 200); print(o.pivot_table(index=["kind", "variant"], columns="window", values=["mae", "within20", "within10"]).to_string())


if __name__ == "__main__":
    main()
