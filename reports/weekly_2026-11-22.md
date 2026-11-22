# Weekly run, 2026-11-22 20:06 UTC

## Steps

| step                | status   | detail                                                                                                                                                                                                   |   seconds |
|:--------------------|:---------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------:|
| pull                | ok       | [('2026-11-22T20:06:34', 'schedules', 'all', 'https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv', 'ok', 2190910, 'ad4e8b852ce9'), ('2026-11-22T20:06:34', 'players', 'all' |       5.7 |
| pull player history | ok       | [('2026-11-22T20:06:40', 'pfr_advstats', 2018, 'https://github.com/nflverse/nflverse-data/releases/download/pfr_advstats/advstats_week_def_2018.parquet', 'cached', 149299, ''), ('2026-11-22T20:06:40', |       0   |
| build               | ok       | team_games (8202, 142)                                                                                                                                                                                   |     128   |
| features            | ok       | [40 rows x 8 columns]                                                                                                                                                                                    |       9.5 |
| snap exposure       | ok       | snap exposure (338652, 10) seasons 2013 to 2026                                                                                                                                                          |       1.3 |
| verify              | ok       | Result: PASS                                                                                                                                                                                             |       0.4 |
| data checks         | ok       | True                                                                                                                                                                                                     |       0.4 |
| weather             | ok       | game_id          kickoff_et  ...  precip        fetched_at                                                                                                                                               |       2.4 |
|                     |          | 0   2026_11_MIA_BUF 2026-11-22 13:00:00  ...     0.0  2026-11-22 15:08                                                                                                                                   |           |
|                     |          | 1   2026_11_BAL_CAR 2026-11-22 13:00:00  ...     0.0  2026                                                                                                                                               |           |
| wind forecast       | ok       | 3                                                                                                                                                                                                        |       1.9 |
| lines               | ok       | {'ts': '2026-11-22T20-09-04Z', 'season': 2026, 'week': 11, 'rows': 5, 'errors': 'oddsapi: 401 Client Error: Unauthorized for url: https://api.the-odds-api.com/v4/sports/americanfootball_nfl/odds?regio |       5.4 |
| live results        | ok       | live results: week 11, 1 final of 13, 7 in progress; spread 0-1, total 0-1, winner 1-0; play-by-play for 8 games                                                                                         |       7   |
| ratings             | ok       | (7668, 51) QB-out check: ok; swaps: none                                                                                                                                                                 |      21.4 |
| trends              | ok       | head-to-head cover margin      96                 0.355         7.079            2.793                                                                                                                   |      47.6 |
| players             | ok       | max           0.104589         1.360481    14.000000                                                                                                                                                     |      94.3 |
| positions           | ok       | Skill    478.0  0.007682  0.00275  0.0684                                                                                                                                                                |      18.1 |
| scheme              | ok       | scheme_plays (367336, 83) profiles for 32 teams as of 2026 11                                                                                                                                            |       5   |
| player splits       | ok       | player_splits.js 1.82 MB                                                                                                                                                                                 |      65.7 |
| model               | ok       | opp_skill_out_value           12.498       0.012          0.156                                                                                                                                          |      38.2 |
| qt shadow           | ok       | qt shadow: 3300 games, 16628 Questionable listings priced, 49s                                                                                                                                           |      49.8 |
| opener study        | ok       | opener study written                                                                                                                                                                                     |      38.1 |
| props by season     | ok       | DONE                                                                                                                                                                                                     |      21.7 |
| props               | error    | RuntimeError: on_upcast=True)                                                                                                                                                                            |       0.5 |
|                     |          |          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^                                                                                                                                        |           |
|                     |          |   File "/opt/hostedtoolcache/Python/3.11.18/x64/lib/python3.11/site-packages/pandas/core/internals/blocks.py", line 48                                                                                   |           |
| sizing backtest     | ok       | 2025   14-6    0.700        6.73                                                                                                                                                                         |       3.8 |
| threshold sweep     | ok       | DONE                                                                                                                                                                                                     |       1.2 |
| calibration start   | ok       | last 5 seasons     0.5288     0.5359     0.5429              0.69326            0.25006                0.68250              0.5639             0.5851             94              0.69274                |       1.3 |
| season backtest     | ok       | {'shrink0.1_sig1': 'not adopted', 'shrink0.1_sig1.15': 'not adopted', 'shrink0.2_sig1': 'not adopted', 'shrink0.2_sig1.15': 'not adopted', 'shrink0.3_sig1': 'not adopted', 'shrink0.3_sig1.15': 'not ad |      77.2 |
| legitimacy tests    | ok       | Reading: the line beats the model on the miss every season (it should; it is the market). The question the flag rests on is whether the model's disagreements with the line carry information, which the |      12   |
| audit reports       | ok       | Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).                                       |       2   |
| picks               | ok       | game_id  season  week  ...     bet_p  bet_odds  stake_pct                                                                                                                                                |       0.9 |
|                     |          | 3178  2026_11_IND_HOU    2026    11  ...  0.558892    -110.0       1.84                                                                                                                                  |           |
|                     |          | 3179  2026_11_MIA_BUF    2026    11  ...       NaN                                                                                                                                                       |           |
| log run             | ok       | run_at  season  ...  total_line        bet                                                                                                                                                               |       0   |
|                     |          | 3178  2026-11-22 20:06 UTC    2026  ...        44.5  IND +12.5                                                                                                                                           |           |
|                     |          | 3179  2026-11-22 20:06 UTC    2026  ...        44.5                                                                                                                                                      |           |
|                     |          | 3180  2026-                                                                                                                                                                                              |           |
| record picks        | ok       | run_at season week  ... spread_edge total_edge p_cover                                                                                                                                                   |       0.4 |
|                     |          | 0  2026-10-04 12:37 UTC   2026    4  ...        5.08       2.49   0.673                                                                                                                                  |           |
|                     |          | 1  2026-10-04 16:01 UTC   2026    4  ...       -4.87                                                                                                                                                     |           |
| inputs fingerprint  | ok       | {'season': 2026, 'week': 11, 'starters': {'2026_11_IND_HOU': ['00-0039163', '00-0035710', '2026-11-19 20:15'], '2026_11_MIA_BUF': ['00-0034857', '00-0040014', '2026-11-22 13:00'], '2026_11_BAL_CAR': [ |       0.6 |
| grade               | ok       |                                                                                                                                                                                                          |       6.4 |
| closing line value  | ok       | CLV 2026: 58 closed, 2 pending, avg +0.03 pts, 19% beat the close                                                                                                                                        |       0.9 |
| forecast history    | ok       | complete: 2235 games stored                                                                                                                                                                              |       0   |
| drift monitor       | ok       | **0 alerts, 0 to watch.** Long run = 2015 to 2024; recent = 2025 and 2026 so far. ALERT at |z| >= 2.5 or a CUSUM trip (h 5); WATCH at |z| >= 2.0.                                                        |       0.4 |
| shadow watch        | ok       | **0 rules ready for a look.** READY = 30+ settled live bets, a win rate past break-even beyond luck (p <= 0.1) and 5+ points more return per unit risked than the rule it would replace over the same se |       0.9 |
| ready checks        | ok       | **1 ready.** Each READY row opens a GitHub issue labelled ready-check (once per title).                                                                                                                  |       0.3 |
| tie check (sources) | error    | RuntimeError: numbers disagree: see reports/tie_check.md                                                                                                                                                 |       2.6 |
| export data room    | ok       |                                                                                                                                                                                                          |      86   |
| tie check (page)    | error    | RuntimeError: page files disagree with the sources: see reports/tie_check.md                                                                                                                             |       7.6 |
| standing checks     | ok       | True                                                                                                                                                                                                     |      31.8 |

**Failed steps above were skipped, not filled with stale data.**

## Week 11, 2026: 2 flagged of 13 games

| away_team   | home_team   |   away_exp |   home_exp |   spread_line |   total_line |   spread_edge |   total_edge | bet       |   stake_pct |
|:------------|:------------|-----------:|-----------:|--------------:|-------------:|--------------:|-------------:|:----------|------------:|
| IND         | HOU         |      19.5  |      26.69 |          12.5 |         44.5 |         -5.3  |         1.69 | IND +12.5 |        1.84 |
| NO          | CHI         |      15.77 |      22.98 |          11.5 |         48.5 |         -4.29 |        -9.75 | NO +11.5  |        0.95 |

Full table: reports/picks_2026_wk11.md

## Track record

## Rules compared

The flag is bet; the shadows are logged and graded on the same games but never bet, so the rule can be chosen on live results.

Backtest columns: the same rule on the three backtest windows, regular season weeks 1 to 17 (`picks.rule_records`).

| Rule | Bets | Settled | Record | Units | Avg CLV | Backtest 2015-18 | Backtest 2019-22 | Backtest 2023-25 |
|---|---|---|---|---|---|---|---|---|
| 4+ edge (the flag, bet) | 10 | 9 | 3-6 (33%) | -3.29 | +0.35 | 67-54 | 80-52 | 38-17 |
| shadow: 4.5+ edge | 6 | 5 | 2-3 (40%) | -1.21 | +0.25 | 46-36 | 55-39 | 23-15 |
| shadow: 4+ edge, model's side the underdog or pick'em | 10 | 9 | 3-6 (33%) | -3.29 | +0.35 | 52-37 | 72-43 | 30-14 |
| shadow: 4+ edge, weeks 1 to 13 only | 10 | 9 | 3-6 (33%) | -3.29 | +0.35 | 50-41 | 69-38 | 30-14 |

Full record: reports/track_record.md
