"""Tie-out: the same number must read the same everywhere it appears. Recomputes the headline records from the
prediction table and compares them with the README block, the threshold sweep, the docs' threshold table, the
week's picks file, the tracker, and the page's data files. Writes reports/tie_check.md and exits non-zero on any
mismatch, so a weekly run shows it as a failed step instead of publishing numbers that disagree.

Usage: python -m nflmodel.tie_check            sources only (README, docs, sweep, picks, tracker, prediction table)
       python -m nflmodel.tie_check --page     also the page's data files (after the export)"""
from __future__ import annotations
import json, re, sys
import numpy as np, pandas as pd
from . import backtest as B, model as M, picks as P, ratings as R
from .features import OUT, ROOT
REP = ROOT / "reports"; WEB = ROOT / "web" / "data"; TR = ROOT / "data" / "tracker"


def _rec(x: pd.DataFrame, cut: float) -> str:
    e = x.model_spread - x.spread_line; cm = x.home_score - x.away_score - x.spread_line
    f = (e.abs() >= cut) & (cm != 0); w = int((((e > 0) & (cm > 0)) | ((e < 0) & (cm < 0)))[f].sum())
    return f"{w}-{int(f.sum()) - w}"


def _js(name: str):
    s = (WEB / name).read_text(); return json.loads(s[s.index("=") + 1:].rstrip().rstrip(";"))


