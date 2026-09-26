"""Assemble reports/backtest_v3.md: 3.0 against the closing line, tuned on 2019 to 2022,
judged on 2023 to 2025, with the market blend and the threshold sweep on the tuning window only.

Usage: python -m nflmodel.report
"""
from __future__ import annotations
import numpy as np, pandas as pd
from pathlib import Path
from . import backtest as bt

ROOT = Path(__file__).resolve().parent.parent
OUT, REP = ROOT / "data" / "processed", ROOT / "reports"
TUNE, TEST = range(2019, 2023), range(2023, 2026)


def compare_points(new: pd.DataFrame, seasons) -> pd.DataFrame:
    n = new[new.season.isin(seasons) & (new.game_type == "REG") & new.spread_line.notna()]
    pn = bt.points_miss(n).set_index("target")
    return pd.DataFrame({"3.0": pn.model_mae, "Vegas close": pn.vegas_mae, "games": pn.n}).round(2)


def market_blend(new: pd.DataFrame):
    """pred = a * model + (1-a) * line. Fit a on the tuning window by margin MAE, report both windows."""
    d = new[new.game_type == "REG"]
    rows = []
    best_a, best = None, 9e9
    for a in np.round(np.arange(0, 1.01, 0.1), 2):
        t = d[d.season.isin(TUNE)]
        mae = np.abs(a * t.model_spread + (1 - a) * t.spread_line - t.result).mean()
        if mae < best:
            best, best_a = mae, a
        v = d[d.season.isin(TEST)]
        rows.append({"a (model share)": a, "margin MAE 2019-22": mae,
                     "margin MAE 2023-25": np.abs(a * v.model_spread + (1 - a) * v.spread_line - v.result).mean(),
                     "total MAE 2023-25": np.abs(a * v.model_total + (1 - a) * v.total_line - v.total).mean()})
    return best_a, pd.DataFrame(rows).round(3)


def threshold_table(d: pd.DataFrame, kind: str, edges=(1, 2, 3, 4, 5, 6, 7, 8)) -> pd.DataFrame:
    rows = []
    for e in edges:
        b = bt.grade_spread(d, e) if kind == "spread" else bt.grade_total(d, e)
        s = bt.summarize_bets(b).iloc[0]
        rows.append({"edge": e, **s.to_dict()})
    return pd.DataFrame(rows).round(3)


def clv_proxy(d: pd.DataFrame, edge: float) -> str:
    """Closing line value can't be measured yet (only closing lines are stored); say so once."""
    return ("Closing line value is not measurable in this backtest: nflverse stores closing lines only. "
            "It starts being logged from the first live week (open, midweek, close).")


