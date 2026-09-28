"""The opener study (28 Sep 2026, Matt: "is the model better against the opener or the close, and is the difference only the
injury report and the weather?"): the full model and a Tuesday model, graded at the closing line and at the opening line.

The Tuesday model is the same fits, walk-forward, with the inputs a Tuesday does not have at their typical values: the injury
report (skill_out_value, opp_skill_out_value, off_snap_out, opp_def_snap_out, qb_out) and the kickoff weather (wind_out, cold,
rain, warm_in_cold) all zero. It keeps its own trees cache (trees_cache_tuesday.parquet) so the live model's is untouched.

Opening lines are the archive at data/archive/openers_2015_2021.csv (sportsbookreviewsonline's season pages, 2015 to
2021, 1,786 of 1,808 regular-season games matched; its close is within a point of nflverse's on 96% of them). Closing lines
are nflverse's (games.parquet), the ones the backtest grades. Runs in the weekly run after the model; writes
data/processed/pred_tuesday.parquet, reports/opener_study.md and web/data/opener_study.js (the Backtest tab's Opener study).
"""
from __future__ import annotations
import json, sys, time
import numpy as np, pandas as pd
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "processed"
WEB_DATA = ROOT / "web" / "data"

RAW_OPENERS = ROOT / "data" / "archive" / "openers_2015_2021.csv"
PRED_TUE = OUT / "pred_tuesday.parquet"
TUESDAY_ZERO = ["skill_out_value", "opp_skill_out_value", "off_snap_out", "opp_def_snap_out", "qb_out", "wind_out", "cold", "rain", "warm_in_cold"]
from .picks import SPREAD_EDGE
CUTS = [3.0, float(SPREAD_EDGE)]   # the study's flags: the model's side this many points or more from the line, spreads and totals alike; the second is the site's own spread flag
PRICE = -110.0
WINDOWS_OPEN = {"2015-18": (2015, 2018), "2019-21": (2019, 2021)}   # the archive's reach
WINDOWS_CLOSE = {"2015-18": (2015, 2018), "2019-22": (2019, 2022), "2023-25": (2023, 2025)}
CASES = [("full", "close"), ("tuesday", "close"), ("tuesday", "open"), ("full", "open")]
LABEL = {"full": "Full model (Sunday: injuries and weather in)", "tuesday": "Tuesday model (no injury report, no weather)"}


def tuesday_predictions(seasons=None, verbose=False) -> pd.DataFrame:
    """Walk-forward predictions of the Tuesday model, with its own trees cache; written to pred_tuesday.parquet."""
    from . import model as M
    f = M.with_trends(pd.read_parquet(OUT / "features_asof.parquet"))
    for c in TUESDAY_ZERO:
        if c in f.columns:
            f[c] = 0.0
    seasons = seasons or sorted(int(s) for s in pd.read_parquet(OUT / "pred_v3.parquet").season.unique())
    saved = (M.TREES_CACHE, M._TC)
    M.TREES_CACHE = OUT / "trees_cache_tuesday.parquet"; M._TC = {"df": None, "used": set(), "new": []}
    try:
        p = M.walk_forward(f, seasons, verbose=verbose)
    finally:
        M.TREES_CACHE, M._TC = saved
    keep = ["game_id", "season", "week", "game_type", "home_team", "away_team", "model_spread", "model_total", "home_exp", "away_exp", "sigma_margin", "sigma_total"]
    p = p[[c for c in keep if c in p.columns]].reset_index(drop=True)
    p.to_parquet(PRED_TUE, index=False)
    return p


def openers() -> pd.DataFrame:
    return pd.read_csv(RAW_OPENERS).set_index("game_id")


def _rec(s) -> str:
    return f"{int((s > 0).sum())}-{int((s < 0).sum())}-{int((s == 0).sum())}"


def _pct(s) -> float | None:
    n = int((s != 0).sum()); return round(100 * float((s > 0).sum()) / n, 1) if n else None


def _units(s) -> float:
    return round(float((s > 0).sum()) * 100 / abs(PRICE) - float((s < 0).sum()), 1)


