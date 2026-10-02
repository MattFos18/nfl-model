"""Calibration recheck on the honest backtest (2 Oct 2026). Pre-registration and results: reports/calibration_recheck.md.

The site's calibrated chances (picks.py) are fit on earlier seasons' backtest rows. The backtest changed today (leak fixes
#381, #384, #387; forecast-priced weather #389), so each calibration is rechecked on main's predictions rerun walk-forward
2015-2025 (model.walk_forward, weekly refit; trees read from the stored cache where their inputs match, refit otherwise,
never written to data/processed/trees_cache.parquet):
  C1  cover calibration (picks.calibration): the model side's cover chance; raw = the bell curve's p_cover_home
  C2  over calibration (picks.over_calibration): p_over_cal; raw = p_over_emp
  C3  home win calibration (picks.home_calibration): p_home_cal; raw = p_home
  C4s / C4t  teaser legs (picks.tease_calibration), spread and total; raw = the bell curve's 6-point teased chance
Each season is scored with the fit that would have been in force (earlier seasons of this table only), as the code does.
Per window (2016-18, 2019-22, 2023-25, regular season): log loss and Brier, raw and calibrated, and reliability by band.
Also the spread flag's record at |edge| 3, 3.5, 4, 4.5, 5 (weeks 1-17, closing line), report only.
Writes reports/calibration_recheck.csv and reports/calibration_recheck_results.md.

    python -m experiments.calibration_recheck [--reuse]   (--reuse: read the rerun table saved by the last run)
"""
from __future__ import annotations
import sys, tempfile
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.linear_model import LogisticRegression
from nflmodel import backtest as B, model as M, picks as P, study_gate as G
from nflmodel.features import OUT, ROOT

REP = ROOT / "reports"
TMP = Path(tempfile.gettempdir()) / "calibration_recheck_pred.parquet"
WIN = {"2016-18": (2016, 2018), "2019-22": (2019, 2022), "2023-25": (2023, 2025)}
GATE_KEY = {"2016-18": "2015-18", "2019-22": "2019-22", "2023-25": "2023-25"}   # study_gate's window names (2015 has no earlier fit)
GAMES = pd.read_parquet(OUT / "games.parquet")
CUTS = (3.0, 3.5, 4.0, 4.5, 5.0)
M.save_trees_cache = lambda: None   # an experiment never rewrites data/processed/trees_cache.parquet


def rerun() -> pd.DataFrame:
    if "--reuse" in sys.argv and TMP.exists():
        return pd.read_parquet(TMP)
    f = M.with_trends(pd.read_parquet(OUT / "features_asof.parquet"))
    p = M.walk_forward(f, range(2015, 2026), M.RIDGE)
    p.to_parquet(TMP, index=False)
    return p


def _lg(p):
    return 1.0 / (1.0 + np.exp(-np.asarray(p, dtype=float)))


def cover_rows(pred: pd.DataFrame, cal_from: int | None = None) -> pd.DataFrame:
    """Every regular-season game with a line, a result and a non-zero edge, pushes dropped: the model side's raw and
    calibrated cover chance and whether it covered. cal_from None: picks.calibration as coded (CAL_FROM); otherwise the
    same form fit from that season (the record-only variant)."""
    d = B.join(pred, GAMES); d = d[(d.game_type == "REG") & d.spread_line.notna()].copy()
    d["cm"] = d.home_score - d.away_score - d.spread_line
    d = d[(d.cm != 0) & (d.spread_edge != 0) & d.p_cover_home.notna()]
    d["y"] = (np.sign(d.spread_edge) == np.sign(d.cm)).astype(int)
    d["raw"] = np.where(d.spread_edge > 0, d.p_cover_home, 1 - d.p_cover_home)
    d["x"] = np.minimum(d.spread_edge.abs(), P.CAL_CAP)
    cal = []
    for s in sorted(d.season.unique()):
        if cal_from is None:
            (a, b), _ = P.calibration(pred, GAMES, int(s))
        else:
            tr = d[(d.season < s) & (d.season >= cal_from)]
            if len(tr) < 200:
                a, b = 0.0, 0.0
            else:
                m = LogisticRegression(C=10.0).fit(tr[["x"]].values, tr.y.values); a, b = float(m.intercept_[0]), float(m.coef_[0][0])
        cal.append(pd.Series(_lg(a + b * d.x[d.season == s].values), index=d.index[d.season == s]))
    d["cal"] = pd.concat(cal)
    return d[["season", "x", "raw", "cal", "y"]]


