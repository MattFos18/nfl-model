# Weekly run, 2026-11-07 18:25 UTC

## Steps

| step                | status   | detail                                                                                                                                                                                                   |   seconds |
|:--------------------|:---------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------:|
| pull                | ok       | [('2026-11-07T18:25:49', 'schedules', 'all', 'https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv', 'ok', 2188941, 'ce23c5241f38'), ('2026-11-07T18:25:49', 'players', 'all' |       8.1 |
| pull player history | ok       | [('2026-11-07T18:25:58', 'pfr_advstats', 2018, 'https://github.com/nflverse/nflverse-data/releases/download/pfr_advstats/advstats_week_def_2018.parquet', 'cached', 149299, ''), ('2026-11-07T18:25:58', |       0   |
| build               | ok       | team_games (8202, 142)                                                                                                                                                                                   |      87.6 |
| features            | ok       | [40 rows x 8 columns]                                                                                                                                                                                    |       7.1 |
| snap exposure       | ok       | snap exposure (335941, 10) seasons 2013 to 2026                                                                                                                                                          |       1   |
| verify              | ok       | Result: PASS                                                                                                                                                                                             |       0.3 |
| data checks         | ok       | True                                                                                                                                                                                                     |       0.3 |
| weather             | ok       | game_id          kickoff_et  ...  precip        fetched_at                                                                                                                                               |       6.8 |
|                     |          | 0   2026_09_DEN_CAR 2026-11-08 13:00:00  ...     0.0  2026-11-07 13:27                                                                                                                                   |           |
|                     |          | 1    2026_09_NYJ_KC 2026-11-08 13:00:00  ...     0.0  2026                                                                                                                                               |           |
| wind forecast       | ok       | 9                                                                                                                                                                                                        |       6.1 |
| lines               | ok       | {'ts': '2026-11-07T18-27-47Z', 'season': 2026, 'week': 9, 'rows': 14, 'errors': 'oddsapi: 401 Client Error: Unauthorized for url: https://api.the-odds-api.com/v4/sports/americanfootball_nfl/odds?regio |     115.3 |
| live results        | ok       | live results: week 9, 1 final of 15, 0 in progress; spread 0-1, total 1-0, winner 1-0; play-by-play for 1 games                                                                                          |       3.8 |
| ratings             | ok       | (7668, 51) QB-out check: ok; swaps: none                                                                                                                                                                 |      13.9 |
| trends              | ok       | head-to-head cover margin      96                 0.355         7.079            2.793                                                                                                                   |      29.2 |
| players             | ok       | max           0.104589         1.360481    14.000000                                                                                                                                                     |      64.2 |
| positions           | ok       | Skill    531.0  0.007950  0.00260  0.0805                                                                                                                                                                |      14.2 |
| scheme              | ok       | scheme_plays (363752, 83) profiles for 32 teams as of 2026 9                                                                                                                                             |       3.4 |
| player splits       | ok       | player_splits.js 1.76 MB                                                                                                                                                                                 |      41.1 |
| model               | ok       | opp_skill_out_value           12.498       0.012          0.156                                                                                                                                          |      30.3 |
| qt shadow           | ok       | qt shadow: 3300 games, 16486 Questionable listings priced, 34s                                                                                                                                           |      34.7 |
| opener study        | ok       | opener study written                                                                                                                                                                                     |      29.9 |
| props by season     | ok       | DONE                                                                                                                                                                                                     |      15.5 |
| props               | error    | RuntimeError: on_upcast=True)                                                                                                                                                                            |       0.4 |
|                     |          |          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^                                                                                                                                        |           |
|                     |          |   File "/opt/hostedtoolcache/Python/3.11.18/x64/lib/python3.11/site-packages/pandas/core/internals/blocks.py", line 48                                                                                   |           |
| sizing backtest     | ok       | 2025   14-6    0.700        6.73                                                                                                                                                                         |       2.7 |
| threshold sweep     | ok       | DONE                                                                                                                                                                                                     |       1   |
| calibration start   | ok       | last 5 seasons     0.5288     0.5359     0.5429              0.69326            0.25006                0.68250              0.5639             0.5851             94              0.69274                |       1   |
| season backtest     | ok       | {'shrink0.1_sig1': 'not adopted', 'shrink0.1_sig1.15': 'not adopted', 'shrink0.2_sig1': 'not adopted', 'shrink0.2_sig1.15': 'not adopted', 'shrink0.3_sig1': 'not adopted', 'shrink0.3_sig1.15': 'not ad |      57   |
| legitimacy tests    | ok       | Reading: the line beats the model on the miss every season (it should; it is the market). The question the flag rests on is whether the model's disagreements with the line carry information, which the |       8.6 |
| audit reports       | ok       | Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).                                       |       1.5 |
| picks               | ok       | game_id  season  week  ...     bet_p  bet_odds  stake_pct                                                                                                                                                |       0.6 |
|                     |          | 3149  2026_09_JAX_BAL    2026     9  ...       NaN       NaN        NaN                                                                                                                                  |           |
|                     |          | 3150  2026_09_CIN_ATL    2026     9  ...       NaN                                                                                                                                                       |           |
| log run             | ok       | run_at  season  week  ...  spread_line  total_line     bet                                                                                                                                               |       0   |
|                     |          | 3149  2026-11-07 18:25 UTC    2026     9  ...        -10.0        39.5                                                                                                                                   |           |
|                     |          | 3150  2026-11-07 18:25 UTC    2026     9                                                                                                                                                                 |           |
| record picks        | ok       | run_at  season  week  ...  spread_edge  total_edge  p_cover                                                                                                                                              |       0.3 |
|                     |          | 0  2026-10-04 12:37 UTC    2026     4  ...         5.08        2.49    0.673                                                                                                                             |           |
|                     |          | 1  2026-10-04 16:01 UTC    2026     4  ...                                                                                                                                                               |           |
| inputs fingerprint  | ok       | {'season': 2026, 'week': 9, 'starters': {'2026_09_JAX_BAL': ['00-0040981', '00-0036971', '2026-11-05 20:15'], '2026_09_CIN_ATL': ['00-0039917', '00-0036442', '2026-11-08 09:30'], '2026_09_DEN_CAR': [' |       0.4 |
| grade               | ok       |                                                                                                                                                                                                          |       4.7 |
| closing line value  | ok       | CLV 2026: 37 closed, 7 pending, avg +0.04 pts, 24% beat the close                                                                                                                                        |       0.6 |
| forecast history    | ok       | 1 games fetched in 1s, 2216 stored, 0 left                                                                                                                                                               |       1.1 |
| drift monitor       | ok       | **0 alerts, 0 to watch.** Long run = 2015 to 2024; recent = 2025 and 2026 so far. ALERT at |z| >= 2.5 or a CUSUM trip (h 5); WATCH at |z| >= 2.0.                                                        |       0.3 |
| shadow watch        | ok       | **0 rules ready for a look.** READY = 30+ settled live bets, a win rate past break-even beyond luck (p <= 0.1) and 5+ points more return per unit risked than the rule it would replace over the same se |       0.7 |
| ready checks        | ok       | **0 ready.** Each READY row opens a GitHub issue labelled ready-check (once per title).                                                                                                                  |       0.3 |
| tie check (sources) | error    | RuntimeError: numbers disagree: see reports/tie_check.md                                                                                                                                                 |       2.2 |
| export data room    | ok       |                                                                                                                                                                                                          |      62.7 |
| tie check (page)    | error    | RuntimeError: page files disagree with the sources: see reports/tie_check.md                                                                                                                             |       6   |
| standing checks     | ok       | True                                                                                                                                                                                                     |      22.6 |

**Failed steps above were skipped, not filled with stale data.**

## Week 9, 2026: 2 flagged of 15 games

| away_team   | home_team   |   away_exp |   home_exp |   spread_line |   total_line |   spread_edge |   total_edge | bet    |   stake_pct |
|:------------|:------------|-----------:|-----------:|--------------:|-------------:|--------------:|-------------:|:-------|------------:|
| HOU         | LAC         |      21.92 |      20.85 |            -6 |         40.5 |          4.92 |         2.27 | LAC +6 |        1.37 |
| LV          | SF          |      23.91 |      29.34 |            10 |         51.5 |         -4.57 |         1.76 | LV +10 |        0.8  |

Full table: reports/picks_2026_wk9.md

## Track record

## Rules compared

The flag is bet; the shadows are logged and graded on the same games but never bet, so the rule can be chosen on live results.

Backtest columns: the same rule on the three backtest windows, regular season weeks 1 to 17 (`picks.rule_records`).

| Rule | Bets | Settled | Record | Units | Avg CLV | Backtest 2015-18 | Backtest 2019-22 | Backtest 2023-25 |
|---|---|---|---|---|---|---|---|---|
| 4+ edge (the flag, bet) | 8 | 6 | 3-3 (50%) | -0.29 | +0.19 | 67-54 | 80-52 | 38-17 |
| shadow: 4.5+ edge | 7 | 5 | 2-3 (40%) | -1.21 | +0.21 | 46-36 | 55-39 | 23-15 |
| shadow: 4+ edge, model's side the underdog or pick'em | 8 | 6 | 3-3 (50%) | -0.29 | +0.19 | 52-37 | 72-43 | 30-14 |
| shadow: 4+ edge, weeks 1 to 13 only | 8 | 6 | 3-3 (50%) | -0.29 | +0.19 | 50-41 | 69-38 | 30-14 |

Full record: reports/track_record.md
