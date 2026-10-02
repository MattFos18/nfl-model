# NFL Model 3.0 backtest

Walk-forward: every week is priced with only games played before it; the points regression is refit before every week on every played game since 2013. Ridge strength and bet thresholds were chosen on 2019 to 2022 only, and 2023 to 2025 was the held-out test for them. Since 22 Sep 2026 every new input, and the rating decay and last-season weight, is accepted only when it helps on both windows, so for those choices 2023 to 2025 is a second test window rather than an untouched one; the live season is the only fully unseen test.

## 1. Points miss (mean absolute error) against Vegas

Tuning window 2019 to 2022:

| target      |   3.0 |   Vegas close |   games |
|:------------|------:|--------------:|--------:|
| team points |  7.37 |          7.29 |    1055 |
| margin      | 10.02 |          9.89 |    1055 |
| total       | 10.54 |         10.54 |    1055 |

Held-out 2023 to 2025:

| target      |   3.0 |   Vegas close |   games |
|:------------|------:|--------------:|--------:|
| team points |  7.24 |          7.21 |     816 |
| margin      |  9.9  |          9.74 |     816 |
| total       | 10.12 |         10.12 |     816 |

Held-out, Week 5 on:

| target      |   3.0 |   Vegas close |   games |
|:------------|------:|--------------:|--------:|
| team points |  7.25 |          7.19 |     624 |
| margin      |  9.81 |          9.59 |     624 |
| total       | 10.1  |         10.09 |     624 |

## 2. Win probability, 2019 to 2022 (tuning)

Brier score (lower is better): 3.0 0.2187, market moneyline 0.2111.

3.0 calibration:

| bin         |   n |   predicted |   actual |
|:------------|----:|------------:|---------:|
| [0.0, 0.3)  |  66 |       0.244 |    0.273 |
| [0.3, 0.4)  | 124 |       0.36  |    0.274 |
| [0.4, 0.5)  | 200 |       0.456 |    0.385 |
| [0.5, 0.6)  | 226 |       0.552 |    0.491 |
| [0.6, 0.7)  | 210 |       0.65  |    0.629 |
| [0.7, 1.01) | 229 |       0.773 |    0.777 |

## 2. Win probability, 2023 to 2025 (held out)

Brier score (lower is better): 3.0 0.2160, market moneyline 0.2102.

3.0 calibration:

| bin         |   n |   predicted |   actual |
|:------------|----:|------------:|---------:|
| [0.0, 0.3)  |  43 |       0.245 |    0.279 |
| [0.3, 0.4)  |  90 |       0.351 |    0.356 |
| [0.4, 0.5)  | 173 |       0.45  |    0.341 |
| [0.5, 0.6)  | 188 |       0.552 |    0.521 |
| [0.6, 0.7)  | 168 |       0.651 |    0.726 |
| [0.7, 1.01) | 154 |       0.779 |    0.773 |

## 3. Spreads: threshold sweep on the tuning window (2019 to 2022)

|   edge |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|-------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|      1 |    700 |    364 |      336 |       14 |     0.52  |    -5.6 | -0.007 |
|      2 |    441 |    234 |      207 |        6 |     0.531 |     6.3 |  0.013 |
|      3 |    257 |    139 |      118 |        3 |     0.541 |     9.2 |  0.033 |
|      4 |    136 |     82 |       54 |        0 |     0.603 |    22.6 |  0.151 |
|      5 |     68 |     39 |       29 |        0 |     0.574 |     7.1 |  0.095 |
|      6 |     29 |     15 |       14 |        0 |     0.517 |    -0.4 | -0.013 |
|      7 |     13 |      6 |        7 |        0 |     0.462 |    -1.7 | -0.119 |
|      8 |      9 |      5 |        4 |        0 |     0.556 |     0.6 |  0.061 |

## 4. Totals: threshold sweep on the tuning window

|   edge |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|-------:|-------:|-------:|---------:|---------:|----------:|--------:|------:|
|      1 |    740 |    401 |      339 |       10 |     0.542 |    28.1 | 0.035 |
|      2 |    503 |    273 |      230 |        6 |     0.543 |    20   | 0.036 |
|      3 |    310 |    176 |      134 |        3 |     0.568 |    28.6 | 0.084 |
|      4 |    172 |    101 |       71 |        0 |     0.587 |    22.9 | 0.121 |
|      5 |     95 |     64 |       31 |        0 |     0.674 |    29.9 | 0.286 |
|      6 |     52 |     36 |       16 |        0 |     0.692 |    18.4 | 0.322 |
|      7 |     24 |     16 |        8 |        0 |     0.667 |     7.2 | 0.273 |
|      8 |     13 |      9 |        4 |        0 |     0.692 |     4.6 | 0.322 |

