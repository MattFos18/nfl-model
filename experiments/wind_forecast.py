"""Wind unders on what was knowable before kickoff (1 Oct 2026, Matt: "if we know wind unders go like that, why don't we
use the forecast an hour before kickoff, or probabilities, and compare the day before to what happened"). The friend's-
model study (reports/friend_ideas.md) found blind unders in outdoor games at 10+ mph went about 58% on 2015-25, but on the
wind that happened; the day-before forecast existed only for 2024-25 (52-47). This reruns the rule on the forecasts in
data/weather/forecast_history.csv (nflmodel/forecast_history.py: NWS MOS GFS wind every season, the National Blend's wind
and gust from Nov 2018, each the day before and the last run out before kickoff; Japan's global model from Open-Meteo),
2018-2025, against the closing total.

  1. How close each forecast comes to the wind that happened (the schedule's reading), by lead.
  2. Blind unders when the forecast passes a cut, per window (2018 / 2019-22 / 2023-25), record, units at -110, and a
     placebo (the forecast shuffled within season among the same games, 200 draws: the share as good on units).
  3. The chance of 10+ mph from the forecasts together (a logistic on the last-run readings, fit on the seasons before
     each one), unders when that chance passes a cut.
  4. With the totals flag: flag AND windy, and flag OR windy.
The same games graded on the wind that happened, for comparison. Writes reports/wind_forecast.{md,csv}.

    python -m experiments.wind_forecast
"""
from __future__ import annotations
import numpy as np, pandas as pd
from sklearn.linear_model import LogisticRegression
from nflmodel import backtest as B, picks as P
from nflmodel.features import OUT, ROOT

REP, WX = ROOT / "reports", ROOT / "data" / "weather"
WIN = {"2018": (2018, 2018), "2019-22": (2019, 2022), "2023-25": (2023, 2025)}
READ = {"gfs_wind_d1": "GFS wind, day before", "gfs_wind_d0": "GFS wind, last run", "nbs_wind_d1": "Blend wind, day before",
        "nbs_wind_d0": "Blend wind, last run", "nbs_gust_d1": "Blend gust, day before", "nbs_gust_d0": "Blend gust, last run",
        "jma_wind_d1": "JMA wind, day before", "jma_wind_d0": "JMA wind, latest", "mean_wind_d0": "mean of the last-run winds",
        "wind": "wind that happened (schedule)"}
CUTS = {"wind": [8, 10, 12, 15], "gust": [15, 20, 25, 30]}
DRAWS, SEED = 200, 7


def data() -> pd.DataFrame:
    g = pd.read_parquet(OUT / "games.parquet")
    d = B.join(pd.read_parquet(OUT / "pred_v3.parquet"), g)
    d = d.merge(g[["game_id", "wind"]], on="game_id", how="left")   # the schedule's wind, the weather that happened
    d = d[(d.game_type == "REG") & d.home_score.notna() & d.total_line.notna() & d.season.between(2018, 2025)].copy()
    f = pd.read_csv(WX / "forecast_history.csv")
    for c in READ:
        if c in f:
            f[c] = pd.to_numeric(f[c], errors="coerce")
    f["mean_wind_d0"] = f[["gfs_wind_d0", "nbs_wind_d0", "jma_wind_d0"]].mean(axis=1)
    d = d.merge(f[["game_id"] + [c for c in READ if c in f and c != "wind"]], on="game_id", how="inner")
    d["cm"] = d.home_score + d.away_score - d.total_line
    d["flag"] = P.rule_mask(d, P.TOTAL_SHADOW["prob"], "under_prob")
    return d


def wl(d, m):
    x = d.cm[m & (d.cm != 0)]
    return int((x < 0).sum()), int((x > 0).sum())


def u(w, l):
    return w - 1.1 * l


def cell(d, m):
    w, l = wl(d, m)
    return f"{w}-{l}" + (f" ({100 * w / (w + l):.1f}%, {u(w, l):+.1f}u)" if w + l else "")


def windows(d, m) -> dict:
    out = {}
    for k, (a, b) in WIN.items():
        out[k] = cell(d, m & d.season.between(a, b))
    w, l = wl(d, m); out["all"] = cell(d, m); out["_units"] = u(w, l)
    return out


def placebo(d, col, cut, real_units, rng) -> float:
    """Share of within-season shuffles of the reading whose blind-under units match the real ones."""
    ok = d[col].notna().values; hits = 0
    for _ in range(DRAWS):
        v = d[col].values.copy()
        for s in d.season.unique():
            ix = np.where((d.season.values == s) & ok)[0]
            v[ix] = rng.permutation(v[ix])
        m = pd.Series(v >= cut, index=d.index) & ok
        w, l = wl(d, m)
        hits += u(w, l) >= real_units
    return hits / DRAWS


