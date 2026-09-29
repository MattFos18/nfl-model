# Per-player availability for the season totals (29 Sep 2026)

Script: `experiments/player_availability.py` (rows built fresh into the scratchpad with the harness's `rows_for`;
`reports/player_season_rows.csv` and `reports/player_season_backtest.csv` untouched). Numbers: `reports/player_availability.csv`.

## Question

The dominant miss in the season totals is games missed, and the projection gives every player of a kind one flat
share of his team's games left (`AVAIL`: rec 0.65, rush 0.625, pass 0.525). Does a per-player expected share of the
games left, from what is known as of the week, cut the season-total miss?

Earlier work (docs section 36, `experiments/availability.py`): a linear fit on the report, practice, share of games
played this season and last, two seasons of Out/Doubtful listings and age, times a fitted scale with the blend held at
today's, predicted games better but left the season total mixed (not adopted). This study changes the inputs (own
absences from snap counts over his last 34 team games, missed-last-game, position, reserve lists), the model (binomial
logistic) and refits the blend per variant.

## Adoption rule (written before the results)

For each kind (rec, rush, pass) and each variant (share, mult, capped; scaled is recorded but was not one of the
pre-registered variants), against today's rule as the harness would refit it on the same fresh rows (`flat`):

1. the season-total MAE (every projected player, all four as-of weeks pooled) must be lower on 2019-22 **and** on 2023-25;
2. let g = the smaller of the two pooled gains; on no as-of week (1, 5, 9, 13) in either window may the variant's MAE
   be worse than flat's by more than g.

If more than one variant passes for a kind, the one with the larger summed pooled gain is taken. Within-10% and
within-20% shares and the calibration are reported but are not part of the rule.

## Results

### Season-total error by kind, variant and window (every projected player, as of weeks 1, 5, 9, 13)

games_miss = mean absolute miss on the games left he played (share x team games left against what he played).

| kind | variant | window | n | mae | pace_mae | bias | within10 | within20 | within20_top | games_miss |
|---|---|---|---|---|---|---|---|---|---|---|
| pass | flat | 2019-22 | 450 | 582.4 | 617.1 | 32.3 | 0.353 | 0.540 | 0.612 | 3.878 |
| pass | share | 2019-22 | 450 | 578.7 | 617.1 | 192.5 | 0.369 | 0.529 | 0.604 | 2.223 |
| pass | mult | 2019-22 | 450 | 568.5 | 617.1 | 85.0 | 0.371 | 0.547 | 0.620 | 2.494 |
| pass | capped | 2019-22 | 450 | 582.5 | 617.1 | 198.4 | 0.367 | 0.527 | 0.604 | 2.236 |
| pass | scaled | 2019-22 | 450 | 568.5 | 617.1 | 90.0 | 0.373 | 0.547 | 0.620 | 2.479 |
| pass | flat | 2023-25 | 333 | 626.2 | 663.9 | 169.5 | 0.300 | 0.465 | 0.531 | 3.596 |
| pass | share | 2023-25 | 333 | 659.5 | 663.9 | 331.1 | 0.321 | 0.459 | 0.521 | 2.539 |
| pass | mult | 2023-25 | 333 | 635.7 | 663.9 | 229.4 | 0.291 | 0.456 | 0.510 | 2.663 |
| pass | capped | 2023-25 | 333 | 660.5 | 663.9 | 333.4 | 0.318 | 0.456 | 0.521 | 2.546 |
| pass | scaled | 2023-25 | 333 | 636.5 | 663.9 | 234.2 | 0.291 | 0.459 | 0.514 | 2.655 |
| rec | flat | 2019-22 | 2966 | 125.2 | 142.0 | -5.800 | 0.253 | 0.451 | 0.618 | 2.719 |
| rec | share | 2019-22 | 2966 | 126.2 | 142.0 | 18.7 | 0.259 | 0.455 | 0.620 | 2.118 |
| rec | mult | 2019-22 | 2966 | 123.8 | 142.0 | -1.300 | 0.267 | 0.447 | 0.609 | 2.303 |
| rec | capped | 2019-22 | 2966 | 126.2 | 142.0 | 18.7 | 0.259 | 0.455 | 0.620 | 2.118 |
| rec | scaled | 2019-22 | 2966 | 123.6 | 142.0 | -5.300 | 0.268 | 0.447 | 0.608 | 2.353 |
| rec | flat | 2023-25 | 2088 | 124.0 | 139.8 | -10.4 | 0.236 | 0.446 | 0.611 | 2.647 |
| rec | share | 2023-25 | 2088 | 123.9 | 139.8 | 19.6 | 0.242 | 0.454 | 0.606 | 1.974 |
| rec | mult | 2023-25 | 2088 | 121.4 | 139.8 | -1.100 | 0.251 | 0.461 | 0.632 | 2.170 |
| rec | capped | 2023-25 | 2088 | 123.9 | 139.8 | 19.6 | 0.242 | 0.454 | 0.606 | 1.974 |
| rec | scaled | 2023-25 | 2088 | 121.1 | 139.8 | -5.200 | 0.256 | 0.462 | 0.634 | 2.225 |
| rush | flat | 2019-22 | 1089 | 155.8 | 173.7 | -28.6 | 0.236 | 0.435 | 0.574 | 2.901 |
| rush | share | 2019-22 | 1089 | 153.3 | 173.7 | -2.400 | 0.259 | 0.450 | 0.594 | 2.204 |
| rush | mult | 2019-22 | 1089 | 152.6 | 173.7 | -26.1 | 0.257 | 0.442 | 0.580 | 2.405 |
| rush | capped | 2019-22 | 1089 | 153.3 | 173.7 | -2.200 | 0.259 | 0.448 | 0.594 | 2.204 |
| rush | scaled | 2019-22 | 1089 | 152.7 | 173.7 | -29.4 | 0.256 | 0.442 | 0.578 | 2.443 |
| rush | flat | 2023-25 | 824 | 142.6 | 155.0 | -21.1 | 0.272 | 0.490 | 0.615 | 3.151 |
| rush | share | 2023-25 | 824 | 139.9 | 155.0 | 5.000 | 0.291 | 0.501 | 0.622 | 2.147 |
| rush | mult | 2023-25 | 824 | 139.2 | 155.0 | -18.9 | 0.289 | 0.495 | 0.617 | 2.422 |
| rush | capped | 2023-25 | 824 | 140.0 | 155.0 | 5.100 | 0.291 | 0.500 | 0.622 | 2.149 |
| rush | scaled | 2023-25 | 824 | 139.4 | 155.0 | -22.3 | 0.285 | 0.493 | 0.612 | 2.469 |

