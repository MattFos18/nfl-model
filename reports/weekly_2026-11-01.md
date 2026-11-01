# Weekly run, 2026-11-01 18:14 UTC

## Steps

| step                | status   | detail                                                                                                                                                                                                   |   seconds |
|:--------------------|:---------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------:|
| pull                | ok       | [('2026-11-01T18:14:42', 'schedules', 'all', 'https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv', 'ok', 2187796, '83ca08609118'), ('2026-11-01T18:14:42', 'players', 'all' |       3   |
| pull player history | ok       | [('2026-11-01T18:14:45', 'pfr_advstats', 2018, 'https://github.com/nflverse/nflverse-data/releases/download/pfr_advstats/advstats_week_def_2018.parquet', 'cached', 149299, ''), ('2026-11-01T18:14:45', |       0   |
| build               | ok       | team_games (8202, 142)                                                                                                                                                                                   |     183.2 |
| features            | ok       | [40 rows x 8 columns]                                                                                                                                                                                    |      16.3 |
| snap exposure       | ok       | snap exposure (334629, 10) seasons 2013 to 2026                                                                                                                                                          |       1.6 |
| verify              | ok       | Result: PASS                                                                                                                                                                                             |       0.5 |
| data checks         | ok       | True                                                                                                                                                                                                     |       0.5 |
| weather             | ok       | game_id          kickoff_et  ...  precip        fetched_at                                                                                                                                               |       4.2 |
|                     |          | 0   2026_08_BAL_BUF 2026-11-01 13:00:00  ...     0.0  2026-11-01 13:18                                                                                                                                   |           |
|                     |          | 1   2026_08_TEN_CIN 2026-11-01 13:00:00  ...     0.0  2026                                                                                                                                               |           |
| wind forecast       | ok       | 4                                                                                                                                                                                                        |       2.6 |
| lines               | ok       | {'ts': '2026-11-01T18-18-15Z', 'season': 2026, 'week': 8, 'rows': 5, 'errors': 'oddsapi: 401 Client Error: Unauthorized for url: https://api.the-odds-api.com/v4/sports/americanfootball_nfl/odds?region |      59.5 |
| live results        | ok       | live results: week 8, 1 final of 14, 8 in progress; spread 1-0, total 0-1, winner 1-0; play-by-play for 9 games                                                                                          |       7.6 |
| ratings             | ok       | (7668, 51) QB-out check: ok; swaps: none                                                                                                                                                                 |      32.7 |
| trends              | ok       | head-to-head cover margin      96                 0.355         7.079            2.793                                                                                                                   |      76.9 |
| players             | ok       | max           0.104589         1.360481    14.000000                                                                                                                                                     |     144.6 |
| positions           | ok       | Skill    483.0  0.007911  0.00250  0.0840                                                                                                                                                                |      26.2 |
| scheme              | ok       | scheme_plays (362035, 83) profiles for 32 teams as of 2026 8                                                                                                                                             |       7.7 |
| player splits       | ok       | player_splits.js 1.74 MB                                                                                                                                                                                 |     113.9 |
| model               | ok       | opp_skill_out_value           12.498       0.012          0.156                                                                                                                                          |      65.1 |
| qt shadow           | ok       | qt shadow: 3300 games, 16411 Questionable listings priced, 75s                                                                                                                                           |      76.1 |
| opener study        | ok       | opener study written                                                                                                                                                                                     |      63.7 |
| props by season     | ok       | DONE                                                                                                                                                                                                     |      33.5 |
| props               | error    | RuntimeError: on_upcast=True)                                                                                                                                                                            |       0.5 |
|                     |          |          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^                                                                                                                                        |           |
|                     |          |   File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/site-packages/pandas/core/internals/blocks.py", line 48                                                                                   |           |
| sizing backtest     | ok       | 2025   14-6    0.700        6.73                                                                                                                                                                         |       5.9 |
| threshold sweep     | ok       | DONE                                                                                                                                                                                                     |       1.7 |
| calibration start   | ok       | last 5 seasons     0.5288     0.5359     0.5429              0.69326            0.25006                0.68250              0.5639             0.5851             94              0.69274                |       1.7 |
| season backtest     | ok       | {'shrink0.1_sig1': 'not adopted', 'shrink0.1_sig1.15': 'not adopted', 'shrink0.2_sig1': 'not adopted', 'shrink0.2_sig1.15': 'not adopted', 'shrink0.3_sig1': 'not adopted', 'shrink0.3_sig1.15': 'not ad |     101.8 |
| legitimacy tests    | ok       | Reading: the line beats the model on the miss every season (it should; it is the market). The question the flag rests on is whether the model's disagreements with the line carry information, which the |      18.3 |
| audit reports       | ok       | Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).                                       |       2.8 |
| picks               | ok       | game_id  season  week  ...     bet_p  bet_odds  stake_pct                                                                                                                                                |       1.3 |
|                     |          | 3135   2026_08_CAR_GB    2026     8  ...       NaN       NaN        NaN                                                                                                                                  |           |
|                     |          | 3136  2026_08_BAL_BUF    2026     8  ...       NaN                                                                                                                                                       |           |
| log run             | ok       | run_at  season  ...  total_line       bet                                                                                                                                                                |       0   |
|                     |          | 3135  2026-11-01 18:14 UTC    2026  ...        46.5                                                                                                                                                      |           |
|                     |          | 3136  2026-11-01 18:14 UTC    2026  ...        54.5                                                                                                                                                      |           |
|                     |          | 3137  2026-11-                                                                                                                                                                                           |           |
| record picks        | ok       | run_at  season  week  ...  spread_edge  total_edge  p_cover                                                                                                                                              |       0.5 |
|                     |          | 0  2026-10-04 12:37 UTC    2026     4  ...         5.08        2.49    0.673                                                                                                                             |           |
|                     |          | 1  2026-10-04 16:01 UTC    2026     4  ...                                                                                                                                                               |           |
| inputs fingerprint  | ok       | {'season': 2026, 'week': 8, 'starters': {'2026_08_CAR_GB': ['00-0036264', '00-0039150', '2026-10-29 20:15'], '2026_08_BAL_BUF': ['00-0034857', '00-0034796', '2026-11-01 13:00'], '2026_08_TEN_CIN': ['0 |       0.7 |
| grade               | ok       |                                                                                                                                                                                                          |       8.4 |
| closing line value  | ok       | CLV 2026: 33 closed, 4 pending, avg -0.05 pts, 21% beat the close                                                                                                                                        |       1.2 |
| forecast history    | ok       | complete: 2205 games stored                                                                                                                                                                              |       0   |
| drift monitor       | ok       | **0 alerts, 0 to watch.** Long run = 2015 to 2024; recent = 2025 and 2026 so far. ALERT at |z| >= 2.5 or a CUSUM trip (h 5); WATCH at |z| >= 2.0.                                                        |       0.5 |
| shadow watch        | ok       | **0 rules ready for a look.** READY = 30+ settled live bets, a win rate past break-even beyond luck (p <= 0.1) and 5+ points more return per unit risked than the rule it would replace over the same se |       1.2 |
| ready checks        | ok       | **0 ready.** Each READY row opens a GitHub issue labelled ready-check (once per title).                                                                                                                  |       0.4 |
| tie check (sources) | error    | RuntimeError: numbers disagree: see reports/tie_check.md                                                                                                                                                 |       4.4 |
| export data room    | ok       |                                                                                                                                                                                                          |     129.4 |
| tie check (page)    | error    | RuntimeError: page files disagree with the sources: see reports/tie_check.md                                                                                                                             |      11.2 |
| standing checks     | ok       | True                                                                                                                                                                                                     |      46.8 |

**Failed steps above were skipped, not filled with stale data.**

## Week 8, 2026: 1 flagged of 14 games

| away_team   | home_team   |   away_exp |   home_exp |   spread_line |   total_line |   spread_edge |   total_edge | bet      |   stake_pct |
|:------------|:------------|-----------:|-----------:|--------------:|-------------:|--------------:|-------------:|:---------|------------:|
| KC          | DEN         |      19.05 |      22.27 |          -1.5 |         41.5 |          4.72 |        -0.18 | DEN +1.5 |        0.34 |

Full table: reports/picks_2026_wk8.md

## Track record

## Rules compared

The flag is bet; the shadows are logged and graded on the same games but never bet, so the rule can be chosen on live results.

Backtest columns: the same rule on the three backtest windows, regular season weeks 1 to 17 (`picks.rule_records`).

| Rule | Bets | Settled | Record | Units | Avg CLV | Backtest 2015-18 | Backtest 2019-22 | Backtest 2023-25 |
|---|---|---|---|---|---|---|---|---|
| 4+ edge (the flag, bet) | 6 | 5 | 2-3 (40%) | -1.12 | -0.25 | 67-54 | 80-52 | 38-17 |
| shadow: 4.5+ edge | 5 | 4 | 1-3 (25%) | -2.05 | -0.30 | 46-36 | 55-39 | 23-15 |
| shadow: 4+ edge, model's side the underdog or pick'em | 6 | 5 | 2-3 (40%) | -1.12 | -0.25 | 52-37 | 72-43 | 30-14 |
| shadow: 4+ edge, weeks 1 to 13 only | 6 | 5 | 2-3 (40%) | -1.12 | -0.25 | 50-41 | 69-38 | 30-14 |

Full record: reports/track_record.md
