# Calibration audit, 2026-10-09 15:47 UTC

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

p_home_cal = logistic(a + b x logit(p_home)), picks.home_calibration: fit on every regular-season game from 2015 to the season before the one priced, ties dropped (walk-forward; each season below is scored with the fit in force for it, the identity under 500 games, so 2017 is the first season scored). Today's fit on 2015 to 2025: a -0.122, b 1.192 on 2885 games (b = 1 and a = 0 would be p_home itself): 35% raw reads 29.7%, 45% raw reads 41.1%, 55% raw reads 52.9%, 65% raw reads 64.9%, 75% raw reads 76.6%. Ties count half. The season simulation (season.py) still reads the raw chance.

**2015-18** (2017 to 2018 scored): 512 games, said 0.565 home, happened 0.584. Against the moneyline (511 games): Brier model 0.2076, line 0.2048; log loss model 0.6043, line 0.5993.

| Bucket | Games | Said | Happened | z |
|---|---|---|---|---|
| [0.2, 0.3) | 33 | 0.258 | 0.242 | -0.2 |
| [0.3, 0.4) | 59 | 0.352 | 0.297 | -0.9 |
| [0.4, 0.5) | 84 | 0.453 | 0.482 | +0.5 |
| [0.5, 0.6) | 106 | 0.556 | 0.613 | +1.2 |
| [0.6, 0.7) | 105 | 0.647 | 0.657 | +0.2 |
| [0.7, 0.8) | 82 | 0.746 | 0.780 | +0.7 |
| [0.8, 0.9) | 32 | 0.839 | 0.844 | +0.1 |

**2019-22** (2019 to 2022 scored): 1055 games, said 0.544 home, happened 0.524. Against the moneyline (1055 games): Brier model 0.2165, line 0.2099; log loss model 0.6253, line 0.6094.

| Bucket | Games | Said | Happened | z |
|---|---|---|---|---|
| [0.1, 0.2) | 36 | 0.161 | 0.333 | +2.8 |
| [0.2, 0.3) | 78 | 0.253 | 0.199 | -1.1 |
| [0.3, 0.4) | 144 | 0.351 | 0.351 | -0.0 |
| [0.4, 0.5) | 178 | 0.451 | 0.396 | -1.5 |
| [0.5, 0.6) | 187 | 0.552 | 0.524 | -0.8 |
| [0.6, 0.7) | 167 | 0.652 | 0.635 | -0.5 |
| [0.7, 0.8) | 163 | 0.749 | 0.706 | -1.3 |
| [0.8, 0.9) | 72 | 0.837 | 0.875 | +0.9 |

**2023-25** (2023 to 2025 scored): 816 games, said 0.536 home, happened 0.542. Against the moneyline (816 games): Brier model 0.2150, line 0.2101; log loss model 0.6202, line 0.6083.

| Bucket | Games | Said | Happened | z |
|---|---|---|---|---|
| [0.2, 0.3) | 62 | 0.257 | 0.282 | +0.5 |
| [0.3, 0.4) | 125 | 0.358 | 0.360 | +0.0 |
| [0.4, 0.5) | 141 | 0.452 | 0.355 | -2.3 |
| [0.5, 0.6) | 158 | 0.552 | 0.582 | +0.8 |
| [0.6, 0.7) | 135 | 0.651 | 0.726 | +1.8 |
| [0.7, 0.8) | 102 | 0.744 | 0.755 | +0.2 |
| [0.8, 0.9) | 60 | 0.847 | 0.783 | -1.4 |

**2015-25** (2017 to 2025 scored): 2383 games, said 0.546 home, happened 0.543. Against the moneyline (2382 games): Brier model 0.2141, line 0.2089; log loss model 0.6190, line 0.6069.

