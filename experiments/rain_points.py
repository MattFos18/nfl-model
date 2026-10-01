"""Rain as points on the model's total, every way we could find (1 Oct 2026, Matt: "I don't want just a flag, I want the
points quantified, figure out the best way"). The weather retest (reports/weather_forecast_retest.md) found blind unders at a
GFS MOS rain chance of 50%+ went 102-60 against the closing total, games that finished 2.9 points under the line on
average while the model had them 0.3 under; but rain band points on top of the total missed worse on 2019-22.

Why the model under-counts rain: the totals equation's rain input (trends.py) is, for every played game, the weather that
happened (the schedule's weather text says rain), while an upcoming game is priced on the forecast (a 50%+ chance). The
equation learns what a rainy game is worth, then is handed a forecast, which is right less often. Two families:

  A. The input itself (the totals equation refit walk-forward, 2015-2025, the points equations untouched):
     A1 rain = forecast chance 50%+ for every game with a stored forecast (2018-2025), the weather text before 2018;
     A2 rain = forecast chance / 100 (continuous) from 2018, the weather text before;
     A3 the weather text kept, plus a second input: forecast chance / 100 (0 before 2018 or without a forecast);
     A4 rain = forecast chance 50%+ from 2018 and zero before (no weather text at all).
  B. Points on top of the live total (as model.wind_points, walk-forward from the seasons before, shrunk by K games):
     B1 bands [0,20) [20,50) 50+ at K = 25, 50, 100; B2 cuts at 40 and 60; B3 a straight line in the chance (the slope
     on the forecast games of earlier seasons, shrunk by K = 50); B4 50+ only (one band).
Scored per window 2015-18 / 2019-22 / 2023-25 on the total miss (all games, and the forecast games), the spread miss (A only,
the points equations are untouched so it should not move), the totals flag (1 - p_over_emp >= 55%, weeks 1-17, re-priced),
and, for the best of each family, 20 within-season shuffles of the forecast chance (A: the equation refit on each shuffle).
Writes reports/rain_points.{md,csv}.

    python -m experiments.rain_points
"""
from __future__ import annotations
import numpy as np, pandas as pd
from nflmodel import backtest as B, model as M, picks as P
from nflmodel.features import OUT, ROOT
from nflmodel.forecast_history import OUTF
from experiments.weather_forecast_retest import p_over

REP = ROOT / "reports"
WIN = {"2015-18": (2015, 2018), "2019-22": (2019, 2022), "2023-25": (2023, 2025)}
NPLAC, SEED = 20, 11
_orig_gf, _orig_tf = M._game_frame, list(M.TOTAL_FEATS)


def forecast_pop() -> pd.Series:
    h = pd.read_csv(OUTF).set_index("game_id")
    return h.gfs_pop_d0.fillna(h.gfs_pop_d1).astype(float)


def with_input(f: pd.DataFrame, pop: pd.Series, how: str) -> pd.DataFrame:
    """f with the totals equation's rain inputs for variant how (rain_t replaces rain; rain_fc is A3's second input)."""
    f = f.copy(); p = f.game_id.map(pop); outdoor = f.dome.fillna(0).eq(0); has = p.notna() & outdoor
    f["rain_t"], f["rain_fc"] = f.rain.astype(float), 0.0
    if how == "A1":
        f.loc[has, "rain_t"] = (p[has] >= 50).astype(float)
    elif how == "A2":
        f.loc[has, "rain_t"] = p[has] / 100
    elif how == "A3":
        f.loc[has, "rain_fc"] = p[has] / 100
    elif how == "A4":
        f["rain_t"] = 0.0; f.loc[has, "rain_t"] = (p[has] >= 50).astype(float)
    f.loc[~outdoor, ["rain_t", "rain_fc"]] = 0.0
    return f


def patch(how: str | None):
    """Point the totals equation at rain_t (and rain_fc for A3); None restores the live equation."""
    if how is None:
        M._game_frame, M.TOTAL_FEATS[:] = _orig_gf, _orig_tf
        return
    def gf(f):
        g = _orig_gf(f); h = f[f.home == 1].set_index("game_id").reindex(g.index)
        g["rain"] = h.rain_t.values; g["rain_fc"] = h.rain_fc.values
        return g
    M._game_frame = gf
    M.TOTAL_FEATS[:] = _orig_tf + (["rain_fc"] if how == "A3" else [])