Constants fitted on 2016-18 (the blend always refit; fit_mae = 2016-18 season-total error with out-of-season shares):

| kind | variant | constants | fit_mae |
|---|---|---|---|
| rec | flat | {'avail': 0.65, 'blend': 0.5} | 118.1 |
| rec | share | {'blend': 0.25} | 116.9 |
| rec | mult | {'avail': 0.7, 'lam': 1.0, 'pbar': 0.7637, 'blend': 0.25} | 115.6 |
| rec | capped | {'blend': 0.25} | 116.9 |
| rec | scaled | {'scale': 0.9, 'blend': 0.25} | 115.6 |
| rush | flat | {'avail': 0.625, 'blend': 0.5} | 149.0 |
| rush | share | {'blend': 0.25} | 149.8 |
| rush | mult | {'avail': 0.675, 'lam': 1.0, 'pbar': 0.7399, 'blend': 0.25} | 148.6 |
| rush | capped | {'blend': 0.25} | 149.9 |
| rush | scaled | {'scale': 0.9, 'blend': 0.25} | 148.6 |
| pass | flat | {'avail': 0.525, 'blend': 0.75} | 550.0 |
| pass | share | {'blend': 0.5} | 543.4 |
| pass | mult | {'avail': 0.65, 'lam': 1.0, 'pbar': 0.7262, 'blend': 0.5} | 532.2 |
| pass | capped | {'blend': 0.5} | 545.1 |
| pass | scaled | {'scale': 0.9, 'blend': 0.5} | 532.2 |

### The rule, per kind and variant (against flat)

