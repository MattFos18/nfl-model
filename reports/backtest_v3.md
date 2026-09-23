# NFL Model 3.0 backtest

Walk-forward: every week is priced with only games played before it; the points regression is refit before every week on every played game since 2013. Ridge strength and bet thresholds were chosen on 2019 to 2022 only, and 2023 to 2025 was the held-out test for them. Since 22 Sep 2026 every new input, and the rating decay and last-season weight, is accepted only when it helps on both windows, so for those choices 2023 to 2025 is a second test window rather than an untouched one; the live season is the only fully unseen test.

## 1. Points miss (mean absolute error) against Vegas

Tuning window 2019 to 2022:

| target      |   3.0 |   Vegas close |   games |
|:------------|------:|--------------:|--------:|
| team points |  7.37 |          7.29 |    1055 |
| margin      | 10.02 |          9.89 |    1055 |
| total       | 10.64 |         10.54 |    1055 |

Held-out 2023 to 2025:

| target      |   3.0 |   Vegas close |   games |
|:------------|------:|--------------:|--------:|
| team points |  7.3  |          7.21 |     816 |
| margin      | 10    |          9.74 |     816 |
| total       | 10.27 |         10.12 |     816 |

Held-out, Week 5 on:

| target      |   3.0 |   Vegas close |   games |
|:------------|------:|--------------:|--------:|
| team points |  7.34 |          7.19 |     624 |
| margin      |  9.92 |          9.59 |     624 |
| total       | 10.26 |         10.09 |     624 |

## 2. Win probability, 2019 to 2022 (tuning)

Brier score (lower is better): 3.0 0.2193, market moneyline 0.2111.

3.0 calibration:

| bin         |   n |   predicted |   actual |
|:------------|----:|------------:|---------:|
| [0.0, 0.3)  |  51 |       0.247 |    0.255 |
| [0.3, 0.4)  | 122 |       0.358 |    0.279 |
| [0.4, 0.5)  | 199 |       0.454 |    0.357 |
| [0.5, 0.6)  | 251 |       0.553 |    0.514 |
| [0.6, 0.7)  | 220 |       0.65  |    0.636 |
| [0.7, 1.01) | 212 |       0.772 |    0.769 |

## 2. Win probability, 2023 to 2025 (held out)

Brier score (lower is better): 3.0 0.2188, market moneyline 0.2102.

3.0 calibration:

| bin         |   n |   predicted |   actual |
|:------------|----:|------------:|---------:|
| [0.0, 0.3)  |  38 |       0.251 |    0.263 |
| [0.3, 0.4)  |  85 |       0.356 |    0.388 |
| [0.4, 0.5)  | 178 |       0.454 |    0.36  |
| [0.5, 0.6)  | 188 |       0.549 |    0.479 |
| [0.6, 0.7)  | 176 |       0.649 |    0.716 |
| [0.7, 1.01) | 151 |       0.773 |    0.788 |

## 3. Spreads: threshold sweep on the tuning window (2019 to 2022)

|   edge |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|-------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|      1 |    721 |    374 |      347 |       15 |     0.519 |    -7.7 | -0.01  |
|      2 |    465 |    242 |      223 |        7 |     0.52  |    -3.3 | -0.006 |
|      3 |    287 |    155 |      132 |        4 |     0.54  |     9.8 |  0.031 |
|      4 |    165 |     94 |       71 |        2 |     0.57  |    15.9 |  0.088 |
|      5 |     83 |     49 |       34 |        0 |     0.59  |    11.6 |  0.127 |
|      6 |     39 |     24 |       15 |        0 |     0.615 |     7.5 |  0.175 |
|      7 |     16 |     10 |        6 |        0 |     0.625 |     3.4 |  0.193 |
|      8 |     10 |      6 |        4 |        0 |     0.6   |     1.6 |  0.145 |

## 4. Totals: threshold sweep on the tuning window

|   edge |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|-------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|      1 |    770 |    398 |      372 |        8 |     0.517 |   -11.2 | -0.013 |
|      2 |    510 |    272 |      238 |        5 |     0.533 |    10.2 |  0.018 |
|      3 |    291 |    160 |      131 |        2 |     0.55  |    15.9 |  0.05  |
|      4 |    149 |     84 |       65 |        2 |     0.564 |    12.5 |  0.076 |
|      5 |     80 |     46 |       34 |        1 |     0.575 |     8.6 |  0.098 |
|      6 |     39 |     21 |       18 |        0 |     0.538 |     1.2 |  0.028 |
|      7 |     19 |     10 |        9 |        0 |     0.526 |     0.1 |  0.005 |
|      8 |      6 |      3 |        3 |        0 |     0.5   |    -0.3 | -0.045 |

