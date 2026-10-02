# NFL Model 3.0 backtest

Walk-forward: every week is priced with only games played before it; the points regression is refit before every week on every played game since 2013. Ridge strength and bet thresholds were chosen on 2019 to 2022 only, and 2023 to 2025 was the held-out test for them. Since 22 Sep 2026 every new input, and the rating decay and last-season weight, is accepted only when it helps on both windows, so for those choices 2023 to 2025 is a second test window rather than an untouched one; the live season is the only fully unseen test.

## 1. Points miss (mean absolute error) against Vegas

Tuning window 2019 to 2022:

| target      |   3.0 |   Vegas close |   games |
|:------------|------:|--------------:|--------:|
| team points |  7.36 |          7.29 |    1055 |
| margin      | 10.01 |          9.89 |    1055 |
| total       | 10.52 |         10.54 |    1055 |

Held-out 2023 to 2025:

| target      |   3.0 |   Vegas close |   games |
|:------------|------:|--------------:|--------:|
| team points |  7.23 |          7.21 |     816 |
| margin      |  9.91 |          9.74 |     816 |
| total       | 10.1  |         10.12 |     816 |

Held-out, Week 5 on:

| target      |   3.0 |   Vegas close |   games |
|:------------|------:|--------------:|--------:|
| team points |  7.25 |          7.19 |     624 |
| margin      |  9.82 |          9.59 |     624 |
| total       | 10.09 |         10.09 |     624 |

## 2. Win probability, 2019 to 2022 (tuning)

Brier score (lower is better): 3.0 0.2186, market moneyline 0.2111.

3.0 calibration:

| bin         |   n |   predicted |   actual |
|:------------|----:|------------:|---------:|
| [0.0, 0.3)  |  65 |       0.243 |    0.277 |
| [0.3, 0.4)  | 126 |       0.359 |    0.27  |
| [0.4, 0.5)  | 196 |       0.456 |    0.388 |
| [0.5, 0.6)  | 230 |       0.551 |    0.496 |
| [0.6, 0.7)  | 211 |       0.651 |    0.621 |
| [0.7, 1.01) | 227 |       0.773 |    0.78  |

## 2. Win probability, 2023 to 2025 (held out)

Brier score (lower is better): 3.0 0.2162, market moneyline 0.2102.

3.0 calibration:

| bin         |   n |   predicted |   actual |
|:------------|----:|------------:|---------:|
| [0.0, 0.3)  |  44 |       0.246 |    0.273 |
| [0.3, 0.4)  |  90 |       0.352 |    0.367 |
| [0.4, 0.5)  | 173 |       0.45  |    0.341 |
| [0.5, 0.6)  | 185 |       0.552 |    0.519 |
| [0.6, 0.7)  | 171 |       0.651 |    0.725 |
| [0.7, 1.01) | 153 |       0.78  |    0.771 |

## 3. Spreads: threshold sweep on the tuning window (2019 to 2022)

|   edge |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|-------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|      1 |    693 |    363 |      330 |       14 |     0.524 |    -0   | -0     |
|      2 |    439 |    235 |      204 |        5 |     0.535 |    10.6 |  0.022 |
|      3 |    258 |    140 |      118 |        3 |     0.543 |    10.2 |  0.036 |
|      4 |    129 |     79 |       50 |        0 |     0.612 |    24   |  0.169 |
|      5 |     69 |     38 |       31 |        0 |     0.551 |     3.9 |  0.051 |
|      6 |     29 |     15 |       14 |        0 |     0.517 |    -0.4 | -0.013 |
|      7 |     15 |      7 |        8 |        0 |     0.467 |    -1.8 | -0.109 |
|      8 |     10 |      6 |        4 |        0 |     0.6   |     1.6 |  0.145 |

## 4. Totals: threshold sweep on the tuning window

|   edge |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|-------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|      1 |    745 |    409 |      336 |        9 |     0.549 |    39.4 |  0.048 |
|      2 |    488 |    279 |      209 |        6 |     0.572 |    49.1 |  0.091 |
|      3 |    297 |    173 |      124 |        3 |     0.582 |    36.6 |  0.112 |
|      4 |    164 |     99 |       65 |        0 |     0.604 |    27.5 |  0.152 |
|      5 |     91 |     58 |       33 |        0 |     0.637 |    21.7 |  0.217 |
|      6 |     46 |     31 |       15 |        0 |     0.674 |    14.5 |  0.287 |
|      7 |     23 |     15 |        8 |        0 |     0.652 |     6.2 |  0.245 |
|      8 |     12 |      6 |        6 |        0 |     0.5   |    -0.6 | -0.045 |