| kind | variant | gain_2019-22 | gain_2023-25 | smaller_gain | worst_week | worst_week_loss | passes | adopted |
|---|---|---|---|---|---|---|---|---|
| rec | share | -0.956 | 0.114 | -0.956 | 2023-25 wk 1 | 5.582 | no |  |
| rec | mult | 1.448 | 2.672 | 1.448 | 2023-25 wk 1 | 0.312 | yes | ADOPT |
| rec | capped | -0.954 | 0.114 | -0.954 | 2023-25 wk 1 | 5.582 | no |  |
| rec | scaled | 1.645 | 2.895 | 1.645 | 2023-25 wk 1 | -0.372 | yes |  |
| rush | share | 2.572 | 2.707 | 2.572 | 2023-25 wk 1 | 1.635 | yes |  |
| rush | mult | 3.243 | 3.463 | 3.243 | 2023-25 wk 13 | 0.023 | yes | ADOPT |
| rush | capped | 2.477 | 2.635 | 2.477 | 2023-25 wk 1 | 1.635 | yes |  |
| rush | scaled | 3.105 | 3.229 | 3.105 | 2023-25 wk 13 | 0.110 | yes |  |
| pass | share | 3.729 | -33.3 | -33.3 | 2023-25 wk 5 | 60.9 | no |  |
| pass | mult | 13.9 | -9.547 | -9.547 | 2023-25 wk 5 | 26.8 | no |  |
| pass | capped | -0.125 | -34.3 | -34.3 | 2023-25 wk 5 | 63.7 | no |  |
| pass | scaled | 14.0 | -10.3 | -10.3 | 2023-25 wk 5 | 28.1 | no |  |

### Per as-of week (season-total MAE; flat against each variant)

| kind | window | asof_week | flat | mult | mult-flat | share-flat | capped-flat | scaled-flat |
|---|---|---|---|---|---|---|---|---|
| pass | 2019-22 | 1 | 952.2 | 934.4 | -17.8 | -22.9 | -21.2 | -18.9 |
| pass | 2019-22 | 5 | 670.6 | 649.5 | -21.1 | 8.868 | 16.5 | -20.1 |
| pass | 2019-22 | 9 | 428.1 | 415.1 | -13.0 | -3.585 | 1.511 | -13.2 |
| pass | 2019-22 | 13 | 291.5 | 287.5 | -3.920 | 0.883 | 1.722 | -3.926 |
| pass | 2023-25 | 1 | 955.3 | 951.6 | -3.709 | 22.3 | 22.3 | -3.095 |
| pass | 2023-25 | 5 | 741.8 | 768.6 | 26.8 | 60.9 | 63.7 | 28.1 |
| pass | 2023-25 | 9 | 523.2 | 534.1 | 10.9 | 31.9 | 31.9 | 11.7 |
| pass | 2023-25 | 13 | 333.2 | 336.4 | 3.268 | 18.0 | 19.1 | 3.783 |
| rec | 2019-22 | 1 | 192.7 | 192.4 | -0.357 | 3.763 | 3.763 | -0.829 |
| rec | 2019-22 | 5 | 145.8 | 142.6 | -3.271 | 0.268 | 0.258 | -3.625 |
| rec | 2019-22 | 9 | 102.7 | 101.5 | -1.185 | 0.549 | 0.549 | -1.223 |
| rec | 2019-22 | 13 | 68.4 | 67.6 | -0.761 | -0.328 | -0.326 | -0.712 |
| rec | 2023-25 | 1 | 182.8 | 183.1 | 0.312 | 5.582 | 5.582 | -0.372 |
| rec | 2023-25 | 5 | 148.1 | 141.7 | -6.383 | -2.714 | -2.714 | -6.774 |
| rec | 2023-25 | 9 | 108.0 | 104.3 | -3.702 | -2.317 | -2.316 | -3.670 |
| rec | 2023-25 | 13 | 71.3 | 70.6 | -0.666 | -0.140 | -0.138 | -0.614 |
| rush | 2019-22 | 1 | 234.5 | 232.4 | -2.087 | -0.538 | -0.410 | -1.874 |
| rush | 2019-22 | 5 | 175.6 | 169.4 | -6.207 | -4.242 | -4.015 | -6.205 |
| rush | 2019-22 | 9 | 127.9 | 125.4 | -2.549 | -2.500 | -2.454 | -2.365 |
| rush | 2019-22 | 13 | 92.5 | 90.6 | -1.829 | -2.681 | -2.707 | -1.654 |
| rush | 2023-25 | 1 | 230.6 | 229.4 | -1.193 | 1.635 | 1.635 | -1.093 |
| rush | 2023-25 | 5 | 163.7 | 154.8 | -8.928 | -7.267 | -7.135 | -8.769 |
| rush | 2023-25 | 9 | 110.5 | 106.7 | -3.757 | -4.457 | -4.349 | -3.190 |
| rush | 2023-25 | 13 | 82.1 | 82.1 | 0.023 | -0.343 | -0.304 | 0.110 |

