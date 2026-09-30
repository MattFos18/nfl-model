"""The drift monitor (30 Sep 2026, Matt: "catch these changes before Vegas does, automatically"). Every weekly run it
measures the few numbers that move the edge, on regular-season games with a line, and asks whether the recent stretch
(last season and this season so far) has left its long-run level (2015 to two seasons ago) by more than noise:

- home field: the home side's margin (neutral sites out) and its cover margin against the line
- favorites and underdogs: the cover margin of home favorites and road favorites, blind (each underdog is its mirror)
- totals: the final total against the closing total, and the over rate
- key numbers: how often the final margin lands on exactly 3 or 7
- the model: its miss of the final margin against the closing line's, its home lean (model margin minus the real one)
  and the 4+ flag's win rate

Each number gets a z-score (the recent mean against the long-run mean, in standard errors of both) and a one-sided
CUSUM over the recent weeks (each week's mean against the long-run mean in its own standard errors, k 0.5, h 5): a slow drift one way trips the
CUSUM before the z-score. ALERT at |z| >= 2.5 or a CUSUM trip, WATCH at |z| >= 2. Each alert names the re-test to run.
Writes reports/drift.csv and reports/drift.md. Usage: python -m nflmodel.drift"""
from __future__ import annotations
import numpy as np
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT, REP = ROOT / "data" / "processed", ROOT / "reports"
Z_ALERT, Z_WATCH, CUSUM_K, CUSUM_H = 2.5, 2.0, 0.5, 5.0
RETEST = {
    "home": "home field fit on recent seasons (the 27 Sep test, reports/home_field_recency.md) and reports/home_field.md, under reports/round3_rule.md",
    "side": "the favorite / underdog rules in experiments/bet_rules_sweep.py and experiments/spread_research.py",
    "total": "the league scoring-environment input and the totals rules (experiments/totals_fix.py, the unders flag cut)",
    "key": "the hook test in experiments/spread_research.py (buying on or off 3 and 7)",
    "model": "the full backtest: threshold sweep (experiments/threshold.py) and the model's miss by window",
}


def games_table() -> pd.DataFrame:
    from . import backtest as B
    g = pd.read_parquet(OUT / "games.parquet"); p = pd.read_parquet(OUT / "pred_v3.parquet")
    d = B.join(p, g)
    d = d[(d.game_type == "REG") & d.home_score.notna() & d.spread_line.notna()].copy()
    loc = g.set_index("game_id").location if "location" in g.columns else pd.Series(dtype=str)
    d["neutral_site"] = d.game_id.map(loc).eq("Neutral")
    d = d.sort_values([c for c in ("season", "week", "gameday", "game_id") if c in d.columns])
    m = d.home_score - d.away_score; ats = m - d.spread_line; e = d.model_spread - d.spread_line
    hf, rf = d.spread_line > 0, d.spread_line < 0   # nflverse sign: positive = home favoured
    cols = {
        ("home", "Home margin (points)"): m.where(~d.neutral_site),
        ("home", "Home cover margin vs the line"): ats.where(~d.neutral_site),
        ("side", "Home favorite cover margin (road dog: the same, reversed)"): ats.where(hf),
        ("side", "Road favorite cover margin (home dog: the same, reversed)"): (-ats).where(rf),
        ("total", "Final total minus the closing total"): (d.home_score + d.away_score - d.total_line).where(d.total_line.notna()),
        ("total", "Over rate"): ((d.home_score + d.away_score) > d.total_line).astype(float).where(d.total_line.notna() & ((d.home_score + d.away_score) != d.total_line)),
        ("key", "Margin exactly 3"): (m.abs() == 3).astype(float),
        ("key", "Margin exactly 7"): (m.abs() == 7).astype(float),
        ("model", "Model miss minus the line's miss"): (d.model_spread - m).abs() - (d.spread_line - m).abs(),
        ("model", "Model home lean (model margin minus real)"): (d.model_spread - m).where(~d.neutral_site),
        ("model", "4+ flag win rate"): pd.Series(np.where(((e > 0) & (ats > 0)) | ((e < 0) & (ats < 0)), 1.0, 0.0), index=d.index).where((e.abs() >= 4) & (d.week <= 17) & (ats != 0)),
    }
    out = d[["season", "week", "game_id"]].copy()
    for (grp, lab), s in cols.items():
        out[f"{grp}|{lab}"] = s
    return out


