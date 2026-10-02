---
name: study
description: Use for any study of a model input, model change, weather or injury idea, bet rule, threshold or shadow in this repo, from Matt's idea to the decision-log row. Covers pre-registration, the experiment script, the study gate (three windows, no bet cost, placebo), counting variants, the model-auditor, the write-up, and what may go live only with Matt's yes.
---

# Running a study

The adoption rule is `reports/round3_rule.md`, coded in `nflmodel/study_gate.py`. This is the procedure around it.
Read `docs/wiki/gotchas.md` before building anything: most past mistakes were data traps, not statistics.

## 1. Pre-register (before any result)
Write the top of `reports/<name>.md` first, and do not change it after seeing results:
- **Claim** in one line, with who asked (Matt's words if he asked).
- **Variants**, every one, numbered (V1, V2 ...). Each cutoff or band is a variant. A variant added later is listed
  under "added after results" with the reason.
- **Data and timing**: each input, its source, and the time it is known (forecast at bet time, not the weather that
  happened; injury status as of the run; no line, split or price as an input).
- **Pass bar**: the three windows 2015-18 (untouched), 2019-22 (tuning), 2023-25 (held out); lower miss on every
  window; the live records (spread flag, totals flag, wind under) not worse on any window; beats its placebo (values
  shuffled within season, 50 draws, at least 45 of 50 on every window). For a bet rule: its record on every window and
  a placebo of at least 200 shuffles.

## 2. Build `experiments/<name>.py`
- Reuse `experiments/common.py` and the walk-forward the model uses; refit, never reuse trees fit on later seasons.
- Every input as of before the game. Trace each new input to where it is built and its timestamp.
- Placebo with `study_gate.shuffle_within_season(values, seasons, rng)`, fixed seed.
- Write the full table to `reports/<name>.csv` and print the counts.
- Run `data-checker` on any new table before trusting its numbers.

## 3. Score through the gate
```python
from nflmodel import study_gate as G
rows = G.gate(miss={w: (base, new) for w ...}, records={w: {"spread flag": ((wb, lb), (wn, ln)), ...}},
              placebo={w: [gain of each draw] for w ...}, calibration=...)
report_table = G.markdown(rows)   # paste into the report
```
All three windows must be scored (a missing window fails). Paste the table into the report as is.

## 4. Count what was tried
In the report: the number of variants tried (including ones in earlier studies of the same idea, from the decision
log), which one is best, and whether it was picked on 2023-25. A winner picked from many, or a cutoff picked after
seeing results, is a shadow candidate, not a rule.

## 5. Audit
Run the `model-auditor` agent on the script, report and claim. Its verdict file is
`reports/audit_<name>_YYYY-MM-DD.md`; quote its one-line verdict in the report. If it finds a leak, fix it and rerun
everything from step 3.

## 6. Write up
- `reports/<name>.md`: the pre-registration, results by window, the gate table, the variant count, the audit verdict,
  the decision.
- A row at the top of `reports/decision_log.md` (Date | Claim | Test | Result | Decision), naming
  `experiments/<name>.py`.
- A paragraph in `docs/how_it_works.md` naming the study.
- A line in `docs/wiki/log.md`.
- Check the paperwork: `python -m nflmodel.study_gate <name>` must print PASS.
- Run `site-fact-checker` on the write-up before showing Matt.

## 7. What may change, and who decides
- **Passes every part:** recommend it to Matt in plain words with the three windows' records. Nothing in the live
  model or bet rules changes without his yes. After his yes: change the code, rerun `experiments.props_by_season` and
  update `props.BACKTEST` / `BACKTEST_COUNTS` if the game model's totals or spreads moved (`docs/handoff.md`), then ship
  with the `ship` skill.
- **Found by looking at results** (a band, a subgroup, a cutoff that looked good): never a bet. Ask Matt to add it as a
  hidden shadow (`picks.SHADOWS` plus `picks.HIDDEN_SHADOWS`), graded live; `shadow_watch.py` and `ready_checks.py`
  open a ready-check issue if it pulls clear.
- **Fails:** record it (report, log row, docs paragraph) and leave the code as it is.

## Rules
- Quote numbers only from the run you just did. After any data fix, rerun and correct every place a number was quoted.
- Report to Matt in a few lines: proven or not (yes/no), the three windows, the one recommendation.
