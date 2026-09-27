# Weekly run, 2026-09-27 20:12 UTC

## Steps

| step                | status   | detail                                                                                                                                                                                                   |   seconds |
|:--------------------|:---------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------:|
| pull                | ok       | [('2026-09-27T20:12:54', 'schedules', 'all', 'https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv', 'ok', 2180470, 'fcbc30a23d73'), ('2026-09-27T20:12:54', 'players', 'all' |      11.3 |
| pull player history | ok       | [('2026-09-27T20:13:05', 'pfr_advstats', 2018, 'https://github.com/nflverse/nflverse-data/releases/download/pfr_advstats/advstats_week_def_2018.parquet', 'ok', 149299, '8606f428d500'), ('2026-09-27T20 |      11.8 |
| build               | ok       | team_games (8202, 142)                                                                                                                                                                                   |     183.8 |
| features            | ok       | [40 rows x 8 columns]                                                                                                                                                                                    |      19.2 |
| verify              | ok       | Result: PASS                                                                                                                                                                                             |       0.5 |
| weather             | ok       | game_id          kickoff_et  ... precip        fetched_at                                                                                                                                                |     128.4 |
|                     |          | 0   2026_03_BAL_DAL 2026-09-27 16:25:00  ...    0.0  2026-09-27 16:16                                                                                                                                    |           |
|                     |          | 1    2026_03_LA_DEN 2026-09-27 20:20:00  ...    0.0  2026-09                                                                                                                                             |           |
| lines               | ok       | {'ts': '2026-09-27T20-18-49Z', 'season': 2026, 'week': 3, 'rows': 4, 'errors': ''}                                                                                                                       |       1.7 |
| ratings             | ok       | (7668, 49)                                                                                                                                                                                               |      32.1 |
| trends              | ok       | head-to-head cover margin      96                 0.355         7.079            2.793                                                                                                                   |      83.7 |
| players             | ok       | max           0.104589         1.360481    14.000000                                                                                                                                                     |     164.3 |
| positions           | ok       | Skill     527.0  0.004299  0.00080  0.0531                                                                                                                                                               |      31.6 |
| scheme              | ok       | scheme_plays (352588, 83) profiles for 32 teams as of 2026 3                                                                                                                                             |       7.8 |
| player splits       | ok       | player_splits.js 1.56 MB                                                                                                                                                                                 |     118.6 |
| snap exposure       | ok       | snap exposure (327629, 10) seasons 2013 to 2026                                                                                                                                                          |       1.4 |
| model               | ok       | neutral            0.082       0.133          0.011                                                                                                                                                      |     111.2 |
| props               | ok       | props 2829 projections for week 4 graded rows 5622 market lines on the cards 0 graded against the market 129                                                                                             |      26   |
| sizing backtest     | ok       | 2025   13-9    0.591        2.82                                                                                                                                                                         |       6.8 |
| threshold sweep     | ok       | DONE                                                                                                                                                                                                     |       1.8 |
| calibration start   | ok       | last 5 seasons     0.5212     0.5238     0.5264              0.69443            0.25063                0.68651              0.5593             0.5895             95              0.69260                |       1.8 |
| season backtest     | ok       | {'shrink0.1_sig1': 'not adopted', 'shrink0.1_sig1.15': 'not adopted', 'shrink0.2_sig1': 'not adopted', 'shrink0.2_sig1.15': 'not adopted', 'shrink0.3_sig1': 'not adopted', 'shrink0.3_sig1.15': 'not ad |     108.7 |
| props by season     | ok       | DONE                                                                                                                                                                                                     |      17.6 |
| legitimacy tests    | ok       | Reading: the line beats the model on the miss every season (it should; it is the market). The question the flag rests on is whether the model's disagreements with the line carry information, which the |      21.4 |
| audit reports       | ok       | Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).                                       |       2.6 |
| picks               | ok       | game_id  season  week  ...     bet_p bet_odds stake_pct                                                                                                                                                  |       0.4 |
|                     |          | 3076  2026_04_PIT_CLE    2026     4  ...       NaN      NaN       NaN                                                                                                                                    |           |
|                     |          | 3077  2026_04_IND_WAS    2026     4  ...  0.556829   -110.0                                                                                                                                              |           |
| log run             | ok       | run_at  season  week  ... spread_line  total_line       bet                                                                                                                                              |       0   |
|                     |          | 3076  2026-09-27 20:12 UTC    2026     4  ...        -2.5        37.5                                                                                                                                    |           |
|                     |          | 3077  2026-09-27 20:12 UTC    2026     4                                                                                                                                                                 |           |
| record picks        | ok       | run_at season week  ... spread_edge total_edge p_cover                                                                                                                                                   |       0.1 |
|                     |          | 0  2026-09-27 20:12 UTC   2026    4  ...        6.12       4.09   0.701                                                                                                                                  |           |
|                     |          |                                                                                                                                                                                                          |           |
|                     |          | [1 rows x 12 columns]                                                                                                                                                                                    |           |
| inputs fingerprint  | ok       | {'season': 2026, 'week': 4, 'starters': {'2026_04_PIT_CLE': ['00-0033537', '00-0023459', '2026-10-01 20:15'], '2026_04_IND_WAS': ['00-0039910', '00-0035710', '2026-10-04 09:30'], '2026_04_TEN_BAL': [' |       0.2 |
| grade               | ok       |                                                                                                                                                                                                          |       0.5 |
| tie check (sources) | error    | RuntimeError: numbers disagree: see reports/tie_check.md                                                                                                                                                 |       3.2 |
| export data room    | ok       |                                                                                                                                                                                                          |     141.1 |
| tie check (page)    | error    | RuntimeError: page files disagree with the sources: see reports/tie_check.md                                                                                                                             |       5.3 |

**Failed steps above were skipped, not filled with stale data.**

## Week 4, 2026: 1 flagged of 16 games

| away_team   | home_team   |   away_exp |   home_exp |   spread_line |   total_line |   spread_edge |   total_edge | bet      |   stake_pct |
|:------------|:------------|-----------:|-----------:|--------------:|-------------:|--------------:|-------------:|:---------|------------:|
| IND         | WAS         |      24.24 |      25.86 |          -4.5 |           46 |          6.12 |         4.09 | WAS +4.5 |        1.73 |

Full table: reports/picks_2026_wk4.md

## Track record

## Rules compared

The flag is bet; the shadows are logged and graded on the same games but never bet, so the rule can be chosen on live results.

Backtest columns: the same rule on the three backtest windows, regular season weeks 1 to 17 (`picks.rule_records`).

| Rule | Bets | Settled | Record | Units | Avg CLV | Backtest 2015-18 | Backtest 2019-22 | Backtest 2023-25 |
|---|---|---|---|---|---|---|---|---|
| 4+ edge (the flag, bet) | 1 | 0 | nothing settled |  | +0.00 | 68-55 | 80-51 | 40-21 |
| shadow: 4.5+ edge | 1 | 0 | nothing settled |  | +0.00 | 43-36 | 52-37 | 25-15 |
| shadow: 4+ edge, model's side the underdog or pick'em | 1 | 0 | nothing settled |  | +0.00 | 50-38 | 73-42 | 32-18 |
| shadow: 4+ edge, weeks 1 to 13 only | 1 | 0 | nothing settled |  | +0.00 | 54-41 | 68-37 | 33-16 |

Full record: reports/track_record.md
