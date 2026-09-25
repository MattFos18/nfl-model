# Weekly run, 2026-09-25 17:14 UTC

## Steps

| step                | status   | detail                                                                                                                                                                                                   |   seconds |
|:--------------------|:---------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------:|
| pull                | ok       | [('2026-09-25T17:14:51', 'schedules', 'all', 'https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv', 'ok', 2180910, '360038990f9f'), ('2026-09-25T17:14:51', 'players', 'all' |       9.9 |
| pull player history | ok       | [('2026-09-25T17:15:01', 'pfr_advstats', 2018, 'https://github.com/nflverse/nflverse-data/releases/download/pfr_advstats/advstats_week_def_2018.parquet', 'ok', 149299, '8606f428d500'), ('2026-09-25T17 |      14.2 |
| build               | ok       | team_games (8202, 142)                                                                                                                                                                                   |     179.8 |
| features            | ok       | [40 rows x 8 columns]                                                                                                                                                                                    |      18.6 |
| verify              | ok       | Result: PASS                                                                                                                                                                                             |       0.5 |
| weather             | ok       | game_id          kickoff_et  ... precip        fetched_at                                                                                                                                                |     251.6 |
|                     |          | 0   2026_03_LAC_BUF 2026-09-27 13:00:00  ...    0.0  2026-09-25 13:18                                                                                                                                    |           |
|                     |          | 1   2026_03_CAR_CLE 2026-09-27 13:00:00  ...    0.0  2026-09                                                                                                                                             |           |
| lines               | ok       | {'ts': '2026-09-25T17-22-46Z', 'season': 2026, 'week': 3, 'rows': 15, 'errors': ''}                                                                                                                      |       1.1 |
| ratings             | ok       | (7668, 49)                                                                                                                                                                                               |      31.9 |
| trends              | ok       | head-to-head cover margin      96                 0.355         7.079            2.793                                                                                                                   |      82.8 |
| players             | ok       | max           0.104589         1.360481    14.000000                                                                                                                                                     |     161.2 |
| positions           | ok       | Skill     527.0  0.004299  0.0008  0.0531                                                                                                                                                                |      30.2 |
| scheme              | ok       | scheme_plays (352588, 83) profiles for 32 teams as of 2026 3                                                                                                                                             |       7.8 |
| player splits       | ok       | player_splits.js 1.56 MB                                                                                                                                                                                 |     116.4 |
| props               | ok       | props 2896 projections for week 3 graded rows 0 market lines on the cards 373 graded against the market 0                                                                                                |      24.5 |
| model               | ok       | neutral            0.082       0.133          0.011                                                                                                                                                      |     109.4 |
| sizing backtest     | ok       | 2025   13-9    0.591        2.82                                                                                                                                                                         |       6.6 |
| threshold sweep     | ok       | DONE                                                                                                                                                                                                     |       1.7 |
| audit reports       | ok       | Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).                                       |       0.8 |
| picks               | ok       | game_id  season  week  ...    bet_p bet_odds stake_pct                                                                                                                                                   |       0.6 |
|                     |          | 3060   2026_03_ATL_GB    2026     3  ...      NaN      NaN       NaN                                                                                                                                     |           |
|                     |          | 3061  2026_03_LAC_BUF    2026     3  ...      NaN      NaN                                                                                                                                               |           |
| log run             | ok       | run_at  season  week  ... spread_line  total_line        bet                                                                                                                                             |       0   |
|                     |          | 3061  2026-09-25 17:14 UTC    2026     3  ...         7.0        50.5                                                                                                                                    |           |
|                     |          | 3062  2026-09-25 17:14 UTC    2026                                                                                                                                                                       |           |
| record picks        | ok       | run_at  season  week  ... spread_edge total_edge  p_cover                                                                                                                                                |       0.1 |
|                     |          | 0  2026-09-25 17:14 UTC    2026     3  ...        4.04       2.68    0.649                                                                                                                               |           |
|                     |          |                                                                                                                                                                                                          |           |
|                     |          | [1 rows x 12 columns]                                                                                                                                                                                    |           |
| inputs fingerprint  | ok       | {'season': 2026, 'week': 3, 'starters': {'2026_03_ATL_GB': ['00-0036264', '00-0039917', '2026-09-24 20:15'], '2026_03_LAC_BUF': ['00-0034857', '00-0036355', '2026-09-27 13:00'], '2026_03_CAR_CLE': ['0 |       0.2 |
| grade               | ok       |                                                                                                                                                                                                          |       0.3 |
| tie check (sources) | ok       | True                                                                                                                                                                                                     |       2.1 |
| export data room    | ok       |                                                                                                                                                                                                          |     125.9 |
| tie check (page)    | ok       | True                                                                                                                                                                                                     |       2.6 |
| legitimacy tests    | ok       | Reading: the line beats the model on the miss every season (it should; it is the market). The question the flag rests on is whether the model's disagreements with the line carry information, which the |      21.3 |

## Week 3, 2026: 1 flagged of 16 games

| away_team   | home_team   |   away_exp |   home_exp |   spread_line |   total_line |   spread_edge |   total_edge | bet       |   stake_pct |
|:------------|:------------|-----------:|-----------:|--------------:|-------------:|--------------:|-------------:|:----------|------------:|
| KC          | MIA         |      27.32 |      20.86 |         -10.5 |         45.5 |          4.04 |         2.68 | MIA +10.5 |        0.83 |

Full table: reports/picks_2026_wk3.md

## Track record

## Rules compared

The flag is bet; the shadows are logged and graded on the same games but never bet, so the rule can be chosen on live results.

Backtest columns: the same rule on the three backtest windows, regular season weeks 1 to 17 (`picks.rule_records`).

| Rule | Bets | Settled | Record | Units | Avg CLV | Backtest 2015-18 | Backtest 2019-22 | Backtest 2023-25 |
|---|---|---|---|---|---|---|---|---|
| 4+ edge (the flag, bet) | 1 | 0 | nothing settled |  | +0.00 | 68-55 | 80-51 | 40-21 |
| shadow: 4.5+ edge | 0 | 0 | | | | 43-36 | 52-37 | 26-15 |
| shadow: 4+ edge, model's side the underdog or pick'em | 1 | 0 | nothing settled |  | +0.00 | 50-38 | 73-42 | 32-18 |
| shadow: 4+ edge, weeks 1 to 13 only | 1 | 0 | nothing settled |  | +0.00 | 54-41 | 68-37 | 33-16 |

Full record: reports/track_record.md