def check_sources() -> list[tuple[str, str, str, bool]]:
    rows = []
    def tie(what, a, b): rows.append((what, str(a), str(b), str(a) == str(b)))
    p = pd.read_parquet(OUT / "pred_v3.parquet"); g = pd.read_parquet(OUT / "games.parquet")
    d = B.join(p, g); d = d[(d.game_type == "REG") & d.home_score.notna() & d.spread_line.notna()]
    v = d[d.season.between(2023, 2025)]; a = d[d.season.between(2019, 2025)]; a17 = a[a.week < 18]
    se = P.SPREAD_EDGE
    # README block
    readme = (ROOT / "README.md").read_text()
    m = re.search(rf"\| Spreads at {se:g}\+ pt edge \(the flag\) \| (\d+-\d+) \(2019 to 2025: (\d+-\d+); (\d+-\d+) outside Week 18\)", readme)
    tie("README flag record, held out", m.group(1) if m else "missing", _rec(v, se))
    tie("README flag record, 2019 to 2025", m.group(2) if m else "missing", _rec(a, se))
    tie("README flag record, outside Week 18", m.group(3) if m else "missing", _rec(a17, se))
    m = re.search(r"\| Margin miss \| ([\d.]+) \|", readme)
    tie("README held-out margin miss", m.group(1) if m else "missing", f"{(v.home_score - v.away_score - v.model_spread).abs().mean():.2f}")
    # threshold sweep csv (weeks 1 to 17)
    sw = REP / "threshold_sweep.csv"
    if sw.exists():
        t = pd.read_csv(sw); t = t[(t.market == "spread") & (t.cut == se)].set_index("window")
        for w, sub in [("2019-22", d[d.season.between(2019, 2022) & (d.week < 18)]), ("2023-25", d[d.season.between(2023, 2025) & (d.week < 18)])]:
            tie(f"threshold sweep, cut {se:g}, {w}", f"{int(t.loc[w, 'wins'])}-{int(t.loc[w, 'losses'])}", _rec(sub, se))
        # docs section 9 row for the live cut
        doc = (ROOT / "docs" / "how_it_works.md").read_text()
        m = re.search(rf"\n\| {se:g} \| (\d+-\d+), [\d.]+% \| (\d+-\d+), [\d.]+% \|", doc)
        tie(f"docs section 9 row, cut {se:g}, 2019-22", m.group(1) if m else "missing", f"{int(t.loc['2019-22', 'wins'])}-{int(t.loc['2019-22', 'losses'])}")
        tie(f"docs section 9 row, cut {se:g}, 2023-25", m.group(2) if m else "missing", f"{int(t.loc['2023-25', 'wins'])}-{int(t.loc['2023-25', 'losses'])}")
    # docs and picks header quote the live cut and the input count
    doc = (ROOT / "docs" / "how_it_works.md").read_text()
    tie("docs: live cut named in section 9", f"the flag is {se:g}" in doc, True)
    tie("docs: QB replacement level", f"shrunk toward {R.DEFAULT['qb_prior']:g}" in doc, True)
    tie("model inputs counted", len(M.FEATS), 22)
    tie("docs: input count", "twenty-two inputs" in doc or "Twenty-two inputs" in doc, True)
    # the rule table (flag and shadows on the three windows) in docs section 9 and in the track record
    rr = P.rule_records(d).set_index("rule")
    tr = (REP / "track_record.md").read_text() if (REP / "track_record.md").exists() else ""
    for who, r in rr.iterrows():
        want = f"{r['2015-18']} | {r['2019-22']} | {r['2023-25']}"
        m = re.search(rf"\n\| {re.escape(r['label'])} \| (\d+-\d+) \| (\d+-\d+) \| (\d+-\d+) \|", doc)
        tie(f"docs section 9 rule table: {r['label']}", " | ".join(m.groups()) if m else "missing", want)
        if tr:
            lab = f"{se:g}+ edge (the flag, bet)" if who == "model" else f"shadow: {r['label']}"   # the track record's row labels
            m = re.search(rf"\| {re.escape(lab)} \|.*\| (\d+-\d+) \| (\d+-\d+) \| (\d+-\d+) \|", tr)
            tie(f"track record backtest columns: {r['label']}", " | ".join(m.groups()) if m else "missing", want)
    # docs section 14 by-week table against the prediction table (2015 to 2025)
    bw = B.by_week(B.join(p, g)[lambda x: x.spread_line.notna()], se)
    for _, r in bw.iterrows():
        m = re.search(rf"\n\| {r.weeks} \| (\d+) \| ([+-]\d\.\d\d) \| (\d+)% \| (\d+-\d+) \((\d+)%\) \|", doc)
        tie(f"docs by-week row: weeks {r.weeks}", " ".join(m.groups()) if m else "missing", f"{r['games']} {r['gap']:+.2f} {r['ats_pct']} {r['flags']} {r['flag_pct']}")
    # scheme profiles: built as of the current week, every team present
    if (OUT / "scheme_profiles.json").exists():
        sp = json.loads((OUT / "scheme_profiles.json").read_text())
        from . import lines as LN
        _s, _w = LN.current_week(g)
        tie("scheme profiles as of the current week", f"{sp['season']} {sp['week']}", f"{_s} {_w}")
        tie("scheme profiles cover 32 teams", len(sp["teams"]), 32)
    if (OUT / "props.json").exists():
        pj = json.loads((OUT / "props.json").read_text()); from . import lines as LN2; _s2, _w2 = LN2.current_week(g)
        tie("props projections are for the current week", f"{pj['season']} {pj['week']}", f"{_s2} {_w2}")
        pf = REP / f"props_{_s2}_wk{_w2}.csv"
        b3, b4 = REP / "props_backtest3.csv", REP / "props_backtest4.csv"
        if b3.exists() and b4.exists():
            import ast as _ast
            bt = pd.read_csv(b3); a85 = bt[bt.variant == "A85B_med"].set_index("stat"); r4 = pd.read_csv(b4)
            pick = {"rec_yards": "base", "rush_yards": "base", "pass_yards": "combo"}
            tie("props backtest errors on the page = props_backtest4.csv (base for receiving and rushing, combo for passing)", {k: [float(r4[(r4.stat == k) & (r4.variant == v)]["mae_2019-22"].iloc[0]), float(r4[(r4.stat == k) & (r4.variant == v)]["mae_2023-25"].iloc[0])] for k, v in pick.items()}, {k: [float(v[0]), float(v[1])] for k, v in pj["backtest"].items() if k != "note"})
            tie("props round-4 base = round-3 adopted variant (receiving, rushing)", {k: [float(r4[(r4.stat == k) & (r4.variant == "base")]["mae_2019-22"].iloc[0]), float(r4[(r4.stat == k) & (r4.variant == "base")]["mae_2023-25"].iloc[0])] for k in ["rec_yards", "rush_yards"]}, {k: [float(a85.loc[k, "mae_2019-22"]), float(a85.loc[k, "mae_2023-25"])] for k in ["rec_yards", "rush_yards"]})
            tie("props median factors = props_backtest3.csv", {k: float(a85.loc[f"{k}_yards", "median_factor_A85B"]) for k in ["rec", "rush", "pass"]}, {k: float(v) for k, v in pj["med"].items()})
            gs = bt[bt.stat == "game_script"].set_index("variant")
            tie("props game-script line = props_backtest3.csv", {"total": float(gs.loc["league_total", "mae_2019-22"]), **{k: [float(gs.loc[c, "mae_2019-22"]), float(gs.loc[c, "mae_2023-25"]), float(gs.loc[c, "n_2019-22"])] for k, c in [("rec", "tp"), ("rush", "tr"), ("pass", "tdb")]}}, {"total": float(pj["gs_total"]), **{k: [float(x) for x in v] for k, v in pj["gs"].items()}})
            fitted = _ast.literal_eval(r4[r4.stat == "pass_yards"].fitted.iloc[0])
            tie("props passing wind factor = props_backtest4.csv", round(float(fitted["wind_c"]), 4), round(float(pj["wind_c"]["pass"]), 4))
        if (WEB / "props_backtest.js").exists():
            pb = _js("props_backtest.js")
            tie("props backtest rounds on the page = the five CSVs (rows)", [len(pd.read_csv(REP / f)) for f in ["props_backtest.csv", "props_backtest2.csv", "props_backtest3.csv", "props_backtest4.csv", "props_backtest5.csv"]], [r["n_rows"] for r in pb["rounds"]])
            tie("props by-season tables on the page = reports (rows)", [len(pd.read_csv(REP / f)) for f in ["props_by_season.csv", "props_by_position.csv", "props_by_bucket.csv"]], [len(pb["by_season"]), len(pb["by_position"]), len(pb["by_bucket"])])
            bs = pd.read_csv(REP / "props_by_season.csv"); bs = bs[bs.season.isin(["2019-22", "2023-25"])].set_index(["stat", "season"])
            tie("props by-season run of the adopted rule = the rounds' adopted errors (yards, both windows)", {k: [float(bs.loc[(k, "2019-22"), "mae"]), float(bs.loc[(k, "2023-25"), "mae"])] for k in ["rec_yards", "rush_yards", "pass_yards"]}, {k: [float(v[0]), float(v[1])] for k, v in pj["backtest"].items() if k != "note"})
        tie("props file = props page data (projections: 3 per receiver, 2 per rusher, 3 per QB)", (len(pd.read_csv(pf)) if pf.exists() else "missing"), sum(3 * len([r for r in side["receivers"] if not r["out"]]) + 2 * len([r for r in side["rushers"] if not r["out"]]) + 3 * len([r for r in side["qb"][:1] if not r["out"]]) for gm in pj["games"].values() for side in gm.values()))
        b5 = REP / "props_backtest5.csv"
        if b5.exists():
            r5 = pd.read_csv(b5); pick5 = {"rec_catches": ("rec_catch", "catch_K25_med", "mae"), "rec_td_ll": ("rec_td", "td_K200_gs", "ll"), "rush_td_ll": ("rush_td", "td_K200", "ll"), "pass_td_ll": ("pass_td", "td_K400_gs", "ll"), "pass_int_ll": ("pass_int", "int_league", "ll")}
            tie("props count backtests on the page = props_backtest5.csv (adopted variants)", {k: [float(r5[(r5.stat == st) & (r5.variant == v)][f"{m}_2019-22"].iloc[0]), float(r5[(r5.stat == st) & (r5.variant == v)][f"{m}_2023-25"].iloc[0])] for k, (st, v, m) in pick5.items()}, {k: [float(v[0]), float(v[1])] for k, v in pj["backtest_counts"].items()})
            fitted5 = {st: r5[r5.stat == st].fitted.dropna().iloc[0] for st in ["rec_catch", "rec_td", "pass_td"]}
            tie("props count constants = props_backtest5.csv", fitted5, {"rec_catch": f"K {pj['k_catch']:.0f}, median factor {pj['med_catch']:.2f}", "rec_td": f"K {pj['k_td']['rec']:.0f}, margin coefficient {pj['td_margin']['rec']:.3f} per point", "pass_td": f"K {pj['k_td']['pass']:.0f}, margin coefficient {pj['td_margin']['pass']:.3f} per point"})
    # the week's picks file against the tracker's unplayed model picks
    from . import lines as LN
    season, week = LN.current_week(g)
    pk_f = REP / f"picks_{season}_wk{week}.csv"
    if pk_f.exists() and (TR / "model_picks.csv").exists():
        pk = pd.read_csv(pk_f); mp = pd.read_csv(TR / "model_picks.csv")
        flagged = pk[pk.bet.fillna("") != ""]
        cur = mp[(mp.season == season) & (mp.week == week)]
        tie("picks file flags = tracker rows (games)", sorted(flagged.game_id), sorted(cur.game_id))
        tie("picks file flags = tracker rows (bets)", sorted(flagged.bet), sorted(cur.bet))
        if "stake_pct" in flagged.columns and "stake_pct" in cur.columns:
            tie("picks file stakes = tracker stakes", sorted(flagged.stake_pct.round(2)), sorted(cur.stake_pct.round(2)))
        md = (REP / f"picks_{season}_wk{week}.md").read_text() if (REP / f"picks_{season}_wk{week}.md").exists() else ""
        tie("picks markdown names the live cut", f"edge is {se:g}+" in md, True)
        m = re.search(r"that cut is (\d+-\d+) on the tuning window and (\d+-\d+) held out \(weeks 1 to 17\).*?and (\d+-\d+) on the untouched 2015 to 2018 window", md)
        tie("picks markdown header records (tuning, held out, untouched)", " ".join(m.groups()) if m else "missing", f"{rr.loc['model', '2019-22']} {rr.loc['model', '2023-25']} {rr.loc['model', '2015-18']}")
    return rows


