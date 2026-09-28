# Weekly audit, 2026-09-28 20:05 UTC

**FAILING**: 5 of 7 sections pass.

| Section | Result | Detail | Seconds |
|---|---|---|---|
| Health: runs, steps, freshness, picks vs tracker, page settings | PASS | HEALTHY: 0 failing, 0 warnings, 29 ok. | 1.2 |
| Data verification: scores, mirrors, PFR totals, known results | PASS | Result: PASS | 0.4 |
| Tie-out: every headline number across README, docs, sweep, picks, tracker and page | FAIL | Result: FAIL (173 of 174 tie) | 4.7 |
| Leak test: corrupt every future game, nothing before the cut may move | PASS | rating change 0.0, prediction change 0.0 after corrupting every future game | 12.1 |
| Page JavaScript parses | PASS | 2 script blocks, all parse | 0.0 |
| Every page data file parses | PASS | 55 files, all parse | 0.6 |
| Chromium walk of every view: no errors, no NaN, nothing empty | FAIL | 12 views, 16 cards, errors [], bad ['teamsec/overview: sub-view button missing', 'teamsec/players: sub-view button missing', 'results/live: sub-view button missing'] | 13.7 |

The health table is in reports/health.md, the tie-out rows in reports/tie_check.md, the verification detail in reports/verification.md.

Result: FAIL

Issue: https://github.com/MattFos18/nfl-model/issues/193
Workflow run: https://github.com/MattFos18/nfl-model/actions/runs/36476659955
