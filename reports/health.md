# Health check, 2026-10-26 19:09 UTC

**BROKEN**: 5 failing, 3 warnings, 53 ok.

| Level | Check | Detail |
|---|---|---|
| OK | weekly run is fresh | last run 2026-10-25 16:57 UTC, 26 hours ago (limit 72) |
| FAIL | every step of the latest run ok | props: error, tie check (sources): error, tie check (page): error |
| OK | latest run has the step: verify | present |
| OK | latest run has the step: tie check (sources) | present |
| OK | latest run has the step: tie check (page) | present |
| OK | latest run has the step: export data room | present |
| OK | latest run has the step: record picks | present |
| OK | latest run has the step: standing checks | present |
| OK | picks week's sources | week 7: in play; the week before it is complete |
| OK | runs in the last seven days | 49 (four scheduled: Tue, Thu, Sat, Sun) |
| OK | verification suite passed | Result: PASS |
| FAIL | tie-out passed | Result: FAIL (254 of 260 tie) |
| FAIL | line watch is logging | last snapshot 26.1 hours ago, 186 in the last seven days (every 30 minutes when GitHub's cron fires) |
| OK | line watch returns rows | 0 of 1 snapshots in the last two days logged no lines |
| OK | live forecast pull (wind_live) ok in the line watch | no failure in the 0 snapshots of the last day |
| OK | kickoff forecasts are fresh | fetched 30 hours ago (limit 96) |
| OK | kickoff forecast for every outdoor game inside the window | 7 of 7 games have a reading |
| FAIL | GFS MOS reading for every US outdoor game within 59 hours of kickoff | 0 of 1 games have one; missing (wind, temperature or rain not on MOS, or no GFS wind): 2026_07_DAL_PHI |
| OK | live weather priced on GFS MOS (the backtest's source) | 5 of 7 games on GFS MOS; 0 on the expected Open-Meteo fallback (more than 59 hours out, or abroad) |
| OK | picks file for Week 7, 2026 | picks_2026_wk7.csv |
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
| OK | page data is fresh | built 26 hours ago (limit 96) |
| OK | cards carry the newest line snapshot | cards 2026-10-25T17-02-00Z, log 2026-10-25T17-02-00Z |
| FAIL | props panel carries the newest prop-line pull | page 2026-10-22T06-30-05Z, log 2026-10-24T17-12-53Z |
| OK | injury reports cover the week being priced | raw injuries not on this machine (the weekly run checks them) |
| OK | page rankings use the code's QB replacement level | page -0.12, code -0.12 |
| OK | QB-out check loaded the injury reports (week 7) | ok |
| OK | QB swaps priced this week (week 7) | PHI Jalen Hurts -> Tanner McKee (depth chart) |
| WARN | ESPN Out/Doubtful players all matched to a roster player | 14 unmatched: BUF C.J. Gardner-Johnson, CLE Audric Estime, HOU Jake Hummel, HOU Nate Thomas, JAX Anton Harrison, LAC Alec Ingold, LAC Denzel Perryman, MIA Robert Beal Jr. |
| WARN | warnings from data checks (last 36 hours) | 1: games inside the forecast window without every live reading: 2026_07_CIN_BAL (no wind, temperature, rain), 2026_07_CLE_TEN (no wind, temperature, rain), 2026_07_DAL_PHI (no wind, temperature, rain), 2026_07_KC_SEA (no wind, temperature, rain), 2026_07_MIA_NYJ (no wind, temperature, rain), 2026_07_TB_CAR (no wind, temperature, rain) |
| WARN | warnings from wind_live (last 36 hours) | 7: 2026_07_DAL_PHI: reading from GFS run 2026-10-25T12Z (logged 2026-10-25T17-01-58Z) is more than 6 hours behind the newest run (2026-10-26T12Z); not used; 2026_07_CIN_BAL: reading from GFS run 2026-10-24T12Z (logged 2026-10-24T17-13-01Z) is more than 6 hours behind the newest run (2026-10-25T12Z); not used; 2026_07_CLE_TEN: reading from GFS run 2026-10-24T12Z (logged 2026-10-24T17-12-47Z) is more than 6 hours behind the newest run (2026-10-25T12Z); not used; 2026_07_DAL_PHI: reading from GFS run 2026-10-24T12Z (logged 2026-10-24T17-12-47Z) is more than 6 hours behind the newest run (2026-10-25T12Z); not used |
| OK | drift monitor: numbers that move the edge are at their long-run level | 11 measures within noise; 0 to watch |

Result: FAIL
