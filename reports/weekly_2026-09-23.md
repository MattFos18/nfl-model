# Weekly run, 2026-09-23 05:07 UTC

## Steps

| step                | status   | detail                                                                                                                                                                                                   |   seconds |
|:--------------------|:---------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------:|
| pull                | ok       | [('2026-09-23T05:07:14', 'schedules', 'all', 'https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv', 'ok', 2180017, 'c6334dadf341'), ('2026-09-23T05:07:14', 'pbp', 2025, 'ht |       1.1 |
| build               | ok       | team_games (8202, 142)                                                                                                                                                                                   |     214   |
| features            | ok       | [40 rows x 8 columns]                                                                                                                                                                                    |      15   |
| verify              | ok       | Result: PASS                                                                                                                                                                                             |       0.5 |
| weather             | ok       | game_id          kickoff_et  ... precip        fetched_at                                                                                                                                                |     147.2 |
|                     |          | 0    2026_03_ATL_GB 2026-09-24 20:15:00  ...    0.0  2026-09-23 01:11                                                                                                                                    |           |
|                     |          | 1   2026_03_LAC_BUF 2026-09-27 13:00:00  ...    0.0  2026-09                                                                                                                                             |           |
| ratings             | ok       | (7668, 49)                                                                                                                                                                                               |      25.5 |
| trends              | ok       | head-to-head cover margin      96                 0.355         7.079            2.793                                                                                                                   |      55.6 |
| players             | ok       | max           0.104502         1.357485    14.000000                                                                                                                                                     |     112.7 |
| positions           | ok       | Skill    518.0  0.004324  0.00080  0.0531                                                                                                                                                                |      11.7 |
| model               | ok       | neutral            0.074       0.133          0.010                                                                                                                                                      |      18.8 |
| picks               | ok       | game_id  season  week  ...     bet_p bet_odds stake_pct                                                                                                                                                  |       0.2 |
|                     |          | 3060   2026_03_ATL_GB    2026     3  ...       NaN      NaN       NaN                                                                                                                                    |           |
|                     |          | 3061  2026_03_LAC_BUF    2026     3  ...       NaN      NaN                                                                                                                                              |           |
| log run             | ok       | run_at  season  week  ... spread_line  total_line        bet                                                                                                                                             |       0   |
|                     |          | 3060  2026-09-23 05:07 UTC    2026     3  ...         5.5        43.5                                                                                                                                    |           |
|                     |          | 3061  2026-09-23 05:07 UTC    2026                                                                                                                                                                       |           |
| record picks        | ok       | run_at  season  week  ... spread_edge total_edge  p_cover                                                                                                                                                |       0.1 |
|                     |          | 0  2026-09-23 05:07 UTC    2026     3  ...        4.88      -0.06    0.659                                                                                                                               |           |
|                     |          | 1  2026-09-23 05:07 UTC    2026     3  ...                                                                                                                                                               |           |
| grade               | ok       |                                                                                                                                                                                                          |       0.1 |
| tie check (sources) | ok       | True                                                                                                                                                                                                     |       0   |
| export data room    | ok       |                                                                                                                                                                                                          |      17.5 |
| tie check (page)    | ok       | True                                                                                                                                                                                                     |       0.1 |
| audit reports       | ok       | Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).                                       |       0.7 |
| legitimacy tests    | ok       | Reading: the line beats the model on the miss every season (it should; it is the market). The question the flag rests on is whether the model's disagreements with the line carry information, which the |      15.4 |

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

| Rule | Bets | Settled | Record | Units | Avg CLV |
|---|---|---|---|---|---|
| 4+ edge (the flag, bet) | 3 | 0 | nothing settled |  | +0.00 |
| shadow: 4.5+ edge | 1 | 0 | nothing settled |  | +0.00 |
| shadow: 4+ edge, model's side the underdog or pick'em | 2 | 0 | nothing settled |  | +0.00 |
| shadow: 4+ edge, weeks 1 to 13 only | 3 | 0 | nothing settled |  | +0.00 |

## Model picks (flagged at a 4+ spread edge, at the best number)

Full record: reports/track_record.md
