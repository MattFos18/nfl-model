# NFL Model 3.0 backtest

Walk-forward: every week is priced with only games played before it; the points regression is refit before every week on every played game since 2013. Rating parameters, ridge strength and bet thresholds were chosen on 2019 to 2022 only. 2023 to 2025 is the held-out test the tuning never saw.

## 1. Points miss (mean absolute error) against Vegas

Tuning window 2019 to 2022:

| target      |   3.0 |   Vegas close |   games |
|:------------|------:|--------------:|--------:|
| team points |  7.45 |          7.29 |    1055 |
| margin      | 10.16 |          9.89 |    1055 |
| total       | 10.71 |         10.54 |    1055 |

Held-out 2023 to 2025:

| target      |   3.0 |   Vegas close |   games |
|:------------|------:|--------------:|--------:|
| team points |  7.35 |          7.21 |     816 |
| margin      | 10.15 |          9.74 |     816 |
| total       | 10.33 |         10.12 |     816 |

Held-out, Week 5 on:

| target      |   3.0 |   Vegas close |   games |
|:------------|------:|--------------:|--------:|
| team points |  7.35 |          7.19 |     624 |
| margin      | 10.06 |          9.59 |     624 |
| total       | 10.3  |         10.09 |     624 |

## 2. Win probability, 2019 to 2022 (tuning)

Brier score (lower is better): 3.0 0.2218, market moneyline 0.2111.

3.0 calibration:

| bin         |   n |   predicted |   actual |
|:------------|----:|------------:|---------:|
| [0.0, 0.3)  |  69 |       0.235 |    0.261 |
| [0.3, 0.4)  | 108 |       0.353 |    0.287 |
| [0.4, 0.5)  | 179 |       0.454 |    0.408 |
| [0.5, 0.6)  | 262 |       0.551 |    0.462 |
| [0.6, 0.7)  | 215 |       0.647 |    0.614 |
| [0.7, 1.01) | 222 |       0.775 |    0.788 |

## 2. Win probability, 2023 to 2025 (held out)

Brier score (lower is better): 3.0 0.2201, market moneyline 0.2102.

3.0 calibration:

| bin         |   n |   predicted |   actual |
|:------------|----:|------------:|---------:|
| [0.0, 0.3)  |  60 |       0.243 |    0.333 |
| [0.3, 0.4)  |  77 |       0.36  |    0.364 |
| [0.4, 0.5)  | 172 |       0.454 |    0.36  |
| [0.5, 0.6)  | 173 |       0.549 |    0.514 |
| [0.6, 0.7)  | 169 |       0.649 |    0.663 |
| [0.7, 1.01) | 165 |       0.785 |    0.794 |

## 3. Spreads: threshold sweep on the tuning window (2019 to 2022)

|   edge |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|-------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|      1 |    705 |    353 |      352 |       12 |     0.501 |   -34.2 | -0.044 |
|      2 |    442 |    228 |      214 |        9 |     0.516 |    -7.4 | -0.015 |
|      3 |    245 |    124 |      121 |        7 |     0.506 |    -9.1 | -0.034 |
|      4 |    130 |     66 |       64 |        5 |     0.508 |    -4.4 | -0.031 |
|      5 |     62 |     34 |       28 |        1 |     0.548 |     3.2 |  0.047 |
|      6 |     32 |     20 |       12 |        1 |     0.625 |     6.8 |  0.193 |
|      7 |     18 |     12 |        6 |        1 |     0.667 |     5.4 |  0.273 |
|      8 |     14 |      9 |        5 |        0 |     0.643 |     3.5 |  0.227 |

## 4. Totals: threshold sweep on the tuning window

|   edge |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|-------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|      1 |    740 |    373 |      367 |        9 |     0.504 |   -30.7 | -0.038 |
|      2 |    499 |    259 |      240 |        4 |     0.519 |    -5   | -0.009 |
|      3 |    287 |    152 |      135 |        2 |     0.53  |     3.5 |  0.011 |
|      4 |    155 |     79 |       76 |        1 |     0.51  |    -4.6 | -0.027 |
|      5 |     89 |     44 |       45 |        0 |     0.494 |    -5.5 | -0.056 |
|      6 |     35 |     19 |       16 |        0 |     0.543 |     1.4 |  0.036 |
|      7 |     15 |      7 |        8 |        0 |     0.467 |    -1.8 | -0.109 |
|      8 |      8 |      4 |        4 |        0 |     0.5   |    -0.4 | -0.045 |

