"""Overs, in depth (2 Oct 2026, Matt: "an in-depth study on the overs: see what's going on, fine-tune, look for flags and
things that can improve this, thresholds, whatever"). Pre-registration and results: reports/overs_deep.md.

Stage 1 (base): the live model's walk-forward on main's code (honest backtest: #381 data fixes, #384 leak fixes, #387
ref_tot dropped, #389 forecast weather for played games 2018+), 2014-2025 (2014 only feeds the model-change fits of
2015), cached in the temp folder with each fit's training misses (model.DIST tres).
Stage 2 (diagnose): the over side sliced every pre-registered way, by window.
Stage 3 (rules): the pre-registered over rules, three windows at -110, 200 within-season shuffles each, and a family-wise
shuffle (outcomes permuted within season, the best rule's units) for the snooping-adjusted strength.
Stage 4 (model): M1 / M2 total corrections through nflmodel.study_gate with 50-draw placebos.
Writes reports/overs_deep.csv (every table, long form) and reports/overs_deep_results.md.

    python -m experiments.overs_deep [--fresh]
"""
from __future__ import annotations
import pickle, sys, tempfile, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import numpy as np, pandas as pd
from nflmodel import backtest as B, model as M, picks as P, study_gate as G
from nflmodel.features import OUT, ROOT

REP = ROOT / "reports"
TMP = Path(tempfile.gettempdir()) / "overs_deep"
M.save_trees_cache = lambda: None   # an experiment never rewrites data/processed/trees_cache.parquet
GAMES = pd.read_parquet(OUT / "games.parquet")


def base(fresh=False):
    """(pred, tres): the live walk-forward 2014-2025 and each fit's training misses {(season, week): array}."""
    TMP.mkdir(parents=True, exist_ok=True); pf, tf = TMP / "pred.parquet", TMP / "tres.pkl"
    if pf.exists() and tf.exists() and not fresh:
        return pd.read_parquet(pf), pickle.loads(tf.read_bytes())
    t0 = time.time(); M.DIST.clear()
    f = M.with_trends(pd.read_parquet(OUT / "features_asof.parquet"))
    p = M.walk_forward(f, range(2014, 2026), M.RIDGE)
    tres = {k: np.asarray(v["tres"], dtype=float) for k, v in M.DIST.items()}
    p.to_parquet(pf); tf.write_bytes(pickle.dumps(tres))
    print(f"base priced in {time.time() - t0:.0f}s", flush=True)
    return p, tres


WIN = {"2015-18": (2015, 2018), "2019-22": (2019, 2022), "2023-25": (2023, 2025)}
SEED, NRULE, NFAM, NMOD = 7, 200, 1000, 50
OUTROWS: list = []   # long-form table: section, slice, window, values


def put(section, slice_, window, **v):
    OUTROWS.append({"section": section, "slice": str(slice_), "window": window, **v})


def p_emp(mt, tl, tres):
    """model.price_at's over chance off the fit's training misses (pushes left out)."""
    if pd.isna(tl) or tres is None:
        return np.nan
    x = mt + tres
    return float(np.mean(x > tl) / max(1e-9, np.mean(x != tl)))


def frame(p, tres) -> pd.DataFrame:
    """Played regular-season games with a line, 2014-2025, with every slicing reading."""
    d = B.join(p, GAMES); d = d[(d.game_type == "REG") & d.total_line.notna()].copy()
    cal = P.over_calibrations(p, GAMES)
    d["p_cal"] = [P.over_cal_p(cal[int(s)], x) if pd.notna(x) and int(s) in cal else np.nan for s, x in zip(d.season, d.p_over_emp)]
    g = GAMES.set_index("game_id")
    d["dome"] = d.game_id.map(g.dome).fillna(0).astype(float); d["prime"] = d.game_id.map(g.primetime).fillna(False).astype(bool)
    d["rain_fc"] = d.game_id.map(P._rain()).astype(float)
    f = M.prep(M.with_trends(pd.read_parquet(OUT / "features_asof.parquet")))
    h = f[f.home == 1].set_index("game_id"); a = f[f.home == 0].set_index("game_id")
    for k, c in (("pace", "off_plays"), ("qbr", "qb_rating"), ("qbf", "qb_form")):
        d[f"h_{k}"] = d.game_id.map(h[c]).astype(float); d[f"a_{k}"] = d.game_id.map(a[c]).astype(float); d[f"{k}_sum"] = d[f"h_{k}"] + d[f"a_{k}"]
    # pace cut for O14: the median of every earlier season's games (2013 on), so nothing from the season priced
    allp = pd.DataFrame({"season": h.season, "pace": h.off_plays + a.off_plays.reindex(h.index)}).dropna()
    d["pace_cut"] = d.season.map({s: float(allp.pace[allp.season < s].median()) for s in d.season.unique()})
    d["cm"] = d.total - d.total_line   # actual minus the line: > 0 the over won
    d["edge"] = d.model_total - d.total_line
    d["wk17"] = d.week <= P.LAST_BET_WEEK
    d["tres_key"] = list(zip(d.season.astype(int), d.week.astype(int)))
    return d


