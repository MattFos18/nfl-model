# Weekly run, 2026-11-08 18:12 UTC

## Steps

| step                | status   | detail                                                                                                                                                                                                   |   seconds |
|:--------------------|:---------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------:|
| pull                | ok       | [('2026-11-08T18:12:26', 'schedules', 'all', 'https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv', 'ok', 2188890, 'b52022f946af'), ('2026-11-08T18:12:26', 'players', 'all' |      10.6 |
| pull player history | ok       | [('2026-11-08T18:12:37', 'pfr_advstats', 2018, 'https://github.com/nflverse/nflverse-data/releases/download/pfr_advstats/advstats_week_def_2018.parquet', 'cached', 149299, ''), ('2026-11-08T18:12:37', |       0   |
| build               | ok       | team_games (8202, 142)                                                                                                                                                                                   |     183.1 |
| features            | ok       | [40 rows x 8 columns]                                                                                                                                                                                    |      14.3 |
| snap exposure       | ok       | snap exposure (335941, 10) seasons 2013 to 2026                                                                                                                                                          |       1.6 |
| verify              | ok       | Result: PASS                                                                                                                                                                                             |       0.5 |
| data checks         | ok       | True                                                                                                                                                                                                     |       0.5 |
| weather             | ok       | game_id           kickoff_et  ...  precip        fetched_at                                                                                                                                              |      78.8 |
|                     |          | 0   2026_09_DEN_CAR  2026-11-08 13:00:00  ...     0.0  2026-11-08 13:15                                                                                                                                  |           |
|                     |          | 1    2026_09_NYJ_KC  2026-11-08 13:00:00  ...     0.0  2                                                                                                                                                 |           |
| wind forecast       | ok       | 4                                                                                                                                                                                                        |       3.5 |
| lines               | ok       | {'ts': '2026-11-08T18-17-19Z', 'season': 2026, 'week': 9, 'rows': 6, 'errors': 'oddsapi: 401 Client Error: Unauthorized for url: https://api.the-odds-api.com/v4/sports/americanfootball_nfl/odds?region |      76.3 |
| live results        | ok       | live results: week 9, 2 final of 15, 7 in progress; spread 0-2, total 2-0, winner 2-0; play-by-play for 9 games                                                                                          |       8.6 |
| ratings             | ok       | (7668, 51) QB-out check: ok; swaps: MIN Kyler Murray -> Carson Wentz (depth chart)                                                                                                                       |      32.6 |
| trends              | ok       | head-to-head cover margin      96                 0.355         7.079            2.793                                                                                                                   |      64.6 |
| players             | ok       | max           0.104589         1.360481    14.000000                                                                                                                                                     |     129.7 |
| positions           | ok       | Skill    531.0  0.007950  0.00260  0.0805                                                                                                                                                                |      26.9 |
| scheme              | ok       | scheme_plays (363752, 83) profiles for 32 teams as of 2026 9                                                                                                                                             |       6.9 |
| player splits       | ok       | player_splits.js 1.76 MB                                                                                                                                                                                 |      92.9 |
| model               | ok       | opp_skill_out_value           12.498       0.012          0.156                                                                                                                                          |      52.1 |
| qt shadow           | ok       | qt shadow: 3300 games, 16466 Questionable listings priced, 66s                                                                                                                                           |      67.3 |
| opener study        | ok       | opener study written                                                                                                                                                                                     |      52.5 |
| props by season     | ok       | DONE                                                                                                                                                                                                     |      28.6 |
| props               | error    | RuntimeError: on_upcast=True)                                                                                                                                                                            |       0.6 |
|                     |          |          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^                                                                                                                                        |           |
|                     |          |   File "/opt/hostedtoolcache/Python/3.11.18/x64/lib/python3.11/site-packages/pandas/core/internals/blocks.py", line 48                                                                                   |           |
| sizing backtest     | ok       | 2025   14-6    0.700        6.73                                                                                                                                                                         |       5.2 |
| threshold sweep     | ok       | DONE                                                                                                                                                                                                     |       1.6 |
| calibration start   | ok       | last 5 seasons     0.5288     0.5359     0.5429              0.69326            0.25006                0.68250              0.5639             0.5851             94              0.69274                |       1.6 |
| season backtest     | ok       | {'shrink0.1_sig1': 'not adopted', 'shrink0.1_sig1.15': 'not adopted', 'shrink0.2_sig1': 'not adopted', 'shrink0.2_sig1.15': 'not adopted', 'shrink0.3_sig1': 'not adopted', 'shrink0.3_sig1.15': 'not ad |      95   |
| legitimacy tests    | ok       | Reading: the line beats the model on the miss every season (it should; it is the market). The question the flag rests on is whether the model's disagreements with the line carry information, which the |      16.4 |
| audit reports       | ok       | Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).                                       |       2.7 |
| picks               | ok       | game_id  season  week  ...     bet_p  bet_odds  stake_pct                                                                                                                                                |       1.2 |
|                     |          | 3149  2026_09_JAX_BAL    2026     9  ...       NaN       NaN        NaN                                                                                                                                  |           |
|                     |          | 3150  2026_09_CIN_ATL    2026     9  ...       NaN                                                                                                                                                       |           |
| log run             | ok       | run_at  season  ...  total_line       bet                                                                                                                                                                |       0   |
|                     |          | 3149  2026-11-08 18:12 UTC    2026  ...        39.5                                                                                                                                                      |           |
|                     |          | 3150  2026-11-08 18:12 UTC    2026  ...        52.5                                                                                                                                                      |           |
|                     |          | 3151  2026-11-                                                                                                                                                                                           |           |
| record picks        | ok       | run_at  season  week  ...  spread_edge  total_edge  p_cover                                                                                                                                              |       0.5 |
|                     |          | 0  2026-10-04 12:37 UTC    2026     4  ...         5.08        2.49    0.673                                                                                                                             |           |
|                     |          | 1  2026-10-04 16:01 UTC    2026     4  ...                                                                                                                                                               |           |
| inputs fingerprint  | ok       | {'season': 2026, 'week': 9, 'starters': {'2026_09_JAX_BAL': ['00-0040981', '00-0036971', '2026-11-05 20:15'], '2026_09_CIN_ATL': ['00-0039917', '00-0036442', '2026-11-08 09:30'], '2026_09_DEN_CAR': [' |       0.7 |
| grade               | ok       |                                                                                                                                                                                                          |       7.6 |
| closing line value  | ok       | CLV 2026: 40 closed, 4 pending, avg +0.04 pts, 22% beat the close                                                                                                                                        |       1.1 |
| forecast history    | ok       | complete: 2216 games stored                                                                                                                                                                              |       0   |
| drift monitor       | ok       | **0 alerts, 0 to watch.** Long run = 2015 to 2024; recent = 2025 and 2026 so far. ALERT at |z| >= 2.5 or a CUSUM trip (h 5); WATCH at |z| >= 2.0.                                                        |       0.5 |
| shadow watch        | ok       | **0 rules ready for a look.** READY = 30+ settled live bets, a win rate past break-even beyond luck (p <= 0.1) and 5+ points more return per unit risked than the rule it would replace over the same se |       1.1 |
| ready checks        | ok       | **0 ready.** Each READY row opens a GitHub issue labelled ready-check (once per title).                                                                                                                  |       0.4 |
| tie check (sources) | error    | RuntimeError: numbers disagree: see reports/tie_check.md                                                                                                                                                 |       4.2 |
| export data room    | ok       |                                                                                                                                                                                                          |     118.7 |
| tie check (page)    | error    | RuntimeError: page files disagree with the sources: see reports/tie_check.md                                                                                                                             |      10.6 |
| standing checks     | ok       | True                                                                                                                                                                                                     |      40.7 |

**Failed steps above were skipped, not filled with stale data.**

## Week 9, 2026: 3 flagged of 15 games

| away_team   | home_team   |   away_exp |   home_exp |   spread_line |   total_line |   spread_edge |   total_edge | bet      |   stake_pct |
|:------------|:------------|-----------:|-----------:|--------------:|-------------:|--------------:|-------------:|:---------|------------:|
| DAL         | IND         |      25.85 |      25.44 |          -4.5 |         51.5 |          4.09 |        -0.22 | IND +4.5 |        1.05 |
| HOU         | LAC         |      21.92 |      20.85 |          -5.5 |         40.5 |          4.42 |         2.27 | LAC +5.5 |        1.04 |
| LV          | SF          |      23.91 |      29.34 |           9.5 |         51.5 |         -4.07 |         1.76 | LV +9.5  |        1.04 |

Full table: reports/picks_2026_wk9.md

## Track record

## Rules compared

The flag is bet; the shadows are logged and graded on the same games but never bet, so the rule can be chosen on live results.

Backtest columns: the same rule on the three backtest windows, regular season weeks 1 to 17 (`picks.rule_records`).

| Rule | Bets | Settled | Record | Units | Avg CLV | Backtest 2015-18 | Backtest 2019-22 | Backtest 2023-25 |
|---|---|---|---|---|---|---|---|---|
| 4+ edge (the flag, bet) | 8 | 6 | 3-3 (50%) | -0.29 | +0.19 | 67-54 | 80-52 | 38-17 |
| shadow: 4.5+ edge | 5 | 5 | 2-3 (40%) | -1.21 | +0.30 | 46-36 | 55-39 | 23-15 |
| shadow: 4+ edge, model's side the underdog or pick'em | 8 | 6 | 3-3 (50%) | -0.29 | +0.19 | 52-37 | 72-43 | 30-14 |
| shadow: 4+ edge, weeks 1 to 13 only | 8 | 6 | 3-3 (50%) | -0.29 | +0.19 | 50-41 | 69-38 | 30-14 |

Full record: reports/track_record.md
