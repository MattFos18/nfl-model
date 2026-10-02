# Weekly run, 2026-10-02 11:57 UTC

## Steps

| step                | status   | detail                                                                                                                                                                                                   |   seconds |
|:--------------------|:---------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------:|
| pull                | ok       | [('2026-10-02T11:57:02', 'schedules', 'all', 'https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv', 'ok', 2182453, 'ae8bdaccb1b4'), ('2026-10-02T11:57:02', 'players', 'all' |       6.6 |
| pull player history | ok       | [('2026-10-02T11:57:08', 'pfr_advstats', 2018, 'https://github.com/nflverse/nflverse-data/releases/download/pfr_advstats/advstats_week_def_2018.parquet', 'cached', 149299, ''), ('2026-10-02T11:57:08', |       0   |
| build               | ok       | team_games (8202, 142)                                                                                                                                                                                   |      90.4 |
| features            | ok       | [40 rows x 8 columns]                                                                                                                                                                                    |       8.3 |
| snap exposure       | ok       | snap exposure (329121, 10) seasons 2013 to 2026                                                                                                                                                          |       0.9 |
| verify              | ok       | Result: PASS                                                                                                                                                                                             |       0.3 |
| data checks         | ok       | True                                                                                                                                                                                                     |       0.1 |
| weather             | ok       | game_id           kickoff_et  ... precip        fetched_at                                                                                                                                               |     131.8 |
|                     |          | 0   2026_04_IND_WAS  2026-10-04 09:30:00  ...    0.0  2026-10-02 07:58                                                                                                                                   |           |
|                     |          | 1   2026_04_TEN_BAL  2026-10-04 13:00:00  ...    0.1  2026                                                                                                                                               |           |
| wind forecast       | ok       | 3                                                                                                                                                                                                        |      77   |
| lines               | ok       | {'ts': '2026-10-02T12-02-18Z', 'season': 2026, 'week': 4, 'rows': 238, 'errors': ''}                                                                                                                     |      81.1 |
| live results        | ok       | live results: week 4, 1 final of 16, 0 in progress; spread 1-0, total 0-1, winner 0-1; play-by-play for 1 games                                                                                          |       1.6 |
| ratings             | ok       | (7668, 49)                                                                                                                                                                                               |      14   |
| trends              | ok       | head-to-head cover margin      96                 0.355         7.079            2.793                                                                                                                   |      33.1 |
| players             | ok       | max           0.104589         1.360481    14.000000                                                                                                                                                     |      82.9 |
| positions           | ok       | Skill     539.0  0.007972  0.00260  0.0816                                                                                                                                                               |      18.8 |
| scheme              | ok       | scheme_plays (354592, 83) profiles for 32 teams as of 2026 4                                                                                                                                             |       3.8 |
| player splits       | ok       | player_splits.js 1.61 MB                                                                                                                                                                                 |      48.4 |
| model               | ok       | neutral            0.082       0.133          0.011                                                                                                                                                      |      44.3 |
| opener study        | ok       | opener study written                                                                                                                                                                                     |      42.4 |
| props by season     | ok       | DONE                                                                                                                                                                                                     |      16.9 |
| props               | ok       | props 2884 projections for week 4 graded rows 0 market lines on the cards 300 graded against the market 1833                                                                                             |      15.9 |
| sizing backtest     | ok       | 2025   13-9    0.591        2.82                                                                                                                                                                         |       3.5 |
| threshold sweep     | ok       | DONE                                                                                                                                                                                                     |       1.1 |
| calibration start   | ok       | last 5 seasons     0.5205     0.5225     0.5244              0.69458            0.25071                0.68567              0.5600             0.5895             95              0.69273                |       1.3 |
| season backtest     | ok       | {'shrink0.1_sig1': 'not adopted', 'shrink0.1_sig1.15': 'not adopted', 'shrink0.2_sig1': 'not adopted', 'shrink0.2_sig1.15': 'not adopted', 'shrink0.3_sig1': 'not adopted', 'shrink0.3_sig1.15': 'not ad |      61.7 |
| legitimacy tests    | ok       | Reading: the line beats the model on the miss every season (it should; it is the market). The question the flag rests on is whether the model's disagreements with the line carry information, which the |       9.5 |
| audit reports       | ok       | Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).                                       |       1.5 |
| picks               | ok       | game_id  season  week  ...     bet_p bet_odds stake_pct                                                                                                                                                  |       0.5 |
|                     |          | 3076  2026_04_PIT_CLE    2026     4  ...       NaN      NaN       NaN                                                                                                                                    |           |
|                     |          | 3077  2026_04_IND_WAS    2026     4  ...  0.549245   -110.0                                                                                                                                              |           |
| log run             | ok       | run_at  season  week  ... spread_line  total_line       bet                                                                                                                                              |       0   |
|                     |          | 3076  2026-10-02 11:57 UTC    2026     4  ...        -2.5        38.5                                                                                                                                    |           |
|                     |          | 3077  2026-10-02 11:57 UTC    2026     4                                                                                                                                                                 |           |
| record picks        | ok       | run_at  season  week  ... spread_edge total_edge  p_cover                                                                                                                                                |       0.2 |
|                     |          | 0  2026-10-02 11:57 UTC    2026     4  ...        5.46       1.10    0.688                                                                                                                               |           |
|                     |          | 1  2026-10-02 11:57 UTC    2026     4  ...       -                                                                                                                                                       |           |
| inputs fingerprint  | ok       | {'season': 2026, 'week': 4, 'starters': {'2026_04_PIT_CLE': ['00-0033537', '00-0023459', '2026-10-01 20:15'], '2026_04_IND_WAS': ['00-0039910', '00-0035710', '2026-10-04 09:30'], '2026_04_TEN_BAL': [' |       0.2 |
| grade               | ok       |                                                                                                                                                                                                          |       0.8 |
| closing line value  | ok       | CLV 2026: 4 closed, 11 pending, avg +0.25 pts, 25% beat the close                                                                                                                                        |       0.1 |
| forecast history    | ok       | complete: 1559 games stored                                                                                                                                                                              |       0   |
| drift monitor       | ok       | **0 alerts, 0 to watch.** Long run = 2015 to 2024; recent = 2025 and 2026 so far. ALERT at |z| >= 2.5 or a CUSUM trip (h 5); WATCH at |z| >= 2.0.                                                        |       0.3 |
| shadow watch        | ok       | **0 rules ready for a look.** READY = 30+ settled live bets, a win rate past break-even beyond luck (p <= 0.1) and 5+ points more return per unit risked than the rule it would replace over the same se |       0.7 |
| ready checks        | ok       | **0 ready.** Each READY row opens a GitHub issue labelled ready-check (once per title).                                                                                                                  |       0.3 |
| tie check (sources) | ok       | True                                                                                                                                                                                                     |       2.2 |
| export data room    | ok       |                                                                                                                                                                                                          |      65.5 |
| tie check (page)    | ok       | True                                                                                                                                                                                                     |       4.8 |

## Week 4, 2026: 3 flagged of 16 games

| away_team   | home_team   |   away_exp |   home_exp |   spread_line |   total_line |   spread_edge |   total_edge | bet      |   stake_pct |
|:------------|:------------|-----------:|-----------:|--------------:|-------------:|--------------:|-------------:|:---------|------------:|
| IND         | WAS         |      24.07 |      25.53 |          -4   |         48.5 |          5.46 |         1.1  | WAS +4   |        1.34 |
| JAX         | CIN         |      26.38 |      24.41 |           2.5 |         51.5 |         -4.47 |        -0.71 | JAX +3   |        0    |
| ARI         | NYG         |      19.67 |      21.94 |          -2.5 |         44   |          4.78 |        -2.39 | NYG +2.5 |        1.23 |

Full table: reports/picks_2026_wk4.md

## Track record

## Rules compared

The flag is bet; the shadows are logged and graded on the same games but never bet, so the rule can be chosen on live results.

Backtest columns: the same rule on the three backtest windows, regular season weeks 1 to 17 (`picks.rule_records`).

| Rule | Bets | Settled | Record | Units | Avg CLV | Backtest 2015-18 | Backtest 2019-22 | Backtest 2023-25 |
|---|---|---|---|---|---|---|---|---|
| 4+ edge (the flag, bet) | 3 | 0 | nothing settled |  | +0.17 | 68-55 | 80-51 | 40-21 |
| shadow: 4.5+ edge | 2 | 0 | nothing settled |  | +0.00 | 43-36 | 52-37 | 25-15 |
| shadow: 4+ edge, model's side the underdog or pick'em | 3 | 0 | nothing settled |  | +0.17 | 50-38 | 73-42 | 32-18 |
| shadow: 4+ edge, weeks 1 to 13 only | 3 | 0 | nothing settled |  | +0.17 | 54-41 | 68-37 | 33-16 |

Full record: reports/track_record.md
