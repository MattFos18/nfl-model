# NFL Model 3.0 backtest

Walk-forward: every week is priced with only games played before it; the points regression is refit before every week on every played game since 2013. Rating parameters, ridge strength and bet thresholds were chosen on 2019 to 2022 only. 2023 to 2025 is the held-out test the tuning never saw.

## 1. Points miss (mean absolute error) against Vegas

Tuning window 2019 to 2022:

| target      |   3.0 |   Vegas close |   games |
|:------------|------:|--------------:|--------:|
| team points |  7.45 |          7.29 |    1055 |
| margin      | 10.16 |          9.89 |    1055 |
| total       | 10.71 |         10.54 |    1055 |

Held-out 2023 to 2025:

| target      |   3.0 |   Vegas close |   games |
|:------------|------:|--------------:|--------:|
| team points |  7.37 |          7.21 |     816 |
| margin      | 10.13 |          9.74 |     816 |
| total       | 10.37 |         10.12 |     816 |

Held-out, Week 5 on:

| target      |   3.0 |   Vegas close |   games |
|:------------|------:|--------------:|--------:|
| team points |  7.38 |          7.19 |     624 |
| margin      | 10.02 |          9.59 |     624 |
| total       | 10.36 |         10.09 |     624 |

## 2. Win probability, 2019 to 2022 (tuning)

Brier score (lower is better): 3.0 0.2227, market moneyline 0.2111.

3.0 calibration:

| bin         |   n |   predicted |   actual |
|:------------|----:|------------:|---------:|
| [0.0, 0.3)  |  44 |       0.242 |    0.227 |
| [0.3, 0.4)  | 108 |       0.357 |    0.269 |
| [0.4, 0.5)  | 190 |       0.455 |    0.421 |
| [0.5, 0.6)  | 285 |       0.551 |    0.456 |
| [0.6, 0.7)  | 250 |       0.648 |    0.648 |
| [0.7, 1.01) | 178 |       0.767 |    0.781 |

## 2. Win probability, 2023 to 2025 (held out)

Brier score (lower is better): 3.0 0.2209, market moneyline 0.2102.

3.0 calibration:

| bin         |   n |   predicted |   actual |
|:------------|----:|------------:|---------:|
| [0.0, 0.3)  |  39 |       0.252 |    0.282 |
| [0.3, 0.4)  |  76 |       0.355 |    0.329 |
| [0.4, 0.5)  | 168 |       0.456 |    0.369 |
| [0.5, 0.6)  | 216 |       0.549 |    0.523 |
| [0.6, 0.7)  | 176 |       0.649 |    0.67  |
| [0.7, 1.01) | 141 |       0.772 |    0.801 |

## 3. Spreads: threshold sweep on the tuning window (2019 to 2022)

|   edge |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|-------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|      1 |    739 |    370 |      369 |       15 |     0.501 |   -35.9 | -0.044 |
|      2 |    471 |    246 |      225 |       10 |     0.522 |    -1.5 | -0.003 |
|      3 |    282 |    145 |      137 |        8 |     0.514 |    -5.7 | -0.018 |
|      4 |    137 |     76 |       61 |        4 |     0.555 |     8.9 |  0.059 |
|      5 |     74 |     42 |       32 |        2 |     0.568 |     6.8 |  0.084 |
|      6 |     35 |     21 |       14 |        2 |     0.6   |     5.6 |  0.145 |
|      7 |     20 |     12 |        8 |        0 |     0.6   |     3.2 |  0.145 |
|      8 |     14 |      8 |        6 |        0 |     0.571 |     1.4 |  0.091 |

## 4. Totals: threshold sweep on the tuning window

