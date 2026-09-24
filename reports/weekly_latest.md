# Weekly run, 2026-09-24 16:06 UTC

## Steps

| step                | status   | detail                                                                                                                                                                                                   |   seconds |
|:--------------------|:---------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------:|
| pull                | ok       | [('2026-09-24T16:06:16', 'schedules', 'all', 'https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv', 'ok', 2180806, '85abda8f0dae'), ('2026-09-24T16:06:16', 'players', 'all' |       7.7 |
| pull player history | ok       | [('2026-09-24T16:06:24', 'pfr_advstats', 2018, 'https://github.com/nflverse/nflverse-data/releases/download/pfr_advstats/advstats_week_def_2018.parquet', 'ok', 149299, '8606f428d500'), ('2026-09-24T16 |      11.6 |
| build               | ok       | team_games (8202, 142)                                                                                                                                                                                   |     182.7 |
| features            | ok       | [40 rows x 8 columns]                                                                                                                                                                                    |      13.2 |
| verify              | ok       | Result: PASS                                                                                                                                                                                             |       0.4 |
| weather             | ok       | game_id          kickoff_et  ... precip        fetched_at                                                                                                                                                |       3.3 |
|                     |          | 0    2026_03_ATL_GB 2026-09-24 20:15:00  ...    0.0  2026-09-24 12:09                                                                                                                                    |           |
|                     |          | 1   2026_03_LAC_BUF 2026-09-27 13:00:00  ...    0.0  2026-09                                                                                                                                             |           |
| lines               | ok       | {'ts': '2026-09-24T16-09-56Z', 'season': 2026, 'week': 3, 'rows': 16, 'errors': ''}                                                                                                                      |       2.5 |
| ratings             | ok       | (7668, 49)                                                                                                                                                                                               |      21.9 |
| trends              | ok       | head-to-head cover margin      96                 0.355         7.079            2.793                                                                                                                   |      48.2 |
| players             | ok       | max           0.104589         1.360481    14.000000                                                                                                                                                     |     111.2 |
| positions           | ok       | Skill     527.0  0.004299  0.0008  0.0531                                                                                                                                                                |      22.5 |
| scheme              | ok       | scheme_plays (352459, 83) profiles for 32 teams as of 2026 3                                                                                                                                             |       5.1 |
| props               | error    | RuntimeError:                                                                                                                                                                                            |      13.4 |
| model               | ok       | neutral            0.082       0.133          0.011                                                                                                                                                      |      17.5 |
| sizing backtest     | ok       | 2025  13-11    0.542        0.82                                                                                                                                                                         |       3.7 |
| threshold sweep     | ok       | DONE                                                                                                                                                                                                     |       1.3 |
| audit reports       | ok       | Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).                                       |       0.6 |
| picks               | ok       | game_id  season  week  ...     bet_p bet_odds stake_pct                                                                                                                                                  |       0.3 |
|                     |          | 3060   2026_03_ATL_GB    2026     3  ...       NaN      NaN       NaN                                                                                                                                    |           |
|                     |          | 3061  2026_03_LAC_BUF    2026     3  ...       NaN      NaN                                                                                                                                              |           |
| log run             | ok       | run_at  season  week  ... spread_line  total_line        bet                                                                                                                                             |       0   |
|                     |          | 3060  2026-09-24 16:06 UTC    2026     3  ...         4.5        42.5                                                                                                                                    |           |
|                     |          | 3061  2026-09-24 16:06 UTC    2026                                                                                                                                                                       |           |
| record picks        | ok       | run_at  season  week  ... spread_edge total_edge  p_cover                                                                                                                                                |       0.1 |
|                     |          | 0  2026-09-24 16:06 UTC    2026     3  ...        4.23      -0.02    0.654                                                                                                                               |           |
|                     |          |                                                                                                                                                                                                          |           |
|                     |          | [1 rows x 12 columns]                                                                                                                                                                                    |           |
| inputs fingerprint  | ok       | {'season': 2026, 'week': 3, 'starters': {'2026_03_ATL_GB': ['00-0036264', '00-0039917', '2026-09-24 20:15'], '2026_03_LAC_BUF': ['00-0034857', '00-0036355', '2026-09-27 13:00'], '2026_03_CAR_CLE': ['0 |       0.1 |
| grade               | ok       |                                                                                                                                                                                                          |       0.1 |
| tie check (sources) | ok       | True                                                                                                                                                                                                     |       1.4 |
| export data room    | ok       |                                                                                                                                                                                                          |      80.7 |
| tie check (page)    | ok       | True                                                                                                                                                                                                     |       1.8 |
| legitimacy tests    | ok       | Reading: the line beats the model on the miss every season (it should; it is the market). The question the flag rests on is whether the model's disagreements with the line carry information, which the |      13.7 |

**Failed steps above were skipped, not filled with stale data.**

## Week 3, 2026: 1 flagged of 16 games

| away_team   | home_team   |   away_exp |   home_exp |   spread_line |   total_line |   spread_edge |   total_edge | bet       |   stake_pct |
|:------------|:------------|-----------:|-----------:|--------------:|-------------:|--------------:|-------------:|:----------|------------:|
| KC          | MIA         |      27.33 |      21.07 |         -10.5 |         46.5 |          4.23 |        -0.02 | MIA +10.5 |        1.34 |

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
