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
REP = ROOT / "reports"; LNS = ROOT / "data" / "lines"; RAW = ROOT / "data" / "raw"
WEB = ROOT / "web" / "data"; TR = ROOT / "data" / "tracker"


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
            r6 = pd.read_csv(REP / "props_backtest6.csv"); r10 = pd.read_csv(REP / "props_backtest10.csv"); pick = {"rec_yards": (r10, "rec_fade", "both_0.5"), "rush_yards": (r10, "rush_fade", "season_0.25_team_0.5"), "pass_yards": (r6, "pass_yards", "yds_recon50")}
            _bs = pd.read_csv(REP / "props_by_season.csv").set_index(["stat", "season"])
            tie("props backtest errors on the page = props_by_season.csv (the adopted rule, walk-forward, league averages as of each game)", {k: [float(_bs.loc[(k, "2019-22"), "mae"]), float(_bs.loc[(k, "2023-25"), "mae"])] for k in ["rec_yards", "rush_yards", "pass_yards"]}, {k: [float(v[0]), float(v[1])] for k, v in pj["backtest"].items() if k != "note"})
            tie("props fade factors on the page = props_backtest10.csv (fitted)", {k: [float(x) for x in re.findall(r"season factor ([\d.]+), team-change factor ([\d.]+)", r10[(r10.stat == st) & (r10.variant == v)]["fitted"].iloc[0])[0]] for k, (r, st, v) in pick.items() if k != "pass_yards"}, {k + "_yards": list(v) for k, v in pj["fade"].items()})
            a6 = {k: [float(r6[(r6.stat == k) & (r6.variant == "yds_vegas")]["mae_2019-22"].iloc[0]), float(r6[(r6.stat == k) & (r6.variant == "yds_vegas")]["mae_2023-25"].iloc[0])] for k in ["rec_yards", "rush_yards", "pass_yards"]}
            a4 = {k: [float(r4[(r4.stat == k) & (r4.variant == v)]["mae_2019-22"].iloc[0]), float(r4[(r4.stat == k) & (r4.variant == v)]["mae_2023-25"].iloc[0])] for k, v in {"rec_yards": "base", "rush_yards": "base", "pass_yards": "combo"}.items()}
            rows.append(("props round-6 baseline = round-4 adopted errors (round 6 keeps three decimals; within 0.006)", str(a6), str(a4), all(abs(a6[k][i] - a4[k][i]) <= 0.006 for k in a6 for i in (0, 1))))
            _tf = {k: {v: [float(r6[(r6.stat == f"{k}_team_fit") & (r6.variant == v)]["mae_2019-22"].iloc[0]), float(r6[(r6.stat == f"{k}_team_fit") & (r6.variant == v)]["mae_2023-25"].iloc[0])] for v in ["td", "yds"]} for k in ["rec", "rush", "pass"]}
            _ro = pd.read_csv(REP / "props_official.csv") if (REP / "props_official.csv").exists() else None   # passing yards refit on the official numbers, 24 Sep 2026
            if _ro is not None:
                _x = _ro[(_ro.stat == "pass_yards") & (_ro.variant == "refit on the official numbers")].iloc[0]; _tf["pass"]["yds"] = [float(v) for v in _x.team_fit.split(" x ")[0].split(" + ")]
            tie("props team fit constants = props_backtest6.csv (passing yards: props_official.csv)", _tf, {k: {v: [float(x) for x in pj["team_fit"][k][v]] for v in ["td", "yds"]} for k in ["rec", "rush", "pass"]})
            tie("props round-4 base = round-3 adopted variant (receiving, rushing)", {k: [float(r4[(r4.stat == k) & (r4.variant == "base")]["mae_2019-22"].iloc[0]), float(r4[(r4.stat == k) & (r4.variant == "base")]["mae_2023-25"].iloc[0])] for k in ["rec_yards", "rush_yards"]}, {k: [float(a85.loc[k, "mae_2019-22"]), float(a85.loc[k, "mae_2023-25"])] for k in ["rec_yards", "rush_yards"]})
            r11 = pd.read_csv(REP / "props_backtest11.csv"); _rf = lambda st: float(r11[(r11.stat == st) & (r11.variant == "refit_2017_18")].factors.iloc[0])
            _mp = float(_ro[(_ro.stat == "pass_yards") & (_ro.variant == "refit on the official numbers")].med.iloc[0]) if _ro is not None else _rf("pass_yards")
            tie("props median factors = props_backtest3.csv (rushing), props_backtest11.csv (receiving) and props_official.csv (passing)", {"rec": _rf("rec_yards"), "rush": float(a85.loc["rush_yards", "median_factor_A85B"]), "pass": _mp}, {k: float(v) for k, v in pj["med"].items()})
            tie("props receptions factor = props_backtest11.csv refit row", _rf("rec_catches"), float(pj["med_catch"]))
            gs = bt[bt.stat == "game_script"].set_index("variant")
            tie("props game-script line = props_backtest3.csv", {"total": float(gs.loc["league_total", "mae_2019-22"]), **{k: [float(gs.loc[c, "mae_2019-22"]), float(gs.loc[c, "mae_2023-25"]), float(gs.loc[c, "n_2019-22"])] for k, c in [("rec", "tp"), ("rush", "tr"), ("pass", "tdb")]}}, {"total": float(pj["gs_total"]), **{k: [float(x) for x in v] for k, v in pj["gs"].items()}})
            fitted = _ast.literal_eval(r4[r4.stat == "pass_yards"].fitted.iloc[0])
            tie("props passing wind factor = props_backtest4.csv", round(float(fitted["wind_c"]), 4), round(float(pj["wind_c"]["pass"]), 4))
        if (WEB / "props_backtest.js").exists():
            pb = _js("props_backtest.js")
            tie("props backtest rounds on the page = the five CSVs (rows)", [len(pd.read_csv(REP / f)) for f in ["props_backtest.csv", "props_backtest2.csv", "props_backtest3.csv", "props_backtest4.csv", "props_backtest5.csv", "props_backtest6.csv", "props_backtest7.csv", "props_backtest8.csv", "props_backtest9.csv", "props_backtest10.csv"]], [r["n_rows"] for r in pb["rounds"]])
            if (REP / "props_vs_market_backtest.csv").exists():
                tie("props market backtest on the page = report (rows)", len(pd.read_csv(REP / "props_vs_market_backtest.csv")), len(pb["market_backtest"]))
            tie("props by-season tables on the page = reports (rows)", [len(pd.read_csv(REP / f)) for f in ["props_by_season.csv", "props_by_position.csv", "props_by_bucket.csv"]], [len(pb["by_season"]), len(pb["by_position"]), len(pb["by_bucket"])])
            bs = pd.read_csv(REP / "props_by_season.csv"); bs = bs[bs.season.isin(["2019-22", "2023-25"])].set_index(["stat", "season"])
            b1 = {k: [float(bs.loc[(k, "2019-22"), "mae"]), float(bs.loc[(k, "2023-25"), "mae"])] for k in ["rec_yards", "rush_yards", "pass_yards"]}; b2 = {k: [float(v[0]), float(v[1])] for k, v in pj["backtest"].items() if k != "note"}
            # passing: the constants last set by experiments/props_official.py (24 Sep 2026); receiving and rushing: round 13 (injury report and snap trend, 25 Sep 2026)
            ro = pd.read_csv(REP / "props_official.csv"); r13 = pd.read_csv(REP / "props_backtest13.csv")
            _src = {"rec_yards": (r13, "D_all (A_injury, B_snap_w0.25)"), "rush_yards": (r13, "D_all (A_injury, B_snap_w0.25)"), "pass_yards": (ro, "refit on the official numbers")}
            b2 = {k: [float(t[(t.stat == k) & (t.variant == v)]["mae_2019-22"].iloc[0]), float(t[(t.stat == k) & (t.variant == v)]["mae_2023-25"].iloc[0])] for k, (t, v) in _src.items()}
            rows.append(("props by-season run = the adopted rule's rows in the round that set it (yards, both windows; within 0.006)", str(b1), str(b2), all(abs(b1[k][i] - b2[k][i]) <= 0.006 for k in b1 for i in (0, 1))))
        if (TR / "props_vs_market.csv").exists():
            vm = pd.read_csv(TR / "props_vs_market.csv"); vm = vm[vm.side != "none"]
            tie("props graded against the market: page record = tracker file", {k: [int((g.result == "win").sum()), int((g.result == "loss").sum())] for k, g in vm.groupby("stat")}, {x["stat"]: [x["wins"], x["losses"]] for x in pj.get("market", []) if x["edge"] == "all"})
        tie("props file = props page data (projections: 5 per receiver, 5 per rusher, 7 per QB, 3 per defender, 2 per kicker)", (len(pd.read_csv(pf)) if pf.exists() else "missing"), sum(5 * len([r for r in side["receivers"] if not r["out"]]) + 5 * len([r for r in side["rushers"] if not r["out"]]) + 7 * len([r for r in side["qb"][:1] if not r["out"]]) + 3 * len([r for r in side.get("defenders", []) if not r["out"]]) + 2 * len([r for r in side.get("kicker", []) if not r["out"]]) for gm in pj["games"].values() for side in gm.values()))
        b7 = REP / "props_backtest7.csv"
        if b7.exists():
            r7 = pd.read_csv(b7)
            tie("props defender backtests on the page = props_backtest7.csv (adopted variants)", {"def_tackles": [float(r7[(r7.stat == "def_tackles") & (r7.variant == "tk_85gs_med")]["mae_2019-22"].iloc[0]), float(r7[(r7.stat == "def_tackles") & (r7.variant == "tk_85gs_med")]["mae_2023-25"].iloc[0])], "def_sacks_ll": [float(r7[(r7.stat == "def_sacks") & (r7.variant == "sk_K300")]["ll_2019-22"].iloc[0]), float(r7[(r7.stat == "def_sacks") & (r7.variant == "sk_K300")]["ll_2023-25"].iloc[0])]}, {k: [float(v[0]), float(v[1])] for k, v in pj["backtest_def"].items()})
        b8 = REP / "props_backtest8.csv"
        if b8.exists():
            r8 = pd.read_csv(b8)
            tie("props longest-play backtests on the page = props_backtest8.csv (l_blend_med)", {k: [float(r8[(r8.stat == k) & (r8.variant == "l_blend_med")]["mae_2019-22"].iloc[0]), float(r8[(r8.stat == k) & (r8.variant == "l_blend_med")]["mae_2023-25"].iloc[0])] for k in ["rec_longest", "rush_longest", "pass_longest"]}, pj["backtest_longest"])
            tie("props longest-play constants on the page = props_backtest8.csv (fitted)", {k: [float(x) for x in re.findall(r"blend ([\d.]+) \+ ([\d.]+) x decayed longest \+ ([\d.]+) x yards per game \(median factor ([\d.]+)\)", r8[(r8.stat == k) & (r8.variant == "l_blend_med")]["fitted"].iloc[0])[0]] for k in ["rec_longest", "rush_longest", "pass_longest"]}, {k + "_longest": list(v) for k, v in pj["longest"].items()})
        b9 = REP / "props_backtest9.csv"
        if b9.exists():
            r9 = pd.read_csv(b9); pick9 = {"kick_points": "k_blend_team", "field_goals": "g_blend_team"}
            tie("props kicker backtests on the page = props_backtest9.csv (team blends)", {k: [float(r9[(r9.stat == k) & (r9.variant == v)]["mae_2019-22"].iloc[0]), float(r9[(r9.stat == k) & (r9.variant == v)]["mae_2023-25"].iloc[0])] for k, v in pick9.items()}, pj["backtest_kick"])
            tie("props kicker constants on the page = props_backtest9.csv (fitted team blends)", {k: [float(x) for x in re.findall(r"team blend ([\d.]+) \+ ([\d.]+) x decayed team \+ ([\d.]+) x implied total", r9[(r9.stat == k) & (r9.variant == v)]["fitted"].iloc[0])[0]] for k, v in pick9.items()}, {"kick_points": list(pj["kick"]["pts"]), "field_goals": list(pj["kick"]["fgm"])})
        b5 = REP / "props_backtest5.csv"
        if b5.exists():
            r5 = pd.read_csv(b5); r6b = pd.read_csv(REP / "props_backtest6.csv"); pick5 = {"rec_catches": (r5, "rec_catch", "catch_K25_med", "mae"), "rec_td_ll": (r6b, "rec_td", "td_recon50", "ll"), "rush_td_ll": (r6b, "rush_td", "td_recon50", "ll"), "pass_td_ll": (r6b, "pass_td", "td_recon100", "ll"), "pass_int_ll": (r5, "pass_int", "int_league", "ll")}
            _bs2 = pd.read_csv(REP / "props_by_season.csv").set_index(["stat", "season"]); _cm = {"rec_catches": ("rec_catches", "mae"), "rec_td_ll": ("rec_td", "ll"), "rush_td_ll": ("rush_td", "ll"), "pass_td_ll": ("pass_td", "ll"), "pass_int_ll": ("pass_int", "ll")}
            tie("props count backtests on the page = props_by_season.csv (the adopted rule, walk-forward, league averages as of each game)", {k: [float(_bs2.loc[(st, "2019-22"), c]), float(_bs2.loc[(st, "2023-25"), c])] for k, (st, c) in _cm.items()}, {k: [float(v[0]), float(v[1])] for k, v in pj["backtest_counts"].items()})
            fitted5 = {st: r5[r5.stat == st].fitted.dropna().iloc[0] for st in ["rec_catch", "rec_td", "pass_td"]}
            fitted5["rec_catch"] = fitted5["rec_catch"].split(", median factor")[0]   # the catch K is round five's; its factor was refit in round eleven (tied above)
            tie("props count constants = props_backtest5.csv", fitted5, {"rec_catch": f"K {pj['k_catch']:.0f}", "rec_td": f"K {pj['k_td']['rec']:.0f}, margin coefficient {pj['td_margin']['rec']:.3f} per point", "pass_td": f"K {pj['k_td']['pass']:.0f}, margin coefficient {pj['td_margin']['pass']:.3f} per point"})
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
    wl = LNS / "watch_log.csv"
    if wl.exists():   # every source in the line watch logs its own error and the run carries on, so an error must fail here (24 Sep 2026:
        # the props pull crashed for 11 hours unseen; the two sources that failed every run were retired, so any error is real)
        last = pd.read_csv(wl).tail(1)
        errs = [e.strip() for e in str(last.errors.iloc[0] if len(last) and pd.notna(last.errors.iloc[0]) else "").split(";") if e.strip()]
        rows.append(("line watch: every source ran without an error on the newest snapshot", "; ".join(errs)[:160] or "no error", "no error", not errs))
    try:   # sportsbooks send player names only: every name in this week's book lines must resolve to a rostered player
        from . import props_lines as PLN
        from .lines import current_week as _cw
        lg = PLN.load_log(); s_, w_ = _cw(g); cur = lg[(lg.season == s_) & (lg.week == w_)]
        tot = hit = 0; miss = []
        for gid in cur.game_id.dropna().unique():
            mk = PLN.closing(lg, gid); gg = cur[cur.game_id == gid].iloc[0]; canon = PLN.roster_keys(s_, {gg.home, gg.away}); vals = set(canon["exact"].values())
            x = mk[~mk.player.str.contains(r"D/ST|Defense$", regex=True)].drop_duplicates("player")
            tot += len(x); m = x.key.isin(vals); hit += int(m.sum()); miss += list(x[~m].player)
        if tot:
            rows.append(("prop lines: book names resolve to rostered players (99%+)", f"{hit / tot:.1%}" + (f"; missed {', '.join(miss[:6])}" if miss else ""), "99% or more", hit / tot >= 0.99))
    except Exception as e:  # noqa
        rows.append(("prop lines: book names resolve to rostered players", str(e)[:80], "", False))
    wd = ROOT / "web" / "data"   # the published page may not pass 64 MB a version: fail with room to spare so a growing season never breaks a publish
    tot_mb = sum(f.stat().st_size for f in wd.rglob("*") if f.is_file()) / 1e6 + (ROOT / "web" / "index.html").stat().st_size / 1e6
    rows.append(("published page size under 60 MB (the cap is 64 MB a version)", f"{tot_mb:.1f} MB", "under 60 MB", tot_mb < 60))
    fjs = ROOT / "web" / "data" / "fresh.js"
    if fjs.exists():   # the live check (injuries, starters, forecasts) logs its errors the same way
        s_ = fjs.read_text(); fr_ = json.loads(s_[s_.index("=") + 1:].rstrip().rstrip(";"))
        rows.append(("live check: injuries, starters and forecasts pulled without an error", "; ".join(fr_.get("errors") or [])[:160] or "no error", "no error", not fr_.get("errors")))
    pvf, dgf = OUT / "player_values_all.parquet", OUT / "defender_games.parquet"
    if pvf.exists() and dgf.exists():   # a regular defender who played in the last two seasons always has a snap share (the team-change bug zeroed 99)
        pv = pd.read_parquet(pvf); dgl = pd.read_parquet(dgf, columns=["player_id", "season"]).groupby("player_id").season.max()
        x = pv[(pv.group == "Defense") & (pv.games > 0) & (pv.plays_per_game.fillna(0) > 15) & (pv.player_id.map(dgl).fillna(0) >= int(g.season.max()) - 1)]
        z = x[x.share.fillna(0) < 0.05]
        rows.append(("defenders with 15+ snaps a game in the last two seasons all have a snap share", ", ".join(z.name.head(5)) or "none zero", "none zero", len(z) == 0))
        # every rostered defender with 300+ snaps last season has a value (Pat Surtain II had none: the snap counts were matched by name)
        dgs = pd.read_parquet(dgf, columns=["player_id", "season", "plays"]); last = int(g.season.max()) - 1
        big = set(dgs[dgs.season == last].groupby("player_id").plays.sum().loc[lambda x: x >= 300].index)
        nov = pv[(pv.group == "Defense") & pv.player_id.isin(big) & pv.value_above_replacement.isna()]
        rows.append((f"rostered defenders with 300+ snaps in {last} all have a value", ", ".join(nov.name.head(5)) or "all valued", "all valued", len(nov) == 0))
        sc = RAW / "snap_counts" / f"snap_counts_{last}.parquet"
        if sc.exists():   # the defender table carries nearly every defensive snap of last season (matched by PFR id)
            tot = float(pd.read_parquet(sc, columns=["defense_snaps"]).defense_snaps.sum()); got = float(dgs[dgs.season == last].plays.sum())
            rows.append((f"defender table holds 97%+ of {last}'s defensive snaps", f"{got / tot:.1%}", "97% or more", got / tot >= 0.97))
        # consensus floor (24 Sep 2026: Myles Garrett and Christian Gonzalez once sat near the bottom of their lists): last
        # season's AP All-Pros who have a value rank in the top half of their group. Linemen are left out: they share
        # their line's unit rating, so a good lineman on a bad line ranks low by design.
        apf = ROOT / "data" / "reference" / "allpro.csv"
        if apf.exists():
            ap_ = pd.read_csv(apf); ap_ = ap_[(ap_.season == ap_.season.max()) & (ap_.group != "OL")]
            vv = pv[pv.value_above_replacement.notna()].copy(); vv["grp"] = vv.def_role.where(vv.group == "Defense", vv.position)
            low = []
            for gid, nm in zip(ap_.gsis_id, ap_.name):
                me = vv[vv.player_id == gid]
                if len(me):
                    g_ = vv[vv.grp == me.grp.iloc[0]]; pct_ = 1 - (g_.value_above_replacement > me.value_above_replacement.iloc[0]).sum() / len(g_)
                    if pct_ < 0.5:
                        low.append(f"{nm} ({me.grp.iloc[0]}, top {100 * (1 - pct_):.0f}%)")
            rows.append((f"{int(ap_.season.max())} All-Pros (not linemen) rank in the top half of their group", "; ".join(low) or "all in the top half", "all in the top half", not low))
        # build order: every table is built after the tables it reads (24 Sep 2026: the Players tab's history was built
        # before this run's defender, kicker and lineman tables, so fixes reached it a run late). Two minutes' slack for
        # a fresh checkout, where every file has the checkout's time.
        order = {"player_history.parquet": ["player_games.parquet", "defender_games.parquet", "kicking_games.parquet", "ol_games.parquet"],
                 "player_values_all.parquet": ["player_games.parquet", "defender_games.parquet", "kicking_games.parquet", "ol_games.parquet"],
                 "roster_now.parquet": ["player_values_all.parquet"]}
        late = [f"{o} before {i}" for o, ins in order.items() for i in ins
                if (OUT / o).exists() and (OUT / i).exists() and (OUT / o).stat().st_mtime < (OUT / i).stat().st_mtime - 120]
        rows.append(("player tables built after the tables they read (none stale)", "; ".join(late) or "in order", "in order", not late))
        # every snap-count row carries a gsis id by PFR id, in every position group (24 Sep 2026: the rosters have no PFR
        # id for linemen, so 579 lineman games went to a namesake and 1,411 were dropped until the players table filled it)
        from .ids import map_pfr
        worst = []
        for s_ in (last, last + 1):
            f_ = RAW / "snap_counts" / f"snap_counts_{s_}.parquet"
            if f_.exists():
                sn_ = pd.read_parquet(f_, columns=["season", "team", "player", "pfr_player_id", "position", "offense_snaps", "defense_snaps"]); sn_ = sn_[(sn_.offense_snaps + sn_.defense_snaps) > 0]
                sn_["gid"] = map_pfr(sn_)
                for pos_, x_ in sn_.groupby("position"):
                    if len(x_) >= 50:
                        worst.append((float(x_.gid.notna().mean()), f"{s_} {pos_}"))
        if worst:
            w_ = min(worst)
            rows.append(("snap counts matched to a player by id (PFR id, else a name unique on that team's roster), worst position group", f"{w_[0]:.1%} ({w_[1]})", "99% or more", w_[0] >= 0.99))
    fj = ROOT / "web" / "data" / "fresh.js"
    if fj.exists() and (LNS / "lines_log.csv").exists() and (LNS / "props_log.csv").exists():   # the This week pull strip against the raw logs
        s = fj.read_text(); fr = json.loads(s[s.index("=") + 1:].rstrip().rstrip(";"))
        if "pulls" in fr:
            ll = pd.read_csv(LNS / "lines_log.csv", usecols=["ts", "source"]); pl = pd.read_csv(LNS / "props_log.csv", usecols=["ts", "book"])
            z = lambda x: None if pd.isna(x) else f"{x[:10]}T{x[11:13]}:{x[14:16]}Z"
            want = {"espn": z(ll[ll.source.str.startswith("espn:")].ts.max()), "oddsapi": z(ll[ll.source.str.startswith("oddsapi:")].ts.max()),
                    "props": z(pl[~pl.book.isin(["prizepicks", "underdog"])].ts.max()), "prizepicks": z(pl[pl.book == "prizepicks"].ts.max()), "underdog": z(pl[pl.book == "underdog"].ts.max())}
            tie("This week's pull times = the newest rows in the line and prop logs", {r["key"]: r["last"] for r in fr["pulls"] if r["key"] in want}, want)
    try:
        check_season_equation(rows)
    except Exception as e:  # noqa
        rows.append(("season simulation's equation check", str(e)[:80], "", False))
    return rows


