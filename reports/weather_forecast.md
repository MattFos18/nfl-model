# Forecast weather vs actual weather in the game model

30 Sep 2026. `experiments/weather_forecast.py`; rows in `reports/weather_forecast.csv`. Forecasts from
`data/weather/forecast_archive.csv` (Open-Meteo previous runs: d1 = the forecast one day before the kickoff hour),
355 regular-season outdoor games whose inputs change. Actuals are the model's own: the schedule's temperature and wind, rain from the
play-by-play weather text. The archive has no precipitation chance, so its rain call is the 1 mm half of the live rule
(the live rule also calls rain at a 50%+ chance). Temperature forecasts cover 2022-25; wind and rain 2024-25.

## 1. How far off is the forecast (d1, all seasons)

| input | against | games | bias (fc - actual) | mean abs error | rmse | corr |
|---|---|---|---|---|---|---|
| temp (F) | schedule | 606 | -0.52 | 2.78 | 4.37 | 0.971 |
| wind (mph) | schedule | 371 | +0.23 | 2.28 | 3.04 | 0.749 |
| temp (F) | reanalysis | 746 | +0.46 | 2.51 | 3.34 | 0.983 |
| wind (mph) | reanalysis | 380 | +0.87 | 2.34 | 3.10 | 0.755 |

By season (d1 against the schedule): 2022 temp bias +0.15, MAE 3.02 (n 106); 2023 temp bias -0.14, MAE 2.76 (n 133); 2023 wind bias -0.48, MAE 2.12 (n 4); 2024 temp bias -0.69, MAE 2.72 (n 180); 2024 wind bias +0.13, MAE 2.16 (n 180); 2025 temp bias -1.00, MAE 2.72 (n 187); 2025 wind bias +0.35, MAE 2.39 (n 187)

Two days out (d2, against the schedule): temp bias +0.07, MAE 2.91; wind bias +0.34, MAE 2.45

| flag (d1) | against | games | forecast rate | actual rate | flips | flip % | fc yes, actual no | fc no, actual yes |
|---|---|---|---|---|---|---|---|---|
| cold (<35F) | schedule | 606 | 14.0% | 12.0% | 20 | 3.3% | 16 | 4 |
| cold (<35F) | reanalysis | 746 | 11.7% | 11.4% | 18 | 2.4% | 10 | 8 |
| rain (1 mm+ fc vs pbp text) | pbp text | 380 | 1.8% | 4.7% | 19 | 5.0% | 4 | 15 |
| rain (1 mm+ fc vs 1 mm+ reanalysis) | reanalysis | 380 | 1.8% | 1.8% | 8 | 2.1% | 4 | 4 |
| rain (0.25 mm+ fc vs pbp text) | pbp text | 380 | 5.8% | 4.7% | 28 | 7.4% | 16 | 12 |
| wind level (<10 / 10-15 / 15+ mph) | schedule | 371 | 32.1% | 30.5% | 94 | 25.3% | 45 | 49 |
| wind level (<10 / 10-15 / 15+ mph) | reanalysis | 380 | 31.6% | 23.9% | 76 | 20.0% | 53 | 23 |

What an input is worth (points per team per unit in the 2023-25 live fits; game total per unit, total equation fit 2013-24): wind_out -0.129 / -0.260; cold +0.502 / -0.056; rain -1.760 / -3.908; warm_in_cold -1.755 / not in the total

## 2. What the forecast costs the model

The live walk-forward refit before every week (fresh trees), the priced week's weather inputs from the d1 forecast; the fits
are unchanged. `fc_live`: the forecast wherever it exists (the live path). `fc_swap`: only where the actual reading exists too.
Team points miss / total miss over every regular-season game of the season; spread flag and totals flag W-L on the live rules.