|   edge |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|-------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|      1 |    771 |    391 |      380 |        9 |     0.507 |   -27   | -0.032 |
|      2 |    475 |    250 |      225 |        6 |     0.526 |     2.5 |  0.005 |
|      3 |    288 |    151 |      137 |        2 |     0.524 |     0.3 |  0.001 |
|      4 |    159 |     89 |       70 |        2 |     0.56  |    12   |  0.069 |
|      5 |     74 |     40 |       34 |        1 |     0.541 |     2.6 |  0.032 |
|      6 |     30 |     16 |       14 |        0 |     0.533 |     0.6 |  0.018 |
|      7 |     14 |      9 |        5 |        0 |     0.643 |     3.5 |  0.227 |
|      8 |      5 |      4 |        1 |        0 |     0.8   |     2.9 |  0.527 |

Best spread threshold with 100+ bets on the tuning window: 4 (ROI +0.059). Best total threshold: 4 (ROI +0.069). The held-out results below use the live flags (5 / 6) and, separately, these.

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
| all |     18 |     10 |        8 |        0 |     0.556 |     1.2 | 0.061 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|     2023 |      4 |      1 |        3 |        0 |     0.25  |    -2.3 | -0.523 |
|     2024 |     11 |      6 |        5 |        0 |     0.545 |     0.5 |  0.041 |
|     2025 |      3 |      3 |        0 |        0 |     1     |     3   |  0.909 |

## 5. Held-out 2023 to 2025, tuned (4 / 4)

Spreads:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|------:|
| all |     93 |     52 |       41 |        2 |     0.559 |     6.9 | 0.067 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|------:|
|     2023 |     33 |     19 |       14 |        2 |     0.576 |     3.6 | 0.099 |
|     2024 |     31 |     17 |       14 |        0 |     0.548 |     1.6 | 0.047 |
|     2025 |     29 |     16 |       13 |        0 |     0.552 |     1.7 | 0.053 |

By edge size:

| bucket      |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|:------------|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
| [4.0, 5.0)  |     51 |     26 |       25 |        1 |     0.51  |    -1.5 | -0.027 |
| [5.0, 6.0)  |     25 |     18 |        7 |        1 |     0.72  |    10.3 |  0.375 |
| [6.0, 8.0)  |      8 |      4 |        4 |        0 |     0.5   |    -0.4 | -0.045 |
| [8.0, 99.0) |      9 |      4 |        5 |        0 |     0.444 |    -1.5 | -0.152 |

Totals:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
| all |    101 |     46 |       55 |        2 |     0.455 |   -14.5 | -0.131 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|     2023 |     36 |     15 |       21 |        1 |     0.417 |    -8.1 | -0.205 |
|     2024 |     40 |     18 |       22 |        1 |     0.45  |    -6.2 | -0.141 |
|     2025 |     25 |     13 |       12 |        0 |     0.52  |    -0.2 | -0.007 |

## 6. Market plus model

Blend the model line with the closing line, pred = a x model + (1 - a) x line. Best a on 2019 to 2022 by margin MAE: 0.1.

|   a (model share) |   margin MAE 2019-22 |   margin MAE 2023-25 |   total MAE 2023-25 |
|------------------:|---------------------:|---------------------:|--------------------:|
|               0   |                9.888 |                9.744 |              10.121 |
|               0.1 |                9.887 |                9.752 |              10.127 |
|               0.2 |                9.892 |                9.77  |              10.137 |
|               0.3 |                9.903 |                9.797 |              10.151 |
|               0.4 |                9.927 |                9.832 |              10.17  |
|               0.5 |                9.957 |                9.873 |              10.194 |
|               0.6 |                9.99  |                9.918 |              10.221 |
|               0.7 |               10.027 |                9.966 |              10.253 |
|               0.8 |               10.067 |               10.018 |              10.29  |
|               0.9 |               10.111 |               10.072 |              10.33  |
|               1   |               10.16  |               10.131 |              10.373 |

Bet selection is unchanged by blending (the edge is scaled, not re-ordered), so this only improves the score and the probabilities.

## 7. Closing line value

Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).
