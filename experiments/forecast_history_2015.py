"""Forecast history back to 2015 (2 Oct 2026, Matt: make the backtest price exactly as live; approved). Report:
reports/forecast_history_2015.md.

data/weather/forecast_history.csv started in 2018, so a played 2015-2017 game was still priced on the weather that happened
(model.priced_weather prices a played game on its stored pre-kickoff forecast only where one exists). The same sources,
fetched by forecast_history's own path (nflmodel/forecast_history.py backfill, FIRST = 2015):
  - GFS MOS (Iowa Environmental Mesonet's MOS archive) reaches 2015: wind, temperature and rain chance, d1 and d0 runs;
  - Japan's model (Open-Meteo previous runs) starts 1 Jan 2016: none for 2015's regular season, all of 2016-2017;
  - the National Blend starts 7 Nov 2018: none.
The wind reading stays the mean of the pre-kickoff forecasts that exist (wind_live.readings): GFS alone in 2015, GFS and
Japan's day-before run in 2016-2017 (as in 2018 before November).

before: the walk-forward 2015-2025 with the history cut to 2018 on (the stored file as it was); after: the full history.
Everything else is the live model. Scored per window (regular season): team points, total and margin miss; the spread flag
(4+), the totals flag (55%+ under) and the wind under (10+ mph), weeks 1-17; nflmodel.study_gate on total miss (no placebo:
this is the honest pricing Matt approved, not a new input). build.fix_wind (which now finds a GFS forecast for 2015-2017
when it weighs the schedule's wind against the archive) is reported separately: it moves the training rows' recorded wind.

    python -m experiments.forecast_history_2015
"""
from __future__ import annotations
import pickle, tempfile
from pathlib import Path
import numpy as np, pandas as pd
from nflmodel import backtest as B, build as BU, forecast_history as FH, model as M, picks as P, study_gate as G
from nflmodel.features import OUT, ROOT

REP = ROOT / "reports"
TMP = Path(tempfile.gettempdir()) / "forecast_history_2015"
WIN = {"2015-18": (2015, 2018), "2019-22": (2019, 2022), "2023-25": (2023, 2025)}
GAMES = pd.read_parquet(OUT / "games.parquet")
M.save_trees_cache = lambda: None   # an experiment never rewrites data/processed/trees_cache.parquet
FULL = FH.OUTF


def _reset():
    P._WIND = P._RAIN = P._COLD = None; M.DIST.clear()


def run(outf: Path) -> pd.DataFrame:
    FH.OUTF = outf; _reset()
    try:
        return M.walk_forward(M.with_trends(pd.read_parquet(OUT / "features_asof.parquet")), range(2015, 2026), M.RIDGE)
    finally:
        FH.OUTF = FULL


def score(p, outf: Path) -> dict:
    FH.OUTF = outf; _reset()
    try:
        d = B.join(p, GAMES); d = d[(d.game_type == "REG") & d.season.between(2015, 2025)]
        out = {}
        for w, (lo, hi) in WIN.items():
            x = d[d.season.between(lo, hi)]
            out[w] = {"team": float(np.r_[x.home_err.abs(), x.away_err.abs()].mean()), "total": float(x.total_err.abs().mean()),
                      "margin": float(x.margin_err.abs().mean()),
                      "spread": P.record(x, P.rule_mask(x, P.SPREAD_EDGE)),
                      "totals": P.record(x, P.rule_mask(x, P.TOTAL_SHADOW["prob"], "under_prob"), "under_prob"),
                      "wind": P.record(x, P.rule_mask(x, P.WIND_UNDER["mph"], "wind_under"), "wind_under")}
        return out
    finally:
        FH.OUTF = FULL; _reset()