def cusum(r: pd.DataFrame, c: str, mu: float, sd: float) -> float:
    """The larger of the one-sided CUSUMs (up and down) at their peak, run on each week's mean standardized by its own
    standard error (a week's mean is close to normal where a single game's 0/1 is not, so the false-alarm rate holds)."""
    wk = r.groupby(["season", "week"])[c].agg(["mean", "count"]).dropna()
    wk = wk[wk["count"] > 0]
    if not len(wk) or not sd:
        return 0.0
    z = ((wk["mean"] - mu) / (sd / np.sqrt(wk["count"]))).values; hi = lo = best = 0.0
    for v in z:
        hi = max(0.0, hi + v - CUSUM_K); lo = max(0.0, lo - v - CUSUM_K); best = max(best, hi, lo)
    return best


def run(season_now: int | None = None) -> pd.DataFrame:
    t = games_table(); season_now = int(t.season.max()) if season_now is None else season_now
    base = t[(t.season >= 2015) & (t.season <= season_now - 2)]; rec = t[t.season >= season_now - 1]
    rows = []
    for c in [c for c in t.columns if "|" in c]:
        grp, lab = c.split("|", 1)
        b, r = base[c].dropna().values, rec[c].dropna().values
        if len(b) < 50 or len(r) < 20:
            continue
        mb, sb, mr = float(b.mean()), float(b.std(ddof=1)), float(r.mean())
        se = sb * np.sqrt(1 / len(r) + 1 / len(b)); z = (mr - mb) / se if se else 0.0
        cs = cusum(rec[["season", "week", c]], c, mb, sb)
        cur = t[t.season == season_now][c].dropna()
        level = "ALERT" if abs(z) >= Z_ALERT or cs >= CUSUM_H else "WATCH" if abs(z) >= Z_WATCH else "ok"
        rows.append({"group": grp, "measure": lab, "long_run": round(mb, 4), "long_run_n": len(b), "recent": round(mr, 4), "recent_n": len(r),
                     "this_season": round(float(cur.mean()), 4) if len(cur) else None, "this_season_n": int(len(cur)),
                     "z": round(z, 2), "cusum": round(cs, 2), "level": level, "retest": RETEST[grp] if level == "ALERT" else ""})
    df = pd.DataFrame(rows)
    REP.mkdir(exist_ok=True); df.to_csv(REP / "drift.csv", index=False)
    al = df[df.level == "ALERT"]; wa = df[df.level == "WATCH"]
    L = [f"# Drift monitor, {season_now}", "",
         f"**{len(al)} alert{'s' if len(al) != 1 else ''}, {len(wa)} to watch.** Long run = {int(base.season.min())} to {season_now - 2}; recent = {season_now - 1} and {season_now} so far. "
         f"ALERT at |z| >= {Z_ALERT} or a CUSUM trip (h {CUSUM_H:g}); WATCH at |z| >= {Z_WATCH}.", ""]
    for r in al.itertuples():
        L.append(f"- **ALERT, {r.measure}:** long run {r.long_run:+.3f}, recent {r.recent:+.3f} (z {r.z:+.2f}, CUSUM {r.cusum:.1f}). Re-test: {r.retest}.")
    for r in wa.itertuples():
        L.append(f"- Watch, {r.measure}: long run {r.long_run:+.3f}, recent {r.recent:+.3f} (z {r.z:+.2f}).")
    L += ["", df.drop(columns=["retest"]).to_markdown(index=False), ""]
    (REP / "drift.md").write_text("\n".join(L))
    print("\n".join(L[:3 + len(al) + len(wa)]))
    return df


if __name__ == "__main__":
    run()
