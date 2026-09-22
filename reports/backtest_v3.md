# NFL Model 3.0 backtest

Walk-forward: every week is priced with only games played before it; the points regression is refit before every week on every played game since 2013. Rating parameters, ridge strength and bet thresholds were chosen on 2019 to 2022 only. 2023 to 2025 is the held-out test the tuning never saw.

## 1. Points miss (mean absolute error) against Vegas

Tuning window 2019 to 2022:

| target      |   3.0 |   Vegas close |   games |
|:------------|------:|--------------:|--------:|
| team points |  7.42 |          7.29 |    1055 |
| margin      | 10.13 |          9.89 |    1055 |
| total       | 10.64 |         10.54 |    1055 |

Held-out 2023 to 2025:

| target      |   3.0 |   Vegas close |   games |
|:------------|------:|--------------:|--------:|
| team points |  7.34 |          7.21 |     816 |
| margin      | 10.1  |          9.74 |     816 |
| total       | 10.29 |         10.12 |     816 |

Held-out, Week 5 on:

| target      |   3.0 |   Vegas close |   games |
|:------------|------:|--------------:|--------:|
| team points |  7.35 |          7.19 |     624 |
| margin      |  9.99 |          9.59 |     624 |
| total       | 10.26 |         10.09 |     624 |

## 2. Win probability, 2019 to 2022 (tuning)

Brier score (lower is better): 3.0 0.2219, market moneyline 0.2111.

3.0 calibration:

| bin         |   n |   predicted |   actual |
|:------------|----:|------------:|---------:|
| [0.0, 0.3)  |  47 |       0.245 |    0.234 |
| [0.3, 0.4)  | 107 |       0.358 |    0.252 |
| [0.4, 0.5)  | 189 |       0.457 |    0.413 |
| [0.5, 0.6)  | 288 |       0.552 |    0.458 |
| [0.6, 0.7)  | 231 |       0.645 |    0.654 |
| [0.7, 1.01) | 193 |       0.765 |    0.782 |

## 2. Win probability, 2023 to 2025 (held out)

Brier score (lower is better): 3.0 0.2199, market moneyline 0.2102.

3.0 calibration:

| bin         |   n |   predicted |   actual |
|:------------|----:|------------:|---------:|
| [0.0, 0.3)  |  38 |       0.249 |    0.289 |
| [0.3, 0.4)  |  76 |       0.357 |    0.342 |
| [0.4, 0.5)  | 172 |       0.456 |    0.36  |
| [0.5, 0.6)  | 211 |       0.549 |    0.531 |
| [0.6, 0.7)  | 173 |       0.648 |    0.653 |
| [0.7, 1.01) | 146 |       0.77  |    0.808 |

## 3. Spreads: threshold sweep on the tuning window (2019 to 2022)

|   edge |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|-------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|      1 |    738 |    375 |      363 |       13 |     0.508 |   -24.3 | -0.03  |
|      2 |    477 |    254 |      223 |        9 |     0.532 |     8.7 |  0.017 |
|      3 |    288 |    149 |      139 |        7 |     0.517 |    -3.9 | -0.012 |
|      4 |    151 |     83 |       68 |        5 |     0.55  |     8.2 |  0.049 |
|      5 |     71 |     42 |       29 |        1 |     0.592 |    10.1 |  0.129 |
|      6 |     35 |     22 |       13 |        0 |     0.629 |     7.7 |  0.2   |
|      7 |     23 |     13 |       10 |        0 |     0.565 |     2   |  0.079 |
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

Best spread threshold with 100+ bets on the tuning window: 4 (ROI +0.049). Best total threshold: 4 (ROI +0.089). The held-out results below use the live flags (5 / 6) and, separately, these.

## 5. Held-out 2023 to 2025, live flags (5 / 6)

Spreads:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|------:|
| all |     41 |     25 |       16 |        1 |      0.61 |     7.4 | 0.164 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|     2023 |     10 |      6 |        4 |        1 |     0.6   |     1.6 |  0.145 |
|     2024 |     16 |     12 |        4 |        0 |     0.75  |     7.6 |  0.432 |
|     2025 |     15 |      7 |        8 |        0 |     0.467 |    -1.8 | -0.109 |

By edge size:

| bucket      |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|:------------|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
| [5.0, 6.0)  |     26 |     18 |        8 |        1 |     0.692 |     9.2 |  0.322 |
| [6.0, 7.0)  |      6 |      4 |        2 |        0 |     0.667 |     1.8 |  0.273 |
| [7.0, 9.0)  |      6 |      2 |        4 |        0 |     0.333 |    -2.4 | -0.364 |
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
| all |    102 |     58 |       44 |        2 |     0.569 |     9.6 | 0.086 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|------:|
|     2023 |     35 |     20 |       15 |        2 |     0.571 |     3.5 | 0.091 |
|     2024 |     32 |     18 |       14 |        0 |     0.562 |     2.6 | 0.074 |
|     2025 |     35 |     20 |       15 |        0 |     0.571 |     3.5 | 0.091 |

By edge size:

| bucket      |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|:------------|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
| [4.0, 5.0)  |     61 |     33 |       28 |        1 |     0.541 |     2.2 |  0.033 |
| [5.0, 6.0)  |     26 |     18 |        8 |        1 |     0.692 |     9.2 |  0.322 |
| [6.0, 8.0)  |      9 |      5 |        4 |        0 |     0.556 |     0.6 |  0.061 |
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
|               0.1 |                9.884 |                9.752 |              10.119 |
|               0.2 |                9.885 |                9.77  |              10.122 |
|               0.3 |                9.893 |                9.795 |              10.127 |
|               0.4 |                9.914 |                9.827 |              10.138 |
|               0.5 |                9.94  |                9.863 |              10.152 |
|               0.6 |                9.97  |                9.902 |              10.172 |
|               0.7 |               10.004 |                9.947 |              10.195 |
|               0.8 |               10.041 |                9.995 |              10.222 |
|               0.9 |               10.082 |               10.045 |              10.254 |
|               1   |               10.128 |               10.102 |              10.29  |

Bet selection is unchanged by blending (the edge is scaled, not re-ordered), so this only improves the score and the probabilities.

## 7. Closing line value

Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).
