# NFL Model 3.0 backtest

Walk-forward: every week is priced with only games played before it; the points regression is refit before every week on every played game since 2013. Rating parameters, ridge strength and bet thresholds were chosen on 2019 to 2022 only. 2023 to 2025 is the held-out test the tuning never saw.

## 1. Points miss (mean absolute error) against Vegas

Tuning window 2019 to 2022:

| target      |   3.0 |   Vegas close |   games |
|:------------|------:|--------------:|--------:|
| team points |  7.41 |          7.29 |    1055 |
| margin      | 10.1  |          9.89 |    1055 |
| total       | 10.62 |         10.54 |    1055 |

Held-out 2023 to 2025:

| target      |   3.0 |   Vegas close |   games |
|:------------|------:|--------------:|--------:|
| team points |  7.32 |          7.21 |     816 |
| margin      | 10.06 |          9.74 |     816 |
| total       | 10.3  |         10.12 |     816 |

Held-out, Week 5 on:

| target      |   3.0 |   Vegas close |   games |
|:------------|------:|--------------:|--------:|
| team points |  7.33 |          7.19 |     624 |
| margin      |  9.94 |          9.59 |     624 |
| total       | 10.27 |         10.09 |     624 |

## 2. Win probability, 2019 to 2022 (tuning)

Brier score (lower is better): 3.0 0.2212, market moneyline 0.2111.

3.0 calibration:

| bin         |   n |   predicted |   actual |
|:------------|----:|------------:|---------:|
| [0.0, 0.3)  |  49 |       0.243 |    0.245 |
| [0.3, 0.4)  |  99 |       0.355 |    0.273 |
| [0.4, 0.5)  | 198 |       0.454 |    0.419 |
| [0.5, 0.6)  | 283 |       0.55  |    0.445 |
| [0.6, 0.7)  | 234 |       0.647 |    0.65  |
| [0.7, 1.01) | 192 |       0.769 |    0.781 |

## 2. Win probability, 2023 to 2025 (held out)

Brier score (lower is better): 3.0 0.2200, market moneyline 0.2102.

3.0 calibration:

| bin         |   n |   predicted |   actual |
|:------------|----:|------------:|---------:|
| [0.0, 0.3)  |  35 |       0.245 |    0.286 |
| [0.3, 0.4)  |  81 |       0.352 |    0.346 |
| [0.4, 0.5)  | 175 |       0.456 |    0.389 |
| [0.5, 0.6)  | 216 |       0.551 |    0.495 |
| [0.6, 0.7)  | 161 |       0.652 |    0.689 |
| [0.7, 1.01) | 148 |       0.769 |    0.797 |

## 3. Spreads: threshold sweep on the tuning window (2019 to 2022)

|   edge |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|-------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|      1 |    719 |    362 |      357 |       13 |     0.503 |   -30.7 | -0.039 |
|      2 |    462 |    242 |      220 |        8 |     0.524 |     0   |  0     |
|      3 |    282 |    151 |      131 |        6 |     0.535 |     6.9 |  0.022 |
|      4 |    161 |     84 |       77 |        2 |     0.522 |    -0.7 | -0.004 |
|      5 |     88 |     48 |       40 |        1 |     0.545 |     4   |  0.041 |
|      6 |     38 |     23 |       15 |        0 |     0.605 |     6.5 |  0.156 |
|      7 |     18 |     11 |        7 |        0 |     0.611 |     3.3 |  0.167 |
|      8 |     14 |      8 |        6 |        0 |     0.571 |     1.4 |  0.091 |

## 4. Totals: threshold sweep on the tuning window

|   edge |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|-------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|      1 |    752 |    383 |      369 |        7 |     0.509 |   -22.9 | -0.028 |
|      2 |    482 |    256 |      226 |        5 |     0.531 |     7.4 |  0.014 |
|      3 |    280 |    148 |      132 |        2 |     0.529 |     2.8 |  0.009 |
|      4 |    141 |     82 |       59 |        1 |     0.582 |    17.1 |  0.11  |
|      5 |     72 |     44 |       28 |        0 |     0.611 |    13.2 |  0.167 |
|      6 |     37 |     22 |       15 |        0 |     0.595 |     5.5 |  0.135 |
|      7 |     12 |      8 |        4 |        0 |     0.667 |     3.6 |  0.273 |
|      8 |      4 |      1 |        3 |        0 |     0.25  |    -2.3 | -0.523 |