Best spread threshold with 100+ bets on the tuning window: 4 (ROI +0.151). Best total threshold: 4 (ROI +0.121). The held-out results below use the live spread flag (4; totals are not flagged, so they are graded at the tuned 4) and, separately, these.

## 5. Held-out 2023 to 2025, live flag (4 / 4)

Spreads:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|------:|
| all |     64 |     41 |       23 |        1 |     0.641 |    15.7 | 0.223 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|------:|
|     2023 |     11 |      7 |        4 |        1 |     0.636 |     2.6 | 0.215 |
|     2024 |     29 |     20 |        9 |        0 |     0.69  |    10.1 | 0.317 |
|     2025 |     24 |     14 |       10 |        0 |     0.583 |     3   | 0.114 |

By edge size:

| bucket      |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|:------------|-------:|-------:|---------:|---------:|----------:|--------:|------:|
| [4.0, 5.0)  |     35 |     23 |       12 |        0 |     0.657 |     9.8 | 0.255 |
| [5.0, 6.0)  |     15 |      8 |        7 |        1 |     0.533 |     0.3 | 0.018 |
| [6.0, 8.0)  |      9 |      7 |        2 |        0 |     0.778 |     4.8 | 0.485 |
| [8.0, 99.0) |      5 |      3 |        2 |        0 |     0.6   |     0.8 | 0.145 |

Totals:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|------:|
| all |    125 |     72 |       53 |        1 |     0.576 |    13.7 |   0.1 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|------:|
|     2023 |     39 |     22 |       17 |        0 |     0.564 |     3.3 | 0.077 |
|     2024 |     43 |     23 |       20 |        1 |     0.535 |     1   | 0.021 |
|     2025 |     43 |     27 |       16 |        0 |     0.628 |     9.4 | 0.199 |

## 5. Held-out 2023 to 2025, tuned (4 / 4)

Spreads:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|------:|
| all |     64 |     41 |       23 |        1 |     0.641 |    15.7 | 0.223 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|------:|
|     2023 |     11 |      7 |        4 |        1 |     0.636 |     2.6 | 0.215 |
|     2024 |     29 |     20 |        9 |        0 |     0.69  |    10.1 | 0.317 |
|     2025 |     24 |     14 |       10 |        0 |     0.583 |     3   | 0.114 |

By edge size:

| bucket      |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|:------------|-------:|-------:|---------:|---------:|----------:|--------:|------:|
| [4.0, 5.0)  |     35 |     23 |       12 |        0 |     0.657 |     9.8 | 0.255 |
| [5.0, 6.0)  |     15 |      8 |        7 |        1 |     0.533 |     0.3 | 0.018 |
| [6.0, 8.0)  |      9 |      7 |        2 |        0 |     0.778 |     4.8 | 0.485 |
| [8.0, 99.0) |      5 |      3 |        2 |        0 |     0.6   |     0.8 | 0.145 |

Totals:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|------:|
| all |    125 |     72 |       53 |        1 |     0.576 |    13.7 |   0.1 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|------:|
|     2023 |     39 |     22 |       17 |        0 |     0.564 |     3.3 | 0.077 |
|     2024 |     43 |     23 |       20 |        1 |     0.535 |     1   | 0.021 |
|     2025 |     43 |     27 |       16 |        0 |     0.628 |     9.4 | 0.199 |

## 6. Market plus model

Blend the model line with the closing line, pred = a x model + (1 - a) x line. Best a on 2019 to 2022 by margin MAE: 0.3.

|   a (model share) |   margin MAE 2019-22 |   margin MAE 2023-25 |   total MAE 2023-25 |
|------------------:|---------------------:|---------------------:|--------------------:|
|               0   |                9.888 |                9.744 |              10.121 |
|               0.1 |                9.878 |                9.739 |              10.1   |
|               0.2 |                9.87  |                9.738 |              10.083 |
|               0.3 |                9.866 |                9.742 |              10.07  |
|               0.4 |                9.871 |                9.748 |              10.061 |
|               0.5 |                9.881 |                9.76  |              10.057 |
|               0.6 |                9.895 |                9.777 |              10.059 |
|               0.7 |                9.917 |                9.8   |              10.066 |
|               0.8 |                9.944 |                9.829 |              10.079 |
|               0.9 |                9.977 |                9.861 |              10.097 |
|               1   |               10.018 |                9.897 |              10.12  |

Bet selection is unchanged by blending (the edge is scaled, not re-ordered), so this only improves the score and the probabilities.

## 7. Closing line value

Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).
