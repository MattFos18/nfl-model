# Audit: forecast_weather_backtest (2 Oct 2026)

**Verdict: holds with caveats.** A is a real look-ahead fix: no leak found, and the numbers reproduce exactly. B3 and C hold. B1 (wind points) and B2 (rain_fc) fail the bar the study set for itself before seeing results. The report then softened that, so keeping them is Matt's call, not a pass.

Sources: experiments/forecast_weather_backtest.py, reports/forecast_weather_backtest.md, reports/forecast_weather_backtest_results.md, reports/forecast_weather_backtest.csv, %TEMP%/forecast_weather_backtest/runs.pkl and placebo.pkl, plus the checks below. My scripts are in the session scratchpad. No repo file was edited by me.

## Checks

**1. Look-ahead: pass for A, with one older leak still in place.**
- **Forecast run times.** Each reading in `priced_weather` comes from a forecast run issued before kickoff.
  - GFS: `gfs_run_d0` is at least 5.0 hours before kickoff on all 1,568 stored rows; none is closer.
  - NBS: `nbs_run_d0` is at least 5.0 hours before kickoff on all 1,469 rows.
  - Japan: the model reads Japan's day-before run only (`FH.PRE_KICKOFF_WIND`). Its same-day run is excluded.
  - Rain and temperature come from the same GFS run (d0, falling back to the day-before run).
- **2026 live log.** No row of wind_live.csv was logged at or after kickoff (0 of 162). Its shortest lead from GFS run to kickoff is 6.25 hours. `wind_live.run` skips games that have started.
- **Training vs pricing.** Training rows keep the recorded weather, as a live fit does. Only played test rows are re-priced.
- **Weather corruption test (mine).** I corrupted the recorded wind, temperature and rain of the 12 outdoor 2024 week-9 games that have a stored forecast.
  - With `FORECAST_WEATHER = True`, those games' own prices moved by 0.
  - With it off, they moved by up to 9.69. So the old look-ahead was real and is now gone.
- **Every weather input checked.** I traced each weather input in `FEATS` and `TOTAL_FEATS`. Snow, cold_edge and wind_edge are not model inputs.
- **The older leak (not from this study): retractable roofs.** The backtest uses the roof state on game day.
  - 2018-25 has 295 closed-roof and 41 open-roof games at ARI, ATL, DAL, HOU and IND.
  - Closed-roof games count as domes. `forecast_history.games` also leaves them out of the stored forecasts.
  - Live, those stadiums' unplayed 2026 games have roof = NaN, so they count as outdoors. For example, 2026_04_DAL_HOU is in the live wind log.
  - So the wind under, wind points and rain_fc backtests skip the games where the roof closed, but live bets would include them. I could not size the effect.
- **Old weather kept elsewhere.** 2015-17 and the games abroad still use recorded weather. So the 2015-18 window is clean for 2018 only.
- **Still not the same as live.** Live upcoming games use Open-Meteo wind and temperature; the backtest uses GFS/NBS/Japan readings. The report says so. Not a leak.

**2. Market inputs: pass.** `priced_weather` and the readings use no lines, splits or prices. Lines are used only to grade.

