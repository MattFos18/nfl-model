# Weekly run, 2026-09-23 22:55 UTC

## Steps

| step                | status   | detail                                                                                                                                                                                                   |   seconds |
|:--------------------|:---------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------:|
| pull                | ok       | [('2026-09-23T22:55:35', 'schedules', 'all', 'https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv', 'ok', 2180730, 'd4aac59013f7'), ('2026-09-23T22:55:35', 'pbp', 2025, 'ht |       3.5 |
| build               | ok       | team_games (8202, 142)                                                                                                                                                                                   |     232.3 |
| features            | ok       | [40 rows x 8 columns]                                                                                                                                                                                    |      15.2 |
| verify              | ok       | Result: PASS                                                                                                                                                                                             |       0.6 |
| weather             | ok       | game_id          kickoff_et  ... precip        fetched_at                                                                                                                                                |     147.5 |
|                     |          | 0    2026_03_ATL_GB 2026-09-24 20:15:00  ...    0.0  2026-09-23 18:59                                                                                                                                    |           |
|                     |          | 1   2026_03_LAC_BUF 2026-09-27 13:00:00  ...    0.0  2026-09                                                                                                                                             |           |
| ratings             | ok       | (7668, 49)                                                                                                                                                                                               |      26   |
| trends              | ok       | head-to-head cover margin      96                 0.355         7.079            2.793                                                                                                                   |      64.4 |
| players             | ok       | max           0.104502         1.357485    14.000000                                                                                                                                                     |     158   |
| positions           | ok       | Skill    525.0  0.004309  0.0008  0.0531                                                                                                                                                                 |      14.5 |
| scheme              | ok       | scheme_plays (348655, 77) profiles for 32 teams as of 2026 3                                                                                                                                             |       6.1 |
| props               | ok       | props 2854 projections for week 3 graded rows 0 market lines on the cards 369 graded against the market 0                                                                                                |      17.1 |
| model               | ok       | neutral            0.074       0.133          0.010                                                                                                                                                      |      26.8 |
| picks               | ok       | game_id  season  week  ...     bet_p bet_odds stake_pct                                                                                                                                                  |       0.3 |
|                     |          | 3060   2026_03_ATL_GB    2026     3  ...       NaN      NaN       NaN                                                                                                                                    |           |
|                     |          | 3061  2026_03_LAC_BUF    2026     3  ...       NaN      NaN                                                                                                                                              |           |
| log run             | ok       | run_at  season  week  ... spread_line  total_line        bet                                                                                                                                             |       0   |
|                     |          | 3060  2026-09-23 22:55 UTC    2026     3  ...         5.5        42.5                                                                                                                                    |           |
|                     |          | 3061  2026-09-23 22:55 UTC    2026                                                                                                                                                                       |           |
| record picks        | ok       | run_at  season  week  ... spread_edge total_edge  p_cover                                                                                                                                                |       0.1 |
|                     |          | 0  2026-09-23 22:55 UTC    2026     3  ...        4.88       0.88    0.659                                                                                                                               |           |
|                     |          | 1  2026-09-23 22:55 UTC    2026     3  ...                                                                                                                                                               |           |
| grade               | ok       |                                                                                                                                                                                                          |       0.2 |
| tie check (sources) | ok       | True                                                                                                                                                                                                     |       0.2 |
| export data room    | ok       |                                                                                                                                                                                                          |      20.4 |
| tie check (page)    | ok       | True                                                                                                                                                                                                     |       1   |
| audit reports       | ok       | Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).                                       |       0.7 |
| legitimacy tests    | ok       | Reading: the line beats the model on the miss every season (it should; it is the market). The question the flag rests on is whether the model's disagreements with the line carry information, which the |      16.9 |

## Week 3, 2026: 4 flagged of 16 games

| away_team   | home_team   |   away_exp |   home_exp |   spread_line |   total_line |   spread_edge |   total_edge | bet       |   stake_pct |
|:------------|:------------|-----------:|-----------:|--------------:|-------------:|--------------:|-------------:|:----------|------------:|
| KC          | MIA         |      27.86 |      21.24 |         -11.5 |         46.5 |          4.88 |         0.88 | MIA +11.5 |        0.97 |
| TEN         | NYG         |      18.63 |      25.71 |           2.5 |         39.5 |          4.58 |         4.63 | NYG -2.5  |        0.79 |
| CIN         | PIT         |      22.84 |      23.61 |          -3.5 |         42.5 |          4.27 |         4.58 | PIT +3.5  |        0.6  |
| PHI         | CHI         |      23.77 |      23.54 |          -4.5 |         41.5 |          4.27 |         4.27 | CHI +4.5  |        0.6  |

Full table: reports/picks_2026_wk3.md

## Track record

## Rules compared

The flag is bet; the shadows are logged and graded on the same games but never bet, so the rule can be chosen on live results.

Backtest columns: the same rule on the three backtest windows, regular season weeks 1 to 17 (`picks.rule_records`).

| Rule | Bets | Settled | Record | Units | Avg CLV | Backtest 2015-18 | Backtest 2019-22 | Backtest 2023-25 |
|---|---|---|---|---|---|---|---|---|
| 4+ edge (the flag, bet) | 4 | 0 | nothing settled |  | +0.00 | 67-57 | 87-59 | 45-21 |
| shadow: 4.5+ edge | 2 | 0 | nothing settled |  | +0.00 | 41-42 | 65-44 | 32-15 |
| shadow: 4+ edge, model's side the underdog or pick'em | 3 | 0 | nothing settled |  | +0.00 | 49-36 | 78-45 | 34-17 |
| shadow: 4+ edge, weeks 1 to 13 only | 4 | 0 | nothing settled |  | +0.00 | 54-42 | 71-41 | 34-16 |

Full record: reports/track_record.md