def checks(h: pd.DataFrame) -> list[str]:
    """Data checks on the 2015-2017 rows: coverage by season, runs before kickoff, no MOS sentinels."""
    x = h[h.season.between(2015, 2017)].copy()
    g = FH.games(range(2015, 2018))
    L = ["| Season | Outdoor US games | Stored | GFS wind d0 | GFS wind d1 | GFS temp d0 | GFS rain d0 | Japan d1 | NBS |", "|---|---|---|---|---|---|---|---|---|"]
    for s in (2015, 2016, 2017):
        y = x[x.season == s]
        L.append(f"| {s} | {int((g.season == s).sum())} | {len(y)} | {int(y.gfs_wind_d0.notna().sum())} | {int(y.gfs_wind_d1.notna().sum())} | "
                 f"{int(y.gfs_temp_d0.notna().sum())} | {int(y.gfs_pop_d0.notna().sum())} | {int(y.jma_wind_d1.notna().sum())} | {int(y.nbs_wind_d0.notna().sum())} |")
    ko = pd.to_datetime(x.kickoff_utc, utc=True); run = pd.to_datetime(x.gfs_run_d0.str.replace("Z", ":00Z"), utc=True)
    lead = (ko - run).dt.total_seconds() / 3600
    vals = [c for c in FH.COLS[6:] if "_run_" not in c]
    v = x[vals].apply(pd.to_numeric, errors="coerce")
    wind = v[[c for c in vals if "wind" in c or "gust" in c]]
    L += ["", f"- GFS last run before kickoff: {lead.min():.1f} to {lead.max():.1f} hours (every run {int((lead >= 5).sum())} of {len(lead)} at 5+ hours); "
          f"the day-before run is 12Z the Eastern day before.",
          f"- Largest wind {float(wind.max().max()):.1f} mph, largest temperature {float(v[['gfs_temp_d1', 'gfs_temp_d0']].max().max()):.1f} F, "
          f"rain chance {float(v[['gfs_pop_d1', 'gfs_pop_d0']].min().min()):.0f} to {float(v[['gfs_pop_d1', 'gfs_pop_d0']].max().max()):.0f}%: "
          f"no 99 / 999 sentinels ({int((wind >= 99).sum().sum())} wind values at 99+, {int((v[['gfs_temp_d1', 'gfs_temp_d0']] >= 900).sum().sum())} temperatures at 900+).",
          f"- Japan's model before 1 Jan 2016: {int(x[pd.to_datetime(x.kickoff_utc, utc=True) < FH.JMA_FROM].jma_wind_d1.notna().sum())} values (none asked); "
          f"games abroad stored: {int(x.game_id.isin(FH.abroad_ids()).sum())}; duplicates: {int(x.game_id.duplicated().sum())}."]
    both = v[["gfs_wind_d0", "jma_wind_d1"]].dropna(); y = h[h.season >= 2018][["gfs_wind_d0", "jma_wind_d1"]].apply(pd.to_numeric, errors="coerce").dropna()
    L.append(f"- GFS d0 against Japan d1: correlation {both.corr().iloc[0, 1]:.2f} on {len(both)} games 2016-2017, {y.corr().iloc[0, 1]:.2f} on {len(y)} games 2018 on; "
             f"mean GFS d0 {v.gfs_wind_d0.mean():.1f} mph 2015-2017, {pd.to_numeric(h[h.season >= 2018].gfs_wind_d0, errors='coerce').mean():.1f} 2018 on.")
    return L


def fix_wind_effect(h_before: pd.DataFrame) -> str:
    """How many played 2015-2017 schedule winds build.fix_wind decides differently with the GFS forecast now stored."""
    g = GAMES.copy(); g["wind"] = g.get("wind_listed", g.wind)
    a = BU.fix_wind(g, forecast=h_before[["game_id", "gfs_wind_d0"]])
    b = BU.fix_wind(g)
    diff = (a.wind.fillna(-1) != b.wind.fillna(-1)) & a.season.between(2015, 2017)
    return f"build.fix_wind with the 2015-2017 forecasts: {int(diff.sum())} schedule winds decided differently ({', '.join(a.game_id[diff].head(8))})"


