# Weekly run, 2026-09-28 19:57 UTC

## Steps

| step                | status   | detail                                                                                                                                                                                                   |   seconds |
|:--------------------|:---------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------:|
| pull                | ok       | [('2026-09-28T19:57:04', 'schedules', 'all', 'https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv', 'ok', 2181217, '9943c03d0349'), ('2026-09-28T19:57:04', 'players', 'all' |      10.7 |
| pull player history | ok       | [('2026-09-28T19:57:15', 'pfr_advstats', 2018, 'https://github.com/nflverse/nflverse-data/releases/download/pfr_advstats/advstats_week_def_2018.parquet', 'ok', 149299, '8606f428d500'), ('2026-09-28T19 |      11.5 |
| build               | ok       | team_games (8202, 142)                                                                                                                                                                                   |      86.2 |
| features            | ok       | [40 rows x 8 columns]                                                                                                                                                                                    |       8.2 |
| verify              | ok       | Result: PASS                                                                                                                                                                                             |       0.3 |
| weather             | ok       | game_id           kickoff_et  ... precip        fetched_at                                                                                                                                               |     153.4 |
|                     |          | 0   2026_03_PHI_CHI  2026-09-28 20:15:00  ...    0.0  2026-09-28 15:59                                                                                                                                   |           |
|                     |          | 1   2026_04_PIT_CLE  2026-10-01 20:15:00  ...    0.0  2026                                                                                                                                               |           |
| lines               | ok       | {'ts': '2026-09-28T20-01-35Z', 'season': 2026, 'week': 3, 'rows': 17, 'errors': ''}                                                                                                                      |       1   |
| live results        | ok       | live results: week 3, 15 final of 16, 0 in progress; spread 8-5-2, total 10-5, winner 10-5; play-by-play for 15 games                                                                                    |       0.8 |
| ratings             | ok       | (7668, 49)                                                                                                                                                                                               |      13.5 |
| trends              | ok       | head-to-head cover margin      96                 0.355         7.079            2.793                                                                                                                   |      31.9 |
| players             | ok       | max           0.104589         1.360481    14.000000                                                                                                                                                     |      71.9 |
| positions           | ok       | Skill     527.0  0.004299  0.00080  0.0531                                                                                                                                                               |      15.3 |
| scheme              | ok       | scheme_plays (354350, 83) profiles for 32 teams as of 2026 3                                                                                                                                             |       3.4 |
| player splits       | ok       | player_splits.js 1.58 MB                                                                                                                                                                                 |      43.7 |
| snap exposure       | ok       | snap exposure (328936, 10) seasons 2013 to 2026                                                                                                                                                          |       0.8 |
| model               | ok       | neutral            0.082       0.133          0.011                                                                                                                                                      |      34.1 |
| opener study        | ok       | opener study written                                                                                                                                                                                     |      33.8 |
| props               | ok       | props 2864 projections for week 3 graded rows 0 market lines on the cards 381 graded against the market 1129                                                                                             |      12.8 |
| sizing backtest     | ok       | 2025   13-9    0.591        2.82                                                                                                                                                                         |       3   |
| threshold sweep     | ok       | DONE                                                                                                                                                                                                     |       1   |
| calibration start   | ok       | last 5 seasons     0.5205     0.5225     0.5244              0.69458            0.25071                0.68567              0.5600             0.5895             95              0.69273                |       1.1 |
| season backtest     | ok       | {'shrink0.1_sig1': 'not adopted', 'shrink0.1_sig1.15': 'not adopted', 'shrink0.2_sig1': 'not adopted', 'shrink0.2_sig1.15': 'not adopted', 'shrink0.3_sig1': 'not adopted', 'shrink0.3_sig1.15': 'not ad |      59.3 |
| props by season     | ok       | DONE                                                                                                                                                                                                     |       8.4 |
| legitimacy tests    | ok       | Reading: the line beats the model on the miss every season (it should; it is the market). The question the flag rests on is whether the model's disagreements with the line carry information, which the |       9.1 |
| audit reports       | ok       | Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).                                       |       1.4 |
| picks               | ok       | game_id  season  week  ...     bet_p bet_odds stake_pct                                                                                                                                                  |       0.3 |
|                     |          | 3060   2026_03_ATL_GB    2026     3  ...       NaN      NaN       NaN                                                                                                                                    |           |
|                     |          | 3061  2026_03_LAC_BUF    2026     3  ...       NaN      NaN                                                                                                                                              |           |
| log run             | ok       | run_at  season  week  ... spread_line  total_line       bet                                                                                                                                              |       0   |
|                     |          | 3060  2026-09-28 19:57 UTC    2026     3  ...         4.5        42.5                                                                                                                                    |           |
|                     |          | 3061  2026-09-28 19:57 UTC    2026     3                                                                                                                                                                 |           |
| record picks        | ok       | run_at season week  ... spread_edge total_edge p_cover                                                                                                                                                   |       0.1 |
|                     |          | 0  2026-09-27 22:18 UTC   2026    4  ...        4.35       1.88   0.653                                                                                                                                  |           |
|                     |          |                                                                                                                                                                                                          |           |
|                     |          | [1 rows x 12 columns]                                                                                                                                                                                    |           |
| inputs fingerprint  | ok       | {'season': 2026, 'week': 3, 'starters': {'2026_03_ATL_GB': ['00-0036264', '00-0039917', '2026-09-24 20:15'], '2026_03_LAC_BUF': ['00-0034857', '00-0036355', '2026-09-27 13:00'], '2026_03_CAR_CLE': ['0 |       0.1 |
| grade               | ok       |                                                                                                                                                                                                          |       0.2 |
| tie check (sources) | ok       | True                                                                                                                                                                                                     |       2.1 |
| export data room    | ok       |                                                                                                                                                                                                          |      60.8 |
| tie check (page)    | ok       | True                                                                                                                                                                                                     |       4   |

## Week 3, 2026: 2 flagged of 16 games

| away_team   | home_team   |   away_exp |   home_exp |   spread_line |   total_line |   spread_edge |   total_edge | bet      |   stake_pct |
|:------------|:------------|-----------:|-----------:|--------------:|-------------:|--------------:|-------------:|:---------|------------:|
| CAR         | CLE         |      21.45 |      23.01 |          -2.5 |         41.5 |          4.06 |         2.97 | CLE +2.5 |        0.42 |
| LA          | DEN         |      20.15 |      22.72 |          -1.5 |         43.5 |          4.07 |        -0.62 | DEN +1.5 |        0    |

Full table: reports/picks_2026_wk3.md

## Track record

## Rules compared

The flag is bet; the shadows are logged and graded on the same games but never bet, so the rule can be chosen on live results.

Backtest columns: the same rule on the three backtest windows, regular season weeks 1 to 17 (`picks.rule_records`).

| Rule | Bets | Settled | Record | Units | Avg CLV | Backtest 2015-18 | Backtest 2019-22 | Backtest 2023-25 |
|---|---|---|---|---|---|---|---|---|
| 4+ edge (the flag, bet) | 1 | 0 | nothing settled |  | +0.00 | 68-55 | 80-51 | 40-21 |
| shadow: 4.5+ edge | 0 | 0 | | | | 43-36 | 52-37 | 25-15 |
| shadow: 4+ edge, model's side the underdog or pick'em | 1 | 0 | nothing settled |  | +0.00 | 50-38 | 73-42 | 32-18 |
| shadow: 4+ edge, weeks 1 to 13 only | 1 | 0 | nothing settled |  | +0.00 | 54-41 | 68-37 | 33-16 |

Full record: reports/track_record.md
