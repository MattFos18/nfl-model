"""Rain, cold and gusts re-tested on forecasts (1 Oct 2026, after wind points went in). Weather other than wind tested
flat before on the weather that happened; wind turned real once it was read off pre-kickoff forecasts
(reports/wind_forecast.md, experiments/wind_points.py). This does the same for the rest, on the GFS MOS temperature and
chance of precipitation at the stadium's airport (nflmodel/forecast_history.py --extend: the last run out at least 5 hours
before kickoff, the day-before 12Z run where it is missing; temperature the mean over the first 3 hours, the chance the
largest 6-hour p06 whose period overlaps them) and the National Blend's gust (Nov 2018 to 2019 only), 2018-2025.

  1. Band points on top of the model's total, exactly as model.wind_points: each season's band amounts are each band's mean
     miss (actual total minus the model's total, wind points already in) against the mean miss of every forecast game of
     the seasons before, shrunk by K = 50 games. Scored on the total miss of the forecast games and the team points miss
     (each team's expected points moved by half), per window 2018 / 2019-22 / 2023-25 (2018 has no earlier forecasts, so
     it and 2015-17 are unchanged by construction), the totals flag (1 - p_over_emp >= 0.55, weeks 1-17) re-priced at the
     adjusted total with the fit's own training misses (model.price_at, the walk-forward's DIST), and 50 within-season
     shuffles of the new reading (the wind left real).
  2. Blind unders at forecast cuts against the closing total, weeks 1-17, record and units at -110 per window, with 200
     within-season shuffles (the share as good on units, 2018-25).
The model is rerun walk-forward 2015-2025 first (about a minute), so the wind points and every fit's training misses are
the live code's. Writes reports/weather_forecast_retest.{md,csv}.

    python -m experiments.weather_forecast_retest
"""
from __future__ import annotations
import numpy as np, pandas as pd
from nflmodel import backtest as B, model as M
from nflmodel.features import OUT, ROOT
from nflmodel.forecast_history import OUTF

REP = ROOT / "reports"
K, NPLAC, NPLAC_BLIND = 50, 50, 200
WIN = {"2018": (2018, 2018), "2019-22": (2019, 2022), "2023-25": (2023, 2025)}
SCORED = ["2019-22", "2023-25"]
RAIN, COLD, GUST = [0, 20, 50, 101], [-99, 32, 45, 999], [0, 20, 30, 999]


def load():
    f = M.with_trends(pd.read_parquet(OUT / "features_asof.parquet"))
    pred = M.walk_forward(f, range(2015, 2026), 10.0)
    dist = {k: np.asarray(v["tres"], dtype=float) for k, v in M.DIST.items()}
    d = B.join(pred, pd.read_parquet(OUT / "games.parquet"))
    d = d[(d.game_type == "REG") & d.total_line.notna() & d.season.between(2015, 2025)].reset_index(drop=True)
    h = pd.read_csv(OUTF).set_index("game_id")
    pick = lambda a, b: d.game_id.map(h[a]).fillna(d.game_id.map(h[b])).astype(float)
    d["pop"], d["temp"], d["gust"] = pick("gfs_pop_d0", "gfs_pop_d1"), pick("gfs_temp_d0", "gfs_temp_d1"), pick("nbs_gust_d0", "nbs_gust_d1")
    d["pop_d1"], d["temp_d1"] = d.game_id.map(h.gfs_pop_d1).astype(float), d.game_id.map(h.gfs_temp_d1).astype(float)
    d["fw"] = d.wind_fc.astype(float)
    d["act"] = d.home_score + d.away_score; d["r"] = d.act - d.model_total
    d["tres_key"] = list(zip(d.season.astype(int), d.week.astype(int)))
    return d, dist


def bands(x, edges):
    return pd.cut(x, edges, right=False).astype(str).where(x.notna())


def cells(a, b):
    return (a.astype(str) + " & " + b.astype(str)).where(a.notna() & b.notna())


# each idea: (label, the columns shuffled for its placebo, a function of the game table to its band label per game)
IDEAS = {
    "rain": ("rain chance bands [0,20) [20,50) 50+ (last run)", ["pop"], lambda d: bands(d["pop"], RAIN)),
    "rain_d1": ("rain chance bands, day-before run", ["pop_d1"], lambda d: bands(d["pop_d1"], RAIN)),
    "cold": ("temperature bands <32, 32-45, 45+ F (last run)", ["temp"], lambda d: bands(d["temp"], COLD)),
    "cold_d1": ("temperature bands, day-before run", ["temp_d1"], lambda d: bands(d["temp_d1"], COLD)),
    "gust": ("Blend gust bands [0,20) [20,30) 30+ mph (Nov 2018-2019 only)", ["gust"], lambda d: bands(d["gust"], GUST)),
    "rain_x_wind": ("rain 50+ x wind 10+ (four cells)", ["pop"], lambda d: cells(d["pop"] >= 50, d.fw >= 10).where(d["pop"].notna() & d.fw.notna())),
    "cold_x_wind": ("below 32 F x wind 10+ (four cells)", ["temp"], lambda d: cells(d["temp"] < 32, d.fw >= 10).where(d["temp"].notna() & d.fw.notna())),
    "wet_or_cold": ("rain 50+ or below 32 F (two cells)", ["pop", "temp"], lambda d: ((d["pop"] >= 50) | (d["temp"] < 32)).astype(str).where(d["pop"].notna() & d["temp"].notna())),
}