| Bucket | Games | Said | Happened | z |
|---|---|---|---|---|
| [0.1, 0.2) | 64 | 0.161 | 0.328 | +3.7 |
| [0.2, 0.3) | 173 | 0.255 | 0.237 | -0.6 |
| [0.3, 0.4) | 328 | 0.354 | 0.345 | -0.4 |
| [0.4, 0.5) | 403 | 0.452 | 0.400 | -2.1 |
| [0.5, 0.6) | 451 | 0.553 | 0.565 | +0.5 |
| [0.6, 0.7) | 407 | 0.651 | 0.671 | +0.9 |
| [0.7, 0.8) | 347 | 0.747 | 0.738 | -0.4 |
| [0.8, 0.9) | 164 | 0.841 | 0.835 | -0.2 |
| [0.9, 1.0) | 39 | 0.924 | 0.923 | -0.0 |

### The mapping against the raw chance: log loss and Brier (lower is better), and the mapped 0.4-0.5 and 0.3-0.4 buckets

| Window | Games | Log loss p_home | Log loss p_home_cal | Brier p_home | Brier p_home_cal | Mapped 0.4-0.5 said / happened | Mapped 0.3-0.4 said / happened |
|---|---|---|---|---|---|---|---|
| 2016-18 (2017 to 2018 scored) | 512 | 0.60639 | 0.60363 | 0.20831 | 0.20731 | 0.453 / 0.482 (n 84) | 0.352 / 0.297 (n 59) |
| 2019-22 (2019 to 2022 scored) | 1055 | 0.62661 | 0.62527 | 0.21752 | 0.21651 | 0.451 / 0.396 (n 178) | 0.351 / 0.351 (n 144) |
| 2020-22 (2020 to 2022 scored) | 799 | 0.62831 | 0.62721 | 0.21814 | 0.21706 | 0.451 / 0.409 (n 138) | 0.352 / 0.350 (n 113) |
| 2023-25 (2023 to 2025 scored) | 816 | 0.62155 | 0.62022 | 0.21587 | 0.21503 | 0.452 / 0.355 (n 141) | 0.358 / 0.360 (n 125) |

### Raw home win chance (p_home, the season simulation's chance) by decile: the record, not a check

Ties count half.

**2015-18**: 1024 games, said 0.572 home, happened 0.571. Against the moneyline (1023 games): Brier model 0.2149, line 0.2146; log loss model 0.6205, line 0.6201.

| Bucket | Games | Said | Happened | z |
|---|---|---|---|---|
| [0.2, 0.3) | 31 | 0.261 | 0.226 | -0.4 |
| [0.3, 0.4) | 109 | 0.357 | 0.289 | -1.5 |
| [0.4, 0.5) | 179 | 0.457 | 0.439 | -0.5 |
| [0.5, 0.6) | 246 | 0.554 | 0.559 | +0.2 |
| [0.6, 0.7) | 245 | 0.646 | 0.659 | +0.4 |
| [0.7, 0.8) | 161 | 0.741 | 0.770 | +0.8 |
| [0.8, 0.9) | 46 | 0.834 | 0.870 | +0.6 |

**2019-22**: 1055 games, said 0.559 home, happened 0.524. Against the moneyline (1055 games): Brier model 0.2175, line 0.2099; log loss model 0.6266, line 0.6094.

| Bucket | Games | Said | Happened | z |
|---|---|---|---|---|
| [0.2, 0.3) | 54 | 0.263 | 0.278 | +0.3 |
| [0.3, 0.4) | 116 | 0.358 | 0.284 | -1.7 |
| [0.4, 0.5) | 205 | 0.454 | 0.390 | -1.8 |
| [0.5, 0.6) | 226 | 0.551 | 0.493 | -1.8 |
| [0.6, 0.7) | 217 | 0.650 | 0.622 | -0.9 |
| [0.7, 0.8) | 168 | 0.747 | 0.738 | -0.3 |
| [0.8, 0.9) | 47 | 0.844 | 0.894 | +0.9 |

**2023-25**: 816 games, said 0.555 home, happened 0.542. Against the moneyline (816 games): Brier model 0.2159, line 0.2101; log loss model 0.6216, line 0.6083.