Best spread threshold with 100+ bets on the tuning window: 4 (ROI +0.169). Best total threshold: 4 (ROI +0.152). The held-out results below use the live spread flag (4; totals are not flagged, so they are graded at the tuned 4) and, separately, these.

## 5. Held-out 2023 to 2025, live flag (4 / 4)

Spreads:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|------:|
| all |     66 |     41 |       25 |        1 |     0.621 |    13.5 | 0.186 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|------:|
|     2023 |     11 |      7 |        4 |        1 |     0.636 |     2.6 | 0.215 |
|     2024 |     31 |     20 |       11 |        0 |     0.645 |     7.9 | 0.232 |
|     2025 |     24 |     14 |       10 |        0 |     0.583 |     3   | 0.114 |

By edge size:

| bucket      |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|:------------|-------:|-------:|---------:|---------:|----------:|--------:|------:|
| [4.0, 5.0)  |     39 |     24 |       15 |        0 |     0.615 |     7.5 | 0.175 |
| [5.0, 6.0)  |     13 |      7 |        6 |        1 |     0.538 |     0.4 | 0.028 |
| [6.0, 8.0)  |      9 |      7 |        2 |        0 |     0.778 |     4.8 | 0.485 |
| [8.0, 99.0) |      5 |      3 |        2 |        0 |     0.6   |     0.8 | 0.145 |

Totals:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|------:|
| all |    120 |     70 |       50 |        1 |     0.583 |      15 | 0.114 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|------:|
|     2023 |     41 |     23 |       18 |        0 |     0.561 |     3.2 | 0.071 |
|     2024 |     42 |     24 |       18 |        1 |     0.571 |     4.2 | 0.091 |
|     2025 |     37 |     23 |       14 |        0 |     0.622 |     7.6 | 0.187 |

## 5. Held-out 2023 to 2025, tuned (4 / 4)

Spreads:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|------:|
| all |     66 |     41 |       25 |        1 |     0.621 |    13.5 | 0.186 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|------:|
|     2023 |     11 |      7 |        4 |        1 |     0.636 |     2.6 | 0.215 |
|     2024 |     31 |     20 |       11 |        0 |     0.645 |     7.9 | 0.232 |
|     2025 |     24 |     14 |       10 |        0 |     0.583 |     3   | 0.114 |

By edge size:

| bucket      |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|:------------|-------:|-------:|---------:|---------:|----------:|--------:|------:|
| [4.0, 5.0)  |     39 |     24 |       15 |        0 |     0.615 |     7.5 | 0.175 |
| [5.0, 6.0)  |     13 |      7 |        6 |        1 |     0.538 |     0.4 | 0.028 |
| [6.0, 8.0)  |      9 |      7 |        2 |        0 |     0.778 |     4.8 | 0.485 |
| [8.0, 99.0) |      5 |      3 |        2 |        0 |     0.6   |     0.8 | 0.145 |

Totals:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|------:|
| all |    120 |     70 |       50 |        1 |     0.583 |      15 | 0.114 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|------:|
|     2023 |     41 |     23 |       18 |        0 |     0.561 |     3.2 | 0.071 |
|     2024 |     42 |     24 |       18 |        1 |     0.571 |     4.2 | 0.091 |
|     2025 |     37 |     23 |       14 |        0 |     0.622 |     7.6 | 0.187 |

## 6. Market plus model

Blend the model line with the closing line, pred = a x model + (1 - a) x line. Best a on 2019 to 2022 by margin MAE: 0.3.

|   a (model share) |   margin MAE 2019-22 |   margin MAE 2023-25 |   total MAE 2023-25 |
|------------------:|---------------------:|---------------------:|--------------------:|
|               0   |                9.888 |                9.744 |              10.121 |
|               0.1 |                9.878 |                9.74  |              10.097 |
|               0.2 |                9.869 |                9.74  |              10.078 |
|               0.3 |                9.864 |                9.745 |              10.063 |
|               0.4 |                9.868 |                9.752 |              10.054 |
|               0.5 |                9.878 |                9.764 |              10.048 |
|               0.6 |                9.892 |                9.783 |              10.046 |
|               0.7 |                9.913 |                9.806 |              10.052 |
|               0.8 |                9.939 |                9.836 |              10.063 |
|               0.9 |                9.971 |                9.87  |              10.079 |
|               1   |               10.011 |                9.907 |              10.103 |

Bet selection is unchanged by blending (the edge is scaled, not re-ordered), so this only improves the score and the probabilities.

## 7. Closing line value

Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).