def adj(d, lab):
    """Walk-forward band amounts, as model.wind_points: band mean miss minus the pool's mean miss, shrunk by K."""
    out = pd.Series(0.0, index=d.index)
    for s in range(2019, 2026):
        tr = lab.notna() & (d.season < s); te = lab.notna() & (d.season == s)
        if not tr.any() or not te.any():
            continue
        base = d.r[tr].mean(); e = d.r[tr].groupby(lab[tr]).agg(["sum", "size"])
        e = (e["sum"] - base * e["size"]) / (e["size"] + K)
        out[te] = lab[te].map(e).astype(float).fillna(0).values
    return out


def p_over(d, dist, shift):
    """p_over_emp re-priced at the model's total plus shift, with the training misses of the fit that priced each game."""
    out = d.p_over_emp.values.copy(); s = shift.values
    for i in np.flatnonzero(s != 0):
        tres = dist[d.tres_key.iat[i]]; v = d.model_total.iat[i] + s[i] + tres; tl = d.total_line.iat[i]
        out[i] = np.mean(v > tl) / max(1e-9, np.mean(v != tl))
    return pd.Series(out, index=d.index)


def flag(d, po):
    m = ((1 - po) >= 0.55) & (d.week <= 17); cm = d.act - d.total_line; f = m & (cm != 0)
    return int((cm < 0)[f].sum()), int(f.sum()) - int((cm < 0)[f].sum())


def score(d, a, lab, dist=None):
    """Per window: games with the reading, total miss before/after, team points miss before/after, flag before/after."""
    out = {}
    po = p_over(d, dist, a) if dist is not None else None
    tp0 = pd.concat([(d.home_exp - d.home_score).abs(), (d.away_exp - d.away_score).abs()], axis=1).mean(axis=1)
    tp1 = pd.concat([(d.home_exp + a / 2 - d.home_score).abs(), (d.away_exp + a / 2 - d.away_score).abs()], axis=1).mean(axis=1)
    for w, (lo, hi) in WIN.items():
        sw = d.season.between(lo, hi); m = sw & lab.notna()
        o = {"n": int(m.sum()), "miss0": d.r[m].abs().mean(), "miss1": (d.r - a)[m].abs().mean(), "tp0": tp0[sw].mean(), "tp1": tp1[sw].mean()}
        if po is not None:
            o["flag0"], o["flag1"] = flag(d[sw], d.p_over_emp[sw]), flag(d[sw], po[sw])
        out[w] = o
    return out


def placebo(d, cols, fn, real, rng):
    beats, gains = 0, []
    for _ in range(NPLAC):
        dd = d.copy()
        for s in range(2018, 2026):
            ix = dd.index[(dd.season == s) & dd[cols].notna().all(axis=1)]
            perm = rng.permutation(len(ix))
            for c in cols:
                dd.loc[ix, c] = dd.loc[ix, c].values[perm]
        lab = fn(dd); aa = adj(dd, lab); sc = score(d, aa, lab)
        g = [sc[w]["miss0"] - sc[w]["miss1"] if sc[w]["n"] else 0.0 for w in SCORED]
        gains.append(g); beats += all(gi < real[i] for i, gi in enumerate(g))
    return beats, np.percentile(np.array(gains), 90, axis=0)


CUTS = {   # blind unders: name -> (label, mask function, columns shuffled)
    "rain50": ("rain chance 50+", lambda d: d["pop"] >= 50, ["pop"]),
    "rain70": ("rain chance 70+", lambda d: d["pop"] >= 70, ["pop"]),
    "rain50_calm": ("rain 50+, wind under 10", lambda d: (d["pop"] >= 50) & (d.fw < 10), ["pop"]),
    "rain50_windy": ("rain 50+, wind 10+", lambda d: (d["pop"] >= 50) & (d.fw >= 10), ["pop"]),
    "cold32": ("below 32 F", lambda d: d["temp"] < 32, ["temp"]),
    "cold40": ("below 40 F", lambda d: d["temp"] < 40, ["temp"]),
    "cold32_calm": ("below 32 F, wind under 10", lambda d: (d["temp"] < 32) & (d.fw < 10), ["temp"]),
    "cold32_windy": ("below 32 F, wind 10+", lambda d: (d["temp"] < 32) & (d.fw >= 10), ["temp"]),
    "gust25": ("Blend gust 25+ mph", lambda d: d["gust"] >= 25, ["gust"]),
    "gust30": ("Blend gust 30+ mph", lambda d: d["gust"] >= 30, ["gust"]),
    "wind10": ("wind 10+ (the live wind under, for reference)", lambda d: d.fw >= 10, ["fw"]),
}


