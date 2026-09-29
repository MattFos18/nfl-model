# Overs against unders: diagnosis, fixes, rules (29 Sep 2026)

`experiments/totals_sides.py`, `reports/totals_sides.csv`. Matt: the unders are really good and the overs are garbage.
Every number is walk-forward (a game priced only with games before its week). Windows: 2015-18 (never tuned on),
2019-22 (tuned on), 2023-25 (held out). Bets: regular season, weeks 1-17, a closing total, pushes dropped, -110.

## Adoption rule (written before the results)

- A change to the total equation or to the chance is adopted only if the total miss (MAE, regular season) or the
  55%+ under record (win rate at the cut) improves on all three windows, with nothing worse on any window: the MAE not
  higher (0.0001 tolerance) and the under win rate not lower. A one- or two-window gain is not adopted.
- A betting rule (over or under) is adopted only if it wins (ROI above zero at -110, 15+ bets) on all three windows.
- Knobs (the shrink s, the upside factor) are fitted on 2019-22 only; 2015-18 and 2023-25 judge them.

## Part 1: where the overs go wrong

**In plain words.** The overs lose for three reasons that stack; the unders win for one of the same reasons plus a real
signal at large edges.

1. **The typical game lands under.** Over 2,895 regular-season games of 2015-25 the actual total beat the closing line by
   +0.40 points on average, but the median game landed 0.5 under it, and unders won 51.1% of non-push games. The total
   equation predicts the average: its bias is +0.04, yet it sits 0.71 above the median game. A bet is paid on the typical
   game, so every over starts about a point behind and every under a point ahead.
2. **The model leans over, and its over projections run hot.** It sits over the line in 1,689 games and under in 1,206
   (0.4 points above the line on average). On its over-leans it is 1.38 points too high (the line is 0.84 too low); only
   38% of an over edge comes true on average, and each point of over edge buys 0.15 points of actual-minus-line. The median
   over-lean lands 0.5 over and wins 50.5%, under the 52.4% break-even. Over edges of 2, 3, 4 and 5 points all lose (-4% to
   -19% ROI over 2015-25, and in nearly every window); the edge size carries no information until 6+ (26-17, 43 bets).
   The over-leans that go worst are the model's biggest projections (projected 49-52: over 3+ 36-47; 52+: 11-20; line
   46-49: 24-36), cold outdoor games (model +2.95 too high; a warm-climate or dome team in the cold +4.7, over 3+ 6-17),
   primetime (+0.88, over 3+ 41-53) and games of one good and one bad offense (+0.66, over 3+ 104-119). Over calls on low
   lines are fine (line under 40: 50-40; 40-43: 74-68). Division games (+0.72) and two good defenses (+0.82) also run hot
   on every window, though their over calls only break even. By window the over-lean overshoot is +2.20 (2015-18, the 2017
   drop), +1.07 (2019-22) and +0.83 (2023-25).
3. **The chance ignores both.** p_over_emp on over-leans said 57%, 62% and 68% in the 55-60, 60-65 and 65+ bands and won
   49.4%, 50.0% and 55.7% (8 to 12 points hot); on under-leans it said 57%, 62% and 69% and won 51.6%, 55.5% and 65.3%
   (3 to 7 points hot). An over at a "60%" chance is a coin flip; an under at 65% is close to what it says.

**The unders.** Small under edges (0 to 3 points) lose like the overs; from 3 points up the under edge is real: 177-112
(+16.9% ROI) with 44% of the edge coming true and the median game 2.75 under the line, positive in every window and every
edge band from 3 up. The under-leans are also too extreme on average (model 1.85 too low), but the skew is on their side.

**What does not matter.** Pace, rest and the week of the season move the bias by half a point or less and not the same way
in every window. The referee carries no trait left in the misses (the per-referee spread is 0.66x chance and
odd-season against even-season correlates -0.19), so ref_tot already has what there is.

### Leaning each side, by edge (model total minus the line), record and ROI

| lean   | edge     | 2015-18         | 2019-22         | 2023-25         | 2015-25          |   units |   mean_edge |   mean_realized |   median_realized |
|:-------|:---------|:----------------|:----------------|:----------------|:-----------------|--------:|------------:|----------------:|------------------:|
| over   | 0-2      | 146-162 (-9.5%) | 150-155 (-6.1%) | 126-107 (+3.2%) | 422-424 (-4.8%)  |   -44.4 |        0.99 |            0.71 |              0    |
| over   | 2-3      | 66-68 (-6.0%)   | 47-48 (-5.6%)   | 57-52 (-0.2%)   | 170-168 (-4.0%)  |   -14.8 |        2.46 |            0.39 |              0.25 |
| over   | 3-4      | 34-28 (+4.7%)   | 28-36 (-16.5%)  | 43-41 (-2.3%)   | 105-105 (-4.5%)  |   -10.5 |        3.47 |            0.75 |              0    |
| over   | 4-5      | 17-18 (-7.3%)   | 18-18 (-4.5%)   | 29-28 (-2.9%)   | 64-64 (-4.5%)    |    -6.4 |        4.42 |            1.68 |              0    |
| over   | 5-6      | 8-12 (-23.6%)   | 6-7 (-11.9%)    | 8-11 (-19.6%)   | 22-30 (-19.2%)   |   -11   |        5.41 |           -0.89 |             -4.5  |
| over   | 6+       | 11-8 (+10.5%)   | 9-4 (+32.2%)    | 6-5 (+4.1%)     | 26-17 (+15.4%)   |     7.3 |        7.17 |            3.59 |              6    |
| over   | 2+ (all) | 136-134 (-3.8%) | 108-113 (-6.7%) | 143-137 (-2.5%) | 387-384 (-4.2%)  |   -35.4 |        3.52 |            0.8  |              0    |
| over   | 3+ (all) | 70-66 (-1.7%)   | 61-65 (-7.6%)   | 86-85 (-4.0%)   | 217-216 (-4.3%)  |   -20.6 |        4.35 |            1.11 |              0    |
| over   | 4+ (all) | 36-38 (-7.1%)   | 33-29 (+1.6%)   | 43-44 (-5.6%)   | 112-111 (-4.1%)  |   -10.1 |        5.17 |            1.44 |              0    |
| over   | 5+ (all) | 19-20 (-7.0%)   | 15-11 (+10.1%)  | 14-16 (-10.9%)  | 48-47 (-3.5%)    |    -3.7 |        6.2  |            1.12 |              0.5  |
| under  | 0-2      | 131-128 (-3.4%) | 123-126 (-5.7%) | 97-81 (+4.0%)   | 351-335 (-2.3%)  |   -17.5 |        0.96 |           -0.09 |              0.5  |
| under  | 2-3      | 34-37 (-8.6%)   | 45-46 (-5.6%)   | 16-19 (-12.7%)  | 95-102 (-7.9%)   |   -17.2 |        2.47 |           -1.78 |             -0.5  |
| under  | 3-4      | 30-23 (+8.1%)   | 42-29 (+12.9%)  | 13-10 (+7.9%)   | 85-62 (+10.4%)   |    16.8 |        3.45 |            1.7  |              2.25 |
| under  | 4-5      | 11-15 (-19.2%)  | 27-9 (+43.2%)   | 3-3 (-4.5%)     | 41-27 (+15.1%)   |    11.3 |        4.45 |            1.38 |              2.25 |
| under  | 5-6      | 10-4 (+36.4%)   | 12-7 (+20.6%)   | 4-2 (+27.3%)    | 26-13 (+27.3%)   |    11.7 |        5.37 |            1.85 |              4    |
| under  | 6+       | 10-4 (+36.4%)   | 14-5 (+40.7%)   | 1-1 (-4.5%)     | 25-10 (+36.4%)   |    14   |        7.34 |            4.14 |              6    |
| under  | 2+ (all) | 95-83 (+1.9%)   | 140-96 (+13.3%) | 37-35 (-1.9%)   | 272-214 (+6.8%)  |    36.6 |        3.62 |            0.42 |              1.5  |
| under  | 3+ (all) | 61-46 (+8.8%)   | 95-50 (+25.1%)  | 21-16 (+8.4%)   | 177-112 (+16.9%) |    53.8 |        4.41 |            1.94 |              2.75 |
| under  | 4+ (all) | 31-23 (+9.6%)   | 53-21 (+36.7%)  | 8-6 (+9.1%)     | 92-50 (+23.7%)   |    37   |        5.42 |            2.19 |              3.25 |
| under  | 5+ (all) | 20-8 (+36.4%)   | 26-12 (+30.6%)  | 5-3 (+19.3%)    | 51-23 (+31.6%)   |    25.7 |        6.3  |            2.93 |              4    |