def readme_block(new: pd.DataFrame) -> str:
    """The README's headline table, computed from the same prediction table as everything else, so it can never go stale."""
    from . import picks as P
    d = new[(new.game_type == "REG") & new.spread_line.notna() & new.home_score.notna()].copy()
    d["margin"] = d.home_score - d.away_score
    d["total"] = d.home_score + d.away_score
    d["edge"] = d.model_spread - d.spread_line
    d["tedge"] = d.model_total - d.total_line
    def rec(x, sig, res):
        r = np.sign(res); w = int((r == np.sign(sig)).sum()); l = int(((r != 0) & (r != np.sign(sig))).sum()); return f"{w}-{l}"
    v = d[d.season.isin(TEST)]
    a = d[d.season.between(2019, 2025)]
    tp = lambda x: ((x.home_exp - x.home_score).abs().mean() + (x.away_exp - x.away_score).abs().mean()) / 2
    vp = lambda x: ((x.home_implied - x.home_score).abs().mean() + (x.away_implied - x.away_score).abs().mean()) / 2
    br = bt.brier(v)
    se = P.SPREAD_EDGE
    f5v, f5a = v[v.edge.abs() >= se], a[a.edge.abs() >= se]
    f5n = f5a[f5a.week < 18]
    f3v = v[v.edge.abs() >= 3]
    t4v, t4a = v[v.tedge.abs() >= 4], a[a.tedge.abs() >= 4]
    L = [f"## Headline results (held-out {TEST[0]} to {TEST[-1]}, {len(v)} games)", "",
         "| | 3.0 | Vegas close |", "|---|---|---|",
         f"| Team points miss | {tp(v):.2f} | {vp(v):.2f} |",
         f"| Margin miss | {(v.margin - v.model_spread).abs().mean():.2f} | {(v.margin - v.spread_line).abs().mean():.2f} |",
         f"| Total miss | {(v.total - v.model_total).abs().mean():.2f} | {(v.total - v.total_line).abs().mean():.2f} |",
         f"| Brier (win odds) | {br['brier_model']:.3f} | {br['brier_market']:.3f} |",
         f"| Spreads at 3+ pt edge | {rec(f3v, f3v.edge, f3v.margin - f3v.spread_line)} | |",
         f"| Spreads at {se:g}+ pt edge (the flag) | {rec(f5v, f5v.edge, f5v.margin - f5v.spread_line)} (2019 to 2025: {rec(f5a, f5a.edge, f5a.margin - f5a.spread_line)}; {rec(f5n, f5n.edge, f5n.margin - f5n.spread_line)} outside Week 18) | |",
         f"| Totals at 4+ pt edge ({'the flag' if P.TOTAL_EDGE is not None else 'not flagged: no total cutoff wins in both windows'}) | {rec(t4v, t4v.tedge, t4v.total - t4v.total_line)} (2019 to 2025: {rec(t4a, t4a.tedge, t4a.total - t4a.total_line)}) | |", "",
         "These rows are written by `report.py` from the same prediction table as the page and the reports, on every run. "
         "Ridge strength and thresholds were tuned on 2019 to 2022 only; since 22 Sep 2026 new inputs and the rating decay are accepted only when they help on both windows, so 2023 to 2025 is a second test window for those, and the live season is the only fully unseen test."]
    return "\n".join(L)


def update_readme(new: pd.DataFrame):
    p = ROOT / "README.md"
    if not p.exists():
        return
    txt = p.read_text()
    start, end = "<!-- results:start -->", "<!-- results:end -->"
    if start in txt and end in txt:
        a, b = txt.index(start) + len(start), txt.index(end)
        txt = txt[:a] + "\n" + readme_block(new) + "\n" + txt[b:]
        p.write_text(txt)


def _rec_pct(w: int, l: int, show_record: bool) -> str:
    n = w + l
    return (f"{100 * w / n:.1f}%" + (f" ({w}-{l})" if show_record else "")) if n else "no bets"


EFFECT_LABEL = {"off_epa_play": "Own offense EPA per play", "def_epa_play": "Opponent defense EPA per play", "off_pf": "Own offense points rating", "def_pf": "Opponent defense points rating",
                "qb_rating": "Starting QB rating", "home": "Home", "neutral": "Neutral site", "dome": "Dome", "wind_out": "Wind (outdoor), per mph", "cold": "Cold", "rain": "Rain at kickoff",
                "warm_in_cold": "Warm-climate or dome team outdoors in the cold", "div_game": "Division game", "qb_out": "Last game's QB listed out",
                "skill_out_value": "Skill players out: value lost", "opp_skill_out_value": "Opponent's skill players out: value lost", "off_snap_out": "Offensive snaps out",
                "opp_def_snap_out": "Opponent's defensive snaps out", "off_turnover_early": "Offseason turnover, offense", "opp_def_turnover_early": "Opponent's offseason turnover, defense",
                "dead_late": "Out of the race", "opp_dead_late": "Opponent out of the race"}


