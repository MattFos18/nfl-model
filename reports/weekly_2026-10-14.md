# Weekly run, 2026-10-14 22:18 UTC

## Steps

| step                | status   | detail                                                                                                                                                                                                   |   seconds |
|:--------------------|:---------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------:|
| pull                | ok       | [('2026-10-14T22:18:54', 'schedules', 'all', 'https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv', 'ok', 2184481, '81494edec340'), ('2026-10-14T22:18:54', 'players', 'all' |       5.5 |
| pull player history | ok       | [('2026-10-14T22:18:59', 'pfr_advstats', 2018, 'https://github.com/nflverse/nflverse-data/releases/download/pfr_advstats/advstats_week_def_2018.parquet', 'cached', 149299, ''), ('2026-10-14T22:18:59', |       0   |
| build               | ok       | team_games (8202, 142)                                                                                                                                                                                   |     176.9 |
| features            | ok       | [40 rows x 8 columns]                                                                                                                                                                                    |      15   |
| snap exposure       | ok       | snap exposure (331910, 10) seasons 2013 to 2026                                                                                                                                                          |       1.5 |
| verify              | ok       | Result: PASS                                                                                                                                                                                             |       0.5 |
| data checks         | ok       | True                                                                                                                                                                                                     |       0.5 |
| weather             | ok       | game_id          kickoff_et  ... precip        fetched_at                                                                                                                                                |       5.7 |
|                     |          | 0   2026_06_SEA_DEN 2026-10-15 20:15:00  ...    0.0  2026-10-14 18:22                                                                                                                                    |           |
|                     |          | 1   2026_06_HOU_JAX 2026-10-18 09:30:00  ...    0.0  2026-10                                                                                                                                             |           |
| wind forecast       | ok       | 0                                                                                                                                                                                                        |       0.9 |
| lines               | ok       | {'ts': '2026-10-14T22-22-21Z', 'season': 2026, 'week': 6, 'rows': 14, 'errors': ''}                                                                                                                      |       6   |
| live results        | ok       | live results: week 6, 0 final of 14, 0 in progress; spread 0-0, total 0-0, winner 0-0; play-by-play for 0 games                                                                                          |       5.8 |
| ratings             | ok       | (7668, 51) QB-out check: ok; swaps: none                                                                                                                                                                 |      29   |
| trends              | ok       | head-to-head cover margin      96                 0.355         7.079            2.793                                                                                                                   |      71.2 |
| players             | ok       | max           0.104589         1.360481    14.000000                                                                                                                                                     |     147.2 |
| positions           | ok       | Skill    492.0  0.007613  0.00250  0.0869                                                                                                                                                                |      28.1 |
| scheme              | ok       | scheme_plays (358372, 83) profiles for 32 teams as of 2026 6                                                                                                                                             |       7   |
| player splits       | ok       | player_splits.js 1.69 MB                                                                                                                                                                                 |      97.7 |
| model               | ok       | opp_skill_out_value           12.498       0.012          0.156                                                                                                                                          |      69.1 |
| qt shadow           | ok       | qt shadow: 3300 games, 16322 Questionable listings priced, 74s                                                                                                                                           |      75.8 |
| opener study        | ok       | opener study written                                                                                                                                                                                     |      68.2 |
| props by season     | ok       | DONE                                                                                                                                                                                                     |      29.3 |
| props               | ok       | props 2559 projections for week 6 graded rows 0 market lines on the cards 210 graded against the market 5418                                                                                             |      35.7 |
| sizing backtest     | ok       | 2025   14-6    0.700        6.73                                                                                                                                                                         |       5.5 |
| threshold sweep     | ok       | DONE                                                                                                                                                                                                     |       1.7 |
| calibration start   | ok       | last 5 seasons     0.5288     0.5359     0.5429              0.69326            0.25006                0.68250              0.5639             0.5851             94              0.69274                |       1.8 |
| season backtest     | ok       | {'shrink0.1_sig1': 'not adopted', 'shrink0.1_sig1.15': 'not adopted', 'shrink0.2_sig1': 'not adopted', 'shrink0.2_sig1.15': 'not adopted', 'shrink0.3_sig1': 'not adopted', 'shrink0.3_sig1.15': 'not ad |     106.1 |
| legitimacy tests    | ok       | Reading: the line beats the model on the miss every season (it should; it is the market). The question the flag rests on is whether the model's disagreements with the line carry information, which the |      17.8 |
| audit reports       | ok       | Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).                                       |       2.9 |
| picks               | ok       | game_id  season  week  ...     bet_p bet_odds stake_pct                                                                                                                                                  |       1.2 |
|                     |          | 3107  2026_06_SEA_DEN    2026     6  ...       NaN      NaN       NaN                                                                                                                                    |           |
|                     |          | 3108  2026_06_HOU_JAX    2026     6  ...       NaN      NaN                                                                                                                                              |           |
| log run             | ok       | run_at  season  week  ... spread_line  total_line       bet                                                                                                                                              |       0   |
|                     |          | 3107  2026-10-14 22:18 UTC    2026     6  ...        -2.5        40.5                                                                                                                                    |           |
|                     |          | 3108  2026-10-14 22:18 UTC    2026     6                                                                                                                                                                 |           |
| record picks        | ok       | run_at  season  week  ... spread_edge total_edge  p_cover                                                                                                                                                |       0.6 |
|                     |          | 0  2026-10-04 12:37 UTC    2026     4  ...        5.08       2.49    0.673                                                                                                                               |           |
|                     |          | 1  2026-10-04 16:01 UTC    2026     4  ...       -                                                                                                                                                       |           |
| inputs fingerprint  | ok       | {'season': 2026, 'week': 6, 'starters': {'2026_06_SEA_DEN': ['00-0039732', '00-0035704', '2026-10-15 20:15'], '2026_06_HOU_JAX': ['00-0036971', '00-0039163', '2026-10-18 09:30'], '2026_06_CHI_ATL': [' |       0.8 |
| grade               | ok       |                                                                                                                                                                                                          |       7   |
| closing line value  | ok       | CLV 2026: 18 closed, 7 pending, avg -0.19 pts, 22% beat the close                                                                                                                                        |       0.9 |
| forecast history    | ok       | complete: 2186 games stored                                                                                                                                                                              |       0.1 |
| drift monitor       | ok       | **0 alerts, 0 to watch.** Long run = 2015 to 2024; recent = 2025 and 2026 so far. ALERT at |z| >= 2.5 or a CUSUM trip (h 5); WATCH at |z| >= 2.0.                                                        |       0.5 |
| shadow watch        | ok       | **0 rules ready for a look.** READY = 30+ settled live bets, a win rate past break-even beyond luck (p <= 0.1) and 5+ points more return per unit risked than the rule it would replace over the same se |       1.3 |
| ready checks        | ok       | **0 ready.** Each READY row opens a GitHub issue labelled ready-check (once per title).                                                                                                                  |       0.5 |
| tie check (sources) | error    | RuntimeError: numbers disagree: see reports/tie_check.md                                                                                                                                                 |       4.4 |
| export data room    | ok       |                                                                                                                                                                                                          |     124   |
| tie check (page)    | error    | RuntimeError: page files disagree with the sources: see reports/tie_check.md                                                                                                                             |      11   |
| standing checks     | ok       | True                                                                                                                                                                                                     |      49.3 |

**Failed steps above were skipped, not filled with stale data.**

## Week 6, 2026: 2 flagged of 14 games

| away_team   | home_team   |   away_exp |   home_exp |   spread_line |   total_line |   spread_edge |   total_edge | bet      |   stake_pct |
|:------------|:------------|-----------:|-----------:|--------------:|-------------:|--------------:|-------------:|:---------|------------:|
| CHI         | ATL         |      21.76 |      25.51 |          -1.5 |         51.5 |          5.25 |        -4.23 | ATL +1.5 |        1.59 |
| CAR         | PHI         |      20.24 |      25.76 |          -1.5 |         39.5 |          7.02 |         6.5  | PHI +1.5 |        2.1  |

Full table: reports/picks_2026_wk6.md

## Track record

## Rules compared

The flag is bet; the shadows are logged and graded on the same games but never bet, so the rule can be chosen on live results.

Backtest columns: the same rule on the three backtest windows, regular season weeks 1 to 17 (`picks.rule_records`).

| Rule | Bets | Settled | Record | Units | Avg CLV | Backtest 2015-18 | Backtest 2019-22 | Backtest 2023-25 |
|---|---|---|---|---|---|---|---|---|
| 4+ edge (the flag, bet) | 5 | 3 | 2-1 (67%) | +0.88 | +0.00 | 67-54 | 80-52 | 38-17 |
| shadow: 4.5+ edge | 4 | 2 | 1-1 (50%) | -0.05 | +0.00 | 46-36 | 55-39 | 23-15 |
| shadow: 4+ edge, model's side the underdog or pick'em | 5 | 3 | 2-1 (67%) | +0.88 | +0.00 | 52-37 | 72-43 | 30-14 |
| shadow: 4+ edge, weeks 1 to 13 only | 5 | 3 | 2-1 (67%) | +0.88 | +0.00 | 50-41 | 69-38 | 30-14 |

Full record: reports/track_record.md
