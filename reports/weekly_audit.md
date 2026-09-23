# Weekly audit, 2026-09-23 07:26 UTC

**CLEAN**: 7 of 7 sections pass.

| Section | Result | Detail | Seconds |
|---|---|---|---|
| Health: runs, steps, freshness, picks vs tracker, page settings | PASS | HEALTHY: 0 failing, 0 warnings, 22 ok. | 1.0 |
| Data verification: scores, mirrors, PFR totals, known results | PASS | Result: PASS | 0.6 |
| Tie-out: every headline number across README, docs, sweep, picks, tracker and page | PASS | Result: PASS (44 of 44 tie) | 0.3 |
| Leak test: corrupt every future game, nothing before the cut may move | PASS | rating change 0.0, prediction change 0.0 after corrupting every future game | 9.7 |
| Page JavaScript parses | PASS | 1 script blocks, all parse | 0.0 |
| Every page data file parses | PASS | 39 files, all parse | 0.3 |
| Chromium walk of every view: no errors, no NaN, nothing empty | PASS | 15 views, 16 cards, errors [], bad [] | 25.1 |

The health table is in reports/health.md, the tie-out rows in reports/tie_check.md, the verification detail in reports/verification.md.

Result: PASS
