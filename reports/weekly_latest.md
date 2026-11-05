# Weekly run, 2026-11-05 23:30 UTC

## Steps

| step                | status   | detail                                                                                                                                                                                                   |   seconds |
|:--------------------|:---------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------:|
| pull                | ok       | [('2026-11-05T23:30:13', 'schedules', 'all', 'https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv', 'ok', 2188858, '5bb1b39ad9d4'), ('2026-11-05T23:30:13', 'players', 'all' |       6.8 |
| pull player history | ok       | [('2026-11-05T23:30:19', 'pfr_advstats', 2018, 'https://github.com/nflverse/nflverse-data/releases/download/pfr_advstats/advstats_week_def_2018.parquet', 'cached', 149299, ''), ('2026-11-05T23:30:19', |       0   |
| build               | ok       | team_games (8202, 142)                                                                                                                                                                                   |     123.9 |
| features            | ok       | [40 rows x 8 columns]                                                                                                                                                                                    |       9.6 |
| snap exposure       | ok       | snap exposure (335848, 10) seasons 2013 to 2026                                                                                                                                                          |       1.3 |
| verify              | ok       | Result: PASS                                                                                                                                                                                             |       0.4 |
| data checks         | ok       | True                                                                                                                                                                                                     |       0.4 |
| weather             | ok       | game_id          kickoff_et  ...  precip        fetched_at                                                                                                                                               |     127.2 |
|                     |          | 0   2026_09_JAX_BAL 2026-11-05 20:15:00  ...     0.0  2026-11-05 18:32                                                                                                                                   |           |
|                     |          | 1   2026_09_DEN_CAR 2026-11-08 13:00:00  ...     0.0  2026                                                                                                                                               |           |
| wind forecast       | ok       | 1                                                                                                                                                                                                        |       1.2 |
| lines               | ok       | {'ts': '2026-11-05T23-34-44Z', 'season': 2026, 'week': 9, 'rows': 15, 'errors': 'oddsapi: 401 Client Error: Unauthorized for url: https://api.the-odds-api.com/v4/sports/americanfootball_nfl/odds?regio |       5.3 |
| live results        | ok       | live results: week 9, 0 final of 15, 0 in progress; spread 0-0, total 0-0, winner 0-0; play-by-play for 0 games                                                                                          |       4.1 |
| ratings             | ok       | (7668, 51) QB-out check: ok; swaps: none                                                                                                                                                                 |      20.9 |
| trends              | ok       | head-to-head cover margin      96                 0.355         7.079            2.793                                                                                                                   |      47   |
| players             | ok       | max           0.104589         1.360481    14.000000                                                                                                                                                     |      98   |
| positions           | ok       | Skill    525.0  0.008029  0.00260  0.0805                                                                                                                                                                |      20.3 |
| scheme              | ok       | scheme_plays (363642, 83) profiles for 32 teams as of 2026 9                                                                                                                                             |       5.1 |
| player splits       | ok       | player_splits.js 1.76 MB                                                                                                                                                                                 |      67.6 |
| model               | ok       | opp_skill_out_value           12.498       0.012          0.156                                                                                                                                          |      41.3 |
| qt shadow           | ok       | qt shadow: 3300 games, 16589 Questionable listings priced, 53s                                                                                                                                           |      53.8 |
| opener study        | ok       | opener study written                                                                                                                                                                                     |      42.7 |
| props by season     | ok       | DONE                                                                                                                                                                                                     |      23   |
| props               | error    | RuntimeError: on_upcast=True)                                                                                                                                                                            |       0.5 |
|                     |          |          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^                                                                                                                                        |           |
|                     |          |   File "/opt/hostedtoolcache/Python/3.11.18/x64/lib/python3.11/site-packages/pandas/core/internals/blocks.py", line 48                                                                                   |           |
| sizing backtest     | ok       | 2025   14-6    0.700        6.73                                                                                                                                                                         |       4.2 |
| threshold sweep     | ok       | DONE                                                                                                                                                                                                     |       1.5 |
| calibration start   | ok       | last 5 seasons     0.5288     0.5359     0.5429              0.69326            0.25006                0.68250              0.5639             0.5851             94              0.69274                |       1.5 |
| season backtest     | ok       | {'shrink0.1_sig1': 'not adopted', 'shrink0.1_sig1.15': 'not adopted', 'shrink0.2_sig1': 'not adopted', 'shrink0.2_sig1.15': 'not adopted', 'shrink0.3_sig1': 'not adopted', 'shrink0.3_sig1.15': 'not ad |      81.1 |
| legitimacy tests    | ok       | Reading: the line beats the model on the miss every season (it should; it is the market). The question the flag rests on is whether the model's disagreements with the line carry information, which the |      13.7 |
| audit reports       | ok       | Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).                                       |       2.2 |
| picks               | ok       | game_id  season  week  ...    bet_p  bet_odds  stake_pct                                                                                                                                                 |       0.9 |
|                     |          | 3149  2026_09_JAX_BAL    2026     9  ...      NaN       NaN        NaN                                                                                                                                   |           |
|                     |          | 3150  2026_09_CIN_ATL    2026     9  ...      NaN       Na                                                                                                                                               |           |
| log run             | ok       | run_at  season  week  ...  spread_line  total_line     bet                                                                                                                                               |       0   |
|                     |          | 3149  2026-11-05 23:30 UTC    2026     9  ...        -10.0        39.5                                                                                                                                   |           |
|                     |          | 3150  2026-11-05 23:30 UTC    2026     9                                                                                                                                                                 |           |
| record picks        | ok       | run_at  season  week  ...  spread_edge  total_edge  p_cover                                                                                                                                              |       0.5 |
|                     |          | 0  2026-10-04 12:37 UTC    2026     4  ...         5.08        2.49    0.673                                                                                                                             |           |
|                     |          | 1  2026-10-04 16:01 UTC    2026     4  ...                                                                                                                                                               |           |
| inputs fingerprint  | ok       | {'season': 2026, 'week': 9, 'starters': {'2026_09_JAX_BAL': ['00-0040981', '00-0036971', '2026-11-05 20:15'], '2026_09_CIN_ATL': ['00-0039917', '00-0036442', '2026-11-08 09:30'], '2026_09_DEN_CAR': [' |       0.5 |
| grade               | ok       |                                                                                                                                                                                                          |       6.8 |
| closing line value  | ok       | CLV 2026: 37 closed, 5 pending, avg +0.04 pts, 24% beat the close                                                                                                                                        |       1   |
| forecast history    | ok       | complete: 2215 games stored                                                                                                                                                                              |       0   |
| drift monitor       | ok       | **0 alerts, 0 to watch.** Long run = 2015 to 2024; recent = 2025 and 2026 so far. ALERT at |z| >= 2.5 or a CUSUM trip (h 5); WATCH at |z| >= 2.0.                                                        |       0.5 |
| shadow watch        | ok       | **0 rules ready for a look.** READY = 30+ settled live bets, a win rate past break-even beyond luck (p <= 0.1) and 5+ points more return per unit risked than the rule it would replace over the same se |       1   |
| ready checks        | ok       | **0 ready.** Each READY row opens a GitHub issue labelled ready-check (once per title).                                                                                                                  |       0.4 |
| tie check (sources) | error    | RuntimeError: numbers disagree: see reports/tie_check.md                                                                                                                                                 |       2.8 |
| export data room    | ok       |                                                                                                                                                                                                          |      89.6 |
| tie check (page)    | error    | RuntimeError: page files disagree with the sources: see reports/tie_check.md                                                                                                                             |       8.2 |
| standing checks     | ok       | True                                                                                                                                                                                                     |      33.7 |

**Failed steps above were skipped, not filled with stale data.**

## Week 9, 2026: 1 flagged of 15 games

| away_team   | home_team   |   away_exp |   home_exp |   spread_line |   total_line |   spread_edge |   total_edge | bet    |   stake_pct |
|:------------|:------------|-----------:|-----------:|--------------:|-------------:|--------------:|-------------:|:-------|------------:|
| HOU         | LAC         |      21.92 |      20.85 |            -6 |         40.5 |          4.92 |         2.27 | LAC +6 |        1.37 |

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
