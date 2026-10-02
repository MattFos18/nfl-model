# Forecast weather in the backtest: results (2 Oct 2026)

Every variant is the live model refit walk-forward 2015-2025 (regular season; flags weeks 1-17 at the close).

| Variant | Window | Team miss | Total miss | Margin miss | Spread flag (4+) | Totals flag (55% under) | Wind under (10+ mph) |
|---|---|---|---|---|---|---|---|
| recorded | 2015-18 | 7.3984 | 10.7413 | 9.9510 | 69-56 | 130-117 | 24-20 |
| recorded | 2019-22 | 7.3651 | 10.5407 | 10.0184 | 79-51 | 185-149 | 143-88 |
| recorded | 2023-25 | 7.2353 | 10.1196 | 9.8969 | 37-18 | 70-57 | 77-52 |
| A | 2015-18 | 7.4046 | 10.7507 | 9.9509 | 69-55 | 132-117 | 24-20 |
| A | 2019-22 | 7.3645 | 10.5161 | 10.0111 | 76-48 | 190-146 | 143-88 |
| A | 2023-25 | 7.2343 | 10.1029 | 9.9059 | 37-19 | 82-59 | 77-52 |
| A_no_rain | 2015-18 | 7.4054 | 10.7454 | 9.9509 | 69-55 | 127-113 | 24-20 |
| A_no_rain | 2019-22 | 7.3724 | 10.5764 | 10.0111 | 76-48 | 171-139 | 143-88 |
| A_no_rain | 2023-25 | 7.2471 | 10.1840 | 9.9059 | 37-19 | 71-51 | 77-52 |
| A_no_qbform | 2015-18 | 7.4180 | 10.8278 | 9.9509 | 69-55 | 140-131 | 24-20 |
| A_no_qbform | 2019-22 | 7.3776 | 10.5608 | 10.0111 | 76-48 | 206-168 | 143-88 |
| A_no_qbform | 2023-25 | 7.2556 | 10.1705 | 9.9059 | 37-19 | 77-64 | 77-52 |
| A_no_wind_pts | 2015-18 | 7.4046 | 10.7507 | 9.9509 | 69-55 | 132-117 | 24-20 |
| A_no_wind_pts | 2019-22 | 7.3660 | 10.5308 | 10.0111 | 76-48 | 184-147 | 143-88 |
| A_no_wind_pts | 2023-25 | 7.2384 | 10.1126 | 9.9059 | 37-19 | 74-55 | 77-52 |
| A_C1 | 2015-18 | 7.4046 | 10.7507 | 9.9509 | 69-55 | 132-117 | 24-20 |
| A_C1 | 2019-22 | 7.3701 | 10.5363 | 10.0111 | 76-48 | 192-156 | 143-88 |
| A_C1 | 2023-25 | 7.2323 | 10.0971 | 9.9059 | 37-19 | 83-58 | 77-52 |
| A_C2 | 2015-18 | 7.4046 | 10.7507 | 9.9509 | 69-55 | 132-117 | 24-20 |
| A_C2 | 2019-22 | 7.3647 | 10.5159 | 10.0111 | 76-48 | 185-148 | 143-88 |
| A_C2 | 2023-25 | 7.2424 | 10.1201 | 9.9059 | 37-19 | 78-60 | 77-52 |

## B1 wind points: study_gate on team points miss

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | yes | miss 7.4046 -> 7.4046 |
| better on 2019-22 | yes | miss 7.3660 -> 7.3645 |
| better on 2023-25 | yes | miss 7.2384 -> 7.2343 |
| no bet cost: spread flag, 2015-18 | yes | 69-55 -> 69-55 |
| no bet cost: totals flag, 2015-18 | yes | 132-117 -> 132-117 |
| no bet cost: wind under, 2015-18 | yes | 24-20 -> 24-20 |
| no bet cost: spread flag, 2019-22 | yes | 76-48 -> 76-48 |
| no bet cost: totals flag, 2019-22 | yes | 184-147 -> 190-146 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 37-19 -> 37-19 |
| no bet cost: totals flag, 2023-25 | yes | 74-55 -> 82-59 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |
| beats its placebo on 2015-18 | yes | not scored: the input is zero on every game (no earlier forecasts) |
| beats its placebo on 2019-22 | NO | 37 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2023-25 | yes | 47 of 50 draws (need 45 of at least 50) |

