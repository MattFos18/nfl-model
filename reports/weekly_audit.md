# Weekly audit, 2026-09-23 02:41 UTC

**CLEAN**: 7 of 7 sections pass.

| Section | Result | Detail | Seconds |
|---|---|---|---|
| Health: runs, steps, freshness, picks vs tracker, page settings | PASS | HEALTHY: 0 failing, 0 warnings, 19 ok. | 2.0 |
| Data verification: scores, mirrors, PFR totals, known results | PASS | Result: PASS | 0.5 |
| Tie-out: every headline number across README, docs, sweep, picks, tracker and page | PASS | Result: PASS (26 of 26 tie) | 0.1 |
| Leak test: corrupt every future game, nothing before the cut may move | PASS | rating change 0.0, prediction change 0.0 after corrupting every future game | 6.3 |
| Page JavaScript parses | PASS | 1 script blocks, all parse | 0.1 |
| Every page data file parses | PASS | 39 files, all parse | 0.2 |
| Chromium walk of every view: no errors, no NaN, nothing empty | PASS | 15 views, 16 cards, errors [], bad [] | 18.1 |

The health table is in reports/health.md, the tie-out rows in reports/tie_check.md, the verification detail in reports/verification.md.

Result: PASS

Issue: none open
Workflow run: https://github.com/MattFos18/nfl-model/actions/runs/35811246686
