"""The shadow watch (30 Sep 2026, Matt: "track them as shadows, I don't want to see it, but if one turns out good, alert me").
Every weekly run: each shadow rule's live record (data/tracker/graded.csv, settled bets) against the rule it would
replace over the same seasons (the spread flag, or the totals flag for a totals rule; the totals flag itself against
break-even). A shadow is READY when it has at least MIN_BETS settled, wins more often than break-even at -110 beyond
luck (one-sided binomial p at or under P_LUCK) and earns at least ROI_GAP more per unit risked. READY opens a
GitHub issue labelled ready-check (nflmodel/ready_checks.py, nflmodel/health_alert.py; GitHub emails the owner). Nothing changes on its own: a
READY rule is re-tested under reports/round3_rule.md before it is bet. Writes reports/shadow_watch.{csv,md}.

    python -m nflmodel.shadow_watch
"""
from __future__ import annotations
import numpy as np, pandas as pd
from pathlib import Path
from scipy.stats import binom

ROOT = Path(__file__).resolve().parent.parent
TR, REP = ROOT / "data" / "tracker", ROOT / "reports"
MIN_BETS, P_LUCK, ROI_GAP = 30, 0.10, 0.05


def _rec(x: pd.DataFrame) -> dict:
    st = x[x.result.isin(["win", "loss", "push"])]
    w, l = int((st.result == "win").sum()), int((st.result == "loss").sum())
    od = pd.to_numeric(st["odds"], errors="coerce").fillna(-110.0) if "odds" in st else pd.Series(-110.0, index=st.index)
    risked = float(np.where(od < 0, od.abs() / 100, 1.0)[st.result.ne("push").values].sum()) if len(st) else 0.0   # at each bet's own price (a teaser leg risks about 3 to win 1)
    u = float(st.units.sum()) if len(st) else 0.0
    return {"w": w, "l": l, "n": w + l, "units": round(u, 2), "roi": (u / risked) if risked else float("nan")}


def run() -> pd.DataFrame:
    from .picks import SHADOWS, HIDDEN_SHADOWS, SHADOW_ODDS, DEFAULT_ODDS, BLIND_RULES, TOTAL_RULES, break_even
    f = TR / "graded.csv"
    g = pd.read_csv(f) if f.exists() else pd.DataFrame(columns=["who", "result", "units", "season"])
    rows = []
    for name, (_, sr, lab) in SHADOWS.items():
        be = break_even(SHADOW_ODDS.get(name, DEFAULT_ODDS))   # the hook at its -125, a teaser leg at its two-team price
        x = g[g.who == name]; r = _rec(x)
        luck = float(binom.sf(r["w"] - 1, r["n"], be)) if r["n"] else float("nan")
        seasons = set(x.season.dropna().astype(int)) if len(x) else set()
        # the rule it would replace, over the same seasons: the totals flag (the unders at 55%) for a totals rule, the spread
        # flag otherwise; the totals flag itself is measured against break-even alone
        # rules that ignore the model (the wind, rain and cold unders, teaser legs, the West Coast road team), like the totals flag, against break-even alone
        base = None if name == "shadowunder" or sr in BLIND_RULES else ("shadowunder" if sr in TOTAL_RULES else "model")
        fl = _rec(g[(g.who == base) & g.season.isin(seasons)]) if base else {"w": 0, "l": 0, "n": 0, "roi": 0.0}
        ready = r["n"] >= MIN_BETS and luck <= P_LUCK and r["roi"] - (fl["roi"] if fl["n"] else 0.0) >= ROI_GAP
        rows.append({"rule": name, "label": lab, "hidden": name in HIDDEN_SHADOWS, "record": f"{r['w']}-{r['l']}", "settled": r["n"], "units": r["units"],
                     "roi": round(r["roi"], 3) if r["n"] else None, "compared_with": base or "break-even", "base_record": f"{fl['w']}-{fl['l']}", "base_roi": round(fl["roi"], 3) if fl["n"] else None,
                     "luck_p": round(luck, 3) if r["n"] else None, "status": "READY" if ready else ("tracking" if r["n"] < MIN_BETS else "not ahead")})
    df = pd.DataFrame(rows)
    REP.mkdir(exist_ok=True); df.to_csv(REP / "shadow_watch.csv", index=False)
    ready = df[df.status == "READY"]
    L = ["# Shadow watch", "", f"**{len(ready)} rule{'s' if len(ready) != 1 else ''} ready for a look.** READY = {MIN_BETS}+ settled live bets, a win rate past "
         f"break-even beyond luck (p <= {P_LUCK}) and {100 * ROI_GAP:.0f}+ points more return per unit risked than the rule it would replace over the same seasons (the spread flag, or the totals flag for a totals rule). "
         "A READY rule is re-tested under reports/round3_rule.md before it is bet.", "", df.to_markdown(index=False), ""]
    (REP / "shadow_watch.md").write_text("\n".join(L))
    print("\n".join(L[:3]))
    return df


if __name__ == "__main__":
    run()