def run(f, how):
    patch(how)
    try:
        p = M.walk_forward(f, range(2015, 2026), 10.0)
        dist = {k: np.asarray(v["tres"], dtype=float) for k, v in M.DIST.items()}
    finally:
        patch(None)
    d = B.join(p, pd.read_parquet(OUT / "games.parquet"))
    d = d[(d.game_type == "REG") & d.home_score.notna() & d.total_line.notna()].reset_index(drop=True)
    d["act"] = d.home_score + d.away_score; d["r"] = d.act - d.model_total
    d["tres_key"] = list(zip(d.season.astype(int), d.week.astype(int)))
    return d, dist


def flag(d, po):
    m = ((1 - po) >= 0.55) & (d.week <= P.LAST_BET_WEEK); cm = d.act - d.total_line; f = m & (cm != 0)
    w = int((cm < 0)[f].sum()); return w, int(f.sum()) - w


def score(d, pop, shift=None, po=None) -> dict:
    shift = pd.Series(0.0, index=d.index) if shift is None else shift
    po = d.p_over_emp if po is None else po
    fc = d.game_id.map(pop).notna(); out = {}
    for w, (a, b) in WIN.items():
        s = d.season.between(a, b); r = (d.r - shift)
        sp = (d.result - d.model_spread).abs()[s].mean() if "result" in d else np.nan
        fw, fl = flag(d[s], po[s])
        out[w] = {"miss": r[s].abs().mean(), "miss_fc": r[s & fc].abs().mean() if (s & fc).any() else np.nan,
                  "spread": sp, "flag": f"{fw}-{fl}", "net": fw - fl}
    return out


def posthoc(d, pop, edges=None, k=50.0, line=False) -> pd.Series:
    """B: walk-forward points on top of the total from the forecast games of earlier seasons."""
    p = d.game_id.map(pop); out = pd.Series(0.0, index=d.index)
    for s in range(2019, 2026):
        tr = p.notna() & (d.season < s) & d.season.ge(2018); te = p.notna() & (d.season == s)
        if not tr.any() or not te.any():
            continue
        r = d.r[tr]; base = r.mean()
        if line:
            x = p[tr] / 100 - (p[tr] / 100).mean(); slope = float((x * (r - base)).sum() / ((x ** 2).sum() + k * x.var()))
            out[te] = slope * (p[te] / 100 - (p[tr] / 100).mean())
            continue
        lab_tr = pd.cut(p[tr], edges, right=False); lab_te = pd.cut(p[te], edges, right=False)
        e = r.groupby(lab_tr, observed=True).agg(["sum", "size"]); e = (e["sum"] - base * e["size"]) / (e["size"] + k)
        out[te] = lab_te.map(e).astype(float).fillna(0).values
    return out


def row(name, sc, base, extra=""):
    r = {"variant": name}
    for w in WIN:
        r[f"{w} miss"] = f"{base[w]['miss']:.3f} -> {sc[w]['miss']:.3f}"
        r[f"{w} forecast-game miss"] = "" if np.isnan(sc[w]["miss_fc"]) else f"{base[w]['miss_fc']:.3f} -> {sc[w]['miss_fc']:.3f}"
        r[f"{w} flag"] = f"{base[w]['flag']} -> {sc[w]['flag']}"
    r["better every window"] = all(sc[w]["miss"] < base[w]["miss"] - 1e-9 for w in ("2019-22", "2023-25")) and sc["2015-18"]["miss"] <= base["2015-18"]["miss"] + 1e-9
    r["flag not worse"] = all(sc[w]["net"] >= base[w]["net"] for w in WIN)
    r["note"] = extra
    return r


def gain(sc, base):
    return [base[w]["miss"] - sc[w]["miss"] for w in ("2019-22", "2023-25")]


