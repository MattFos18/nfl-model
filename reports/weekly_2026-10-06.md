# Weekly run, 2026-10-06 22:05 UTC

## Steps

| step                | status   | detail                                                                                                                                                                                                   |   seconds |
|:--------------------|:---------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------:|
| pull                | ok       | [('2026-10-06T22:05:11', 'schedules', 'all', 'https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv', 'missing', 0, ''), ('2026-10-06T22:05:11', 'players', 'all', 'https://gi |       4.7 |
| pull player history | ok       | [('2026-10-06T22:05:16', 'pfr_advstats', 2018, 'https://github.com/nflverse/nflverse-data/releases/download/pfr_advstats/advstats_week_def_2018.parquet', 'cached', 149299, ''), ('2026-10-06T22:05:16', |       0   |
| build               | ok       | team_games (8202, 142)                                                                                                                                                                                   |     191.9 |
| features            | ok       | [40 rows x 8 columns]                                                                                                                                                                                    |      19.1 |
| snap exposure       | ok       | snap exposure (330511, 10) seasons 2013 to 2026                                                                                                                                                          |       1.3 |
| verify              | ok       | Result: PASS                                                                                                                                                                                             |       0.5 |
| data checks         | ok       | True                                                                                                                                                                                                     |       0.5 |
| weather             | ok       | game_id           kickoff_et  ... precip        fetched_at                                                                                                                                               |       7.3 |
|                     |          | 0   2026_05_PHI_JAX  2026-10-11 09:30:00  ...    0.0  2026-10-06 18:08                                                                                                                                   |           |
|                     |          | 1   2026_05_CIN_MIA  2026-10-11 13:00:00  ...    0.1  2026                                                                                                                                               |           |
| wind forecast       | ok       | 0                                                                                                                                                                                                        |       0.1 |
| lines               | ok       | {'ts': '2026-10-06T22-08-57Z', 'season': 2026, 'week': 5, 'rows': 15, 'errors': ''}                                                                                                                      |       5.3 |
| live results        | ok       | live results: week 5, 0 final of 15, 0 in progress; spread 0-0, total 0-0, winner 0-0; play-by-play for 0 games                                                                                          |       4.1 |
| ratings             | ok       | (7668, 51) QB-out check: ok; swaps: none                                                                                                                                                                 |      33.7 |
| trends              | ok       | head-to-head cover margin      96                 0.355         7.079            2.793                                                                                                                   |      83.1 |
| players             | ok       | max           0.104589         1.360481    14.000000                                                                                                                                                     |     166.3 |
| positions           | ok       | Skill    506.0  0.008006  0.00250  0.0806                                                                                                                                                                |      30.4 |
| scheme              | ok       | scheme_plays (356476, 83) profiles for 32 teams as of 2026 5                                                                                                                                             |       7.8 |
| player splits       | ok       | player_splits.js 1.65 MB                                                                                                                                                                                 |     124.2 |
| model               | ok       | opp_skill_out_value           12.498       0.012          0.156                                                                                                                                          |      69.4 |
| qt shadow           | ok       | qt shadow: 3300 games, 16222 Questionable listings priced, 86s                                                                                                                                           |      87   |
| opener study        | ok       | opener study written                                                                                                                                                                                     |      71.6 |
| props by season     | ok       | DONE                                                                                                                                                                                                     |      31.8 |
| props               | ok       | props 2730 projections for week 5 graded rows 0 market lines on the cards 163 graded against the market 3661                                                                                             |      36.5 |
| sizing backtest     | ok       | 2025   14-6    0.700        6.73                                                                                                                                                                         |       6.6 |
| threshold sweep     | ok       | DONE                                                                                                                                                                                                     |       1.8 |
| calibration start   | ok       | last 5 seasons     0.5288     0.5359     0.5429              0.69326            0.25006                0.68250              0.5639             0.5851             94              0.69274                |       1.8 |
| season backtest     | ok       | {'shrink0.1_sig1': 'not adopted', 'shrink0.1_sig1.15': 'not adopted', 'shrink0.2_sig1': 'not adopted', 'shrink0.2_sig1.15': 'not adopted', 'shrink0.3_sig1': 'not adopted', 'shrink0.3_sig1.15': 'not ad |     102.2 |
| legitimacy tests    | ok       | Reading: the line beats the model on the miss every season (it should; it is the market). The question the flag rests on is whether the model's disagreements with the line carry information, which the |      21.3 |
| audit reports       | ok       | Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).                                       |       3   |
| picks               | ok       | game_id  season  week  ...     bet_p bet_odds stake_pct                                                                                                                                                  |       1.2 |
|                     |          | 3092   2026_05_TB_DAL    2026     5  ...       NaN      NaN       NaN                                                                                                                                    |           |
|                     |          | 3093  2026_05_PHI_JAX    2026     5  ...       NaN      NaN                                                                                                                                              |           |
| log run             | ok       | run_at  season  week  ... spread_line  total_line       bet                                                                                                                                              |       0   |
|                     |          | 3092  2026-10-06 22:05 UTC    2026     5  ...         8.5        47.5                                                                                                                                    |           |
|                     |          | 3093  2026-10-06 22:05 UTC    2026     5                                                                                                                                                                 |           |
| record picks        | ok       | run_at  season  week  ... spread_edge total_edge  p_cover                                                                                                                                                |       0.7 |
|                     |          | 0  2026-10-04 12:37 UTC    2026     4  ...        5.08       2.49    0.673                                                                                                                               |           |
|                     |          | 1  2026-10-04 16:01 UTC    2026     4  ...       -                                                                                                                                                       |           |
| inputs fingerprint  | ok       | {'season': 2026, 'week': 5, 'starters': {'2026_05_TB_DAL': ['00-0033077', '00-0041251', '2026-10-08 20:15'], '2026_05_PHI_JAX': ['00-0036971', '00-0036389', '2026-10-11 09:30'], '2026_05_CIN_MIA': ['0 |       0.6 |
| grade               | ok       |                                                                                                                                                                                                          |       4.4 |
| closing line value  | ok       | CLV 2026: 10 closed, 5 pending, avg -0.05 pts, 20% beat the close                                                                                                                                        |       0.6 |
| forecast history    | ok       | complete: 2176 games stored                                                                                                                                                                              |       0.1 |
| drift monitor       | ok       | **0 alerts, 0 to watch.** Long run = 2015 to 2024; recent = 2025 and 2026 so far. ALERT at |z| >= 2.5 or a CUSUM trip (h 5); WATCH at |z| >= 2.0.                                                        |       0.5 |
| shadow watch        | ok       | **0 rules ready for a look.** READY = 30+ settled live bets, a win rate past break-even beyond luck (p <= 0.1) and 5+ points more return per unit risked than the rule it would replace over the same se |       1.2 |
| ready checks        | ok       | **0 ready.** Each READY row opens a GitHub issue labelled ready-check (once per title).                                                                                                                  |       0.4 |
| tie check (sources) | ok       | True                                                                                                                                                                                                     |       4.3 |
| export data room    | ok       |                                                                                                                                                                                                          |     137   |
| tie check (page)    | ok       | True                                                                                                                                                                                                     |      10.6 |
| standing checks     | ok       | True                                                                                                                                                                                                     |      49.5 |

## Week 5, 2026: 2 flagged of 15 games

| away_team   | home_team   |   away_exp |   home_exp |   spread_line |   total_line |   spread_edge |   total_edge | bet      |   stake_pct |
|:------------|:------------|-----------:|-----------:|--------------:|-------------:|--------------:|-------------:|:---------|------------:|
| CHI         | GB          |      22.22 |      23.26 |          -3   |         45.5 |          4.04 |        -0.02 | GB +3    |        0.11 |
| BAL         | ATL         |      28.15 |      25.23 |           3.5 |         43.5 |         -6.42 |         9.88 | BAL +3.5 |        2.03 |

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
