# Weekly run, 2026-11-10 17:27 UTC

## Steps

| step                           | status   | detail                                                                                                                                                                                                   |   seconds |
|:-------------------------------|:---------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------:|
| pull                           | ok       | [('2026-11-10T17:27:41', 'schedules', 'all', 'https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv', 'ok', 2188990, '409ce8d561b7'), ('2026-11-10T17:27:41', 'players', 'all' |       8.7 |
| pull player history            | ok       | [('2026-11-10T17:27:50', 'pfr_advstats', 2018, 'https://github.com/nflverse/nflverse-data/releases/download/pfr_advstats/advstats_week_def_2018.parquet', 'cached', 149299, ''), ('2026-11-10T17:27:50', |       0   |
| build                          | ok       | team_games (8202, 142)                                                                                                                                                                                   |     157.4 |
| features                       | ok       | [40 rows x 8 columns]                                                                                                                                                                                    |      12.9 |
| snap exposure                  | ok       | snap exposure (337249, 10) seasons 2013 to 2026                                                                                                                                                          |       1.6 |
| verify                         | ok       | Result: PASS                                                                                                                                                                                             |       0.5 |
| data checks                    | ok       | True                                                                                                                                                                                                     |       0.4 |
| weather                        | ok       | game_id          kickoff_et  ...  precip        fetched_at                                                                                                                                               |       2.7 |
|                                |          | 0  2026_10_WAS_NYG 2026-11-12 20:15:00  ...     0.1  2026-11-10 12:30                                                                                                                                    |           |
|                                |          | 1   2026_10_NE_DET 2026-11-15 09:30:00  ...     0.0  2026-11                                                                                                                                             |           |
| wind forecast                  | ok       | 1                                                                                                                                                                                                        |       0.9 |
| lines                          | ok       | {'ts': '2026-11-10T17-30-47Z', 'season': 2026, 'week': 9, 'rows': 14, 'errors': 'oddsapi: 401 Client Error: Unauthorized for url: https://api.the-odds-api.com/v4/sports/americanfootball_nfl/odds?regio |       6   |
| live results                   | ok       | live results: week 9, 15 final of 15, 0 in progress; spread 7-8, total 9-6, winner 14-1; play-by-play for 15 games                                                                                       |       9.8 |
| ratings                        | ok       | (7668, 51) QB-out check: ok; swaps: none                                                                                                                                                                 |      27.6 |
| trends                         | ok       | head-to-head cover margin      96                 0.355         7.079            2.793                                                                                                                   |      54.2 |
| players                        | ok       | max           0.104589         1.360481    14.000000                                                                                                                                                     |     116   |
| positions                      | ok       | Skill    531.0  0.007950  0.00260  0.0805                                                                                                                                                                |      26.3 |
| scheme                         | ok       | scheme_plays (365492, 83) profiles for 32 teams as of 2026 10                                                                                                                                            |       6.2 |
| player splits                  | ok       | player_splits.js 1.79 MB                                                                                                                                                                                 |      78   |
| week moved mid-run             | ok       | (2026, 9) -> (2026, 10): input steps run again                                                                                                                                                           |       0   |
| ratings (again, week 10)       | ok       | (7668, 51) QB-out check: ok; swaps: ARI Gardner Minshew -> Carson Beck (depth chart); SEA Sam Darnold -> Drew Lock (depth chart); BAL Tyler Huntley -> Joe Fagnano (depth chart)                         |      27.5 |
| trends (again, week 10)        | ok       | head-to-head cover margin      96                 0.355         7.079            2.793                                                                                                                   |      54   |
| players (again, week 10)       | ok       | max           0.104589         1.360481    14.000000                                                                                                                                                     |     116.5 |
| positions (again, week 10)     | ok       | Skill    498.0  0.007932  0.00250  0.0876                                                                                                                                                                |      24.7 |
| scheme (again, week 10)        | ok       | scheme_plays (365492, 83) profiles for 32 teams as of 2026 10                                                                                                                                            |       6.2 |
| player splits (again, week 10) | ok       | player_splits.js 1.79 MB                                                                                                                                                                                 |      77.8 |
| model                          | ok       | opp_skill_out_value           12.498       0.012          0.156                                                                                                                                          |      50.2 |
| qt shadow                      | ok       | qt shadow: 3300 games, 16596 Questionable listings priced, 62s                                                                                                                                           |      63.7 |
| opener study                   | ok       | opener study written                                                                                                                                                                                     |      49.7 |
| props by season                | ok       | DONE                                                                                                                                                                                                     |      26.5 |
| props                          | error    | RuntimeError: on_upcast=True)                                                                                                                                                                            |       0.6 |
|                                |          |          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^                                                                                                                                        |           |
|                                |          |   File "/opt/hostedtoolcache/Python/3.11.18/x64/lib/python3.11/site-packages/pandas/core/internals/blocks.py", line 48                                                                                   |           |
| sizing backtest                | ok       | 2025   14-6    0.700        6.73                                                                                                                                                                         |       4.9 |
| threshold sweep                | ok       | DONE                                                                                                                                                                                                     |       1.6 |
| calibration start              | ok       | last 5 seasons     0.5288     0.5359     0.5429              0.69326            0.25006                0.68250              0.5639             0.5851             94              0.69274                |       1.6 |
| season backtest                | ok       | {'shrink0.1_sig1': 'not adopted', 'shrink0.1_sig1.15': 'not adopted', 'shrink0.2_sig1': 'not adopted', 'shrink0.2_sig1.15': 'not adopted', 'shrink0.3_sig1': 'not adopted', 'shrink0.3_sig1.15': 'not ad |      90.6 |
| legitimacy tests               | ok       | Reading: the line beats the model on the miss every season (it should; it is the market). The question the flag rests on is whether the model's disagreements with the line carry information, which the |      15.4 |
| audit reports                  | ok       | Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).                                       |       2.6 |
| picks                          | ok       | game_id  season  week  ...     bet_p  bet_odds  stake_pct                                                                                                                                                |       1   |
|                                |          | 3164  2026_10_WAS_NYG    2026    10  ...       NaN       NaN        NaN                                                                                                                                  |           |
|                                |          | 3165   2026_10_NE_DET    2026    10  ...       NaN                                                                                                                                                       |           |
| log run                        | ok       | run_at  season  ...  total_line       bet                                                                                                                                                                |       0   |
|                                |          | 3164  2026-11-10 17:27 UTC    2026  ...        41.5                                                                                                                                                      |           |
|                                |          | 3165  2026-11-10 17:27 UTC    2026  ...        51.5                                                                                                                                                      |           |
|                                |          | 3166  2026-11-                                                                                                                                                                                           |           |
| record picks                   | ok       | run_at  season  week  ...  spread_edge  total_edge  p_cover                                                                                                                                              |       0.6 |
|                                |          | 0  2026-10-04 12:37 UTC    2026     4  ...         5.08        2.49    0.673                                                                                                                             |           |
|                                |          | 1  2026-10-04 16:01 UTC    2026     4  ...                                                                                                                                                               |           |
| inputs fingerprint             | ok       | {'season': 2026, 'week': 10, 'starters': {'2026_10_WAS_NYG': ['00-0039923', '00-0039910', '2026-11-12 20:15'], '2026_10_NE_DET': ['00-0033106', '00-0039851', '2026-11-15 09:30'], '2026_10_KC_ATL': ['0 |       0.6 |
| grade                          | ok       |                                                                                                                                                                                                          |       7.7 |
| closing line value             | ok       | CLV 2026: 44 closed, 2 pending, avg +0.03 pts, 25% beat the close                                                                                                                                        |       1.1 |
| forecast history               | ok       | 10 games fetched in 2s, 2226 stored, 0 left                                                                                                                                                              |       2.4 |
| drift monitor                  | ok       | **0 alerts, 0 to watch.** Long run = 2015 to 2024; recent = 2025 and 2026 so far. ALERT at |z| >= 2.5 or a CUSUM trip (h 5); WATCH at |z| >= 2.0.                                                        |       0.5 |
| shadow watch                   | ok       | **0 rules ready for a look.** READY = 30+ settled live bets, a win rate past break-even beyond luck (p <= 0.1) and 5+ points more return per unit risked than the rule it would replace over the same se |       1.1 |
| ready checks                   | ok       | **0 ready.** Each READY row opens a GitHub issue labelled ready-check (once per title).                                                                                                                  |       0.5 |
| tie check (sources)            | error    | RuntimeError: numbers disagree: see reports/tie_check.md                                                                                                                                                 |       3.3 |
| export data room               | ok       |                                                                                                                                                                                                          |     113.1 |
| tie check (page)               | error    | RuntimeError: page files disagree with the sources: see reports/tie_check.md                                                                                                                             |       9.7 |
| standing checks                | ok       | True                                                                                                                                                                                                     |      38.9 |

**Failed steps above were skipped, not filled with stale data.**

## Week 10, 2026: 1 flagged of 14 games

| away_team   | home_team   |   away_exp |   home_exp |   spread_line |   total_line |   spread_edge |   total_edge | bet      |   stake_pct |
|:------------|:------------|-----------:|-----------:|--------------:|-------------:|--------------:|-------------:|:---------|------------:|
| LAC         | BAL         |      19.21 |      16.94 |           5.5 |         38.5 |         -7.77 |        -2.35 | LAC +5.5 |        2.73 |

Full table: reports/picks_2026_wk10.md

## Track record

## Rules compared

The flag is bet; the shadows are logged and graded on the same games but never bet, so the rule can be chosen on live results.

Backtest columns: the same rule on the three backtest windows, regular season weeks 1 to 17 (`picks.rule_records`).

| Rule | Bets | Settled | Record | Units | Avg CLV | Backtest 2015-18 | Backtest 2019-22 | Backtest 2023-25 |
|---|---|---|---|---|---|---|---|---|
| 4+ edge (the flag, bet) | 9 | 8 | 3-5 (38%) | -2.29 | +0.28 | 67-54 | 80-52 | 38-17 |
| shadow: 4.5+ edge | 6 | 5 | 2-3 (40%) | -1.21 | +0.25 | 46-36 | 55-39 | 23-15 |
| shadow: 4+ edge, model's side the underdog or pick'em | 9 | 8 | 3-5 (38%) | -2.29 | +0.28 | 52-37 | 72-43 | 30-14 |
| shadow: 4+ edge, weeks 1 to 13 only | 9 | 8 | 3-5 (38%) | -2.29 | +0.28 | 50-41 | 69-38 | 30-14 |

Full record: reports/track_record.md
