# Weekly run, 2026-10-12 22:14 UTC

## Steps

| step                | status   | detail                                                                                                                                                                                                   |   seconds |
|:--------------------|:---------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------:|
| pull                | ok       | [('2026-10-12T22:14:56', 'schedules', 'all', 'https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv', 'ok', 2184049, '4a41508a648e'), ('2026-10-12T22:14:56', 'players', 'all' |       4.9 |
| pull player history | ok       | [('2026-10-12T22:15:01', 'pfr_advstats', 2018, 'https://github.com/nflverse/nflverse-data/releases/download/pfr_advstats/advstats_week_def_2018.parquet', 'cached', 149299, ''), ('2026-10-12T22:15:01', |       0   |
| build               | ok       | team_games (8202, 142)                                                                                                                                                                                   |     125.4 |
| features            | ok       | [40 rows x 8 columns]                                                                                                                                                                                    |      11   |
| snap exposure       | ok       | snap exposure (331817, 10) seasons 2013 to 2026                                                                                                                                                          |       1   |
| verify              | ok       | Result: PASS                                                                                                                                                                                             |       0.4 |
| data checks         | ok       | True                                                                                                                                                                                                     |       0.4 |
| weather             | ok       | game_id          kickoff_et  ... precip        fetched_at                                                                                                                                                |       1.8 |
|                     |          | 0  2026_06_SEA_DEN 2026-10-15 20:15:00  ...    0.0  2026-10-12 18:17                                                                                                                                     |           |
|                     |          | 1  2026_06_HOU_JAX 2026-10-18 09:30:00  ...    0.2  2026-10-12                                                                                                                                           |           |
| wind forecast       | ok       | 0                                                                                                                                                                                                        |       0.1 |
| lines               | ok       | {'ts': '2026-10-12T22-17-22Z', 'season': 2026, 'week': 5, 'rows': 15, 'errors': ''}                                                                                                                      |       6.1 |
| live results        | ok       | live results: week 5, 14 final of 15, 0 in progress; spread 6-7-1, total 5-9, winner 10-3-1; play-by-play for 14 games                                                                                   |       2.9 |
| ratings             | ok       | (7668, 51) QB-out check: ok; swaps: none                                                                                                                                                                 |      19.1 |
| trends              | ok       | head-to-head cover margin      96                 0.355         7.079            2.793                                                                                                                   |      43.1 |
| players             | ok       | max           0.104589         1.360481    14.000000                                                                                                                                                     |      94.4 |
| positions           | ok       | Skill    516.0  0.007898  0.00250  0.0806                                                                                                                                                                |      20.1 |
| scheme              | ok       | scheme_plays (358237, 83) profiles for 32 teams as of 2026 5                                                                                                                                             |       4.7 |
| player splits       | ok       | player_splits.js 1.67 MB                                                                                                                                                                                 |      60   |
| model               | ok       | opp_skill_out_value           12.498       0.012          0.156                                                                                                                                          |      39.9 |
| qt shadow           | ok       | qt shadow: 3300 games, 16221 Questionable listings priced, 49s                                                                                                                                           |      49.7 |
| opener study        | ok       | opener study written                                                                                                                                                                                     |      40.4 |
| props by season     | ok       | DONE                                                                                                                                                                                                     |      19.6 |
| props               | ok       | props 2710 projections for week 5 graded rows 0 market lines on the cards 353 graded against the market 3661                                                                                             |      21.7 |
| sizing backtest     | ok       | 2025   14-6    0.700        6.73                                                                                                                                                                         |       3.8 |
| threshold sweep     | ok       | DONE                                                                                                                                                                                                     |       1.2 |
| calibration start   | ok       | last 5 seasons     0.5288     0.5359     0.5429              0.69326            0.25006                0.68250              0.5639             0.5851             94              0.69274                |       1.2 |
| season backtest     | ok       | {'shrink0.1_sig1': 'not adopted', 'shrink0.1_sig1.15': 'not adopted', 'shrink0.2_sig1': 'not adopted', 'shrink0.2_sig1.15': 'not adopted', 'shrink0.3_sig1': 'not adopted', 'shrink0.3_sig1.15': 'not ad |      67   |
| legitimacy tests    | ok       | Reading: the line beats the model on the miss every season (it should; it is the market). The question the flag rests on is whether the model's disagreements with the line carry information, which the |      11.9 |
| audit reports       | ok       | Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).                                       |       2   |
| picks               | ok       | game_id  season  week  ... bet_p bet_odds stake_pct                                                                                                                                                      |       0.7 |
|                     |          | 3092   2026_05_TB_DAL    2026     5  ...   NaN      NaN       NaN                                                                                                                                        |           |
|                     |          | 3093  2026_05_PHI_JAX    2026     5  ...   NaN      NaN       NaN                                                                                                                                        |           |
|                     |          | 30                                                                                                                                                                                                       |           |
| log run             | ok       | run_at  season  week  ... spread_line  total_line  bet                                                                                                                                                   |       0   |
|                     |          | 3092  2026-10-12 22:14 UTC    2026     5  ...         9.5        49.5                                                                                                                                    |           |
|                     |          | 3093  2026-10-12 22:14 UTC    2026     5  ...                                                                                                                                                            |           |
| record picks        | ok       | run_at season week  ... spread_edge total_edge p_cover                                                                                                                                                   |       0.4 |
|                     |          | 0  2026-10-04 12:37 UTC   2026    4  ...        5.08       2.49   0.673                                                                                                                                  |           |
|                     |          | 1  2026-10-04 16:01 UTC   2026    4  ...       -4.87                                                                                                                                                     |           |
| inputs fingerprint  | ok       | {'season': 2026, 'week': 5, 'starters': {'2026_05_TB_DAL': ['00-0033077', '00-0041251', '2026-10-08 20:15'], '2026_05_PHI_JAX': ['00-0036971', '00-0036389', '2026-10-11 09:30'], '2026_05_CHI_GB': ['00 |       0.5 |
| grade               | ok       |                                                                                                                                                                                                          |       3.8 |
| closing line value  | ok       | CLV 2026: 17 closed, 1 pending, avg -0.15 pts, 24% beat the close                                                                                                                                        |       0.5 |
| forecast history    | ok       | complete: 2186 games stored                                                                                                                                                                              |       0   |
| drift monitor       | ok       | **0 alerts, 0 to watch.** Long run = 2015 to 2024; recent = 2025 and 2026 so far. ALERT at |z| >= 2.5 or a CUSUM trip (h 5); WATCH at |z| >= 2.0.                                                        |       0.4 |
| shadow watch        | ok       | **0 rules ready for a look.** READY = 30+ settled live bets, a win rate past break-even beyond luck (p <= 0.1) and 5+ points more return per unit risked than the rule it would replace over the same se |       0.8 |
| ready checks        | ok       | **0 ready.** Each READY row opens a GitHub issue labelled ready-check (once per title).                                                                                                                  |       0.3 |
| tie check (sources) | error    | RuntimeError: numbers disagree: see reports/tie_check.md                                                                                                                                                 |       3.2 |
| export data room    | ok       |                                                                                                                                                                                                          |      78.4 |
| tie check (page)    | error    | RuntimeError: page files disagree with the sources: see reports/tie_check.md                                                                                                                             |       7.4 |
| standing checks     | ok       | True                                                                                                                                                                                                     |      28.7 |

**Failed steps above were skipped, not filled with stale data.**

## Week 5, 2026: 0 flagged of 15 games

No game clears the flag thresholds.

Full table: reports/picks_2026_wk5.md

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