| variant | season | team miss | total miss | spread flag | totals flag | cal. log loss | forecast games: team miss | total miss |
|---|---|---|---|---|---|---|---|---|
| actual | 2022 | 7.1098 | 10.5099 | 14-20 | 23-11 | 0.6455 | 7.091 (185 g) | 10.351 |
| actual | 2023 | 7.3797 | 10.4326 | 6-3 | 22-13 | 0.6339 | 7.505 (190 g) | 10.157 |
| actual | 2024 | 7.0872 | 9.6851 | 21-9 | 23-26 | 0.5985 | 6.800 (177 g) | 9.219 |
| actual | 2025 | 7.3205 | 10.4124 | 13-9 | 26-20 | 0.6282 | 7.491 (178 g) | 11.120 |
| fc_swap | 2022 | 7.1118 | 10.5145 | 14-20 | 23-12 | 0.6462 | 7.094 (185 g) | 10.358 |
| fc_swap | 2023 | 7.3774 | 10.4324 | 6-3 | 22-13 | 0.6335 | 7.502 (190 g) | 10.157 |
| fc_swap | 2024 | 7.1030 | 9.7473 | 22-10 | 24-27 | 0.5993 | 6.824 (177 g) | 9.315 |
| fc_swap | 2025 | 7.2748 | 10.3155 | 13-9 | 25-19 | 0.6284 | 7.421 (178 g) | 10.972 |
| fc_live | 2022 | 7.1118 | 10.5145 | 14-20 | 23-12 | 0.6462 | 7.094 (185 g) | 10.358 |
| fc_live | 2023 | 7.3777 | 10.4331 | 6-3 | 22-13 | 0.6338 | 7.502 (190 g) | 10.158 |
| fc_live | 2024 | 7.1062 | 9.7537 | 22-10 | 24-27 | 0.5994 | 6.829 (177 g) | 9.324 |
| fc_live | 2025 | 7.2821 | 10.3300 | 13-9 | 25-19 | 0.6288 | 7.432 (178 g) | 10.994 |
| fc_temp_only | 2022 | 7.1118 | 10.5145 | 14-20 | 23-12 | 0.6462 | 7.094 (185 g) | 10.358 |
| fc_temp_only | 2023 | 7.3777 | 10.4331 | 6-3 | 22-13 | 0.6338 | 7.502 (190 g) | 10.158 |
| fc_temp_only | 2024 | 7.0872 | 9.6842 | 22-9 | 23-26 | 0.5989 | 6.800 (177 g) | 9.218 |
| fc_temp_only | 2025 | 7.3197 | 10.4106 | 13-9 | 26-20 | 0.6288 | 7.490 (178 g) | 11.117 |
| fc_wind_only | 2022 | 7.1098 | 10.5099 | 14-20 | 23-11 | 0.6455 | 7.091 (185 g) | 10.351 |
| fc_wind_only | 2023 | 7.3797 | 10.4326 | 6-3 | 22-13 | 0.6339 | 7.505 (190 g) | 10.157 |
| fc_wind_only | 2024 | 7.0913 | 9.6823 | 21-10 | 26-27 | 0.5988 | 6.806 (177 g) | 9.215 |
| fc_wind_only | 2025 | 7.2982 | 10.3552 | 13-9 | 25-21 | 0.6282 | 7.457 (178 g) | 11.032 |
| fc_rain_only | 2022 | 7.1098 | 10.5099 | 14-20 | 23-11 | 0.6455 | 7.091 (185 g) | 10.351 |
| fc_rain_only | 2023 | 7.3797 | 10.4326 | 6-3 | 22-13 | 0.6339 | 7.505 (190 g) | 10.157 |
| fc_rain_only | 2024 | 7.1007 | 9.7563 | 21-9 | 22-26 | 0.5986 | 6.820 (177 g) | 9.328 |
| fc_rain_only | 2025 | 7.3052 | 10.3904 | 13-9 | 25-19 | 0.6283 | 7.468 (178 g) | 11.086 |

## 3. Candidates (each against `fc_live`, scored with forecast inputs)

Change in team points miss / total miss (negative = better), spread and totals flag W-L change, calibrated log loss change.

