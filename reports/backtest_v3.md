# NFL Model 3.0 backtest

Walk-forward: every week is priced with only games played before it; the points regression is refit each season on all prior seasons from 2013. Rating parameters, ridge strength and bet thresholds were chosen on 2019 to 2022 only. 2023 to 2025 is the held-out test the tuning never saw.

## 1. Points miss (mean absolute error) against the old model and Vegas

Tuning window 2019 to 2022:

| target      |   3.0 |   old model |   Vegas close |   games |
|:------------|------:|------------:|--------------:|--------:|
| team points |  7.46 |        9.16 |          7.29 |    1055 |
| margin      | 10.16 |       12.83 |          9.89 |    1055 |
| total       | 10.73 |       13.05 |         10.54 |    1055 |

Held-out 2023 to 2025:

| target      |   3.0 |   old model |   Vegas close |   games |
|:------------|------:|------------:|--------------:|--------:|
| team points |  7.35 |        9    |          7.21 |     816 |
| margin      | 10.16 |       12.61 |          9.74 |     816 |
| total       | 10.35 |       12.75 |         10.12 |     816 |

Held-out, Week 5 on:

| target      |   3.0 |   old model |   Vegas close |   games |
|:------------|------:|------------:|--------------:|--------:|
| team points |  7.35 |        8.54 |          7.19 |     624 |
| margin      | 10.06 |       11.87 |          9.59 |     624 |
| total       | 10.31 |       12.09 |         10.09 |     624 |

## 2. Win probability, 2019 to 2022 (tuning)

Brier score (lower is better): 3.0 0.2217, old model 0.2973, market moneyline 0.2111.

3.0 calibration:

| bin         |   n |   predicted |   actual |
|:------------|----:|------------:|---------:|
| [0.0, 0.3)  |  68 |       0.239 |    0.235 |
| [0.3, 0.4)  | 105 |       0.354 |    0.305 |
| [0.4, 0.5)  | 180 |       0.455 |    0.406 |
| [0.5, 0.6)  | 252 |       0.551 |    0.448 |
| [0.6, 0.7)  | 221 |       0.646 |    0.615 |
| [0.7, 1.01) | 229 |       0.774 |    0.786 |

Old model calibration (the Poisson grid problem):

| bin         |   n |   predicted |   actual |
|:------------|----:|------------:|---------:|
| [0.0, 0.3)  | 394 |       0.081 |    0.381 |
| [0.3, 0.4)  |  75 |       0.356 |    0.52  |
| [0.4, 0.5)  |  64 |       0.455 |    0.5   |
| [0.5, 0.6)  |  65 |       0.552 |    0.554 |
| [0.6, 0.7)  |  60 |       0.652 |    0.517 |
| [0.7, 1.01) | 397 |       0.914 |    0.66  |

## 2. Win probability, 2023 to 2025 (held out)

Brier score (lower is better): 3.0 0.2204, old model 0.2922, market moneyline 0.2102.

3.0 calibration:

| bin         |   n |   predicted |   actual |
|:------------|----:|------------:|---------:|
| [0.0, 0.3)  |  59 |       0.241 |    0.322 |
| [0.3, 0.4)  |  78 |       0.362 |    0.346 |
| [0.4, 0.5)  | 172 |       0.456 |    0.372 |
| [0.5, 0.6)  | 173 |       0.55  |    0.526 |
| [0.6, 0.7)  | 168 |       0.65  |    0.655 |
| [0.7, 1.01) | 166 |       0.785 |    0.789 |

Old model calibration (the Poisson grid problem):

| bin         |   n |   predicted |   actual |
|:------------|----:|------------:|---------:|
| [0.0, 0.3)  | 308 |       0.09  |    0.383 |
| [0.3, 0.4)  |  51 |       0.353 |    0.549 |
| [0.4, 0.5)  |  37 |       0.449 |    0.595 |
| [0.5, 0.6)  |  49 |       0.556 |    0.551 |
| [0.6, 0.7)  |  42 |       0.651 |    0.714 |
| [0.7, 1.01) | 329 |       0.914 |    0.66  |

## 3. Spreads: threshold sweep on the tuning window (2019 to 2022)

|   edge |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|-------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|      1 |    711 |    354 |      357 |       13 |     0.498 |   -38.7 | -0.049 |
|      2 |    458 |    237 |      221 |       10 |     0.517 |    -6.1 | -0.012 |
|      3 |    247 |    124 |      123 |        7 |     0.502 |   -11.3 | -0.042 |
|      4 |    136 |     70 |       66 |        5 |     0.515 |    -2.6 | -0.017 |
|      5 |     68 |     37 |       31 |        1 |     0.544 |     2.9 |  0.039 |
|      6 |     32 |     21 |       11 |        1 |     0.656 |     8.9 |  0.253 |
|      7 |     20 |     13 |        7 |        1 |     0.65  |     5.3 |  0.241 |
|      8 |     13 |      8 |        5 |        1 |     0.615 |     2.5 |  0.175 |

## 4. Totals: threshold sweep on the tuning window

|   edge |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|-------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|      1 |    761 |    381 |      380 |        9 |     0.501 |   -37   | -0.044 |
|      2 |    518 |    262 |      256 |        6 |     0.506 |   -19.6 | -0.034 |
|      3 |    296 |    159 |      137 |        3 |     0.537 |     8.3 |  0.025 |
|      4 |    167 |     86 |       81 |        1 |     0.515 |    -3.1 | -0.017 |
|      5 |     97 |     49 |       48 |        0 |     0.505 |    -3.8 | -0.036 |
|      6 |     39 |     23 |       16 |        0 |     0.59  |     5.4 |  0.126 |
|      7 |     17 |      9 |        8 |        0 |     0.529 |     0.2 |  0.011 |
|      8 |      7 |      4 |        3 |        0 |     0.571 |     0.7 |  0.091 |

