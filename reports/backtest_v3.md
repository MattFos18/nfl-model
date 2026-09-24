# NFL Model 3.0 backtest

Walk-forward: every week is priced with only games played before it; the points regression is refit before every week on every played game since 2013. Ridge strength and bet thresholds were chosen on 2019 to 2022 only, and 2023 to 2025 was the held-out test for them. Since 22 Sep 2026 every new input, and the rating decay and last-season weight, is accepted only when it helps on both windows, so for those choices 2023 to 2025 is a second test window rather than an untouched one; the live season is the only fully unseen test.

## 1. Points miss (mean absolute error) against Vegas

Tuning window 2019 to 2022:

| target      |   3.0 |   Vegas close |   games |
|:------------|------:|--------------:|--------:|
| team points |  7.34 |          7.29 |    1055 |
| margin      | 10.02 |          9.89 |    1055 |
| total       | 10.61 |         10.54 |    1055 |

Held-out 2023 to 2025:

| target      |   3.0 |   Vegas close |   games |
|:------------|------:|--------------:|--------:|
| team points |  7.27 |          7.21 |     816 |
| margin      |  9.92 |          9.74 |     816 |
| total       | 10.27 |         10.12 |     816 |

Held-out, Week 5 on:

| target      |   3.0 |   Vegas close |   games |
|:------------|------:|--------------:|--------:|
| team points |  7.3  |          7.19 |     624 |
| margin      |  9.82 |          9.59 |     624 |
| total       | 10.27 |         10.09 |     624 |

## 2. Win probability, 2019 to 2022 (tuning)

Brier score (lower is better): 3.0 0.2185, market moneyline 0.2111.

3.0 calibration:

| bin         |   n |   predicted |   actual |
|:------------|----:|------------:|---------:|
| [0.0, 0.3)  |  64 |       0.245 |    0.297 |
| [0.3, 0.4)  | 124 |       0.359 |    0.242 |
| [0.4, 0.5)  | 197 |       0.456 |    0.391 |
| [0.5, 0.6)  | 230 |       0.553 |    0.504 |
| [0.6, 0.7)  | 204 |       0.65  |    0.618 |
| [0.7, 1.01) | 236 |       0.773 |    0.771 |

## 2. Win probability, 2023 to 2025 (held out)

Brier score (lower is better): 3.0 0.2165, market moneyline 0.2102.

3.0 calibration:

| bin         |   n |   predicted |   actual |
|:------------|----:|------------:|---------:|
| [0.0, 0.3)  |  44 |       0.247 |    0.273 |
| [0.3, 0.4)  |  85 |       0.35  |    0.353 |
| [0.4, 0.5)  | 181 |       0.451 |    0.348 |
| [0.5, 0.6)  | 177 |       0.551 |    0.525 |
| [0.6, 0.7)  | 171 |       0.65  |    0.713 |
| [0.7, 1.01) | 158 |       0.779 |    0.772 |

## 3. Spreads: threshold sweep on the tuning window (2019 to 2022)

|   edge |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|-------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|      1 |    700 |    362 |      338 |       15 |     0.517 |    -9.8 | -0.013 |
|      2 |    438 |    233 |      205 |        6 |     0.532 |     7.5 |  0.016 |
|      3 |    256 |    137 |      119 |        3 |     0.535 |     6.1 |  0.022 |
|      4 |    143 |     84 |       59 |        0 |     0.587 |    19.1 |  0.121 |
|      5 |     70 |     37 |       33 |        0 |     0.529 |     0.7 |  0.009 |
|      6 |     31 |     16 |       15 |        0 |     0.516 |    -0.5 | -0.015 |
|      7 |     14 |      7 |        7 |        0 |     0.5   |    -0.7 | -0.045 |
|      8 |      9 |      5 |        4 |        0 |     0.556 |     0.6 |  0.061 |

## 4. Totals: threshold sweep on the tuning window

