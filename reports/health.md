# Health check, 2026-09-23 23:17 UTC

**BROKEN**: 1 failing, 0 warnings, 24 ok.

| Level | Check | Detail |
|---|---|---|
| OK | weekly run is fresh | last run 2026-09-23 22:55 UTC, 0 hours ago (limit 72) |
| OK | every step of the latest run ok | 21 steps ok |
| OK | latest run has the step: verify | present |
| OK | latest run has the step: tie check (sources) | present |
| OK | latest run has the step: tie check (page) | present |
| OK | latest run has the step: export data room | present |
| OK | latest run has the step: record picks | present |
| OK | runs in the last seven days | 20 (four scheduled: Tue, Thu, Sat, Sun) |
| OK | verification suite passed | Result: PASS |
| FAIL | tie-out passed | Result: FAIL (80 of 81 tie) |
| OK | line watch is logging | last snapshot 0.7 hours ago, 34 in the last seven days (every 30 minutes when GitHub's cron fires) |
| OK | line watch returns rows | 1 of 34 snapshots in the last two days logged no lines |
| OK | kickoff forecasts are fresh | fetched 4 hours ago (limit 96) |
| OK | picks file for Week 3, 2026 | picks_2026_wk3.csv |
| OK | tracker holds the week's flags | picks: ['CHI +4.5', 'MIA +11.5', 'NYG -2.5', 'PIT +3.5']; tracker: ['CHI +4.5', 'MIA +11.5', 'NYG -2.5', 'PIT +3.5'] |
| OK | shadow rule recorded for the week: shadow45 | picks: ['MIA +11.5', 'NYG -2.5']; tracker: ['MIA +11.5', 'NYG -2.5'] |
| OK | shadow rule recorded for the week: shadowdog | picks: ['CHI +4.5', 'MIA +11.5', 'PIT +3.5']; tracker: ['CHI +4.5', 'MIA +11.5', 'PIT +3.5'] |
| OK | shadow rule recorded for the week: shadowearly | picks: ['CHI +4.5', 'MIA +11.5', 'NYG -2.5', 'PIT +3.5']; tracker: ['CHI +4.5', 'MIA +11.5', 'NYG -2.5', 'PIT +3.5'] |
| OK | page flag threshold = code | page 4.0, code 4.0 |
| OK | page inputs = code | 22 on the page, 22 in code |
| OK | page data is fresh | built 0 hours ago (limit 96) |
| OK | cards carry the newest line snapshot | cards 2026-09-23T22-35-41Z, log 2026-09-23T22-35-41Z |
| OK | props panel carries the newest prop-line pull | page 2026-09-23T21-57-38Z, log 2026-09-23T21-57-38Z |
| OK | injury reports cover the week being priced (week 3) | league reports for 2 teams, ESPN fills 30 more (fetched 0 hours ago), 32 of 32; first kickoff in 1.0 days |
| OK | page rankings use the code's QB replacement level | page -0.12, code -0.12 |

Result: FAIL
