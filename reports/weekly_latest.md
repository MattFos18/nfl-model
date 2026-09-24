# Weekly run, 2026-09-24 09:14 UTC

## Steps

| step                | status   | detail                                                                                                                                                                                                   |   seconds |
|:--------------------|:---------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------:|
| pull                | ok       | [('2026-09-24T09:14:38', 'schedules', 'all', 'https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv', 'ok', 2180807, '9d3644487c60'), ('2026-09-24T09:14:38', 'pbp', 2025, 'ht |       8.9 |
| pull player history | ok       | [('2026-09-24T09:14:47', 'pfr_advstats', 2018, 'https://github.com/nflverse/nflverse-data/releases/download/pfr_advstats/advstats_week_def_2018.parquet', 'ok', 149299, '8606f428d500'), ('2026-09-24T09 |      14.2 |
| build               | ok       | team_games (8202, 142)                                                                                                                                                                                   |     178.3 |
| features            | ok       | [40 rows x 8 columns]                                                                                                                                                                                    |      11.4 |
| verify              | ok       | Result: PASS                                                                                                                                                                                             |       0.4 |
| weather             | ok       | game_id          kickoff_et  ... precip        fetched_at                                                                                                                                                |     126.8 |
|                     |          | 0    2026_03_ATL_GB 2026-09-24 20:15:00  ...    0.0  2026-09-24 05:18                                                                                                                                    |           |
|                     |          | 1   2026_03_LAC_BUF 2026-09-27 13:00:00  ...    0.0  2026-09                                                                                                                                             |           |
| lines               | ok       | {'ts': '2026-09-24T09-20-18Z', 'season': 2026, 'week': 3, 'rows': 16, 'errors': 'draftkings: sportsbook.draftkings.com: 403 Client Error: Forbidden for url: https://sportsbook.draf | sportsbook-nash.d |       2   |
| ratings             | ok       | (7668, 49)                                                                                                                                                                                               |      19.7 |
| trends              | ok       | head-to-head cover margin      96                 0.355         7.079            2.793                                                                                                                   |      48   |
| players             | ok       | max           0.104589         1.360481    14.000000                                                                                                                                                     |     107.5 |
| positions           | ok       | Skill    527.0  0.004299  0.0008  0.0531                                                                                                                                                                 |      10.7 |
| scheme              | ok       | scheme_plays (352459, 83) profiles for 32 teams as of 2026 3                                                                                                                                             |       5   |
| props               | ok       | props 2874 projections for week 3 graded rows 0 market lines on the cards 367 graded against the market 0                                                                                                |      15.3 |
| model               | ok       | neutral            0.088       0.133          0.012                                                                                                                                                      |      16.8 |
| picks               | ok       | game_id  season  week  ...     bet_p bet_odds stake_pct                                                                                                                                                  |       0.3 |
|                     |          | 3060   2026_03_ATL_GB    2026     3  ...       NaN      NaN       NaN                                                                                                                                    |           |
|                     |          | 3061  2026_03_LAC_BUF    2026     3  ...       NaN      NaN                                                                                                                                              |           |
| log run             | ok       | run_at  season  week  ... spread_line  total_line        bet                                                                                                                                             |       0   |
|                     |          | 3060  2026-09-24 09:14 UTC    2026     3  ...         4.5        42.5                                                                                                                                    |           |
|                     |          | 3061  2026-09-24 09:14 UTC    2026                                                                                                                                                                       |           |
| record picks        | ok       | run_at  season  week  ... spread_edge total_edge  p_cover                                                                                                                                                |       0.1 |
|                     |          | 0  2026-09-24 09:14 UTC    2026     3  ...        4.24       0.24    0.655                                                                                                                               |           |
|                     |          |                                                                                                                                                                                                          |           |
|                     |          | [1 rows x 12 columns]                                                                                                                                                                                    |           |
| inputs fingerprint  | ok       | {'season': 2026, 'week': 3, 'starters': {'2026_03_ATL_GB': ['00-0036264', '00-0039917', '2026-09-24 20:15'], '2026_03_LAC_BUF': ['00-0034857', '00-0036355', '2026-09-27 13:00'], '2026_03_CAR_CLE': ['0 |       0   |
| grade               | ok       |                                                                                                                                                                                                          |       0.1 |
| tie check (sources) | ok       | True                                                                                                                                                                                                     |       0.3 |
| export data room    | ok       |                                                                                                                                                                                                          |      43.8 |
| tie check (page)    | ok       | True                                                                                                                                                                                                     |       1.2 |
| audit reports       | ok       | Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).                                       |       0.6 |
| legitimacy tests    | ok       | Reading: the line beats the model on the miss every season (it should; it is the market). The question the flag rests on is whether the model's disagreements with the line carry information, which the |      13   |

## Week 3, 2026: 1 flagged of 16 games

| away_team   | home_team   |   away_exp |   home_exp |   spread_line |   total_line |   spread_edge |   total_edge | bet       |   stake_pct |
|:------------|:------------|-----------:|-----------:|--------------:|-------------:|--------------:|-------------:|:----------|------------:|
| KC          | MIA         |      27.46 |      21.19 |         -10.5 |         46.5 |          4.24 |         0.24 | MIA +10.5 |        1.46 |

Full table: reports/picks_2026_wk3.md

## Track record

## Rules compared

The flag is bet; the shadows are logged and graded on the same games but never bet, so the rule can be chosen on live results.

Backtest columns: the same rule on the three backtest windows, regular season weeks 1 to 17 (`picks.rule_records`).

| Rule | Bets | Settled | Record | Units | Avg CLV | Backtest 2015-18 | Backtest 2019-22 | Backtest 2023-25 |
|---|---|---|---|---|---|---|---|---|
| 4+ edge (the flag, bet) | 1 | 0 | nothing settled |  | +0.00 | 61-59 | 81-56 | 41-21 |
| shadow: 4.5+ edge | 0 | 0 | | | | 39-40 | 55-36 | 28-14 |
| shadow: 4+ edge, model's side the underdog or pick'em | 1 | 0 | nothing settled |  | +0.00 | 45-37 | 73-44 | 33-16 |
| shadow: 4+ edge, weeks 1 to 13 only | 1 | 0 | nothing settled |  | +0.00 | 46-43 | 67-41 | 34-17 |

Full record: reports/track_record.md
