# Weekly run, 2026-10-06 16:28 UTC

## Steps

| step                | status   | detail                                                                                                                                                                                                   |   seconds |
|:--------------------|:---------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------:|
| pull                | ok       | [('2026-10-06T16:28:59', 'schedules', 'all', 'https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv', 'ok', 2182782, '1896f36a70ab'), ('2026-10-06T16:28:59', 'players', 'all' |       9.2 |
| pull player history | ok       | [('2026-10-06T16:29:08', 'pfr_advstats', 2018, 'https://github.com/nflverse/nflverse-data/releases/download/pfr_advstats/advstats_week_def_2018.parquet', 'cached', 149299, ''), ('2026-10-06T16:29:08', |       0   |
| build               | ok       | team_games (8202, 142)                                                                                                                                                                                   |     193.1 |
| features            | ok       | [40 rows x 8 columns]                                                                                                                                                                                    |      16.5 |
| snap exposure       | ok       | snap exposure (330511, 10) seasons 2013 to 2026                                                                                                                                                          |       1.5 |
| verify              | ok       | Result: PASS                                                                                                                                                                                             |       0.5 |
| data checks         | ok       | True                                                                                                                                                                                                     |       0.5 |
| weather             | ok       | game_id           kickoff_et  ... precip        fetched_at                                                                                                                                               |       6.6 |
|                     |          | 0   2026_05_PHI_JAX  2026-10-11 09:30:00  ...    0.0  2026-10-06 12:32                                                                                                                                   |           |
|                     |          | 1   2026_05_CIN_MIA  2026-10-11 13:00:00  ...    0.0  2026                                                                                                                                               |           |
| wind forecast       | ok       | 0                                                                                                                                                                                                        |       0.1 |
| lines               | ok       | {'ts': '2026-10-06T16-32-48Z', 'season': 2026, 'week': 4, 'rows': 15, 'errors': ''}                                                                                                                      |       7.4 |
| live results        | ok       | live results: week 4, 16 final of 16, 0 in progress; spread 10-4-2, total 5-11, winner 10-6; play-by-play for 16 games                                                                                   |       4.7 |
| ratings             | ok       | (7668, 51) QB-out check: ok; swaps: none                                                                                                                                                                 |      33.5 |
| trends              | ok       | head-to-head cover margin      96                 0.355         7.079            2.793                                                                                                                   |      72.6 |
| players             | ok       | max           0.104589         1.360481    14.000000                                                                                                                                                     |     162.2 |
| positions           | ok       | Skill     541.0  0.007945  0.00250  0.0816                                                                                                                                                               |      33.8 |
| scheme              | ok       | scheme_plays (356476, 83) profiles for 32 teams as of 2026 5                                                                                                                                             |       7.2 |
| player splits       | ok       | player_splits.js 1.65 MB                                                                                                                                                                                 |      99.9 |
| model               | ok       | opp_skill_out_value           12.498       0.012          0.156                                                                                                                                          |      66.4 |
| qt shadow           | ok       | qt shadow: 3300 games, 16167 Questionable listings priced, 79s                                                                                                                                           |      80.7 |
| opener study        | ok       | opener study written                                                                                                                                                                                     |      65.9 |
| props by season     | ok       | DONE                                                                                                                                                                                                     |      29.9 |
| props               | ok       | props 2740 projections for week 5 graded rows 11275 market lines on the cards 0 graded against the market 3661                                                                                           |      40.2 |
| sizing backtest     | ok       | 2025   14-6    0.700        6.73                                                                                                                                                                         |       5.8 |
| threshold sweep     | ok       | DONE                                                                                                                                                                                                     |       1.7 |
| calibration start   | ok       | last 5 seasons     0.5288     0.5359     0.5429              0.69326            0.25006                0.68250              0.5639             0.5851             94              0.69274                |       1.8 |
| season backtest     | ok       | {'shrink0.1_sig1': 'not adopted', 'shrink0.1_sig1.15': 'not adopted', 'shrink0.2_sig1': 'not adopted', 'shrink0.2_sig1.15': 'not adopted', 'shrink0.3_sig1': 'not adopted', 'shrink0.3_sig1.15': 'not ad |      98.8 |
| legitimacy tests    | ok       | Reading: the line beats the model on the miss every season (it should; it is the market). The question the flag rests on is whether the model's disagreements with the line carry information, which the |      19.3 |
| audit reports       | ok       | Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).                                       |       2.9 |
| picks               | ok       | game_id  season  week  ...     bet_p bet_odds stake_pct                                                                                                                                                  |       1.1 |
|                     |          | 3092   2026_05_TB_DAL    2026     5  ...       NaN      NaN       NaN                                                                                                                                    |           |
|                     |          | 3093  2026_05_PHI_JAX    2026     5  ...       NaN      NaN                                                                                                                                              |           |
| log run             | ok       | run_at  season  week  ... spread_line  total_line     bet                                                                                                                                                |       0   |
|                     |          | 3092  2026-10-06 16:28 UTC    2026     5  ...         8.5        47.5                                                                                                                                    |           |
|                     |          | 3093  2026-10-06 16:28 UTC    2026     5  ..                                                                                                                                                             |           |
| record picks        | ok       | run_at  season  week  ... spread_edge total_edge  p_cover                                                                                                                                                |       0.6 |
|                     |          | 0  2026-10-04 12:37 UTC    2026     4  ...        5.08       2.49    0.673                                                                                                                               |           |
|                     |          | 1  2026-10-04 16:01 UTC    2026     4  ...       -                                                                                                                                                       |           |
| inputs fingerprint  | ok       | {'season': 2026, 'week': 5, 'starters': {'2026_05_TB_DAL': ['00-0033077', '00-0041251', '2026-10-08 20:15'], '2026_05_PHI_JAX': ['00-0036971', '00-0036389', '2026-10-11 09:30'], '2026_05_CIN_MIA': ['0 |       0.6 |
| grade               | ok       |                                                                                                                                                                                                          |       4   |
| closing line value  | ok       | CLV 2026: 10 closed, 5 pending, avg -0.05 pts, 20% beat the close                                                                                                                                        |       0.5 |
| forecast history    | ok       | complete: 2176 games stored                                                                                                                                                                              |       0.1 |
| drift monitor       | ok       | **0 alerts, 0 to watch.** Long run = 2015 to 2024; recent = 2025 and 2026 so far. ALERT at |z| >= 2.5 or a CUSUM trip (h 5); WATCH at |z| >= 2.0.                                                        |       0.5 |
| shadow watch        | ok       | **0 rules ready for a look.** READY = 30+ settled live bets, a win rate past break-even beyond luck (p <= 0.1) and 5+ points more return per unit risked than the rule it would replace over the same se |       1.2 |
| ready checks        | ok       | **0 ready.** Each READY row opens a GitHub issue labelled ready-check (once per title).                                                                                                                  |       0.5 |
| tie check (sources) | error    | RuntimeError: numbers disagree: see reports/tie_check.md                                                                                                                                                 |       3.8 |
| export data room    | ok       |                                                                                                                                                                                                          |     134.6 |
| tie check (page)    | error    | RuntimeError: page files disagree with the sources: see reports/tie_check.md                                                                                                                             |       9.6 |
| standing checks     | error    | RuntimeError: a fixed bug is back: see reports/standing_checks.md                                                                                                                                        |      44.2 |

**Failed steps above were skipped, not filled with stale data.**

## Week 5, 2026: 2 flagged of 15 games

| away_team   | home_team   |   away_exp |   home_exp |   spread_line |   total_line |   spread_edge |   total_edge | bet    |   stake_pct |
|:------------|:------------|-----------:|-----------:|--------------:|-------------:|--------------:|-------------:|:-------|------------:|
| CHI         | GB          |      22.07 |      23.41 |            -3 |         45.5 |          4.34 |        -0.02 | GB +3  |        0.31 |
| BAL         | ATL         |      28.16 |      25.22 |             3 |         43.5 |         -5.94 |         9.88 | BAL +3 |        1.71 |

Full table: reports/picks_2026_wk5.md

## Track record

## Rules compared

The flag is bet; the shadows are logged and graded on the same games but never bet, so the rule can be chosen on live results.

Backtest columns: the same rule on the three backtest windows, regular season weeks 1 to 17 (`picks.rule_records`).

| Rule | Bets | Settled | Record | Units | Avg CLV | Backtest 2015-18 | Backtest 2019-22 | Backtest 2023-25 |
|---|---|---|---|---|---|---|---|---|
| 4+ edge (the flag, bet) | 5 | 3 | 2-1 (67%) | +0.88 | +0.00 | 67-54 | 80-52 | 38-17 |
| shadow: 4.5+ edge | 3 | 2 | 1-1 (50%) | -0.05 | +0.00 | 46-36 | 55-39 | 23-15 |
| shadow: 4+ edge, model's side the underdog or pick'em | 5 | 3 | 2-1 (67%) | +0.88 | +0.00 | 52-37 | 72-43 | 30-14 |
| shadow: 4+ edge, weeks 1 to 13 only | 5 | 3 | 2-1 (67%) | +0.88 | +0.00 | 50-41 | 69-38 | 30-14 |

Full record: reports/track_record.md