`mean_realized`: the actual total minus the line on the lean's side, all 2015-25 (positive = the lean was right on average);
`median_realized`: the typical game.

### How much of the edge comes true, by side

| lean   | window   |   games |   mean_edge |   mean_actual_minus_line |   median_actual_minus_line |   share_of_edge_realized |   slope |   side_won |   model_bias |   line_bias |
|:-------|:---------|--------:|------------:|-------------------------:|---------------------------:|-------------------------:|--------:|-----------:|-------------:|------------:|
| over   | 2015-18  |     584 |        2.17 |                    -0.03 |                      -0.5  |                    -0.01 |    0.04 |      0.488 |         2.2  |        0.03 |
| over   | 2019-22  |     558 |        2.06 |                     0.98 |                       0    |                     0.48 |    0.18 |      0.498 |         1.07 |       -0.98 |
| over   | 2023-25  |     547 |        2.44 |                     1.61 |                       1    |                     0.66 |    0.2  |      0.531 |         0.83 |       -1.61 |
| over   | 2015-25  |    1689 |        2.22 |                     0.84 |                       0.5  |                     0.38 |    0.15 |      0.505 |         1.38 |       -0.84 |
| under  | 2015-18  |     440 |       -2.07 |                     0.03 |                      -0.75 |                    -0.02 |    0.1  |      0.517 |        -2.11 |       -0.03 |
| under  | 2019-22  |     497 |       -2.29 |                    -0.53 |                      -1.5  |                     0.23 |    0.9  |      0.546 |        -1.76 |        0.53 |
| under  | 2023-25  |     269 |       -1.61 |                    -0.02 |                      -1.5  |                     0.01 |   -0.42 |      0.543 |        -1.59 |        0.02 |
| under  | 2015-25  |    1206 |       -2.06 |                    -0.21 |                      -1    |                     0.1  |    0.38 |      0.535 |        -1.85 |        0.21 |

`slope`: points of (actual minus line) per point of (model minus line) within the side; 1 would mean the edge is fully real.

### Leaning each side by the empirical chance (p_over_emp), record and ROI

| lean   | chance    | 2015-18         | 2019-22          | 2023-25         | 2015-25         |   units |   stated |   won |
|:-------|:----------|:----------------|:-----------------|:----------------|:----------------|--------:|---------:|------:|
| over   | 50-55     | 123-131 (-7.6%) | 120-133 (-9.5%)  | 98-88 (+0.6%)   | 341-352 (-6.1%) |   -46.2 |    0.524 | 0.492 |
| over   | 55-60     | 64-79 (-14.6%)  | 68-68 (-4.5%)    | 86-76 (+1.3%)   | 218-223 (-5.6%) |   -27.3 |    0.574 | 0.494 |
| over   | 60-65     | 44-33 (+9.1%)   | 25-33 (-17.7%)   | 36-39 (-8.4%)   | 105-105 (-4.5%) |   -10.5 |    0.619 | 0.5   |
| over   | 65+       | 13-12 (-0.7%)   | 11-7 (+16.7%)    | 10-8 (+6.1%)    | 34-27 (+6.4%)   |     4.3 |    0.681 | 0.557 |
| over   | 55+ (all) | 121-124 (-5.7%) | 104-108 (-6.3%)  | 132-123 (-1.2%) | 357-355 (-4.3%) |   -33.5 |    0.596 | 0.501 |
| under  | 50-55     | 132-122 (-0.8%) | 115-128 (-9.7%)  | 96-96 (-4.5%)   | 343-346 (-5.0%) |   -37.6 |    0.525 | 0.498 |
| under  | 55-60     | 71-74 (-6.5%)   | 73-70 (-2.5%)    | 47-35 (+9.4%)   | 191-179 (-1.4%) |    -5.9 |    0.571 | 0.516 |
| under  | 60-65     | 38-38 (-4.5%)   | 70-44 (+17.2%)   | 18-19 (-7.1%)   | 126-101 (+6.0%) |    14.9 |    0.621 | 0.555 |
| under  | 65+       | 26-15 (+21.1%)  | 32-14 (+32.8%)   | 6-5 (+4.1%)     | 64-34 (+24.7%)  |    26.6 |    0.687 | 0.653 |
| under  | 55+ (all) | 135-127 (-1.6%) | 175-128 (+10.3%) | 71-59 (+4.3%)   | 381-314 (+4.7%) |    35.6 |    0.604 | 0.548 |

### Reliability of p_over_emp, over-leans and under-leans apart

| lean   | band   | 2015-18                       | 2019-22                       | 2023-25                       | 2015-25                       |   gap_pts |
|:-------|:-------|:------------------------------|:------------------------------|:------------------------------|:------------------------------|----------:|
| over   | 50-55  | 52.4% said, 48.4% won (n 254) | 52.3% said, 47.4% won (n 253) | 52.5% said, 52.7% won (n 186) | 52.4% said, 49.2% won (n 693) |      -3.2 |
| over   | 55-60  | 57.0% said, 44.8% won (n 143) | 57.6% said, 50.0% won (n 136) | 57.5% said, 53.1% won (n 162) | 57.4% said, 49.4% won (n 441) |      -7.9 |
| over   | 60-65  | 62.0% said, 57.1% won (n 77)  | 61.8% said, 43.1% won (n 58)  | 61.7% said, 48.0% won (n 75)  | 61.9% said, 50.0% won (n 210) |     -11.9 |
| over   | 65+    | 69.1% said, 52.0% won (n 25)  | 68.0% said, 61.1% won (n 18)  | 66.8% said, 55.6% won (n 18)  | 68.1% said, 55.7% won (n 61)  |     -12.3 |
| under  | 50-55  | 52.6% said, 52.0% won (n 254) | 52.5% said, 47.3% won (n 243) | 52.6% said, 50.0% won (n 192) | 52.6% said, 49.8% won (n 689) |      -2.8 |
| under  | 55-60  | 57.0% said, 49.0% won (n 145) | 57.3% said, 51.0% won (n 143) | 57.0% said, 57.3% won (n 82)  | 57.1% said, 51.6% won (n 370) |      -5.5 |
| under  | 60-65  | 62.0% said, 50.0% won (n 76)  | 62.2% said, 61.4% won (n 114) | 62.1% said, 48.6% won (n 37)  | 62.1% said, 55.5% won (n 227) |      -6.6 |
| under  | 65+    | 68.6% said, 63.4% won (n 41)  | 68.8% said, 69.6% won (n 46)  | 68.2% said, 54.5% won (n 11)  | 68.7% said, 65.3% won (n 98)  |      -3.4 |

### Signed bias, model total minus actual (positive = the model too high), 2015-25 regular season

