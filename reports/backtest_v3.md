# NFL Model 3.0 backtest

Walk-forward: every week is priced with only games played before it; the points regression is refit before every week on every played game since 2013. Ridge strength and bet thresholds were chosen on 2019 to 2022 only, and 2023 to 2025 was the held-out test for them. Since 22 Sep 2026 every new input, and the rating decay and last-season weight, is accepted only when it helps on both windows, so for those choices 2023 to 2025 is a second test window rather than an untouched one; the live season is the only fully unseen test.

## 1. Points miss (mean absolute error) against Vegas

Tuning window 2019 to 2022:

| target      |   3.0 |   Vegas close |   games |
|:------------|------:|--------------:|--------:|
| team points |  7.37 |          7.29 |    1055 |
| margin      | 10    |          9.89 |    1055 |
| total       | 10.53 |         10.54 |    1055 |

Held-out 2023 to 2025:

| target      |   3.0 |   Vegas close |   games |
|:------------|------:|--------------:|--------:|
| team points |  7.23 |          7.21 |     816 |
| margin      |  9.9  |          9.74 |     816 |
| total       | 10.1  |         10.12 |     816 |

Held-out, Week 5 on:

| target      |   3.0 |   Vegas close |   games |
|:------------|------:|--------------:|--------:|
| team points |  7.24 |          7.19 |     624 |
| margin      |  9.82 |          9.59 |     624 |
| total       | 10.09 |         10.09 |     624 |

## 2. Win probability, 2019 to 2022 (tuning)

Brier score (lower is better): 3.0 0.2187, market moneyline 0.2111.

3.0 calibration:

| bin         |   n |   predicted |   actual |
|:------------|----:|------------:|---------:|
| [0.0, 0.3)  |  67 |       0.244 |    0.269 |
| [0.3, 0.4)  | 116 |       0.358 |    0.276 |
| [0.4, 0.5)  | 205 |       0.454 |    0.39  |
| [0.5, 0.6)  | 226 |       0.551 |    0.491 |
| [0.6, 0.7)  | 217 |       0.65  |    0.618 |
| [0.7, 1.01) | 224 |       0.774 |    0.781 |

## 2. Win probability, 2023 to 2025 (held out)

Brier score (lower is better): 3.0 0.2160, market moneyline 0.2102.

3.0 calibration:

| bin         |   n |   predicted |   actual |
|:------------|----:|------------:|---------:|
| [0.0, 0.3)  |  42 |       0.242 |    0.262 |
| [0.3, 0.4)  |  96 |       0.353 |    0.365 |
| [0.4, 0.5)  | 173 |       0.452 |    0.335 |
| [0.5, 0.6)  | 176 |       0.552 |    0.528 |
| [0.6, 0.7)  | 173 |       0.649 |    0.717 |
| [0.7, 1.01) | 156 |       0.778 |    0.776 |

## 3. Spreads: threshold sweep on the tuning window (2019 to 2022)

|   edge |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|-------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|      1 |    696 |    367 |      329 |       14 |     0.527 |     5.1 |  0.007 |
|      2 |    445 |    238 |      207 |        5 |     0.535 |    10.3 |  0.021 |
|      3 |    260 |    143 |      117 |        1 |     0.55  |    14.3 |  0.05  |
|      4 |    137 |     82 |       55 |        0 |     0.599 |    21.5 |  0.143 |
|      5 |     74 |     44 |       30 |        0 |     0.595 |    11   |  0.135 |
|      6 |     32 |     17 |       15 |        0 |     0.531 |     0.5 |  0.014 |
|      7 |     17 |      8 |        9 |        0 |     0.471 |    -1.9 | -0.102 |
|      8 |     10 |      6 |        4 |        0 |     0.6   |     1.6 |  0.145 |

## 4. Totals: threshold sweep on the tuning window

|   edge |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|-------:|-------:|-------:|---------:|---------:|----------:|--------:|------:|
|      1 |    756 |    411 |      345 |        8 |     0.544 |    31.5 | 0.038 |
|      2 |    502 |    275 |      227 |        6 |     0.548 |    25.3 | 0.046 |
|      3 |    308 |    170 |      138 |        3 |     0.552 |    18.2 | 0.054 |
|      4 |    166 |    100 |       66 |        0 |     0.602 |    27.4 | 0.15  |
|      5 |     89 |     55 |       34 |        0 |     0.618 |    17.6 | 0.18  |
|      6 |     50 |     33 |       17 |        0 |     0.66  |    14.3 | 0.26  |
|      7 |     19 |     13 |        6 |        0 |     0.684 |     6.4 | 0.306 |
|      8 |     10 |      7 |        3 |        0 |     0.7   |     3.7 | 0.336 |