def wl(cm: pd.Series, m) -> tuple[int, int]:
    m = np.asarray(m, dtype=bool); c = np.asarray(cm)[m]
    return int((c > 0).sum()), int((c < 0).sum())


def units(w, l):
    return round(w * 100 / 110 - l, 1)


def rec_str(w, l):
    return f"{w}-{l}" + (f" ({100 * w / (w + l):.1f}%, {units(w, l):+.1f}u)" if w + l else "")


def windows(d):
    for w, (lo, hi) in WIN.items():
        yield w, d[d.season.between(lo, hi)]


# ---------------------------------------------------------------- Part 1: diagnosis
def slice_table(d, section, labels: pd.Series, order=None):
    """Blind over and the model's over calls (55%+ raw) by slice, per window, weeks 1-17."""
    x0 = d[d.wk17]; lab = labels.reindex(x0.index)
    keys = order or sorted(lab.dropna().unique())
    for k in keys:
        for w, x in windows(x0):
            m = lab.reindex(x.index) == k
            bw, bl = wl(x.cm, m); cw, cl = wl(x.cm, m & (x.p_over_emp >= 0.55))
            put(section, k, w, n=int(m.sum()), blind_over=rec_str(bw, bl), blind_pct=round(100 * bw / max(1, bw + bl), 1),
                model_over55=rec_str(cw, cl), mean_cm=round(float(x.cm[m].mean()), 2) if m.any() else np.nan,
                model_minus_actual=round(float((x.model_total - x.total)[m].mean()), 2) if m.any() else np.nan)