| Bucket | Games | Said | Happened | z |
|---|---|---|---|---|
| [0.2, 0.3) | 32 | 0.264 | 0.312 | +0.6 |
| [0.3, 0.4) | 96 | 0.353 | 0.370 | +0.3 |
| [0.4, 0.5) | 173 | 0.452 | 0.335 | -3.1 |
| [0.5, 0.6) | 176 | 0.552 | 0.528 | -0.6 |
| [0.6, 0.7) | 173 | 0.649 | 0.717 | +1.9 |
| [0.7, 0.8) | 102 | 0.744 | 0.725 | -0.4 |
| [0.8, 0.9) | 52 | 0.839 | 0.865 | +0.5 |

**2015-25**: 2895 games, said 0.563 home, happened 0.546. Against the moneyline (2894 games): Brier model 0.2161, line 0.2116; log loss model 0.6230, line 0.6129.

| Bucket | Games | Said | Happened | z |
|---|---|---|---|---|
| [0.2, 0.3) | 117 | 0.263 | 0.274 | +0.3 |
| [0.3, 0.4) | 321 | 0.356 | 0.312 | -1.7 |
| [0.4, 0.5) | 557 | 0.454 | 0.389 | -3.1 |
| [0.5, 0.6) | 648 | 0.552 | 0.528 | -1.3 |
| [0.6, 0.7) | 635 | 0.648 | 0.662 | +0.7 |
| [0.7, 0.8) | 431 | 0.744 | 0.747 | +0.1 |
| [0.8, 0.9) | 145 | 0.839 | 0.876 | +1.2 |

## Spread cover: the model's side, by size of the edge

Calibrated cover chance = picks.calibration's logistic on |edge| capped at 7, fit on 2019 to 2025 (intercept -0.029, slope 0.0502 a point): 49.3% at 0, 51.8% at 2, 54.3% at 4, 56.7% at 6, 58.0% at 7. Raw = the bell curve's own cover chance (p_cover_home; picks file only). Pushes dropped.

**2019-22**: 1031 games.

| Edge | Games | Said (calibrated) | Said (raw) | Covered | z (calibrated) | z (raw) |
|---|---|---|---|---|---|---|
| 0-1 | 335 | 0.499 | 0.516 | 0.537 | +1.4 | +0.8 |
| 1-2 | 251 | 0.511 | 0.547 | 0.514 | +0.1 | -1.1 |
| 2-3 | 185 | 0.523 | 0.583 | 0.514 | -0.3 | -1.9 |
| 3-4 | 123 | 0.537 | 0.612 | 0.496 | -0.9 | -2.6 |
| 4-5 | 63 | 0.548 | 0.637 | 0.603 | +0.9 | -0.6 |
| 5-6 | 42 | 0.561 | 0.672 | 0.643 | +1.1 | -0.4 |
| 6+ | 32 | 0.576 | 0.727 | 0.531 | -0.5 | -2.5 |

**2023-25**: 797 games.

| Edge | Games | Said (calibrated) | Said (raw) | Covered | z (calibrated) | z (raw) |
|---|---|---|---|---|---|---|
| 0-1 | 254 | 0.499 | 0.519 | 0.457 | -1.3 | -2.0 |
| 1-2 | 234 | 0.511 | 0.546 | 0.504 | -0.2 | -1.3 |
| 2-3 | 156 | 0.524 | 0.571 | 0.506 | -0.4 | -1.6 |
| 3-4 | 89 | 0.535 | 0.600 | 0.494 | -0.8 | -2.0 |
| 4-5 | 36 | 0.549 | 0.639 | 0.694 | +1.8 | +0.7 |
| 5-6 | 11 | 0.560 | 0.657 | 0.545 | -0.1 | -0.8 |
| 6+ | 17 | 0.575 | 0.714 | 0.647 | +0.6 | -0.6 |

**2019-25**: 1828 games.

