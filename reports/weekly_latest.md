# Weekly run, 2026-09-24 00:27 UTC

## Steps

| step                | status   | detail                                                                                                                                                                                                   |   seconds |
|:--------------------|:---------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------:|
| pull                | ok       | [('2026-09-24T00:27:05', 'schedules', 'all', 'https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv', 'ok', 2180727, 'a04722e4027f'), ('2026-09-24T00:27:05', 'pbp', 2025, 'ht |       3   |
| build               | ok       | team_games (8202, 142)                                                                                                                                                                                   |     177   |
| features            | ok       | [40 rows x 8 columns]                                                                                                                                                                                    |      11.5 |
| verify              | ok       | Result: PASS                                                                                                                                                                                             |       0.4 |
| weather             | ok       | game_id          kickoff_et  ... precip        fetched_at                                                                                                                                                |       2.2 |
|                     |          | 0    2026_03_ATL_GB 2026-09-24 20:15:00  ...    0.0  2026-09-23 20:30                                                                                                                                    |           |
|                     |          | 1   2026_03_LAC_BUF 2026-09-27 13:00:00  ...    0.0  2026-09                                                                                                                                             |           |
| lines               | ok       | {'ts': '2026-09-24T00-30-19Z', 'season': 2026, 'week': 3, 'rows': 16, 'errors': "draftkings: sportsbook.draftkings.com: 403 Client Error: Forbidden for url: https://sportsbook.draf | sportsbook-nash.d |       1.5 |
| ratings             | ok       | (7668, 49)                                                                                                                                                                                               |      19.1 |
| trends              | ok       | head-to-head cover margin      96                 0.355         7.079            2.793                                                                                                                   |      47.7 |
| players             | ok       | max           0.104502         1.357485    14.000000                                                                                                                                                     |     112.5 |
| positions           | ok       | Skill    525.0  0.004309  0.0008  0.0531                                                                                                                                                                 |      10.5 |
| scheme              | ok       | scheme_plays (348655, 77) profiles for 32 teams as of 2026 3                                                                                                                                             |       4.8 |
| props               | ok       | props 2854 projections for week 3 graded rows 0 market lines on the cards 369 graded against the market 0                                                                                                |      14.7 |
| model               | ok       | neutral            0.074       0.133          0.010                                                                                                                                                      |      16.6 |
| picks               | ok       | game_id  season  week  ...     bet_p bet_odds stake_pct                                                                                                                                                  |       0.2 |
|                     |          | 3060   2026_03_ATL_GB    2026     3  ...       NaN      NaN       NaN                                                                                                                                    |           |
|                     |          | 3061  2026_03_LAC_BUF    2026     3  ...       NaN      NaN                                                                                                                                              |           |
| log run             | ok       | run_at  season  week  ... spread_line  total_line        bet                                                                                                                                             |       0   |
|                     |          | 3060  2026-09-24 00:27 UTC    2026     3  ...         5.5        42.5                                                                                                                                    |           |
|                     |          | 3061  2026-09-24 00:27 UTC    2026                                                                                                                                                                       |           |
| record picks        | ok       | run_at  season  week  ... spread_edge total_edge  p_cover                                                                                                                                                |       0.1 |
|                     |          | 0  2026-09-24 00:27 UTC    2026     3  ...        4.88      -0.55    0.659                                                                                                                               |           |
|                     |          | 1  2026-09-24 00:27 UTC    2026     3  ...                                                                                                                                                               |           |
| inputs fingerprint  | ok       | {'season': 2026, 'week': 3, 'starters': {'2026_03_ATL_GB': ['00-0036264', '00-0039917', '2026-09-24 20:15'], '2026_03_LAC_BUF': ['00-0034857', '00-0036355', '2026-09-27 13:00'], '2026_03_CAR_CLE': ['0 |       0   |
| grade               | ok       |                                                                                                                                                                                                          |       0.2 |
| tie check (sources) | ok       | True                                                                                                                                                                                                     |       0.3 |
| export data room    | ok       |                                                                                                                                                                                                          |      24   |
| tie check (page)    | ok       | True                                                                                                                                                                                                     |       1   |
| audit reports       | ok       | Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).                                       |       0.6 |
| legitimacy tests    | ok       | Reading: the line beats the model on the miss every season (it should; it is the market). The question the flag rests on is whether the model's disagreements with the line carry information, which the |      12.7 |

## Week 3, 2026: 3 flagged of 16 games

| away_team   | home_team   |   away_exp |   home_exp |   spread_line |   total_line |   spread_edge |   total_edge | bet       |   stake_pct |
|:------------|:------------|-----------:|-----------:|--------------:|-------------:|--------------:|-------------:|:----------|------------:|
| KC          | MIA         |      27.15 |      20.52 |         -11.5 |         46.5 |          4.88 |        -0.55 | MIA +11.5 |        0.97 |
| TEN         | NYG         |      18.05 |      25.11 |           3   |         39.5 |          4.06 |         3.47 | NYG -3    |        0.47 |
| CIN         | PIT         |      22.56 |      23.43 |          -3.5 |         42.5 |          4.37 |         4.23 | PIT +3.5  |        0.66 |

Full table: reports/picks_2026_wk3.md

## Track record

## Rules compared

The flag is bet; the shadows are logged and graded on the same games but never bet, so the rule can be chosen on live results.

Backtest columns: the same rule on the three backtest windows, regular season weeks 1 to 17 (`picks.rule_records`).

| Rule | Bets | Settled | Record | Units | Avg CLV | Backtest 2015-18 | Backtest 2019-22 | Backtest 2023-25 |
|---|---|---|---|---|---|---|---|---|
| 4+ edge (the flag, bet) | 3 | 0 | nothing settled |  | +0.00 | 67-57 | 87-59 | 45-21 |
| shadow: 4.5+ edge | 1 | 0 | nothing settled |  | +0.00 | 41-42 | 65-44 | 32-15 |
| shadow: 4+ edge, model's side the underdog or pick'em | 2 | 0 | nothing settled |  | +0.00 | 49-36 | 78-45 | 34-17 |
| shadow: 4+ edge, weeks 1 to 13 only | 3 | 0 | nothing settled |  | +0.00 | 54-42 | 71-41 | 34-16 |

Full record: reports/track_record.md
