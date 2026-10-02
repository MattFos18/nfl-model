# Standing checks

Every bug class found and fixed on 1-2 Oct 2026, and the check that would catch it again. A check runs on its own every
run; a test runs on every pull request (the code it guards cannot change without one). New checks of 2 Oct 2026 live in
`nflmodel/standing_checks.py` (tests: `tests/test_standing_checks.py`, a planted bad row for each); its report is
`reports/standing_checks.md`.

Where a check runs:
- **tie check**: `tie_check --page`, in the weekly run (step "tie check (page)") and every line watch (every 30 minutes). A
  failing row fails the step and shows on the page's health chip (`web/data/health.js`).
- **standing step**: the weekly run's step "standing checks" (`python -m nflmodel.standing_checks`): the tie check's rows
  plus the leak tests (about a minute). A FAIL fails the step; `health.py` fails when the step failed or is missing.
- **data checks**: the weekly run's step "data checks" (`nflmodel/data_checks.py`).
- **health**: `nflmodel/health.py` after every run; WARN rows include every `warnlog.warn` of the last 36 hours (a
  standing check's WARN goes there too).

| Bug class (date, PR) | Check | Runs in | Catches |
|---|---|---|---|
| Same-game leak: the referee prior counted the game's own total (2 Oct, #384) | `standing_checks.leaks`: `audit.own_game_shift` on the newest played week, and on 2024 Week 9 | standing step | any change in a game's own team points, total or under chance when its own score is corrupted; `tests/test_same_game_leak.py` |
| Future-data leak | `standing_checks.leaks`: `audit.leakage_test` (2024 Weeks 10 on corrupted) | standing step | any change in 2024 Weeks 1-9 ratings or predictions |
| Japan's post-kickoff run read as a forecast (2 Oct, #384) | `forecasts_before_kickoff`: `PRE_KICKOFF_WIND` holds no `POST_KICKOFF` column | tie check | `jma_wind_d0` (or any post-kickoff column) put back into a reading |
| Forecast run issued at or after kickoff (live and history) | `forecasts_before_kickoff`: every stored GFS/NBS d0 run 5+ hours before kickoff; every `wind_live.csv` row fetched before kickoff on a run 5+ hours before | tie check | a reading built from a run a live bet could not have had. Open-Meteo's kickoff hour is re-fetched up to a day after kickoff for games already started (by design, `gotchas.md`); bets are covered by the next rows |
| Backtest priced on the weather that happened (2 Oct, #389) | `tests/test_priced_weather.py` | tests | `model.priced_weather` bypassed |
| Starting QB ruled out but priced (2 Oct, #376) | `qb_priced_not_out`: no unplayed picks-week side priced at a QB Out, Doubtful or off the roster; tie row "this week's QB swaps = the cards' QB names" | tie check | the WAS card pricing Daniels after ESPN ruled him Out |
| `qb_out` set for a named starter already replaced (2 Oct, #380, #396) | `qb_out_is_last_starter`: `qb_out = 1` only when a QB of the team's last game is ruled out (FAIL); last game's starter out with `qb_out = 0` (WARN) | tie check | WAS reading 1 for Daniels when Mariota started Week 3 |
| QB-out check swallowed errors; replacement from a stale depth chart; card named the QB ruled out (2 Oct, #390) | health "QB-out check loaded the injury reports" (FAIL on error) and "QB swaps priced this week" (WARN on a prior or unconfirmed QB); tie rows "QB-out check: the injury load ... ran without an error" and the QB-swap row | health, tie check | `tests/test_live_hardening.py` |
| ESPN Out/Doubtful players unmatched (suffixes; 2 Oct) | health "ESPN Out/Doubtful players all matched to a roster player" (WARN); tie row "every player ESPN lists Out or Doubtful ... is counted on its card" | health, tie check | a nickname or suffix that matches no roster player |
| ESPN statuses carried over the week change (2 Oct) | `players.espn_fresh` in the tie row above; health "injury reports cover the week being priced" | tie check, health | `tests/test_live_hardening.py` |
| A failed model step still recorded bets (2 Oct) | `weekly.pick_week` logs the pick steps "skipped"; health "every step of the latest run ok" fails | health | `tests/test_live_followups.py` |
| Weather fallbacks were silent (2 Oct) | `warnlog.warn` -> health WARN rows; data checks' forecast coverage rows | health, data checks | an older MOS pull, a one-model wind, a reader pricing games calm |
| Retractable roof blank on an unplayed game, priced as outdoors (2 Oct, #391) | `retractable_roofs`: no unplayed ATL/DAL/HOU/IND/ARI home game (or the Bernabeu) with a blank roof; no such card priced outdoors unless the roof was announced open | tie check | the wind under at 2026_04_DAL_HOU |
| Weather reading under a roof (2 Oct, #391) | `no_weather_under_roof`: no wind, rain or temperature reading for a dome or closed game; no card wind or weather bet (wind under, rain, cold, under-wind) on one | tie check | `wind_live._roofed` filter dropped |
| Line snapshot after kickoff used (2 Oct, #381) | tie rows "card line = the lines log's consensus now (newest snapshot per game before kickoff ...)" and "no unplayed game priced on the schedule's line ..."; `bets_before_kickoff`: every recorded live bet logged before kickoff | tie check | 2026_03_LA_DEN's post-kickoff line; a bet logged after kickoff |
| Game abroad or neutral site at the wrong or an unknown venue (2 Oct, #381, #382) | data checks "neutral-site and overseas games at their real stadium and roof (venues.py)" | data checks | a new stadium id `venues.VENUE` lacks |
| Implausible wind (schedule typos; NWS MOS 99/999 sentinels; 1-2 Oct, #365, #381) | data checks "kickoff wind 40 mph or under"; `plausible_weather`: every forecast reading wind 0-40 mph, rain 0-100%, temperature -40 to 130 F, Open-Meteo kickoff readings too | data checks, tie check | 71 mph at Pittsburgh; 2018_16_BAL_LAC's 20 mph built from a 99 |
| Listed starting QB who never played; played game without play-by-play (2 Oct, #381, #382) | data checks "every played game's starting QB dropped back in it", "every played game has play-by-play" | data checks | |
| Props constants drift (2 Oct, #386, #397) | tie rows "props team fit constants = props_backtest6.csv", "props by-season run = the adopted rule's rows ... (within 0.2)", the longest-play, kicker and count constants rows | tie check | a page constant out of step with its backtest |
| Chances priced at a line other than the card's (2 Oct, #395) | tie row "card chances (win, cover, over) = the model's fit priced at the card's line" (with the stored fit); `chances_at_card_line` (without it: no chance where the line moved) | tie check | a totals flag firing on a chance from the schedule's line; `tests/test_stale_chance_guard.py` |
| Hidden shadows leaking onto the page or into bets (2 Oct, #379) | `shadows_stay_off`: index.html names no hidden shadow and every `PK.rules` list drops hidden rules; meta.js marks each hidden; the bet files graded as live bets (`clv.RULE_FILES`) are the spread flag, totals flag and wind under only | tie check | `tests/test_more_shadows.py` |
| Questionable-in-totals shadow touching the live model or the page (2 Oct, hidden shadow `shadowqtotals`) | `qt_isolated`: the live totals equation for the newest fully played week recomputed before the shadow's fit, after it and on the table carrying its columns, all equal and equal to pred_v3's model_total and p_over_emp, `model.TOTAL_FEATS` and `_game_frame` untouched, no `qt_` column in pred_v3; `qt_stays_off`: no page file (index.html, web/data) names `qt_model_total`, `qt_p_over_emp`, `shadowqtotals_bet` or the shadow's files (kept in `data/processed/shadow/`, which the page's data catalog does not list), no card carries a `qt_` key, the rule hidden and no live bet file, the shadow's run left pred_v3's hash unchanged (WARN when the model re-ran without it) | standing step; tie check | `tests/test_qt_shadow.py` |
| Kelly stake text reappearing (2 Oct, #385: one unit a bet) | `one_unit`: index.html renders no `stake_pct` and says no "Kelly" outside a comment; the picks file says no Kelly or "% at" stake | tie check | the stake code #385 left behind (the unused "Bet logged" chip and log table still printed `stake_pct`; removed 2 Oct) |
| Logs appended by position (2 Oct, `rule_history.csv`) | `logs_by_column`: every row of rule_history, pred_history and the live-bet trackers has the header's fields | tie check | a new `*_bet` column shifting later rows |
