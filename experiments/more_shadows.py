"""Every promising rule not adopted, tracked as a hidden shadow (2 Oct 2026, Matt: track the rain under as a hidden shadow,
and "everything we can think of that's possible should be shadow tracked").

Tracking only: nothing here changes a bet rule, a threshold, the model or the page. Each candidate comes from a study in
reports/ or docs/todo.md ("Ideas parked"); each one that can be written as a picks.rule_mask side rule with a reading known
before kickoff, both live and on the backtest, and with no market input beyond the closing line it is graded at, is added
to picks.SHADOWS and picks.HIDDEN_SHADOWS. The records below are picks.rule_records' grading (regular season, weeks 1 to
17, the closing line, pushes dropped) on the stored prediction table; the forecast rules start in 2018, so their 2015-18
column is 2018 alone. The rest are listed with the reason they were not added (with a record where one is cheap to grade).
Writes reports/more_shadows.{md,csv}.

    python -m experiments.more_shadows
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import numpy as np, pandas as pd
from nflmodel import backtest as B, picks as P
from nflmodel.model import OUT

ROOT = Path(__file__).resolve().parent.parent
REP = ROOT / "reports"
ADDED = {   # rule -> source
    "shadowrain": "reports/rain_under_retest.md, reports/weather_forecast_retest.md",
    "shadowcold": "reports/weather_forecast_retest.md",
    "shadowunder3": "decision log 25 Sep 2026; docs/todo.md",
    "shadowunderwind": "reports/friend_ideas.md, reports/wind_forecast.md",
    "shadowtreestotal": "reports/ml_compare.md; docs/todo.md",
    "shadowwestcoast": "reports/audit.md section 4; decision log 21 Sep 2026",
    "shadowroaddog": "reports/bet_rules_sweep.md, reports/spread_research.md",
    "shadowsmalldog": "reports/spread_research.md",
    "shadowdog35": "reports/favorite_review.md",
    "shadowwk4": "reports/bet_rules_sweep.md",
    "shadowwk15": "reports/bet_rules_sweep.md",
    "shadow6": "decision log 21 Sep 2026",
}
NOTE = {   # what the source study said against it, kept beside the record
    "shadowcold": "; the study rejected it (27.5% of shuffles as good), tracked anyway as possible",
    "shadowwestcoast": "; loses 2015-18",
    "shadow6": "; loses 2015-18",
    "shadowunderwind": "; the friend's study's version on the wind that happened failed its placebo",
}


def data() -> pd.DataFrame:
    d = B.join(pd.read_parquet(OUT / "pred_v3.parquet"), pd.read_parquet(OUT / "games.parquet"))
    return d[(d.game_type == "REG") & d.home_score.notna() & d.spread_line.notna()].reset_index(drop=True)


def windows(d: pd.DataFrame, mask_fn, sr) -> dict:
    out = {}
    for w, (a, b) in P.WINDOWS.items():
        x = d[d.season.between(a, b)]; wi, lo = P.record(x, mask_fn(x), sr); out[w] = f"{wi}-{lo}"
    return out


def total_both(x: pd.DataFrame, cut: float) -> pd.Series:
    return ((x.model_total - x.total_line).abs() >= cut) & (x.week <= P.LAST_BET_WEEK) & x.total_line.notna()


def main():
    d = data(); rows = []
    for name, src in ADDED.items():
        edge, sr, lab = P.SHADOWS[name]
        rows.append({"candidate": lab, "rule": name, "source": src, **windows(d, lambda x, e=edge, s=sr: P.rule_mask(x, e, s), sr), "status": "added (hidden)" + NOTE.get(name, "")})
    # graded not-added candidates: same grading
    prime = lambda x: P._prime(x) & (x.week <= P.LAST_BET_WEEK) & x.total_line.notna()
    graded = [("Under, forecast rain chance 70%+", "reports/rain_under_retest.md", lambda x: P.rule_mask(x, 70.0, "rain_under"), "rain_under",
               "not added: a subset of the 50%+ rule, fails 2018 and 6% of shuffles as good (the study's own verdict)"),
              ("Under, model total 4+ points below the line", "decision log 25 Sep 2026", lambda x: P.rule_mask(x, 4.0, "under_edge"), "under_edge",
               "not added: a subset of the Under 3+ shadow"),
              ("Under in every prime-time game, blind", "reports/bet_rules_sweep.md", prime, "under_edge",
               "not added: loses units on 2015-18 and 2023-25 at -110; the totals flag in prime time is already tracked (shadowunderprime)")]
    for lab, src, fn, sr, why in graded:
        rows.append({"candidate": lab, "rule": "", "source": src, **windows(d, fn, sr), "status": why})
    # totals 6+ both ways: the model's side of the total
    r6 = {}
    for w, (a, b) in P.WINDOWS.items():
        x = d[d.season.between(a, b)]; m = total_both(x, 6.0); cm = x.home_score + x.away_score - x.total_line; e = x.model_total - x.total_line
        f = m & (cm != 0); wi = int((np.sign(e) == np.sign(cm))[f].sum()); r6[w] = f"{wi}-{int(f.sum()) - wi}"
    rows.append({"candidate": "Total 6+ points off the line, either side", "rule": "", "source": "decision log 21 Sep 2026", **r6,
                 "status": "not added: overs lose every way tried (experiments/totals_fix.py); the under side is the Under 3+ shadow"})
    na = "n/a"
    for lab, src, why in [
            ("Chance the wind reaches 10+ mph (walk-forward fit)", "reports/wind_forecast.md", "not added: needs a fitted wind-chance model that does not run live"),
            ("Under at a Blend gust of 25+ mph", "reports/weather_forecast_retest.md", "not added: the gust exists Nov 2018 to 2019 only; no live reading"),
            ("Totals flag, or wind 10+ at a 50%+ chance", "reports/friend_ideas.md", "not added: the wind under already bets every 10+ game, so this is the totals flag plus the wind under, both tracked"),
            ("Teaser legs on favourites at -1.5 to -2.5", "reports/friend_ideas.md", "not added: 61.7% on 2023-25, under a leg's break-even at -130 (75%)"),
            ("Moneyline on the flag's side", "reports/bet_rules_sweep.md", "not added: better than the spread on one window only, and needs each bet's moneyline price, which the tracker does not log for shadows"),
            ("Rules on the opener or line moves (bet timing)", "reports/bet_rules_sweep.md", "not added: a market input"),
            ("Betting splits (money and bet share)", "docs/todo.md", "not added: a market input; Matt, 29 Sep: build nothing on splits until a history can be tested"),
            ("Rain, cold, gust and wet-or-cold points in the total", "reports/weather_forecast_retest.md, reports/friend_ideas.md", "not added: model changes, not side rules (all rejected)"),
            ("Game situations (121 ideas; the closest, turf)", "reports/situational_game.md", "not added: none passed; the closest did no better than luck"),
            ("Already tracked: 4.5+, dogs, weeks 1-13, trees 5+, the hook, unders 59% early, road sides, road 4 / home 6, unders 60%+, prime-time unders, dog teaser legs, the wind under", "picks.SHADOWS", "already tracked")]:
        rows.append({"candidate": lab, "rule": "", "source": src, "2015-18": na, "2019-22": na, "2023-25": na, "status": why})
    t = pd.DataFrame(rows)
    REP.mkdir(exist_ok=True); t.to_csv(REP / "more_shadows.csv", index=False)
    L = ["# More shadows (2 Oct 2026)", "",
         "Every rule a study found promising but did not adopt, checked for whether it can be tracked live: a `picks.rule_mask` side rule with a",
         "reading known before kickoff, live and on the backtest, and no market input beyond the closing line used for grading. Each one that",
         "can is added to `picks.SHADOWS` and `picks.HIDDEN_SHADOWS`: graded every run, never bet, never shown on the page; `nflmodel/shadow_watch.py`",
         "measures it against the rule it would replace (the spread flag, the totals flag for a totals rule, break-even for a rule that ignores",
         "the model) and `ready_checks` opens a ready-check issue if one pulls clear. Nothing in the live rules, thresholds, model or page changes.", "",
         "Records: regular season, weeks 1 to 17, at the closing line, pushes dropped (`picks.rule_records`), on the stored prediction table.",
         "The forecast rules (rain, cold, the totals flag in wind) start in 2018, so their 2015-18 column is 2018 alone. These rules were",
         "found by looking at past results, so none of these records is evidence the rule wins; the live record decides.", "",
         "| Candidate | Source | 2015-18 | 2019-22 | 2023-25 | Status |", "|---|---|---|---|---|---|"]
    L += [f"| {r.candidate}{f' (`{r.rule}`)' if r.rule else ''} | {r.source} | {r['2015-18']} | {r['2019-22']} | {r['2023-25']} | {r.status} |" for _, r in t.iterrows()]
    (REP / "more_shadows.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