**3. Every window: pass for the reproduction. A is a correctness fix, not an adoption.**
- **Reruns.** I reran the A, recorded and A_no_rain walk-forwards from scratch (about 70 seconds each, using the study's own tree fits). They match runs.pkl to 0.0 on home and away points, total, spread, over chance and wind points.
- **CSV.** All 21 CSV rows match my re-scoring.
- **Report vs results.** The report's A table matches the results file: spread 69-55 / 76-48 / 37-19, totals 132-117 / 190-146 / 82-59, wind under 24-20 / 143-88 / 77-52, team miss 7.4046 / 7.3645 / 7.2343, total miss 10.7507 / 10.5161 / 10.1029.
- **Re-pricing checks.**
  - The rebuilt wind points equal `model.wind_points` (max difference 5.6e-16).
  - Re-pricing the over chance with the run's own wind points gives exactly the run's values (difference 0).
  - Wind points are zero in every 2015-18 game. That window is identical by construction.
- **Caveat on the numbers.** This "recorded" baseline does not match the latest published numbers in the decision log (the referee-drop row: totals flag 138-126 / 182-142 / 75-57; spread flag 68-55 / 80-51 / 40-21). Here it is 130-117 / 185-149 / 70-57 and 69-56 / 79-51 / 37-18. The laptop data differs from GitHub's. Also, the trees for the re-priced games were fit on this laptop. So GitHub's numbers will move; do not quote these as final.

**4. Placebo: pass for B3, borderline for B2, fail for B1 on team points.** 50 draws each. The shuffles are set up correctly:
- B2 shuffles each game's rain_fc within the season, in training and pricing alike, through the prep wrapper.
- B3 shuffles each team-game's qb_form.
- B1 and C shuffle the forecast wind only for the wind-points step. That is the right placebo for an add-on.

Real gain compared with the 90th-percentile placebo gain (from placebo.pkl):

| Variant | Measure | 2015-18 | 2019-22 | 2023-25 |
|---|---|---|---|---|
| B1 | team | not scored | 0.0015 vs 0.0031 (37 of 50) | |
| B1 | total | not scored | 0.0147 vs 0.0082 | 0.0097 vs 0.0065 |
| B2 | team | 0.0008 vs 0.0010 (exactly 45 of 50, the minimum) | | |
| B2 | total | -0.0052 (the placebo median is -0.0134) | 0.060 vs 0.004 | 0.081 vs 0.006 |
| B3 | all cells | 50 of 50 everywhere | | |

**5. Snooping: fail for part B as written; pass for A, B3 and C.**
- **The bar.** The pre-registration says both gates must pass and that "anything that now fails is recommended for dropping."
- **The deviation.** B1 fails the team-points placebo and B2 fails the 2018 total miss. The report and the docs paragraph then present each as failing "one check of one gate" and leave both in. That changes the consequence after seeing the results.
- **How the placebo choice was made.** Using team-points parts 1-2 to decide which variants got a placebo was also decided after the results (the report says so).
- **Other variants.** C2 (the 8-10 band) was suggested by the known 8-10 mph bias. It failed anyway.
- **Count.** Six variants were pre-registered. None was picked on 2023-25.
- **Paperwork.** `python -m nflmodel.study_gate forecast_weather_backtest` fails: there is no decision-log row yet.

**6. Sample size: the bet-record changes are inside the noise.** Standard error at each window's bet count:

| Comparison | Records | Bets (n) | Standard error |
|---|---|---|---|
| Totals flag, recorded to A, 2023-25 | 55.1% to 58.2% | 141 | 0.042 |
| B1 totals flag, 2019-22 | 55.6% to 56.5% | 336 | 0.027 |
| B1 totals flag, 2023-25 | 57.4% to 58.2% | 141 | 0.042 |
| Spread flag, A, all windows | 69-55 / 76-48 / 37-19 | 124 / 124 / 56 | 0.045 / 0.045 / 0.067 |
| Wind under, 2015-18 | 24-20 | 44 | 0.075 |

The miss gains are small but beat the placebo where noted above.

**7. Leak test: pass.**
- I did not run `python -m nflmodel.audit` itself: it writes reports/audit.md, and its walk-forward would rewrite trees_cache.parquet.
- Instead I ran `audit.leakage_test()` with the cache save turned off. All three checks gave 0.0: ratings, future targets and the game's own score.
- My weather corruption test also gave 0 (see check 1).
- tests/test_priced_weather.py: 5 passed.
- Note: data/processed/trees_cache.parquet, pred_v3.parquet and pred_v3_dist.json were rewritten at 13:11:59 by another process working in this worktree, before my runs started. tie_check.py was also edited at 13:13:54. My runs wrote nothing to the repo.

## Should wind points or rain_fc be dropped?
- **By the pre-registration:** both fail, so both should be recommended for dropping.
- **By the round-3 rule** (team points miss): B2 passes 15 of 15, and B1 fails its 2019-22 placebo (37 of 50).
- **By total miss** (the measure both were adopted on, 1 Oct): B1 passes 15 of 15, and B2 fails on 2018 alone.
- **My judgment:** dropping rain_fc is not warranted.
  - Its only failure is 2018. In 2018 its weight is learned only from that season's earlier weeks, because no forecasts exist before 2018.
  - The 2018 loss is smaller than the typical placebo loss.
  - It beats the placebo by about 10 times on the scored windows.
- **Wind points are the real fail on the rule's own measure.** Team points miss is a diluted measure for an add-on that only moves the total. Its total-miss evidence beats the placebo on both scored windows.
- **Recommendation:** keep both and record plainly that they fail the pre-registered bar. Pre-register total miss as the measure for totals-only inputs before the next study.

## What would change the verdict
- Retractable-roof games re-priced as live would see them (roof unknown, forecast weather) and the forecast rules rescored. If the wind under, wind points or rain_fc lose their edge, A's baseline and B change.
- GitHub's rerun moving the A records noticeably once the trees are refit there.
- Matt holding to the pre-registered bar, which drops both B1 and B2.
