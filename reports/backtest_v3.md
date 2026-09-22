# NFL Model 3.0 backtest

Walk-forward: every week is priced with only games played before it; the points regression is refit before every week on every played game since 2013. Ridge strength and bet thresholds were chosen on 2019 to 2022 only, and 2023 to 2025 was the held-out test for them. Since 22 Sep 2026 every new input, and the rating decay and last-season weight, is accepted only when it helps on both windows, so for those choices 2023 to 2025 is a second test window rather than an untouched one; the live season is the only fully unseen test.

## 1. Points miss (mean absolute error) against Vegas

Tuning window 2019 to 2022:

| target      |   3.0 |   Vegas close |   games |
|:------------|------:|--------------:|--------:|
| team points |  7.4  |          7.29 |    1055 |
| margin      | 10.05 |          9.89 |    1055 |
| total       | 10.64 |         10.54 |    1055 |

Held-out 2023 to 2025:

| target      |   3.0 |   Vegas close |   games |
|:------------|------:|--------------:|--------:|
| team points |  7.3  |          7.21 |     816 |
| margin      | 10.04 |          9.74 |     816 |
| total       | 10.27 |         10.12 |     816 |

Held-out, Week 5 on:

| target      |   3.0 |   Vegas close |   games |
|:------------|------:|--------------:|--------:|
| team points |  7.34 |          7.19 |     624 |
| margin      |  9.95 |          9.59 |     624 |
| total       | 10.26 |         10.09 |     624 |

## 2. Win probability, 2019 to 2022 (tuning)

Brier score (lower is better): 3.0 0.2198, market moneyline 0.2111.

3.0 calibration:

| bin         |   n |   predicted |   actual |
|:------------|----:|------------:|---------:|
| [0.0, 0.3)  |  51 |       0.243 |    0.255 |
| [0.3, 0.4)  | 112 |       0.356 |    0.277 |
| [0.4, 0.5)  | 203 |       0.455 |    0.36  |
| [0.5, 0.6)  | 260 |       0.553 |    0.504 |
| [0.6, 0.7)  | 220 |       0.649 |    0.614 |
| [0.7, 1.01) | 209 |       0.771 |    0.799 |

## 2. Win probability, 2023 to 2025 (held out)

Brier score (lower is better): 3.0 0.2197, market moneyline 0.2102.

3.0 calibration:

| bin         |   n |   predicted |   actual |
|:------------|----:|------------:|---------:|
| [0.0, 0.3)  |  38 |       0.251 |    0.316 |
| [0.3, 0.4)  |  76 |       0.355 |    0.329 |
| [0.4, 0.5)  | 185 |       0.454 |    0.384 |
| [0.5, 0.6)  | 197 |       0.552 |    0.492 |
| [0.6, 0.7)  | 169 |       0.649 |    0.71  |
| [0.7, 1.01) | 151 |       0.768 |    0.775 |

## 3. Spreads: threshold sweep on the tuning window (2019 to 2022)

|   edge |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|-------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|      1 |    710 |    364 |      346 |       16 |     0.513 |   -16.6 | -0.021 |
|      2 |    455 |    239 |      216 |        9 |     0.525 |     1.4 |  0.003 |
|      3 |    283 |    155 |      128 |        4 |     0.548 |    14.2 |  0.046 |
|      4 |    161 |     87 |       74 |        1 |     0.54  |     5.6 |  0.032 |
|      5 |     84 |     51 |       33 |        0 |     0.607 |    14.7 |  0.159 |
|      6 |     35 |     19 |       16 |        0 |     0.543 |     1.4 |  0.036 |
|      7 |     22 |     12 |       10 |        0 |     0.545 |     1   |  0.041 |
|      8 |     10 |      5 |        5 |        0 |     0.5   |    -0.5 | -0.045 |

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

Best spread threshold with 100+ bets on the tuning window: 3 (ROI +0.046). Best total threshold: 4 (ROI +0.076). The held-out results below use the live flags (5 / 6) and, separately, these.

## 5. Held-out 2023 to 2025, live flags (5 / 6)

Spreads:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|------:|
| all |     37 |     21 |       16 |        1 |     0.568 |     3.4 | 0.084 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|     2023 |      8 |      5 |        3 |        1 |     0.625 |     1.7 |  0.193 |
|     2024 |     15 |     11 |        4 |        0 |     0.733 |     6.6 |  0.4   |
|     2025 |     14 |      5 |        9 |        0 |     0.357 |    -4.9 | -0.318 |

By edge size:

| bucket      |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|:------------|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
| [5.0, 6.0)  |     22 |     13 |        9 |        1 |     0.591 |     3.1 |  0.128 |
| [6.0, 7.0)  |      9 |      5 |        4 |        0 |     0.556 |     0.6 |  0.061 |
| [7.0, 9.0)  |      3 |      2 |        1 |        0 |     0.667 |     0.9 |  0.273 |
| [9.0, 99.0) |      3 |      1 |        2 |        0 |     0.333 |    -1.2 | -0.364 |

Totals:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
| all |     20 |     10 |       10 |        0 |       0.5 |      -1 | -0.045 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|     2023 |      6 |      2 |        4 |        0 |     0.333 |    -2.4 | -0.364 |
|     2024 |     10 |      4 |        6 |        0 |     0.4   |    -2.6 | -0.236 |
|     2025 |      4 |      4 |        0 |        0 |     1     |     4   |  0.909 |

## 5. Held-out 2023 to 2025, tuned (3 / 4)

Spreads:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|------:|
| all |    185 |     97 |       88 |        4 |     0.524 |     0.2 | 0.001 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|     2023 |     47 |     22 |       25 |        3 |     0.468 |    -5.5 | -0.106 |
|     2024 |     77 |     45 |       32 |        0 |     0.584 |     9.8 |  0.116 |
|     2025 |     61 |     30 |       31 |        1 |     0.492 |    -4.1 | -0.061 |

By edge size:

| bucket      |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|:------------|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
| [3.0, 4.0)  |     94 |     42 |       52 |        3 |     0.447 |   -15.2 | -0.147 |
| [4.0, 5.0)  |     54 |     34 |       20 |        0 |     0.63  |    12   |  0.202 |
| [5.0, 7.0)  |     31 |     18 |       13 |        1 |     0.581 |     3.7 |  0.109 |
| [7.0, 99.0) |      6 |      3 |        3 |        0 |     0.5   |    -0.3 | -0.045 |

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

Blend the model line with the closing line, pred = a x model + (1 - a) x line. Best a on 2019 to 2022 by margin MAE: 0.2.

|   a (model share) |   margin MAE 2019-22 |   margin MAE 2023-25 |   total MAE 2023-25 |
|------------------:|---------------------:|---------------------:|--------------------:|
|               0   |                9.888 |                9.744 |              10.121 |
|               0.1 |                9.88  |                9.749 |              10.116 |
|               0.2 |                9.874 |                9.759 |              10.117 |
|               0.3 |                9.876 |                9.775 |              10.119 |
|               0.4 |                9.887 |                9.797 |              10.126 |
|               0.5 |                9.902 |                9.824 |              10.137 |
|               0.6 |                9.923 |                9.859 |              10.156 |
|               0.7 |                9.947 |                9.899 |              10.178 |
|               0.8 |                9.977 |                9.941 |              10.205 |
|               0.9 |               10.01  |                9.988 |              10.236 |
|               1   |               10.052 |               10.04  |              10.271 |

Bet selection is unchanged by blending (the edge is scaled, not re-ordered), so this only improves the score and the probabilities.

## 7. Closing line value

Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).
