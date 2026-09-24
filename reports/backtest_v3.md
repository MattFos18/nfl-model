# NFL Model 3.0 backtest

Walk-forward: every week is priced with only games played before it; the points regression is refit before every week on every played game since 2013. Ridge strength and bet thresholds were chosen on 2019 to 2022 only, and 2023 to 2025 was the held-out test for them. Since 22 Sep 2026 every new input, and the rating decay and last-season weight, is accepted only when it helps on both windows, so for those choices 2023 to 2025 is a second test window rather than an untouched one; the live season is the only fully unseen test.

## 1. Points miss (mean absolute error) against Vegas

Tuning window 2019 to 2022:

| target      |   3.0 |   Vegas close |   games |
|:------------|------:|--------------:|--------:|
| team points |  7.34 |          7.29 |    1055 |
| margin      | 10.03 |          9.89 |    1055 |
| total       | 10.61 |         10.54 |    1055 |

Held-out 2023 to 2025:

| target      |   3.0 |   Vegas close |   games |
|:------------|------:|--------------:|--------:|
| team points |  7.27 |          7.21 |     816 |
| margin      |  9.91 |          9.74 |     816 |
| total       | 10.27 |         10.12 |     816 |

Held-out, Week 5 on:

| target      |   3.0 |   Vegas close |   games |
|:------------|------:|--------------:|--------:|
| team points |  7.3  |          7.19 |     624 |
| margin      |  9.82 |          9.59 |     624 |
| total       | 10.26 |         10.09 |     624 |

## 2. Win probability, 2019 to 2022 (tuning)

Brier score (lower is better): 3.0 0.2185, market moneyline 0.2111.

3.0 calibration:

| bin         |   n |   predicted |   actual |
|:------------|----:|------------:|---------:|
| [0.0, 0.3)  |  64 |       0.244 |    0.297 |
| [0.3, 0.4)  | 126 |       0.36  |    0.238 |
| [0.4, 0.5)  | 194 |       0.456 |    0.397 |
| [0.5, 0.6)  | 231 |       0.552 |    0.502 |
| [0.6, 0.7)  | 205 |       0.65  |    0.62  |
| [0.7, 1.01) | 235 |       0.774 |    0.77  |

## 2. Win probability, 2023 to 2025 (held out)

Brier score (lower is better): 3.0 0.2164, market moneyline 0.2102.

3.0 calibration:

| bin         |   n |   predicted |   actual |
|:------------|----:|------------:|---------:|
| [0.0, 0.3)  |  45 |       0.248 |    0.267 |
| [0.3, 0.4)  |  86 |       0.352 |    0.36  |
| [0.4, 0.5)  | 176 |       0.451 |    0.347 |
| [0.5, 0.6)  | 179 |       0.551 |    0.52  |
| [0.6, 0.7)  | 172 |       0.649 |    0.715 |
| [0.7, 1.01) | 158 |       0.779 |    0.772 |

## 3. Spreads: threshold sweep on the tuning window (2019 to 2022)

|   edge |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|-------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|      1 |    701 |    364 |      337 |       16 |     0.519 |    -6.7 | -0.009 |
|      2 |    443 |    231 |      212 |        6 |     0.521 |    -2.2 | -0.005 |
|      3 |    257 |    139 |      118 |        3 |     0.541 |     9.2 |  0.033 |
|      4 |    143 |     84 |       59 |        0 |     0.587 |    19.1 |  0.121 |
|      5 |     68 |     35 |       33 |        0 |     0.515 |    -1.3 | -0.017 |
|      6 |     30 |     15 |       15 |        0 |     0.5   |    -1.5 | -0.045 |
|      7 |     14 |      7 |        7 |        0 |     0.5   |    -0.7 | -0.045 |
|      8 |      9 |      5 |        4 |        0 |     0.556 |     0.6 |  0.061 |

## 4. Totals: threshold sweep on the tuning window

|   edge |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|-------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|      1 |    766 |    395 |      371 |        9 |     0.516 |   -13.1 | -0.016 |
|      2 |    492 |    262 |      230 |        4 |     0.533 |     9   |  0.017 |
|      3 |    282 |    154 |      128 |        2 |     0.546 |    13.2 |  0.043 |
|      4 |    131 |     74 |       57 |        1 |     0.565 |    11.3 |  0.078 |
|      5 |     69 |     42 |       27 |        1 |     0.609 |    12.3 |  0.162 |
|      6 |     36 |     23 |       13 |        0 |     0.639 |     8.7 |  0.22  |
|      7 |     12 |      8 |        4 |        0 |     0.667 |     3.6 |  0.273 |
|      8 |      6 |      3 |        3 |        0 |     0.5   |    -0.3 | -0.045 |