def diagnose(d):
    x0 = d[d.season.between(2015, 2025)]
    # D1 base rates
    for w, x in windows(x0[x0.wk17]):
        bw, bl = wl(x.cm, np.ones(len(x)))
        put("D1 base", "all games", w, n=len(x), blind_over=rec_str(bw, bl), mean_cm=round(float(x.cm.mean()), 2), median_cm=float(x.cm.median()),
            skew=round(float(x.cm.skew()), 3), model_minus_line=round(float(x.edge.mean()), 2), model_minus_actual=round(float((x.model_total - x.total).mean()), 2),
            share_model_over=round(float((x.p_over_emp >= 0.5).mean()), 3))
    # D2 / D3 raw chance band, calibration of both chances on the over side
    bands = [0.50, 0.53, 0.55, 0.58, 0.62, 1.01]
    for col, sec in (("p_over_emp", "D2/D3 raw chance"), ("p_cal", "D3 calibrated chance")):
        for w, x in windows(x0[x0.wk17 & x0[col].notna()]):
            b = pd.cut(x[col], bands, right=False)
            for k, xx in x.groupby(b, observed=True):
                if not len(xx):
                    continue
                ww, ll = wl(xx.cm, np.ones(len(xx))); n = ww + ll; said = float(xx[col][xx.cm != 0].mean()); came = ww / max(1, n)
                z = (came - said) / np.sqrt(max(1e-9, said * (1 - said) / max(1, n)))
                put(sec, f"[{k.left:.2f}, {k.right:.2f})", w, n=n, over=rec_str(ww, ll), said=round(said, 3), came=round(came, 3), z=round(float(z), 2))
    # D4 model edge in points, over side
    eb = pd.cut(x0.edge, [0, 1, 2, 3, 4, 6, 99], right=False, labels=["0-1", "1-2", "2-3", "3-4", "4-6", "6+"])
    slice_table(x0, "D4 model edge (pts)", eb.astype(object), ["0-1", "1-2", "2-3", "3-4", "4-6", "6+"])
    # D5 line size
    lb = pd.cut(x0.total_line, [0, 40, 44, 47, 50, 99], right=False, labels=["<40", "40-43.5", "44-46.5", "47-49.5", "50+"]).astype(object)
    slice_table(x0, "D5 total line", lb, ["<40", "40-43.5", "44-46.5", "47-49.5", "50+"])
    # D6 week
    wb = pd.cut(x0.week, [0, 4, 8, 13, 17], labels=["1-4", "5-8", "9-13", "14-17"]).astype(object)
    slice_table(x0, "D6 week", wb, ["1-4", "5-8", "9-13", "14-17"])
    # D7 weather
    slice_table(x0, "D7 roof", pd.Series(np.where(x0.dome == 1, "dome", "outdoor"), index=x0.index), ["dome", "outdoor"])
    wf = x0.wind_fc.where(x0.dome != 1)
    slice_table(x0, "D7 forecast wind (2018+)", pd.cut(wf, [0, 5, 10, 15, 99], right=False, labels=["0-5", "5-10", "10-15", "15+"]).astype(object), ["0-5", "5-10", "10-15", "15+"])
    slice_table(x0, "D7 forecast rain (2018+)", pd.Series(np.where(x0.rain_fc >= 50, "50%+", np.where(x0.rain_fc.notna(), "under 50%", None)), index=x0.index), ["50%+", "under 50%"])
    # D8 pace, QB form, QB rating: terciles within season
    for col, sec in (("pace_sum", "D8 pace"), ("qbf_sum", "D8 QB form"), ("qbr_sum", "D8 QB rating")):
        t = x0.groupby("season")[col].transform(lambda s: pd.qcut(s.rank(method="first"), 3, labels=["low", "mid", "high"])).astype(object)
        slice_table(x0, sec, t, ["low", "mid", "high"])
    slice_table(x0, "D8 both QBs' form above 0", pd.Series(np.where((x0.h_qbf > 0) & (x0.a_qbf > 0), "both > 0", "not"), index=x0.index), ["both > 0", "not"])
    # D9 favourite size
    fb = pd.cut(x0.spread_line.abs(), [-0.1, 3.0, 6.5, 9.5, 99], labels=["0-3", "3.5-6.5", "7-9.5", "10+"]).astype(object)
    slice_table(x0, "D9 favourite size", fb, ["0-3", "3.5-6.5", "7-9.5", "10+"])
    # D10 prime time
    slice_table(x0, "D10 prime time", pd.Series(np.where(x0.prime, "prime", "not prime"), index=x0.index), ["prime", "not prime"])
    # D11 bias by model-total band and by line band (all regular-season games)
    for lab, col in (("D11 bias by model total", "model_total"), ("D11 bias by line", "total_line")):
        bb = pd.cut(x0[col], [0, 40, 44, 48, 52, 99], right=False, labels=["<40", "40-44", "44-48", "48-52", "52+"])
        for w, x in windows(x0):
            for k, xx in x.groupby(bb.reindex(x.index), observed=True):
                put(lab, k, w, n=len(xx), model_minus_actual=round(float((xx.model_total - xx.total).mean()), 2),
                    model_minus_line=round(float((xx.model_total - xx.total_line).mean()), 2), line_minus_actual=round(float((xx.total_line - xx.total).mean()), 2))
    # D12 key numbers: where finals land, and the over record on and off them
    x = x0[x0.wk17]; vc = x.total.value_counts(normalize=True).sort_index()
    for v in (30, 33, 37, 38, 40, 41, 43, 44, 45, 47, 48, 51, 54, 55):
        put("D12 final total share", int(v), "2015-25", share=round(float(vc.get(v, 0.0)), 4))
    for k in (37, 41, 43, 44, 47, 51):
        for off, lab_ in ((-0.5, f"{k - 0.5:g}"), (0.0, f"{k:g}"), (0.5, f"{k + 0.5:g}")):
            m = x.total_line == k + off; ww, ll = wl(x.cm, m)
            put("D12 line on a key total", f"{lab_} (key {k})", "2015-25", n=int(m.sum()), blind_over=rec_str(ww, ll),
                land_on_key=round(float((x.total[m] == k).mean()), 3) if m.any() else np.nan, model_over55=rec_str(*wl(x.cm, m & (x.p_over_emp >= 0.55))))


