# A calibrated chance for every yards prop line

29 Sep 2026. experiments/props_chance.py. A calibrated chance for every yards prop line (29 Sep 2026). The player projection (nflmodel/props.py) sets each yards line L as a median (the median factor MED / MED_TIER on the projected mean M) and keeps the mean beside it, but carries no chance that the actual beats a book number x: the grading picks a side by edge = projection - line, and the page ranks only game bets, which have a calibrated chance. Here every player-game of the walk-forward frame (experiments/props_by_season.build: the live rule's inputs, its line L, its mean M and what happened) is given P(actual > x) for an arbitrary book number x from three families, every parameter fitted on 2017-18 only, and scored on 2019-22 and 2023-25 at hypothetical book numbers x = L + delta (delta in -15 .. +15 yards in steps of 5; passing x3; receptions -2 .. +2 catches; a number below 0.5 is dropped, no book hangs one):

## Adoption rule (set before the run)

Per stat, the distribution with the lowest mean log loss over the delta grid on 2019-22 is adopted only if it is also the lowest on 2023-25 and its reliability (bins of the stated chance pooled over the deltas) is within 3 points of the stated chance in every bin with n >= 200 on both windows. Where the best by log loss fails the reliability check, the best one that passes it on both windows is named instead and the report says so. Nothing here reads a book line: x is an offset from our own line L.

## Frames

The walk-forward by-season frame (experiments/props_by_season.build): every player-game with a touch of the kind, projected from the previous games only. L is the live rule's line (the median factor on the mean, the team reconciliation, the injury report and snap trend), M = L / the median factor, i.e. the mean scaled the same way, which is what the card's proj_*_yards_mean carries. The frame grades only games with a touch, so a chance read off it is for a player who gets on the stat sheet; the zero-touch games of a projected player (the active frame of round 17) are not in it, and a line for a player at risk of no touches is not covered.

- rec_yards: 36630 player-games 2017-25, 7518 in the fit window 2017-18, 16076 in 2019-22, 12383 in 2023-25.
- rush_yards: 17788 player-games 2017-25, 3497 in the fit window 2017-18, 7778 in 2019-22, 6196 in 2023-25.
- pass_yards: 5031 player-games 2017-25, 1046 in the fit window 2017-18, 2176 in 2019-22, 1712 in 2023-25.
- rec_catches: 36630 player-games 2017-25, 7518 in the fit window 2017-18, 16076 in 2019-22, 12383 in 2023-25.

## Fitted parameters (2017-18, chosen by the delta-grid log loss)

Parametric tiers are tiers of M (the mean) with the empirical tiers' edges (tiers of L for the L-centred forms); the empirical tiers are tiers of L (the line). Forms: normal_prop s = c M; normal_lin s = a + b M; normal_pow s = a M^b; lognorm sigma; lognorm_pow sigma = a M^b; gamma shape k; gamma_pow k = a M^b; normal_L mean L, s = a + b L; lognorm_L median L, sigma (lognorm_L_pow: sigma = a L^b); negbin size r (variance M + M^2 / r). A parameter at a bound of its search box (normal_lin a = 500, normal_pow a = 200 or b = 0.05, lognorm_pow at 50 or -1.5, gamma_pow at 0.001 or 1.5) means the form found no fit.

| stat        | dist           | params                                                                 |
|:------------|:---------------|:-----------------------------------------------------------------------|
| rec_yards   | normal_prop    | 1.4057                                                                 |
| rec_yards   | normal_lin     | 8.7447, 0.7044                                                         |
| rec_yards   | normal_pow     | 4.3903, 0.5773                                                         |
| rec_yards   | lognorm        | 0.9073                                                                 |
| rec_yards   | lognorm_pow    | 2.1908, -0.2784                                                        |
| rec_yards   | gamma          | 1.1019                                                                 |
| rec_yards   | gamma_pow      | 0.1749, 0.5894                                                         |
| rec_yards   | normal_L       | 15.2926, 0.3450                                                        |
| rec_yards   | lognorm_L      | 1.5140                                                                 |
| rec_yards   | lognorm_L_pow  | 5.4270, -0.4984                                                        |
| rec_yards   | normal_tier    | 0-20: 1.8767, 20-40: 0.9688, 40-60: 1.0990, 60-80: 0.8598, 80+: 0.9880 |
| rec_yards   | lognorm_tier   | 0-20: 1.0728, 20-40: 0.9228, 40-60: 0.6962, 60-80: 0.5418, 80+: 0.5253 |
| rec_yards   | gamma_tier     | 0-20: 0.7643, 20-40: 1.1765, 40-60: 1.6942, 60-80: 2.7933, 80+: 2.8506 |
| rec_yards   | lognorm_L_tier | 0-20: 1.7485, 20-40: 1.0101, 40-60: 0.8354, 60-80: 0.5400, 80+: 0.5979 |
| rush_yards  | normal_prop    | 1.8345                                                                 |
| rush_yards  | normal_lin     | 6.9227, 0.7449                                                         |
| rush_yards  | normal_pow     | 5.7877, 0.4959                                                         |
| rush_yards  | lognorm        | 0.8952                                                                 |
| rush_yards  | lognorm_pow    | 1.7074, -0.2170                                                        |
| rush_yards  | gamma          | 1.0179                                                                 |
| rush_yards  | gamma_pow      | 0.1742, 0.6011                                                         |
| rush_yards  | normal_L       | 9.4957, 0.4874                                                         |
| rush_yards  | lognorm_L      | 1.3718                                                                 |
| rush_yards  | lognorm_L_pow  | 2.3428, -0.2560                                                        |
| rush_yards  | normal_tier    | 0-20: 2.4857, 20-40: 0.9405, 40-60: 0.9582, 60-80: 1.9094, 80+: 2.7612 |
| rush_yards  | lognorm_tier   | 0-20: 1.0715, 20-40: 0.8776, 40-60: 0.6532, 60-80: 0.6995, 80+: 0.6851 |
| rush_yards  | gamma_tier     | 0-20: 0.6563, 20-40: 1.2358, 40-60: 1.9771, 60-80: 1.5170, 80+: 1.5132 |
| rush_yards  | lognorm_L_tier | 0-20: 1.5322, 20-40: 1.0298, 40-60: 0.6810, 60-80: 0.6387, 80+: 0.4399 |
| pass_yards  | normal_prop    | 0.6614                                                                 |
| pass_yards  | normal_lin     | 464.5455, 0.0000                                                       |
| pass_yards  | normal_pow     | 200.0000, 0.0500                                                       |
| pass_yards  | lognorm        | 0.4826                                                                 |
| pass_yards  | lognorm_pow    | 50.0000, -1.5000                                                       |
| pass_yards  | gamma          | 3.6180                                                                 |
| pass_yards  | gamma_pow      | 0.0010, 1.5000                                                         |
| pass_yards  | normal_L       | 79.6015, 0.0000                                                        |
| pass_yards  | lognorm_L      | 0.3427                                                                 |
| pass_yards  | lognorm_L_pow  | 50.0000, -1.2513                                                       |
| pass_yards  | normal_tier    | 0-175: 0.7249, 175-225: 0.7249, 225-275: 0.7249, 275+: 0.4316          |
| pass_yards  | lognorm_tier   | 0-175: 0.5081, 175-225: 0.5081, 225-275: 0.5081, 275+: 0.3690          |
| pass_yards  | gamma_tier     | 0-175: 3.2414, 175-225: 3.2414, 225-275: 3.2414, 275+: 6.6116          |
| pass_yards  | lognorm_L_tier | 0-175: 0.3838, 175-225: 0.3838, 225-275: 0.2964, 275+: 0.3243          |
| rec_catches | normal_prop    | 1.1820                                                                 |
| rec_catches | normal_tier    | 0-2: 1.9382, 2-4: 0.6699, 4-6: 0.5366, 6+: 0.4698                      |
| rec_catches | lognorm        | 0.7087                                                                 |
| rec_catches | gamma          | 1.6090                                                                 |
| rec_catches | lognorm_L      | 0.9121                                                                 |
| rec_catches | lognorm_L_tier | 0-2: 1.1165, 2-4: 0.7699, 4-6: 0.5413, 6+: 0.5293                      |
| rec_catches | poisson        |                                                                        |
| rec_catches | negbin         | 9.8788                                                                 |

## rec_yards

Mean log loss and Brier over the delta grid, and at delta 0 (x = L), by window:

| dist           |   logloss_2019-22 |   logloss_2023-25 |   logloss_d0_2019-22 |   logloss_d0_2023-25 |   brier_2019-22 |   brier_2023-25 |
|:---------------|------------------:|------------------:|---------------------:|---------------------:|----------------:|----------------:|
| emp_knn_ratio  |           0.6316  |           0.62534 |              0.68834 |              0.68893 |         0.22061 |         0.21778 |
| emp_knn_diff   |           0.63169 |           0.62547 |              0.68834 |              0.68893 |         0.22065 |         0.21783 |
| lognorm_L_pow  |           0.63509 |           0.62913 |              0.69315 |              0.69315 |         0.22155 |         0.21885 |
| lognorm_L_tier |           0.63511 |           0.62886 |              0.69315 |              0.69315 |         0.22194 |         0.21912 |
| emp_ratio      |           0.63516 |           0.62912 |              0.69016 |              0.69065 |         0.22187 |         0.219   |
| normal_L       |           0.63579 |           0.62983 |              0.69315 |              0.69315 |         0.22233 |         0.21958 |
| emp_diff       |           0.63764 |           0.63166 |              0.69016 |              0.69065 |         0.22208 |         0.21931 |
| lognorm_L      |           0.63817 |           0.63259 |              0.69315 |              0.69315 |         0.22315 |         0.22052 |
| gamma_pow      |           0.64045 |           0.63318 |              0.70235 |              0.7029  |         0.22354 |         0.22025 |
| gamma_tier     |           0.64116 |           0.63434 |              0.69813 |              0.69787 |         0.22344 |         0.22027 |
| normal_lin     |           0.64161 |           0.63467 |              0.69969 |              0.69878 |         0.22534 |         0.22215 |
| normal_pow     |           0.6426  |           0.6358  |              0.69915 |              0.69811 |         0.22572 |         0.22256 |
| normal_tier    |           0.64467 |           0.63796 |              0.6984  |              0.69708 |         0.22643 |         0.22327 |
| gamma          |           0.64664 |           0.64089 |              0.69436 |              0.69421 |         0.22515 |         0.22218 |
| normal_prop    |           0.64707 |           0.64186 |              0.69354 |              0.69323 |         0.2267  |         0.22404 |
| lognorm_tier   |           0.65575 |           0.64935 |              0.70846 |              0.70881 |         0.22694 |         0.22389 |
| lognorm_pow    |           0.65833 |           0.6514  |              0.71591 |              0.71755 |         0.22766 |         0.2244  |
| lognorm        |           0.66727 |           0.66171 |              0.70467 |              0.70432 |         0.23019 |         0.22705 |

At delta 0 (the line is the median, so a good distribution says about 0.5): the mean stated chance of the over, its mean distance from 0.5, the realised over rate:

| dist           | window   |     n |   mean_p_over |   mean_abs_from_half |   over_rate |
|:---------------|:---------|------:|--------------:|---------------------:|------------:|
| normal_prop    | 2019-22  | 16076 |        0.5682 |               0.0682 |      0.5275 |
| normal_prop    | 2023-25  | 12383 |        0.57   |               0.07   |      0.5302 |
| normal_lin     | 2019-22  | 16076 |        0.5835 |               0.0835 |      0.5275 |
| normal_lin     | 2023-25  | 12383 |        0.5839 |               0.0839 |      0.5302 |
| normal_pow     | 2019-22  | 16076 |        0.5822 |               0.0822 |      0.5275 |
| normal_pow     | 2023-25  | 12383 |        0.5824 |               0.0824 |      0.5302 |
| lognorm        | 2019-22  | 16076 |        0.4432 |               0.0568 |      0.5275 |
| lognorm        | 2023-25  | 12383 |        0.4467 |               0.0533 |      0.5302 |
| lognorm_pow    | 2019-22  | 16076 |        0.4394 |               0.0606 |      0.5275 |
| lognorm_pow    | 2023-25  | 12383 |        0.4376 |               0.0624 |      0.5302 |
| gamma          | 2019-22  | 16076 |        0.4814 |               0.0298 |      0.5275 |
| gamma          | 2023-25  | 12383 |        0.4845 |               0.028  |      0.5302 |
| gamma_pow      | 2019-22  | 16076 |        0.4814 |               0.0242 |      0.5275 |
| gamma_pow      | 2023-25  | 12383 |        0.48   |               0.026  |      0.5302 |
| normal_L       | 2019-22  | 16076 |        0.5    |               0      |      0.5275 |
| normal_L       | 2023-25  | 12383 |        0.5    |               0      |      0.5302 |
| lognorm_L      | 2019-22  | 16076 |        0.5    |               0      |      0.5275 |
| lognorm_L      | 2023-25  | 12383 |        0.5    |               0      |      0.5302 |
| lognorm_L_pow  | 2019-22  | 16076 |        0.5    |               0      |      0.5275 |
| lognorm_L_pow  | 2023-25  | 12383 |        0.5    |               0      |      0.5302 |
| normal_tier    | 2019-22  | 16076 |        0.5762 |               0.0762 |      0.5275 |
| normal_tier    | 2023-25  | 12383 |        0.5767 |               0.0767 |      0.5302 |
| lognorm_tier   | 2019-22  | 16076 |        0.4465 |               0.0537 |      0.5275 |
| lognorm_tier   | 2023-25  | 12383 |        0.4459 |               0.0542 |      0.5302 |
| gamma_tier     | 2019-22  | 16076 |        0.4839 |               0.024  |      0.5275 |
| gamma_tier     | 2023-25  | 12383 |        0.4837 |               0.0242 |      0.5302 |
| lognorm_L_tier | 2019-22  | 16076 |        0.5    |               0      |      0.5275 |
| lognorm_L_tier | 2023-25  | 12383 |        0.5    |               0      |      0.5302 |
| emp_ratio      | 2019-22  | 16076 |        0.5322 |               0.0377 |      0.5275 |
| emp_ratio      | 2023-25  | 12383 |        0.532  |               0.0339 |      0.5302 |
| emp_diff       | 2019-22  | 16076 |        0.5322 |               0.0377 |      0.5275 |
| emp_diff       | 2023-25  | 12383 |        0.532  |               0.0339 |      0.5302 |
| emp_knn_ratio  | 2019-22  | 16076 |        0.533  |               0.0378 |      0.5275 |
| emp_knn_ratio  | 2023-25  | 12383 |        0.5337 |               0.0376 |      0.5302 |
| emp_knn_diff   | 2019-22  | 16076 |        0.533  |               0.0378 |      0.5275 |
| emp_knn_diff   | 2023-25  | 12383 |        0.5337 |               0.0376 |      0.5302 |

**Verdict for rec_yards:** best by log loss on 2019-22 (emp_knn_ratio) and on 2023-25 (emp_knn_ratio), reliability within 3 points in every bin with n >= 200 on both windows (largest gap 2.5 / 1.2 points).

Reliability on 2019-22 (bins of the stated chance pooled over the deltas; gap = realised - stated, in points; flagged when |gap| > 3 with n >= 200):

emp_knn_ratio:

|   bin_lo |   bin_hi |     n |   mean_p |   over_rate |   gap | flag   |
|---------:|---------:|------:|---------:|------------:|------:|:-------|
|      0   |      0.1 |   149 |   0.0735 |      0.1477 |   7.4 |        |
|      0.1 |      0.2 |   531 |   0.161  |      0.1864 |   2.6 |        |
|      0.2 |      0.3 |  9576 |   0.2602 |      0.2551 |  -0.5 |        |
|      0.3 |      0.4 | 20594 |   0.3434 |      0.3404 |  -0.3 |        |
|      0.4 |      0.5 | 20688 |   0.4367 |      0.435  |  -0.2 |        |
|      0.5 |      0.6 | 19244 |   0.5475 |      0.5417 |  -0.6 |        |
|      0.6 |      0.7 | 15997 |   0.6462 |      0.642  |  -0.4 |        |
|      0.7 |      0.8 |  9032 |   0.7442 |      0.7347 |  -0.9 |        |
|      0.8 |      0.9 |  5064 |   0.8381 |      0.8264 |  -1.2 |        |

Reliability on 2023-25 (bins of the stated chance pooled over the deltas; gap = realised - stated, in points; flagged when |gap| > 3 with n >= 200):

emp_knn_ratio:

|   bin_lo |   bin_hi |     n |   mean_p |   over_rate |   gap | flag   |
|---------:|---------:|------:|---------:|------------:|------:|:-------|
|      0   |      0.1 |    82 |   0.0717 |      0.061  |  -1.1 |        |
|      0.1 |      0.2 |   400 |   0.158  |      0.1625 |   0.4 |        |
|      0.2 |      0.3 |  8938 |   0.2567 |      0.2448 |  -1.2 |        |
|      0.3 |      0.4 | 15368 |   0.3457 |      0.3478 |   0.2 |        |
|      0.4 |      0.5 | 15140 |   0.4386 |      0.435  |  -0.4 |        |
|      0.5 |      0.6 | 13951 |   0.5461 |      0.541  |  -0.5 |        |
|      0.6 |      0.7 | 11934 |   0.6474 |      0.6475 |   0   |        |
|      0.7 |      0.8 |  7113 |   0.7425 |      0.7434 |   0.1 |        |
|      0.8 |      0.9 |  3731 |   0.8355 |      0.8285 |  -0.7 |        |

## rush_yards

Mean log loss and Brier over the delta grid, and at delta 0 (x = L), by window:

| dist           |   logloss_2019-22 |   logloss_2023-25 |   logloss_d0_2019-22 |   logloss_d0_2023-25 |   brier_2019-22 |   brier_2023-25 |
|:---------------|------------------:|------------------:|---------------------:|---------------------:|----------------:|----------------:|
| emp_knn_diff   |           0.62252 |           0.61749 |              0.68991 |              0.68742 |         0.21675 |         0.21447 |
| normal_L       |           0.62519 |           0.6204  |              0.69315 |              0.69315 |         0.21765 |         0.21556 |
| emp_knn_ratio  |           0.62672 |           0.62007 |              0.68991 |              0.68742 |         0.21719 |         0.21496 |
| lognorm_L_pow  |           0.62705 |           0.62374 |              0.69315 |              0.69315 |         0.21809 |         0.21637 |
| emp_diff       |           0.62965 |           0.62557 |              0.69328 |              0.69187 |         0.21883 |         0.21669 |
| normal_lin     |           0.63261 |           0.62905 |              0.70067 |              0.7008  |         0.22086 |         0.21945 |
| lognorm_L_tier |           0.6335  |           0.63049 |              0.69315 |              0.69315 |         0.21874 |         0.21716 |
| emp_ratio      |           0.63549 |           0.62878 |              0.69328 |              0.69187 |         0.21899 |         0.21685 |
| lognorm_L      |           0.63815 |           0.63542 |              0.69315 |              0.69315 |         0.22004 |         0.21856 |
| normal_pow     |           0.64326 |           0.64058 |              0.70101 |              0.70144 |         0.22247 |         0.22139 |
| gamma_pow      |           0.64606 |           0.64247 |              0.72314 |              0.72626 |         0.22152 |         0.21987 |
| lognorm_pow    |           0.6573  |           0.65351 |              0.73446 |              0.73768 |         0.22472 |         0.22264 |
| gamma_tier     |           0.65877 |           0.65661 |              0.71002 |              0.7115  |         0.2221  |         0.22028 |
| normal_tier    |           0.66088 |           0.66037 |              0.69745 |              0.69762 |         0.22526 |         0.22402 |
| lognorm_tier   |           0.66263 |           0.65928 |              0.72253 |              0.72442 |         0.22439 |         0.22228 |
| normal_prop    |           0.66864 |           0.66898 |              0.69445 |              0.69416 |         0.22568 |         0.22476 |
| gamma          |           0.67007 |           0.66762 |              0.70422 |              0.70478 |         0.22408 |         0.22197 |
| lognorm        |           0.67727 |           0.67344 |              0.71673 |              0.71757 |         0.22791 |         0.22537 |

At delta 0 (the line is the median, so a good distribution says about 0.5): the mean stated chance of the over, its mean distance from 0.5, the realised over rate:

| dist           | window   |    n |   mean_p_over |   mean_abs_from_half |   over_rate |
|:---------------|:---------|-----:|--------------:|---------------------:|------------:|
| normal_prop    | 2019-22  | 7665 |        0.5348 |               0.0348 |      0.508  |
| normal_prop    | 2023-25  | 6083 |        0.5348 |               0.0348 |      0.5101 |
| normal_lin     | 2019-22  | 7665 |        0.556  |               0.056  |      0.508  |
| normal_lin     | 2023-25  | 6083 |        0.556  |               0.056  |      0.5101 |
| normal_pow     | 2019-22  | 7665 |        0.5565 |               0.0565 |      0.508  |
| normal_pow     | 2023-25  | 6083 |        0.5567 |               0.0567 |      0.5101 |
| lognorm        | 2019-22  | 7665 |        0.4002 |               0.0998 |      0.508  |
| lognorm        | 2023-25  | 6083 |        0.4002 |               0.0998 |      0.5101 |
| lognorm_pow    | 2019-22  | 7665 |        0.3995 |               0.1005 |      0.508  |
| lognorm_pow    | 2023-25  | 6083 |        0.3997 |               0.1003 |      0.5101 |
| gamma          | 2019-22  | 7665 |        0.4335 |               0.0665 |      0.508  |
| gamma          | 2023-25  | 6083 |        0.4335 |               0.0665 |      0.5101 |
| gamma_pow      | 2019-22  | 7665 |        0.4349 |               0.0697 |      0.508  |
| gamma_pow      | 2023-25  | 6083 |        0.4351 |               0.0698 |      0.5101 |
| normal_L       | 2019-22  | 7665 |        0.5    |               0      |      0.508  |
| normal_L       | 2023-25  | 6083 |        0.5    |               0      |      0.5101 |
| lognorm_L      | 2019-22  | 7665 |        0.5    |               0      |      0.508  |
| lognorm_L      | 2023-25  | 6083 |        0.5    |               0      |      0.5101 |
| lognorm_L_pow  | 2019-22  | 7665 |        0.5    |               0      |      0.508  |
| lognorm_L_pow  | 2023-25  | 6083 |        0.5    |               0      |      0.5101 |
| normal_tier    | 2019-22  | 7665 |        0.5422 |               0.0422 |      0.508  |
| normal_tier    | 2023-25  | 6083 |        0.5423 |               0.0423 |      0.5101 |
| lognorm_tier   | 2019-22  | 7665 |        0.4032 |               0.0968 |      0.508  |
| lognorm_tier   | 2023-25  | 6083 |        0.403  |               0.097  |      0.5101 |
| gamma_tier     | 2019-22  | 7665 |        0.4344 |               0.0656 |      0.508  |
| gamma_tier     | 2023-25  | 6083 |        0.4345 |               0.0655 |      0.5101 |
| lognorm_L_tier | 2019-22  | 7665 |        0.5    |               0      |      0.508  |
| lognorm_L_tier | 2023-25  | 6083 |        0.5    |               0      |      0.5101 |
| emp_ratio      | 2019-22  | 7665 |        0.501  |               0.0189 |      0.508  |
| emp_ratio      | 2023-25  | 6083 |        0.5078 |               0.0192 |      0.5101 |
| emp_diff       | 2019-22  | 7665 |        0.501  |               0.0189 |      0.508  |
| emp_diff       | 2023-25  | 6083 |        0.5078 |               0.0192 |      0.5101 |
| emp_knn_ratio  | 2019-22  | 7665 |        0.4976 |               0.0304 |      0.508  |
| emp_knn_ratio  | 2023-25  | 6083 |        0.5036 |               0.0289 |      0.5101 |
| emp_knn_diff   | 2019-22  | 7665 |        0.4976 |               0.0304 |      0.508  |
| emp_knn_diff   | 2023-25  | 6083 |        0.5036 |               0.0289 |      0.5101 |

**Verdict for rush_yards:** best by log loss on 2019-22 is emp_knn_diff, on 2023-25 emp_knn_diff; emp_knn_diff fails the reliability check (largest gap 4.0 / 0.7 points); nothing passes the reliability check on both windows, so nothing is adopted.

Reliability on 2019-22 (bins of the stated chance pooled over the deltas; gap = realised - stated, in points; flagged when |gap| > 3 with n >= 200):

emp_knn_diff:

|   bin_lo |   bin_hi |     n |   mean_p |   over_rate |   gap | flag   |
|---------:|---------:|------:|---------:|------------:|------:|:-------|
|      0   |      0.1 |   239 |   0.0941 |      0.1339 |   4   | x      |
|      0.1 |      0.2 |  3571 |   0.1537 |      0.1691 |   1.5 |        |
|      0.2 |      0.3 |  5533 |   0.2544 |      0.2624 |   0.8 |        |
|      0.3 |      0.4 | 10671 |   0.3485 |      0.363  |   1.5 |        |
|      0.4 |      0.5 |  7828 |   0.4534 |      0.4663 |   1.3 |        |
|      0.5 |      0.6 |  8481 |   0.5454 |      0.5548 |   0.9 |        |
|      0.6 |      0.7 |  6355 |   0.65   |      0.6546 |   0.5 |        |
|      0.7 |      0.8 |  2780 |   0.7416 |      0.7335 |  -0.8 |        |
|      0.8 |      0.9 |  1448 |   0.8445 |      0.8377 |  -0.7 |        |
|      0.9 |      1   |   190 |   0.9171 |      0.9263 |   0.9 |        |

Reliability on 2023-25 (bins of the stated chance pooled over the deltas; gap = realised - stated, in points; flagged when |gap| > 3 with n >= 200):

emp_knn_diff:

|   bin_lo |   bin_hi |    n |   mean_p |   over_rate |   gap | flag   |
|---------:|---------:|-----:|---------:|------------:|------:|:-------|
|      0.1 |      0.2 | 3156 |   0.1606 |      0.1594 |  -0.1 |        |
|      0.2 |      0.3 | 3862 |   0.2526 |      0.2488 |  -0.4 |        |
|      0.3 |      0.4 | 8836 |   0.3512 |      0.3516 |   0   |        |
|      0.4 |      0.5 | 6627 |   0.4596 |      0.4637 |   0.4 |        |
|      0.5 |      0.6 | 5927 |   0.5507 |      0.5537 |   0.3 |        |
|      0.6 |      0.7 | 5225 |   0.6463 |      0.6526 |   0.6 |        |
|      0.7 |      0.8 | 2753 |   0.7369 |      0.7421 |   0.5 |        |
|      0.8 |      0.9 | 1044 |   0.8495 |      0.8429 |  -0.7 |        |
|      0.9 |      1   |  119 |   0.9202 |      0.9244 |   0.4 |        |

## pass_yards

Mean log loss and Brier over the delta grid, and at delta 0 (x = L), by window:

| dist           |   logloss_2019-22 |   logloss_2023-25 |   logloss_d0_2019-22 |   logloss_d0_2023-25 |   brier_2019-22 |   brier_2023-25 |
|:---------------|------------------:|------------------:|---------------------:|---------------------:|----------------:|----------------:|
| emp_ratio      |           0.62891 |           0.63016 |              0.68375 |              0.67959 |         0.21938 |         0.22003 |
| emp_diff       |           0.62894 |           0.62993 |              0.68375 |              0.67959 |         0.21941 |         0.21995 |
| emp_knn_diff   |           0.63341 |           0.63545 |              0.68907 |              0.68431 |         0.22128 |         0.22224 |
| emp_knn_ratio  |           0.63349 |           0.63567 |              0.68907 |              0.68431 |         0.22135 |         0.22242 |
| normal_L       |           0.63826 |           0.64215 |              0.69315 |              0.69315 |         0.22338 |         0.22525 |
| lognorm_L_tier |           0.63886 |           0.64484 |              0.69315 |              0.69315 |         0.22359 |         0.22624 |
| lognorm_L      |           0.63933 |           0.64651 |              0.69315 |              0.69315 |         0.22373 |         0.22683 |
| lognorm_tier   |           0.64719 |           0.65633 |              0.69623 |              0.69992 |         0.22748 |         0.2317  |
| gamma_pow      |           0.64928 |           0.65731 |              0.69558 |              0.69953 |         0.2286  |         0.23248 |
| lognorm        |           0.64966 |           0.65669 |              0.69748 |              0.6991  |         0.2286  |         0.23177 |
| gamma_tier     |           0.65135 |           0.66097 |              0.69746 |              0.70283 |         0.22953 |         0.23408 |
| gamma          |           0.65341 |           0.66107 |              0.69763 |              0.70132 |         0.23044 |         0.23405 |
| normal_tier    |           0.66758 |           0.68109 |              0.70667 |              0.71746 |         0.23757 |         0.24409 |
| normal_prop    |           0.66891 |           0.68119 |              0.70474 |              0.71498 |         0.23815 |         0.2441  |
| normal_pow     |           0.67065 |           0.67759 |              0.69625 |              0.70169 |         0.23891 |         0.24235 |
| normal_lin     |           0.67789 |           0.68164 |              0.69341 |              0.69631 |         0.24241 |         0.24428 |
| lognorm_L_pow  |           1.43495 |           1.45884 |              0.69315 |              0.69315 |         0.29624 |         0.30195 |
| lognorm_pow    |           3.33247 |           3.59256 |              4.49094 |              4.75048 |         0.4023  |         0.42922 |

At delta 0 (the line is the median, so a good distribution says about 0.5): the mean stated chance of the over, its mean distance from 0.5, the realised over rate:

| dist           | window   |    n |   mean_p_over |   mean_abs_from_half |   over_rate |
|:---------------|:---------|-----:|--------------:|---------------------:|------------:|
| normal_prop    | 2019-22  | 2176 |        0.5808 |               0.0808 |      0.5124 |
| normal_prop    | 2023-25  | 1712 |        0.5883 |               0.0883 |      0.4842 |
| normal_lin     | 2019-22  | 2176 |        0.5307 |               0.0307 |      0.5124 |
| normal_lin     | 2023-25  | 1712 |        0.5327 |               0.0327 |      0.4842 |
| normal_pow     | 2019-22  | 2176 |        0.5537 |               0.0537 |      0.5124 |
| normal_pow     | 2023-25  | 1712 |        0.5573 |               0.0573 |      0.4842 |
| lognorm        | 2019-22  | 2176 |        0.524  |               0.0302 |      0.5124 |
| lognorm        | 2023-25  | 1712 |        0.5362 |               0.0376 |      0.4842 |
| lognorm_pow    | 2019-22  | 2176 |        1      |               0.5    |      0.5124 |
| lognorm_pow    | 2023-25  | 1712 |        1      |               0.5    |      0.4842 |
| gamma          | 2019-22  | 2176 |        0.5365 |               0.0378 |      0.5124 |
| gamma          | 2023-25  | 1712 |        0.547  |               0.0472 |      0.4842 |
| gamma_pow      | 2019-22  | 2176 |        0.5523 |               0.0524 |      0.5124 |
| gamma_pow      | 2023-25  | 1712 |        0.5595 |               0.0595 |      0.4842 |
| normal_L       | 2019-22  | 2176 |        0.5    |               0      |      0.5124 |
| normal_L       | 2023-25  | 1712 |        0.5    |               0      |      0.4842 |
| lognorm_L      | 2019-22  | 2176 |        0.5    |               0      |      0.5124 |
| lognorm_L      | 2023-25  | 1712 |        0.5    |               0      |      0.4842 |
| lognorm_L_pow  | 2019-22  | 2176 |        0.5    |               0      |      0.5124 |
| lognorm_L_pow  | 2023-25  | 1712 |        0.5    |               0      |      0.4842 |
| normal_tier    | 2019-22  | 2176 |        0.5919 |               0.0919 |      0.5124 |
| normal_tier    | 2023-25  | 1712 |        0.5964 |               0.0964 |      0.4842 |
| lognorm_tier   | 2019-22  | 2176 |        0.5405 |               0.0413 |      0.5124 |
| lognorm_tier   | 2023-25  | 1712 |        0.5476 |               0.048  |      0.4842 |
| gamma_tier     | 2019-22  | 2176 |        0.5523 |               0.0525 |      0.5124 |
| gamma_tier     | 2023-25  | 1712 |        0.5582 |               0.0582 |      0.4842 |
| lognorm_L_tier | 2019-22  | 2176 |        0.5    |               0      |      0.5124 |
| lognorm_L_tier | 2023-25  | 1712 |        0.5    |               0      |      0.4842 |
| emp_ratio      | 2019-22  | 2176 |        0.514  |               0.0369 |      0.5124 |
| emp_ratio      | 2023-25  | 1712 |        0.4972 |               0.0413 |      0.4842 |
| emp_diff       | 2019-22  | 2176 |        0.514  |               0.0369 |      0.5124 |
| emp_diff       | 2023-25  | 1712 |        0.4972 |               0.0413 |      0.4842 |
| emp_knn_ratio  | 2019-22  | 2176 |        0.5202 |               0.036  |      0.5124 |
| emp_knn_ratio  | 2023-25  | 1712 |        0.5009 |               0.0455 |      0.4842 |
| emp_knn_diff   | 2019-22  | 2176 |        0.5202 |               0.036  |      0.5124 |
| emp_knn_diff   | 2023-25  | 1712 |        0.5009 |               0.0455 |      0.4842 |

**Verdict for pass_yards:** best by log loss on 2019-22 is emp_ratio, on 2023-25 emp_diff; emp_ratio fails the reliability check (largest gap 2.8 / 3.1 points); the best that passes the reliability check on both windows is emp_knn_diff (largest gap 2.7 / 2.7 points), adopted under the rule's second clause.

Reliability on 2019-22 (bins of the stated chance pooled over the deltas; gap = realised - stated, in points; flagged when |gap| > 3 with n >= 200):

emp_knn_diff:

|   bin_lo |   bin_hi |    n |   mean_p |   over_rate |   gap | flag   |
|---------:|---------:|-----:|---------:|------------:|------:|:-------|
|      0.1 |      0.2 |  115 |   0.169  |      0.1391 |  -3   |        |
|      0.2 |      0.3 |  976 |   0.2665 |      0.2398 |  -2.7 |        |
|      0.3 |      0.4 | 3204 |   0.3508 |      0.3246 |  -2.6 |        |
|      0.4 |      0.5 | 2662 |   0.4476 |      0.4249 |  -2.3 |        |
|      0.5 |      0.6 | 2376 |   0.5409 |      0.5354 |  -0.5 |        |
|      0.6 |      0.7 | 2994 |   0.6472 |      0.6409 |  -0.6 |        |
|      0.7 |      0.8 | 2870 |   0.7434 |      0.7446 |   0.1 |        |
|      0.8 |      0.9 |   35 |   0.8031 |      0.7714 |  -3.2 |        |

emp_ratio:

|   bin_lo |   bin_hi |    n |   mean_p |   over_rate |   gap | flag   |
|---------:|---------:|-----:|---------:|------------:|------:|:-------|
|      0   |      0.1 |   76 |   0.0796 |      0.0526 |  -2.7 |        |
|      0.1 |      0.2 |  175 |   0.1444 |      0.0914 |  -5.3 |        |
|      0.2 |      0.3 | 1089 |   0.2763 |      0.2489 |  -2.8 |        |
|      0.3 |      0.4 | 3151 |   0.3515 |      0.3307 |  -2.1 |        |
|      0.4 |      0.5 | 2591 |   0.4509 |      0.4423 |  -0.9 |        |
|      0.5 |      0.6 | 2614 |   0.5478 |      0.5436 |  -0.4 |        |
|      0.6 |      0.7 | 2413 |   0.6497 |      0.6432 |  -0.6 |        |
|      0.7 |      0.8 | 3123 |   0.7413 |      0.7442 |   0.3 |        |

Reliability on 2023-25 (bins of the stated chance pooled over the deltas; gap = realised - stated, in points; flagged when |gap| > 3 with n >= 200):

emp_knn_diff:

|   bin_lo |   bin_hi |    n |   mean_p |   over_rate |   gap | flag   |
|---------:|---------:|-----:|---------:|------------:|------:|:-------|
|      0.1 |      0.2 |  311 |   0.1583 |      0.1608 |   0.2 |        |
|      0.2 |      0.3 | 1364 |   0.2669 |      0.2603 |  -0.7 |        |
|      0.3 |      0.4 | 2180 |   0.3497 |      0.3234 |  -2.6 |        |
|      0.4 |      0.5 | 1864 |   0.4419 |      0.4233 |  -1.9 |        |
|      0.5 |      0.6 | 2107 |   0.5436 |      0.5164 |  -2.7 |        |
|      0.6 |      0.7 | 2064 |   0.6466 |      0.625  |  -2.2 |        |
|      0.7 |      0.8 | 2058 |   0.7455 |      0.7187 |  -2.7 |        |
|      0.8 |      0.9 |   36 |   0.8069 |      0.75   |  -5.7 |        |

emp_ratio:

|   bin_lo |   bin_hi |    n |   mean_p |   over_rate |   gap | flag   |
|---------:|---------:|-----:|---------:|------------:|------:|:-------|
|      0   |      0.1 |  224 |   0.068  |      0.0759 |   0.8 |        |
|      0.1 |      0.2 |  220 |   0.1618 |      0.1409 |  -2.1 |        |
|      0.2 |      0.3 | 1255 |   0.2662 |      0.2598 |  -0.6 |        |
|      0.3 |      0.4 | 2181 |   0.3462 |      0.321  |  -2.5 |        |
|      0.4 |      0.5 | 2356 |   0.4525 |      0.4461 |  -0.6 |        |
|      0.5 |      0.6 | 1600 |   0.5577 |      0.5387 |  -1.9 |        |
|      0.6 |      0.7 | 1909 |   0.649  |      0.6176 |  -3.1 | x      |
|      0.7 |      0.8 | 2239 |   0.7457 |      0.7222 |  -2.4 |        |

## rec_catches

Mean log loss and Brier over the delta grid, and at delta 0 (x = L), by window:

| dist           |   logloss_2019-22 |   logloss_2023-25 |   logloss_d0_2019-22 |   logloss_d0_2023-25 |   brier_2019-22 |   brier_2023-25 |
|:---------------|------------------:|------------------:|---------------------:|---------------------:|----------------:|----------------:|
| emp_knn_ratio  |           0.54335 |           0.52833 |              0.65991 |              0.65465 |         0.18196 |         0.17575 |
| emp_knn_diff   |           0.54362 |           0.52876 |              0.65991 |              0.65465 |         0.18199 |         0.17586 |
| emp_diff       |           0.55006 |           0.53733 |              0.67889 |              0.67721 |         0.18448 |         0.17906 |
| negbin         |           0.55194 |           0.53855 |              0.6815  |              0.68128 |         0.18466 |         0.1791  |
| emp_ratio      |           0.55297 |           0.5403  |              0.67889 |              0.67721 |         0.18542 |         0.17997 |
| poisson        |           0.55599 |           0.54061 |              0.67997 |              0.6791  |         0.18563 |         0.17949 |
| lognorm_L_tier |           0.55743 |           0.54508 |              0.69315 |              0.69315 |         0.18733 |         0.18211 |
| lognorm_L      |           0.56022 |           0.54943 |              0.69315 |              0.69315 |         0.18849 |         0.1838  |
| normal_tier    |           0.56292 |           0.55171 |              0.69267 |              0.69119 |         0.18935 |         0.18441 |
| gamma          |           0.58239 |           0.57307 |              0.71169 |              0.71352 |         0.19356 |         0.18925 |
| lognorm        |           0.58297 |           0.57231 |              0.7257  |              0.72847 |         0.19453 |         0.1899  |
| normal_prop    |           0.58862 |           0.58064 |              0.68758 |              0.68645 |         0.19659 |         0.19258 |

At delta 0 (the line is the median, so a good distribution says about 0.5): the mean stated chance of the over, its mean distance from 0.5, the realised over rate:

| dist           | window   |     n |   mean_p_over |   mean_abs_from_half |   over_rate |
|:---------------|:---------|------:|--------------:|---------------------:|------------:|
| normal_prop    | 2019-22  | 15498 |        0.5337 |               0.0337 |      0.5581 |
| normal_prop    | 2023-25  | 11829 |        0.5337 |               0.0337 |      0.5665 |
| normal_tier    | 2019-22  | 15498 |        0.5482 |               0.0482 |      0.5581 |
| normal_tier    | 2023-25  | 11829 |        0.5469 |               0.0469 |      0.5665 |
| lognorm        | 2019-22  | 15498 |        0.4185 |               0.0815 |      0.5581 |
| lognorm        | 2023-25  | 11829 |        0.4185 |               0.0815 |      0.5665 |
| gamma          | 2019-22  | 15498 |        0.4458 |               0.0542 |      0.5581 |
| gamma          | 2023-25  | 11829 |        0.4458 |               0.0542 |      0.5665 |
| lognorm_L      | 2019-22  | 15498 |        0.5    |               0      |      0.5581 |
| lognorm_L      | 2023-25  | 11829 |        0.5    |               0      |      0.5665 |
| lognorm_L_tier | 2019-22  | 15498 |        0.5    |               0      |      0.5581 |
| lognorm_L_tier | 2023-25  | 11829 |        0.5    |               0      |      0.5665 |
| poisson        | 2019-22  | 15498 |        0.5227 |               0.0737 |      0.5581 |
| poisson        | 2023-25  | 11829 |        0.5231 |               0.0739 |      0.5665 |
| negbin         | 2019-22  | 15498 |        0.5003 |               0.0628 |      0.5581 |
| negbin         | 2023-25  | 11829 |        0.501  |               0.0631 |      0.5665 |
| emp_ratio      | 2019-22  | 15498 |        0.5634 |               0.0683 |      0.5581 |
| emp_ratio      | 2023-25  | 11829 |        0.5677 |               0.0716 |      0.5665 |
| emp_diff       | 2019-22  | 15498 |        0.5634 |               0.0683 |      0.5581 |
| emp_diff       | 2023-25  | 11829 |        0.5677 |               0.0716 |      0.5665 |
| emp_knn_ratio  | 2019-22  | 15498 |        0.5596 |               0.0686 |      0.5581 |
| emp_knn_ratio  | 2023-25  | 11829 |        0.5654 |               0.0819 |      0.5665 |
| emp_knn_diff   | 2019-22  | 15498 |        0.5596 |               0.0686 |      0.5581 |
| emp_knn_diff   | 2023-25  | 11829 |        0.5654 |               0.0819 |      0.5665 |

**Verdict for rec_catches:** best by log loss on 2019-22 (emp_knn_ratio) and on 2023-25 (emp_knn_ratio), reliability within 3 points in every bin with n >= 200 on both windows (largest gap 1.2 / 1.8 points).

Reliability on 2019-22 (bins of the stated chance pooled over the deltas; gap = realised - stated, in points; flagged when |gap| > 3 with n >= 200):

emp_knn_ratio:

|   bin_lo |   bin_hi |     n |   mean_p |   over_rate |   gap | flag   |
|---------:|---------:|------:|---------:|------------:|------:|:-------|
|      0   |      0.1 |   474 |   0.0614 |      0.0654 |   0.4 |        |
|      0.1 |      0.2 |  9720 |   0.1561 |      0.1543 |  -0.2 |        |
|      0.2 |      0.3 |  9455 |   0.2463 |      0.2359 |  -1   |        |
|      0.3 |      0.4 | 12395 |   0.3394 |      0.3431 |   0.4 |        |
|      0.4 |      0.5 |  3921 |   0.4797 |      0.4741 |  -0.6 |        |
|      0.5 |      0.6 |  8691 |   0.5341 |      0.5223 |  -1.2 |        |
|      0.6 |      0.7 |  6083 |   0.6631 |      0.6587 |  -0.4 |        |
|      0.7 |      0.8 |  5745 |   0.7549 |      0.756  |   0.1 |        |
|      0.8 |      0.9 |  6319 |   0.8431 |      0.8421 |  -0.1 |        |
|      0.9 |      1   |  2434 |   0.9319 |      0.9285 |  -0.3 |        |

Reliability on 2023-25 (bins of the stated chance pooled over the deltas; gap = realised - stated, in points; flagged when |gap| > 3 with n >= 200):

emp_knn_ratio:

|   bin_lo |   bin_hi |    n |   mean_p |   over_rate |   gap | flag   |
|---------:|---------:|-----:|---------:|------------:|------:|:-------|
|      0   |      0.1 |  330 |   0.0635 |      0.0697 |   0.6 |        |
|      0.1 |      0.2 | 8302 |   0.1533 |      0.1442 |  -0.9 |        |
|      0.2 |      0.3 | 7350 |   0.2508 |      0.2331 |  -1.8 |        |
|      0.3 |      0.4 | 8684 |   0.3469 |      0.3442 |  -0.3 |        |
|      0.4 |      0.5 | 3829 |   0.472  |      0.4685 |  -0.4 |        |
|      0.5 |      0.6 | 5504 |   0.5415 |      0.5394 |  -0.2 |        |
|      0.6 |      0.7 | 4305 |   0.6547 |      0.6581 |   0.3 |        |
|      0.7 |      0.8 | 4374 |   0.7567 |      0.7686 |   1.2 |        |
|      0.8 |      0.9 | 5186 |   0.847  |      0.8533 |   0.6 |        |
|      0.9 |      1   | 1608 |   0.9367 |      0.9397 |   0.3 |        |

## How to compute P(over x) in the live rule

The card carries L = proj_<kind>_yards (the line) and M = proj_<kind>_yards_mean (the mean, scaled the same way). For a book number x:

- rec_yards: emp_knn_ratio: keep a reference table of (L, actual) for every row of the by-season frame from 2017 to the last completed season (rebuilt each run, as the game model keeps its training misses in model.price_at). For a line L, take the K rows nearest to it in L (K = 10% of the table, at least 300, at most 1500: sort the table by L, find L's position, take K/2 rows on each side, shifted in from the ends), and P(over x) = the share of those rows with actual / L > x / L.
- rush_yards: nothing adopted.
- pass_yards: emp_knn_diff: keep a reference table of (L, actual) for every row of the by-season frame from 2017 to the last completed season (rebuilt each run, as the game model keeps its training misses in model.price_at). For a line L, take the K rows nearest to it in L (K = 10% of the table, at least 300, at most 1500: sort the table by L, find L's position, take K/2 rows on each side, shifted in from the ends), and P(over x) = the share of those rows with actual - L > x - L.
- rec_catches: emp_knn_ratio: keep a reference table of (L, actual) for every row of the by-season frame from 2017 to the last completed season (rebuilt each run, as the game model keeps its training misses in model.price_at). For a line L, take the K rows nearest to it in L (K = 10% of the table, at least 300, at most 1500: sort the table by L, find L's position, take K/2 rows on each side, shifted in from the ends), and P(over x) = the share of those rows with actual / L > x / L.

## Reading of the results (29 Sep 2026, written after the run; the tables above are the evidence)

- The mean M is not the mean of what happened for passing: on 2017-25 M averages 266 yards against 233 actual (the linear median factor MED_TIER['pass'], 0.63 + 0.00091 x M, absorbs a bias there, since passing yards are nearly symmetric and a true median factor would sit near 0.95). Every M-centred form (normal, log-normal, gamma with mean M) is therefore off for passing, and the M-centred forms say 0.43 to 0.60 at x = L for every stat; only the L-centred forms (0.5 by construction) and the empirical ones (the fit window's own over rate, 0.50 to 0.53) sit where a median line should. Receiving and rushing M do match the actual mean (31.8 / 31.7 and 31.1 / 30.9).
- The first pass (tiers of L, and every parametric form) failed the reliability check in the tail bins, and the failures were all rows with a small line and a large positive delta (L of 2 to 6, x of 12 to 21: numbers no book hangs). Within the 0-20 tier the shape of actual / L changes fast with L (the median of actual / L is 2.1 below L = 5, 1.1 at 10 to 20: the median factor undershoots at tiny means), so the fixed tier pools rows that do not belong together. The nearest-neighbour empirical (emp_knn, K earlier rows nearest in L) fixes that and is the best by log loss on both windows for receiving yards and receptions, and passes the reliability check on both.
- Rushing: emp_knn_diff is the best by log loss on both windows and within 1.5 points in every bin but one: the 0-0.1 bin on 2019-22 (239 rows, stated 9.4%, realised 13.4%, a 4.0-point gap; on 2023-25 every bin is within 0.7). Under the rule as set it is not adopted; the miss is one thin tail bin, and adopting it anyway is a call for the reader, not this study.
- Passing: the fixed-tier empirical (emp_ratio / emp_diff, the same family) is the best by log loss on both windows but emp_ratio misses the reliability bar by a tenth of a point in one bin on 2023-25 (3.1); emp_knn_diff is the best that passes on both windows and is adopted under the rule's second clause. Its gaps on 2023-25 run 2 to 3 points negative across the bins: the passing line ran high in 2023-25 (over rate 0.484 at x = L), which no distribution around the line can know.
- Receptions: emp_knn_ratio beats the count models (negbin, poisson) on both windows and is within 2 points in every bin. The Poisson and negative binomial around the receptions mean M (the line / MED_CATCH) say 0.50 to 0.52 at x = L while 0.56 to 0.57 of the games went over: the receptions line sits low.
- On integration: emp_knn needs a reference table per stat, (L, actual) for every row of the by-season frame from 2017 to the last completed season (the cached frames this script writes carry it: season, L, act_yds / act_catch), rebuilt when props_by_season is rerun; at 36k receiving rows K is the cap of 1500. The frame grades only games with a touch, so the chance is conditional on the player getting on the stat sheet.

Pushes: a book number the actual can land on (a whole number) is a push; the scoring here left ties out. In the grading, the side is the one with the higher chance (over when P(over x) > 0.5, which is the same side as edge = L - x > 0 for a median-consistent distribution), and the chance is the number to rank props by, as the page ranks game bets.
