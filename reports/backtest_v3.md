# NFL Model 3.0 backtest

Walk-forward: every week is priced with only games played before it; the points regression is refit before every week on every played game since 2013. Ridge strength and bet thresholds were chosen on 2019 to 2022 only, and 2023 to 2025 was the held-out test for them. Since 22 Sep 2026 every new input, and the rating decay and last-season weight, is accepted only when it helps on both windows, so for those choices 2023 to 2025 is a second test window rather than an untouched one; the live season is the only fully unseen test.

## 1. Points miss (mean absolute error) against Vegas

Tuning window 2019 to 2022:

| target      |   3.0 |   Vegas close |   games |
|:------------|------:|--------------:|--------:|
| team points |  7.37 |          7.29 |    1055 |
| margin      | 10.01 |          9.89 |    1055 |
| total       | 10.53 |         10.54 |    1055 |

Held-out 2023 to 2025:

| target      |   3.0 |   Vegas close |   games |
|:------------|------:|--------------:|--------:|
| team points |  7.24 |          7.21 |     816 |
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
| [0.0, 0.3)  |  66 |       0.243 |    0.273 |
| [0.3, 0.4)  | 123 |       0.359 |    0.276 |
| [0.4, 0.5)  | 199 |       0.456 |    0.382 |
| [0.5, 0.6)  | 231 |       0.552 |    0.498 |
| [0.6, 0.7)  | 211 |       0.652 |    0.63  |
| [0.7, 1.01) | 225 |       0.774 |    0.773 |

## 2. Win probability, 2023 to 2025 (held out)

Brier score (lower is better): 3.0 0.2162, market moneyline 0.2102.

3.0 calibration:

| bin         |   n |   predicted |   actual |
|:------------|----:|------------:|---------:|
| [0.0, 0.3)  |  44 |       0.245 |    0.273 |
| [0.3, 0.4)  |  90 |       0.352 |    0.367 |
| [0.4, 0.5)  | 176 |       0.451 |    0.341 |
| [0.5, 0.6)  | 183 |       0.553 |    0.519 |
| [0.6, 0.7)  | 168 |       0.651 |    0.726 |
| [0.7, 1.01) | 155 |       0.779 |    0.774 |

## 3. Spreads: threshold sweep on the tuning window (2019 to 2022)

|   edge |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|-------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|      1 |    694 |    361 |      333 |       13 |     0.52  |    -5.3 | -0.007 |
|      2 |    440 |    235 |      205 |        5 |     0.534 |     9.5 |  0.02  |
|      3 |    260 |    141 |      119 |        2 |     0.542 |    10.1 |  0.035 |
|      4 |    133 |     81 |       52 |        0 |     0.609 |    23.8 |  0.163 |
|      5 |     69 |     40 |       29 |        0 |     0.58  |     8.1 |  0.107 |
|      6 |     30 |     16 |       14 |        0 |     0.533 |     0.6 |  0.018 |
|      7 |     16 |      7 |        9 |        0 |     0.438 |    -2.9 | -0.165 |
|      8 |     10 |      6 |        4 |        0 |     0.6   |     1.6 |  0.145 |

## 4. Totals: threshold sweep on the tuning window

|   edge |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|-------:|-------:|-------:|---------:|---------:|----------:|--------:|------:|
|      1 |    752 |    406 |      346 |        9 |     0.54  |    25.4 | 0.031 |
|      2 |    483 |    268 |      215 |        6 |     0.555 |    31.5 | 0.059 |
|      3 |    293 |    162 |      131 |        3 |     0.553 |    17.9 | 0.056 |
|      4 |    161 |     96 |       65 |        0 |     0.596 |    24.5 | 0.138 |
|      5 |     86 |     55 |       31 |        0 |     0.64  |    20.9 | 0.221 |
|      6 |     39 |     24 |       15 |        0 |     0.615 |     7.5 | 0.175 |
|      7 |     16 |     10 |        6 |        0 |     0.625 |     3.4 | 0.193 |
|      8 |      9 |      5 |        4 |        0 |     0.556 |     0.6 | 0.061 |

Best spread threshold with 100+ bets on the tuning window: 4 (ROI +0.163). Best total threshold: 4 (ROI +0.138). The held-out results below use the live spread flag (4; totals are not flagged, so they are graded at the tuned 4) and, separately, these.

