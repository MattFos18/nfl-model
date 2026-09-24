# NFL Model 3.0 backtest

Walk-forward: every week is priced with only games played before it; the points regression is refit before every week on every played game since 2013. Ridge strength and bet thresholds were chosen on 2019 to 2022 only, and 2023 to 2025 was the held-out test for them. Since 22 Sep 2026 every new input, and the rating decay and last-season weight, is accepted only when it helps on both windows, so for those choices 2023 to 2025 is a second test window rather than an untouched one; the live season is the only fully unseen test.

## 1. Points miss (mean absolute error) against Vegas

Tuning window 2019 to 2022:

| target      |   3.0 |   Vegas close |   games |
|:------------|------:|--------------:|--------:|
| team points |  7.35 |          7.29 |    1055 |
| margin      | 10.02 |          9.89 |    1055 |
| total       | 10.63 |         10.54 |    1055 |

Held-out 2023 to 2025:

| target      |   3.0 |   Vegas close |   games |
|:------------|------:|--------------:|--------:|
| team points |  7.28 |          7.21 |     816 |
| margin      |  9.93 |          9.74 |     816 |
| total       | 10.27 |         10.12 |     816 |

Held-out, Week 5 on:

| target      |   3.0 |   Vegas close |   games |
|:------------|------:|--------------:|--------:|
| team points |  7.31 |          7.19 |     624 |
| margin      |  9.84 |          9.59 |     624 |
| total       | 10.27 |         10.09 |     624 |

## 2. Win probability, 2019 to 2022 (tuning)

Brier score (lower is better): 3.0 0.2185, market moneyline 0.2111.

3.0 calibration:

| bin         |   n |   predicted |   actual |
|:------------|----:|------------:|---------:|
| [0.0, 0.3)  |  65 |       0.245 |    0.277 |
| [0.3, 0.4)  | 125 |       0.36  |    0.272 |
| [0.4, 0.5)  | 195 |       0.456 |    0.364 |
| [0.5, 0.6)  | 224 |       0.551 |    0.518 |
| [0.6, 0.7)  | 212 |       0.649 |    0.627 |
| [0.7, 1.01) | 234 |       0.774 |    0.761 |

## 2. Win probability, 2023 to 2025 (held out)

Brier score (lower is better): 3.0 0.2169, market moneyline 0.2102.

3.0 calibration:

| bin         |   n |   predicted |   actual |
|:------------|----:|------------:|---------:|
| [0.0, 0.3)  |  45 |       0.249 |    0.289 |
| [0.3, 0.4)  |  88 |       0.355 |    0.341 |
| [0.4, 0.5)  | 171 |       0.452 |    0.357 |
| [0.5, 0.6)  | 184 |       0.55  |    0.511 |
| [0.6, 0.7)  | 172 |       0.65  |    0.721 |
| [0.7, 1.01) | 156 |       0.779 |    0.769 |

## 3. Spreads: threshold sweep on the tuning window (2019 to 2022)

|   edge |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|-------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|      1 |    715 |    374 |      341 |       13 |     0.523 |    -1.1 | -0.001 |
|      2 |    449 |    241 |      208 |        6 |     0.537 |    12.2 |  0.025 |
|      3 |    271 |    147 |      124 |        5 |     0.542 |    10.6 |  0.036 |
|      4 |    153 |     89 |       64 |        0 |     0.582 |    18.6 |  0.111 |
|      5 |     71 |     38 |       33 |        0 |     0.535 |     1.7 |  0.022 |
|      6 |     34 |     20 |       14 |        0 |     0.588 |     4.6 |  0.123 |
|      7 |     14 |      7 |        7 |        0 |     0.5   |    -0.7 | -0.045 |
|      8 |      9 |      5 |        4 |        0 |     0.556 |     0.6 |  0.061 |

## 4. Totals: threshold sweep on the tuning window

|   edge |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|-------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|      1 |    764 |    398 |      366 |        8 |     0.521 |    -4.6 | -0.005 |
|      2 |    502 |    267 |      235 |        4 |     0.532 |     8.5 |  0.015 |
|      3 |    286 |    156 |      130 |        2 |     0.545 |    13   |  0.041 |
|      4 |    140 |     76 |       64 |        1 |     0.543 |     5.6 |  0.036 |
|      5 |     75 |     45 |       30 |        1 |     0.6   |    12   |  0.145 |
|      6 |     39 |     23 |       16 |        0 |     0.59  |     5.4 |  0.126 |
|      7 |     13 |      9 |        4 |        0 |     0.692 |     4.6 |  0.322 |
|      8 |      6 |      3 |        3 |        0 |     0.5   |    -0.3 | -0.045 |

