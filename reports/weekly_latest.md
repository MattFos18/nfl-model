# Weekly run, 2026-09-24 22:37 UTC

## Steps

| step                | status   | detail                                                                                                                                                                                                   |   seconds |
|:--------------------|:---------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------:|
| pull                | ok       | [('2026-09-24T22:37:43', 'schedules', 'all', 'https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv', 'ok', 2180812, 'd4da4c9c81af'), ('2026-09-24T22:37:43', 'players', 'all' |       8   |
| pull player history | ok       | [('2026-09-24T22:37:51', 'pfr_advstats', 2018, 'https://github.com/nflverse/nflverse-data/releases/download/pfr_advstats/advstats_week_def_2018.parquet', 'ok', 149299, '8606f428d500'), ('2026-09-24T22 |      10.5 |
| build               | ok       | team_games (8202, 142)                                                                                                                                                                                   |     178.7 |
| features            | ok       | [40 rows x 8 columns]                                                                                                                                                                                    |      16.2 |
| verify              | ok       | Result: PASS                                                                                                                                                                                             |       0.5 |
| weather             | ok       | game_id          kickoff_et  ... precip        fetched_at                                                                                                                                                |       4.9 |
|                     |          | 0    2026_03_ATL_GB 2026-09-24 20:15:00  ...    0.0  2026-09-24 18:41                                                                                                                                    |           |
|                     |          | 1   2026_03_LAC_BUF 2026-09-27 13:00:00  ...    0.0  2026-09                                                                                                                                             |           |
| lines               | ok       | {'ts': '2026-09-24T22-41-22Z', 'season': 2026, 'week': 3, 'rows': 16, 'errors': ''}                                                                                                                      |       1.1 |
| ratings             | ok       | (7668, 49)                                                                                                                                                                                               |      31   |
| trends              | ok       | head-to-head cover margin      96                 0.355         7.079            2.793                                                                                                                   |      68.3 |
| players             | ok       | max           0.104589         1.360481    14.000000                                                                                                                                                     |     142.5 |
| positions           | ok       | Skill     527.0  0.004299  0.0008  0.0531                                                                                                                                                                |      28.8 |
| scheme              | ok       | scheme_plays (352459, 83) profiles for 32 teams as of 2026 3                                                                                                                                             |       6.8 |
| player splits       | ok       | player_splits.js 1.55 MB                                                                                                                                                                                 |      93.3 |
| props               | ok       | props 2874 projections for week 3 graded rows 0 market lines on the cards 371 graded against the market 0                                                                                                |      21.1 |
| model               | ok       | neutral            0.082       0.133          0.011                                                                                                                                                      |      22.9 |
| sizing backtest     | ok       | 2025  13-11    0.542        0.82                                                                                                                                                                         |       4.8 |
| threshold sweep     | ok       | DONE                                                                                                                                                                                                     |       1.5 |
| audit reports       | ok       | Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).                                       |       0.7 |
| picks               | ok       | game_id  season  week  ...     bet_p bet_odds stake_pct                                                                                                                                                  |       0.5 |
|                     |          | 3060   2026_03_ATL_GB    2026     3  ...       NaN      NaN       NaN                                                                                                                                    |           |
|                     |          | 3061  2026_03_LAC_BUF    2026     3  ...       NaN      NaN                                                                                                                                              |           |
| log run             | ok       | run_at  season  week  ... spread_line  total_line        bet                                                                                                                                             |       0   |
|                     |          | 3060  2026-09-24 22:37 UTC    2026     3  ...         5.5        43.5                                                                                                                                    |           |
|                     |          | 3061  2026-09-24 22:37 UTC    2026                                                                                                                                                                       |           |
| record picks        | ok       | run_at  season  week  ... spread_edge total_edge  p_cover                                                                                                                                                |       0.1 |
|                     |          | 0  2026-09-24 22:37 UTC    2026     3  ...        4.23       1.14    0.654                                                                                                                               |           |
|                     |          |                                                                                                                                                                                                          |           |
|                     |          | [1 rows x 12 columns]                                                                                                                                                                                    |           |
| inputs fingerprint  | ok       | {'season': 2026, 'week': 3, 'starters': {'2026_03_ATL_GB': ['00-0036264', '00-0039917', '2026-09-24 20:15'], '2026_03_LAC_BUF': ['00-0034857', '00-0036355', '2026-09-27 13:00'], '2026_03_CAR_CLE': ['0 |       0.1 |
| grade               | ok       |                                                                                                                                                                                                          |       0.2 |
| tie check (sources) | ok       | True                                                                                                                                                                                                     |       1.8 |
| export data room    | ok       |                                                                                                                                                                                                          |     109   |
| tie check (page)    | ok       | True                                                                                                                                                                                                     |       2.2 |
| legitimacy tests    | ok       | Reading: the line beats the model on the miss every season (it should; it is the market). The question the flag rests on is whether the model's disagreements with the line carry information, which the |      18   |

## Week 3, 2026: 1 flagged of 16 games

| away_team   | home_team   |   away_exp |   home_exp |   spread_line |   total_line |   spread_edge |   total_edge | bet       |   stake_pct |
|:------------|:------------|-----------:|-----------:|--------------:|-------------:|--------------:|-------------:|:----------|------------:|
| KC          | MIA         |      27.41 |      21.15 |         -10.5 |         45.5 |          4.23 |         1.14 | MIA +10.5 |           1 |

Full table: reports/picks_2026_wk3.md

## Track record

## Rules compared

The flag is bet; the shadows are logged and graded on the same games but never bet, so the rule can be chosen on live results.

Backtest columns: the same rule on the three backtest windows, regular season weeks 1 to 17 (`picks.rule_records`).

| Rule | Bets | Settled | Record | Units | Avg CLV | Backtest 2015-18 | Backtest 2019-22 | Backtest 2023-25 |
|---|---|---|---|---|---|---|---|---|
| 4+ edge (the flag, bet) | 1 | 0 | nothing settled |  | +0.00 | 61-58 | 81-55 | 40-23 |
| shadow: 4.5+ edge | 0 | 0 | | | | 41-40 | 53-35 | 27-14 |
| shadow: 4+ edge, model's side the underdog or pick'em | 1 | 0 | nothing settled |  | +0.00 | 45-36 | 73-43 | 32-18 |
| shadow: 4+ edge, weeks 1 to 13 only | 1 | 0 | nothing settled |  | +0.00 | 46-42 | 67-40 | 34-19 |

Full record: reports/track_record.md