### Calibration: predicted against realised share of the team's games left played (logit p; weighted by games left)

(2016-18 rows are out-of-season predictions.) By kind: `calib` rows in the csv.

| band | n_2016-18 | pred_2016-18 | real_2016-18 | n_2019-22 | pred_2019-22 | real_2019-22 | n_2023-25 | pred_2023-25 | real_2023-25 |
|---|---|---|---|---|---|---|---|---|---|
| <0.3 | 51 | 0.245 | 0.336 | 73 | 0.247 | 0.299 | 29 | 0.254 | 0.213 |
| 0.3-0.5 | 206 | 0.410 | 0.423 | 187 | 0.430 | 0.452 | 157 | 0.413 | 0.388 |
| 0.5-0.6 | 202 | 0.554 | 0.582 | 250 | 0.558 | 0.590 | 164 | 0.553 | 0.518 |
| 0.6-0.7 | 306 | 0.655 | 0.660 | 489 | 0.657 | 0.684 | 286 | 0.658 | 0.647 |
| 0.7-0.8 | 681 | 0.757 | 0.754 | 1239 | 0.756 | 0.739 | 843 | 0.758 | 0.752 |
| 0.8-0.9 | 1478 | 0.851 | 0.849 | 2055 | 0.847 | 0.827 | 1606 | 0.845 | 0.827 |
| 0.9-1 | 127 | 0.912 | 0.902 | 212 | 0.914 | 0.907 | 160 | 0.909 | 0.898 |

### The share model itself (against the flat 2016-18 rate of the kind)

| kind | window | n | logloss | logloss_flat | games_miss | games_miss_flat |
|---|---|---|---|---|---|---|
| pass | 2016-18 | 299 | 0.442 | 0.577 | 2.004 | 2.927 |
| rec | 2016-18 | 2003 | 0.510 | 0.545 | 1.881 | 2.109 |
| rush | 2016-18 | 749 | 0.540 | 0.573 | 2.152 | 2.392 |
| pass | 2019-22 | 450 | 0.485 | 0.606 | 2.152 | 3.022 |
| rec | 2019-22 | 2966 | 0.533 | 0.551 | 2.067 | 2.234 |
| rush | 2019-22 | 1089 | 0.540 | 0.564 | 2.146 | 2.389 |
| pass | 2023-25 | 333 | 0.574 | 0.684 | 2.539 | 3.362 |
| rec | 2023-25 | 2088 | 0.523 | 0.540 | 1.972 | 2.156 |
| rush | 2023-25 | 824 | 0.501 | 0.558 | 2.147 | 2.616 |

### The model

