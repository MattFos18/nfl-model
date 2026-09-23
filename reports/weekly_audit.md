# Weekly audit, 2026-09-23 16:05 UTC

**CLEAN**: 7 of 7 sections pass.

| Section | Result | Detail | Seconds |
|---|---|---|---|
| Health: runs, steps, freshness, picks vs tracker, page settings | PASS | HEALTHY: 0 failing, 0 warnings, 22 ok. | 1.0 |
| Data verification: scores, mirrors, PFR totals, known results | PASS | Result: PASS | 0.8 |
| Tie-out: every headline number across README, docs, sweep, picks, tracker and page | PASS | Result: PASS (48 of 48 tie) | 0.4 |
| Leak test: corrupt every future game, nothing before the cut may move | PASS | rating change 0.0, prediction change 0.0 after corrupting every future game | 9.5 |
| Page JavaScript parses | PASS | 1 script blocks, all parse | 0.1 |
| Every page data file parses | PASS | 41 files, all parse | 0.4 |
| Chromium walk of every view: no errors, no NaN, nothing empty | PASS | 15 views, 16 cards, errors [], bad [] | 25.2 |

The health table is in reports/health.md, the tie-out rows in reports/tie_check.md, the verification detail in reports/verification.md.

Result: PASS
