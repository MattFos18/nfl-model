# Weekly run, 2026-09-22 15:32 UTC

## Steps

| step             | status   | detail                                                                                                                                                                                                   |   seconds |
|:-----------------|:---------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------:|
| pull             | ok       | [('2026-09-22T15:32:02', 'schedules', 'all', 'https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv', 'ok', 2179538, 'be302dc1234b'), ('2026-09-22T15:32:02', 'pbp', 2012, 'ht |      13.5 |
| build            | ok       | team_games (8202, 142)                                                                                                                                                                                   |     256   |
| features         | ok       | [40 rows x 8 columns]                                                                                                                                                                                    |      20.2 |
| verify           | ok       | Result: PASS                                                                                                                                                                                             |       0.6 |
| weather          | ok       | game_id          kickoff_et  ... precip        fetched_at                                                                                                                                                |     127.9 |
|                  |          | 0    2026_03_ATL_GB 2026-09-24 20:15:00  ...    0.0  2026-09-22 11:36                                                                                                                                    |           |
|                  |          | 1   2026_03_LAC_BUF 2026-09-27 13:00:00  ...    0.0  2026-09                                                                                                                                             |           |
| ratings          | ok       | (7668, 49)                                                                                                                                                                                               |      33.1 |
| trends           | ok       | head-to-head cover margin      96                 0.355         7.079            2.793                                                                                                                   |      43   |
| model            | ok       | cold           -0.091       0.245         -0.022                                                                                                                                                         |       8.4 |
| picks            | ok       | game_id  season  week  ...   old_home   old_away        bet                                                                                                                                              |       0   |
|                  |          | 1992   2026_03_ATL_GB    2026     3  ...  14.268737 -10.812540                                                                                                                                           |           |
|                  |          | 1993  2026_03_LAC_BUF    2026     3  ...  52.645364                                                                                                                                                      |           |
| record picks     | ok       | run_at  season  week  ... spread_edge total_edge  p_cover                                                                                                                                                |       0   |
|                  |          | 0  2026-09-22 15:32 UTC    2026     3  ...        6.47      -2.86    0.699                                                                                                                               |           |
|                  |          |                                                                                                                                                                                                          |           |
|                  |          | [1 rows x 10 columns]                                                                                                                                                                                    |           |
| grade            | ok       |                                                                                                                                                                                                          |       0   |
| export data room | ok       |                                                                                                                                                                                                          |       5.3 |
| audit reports    | ok       | Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).                                       |       0.8 |

## Week 3, 2026: 1 flagged of 16 games

| away_team   | home_team   |   away_exp |   home_exp |   spread_line |   total_line |   spread_edge |   total_edge | bet       |
|:------------|:------------|-----------:|-----------:|--------------:|-------------:|--------------:|-------------:|:----------|
| KC          | MIA         |       24.3 |       19.3 |         -11.5 |         46.5 |           6.5 |         -2.9 | MIA +11.5 |

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
