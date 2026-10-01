# Rain, cold and gusts re-tested on forecasts

1 Oct 2026. `experiments/weather_forecast_retest.py`, data `data/weather/forecast_history.csv` (GFS MOS temperature and
rain chance added by `nflmodel/forecast_history.py --extend`; 1,526 outdoor or open-roof games 2018-2025). Band points on
top of the model's total (wind points already in), walk-forward like `model.wind_points` (K = 50); 2018 has no earlier
forecasts, so it and 2015-17 are unchanged by construction. Totals flag: under at 1 - p_over_emp >= 0.55, weeks 1-17,
re-priced at the adjusted total with each fit's own training misses. Placebo: the reading shuffled within season (50
draws), counted when the real gain beats the shuffle on both 2019-22 and 2023-25 (45 of 50 needed).

## Band points

| Idea | 2019-22 total miss | 2023-25 total miss | 2019-22 team pts | 2023-25 team pts | 2019-22 flag | 2023-25 flag | Shuffles beaten | 2025 amounts |
|---|---|---|---|---|---|---|---|---|
| rain chance bands [0,20) [20,50) 50+ (last run) | 10.341 -> 10.355 | 10.087 -> 10.052 | 7.3349 -> 7.3481 | 7.2448 -> 7.2335 | 182-130 -> 167-113 | 81-62 -> 86-51 | 12 of 50 | [0.0, 20.0): +0.67; [20.0, 50.0): -0.98; [50.0, 101.0): -2.29 |
| rain chance bands, day-before run | 10.341 -> 10.363 | 10.087 -> 10.098 | 7.3349 -> 7.3430 | 7.2448 -> 7.2521 | 182-130 -> 169-115 | 81-62 -> 84-58 | 3 of 50 | [0.0, 20.0): +0.60; [20.0, 50.0): -1.42; [50.0, 101.0): -1.36 |
| temperature bands <32, 32-45, 45+ F (last run) | 10.341 -> 10.319 | 10.087 -> 10.090 | 7.3349 -> 7.3294 | 7.2448 -> 7.2454 | 182-130 -> 171-119 | 81-62 -> 81-57 | 28 of 50 | [-99.0, 32.0): -0.72; [32.0, 45.0): -0.70; [45.0, 999.0): +0.25 |
| temperature bands, day-before run | 10.341 -> 10.314 | 10.087 -> 10.078 | 7.3349 -> 7.3280 | 7.2448 -> 7.2410 | 182-130 -> 171-119 | 81-62 -> 81-59 | 44 of 50 | [-99.0, 32.0): -0.54; [32.0, 45.0): -1.15; [45.0, 999.0): +0.34 |
| Blend gust bands [0,20) [20,30) 30+ mph (Nov 2018-2019 only) | 10.614 -> 10.603 | no games | 7.3349 -> 7.3351 | 7.2448 -> 7.2448 | 182-130 -> 180-127 | 81-62 -> 81-62 | 0 of 50 |  |
| rain 50+ x wind 10+ (four cells) | 10.341 -> 10.343 | 10.087 -> 10.039 | 7.3349 -> 7.3414 | 7.2448 -> 7.2343 | 182-130 -> 178-120 | 81-62 -> 87-58 | 40 of 50 | False & False: +0.64; False & True: -0.15; True & False: -1.50; True & True: -2.37 |
| below 32 F x wind 10+ (four cells) | 10.341 -> 10.364 | 10.087 -> 10.057 | 7.3349 -> 7.3392 | 7.2448 -> 7.2389 | 182-130 -> 182-128 | 81-62 -> 89-59 | 0 of 50 | False & False: +0.38; False & True: -0.63; True & False: -0.41; True & True: -0.61 |
| rain 50+ or below 32 F (two cells) | 10.341 -> 10.299 | 10.087 -> 10.033 | 7.3349 -> 7.3349 | 7.2448 -> 7.2304 | 182-130 -> 170-119 | 81-62 -> 85-54 | 50 of 50 | False: +0.50; True: -2.11 |

Forecast games scored: rain 723 / 536, rain_d1 723 / 536, cold 723 / 536, cold_d1 723 / 536, gust 178 / 0, rain_x_wind 723 / 536, cold_x_wind 723 / 536, wet_or_cold 723 / 536 (2019-22 / 2023-25).

## Blind unders at forecast cuts (weeks 1-17, closing total, -110)

