# NFL Model 3.0 backtest

Walk-forward: every week is priced with only games played before it; the points regression is refit before every week on every played game since 2013. Ridge strength and bet thresholds were chosen on 2019 to 2022 only, and 2023 to 2025 was the held-out test for them. Since 22 Sep 2026 every new input, and the rating decay and last-season weight, is accepted only when it helps on both windows, so for those choices 2023 to 2025 is a second test window rather than an untouched one; the live season is the only fully unseen test.

## 1. Points miss (mean absolute error) against Vegas

Tuning window 2019 to 2022:

| target      |   3.0 |   Vegas close |   games |
|:------------|------:|--------------:|--------:|
| team points |  7.36 |          7.29 |    1055 |
| margin      | 10.03 |          9.89 |    1055 |
| total       | 10.62 |         10.54 |    1055 |

Held-out 2023 to 2025:

| target      |   3.0 |   Vegas close |   games |
|:------------|------:|--------------:|--------:|
| team points |  7.29 |          7.21 |     816 |
| margin      |  9.95 |          9.74 |     816 |
| total       | 10.26 |         10.12 |     816 |

Held-out, Week 5 on:

| target      |   3.0 |   Vegas close |   games |
|:------------|------:|--------------:|--------:|
| team points |  7.32 |          7.19 |     624 |
| margin      |  9.86 |          9.59 |     624 |
| total       | 10.25 |         10.09 |     624 |

## 2. Win probability, 2019 to 2022 (tuning)

Brier score (lower is better): 3.0 0.2193, market moneyline 0.2111.

3.0 calibration:

| bin         |   n |   predicted |   actual |
|:------------|----:|------------:|---------:|
| [0.0, 0.3)  |  62 |       0.247 |    0.258 |
| [0.3, 0.4)  | 120 |       0.359 |    0.275 |
| [0.4, 0.5)  | 191 |       0.454 |    0.372 |
| [0.5, 0.6)  | 240 |       0.55  |    0.508 |
| [0.6, 0.7)  | 215 |       0.649 |    0.614 |
| [0.7, 1.01) | 227 |       0.774 |    0.775 |

## 2. Win probability, 2023 to 2025 (held out)

Brier score (lower is better): 3.0 0.2175, market moneyline 0.2102.

3.0 calibration:

| bin         |   n |   predicted |   actual |
|:------------|----:|------------:|---------:|
| [0.0, 0.3)  |  45 |       0.249 |    0.289 |
| [0.3, 0.4)  |  85 |       0.356 |    0.365 |
| [0.4, 0.5)  | 175 |       0.451 |    0.343 |
| [0.5, 0.6)  | 181 |       0.549 |    0.503 |
| [0.6, 0.7)  | 167 |       0.647 |    0.731 |
| [0.7, 1.01) | 163 |       0.775 |    0.767 |

## 3. Spreads: threshold sweep on the tuning window (2019 to 2022)

|   edge |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|-------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|      1 |    717 |    375 |      342 |       15 |     0.523 |    -1.2 | -0.002 |
|      2 |    448 |    238 |      210 |        7 |     0.531 |     7   |  0.014 |
|      3 |    283 |    151 |      132 |        4 |     0.534 |     5.8 |  0.019 |
|      4 |    155 |     92 |       63 |        0 |     0.594 |    22.7 |  0.133 |
|      5 |     74 |     41 |       33 |        0 |     0.554 |     4.7 |  0.058 |
|      6 |     37 |     21 |       16 |        0 |     0.568 |     3.4 |  0.084 |
|      7 |     14 |      8 |        6 |        0 |     0.571 |     1.4 |  0.091 |
|      8 |      9 |      5 |        4 |        0 |     0.556 |     0.6 |  0.061 |

## 4. Totals: threshold sweep on the tuning window

|   edge |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|-------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|      1 |    765 |    400 |      365 |        7 |     0.523 |    -1.5 | -0.002 |
|      2 |    510 |    273 |      237 |        4 |     0.535 |    12.3 |  0.022 |
|      3 |    293 |    160 |      133 |        2 |     0.546 |    13.7 |  0.043 |
|      4 |    150 |     82 |       68 |        1 |     0.547 |     7.2 |  0.044 |
|      5 |     79 |     46 |       33 |        1 |     0.582 |     9.7 |  0.112 |
|      6 |     39 |     22 |       17 |        0 |     0.564 |     3.3 |  0.077 |
|      7 |     13 |      8 |        5 |        0 |     0.615 |     2.5 |  0.175 |
|      8 |      6 |      3 |        3 |        0 |     0.5   |    -0.3 | -0.045 |

