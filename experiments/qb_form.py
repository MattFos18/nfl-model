"""This season's QB form beside the career rating (25 Sep 2026, Matt: "Jordan Love should not be a top 10 QB ... update
our rating system"). The QB rating is a career-long decayed EPA per dropback (0.985 a game, 0.8 a season back, shrunk
to replacement), so Love (+0.275 in 2025, first in the league) stays near the top after three poor 2026 starts
(-0.052 on 134 dropbacks). Making the whole rating fade faster was tested (experiments/sweep_all.py, sweep_confirm.py):
better team points, worse spread bets. Here the career rating stays and the starter's EPA per dropback this season
(before the game, shrunk toward his career rating with k dropbacks of weight) enters as its own input, so the fit
decides how much this season counts and when. k = 50, 100, 200; also the opponent's QB form (the other side's
passing game sets the pace and the script). Walk-forward 2015-2025, scored on 2015-18, 2019-22, 2023-25.
Writes reports/qb_form.csv."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import numpy as np, pandas as pd
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from nflmodel import model as M
from nflmodel.model import OUT

REP = Path(__file__).resolve().parent.parent / "reports"


def main():
    f = M.prep(M.with_trends(pd.read_parquet(OUT / "features_asof.parquet")))
    q = pd.read_parquet(OUT / "qb_games.parquet").sort_values(["qb_id", "season", "week"])
    g = q.groupby(["qb_id", "season"])
    q["db_before"] = g.dropbacks.cumsum() - q.dropbacks; q["epa_before"] = g.qb_epa.cumsum() - q.qb_epa
    key = q.set_index(["qb_id", "season", "week"])[["db_before", "epa_before"]]
    # the starter's this-season dropbacks and EPA before the game; a QB who has not played this season has none
    last = q.groupby(["qb_id", "season"]).agg(db=("dropbacks", "sum"), epa=("qb_epa", "sum"))
    def before(qid, s, w):
        if not isinstance(qid, str):
            return 0.0, 0.0
        x = q[(q.qb_id == qid) & (q.season == s) & (q.week < w)]
        return float(x.dropbacks.sum()), float(x.qb_epa.sum())
    cache = {}
    dbs, eps = [], []
    for qid, s, w in zip(f.qb_id, f.season, f.week):
        k_ = (qid, s, w)
        if k_ not in cache:
            cache[k_] = before(qid, s, w)
        dbs.append(cache[k_][0]); eps.append(cache[k_][1])
    f["qb_db_season"], f["qb_epa_season"] = dbs, eps
    for k in (50, 100, 200):
        f[f"qb_form_k{k}"] = (f.qb_epa_season + k * f.qb_rating) / (f.qb_db_season + k) - f.qb_rating   # this season's pull away from the career rating
    o = f[["game_id", "team"] + [f"qb_form_k{k}" for k in (50, 100, 200)]].rename(columns={"team": "opp", **{f"qb_form_k{k}": f"opp_qb_form_k{k}" for k in (50, 100, 200)}})
    f = f.merge(o, on=["game_id", "opp"], how="left")
    x = f[(f.game_id == "2026_03_ATL_GB")][["team", "qb_rating", "qb_db_season", "qb_epa_season", "qb_form_k100"]]
    print(x.round(4).to_string(index=False))
    V = {"live": []}
    for k in (50, 100, 200):
        V[f"form k{k}"] = [f"qb_form_k{k}"]; V[f"form k{k} + opponent's"] = [f"qb_form_k{k}", f"opp_qb_form_k{k}"]
    newc = list(dict.fromkeys(c for v in V.values() for c in v)); f[newc] = f[newc].fillna(0.0)
    played = f[f.pf.notna()]; rows = []
    for s in range(2015, 2026):
        for wk in sorted(f[f.season == s].week.unique()):
            tr = played[(played.season >= 2013) & ((played.season < s) | ((played.season == s) & (played.week < wk)))]
            te = f[(f.season == s) & (f.week == wk)]
            h = te[te.home == 1].set_index("game_id"); a = te[te.home == 0].set_index("game_id"); ids = h.index.intersection(a.index)
            if not len(ids):
                continue
            gg = pd.DataFrame({"game_id": ids, "season": s, "week": wk})
            for lab, ex in V.items():
                c = list(M.FEATS) + ex; m = make_pipeline(StandardScaler(), Ridge(alpha=10.0)).fit(tr[c].values, tr.pf.values)
                gg[f"h|{lab}"], gg[f"a|{lab}"] = m.predict(h.loc[ids, c].values), m.predict(a.loc[ids, c].values)
            rows.append(gg)
        print("priced", s, flush=True)
    P = pd.concat(rows).merge(pd.read_parquet(OUT / "games.parquet")[["game_id", "game_type", "home_score", "away_score", "result", "spread_line", "total", "total_line"]], on="game_id")
    P = P[(P.game_type == "REG") & P.result.notna()]
    out = []
    for lab in V:
        r = {"variant": lab}
        for w, (a_, b_) in {"2015-18": (2015, 2018), "2019-22": (2019, 2022), "2023-25": (2023, 2025)}.items():
            d = P[P.season.between(a_, b_)]; sp = d[f"h|{lab}"] - d[f"a|{lab}"]
            r[f"margin_{w}"] = round(float((sp - d.result).abs().mean()), 4)
            r[f"team_{w}"] = round(float(pd.concat([(d[f"h|{lab}"] - d.home_score).abs(), (d[f"a|{lab}"] - d.away_score).abs()]).mean()), 4)
            x = d[d.spread_line.notna() & (d.week <= 17)]; e = (x[f"h|{lab}"] - x[f"a|{lab}"]) - x.spread_line; k_ = e.abs() >= 4; c_ = (x.result - x.spread_line)[k_] * np.sign(e[k_])
            r[f"4+_{w}"] = f"{int((c_ > 0).sum())}-{int((c_ < 0).sum())}"
        out.append(r); print(r, flush=True)
    pd.DataFrame(out).to_csv(REP / "qb_form.csv", index=False)


if __name__ == "__main__":
    main()
