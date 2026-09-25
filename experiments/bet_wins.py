"""Betting wins first (25 Sep 2026, Matt: "I just want to increase accuracy and betting wins"). Our own data only; the
closing line is only what the bets are graded against.

One walk-forward pass over 2015-2025 (weekly refit, every game priced with earlier games only) that prices each game
under several spread and total models at once, then grades the model's side against the closing line:

  Spreads (team points, then home minus away):
    base           the live model (M.FEATS, ridge alpha 10)
    success        + success rate, offense and the opponent's defense
    split          + pass and rush EPA
    plays          + plays per game (pace)
    alpha3/alpha30 the same inputs, less / more shrinkage
    gbm            gradient-boosted trees on the live inputs (catches interactions a line cannot)
    blend_*        averages of the above (averaging models that err differently cuts the noise)
  Totals (the game total's own equation):
    base           the live model (M.TOTAL_FEATS)
    pace           + both teams' plays per game, offense and defense
    eff            + success rate and pass EPA sums
    avail          + skill players out, snaps out, offseason turnover, division game
    ref            + the referee's over rate
    all            every addition above
    teams          the two team scores added (home_exp + away_exp from the base spread model)
    gbm            gradient-boosted trees on the "all" inputs
    blend_*        averages

Output: reports/bet_wins_preds.parquet (every game, every variant) and reports/bet_wins.csv (records by window and edge,
misses, pooled 2019-25 and a bootstrap of the gain against the live model)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import numpy as np, pandas as pd
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import HistGradientBoostingRegressor
from nflmodel import model as M
from nflmodel.model import OUT

REP = Path(__file__).resolve().parent.parent / "reports"
SEASONS = range(2015, 2026)
SPREAD = {"base": (list(M.FEATS), 10.0), "success": (list(M.FEATS) + ["off_success", "def_success"], 10.0),
          "split": (list(M.FEATS) + ["off_pass_epa", "def_pass_epa", "off_rush_epa", "def_rush_epa"], 10.0),
          "plays": (list(M.FEATS) + ["off_plays", "def_plays"], 10.0), "alpha3": (list(M.FEATS), 3.0), "alpha30": (list(M.FEATS), 30.0)}
GAME_LEVEL = {"wind_out", "rain", "cold", "dome", "div_game", "ref_over"}
T_ADD = {"pace": ["off_plays", "def_plays"], "eff": ["off_success", "def_success", "off_pass_epa", "def_pass_epa"],
         "avail": ["skill_out_value", "off_snap_out", "off_turnover_early", "div_game"], "ref": ["ref_over"]}
TOTAL = {"base": list(M.TOTAL_FEATS)}
for k, v in T_ADD.items():
    TOTAL[k] = list(M.TOTAL_FEATS) + v
TOTAL["all"] = list(M.TOTAL_FEATS) + sum(T_ADD.values(), [])
BASE_T = {"off_sum": "off_epa_play", "def_sum": "def_epa_play", "pf_sum": "off_pf", "pa_sum": "def_pf", "qb_sum": "qb_rating", "qb_out_sum": "qb_out"}


def game_frame(x: pd.DataFrame, cols) -> pd.DataFrame:
    h = x[x.home == 1].set_index("game_id"); a = x[x.home == 0].set_index("game_id"); ids = h.index.intersection(a.index)
    out = {"total": (h.loc[ids, "pf"] + a.loc[ids, "pf"]).values}
    for c in cols:
        src = BASE_T.get(c, c)
        out[c] = h.loc[ids, src].values if c in GAME_LEVEL else (h.loc[ids, src] + a.loc[ids, src]).values
    return pd.DataFrame(out, index=ids)


def ridge(alpha):
    return make_pipeline(StandardScaler(), Ridge(alpha=alpha))


def gbm():
    return HistGradientBoostingRegressor(max_iter=300, learning_rate=0.03, max_leaf_nodes=8, min_samples_leaf=60, l2_regularization=1.0, random_state=0)


def predict():
    f = M.prep(M.with_trends(pd.read_parquet(OUT / "features_asof.parquet")))
    allc = sorted(set(sum([v for v, _ in SPREAD.values()], [])) | set(sum(T_ADD.values(), [])))
    f[allc] = f[allc].astype(float)
    played = f[f.pf.notna()]
    tcols = sorted(set(sum(TOTAL.values(), [])))
    rows = []
    for s in SEASONS:
        for wk in sorted(f[f.season == s].week.unique()):
            train = played[(played.season >= 2013) & ((played.season < s) | ((played.season == s) & (played.week < wk)))]
            test = f[(f.season == s) & (f.week == wk)].copy()
            mu = train[allc].mean(); train = train.fillna({c: mu[c] for c in allc}); test = test.fillna({c: mu[c] for c in allc})
            h = test[test.home == 1].set_index("game_id"); a = test[test.home == 0].set_index("game_id"); ids = h.index.intersection(a.index)
            if len(ids) == 0:
                continue
            g = pd.DataFrame({"game_id": ids, "season": s, "week": wk})
            for name, (feats, al) in SPREAD.items():
                m = ridge(al).fit(train[feats].values, train.pf.values); e = pd.Series(m.predict(test[feats].values), index=test.index)
                eh, ea = e[test.home == 1].values, e[test.home == 0].values
                hh = pd.Series(eh, index=test[test.home == 1].game_id).reindex(ids).values; aa = pd.Series(ea, index=test[test.home == 0].game_id).reindex(ids).values
                g[f"sp_{name}"] = hh - aa
                if name == "base":
                    g["tot_teams"] = hh + aa
            m = gbm().fit(train[list(M.FEATS)].values, train.pf.values); e = m.predict(test[list(M.FEATS)].values)
            hh = pd.Series(e[(test.home == 1).values], index=test[test.home == 1].game_id).reindex(ids).values
            aa = pd.Series(e[(test.home == 0).values], index=test[test.home == 0].game_id).reindex(ids).values
            g["sp_gbm"] = hh - aa
            gtr, gte = game_frame(train, tcols), game_frame(test, tcols).reindex(ids)
            for name, cols in TOTAL.items():
                g[f"tot_{name}"] = ridge(10.0).fit(gtr[cols].values, gtr.total.values).predict(gte[cols].values)
            g["tot_gbm"] = gbm().fit(gtr[TOTAL["all"]].values, gtr.total.values).predict(gte[TOTAL["all"]].values)
            rows.append(g)
        print("priced", s, flush=True)
    p = pd.concat(rows, ignore_index=True)
    sp = [c for c in p.columns if c.startswith("sp_")]; tt = [c for c in p.columns if c.startswith("tot_")]
    p["sp_blend_lin"] = p[["sp_base", "sp_success", "sp_split", "sp_plays"]].mean(axis=1)
    p["sp_blend_gbm"] = p[["sp_base", "sp_gbm"]].mean(axis=1)
    p["sp_blend_all"] = p[sp].mean(axis=1)
    p["tot_blend_lin"] = p[["tot_base", "tot_pace", "tot_eff", "tot_avail", "tot_ref", "tot_all", "tot_teams"]].mean(axis=1)
    p["tot_blend_gbm"] = p[["tot_all", "tot_gbm"]].mean(axis=1)
    p["tot_blend_all"] = p[tt].mean(axis=1)
    g = pd.read_parquet(OUT / "games.parquet")[["game_id", "game_type", "result", "total", "spread_line", "total_line"]]
    p = p.merge(g, on="game_id")
    p = p[(p.game_type == "REG") & p.result.notna()]
    p.to_parquet(REP / "bet_wins_preds.parquet", index=False)
    return p


WIN = {"2015-18": (2015, 2018), "2019-22": (2019, 2022), "2023-25": (2023, 2025), "2019-25": (2019, 2025)}


def rec(d, col, line, actual, cut):
    e = d[col] - d[line]; b = d[e.abs() >= cut]; diff = b[actual] - b[line]; side = np.sign(b[col] - b[line])
    w = int(((diff * side) > 0).sum()); l = int(((diff * side) < 0).sum())
    return w, l


def score(p):
    p = p[p.week <= 17]
    out = []
    for kind, pre, line, actual, cuts in (("spread", "sp_", "spread_line", "result", (3, 4, 5)), ("total", "tot_", "total_line", "total", (3, 4, 5, 6))):
        for col in [c for c in p.columns if c.startswith(pre)]:
            r = {"kind": kind, "variant": col[len(pre):]}
            for w, (a, b) in WIN.items():
                d = p[p.season.between(a, b) & p[line].notna()]
                r[f"mae_{w}"] = round(float((d[col] - d[actual]).abs().mean()), 3)
                for c in cuts:
                    wi, lo = rec(d, col, line, actual, c); r[f"{c}+_{w}"] = f"{wi}-{lo}"; r[f"{c}+pct_{w}"] = round(wi / max(1, wi + lo), 3)
                wi, lo = rec(d, col, line, actual, 0.0001); r[f"all_{w}"] = round(wi / max(1, wi + lo), 3)
            # bootstrap over games, 2019-25: the share of resamples where this variant misses less than the live model
            d = p[p.season.between(2019, 2025) & p[line].notna()]; base = pre + "base"
            gain = ((d[base] - d[actual]).abs() - (d[col] - d[actual]).abs()).values
            rng = np.random.default_rng(0); bs = [gain[rng.integers(0, len(gain), len(gain))].mean() for _ in range(2000)]
            r["gain_2019-25"] = round(float(gain.mean()), 4); r["p_better"] = round(float(np.mean(np.array(bs) > 0)), 3)
            out.append(r)
    o = pd.DataFrame(out); o.to_csv(REP / "bet_wins.csv", index=False)
    return o


if __name__ == "__main__":
    p = pd.read_parquet(REP / "bet_wins_preds.parquet") if "--score" in sys.argv else predict()
    o = score(p)
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 60)
    keep = ["kind", "variant"] + [f"mae_{w}" for w in WIN] + ["gain_2019-25", "p_better"]
    print(o[keep].to_string(index=False))
    for kind, cuts in (("spread", (3, 4, 5)), ("total", (3, 4, 5, 6))):
        print(o[o.kind == kind][["variant"] + [f"{c}+_{w}" for c in cuts for w in ("2015-18", "2019-22", "2023-25")]].to_string(index=False))