def blind(d, rng):
    rows = []
    b = d[d.season.between(2018, 2025) & (d.week <= 17)].copy()
    cm = b.act - b.total_line

    def rec(m):
        f = m & (cm != 0); w = int((cm < 0)[f].sum()); return w, int(f.sum()) - w
    for name, (lab, fn, cols) in CUTS.items():
        m = fn(b).fillna(False)
        r = {"kind": "blind under", "idea": name, "label": lab}
        for w, (lo, hi) in WIN.items():
            wi, lo_ = rec(m & b.season.between(lo, hi)); r[w] = f"{wi}-{lo_}"
        wi, lo_ = rec(m); u = wi - 1.1 * lo_
        r.update({"all": f"{wi}-{lo_}", "win_pct": round(100 * wi / max(1, wi + lo_), 1), "units": round(u, 1)})
        good = 0
        for _ in range(NPLAC_BLIND):
            bb = b.copy()
            for s in range(2018, 2026):
                ix = bb.index[(bb.season == s) & bb[cols].notna().all(axis=1)]; perm = rng.permutation(len(ix))
                for c in cols:
                    bb.loc[ix, c] = bb.loc[ix, c].values[perm]
            pw, pl = rec(fn(bb).fillna(False)); good += (pw - 1.1 * pl) >= u
        r["placebo_share"] = round(good / NPLAC_BLIND, 3)
        rows.append(r)
    return rows


VERDICT = """## Verdict (round-3 rule)

| Idea | Verdict | Why |
|---|---|---|
| Rain points (chance bands) | Reject | Total miss worse on 2019-22 (10.342 -> 10.357), better on 2023-25; 11 of 50 shuffles beaten (45 needed). The day-before run is worse on both windows. |
| Cold points (temperature bands) | Reject | Better on 2019-22, worse on 2023-25 (10.089 -> 10.091); 28 of 50 shuffles beaten. The day-before run is the other near miss: better on both windows (10.342 -> 10.315, 10.089 -> 10.079), team points better on both, flag not worse (net 53 -> 53, 19 -> 22), but it beats 44 of 50 shuffles, one short of 45. |
| Gust points (Blend) | Reject (cannot be tested) | The Blend's gust exists for 223 last-run games, Nov 2018 to 2019 only; band points can be scored on 2019 alone (178 games) and on no game after it (so 0 of 50 shuffles can be beaten on both windows); 2019 alone 10.626 -> 10.614. Blind unders at 25+ mph 16-12. |
| Rain x wind points | Reject | Total miss worse on 2019-22 (10.342 -> 10.344); 41 of 50. |
| Cold x wind points | Reject | Total miss worse on 2019-22 (10.342 -> 10.366); 0 of 50. |
| Wet or cold points (rain 50+ or below 32 F, one band) | Reject | Total miss better on both windows (10.342 -> 10.301, 10.089 -> 10.034), team points better on both, 50 of 50 shuffles beaten, about -2.1 points in those games; but the totals flag on 2019-22 goes 182-129 -> 168-120 (net 53 -> 48), failing the no-bet-cost test (2023-25: 81-62 -> 85-54). |
| Blind under, rain chance 50+ | Track as a hidden shadow | 11-9 / 55-30 / 36-21, 102-60 (63.0%), +36.0 units, 0.5% of 200 shuffles as good. With wind under 10 (games the wind under does not already bet) 64-41, 0 of 200. Found on the backtest, so graded live, not bet; 2025 went 7-8 and 70+ is weaker (54-39), so it must prove itself live. Its live reading is the GFS MOS response the wind under already pulls (no new source). |
| Blind under, below 32 F | Reject | 36-27, 27.5% of shuffles as good; below 40 F 93-84. |

The backtest's total already carries the model's own rain, cold and wind terms, which in past seasons read the weather
that happened (live they read the forecast), so this measures what the forecast adds beyond them. Two data notes: the
GFS MOS writes 999 / 99 for a missing hour; one game (2018_16_BAL_LAC at KTOA) had its stored GFS wind built from those
(18.6 mph against the Japan model's 3.9). forecast_history.mos_all now reads them as missing for every field and that game
was refetched (GFS 7.4 / 5.5 mph), which took it out of the wind under (2018: 24-19 -> 23-19) and the 10-15 band.
And this study reruns the model itself first, so it never depends on a stored prediction table being current.
"""


