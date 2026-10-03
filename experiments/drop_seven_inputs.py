"""Drop the seven failing inputs (3 Oct 2026, Matt's yes on condition the margin miss is not worse on any window).
Pre-registration and results: reports/drop_seven_inputs.md.

The live model (as on main before the drop: the 22 points inputs, the 11 totals inputs) against the same model without
neutral, dome, rain, div_game, qb_out (points equations) and pf_sum, qb_out_sum (totals equation), each refit
walk-forward 2015-2025 with model.walk_forward (data/processed/trees_cache.parquet read only). Per window: margin, team
points and total miss; Brier of the raw and calibrated home win chance and the calibration error; the spread flag,
totals flag and wind under. Study gate on each miss. Runs are kept in <tmp>/drop_seven_inputs.

    python -m experiments.drop_seven_inputs run live|drop   (one walk-forward; the two run in parallel)
    python -m experiments.drop_seven_inputs                 (score both; writes reports/drop_seven_inputs.csv and _results.md)
"""
from __future__ import annotations
import os
for _v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
import sys, tempfile
from pathlib import Path
import numpy as np, pandas as pd
from nflmodel import model as M, picks as P, study_gate as G
from nflmodel.features import OUT, ROOT

M.save_trees_cache = lambda: None   # an experiment never rewrites data/processed/trees_cache.parquet
from experiments import forecast_weather_backtest as FW   # noqa: E402  (score: misses and the three records)
from experiments import calibration_recheck as CR          # noqa: E402  (calibrated home win rows, Brier)

REP = ROOT / "reports"
TMP = Path(tempfile.gettempdir()) / "drop_seven_inputs"
WIN = {"2015-18": (2015, 2018), "2019-22": (2019, 2022), "2023-25": (2023, 2025)}
GAMES = pd.read_parquet(OUT / "games.parquet")
DROP_FEATS = ["neutral", "dome", "rain", "div_game", "qb_out"]
DROP_TOTAL = ["pf_sum", "qb_out_sum"]
# the live input lists as they stood before the drop (main 0788403f), so the comparison reruns after the code change too
FEATS_BEFORE = ["off_epa_play", "def_epa_play", "off_pf", "def_pf", "qb_rating", "home", "neutral", "dome", "wind_out", "cold", "rain",
                "warm_in_cold", "div_game", "qb_out", "skill_out_value", "opp_skill_out_value", "off_snap_out", "opp_def_snap_out",
                "off_turnover_early", "opp_def_turnover_early", "dead_late", "opp_dead_late"]
TOTAL_BEFORE = ["off_sum", "def_sum", "pf_sum", "pa_sum", "qb_sum", "qb_out_sum", "wind_out", "rain_fc", "cold", "dome", "qb_form_sum"]
TIE = 0.0005   # Matt's rule: a worse margin miss counts as a tie only within this


def run(kind: str) -> pd.DataFrame:
    feats = FEATS_BEFORE if kind == "live" else [c for c in FEATS_BEFORE if c not in DROP_FEATS]
    total = TOTAL_BEFORE if kind == "live" else [c for c in TOTAL_BEFORE if c not in DROP_TOTAL]
    keep_f, keep_t = list(M.FEATS), list(M.TOTAL_FEATS)
    M.FEATS[:] = feats; M.TOTAL_FEATS[:] = total; M.DIST.clear()
    try:
        with M.trees_cache_read_only():
            f = M.with_trends(pd.read_parquet(OUT / "features_asof.parquet"))
            return M.walk_forward(f, range(2015, 2026), M.RIDGE)
    finally:
        M.FEATS[:] = keep_f; M.TOTAL_FEATS[:] = keep_t


def win_chance(p: pd.DataFrame) -> dict:
    """Brier of the raw p_home (every regular-season game with a result, ties out) and of the calibrated chance (seasons with
    a fit in force, picks._home_rows / home_calibrations), and the calibrated chance's calibration error (10 equal bins)."""
    g = GAMES.set_index("game_id")
    d = p[(p.game_type == "REG") & p.p_home.notna()].copy()
    d["res"] = d.game_id.map(g.home_score) - d.game_id.map(g.away_score); d = d[d.res.notna() & (d.res != 0)]
    c = CR.logit_rows(P._home_rows(p, GAMES), "hw", P.home_calibrations(p, GAMES))
    out = {}
    for w, (lo, hi) in WIN.items():
        x = d[d.season.between(lo, hi)]; y = (x.res > 0).astype(float)
        cx = c[c.season.between(lo, hi)]
        _, bc = CR.scores(cx.cal, cx.y)
        b = pd.qcut(cx.cal.rank(method="first"), 10, labels=False)
        ece = float(cx.groupby(b).apply(lambda z: abs(z.cal.mean() - z.y.mean())).mean())
        out[w] = {"brier_raw": float(((x.p_home - y) ** 2).mean()), "brier_cal": bc, "cal_err": ece, "n_cal": len(cx)}
    return out


