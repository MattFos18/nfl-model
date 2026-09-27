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
    # injury reasons come from this season only (26 Sep 2026: A.J. Brown on IR showed "Teeth" from a 2025 report)
    if (OUT / "roster_now.parquet").exists():
        from . import lines as LN3; _s3, _ = LN3.current_week(g); _rn = pd.read_parquet(OUT / "roster_now.parquet")
        _old = _rn[_rn.why_src.astype(str).str.contains(r"listed him \(20\d\d") & _rn.why.astype(str).ne("")]
        tie("injury reasons shown come from this season (no reason from an earlier season's report)", sorted(_old.name.astype(str))[:10], [])
    if (OUT / "props.json").exists():
        pj = json.loads((OUT / "props.json").read_text()); from . import lines as LN2; _s2, _w2 = LN2.current_week(g)
        tie("props projections are for the current week", f"{pj['season']} {pj['week']}", f"{_s2} {_w2}")
        # the chip "Game model N pts" and the player lines' team scaling come from the model's expected points; the
        # weekly run built props one step before the model re-priced, so they carried the previous run's points (26 Sep 2026)
        _xp = pd.read_parquet(OUT / "pred_v3.parquet").set_index("game_id")
        _pe = {f"{gid} {t}": s_["recon"]["rec"]["exp_pts"] for gid, gm in pj["games"].items() for t, s_ in gm.items() if s_.get("recon", {}).get("rec", {}).get("exp_pts") is not None}
        _me = {f"{gid} {t}": round(float(_xp.loc[gid, "home_exp" if gid.endswith("_" + t) else "away_exp"]), 1) for gid, gm in pj["games"].items() for t in gm if gid in _xp.index and f"{gid} {t}" in _pe}
        tie("props game-model points = the model's expected points (pred_v3)", _pe, _me)
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
            _ro = pd.read_csv(REP / "props_official.csv") if (REP / "props_official.csv").exists() else None   # passing yards: the live constants' row (refit on the official numbers 24 Sep 2026, kept 25 Sep)
            if _ro is not None:
                _x = _ro[(_ro.stat == "pass_yards") & _ro.verdict.str.startswith(("kept", "adopted"))].iloc[0]; _tf["pass"]["yds"] = [float(v) for v in _x.team_fit.split(" x ")[0].split(" + ")]
            tie("props team fit constants = props_backtest6.csv (passing yards: props_official.csv)", _tf, {k: {v: [float(x) for x in pj["team_fit"][k][v]] for v in ["td", "yds"]} for k in ["rec", "rush", "pass"]})
            tie("props round-4 base = round-3 adopted variant (receiving, rushing)", {k: [float(r4[(r4.stat == k) & (r4.variant == "base")]["mae_2019-22"].iloc[0]), float(r4[(r4.stat == k) & (r4.variant == "base")]["mae_2023-25"].iloc[0])] for k in ["rec_yards", "rush_yards"]}, {k: [float(a85.loc[k, "mae_2019-22"]), float(a85.loc[k, "mae_2023-25"])] for k in ["rec_yards", "rush_yards"]})
            r11 = pd.read_csv(REP / "props_backtest11.csv"); _rf = lambda st: float(r11[(r11.stat == st) & (r11.variant == "refit_2017_18")].factors.iloc[0])
            _mp = float(_ro[(_ro.stat == "pass_yards") & _ro.verdict.str.startswith(("kept", "adopted"))].med.iloc[0]) if _ro is not None else _rf("pass_yards")
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
            # receiving and passing: round 15 (the median factor that rises with the mean, 27 Sep 2026; one row per window); rushing: round 13 (injury report and snap trend, 25 Sep 2026; round 15 kept its flat factor)
            r13 = pd.read_csv(REP / "props_backtest13.csv"); r15 = pd.read_csv(REP / "props_backtest15.csv")
            def _r15(stat, var): return [float(r15[(r15.stat == stat) & (r15.variant == var) & (r15.window == w)].mae.iloc[0]) for w in ("2019-22", "2023-25")]
            b2 = {"rec_yards": _r15("rec_yards", "A_logistic_mean_s5"), "pass_yards": _r15("pass_yards", "A_linear_mean"),
                  "rush_yards": [float(r13[(r13.stat == "rush_yards") & (r13.variant == "D_all (A_injury, B_snap_w0.25)")]["mae_2019-22"].iloc[0]), float(r13[(r13.stat == "rush_yards") & (r13.variant == "D_all (A_injury, B_snap_w0.25)")]["mae_2023-25"].iloc[0])]}
            # within 0.01: two decimals on the by-season run, and round 13 was scored on the team scores before they were matched to the game total (25 Sep 2026), which moved receiving and rushing by at most 0.007
            rows.append(("props by-season run = the adopted rule's rows in the round that set it (yards, both windows; within 0.01)", str(b1), str(b2), all(abs(b1[k][i] - b2[k][i]) <= 0.01 for k in b1 for i in (0, 1))))
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
        from . import pulls as _PU
        tie("the page's freshness limits (fresh.js late_h) = nflmodel/pulls.py LATE_H", fr_.get("late_h", "missing"), _PU.LATE_H)
    try:   # docs section 4 quotes the live fit (report.effects_tables, rewritten every run): the QB row and the overlap sentence
        from . import lines as _LN
        _s, _w = _LN.current_week(g); _x = p[(p.season == _s) & (p.week == _w)]
        _doc = (ROOT / "docs" / "how_it_works.md").read_text()
        _m = re.search(r"\n\| Starting QB rating \| ([+-][\d.]+) \|", _doc)
        tie("docs section 4 effects table: QB points per unit = the fit that priced the week (pred_v3)", _m.group(1) if _m else "missing", f"{float(_x.iloc[0]['coef_qb_rating']):+.3f}" if len(_x) else "no week")
        _q = M.qb_overlap(M.prep(M.with_trends(pd.read_parquet(OUT / "features_asof.parquet"))), _s)
        _m = re.search(r"move together \(correlation ([\d.]+) over", _doc)
        tie("docs section 4: QB and offense rating correlation = model.qb_overlap", _m.group(1) if _m else "missing", f"{_q['corr']:.2f}")
    except Exception as e:  # noqa
        rows.append(("docs section 4 live-fit blocks", str(e)[:80], "", False))
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
    try:
        check_calibration(rows)
    except Exception as e:  # noqa
        rows.append(("calibration audit (home win, cover and over chances against what happened)", str(e)[:80], "", False))
    check_run(rows, g)
    return rows


