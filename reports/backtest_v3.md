# NFL Model 3.0 backtest

Walk-forward: every week is priced with only games played before it; the points regression is refit before every week on every played game since 2013. Rating parameters, ridge strength and bet thresholds were chosen on 2019 to 2022 only. 2023 to 2025 is the held-out test the tuning never saw.

## 1. Points miss (mean absolute error) against Vegas

Tuning window 2019 to 2022:

| target      |   3.0 |   Vegas close |   games |
|:------------|------:|--------------:|--------:|
| team points |  7.43 |          7.29 |    1055 |
| margin      | 10.14 |          9.89 |    1055 |
| total       | 10.64 |         10.54 |    1055 |

Held-out 2023 to 2025:

| target      |   3.0 |   Vegas close |   games |
|:------------|------:|--------------:|--------:|
| team points |  7.34 |          7.21 |     816 |
| margin      | 10.11 |          9.74 |     816 |
| total       | 10.29 |         10.12 |     816 |

Held-out, Week 5 on:

| target      |   3.0 |   Vegas close |   games |
|:------------|------:|--------------:|--------:|
| team points |  7.35 |          7.19 |     624 |
| margin      | 10    |          9.59 |     624 |
| total       | 10.26 |         10.09 |     624 |

## 2. Win probability, 2019 to 2022 (tuning)

Brier score (lower is better): 3.0 0.2224, market moneyline 0.2111.

3.0 calibration:

| bin         |   n |   predicted |   actual |
|:------------|----:|------------:|---------:|
| [0.0, 0.3)  |  45 |       0.244 |    0.267 |
| [0.3, 0.4)  | 104 |       0.357 |    0.25  |
| [0.4, 0.5)  | 192 |       0.455 |    0.401 |
| [0.5, 0.6)  | 292 |       0.552 |    0.466 |
| [0.6, 0.7)  | 237 |       0.647 |    0.658 |
| [0.7, 1.01) | 185 |       0.766 |    0.773 |

## 2. Win probability, 2023 to 2025 (held out)

Brier score (lower is better): 3.0 0.2200, market moneyline 0.2102.

3.0 calibration:

| bin         |   n |   predicted |   actual |
|:------------|----:|------------:|---------:|
| [0.0, 0.3)  |  37 |       0.248 |    0.297 |
| [0.3, 0.4)  |  76 |       0.355 |    0.303 |
| [0.4, 0.5)  | 172 |       0.455 |    0.372 |
| [0.5, 0.6)  | 211 |       0.548 |    0.526 |
| [0.6, 0.7)  | 176 |       0.647 |    0.665 |
| [0.7, 1.01) | 144 |       0.771 |    0.806 |

## 3. Spreads: threshold sweep on the tuning window (2019 to 2022)

|   edge |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|-------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|      1 |    742 |    372 |      370 |       13 |     0.501 |   -35   | -0.043 |
|      2 |    477 |    248 |      229 |        9 |     0.52  |    -3.9 | -0.007 |
|      3 |    289 |    148 |      141 |        7 |     0.512 |    -7.1 | -0.022 |
|      4 |    146 |     80 |       66 |        5 |     0.548 |     7.4 |  0.046 |
|      5 |     72 |     40 |       32 |        1 |     0.556 |     4.8 |  0.061 |
|      6 |     35 |     22 |       13 |        1 |     0.629 |     7.7 |  0.2   |
|      7 |     21 |     12 |        9 |        0 |     0.571 |     2.1 |  0.091 |
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

Best spread threshold with 100+ bets on the tuning window: 4 (ROI +0.046). Best total threshold: 4 (ROI +0.089). The held-out results below use the live flags (5 / 6) and, separately, these.

## 5. Held-out 2023 to 2025, live flags (5 / 6)

Spreads:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|------:|
| all |     43 |     26 |       17 |        1 |     0.605 |     7.3 | 0.154 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|     2023 |     11 |      6 |        5 |        1 |     0.545 |     0.5 |  0.041 |
|     2024 |     16 |     12 |        4 |        0 |     0.75  |     7.6 |  0.432 |
|     2025 |     16 |      8 |        8 |        0 |     0.5   |    -0.8 | -0.045 |

By edge size:

| bucket      |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|:------------|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
| [5.0, 6.0)  |     27 |     19 |        8 |        1 |     0.704 |    10.2 |  0.343 |
| [6.0, 7.0)  |      9 |      5 |        4 |        0 |     0.556 |     0.6 |  0.061 |
| [7.0, 9.0)  |      4 |      1 |        3 |        0 |     0.25  |    -2.3 | -0.523 |
| [9.0, 99.0) |      3 |      1 |        2 |        0 |     0.333 |    -1.2 | -0.364 |

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
| all |     96 |     51 |       45 |        2 |     0.531 |     1.5 | 0.014 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|     2023 |     34 |     18 |       16 |        2 |     0.529 |     0.4 |  0.011 |
|     2024 |     31 |     17 |       14 |        0 |     0.548 |     1.6 |  0.047 |
|     2025 |     31 |     16 |       15 |        0 |     0.516 |    -0.5 | -0.015 |

By edge size:

| bucket      |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|:------------|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
| [4.0, 5.0)  |     53 |     25 |       28 |        1 |     0.472 |    -5.8 | -0.099 |
| [5.0, 6.0)  |     27 |     19 |        8 |        1 |     0.704 |    10.2 |  0.343 |
| [6.0, 8.0)  |     10 |      5 |        5 |        0 |     0.5   |    -0.5 | -0.045 |
| [8.0, 99.0) |      6 |      2 |        4 |        0 |     0.333 |    -2.4 | -0.364 |

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
|               0.1 |                9.886 |                9.753 |              10.119 |
|               0.2 |                9.889 |                9.772 |              10.122 |
|               0.3 |                9.899 |                9.797 |              10.127 |
|               0.4 |                9.92  |                9.83  |              10.138 |
|               0.5 |                9.949 |                9.865 |              10.152 |
|               0.6 |                9.979 |                9.906 |              10.172 |
|               0.7 |               10.015 |                9.95  |              10.195 |
|               0.8 |               10.053 |                9.998 |              10.222 |
|               0.9 |               10.095 |               10.049 |              10.254 |
|               1   |               10.143 |               10.106 |              10.29  |

Bet selection is unchanged by blending (the edge is scaled, not re-ordered), so this only improves the score and the probabilities.

## 7. Closing line value

Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).