Gate: FAIL (14 of 15); no market input and no look-ahead checked by the model-auditor agent

## B1 wind points: study_gate on total miss

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | yes | miss 10.7507 -> 10.7507 |
| better on 2019-22 | yes | miss 10.5308 -> 10.5161 |
| better on 2023-25 | yes | miss 10.1126 -> 10.1029 |
| no bet cost: spread flag, 2015-18 | yes | 69-55 -> 69-55 |
| no bet cost: totals flag, 2015-18 | yes | 132-117 -> 132-117 |
| no bet cost: wind under, 2015-18 | yes | 24-20 -> 24-20 |
| no bet cost: spread flag, 2019-22 | yes | 76-48 -> 76-48 |
| no bet cost: totals flag, 2019-22 | yes | 184-147 -> 190-146 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 37-19 -> 37-19 |
| no bet cost: totals flag, 2023-25 | yes | 74-55 -> 82-59 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |
| beats its placebo on 2015-18 | yes | not scored: the input is zero on every game (no earlier forecasts) |
| beats its placebo on 2019-22 | yes | 48 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2023-25 | yes | 48 of 50 draws (need 45 of at least 50) |

Gate: PASS (15 of 15); no market input and no look-ahead checked by the model-auditor agent

## B2 rain in the total: study_gate on team points miss

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | yes | miss 7.4054 -> 7.4046 |
| better on 2019-22 | yes | miss 7.3724 -> 7.3645 |
| better on 2023-25 | yes | miss 7.2471 -> 7.2343 |
| no bet cost: spread flag, 2015-18 | yes | 69-55 -> 69-55 |
| no bet cost: totals flag, 2015-18 | yes | 127-113 -> 132-117 |
| no bet cost: wind under, 2015-18 | yes | 24-20 -> 24-20 |
| no bet cost: spread flag, 2019-22 | yes | 76-48 -> 76-48 |
| no bet cost: totals flag, 2019-22 | yes | 171-139 -> 190-146 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 37-19 -> 37-19 |
| no bet cost: totals flag, 2023-25 | yes | 71-51 -> 82-59 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |
| beats its placebo on 2015-18 | yes | 45 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2019-22 | yes | 50 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2023-25 | yes | 50 of 50 draws (need 45 of at least 50) |

Gate: PASS (15 of 15); no market input and no look-ahead checked by the model-auditor agent

## B2 rain in the total: study_gate on total miss

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | NO | miss 10.7454 -> 10.7507 |
| better on 2019-22 | yes | miss 10.5764 -> 10.5161 |
| better on 2023-25 | yes | miss 10.1840 -> 10.1029 |
| no bet cost: spread flag, 2015-18 | yes | 69-55 -> 69-55 |
| no bet cost: totals flag, 2015-18 | yes | 127-113 -> 132-117 |
| no bet cost: wind under, 2015-18 | yes | 24-20 -> 24-20 |
| no bet cost: spread flag, 2019-22 | yes | 76-48 -> 76-48 |
| no bet cost: totals flag, 2019-22 | yes | 171-139 -> 190-146 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 37-19 -> 37-19 |
| no bet cost: totals flag, 2023-25 | yes | 71-51 -> 82-59 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |
| beats its placebo on 2015-18 | NO | 39 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2019-22 | yes | 50 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2023-25 | yes | 50 of 50 draws (need 45 of at least 50) |

Gate: FAIL (13 of 15); no market input and no look-ahead checked by the model-auditor agent

