# NFL Model 3.0 backtest

Walk-forward: every week is priced with only games played before it; the points regression is refit before every week on every played game since 2013. Ridge strength and bet thresholds were chosen on 2019 to 2022 only, and 2023 to 2025 was the held-out test for them. Since 22 Sep 2026 every new input, and the rating decay and last-season weight, is accepted only when it helps on both windows, so for those choices 2023 to 2025 is a second test window rather than an untouched one; the live season is the only fully unseen test.

## 1. Points miss (mean absolute error) against Vegas

Tuning window 2019 to 2022:

| target      |   3.0 |   Vegas close |   games |
|:------------|------:|--------------:|--------:|
| team points |  7.34 |          7.29 |    1055 |
| margin      | 10.02 |          9.89 |    1055 |
| total       | 10.58 |         10.54 |    1055 |

Held-out 2023 to 2025:

| target      |   3.0 |   Vegas close |   games |
|:------------|------:|--------------:|--------:|
| team points |  7.27 |          7.21 |     816 |
| margin      |  9.9  |          9.74 |     816 |
| total       | 10.24 |         10.12 |     816 |

Held-out, Week 5 on:

| target      |   3.0 |   Vegas close |   games |
|:------------|------:|--------------:|--------:|
| team points |  7.3  |          7.19 |     624 |
| margin      |  9.82 |          9.59 |     624 |
| total       | 10.23 |         10.09 |     624 |

## 2. Win probability, 2019 to 2022 (tuning)

Brier score (lower is better): 3.0 0.2186, market moneyline 0.2111.

3.0 calibration:

| bin         |   n |   predicted |   actual |
|:------------|----:|------------:|---------:|
| [0.0, 0.3)  |  66 |       0.244 |    0.273 |
| [0.3, 0.4)  | 125 |       0.36  |    0.28  |
| [0.4, 0.5)  | 198 |       0.456 |    0.379 |
| [0.5, 0.6)  | 224 |       0.552 |    0.5   |
| [0.6, 0.7)  | 217 |       0.65  |    0.622 |
| [0.7, 1.01) | 225 |       0.774 |    0.778 |

## 2. Win probability, 2023 to 2025 (held out)

Brier score (lower is better): 3.0 0.2161, market moneyline 0.2102.

3.0 calibration:

| bin         |   n |   predicted |   actual |
|:------------|----:|------------:|---------:|
| [0.0, 0.3)  |  42 |       0.247 |    0.286 |
| [0.3, 0.4)  |  89 |       0.35  |    0.36  |
| [0.4, 0.5)  | 179 |       0.45  |    0.341 |
| [0.5, 0.6)  | 182 |       0.551 |    0.527 |
| [0.6, 0.7)  | 167 |       0.65  |    0.719 |
| [0.7, 1.01) | 157 |       0.777 |    0.771 |

## 3. Spreads: threshold sweep on the tuning window (2019 to 2022)

|   edge |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|-------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|      1 |    696 |    358 |      338 |       14 |     0.514 |   -13.8 | -0.018 |
|      2 |    439 |    232 |      207 |        6 |     0.528 |     4.3 |  0.009 |
|      3 |    259 |    139 |      120 |        2 |     0.537 |     7   |  0.025 |
|      4 |    136 |     82 |       54 |        0 |     0.603 |    22.6 |  0.151 |
|      5 |     68 |     38 |       30 |        0 |     0.559 |     5   |  0.067 |
|      6 |     30 |     16 |       14 |        0 |     0.533 |     0.6 |  0.018 |
|      7 |     13 |      6 |        7 |        0 |     0.462 |    -1.7 | -0.119 |
|      8 |      9 |      5 |        4 |        0 |     0.556 |     0.6 |  0.061 |

## 4. Totals: threshold sweep on the tuning window

|   edge |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|-------:|-------:|-------:|---------:|---------:|----------:|--------:|------:|
|      1 |    756 |    404 |      352 |        7 |     0.534 |    16.8 | 0.02  |
|      2 |    504 |    272 |      232 |        5 |     0.54  |    16.8 | 0.03  |
|      3 |    322 |    183 |      139 |        3 |     0.568 |    30.1 | 0.085 |
|      4 |    185 |    114 |       71 |        1 |     0.616 |    35.9 | 0.176 |
|      5 |     96 |     65 |       31 |        1 |     0.677 |    30.9 | 0.293 |
|      6 |     50 |     29 |       21 |        0 |     0.58  |     5.9 | 0.107 |
|      7 |     20 |     11 |        9 |        0 |     0.55  |     1.1 | 0.05  |
|      8 |      7 |      4 |        3 |        0 |     0.571 |     0.7 | 0.091 |