def logit_rows(rows: pd.DataFrame, y: str, cals: dict, kind: str | None = None) -> pd.DataFrame:
    """rows (picks._over_rows / _home_rows / _tease_rows): raw = logistic(lg), cal = the fit in force for the season."""
    d = rows if kind is None else rows[rows.kind == kind]
    d = d.copy(); d["raw"] = _lg(d.lg); d["y"] = d[y].astype(int)
    d["cal"] = [_lg((c := cals[int(s)] if kind is None else cals[int(s)][kind])[0] + c[1] * l) for s, l in zip(d.season, d.lg)]
    return d[["season", "raw", "cal", "y"]]


def tease_cals(pred: pd.DataFrame, slope: dict) -> dict:
    """season -> {kind: (a, b, n)} as picks.tease_calibration, with each kind's form (slope or shift) given: the fix candidates."""
    d = P._tease_rows(pred, GAMES)
    return {int(s): {k: P._fit_logit(d[(d.season < s) & (d.kind == k)], "hit", slope[k], P.TEASE_MIN_N) for k in ("spread", "total")}
            for s in sorted(pred.season.unique())}


def scores(p, y):
    p = np.clip(np.asarray(p, float), 1e-6, 1 - 1e-6); y = np.asarray(y, float)
    return float(-(y * np.log(p) + (1 - y) * np.log(1 - p)).mean()), float(((p - y) ** 2).mean())


def bands(d: pd.DataFrame, col: str, edges) -> list[dict]:
    out = []
    b = pd.cut(d[col], edges, right=False)
    for k, x in d.groupby(b, observed=True):
        n = len(x); said = float(x[col].mean()); hap = float(x.y.mean()); se = float(np.sqrt((x[col] * (1 - x[col])).sum())) / n
        out.append({"band": f"[{k.left:g}, {k.right:g})", "n": n, "said": round(said, 4), "happened": round(hap, 4), "z": round((hap - said) / se, 2) if se > 0 else np.nan})
    return out


