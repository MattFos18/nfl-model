# Health check, 2026-10-19 13:27 UTC

**HEALTHY**: 0 failing, 5 warnings, 57 ok.

| Level | Check | Detail |
|---|---|---|
| OK | weekly run is fresh | last run 2026-10-19 09:56 UTC, 4 hours ago (limit 72) |
| OK | every step of the latest run ok | 42 steps ok |
| OK | latest run has the step: verify | present |
| OK | latest run has the step: tie check (sources) | present |
| OK | latest run has the step: tie check (page) | present |
| OK | latest run has the step: export data room | present |
| OK | latest run has the step: record picks | present |
| OK | latest run has the step: standing checks | present |
| OK | picks week's sources | week 6: in play; the week before it is complete |
| OK | runs in the last seven days | 121 (four scheduled: Tue, Thu, Sat, Sun) |
| OK | verification suite passed | Result: PASS |
| OK | tie-out passed | Result: PASS (260 of 260 tie) |
| OK | line watch is logging | last snapshot 0.0 hours ago, 452 in the last seven days (every 30 minutes when GitHub's cron fires) |
| OK | line watch returns rows | 0 of 127 snapshots in the last two days logged no lines |
| OK | live forecast pull (wind_live) ok in the line watch | no failure in the 69 snapshots of the last day |
| OK | kickoff forecasts are fresh | fetched 4 hours ago (limit 96) |
| OK | kickoff forecast for every outdoor game inside the window | 2 of 2 games have a reading |
| OK | GFS MOS reading for every US outdoor game within 59 hours of kickoff | 1 of 1 games have one |
| WARN | live weather priced on GFS MOS (the backtest's source) | 1 of 2 games on GFS MOS; 1 on the expected Open-Meteo fallback (more than 59 hours out, or abroad): 2026_07_NE_CHI |
| OK | picks file for Week 6, 2026 | picks_2026_wk6.csv |
| OK | tracker holds the week's flags | picks: []; tracker: [] |
| OK | shadow rule recorded for the week: shadow45 | picks: []; tracker: [] |
| OK | shadow rule recorded for the week: shadowdog | picks: []; tracker: [] |
| OK | shadow rule recorded for the week: shadowearly | picks: []; tracker: [] |
| OK | shadow rule recorded for the week: shadowtrees | picks: []; tracker: [] |
| OK | shadow rule recorded for the week: shadowunder | picks: ['Under 52.5']; tracker: ['Under 52.5'] |
| OK | shadow rule recorded for the week: shadowunderearly | picks: ['Under 52.5']; tracker: ['Under 52.5'] |
| OK | shadow rule recorded for the week: shadowhook | picks: []; tracker: [] |
| OK | shadow rule recorded for the week: shadowroad6 | picks: []; tracker: [] |
| OK | shadow rule recorded for the week: shadowroad | picks: []; tracker: [] |
| OK | shadow rule recorded for the week: shadowunder60 | picks: []; tracker: [] |
| OK | shadow rule recorded for the week: shadowunderprime | picks: ['Under 52.5']; tracker: ['Under 52.5'] |
| OK | shadow rule recorded for the week: windunder | picks: ['Under 52.5']; tracker: ['Under 52.5'] |
| OK | shadow rule recorded for the week: shadowteasedog | picks: []; tracker: [] |
| OK | shadow rule recorded for the week: shadowrain | picks: []; tracker: [] |
| OK | shadow rule recorded for the week: shadowcold | picks: []; tracker: [] |
| OK | shadow rule recorded for the week: shadowunder3 | picks: []; tracker: [] |
| OK | shadow rule recorded for the week: shadowunderwind | picks: ['Under 52.5']; tracker: ['Under 52.5'] |
| OK | shadow rule recorded for the week: shadowtreestotal | picks: []; tracker: [] |
| OK | shadow rule recorded for the week: shadowwestcoast | picks: []; tracker: [] |
| OK | shadow rule recorded for the week: shadowroaddog | picks: []; tracker: [] |
| OK | shadow rule recorded for the week: shadowsmalldog | picks: []; tracker: [] |
| OK | shadow rule recorded for the week: shadowdog35 | picks: []; tracker: [] |
| OK | shadow rule recorded for the week: shadowwk4 | picks: []; tracker: [] |
| OK | shadow rule recorded for the week: shadowwk15 | picks: []; tracker: [] |
| OK | shadow rule recorded for the week: shadow6 | picks: []; tracker: [] |
| OK | shadow rule recorded for the week: shadowoverlow | picks: []; tracker: [] |
| OK | shadow rule recorded for the week: shadowqtotals | picks: ['Under 52.5']; tracker: ['Under 52.5'] |
| OK | page flag threshold = code | page 4.0, code 4.0 |
| OK | page inputs = code | 17 on the page, 17 in code |
| OK | page data is fresh | built 3 hours ago (limit 96) |
| OK | cards carry the newest line snapshot | cards 2026-10-19T13-25-50Z, log 2026-10-19T13-25-50Z |
| OK | props panel carries the newest prop-line pull | page 2026-10-19T10-55-03Z, log 2026-10-19T10-55-03Z |
| OK | injury reports cover the week being priced | raw injuries not on this machine (the weekly run checks them) |
| OK | page rankings use the code's QB replacement level | page -0.12, code -0.12 |
| OK | QB-out check loaded the injury reports (week 6) | ok |
| OK | QB swaps priced this week (week 6) | no named starter ruled out |
| WARN | ESPN Out/Doubtful players all matched to a roster player | 17 unmatched: BAL Matt Hibner, BUF Mike Danna, CIN Swayze Bozeman, CIN Tanner Hudson, DET Ben Bartch, DET Brian Branch, DET Cade Mays, DET Devin White |
| WARN | warnings from data checks (last 36 hours) | 1: played outdoor games since 2015 without every forecast reading: 0 partial, 1 missing |
| WARN | warnings from live weather (last 36 hours) | 2: 2026_07_NE_CHI: no GFS MOS reading for wind, temp, rain; priced on Open-Meteo; 2026_06_HOU_JAX: no GFS MOS reading for wind, temp, rain; priced on Open-Meteo |
| WARN | warnings from wind_live (last 36 hours) | 5: 2026_06_DAL_GB: wind reading from GFS MOS alone (the other forecast is missing), not the two-model mean; 2026_06_WAS_SF: wind reading from GFS MOS alone (the other forecast is missing), not the two-model mean; 2026_06_LAC_KC: wind reading from GFS MOS alone (the other forecast is missing), not the two-model mean; 2026_06_NYJ_NE: wind reading from GFS MOS alone (the other forecast is missing), not the two-model mean |
| OK | drift monitor: numbers that move the edge are at their long-run level | 11 measures within noise; 0 to watch |

Result: PASS