# ---------------------------------------------------------------- Part 2: rules
def rules(d) -> dict:
    o = lambda m: (m & d.wk17).fillna(False).astype(bool)
    pe, pc = d.p_over_emp, d.p_cal
    return {"O1 cal 55%+": o(pc >= 0.55), "O2 cal 58%+": o(pc >= 0.58), "O3 cal 60%+": o(pc >= 0.60), "O4 cal 62%+": o(pc >= 0.62),
            "O5 raw 60%+": o(pe >= 0.60), "O6 raw 65%+": o(pe >= 0.65), "O7 dome, raw 55%+": o((d.dome == 1) & (pe >= 0.55)),
            "O8 both QBs' form > 0, raw 55%+": o((d.h_qbf > 0) & (d.a_qbf > 0) & (pe >= 0.55)),
            "O9 line 41 or lower, raw 55%+": o((d.total_line <= 41) & (pe >= 0.55)), "O10 blind, line 40 or lower": o(d.total_line <= 40),
            "O11 blind, dome": o(d.dome == 1), "O12 model 4+ over the line": o(d.edge >= 4),
            "O13 outdoor, wind under 5, raw 55%+": o((d.dome != 1) & (d.wind_fc < 5) & (pe >= 0.55)),
            "O14 pace above earlier median, raw 55%+": o((d.pace_sum > d.pace_cut) & (pe >= 0.55))}


def shuffle_mask(m, seasons, rng):
    return G.shuffle_within_season(m.astype(float), seasons, rng) > 0.5


def test_rules(d):
    x = d[d.season.between(2015, 2025)].copy(); R = rules(x); rng = np.random.default_rng(SEED)
    seasons = x.season.values; cm = x.cm.values; elig = x.wk17.values
    live_tf = P.rule_mask(x, P.TOTAL_SHADOW["prob"], "under_prob").fillna(False).values
    live_wu = P.rule_mask(x, P.WIND_UNDER["mph"], "wind_under").fillna(False).values
    out = {}
    for name, m in R.items():
        m = m.values; row = {}
        for w, (lo, hi) in WIN.items():
            s = (seasons >= lo) & (seasons <= hi); ww, ll = wl(cm, m & s); row[w] = (ww, ll)
        tw, tl = wl(cm, m); real = units(tw, tl)
        # placebo: the rule's games shuffled among each season's weeks 1-17 games (its reading shuffled within season)
        gains = []
        for _ in range(NRULE):
            mm = np.zeros(len(m), dtype=bool); ie = np.flatnonzero(elig)
            mm[ie] = G.shuffle_within_season(m[ie].astype(float), seasons[ie], rng) > 0.5
            gains.append(units(*wl(cm, mm)))
        beat = int((real > np.asarray(gains)).sum())
        ok = all(row[w][0] + row[w][1] >= 20 and units(*row[w]) > 0 for w in WIN) and beat >= 190
        out[name] = {"rec": row, "total": (tw, tl), "units": real, "beat": beat, "pass": ok,
                     "share_tf": int((m & live_tf).sum()), "share_wu": int((m & live_wu).sum())}
        for w in WIN:
            put("Rules", name, w, record=rec_str(*row[w]), units=units(*row[w]))
        put("Rules", name, "2015-25", record=rec_str(tw, tl), units=real, placebo_beaten=f"{beat} of {NRULE}", passes=ok,
            same_game_as_totals_flag=out[name]["share_tf"], same_game_as_wind_under=out[name]["share_wu"])
    # family-wise: outcomes permuted within season among weeks 1-17 games, the best rule's units each draw
    ie = np.flatnonzero(elig); best_real = max(v["units"] for v in out.values()); Ms = {k: v.values[ie] for k, v in R.items()}
    cme, se = cm[ie], seasons[ie]; bests = []
    for _ in range(NFAM):
        c = G.shuffle_within_season(cme, se, rng)
        bests.append(max(units(*wl(c, m)) for m in Ms.values()))
    fam = float(np.mean(np.asarray(bests) >= best_real))
    put("Rules family-wise", "best of 14 rules", "2015-25", best_units=best_real, share_of_shuffles_as_good=round(fam, 4), draws=NFAM)
    return out, fam


