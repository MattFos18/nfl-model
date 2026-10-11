# Weekly run, 2026-10-11 21:32 UTC

## Steps

| step                | status   | detail                                                                                                                                                                                                   |   seconds |
|:--------------------|:---------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------:|
| pull                | ok       | [('2026-10-11T21:32:43', 'schedules', 'all', 'https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv', 'ok', 2183610, '63cd0cd9a743'), ('2026-10-11T21:32:43', 'players', 'all' |       6.4 |
| pull player history | ok       | [('2026-10-11T21:32:50', 'pfr_advstats', 2018, 'https://github.com/nflverse/nflverse-data/releases/download/pfr_advstats/advstats_week_def_2018.parquet', 'cached', 149299, ''), ('2026-10-11T21:32:50', |       0   |
| build               | ok       | team_games (8202, 142)                                                                                                                                                                                   |     129.2 |
| features            | error    | RuntimeError: ^^^^^^^^^^^^                                                                                                                                                                               |      10.7 |
|                     |          |   File "/opt/hostedtoolcache/Python/3.11.17/x64/lib/python3.11/site-packages/pandas/core/frame.py", line 4495, in _get_value                                                                             |           |
|                     |          |     row = self.index.get_loc(index)                                                                                                                                                                      |           |
|                     |          |           ^^^^^^^^^^^^^^^^                                                                                                                                                                               |           |
| snap exposure       | ok       | snap exposure (330605, 10) seasons 2013 to 2026                                                                                                                                                          |       1.1 |
| verify              | ok       | Result: PASS                                                                                                                                                                                             |       0.4 |
| data checks         | ok       | True                                                                                                                                                                                                     |       0.4 |
| weather             | ok       | game_id           kickoff_et  ... precip        fetched_at                                                                                                                                               |       7.3 |
|                     |          | 0   2026_05_NYG_WAS  2026-10-11 13:00:00  ...    0.7  2026-10-11 17:35                                                                                                                                   |           |
|                     |          | 1    2026_05_SF_SEA  2026-10-11 16:25:00  ...    0.0  2026                                                                                                                                               |           |
| wind forecast       | ok       | 0                                                                                                                                                                                                        |       0.1 |
| lines               | ok       | {'ts': '2026-10-11T21-35-20Z', 'season': 2026, 'week': 5, 'rows': 2, 'errors': ''}                                                                                                                       |       9.3 |
| live results        | ok       | live results: week 5, 10 final of 15, 3 in progress; spread 5-4-1, total 3-7, winner 8-1-1; play-by-play for 13 games                                                                                    |       3.8 |
| ratings             | ok       | (7668, 51) QB-out check: ok; swaps: none                                                                                                                                                                 |      20.6 |
| trends              | ok       | head-to-head cover margin      96                 0.355         7.079            2.793                                                                                                                   |      50.3 |
| players             | ok       | max           0.104589         1.360481    14.000000                                                                                                                                                     |     103.8 |
| positions           | ok       | Skill    516.0  0.007898  0.00250  0.0806                                                                                                                                                                |      21.5 |
| scheme              | ok       | scheme_plays (357730, 83) profiles for 32 teams as of 2026 5                                                                                                                                             |       5.1 |
| player splits       | ok       | player_splits.js 1.66 MB                                                                                                                                                                                 |      70.5 |
| model               | ok       | opp_skill_out_value           12.498       0.012          0.156                                                                                                                                          |      53.3 |
| qt shadow           | ok       | qt shadow: 3300 games, 16145 Questionable listings priced, 54s                                                                                                                                           |      54.9 |
| opener study        | ok       | opener study written                                                                                                                                                                                     |      53.5 |
| props by season     | ok       | DONE                                                                                                                                                                                                     |      21.8 |
| props               | ok       | props 2685 projections for week 5 graded rows 0 market lines on the cards 358 graded against the market 3661                                                                                             |      24.4 |
| sizing backtest     | ok       | 2025   14-6    0.700        6.73                                                                                                                                                                         |       4.1 |
| threshold sweep     | ok       | DONE                                                                                                                                                                                                     |       1.3 |
| calibration start   | ok       | last 5 seasons     0.5288     0.5359     0.5429              0.69326            0.25006                0.68250              0.5639             0.5851             94              0.69274                |       1.3 |
| season backtest     | ok       | {'shrink0.1_sig1': 'not adopted', 'shrink0.1_sig1.15': 'not adopted', 'shrink0.2_sig1': 'not adopted', 'shrink0.2_sig1.15': 'not adopted', 'shrink0.3_sig1': 'not adopted', 'shrink0.3_sig1.15': 'not ad |      78.4 |
| legitimacy tests    | ok       | Reading: the line beats the model on the miss every season (it should; it is the market). The question the flag rests on is whether the model's disagreements with the line carry information, which the |      13.3 |
| audit reports       | ok       | Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).                                       |       2.3 |
| picks               | ok       | game_id  season  week  ... bet_p bet_odds stake_pct                                                                                                                                                      |       0.9 |
|                     |          | 3092   2026_05_TB_DAL    2026     5  ...   NaN      NaN       NaN                                                                                                                                        |           |
|                     |          | 3093  2026_05_PHI_JAX    2026     5  ...   NaN      NaN       NaN                                                                                                                                        |           |
|                     |          | 30                                                                                                                                                                                                       |           |
| log run             | ok       | run_at  season  week  ... spread_line  total_line  bet                                                                                                                                                   |       0   |
|                     |          | 3092  2026-10-11 21:32 UTC    2026     5  ...         9.5        49.5                                                                                                                                    |           |
|                     |          | 3093  2026-10-11 21:32 UTC    2026     5  ...                                                                                                                                                            |           |
| record picks        | ok       | run_at season week  ... spread_edge total_edge p_cover                                                                                                                                                   |       0.5 |
|                     |          | 0  2026-10-04 12:37 UTC   2026    4  ...        5.08       2.49   0.673                                                                                                                                  |           |
|                     |          | 1  2026-10-04 16:01 UTC   2026    4  ...       -4.87                                                                                                                                                     |           |
| inputs fingerprint  | ok       | {'season': 2026, 'week': 5, 'starters': {'2026_05_TB_DAL': ['00-0033077', '00-0041251', '2026-10-08 20:15'], '2026_05_PHI_JAX': ['00-0036971', '00-0036389', '2026-10-11 09:30'], '2026_05_CHI_GB': ['00 |       0.6 |
| grade               | ok       |                                                                                                                                                                                                          |       4.4 |
| closing line value  | ok       | CLV 2026: 17 closed, 1 pending, avg -0.15 pts, 24% beat the close                                                                                                                                        |       0.5 |
| forecast history    | ok       | complete: 2183 games stored                                                                                                                                                                              |       0   |
| drift monitor       | ok       | **0 alerts, 0 to watch.** Long run = 2015 to 2024; recent = 2025 and 2026 so far. ALERT at |z| >= 2.5 or a CUSUM trip (h 5); WATCH at |z| >= 2.0.                                                        |       0.4 |
| shadow watch        | ok       | **0 rules ready for a look.** READY = 30+ settled live bets, a win rate past break-even beyond luck (p <= 0.1) and 5+ points more return per unit risked than the rule it would replace over the same se |       1   |
| ready checks        | ok       | **0 ready.** Each READY row opens a GitHub issue labelled ready-check (once per title).                                                                                                                  |       0.4 |
| tie check (sources) | error    | RuntimeError: numbers disagree: see reports/tie_check.md                                                                                                                                                 |       3.5 |
| export data room    | ok       |                                                                                                                                                                                                          |      90.3 |
| tie check (page)    | error    | RuntimeError: page files disagree with the sources: see reports/tie_check.md                                                                                                                             |       8.1 |
| standing checks     | ok       | True                                                                                                                                                                                                     |      35.1 |

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
