# NFL Model 3.0 backtest

Walk-forward: every week is priced with only games played before it; the points regression is refit before every week on every played game since 2013. Ridge strength and bet thresholds were chosen on 2019 to 2022 only, and 2023 to 2025 was the held-out test for them. Since 22 Sep 2026 every new input, and the rating decay and last-season weight, is accepted only when it helps on both windows, so for those choices 2023 to 2025 is a second test window rather than an untouched one; the live season is the only fully unseen test.

## 1. Points miss (mean absolute error) against Vegas

Tuning window 2019 to 2022:

| target      |   3.0 |   Vegas close |   games |
|:------------|------:|--------------:|--------:|
| team points |  7.35 |          7.29 |    1055 |
| margin      | 10.02 |          9.89 |    1055 |
| total       | 10.5  |         10.54 |    1055 |

Held-out 2023 to 2025:

| target      |   3.0 |   Vegas close |   games |
|:------------|------:|--------------:|--------:|
| team points |  7.24 |          7.21 |     816 |
| margin      |  9.9  |          9.74 |     816 |
| total       | 10.09 |         10.12 |     816 |

Held-out, Week 5 on:

| target      |   3.0 |   Vegas close |   games |
|:------------|------:|--------------:|--------:|
| team points |  7.25 |          7.19 |     624 |
| margin      |  9.81 |          9.59 |     624 |
| total       | 10.07 |         10.09 |     624 |

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
|      1 |    770 |    416 |      354 |       10 |     0.54  |    26.6 | 0.031 |
|      2 |    511 |    279 |      232 |        3 |     0.546 |    23.8 | 0.042 |
|      3 |    328 |    191 |      137 |        2 |     0.582 |    40.3 | 0.112 |
|      4 |    189 |    120 |       69 |        0 |     0.635 |    44.1 | 0.212 |
|      5 |    108 |     70 |       38 |        0 |     0.648 |    28.2 | 0.237 |
|      6 |     60 |     40 |       20 |        0 |     0.667 |    18   | 0.273 |
|      7 |     30 |     20 |       10 |        0 |     0.667 |     9   | 0.273 |
|      8 |     17 |     13 |        4 |        0 |     0.765 |     8.6 | 0.46  |

Best spread threshold with 100+ bets on the tuning window: 4 (ROI +0.151). Best total threshold: 5 (ROI +0.237). The held-out results below use the live spread flag (4; totals are not flagged, so they are graded at the tuned 5) and, separately, these.

## 5. Held-out 2023 to 2025, live flag (4 / 5)

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
| all |     57 |     33 |       24 |        1 |     0.579 |     6.6 | 0.105 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|------:|
|     2023 |     20 |     12 |        8 |        0 |     0.6   |     3.2 | 0.145 |
|     2024 |     20 |     11 |        9 |        1 |     0.55  |     1.1 | 0.05  |
|     2025 |     17 |     10 |        7 |        0 |     0.588 |     2.3 | 0.123 |

## 5. Held-out 2023 to 2025, tuned (4 / 5)

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
| all |     57 |     33 |       24 |        1 |     0.579 |     6.6 | 0.105 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|------:|
|     2023 |     20 |     12 |        8 |        0 |     0.6   |     3.2 | 0.145 |
|     2024 |     20 |     11 |        9 |        1 |     0.55  |     1.1 | 0.05  |
|     2025 |     17 |     10 |        7 |        0 |     0.588 |     2.3 | 0.123 |

## 6. Market plus model

Blend the model line with the closing line, pred = a x model + (1 - a) x line. Best a on 2019 to 2022 by margin MAE: 0.3.

|   a (model share) |   margin MAE 2019-22 |   margin MAE 2023-25 |   total MAE 2023-25 |
|------------------:|---------------------:|---------------------:|--------------------:|
|               0   |                9.888 |                9.744 |              10.121 |
|               0.1 |                9.878 |                9.739 |              10.098 |
|               0.2 |                9.87  |                9.738 |              10.08  |
|               0.3 |                9.866 |                9.742 |              10.067 |
|               0.4 |                9.871 |                9.748 |              10.058 |
|               0.5 |                9.881 |                9.76  |              10.053 |
|               0.6 |                9.895 |                9.777 |              10.05  |
|               0.7 |                9.917 |                9.8   |              10.051 |
|               0.8 |                9.944 |                9.829 |              10.056 |
|               0.9 |                9.977 |                9.861 |              10.069 |
|               1   |               10.018 |                9.897 |              10.089 |

Bet selection is unchanged by blending (the edge is scaled, not re-ordered), so this only improves the score and the probabilities.

## 7. Closing line value

Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).