def o9_checks(d):
    """Added after results (O9 was the one rule to pass): its neighbours, a stricter placebo (the chance shuffled only among
    low-total games, so it must beat blind low-total overs), by season, and its games shared with the wind under."""
    x = d[d.season.between(2015, 2025) & d.wk17].copy(); rng = np.random.default_rng(SEED + 9)
    for cut in (40, 41, 42, 43):
        for thr in (0.53, 0.55, 0.57):
            m = (x.total_line <= cut) & (x.p_over_emp >= thr)
            for w, (lo, hi) in WIN.items():
                put("O9 neighbours", f"line {cut} or lower, raw {100 * thr:.0f}%+", w, record=rec_str(*wl(x.cm, m & x.season.between(lo, hi))))
    low = x[x.total_line <= 41]; m = (low.p_over_emp >= 0.55).values; real = units(*wl(low.cm, m)); g = []
    for _ in range(NRULE):
        mm = G.shuffle_within_season(low.p_over_emp.values, low.season.values, rng) >= 0.55
        g.append(units(*wl(low.cm, mm)))
    put("O9 strict placebo", "chance shuffled among line-41-or-lower games", "2015-25", units=real, placebo_beaten=f"{int((real > np.asarray(g)).sum())} of {NRULE}",
        placebo_median=float(np.median(g)))
    o9 = (x.total_line <= 41) & (x.p_over_emp >= 0.55)
    for s in range(2015, 2026):
        put("O9 by season", s, str(s), record=rec_str(*wl(x.cm, o9 & (x.season == s))))
    wu = P.rule_mask(x, P.WIND_UNDER["mph"], "wind_under").fillna(False)
    put("O9 shared with wind under", "O9 games the wind under bets under", "2015-25", over_record=rec_str(*wl(x.cm, o9 & wu)))
    put("O9 shared with wind under", "O9 without them", "2015-25", over_record=rec_str(*wl(x.cm, o9 & ~wu)))


# ---------------------------------------------------------------- Part 3: model changes
BANDS = [-np.inf, 40, 44, 48, 52, np.inf]


def correction(hist_mt, hist_miss, mt, kind):
    """The amount added to totals mt, learned from earlier seasons' (model total, miss = actual - model total)."""
    if len(hist_mt) < 200:
        return np.zeros(len(mt))
    if kind == "M1":   # actual = a + b x model total
        b, a = np.polyfit(hist_mt, hist_mt + hist_miss, 1)
        return a + b * mt - mt
    bh = np.searchsorted(BANDS, hist_mt, side="right") - 1; bt = np.searchsorted(BANDS, mt, side="right") - 1
    s = pd.Series(hist_miss).groupby(bh).agg(["sum", "size"])
    return np.array([s["sum"].get(k, 0.0) / (s["size"].get(k, 0) + 100.0) for k in bt])


def corrected(p, kind, rng=None):
    """p with model_total corrected season by season (earlier seasons' walk-forward misses only); rng shuffles those misses
    within season (the placebo)."""
    q = p.copy(); act = q.game_id.map(GAMES.set_index("game_id").total)
    reg = (q.game_type == "REG").values & act.notna().values
    mt0 = q.model_total.values.astype(float); miss = act.values - mt0; amt = np.zeros(len(q))
    if rng is not None:
        miss = miss.copy(); miss[reg] = G.shuffle_within_season(miss[reg], q.season.values[reg], rng)
    for s in range(2015, 2026):
        h = reg & (q.season.values < s); t = q.season.values == s
        amt[t] = correction(mt0[h], miss[h], mt0[t], kind)
    q["model_total"] = mt0 + amt
    q["home_exp"] = (q.model_total + q.model_spread) / 2; q["away_exp"] = (q.model_total - q.model_spread) / 2
    return q, amt


