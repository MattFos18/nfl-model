# Weekly run, 2026-10-22 21:23 UTC

## Steps

| step                | status   | detail                                                                                                                                                                                                   |   seconds |
|:--------------------|:---------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------:|
| pull                | ok       | [('2026-10-22T21:23:48', 'schedules', 'all', 'https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv', 'ok', 2186338, '129a7f516d03'), ('2026-10-22T21:23:48', 'players', 'all' |       8.5 |
| pull player history | ok       | [('2026-10-22T21:23:56', 'pfr_advstats', 2018, 'https://github.com/nflverse/nflverse-data/releases/download/pfr_advstats/advstats_week_def_2018.parquet', 'cached', 149299, ''), ('2026-10-22T21:23:56', |       0   |
| build               | ok       | team_games (8202, 142)                                                                                                                                                                                   |     132.9 |
| features            | ok       | [40 rows x 8 columns]                                                                                                                                                                                    |      11.1 |
| snap exposure       | ok       | snap exposure (333227, 10) seasons 2013 to 2026                                                                                                                                                          |       1.3 |
| verify              | ok       | Result: PASS                                                                                                                                                                                             |       0.4 |
| data checks         | ok       | True                                                                                                                                                                                                     |       0.3 |
| weather             | ok       | game_id          kickoff_et  ...  precip        fetched_at                                                                                                                                               |       3.5 |
|                     |          | 0    2026_07_NE_CHI 2026-10-22 20:15:00  ...     0.0  2026-10-22 17:26                                                                                                                                   |           |
|                     |          | 1    2026_07_PIT_NO 2026-10-25 09:30:00  ...     0.0  2026                                                                                                                                               |           |
| wind forecast       | ok       | 1                                                                                                                                                                                                        |       0.8 |
| lines               | ok       | {'ts': '2026-10-22T21-26-27Z', 'season': 2026, 'week': 7, 'rows': 224, 'errors': ''}                                                                                                                     |       8.2 |
| live results        | ok       | live results: week 7, 0 final of 14, 0 in progress; spread 0-0, total 0-0, winner 0-0; play-by-play for 0 games                                                                                          |       4.9 |
| ratings             | ok       | (7668, 51) QB-out check: ok; swaps: PHI Jalen Hurts -> Tanner McKee (depth chart)                                                                                                                        |      22.7 |
| trends              | ok       | head-to-head cover margin      96                 0.355         7.079            2.793                                                                                                                   |      45.7 |
| players             | ok       | max           0.104589         1.360481    14.000000                                                                                                                                                     |      98   |
| positions           | ok       | Skill    489.0  0.007831  0.0023  0.0844                                                                                                                                                                 |      19.5 |
| scheme              | ok       | scheme_plays (360185, 83) profiles for 32 teams as of 2026 7                                                                                                                                             |       5.1 |
| player splits       | ok       | player_splits.js 1.72 MB                                                                                                                                                                                 |      62.2 |
| model               | ok       | opp_skill_out_value           12.498       0.012          0.156                                                                                                                                          |      42.8 |
| qt shadow           | ok       | qt shadow: 3300 games, 16427 Questionable listings priced, 52s                                                                                                                                           |      52.8 |
| opener study        | ok       | opener study written                                                                                                                                                                                     |      42   |
| props by season     | ok       | DONE                                                                                                                                                                                                     |      21   |
| props               | error    | RuntimeError: on_upcast=True)                                                                                                                                                                            |       0.5 |
|                     |          |          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^                                                                                                                                        |           |
|                     |          |   File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/site-packages/pandas/core/internals/blocks.py", line 48                                                                                   |           |
| sizing backtest     | ok       | 2025   14-6    0.700        6.73                                                                                                                                                                         |       4.1 |
| threshold sweep     | ok       | DONE                                                                                                                                                                                                     |       1.3 |
| calibration start   | ok       | last 5 seasons     0.5288     0.5359     0.5429              0.69326            0.25006                0.68250              0.5639             0.5851             94              0.69274                |       1.3 |
| season backtest     | ok       | {'shrink0.1_sig1': 'not adopted', 'shrink0.1_sig1.15': 'not adopted', 'shrink0.2_sig1': 'not adopted', 'shrink0.2_sig1.15': 'not adopted', 'shrink0.3_sig1': 'not adopted', 'shrink0.3_sig1.15': 'not ad |      78   |
| legitimacy tests    | ok       | Reading: the line beats the model on the miss every season (it should; it is the market). The question the flag rests on is whether the model's disagreements with the line carry information, which the |      12.9 |
| audit reports       | ok       | Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).                                       |       2.1 |
| picks               | ok       | game_id  season  week  ...  bet_p  bet_odds  stake_pct                                                                                                                                                   |       0.9 |
|                     |          | 3121   2026_07_NE_CHI    2026     7  ...    NaN       NaN        NaN                                                                                                                                     |           |
|                     |          | 3122   2026_07_PIT_NO    2026     7  ...    NaN       NaN                                                                                                                                                |           |
| log run             | ok       | run_at  season  week  ...  spread_line  total_line bet                                                                                                                                                   |       0   |
|                     |          | 3121  2026-10-22 21:23 UTC    2026     7  ...          3.0        51.0                                                                                                                                   |           |
|                     |          | 3122  2026-10-22 21:23 UTC    2026     7  ...                                                                                                                                                            |           |
| record picks        | ok       | run_at season week  ... spread_edge total_edge p_cover                                                                                                                                                   |       0.4 |
|                     |          | 0  2026-10-04 12:37 UTC   2026    4  ...        5.08       2.49   0.673                                                                                                                                  |           |
|                     |          | 1  2026-10-04 16:01 UTC   2026    4  ...       -4.87                                                                                                                                                     |           |
| inputs fingerprint  | ok       | {'season': 2026, 'week': 7, 'starters': {'2026_07_NE_CHI': ['00-0039918', '00-0039851', '2026-10-22 20:15'], '2026_07_PIT_NO': ['00-0040743', '00-0023459', '2026-10-25 09:30'], '2026_07_SF_ATL': ['00- |       0.5 |
| grade               | ok       |                                                                                                                                                                                                          |       5.8 |
| closing line value  | ok       | CLV 2026: 26 closed, 2 pending, avg -0.15 pts, 23% beat the close                                                                                                                                        |       0.8 |
| forecast history    | ok       | complete: 2196 games stored                                                                                                                                                                              |       0   |
| drift monitor       | ok       | **0 alerts, 0 to watch.** Long run = 2015 to 2024; recent = 2025 and 2026 so far. ALERT at |z| >= 2.5 or a CUSUM trip (h 5); WATCH at |z| >= 2.0.                                                        |       0.4 |
| shadow watch        | ok       | **0 rules ready for a look.** READY = 30+ settled live bets, a win rate past break-even beyond luck (p <= 0.1) and 5+ points more return per unit risked than the rule it would replace over the same se |       0.9 |
| ready checks        | ok       | **0 ready.** Each READY row opens a GitHub issue labelled ready-check (once per title).                                                                                                                  |       0.4 |
| tie check (sources) | error    | RuntimeError: numbers disagree: see reports/tie_check.md                                                                                                                                                 |       3.2 |
| export data room    | ok       |                                                                                                                                                                                                          |      85.9 |
| tie check (page)    | error    | RuntimeError: page files disagree with the sources: see reports/tie_check.md                                                                                                                             |       8.1 |
| standing checks     | ok       | True                                                                                                                                                                                                     |      31.7 |

**Failed steps above were skipped, not filled with stale data.**

## Week 7, 2026: 0 flagged of 14 games

No game clears the flag thresholds.

Full table: reports/picks_2026_wk7.md

## Track record

## Rules compared

The flag is bet; the shadows are logged and graded on the same games but never bet, so the rule can be chosen on live results.

Backtest columns: the same rule on the three backtest windows, regular season weeks 1 to 17 (`picks.rule_records`).

| Rule | Bets | Settled | Record | Units | Avg CLV | Backtest 2015-18 | Backtest 2019-22 | Backtest 2023-25 |
|---|---|---|---|---|---|---|---|---|
| 4+ edge (the flag, bet) | 4 | 4 | 2-2 (50%) | -0.12 | +0.00 | 67-54 | 80-52 | 38-17 |
| shadow: 4.5+ edge | 3 | 3 | 1-2 (33%) | -1.05 | +0.00 | 46-36 | 55-39 | 23-15 |
| shadow: 4+ edge, model's side the underdog or pick'em | 4 | 4 | 2-2 (50%) | -0.12 | +0.00 | 52-37 | 72-43 | 30-14 |
| shadow: 4+ edge, weeks 1 to 13 only | 4 | 4 | 2-2 (50%) | -0.12 | +0.00 | 50-41 | 69-38 | 30-14 |

Full record: reports/track_record.md
