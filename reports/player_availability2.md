# Availability follow-up: the midweek roster and a passer logit (29 Sep 2026)

Script: `experiments/player_availability2.py`. Rows built fresh into the scratchpad
(`scratchpad/availability2/`); `reports/player_season_rows.csv`, `reports/player_season_backtest.csv` and
today's study files untouched. Numbers: `reports/player_availability2.csv`.

## Questions

1. **Harness look-ahead.** `player_season.roster_at` keeps only players whose weekly roster status is `ACT` at the
   as-of week. From 2019 nflverse marks game-day inactives `INA` (before 2019 they are `ACT`), so the 2019-25 backtest
   rows drop players ruled inactive for the as-of week's game, which the live page cannot know midweek. How much did
   that flatter today's numbers (flat rule and the adopted pooled-logit `mult` for receivers and rushers), and does
   the adoption still hold on rows built from the roster as the page sees it midweek?
2. **Passers.** Today's study found post hoc that a per-kind logit turns passing into a gain on both windows. Here it
   is pre-registered and run on the corrected rows.

## The roster fix (as the live page would see it midweek)

Weekly roster status codes in `data/raw/rosters/roster_weekly_<season>.parquet` (regular season): `ACT` active,
`INA` inactive for that week's game (from 2019; almost all carry description `A01`, i.e. on the 53), `RES` reserve
(IR and the other R-codes), `PUP`, `NFI` (2016-18 only), `SUS` suspended, `EXE` exempt, `NWT` non-football injury /
not with team, `RSN`/`RSR` reserve, `DEV` practice squad, `CUT`, `RET` retired, `TRC`/`TRD`/`TRT` traded, `E01`/`E14`
exempt / international. 2016-18 have no `INA` at all.

**Kept: `ACT` and `INA`** (on the 53, not on a reserve list, not suspended or exempt), taking `ACT` first when a
player has two rows in a week. Everything else in `roster_at` is unchanged (the latest roster week at or before the
as-of week). Because 2016-18 have no `INA`, the 2016-18 rows, and so every constant and logit fitted on them, are
identical to today's; only the 2019-25 rows change.

## Pre-registered rules (written before the corrected rows were scored)

**Look-ahead (1).** Descriptive, no rule: for rec, rush and pass, the season-total MAE of `flat` (AVAIL and BLEND
refit on 2016-18 on the harness grid) and of today's adopted pooled-logit `mult` (the same fit as today's study) on
the old rows (ACT only) and the corrected rows (ACT or INA), both windows, pooled and by as-of week. Today's adoption
for rec and rush is re-checked with today's rule on the corrected rows: MAE lower on 2019-22 and 2023-25, and on no
as-of week (1, 5, 9, 13) in either window worse than flat by more than the smaller pooled gain.

**Passers (2).**
- Model: a binomial logit fitted on the passer rows of 2016-18 only, with the same features and fit as today's
  pooled model (`experiments/player_availability.py` `design` / `fit_logit`: sklearn LogisticRegression, L2, C = 1,
  each row as games played / not played of the team's games left; the kind and position columns are constant or
  near-constant for passers and are left in). The 2016-18 passer rows carry out-of-season predictions (each season
  predicted by a fit on the other two) for fitting the constants; 2019-25 use the full 2016-18 fit.
- Variants: `mult` (AVAIL x (1 + lam x (p / pbar - 1)), capped at 1, pbar the mean p on the 2016-18 passer rows, AVAIL
  on the harness grid 0.3..1.0, lam in 0, 0.25 .. 1) and `share` (p itself), with BLEND refit on 2016-18 on the
  season-total error for each (grid 0, 0.25 .. 1), exactly as `fit_variant` in today's study.
