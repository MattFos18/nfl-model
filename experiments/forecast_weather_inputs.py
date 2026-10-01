"""Wind and cold inputs trained on forecasts, not the weather that happened (1 Oct 2026).

The rain fix (experiments/rain_points.py, adopted as model.RAIN_FC) found the totals equation learned rain from the
weather that happened but priced upcoming games on a forecast, and that training it on the forecast improved the total
on every window. The same mismatch is left in two inputs (docs/handoff.md, known quirks): wind_out (both points
equations and the totals equation) and cold (under 35 F outdoors) read, for every played game, the schedule's recorded
weather, while an upcoming game is priced on a kickoff forecast. Variants, each refit walk-forward 2015-2025:
  W  wind = the forecast wind the wind points read (model._wind_readings: GFS MOS and Japan's model, 2018 on) where
     there is one, the recorded wind before;
  C  temp = the GFS MOS kickoff temperature (forecast_history gfs_temp_d0, else d1) where there is one;
  WC both.
Scored through nflmodel.study_gate on 2015-18 / 2019-22 / 2023-25: team points miss (the game model's yardstick), with
the total and margin miss shown, and the live spread flag (edge 4) and totals flag (55% under) records for the no-bet-
cost part. --placebo V runs 50 within-season shuffles of variant V's forecast values (about an hour).
Writes reports/forecast_weather_inputs.{md,csv}.

    python -m experiments.forecast_weather_inputs [--placebo W]
"""
from __future__ import annotations
import sys
import numpy as np, pandas as pd
from nflmodel import backtest as B, model as M, picks as P, study_gate as G
from nflmodel.features import OUT, ROOT
from nflmodel.forecast_history import OUTF

REP = ROOT / "reports"
WIN = {"2015-18": (2015, 2018), "2019-22": (2019, 2022), "2023-25": (2023, 2025)}
GAMES = pd.read_parquet(OUT / "games.parquet")


def readings():
    h = pd.read_csv(OUTF).set_index("game_id")
    wind = pd.Series(M._wind_readings(), dtype=float)
    temp = h.gfs_temp_d0.fillna(h.gfs_temp_d1).astype(float)
    return wind, temp


def variant(f: pd.DataFrame, v: str, wind: pd.Series, temp: pd.Series) -> pd.DataFrame:
    f = f.copy(); played = f.game_id.isin(GAMES[GAMES.home_score.notna()].game_id)
    if "W" in v:
        w = f.game_id.map(wind); m = played & w.notna(); f.loc[m, "wind"] = w[m]
    if "C" in v:
        t = f.game_id.map(temp); m = played & t.notna(); f.loc[m, "temp"] = t[m]
    return f


def score(pred: pd.DataFrame) -> dict:
    d = B.join(pred, GAMES); d = d[(d.game_type == "REG") & d.season.between(2015, 2025)]
    out = {}
    for w, (lo, hi) in WIN.items():
        x = d[d.season.between(lo, hi)]
        tp = float(np.r_[x.home_err.abs(), x.away_err.abs()].mean())
        sp = P.record(x, P.rule_mask(x, P.SPREAD_EDGE)); tf = P.record(x, P.rule_mask(x, P.TOTAL_SHADOW["prob"], "under_prob"), "under_prob")
        out[w] = {"team": tp, "total": float(x.total_err.abs().mean()), "margin": float(x.margin_err.abs().mean()), "spread": sp, "totals": tf}
    return out


def run(f, v, wind, temp):
    return score(M.walk_forward(variant(f, v, wind, temp) if v != "base" else f, range(2015, 2026), 10.0))


def gate_rows(base, sc, placebo=None):
    return G.gate({w: (base[w]["team"], sc[w]["team"]) for w in WIN},
                  {w: {"spread flag": (base[w]["spread"], sc[w]["spread"]), "totals flag": (base[w]["totals"], sc[w]["totals"])} for w in WIN},
                  placebo)


def shuffled(s: pd.Series, rng) -> pd.Series:
    seas = s.index.str[:4]; out = s.copy()
    for y in seas.unique():
        ix = np.flatnonzero((seas == y) & s.notna().values); out.iloc[ix] = s.iloc[ix].values[rng.permutation(len(ix))]
    return out


def main():
    f = M.with_trends(pd.read_parquet(OUT / "features_asof.parquet")); wind, temp = readings()
    if "--placebo" in sys.argv:
        v = sys.argv[sys.argv.index("--placebo") + 1]; rng = np.random.default_rng(11)
        base = run(f, "base", wind, temp); real = run(f, v, wind, temp); gains = {w: [] for w in WIN}
        for i in range(50):
            sc = run(f, v, shuffled(wind, rng) if "W" in v else wind, shuffled(temp, rng) if "C" in v else temp)
            for w in WIN:
                gains[w].append(base[w]["team"] - sc[w]["team"])
            print(f"placebo {i + 1}/50", flush=True)
        rows = gate_rows(base, real, gains)
        pd.DataFrame(gains).to_csv(REP / f"forecast_weather_inputs_placebo_{v}.csv", index=False)
        md = REP / "forecast_weather_inputs.md"
        md.write_text(md.read_text(encoding="utf-8") + f"\n## Placebo, variant {v} (50 within-season shuffles)\n\n" + G.markdown(rows) + "\n", encoding="utf-8")
        print(G.markdown(rows)); return
    res = {v: run(f, v, wind, temp) for v in ("base", "W", "C", "WC")}
    rows = []
    for v, sc in res.items():
        for w in WIN:
            rows.append({"variant": v, "window": w, "team_miss": round(sc[w]["team"], 4), "total_miss": round(sc[w]["total"], 4),
                         "margin_miss": round(sc[w]["margin"], 4), "spread_flag": "%d-%d" % sc[w]["spread"], "totals_flag": "%d-%d" % sc[w]["totals"]})
    pd.DataFrame(rows).to_csv(REP / "forecast_weather_inputs.csv", index=False)
    L = ["# Wind and cold trained on forecasts (1 Oct 2026)", "",
         "Each variant refit walk-forward 2015-2025. Team points miss is the yardstick; flags at the live rules (weeks 1-17).", "",
         "| Variant | Window | Team miss | Total miss | Margin miss | Spread flag | Totals flag |", "|---|---|---|---|---|---|---|"]
    L += [f"| {r['variant']} | {r['window']} | {r['team_miss']:.4f} | {r['total_miss']:.4f} | {r['margin_miss']:.4f} | {r['spread_flag']} | {r['totals_flag']} |" for r in rows]
    for v in ("W", "C", "WC"):
        L += ["", f"## Gate, variant {v} (parts 1 and 2; the placebo runs separately)", "", G.markdown(gate_rows(res["base"], res[v]))]
    (REP / "forecast_weather_inputs.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
