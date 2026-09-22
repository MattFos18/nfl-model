# NFL Model 3.0 backtest

Walk-forward: every week is priced with only games played before it; the points regression is refit before every week on every played game since 2013. Rating parameters, ridge strength and bet thresholds were chosen on 2019 to 2022 only. 2023 to 2025 is the held-out test the tuning never saw.

## 1. Points miss (mean absolute error) against Vegas

Tuning window 2019 to 2022:

| target      |   3.0 |   Vegas close |   games |
|:------------|------:|--------------:|--------:|
| team points |  7.42 |          7.29 |    1055 |
| margin      | 10.11 |          9.89 |    1055 |
| total       | 10.62 |         10.54 |    1055 |

Held-out 2023 to 2025:

| target      |   3.0 |   Vegas close |   games |
|:------------|------:|--------------:|--------:|
| team points |  7.33 |          7.21 |     816 |
| margin      | 10.07 |          9.74 |     816 |
| total       | 10.3  |         10.12 |     816 |

Held-out, Week 5 on:

| target      |   3.0 |   Vegas close |   games |
|:------------|------:|--------------:|--------:|
| team points |  7.35 |          7.19 |     624 |
| margin      |  9.96 |          9.59 |     624 |
| total       | 10.27 |         10.09 |     624 |

## 2. Win probability, 2019 to 2022 (tuning)

Brier score (lower is better): 3.0 0.2214, market moneyline 0.2111.

3.0 calibration:

| bin         |   n |   predicted |   actual |
|:------------|----:|------------:|---------:|
| [0.0, 0.3)  |  49 |       0.247 |    0.265 |
| [0.3, 0.4)  | 101 |       0.355 |    0.267 |
| [0.4, 0.5)  | 200 |       0.453 |    0.395 |
| [0.5, 0.6)  | 282 |       0.551 |    0.457 |
| [0.6, 0.7)  | 226 |       0.648 |    0.642 |
| [0.7, 1.01) | 197 |       0.767 |    0.797 |

## 2. Win probability, 2023 to 2025 (held out)

Brier score (lower is better): 3.0 0.2199, market moneyline 0.2102.

3.0 calibration:

| bin         |   n |   predicted |   actual |
|:------------|----:|------------:|---------:|
| [0.0, 0.3)  |  37 |       0.244 |    0.297 |
| [0.3, 0.4)  |  78 |       0.352 |    0.333 |
| [0.4, 0.5)  | 173 |       0.454 |    0.387 |
| [0.5, 0.6)  | 218 |       0.552 |    0.505 |
| [0.6, 0.7)  | 157 |       0.648 |    0.675 |
| [0.7, 1.01) | 153 |       0.77  |    0.797 |

## 3. Spreads: threshold sweep on the tuning window (2019 to 2022)

|   edge |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|-------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|      1 |    720 |    366 |      354 |       15 |     0.508 |   -23.4 | -0.03  |
|      2 |    469 |    247 |      222 |        8 |     0.527 |     2.8 |  0.005 |
|      3 |    286 |    152 |      134 |        6 |     0.531 |     4.6 |  0.015 |
|      4 |    165 |     92 |       73 |        3 |     0.558 |    11.7 |  0.064 |
|      5 |     77 |     42 |       35 |        0 |     0.545 |     3.5 |  0.041 |
|      6 |     33 |     19 |       14 |        0 |     0.576 |     3.6 |  0.099 |
|      7 |     23 |     13 |       10 |        0 |     0.565 |     2   |  0.079 |
|      8 |     14 |      8 |        6 |        0 |     0.571 |     1.4 |  0.091 |

## 4. Totals: threshold sweep on the tuning window

|   edge |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|-------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|      1 |    752 |    383 |      369 |        7 |     0.509 |   -22.9 | -0.028 |
|      2 |    482 |    256 |      226 |        5 |     0.531 |     7.4 |  0.014 |
|      3 |    280 |    148 |      132 |        2 |     0.529 |     2.8 |  0.009 |
|      4 |    141 |     82 |       59 |        1 |     0.582 |    17.1 |  0.11  |
|      5 |     72 |     44 |       28 |        0 |     0.611 |    13.2 |  0.167 |
|      6 |     37 |     22 |       15 |        0 |     0.595 |     5.5 |  0.135 |
|      7 |     12 |      8 |        4 |        0 |     0.667 |     3.6 |  0.273 |
|      8 |      4 |      1 |        3 |        0 |     0.25  |    -2.3 | -0.523 |

