# Standing checks

Every bug class fixed on 1-2 Oct 2026, checked again (nflmodel/standing_checks.py; the list: docs/wiki/checks.md).

| Level | Check | Detail |
|---|---|---|
| OK | QB priced on every unplayed picks-week side is not ruled out (Out, Doubtful, off the active roster) | 0 of 28 |
| OK | qb_out = 1 only when last game's starting QB is ruled out (picks week) | 0 of 28 |
| OK | last game's starting QB ruled out and qb_out = 1 (picks week) | 0 of 28 |
| OK | unplayed games at retractable-roof stadiums have a roof (blank counts as closed: build.RETRACTABLE_HOME) | 0 of 33 |
| OK | cards price unplayed retractable-roof games (roof not announced open) as roofed, not outdoors | 0 of 33 |
| OK | no wind, rain or temperature reading for a game under a roof (wind_live readings) | 0 of 1903 |
| OK | cards of roofed games carry no wind and no weather bet (wind under, rain, cold) | 0 |
| OK | forecast columns read for a reading are all pre-kickoff runs (forecast_history.PRE_KICKOFF_WIND has no POST_KICKOFF column) | 0 |
| OK | stored forecasts: every GFS and NBS run read was issued 5+ hours before kickoff | 0 of 2447 |
| OK | live forecasts (wind_live.csv): every row fetched before kickoff on a GFS run 5+ hours before | 0 of 651 |
| OK | forecast readings plausible (wind 0 to 40 mph, rain chance 0 to 100, temperature -40 to 130 F) | 0 of 6546 |
| OK | every recorded live bet was logged before its game kicked off | 0 of 18 |
| OK | no card chance priced at a line other than the card's (no stored fit: chances cleared where the line moved) | 0 of 15 |
| OK | index.html names no hidden shadow and every PK.rules list drops hidden rules | 0 |
| OK | meta.js marks every hidden shadow hidden | 0 of 19 |
| OK | the bet files graded as live bets (clv.RULE_FILES) are the live rules only (spread flag, totals flag, wind under) | 0 of 3 |
| OK | qtotals shadow: no page file names its columns or bet, no card carries them, hidden and never a live bet | 0 |
| OK | qtotals shadow: its last run left the live table (pred_v3) unchanged | 0 |
| OK | qtotals shadow: priced beside the live table there now (pred_v3 not re-run since) | 0 |
| OK | one unit a bet: no Kelly stake or stake_pct on the page or in the picks file | 0 |
| OK | appended logs: every row has the header's fields (rule_history, pred_history, the bet trackers) | 0 of 7070 |
| OK | future-data leak: ratings for 2024 Weeks 1-9 unchanged when later games are corrupted (audit.leakage_test) | largest change 0 |
| OK | future-data leak: 2024 Weeks 1-9 predictions unchanged when later targets are corrupted (audit.leakage_test) | largest change 0 |
| OK | future-data leak: 2024 Week 9 games' own predictions unchanged when their own scores are corrupted (audit.leakage_test) | largest change 0 |
| OK | same-game leak: 2026 Week 4 games' own predictions unchanged when their own scores are corrupted (audit.own_game_shift) | largest change 0 |
| OK | live model_total and p_over_emp the same with and without the qtotals shadow (2026 Week 4) | 0 of 16 |
| OK | the stored tables still reproduce pred_v3's totals (2026 Week 4) | 0 of 16 |

Result: PASS (27 of 27)
