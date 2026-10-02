# Weekly run, 2026-10-02 22:28 UTC

## Steps

| step                | status   | detail                                                                                                                                                                                                   |   seconds |
|:--------------------|:---------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------:|
| pull                | ok       | [('2026-10-02T22:28:38', 'schedules', 'all', 'https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv', 'ok', 2182452, '3b506eb7fcc3'), ('2026-10-02T22:28:38', 'players', 'all' |       5   |
| pull player history | ok       | [('2026-10-02T22:28:43', 'pfr_advstats', 2018, 'https://github.com/nflverse/nflverse-data/releases/download/pfr_advstats/advstats_week_def_2018.parquet', 'cached', 149299, ''), ('2026-10-02T22:28:43', |       0   |
| build               | ok       | team_games (8202, 142)                                                                                                                                                                                   |     135.8 |
| features            | ok       | [40 rows x 8 columns]                                                                                                                                                                                    |      12.7 |
| snap exposure       | ok       | snap exposure (329121, 10) seasons 2013 to 2026                                                                                                                                                          |       1.1 |
| verify              | ok       | Result: PASS                                                                                                                                                                                             |       0.4 |
| data checks         | ok       | True                                                                                                                                                                                                     |       0.4 |
| weather             | ok       | game_id           kickoff_et  ... precip        fetched_at                                                                                                                                               |     128.5 |
|                     |          | 0   2026_04_IND_WAS  2026-10-04 09:30:00  ...   0.00  2026-10-02 18:31                                                                                                                                   |           |
|                     |          | 1   2026_04_TEN_BAL  2026-10-04 13:00:00  ...   0.00  2026                                                                                                                                               |           |
| wind forecast       | ok       | 10                                                                                                                                                                                                       |       6.6 |
| lines               | ok       | {'ts': '2026-10-02T22-33-29Z', 'season': 2026, 'week': 4, 'rows': 15, 'errors': ''}                                                                                                                      |      78.5 |
| live results        | ok       | live results: week 4, 1 final of 16, 0 in progress; spread 1-0, total 0-1, winner 0-1; play-by-play for 1 games                                                                                          |       2.9 |
| ratings             | ok       | (7668, 50) QB-out check: ok; swaps: none                                                                                                                                                                 |      22.8 |
| trends              | ok       | head-to-head cover margin      96                 0.355         7.079            2.793                                                                                                                   |      50.7 |
| players             | ok       | max           0.104589         1.360481    14.000000                                                                                                                                                     |     112   |
| positions           | ok       | Skill     541.0  0.007945  0.00250  0.0816                                                                                                                                                               |      23.3 |
| scheme              | ok       | scheme_plays (354592, 83) profiles for 32 teams as of 2026 4                                                                                                                                             |       5.2 |
| player splits       | ok       | player_splits.js 1.61 MB                                                                                                                                                                                 |      67.9 |
| model               | ok       | neutral            0.054       0.133          0.007                                                                                                                                                      |     102.5 |
| qt shadow           | ok       | qt shadow: 3300 games, 16120 Questionable listings priced, 57s                                                                                                                                           |      57.5 |
| opener study        | ok       | opener study written                                                                                                                                                                                     |     102.8 |
| props by season     | ok       | DONE                                                                                                                                                                                                     |      21.4 |
| props               | ok       | props 2869 projections for week 4 graded rows 0 market lines on the cards 314 graded against the market 1833                                                                                             |      22.4 |
| sizing backtest     | ok       | 2025   13-7    0.650        4.82                                                                                                                                                                         |       4.5 |
| threshold sweep     | ok       | DONE                                                                                                                                                                                                     |       1.3 |
| calibration start   | ok       | last 5 seasons     0.5250     0.5309     0.5368              0.69317            0.25001                0.68230              0.5587             0.5978             92              0.69252                |       1.4 |
| season backtest     | ok       | {'shrink0.1_sig1': 'not adopted', 'shrink0.1_sig1.15': 'not adopted', 'shrink0.2_sig1': 'not adopted', 'shrink0.2_sig1.15': 'not adopted', 'shrink0.3_sig1': 'not adopted', 'shrink0.3_sig1.15': 'not ad |      81.3 |
| legitimacy tests    | ok       | Reading: the line beats the model on the miss every season (it should; it is the market). The question the flag rests on is whether the model's disagreements with the line carry information, which the |      13.7 |
| audit reports       | ok       | Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).                                       |       2.2 |
| picks               | ok       | game_id  season  week  ...     bet_p bet_odds stake_pct                                                                                                                                                  |       0.8 |
|                     |          | 3076  2026_04_PIT_CLE    2026     4  ...       NaN      NaN       NaN                                                                                                                                    |           |
|                     |          | 3077  2026_04_IND_WAS    2026     4  ...  0.548913   -115.0                                                                                                                                              |           |
| log run             | ok       | run_at  season  week  ... spread_line  total_line       bet                                                                                                                                              |       0   |
|                     |          | 3076  2026-10-02 22:28 UTC    2026     4  ...        -2.5        38.5                                                                                                                                    |           |
|                     |          | 3077  2026-10-02 22:28 UTC    2026     4                                                                                                                                                                 |           |
| record picks        | ok       | run_at  season  week  ... spread_edge total_edge  p_cover                                                                                                                                                |       0.5 |
|                     |          | 0  2026-10-02 22:28 UTC    2026     4  ...        4.93       2.11    0.670                                                                                                                               |           |
|                     |          | 1  2026-10-02 22:28 UTC    2026     4  ...       -                                                                                                                                                       |           |
| inputs fingerprint  | ok       | {'season': 2026, 'week': 4, 'starters': {'2026_04_PIT_CLE': ['00-0033537', '00-0023459', '2026-10-01 20:15'], '2026_04_IND_WAS': ['00-0032268', '00-0035710', '2026-10-04 09:30'], '2026_04_TEN_BAL': [' |       0.4 |
| grade               | ok       |                                                                                                                                                                                                          |       2.3 |
| closing line value  | ok       | CLV 2026: 4 closed, 7 pending, avg +0.25 pts, 25% beat the close                                                                                                                                         |       0.2 |
| forecast history    | ok       | 43 games fetched in 5s, 2166 stored, 0 left                                                                                                                                                              |       5.5 |
| drift monitor       | ok       | **0 alerts, 0 to watch.** Long run = 2015 to 2024; recent = 2025 and 2026 so far. ALERT at |z| >= 2.5 or a CUSUM trip (h 5); WATCH at |z| >= 2.0.                                                        |       0.4 |
| shadow watch        | ok       | **0 rules ready for a look.** READY = 30+ settled live bets, a win rate past break-even beyond luck (p <= 0.1) and 5+ points more return per unit risked than the rule it would replace over the same se |       0.9 |
| ready checks        | ok       | **0 ready.** Each READY row opens a GitHub issue labelled ready-check (once per title).                                                                                                                  |       0.4 |
| tie check (sources) | error    | RuntimeError: numbers disagree: see reports/tie_check.md                                                                                                                                                 |       3.4 |
| export data room    | ok       |                                                                                                                                                                                                          |      89.4 |
| tie check (page)    | error    | RuntimeError: page files disagree with the sources: see reports/tie_check.md                                                                                                                             |       7.7 |
| standing checks     | error    | RuntimeError: a fixed bug is back: see reports/standing_checks.md                                                                                                                                        |      34.8 |

**Failed steps above were skipped, not filled with stale data.**

## Week 4, 2026: 3 flagged of 16 games

| away_team   | home_team   |   away_exp |   home_exp |   spread_line |   total_line |   spread_edge |   total_edge | bet      |   stake_pct |
|:------------|:------------|-----------:|-----------:|--------------:|-------------:|--------------:|-------------:|:---------|------------:|
| IND         | WAS         |      24.59 |      25.02 |          -4.5 |         47.5 |          4.93 |         2.11 | WAS +4.5 |        0.75 |
| JAX         | CIN         |      26.54 |      24.07 |           2.5 |         51.5 |         -4.98 |        -0.89 | JAX +2.5 |        1.91 |
| ARI         | NYG         |      18.98 |      21.52 |          -2.5 |         44.5 |          5.04 |        -4.01 | NYG +2.5 |        1.61 |

Full table: reports/picks_2026_wk4.md

## Track record

## Rules compared

The flag is bet; the shadows are logged and graded on the same games but never bet, so the rule can be chosen on live results.

Backtest columns: the same rule on the three backtest windows, regular season weeks 1 to 17 (`picks.rule_records`).

| Rule | Bets | Settled | Record | Units | Avg CLV | Backtest 2015-18 | Backtest 2019-22 | Backtest 2023-25 |
|---|---|---|---|---|---|---|---|---|
| 4+ edge (the flag, bet) | 3 | 0 | nothing settled |  | +0.00 | 68-58 | 78-49 | 37-19 |
| shadow: 4.5+ edge | 3 | 0 | nothing settled |  | +0.00 | 42-35 | 53-38 | 24-14 |
| shadow: 4+ edge, model's side the underdog or pick'em | 3 | 0 | nothing settled |  | +0.00 | 51-39 | 71-40 | 29-16 |
| shadow: 4+ edge, weeks 1 to 13 only | 3 | 0 | nothing settled |  | +0.00 | 53-42 | 68-37 | 30-16 |

Full record: reports/track_record.md