| Edge | Games | Said (calibrated) | Said (raw) | Covered | z (calibrated) | z (raw) |
|---|---|---|---|---|---|---|
| 0-1 | 589 | 0.499 | 0.517 | 0.503 | +0.2 | -0.7 |
| 1-2 | 485 | 0.511 | 0.547 | 0.509 | -0.1 | -1.7 |
| 2-3 | 341 | 0.523 | 0.577 | 0.510 | -0.5 | -2.5 |
| 3-4 | 212 | 0.536 | 0.607 | 0.495 | -1.2 | -3.3 |
| 4-5 | 99 | 0.548 | 0.638 | 0.636 | +1.8 | -0.0 |
| 5-6 | 53 | 0.561 | 0.669 | 0.623 | +0.9 | -0.7 |
| 6+ | 49 | 0.576 | 0.722 | 0.571 | -0.1 | -2.4 |

**2015-18** (before the calibration window; not checked): 994 games.

| Edge | Games | Said (calibrated) | Said (raw) | Covered | z (calibrated) | z (raw) |
|---|---|---|---|---|---|---|
| 0-1 | 335 | 0.499 | 0.516 | 0.481 | -0.7 | -1.3 |
| 1-2 | 273 | 0.511 | 0.548 | 0.491 | -0.7 | -1.9 |
| 2-3 | 152 | 0.523 | 0.579 | 0.553 | +0.7 | -0.7 |
| 3-4 | 113 | 0.535 | 0.609 | 0.496 | -0.8 | -2.5 |
| 4-5 | 66 | 0.548 | 0.634 | 0.530 | -0.3 | -1.8 |
| 5-6 | 33 | 0.561 | 0.675 | 0.697 | +1.6 | +0.3 |
| 6+ | 22 | 0.574 | 0.712 | 0.409 | -1.6 | -3.1 |

### Biases: the model's side by situation (said = calibrated chance; flags = edge of 4+)

| Window | Group | Games | Said | Covered | z | Flags | Flags covered |
|---|---|---|---|---|---|---|---|
| 2015-18 | away side | 456 | 0.516 | 0.518 | +0.1 | 52 | 0.750 |
| 2015-18 | home side | 538 | 0.518 | 0.494 | -1.1 | 69 | 0.406 |
| 2015-18 | underdog | 620 | 0.519 | 0.510 | -0.5 | 89 | 0.584 |
| 2015-18 | favorite | 370 | 0.513 | 0.497 | -0.6 | 32 | 0.469 |
| 2015-18 | high total | 294 | 0.517 | 0.510 | -0.2 | 36 | 0.472 |
| 2015-18 | mid total | 326 | 0.516 | 0.509 | -0.2 | 38 | 0.500 |
| 2015-18 | low total | 374 | 0.518 | 0.497 | -0.8 | 47 | 0.660 |
| 2015-18 | primetime | 200 | 0.519 | 0.495 | -0.7 | 26 | 0.615 |
| 2015-18 | daytime | 794 | 0.517 | 0.508 | -0.5 | 95 | 0.537 |
| 2015-18 | non-divisional | 620 | 0.517 | 0.505 | -0.6 | 68 | 0.559 |
| 2015-18 | divisional | 374 | 0.518 | 0.505 | -0.5 | 53 | 0.547 |
| 2019-22 | home side | 577 | 0.520 | 0.506 | -0.7 | 78 | 0.564 |
| 2019-22 | away side | 454 | 0.517 | 0.562 | +1.9 | 59 | 0.644 |
| 2019-22 | favorite | 354 | 0.512 | 0.480 | -1.2 | 18 | 0.444 |
| 2019-22 | underdog | 677 | 0.522 | 0.557 | +1.8 | 119 | 0.622 |
| 2019-22 | mid total | 330 | 0.520 | 0.515 | -0.2 | 43 | 0.651 |
| 2019-22 | high total | 377 | 0.515 | 0.533 | +0.7 | 37 | 0.595 |
| 2019-22 | low total | 324 | 0.521 | 0.543 | +0.8 | 57 | 0.561 |
| 2019-22 | primetime | 208 | 0.518 | 0.505 | -0.4 | 23 | 0.522 |
| 2019-22 | daytime | 823 | 0.519 | 0.537 | +1.0 | 114 | 0.614 |
| 2019-22 | divisional | 376 | 0.520 | 0.545 | +1.0 | 53 | 0.547 |
| 2019-22 | non-divisional | 655 | 0.518 | 0.522 | +0.2 | 84 | 0.631 |
| 2023-25 | home side | 468 | 0.517 | 0.502 | -0.6 | 41 | 0.659 |
| 2023-25 | away side | 329 | 0.515 | 0.498 | -0.6 | 23 | 0.652 |
| 2023-25 | favorite | 311 | 0.514 | 0.521 | +0.3 | 15 | 0.667 |
| 2023-25 | underdog | 486 | 0.518 | 0.488 | -1.3 | 49 | 0.653 |
| 2023-25 | high total | 201 | 0.516 | 0.398 | -3.3 | 18 | 0.556 |
| 2023-25 | low total | 379 | 0.517 | 0.538 | +0.8 | 38 | 0.658 |
| 2023-25 | mid total | 217 | 0.514 | 0.530 | +0.5 | 8 | 0.875 |
| 2023-25 | primetime | 170 | 0.515 | 0.453 | -1.6 | 14 | 0.643 |
| 2023-25 | daytime | 627 | 0.516 | 0.514 | -0.1 | 50 | 0.660 |
| 2023-25 | non-divisional | 514 | 0.516 | 0.502 | -0.6 | 39 | 0.641 |
| 2023-25 | divisional | 283 | 0.517 | 0.498 | -0.6 | 25 | 0.680 |

