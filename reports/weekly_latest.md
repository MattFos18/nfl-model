# Weekly run, 2026-09-27 21:59 UTC

## Steps

| step                | status   | detail                                                                                                                                                                                                   |   seconds |
|:--------------------|:---------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------:|
| pull                | ok       | [('2026-09-27T21:59:04', 'schedules', 'all', 'https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv', 'ok', 2180471, '253020a80061'), ('2026-09-27T21:59:04', 'players', 'all' |       6   |
| pull player history | ok       | [('2026-09-27T21:59:10', 'pfr_advstats', 2018, 'https://github.com/nflverse/nflverse-data/releases/download/pfr_advstats/advstats_week_def_2018.parquet', 'ok', 149299, '8606f428d500'), ('2026-09-27T21 |       5   |
| build               | ok       | team_games (8202, 142)                                                                                                                                                                                   |     124.1 |
| features            | ok       | [40 rows x 8 columns]                                                                                                                                                                                    |      10.7 |
| verify              | ok       | Result: PASS                                                                                                                                                                                             |       0.4 |
| weather             | ok       | game_id           kickoff_et  ... precip        fetched_at                                                                                                                                               |     125.5 |
|                     |          | 0    2026_03_ARI_SF  2026-09-27 16:05:00  ...    0.0  2026-09-27 18:01                                                                                                                                   |           |
|                     |          | 1    2026_03_MIN_TB  2026-09-27 16:05:00  ...    0.0  2026                                                                                                                                               |           |
| lines               | ok       | {'ts': '2026-09-27T22-03-36Z', 'season': 2026, 'week': 4, 'rows': 16, 'errors': ''}                                                                                                                      |       0.8 |
| live results        | ok       | live results: week 3, 10 final of 16, 4 in progress; spread 6-3-1, total 6-4, winner 6-4                                                                                                                 |       1.3 |
| ratings             | ok       | (7668, 49)                                                                                                                                                                                               |      20.1 |
| trends              | ok       | head-to-head cover margin      96                 0.355         7.079            2.793                                                                                                                   |      49.2 |
| players             | ok       | max           0.104589         1.360481    14.000000                                                                                                                                                     |     107.6 |
| positions           | ok       | Skill     531.0  0.004282  0.0009  0.0531                                                                                                                                                                |      21.7 |
| scheme              | ok       | scheme_plays (353694, 83) profiles for 32 teams as of 2026 4                                                                                                                                             |       5.1 |
| player splits       | ok       | player_splits.js 1.57 MB                                                                                                                                                                                 |      66.7 |
| snap exposure       | ok       | snap exposure (327629, 10) seasons 2013 to 2026                                                                                                                                                          |       1.1 |
| model               | ok       | neutral            0.082       0.133          0.011                                                                                                                                                      |      82   |
| props               | ok       | props 2839 projections for week 4 graded rows 0 market lines on the cards 0 graded against the market 1129                                                                                               |      17.2 |
| sizing backtest     | ok       | 2025   13-9    0.591        2.82                                                                                                                                                                         |       4.4 |
| threshold sweep     | ok       | DONE                                                                                                                                                                                                     |       1.4 |
| calibration start   | ok       | last 5 seasons     0.5210     0.5235     0.5260              0.69442            0.25063                0.68651              0.5592             0.5895             95              0.69261                |       1.5 |
| season backtest     | ok       | {'shrink0.1_sig1': 'not adopted', 'shrink0.1_sig1.15': 'not adopted', 'shrink0.2_sig1': 'not adopted', 'shrink0.2_sig1.15': 'not adopted', 'shrink0.3_sig1': 'not adopted', 'shrink0.3_sig1.15': 'not ad |      82.6 |
| props by season     | ok       | DONE                                                                                                                                                                                                     |      11.8 |
| legitimacy tests    | ok       | Reading: the line beats the model on the miss every season (it should; it is the market). The question the flag rests on is whether the model's disagreements with the line carry information, which the |      13.6 |
| audit reports       | ok       | Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).                                       |       1.9 |
| picks               | ok       | game_id  season  week  ...     bet_p bet_odds stake_pct                                                                                                                                                  |       0.2 |
|                     |          | 3076  2026_04_PIT_CLE    2026     4  ...       NaN      NaN       NaN                                                                                                                                    |           |
|                     |          | 3077  2026_04_IND_WAS    2026     4  ...  0.539487   -110.0                                                                                                                                              |           |
| log run             | ok       | run_at  season  week  ... spread_line  total_line       bet                                                                                                                                              |       0   |
|                     |          | 3076  2026-09-27 21:59 UTC    2026     4  ...        -2.5        38.5                                                                                                                                    |           |
|                     |          | 3077  2026-09-27 21:59 UTC    2026     4                                                                                                                                                                 |           |
| record picks        | ok       | run_at  season  week  ... spread_edge total_edge  p_cover                                                                                                                                                |       0.1 |
|                     |          | 0  2026-09-27 21:59 UTC    2026     4  ...        4.35       1.88    0.653                                                                                                                               |           |
|                     |          | 1  2026-09-27 21:59 UTC    2026     4  ...       -                                                                                                                                                       |           |
| inputs fingerprint  | ok       | {'season': 2026, 'week': 4, 'starters': {'2026_04_PIT_CLE': ['00-0033537', '00-0023459', '2026-10-01 20:15'], '2026_04_IND_WAS': ['00-0039910', '00-0035710', '2026-10-04 09:30'], '2026_04_TEN_BAL': [' |       0.2 |
| grade               | ok       |                                                                                                                                                                                                          |       0.3 |
| tie check (sources) | ok       | True                                                                                                                                                                                                     |       2.2 |
| export data room    | ok       |                                                                                                                                                                                                          |      84.9 |
| tie check (page)    | ok       | True                                                                                                                                                                                                     |       3.9 |

## Week 4, 2026: 2 flagged of 16 games

| away_team   | home_team   |   away_exp |   home_exp |   spread_line |   total_line |   spread_edge |   total_edge | bet      |   stake_pct |
|:------------|:------------|-----------:|-----------:|--------------:|-------------:|--------------:|-------------:|:---------|------------:|
| IND         | WAS         |      23.76 |      24.62 |          -3.5 |         46.5 |          4.35 |         1.88 | WAS +3.5 |        0.82 |
| JAX         | CIN         |      25.35 |      24    |           3   |         49.5 |         -4.34 |        -0.15 | JAX +3   |        0.82 |

Full table: reports/picks_2026_wk4.md

## Track record

## Rules compared

The flag is bet; the shadows are logged and graded on the same games but never bet, so the rule can be chosen on live results.

Backtest columns: the same rule on the three backtest windows, regular season weeks 1 to 17 (`picks.rule_records`).

| Rule | Bets | Settled | Record | Units | Avg CLV | Backtest 2015-18 | Backtest 2019-22 | Backtest 2023-25 |
|---|---|---|---|---|---|---|---|---|
| 4+ edge (the flag, bet) | 2 | 0 | nothing settled |  | +0.00 | 68-55 | 80-51 | 40-21 |
| shadow: 4.5+ edge | 0 | 0 | | | | 43-36 | 52-37 | 25-15 |
| shadow: 4+ edge, model's side the underdog or pick'em | 2 | 0 | nothing settled |  | +0.00 | 50-38 | 73-42 | 32-18 |
| shadow: 4+ edge, weeks 1 to 13 only | 2 | 0 | nothing settled |  | +0.00 | 54-41 | 68-37 | 33-16 |

Full record: reports/track_record.md