CAL_MIN_N, CAL_Z = 150, 2.5   # a calibration bucket fails when it holds this many games and what happened sits more than this many binomial standard errors from what was said
CAL_WINDOWS = list(P.WINDOWS.items()) + [("2015-25", (2015, 2025))]
AUDIT_NOTES = [   # the 27 Sep 2026 audit (every model output against what happened, 2015 to 2025); the tables below are rebuilt every run
    "Over chance: the raw p_over_emp was too far from 50% on both sides, every window (said 63% over, the over came 50%: 2015-25 n 256, z -4.5; said 55%, came 50%: n 1119, z -2.8; said 46%, came 49%: n 1125, z +2.3; the same shape in each window). Cause: the chance is priced as if the model's total were the truth and the line carried nothing, while the line's miss is the model's (MAE 10.5 each). Shipped 27 Sep 2026, a mapping and not a model change: the cards, the takeaways and the report show p_over_cal = logistic(a + b x logit(p_over_emp)) (picks.over_calibration), fit walk-forward on every regular-season game from 2015 to the season before the one priced, refit every run (today a -0.040, b 0.389 on 2869 games: 63% raw reads 54%, 55% reads 51%). It scores a better log loss and Brier than the raw chance on 2016-18, 2019-22, 2020-22 and 2023-25 (table below), and the checked over table is now the calibrated one. The totals flag (unders at 55%+) stays on the raw chance, the same monotone mapping, so it is the same rule with the same records; the raw table stays below for the record.",
    "Home win chance (p_home): the home side won less often than said when the model had it a slight underdog. Said 45%, won 39% in 2015-25 (n 556, z -3.0; 2023-25 alone n 180, 45% said, 34% won, z -3.0); said 35%, won 30% (n 327, z -2.0); the line was high in the same games but less (43% implied); overall 2019-22 said 56.0% home and 52.4% happened (z -2.5) while the fitted home coefficient was 2.2 and 1.9 points in 2019 and 2020 against a realised home margin near 0. Cause: one home-field term fit on 2013 on lags the fall in home advantage; a home term that follows recent seasons did not fix the 2023-25 bucket (31 variants, reports/home_field_recency.md), so the model stays. Shipped 27 Sep 2026, a mapping and not a model change: the cards, the friends' report and the picks file show p_home_cal = logistic(a + b x logit(p_home)) (picks.home_calibration), fit walk-forward on every regular-season game from 2015 to the season before the one priced, ties dropped, the identity under 500 games (two seasons: a one-season fit read worse than the raw chance), refit every run (today a -0.123, b 1.191 on 2885 games: 45% raw reads 41%, 35% reads 30%, 65% reads 65%). It scores a better log loss and Brier than the raw chance on 2016-18, 2019-22, 2020-22 and 2023-25 (table below; a richer form with an intercept shift for the home side being the model's underdog was worse than the raw chance on 2016-18 and is not adopted), and the checked home table is now the calibrated one. It does not cure the 2023-25 slight-underdog bucket: it moves a third of those games down into 0.3-0.4, where they sit within noise, and the 147 left say 45% and won 35% (z -2.5), three games under the check's 150-game floor; the stretch (b over 1) also reads the few 10-20% home sides low (2016-25 n 61, said 16%, won 31%, under the floor). The season simulation (season.py, the season file's chance per game) still reads the raw chance; the raw table stays below for the record.",
    "Calibrated cover chance (the cards' cover odds, picks.calibration): honest within noise in every band, 2019-25. It is nearly flat (50% at a 0-point edge to 56% at 7) and conservative on the flags: 4-5 point edges said 54% and covered 64% (n 107, z +2.0) while 2-4 point edges covered 48% (n 546). The raw bell-curve chance (p_cover_home, picks file only) runs 8 to 15 points hot at every edge (3-4 points: said 61%, covered 47%, z -3.7), as documented.",
    "Cover biases (2019-25, all games at the model's side): home or away side, favourite or underdog, primetime and divisional games are all within 2 SE in every window. One bucket is not: in 2023-25 the model's side covered 41% in the highest third of totals (n 201, z -3.0); 2019-22 was 54% and 2015-18 51% in the same third, so it is not a standing flaw.",
    "Margin scale: the stated sigma (13.0 to 13.2) is a shade wide against the realised spread of result minus model spread (12.8 to 12.9): the 50% interval holds 53 to 55%, the 80% 80 to 82%, the 95% 94 to 95%.",
    "Team points by tier: within noise except the top tier in 2023-25, where sides expected to score 27+ scored 30.7 against 28.6 said (n 172, z -2.9); 2015-18 and 2019-22 show no such gap.",
    "Season odds (reports/season_calibration.csv): 2019-22 is within noise in every band; 2023-25 is overconfident at both ends (division chances said 1% came 4%, n 183, z +4.5; playoff chances said 77% came 59%, n 41, z -2.9), as the docs already say.",
    "Player props (data/tracker/props_graded.csv, two weeks, projections made after the fact): every volume stat is projected high. Targets 4.9 said, 3.4 happened (ratio 0.69, z 12); carries 0.78; catches 0.80; receiving TDs 0.78 (101 said, 79 scored); interceptions 0.70; tackles 0.88. A quarter of the receiving rows (22.5%) are players who saw no target; without them targets are still 18% high and receiving TDs 7.5% high. TD chances read as 1 - exp(-projection) overstate the anytime rate: a 0.15-0.25 TD projection scored in 8.6% of games against 17.9% implied (n 128, z -2.7). Cause: the volume shares do not fall enough for depth players, and no availability check drops players who will not play. Two weeks is too few for a check; reviewed here until the record is long enough.",
]


def _cal_table(x: pd.DataFrame, key, said: str, y: str, edges, labels=None) -> pd.DataFrame:
    """Buckets of `key` (edges, optional labels): games, the mean stated chance, what happened, the binomial standard
    error of the stated chance and how many of them the outcome sits away."""
    b = pd.cut(key, edges, right=False, labels=labels)
    t = x.groupby(b, observed=True).agg(n=(y, "size"), said=(said, "mean"), actual=(y, "mean"))
    t["se"] = np.sqrt(t.said * (1 - t.said) / t.n); t["z"] = (t.actual - t.said) / t.se
    return t


def _cal_md(t: pd.DataFrame, min_n: int = 30, fail: bool = True) -> list[str]:
    """fail=False: a table kept for the record (the raw over chance), never marked."""
    L = ["| Bucket | Games | Said | Happened | z |", "|---|---|---|---|---|"]
    for ix, r in t[t.n >= min_n].iterrows():
        L.append(f"| {ix} | {int(r.n)} | {r.said:.3f} | {r.actual:.3f} | {r.z:+.1f}{' **FAIL**' if fail and r.n >= CAL_MIN_N and abs(r.z) > CAL_Z else ''} |")
    return L


