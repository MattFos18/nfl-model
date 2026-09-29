# Weekly run, 2026-09-29 14:19 UTC

## Steps

| step                | status   | detail                                                                                                                                                                                                   |   seconds |
|:--------------------|:---------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------:|
| pull                | ok       | [('2026-09-29T14:19:58', 'schedules', 'all', 'https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv', 'ok', 2181240, '5978365f966a'), ('2026-09-29T14:19:58', 'players', 'all' |       7.6 |
| pull player history | ok       | [('2026-09-29T14:20:06', 'pfr_advstats', 2018, 'https://github.com/nflverse/nflverse-data/releases/download/pfr_advstats/advstats_week_def_2018.parquet', 'ok', 149299, '8606f428d500'), ('2026-09-29T14 |       7.7 |
| build               | ok       | team_games (8202, 142)                                                                                                                                                                                   |     181.4 |
| features            | ok       | [40 rows x 8 columns]                                                                                                                                                                                    |      18.8 |
| verify              | ok       | Result: PASS                                                                                                                                                                                             |       0.5 |
| weather             | ok       | game_id          kickoff_et  ... precip        fetched_at                                                                                                                                                |       5.6 |
|                     |          | 0   2026_04_PIT_CLE 2026-10-01 20:15:00  ...    0.0  2026-09-29 10:23                                                                                                                                    |           |
|                     |          | 1   2026_04_IND_WAS 2026-10-04 09:30:00  ...    2.1  2026-09                                                                                                                                             |           |
| lines               | ok       | {'ts': '2026-09-29T14-23-40Z', 'season': 2026, 'week': 3, 'rows': 16, 'errors': ''}                                                                                                                      |       1.3 |
| live results        | ok       | live results: week 3, 16 final of 16, 0 in progress; spread 9-5-2, total 10-6, winner 10-6; play-by-play for 16 games                                                                                    |       1.1 |
| ratings             | ok       | (7668, 49)                                                                                                                                                                                               |      31.9 |
| trends              | ok       | head-to-head cover margin      96                 0.355         7.079            2.793                                                                                                                   |      82.2 |
| players             | ok       | max           0.104589         1.360481    14.000000                                                                                                                                                     |     165.2 |
| positions           | ok       | Skill     527.0  0.004299  0.00080  0.0531                                                                                                                                                               |      31.7 |
| scheme              | ok       | scheme_plays (354466, 83) profiles for 32 teams as of 2026 3                                                                                                                                             |       7.8 |
| player splits       | ok       | player_splits.js 1.61 MB                                                                                                                                                                                 |     119.6 |
| snap exposure       | ok       | snap exposure (329030, 10) seasons 2013 to 2026                                                                                                                                                          |       1.3 |
| model               | ok       | neutral            0.082       0.133          0.011                                                                                                                                                      |      72.3 |
| opener study        | ok       | opener study written                                                                                                                                                                                     |      72.6 |
| props               | ok       | props 2916 projections for week 4 graded rows 8394 market lines on the cards 0 graded against the market 1833                                                                                            |      33.9 |
| sizing backtest     | ok       | 2025   13-9    0.591        2.82                                                                                                                                                                         |       6.8 |
| threshold sweep     | ok       | DONE                                                                                                                                                                                                     |       1.8 |
| calibration start   | ok       | last 5 seasons     0.5205     0.5225     0.5244              0.69458            0.25071                0.68567              0.5600             0.5895             95              0.69273                |       1.8 |
| season backtest     | ok       | {'shrink0.1_sig1': 'not adopted', 'shrink0.1_sig1.15': 'not adopted', 'shrink0.2_sig1': 'not adopted', 'shrink0.2_sig1.15': 'not adopted', 'shrink0.3_sig1': 'not adopted', 'shrink0.3_sig1.15': 'not ad |     107.5 |
| props by season     | ok       | DONE                                                                                                                                                                                                     |      17.4 |
| legitimacy tests    | ok       | Reading: the line beats the model on the miss every season (it should; it is the market). The question the flag rests on is whether the model's disagreements with the line carry information, which the |      21.4 |
| audit reports       | ok       | Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).                                       |       2.6 |
| picks               | ok       | game_id  season  week  ...     bet_p bet_odds stake_pct                                                                                                                                                  |       0.8 |
|                     |          | 3076  2026_04_PIT_CLE    2026     4  ...       NaN      NaN       NaN                                                                                                                                    |           |
|                     |          | 3077  2026_04_IND_WAS    2026     4  ...  0.547745   -112.0                                                                                                                                              |           |
| log run             | ok       | run_at  season  week  ... spread_line  total_line       bet                                                                                                                                              |       0   |
|                     |          | 3076  2026-09-29 14:19 UTC    2026     4  ...        -2.5        38.5                                                                                                                                    |           |
|                     |          | 3077  2026-09-29 14:19 UTC    2026     4                                                                                                                                                                 |           |
| record picks        | ok       | run_at  season  week  ... spread_edge total_edge  p_cover                                                                                                                                                |       0.1 |
|                     |          | 0  2026-09-29 14:19 UTC    2026     4  ...        5.30       1.90    0.678                                                                                                                               |           |
|                     |          | 1  2026-09-29 14:19 UTC    2026     4  ...       -                                                                                                                                                       |           |
| inputs fingerprint  | ok       | {'season': 2026, 'week': 4, 'starters': {'2026_04_PIT_CLE': ['00-0033537', '00-0023459', '2026-10-01 20:15'], '2026_04_IND_WAS': ['00-0039910', '00-0035710', '2026-10-04 09:30'], '2026_04_TEN_BAL': [' |       0.2 |
| grade               | ok       |                                                                                                                                                                                                          |       0.6 |
| tie check (sources) | error    | RuntimeError: numbers disagree: see reports/tie_check.md                                                                                                                                                 |       3.4 |
| export data room    | ok       |                                                                                                                                                                                                          |     136.4 |
| tie check (page)    | error    | RuntimeError: page files disagree with the sources: see reports/tie_check.md                                                                                                                             |       6.3 |

**Failed steps above were skipped, not filled with stale data.**

## Week 4, 2026: 4 flagged of 16 games

| away_team   | home_team   |   away_exp |   home_exp |   spread_line |   total_line |   spread_edge |   total_edge | bet      |   stake_pct |
|:------------|:------------|-----------:|-----------:|--------------:|-------------:|--------------:|-------------:|:---------|------------:|
| IND         | WAS         |      23.8  |      25.6  |          -3.5 |         47.5 |          5.3  |         1.9  | WAS +3.5 |        1.03 |
| JAX         | CIN         |      25.3  |      23.63 |           2.5 |         51.5 |         -4.17 |        -2.56 | JAX +2.5 |        1.29 |
| ARI         | NYG         |      21.07 |      23.86 |          -1.5 |         44.5 |          4.29 |         0.43 | NYG +1.5 |        0    |
| GB          | TB          |      20.8  |      23.39 |          -3.5 |         39.5 |          6.08 |         4.69 | TB +3.5  |        2.75 |

Full table: reports/picks_2026_wk4.md

## Track record

## Rules compared

The flag is bet; the shadows are logged and graded on the same games but never bet, so the rule can be chosen on live results.

Backtest columns: the same rule on the three backtest windows, regular season weeks 1 to 17 (`picks.rule_records`).

| Rule | Bets | Settled | Record | Units | Avg CLV | Backtest 2015-18 | Backtest 2019-22 | Backtest 2023-25 |
|---|---|---|---|---|---|---|---|---|
| 4+ edge (the flag, bet) | 4 | 0 | nothing settled |  | +0.00 | 68-55 | 80-51 | 40-21 |
| shadow: 4.5+ edge | 2 | 0 | nothing settled |  | +0.00 | 43-36 | 52-37 | 25-15 |
| shadow: 4+ edge, model's side the underdog or pick'em | 4 | 0 | nothing settled |  | +0.00 | 50-38 | 73-42 | 32-18 |
| shadow: 4+ edge, weeks 1 to 13 only | 4 | 0 | nothing settled |  | +0.00 | 54-41 | 68-37 | 33-16 |

Full record: reports/track_record.md
