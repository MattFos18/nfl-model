"""Home-side bet rules (30 Sep 2026, Matt: "if our error is on home teams, give them less edge").

Research only: reads data/processed, writes reports/home_side_rules.{csv,md}. Nothing in nflmodel/, web/ or data/ changes.

The live flag bets the model's side at |model_spread - spread_line| >= 4 (weeks 1-17, graded at the close, -110). The
favorite review found its home sides weaker (home favorite 24-25, home dog 76-63) than its road sides (road favorite 9-4,
road dog 79-35), and the model leaning 0.3-0.4 points more to home than the close. The model fix (a lower home field)
failed there, so this tests the bet rule instead:

  - a higher cut for home sides (road 4+, home 5+ / 6+), or no home sides
  - a lower cut for road sides (3.5+)
  - the edge less the model's home lean, measured walk-forward (the mean of model_spread - spread_line over every
    earlier season's games, taken off every edge before the 4+ cut), and the same with a fixed half point

Neutral sites have no home side: they count as road here. A rule passes only if it wins more units than the live rule on
every window (2015-18, 2019-22, 2023-25) and beats its placebo (the same number of bets per season drawn at random from the
rule's pool) at p <= 0.10.

    python -m experiments.home_side_rules
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import numpy as np, pandas as pd
from experiments.favorite_review import load, sides, grade_rule, WINDOWS, LAST_WEEK, EDGE, VIG, md_table

ROOT = Path(__file__).resolve().parent.parent
REP = ROOT / "reports"
PLACEBO_P = 0.10


def table() -> pd.DataFrame:
    d, g = load()
    d = d[d.season <= 2025].copy()
    d["neutral_site"] = d.game_id.map(g.set_index("game_id").location).eq("Neutral").values
    x = sides(d)
    x["home"] = x.home_side & ~x.neutral_site; x["road"] = ~x.home
    # walk-forward home lean: mean(model - close) over every earlier season (non-neutral games)
    lean = (x.model_spread - x.spread_line).where(~x.neutral_site).groupby(x.season).agg(["sum", "count"])
    past = lean.cumsum().shift(1); x["lean_wf"] = x.season.map(past["sum"] / past["count"]).fillna(0.0)
    return x


def adj_side(x: pd.DataFrame, k) -> tuple[pd.Series, pd.Series]:
    """Edge after taking k points of home lean off (home sides lose k, road sides gain k); returns |edge| and the
    new side's grading (the side can flip)."""
    e = (x.model_spread - x.spread_line) - np.where(x.neutral_site, 0.0, k)
    sgn = np.where(e > 0, 1.0, -1.0); ats = (x.result - x.spread_line) * sgn
    return pd.Series(np.abs(e), index=x.index), pd.Series(ats, index=x.index)


def rules(x: pd.DataFrame) -> dict:
    a, h, r = x.aedge, x.home, x.road
    return {
        "LIVE: 4+ either side": (a >= 4, a >= 4),
        "Road 4+, home 4.5+": ((r & (a >= 4)) | (h & (a >= 4.5)), a >= 4),
        "Road 4+, home 5+": ((r & (a >= 4)) | (h & (a >= 5)), a >= 4),
        "Road 4+, home 6+": ((r & (a >= 4)) | (h & (a >= 6)), a >= 4),
        "Road 4+ only (no home sides)": (r & (a >= 4), a >= 4),
        "Road 3.5+, home 4+": ((r & (a >= 3.5)) | (h & (a >= 4)), a >= 3.5),
        "Road 3.5+, home 5+": ((r & (a >= 3.5)) | (h & (a >= 5)), a >= 3.5),
        "Road 3.5+ only": (r & (a >= 3.5), a >= 3.5),
        "Home 4+ alone (for reference)": (h & (a >= 4), a >= 4),
    }


def run():
    x = table(); wk = x.week <= LAST_WEEK
    rows, per = [], []
    live = grade_rule(x, (x.aedge >= EDGE) & wk, (x.aedge >= EDGE) & wk)

    def add(name, o):
        beats = all(o[w]["units"] > live[w]["units"] + 1e-9 for w in WINDOWS)
        ok = beats and o["placebo_p"] == o["placebo_p"] and o["placebo_p"] <= PLACEBO_P
        rows.append({"rule": name, **{w: f"{o[w]['w']}-{o[w]['l']} ({o[w]['units']:+.1f}u)" for w in list(WINDOWS) + ["2015-25"]},
                     "win %": round(100 * o["2015-25"]["w"] / max(o["2015-25"]["n"], 1), 1),
                     "more units than live on all 3": "" if name.startswith("LIVE") else ("yes" if beats else "no"),
                     "placebo p": "" if o["placebo_p"] != o["placebo_p"] else round(o["placebo_p"], 3),
                     "passes": "" if name.startswith("LIVE") else ("PASS" if ok else "fail")})

    for name, (sel, pool) in rules(x).items():
        add(name, grade_rule(x, sel & wk, pool & wk))
    # lean-adjusted edges: re-grade on the adjusted side, then reuse grade_rule on a copy
    for name, k in [("Edge less the walk-forward home lean, 4+", x.lean_wf.values), ("Edge less 0.5 pt home lean, 4+", 0.5),
                    ("Edge less 1 pt home lean, 4+", 1.0)]:
        a, ats = adj_side(x, k); y = x.copy()
        y["aedge"] = a; y["ats"] = ats; y["win"] = ats > 0; y["push"] = ats == 0
        y["units"] = np.where(y.push, 0.0, np.where(y.win, 1.0, -VIG))
        add(name, grade_rule(y, (a >= EDGE) & wk, (a >= EDGE - 0.5) & wk))

    # per season: home vs road sides at 4+ (the split behind the idea)
    b = x[(x.aedge >= EDGE) & wk & ~x.push]
    for s, q in b.groupby("season"):
        hq, rq = q[q.home], q[q.road]
        per.append({"season": s, "home sides": f"{int(hq.win.sum())}-{int((~hq.win).sum())}", "home units": round(hq.units.sum(), 1),
                    "road sides": f"{int(rq.win.sum())}-{int((~rq.win).sum())}", "road units": round(rq.units.sum(), 1),
                    "model home lean (all games)": round(float((x.model_spread - x.spread_line)[(x.season == s) & ~x.neutral_site].mean()), 2),
                    "walk-forward lean used": round(float(x.lean_wf[x.season == s].iloc[0]), 2)})
    R, P = pd.DataFrame(rows), pd.DataFrame(per)
    REP.mkdir(exist_ok=True); R.to_csv(REP / "home_side_rules.csv", index=False)
    hw = int((P["home units"] > P["road units"]).sum())
    passed = R[R.passes == "PASS"]
    L = ["# Home-side bet rules (30 Sep 2026)", "",
         f"**{'Passes: ' + ', '.join(passed.rule) if len(passed) else 'Nothing passes; the live rule (4+ either side) stays.'}** "
         f"A rule needs more units than the live rule on every window and a placebo p at or under {PLACEBO_P}.", "",
         "Home side = the model's side is the home team at a non-neutral site. The lean-adjusted rules take the model's "
         "home lean off every edge before the 4+ cut (the walk-forward one uses the mean lean of every earlier season).", "",
         md_table(R), "", "## Home and road sides at 4+, by season", "",
         f"Home sides out-earned road sides in {hw} of {len(P)} seasons.", "", md_table(P), ""]
    (REP / "home_side_rules.md").write_text("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    run()