Best spread threshold with 100+ bets on the tuning window: 4 (ROI +0.111). Best total threshold: 3 (ROI +0.041). The held-out results below use the live flags (5 / 6) and, separately, these.

## 5. Held-out 2023 to 2025, live flags (5 / 6)

Spreads:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|------:|
| all |     37 |     21 |       16 |        2 |     0.568 |     3.4 | 0.084 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|     2023 |      6 |      3 |        3 |        2 |     0.5   |    -0.3 | -0.045 |
|     2024 |     15 |     11 |        4 |        0 |     0.733 |     6.6 |  0.4   |
|     2025 |     16 |      7 |        9 |        0 |     0.438 |    -2.9 | -0.165 |

By edge size:

| bucket      |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|:------------|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
| [5.0, 6.0)  |     16 |      9 |        7 |        1 |     0.562 |     1.3 |  0.074 |
| [6.0, 7.0)  |     12 |      6 |        6 |        1 |     0.5   |    -0.6 | -0.045 |
| [7.0, 9.0)  |      6 |      5 |        1 |        0 |     0.833 |     3.9 |  0.591 |
| [9.0, 99.0) |      3 |      1 |        2 |        0 |     0.333 |    -1.2 | -0.364 |

Totals:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|------:|
| all |     23 |     13 |       10 |        0 |     0.565 |       2 | 0.079 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|     2023 |      6 |      3 |        3 |        0 |     0.5   |    -0.3 | -0.045 |
|     2024 |     13 |      6 |        7 |        0 |     0.462 |    -1.7 | -0.119 |
|     2025 |      4 |      4 |        0 |        0 |     1     |     4   |  0.909 |

## 5. Held-out 2023 to 2025, tuned (4 / 3)

Spreads:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|------:|
| all |     76 |     46 |       30 |        2 |     0.605 |      13 | 0.156 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|     2023 |     15 |     10 |        5 |        2 |     0.667 |     4.5 |  0.273 |
|     2024 |     32 |     22 |       10 |        0 |     0.688 |    11   |  0.312 |
|     2025 |     29 |     14 |       15 |        0 |     0.483 |    -2.5 | -0.078 |

By edge size:

| bucket      |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|:------------|-------:|-------:|---------:|---------:|----------:|--------:|------:|
| [4.0, 5.0)  |     39 |     25 |       14 |        0 |     0.641 |     9.6 | 0.224 |
| [5.0, 6.0)  |     16 |      9 |        7 |        1 |     0.562 |     1.3 | 0.074 |
| [6.0, 8.0)  |     15 |      8 |        7 |        1 |     0.533 |     0.3 | 0.018 |
| [8.0, 99.0) |      6 |      4 |        2 |        0 |     0.667 |     1.8 | 0.273 |

Totals:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
| all |    251 |    131 |      120 |        2 |     0.522 |      -1 | -0.004 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|     2023 |    100 |     48 |       52 |        2 |     0.48  |    -9.2 | -0.084 |
|     2024 |     85 |     47 |       38 |        0 |     0.553 |     5.2 |  0.056 |
|     2025 |     66 |     36 |       30 |        0 |     0.545 |     3   |  0.041 |

## 6. Market plus model

Blend the model line with the closing line, pred = a x model + (1 - a) x line. Best a on 2019 to 2022 by margin MAE: 0.3.

|   a (model share) |   margin MAE 2019-22 |   margin MAE 2023-25 |   total MAE 2023-25 |
|------------------:|---------------------:|---------------------:|--------------------:|
|               0   |                9.888 |                9.744 |              10.121 |
|               0.1 |                9.878 |                9.74  |              10.115 |
|               0.2 |                9.87  |                9.741 |              10.114 |
|               0.3 |                9.866 |                9.746 |              10.116 |
|               0.4 |                9.872 |                9.757 |              10.123 |
|               0.5 |                9.883 |                9.773 |              10.135 |
|               0.6 |                9.897 |                9.795 |              10.154 |
|               0.7 |                9.918 |                9.821 |              10.176 |
|               0.8 |                9.944 |                9.852 |              10.204 |
|               0.9 |                9.976 |                9.887 |              10.239 |
|               1   |               10.016 |                9.927 |              10.274 |

Bet selection is unchanged by blending (the edge is scaled, not re-ordered), so this only improves the score and the probabilities.

## 7. Closing line value

Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).
