# Health check, 2026-09-23 22:01 UTC

**BROKEN**: 1 failing, 1 warnings, 23 ok.

| Level | Check | Detail |
|---|---|---|
| OK | weekly run is fresh | last run 2026-09-23 21:50 UTC, 0 hours ago (limit 72) |
| FAIL | every step of the latest run ok | pull: error |
| OK | latest run has the step: verify | present |
| OK | latest run has the step: tie check (sources) | present |
| OK | latest run has the step: tie check (page) | present |
| OK | latest run has the step: export data room | present |
| OK | latest run has the step: record picks | present |
| OK | runs in the last seven days | 18 (four scheduled: Tue, Thu, Sat, Sun) |
| OK | verification suite passed | Result: PASS |
| OK | tie-out passed | Result: PASS (73 of 73 tie) |
| OK | line watch is logging | last snapshot 0.1 hours ago, 33 in the last seven days (every 30 minutes when GitHub's cron fires) |
| OK | line watch returns rows | 1 of 33 snapshots in the last two days logged no lines |
| OK | kickoff forecasts are fresh | fetched 4 hours ago (limit 96) |
| OK | picks file for Week 3, 2026 | picks_2026_wk3.csv |
| OK | tracker holds the week's flags | picks: ['MIA +11.5', 'NYG -2.5', 'PIT +3.5']; tracker: ['MIA +11.5', 'NYG -2.5', 'PIT +3.5'] |
| OK | shadow rule recorded for the week: shadow45 | picks: ['MIA +11.5', 'NYG -2.5']; tracker: ['MIA +11.5', 'NYG -2.5'] |
| OK | shadow rule recorded for the week: shadowdog | picks: ['MIA +11.5', 'PIT +3.5']; tracker: ['MIA +11.5', 'PIT +3.5'] |
| OK | shadow rule recorded for the week: shadowearly | picks: ['MIA +11.5', 'NYG -2.5', 'PIT +3.5']; tracker: ['MIA +11.5', 'NYG -2.5', 'PIT +3.5'] |
| OK | page flag threshold = code | page 4.0, code 4.0 |
| OK | page inputs = code | 22 on the page, 22 in code |
| OK | page data is fresh | built 0 hours ago (limit 96) |
| OK | cards carry the newest line snapshot | cards 2026-09-23T21-57-37Z, log 2026-09-23T21-57-37Z |
| OK | props panel carries the newest prop-line pull | page 2026-09-23T21-57-38Z, log 2026-09-23T21-57-38Z |
| WARN | injury reports cover the week being priced (week 3) | league reports for 2 teams, ESPN fills 0 more (no ESPN file), 2 of 32; first kickoff in 1.1 days |
| OK | page rankings use the code's QB replacement level | page -0.12, code -0.12 |

Result: FAIL
