"""Every knob, re-swept (25 Sep 2026, Matt: "change numbers and coefficients and how we calculate things and how quickly we
fade out data ... do everything"). Our own data only. Each variant is priced walk-forward over 2015-2025 (weekly refit on
every earlier game) with the live equation, then scored on 2015-18 (never used for a choice), 2019-22 and 2023-25 by
the team points, margin and total miss and the 4+ spread record against the closing line. The live blend is checked
separately on the finalists (experiments/sweep_confirm.py).

Parts (python experiments/sweep_all.py <part>):
  ratings   how fast the team ratings fade (decay per week), last season's weight, the pull toward average; the QB
            rating's shrinkage, decay per game, fade per season and replacement level
  fit       the regression's training window (every season since 2013, or the last 3 / 5 / 8), weighting recent
            seasons more (0.95 / 0.9 / 0.8 per season back), this season's games more, the ridge penalty, how long
            the offseason-turnover input lasts (weeks 4 to 12), when "out of the race" starts and its cut
  totals    the total equation's penalty, window and recency weight
Writes reports/sweep_<part>.csv."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import numpy as np, pandas as pd
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from nflmodel import model as M, ratings as R
from nflmodel.model import OUT

REP = Path(__file__).resolve().parent.parent / "reports"
GAMES = pd.read_parquet(OUT / "games.parquet")[["game_id", "game_type", "result", "total", "spread_line", "total_line"]]
W = {"2015-18": (2015, 2018), "2019-22": (2019, 2022), "2023-25": (2023, 2025)}


def price(f, alpha=10.0, start=2013, window=None, season_w=1.0, cur_w=1.0, t_alpha=10.0, t_window=None, t_season_w=1.0):
    """Walk-forward with the live equation and the total equation under the given fitting choices."""
    f = M.prep(f); played = f[f.pf.notna()]; rows = []
    for s in range(2015, 2026):
        for wk in sorted(f[f.season == s].week.unique()):
            lo = max(start, s - window) if window else start
            train = played[(played.season >= lo) & ((played.season < s) | ((played.season == s) & (played.week < wk)))]
            test = f[(f.season == s) & (f.week == wk)]
            h = test[test.home == 1].set_index("game_id"); a = test[test.home == 0].set_index("game_id"); ids = h.index.intersection(a.index)
            if len(ids) == 0:
                continue
            sw = season_w ** (s - train.season.values) * np.where(train.season.values == s, cur_w, 1.0)
            m = make_pipeline(StandardScaler(), Ridge(alpha=alpha)).fit(train[M.FEATS].values, train.pf.values, ridge__sample_weight=sw)
            he, ae = m.predict(h.loc[ids, M.FEATS].values), m.predict(a.loc[ids, M.FEATS].values)
            tlo = max(start, s - t_window) if t_window else start
            ttr = train[train.season >= tlo]
            gtr, gte = M._game_frame(ttr), M._game_frame(test).reindex(ids)
            tw = t_season_w ** (s - pd.Series(ttr.set_index("game_id").season).groupby(level=0).first().reindex(gtr.index).values)
            tm = make_pipeline(StandardScaler(), Ridge(alpha=t_alpha)).fit(gtr[M.TOTAL_FEATS].values, gtr.total.values, ridge__sample_weight=tw)
            rows.append(pd.DataFrame({"game_id": ids, "season": s, "week": wk, "he": he, "ae": ae, "tot": tm.predict(gte[M.TOTAL_FEATS].values)}))
    p = pd.concat(rows, ignore_index=True).merge(GAMES, on="game_id")
    p = p[(p.game_type == "REG") & p.result.notna()]
    sc = pd.read_parquet(OUT / "games.parquet").set_index("game_id")
    p["hs"], p["as_"] = p.game_id.map(sc.home_score), p.game_id.map(sc.away_score)
    return p


def score(p, label, **kw):
    r = {"variant": label, **kw}
    for w, (a, b) in W.items():
        d = p[p.season.between(a, b)]
        r[f"team_{w}"] = round(float(pd.concat([(d.he - d.hs).abs(), (d.ae - d.as_).abs()]).mean()), 4)
        r[f"margin_{w}"] = round(float(((d.he - d.ae) - d.result).abs().mean()), 4)
        r[f"total_{w}"] = round(float((d.tot - d.total).abs().mean()), 4)
        x = d[d.spread_line.notna() & (d.week <= 17)]; e = (x.he - x.ae) - x.spread_line; bb = x[e.abs() >= 4]; c = (bb.result - bb.spread_line) * np.sign(e[e.abs() >= 4])
        r[f"4+_{w}"] = f"{int((c > 0).sum())}-{int((c < 0).sum())}"
        y = d[d.total_line.notna() & (d.week <= 17)]; te = y.tot - y.total_line; ub = y[te <= -3]; r[f"u3_{w}"] = f"{int((ub.total < ub.total_line).sum())}-{int((ub.total > ub.total_line).sum())}"
    print({k: v for k, v in r.items() if k.startswith(("variant", "margin", "4+"))}, flush=True)
    return r


def finish(rows, part):
    o = pd.DataFrame(rows); b = o.iloc[0]
    for w in W:
        for k in ("team", "margin", "total"):
            o[f"d_{k}_{w}"] = (o[f"{k}_{w}"] - b[f"{k}_{w}"]).round(4)
    o["margin_better_all3"] = [all(r[f"d_margin_{w}"] < 0 for w in W) for _, r in o.iterrows()]
    o["team_better_all3"] = [all(r[f"d_team_{w}"] < 0 for w in W) for _, r in o.iterrows()]
    o["total_better_all3"] = [all(r[f"d_total_{w}"] < 0 for w in W) for _, r in o.iterrows()]
    o.to_csv(REP / f"sweep_{part}.csv", index=False)


def part_ratings():
    tg = pd.read_parquet(OUT / "team_games.parquet"); games = pd.read_parquet(OUT / "games.parquet"); qb = pd.read_parquet(OUT / "qb_games.parquet")
    V = [("live", {})] + [(f"decay {v}", {"decay": v}) for v in (0.90, 0.92, 0.96, 0.98)] + [(f"last season {v}", {"prior": v}) for v in (0.5, 0.65, 1.0)] + \
        [(f"pull to average {v}", {"alpha": v}) for v in (8.0, 24.0, 32.0)] + [(f"QB shrink {v}", {"qb_k": v}) for v in (100.0, 250.0)] + \
        [(f"QB decay per game {v}", {"qb_decay": v}) for v in (0.97, 0.995)] + [(f"QB fade per season {v}", {"qb_season_fade": v}) for v in (0.7, 0.9)] + \
        [(f"QB replacement {v}", {"qb_prior": v}) for v in (-0.08, -0.16)] + \
        [("decay 0.96 + last season 1.0", {"decay": 0.96, "prior": 1.0}), ("decay 0.92 + last season 0.65", {"decay": 0.92, "prior": 0.65})]
    rows = []
    for lab, chg in V:
        p = {**R.DEFAULT, **chg}; f = M.with_trends(R.build_features(p, tg=tg, games=games, qb=qb)); rows.append(score(price(f), lab, **{k: str(v) for k, v in chg.items()}))
        finish(rows, "ratings")


def part_fit():
    f = M.with_trends(pd.read_parquet(OUT / "features_asof.parquet"))
    V = [("live", {})] + [(f"last {n} seasons only", {"window": n}) for n in (3, 5, 8)] + [(f"recent seasons weigh {v} per season back", {"season_w": v}) for v in (0.95, 0.9, 0.8)] + \
        [(f"this season's games x{v}", {"cur_w": v}) for v in (1.5, 2.0, 3.0)] + [(f"ridge {v}", {"alpha": v}) for v in (1.0, 3.0, 30.0, 100.0)]
    rows = []
    for lab, kw in V:
        rows.append(score(price(f, **kw), lab, **{k: str(v) for k, v in kw.items()})); finish(rows, "fit")
    # how long the offseason-turnover input lasts, when "out of the race" begins and its cut
    for lab, var, vals in (("turnover input lasts through week", "EARLY_WEEKS", (4, 6, 10, 12)), ("out of the race from week", "LATE_WEEK", (10, 14)), ("out of the race at win rate", "DEAD_PCT", (0.3, 0.5))):
        old = getattr(M, var)
        for v in vals:
            setattr(M, var, v)
            try:
                rows.append(score(price(f), f"{lab} {v}", **{var: str(v)}))
            finally:
                setattr(M, var, old)
            finish(rows, "fit")


def part_totals():
    f = M.with_trends(pd.read_parquet(OUT / "features_asof.parquet"))
    V = [("live", {})] + [(f"total ridge {v}", {"t_alpha": v}) for v in (1.0, 3.0, 30.0, 100.0)] + [(f"total: last {n} seasons", {"t_window": n}) for n in (3, 5, 8)] + \
        [(f"total: recent seasons weigh {v}", {"t_season_w": v}) for v in (0.9, 0.8, 0.7)]
    rows = []
    for lab, kw in V:
        rows.append(score(price(f, **kw), lab, **{k: str(v) for k, v in kw.items()})); finish(rows, "totals")


if __name__ == "__main__":
    {"ratings": part_ratings, "fit": part_fit, "totals": part_totals}[sys.argv[1]]()