def check_season_equation(rows) -> None:
    """The season simulation's equation (season.expected_points on the as-of team profiles) must give the model's own
    expected points for the week being priced when the game's situational inputs are set to what the model saw; the
    ratings and QB come from the profiles, so this ties the profile mapping as well as the coefficients."""
    from . import season as SE, model as M, lines as LN
    games = pd.read_parquet(OUT / "games.parquet"); pred = pd.read_parquet(OUT / "pred_v3.parquet")
    s_, w_ = LN.current_week(games)
    f = SE._frame(); P = SE.profiles(f, s_, w_); fit = SE.fit_asof(pred, s_, w_)
    fw = f[(f.season == s_) & (f.week == w_)]; pw = pred[(pred.season == s_) & (pred.week == w_)].set_index("game_id")
    sit = M.SIT_FEATS + ["qb_out"] + M.INJ_FEATS + M.CONT_FEATS + M.LATE_FEATS
    worst, n = 0.0, 0
    for r in fw.itertuples():
        if r.game_id not in pw.index or r.opp not in P:
            continue
        ov = {k: float(getattr(r, k)) for k in sit}
        e = SE.expected_points(P[r.team], P[r.opp], fit, float(r.home), float(r.neutral), float(r.dome), float(r.div_game), int(w_), overrides=ov)
        exp = float(pw.loc[r.game_id, "home_exp" if r.home == 1 else "away_exp"]); worst = max(worst, abs(e - exp)); n += 1
    rows.append((f"season simulation's equation on the as-of profiles rebuilds the model's expected points for the week being priced ({n} sides, worst gap in points)", round(worst, 4), "0.01 or under", worst <= 0.01))