- Baseline: `flat` passing (AVAIL and BLEND refit on 2016-18: 0.525 / 0.75) on the same corrected rows.
- Adoption for passing: a variant passes if the season-total MAE (every projected passer, weeks 1, 5, 9, 13 pooled)
  is lower than flat's on 2019-22 **and** 2023-25, and on no as-of week in either window is it worse than flat by
  more than g = the smaller of the two pooled gains. If both pass, the one with the larger summed pooled gain is
  adopted. Otherwise passing stays flat.
- Reported but not part of the rule: calibration of p (pooled logit by kind; passer logit) on the corrected rows,
  within-20%, bias, games miss.

## Results

### 1. Look-ahead: old rows (ACT only) against corrected rows (ACT or INA), season-total error

Every projected player, as of weeks 1, 5, 9, 13 pooled. `mult` for pass is today's pooled logit (recorded, never adopted).

| kind | variant | window | n_old | n_new | mae_old | mae_new | mae_change | bias_old | bias_new | within20_old | within20_new |
|---|---|---|---|---|---|---|---|---|---|---|---|
| pass | flat | 2019-22 | 450 | 460 | 582.4 | 611.6 | 29.2 | 32.3 | 55.4 | 0.540 | 0.504 |
| pass | flat | 2023-25 | 333 | 335 | 626.2 | 621.6 | -4.605 | 169.5 | 120.7 | 0.465 | 0.490 |
| pass | mult | 2019-22 | 450 | 460 | 568.5 | 598.0 | 29.5 | 85.0 | 103.4 | 0.547 | 0.513 |
| pass | mult | 2023-25 | 333 | 335 | 635.7 | 625.5 | -10.2 | 229.4 | 185.7 | 0.456 | 0.469 |
| rec | flat | 2019-22 | 2966 | 3227 | 125.2 | 125.8 | 0.578 | -5.802 | 0.476 | 0.451 | 0.437 |
| rec | flat | 2023-25 | 2088 | 2268 | 124.0 | 123.1 | -0.916 | -10.4 | -4.988 | 0.446 | 0.434 |
| rec | mult | 2019-22 | 2966 | 3227 | 123.8 | 123.1 | -0.604 | -1.318 | 1.737 | 0.447 | 0.435 |
| rec | mult | 2023-25 | 2088 | 2268 | 121.4 | 120.5 | -0.858 | -1.086 | 1.285 | 0.461 | 0.448 |
| rush | flat | 2019-22 | 1089 | 1214 | 155.8 | 152.0 | -3.832 | -28.6 | -18.6 | 0.435 | 0.418 |
| rush | flat | 2023-25 | 824 | 915 | 142.6 | 143.1 | 0.432 | -21.1 | -14.8 | 0.490 | 0.462 |
| rush | mult | 2019-22 | 1089 | 1214 | 152.6 | 148.1 | -4.481 | -26.1 | -18.7 | 0.442 | 0.429 |
| rush | mult | 2023-25 | 824 | 915 | 139.2 | 140.0 | 0.766 | -18.9 | -14.8 | 0.495 | 0.463 |

