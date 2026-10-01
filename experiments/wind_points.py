"""Wind points in the model's total (1 Oct 2026, Matt: "have the wind impact the total score instead of just saying under").
Walk-forward: each season's band amounts (forecast wind [0, 10), [10, 15), 15+ mph) are each band's mean miss (actual total
minus the model's total) against the mean miss of every forecast game in the seasons before, shrunk by K = 50 games. Scored on
the total miss and the totals flag (1 - p_over_emp >= 55%, p_over_emp shifted by the same amount), 2019-22 and 2023-25 (2018
has no earlier forecasts), and against 50 within-season shuffles of the forecast. Reads data/weather/forecast_history.csv
through nflmodel/wind_live.readings and the prediction table from before the change (pass its path).

    python -m experiments.wind_points [pred_v3.parquet]
"""
from __future__ import annotations
import sys
import numpy as np, pandas as pd
from nflmodel import backtest as B
from nflmodel.features import OUT
from nflmodel.wind_live import readings

EDGES, K = [0, 10, 15, 99], 50


def adj(d, col="fw"):
    out = pd.Series(0.0, index=d.index)
    for s in range(2019, 2027):
        tr = d[(d.season < s) & d[col].notna()]; te = (d.season == s) & d[col].notna()
        if not len(tr) or not te.any():
            continue
        base = tr.r.mean(); e = tr.groupby(pd.cut(tr[col], EDGES, right=False), observed=True).r.agg(["sum", "size"])
        e = (e["sum"] - base * e["size"]) / (e["size"] + K)
        out[te] = pd.cut(d.loc[te, col], EDGES, right=False).map(e).astype(float).fillna(0).values
    return out


def main(pred_path=None):
    g = pd.read_parquet(OUT / "games.parquet"); p = pd.read_parquet(pred_path or OUT / "pred_v3.parquet")
    if "model_total_raw" in p:
        p = p.assign(model_total=p.model_total_raw)
    d = B.join(p, g); d = d[(d.game_type == "REG") & d.home_score.notna() & d.total_line.notna() & d.season.between(2015, 2025)].copy()
    d["fw"] = d.game_id.map(readings()); d["act"] = d.home_score + d.away_score; d["r"] = d.act - d.model_total
    a = adj(d)
    for w, (lo, hi) in {"2019-22": (2019, 2022), "2023-25": (2023, 2025)}.items():
        m = d.season.between(lo, hi) & d.fw.notna()
        print(w, "total miss", round(d.r[m].abs().mean(), 3), "->", round((d.r - a)[m].abs().mean(), 3))
    rng = np.random.default_rng(1); real = [(d.r[m].abs().mean() - (d.r - a)[m].abs().mean()) for m in [d.season.between(2019, 2022) & d.fw.notna(), d.season.between(2023, 2025) & d.fw.notna()]]
    hits = 0
    for _ in range(50):
        dd = d.copy()
        for s in dd.season.unique():
            ix = dd.index[(dd.season == s) & dd.fw.notna()]; dd.loc[ix, "fw"] = rng.permutation(dd.loc[ix, "fw"].values)
        aa = adj(dd)
        gain = [(d.r[m].abs().mean() - (d.r - aa)[m].abs().mean()) for m in [d.season.between(2019, 2022) & d.fw.notna(), d.season.between(2023, 2025) & d.fw.notna()]]
        hits += gain[0] >= real[0] or gain[1] >= real[1]
    print("shuffles as good on either window:", hits, "of 50")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
