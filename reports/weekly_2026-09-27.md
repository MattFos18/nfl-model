# Weekly run, 2026-09-27 21:13 UTC

## Steps

| step                | status   | detail                                                                                                                                                                                                   |   seconds |
|:--------------------|:---------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------:|
| pull                | ok       | [('2026-09-27T21:13:06', 'schedules', 'all', 'https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv', 'ok', 2180471, '3add72df3b0a'), ('2026-09-27T21:13:06', 'players', 'all' |      11.5 |
| pull player history | ok       | [('2026-09-27T21:13:17', 'pfr_advstats', 2018, 'https://github.com/nflverse/nflverse-data/releases/download/pfr_advstats/advstats_week_def_2018.parquet', 'ok', 149299, '8606f428d500'), ('2026-09-27T21 |      11.2 |
| build               | ok       | team_games (8202, 142)                                                                                                                                                                                   |     187.2 |
| features            | ok       | [40 rows x 8 columns]                                                                                                                                                                                    |      19.2 |
| verify              | ok       | Result: PASS                                                                                                                                                                                             |       0.5 |
| weather             | ok       | game_id           kickoff_et  ... precip        fetched_at                                                                                                                                               |     129.6 |
|                     |          | 0    2026_03_ARI_SF  2026-09-27 16:05:00  ...    0.0  2026-09-27 17:16                                                                                                                                   |           |
|                     |          | 1    2026_03_MIN_TB  2026-09-27 16:05:00  ...    0.0  2026                                                                                                                                               |           |
| lines               | ok       | {'ts': '2026-09-27T21-19-05Z', 'season': 2026, 'week': 4, 'rows': 16, 'errors': ''}                                                                                                                      |       1.1 |
| live results        | ok       | live results: week 3, 10 final of 16, 4 in progress; spread 6-3-1, total 6-4, winner 6-4                                                                                                                 |       1.6 |
| ratings             | ok       | (7668, 49)                                                                                                                                                                                               |      32.3 |
| trends              | ok       | head-to-head cover margin      96                 0.355         7.079            2.793                                                                                                                   |      81.6 |
| players             | ok       | max           0.104589         1.360481    14.000000                                                                                                                                                     |     167.2 |
| positions           | ok       | Skill     531.0  0.004282  0.0009  0.0531                                                                                                                                                                |      32.2 |
| scheme              | ok       | scheme_plays (353694, 83) profiles for 32 teams as of 2026 4                                                                                                                                             |       7.9 |
| player splits       | ok       | player_splits.js 1.57 MB                                                                                                                                                                                 |     117.9 |
| snap exposure       | ok       | snap exposure (327629, 10) seasons 2013 to 2026                                                                                                                                                          |       1.4 |
| model               | ok       | neutral            0.082       0.133          0.011                                                                                                                                                      |     110.9 |
| props               | ok       | props 2839 projections for week 4 graded rows 7206 market lines on the cards 0 graded against the market 1129                                                                                            |      31.4 |
| sizing backtest     | ok       | 2025   13-9    0.591        2.82                                                                                                                                                                         |       6.7 |
| threshold sweep     | ok       | DONE                                                                                                                                                                                                     |       1.8 |
| calibration start   | ok       | last 5 seasons     0.5204     0.5223     0.5242              0.69422            0.25053                0.68640              0.5585             0.5895             95              0.69281                |       1.8 |
| season backtest     | ok       | {'shrink0.1_sig1': 'not adopted', 'shrink0.1_sig1.15': 'not adopted', 'shrink0.2_sig1': 'not adopted', 'shrink0.2_sig1.15': 'not adopted', 'shrink0.3_sig1': 'not adopted', 'shrink0.3_sig1.15': 'not ad |     109.1 |
| props by season     | ok       | DONE                                                                                                                                                                                                     |      17.8 |
| legitimacy tests    | ok       | Reading: the line beats the model on the miss every season (it should; it is the market). The question the flag rests on is whether the model's disagreements with the line carry information, which the |      21.7 |
| audit reports       | ok       | Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).                                       |       2.6 |
| picks               | ok       | game_id  season  week  ...     bet_p bet_odds stake_pct                                                                                                                                                  |       0.4 |
|                     |          | 3076  2026_04_PIT_CLE    2026     4  ...       NaN      NaN       NaN                                                                                                                                    |           |
|                     |          | 3077  2026_04_IND_WAS    2026     4  ...  0.546527   -110.0                                                                                                                                              |           |
| log run             | ok       | run_at  season  week  ... spread_line  total_line       bet                                                                                                                                              |       0   |
|                     |          | 3076  2026-09-27 21:13 UTC    2026     4  ...        -3.0        37.5                                                                                                                                    |           |
|                     |          | 3077  2026-09-27 21:13 UTC    2026     4                                                                                                                                                                 |           |
| record picks        | ok       | run_at  season  week  ... spread_edge total_edge  p_cover                                                                                                                                                |       0.1 |
|                     |          | 0  2026-09-27 21:13 UTC    2026     4  ...        5.36       1.87    0.681                                                                                                                               |           |
|                     |          | 1  2026-09-27 21:13 UTC    2026     4  ...       -                                                                                                                                                       |           |
| inputs fingerprint  | ok       | {'season': 2026, 'week': 4, 'starters': {'2026_04_PIT_CLE': ['00-0033537', '00-0023459', '2026-10-01 20:15'], '2026_04_IND_WAS': ['00-0039910', '00-0035710', '2026-10-04 09:30'], '2026_04_TEN_BAL': [' |       0.2 |
| grade               | ok       |                                                                                                                                                                                                          |       0.5 |
| tie check (sources) | ok       | True                                                                                                                                                                                                     |       3.3 |
| export data room    | ok       |                                                                                                                                                                                                          |     131.4 |
| tie check (page)    | ok       | True                                                                                                                                                                                                     |       5.6 |

## Week 4, 2026: 2 flagged of 16 games

| away_team   | home_team   |   away_exp |   home_exp |   spread_line |   total_line |   spread_edge |   total_edge | bet      |   stake_pct |
|:------------|:------------|-----------:|-----------:|--------------:|-------------:|--------------:|-------------:|:---------|------------:|
| IND         | WAS         |      23.76 |      24.62 |          -4.5 |         46.5 |          5.36 |         1.87 | WAS +4.5 |        1.19 |
| JAX         | CIN         |      25.36 |      23.99 |           3   |         49.5 |         -4.37 |        -0.15 | JAX +3   |        0.76 |

Full table: reports/picks_2026_wk4.md

## Track record

## Rules compared

The flag is bet; the shadows are logged and graded on the same games but never bet, so the rule can be chosen on live results.

Backtest columns: the same rule on the three backtest windows, regular season weeks 1 to 17 (`picks.rule_records`).

| Rule | Bets | Settled | Record | Units | Avg CLV | Backtest 2015-18 | Backtest 2019-22 | Backtest 2023-25 |
|---|---|---|---|---|---|---|---|---|
| 4+ edge (the flag, bet) | 2 | 0 | nothing settled |  | +0.00 | 68-55 | 80-51 | 40-21 |
| shadow: 4.5+ edge | 1 | 0 | nothing settled |  | +0.00 | 43-36 | 52-38 | 26-15 |
| shadow: 4+ edge, model's side the underdog or pick'em | 2 | 0 | nothing settled |  | +0.00 | 50-38 | 73-42 | 32-18 |
| shadow: 4+ edge, weeks 1 to 13 only | 2 | 0 | nothing settled |  | +0.00 | 54-41 | 68-37 | 33-16 |

Full record: reports/track_record.md
