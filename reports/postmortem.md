# Postmortem: every bet the model would have made, 2015-2025 (and 2026 so far)

`experiments/postmortem.py`, run 29 Sep 2026, 107s. Walk-forward predictions from `data/processed/pred_v3.parquet`, no refit. Rows: `reports/postmortem.csv` (one per bet, with the decomposition); every comparison and every filter test: `reports/postmortem_patterns.csv`.

## The bets

- **Spread flag**: the model 4+ points from the closing line, regular season, Weeks 1-17. 2015-18 68-55 (+7.5u), 2019-22 80-51 (+23.9u), 2023-25 40-21-1 (+16.9u).
- **Under flag**: an under at a 55%+ raw chance (`p_over_emp`), Weeks 1-17. 2015-18 135-127-3 (-4.7u), 2019-22 175-128-4 (+34.2u), 2023-25 71-59-1 (+6.1u).
- Graded at -110 (a loss costs 1.1 units), pushes out of the record, exactly as `backtest.grade_spread` and `picks.record`.

## Adoption rule (fixed before any result below)

A filter or adjustment is adopted only if (1) its units at -110 are higher than today's rule on **each** of 2015-18, 2019-22 and 2023-25, and (2) it keeps at least 80% of today's bets in **each** window. The bootstrap probability that the filtered record beats the unfiltered one (10,000 Poisson-weight resamples of the games in either set) is reported beside every rule but does not decide. No adjustment may read a market input: the line defines and grades the bet only (a filter may read the bet's own number, e.g. 'the model's side lays 7+').

Pre-registered candidates (the brief's examples and the docs' open questions): skip when the model's side lays 7+; skip Weeks 1-2; skip Week 17 (Week 18 is already out); skip each season's final week (Week 17 through 2020); skip when the edge comes only from the injury inputs (with and without QB-out); cap the injury inputs' pull on the margin at 1, 2 or 3 points or drop it; skip Weeks 14-17; skip favourites; skip laying exactly 3 or 7; skip edges that cross neither 3 nor 7; skip 7+ edges; skip when the trees disagree or the seven models disagree most; skip when either side's starting QB is out. Unders: skip Weeks 1-2, Week 17, the final week, Weeks 14-17, domes, wind 15+, primetime, either starter out, lines 50+; raise the cut to 56/57/58/60%. On top of these, every situation in the loss-against-win comparison is scored as a 'skip it' filter (marked 'every situation'); those are found by looking, so a pass there needs more than the rule to be believed.

## How the miss is decomposed

The miss is the actual margin (or total) minus the model's, signed so negative hurt the bet. Each game's components come from its play-by-play (one read per season). They are put in points by one least-squares fit of the model's miss on all of them over every regular-season game 2015-2025 (2895 games), then centred on the league mean and signed toward the bet. Margin fit R² 0.65 (the four luck components alone 0.63); total fit R² 0.30 (luck alone 0.20).

Margin (home side):

| Component   | Measured as   | Group   |   Points per unit |    se |
|:------------|:--------------|:--------|------------------:|------:|
| turnovers   | to_epa_net    | luck    |             0.503 | 0.017 |
| returns     | st_epa_net    | luck    |             0.625 | 0.103 |
| kicks       | kick_epa_net  | luck    |             0.37  | 0.043 |
| garbage     | gb_net        | luck    |             0.91  | 0.022 |
| qb_lost     | qb_lost_net   | event   |             3.007 | 0.534 |
| weather     | wx_margin     | event   |            -0.36  | 0.97  |
| overtime    | ot_net        | event   |             0.198 | 0.123 |
| pace        | pace_margin   | event   |            -0.478 | 0.365 |
| penalties   | pen_epa_h     | event   |             0.133 | 0.044 |
| fourth      | fd_epa_h      | event   |             0.342 | 0.031 |

Total:

| Component   | Measured as    | Group   |   Points per unit |    se |
|:------------|:---------------|:--------|------------------:|------:|
| turnovers   | pot_sum_nonret | luck    |             0.319 | 0.035 |
| returns     | ret_td_sum     | luck    |             4.671 | 0.382 |
| kicks       | kick_epa_sum   | luck    |             0.396 | 0.062 |
| garbage     | gb_sum         | luck    |             0.366 | 0.018 |
| qb_lost     | qb_lost_sum    | event   |            -2.511 | 0.799 |
| weather     | wx_total       | event   |             0.552 | 0.246 |
| overtime    | ot_sum         | event   |             0.589 | 0.156 |
| pace        | d_plays        | event   |             0.412 | 0.027 |
| penalties   | pen_yds_sum    | event   |             0.009 | 0.005 |
| fourth      | fd_att_sum     | event   |            -0.696 | 0.132 |

Notes. Turnovers: the EPA of every interception and lost fumble (muffs included) on the side that lost the ball, return TDs on them included; points off turnovers (the next drive's points plus return TDs) are in the CSV and drive the totals version. Returns: kickoff and punt return TDs. Kicks: EPA of every field goal, extra point and blocked punt (a miss or block is the luck; a made kick of average difficulty is about zero). Garbage time: points on plays that start with the home side under 10% or over 90% to win, turnover and return plays taken out. QB: the starter (the schedule's QB id) under 60% of his team's dropbacks. Weather: the Open-Meteo kickoff-hour reading (archive; the play-by-play's game-day text when the archive lacks the game) against the temp/wind the model read. In the backtest that input is the schedule's game-day reading, not a forecast, so the weather surprise here is small by construction; live, the model reads a forecast. Pace: the game's offensive plays against a fit of plays on the two teams' plays ratings; on the margin, the model's margin scaled by the extra plays. Penalties: EPA of accepted penalties that wiped the play out (margin), accepted penalty yards (total). Fourth downs: EPA of go-for-it plays (margin), the number of tries (total).

## What we missed

### Spread flag, the losses 2015-2025

A loss is put in the first class that flips it: 'luck' if taking the four luck components out would have covered, then 'in-game events', then 'knowable' if the model priced a QB who did not play or the bet sits in a situation whose removal improved units on all three windows (an upper bound: the Part 2 placebo puts those situations at chance level), else 'ordinary variance'. Points: the sum over the losses of each group's points (knowable and variance share the residual).

| Explained by                                                                                   | Losses (count, first that flips it)   | Points of the miss   |
|:-----------------------------------------------------------------------------------------------|:--------------------------------------|:---------------------|
| Luck (turnovers, returns, kicks, garbage time)                                                 | 50 (39%)                              | -1144 (56%)          |
| In-game events (QB lost, weather, overtime, pace, penalties, 4th downs)                        | 9 (7%)                                | -79 (4%)             |
| Knowable (the model priced a QB who did not play, or a pattern that lost on all three windows) | 15 (12%)                              | -129 (6%)            |
| Ordinary variance (the rest)                                                                   | 53 (42%)                              | -690 (34%)           |
| All losses                                                                                     | 127                                   | -2042 (mean -16.1)   |

Luck cuts both ways: 50 of 127 losses flip to a cover without the luck, and 27 of 188 wins flip to a loss without it. Some of that asymmetry is mechanical (a bet with a real edge sits above the line more often than below it, so symmetric noise pushes more would-be wins under than would-be losses over); the record with the luck taken out:

| Window   | Actual record   | Record with the four luck components taken out   |
|:---------|:----------------|:-------------------------------------------------|
| 2015-18  | 68-55           | 78-45                                            |
| 2019-22  | 80-51           | 93-38                                            |
| 2023-25  | 40-21           | 41-21                                            |
| 2015-25  | 188-127         | 212-104                                          |