Best spread threshold with 100+ bets on the tuning window: 3 (ROI +0.022). Best total threshold: 4 (ROI +0.110). The held-out results below use the live flags (5 / 6) and, separately, these.

## 5. Held-out 2023 to 2025, live flags (5 / 6)

Spreads:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|------:|
| all |     47 |     29 |       18 |        1 |     0.617 |     9.2 | 0.178 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|------:|
|     2023 |     13 |      9 |        4 |        1 |     0.692 |     4.6 | 0.322 |
|     2024 |     17 |     11 |        6 |        0 |     0.647 |     4.4 | 0.235 |
|     2025 |     17 |      9 |        8 |        0 |     0.529 |     0.2 | 0.011 |

By edge size:

| bucket      |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|:------------|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
| [5.0, 6.0)  |     31 |     22 |        9 |        1 |     0.71  |    12.1 |  0.355 |
| [6.0, 7.0)  |      9 |      3 |        6 |        0 |     0.333 |    -3.6 | -0.364 |
| [7.0, 9.0)  |      4 |      3 |        1 |        0 |     0.75  |     1.9 |  0.432 |
| [9.0, 99.0) |      3 |      1 |        2 |        0 |     0.333 |    -1.2 | -0.364 |

Totals:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|------:|
| all |     18 |     10 |        8 |        0 |     0.556 |     1.2 | 0.061 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|     2023 |      5 |      3 |        2 |        0 |       0.6 |     0.8 |  0.145 |
|     2024 |     10 |      4 |        6 |        0 |       0.4 |    -2.6 | -0.236 |
|     2025 |      3 |      3 |        0 |        0 |       1   |     3   |  0.909 |

## 5. Held-out 2023 to 2025, tuned (3 / 4)

Spreads:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|------:|
| all |    192 |    104 |       88 |        3 |     0.542 |     7.2 | 0.034 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|     2023 |     65 |     31 |       34 |        3 |     0.477 |    -6.4 | -0.09  |
|     2024 |     72 |     42 |       30 |        0 |     0.583 |     9   |  0.114 |
|     2025 |     55 |     31 |       24 |        0 |     0.564 |     4.6 |  0.076 |

By edge size:

| bucket      |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|:------------|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
| [3.0, 4.0)  |     93 |     44 |       49 |        2 |     0.473 |    -9.9 | -0.097 |
| [4.0, 5.0)  |     52 |     31 |       21 |        0 |     0.596 |     7.9 |  0.138 |
| [5.0, 7.0)  |     40 |     25 |       15 |        1 |     0.625 |     8.5 |  0.193 |
| [7.0, 99.0) |      7 |      4 |        3 |        0 |     0.571 |     0.7 |  0.091 |

Totals:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
| all |    121 |     61 |       60 |        1 |     0.504 |      -5 | -0.038 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|     2023 |     56 |     24 |       32 |        1 |     0.429 |   -11.2 | -0.182 |
|     2024 |     40 |     24 |       16 |        0 |     0.6   |     6.4 |  0.145 |
|     2025 |     25 |     13 |       12 |        0 |     0.52  |    -0.2 | -0.007 |

## 6. Market plus model

Blend the model line with the closing line, pred = a x model + (1 - a) x line. Best a on 2019 to 2022 by margin MAE: 0.2.

|   a (model share) |   margin MAE 2019-22 |   margin MAE 2023-25 |   total MAE 2023-25 |
|------------------:|---------------------:|---------------------:|--------------------:|
|               0   |                9.888 |                9.744 |              10.121 |
|               0.1 |                9.882 |                9.746 |              10.119 |
|               0.2 |                9.88  |                9.756 |              10.122 |
|               0.3 |                9.887 |                9.774 |              10.128 |
|               0.4 |                9.903 |                9.798 |              10.139 |
|               0.5 |                9.926 |                9.827 |              10.153 |
|               0.6 |                9.953 |                9.863 |              10.173 |
|               0.7 |                9.983 |                9.907 |              10.197 |
|               0.8 |               10.016 |                9.953 |              10.225 |
|               0.9 |               10.054 |               10.005 |              10.259 |
|               1   |               10.098 |               10.063 |              10.296 |

Bet selection is unchanged by blending (the edge is scaled, not re-ordered), so this only improves the score and the probabilities.

## 7. Closing line value

Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).