def check_calibration(rows) -> None:
    """Every chance the model states against what happened (27 Sep 2026: the player-TD miscalibration was found by
    hand against book prices, not by a check). Three checks, on the committed prediction table and results: the calibrated
    home win chance by decile, the calibrated cover chance by band of the edge (2019 on, the calibration window) and the
    calibrated over chance by decile, per backtest window and pooled, each the figure the cards show. A bucket with CAL_MIN_N
    games whose outcome sits more than CAL_Z binomial standard errors from the stated chance fails. The wider audit (raw home
    win and over chances, raw cover chance, biases by side and situation, totals bias, margin scale, team points, season odds,
    props) is written to reports/calibration_audit.md every run; it does not fail the check."""
    p = pd.read_parquet(OUT / "pred_v3.parquet"); g = pd.read_parquet(OUT / "games.parquet")
    d = B.join(p, g); d = d[(d.game_type == "REG") & d.home_score.notna()].copy()
    gi = g.set_index("game_id"); d["primetime"] = d.game_id.map(gi.primetime).fillna(0); d["div_game"] = d.game_id.map(gi.div_game).fillna(0)
    d["hw"] = (d.result > 0).astype(float) + 0.5 * (d.result == 0)
    L = [f"# Calibration audit, {pd.Timestamp.now('UTC').strftime('%Y-%m-%d %H:%M UTC')}", "",
         "Every chance the model states against what happened, regular season, from the committed prediction table (pred_v3) and results (games). "
         f"Said is the mean stated chance in the bucket, z is how many binomial standard errors the outcome sits from it. A bucket with {CAL_MIN_N}+ games and |z| over {CAL_Z:g} fails the health check "
         "(the three checked tables are the calibrated home win chance, the calibrated cover chance and the calibrated over chance, the figures the cards show); every other table is the audit's record and does not fail. Windows are the backtest's: "
         "2015-18 untouched, 2019-22 tuning, 2023-25 held out. Rebuilt by nflmodel.tie_check on every run.", "", "## Findings (27 Sep 2026 audit; the tables below are today's)", ""]
    L += [f"- {n}" for n in AUDIT_NOTES] + [""]
    fails = {"home win": [], "cover": [], "over": []}
    def note(k, w, t):
        for ix, r in t[(t.n >= CAL_MIN_N) & (t.z.abs() > CAL_Z)].iterrows():
            fails[k].append(f"{w} {ix}: said {r.said:.3f}, happened {r.actual:.3f} (n {int(r.n)}, z {r.z:+.1f})")
    # 1. the home win chance: the calibrated one on the cards (picks.home_calibration, shipped 27 Sep 2026: each season scored with the fit in
    # force for it, seasons before from HOME_CAL_FROM) is the checked table; the raw p_home (the season simulation's chance) is the record, not a check.
    # Both against the closing moneyline (vig removed) where there is one
    def imp(m): m = m.astype(float); return np.where(m < 0, -m / (-m + 100), 100 / (m + 100))
    def vs_line(x, col):
        ml = x[x.home_moneyline.notna() & x.away_moneyline.notna()]; y = ml.hw.values; q = ml[col].clip(1e-6, 1 - 1e-6).values
        ph, pa = imp(ml.home_moneyline), imp(ml.away_moneyline); pv = ph / (ph + pa)
        ll = lambda q_: float(-np.mean(y * np.log(q_) + (1 - y) * np.log(1 - q_))) if len(y) else np.nan
        return f"Against the moneyline ({len(ml)} games): Brier model {np.mean((q - y) ** 2):.4f}, line {np.mean((pv - y) ** 2):.4f}; log loss model {ll(q):.4f}, line {ll(pv):.4f}."
    ch = P.home_calibrations(p, g); hfit = {s_ for s_, c in ch.items() if c[2] >= P.HOME_CAL_MIN_N}   # seasons with a fitted mapping (the first two priced seasons have none: the identity)
    d["p_home_cal"] = [P.home_cal_p(ch[int(s_)], q) if int(s_) in hfit else np.nan for s_, q in zip(d.season, d.p_home)]
    curh = ch[int(g.season.max())]
    L += ["## Game winner: calibrated home win chance (p_home_cal, the cards' figure) by decile", "",
          f"p_home_cal = logistic(a + b x logit(p_home)), picks.home_calibration: fit on every regular-season game from {P.HOME_CAL_FROM} to the season before the one priced, ties dropped (walk-forward; each season below is scored with the fit in force for it, the identity under {P.HOME_CAL_MIN_N} games, so {int(min(hfit)) if hfit else '?'} is the first season scored). "
          f"Today's fit on {P.HOME_CAL_FROM} to {int(g.season.max()) - 1}: a {curh[0]:+.3f}, b {curh[1]:.3f} on {curh[2]} games (b = 1 and a = 0 would be p_home itself): "
          f"{', '.join(f'{q:.0%} raw reads {P.home_cal_p(curh, q):.1%}' for q in (0.35, 0.45, 0.55, 0.65, 0.75))}. Ties count half. The season simulation (season.py) still reads the raw chance.", ""]
    for w, (a, b) in CAL_WINDOWS:
        x = d[d.season.between(a, b) & d.p_home_cal.notna()]
        if not len(x): continue
        t = _cal_table(x, x.p_home_cal, "p_home_cal", "hw", np.arange(0, 1.01, 0.1)); note("home win", w, t)
        L += [f"**{w}** ({int(x.season.min())} to {int(x.season.max())} scored): {len(x)} games, said {x.p_home_cal.mean():.3f} home, happened {x.hw.mean():.3f}. {vs_line(x, 'p_home_cal')}", ""] + _cal_md(t) + [""]
    # the mapping against the raw chance it replaced: log loss and Brier per window (the audit's test, on which it shipped), and the mapped slight-underdog buckets
    L += ["### The mapping against the raw chance: log loss and Brier (lower is better), and the mapped 0.4-0.5 and 0.3-0.4 buckets", "",
          "| Window | Games | Log loss p_home | Log loss p_home_cal | Brier p_home | Brier p_home_cal | Mapped 0.4-0.5 said / happened | Mapped 0.3-0.4 said / happened |", "|---|---|---|---|---|---|---|---|"]
    for w, (a_, b_) in [("2016-18", (2016, 2018)), ("2019-22", (2019, 2022)), ("2020-22", (2020, 2022)), ("2023-25", (2023, 2025))]:
        x = d[d.season.between(a_, b_) & d.p_home_cal.notna()]; y = x.hw.values
        if not len(x): continue
        ll = lambda q_: float(-np.mean(y * np.log(q_) + (1 - y) * np.log(1 - q_))); q0 = x.p_home.clip(1e-6, 1 - 1e-6).values; q1 = x.p_home_cal.clip(1e-6, 1 - 1e-6).values
        ta = _cal_table(x, x.p_home_cal, "p_home_cal", "hw", np.arange(0, 1.01, 0.1))
        cell = lambda k: (f"{ta.loc[k, 'said']:.3f} / {ta.loc[k, 'actual']:.3f} (n {int(ta.loc[k, 'n'])})" if k in ta.index else "")
        L.append(f"| {w} ({int(x.season.min())} to {int(x.season.max())} scored) | {len(x)} | {ll(q0):.5f} | {ll(q1):.5f} | {np.mean((q0 - y) ** 2):.5f} | {np.mean((q1 - y) ** 2):.5f} | {cell(pd.Interval(0.4, 0.5, closed='left'))} | {cell(pd.Interval(0.3, 0.4, closed='left'))} |")
    L.append("")
    L += ["### Raw home win chance (p_home, the season simulation's chance) by decile: the record, not a check", "", "Ties count half.", ""]
    for w, (a, b) in CAL_WINDOWS:
        x = d[d.season.between(a, b)]
        if not len(x): continue
        t = _cal_table(x, x.p_home, "p_home", "hw", np.arange(0, 1.01, 0.1))
        L += [f"**{w}**: {len(x)} games, said {x.p_home.mean():.3f} home, happened {x.hw.mean():.3f}. {vs_line(x, 'p_home')}", ""] + _cal_md(t, fail=False) + [""]
    # 2. the cover chance: the calibrated one on the cards (the mapping the run uses today, fit on CAL_FROM to the season before) and the raw one, by band of the edge
    s = d[d.spread_line.notna()].copy(); s["edge"] = s.model_spread - s.spread_line; s["cm"] = s.result - s.spread_line; s = s[s.cm != 0]
    s["won"] = (np.sign(s.edge) == np.sign(s.cm)).astype(float)
    s["p_raw"] = np.where(s.edge > 0, s.p_cover_home, 1 - s.p_cover_home)
    cal = P.calibration(p, g, int(g.season.max()))[0]; s["p_cal"] = [P.cal_p(cal, e) for e in s.edge]
    bands = ([0, 1, 2, 3, 4, 5, 6, 99], ["0-1", "1-2", "2-3", "3-4", "4-5", "5-6", "6+"])
    L += ["## Spread cover: the model's side, by size of the edge", "", f"Calibrated cover chance = picks.calibration's logistic on |edge| capped at {P.CAL_CAP:g}, fit on {P.CAL_FROM} to {int(g.season.max()) - 1} (intercept {cal[0]:+.3f}, slope {cal[1]:.4f} a point): "
          f"{', '.join(f'{P.cal_p(cal, e):.1%} at {e:g}' for e in (0, 2, 4, 6, 7))}. Raw = the bell curve's own cover chance (p_cover_home; picks file only). Pushes dropped.", ""]
    for w, (a, b) in [("2019-22", P.WINDOWS["2019-22"]), ("2023-25", P.WINDOWS["2023-25"]), ("2019-25", (2019, 2025)), ("2015-18", P.WINDOWS["2015-18"])]:
        x = s[s.season.between(a, b)]
        if not len(x): continue
        t = _cal_table(x, x.edge.abs(), "p_cal", "won", *bands); tr = _cal_table(x, x.edge.abs(), "p_raw", "won", *bands)
        if a >= P.CAL_FROM: note("cover", w, t)
        L += [f"**{w}**{'' if a >= P.CAL_FROM else ' (before the calibration window; not checked)'}: {len(x)} games.", "", "| Edge | Games | Said (calibrated) | Said (raw) | Covered | z (calibrated) | z (raw) |", "|---|---|---|---|---|---|---|"]
        for ix, r in t.iterrows():
            L.append(f"| {ix} | {int(r.n)} | {r.said:.3f} | {tr.loc[ix, 'said']:.3f} | {r.actual:.3f} | {r.z:+.1f}{' **FAIL**' if a >= P.CAL_FROM and r.n >= CAL_MIN_N and abs(r.z) > CAL_Z else ''} | {tr.loc[ix, 'z']:+.1f} |")
        L.append("")
    # biases: the calibrated chance against the cover rate by side, favourite, total, primetime and division, all games and the flags
    s["side"] = np.where(s.edge > 0, "home side", "away side"); s["fav"] = np.where(s.spread_line == 0, "pick'em", np.where(np.sign(s.edge) == np.sign(s.spread_line), "favourite", "underdog"))
    s["tot"] = pd.qcut(s.total_line, 3, labels=["low total", "mid total", "high total"]).astype(str); s["prime"] = np.where(s.primetime == 1, "primetime", "daytime"); s["div"] = np.where(s.div_game == 1, "divisional", "non-divisional")
    L += ["### Biases: the model's side by situation (said = calibrated chance; flags = edge of 4+)", "", "| Window | Group | Games | Said | Covered | z | Flags | Flags covered |", "|---|---|---|---|---|---|---|---|"]
    for w, (a, b) in P.WINDOWS.items():
        x = s[s.season.between(a, b)]
        for col in ("side", "fav", "tot", "prime", "div"):
            for k, y in x.groupby(col, sort=False):
                if len(y) < 30: continue
                f = y[y.edge.abs() >= P.SPREAD_EDGE]; z = (y.won.mean() - y.p_cal.mean()) / np.sqrt(y.p_cal.mean() * (1 - y.p_cal.mean()) / len(y))
                L.append(f"| {w} | {k} | {len(y)} | {y.p_cal.mean():.3f} | {y.won.mean():.3f} | {z:+.1f} | {len(f)} | {f.won.mean():.3f} |" if len(f) else f"| {w} | {k} | {len(y)} | {y.p_cal.mean():.3f} | {y.won.mean():.3f} | {z:+.1f} | 0 | |")
    L.append("")
    # 3. the over chance: the calibrated one on the cards (picks.over_calibration, shipped 27 Sep 2026: each season scored with the fit in
    # force for it, seasons before from OVER_CAL_FROM) is the checked table; the raw p_over_emp (the totals flag's chance) is the record, not a check
    t_ = d[d.total_line.notna() & d.p_over_emp.notna()].copy(); t_["ov"] = t_.total - t_.total_line; t_ = t_[t_.ov != 0]; t_["over"] = (t_.ov > 0).astype(float)
    co = P.over_calibrations(p, g); fitted = {s_ for s_, c in co.items() if c[2] >= P.OVER_CAL_MIN_N}   # seasons with a fitted mapping (the first priced season has none: the identity)
    t_["p_cal"] = [P.over_cal_p(co[int(s_)], q) if int(s_) in fitted else np.nan for s_, q in zip(t_.season, t_.p_over_emp)]
    cur = co[int(g.season.max())]
    L += ["## Totals: calibrated over chance (p_over_cal, the cards' figure) by decile", "",
          f"p_over_cal = logistic(a + b x logit(p_over_emp)), picks.over_calibration: fit on every regular-season game from {P.OVER_CAL_FROM} to the season before the one priced (walk-forward; each season below is scored with the fit in force for it, so {int(min(fitted)) if fitted else '?'} is the first season scored). "
          f"Today's fit on {P.OVER_CAL_FROM} to {int(g.season.max()) - 1}: a {cur[0]:+.3f}, b {cur[1]:.3f} on {cur[2]} games (b = 1 and a = 0 would be p_over_emp itself): "
          f"{', '.join(f'{q:.0%} raw reads {P.over_cal_p(cur, q):.1%}' for q in (0.35, 0.45, 0.55, 0.65))}. Pushes dropped. The totals flag (an under at {P.TOTAL_SHADOW['prob']:.0%}+) stays on the raw chance.", ""]
    for w, (a_, b_) in CAL_WINDOWS:
        x = t_[t_.season.between(a_, b_) & t_.p_cal.notna()]
        if not len(x): continue
        t = _cal_table(x, x.p_cal, "p_cal", "over", np.arange(0, 1.01, 0.1)); note("over", w, t)
        L += [f"**{w}** ({int(x.season.min())} to {int(x.season.max())} scored): {len(x)} games, said {x.p_cal.mean():.3f} over, happened {x.over.mean():.3f}.", ""] + _cal_md(t) + [""]
    # the mapping against the raw chance it replaced: log loss and Brier per window (the audit's test, on which it shipped)
    L += ["### The mapping against the raw chance: log loss and Brier (lower is better), and the mapped 0.5-0.6 and 0.4-0.5 buckets", "",
          "| Window | Games | Log loss p_over_emp | Log loss p_over_cal | Brier p_over_emp | Brier p_over_cal | Mapped 0.5-0.6 said / happened | Mapped 0.4-0.5 said / happened |", "|---|---|---|---|---|---|---|---|"]
    for w, (a_, b_) in [("2016-18", (2016, 2018)), ("2019-22", (2019, 2022)), ("2020-22", (2020, 2022)), ("2023-25", (2023, 2025))]:
        x = t_[t_.season.between(a_, b_) & t_.p_cal.notna()]; y = x.over.values
        if not len(x): continue
        ll = lambda q_: float(-np.mean(y * np.log(q_) + (1 - y) * np.log(1 - q_))); q0 = x.p_over_emp.clip(1e-6, 1 - 1e-6).values; q1 = x.p_cal.clip(1e-6, 1 - 1e-6).values
        ta = _cal_table(x, x.p_cal, "p_cal", "over", np.arange(0, 1.01, 0.1))
        cell = lambda k: (f"{ta.loc[k, 'said']:.3f} / {ta.loc[k, 'actual']:.3f} (n {int(ta.loc[k, 'n'])})" if k in ta.index else "")
        L.append(f"| {w} | {len(x)} | {ll(q0):.5f} | {ll(q1):.5f} | {np.mean((q0 - y) ** 2):.5f} | {np.mean((q1 - y) ** 2):.5f} | {cell(pd.Interval(0.5, 0.6, closed='left'))} | {cell(pd.Interval(0.4, 0.5, closed='left'))} |")
    L.append("")
    L += ["### Raw over chance (p_over_emp, the totals flag's chance) by decile: the record, not a check", "", "Pushes dropped. p_over (the normal curve, picks file only) is quoted for reference.", ""]
    for w, (a_, b_) in CAL_WINDOWS:
        x = t_[t_.season.between(a_, b_)]
        if not len(x): continue
        t = _cal_table(x, x.p_over_emp, "p_over_emp", "over", np.arange(0, 1.01, 0.1))
        L += [f"**{w}**: {len(x)} games, said {x.p_over_emp.mean():.3f} over (normal curve {x.p_over.mean():.3f}), happened {x.over.mean():.3f}.", ""] + _cal_md(t, fail=False) + [""]
    tt = d[d.total_line.notna()].copy(); tt["third"] = pd.qcut(tt.total_line, 3, labels=["low", "mid", "high"])
    L += ["### Model total against the actual total, by third of the line (bias = said minus happened)", "", "| Window | Third | Games | Line | Model | Actual | Bias model | Bias line | MAE model | MAE line |", "|---|---|---|---|---|---|---|---|---|---|"]
    for w, (a, b) in P.WINDOWS.items():
        x = tt[tt.season.between(a, b)]
        for k, y in x.groupby("third", observed=True):
            L.append(f"| {w} | {k} | {len(y)} | {y.total_line.mean():.1f} | {y.model_total.mean():.1f} | {y.total.mean():.1f} | {y.total_err.mean():+.2f} | {y.v_total_err.mean():+.2f} | {y.total_err.abs().mean():.2f} | {y.v_total_err.abs().mean():.2f} |")
    L.append("")
    # 4. the margin scale: the stated sigma against the realised spread of result minus the model spread, and interval coverage
    L += ["## Margin scale: stated sigma against the realised miss, and how much of it the 50 / 80 / 95% intervals hold", "", "| Window | Games | Sigma stated | Realised SD | Mean miss (result minus model) | Line's SD | 50% holds | 80% holds | 95% holds |", "|---|---|---|---|---|---|---|---|---|"]
    for w, (a, b) in P.WINDOWS.items():
        x = d[d.season.between(a, b)]; r = x.result - x.model_spread; z = r / x.sigma_margin
        L.append(f"| {w} | {len(x)} | {x.sigma_margin.mean():.2f} | {r.std():.2f} | {r.mean():+.2f} | {(x.result - x.spread_line).std():.2f} | {np.mean(np.abs(z) <= 0.6745):.3f} | {np.mean(np.abs(z) <= 1.2816):.3f} | {np.mean(np.abs(z) <= 1.96):.3f} |")
    L.append("")
    # 5. team points by tier of the expected score (both sides)
    long = pd.concat([d.assign(exp=d.home_exp, sc=d.home_score), d.assign(exp=d.away_exp, sc=d.away_score)])
    long["tier"] = pd.cut(long.exp, [0, 18, 21, 24, 27, 99], labels=["under 18", "18-21", "21-24", "24-27", "27+"])
    L += ["## Team points by tier of the expected score (bias = said minus scored; z on the scores' own spread)", "", "| Window | Tier | Sides | Said | Scored | Bias | z |", "|---|---|---|---|---|---|---|"]
    for w, (a, b) in P.WINDOWS.items():
        x = long[long.season.between(a, b)]
        for k, y in x.groupby("tier", observed=True):
            bias = (y.exp - y.sc).mean(); L.append(f"| {w} | {k} | {len(y)} | {y.exp.mean():.2f} | {y.sc.mean():.2f} | {bias:+.2f} | {bias / (y.sc.std() / np.sqrt(len(y))):+.1f} |")
    L.append("")
    # 6. season odds reliability (reports/season_calibration.csv, written by the season backtest)
    scf = REP / "season_calibration.csv"
    if scf.exists():
        sc = pd.read_csv(scf); sc["se"] = np.sqrt(sc.said.clip(0.001, 0.999) * (1 - sc.said.clip(0.001, 0.999)) / sc.n); sc["z"] = (sc.happened - sc.said) / sc.se
        big = sc[(sc.n >= 30) & (sc.z.abs() >= 2)]
        L += ["## Season odds (reports/season_calibration.csv): bands of 30+ teams more than 2 SE out", "", f"{int((sc.n >= 30).sum())} bands with 30+ teams; {len(big)} more than 2 SE from what was said.", "", "| Odds | Window | Band | Teams | Said | Happened | z |", "|---|---|---|---|---|---|---|"]
        L += [f"| {r.odds} | {r.window} | {r.band_from:g}-{r.band_to:g} | {int(r.n)} | {r.said:.3f} | {r.happened:.3f} | {r.z:+.1f} |" for r in big.itertuples()] + [""]
    else:
        L += ["## Season odds", "", "reports/season_calibration.csv is missing; not audited.", ""]
    # 7. the graded player props (data/tracker/props_graded.csv): signed error and MAE per stat, the ratio scored / said by tier of the projection
    pgf = TR / "props_graded.csv"
    if pgf.exists():
        pg = pd.read_csv(pgf); pg = pg[pg.actual.notna()]
        wk_ = pg.groupby(["season", "week"]).size(); made = ", ".join(sorted(pg.made.dropna().astype(str).unique())) if "made" in pg.columns else "unknown"
        L += ["## Player props (data/tracker/props_graded.csv)", "", f"{len(pg)} graded projections over {len(wk_)} week(s) ({', '.join(f'{s}-W{w}' for s, w in wk_.index)}); made: {made}. Ratio = total scored / total said; tiers are thirds of the projection within each stat. Bias = said minus scored, z on its own spread. Too short a record for a failing check.", "",
              "| Stat | Rows | Said | Scored | Bias | z | MAE | Ratio | Ratio low tier | Ratio mid | Ratio high |", "|---|---|---|---|---|---|---|---|---|---|---|"]
        for st_, x in pg.groupby("stat"):
            e = x.proj - x.actual; rat = lambda y: f"{y.actual.sum() / y.proj.sum():.2f}" if y.proj.sum() > 0 else ""
            try: tier = pd.qcut(x.proj, 3, labels=["low", "mid", "high"], duplicates="drop")
            except Exception: tier = pd.Series("all", index=x.index)
            tiers = {k: rat(y) for k, y in x.groupby(tier, observed=True)}
            L.append(f"| {st_} | {len(x)} | {x.proj.mean():.2f} | {x.actual.mean():.2f} | {e.mean():+.2f} | {(e.mean() / (e.std() / np.sqrt(len(x)))) if len(x) > 1 and e.std() > 0 else 0:+.1f} | {e.abs().mean():.2f} | {rat(x)} | {tiers.get('low', '')} | {tiers.get('mid', '')} | {tiers.get('high', '')} |")
        L.append("")
    else:
        L += ["## Player props", "", "data/tracker/props_graded.csv is missing; not audited.", ""]
    L += [f"Result: {'PASS' if not any(fails.values()) else 'FAIL'} ({', '.join(f'{k}: {len(v)} bucket(s) out' for k, v in fails.items())})", ""]
    (REP / "calibration_audit.md").write_text("\n".join(L))
    rows.append((f"calibration: calibrated home win chance (p_home_cal, the cards' figure) by decile = the home win rate (regular season, per window and pooled, each season with the fit in force for it; buckets of {CAL_MIN_N}+ games within {CAL_Z:g} SE)", "; ".join(fails["home win"])[:200] or "all within", "all within", not fails["home win"]))
    rows.append((f"calibration: calibrated cover chance by band of the edge = the cover rate of the model's side ({P.CAL_FROM} on, the calibration window, and pooled; buckets of {CAL_MIN_N}+ games within {CAL_Z:g} SE)", "; ".join(fails["cover"])[:200] or "all within", "all within", not fails["cover"]))
    rows.append((f"calibration: calibrated over chance (p_over_cal, the cards' figure) by decile = the over rate (regular season, per window and pooled, each season with the fit in force for it; buckets of {CAL_MIN_N}+ games within {CAL_Z:g} SE)", "; ".join(fails["over"])[:200] or "all within", "all within", not fails["over"]))


