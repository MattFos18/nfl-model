# NFL Model 3.0 backtest

Walk-forward: every week is priced with only games played before it; the points regression is refit before every week on every played game since 2013. Ridge strength and bet thresholds were chosen on 2019 to 2022 only, and 2023 to 2025 was the held-out test for them. Since 22 Sep 2026 every new input, and the rating decay and last-season weight, is accepted only when it helps on both windows, so for those choices 2023 to 2025 is a second test window rather than an untouched one; the live season is the only fully unseen test.

## 1. Points miss (mean absolute error) against Vegas

Tuning window 2019 to 2022:

| target      |   3.0 |   Vegas close |   games |
|:------------|------:|--------------:|--------:|
| team points |  7.36 |          7.29 |    1055 |
| margin      | 10.03 |          9.89 |    1055 |
| total       | 10.62 |         10.54 |    1055 |

Held-out 2023 to 2025:

| target      |   3.0 |   Vegas close |   games |
|:------------|------:|--------------:|--------:|
| team points |  7.3  |          7.21 |     816 |
| margin      |  9.98 |          9.74 |     816 |
| total       | 10.26 |         10.12 |     816 |

Held-out, Week 5 on:

| target      |   3.0 |   Vegas close |   games |
|:------------|------:|--------------:|--------:|
| team points |  7.33 |          7.19 |     624 |
| margin      |  9.9  |          9.59 |     624 |
| total       | 10.25 |         10.09 |     624 |

## 2. Win probability, 2019 to 2022 (tuning)

Brier score (lower is better): 3.0 0.2193, market moneyline 0.2111.

3.0 calibration:

| bin         |   n |   predicted |   actual |
|:------------|----:|------------:|---------:|
| [0.0, 0.3)  |  51 |       0.244 |    0.255 |
| [0.3, 0.4)  | 117 |       0.356 |    0.265 |
| [0.4, 0.5)  | 205 |       0.454 |    0.371 |
| [0.5, 0.6)  | 251 |       0.553 |    0.514 |
| [0.6, 0.7)  | 215 |       0.65  |    0.619 |
| [0.7, 1.01) | 216 |       0.772 |    0.778 |

## 2. Win probability, 2023 to 2025 (held out)

Brier score (lower is better): 3.0 0.2184, market moneyline 0.2102.

3.0 calibration:

| bin         |   n |   predicted |   actual |
|:------------|----:|------------:|---------:|
| [0.0, 0.3)  |  39 |       0.253 |    0.282 |
| [0.3, 0.4)  |  83 |       0.356 |    0.386 |
| [0.4, 0.5)  | 180 |       0.453 |    0.344 |
| [0.5, 0.6)  | 186 |       0.549 |    0.5   |
| [0.6, 0.7)  | 175 |       0.648 |    0.709 |
| [0.7, 1.01) | 153 |       0.772 |    0.784 |

## 3. Spreads: threshold sweep on the tuning window (2019 to 2022)

|   edge |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|-------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|      1 |    724 |    370 |      354 |       15 |     0.511 |   -19.4 | -0.024 |
|      2 |    466 |    246 |      220 |        6 |     0.528 |     4   |  0.008 |
|      3 |    288 |    155 |      133 |        4 |     0.538 |     8.7 |  0.027 |
|      4 |    163 |     94 |       69 |        0 |     0.577 |    18.1 |  0.101 |
|      5 |     81 |     47 |       34 |        0 |     0.58  |     9.6 |  0.108 |
|      6 |     39 |     25 |       14 |        0 |     0.641 |     9.6 |  0.224 |
|      7 |     15 |      9 |        6 |        0 |     0.6   |     2.4 |  0.145 |
|      8 |     10 |      5 |        5 |        0 |     0.5   |    -0.5 | -0.045 |

## 4. Totals: threshold sweep on the tuning window

|   edge |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|-------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|      1 |    765 |    400 |      365 |        7 |     0.523 |    -1.5 | -0.002 |
|      2 |    510 |    273 |      237 |        4 |     0.535 |    12.3 |  0.022 |
|      3 |    293 |    160 |      133 |        2 |     0.546 |    13.7 |  0.043 |
|      4 |    150 |     82 |       68 |        1 |     0.547 |     7.2 |  0.044 |
|      5 |     79 |     46 |       33 |        1 |     0.582 |     9.7 |  0.112 |
|      6 |     39 |     22 |       17 |        0 |     0.564 |     3.3 |  0.077 |
|      7 |     13 |      8 |        5 |        0 |     0.615 |     2.5 |  0.175 |
|      8 |      6 |      3 |        3 |        0 |     0.5   |    -0.3 | -0.045 |

