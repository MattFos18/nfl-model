# NFL Model 3.0 backtest

Walk-forward: every week is priced with only games played before it; the points regression is refit before every week on every played game since 2013. Rating parameters, ridge strength and bet thresholds were chosen on 2019 to 2022 only. 2023 to 2025 is the held-out test the tuning never saw.

## 1. Points miss (mean absolute error) against Vegas

Tuning window 2019 to 2022:

| target      |   3.0 |   Vegas close |   games |
|:------------|------:|--------------:|--------:|
| team points |  7.44 |          7.29 |    1055 |
| margin      | 10.16 |          9.89 |    1055 |
| total       | 10.64 |         10.54 |    1055 |

Held-out 2023 to 2025:

| target      |   3.0 |   Vegas close |   games |
|:------------|------:|--------------:|--------:|
| team points |  7.36 |          7.21 |     816 |
| margin      | 10.13 |          9.74 |     816 |
| total       | 10.29 |         10.12 |     816 |

Held-out, Week 5 on:

| target      |   3.0 |   Vegas close |   games |
|:------------|------:|--------------:|--------:|
| team points |  7.37 |          7.19 |     624 |
| margin      | 10.02 |          9.59 |     624 |
| total       | 10.26 |         10.09 |     624 |

## 2. Win probability, 2019 to 2022 (tuning)

Brier score (lower is better): 3.0 0.2227, market moneyline 0.2111.

3.0 calibration:

| bin         |   n |   predicted |   actual |
|:------------|----:|------------:|---------:|
| [0.0, 0.3)  |  44 |       0.243 |    0.227 |
| [0.3, 0.4)  | 108 |       0.357 |    0.269 |
| [0.4, 0.5)  | 189 |       0.455 |    0.423 |
| [0.5, 0.6)  | 286 |       0.551 |    0.451 |
| [0.6, 0.7)  | 249 |       0.648 |    0.655 |
| [0.7, 1.01) | 179 |       0.766 |    0.777 |

## 2. Win probability, 2023 to 2025 (held out)

Brier score (lower is better): 3.0 0.2209, market moneyline 0.2102.

3.0 calibration:

| bin         |   n |   predicted |   actual |
|:------------|----:|------------:|---------:|
| [0.0, 0.3)  |  37 |       0.25  |    0.297 |
| [0.3, 0.4)  |  78 |       0.354 |    0.321 |
| [0.4, 0.5)  | 169 |       0.456 |    0.373 |
| [0.5, 0.6)  | 216 |       0.549 |    0.519 |
| [0.6, 0.7)  | 175 |       0.649 |    0.674 |
| [0.7, 1.01) | 141 |       0.771 |    0.801 |

## 3. Spreads: threshold sweep on the tuning window (2019 to 2022)

|   edge |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|-------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|      1 |    742 |    373 |      369 |       15 |     0.503 |   -32.9 | -0.04  |
|      2 |    474 |    246 |      228 |       10 |     0.519 |    -4.8 | -0.009 |
|      3 |    285 |    145 |      140 |        8 |     0.509 |    -9   | -0.029 |
|      4 |    136 |     75 |       61 |        4 |     0.551 |     7.9 |  0.053 |
|      5 |     74 |     42 |       32 |        2 |     0.568 |     6.8 |  0.084 |
|      6 |     35 |     21 |       14 |        2 |     0.6   |     5.6 |  0.145 |
|      7 |     20 |     12 |        8 |        0 |     0.6   |     3.2 |  0.145 |
|      8 |     14 |      8 |        6 |        0 |     0.571 |     1.4 |  0.091 |

## 4. Totals: threshold sweep on the tuning window

|   edge |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|-------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|      1 |    753 |    383 |      370 |        7 |     0.509 |   -24   | -0.029 |
|      2 |    480 |    252 |      228 |        4 |     0.525 |     1.2 |  0.002 |
|      3 |    272 |    141 |      131 |        2 |     0.518 |    -3.1 | -0.01  |
|      4 |    142 |     81 |       61 |        1 |     0.57  |    13.9 |  0.089 |
|      5 |     79 |     48 |       31 |        0 |     0.608 |    13.9 |  0.16  |
|      6 |     38 |     22 |       16 |        0 |     0.579 |     4.4 |  0.105 |
|      7 |     12 |      7 |        5 |        0 |     0.583 |     1.5 |  0.114 |
|      8 |      4 |      1 |        3 |        0 |     0.25  |    -2.3 | -0.523 |