def effects_tables() -> dict:
    """Docs section 4: every input's points from the fit that priced the week being priced (pred_v3's coefficients, the
    same the cards break down), per unit and per standard deviation of the training games, with the raw gap in the data
    beside each flag (export_web.situation_facts); and the QB rating's overlap with the offense rating (model.qb_overlap).
    Written into the docs on every run, so the section quotes the live fit (26 Sep 2026: it had been typed by hand and
    had gone stale, two signs flipped)."""
    from . import model as M, lines as LN
    from .export_web import situation_facts
    games = pd.read_parquet(OUT / "games.parquet"); pred = pd.read_parquet(OUT / "pred_v3.parquet")
    s, w = LN.current_week(games)
    x = pred[(pred.season == s) & (pred.week == w)]
    feats = M.with_trends(pd.read_parquet(OUT / "features_asof.parquet")); fp = M.prep(feats)
    train = fp[fp.pf.notna() & (fp.season >= M.TRAIN_FROM) & ((fp.season < s) | ((fp.season == s) & (fp.week < w)))]
    sf = situation_facts(feats)
    r0 = x.iloc[0]
    raw = lambda f: (lambda q: f"{q['on']} with it ({q['n_on']:,} team-games), {q['off']} without" if q else "")(sf["flags"].get(f))
    wraw = ""
    if sf.get("wind"):
        wraw = f"{sf['wind'][0]['pf']} points in calm air, {sf['wind'][3]['pf']} at {sf['wind'][3]['bucket']} mph"
    L = [f"| Input | Points per unit | Points per SD | Raw points, {sf['seasons']} |", "|---|---|---|---|"]
    rows = []
    for f in M.FEATS:
        c = float(r0[f"coef_{f}"]); sd = float(train[f].std()) if f in train.columns else float("nan")
        rows.append((abs(c * sd) if sd == sd else 0.0, f"| {EFFECT_LABEL.get(f, f)} | {c:+.3f} | {c * sd:+.2f} | {wraw if f == 'wind_out' else raw(f)} |"))
    L += [r for _, r in sorted(rows, key=lambda t: -t[0])]
    L += ["", f"The fit that priced Week {w} of {s}: {int(r0['n_train']):,} team-games from {M.TRAIN_FROM} on. Points per SD is the unit's worth times the input's "
          "spread in those games, so the inputs can be compared. The flags, the wind in mph and the shares out are measured from zero; the ratings and the QB "
          "from the league average. Raw points: what teams scored with the flag on and off, before any adjustment."]
    q = M.qb_overlap(fp, s)
    qb = (f"The QB rating and the offense EPA rating move together (correlation {q['corr']:.2f} over {q['seasons']}), and the regression sorts that out: "
          f"fitted at once the QB rating is worth {q['qb_per_sd']:+.2f} points per SD and the offense EPA rating {q['off_per_sd']:+.2f}; drop the QB and refit, "
          f"and the offense EPA coefficient rises to {q['off_per_sd_no_qb']:+.2f} per SD, so the credit is shared, not counted twice.")
    return {"effects": "\n".join(L), "qb_overlap": qb}


