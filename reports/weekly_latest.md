# Weekly run, 2026-11-27 01:37 UTC

## Steps

| step                | status   | detail                                                                                                                                                                                                   |   seconds |
|:--------------------|:---------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------:|
| pull                | ok       | [('2026-11-27T01:37:28', 'schedules', 'all', 'https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv', 'ok', 2192427, 'b63b040b4b9f'), ('2026-11-27T01:37:28', 'players', 'all' |       9.5 |
| pull player history | ok       | [('2026-11-27T01:37:38', 'pfr_advstats', 2018, 'https://github.com/nflverse/nflverse-data/releases/download/pfr_advstats/advstats_week_def_2018.parquet', 'cached', 149299, ''), ('2026-11-27T01:37:38', |       0   |
| build               | ok       | team_games (8202, 142)                                                                                                                                                                                   |     124.1 |
| features            | ok       | [40 rows x 8 columns]                                                                                                                                                                                    |       9.4 |
| snap exposure       | ok       | snap exposure (339865, 10) seasons 2013 to 2026                                                                                                                                                          |       1.2 |
| verify              | ok       | Result: PASS                                                                                                                                                                                             |       0.4 |
| data checks         | ok       | True                                                                                                                                                                                                     |       0.3 |
| weather             | ok       | game_id          kickoff_et  ...  precip        fetched_at                                                                                                                                               |      47.9 |
|                     |          | 0    2026_12_KC_BUF 2026-11-26 20:20:00  ...    27.7  2026-11-26 20:39                                                                                                                                   |           |
|                     |          | 1   2026_12_DEN_PIT 2026-11-27 15:00:00  ...     0.0  2026                                                                                                                                               |           |
| wind forecast       | ok       | 4                                                                                                                                                                                                        |       4.3 |
| lines               | ok       | {'ts': '2026-11-27T01-40-46Z', 'season': 2026, 'week': 12, 'rows': 12, 'errors': 'oddsapi: 401 Client Error: Unauthorized for url: https://api.the-odds-api.com/v4/sports/americanfootball_nfl/odds?regi |      44.1 |
| live results        | ok       | live results: week 12, 3 final of 16, 1 in progress; spread 0-3, total 1-2, winner 1-2; play-by-play for 4 games                                                                                         |       6.9 |
| ratings             | ok       | (7668, 51) QB-out check: ok; swaps: NE Drake Maye -> Tommy DeVito (depth chart)                                                                                                                          |      20.2 |
| trends              | ok       | head-to-head cover margin      96                 0.355         7.079            2.793                                                                                                                   |      46.1 |
| players             | ok       | max           0.104589         1.360481    14.000000                                                                                                                                                     |      93.8 |
| positions           | ok       | Skill     580.0  0.007827  0.00270  0.0869                                                                                                                                                               |      20.8 |
| scheme              | ok       | scheme_plays (369099, 83) profiles for 32 teams as of 2026 12                                                                                                                                            |       5   |
| player splits       | ok       | player_splits.js 1.83 MB                                                                                                                                                                                 |      67.1 |
| model               | ok       | opp_skill_out_value           12.498       0.012          0.156                                                                                                                                          |      39.8 |
| qt shadow           | ok       | qt shadow: 3300 games, 16793 Questionable listings priced, 49s                                                                                                                                           |      49.7 |
| opener study        | ok       | opener study written                                                                                                                                                                                     |      39.5 |
| props by season     | ok       | DONE                                                                                                                                                                                                     |      21.5 |
| props               | error    | RuntimeError: on_upcast=True)                                                                                                                                                                            |       0.4 |
|                     |          |          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^                                                                                                                                        |           |
|                     |          |   File "/opt/hostedtoolcache/Python/3.11.18/x64/lib/python3.11/site-packages/pandas/core/internals/blocks.py", line 48                                                                                   |           |
| sizing backtest     | ok       | 2025   14-6    0.700        6.73                                                                                                                                                                         |       3.7 |
| threshold sweep     | ok       | DONE                                                                                                                                                                                                     |       1.3 |
| calibration start   | ok       | last 5 seasons     0.5288     0.5359     0.5429              0.69326            0.25006                0.68250              0.5639             0.5851             94              0.69274                |       1.3 |
| season backtest     | ok       | {'shrink0.1_sig1': 'not adopted', 'shrink0.1_sig1.15': 'not adopted', 'shrink0.2_sig1': 'not adopted', 'shrink0.2_sig1.15': 'not adopted', 'shrink0.3_sig1': 'not adopted', 'shrink0.3_sig1.15': 'not ad |      77.3 |
| legitimacy tests    | ok       | Reading: the line beats the model on the miss every season (it should; it is the market). The question the flag rests on is whether the model's disagreements with the line carry information, which the |      11.7 |
| audit reports       | ok       | Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).                                       |       2   |
| picks               | ok       | game_id  season  week  ...     bet_p  bet_odds  stake_pct                                                                                                                                                |       0.9 |
|                     |          | 3191    2026_12_GB_LA    2026    12  ...       NaN       NaN        NaN                                                                                                                                  |           |
|                     |          | 3192  2026_12_CHI_DET    2026    12  ...  0.552116    -1                                                                                                                                                 |           |
| log run             | ok       | run_at  season  ...  total_line       bet                                                                                                                                                                |       0   |
|                     |          | 3191  2026-11-27 01:37 UTC    2026  ...        44.5                                                                                                                                                      |           |
|                     |          | 3192  2026-11-27 01:37 UTC    2026  ...        55.5  DET +2.5                                                                                                                                            |           |
|                     |          | 3193  2026-11-                                                                                                                                                                                           |           |
| record picks        | ok       | run_at  season  week  ...  spread_edge  total_edge  p_cover                                                                                                                                              |       0.4 |
|                     |          | 0   2026-10-04 12:37 UTC    2026     4  ...         5.08        2.49    0.673                                                                                                                            |           |
|                     |          | 1   2026-10-04 16:01 UTC    2026     4  ...                                                                                                                                                              |           |
| inputs fingerprint  | ok       | {'season': 2026, 'week': 12, 'starters': {'2026_12_GB_LA': ['00-0026498', '00-0036264', '2026-11-25 20:00'], '2026_12_CHI_DET': ['00-0033106', '00-0039918', '2026-11-26 13:00'], '2026_12_PHI_DAL': ['0 |       0.5 |
| grade               | ok       |                                                                                                                                                                                                          |       6.6 |
| closing line value  | ok       | CLV 2026: 64 closed, 5 pending, avg +0.02 pts, 17% beat the close                                                                                                                                        |       1   |
| forecast history    | ok       | complete: 2243 games stored                                                                                                                                                                              |       0   |
| drift monitor       | ok       | **0 alerts, 0 to watch.** Long run = 2015 to 2024; recent = 2025 and 2026 so far. ALERT at |z| >= 2.5 or a CUSUM trip (h 5); WATCH at |z| >= 2.0.                                                        |       0.4 |
| shadow watch        | ok       | **0 rules ready for a look.** READY = 30+ settled live bets, a win rate past break-even beyond luck (p <= 0.1) and 5+ points more return per unit risked than the rule it would replace over the same se |       0.9 |
| ready checks        | ok       | **1 ready.** Each READY row opens a GitHub issue labelled ready-check (once per title).                                                                                                                  |       0.4 |
| tie check (sources) | error    | RuntimeError: numbers disagree: see reports/tie_check.md                                                                                                                                                 |       2.6 |
| export data room    | ok       |                                                                                                                                                                                                          |      86.5 |
| tie check (page)    | error    | RuntimeError: page files disagree with the sources: see reports/tie_check.md                                                                                                                             |       7.7 |
| standing checks     | ok       | True                                                                                                                                                                                                     |      32.2 |

**Failed steps above were skipped, not filled with stale data.**

## Week 12, 2026: 4 flagged of 16 games

| away_team   | home_team   |   away_exp |   home_exp |   spread_line |   total_line |   spread_edge |   total_edge | bet      |   stake_pct |
|:------------|:------------|-----------:|-----------:|--------------:|-------------:|--------------:|-------------:|:---------|------------:|
| CHI         | DET         |      24.37 |      26.62 |          -2.5 |         55.5 |          4.76 |        -4.51 | DET +2.5 |        1.93 |
| DEN         | PIT         |      17.73 |      17.94 |          -4.5 |         36.5 |          4.71 |        -0.82 | PIT +4.5 |        2.35 |
| NYG         | IND         |      23.02 |      21.45 |          -6   |         41.5 |          4.43 |         2.97 | IND +6   |        1.28 |
| NE          | LAC         |      19.02 |      21.75 |          -2.5 |         35.5 |          5.23 |         5.26 | LAC +2.5 |        1.68 |

Full table: reports/picks_2026_wk12.md

## Track record

## Rules compared

The flag is bet; the shadows are logged and graded on the same games but never bet, so the rule can be chosen on live results.

Backtest columns: the same rule on the three backtest windows, regular season weeks 1 to 17 (`picks.rule_records`).

| Rule | Bets | Settled | Record | Units | Avg CLV | Backtest 2015-18 | Backtest 2019-22 | Backtest 2023-25 |
|---|---|---|---|---|---|---|---|---|
| 4+ edge (the flag, bet) | 14 | 11 | 4-7 (36%) | -3.40 | +0.32 | 67-54 | 80-52 | 38-17 |
| shadow: 4.5+ edge | 9 | 7 | 3-4 (43%) | -1.32 | +0.28 | 46-36 | 55-39 | 23-15 |
| shadow: 4+ edge, model's side the underdog or pick'em | 14 | 11 | 4-7 (36%) | -3.40 | +0.32 | 52-37 | 72-43 | 30-14 |
| shadow: 4+ edge, weeks 1 to 13 only | 14 | 11 | 4-7 (36%) | -3.40 | +0.32 | 50-41 | 69-38 | 30-14 |

Full record: reports/track_record.md