def check_page() -> list[tuple[str, str, str, bool]]:
    rows = []
    def tie(what, a, b): rows.append((what, str(a), str(b), str(a) == str(b)))
    import collections as _c
    _ids = re.findall(r'\sid="([^"]+)"', (ROOT / "web" / "index.html").read_text()); _dup = sorted(k for k, v in _c.Counter(_ids).items() if v > 1)
    tie("the page has no duplicate element ids (a duplicate points a control at the wrong element)", _dup, [])
    pj = json.loads((OUT / "props.json").read_text()) if (OUT / "props.json").exists() else None
    if pj is not None:
        if (WEB / "player_profiles.js").exists() and (OUT / "props_profiles.json").exists():
            ppg = _js("player_profiles.js"); pp0 = json.loads((OUT / "props_profiles.json").read_text())
            tie("player profiles on the page = props_profiles.json (receivers, rushers, passers, defenses; week)", [len(pp0["receivers"]), len(pp0["rushers"]), len(pp0["passers"]), len(pp0["defenses"]), pp0["season"], pp0["week"]], [len(ppg["receivers"]), len(ppg["rushers"]), len(ppg["passers"]), len(ppg["defenses"]), ppg["season"], ppg["week"]])
        if (WEB / "props_record.js").exists():
            prr = _js("props_record.js"); n_proj = sum(len(pd.read_csv(f)) for f in REP.glob("props_*_wk*.csv")); n_gr = len(pd.read_csv(TR / "props_graded.csv")) if (TR / "props_graded.csv").exists() else 0; n_mk = len(pd.read_csv(TR / "props_vs_market.csv")) if (TR / "props_vs_market.csv").exists() else 0
            tie("props record on the page = every projection file, graded rows and market rows", [n_proj, n_gr, n_mk], [len(prr["projections"]), len(prr["graded"]), len(prr["market"])])
        if (WEB / "player_careers.js").exists():
            pc = _js("player_careers.js"); yr = max(y for y in pc["seasons"] if y < max(pc["seasons"]))   # the last complete season
            from .player_logs import unpack
            lg = unpack((WEB / "plogs" / f"{yr}.js").read_text())
            ix = {k: {c: i for i, c in enumerate(v)} for k, v in pc["cols"].items()}
            sf = RAW / "player_stats" / f"stats_player_week_{yr}.parquet"
            if sf.exists():   # the game logs against nflverse's official box score (the league's numbers, what the books settle on)
                st = pd.read_parquet(sf).fillna(0); S_ = lambda k, c: round(float(sum((r[ix[k][c]] or 0) for v in lg.values() for r in v.get(k, []))), 1)
                exact = [("rec", "targets", "targets"), ("rec", "catches", "receptions"), ("rec", "td", "receiving_tds"), ("rush", "carries", "carries"), ("rush", "yards", "rushing_yards"), ("rush", "td", "rushing_tds"),
                         ("pass", "completions", "completions"), ("pass", "td", "passing_tds"), ("pass", "int", "passing_interceptions"), ("pass", "sacks", "sacks_suffered")]
                tie(f"player game logs on the page = nflverse's official player stats, {yr} (targets, catches, rec TD, carries, rush yards, rush TD, completions, pass TD, INT, sacks taken)",
                    [S_(k, c) for k, c, _ in exact], [round(float(st[o].sum()), 1) for _, _, o in exact])
                # defense, game by game: every defensive player's official line is in the logs with the same numbers
                dl = pd.DataFrame([{"player_id": pid, "game_id": r[ix["def"]["game_id"]], "tk": r[ix["def"]["tackles"]], "solo": r[ix["def"]["solo"]], "sk": r[ix["def"]["sacks"]], "it": r[ix["def"]["ints"]], "pdf": r[ix["def"]["passes_defended"]]} for pid, v in lg.items() for r in v.get("def", [])])
                so = st.assign(tk=st.def_tackles_solo + st.def_tackle_assists + st.def_tackles_with_assist)
                jn = dl.merge(so[["player_id", "game_id", "tk", "def_tackles_solo", "def_sacks", "def_interceptions", "def_pass_defended"]], on=["player_id", "game_id"], how="inner")
                bad = int(((jn.tk_x - jn.tk_y).abs() > 0.01).sum() + ((jn.solo - jn.def_tackles_solo).abs() > 0.01).sum() + ((jn.sk - jn.def_sacks).abs() > 0.01).sum() + ((jn.it - jn.def_interceptions).abs() > 0.01).sum() + ((jn.pdf - jn.def_pass_defended).abs() > 0.01).sum())
                need = so[so.position_group.isin(["DL", "LB", "DB"]) & ((so.tk + so.def_sacks + so.def_interceptions + so.def_pass_defended) > 0)]
                miss = len(set(zip(need.player_id, need.game_id)) - set(zip(dl.player_id, dl.game_id)))
                tie(f"player game logs: defenders' tackles, solo, sacks, INT, passes defended = official game by game, {yr} (numbers off; official defensive games missing)", [bad, miss], [0, 0])
                gap = max(abs(S_("pass", "yards") - st.passing_yards.sum()), abs(S_("rec", "yards") - st.receiving_yards.sum()), abs(S_("pass", "attempts") - st.attempts.sum()))
                rows.append((f"player game logs: passing yards, receiving yards and attempts against official, {yr} (worst gap; laterals and a rare passer the play-by-play leaves unnamed)", str(round(gap)), "0.05% of the season or under", gap <= 0.0005 * st.passing_yards.sum()))
            # the props are graded on the same terms: rebuild the grading's actuals for the season from the charted plays
            from . import props as PRP
            sp = PRP.official(pd.read_parquet(OUT / "scheme_plays.parquet")); sp = sp[(sp.season == yr) & (sp.season_type == "REG")]
            stR = st[st.season_type == "REG"] if sf.exists() else None
            if stR is not None and len(sp):
                ours = [int(sp[sp.pass_play & sp.receiver_player_id.notna()].shape[0]), int(sp[sp.play_type.eq("run") & sp.rusher_player_id.notna()].shape[0]), int(sp[sp.play_type.eq("run") & sp.rusher_player_id.notna()].yards_gained.sum()),
                        int(sp.pass_att.sum()), int(sp[sp.pass_att].complete_pass.sum())]
                offi = [int(stR.targets.sum()), int(stR.carries.sum()), int(stR.rushing_yards.sum()), int(stR.attempts.sum()), int(stR.completions.sum())]
                gap = max(abs(a_ - b_) for a_, b_ in zip(ours, offi)); pgap = abs(float(sp.pass_yds.sum()) - float(stR.passing_yards.sum()))
                rows.append((f"props graded on the official box score, {yr} regular season (targets, carries, rush yards, attempts, completions: worst gap; passing yards gap)", f"{gap}; {round(pgap)}", "0.05% of each or under",
                             gap <= 0.0005 * min(offi) + 2 and pgap <= 0.0005 * float(stR.passing_yards.sum())))
            car_t = sum(r[4] for v in pc["careers"]["rows"].values() for r in v if r[0] == yr and r[1] == "rec"); log_t = sum(r[ix["rec"]["targets"]] for v in lg.values() for r in v.get("rec", []))
            tie(f"career totals on the page = the season's game logs, {yr} (targets)", car_t, log_t)
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
    # the card and deep-dive breakdowns: intercept + sum of coefficient x (input - training mean) from the page's own files = the model's expected points
    SIT = set(M.SIT_FEATS) | {"qb_out"} | set(M.INJ_FEATS) | set(M.CONT_FEATS) | set(M.LATE_FEATS)
    def rebuild(co, inputs):
        tot = co["intercept"]
        for f in M.FEATS:
            v = inputs.get(f); c = co["per_unit"][f]; mu = co["mean"][f]
            if v is None: return None
            tot += c * (v - mu)   # the page moves the situational means into its base; the sum is the same
        return tot
    if "games" in wk and wk["games"] and wk["games"][0].get("coefs"):
        worst = 0.0; n = 0
        for g in wk["games"]:
            for tm, key in [(g["home_team"], "home_exp"), (g["away_team"], "away_exp")]:
                if tm in g.get("sides", {}) and g.get(key) is not None:
                    v = rebuild(g["coefs"], g["sides"][tm]); n += 1
                    if v is not None: worst = max(worst, abs(v - g[key]))
        rows.append((f"card breakdowns rebuild the expected points from the page's files ({n} sides, worst gap in points)", round(worst, 3), "0.01 or under", worst <= 0.01))
        bk = _js("backtest.js")
        if "coef" in bk["cols"]:
            ci = {c: i for i, c in enumerate(bk["cols"])}; worst = 0.0; n = 0; TD = {}
            def team_js(tm):   # a team file reads window.TEAMDATA["XXX"]=...; keep each one parsed once
                if tm not in TD: t = (WEB / f"{tm}.js").read_text(); TD[tm] = json.loads(t[t.index('"]=') + 3:].rstrip().rstrip(";"))
                return TD[tm]
            for r in bk["rows"][-60:]:   # the newest sixty priced games, from every team's own file
                co = {"per_unit": dict(zip(M.FEATS, r[ci["coef"]])), "mean": dict(zip(M.FEATS, r[ci["mean"]])), "intercept": r[ci["intercept"]]}
                for tm, key in [(r[ci["home_team"]], "home_exp"), (r[ci["away_team"]], "away_exp")]:
                    td = team_js(tm); cols = td["cols"]; row = next((x for x in td["rows"] if x[0] == r[ci["game_id"]]), None)
                    if row is None: continue
                    inputs = {f: row[cols.index("mf_" + f)] for f in M.FEATS if ("mf_" + f) in cols}
                    v = rebuild(co, inputs); n += 1
                    if v is not None: worst = max(worst, abs(v - r[ci[key]]))
            rows.append((f"game-log model inputs rebuild the expected points from the team files ({n} sides, worst gap in points)", round(worst, 3), "0.01 or under", worst <= 0.01))
    g = pd.read_parquet(OUT / "games.parquet")
    from . import lines as LN
    season, week = LN.current_week(g)
    pk_f = REP / f"picks_{season}_wk{week}.csv"
    llf = LNS / "lines_log.csv"
    if llf.exists() and wk.get("games"):   # no number on a card older than its source: the cards' newest snapshot is the log's newest
        ll = pd.read_csv(llf, usecols=["ts"]); page_ts = max([r["ts"] for g in wk["games"] for r in g.get("line_history", [])] or ["none"])
        tie("cards' newest line snapshot = the line log's newest snapshot", page_ts, str(ll.ts.max()))
        # the Vegas win chance on a card comes from the newest snapshot with moneylines; it must be the log's newest one
        lm = LN.load_log(); lm = lm[lm.home_ml.notna() & lm.away_ml.notna() & lm.game_id.isin([g_["game_id"] for g_ in wk["games"]])]
        if len(lm):
            page_ml = max([r["ts"] for g_ in wk["games"] for r in g_.get("line_history", []) if r.get("home_ml") is not None and r.get("away_ml") is not None] or ["none"])
            tie("cards' Vegas win chance uses the line log's newest moneyline snapshot", page_ml, str(lm.ts.max()))
    if "cal" in wk and "games" in wk:   # the card re-prices a moved line with the same calibration the run used
        import math
        def cal_p(cal, e): p = 1 / (1 + math.exp(-(cal[0] + cal[1] * min(abs(e), 7.0)))); return p if e > 0 else 1 - p
        worst = max([abs(cal_p(wk["cal"]["spread"], g["spread_edge"]) - g["p_cover_cal_home"]) for g in wk["games"] if g.get("spread_edge") is not None and g.get("p_cover_cal_home") is not None] or [0.0])
        rows.append(("card calibration on the page reproduces the run's calibrated cover odds at the run's line (worst gap)", round(worst, 4), "0.0005 or under", worst <= 0.0005))
    if pk_f.exists() and "games" in wk:
        pk = pd.read_csv(pk_f).set_index("game_id")
        pg = {x["game_id"]: x for x in wk["games"]}
        tie("page week = picks file (games)", sorted(pg), sorted(pk.index))
        _side = lambda b: " ".join(w.split()[0] for w in str(b or "").split(", ") if w)   # the team or Over/Under; the number follows the line log (the freshness tie holds it to the newest snapshot)
        tie("page week = picks file (bets: the side flagged)", sorted(_side(x.get("bet")) for x in pg.values()), sorted(_side(b) for b in pk.bet.fillna("")))
        tie("page week = picks file (model spread)", round(float(max(abs((pg[k]["model_spread"] or 0) - pk.loc[k, "model_spread"]) for k in pg if k in pk.index)), 3), 0.0)
    tr = _js("track.js"); mp = pd.read_csv(TR / "model_picks.csv") if (TR / "model_picks.csv").exists() else pd.DataFrame()
    if len(mp):
        cur = mp[(mp.season == season) & (mp.week == week)]
        tie("page live table = tracker (pending model rows)", sorted(x["bet"] for x in tr if x.get("who") == "model" and x.get("season") == season and x.get("week") == week), sorted(cur.bet))
    rk = _js("rankings.js")
    tie("page rankings: QB replacement level", rk.get("params", {}).get("qb_prior"), R.DEFAULT["qb_prior"])
    # the Season tab: odds and totals on the page = the reports the same export wrote; probabilities add up
    try:
        from . import lines as LN
        sj = _js("season.js"); so = pd.read_csv(REP / "season_odds.csv"); g_ = pd.read_parquet(OUT / "games.parquet"); s_, w_ = LN.current_week(g_)
        tie("season odds are for the week being priced", f"{sj['season']} {sj['week']}", f"{s_} {w_}")
        tie("season odds on the page = reports/season_odds.csv (teams; Super Bowl, division and playoff odds)", [len(sj["teams"]), [round(t["p_sb"], 4) for t in sj["teams"]], [round(t["p_div"], 4) for t in sj["teams"]]], [len(so), so.p_sb.round(4).tolist(), so.p_div.round(4).tolist()])
        sums = {"champion": round(sum(t["p_sb"] for t in sj["teams"]), 3), "conference": round(sum(t["p_conf"] for t in sj["teams"]), 3), "division": round(sum(t["p_div"] for t in sj["teams"]), 3), "playoffs": round(sum(t["p_playoffs"] for t in sj["teams"]), 3), "byes": round(sum(t["p_bye"] for t in sj["teams"]), 3)}
        tie("season odds add up (one champion, two conference champions, eight division winners, the playoff field, the byes)", sums, {"champion": 1.0, "conference": 2.0, "division": 8.0, "playoffs": float(2 * sj["format"]), "byes": 2.0 if sj["format"] == 7 else 4.0})
        n_reg = int(((g_.season == s_) & (g_.game_type == "REG")).sum())
        tie("expected wins across the league = regular-season games (every game gives one win, a tie half each)", round(sum(t["wins"] for t in sj["teams"]), 1), float(n_reg))
        if sj.get("left"):   # the page's math under Wins: record + the chance in each game left = the simulated wins (the draws' noise and the tie band, under 0.1)
            gap = max(abs(t["wins_now"] + sum(g[3] for g in sj["left"].get(t["team"], [])) - t["wins"]) for t in sj["teams"])
            rows.append(("season wins on the page = record + the chance in each game left (worst team, wins)", round(gap, 3), "0.1 or under", gap <= 0.1))
        if (REP / "season_backtest.csv").exists() and "backtest" in sj:
            b = pd.read_csv(REP / "season_backtest.csv"); m = b[(b.season.astype(str) == "mean") & (b.asof_week.astype(str) == "all") & (b.shrink == 0.0) & (b.sigma_mult == 1.0)].sort_values("window")
            tie("season backtest on the page = reports/season_backtest.csv (base variant, window means: wins off, division Brier, Super Bowl log loss)", [[r["window"], round(r["wins_mae"], 4), round(r["div_brier"], 4), round(r["sb_ll"], 4)] for r in sorted(sj["backtest"]["windows"], key=lambda r: r["window"])], [[r.window, round(r.wins_mae, 4), round(r.div_brier, 4), round(r.sb_ll, 4)] for r in m.itertuples()])
        if (REP / "season_calibration.csv").exists():
            tie("season reliability table on the page = reports/season_calibration.csv (rows, teams counted)", [len(sj.get("calibration", [])), sum(r["n"] for r in sj.get("calibration", []))], [len(pd.read_csv(REP / "season_calibration.csv")), int(pd.read_csv(REP / "season_calibration.csv").n.sum())])
        lj = _js("legit.js")
        for key, fn in (("sizing", "sizing_backtest.csv"), ("seasons", "sizing_seasons.csv"), ("cover_cal", "cover_calibration.csv"), ("cal_start", "calibration_start.csv")):
            if (REP / fn).exists():
                tie(f"Bets tab: {key} on the page = reports/{fn} (rows)", len(lj.get(key, [])), len(pd.read_csv(REP / fn)))
        if (REP / "sizing_backtest.csv").exists() and (REP / "track_record.md").exists():
            _sz = pd.read_csv(REP / "sizing_backtest.csv"); _f = _sz[(_sz.staking == "flat")].set_index("window")
            from . import backtest as _B, picks as _P
            _d = _B.join(pd.read_parquet(OUT / "pred_v3.parquet"), pd.read_parquet(OUT / "games.parquet")); _rr = _P.rule_records(_d[(_d.game_type == "REG") & _d.spread_line.notna()]).set_index("rule")
            tie("sizing backtest flag records = the rule records on the Bets tab (2019-22, 2023-25)", [_f.loc["2019-22", "record"], _f.loc["2023-25", "record"]], [_rr.loc["model", "2019-22"], _rr.loc["model", "2023-25"]])
        pt = pd.read_csv(REP / "player_season_totals.csv"); pr = sj["players"]["rows"]
        tie("player season totals on the page = reports/player_season_totals.csv (rows, projected yards, breakouts)", [len(pr), round(sum(r["proj_yards"] for r in pr), 1), sum(1 for r in pr if r["breakout"])], [len(pt), round(float(pt.proj_yards.sum()), 1), int(pt.breakout.sum())])
        if (REP / "player_season_backtest.csv").exists() and "player_backtest" in sj:
            pb = pd.read_csv(REP / "player_season_backtest.csv")
            tie("player season backtest on the page = reports/player_season_backtest.csv (rows)", len(sj["player_backtest"]), len(pb))
    except Exception as e:  # noqa
        rows.append(("season tab files", str(e)[:80], "", False))
    return rows


