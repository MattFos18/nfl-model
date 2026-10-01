# NFL Model 3.0 backtest

Walk-forward: every week is priced with only games played before it; the points regression is refit before every week on every played game since 2013. Ridge strength and bet thresholds were chosen on 2019 to 2022 only, and 2023 to 2025 was the held-out test for them. Since 22 Sep 2026 every new input, and the rating decay and last-season weight, is accepted only when it helps on both windows, so for those choices 2023 to 2025 is a second test window rather than an untouched one; the live season is the only fully unseen test.

## 1. Points miss (mean absolute error) against Vegas

Tuning window 2019 to 2022:

| target      |   3.0 |   Vegas close |   games |
|:------------|------:|--------------:|--------:|
| team points |  7.33 |          7.29 |    1055 |
| margin      | 10.02 |          9.89 |    1055 |
| total       | 10.51 |         10.54 |    1055 |

Held-out 2023 to 2025:

| target      |   3.0 |   Vegas close |   games |
|:------------|------:|--------------:|--------:|
| team points |  7.24 |          7.21 |     816 |
| margin      |  9.9  |          9.74 |     816 |
| total       | 10.12 |         10.12 |     816 |

Held-out, Week 5 on:

| target      |   3.0 |   Vegas close |   games |
|:------------|------:|--------------:|--------:|
| team points |  7.26 |          7.19 |     624 |
| margin      |  9.82 |          9.59 |     624 |
| total       | 10.11 |         10.09 |     624 |

## 2. Win probability, 2019 to 2022 (tuning)

Brier score (lower is better): 3.0 0.2185, market moneyline 0.2111.

3.0 calibration:

| bin         |   n |   predicted |   actual |
|:------------|----:|------------:|---------:|
| [0.0, 0.3)  |  66 |       0.244 |    0.273 |
| [0.3, 0.4)  | 126 |       0.36  |    0.286 |
| [0.4, 0.5)  | 196 |       0.456 |    0.378 |
| [0.5, 0.6)  | 226 |       0.552 |    0.5   |
| [0.6, 0.7)  | 216 |       0.651 |    0.62  |
| [0.7, 1.01) | 225 |       0.775 |    0.778 |

## 2. Win probability, 2023 to 2025 (held out)

Brier score (lower is better): 3.0 0.2161, market moneyline 0.2102.

3.0 calibration:

| bin         |   n |   predicted |   actual |
|:------------|----:|------------:|---------:|
| [0.0, 0.3)  |  44 |       0.249 |    0.295 |
| [0.3, 0.4)  |  87 |       0.351 |    0.356 |
| [0.4, 0.5)  | 179 |       0.45  |    0.341 |
| [0.5, 0.6)  | 183 |       0.552 |    0.525 |
| [0.6, 0.7)  | 165 |       0.65  |    0.721 |
| [0.7, 1.01) | 158 |       0.776 |    0.772 |

## 3. Spreads: threshold sweep on the tuning window (2019 to 2022)

|   edge |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|-------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|      1 |    693 |    357 |      336 |       14 |     0.515 |   -12.6 | -0.017 |
|      2 |    440 |    232 |      208 |        6 |     0.527 |     3.2 |  0.007 |
|      3 |    259 |    139 |      120 |        2 |     0.537 |     7   |  0.025 |
|      4 |    137 |     83 |       54 |        0 |     0.606 |    23.6 |  0.157 |
|      5 |     69 |     39 |       30 |        0 |     0.565 |     6   |  0.079 |
|      6 |     30 |     16 |       14 |        0 |     0.533 |     0.6 |  0.018 |
|      7 |     13 |      6 |        7 |        0 |     0.462 |    -1.7 | -0.119 |
|      8 |      9 |      5 |        4 |        0 |     0.556 |     0.6 |  0.061 |

## 4. Totals: threshold sweep on the tuning window

|   edge |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|-------:|-------:|-------:|---------:|---------:|----------:|--------:|------:|
|      1 |    750 |    401 |      349 |       10 |     0.535 |    17.1 | 0.021 |
|      2 |    491 |    270 |      221 |        3 |     0.55  |    26.9 | 0.05  |
|      3 |    298 |    180 |      118 |        1 |     0.604 |    50.2 | 0.153 |
|      4 |    157 |     99 |       58 |        0 |     0.631 |    35.2 | 0.204 |
|      5 |     79 |     51 |       28 |        0 |     0.646 |    20.2 | 0.232 |
|      6 |     40 |     30 |       10 |        0 |     0.75  |    19   | 0.432 |
|      7 |     16 |     12 |        4 |        0 |     0.75  |     7.6 | 0.432 |
|      8 |      6 |      5 |        1 |        0 |     0.833 |     3.9 | 0.591 |

Best spread threshold with 100+ bets on the tuning window: 4 (ROI +0.157). Best total threshold: 4 (ROI +0.204). The held-out results below use the live spread flag (4; totals are not flagged, so they are graded at the tuned 4) and, separately, these.

## 5. Held-out 2023 to 2025, live flag (4 / 4)

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

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|------:|
| all |    137 |     75 |       62 |        1 |     0.547 |     6.8 | 0.045 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|     2023 |     40 |     21 |       19 |        1 |     0.525 |     0.1 |  0.002 |
|     2024 |     50 |     26 |       24 |        0 |     0.52  |    -0.4 | -0.007 |
|     2025 |     47 |     28 |       19 |        0 |     0.596 |     7.1 |  0.137 |

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

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |   roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|------:|
| all |    137 |     75 |       62 |        1 |     0.547 |     6.8 | 0.045 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|     2023 |     40 |     21 |       19 |        1 |     0.525 |     0.1 |  0.002 |
|     2024 |     50 |     26 |       24 |        0 |     0.52  |    -0.4 | -0.007 |
|     2025 |     47 |     28 |       19 |        0 |     0.596 |     7.1 |  0.137 |

## 6. Market plus model

Blend the model line with the closing line, pred = a x model + (1 - a) x line. Best a on 2019 to 2022 by margin MAE: 0.3.

|   a (model share) |   margin MAE 2019-22 |   margin MAE 2023-25 |   total MAE 2023-25 |
|------------------:|---------------------:|---------------------:|--------------------:|
|               0   |                9.888 |                9.744 |              10.121 |
|               0.1 |                9.879 |                9.739 |              10.101 |
|               0.2 |                9.872 |                9.739 |              10.087 |
|               0.3 |                9.869 |                9.742 |              10.075 |
|               0.4 |                9.874 |                9.749 |              10.068 |
|               0.5 |                9.885 |                9.761 |              10.064 |
|               0.6 |                9.9   |                9.78  |              10.065 |
|               0.7 |                9.921 |                9.804 |              10.071 |
|               0.8 |                9.948 |                9.833 |              10.083 |
|               0.9 |                9.98  |                9.867 |              10.101 |
|               1   |               10.02  |                9.904 |              10.124 |

Bet selection is unchanged by blending (the edge is scaled, not re-ordered), so this only improves the score and the probabilities.

## 7. Closing line value

Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).
