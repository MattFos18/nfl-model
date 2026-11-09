# Health check, 2026-11-09 22:57 UTC

**BROKEN**: 4 failing, 3 warnings, 54 ok.

| Level | Check | Detail |
|---|---|---|
| OK | weekly run is fresh | last run 2026-11-08 18:12 UTC, 29 hours ago (limit 72) |
| FAIL | every step of the latest run ok | props: error, tie check (sources): error, tie check (page): error |
| OK | latest run has the step: verify | present |
| OK | latest run has the step: tie check (sources) | present |
| OK | latest run has the step: tie check (page) | present |
| OK | latest run has the step: export data room | present |
| OK | latest run has the step: record picks | present |
| OK | latest run has the step: standing checks | present |
| OK | picks week's sources | week 9: in play; the week before it is complete |
| OK | runs in the last seven days | 4 (four scheduled: Tue, Thu, Sat, Sun) |
| OK | verification suite passed | Result: PASS |
| FAIL | tie-out passed | Result: FAIL (254 of 260 tie) |
| FAIL | line watch is logging | last snapshot 28.7 hours ago, 4 in the last seven days (every 30 minutes when GitHub's cron fires) |
| OK | line watch returns rows | 0 of 1 snapshots in the last two days logged no lines |
| OK | live forecast pull (wind_live) ok in the line watch | no failure in the 0 snapshots of the last day |
| OK | kickoff forecasts are fresh | fetched 34 hours ago (limit 96) |
| OK | kickoff forecast for every outdoor game inside the window | 10 of 10 games have a reading |
| OK | GFS MOS reading for every US outdoor game within 59 hours of kickoff | 0 of 0 games have one |
| OK | live weather priced on GFS MOS (the backtest's source) | 9 of 10 games on GFS MOS; 0 on the expected Open-Meteo fallback (more than 59 hours out, or abroad) |
| OK | picks file for Week 9, 2026 | picks_2026_wk9.csv |
| OK | tracker holds the week's flags | picks: []; tracker: [] |
| OK | shadow rule recorded for the week: shadow45 | picks: []; tracker: [] |
| OK | shadow rule recorded for the week: shadowdog | picks: []; tracker: [] |
| OK | shadow rule recorded for the week: shadowearly | picks: []; tracker: [] |
| OK | shadow rule recorded for the week: shadowtrees | picks: []; tracker: [] |
| OK | shadow rule recorded for the week: shadowunder | picks: []; tracker: [] |
| OK | shadow rule recorded for the week: shadowunderearly | picks: []; tracker: [] |
| OK | shadow rule recorded for the week: shadowhook | picks: []; tracker: [] |
| OK | shadow rule recorded for the week: shadowroad6 | picks: []; tracker: [] |
| OK | shadow rule recorded for the week: shadowroad | picks: []; tracker: [] |
| OK | shadow rule recorded for the week: shadowunder60 | picks: []; tracker: [] |
| OK | shadow rule recorded for the week: shadowunderprime | picks: []; tracker: [] |
| OK | shadow rule recorded for the week: windunder | picks: []; tracker: [] |
| OK | shadow rule recorded for the week: shadowteasedog | picks: []; tracker: [] |
| OK | shadow rule recorded for the week: shadowrain | picks: []; tracker: [] |
| OK | shadow rule recorded for the week: shadowcold | picks: []; tracker: [] |
| OK | shadow rule recorded for the week: shadowunder3 | picks: []; tracker: [] |
| OK | shadow rule recorded for the week: shadowunderwind | picks: []; tracker: [] |
| OK | shadow rule recorded for the week: shadowtreestotal | picks: []; tracker: [] |
| OK | shadow rule recorded for the week: shadowwestcoast | picks: []; tracker: [] |
| OK | shadow rule recorded for the week: shadowroaddog | picks: []; tracker: [] |
| OK | shadow rule recorded for the week: shadowsmalldog | picks: []; tracker: [] |
| OK | shadow rule recorded for the week: shadowdog35 | picks: []; tracker: [] |
| OK | shadow rule recorded for the week: shadowwk4 | picks: []; tracker: [] |
| OK | shadow rule recorded for the week: shadowwk15 | picks: []; tracker: [] |
| OK | shadow rule recorded for the week: shadow6 | picks: []; tracker: [] |
| OK | shadow rule recorded for the week: shadowoverlow | picks: []; tracker: [] |
| OK | shadow rule recorded for the week: shadowqtotals | picks: []; tracker: [] |
| OK | page flag threshold = code | page 4.0, code 4.0 |
| OK | page inputs = code | 17 on the page, 17 in code |
| OK | page data is fresh | built 28 hours ago (limit 96) |
| OK | cards carry the newest line snapshot | cards 2026-11-08T18-17-19Z, log 2026-11-08T18-17-19Z |
| FAIL | props panel carries the newest prop-line pull | page 2026-10-22T06-30-05Z, log 2026-10-27T15-44-47Z |
| OK | injury reports cover the week being priced | raw injuries not on this machine (the weekly run checks them) |
| OK | page rankings use the code's QB replacement level | page -0.12, code -0.12 |
| OK | QB-out check loaded the injury reports (week 9) | ok |
| OK | QB swaps priced this week (week 9) | MIN Kyler Murray -> Carson Wentz (depth chart) |
| WARN | ESPN Out/Doubtful players all matched to a roster player | 14 unmatched: BUF Joshua Palmer, NO Mike Reid, NYG CJ Okoye, PIT Ben Skowronek, PIT Brandin Echols, PIT Doneiko Slaughter, PIT Michael Pittman Jr., PIT Sebastian Joseph-Day |
| WARN | warnings from data checks (last 36 hours) | 1: games inside the forecast window without every live reading: 2026_09_ARI_SEA (no wind, temperature, rain), 2026_09_GB_NE (no wind, temperature, rain), 2026_09_LV_SF (no wind, temperature, rain), 2026_09_TB_CHI (no wind, temperature, rain) |
| WARN | warnings from wind_live (last 36 hours) | 5: 2026_09_LV_SF: wind reading from GFS MOS alone (the other forecast is missing), not the two-model mean; 2026_09_ARI_SEA: reading from GFS run 2026-11-07T12Z (logged 2026-11-07T18-27-41Z) is more than 6 hours behind the newest run (2026-11-08T12Z); not used; 2026_09_GB_NE: reading from GFS run 2026-11-07T12Z (logged 2026-11-07T18-27-41Z) is more than 6 hours behind the newest run (2026-11-08T12Z); not used; 2026_09_LV_SF: reading from GFS run 2026-11-07T12Z (logged 2026-11-07T18-27-41Z) is more than 6 hours behind the newest run (2026-11-08T12Z); not used |
| OK | drift monitor: numbers that move the edge are at their long-run level | 11 measures within noise; 0 to watch |

Result: FAIL
