"""The adoption rule as code (1 Oct 2026): reports/round3_rule.md, checked the same way for every study.

A study passes its numbers in; the gate says pass or fail on each part of the rule and writes the table for the report:
1. better on every window (the miss lower on 2015-18, 2019-22 and 2023-25; a fit window may tie),
2. no bet cost (each live record's wins minus losses not worse on any window; calibration not worse when given),
3. beats its own placebo (the real gain above the within-season-shuffle gain in at least 45 of 50 draws, every window).
Part 4 (no market input, no look-ahead, no new source) needs reading the code: the model-auditor agent does it.
paperwork(name) checks the write-up CLAUDE.md asks for: the script, the report, the decision-log row, the docs paragraph.

Usage: python -m nflmodel.study_gate <study name>   (the paperwork check for experiments/<name>.py)
"""
from __future__ import annotations
import math, sys
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WINDOWS = ("2015-18", "2019-22", "2023-25")
PLACEBO_SHARE = 0.9   # 45 of 50


def shuffle_within_season(values: np.ndarray, seasons: np.ndarray, rng) -> np.ndarray:
    """The placebo input: the same values shuffled among the games of each season."""
    out = np.array(values, dtype=float, copy=True)
    for s in np.unique(seasons):
        i = np.flatnonzero(seasons == s); out[i] = rng.permutation(out[i])
    return out


def gate(miss: dict, records: dict | None = None, placebo: dict | None = None, calibration: dict | None = None,
         fit_window: str | None = None) -> list[tuple[str, bool, str]]:
    """miss: {window: (base, new)}, lower is better. records: {window: {name: ((wins, losses) base, (wins, losses) new)}}.
    placebo: {window: [the gain (base - new) of each shuffled draw]}. calibration: {window: (base, new)}, lower is better.
    Returns (check, passes, detail) rows; a missing window fails."""
    rows = []
    def add(what, ok, detail): rows.append((what, bool(ok), detail))
    for w in WINDOWS:
        if w not in miss:
            add(f"better on {w}", False, "not scored"); continue
        b, n = miss[w]; ok = n < b or (w == fit_window and n <= b)
        add(f"better on {w}", ok, f"miss {b:.4f} -> {n:.4f}")
    if records is not None:
        for w in WINDOWS:
            for name, ((wb, lb), (wn, ln)) in (records.get(w) or {}).items():
                add(f"no bet cost: {name}, {w}", wn - ln >= wb - lb, f"{wb}-{lb} -> {wn}-{ln}")
    if calibration is not None:
        for w in WINDOWS:
            if w in calibration:
                b, n = calibration[w]; add(f"calibration not worse, {w}", n <= b, f"{b:.4f} -> {n:.4f}")
    if placebo is not None:
        for w in WINDOWS:
            if w not in placebo or w not in miss:
                add(f"beats its placebo on {w}", False, "no placebo draws"); continue
            real = miss[w][0] - miss[w][1]; g = np.asarray(placebo[w], dtype=float)
            beat = int((real > g).sum()); need = math.ceil(PLACEBO_SHARE * len(g))
            add(f"beats its placebo on {w}", len(g) >= 50 and beat >= need, f"{beat} of {len(g)} draws (need {need} of at least 50)")
    return rows


def passes(rows) -> bool:
    return bool(rows) and all(ok for _, ok, _ in rows)


def markdown(rows) -> str:
    L = ["| Check | Passes | Detail |", "|---|---|---|"] + [f"| {w} | {'yes' if o else 'NO'} | {d} |" for w, o, d in rows]
    return "\n".join(L + ["", f"Gate: {'PASS' if passes(rows) else 'FAIL'} ({sum(o for _, o, _ in rows)} of {len(rows)}); "
                              "no market input and no look-ahead checked by the model-auditor agent"])


def paperwork(name: str, root: Path = ROOT) -> list[tuple[str, bool, str]]:
    """The write-up every study needs (CLAUDE.md): experiments/<name>.py, reports/<name>.md (or .csv), a decision-log row naming
    the script, and a paragraph in docs/how_it_works.md naming the study."""
    log = (root / "reports" / "decision_log.md"); docs = (root / "docs" / "how_it_works.md")
    lt = log.read_text(encoding="utf-8") if log.exists() else ""; dt = docs.read_text(encoding="utf-8") if docs.exists() else ""
    return [(f"script experiments/{name}.py", (root / "experiments" / f"{name}.py").exists(), ""),
            (f"report reports/{name}.md or .csv", any((root / "reports" / f"{name}{x}").exists() for x in (".md", ".csv")), ""),
            ("decision-log row names the script", f"experiments/{name}.py" in lt, "reports/decision_log.md"),
            ("docs paragraph names the study", name in dt, "docs/how_it_works.md")]


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    rows = paperwork(sys.argv[1]); print(markdown(rows).replace("; no market input and no look-ahead checked by the model-auditor agent", ""))
    sys.exit(0 if passes(rows) else 1)