| Cut | 2018 | 2019-22 | 2023-25 | All | Win % | Units | Shuffles as good |
|---|---|---|---|---|---|---|---|
| rain chance 50+ | 11-9 | 55-30 | 36-21 | 102-60 | 63.0 | 36.0 | 0.005 |
| rain chance 70+ | 6-6 | 34-22 | 14-11 | 54-39 | 58.1 | 11.1 | 0.125 |
| rain 50+, wind under 10 | 8-7 | 34-19 | 22-15 | 64-41 | 61.0 | 18.9 | 0.0 |
| rain 50+, wind 10+ | 3-2 | 21-11 | 14-6 | 38-19 | 66.7 | 17.1 | 0.105 |
| below 32 F | 4-2 | 21-15 | 11-10 | 36-27 | 57.1 | 6.3 | 0.275 |
| below 40 F | 11-11 | 53-43 | 29-30 | 93-84 | 52.5 | 0.6 | 0.525 |
| below 32 F, wind under 10 | 3-2 | 12-9 | 7-8 | 22-19 | 53.7 | 1.1 | 0.275 |
| below 32 F, wind 10+ | 1-0 | 9-6 | 4-2 | 14-8 | 63.6 | 5.2 | 0.345 |
| Blend gust 25+ mph | 6-3 | 10-9 | 0-0 | 16-12 | 57.1 | 2.8 | 0.305 |
| Blend gust 30+ mph | 3-0 | 5-4 | 0-0 | 8-4 | 66.7 | 3.6 | 0.19 |
| wind 10+ (the live wind under, for reference) | 24-19 | 143-89 | 83-52 | 250-160 | 61.0 | 74.0 | 0.0 |

## Verdict (round-3 rule)

| Idea | Verdict | Why |
|---|---|---|
| Rain points (chance bands) | Reject | Total miss worse on 2019-22 (10.341 -> 10.355), better on 2023-25; 12 of 50 shuffles beaten (45 needed). The day-before run is worse on both windows. |
| Cold points (temperature bands) | Reject | Better on 2019-22, worse on 2023-25 (10.087 -> 10.090); 28 of 50 shuffles beaten. The day-before run is the other near miss: better on both windows (10.341 -> 10.314, 10.087 -> 10.078), team points better on both, flag not worse (net 52 -> 52, 19 -> 22), but it beats 44 of 50 shuffles, one short of 45. |
| Gust points (Blend) | Reject (cannot be tested) | The Blend's gust exists for 223 last-run games, Nov 2018 to 2019 only; band points can be scored on 2019 alone (178 games) and on no game after it (so 0 of 50 shuffles can be beaten on both windows); 2019 alone 10.614 -> 10.603. Blind unders at 25+ mph 16-12. |
| Rain x wind points | Reject | Total miss worse on 2019-22 (10.341 -> 10.343); 40 of 50. |
| Cold x wind points | Reject | Total miss worse on 2019-22 (10.341 -> 10.364); 0 of 50. |
| Wet or cold points (rain 50+ or below 32 F, one band) | Reject, the near miss | Total miss better on both windows (10.341 -> 10.299, 10.087 -> 10.033), team points better on both, 50 of 50 shuffles beaten, about -2.1 points in those games; but the totals flag on 2019-22 goes 182-130 -> 170-119 (net 52 -> 51), one win short of the no-bet-cost test (2023-25: 81-62 -> 85-54). |
| Blind under, rain chance 50+ | Track as a hidden shadow | 11-9 / 55-30 / 36-21, 102-60 (63.0%), +36.0 units, 0.5% of 200 shuffles as good. With wind under 10 (games the wind under does not already bet) 64-41, 0 of 200. Found on the backtest, so graded live, not bet; 2025 went 7-8 and 70+ is weaker (54-39), so it must prove itself live. Its live reading is the GFS MOS response the wind under already pulls (no new source). |
| Blind under, below 32 F | Reject | 36-27, 27.5% of shuffles as good; below 40 F 93-84. |

The backtest's total already carries the model's own rain, cold and wind terms, which in past seasons read the weather
that happened (live they read the forecast), so this measures what the forecast adds beyond them. Two data notes: the
GFS MOS writes 999 / 99 for a missing hour; one game (2018_16_BAL_LAC at KTOA) has its stored GFS wind built from those
(18.6 mph against the Japan model's 3.9), which puts it in the wind under and the 10-15 band. The temperature and rain
columns read them as missing; the stored wind is left as is (a live input). And the stored pred_v3.parquet in this
checkout has no wind points (no model_total_raw column: the weekly run that wrote it predates #363), so this study reruns
the model itself first.
