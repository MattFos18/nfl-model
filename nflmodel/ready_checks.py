"""Ready checks (30 Sep 2026, Matt: "build it into the site and delete the routines"). Every weekly run, one row per
question that waits on live data, READY once the data is in. nflmodel/health_alert.py opens one GitHub issue per READY
row (label ready-check; GitHub emails the owner), once per title. Matt pastes the issue into a Claude session with this
repo; the issue body says what to run. Nothing changes on its own. Writes reports/ready_checks.{csv,md}.

  - drift: an ALERT in reports/drift.csv (nflmodel/drift.py)
  - shadow: a READY rule in reports/shadow_watch.csv (nflmodel/shadow_watch.py)
  - calibration: CAL_FLAGS settled live flags, enough to check the cover odds against live results
  - market: MARKET_WEEKS weeks of this season in the line log, enough to test market signals
  - season: every regular-season game of the season scored, time to re-test the out-of-the-race input and the rules

    python -m nflmodel.ready_checks
"""
from __future__ import annotations
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT, TR, REP, LN = ROOT / "data" / "processed", ROOT / "data" / "tracker", ROOT / "reports", ROOT / "data" / "lines"
CAL_FLAGS, MARKET_WEEKS = 50, 9
ASK = "Paste this issue into a Claude session with the MattFos18/nfl-model repo and say \"look at this\". Nothing in the live model changes without Matt's yes."


def run() -> pd.DataFrame:
    g = pd.read_parquet(OUT / "games.parquet")
    season = int(g.season.max()); rows = []

    def add(key, title, ready, reading, task):
        rows.append({"key": key, "title": title, "ready": bool(ready), "reading": reading, "body": f"{reading}\n\n{task}\n\n{ASK}"})

    # drift alerts
    f = REP / "drift.csv"
    dr = pd.read_csv(f) if f.exists() else pd.DataFrame(columns=["measure", "level"])
    for r in dr[dr.level == "ALERT"].itertuples():
        add("drift", f"Drift alert {season}: {r.measure}", True, f"{r.measure}: long run {r.long_run:+.3f}, recent {r.recent:+.3f} (z {r.z:+.2f}, CUSUM {r.cusum:.1f}).",
            f"Run the re-test reports/drift.md names ({r.retest}) under reports/round3_rule.md, on a new branch with a pull request, and report the numbers per window.")
    if not (dr.level == "ALERT").any():
        add("drift", "Drift alert", False, f"{len(dr)} measures within noise", "")
    # tracked rules ahead of the live rule
    f = REP / "shadow_watch.csv"
    sw = pd.read_csv(f) if f.exists() else pd.DataFrame(columns=["status"])
    for r in sw[sw.status == "READY"].itertuples():
        add("shadow", f"Tracked rule worth a look: {r.label}", True,
            f"Live: {r.record} ({r.settled} settled, {r.units:+.2f} units, return {100 * r.roi:.1f}% a unit risked); {r.compared_with} over the same seasons: {r.base_record}. "
            f"Chance of a record this good by luck at -110: {r.luck_p:.3f}.",
            "Re-test the rule on the backtest windows under reports/round3_rule.md (its logic is in nflmodel/picks.py SHADOWS; experiments/home_side_rules.py has the grading and placebo) and say whether to bet it.")
    if not (sw.status == "READY").any():
        add("shadow", "Tracked rule worth a look", False, f"{len(sw)} tracked rules, none ahead", "")
    # the cover calibration against live flags
    f = TR / "graded.csv"
    gr = pd.read_csv(f) if f.exists() else pd.DataFrame(columns=["who", "result"])
    n = int(((gr.who == "model") & gr.result.isin(["win", "loss"])).sum())
    add("calibration", f"Ready: check the cover odds against {CAL_FLAGS} live flags", n >= CAL_FLAGS, f"{n} settled live flags (ready at {CAL_FLAGS}).",
        "Compare the live cover rate by edge (4 to 5, 5+) with what the calibrated cover odds promised (nflmodel/picks.py calibration), and whether the quarter-Kelly stakes "
        "ran high or low. Propose blending the live results into the calibration (for example five to one) and show the stakes it gives; change nothing.")
    # market signals on the line log
    f = LN / "lines_log.csv"
    wk = pd.read_csv(f, usecols=["season", "week"]) if f.exists() else pd.DataFrame(columns=["season", "week"])
    nw = int(wk[wk.season == season].week.nunique())
    add("market", f"Ready: test market signals on the {season} line log", nw >= MARKET_WEEKS, f"{nw} weeks of {season} in the line log (ready at {MARKET_WEEKS}).",
        "Run python -m experiments.market_signals: does a line that moved toward the model cover more often, does the opener edge predict the closing move, is there any reverse "
        "line movement signal. Then the betting splits (data/lines/splits_log.csv, DraftKings, every line-watch pull since 29 Sep 2026; data/lines/splits_consensus_log.csv, the multi-book consensus, and data/lines/books_log.csv, every book's line, both from 1 Oct 2026; joined by game and time): when the "
        "money share and the bet share point opposite ways, or the line moves against the side most bets are on, does the side the money or the move backs cover more often, "
        "and does it agree with the model's flags. Say plainly how small the sample is; change nothing (market numbers stay out of the model).")
    # the season is over
    reg = g[(g.season == season) & (g.game_type == "REG")]
    left = int(reg.home_score.isna().sum())
    add("season", f"Ready: {season} season over, re-test the rules and the out-of-the-race input", len(reg) > 0 and left == 0, f"{left} regular-season games of {season} left.",
        f"With {season} as another held-out season: re-test the out-of-the-race inputs (dead_late, opp_dead_late in nflmodel/model.py; experiments/late_season.py), and compare "
        "every rule's live record in reports/track_record.md and reports/shadow_watch.md with the 4-point flag. Recommend keeping or changing only where the windows agree.")
    df = pd.DataFrame(rows)
    REP.mkdir(exist_ok=True); df.to_csv(REP / "ready_checks.csv", index=False)
    ready = df[df.ready]
    L = ["# Ready checks", "", f"**{len(ready)} ready.** Each READY row opens a GitHub issue labelled ready-check (once per title).", "",
         df[["key", "title", "ready", "reading"]].to_markdown(index=False), ""]
    (REP / "ready_checks.md").write_text("\n".join(L))
    print("\n".join(L[:3]))
    return df


if __name__ == "__main__":
    run()