def chance_of_windy(d, cut=10.0) -> pd.Series:
    """Walk-forward chance that the wind that happened reaches cut, from the last-run forecasts (fit on earlier seasons)."""
    X = d[["gfs_wind_d0", "nbs_wind_d0", "jma_wind_d0"]].copy()
    X = X.apply(lambda r: r.fillna(r.mean()), axis=1)   # a missing reading takes the mean of the others
    y = (d.wind >= cut).astype(int); ok = X.notna().all(axis=1) & d.wind.notna()
    p = pd.Series(np.nan, index=d.index)
    for s in sorted(d.season.unique()):
        tr, te = ok & (d.season < s), X.notna().all(axis=1) & (d.season == s)
        if tr.sum() < 100 or not te.any():
            continue
        lr = LogisticRegression().fit(X[tr], y[tr]); p[te] = lr.predict_proba(X[te])[:, 1]
    return p


def main():
    d = data(); rng = np.random.default_rng(SEED); rows, L = [], ["# Wind unders on forecasts, 2018-2025", ""]
    L += [f"{len(d)} outdoor and open-roof regular-season games with a closing total and a stored forecast "
          f"({', '.join(f'{s}: {n}' for s, n in d.season.value_counts().sort_index().items())}). Unders graded at -110 against the closing total.", ""]
    # 1. forecast against what happened
    acc = []
    for c, lab in READ.items():
        if c == "wind" or c not in d or "gust" in c:
            continue
        ok = d[c].notna() & d.wind.notna()
        acc.append({"forecast": lab, "games": int(ok.sum()), "correlation with the wind that happened": round(d.loc[ok, c].corr(d.loc[ok, "wind"]), 2),
                    "mean gap (mph)": round((d.loc[ok, c] - d.loc[ok, "wind"]).abs().mean(), 1), "bias (mph)": round((d.loc[ok, c] - d.loc[ok, "wind"]).mean(), 1),
                    "agree on 10+": f"{100 * ((d.loc[ok, c] >= 10) == (d.loc[ok, 'wind'] >= 10)).mean():.0f}%"})
    L += ["## 1. How close each forecast came", "", pd.DataFrame(acc).to_markdown(index=False), ""]
    # 2. blind unders
    for c, lab in READ.items():
        if c not in d:
            continue
        for cut in CUTS["gust" if "gust" in c else "wind"]:
            m = d[c].notna() & (d[c] >= cut); r = windows(d, m)
            pl = placebo(d, c, cut, r["_units"], rng) if c != "wind" else np.nan
            rows.append({"part": "blind", "reading": lab, "cut": cut, **{k: v for k, v in r.items() if not k.startswith("_")}, "units": round(r["_units"], 1), "placebo share as good": pl})
    # 3. chance of 10+
    d["p10"] = chance_of_windy(d)
    for cut in [0.4, 0.5, 0.6, 0.7]:
        m = d.p10.notna() & (d.p10 >= cut); r = windows(d, m)
        rows.append({"part": "chance", "reading": "chance the wind reaches 10+ mph (walk-forward, from 2019)", "cut": cut,
                     **{k: v for k, v in r.items() if not k.startswith("_")}, "units": round(r["_units"], 1), "placebo share as good": np.nan})
    # 4. with the flag
    for c in ["gfs_wind_d0", "mean_wind_d0", "nbs_gust_d0", "wind"]:
        if c not in d:
            continue
        for cut in ([10, 12] if "gust" not in c else [20, 25]):
            wd = d[c].notna() & (d[c] >= cut)
            for how, m in [("flag AND windy", d.flag & wd), ("flag OR windy", d.flag | wd)]:
                r = windows(d, m)
                rows.append({"part": how, "reading": READ[c], "cut": cut, **{k: v for k, v in r.items() if not k.startswith("_")}, "units": round(r["_units"], 1), "placebo share as good": np.nan})
    r = windows(d, d.flag)
    rows.append({"part": "the totals flag on these games", "reading": "", "cut": np.nan, **{k: v for k, v in r.items() if not k.startswith("_")}, "units": round(r["_units"], 1), "placebo share as good": np.nan})
    T = pd.DataFrame(rows); T.to_csv(REP / "wind_forecast.csv", index=False)
    for part, x in T.groupby("part", sort=False):
        L += [f"## {part}", "", x.drop(columns=["part"]).to_markdown(index=False), ""]
    (REP / "wind_forecast.md").write_text("\n".join(L))
    print("\n".join(L))
    return T


if __name__ == "__main__":
    main()
