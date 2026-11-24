# Health check, 2026-11-24 00:43 UTC

**BROKEN**: 5 failing, 6 warnings, 51 ok.

| Level | Check | Detail |
|---|---|---|
| OK | weekly run is fresh | last run 2026-11-22 20:06 UTC, 29 hours ago (limit 72) |
| FAIL | every step of the latest run ok | props: error, tie check (sources): error, tie check (page): error |
| OK | latest run has the step: verify | present |
| OK | latest run has the step: tie check (sources) | present |
| OK | latest run has the step: tie check (page) | present |
| OK | latest run has the step: export data room | present |
| OK | latest run has the step: record picks | present |
| OK | latest run has the step: standing checks | present |
| OK | picks week's sources | week 11: in play; the week before it is complete |
| WARN | runs in the last seven days | 2 (four scheduled: Tue, Thu, Sat, Sun) |
| OK | verification suite passed | Result: PASS |
| FAIL | tie-out passed | Result: FAIL (253 of 259 tie) |
| FAIL | line watch is logging | last snapshot 28.6 hours ago, 2 in the last seven days (every 30 minutes when GitHub's cron fires) |
| OK | line watch returns rows | 0 of 1 snapshots in the last two days logged no lines |
| OK | live forecast pull (wind_live) ok in the line watch | no failure in the 0 snapshots of the last day |
| OK | kickoff forecasts are fresh | fetched 34 hours ago (limit 96) |
| OK | kickoff forecast for every outdoor game inside the window | 11 of 11 games have a reading |
| FAIL | GFS MOS reading for every US outdoor game within 59 hours of kickoff | 0 of 1 games have one; missing (wind, temperature or rain not on MOS, or no GFS wind): 2026_11_CIN_WAS |
| WARN | live weather priced on GFS MOS (the backtest's source) | 7 of 11 games on GFS MOS; 1 on the expected Open-Meteo fallback (more than 59 hours out, or abroad): 2026_11_MIN_SF |
| OK | picks file for Week 11, 2026 | picks_2026_wk11.csv |
| OK | tracker holds the week's flags | picks: []; tracker: [] |
| OK | shadow rule recorded for the week: shadow45 | picks: []; tracker: [] |
| OK | shadow rule recorded for the week: shadowdog | picks: []; tracker: [] |
| OK | shadow rule recorded for the week: shadowearly | picks: []; tracker: [] |
| OK | shadow rule recorded for the week: shadowtrees | picks: []; tracker: [] |
| OK | shadow rule recorded for the week: shadowunder | picks: ['Under 54.5']; tracker: ['Under 54.5'] |
| OK | shadow rule recorded for the week: shadowunderearly | picks: ['Under 54.5']; tracker: ['Under 54.5'] |
| OK | shadow rule recorded for the week: shadowhook | picks: []; tracker: [] |
| OK | shadow rule recorded for the week: shadowroad6 | picks: []; tracker: [] |
| OK | shadow rule recorded for the week: shadowroad | picks: []; tracker: [] |
| OK | shadow rule recorded for the week: shadowunder60 | picks: ['Under 54.5']; tracker: ['Under 54.5'] |
| OK | shadow rule recorded for the week: shadowunderprime | picks: ['Under 54.5']; tracker: ['Under 54.5'] |
| OK | shadow rule recorded for the week: windunder | picks: ['Under 54.5']; tracker: ['Under 54.5'] |
| OK | shadow rule recorded for the week: shadowteasedog | picks: []; tracker: [] |
| OK | shadow rule recorded for the week: shadowrain | picks: []; tracker: [] |
| OK | shadow rule recorded for the week: shadowcold | picks: []; tracker: [] |
| OK | shadow rule recorded for the week: shadowunder3 | picks: ['Under 54.5']; tracker: ['Under 54.5'] |
| OK | shadow rule recorded for the week: shadowunderwind | picks: ['Under 54.5']; tracker: ['Under 54.5'] |
| OK | shadow rule recorded for the week: shadowtreestotal | picks: ['Under 54.5']; tracker: ['Under 54.5'] |
| OK | shadow rule recorded for the week: shadowwestcoast | picks: []; tracker: [] |
| OK | shadow rule recorded for the week: shadowroaddog | picks: []; tracker: [] |
| OK | shadow rule recorded for the week: shadowsmalldog | picks: []; tracker: [] |
| OK | shadow rule recorded for the week: shadowdog35 | picks: []; tracker: [] |
| OK | shadow rule recorded for the week: shadowwk4 | picks: []; tracker: [] |
| OK | shadow rule recorded for the week: shadowwk15 | picks: []; tracker: [] |
| OK | shadow rule recorded for the week: shadow6 | picks: []; tracker: [] |
| OK | shadow rule recorded for the week: shadowoverlow | picks: []; tracker: [] |
| OK | shadow rule recorded for the week: shadowqtotals | picks: ['Under 54.5']; tracker: ['Under 54.5'] |
| OK | page flag threshold = code | page 4.0, code 4.0 |
| OK | page inputs = code | 17 on the page, 17 in code |
| OK | page data is fresh | built 28 hours ago (limit 96) |
| OK | cards carry the newest line snapshot | cards 2026-11-22T20-09-04Z, log 2026-11-22T20-09-04Z |
| FAIL | props panel carries the newest prop-line pull | page 2026-10-22T06-30-05Z, log 2026-10-27T15-44-47Z |
| OK | injury reports cover the week being priced | raw injuries not on this machine (the weekly run checks them) |
| OK | page rankings use the code's QB replacement level | page -0.12, code -0.12 |
| OK | QB-out check loaded the injury reports (week 11) | ok |
| OK | QB swaps priced this week (week 11) | no named starter ruled out |
| WARN | ESPN Out/Doubtful players all matched to a roster player | 32 unmatched: ATL Divine Deablo, ATL Zachariah Branch, BUF Mike Danna, CLE Michael Burton, CLE Ronnie Hickman, GB Josh Jacobs, GB Kevin Zeitler, GB Luke Musgrave |
| WARN | warnings from data checks (last 36 hours) | 1: games inside the forecast window without every live reading: 2026_11_CIN_WAS (no wind, temperature, rain), 2026_11_LV_DEN (no wind, temperature, rain) |
| WARN | warnings from live weather (last 36 hours) | 2: 2026_11_MIN_SF: no GFS MOS reading for wind, temp, rain; priced on Open-Meteo; 2026_11_PIT_PHI: no GFS MOS reading for wind, temp, rain; priced on Open-Meteo |
| WARN | warnings from wind_live (last 36 hours) | 4: 2026_11_CIN_WAS: reading from GFS run 2026-11-22T12Z (logged 2026-11-22T20-09-02Z) is more than 6 hours behind the newest run (2026-11-23T18Z); not used; 2026_11_PIT_PHI: reading from GFS run 2026-11-21T12Z (logged 2026-11-21T20-22-05Z) is more than 6 hours behind the newest run (2026-11-22T12Z); not used; 2026_11_CIN_WAS: reading from GFS run 2026-11-21T12Z (logged 2026-11-21T20-22-05Z) is more than 6 hours behind the newest run (2026-11-22T12Z); not used; 2026_11_LV_DEN: reading from GFS run 2026-11-21T12Z (logged 2026-11-21T20-22-05Z) is more than 6 hours behind the newest run (2026-11-22T12Z); not used |
| OK | drift monitor: numbers that move the edge are at their long-run level | 11 measures within noise; 0 to watch |

Result: FAIL