Binomial logistic regression, pooled over kinds, fitted on 2016-18 (sklearn LogisticRegression, L2, C=1, each row as games played / not played of the team's games left). Features (all as of the week):

| feature | coef |
|---|---|
| intercept | 0.437 |
| k_rush | 0.115 |
| k_pass | 0.143 |
| p_RB | -0.270 |
| p_TE | -0.099 |
| p_QB | -0.111 |
| rep_out | -0.290 |
| rep_doubt | -0.931 |
| rep_q | -0.088 |
| prac_dnp | -0.799 |
| prac_lim | -0.092 |
| ir_prev | 1.657 |
| ir_season | 0.527 |
| miss34_rate | -1.859 |
| n34_short | -0.324 |
| miss_last | -0.132 |
| age_le23 | 0.488 |
| age_27_29 | 0.023 |
| age_30_32 | -0.091 |
| age_33p | -0.131 |
| share_now | 1.586 |
| wk1 | 1.120 |

Feature means by window (mean over kinds):

| feature | 2016-18 | 2019-22 | 2023-25 |
|---|---|---|---|
| ir_now | 0.000 | 0.000 | 0.000 |
| ir_prev | 0.002 | 0.009 | 0.003 |
| ir_season | 0.009 | 0.034 | 0.025 |
| miss34_rate | 0.199 | 0.227 | 0.227 |
| miss_last | 0.159 | 0.164 | 0.162 |
| prac_dnp | 0.044 | 0.016 | 0.010 |
| prac_lim | 0.058 | 0.042 | 0.033 |
| rep_doubt | 0.007 | 0.001 | 0.000 |
| rep_out | 0.038 | 0.001 | 0.000 |
| rep_q | 0.059 | 0.044 | 0.032 |
| share_now | 0.672 | 0.600 | 0.608 |

## Verdict

**Adopted for receiving and rushing (variant `mult`); not for passing.**

- rec: MAE 125.2 -> 123.8 (2019-22), 124.0 -> 121.4 (2023-25); smaller gain 1.45; worst as-of week 2023-25 week 1, +0.31
  (inside 1.45). Within 20%: 0.451 -> 0.447 and 0.446 -> 0.461.
- rush: 155.8 -> 152.6, 142.6 -> 139.2; smaller gain 3.24; worst week 2023-25 week 13, +0.02. Within 20%: 0.435 -> 0.442,
  0.490 -> 0.495.
- pass: every variant is worse on 2023-25 (mult 626.2 -> 635.7; share and capped about +33), the worst week 2023-25
  week 5. Passing keeps the flat 0.525 / 0.75.

`share` and `capped` (the raw p, blend refit) lose for receivers: p is calibrated for games played (the realised share
is about 0.77) but the season-total error wants a lower level (the misses are one-sided), so the level has to be
fitted: `mult` refits it (AVAIL 0.70 / 0.675) and `scaled` does the same thing (p x 0.9). The fit chose no shrinkage
(lam 1, the edge of the 0..1 grid), so `mult` is AVAIL x p / pbar, i.e. rec 0.9166 p, rush 0.9123 p, at most 1.
With the per-player share the blend toward pace drops from 0.5 to 0.25 for both kinds.

What carries p: own absences over the last 34 team games (coef -1.86 on the missed rate), the share of team games
played so far this season (+1.59), young (<24, +0.49), RB (-0.27), Doubtful (-0.93) and DNP (-0.80). The report terms
matter little in the test windows because from 2019 the weekly roster marks game-day inactives INA and the harness
(`roster_at`, status ACT) drops them from the rows: players listed Out are 3.8% of the 2016-18 rows and 0.1% after.
"On IR now" is always 0 for the same reason (only ACT players are projected); `ir_prev` (activated this week, +1.66)
and `ir_season` (+0.53) are rare (0.2-3%).

Robustness (not part of the rule): the pooled logit at C = 0.1 and 10 gives the same constants and gains (rec +1.4 to
+1.5 / +2.6 to +2.7, rush +3.2 to +3.4 / +3.2 to +3.5). A per-kind logit (not the pre-stated model) keeps rec (+1.44 /
+2.72), loses rush (the fit falls back to flat), and turns passing into a gain on both windows (+36.3 / +14.2; worst
week 2023-25 week 5, +8.6): a lead for a pre-registered follow-up on passers, not adopted here.

Side finding for the harness: the INA drop above means the 2019-25 rows exclude players ruled inactive on game day of
the as-of week, which the page cannot know when it projects during the week; 2016-18 rows keep them.

### The change to nflmodel/player_season.py

Verified: the function below reproduces the study's p to 3e-5 on 2019 wk 1, 2021 wk 9, 2023 wk 5, 2025 wk 13 (about
1.3 s per call, inputs cached). Constants: AVAIL rec 0.65 -> 0.70, rush 0.625 -> 0.675, pass 0.525; BLEND rec 0.5 ->
0.25, rush 0.5 -> 0.25, pass 0.75. AVAIL_PBAR rec 0.7637, rush 0.7399 (pass absent = flat). The logit coefficients are
the table above (4 decimals in the code). In `project()` replace `out["avail"] = out.kind.map(avail)` by
`out["avail_p"] = availability_p(out, season, week)`, `out["avail_mult"] = (out.avail_p / out.kind.map(AVAIL_PBAR)).fillna(1.0)`,
`out["avail"] = (out.kind.map(avail) * out.avail_mult).clip(upper=1.0)`; in `_finish()` and the harness's `evaluate()`
the share becomes `(R.kind.map(avail) * R.avail_mult).clip(upper=1.0)` (the rows cache then needs a rebuild to carry
avail_mult). Full code in the study's final report.

Runtimes: fresh rows 492 s wall (39 season-weeks, 2 workers, about 25 s each); features + fit + scoring 14 s; the
robustness checks 28 s.
