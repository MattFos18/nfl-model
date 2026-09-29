# A league scoring-environment input (29 Sep 2026)

`experiments/scoring_env.py`, `reports/scoring_env.csv`. The points regression's intercept is the training mean of points
since 2013, so it learns the league's scoring level slowly and lags a within-season drift. Candidates built from our own
results only (no line anywhere): last season's league mean points per team-game (`pts_prev`); this season's mean over the
weeks before this one, shrunk toward `pts_prev` with K team-games of weight so week 1 equals `pts_prev` (`pts_ytd_kK`);
the mean over the last four played weeks, across the season boundary, shrunk the same way (`pts_rec_kK`); and the same
three for league offensive EPA per play (`epa_*`). K in 64, 128, 256. Each candidate added, one at a time, to the points
equation (`M.FEATS`; the blend's ridges and trees carry it too) and separately to the total equation (`M.TOTAL_FEATS`),
then the best pair of each and the two equations' best singles together. Walk-forward, weekly refit, as-of only.

**Adoption rule (stated before the results):** adopted only if the margin miss (points equation) or the total miss (total
equation) improves on all three windows, 2015-18 (never used for a choice), 2019-22 and 2023-25, with the team points miss
not worse on any. A one- or two-window gain is not adopted.

Columns: team, margin and total miss (MAE); total bias, the mean of model total minus actual; 4+ and 5+ the spread record at
that edge; eq miss / eq bias, the points equation's own team points (before the total is shared out by the spread), where a
league-level input shows: it is the same number for both teams of a game, so it cancels in the margin and cannot move the
graded team points, which are the total equation's number shared out by the spread.

| variant | eq | 2015-18 team / margin / total / total bias / 4+ / eq miss / eq bias | 2019-22 team / margin / total / total bias / 4+ / eq miss / eq bias | 2023-25 team / margin / total / total bias / 4+ / eq miss / eq bias | secs | verdict |
|---|---|---|---|---|---|---|
| base | base | 7.4094 / 9.9491 / 10.7437 / +0.35 / 68-55 / 7.3817 / +0.06 | 7.3477 / 10.0204 / 10.5406 / -0.26 / 83-54 / 7.3407 / -0.12 | 7.2623 / 9.9041 / 10.1767 / +0.04 / 44-26 / 7.2672 / +0.20 | 123 | base |
| pts:pts_prev | points | 7.4084 / 9.9469 / 10.7437 / +0.35 / 65-58 / 7.3902 / +0.43 | 7.3475 / 10.0222 / 10.5406 / -0.26 / 81-56 / 7.3428 / -0.35 | 7.2626 / 9.9046 / 10.1767 / +0.04 / 44-26 / 7.2693 / +0.21 | 152 | not adopted: margin better on 1 of 3 (2015-18) |
| pts:pts_ytd_k64 | points | 7.4093 / 9.9485 / 10.7437 / +0.35 / 66-60 / 7.3886 / +0.22 | 7.3461 / 10.0136 / 10.5406 / -0.26 / 83-52 / 7.3265 / -0.06 | 7.2630 / 9.9057 / 10.1767 / +0.04 / 43-28 / 7.2527 / -0.01 | 329 | not adopted: margin better on 2 of 3 (2015-18, 2019-22) |
| pts:pts_ytd_k128 | points | 7.4108 / 9.9532 / 10.7437 / +0.35 / 66-57 / 7.3915 / +0.25 | 7.3467 / 10.0167 / 10.5406 / -0.26 / 83-54 / 7.3345 / -0.05 | 7.2640 / 9.9075 / 10.1767 / +0.04 / 43-28 / 7.2521 / -0.01 | 252 | not adopted: margin better on 1 of 3 (2019-22) |
| pts:pts_ytd_k256 | points | 7.4092 / 9.9489 / 10.7437 / +0.35 / 68-58 / 7.3927 / +0.31 | 7.3462 / 10.0138 / 10.5406 / -0.26 / 84-52 / 7.3414 / -0.11 | 7.2632 / 9.9040 / 10.1767 / +0.04 / 44-26 / 7.2543 / +0.02 | 266 | not adopted: target better on all three but team points worse on 2023-25 |
| pts:pts_rec_k64 | points | 7.4081 / 9.9460 / 10.7437 / +0.35 / 66-56 / 7.3841 / +0.07 | 7.3448 / 10.0082 / 10.5406 / -0.26 / 79-54 / 7.3295 / -0.05 | 7.2623 / 9.9022 / 10.1767 / +0.04 / 44-28 / 7.2618 / +0.04 | 268 | ADOPTABLE: better on all three, team points not worse |
| pts:pts_rec_k128 | points | 7.4085 / 9.9476 / 10.7437 / +0.35 / 68-56 / 7.3842 / +0.11 | 7.3452 / 10.0092 / 10.5406 / -0.26 / 85-54 / 7.3336 / -0.02 | 7.2637 / 9.9075 / 10.1767 / +0.04 / 43-26 / 7.2590 / +0.02 | 232 | not adopted: margin better on 2 of 3 (2015-18, 2019-22) |
| pts:pts_rec_k256 | points | 7.4089 / 9.9458 / 10.7437 / +0.35 / 66-57 / 7.3853 / +0.24 | 7.3454 / 10.0150 / 10.5406 / -0.26 / 83-54 / 7.3410 / -0.11 | 7.2639 / 9.9088 / 10.1767 / +0.04 / 43-27 / 7.2600 / +0.07 | 225 | not adopted: margin better on 2 of 3 (2015-18, 2019-22) |
| pts:epa_prev | points | 7.4096 / 9.9522 / 10.7437 / +0.35 / 71-55 / 7.3869 / +0.01 | 7.3448 / 10.0127 / 10.5406 / -0.26 / 84-53 / 7.3371 / -0.29 | 7.2628 / 9.9068 / 10.1767 / +0.04 / 44-26 / 7.2702 / +0.22 | 153 | not adopted: margin better on 1 of 3 (2019-22) |
| pts:epa_ytd_k64 | points | 7.4076 / 9.9435 / 10.7437 / +0.35 / 70-55 / 7.3835 / +0.08 | 7.3459 / 10.0165 / 10.5406 / -0.26 / 81-52 / 7.3405 / -0.02 | 7.2609 / 9.9031 / 10.1767 / +0.04 / 44-26 / 7.2514 / +0.08 | 330 | ADOPTABLE: better on all three, team points not worse |
| pts:epa_ytd_k128 | points | 7.4099 / 9.9457 / 10.7437 / +0.35 / 66-52 / 7.3866 / +0.07 | 7.3463 / 10.0146 / 10.5406 / -0.26 / 78-52 / 7.3434 / -0.06 | 7.2627 / 9.9067 / 10.1767 / +0.04 / 44-27 / 7.2569 / +0.11 | 254 | not adopted: margin better on 2 of 3 (2015-18, 2019-22) |
| pts:epa_ytd_k256 | points | 7.4100 / 9.9491 / 10.7437 / +0.35 / 69-55 / 7.3830 / +0.03 | 7.3446 / 10.0134 / 10.5406 / -0.26 / 81-53 / 7.3442 / -0.14 | 7.2620 / 9.9061 / 10.1767 / +0.04 / 43-27 / 7.2582 / +0.15 | 273 | not adopted: margin better on 1 of 3 (2019-22) |
| pts:epa_rec_k64 | points | 7.4098 / 9.9495 / 10.7437 / +0.35 / 66-55 / 7.3862 / +0.07 | 7.3454 / 10.0143 / 10.5406 / -0.26 / 79-51 / 7.3397 / -0.04 | 7.2639 / 9.9089 / 10.1767 / +0.04 / 44-27 / 7.2648 / +0.15 | 270 | not adopted: margin better on 1 of 3 (2019-22) |
| pts:epa_rec_k128 | points | 7.4082 / 9.9475 / 10.7437 / +0.35 / 67-58 / 7.3839 / +0.03 | 7.3461 / 10.0146 / 10.5406 / -0.26 / 79-53 / 7.3425 / -0.06 | 7.2622 / 9.9055 / 10.1767 / +0.04 / 45-26 / 7.2649 / +0.16 | 234 | not adopted: margin better on 2 of 3 (2015-18, 2019-22) |
| pts:epa_rec_k256 | points | 7.4087 / 9.9467 / 10.7437 / +0.35 / 69-56 / 7.3845 / +0.03 | 7.3459 / 10.0150 / 10.5406 / -0.26 / 81-54 / 7.3433 / -0.15 | 7.2622 / 9.9049 / 10.1767 / +0.04 / 43-27 / 7.2641 / +0.17 | 226 | not adopted: margin better on 2 of 3 (2015-18, 2019-22) |
| tot:pts_prev | total | 7.4194 / 9.9491 / 10.7721 / +1.07 / 68-55 / 7.3817 / +0.06 | 7.3477 / 10.0204 / 10.5436 / -0.43 / 83-54 / 7.3407 / -0.12 | 7.2652 / 9.9041 / 10.1875 / +0.10 / 44-26 / 7.2672 / +0.20 | 114 | not adopted: total better on 0 of 3 |
| tot:pts_ytd_k64 | total | 7.4218 / 9.9491 / 10.7671 / +0.80 / 68-55 / 7.3817 / +0.06 | 7.3427 / 10.0204 / 10.5357 / -0.17 / 83-54 / 7.3407 / -0.12 | 7.2559 / 9.9041 / 10.1661 / -0.19 / 44-26 / 7.2672 / +0.20 | 147 | not adopted: total better on 2 of 3 (2019-22, 2023-25) |
| tot:pts_ytd_k128 | total | 7.4205 / 9.9491 / 10.7645 / +0.91 / 68-55 / 7.3817 / +0.06 | 7.3471 / 10.0204 / 10.5455 / -0.18 / 83-54 / 7.3407 / -0.12 | 7.2557 / 9.9041 / 10.1653 / -0.18 / 44-26 / 7.2672 / +0.20 | 155 | not adopted: total better on 1 of 3 (2023-25) |
| tot:pts_ytd_k256 | total | 7.4191 / 9.9491 / 10.7636 / +1.01 / 68-55 / 7.3817 / +0.06 | 7.3512 / 10.0204 / 10.5541 / -0.26 / 83-54 / 7.3407 / -0.12 | 7.2575 / 9.9041 / 10.1690 / -0.12 / 44-26 / 7.2672 / +0.20 | 164 | not adopted: total better on 1 of 3 (2023-25) |
| tot:pts_rec_k64 | total | 7.4133 / 9.9491 / 10.7529 / +0.42 / 68-55 / 7.3817 / +0.06 | 7.3372 / 10.0204 / 10.5258 / -0.07 / 83-54 / 7.3407 / -0.12 | 7.2595 / 9.9041 / 10.1738 / -0.18 / 44-26 / 7.2672 / +0.20 | 144 | not adopted: total better on 2 of 3 (2019-22, 2023-25) |
| tot:pts_rec_k128 | total | 7.4153 / 9.9491 / 10.7576 / +0.53 / 68-55 / 7.3817 / +0.06 | 7.3421 / 10.0204 / 10.5408 / +0.03 / 83-54 / 7.3407 / -0.12 | 7.2573 / 9.9041 / 10.1681 / -0.20 / 44-26 / 7.2672 / +0.20 | 123 | not adopted: total better on 1 of 3 (2023-25) |
| tot:pts_rec_k256 | total | 7.4196 / 9.9491 / 10.7680 / +0.81 / 68-55 / 7.3817 / +0.06 | 7.3465 / 10.0204 / 10.5523 / -0.03 / 83-54 / 7.3407 / -0.12 | 7.2583 / 9.9041 / 10.1700 / -0.13 / 44-26 / 7.2672 / +0.20 | 130 | not adopted: total better on 1 of 3 (2023-25) |
| tot:epa_prev | total | 7.4192 / 9.9491 / 10.7750 / +0.52 / 68-55 / 7.3817 / +0.06 | 7.3469 / 10.0204 / 10.5442 / -0.35 / 83-54 / 7.3407 / -0.12 | 7.2645 / 9.9041 / 10.1778 / +0.06 / 44-26 / 7.2672 / +0.20 | 134 | not adopted: total better on 0 of 3 |
| tot:epa_ytd_k64 | total | 7.4133 / 9.9491 / 10.7509 / +0.39 / 68-55 / 7.3817 / +0.06 | 7.3513 / 10.0204 / 10.5568 / -0.16 / 83-54 / 7.3407 / -0.12 | 7.2592 / 9.9041 / 10.1744 / -0.00 / 44-26 / 7.2672 / +0.20 | 153 | not adopted: total better on 1 of 3 (2023-25) |
| tot:epa_ytd_k128 | total | 7.4115 / 9.9491 / 10.7505 / +0.38 / 68-55 / 7.3817 / +0.06 | 7.3526 / 10.0204 / 10.5596 / -0.23 / 83-54 / 7.3407 / -0.12 | 7.2603 / 9.9041 / 10.1770 / +0.02 / 44-26 / 7.2672 / +0.20 | 129 | not adopted: total better on 0 of 3 |
| tot:epa_ytd_k256 | total | 7.4113 / 9.9491 / 10.7547 / +0.34 / 68-55 / 7.3817 / +0.06 | 7.3529 / 10.0204 / 10.5615 / -0.34 / 83-54 / 7.3407 / -0.12 | 7.2626 / 9.9041 / 10.1808 / +0.04 / 44-26 / 7.2672 / +0.20 | 118 | not adopted: total better on 0 of 3 |
| tot:epa_rec_k64 | total | 7.4109 / 9.9491 / 10.7487 / +0.32 / 68-55 / 7.3817 / +0.06 | 7.3478 / 10.0204 / 10.5509 / -0.04 / 83-54 / 7.3407 / -0.12 | 7.2606 / 9.9041 / 10.1757 / +0.01 / 44-26 / 7.2672 / +0.20 | 117 | not adopted: total better on 1 of 3 (2023-25) |
| tot:epa_rec_k128 | total | 7.4110 / 9.9491 / 10.7510 / +0.27 / 68-55 / 7.3817 / +0.06 | 7.3495 / 10.0204 / 10.5567 / -0.02 / 83-54 / 7.3407 / -0.12 | 7.2603 / 9.9041 / 10.1764 / +0.00 / 44-26 / 7.2672 / +0.20 | 118 | not adopted: total better on 1 of 3 (2023-25) |
| tot:epa_rec_k256 | total | 7.4127 / 9.9491 / 10.7553 / +0.29 / 68-55 / 7.3817 / +0.06 | 7.3495 / 10.0204 / 10.5564 / -0.11 / 83-54 / 7.3407 / -0.12 | 7.2616 / 9.9041 / 10.1779 / +0.01 / 44-26 / 7.2672 / +0.20 | 113 | not adopted: total better on 0 of 3 |
| pair pts:pts_rec_k64+epa_ytd_k64 | points | 7.4069 / 9.9435 / 10.7437 / +0.35 / 67-60 / 7.3866 / +0.04 | 7.3448 / 10.0086 / 10.5406 / -0.26 / 82-53 / 7.3308 / -0.05 | 7.2621 / 9.9040 / 10.1767 / +0.04 / 44-27 / 7.2592 / +0.05 | 238 | ADOPTABLE: better on all three, team points not worse |
| pair tot:pts_rec_k64+pts_ytd_k64 | total | 7.4260 / 9.9493 / 10.7758 / +0.69 / 69-55 / 7.3818 / +0.06 | 7.3419 / 10.0202 / 10.5286 / -0.12 / 83-54 / 7.3399 / -0.12 | 7.2588 / 9.9050 / 10.1732 / -0.20 / 44-26 / 7.2675 / +0.20 | 232 | not adopted: total better on 2 of 3 (2019-22, 2023-25) |
| both pts:pts_rec_k64 tot:pts_rec_k64 | both | 7.4119 / 9.9460 / 10.7529 / +0.42 / 66-56 / 7.3841 / +0.07 | 7.3341 / 10.0082 / 10.5258 / -0.07 / 79-54 / 7.3295 / -0.05 | 7.2598 / 9.9022 / 10.1738 / -0.18 / 44-28 / 7.2618 / +0.04 | 240 | not adopted: total not better on all three; team points worse on 2015-18 |

## Change against the base (miss deltas; negative is better)

| variant | d team 2015-18 | d margin 2015-18 | d total 2015-18 | d team 2019-22 | d margin 2019-22 | d total 2019-22 | d team 2023-25 | d margin 2023-25 | d total 2023-25 | d eq miss (3 windows) |
|---|---|---|---|---|---|---|---|---|---|---|
| pts:pts_prev | -0.0010 | -0.0022 | +0.0000 | -0.0002 | +0.0018 | +0.0000 | +0.0003 | +0.0005 | +0.0000 | +0.0085 / +0.0021 / +0.0021 |
| pts:pts_ytd_k64 | -0.0001 | -0.0006 | +0.0000 | -0.0016 | -0.0068 | +0.0000 | +0.0007 | +0.0016 | +0.0000 | +0.0069 / -0.0142 / -0.0145 |
| pts:pts_ytd_k128 | +0.0014 | +0.0041 | +0.0000 | -0.0010 | -0.0037 | +0.0000 | +0.0017 | +0.0034 | +0.0000 | +0.0098 / -0.0062 / -0.0151 |
| pts:pts_ytd_k256 | -0.0002 | -0.0002 | +0.0000 | -0.0015 | -0.0066 | +0.0000 | +0.0009 | -0.0001 | +0.0000 | +0.0110 / +0.0007 / -0.0129 |
| pts:pts_rec_k64 | -0.0013 | -0.0031 | +0.0000 | -0.0029 | -0.0122 | +0.0000 | +0.0000 | -0.0019 | +0.0000 | +0.0024 / -0.0112 / -0.0054 |
| pts:pts_rec_k128 | -0.0009 | -0.0015 | +0.0000 | -0.0025 | -0.0112 | +0.0000 | +0.0014 | +0.0034 | +0.0000 | +0.0025 / -0.0071 / -0.0082 |
| pts:pts_rec_k256 | -0.0005 | -0.0033 | +0.0000 | -0.0023 | -0.0054 | +0.0000 | +0.0016 | +0.0047 | +0.0000 | +0.0036 / +0.0003 / -0.0072 |
| pts:epa_prev | +0.0002 | +0.0031 | +0.0000 | -0.0029 | -0.0077 | +0.0000 | +0.0005 | +0.0027 | +0.0000 | +0.0052 / -0.0036 / +0.0030 |
| pts:epa_ytd_k64 | -0.0018 | -0.0056 | +0.0000 | -0.0018 | -0.0039 | +0.0000 | -0.0014 | -0.0010 | +0.0000 | +0.0018 / -0.0002 / -0.0158 |
| pts:epa_ytd_k128 | +0.0005 | -0.0034 | +0.0000 | -0.0014 | -0.0058 | +0.0000 | +0.0004 | +0.0026 | +0.0000 | +0.0049 / +0.0027 / -0.0103 |
| pts:epa_ytd_k256 | +0.0006 | +0.0000 | +0.0000 | -0.0031 | -0.0070 | +0.0000 | -0.0003 | +0.0020 | +0.0000 | +0.0013 / +0.0035 / -0.0090 |
| pts:epa_rec_k64 | +0.0004 | +0.0004 | +0.0000 | -0.0023 | -0.0061 | +0.0000 | +0.0016 | +0.0048 | +0.0000 | +0.0045 / -0.0010 / -0.0024 |
| pts:epa_rec_k128 | -0.0012 | -0.0016 | +0.0000 | -0.0016 | -0.0058 | +0.0000 | -0.0001 | +0.0014 | +0.0000 | +0.0022 / +0.0018 / -0.0023 |
| pts:epa_rec_k256 | -0.0007 | -0.0024 | +0.0000 | -0.0018 | -0.0054 | +0.0000 | -0.0001 | +0.0008 | +0.0000 | +0.0028 / +0.0026 / -0.0031 |
| tot:pts_prev | +0.0100 | +0.0000 | +0.0284 | +0.0000 | +0.0000 | +0.0030 | +0.0029 | +0.0000 | +0.0108 | +0.0000 / +0.0000 / +0.0000 |
| tot:pts_ytd_k64 | +0.0124 | +0.0000 | +0.0234 | -0.0050 | +0.0000 | -0.0049 | -0.0064 | +0.0000 | -0.0106 | +0.0000 / +0.0000 / +0.0000 |
| tot:pts_ytd_k128 | +0.0111 | +0.0000 | +0.0208 | -0.0006 | +0.0000 | +0.0049 | -0.0066 | +0.0000 | -0.0114 | +0.0000 / +0.0000 / +0.0000 |
| tot:pts_ytd_k256 | +0.0097 | +0.0000 | +0.0199 | +0.0035 | +0.0000 | +0.0135 | -0.0048 | +0.0000 | -0.0077 | +0.0000 / +0.0000 / +0.0000 |
| tot:pts_rec_k64 | +0.0039 | +0.0000 | +0.0092 | -0.0105 | +0.0000 | -0.0148 | -0.0028 | +0.0000 | -0.0029 | +0.0000 / +0.0000 / +0.0000 |
| tot:pts_rec_k128 | +0.0059 | +0.0000 | +0.0139 | -0.0056 | +0.0000 | +0.0002 | -0.0050 | +0.0000 | -0.0086 | +0.0000 / +0.0000 / +0.0000 |
| tot:pts_rec_k256 | +0.0102 | +0.0000 | +0.0243 | -0.0012 | +0.0000 | +0.0117 | -0.0040 | +0.0000 | -0.0067 | +0.0000 / +0.0000 / +0.0000 |
| tot:epa_prev | +0.0098 | +0.0000 | +0.0313 | -0.0008 | +0.0000 | +0.0036 | +0.0022 | +0.0000 | +0.0011 | +0.0000 / +0.0000 / +0.0000 |
| tot:epa_ytd_k64 | +0.0039 | +0.0000 | +0.0072 | +0.0036 | +0.0000 | +0.0162 | -0.0031 | +0.0000 | -0.0023 | +0.0000 / +0.0000 / +0.0000 |
| tot:epa_ytd_k128 | +0.0021 | +0.0000 | +0.0068 | +0.0049 | +0.0000 | +0.0190 | -0.0020 | +0.0000 | +0.0003 | +0.0000 / +0.0000 / +0.0000 |
| tot:epa_ytd_k256 | +0.0019 | +0.0000 | +0.0110 | +0.0052 | +0.0000 | +0.0209 | +0.0003 | +0.0000 | +0.0041 | +0.0000 / +0.0000 / +0.0000 |
| tot:epa_rec_k64 | +0.0015 | +0.0000 | +0.0050 | +0.0001 | +0.0000 | +0.0103 | -0.0017 | +0.0000 | -0.0010 | +0.0000 / +0.0000 / +0.0000 |
| tot:epa_rec_k128 | +0.0016 | +0.0000 | +0.0073 | +0.0018 | +0.0000 | +0.0161 | -0.0020 | +0.0000 | -0.0003 | +0.0000 / +0.0000 / +0.0000 |
| tot:epa_rec_k256 | +0.0033 | +0.0000 | +0.0116 | +0.0018 | +0.0000 | +0.0158 | -0.0007 | +0.0000 | +0.0012 | +0.0000 / +0.0000 / +0.0000 |
| pair pts:pts_rec_k64+epa_ytd_k64 | -0.0025 | -0.0056 | +0.0000 | -0.0029 | -0.0118 | +0.0000 | -0.0002 | -0.0001 | +0.0000 | +0.0049 / -0.0099 / -0.0080 |
| pair tot:pts_rec_k64+pts_ytd_k64 | +0.0166 | +0.0002 | +0.0321 | -0.0058 | -0.0002 | -0.0120 | -0.0035 | +0.0009 | -0.0035 | +0.0001 / -0.0008 / +0.0003 |
| both pts:pts_rec_k64 tot:pts_rec_k64 | +0.0025 | -0.0031 | +0.0092 | -0.0136 | -0.0122 | -0.0148 | -0.0025 | -0.0019 | -0.0029 | +0.0024 / -0.0112 / -0.0054 |

## The drift the study is about: the base model's signed bias by season (model minus actual, regular season)

| season | total bias | points-equation bias per team | games |
|---|---|---|---|
| 2015 | -0.04 | +0.13 | 256 |
| 2016 | +0.36 | +0.05 | 256 |
| 2017 | +1.50 | +0.73 | 256 |
| 2018 | -0.43 | -0.67 | 256 |
| 2019 | -0.31 | -0.14 | 256 |
| 2020 | -2.83 | -1.48 | 256 |
| 2021 | +0.39 | +0.11 | 272 |
| 2022 | +1.55 | +0.94 | 271 |
| 2023 | +0.68 | +0.71 | 272 |
| 2024 | -0.36 | -0.03 | 272 |
| 2025 | -0.21 | -0.10 | 272 |

## Reading the points-equation rows

A league-level input is the same number for both teams, so in the ridge it cancels in the margin exactly; what moves the
margin is the other coefficients re-settling around it and the boosted trees in the blend, which do not cancel. The
margin gains are hundredths of a point at most. The `pair tot:` and `both` rows refit the trees where the singles read
the cache, and the base inputs refit on this machine moved the margin miss by 0.0002 (9.9493 against 9.9491 on 2015-18),
so a 2023-25 margin gain of 0.001 or less is inside the trees' own noise. The 4+ spread record, which the rule does not
score, is worse on every window for `pts_rec_k64` (66-56 / 79-54 / 44-28 against 68-55 / 83-54 / 44-26) and about level
for `epa_ytd_k64` and the pair. In the total equation, where the input would matter most,
every candidate is worse on 2015-18: it adds a positive bias there (+0.4 to +1.1 against +0.35) while trimming the
2023-25 miss and bias, the same shape as the passing rolling factor for props (fixes the late drift, costs the early
windows).

## Verdict

Variants meeting the letter of the rule: `pts:pts_rec_k64`, `pts:epa_ytd_k64`, `pair pts:pts_rec_k64+epa_ytd_k64`. Each passes only at one k (its k128 and k256
siblings fail), none wins more spread bets at 4+, and the 2023-25 margin gains are within the trees' refit noise, so the
pass is not a stable effect. Recommendation: not adopted; the points equation's intercept keeps carrying the league level. No
total-equation candidate passes.
