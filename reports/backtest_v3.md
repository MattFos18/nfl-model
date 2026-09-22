# NFL Model 3.0 backtest

Walk-forward: every week is priced with only games played before it; the points regression is refit before every week on every played game since 2013. Rating parameters, ridge strength and bet thresholds were chosen on 2019 to 2022 only. 2023 to 2025 is the held-out test the tuning never saw.

## 1. Points miss (mean absolute error) against Vegas

Tuning window 2019 to 2022:

| target      |   3.0 |   Vegas close |   games |
|:------------|------:|--------------:|--------:|
| team points |  7.44 |          7.29 |    1055 |
| margin      | 10.15 |          9.89 |    1055 |
| total       | 10.64 |         10.54 |    1055 |

Held-out 2023 to 2025:

| target      |   3.0 |   Vegas close |   games |
|:------------|------:|--------------:|--------:|
| team points |  7.35 |          7.21 |     816 |
| margin      | 10.12 |          9.74 |     816 |
| total       | 10.29 |         10.12 |     816 |

Held-out, Week 5 on:

| target      |   3.0 |   Vegas close |   games |
|:------------|------:|--------------:|--------:|
| team points |  7.36 |          7.19 |     624 |
| margin      | 10    |          9.59 |     624 |
| total       | 10.26 |         10.09 |     624 |

## 2. Win probability, 2019 to 2022 (tuning)

Brier score (lower is better): 3.0 0.2225, market moneyline 0.2111.

3.0 calibration:

| bin         |   n |   predicted |   actual |
|:------------|----:|------------:|---------:|
| [0.0, 0.3)  |  43 |       0.242 |    0.233 |
| [0.3, 0.4)  | 109 |       0.356 |    0.266 |
| [0.4, 0.5)  | 190 |       0.455 |    0.416 |
| [0.5, 0.6)  | 291 |       0.552 |    0.464 |
| [0.6, 0.7)  | 242 |       0.649 |    0.64  |
| [0.7, 1.01) | 180 |       0.767 |    0.789 |

## 2. Win probability, 2023 to 2025 (held out)

Brier score (lower is better): 3.0 0.2208, market moneyline 0.2102.

3.0 calibration:

| bin         |   n |   predicted |   actual |
|:------------|----:|------------:|---------:|
| [0.0, 0.3)  |  40 |       0.254 |    0.3   |
| [0.3, 0.4)  |  76 |       0.356 |    0.316 |
| [0.4, 0.5)  | 169 |       0.456 |    0.367 |
| [0.5, 0.6)  | 215 |       0.549 |    0.526 |
| [0.6, 0.7)  | 173 |       0.648 |    0.676 |
| [0.7, 1.01) | 143 |       0.77  |    0.797 |

## 3. Spreads: threshold sweep on the tuning window (2019 to 2022)

|   edge |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|-------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|      1 |    735 |    369 |      366 |       15 |     0.502 |   -33.6 | -0.042 |
|      2 |    471 |    249 |      222 |        9 |     0.529 |     4.8 |  0.009 |
|      3 |    290 |    149 |      141 |        7 |     0.514 |    -6.1 | -0.019 |
|      4 |    136 |     75 |       61 |        4 |     0.551 |     7.9 |  0.053 |
|      5 |     73 |     41 |       32 |        2 |     0.562 |     5.8 |  0.072 |
|      6 |     35 |     20 |       15 |        2 |     0.571 |     3.5 |  0.091 |
|      7 |     21 |     12 |        9 |        0 |     0.571 |     2.1 |  0.091 |
|      8 |     15 |      8 |        7 |        0 |     0.533 |     0.3 |  0.018 |

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
| all |     42 |     25 |       17 |        1 |     0.595 |     6.3 | 0.136 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|     2023 |      9 |      6 |        3 |        1 |     0.667 |     2.7 |  0.273 |
|     2024 |     18 |     12 |        6 |        0 |     0.667 |     5.4 |  0.273 |
|     2025 |     15 |      7 |        8 |        0 |     0.467 |    -1.8 | -0.109 |

By edge size:

| bucket      |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|:------------|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
| [5.0, 6.0)  |     24 |     17 |        7 |        1 |     0.708 |     9.3 |  0.352 |
| [6.0, 7.0)  |      7 |      4 |        3 |        0 |     0.571 |     0.7 |  0.091 |
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
| all |     96 |     53 |       43 |        2 |     0.552 |     5.7 | 0.054 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|------:|
|     2023 |     34 |     18 |       16 |        2 |     0.529 |     0.4 | 0.011 |
|     2024 |     32 |     18 |       14 |        0 |     0.562 |     2.6 | 0.074 |
|     2025 |     30 |     17 |       13 |        0 |     0.567 |     2.7 | 0.082 |

By edge size:

| bucket      |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|:------------|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
| [4.0, 5.0)  |     54 |     28 |       26 |        1 |     0.519 |    -0.6 | -0.01  |
| [5.0, 6.0)  |     24 |     17 |        7 |        1 |     0.708 |     9.3 |  0.352 |
| [6.0, 8.0)  |      9 |      4 |        5 |        0 |     0.444 |    -1.5 | -0.152 |
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
|               0.1 |                9.887 |                9.751 |              10.119 |
|               0.2 |                9.89  |                9.768 |              10.122 |
|               0.3 |                9.901 |                9.793 |              10.127 |
|               0.4 |                9.924 |                9.827 |              10.138 |
|               0.5 |                9.953 |                9.867 |              10.152 |
|               0.6 |                9.985 |                9.91  |              10.172 |
|               0.7 |               10.021 |                9.957 |              10.195 |
|               0.8 |               10.061 |               10.008 |              10.222 |
|               0.9 |               10.104 |               10.06  |              10.254 |
|               1   |               10.152 |               10.117 |              10.29  |

Bet selection is unchanged by blending (the edge is scaled, not re-ordered), so this only improves the score and the probabilities.

## 7. Closing line value

Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).
