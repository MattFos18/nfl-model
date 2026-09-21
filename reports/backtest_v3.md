# NFL Model 3.0 backtest

Walk-forward: every week is priced with only games played before it; the points regression is refit each season on all prior seasons from 2013. Rating parameters, ridge strength and bet thresholds were chosen on 2019 to 2022 only. 2023 to 2025 is the held-out test the tuning never saw.

## 1. Points miss (mean absolute error) against the old model and Vegas

Tuning window 2019 to 2022:

| target      |   3.0 |   old model |   Vegas close |   games |
|:------------|------:|------------:|--------------:|--------:|
| team points |  7.47 |        9.18 |          7.29 |    1055 |
| margin      | 10.16 |       12.84 |          9.89 |    1055 |
| total       | 10.74 |       13.08 |         10.54 |    1055 |

Held-out 2023 to 2025:

| target      |   3.0 |   old model |   Vegas close |   games |
|:------------|------:|------------:|--------------:|--------:|
| team points |  7.34 |        9.02 |          7.21 |     816 |
| margin      | 10.16 |       12.66 |          9.74 |     816 |
| total       | 10.32 |       12.8  |         10.12 |     816 |

Held-out, Week 5 on:

| target      |   3.0 |   old model |   Vegas close |   games |
|:------------|------:|------------:|--------------:|--------:|
| team points |  7.35 |        8.55 |          7.19 |     624 |
| margin      | 10.08 |       11.92 |          9.59 |     624 |
| total       | 10.3  |       12.12 |         10.09 |     624 |

## 2. Win probability, 2019 to 2022 (tuning)

Brier score (lower is better): 3.0 0.2221, old model 0.2976, market moneyline 0.2111.

3.0 calibration:

| bin         |   n |   predicted |   actual |
|:------------|----:|------------:|---------:|
| [0.0, 0.3)  |  67 |       0.238 |    0.239 |
| [0.3, 0.4)  | 106 |       0.355 |    0.302 |
| [0.4, 0.5)  | 180 |       0.455 |    0.406 |
| [0.5, 0.6)  | 251 |       0.551 |    0.458 |
| [0.6, 0.7)  | 222 |       0.646 |    0.608 |
| [0.7, 1.01) | 229 |       0.772 |    0.782 |

Old model calibration (the Poisson grid problem):

| bin         |   n |   predicted |   actual |
|:------------|----:|------------:|---------:|
| [0.0, 0.3)  | 406 |       0.087 |    0.387 |
| [0.3, 0.4)  |  55 |       0.353 |    0.473 |
| [0.4, 0.5)  |  70 |       0.444 |    0.543 |
| [0.5, 0.6)  |  65 |       0.553 |    0.492 |
| [0.6, 0.7)  |  59 |       0.65  |    0.576 |
| [0.7, 1.01) | 400 |       0.909 |    0.658 |

## 2. Win probability, 2023 to 2025 (held out)

Brier score (lower is better): 3.0 0.2204, old model 0.2943, market moneyline 0.2102.

3.0 calibration:

| bin         |   n |   predicted |   actual |
|:------------|----:|------------:|---------:|
| [0.0, 0.3)  |  52 |       0.236 |    0.327 |
| [0.3, 0.4)  |  88 |       0.359 |    0.341 |
| [0.4, 0.5)  | 165 |       0.455 |    0.37  |
| [0.5, 0.6)  | 180 |       0.549 |    0.517 |
| [0.6, 0.7)  | 167 |       0.651 |    0.665 |
| [0.7, 1.01) | 164 |       0.785 |    0.793 |

Old model calibration (the Poisson grid problem):

| bin         |   n |   predicted |   actual |
|:------------|----:|------------:|---------:|
| [0.0, 0.3)  | 310 |       0.092 |    0.384 |
| [0.3, 0.4)  |  49 |       0.352 |    0.51  |
| [0.4, 0.5)  |  38 |       0.452 |    0.658 |
| [0.5, 0.6)  |  50 |       0.55  |    0.58  |
| [0.6, 0.7)  |  39 |       0.65  |    0.667 |
| [0.7, 1.01) | 330 |       0.914 |    0.661 |

## 3. Spreads: threshold sweep on the tuning window (2019 to 2022)

|   edge |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|-------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|      1 |    703 |    353 |      350 |       13 |     0.502 |   -32   | -0.041 |
|      2 |    459 |    240 |      219 |        9 |     0.523 |    -0.9 | -0.002 |
|      3 |    250 |    128 |      122 |        6 |     0.512 |    -6.2 | -0.023 |
|      4 |    148 |     76 |       72 |        4 |     0.514 |    -3.2 | -0.02  |
|      5 |     69 |     37 |       32 |        1 |     0.536 |     1.8 |  0.024 |
|      6 |     34 |     21 |       13 |        1 |     0.618 |     6.7 |  0.179 |
|      7 |     24 |     15 |        9 |        1 |     0.625 |     5.1 |  0.193 |
|      8 |     16 |      9 |        7 |        1 |     0.562 |     1.3 |  0.074 |

## 4. Totals: threshold sweep on the tuning window