Best spread threshold with 100+ bets on the tuning window: 4 (ROI +0.101). Best total threshold: 4 (ROI +0.044). The held-out results below use the live flags (5 / 6) and, separately, these.

## 5. Held-out 2023 to 2025, live flags (5 / 6)

Spreads:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|------:|
| all |     40 |     23 |       17 |        1 |     0.575 |     4.3 | 0.098 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|     2023 |      5 |      4 |        1 |        1 |     0.8   |     2.9 |  0.527 |
|     2024 |     16 |     10 |        6 |        0 |     0.625 |     3.4 |  0.193 |
|     2025 |     19 |      9 |       10 |        0 |     0.474 |    -2   | -0.096 |

By edge size:

| bucket      |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|:------------|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
| [5.0, 6.0)  |     24 |     15 |        9 |        1 |     0.625 |     5.1 |  0.193 |
| [6.0, 7.0)  |      8 |      4 |        4 |        0 |     0.5   |    -0.4 | -0.045 |
| [7.0, 9.0)  |      4 |      2 |        2 |        0 |     0.5   |    -0.2 | -0.045 |
| [9.0, 99.0) |      4 |      2 |        2 |        0 |     0.5   |    -0.2 | -0.045 |

Totals:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|------:|
| all |     22 |     12 |       10 |        0 |     0.545 |       1 | 0.041 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|     2023 |      7 |      3 |        4 |        0 |     0.429 |    -1.4 | -0.182 |
|     2024 |     11 |      5 |        6 |        0 |     0.455 |    -1.6 | -0.132 |
|     2025 |      4 |      4 |        0 |        0 |     1     |     4   |  0.909 |

## 5. Held-out 2023 to 2025, tuned (4 / 4)

Spreads:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|------:|
| all |     79 |     47 |       32 |        2 |     0.595 |    11.8 | 0.136 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|------:|
|     2023 |     13 |      9 |        4 |        2 |     0.692 |     4.6 | 0.322 |
|     2024 |     35 |     20 |       15 |        0 |     0.571 |     3.5 | 0.091 |
|     2025 |     31 |     18 |       13 |        0 |     0.581 |     3.7 | 0.109 |

By edge size:

| bucket      |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|:------------|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
| [4.0, 5.0)  |     39 |     24 |       15 |        1 |     0.615 |     7.5 |  0.175 |
| [5.0, 6.0)  |     24 |     15 |        9 |        1 |     0.625 |     5.1 |  0.193 |
| [6.0, 8.0)  |     10 |      4 |        6 |        0 |     0.4   |    -2.6 | -0.236 |
| [8.0, 99.0) |      6 |      4 |        2 |        0 |     0.667 |     1.8 |  0.273 |

Totals:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
| all |    127 |     61 |       66 |        1 |      0.48 |   -11.6 | -0.083 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|     2023 |     56 |     24 |       32 |        1 |     0.429 |   -11.2 | -0.182 |
|     2024 |     43 |     21 |       22 |        0 |     0.488 |    -3.2 | -0.068 |
|     2025 |     28 |     16 |       12 |        0 |     0.571 |     2.8 |  0.091 |

## 6. Market plus model

Blend the model line with the closing line, pred = a x model + (1 - a) x line. Best a on 2019 to 2022 by margin MAE: 0.3.

|   a (model share) |   margin MAE 2019-22 |   margin MAE 2023-25 |   total MAE 2023-25 |
|------------------:|---------------------:|---------------------:|--------------------:|
|               0   |                9.888 |                9.744 |              10.121 |
|               0.1 |                9.879 |                9.743 |              10.116 |
|               0.2 |                9.874 |                9.748 |              10.115 |
|               0.3 |                9.872 |                9.76  |              10.117 |
|               0.4 |                9.878 |                9.776 |              10.122 |
|               0.5 |                9.89  |                9.797 |              10.133 |
|               0.6 |                9.907 |                9.823 |              10.15  |
|               0.7 |                9.928 |                9.857 |              10.17  |
|               0.8 |                9.956 |                9.895 |              10.196 |
|               0.9 |                9.99  |                9.934 |              10.226 |
|               1   |               10.032 |                9.977 |              10.261 |

Bet selection is unchanged by blending (the edge is scaled, not re-ordered), so this only improves the score and the probabilities.

## 7. Closing line value

Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).