Best spread threshold with 100+ bets on the tuning window: 4 (ROI +0.151). Best total threshold: 4 (ROI +0.176). The held-out results below use the live flags (5 / 6) and, separately, these.

## 5. Held-out 2023 to 2025, live flags (5 / 6)

Spreads:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|------:|
| all |     31 |     20 |       11 |        1 |     0.645 |     7.9 | 0.232 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|------:|
|     2023 |      6 |      4 |        2 |        1 |     0.667 |     1.8 | 0.273 |
|     2024 |     10 |      8 |        2 |        0 |     0.8   |     5.8 | 0.527 |
|     2025 |     15 |      8 |        7 |        0 |     0.533 |     0.3 | 0.018 |

By edge size:

| bucket      |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|:------------|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
| [5.0, 6.0)  |     14 |      9 |        5 |        1 |     0.643 |     3.5 |  0.227 |
| [6.0, 7.0)  |     11 |      7 |        4 |        0 |     0.636 |     2.6 |  0.215 |
| [7.0, 9.0)  |      5 |      4 |        1 |        0 |     0.8   |     2.9 |  0.527 |
| [9.0, 99.0) |      1 |      0 |        1 |        0 |     0     |    -1.1 | -1     |

Totals:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
| all |     19 |      9 |       10 |        0 |     0.474 |      -2 | -0.096 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|     2023 |      6 |      2 |        4 |        0 |     0.333 |    -2.4 | -0.364 |
|     2024 |     10 |      4 |        6 |        0 |     0.4   |    -2.6 | -0.236 |
|     2025 |      3 |      3 |        0 |        0 |     1     |     3   |  0.909 |

## 5. Held-out 2023 to 2025, tuned (4 / 4)

Spreads:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|------:|
| all |     70 |     44 |       26 |        1 |     0.629 |    15.4 |   0.2 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|------:|
|     2023 |     11 |      7 |        4 |        1 |     0.636 |     2.6 | 0.215 |
|     2024 |     33 |     23 |       10 |        0 |     0.697 |    12   | 0.331 |
|     2025 |     26 |     14 |       12 |        0 |     0.538 |     0.8 | 0.028 |

By edge size:

| bucket      |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|:------------|-------:|-------:|---------:|---------:|----------:|--------:|------:|
| [4.0, 5.0)  |     39 |     24 |       15 |        0 |     0.615 |     7.5 | 0.175 |
| [5.0, 6.0)  |     14 |      9 |        5 |        1 |     0.643 |     3.5 | 0.227 |
| [6.0, 8.0)  |     12 |      8 |        4 |        0 |     0.667 |     3.6 | 0.273 |
| [8.0, 99.0) |      5 |      3 |        2 |        0 |     0.6   |     0.8 | 0.145 |

Totals:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
| all |    105 |     50 |       55 |        0 |     0.476 |   -10.5 | -0.091 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|     2023 |     39 |     15 |       24 |        0 |     0.385 |   -11.4 | -0.266 |
|     2024 |     39 |     20 |       19 |        0 |     0.513 |    -0.9 | -0.021 |
|     2025 |     27 |     15 |       12 |        0 |     0.556 |     1.8 |  0.061 |

## 6. Market plus model

Blend the model line with the closing line, pred = a x model + (1 - a) x line. Best a on 2019 to 2022 by margin MAE: 0.3.

|   a (model share) |   margin MAE 2019-22 |   margin MAE 2023-25 |   total MAE 2023-25 |
|------------------:|---------------------:|---------------------:|--------------------:|
|               0   |                9.888 |                9.744 |              10.121 |
|               0.1 |                9.879 |                9.739 |              10.114 |
|               0.2 |                9.872 |                9.739 |              10.111 |
|               0.3 |                9.869 |                9.743 |              10.112 |
|               0.4 |                9.874 |                9.749 |              10.116 |
|               0.5 |                9.885 |                9.761 |              10.125 |
|               0.6 |                9.9   |                9.78  |              10.139 |
|               0.7 |                9.921 |                9.804 |              10.158 |
|               0.8 |                9.948 |                9.833 |              10.181 |
|               0.9 |                9.981 |                9.867 |              10.211 |
|               1   |               10.021 |                9.905 |              10.245 |

Bet selection is unchanged by blending (the edge is scaled, not re-ordered), so this only improves the score and the probabilities.

## 7. Closing line value

Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).