def main():
    pred = rerun()
    print(f"rerun table: {len(pred)} games, seasons {pred.season.min()}-{pred.season.max()}", flush=True)
    sets = {"C1 cover": cover_rows(pred),
            "C1 cover (fit from 2015, record only)": cover_rows(pred, 2015),
            "C2 over": logit_rows(P._over_rows(pred, GAMES), "over", P.over_calibrations(pred, GAMES)),
            "C3 home win": logit_rows(P._home_rows(pred, GAMES), "hw", P.home_calibrations(pred, GAMES)),
            "C4s teaser spread leg": logit_rows(P._tease_rows(pred, GAMES), "hit", P.tease_calibrations(pred, GAMES), "spread"),
            "C4t teaser total leg": logit_rows(P._tease_rows(pred, GAMES), "hit", P.tease_calibrations(pred, GAMES), "total")}
    alt = tease_cals(pred, {"spread": not P.TEASE_SLOPE["spread"], "total": not P.TEASE_SLOPE["total"]})   # the other form in the code family
    form = lambda b: "intercept and slope" if b else "shift"
    sets[f"C4s fix candidate: {form(not P.TEASE_SLOPE['spread'])}"] = logit_rows(P._tease_rows(pred, GAMES), "hit", alt, "spread")
    sets[f"C4t fix candidate: {form(not P.TEASE_SLOPE['total'])}"] = logit_rows(P._tease_rows(pred, GAMES), "hit", alt, "total")
    rows, summ, gates = [], [], {}
    for name, d in sets.items():
        ll, br = {}, {}
        for w, (lo, hi) in WIN.items():
            x = d[d.season.between(lo, hi)]
            if name.startswith("C3"):
                x = x[x.season >= 2017] if w == "2016-18" else x   # the identity under 500 games: 2016 raw = cal
            lr, brr = scores(x.raw, x.y); lc, brc = scores(x.cal, x.y)
            ll[GATE_KEY[w]] = (lr, lc); br[GATE_KEY[w]] = (brr, brc)
            seasons = f"{int(x.season.min())}-{int(x.season.max())}"
            summ.append({"calibration": name, "window": w, "seasons": seasons, "n": len(x), "raw_logloss": round(lr, 5), "cal_logloss": round(lc, 5),
                         "raw_brier": round(brr, 5), "cal_brier": round(brc, 5), "cal_better_both": bool(lc < lr and brc < brr),
                         "said_raw": round(float(x.raw.mean()), 4), "said_cal": round(float(x.cal.mean()), 4), "happened": round(float(x.y.mean()), 4)})
            if name.startswith("C1"):
                for v in ("raw", "cal"):   # by |edge|, the cover calibration's own input
                    xx = x.assign(p=x[v])
                    for e0, g in xx.groupby(pd.cut(xx.x, [0, 1, 2, 3, 4, 5, 6, 7.01], right=False), observed=True):
                        n = len(g); said = float(g.p.mean()); hap = float(g.y.mean()); se = float(np.sqrt((g.p * (1 - g.p)).sum())) / n
                        rows.append({"section": "reliability", "calibration": name, "window": w, "chance": v, "band": f"|edge| [{e0.left:g}, {min(e0.right, 7):g}{']' if e0.right > 7 else ')'}",
                                     "n": n, "said": round(said, 4), "happened": round(hap, 4), "z": round((hap - said) / se, 2) if se > 0 else np.nan})
            else:
                for v in ("raw", "cal"):
                    for r in bands(x, v, np.round(np.arange(0, 1.01, 0.1), 1)):
                        rows.append({"section": "reliability", "calibration": name, "window": w, "chance": v, **r})
        if "record only" not in name:
            gates[name] = G.gate(miss=ll, calibration=br)
    # the spread flag's record at each cut, weeks 1-17, closing line (report only: SPREAD_EDGE is not changed)
    d = B.join(pred, GAMES); d = d[d.game_type == "REG"]
    cut = []
    for c in CUTS:
        for w, (lo, hi) in {"2015-18": (2015, 2018), "2019-22": (2019, 2022), "2023-25": (2023, 2025)}.items():
            x = d[d.season.between(lo, hi)]; wn, ln = P.record(x, P.rule_mask(x, c))
            cut.append({"cut": c, "window": w, "wins": wn, "losses": ln, "win_pct": round(wn / max(1, wn + ln), 4), "units": round(wn - 1.1 * ln, 1)})
    out = pd.concat([pd.DataFrame(summ).assign(section="score"), pd.DataFrame(rows), pd.DataFrame(cut).assign(section="spread cut")], ignore_index=True)
    first = ["section", "calibration", "window"]
    out[first + [c for c in out.columns if c not in first]].to_csv(REP / "calibration_recheck.csv", index=False)
    S = pd.DataFrame(summ); C = pd.DataFrame(cut)
    L = ["# Calibration recheck: results (written by experiments/calibration_recheck.py)", "",
         f"Rerun table: {len(pred)} games 2015-2025, regular season scored. Log loss and Brier, lower is better.", "",
         "| Calibration | Window | Seasons | Games | Log loss raw | Log loss cal | Brier raw | Brier cal | Said raw | Said cal | Happened | Cal better on both |", "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    L += [f"| {r.calibration} | {r.window} | {r.seasons} | {r.n} | {r.raw_logloss:.4f} | {r.cal_logloss:.4f} | {r.raw_brier:.4f} | {r.cal_brier:.4f} | {r.said_raw:.3f} | {r.said_cal:.3f} | {r.happened:.3f} | {'yes' if r.cal_better_both else 'NO'} |" for r in S.itertuples()]
    for name, g in gates.items():
        L += ["", f"## Gate: {name} (better = log loss; calibration = Brier; window 2015-18 is 2016-18 here)", "", G.markdown(g)]
    L += ["", "## Spread flag by cut (weeks 1-17, closing line, -110; report only)", "", "| Cut | 2015-18 | 2019-22 | 2023-25 |", "|---|---|---|---|"]
    for c in CUTS:
        x = C[C.cut == c].set_index("window")
        L.append(f"| {c:g} | " + " | ".join(f"{int(x.loc[w, 'wins'])}-{int(x.loc[w, 'losses'])} ({100 * x.loc[w, 'win_pct']:.1f}%, {x.loc[w, 'units']:+.1f}u)" for w in ("2015-18", "2019-22", "2023-25")) + " |")
    head = len(L)
    R = pd.DataFrame(rows)
    L += ["", "## Reliability by band (z = happened minus said in binomial standard errors)", ""]
    for name in sets:
        L += [f"**{name}**", "", "| Window | Chance | Band | Games | Said | Happened | z |", "|---|---|---|---|---|---|---|"]
        L += [f"| {r.window} | {r.chance} | {r.band} | {r.n} | {r.said:.3f} | {r.happened:.3f} | {r.z:+.1f} |" for r in R[R.calibration == name].itertuples()]
        L.append("")
    (REP / "calibration_recheck_results.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L[:60 + 4 * len(gates) * 10]))


if __name__ == "__main__":
    main()
