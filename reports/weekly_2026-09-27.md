# Weekly run, 2026-09-27 22:18 UTC

## Steps

| step                | status   | detail                                                                                                                                                                                                   |   seconds |
|:--------------------|:---------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------:|
| pull                | ok       | [('2026-09-27T22:18:27', 'schedules', 'all', 'https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv', 'ok', 2180921, '7f6776f4c6cc'), ('2026-09-27T22:18:27', 'players', 'all' |      11.4 |
| pull player history | ok       | [('2026-09-27T22:18:39', 'pfr_advstats', 2018, 'https://github.com/nflverse/nflverse-data/releases/download/pfr_advstats/advstats_week_def_2018.parquet', 'ok', 149299, '8606f428d500'), ('2026-09-27T22 |       9.8 |
| build               | ok       | team_games (8202, 142)                                                                                                                                                                                   |     118   |
| features            | ok       | [40 rows x 8 columns]                                                                                                                                                                                    |      10.7 |
| verify              | ok       | Result: PASS                                                                                                                                                                                             |       0.4 |
| weather             | ok       | game_id          kickoff_et  ... precip        fetched_at                                                                                                                                                |       3.7 |
|                     |          | 0    2026_03_ARI_SF 2026-09-27 16:05:00  ...    0.0  2026-09-27 18:20                                                                                                                                    |           |
|                     |          | 1    2026_03_MIN_TB 2026-09-27 16:05:00  ...    0.0  2026-09                                                                                                                                             |           |
| lines               | ok       | {'ts': '2026-09-27T22-21-02Z', 'season': 2026, 'week': 4, 'rows': 16, 'errors': ''}                                                                                                                      |       0.9 |
| live results        | ok       | live results: week 3, 10 final of 16, 4 in progress; spread 6-3-1, total 6-4, winner 6-4                                                                                                                 |       1.3 |
| ratings             | ok       | (7668, 49)                                                                                                                                                                                               |      17.6 |
| trends              | ok       | head-to-head cover margin      96                 0.355         7.079            2.793                                                                                                                   |      41.5 |
| players             | ok       | max           0.104589         1.360481    14.000000                                                                                                                                                     |      95.9 |
| positions           | ok       | Skill     531.0  0.004282  0.0009  0.0531                                                                                                                                                                |      19.7 |
| scheme              | ok       | scheme_plays (353694, 83) profiles for 32 teams as of 2026 4                                                                                                                                             |       4.3 |
| player splits       | ok       | player_splits.js 1.57 MB                                                                                                                                                                                 |      57.5 |
| snap exposure       | ok       | snap exposure (327629, 10) seasons 2013 to 2026                                                                                                                                                          |       1   |
| model               | ok       | neutral            0.082       0.133          0.011                                                                                                                                                      |      70.1 |
| props               | ok       | props 2829 projections for week 4 graded rows 0 market lines on the cards 0 graded against the market 1129                                                                                               |      15.3 |
| sizing backtest     | ok       | 2025   13-9    0.591        2.82                                                                                                                                                                         |       4   |
| threshold sweep     | ok       | DONE                                                                                                                                                                                                     |       1.2 |
| calibration start   | ok       | last 5 seasons     0.5206     0.5229     0.5252              0.69435            0.25060                0.68604              0.5591             0.5895             95              0.69275                |       1.2 |
| season backtest     | ok       | {'shrink0.1_sig1': 'not adopted', 'shrink0.1_sig1.15': 'not adopted', 'shrink0.2_sig1': 'not adopted', 'shrink0.2_sig1.15': 'not adopted', 'shrink0.3_sig1': 'not adopted', 'shrink0.3_sig1.15': 'not ad |      70.2 |
| props by season     | ok       | DONE                                                                                                                                                                                                     |      10.3 |
| legitimacy tests    | ok       | Reading: the line beats the model on the miss every season (it should; it is the market). The question the flag rests on is whether the model's disagreements with the line carry information, which the |      12.2 |
| audit reports       | ok       | Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).                                       |       1.8 |
| picks               | ok       | game_id  season  week  ...     bet_p bet_odds stake_pct                                                                                                                                                  |       0.2 |
|                     |          | 3076  2026_04_PIT_CLE    2026     4  ...       NaN      NaN       NaN                                                                                                                                    |           |
|                     |          | 3077  2026_04_IND_WAS    2026     4  ...  0.538661   -110.0                                                                                                                                              |           |
| log run             | ok       | run_at  season  week  ... spread_line  total_line       bet                                                                                                                                              |       0   |
|                     |          | 3076  2026-09-27 22:18 UTC    2026     4  ...        -2.5        38.5                                                                                                                                    |           |
|                     |          | 3077  2026-09-27 22:18 UTC    2026     4                                                                                                                                                                 |           |
| record picks        | ok       | run_at  season  week  ... spread_edge total_edge  p_cover                                                                                                                                                |       0.1 |
|                     |          | 0  2026-09-27 22:18 UTC    2026     4  ...        4.35       1.88    0.653                                                                                                                               |           |
|                     |          |                                                                                                                                                                                                          |           |
|                     |          | [1 rows x 12 columns]                                                                                                                                                                                    |           |
| inputs fingerprint  | ok       | {'season': 2026, 'week': 4, 'starters': {'2026_04_PIT_CLE': ['00-0033537', '00-0023459', '2026-10-01 20:15'], '2026_04_IND_WAS': ['00-0039910', '00-0035710', '2026-10-04 09:30'], '2026_04_TEN_BAL': [' |       0.1 |
| grade               | ok       |                                                                                                                                                                                                          |       0.2 |
| tie check (sources) | ok       | True                                                                                                                                                                                                     |       2   |
| export data room    | ok       |                                                                                                                                                                                                          |      72.4 |
| tie check (page)    | ok       | True                                                                                                                                                                                                     |       3.3 |

## Week 4, 2026: 1 flagged of 16 games

| away_team   | home_team   |   away_exp |   home_exp |   spread_line |   total_line |   spread_edge |   total_edge | bet      |   stake_pct |
|:------------|:------------|-----------:|-----------:|--------------:|-------------:|--------------:|-------------:|:---------|------------:|
| IND         | WAS         |      23.76 |      24.62 |          -3.5 |         46.5 |          4.35 |         1.88 | WAS +3.5 |        0.78 |

Full table: reports/picks_2026_wk4.md

## Track record

## Rules compared

The flag is bet; the shadows are logged and graded on the same games but never bet, so the rule can be chosen on live results.

Backtest columns: the same rule on the three backtest windows, regular season weeks 1 to 17 (`picks.rule_records`).

| Rule | Bets | Settled | Record | Units | Avg CLV | Backtest 2015-18 | Backtest 2019-22 | Backtest 2023-25 |
|---|---|---|---|---|---|---|---|---|
| 4+ edge (the flag, bet) | 1 | 0 | nothing settled |  | +0.00 | 68-55 | 80-51 | 40-21 |
| shadow: 4.5+ edge | 0 | 0 | | | | 43-36 | 52-37 | 25-15 |
| shadow: 4+ edge, model's side the underdog or pick'em | 1 | 0 | nothing settled |  | +0.00 | 50-38 | 73-42 | 32-18 |
| shadow: 4+ edge, weeks 1 to 13 only | 1 | 0 | nothing settled |  | +0.00 | 54-41 | 68-37 | 33-16 |

Full record: reports/track_record.md