## B3 QB form in the total: study_gate on team points miss

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | yes | miss 7.4180 -> 7.4046 |
| better on 2019-22 | yes | miss 7.3776 -> 7.3645 |
| better on 2023-25 | yes | miss 7.2556 -> 7.2343 |
| no bet cost: spread flag, 2015-18 | yes | 69-55 -> 69-55 |
| no bet cost: totals flag, 2015-18 | yes | 140-131 -> 132-117 |
| no bet cost: wind under, 2015-18 | yes | 24-20 -> 24-20 |
| no bet cost: spread flag, 2019-22 | yes | 76-48 -> 76-48 |
| no bet cost: totals flag, 2019-22 | yes | 206-168 -> 190-146 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 37-19 -> 37-19 |
| no bet cost: totals flag, 2023-25 | yes | 77-64 -> 82-59 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |
| beats its placebo on 2015-18 | yes | 50 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2019-22 | yes | 50 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2023-25 | yes | 50 of 50 draws (need 45 of at least 50) |

Gate: PASS (15 of 15); no market input and no look-ahead checked by the model-auditor agent

## B3 QB form in the total: study_gate on total miss

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | yes | miss 10.8278 -> 10.7507 |
| better on 2019-22 | yes | miss 10.5608 -> 10.5161 |
| better on 2023-25 | yes | miss 10.1705 -> 10.1029 |
| no bet cost: spread flag, 2015-18 | yes | 69-55 -> 69-55 |
| no bet cost: totals flag, 2015-18 | yes | 140-131 -> 132-117 |
| no bet cost: wind under, 2015-18 | yes | 24-20 -> 24-20 |
| no bet cost: spread flag, 2019-22 | yes | 76-48 -> 76-48 |
| no bet cost: totals flag, 2019-22 | yes | 206-168 -> 190-146 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 37-19 -> 37-19 |
| no bet cost: totals flag, 2023-25 | yes | 77-64 -> 82-59 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |
| beats its placebo on 2015-18 | yes | 50 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2019-22 | yes | 50 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2023-25 | yes | 50 of 50 draws (need 45 of at least 50) |

Gate: PASS (15 of 15); no market input and no look-ahead checked by the model-auditor agent

## C1 isotonic curve vs bands: study_gate on team points miss

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | yes | miss 7.4046 -> 7.4046 |
| better on 2019-22 | NO | miss 7.3645 -> 7.3701 |
| better on 2023-25 | yes | miss 7.2343 -> 7.2323 |
| no bet cost: spread flag, 2015-18 | yes | 69-55 -> 69-55 |
| no bet cost: totals flag, 2015-18 | yes | 132-117 -> 132-117 |
| no bet cost: wind under, 2015-18 | yes | 24-20 -> 24-20 |
| no bet cost: spread flag, 2019-22 | yes | 76-48 -> 76-48 |
| no bet cost: totals flag, 2019-22 | NO | 190-146 -> 192-156 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 37-19 -> 37-19 |
| no bet cost: totals flag, 2023-25 | yes | 82-59 -> 83-58 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |

Gate: FAIL (10 of 12); no market input and no look-ahead checked by the model-auditor agent

## C1 isotonic curve vs bands: study_gate on total miss

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | yes | miss 10.7507 -> 10.7507 |
| better on 2019-22 | NO | miss 10.5161 -> 10.5363 |
| better on 2023-25 | yes | miss 10.1029 -> 10.0971 |
| no bet cost: spread flag, 2015-18 | yes | 69-55 -> 69-55 |
| no bet cost: totals flag, 2015-18 | yes | 132-117 -> 132-117 |
| no bet cost: wind under, 2015-18 | yes | 24-20 -> 24-20 |
| no bet cost: spread flag, 2019-22 | yes | 76-48 -> 76-48 |
| no bet cost: totals flag, 2019-22 | NO | 190-146 -> 192-156 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 37-19 -> 37-19 |
| no bet cost: totals flag, 2023-25 | yes | 82-59 -> 83-58 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |

Gate: FAIL (10 of 12); no market input and no look-ahead checked by the model-auditor agent

## C2 bands 0/8/10/15 vs bands: study_gate on team points miss

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | yes | miss 7.4046 -> 7.4046 |
| better on 2019-22 | NO | miss 7.3645 -> 7.3647 |
| better on 2023-25 | NO | miss 7.2343 -> 7.2424 |
| no bet cost: spread flag, 2015-18 | yes | 69-55 -> 69-55 |
| no bet cost: totals flag, 2015-18 | yes | 132-117 -> 132-117 |
| no bet cost: wind under, 2015-18 | yes | 24-20 -> 24-20 |
| no bet cost: spread flag, 2019-22 | yes | 76-48 -> 76-48 |
| no bet cost: totals flag, 2019-22 | NO | 190-146 -> 185-148 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 37-19 -> 37-19 |
| no bet cost: totals flag, 2023-25 | NO | 82-59 -> 78-60 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |

Gate: FAIL (8 of 12); no market input and no look-ahead checked by the model-auditor agent

## C2 bands 0/8/10/15 vs bands: study_gate on total miss

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | yes | miss 10.7507 -> 10.7507 |
| better on 2019-22 | yes | miss 10.5161 -> 10.5159 |
| better on 2023-25 | NO | miss 10.1029 -> 10.1201 |
| no bet cost: spread flag, 2015-18 | yes | 69-55 -> 69-55 |
| no bet cost: totals flag, 2015-18 | yes | 132-117 -> 132-117 |
| no bet cost: wind under, 2015-18 | yes | 24-20 -> 24-20 |
| no bet cost: spread flag, 2019-22 | yes | 76-48 -> 76-48 |
| no bet cost: totals flag, 2019-22 | NO | 190-146 -> 185-148 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 37-19 -> 37-19 |
| no bet cost: totals flag, 2023-25 | NO | 82-59 -> 78-60 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |

Gate: FAIL (9 of 12); no market input and no look-ahead checked by the model-auditor agent

## Total-points effect by forecast wind (latest fit: totals equation -0.340 per mph; wind points from the 2018-2025 pool)

| Forecast wind (mph) | bands: equation + wind points = total | C1: equation + wind points = total | C2: equation + wind points = total |
|---|---|---|---|
| 0 | -0.00 +0.33 = +0.33 | -0.00 +1.13 = +1.13 | -0.00 +0.14 = +0.14 |
| 5 | -1.70 +0.33 = -1.37 | -1.70 +0.43 = -1.27 | -1.70 +0.14 = -1.56 |
| 9 | -3.06 +0.33 = -2.73 | -3.06 +0.43 = -2.63 | -3.06 +0.82 = -2.25 |
| 10 | -3.40 -1.17 = -4.58 | -3.40 -0.89 = -4.29 | -3.40 -1.17 = -4.58 |
| 14 | -4.76 -1.17 = -5.94 | -4.76 -0.89 = -5.66 | -4.76 -1.17 = -5.94 |
| 15 | -5.10 +0.40 = -4.70 | -5.10 -0.89 = -6.00 | -5.10 +0.40 = -4.70 |
| 20 | -6.80 +0.40 = -6.40 | -6.80 -0.89 = -7.70 | -6.80 +0.40 = -6.40 |

## Mean miss (actual total minus the model's total) by forecast-wind band, 2019-2025 regular season

| Band | Games | Before wind points | Bands (A) | C1 | C2 |
|---|---|---|---|---|---|
| [0,8) | 672 | +0.32 | +0.13 | +0.19 | +0.44 |
| [8,10) | 208 | +1.20 | +1.00 | +1.15 | +0.18 |
| [10,15) | 273 | -1.13 | -0.08 | -0.85 | -0.08 |
| [15,99) | 111 | +0.59 | -0.43 | +0.92 | -0.43 |