## Totals: calibrated over chance (p_over_cal, the cards' figure) by decile

p_over_cal = logistic(a + b x logit(p_over_emp)), picks.over_calibration: fit on every regular-season game from 2015 to the season before the one priced (walk-forward; each season below is scored with the fit in force for it, so 2016 is the first season scored). Today's fit on 2015 to 2025: a -0.041, b 0.420 on 2869 games (b = 1 and a = 0 would be p_over_emp itself): 35% raw reads 42.5%, 45% raw reads 46.9%, 55% raw reads 51.1%, 65% raw reads 55.4%. Pushes dropped. The totals flag (an under at 55%+) stays on the raw chance.

**2015-18** (2016 to 2018 scored): 764 games, said 0.489 over, happened 0.488.

| Bucket | Games | Said | Happened | z |
|---|---|---|---|---|
| [0.4, 0.5) | 524 | 0.480 | 0.502 | +1.0 |
| [0.5, 0.6) | 239 | 0.509 | 0.460 | -1.5 |

**2019-22** (2019 to 2022 scored): 1043 games, said 0.487 over, happened 0.477.

| Bucket | Games | Said | Happened | z |
|---|---|---|---|---|
| [0.4, 0.5) | 769 | 0.477 | 0.463 | -0.8 |
| [0.5, 0.6) | 274 | 0.516 | 0.518 | +0.1 |

**2023-25** (2023 to 2025 scored): 811 games, said 0.489 over, happened 0.507.

| Bucket | Games | Said | Happened | z |
|---|---|---|---|---|
| [0.4, 0.5) | 518 | 0.473 | 0.483 | +0.4 |
| [0.5, 0.6) | 290 | 0.520 | 0.552 | +1.1 |

**2015-25** (2016 to 2025 scored): 2618 games, said 0.488 over, happened 0.490.

| Bucket | Games | Said | Happened | z |
|---|---|---|---|---|
| [0.4, 0.5) | 1811 | 0.477 | 0.480 | +0.3 |
| [0.5, 0.6) | 803 | 0.515 | 0.513 | -0.1 |

### The mapping against the raw chance: log loss and Brier (lower is better), and the mapped 0.5-0.6 and 0.4-0.5 buckets