def score(p, tres, reprice=True) -> dict:
    d = B.join(p, GAMES); d = d[(d.game_type == "REG") & d.season.between(2015, 2025)].copy()
    if reprice:
        d["p_over_emp"] = [p_emp(mt, tl, tres.get((int(s), int(w)))) for mt, tl, s, w in zip(d.model_total, d.total_line, d.season, d.week)]
    out = {}
    for w, (lo, hi) in WIN.items():
        x = d[d.season.between(lo, hi)]
        y = x[x.total_line.notna() & (x.total != x.total_line) & x.p_over_emp.notna()]
        q = y.p_over_emp.clip(0.02, 0.98); ov = (y.total > y.total_line).astype(float)
        out[w] = {"team": float(np.r_[x.home_err.abs(), x.away_err.abs()].mean()), "total": float(x.total_err.abs().mean()),
                  "logloss": float(-(ov * np.log(q) + (1 - ov) * np.log(1 - q)).mean()),
                  "spread": P.record(x, P.rule_mask(x, P.SPREAD_EDGE)),
                  "totals": P.record(x, P.rule_mask(x, P.TOTAL_SHADOW["prob"], "under_prob"), "under_prob"),
                  "wind": P.record(x, P.rule_mask(x, P.WIND_UNDER["mph"], "wind_under"), "wind_under")}
    return out


def fast_miss(p) -> dict:
    """Team points and total miss per window (placebo draws)."""
    a = p.game_id.map(GAMES.set_index("game_id").total); hs = p.game_id.map(GAMES.set_index("game_id").home_score); as_ = p.game_id.map(GAMES.set_index("game_id").away_score)
    keep = (p.game_type == "REG").values & a.notna().values; out = {}
    for w, (lo, hi) in WIN.items():
        m = keep & p.season.between(lo, hi).values
        out[w] = {"team": float(np.r_[np.abs(p.home_exp.values[m] - hs.values[m]), np.abs(p.away_exp.values[m] - as_.values[m])].mean()),
                  "total": float(np.abs(p.model_total.values[m] - a.values[m]).mean())}
    return out


def models(p, tres):
    b = score(p, tres, reprice=False); res = {}
    chk = score(p, tres, reprice=True)   # the re-pricing reproduces the live over chance exactly
    assert all(chk[w]["totals"] == b[w]["totals"] and abs(chk[w]["logloss"] - b[w]["logloss"]) < 1e-9 for w in WIN), (chk, b)
    put("Model", "base (live)", "-", **{f"{k}_{w}": (round(v[k], 4) if isinstance(v[k], float) else f"{v[k][0]}-{v[k][1]}") for w, v in b.items() for k in v})
    for kind in ("M1", "M2"):
        q, amt = corrected(p, kind); n = score(q, tres); rng = np.random.default_rng(SEED + (1 if kind == "M1" else 2))
        bm = fast_miss(p); plc = {"team": {w: [] for w in WIN}, "total": {w: [] for w in WIN}}
        for _ in range(NMOD):
            qq, _ = corrected(p, kind, rng); fm = fast_miss(qq)
            for k in plc:
                for w in WIN:
                    plc[k][w].append(bm[w][k] - fm[w][k])
        tables = {}
        for key in ("total", "team"):
            rows = G.gate({w: (b[w][key], n[w][key]) for w in WIN},
                          {w: {"spread flag": (b[w]["spread"], n[w]["spread"]), "totals flag": (b[w]["totals"], n[w]["totals"]),
                               "wind under": (b[w]["wind"], n[w]["wind"])} for w in WIN}, plc[key],
                          calibration={w: (b[w]["logloss"], n[w]["logloss"]) for w in WIN})
            tables[key] = rows
        res[kind] = {"new": n, "tables": tables, "amt": amt, "pass": all(G.passes(t) for t in tables.values())}
        put("Model", kind, "-", **{f"{k}_{w}": (round(v[k], 4) if isinstance(v[k], float) else f"{v[k][0]}-{v[k][1]}") for w, v in n.items() for k in v},
            mean_amount=round(float(np.mean(amt[p.season.between(2015, 2025).values])), 3), passes=res[kind]["pass"])
    return b, res


