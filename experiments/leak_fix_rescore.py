"""Rescore after the two backtest leak fixes (2 Oct 2026, Matt approved fixing backtest leaks; audit of 2 Oct 2026).

Fix 1, ref_tot (trends._prior_mean): the referee prior counted every earlier row in `order`, which sorts a game's away row
before its home row, so the home row's "previous games" included the away row of the same game, whose value is this
game's own final total; the totals equation reads ref_tot from the home row. Now only games that kicked off strictly
before this one count (same game and same kickoff excluded). ref_over and ref_pen had the same leak (shown, not used).
Fix 2, Japan-model wind (forecast_history.PRE_KICKOFF_WIND, wind_live): the stored jma_wind_d0 is Open-Meteo's newest
run for each hour, issued at or after kickoff. Open-Meteo keeps no single runs of jma_gsm for 2018-2025 (checked 2 Oct
2026), so the 5-hour run the GFS reading uses cannot be refetched; the reading now uses jma_wind_d1 (lead 24-47 hours),
stored and live alike.

Variants, each the live model refit walk-forward 2015-2025 (the trees read from the stored fits, never rewritten):
  before          the stored (leaky) ref_tot and the old wind reading (GFS d0, NBS d0, Japan d0)
  after           ref_tot rebuilt by the fixed trends.trend_table, the wind reading with Japan d1
  after_no_ref    as after, ref_tot dropped from the totals equation (this experiment only; the live model keeps it)
Per window (2015-18 / 2019-22 / 2023-25, regular season): team points, total and margin miss; the spread flag (4+),
the totals flag (55% under) and the wind under (10+ mph), weeks 1-17. ref_tot's adoption after the fix is scored through
nflmodel.study_gate: total miss, after_no_ref -> after, no bet cost on the three records, and 50 within-season shuffles
of the fixed ref_tot (--placebo; about 15 minutes on 6 processes). Writes reports/leak_fix_rescore.{md,csv}.

    python -m experiments.leak_fix_rescore [--placebo]
"""
from __future__ import annotations
import sys
import numpy as np, pandas as pd
from nflmodel import backtest as B, model as M, picks as P, study_gate as G, trends as T, wind_live as WL, forecast_history as FH
from nflmodel.features import OUT, ROOT

REP = ROOT / "reports"
WIN = {"2015-18": (2015, 2018), "2019-22": (2019, 2022), "2023-25": (2023, 2025)}
GAMES = pd.read_parquet(OUT / "games.parquet")
NPLAC, SEED = 50, 7
M.save_trees_cache = lambda: None   # an experiment never rewrites data/processed/trees_cache.parquet
TOTAL_LIVE = list(M.TOTAL_FEATS)


def old_wind() -> dict:
    """The reading before the fix: Japan's d0 (issued at or after kickoff) in the stored mean, the live log on top."""
    out = {}
    h = WL._history()
    m = h[["gfs_wind_d0", "nbs_wind_d0", "jma_wind_d0"]].apply(pd.to_numeric, errors="coerce").mean(axis=1)
    out.update({g: float(v) for g, v in zip(h.game_id, m) if pd.notna(v)})
    if WL.F.exists():
        lv = pd.read_csv(WL.F).sort_values("ts").drop_duplicates("game_id", keep="last")
        out.update({g: float(v) for g, v in zip(lv.game_id, lv.wind_mean) if pd.notna(v)})
    return out


def fixed_ref_tot() -> pd.DataFrame:
    tt = T.trend_table(GAMES, pd.read_parquet(OUT / "team_games.parquet"))
    return tt[["game_id", "team", "ref_tot"]]


def frames():
    f0 = M.with_trends(pd.read_parquet(OUT / "features_asof.parquet"))   # the stored trends_asof: the leaky ref_tot
    rt = fixed_ref_tot()
    f1 = f0.drop(columns="ref_tot").merge(rt, on=["game_id", "team"], how="left"); f1["ref_tot"] = f1.ref_tot.fillna(0.0)
    return f0, f1


def run(f: pd.DataFrame, wind: dict, total_feats=None) -> pd.DataFrame:
    M._wind_readings = lambda: wind
    M.TOTAL_FEATS[:] = total_feats or TOTAL_LIVE
    try:
        return M.walk_forward(f, range(2015, 2026), 10.0)
    finally:
        M.TOTAL_FEATS[:] = TOTAL_LIVE