| dim                         | group                           |   games |   model_bias |   line_bias |   model_minus_line |   bias 2015-18 |   bias 2019-22 |   bias 2023-25 |   over_hit | over 3+   | under 55%   |
|:----------------------------|:--------------------------------|--------:|-------------:|------------:|-------------------:|---------------:|---------------:|---------------:|-----------:|:----------|:------------|
| projected total             | <40                             |     237 |         0.81 |        1.92 |              -1.11 |          -1.02 |           0.87 |           2.59 |      0.418 | 4-5       | 54-43       |
| projected total             | 40-43                           |     504 |        -0.8  |       -0.74 |              -0.06 |          -1.12 |          -0.19 |          -1.06 |      0.495 | 29-25     | 90-62       |
| projected total             | 43-46                           |     805 |         0.22 |       -0.31 |               0.54 |           0.65 |           0.26 |          -0.44 |      0.481 | 66-55     | 104-74      |
| projected total             | 46-49                           |     785 |        -0.35 |       -1.16 |               0.8  |           0.81 |          -1.23 |          -0.57 |      0.526 | 71-64     | 65-82       |
| projected total             | 49-52                           |     412 |         0.8  |        0.02 |               0.78 |           0.26 |           0.29 |           2.08 |      0.467 | 36-47     | 56-40       |
| projected total             | 52+                             |     152 |         0.62 |       -0.55 |               1.17 |           2.73 |          -0.99 |          -1.01 |      0.49  | 11-20     | 12-13       |
| line                        | <40                             |     275 |         1.64 |       -0.48 |               2.12 |           1.37 |           2.57 |           1.27 |      0.493 | 50-40     | 10-8        |
| line                        | 40-43                           |     563 |         0.18 |       -1.23 |               1.41 |           0.33 |           0.74 |          -0.52 |      0.52  | 74-68     | 36-29       |
| line                        | 43-46                           |     802 |         0.83 |        0.05 |               0.78 |           1.4  |          -0.08 |           1.17 |      0.469 | 65-62     | 89-69       |
| line                        | 46-49                           |     692 |        -0.3  |       -0.42 |               0.12 |          -0.01 |          -0.37 |          -0.59 |      0.497 | 24-36     | 92-83       |
| line                        | 49-52                           |     345 |        -1.01 |        0.02 |              -1.02 |          -0.3  |          -1.32 |          -1.37 |      0.471 | 4-7       | 79-68       |
| line                        | 52+                             |     218 |        -2.54 |       -0.43 |              -2.1  |          -2.45 |          -2.32 |          -3.72 |      0.477 | 0-3       | 75-57       |
| roof                        | indoors (dome or closed)        |     821 |        -0.27 |       -1.36 |               1.09 |           1.23 |          -1.77 |           0.14 |      0.505 | 79-81     | 71-61       |
| roof                        | outdoors                        |    2022 |         0.26 |        0.05 |               0.2  |           0.13 |           0.47 |           0.15 |      0.482 | 135-134   | 300-245     |
| roof                        | retractable, open               |      52 |        -3.66 |       -2.91 |              -0.74 |          -2.74 |          -2.38 |          -7.92 |      0.481 | 3-1       | 10-8        |
| wind                        | indoors                         |     821 |        -0.27 |       -1.36 |               1.09 |           1.23 |          -1.77 |           0.14 |      0.505 | 79-81     | 71-61       |
| wind                        | outdoors, wind 10-14            |     425 |         1.03 |        1.45 |              -0.42 |           1.25 |           0.85 |           0.97 |      0.405 | 17-19     | 93-56       |
| wind                        | outdoors, wind 15+              |     216 |         0.49 |        1.65 |              -1.16 |           1.31 |          -0.77 |           1.53 |      0.449 | 5-9       | 55-48       |
| wind                        | outdoors, wind <10              |    1433 |        -0.15 |       -0.71 |               0.56 |          -0.46 |           0.44 |          -0.47 |      0.51  | 116-107   | 162-149     |
| cold                        | indoors                         |     821 |        -0.27 |       -1.36 |               1.09 |           1.23 |          -1.77 |           0.14 |      0.505 | 79-81     | 71-61       |
| cold                        | outdoors, 35F+                  |    1923 |        -0.06 |       -0.09 |               0.03 |          -0.39 |           0.36 |          -0.17 |      0.484 | 120-103   | 300-247     |
| cold                        | outdoors, under 35F             |     151 |         2.95 |        0.83 |               2.12 |           6.19 |           0.54 |           1.76 |      0.46  | 18-32     | 10-6        |
| warm/dome team in cold      | a warm or dome team in the cold |      70 |         4.7  |        2.7  |               2    |           9.99 |           1.39 |           1.35 |      0.391 | 6-17      | 7-2         |
| warm/dome team in cold      | no                              |    2825 |        -0.08 |       -0.48 |               0.4  |           0.09 |          -0.31 |           0.01 |      0.491 | 211-199   | 374-312     |
| primetime                   | day                             |    2299 |        -0.18 |       -0.66 |               0.48 |           0.46 |          -0.77 |          -0.21 |      0.496 | 176-163   | 276-253     |
| primetime                   | primetime                       |     596 |         0.88 |        0.59 |               0.29 |          -0.09 |           1.81 |           0.93 |      0.458 | 41-53     | 105-61      |
| division                    | division                        |    1056 |         0.72 |       -0.05 |               0.77 |           1.09 |           0.47 |           0.58 |      0.487 | 93-92     | 117-96      |
| division                    | non-division                    |    1839 |        -0.36 |       -0.6  |               0.25 |          -0.1  |          -0.68 |          -0.26 |      0.49  | 124-124   | 264-218     |
| week                        | 1-4                             |     698 |        -0.35 |       -0.42 |               0.08 |          -0.77 |          -0.46 |           0.35 |      0.489 | 43-37     | 98-104      |
| week                        | 5-13                            |    1425 |         0.16 |       -0.08 |               0.24 |          -0.15 |           0.39 |           0.26 |      0.48  | 100-100   | 221-151     |
| week                        | 14-18                           |     772 |         0.16 |       -0.97 |               1.13 |           2.45 |          -1.28 |          -0.6  |      0.503 | 74-79     | 62-59       |
| rest                        | a team off a bye                |     666 |        -0.01 |       -0.24 |               0.23 |          -0.48 |          -0.18 |           0.77 |      0.48  | 39-54     | 95-77       |
| rest                        | normal                          |    2042 |         0.09 |       -0.38 |               0.48 |           0.71 |          -0.3  |          -0.16 |      0.491 | 157-149   | 259-222     |
| rest                        | short week (Thursday)           |     187 |        -0.41 |       -1.16 |               0.74 |          -0.69 |          -0.04 |          -0.53 |      0.495 | 21-13     | 27-15       |
| pace (both offenses' plays) | slow third                      |     965 |         0.08 |       -0.69 |               0.77 |           0.45 |          -0.61 |           0.54 |      0.502 | 87-79     | 96-95       |
| pace (both offenses' plays) | middle third                    |     965 |         0.22 |       -0.17 |               0.39 |           0.61 |           0.02 |          -0.02 |      0.484 | 74-69     | 120-115     |
| pace (both offenses' plays) | fast third                      |     965 |        -0.18 |       -0.34 |               0.15 |          -0.01 |          -0.16 |          -0.44 |      0.48  | 56-68     | 165-104     |
| offenses                    | both below median               |     733 |        -0.19 |       -1.05 |               0.87 |           0.08 |          -0.25 |          -0.44 |      0.503 | 78-54     | 74-65       |
| offenses                    | both offenses above median      |     733 |        -0.95 |       -0.86 |              -0.09 |          -0.34 |          -1.54 |          -0.83 |      0.512 | 35-43     | 107-111     |
| offenses                    | one of each                     |    1429 |         0.66 |        0.17 |               0.49 |           0.81 |           0.46 |           0.73 |      0.469 | 104-119   | 200-138     |
| defenses                    | both defenses bad               |     709 |        -0.1  |       -0.48 |               0.38 |          -0.25 |           0.08 |          -0.16 |      0.49  | 55-56     | 104-82      |
| defenses                    | both defenses good              |     709 |         0.82 |        0.31 |               0.51 |           0.27 |           1.22 |           1.01 |      0.474 | 52-57     | 94-68       |
| defenses                    | one of each                     |    1477 |        -0.27 |       -0.7  |               0.43 |           0.63 |          -1.13 |          -0.33 |      0.495 | 110-103   | 183-164     |
| referee (ref_tot)           | referee low-scoring third       |     965 |        -0.08 |        0.44 |              -0.52 |           0.67 |          -0.54 |          -0.41 |      0.455 | 27-30     | 199-134     |
| referee (ref_tot)           | middle third                    |     965 |        -0.34 |       -0.85 |               0.51 |          -0.38 |          -0.01 |          -0.79 |      0.518 | 63-67     | 98-105      |
| referee (ref_tot)           | high-scoring third              |     965 |         0.54 |       -0.79 |               1.33 |           0.71 |          -0.27 |           1.4  |      0.494 | 127-119   | 84-75       |
| sign of the edge            | model over the line             |    1689 |         1.38 |       -0.84 |               2.22 |           2.2  |           1.07 |           0.83 |      0.505 | 217-216   | 0-0         |
| sign of the edge            | model under the line            |    1206 |        -1.85 |        0.21 |              -2.06 |          -2.11 |          -1.76 |          -1.59 |      0.465 | 0-0       | 381-314     |
| signed edge                 | under 6+                        |      35 |        -3.2  |        4.14 |              -7.34 |          -3.58 |          -3.4  |           1.38 |      0.286 | 0-0       | 25-10       |
| signed edge                 | under 4-6                       |     108 |        -3.25 |        1.54 |              -4.79 |          -6.13 |          -0.9  |          -4.62 |      0.37  | 0-0       | 67-40       |
| signed edge                 | under 2-4                       |     356 |        -3.17 |       -0.28 |              -2.89 |          -3.47 |          -2.17 |          -5.24 |      0.476 | 0-0       | 180-164     |
| signed edge                 | under 0-2                       |     707 |        -0.9  |        0.06 |              -0.96 |          -0.75 |          -1.56 |          -0.23 |      0.484 | 0-0       | 109-100     |
| signed edge                 | over 0-2                        |     874 |         0.16 |       -0.83 |               0.99 |           0.96 |          -0.24 |          -0.33 |      0.503 | 0-0       | 0-0         |
| signed edge                 | over 2-4                        |     574 |         2.39 |       -0.46 |               2.85 |           2.62 |           3.3  |           1.42 |      0.503 | 105-105   | 0-0         |
| signed edge                 | over 4-6                        |     194 |         3.57 |       -1.14 |               4.71 |           6.38 |           2.91 |           2.09 |      0.497 | 86-94     | 0-0         |
| signed edge                 | over 6+                         |      47 |         2.83 |       -4.31 |               7.14 |           5.54 |          -2.29 |           4.77 |      0.617 | 26-17     | 0-0         |

All games: actual minus line mean +0.40, median -0.50, unders win 51.1% of non-push games; model minus actual mean +0.04, median +0.71.

Referees (27 with 40+ games): the spread of their mean misses is 0.66x what chance gives (variance 1.423 against 2.146); odd-season against even-season mean miss correlates -0.187 over 21 referees; between-referee sd about 0.0 points.

## Part 2: fixes to the total and the chance

The walk-forward refits the total equation before every week (training from 2013), exactly as `M.walk_forward` prices the total; the base run matches pred_v3 (model_total within 3.6e-14, p_over_emp within 0.0e+00). Knobs picked on 2019-22 MAE: shrink s = 1.00 (no shrink: the best s below 1, s 0.95, misses 2019-22 by 10.5510 against 10.5406), upside = 1.0 (no cap: the best factor below 1, above the mean x 0.9, misses 2019-22 by 10.5458 against 10.5406). The weekly-refit s (from earlier out-of-sample misses) ran 0.647 / 0.925 (2015 Week 1 / 2025 last week).

Each cell: total MAE / bias (model minus actual) / 55%+ under record (win rate, units) / 55%+ over record / 3+ edge over record / log loss of the over chance.

| family | variant | 2015-18 | 2019-22 | 2023-25 | verdict |
|---|---|---|---|---|---|
| base | live total equation, p_over_emp | 10.7437 / +0.35 / 135-127 (51.5%, -4.7u) / 121-124 / 70-66 / 0.7017 | 10.5406 / -0.26 / 175-128 (57.8%, +34.2u) / 104-108 / 61-65 / 0.6945 | 10.1767 / +0.04 / 71-59 (54.6%, +6.1u) / 132-123 / 86-85 / 0.6993 | base |
| a shrink | s 0.70 | 10.7153 / +0.38 / 140-142 (49.6%, -16.2u) / 121-107 / 80-65 / 0.7009 | 10.6292 / -0.28 / 180-157 (53.4%, +7.3u) / 100-105 / 65-63 / 0.6989 | 10.2300 / +0.20 / 67-72 (48.2%, -12.2u) / 130-124 / 100-89 / 0.7016 | not adopted: MAE better on 1/3, under 55% win rate better on 0/3 |
| a shrink | s 0.75 | 10.7150 / +0.38 / 136-135 (50.2%, -12.5u) / 114-108 / 74-66 / 0.7004 | 10.6073 / -0.28 / 176-150 (54.0%, +11.0u) / 98-105 / 62-63 / 0.6979 | 10.2169 / +0.17 / 68-73 (48.2%, -12.3u) / 129-122 / 93-88 / 0.7008 | not adopted: MAE better on 1/3, under 55% win rate better on 0/3 |
| a shrink | s 0.80 | 10.7164 / +0.37 / 135-128 (51.3%, -5.8u) / 109-105 / 71-63 / 0.7003 | 10.5894 / -0.27 / 175-148 (54.2%, +12.2u) / 97-105 / 61-63 / 0.6969 | 10.2047 / +0.15 / 70-73 (48.9%, -10.3u) / 125-124 / 95-88 / 0.7002 | not adopted: MAE better on 1/3, under 55% win rate better on 0/3 |
| a shrink | s 0.85 | 10.7199 / +0.37 / 131-123 (51.6%, -4.3u) / 107-106 / 73-63 / 0.7004 | 10.5749 / -0.27 / 178-143 (55.5%, +20.7u) / 96-112 / 59-60 / 0.6962 | 10.1941 / +0.12 / 69-68 (50.4%, -5.8u) / 125-124 / 94-89 / 0.6997 | not adopted: MAE better on 1/3, under 55% win rate better on 1/3 |
| a shrink | s 0.90 | 10.7251 / +0.36 / 131-117 (52.8%, +2.3u) / 109-108 / 72-62 / 0.7007 | 10.5623 / -0.27 / 179-139 (56.3%, +26.1u) / 97-110 / 59-57 / 0.6955 | 10.1857 / +0.09 / 67-65 (50.8%, -4.5u) / 126-123 / 90-91 / 0.6995 | not adopted: MAE better on 1/3, under 55% win rate better on 1/3 |
| a shrink | s 0.95 | 10.7330 / +0.35 / 129-119 (52.0%, -1.9u) / 111-112 / 69-64 / 0.7011 | 10.5510 / -0.26 / 174-136 (56.1%, +24.4u) / 98-110 / 58-59 / 0.6949 | 10.1800 / +0.06 / 68-61 (52.7%, +0.9u) / 133-124 / 89-88 / 0.6994 | not adopted: MAE better on 1/3, under 55% win rate better on 1/3 |
| a shrink | s refit weekly from earlier misses | 10.7232 / +0.41 / 140-138 (50.4%, -11.8u) / 115-110 / 82-63 / 0.7009 | 10.5694 / -0.27 / 181-144 (55.7%, +22.6u) / 97-107 / 61-60 / 0.6962 | 10.1861 / +0.09 / 69-64 (51.9%, -1.4u) / 125-126 / 91-89 / 0.6996 | not adopted: MAE better on 1/3, under 55% win rate better on 0/3 |
| b upside | above the mean x 0.5 | 10.7376 / -0.41 / 144-144 (50.0%, -14.4u) / 116-117 / 50-43 / 0.7022 | 10.6090 / -1.07 / 184-157 (54.0%, +11.3u) / 96-106 / 44-40 / 0.6977 | 10.1355 / -0.62 / 67-63 (51.5%, -2.3u) / 126-124 / 66-51 / 0.6988 | not adopted: MAE better on 2/3, under 55% win rate better on 0/3 |
| b upside | above the mean x 0.6 | 10.7314 / -0.26 / 139-139 (50.0%, -13.9u) / 113-111 / 55-48 / 0.7017 | 10.5863 / -0.91 / 181-152 (54.4%, +13.8u) / 95-103 / 45-44 / 0.6965 | 10.1386 / -0.49 / 63-63 (50.0%, -6.3u) / 128-125 / 69-56 / 0.6985 | not adopted: MAE better on 2/3, under 55% win rate better on 0/3 |
| b upside | above the mean x 0.7 | 10.7287 / -0.11 / 136-130 (51.1%, -7.0u) / 110-108 / 58-53 / 0.7015 | 10.5681 / -0.75 / 179-145 (55.2%, +19.5u) / 95-104 / 48-47 / 0.6957 | 10.1437 / -0.36 / 64-64 (50.0%, -6.4u) / 128-126 / 73-60 / 0.6986 | not adopted: MAE better on 2/3, under 55% win rate better on 0/3 |
| b upside | above the mean x 0.8 | 10.7311 / +0.04 / 131-124 (51.4%, -5.4u) / 107-107 / 60-56 / 0.7014 | 10.5552 / -0.59 / 180-136 (57.0%, +30.4u) / 97-109 / 51-54 / 0.6951 | 10.1500 / -0.23 / 65-64 (50.4%, -5.4u) / 129-125 / 76-70 / 0.6985 | not adopted: MAE better on 2/3, under 55% win rate better on 0/3 |
| b upside | above the mean x 0.9 | 10.7353 / +0.20 / 132-119 (52.6%, +1.1u) / 111-113 / 65-59 / 0.7014 | 10.5458 / -0.42 / 177-136 (56.5%, +27.4u) / 100-109 / 55-57 / 0.6947 | 10.1609 / -0.10 / 69-64 (51.9%, -1.4u) / 135-126 / 81-81 / 0.6989 | not adopted: MAE better on 2/3, under 55% win rate better on 1/3 |
| b upside | knee +2, beyond it x 0.3 | 10.7420 / -0.19 / 143-139 (50.7%, -9.9u) / 118-121 / 59-54 / 0.7032 | 10.5933 / -0.81 / 185-154 (54.6%, +15.6u) / 98-104 / 51-48 / 0.6971 | 10.1373 / -0.37 / 64-62 (50.8%, -4.2u) / 130-128 / 76-62 / 0.6985 | not adopted: MAE better on 2/3, under 55% win rate better on 0/3 |
| b upside | knee +2, beyond it x 0.5 | 10.7369 / -0.04 / 138-134 (50.7%, -9.4u) / 113-111 / 64-58 / 0.7021 | 10.5697 / -0.65 / 183-146 (55.6%, +22.4u) / 98-104 / 51-53 / 0.6957 | 10.1449 / -0.25 / 63-65 (49.2%, -8.5u) / 128-126 / 78-65 / 0.6984 | not adopted: MAE better on 2/3, under 55% win rate better on 0/3 |
| b upside | knee +4, beyond it x 0.3 | 10.7454 / +0.10 / 137-133 (50.7%, -9.3u) / 113-113 / 66-60 / 0.7023 | 10.5690 / -0.48 / 180-137 (56.8%, +29.3u) / 102-108 / 55-55 / 0.6954 | 10.1714 / -0.09 / 72-67 (51.8%, -1.7u) / 134-123 / 81-79 / 0.6996 | not adopted: MAE better on 1/3, under 55% win rate better on 0/3 |
| b upside | knee +4, beyond it x 0.5 | 10.7438 / +0.17 / 134-129 (50.9%, -7.9u) / 113-116 / 67-62 / 0.7018 | 10.5582 / -0.42 / 180-134 (57.3%, +32.6u) / 102-110 / 56-56 / 0.6949 | 10.1708 / -0.06 / 71-65 (52.2%, -0.5u) / 136-125 / 83-80 / 0.6994 | not adopted: MAE better on 1/3, under 55% win rate better on 0/3 |
| c chance | symmetric residuals (mirrored) | 10.7437 / +0.35 / 108-96 (52.9%, +2.4u) / 148-149 / 70-66 / 0.7024 | 10.5406 / -0.26 / 157-114 (57.9%, +31.6u) / 125-136 / 61-65 / 0.6957 | 10.1767 / +0.04 / 48-44 (52.2%, -0.4u) / 162-149 / 86-85 / 0.7006 | not adopted: MAE better on 0/3, under 55% win rate better on 2/3 |
| c chance | two-piece: upper half above, lower half below the median | 10.7437 / +0.35 / 141-130 (52.0%, -2.0u) / 121-123 / 70-66 / 0.7019 | 10.5406 / -0.26 / 175-127 (58.0%, +35.3u) / 110-115 / 61-65 / 0.6951 | 10.1767 / +0.04 / 70-58 (54.7%, +6.2u) / 137-128 / 86-85 / 0.6995 | ADOPTABLE |
| c chance | normal curve (p_over) | 10.7437 / +0.35 / 111-104 (51.6%, -3.4u) / 156-159 / 70-66 / 0.7021 | 10.5406 / -0.26 / 160-114 (58.4%, +34.6u) / 127-138 / 61-65 / 0.6953 | 10.1767 / +0.04 / 50-46 (52.1%, -0.6u) / 164-152 / 86-85 / 0.7001 | not adopted: MAE better on 0/3, under 55% win rate better on 2/3 |
| c chance | earlier out-of-sample misses, all | 10.7437 / +0.35 / 147-145 (50.3%, -12.5u) / 94-92 / 70-66 / 0.7014 | 10.5406 / -0.26 / 178-137 (56.5%, +27.3u) / 96-99 / 61-65 / 0.6946 | 10.1767 / +0.04 / 84-74 (53.2%, +2.6u) / 128-114 / 86-85 / 0.6992 | not adopted: MAE better on 0/3, under 55% win rate better on 0/3 |
| c chance | earlier out-of-sample misses, same projected half | 10.7437 / +0.35 / 139-140 (49.8%, -15.0u) / 86-80 / 70-66 / 0.7016 | 10.5406 / -0.26 / 184-136 (57.5%, +34.4u) / 93-102 / 61-65 / 0.6950 | 10.1767 / +0.04 / 87-75 (53.7%, +4.5u) / 126-114 / 86-85 / 0.6991 | not adopted: MAE better on 0/3, under 55% win rate better on 0/3 |
| d drift | offset: league mean of last 128 games x 0.5 | 10.7515 / +0.13 / 143-138 (50.9%, -8.8u) / 101-93 / 61-60 / 0.7029 | 10.5273 / -0.09 / 164-119 (58.0%, +33.1u) / 101-110 / 58-66 / 0.6933 | 10.1613 / -0.15 / 76-72 (51.3%, -3.2u) / 106-103 / 73-70 / 0.6987 | not adopted: MAE better on 2/3, under 55% win rate better on 1/3 |
| d drift | offset: league mean of last 128 games x 1 | 10.7888 / -0.08 / 145-157 (48.0%, -27.7u) / 89-88 / 64-60 / 0.7065 | 10.5828 / +0.07 / 159-118 (57.4%, +29.2u) / 119-123 / 77-79 / 0.6958 | 10.1726 / -0.34 / 96-86 (52.8%, +1.4u) / 100-94 / 67-61 / 0.6998 | not adopted: MAE better on 1/3, under 55% win rate better on 0/3 |
| d drift | offset: league mean of last 256 games x 0.5 | 10.7504 / +0.05 / 149-150 (49.8%, -16.0u) / 95-95 / 61-52 / 0.7028 | 10.5414 / +0.03 / 151-106 (58.8%, +34.4u) / 112-129 / 66-74 / 0.6947 | 10.1536 / -0.25 / 84-75 (52.8%, +1.5u) / 106-107 / 70-66 / 0.6985 | not adopted: MAE better on 1/3, under 55% win rate better on 1/3 |
| d drift | offset: league mean of last 256 games x 1 | 10.7685 / -0.25 / 169-175 (49.1%, -23.5u) / 80-79 / 49-48 / 0.7046 | 10.5811 / +0.32 / 126-87 (59.2%, +30.3u) / 131-139 / 80-89 / 0.6973 | 10.1547 / -0.54 / 94-83 (53.1%, +2.7u) / 89-80 / 63-56 / 0.6989 | not adopted: MAE better on 1/3, under 55% win rate better on 1/3 |
| d drift | offset: league mean of last 512 games x 0.5 | 10.7379 / +0.12 / 148-145 (50.5%, -11.5u) / 103-105 / 61-56 / 0.7013 | 10.5642 / +0.13 / 152-103 (59.6%, +38.7u) / 121-133 / 71-85 / 0.6960 | 10.1569 / -0.44 / 92-81 (53.2%, +2.9u) / 99-97 / 60-62 / 0.6990 | not adopted: MAE better on 2/3, under 55% win rate better on 1/3 |
| d drift | offset: league mean of last 512 games x 1 | 10.7370 / -0.11 / 167-161 (50.9%, -10.1u) / 93-85 / 54-50 / 0.7019 | 10.6038 / +0.52 / 120-83 (59.1%, +28.7u) / 148-164 / 94-102 / 0.6988 | 10.1588 / -0.92 / 115-99 (53.7%, +6.1u) / 73-67 / 39-42 / 0.6996 | not adopted: MAE better on 2/3, under 55% win rate better on 1/3 |
| d drift | own recent miss: last 128 games x 0.5 | 10.7571 / +0.21 / 135-138 (49.5%, -16.8u) / 110-106 / 66-62 / 0.7039 | 10.5154 / -0.21 / 177-121 (59.4%, +43.9u) / 105-110 / 57-63 / 0.6929 | 10.1872 / +0.01 / 72-65 (52.5%, +0.5u) / 122-123 / 85-77 / 0.7002 | not adopted: MAE better on 1/3, under 55% win rate better on 1/3 |
| d drift | own recent miss: last 128 games x 1 | 10.8005 / +0.07 / 144-155 (48.2%, -26.5u) / 111-108 / 65-63 / 0.7073 | 10.5522 / -0.17 / 176-129 (57.7%, +34.1u) / 118-122 / 72-68 / 0.6945 | 10.2052 / -0.02 / 77-70 (52.4%, +0.0u) / 121-125 / 83-75 / 0.7018 | not adopted: MAE better on 0/3, under 55% win rate better on 0/3 |
| d drift | own recent miss: last 256 games x 0.5 | 10.7506 / +0.10 / 148-148 (50.0%, -14.8u) / 98-102 / 63-55 / 0.7027 | 10.5221 / -0.16 / 172-121 (58.7%, +38.9u) / 107-119 / 63-66 / 0.6935 | 10.1653 / -0.05 / 75-69 (52.1%, -0.9u) / 122-118 / 85-80 / 0.6987 | not adopted: MAE better on 2/3, under 55% win rate better on 1/3 |
| d drift | own recent miss: last 256 games x 1 | 10.7670 / -0.14 / 158-163 (49.2%, -21.3u) / 84-89 / 55-51 / 0.7045 | 10.5332 / -0.06 / 160-115 (58.2%, +33.5u) / 110-118 / 72-76 / 0.6944 | 10.1594 / -0.13 / 85-68 (55.6%, +10.2u) / 118-122 / 77-74 / 0.6987 | not adopted: MAE better on 2/3, under 55% win rate better on 2/3 |
| e weather | + wind x pass rate | 10.7409 / +0.41 / 133-123 (51.9%, -2.3u) / 122-125 / 70-71 / 0.7024 | 10.5489 / -0.26 / 175-130 (57.4%, +32.0u) / 104-110 / 59-67 / 0.6951 | 10.1808 / +0.03 / 71-62 (53.4%, +2.8u) / 128-124 / 85-86 / 0.6997 | not adopted: MAE better on 1/3, under 55% win rate better on 1/3 |
| e weather | + warm/dome team in the cold | 10.7365 / +0.35 / 135-127 (51.5%, -4.7u) / 126-121 / 75-68 / 0.7008 | 10.5660 / -0.27 / 177-130 (57.6%, +34.0u) / 103-105 / 62-66 / 0.6950 | 10.1808 / +0.06 / 73-60 (54.9%, +7.0u) / 134-120 / 86-87 / 0.6991 | not adopted: MAE better on 1/3, under 55% win rate better on 1/3 |
| e weather | + both | 10.7349 / +0.41 / 132-125 (51.4%, -5.5u) / 125-121 / 76-73 / 0.7016 | 10.5745 / -0.27 / 176-127 (58.1%, +36.3u) / 105-107 / 60-65 / 0.6954 | 10.1846 / +0.06 / 73-60 (54.9%, +7.0u) / 132-120 / 85-87 / 0.6995 | not adopted: MAE better on 1/3, under 55% win rate better on 2/3 |
| e weather | + both, and the pass-rate sum | 10.6942 / +0.45 / 139-122 (53.3%, +4.8u) / 136-125 / 78-78 / 0.6989 | 10.6159 / -0.26 / 174-140 (55.4%, +20.0u) / 113-114 / 67-73 / 0.6975 | 10.2020 / -0.05 / 75-69 (52.1%, -0.9u) / 120-111 / 87-85 / 0.6992 | not adopted: MAE better on 1/3, under 55% win rate better on 1/3 |
| f team points | sum of the ridge points equation (own misses for the chance) | 10.7986 / +0.15 / 170-153 (52.6%, +1.7u) / 109-127 / 65-82 / 0.7042 | 10.5845 / -0.24 / 181-142 (56.0%, +24.8u) / 121-111 / 69-66 / 0.6968 | 10.3148 / +0.40 / 52-51 (50.5%, -4.1u) / 147-140 / 105-101 / 0.7036 | not adopted: MAE better on 0/3, under 55% win rate better on 1/3 |
| f team points | sum of the live seven-model blend (pred_v3; total equation's misses for the chance) | 10.7576 / +0.12 / 158-136 (53.7%, +8.4u) / 105-125 / 64-76 / 0.7012 | 10.5760 / -0.24 / 171-132 (56.4%, +25.8u) / 117-117 / 72-60 / 0.6962 | 10.2811 / +0.39 / 52-47 (52.5%, +0.3u) / 156-149 / 108-96 / 0.7020 | not adopted: MAE better on 0/3, under 55% win rate better on 1/3 |
| f team points | half the total equation, half the blend sum | 10.6969 / +0.23 / 145-126 (53.5%, +6.4u) / 105-109 / 53-59 / 0.6988 | 10.5241 / -0.25 / 158-124 (56.0%, +21.6u) / 94-101 / 50-55 / 0.6930 | 10.1953 / +0.21 / 51-51 (50.0%, -5.1u) / 136-131 / 83-81 / 0.6986 | not adopted: MAE better on 2/3, under 55% win rate better on 1/3 |

### The two-piece chance against the live one at neighbouring under cuts

| cut   | live 2015-18    | two-piece 2015-18   |   flags changed 2015-18 | live 2019-22     | two-piece 2019-22   |   flags changed 2019-22 | live 2023-25    | two-piece 2023-25   |   flags changed 2023-25 |
|:------|:----------------|:--------------------|------------------------:|:-----------------|:--------------------|------------------------:|:----------------|:--------------------|------------------------:|
| 53%   | 189-176 (-4.6u) | 185-176 (-8.6u)     |                      20 | 222-187 (+16.3u) | 226-185 (+22.5u)    |                      16 | 116-100 (+6.0u) | 114-95 (+9.5u)      |                       7 |
| 54%   | 161-155 (-9.5u) | 162-156 (-9.6u)     |                      18 | 192-157 (+19.3u) | 194-158 (+20.2u)    |                      13 | 93-83 (+1.7u)   | 90-81 (+0.9u)       |                       5 |
| 55%   | 135-127 (-4.7u) | 141-130 (-2.0u)     |                      15 | 175-128 (+34.2u) | 175-127 (+35.3u)    |                      11 | 71-59 (+6.1u)   | 70-58 (+6.2u)       |                       3 |
| 56%   | 115-103 (+1.7u) | 119-113 (-5.3u)     |                      19 | 159-114 (+33.6u) | 154-111 (+31.9u)    |                       8 | 52-52 (-5.2u)   | 51-52 (-6.2u)       |                       1 |
| 57%   | 95-86 (+0.4u)   | 99-88 (+2.2u)       |                      20 | 143-99 (+34.1u)  | 135-90 (+36.0u)     |                      17 | 41-39 (-1.9u)   | 37-37 (-3.7u)       |                       6 |
| 58%   | 83-72 (+3.8u)   | 83-71 (+4.9u)       |                      15 | 125-84 (+32.6u)  | 116-73 (+35.7u)     |                      21 | 35-31 (+0.9u)   | 33-31 (-1.1u)       |                       2 |
| 60%   | 64-53 (+5.7u)   | 60-46 (+9.4u)       |                      12 | 102-58 (+38.2u)  | 89-41 (+43.9u)      |                      30 | 24-24 (-2.4u)   | 21-16 (+3.4u)       |                      11 |

**Reading Part 2.** No change to the equation passes, and nothing moves the over side:

- (a) Shrinking the total toward the training mean lowers the 2015-18 miss (the 2017 drop) and raises the miss on 2019-22 and
  2023-25 at every s; fitted on 2019-22 the best s is 1.0 (no shrink). The out-of-sample slope of actual on projection is
  0.65 to 0.93, so the deviations are too big for the average, but shrinking does not lower the absolute miss outside
  2015-18, and the under record falls on 2019-22 and 2023-25 at every s.
- (b) Capping the upside at 0.5 to 0.9 of the deviation cuts the 2015-18 and 2023-25 misses, raises 2019-22, drags the bias
  negative and costs the under record on 2019-22 and 2023-25 at every factor. The overs it removes were not the losing ones (the over 3+ record
  shrinks without improving).
- (c) The two-piece chance meets the letter of the rule at the 55% cut by 1 to 6 bets a window (141-130, 175-127, 70-58
  against 135-127, 175-128, 71-59), but at 53, 54, 56, 57 and 58% it is worse by units on at least one window (it is
  ahead on all three only at 55 and 60%), it
  changes only 3 to 15 flags a window, and its log loss is worse on all three windows: a coin-flip difference, not adopted.
  The symmetric and normal chances drop the skew and with it a third of the unders; the out-of-sample pools read
  slightly better by log loss on two windows but lose under record on all three, and no over rule on them wins.
- (d) Both new drift forms (a league-level offset with a fixed coefficient, and a correction by the equation's own recent
  miss) trade windows the way the scoring_env inputs did: the 128/256-game forms help 2019-22 or 2023-25 and hurt 2015-18;
  the 512-game offset helps 2015-18 and 2023-25 and hurts 2019-22.
- (e) Wind x both teams' pass rate and the warm-or-dome-team-in-the-cold count lower the 2015-18 miss only; the cold-game
  overshoot is almost all 2015-18 (+9.99 there, +1.4 since), 70 games in all.
- (f) The sum of the team-points equations misses by more on every window (blend sum 10.758 / 10.576 / 10.281 against
  10.744 / 10.541 / 10.177); half of each is better on two windows and worse on 2023-25. The total keeps its own equation.

## Part 3: rules

### Over rules (live p_over_emp and the edge), the 15 best by their worst window

| side   | rule                          | filter        | rec 2015-18   | rec 2019-22   | rec 2023-25   | rec 2015-25   |   roi 2015-18 |   roi 2019-22 |   roi 2023-25 |   units 2015-25 | wins all three   |
|:-------|:------------------------------|:--------------|:--------------|:--------------|:--------------|:--------------|--------------:|--------------:|--------------:|----------------:|:-----------------|
| over   | over, chance 60%+             | line under 43 | 31-25         | 18-16         | 33-27         | 82-68         |         0.057 |         0.011 |         0.05  |             7.2 | True             |
| over   | over, chance 65%+             | all           | 13-12         | 11-7          | 10-8          | 34-27         |        -0.007 |         0.167 |         0.061 |             4.3 | False            |
| over   | over, chance 58%+             | line under 43 | 38-34         | 31-30         | 51-40         | 120-104       |         0.008 |        -0.03  |         0.07  |             5.6 | False            |
| over   | over, chance 55%+             | division      | 53-52         | 47-44         | 46-45         | 146-141       |        -0.036 |        -0.014 |        -0.035 |            -9.1 | False            |
| over   | over, chance 55%+             | line under 43 | 58-49         | 40-40         | 82-63         | 180-152       |         0.035 |        -0.045 |         0.08  |            12.8 | False            |
| over   | over, chance 60%+             | day games     | 44-36         | 33-33         | 35-35         | 112-104       |         0.05  |        -0.045 |        -0.045 |            -2.4 | False            |
| over   | over, edge 4+                 | outdoors      | 29-24         | 21-17         | 23-23         | 73-64         |         0.045 |         0.055 |        -0.045 |             2.6 | False            |
| over   | over, edge 2+                 | weeks 9-17    | 86-87         | 69-69         | 76-73         | 231-229       |        -0.051 |        -0.045 |        -0.026 |           -20.9 | False            |
| over   | over, chance 58%+             | all           | 71-65         | 68-69         | 78-78         | 217-212       |        -0.003 |        -0.052 |        -0.045 |           -16.2 | False            |
| over   | over, edge 2+                 | division      | 63-56         | 47-48         | 50-51         | 160-155       |         0.011 |        -0.056 |        -0.055 |           -10.5 | False            |
| over   | over, edge 2+                 | line under 43 | 62-51         | 44-45         | 87-66         | 193-162       |         0.047 |        -0.056 |         0.086 |            14.8 | False            |
| over   | over, chance 58%+             | division      | 30-31         | 33-32         | 34-26         | 97-89         |        -0.061 |        -0.031 |         0.082 |            -0.9 | False            |
| over   | over, edge 3+ and chance 55%+ | line under 43 | 38-35         | 29-30         | 57-43         | 124-108       |        -0.006 |        -0.062 |         0.088 |             5.2 | False            |
| over   | over, edge 3+                 | line under 43 | 38-35         | 29-30         | 57-43         | 124-108       |        -0.006 |        -0.062 |         0.088 |             5.2 | False            |
| over   | over, chance 55%+             | weeks 9-17    | 79-82         | 68-68         | 71-65         | 218-215       |        -0.063 |        -0.045 |        -0.003 |           -18.5 | False            |

Over rules tried: 100; winning all three windows: 1.

### The under rule's cutoff, every game

| side   | rule               | filter   | rec 2015-18   | rec 2019-22   | rec 2023-25   | rec 2015-25   |   roi 2015-18 |   roi 2019-22 |   roi 2023-25 |   units 2015-25 | wins all three   |
|:-------|:-------------------|:---------|:--------------|:--------------|:--------------|:--------------|--------------:|--------------:|--------------:|----------------:|:-----------------|
| under  | under, chance 52%+ | all      | 216-203       | 245-201       | 132-114       | 593-518       |        -0.016 |         0.049 |         0.024 |            23.2 | False            |
| under  | under, chance 53%+ | all      | 189-176       | 222-187       | 116-100       | 527-463       |        -0.011 |         0.036 |         0.025 |            17.7 | False            |
| under  | under, chance 54%+ | all      | 161-155       | 192-157       | 93-83         | 446-395       |        -0.027 |         0.05  |         0.009 |            11.5 | False            |
| under  | under, chance 55%+ | all      | 135-127       | 175-128       | 71-59         | 381-314       |        -0.016 |         0.103 |         0.043 |            35.6 | False            |
| under  | under, chance 56%+ | all      | 115-103       | 159-114       | 52-52         | 326-269       |         0.007 |         0.112 |        -0.045 |            30.1 | False            |
| under  | under, chance 57%+ | all      | 95-86         | 143-99        | 41-39         | 279-224       |         0.002 |         0.128 |        -0.022 |            32.6 | False            |
| under  | under, chance 58%+ | all      | 83-72         | 125-84        | 35-31         | 243-187       |         0.022 |         0.142 |         0.012 |            37.3 | True             |
| under  | under, chance 60%+ | all      | 64-53         | 102-58        | 24-24         | 190-135       |         0.044 |         0.217 |        -0.045 |            41.5 | False            |
| under  | under, chance 62%+ | all      | 45-29         | 71-34         | 20-13         | 136-76        |         0.161 |         0.291 |         0.157 |            52.4 | True             |
| under  | under, chance 65%+ | all      | 26-15         | 32-14         | 6-5           | 64-34         |         0.211 |         0.328 |         0.041 |            26.6 | False            |
| under  | under, edge 2+     | all      | 95-83         | 140-96        | 37-35         | 272-214       |         0.019 |         0.133 |        -0.019 |            36.6 | False            |
| under  | under, edge 2.5+   | all      | 74-63         | 114-72        | 27-30         | 215-165       |         0.031 |         0.17  |        -0.096 |            33.5 | False            |
| under  | under, edge 3+     | all      | 61-46         | 95-50         | 21-16         | 177-112       |         0.088 |         0.251 |         0.084 |            53.8 | True             |
| under  | under, edge 3.5+   | all      | 45-31         | 72-34         | 17-9          | 134-74        |         0.13  |         0.297 |         0.248 |            52.6 | True             |
| under  | under, edge 4+     | all      | 31-23         | 53-21         | 8-6           | 92-50         |         0.096 |         0.367 |         0.091 |            37   | False            |
| under  | under, edge 5+     | all      | 20-8          | 26-12         | 5-3           | 51-23         |         0.364 |         0.306 |         0.193 |            25.7 | False            |
| under  | under, edge 6+     | all      | 10-4          | 14-5          | 1-1           | 25-10         |         0.364 |         0.407 |        -0.045 |            14   | False            |

### The 55% under rule by filter

| side   | rule               | filter        | rec 2015-18   | rec 2019-22   | rec 2023-25   | rec 2015-25   |   roi 2015-18 |   roi 2019-22 |   roi 2023-25 |   units 2015-25 | wins all three   |
|:-------|:-------------------|:--------------|:--------------|:--------------|:--------------|:--------------|--------------:|--------------:|--------------:|----------------:|:-----------------|
| under  | under, chance 55%+ | all           | 135-127       | 175-128       | 71-59         | 381-314       |        -0.016 |         0.103 |         0.043 |            35.6 | False            |
| under  | under, chance 55%+ | indoors       | 22-16         | 30-33         | 19-12         | 71-61         |         0.105 |        -0.091 |         0.17  |             3.9 | False            |
| under  | under, chance 55%+ | outdoors      | 113-111       | 145-95        | 52-47         | 310-253       |        -0.037 |         0.153 |         0.003 |            31.7 | False            |
| under  | under, chance 55%+ | line 47+      | 75-69         | 105-86        | 36-30         | 216-185       |        -0.006 |         0.05  |         0.041 |            12.5 | False            |
| under  | under, chance 55%+ | line under 43 | 18-18         | 17-12         | 11-7          | 46-37         |        -0.045 |         0.119 |         0.167 |             5.3 | False            |
| under  | under, chance 55%+ | primetime     | 41-25         | 45-23         | 19-13         | 105-61        |         0.186 |         0.263 |         0.134 |            37.9 | True             |
| under  | under, chance 55%+ | day games     | 94-102        | 130-105       | 52-46         | 276-253       |        -0.084 |         0.056 |         0.013 |            -2.3 | False            |
| under  | under, chance 55%+ | division      | 54-43         | 49-36         | 14-17         | 117-96        |         0.063 |         0.101 |        -0.138 |            11.4 | False            |
| under  | under, chance 55%+ | weeks 1-8     | 67-82         | 92-70         | 37-31         | 196-183       |        -0.142 |         0.084 |         0.039 |            -5.3 | False            |
| under  | under, chance 55%+ | weeks 9-17    | 68-45         | 83-58         | 34-28         | 185-131       |         0.149 |         0.124 |         0.047 |            40.9 | True             |

### Over rules read off the out-of-sample chance (Part 2 c), the 8 best by worst window

| source                | side   | rule                          | filter        | rec 2015-18   | rec 2019-22   | rec 2023-25   | rec 2015-25   |   roi 2015-18 |   roi 2019-22 |   roi 2023-25 |   units 2015-25 | wins all three   |
|:----------------------|:-------|:------------------------------|:--------------|:--------------|:--------------|:--------------|:--------------|--------------:|--------------:|--------------:|----------------:|:-----------------|
| oos misses, all       | over   | over, chance 55%+             | line under 43 | 47-40         | 39-36         | 79-58         | 165-134       |         0.031 |        -0.007 |         0.101 |            17.6 | False            |
| oos misses, all       | over   | over, chance 58%+             | day games     | 40-37         | 50-44         | 56-52         | 146-133       |        -0.008 |         0.015 |        -0.01  |            -0.3 | False            |
| oos misses, all       | over   | over, chance 55%+             | division      | 41-40         | 43-41         | 45-40         | 129-121       |        -0.034 |        -0.023 |         0.011 |            -4.1 | False            |
| oos misses, same half | over   | over, edge 4+                 | outdoors      | 29-24         | 21-17         | 23-23         | 73-64         |         0.045 |         0.055 |        -0.045 |             2.6 | False            |
| oos misses, same half | over   | over, edge 3+ and chance 55%+ | day games     | 48-48         | 56-48         | 68-60         | 172-156       |        -0.045 |         0.028 |         0.014 |             0.4 | False            |
| oos misses, same half | over   | over, chance 60%+             | outdoors      | 21-17         | 21-19         | 21-21         | 63-57         |         0.055 |         0.002 |        -0.045 |             0.3 | False            |
| oos misses, same half | over   | over, chance 58%+             | day games     | 37-37         | 51-45         | 55-52         | 143-134       |        -0.045 |         0.014 |        -0.019 |            -4.4 | False            |
| oos misses, same half | over   | over, chance 58%+             | line under 43 | 31-31         | 28-28         | 46-35         | 105-94        |        -0.045 |        -0.045 |         0.084 |             1.6 | False            |

Over rules on those chances winning all three windows: 0 of 200.

### By season (weeks 1-17)

| rule                             | 2015   | 2016   | 2017   | 2018   | 2019   | 2020   | 2021   | 2022   | 2023   | 2024   | 2025   | 2015-25   |   units |   losing seasons |
|:---------------------------------|:-------|:-------|:-------|:-------|:-------|:-------|:-------|:-------|:-------|:-------|:-------|:----------|--------:|-----------------:|
| under, chance 55%+ (live)        | 42-34  | 23-33  | 20-19  | 50-41  | 30-23  | 66-56  | 56-38  | 23-11  | 22-13  | 23-26  | 26-20  | 381-314   |    35.6 |                2 |
| under, chance 58%+               | 28-16  | 13-16  | 14-8   | 28-32  | 17-12  | 51-39  | 42-28  | 15-5   | 13-8   | 9-12   | 13-11  | 243-187   |    37.3 |                3 |
| under, chance 62%+               | 19-7   | 10-4   | 3-4    | 13-14  | 8-4    | 36-19  | 22-11  | 5-0    | 7-5    | 5-3    | 8-5    | 136-76    |    52.4 |                2 |
| under, edge 3+                   | 24-12  | 11-11  | 7-6    | 19-17  | 12-4   | 43-28  | 30-17  | 10-1   | 8-5    | 5-4    | 8-7    | 177-112   |    53.8 |                0 |
| under, edge 4+                   | 10-6   | 10-3   | 2-4    | 9-10   | 5-2    | 32-10  | 14-9   | 2-0    | 3-2    | 2-2    | 3-2    | 92-50     |    37   |                2 |
| over, chance 60%+, line under 43 | 9-6    | 3-6    | 11-8   | 8-5    | 1-3    | 1-1    | 3-3    | 13-9   | 13-8   | 11-10  | 9-9    | 82-68     |     7.2 |                2 |
| over, edge 3+                    | 15-21  | 14-17  | 24-17  | 17-11  | 11-12  | 9-5    | 19-20  | 22-28  | 26-33  | 31-25  | 29-27  | 217-216   |   -20.6 |                6 |

### Units at -110 and the bootstrap chance that ROI is above zero (10,000 resamples of the bets)

| which                                 | rule               | filter        | rec 2015-18   | rec 2019-22   | rec 2023-25   | rec 2015-25   |   units 2015-18 |   units 2019-22 |   units 2023-25 |   units 2015-25 |   P(roi>0) 2015-18 |   P(roi>0) 2019-22 |   P(roi>0) 2023-25 |   P(roi>0) 2015-25 |
|:--------------------------------------|:-------------------|:--------------|:--------------|:--------------|:--------------|:--------------|----------------:|----------------:|----------------:|----------------:|-------------------:|-------------------:|-------------------:|-------------------:|
| best over rule (by worst window)      | over, chance 60%+  | line under 43 | 31-25         | 18-16         | 33-27         | 82-68         |             3.5 |             0.4 |             3.3 |             7.2 |              0.655 |              0.567 |              0.655 |              0.714 |
| best under rule (by worst window)     | under, chance 62%+ | all           | 45-29         | 71-34         | 20-13         | 136-76        |            13.1 |            33.6 |             5.7 |            52.4 |              0.937 |              0.999 |              0.818 |              1     |
| the live under rule (55%, every game) | under, chance 55%+ | all           | 135-127       | 175-128       | 71-59         | 381-314       |            -4.7 |            34.2 |             6.1 |            35.6 |              0.382 |              0.975 |              0.669 |              0.888 |
| under, 58% chance                     | under, chance 58%+ | all           | 83-72         | 125-84        | 35-31         | 243-187       |             3.8 |            32.6 |             0.9 |            37.3 |              0.586 |              0.986 |              0.556 |              0.955 |
| under, 3+ edge                        | under, edge 3+     | all           | 61-46         | 95-50         | 21-16         | 177-112       |            10.4 |            40   |             3.4 |            53.8 |              0.81  |              1     |              0.695 |              0.999 |
| under, 4+ edge                        | under, edge 4+     | all           | 31-23         | 53-21         | 8-6           | 92-50         |             5.7 |            29.9 |             1.4 |            37   |              0.765 |              1     |              0.61  |              0.999 |

**Reading Part 3.** One over rule of 100 meets the letter: over at a 60%+ chance on a line under 43 (31-25, 18-16, 33-27,
+7.2 units, bootstrap chance of a positive ROI 0.71 over 2015-25, two losing seasons of eleven). At a true 50% a rule has
about a one-in-three chance of a positive ROI in a window of 60 to 100 bets, so about 3 of 100 rules would pass all three
windows by luck alone; one passing is less than chance. No over rule is adopted. Over 3+ has six losing seasons of eleven.

The live under rule (55%) no longer wins on all three windows: 2015-18 is 135-127, -4.7 units (ROI -1.6%, bootstrap 0.38).
The cuts that do: chance 58% (243-187, +37.3u, but 2023-25 is +0.9u), 62% (136-76, +52.4u), and the edge 3+ and 3.5+
(177-112, +53.8u; 134-74, +52.6u). Under at 3+ points of edge has no losing season in eleven (2016 is 11-11), and every
edge cut from 3 up is positive on every window (4+ and 5+ have under 15 bets in 2023-25). Its bootstrap chance of a positive
ROI is 0.81 / 1.00 / 0.70 by window and 0.999 over 2015-25. Of the 55% rule's filters, primetime and weeks 9-17 win all
three windows (105-61, 185-131), but those are two of nine filters tried on it.

## Verdict

- **The total equation and the chance: nothing adopted.** No form of shrink, upside cap, drift term, weather interaction
  or team-points sum lowers the total miss on all three windows, and none lifts the under record on all three; the one
  chance that meets the letter (two-piece) does so by a handful of bets, reverses at the neighbouring cuts and scores worse
  by log loss on every window. The total equation, TOTAL_FEATS and p_over_emp stay as they are.
- **Overs: no rule.** The overs lose because the typical game lands under the line, because the equation's over-leans run
  1.4 points hot (mostly its biggest projections, cold games with warm or dome teams, primetime and mismatched offenses),
  and because the chance does not know either. One over rule of 100 passes, fewer than luck gives; keep overs unflagged.
- **Unders: the 55% cut fails the every-window rule on 2015-18 today** (135-127, -4.7u). Under at 3+ points of edge (model
  total 3 or more below the line) wins on all three windows (61-46, 95-50, 21-16; +10.4, +40.0, +3.4 units at -110; 177-112,
  +53.8u, ROI +16.9% over 2015-25), with no losing season, and every edge cut from 3 up is positive on every window. It
  meets the adoption rule and is recommended as the tracked totals flag in place of the 55% chance. Caveats: it was chosen
  after all three windows were seen (15 under rules tried), so no untouched window is left to confirm it; 2023-25 is thin
  (37 bets, bootstrap 0.70); and on the 25 Sep equation (before qb_form_sum and ref_tot) the same rule was 10-13 on 2023-25
  (reports/totals_fix.csv), so the record moves with the equation. Grade it live, not bet, as the 55% rule is now.

## Runtime

- base walk-forward (2014-2025, weekly): 4.9 s
- part 1: 2.3 s
- s refit, first/last: 0.647 / 0.925
- (f) ridge-sum walk-forward: 8.5 s
- part 2: 133.6 s
- part 3: 10.1 s