def check_run(rows, g) -> None:
    """The weekly run itself: every step finished, every backtest the pages quote was re-run on today's inputs, and the
    live re-price uses the same function and fit as the model run (26 Sep 2026)."""
    rl = ROOT / "data" / "runs" / "run_log.csv"
    if rl.exists():   # a failed step keeps its old file, so it must fail the health check until a run succeeds (P6)
        r_ = pd.read_csv(rl); last = r_[r_.run_at == r_.run_at.iloc[-1]]
        bad = [f"{x.step}: {str(x.detail)[:60]}" for x in last.itertuples() if x.status != "ok"]
        rows.append((f"every step of the newest weekly run finished ({last.run_at.iloc[0]}, {len(last)} steps so far)", "; ".join(bad)[:160] or "all ok", "all ok", not bad))
    from . import weekly as WK
    st = json.loads(WK.STAMPS.read_text()) if WK.STAMPS.exists() else {}
    stale = []
    for name, (mod, ins) in WK.BACKTESTS.items():
        now = WK.input_hashes(ins); was = (st.get(name) or {}).get("inputs", {})
        ch = [k.split("/")[-1] for k in ins if was.get(k) != now[k]]
        if ch:
            stale.append(f"{name} ({', '.join(ch)})")
    rows.append(("backtests the pages quote were re-run on the current model, predictions and code (inputs changed since)", "; ".join(stale)[:160] or "all current", "all current", not stale))
    from . import lines as LN
    s_, w_ = LN.current_week(g)
    dist = M.load_dist(s_, w_); pw = pd.read_parquet(OUT / "pred_v3.parquet"); pw = pw[(pw.season == s_) & (pw.week == w_)]
    if dist is None:
        rows.append(("the fit that priced this week is on file (pred_v3_dist.json), so the picks re-price the live line with it", "missing", "on file", False))
    else:   # the model run's own chances at the schedule's line, rebuilt from the file: the same function and the same fit
        worst = max([abs(M.price_at(r.model_spread, r.model_total, r.spread_line, r.total_line, dist)[k] - getattr(r, k)) for r in pw.itertuples() for k in ("p_home", "p_cover_home", "p_over", "p_over_emp") if pd.notna(getattr(r, k))] or [0.0])
        rows.append((f"the live re-price (model.price_at on pred_v3_dist.json) rebuilds the model run's win, cover and over chances at the schedule's line ({len(pw)} games, worst gap)", f"{worst:.2e}", "1e-9 or under", worst <= 1e-9))


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
        side_ = "home" if r.home == 1 else "away"; exp = float(pw.loc[r.game_id, f"{side_}_exp"]) - float(pw.loc[r.game_id, f"{side_}_blend_adj"] if f"{side_}_blend_adj" in pw.columns else 0.0) - float(pw.loc[r.game_id, f"{side_}_total_adj"] if f"{side_}_total_adj" in pw.columns else 0.0)   # the equation's share; the blend's pull sits on top
        worst = max(worst, abs(e - exp)); n += 1
    rows.append((f"season simulation's equation on the as-of profiles rebuilds the equation's expected points for the week being priced (the blend's pull excluded) ({n} sides, worst gap in points)", round(worst, 4), "0.01 or under", worst <= 0.01))


