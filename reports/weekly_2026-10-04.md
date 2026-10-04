# Weekly run, 2026-10-04 16:01 UTC

## Steps

| step                | status   | detail                                                                                                                                                                                                   |   seconds |
|:--------------------|:---------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------:|
| pull                | ok       | [('2026-10-04T16:01:16', 'schedules', 'all', 'https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv', 'ok', 2182389, '158506aad07a'), ('2026-10-04T16:01:16', 'players', 'all' |       3.1 |
| pull player history | ok       | [('2026-10-04T16:01:19', 'pfr_advstats', 2018, 'https://github.com/nflverse/nflverse-data/releases/download/pfr_advstats/advstats_week_def_2018.parquet', 'cached', 149299, ''), ('2026-10-04T16:01:19', |       0   |
| build               | ok       | team_games (8202, 142)                                                                                                                                                                                   |     127.6 |
| features            | ok       | [40 rows x 8 columns]                                                                                                                                                                                    |      10.8 |
| snap exposure       | ok       | snap exposure (329121, 10) seasons 2013 to 2026                                                                                                                                                          |       1.1 |
| verify              | ok       | Result: PASS                                                                                                                                                                                             |       0.4 |
| data checks         | ok       | True                                                                                                                                                                                                     |       0.4 |
| weather             | ok       | game_id           kickoff_et  ... precip        fetched_at                                                                                                                                               |     126.9 |
|                     |          | 0   2026_04_IND_WAS  2026-10-04 09:30:00  ...    0.0  2026-10-04 12:03                                                                                                                                   |           |
|                     |          | 1   2026_04_TEN_BAL  2026-10-04 13:00:00  ...    0.0  2026                                                                                                                                               |           |
| wind forecast       | ok       | 3                                                                                                                                                                                                        |      78.3 |
| lines               | ok       | {'ts': '2026-10-04T16-07-05Z', 'season': 2026, 'week': 4, 'rows': 14, 'errors': ''}                                                                                                                      |      82.1 |
| live results        | ok       | live results: week 4, 1 final of 16, 1 in progress; spread 1-0, total 0-1, winner 0-1; play-by-play for 2 games                                                                                          |       3.4 |
| ratings             | ok       | (7668, 51) QB-out check: ok; swaps: WAS Marcus Mariota -> Athan Kaliakmanis (depth chart)                                                                                                                |      21.1 |
| trends              | ok       | head-to-head cover margin      96                 0.355         7.079            2.793                                                                                                                   |      50   |
| players             | ok       | max           0.104589         1.360481    14.000000                                                                                                                                                     |     107.2 |
| positions           | ok       | Skill     541.0  0.007945  0.00250  0.0816                                                                                                                                                               |      22   |
| scheme              | ok       | scheme_plays (354592, 83) profiles for 32 teams as of 2026 4                                                                                                                                             |       5   |
| player splits       | ok       | player_splits.js 1.61 MB                                                                                                                                                                                 |      68.3 |
| model               | ok       | opp_skill_out_value           12.498       0.012          0.156                                                                                                                                          |      49.7 |
| qt shadow           | ok       | qt shadow: 3300 games, 16103 Questionable listings priced, 54s                                                                                                                                           |      55   |
| opener study        | ok       | opener study written                                                                                                                                                                                     |      49.1 |
| props by season     | ok       | DONE                                                                                                                                                                                                     |      21.3 |
| props               | ok       | props 2869 projections for week 4 graded rows 0 market lines on the cards 373 graded against the market 1833                                                                                             |      22.2 |
| sizing backtest     | ok       | 2025   14-6    0.700        6.73                                                                                                                                                                         |       4.1 |
| threshold sweep     | ok       | DONE                                                                                                                                                                                                     |       1.3 |
| calibration start   | ok       | last 5 seasons     0.5288     0.5359     0.5429              0.69326            0.25006                0.68250              0.5639             0.5851             94              0.69274                |       1.4 |
| season backtest     | ok       | {'shrink0.1_sig1': 'not adopted', 'shrink0.1_sig1.15': 'not adopted', 'shrink0.2_sig1': 'not adopted', 'shrink0.2_sig1.15': 'not adopted', 'shrink0.3_sig1': 'not adopted', 'shrink0.3_sig1.15': 'not ad |      77.9 |
| legitimacy tests    | ok       | Reading: the line beats the model on the miss every season (it should; it is the market). The question the flag rests on is whether the model's disagreements with the line carry information, which the |      13.1 |
| audit reports       | ok       | Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).                                       |       2.2 |
| picks               | ok       | game_id  season  week  ...     bet_p bet_odds stake_pct                                                                                                                                                  |       0.8 |
|                     |          | 3076  2026_04_PIT_CLE    2026     4  ...       NaN      NaN       NaN                                                                                                                                    |           |
|                     |          | 3077  2026_04_IND_WAS    2026     4  ...       NaN      NaN                                                                                                                                              |           |
| log run             | ok       | run_at  season  week  ... spread_line  total_line       bet                                                                                                                                              |       0   |
|                     |          | 3076  2026-10-04 16:01 UTC    2026     4  ...        -2.5        38.5                                                                                                                                    |           |
|                     |          | 3077  2026-10-04 16:01 UTC    2026     4                                                                                                                                                                 |           |
| record picks        | ok       | run_at  season  week  ... spread_edge total_edge  p_cover                                                                                                                                                |       0.5 |
|                     |          | 0  2026-10-04 12:37 UTC    2026     4  ...        5.08       2.49    0.673                                                                                                                               |           |
|                     |          | 1  2026-10-04 16:01 UTC    2026     4  ...       -                                                                                                                                                       |           |
| inputs fingerprint  | ok       | {'season': 2026, 'week': 4, 'starters': {'2026_04_PIT_CLE': ['00-0033537', '00-0023459', '2026-10-01 20:15'], '2026_04_IND_WAS': ['00-0032268', '00-0035710', '2026-10-04 09:30'], '2026_04_TEN_BAL': [' |       0.4 |
| grade               | ok       |                                                                                                                                                                                                          |       2.7 |
| closing line value  | ok       | CLV 2026: 5 closed, 5 pending, avg +0.20 pts, 20% beat the close                                                                                                                                         |       0.3 |
| forecast history    | ok       | complete: 2166 games stored                                                                                                                                                                              |       0   |
| drift monitor       | ok       | **0 alerts, 0 to watch.** Long run = 2015 to 2024; recent = 2025 and 2026 so far. ALERT at |z| >= 2.5 or a CUSUM trip (h 5); WATCH at |z| >= 2.0.                                                        |       0.4 |
| shadow watch        | ok       | **0 rules ready for a look.** READY = 30+ settled live bets, a win rate past break-even beyond luck (p <= 0.1) and 5+ points more return per unit risked than the rule it would replace over the same se |       0.9 |
| ready checks        | ok       | **0 ready.** Each READY row opens a GitHub issue labelled ready-check (once per title).                                                                                                                  |       0.4 |
| tie check (sources) | ok       | True                                                                                                                                                                                                     |       3.4 |
| export data room    | ok       |                                                                                                                                                                                                          |      87.8 |
| tie check (page)    | ok       | True                                                                                                                                                                                                     |       7.5 |
| standing checks     | ok       | True                                                                                                                                                                                                     |      34.9 |

## Week 4, 2026: 2 flagged of 16 games

| away_team   | home_team   |   away_exp |   home_exp |   spread_line |   total_line |   spread_edge |   total_edge | bet      |   stake_pct |
|:------------|:------------|-----------:|-----------:|--------------:|-------------:|--------------:|-------------:|:---------|------------:|
| JAX         | CIN         |      26.04 |      23.67 |           2.5 |         51.5 |         -4.87 |        -1.79 | JAX +2.5 |        2.12 |
| ARI         | NYG         |      21.81 |      23.67 |          -2.5 |         43.5 |          4.36 |         1.99 | NYG +2.5 |        1.45 |

Full table: reports/picks_2026_wk4.md

## Track record

## Rules compared

The flag is bet; the shadows are logged and graded on the same games but never bet, so the rule can be chosen on live results.

Backtest columns: the same rule on the three backtest windows, regular season weeks 1 to 17 (`picks.rule_records`).

| Rule | Bets | Settled | Record | Units | Avg CLV | Backtest 2015-18 | Backtest 2019-22 | Backtest 2023-25 |
|---|---|---|---|---|---|---|---|---|
| 4+ edge (the flag, bet) | 3 | 0 | nothing settled |  | +0.00 | 67-54 | 80-52 | 38-17 |
| shadow: 4.5+ edge | 2 | 0 | nothing settled |  | +0.00 | 46-36 | 55-39 | 23-15 |
| shadow: 4+ edge, model's side the underdog or pick'em | 3 | 0 | nothing settled |  | +0.00 | 52-37 | 72-43 | 30-14 |
| shadow: 4+ edge, weeks 1 to 13 only | 3 | 0 | nothing settled |  | +0.00 | 50-41 | 69-38 | 30-14 |

Full record: reports/track_record.md
