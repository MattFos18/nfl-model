# Weekly run, 2026-11-12 23:25 UTC

## Steps

| step                | status   | detail                                                                                                                                                                                                   |   seconds |
|:--------------------|:---------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------:|
| pull                | ok       | [('2026-11-12T23:25:48', 'schedules', 'all', 'https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv', 'ok', 2189959, '5ae004ff6d26'), ('2026-11-12T23:25:48', 'players', 'all' |       7   |
| pull player history | ok       | [('2026-11-12T23:25:55', 'pfr_advstats', 2018, 'https://github.com/nflverse/nflverse-data/releases/download/pfr_advstats/advstats_week_def_2018.parquet', 'cached', 149299, ''), ('2026-11-12T23:25:55', |       0   |
| build               | ok       | team_games (8202, 142)                                                                                                                                                                                   |     197   |
| features            | ok       | [40 rows x 8 columns]                                                                                                                                                                                    |      16.7 |
| snap exposure       | ok       | snap exposure (337249, 10) seasons 2013 to 2026                                                                                                                                                          |       1.8 |
| verify              | ok       | Result: PASS                                                                                                                                                                                             |       0.5 |
| data checks         | ok       | True                                                                                                                                                                                                     |       0.5 |
| weather             | ok       | game_id          kickoff_et  ...  precip        fetched_at                                                                                                                                               |      79.3 |
|                     |          | 0   2026_10_WAS_NYG 2026-11-12 20:15:00  ...     2.2  2026-11-12 18:29                                                                                                                                   |           |
|                     |          | 1    2026_10_NE_DET 2026-11-15 09:30:00  ...     0.0  2026                                                                                                                                               |           |
| wind forecast       | ok       | 1                                                                                                                                                                                                        |       1.1 |
| lines               | ok       | {'ts': '2026-11-12T23-30-52Z', 'season': 2026, 'week': 10, 'rows': 14, 'errors': 'oddsapi: 401 Client Error: Unauthorized for url: https://api.the-odds-api.com/v4/sports/americanfootball_nfl/odds?regi |       5.6 |
| live results        | ok       | live results: week 10, 0 final of 14, 0 in progress; spread 0-0, total 0-0, winner 0-0; play-by-play for 0 games                                                                                         |       7.7 |
| ratings             | ok       | (7668, 51) QB-out check: ok; swaps: MIA Malik Willis -> Kyle McCord (depth chart); ARI Gardner Minshew -> Carson Beck (depth chart); SEA Sam Darnold -> Drew Lock (depth chart); BAL Tyler Huntley -> Ja |      35.8 |
| trends              | ok       | head-to-head cover margin      96                 0.355         7.079            2.793                                                                                                                   |      77.7 |
| players             | ok       | max           0.104589         1.360481    14.000000                                                                                                                                                     |     158   |
| positions           | ok       | Skill    500.0  0.007901  0.00245  0.0876                                                                                                                                                                |      29.9 |
| scheme              | ok       | scheme_plays (365492, 83) profiles for 32 teams as of 2026 10                                                                                                                                            |       8.1 |
| player splits       | ok       | player_splits.js 1.79 MB                                                                                                                                                                                 |     117.4 |
| model               | ok       | opp_skill_out_value           12.498       0.012          0.156                                                                                                                                          |      65.3 |
| qt shadow           | ok       | qt shadow: 3300 games, 16644 Questionable listings priced, 85s                                                                                                                                           |      86.2 |
| opener study        | ok       | opener study written                                                                                                                                                                                     |      65.6 |
| props by season     | ok       | DONE                                                                                                                                                                                                     |      35.2 |
| props               | error    | RuntimeError: on_upcast=True)                                                                                                                                                                            |       0.7 |
|                     |          |          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^                                                                                                                                        |           |
|                     |          |   File "/opt/hostedtoolcache/Python/3.11.18/x64/lib/python3.11/site-packages/pandas/core/internals/blocks.py", line 48                                                                                   |           |
| sizing backtest     | ok       | 2025   14-6    0.700        6.73                                                                                                                                                                         |       6.6 |
| threshold sweep     | ok       | DONE                                                                                                                                                                                                     |       2   |
| calibration start   | ok       | last 5 seasons     0.5288     0.5359     0.5429              0.69326            0.25006                0.68250              0.5639             0.5851             94              0.69274                |       2   |
| season backtest     | ok       | {'shrink0.1_sig1': 'not adopted', 'shrink0.1_sig1.15': 'not adopted', 'shrink0.2_sig1': 'not adopted', 'shrink0.2_sig1.15': 'not adopted', 'shrink0.3_sig1': 'not adopted', 'shrink0.3_sig1.15': 'not ad |     107   |
| legitimacy tests    | ok       | Reading: the line beats the model on the miss every season (it should; it is the market). The question the flag rests on is whether the model's disagreements with the line carry information, which the |      21   |
| audit reports       | ok       | Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).                                       |       3.2 |
| picks               | ok       | game_id  season  week  ...  bet_p  bet_odds  stake_pct                                                                                                                                                   |       1.4 |
|                     |          | 3164  2026_10_WAS_NYG    2026    10  ...    NaN       NaN        NaN                                                                                                                                     |           |
|                     |          | 3165   2026_10_NE_DET    2026    10  ...    NaN       NaN                                                                                                                                                |           |
| log run             | ok       | run_at  season  week  ...  spread_line  total_line bet                                                                                                                                                   |       0   |
|                     |          | 3164  2026-11-12 23:25 UTC    2026    10  ...          1.5        40.5                                                                                                                                   |           |
|                     |          | 3165  2026-11-12 23:25 UTC    2026    10  ...                                                                                                                                                            |           |
| record picks        | ok       | run_at season week  ... spread_edge total_edge p_cover                                                                                                                                                   |       0.7 |
|                     |          | 0  2026-10-04 12:37 UTC   2026    4  ...        5.08       2.49   0.673                                                                                                                                  |           |
|                     |          | 1  2026-10-04 16:01 UTC   2026    4  ...       -4.87                                                                                                                                                     |           |
| inputs fingerprint  | ok       | {'season': 2026, 'week': 10, 'starters': {'2026_10_WAS_NYG': ['00-0039923', '00-0039910', '2026-11-12 20:15'], '2026_10_NE_DET': ['00-0033106', '00-0039851', '2026-11-15 09:30'], '2026_10_KC_ATL': ['0 |       0.7 |
| grade               | ok       |                                                                                                                                                                                                          |       9.6 |
| closing line value  | ok       | CLV 2026: 44 closed, 3 pending, avg +0.03 pts, 25% beat the close                                                                                                                                        |       1.4 |
| forecast history    | ok       | complete: 2226 games stored                                                                                                                                                                              |       0.1 |
| drift monitor       | ok       | **0 alerts, 0 to watch.** Long run = 2015 to 2024; recent = 2025 and 2026 so far. ALERT at |z| >= 2.5 or a CUSUM trip (h 5); WATCH at |z| >= 2.0.                                                        |       0.6 |
| shadow watch        | ok       | **0 rules ready for a look.** READY = 30+ settled live bets, a win rate past break-even beyond luck (p <= 0.1) and 5+ points more return per unit risked than the rule it would replace over the same se |       1.4 |
| ready checks        | ok       | **0 ready.** Each READY row opens a GitHub issue labelled ready-check (once per title).                                                                                                                  |       0.6 |
| tie check (sources) | error    | RuntimeError: numbers disagree: see reports/tie_check.md                                                                                                                                                 |       4.1 |
| export data room    | ok       |                                                                                                                                                                                                          |     139.6 |
| tie check (page)    | error    | RuntimeError: page files disagree with the sources: see reports/tie_check.md                                                                                                                             |      12   |
| standing checks     | ok       | True                                                                                                                                                                                                     |      49.2 |

**Failed steps above were skipped, not filled with stale data.**

## Week 10, 2026: 0 flagged of 14 games

No game clears the flag thresholds.

Full table: reports/picks_2026_wk10.md

## Track record

## Rules compared

The flag is bet; the shadows are logged and graded on the same games but never bet, so the rule can be chosen on live results.

Backtest columns: the same rule on the three backtest windows, regular season weeks 1 to 17 (`picks.rule_records`).

| Rule | Bets | Settled | Record | Units | Avg CLV | Backtest 2015-18 | Backtest 2019-22 | Backtest 2023-25 |
|---|---|---|---|---|---|---|---|---|
| 4+ edge (the flag, bet) | 8 | 8 | 3-5 (38%) | -2.29 | +0.31 | 67-54 | 80-52 | 38-17 |
| shadow: 4.5+ edge | 5 | 5 | 2-3 (40%) | -1.21 | +0.30 | 46-36 | 55-39 | 23-15 |
| shadow: 4+ edge, model's side the underdog or pick'em | 8 | 8 | 3-5 (38%) | -2.29 | +0.31 | 52-37 | 72-43 | 30-14 |
| shadow: 4+ edge, weeks 1 to 13 only | 8 | 8 | 3-5 (38%) | -2.29 | +0.31 | 50-41 | 69-38 | 30-14 |

Full record: reports/track_record.md
