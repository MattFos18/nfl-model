# Weekly run, 2026-09-24 16:16 UTC

## Steps

| step                | status   | detail                                                                                                                                                                                                   |   seconds |
|:--------------------|:---------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------:|
| pull                | ok       | [('2026-09-24T16:16:38', 'schedules', 'all', 'https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv', 'ok', 2180806, '2b0958803dbc'), ('2026-09-24T16:16:38', 'players', 'all' |       8.9 |
| pull player history | ok       | [('2026-09-24T16:16:47', 'pfr_advstats', 2018, 'https://github.com/nflverse/nflverse-data/releases/download/pfr_advstats/advstats_week_def_2018.parquet', 'ok', 149299, '8606f428d500'), ('2026-09-24T16 |      14.2 |
| build               | ok       | team_games (8202, 142)                                                                                                                                                                                   |     251.5 |
| features            | ok       | [40 rows x 8 columns]                                                                                                                                                                                    |      19.8 |
| verify              | ok       | Result: PASS                                                                                                                                                                                             |       0.5 |
| weather             | ok       | game_id          kickoff_et  ... precip        fetched_at                                                                                                                                                |     127.3 |
|                     |          | 0    2026_03_ATL_GB 2026-09-24 20:15:00  ...    0.0  2026-09-24 12:21                                                                                                                                    |           |
|                     |          | 1   2026_03_LAC_BUF 2026-09-27 13:00:00  ...    0.0  2026-09                                                                                                                                             |           |
| lines               | ok       | {'ts': '2026-09-24T16-23-40Z', 'season': 2026, 'week': 3, 'rows': 16, 'errors': ''}                                                                                                                      |       5.3 |
| ratings             | ok       | (7668, 49)                                                                                                                                                                                               |      32.5 |
| trends              | ok       | head-to-head cover margin      96                 0.355         7.079            2.793                                                                                                                   |      82   |
| players             | ok       | max           0.104589         1.360481    14.000000                                                                                                                                                     |     166.3 |
| positions           | ok       | Skill     527.0  0.004299  0.0008  0.0531                                                                                                                                                                |      31.8 |
| scheme              | ok       | scheme_plays (352459, 83) profiles for 32 teams as of 2026 3                                                                                                                                             |       8   |
| props               | ok       | props 2874 projections for week 3 graded rows 0 market lines on the cards 370 graded against the market 0                                                                                                |      24.2 |
| model               | ok       | neutral            0.082       0.133          0.011                                                                                                                                                      |      31.7 |
| sizing backtest     | ok       | 2025  13-11    0.542        0.82                                                                                                                                                                         |       5.5 |
| threshold sweep     | ok       | DONE                                                                                                                                                                                                     |       1.7 |
| audit reports       | ok       | Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).                                       |       0.8 |
| picks               | ok       | game_id  season  week  ...     bet_p bet_odds stake_pct                                                                                                                                                  |       0.5 |
|                     |          | 3060   2026_03_ATL_GB    2026     3  ...       NaN      NaN       NaN                                                                                                                                    |           |
|                     |          | 3061  2026_03_LAC_BUF    2026     3  ...       NaN      NaN                                                                                                                                              |           |
| log run             | ok       | run_at  season  week  ... spread_line  total_line        bet                                                                                                                                             |       0   |
|                     |          | 3060  2026-09-24 16:16 UTC    2026     3  ...         4.5        42.5                                                                                                                                    |           |
|                     |          | 3061  2026-09-24 16:16 UTC    2026                                                                                                                                                                       |           |
| record picks        | ok       | run_at  season  week  ... spread_edge total_edge  p_cover                                                                                                                                                |       0.1 |
|                     |          | 0  2026-09-24 16:16 UTC    2026     3  ...        4.23       0.98    0.654                                                                                                                               |           |
|                     |          |                                                                                                                                                                                                          |           |
|                     |          | [1 rows x 12 columns]                                                                                                                                                                                    |           |
| inputs fingerprint  | ok       | {'season': 2026, 'week': 3, 'starters': {'2026_03_ATL_GB': ['00-0036264', '00-0039917', '2026-09-24 20:15'], '2026_03_LAC_BUF': ['00-0034857', '00-0036355', '2026-09-27 13:00'], '2026_03_CAR_CLE': ['0 |       0.1 |
| grade               | ok       |                                                                                                                                                                                                          |       0.2 |
| tie check (sources) | ok       | True                                                                                                                                                                                                     |       1.9 |
| export data room    | ok       |                                                                                                                                                                                                          |     122.4 |
| tie check (page)    | ok       | True                                                                                                                                                                                                     |       2.4 |
| legitimacy tests    | ok       | Reading: the line beats the model on the miss every season (it should; it is the market). The question the flag rests on is whether the model's disagreements with the line carry information, which the |      21.3 |

## Week 3, 2026: 1 flagged of 16 games

| away_team   | home_team   |   away_exp |   home_exp |   spread_line |   total_line |   spread_edge |   total_edge | bet       |   stake_pct |
|:------------|:------------|-----------:|-----------:|--------------:|-------------:|--------------:|-------------:|:----------|------------:|
| KC          | MIA         |      27.33 |      21.07 |         -10.5 |         45.5 |          4.23 |         0.98 | MIA +10.5 |        1.34 |

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
