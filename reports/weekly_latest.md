# Weekly run, 2026-09-23 01:58 UTC

## Steps

| step                | status   | detail                                                                                                                                                                                                   |   seconds |
|:--------------------|:---------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------:|
| pull                | ok       | [('2026-09-23T01:58:19', 'schedules', 'all', 'https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv', 'ok', 2180017, '4df6d806bd77'), ('2026-09-23T01:58:19', 'pbp', 2025, 'ht |       0.8 |
| build               | ok       | team_games (8202, 142)                                                                                                                                                                                   |     254.7 |
| features            | ok       | [40 rows x 8 columns]                                                                                                                                                                                    |      20.2 |
| verify              | ok       | Result: PASS                                                                                                                                                                                             |       0.5 |
| weather             | ok       | game_id          kickoff_et  ... precip        fetched_at                                                                                                                                                |       1.2 |
|                     |          | 0    2026_03_ATL_GB 2026-09-24 20:15:00  ...    0.0  2026-09-22 22:02                                                                                                                                    |           |
|                     |          | 1   2026_03_LAC_BUF 2026-09-27 13:00:00  ...    0.0  2026-09                                                                                                                                             |           |
| ratings             | ok       | (7668, 49)                                                                                                                                                                                               |      32.3 |
| trends              | ok       | head-to-head cover margin      96                 0.355         7.079            2.793                                                                                                                   |      81.8 |
| players             | ok       | max           0.151042         1.357485    14.000000                                                                                                                                                     |     151.5 |
| positions           | ok       | Skill    518.0  0.005764  0.00180  0.0750                                                                                                                                                                |      14.4 |
| model               | ok       | neutral            0.044       0.133          0.006                                                                                                                                                      |      19.6 |
| picks               | ok       | game_id  season  week  ...     bet_p bet_odds stake_pct                                                                                                                                                  |       0.2 |
|                     |          | 1992   2026_03_ATL_GB    2026     3  ...       NaN      NaN       NaN                                                                                                                                    |           |
|                     |          | 1993  2026_03_LAC_BUF    2026     3  ...       NaN      NaN                                                                                                                                              |           |
| log run             | ok       | run_at  season  week  ... spread_line  total_line        bet                                                                                                                                             |       0   |
|                     |          | 1992  2026-09-23 01:58 UTC    2026     3  ...         5.5        43.5                                                                                                                                    |           |
|                     |          | 1993  2026-09-23 01:58 UTC    2026                                                                                                                                                                       |           |
| record picks        | ok       | run_at  season  week  ... spread_edge total_edge  p_cover                                                                                                                                                |       0   |
|                     |          | 0  2026-09-23 01:58 UTC    2026     3  ...        4.75      -0.06    0.653                                                                                                                               |           |
|                     |          | 1  2026-09-23 01:58 UTC    2026     3  ...                                                                                                                                                               |           |
| grade               | ok       |                                                                                                                                                                                                          |       0   |
| tie check (sources) | ok       | True                                                                                                                                                                                                     |       0   |
| export data room    | ok       |                                                                                                                                                                                                          |      21.2 |
| tie check (page)    | ok       | True                                                                                                                                                                                                     |       0.1 |
| audit reports       | ok       | Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).                                       |       0.8 |

## Week 3, 2026: 3 flagged of 16 games

| away_team   | home_team   |   away_exp |   home_exp |   spread_line |   total_line |   spread_edge |   total_edge | bet       |   stake_pct |
|:------------|:------------|-----------:|-----------:|--------------:|-------------:|--------------:|-------------:|:----------|------------:|
| KC          | MIA         |      27.35 |      20.6  |         -11.5 |         46.5 |          4.75 |        -0.06 | MIA +11.5 |        0.75 |
| TEN         | NYG         |      18.85 |      25.79 |           2.5 |         39.5 |          4.44 |         4.95 | NYG -3    |        0.57 |
| CIN         | PIT         |      22.8  |      23.42 |          -3.5 |         42.5 |          4.12 |         4.28 | PIT +3.5  |        0.38 |

Full table: reports/picks_2026_wk3.md

## Track record

## Model picks (flagged at a 4+ spread edge, at the best number)

3 recorded, 0 settled, 3 pending.

Every bet:

|   season |   week | game_id         | bet       |   odds |   close |   clv | result   |   units |
|---------:|-------:|:----------------|:----------|-------:|--------:|------:|:---------|--------:|
|     2026 |      3 | 2026_03_KC_MIA  | MIA +11.5 |   -110 |     nan |   nan | pending  |     nan |
|     2026 |      3 | 2026_03_TEN_NYG | NYG -3    |   -110 |     nan |   nan | pending  |     nan |
|     2026 |      3 | 2026_03_CIN_PIT | PIT +3.5  |   -110 |     nan |   nan | pending  |     nan |


Full record: reports/track_record.md
