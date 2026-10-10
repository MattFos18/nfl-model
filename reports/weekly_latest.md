# Weekly run, 2026-10-10 16:17 UTC

## Steps

| step                | status   | detail                                                                                                                                                                                                   |   seconds |
|:--------------------|:---------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------:|
| pull                | ok       | [('2026-10-10T16:17:50', 'schedules', 'all', 'https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv', 'ok', 2183995, 'f9c22f829473'), ('2026-10-10T16:17:50', 'players', 'all' |       2.7 |
| pull player history | ok       | [('2026-10-10T16:17:53', 'pfr_advstats', 2018, 'https://github.com/nflverse/nflverse-data/releases/download/pfr_advstats/advstats_week_def_2018.parquet', 'cached', 149299, ''), ('2026-10-10T16:17:53', |       0   |
| build               | ok       | team_games (8202, 142)                                                                                                                                                                                   |     199.3 |
| features            | ok       | [40 rows x 8 columns]                                                                                                                                                                                    |      19.6 |
| snap exposure       | ok       | snap exposure (330605, 10) seasons 2013 to 2026                                                                                                                                                          |       1.5 |
| verify              | ok       | Result: PASS                                                                                                                                                                                             |       0.6 |
| data checks         | ok       | True                                                                                                                                                                                                     |       0.6 |
| weather             | ok       | game_id           kickoff_et  ... precip        fetched_at                                                                                                                                               |     148.6 |
|                     |          | 0   2026_05_PHI_JAX  2026-10-11 09:30:00  ...    0.0  2026-10-10 12:21                                                                                                                                   |           |
|                     |          | 1    2026_05_CHI_GB  2026-10-11 13:00:00  ...    0.0  2026                                                                                                                                               |           |
| wind forecast       | ok       | 1                                                                                                                                                                                                        |       5.4 |
| lines               | ok       | {'ts': '2026-10-10T16-24-09Z', 'season': 2026, 'week': 5, 'rows': 14, 'errors': ''}                                                                                                                      |     128.1 |
| live results        | ok       | live results: week 5, 1 final of 15, 0 in progress; spread 1-0, total 0-1, winner 0-1; play-by-play for 1 games                                                                                          |       3.9 |
| ratings             | ok       | (7668, 51) QB-out check: ok; swaps: none                                                                                                                                                                 |      33.9 |
| trends              | ok       | head-to-head cover margin      96                 0.355         7.079            2.793                                                                                                                   |      85.3 |
| players             | ok       | max           0.104589         1.360481    14.000000                                                                                                                                                     |     179.4 |
| positions           | ok       | Skill    516.0  0.007898  0.00250  0.0806                                                                                                                                                                |      32.9 |
| scheme              | ok       | scheme_plays (356596, 83) profiles for 32 teams as of 2026 5                                                                                                                                             |       8.1 |
| player splits       | ok       | player_splits.js 1.65 MB                                                                                                                                                                                 |     130   |
| model               | ok       | opp_skill_out_value           12.498       0.012          0.156                                                                                                                                          |      73.8 |
| qt shadow           | ok       | qt shadow: 3300 games, 16181 Questionable listings priced, 88s                                                                                                                                           |      89   |
| opener study        | ok       | opener study written                                                                                                                                                                                     |      74.2 |
| props by season     | ok       | DONE                                                                                                                                                                                                     |      33.1 |
| props               | ok       | props 2690 projections for week 5 graded rows 0 market lines on the cards 288 graded against the market 3661                                                                                             |      39.3 |
| sizing backtest     | ok       | 2025   14-6    0.700        6.73                                                                                                                                                                         |       6.6 |
| threshold sweep     | ok       | DONE                                                                                                                                                                                                     |       1.9 |
| calibration start   | ok       | last 5 seasons     0.5288     0.5359     0.5429              0.69326            0.25006                0.68250              0.5639             0.5851             94              0.69274                |       1.9 |
| season backtest     | ok       | {'shrink0.1_sig1': 'not adopted', 'shrink0.1_sig1.15': 'not adopted', 'shrink0.2_sig1': 'not adopted', 'shrink0.2_sig1.15': 'not adopted', 'shrink0.3_sig1': 'not adopted', 'shrink0.3_sig1.15': 'not ad |     105.7 |
| legitimacy tests    | ok       | Reading: the line beats the model on the miss every season (it should; it is the market). The question the flag rests on is whether the model's disagreements with the line carry information, which the |      22.6 |
| audit reports       | ok       | Closing line value is not measurable in this backtest: nflverse stores closing lines only. It starts being logged from the first live week (open, midweek, close).                                       |       3.4 |
| picks               | ok       | game_id  season  week  ... bet_p bet_odds stake_pct                                                                                                                                                      |       1.3 |
|                     |          | 3092   2026_05_TB_DAL    2026     5  ...   NaN      NaN       NaN                                                                                                                                        |           |
|                     |          | 3093  2026_05_PHI_JAX    2026     5  ...   NaN      NaN       NaN                                                                                                                                        |           |
|                     |          | 30                                                                                                                                                                                                       |           |
| log run             | ok       | run_at  season  week  ... spread_line  total_line  bet                                                                                                                                                   |       0   |
|                     |          | 3092  2026-10-10 16:17 UTC    2026     5  ...         9.5        49.5                                                                                                                                    |           |
|                     |          | 3093  2026-10-10 16:17 UTC    2026     5  ...                                                                                                                                                            |           |
| record picks        | ok       | run_at season week  ... spread_edge total_edge p_cover                                                                                                                                                   |       0.8 |
|                     |          | 0  2026-10-04 12:37 UTC   2026    4  ...        5.08       2.49   0.673                                                                                                                                  |           |
|                     |          | 1  2026-10-04 16:01 UTC   2026    4  ...       -4.87                                                                                                                                                     |           |
| inputs fingerprint  | ok       | {'season': 2026, 'week': 5, 'starters': {'2026_05_TB_DAL': ['00-0033077', '00-0041251', '2026-10-08 20:15'], '2026_05_PHI_JAX': ['00-0036971', '00-0036389', '2026-10-11 09:30'], '2026_05_CHI_GB': ['00 |       0.8 |
| grade               | ok       |                                                                                                                                                                                                          |       5.9 |
| closing line value  | ok       | CLV 2026: 10 closed, 9 pending, avg -0.05 pts, 20% beat the close                                                                                                                                        |       0.7 |
| forecast history    | ok       | complete: 2177 games stored                                                                                                                                                                              |       0.1 |
| drift monitor       | ok       | **0 alerts, 0 to watch.** Long run = 2015 to 2024; recent = 2025 and 2026 so far. ALERT at |z| >= 2.5 or a CUSUM trip (h 5); WATCH at |z| >= 2.0.                                                        |       0.6 |
| shadow watch        | ok       | **0 rules ready for a look.** READY = 30+ settled live bets, a win rate past break-even beyond luck (p <= 0.1) and 5+ points more return per unit risked than the rule it would replace over the same se |       1.4 |
| ready checks        | ok       | **0 ready.** Each READY row opens a GitHub issue labelled ready-check (once per title).                                                                                                                  |       0.5 |
| tie check (sources) | error    | RuntimeError: numbers disagree: see reports/tie_check.md                                                                                                                                                 |       5.1 |
| export data room    | ok       |                                                                                                                                                                                                          |     144.4 |
| tie check (page)    | error    | RuntimeError: page files disagree with the sources: see reports/tie_check.md                                                                                                                             |      12.2 |
| standing checks     | ok       | True                                                                                                                                                                                                     |      51.7 |

**Failed steps above were skipped, not filled with stale data.**

## Week 5, 2026: 0 flagged of 15 games

No game clears the flag thresholds.

Full table: reports/picks_2026_wk5.md

## Track record

## Rules compared

The flag is bet; the shadows are logged and graded on the same games but never bet, so the rule can be chosen on live results.

Backtest columns: the same rule on the three backtest windows, regular season weeks 1 to 17 (`picks.rule_records`).

| Rule | Bets | Settled | Record | Units | Avg CLV | Backtest 2015-18 | Backtest 2019-22 | Backtest 2023-25 |
|---|---|---|---|---|---|---|---|---|
| 4+ edge (the flag, bet) | 3 | 3 | 2-1 (67%) | +0.88 | +0.00 | 67-54 | 80-52 | 38-17 |
| shadow: 4.5+ edge | 2 | 2 | 1-1 (50%) | -0.05 | +0.00 | 46-36 | 55-39 | 23-15 |
| shadow: 4+ edge, model's side the underdog or pick'em | 3 | 3 | 2-1 (67%) | +0.88 | +0.00 | 52-37 | 72-43 | 30-14 |
| shadow: 4+ edge, weeks 1 to 13 only | 3 | 3 | 2-1 (67%) | +0.88 | +0.00 | 50-41 | 69-38 | 30-14 |

Full record: reports/track_record.md
