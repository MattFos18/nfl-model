# Weekly run, 2026-09-30 07:13 UTC

## Steps

| step                | status   | detail                                                                                                                                                                                                   |   seconds |
|:--------------------|:---------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------:|
| pull                | ok       | [('2026-09-30T07:13:28', 'schedules', 'all', 'https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv', 'ok', 2182348, '62032e264613'), ('2026-09-30T07:13:28', 'players', 'all' |       6.1 |
| pull player history | ok       | [('2026-09-30T07:13:34', 'pfr_advstats', 2018, 'https://github.com/nflverse/nflverse-data/releases/download/pfr_advstats/advstats_week_def_2018.parquet', 'cached', 149299, ''), ('2026-09-30T07:13:34', |       0   |
| build               | ok       | team_games (8202, 142)                                                                                                                                                                                   |     139.5 |
| features            | ok       | [40 rows x 8 columns]                                                                                                                                                                                    |      12.8 |
| snap exposure       | ok       | snap exposure (329030, 10) seasons 2013 to 2026                                                                                                                                                          |       1.2 |
| verify              | ok       | Result: PASS                                                                                                                                                                                             |       0.4 |
| weather             | ok       | game_id          kickoff_et  ... precip        fetched_at                                                                                                                                                |       7.8 |
|                     |          | 0   2026_04_PIT_CLE 2026-10-01 20:15:00  ...    0.0  2026-09-30 03:16                                                                                                                                    |           |
|                     |          | 1   2026_04_IND_WAS 2026-10-04 09:30:00  ...    0.0  2026-09                                                                                                                                             |           |
| lines               | ok       | {'ts': '2026-09-30T07-16-16Z', 'season': 2026, 'week': 4, 'rows': 16, 'errors': ''}                                                                                                                      |       3.6 |
| live results        | ok       | live results: week 4, 0 final of 16, 0 in progress; spread 0-0, total 0-0, winner 0-0; play-by-play for 0 games                                                                                          |       1.4 |
| ratings             | ok       | (7668, 49)                                                                                                                                                                                               |      22.7 |
| trends              | ok       | head-to-head cover margin      96                 0.355         7.079            2.793                                                                                                                   |      49.8 |
| players             | ok       | max           0.104589         1.360481    14.000000                                                                                                                                                     |     115.5 |
| positions           | ok       | Skill     534.0  0.008027  0.00270  0.0816                                                                                                                                                               |      23.9 |
| scheme              | ok       | scheme_plays (354466, 83) profiles for 32 teams as of 2026 4                                                                                                                                             |       5.5 |
| player splits       | ok       | player_splits.js 1.61 MB                                                                                                                                                                                 |      68.7 |
| model               | ok       | neutral            0.082       0.133          0.011                                                                                                                                                      |      44.1 |
| opener study        | ok       | opener study written                                                                                                                                                                                     |      44.2 |
| props by season     | ok       | DONE                                                                                                                                                                                                     |      22.3 |
| props               | ok       | props 2884 projections for week 4 graded rows 0 market lines on the cards 228 graded against the market 1833                                                                                             |      22.8 |
| sizing backtest     | ok       | 2025   13-9    0.591        2.82                                                                                                                                                                         |       4.6 |
| threshold sweep     | ok       | DONE                                                                                                                                                                                                     |       1.4 |
| calibration start   | ok       | last 5 seasons     0.5205     0.5225     0.5244              0.69458            0.25071                0.68567              0.5600             0.5895             95              0.69273                |       1.5 |
| season backtest     | ok       | {'shrink0.1_sig1': 'not adopted', 'shrink0.1_sig1.15': 'not adopted', 'shrink0.2_sig1': 'not adopted', 'shrink0.2_sig1.15': 'not adopted', 'shrink0.3_sig1': 'not adopted', 'shrink0.3_sig1.15': 'not ad |      82.8 |
| legitimacy tests    | ok       | Reading: the line beats the model on the miss every season (it should; it is the market). The question the flag rests on is whether the model's disagreements with the line carry information, which the |      14.2 |
| audit reports       | ok       | Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).                                       |       2   |
| picks               | ok       | game_id  season  week  ...     bet_p bet_odds stake_pct                                                                                                                                                  |       0.5 |
|                     |          | 3076  2026_04_PIT_CLE    2026     4  ...       NaN      NaN       NaN                                                                                                                                    |           |
|                     |          | 3077  2026_04_IND_WAS    2026     4  ...  0.546752   -112.0                                                                                                                                              |           |
| log run             | ok       | run_at  season  week  ... spread_line  total_line       bet                                                                                                                                              |       0   |
|                     |          | 3076  2026-09-30 07:13 UTC    2026     4  ...        -2.5        38.5                                                                                                                                    |           |
|                     |          | 3077  2026-09-30 07:13 UTC    2026     4                                                                                                                                                                 |           |
| record picks        | ok       | run_at  season  week  ... spread_edge total_edge  p_cover                                                                                                                                                |       0.1 |
|                     |          | 0  2026-09-30 07:13 UTC    2026     4  ...        5.19       1.90    0.675                                                                                                                               |           |
|                     |          | 1  2026-09-30 07:13 UTC    2026     4  ...       -                                                                                                                                                       |           |
| inputs fingerprint  | ok       | {'season': 2026, 'week': 4, 'starters': {'2026_04_PIT_CLE': ['00-0033537', '00-0023459', '2026-10-01 20:15'], '2026_04_IND_WAS': ['00-0039910', '00-0035710', '2026-10-04 09:30'], '2026_04_TEN_BAL': [' |       0.2 |
| grade               | ok       |                                                                                                                                                                                                          |       0.4 |
| tie check (sources) | ok       | True                                                                                                                                                                                                     |       3   |
| export data room    | ok       |                                                                                                                                                                                                          |      89.7 |
| tie check (page)    | ok       | True                                                                                                                                                                                                     |       5.4 |

## Week 4, 2026: 2 flagged of 16 games

| away_team   | home_team   |   away_exp |   home_exp |   spread_line |   total_line |   spread_edge |   total_edge | bet      |   stake_pct |
|:------------|:------------|-----------:|-----------:|--------------:|-------------:|--------------:|-------------:|:---------|------------:|
| IND         | WAS         |      23.86 |      25.54 |          -3.5 |         47.5 |          5.19 |         1.9  | WAS +3.5 |        0.98 |
| JAX         | CIN         |      25.37 |      23.57 |           2.5 |         51.5 |         -4.3  |        -2.56 | JAX +2.5 |        1.35 |

Full table: reports/picks_2026_wk4.md

## Track record

## Rules compared

The flag is bet; the shadows are logged and graded on the same games but never bet, so the rule can be chosen on live results.

Backtest columns: the same rule on the three backtest windows, regular season weeks 1 to 17 (`picks.rule_records`).

| Rule | Bets | Settled | Record | Units | Avg CLV | Backtest 2015-18 | Backtest 2019-22 | Backtest 2023-25 |
|---|---|---|---|---|---|---|---|---|
| 4+ edge (the flag, bet) | 2 | 0 | nothing settled |  | +0.00 | 68-55 | 80-51 | 40-21 |
| shadow: 4.5+ edge | 1 | 0 | nothing settled |  | +0.00 | 43-36 | 52-37 | 25-15 |
| shadow: 4+ edge, model's side the underdog or pick'em | 2 | 0 | nothing settled |  | +0.00 | 50-38 | 73-42 | 32-18 |
| shadow: 4+ edge, weeks 1 to 13 only | 2 | 0 | nothing settled |  | +0.00 | 54-41 | 68-37 | 33-16 |

Full record: reports/track_record.md
