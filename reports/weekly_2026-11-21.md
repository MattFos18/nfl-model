# Weekly run, 2026-11-21 20:19 UTC

## Steps

| step                           | status   | detail                                                                                                                                                                                                   |   seconds |
|:-------------------------------|:---------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------:|
| pull                           | ok       | [('2026-11-21T20:19:50', 'schedules', 'all', 'https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv', 'ok', 2191359, 'd1260c9c194f'), ('2026-11-21T20:19:50', 'players', 'all' |       5.8 |
| pull player history            | ok       | [('2026-11-21T20:19:56', 'pfr_advstats', 2018, 'https://github.com/nflverse/nflverse-data/releases/download/pfr_advstats/advstats_week_def_2018.parquet', 'cached', 149299, ''), ('2026-11-21T20:19:56', |       0   |
| build                          | ok       | team_games (8202, 142)                                                                                                                                                                                   |     117   |
| features                       | ok       | [40 rows x 8 columns]                                                                                                                                                                                    |       9.9 |
| snap exposure                  | ok       | snap exposure (338652, 10) seasons 2013 to 2026                                                                                                                                                          |       1.1 |
| verify                         | ok       | Result: PASS                                                                                                                                                                                             |       0.3 |
| data checks                    | ok       | True                                                                                                                                                                                                     |       0.3 |
| weather                        | ok       | game_id          kickoff_et  ...  precip        fetched_at                                                                                                                                               |       0.6 |
|                                |          | 0   2026_11_MIA_BUF 2026-11-22 13:00:00  ...     0.0  2026-11-21 15:22                                                                                                                                   |           |
|                                |          | 1   2026_11_BAL_CAR 2026-11-22 13:00:00  ...     0.0  2026                                                                                                                                               |           |
| wind forecast                  | ok       | 8                                                                                                                                                                                                        |       7.6 |
| lines                          | ok       | {'ts': '2026-11-21T20-22-13Z', 'season': 2026, 'week': 10, 'rows': 12, 'errors': 'oddsapi: 401 Client Error: Unauthorized for url: https://api.the-odds-api.com/v4/sports/americanfootball_nfl/odds?regi |      12.3 |
| live results                   | ok       | live results: week 11, 1 final of 13, 0 in progress; spread 0-0, total 0-0, winner 0-0; play-by-play for 15 games                                                                                        |       4.4 |
| ratings                        | ok       | (7668, 51) QB-out check: ok; swaps: none                                                                                                                                                                 |      17.8 |
| trends                         | ok       | head-to-head cover margin      96                 0.355         7.079            2.793                                                                                                                   |      40.6 |
| players                        | ok       | max           0.104589         1.360481    14.000000                                                                                                                                                     |      87.8 |
| positions                      | ok       | Skill    503.0  0.007822  0.00240  0.0867                                                                                                                                                                |      18.7 |
| scheme                         | ok       | scheme_plays (367336, 83) profiles for 32 teams as of 2026 11                                                                                                                                            |       4.7 |
| player splits                  | ok       | player_splits.js 1.82 MB                                                                                                                                                                                 |      58.7 |
| week moved mid-run             | ok       | (2026, 10) -> (2026, 11): input steps run again                                                                                                                                                          |       0   |
| ratings (again, week 11)       | ok       | (7668, 51) QB-out check: ok; swaps: ARI Gardner Minshew -> Josh Johnson (depth chart)                                                                                                                    |      18   |
| trends (again, week 11)        | ok       | head-to-head cover margin      96                 0.355         7.079            2.793                                                                                                                   |      40.7 |
| players (again, week 11)       | ok       | max           0.104589         1.360481    14.000000                                                                                                                                                     |      88.7 |
| positions (again, week 11)     | ok       | Skill    478.0  0.007682  0.00275  0.0684                                                                                                                                                                |      18   |
| scheme (again, week 11)        | ok       | scheme_plays (367336, 83) profiles for 32 teams as of 2026 11                                                                                                                                            |       4.7 |
| player splits (again, week 11) | ok       | player_splits.js 1.82 MB                                                                                                                                                                                 |      59.8 |
| model                          | ok       | opp_skill_out_value           12.498       0.012          0.156                                                                                                                                          |      37.6 |
| qt shadow                      | ok       | qt shadow: 3300 games, 16631 Questionable listings priced, 46s                                                                                                                                           |      47.2 |
| opener study                   | ok       | opener study written                                                                                                                                                                                     |      37.5 |
| props by season                | ok       | DONE                                                                                                                                                                                                     |      19.7 |
| props                          | error    | RuntimeError: on_upcast=True)                                                                                                                                                                            |       0.4 |
|                                |          |          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^                                                                                                                                        |           |
|                                |          |   File "/opt/hostedtoolcache/Python/3.11.18/x64/lib/python3.11/site-packages/pandas/core/internals/blocks.py", line 48                                                                                   |           |
| sizing backtest                | ok       | 2025   14-6    0.700        6.73                                                                                                                                                                         |       3.6 |
| threshold sweep                | ok       | DONE                                                                                                                                                                                                     |       1.2 |
| calibration start              | ok       | last 5 seasons     0.5288     0.5359     0.5429              0.69326            0.25006                0.68250              0.5639             0.5851             94              0.69274                |       1.2 |
| season backtest                | ok       | {'shrink0.1_sig1': 'not adopted', 'shrink0.1_sig1.15': 'not adopted', 'shrink0.2_sig1': 'not adopted', 'shrink0.2_sig1.15': 'not adopted', 'shrink0.3_sig1': 'not adopted', 'shrink0.3_sig1.15': 'not ad |      66.9 |
| legitimacy tests               | ok       | Reading: the line beats the model on the miss every season (it should; it is the market). The question the flag rests on is whether the model's disagreements with the line carry information, which the |      11.4 |
| audit reports                  | ok       | Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).                                       |       1.9 |
| picks                          | ok       | game_id  season  week  ...     bet_p  bet_odds  stake_pct                                                                                                                                                |       0.8 |
|                                |          | 3178  2026_11_IND_HOU    2026    11  ...  0.559990    -110.0       1.90                                                                                                                                  |           |
|                                |          | 3179  2026_11_MIA_BUF    2026    11  ...       NaN                                                                                                                                                       |           |
| log run                        | ok       | run_at  season  ...  total_line        bet                                                                                                                                                               |       0   |
|                                |          | 3178  2026-11-21 20:19 UTC    2026  ...        44.5  IND +12.5                                                                                                                                           |           |
|                                |          | 3179  2026-11-21 20:19 UTC    2026  ...        44.5                                                                                                                                                      |           |
|                                |          | 3180  2026-                                                                                                                                                                                              |           |
| record picks                   | ok       | run_at  season  week  ...  spread_edge  total_edge  p_cover                                                                                                                                              |       0.4 |
|                                |          | 0  2026-10-04 12:37 UTC    2026     4  ...         5.08        2.49    0.673                                                                                                                             |           |
|                                |          | 1  2026-10-04 16:01 UTC    2026     4  ...                                                                                                                                                               |           |
| inputs fingerprint             | ok       | {'season': 2026, 'week': 11, 'starters': {'2026_11_IND_HOU': ['00-0039163', '00-0035710', '2026-11-19 20:15'], '2026_11_MIA_BUF': ['00-0034857', '00-0040014', '2026-11-22 13:00'], '2026_11_BAL_CAR': [ |       0.5 |
| grade                          | ok       |                                                                                                                                                                                                          |       5.7 |
| closing line value             | ok       | CLV 2026: 50 closed, 11 pending, avg +0.03 pts, 22% beat the close                                                                                                                                       |       0.8 |
| forecast history               | ok       | 8 games fetched in 2s, 2235 stored, 0 left                                                                                                                                                               |       2.5 |
| drift monitor                  | ok       | **0 alerts, 0 to watch.** Long run = 2015 to 2024; recent = 2025 and 2026 so far. ALERT at |z| >= 2.5 or a CUSUM trip (h 5); WATCH at |z| >= 2.0.                                                        |       0.4 |
| shadow watch                   | ok       | **0 rules ready for a look.** READY = 30+ settled live bets, a win rate past break-even beyond luck (p <= 0.1) and 5+ points more return per unit risked than the rule it would replace over the same se |       0.8 |
| ready checks                   | ok       | **1 ready.** Each READY row opens a GitHub issue labelled ready-check (once per title).                                                                                                                  |       0.3 |
| tie check (sources)            | error    | RuntimeError: numbers disagree: see reports/tie_check.md                                                                                                                                                 |       2.5 |
| export data room               | ok       |                                                                                                                                                                                                          |      84.1 |
| tie check (page)               | error    | RuntimeError: page files disagree with the sources: see reports/tie_check.md                                                                                                                             |       7.1 |
| standing checks                | ok       | True                                                                                                                                                                                                     |      28.2 |

**Failed steps above were skipped, not filled with stale data.**

## Week 11, 2026: 2 flagged of 13 games

| away_team   | home_team   |   away_exp |   home_exp |   spread_line |   total_line |   spread_edge |   total_edge | bet       |   stake_pct |
|:------------|:------------|-----------:|-----------:|--------------:|-------------:|--------------:|-------------:|:----------|------------:|
| IND         | HOU         |      18.78 |      25.89 |          12.5 |         44.5 |         -5.39 |         0.17 | IND +12.5 |        1.9  |
| NO          | CHI         |      15.89 |      22.86 |          11.5 |         48.5 |         -4.53 |        -9.75 | NO +11.5  |        1.11 |

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
