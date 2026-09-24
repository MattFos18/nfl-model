# Weekly run, 2026-09-24 01:34 UTC

## Steps

| step                | status   | detail                                                                                                                                                                                                   |   seconds |
|:--------------------|:---------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------:|
| pull                | ok       | [('2026-09-24T01:34:38', 'schedules', 'all', 'https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv', 'ok', 2180727, 'c4797524cea9'), ('2026-09-24T01:34:38', 'pbp', 2025, 'ht |       3.5 |
| pull player history | ok       | [('2026-09-24T01:34:41', 'pfr_advstats', 2018, 'https://github.com/nflverse/nflverse-data/releases/download/pfr_advstats/advstats_week_def_2018.parquet', 'ok', 149299, '8606f428d500'), ('2026-09-24T01 |       5.3 |
| build               | ok       | team_games (8202, 142)                                                                                                                                                                                   |     254.6 |
| features            | ok       | [40 rows x 8 columns]                                                                                                                                                                                    |      20.5 |
| verify              | ok       | Result: PASS                                                                                                                                                                                             |       0.6 |
| weather             | ok       | game_id          kickoff_et  ... precip        fetched_at                                                                                                                                                |      78.6 |
|                     |          | 0    2026_03_ATL_GB 2026-09-24 20:15:00  ...    0.0  2026-09-23 21:39                                                                                                                                    |           |
|                     |          | 1   2026_03_LAC_BUF 2026-09-27 13:00:00  ...    0.0  2026-09                                                                                                                                             |           |
| lines               | ok       | {'ts': '2026-09-24T01-40-41Z', 'season': 2026, 'week': 3, 'rows': 16, 'errors': "draftkings: sportsbook.draftkings.com: 403 Client Error: Forbidden for url: https://sportsbook.draf | sportsbook-nash.d |       3.3 |
| ratings             | ok       | (7668, 49)                                                                                                                                                                                               |      33.3 |
| trends              | ok       | head-to-head cover margin      96                 0.355         7.079            2.793                                                                                                                   |      83.5 |
| players             | ok       | max           0.104589         1.360481    14.000000                                                                                                                                                     |     168.4 |
| positions           | ok       | Skill    525.0  0.004296  0.00080  0.0531                                                                                                                                                                |      15.1 |
| scheme              | ok       | scheme_plays (352459, 83) profiles for 32 teams as of 2026 3                                                                                                                                             |       8.1 |
| props               | ok       | props 2859 projections for week 3 graded rows 0 market lines on the cards 368 graded against the market 0                                                                                                |      24.6 |
| model               | ok       | neutral            0.091       0.133          0.012                                                                                                                                                      |      32.2 |
| picks               | ok       | game_id  season  week  ...     bet_p bet_odds stake_pct                                                                                                                                                  |       0.3 |
|                     |          | 3060   2026_03_ATL_GB    2026     3  ...       NaN      NaN       NaN                                                                                                                                    |           |
|                     |          | 3061  2026_03_LAC_BUF    2026     3  ...       NaN      NaN                                                                                                                                              |           |
| log run             | ok       | run_at  season  week  ... spread_line  total_line        bet                                                                                                                                             |       0   |
|                     |          | 3060  2026-09-24 01:34 UTC    2026     3  ...         5.5        42.5                                                                                                                                    |           |
|                     |          | 3061  2026-09-24 01:34 UTC    2026                                                                                                                                                                       |           |
| record picks        | ok       | run_at  season  week  ... spread_edge total_edge  p_cover                                                                                                                                                |       0.1 |
|                     |          | 0  2026-09-24 01:34 UTC    2026     3  ...        4.64      -0.09    0.652                                                                                                                               |           |
|                     |          | 1  2026-09-24 01:34 UTC    2026     3  ...                                                                                                                                                               |           |
| inputs fingerprint  | ok       | {'season': 2026, 'week': 3, 'starters': {'2026_03_ATL_GB': ['00-0036264', '00-0039917', '2026-09-24 20:15'], '2026_03_LAC_BUF': ['00-0034857', '00-0036355', '2026-09-27 13:00'], '2026_03_CAR_CLE': ['0 |       0.1 |
| grade               | ok       |                                                                                                                                                                                                          |       0.2 |
| tie check (sources) | ok       | True                                                                                                                                                                                                     |       0.5 |
| export data room    | ok       |                                                                                                                                                                                                          |      73   |
| tie check (page)    | ok       | True                                                                                                                                                                                                     |       1.7 |
| audit reports       | ok       | Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).                                       |       0.8 |
| legitimacy tests    | ok       | Reading: the line beats the model on the miss every season (it should; it is the market). The question the flag rests on is whether the model's disagreements with the line carry information, which the |      21.3 |

## Week 3, 2026: 3 flagged of 16 games

| away_team   | home_team   |   away_exp |   home_exp |   spread_line |   total_line |   spread_edge |   total_edge | bet       |   stake_pct |
|:------------|:------------|-----------:|-----------:|--------------:|-------------:|--------------:|-------------:|:----------|------------:|
| KC          | MIA         |      27.58 |      20.72 |         -11.5 |         46.5 |          4.64 |        -0.09 | MIA +11.5 |        0.89 |
| TEN         | NYG         |      18.09 |      25.2  |           3   |         39.5 |          4.11 |         3.8  | NYG -3    |        2.14 |
| CIN         | PIT         |      22.72 |      23.55 |          -3.5 |         42.5 |          4.33 |         4.26 | PIT +3.5  |        1.48 |

Full table: reports/picks_2026_wk3.md

## Track record

## Rules compared

The flag is bet; the shadows are logged and graded on the same games but never bet, so the rule can be chosen on live results.

Backtest columns: the same rule on the three backtest windows, regular season weeks 1 to 17 (`picks.rule_records`).

| Rule | Bets | Settled | Record | Units | Avg CLV | Backtest 2015-18 | Backtest 2019-22 | Backtest 2023-25 |
|---|---|---|---|---|---|---|---|---|
| 4+ edge (the flag, bet) | 3 | 0 | nothing settled |  | +0.00 | 62-57 | 86-60 | 42-24 |
| shadow: 4.5+ edge | 1 | 0 | nothing settled |  | +0.00 | 41-44 | 62-37 | 25-15 |
| shadow: 4+ edge, model's side the underdog or pick'em | 2 | 0 | nothing settled |  | +0.00 | 45-35 | 76-46 | 32-19 |
| shadow: 4+ edge, weeks 1 to 13 only | 3 | 0 | nothing settled |  | +0.00 | 47-42 | 71-44 | 31-19 |

Full record: reports/track_record.md
