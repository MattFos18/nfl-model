# Weekly audit, 2026-10-05 21:14 UTC

**FAILING**: 4 of 7 sections pass.

| Section | Result | Detail | Seconds |
|---|---|---|---|
| Health: runs, steps, freshness, picks vs tracker, page settings | FAIL | BROKEN: 2 failing, 4 warnings, 56 ok. | 2.7 |
| Data verification: scores, mirrors, PFR totals, known results | PASS | Result: PASS | 0.4 |
| Tie-out: every headline number across README, docs, sweep, picks, tracker and page | FAIL | Result: FAIL (250 of 253 tie) | 8.4 |
| Leak test: corrupt every future game, nothing before the cut may move | PASS | rating change 0.0, prediction change 0.0 after corrupting every future game; own-game change 0.0 after corrupting each game's own score | 28.4 |
| Page JavaScript parses | PASS | 2 script blocks, all parse | 0.0 |
| Every page data file parses | PASS | 55 files, all parse | 0.6 |
| Chromium walk of every view: no errors, no NaN, nothing empty | FAIL | 8 views, 16 cards, errors [], bad ["rank: page.click: Timeout 30000ms exceeded.\nCall log:\n  - waiting for locator('button[", 'teamsec/overview: sub-view button missing', 'teamsec/players: sub-view button missing'] | 42.9 |

The health table is in reports/health.md, the tie-out rows in reports/tie_check.md, the verification detail in reports/verification.md.

Result: FAIL

Issue: https://github.com/MattFos18/nfl-model/issues/193
Workflow run: https://github.com/MattFos18/nfl-model/actions/runs/37373534619
