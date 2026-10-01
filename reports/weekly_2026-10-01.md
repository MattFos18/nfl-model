# Weekly run, 2026-10-01 23:22 UTC

## Steps

| step                | status   | detail                                                                                                                                                                                                   |   seconds |
|:--------------------|:---------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------:|
| pull                | ok       | [('2026-10-01T23:22:05', 'schedules', 'all', 'https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv', 'ok', 2182350, '024f2f7ad626'), ('2026-10-01T23:22:05', 'players', 'all' |       2.9 |
| pull player history | ok       | [('2026-10-01T23:22:08', 'pfr_advstats', 2018, 'https://github.com/nflverse/nflverse-data/releases/download/pfr_advstats/advstats_week_def_2018.parquet', 'cached', 149299, ''), ('2026-10-01T23:22:08', |       0   |
| build               | ok       | team_games (8202, 142)                                                                                                                                                                                   |     180.8 |
| features            | ok       | [40 rows x 8 columns]                                                                                                                                                                                    |      18.4 |
| snap exposure       | ok       | snap exposure (329030, 10) seasons 2013 to 2026                                                                                                                                                          |       1.3 |
| verify              | ok       | Result: PASS                                                                                                                                                                                             |       0.5 |
| data checks         | ok       | True                                                                                                                                                                                                     |       0.1 |
| weather             | ok       | game_id          kickoff_et  ... precip        fetched_at                                                                                                                                                |       2   |
|                     |          | 0   2026_04_PIT_CLE 2026-10-01 20:15:00  ...    0.0  2026-10-01 19:25                                                                                                                                    |           |
|                     |          | 1   2026_04_IND_WAS 2026-10-04 09:30:00  ...    0.1  2026-10                                                                                                                                             |           |
| wind forecast       | ok       | 0                                                                                                                                                                                                        |       5.6 |
| lines               | ok       | {'ts': '2026-10-01T23-25-37Z', 'season': 2026, 'week': 4, 'rows': 16, 'errors': ''}                                                                                                                      |     128.9 |
| live results        | ok       | live results: week 4, 0 final of 16, 0 in progress; spread 0-0, total 0-0, winner 0-0; play-by-play for 0 games                                                                                          |       2.2 |
| ratings             | ok       | (7668, 49)                                                                                                                                                                                               |      31.6 |
| trends              | ok       | head-to-head cover margin      96                 0.355         7.079            2.793                                                                                                                   |      80   |
| players             | ok       | max           0.104589         1.360481    14.000000                                                                                                                                                     |     159.8 |
| positions           | ok       | Skill     539.0  0.007972  0.00260  0.0816                                                                                                                                                               |      30.5 |
| scheme              | ok       | scheme_plays (354466, 83) profiles for 32 teams as of 2026 4                                                                                                                                             |       7.6 |
| player splits       | ok       | player_splits.js 1.61 MB                                                                                                                                                                                 |     118.1 |
| model               | ok       | neutral            0.082       0.133          0.011                                                                                                                                                      |      70.2 |
| opener study        | ok       | opener study written                                                                                                                                                                                     |      70.9 |
| props by season     | ok       | DONE                                                                                                                                                                                                     |      31   |
| props               | ok       | props 2879 projections for week 4 graded rows 0 market lines on the cards 286 graded against the market 1833                                                                                             |      33.4 |
| sizing backtest     | ok       | 2025   13-9    0.591        2.82                                                                                                                                                                         |       6.8 |
| threshold sweep     | ok       | DONE                                                                                                                                                                                                     |       1.7 |
| calibration start   | ok       | last 5 seasons     0.5205     0.5225     0.5244              0.69458            0.25071                0.68567              0.5600             0.5895             95              0.69273                |       1.7 |
| season backtest     | ok       | {'shrink0.1_sig1': 'not adopted', 'shrink0.1_sig1.15': 'not adopted', 'shrink0.2_sig1': 'not adopted', 'shrink0.2_sig1.15': 'not adopted', 'shrink0.3_sig1': 'not adopted', 'shrink0.3_sig1.15': 'not ad |     106.3 |
| legitimacy tests    | ok       | Reading: the line beats the model on the miss every season (it should; it is the market). The question the flag rests on is whether the model's disagreements with the line carry information, which the |      21.2 |
| audit reports       | ok       | Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).                                       |       2.6 |
| picks               | ok       | game_id  season  week  ...     bet_p bet_odds stake_pct                                                                                                                                                  |       0.8 |
|                     |          | 3076  2026_04_PIT_CLE    2026     4  ...       NaN      NaN       NaN                                                                                                                                    |           |
|                     |          | 3077  2026_04_IND_WAS    2026     4  ...  0.543410   -110.0                                                                                                                                              |           |
| log run             | ok       | run_at  season  week  ... spread_line  total_line       bet                                                                                                                                              |       0   |
|                     |          | 3076  2026-10-01 23:22 UTC    2026     4  ...        -2.5        38.5                                                                                                                                    |           |
|                     |          | 3077  2026-10-01 23:22 UTC    2026     4                                                                                                                                                                 |           |
| record picks        | ok       | run_at  season  week  ... spread_edge total_edge  p_cover                                                                                                                                                |       0.3 |
|                     |          | 0  2026-10-01 23:22 UTC    2026     4  ...        4.83       1.41    0.666                                                                                                                               |           |
|                     |          | 1  2026-10-01 23:22 UTC    2026     4  ...       -                                                                                                                                                       |           |
| inputs fingerprint  | ok       | {'season': 2026, 'week': 4, 'starters': {'2026_04_PIT_CLE': ['00-0033537', '00-0023459', '2026-10-01 20:15'], '2026_04_IND_WAS': ['00-0039910', '00-0035710', '2026-10-04 09:30'], '2026_04_TEN_BAL': [' |       0.3 |
| grade               | ok       |                                                                                                                                                                                                          |       1.5 |
| forecast history    | ok       | complete: 1558 games stored                                                                                                                                                                              |       0   |
| drift monitor       | ok       | **0 alerts, 0 to watch.** Long run = 2015 to 2024; recent = 2025 and 2026 so far. ALERT at |z| >= 2.5 or a CUSUM trip (h 5); WATCH at |z| >= 2.0.                                                        |       0.5 |
| shadow watch        | ok       | **0 rules ready for a look.** READY = 30+ settled live bets, a win rate past break-even beyond luck (p <= 0.1) and 5+ points more return per unit risked than the rule it would replace over the same se |       1.1 |
| ready checks        | ok       | **0 ready.** Each READY row opens a GitHub issue labelled ready-check (once per title).                                                                                                                  |       0.4 |
| tie check (sources) | ok       | True                                                                                                                                                                                                     |       4.1 |
| export data room    | ok       |                                                                                                                                                                                                          |     129.6 |
| tie check (page)    | ok       | True                                                                                                                                                                                                     |       8.1 |

## Week 4, 2026: 3 flagged of 16 games

| away_team   | home_team   |   away_exp |   home_exp |   spread_line |   total_line |   spread_edge |   total_edge | bet      |   stake_pct |
|:------------|:------------|-----------:|-----------:|--------------:|-------------:|--------------:|-------------:|:---------|------------:|
| IND         | WAS         |      24.29 |      25.62 |          -3.5 |         48.5 |          4.83 |         1.41 | WAS +3.5 |        1.03 |
| JAX         | CIN         |      26.35 |      24.38 |           2.5 |         51.5 |         -4.47 |        -0.77 | JAX +2.5 |        1.43 |
| ARI         | NYG         |      21.57 |      23.88 |          -2.5 |         44.5 |          4.8  |         0.95 | NYG +2.5 |        1.25 |

Full table: reports/picks_2026_wk4.md

## Track record

## Rules compared

The flag is bet; the shadows are logged and graded on the same games but never bet, so the rule can be chosen on live results.

Backtest columns: the same rule on the three backtest windows, regular season weeks 1 to 17 (`picks.rule_records`).

| Rule | Bets | Settled | Record | Units | Avg CLV | Backtest 2015-18 | Backtest 2019-22 | Backtest 2023-25 |
|---|---|---|---|---|---|---|---|---|
| 4+ edge (the flag, bet) | 3 | 0 | nothing settled |  | +0.00 | 68-55 | 80-51 | 40-21 |
| shadow: 4.5+ edge | 2 | 0 | nothing settled |  | +0.00 | 43-36 | 52-37 | 25-15 |
| shadow: 4+ edge, model's side the underdog or pick'em | 3 | 0 | nothing settled |  | +0.00 | 50-38 | 73-42 | 32-18 |
| shadow: 4+ edge, weeks 1 to 13 only | 3 | 0 | nothing settled |  | +0.00 | 54-41 | 68-37 | 33-16 |

Full record: reports/track_record.md
