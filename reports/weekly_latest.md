# Weekly run, 2026-10-18 23:31 UTC

## Steps

| step                | status   | detail                                                                                                                                                                                                   |   seconds |
|:--------------------|:---------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------:|
| pull                | ok       | [('2026-10-18T23:31:46', 'schedules', 'all', 'https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv', 'ok', 2185286, '1394deaa50de'), ('2026-10-18T23:31:46', 'players', 'all' |       5.1 |
| pull player history | ok       | [('2026-10-18T23:31:52', 'pfr_advstats', 2018, 'https://github.com/nflverse/nflverse-data/releases/download/pfr_advstats/advstats_week_def_2018.parquet', 'cached', 149299, ''), ('2026-10-18T23:31:52', |       0   |
| build               | ok       | team_games (8202, 142)                                                                                                                                                                                   |      96.1 |
| features            | ok       | [40 rows x 8 columns]                                                                                                                                                                                    |       8.5 |
| snap exposure       | ok       | snap exposure (332019, 10) seasons 2013 to 2026                                                                                                                                                          |       1   |
| verify              | ok       | Result: PASS                                                                                                                                                                                             |       0.3 |
| data checks         | ok       | True                                                                                                                                                                                                     |       0.4 |
| weather             | ok       | game_id          kickoff_et  ... precip        fetched_at                                                                                                                                                |       2.1 |
|                     |          | 0    2026_06_LAC_KC 2026-10-18 16:25:00  ...    0.0  2026-10-18 19:33                                                                                                                                    |           |
|                     |          | 1    2026_06_DAL_GB 2026-10-18 20:20:00  ...    0.0  2026-10                                                                                                                                             |           |
| wind forecast       | ok       | 0                                                                                                                                                                                                        |       1.4 |
| lines               | ok       | {'ts': '2026-10-18T23-33-42Z', 'season': 2026, 'week': 6, 'rows': 16, 'errors': ''}                                                                                                                      |       6.6 |
| live results        | ok       | live results: week 6, 12 final of 14, 0 in progress; spread 4-8, total 6-6, winner 4-8; play-by-play for 12 games                                                                                        |       4.5 |
| ratings             | ok       | (7668, 51) QB-out check: ok; swaps: none                                                                                                                                                                 |      15.2 |
| trends              | ok       | head-to-head cover margin      96                 0.355         7.079            2.793                                                                                                                   |      34   |
| players             | ok       | max           0.104589         1.360481    14.000000                                                                                                                                                     |      75.9 |
| positions           | ok       | Skill    496.0  0.007557  0.00235  0.0869                                                                                                                                                                |      16.3 |
| scheme              | ok       | scheme_plays (359553, 83) profiles for 32 teams as of 2026 6                                                                                                                                             |       3.8 |
| player splits       | ok       | player_splits.js 1.7 MB                                                                                                                                                                                  |      47.9 |
| model               | ok       | opp_skill_out_value           12.498       0.012          0.156                                                                                                                                          |      43.4 |
| qt shadow           | ok       | qt shadow: 3300 games, 16219 Questionable listings priced, 42s                                                                                                                                           |      42.5 |
| opener study        | ok       | opener study written                                                                                                                                                                                     |      42.9 |
| props by season     | ok       | DONE                                                                                                                                                                                                     |      18.1 |
| props               | ok       | props 2524 projections for week 6 graded rows 0 market lines on the cards 336 graded against the market 5418                                                                                             |      19.1 |
| sizing backtest     | ok       | 2025   14-6    0.700        6.73                                                                                                                                                                         |       3.3 |
| threshold sweep     | ok       | DONE                                                                                                                                                                                                     |       1.3 |
| calibration start   | ok       | last 5 seasons     0.5288     0.5359     0.5429              0.69326            0.25006                0.68250              0.5639             0.5851             94              0.69274                |       1.2 |
| season backtest     | ok       | {'shrink0.1_sig1': 'not adopted', 'shrink0.1_sig1.15': 'not adopted', 'shrink0.2_sig1': 'not adopted', 'shrink0.2_sig1.15': 'not adopted', 'shrink0.3_sig1': 'not adopted', 'shrink0.3_sig1.15': 'not ad |      60   |
| legitimacy tests    | ok       | Reading: the line beats the model on the miss every season (it should; it is the market). The question the flag rests on is whether the model's disagreements with the line carry information, which the |       9.5 |
| audit reports       | ok       | Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).                                       |       1.6 |
| picks               | ok       | game_id  season  week  ... bet_p bet_odds stake_pct                                                                                                                                                      |       0.7 |
|                     |          | 3107  2026_06_SEA_DEN    2026     6  ...   NaN      NaN       NaN                                                                                                                                        |           |
|                     |          | 3108  2026_06_HOU_JAX    2026     6  ...   NaN      NaN       NaN                                                                                                                                        |           |
|                     |          | 31                                                                                                                                                                                                       |           |
| log run             | ok       | run_at  season  week  ... spread_line  total_line  bet                                                                                                                                                   |       0   |
|                     |          | 3107  2026-10-18 23:31 UTC    2026     6  ...        -2.5        40.5                                                                                                                                    |           |
|                     |          | 3108  2026-10-18 23:31 UTC    2026     6  ...                                                                                                                                                            |           |
| record picks        | ok       | run_at season week  ... spread_edge total_edge p_cover                                                                                                                                                   |       0.4 |
|                     |          | 0  2026-10-04 12:37 UTC   2026    4  ...        5.08       2.49   0.673                                                                                                                                  |           |
|                     |          | 1  2026-10-04 16:01 UTC   2026    4  ...       -4.87                                                                                                                                                     |           |
| inputs fingerprint  | ok       | {'season': 2026, 'week': 6, 'starters': {'2026_06_SEA_DEN': ['00-0039732', '00-0035704', '2026-10-15 20:15'], '2026_06_HOU_JAX': ['00-0036971', '00-0039163', '2026-10-18 09:30'], '2026_06_CHI_ATL': [' |       0.5 |
| grade               | ok       |                                                                                                                                                                                                          |       4.3 |
| closing line value  | ok       | CLV 2026: 25 closed, 3 pending, avg -0.12 pts, 24% beat the close                                                                                                                                        |       0.5 |
| forecast history    | ok       | complete: 2193 games stored                                                                                                                                                                              |       0   |
| drift monitor       | ok       | **0 alerts, 0 to watch.** Long run = 2015 to 2024; recent = 2025 and 2026 so far. ALERT at |z| >= 2.5 or a CUSUM trip (h 5); WATCH at |z| >= 2.0.                                                        |       0.3 |
| shadow watch        | ok       | **0 rules ready for a look.** READY = 30+ settled live bets, a win rate past break-even beyond luck (p <= 0.1) and 5+ points more return per unit risked than the rule it would replace over the same se |       0.7 |
| ready checks        | ok       | **0 ready.** Each READY row opens a GitHub issue labelled ready-check (once per title).                                                                                                                  |       0.3 |
| tie check (sources) | ok       | True                                                                                                                                                                                                     |       2.7 |
| export data room    | ok       |                                                                                                                                                                                                          |      69.3 |
| tie check (page)    | ok       | True                                                                                                                                                                                                     |       7.3 |
| standing checks     | ok       | True                                                                                                                                                                                                     |      26.6 |

## Week 6, 2026: 0 flagged of 14 games

No game clears the flag thresholds.

Full table: reports/picks_2026_wk6.md

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
