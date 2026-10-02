# Calibration audit, 2026-10-02 16:48 UTC

Every chance the model states against what happened, regular season, from the committed prediction table (pred_v3) and results (games). Said is the mean stated chance in the bucket, z is how many binomial standard errors the outcome sits from it. A bucket with 150+ games and |z| over 2.5 fails the health check (the three checked tables are the calibrated home win chance, the calibrated cover chance and the calibrated over chance, the figures the cards show); every other table is the audit's record and does not fail. Windows are the backtest's: 2015-18 untouched, 2019-22 tuning, 2023-25 held out. Rebuilt by nflmodel.tie_check on every run.

## Findings (27 Sep 2026 audit; the tables below are today's)

- Over chance: the raw p_over_emp was too far from 50% on both sides, every window (said 63% over, the over came 50%: 2015-25 n 256, z -4.5; said 55%, came 50%: n 1119, z -2.8; said 46%, came 49%: n 1125, z +2.3; the same shape in each window). Cause: the chance is priced as if the model's total were the truth and the line carried nothing, while the line's miss is the model's (MAE 10.5 each). Shipped 27 Sep 2026, a mapping and not a model change: the cards, the takeaways and the report show p_over_cal = logistic(a + b x logit(p_over_emp)) (picks.over_calibration), fit walk-forward on every regular-season game from 2015 to the season before the one priced, refit every run (today a -0.040, b 0.389 on 2869 games: 63% raw reads 54%, 55% reads 51%). It scores a better log loss and Brier than the raw chance on 2016-18, 2019-22, 2020-22 and 2023-25 (table below), and the checked over table is now the calibrated one. The totals flag (unders at 55%+) stays on the raw chance, the same monotone mapping, so it is the same rule with the same records; the raw table stays below for the record.
- Home win chance (p_home): the home side won less often than said when the model had it a slight underdog. Said 45%, won 39% in 2015-25 (n 556, z -3.0; 2023-25 alone n 180, 45% said, 34% won, z -3.0); said 35%, won 30% (n 327, z -2.0); the line was high in the same games but less (43% implied); overall 2019-22 said 56.0% home and 52.4% happened (z -2.5) while the fitted home coefficient was 2.2 and 1.9 points in 2019 and 2020 against a realised home margin near 0. Cause: one home-field term fit on 2013 on lags the fall in home advantage; a home term that follows recent seasons did not fix the 2023-25 bucket (31 variants, reports/home_field_recency.md), so the model stays. Shipped 27 Sep 2026, a mapping and not a model change: the cards, the friends' report and the picks file show p_home_cal = logistic(a + b x logit(p_home)) (picks.home_calibration), fit walk-forward on every regular-season game from 2015 to the season before the one priced, ties dropped, the identity under 500 games (two seasons: a one-season fit read worse than the raw chance), refit every run (today a -0.123, b 1.191 on 2885 games: 45% raw reads 41%, 35% reads 30%, 65% reads 65%). It scores a better log loss and Brier than the raw chance on 2016-18, 2019-22, 2020-22 and 2023-25 (table below; a richer form with an intercept shift for the home side being the model's underdog was worse than the raw chance on 2016-18 and is not adopted), and the checked home table is now the calibrated one. It does not cure the 2023-25 slight-underdog bucket: it moves a third of those games down into 0.3-0.4, where they sit within noise, and the 147 left say 45% and won 35% (z -2.5), three games under the check's 150-game floor; the stretch (b over 1) also reads the few 10-20% home sides low (2016-25 n 61, said 16%, won 31%, under the floor). The season simulation (season.py, the season file's chance per game) still reads the raw chance; the raw table stays below for the record.
- Calibrated cover chance (the cards' cover odds, picks.calibration): honest within noise in every band, 2019-25. It is nearly flat (50% at a 0-point edge to 56% at 7) and conservative on the flags: 4-5 point edges said 54% and covered 64% (n 107, z +2.0) while 2-4 point edges covered 48% (n 546). The raw bell-curve chance (p_cover_home, picks file only) runs 8 to 15 points hot at every edge (3-4 points: said 61%, covered 47%, z -3.7), as documented.
- Cover biases (2019-25, all games at the model's side): home or away side, favorite or underdog, primetime and divisional games are all within 2 SE in every window. One bucket is not: in 2023-25 the model's side covered 41% in the highest third of totals (n 201, z -3.0); 2019-22 was 54% and 2015-18 51% in the same third, so it is not a standing flaw.
- Margin scale: the stated sigma (13.0 to 13.2) is a shade wide against the realised spread of result minus model spread (12.8 to 12.9): the 50% interval holds 53 to 55%, the 80% 80 to 82%, the 95% 94 to 95%.
- Team points by tier: within noise except the top tier in 2023-25, where sides expected to score 27+ scored 30.7 against 28.6 said (n 172, z -2.9); 2015-18 and 2019-22 show no such gap.
- Season odds (reports/season_calibration.csv): 2019-22 is within noise in every band; 2023-25 is overconfident at both ends (division chances said 1% came 4%, n 183, z +4.5; playoff chances said 77% came 59%, n 41, z -2.9), as the docs already say.
- Player props (data/tracker/props_graded.csv, two weeks, projections made after the fact): every volume stat is projected high. Targets 4.9 said, 3.4 happened (ratio 0.69, z 12); carries 0.78; catches 0.80; receiving TDs 0.78 (101 said, 79 scored); interceptions 0.70; tackles 0.88. A quarter of the receiving rows (22.5%) are players who saw no target; without them targets are still 18% high and receiving TDs 7.5% high. TD chances read as 1 - exp(-projection) overstate the anytime rate: a 0.15-0.25 TD projection scored in 8.6% of games against 17.9% implied (n 128, z -2.7). Cause: the volume shares do not fall enough for depth players, and no availability check drops players who will not play. Two weeks is too few for a check; reviewed here until the record is long enough.

## Game winner: calibrated home win chance (p_home_cal, the cards' figure) by decile

p_home_cal = logistic(a + b x logit(p_home)), picks.home_calibration: fit on every regular-season game from 2015 to the season before the one priced, ties dropped (walk-forward; each season below is scored with the fit in force for it, the identity under 500 games, so 2017 is the first season scored). Today's fit on 2015 to 2025: a -0.122, b 1.188 on 2885 games (b = 1 and a = 0 would be p_home itself): 35% raw reads 29.8%, 45% raw reads 41.1%, 55% raw reads 52.9%, 65% raw reads 64.9%, 75% raw reads 76.5%. Ties count half. The season simulation (season.py) still reads the raw chance.

**2015-18** (2017 to 2018 scored): 512 games, said 0.566 home, happened 0.584. Against the moneyline (511 games): Brier model 0.2080, line 0.2048; log loss model 0.6058, line 0.5993.

| Bucket | Games | Said | Happened | z |
|---|---|---|---|---|
| [0.2, 0.3) | 34 | 0.261 | 0.206 | -0.7 |
| [0.3, 0.4) | 56 | 0.355 | 0.312 | -0.7 |
| [0.4, 0.5) | 83 | 0.453 | 0.464 | +0.2 |
| [0.5, 0.6) | 112 | 0.555 | 0.580 | +0.5 |
| [0.6, 0.7) | 106 | 0.647 | 0.708 | +1.3 |
| [0.7, 0.8) | 79 | 0.745 | 0.772 | +0.6 |
| [0.8, 0.9) | 31 | 0.836 | 0.839 | +0.0 |

**2019-22** (2019 to 2022 scored): 1055 games, said 0.543 home, happened 0.524. Against the moneyline (1055 games): Brier model 0.2164, line 0.2099; log loss model 0.6252, line 0.6094.

| Bucket | Games | Said | Happened | z |
|---|---|---|---|---|
| [0.1, 0.2) | 36 | 0.161 | 0.306 | +2.4 |
| [0.2, 0.3) | 77 | 0.253 | 0.214 | -0.8 |
| [0.3, 0.4) | 145 | 0.349 | 0.334 | -0.4 |
| [0.4, 0.5) | 178 | 0.450 | 0.413 | -1.0 |
| [0.5, 0.6) | 185 | 0.550 | 0.519 | -0.9 |
| [0.6, 0.7) | 174 | 0.651 | 0.626 | -0.7 |
| [0.7, 0.8) | 161 | 0.751 | 0.708 | -1.3 |
| [0.8, 0.9) | 70 | 0.836 | 0.871 | +0.8 |

**2023-25** (2023 to 2025 scored): 816 games, said 0.536 home, happened 0.542. Against the moneyline (816 games): Brier model 0.2150, line 0.2101; log loss model 0.6202, line 0.6083.

| Bucket | Games | Said | Happened | z |
|---|---|---|---|---|
| [0.2, 0.3) | 66 | 0.253 | 0.280 | +0.5 |
| [0.3, 0.4) | 121 | 0.358 | 0.364 | +0.1 |
| [0.4, 0.5) | 146 | 0.450 | 0.363 | -2.1 |
| [0.5, 0.6) | 156 | 0.551 | 0.571 | +0.5 |
| [0.6, 0.7) | 144 | 0.652 | 0.743 | +2.3 |
| [0.7, 0.8) | 97 | 0.748 | 0.722 | -0.6 |
| [0.8, 0.9) | 59 | 0.850 | 0.814 | -0.8 |

**2015-25** (2017 to 2025 scored): 2383 games, said 0.546 home, happened 0.543. Against the moneyline (2382 games): Brier model 0.2141, line 0.2089; log loss model 0.6193, line 0.6069.

| Bucket | Games | Said | Happened | z |
|---|---|---|---|---|
| [0.1, 0.2) | 60 | 0.157 | 0.317 | +3.4 |
| [0.2, 0.3) | 177 | 0.255 | 0.237 | -0.5 |
| [0.3, 0.4) | 322 | 0.354 | 0.342 | -0.5 |
| [0.4, 0.5) | 407 | 0.451 | 0.405 | -1.8 |
| [0.5, 0.6) | 453 | 0.552 | 0.552 | -0.0 |
| [0.6, 0.7) | 424 | 0.651 | 0.686 | +1.5 |
| [0.7, 0.8) | 337 | 0.749 | 0.727 | -0.9 |
| [0.8, 0.9) | 160 | 0.841 | 0.844 | +0.1 |
| [0.9, 1.0) | 38 | 0.924 | 0.947 | +0.5 |

### The mapping against the raw chance: log loss and Brier (lower is better), and the mapped 0.4-0.5 and 0.3-0.4 buckets

| Window | Games | Log loss p_home | Log loss p_home_cal | Brier p_home | Brier p_home_cal | Mapped 0.4-0.5 said / happened | Mapped 0.3-0.4 said / happened |
|---|---|---|---|---|---|---|---|
| 2016-18 (2017 to 2018 scored) | 512 | 0.60741 | 0.60507 | 0.20866 | 0.20772 | 0.453 / 0.464 (n 83) | 0.355 / 0.312 (n 56) |
| 2019-22 (2019 to 2022 scored) | 1055 | 0.62660 | 0.62516 | 0.21748 | 0.21642 | 0.450 / 0.413 (n 178) | 0.349 / 0.334 (n 145) |
| 2020-22 (2020 to 2022 scored) | 799 | 0.62830 | 0.62714 | 0.21808 | 0.21695 | 0.450 / 0.421 (n 139) | 0.350 / 0.335 (n 112) |
| 2023-25 (2023 to 2025 scored) | 816 | 0.62150 | 0.62015 | 0.21587 | 0.21504 | 0.450 / 0.363 (n 146) | 0.358 / 0.364 (n 121) |

### Raw home win chance (p_home, the season simulation's chance) by decile: the record, not a check

Ties count half.

**2015-18**: 1024 games, said 0.573 home, happened 0.571. Against the moneyline (1023 games): Brier model 0.2154, line 0.2146; log loss model 0.6217, line 0.6201.

| Bucket | Games | Said | Happened | z |
|---|---|---|---|---|
| [0.3, 0.4) | 112 | 0.353 | 0.263 | -2.0 |
| [0.4, 0.5) | 179 | 0.456 | 0.455 | -0.0 |
| [0.5, 0.6) | 249 | 0.554 | 0.544 | -0.3 |
| [0.6, 0.7) | 246 | 0.646 | 0.677 | +1.0 |
| [0.7, 0.8) | 162 | 0.743 | 0.759 | +0.5 |
| [0.8, 0.9) | 43 | 0.835 | 0.837 | +0.0 |

**2019-22**: 1055 games, said 0.560 home, happened 0.524. Against the moneyline (1055 games): Brier model 0.2175, line 0.2099; log loss model 0.6266, line 0.6094.

| Bucket | Games | Said | Happened | z |
|---|---|---|---|---|
| [0.2, 0.3) | 53 | 0.264 | 0.283 | +0.3 |
| [0.3, 0.4) | 124 | 0.360 | 0.282 | -1.8 |
| [0.4, 0.5) | 200 | 0.456 | 0.385 | -2.0 |
| [0.5, 0.6) | 226 | 0.552 | 0.493 | -1.8 |
| [0.6, 0.7) | 210 | 0.650 | 0.633 | -0.5 |
| [0.7, 0.8) | 172 | 0.746 | 0.738 | -0.2 |
| [0.8, 0.9) | 48 | 0.843 | 0.875 | +0.6 |

**2023-25**: 816 games, said 0.555 home, happened 0.542. Against the moneyline (816 games): Brier model 0.2159, line 0.2101; log loss model 0.6215, line 0.6083.

| Bucket | Games | Said | Happened | z |
|---|---|---|---|---|
| [0.2, 0.3) | 33 | 0.266 | 0.333 | +0.9 |
| [0.3, 0.4) | 90 | 0.351 | 0.361 | +0.2 |
| [0.4, 0.5) | 173 | 0.450 | 0.341 | -2.9 |
| [0.5, 0.6) | 188 | 0.552 | 0.521 | -0.8 |
| [0.6, 0.7) | 168 | 0.651 | 0.726 | +2.0 |
| [0.7, 0.8) | 101 | 0.745 | 0.723 | -0.5 |
| [0.8, 0.9) | 51 | 0.840 | 0.863 | +0.4 |

**2015-25**: 2895 games, said 0.563 home, happened 0.546. Against the moneyline (2894 games): Brier model 0.2163, line 0.2116; log loss model 0.6234, line 0.6129.

| Bucket | Games | Said | Happened | z |
|---|---|---|---|---|
| [0.2, 0.3) | 110 | 0.263 | 0.300 | +0.9 |
| [0.3, 0.4) | 326 | 0.355 | 0.298 | -2.2 |
| [0.4, 0.5) | 552 | 0.454 | 0.394 | -2.8 |
| [0.5, 0.6) | 663 | 0.553 | 0.520 | -1.7 |
| [0.6, 0.7) | 624 | 0.649 | 0.675 | +1.4 |
| [0.7, 0.8) | 435 | 0.745 | 0.743 | -0.1 |
| [0.8, 0.9) | 142 | 0.839 | 0.859 | +0.6 |

## Spread cover: the model's side, by size of the edge

Calibrated cover chance = picks.calibration's logistic on |edge| capped at 7, fit on 2019 to 2025 (intercept -0.026, slope 0.0453 a point): 49.4% at 0, 51.6% at 2, 53.9% at 4, 56.1% at 6, 57.2% at 7. Raw = the bell curve's own cover chance (p_cover_home; picks file only). Pushes dropped.

**2019-22**: 1031 games.

| Edge | Games | Said (calibrated) | Said (raw) | Covered | z (calibrated) | z (raw) |
|---|---|---|---|---|---|---|
| 0-1 | 331 | 0.499 | 0.513 | 0.532 | +1.2 | +0.7 |
| 1-2 | 259 | 0.510 | 0.548 | 0.502 | -0.3 | -1.5 |
| 2-3 | 184 | 0.522 | 0.583 | 0.516 | -0.1 | -1.8 |
| 3-4 | 121 | 0.533 | 0.612 | 0.471 | -1.4 | -3.2 |
| 4-5 | 68 | 0.544 | 0.639 | 0.632 | +1.5 | -0.1 |
| 5-6 | 39 | 0.556 | 0.673 | 0.615 | +0.8 | -0.8 |
| 6+ | 29 | 0.569 | 0.724 | 0.517 | -0.6 | -2.5 |

**2023-25**: 797 games.

| Edge | Games | Said (calibrated) | Said (raw) | Covered | z (calibrated) | z (raw) |
|---|---|---|---|---|---|---|
| 0-1 | 252 | 0.499 | 0.521 | 0.468 | -1.0 | -1.7 |
| 1-2 | 240 | 0.510 | 0.547 | 0.529 | +0.6 | -0.5 |
| 2-3 | 158 | 0.521 | 0.570 | 0.475 | -1.2 | -2.4 |
| 3-4 | 83 | 0.532 | 0.600 | 0.506 | -0.5 | -1.7 |
| 4-5 | 35 | 0.545 | 0.639 | 0.657 | +1.3 | +0.2 |
| 5-6 | 15 | 0.556 | 0.659 | 0.533 | -0.2 | -1.0 |
| 6+ | 14 | 0.568 | 0.720 | 0.714 | +1.1 | -0.0 |

**2019-25**: 1828 games.

| Edge | Games | Said (calibrated) | Said (raw) | Covered | z (calibrated) | z (raw) |
|---|---|---|---|---|---|---|
| 0-1 | 583 | 0.499 | 0.516 | 0.504 | +0.3 | -0.6 |
| 1-2 | 499 | 0.510 | 0.547 | 0.515 | +0.2 | -1.4 |
| 2-3 | 342 | 0.521 | 0.577 | 0.497 | -0.9 | -3.0 |
| 3-4 | 204 | 0.533 | 0.607 | 0.485 | -1.4 | -3.6 |
| 4-5 | 103 | 0.544 | 0.639 | 0.641 | +2.0 | +0.0 |
| 5-6 | 54 | 0.556 | 0.669 | 0.593 | +0.5 | -1.2 |
| 6+ | 43 | 0.569 | 0.723 | 0.581 | +0.2 | -2.1 |

**2015-18** (before the calibration window; not checked): 994 games.

| Edge | Games | Said (calibrated) | Said (raw) | Covered | z (calibrated) | z (raw) |
|---|---|---|---|---|---|---|
| 0-1 | 344 | 0.499 | 0.516 | 0.480 | -0.7 | -1.3 |
| 1-2 | 261 | 0.510 | 0.547 | 0.490 | -0.6 | -1.8 |
| 2-3 | 157 | 0.521 | 0.581 | 0.573 | +1.3 | -0.2 |
| 3-4 | 107 | 0.533 | 0.610 | 0.458 | -1.5 | -3.2 |
| 4-5 | 73 | 0.544 | 0.633 | 0.534 | -0.2 | -1.7 |
| 5-6 | 34 | 0.555 | 0.674 | 0.647 | +1.1 | -0.3 |
| 6+ | 18 | 0.568 | 0.721 | 0.444 | -1.1 | -2.6 |

### Biases: the model's side by situation (said = calibrated chance; flags = edge of 4+)

| Window | Group | Games | Said | Covered | z | Flags | Flags covered |
|---|---|---|---|---|---|---|---|
| 2015-18 | home side | 545 | 0.516 | 0.494 | -1.1 | 73 | 0.411 |
| 2015-18 | away side | 449 | 0.515 | 0.517 | +0.1 | 52 | 0.750 |
| 2015-18 | favorite | 365 | 0.512 | 0.496 | -0.6 | 37 | 0.486 |
| 2015-18 | underdog | 625 | 0.517 | 0.509 | -0.4 | 88 | 0.580 |
| 2015-18 | high total | 294 | 0.515 | 0.503 | -0.4 | 33 | 0.485 |
| 2015-18 | mid total | 326 | 0.514 | 0.512 | -0.1 | 39 | 0.538 |
| 2015-18 | low total | 374 | 0.517 | 0.497 | -0.7 | 53 | 0.604 |
| 2015-18 | primetime | 200 | 0.518 | 0.515 | -0.1 | 30 | 0.600 |
| 2015-18 | daytime | 794 | 0.515 | 0.501 | -0.8 | 95 | 0.537 |
| 2015-18 | non-divisional | 620 | 0.515 | 0.500 | -0.8 | 71 | 0.563 |
| 2015-18 | divisional | 374 | 0.516 | 0.511 | -0.2 | 54 | 0.537 |
| 2019-22 | home side | 578 | 0.518 | 0.500 | -0.9 | 78 | 0.577 |
| 2019-22 | away side | 453 | 0.515 | 0.554 | +1.6 | 58 | 0.638 |
| 2019-22 | favorite | 357 | 0.511 | 0.471 | -1.5 | 17 | 0.412 |
| 2019-22 | underdog | 674 | 0.520 | 0.552 | +1.7 | 119 | 0.630 |
| 2019-22 | mid total | 330 | 0.518 | 0.518 | -0.0 | 43 | 0.651 |
| 2019-22 | high total | 377 | 0.514 | 0.525 | +0.4 | 36 | 0.611 |
| 2019-22 | low total | 324 | 0.519 | 0.528 | +0.3 | 57 | 0.561 |
| 2019-22 | primetime | 208 | 0.516 | 0.500 | -0.5 | 24 | 0.500 |
| 2019-22 | daytime | 823 | 0.517 | 0.530 | +0.7 | 112 | 0.625 |
| 2019-22 | divisional | 376 | 0.518 | 0.543 | +0.9 | 54 | 0.556 |
| 2019-22 | non-divisional | 655 | 0.516 | 0.513 | -0.2 | 82 | 0.634 |
| 2023-25 | home side | 464 | 0.516 | 0.506 | -0.4 | 41 | 0.659 |
| 2023-25 | away side | 333 | 0.513 | 0.505 | -0.3 | 23 | 0.609 |
| 2023-25 | favorite | 303 | 0.513 | 0.528 | +0.5 | 15 | 0.667 |
| 2023-25 | underdog | 494 | 0.516 | 0.492 | -1.1 | 49 | 0.633 |
| 2023-25 | high total | 201 | 0.514 | 0.403 | -3.1 | 17 | 0.529 |
| 2023-25 | low total | 379 | 0.516 | 0.544 | +1.1 | 39 | 0.641 |
| 2023-25 | mid total | 217 | 0.513 | 0.535 | +0.6 | 8 | 0.875 |
| 2023-25 | primetime | 170 | 0.514 | 0.453 | -1.6 | 13 | 0.615 |
| 2023-25 | daytime | 627 | 0.515 | 0.520 | +0.3 | 51 | 0.647 |
| 2023-25 | non-divisional | 514 | 0.514 | 0.504 | -0.5 | 40 | 0.625 |
| 2023-25 | divisional | 283 | 0.515 | 0.509 | -0.2 | 24 | 0.667 |

## Totals: calibrated over chance (p_over_cal, the cards' figure) by decile

p_over_cal = logistic(a + b x logit(p_over_emp)), picks.over_calibration: fit on every regular-season game from 2015 to the season before the one priced (walk-forward; each season below is scored with the fit in force for it, so 2016 is the first season scored). Today's fit on 2015 to 2025: a -0.040, b 0.375 on 2869 games (b = 1 and a = 0 would be p_over_emp itself): 35% raw reads 43.2%, 45% raw reads 47.1%, 55% raw reads 50.9%, 65% raw reads 54.8%. Pushes dropped. The totals flag (an under at 55%+) stays on the raw chance.

**2015-18** (2016 to 2018 scored): 764 games, said 0.490 over, happened 0.488.

| Bucket | Games | Said | Happened | z |
|---|---|---|---|---|
| [0.4, 0.5) | 520 | 0.482 | 0.502 | +0.9 |
| [0.5, 0.6) | 242 | 0.509 | 0.463 | -1.4 |

**2019-22** (2019 to 2022 scored): 1043 games, said 0.486 over, happened 0.477.

| Bucket | Games | Said | Happened | z |
|---|---|---|---|---|
| [0.4, 0.5) | 814 | 0.479 | 0.473 | -0.3 |
| [0.5, 0.6) | 229 | 0.514 | 0.493 | -0.6 |

**2023-25** (2023 to 2025 scored): 811 games, said 0.490 over, happened 0.507.

| Bucket | Games | Said | Happened | z |
|---|---|---|---|---|
| [0.4, 0.5) | 512 | 0.475 | 0.488 | +0.6 |
| [0.5, 0.6) | 297 | 0.517 | 0.542 | +0.9 |

**2015-25** (2016 to 2025 scored): 2618 games, said 0.489 over, happened 0.490.

| Bucket | Games | Said | Happened | z |
|---|---|---|---|---|
| [0.4, 0.5) | 1846 | 0.478 | 0.485 | +0.6 |
| [0.5, 0.6) | 768 | 0.513 | 0.503 | -0.6 |

### The mapping against the raw chance: log loss and Brier (lower is better), and the mapped 0.5-0.6 and 0.4-0.5 buckets

| Window | Games | Log loss p_over_emp | Log loss p_over_cal | Brier p_over_emp | Brier p_over_cal | Mapped 0.5-0.6 said / happened | Mapped 0.4-0.5 said / happened |
|---|---|---|---|---|---|---|---|
| 2016-18 | 764 | 0.70511 | 0.69500 | 0.25579 | 0.25093 | 0.509 / 0.463 (n 242) | 0.482 / 0.502 (n 520) |
| 2019-22 | 1043 | 0.69316 | 0.69008 | 0.24990 | 0.24847 | 0.514 / 0.493 (n 229) | 0.479 / 0.473 (n 814) |
| 2020-22 | 788 | 0.69494 | 0.68945 | 0.25071 | 0.24816 | 0.514 / 0.496 (n 224) | 0.476 / 0.459 (n 564) |
| 2023-25 | 811 | 0.69239 | 0.69075 | 0.24956 | 0.24881 | 0.517 / 0.542 (n 297) | 0.475 / 0.488 (n 512) |

### Raw over chance (p_over_emp, the totals flag's chance) by decile: the record, not a check

Pushes dropped. p_over (the normal curve, picks file only) is quoted for reference.

**2015-18**: 1015 games, said 0.498 over (normal curve 0.511), happened 0.486.

| Bucket | Games | Said | Happened | z |
|---|---|---|---|---|
| [0.3, 0.4) | 91 | 0.362 | 0.440 | +1.5 |
| [0.4, 0.5) | 410 | 0.458 | 0.495 | +1.5 |
| [0.5, 0.6) | 417 | 0.545 | 0.480 | -2.7 |
| [0.6, 0.7) | 80 | 0.630 | 0.500 | -2.4 |

**2019-22**: 1043 games, said 0.480 over (normal curve 0.492), happened 0.477.

| Bucket | Games | Said | Happened | z |
|---|---|---|---|---|
| [0.3, 0.4) | 161 | 0.358 | 0.429 | +1.9 |
| [0.4, 0.5) | 390 | 0.456 | 0.462 | +0.2 |
| [0.5, 0.6) | 393 | 0.543 | 0.529 | -0.6 |
| [0.6, 0.7) | 68 | 0.629 | 0.471 | -2.7 |

**2023-25**: 811 games, said 0.517 over (normal curve 0.534), happened 0.507.

| Bucket | Games | Said | Happened | z |
|---|---|---|---|---|
| [0.3, 0.4) | 55 | 0.366 | 0.436 | +1.1 |
| [0.4, 0.5) | 263 | 0.461 | 0.452 | -0.3 |
| [0.5, 0.6) | 378 | 0.547 | 0.548 | +0.0 |
| [0.6, 0.7) | 108 | 0.631 | 0.537 | -2.0 |

**2015-25**: 2869 games, said 0.497 over (normal curve 0.511), happened 0.489.

| Bucket | Games | Said | Happened | z |
|---|---|---|---|---|
| [0.2, 0.3) | 43 | 0.268 | 0.349 | +1.2 |
| [0.3, 0.4) | 307 | 0.361 | 0.433 | +2.6 |
| [0.4, 0.5) | 1063 | 0.458 | 0.472 | +0.9 |
| [0.5, 0.6) | 1188 | 0.545 | 0.518 | -1.9 |
| [0.6, 0.7) | 256 | 0.630 | 0.508 | -4.1 |

### Model total against the actual total, by third of the line (bias = said minus happened)

| Window | Third | Games | Line | Model | Actual | Bias model | Bias line | MAE model | MAE line |
|---|---|---|---|---|---|---|---|---|---|
| 2015-18 | low | 384 | 41.3 | 42.7 | 41.5 | +1.28 | -0.17 | 10.63 | 10.46 |
| 2015-18 | mid | 336 | 45.4 | 45.7 | 44.6 | +1.10 | +0.77 | 10.31 | 10.12 |
| 2015-18 | high | 304 | 50.3 | 49.4 | 51.0 | -1.57 | -0.64 | 11.36 | 11.14 |
| 2019-22 | low | 335 | 41.1 | 42.0 | 41.0 | +0.99 | +0.07 | 10.00 | 10.10 |
| 2019-22 | mid | 337 | 45.5 | 45.6 | 46.2 | -0.68 | -0.76 | 11.01 | 11.01 |
| 2019-22 | high | 383 | 50.5 | 48.9 | 50.7 | -1.77 | -0.14 | 10.60 | 10.52 |
| 2023-25 | low | 391 | 40.5 | 42.3 | 41.9 | +0.36 | -1.41 | 9.95 | 10.13 |
| 2023-25 | mid | 221 | 45.4 | 46.6 | 46.0 | +0.59 | -0.67 | 9.85 | 9.71 |
| 2023-25 | high | 204 | 49.4 | 49.3 | 50.3 | -1.00 | -0.87 | 10.73 | 10.55 |

## Margin scale: stated sigma against the realised miss, and how much of it the 50 / 80 / 95% intervals hold

| Window | Games | Sigma stated | Realised SD | Mean miss (result minus model) | Line's SD | 50% holds | 80% holds | 95% holds |
|---|---|---|---|---|---|---|---|---|
| 2015-18 | 1024 | 13.20 | 12.90 | -0.21 | 12.75 | 0.552 | 0.820 | 0.936 |
| 2019-22 | 1055 | 13.07 | 12.90 | -0.98 | 12.76 | 0.528 | 0.803 | 0.945 |
| 2023-25 | 816 | 13.00 | 12.80 | +0.24 | 12.64 | 0.548 | 0.804 | 0.949 |

## Team points by tier of the expected score (bias = said minus scored; z on the scores' own spread)

| Window | Tier | Sides | Said | Scored | Bias | z |
|---|---|---|---|---|---|---|
| 2015-18 | under 18 | 156 | 16.21 | 17.15 | -0.94 | -1.3 |
| 2015-18 | 18-21 | 475 | 19.63 | 19.21 | +0.42 | +1.0 |
| 2015-18 | 21-24 | 605 | 22.50 | 22.31 | +0.19 | +0.5 |
| 2015-18 | 24-27 | 592 | 25.37 | 25.04 | +0.32 | +0.8 |
| 2015-18 | 27+ | 220 | 28.67 | 28.59 | +0.08 | +0.1 |
| 2019-22 | under 18 | 219 | 16.14 | 16.94 | -0.80 | -1.3 |
| 2019-22 | 18-21 | 431 | 19.66 | 20.03 | -0.37 | -0.9 |
| 2019-22 | 21-24 | 643 | 22.58 | 22.47 | +0.11 | +0.3 |
| 2019-22 | 24-27 | 542 | 25.38 | 25.55 | -0.17 | -0.4 |
| 2019-22 | 27+ | 275 | 28.65 | 29.45 | -0.79 | -1.4 |
| 2023-25 | under 18 | 189 | 16.17 | 15.41 | +0.76 | +1.2 |
| 2023-25 | 18-21 | 327 | 19.66 | 20.08 | -0.42 | -0.9 |
| 2023-25 | 21-24 | 526 | 22.53 | 22.01 | +0.52 | +1.3 |
| 2023-25 | 24-27 | 409 | 25.34 | 25.08 | +0.26 | +0.6 |
| 2023-25 | 27+ | 181 | 28.70 | 30.46 | -1.76 | -2.4 |

## Season odds (reports/season_calibration.csv): bands of 30+ teams more than 2 SE out

38 bands with 30+ teams; 4 more than 2 SE from what was said.

| Odds | Window | Band | Teams | Said | Happened | z |
|---|---|---|---|---|---|---|
| division | 2023-25 | 0-0.05 | 183 | 0.008 | 0.038 | +4.4 |
| division | 2023-25 | 0.05-0.15 | 78 | 0.095 | 0.179 | +2.5 |
| playoffs | 2023-25 | 0.05-0.15 | 43 | 0.093 | 0.256 | +3.7 |
| playoffs | 2023-25 | 0.7-0.85 | 41 | 0.775 | 0.585 | -2.9 |

## Player props (data/tracker/props_graded.csv)

8394 graded projections over 3 week(s) (2026-W1, 2026-W2, 2026-W3); made: after the fact, live. Ratio = total scored / total said; tiers are thirds of the projection within each stat. Bias = said minus scored, z on its own spread. Too short a record for a failing check.

| Stat | Rows | Said | Scored | Bias | z | MAE | Ratio | Ratio low tier | Ratio mid | Ratio high |
|---|---|---|---|---|---|---|---|---|---|---|
| def_sacks | 777 | 0.14 | 0.11 | +0.03 | +2.7 | 0.19 | 0.77 | 1.19 | 0.46 | 0.80 |
| def_solo_tackles | 777 | 2.52 | 2.23 | +0.29 | +4.3 | 1.57 | 0.88 | 0.88 | 0.94 | 0.84 |
| def_tackles | 777 | 4.56 | 4.06 | +0.51 | +4.8 | 2.41 | 0.89 | 0.87 | 0.93 | 0.87 |
| field_goals | 96 | 1.67 | 1.60 | +0.07 | +0.5 | 1.02 | 0.96 | 1.23 | 0.91 | 0.75 |
| kick_points | 96 | 7.20 | 7.04 | +0.16 | +0.4 | 3.10 | 0.98 | 1.06 | 0.96 | 0.91 |
| pass_attempts | 93 | 33.69 | 31.27 | +2.42 | +2.1 | 8.14 | 0.93 | 0.90 | 0.88 | 0.99 |
| pass_completions | 93 | 20.58 | 19.32 | +1.26 | +1.8 | 5.25 | 0.94 | 0.84 | 0.97 | 0.99 |
| pass_int | 93 | 0.72 | 0.55 | +0.17 | +2.4 | 0.60 | 0.77 | 0.57 | 0.84 | 0.87 |
| pass_longest | 93 | 33.16 | 36.05 | -2.89 | -1.6 | 13.44 | 1.09 | 1.14 | 1.08 | 1.05 |
| pass_rush_yards | 93 | 239.03 | 222.62 | +16.41 | +1.8 | 67.54 | 0.93 | 0.93 | 0.88 | 0.97 |
| pass_td | 93 | 1.59 | 1.56 | +0.04 | +0.3 | 0.99 | 0.98 | 1.02 | 0.91 | 1.00 |
| pass_yards | 93 | 223.86 | 205.87 | +17.99 | +2.1 | 64.77 | 0.92 | 0.92 | 0.89 | 0.94 |
| rec_catches | 686 | 2.86 | 2.36 | +0.49 | +6.5 | 1.64 | 0.83 | 0.81 | 0.75 | 0.88 |
| rec_longest | 686 | 13.78 | 13.12 | +0.65 | +1.3 | 9.66 | 0.95 | 0.72 | 0.99 | 1.06 |
| rec_targets | 686 | 4.80 | 3.47 | +1.32 | +12.8 | 2.42 | 0.72 | 0.68 | 0.65 | 0.78 |
| rec_td | 686 | 0.22 | 0.19 | +0.04 | +2.2 | 0.31 | 0.84 | 0.73 | 0.69 | 0.93 |
| rec_yards | 686 | 28.96 | 26.72 | +2.25 | +2.1 | 20.47 | 0.92 | 0.93 | 0.75 | 1.01 |
| rush_attempts | 358 | 7.28 | 5.88 | +1.40 | +6.0 | 3.57 | 0.81 | 0.69 | 0.62 | 0.91 |
| rush_longest | 358 | 9.79 | 8.06 | +1.73 | +4.1 | 6.28 | 0.82 | 0.52 | 0.77 | 1.05 |
| rush_rec_yards | 358 | 38.41 | 34.44 | +3.97 | +2.6 | 22.12 | 0.90 | 0.85 | 0.77 | 0.96 |
| rush_td | 358 | 0.23 | 0.19 | +0.04 | +1.7 | 0.31 | 0.82 | 0.93 | 0.51 | 0.93 |
| rush_yards | 358 | 27.37 | 25.32 | +2.06 | +1.7 | 17.63 | 0.92 | 0.56 | 0.79 | 1.05 |

Result: PASS (home win: 0 bucket(s) out, cover: 0 bucket(s) out, over: 0 bucket(s) out)