def fmt(x):
    return "" if pd.isna(x) else str(x)


def write_md(out):
    bp, bl = out[out.kind == "band points"], out[out.kind == "blind under"]
    L = ["# Rain, cold and gusts re-tested on forecasts", "",
         "1 Oct 2026. `experiments/weather_forecast_retest.py`, data `data/weather/forecast_history.csv` (GFS MOS temperature and",
         "rain chance added by `nflmodel/forecast_history.py --extend`; 1,526 outdoor or open-roof games 2018-2025). Band points on",
         "top of the model's total (wind points already in), walk-forward like `model.wind_points` (K = 50); 2018 has no earlier",
         "forecasts, so it and 2015-17 are unchanged by construction. Totals flag: under at 1 - p_over_emp >= 0.55, weeks 1-17,",
         "re-priced at the adjusted total with each fit's own training misses. Placebo: the reading shuffled within season (50",
         "draws), counted when the real gain beats the shuffle on both 2019-22 and 2023-25 (45 of 50 needed).", "",
         "## Band points", "",
         "| Idea | 2019-22 total miss | 2023-25 total miss | 2019-22 team pts | 2023-25 team pts | 2019-22 flag | 2023-25 flag | Shuffles beaten | 2025 amounts |",
         "|---|---|---|---|---|---|---|---|---|"]
    for r in bp.itertuples():
        g = r._asdict(); c = lambda k: fmt(out.loc[r.Index, k])
        L.append(f"| {r.label} | {c('2019-22 total miss')} | {c('2023-25 total miss')} | {c('2019-22 team pts')} | {c('2023-25 team pts')} | {c('2019-22 flag')} | {c('2023-25 flag')} | {int(r.placebo_beats)} of {NPLAC} | {fmt(r.amounts_2025)} |")
    L += ["", "Forecast games scored: " + ", ".join(f"{r.idea} {int(out.loc[r.Index, '2019-22 n'])} / {int(out.loc[r.Index, '2023-25 n'])}" for r in bp.itertuples()) + " (2019-22 / 2023-25).", "",
          "## Blind unders at forecast cuts (weeks 1-17, closing total, -110)", "",
          "| Cut | 2018 | 2019-22 | 2023-25 | All | Win % | Units | Shuffles as good |", "|---|---|---|---|---|---|---|---|"]
    for r in bl.itertuples():
        c = lambda k: fmt(out.loc[r.Index, k])
        L.append(f"| {r.label} | {c('2018')} | {c('2019-22')} | {c('2023-25')} | {c('all')} | {c('win_pct')} | {c('units')} | {c('placebo_share')} |")
    L += ["", VERDICT]
    (REP / "weather_forecast_retest.md").write_text("\n".join(L))


def main():
    d, dist = load()
    chk = p_over(d, dist, pd.Series(1e-12, index=d.index))   # re-pricing with no shift returns the model's own chance
    assert np.nanmax(np.abs(chk - d.p_over_emp)) < 1e-6, "re-pricing does not reproduce p_over_emp"
    rng = np.random.default_rng(7); rows = []
    for name, (lab_, cols, fn) in IDEAS.items():
        lab = fn(d); a = adj(d, lab); sc = score(d, a, lab, dist)
        real = [sc[w]["miss0"] - sc[w]["miss1"] if sc[w]["n"] else 0.0 for w in SCORED]
        beats, p90 = placebo(d, cols, fn, real, rng)
        last = d[(d.season == 2025) & lab.notna()]; amt = a[last.index].groupby(lab[last.index]).first().round(2).to_dict()
        r = {"kind": "band points", "idea": name, "label": lab_, "placebo_beats": beats, "placebo_p90_1922": round(p90[0], 4), "placebo_p90_2325": round(p90[1], 4),
             "amounts_2025": "; ".join(f"{k}: {v:+.2f}" for k, v in amt.items())}
        for w, o in sc.items():
            r[f"{w} n"] = o["n"]; r[f"{w} total miss"] = f"{o['miss0']:.3f} -> {o['miss1']:.3f}" if o["n"] else "no games"; r[f"{w} team pts"] = f"{o['tp0']:.4f} -> {o['tp1']:.4f}"
            r[f"{w} flag"] = f"{o['flag0'][0]}-{o['flag0'][1]} -> {o['flag1'][0]}-{o['flag1'][1]}"
        rows.append(r); print(name, {k: v for k, v in r.items() if k not in ("label",)}, flush=True)
    br = blind(d, rng)
    for r in br:
        print(r, flush=True)
    out = pd.DataFrame(rows + br); out.to_csv(REP / "weather_forecast_retest.csv", index=False)
    write_md(out)
    return out


if __name__ == "__main__":
    main()
