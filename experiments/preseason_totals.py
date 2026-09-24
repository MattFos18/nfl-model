"""Preseason season totals with offseason information (24 Sep 2026). Before Week 1 the season-total projection is last
season carried forward (nflmodel/player_season.py; it knows only last season's games), so it barely beats last
season's total and flags no breakout. The standard projection systems add offseason information. What our own data
has before a snap: the player's age, whether he changed teams, how much of his team's volume (targets, carries,
dropbacks) left with players no longer on its roster, his share of that volume last season, the season before last,
and his years in the league.

Test: the Week 1 projection (base) against base adjusted by those, a linear fit on 2017-18 (the seasons with a
season before last in the data) per kind, scored by the mean miss of the season total on 2019-22 and 2023-25, and the
breakout flag's hits under each. Adopt only if better on both windows. Writes reports/preseason_totals.csv.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import numpy as np, pandas as pd
from nflmodel import player_season as PS
from nflmodel.model import OUT
from nflmodel.features import RAW

ROLE = {"rec": "receiver", "rush": "rusher", "pass": "passer"}


def features() -> pd.DataFrame:
    R = PS._finish(pd.read_csv(PS.REP / "player_season_rows.csv"))
    w1 = R[R.week == 1].copy()
    pg = pd.read_parquet(OUT / "player_games.parquet")
    pl = pd.read_parquet(RAW / "players" / "players.parquet", columns=["gsis_id", "birth_date"]).dropna()
    born = dict(zip(pl.gsis_id, pd.to_datetime(pl.birth_date, errors="coerce")))
    rows = []
    for s, g in w1.groupby("season"):
        ros = pd.read_parquet(RAW / "rosters" / f"roster_weekly_{s}.parquet", columns=["week", "team", "gsis_id", "years_exp"])
        ros = ros[ros.week == ros.week.min()]; on = set(zip(ros.team, ros.gsis_id)); yexp = dict(zip(ros.gsis_id, ros.years_exp))
        last = pg[pg.season == s - 1]; last2 = pg[pg.season == s - 2]
        for k, x in g.groupby("kind"):
            L = last[last.role == ROLE[k]]; L2 = last2[last2.role == ROLE[k]]
            team_vol = L.groupby("team").plays.sum()
            left = L.groupby(["team", "player_id"]).plays.sum().reset_index()
            left["gone"] = [(t, p) not in on for t, p in zip(left.team, left.player_id)]
            vac = (left[left.gone].groupby("team").plays.sum() / team_vol).reindex(team_vol.index).fillna(0.0)
            main_team = L.sort_values("plays").groupby("player_id").team.last()
            share = (L.groupby(["player_id", "team"]).plays.sum() / L.groupby("team").plays.sum()).groupby("player_id").max()
            y2 = L2.groupby("player_id").agg(g2=("game_id", "nunique"))
            for r in x.itertuples():
                b = born.get(r.player_id)
                rows.append({"season": s, "kind": k, "player_id": r.player_id, "name": r.name, "team": r.team, "base": r.proj_yards, "actual": r.actual_yards, "actual_games": r.actual_games,
                             "prev_yards": r.prev_yards, "prev_games": r.prev_games, "team_games": r.team_games, "rank": r.rank, "prev_pg": r.prev_pg,
                             "age": (pd.Timestamp(f"{s}-09-01") - b).days / 365.25 if b is not None and pd.notna(b) else np.nan,
                             "moved": float(main_team.get(r.player_id, r.team) != r.team), "vacated": float(vac.get(r.team, 0.0)), "share": float(share.get(r.player_id, 0.0)),
                             "yexp": yexp.get(r.player_id, np.nan), "had_y2": float(r.player_id in y2.index)})
    f = pd.DataFrame(rows)
    f["age"] = f.age.fillna(f.groupby("kind").age.transform("median")); f["yexp"] = f.yexp.fillna(f.groupby("kind").yexp.transform("median"))
    return f


def design(f: pd.DataFrame, variant: str) -> np.ndarray:
    cols = [f.base]
    if variant in ("age", "all"):
        cols += [f.base * (f.age - 27).clip(lower=0), f.base * (27 - f.age).clip(lower=0)]
    if variant in ("team", "all"):
        cols += [f.base * f.moved, f.vacated * f.team_games * 10, f.base * f.vacated]
    if variant in ("young", "all"):
        cols += [f.base * (f.yexp <= 1), f.base * (1 - f.had_y2)]
    return np.column_stack([np.ones(len(f))] + [np.asarray(c, float) for c in cols])


def run() -> pd.DataFrame:
    f = features(); res = []
    for k, x in f.groupby("kind"):
        fit = x[x.season <= 2018]
        for v in ("base", "age", "team", "young", "all"):
            if v == "base":
                pred = x.base.values
            else:
                X = design(fit, v); lam = 1e-6 * np.eye(X.shape[1])
                beta = np.linalg.solve(X.T @ X + lam, X.T @ fit.actual.values)
                pred = design(x, v) @ beta
            y = x.assign(pred=pred)
            y["rk"] = y.groupby("season").pred.rank(ascending=False, method="first")
            y["flag"] = (y.rk <= PS.TOP_N[k]) & (y.pred / y.team_games.clip(lower=1) >= PS.BREAK_UP * y.prev_pg) & (y.prev_games > 0)
            y["arank"] = y.groupby("season").actual.rank(ascending=False, method="min")
            y["hit"] = (y.actual / y.actual_games.clip(lower=1) >= PS.BREAK_UP * y.prev_pg) & (y.arank <= PS.TOP_N[k])
            for w, (a, b) in {"2017-18 (fit)": (2017, 2018), "2019-22": (2019, 2022), "2023-25": (2023, 2025)}.items():
                z = y[y.season.between(a, b)]
                res.append({"kind": k, "variant": v, "window": w, "n": len(z), "mae": round(float((z.pred - z.actual).abs().mean()), 1),
                            "flags": int(z.flag.sum()), "hits": int((z.flag & z.hit).sum())})
    return pd.DataFrame(res)


if __name__ == "__main__":
    r = run(); r.to_csv(PS.REP / "preseason_totals.csv", index=False)
    pd.set_option("display.width", 200)
    print(r.pivot_table(index=["kind", "variant"], columns="window", values="mae").round(1).to_string())
    print(r[r.window != "2017-18 (fit)"].pivot_table(index=["kind", "variant"], columns="window", values=["flags", "hits"]).to_string())
