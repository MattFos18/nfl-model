# Weekly run, 2026-10-03 21:31 UTC

## Steps

| step                | status   | detail                                                                                                                                                                                                   |   seconds |
|:--------------------|:---------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------:|
| pull                | ok       | [('2026-10-03T21:31:29', 'schedules', 'all', 'https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv', 'ok', 2182448, '5db3e66c13fa'), ('2026-10-03T21:31:29', 'players', 'all' |       5.5 |
| pull player history | ok       | [('2026-10-03T21:31:34', 'pfr_advstats', 2018, 'https://github.com/nflverse/nflverse-data/releases/download/pfr_advstats/advstats_week_def_2018.parquet', 'cached', 149299, ''), ('2026-10-03T21:31:34', |       0   |
| build               | ok       | team_games (8202, 142)                                                                                                                                                                                   |     124.3 |
| features            | ok       | [40 rows x 8 columns]                                                                                                                                                                                    |      11   |
| snap exposure       | ok       | snap exposure (329121, 10) seasons 2013 to 2026                                                                                                                                                          |       1.1 |
| verify              | ok       | Result: PASS                                                                                                                                                                                             |       0.4 |
| data checks         | ok       | True                                                                                                                                                                                                     |       0.4 |
| weather             | ok       | game_id           kickoff_et  ... precip        fetched_at                                                                                                                                               |       3.6 |
|                     |          | 0   2026_04_IND_WAS  2026-10-04 09:30:00  ...    0.0  2026-10-03 17:33                                                                                                                                   |           |
|                     |          | 1   2026_04_TEN_BAL  2026-10-04 13:00:00  ...    0.0  2026                                                                                                                                               |           |
| wind forecast       | ok       | 2                                                                                                                                                                                                        |       6.6 |
| lines               | ok       | {'ts': '2026-10-03T21-34-02Z', 'season': 2026, 'week': 4, 'rows': 15, 'errors': ''}                                                                                                                      |     186.5 |
| live results        | ok       | live results: week 4, 1 final of 16, 0 in progress; spread 1-0, total 0-1, winner 0-1; play-by-play for 1 games                                                                                          |       2.5 |
| ratings             | ok       | (7668, 51) QB-out check: ok; swaps: none                                                                                                                                                                 |      18.5 |
| trends              | ok       | head-to-head cover margin      96                 0.355         7.079            2.793                                                                                                                   |      42.1 |
| players             | ok       | max           0.104589         1.360481    14.000000                                                                                                                                                     |      95.2 |
| positions           | ok       | Skill     541.0  0.007945  0.00250  0.0816                                                                                                                                                               |      20.8 |
| scheme              | ok       | scheme_plays (354592, 83) profiles for 32 teams as of 2026 4                                                                                                                                             |       4.6 |
| player splits       | ok       | player_splits.js 1.61 MB                                                                                                                                                                                 |      58.1 |
| model               | ok       | opp_skill_out_value           12.498       0.012          0.156                                                                                                                                          |      40.5 |
| qt shadow           | ok       | qt shadow: 3300 games, 16116 Questionable listings priced, 49s                                                                                                                                           |      49.6 |
| opener study        | ok       | opener study written                                                                                                                                                                                     |      39.9 |
| props by season     | ok       | DONE                                                                                                                                                                                                     |      19.1 |
| props               | ok       | props 2864 projections for week 4 graded rows 0 market lines on the cards 318 graded against the market 1833                                                                                             |      19.5 |
| sizing backtest     | ok       | 2025   14-6    0.700        6.73                                                                                                                                                                         |       3.7 |
| threshold sweep     | ok       | DONE                                                                                                                                                                                                     |       1.2 |
| calibration start   | ok       | last 5 seasons     0.5288     0.5359     0.5429              0.69326            0.25006                0.68250              0.5639             0.5851             94              0.69274                |       1.2 |
| season backtest     | ok       | {'shrink0.1_sig1': 'not adopted', 'shrink0.1_sig1.15': 'not adopted', 'shrink0.2_sig1': 'not adopted', 'shrink0.2_sig1.15': 'not adopted', 'shrink0.3_sig1': 'not adopted', 'shrink0.3_sig1.15': 'not ad |      66.2 |
| legitimacy tests    | ok       | Reading: the line beats the model on the miss every season (it should; it is the market). The question the flag rests on is whether the model's disagreements with the line carry information, which the |      11.8 |
| audit reports       | ok       | Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).                                       |       2   |
| picks               | ok       | game_id  season  week  ...     bet_p bet_odds stake_pct                                                                                                                                                  |       0.7 |
|                     |          | 3076  2026_04_PIT_CLE    2026     4  ...       NaN      NaN       NaN                                                                                                                                    |           |
|                     |          | 3077  2026_04_IND_WAS    2026     4  ...  0.552170   -115.0                                                                                                                                              |           |
| log run             | ok       | run_at  season  week  ... spread_line  total_line       bet                                                                                                                                              |       0   |
|                     |          | 3076  2026-10-03 21:31 UTC    2026     4  ...        -2.5        38.5                                                                                                                                    |           |
|                     |          | 3077  2026-10-03 21:31 UTC    2026     4                                                                                                                                                                 |           |
| record picks        | ok       | run_at  season  week  ... spread_edge total_edge  p_cover                                                                                                                                                |       0.4 |
|                     |          | 0  2026-10-03 21:31 UTC    2026     4  ...        4.76       2.32    0.665                                                                                                                               |           |
|                     |          | 1  2026-10-03 21:31 UTC    2026     4  ...       -                                                                                                                                                       |           |
| inputs fingerprint  | ok       | {'season': 2026, 'week': 4, 'starters': {'2026_04_PIT_CLE': ['00-0033537', '00-0023459', '2026-10-01 20:15'], '2026_04_IND_WAS': ['00-0032268', '00-0035710', '2026-10-04 09:30'], '2026_04_TEN_BAL': [' |       0.4 |
| grade               | ok       |                                                                                                                                                                                                          |       1.9 |
| closing line value  | ok       | CLV 2026: 4 closed, 6 pending, avg +0.25 pts, 25% beat the close                                                                                                                                         |       0.2 |
| forecast history    | ok       | complete: 2166 games stored                                                                                                                                                                              |       0   |
| drift monitor       | ok       | **0 alerts, 0 to watch.** Long run = 2015 to 2024; recent = 2025 and 2026 so far. ALERT at |z| >= 2.5 or a CUSUM trip (h 5); WATCH at |z| >= 2.0.                                                        |       0.4 |
| shadow watch        | ok       | **0 rules ready for a look.** READY = 30+ settled live bets, a win rate past break-even beyond luck (p <= 0.1) and 5+ points more return per unit risked than the rule it would replace over the same se |       0.8 |
| ready checks        | ok       | **0 ready.** Each READY row opens a GitHub issue labelled ready-check (once per title).                                                                                                                  |       0.3 |
| tie check (sources) | ok       | True                                                                                                                                                                                                     |       2.9 |
| export data room    | ok       |                                                                                                                                                                                                          |      74.8 |
| tie check (page)    | ok       | True                                                                                                                                                                                                     |       6.8 |
| standing checks     | ok       | True                                                                                                                                                                                                     |      28.1 |

## Week 4, 2026: 3 flagged of 16 games

| away_team   | home_team   |   away_exp |   home_exp |   spread_line |   total_line |   spread_edge |   total_edge | bet      |   stake_pct |
|:------------|:------------|-----------:|-----------:|--------------:|-------------:|--------------:|-------------:|:---------|------------:|
| IND         | WAS         |      24.28 |      24.54 |          -4.5 |         46.5 |          4.76 |         2.32 | WAS +4.5 |        0.93 |
| JAX         | CIN         |      26.07 |      23.58 |           2.5 |         51.5 |         -4.99 |        -1.85 | JAX +2.5 |        2.2  |
| ARI         | NYG         |      21.41 |      23.75 |          -2.5 |         44.5 |          4.84 |         0.66 | NYG +2.5 |        1.77 |

Full table: reports/picks_2026_wk4.md

## Track record

## Rules compared

The flag is bet; the shadows are logged and graded on the same games but never bet, so the rule can be chosen on live results.

Backtest columns: the same rule on the three backtest windows, regular season weeks 1 to 17 (`picks.rule_records`).

| Rule | Bets | Settled | Record | Units | Avg CLV | Backtest 2015-18 | Backtest 2019-22 | Backtest 2023-25 |
|---|---|---|---|---|---|---|---|---|
| 4+ edge (the flag, bet) | 3 | 0 | nothing settled |  | +0.00 | 67-54 | 80-52 | 38-17 |
| shadow: 4.5+ edge | 3 | 0 | nothing settled |  | +0.00 | 46-36 | 55-39 | 23-15 |
| shadow: 4+ edge, model's side the underdog or pick'em | 3 | 0 | nothing settled |  | +0.00 | 52-37 | 72-43 | 30-14 |
| shadow: 4+ edge, weeks 1 to 13 only | 3 | 0 | nothing settled |  | +0.00 | 50-41 | 69-38 | 30-14 |

Full record: reports/track_record.md
