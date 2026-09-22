# Weekly run, 2026-09-22 19:58 UTC

## Steps

| step             | status   | detail                                                                                                                                                                                                   |   seconds |
|:-----------------|:---------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------:|
| pull             | ok       | [('2026-09-22T19:58:41', 'schedules', 'all', 'https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv', 'ok', 2180012, '56f92c0f2faa'), ('2026-09-22T19:58:41', 'pbp', 2025, 'ht |       1.5 |
| build            | ok       | team_games (8202, 142)                                                                                                                                                                                   |     249.8 |
| features         | ok       | [40 rows x 8 columns]                                                                                                                                                                                    |      19.7 |
| verify           | ok       | Result: PASS                                                                                                                                                                                             |       0.5 |
| weather          | ok       | game_id          kickoff_et  ... precip        fetched_at                                                                                                                                                |     152.3 |
|                  |          | 0    2026_03_ATL_GB 2026-09-24 20:15:00  ...    0.0  2026-09-22 16:03                                                                                                                                    |           |
|                  |          | 1   2026_03_LAC_BUF 2026-09-27 13:00:00  ...    0.0  2026-09                                                                                                                                             |           |
| ratings          | ok       | (7668, 49)                                                                                                                                                                                               |      32.1 |
| trends           | ok       | head-to-head cover margin      96                 0.355         7.079            2.793                                                                                                                   |      71.8 |
| players          | ok       | max           0.151042         1.357485    14.000000                                                                                                                                                     |     146.1 |
| positions        | ok       | Skill    518.0  0.005764  0.00180  0.0750                                                                                                                                                                |      14.1 |
| model            | ok       | neutral            0.129       0.133          0.017                                                                                                                                                      |      19.2 |
| picks            | ok       | game_id  season  week  ... best_line    best_book spread_edge_best                                                                                                                                       |       0.2 |
|                  |          | 1992   2026_03_ATL_GB    2026     3  ...       6.0  Draft Kings        -0.724311                                                                                                                         |           |
|                  |          | 1993  2026_03_LAC_BUF    2026     3  .                                                                                                                                                                   |           |
| record picks     | ok       | run_at  season  week  ... total_edge p_cover         book                                                                                                                                                |       0   |
|                  |          | 0  2026-09-22 19:58 UTC    2026     3  ...       0.02   0.705  Draft Kings                                                                                                                               |           |
|                  |          |                                                                                                                                                                                                          |           |
|                  |          | [1 rows x 11 columns]                                                                                                                                                                                    |           |
| grade            | ok       |                                                                                                                                                                                                          |       0   |
| export data room | ok       |                                                                                                                                                                                                          |       6.4 |
| audit reports    | ok       | Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).                                       |       0.8 |

## Week 3, 2026: 1 flagged of 16 games

| away_team   | home_team   |   away_exp |   home_exp |   spread_line |   total_line |   spread_edge |   total_edge | bet       |
|:------------|:------------|-----------:|-----------:|--------------:|-------------:|--------------:|-------------:|:----------|
| KC          | MIA         |       25.8 |       20.9 |         -11.5 |         46.5 |           6.6 |            0 | MIA +11.5 |

Full table: reports/picks_2026_wk3.md

## Track record

## Model picks (flagged at 5+ spread, 6+ total)

1 recorded, 0 settled, 1 pending.

Every bet:

|   season |   week | game_id        | bet       |   odds |   close |   clv | result   |   units |
|---------:|-------:|:---------------|:----------|-------:|--------:|------:|:---------|--------:|
|     2026 |      3 | 2026_03_KC_MIA | MIA +11.5 |   -110 |     nan |   nan | pending  |     nan |

## Matt's bets


Full record: reports/track_record.md