def check_page_facts(rows, meta: dict, wk: dict) -> None:
    """Every fact the page's text quotes from meta.js, week.js, season.js, rankings.js and props_record.js, against the
    module or report that produces it (26 Sep 2026: the page had typed them, and several had gone stale)."""
    def tie(what, a, b): rows.append((what, str(a), str(b), str(a) == str(b)))
    from . import season as SE, player_season as PS, players as PL, positions as PO, pull as PU, lines as LN
    g = pd.read_parquet(OUT / "games.parquet"); p = pd.read_parquet(OUT / "pred_v3.parquet")
    d = B.join(p, g); d = d[(d.game_type == "REG") & d.home_score.notna() & d.spread_line.notna()]
    pk = meta.get("picks", {})
    tie("page rules: the flag's cut, the totals flag, the last week bet = picks.py", [pk.get("spread_edge"), pk.get("total_shadow"), pk.get("last_week")], [P.SPREAD_EDGE, P.TOTAL_SHADOW, P.LAST_BET_WEEK])
    tie("page rules: break-even at the default price = picks.break_even", [pk.get("break_even"), pk.get("default_odds")], [round(P.break_even(), 4), P.DEFAULT_ODDS])
    tie("page rules: backtest windows = picks.WINDOWS (with the words the reports use)", [(w["key"], w["from"], w["to"], w["label"]) for w in pk.get("windows", [])], [(k, a, b, P.WINDOW_LABEL[k]) for k, (a, b) in P.WINDOWS.items()])
    rr = P.rule_records(d)
    tie("Bets tab: every rule's backtest record = picks.rule_records on the prediction table", [[r["rule"]] + [r[w] for w in P.WINDOWS] for r in pk.get("rules", [])], [[r["rule"]] + [r[w] for w in P.WINDOWS] for _, r in rr.iterrows()])
    tie("page flag threshold (meta.js) = week.js flag threshold", pk.get("spread_edge"), wk.get("spread_edge"))
    # the Backtest tab grades the flag and the totals flag itself from backtest.js; its window records must be the rule records
    bk_ = _js("backtest.js"); b_ = pd.DataFrame(bk_["rows"], columns=bk_["cols"]); b_ = b_[(b_.game_type == "REG") & b_.home_score.notna() & (b_.week <= P.LAST_BET_WEEK)]
    def _pg(x):
        e = x.model_spread - x.spread_line; cm = x.home_score - x.away_score - x.spread_line; f = x.spread_line.notna() & (e.abs() >= P.SPREAD_EDGE) & (cm != 0)
        w = int(((e > 0) & (cm > 0) | (e < 0) & (cm < 0))[f].sum()); return f"{w}-{int(f.sum()) - w}"
    def _pt(x):
        t = x.home_score + x.away_score; f = x.total_line.notna() & (t != x.total_line) & x.p_over_emp.notna() & ((1 - x.p_over_emp) >= P.TOTAL_SHADOW["prob"])
        w = int((t < x.total_line)[f].sum()); return f"{w}-{int(f.sum()) - w}"
    rri = rr.set_index("rule")
    tie("Backtest tab's flag and totals-flag records (from backtest.js) = picks.rule_records, every window", [[_pg(b_[b_.season.between(a, z)]), _pt(b_[b_.season.between(a, z)])] for a, z in P.WINDOWS.values()],
        [[rri.loc["model", w], rri.loc["shadowunder", w]] for w in P.WINDOWS])
    s_, w_ = LN.current_week(g); x = p[(p.season == s_) & (p.week == w_)]
    fit = wk.get("fit") or {}
    if len(x):
        tie("week.js fit (points if out, points a game, the inputs table) = pred_v3's fit for the week (intercept, QB, skill out)", [fit.get("intercept"), (fit.get("per_unit") or {}).get("qb_rating"), (fit.get("per_unit") or {}).get("skill_out_value"), fit.get("sigma_margin")],
            [round(float(x.iloc[0]["intercept"]), 6), round(float(x.iloc[0]["coef_qb_rating"]), 6), round(float(x.iloc[0]["coef_skill_out_value"]), 6), round(float(x.iloc[0]["sigma_margin"]), 6)])
        tie("every card's fit = the week's one fit", sorted({json.dumps(g_.get("coefs"), sort_keys=True) == json.dumps({k: fit.get(k) for k in ("per_unit", "mean", "intercept")}, sort_keys=True) for g_ in wk.get("games", []) if g_.get("coefs")}), [True])
    tie("week.js calibration window = picks.CAL_FROM, CAL_CAP", [(wk.get("cal") or {}).get("from"), (wk.get("cal") or {}).get("cap")], [P.CAL_FROM, P.CAL_CAP])
    # the over calibration (27 Sep 2026): the week's coefficients on the page are the picks' fit, and every backtest season carries the fit in force for it
    co_ = P.over_calibration(p, g, s_); ov_ = ((wk.get("cal") or {}).get("over") or {})
    tie("week.js over calibration (cal.over) = picks.over_calibration for the week (a, b, from, before, n, clip)", [ov_.get(k) for k in ("a", "b", "from", "before", "n", "clip")], [round(co_[0], 6), round(co_[1], 6), P.OVER_CAL_FROM, s_, co_[2], P.OVER_CAL_CLIP])
    bfull = pd.DataFrame(bk_["rows"], columns=bk_["cols"])
    if "p_over_cal" in bfull.columns:
        co_all = P.over_calibrations(p, g); bb = bfull[bfull.p_over_emp.notna() & bfull.p_over_cal.notna()]
        worst = max([abs(P.over_cal_p(co_all[int(s)], q) - v) for s, q, v in zip(bb.season, bb.p_over_emp, bb.p_over_cal) if int(s) in co_all] or [0.0])
        rows.append(("backtest.js calibrated over chance = picks.over_calibrations as of each season, on the file's own raw chance (worst gap)", round(worst, 7), "0.00001 or under", worst <= 1e-5))
    else:
        tie("backtest.js carries the calibrated over chance (p_over_cal)", "missing", "present")
    # the home win calibration (27 Sep 2026): the week's coefficients on the page are the picks' fit, and every backtest season carries the fit in force for it
    chh = P.home_calibration(p, g, s_); hm_ = ((wk.get("cal") or {}).get("home") or {})
    tie("week.js home win calibration (cal.home) = picks.home_calibration for the week (a, b, from, before, n, clip)", [hm_.get(k) for k in ("a", "b", "from", "before", "n", "clip")], [round(chh[0], 6), round(chh[1], 6), P.HOME_CAL_FROM, s_, chh[2], P.HOME_CAL_CLIP])
    if "p_home_cal" in bfull.columns:
        ch_all = P.home_calibrations(p, g); bh = bfull[bfull.p_home.notna() & bfull.p_home_cal.notna()]
        worst = max([abs(P.home_cal_p(ch_all[int(s)], q) - v) for s, q, v in zip(bh.season, bh.p_home, bh.p_home_cal) if int(s) in ch_all] or [0.0])
        rows.append(("backtest.js calibrated home win chance = picks.home_calibrations as of each season, on the file's own raw chance (worst gap)", round(worst, 7), "0.00001 or under", worst <= 1e-5))
    else:
        tie("backtest.js carries the calibrated home win chance (p_home_cal)", "missing", "present")
    feats = M.with_trends(pd.read_parquet(OUT / "features_asof.parquet"))
    q = M.qb_overlap(M.prep(feats), max(int(k) for k in meta["coefs"]))
    tie("QB rating and offense rating overlap on the page = model.qb_overlap (the fit)", meta["analysis"].get("qb_overlap"), q)
    au = (REP / "audit.md").read_text() if (REP / "audit.md").exists() else ""
    nz = meta["analysis"].get("noise") or {}
    tie("the page's noise figure = reports/audit.md's noise floor", f"plus or minus {nz.get('tune', 0):.3f} points wide on the tuning window" in au, True)
    mc = meta.get("model", {})
    tie("the model's stand-in wind (meta.js) = the season simulation's (season.WIND_FAR)", mc.get("wind_fill"), SE.WIND_FAR)
    tie("the model's constants on the page = model.py", [mc.get("ridge"), mc.get("train_from"), mc.get("early_weeks"), mc.get("late_week"), mc.get("dead_pct"), mc.get("cold_f")], [M.RIDGE, M.TRAIN_FROM, M.EARLY_WEEKS, M.LATE_WEEK, M.DEAD_PCT, M.COLD_F])
    pm = meta.get("player_model", {})
    tie("the player model's settings on the page = players.DEFAULT, positions (replacement, starters), ratings.DEFAULT", [pm.get("decay"), pm.get("k"), pm.get("usage_games"), pm.get("skill_pct"), pm.get("repl_pct"), pm.get("qb_prior"), pm.get("starters"), pm.get("starters_def"), pm.get("starter_qb_games")],
        [PL.DEFAULT["decay"], PL.DEFAULT["k"], PL.DEFAULT["usage_games"], PL.DEFAULT["pct"], PO.REPL_PCT, R.DEFAULT["qb_prior"], PO.STARTERS, PO.STARTERS_DEF, PO.STARTER_QB_GAMES])
    tie("data sources' first seasons on the page = pull.DATASETS", meta.get("data_from"), {k: v[1] for k, v in PU.DATASETS.items()})
    sj = _js("season.js")
    tie("season.js league tie rate = the schedule (season.league_tie_rate)", sj.get("tie_rate_league"), SE.league_tie_rate(g))
    tie("season.js accuracy cut (top of each list) = player_season.TOPW", (sj.get("players") or {}).get("topw"), PS.TOPW)
    bg = REP / "season_by_game.csv"
    if bg.exists():
        b_ = pd.read_csv(bg)
        tie("season.js game-by-game test = reports/season_by_game.csv (rows, misses)", [len(sj.get("by_game", [])), round(sum(r["mae"] for r in sj.get("by_game", [])), 1)], [len(b_), round(float(b_.mae.sum()), 1)])
    rk = _js("rankings.js"); mx = rk.get("matchup") or {}
    ls = str(max(int(k) for k in rk["seasons"])); lw = str(max(int(k) for k in rk["seasons"][ls])); tm = sorted(rk["seasons"][ls][lw]["teams"])
    tie("Rankings matchup: priced for the latest ratings table, every pair of teams", [mx.get("season"), mx.get("week"), sum(len(v) for v in (mx.get("pts") or {}).values())], [int(ls), int(lw), len(tm) * (len(tm) - 1)])
    pr = _js("props_record.js"); vm = TR / "props_vs_market.csv"
    if vm.exists():
        from .props import market_summary
        tie("props record summary on the page = props.market_summary(props_vs_market.csv)", pr.get("summary"), json.loads(json.dumps(market_summary(pd.read_csv(vm)))))
    else:
        tie("props record summary absent while no line is graded", pr.get("summary"), None)


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
    # the report's records: the flagged games' records = the rule records' three windows added up (one grading)
    _rr, _rp = wk.get("rule_records") or {}, wk.get("report_records") or {}
    if _rr and _rp:
        _sum = lambda k: [sum(int(v.split("-")[0]) for v in _rr[k].values()), sum(int(v.split("-")[1]) for v in _rr[k].values())]
        tie("report records: spread flag and totals flag = the rule records' three windows added up", [_rp["spread"]["flag"], _rp["total"]["flag"]], [_sum("model"), _sum("shadowunder")])
    # the report's injury lines: each unplayed game's priced players add up to the model's injury inputs on the spread
    # (skill value and offensive snaps on the player's side, defensive snaps in the opponent's equation)
    _ig = []
    for g in (wk.get("games") or []):
        if g.get("home_score") is not None or not g.get("coefs"):
            continue
        co = g["coefs"]["per_unit"]
        for t, o in ((g["home_team"], g["away_team"]), (g["away_team"], g["home_team"])):
            sd, so = g["sides"].get(t, {}), g["sides"].get(o, {})
            if "injuries" not in sd:
                _ig.append(f"{g['game_id']} {t}: no injury list"); continue
            eff = (co["skill_out_value"] - co["opp_skill_out_value"]) * (sd.get("skill_out_value") or 0) + co["off_snap_out"] * (sd.get("off_snap_out") or 0) - co["opp_def_snap_out"] * (so.get("opp_def_snap_out") or 0)
            lst = sum(x["spread_pts"] for x in sd["injuries"] if x["priced"])
            if abs(eff - lst) > 0.05:
                _ig.append(f"{g['game_id']} {t}: inputs {eff:.2f}, players {lst:.2f}")
    tie("report injury lines add up to the model's injury inputs (every unplayed game, within 0.05)", _ig, [])
    # the card and deep-dive breakdowns: intercept + sum of coefficient x (input - training mean) from the page's own files = the model's expected points
    SIT = set(M.SIT_FEATS) | {"qb_out"} | set(M.INJ_FEATS) | set(M.CONT_FEATS) | set(M.LATE_FEATS)
    def rebuild(co, inputs):
        tot = co["intercept"]
        for f in M.FEATS:
            v = inputs.get(f); c = co["per_unit"][f]; mu = co["mean"][f]
            if v is None: return None
            tot += c * (v - mu)   # the page moves the situational means into its base; the sum is the same
        return tot + (inputs.get("blend_adj") or 0.0) + (inputs.get("total_adj") or 0.0)   # the other six models' average pull (the blend) and the share-out to the game total (25 Sep 2026)
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
                    if "m_blend_adj" in cols: inputs["blend_adj"] = row[cols.index("m_blend_adj")]
                    if "m_total_adj" in cols: inputs["total_adj"] = row[cols.index("m_total_adj")]
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
        # 0.0006: the page carries the cover odds and the edge to 3 decimals, so the odds' own rounding alone reaches 0.0005 and the edge's adds a little (25 Sep 2026: a 0.00050x gap failed the run)
        rows.append(("card calibration on the page reproduces the run's calibrated cover odds at the run's line (worst gap)", round(worst, 5), "0.0006 or under", worst <= 0.0006))
        # the calibrated over chance on each card (27 Sep 2026) = week.js cal.over on the card's own raw chance (three decimals on the page, so 0.0002 of gap is its rounding)
        ov = wk["cal"].get("over") or {}
        def cal_o(q): q = min(max(q, ov["clip"]), 1 - ov["clip"]); return 1 / (1 + math.exp(-(ov["a"] + ov["b"] * math.log(q / (1 - q)))))
        worst = max([abs(cal_o(g["p_over_emp"]) - g["p_over_cal"]) for g in wk["games"] if ov and g.get("p_over_emp") is not None and g.get("p_over_cal") is not None] or [0.0])
        rows.append(("card calibrated over chance = week.js cal.over on the card's raw over chance (worst gap)", round(worst, 5), "0.0006 or under", bool(ov) and worst <= 0.0006))
        # the calibrated win chance on each card (27 Sep 2026) = week.js cal.home on the card's own raw p_home (both at six decimals, so the gap is the arithmetic's)
        hc = wk["cal"].get("home") or {}
        def cal_h(q): q = min(max(q, hc["clip"]), 1 - hc["clip"]); return 1 / (1 + math.exp(-(hc["a"] + hc["b"] * math.log(q / (1 - q)))))
        worst = max([abs(cal_h(g["p_home"]) - g["p_home_cal"]) for g in wk["games"] if hc and g.get("p_home") is not None and g.get("p_home_cal") is not None] or [0.0])
        rows.append(("card calibrated win chance = week.js cal.home on the card's raw win chance (worst gap)", round(worst, 5), "0.0006 or under", bool(hc) and worst <= 0.0006))
    if pk_f.exists() and "games" in wk:
        pk = pd.read_csv(pk_f).set_index("game_id")
        pg = {x["game_id"]: x for x in wk["games"]}
        tie("page week = picks file (games)", sorted(pg), sorted(pk.index))
        # the picks file is the weekly run's (what it logged); the card's flag follows the line, so the flags are tied to the
        # tracker (bet_recorded) and to the rule on the card's own edge below, not to this file
        tie("page week = picks file (model spread)", round(float(max(abs((pg[k]["model_spread"] or 0) - pk.loc[k, "model_spread"]) for k in pg if k in pk.index)), 3), 0.0)
    if wk.get("games"):
        check_live(rows, wk)
    tr = _js("track.js"); mp = pd.read_csv(TR / "model_picks.csv") if (TR / "model_picks.csv").exists() else pd.DataFrame()
    if len(mp):
        cur = mp[(mp.season == season) & (mp.week == week)]
        tie("page live table = tracker (pending model rows)", sorted(x["bet"] for x in tr if x.get("who") == "model" and x.get("season") == season and x.get("week") == week), sorted(cur.bet))
    try:
        check_page_facts(rows, meta, wk)
    except Exception as e:  # noqa
        rows.append(("page facts (rules, fit, constants)", str(e)[:80], "", False))
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


