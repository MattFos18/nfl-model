# Weekly run, 2026-11-03 17:30 UTC

## Steps

| step                          | status   | detail                                                                                                                                                                                                   |   seconds |
|:------------------------------|:---------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------:|
| pull                          | ok       | [('2026-11-03T17:30:39', 'schedules', 'all', 'https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv', 'ok', 2187848, '7a95e8c28d08'), ('2026-11-03T17:30:39', 'players', 'all' |       9.9 |
| pull player history           | ok       | [('2026-11-03T17:30:48', 'pfr_advstats', 2018, 'https://github.com/nflverse/nflverse-data/releases/download/pfr_advstats/advstats_week_def_2018.parquet', 'cached', 149299, ''), ('2026-11-03T17:30:48', |       0   |
| build                         | ok       | team_games (8202, 142)                                                                                                                                                                                   |     183.1 |
| features                      | ok       | [40 rows x 8 columns]                                                                                                                                                                                    |      16.5 |
| snap exposure                 | ok       | snap exposure (335848, 10) seasons 2013 to 2026                                                                                                                                                          |       1.7 |
| verify                        | ok       | Result: PASS                                                                                                                                                                                             |       0.5 |
| data checks                   | ok       | True                                                                                                                                                                                                     |       0.5 |
| weather                       | ok       | game_id          kickoff_et  ...  precip        fetched_at                                                                                                                                               |       5.8 |
|                               |          | 0   2026_09_JAX_BAL 2026-11-05 20:15:00  ...     0.2  2026-11-03 12:34                                                                                                                                   |           |
|                               |          | 1   2026_09_DEN_CAR 2026-11-08 13:00:00  ...     0.0  2026                                                                                                                                               |           |
| wind forecast                 | ok       | 1                                                                                                                                                                                                        |       1.3 |
| lines                         | ok       | {'ts': '2026-11-03T17-34-18Z', 'season': 2026, 'week': 8, 'rows': 15, 'errors': 'oddsapi: 401 Client Error: Unauthorized for url: https://api.the-odds-api.com/v4/sports/americanfootball_nfl/odds?regio |      25.8 |
| live results                  | ok       | live results: week 8, 14 final of 14, 0 in progress; spread 8-6, total 5-9, winner 11-3; play-by-play for 14 games                                                                                       |      11.4 |
| ratings                       | ok       | (7668, 51) QB-out check: ok; swaps: none                                                                                                                                                                 |      33.7 |
| trends                        | ok       | head-to-head cover margin      96                 0.355         7.079            2.793                                                                                                                   |      76.9 |
| players                       | ok       | max           0.104589         1.360481    14.000000                                                                                                                                                     |     147.8 |
| positions                     | ok       | Skill    483.0  0.007911  0.00250  0.0840                                                                                                                                                                |      28   |
| scheme                        | ok       | scheme_plays (363642, 83) profiles for 32 teams as of 2026 9                                                                                                                                             |       7.7 |
| player splits                 | ok       | player_splits.js 1.76 MB                                                                                                                                                                                 |     116.9 |
| week moved mid-run            | ok       | (2026, 8) -> (2026, 9): input steps run again                                                                                                                                                            |       0   |
| ratings (again, week 9)       | ok       | (7668, 51) QB-out check: ok; swaps: BAL Tyler Huntley -> Joe Fagnano (depth chart)                                                                                                                       |      33.2 |
| trends (again, week 9)        | ok       | head-to-head cover margin      96                 0.355         7.079            2.793                                                                                                                   |      77.4 |
| players (again, week 9)       | ok       | max           0.104589         1.360481     14.00000                                                                                                                                                     |     145.4 |
| positions (again, week 9)     | ok       | Skill    486.0  0.007891  0.00260  0.0805                                                                                                                                                                |      26.9 |
| scheme (again, week 9)        | ok       | scheme_plays (363642, 83) profiles for 32 teams as of 2026 9                                                                                                                                             |       7.7 |
| player splits (again, week 9) | ok       | player_splits.js 1.76 MB                                                                                                                                                                                 |     115.3 |
| model                         | ok       | opp_skill_out_value           12.498       0.012          0.156                                                                                                                                          |      71.7 |
| qt shadow                     | ok       | qt shadow: 3300 games, 16529 Questionable listings priced, 77s                                                                                                                                           |      78.1 |
| opener study                  | ok       | opener study written                                                                                                                                                                                     |      70.2 |
| props by season               | ok       | DONE                                                                                                                                                                                                     |      34   |
| props                         | error    | RuntimeError: on_upcast=True)                                                                                                                                                                            |       0.6 |
|                               |          |          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^                                                                                                                                        |           |
|                               |          |   File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/site-packages/pandas/core/internals/blocks.py", line 48                                                                                   |           |
| sizing backtest               | ok       | 2025   14-6    0.700        6.73                                                                                                                                                                         |       6   |
| threshold sweep               | ok       | DONE                                                                                                                                                                                                     |       1.8 |
| calibration start             | ok       | last 5 seasons     0.5288     0.5359     0.5429              0.69326            0.25006                0.68250              0.5639             0.5851             94              0.69274                |       1.8 |
| season backtest               | ok       | {'shrink0.1_sig1': 'not adopted', 'shrink0.1_sig1.15': 'not adopted', 'shrink0.2_sig1': 'not adopted', 'shrink0.2_sig1.15': 'not adopted', 'shrink0.3_sig1': 'not adopted', 'shrink0.3_sig1.15': 'not ad |     105.1 |
| legitimacy tests              | ok       | Reading: the line beats the model on the miss every season (it should; it is the market). The question the flag rests on is whether the model's disagreements with the line carry information, which the |      20   |
| audit reports                 | ok       | Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).                                       |       3.1 |
| picks                         | ok       | game_id  season  week  ...     bet_p  bet_odds  stake_pct                                                                                                                                                |       1.3 |
|                               |          | 3149  2026_09_JAX_BAL    2026     9  ...       NaN       NaN        NaN                                                                                                                                  |           |
|                               |          | 3150  2026_09_CIN_ATL    2026     9  ...       NaN                                                                                                                                                       |           |
| log run                       | ok       | run_at  season  week  ...  spread_line  total_line     bet                                                                                                                                               |       0   |
|                               |          | 3149  2026-11-03 17:30 UTC    2026     9  ...         -9.5        41.5                                                                                                                                   |           |
|                               |          | 3150  2026-11-03 17:30 UTC    2026     9                                                                                                                                                                 |           |
| record picks                  | ok       | run_at  season  week  ...  spread_edge  total_edge  p_cover                                                                                                                                              |       0.6 |
|                               |          | 0  2026-10-04 12:37 UTC    2026     4  ...         5.08        2.49    0.673                                                                                                                             |           |
|                               |          | 1  2026-10-04 16:01 UTC    2026     4  ...                                                                                                                                                               |           |
| inputs fingerprint            | ok       | {'season': 2026, 'week': 9, 'starters': {'2026_09_JAX_BAL': ['00-0035993', '00-0036971', '2026-11-05 20:15'], '2026_09_CIN_ATL': ['00-0039917', '00-0036442', '2026-11-08 09:30'], '2026_09_DEN_CAR': [' |       0.7 |
| grade                         | ok       |                                                                                                                                                                                                          |       9.1 |
| closing line value            | ok       | CLV 2026: 37 closed, 4 pending, avg +0.04 pts, 24% beat the close                                                                                                                                        |       1.3 |
| forecast history              | ok       | 10 games fetched in 5s, 2215 stored, 0 left                                                                                                                                                              |       4.7 |
| drift monitor                 | ok       | **0 alerts, 0 to watch.** Long run = 2015 to 2024; recent = 2025 and 2026 so far. ALERT at |z| >= 2.5 or a CUSUM trip (h 5); WATCH at |z| >= 2.0.                                                        |       0.5 |
| shadow watch                  | ok       | **0 rules ready for a look.** READY = 30+ settled live bets, a win rate past break-even beyond luck (p <= 0.1) and 5+ points more return per unit risked than the rule it would replace over the same se |       1.3 |
| ready checks                  | ok       | **0 ready.** Each READY row opens a GitHub issue labelled ready-check (once per title).                                                                                                                  |       0.5 |
| tie check (sources)           | error    | RuntimeError: numbers disagree: see reports/tie_check.md                                                                                                                                                 |       3.9 |
| export data room              | ok       |                                                                                                                                                                                                          |     144.2 |
| tie check (page)              | error    | RuntimeError: page files disagree with the sources: see reports/tie_check.md                                                                                                                             |      11.3 |
| standing checks               | ok       | True                                                                                                                                                                                                     |      49.2 |

**Failed steps above were skipped, not filled with stale data.**

## Week 9, 2026: 1 flagged of 15 games

| away_team   | home_team   |   away_exp |   home_exp |   spread_line |   total_line |   spread_edge |   total_edge | bet    |   stake_pct |
|:------------|:------------|-----------:|-----------:|--------------:|-------------:|--------------:|-------------:|:-------|------------:|
| DAL         | IND         |      26.29 |      24.99 |            -6 |         51.5 |          4.69 |        -0.22 | IND +6 |        1.45 |

Full table: reports/picks_2026_wk9.md

## Track record

## Rules compared

The flag is bet; the shadows are logged and graded on the same games but never bet, so the rule can be chosen on live results.

Backtest columns: the same rule on the three backtest windows, regular season weeks 1 to 17 (`picks.rule_records`).

| Rule | Bets | Settled | Record | Units | Avg CLV | Backtest 2015-18 | Backtest 2019-22 | Backtest 2023-25 |
|---|---|---|---|---|---|---|---|---|
| 4+ edge (the flag, bet) | 7 | 6 | 3-3 (50%) | -0.29 | +0.21 | 67-54 | 80-52 | 38-17 |
| shadow: 4.5+ edge | 6 | 5 | 2-3 (40%) | -1.21 | +0.25 | 46-36 | 55-39 | 23-15 |
| shadow: 4+ edge, model's side the underdog or pick'em | 7 | 6 | 3-3 (50%) | -0.29 | +0.21 | 52-37 | 72-43 | 30-14 |
| shadow: 4+ edge, weeks 1 to 13 only | 7 | 6 | 3-3 (50%) | -0.29 | +0.21 | 50-41 | 69-38 | 30-14 |

Full record: reports/track_record.md