Best spread threshold with 100+ bets on the tuning window: 4 (ROI +0.133). Best total threshold: 4 (ROI +0.044). The held-out results below use the live flags (5 / 6) and, separately, these.

## 5. Held-out 2023 to 2025, live flags (5 / 6)

Spreads:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|------:|
| all |     39 |     22 |       17 |        2 |     0.564 |     3.3 | 0.077 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|     2023 |      5 |      3 |        2 |        2 |     0.6   |     0.8 |  0.145 |
|     2024 |     16 |     11 |        5 |        0 |     0.688 |     5.5 |  0.312 |
|     2025 |     18 |      8 |       10 |        0 |     0.444 |    -3   | -0.152 |

By edge size:

| bucket      |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|:------------|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
| [5.0, 6.0)  |     18 |     11 |        7 |        2 |     0.611 |     3.3 |  0.167 |
| [6.0, 7.0)  |     11 |      6 |        5 |        0 |     0.545 |     0.5 |  0.041 |
| [7.0, 9.0)  |      6 |      3 |        3 |        0 |     0.5   |    -0.3 | -0.045 |
| [9.0, 99.0) |      4 |      2 |        2 |        0 |     0.5   |    -0.2 | -0.045 |

Totals:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|------:|
| all |     22 |     12 |       10 |        0 |     0.545 |       1 | 0.041 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|     2023 |      7 |      3 |        4 |        0 |     0.429 |    -1.4 | -0.182 |
|     2024 |     11 |      5 |        6 |        0 |     0.455 |    -1.6 | -0.132 |
|     2025 |      4 |      4 |        0 |        0 |     1     |     4   |  0.909 |

## 5. Held-out 2023 to 2025, tuned (4 / 4)

Spreads:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|------:|
| all |     76 |     49 |       27 |        2 |     0.645 |    19.3 | 0.231 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|------:|
|     2023 |     17 |     12 |        5 |        2 |     0.706 |     6.5 | 0.348 |
|     2024 |     31 |     22 |        9 |        0 |     0.71  |    12.1 | 0.355 |
|     2025 |     28 |     15 |       13 |        0 |     0.536 |     0.7 | 0.023 |

By edge size:

| bucket      |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|:------------|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
| [4.0, 5.0)  |     37 |     27 |       10 |        0 |     0.73  |    16   |  0.393 |
| [5.0, 6.0)  |     18 |     11 |        7 |        2 |     0.611 |     3.3 |  0.167 |
| [6.0, 8.0)  |     15 |      7 |        8 |        0 |     0.467 |    -1.8 | -0.109 |
| [8.0, 99.0) |      6 |      4 |        2 |        0 |     0.667 |     1.8 |  0.273 |

Totals:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
| all |    127 |     61 |       66 |        1 |      0.48 |   -11.6 | -0.083 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|     2023 |     56 |     24 |       32 |        1 |     0.429 |   -11.2 | -0.182 |
|     2024 |     43 |     21 |       22 |        0 |     0.488 |    -3.2 | -0.068 |
|     2025 |     28 |     16 |       12 |        0 |     0.571 |     2.8 |  0.091 |

## 6. Market plus model

Blend the model line with the closing line, pred = a x model + (1 - a) x line. Best a on 2019 to 2022 by margin MAE: 0.3.

|   a (model share) |   margin MAE 2019-22 |   margin MAE 2023-25 |   total MAE 2023-25 |
|------------------:|---------------------:|---------------------:|--------------------:|
|               0   |                9.888 |                9.744 |              10.121 |
|               0.1 |                9.879 |                9.742 |              10.116 |
|               0.2 |                9.873 |                9.744 |              10.115 |
|               0.3 |                9.872 |                9.752 |              10.117 |
|               0.4 |                9.878 |                9.764 |              10.122 |
|               0.5 |                9.89  |                9.783 |              10.133 |
|               0.6 |                9.905 |                9.805 |              10.15  |
|               0.7 |                9.929 |                9.835 |              10.17  |
|               0.8 |                9.957 |                9.869 |              10.196 |
|               0.9 |                9.99  |                9.906 |              10.226 |
|               1   |               10.033 |                9.949 |              10.261 |

Bet selection is unchanged by blending (the edge is scaled, not re-ordered), so this only improves the score and the probabilities.

## 7. Closing line value

Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).
