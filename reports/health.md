# Health check, 2026-09-23 02:36 UTC

**BROKEN**: 2 failing, 0 warnings, 13 ok.

| Level | Check | Detail |
|---|---|---|
| OK | weekly run is fresh | last run 2026-09-23 01:58 UTC, 1 hours ago (limit 72) |
| OK | every step of the latest run ok | 18 steps ok |
| OK | latest run has the step: verify | present |
| OK | latest run has the step: tie check (sources) | present |
| OK | latest run has the step: tie check (page) | present |
| OK | latest run has the step: export data room | present |
| OK | latest run has the step: record picks | present |
| OK | runs in the last seven days | 9 (four scheduled: Tue, Thu, Sat, Sun) |
| OK | verification suite passed | Result: PASS |
| OK | tie-out passed | Result: PASS (26 of 26 tie) |
| OK | line watch is logging | last snapshot 0.4 hours ago, 9 in the last seven days (every 30 minutes when GitHub's cron fires) |
| OK | line watch returns rows | 1 of 9 snapshots in the last two days logged no lines |
| OK | kickoff forecasts are fresh | fetched 5 hours ago (limit 96) |
| FAIL | picks and tracker check | No module named 'requests' |
| FAIL | page settings check | No module named 'scipy' |

Result: FAIL

Issue: https://github.com/MattFos18/nfl-model/issues/
Workflow run: https://github.com/MattFos18/nfl-model/actions/runs/35810994683
