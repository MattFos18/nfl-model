# Calibration audit, 2026-09-27 17:29 UTC

Every chance the model states against what happened, regular season, from the committed prediction table (pred_v3) and results (games). Said is the mean stated chance in the bucket, z is how many binomial standard errors the outcome sits from it. A bucket with 150+ games and |z| over 2.5 fails the health check (the three checked tables are the calibrated home win chance, the calibrated cover chance and the calibrated over chance, the figures the cards show); every other table is the audit's record and does not fail. Windows are the backtest's: 2015-18 untouched, 2019-22 tuning, 2023-25 held out. Rebuilt by nflmodel.tie_check on every run.

## Findings (27 Sep 2026 audit; the tables below are today's)

- Over chance: the raw p_over_emp was too far from 50% on both sides, every window (said 63% over, the over came 50%: 2015-25 n 256, z -4.5; said 55%, came 50%: n 1119, z -2.8; said 46%, came 49%: n 1125, z +2.3; the same shape in each window). Cause: the chance is priced as if the model's total were the truth and the line carried nothing, while the line's miss is the model's (MAE 10.5 each). Shipped 27 Sep 2026, a mapping and not a model change: the cards, the takeaways and the report show p_over_cal = logistic(a + b x logit(p_over_emp)) (picks.over_calibration), fit walk-forward on every regular-season game from 2015 to the season before the one priced, refit every run (today a -0.040, b 0.389 on 2869 games: 63% raw reads 54%, 55% reads 51%). It scores a better log loss and Brier than the raw chance on 2016-18, 2019-22, 2020-22 and 2023-25 (table below), and the checked over table is now the calibrated one. The totals flag (unders at 55%+) stays on the raw chance, the same monotone mapping, so it is the same rule with the same records; the raw table stays below for the record.
- Home win chance (p_home): the home side won less often than said when the model had it a slight underdog. Said 45%, won 39% in 2015-25 (n 556, z -3.0; 2023-25 alone n 180, 45% said, 34% won, z -3.0); said 35%, won 30% (n 327, z -2.0); the line was high in the same games but less (43% implied); overall 2019-22 said 56.0% home and 52.4% happened (z -2.5) while the fitted home coefficient was 2.2 and 1.9 points in 2019 and 2020 against a realised home margin near 0. Cause: one home-field term fit on 2013 on lags the fall in home advantage; a home term that follows recent seasons did not fix the 2023-25 bucket (31 variants, reports/home_field_recency.md), so the model stays. Shipped 27 Sep 2026, a mapping and not a model change: the cards, the friends' report and the picks file show p_home_cal = logistic(a + b x logit(p_home)) (picks.home_calibration), fit walk-forward on every regular-season game from 2015 to the season before the one priced, ties dropped, the identity under 500 games (two seasons: a one-season fit read worse than the raw chance), refit every run (today a -0.123, b 1.191 on 2885 games: 45% raw reads 41%, 35% reads 30%, 65% reads 65%). It scores a better log loss and Brier than the raw chance on 2016-18, 2019-22, 2020-22 and 2023-25 (table below; a richer form with an intercept shift for the home side being the model's underdog was worse than the raw chance on 2016-18 and is not adopted), and the checked home table is now the calibrated one. It does not cure the 2023-25 slight-underdog bucket: it moves a third of those games down into 0.3-0.4, where they sit within noise, and the 147 left say 45% and won 35% (z -2.5), three games under the check's 150-game floor; the stretch (b over 1) also reads the few 10-20% home sides low (2016-25 n 61, said 16%, won 31%, under the floor). The season simulation (season.py, the season file's chance per game) still reads the raw chance; the raw table stays below for the record.
- Calibrated cover chance (the cards' cover odds, picks.calibration): honest within noise in every band, 2019-25. It is nearly flat (50% at a 0-point edge to 56% at 7) and conservative on the flags: 4-5 point edges said 54% and covered 64% (n 107, z +2.0) while 2-4 point edges covered 48% (n 546). The raw bell-curve chance (p_cover_home, picks file only) runs 8 to 15 points hot at every edge (3-4 points: said 61%, covered 47%, z -3.7), as documented.
- Cover biases (2019-25, all games at the model's side): home or away side, favourite or underdog, primetime and divisional games are all within 2 SE in every window. One bucket is not: in 2023-25 the model's side covered 41% in the highest third of totals (n 201, z -3.0); 2019-22 was 54% and 2015-18 51% in the same third, so it is not a standing flaw.
- Margin scale: the stated sigma (13.0 to 13.2) is a shade wide against the realised spread of result minus model spread (12.8 to 12.9): the 50% interval holds 53 to 55%, the 80% 80 to 82%, the 95% 94 to 95%.
- Team points by tier: within noise except the top tier in 2023-25, where sides expected to score 27+ scored 30.7 against 28.6 said (n 172, z -2.9); 2015-18 and 2019-22 show no such gap.
- Season odds (reports/season_calibration.csv): 2019-22 is within noise in every band; 2023-25 is overconfident at both ends (division chances said 1% came 4%, n 183, z +4.5; playoff chances said 77% came 59%, n 41, z -2.9), as the docs already say.
- Player props (data/tracker/props_graded.csv, two weeks, projections made after the fact): every volume stat is projected high. Targets 4.9 said, 3.4 happened (ratio 0.69, z 12); carries 0.78; catches 0.80; receiving TDs 0.78 (101 said, 79 scored); interceptions 0.70; tackles 0.88. A quarter of the receiving rows (22.5%) are players who saw no target; without them targets are still 18% high and receiving TDs 7.5% high. TD chances read as 1 - exp(-projection) overstate the anytime rate: a 0.15-0.25 TD projection scored in 8.6% of games against 17.9% implied (n 128, z -2.7). Cause: the volume shares do not fall enough for depth players, and no availability check drops players who will not play. Two weeks is too few for a check; reviewed here until the record is long enough.

## Game winner: calibrated home win chance (p_home_cal, the cards' figure) by decile

p_home_cal = logistic(a + b x logit(p_home)), picks.home_calibration: fit on every regular-season game from 2015 to the season before the one priced, ties dropped (walk-forward; each season below is scored with the fit in force for it, the identity under 500 games, so 2017 is the first season scored). Today's fit on 2015 to 2025: a -0.123, b 1.191 on 2885 games (b = 1 and a = 0 would be p_home itself): 35% raw reads 29.7%, 45% raw reads 41.1%, 55% raw reads 52.9%, 65% raw reads 64.9%, 75% raw reads 76.6%. Ties count half. The season simulation (season.py) still reads the raw chance.

**2015-18** (2017 to 2018 scored): 512 games, said 0.566 home, happened 0.584. Against the moneyline (511 games): Brier model 0.2079, line 0.2048; log loss model 0.6054, line 0.5993.

| Bucket | Games | Said | Happened | z |
|---|---|---|---|---|
| [0.2, 0.3) | 34 | 0.260 | 0.206 | -0.7 |
| [0.3, 0.4) | 56 | 0.354 | 0.330 | -0.4 |
| [0.4, 0.5) | 84 | 0.453 | 0.458 | +0.1 |
| [0.5, 0.6) | 110 | 0.555 | 0.573 | +0.4 |
| [0.6, 0.7) | 107 | 0.647 | 0.710 | +1.4 |
| [0.7, 0.8) | 78 | 0.745 | 0.782 | +0.8 |
| [0.8, 0.9) | 33 | 0.837 | 0.818 | -0.3 |

**2019-22** (2019 to 2022 scored): 1055 games, said 0.543 home, happened 0.524. Against the moneyline (1055 games): Brier model 0.2163, line 0.2099; log loss model 0.6248, line 0.6094.

| Bucket | Games | Said | Happened | z |
|---|---|---|---|---|
| [0.1, 0.2) | 35 | 0.159 | 0.314 | +2.5 |
| [0.2, 0.3) | 81 | 0.254 | 0.216 | -0.8 |
| [0.3, 0.4) | 141 | 0.349 | 0.337 | -0.3 |
| [0.4, 0.5) | 179 | 0.450 | 0.405 | -1.2 |
| [0.5, 0.6) | 186 | 0.551 | 0.522 | -0.8 |
| [0.6, 0.7) | 173 | 0.652 | 0.630 | -0.6 |
| [0.7, 0.8) | 159 | 0.751 | 0.711 | -1.2 |
| [0.8, 0.9) | 71 | 0.835 | 0.873 | +0.9 |

**2023-25** (2023 to 2025 scored): 816 games, said 0.535 home, happened 0.542. Against the moneyline (816 games): Brier model 0.2151, line 0.2101; log loss model 0.6205, line 0.6083.

| Bucket | Games | Said | Happened | z |
|---|---|---|---|---|
| [0.2, 0.3) | 66 | 0.254 | 0.295 | +0.8 |
| [0.3, 0.4) | 123 | 0.361 | 0.374 | +0.3 |
| [0.4, 0.5) | 148 | 0.451 | 0.351 | -2.4 |
| [0.5, 0.6) | 151 | 0.552 | 0.576 | +0.6 |
| [0.6, 0.7) | 140 | 0.651 | 0.736 | +2.1 |
| [0.7, 0.8) | 101 | 0.746 | 0.733 | -0.3 |
| [0.8, 0.9) | 59 | 0.849 | 0.814 | -0.7 |

**2015-25** (2017 to 2025 scored): 2383 games, said 0.545 home, happened 0.543. Against the moneyline (2382 games): Brier model 0.2141, line 0.2089; log loss model 0.6192, line 0.6069.

| Bucket | Games | Said | Happened | z |
|---|---|---|---|---|
| [0.1, 0.2) | 60 | 0.159 | 0.317 | +3.4 |
| [0.2, 0.3) | 181 | 0.255 | 0.243 | -0.4 |
| [0.3, 0.4) | 320 | 0.354 | 0.350 | -0.2 |
| [0.4, 0.5) | 411 | 0.451 | 0.397 | -2.2 |
| [0.5, 0.6) | 447 | 0.552 | 0.553 | +0.0 |
| [0.6, 0.7) | 420 | 0.650 | 0.686 | +1.5 |
| [0.7, 0.8) | 338 | 0.748 | 0.734 | -0.6 |
| [0.8, 0.9) | 163 | 0.840 | 0.840 | +0.0 |
| [0.9, 1.0) | 38 | 0.924 | 0.921 | -0.1 |

### The mapping against the raw chance: log loss and Brier (lower is better), and the mapped 0.4-0.5 and 0.3-0.4 buckets

| Window | Games | Log loss p_home | Log loss p_home_cal | Brier p_home | Brier p_home_cal | Mapped 0.4-0.5 said / happened | Mapped 0.3-0.4 said / happened |
|---|---|---|---|---|---|---|---|
| 2016-18 (2017 to 2018 scored) | 512 | 0.60717 | 0.60473 | 0.20854 | 0.20756 | 0.453 / 0.458 (n 84) | 0.354 / 0.330 (n 56) |
| 2019-22 (2019 to 2022 scored) | 1055 | 0.62628 | 0.62480 | 0.21734 | 0.21627 | 0.450 / 0.405 (n 179) | 0.349 / 0.337 (n 141) |
| 2020-22 (2020 to 2022 scored) | 799 | 0.62792 | 0.62674 | 0.21791 | 0.21678 | 0.449 / 0.412 (n 137) | 0.350 / 0.350 (n 110) |
| 2023-25 (2023 to 2025 scored) | 816 | 0.62182 | 0.62047 | 0.21599 | 0.21514 | 0.451 / 0.351 (n 148) | 0.361 / 0.374 (n 123) |

### Raw home win chance (p_home, the season simulation's chance) by decile: the record, not a check

Ties count half.

**2015-18**: 1024 games, said 0.573 home, happened 0.571. Against the moneyline (1023 games): Brier model 0.2152, line 0.2146; log loss model 0.6214, line 0.6201.

| Bucket | Games | Said | Happened | z |
|---|---|---|---|---|
| [0.3, 0.4) | 114 | 0.354 | 0.268 | -1.9 |
| [0.4, 0.5) | 178 | 0.457 | 0.458 | +0.0 |
| [0.5, 0.6) | 246 | 0.554 | 0.539 | -0.5 |
| [0.6, 0.7) | 249 | 0.646 | 0.681 | +1.2 |
| [0.7, 0.8) | 160 | 0.743 | 0.750 | +0.2 |
| [0.8, 0.9) | 44 | 0.833 | 0.864 | +0.5 |

**2019-22**: 1055 games, said 0.560 home, happened 0.524. Against the moneyline (1055 games): Brier model 0.2173, line 0.2099; log loss model 0.6263, line 0.6094.

| Bucket | Games | Said | Happened | z |
|---|---|---|---|---|
| [0.2, 0.3) | 52 | 0.263 | 0.288 | +0.4 |
| [0.3, 0.4) | 126 | 0.359 | 0.286 | -1.7 |
| [0.4, 0.5) | 198 | 0.456 | 0.379 | -2.2 |
| [0.5, 0.6) | 225 | 0.552 | 0.504 | -1.4 |
| [0.6, 0.7) | 216 | 0.651 | 0.625 | -0.8 |
| [0.7, 0.8) | 168 | 0.747 | 0.738 | -0.3 |
| [0.8, 0.9) | 48 | 0.844 | 0.875 | +0.6 |

**2023-25**: 816 games, said 0.555 home, happened 0.542. Against the moneyline (816 games): Brier model 0.2160, line 0.2101; log loss model 0.6218, line 0.6083.

| Bucket | Games | Said | Happened | z |
|---|---|---|---|---|
| [0.2, 0.3) | 34 | 0.264 | 0.324 | +0.8 |
| [0.3, 0.4) | 89 | 0.350 | 0.365 | +0.3 |
| [0.4, 0.5) | 179 | 0.450 | 0.341 | -2.9 |
| [0.5, 0.6) | 182 | 0.551 | 0.527 | -0.6 |
| [0.6, 0.7) | 167 | 0.650 | 0.719 | +1.9 |
| [0.7, 0.8) | 106 | 0.744 | 0.717 | -0.6 |
| [0.8, 0.9) | 49 | 0.840 | 0.878 | +0.7 |

**2015-25**: 2895 games, said 0.563 home, happened 0.546. Against the moneyline (2894 games): Brier model 0.2162, line 0.2116; log loss model 0.6233, line 0.6129.

| Bucket | Games | Said | Happened | z |
|---|---|---|---|---|
| [0.2, 0.3) | 110 | 0.262 | 0.300 | +0.9 |
| [0.3, 0.4) | 329 | 0.355 | 0.301 | -2.0 |
| [0.4, 0.5) | 555 | 0.455 | 0.392 | -3.0 |
| [0.5, 0.6) | 653 | 0.553 | 0.524 | -1.5 |
| [0.6, 0.7) | 632 | 0.648 | 0.672 | +1.2 |
| [0.7, 0.8) | 434 | 0.745 | 0.737 | -0.4 |
| [0.8, 0.9) | 141 | 0.839 | 0.872 | +1.1 |

## Spread cover: the model's side, by size of the edge

Calibrated cover chance = picks.calibration's logistic on |edge| capped at 7, fit on 2019 to 2025 (intercept -0.011, slope 0.0386 a point): 49.7% at 0, 51.7% at 2, 53.6% at 4, 55.5% at 6, 56.5% at 7. Raw = the bell curve's own cover chance (p_cover_home; picks file only). Pushes dropped.

**2019-22**: 1031 games.

| Edge | Games | Said (calibrated) | Said (raw) | Covered | z (calibrated) | z (raw) |
|---|---|---|---|---|---|---|
| 0-1 | 336 | 0.502 | 0.515 | 0.551 | +1.8 | +1.3 |
| 1-2 | 255 | 0.512 | 0.547 | 0.494 | -0.6 | -1.7 |
| 2-3 | 182 | 0.521 | 0.583 | 0.511 | -0.3 | -2.0 |
| 3-4 | 121 | 0.531 | 0.610 | 0.463 | -1.5 | -3.3 |
| 4-5 | 68 | 0.540 | 0.640 | 0.647 | +1.8 | +0.1 |
| 5-6 | 39 | 0.550 | 0.670 | 0.590 | +0.5 | -1.1 |
| 6+ | 30 | 0.562 | 0.723 | 0.533 | -0.3 | -2.3 |

**2023-25**: 797 games.

| Edge | Games | Said (calibrated) | Said (raw) | Covered | z (calibrated) | z (raw) |
|---|---|---|---|---|---|---|
| 0-1 | 257 | 0.502 | 0.520 | 0.467 | -1.1 | -1.7 |
| 1-2 | 230 | 0.511 | 0.546 | 0.539 | +0.8 | -0.2 |
| 2-3 | 160 | 0.521 | 0.571 | 0.463 | -1.5 | -2.8 |
| 3-4 | 80 | 0.530 | 0.600 | 0.487 | -0.8 | -2.1 |
| 4-5 | 39 | 0.540 | 0.638 | 0.615 | +0.9 | -0.3 |
| 5-6 | 15 | 0.550 | 0.664 | 0.600 | +0.4 | -0.5 |
| 6+ | 16 | 0.560 | 0.714 | 0.688 | +1.0 | -0.2 |

**2019-25**: 1828 games.

| Edge | Games | Said (calibrated) | Said (raw) | Covered | z (calibrated) | z (raw) |
|---|---|---|---|---|---|---|
| 0-1 | 593 | 0.502 | 0.518 | 0.514 | +0.6 | -0.2 |
| 1-2 | 485 | 0.512 | 0.547 | 0.515 | +0.2 | -1.4 |
| 2-3 | 342 | 0.521 | 0.577 | 0.488 | -1.2 | -3.3 |
| 3-4 | 201 | 0.531 | 0.606 | 0.473 | -1.6 | -3.9 |
| 4-5 | 107 | 0.540 | 0.639 | 0.636 | +2.0 | -0.1 |
| 5-6 | 54 | 0.550 | 0.669 | 0.593 | +0.6 | -1.2 |
| 6+ | 46 | 0.561 | 0.720 | 0.587 | +0.4 | -2.0 |

**2015-18** (before the calibration window; not checked): 994 games.

| Edge | Games | Said (calibrated) | Said (raw) | Covered | z (calibrated) | z (raw) |
|---|---|---|---|---|---|---|
| 0-1 | 346 | 0.502 | 0.515 | 0.494 | -0.3 | -0.8 |
| 1-2 | 262 | 0.511 | 0.547 | 0.496 | -0.5 | -1.7 |
| 2-3 | 149 | 0.521 | 0.582 | 0.577 | +1.4 | -0.1 |
| 3-4 | 114 | 0.530 | 0.609 | 0.456 | -1.6 | -3.3 |
| 4-5 | 70 | 0.540 | 0.632 | 0.557 | +0.3 | -1.3 |
| 5-6 | 36 | 0.550 | 0.677 | 0.611 | +0.7 | -0.8 |
| 6+ | 17 | 0.561 | 0.720 | 0.412 | -1.2 | -2.8 |

### Biases: the model's side by situation (said = calibrated chance; flags = edge of 4+)

| Window | Group | Games | Said | Covered | z | Flags | Flags covered |
|---|---|---|---|---|---|---|---|
| 2015-18 | away side | 451 | 0.515 | 0.523 | +0.3 | 51 | 0.745 |
| 2015-18 | home side | 543 | 0.517 | 0.499 | -0.8 | 72 | 0.417 |
| 2015-18 | underdog | 621 | 0.518 | 0.514 | -0.2 | 88 | 0.568 |
| 2015-18 | favourite | 369 | 0.513 | 0.504 | -0.3 | 35 | 0.514 |
| 2015-18 | high total | 294 | 0.516 | 0.514 | -0.1 | 32 | 0.500 |
| 2015-18 | mid total | 326 | 0.515 | 0.528 | +0.5 | 39 | 0.538 |
| 2015-18 | low total | 374 | 0.517 | 0.492 | -1.0 | 52 | 0.596 |
| 2015-18 | primetime | 200 | 0.518 | 0.515 | -0.1 | 30 | 0.567 |
| 2015-18 | daytime | 794 | 0.516 | 0.509 | -0.4 | 93 | 0.548 |
| 2015-18 | non-divisional | 620 | 0.516 | 0.506 | -0.5 | 68 | 0.574 |
| 2015-18 | divisional | 374 | 0.517 | 0.516 | -0.0 | 55 | 0.527 |
| 2019-22 | home side | 577 | 0.518 | 0.503 | -0.8 | 78 | 0.577 |
| 2019-22 | away side | 454 | 0.516 | 0.557 | +1.8 | 59 | 0.644 |
| 2019-22 | favourite | 354 | 0.512 | 0.475 | -1.4 | 17 | 0.412 |
| 2019-22 | underdog | 677 | 0.520 | 0.554 | +1.8 | 120 | 0.633 |
| 2019-22 | mid total | 330 | 0.518 | 0.515 | -0.1 | 45 | 0.667 |
| 2019-22 | high total | 377 | 0.515 | 0.538 | +0.9 | 36 | 0.611 |
| 2019-22 | low total | 324 | 0.519 | 0.525 | +0.2 | 56 | 0.554 |
| 2019-22 | primetime | 208 | 0.516 | 0.495 | -0.6 | 24 | 0.500 |
| 2019-22 | daytime | 823 | 0.517 | 0.535 | +1.0 | 113 | 0.628 |
| 2019-22 | divisional | 376 | 0.518 | 0.540 | +0.8 | 54 | 0.574 |
| 2019-22 | non-divisional | 655 | 0.517 | 0.519 | +0.1 | 83 | 0.627 |
| 2023-25 | home side | 464 | 0.516 | 0.504 | -0.5 | 44 | 0.636 |
| 2023-25 | away side | 333 | 0.514 | 0.502 | -0.5 | 26 | 0.615 |
| 2023-25 | favourite | 299 | 0.514 | 0.525 | +0.4 | 15 | 0.667 |
| 2023-25 | underdog | 498 | 0.516 | 0.490 | -1.2 | 55 | 0.618 |
| 2023-25 | high total | 201 | 0.515 | 0.408 | -3.0 | 17 | 0.529 |
| 2023-25 | low total | 379 | 0.517 | 0.528 | +0.4 | 44 | 0.614 |
| 2023-25 | mid total | 217 | 0.514 | 0.548 | +1.0 | 9 | 0.889 |
| 2023-25 | primetime | 170 | 0.515 | 0.447 | -1.8 | 13 | 0.615 |
| 2023-25 | daytime | 627 | 0.515 | 0.518 | +0.1 | 57 | 0.632 |
| 2023-25 | non-divisional | 514 | 0.515 | 0.496 | -0.9 | 45 | 0.622 |
| 2023-25 | divisional | 283 | 0.516 | 0.516 | +0.0 | 25 | 0.640 |

## Totals: calibrated over chance (p_over_cal, the cards' figure) by decile

p_over_cal = logistic(a + b x logit(p_over_emp)), picks.over_calibration: fit on every regular-season game from 2015 to the season before the one priced (walk-forward; each season below is scored with the fit in force for it, so 2016 is the first season scored). Today's fit on 2015 to 2025: a -0.040, b 0.389 on 2869 games (b = 1 and a = 0 would be p_over_emp itself): 35% raw reads 43.0%, 45% raw reads 47.1%, 55% raw reads 51.0%, 65% raw reads 55.0%. Pushes dropped. The totals flag (an under at 55%+) stays on the raw chance.

**2015-18** (2016 to 2018 scored): 764 games, said 0.490 over, happened 0.488.

| Bucket | Games | Said | Happened | z |
|---|---|---|---|---|
| [0.4, 0.5) | 452 | 0.476 | 0.509 | +1.4 |
| [0.5, 0.6) | 298 | 0.516 | 0.466 | -1.7 |

**2019-22** (2019 to 2022 scored): 1043 games, said 0.488 over, happened 0.477.

| Bucket | Games | Said | Happened | z |
|---|---|---|---|---|
| [0.4, 0.5) | 732 | 0.473 | 0.463 | -0.5 |
| [0.5, 0.6) | 310 | 0.521 | 0.513 | -0.3 |

**2023-25** (2023 to 2025 scored): 811 games, said 0.491 over, happened 0.507.

| Bucket | Games | Said | Happened | z |
|---|---|---|---|---|
| [0.4, 0.5) | 488 | 0.473 | 0.484 | +0.5 |
| [0.5, 0.6) | 322 | 0.518 | 0.540 | +0.8 |

**2015-25** (2016 to 2025 scored): 2618 games, said 0.489 over, happened 0.490.

| Bucket | Games | Said | Happened | z |
|---|---|---|---|---|
| [0.4, 0.5) | 1672 | 0.474 | 0.481 | +0.6 |
| [0.5, 0.6) | 930 | 0.519 | 0.508 | -0.7 |

### The mapping against the raw chance: log loss and Brier (lower is better), and the mapped 0.5-0.6 and 0.4-0.5 buckets

| Window | Games | Log loss p_over_emp | Log loss p_over_cal | Brier p_over_emp | Brier p_over_cal | Mapped 0.5-0.6 said / happened | Mapped 0.4-0.5 said / happened |
|---|---|---|---|---|---|---|---|
| 2016-18 | 764 | 0.70305 | 0.69578 | 0.25486 | 0.25134 | 0.516 / 0.466 (n 298) | 0.476 / 0.509 (n 452) |
| 2019-22 | 1043 | 0.69091 | 0.68898 | 0.24888 | 0.24792 | 0.521 / 0.513 (n 310) | 0.473 / 0.463 (n 732) |
| 2020-22 | 788 | 0.68986 | 0.68796 | 0.24839 | 0.24742 | 0.523 / 0.506 (n 263) | 0.471 / 0.452 (n 524) |
| 2023-25 | 811 | 0.69726 | 0.69279 | 0.25192 | 0.24982 | 0.518 / 0.540 (n 322) | 0.473 / 0.484 (n 488) |

### Raw over chance (p_over_emp, the totals flag's chance) by decile: the record, not a check

Pushes dropped. p_over (the normal curve, picks file only) is quoted for reference.

**2015-18**: 1015 games, said 0.496 over (normal curve 0.509), happened 0.486.

| Bucket | Games | Said | Happened | z |
|---|---|---|---|---|
| [0.3, 0.4) | 109 | 0.363 | 0.459 | +2.1 |
| [0.4, 0.5) | 415 | 0.459 | 0.489 | +1.3 |
| [0.5, 0.6) | 389 | 0.546 | 0.483 | -2.5 |
| [0.6, 0.7) | 82 | 0.632 | 0.512 | -2.3 |

**2019-22**: 1043 games, said 0.483 over (normal curve 0.494), happened 0.477.

| Bucket | Games | Said | Happened | z |
|---|---|---|---|---|
| [0.3, 0.4) | 162 | 0.361 | 0.370 | +0.3 |
| [0.4, 0.5) | 419 | 0.458 | 0.499 | +1.7 |
| [0.5, 0.6) | 362 | 0.544 | 0.494 | -1.9 |
| [0.6, 0.7) | 76 | 0.631 | 0.500 | -2.4 |

**2023-25**: 811 games, said 0.514 over (normal curve 0.531), happened 0.507.

| Bucket | Games | Said | Happened | z |
|---|---|---|---|---|
| [0.3, 0.4) | 53 | 0.370 | 0.453 | +1.2 |
| [0.4, 0.5) | 291 | 0.461 | 0.488 | +0.9 |
| [0.5, 0.6) | 368 | 0.548 | 0.535 | -0.5 |
| [0.6, 0.7) | 98 | 0.629 | 0.480 | -3.1 |

**2015-25**: 2869 games, said 0.496 over (normal curve 0.510), happened 0.489.

| Bucket | Games | Said | Happened | z |
|---|---|---|---|---|
| [0.2, 0.3) | 30 | 0.274 | 0.433 | +2.0 |
| [0.3, 0.4) | 324 | 0.363 | 0.414 | +1.9 |
| [0.4, 0.5) | 1125 | 0.459 | 0.492 | +2.3 |
| [0.5, 0.6) | 1119 | 0.546 | 0.504 | -2.8 |
| [0.6, 0.7) | 256 | 0.631 | 0.496 | -4.5 |

### Model total against the actual total, by third of the line (bias = said minus happened)

| Window | Third | Games | Line | Model | Actual | Bias model | Bias line | MAE model | MAE line |
|---|---|---|---|---|---|---|---|---|---|
| 2015-18 | low | 384 | 41.3 | 42.6 | 41.5 | +1.19 | -0.17 | 10.59 | 10.46 |
| 2015-18 | mid | 336 | 45.4 | 45.8 | 44.6 | +1.13 | +0.77 | 10.26 | 10.12 |
| 2015-18 | high | 304 | 50.3 | 49.3 | 51.0 | -1.68 | -0.64 | 11.35 | 11.14 |
| 2019-22 | low | 335 | 41.1 | 42.2 | 41.0 | +1.17 | +0.07 | 10.01 | 10.10 |
| 2019-22 | mid | 337 | 45.5 | 45.5 | 46.2 | -0.71 | -0.76 | 11.03 | 11.01 |
| 2019-22 | high | 383 | 50.5 | 49.0 | 50.7 | -1.69 | -0.14 | 10.54 | 10.52 |
| 2023-25 | low | 391 | 40.5 | 42.3 | 41.9 | +0.41 | -1.41 | 10.08 | 10.13 |
| 2023-25 | mid | 221 | 45.4 | 46.4 | 46.0 | +0.38 | -0.67 | 9.97 | 9.71 |
| 2023-25 | high | 204 | 49.4 | 49.0 | 50.3 | -1.30 | -0.87 | 10.61 | 10.55 |

## Margin scale: stated sigma against the realised miss, and how much of it the 50 / 80 / 95% intervals hold

| Window | Games | Sigma stated | Realised SD | Mean miss (result minus model) | Line's SD | 50% holds | 80% holds | 95% holds |
|---|---|---|---|---|---|---|---|---|
| 2015-18 | 1024 | 13.20 | 12.90 | -0.21 | 12.75 | 0.550 | 0.818 | 0.936 |
| 2019-22 | 1055 | 13.07 | 12.90 | -0.98 | 12.76 | 0.528 | 0.804 | 0.944 |
| 2023-25 | 816 | 13.00 | 12.81 | +0.25 | 12.64 | 0.548 | 0.803 | 0.950 |

## Team points by tier of the expected score (bias = said minus scored; z on the scores' own spread)

| Window | Tier | Sides | Said | Scored | Bias | z |
|---|---|---|---|---|---|---|
| 2015-18 | under 18 | 177 | 16.42 | 17.17 | -0.75 | -1.1 |
| 2015-18 | 18-21 | 461 | 19.68 | 19.63 | +0.05 | +0.1 |
| 2015-18 | 21-24 | 605 | 22.49 | 22.09 | +0.39 | +1.0 |
| 2015-18 | 24-27 | 581 | 25.35 | 25.04 | +0.31 | +0.8 |
| 2015-18 | 27+ | 224 | 28.68 | 28.62 | +0.06 | +0.1 |
| 2019-22 | under 18 | 194 | 16.09 | 16.36 | -0.27 | -0.4 |
| 2019-22 | 18-21 | 454 | 19.62 | 20.07 | -0.45 | -1.1 |
| 2019-22 | 21-24 | 638 | 22.54 | 22.56 | -0.02 | -0.0 |
| 2019-22 | 24-27 | 540 | 25.36 | 25.70 | -0.34 | -0.8 |
| 2019-22 | 27+ | 284 | 28.64 | 28.78 | -0.15 | -0.3 |
| 2023-25 | under 18 | 191 | 16.37 | 16.41 | -0.04 | -0.1 |
| 2023-25 | 18-21 | 343 | 19.73 | 19.44 | +0.29 | +0.6 |
| 2023-25 | 21-24 | 524 | 22.52 | 22.14 | +0.38 | +0.9 |
| 2023-25 | 24-27 | 402 | 25.34 | 25.22 | +0.12 | +0.3 |
| 2023-25 | 27+ | 172 | 28.60 | 30.72 | -2.12 | -2.9 |

## Season odds (reports/season_calibration.csv): bands of 30+ teams more than 2 SE out

37 bands with 30+ teams; 4 more than 2 SE from what was said.

| Odds | Window | Band | Teams | Said | Happened | z |
|---|---|---|---|---|---|---|
| division | 2023-25 | 0-0.05 | 183 | 0.008 | 0.038 | +4.5 |
| division | 2023-25 | 0.05-0.15 | 78 | 0.096 | 0.179 | +2.5 |
| playoffs | 2023-25 | 0.05-0.15 | 42 | 0.091 | 0.238 | +3.3 |
| playoffs | 2023-25 | 0.7-0.85 | 41 | 0.774 | 0.585 | -2.9 |

## Player props (data/tracker/props_graded.csv)

5441 graded projections over 2 week(s) (2026-W1, 2026-W2); made: after the fact. Ratio = total scored / total said; tiers are thirds of the projection within each stat. Bias = said minus scored, z on its own spread. Too short a record for a failing check.

| Stat | Rows | Said | Scored | Bias | z | MAE | Ratio | Ratio low tier | Ratio mid | Ratio high |
|---|---|---|---|---|---|---|---|---|---|---|
| def_sacks | 512 | 0.14 | 0.11 | +0.03 | +1.8 | 0.19 | 0.82 | 1.06 | 0.52 | 0.86 |
| def_solo_tackles | 512 | 2.49 | 2.24 | +0.25 | +3.0 | 1.56 | 0.90 | 0.90 | 0.92 | 0.89 |
| def_tackles | 512 | 4.50 | 3.98 | +0.52 | +4.0 | 2.39 | 0.88 | 0.91 | 0.89 | 0.87 |
| field_goals | 64 | 1.67 | 1.50 | +0.17 | +1.2 | 0.93 | 0.90 | 1.01 | 0.96 | 0.71 |
| kick_points | 64 | 7.21 | 6.78 | +0.43 | +0.9 | 2.89 | 0.94 | 0.90 | 1.02 | 0.90 |
| pass_attempts | 61 | 33.90 | 31.07 | +2.83 | +1.9 | 8.28 | 0.92 | 0.95 | 0.81 | 0.98 |
| pass_completions | 61 | 20.06 | 19.05 | +1.01 | +1.1 | 5.09 | 0.95 | 0.82 | 0.98 | 1.03 |
| pass_int | 61 | 0.71 | 0.49 | +0.22 | +2.5 | 0.61 | 0.70 | 0.53 | 0.66 | 0.90 |
| pass_longest | 61 | 33.21 | 36.67 | -3.46 | -1.4 | 14.38 | 1.10 | 1.25 | 1.07 | 0.98 |
| pass_rush_yards | 61 | 237.51 | 217.23 | +20.28 | +1.8 | 71.43 | 0.91 | 0.92 | 0.83 | 0.99 |
| pass_td | 61 | 1.61 | 1.54 | +0.07 | +0.5 | 0.99 | 0.95 | 0.88 | 0.88 | 1.07 |
| pass_yards | 61 | 221.93 | 199.54 | +22.39 | +2.0 | 68.02 | 0.90 | 0.88 | 0.84 | 0.97 |
| rec_catches | 440 | 2.87 | 2.30 | +0.57 | +6.1 | 1.61 | 0.80 | 0.71 | 0.77 | 0.86 |
| rec_longest | 440 | 13.82 | 12.80 | +1.02 | +1.7 | 9.68 | 0.93 | 0.64 | 0.95 | 1.07 |
| rec_targets | 440 | 4.87 | 3.35 | +1.51 | +12.1 | 2.45 | 0.69 | 0.57 | 0.64 | 0.76 |
| rec_td | 440 | 0.23 | 0.18 | +0.05 | +2.4 | 0.32 | 0.78 | 0.66 | 0.52 | 0.95 |
| rec_yards | 440 | 30.25 | 25.96 | +4.29 | +3.2 | 20.88 | 0.86 | 0.62 | 0.79 | 0.96 |
| rush_attempts | 230 | 7.28 | 5.69 | +1.59 | +5.5 | 3.60 | 0.78 | 0.64 | 0.62 | 0.87 |
| rush_longest | 230 | 9.85 | 7.97 | +1.88 | +3.6 | 6.35 | 0.81 | 0.48 | 0.73 | 1.06 |
| rush_rec_yards | 230 | 40.01 | 34.85 | +5.16 | +2.8 | 22.44 | 0.87 | 0.89 | 0.76 | 0.91 |
| rush_td | 230 | 0.23 | 0.20 | +0.03 | +1.1 | 0.32 | 0.85 | 0.95 | 0.42 | 1.02 |
| rush_yards | 230 | 27.87 | 25.00 | +2.87 | +1.9 | 17.68 | 0.90 | 0.52 | 0.77 | 1.03 |

Result: PASS (home win: 0 bucket(s) out, cover: 0 bucket(s) out, over: 0 bucket(s) out)