Best spread threshold with 100+ bets on the tuning window: 4 (ROI +0.088). Best total threshold: 4 (ROI +0.076). The held-out results below use the live flags (5 / 6) and, separately, these.

## 5. Held-out 2023 to 2025, live flags (5 / 6)

Spreads:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|------:|
| all |     42 |     24 |       18 |        1 |     0.571 |     4.2 | 0.091 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|     2023 |      6 |      5 |        1 |        1 |     0.833 |     3.9 |  0.591 |
|     2024 |     17 |     10 |        7 |        0 |     0.588 |     2.3 |  0.123 |
|     2025 |     19 |      9 |       10 |        0 |     0.474 |    -2   | -0.096 |

By edge size:

| bucket      |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|:------------|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
| [5.0, 6.0)  |     26 |     16 |       10 |        1 |     0.615 |     5   |  0.175 |
| [6.0, 7.0)  |      8 |      4 |        4 |        0 |     0.5   |    -0.4 | -0.045 |
| [7.0, 9.0)  |      4 |      2 |        2 |        0 |     0.5   |    -0.2 | -0.045 |
| [9.0, 99.0) |      4 |      2 |        2 |        0 |     0.5   |    -0.2 | -0.045 |

Totals:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
| all |     20 |     10 |       10 |        0 |       0.5 |      -1 | -0.045 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|     2023 |      6 |      2 |        4 |        0 |     0.333 |    -2.4 | -0.364 |
|     2024 |     10 |      4 |        6 |        0 |     0.4   |    -2.6 | -0.236 |
|     2025 |      4 |      4 |        0 |        0 |     1     |     4   |  0.909 |

## 5. Held-out 2023 to 2025, tuned (4 / 4)

Spreads:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|------:|
| all |     84 |     50 |       34 |        2 |     0.595 |    12.6 | 0.136 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|------:|
|     2023 |     16 |      9 |        7 |        2 |     0.562 |     1.3 | 0.074 |
|     2024 |     37 |     23 |       14 |        0 |     0.622 |     7.6 | 0.187 |
|     2025 |     31 |     18 |       13 |        0 |     0.581 |     3.7 | 0.109 |

By edge size:

| bucket      |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|:------------|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
| [4.0, 5.0)  |     42 |     26 |       16 |        1 |     0.619 |     8.4 |  0.182 |
| [5.0, 6.0)  |     26 |     16 |       10 |        1 |     0.615 |     5   |  0.175 |
| [6.0, 8.0)  |     10 |      4 |        6 |        0 |     0.4   |    -2.6 | -0.236 |
| [8.0, 99.0) |      6 |      4 |        2 |        0 |     0.667 |     1.8 |  0.273 |

Totals:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
| all |    127 |     60 |       67 |        1 |     0.472 |   -13.7 | -0.098 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|     2023 |     57 |     24 |       33 |        1 |     0.421 |   -12.3 | -0.196 |
|     2024 |     42 |     21 |       21 |        0 |     0.5   |    -2.1 | -0.045 |
|     2025 |     28 |     15 |       13 |        0 |     0.536 |     0.7 |  0.023 |

## 6. Market plus model

Blend the model line with the closing line, pred = a x model + (1 - a) x line. Best a on 2019 to 2022 by margin MAE: 0.3.

|   a (model share) |   margin MAE 2019-22 |   margin MAE 2023-25 |   total MAE 2023-25 |
|------------------:|---------------------:|---------------------:|--------------------:|
|               0   |                9.888 |                9.744 |              10.121 |
|               0.1 |                9.879 |                9.744 |              10.116 |
|               0.2 |                9.872 |                9.751 |              10.117 |
|               0.3 |                9.87  |                9.764 |              10.119 |
|               0.4 |                9.876 |                9.782 |              10.126 |
|               0.5 |                9.887 |                9.804 |              10.137 |
|               0.6 |                9.903 |                9.833 |              10.156 |
|               0.7 |                9.924 |                9.871 |              10.178 |
|               0.8 |                9.951 |                9.91  |              10.205 |
|               0.9 |                9.983 |                9.952 |              10.236 |
|               1   |               10.024 |                9.997 |              10.271 |

Bet selection is unchanged by blending (the edge is scaled, not re-ordered), so this only improves the score and the probabilities.

## 7. Closing line value

Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).
