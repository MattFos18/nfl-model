# Weekly run, 2026-10-21 21:47 UTC

## Steps

| step                | status   | detail                                                                                                                                                                                                   |   seconds |
|:--------------------|:---------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------:|
| pull                | ok       | [('2026-10-21T21:47:57', 'schedules', 'all', 'https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv', 'ok', 2186336, '67712694c87e'), ('2026-10-21T21:47:57', 'players', 'all' |       5   |
| pull player history | ok       | [('2026-10-21T21:48:02', 'pfr_advstats', 2018, 'https://github.com/nflverse/nflverse-data/releases/download/pfr_advstats/advstats_week_def_2018.parquet', 'cached', 149299, ''), ('2026-10-21T21:48:02', |       0   |
| build               | ok       | team_games (8202, 142)                                                                                                                                                                                   |     203   |
| features            | ok       | [40 rows x 8 columns]                                                                                                                                                                                    |      19.8 |
| snap exposure       | ok       | snap exposure (333227, 10) seasons 2013 to 2026                                                                                                                                                          |       1.7 |
| verify              | ok       | Result: PASS                                                                                                                                                                                             |       0.5 |
| data checks         | ok       | True                                                                                                                                                                                                     |       0.6 |
| weather             | ok       | game_id          kickoff_et  ... precip        fetched_at                                                                                                                                                |       5.7 |
|                     |          | 0   2026_07_NE_CHI 2026-10-22 20:15:00  ...    0.0  2026-10-21 17:51                                                                                                                                     |           |
|                     |          | 1   2026_07_PIT_NO 2026-10-25 09:30:00  ...    0.0  2026-10-21                                                                                                                                           |           |
| wind forecast       | ok       | 0                                                                                                                                                                                                        |       1.2 |
| lines               | ok       | {'ts': '2026-10-21T21-51-56Z', 'season': 2026, 'week': 7, 'rows': 14, 'errors': ''}                                                                                                                      |       6.9 |
| live results        | ok       | live results: week 7, 0 final of 14, 0 in progress; spread 0-0, total 0-0, winner 0-0; play-by-play for 0 games                                                                                          |       7.2 |
| ratings             | ok       | (7668, 51) QB-out check: ok; swaps: PHI Jalen Hurts -> Tanner McKee (depth chart)                                                                                                                        |      35.5 |
| trends              | ok       | head-to-head cover margin      96                 0.355         7.079            2.793                                                                                                                   |      88.2 |
| players             | ok       | max           0.104589         1.360481    14.000000                                                                                                                                                     |     165.2 |
| positions           | ok       | Skill    489.0  0.007831  0.0023  0.0844                                                                                                                                                                 |      30.2 |
| scheme              | ok       | scheme_plays (360185, 83) profiles for 32 teams as of 2026 7                                                                                                                                             |       8   |
| player splits       | ok       | player_splits.js 1.72 MB                                                                                                                                                                                 |     129.7 |
| model               | ok       | opp_skill_out_value           12.498       0.012          0.156                                                                                                                                          |      73.4 |
| qt shadow           | ok       | qt shadow: 3300 games, 16416 Questionable listings priced, 85s                                                                                                                                           |      86.7 |
| opener study        | ok       | opener study written                                                                                                                                                                                     |      71.7 |
| props by season     | ok       | DONE                                                                                                                                                                                                     |      32.5 |
| props               | ok       | props 2547 projections for week 7 graded rows 0 market lines on the cards 205 graded against the market 7089                                                                                             |      43   |
| sizing backtest     | ok       | 2025   14-6    0.700        6.73                                                                                                                                                                         |       6.4 |
| threshold sweep     | ok       | DONE                                                                                                                                                                                                     |       1.8 |
| calibration start   | ok       | last 5 seasons     0.5288     0.5359     0.5429              0.69326            0.25006                0.68250              0.5639             0.5851             94              0.69274                |       1.8 |
| season backtest     | ok       | {'shrink0.1_sig1': 'not adopted', 'shrink0.1_sig1.15': 'not adopted', 'shrink0.2_sig1': 'not adopted', 'shrink0.2_sig1.15': 'not adopted', 'shrink0.3_sig1': 'not adopted', 'shrink0.3_sig1.15': 'not ad |     104.9 |
| legitimacy tests    | ok       | Reading: the line beats the model on the miss every season (it should; it is the market). The question the flag rests on is whether the model's disagreements with the line carry information, which the |      21.7 |
| audit reports       | ok       | Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).                                       |       3.2 |
| picks               | ok       | game_id  season  week  ...     bet_p bet_odds stake_pct                                                                                                                                                  |       1.4 |
|                     |          | 3121   2026_07_NE_CHI    2026     7  ...       NaN      NaN       NaN                                                                                                                                    |           |
|                     |          | 3122   2026_07_PIT_NO    2026     7  ...       NaN      NaN                                                                                                                                              |           |
| log run             | ok       | run_at  season  week  ... spread_line  total_line       bet                                                                                                                                              |       0   |
|                     |          | 3121  2026-10-21 21:47 UTC    2026     7  ...         3.0        50.5                                                                                                                                    |           |
|                     |          | 3122  2026-10-21 21:47 UTC    2026     7                                                                                                                                                                 |           |
| record picks        | ok       | run_at  season  week  ... spread_edge total_edge  p_cover                                                                                                                                                |       0.7 |
|                     |          | 0  2026-10-04 12:37 UTC    2026     4  ...        5.08       2.49    0.673                                                                                                                               |           |
|                     |          | 1  2026-10-04 16:01 UTC    2026     4  ...       -                                                                                                                                                       |           |
| inputs fingerprint  | ok       | {'season': 2026, 'week': 7, 'starters': {'2026_07_NE_CHI': ['00-0039918', '00-0039851', '2026-10-22 20:15'], '2026_07_PIT_NO': ['00-0040743', '00-0023459', '2026-10-25 09:30'], '2026_07_SF_ATL': ['00- |       1   |
| grade               | ok       |                                                                                                                                                                                                          |       8.8 |
| closing line value  | ok       | CLV 2026: 26 closed, 3 pending, avg -0.15 pts, 23% beat the close                                                                                                                                        |       1.3 |
| forecast history    | ok       | complete: 2196 games stored                                                                                                                                                                              |       0.1 |
| drift monitor       | ok       | **0 alerts, 0 to watch.** Long run = 2015 to 2024; recent = 2025 and 2026 so far. ALERT at |z| >= 2.5 or a CUSUM trip (h 5); WATCH at |z| >= 2.0.                                                        |       0.5 |
| shadow watch        | ok       | **0 rules ready for a look.** READY = 30+ settled live bets, a win rate past break-even beyond luck (p <= 0.1) and 5+ points more return per unit risked than the rule it would replace over the same se |       1.3 |
| ready checks        | ok       | **0 ready.** Each READY row opens a GitHub issue labelled ready-check (once per title).                                                                                                                  |       0.5 |
| tie check (sources) | ok       | True                                                                                                                                                                                                     |       5.2 |
| export data room    | ok       |                                                                                                                                                                                                          |     144.8 |
| tie check (page)    | error    | RuntimeError: page files disagree with the sources: see reports/tie_check.md                                                                                                                             |      12.6 |
| standing checks     | ok       | True                                                                                                                                                                                                     |      52.2 |

**Failed steps above were skipped, not filled with stale data.**

## Week 7, 2026: 1 flagged of 14 games

| away_team   | home_team   |   away_exp |   home_exp |   spread_line |   total_line |   spread_edge |   total_edge | bet      |   stake_pct |
|:------------|:------------|-----------:|-----------:|--------------:|-------------:|--------------:|-------------:|:---------|------------:|
| CIN         | BAL         |      24.39 |      28.66 |          -1.5 |         48.5 |          5.77 |         4.54 | BAL +1.5 |        1.05 |

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