def grade(pred: pd.DataFrame, games: pd.DataFrame, line: str, windows: dict, opn: pd.DataFrame | None = None, label: str = "", cut: float = 3.0) -> list[dict]:
    """One row per window: every-game ATS and the 3+ flags (record, pct, units at -110), and the same for totals, with the
    model's side against `line` ("close" = nflverse, "open" = the archive; the archive's games only, either way, so the
    two lines are graded on the same games)."""
    g = games.set_index("game_id")
    d = pred[pred.game_type == "REG"].copy()
    if opn is not None:
        d = d[d.game_id.isin(opn.index)]
    d["hs"] = d.game_id.map(g.home_score); d["as_"] = d.game_id.map(g.away_score)
    if line == "open":
        d["sl"] = d.game_id.map(opn.open_spread); d["tl"] = d.game_id.map(opn.open_total)
    else:
        d["sl"] = d.game_id.map(g.spread_line); d["tl"] = d.game_id.map(g.total_line)
    d = d[d.hs.notna() & d.sl.notna() & d.tl.notna()]
    m = d.hs - d.as_; t = d.hs + d.as_; se = d.model_spread - d.sl; te = d.model_total - d.tl
    d["cov"] = np.sign(np.where(se > 0, m - d.sl, d.sl - m)); d["ov"] = np.sign(np.where(te > 0, t - d.tl, d.tl - t))
    d["sflag"] = se.abs() >= cut; d["tflag"] = te.abs() >= cut
    rows = []
    for w, (a, b) in windows.items():
        x = d[d.season.between(a, b)]; fs = x[x.sflag]; ft = x[x.tflag]
        rows.append({"model": label, "line": line, "cut": cut, "window": w, "n": int(len(x)),
                     "ats": _rec(x["cov"]), "ats_pct": _pct(x["cov"]), "flags": _rec(fs["cov"]), "flags_pct": _pct(fs["cov"]), "flags_units": _units(fs["cov"]),
                     "totals": _rec(x["ov"]), "totals_pct": _pct(x["ov"]), "tflags": _rec(ft["ov"]), "tflags_pct": _pct(ft["ov"]), "tflags_units": _units(ft["ov"])})
    return rows


def study(pred_full: pd.DataFrame | None = None, pred_tue: pd.DataFrame | None = None) -> dict:
    """Every row the report and the page show: the four cases on the archive's games (2015-18, 2019-21) and the two models
    at the close on the backtest's three windows."""
    games = pd.read_parquet(OUT / "games.parquet")
    pred_full = pd.read_parquet(OUT / "pred_v3.parquet") if pred_full is None else pred_full
    pred_tue = pd.read_parquet(PRED_TUE) if pred_tue is None else pred_tue
    opn = openers()
    preds = {"full": pred_full, "tuesday": pred_tue}
    open_rows, close_rows = [], []
    for cut in CUTS:
        for mk, ln in CASES:
            open_rows += grade(preds[mk], games, ln, WINDOWS_OPEN, opn, mk, cut)
        close_rows += grade(pred_full, games, "close", WINDOWS_CLOSE, None, "full", cut) + grade(pred_tue, games, "close", WINDOWS_CLOSE, None, "tuesday", cut)
    return {"cuts": CUTS, "site_flag": float(SPREAD_EDGE), "price": PRICE, "archive": {"file": str(RAW_OPENERS.relative_to(ROOT)), "games": int(len(opn)), "seasons": f"{int(opn.season.min())}-{int(opn.season.max())}"},
            "zeroed": TUESDAY_ZERO, "labels": LABEL, "open": open_rows, "close": close_rows}


def write(res: dict) -> None:
    (WEB_DATA / "opener_study.js").write_text("window.OPENER=" + json.dumps(res, separators=(",", ":")) + ";")
    L = ["# The opener study", "",
         f"The full model (the one that prices the week, injuries and weather in) and a Tuesday model (the same fits with {', '.join(TUESDAY_ZERO)} at zero: what a Tuesday does not know), "
         f"each graded on the model's side against the closing line (nflverse) and against the opening line ({res['archive']['file']}, {res['archive']['games']} regular-season games, {res['archive']['seasons']}). "
         f"Flags: the model's side the cut or more points from the line, at {' and '.join(f'{c:g}' for c in CUTS)} points (the second is the site's spread flag); units at {PRICE:g}. Every game ATS counts every game with a line. Rebuilt every weekly run (nflmodel/opener_study.py).", "",
         "## Against the opener and the close, the archive's games", "",
         "| Cut | Model | Line | Window | Games | ATS every game | % | Flags | % | Units | Totals every game | % | Totals flagged | % | Units |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in res["open"]:
        L.append(f"| {r['cut']:g}+ | {LABEL[r['model']]} | {r['line']} | {r['window']} | {r['n']} | {r['ats']} | {r['ats_pct']} | {r['flags']} | {r['flags_pct']} | {r['flags_units']} | {r['totals']} | {r['totals_pct']} | {r['tflags']} | {r['tflags_pct']} | {r['tflags_units']} |")
    L += ["", "## At the close, the backtest's windows", "", "| Cut | Model | Window | Games | ATS every game | % | Flags | % | Units | Totals every game | % | Totals flagged | % | Units |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in res["close"]:
        L.append(f"| {r['cut']:g}+ | {LABEL[r['model']]} | {r['window']} | {r['n']} | {r['ats']} | {r['ats_pct']} | {r['flags']} | {r['flags_pct']} | {r['flags_units']} | {r['totals']} | {r['totals_pct']} | {r['tflags']} | {r['tflags_pct']} | {r['tflags_units']} |")
    (ROOT / "reports" / "opener_study.md").write_text("\n".join(L) + "\n")


def main() -> None:
    t0 = time.time()
    if "--grade-only" not in sys.argv:
        tuesday_predictions(verbose="--verbose" in sys.argv)
        print(f"tuesday model priced in {time.time() - t0:.0f} s", flush=True)
    write(study())
    print("opener study written", flush=True)


if __name__ == "__main__":
    main()