def main():
    TMP.mkdir(exist_ok=True)
    if len(sys.argv) > 2 and sys.argv[1] == "run":
        k = sys.argv[2]; p = run(k); p.to_parquet(TMP / f"{k}.parquet", index=False); print(k, "done", len(p), flush=True); return
    live, drop = pd.read_parquet(TMP / "live.parquet"), pd.read_parquet(TMP / "drop.parquet")
    sl, sd = FW.score(live), FW.score(drop); wl, wd = win_chance(live), win_chance(drop)
    rows = []
    for w in WIN:
        for name, a, b in [("margin miss", sl[w]["margin"], sd[w]["margin"]), ("team points miss", sl[w]["team"], sd[w]["team"]),
                           ("total miss", sl[w]["total"], sd[w]["total"]), ("Brier, raw win chance", wl[w]["brier_raw"], wd[w]["brier_raw"]),
                           ("Brier, calibrated win chance", wl[w]["brier_cal"], wd[w]["brier_cal"]), ("calibration error", wl[w]["cal_err"], wd[w]["cal_err"])]:
            rows.append({"window": w, "measure": name, "live": round(a, 5), "without": round(b, 5), "change": round(b - a, 5)})
        for name, r in [("spread flag", "spread"), ("totals flag", "totals"), ("wind under", "wind")]:
            (a1, a2), (b1, b2) = sl[w][r], sd[w][r]
            rows.append({"window": w, "measure": name, "live": f"{a1}-{a2}", "without": f"{b1}-{b2}", "change": (b1 - b2) - (a1 - a2)})
    pd.DataFrame(rows).to_csv(REP / "drop_seven_inputs.csv", index=False)
    margin_ok = {w: sd[w]["margin"] - sl[w]["margin"] <= TIE for w in WIN}
    L = ["# Drop the seven inputs: results (written by experiments/drop_seven_inputs.py)", "",
         "| Window | Margin miss | Team points miss | Total miss | Brier raw win | Brier calibrated win | Calibration error | Spread flag | Totals flag | Wind under |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    r2 = lambda t: "%d-%d" % tuple(t)
    for w in WIN:
        L.append(f"| {w} | {sl[w]['margin']:.4f} -> {sd[w]['margin']:.4f} | {sl[w]['team']:.4f} -> {sd[w]['team']:.4f} | {sl[w]['total']:.4f} -> {sd[w]['total']:.4f} | "
                 f"{wl[w]['brier_raw']:.4f} -> {wd[w]['brier_raw']:.4f} | {wl[w]['brier_cal']:.4f} -> {wd[w]['brier_cal']:.4f} | {wl[w]['cal_err']:.4f} -> {wd[w]['cal_err']:.4f} | "
                 f"{r2(sl[w]['spread'])} -> {r2(sd[w]['spread'])} | {r2(sl[w]['totals'])} -> {r2(sd[w]['totals'])} | {r2(sl[w]['wind'])} -> {r2(sd[w]['wind'])} |")
    L += ["", f"Calibrated win chance scored on {', '.join(str(wl[w]['n_cal']) for w in WIN)} games (seasons with a home calibration in force).", "",
          f"Margin rule (not worse on any window, ties within {TIE}): " + ", ".join(f"{w} {'ok' if o else 'WORSE'}" for w, o in margin_ok.items()) +
          f" -> {'implement' if all(margin_ok.values()) else 'do not implement'}", ""]
    for key in ("margin", "team", "total"):
        g = G.gate({w: (sl[w][key], sd[w][key]) for w in WIN},
                   {w: {"spread flag": (sl[w]["spread"], sd[w]["spread"]), "totals flag": (sl[w]["totals"], sd[w]["totals"]),
                        "wind under": (sl[w]["wind"], sd[w]["wind"])} for w in WIN})
        L += [f"## {key} miss (base = live, new = without the seven)", "", G.markdown(g), ""]
    (REP / "drop_seven_inputs_results.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L), flush=True)


if __name__ == "__main__":
    main()
