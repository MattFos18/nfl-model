# Health check, 2026-10-05 13:26 UTC

**BROKEN**: 2 failing, 4 warnings, 56 ok.

| Level | Check | Detail |
|---|---|---|
| OK | weekly run is fresh | last run 2026-10-05 05:21 UTC, 8 hours ago (limit 72) |
| FAIL | every step of the latest run ok | tie check (sources): error, tie check (page): error |
| OK | latest run has the step: verify | present |
| OK | latest run has the step: tie check (sources) | present |
| OK | latest run has the step: tie check (page) | present |
| OK | latest run has the step: export data room | present |
| OK | latest run has the step: record picks | present |
| OK | latest run has the step: standing checks | present |
| OK | picks week's sources | week 4: in play; the week before it is complete |
| OK | runs in the last seven days | 146 (four scheduled: Tue, Thu, Sat, Sun) |
| OK | verification suite passed | Result: PASS |
| FAIL | tie-out passed | Result: FAIL (258 of 260 tie) |
| OK | line watch is logging | last snapshot 0.0 hours ago, 433 in the last seven days (every 30 minutes when GitHub's cron fires) |
| OK | line watch returns rows | 0 of 124 snapshots in the last two days logged no lines |
| OK | live forecast pull (wind_live) ok in the line watch | no failure in the 69 snapshots of the last day |
| OK | kickoff forecasts are fresh | fetched 4 hours ago (limit 96) |
| OK | kickoff forecast for every outdoor game inside the window | 0 of 0 games have a reading |
| OK | GFS MOS reading for every US outdoor game within 59 hours of kickoff | 0 of 0 games have one |
| OK | live weather priced on GFS MOS (the backtest's source) | 0 of 0 games on GFS MOS; 0 on the expected Open-Meteo fallback (more than 59 hours out, or abroad) |
| OK | picks file for Week 4, 2026 | picks_2026_wk4.csv |
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
| OK | shadow rule recorded for the week: shadowteasedog | picks: ['ATL +1.5']; tracker: ['ATL +1.5'] |
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
| OK | page data is fresh | built 8 hours ago (limit 96) |
| OK | cards carry the newest line snapshot | cards 2026-10-05T13-24-10Z, log 2026-10-05T13-24-10Z |
| OK | props panel carries the newest prop-line pull | page 2026-10-05T08-52-27Z, log 2026-10-05T08-52-27Z |
| OK | injury reports cover the week being priced | raw injuries not on this machine (the weekly run checks them) |
| OK | page rankings use the code's QB replacement level | page -0.12, code -0.12 |
| OK | QB-out check loaded the injury reports (week 4) | ok |
| OK | QB swaps priced this week (week 4) | no named starter ruled out |
| WARN | ESPN Out/Doubtful players all matched to a roster player | 7 unmatched: ARI Cameron Robertson, BUF Mike Danna, HOU Nate Thomas, MIA Robert Beal Jr., NYJ Kiko Mauigoa, PHI Hollywood Brown, PIT Gabriel Rubio |
| WARN | warnings from live weather (last 36 hours) | 1: 2026_04_IND_WAS: no GFS MOS reading for wind, temp, rain; priced on Open-Meteo |
| WARN | warnings from standing checks (last 36 hours) | 1: last game's starting QB ruled out and qb_out = 1 (picks week): 1 of 30: 2026_04_IND_WAS WAS |
| WARN | warnings from wind_live (last 36 hours) | 11: 2026_04_DEN_SF: wind reading from GFS MOS alone (the other forecast is missing), not the two-model mean; 2026_04_LAC_SEA: wind reading from GFS MOS alone (the other forecast is missing), not the two-model mean; 2026_04_DET_CAR: wind reading from GFS MOS alone (the other forecast is missing), not the two-model mean; 2026_04_DAL_HOU: reading from GFS run 2026-10-02T12Z (logged 2026-10-02T16-30-10Z) is more than 6 hours behind the newest run (2026-10-04T12Z); not used |
| OK | drift monitor: numbers that move the edge are at their long-run level | 11 measures within noise; 0 to watch |

Result: FAIL
