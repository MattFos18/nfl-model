# Drop the seven inputs: results (written by experiments/drop_seven_inputs.py)

| Window | Margin miss | Team points miss | Total miss | Brier raw win | Brier calibrated win | Calibration error | Spread flag | Totals flag | Wind under |
|---|---|---|---|---|---|---|---|---|---|
| 2015-18 | 9.9471 -> 9.9429 | 7.3993 -> 7.3889 | 10.7484 -> 10.7238 | 0.2158 -> 0.2155 | 0.2153 -> 0.2150 | 0.0350 -> 0.0364 | 68-58 -> 66-53 | 132-111 -> 142-117 | 119-97 -> 119-97 |
| 2019-22 | 10.0116 -> 10.0040 | 7.3740 -> 7.3681 | 10.5340 -> 10.5343 | 0.2184 -> 0.2185 | 0.2173 -> 0.2174 | 0.0267 -> 0.0310 | 78-49 -> 81-53 | 175-140 -> 183-134 | 143-88 -> 143-88 |
| 2023-25 | 9.9069 -> 9.8997 | 7.2357 -> 7.2285 | 10.1040 -> 10.1037 | 0.2163 -> 0.2161 | 0.2155 -> 0.2152 | 0.0610 -> 0.0488 | 37-19 -> 38-17 | 76-55 -> 86-61 | 77-52 -> 77-52 |

Calibrated win chance scored on 1020, 1050, 815 games (seasons with a home calibration in force).

Margin rule (not worse on any window, ties within 0.0005): 2015-18 ok, 2019-22 ok, 2023-25 ok -> implement

## margin miss (base = live, new = without the seven)

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | yes | miss 9.9471 -> 9.9429 |
| better on 2019-22 | yes | miss 10.0116 -> 10.0040 |
| better on 2023-25 | yes | miss 9.9069 -> 9.8997 |
| no bet cost: spread flag, 2015-18 | yes | 68-58 -> 66-53 |
| no bet cost: totals flag, 2015-18 | yes | 132-111 -> 142-117 |
| no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| no bet cost: spread flag, 2019-22 | NO | 78-49 -> 81-53 |
| no bet cost: totals flag, 2019-22 | yes | 175-140 -> 183-134 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 37-19 -> 38-17 |
| no bet cost: totals flag, 2023-25 | yes | 76-55 -> 86-61 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |

Gate: FAIL (11 of 12); no market input and no look-ahead checked by the model-auditor agent

## team miss (base = live, new = without the seven)

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | yes | miss 7.3993 -> 7.3889 |
| better on 2019-22 | yes | miss 7.3740 -> 7.3681 |
| better on 2023-25 | yes | miss 7.2357 -> 7.2285 |
| no bet cost: spread flag, 2015-18 | yes | 68-58 -> 66-53 |
| no bet cost: totals flag, 2015-18 | yes | 132-111 -> 142-117 |
| no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| no bet cost: spread flag, 2019-22 | NO | 78-49 -> 81-53 |
| no bet cost: totals flag, 2019-22 | yes | 175-140 -> 183-134 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 37-19 -> 38-17 |
| no bet cost: totals flag, 2023-25 | yes | 76-55 -> 86-61 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |

Gate: FAIL (11 of 12); no market input and no look-ahead checked by the model-auditor agent

## total miss (base = live, new = without the seven)

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | yes | miss 10.7484 -> 10.7238 |
| better on 2019-22 | NO | miss 10.5340 -> 10.5343 |
| better on 2023-25 | yes | miss 10.1040 -> 10.1037 |
| no bet cost: spread flag, 2015-18 | yes | 68-58 -> 66-53 |
| no bet cost: totals flag, 2015-18 | yes | 132-111 -> 142-117 |
| no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| no bet cost: spread flag, 2019-22 | NO | 78-49 -> 81-53 |
| no bet cost: totals flag, 2019-22 | yes | 175-140 -> 183-134 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 37-19 -> 38-17 |
| no bet cost: totals flag, 2023-25 | yes | 76-55 -> 86-61 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |

Gate: FAIL (10 of 12); no market input and no look-ahead checked by the model-auditor agent