|   edge |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|-------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|      1 |    766 |    397 |      369 |        9 |     0.518 |    -8.9 | -0.011 |
|      2 |    492 |    262 |      230 |        4 |     0.533 |     9   |  0.017 |
|      3 |    284 |    155 |      129 |        2 |     0.546 |    13.1 |  0.042 |
|      4 |    133 |     75 |       58 |        1 |     0.564 |    11.2 |  0.077 |
|      5 |     69 |     41 |       28 |        1 |     0.594 |    10.2 |  0.134 |
|      6 |     36 |     23 |       13 |        0 |     0.639 |     8.7 |  0.22  |
|      7 |     12 |      8 |        4 |        0 |     0.667 |     3.6 |  0.273 |
|      8 |      6 |      3 |        3 |        0 |     0.5   |    -0.3 | -0.045 |

Best spread threshold with 100+ bets on the tuning window: 4 (ROI +0.121). Best total threshold: 4 (ROI +0.077). The held-out results below use the live flags (5 / 6) and, separately, these.

## 5. Held-out 2023 to 2025, live flags (5 / 6)

Spreads:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|------:|
| all |     34 |     20 |       14 |        2 |     0.588 |     4.6 | 0.123 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|     2023 |      4 |      2 |        2 |        2 |     0.5   |    -0.2 | -0.045 |
|     2024 |     13 |     10 |        3 |        0 |     0.769 |     6.7 |  0.469 |
|     2025 |     17 |      8 |        9 |        0 |     0.471 |    -1.9 | -0.102 |

By edge size:

| bucket      |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|:------------|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
| [5.0, 6.0)  |     16 |     10 |        6 |        2 |     0.625 |     3.4 |  0.193 |
| [6.0, 7.0)  |     12 |      6 |        6 |        0 |     0.5   |    -0.6 | -0.045 |
| [7.0, 9.0)  |      5 |      4 |        1 |        0 |     0.8   |     2.9 |  0.527 |
| [9.0, 99.0) |      1 |      0 |        1 |        0 |     0     |    -1.1 | -1     |

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
| all |     72 |     45 |       27 |        2 |     0.625 |    15.3 | 0.193 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|     2023 |     13 |      9 |        4 |        2 |     0.692 |     4.6 |  0.322 |
|     2024 |     30 |     21 |        9 |        0 |     0.7   |    11.1 |  0.336 |
|     2025 |     29 |     15 |       14 |        0 |     0.517 |    -0.4 | -0.013 |

By edge size:

| bucket      |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|:------------|-------:|-------:|---------:|---------:|----------:|--------:|------:|
| [4.0, 5.0)  |     38 |     25 |       13 |        0 |     0.658 |    10.7 | 0.256 |
| [5.0, 6.0)  |     16 |     10 |        6 |        2 |     0.625 |     3.4 | 0.193 |
| [6.0, 8.0)  |     13 |      7 |        6 |        0 |     0.538 |     0.4 | 0.028 |
| [8.0, 99.0) |      5 |      3 |        2 |        0 |     0.6   |     0.8 | 0.145 |

Totals:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
| all |    120 |     62 |       58 |        0 |     0.517 |    -1.8 | -0.014 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|     2023 |     49 |     21 |       28 |        0 |     0.429 |    -9.8 | -0.182 |
|     2024 |     40 |     23 |       17 |        0 |     0.575 |     4.3 |  0.098 |
|     2025 |     31 |     18 |       13 |        0 |     0.581 |     3.7 |  0.109 |

## 6. Market plus model

Blend the model line with the closing line, pred = a x model + (1 - a) x line. Best a on 2019 to 2022 by margin MAE: 0.3.

|   a (model share) |   margin MAE 2019-22 |   margin MAE 2023-25 |   total MAE 2023-25 |
|------------------:|---------------------:|---------------------:|--------------------:|
|               0   |                9.888 |                9.744 |              10.121 |
|               0.1 |                9.88  |                9.739 |              10.115 |
|               0.2 |                9.873 |                9.74  |              10.114 |
|               0.3 |                9.871 |                9.744 |              10.117 |
|               0.4 |                9.877 |                9.752 |              10.123 |
|               0.5 |                9.889 |                9.766 |              10.133 |
|               0.6 |                9.905 |                9.787 |              10.149 |
|               0.7 |                9.927 |                9.812 |              10.171 |
|               0.8 |                9.953 |                9.842 |              10.199 |
|               0.9 |                9.985 |                9.876 |              10.233 |
|               1   |               10.024 |                9.916 |              10.269 |

Bet selection is unchanged by blending (the edge is scaled, not re-ordered), so this only improves the score and the probabilities.

## 7. Closing line value

Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).