Garbage time is the one luck component that is not zero on average over all spread bets (table below). Split by who was ahead (mean points per bet toward the model's side, plays at a 90%+ win chance):

| Bets                       |   n |   own pts, own side leading |   opp pts, own side leading (backdoor against) |   own pts, own side trailing (backdoor for) |   opp pts, own side trailing (pile-on) |   net |
|:---------------------------|----:|----------------------------:|-----------------------------------------------:|--------------------------------------------:|---------------------------------------:|------:|
| losses                     | 127 |                        0.19 |                                          -0.21 |                                        3.45 |                                  -9.41 | -5.98 |
| wins                       | 188 |                        5.34 |                                          -3.12 |                                        0.91 |                                  -0.72 |  2.41 |
| all bets                   | 315 |                        3.26 |                                          -1.95 |                                        1.94 |                                  -4.23 | -0.97 |
| model's side the underdog  | 253 |                        2.67 |                                          -1.66 |                                        2.13 |                                  -4.92 | -1.78 |
| model's side the favourite |  62 |                        5.68 |                                          -3.13 |                                        1.15 |                                  -1.39 |  2.31 |

Nearly all of it is the leader's points: when the model's side (four in five times the underdog) is being blown out, the favourite keeps scoring after the game is decided. That is the tail of being outplayed, not a backdoor. The backdoor parts (the trailing side's garbage points) cancel. Counting only the trailing side's garbage points as luck (the leader's pile-on moves to the residual):

| Explained by                                                                                   | Losses (count, first that flips it)   | Points of the miss   |
|:-----------------------------------------------------------------------------------------------|:--------------------------------------|:---------------------|
| Luck (turnovers, returns, kicks, garbage time)                                                 | 16 (13%)                              | +2 (-0%)             |
| In-game events (QB lost, weather, overtime, pace, penalties, 4th downs)                        | 4 (3%)                                | -79 (4%)             |
| Knowable (the model priced a QB who did not play, or a pattern that lost on all three windows) | 23 (18%)                              | -406 (20%)           |
| Ordinary variance (the rest)                                                                   | 84 (66%)                              | -1558 (76%)          |
| All losses                                                                                     | 127                                   | -2042 (mean -16.1)   |

### Under flag, the losses 2015-2025

| Explained by                                                                                   | Losses (count, first that flips it)   | Points of the miss   |
|:-----------------------------------------------------------------------------------------------|:--------------------------------------|:---------------------|
| Luck (turnovers, returns, kicks, garbage time)                                                 | 52 (17%)                              | -597 (14%)           |
| In-game events (QB lost, weather, overtime, pace, penalties, 4th downs)                        | 21 (7%)                               | -492 (11%)           |
| Knowable (the model priced a QB who did not play, or a pattern that lost on all three windows) | 58 (18%)                              | -746 (17%)           |
| Ordinary variance (the rest)                                                                   | 183 (58%)                             | -2539 (58%)          |
| All losses                                                                                     | 314                                   | -4374 (mean -13.9)   |

Luck both ways: 52 of 314 losses flip without the luck; 54 of 381 wins flip the other way.

| Window   | Actual record   | Record with the four luck components taken out   |
|:---------|:----------------|:-------------------------------------------------|
| 2015-18  | 135-127         | 132-133                                          |
| 2019-22  | 175-128         | 171-136                                          |
| 2023-25  | 71-59           | 79-52                                            |
| 2015-25  | 381-314         | 382-321                                          |

### Losses against wins, component by component (mean points toward the bet)

The line that matters for 'systematic' is the all-bets mean: luck that is noise averages zero over every bet; a component that is negative on every bet, wins and losses together, in every window, is something the model gets wrong before kickoff.

Spread flag:

| Component (pts toward the bet)   |   Losses |   Wins |   All bets |   t (all bets vs 0) |   2015-18 |   2019-22 |   2023-25 |
|:---------------------------------|---------:|-------:|-----------:|--------------------:|----------:|----------:|----------:|
| miss                             |   -16.08 |   6.25 |      -2.75 |                     |     -3.49 |     -2.31 |     -2.23 |
| luck                             |    -9.01 |   4.56 |      -0.91 |                -1.5 |     -1.58 |     -0.76 |      0.13 |
| turnovers                        |    -2.96 |   2.04 |       0.02 |                 0.1 |     -0.33 |      0.31 |      0.1  |
| returns                          |    -0.01 |   0.22 |       0.12 |                 2   |      0.04 |      0.17 |      0.21 |
| kicks                            |    -0.21 |   0.18 |       0.02 |                 0.3 |     -0.02 |     -0.02 |      0.2  |
| garbage                          |    -5.82 |   2.13 |      -1.08 |                -2.6 |     -1.27 |     -1.22 |     -0.38 |
| events                           |    -0.62 |   0.44 |       0.01 |                 0.1 |      0.09 |     -0.08 |      0.03 |
| qb_lost                          |    -0.28 |  -0.02 |      -0.12 |                -2.6 |     -0.07 |     -0.21 |     -0.05 |
| weather                          |     0    |   0    |       0    |                 1   |      0    |      0    |      0    |
| overtime                         |    -0    |   0.02 |       0.01 |                 1.1 |      0.02 |     -0.01 |      0.03 |
| pace                             |    -0.02 |   0.01 |      -0    |                -0   |     -0.04 |      0.01 |      0.07 |
| penalties                        |     0.02 |   0.04 |       0.03 |                 1.2 |     -0.01 |      0.06 |      0.05 |
| fourth                           |    -0.34 |   0.38 |       0.09 |                 1   |      0.2  |      0.06 |     -0.06 |
| residual                         |    -6.45 |   1.25 |      -1.85 |                -4.4 |     -2    |     -1.46 |     -2.38 |

Under flag:

| Component (pts toward the bet)   |   Losses |   Wins |   All bets |   t (all bets vs 0) |   2015-18 |   2019-22 |   2023-25 |
|:---------------------------------|---------:|-------:|-----------:|--------------------:|----------:|----------:|----------:|
| miss                             |   -13.93 |   6.56 |      -2.7  |                     |     -3.68 |     -1.69 |     -3.06 |
| luck                             |    -1.9  |   1.76 |       0.11 |                 0.5 |      0.09 |      0.46 |     -0.67 |
| turnovers                        |    -0.53 |   0.32 |      -0.06 |                -0.8 |      0.07 |     -0.15 |     -0.14 |
| returns                          |    -0.29 |   0.41 |       0.1  |                 1   |     -0.15 |      0.28 |      0.16 |
| kicks                            |    -0.1  |   0.1  |       0.01 |                 0.2 |      0.07 |      0.06 |     -0.21 |
| garbage                          |    -0.99 |   0.93 |       0.06 |                 0.4 |      0.1  |      0.26 |     -0.48 |
| events                           |    -1.57 |   0.66 |      -0.35 |                -2.2 |     -0.66 |     -0.35 |      0.28 |
| qb_lost                          |    -0.06 |  -0.04 |      -0.05 |                -2.3 |     -0.04 |     -0.06 |     -0.05 |
| weather                          |    -0.1  |  -0.09 |      -0.1  |                -4.4 |     -0.14 |     -0.05 |     -0.12 |
| overtime                         |    -0.11 |   0.12 |       0.02 |                 0.5 |      0.06 |      0.05 |     -0.13 |
| pace                             |    -1.08 |   0.6  |      -0.16 |                -1.2 |     -0    |     -0.42 |      0.15 |
| penalties                        |    -0.06 |   0    |      -0.03 |                -1.9 |     -0.1  |      0    |      0.06 |
| fourth                           |    -0.14 |   0.06 |      -0.03 |                -0.8 |     -0.43 |      0.14 |      0.38 |
| residual                         |   -10.46 |   4.14 |      -2.46 |                -5.9 |     -3.11 |     -1.8  |     -2.67 |

### Losses against wins by situation (spread flag, 2015-2025, sorted by |z| of the win-rate gap)

| Situation                                             |   Bets |   Win% in |   Win% out |     z |   Units in | 2015-18   | 2019-22   | 2023-25   | Lost units all 3   |
|:------------------------------------------------------|-------:|----------:|-----------:|------:|-----------:|:----------|:----------|:----------|:-------------------|
| model's side at home                                  |    188 |     0.532 |      0.693 | -2.86 |        3.2 | 30-42     | 45-32     | 25-14     |                    |
| model's side away                                     |    127 |     0.693 |      0.532 |  2.86 |       45.1 | 38-13     | 35-19     | 15-7      |                    |
| boosted trees on the other side of the line           |      7 |     0.143 |      0.607 | -2.48 |       -5.6 | 0-4       | 1-1       | 0-1       | yes                |
| opponent bottom-quartile rating                       |     76 |     0.711 |      0.561 |  2.32 |       29.8 | 15-8      | 21-7      | 18-7      |                    |
| model's side QB bottom-quartile rating                |     95 |     0.505 |      0.636 | -2.18 |       -3.7 | 17-22     | 23-19     | 8-6       |                    |
| home team under 4 games played this season            |     91 |     0.681 |      0.562 |  1.95 |       30.1 | 23-12     | 20-12     | 19-5      |                    |
| opponent without last game's starting QB              |     16 |     0.375 |      0.609 | -1.86 |       -5   | 3-6       | 2-3       | 1-1       | yes                |
| Weeks 14-17                                           |     66 |     0.5   |      0.622 | -1.8  |       -3.3 | 14-14     | 12-14     | 7-5       |                    |
| opponent out of the race                              |     48 |     0.479 |      0.618 | -1.8  |       -4.5 | 12-13     | 7-10      | 4-2       |                    |
| model's side out of the race (Week 12+, 40% or worse) |     31 |     0.452 |      0.613 | -1.74 |       -4.7 | 3-6       | 9-9       | 2-2       | yes                |
| the seven models disagree (top fifth of spread)       |     80 |     0.525 |      0.621 | -1.52 |        0.2 | 20-20     | 20-15     | 2-3       |                    |
| opponent QB top-quartile rating                       |     69 |     0.522 |      0.618 | -1.44 |       -0.3 | 10-10     | 17-17     | 9-6       |                    |
| Weeks 1-2                                             |     51 |     0.686 |      0.58  |  1.42 |       17.4 | 10-7      | 12-7      | 13-2      |                    |
| the ridge equation alone under 4                      |     36 |     0.694 |      0.584 |  1.27 |       12.9 | 13-6      | 10-2      | 2-3       |                    |
| model's side gets 7+                                  |     90 |     0.544 |      0.618 | -1.2  |        3.9 | 20-16     | 22-20     | 7-5       |                    |
| edge 7+                                               |     21 |     0.476 |      0.605 | -1.17 |       -2.1 | 1-6       | 5-5       | 4-0       |                    |
| model's side is the favourite                         |     62 |     0.532 |      0.613 | -1.16 |        1.1 | 18-17     | 7-9       | 8-3       |                    |
| model's side is the underdog                          |    253 |     0.613 |      0.532 |  1.16 |       47.2 | 50-38     | 73-42     | 32-18     |                    |
| model's side off a bye/long week                      |     32 |     0.688 |      0.587 |  1.1  |       11   | 9-5       | 12-5      | 1-0       |                    |
| model's side top-quartile rating                      |     79 |     0.646 |      0.581 |  1.02 |       20.2 | 15-15     | 19-7      | 17-6      |                    |
| neutral site                                          |     13 |     0.462 |      0.603 | -1.02 |       -1.7 | 1-2       | 1-3       | 4-2       |                    |
| model's side lays exactly 3 or 7                      |     11 |     0.455 |      0.602 | -0.98 |       -1.6 | 1-0       | 4-5       | 0-1       |                    |
| Weeks 3-4                                             |     39 |     0.667 |      0.587 |  0.95 |       11.7 | 13-5      | 7-5       | 6-3       |                    |
| primetime                                             |     67 |     0.552 |      0.609 | -0.84 |        4   | 17-13     | 12-12     | 8-5       |                    |
| Week 17                                               |     25 |     0.52  |      0.603 | -0.82 |       -0.2 | 7-7       | 4-4       | 2-1       |                    |
| season's final regular-season week                    |     21 |     0.524 |      0.602 | -0.71 |       -0   | 7-7       | 4-3       | 0-0       |                    |
| injury inputs move the margin 2+ points               |     40 |     0.55  |      0.604 | -0.65 |        2.2 | 15-10     | 6-7       | 1-1       |                    |
| outdoors, wind 15+ or under 35F                       |     41 |     0.561 |      0.602 | -0.5  |        3.2 | 9-10      | 11-5      | 3-3       |                    |
| opponent top-quartile rating                          |     70 |     0.571 |      0.604 | -0.49 |        7   | 15-11     | 19-10     | 6-9       |                    |
| Weeks 5-8                                             |     75 |     0.573 |      0.604 | -0.48 |        7.8 | 19-13     | 22-11     | 2-8       |                    |
| division game                                         |    119 |     0.58  |      0.607 | -0.48 |       14   | 29-26     | 28-20     | 12-4      |                    |
| model's side on short rest                            |     20 |     0.55  |      0.6   | -0.44 |        1.1 | 5-3       | 4-4       | 2-2       |                    |
| opponent on short rest                                |     20 |     0.55  |      0.6   | -0.44 |        1.1 | 5-3       | 4-4       | 2-2       |                    |
| model's side without last game's starting QB          |      9 |     0.667 |      0.595 |  0.43 |        2.7 | 1-0       | 5-3       | 0-0       |                    |
| edge 4 to 5                                           |    175 |     0.606 |      0.586 |  0.36 |       30.1 | 39-31     | 43-23     | 24-15     |                    |
| model's side bottom-quartile rating                   |     87 |     0.609 |      0.592 |  0.28 |       15.6 | 22-19     | 26-13     | 5-2       |                    |
| edge 5 to 7                                           |    119 |     0.605 |      0.592 |  0.23 |       20.3 | 28-18     | 32-23     | 12-6      |                    |
| Weeks 9-13                                            |     84 |     0.607 |      0.593 |  0.23 |       14.7 | 12-16     | 27-14     | 12-3      |                    |
| edge under 4 without the player-injury inputs         |    107 |     0.589 |      0.601 | -0.21 |       14.6 | 23-19     | 28-19     | 12-6      |                    |
| edge under 4 without the injury inputs and QB-out     |    107 |     0.589 |      0.601 | -0.21 |       14.6 | 23-20     | 28-18     | 12-6      |                    |
| model's side 3+ fewer days' rest                      |     41 |     0.585 |      0.599 | -0.16 |        5.3 | 11-10     | 9-5       | 4-2       |                    |
| model's side lays 7+                                  |     13 |     0.615 |      0.596 |  0.14 |        2.5 | 2-3       | 3-1       | 3-1       |                    |
| model and line on the same side of 3 and 7            |     98 |     0.602 |      0.594 |  0.13 |       16.1 | 21-15     | 23-19     | 15-5      |                    |
| line within a half point of 3 or 7                    |    145 |     0.593 |      0.6   | -0.12 |       21.1 | 32-24     | 30-22     | 24-13     |                    |
| line exactly 3 or 7                                   |     53 |     0.604 |      0.595 |  0.11 |        8.9 | 13-5      | 13-12     | 6-4       |                    |
| dome / closed roof                                    |     85 |     0.6   |      0.596 |  0.07 |       13.6 | 19-15     | 20-11     | 12-8      |                    |
| opponent off a bye/long week                          |     50 |     0.6   |      0.596 |  0.05 |        8   | 12-13     | 13-5      | 5-2       |                    |

### Losses against wins by situation (under flag)

| Situation                                  |   Bets |   Win% in |   Win% out |     z |   Units in | 2015-18   | 2019-22   | 2023-25   | Lost units all 3   |
|:-------------------------------------------|-------:|----------:|-----------:|------:|-----------:|:----------|:----------|:----------|:-------------------|
| Weeks 9-13                                 |    195 |     0.631 |      0.516 |  2.73 |       43.8 | 44-24     | 55-34     | 24-14     |                    |
| primetime                                  |    166 |     0.633 |      0.522 |  2.5  |       37.9 | 41-25     | 45-23     | 19-13     |                    |
| Weeks 3-4                                  |     98 |     0.449 |      0.564 | -2.13 |      -15.4 | 14-24     | 22-22     | 8-8       | yes                |
| home team under 4 games played this season |    206 |     0.49  |      0.573 | -1.99 |      -14.5 | 33-47     | 47-41     | 21-17     |                    |
| a team out of the race                     |    106 |     0.632 |      0.533 |  1.88 |       24.1 | 32-12     | 26-20     | 9-7       |                    |
| under chance 60%+                          |    325 |     0.585 |      0.516 |  1.81 |       41.5 | 64-53     | 102-58    | 24-24     |                    |
| rain                                       |     51 |     0.667 |      0.539 |  1.77 |       15.3 | 3-6       | 22-5      | 9-6       |                    |
| under chance 57-60%                        |    178 |     0.5   |      0.565 | -1.5  |       -8.9 | 31-33     | 41-41     | 17-15     |                    |
| Thursday / short rest                      |     42 |     0.643 |      0.542 |  1.27 |       10.5 | 9-4       | 11-5      | 7-6       |                    |
| total line under 41                        |     35 |     0.457 |      0.553 | -1.11 |       -4.9 | 8-9       | 5-6       | 3-4       | yes                |
| slow expected pace (bottom quartile)       |    117 |     0.504 |      0.557 | -1.05 |       -4.8 | 15-13     | 23-19     | 21-26     |                    |
| both offenses strong (top-quartile sum)    |    214 |     0.519 |      0.561 | -1.04 |       -2.3 | 38-33     | 48-43     | 25-27     |                    |
| Weeks 14-17                                |    121 |     0.512 |      0.556 | -0.87 |       -2.9 | 24-21     | 28-24     | 10-14     |                    |
| neutral site                               |     19 |     0.632 |      0.546 |  0.74 |        4.3 | 4-2       | 4-4       | 4-1       |                    |
| Weeks 1-2                                  |    104 |     0.519 |      0.553 | -0.64 |       -1   | 17-23     | 24-18     | 13-9      |                    |
| outdoors, under 35F                        |     16 |     0.625 |      0.546 |  0.62 |        3.4 | 6-2       | 3-3       | 1-1       |                    |
| under chance 55-57%                        |    192 |     0.531 |      0.555 | -0.55 |        3   | 40-41     | 32-29     | 30-20     |                    |
| Week 17                                    |     25 |     0.6   |      0.546 |  0.53 |        4   | 4-4       | 8-4       | 3-2       |                    |
| both offenses weak (bottom-quartile sum)   |    138 |     0.565 |      0.544 |  0.45 |       12   | 26-24     | 39-25     | 13-11     |                    |
| season's final regular-season week         |     12 |     0.5   |      0.549 | -0.34 |       -0.6 | 4-4       | 2-2       | 0-0       |                    |
| outdoors, wind 15+                         |    103 |     0.534 |      0.551 | -0.31 |        2.2 | 20-17     | 26-22     | 9-9       |                    |
| dome / closed roof                         |    132 |     0.538 |      0.551 | -0.26 |        3.9 | 22-16     | 30-33     | 19-12     |                    |
| total line 50+                             |    209 |     0.555 |      0.545 |  0.24 |       13.7 | 41-32     | 57-49     | 18-12     |                    |
| model total under 40                       |     97 |     0.557 |      0.547 |  0.18 |        6.7 | 21-20     | 25-15     | 8-8       |                    |
| Weeks 5-8                                  |    177 |     0.554 |      0.546 |  0.17 |       11.1 | 36-35     | 46-30     | 16-14     |                    |
| model total 48+                            |    158 |     0.544 |      0.549 | -0.11 |        6.8 | 27-26     | 43-37     | 16-9      |                    |
| fast expected pace (top quartile)          |    227 |     0.546 |      0.549 | -0.07 |       10.7 | 58-48     | 63-52     | 3-3       |                    |
| division game                              |    213 |     0.549 |      0.548 |  0.04 |       11.4 | 54-43     | 49-36     | 14-17     |                    |
| either starting QB out                     |     91 |     0.549 |      0.548 |  0.03 |        4.9 | 23-19     | 22-13     | 5-9       |                    |

## Part 2: the pattern tests

Δu: units of the rule minus units of today's rule in that window. Bets kept: the smallest share of today's bets across the three windows. P(boot better): share of bootstrap resamples (2015-2025) in which the rule's units beat today's. P(random pass): the chance that dropping the same number of today's bets at random in each window improves units on all three windows, i.e. passes the first half of the adoption rule by luck (skip rules only). Adopt: meets the adoption rule as written.

### Spread flag, pre-registered

| Rule                                                                    | 2015-18   |   Δu | 2019-22   |   Δu  | 2023-25   |   Δu   |   Δu all |   P(boot better) | Adopt   | Bets kept   |   P(random pass) |
|:------------------------------------------------------------------------|:----------|-----:|:----------|------:|:----------|-------:|---------:|-----------------:|:--------|:------------|-----------------:|
| cap the injury + QB-out pull on the margin at 1 pts, re-flag every game | 59-45     |  2   | 80-46-1   |   5.5 | 42-22-1   |    0.9 |      8.4 |            0.824 | yes     | 85%         |          nan     |
| cap the player-injury pull on the margin at 1 pts, re-flag every game   | 58-46     | -0.1 | 78-45-1   |   4.6 | 42-21-1   |    2   |      6.5 |            0.802 | no      | 85%         |          nan     |
| skip when the boosted trees disagree                                    | 68-51     |  4.4 | 79-50     |   0.1 | 40-20-1   |    1.1 |      5.6 |            0.987 | yes     | 97%         |            0.131 |
| skip when the opponent is without its starting QB                       | 65-49     |  3.6 | 78-48     |   1.3 | 39-20-1   |    0.1 |      5   |            0.875 | yes     | 93%         |            0.062 |
| skip Weeks 14-17 (the shadowearly rule)                                 | 54-41     |  1.4 | 68-37     |   3.4 | 33-16-1   |   -1.5 |      3.3 |            0.645 | no      | 77%         |            0.008 |
| skip edges of 7+                                                        | 67-49     |  5.6 | 75-46     |   0.5 | 36-21-1   |   -4   |      2.1 |            0.672 | no      | 92%         |            0.052 |
| skip when the model's side lays exactly 3 or 7                          | 67-55     | -1   | 76-46     |   1.5 | 40-20-1   |    1.1 |      1.6 |            0.675 | no      | 93%         |            0.035 |
| skip Week 17 (Weeks 17-18; 18 is already skipped)                       | 61-48     |  0.7 | 76-47     |   0.4 | 38-20-1   |   -0.9 |      0.2 |            0.516 | no      | 89%         |            0.048 |
| skip each season's final regular-season week (Week 17 through 2020)     | 61-48     |  0.7 | 76-48     |  -0.7 | 40-21-1   |    0   |     -0   |            0.507 | no      | 89%         |            0     |
| skip when the seven models disagree most                                | 48-35     |  2   | 60-36     |  -3.5 | 38-18-1   |    1.3 |     -0.2 |            0.49  | no      | 68%         |            0.008 |
| cap the injury + QB-out pull on the margin at 2 pts, re-flag every game | 59-47     | -0.2 | 78-50-1   |  -0.9 | 40-21-1   |    0   |     -1.1 |            0.432 | no      | 86%         |          nan     |
| skip favourites (the shadowdog rule)                                    | 50-38     |  0.7 | 73-42     |   2.9 | 32-18-1   |   -4.7 |     -1.1 |            0.452 | no      | 72%         |            0.011 |
| skip when the model's side lays 7+                                      | 66-52     |  1.3 | 77-50     |  -1.9 | 37-20-1   |   -1.9 |     -2.5 |            0.242 | no      | 94%         |            0.084 |
| skip when the model's side is without its starting QB                   | 67-55     | -1   | 75-48     |  -1.7 | 40-21-1   |    0   |     -2.7 |            0.199 | no      | 94%         |            0     |
| cap the injury + QB-out pull on the margin at 3 pts, re-flag every game | 62-52     | -2.7 | 79-51     |  -1   | 40-21-1   |    0   |     -3.7 |            0.131 | no      | 93%         |          nan     |
| cap the player-injury pull on the margin at 3 pts, re-flag every game   | 63-53     | -2.8 | 79-51     |  -1   | 40-21-1   |    0   |     -3.8 |            0.102 | no      | 94%         |          nan     |
| cap the player-injury pull on the margin at 2 pts, re-flag every game   | 59-51     | -4.6 | 77-50-1   |  -1.9 | 39-22-1   |   -2.1 |     -8.6 |            0.026 | no      | 89%         |          nan     |
| skip when the edge comes only from the player-injury inputs             | 45-36     | -2.1 | 52-32     |  -7.1 | 28-15-1   |   -5.4 |    -14.6 |            0.09  | no      | 64%         |            0.001 |
| skip when the edge comes only from the injury inputs incl. QB-out       | 45-35     | -1   | 52-33     |  -8.2 | 28-15-1   |   -5.4 |    -14.6 |            0.085 | no      | 65%         |            0.002 |
| skip when the edge crosses neither 3 nor 7                              | 47-40     | -4.5 | 57-32     |  -2.1 | 25-16     |   -9.5 |    -16.1 |            0.063 | no      | 66%         |            0.001 |
| skip Weeks 1-2                                                          | 58-48     | -2.3 | 68-44     |  -4.3 | 27-19-1   |  -10.8 |    -17.4 |            0.007 | no      | 76%         |            0.004 |
| drop the injury inputs' pull entirely, re-flag every game               | 58-46     | -0.1 | 75-52-3   |  -6.1 | 38-31-1   |  -13   |    -19.2 |            0.098 | no      | 85%         |          nan     |

### Spread flag, every situation as a filter (top 12 by units gained)

| Rule                                                        | 2015-18   |   Δu | 2019-22   |   Δu  | 2023-25   |   Δu   |   Δu all |   P(boot better) | Adopt   | Bets kept   |   P(random pass) |
|:------------------------------------------------------------|:----------|-----:|:----------|------:|:----------|-------:|---------:|-----------------:|:--------|:------------|-----------------:|
| skip: model's side out of the race (Week 12+, 40% or worse) | 65-49     |  3.6 | 71-42     |   0.9 | 38-19-1   |    0.2 |      4.7 |            0.78  | yes     | 86%         |            0.034 |
| skip: opponent out of the race                              | 56-42     |  2.3 | 73-41     |   4   | 36-19-1   |   -1.8 |      4.5 |            0.735 | no      | 80%         |            0.022 |
| skip: model's side QB bottom-quartile rating                | 51-33     |  7.2 | 57-32     |  -2.1 | 32-15-1   |   -1.4 |      3.7 |            0.647 | no      | 68%         |            0.002 |
| skip: neutral site                                          | 67-53     |  1.2 | 79-48     |   2.3 | 36-19-1   |   -1.8 |      1.7 |            0.672 | no      | 90%         |            0.069 |
| skip: opponent QB top-quartile rating                       | 58-45     |  1   | 63-34     |   1.7 | 31-15-1   |   -2.4 |      0.3 |            0.515 | no      | 74%         |            0.003 |
| skip: opponent on short rest                                | 63-52     | -1.7 | 76-47     |   0.4 | 38-19-1   |    0.2 |     -1.1 |            0.405 | no      | 94%         |            0.082 |
| skip: model's side on short rest                            | 63-52     | -1.7 | 76-47     |   0.4 | 38-19-1   |    0.2 |     -1.1 |            0.402 | no      | 94%         |            0.079 |
| skip: injury inputs move the margin 2+ points               | 53-45     | -4   | 74-44     |   1.7 | 39-20-1   |    0.1 |     -2.2 |            0.365 | no      | 80%         |            0.048 |
| skip: model's side at home                                  | 38-13     | 16.2 | 35-19     |  -9.8 | 15-7      |   -9.6 |     -3.2 |            0.423 | no      | 36%         |            0     |
| skip: outdoors, wind 15+ or under 35F                       | 59-45     |  2   | 69-46     |  -5.5 | 37-18-1   |    0.3 |     -3.2 |            0.316 | no      | 85%         |            0.025 |
| skip: model's side gets 7+                                  | 48-39     | -2.4 | 58-31     |   0   | 33-16-1   |   -1.5 |     -3.9 |            0.348 | no      | 68%         |            0.003 |
| skip: primetime                                             | 51-42     | -2.7 | 68-39     |   1.2 | 32-16-1   |   -2.5 |     -4   |            0.327 | no      | 76%         |            0.006 |

### Under flag, pre-registered

| Rule                            | 2015-18   |    Δu | 2019-22   |   Δu  | 2023-25   |   Δu   |   Δu all |   P(boot better) | Adopt   | Bets kept   |   P(random pass) |
|:--------------------------------|:----------|------:|:----------|------:|:----------|-------:|---------:|-----------------:|:--------|:------------|-----------------:|
| raise the under cut to 60%      | 64-53-1   |  10.4 | 102-58-1  |   4   | 24-24     |   -8.5 |      5.9 |            0.609 | no      | 37%         |          nan     |
| skip Weeks 14-17                | 111-106-3 |  -0.9 | 147-104-3 |  -1.6 | 61-45-1   |    5.4 |      2.9 |            0.607 | no      | 82%         |            0.045 |
| raise the under cut to 58%      | 83-72-2   |   8.5 | 125-84-3  |  -1.6 | 35-31     |   -5.2 |      1.7 |            0.545 | no      | 50%         |          nan     |
| skip Weeks 1-2                  | 118-104-3 |   8.3 | 151-110-4 |  -4.2 | 58-50-1   |   -3.1 |      1   |            0.532 | no      | 83%         |            0.04  |
| skip each season's final week   | 131-123-3 |   0.4 | 173-126-4 |   0.2 | 71-59-1   |    0   |      0.6 |            0.554 | no      | 97%         |            0     |
| skip wind 15+                   | 115-110-2 |  -1.3 | 149-106-4 |  -1.8 | 62-50-1   |    0.9 |     -2.2 |            0.428 | no      | 84%         |            0.047 |
| raise the under cut to 57%      | 95-86-2   |   5.1 | 143-99-3  |  -0.1 | 41-39     |   -8   |     -3   |            0.425 | no      | 61%         |          nan     |
| skip domes                      | 113-111-3 |  -4.4 | 145-95-2  |   6.3 | 52-47-1   |   -5.8 |     -3.9 |            0.37  | no      | 76%         |            0.036 |
| skip Week 17                    | 131-123-3 |   0.4 | 167-124-4 |  -3.6 | 68-57-1   |   -0.8 |     -4   |            0.229 | no      | 96%         |            0.095 |
| skip when either starter is out | 112-108-3 |  -2.1 | 153-115-4 |  -7.7 | 66-50-1   |    4.9 |     -4.9 |            0.311 | no      | 84%         |            0.057 |
| raise the under cut to 56%      | 115-103-2 |   6.4 | 159-114-4 |  -0.6 | 52-52     |  -11.3 |     -5.5 |            0.303 | no      | 79%         |          nan     |
| skip total lines 50+            | 94-95-2   |  -5.8 | 118-79-1  |  -3.1 | 53-47-1   |   -4.8 |    -13.7 |            0.184 | no      | 64%         |            0.019 |
| skip primetime                  | 94-102-3  | -13.5 | 130-105-3 | -19.7 | 52-46-1   |   -4.7 |    -37.9 |            0.002 | no      | 75%         |            0.034 |

### Under flag, every situation as a filter (top 12 by units gained)

| Rule                                             | 2015-18   |   Δu | 2019-22   |   Δu  | 2023-25   |   Δu   |   Δu all |   P(boot better) | Adopt   | Bets kept   |   P(random pass) |
|:-------------------------------------------------|:----------|-----:|:----------|------:|:----------|-------:|---------:|-----------------:|:--------|:------------|-----------------:|
| skip: Weeks 3-4                                  | 121-103-3 | 12.4 | 153-106-2 |   2.2 | 63-51-1   |    0.8 |     15.4 |            0.932 | yes     | 85%         |            0.052 |
| skip: home team under 4 games played this season | 102-80-3  | 18.7 | 128-87-2  |  -1.9 | 50-42-1   |   -2.3 |     14.5 |            0.831 | no      | 70%         |            0.022 |
| skip: under chance 57-60%                        | 104-94-2  |  5.3 | 134-87-2  |   4.1 | 54-44-1   |   -0.5 |      8.9 |            0.739 | no      | 73%         |            0.023 |
| skip: total line under 41                        | 127-118-3 |  1.9 | 170-122-4 |   1.6 | 68-55-1   |    1.4 |      4.9 |            0.779 | yes     | 94%         |            0.06  |
| skip: slow expected pace (bottom quartile)       | 120-114-3 | -0.7 | 152-109-2 |  -2.1 | 50-33-1   |    7.6 |      4.8 |            0.663 | no      | 64%         |            0.046 |
| skip: both offenses strong (top-quartile sum)    | 97-94-2   | -1.7 | 127-85-3  |  -0.7 | 46-32     |    4.7 |      2.3 |            0.558 | no      | 60%         |            0.021 |
| skip: under chance 55-57%                        | 95-86-2   |  5.1 | 143-99-3  |  -0.1 | 41-39     |   -8   |     -3   |            0.432 | no      | 61%         |            0.031 |
| skip: outdoors, under 35F                        | 129-125-3 | -3.8 | 172-125-4 |   0.3 | 70-58-1   |    0.1 |     -3.4 |            0.197 | no      | 97%         |            0.201 |
| skip: neutral site                               | 131-125-3 | -1.8 | 171-124-4 |   0.4 | 67-58-1   |   -2.9 |     -4.3 |            0.173 | no      | 96%         |            0.119 |
| skip: model total under 40                       | 114-107-3 |  1   | 150-113-4 |  -8.5 | 63-51-1   |    0.8 |     -6.7 |            0.255 | no      | 84%         |            0.047 |
| skip: model total 48+                            | 108-101-2 |  1.6 | 132-91-1  |  -2.3 | 55-50-1   |   -6.1 |     -6.8 |            0.302 | no      | 73%         |            0.031 |
| skip: Thursday / short rest                      | 126-123-3 | -4.6 | 164-123-4 |  -5.5 | 64-53-1   |   -0.4 |    -10.5 |            0.061 | no      | 90%         |            0.059 |

### Rules that improved units on all three windows

| kind   | rule                | label                                                                   | source          | rec_2015-18   |   d_units_2015-18 | rec_2019-22   |   d_units_2019-22 | rec_2023-25   |   d_units_2023-25 |   bets_share_2015-18 |   bets_share_2019-22 |   bets_share_2023-25 |   p_boot_better_all |   p_random_pass | adopt   |
|:-------|:--------------------|:------------------------------------------------------------------------|:----------------|:--------------|------------------:|:--------------|------------------:|:--------------|------------------:|---------------------:|---------------------:|---------------------:|--------------------:|----------------:|:--------|
| spread | skip_opp_qb_out     | skip when the opponent is without its starting QB                       | pre-registered  | 65-49         |               3.6 | 78-48         |               1.3 | 39-20-1       |               0.1 |                0.927 |                0.962 |                0.968 |               0.875 |           0.062 | True    |
| spread | skip_trees_disagree | skip when the boosted trees disagree                                    | pre-registered  | 68-51         |               4.4 | 79-50         |               0.1 | 40-20-1       |               1.1 |                0.967 |                0.985 |                0.984 |               0.987 |           0.131 | True    |
| spread | skip_side_dead      | skip: model's side out of the race (Week 12+, 40% or worse)             | every situation | 65-49         |               3.6 | 71-42         |               0.9 | 38-19-1       |               0.2 |                0.927 |                0.863 |                0.935 |               0.78  |           0.034 | True    |
| spread | cap_injq_1          | cap the injury + QB-out pull on the margin at 1 pts, re-flag every game | pre-registered  | 59-45         |               2   | 80-46-1       |               5.5 | 42-22-1       |               0.9 |                0.846 |                0.969 |                1.048 |               0.824 |         nan     | True    |
| under  | skip_wk3_4          | skip: Weeks 3-4                                                         | every situation | 121-103-3     |              12.4 | 153-106-2     |               2.2 | 63-51-1       |               0.8 |                0.857 |                0.85  |                0.878 |               0.932 |           0.052 | True    |
| under  | skip_line_u41       | skip: total line under 41                                               | every situation | 127-118-3     |               1.9 | 170-122-4     |               1.6 | 68-55-1       |               1.4 |                0.936 |                0.964 |                0.947 |               0.779 |           0.06  | True    |

Spread: 47 skip rules scored; 3 improved units on all three windows; dropping the same numbers of bets at random would pass that test 1.0 times in expectation. Meeting the full rule (with the 80% volume floor): 3 observed against 0.8 expected by chance.

Under: 29 skip rules scored; 2 improved units on all three windows; dropping the same numbers of bets at random would pass that test 1.4 times in expectation. Meeting the full rule (with the 80% volume floor): 2 observed against 0.9 expected by chance.

## A data problem the postmortem turned up: the listed starter who did not play

The model's QB input is the schedule's starter (`games.parquet` home_qb_id / away_qb_id, from nflverse). In some games that QB took no dropback at all (`qb_games.parquet`), so the game was priced with a quarterback who did not play. Team-games per season where the listed starter had zero dropbacks:

2015: 0, 2016: 0, 2017: 0, 2018: 0, 2019: 0, 2020: 0, 2021: 0, 2022: 4, 2023: 0, 2024: 33, 2025: 7, 2026: 1

2024 (Weeks 8-18) holds most of them: Mariota listed for Washington while Daniels played, Dalton for Carolina while Young played, Rudolph, Flacco, O'Connell, DeVito and others; 2025 has Tyrod Taylor listed for the Jets in games Fields or Cook started. These are not in-game losses (they are kept out of the QB-lost component) and they were knowable before kickoff. Bets touched:

| game_id         | kind   | bet        | win   |   units |   miss |
|:----------------|:-------|:-----------|:------|--------:|-------:|
| 2024_08_ARI_MIA | spread | ARI +4     | True  |     1   |   -0.9 |
| 2024_10_NYG_CAR | spread | CAR +6.5   | True  |     1   |    4.1 |
| 2025_10_CLE_NYJ | spread | NYJ +1.5   | True  |     1   |    2.4 |
| 2025_11_NYJ_NE  | spread | NYJ +12.5  | False |    -1.1 |   -6.5 |
| 2025_16_NYJ_NO  | spread | NYJ +6.5   | False |    -1.1 |  -20.8 |
| 2025_17_NE_NYJ  | spread | NYJ +12.5  | False |    -1.1 |  -23.8 |
| 2026_02_CAR_ATL | spread | ATL +2.5   | False |    -1.1 |  -36.9 |
| 2022_11_PHI_IND | under  | Under 45.5 | True  |     1   |    9.2 |
| 2024_08_ARI_MIA | under  | Under 46.5 | False |    -1.1 |  -15.1 |
| 2024_11_WAS_PHI | under  | Under 49.5 | True  |     1   |    1.9 |
| 2024_12_DET_IND | under  | Under 50.5 | True  |     1   |   17.9 |
| 2024_13_IND_NE  | under  | Under 41.5 | False |    -1.1 |   -8.9 |
| 2024_14_CAR_PHI | under  | Under 44.5 | True  |     1   |    5.1 |
| 2024_14_LV_TB   | under  | Under 47   | True  |     1   |    4.6 |
| 2024_16_NO_GB   | under  | Under 44   | True  |     1   |    8.2 |
| 2025_08_BUF_CAR | under  | Under 47.5 | False |    -1.1 |   -3.3 |
| 2025_08_WAS_KC  | under  | Under 48.5 | True  |     1   |   12.2 |
| 2025_10_CLE_NYJ | under  | Under 37.5 | False |    -1.1 |  -11.3 |

Record on those bets: 10-8, +1.2 units. Small money, but the fix belongs in the data (the starter should be the QB who took the snaps for played games, and the announced starter for coming ones), not in a filter.

## Verdict

Meet the adoption rule as written (87 rules scored): spread: skip when the opponent is without its starting QB; spread: skip when the boosted trees disagree; spread: skip: model's side out of the race (Week 12+, 40% or worse); spread: cap the injury + QB-out pull on the margin at 1 pts, re-flag every game; under: skip: Weeks 3-4; under: skip: total line under 41.

**6 rules meet the letter of the adoption rule; none should be adopted.** The rule is a necessary condition ("adopted only if"), and
what passes it here looks like what random filters would do:

- Each passing skip rule drops 1 to 46 bets per window. Its gain on the held-out 2023-25 is 0.1 to
  1.4 units, one or two bets. Dropping the same number of bets at random passes the all-three-windows test
  3% to 13% of the time for each of them (P(random pass)). Across the
  76 skip rules scored, 5 passed against 2.3 expected by chance, and the rules overlap, so they are not 76
  independent tries. 3 of the 6 were found by looking (every situation turned into a filter), not named in advance.
- The injury cap passes at 1 point (+2.0 / +5.5 / +0.9 units) and fails at 2 points
  (-0.2 / -0.9 / +0.0) and at 3 (-2.7 / -1.0 / +0.0).
  A real overreaction would show a dose response, and this has none. The injury-only skip, the brief's own suggestion, loses on every window
  (the injury inputs earn their place).
- "Skip total lines under 41" reads the market total. The model-total version of the same idea fails.
- The brief's named candidates all fail: skip laying 7+ (+1.3 / -1.9 / -1.9), skip Weeks 1-2 (-2.3 / -4.3 / -10.8; the early weeks are the
  flag's best stretch), skip Week 17 (+0.7 / +0.4 / -0.9), skip the season's final week (+0.7 / -0.7 / 0), and every injury cap but the 1-point one.

`nflmodel/picks.py` should stay as it is. If the rule is applied to the letter anyway, the change is:

```python
# rule_mask(), spread branch, and the same tests in table().bet():
m &= ~((np.sign(d.home_m_trees - d.away_m_trees - d.spread_line) != np.sign(e)))      # skip when the boosted trees disagree
m &= ~np.where(e > 0, d.away_qb_out, d.home_qb_out).astype(bool)                       # skip when the opponent's starting QB is out
m &= ~np.where(e > 0, d.home_dead_late, d.away_dead_late).astype(bool)                 # skip when the model's side is out of the race
# (home/away qb_out and dead_late are not in pred_v3 today; walk_forward would have to write them)
# under_prob branch:
return ((1 - d.p_over_emp) >= edge) & (d.week <= LAST_BET_WEEK) & ~d.week.between(3, 4) & (d.total_line >= 41) & d.total_line.notna()
```

plus the 1-point cap on the injury inputs' pull, which changes the model's spread itself (model.py, not picks.py).

**What the losses tell us instead.** Most of the damage is the game, not a pattern: the four luck components flip 39% of the spread losses
(56% of the points), and the model's side covers 212-104 instead of 188-127 without them. That figure leans on the brief's garbage-time
definition, though. The garbage points that hurt are the favourite piling on while the model's underdog is being blown out, which is
being outplayed. Counted as backdoor points only, luck explains 13% of the losses. Three things are systematic and are not luck:

1. **The model's edge is about half real.** On the 4+ bets the average edge is 5.2 points and the average cover is
   +2.5, so the residual is negative on every window (t = -4.4 on the spread, -5.9 on the unders). The line holds the rest.
   The cut already allows for this, and it is not a filter.
2. **The model's side loses its starting QB in the game far more often than the opponent does:** 19 times against
   6 over 2015-25 (binomial p = 0.015; the base rate is about 4.4% of team-games for each side). Those bets went
   6-13. The model mostly backs underdogs, and their quarterbacks get hurt or benched.
   No pre-game input tried here predicts it (the model's side with a bottom-quartile QB rating, or without last week's starter, does not
   lose units on every window), so it stays a finding, not a rule.
3. **The listed starter who did not play** (section above) is a data error in the QB input, mostly 2024 Weeks 8-18. It cost little on the
   bets (10-8), but it feeds every 2024-25 prediction and the training rows. It should be fixed in the data build, not filtered.

The under flag's losses are mostly ordinary variance. Luck is neutral there: the record with luck taken out is 382-321, against 381-314
actual. The one systematic component is small: the realised kickoff wind comes in under the model's input on the games it bets under
(-0.1 points, t = -4.4). That is the selection effect of betting unders on high reported wind.

## This season's recorded picks (data/tracker)

Graded:

| game_id         | who         | bet        | result   |   units |   model_total |   actual_total |   miss |   cover |   espn_return_tds |   espn_turnovers |   espn_pts_off_to |   espn_missed_fg |   espn_ot_pts | espn_note                         |
|:----------------|:------------|:-----------|:---------|--------:|--------------:|---------------:|-------:|--------:|------------------:|-----------------:|------------------:|-----------------:|--------------:|:----------------------------------|
| 2026_03_LAC_BUF | shadowunder | Under 50.5 | win      |    0.91 |         47.89 |             40 |   7.89 |    10.5 |                 0 |                6 |                17 |                1 |             0 |                                   |
| 2026_03_NE_JAX  | shadowunder | Under 46.5 | win      |    0.91 |         44.23 |             41 |   3.23 |     5.5 |                 0 |                4 |                17 |                2 |             0 |                                   |
| 2026_03_LA_DEN  | shadowunder | Under 44.5 | loss     |   -1    |         43.32 |             56 | -12.68 |   -11.5 |                 1 |                3 |                10 |                1 |             0 | Interception Return Touchdown DEN |

Pending (Week 4): model WAS +3.5 (2026_04_IND_WAS), model JAX +2.5 (2026_04_JAX_CIN), model NYG +1.5 (2026_04_ARI_NYG), model TB +3.5 (2026_04_GB_TB), shadowunder Under 48.5 (2026_04_NE_BUF), shadowunder Under 51.5 (2026_04_JAX_CIN), shadowunder Under 42.5 (2026_04_LAC_SEA), shadowunder Under 48.5 (2026_04_ATL_NO).

The 2026 play-by-play reaches Week 2 only, so the graded Week 3 unders are read from the ESPN game summaries in `data/results` (return TDs, turnovers and the points after them, missed field goals, overtime). The backtest rule's 2026 bets (Weeks 1-3, schedule line) are in the CSV with window 2026.

Backtest-rule bets in 2026 so far:

| game_id         | kind   | bet        | win   | push   |   miss |   luck |   residual | reason                                                                          |
|:----------------|:-------|:-----------|:------|:-------|-------:|-------:|-----------:|:--------------------------------------------------------------------------------|
| 2026_01_DEN_KC  | spread | DEN +2.5   | False | False  |  -23   |   -5.8 |      -13.1 | garbage time (-5.4); fourth downs (-4.2); and outplayed (-13.1)                 |
| 2026_02_CAR_ATL | spread | ATL +2.5   | False | False  |  -36.9 |  -30.2 |       -6.6 | model priced a QB who did not play; garbage time (-14.6); turnovers 5-0 (-14.1) |
| 2026_03_CAR_CLE | spread | CLE +2.5   | True  | False  |    1.4 |  nan   |        1.4 | no play-by-play yet                                                             |
| 2026_01_NE_SEA  | under  | Under 44.5 | True  | False  |   19.1 |    3.6 |       10.4 | covered anyway (miss +19.1 inside the edge)                                     |
| 2026_01_CHI_CAR | under  | Under 47.5 | False | False  |  -51.2 |   -8.3 |      -38.6 | garbage time (-5.7); pace (-3.7); and outplayed (-38.6)                         |
| 2026_01_NO_DET  | under  | Under 49.5 | False | False  |  -13.5 |   -4.2 |       13.8 | pace (-15.0); overtime (-7.5)                                                   |
| 2026_02_DET_BUF | under  | Under 54.5 | False | False  |  -19.2 |  -12.1 |       -5.1 | garbage time (-15.6)                                                            |
| 2026_02_MIN_CHI | under  | Under 46.5 | True  | False  |   30.9 |    6.1 |       22.5 | covered anyway (miss +30.9 inside the edge)                                     |
| 2026_02_GB_NYJ  | under  | Under 44.5 | True  | False  |    5.5 |    4   |        7   | covered anyway; overtime (-3.4)                                                 |
| 2026_02_JAX_DEN | under  | Under 45.5 | True  | False  |   10.1 |    4   |        3   | covered anyway (miss +10.1 inside the edge)                                     |
| 2026_02_IND_KC  | under  | Under 46.5 | False | False  |  -18.5 |    3.3 |       -7.1 | pace (-8.6); overtime (-6.9)                                                    |
| 2026_03_LAC_BUF | under  | Under 50.5 | True  | False  |    7.9 |  nan   |        7.9 | no play-by-play yet                                                             |
| 2026_03_NE_JAX  | under  | Under 46.5 | True  | False  |    3.2 |  nan   |        3.2 | no play-by-play yet                                                             |
| 2026_03_MIN_TB  | under  | Under 42.5 | True  | False  |    2.5 |  nan   |        2.5 | no play-by-play yet                                                             |

## The ten worst misses per season

Miss: actual minus the model, signed toward the bet. Model: the model's home margin (spread bets) or total (unders). Reason: the one or two luck or event components that cost 3+ points toward the bet (points in brackets), and 'outplayed' where the residual after them is 8+ points; 'outplayed, no luck' when nothing in the game explains a big miss. A season with few losses fills its ten with its smallest wins.

### Spread flag

|   Season |   Wk | Game      | Bet       | Final   |   Model |   Miss | Result   | Reason                                                                                 |
|---------:|-----:|:----------|:----------|:--------|--------:|-------:|:---------|:---------------------------------------------------------------------------------------|
|     2015 |   16 | NYG @ MIN | NYG +7    | 17-49   |     2.7 |  -29.3 | L        | garbage time (-13.6); turnovers 3-0 (-9.5)                                             |
|     2015 |   14 | SEA @ BAL | BAL +10.5 | 35-6    |    -6.1 |  -22.9 | L        | garbage time (-14.6)                                                                   |
|     2015 |    1 | CLE @ NYJ | CLE +3.5  | 10-31   |    -0.5 |  -21.5 | L        | turnovers 4-1 (-10.2); garbage time (-8.1)                                             |
|     2015 |    5 | NE @ DAL  | DAL +8    | 30-6    |    -3.1 |  -20.9 | L        | garbage time (-13.7); turnovers 2-0 (-5.3)                                             |
|     2015 |    7 | HOU @ MIA | HOU +4.5  | 26-44   |     0.4 |  -17.6 | L        | outplayed, no luck (residual -17.8)                                                    |
|     2015 |   12 | CHI @ GB  | GB -7.5   | 17-13   |    12   |  -16   | L        | turnovers 2-0 (-3.8); and outplayed (-9.9)                                             |
|     2015 |    3 | LV @ CLE  | CLE -3.5  | 27-20   |     8.6 |  -15.6 | L        | outplayed, no luck (residual -19.3)                                                    |
|     2015 |    9 | CHI @ LAC | LAC -3.5  | 22-19   |    11.2 |  -14.2 | L        | outplayed, no luck (residual -20.3)                                                    |
|     2015 |    6 | BAL @ SF  | BAL -2.5  | 20-25   |    -7.2 |  -12.2 | L        | turnovers 2-0 (-5.5); and outplayed (-17.3)                                            |
|     2015 |   11 | IND @ ATL | ATL -3.5  | 24-21   |     8.6 |  -11.6 | L        | outplayed, no luck (residual -8.7)                                                     |
|     2016 |   17 | DAL @ PHI | DAL +6.5  | 13-27   |    -3   |  -17   | L        | garbage time (-5.4); turnovers 2-0 (-5.1)                                              |
|     2016 |    8 | NE @ BUF  | BUF +5.5  | 41-25   |    -0.9 |  -15.1 | L        | garbage time (-5.5); and outplayed (-9.8)                                              |
|     2016 |    5 | NE @ CLE  | CLE +10   | 33-13   |    -5.9 |  -14.1 | L        | garbage time (-4.6); QB lost in game (21% of dropbacks) (-3.0)                         |
|     2016 |   12 | LAC @ HOU | HOU +2.5  | 21-13   |     5.4 |  -13.4 | L        | turnovers 4-1 (-5.0); and outplayed (-10.3)                                            |
|     2016 |    5 | ARI @ SF  | SF +3.5   | 33-21   |     0.7 |  -12.7 | L        | turnovers 3-0 (-7.9)                                                                   |
|     2016 |    7 | NYG @ LA  | LA +3     | 17-10   |     2.2 |   -9.2 | L        | turnovers 4-1 (-8.1)                                                                   |
|     2016 |   17 | CLE @ PIT | PIT -3.5  | 24-27   |    11.2 |   -8.2 | L        | garbage time (-3.7); and outplayed (-14.2)                                             |
|     2016 |    1 | BUF @ BAL | BUF +3    | 7-13    |    -1.1 |   -7.1 | L        | outplayed, no luck (residual -11.0)                                                    |
|     2016 |   15 | JAX @ HOU | HOU -3.5  | 20-21   |     7.6 |   -6.6 | L        | turnovers 2-1 (-4.0); return TD (-3.8)                                                 |
|     2016 |   10 | HOU @ JAX | HOU +3    | 24-21   |    -1.1 |    1.9 | W        | covered anyway; garbage time (-4.5)                                                    |
|     2017 |   15 | LA @ SEA  | SEA +1    | 42-7    |     4.1 |  -39.1 | L        | garbage time (-21.0); turnovers 2-1 (-3.1); and outplayed (-16.0)                      |
|     2017 |    9 | LA @ NYG  | NYG +5.5  | 51-17   |     0.1 |  -34.1 | L        | garbage time (-16.5); turnovers 3-0 (-6.4); and outplayed (-8.7)                       |
|     2017 |   11 | PHI @ DAL | DAL +6    | 37-9    |     0.9 |  -28.9 | L        | turnovers 4-0 (-9.6); garbage time (-8.3); and outplayed (-10.6)                       |
|     2017 |   17 | SF @ LA   | LA +6.5   | 34-13   |     5.2 |  -26.2 | L        | garbage time (-7.4); and outplayed (-21.3)                                             |
|     2017 |   12 | LAC @ DAL | DAL +1    | 28-6    |     3.3 |  -25.3 | L        | turnovers 2-0 (-8.3); and outplayed (-18.2)                                            |
|     2017 |    4 | IND @ SEA | IND +12.5 | 18-46   |     8   |  -20   | L        | garbage time (-12.7)                                                                   |
|     2017 |   10 | HOU @ LA  | HOU +12   | 7-33    |     6.1 |  -19.9 | L        | garbage time (-14.5); turnovers 4-0 (-10.1)                                            |
|     2017 |   15 | CIN @ MIN | CIN +12.5 | 7-34    |     8.3 |  -18.7 | L        | garbage time (-8.1)                                                                    |
|     2017 |    2 | NYJ @ LV  | NYJ +14   | 20-45   |     7.9 |  -17.1 | L        | garbage time (-9.0); turnovers 2-0 (-5.9)                                              |
|     2017 |    6 | LA @ JAX  | JAX -1    | 27-17   |     7   |  -17   | L        | return TD (-4.0); kicks (2 FG missed, 1 blocked) (-4.0)                                |
|     2018 |   14 | NYG @ WAS | WAS +3    | 40-16   |     3   |  -27   | L        | garbage time (-7.4); turnovers 3-1 (-6.7)                                              |
|     2018 |    2 | ARI @ LA  | ARI +13.5 | 0-34    |     7.9 |  -26.1 | L        | garbage time (-19.9)                                                                   |
|     2018 |   17 | PHI @ WAS | WAS +6    | 24-0    |    -1.2 |  -22.8 | L        | garbage time (-13.7); and outplayed (-10.1)                                            |
|     2018 |    1 | LA @ LV   | LV +6     | 33-13   |    -0   |  -20   | L        | turnovers 3-0 (-8.7); garbage time (-4.6)                                              |
|     2018 |   12 | CLE @ CIN | CIN +1    | 35-20   |     4.9 |  -19.9 | L        | turnovers 2-0 (-5.0); QB lost in game (35% of dropbacks) (-3.0); and outplayed (-14.7) |
|     2018 |    1 | KC @ LAC  | LAC -3.5  | 38-28   |     7.6 |  -17.6 | L        | turnovers 2-0 (-5.5); return TD (-4.4); and outplayed (-8.4)                           |
|     2018 |   16 | LA @ ARI  | ARI +14.5 | 31-9    |   -10.5 |  -11.5 | L        | garbage time (-10.1)                                                                   |
|     2018 |   10 | MIA @ GB  | MIA +13   | 12-31   |     8   |  -11   | L        | garbage time (-8.1); turnovers 2-1 (-4.3)                                              |
|     2018 |    8 | NE @ BUF  | BUF +13.5 | 25-6    |    -8.7 |  -10.3 | L        | turnovers 2-0 (-7.6); garbage time (-7.4)                                              |
|     2018 |   13 | LA @ DET  | DET +10.5 | 30-16   |    -5.4 |   -8.6 | L        | garbage time (-5.5)                                                                    |
|     2019 |    1 | BAL @ MIA | MIA +7    | 59-10   |    -1   |  -48   | L        | garbage time (-26.5); turnovers 3-0 (-7.1); and outplayed (-11.4)                      |
|     2019 |    2 | NE @ MIA  | MIA +18   | 43-0    |   -11.1 |  -31.9 | L        | garbage time (-17.4); turnovers 4-1 (-10.2)                                            |
|     2019 |   17 | TEN @ HOU | HOU +10   | 35-14   |    -1.2 |  -19.8 | L        | garbage time (-13.7)                                                                   |
|     2019 |    2 | CLE @ NYJ | NYJ +6.5  | 23-3    |    -0.8 |  -19.2 | L        | garbage time (-7.4); QB lost in game (23% of dropbacks) (-3.0)                         |
|     2019 |   11 | PIT @ CLE | PIT +3    | 7-21    |    -1.5 |  -15.5 | L        | turnovers 4-0 (-9.8); garbage time (-5.4)                                              |
|     2019 |   17 | NYJ @ BUF | BUF +1.5  | 13-6    |     8.4 |  -15.4 | L        | turnovers 3-1 (-4.8); and outplayed (-11.5)                                            |
|     2019 |   11 | BUF @ MIA | MIA +7    | 37-20   |    -2.2 |  -14.8 | L        | garbage time (-8.3)                                                                    |
|     2019 |   12 | MIA @ CLE | MIA +11   | 24-41   |     5.9 |  -11.1 | L        | outplayed, no luck (residual -8.7)                                                     |
|     2019 |    3 | MIA @ DAL | MIA +22   | 6-31    |    17.2 |   -7.8 | L        | garbage time (-11.7)                                                                   |
|     2019 |    9 | CHI @ PHI | CHI +5    | 14-22   |     1   |   -7   | L        | nothing stands out: ordinary miss (residual -2.7)                                      |
|     2020 |   16 | TB @ DET  | DET +12   | 47-7    |    -7   |  -33   | L        | garbage time (-31.0); turnovers 2-0 (-5.0)                                             |
|     2020 |   16 | BUF @ NE  | NE +7     | 38-9    |    -2.6 |  -26.4 | L        | garbage time (-13.7); fourth downs (-3.4)                                              |
|     2020 |   14 | NYJ @ SEA | NYJ +16.5 | 3-40    |    10.9 |  -26.1 | L        | garbage time (-19.9); kicks (3 FG missed, 0 blocked) (-3.1)                            |
|     2020 |   12 | NO @ DEN  | DEN +17   | 31-3    |    -6.6 |  -21.4 | L        | garbage time (-13.7); turnovers 3-1 (-4.2)                                             |
|     2020 |   17 | LAC @ KC  | KC +7     | 38-21   |     2.8 |  -19.8 | L        | outplayed, no luck (residual -14.6)                                                    |
|     2020 |    9 | GB @ SF   | SF +6     | 34-17   |    -1.6 |  -15.4 | L        | turnovers 2-0 (-5.2)                                                                   |
|     2020 |    5 | CAR @ ATL | ATL -2.5  | 23-16   |     7.7 |  -14.7 | L        | outplayed, no luck (residual -12.2)                                                    |
|     2020 |    5 | IND @ CLE | IND +1    | 23-32   |    -4   |  -13   | L        | outplayed, no luck (residual -15.3)                                                    |
|     2020 |    8 | DAL @ PHI | DAL +10   | 9-23    |     3.7 |  -10.3 | L        | outplayed, no luck (residual -11.7)                                                    |
|     2020 |   10 | HOU @ CLE | HOU +4.5  | 7-10    |     0.2 |   -2.8 | W        | covered anyway (miss -2.8 inside the edge)                                             |
|     2021 |   16 | TB @ CAR  | CAR +11.5 | 32-6    |    -7.2 |  -18.8 | L        | garbage time (-12.8)                                                                   |
|     2021 |    1 | DEN @ NYG | NYG +3    | 27-13   |     2.9 |  -16.9 | L        | garbage time (-4.6); fourth downs (-4.1)                                               |
|     2021 |   12 | NYJ @ HOU | HOU -3    | 21-14   |     8.9 |  -15.9 | L        | outplayed, no luck (residual -11.1)                                                    |
|     2021 |    7 | HOU @ ARI | HOU +20.5 | 5-31    |    15.5 |  -10.5 | L        | garbage time (-11.7)                                                                   |
|     2021 |   17 | HOU @ SF  | HOU +14   | 7-23    |     7   |   -9   | L        | garbage time (-4.5)                                                                    |
|     2021 |    7 | DEN @ CLE | DEN +2    | 14-17   |    -4.6 |   -7.6 | L        | nothing stands out: ordinary miss (residual -7.4)                                      |
|     2021 |    2 | SF @ PHI  | PHI +3    | 17-11   |     1.4 |   -7.4 | L        | outplayed, no luck (residual -8.5)                                                     |
|     2021 |   16 | JAX @ NYJ | JAX +2.5  | 21-26   |    -2.1 |   -7.1 | L        | turnovers 1-0 (-3.8); return TD (-3.5)                                                 |
|     2021 |    2 | HOU @ CLE | HOU +13.5 | 21-31   |     3.7 |   -6.3 | W        | covered anyway; QB lost in game (36% of dropbacks) (-3.0)                              |
|     2021 |   13 | TB @ ATL  | ATL +11   | 30-17   |    -7   |   -6   | L        | garbage time (-3.7)                                                                    |
|     2022 |    5 | MIA @ NYJ | MIA -3    | 17-40   |    -7.4 |  -30.4 | L        | garbage time (-11.7); turnovers 2-0 (-5.2); and outplayed (-9.3)                       |
|     2022 |   14 | TB @ SF   | TB +3.5   | 7-35    |    -0.7 |  -28.7 | L        | garbage time (-6.3); turnovers 3-1 (-5.0); and outplayed (-16.4)                       |
|     2022 |    5 | PIT @ BUF | PIT +14   | 3-38    |    10   |  -25   | L        | garbage time (-18.1)                                                                   |
|     2022 |   11 | SF @ ARI  | ARI +10   | 38-10   |    -4.1 |  -23.9 | L        | garbage time (-13.7); turnovers 2-0 (-4.1)                                             |
|     2022 |   14 | JAX @ TEN | TEN -3    | 36-22   |     8.6 |  -22.6 | L        | turnovers 4-0 (-10.0); and outplayed (-9.8)                                            |
|     2022 |    8 | SF @ LA   | LA +1     | 31-14   |     5.2 |  -22.2 | L        | garbage time (-7.4); and outplayed (-15.3)                                             |
|     2022 |    2 | SEA @ SF  | SEA +8.5  | 7-27    |     1.8 |  -18.2 | L        | garbage time (-16.3); turnovers 3-0 (-6.5)                                             |
|     2022 |    5 | NYG @ GB  | GB -8.5   | 27-22   |    13   |  -18   | L        | outplayed, no luck (residual -20.9)                                                    |
|     2022 |   16 | NO @ CLE  | CLE -3    | 17-10   |    10.6 |  -17.6 | L        | outplayed, no luck (residual -15.4)                                                    |
|     2022 |    1 | TB @ DAL  | DAL +2.5  | 19-3    |     1.5 |  -17.5 | L        | garbage time (-7.4); and outplayed (-10.3)                                             |
|     2023 |    3 | HOU @ JAX | JAX -7.5  | 37-17   |    12.7 |  -32.7 | L        | garbage time (-12.8); return TD (-3.8); and outplayed (-9.4)                           |
|     2023 |   16 | CLE @ HOU | HOU +3    | 36-22   |     1.8 |  -15.8 | L        | QB lost in game (37% of dropbacks) (-3.0); and outplayed (-14.2)                       |
|     2023 |    6 | BAL @ TEN | TEN +5.5  | 24-16   |    -1.1 |   -6.9 | L        | garbage time (-6.4)                                                                    |
|     2023 |    8 | NYJ @ NYG | NYG +3    | 13-10   |     2.6 |   -5.6 | P        | garbage time (-6.4); QB lost in game (52% of dropbacks) (-3.0)                         |
|     2023 |    1 | LV @ DEN  | LV +3     | 17-16   |    -2.1 |   -1.1 | W        | covered anyway (miss -1.1 inside the edge)                                             |
|     2023 |   11 | LV @ MIA  | LV +14    | 13-20   |     7.7 |    0.7 | W        | covered anyway (miss +0.7 inside the edge)                                             |
|     2023 |   10 | NYJ @ LV  | LV +1     | 12-16   |     3.3 |    0.7 | W        | covered anyway (miss +0.7 inside the edge)                                             |
|     2023 |    9 | MIA @ KC  | KC -1     | 14-21   |     5.9 |    1.1 | W        | covered anyway; garbage time (-6.4)                                                    |
|     2023 |   13 | CIN @ JAX | CIN +10   | 34-31   |     4.9 |    7.9 | W        | covered anyway; turnovers 1-0 (-3.3)                                                   |
|     2023 |   15 | NYJ @ MIA | MIA -7.5  | 0-30    |    11.7 |   18.3 | W        | covered anyway (miss +18.3 inside the edge)                                            |
|     2024 |    6 | DET @ DAL | DAL +3.5  | 47-9    |     1   |  -39   | L        | garbage time (-25.5); turnovers 5-0 (-11.7)                                            |
|     2024 |   11 | HOU @ DAL | DAL +7.5  | 34-10   |    -2.8 |  -21.2 | L        | garbage time (-8.3); turnovers 2-1 (-4.5)                                              |
|     2024 |    6 | HOU @ NE  | NE +6.5   | 41-21   |    -2.5 |  -17.5 | L        | turnovers 4-1 (-7.7); garbage time (-6.4)                                              |
|     2024 |    3 | PHI @ NO  | NO -2.5   | 15-12   |     9.1 |  -12.1 | L        | outplayed, no luck (residual -19.3)                                                    |
|     2024 |    7 | BAL @ TB  | TB +4.5   | 41-31   |     0.3 |  -10.3 | L        | outplayed, no luck (residual -11.1)                                                    |
|     2024 |    1 | GB @ PHI  | GB +2     | 29-34   |    -2.6 |   -7.6 | L        | nothing stands out: ordinary miss (residual -7.7)                                      |
|     2024 |    2 | NYG @ WAS | NYG +1.5  | 18-21   |    -3.2 |   -6.2 | L        | nothing stands out: ordinary miss (residual -0.8)                                      |
|     2024 |    5 | BUF @ HOU | BUF +1    | 20-23   |    -3.1 |   -6.1 | L        | garbage time (-4.5); and outplayed (-9.2)                                              |
|     2024 |    7 | HOU @ GB  | GB -3     | 22-24   |     7.8 |   -5.8 | L        | turnovers 3-0 (-8.5)                                                                   |
|     2024 |    4 | NO @ ATL  | NO +2.5   | 24-26   |    -2.8 |   -4.8 | W        | covered anyway; turnovers 2-1 (-5.4)                                                   |
|     2025 |    3 | CIN @ MIN | CIN +3    | 10-48   |    -1.4 |  -39.4 | L        | garbage time (-18.1); turnovers 5-0 (-15.8)                                            |
|     2025 |    7 | MIA @ CLE | MIA +2.5  | 6-31    |    -3.5 |  -28.5 | L        | turnovers 4-0 (-10.5); garbage time (-6.3); and outplayed (-11.4)                      |
|     2025 |   16 | CIN @ MIA | MIA +3.5  | 45-21   |     1.1 |  -25.1 | L        | garbage time (-13.7); turnovers 3-0 (-5.6)                                             |
|     2025 |   17 | NE @ NYJ  | NYJ +12.5 | 42-10   |    -8.2 |  -23.8 | L        | model priced a QB who did not play; garbage time (-13.7); fourth downs (-3.7)          |
|     2025 |   16 | SF @ IND  | IND +4.5  | 48-27   |     1.8 |  -22.8 | L        | garbage time (-11.0); turnovers 2-1 (-6.2)                                             |
|     2025 |   16 | NYJ @ NO  | NYJ +6.5  | 6-29    |     2.2 |  -20.8 | L        | model priced a QB who did not play; garbage time (-10.8)                               |
|     2025 |    9 | BAL @ MIA | MIA +7.5  | 28-6    |    -2.7 |  -19.3 | L        | garbage time (-13.7); turnovers 3-0 (-5.7)                                             |
|     2025 |    6 | LA @ BAL  | BAL +7    | 17-3    |    -1.7 |  -12.3 | L        | turnovers 3-1 (-3.8); QB lost in game (49% of dropbacks) (-3.0)                        |
|     2025 |   11 | NYJ @ NE  | NYJ +12.5 | 14-27   |     6.5 |   -6.5 | L        | model priced a QB who did not play                                                     |
|     2025 |    3 | ARI @ SF  | ARI +1.5  | 15-16   |    -3.8 |   -4.8 | W        | covered anyway (miss -4.8 inside the edge)                                             |
|     2026 |    2 | CAR @ ATL | ATL +2.5  | 34-3    |     5.9 |  -36.9 | L        | model priced a QB who did not play; garbage time (-14.6); turnovers 5-0 (-14.1)        |
|     2026 |    1 | DEN @ KC  | DEN +2.5  | 10-31   |    -2   |  -23   | L        | garbage time (-5.4); fourth downs (-4.2); and outplayed (-13.1)                        |
|     2026 |    3 | CAR @ CLE | CLE +2.5  | 18-21   |     1.6 |    1.4 | W        | no play-by-play yet                                                                    |

### Under flag

|   Season |   Wk | Game      | Bet        | Final   |   Model |   Miss | Result   | Reason                                                                          |
|---------:|-----:|:----------|:-----------|:--------|--------:|-------:|:---------|:--------------------------------------------------------------------------------|
|     2015 |    7 | HOU @ MIA | Under 46.5 | 26-44   |    42.4 |  -27.6 | L        | garbage time (-14.1); return TD (-3.3)                                          |
|     2015 |    2 | ARI @ CHI | Under 45.5 | 48-23   |    44.5 |  -26.5 | L        | return TD (-8.0); and outplayed (-19.9)                                         |
|     2015 |   11 | TB @ PHI  | Under 46   | 45-17   |    35.9 |  -26.1 | L        | pace (-4.4); return TD (-3.3); and outplayed (-15.0)                            |
|     2015 |   12 | PIT @ SEA | Under 46.5 | 30-39   |    44.4 |  -24.6 | L        | pace (-5.7); 4 turnovers, 19 pts off them (-4.0); and outplayed (-18.6)         |
|     2015 |    3 | IND @ TEN | Under 46.5 | 35-33   |    44.8 |  -23.2 | L        | 4 turnovers, 24 pts off them (-3.3); return TD (-3.3); and outplayed (-14.8)    |
|     2015 |    3 | JAX @ NE  | Under 48.5 | 17-51   |    47.1 |  -20.9 | L        | garbage time (-14.9)                                                            |
|     2015 |    7 | LV @ LAC  | Under 48   | 37-29   |    45.3 |  -20.7 | L        | garbage time (-11.6); pace (-5.7)                                               |
|     2015 |    2 | SF @ PIT  | Under 46   | 18-43   |    41.7 |  -19.3 | L        | garbage time (-11.2); pace (-3.9)                                               |
|     2015 |    1 | TEN @ TB  | Under 40.5 | 42-14   |    37.4 |  -18.6 | L        | garbage time (-6.1); return TD (-3.3); and outplayed (-12.9)                    |
|     2015 |    1 | DET @ LAC | Under 45.5 | 28-33   |    42.4 |  -18.6 | L        | return TD (-3.3); and outplayed (-15.2)                                         |
|     2016 |    1 | DET @ IND | Under 51.5 | 39-35   |    46.1 |  -27.9 | L        | outplayed, no luck (residual -29.4)                                             |
|     2016 |    6 | CAR @ NO  | Under 53.5 | 38-41   |    51.4 |  -27.6 | L        | pace (-6.8); and outplayed (-22.2)                                              |
|     2016 |   17 | KC @ LAC  | Under 45   | 37-27   |    43   |  -21   | L        | return TD (-8.0); and outplayed (-10.4)                                         |
|     2016 |   11 | GB @ WAS  | Under 48.5 | 24-42   |    45.3 |  -20.7 | L        | garbage time (-3.5); and outplayed (-20.0)                                      |
|     2016 |   12 | CAR @ LV  | Under 48.5 | 32-35   |    46.3 |  -20.7 | L        | return TD (-3.3); and outplayed (-18.6)                                         |
|     2016 |    6 | SF @ BUF  | Under 44   | 16-45   |    42.1 |  -18.9 | L        | garbage time (-3.5); and outplayed (-12.7)                                      |
|     2016 |   12 | KC @ DEN  | Under 40   | 30-27   |    38.2 |  -18.8 | L        | pace (-10.2); overtime (-5.1)                                                   |
|     2016 |    4 | NO @ LAC  | Under 54   | 35-34   |    51.1 |  -17.9 | L        | 5 turnovers, 20 pts off them (-4.3); and outplayed (-12.3)                      |
|     2016 |    5 | ARI @ SF  | Under 42.5 | 33-21   |    36.7 |  -17.3 | L        | pace (-4.2); and outplayed (-9.1)                                               |
|     2016 |    1 | LAC @ KC  | Under 45.5 | 27-33   |    43.4 |  -16.6 | L        | garbage time (-6.5); pace (-5.1)                                                |
|     2017 |    8 | HOU @ SEA | Under 45   | 38-41   |    42.8 |  -36.2 | L        | return TD (-3.3); and outplayed (-33.8)                                         |
|     2017 |   14 | BAL @ PIT | Under 43   | 38-39   |    41.4 |  -35.6 | L        | pace (-7.7); and outplayed (-29.0)                                              |
|     2017 |   15 | PHI @ NYG | Under 40.5 | 34-29   |    36.4 |  -26.6 | L        | pace (-7.6); and outplayed (-25.9)                                              |
|     2017 |    1 | KC @ NE   | Under 47.5 | 42-27   |    45.1 |  -23.9 | L        | pace (-3.5); and outplayed (-24.1)                                              |
|     2017 |    7 | NYJ @ MIA | Under 40   | 28-31   |    38.3 |  -20.7 | L        | 4 turnovers, 17 pts off them (-3.3); and outplayed (-22.1)                      |
|     2017 |   12 | GB @ PIT  | Under 43   | 28-31   |    40.9 |  -18.1 | L        | outplayed, no luck (residual -24.3)                                             |
|     2017 |    5 | GB @ DAL  | Under 52   | 35-31   |    50.1 |  -15.9 | L        | return TD (-3.3); and outplayed (-17.9)                                         |
|     2017 |    1 | IND @ LA  | Under 41.5 | 9-46    |    39.8 |  -15.2 | L        | return TD (-8.0); garbage time (-6.5); and outplayed (-9.7)                     |
|     2017 |    3 | NYG @ PHI | Under 42   | 24-27   |    40   |  -11   | L        | pace (-3.8); and outplayed (-9.8)                                               |
|     2017 |   13 | DEN @ MIA | Under 41   | 9-35    |    34.8 |   -9.2 | L        | return TD (-8.0); pace (-3.5)                                                   |
|     2018 |   11 | KC @ LA   | Under 63.5 | 51-54   |    59.9 |  -45.1 | L        | return TD (-12.7); pace (-6.8); and outplayed (-26.9)                           |
|     2018 |    4 | CLE @ LV  | Under 44.5 | 42-45   |    43   |  -44   | L        | pace (-16.6); 6 turnovers, 29 pts off them (-4.9); and outplayed (-22.3)        |
|     2018 |    1 | TB @ NO   | Under 50   | 48-40   |    47.4 |  -40.6 | L        | garbage time (-4.6); return TD (-3.3); and outplayed (-34.7)                    |
|     2018 |    6 | IND @ NYJ | Under 47.5 | 34-42   |    44.8 |  -31.2 | L        | garbage time (-5.4); 6 turnovers, 26 pts off them (-4.0); and outplayed (-14.5) |
|     2018 |    2 | KC @ PIT  | Under 52   | 42-37   |    48.3 |  -30.7 | L        | outplayed, no luck (residual -32.1)                                             |
|     2018 |    3 | NO @ ATL  | Under 54   | 43-37   |    49.4 |  -30.6 | L        | pace (-5.8); overtime (-3.4); and outplayed (-25.8)                             |
|     2018 |    6 | KC @ NE   | Under 59.5 | 40-43   |    54.6 |  -28.4 | L        | outplayed, no luck (residual -28.3)                                             |
|     2018 |    9 | LA @ NO   | Under 57.5 | 35-45   |    55   |  -25   | L        | outplayed, no luck (residual -23.7)                                             |
|     2018 |    4 | MIN @ LA  | Under 48.5 | 31-38   |    44.2 |  -24.8 | L        | outplayed, no luck (residual -33.0)                                             |
|     2018 |    4 | CIN @ ATL | Under 52   | 37-36   |    49.1 |  -23.9 | L        | pace (-4.0); and outplayed (-25.9)                                              |
|     2019 |   13 | PHI @ MIA | Under 45   | 31-37   |    42.7 |  -25.3 | L        | pace (-3.0); and outplayed (-26.2)                                              |
|     2019 |   12 | MIA @ CLE | Under 45.5 | 24-41   |    43.8 |  -21.2 | L        | garbage time (-14.5); 3 turnovers, 21 pts off them (-4.6)                       |
|     2019 |    3 | NYG @ TB  | Under 48   | 32-31   |    42.2 |  -20.8 | L        | outplayed, no luck (residual -20.1)                                             |
|     2019 |    4 | CLE @ BAL | Under 47   | 40-25   |    44.6 |  -20.4 | L        | garbage time (-4.6); 4 turnovers, 21 pts off them (-4.6); and outplayed (-11.8) |
|     2019 |   10 | KC @ TEN  | Under 49   | 32-35   |    47.1 |  -19.9 | L        | return TD (-3.3); and outplayed (-21.0)                                         |
|     2019 |    6 | SEA @ CLE | Under 45.5 | 32-28   |    41.7 |  -18.3 | L        | pace (-4.6); and outplayed (-18.4)                                              |
|     2019 |    6 | CAR @ TB  | Under 48.5 | 37-26   |    45.6 |  -17.4 | L        | garbage time (-9.0); 8 turnovers, 27 pts off them (-6.5)                        |
|     2019 |    6 | ATL @ ARI | Under 52.5 | 33-34   |    50.2 |  -16.8 | L        | outplayed, no luck (residual -19.6)                                             |
|     2019 |   15 | CLE @ ARI | Under 49   | 24-38   |    45.3 |  -16.7 | L        | outplayed, no luck (residual -16.6)                                             |
|     2019 |    3 | CAR @ ARI | Under 46   | 38-20   |    43.2 |  -14.8 | L        | 3 turnovers, 17 pts off them (-3.3); and outplayed (-9.5)                       |
|     2020 |   14 | BAL @ CLE | Under 45.5 | 47-42   |    42.9 |  -46.1 | L        | pace (-4.7); and outplayed (-43.8)                                              |
|     2020 |   16 | MIN @ NO  | Under 49   | 33-52   |    46.7 |  -38.3 | L        | garbage time (-3.5); and outplayed (-34.6)                                      |
|     2020 |    4 | CLE @ DAL | Under 56.5 | 49-38   |    49.5 |  -37.5 | L        | garbage time (-12.3); pace (-10.2); and outplayed (-13.1)                       |
|     2020 |    2 | ATL @ DAL | Under 53   | 39-40   |    49.1 |  -29.9 | L        | pace (-10.4); 3 turnovers, 17 pts off them (-3.3); and outplayed (-14.8)        |
|     2020 |    6 | HOU @ TEN | Under 52   | 36-42   |    50.3 |  -27.7 | L        | pace (-5.4); overtime (-3.4); and outplayed (-22.7)                             |
|     2020 |    4 | DEN @ NYJ | Under 41   | 37-28   |    38.4 |  -26.6 | L        | pace (-4.6); kicks (0 FG missed, 0 blocked) (-3.4); and outplayed (-17.0)       |
|     2020 |   15 | BUF @ DEN | Under 49   | 48-19   |    42.3 |  -24.7 | L        | garbage time (-3.5); return TD (-3.3); and outplayed (-15.2)                    |
|     2020 |    7 | CLE @ CIN | Under 50   | 37-34   |    47.3 |  -23.7 | L        | outplayed, no luck (residual -29.3)                                             |
|     2020 |    3 | LA @ BUF  | Under 46.5 | 32-35   |    43.9 |  -23.1 | L        | garbage time (-6.5); 4 turnovers, 21 pts off them (-4.6); and outplayed (-14.8) |
|     2020 |   10 | TB @ CAR  | Under 49.5 | 46-23   |    46.8 |  -22.2 | L        | garbage time (-4.3); and outplayed (-20.0)                                      |
|     2021 |    3 | WAS @ BUF | Under 45.5 | 21-43   |    39.1 |  -24.9 | L        | garbage time (-9.0); 3 turnovers, 17 pts off them (-3.3); and outplayed (-15.2) |
|     2021 |    2 | ATL @ TB  | Under 52   | 25-48   |    48.4 |  -24.6 | L        | return TD (-8.0); and outplayed (-18.7)                                         |
|     2021 |    4 | KC @ PHI  | Under 53.5 | 42-30   |    52   |  -20   | L        | outplayed, no luck (residual -18.6)                                             |
|     2021 |    2 | KC @ BAL  | Under 53.5 | 35-36   |    51.2 |  -19.8 | L        | return TD (-3.3); and outplayed (-22.5)                                         |
|     2021 |   15 | GB @ BAL  | Under 45.5 | 31-30   |    41.6 |  -19.4 | L        | outplayed, no luck (residual -25.0)                                             |
|     2021 |    2 | NYG @ WAS | Under 42   | 29-30   |    39.7 |  -19.3 | L        | kicks (0 FG missed, 0 blocked) (-3.5); and outplayed (-19.9)                    |
|     2021 |    6 | DAL @ NE  | Under 50.5 | 35-29   |    45.1 |  -18.9 | L        | overtime (-3.4); return TD (-3.3); and outplayed (-17.6)                        |
|     2021 |    4 | WAS @ ATL | Under 47.5 | 34-30   |    45.3 |  -18.7 | L        | return TD (-3.3); and outplayed (-19.4)                                         |
|     2021 |    9 | MIN @ BAL | Under 51   | 31-34   |    47.9 |  -17.1 | L        | pace (-4.9); return TD (-3.3); and outplayed (-11.5)                            |
|     2021 |    8 | TEN @ IND | Under 51   | 34-31   |    48   |  -17   | L        | pace (-4.7); 4 turnovers, 24 pts off them (-3.3); and outplayed (-8.4)          |
|     2022 |    2 | MIA @ BAL | Under 44   | 42-38   |    42.2 |  -37.8 | L        | garbage time (-8.3); return TD (-3.3); and outplayed (-28.2)                    |
|     2022 |   12 | GB @ PHI  | Under 46   | 33-40   |    43.3 |  -29.7 | L        | garbage time (-3.9); and outplayed (-24.7)                                      |
|     2022 |    1 | PHI @ DET | Under 49   | 38-35   |    47.4 |  -25.6 | L        | garbage time (-5.4); pace (-4.5); and outplayed (-15.2)                         |
|     2022 |   10 | DET @ CHI | Under 48.5 | 31-30   |    46.2 |  -14.8 | L        | return TD (-3.3); and outplayed (-19.3)                                         |
|     2022 |   15 | CIN @ TB  | Under 47   | 34-23   |    43.8 |  -13.2 | L        | garbage time (-8.6); 5 turnovers, 24 pts off them (-5.6)                        |
|     2022 |    1 | KC @ ARI  | Under 54   | 44-21   |    52.4 |  -12.6 | L        | garbage time (-8.6)                                                             |
|     2022 |    4 | NE @ GB   | Under 40.5 | 24-27   |    38.5 |  -12.5 | L        | pace (-4.1); overtime (-3.4)                                                    |
|     2022 |   11 | CLE @ BUF | Under 50.5 | 23-31   |    48.1 |   -5.9 | L        | garbage time (-3.9)                                                             |
|     2022 |   13 | GB @ CHI  | Under 45   | 28-19   |    42.4 |   -4.6 | L        | outplayed, no luck (residual -12.2)                                             |
|     2022 |    9 | SEA @ ARI | Under 49.5 | 31-21   |    47.5 |   -4.5 | L        | return TD (-3.3)                                                                |
|     2023 |   14 | LA @ BAL  | Under 42   | 31-37   |    40.3 |  -27.7 | L        | pace (-8.5); overtime (-3.4); and outplayed (-14.7)                             |
|     2023 |   12 | BUF @ PHI | Under 49   | 34-37   |    45.1 |  -25.9 | L        | pace (-12.4); overtime (-5.1); and outplayed (-9.0)                             |
|     2023 |    1 | MIA @ LAC | Under 50.5 | 36-34   |    48.6 |  -21.4 | L        | pace (-6.1); and outplayed (-19.5)                                              |
|     2023 |   13 | SF @ PHI  | Under 46.5 | 42-19   |    40.7 |  -20.3 | L        | garbage time (-7.9); weather surprise (-5.6); and outplayed (-9.1)              |
|     2023 |    4 | MIA @ BUF | Under 53   | 20-48   |    50.2 |  -17.8 | L        | garbage time (-4.3); and outplayed (-18.6)                                      |
|     2023 |    6 | CAR @ MIA | Under 47.5 | 21-42   |    45.5 |  -17.5 | L        | garbage time (-3.9); return TD (-3.3); and outplayed (-11.4)                    |
|     2023 |    2 | MIN @ PHI | Under 49   | 28-34   |    46.9 |  -15.1 | L        | garbage time (-8.3)                                                             |
|     2023 |    3 | HOU @ JAX | Under 43.5 | 37-17   |    40.7 |  -13.3 | L        | garbage time (-5.7); return TD (-3.3)                                           |
|     2023 |   14 | TEN @ MIA | Under 45   | 28-27   |    43.6 |  -11.4 | L        | pace (-7.1); return TD (-3.3)                                                   |
|     2023 |   11 | CIN @ BAL | Under 46.5 | 20-34   |    42.9 |  -11.1 | L        | outplayed, no luck (residual -16.3)                                             |
|     2024 |   15 | BUF @ DET | Under 55.5 | 48-42   |    52.7 |  -37.3 | L        | garbage time (-13.4); pace (-8.2); and outplayed (-19.9)                        |
|     2024 |   16 | ARI @ CAR | Under 47   | 30-36   |    43.2 |  -22.8 | L        | overtime (-6.9); and outplayed (-14.5)                                          |
|     2024 |    7 | BAL @ TB  | Under 51   | 41-31   |    49.9 |  -22.1 | L        | garbage time (-9.0); 3 turnovers, 18 pts off them (-3.7)                        |
|     2024 |    4 | MIN @ GB  | Under 44   | 31-29   |    41.4 |  -18.6 | L        | garbage time (-13.0); 7 turnovers, 41 pts off them (-11.0)                      |
|     2024 |    1 | ARI @ BUF | Under 46   | 28-34   |    44.2 |  -17.8 | L        | return TD (-3.3); and outplayed (-19.7)                                         |
|     2024 |    8 | ARI @ MIA | Under 46.5 | 28-27   |    39.9 |  -15.1 | L        | model priced a QB who did not play; and outplayed (-16.5)                       |
|     2024 |   14 | GB @ DET  | Under 53   | 31-34   |    50.4 |  -14.6 | L        | outplayed, no luck (residual -20.1)                                             |
|     2024 |    6 | SF @ SEA  | Under 49   | 36-24   |    47.3 |  -12.7 | L        | garbage time (-9.4); pace (-3.7)                                                |
|     2024 |    7 | DET @ MIN | Under 50.5 | 31-29   |    47.7 |  -12.3 | L        | return TD (-3.3); and outplayed (-16.0)                                         |
|     2024 |   11 | JAX @ DET | Under 47.5 | 6-52    |    46.1 |  -11.9 | L        | garbage time (-11.9)                                                            |
|     2025 |    9 | CHI @ CIN | Under 51.5 | 47-42   |    46.6 |  -42.4 | L        | pace (-8.0); garbage time (-3.5); and outplayed (-29.8)                         |
|     2025 |    8 | NYJ @ CIN | Under 43.5 | 39-38   |    41.7 |  -35.3 | L        | garbage time (-3.2); and outplayed (-34.0)                                      |
|     2025 |   16 | LA @ SEA  | Under 42.5 | 37-38   |    39.8 |  -35.2 | L        | overtime (-13.4); pace (-12.8)                                                  |
|     2025 |   17 | NO @ TEN  | Under 39.5 | 34-26   |    36.3 |  -23.7 | L        | return TD (-3.3); and outplayed (-20.6)                                         |
|     2025 |    3 | LV @ WAS  | Under 43.5 | 24-41   |    41.6 |  -23.4 | L        | garbage time (-8.6); return TD (-3.3); and outplayed (-17.3)                    |
|     2025 |   15 | DET @ LA  | Under 54.5 | 34-41   |    52   |  -23   | L        | pace (-3.1); and outplayed (-21.9)                                              |
|     2025 |   10 | LA @ SF   | Under 49.5 | 42-26   |    46   |  -22   | L        | garbage time (-3.5); and outplayed (-18.8)                                      |
|     2025 |   14 | CIN @ BUF | Under 54.5 | 34-39   |    51.1 |  -21.9 | L        | return TD (-3.3); and outplayed (-22.1)                                         |
|     2025 |   16 | CIN @ MIA | Under 48.5 | 45-21   |    45.4 |  -20.6 | L        | garbage time (-6.1); 3 turnovers, 21 pts off them (-4.6); and outplayed (-12.0) |
|     2025 |   10 | DET @ WAS | Under 49.5 | 44-22   |    46.7 |  -19.3 | L        | garbage time (-10.5); and outplayed (-14.4)                                     |
|     2026 |    1 | CHI @ CAR | Under 47.5 | 59-37   |    44.8 |  -51.2 | L        | garbage time (-5.7); pace (-3.7); and outplayed (-38.6)                         |
|     2026 |    2 | DET @ BUF | Under 54.5 | 31-41   |    52.8 |  -19.2 | L        | garbage time (-15.6)                                                            |
|     2026 |    2 | IND @ KC  | Under 46.5 | 30-33   |    44.5 |  -18.5 | L        | pace (-8.6); overtime (-6.9)                                                    |
|     2026 |    1 | NO @ DET  | Under 49.5 | 30-31   |    47.5 |  -13.5 | L        | pace (-15.0); overtime (-7.5)                                                   |
|     2026 |    3 | MIN @ TB  | Under 42.5 | 23-16   |    41.5 |    2.5 | W        | no play-by-play yet                                                             |
|     2026 |    3 | NE @ JAX  | Under 46.5 | 6-35    |    44.2 |    3.2 | W        | no play-by-play yet                                                             |
|     2026 |    2 | GB @ NYJ  | Under 44.5 | 20-17   |    42.5 |    5.5 | W        | covered anyway; overtime (-3.4)                                                 |
|     2026 |    3 | LAC @ BUF | Under 50.5 | 16-24   |    47.9 |    7.9 | W        | no play-by-play yet                                                             |
|     2026 |    2 | JAX @ DEN | Under 45.5 | 13-20   |    43.1 |   10.1 | W        | covered anyway (miss +10.1 inside the edge)                                     |
|     2026 |    1 | NE @ SEA  | Under 44.5 | 10-13   |    42.1 |   19.1 | W        | covered anyway (miss +19.1 inside the edge)                                     |

Runtime: 108s on 4 shared cores (play-by-play read once per season, 2015-2026).