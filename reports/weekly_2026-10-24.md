# Weekly run, 2026-10-24 17:08 UTC

## Steps

| step                | status   | detail                                                                                                                                                                                                   |   seconds |
|:--------------------|:---------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------:|
| pull                | ok       | [('2026-10-24T17:08:10', 'schedules', 'all', 'https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv', 'ok', 2186409, '0d44bf2217d1'), ('2026-10-24T17:08:10', 'players', 'all' |       9.1 |
| pull player history | ok       | [('2026-10-24T17:08:19', 'pfr_advstats', 2018, 'https://github.com/nflverse/nflverse-data/releases/download/pfr_advstats/advstats_week_def_2018.parquet', 'cached', 149299, ''), ('2026-10-24T17:08:19', |       0   |
| build               | ok       | team_games (8202, 142)                                                                                                                                                                                   |     129.7 |
| features            | ok       | [40 rows x 8 columns]                                                                                                                                                                                    |      10.5 |
| snap exposure       | ok       | snap exposure (333319, 10) seasons 2013 to 2026                                                                                                                                                          |       1.3 |
| verify              | ok       | Result: PASS                                                                                                                                                                                             |       0.4 |
| data checks         | ok       | True                                                                                                                                                                                                     |       0.3 |
| weather             | ok       | game_id          kickoff_et  ...  precip        fetched_at                                                                                                                                               |     125.7 |
|                     |          | 0    2026_07_PIT_NO 2026-10-25 09:30:00  ...     0.0  2026-10-24 13:10                                                                                                                                   |           |
|                     |          | 1   2026_07_CIN_BAL 2026-10-25 13:00:00  ...     0.0  2026                                                                                                                                               |           |
| wind forecast       | ok       | 6                                                                                                                                                                                                        |       3.9 |
| lines               | ok       | {'ts': '2026-10-24T17-12-51Z', 'season': 2026, 'week': 7, 'rows': 13, 'errors': 'oddsapi: 401 Client Error: Unauthorized for url: https://api.the-odds-api.com/v4/sports/americanfootball_nfl/odds?regio |      64.8 |
| live results        | ok       | live results: week 7, 1 final of 14, 0 in progress; spread 0-1, total 0-1, winner 0-1; play-by-play for 1 games                                                                                          |       4.1 |
| ratings             | ok       | (7668, 51) QB-out check: ok; swaps: PHI Jalen Hurts -> Tanner McKee (depth chart)                                                                                                                        |      20.9 |
| trends              | ok       | head-to-head cover margin      96                 0.355         7.079            2.793                                                                                                                   |      42.9 |
| players             | ok       | max           0.104589         1.360481    14.000000                                                                                                                                                     |      92.8 |
| positions           | ok       | Skill    489.0  0.007831  0.0023  0.0844                                                                                                                                                                 |      19.6 |
| scheme              | ok       | scheme_plays (360301, 83) profiles for 32 teams as of 2026 7                                                                                                                                             |       4.9 |
| player splits       | ok       | player_splits.js 1.72 MB                                                                                                                                                                                 |      57.6 |
| model               | ok       | opp_skill_out_value           12.498       0.012          0.156                                                                                                                                          |      43   |
| qt shadow           | ok       | qt shadow: 3300 games, 16351 Questionable listings priced, 48s                                                                                                                                           |      48.8 |
| opener study        | ok       | opener study written                                                                                                                                                                                     |      44.2 |
| props by season     | ok       | DONE                                                                                                                                                                                                     |      21.7 |
| props               | error    | RuntimeError: on_upcast=True)                                                                                                                                                                            |       0.5 |
|                     |          |          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^                                                                                                                                        |           |
|                     |          |   File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/site-packages/pandas/core/internals/blocks.py", line 48                                                                                   |           |
| sizing backtest     | ok       | 2025   14-6    0.700        6.73                                                                                                                                                                         |       3.9 |
| threshold sweep     | ok       | DONE                                                                                                                                                                                                     |       1.4 |
| calibration start   | ok       | last 5 seasons     0.5288     0.5359     0.5429              0.69326            0.25006                0.68250              0.5639             0.5851             94              0.69274                |       1.4 |
| season backtest     | ok       | {'shrink0.1_sig1': 'not adopted', 'shrink0.1_sig1.15': 'not adopted', 'shrink0.2_sig1': 'not adopted', 'shrink0.2_sig1.15': 'not adopted', 'shrink0.3_sig1': 'not adopted', 'shrink0.3_sig1.15': 'not ad |      73.9 |
| legitimacy tests    | ok       | Reading: the line beats the model on the miss every season (it should; it is the market). The question the flag rests on is whether the model's disagreements with the line carry information, which the |      12.2 |
| audit reports       | ok       | Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).                                       |       2.1 |
| picks               | ok       | game_id  season  week  ...     bet_p  bet_odds  stake_pct                                                                                                                                                |       0.9 |
|                     |          | 3121   2026_07_NE_CHI    2026     7  ...       NaN       NaN        NaN                                                                                                                                  |           |
|                     |          | 3122   2026_07_PIT_NO    2026     7  ...       NaN                                                                                                                                                       |           |
| log run             | ok       | run_at  season  ...  total_line       bet                                                                                                                                                                |       0   |
|                     |          | 3121  2026-10-24 17:08 UTC    2026  ...        51.0                                                                                                                                                      |           |
|                     |          | 3122  2026-10-24 17:08 UTC    2026  ...        44.5                                                                                                                                                      |           |
|                     |          | 3123  2026-10-                                                                                                                                                                                           |           |
| record picks        | ok       | run_at  season  week  ...  spread_edge  total_edge  p_cover                                                                                                                                              |       0.5 |
|                     |          | 0  2026-10-04 12:37 UTC    2026     4  ...         5.08        2.49    0.673                                                                                                                             |           |
|                     |          | 1  2026-10-04 16:01 UTC    2026     4  ...                                                                                                                                                               |           |
| inputs fingerprint  | ok       | {'season': 2026, 'week': 7, 'starters': {'2026_07_NE_CHI': ['00-0039918', '00-0039851', '2026-10-22 20:15'], '2026_07_PIT_NO': ['00-0040743', '00-0023459', '2026-10-25 09:30'], '2026_07_SF_ATL': ['00- |       0.5 |
| grade               | ok       |                                                                                                                                                                                                          |       6.2 |
| closing line value  | ok       | CLV 2026: 27 closed, 2 pending, avg -0.17 pts, 22% beat the close                                                                                                                                        |       0.7 |
| forecast history    | ok       | 1 games fetched in 1s, 2197 stored, 0 left                                                                                                                                                               |       1.3 |
| drift monitor       | ok       | **0 alerts, 0 to watch.** Long run = 2015 to 2024; recent = 2025 and 2026 so far. ALERT at |z| >= 2.5 or a CUSUM trip (h 5); WATCH at |z| >= 2.0.                                                        |       0.4 |
| shadow watch        | ok       | **0 rules ready for a look.** READY = 30+ settled live bets, a win rate past break-even beyond luck (p <= 0.1) and 5+ points more return per unit risked than the rule it would replace over the same se |       0.9 |
| ready checks        | ok       | **0 ready.** Each READY row opens a GitHub issue labelled ready-check (once per title).                                                                                                                  |       0.4 |
| tie check (sources) | error    | RuntimeError: numbers disagree: see reports/tie_check.md                                                                                                                                                 |       3.3 |
| export data room    | ok       |                                                                                                                                                                                                          |      79.5 |
| tie check (page)    | error    | RuntimeError: page files disagree with the sources: see reports/tie_check.md                                                                                                                             |       7.5 |
| standing checks     | ok       | True                                                                                                                                                                                                     |      29   |

**Failed steps above were skipped, not filled with stale data.**

## Week 7, 2026: 1 flagged of 14 games

| away_team   | home_team   |   away_exp |   home_exp |   spread_line |   total_line |   spread_edge |   total_edge | bet      |   stake_pct |
|:------------|:------------|-----------:|-----------:|--------------:|-------------:|--------------:|-------------:|:---------|------------:|
| CIN         | BAL         |      25.27 |      28.63 |          -1.5 |         47.5 |          4.86 |          6.4 | BAL +1.5 |        0.99 |

Full table: reports/picks_2026_wk7.md

## Track record

## Rules compared

The flag is bet; the shadows are logged and graded on the same games but never bet, so the rule can be chosen on live results.

Backtest columns: the same rule on the three backtest windows, regular season weeks 1 to 17 (`picks.rule_records`).

| Rule | Bets | Settled | Record | Units | Avg CLV | Backtest 2015-18 | Backtest 2019-22 | Backtest 2023-25 |
|---|---|---|---|---|---|---|---|---|
| 4+ edge (the flag, bet) | 5 | 4 | 2-2 (50%) | -0.12 | +0.00 | 67-54 | 80-52 | 38-17 |
| shadow: 4.5+ edge | 4 | 3 | 1-2 (33%) | -1.05 | +0.00 | 46-36 | 55-39 | 23-15 |
| shadow: 4+ edge, model's side the underdog or pick'em | 5 | 4 | 2-2 (50%) | -0.12 | +0.00 | 52-37 | 72-43 | 30-14 |
| shadow: 4+ edge, weeks 1 to 13 only | 5 | 4 | 2-2 (50%) | -0.12 | +0.00 | 50-41 | 69-38 | 30-14 |

Full record: reports/track_record.md
