# Weekly run, 2026-09-28 18:48 UTC

## Steps

| step                | status   | detail                                                                                                                                                                                                   |   seconds |
|:--------------------|:---------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------:|
| pull                | ok       | [('2026-09-28T18:48:09', 'schedules', 'all', 'https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv', 'ok', 2181219, 'e21c06a69e65'), ('2026-09-28T18:48:09', 'players', 'all' |      11.1 |
| pull player history | ok       | [('2026-09-28T18:48:20', 'pfr_advstats', 2018, 'https://github.com/nflverse/nflverse-data/releases/download/pfr_advstats/advstats_week_def_2018.parquet', 'ok', 149299, '8606f428d500'), ('2026-09-28T18 |      11.7 |
| build               | ok       | team_games (8202, 142)                                                                                                                                                                                   |     182.3 |
| features            | ok       | [40 rows x 8 columns]                                                                                                                                                                                    |      18.7 |
| verify              | ok       | Result: PASS                                                                                                                                                                                             |       0.5 |
| weather             | ok       | game_id           kickoff_et  ... precip        fetched_at                                                                                                                                               |     127.8 |
|                     |          | 0   2026_03_PHI_CHI  2026-09-28 20:15:00  ...    0.0  2026-09-28 14:51                                                                                                                                   |           |
|                     |          | 1   2026_04_PIT_CLE  2026-10-01 20:15:00  ...    0.0  2026                                                                                                                                               |           |
| lines               | ok       | {'ts': '2026-09-28T18-54-01Z', 'season': 2026, 'week': 3, 'rows': 17, 'errors': ''}                                                                                                                      |       1.4 |
| live results        | ok       | live results: week 3, 15 final of 16, 0 in progress; spread 8-5-2, total 10-5, winner 10-5; play-by-play for 15 games                                                                                    |       1.2 |
| ratings             | ok       | (7668, 49)                                                                                                                                                                                               |      31.6 |
| trends              | ok       | head-to-head cover margin      96                 0.355         7.079            2.793                                                                                                                   |      81.7 |
| players             | ok       | max           0.104589         1.360481    14.000000                                                                                                                                                     |     162.2 |
| positions           | ok       | Skill     527.0  0.004299  0.00080  0.0531                                                                                                                                                               |      31.3 |
| scheme              | ok       | scheme_plays (354350, 83) profiles for 32 teams as of 2026 3                                                                                                                                             |       7.8 |
| player splits       | ok       | player_splits.js 1.58 MB                                                                                                                                                                                 |     118.2 |
| snap exposure       | ok       | snap exposure (328936, 10) seasons 2013 to 2026                                                                                                                                                          |       1.4 |
| model               | ok       | neutral            0.082       0.133          0.011                                                                                                                                                      |      74.2 |
| props               | ok       | props 2864 projections for week 3 graded rows 0 market lines on the cards 381 graded against the market 1129                                                                                             |      31.7 |
| sizing backtest     | ok       | 2025   13-9    0.591        2.82                                                                                                                                                                         |       7.4 |
| threshold sweep     | ok       | DONE                                                                                                                                                                                                     |       2.1 |
| calibration start   | ok       | last 5 seasons     0.5205     0.5225     0.5244              0.69458            0.25071                0.68567              0.5600             0.5895             95              0.69273                |       2.1 |
| season backtest     | ok       | {'shrink0.1_sig1': 'not adopted', 'shrink0.1_sig1.15': 'not adopted', 'shrink0.2_sig1': 'not adopted', 'shrink0.2_sig1.15': 'not adopted', 'shrink0.3_sig1': 'not adopted', 'shrink0.3_sig1.15': 'not ad |     110   |
| props by season     | ok       | DONE                                                                                                                                                                                                     |      18.4 |
| legitimacy tests    | ok       | Reading: the line beats the model on the miss every season (it should; it is the market). The question the flag rests on is whether the model's disagreements with the line carry information, which the |      24.5 |
| audit reports       | ok       | Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).                                       |       2.9 |
| picks               | ok       | game_id  season  week  ...     bet_p bet_odds stake_pct                                                                                                                                                  |       0.8 |
|                     |          | 3060   2026_03_ATL_GB    2026     3  ...       NaN      NaN       NaN                                                                                                                                    |           |
|                     |          | 3061  2026_03_LAC_BUF    2026     3  ...       NaN      NaN                                                                                                                                              |           |
| log run             | ok       | run_at  season  week  ... spread_line  total_line       bet                                                                                                                                              |       0   |
|                     |          | 3060  2026-09-28 18:48 UTC    2026     3  ...         4.5        42.5                                                                                                                                    |           |
|                     |          | 3061  2026-09-28 18:48 UTC    2026     3                                                                                                                                                                 |           |
| record picks        | ok       | run_at season week  ... spread_edge total_edge p_cover                                                                                                                                                   |       0.2 |
|                     |          | 0  2026-09-27 22:18 UTC   2026    4  ...        4.35       1.88   0.653                                                                                                                                  |           |
|                     |          |                                                                                                                                                                                                          |           |
|                     |          | [1 rows x 12 columns]                                                                                                                                                                                    |           |
| inputs fingerprint  | ok       | {'season': 2026, 'week': 3, 'starters': {'2026_03_ATL_GB': ['00-0036264', '00-0039917', '2026-09-24 20:15'], '2026_03_LAC_BUF': ['00-0034857', '00-0036355', '2026-09-27 13:00'], '2026_03_CAR_CLE': ['0 |       0.3 |
| grade               | ok       |                                                                                                                                                                                                          |       0.5 |
| tie check (sources) | ok       | True                                                                                                                                                                                                     |       5   |
| export data room    | ok       |                                                                                                                                                                                                          |     132.9 |
| tie check (page)    | ok       | True                                                                                                                                                                                                     |       7.1 |

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
