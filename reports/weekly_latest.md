# Weekly run, 2026-10-02 16:50 UTC

## Steps

| step                | status   | detail                                                                                                                                                                                                   |   seconds |
|:--------------------|:---------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------:|
| pull                | ok       | [('2026-10-02T16:50:17', 'schedules', 'all', 'https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv', 'ok', 2182452, '4bf8e482d500'), ('2026-10-02T16:50:17', 'players', 'all' |       5   |
| pull player history | ok       | [('2026-10-02T16:50:22', 'pfr_advstats', 2018, 'https://github.com/nflverse/nflverse-data/releases/download/pfr_advstats/advstats_week_def_2018.parquet', 'cached', 149299, ''), ('2026-10-02T16:50:22', |       0   |
| build               | ok       | team_games (8202, 142)                                                                                                                                                                                   |     194.5 |
| features            | ok       | [40 rows x 8 columns]                                                                                                                                                                                    |      19.4 |
| snap exposure       | ok       | snap exposure (329121, 10) seasons 2013 to 2026                                                                                                                                                          |       1.4 |
| verify              | ok       | Result: PASS                                                                                                                                                                                             |       0.5 |
| data checks         | ok       | True                                                                                                                                                                                                     |       0.4 |
| weather             | ok       | game_id           kickoff_et  ... precip        fetched_at                                                                                                                                               |     206.1 |
|                     |          | 0   2026_04_IND_WAS  2026-10-04 09:30:00  ...    0.0  2026-10-02 12:53                                                                                                                                   |           |
|                     |          | 1   2026_04_TEN_BAL  2026-10-04 13:00:00  ...    0.1  2026                                                                                                                                               |           |
| wind forecast       | ok       | 4                                                                                                                                                                                                        |     111.9 |
| lines               | ok       | {'ts': '2026-10-02T16-59-16Z', 'season': 2026, 'week': 4, 'rows': 15, 'errors': ''}                                                                                                                      |     152.4 |
| live results        | ok       | live results: week 4, 1 final of 16, 0 in progress; spread 1-0, total 0-1, winner 0-1; play-by-play for 1 games                                                                                          |       4   |
| ratings             | ok       | (7668, 49)                                                                                                                                                                                               |      32.8 |
| trends              | ok       | head-to-head cover margin      96                 0.355         7.079            2.793                                                                                                                   |      83.7 |
| players             | ok       | max           0.104589         1.360481    14.000000                                                                                                                                                     |     166.5 |
| positions           | ok       | Skill     541.0  0.007945  0.00250  0.0816                                                                                                                                                               |      32.3 |
| scheme              | ok       | scheme_plays (354592, 83) profiles for 32 teams as of 2026 4                                                                                                                                             |       7.9 |
| player splits       | ok       | player_splits.js 1.61 MB                                                                                                                                                                                 |     125.3 |
| model               | ok       | neutral            0.054       0.133          0.007                                                                                                                                                      |      74   |
| opener study        | ok       | opener study written                                                                                                                                                                                     |      75.1 |
| props by season     | ok       | DONE                                                                                                                                                                                                     |      32.8 |
| props               | ok       | props 2879 projections for week 4 graded rows 0 market lines on the cards 300 graded against the market 1833                                                                                             |      34.8 |
| sizing backtest     | ok       | 2025   13-7    0.650        4.82                                                                                                                                                                         |       6.9 |
| threshold sweep     | ok       | DONE                                                                                                                                                                                                     |       1.8 |
| calibration start   | ok       | last 5 seasons     0.5254     0.5311     0.5368              0.69384            0.25034                0.68419              0.5610             0.5895             95              0.69219                |       1.8 |
| season backtest     | ok       | {'shrink0.1_sig1': 'not adopted', 'shrink0.1_sig1.15': 'not adopted', 'shrink0.2_sig1': 'not adopted', 'shrink0.2_sig1.15': 'not adopted', 'shrink0.3_sig1': 'not adopted', 'shrink0.3_sig1.15': 'not ad |     108.5 |
| legitimacy tests    | ok       | Reading: the line beats the model on the miss every season (it should; it is the market). The question the flag rests on is whether the model's disagreements with the line carry information, which the |      21   |
| audit reports       | ok       | Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).                                       |       2.9 |
| picks               | ok       | game_id  season  week  ...     bet_p bet_odds stake_pct                                                                                                                                                  |       1.1 |
|                     |          | 3076  2026_04_PIT_CLE    2026     4  ...       NaN      NaN       NaN                                                                                                                                    |           |
|                     |          | 3077  2026_04_IND_WAS    2026     4  ...  0.541380   -105.0                                                                                                                                              |           |
| log run             | ok       | run_at  season  week  ... spread_line  total_line       bet                                                                                                                                              |       0   |
|                     |          | 3076  2026-10-02 16:50 UTC    2026     4  ...        -2.5        38.5                                                                                                                                    |           |
|                     |          | 3077  2026-10-02 16:50 UTC    2026     4                                                                                                                                                                 |           |
| record picks        | ok       | run_at  season  week  ... spread_edge total_edge  p_cover                                                                                                                                                |       0.6 |
|                     |          | 0  2026-10-02 16:50 UTC    2026     4  ...        4.24       1.22    0.650                                                                                                                               |           |
|                     |          | 1  2026-10-02 16:50 UTC    2026     4  ...       -                                                                                                                                                       |           |
| inputs fingerprint  | ok       | {'season': 2026, 'week': 4, 'starters': {'2026_04_PIT_CLE': ['00-0033537', '00-0023459', '2026-10-01 20:15'], '2026_04_IND_WAS': ['00-0032268', '00-0035710', '2026-10-04 09:30'], '2026_04_TEN_BAL': [' |       0.3 |
| grade               | ok       |                                                                                                                                                                                                          |       3   |
| closing line value  | ok       | CLV 2026: 4 closed, 9 pending, avg +0.25 pts, 25% beat the close                                                                                                                                         |       0.3 |
| forecast history    | ok       | complete: 1568 games stored                                                                                                                                                                              |       0   |
| drift monitor       | ok       | **0 alerts, 0 to watch.** Long run = 2015 to 2024; recent = 2025 and 2026 so far. ALERT at |z| >= 2.5 or a CUSUM trip (h 5); WATCH at |z| >= 2.0.                                                        |       0.5 |
| shadow watch        | ok       | **0 rules ready for a look.** READY = 30+ settled live bets, a win rate past break-even beyond luck (p <= 0.1) and 5+ points more return per unit risked than the rule it would replace over the same se |       1.2 |
| ready checks        | ok       | **0 ready.** Each READY row opens a GitHub issue labelled ready-check (once per title).                                                                                                                  |       0.5 |
| tie check (sources) | error    | RuntimeError: numbers disagree: see reports/tie_check.md                                                                                                                                                 |       4.5 |
| export data room    | ok       |                                                                                                                                                                                                          |     136.1 |
| tie check (page)    | error    | RuntimeError: page files disagree with the sources: see reports/tie_check.md                                                                                                                             |       9.4 |

**Failed steps above were skipped, not filled with stale data.**

## Week 4, 2026: 3 flagged of 16 games

| away_team   | home_team   |   away_exp |   home_exp |   spread_line |   total_line |   spread_edge |   total_edge | bet      |   stake_pct |
|:------------|:------------|-----------:|-----------:|--------------:|-------------:|--------------:|-------------:|:---------|------------:|
| IND         | WAS         |      24.49 |      25.23 |          -3.5 |         48.5 |          4.24 |         1.22 | WAS +3.5 |        1.5  |
| JAX         | CIN         |      26.41 |      24.45 |           2.5 |         51.5 |         -4.46 |        -0.64 | JAX +2.5 |        1.62 |
| ARI         | NYG         |      17.83 |      20.22 |          -2.5 |         44.5 |          4.88 |        -6.45 | NYG +2.5 |        1.53 |

Full table: reports/picks_2026_wk4.md

## Track record

## Rules compared

The flag is bet; the shadows are logged and graded on the same games but never bet, so the rule can be chosen on live results.

Backtest columns: the same rule on the three backtest windows, regular season weeks 1 to 17 (`picks.rule_records`).

| Rule | Bets | Settled | Record | Units | Avg CLV | Backtest 2015-18 | Backtest 2019-22 | Backtest 2023-25 |
|---|---|---|---|---|---|---|---|---|
| 4+ edge (the flag, bet) | 3 | 0 | nothing settled |  | +0.00 | 69-56 | 79-51 | 37-18 |
| shadow: 4.5+ edge | 1 | 0 | nothing settled |  | +0.00 | 42-37 | 53-38 | 24-15 |
| shadow: 4+ edge, model's side the underdog or pick'em | 3 | 0 | nothing settled |  | +0.00 | 51-37 | 72-42 | 29-15 |
| shadow: 4+ edge, weeks 1 to 13 only | 3 | 0 | nothing settled |  | +0.00 | 55-42 | 68-37 | 31-15 |

Full record: reports/track_record.md