Best spread threshold with 100+ bets on the tuning window: 4 (ROI +0.064). Best total threshold: 4 (ROI +0.110). The held-out results below use the live flags (5 / 6) and, separately, these.

## 5. Held-out 2023 to 2025, live flags (5 / 6)

Spreads:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|------:|
| all |     47 |     28 |       19 |        2 |     0.596 |     7.1 | 0.137 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|     2023 |     11 |      7 |        4 |        2 |     0.636 |     2.6 |  0.215 |
|     2024 |     21 |     14 |        7 |        0 |     0.667 |     6.3 |  0.273 |
|     2025 |     15 |      7 |        8 |        0 |     0.467 |    -1.8 | -0.109 |

By edge size:

| bucket      |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|:------------|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
| [5.0, 6.0)  |     26 |     17 |        9 |        2 |     0.654 |     7.1 |  0.248 |
| [6.0, 7.0)  |     10 |      5 |        5 |        0 |     0.5   |    -0.5 | -0.045 |
| [7.0, 9.0)  |      8 |      5 |        3 |        0 |     0.625 |     1.7 |  0.193 |
| [9.0, 99.0) |      3 |      1 |        2 |        0 |     0.333 |    -1.2 | -0.364 |

Totals:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|------:|
| all |     18 |     10 |        8 |        0 |     0.556 |     1.2 | 0.061 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|     2023 |      5 |      3 |        2 |        0 |       0.6 |     0.8 |  0.145 |
|     2024 |     10 |      4 |        6 |        0 |       0.4 |    -2.6 | -0.236 |
|     2025 |      3 |      3 |        0 |        0 |       1   |     3   |  0.909 |

## 5. Held-out 2023 to 2025, tuned (4 / 4)

Spreads:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|------:|
| all |     97 |     58 |       39 |        2 |     0.598 |    15.1 | 0.142 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|------:|
|     2023 |     30 |     16 |       14 |        2 |     0.533 |     0.6 | 0.018 |
|     2024 |     38 |     24 |       14 |        0 |     0.632 |     8.6 | 0.206 |
|     2025 |     29 |     18 |       11 |        0 |     0.621 |     5.9 | 0.185 |

By edge size:

| bucket      |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|:------------|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
| [4.0, 5.0)  |     50 |     30 |       20 |        0 |     0.6   |     8   |  0.145 |
| [5.0, 6.0)  |     26 |     17 |        9 |        2 |     0.654 |     7.1 |  0.248 |
| [6.0, 8.0)  |     17 |      9 |        8 |        0 |     0.529 |     0.2 |  0.011 |
| [8.0, 99.0) |      4 |      2 |        2 |        0 |     0.5   |    -0.2 | -0.045 |

Totals:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
| all |    121 |     61 |       60 |        1 |     0.504 |      -5 | -0.038 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|     2023 |     56 |     24 |       32 |        1 |     0.429 |   -11.2 | -0.182 |
|     2024 |     40 |     24 |       16 |        0 |     0.6   |     6.4 |  0.145 |
|     2025 |     25 |     13 |       12 |        0 |     0.52  |    -0.2 | -0.007 |

## 6. Market plus model

Blend the model line with the closing line, pred = a x model + (1 - a) x line. Best a on 2019 to 2022 by margin MAE: 0.2.

|   a (model share) |   margin MAE 2019-22 |   margin MAE 2023-25 |   total MAE 2023-25 |
|------------------:|---------------------:|---------------------:|--------------------:|
|               0   |                9.888 |                9.744 |              10.121 |
|               0.1 |                9.882 |                9.748 |              10.119 |
|               0.2 |                9.881 |                9.761 |              10.122 |
|               0.3 |                9.888 |                9.781 |              10.128 |
|               0.4 |                9.906 |                9.809 |              10.139 |
|               0.5 |                9.931 |                9.84  |              10.153 |
|               0.6 |                9.96  |                9.878 |              10.173 |
|               0.7 |                9.991 |                9.921 |              10.197 |
|               0.8 |               10.024 |                9.968 |              10.225 |
|               0.9 |               10.064 |               10.018 |              10.259 |
|               1   |               10.109 |               10.072 |              10.296 |

Bet selection is unchanged by blending (the edge is scaled, not re-ordered), so this only improves the score and the probabilities.

## 7. Closing line value

Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).