def main(page: bool = False, source: str = "weekly run") -> bool:
    rows = check_sources() + (check_page() if page else [])
    ok = all(r[3] for r in rows)
    L = [f"# Tie-out ({'sources and page' if page else 'sources'}), {pd.Timestamp.now('UTC').strftime('%Y-%m-%d %H:%M UTC')}", "",
         "The same number must read the same everywhere it appears. Each row: what was compared, what it says, what it should say.", "",
         "| Check | Reads | Should read | Ties |", "|---|---|---|---|"] + [f"| {w} | {str(a)[:80]} | {str(b)[:80]} | {'yes' if t else 'NO'} |" for w, a, b, t in rows] + \
        ["", f"Result: {'PASS' if ok else 'FAIL'} ({sum(1 for r in rows if r[3])} of {len(rows)} tie)"]
    (REP / "tie_check.md").write_text("\n".join(L) + "\n"); print("\n".join(L))
    write_health(rows, page, source)
    return ok


def write_health(rows, page: bool, source: str) -> None:
    """web/data/health.js: the result of every check, for the page's health chip and Model -> Health checks. Written by
    the weekly run (sources and page) and by every line-watch run (every 30 minutes)."""
    import json
    now = pd.Timestamp.now("UTC").strftime("%Y-%m-%d %H:%M UTC")
    fails = [{"what": w, "reads": str(a)[:120], "should": str(b)[:120]} for w, a, b, t in rows if not t]
    h = {"checked": now, "source": source, "scope": "sources and page" if page else "sources", "total": len(rows), "passed": len(rows) - len(fails),
         "ok": not fails, "fails": fails[:40], "checks": [[w, bool(t)] for w, a, b, t in rows]}
    WEB.mkdir(parents=True, exist_ok=True); (WEB / "health.js").write_text("window.HEALTH=" + json.dumps(h, separators=(",", ":")) + ";")


if __name__ == "__main__":
    src = sys.argv[sys.argv.index("--source") + 1] if "--source" in sys.argv else "weekly run"
    sys.exit(0 if main("--page" in sys.argv, src) else 1)
