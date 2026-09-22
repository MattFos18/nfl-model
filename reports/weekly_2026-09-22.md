# Weekly run, 2026-09-22 19:19 UTC

## Steps

| step             | status   | detail                                                                                                                                                                                                   |   seconds |
|:-----------------|:---------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------:|
| pull             | ok       | [('2026-09-22T19:19:01', 'schedules', 'all', 'https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv', 'ok', 2180001, '6604447cf33e'), ('2026-09-22T19:19:01', 'pbp', 2025, 'ht |       1.5 |
| build            | ok       | team_games (8202, 142)                                                                                                                                                                                   |     180.8 |
| features         | ok       | [40 rows x 8 columns]                                                                                                                                                                                    |      11.4 |
| verify           | ok       | Result: PASS                                                                                                                                                                                             |       0.4 |
| weather          | ok       | game_id          kickoff_et  ... precip        fetched_at                                                                                                                                                |     150.2 |
|                  |          | 0    2026_03_ATL_GB 2026-09-24 20:15:00  ...    0.0  2026-09-22 15:22                                                                                                                                    |           |
|                  |          | 1   2026_03_LAC_BUF 2026-09-27 13:00:00  ...    0.0  2026-09                                                                                                                                             |           |
| ratings          | ok       | (7668, 49)                                                                                                                                                                                               |      19.5 |
| trends           | ok       | head-to-head cover margin      96                 0.355         7.079            2.793                                                                                                                   |      42.2 |
| players          | ok       | max           0.151042         1.357485    14.000000                                                                                                                                                     |      93.2 |
| positions        | ok       | Skill    518.0  0.005764  0.00180  0.0750                                                                                                                                                                |       9.7 |
| model            | ok       | neutral            0.142       0.133          0.019                                                                                                                                                      |      10.4 |
| picks            | ok       | game_id  season  week  ...   old_home   old_away        bet                                                                                                                                              |       0   |
|                  |          | 1992   2026_03_ATL_GB    2026     3  ...  14.268737 -10.812540                                                                                                                                           |           |
|                  |          | 1993  2026_03_LAC_BUF    2026     3  ...  52.645364                                                                                                                                                      |           |
| record picks     | ok       | run_at  season  week  ... spread_edge total_edge  p_cover                                                                                                                                                |       0   |
|                  |          | 0  2026-09-22 19:19 UTC    2026     3  ...        6.57       0.39    0.703                                                                                                                               |           |
|                  |          |                                                                                                                                                                                                          |           |
|                  |          | [1 rows x 10 columns]                                                                                                                                                                                    |           |
| grade            | ok       |                                                                                                                                                                                                          |       0   |
| export data room | ok       |                                                                                                                                                                                                          |       4.4 |
| audit reports    | ok       | Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).                                       |       0.6 |

## Week 3, 2026: 1 flagged of 16 games

| away_team   | home_team   |   away_exp |   home_exp |   spread_line |   total_line |   spread_edge |   total_edge | bet       |
|:------------|:------------|-----------:|-----------:|--------------:|-------------:|--------------:|-------------:|:----------|
| KC          | MIA         |       26.2 |       21.3 |         -11.5 |         46.5 |           6.6 |          0.4 | MIA +11.5 |

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
