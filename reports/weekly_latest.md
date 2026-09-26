# Weekly run, 2026-09-26 04:15 UTC

## Steps

| step                | status   | detail                                                                                                                                                                                                   |   seconds |
|:--------------------|:---------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------:|
| pull                | ok       | [('2026-09-26T04:15:54', 'schedules', 'all', 'https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv', 'ok', 2180907, 'd45f0ef83d8a'), ('2026-09-26T04:15:54', 'players', 'all' |       8.1 |
| pull player history | ok       | [('2026-09-26T04:16:02', 'pfr_advstats', 2018, 'https://github.com/nflverse/nflverse-data/releases/download/pfr_advstats/advstats_week_def_2018.parquet', 'ok', 149299, '8606f428d500'), ('2026-09-26T04 |      10.5 |
| build               | ok       | team_games (8202, 142)                                                                                                                                                                                   |      89.1 |
| features            | ok       | [40 rows x 8 columns]                                                                                                                                                                                    |       8   |
| verify              | ok       | Result: PASS                                                                                                                                                                                             |       0.3 |
| weather             | ok       | game_id          kickoff_et  ... precip        fetched_at                                                                                                                                                |     132.9 |
|                     |          | 0   2026_03_LAC_BUF 2026-09-27 13:00:00  ...    0.0  2026-09-26 00:17                                                                                                                                    |           |
|                     |          | 1   2026_03_CAR_CLE 2026-09-27 13:00:00  ...    0.0  2026-09                                                                                                                                             |           |
| lines               | ok       | {'ts': '2026-09-26T04-20-03Z', 'season': 2026, 'week': 3, 'rows': 15, 'errors': ''}                                                                                                                      |       0.9 |
| ratings             | ok       | (7668, 49)                                                                                                                                                                                               |      14.3 |
| trends              | ok       | head-to-head cover margin      96                 0.355         7.079            2.793                                                                                                                   |      32.4 |
| players             | ok       | max           0.104589         1.360481    14.000000                                                                                                                                                     |      75.3 |
| positions           | ok       | Skill     527.0  0.004299  0.0008  0.0531                                                                                                                                                                |      15.7 |
| scheme              | ok       | scheme_plays (352588, 83) profiles for 32 teams as of 2026 3                                                                                                                                             |       3.5 |
| player splits       | ok       | player_splits.js 1.56 MB                                                                                                                                                                                 |      42.8 |
| props               | ok       | props 2896 projections for week 3 graded rows 0 market lines on the cards 373 graded against the market 0                                                                                                |      11.1 |
| model               | ok       | neutral            0.082       0.133          0.011                                                                                                                                                      |      57.5 |
| sizing backtest     | ok       | 2025   13-9    0.591        2.82                                                                                                                                                                         |       3.1 |
| threshold sweep     | ok       | DONE                                                                                                                                                                                                     |       1   |
| audit reports       | ok       | Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).                                       |       0.5 |
| picks               | ok       | game_id  season  week  ... bet_p bet_odds stake_pct                                                                                                                                                      |       0.3 |
|                     |          | 3060   2026_03_ATL_GB    2026     3  ...   NaN      NaN       NaN                                                                                                                                        |           |
|                     |          | 3061  2026_03_LAC_BUF    2026     3  ...   NaN      NaN       NaN                                                                                                                                        |           |
|                     |          | 30                                                                                                                                                                                                       |           |
| log run             | ok       | run_at  season  week  ... spread_line  total_line  bet                                                                                                                                                   |       0   |
|                     |          | 3061  2026-09-26 04:15 UTC    2026     3  ...         7.0        50.5                                                                                                                                    |           |
|                     |          | 3062  2026-09-26 04:15 UTC    2026     3  ...                                                                                                                                                            |           |
| record picks        | ok       | Empty DataFrame                                                                                                                                                                                          |       0.1 |
|                     |          | Columns: [run_at, season, week, game_id, bet, odds, stake, stake_pct, book, spread_edge, total_edge, p_cover]                                                                                            |           |
|                     |          | Index: []                                                                                                                                                                                                |           |
| inputs fingerprint  | ok       | {'season': 2026, 'week': 3, 'starters': {'2026_03_ATL_GB': ['00-0036264', '00-0039917', '2026-09-24 20:15'], '2026_03_LAC_BUF': ['00-0034857', '00-0036355', '2026-09-27 13:00'], '2026_03_CAR_CLE': ['0 |       0.1 |
| grade               | ok       |                                                                                                                                                                                                          |       0.1 |
| tie check (sources) | ok       | True                                                                                                                                                                                                     |       1.1 |
| export data room    | ok       |                                                                                                                                                                                                          |      61.5 |
| tie check (page)    | ok       | True                                                                                                                                                                                                     |       1.7 |
| legitimacy tests    | ok       | Reading: the line beats the model on the miss every season (it should; it is the market). The question the flag rests on is whether the model's disagreements with the line carry information, which the |       9   |

## Week 3, 2026: 0 flagged of 16 games

No game clears the flag thresholds.

Full table: reports/picks_2026_wk3.md

## Track record

## Rules compared

The flag is bet; the shadows are logged and graded on the same games but never bet, so the rule can be chosen on live results.

Backtest columns: the same rule on the three backtest windows, regular season weeks 1 to 17 (`picks.rule_records`).

| Rule | Bets | Settled | Record | Units | Avg CLV | Backtest 2015-18 | Backtest 2019-22 | Backtest 2023-25 |
|---|---|---|---|---|---|---|---|---|
| 4+ edge (the flag, bet) | 0 | 0 | | | | 69-55 | 80-51 | 40-21 |
| shadow: 4.5+ edge | 0 | 0 | | | | 43-36 | 52-37 | 25-15 |
| shadow: 4+ edge, model's side the underdog or pick'em | 0 | 0 | | | | 51-38 | 73-42 | 32-18 |
| shadow: 4+ edge, weeks 1 to 13 only | 0 | 0 | | | | 54-41 | 68-37 | 33-16 |

Full record: reports/track_record.md
