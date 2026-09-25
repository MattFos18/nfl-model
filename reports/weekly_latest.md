# Weekly run, 2026-09-25 02:50 UTC

## Steps

| step                | status   | detail                                                                                                                                                                                                   |   seconds |
|:--------------------|:---------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------:|
| pull                | ok       | [('2026-09-25T02:50:24', 'schedules', 'all', 'https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv', 'ok', 2180827, 'bcb46a71e75a'), ('2026-09-25T02:50:24', 'players', 'all' |      10.6 |
| pull player history | ok       | [('2026-09-25T02:50:35', 'pfr_advstats', 2018, 'https://github.com/nflverse/nflverse-data/releases/download/pfr_advstats/advstats_week_def_2018.parquet', 'ok', 149299, '8606f428d500'), ('2026-09-25T02 |      13.8 |
| build               | ok       | team_games (8202, 142)                                                                                                                                                                                   |     179.4 |
| features            | ok       | [40 rows x 8 columns]                                                                                                                                                                                    |      18.9 |
| verify              | ok       | Result: PASS                                                                                                                                                                                             |       0.5 |
| weather             | ok       | game_id          kickoff_et  ... precip        fetched_at                                                                                                                                                |     205.8 |
|                     |          | 0   2026_03_LAC_BUF 2026-09-27 13:00:00  ...    0.0  2026-09-24 22:54                                                                                                                                    |           |
|                     |          | 1   2026_03_CAR_CLE 2026-09-27 13:00:00  ...    0.0  2026-09                                                                                                                                             |           |
| lines               | ok       | {'ts': '2026-09-25T02-57-33Z', 'season': 2026, 'week': 3, 'rows': 15, 'errors': ''}                                                                                                                      |       1.1 |
| ratings             | ok       | (7668, 49)                                                                                                                                                                                               |      32.3 |
| trends              | ok       | head-to-head cover margin      96                 0.355         7.079            2.793                                                                                                                   |      81.9 |
| players             | ok       | max           0.104589         1.360481    14.000000                                                                                                                                                     |     161.9 |
| positions           | ok       | Skill     527.0  0.004299  0.0008  0.0531                                                                                                                                                                |      29.9 |
| scheme              | ok       | scheme_plays (352459, 83) profiles for 32 teams as of 2026 3                                                                                                                                             |       7.6 |
| player splits       | ok       | player_splits.js 1.55 MB                                                                                                                                                                                 |     115.5 |
| props               | ok       | props 2874 projections for week 3 graded rows 0 market lines on the cards 371 graded against the market 0                                                                                                |      24.1 |
| model               | ok       | neutral            0.082       0.133          0.011                                                                                                                                                      |     106.8 |
| sizing backtest     | ok       | 2025   13-9    0.591        2.82                                                                                                                                                                         |       6.4 |
| threshold sweep     | ok       | DONE                                                                                                                                                                                                     |       1.7 |
| audit reports       | ok       | Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).                                       |       0.8 |
| picks               | ok       | game_id  season  week  ...     bet_p bet_odds stake_pct                                                                                                                                                  |       0.5 |
|                     |          | 3060   2026_03_ATL_GB    2026     3  ...       NaN      NaN       NaN                                                                                                                                    |           |
|                     |          | 3061  2026_03_LAC_BUF    2026     3  ...       NaN      NaN                                                                                                                                              |           |
| log run             | ok       | run_at  season  week  ... spread_line  total_line        bet                                                                                                                                             |       0   |
|                     |          | 3060  2026-09-25 02:50 UTC    2026     3  ...         4.5        43.5                                                                                                                                    |           |
|                     |          | 3061  2026-09-25 02:50 UTC    2026                                                                                                                                                                       |           |
| record picks        | ok       | run_at  season  week  ... spread_edge total_edge  p_cover                                                                                                                                                |       0.1 |
|                     |          | 0  2026-09-25 02:50 UTC    2026     3  ...        4.19       1.66    0.653                                                                                                                               |           |
|                     |          |                                                                                                                                                                                                          |           |
|                     |          | [1 rows x 12 columns]                                                                                                                                                                                    |           |
| inputs fingerprint  | ok       | {'season': 2026, 'week': 3, 'starters': {'2026_03_ATL_GB': ['00-0036264', '00-0039917', '2026-09-24 20:15'], '2026_03_LAC_BUF': ['00-0034857', '00-0036355', '2026-09-27 13:00'], '2026_03_CAR_CLE': ['0 |       0.1 |
| grade               | ok       |                                                                                                                                                                                                          |       0.3 |
| tie check (sources) | ok       | True                                                                                                                                                                                                     |       1.8 |
| export data room    | ok       |                                                                                                                                                                                                          |     122.6 |
| tie check (page)    | ok       | True                                                                                                                                                                                                     |       2.2 |
| legitimacy tests    | ok       | Reading: the line beats the model on the miss every season (it should; it is the market). The question the flag rests on is whether the model's disagreements with the line carry information, which the |      20.9 |

## Week 3, 2026: 1 flagged of 16 games

| away_team   | home_team   |   away_exp |   home_exp |   spread_line |   total_line |   spread_edge |   total_edge | bet       |   stake_pct |
|:------------|:------------|-----------:|-----------:|--------------:|-------------:|--------------:|-------------:|:----------|------------:|
| KC          | MIA         |      27.31 |         21 |         -10.5 |         45.5 |          4.19 |         1.66 | MIA +10.5 |        0.93 |

Full table: reports/picks_2026_wk3.md

## Track record

## Rules compared

The flag is bet; the shadows are logged and graded on the same games but never bet, so the rule can be chosen on live results.

Backtest columns: the same rule on the three backtest windows, regular season weeks 1 to 17 (`picks.rule_records`).

| Rule | Bets | Settled | Record | Units | Avg CLV | Backtest 2015-18 | Backtest 2019-22 | Backtest 2023-25 |
|---|---|---|---|---|---|---|---|---|
| 4+ edge (the flag, bet) | 1 | 0 | nothing settled |  | +0.00 | 68-56 | 79-51 | 40-21 |
| shadow: 4.5+ edge | 0 | 0 | | | | 43-36 | 52-37 | 25-15 |
| shadow: 4+ edge, model's side the underdog or pick'em | 1 | 0 | nothing settled |  | +0.00 | 50-39 | 72-42 | 32-18 |
| shadow: 4+ edge, weeks 1 to 13 only | 1 | 0 | nothing settled |  | +0.00 | 54-42 | 67-37 | 33-16 |

Full record: reports/track_record.md