Best spread threshold with 100+ bets on the tuning window: 4 (ROI +0.143). Best total threshold: 4 (ROI +0.150). The held-out results below use the live spread flag (4; totals are not flagged, so they are graded at the tuned 4) and, separately, these.

## 5. Held-out 2023 to 2025, live flag (4 / 4)

Spreads:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|------:|
| all |     64 |     42 |       22 |        1 |     0.656 |    17.8 | 0.253 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|------:|
|     2023 |     11 |      7 |        4 |        1 |     0.636 |     2.6 | 0.215 |
|     2024 |     29 |     20 |        9 |        0 |     0.69  |    10.1 | 0.317 |
|     2025 |     24 |     15 |        9 |        0 |     0.625 |     5.1 | 0.193 |

By edge size:

| bucket      |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|:------------|-------:|-------:|---------:|---------:|----------:|--------:|------:|
| [4.0, 5.0)  |     36 |     25 |       11 |        0 |     0.694 |    12.9 | 0.326 |
| [5.0, 6.0)  |     11 |      6 |        5 |        1 |     0.545 |     0.5 | 0.041 |
| [6.0, 8.0)  |     11 |      7 |        4 |        0 |     0.636 |     2.6 | 0.215 |
| [8.0, 99.0) |      6 |      4 |        2 |        0 |     0.667 |     1.8 | 0.273 |

Totals:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|------:|
| all |    138 |     82 |       56 |        1 |     0.594 |    20.4 | 0.134 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|------:|
|     2023 |     46 |     25 |       21 |        0 |     0.543 |     1.9 | 0.038 |
|     2024 |     47 |     28 |       19 |        1 |     0.596 |     7.1 | 0.137 |
|     2025 |     45 |     29 |       16 |        0 |     0.644 |    11.4 | 0.23  |

## 5. Held-out 2023 to 2025, tuned (4 / 4)

Spreads:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|------:|
| all |     64 |     42 |       22 |        1 |     0.656 |    17.8 | 0.253 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|------:|
|     2023 |     11 |      7 |        4 |        1 |     0.636 |     2.6 | 0.215 |
|     2024 |     29 |     20 |        9 |        0 |     0.69  |    10.1 | 0.317 |
|     2025 |     24 |     15 |        9 |        0 |     0.625 |     5.1 | 0.193 |

By edge size:

| bucket      |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|:------------|-------:|-------:|---------:|---------:|----------:|--------:|------:|
| [4.0, 5.0)  |     36 |     25 |       11 |        0 |     0.694 |    12.9 | 0.326 |
| [5.0, 6.0)  |     11 |      6 |        5 |        1 |     0.545 |     0.5 | 0.041 |
| [6.0, 8.0)  |     11 |      7 |        4 |        0 |     0.636 |     2.6 | 0.215 |
| [8.0, 99.0) |      6 |      4 |        2 |        0 |     0.667 |     1.8 | 0.273 |

Totals:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|------:|
| all |    138 |     82 |       56 |        1 |     0.594 |    20.4 | 0.134 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|------:|
|     2023 |     46 |     25 |       21 |        0 |     0.543 |     1.9 | 0.038 |
|     2024 |     47 |     28 |       19 |        1 |     0.596 |     7.1 | 0.137 |
|     2025 |     45 |     29 |       16 |        0 |     0.644 |    11.4 | 0.23  |

## 6. Market plus model

Blend the model line with the closing line, pred = a x model + (1 - a) x line. Best a on 2019 to 2022 by margin MAE: 0.3.

|   a (model share) |   margin MAE 2019-22 |   margin MAE 2023-25 |   total MAE 2023-25 |
|------------------:|---------------------:|---------------------:|--------------------:|
|               0   |                9.888 |                9.744 |              10.121 |
|               0.1 |                9.876 |                9.738 |              10.097 |
|               0.2 |                9.866 |                9.737 |              10.078 |
|               0.3 |                9.86  |                9.739 |              10.062 |
|               0.4 |                9.862 |                9.746 |              10.052 |
|               0.5 |                9.871 |                9.758 |              10.046 |
|               0.6 |                9.884 |                9.778 |              10.046 |
|               0.7 |                9.904 |                9.801 |              10.05  |
|               0.8 |                9.928 |                9.831 |              10.063 |
|               0.9 |                9.963 |                9.864 |              10.081 |
|               1   |               10.003 |                9.9   |              10.104 |

Bet selection is unchanged by blending (the edge is scaled, not re-ordered), so this only improves the score and the probabilities.

## 7. Closing line value

Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).
