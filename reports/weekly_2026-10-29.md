# Weekly run, 2026-10-29 22:38 UTC

## Steps

| step                | status   | detail                                                                                                                                                                                                   |   seconds |
|:--------------------|:---------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------:|
| pull                | ok       | [('2026-10-29T22:38:35', 'schedules', 'all', 'https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv', 'ok', 2186983, '4cf75a64a522'), ('2026-10-29T22:38:35', 'players', 'all' |       5.1 |
| pull player history | ok       | [('2026-10-29T22:38:40', 'pfr_advstats', 2018, 'https://github.com/nflverse/nflverse-data/releases/download/pfr_advstats/advstats_week_def_2018.parquet', 'cached', 149299, ''), ('2026-10-29T22:38:40', |       0   |
| build               | ok       | team_games (8202, 142)                                                                                                                                                                                   |     186.6 |
| features            | ok       | [40 rows x 8 columns]                                                                                                                                                                                    |      16.7 |
| snap exposure       | ok       | snap exposure (334537, 10) seasons 2013 to 2026                                                                                                                                                          |       1.7 |
| verify              | ok       | Result: PASS                                                                                                                                                                                             |       0.5 |
| data checks         | ok       | True                                                                                                                                                                                                     |       0.5 |
| weather             | ok       | game_id          kickoff_et  ...  precip        fetched_at                                                                                                                                               |     126.6 |
|                     |          | 0    2026_08_CAR_GB 2026-10-29 20:15:00  ...     0.0  2026-10-29 18:42                                                                                                                                   |           |
|                     |          | 1   2026_08_BAL_BUF 2026-11-01 13:00:00  ...     0.0  2026                                                                                                                                               |           |
| wind forecast       | ok       | 1                                                                                                                                                                                                        |       0.9 |
| lines               | ok       | {'ts': '2026-10-29T22-44-15Z', 'season': 2026, 'week': 8, 'rows': 14, 'errors': 'oddsapi: 401 Client Error: Unauthorized for url: https://api.the-odds-api.com/v4/sports/americanfootball_nfl/odds?regio |       4.9 |
| live results        | ok       | live results: week 8, 0 final of 14, 0 in progress; spread 0-0, total 0-0, winner 0-0; play-by-play for 0 games                                                                                          |       6.1 |
| ratings             | ok       | (7668, 51) QB-out check: ok; swaps: none                                                                                                                                                                 |      34.2 |
| trends              | ok       | head-to-head cover margin      96                 0.355         7.079            2.793                                                                                                                   |      80   |
| players             | ok       | max           0.104589         1.360481    14.000000                                                                                                                                                     |     147.9 |
| positions           | ok       | Skill    483.0  0.007911  0.00250  0.0840                                                                                                                                                                |      26.4 |
| scheme              | ok       | scheme_plays (361898, 83) profiles for 32 teams as of 2026 8                                                                                                                                             |       7.7 |
| player splits       | ok       | player_splits.js 1.74 MB                                                                                                                                                                                 |     116.5 |
| model               | ok       | opp_skill_out_value           12.498       0.012          0.156                                                                                                                                          |      69.7 |
| qt shadow           | ok       | qt shadow: 3300 games, 16510 Questionable listings priced, 76s                                                                                                                                           |      76.8 |
| opener study        | ok       | opener study written                                                                                                                                                                                     |      68.5 |
| props by season     | ok       | DONE                                                                                                                                                                                                     |      34   |
| props               | error    | RuntimeError: on_upcast=True)                                                                                                                                                                            |       0.6 |
|                     |          |          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^                                                                                                                                        |           |
|                     |          |   File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/site-packages/pandas/core/internals/blocks.py", line 48                                                                                   |           |
| sizing backtest     | ok       | 2025   14-6    0.700        6.73                                                                                                                                                                         |       5.9 |
| threshold sweep     | ok       | DONE                                                                                                                                                                                                     |       1.7 |
| calibration start   | ok       | last 5 seasons     0.5288     0.5359     0.5429              0.69326            0.25006                0.68250              0.5639             0.5851             94              0.69274                |       1.7 |
| season backtest     | ok       | {'shrink0.1_sig1': 'not adopted', 'shrink0.1_sig1.15': 'not adopted', 'shrink0.2_sig1': 'not adopted', 'shrink0.2_sig1.15': 'not adopted', 'shrink0.3_sig1': 'not adopted', 'shrink0.3_sig1.15': 'not ad |     103.1 |
| legitimacy tests    | ok       | Reading: the line beats the model on the miss every season (it should; it is the market). The question the flag rests on is whether the model's disagreements with the line carry information, which the |      19   |
| audit reports       | ok       | Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).                                       |       3   |
| picks               | ok       | game_id  season  week  ...     bet_p  bet_odds  stake_pct                                                                                                                                                |       1.3 |
|                     |          | 3135   2026_08_CAR_GB    2026     8  ...       NaN       NaN        NaN                                                                                                                                  |           |
|                     |          | 3136  2026_08_BAL_BUF    2026     8  ...       NaN                                                                                                                                                       |           |
| log run             | ok       | run_at  season  ...  total_line       bet                                                                                                                                                                |       0   |
|                     |          | 3135  2026-10-29 22:38 UTC    2026  ...        46.5                                                                                                                                                      |           |
|                     |          | 3136  2026-10-29 22:38 UTC    2026  ...        54.5                                                                                                                                                      |           |
|                     |          | 3137  2026-10-                                                                                                                                                                                           |           |
| record picks        | ok       | run_at  season  week  ...  spread_edge  total_edge  p_cover                                                                                                                                              |       0.6 |
|                     |          | 0  2026-10-04 12:37 UTC    2026     4  ...         5.08        2.49    0.673                                                                                                                             |           |
|                     |          | 1  2026-10-04 16:01 UTC    2026     4  ...                                                                                                                                                               |           |
| inputs fingerprint  | ok       | {'season': 2026, 'week': 8, 'starters': {'2026_08_CAR_GB': ['00-0036264', '00-0039150', '2026-10-29 20:15'], '2026_08_BAL_BUF': ['00-0034857', '00-0035993', '2026-11-01 13:00'], '2026_08_TEN_CIN': ['0 |       0.7 |
| grade               | ok       |                                                                                                                                                                                                          |       8.4 |
| closing line value  | ok       | CLV 2026: 30 closed, 5 pending, avg -0.15 pts, 20% beat the close                                                                                                                                        |       1.2 |
| forecast history    | ok       | complete: 2204 games stored                                                                                                                                                                              |       0   |
| drift monitor       | ok       | **0 alerts, 0 to watch.** Long run = 2015 to 2024; recent = 2025 and 2026 so far. ALERT at |z| >= 2.5 or a CUSUM trip (h 5); WATCH at |z| >= 2.0.                                                        |       0.5 |
| shadow watch        | ok       | **0 rules ready for a look.** READY = 30+ settled live bets, a win rate past break-even beyond luck (p <= 0.1) and 5+ points more return per unit risked than the rule it would replace over the same se |       1.2 |
| ready checks        | ok       | **0 ready.** Each READY row opens a GitHub issue labelled ready-check (once per title).                                                                                                                  |       0.4 |
| tie check (sources) | error    | RuntimeError: numbers disagree: see reports/tie_check.md                                                                                                                                                 |       3.7 |
| export data room    | ok       |                                                                                                                                                                                                          |     129.6 |
| tie check (page)    | error    | RuntimeError: page files disagree with the sources: see reports/tie_check.md                                                                                                                             |      10.6 |
| standing checks     | ok       | True                                                                                                                                                                                                     |      47   |

**Failed steps above were skipped, not filled with stale data.**

## Week 8, 2026: 2 flagged of 14 games

| away_team   | home_team   |   away_exp |   home_exp |   spread_line |   total_line |   spread_edge |   total_edge | bet      |   stake_pct |
|:------------|:------------|-----------:|-----------:|--------------:|-------------:|--------------:|-------------:|:---------|------------:|
| KC          | DEN         |      20.5  |      23.33 |          -1.5 |         40.5 |          4.33 |         3.33 | DEN +1.5 |        0.64 |
| PHI         | WAS         |      22.42 |      23.46 |           6   |         40.5 |         -4.96 |         5.38 | PHI +6   |        1.84 |

Full table: reports/picks_2026_wk8.md

## Track record

## Rules compared

The flag is bet; the shadows are logged and graded on the same games but never bet, so the rule can be chosen on live results.

Backtest columns: the same rule on the three backtest windows, regular season weeks 1 to 17 (`picks.rule_records`).

| Rule | Bets | Settled | Record | Units | Avg CLV | Backtest 2015-18 | Backtest 2019-22 | Backtest 2023-25 |
|---|---|---|---|---|---|---|---|---|
| 4+ edge (the flag, bet) | 7 | 5 | 2-3 (40%) | -1.12 | -0.21 | 67-54 | 80-52 | 38-17 |
| shadow: 4.5+ edge | 5 | 4 | 1-3 (25%) | -2.05 | -0.30 | 46-36 | 55-39 | 23-15 |
| shadow: 4+ edge, model's side the underdog or pick'em | 7 | 5 | 2-3 (40%) | -1.12 | -0.21 | 52-37 | 72-43 | 30-14 |
| shadow: 4+ edge, weeks 1 to 13 only | 7 | 5 | 2-3 (40%) | -1.12 | -0.21 | 50-41 | 69-38 | 30-14 |

Full record: reports/track_record.md