def docs_tables(new: pd.DataFrame) -> dict:
    """The docs tables that quote backtest records, built from the same files the tie check reads (24 Sep 2026: they
    were typed by hand and went stale after every model change; the staking table was a run behind unnoticed)."""
    from . import picks as P
    out = {}
    try:
        out.update(effects_tables())
    except Exception as e:  # noqa
        print("docs effects table not built:", str(e)[:200], flush=True)
    sw = REP / "threshold_sweep.csv"
    if sw.exists():
        t = pd.read_csv(sw); t = t[t.market == "spread"]
        L = ["| Cut | 2019-22 | 2023-25 | 2015-18 (untouched) | " + " | ".join(str(y) for y in range(2019, 2026)) + " |", "|" + "---|" * 11]
        for cut in (4.0, 4.5, 5.0):
            x = t[t.cut == cut].set_index("window")
            cell = lambda k, pct_only=False: (_rec_pct(int(x.loc[k, "wins"]), int(x.loc[k, "losses"]), (x.loc[k, "wins"] < x.loc[k, "losses"]) or (x.loc[k, "wins"] + x.loc[k, "losses"] < 5))
                                              if pct_only else f"{int(x.loc[k, 'wins'])}-{int(x.loc[k, 'losses'])}, {100 * x.loc[k, 'pct']:.1f}%") if k in x.index else ""
            L.append(f"| {cut:g} | {cell('2019-22')} | {cell('2023-25')} | {cell('2015-18')} | " + " | ".join(cell(str(y), True) for y in range(2019, 2026)) + " |")
        out["threshold"] = "\n".join(L)
    d = new[(new.game_type == "REG") & new.home_score.notna() & new.spread_line.notna()]
    rr = P.rule_records(d)
    out["rules"] = "\n".join(["| Rule | 2015 to 2018 (untouched) | 2019 to 2022 (tuning) | 2023 to 2025 (held out) |", "|---|---|---|---|"] +
                             [f"| {r['label']} | {r['2015-18']} | {r['2019-22']} | {r['2023-25']} |" for _, r in rr.iterrows()])
    bw = bt.by_week(new[new.spread_line.notna()], P.SPREAD_EDGE)
    out["byweek"] = "\n".join([f"| Weeks | Games | Gap to the line | Every game ATS | Flags at {P.SPREAD_EDGE:g} |", "|---|---|---|---|---|"] +
                              [f"| {r.weeks} | {r['games']} | {r['gap']:+.2f} | {r['ats_pct']}% | {r['flags']} ({r['flag_pct']}%) |" for _, r in bw.iterrows()])
    sz = REP / "sizing_backtest.csv"
    if sz.exists():
        z = pd.read_csv(sz); lab = {"2016-18": "2016-18 (never used to choose)", "2019-22": "2019-22 (the threshold was chosen here)", "2023-25": "2023-25 (held out)"}
        L = ["| Window | Record | Units | Drawdown (units) | Quarter Kelly | Chance of this by luck |", "|---|---|---|---|---|---|"]
        for w, name in lab.items():
            f, q = z[(z.window == w) & (z.staking == "flat")], z[(z.window == w) & (z.staking == "kelly_q")]
            if len(f) and len(q):
                f, q = f.iloc[0], q.iloc[0]; pv = 100 * float(f.p_value_vs_break_even)
                L.append(f"| {name} | {f.record} | {f.units_flat:+.1f} | {f.max_drawdown:.1f} | {q.growth_pct:+.1f}% | {pv:.1f}% |" if pv < 10 else
                         f"| {name} | {f.record} | {f.units_flat:+.1f} | {f.max_drawdown:.1f} | {q.growth_pct:+.1f}% | {pv:.0f}% |")
        out["sizing"] = "\n".join(L)
    return out


def update_docs(new: pd.DataFrame):
    """Rewrite each <!-- auto:NAME --> ... <!-- /auto:NAME --> block in docs/how_it_works.md."""
    p = ROOT / "docs" / "how_it_works.md"
    if not p.exists():
        return
    txt = p.read_text()
    for name, body in docs_tables(new).items():
        a, b = f"<!-- auto:{name} -->", f"<!-- /auto:{name} -->"
        if a in txt and b in txt:
            i, j = txt.index(a) + len(a), txt.index(b)
            txt = txt[:i] + "\n" + body + "\n" + txt[j:]
    p.write_text(txt)