Best spread threshold with 100+ bets on the tuning window: 2 (ROI -0.012). Best total threshold: 3 (ROI +0.025). The held-out results below use the sheet's 3 and 4 and, separately, these.

## 5. Held-out 2023 to 2025, sheet rules (3 / 4)

Spreads:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
| all |    214 |    109 |      105 |        2 |     0.509 |    -6.5 | -0.028 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|     2023 |     71 |     36 |       35 |        2 |     0.507 |    -2.5 | -0.032 |
|     2024 |     75 |     43 |       32 |        0 |     0.573 |     7.8 |  0.095 |
|     2025 |     68 |     30 |       38 |        0 |     0.441 |   -11.8 | -0.158 |

By edge size:

| bucket      |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|:------------|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
| [3.0, 4.0)  |    106 |     56 |       50 |        0 |     0.528 |     1   |  0.009 |
| [4.0, 5.0)  |     49 |     22 |       27 |        0 |     0.449 |    -7.7 | -0.143 |
| [5.0, 7.0)  |     46 |     25 |       21 |        2 |     0.543 |     1.9 |  0.038 |
| [7.0, 99.0) |     13 |      6 |        7 |        0 |     0.462 |    -1.7 | -0.119 |

Totals:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
| all |    129 |     65 |       64 |        2 |     0.504 |    -5.4 | -0.038 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|     2023 |     52 |     24 |       28 |        1 |     0.462 |    -6.8 | -0.119 |
|     2024 |     44 |     24 |       20 |        1 |     0.545 |     2   |  0.041 |
|     2025 |     33 |     17 |       16 |        0 |     0.515 |    -0.6 | -0.017 |

Old model on the same seasons and rules:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi | kind    |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|-------:|:--------|
| all |    605 |    315 |      290 |       11 |     0.521 |    -4   | -0.006 | spreads |
| all |    513 |    254 |      259 |        4 |     0.495 |   -30.9 | -0.055 | totals  |

## 5. Held-out 2023 to 2025, tuned (2 / 3)

Spreads:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
| all |    368 |    184 |      184 |        6 |       0.5 |   -18.4 | -0.045 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|     2023 |    120 |     62 |       58 |        5 |     0.517 |    -1.8 | -0.014 |
|     2024 |    130 |     66 |       64 |        1 |     0.508 |    -4.4 | -0.031 |
|     2025 |    118 |     56 |       62 |        0 |     0.475 |   -12.2 | -0.094 |

By edge size:

| bucket      |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|:------------|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
| [2.0, 3.0)  |    154 |     75 |       79 |        4 |     0.487 |   -11.9 | -0.07  |
| [3.0, 4.0)  |    106 |     56 |       50 |        0 |     0.528 |     1   |  0.009 |
| [4.0, 6.0)  |     79 |     37 |       42 |        1 |     0.468 |    -9.2 | -0.106 |
| [6.0, 99.0) |     29 |     16 |       13 |        1 |     0.552 |     1.7 |  0.053 |

Totals:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
| all |    240 |    116 |      124 |        2 |     0.483 |   -20.4 | -0.077 |

|   season |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi |
|---------:|-------:|-------:|---------:|---------:|----------:|--------:|-------:|
|     2023 |     94 |     40 |       54 |        1 |     0.426 |   -19.4 | -0.188 |
|     2024 |     76 |     38 |       38 |        1 |     0.5   |    -3.8 | -0.045 |
|     2025 |     70 |     38 |       32 |        0 |     0.543 |     2.8 |  0.036 |

Old model on the same seasons and rules:

|     |   bets |   wins |   losses |   pushes |   win_pct |   units |    roi | kind    |
|:----|-------:|-------:|---------:|---------:|----------:|--------:|-------:|:--------|
| all |    676 |    345 |      331 |       14 |     0.51  |   -19.1 | -0.026 | spreads |
| all |    590 |    291 |      299 |        4 |     0.493 |   -37.9 | -0.058 | totals  |

## 6. Market plus model

Blend the model line with the closing line, pred = a x model + (1 - a) x line. Best a on 2019 to 2022 by margin MAE: 0.1.

|   a (model share) |   margin MAE 2019-22 |   margin MAE 2023-25 |   total MAE 2023-25 |
|------------------:|---------------------:|---------------------:|--------------------:|
|               0   |                9.888 |                9.744 |              10.121 |
|               0.1 |                9.888 |                9.754 |              10.123 |
|               0.2 |                9.893 |                9.774 |              10.129 |
|               0.3 |                9.904 |                9.802 |              10.138 |
|               0.4 |                9.926 |                9.841 |              10.154 |
|               0.5 |                9.955 |                9.886 |              10.175 |
|               0.6 |                9.989 |                9.933 |              10.202 |
|               0.7 |               10.026 |                9.983 |              10.231 |
|               0.8 |               10.067 |               10.035 |              10.264 |
|               0.9 |               10.112 |               10.094 |              10.302 |
|               1   |               10.161 |               10.156 |              10.346 |

Bet selection is unchanged by blending (the edge is scaled, not re-ordered), so this only improves the score and the probabilities.

## 7. Closing line value

Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).