Best spread threshold with 100+ bets on the tuning window: 2 (ROI -0.015). Best total threshold: 3 (ROI +0.011). The held-out results below use the live flags (5 / 6) and, separately, these.

## 5. Held-out 2023 to 2025, live flags (5 / 6)

Spreads:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
| all |     58 |     30 |       28 |        2 |     0.517 |    -0.8 | -0.013 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|     2023 |     19 |     11 |        8 |        2 |     0.579 |     2.2 |  0.105 |
|     2024 |     23 |     13 |       10 |        0 |     0.565 |     2   |  0.079 |
|     2025 |     16 |      6 |       10 |        0 |     0.375 |    -5   | -0.284 |

By edge size:

| bucket      |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|:------------|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
| [5.0, 6.0)  |     27 |     13 |       14 |        1 |     0.481 |    -2.4 | -0.081 |
| [6.0, 7.0)  |     19 |     11 |        8 |        1 |     0.579 |     2.2 |  0.105 |
| [7.0, 9.0)  |      5 |      2 |        3 |        0 |     0.4   |    -1.3 | -0.236 |
| [9.0, 99.0) |      7 |      4 |        3 |        0 |     0.571 |     0.7 |  0.091 |

Totals:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|------:|
| all |     23 |     16 |        7 |        0 |     0.696 |     8.3 | 0.328 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|------:|
|     2023 |      7 |      5 |        2 |        0 |     0.714 |     2.8 | 0.364 |
|     2024 |     10 |      6 |        4 |        0 |     0.6   |     1.6 | 0.145 |
|     2025 |      6 |      5 |        1 |        0 |     0.833 |     3.9 | 0.591 |

## 5. Held-out 2023 to 2025, tuned (2 / 3)

Spreads:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
| all |    368 |    183 |      185 |        6 |     0.497 |   -20.5 | -0.051 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|     2023 |    117 |     60 |       57 |        5 |     0.513 |    -2.7 | -0.021 |
|     2024 |    131 |     66 |       65 |        1 |     0.504 |    -5.5 | -0.038 |
|     2025 |    120 |     57 |       63 |        0 |     0.475 |   -12.3 | -0.093 |

By edge size:

| bucket      |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|:------------|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
| [2.0, 3.0)  |    157 |     74 |       83 |        3 |     0.471 |   -17.3 | -0.1   |
| [3.0, 4.0)  |    106 |     56 |       50 |        1 |     0.528 |     1   |  0.009 |
| [4.0, 6.0)  |     74 |     36 |       38 |        1 |     0.486 |    -5.8 | -0.071 |
| [6.0, 99.0) |     31 |     17 |       14 |        1 |     0.548 |     1.6 |  0.047 |

Totals:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
| all |    229 |    110 |      119 |        2 |      0.48 |   -20.9 | -0.083 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|     2023 |     86 |     36 |       50 |        1 |     0.419 |   -19   | -0.201 |
|     2024 |     73 |     37 |       36 |        1 |     0.507 |    -2.6 | -0.032 |
|     2025 |     70 |     37 |       33 |        0 |     0.529 |     0.7 |  0.009 |

## 6. Market plus model

Blend the model line with the closing line, pred = a x model + (1 - a) x line. Best a on 2019 to 2022 by margin MAE: 0.

|   a (model share) |   margin MAE 2019-22 |   margin MAE 2023-25 |   total MAE 2023-25 |
|------------------:|---------------------:|---------------------:|--------------------:|
|               0   |                9.888 |                9.744 |              10.121 |
|               0.1 |                9.889 |                9.753 |              10.122 |
|               0.2 |                9.893 |                9.772 |              10.127 |
|               0.3 |                9.904 |                9.8   |              10.136 |
|               0.4 |                9.925 |                9.839 |              10.151 |
|               0.5 |                9.956 |                9.884 |              10.171 |
|               0.6 |                9.989 |                9.931 |              10.196 |
|               0.7 |               10.026 |                9.98  |              10.224 |
|               0.8 |               10.068 |               10.033 |              10.257 |
|               0.9 |               10.112 |               10.091 |              10.293 |
|               1   |               10.159 |               10.152 |              10.335 |

Bet selection is unchanged by blending (the edge is scaled, not re-ordered), so this only improves the score and the probabilities.

## 7. Closing line value

Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).
