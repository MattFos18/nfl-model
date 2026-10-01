# Wind and cold trained on forecasts (1 Oct 2026)

Each variant refit walk-forward 2015-2025. Team points miss is the yardstick; flags at the live rules (weeks 1-17).

| Variant | Window | Team miss | Total miss | Margin miss | Spread flag | Totals flag |
|---|---|---|---|---|---|---|
| base | 2015-18 | 7.4082 | 10.7382 | 9.9491 | 68-55 | 137-127 |
| base | 2019-22 | 7.3426 | 10.4934 | 10.0204 | 80-51 | 202-146 |
| base | 2023-25 | 7.2439 | 10.1081 | 9.9041 | 40-21 | 98-73 |
| W | 2015-18 | 7.4125 | 10.7464 | 9.9521 | 68-57 | 133-128 |
| W | 2019-22 | 7.3367 | 10.4764 | 10.0185 | 77-45 | 203-142 |
| W | 2023-25 | 7.2471 | 10.1041 | 9.9064 | 39-19 | 105-70 |
| C | 2015-18 | 7.4083 | 10.7381 | 9.9490 | 68-55 | 137-127 |
| C | 2019-22 | 7.3427 | 10.4936 | 10.0113 | 78-50 | 202-145 |
| C | 2023-25 | 7.2466 | 10.1057 | 9.9122 | 40-21 | 97-72 |
| WC | 2015-18 | 7.4125 | 10.7463 | 9.9520 | 68-57 | 133-128 |
| WC | 2019-22 | 7.3372 | 10.4764 | 10.0108 | 77-47 | 203-141 |
| WC | 2023-25 | 7.2505 | 10.1018 | 9.9145 | 39-19 | 105-71 |

## Gate, variant W (parts 1 and 2; the placebo runs separately)

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | NO | miss 7.4082 -> 7.4125 |
| better on 2019-22 | yes | miss 7.3426 -> 7.3367 |
| better on 2023-25 | NO | miss 7.2439 -> 7.2471 |
| no bet cost: spread flag, 2015-18 | NO | 68-55 -> 68-57 |
| no bet cost: totals flag, 2015-18 | NO | 137-127 -> 133-128 |
| no bet cost: spread flag, 2019-22 | yes | 80-51 -> 77-45 |
| no bet cost: totals flag, 2019-22 | yes | 202-146 -> 203-142 |
| no bet cost: spread flag, 2023-25 | yes | 40-21 -> 39-19 |
| no bet cost: totals flag, 2023-25 | yes | 98-73 -> 105-70 |

Gate: FAIL (5 of 9); no market input and no look-ahead checked by the model-auditor agent

## Gate, variant C (parts 1 and 2; the placebo runs separately)

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | NO | miss 7.4082 -> 7.4083 |
| better on 2019-22 | NO | miss 7.3426 -> 7.3427 |
| better on 2023-25 | NO | miss 7.2439 -> 7.2466 |
| no bet cost: spread flag, 2015-18 | yes | 68-55 -> 68-55 |
| no bet cost: totals flag, 2015-18 | yes | 137-127 -> 137-127 |
| no bet cost: spread flag, 2019-22 | NO | 80-51 -> 78-50 |
| no bet cost: totals flag, 2019-22 | yes | 202-146 -> 202-145 |
| no bet cost: spread flag, 2023-25 | yes | 40-21 -> 40-21 |
| no bet cost: totals flag, 2023-25 | yes | 98-73 -> 97-72 |

Gate: FAIL (5 of 9); no market input and no look-ahead checked by the model-auditor agent

## Gate, variant WC (parts 1 and 2; the placebo runs separately)

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | NO | miss 7.4082 -> 7.4125 |
| better on 2019-22 | yes | miss 7.3426 -> 7.3372 |
| better on 2023-25 | NO | miss 7.2439 -> 7.2505 |
| no bet cost: spread flag, 2015-18 | NO | 68-55 -> 68-57 |
| no bet cost: totals flag, 2015-18 | NO | 137-127 -> 133-128 |
| no bet cost: spread flag, 2019-22 | yes | 80-51 -> 77-47 |
| no bet cost: totals flag, 2019-22 | yes | 202-146 -> 203-141 |
| no bet cost: spread flag, 2023-25 | yes | 40-21 -> 39-19 |
| no bet cost: totals flag, 2023-25 | yes | 98-73 -> 105-71 |

Gate: FAIL (5 of 9); no market input and no look-ahead checked by the model-auditor agent