|   edge |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|-------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|      1 |    760 |    379 |      381 |        9 |     0.499 |   -40.1 | -0.048 |
|      2 |    508 |    259 |      249 |        7 |     0.51  |   -14.9 | -0.027 |
|      3 |    296 |    158 |      138 |        4 |     0.534 |     6.2 |  0.019 |
|      4 |    167 |     85 |       82 |        1 |     0.509 |    -5.2 | -0.028 |
|      5 |     92 |     45 |       47 |        0 |     0.489 |    -6.7 | -0.066 |
|      6 |     35 |     20 |       15 |        0 |     0.571 |     3.5 |  0.091 |
|      7 |     15 |      9 |        6 |        0 |     0.6   |     2.4 |  0.145 |
|      8 |      8 |      4 |        4 |        0 |     0.5   |    -0.4 | -0.045 |

Best spread threshold with 100+ bets on the tuning window: 2 (ROI -0.002). Best total threshold: 3 (ROI +0.019). The held-out results below use the sheet's 3 and 4 and, separately, these.

## 5. Held-out 2023 to 2025, sheet rules (3 / 4)

Spreads:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
| all |    214 |    107 |      107 |        2 |       0.5 |   -10.7 | -0.045 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|     2023 |     73 |     37 |       36 |        2 |     0.507 |    -2.6 | -0.032 |
|     2024 |     73 |     40 |       33 |        0 |     0.548 |     3.7 |  0.046 |
|     2025 |     68 |     30 |       38 |        0 |     0.441 |   -11.8 | -0.158 |

By edge size:

| bucket      |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|:------------|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
| [3.0, 4.0)  |    105 |     53 |       52 |        0 |     0.505 |    -4.2 | -0.036 |
| [4.0, 5.0)  |     47 |     20 |       27 |        0 |     0.426 |    -9.7 | -0.188 |
| [5.0, 7.0)  |     49 |     28 |       21 |        2 |     0.571 |     4.9 |  0.091 |
| [7.0, 99.0) |     13 |      6 |        7 |        0 |     0.462 |    -1.7 | -0.119 |

Totals:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
| all |    136 |     71 |       65 |        2 |     0.522 |    -0.5 | -0.003 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|     2023 |     54 |     26 |       28 |        1 |     0.481 |    -4.8 | -0.081 |
|     2024 |     44 |     24 |       20 |        1 |     0.545 |     2   |  0.041 |
|     2025 |     38 |     21 |       17 |        0 |     0.553 |     2.3 |  0.055 |

Old model on the same seasons and rules:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi | kind    |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|-------:|:--------|
| all |    596 |    307 |      289 |       13 |     0.515 |   -10.9 | -0.017 | spreads |
| all |    520 |    258 |      262 |        4 |     0.496 |   -30.2 | -0.053 | totals  |

## 5. Held-out 2023 to 2025, tuned (2 / 3)

Spreads:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
| all |    374 |    184 |      190 |        6 |     0.492 |     -25 | -0.061 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|     2023 |    120 |     62 |       58 |        5 |     0.517 |    -1.8 | -0.014 |
|     2024 |    128 |     63 |       65 |        1 |     0.492 |    -8.5 | -0.06  |
|     2025 |    126 |     59 |       67 |        0 |     0.468 |   -14.7 | -0.106 |

By edge size:

| bucket      |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|:------------|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
| [2.0, 3.0)  |    160 |     77 |       83 |        4 |     0.481 |   -14.3 | -0.081 |
| [3.0, 4.0)  |    105 |     53 |       52 |        0 |     0.505 |    -4.2 | -0.036 |
| [4.0, 6.0)  |     78 |     36 |       42 |        1 |     0.462 |   -10.2 | -0.119 |
| [6.0, 99.0) |     31 |     18 |       13 |        1 |     0.581 |     3.7 |  0.109 |

Totals:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
| all |    246 |    121 |      125 |        2 |     0.492 |   -16.5 | -0.061 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|     2023 |     99 |     44 |       55 |        1 |     0.444 |   -16.5 | -0.152 |
|     2024 |     78 |     38 |       40 |        1 |     0.487 |    -6   | -0.07  |
|     2025 |     69 |     39 |       30 |        0 |     0.565 |     6   |  0.079 |

Old model on the same seasons and rules:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi | kind    |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|-------:|:--------|
| all |    684 |    350 |      334 |       13 |     0.512 |   -17.4 | -0.023 | spreads |
| all |    586 |    289 |      297 |        4 |     0.493 |   -37.7 | -0.058 | totals  |

## 6. Market plus model

Blend the model line with the closing line, pred = a x model + (1 - a) x line. Best a on 2019 to 2022 by margin MAE: 0.1.

|   a (model share) |   margin MAE 2019-22 |   margin MAE 2023-25 |   total MAE 2023-25 |
|------------------:|---------------------:|---------------------:|--------------------:|
|               0   |                9.888 |                9.744 |              10.121 |
|               0.1 |                9.887 |                9.753 |              10.12  |
|               0.2 |                9.891 |                9.772 |              10.123 |
|               0.3 |                9.904 |                9.802 |              10.13  |
|               0.4 |                9.926 |                9.841 |              10.143 |
|               0.5 |                9.956 |                9.886 |              10.161 |
|               0.6 |                9.99  |                9.933 |              10.185 |
|               0.7 |               10.027 |                9.983 |              10.213 |
|               0.8 |               10.068 |               10.037 |              10.242 |
|               0.9 |               10.112 |               10.098 |              10.277 |
|               1   |               10.16  |               10.161 |              10.318 |

Bet selection is unchanged by blending (the edge is scaled, not re-ordered), so this only improves the score and the probabilities.

## 7. Closing line value

Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).
