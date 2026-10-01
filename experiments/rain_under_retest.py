"""The blind rain under, re-tested on top of the model with rain in its total (1 Oct 2026).

reports/weather_forecast_retest.md found the under at a GFS rain chance of 50%+ went 102-60 on 2018-25 (blind, weeks
1-17) and listed it as a hidden-shadow candidate. Since then the totals equation reads the same forecast (model.RAIN_FC),
so the totals flag now picks up many of those games itself. The question here is what the rain under adds on top of
the bets already made: the totals flag (1 - p_over_emp >= 0.55) and the wind under (forecast wind 10+ mph).

  1. The rain under per window 2018 / 2019-22 / 2023-25 (forecasts start in 2018), blind and on games neither live
     rule already bets.
  2. The live totals bets (flag OR wind under) with and without the rain under added, wins minus losses and units at
     -110 per window: the rule-of-three "no bet cost" test turned around (adding must help every window).
  3. 200 within-season shuffles of the rain chance: the share of shuffles whose added units are as good.
Two variants only (rain 50+ and rain 70+), both from the earlier study, so nothing new is picked on these results.
The model is rerun walk-forward 2015-2025 first, so every number is the live code's. Writes reports/rain_under_retest.{md,csv}.

    python -m experiments.rain_under_retest
"""
from __future__ import annotations
import numpy as np, pandas as pd
from nflmodel import backtest as B, model as M, picks as P
from nflmodel.features import OUT, ROOT
from nflmodel.forecast_history import OUTF

REP = ROOT / "reports"
WIN = {"2018": (2018, 2018), "2019-22": (2019, 2022), "2023-25": (2023, 2025)}
NPLAC = 200
CUTS = {"rain50": 50.0, "rain70": 70.0}


def load():
    f = M.with_trends(pd.read_parquet(OUT / "features_asof.parquet"))
    pred = M.walk_forward(f, range(2015, 2026), 10.0)
    d = B.join(pred, pd.read_parquet(OUT / "games.parquet"))
    d = d[(d.game_type == "REG") & d.total_line.notna() & d.season.between(2018, 2025) & (d.week <= P.LAST_BET_WEEK)].reset_index(drop=True)
    h = pd.read_csv(OUTF).set_index("game_id")
    d["pop"] = d.game_id.map(h.gfs_pop_d0).fillna(d.game_id.map(h.gfs_pop_d1)).astype(float)
    d["cm"] = d.home_score + d.away_score - d.total_line
    d["flag"] = (1 - d.p_over_emp) >= P.TOTAL_SHADOW["prob"]
    d["wind"] = P.rule_mask(d, P.WIND_UNDER["mph"], "wind_under").values
    return d


def rec(d, m):
    f = m & (d.cm != 0); w = int((d.cm < 0)[f].sum()); l = int(f.sum()) - w
    return w, l, round(w - 1.1 * l, 1)


def windows(d, m):
    return {w: rec(d, m & d.season.between(lo, hi)) for w, (lo, hi) in WIN.items()} | {"all": rec(d, m)}


def study(d, pop):
    """Rows for one rain-chance column: the rule alone, its extra games, and the live totals bets with and without it."""
    live = d.flag | d.wind; rows = []
    for name, cut in CUTS.items():
        rain = (pop >= cut).fillna(False)
        for what, m in (("rain under, blind", rain), ("rain under, games no live rule bets", rain & ~live),
                        ("live totals bets", live), ("live totals bets + rain under", live | rain)):
            rows.append({"cut": name, "what": what} | windows(d, m))
    return rows


def main():
    d = load(); rng = np.random.default_rng(11)
    rows = study(d, d["pop"]); live = d.flag | d.wind
    out = pd.DataFrame(rows)
    # placebo: the rain chance shuffled within season; the added units (extra games only) as good as the real ones
    for name, cut in CUTS.items():
        real = rec(d, (d["pop"] >= cut).fillna(False) & ~live)[2]; good = 0
        for _ in range(NPLAC):
            pp = d["pop"].copy()
            for s in range(2018, 2026):
                ix = d.index[(d.season == s) & pp.notna()]; pp.loc[ix] = pp.loc[ix].values[rng.permutation(len(ix))]
            good += rec(d, (pp >= cut).fillna(False) & ~live)[2] >= real
        out.loc[out.cut == name, "placebo_share"] = round(good / NPLAC, 3)
    # does adding it help every window (wins minus losses and units)?
    for name in CUTS:
        a = out[(out.cut == name) & (out.what == "live totals bets")].iloc[0]; b = out[(out.cut == name) & (out.what == "live totals bets + rain under")].iloc[0]
        out.loc[out.cut == name, "helps_every_window"] = all((b[w][0] - b[w][1] >= a[w][0] - a[w][1]) and (b[w][2] >= a[w][2]) for w in WIN)
    REP.mkdir(exist_ok=True); out.to_csv(REP / "rain_under_retest.csv", index=False)
    fmt = lambda x: f"{x[0]}-{x[1]} ({x[2]:+.1f}u)"
    L = ["# Rain under, re-tested on the model with rain in its total (1 Oct 2026)", "",
         "Under at a GFS rain chance of 50%+ (or 70%+), weeks 1-17, against the closing total, graded at -110; 2018-2025",
         "(forecasts start in 2018). Live totals bets = the totals flag (55%+ under chance) or the wind under (10+ mph).",
         "Placebo: the rain chance shuffled within season, 200 draws; the share as good on the extra games' units.", "",
         "| Cut | Bets | 2018 | 2019-22 | 2023-25 | All |", "|---|---|---|---|---|---|"]
    for r in out.itertuples():
        L.append(f"| {r.cut} | {r.what} | {fmt(r._3)} | {fmt(r._4)} | {fmt(r._5)} | {fmt(r.all)} |")
    L += ["", "| Cut | Placebo share as good | Adding it helps every window |", "|---|---|---|"]
    for name in CUTS:
        x = out[out.cut == name].iloc[0]; L.append(f"| {name} | {x.placebo_share:.3f} | {'yes' if x.helps_every_window else 'no'} |")
    (REP / "rain_under_retest.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