| Window | Games | Log loss p_over_emp | Log loss p_over_cal | Brier p_over_emp | Brier p_over_cal | Mapped 0.5-0.6 said / happened | Mapped 0.4-0.5 said / happened |
|---|---|---|---|---|---|---|---|
| 2016-18 | 764 | 0.70303 | 0.69461 | 0.25471 | 0.25073 | 0.509 / 0.460 (n 239) | 0.480 / 0.502 (n 524) |
| 2019-22 | 1043 | 0.69193 | 0.68956 | 0.24928 | 0.24821 | 0.516 / 0.518 (n 274) | 0.477 / 0.463 (n 769) |
| 2020-22 | 788 | 0.69288 | 0.68892 | 0.24971 | 0.24789 | 0.517 / 0.506 (n 247) | 0.474 / 0.453 (n 541) |
| 2023-25 | 811 | 0.69095 | 0.68993 | 0.24890 | 0.24840 | 0.520 / 0.552 (n 290) | 0.473 / 0.483 (n 518) |

### Raw over chance (p_over_emp, the totals flag's chance) by decile: the record, not a check

Pushes dropped. p_over (the normal curve, picks file only) is quoted for reference.

**2015-18**: 1015 games, said 0.497 over (normal curve 0.511), happened 0.486.

| Bucket | Games | Said | Happened | z |
|---|---|---|---|---|
| [0.3, 0.4) | 109 | 0.366 | 0.431 | +1.4 |
| [0.4, 0.5) | 397 | 0.459 | 0.491 | +1.3 |
| [0.5, 0.6) | 413 | 0.545 | 0.511 | -1.4 |
| [0.6, 0.7) | 78 | 0.632 | 0.410 | -4.1 |

**2019-22**: 1043 games, said 0.485 over (normal curve 0.498), happened 0.477.

| Bucket | Games | Said | Happened | z |
|---|---|---|---|---|
| [0.3, 0.4) | 140 | 0.361 | 0.436 | +1.8 |
| [0.4, 0.5) | 393 | 0.457 | 0.463 | +0.2 |
| [0.5, 0.6) | 400 | 0.541 | 0.497 | -1.7 |
| [0.6, 0.7) | 81 | 0.632 | 0.580 | -1.0 |

**2023-25**: 811 games, said 0.514 over (normal curve 0.533), happened 0.507.

| Bucket | Games | Said | Happened | z |
|---|---|---|---|---|
| [0.3, 0.4) | 61 | 0.367 | 0.426 | +1.0 |
| [0.4, 0.5) | 260 | 0.461 | 0.458 | -0.1 |
| [0.5, 0.6) | 364 | 0.543 | 0.536 | -0.3 |
| [0.6, 0.7) | 116 | 0.632 | 0.560 | -1.6 |

**2015-25**: 2869 games, said 0.498 over (normal curve 0.512), happened 0.489.

| Bucket | Games | Said | Happened | z |
|---|---|---|---|---|
| [0.2, 0.3) | 45 | 0.271 | 0.356 | +1.3 |
| [0.3, 0.4) | 310 | 0.364 | 0.432 | +2.5 |
| [0.4, 0.5) | 1050 | 0.459 | 0.472 | +0.9 |
| [0.5, 0.6) | 1177 | 0.543 | 0.514 | -2.0 |
| [0.6, 0.7) | 275 | 0.632 | 0.524 | -3.7 |

### Model total against the actual total, by third of the line (bias = said minus happened)

| Window | Third | Games | Line | Model | Actual | Bias model | Bias line | MAE model | MAE line |
|---|---|---|---|---|---|---|---|---|---|
| 2015-18 | low | 384 | 41.3 | 42.9 | 41.5 | +1.42 | -0.17 | 10.56 | 10.46 |
| 2015-18 | mid | 336 | 45.4 | 45.7 | 44.6 | +1.06 | +0.77 | 10.31 | 10.12 |
| 2015-18 | high | 304 | 50.3 | 49.3 | 51.0 | -1.71 | -0.64 | 11.39 | 11.14 |
| 2019-22 | low | 335 | 41.1 | 42.3 | 41.0 | +1.23 | +0.07 | 10.03 | 10.10 |
| 2019-22 | mid | 337 | 45.5 | 45.7 | 46.2 | -0.59 | -0.76 | 10.95 | 11.01 |
| 2019-22 | high | 383 | 50.5 | 49.1 | 50.7 | -1.55 | -0.14 | 10.61 | 10.52 |
| 2023-25 | low | 391 | 40.5 | 42.3 | 41.9 | +0.41 | -1.41 | 9.94 | 10.13 |
| 2023-25 | mid | 221 | 45.4 | 46.6 | 46.0 | +0.57 | -0.67 | 9.88 | 9.71 |
| 2023-25 | high | 204 | 49.4 | 49.0 | 50.3 | -1.24 | -0.87 | 10.66 | 10.55 |