def check_live(rows, wk) -> None:
    """The cards display what Python priced (26 Sep 2026: the page re-priced the line itself, so no check could see
    it). week.js's line is the lines log's consensus now; the edges, chances, flags and stake follow from it; the
    recorded bet is the tracker's; the props re-project on the same line and carry one book line per player-stat."""
    from . import lines as LN, model as M_
    def tie(what, a, b): rows.append((what, str(a), str(b), str(a) == str(b)))
    G = wk["games"]; log = LN.load_log()
    want = {}
    for g_ in G:
        h = log[log.game_id == g_["game_id"]]; sl, _ = LN.latest(h, "home_spread"); tl, _ = LN.latest(h, "total")
        want[g_["game_id"]] = [sl, tl]
    tie("card line = the lines log's consensus now (newest snapshot per game, median across sources, to the half point)", {k: [g_["spread_line"], g_["total_line"]] for g_ in G for k in [g_["game_id"]] if want[k] != [None, None]}, {k: v for k, v in want.items() if v != [None, None]})
    worst = max([abs(g_["model_spread"] - g_["spread_line"] - g_["spread_edge"]) for g_ in G if g_.get("spread_line") is not None] + [abs(g_["model_total"] - g_["total_line"] - g_["total_edge"]) for g_ in G if g_.get("total_line") is not None] or [0.0])
    rows.append(("card edges = model minus the card's line (spread and total, worst gap)", round(worst, 4), "0.002 or under", worst <= 0.002))
    dist = M_.load_dist(wk["season"], wk["week"])
    if dist is not None:
        worst = 0.0
        for g_ in G:
            pr = M_.price_at(g_["model_spread"], g_["model_total"], g_.get("spread_line"), g_.get("total_line"), dist)
            for k in ("p_home", "p_cover_home", "p_over_emp"):
                if g_.get(k) is not None and pd.notna(pr[k]): worst = max(worst, abs(pr[k] - g_[k]))
        rows.append(("card chances (win, cover, over) = the model's fit priced at the card's line (worst gap; three decimals on the page)", round(worst, 5), "0.0006 or under", worst <= 0.0006))
    # the live flag: the rule on the card's own numbers (weeks 1 to 17)
    fl = {g_["game_id"]: ((g_["home_team"] if g_["spread_edge"] > 0 else g_["away_team"]) if g_.get("spread_edge") is not None and abs(g_["spread_edge"]) >= wk["spread_edge"] and g_["week"] < 18 else "") for g_ in G}
    tie("card flag = the flag rule on the card's edge (side flagged, weeks 1 to 17)", {g_["game_id"]: (g_.get("bet") or "").split(" ")[0] for g_ in G}, fl)
    pu = wk["total_shadow"]["prob"]
    fu = {g_["game_id"]: bool(g_.get("p_over_emp") is not None and g_.get("total_line") is not None and 1 - g_["p_over_emp"] >= pu - 0.0005 and g_["week"] < 18) for g_ in G}
    near = {g_["game_id"] for g_ in G if g_.get("p_over_emp") is not None and abs(1 - g_["p_over_emp"] - pu) < 0.0006}   # at the cut to three decimals: either reading holds
    tie(f"card totals flag = an under at a {pu:.0%}+ chance on the card's own over chance (p_over_emp)", {k: bool(g_.get("shadowunder_bet")) for g_ in G for k in [g_["game_id"]] if k not in near}, {k: v for k, v in fu.items() if k not in near})
    mp = pd.read_csv(TR / "model_picks.csv") if (TR / "model_picks.csv").exists() else pd.DataFrame(columns=["season", "week", "game_id", "bet"])
    cur = mp[(mp.season == wk["season"]) & (mp.week == wk["week"])]
    tie("card recorded bet = the tracker's logged picks (game, bet)", sorted(f"{g_['game_id']} {b['bet']}" for g_ in G for b in g_.get("bet_recorded", [])), sorted(f"{r.game_id} {r.bet}" for r in cur.itertuples()))
    vw = {}
    for g_ in G:
        v_, _, _ = LN.vegas_win(log[log.game_id == g_["game_id"]]); vw[g_["game_id"]] = v_
    worst = max([abs((g_.get("vegas_win") or 0) - (vw[g_["game_id"]] or 0)) for g_ in G] or [0.0]); miss = [g_["game_id"] for g_ in G if (g_.get("vegas_win") is None) != (vw[g_["game_id"]] is None)]
    rows.append(("card Vegas win chance = the newest moneyline snapshot, vig removed per book, averaged (worst gap; games missing one side)", f"{worst:.4f}; {len(miss)}", "0.0006 or under; 0", worst <= 0.0006 and not miss))
    fin = [g_["game_id"] for g_ in G if g_.get("runs") and (abs(g_["runs"][-1]["model_spread"] - g_["model_spread"]) > 0.002 or abs(g_["runs"][-1]["model_total"] - g_["model_total"]) > 0.002)]
    rows.append(("each card's run history ends with the run that priced it (model spread and total)", ", ".join(fin) or "all", "all", not fin))
    try:
        sj = _js("season.js"); left = {(t, x[1], x[0]): x[3] for t, xs in sj.get("left", {}).items() for x in xs if x[2] == 1}
        gap = [g_["game_id"] for g_ in G if (g_["home_team"], g_["away_team"], wk["week"]) in left and abs(left[(g_["home_team"], g_["away_team"], wk["week"])] - round(g_["p_home"], 3)) > 0.0015]
        # the season simulation prices each game with the model's raw chance (season.py); the card carries that as p_home and displays p_home_cal (27 Sep 2026)
        rows.append(("season file's chance in each game of the week = the card's raw model win chance, p_home (one function, three decimals; the card displays it calibrated)", ", ".join(gap) or "all equal", "all equal", not gap))
        from . import futures as FU
        tie("season file's books = the newest futures pull", json.dumps(sj.get("books"), sort_keys=True, default=str)[:4000] == json.dumps(json.loads(json.dumps(FU.latest(), default=str)), sort_keys=True, default=str)[:4000], True)
    except Exception as e:  # noqa
        rows.append(("season file against the week", str(e)[:80], "", False))
    from . import weather as WX
    fc = WX.usable_forecast(); bad = []
    for g_ in G:
        if g_.get("home_score") is not None: continue
        for t, sd in (g_.get("sides") or {}).items():
            f_ = fc.loc[g_["game_id"]] if g_["game_id"] in fc.index and not sd.get("dome") else None
            w_ = None if f_ is None or pd.isna(f_.wind) else round(float(f_.wind), 1)
            if sd.get("wind") != w_: bad.append(f"{g_['game_id']} {t}")
    if (OUT / "props.json").exists():   # the props' passing-wind factor reads the same forecast
        pj_ = json.loads((OUT / "props.json").read_text())
        for g_ in G:
            if g_.get("home_score") is not None or g_["game_id"] not in pj_["games"]: continue
            dome = bool((g_.get("sides") or {}).get(g_["home_team"], {}).get("dome"))
            f_ = fc.loc[g_["game_id"]] if g_["game_id"] in fc.index and not dome else None
            w_ = None if f_ is None or pd.isna(f_.wind) else float(f_.wind)
            for t, sd in pj_["games"][g_["game_id"]].items():
                v = sd.get("volume", {}).get("wind")
                if (v is None) != (w_ is None) or (v is not None and abs(v - w_) > 1e-9): bad.append(f"{g_['game_id']} {t} props")
    tie("card and props wind (unplayed games) = the kickoff forecast in use now", bad, [])
    if (OUT / "props.json").exists():
        pj = json.loads((OUT / "props.json").read_text()); gm = {g_["game_id"]: g_ for g_ in G}; off = []
        for gid, sides in pj["games"].items():
            g_ = gm.get(gid)
            if g_ is None: continue
            for t, sd in sides.items():
                v = sd.get("volume", {}); sg = 1 if t == g_["home_team"] else -1
                if g_.get("total_line") is not None and v.get("total") != g_["total_line"]: off.append(f"{gid} {t} total")
                if g_.get("spread_line") is not None and v.get("margin") is not None and abs(v["margin"] - sg * g_["spread_line"]) > 1e-9: off.append(f"{gid} {t} margin")
                for k in sd.get("kicker", []):
                    if g_.get("total_line") is not None and abs(k["implied_total"] - round((g_["total_line"] + sg * g_["spread_line"]) / 2, 2)) > 0.006: off.append(f"{gid} {t} kicker")
        tie("props game script (volume margin and total, kicker implied total) = the card's line", off[:8], [])
        dup, dis = [], []
        for gid, sides in pj["games"].items():
            for t, sd in sides.items():
                for grp, pairs in (("qb", [("pass_yards", "mkt_pass_yards")]), ("receivers", [("rec_yards", "mkt_rec_yards"), ("rec_catches", "mkt_catches")]), ("rushers", [("rush_yards", "mkt_rush_yards")]), ("defenders", [("def_tackles", "mkt_tackles")])):
                    for r in sd.get(grp, []):
                        stats = [m["stat"] for m in r.get("markets", [])]
                        if len(stats) != len(set(stats)): dup.append(r["name"])
                        mm = {m["stat"]: m["line"] for m in r.get("markets", [])}
                        for st_, key in pairs:
                            if r.get(key) is not None and mm.get(st_) != r[key]: dis.append(f"{r['name']} {st_}")
        tie("props: one book line per player-stat (the card's takeaways and the props table read the same one)", sorted(set(dup))[:6] + sorted(set(dis))[:6], [])


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
