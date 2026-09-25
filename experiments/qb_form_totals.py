"""The starter's this-season form (experiments/qb_form.py, k = 100 and 200) summed over both teams, in the total
equation (25 Sep 2026): it lowered the team-points miss on all three windows but hurt the spread on 2019-22; does it
help the total? Walk-forward 2015-2025; total miss and the totals flag (under at a 55%+ chance) by window.
Writes reports/qb_form_totals.csv."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import numpy as np, pandas as pd
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from nflmodel import model as M
from nflmodel.model import OUT


def main():
    f = M.prep(M.with_trends(pd.read_parquet(OUT / "features_asof.parquet")))
    q = pd.read_parquet(OUT / "qb_games.parquet"); qd = {}
    for (qid, s), x in q.groupby(["qb_id", "season"]):
        x = x.sort_values("week"); qd[(qid, s)] = (x.week.values, x.dropbacks.values, x.qb_epa.values)
    def before(qid, s, w):
        v = qd.get((qid, s))
        if v is None:
            return 0.0, 0.0
        m = v[0] < w; return float(v[1][m].sum()), float(v[2][m].sum())
    b = [before(qid, s, w) if isinstance(qid, str) else (0.0, 0.0) for qid, s, w in zip(f.qb_id, f.season, f.week)]
    f["db_s"], f["epa_s"] = [x[0] for x in b], [x[1] for x in b]
    for k in (100, 200):
        f[f"form{k}"] = (f.epa_s + k * f.qb_rating) / (f.db_s + k) - f.qb_rating
    h = f[f.home == 1].set_index("game_id"); a = f[f.home == 0].set_index("game_id")
    extra = pd.DataFrame({f"form{k}_sum": (h[f"form{k}"] + a[f"form{k}"].reindex(h.index)) for k in (100, 200)})
    V = {"live": [], "form k100": ["form100_sum"], "form k200": ["form200_sum"]}
    played = f[f.pf.notna()]; rows = []
    for s in (range(2015, 2016) if "--debug" in sys.argv else range(2015, 2026)):
        for wk in sorted(f[f.season == s].week.unique()):
            tr = played[(played.season >= 2013) & ((played.season < s) | ((played.season == s) & (played.week < wk)))]
            te = f[(f.season == s) & (f.week == wk)]
            gtr = M._game_frame(tr).join(extra); gte = M._game_frame(te).join(extra)
            if not len(gte):
                continue
            o = pd.DataFrame(index=gte.index)
            for lab, ex in V.items():
                c = list(M.TOTAL_FEATS) + ex; m = make_pipeline(StandardScaler(), Ridge(alpha=10.0)).fit(gtr[c].values, gtr.total.values)
                o[lab] = m.predict(gte[c].values); res = gtr.total.values - m.predict(gtr[c].values)
                o[f"pu|{lab}"] = np.nan; o[f"res|{lab}"] = [res] * len(o)
            o["season"], o["week"] = s, wk; rows.append(o)
        print("priced", s, flush=True)
    P = pd.concat(rows); gm = pd.read_parquet(OUT / "games.parquet").set_index("game_id")
    P["total"] = gm.total.reindex(P.index); P["line"] = gm.total_line.reindex(P.index); P["gtype"] = gm.game_type.reindex(P.index)
    P = P[(P.gtype == "REG") & P.total.notna()]
    out = []
    for lab in V:
        pu = [float(np.mean(mt + r_ < L) / max(1e-9, np.mean(mt + r_ != L))) if pd.notna(L) else np.nan for mt, r_, L in zip(P[lab], P[f"res|{lab}"], P.line)]
        P[f"pu|{lab}"] = pu; r = {"variant": lab}
        for w, (a_, b_) in {"2015-18": (2015, 2018), "2019-22": (2019, 2022), "2023-25": (2023, 2025)}.items():
            d = P[P.season.between(a_, b_)]; r[f"total_{w}"] = round(float((d[lab] - d.total).abs().mean()), 4)
            x = d[(d.week <= 17) & d.line.notna() & (d[f"pu|{lab}"] >= 0.55)]; r[f"u55_{w}"] = f"{int((x.total < x.line).sum())}-{int((x.total > x.line).sum())}"
        out.append(r); print(r, flush=True)
    pd.DataFrame(out).to_csv("reports/qb_form_totals.csv", index=False)


if __name__ == "__main__":
    main()