## 5. Held-out 2023 to 2025, live flag (4 / 4)

Spreads:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|------:|
| all |     65 |     41 |       24 |        1 |     0.631 |    14.6 | 0.204 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|------:|
|     2023 |     11 |      7 |        4 |        1 |     0.636 |     2.6 | 0.215 |
|     2024 |     30 |     20 |       10 |        0 |     0.667 |     9   | 0.273 |
|     2025 |     24 |     14 |       10 |        0 |     0.583 |     3   | 0.114 |

By edge size:

| bucket      |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|:------------|-------:|-------:|---------:|---------:|----------:|--------:|------:|
| [4.0, 5.0)  |     38 |     24 |       14 |        0 |     0.632 |     8.6 | 0.206 |
| [5.0, 6.0)  |     13 |      8 |        5 |        1 |     0.615 |     2.5 | 0.175 |
| [6.0, 8.0)  |      9 |      6 |        3 |        0 |     0.667 |     2.7 | 0.273 |
| [8.0, 99.0) |      5 |      3 |        2 |        0 |     0.6   |     0.8 | 0.145 |

Totals:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|------:|
| all |    123 |     72 |       51 |        1 |     0.585 |    15.9 | 0.118 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|------:|
|     2023 |     42 |     24 |       18 |        0 |     0.571 |     4.2 | 0.091 |
|     2024 |     43 |     25 |       18 |        1 |     0.581 |     5.2 | 0.11  |
|     2025 |     38 |     23 |       15 |        0 |     0.605 |     6.5 | 0.156 |

## 5. Held-out 2023 to 2025, tuned (4 / 4)

Spreads:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|------:|
| all |     65 |     41 |       24 |        1 |     0.631 |    14.6 | 0.204 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|------:|
|     2023 |     11 |      7 |        4 |        1 |     0.636 |     2.6 | 0.215 |
|     2024 |     30 |     20 |       10 |        0 |     0.667 |     9   | 0.273 |
|     2025 |     24 |     14 |       10 |        0 |     0.583 |     3   | 0.114 |

By edge size:

| bucket      |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|:------------|-------:|-------:|---------:|---------:|----------:|--------:|------:|
| [4.0, 5.0)  |     38 |     24 |       14 |        0 |     0.632 |     8.6 | 0.206 |
| [5.0, 6.0)  |     13 |      8 |        5 |        1 |     0.615 |     2.5 | 0.175 |
| [6.0, 8.0)  |      9 |      6 |        3 |        0 |     0.667 |     2.7 | 0.273 |
| [8.0, 99.0) |      5 |      3 |        2 |        0 |     0.6   |     0.8 | 0.145 |

Totals:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|------:|
| all |    123 |     72 |       51 |        1 |     0.585 |    15.9 | 0.118 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|------:|
|     2023 |     42 |     24 |       18 |        0 |     0.571 |     4.2 | 0.091 |
|     2024 |     43 |     25 |       18 |        1 |     0.581 |     5.2 | 0.11  |
|     2025 |     38 |     23 |       15 |        0 |     0.605 |     6.5 | 0.156 |

## 6. Market plus model

Blend the model line with the closing line, pred = a x model + (1 - a) x line. Best a on 2019 to 2022 by margin MAE: 0.3.

|   a (model share) |   margin MAE 2019-22 |   margin MAE 2023-25 |   total MAE 2023-25 |
|------------------:|---------------------:|---------------------:|--------------------:|
|               0   |                9.888 |                9.744 |              10.121 |
|               0.1 |                9.878 |                9.74  |              10.098 |
|               0.2 |                9.869 |                9.74  |              10.078 |
|               0.3 |                9.865 |                9.745 |              10.064 |
|               0.4 |                9.868 |                9.752 |              10.053 |
|               0.5 |                9.878 |                9.765 |              10.048 |
|               0.6 |                9.892 |                9.783 |              10.046 |
|               0.7 |                9.913 |                9.807 |              10.053 |
|               0.8 |                9.939 |                9.837 |              10.064 |
|               0.9 |                9.971 |                9.87  |              10.08  |
|               1   |               10.012 |                9.907 |              10.104 |

Bet selection is unchanged by blending (the edge is scaled, not re-ordered), so this only improves the score and the probabilities.

## 7. Closing line value

Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).