| candidate | season | d team miss | d total miss | d spread W-L | d totals W-L | d log loss |
|---|---|---|---|---|---|---|
| a_shrink | 2022 | -0.0049 | -0.0073 | +0 | +0 | +0.00007 |
| a_shrink | 2023 | +0.0006 | +0.0002 | +0 | +0 | +0.00001 |
| a_shrink | 2024 | +0.0042 | -0.0027 | -1 | -1 | +0.00002 |
| a_shrink | 2025 | +0.0183 | +0.0454 | +0 | +0 | -0.00017 |
| b_train_fc | 2022 | -0.0026 | -0.0080 | +0 | +0 | +0.00003 |
| b_train_fc | 2023 | -0.0015 | +0.0028 | +0 | +0 | -0.00027 |
| b_train_fc | 2024 | -0.0007 | -0.0013 | +0 | +0 | +0.00012 |
| b_train_fc | 2025 | -0.0003 | -0.0010 | +0 | -1 | +0.00062 |
| c1_calib | 2022 | -0.0048 | -0.0072 | +0 | +0 | +0.00006 |
| c1_calib | 2023 | +0.0009 | +0.0003 | +0 | +0 | +0.00002 |
| c1_calib | 2024 | +0.0051 | -0.0018 | -1 | -1 | +0.00005 |
| c1_calib | 2025 | +0.0186 | +0.0460 | +0 | -1 | -0.00045 |
| c2_prob | 2022 | -0.0030 | -0.0005 | +0 | +1 | -0.00027 |
| c2_prob | 2023 | +0.0018 | +0.0001 | +0 | +0 | +0.00021 |
| c2_prob | 2024 | +0.0058 | -0.0018 | -1 | -1 | +0.00001 |
| c2_prob | 2025 | +0.0225 | +0.0490 | +0 | +0 | -0.00029 |
| c3_bias | 2022 | +0.0000 | +0.0000 | +0 | +0 | +0.00000 |
| c3_bias | 2023 | +0.0000 | +0.0000 | +0 | +0 | +0.00000 |
| c3_bias | 2024 | -0.0017 | -0.0042 | +0 | +0 | -0.00004 |
| c3_bias | 2025 | -0.0008 | +0.0005 | +0 | -2 | -0.00002 |
| c4_rain_any | 2022 | +0.0000 | +0.0000 | +0 | +0 | +0.00000 |
| c4_rain_any | 2023 | +0.0000 | +0.0000 | +0 | +0 | +0.00000 |
| c4_rain_any | 2024 | +0.0006 | -0.0124 | +0 | +0 | +0.00003 |
| c4_rain_any | 2025 | +0.0271 | +0.0404 | +0 | -2 | +0.00006 |

| candidate | seasons it changes | rule 1 (miss) | rule 2 (flags) | placebo beaten / draws | verdict | why |
|---|---|---|---|---|---|---|
| a_shrink | 2022 2023 2024 2025 | False | False | 50 / 50 | not adopted | miss not lower on every season it changes; costs flags or calibration; placebo beat or matched it in 50 of 50 draws |
| b_train_fc | 2022-25 (fits) | False | False |  / 0 | not adopted | miss not lower on every season it changes; costs flags or calibration |
| c1_calib | 2022 2023 2024 2025 | False | False | 50 / 50 | not adopted | miss not lower on every season it changes; costs flags or calibration; placebo beat or matched it in 50 of 50 draws |
| c2_prob | 2022 2023 2024 2025 | False | False | 50 / 50 | not adopted | miss not lower on every season it changes; costs flags or calibration; placebo beat or matched it in 50 of 50 draws |
| c3_bias | 2024 2025 | False | False | 48 / 50 | not adopted | miss not lower on every season it changes; costs flags or calibration; placebo beat or matched it in 48 of 50 draws |
| c4_rain_any | 2024 2025 | False | False | 50 / 50 | not adopted | miss not lower on every season it changes; costs flags or calibration; placebo beat or matched it in 50 of 50 draws |

Engine check: the `actual` variant against situational_game.lean_walk_forward on 2023: max differences {"model_spread": 0.0, "model_total": 0.0, "p_home": 0.0, "p_over_emp": 0.0}; against pred_v3 (cached trees) mean |spread| difference 0.005.

## Verdict

Cost of the forecast (fc_live minus actual), team points miss +0.0020 / -0.0020 / +0.0190 / -0.0384, total miss +0.0046 / +0.0005 / +0.0686 / -0.0824 (2022 / 2023 / 2024 / 2025); spread-flag net W-L change +0 / +0 / +0 / +0, totals-flag net change -1 / +0 / +0 / +0.
The cost is small and not one-signed: the forecast priced 2025 better than the actuals did, which says the difference is
within the noise of ~180 forecast games a season. Rain drives the 2024 cost (the 1 mm forecast calls rain in a third as
many games as the play-by-play text records, so most rain games are priced dry); rain and wind both drive the 2025 gain;
temperature moves almost nothing (the cold flag flips in 3% of games).

No candidate passes the rule. With two to four scoreable seasons of 177-190 outdoor games, and gains of at most a few
thousandths of a point, none of these results would be strong enough to adopt even if one had passed every season;
the live weather treatment stays as it is. Rules 1 and 2 are checked on 2022-25 only (the round-3 windows 2015-18 and
2019-22 have no archived forecast), and the placebo is run for the test-side candidates (train_fc's refit placebo
runs only past the rule's gate, which it does not reach).