def score(pred: pd.DataFrame, wind: dict) -> dict:
    P._WIND = wind
    d = B.join(pred, GAMES); d = d[(d.game_type == "REG") & d.season.between(2015, 2025)]
    out = {}
    for w, (lo, hi) in WIN.items():
        x = d[d.season.between(lo, hi)]
        out[w] = {"team": float(np.r_[x.home_err.abs(), x.away_err.abs()].mean()), "total": float(x.total_err.abs().mean()),
                  "margin": float(x.margin_err.abs().mean()),
                  "spread": P.record(x, P.rule_mask(x, P.SPREAD_EDGE)),
                  "totals": P.record(x, P.rule_mask(x, P.TOTAL_SHADOW["prob"], "under_prob"), "under_prob"),
                  "wind": P.record(x, P.rule_mask(x, P.WIND_UNDER["mph"], "wind_under"), "wind_under")}
    return out


def shuffled(f: pd.DataFrame, seed: int) -> pd.DataFrame:
    """The placebo: each game's ref_tot (both rows read the same number after the fix) shuffled among the season's games."""
    rng = np.random.default_rng(seed)
    g = f[f.home == 1][["game_id", "season", "ref_tot"]].drop_duplicates("game_id")
    g["ref_tot"] = G.shuffle_within_season(g.ref_tot.values, g.season.values, rng)
    return f.drop(columns="ref_tot").merge(g[["game_id", "ref_tot"]], on="game_id", how="left").assign(ref_tot=lambda x: x.ref_tot.fillna(0.0))


def _placebo_job(seed):
    _, f1 = frames(); wind = WL.readings()
    return score(run(shuffled(f1, seed), wind), wind)


def gate_rows(base, new, placebo=None):
    return G.gate({w: (base[w]["total"], new[w]["total"]) for w in WIN},
                  {w: {"spread flag": (base[w]["spread"], new[w]["spread"]), "totals flag": (base[w]["totals"], new[w]["totals"]),
                       "wind under": (base[w]["wind"], new[w]["wind"])} for w in WIN}, placebo)


def rec(t):
    return "%d-%d" % t


def main():
    f0, f1 = frames()
    wold, wnew = old_wind(), WL.readings()
    res = {"before": score(run(f0, wold), wold), "after": score(run(f1, wnew), wnew),
           "after_no_ref": score(run(f1, wnew, [c for c in TOTAL_LIVE if c != "ref_tot"]), wnew)}
    placebo = None
    if "--placebo" in sys.argv:
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor(6) as ex:
            draws = list(ex.map(_placebo_job, [SEED * 1000 + i for i in range(NPLAC)]))
        placebo = {w: [res["after_no_ref"][w]["total"] - d[w]["total"] for d in draws] for w in WIN}
        pd.DataFrame(placebo).to_csv(REP / "leak_fix_rescore_placebo.csv", index=False)
    rows = [{"variant": v, "window": w, "team_miss": round(sc[w]["team"], 4), "total_miss": round(sc[w]["total"], 4),
             "margin_miss": round(sc[w]["margin"], 4), "spread_flag": rec(sc[w]["spread"]), "totals_flag": rec(sc[w]["totals"]),
             "wind_under": rec(sc[w]["wind"])} for v, sc in res.items() for w in WIN]
    pd.DataFrame(rows).to_csv(REP / "leak_fix_rescore.csv", index=False)
    gr = gate_rows(res["after_no_ref"], res["after"], placebo)
    L = ["# Leak fixes rescored (2 Oct 2026)", "",
         "Fix 1: the referee prior (ref_tot, also ref_over and ref_pen) now counts only games that kicked off strictly before this one; "
         "the home row used to count the away row of the same game, this game's own total. Fix 2: the wind reading uses Japan's "
         "day-before run (jma_wind_d1), not its newest run (issued at or after kickoff); Open-Meteo keeps no 2018-2025 single runs to refetch.", "",
         "Each variant is the live model refit walk-forward 2015-2025 (regular season; flags weeks 1-17 against the close).", "",
         "| Variant | Window | Team miss | Total miss | Margin miss | Spread flag (4+) | Totals flag (55% under) | Wind under (10+ mph) |",
         "|---|---|---|---|---|---|---|---|"]
    L += [f"| {r['variant']} | {r['window']} | {r['team_miss']:.4f} | {r['total_miss']:.4f} | {r['margin_miss']:.4f} | {r['spread_flag']} | {r['totals_flag']} | {r['wind_under']} |" for r in rows]
    L += ["", "## ref_tot after the fix (study_gate: total miss, no ref_tot -> ref_tot)", "", G.markdown(gr)]
    (REP / "leak_fix_rescore.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