def main():
    rng = np.random.default_rng(SEED)
    f = M.with_trends(pd.read_parquet(OUT / "features_asof.parquet")); pop = forecast_pop()
    g = pd.read_parquet(OUT / "games.parquet").set_index("game_id")
    base_d, base_dist = run(with_input(f, pop, "base"), "base")
    base_d["result"] = base_d.game_id.map(g.result); base = score(base_d, pop)
    rows, L = [], ["# Rain as points on the model's total", ""]
    rs = (base_d.game_id.map(pop) >= 50) & (base_d.week <= 17) & base_d.season.between(2018, 2025)
    L += [f"Rain 50%+ games 2018-25 (weeks 1-17): {int(rs.sum())}; they finished {(base_d.act - base_d.total_line)[rs].mean():+.2f} against the closing total "
          f"and the live model had them {(base_d.model_total - base_d.total_line)[rs].mean():+.2f}; every other game {(base_d.act - base_d.total_line)[~rs & base_d.season.between(2018, 2025) & (base_d.week <= 17)].mean():+.2f} "
          f"and {(base_d.model_total - base_d.total_line)[~rs & base_d.season.between(2018, 2025) & (base_d.week <= 17)].mean():+.2f}.", ""]
    # A: the input
    A = {}
    for how in ["A1", "A2", "A3", "A4"]:
        d, _ = run(with_input(f, pop, how), how); d["result"] = d.game_id.map(g.result); sc = score(d, pop); A[how] = (d, sc)
        rows.append(row({"A1": "A1 input: forecast 50%+ from 2018, weather text before", "A2": "A2 input: forecast chance / 100 from 2018, weather text before",
                         "A3": "A3 input: weather text plus forecast chance / 100", "A4": "A4 input: forecast 50%+ only (no weather text)"}[how], sc, base,
                        f"spread miss {base['2019-22']['spread']:.4f} -> {sc['2019-22']['spread']:.4f} / {base['2023-25']['spread']:.4f} -> {sc['2023-25']['spread']:.4f}; rain points "
                        f"{(d.model_total - base_d.set_index('game_id').model_total.reindex(d.game_id).values)[(d.game_id.map(pop) >= 50).values & d.season.between(2019, 2025).values].mean():+.2f} on 50%+ games"))
        print(rows[-1], flush=True)
    # B: points on top
    Bv = {"B1 bands 20/50, K 25": dict(edges=[0, 20, 50, 101], k=25), "B1 bands 20/50, K 50": dict(edges=[0, 20, 50, 101], k=50),
          "B1 bands 20/50, K 100": dict(edges=[0, 20, 50, 101], k=100), "B2 bands 40/60, K 50": dict(edges=[0, 40, 60, 101], k=50),
          "B3 straight line in the chance, K 50": dict(line=True, k=50), "B4 50%+ only, K 50": dict(edges=[0, 50, 101], k=50)}
    Bres = {}
    for name, kw in Bv.items():
        sh = posthoc(base_d, pop, **kw); po = p_over(base_d, base_dist, sh); sc = score(base_d, pop, sh, po); Bres[name] = (sh, sc)
        rows.append(row(name, sc, base, f"50%+ games {sh[rs].mean():+.2f} points"))
        print(rows[-1], flush=True)
    T = pd.DataFrame(rows)
    # placebo for the best of each family (largest worst-window gain)
    best_a = max(A, key=lambda h: min(gain(A[h][1], base))); best_b = max(Bres, key=lambda n: min(gain(Bres[n][1], base)))
    pl = []
    for fam, name in [("A", best_a), ("B", best_b)]:
        real = gain(A[name][1] if fam == "A" else Bres[name][1], base); beats = 0
        for i in range(NPLAC):
            sp = pop.copy(); seas = sp.index.str[:4].astype(int)
            for s in range(2018, 2026):
                ix = sp.index[(seas == s) & sp.notna()]; sp[ix] = rng.permutation(sp[ix].values)
            if fam == "A":
                d, _ = run(with_input(f, sp, name), name); sc = score(d, sp)
            else:
                sh = posthoc(base_d, sp, **Bv[name]); sc = score(base_d, sp, sh)
            g_ = gain(sc, base); beats += all(gi < real[j] for j, gi in enumerate(g_))
            print(fam, name, i, g_, flush=True)
        pl.append({"variant": name, "real gain (2019-22, 2023-25)": f"{real[0]:+.4f}, {real[1]:+.4f}", "shuffles beaten": f"{beats} of {NPLAC}"})
    T.to_csv(REP / "rain_points.csv", index=False)
    L += ["## Every variant (total miss: all games; forecast-game miss: games with a stored forecast; flag: the totals flag, weeks 1-17)", "",
          T.to_markdown(index=False), "", "## Placebo (the forecast chance shuffled within season; real gain must beat the shuffle on both windows)", "",
          pd.DataFrame(pl).to_markdown(index=False), ""]
    (REP / "rain_points.md").write_text("\n".join(L)); print("\n".join(L))


if __name__ == "__main__":
    main()