## Margin scale: stated sigma against the realised miss, and how much of it the 50 / 80 / 95% intervals hold

| Window | Games | Sigma stated | Realised SD | Mean miss (result minus model) | Line's SD | 50% holds | 80% holds | 95% holds |
|---|---|---|---|---|---|---|---|---|
| 2015-18 | 1024 | 13.19 | 12.90 | -0.19 | 12.75 | 0.554 | 0.819 | 0.936 |
| 2019-22 | 1055 | 13.07 | 12.89 | -0.97 | 12.76 | 0.529 | 0.803 | 0.945 |
| 2023-25 | 816 | 13.00 | 12.81 | +0.23 | 12.64 | 0.548 | 0.803 | 0.950 |

## Team points by tier of the expected score (bias = said minus scored; z on the scores' own spread)

| Window | Tier | Sides | Said | Scored | Bias | z |
|---|---|---|---|---|---|---|
| 2015-18 | under 18 | 170 | 16.44 | 17.02 | -0.58 | -0.8 |
| 2015-18 | 18-21 | 438 | 19.67 | 19.01 | +0.66 | +1.5 |
| 2015-18 | 21-24 | 664 | 22.52 | 22.56 | -0.04 | -0.1 |
| 2015-18 | 24-27 | 546 | 25.35 | 25.05 | +0.30 | +0.7 |
| 2015-18 | 27+ | 230 | 28.66 | 28.40 | +0.27 | +0.4 |
| 2019-22 | under 18 | 208 | 16.16 | 16.50 | -0.34 | -0.6 |
| 2019-22 | 18-21 | 420 | 19.64 | 20.04 | -0.40 | -0.9 |
| 2019-22 | 21-24 | 648 | 22.60 | 22.51 | +0.09 | +0.2 |
| 2019-22 | 24-27 | 550 | 25.37 | 25.54 | -0.16 | -0.4 |
| 2019-22 | 27+ | 284 | 28.68 | 29.08 | -0.40 | -0.7 |
| 2023-25 | under 18 | 199 | 16.32 | 16.02 | +0.31 | +0.5 |
| 2023-25 | 18-21 | 335 | 19.73 | 19.80 | -0.07 | -0.1 |
| 2023-25 | 21-24 | 512 | 22.55 | 21.89 | +0.66 | +1.7 |
| 2023-25 | 24-27 | 402 | 25.30 | 25.41 | -0.11 | -0.2 |
| 2023-25 | 27+ | 184 | 28.69 | 30.34 | -1.66 | -2.3 |

## Season odds (reports/season_calibration.csv): bands of 30+ teams more than 2 SE out

38 bands with 30+ teams; 3 more than 2 SE from what was said.

| Odds | Window | Band | Teams | Said | Happened | z |
|---|---|---|---|---|---|---|
| division | 2023-25 | 0-0.05 | 186 | 0.009 | 0.048 | +5.7 |
| playoffs | 2023-25 | 0.05-0.15 | 43 | 0.091 | 0.256 | +3.7 |
| playoffs | 2023-25 | 0.7-0.85 | 40 | 0.774 | 0.600 | -2.6 |

## Player props (data/tracker/props_graded.csv)

11275 graded projections over 4 week(s) (2026-W1, 2026-W2, 2026-W3, 2026-W4); made: after the fact, live. Ratio = total scored / total said; tiers are thirds of the projection within each stat. Bias = said minus scored, z on its own spread. Too short a record for a failing check.

