# NFL Model 3.0 backtest

Walk-forward: every week is priced with only games played before it; the points regression is refit before every week on every played game since 2013. Ridge strength and bet thresholds were chosen on 2019 to 2022 only, and 2023 to 2025 was the held-out test for them. Since 22 Sep 2026 every new input, and the rating decay and last-season weight, is accepted only when it helps on both windows, so for those choices 2023 to 2025 is a second test window rather than an untouched one; the live season is the only fully unseen test.

## 1. Points miss (mean absolute error) against Vegas

Tuning window 2019 to 2022:

| target      |   3.0 |   Vegas close |   games |
|:------------|------:|--------------:|--------:|
| team points |  7.36 |          7.29 |    1055 |
| margin      | 10.02 |          9.89 |    1055 |
| total       | 10.62 |         10.54 |    1055 |

Held-out 2023 to 2025:

| target      |   3.0 |   Vegas close |   games |
|:------------|------:|--------------:|--------:|
| team points |  7.29 |          7.21 |     816 |
| margin      |  9.97 |          9.74 |     816 |
| total       | 10.26 |         10.12 |     816 |

Held-out, Week 5 on:

| target      |   3.0 |   Vegas close |   games |
|:------------|------:|--------------:|--------:|
| team points |  7.32 |          7.19 |     624 |
| margin      |  9.89 |          9.59 |     624 |
| total       | 10.25 |         10.09 |     624 |

## 2. Win probability, 2019 to 2022 (tuning)

Brier score (lower is better): 3.0 0.2193, market moneyline 0.2111.

3.0 calibration:

| bin         |   n |   predicted |   actual |
|:------------|----:|------------:|---------:|
| [0.0, 0.3)  |  54 |       0.245 |    0.259 |
| [0.3, 0.4)  | 117 |       0.357 |    0.256 |
| [0.4, 0.5)  | 203 |       0.454 |    0.355 |
| [0.5, 0.6)  | 252 |       0.552 |    0.524 |
| [0.6, 0.7)  | 204 |       0.65  |    0.632 |
| [0.7, 1.01) | 225 |       0.77  |    0.769 |

## 2. Win probability, 2023 to 2025 (held out)

Brier score (lower is better): 3.0 0.2181, market moneyline 0.2102.

3.0 calibration:

| bin         |   n |   predicted |   actual |
|:------------|----:|------------:|---------:|
| [0.0, 0.3)  |  41 |       0.252 |    0.268 |
| [0.3, 0.4)  |  84 |       0.359 |    0.381 |
| [0.4, 0.5)  | 175 |       0.452 |    0.337 |
| [0.5, 0.6)  | 190 |       0.55  |    0.526 |
| [0.6, 0.7)  | 170 |       0.648 |    0.694 |
| [0.7, 1.01) | 156 |       0.772 |    0.782 |

## 3. Spreads: threshold sweep on the tuning window (2019 to 2022)

|   edge |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|-------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|      1 |    734 |    382 |      352 |       13 |     0.52  |    -5.2 | -0.006 |
|      2 |    455 |    239 |      216 |        7 |     0.525 |     1.4 |  0.003 |
|      3 |    285 |    153 |      132 |        3 |     0.537 |     7.8 |  0.025 |
|      4 |    162 |     93 |       69 |        0 |     0.574 |    17.1 |  0.096 |
|      5 |     91 |     53 |       38 |        0 |     0.582 |    11.2 |  0.112 |
|      6 |     39 |     25 |       14 |        0 |     0.641 |     9.6 |  0.224 |
|      7 |     13 |      8 |        5 |        0 |     0.615 |     2.5 |  0.175 |
|      8 |      9 |      5 |        4 |        0 |     0.556 |     0.6 |  0.061 |

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

Best spread threshold with 100+ bets on the tuning window: 4 (ROI +0.096). Best total threshold: 4 (ROI +0.044). The held-out results below use the live flags (5 / 6) and, separately, these.

## 5. Held-out 2023 to 2025, live flags (5 / 6)

Spreads:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|------:|
| all |     37 |     21 |       16 |        2 |     0.568 |     3.4 | 0.084 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|     2023 |      5 |      3 |        2 |        2 |     0.6   |     0.8 |  0.145 |
|     2024 |     16 |     10 |        6 |        0 |     0.625 |     3.4 |  0.193 |
|     2025 |     16 |      8 |        8 |        0 |     0.5   |    -0.8 | -0.045 |

By edge size:

| bucket      |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|:------------|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
| [5.0, 6.0)  |     21 |     12 |        9 |        2 |     0.571 |     2.1 |  0.091 |
| [6.0, 7.0)  |      8 |      5 |        3 |        0 |     0.625 |     1.7 |  0.193 |
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
| all |     74 |     46 |       28 |        2 |     0.622 |    15.2 | 0.187 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|------:|
|     2023 |     15 |     10 |        5 |        2 |     0.667 |     4.5 | 0.273 |
|     2024 |     33 |     22 |       11 |        0 |     0.667 |     9.9 | 0.273 |
|     2025 |     26 |     14 |       12 |        0 |     0.538 |     0.8 | 0.028 |

By edge size:

| bucket      |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|:------------|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
| [4.0, 5.0)  |     37 |     25 |       12 |        0 |     0.676 |    11.8 |  0.29  |
| [5.0, 6.0)  |     21 |     12 |        9 |        2 |     0.571 |     2.1 |  0.091 |
| [6.0, 8.0)  |     10 |      5 |        5 |        0 |     0.5   |    -0.5 | -0.045 |
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
|               0.1 |                9.878 |                9.742 |              10.116 |
|               0.2 |                9.871 |                9.747 |              10.115 |
|               0.3 |                9.868 |                9.757 |              10.117 |
|               0.4 |                9.872 |                9.772 |              10.122 |
|               0.5 |                9.883 |                9.791 |              10.133 |
|               0.6 |                9.899 |                9.817 |              10.15  |
|               0.7 |                9.922 |                9.851 |              10.17  |
|               0.8 |                9.949 |                9.888 |              10.196 |
|               0.9 |                9.982 |                9.926 |              10.226 |
|               1   |               10.023 |                9.97  |              10.261 |

Bet selection is unchanged by blending (the edge is scaled, not re-ordered), so this only improves the score and the probabilities.

## 7. Closing line value

Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).