def main():
    from . import picks as P
    new = bt.join(pd.read_parquet(OUT / "pred_v3.parquet"))
    L = ["# NFL Model 3.0 backtest", "",
         "Walk-forward: every week is priced with only games played before it; the points regression is refit before every week on every "
         "played game since 2013. Ridge strength and bet thresholds were chosen on 2019 to 2022 only, and 2023 to 2025 was the "
         "held-out test for them. Since 22 Sep 2026 every new input, and the rating decay and last-season weight, is accepted only "
         "when it helps on both windows, so for those choices 2023 to 2025 is a second test window rather than an untouched one; "
         "the live season is the only fully unseen test.", ""]
    L += ["## 1. Points miss (mean absolute error) against Vegas", "",
          "Tuning window 2019 to 2022:", "", compare_points(new, TUNE).to_markdown(), "",
          "Held-out 2023 to 2025:", "", compare_points(new, TEST).to_markdown(), "",
          "Held-out, Week 5 on:", "", compare_points(new[new.week > 4], TEST).to_markdown(), ""]
    for name, seasons in [("2019 to 2022 (tuning)", TUNE), ("2023 to 2025 (held out)", TEST)]:
        d = new[new.season.isin(seasons) & (new.game_type == "REG")]
        bs = bt.brier(d)
        L += [f"## 2. Win probability, {name}", "",
              f"Brier score (lower is better): 3.0 {bs['brier_model']:.4f}, market moneyline {bs['brier_market']:.4f}.", "",
              "3.0 calibration:", "", bt.calibration(d).round(3).to_markdown(), ""]
    d_t = new[new.season.isin(TUNE) & (new.game_type == "REG")]
    d_v = new[new.season.isin(TEST) & (new.game_type == "REG")]
    L += ["## 3. Spreads: threshold sweep on the tuning window (2019 to 2022)", "", threshold_table(d_t, "spread").to_markdown(index=False), "",
          "## 4. Totals: threshold sweep on the tuning window", "", threshold_table(d_t, "total").to_markdown(index=False), ""]
    # lock the sheet's thresholds unless the sweep shows a threshold with 100+ bets and better ROI
    st = threshold_table(d_t, "spread")
    tt = threshold_table(d_t, "total")
    s_ok = st[st.bets >= 100].sort_values("roi", ascending=False).iloc[0]
    t_ok = tt[tt.bets >= 100].sort_values("roi", ascending=False).iloc[0]
    L += [f"Best spread threshold with 100+ bets on the tuning window: {s_ok.edge:g} (ROI {s_ok.roi:+.3f}). "
          f"Best total threshold: {t_ok.edge:g} (ROI {t_ok.roi:+.3f}). The held-out results below use the live spread flag ({P.SPREAD_EDGE:g}; totals are not flagged, so they are graded at the tuned {t_ok.edge:g}) and, separately, these.", ""]
    for label, se, te in [(f"live flag ({P.SPREAD_EDGE:g} / {t_ok.edge:g})", float(P.SPREAD_EDGE), float(t_ok.edge)), (f"tuned ({s_ok.edge:g} / {t_ok.edge:g})", float(s_ok.edge), float(t_ok.edge))]:
        sp, to = bt.grade_spread(d_v, se), bt.grade_total(d_v, te)
        L += [f"## 5. Held-out 2023 to 2025, {label}", "", "Spreads:", "", bt.summarize_bets(sp).round(3).to_markdown(), "",
              bt.summarize_bets(sp, "season").round(3).to_markdown(), "", "By edge size:", "", bt.edge_buckets(sp, edges=(se, se + 1, se + 2, se + 4, 99)).round(3).to_markdown(), "",
              "Totals:", "", bt.summarize_bets(to).round(3).to_markdown(), "", bt.summarize_bets(to, "season").round(3).to_markdown(), ""]
    a, mb = market_blend(new)
    L += ["## 6. Market plus model", "",
          f"Blend the model line with the closing line, pred = a x model + (1 - a) x line. Best a on 2019 to 2022 by margin MAE: {a:g}.", "",
          mb.to_markdown(index=False), "",
          "Bet selection is unchanged by blending (the edge is scaled, not re-ordered), so this only improves the score and the probabilities.", "",
          "## 7. Closing line value", "", clv_proxy(new, 3.0), ""]
    txt = "\n".join(L)
    (REP / "backtest_v3.md").write_text(txt)
    update_readme(new)
    update_docs(new)
    print(txt)


if __name__ == "__main__":
    main()