Best spread threshold with 100+ bets on the tuning window: 4 (ROI +0.121). Best total threshold: 4 (ROI +0.078). The held-out results below use the live flags (5 / 6) and, separately, these.

## 5. Held-out 2023 to 2025, live flags (5 / 6)

Spreads:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|------:|
| all |     33 |     19 |       14 |        1 |     0.576 |     3.6 | 0.099 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|     2023 |      4 |      2 |        2 |        1 |     0.5   |    -0.2 | -0.045 |
|     2024 |     12 |      9 |        3 |        0 |     0.75  |     5.7 |  0.432 |
|     2025 |     17 |      8 |        9 |        0 |     0.471 |    -1.9 | -0.102 |

By edge size:

| bucket      |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|:------------|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
| [5.0, 6.0)  |     15 |      9 |        6 |        1 |       0.6 |     2.4 |  0.145 |
| [6.0, 7.0)  |     12 |      6 |        6 |        0 |       0.5 |    -0.6 | -0.045 |
| [7.0, 9.0)  |      5 |      4 |        1 |        0 |       0.8 |     2.9 |  0.527 |
| [9.0, 99.0) |      1 |      0 |        1 |        0 |       0   |    -1.1 | -1     |

Totals:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
| all |     17 |      8 |        9 |        0 |     0.471 |    -1.9 | -0.102 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|     2023 |      3 |      1 |        2 |        0 |     0.333 |    -1.2 | -0.364 |
|     2024 |     11 |      4 |        7 |        0 |     0.364 |    -3.7 | -0.306 |
|     2025 |      3 |      3 |        0 |        0 |     1     |     3   |  0.909 |

## 5. Held-out 2023 to 2025, tuned (4 / 4)

Spreads:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|------:|
| all |     73 |     44 |       29 |        2 |     0.603 |    12.1 | 0.151 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|     2023 |     14 |      9 |        5 |        2 |     0.643 |     3.5 |  0.227 |
|     2024 |     31 |     21 |       10 |        0 |     0.677 |    10   |  0.293 |
|     2025 |     28 |     14 |       14 |        0 |     0.5   |    -1.4 | -0.045 |

By edge size:

| bucket      |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|:------------|-------:|-------:|---------:|---------:|----------:|--------:|------:|
| [4.0, 5.0)  |     40 |     25 |       15 |        1 |     0.625 |     8.5 | 0.193 |
| [5.0, 6.0)  |     15 |      9 |        6 |        1 |     0.6   |     2.4 | 0.145 |
| [6.0, 8.0)  |     13 |      7 |        6 |        0 |     0.538 |     0.4 | 0.028 |
| [8.0, 99.0) |      5 |      3 |        2 |        0 |     0.6   |     0.8 | 0.145 |

Totals:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|------:|
| all |    120 |     63 |       57 |        0 |     0.525 |     0.3 | 0.002 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|     2023 |     50 |     22 |       28 |        0 |     0.44  |    -8.8 | -0.16  |
|     2024 |     39 |     23 |       16 |        0 |     0.59  |     5.4 |  0.126 |
|     2025 |     31 |     18 |       13 |        0 |     0.581 |     3.7 |  0.109 |

## 6. Market plus model

Blend the model line with the closing line, pred = a x model + (1 - a) x line. Best a on 2019 to 2022 by margin MAE: 0.3.

|   a (model share) |   margin MAE 2019-22 |   margin MAE 2023-25 |   total MAE 2023-25 |
|------------------:|---------------------:|---------------------:|--------------------:|
|               0   |                9.888 |                9.744 |              10.121 |
|               0.1 |                9.88  |                9.739 |              10.115 |
|               0.2 |                9.874 |                9.74  |              10.113 |
|               0.3 |                9.873 |                9.744 |              10.116 |
|               0.4 |                9.88  |                9.752 |              10.122 |
|               0.5 |                9.892 |                9.766 |              10.131 |
|               0.6 |                9.909 |                9.786 |              10.147 |
|               0.7 |                9.931 |                9.811 |              10.168 |
|               0.8 |                9.958 |                9.84  |              10.197 |
|               0.9 |                9.991 |                9.875 |              10.23  |
|               1   |               10.03  |                9.914 |              10.265 |

Bet selection is unchanged by blending (the edge is scaled, not re-ordered), so this only improves the score and the probabilities.

## 7. Closing line value

Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).
