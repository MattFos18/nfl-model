# Weekly audit, 2026-10-19 19:13 UTC

**FAILING**: 4 of 7 sections pass.

| Section | Result | Detail | Seconds |
|---|---|---|---|
| Health: runs, steps, freshness, picks vs tracker, page settings | FAIL | BROKEN: 2 failing, 5 warnings, 55 ok. | 1.9 |
| Data verification: scores, mirrors, PFR totals, known results | PASS | Result: PASS | 0.5 |
| Tie-out: every headline number across README, docs, sweep, picks, tracker and page | FAIL | Result: FAIL (250 of 253 tie) | 13.5 |
| Leak test: corrupt every future game, nothing before the cut may move | PASS | rating change 0.0, prediction change 0.0 after corrupting every future game; own-game change 0.0 after corrupting each game's own score | 40.8 |
| Page JavaScript parses | PASS | 2 script blocks, all parse | 0.0 |
| Every page data file parses | PASS | 55 files, all parse | 0.7 |
| Chromium walk of every view: no errors, no NaN, nothing empty | FAIL | 8 views, 14 cards, errors [], bad ["rank: page.click: Timeout 30000ms exceeded.\nCall log:\n  - waiting for locator('button[", 'teamsec/overview: sub-view button missing', 'teamsec/players: sub-view button missing'] | 44.1 |

The health table is in reports/health.md, the tie-out rows in reports/tie_check.md, the verification detail in reports/verification.md.

Result: FAIL

Issue: https://github.com/MattFos18/nfl-model/issues/193
Workflow run: https://github.com/MattFos18/nfl-model/actions/runs/39309030996
