# Log

One dated line per change to the model, the bet rules, the data sources or the way we work. Newest first. The full
record of every study stays in `reports/decision_log.md`; this is the short version to skim at session start.

## 3 Oct 2026
- Props follow the QB the game model priced: `props.main` took the schedule's named starter, so SEA's props still showed Drew Lock after the starter check; it now uses `features_asof.qb_id` wherever ratings overrode a stale named starter (`qb_named_over`).
- QB starter check (`ratings.build_features`): the schedule named Drew Lock for SEA week 4 (a week-2 fill-in) though Sam Darnold started week 3 and is healthy. For unplayed games, a named QB who is not the team's regular starter is overridden by the regular when the regular is not ruled out; a start while the regular was Out/Doubtful counts as a fill-in. Overrides print a warning and go to `data/runs/qb_swaps.json` (`conflicts`); the card shows the QB priced. Only SEA's unplayed games changed; no bet changed.
- Site-health alert fixed: #343 had deleted `health_alert._sync_issue` while `main()` still called it inside a try/except, so no failing check opened or closed the `site-health` issue from 30 Sep to 3 Oct; restored, with `tests/test_health_alert_sync.py` calling `main()`.
- `tools/scrape.py` (#420): saves public pages as clean text for research; robots.txt respected, blocks never bypassed, output and log in gitignored `data/private/research/`.
- Breakdown cards (page only): expected points as a banner at the top; Spread, Total and Win in three equal columns with rows lined up (CSS subgrid), stacked on phones; line charts drawn at their shown size, label rows chosen to keep clear of the other line; moneyline splits show each side's price (`export_web._add_consensus` fills the consensus ml odds from the newest consensus moneylines).
- Seven inputs dropped (Matt's yes; reports/drop_seven_inputs.md): neutral, dome, rain, div_game, qb_out out of `model.FEATS` (22 -> 17), pf_sum and qb_out_sum out of `model.TOTAL_FEATS` (11 -> 9); margin miss better on every window; readings kept for cards and checks; props_by_season constants drift after the weekly run.
- Input ablation (reports/input_ablation.md): all 47 live pieces drop-one with placebos; 3 earn their spot, 24 thin, 20 fail; the seven failing inputs with no flag cost, dropped together, cost one net spread-flag win and 0.0003 of total miss on 2019-22, so nothing changes; left for Matt.
- Spread: eight new ways to build the team ratings (spread_new_ideas): none passes, each misses the margin worse on 2015-18; no change.
- Old ideas retested on the honest backtest (reports/old_ideas_retest.md): 13 near misses from before the 1-2 Oct fixes rerun as first specified; none passes, nothing changes (near misses: drop QB out, drop cold from the total, drop dome from the points equation).
- Relative pace studied (reports/relative_pace.md): pace against the league's own average, three forms; all still fail 2023-25, so the league slowdown was not why pace failed; nothing changed.
- New totals ideas studied (reports/totals_new_ideas.md): pace, neutral pace, red-zone TD rate, explosive plays, kicker, turf, altitude, and two over-chance constructions; none passes, nothing changed.

## 2 Oct 2026
- Questionable-in-totals (questionable_totals T2) tracked as hidden shadow `shadowqtotals`: its own total each weekly run (`nflmodel/qtotals.py`, step "qt shadow"), the under at 55%+, never bet; the live model unchanged (standing checks `qt_isolated`, `qt_stays_off`).
- Forecast history extended to 2015 (`forecast_history.FIRST`): GFS MOS from 2015, Japan from Jan 2016, no NBS; 2015-17 backtest priced on the forecast; moves the live total through the rain input and wind pool (reports/forecast_history_2015.md; Matt approved).
- Live weather follow-ups (review of #399): a weather source change re-prices; stale MOS readings (2+ runs behind) are dropped; health fails a US outdoor game within 59 hours with no MOS reading and shows the live forecast pull; the re-price rain call matches trends'.
- Standing checks: every bug class fixed 1-2 Oct re-checked on every run (`nflmodel/standing_checks.py`, `docs/wiki/checks.md`); leak tests in the weekly step "standing checks"; stake code #385 left in unused page code removed.
- Live games priced on the backtest's weather: GFS MOS / Japan reading for wind, temperature and rain (`weather.live_source`), Open-Meteo only as a logged fallback; opponent strength centred as of the week; leak checks no longer rewrite the trees cache (reports/live_weather_match.md).
- Overs studied in depth (reports/overs_deep.md): no over bet, no model change; the over at totals of 41 or lower with a 55%+ raw chance tracked as hidden shadow `shadowoverlow`.
- Questionable players in the totals equation only (questionable_totals): not adopted, total miss worse on 2015-18.
- Calibrations rechecked on the honest backtest: cover, over and home win still beat raw on every window; the teaser legs lose one window each, left for Matt; spread cut table report only (reports/calibration_recheck.md).
- The backtest prices played games (2018 on) on the stored pre-kickoff forecast, not the weather that happened: `model.priced_weather`; QB form re-passes, wind points and the totals' rain fail the pre-registered bar (one and two checks), left for Matt; no wind curve beats the bands (reports/forecast_weather_backtest.md).
- Follow-ups: ESPN names match with suffixes dropped (`players.name_key`); a failed model step records no bets; weather fallbacks and forecast gaps are health warnings (`nflmodel/warnlog.py`).
- Live failures made loud: QB-out check errors fail the ratings step and health (`data/runs/qb_swaps.json`), replacement QB must be ACT, card names the QB priced, ESPN statuses only after last week's final kickoff, rule_history appends by column.
- Referee input (`ref_tot`) dropped from the totals equation: with the same-game leak fixed it fails the rule (#387).
- Two backtest leaks fixed: the referee prior counted the same game; Japan's wind used its post-kickoff run (now the day-before run); rescored in reports/leak_fix_rescore.md (#384).
- One unit a bet; quarter-Kelly retired from the page (#385).
- Data fixes: the starting QB who played, games abroad at their real site, recorded wind checked against the archive, the line before kickoff; new data checks (reports/data_fixes.md).
- Project wiki (`docs/wiki/`), `study` and `ship` skills, and the data-checker, site-fact-checker and pr-reviewer agents added.
- A named starter ruled out this week sets `qb_out` (#380).
- Every promising rule not adopted tracked as a hidden shadow, the rain under (`shadowrain`) among them (#379).
- Cards show only real bets; reverse line move chip (#377).
- A QB ruled out this week is priced at his replacement, not the named starter: `ratings.qbs_out_now` (#376).
- Cards' live badge comes from the page's own ESPN fetch (#375).

## 1 Oct 2026
- Injury retest (Questionable at the measured sit chance, linemen and defenders out): not adopted, costs the spread flag or fails a window (#374).
- Closing line value tracked on the live bets (`nflmodel/clv.py`); tracking only (#373).
- Wind and cold learned from forecasts instead of the weather that happened: not adopted.
- Blind rain under (GFS rain chance 50%+) re-tested on top of the new model: candidate hidden shadow (added 2 Oct as `shadowrain`, #379).
- Forecast rain (GFS MOS 50%+) in the totals equation: adopted with Matt's yes (`model.RAIN_FC`, #366).
- Rain, cold and gust bands re-tested on forecasts: none adopted; MOS 99 missing-wind bug fixed (#365).
- Wind points in the model's total: adopted (`model.wind_points`, #363).
- Wind under (forecast wind 10+ mph, outdoor, weeks 1-17) adopted as a bet (`picks.WIND_UNDER`, `wind_live.py`, #362).
- ESPN fills injury statuses player by player (#360); inactives logged from ESPN game rosters, not priced (#361).
- Study gate, data checks and bet-math tests (#370); Gitleaks hook, public-repo rules, model-auditor agent (#369).
- Unders at 60%+ and prime-time unders tracked as hidden shadows (`shadowunder60`, `shadowunderprime`).
