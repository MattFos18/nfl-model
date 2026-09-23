# Weekly run, 2026-09-23 14:55 UTC

## Steps

| step                | status   | detail                                                                                                                                                                                                   |   seconds |
|:--------------------|:---------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------:|
| build               | ok       | team_games (8202, 142)                                                                                                                                                                                   |     214.6 |
| features            | ok       | [40 rows x 8 columns]                                                                                                                                                                                    |      22.1 |
| verify              | ok       | Result: PASS                                                                                                                                                                                             |       0.6 |
| ratings             | ok       | (7668, 49)                                                                                                                                                                                               |      29.2 |
| trends              | ok       | head-to-head cover margin      96                 0.355         7.079            2.793                                                                                                                   |      90.4 |
| players             | ok       | max           0.104502         1.357485    14.000000                                                                                                                                                     |     212.1 |
| positions           | ok       | Skill    525.0  0.004309  0.0008  0.0531                                                                                                                                                                 |      21   |
| model               | ok       | neutral            0.074       0.133          0.010                                                                                                                                                      |      27.4 |
| picks               | ok       | game_id  season  week  ...     bet_p bet_odds stake_pct                                                                                                                                                  |       0.3 |
|                     |          | 3060   2026_03_ATL_GB    2026     3  ...       NaN      NaN       NaN                                                                                                                                    |           |
|                     |          | 3061  2026_03_LAC_BUF    2026     3  ...       NaN      NaN                                                                                                                                              |           |
| log run             | ok       | run_at  season  week  ... spread_line  total_line        bet                                                                                                                                             |       0   |
|                     |          | 3060  2026-09-23 14:55 UTC    2026     3  ...         5.5        43.5                                                                                                                                    |           |
|                     |          | 3061  2026-09-23 14:55 UTC    2026                                                                                                                                                                       |           |
| record picks        | ok       | run_at  season  week  ... spread_edge total_edge  p_cover                                                                                                                                                |       0.1 |
|                     |          | 0  2026-09-23 14:55 UTC    2026     3  ...        4.88      -0.06    0.659                                                                                                                               |           |
|                     |          | 1  2026-09-23 14:55 UTC    2026     3  ...                                                                                                                                                               |           |
| grade               | ok       |                                                                                                                                                                                                          |       0.2 |
| tie check (sources) | error    | RuntimeError: numbers disagree: see reports/tie_check.md                                                                                                                                                 |       0.1 |
| export data room    | ok       |                                                                                                                                                                                                          |      22.7 |
| tie check (page)    | error    | RuntimeError: page files disagree with the sources: see reports/tie_check.md                                                                                                                             |       0.2 |
| audit reports       | ok       | Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).                                       |       0.9 |
| legitimacy tests    | ok       | Reading: the line beats the model on the miss every season (it should; it is the market). The question the flag rests on is whether the model's disagreements with the line carry information, which the |      22.7 |

**Failed steps above were skipped, not filled with stale data.**

## Week 3, 2026: 3 flagged of 16 games

| away_team   | home_team   |   away_exp |   home_exp |   spread_line |   total_line |   spread_edge |   total_edge | bet       |   stake_pct |
|:------------|:------------|-----------:|-----------:|--------------:|-------------:|--------------:|-------------:|:----------|------------:|
| KC          | MIA         |      27.39 |      20.77 |         -11.5 |         46.5 |          4.88 |        -0.06 | MIA +11.5 |        0.97 |
| TEN         | NYG         |      18.91 |      25.74 |           2.5 |         39.5 |          4.32 |         4.95 | NYG -2.5  |        0.63 |
| CIN         | PIT         |      22.75 |      23.42 |          -3.5 |         42.5 |          4.17 |         4.28 | PIT +3.5  |        0.54 |

Full table: reports/picks_2026_wk3.md

## Track record

## Rules compared

The flag is bet; the shadows are logged and graded on the same games but never bet, so the rule can be chosen on live results.

Backtest columns: the same rule on the three backtest windows, regular season weeks 1 to 17 (`picks.rule_records`).

| Rule | Bets | Settled | Record | Units | Avg CLV | Backtest 2015-18 | Backtest 2019-22 | Backtest 2023-25 |
|---|---|---|---|---|---|---|---|---|
| 4+ edge (the flag, bet) | 3 | 0 | nothing settled |  | +0.00 | 67-57 | 87-59 | 45-21 |
| shadow: 4.5+ edge | 1 | 0 | nothing settled |  | +0.00 | 41-42 | 65-44 | 32-15 |
| shadow: 4+ edge, model's side the underdog or pick'em | 2 | 0 | nothing settled |  | +0.00 | 49-36 | 78-45 | 34-17 |
| shadow: 4+ edge, weeks 1 to 13 only | 3 | 0 | nothing settled |  | +0.00 | 54-42 | 71-41 | 34-16 |

Full record: reports/track_record.md
