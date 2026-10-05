# Weekly run, 2026-10-04 23:51 UTC

## Steps

| step                | status   | detail                                                                                                                                                                                                   |   seconds |
|:--------------------|:---------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------:|
| pull                | ok       | [('2026-10-04T23:51:41', 'schedules', 'all', 'https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv', 'ok', 2182513, '6ace3a6d7eac'), ('2026-10-04T23:51:41', 'players', 'all' |       6.4 |
| pull player history | ok       | [('2026-10-04T23:51:47', 'pfr_advstats', 2018, 'https://github.com/nflverse/nflverse-data/releases/download/pfr_advstats/advstats_week_def_2018.parquet', 'cached', 149299, ''), ('2026-10-04T23:51:47', |       0   |
| build               | ok       | team_games (8202, 142)                                                                                                                                                                                   |      96.2 |
| features            | ok       | [40 rows x 8 columns]                                                                                                                                                                                    |       8.4 |
| snap exposure       | ok       | snap exposure (329121, 10) seasons 2013 to 2026                                                                                                                                                          |       1   |
| verify              | ok       | Result: PASS                                                                                                                                                                                             |       0.5 |
| data checks         | ok       | True                                                                                                                                                                                                     |       0.4 |
| weather             | ok       | game_id           kickoff_et  ... precip        fetched_at                                                                                                                                               |       6.9 |
|                     |          | 0   2026_04_LAC_SEA  2026-10-04 16:25:00  ...    0.0  2026-10-04 19:53                                                                                                                                   |           |
|                     |          | 1   2026_04_DET_CAR  2026-10-04 20:20:00  ...    0.0  2026                                                                                                                                               |           |
| wind forecast       | ok       | 0                                                                                                                                                                                                        |       1   |
| lines               | ok       | {'ts': '2026-10-04T23-53-42Z', 'season': 2026, 'week': 4, 'rows': 17, 'errors': ''}                                                                                                                      |       5.3 |
| live results        | ok       | live results: week 4, 14 final of 16, 0 in progress; spread 9-3-2, total 4-10, winner 10-4; play-by-play for 14 games                                                                                    |       2.7 |
| ratings             | ok       | (7668, 51) QB-out check: ok; swaps: none                                                                                                                                                                 |      16.5 |
| trends              | ok       | head-to-head cover margin      96                 0.355         7.079            2.793                                                                                                                   |      33.7 |
| players             | ok       | max           0.104589         1.360481    14.000000                                                                                                                                                     |      82.1 |
| positions           | ok       | Skill     541.0  0.007945  0.00250  0.0816                                                                                                                                                               |      18.1 |
| scheme              | ok       | scheme_plays (355711, 83) profiles for 32 teams as of 2026 4                                                                                                                                             |       3.7 |
| player splits       | ok       | player_splits.js 1.63 MB                                                                                                                                                                                 |      46.5 |
| model               | ok       | opp_skill_out_value           12.498       0.012          0.156                                                                                                                                          |      43.9 |
| qt shadow           | ok       | qt shadow: 3300 games, 16070 Questionable listings priced, 41s                                                                                                                                           |      42   |
| opener study        | ok       | opener study written                                                                                                                                                                                     |      43.7 |
| props by season     | ok       | DONE                                                                                                                                                                                                     |      17.3 |
| props               | ok       | props 2849 projections for week 4 graded rows 0 market lines on the cards 371 graded against the market 1833                                                                                             |      16.1 |
| sizing backtest     | ok       | 2025   14-6    0.700        6.73                                                                                                                                                                         |       3.2 |
| threshold sweep     | ok       | DONE                                                                                                                                                                                                     |       1   |
| calibration start   | ok       | last 5 seasons     0.5288     0.5359     0.5429              0.69326            0.25006                0.68250              0.5639             0.5851             94              0.69274                |       1.1 |
| season backtest     | ok       | {'shrink0.1_sig1': 'not adopted', 'shrink0.1_sig1.15': 'not adopted', 'shrink0.2_sig1': 'not adopted', 'shrink0.2_sig1.15': 'not adopted', 'shrink0.3_sig1': 'not adopted', 'shrink0.3_sig1.15': 'not ad |      60.1 |
| legitimacy tests    | ok       | Reading: the line beats the model on the miss every season (it should; it is the market). The question the flag rests on is whether the model's disagreements with the line carry information, which the |      10   |
| audit reports       | ok       | Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).                                       |       1.7 |
| picks               | ok       | game_id  season  week  ...     bet_p bet_odds stake_pct                                                                                                                                                  |       0.6 |
|                     |          | 3076  2026_04_PIT_CLE    2026     4  ...       NaN      NaN       NaN                                                                                                                                    |           |
|                     |          | 3077  2026_04_IND_WAS    2026     4  ...  0.551738   -102.0                                                                                                                                              |           |
| log run             | ok       | run_at  season  week  ... spread_line  total_line       bet                                                                                                                                              |       0   |
|                     |          | 3076  2026-10-04 23:51 UTC    2026     4  ...        -2.5        38.5                                                                                                                                    |           |
|                     |          | 3077  2026-10-04 23:51 UTC    2026     4                                                                                                                                                                 |           |
| record picks        | ok       | run_at season week  ... spread_edge total_edge p_cover                                                                                                                                                   |       0.4 |
|                     |          | 0  2026-10-04 12:37 UTC   2026    4  ...        5.08       2.49   0.673                                                                                                                                  |           |
|                     |          | 1  2026-10-04 16:01 UTC   2026    4  ...       -4.87                                                                                                                                                     |           |
| inputs fingerprint  | ok       | {'season': 2026, 'week': 4, 'starters': {'2026_04_PIT_CLE': ['00-0033537', '00-0023459', '2026-10-01 20:15'], '2026_04_IND_WAS': ['00-0032268', '00-0035710', '2026-10-04 09:30'], '2026_04_TEN_BAL': [' |       0.3 |
| grade               | ok       |                                                                                                                                                                                                          |       2   |
| closing line value  | ok       | CLV 2026: 10 closed, 0 pending, avg -0.05 pts, 20% beat the close                                                                                                                                        |       0.2 |
| forecast history    | ok       | 1 games fetched in 2s, 2174 stored, 0 left                                                                                                                                                               |       1.8 |
| drift monitor       | ok       | **0 alerts, 0 to watch.** Long run = 2015 to 2024; recent = 2025 and 2026 so far. ALERT at |z| >= 2.5 or a CUSUM trip (h 5); WATCH at |z| >= 2.0.                                                        |       0.4 |
| shadow watch        | ok       | **0 rules ready for a look.** READY = 30+ settled live bets, a win rate past break-even beyond luck (p <= 0.1) and 5+ points more return per unit risked than the rule it would replace over the same se |       0.8 |
| ready checks        | ok       | **0 ready.** Each READY row opens a GitHub issue labelled ready-check (once per title).                                                                                                                  |       0.4 |
| tie check (sources) | error    | RuntimeError: numbers disagree: see reports/tie_check.md                                                                                                                                                 |       2.6 |
| export data room    | ok       |                                                                                                                                                                                                          |      70.9 |
| tie check (page)    | error    | RuntimeError: page files disagree with the sources: see reports/tie_check.md                                                                                                                             |       6.5 |
| standing checks     | ok       | True                                                                                                                                                                                                     |      27.6 |

**Failed steps above were skipped, not filled with stale data.**

## Week 4, 2026: 3 flagged of 16 games

| away_team   | home_team   |   away_exp |   home_exp |   spread_line |   total_line |   spread_edge |   total_edge | bet      |   stake_pct |
|:------------|:------------|-----------:|-----------:|--------------:|-------------:|--------------:|-------------:|:---------|------------:|
| IND         | WAS         |      24.41 |      24.64 |          -4.5 |         46.5 |          4.73 |         2.55 | WAS +4.5 |        2.36 |
| JAX         | CIN         |      26.02 |      23.65 |           2.5 |         51.5 |         -4.87 |        -1.82 | JAX +2.5 |        2.45 |
| ARI         | NYG         |      21.76 |      23.53 |          -2.5 |         44.5 |          4.28 |         0.79 | NYG +2.5 |        1.17 |

Full table: reports/picks_2026_wk4.md

## Track record

## Rules compared

The flag is bet; the shadows are logged and graded on the same games but never bet, so the rule can be chosen on live results.

Backtest columns: the same rule on the three backtest windows, regular season weeks 1 to 17 (`picks.rule_records`).

| Rule | Bets | Settled | Record | Units | Avg CLV | Backtest 2015-18 | Backtest 2019-22 | Backtest 2023-25 |
|---|---|---|---|---|---|---|---|---|
| 4+ edge (the flag, bet) | 3 | 3 | 2-1 (67%) | +0.88 | +0.00 | 67-54 | 80-52 | 38-17 |
| shadow: 4.5+ edge | 2 | 2 | 1-1 (50%) | -0.05 | +0.00 | 46-36 | 55-39 | 23-15 |
| shadow: 4+ edge, model's side the underdog or pick'em | 3 | 3 | 2-1 (67%) | +0.88 | +0.00 | 52-37 | 72-43 | 30-14 |
| shadow: 4+ edge, weeks 1 to 13 only | 3 | 3 | 2-1 (67%) | +0.88 | +0.00 | 50-41 | 69-38 | 30-14 |

Full record: reports/track_record.md