Rows added by the fix (in the corrected rows, not in the old; `old_rows_gone`: old rows no longer present, e.g. a team's starting QB by dropbacks changes when the inactive starter comes back into the roster):

| kind | window | rows_added | share_of_rows | old_rows_gone |
|---|---|---|---|---|
| pass | 2019-22 | 108 | 0.235 | 98 |
| pass | 2023-25 | 91 | 0.272 | 89 |
| rec | 2019-22 | 261 | 0.081 | 0 |
| rec | 2023-25 | 180 | 0.079 | 0 |
| rush | 2019-22 | 125 | 0.103 | 0 |
| rush | 2023-25 | 91 | 0.099 | 0 |

On the corrected rows, split into the rows the fix added and the rest:

| kind | variant | window | row | n | mae | bias | games_miss |
|---|---|---|---|---|---|---|---|
| pass | flat | 2019-22 | added | 108 | 566.0 | 164.9 | 2.990 |
| pass | flat | 2019-22 | kept | 352 | 625.6 | 21.8 | 4.153 |
| pass | mult | 2019-22 | added | 108 | 566.8 | 188.9 | 2.438 |
| pass | mult | 2019-22 | kept | 352 | 607.6 | 77.1 | 2.636 |
| pass | flat | 2023-25 | added | 91 | 563.0 | -0.400 | 3.381 |
| pass | flat | 2023-25 | kept | 244 | 643.4 | 165.8 | 3.690 |
| pass | mult | 2023-25 | added | 91 | 554.1 | 72.9 | 2.476 |
| pass | mult | 2023-25 | kept | 244 | 652.1 | 227.7 | 2.722 |
| rec | flat | 2019-22 | added | 261 | 132.3 | 71.8 | 2.768 |
| rec | flat | 2019-22 | kept | 2966 | 125.2 | -5.802 | 2.719 |
| rec | mult | 2019-22 | added | 261 | 116.3 | 36.5 | 2.602 |
| rec | mult | 2019-22 | kept | 2966 | 123.8 | -1.318 | 2.303 |
| rec | flat | 2023-25 | added | 180 | 112.5 | 57.4 | 2.781 |
| rec | flat | 2023-25 | kept | 2088 | 124.0 | -10.4 | 2.647 |
| rec | mult | 2023-25 | added | 180 | 110.5 | 28.8 | 2.830 |
| rec | mult | 2023-25 | kept | 2088 | 121.4 | -1.086 | 2.170 |
| rush | flat | 2019-22 | added | 125 | 118.6 | 68.8 | 3.022 |
| rush | flat | 2019-22 | kept | 1089 | 155.8 | -28.6 | 2.901 |
| rush | mult | 2019-22 | added | 125 | 109.1 | 45.7 | 2.615 |
| rush | mult | 2019-22 | kept | 1089 | 152.6 | -26.1 | 2.405 |
| rush | flat | 2023-25 | added | 91 | 147.0 | 42.6 | 3.080 |
| rush | flat | 2023-25 | kept | 824 | 142.6 | -21.1 | 3.151 |
| rush | mult | 2023-25 | added | 91 | 146.9 | 22.1 | 2.655 |
| rush | mult | 2023-25 | kept | 824 | 139.2 | -18.9 | 2.422 |

Feature means (all kinds) by window, old and corrected rows:

| feature | new_2016-18 | new_2019-22 | new_2023-25 | old_2016-18 | old_2019-22 | old_2023-25 |
|---|---|---|---|---|---|---|
| miss_last | 0.143 | 0.163 | 0.149 | 0.143 | 0.132 | 0.119 |
| prac_dnp | 0.057 | 0.062 | 0.048 | 0.057 | 0.021 | 0.013 |
| prac_lim | 0.067 | 0.067 | 0.054 | 0.067 | 0.053 | 0.042 |
| rep_doubt | 0.009 | 0.010 | 0.005 | 0.009 | 0.001 | 0.000 |
| rep_out | 0.043 | 0.039 | 0.032 | 0.043 | 0.001 | 0.000 |
| rep_q | 0.071 | 0.066 | 0.051 | 0.071 | 0.054 | 0.038 |
| share_now | 0.685 | 0.609 | 0.624 | 0.685 | 0.615 | 0.631 |
| status_INA | 0.000 | 0.085 | 0.083 | 0.000 | 0.000 | 0.000 |

### Today's rule for the adopted `mult` (rec, rush), old and corrected rows

| kind | variant | rows | gain_2019-22 | gain_2023-25 | smaller_gain | worst_week | worst_week_loss | passes |
|---|---|---|---|---|---|---|---|---|
| rec | mult | old | 1.448 | 2.672 | 1.448 | 2023-25 wk 1 | 0.312 | yes |
| rec | mult | new | 2.631 | 2.615 | 2.615 | 2023-25 wk 1 | 0.210 | yes |
| rush | mult | old | 3.243 | 3.463 | 3.243 | 2023-25 wk 13 | 0.023 | yes |
| rush | mult | new | 3.893 | 3.130 | 3.130 | 2023-25 wk 13 | -0.424 | yes |

Per as-of week (rec, rush):

| kind | window | asof_week | flat_old | flat_new | mult_old | mult_new | mult-flat_old | mult-flat_new |
|---|---|---|---|---|---|---|---|---|
| rec | 2019-22 | 1 | 192.7 | 193.5 | 192.4 | 192.3 | -0.357 | -1.186 |
| rec | 2019-22 | 5 | 145.8 | 148.8 | 142.6 | 144.3 | -3.271 | -4.515 |
| rec | 2019-22 | 9 | 102.7 | 104.5 | 101.5 | 101.7 | -1.185 | -2.803 |
| rec | 2019-22 | 13 | 68.4 | 68.2 | 67.6 | 66.5 | -0.761 | -1.712 |
| rec | 2023-25 | 1 | 182.8 | 182.6 | 183.1 | 182.8 | 0.312 | 0.210 |
| rec | 2023-25 | 5 | 148.1 | 146.7 | 141.7 | 141.5 | -6.383 | -5.106 |
| rec | 2023-25 | 9 | 108.0 | 107.6 | 104.3 | 103.6 | -3.702 | -4.044 |
| rec | 2023-25 | 13 | 71.3 | 70.6 | 70.6 | 69.4 | -0.666 | -1.146 |
| rush | 2019-22 | 1 | 234.5 | 231.9 | 232.4 | 229.9 | -2.087 | -1.915 |
| rush | 2019-22 | 5 | 175.6 | 174.8 | 169.4 | 166.5 | -6.207 | -8.262 |
| rush | 2019-22 | 9 | 127.9 | 126.5 | 125.4 | 123.2 | -2.549 | -3.364 |
| rush | 2019-22 | 13 | 92.5 | 88.7 | 90.6 | 87.0 | -1.829 | -1.674 |
| rush | 2023-25 | 1 | 230.6 | 231.5 | 229.4 | 230.4 | -1.193 | -1.158 |
| rush | 2023-25 | 5 | 163.7 | 169.7 | 154.8 | 163.2 | -8.928 | -6.536 |
| rush | 2023-25 | 9 | 110.5 | 109.9 | 106.7 | 105.7 | -3.757 | -4.210 |
| rush | 2023-25 | 13 | 82.1 | 80.2 | 82.1 | 79.7 | 0.023 | -0.424 |

Constants fitted on 2016-18 (identical on old and corrected rows; `pmult` / `pshare` use the passer logit):

| kind | variant | constants | fit_mae_2016-18 |
|---|---|---|---|
| rec | flat | {'avail': 0.65, 'blend': 0.5} | 118.1 |
| rec | mult | {'avail': 0.7, 'lam': 1.0, 'pbar': 0.7637, 'blend': 0.25} | 115.6 |
| rush | flat | {'avail': 0.625, 'blend': 0.5} | 149.0 |
| rush | mult | {'avail': 0.675, 'lam': 1.0, 'pbar': 0.7399, 'blend': 0.25} | 148.6 |
| pass | flat | {'avail': 0.525, 'blend': 0.75} | 550.0 |
| pass | mult | {'avail': 0.65, 'lam': 1.0, 'pbar': 0.7262, 'blend': 0.5} | 532.2 |
| pass | pmult | {'avail': 0.625, 'lam': 1.0, 'pbar': 0.725, 'blend': 0.5} | 526.8 |
| pass | pshare | {'blend': 0.25} | 540.1 |

### 2. Passers: the pre-registered rule on the corrected rows (`mult` = today's pooled logit, for reference)

| kind | variant | rows | gain_2019-22 | gain_2023-25 | smaller_gain | worst_week | worst_week_loss | passes | adopted |
|---|---|---|---|---|---|---|---|---|---|
| pass | pmult | new | 35.7 | 18.7 | 18.7 | 2023-25 wk 5 | -11.5 | yes | ADOPT |
| pass | pshare | new | 11.9 | -18.7 | -18.7 | 2023-25 wk 5 | 33.4 | no |  |
| pass | mult | new | 13.5 | -3.935 | -3.935 | 2023-25 wk 5 | 14.2 | no |  |

Passing season-total error on the corrected rows:

| variant | window | n | mae | pace_mae | bias | within10 | within20 | within20_top | games_miss |
|---|---|---|---|---|---|---|---|---|---|
| flat | 2019-22 | 460 | 611.6 | 653.6 | 55.4 | 0.328 | 0.504 | 0.578 | 3.880 |
| mult | 2019-22 | 460 | 598.0 | 653.6 | 103.4 | 0.348 | 0.513 | 0.594 | 2.590 |
| pmult | 2019-22 | 460 | 575.9 | 653.6 | 71.1 | 0.352 | 0.522 | 0.602 | 2.476 |
| pshare | 2019-22 | 460 | 599.7 | 653.6 | 230.4 | 0.393 | 0.511 | 0.589 | 2.189 |
| flat | 2023-25 | 335 | 621.6 | 653.5 | 120.7 | 0.296 | 0.490 | 0.556 | 3.606 |
| mult | 2023-25 | 335 | 625.5 | 653.5 | 185.7 | 0.293 | 0.469 | 0.535 | 2.655 |
| pmult | 2023-25 | 335 | 602.9 | 653.5 | 133.6 | 0.304 | 0.484 | 0.542 | 2.538 |
| pshare | 2023-25 | 335 | 640.3 | 653.5 | 295.2 | 0.310 | 0.484 | 0.549 | 2.301 |

Passing per as-of week (corrected rows):

| window | asof_week | flat | pmult | pshare | pmult-flat | pshare-flat | mult-flat |
|---|---|---|---|---|---|---|---|
| 2019-22 | 1 | 975.7 | 910.0 | 940.3 | -65.8 | -35.4 | -22.5 |
| 2019-22 | 5 | 701.4 | 673.7 | 713.5 | -27.7 | 12.0 | -11.3 |
| 2019-22 | 9 | 472.8 | 449.0 | 461.3 | -23.8 | -11.5 | -11.8 |
| 2019-22 | 13 | 303.8 | 277.2 | 288.7 | -26.6 | -15.0 | -9.104 |
| 2023-25 | 1 | 921.6 | 888.6 | 943.9 | -32.9 | 22.4 | 1.775 |
| 2023-25 | 5 | 689.2 | 677.7 | 722.6 | -11.5 | 33.4 | 14.2 |
| 2023-25 | 9 | 550.4 | 530.9 | 567.3 | -19.6 | 16.8 | 4.476 |
| 2023-25 | 13 | 368.2 | 355.9 | 371.8 | -12.3 | 3.626 | -4.324 |

Logit coefficients (fitted on 2016-18): the pooled model (today's) and the passer model:

| feature | passer | pooled |
|---|---|---|
| intercept | 0.431 | 0.437 |
| k_rush | 0.000 | 0.115 |
| k_pass | 0.328 | 0.143 |
| p_RB | 0.000 | -0.270 |
| p_TE | 0.000 | -0.099 |
| p_QB | 0.328 | -0.111 |
| rep_out | -0.921 | -0.290 |
| rep_doubt | 0.000 | -0.931 |
| rep_q | 0.214 | -0.088 |
| prac_dnp | -0.540 | -0.799 |
| prac_lim | -0.243 | -0.092 |
| ir_prev | 0.000 | 1.657 |
| ir_season | 0.000 | 0.527 |
| miss34_rate | -3.302 | -1.859 |
| n34_short | -1.037 | -0.324 |
| miss_last | -0.428 | -0.132 |
| age_le23 | 2.407 | 0.488 |
| age_27_29 | -0.069 | 0.023 |
| age_30_32 | -0.064 | -0.091 |
| age_33p | -0.349 | -0.131 |
| share_now | 1.429 | 1.586 |
| wk1 | 1.110 | 1.120 |

### 3. Calibration of p on the corrected rows (weighted by team games left; 2016-18 out of season)

Overall by kind:

| variant | kind | window | n | pred | real | logloss | games_miss |
|---|---|---|---|---|---|---|---|
| passer | pass | 2016-18 | 299 | 0.733 | 0.736 | 0.453 | 1.859 |
| passer | pass | 2019-22 | 460 | 0.713 | 0.696 | 0.514 | 2.116 |
| passer | pass | 2023-25 | 335 | 0.677 | 0.647 | 0.566 | 2.301 |
| pooled | pass | 2016-18 | 299 | 0.734 | 0.736 | 0.442 | 2.004 |
| pooled | pass | 2019-22 | 460 | 0.713 | 0.696 | 0.500 | 2.270 |
| pooled | pass | 2023-25 | 335 | 0.697 | 0.647 | 0.564 | 2.500 |
| pooled | rec | 2016-18 | 2003 | 0.763 | 0.765 | 0.510 | 1.881 |
| pooled | rec | 2019-22 | 3227 | 0.755 | 0.739 | 0.548 | 2.117 |
| pooled | rec | 2023-25 | 2268 | 0.771 | 0.748 | 0.542 | 2.046 |
| pooled | rush | 2016-18 | 749 | 0.738 | 0.740 | 0.540 | 2.152 |
| pooled | rush | 2019-22 | 1214 | 0.730 | 0.716 | 0.560 | 2.212 |
| pooled | rush | 2023-25 | 915 | 0.733 | 0.725 | 0.522 | 2.213 |

By band:

| variant | kind | band | n_2016-18 | pred_2016-18 | real_2016-18 | n_2019-22 | pred_2019-22 | real_2019-22 | n_2023-25 | pred_2023-25 | real_2023-25 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| passer | pass | <0.3 | 42 | 0.193 | 0.309 | 78 | 0.168 | 0.216 | 49 | 0.184 | 0.303 |
| passer | pass | 0.3-0.5 | 23 | 0.399 | 0.304 | 34 | 0.400 | 0.478 | 46 | 0.397 | 0.369 |
| passer | pass | 0.5-0.6 | 11 | 0.552 | 0.589 | 14 | 0.546 | 0.614 | 15 | 0.545 | 0.559 |
| passer | pass | 0.6-0.7 | 15 | 0.660 | 0.741 | 28 | 0.654 | 0.672 | 25 | 0.648 | 0.633 |
| passer | pass | 0.7-0.8 | 24 | 0.755 | 0.664 | 45 | 0.752 | 0.723 | 40 | 0.753 | 0.685 |
| passer | pass | 0.8-0.9 | 86 | 0.869 | 0.868 | 151 | 0.868 | 0.827 | 88 | 0.862 | 0.799 |
| passer | pass | 0.9-1 | 98 | 0.931 | 0.922 | 110 | 0.949 | 0.880 | 72 | 0.936 | 0.863 |
| pooled | pass | <0.3 | 15 | 0.243 | 0.209 | 42 | 0.246 | 0.224 | 20 | 0.258 | 0.176 |
| pooled | pass | 0.3-0.5 | 41 | 0.398 | 0.313 | 52 | 0.412 | 0.329 | 46 | 0.411 | 0.388 |
| pooled | pass | 0.5-0.6 | 13 | 0.548 | 0.387 | 31 | 0.544 | 0.432 | 32 | 0.548 | 0.396 |
| pooled | pass | 0.6-0.7 | 21 | 0.643 | 0.498 | 28 | 0.654 | 0.615 | 31 | 0.655 | 0.559 |
| pooled | pass | 0.7-0.8 | 35 | 0.759 | 0.808 | 68 | 0.755 | 0.751 | 58 | 0.755 | 0.708 |
| pooled | pass | 0.8-0.9 | 160 | 0.855 | 0.906 | 213 | 0.847 | 0.855 | 137 | 0.848 | 0.823 |
| pooled | pass | 0.9-1 | 14 | 0.909 | 0.922 | 26 | 0.913 | 0.918 | 11 | 0.911 | 0.955 |
| pooled | rec | <0.3 | 19 | 0.252 | 0.380 | 21 | 0.221 | 0.326 | 12 | 0.262 | 0.319 |
| pooled | rec | 0.3-0.5 | 108 | 0.410 | 0.455 | 167 | 0.426 | 0.495 | 82 | 0.421 | 0.462 |
| pooled | rec | 0.5-0.6 | 137 | 0.553 | 0.571 | 214 | 0.559 | 0.588 | 129 | 0.555 | 0.583 |
| pooled | rec | 0.6-0.7 | 191 | 0.658 | 0.683 | 403 | 0.658 | 0.645 | 218 | 0.659 | 0.622 |
| pooled | rec | 0.7-0.8 | 475 | 0.758 | 0.749 | 903 | 0.756 | 0.726 | 602 | 0.757 | 0.737 |
| pooled | rec | 0.8-0.9 | 1001 | 0.850 | 0.845 | 1367 | 0.847 | 0.819 | 1094 | 0.845 | 0.813 |
| pooled | rec | 0.9-1 | 72 | 0.914 | 0.925 | 152 | 0.913 | 0.909 | 131 | 0.909 | 0.880 |
| pooled | rush | <0.3 | 17 | 0.240 | 0.362 | 45 | 0.236 | 0.299 | 20 | 0.238 | 0.220 |
| pooled | rush | 0.3-0.5 | 57 | 0.418 | 0.443 | 78 | 0.412 | 0.467 | 74 | 0.416 | 0.367 |
| pooled | rush | 0.5-0.6 | 52 | 0.558 | 0.670 | 95 | 0.555 | 0.547 | 68 | 0.553 | 0.511 |
| pooled | rush | 0.6-0.7 | 94 | 0.652 | 0.657 | 145 | 0.655 | 0.661 | 104 | 0.656 | 0.622 |
| pooled | rush | 0.7-0.8 | 171 | 0.753 | 0.757 | 324 | 0.755 | 0.730 | 238 | 0.757 | 0.740 |
| pooled | rush | 0.8-0.9 | 317 | 0.851 | 0.830 | 489 | 0.846 | 0.819 | 391 | 0.846 | 0.865 |
| pooled | rush | 0.9-1 | 41 | 0.910 | 0.856 | 38 | 0.917 | 0.886 | 20 | 0.909 | 0.978 |

## Verdict

**1. The look-ahead is real and now fixed in the experiment rows; the rec/rush adoption holds (stronger for receivers).**

- The fix adds rows only (no rec/rush row is lost): 8% more receiver rows, 10% more rusher rows in 2019-25, and in
  about a quarter of the passer team-weeks the projected starter changes (the inactive starter comes back, the backup
  he displaced leaves). The report features now look like 2016-18 again: players listed Out 4.3% of 2016-18 rows,
  3.9% / 3.2% of 2019-22 / 2023-25 (was 0.1% / 0.0%); INA players 8.5% / 8.3% of the rows.
- The live data confirm it is look-ahead: `roster_weekly_2026` (pulled Thu 24 Sep) has 200 and 202 INA in weeks 1
  and 2 (already played) and none in week 3 (not yet played), so the page midweek sees the as-of week's inactives as
  ACT. Once a week is played its INA are stamped, so `roster_at` also drops last week's inactives on the live page
  whenever the current week's roster is not yet out.
- Flat MAE, old -> corrected: rec 125.2 -> 125.8 (2019-22), 124.0 -> 123.1 (2023-25); rush 155.8 -> 152.0,
  142.6 -> 143.1; pass 582.4 -> 611.6, 626.2 -> 621.6. The levels move both ways because the row sets differ; the
  cleaner measure is on the rows that were missing: flat over-projects them (bias +72 / +57 yards rec, +69 / +43 rush),
  as expected for players who were inactive that week. So the old numbers flattered flat's bias (rec -5.8 -> +0.5,
  rush -28.6 -> -18.6 on 2019-22) more than its MAE.
- The adopted pooled-logit `mult` gains more against flat on the corrected rows: rec +1.45 / +2.67 -> +2.63 / +2.61
  (smaller gain 1.45 -> 2.61; worst week 2023-25 wk 1, +0.21), rush +3.24 / +3.46 -> +3.89 / +3.13 (smaller gain 3.13;
  no as-of week worse). On the added rows `mult` cuts the receiver MAE 132.3 -> 116.3 and 112.5 -> 110.5, the rusher
  118.6 -> 109.1 and 147.0 -> 146.9. The look-ahead hid part of the availability model's value, it did not create it.
- Rows with residual timing risk (not fixed here, the same in every season): a player moved to a reserve list during
  the as-of week before its games is absent at week w but was on the 53 at w-1: about 5 (2016-18) and 8 (2019-25)
  QB/RB/WR/TE per as-of week, before the volume filter; small against the ~63 INA per week.

**2. Passers: the pre-registered passer logit (`pmult`) passes and is adopted for passing.**

- MAE 611.6 -> 575.9 (2019-22, +35.7) and 621.6 -> 602.9 (2023-25, +18.7); g = 18.7; every as-of week in both windows
  is better (least: 2023-25 week 5, -11.5). Within 20%: 0.504 -> 0.522 and 0.490 -> 0.484; games miss 3.88 -> 2.48 and
  3.61 -> 2.54. `pshare` fails (2023-25 +18.7 worse); today's pooled `mult` fails (2023-25 +3.9 worse).
- Constants (2016-18): AVAIL pass 0.525 -> 0.625, BLEND pass 0.75 -> 0.5, lam 1, pbar 0.7250, i.e. share =
  min(1, 0.8621 p). The passer logit leans on the missed rate over the last 34 team games (-3.30), young (<24, +2.41),
  share of games so far (+1.43), Out (-0.92), DNP (-0.54), missed last game (-0.43); Doubtful, ir_prev and
  ir_season never occur for 2016-18 passers and get 0.
- Caveat: the rule was written after today's study had seen the per-kind result on the old rows (+36.3 / +14.2),
  and three quarters of the corrected passer rows are the same rows, so this is a re-test on corrected rows, not an
  independent confirmation. It improved on the corrected rows (2023-25 gain 14.2 -> 18.7, worst week +8.6 -> -11.5).
  The passer model's p is over-confident at the top in the test windows (0.9-1 band: 0.949 predicted vs 0.880 realised
  on 2019-22, 0.936 vs 0.863 on 2023-25); the fitted AVAIL (0.625 x p / 0.725) absorbs the level.

**3. Calibration on the corrected rows** (pooled logit, games-left weighted, predicted vs realised): rec 0.755 vs
0.739 (2019-22), 0.771 vs 0.748 (2023-25); rush 0.730 vs 0.716, 0.733 vs 0.725; pass (pooled) 0.713 vs 0.696,
0.697 vs 0.647; pass (passer logit) 0.713 vs 0.696, 0.677 vs 0.647. Slightly high everywhere after 2018 (1.5-5 points),
compressed at the ends for rec (low bands under-predict); the mult variants refit the level, so this does not reach the
season totals.

Runtimes: fresh rows 411 s wall (28 season-weeks built at 23-33 s each on 2 workers; the 11 of 2016-18 copied from
today's build after checking those seasons have no INA); features + both logits + scoring on both rowsets 29 s.