Best spread threshold with 100+ bets on the tuning window: 4 (ROI +0.053). Best total threshold: 4 (ROI +0.089). The held-out results below use the live flags (5 / 6) and, separately, these.

## 5. Held-out 2023 to 2025, live flags (5 / 6)

Spreads:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|------:|
| all |     42 |     26 |       16 |        1 |     0.619 |     8.4 | 0.182 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|     2023 |      9 |      6 |        3 |        1 |     0.667 |     2.7 |  0.273 |
|     2024 |     18 |     13 |        5 |        0 |     0.722 |     7.5 |  0.379 |
|     2025 |     15 |      7 |        8 |        0 |     0.467 |    -1.8 | -0.109 |

By edge size:

| bucket      |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|:------------|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
| [5.0, 6.0)  |     25 |     18 |        7 |        1 |     0.72  |    10.3 |  0.375 |
| [6.0, 7.0)  |      6 |      4 |        2 |        0 |     0.667 |     1.8 |  0.273 |
| [7.0, 9.0)  |      5 |      1 |        4 |        0 |     0.2   |    -3.4 | -0.618 |
| [9.0, 99.0) |      6 |      3 |        3 |        0 |     0.5   |    -0.3 | -0.045 |

Totals:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|------:|
| all |     17 |      9 |        8 |        0 |     0.529 |     0.2 | 0.011 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|     2023 |      5 |      3 |        2 |        0 |       0.6 |     0.8 |  0.145 |
|     2024 |     10 |      4 |        6 |        0 |       0.4 |    -2.6 | -0.236 |
|     2025 |      2 |      2 |        0 |        0 |       1   |     2   |  0.909 |

## 5. Held-out 2023 to 2025, tuned (4 / 4)

Spreads:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|------:|
| all |     93 |     51 |       42 |        2 |     0.548 |     4.8 | 0.047 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|------:|
|     2023 |     33 |     18 |       15 |        2 |     0.545 |     1.5 | 0.041 |
|     2024 |     31 |     17 |       14 |        0 |     0.548 |     1.6 | 0.047 |
|     2025 |     29 |     16 |       13 |        0 |     0.552 |     1.7 | 0.053 |

By edge size:

| bucket      |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|:------------|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
| [4.0, 5.0)  |     51 |     25 |       26 |        1 |     0.49  |    -3.6 | -0.064 |
| [5.0, 6.0)  |     25 |     18 |        7 |        1 |     0.72  |    10.3 |  0.375 |
| [6.0, 8.0)  |      8 |      4 |        4 |        0 |     0.5   |    -0.4 | -0.045 |
| [8.0, 99.0) |      9 |      4 |        5 |        0 |     0.444 |    -1.5 | -0.152 |

Totals:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
| all |    116 |     60 |       56 |        1 |     0.517 |    -1.6 | -0.013 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|     2023 |     51 |     23 |       28 |        1 |     0.451 |    -7.8 | -0.139 |
|     2024 |     39 |     23 |       16 |        0 |     0.59  |     5.4 |  0.126 |
|     2025 |     26 |     14 |       12 |        0 |     0.538 |     0.8 |  0.028 |

## 6. Market plus model

Blend the model line with the closing line, pred = a x model + (1 - a) x line. Best a on 2019 to 2022 by margin MAE: 0.1.

|   a (model share) |   margin MAE 2019-22 |   margin MAE 2023-25 |   total MAE 2023-25 |
|------------------:|---------------------:|---------------------:|--------------------:|
|               0   |                9.888 |                9.744 |              10.121 |
|               0.1 |                9.887 |                9.752 |              10.119 |
|               0.2 |                9.892 |                9.77  |              10.122 |
|               0.3 |                9.903 |                9.797 |              10.127 |
|               0.4 |                9.927 |                9.832 |              10.138 |
|               0.5 |                9.957 |                9.873 |              10.152 |
|               0.6 |                9.99  |                9.918 |              10.172 |
|               0.7 |               10.027 |                9.967 |              10.195 |
|               0.8 |               10.067 |               10.018 |              10.222 |
|               0.9 |               10.112 |               10.072 |              10.254 |
|               1   |               10.16  |               10.131 |              10.29  |

Bet selection is unchanged by blending (the edge is scaled, not re-ordered), so this only improves the score and the probabilities.

## 7. Closing line value

Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).