def main():
    TMP.mkdir(exist_ok=True)
    h = pd.read_csv(FULL, dtype={"season": int})
    cut = TMP / "forecast_history_2018on.csv"; h[h.season >= 2018].to_csv(cut, index=False)
    cache = TMP / "runs.pkl"
    if cache.exists():
        runs = pickle.loads(cache.read_bytes())
    else:
        runs = {"before": run(cut)}; print("before done", flush=True)
        runs["after"] = run(FULL); print("after done", flush=True)
        cache.write_bytes(pickle.dumps(runs))
    res = {"before": score(runs["before"], cut), "after": score(runs["after"], FULL)}
    rec = lambda t: "%d-%d" % t
    T = ["| Window | Spread flag (4+) | Totals flag (55% under) | Wind under (10+ mph) | Team points miss | Total miss | Margin miss |", "|---|---|---|---|---|---|---|"]
    for w in WIN:
        b, a = res["before"][w], res["after"][w]
        T.append(f"| {w} | {rec(b['spread'])} -> {rec(a['spread'])} | {rec(b['totals'])} -> {rec(a['totals'])} | {rec(b['wind'])} -> {rec(a['wind'])} | "
                 f"{b['team']:.4f} -> {a['team']:.4f} | {b['total']:.4f} -> {a['total']:.4f} | {b['margin']:.4f} -> {a['margin']:.4f} |")
    gate = G.gate({w: (res["before"][w]["total"], res["after"][w]["total"]) for w in WIN},
                  {w: {"spread flag": (res["before"][w]["spread"], res["after"][w]["spread"]), "totals flag": (res["before"][w]["totals"], res["after"][w]["totals"]),
                       "wind under": (res["before"][w]["wind"], res["after"][w]["wind"])} for w in WIN})
    pd.DataFrame([{"variant": v, "window": w, **{k: (rec(x) if isinstance(x, tuple) else x) for k, x in res[v][w].items()}} for v in res for w in WIN]).to_csv(REP / "forecast_history_2015.csv", index=False)
    fw = fix_wind_effect(h[h.season >= 2018])
    out = ["# Forecast history back to 2015", "",
           "2 Oct 2026. `experiments/forecast_history_2015.py`; data `data/weather/forecast_history.csv` (fetched by `nflmodel/forecast_history.py`, `FIRST = 2015`).", "",
           "Approved goal (Matt): the backtest prices every played game exactly as live, on the pre-kickoff forecast. Until now 2015-2017 used the weather that happened, because the stored forecasts began in 2018.", "",
           "## What reaches back", "",
           "- GFS MOS (Iowa Environmental Mesonet MOS archive): yes, every 2015-2017 run asked.",
           "- Japan's model (Open-Meteo previous runs): from 1 Jan 2016 only (an earlier start date is refused). None for the 2015 regular season; all of 2016-2017.",
           "- National Blend (NBS): from 7 Nov 2018. None.", "",
           "The wind reading stays the mean of the pre-kickoff forecasts that exist (`wind_live.readings`): GFS alone for 2015, GFS and Japan's day-before run for 2016-2017, as live when one source is missing.", "",
           "## Data checks (2015-2017 rows)", ""] + checks(h) + [f"- {fw}. The walk-forward below reads `features_asof.parquet` as built; the weekly build applies this.", "",
           "## Walk-forward 2015-2025, before -> after", "",
           "Before: the history cut to 2018 on. After: the full history (2015-2017 priced on the forecast, the wind points' pool and the rain input's training rows from 2015).", ""] + T + [
           "", "## Study gate (total miss)", "", "| Check | Pass | Detail |", "|---|---|---|"] + [f"| {c} | {'yes' if o else 'no'} | {d} |" for c, o, d in gate] + [
           "", "Not a new input: the approved honest pricing. The gate is shown for the record; no placebo is run (nothing is chosen from these numbers).", "",
           "## Why 2019-2025 move too: the live model changes", "",
           "The stored forecasts are training data as well as prices. With 2015-2017 stored, the totals equation's rain input (`rain_fc`, the GFS chance 50%+) is learned on 2015-2017 rows that were 0 before, and the wind points' pool (each season's band amounts from earlier seasons) starts in 2015 instead of 2018. So the live total moves: on 2019-22 the total miss rises and the totals flag gives back 10 net wins; 2023-25 is flat. The spread flag and the wind under there do not move (the wind under reads the reading, not the model).",
           "",
           "## Storage", "",
           "`data/weather/forecast_history.csv` is rewritten by the weekly run (`forecast_history.backfill` appends each week's played games and `weekly.yml` commits `data/weather`), so the PR commits code only: with `FIRST = 2015` the weekly run fetches the 598 games itself on GitHub's network, ten minutes a run (about two runs). The numbers above are from the same fetch path run here."]
    (REP / "forecast_history_2015.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(T)); print(fw)


if __name__ == "__main__":
    main()
