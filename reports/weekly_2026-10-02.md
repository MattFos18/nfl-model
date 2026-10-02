# Weekly run, 2026-10-02 21:56 UTC

## Steps

| step                | status   | detail                                                                                                                                                                                                   |   seconds |
|:--------------------|:---------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------:|
| pull                | ok       | [('2026-10-02T21:56:54', 'schedules', 'all', 'https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv', 'ok', 2182452, 'a8420139b2b5'), ('2026-10-02T21:56:54', 'players', 'all' |       3.8 |
| pull player history | ok       | [('2026-10-02T21:56:58', 'pfr_advstats', 2018, 'https://github.com/nflverse/nflverse-data/releases/download/pfr_advstats/advstats_week_def_2018.parquet', 'cached', 149299, ''), ('2026-10-02T21:56:58', |       0   |
| build               | ok       | team_games (8202, 142)                                                                                                                                                                                   |     161.2 |
| features            | ok       | [40 rows x 8 columns]                                                                                                                                                                                    |      14   |
| snap exposure       | ok       | snap exposure (329121, 10) seasons 2013 to 2026                                                                                                                                                          |       1.3 |
| verify              | ok       | Result: PASS                                                                                                                                                                                             |       0.5 |
| data checks         | ok       | True                                                                                                                                                                                                     |       0.5 |
| weather             | ok       | game_id           kickoff_et  ... precip        fetched_at                                                                                                                                               |       2.7 |
|                     |          | 0   2026_04_IND_WAS  2026-10-04 09:30:00  ...   0.00  2026-10-02 17:59                                                                                                                                   |           |
|                     |          | 1   2026_04_TEN_BAL  2026-10-04 13:00:00  ...   0.00  2026                                                                                                                                               |           |
| wind forecast       | ok       | 2                                                                                                                                                                                                        |       7.1 |
| lines               | ok       | {'ts': '2026-10-02T22-00-06Z', 'season': 2026, 'week': 4, 'rows': 15, 'errors': 'wind: GFS MOS gave nothing for any of the 10 games within 59 hours of kickoff'}                                         |     129.4 |
| live results        | ok       | live results: week 4, 1 final of 16, 0 in progress; spread 1-0, total 0-1, winner 0-1; play-by-play for 1 games                                                                                          |       3.6 |
| ratings             | ok       | (7668, 50) QB-out check: ok; swaps: none                                                                                                                                                                 |      25.4 |
| trends              | ok       | head-to-head cover margin      96                 0.355         7.079            2.793                                                                                                                   |      64.8 |
| players             | ok       | max           0.104589         1.360481    14.000000                                                                                                                                                     |     136.3 |
| positions           | ok       | Skill     541.0  0.007945  0.00250  0.0816                                                                                                                                                               |      27.5 |
| scheme              | ok       | scheme_plays (354592, 83) profiles for 32 teams as of 2026 4                                                                                                                                             |       6.3 |
| player splits       | ok       | player_splits.js 1.61 MB                                                                                                                                                                                 |      87.9 |
| model               | ok       | neutral            0.054       0.133          0.007                                                                                                                                                      |      65.5 |
| opener study        | ok       | opener study written                                                                                                                                                                                     |      64.2 |
| props by season     | ok       | DONE                                                                                                                                                                                                     |      26.4 |
| props               | ok       | props 2869 projections for week 4 graded rows 0 market lines on the cards 314 graded against the market 1833                                                                                             |      28.5 |
| sizing backtest     | ok       | 2025   13-7    0.650        4.82                                                                                                                                                                         |       5.4 |
| threshold sweep     | ok       | DONE                                                                                                                                                                                                     |       1.6 |
| calibration start   | ok       | last 5 seasons     0.5243     0.5295     0.5347              0.69375            0.25030                0.68186              0.5595                0.6             90              0.69254                |       1.6 |
| season backtest     | ok       | {'shrink0.1_sig1': 'not adopted', 'shrink0.1_sig1.15': 'not adopted', 'shrink0.2_sig1': 'not adopted', 'shrink0.2_sig1.15': 'not adopted', 'shrink0.3_sig1': 'not adopted', 'shrink0.3_sig1.15': 'not ad |     102.9 |
| legitimacy tests    | ok       | Reading: the line beats the model on the miss every season (it should; it is the market). The question the flag rests on is whether the model's disagreements with the line carry information, which the |      16.5 |
| audit reports       | ok       | Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).                                       |       2.7 |
| picks               | ok       | game_id  season  week  ...     bet_p bet_odds stake_pct                                                                                                                                                  |       1   |
|                     |          | 3076  2026_04_PIT_CLE    2026     4  ...       NaN      NaN       NaN                                                                                                                                    |           |
|                     |          | 3077  2026_04_IND_WAS    2026     4  ...  0.547617   -115.0                                                                                                                                              |           |
| log run             | ok       | run_at  season  week  ... spread_line  total_line       bet                                                                                                                                              |       0   |
|                     |          | 3076  2026-10-02 21:56 UTC    2026     4  ...        -2.5        38.5                                                                                                                                    |           |
|                     |          | 3077  2026-10-02 21:56 UTC    2026     4                                                                                                                                                                 |           |
| record picks        | ok       | run_at  season  week  ... spread_edge total_edge  p_cover                                                                                                                                                |       0.6 |
|                     |          | 0  2026-10-02 21:56 UTC    2026     4  ...        4.99       2.05    0.671                                                                                                                               |           |
|                     |          | 1  2026-10-02 21:56 UTC    2026     4  ...       -                                                                                                                                                       |           |
| inputs fingerprint  | ok       | {'season': 2026, 'week': 4, 'starters': {'2026_04_PIT_CLE': ['00-0033537', '00-0023459', '2026-10-01 20:15'], '2026_04_IND_WAS': ['00-0032268', '00-0035710', '2026-10-04 09:30'], '2026_04_TEN_BAL': [' |       0.5 |
| grade               | ok       |                                                                                                                                                                                                          |       2.8 |
| closing line value  | ok       | CLV 2026: 4 closed, 7 pending, avg +0.25 pts, 25% beat the close                                                                                                                                         |       0.3 |
| forecast history    | ok       | 555 games fetched in 647s, 2123 stored, 43 left                                                                                                                                                          |     646.8 |
| drift monitor       | ok       | **0 alerts, 0 to watch.** Long run = 2015 to 2024; recent = 2025 and 2026 so far. ALERT at |z| >= 2.5 or a CUSUM trip (h 5); WATCH at |z| >= 2.0.                                                        |       0.5 |
| shadow watch        | ok       | **0 rules ready for a look.** READY = 30+ settled live bets, a win rate past break-even beyond luck (p <= 0.1) and 5+ points more return per unit risked than the rule it would replace over the same se |       1.1 |
| ready checks        | ok       | **0 ready.** Each READY row opens a GitHub issue labelled ready-check (once per title).                                                                                                                  |       0.4 |
| tie check (sources) | error    | RuntimeError: numbers disagree: see reports/tie_check.md                                                                                                                                                 |       4.1 |
| export data room    | ok       |                                                                                                                                                                                                          |     110.9 |
| tie check (page)    | error    | RuntimeError: page files disagree with the sources: see reports/tie_check.md                                                                                                                             |       8.9 |
| standing checks     | ok       | True                                                                                                                                                                                                     |      44.9 |

**Failed steps above were skipped, not filled with stale data.**

## Week 4, 2026: 3 flagged of 16 games

| away_team   | home_team   |   away_exp |   home_exp |   spread_line |   total_line |   spread_edge |   total_edge | bet      |   stake_pct |
|:------------|:------------|-----------:|-----------:|--------------:|-------------:|--------------:|-------------:|:---------|------------:|
| IND         | WAS         |      24.53 |      25.02 |          -4.5 |         47.5 |          4.99 |         2.05 | WAS +4.5 |        0.68 |
| JAX         | CIN         |      26.53 |      24.04 |           2.5 |         51.5 |         -4.99 |        -0.93 | JAX +2.5 |        1.81 |
| ARI         | NYG         |      18.87 |      21.41 |          -2.5 |         44.5 |          5.04 |        -4.22 | NYG +2.5 |        1.5  |

Full table: reports/picks_2026_wk4.md

## Track record

## Rules compared

The flag is bet; the shadows are logged and graded on the same games but never bet, so the rule can be chosen on live results.

Backtest columns: the same rule on the three backtest windows, regular season weeks 1 to 17 (`picks.rule_records`).

| Rule | Bets | Settled | Record | Units | Avg CLV | Backtest 2015-18 | Backtest 2019-22 | Backtest 2023-25 |
|---|---|---|---|---|---|---|---|---|
| 4+ edge (the flag, bet) | 3 | 0 | nothing settled |  | +0.00 | 67-55 | 76-47 | 37-20 |
| shadow: 4.5+ edge | 3 | 0 | nothing settled |  | +0.00 | 42-37 | 53-39 | 24-15 |
| shadow: 4+ edge, model's side the underdog or pick'em | 3 | 0 | nothing settled |  | +0.00 | 50-37 | 69-38 | 29-17 |
| shadow: 4+ edge, weeks 1 to 13 only | 3 | 0 | nothing settled |  | +0.00 | 53-41 | 66-35 | 30-17 |

Full record: reports/track_record.md
