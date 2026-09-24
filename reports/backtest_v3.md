# NFL Model 3.0 backtest

Walk-forward: every week is priced with only games played before it; the points regression is refit before every week on every played game since 2013. Ridge strength and bet thresholds were chosen on 2019 to 2022 only, and 2023 to 2025 was the held-out test for them. Since 22 Sep 2026 every new input, and the rating decay and last-season weight, is accepted only when it helps on both windows, so for those choices 2023 to 2025 is a second test window rather than an untouched one; the live season is the only fully unseen test.

## 1. Points miss (mean absolute error) against Vegas

Tuning window 2019 to 2022:

| target      |   3.0 |   Vegas close |   games |
|:------------|------:|--------------:|--------:|
| team points |  7.34 |          7.29 |    1055 |
| margin      | 10.03 |          9.89 |    1055 |
| total       | 10.62 |         10.54 |    1055 |

Held-out 2023 to 2025:

| target      |   3.0 |   Vegas close |   games |
|:------------|------:|--------------:|--------:|
| team points |  7.27 |          7.21 |     816 |
| margin      |  9.91 |          9.74 |     816 |
| total       | 10.26 |         10.12 |     816 |

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
| [0.3, 0.4)  | 126 |       0.36  |    0.246 |
| [0.4, 0.5)  | 193 |       0.456 |    0.394 |
| [0.5, 0.6)  | 231 |       0.552 |    0.502 |
| [0.6, 0.7)  | 206 |       0.65  |    0.617 |
| [0.7, 1.01) | 235 |       0.774 |    0.77  |

## 2. Win probability, 2023 to 2025 (held out)

Brier score (lower is better): 3.0 0.2164, market moneyline 0.2102.

3.0 calibration:

| bin         |   n |   predicted |   actual |
|:------------|----:|------------:|---------:|
| [0.0, 0.3)  |  45 |       0.248 |    0.267 |
| [0.3, 0.4)  |  85 |       0.352 |    0.365 |
| [0.4, 0.5)  | 178 |       0.451 |    0.348 |
| [0.5, 0.6)  | 180 |       0.551 |    0.522 |
| [0.6, 0.7)  | 170 |       0.65  |    0.712 |
| [0.7, 1.01) | 158 |       0.779 |    0.772 |

## 3. Spreads: threshold sweep on the tuning window (2019 to 2022)

|   edge |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|-------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|      1 |    702 |    365 |      337 |       16 |     0.52  |    -5.7 | -0.007 |
|      2 |    446 |    232 |      214 |        6 |     0.52  |    -3.4 | -0.007 |
|      3 |    257 |    140 |      117 |        3 |     0.545 |    11.3 |  0.04  |
|      4 |    146 |     85 |       61 |        0 |     0.582 |    17.9 |  0.111 |
|      5 |     68 |     35 |       33 |        0 |     0.515 |    -1.3 | -0.017 |
|      6 |     30 |     16 |       14 |        0 |     0.533 |     0.6 |  0.018 |
|      7 |     14 |      7 |        7 |        0 |     0.5   |    -0.7 | -0.045 |
|      8 |      9 |      5 |        4 |        0 |     0.556 |     0.6 |  0.061 |

## 4. Totals: threshold sweep on the tuning window

|   edge |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|-------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|      1 |    763 |    394 |      369 |        9 |     0.516 |   -11.9 | -0.014 |
|      2 |    489 |    260 |      229 |        4 |     0.532 |     8.1 |  0.015 |
|      3 |    278 |    151 |      127 |        2 |     0.543 |    11.3 |  0.037 |
|      4 |    132 |     74 |       58 |        1 |     0.561 |    10.2 |  0.07  |
|      5 |     68 |     41 |       27 |        1 |     0.603 |    11.3 |  0.151 |
|      6 |     36 |     23 |       13 |        0 |     0.639 |     8.7 |  0.22  |
|      7 |     12 |      8 |        4 |        0 |     0.667 |     3.6 |  0.273 |
|      8 |      6 |      3 |        3 |        0 |     0.5   |    -0.3 | -0.045 |

Best spread threshold with 100+ bets on the tuning window: 4 (ROI +0.111). Best total threshold: 4 (ROI +0.070). The held-out results below use the live flags (5 / 6) and, separately, these.

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
| all |     72 |     45 |       27 |        2 |     0.625 |    15.3 | 0.193 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|------:|
|     2023 |     14 |      9 |        5 |        2 |     0.643 |     3.5 | 0.227 |
|     2024 |     30 |     21 |        9 |        0 |     0.7   |    11.1 | 0.336 |
|     2025 |     28 |     15 |       13 |        0 |     0.536 |     0.7 | 0.023 |

By edge size:

| bucket      |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|:------------|-------:|-------:|---------:|---------:|----------:|--------:|------:|
| [4.0, 5.0)  |     39 |     26 |       13 |        1 |     0.667 |    11.7 | 0.273 |
| [5.0, 6.0)  |     15 |      9 |        6 |        1 |     0.6   |     2.4 | 0.145 |
| [6.0, 8.0)  |     13 |      7 |        6 |        0 |     0.538 |     0.4 | 0.028 |
| [8.0, 99.0) |      5 |      3 |        2 |        0 |     0.6   |     0.8 | 0.145 |

Totals:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
| all |    118 |     61 |       57 |        0 |     0.517 |    -1.7 | -0.013 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|     2023 |     48 |     20 |       28 |        0 |     0.417 |   -10.8 | -0.205 |
|     2024 |     39 |     23 |       16 |        0 |     0.59  |     5.4 |  0.126 |
|     2025 |     31 |     18 |       13 |        0 |     0.581 |     3.7 |  0.109 |

## 6. Market plus model

Blend the model line with the closing line, pred = a x model + (1 - a) x line. Best a on 2019 to 2022 by margin MAE: 0.3.

|   a (model share) |   margin MAE 2019-22 |   margin MAE 2023-25 |   total MAE 2023-25 |
|------------------:|---------------------:|---------------------:|--------------------:|
|               0   |                9.888 |                9.744 |              10.121 |
|               0.1 |                9.88  |                9.739 |              10.115 |
|               0.2 |                9.874 |                9.74  |              10.113 |
|               0.3 |                9.873 |                9.744 |              10.115 |
|               0.4 |                9.88  |                9.752 |              10.121 |
|               0.5 |                9.893 |                9.766 |              10.131 |
|               0.6 |                9.91  |                9.786 |              10.146 |
|               0.7 |                9.933 |                9.811 |              10.167 |
|               0.8 |                9.96  |                9.841 |              10.195 |
|               0.9 |                9.993 |                9.875 |              10.228 |
|               1   |               10.032 |                9.914 |              10.263 |

Bet selection is unchanged by blending (the edge is scaled, not re-ordered), so this only improves the score and the probabilities.

## 7. Closing line value

Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).