| Stat | Rows | Said | Scored | Bias | z | MAE | Ratio | Ratio low tier | Ratio mid | Ratio high |
|---|---|---|---|---|---|---|---|---|---|---|
| def_sacks | 1033 | 0.13 | 0.10 | +0.03 | +3.2 | 0.19 | 0.76 | 1.18 | 0.64 | 0.74 |
| def_solo_tackles | 1033 | 2.57 | 2.27 | +0.29 | +4.8 | 1.59 | 0.89 | 0.89 | 0.93 | 0.86 |
| def_tackles | 1033 | 4.65 | 4.12 | +0.53 | +5.7 | 2.42 | 0.89 | 0.89 | 0.88 | 0.88 |
| field_goals | 128 | 1.67 | 1.66 | +0.02 | +0.2 | 1.01 | 0.99 | 1.12 | 0.98 | 0.87 |
| kick_points | 128 | 7.23 | 7.17 | +0.06 | +0.2 | 3.02 | 0.99 | 1.01 | 0.98 | 0.98 |
| pass_attempts | 125 | 33.73 | 31.18 | +2.54 | +2.4 | 8.67 | 0.92 | 0.90 | 0.85 | 1.01 |
| pass_completions | 125 | 20.88 | 19.43 | +1.45 | +2.2 | 5.66 | 0.93 | 0.84 | 0.91 | 1.03 |
| pass_int | 125 | 0.72 | 0.58 | +0.15 | +2.3 | 0.64 | 0.80 | 0.56 | 1.00 | 0.82 |
| pass_longest | 125 | 33.17 | 35.70 | -2.52 | -1.6 | 13.43 | 1.08 | 1.10 | 1.00 | 1.13 |
| pass_rush_yards | 125 | 240.08 | 225.04 | +15.04 | +1.8 | 71.97 | 0.94 | 0.94 | 0.89 | 0.97 |
| pass_td | 125 | 1.59 | 1.49 | +0.10 | +1.0 | 0.94 | 0.93 | 1.05 | 0.86 | 0.92 |
| pass_yards | 125 | 225.15 | 210.10 | +15.05 | +1.9 | 68.86 | 0.93 | 0.92 | 0.92 | 0.96 |
| rec_catches | 927 | 2.84 | 2.41 | +0.43 | +6.3 | 1.65 | 0.85 | 0.78 | 0.79 | 0.90 |
| rec_longest | 927 | 13.78 | 13.10 | +0.68 | +1.6 | 9.80 | 0.95 | 0.70 | 1.00 | 1.05 |
| rec_targets | 927 | 4.75 | 3.55 | +1.20 | +12.9 | 2.42 | 0.75 | 0.69 | 0.70 | 0.79 |
| rec_td | 927 | 0.22 | 0.18 | +0.04 | +2.9 | 0.31 | 0.81 | 0.73 | 0.79 | 0.84 |
| rec_yards | 927 | 28.31 | 27.21 | +1.10 | +1.2 | 20.78 | 0.96 | 0.94 | 0.86 | 1.01 |
| rush_attempts | 482 | 7.20 | 5.95 | +1.25 | +6.3 | 3.44 | 0.83 | 0.71 | 0.65 | 0.92 |
| rush_longest | 482 | 9.72 | 8.32 | +1.39 | +3.5 | 6.51 | 0.86 | 0.59 | 0.82 | 1.03 |
| rush_rec_yards | 482 | 37.44 | 34.54 | +2.90 | +2.3 | 21.19 | 0.92 | 0.75 | 0.85 | 0.98 |
| rush_td | 482 | 0.22 | 0.22 | +0.01 | +0.3 | 0.32 | 0.97 | 0.88 | 0.75 | 1.08 |
| rush_yards | 482 | 26.94 | 25.24 | +1.70 | +1.6 | 17.14 | 0.94 | 0.60 | 0.81 | 1.05 |

Result: PASS (home win: 0 bucket(s) out, cover: 0 bucket(s) out, over: 0 bucket(s) out)