# ---------------------------------------------------------------- write-up
def md_table(sec, cols, keep=None):
    t = pd.DataFrame([r for r in OUTROWS if r["section"] == sec])
    if keep is not None:
        t = t[t.window.isin(keep)]
    if t.empty:
        return ""
    L = ["| " + " | ".join(["slice", "window"] + cols) + " |", "|" + "---|" * (len(cols) + 2)]
    L += ["| " + " | ".join([str(r["slice"]), str(r["window"])] + [str(r.get(c, "")) for c in cols]) + " |" for _, r in t.iterrows()]
    return "\n".join(L)


def main():
    p, tres = base("--fresh" in sys.argv)
    d = frame(p, tres)
    diagnose(d)
    rr, fam = test_rules(d)
    o9_checks(d)
    b, res = models(p, tres)
    pd.DataFrame(OUTROWS).to_csv(REP / "overs_deep.csv", index=False)
    L = ["# Overs, in depth: results (generated by experiments/overs_deep.py)", ""]
    for sec, cols in [("D1 base", ["n", "blind_over", "mean_cm", "median_cm", "skew", "model_minus_line", "model_minus_actual", "share_model_over"]),
                      ("D2/D3 raw chance", ["n", "over", "said", "came", "z"]), ("D3 calibrated chance", ["n", "over", "said", "came", "z"])]:
        L += [f"## {sec}", "", md_table(sec, cols), ""]
    for sec in ["D4 model edge (pts)", "D5 total line", "D6 week", "D7 roof", "D7 forecast wind (2018+)", "D7 forecast rain (2018+)", "D8 pace",
                "D8 QB form", "D8 QB rating", "D8 both QBs' form above 0", "D9 favourite size", "D10 prime time"]:
        L += [f"## {sec}", "", md_table(sec, ["n", "blind_over", "model_over55", "mean_cm", "model_minus_actual"]), ""]
    for sec in ["D11 bias by model total", "D11 bias by line"]:
        L += [f"## {sec}", "", md_table(sec, ["n", "model_minus_actual", "model_minus_line", "line_minus_actual"]), ""]
    L += ["## D12 final total share", "", md_table("D12 final total share", ["share"]), "", "## D12 line on a key total", "",
          md_table("D12 line on a key total", ["n", "blind_over", "land_on_key", "model_over55"]), ""]
    L += ["## Rules", "", "| Rule | 2015-18 | 2019-22 | 2023-25 | 2015-25 | placebo beaten | passes | shares a game with the totals flag / wind under |", "|---|---|---|---|---|---|---|---|"]
    L += [f"| {k} | {rec_str(*v['rec']['2015-18'])} | {rec_str(*v['rec']['2019-22'])} | {rec_str(*v['rec']['2023-25'])} | {rec_str(*v['total'])} | {v['beat']} of {NRULE} | {'yes' if v['pass'] else 'no'} | {v['share_tf']} / {v['share_wu']} |" for k, v in rr.items()]
    L += ["", f"Family-wise: the best of the 14 rules made {max(v['units'] for v in rr.values()):+.1f}u; {100 * fam:.1f}% of {NFAM} within-season outcome shuffles had a best rule as good.", ""]
    L += ["## O9 checks (added after results)", "", md_table("O9 neighbours", ["record"]), "", md_table("O9 strict placebo", ["units", "placebo_beaten", "placebo_median"]), "",
          md_table("O9 by season", ["record"]), "", md_table("O9 shared with wind under", ["over_record"]), ""]
    for kind, r in res.items():
        for key, rows in r["tables"].items():
            L += [f"## {kind}, gate on {key} miss", "", G.markdown(rows), ""]
    L += ["## Model records", "", md_table("Model", [c for c in pd.DataFrame([r for r in OUTROWS if r["section"] == "Model"]).columns if c not in ("section", "slice", "window")]), ""]
    (REP / "overs_deep_results.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