def check_page() -> list[tuple[str, str, str, bool]]:
    rows = []
    def tie(what, a, b): rows.append((what, str(a), str(b), str(a) == str(b)))
    p = pd.read_parquet(OUT / "pred_v3.parquet").set_index("game_id")
    bk = _js("backtest.js"); b = pd.DataFrame(bk["rows"], columns=bk["cols"]).set_index("game_id")
    common = b.index.intersection(p.index)
    tie("page backtest file: games", len(b), len(p[p.index.isin(b.index)]))
    tie("page backtest file: model spread equals the prediction table", round(float((b.loc[common, "model_spread"] - p.loc[common, "model_spread"]).abs().max()), 3), 0.0)
    tie("page backtest file: model total equals the prediction table", round(float((b.loc[common, "model_total"] - p.loc[common, "model_total"]).abs().max()), 3), 0.0)
    meta = _js("meta.js")
    tie("page inputs = model inputs", meta.get("feats"), M.FEATS)
    wk = _js("week.js")
    tie("page flag threshold = picks threshold", wk.get("spread_edge"), P.SPREAD_EDGE)
    g = pd.read_parquet(OUT / "games.parquet")
    from . import lines as LN
    season, week = LN.current_week(g)
    pk_f = REP / f"picks_{season}_wk{week}.csv"
    if pk_f.exists() and "games" in wk:
        pk = pd.read_csv(pk_f).set_index("game_id")
        pg = {x["game_id"]: x for x in wk["games"]}
        tie("page week = picks file (games)", sorted(pg), sorted(pk.index))
        tie("page week = picks file (bets)", sorted((x.get("bet") or "") for x in pg.values()), sorted(pk.bet.fillna("")))
        tie("page week = picks file (model spread)", round(float(max(abs((pg[k]["model_spread"] or 0) - pk.loc[k, "model_spread"]) for k in pg if k in pk.index)), 3), 0.0)
    tr = _js("track.js"); mp = pd.read_csv(TR / "model_picks.csv") if (TR / "model_picks.csv").exists() else pd.DataFrame()
    if len(mp):
        cur = mp[(mp.season == season) & (mp.week == week)]
        tie("page live table = tracker (pending model rows)", sorted(x["bet"] for x in tr if x.get("who") == "model" and x.get("season") == season and x.get("week") == week), sorted(cur.bet))
    rk = _js("rankings.js")
    tie("page rankings: QB replacement level", rk.get("params", {}).get("qb_prior"), R.DEFAULT["qb_prior"])
    return rows


def main(page: bool = False) -> bool:
    rows = check_sources() + (check_page() if page else [])
    ok = all(r[3] for r in rows)
    L = [f"# Tie-out ({'sources and page' if page else 'sources'}), {pd.Timestamp.now('UTC').strftime('%Y-%m-%d %H:%M UTC')}", "",
         "The same number must read the same everywhere it appears. Each row: what was compared, what it says, what it should say.", "",
         "| Check | Reads | Should read | Ties |", "|---|---|---|---|"] + [f"| {w} | {a[:80]} | {b[:80]} | {'yes' if t else 'NO'} |" for w, a, b, t in rows] + \
        ["", f"Result: {'PASS' if ok else 'FAIL'} ({sum(1 for r in rows if r[3])} of {len(rows)} tie)"]
    (REP / "tie_check.md").write_text("\n".join(L) + "\n"); print("\n".join(L))
    return ok


if __name__ == "__main__":
    sys.exit(0 if main("--page" in sys.argv) else 1)
