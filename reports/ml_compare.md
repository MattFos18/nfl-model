# Machine-learning comparison: ridge, lasso, boosting, forests and a neural network (29 Sep 2026)

`experiments/ml_compare.py`. Matt found a published study comparing linear regression, gradient boosting and a neural
network for NFL totals and spreads, each on three feature sets (forward selection, lasso-selected, all variables),
reporting RMSE and "classification accuracy" at betting thresholds (totals about 13.0 RMSE and 55-57% at small
thresholds with at least 500 bets; spreads about 12.8 RMSE, boosting best at high thresholds). This runs the same
comparison on our data, walk-forward, against the live model.

## Adoption rule (written before any result was seen)

A model, or a stacked blend of the live model with a model, replaces or joins the live one only if

- **spreads:** its margin MAE is lower than the live model's on all three windows (2015-18, 2019-22, 2023-25) AND its
  4+ spread-edge record (regular season, weeks 1 to 17, pushes dropped) is not worse than the live model's on any
  window (not worse = win rate at least the live rate; fewer bets at the same or a better rate is not worse);
- **totals:** its total MAE is lower than the live model's on all three windows AND its record on unders with the
  model total 3+ points below the line (the totals flag) is not worse than the live model's on any window.

Caveats fixed in advance: the boosting and network grids, the forward selection and the stacking weights are all
chosen on 2013-18 data, so 2015-18 is in-sample for those choices and only 2019-22 and 2023-25 are clean for them;
that biases the comparison toward the challengers, not against them. The study-style threshold is chosen on
2015-18 and reported on the later windows; the "best threshold with 500+ bets over 2015-25" figure the study
reports is shown too, labelled as look-ahead.


## Reading of the results (written after them)

**Verdict: nothing is adopted.** No model and no stacked blend passes the rule on spreads or on totals (the full
table is under Results and in `reports/ml_compare.csv`, one row per model x features x target x window, then the
study-style rows).

- **Spreads.** No challenger beats the live seven-model average on margin MAE in all three windows. The best
  standalone models are the live-input ridge (it is the live equation) and lasso on the live inputs (9.979 / 10.034 /
  9.925 against 9.949 / 10.020 / 9.904). Boosting, forests and the MLP all miss by more (boosting on the live inputs
  10.002 / 10.063 / 9.987; MLP 10.08 to 10.48). Adding every new-signal family (set 2) makes every model worse on
  2019-22 and 2023-25; the lasso-selected subset does not rescue it; forward selection on 2013-18 wins 2015-18
  (where it was chosen: 9.90) and loses both later windows. The stacks that come closest (live + boosting on the wide
  or lasso set, w 0.15-0.2; live + forest on the lasso set, w 0.1) gain 0.007 to 0.014 on 2019-22 and lose 0.002 to
  0.004 on 2023-25, and each takes fewer, weaker 4+ bets on 2019-22 (69-47, 73-51, 73-48 against 80-51).
- **Totals.** Nothing beats the live total equation on all three windows. Its own re-fit here (ridge on set 1, the
  total target) reproduces it exactly. Stacks with the lasso-selected ridge or lasso totals (w 0.2-0.25) are
  0.014-0.019 better on 2015-18 (where w was fitted) and 2019-22, and 0.003-0.004 worse on 2023-25, where their
  under 3+ record is also worse (20-18 against 21-16). Boosting, forests and the MLP are 0.08 to 0.7 worse than the equation on the
  later windows. Forward-selected totals win 2015-18 (in sample) by 0.26 and lose 2023-25 by 0.19.
- **The published study's style.** On RMSE our live model is 12.88 (spreads) and 13.32 (totals) over 2015-25; the
  closing line is 12.73 and 13.19. The study's ~12.8 and ~13.0 sit at the line's level, which no model reaches here.
  The "accuracy at a threshold" figure is the pitfall: picking the best share of the line after seeing 2015-25 gives
  55-59% on totals for almost every model (live model 55.7% at 6.5% of the line on 752 bets), the same range as the
  study's 55-57%. Choosing the share on 2015-18 and scoring later windows, the live model's totals go 58.5% on
  2019-22 and 50.3% on 2023-25; most rows land at 50-54% on 2023-25. Spreads peak at the grid's edge
  (edge 50% of the line) at 50-55% look-ahead, and 46-54% on 2023-25 when picked honestly.
  One row holds up out of sample: team-point boosting on the live inputs, summed to a total and bet both ways at
  8.5%+ of the line, went 60.9% (225) on 2015-18, 58.1% (210) on 2019-22 and 53.8% (184) on 2023-25. The live trees'
  own sum does the same at 9.5% (58.4 / 56.4 / 60.4%). That is one or two rows of about 45 tried, and the same
  models' under 3+ records are weaker than the live flag's, so it is a lead to log, not an edge.
- **Caveats.** The boosting, forest and MLP settings, the forward selection and the stack weights were all chosen on
  2013-18 data, so 2015-18 is in sample for them and only 2019-22 and 2023-25 are clean; the bias favours the
  challengers and they still lost. The forest's grid chose its smallest leaf (25) on every set; the MLP is one seed.
  The forest and MLP refit every 4 weeks, the others every week. Bet records are weeks 1-17 of the regular season,
  with pushes dropped; the live records reproduce the ones on the site (68-55 / 80-51 / 40-21; 61-46 / 95-50 / 21-16).

## Results

Inputs: set 1 is 22 points inputs / 12 total inputs; set 2 is 94 / 105; set 4 (forward, ridge, chosen on 2013-18 only): points qb_rating, def_pf, home, off_pf, skill_out_value, opp_def_turnover_early, o_avg_start_ytg, o_def_explosive_rate, turnover_rate, wind_out, o_third_conv, neutral, off_turnover_early, rz_td_rate, explosive_rate, def_explosive_rate, third_conv, streak, o_pen_def; total qb_sum, s_def_explosive_rate, qb_form_sum, s_opp_def_snap_out, wind_out, ref_tot, s_sec_per_play, s_opp_def_turnover_early, s_off_turnover_early, s_pen_def, s_def_turnover_rate. Set 3 is refit inside every refit (a LassoCV on the training rows). No input reads a line (asserted by name; the wide inputs' largest correlation with the market's implied points is the offense and defense ratings, as it should be).

Tuned on 2013-18 (season refits, validation 2015-18): hgb: points/live {'max_iter': 300, 'learning_rate': 0.03, 'max_leaf_nodes': 4, 'min_samples_leaf': 100, 'l2_regularization': 1.0}, points/wide {'max_iter': 500, 'learning_rate': 0.02, 'max_depth': 2, 'min_samples_leaf': 200, 'l2_regularization': 3.0}, points/lasso {'max_iter': 300, 'learning_rate': 0.03, 'max_leaf_nodes': 4, 'min_samples_leaf': 100, 'l2_regularization': 1.0}, points/forward {'max_iter': 300, 'learning_rate': 0.03, 'max_leaf_nodes': 4, 'min_samples_leaf': 100, 'l2_regularization': 1.0}, total/live {'max_iter': 500, 'learning_rate': 0.02, 'max_depth': 2, 'min_samples_leaf': 200, 'l2_regularization': 3.0}, total/wide {'max_iter': 500, 'learning_rate': 0.02, 'max_depth': 2, 'min_samples_leaf': 200, 'l2_regularization': 3.0}, total/lasso {'max_iter': 500, 'learning_rate': 0.02, 'max_depth': 2, 'min_samples_leaf': 200, 'l2_regularization': 3.0}, total/forward {'max_iter': 500, 'learning_rate': 0.02, 'max_depth': 2, 'min_samples_leaf': 200, 'l2_regularization': 3.0}; mlp: points/live {'hidden_layer_sizes': [32], 'alpha': 1.0}, points/wide {'hidden_layer_sizes': [64, 32], 'alpha': 1.0}, points/lasso {'hidden_layer_sizes': [64, 32], 'alpha': 1.0}, points/forward {'hidden_layer_sizes': [8], 'alpha': 0.01}, total/live {'hidden_layer_sizes': [32, 16], 'alpha': 0.1}, total/wide {'hidden_layer_sizes': [64, 32], 'alpha': 1.0}, total/lasso {'hidden_layer_sizes': [32, 16], 'alpha': 0.1}, total/forward {'hidden_layer_sizes': [64, 32], 'alpha': 1.0}; rf: points/live {'min_samples_leaf': 25}, points/wide {'min_samples_leaf': 25}, points/lasso {'min_samples_leaf': 25}, points/forward {'min_samples_leaf': 25}, total/live {'min_samples_leaf': 25}, total/wide {'min_samples_leaf': 25}, total/lasso {'min_samples_leaf': 25}, total/forward {'min_samples_leaf': 25}

### Spreads: team points and margin (model of each team's points)

| model            | features   | team MAE/RMSE 2015-18   | team MAE/RMSE 2019-22   | team MAE/RMSE 2023-25   | margin MAE/RMSE 2015-18   | margin MAE/RMSE 2019-22   | margin MAE/RMSE 2023-25   | 4+ 2015-18   | 4+ 2019-22   | 4+ 2023-25   |
|:-----------------|:-----------|:------------------------|:------------------------|:------------------------|:--------------------------|:--------------------------|:--------------------------|:-------------|:-------------|:-------------|
| live model       | live       | 7.409 / 9.379           | 7.348 / 9.257           | 7.262 / 9.130           | 9.949 / 12.891            | 10.020 / 12.933           | 9.904 / 12.803            | 68-55        | 80-51        | 40-21        |
| live ridge alone | live       | 7.397 / 9.410           | 7.344 / 9.269           | 7.274 / 9.167           | 9.962 / 12.905            | 10.030 / 12.939           | 9.914 / 12.816            | 61-58        | 81-55        | 40-23        |
| live trees alone | live       | 7.470 / 9.491           | 7.419 / 9.373           | 7.301 / 9.190           | 10.087 / 13.119           | 10.158 / 13.104           | 9.986 / 12.874            | 136-121      | 126-98       | 60-33        |
| ridge            | live       | 7.397 / 9.410           | 7.344 / 9.269           | 7.274 / 9.167           | 9.962 / 12.905            | 10.030 / 12.939           | 9.914 / 12.816            | 61-58        | 81-55        | 40-23        |
| ridge            | wide       | 7.604 / 9.664           | 7.401 / 9.335           | 7.311 / 9.198           | 10.208 / 13.212           | 10.195 / 13.046           | 9.982 / 12.826            | 104-109      | 121-95       | 61-50        |
| ridge            | lasso      | 7.489 / 9.497           | 7.371 / 9.300           | 7.296 / 9.183           | 10.084 / 13.038           | 10.168 / 13.039           | 10.002 / 12.848           | 99-106       | 89-82        | 57-43        |
| ridge            | forward    | 7.301 / 9.303           | 7.395 / 9.333           | 7.297 / 9.208           | 9.901 / 12.801            | 10.062 / 12.960           | 9.972 / 12.868            | 78-56        | 89-72        | 48-41        |
| lasso            | live       | 7.397 / 9.391           | 7.355 / 9.280           | 7.277 / 9.167           | 9.979 / 12.915            | 10.034 / 12.953           | 9.925 / 12.835            | 58-46        | 72-53        | 40-19        |
| lasso            | wide       | 7.439 / 9.415           | 7.373 / 9.287           | 7.297 / 9.183           | 10.032 / 12.973           | 10.069 / 12.974           | 9.990 / 12.904            | 74-67        | 64-57        | 37-27        |
| lasso            | lasso      | 7.471 / 9.470           | 7.367 / 9.294           | 7.291 / 9.178           | 10.057 / 13.002           | 10.145 / 13.024           | 9.990 / 12.848            | 90-95        | 86-74        | 53-42        |
| lasso            | forward    | 7.309 / 9.315           | 7.382 / 9.312           | 7.298 / 9.206           | 9.908 / 12.822            | 10.038 / 12.955           | 9.982 / 12.883            | 67-50        | 77-63        | 46-31        |
| hgb              | live       | 7.394 / 9.406           | 7.395 / 9.329           | 7.339 / 9.205           | 10.002 / 13.014           | 10.063 / 13.025           | 9.987 / 12.918            | 101-89       | 107-80       | 44-32        |
| hgb              | wide       | 7.487 / 9.486           | 7.423 / 9.342           | 7.367 / 9.215           | 10.081 / 13.103           | 10.029 / 12.994           | 10.035 / 12.955           | 113-96       | 85-71        | 49-45        |
| hgb              | lasso      | 7.463 / 9.465           | 7.424 / 9.356           | 7.363 / 9.226           | 10.070 / 13.025           | 10.077 / 13.033           | 10.039 / 12.962           | 112-97       | 95-82        | 50-38        |
| hgb              | forward    | 7.377 / 9.372           | 7.420 / 9.355           | 7.356 / 9.235           | 9.960 / 12.920            | 10.070 / 13.002           | 9.994 / 12.952            | 132-83       | 118-85       | 57-46        |
| rf               | live       | 7.443 / 9.437           | 7.430 / 9.340           | 7.370 / 9.246           | 10.104 / 13.083           | 10.073 / 13.011           | 10.034 / 12.986           | 97-86        | 102-91       | 49-41        |
| rf               | wide       | 7.496 / 9.504           | 7.471 / 9.366           | 7.438 / 9.312           | 10.181 / 13.189           | 10.056 / 13.008           | 10.123 / 13.147           | 125-119      | 113-95       | 49-58        |
| rf               | lasso      | 7.487 / 9.481           | 7.464 / 9.364           | 7.389 / 9.264           | 10.122 / 13.134           | 10.049 / 13.019           | 10.075 / 13.068           | 121-98       | 105-89       | 53-53        |
| rf               | forward    | 7.433 / 9.426           | 7.456 / 9.358           | 7.398 / 9.270           | 10.035 / 13.055           | 10.066 / 13.009           | 10.050 / 13.034           | 119-90       | 120-93       | 51-54        |
| mlp              | live       | 7.612 / 9.639           | 7.459 / 9.422           | 7.357 / 9.264           | 10.284 / 13.280           | 10.248 / 13.126           | 10.085 / 13.016           | 147-142      | 139-119      | 55-47        |
| mlp              | wide       | 7.820 / 9.877           | 7.610 / 9.576           | 7.462 / 9.358           | 10.479 / 13.575           | 10.429 / 13.316           | 10.275 / 13.135           | 203-190      | 172-151      | 100-89       |
| mlp              | lasso      | 7.649 / 9.659           | 7.526 / 9.490           | 7.406 / 9.300           | 10.107 / 13.106           | 10.288 / 13.191           | 10.223 / 13.091           | 144-133      | 158-127      | 88-92        |
| mlp              | forward    | 7.471 / 9.512           | 7.553 / 9.531           | 7.437 / 9.349           | 10.121 / 13.104           | 10.241 / 13.218           | 10.121 / 12.992           | 195-146      | 159-141      | 80-71        |

### Totals (the total direct, and the sum of the two team scores)

| model            | features   | target   | total MAE/RMSE 2015-18   | total MAE/RMSE 2019-22   | total MAE/RMSE 2023-25   | under 3+ 2015-18   | under 3+ 2019-22   | under 3+ 2023-25   |
|:-----------------|:-----------|:---------|:-------------------------|:-------------------------|:-------------------------|:-------------------|:-------------------|:-------------------|
| live model       | live       | live     | 10.744 / 13.628          | 10.541 / 13.247          | 10.177 / 13.021          | 61-46              | 95-50              | 21-16              |
| live ridge alone | live       | points   | 10.799 / 13.700          | 10.585 / 13.275          | 10.315 / 13.111          | 75-55              | 81-63              | 12-11              |
| live trees alone | live       | points   | 10.763 / 13.718          | 10.612 / 13.404          | 10.221 / 13.118          | 121-95             | 107-79             | 21-22              |
| ridge            | live       | points   | 10.799 / 13.700          | 10.585 / 13.275          | 10.315 / 13.111          | 75-55              | 81-63              | 12-11              |
| ridge            | wide       | points   | 11.166 / 14.107          | 10.706 / 13.355          | 10.386 / 13.188          | 102-121            | 95-74              | 19-28              |
| ridge            | lasso      | points   | 10.885 / 13.812          | 10.611 / 13.264          | 10.293 / 13.126          | 93-86              | 94-61              | 18-28              |
| ridge            | forward    | points   | 10.625 / 13.501          | 10.687 / 13.432          | 10.322 / 13.174          | 76-52              | 113-105            | 34-33              |
| ridge            | live       | total    | 10.744 / 13.628          | 10.541 / 13.247          | 10.177 / 13.021          | 61-46              | 95-50              | 21-16              |
| ridge            | wide       | total    | 11.151 / 14.099          | 10.716 / 13.329          | 10.387 / 13.211          | 123-121            | 105-87             | 23-31              |
| ridge            | lasso      | total    | 10.962 / 13.924          | 10.590 / 13.223          | 10.259 / 13.113          | 98-107             | 88-57              | 27-39              |
| ridge            | forward    | total    | 10.482 / 13.373          | 10.512 / 13.224          | 10.369 / 13.230          | 94-59              | 97-75              | 56-57              |
| lasso            | live       | points   | 10.736 / 13.636          | 10.599 / 13.294          | 10.293 / 13.092          | 60-39              | 76-64              | 12-11              |
| lasso            | wide       | points   | 10.755 / 13.648          | 10.604 / 13.292          | 10.257 / 13.069          | 62-52              | 78-52              | 9-18               |
| lasso            | lasso      | points   | 10.852 / 13.774          | 10.607 / 13.263          | 10.285 / 13.111          | 88-75              | 91-60              | 16-26              |
| lasso            | forward    | points   | 10.629 / 13.515          | 10.656 / 13.380          | 10.314 / 13.153          | 70-49              | 96-91              | 29-27              |
| lasso            | live       | total    | 10.744 / 13.633          | 10.545 / 13.255          | 10.183 / 13.020          | 58-48              | 90-52              | 19-15              |
| lasso            | wide       | total    | 10.804 / 13.692          | 10.567 / 13.224          | 10.225 / 13.054          | 63-57              | 77-48              | 18-22              |
| lasso            | lasso      | total    | 10.926 / 13.877          | 10.575 / 13.212          | 10.240 / 13.090          | 93-102             | 84-55              | 23-28              |
| lasso            | forward    | total    | 10.495 / 13.396          | 10.520 / 13.228          | 10.370 / 13.230          | 76-52              | 94-73              | 55-54              |
| hgb              | live       | points   | 10.617 / 13.583          | 10.599 / 13.361          | 10.262 / 13.116          | 106-65             | 105-82             | 17-23              |
| hgb              | wide       | points   | 10.726 / 13.721          | 10.703 / 13.424          | 10.290 / 13.107          | 81-68              | 83-71              | 18-19              |
| hgb              | lasso      | points   | 10.784 / 13.736          | 10.677 / 13.427          | 10.276 / 13.132          | 92-79              | 89-71              | 20-22              |
| hgb              | forward    | points   | 10.640 / 13.581          | 10.675 / 13.455          | 10.284 / 13.167          | 85-66              | 116-94             | 36-37              |
| hgb              | live       | total    | 10.715 / 13.694          | 10.697 / 13.429          | 10.307 / 13.161          | 78-65              | 111-73             | 36-32              |
| hgb              | wide       | total    | 10.703 / 13.720          | 10.671 / 13.361          | 10.305 / 13.166          | 92-81              | 92-61              | 31-32              |
| hgb              | lasso      | total    | 10.713 / 13.666          | 10.620 / 13.314          | 10.300 / 13.175          | 104-98             | 92-59              | 30-36              |
| hgb              | forward    | total    | 10.580 / 13.569          | 10.676 / 13.417          | 10.359 / 13.269          | 110-72             | 96-79              | 57-56              |
| rf               | live       | points   | 10.686 / 13.603          | 10.700 / 13.405          | 10.338 / 13.165          | 55-35              | 87-63              | 12-10              |
| rf               | wide       | points   | 10.778 / 13.687          | 10.786 / 13.479          | 10.377 / 13.191          | 54-47              | 63-59              | 14-14              |
| rf               | lasso      | points   | 10.772 / 13.678          | 10.741 / 13.463          | 10.293 / 13.135          | 62-52              | 75-73              | 12-12              |
| rf               | forward    | points   | 10.712 / 13.601          | 10.723 / 13.456          | 10.345 / 13.185          | 50-36              | 78-70              | 23-26              |
| rf               | live       | total    | 10.748 / 13.720          | 10.689 / 13.395          | 10.297 / 13.140          | 55-51              | 83-66              | 17-15              |
| rf               | wide       | total    | 10.826 / 13.791          | 10.753 / 13.418          | 10.318 / 13.168          | 53-60              | 70-53              | 17-20              |
| rf               | lasso      | total    | 10.765 / 13.724          | 10.709 / 13.356          | 10.290 / 13.143          | 56-64              | 72-50              | 15-21              |
| rf               | forward    | total    | 10.642 / 13.589          | 10.756 / 13.427          | 10.313 / 13.185          | 79-62              | 87-78              | 37-43              |
| mlp              | live       | points   | 11.077 / 13.973          | 10.706 / 13.521          | 10.425 / 13.185          | 113-91             | 114-98             | 18-20              |
| mlp              | wide       | points   | 11.251 / 14.351          | 10.984 / 13.767          | 10.549 / 13.333          | 135-113            | 133-121            | 42-67              |
| mlp              | lasso      | points   | 11.271 / 14.191          | 10.907 / 13.647          | 10.419 / 13.212          | 116-132            | 130-107            | 46-50              |
| mlp              | forward    | points   | 10.935 / 13.790          | 10.934 / 13.736          | 10.534 / 13.447          | 118-76             | 144-122            | 41-51              |
| mlp              | live       | total    | 10.828 / 13.806          | 10.791 / 13.493          | 10.342 / 13.125          | 78-72              | 107-90             | 40-34              |
| mlp              | wide       | total    | 11.357 / 14.539          | 11.256 / 14.034          | 10.690 / 13.474          | 149-153            | 152-136            | 87-86              |
| mlp              | lasso      | total    | 11.391 / 14.586          | 10.888 / 13.655          | 10.628 / 13.456          | 136-137            | 132-100            | 70-77              |
| mlp              | forward    | total    | 10.622 / 13.580          | 10.784 / 13.549          | 10.399 / 13.301          | 109-87             | 137-112            | 72-71              |

The closing line for scale: margin MAE/RMSE 2015-18 9.805 / 12.745, 2019-22 9.888 / 12.773, 2023-25 9.745 / 12.653; total 2015-18 10.552 / 13.359, 2019-22 10.541 / 13.200, 2023-25 10.121 / 12.959.

### Stacked blends, spread: live + w x (model - live), w on a 0.05 grid fitted on 2015-18 by MAE

Live for reference: 2015-18 9.949 (68-55), 2019-22 10.020 (80-51), 2023-25 9.904 (40-21)

| blend            | features   | ML target   |   w (2015-18) |   margin MAE 2015-18 |   margin MAE 2019-22 |   margin MAE 2023-25 | 4+ 2015-18   | 4+ 2019-22   | 4+ 2023-25   |
|:-----------------|:-----------|:------------|--------------:|---------------------:|---------------------:|---------------------:|:-------------|:-------------|:-------------|
| stack live+ridge | live       | points      |          0    |                9.949 |               10.02  |                9.904 | 68-55        | 80-51        | 40-21        |
| stack live+ridge | wide       | points      |          0    |                9.949 |               10.02  |                9.904 | 68-55        | 80-51        | 40-21        |
| stack live+ridge | lasso      | points      |          0.05 |                9.949 |               10.022 |                9.904 | 65-55        | 78-48        | 39-22        |
| stack live+ridge | forward    | points      |          0.7  |                9.895 |               10.031 |                9.94  | 64-49        | 78-65        | 40-32        |
| stack live+lasso | live       | points      |          0    |                9.949 |               10.02  |                9.904 | 68-55        | 80-51        | 40-21        |
| stack live+lasso | wide       | points      |          0.1  |                9.947 |               10.017 |                9.906 | 65-50        | 78-48        | 38-22        |
| stack live+lasso | lasso      | points      |          0.1  |                9.948 |               10.023 |                9.904 | 63-54        | 75-51        | 38-23        |
| stack live+lasso | forward    | points      |          0.65 |                9.898 |               10.011 |                9.941 | 51-42        | 74-57        | 40-29        |
| stack live+hgb   | live       | points      |          0.35 |                9.94  |               10.019 |                9.914 | 70-57        | 82-56        | 36-22        |
| stack live+hgb   | wide       | points      |          0.15 |                9.942 |               10.007 |                9.906 | 63-49        | 69-47        | 40-21        |
| stack live+hgb   | lasso      | points      |          0.2  |                9.94  |               10.013 |                9.908 | 67-50        | 73-51        | 37-21        |
| stack live+hgb   | forward    | points      |          0.45 |                9.888 |               10.006 |                9.916 | 69-45        | 77-63        | 38-24        |
| stack live+rf    | live       | points      |          0    |                9.949 |               10.02  |                9.904 | 68-55        | 80-51        | 40-21        |
| stack live+rf    | wide       | points      |          0.05 |                9.948 |               10.011 |                9.906 | 65-49        | 76-49        | 40-21        |
| stack live+rf    | lasso      | points      |          0.1  |                9.945 |               10.006 |                9.906 | 61-48        | 73-48        | 39-22        |
| stack live+rf    | forward    | points      |          0.3  |                9.925 |                9.989 |                9.917 | 59-43        | 70-57        | 34-24        |
| stack live+mlp   | live       | points      |          0    |                9.949 |               10.02  |                9.904 | 68-55        | 80-51        | 40-21        |
| stack live+mlp   | wide       | points      |          0    |                9.949 |               10.02  |                9.904 | 68-55        | 80-51        | 40-21        |
| stack live+mlp   | lasso      | points      |          0.25 |                9.927 |               10.025 |                9.931 | 65-58        | 78-55        | 36-27        |
| stack live+mlp   | forward    | points      |          0.35 |                9.889 |               10.042 |                9.933 | 81-63        | 79-71        | 46-28        |

### Stacked blends, total: live + w x (model - live), w on a 0.05 grid fitted on 2015-18 by MAE

Live for reference: 2015-18 10.744 (61-46), 2019-22 10.541 (95-50), 2023-25 10.177 (21-16)

| blend            | features   | ML target   |   w (2015-18) |   total MAE 2015-18 |   total MAE 2019-22 |   total MAE 2023-25 | under 3+ 2015-18   | under 3+ 2019-22   | under 3+ 2023-25   |
|:-----------------|:-----------|:------------|--------------:|--------------------:|--------------------:|--------------------:|:-------------------|:-------------------|:-------------------|
| stack live+ridge | live       | points      |          0.4  |              10.716 |              10.526 |              10.2   | 43-36              | 82-39              | 9-9                |
| stack live+ridge | wide       | points      |          0.15 |              10.731 |              10.535 |              10.186 | 54-38              | 86-45              | 17-14              |
| stack live+ridge | lasso      | points      |          0.25 |              10.716 |              10.524 |              10.181 | 56-38              | 84-39              | 14-14              |
| stack live+ridge | forward    | points      |          0.7  |              10.602 |              10.6   |              10.25  | 63-33              | 98-81              | 17-18              |
| stack live+ridge | live       | total       |          0    |              10.744 |              10.541 |              10.177 | 61-46              | 95-50              | 21-16              |
| stack live+ridge | wide       | total       |          0.2  |              10.727 |              10.538 |              10.198 | 59-41              | 93-46              | 16-14              |
| stack live+ridge | lasso      | total       |          0.2  |              10.726 |              10.526 |              10.18  | 63-47              | 91-42              | 20-18              |
| stack live+ridge | forward    | total       |          1    |              10.482 |              10.512 |              10.369 | 94-59              | 97-75              | 56-57              |
| stack live+lasso | live       | points      |          0.55 |              10.699 |              10.544 |              10.213 | 45-24              | 78-40              | 6-9                |
| stack live+lasso | wide       | points      |          0.45 |              10.698 |              10.542 |              10.193 | 48-32              | 81-40              | 12-10              |
| stack live+lasso | lasso      | points      |          0.3  |              10.714 |              10.525 |              10.184 | 55-34              | 84-39              | 13-12              |
| stack live+lasso | forward    | points      |          0.7  |              10.608 |              10.588 |              10.246 | 58-32              | 88-65              | 16-17              |
| stack live+lasso | live       | total       |          0.4  |              10.74  |              10.54  |              10.178 | 60-45              | 93-50              | 21-16              |
| stack live+lasso | wide       | total       |          0.35 |              10.709 |              10.53  |              10.183 | 56-38              | 83-40              | 16-14              |
| stack live+lasso | lasso      | total       |          0.25 |              10.725 |              10.527 |              10.181 | 63-47              | 87-43              | 20-18              |
| stack live+lasso | forward    | total       |          1    |              10.495 |              10.52  |              10.37  | 76-52              | 94-73              | 55-54              |
| stack live+hgb   | live       | points      |          0.7  |              10.577 |              10.539 |              10.19  | 74-42              | 91-60              | 11-16              |
| stack live+hgb   | wide       | points      |          0.5  |              10.642 |              10.568 |              10.187 | 52-38              | 71-44              | 12-10              |
| stack live+hgb   | lasso      | points      |          0.45 |              10.675 |              10.554 |              10.181 | 53-42              | 79-48              | 12-10              |
| stack live+hgb   | forward    | points      |          0.6  |              10.601 |              10.562 |              10.183 | 55-39              | 94-62              | 17-15              |
| stack live+hgb   | live       | total       |          0.6  |              10.654 |              10.596 |              10.229 | 57-51              | 99-68              | 23-20              |
| stack live+hgb   | wide       | total       |          0.55 |              10.631 |              10.562 |              10.203 | 62-54              | 88-50              | 20-14              |
| stack live+hgb   | lasso      | total       |          0.5  |              10.64  |              10.521 |              10.192 | 61-58              | 88-47              | 18-15              |
| stack live+hgb   | forward    | total       |          0.65 |              10.556 |              10.574 |              10.255 | 67-53              | 86-59              | 35-36              |
| stack live+rf    | live       | points      |          0.6  |              10.636 |              10.592 |              10.227 | 41-25              | 86-40              | 7-8                |
| stack live+rf    | wide       | points      |          0.45 |              10.686 |              10.603 |              10.225 | 37-30              | 66-37              | 10-8               |
| stack live+rf    | lasso      | points      |          0.45 |              10.683 |              10.582 |              10.185 | 42-34              | 70-47              | 11-6               |
| stack live+rf    | forward    | points      |          0.55 |              10.66  |              10.591 |              10.214 | 42-28              | 82-52              | 17-11              |
| stack live+rf    | live       | total       |          0.45 |              10.699 |              10.576 |              10.211 | 45-38              | 84-55              | 16-10              |
| stack live+rf    | wide       | total       |          0.35 |              10.71  |              10.578 |              10.197 | 45-41              | 72-43              | 15-12              |
| stack live+rf    | lasso      | total       |          0.4  |              10.694 |              10.564 |              10.194 | 43-41              | 74-39              | 13-9               |
| stack live+rf    | forward    | total       |          0.65 |              10.615 |              10.634 |              10.233 | 56-49              | 82-59              | 24-28              |
| stack live+mlp   | live       | points      |          0.2  |              10.722 |              10.531 |              10.185 | 56-44              | 94-45              | 15-12              |
| stack live+mlp   | wide       | points      |          0.2  |              10.711 |              10.538 |              10.199 | 58-38              | 85-54              | 17-15              |
| stack live+mlp   | lasso      | points      |          0.1  |              10.743 |              10.543 |              10.175 | 58-49              | 91-49              | 19-14              |
| stack live+mlp   | forward    | points      |          0.35 |              10.659 |              10.575 |              10.244 | 59-27              | 95-58              | 13-16              |
| stack live+mlp   | live       | total       |          0.4  |              10.716 |              10.585 |              10.206 | 59-41              | 96-65              | 24-17              |
| stack live+mlp   | wide       | total       |          0.15 |              10.716 |              10.569 |              10.181 | 63-50              | 83-47              | 20-20              |
| stack live+mlp   | lasso      | total       |          0.05 |              10.74  |              10.538 |              10.181 | 62-44              | 97-46              | 20-15              |
| stack live+mlp   | forward    | total       |          0.65 |              10.582 |              10.632 |              10.267 | 78-54              | 111-80             | 46-38              |

### The study's style: accuracy of the model's side when the edge is at least a share of the line

Totals: shares 0 to 10% of the total line (0.5% steps); spreads: 0 to 50% of the spread line (5% steps); weeks 1-17, pushes out. "Look-ahead" is what the study reports: the best share over 2015-25 pooled with 500+ bets, chosen after seeing every result. "Picked on 2015-18" chooses the share on 2015-18 only (at least 182 bets there: 500 pro-rated to four of eleven seasons) and reports every window at that share, accuracy (bets); only 2019-22 and 2023-25 are out of sample. Break-even at -110 is 52.4%.

**Totals**

| model            | features   | target   |   RMSE 2015-25 |   acc, every game | look-ahead best (share, acc, bets)   |   share picked on 2015-18 | 2015-18      | 2019-22      | 2023-25     |
|:-----------------|:-----------|:---------|---------------:|------------------:|:-------------------------------------|--------------------------:|:-------------|:-------------|:------------|
| live model       | live       | live     |          13.32 |             0.513 | 0.065, 0.557, 752                    |                     0.075 | 0.553 (190)  | 0.585 (200)  | 0.503 (189) |
| live ridge alone | live       | points   |          13.38 |             0.511 | 0.08, 0.527, 554                     |                     0.08  | 0.534 (193)  | 0.532 (188)  | 0.514 (173) |
| live trees alone | live       | points   |          13.44 |             0.522 | 0.095, 0.583, 599                    |                     0.095 | 0.584 (238)  | 0.564 (202)  | 0.604 (159) |
| ridge            | live       | points   |          13.38 |             0.511 | 0.08, 0.527, 554                     |                     0.08  | 0.534 (193)  | 0.532 (188)  | 0.514 (173) |
| ridge            | wide       | points   |          13.58 |             0.499 | 0.01, 0.506, 2465                    |                     0     | 0.495 (1015) | 0.514 (1011) | 0.485 (763) |
| ridge            | lasso      | points   |          13.42 |             0.506 | 0.025, 0.519, 1989                   |                     0.03  | 0.510 (677)  | 0.529 (656)  | 0.508 (474) |
| ridge            | forward    | points   |          13.38 |             0.507 | 0.08, 0.547, 541                     |                     0.065 | 0.558 (240)  | 0.524 (332)  | 0.505 (206) |
| ridge            | live       | total    |          13.32 |             0.513 | 0.065, 0.557, 752                    |                     0.075 | 0.553 (190)  | 0.585 (200)  | 0.503 (189) |
| ridge            | wide       | total    |          13.57 |             0.5   | 0.09, 0.530, 713                     |                     0.085 | 0.517 (352)  | 0.556 (257)  | 0.503 (185) |
| ridge            | lasso      | total    |          13.44 |             0.502 | 0.09, 0.529, 535                     |                     0.08  | 0.516 (285)  | 0.556 (232)  | 0.497 (165) |
| ridge            | forward    | total    |          13.28 |             0.524 | 0.08, 0.594, 608                     |                     0.075 | 0.612 (245)  | 0.601 (253)  | 0.541 (209) |
| lasso            | live       | points   |          13.36 |             0.502 | 0.06, 0.523, 849                     |                     0.07  | 0.529 (191)  | 0.518 (218)  | 0.516 (215) |
| lasso            | wide       | points   |          13.36 |             0.501 | 0.065, 0.529, 629                    |                     0.065 | 0.528 (229)  | 0.554 (224)  | 0.500 (176) |
| lasso            | lasso      | points   |          13.4  |             0.504 | 0.025, 0.517, 1949                   |                     0.075 | 0.508 (256)  | 0.508 (238)  | 0.503 (165) |
| lasso            | forward    | points   |          13.36 |             0.502 | 0.07, 0.543, 611                     |                     0.07  | 0.572 (187)  | 0.540 (252)  | 0.517 (172) |
| lasso            | live       | total    |          13.32 |             0.504 | 0.075, 0.553, 541                    |                     0.065 | 0.547 (245)  | 0.584 (257)  | 0.509 (232) |
| lasso            | wide       | total    |          13.34 |             0.499 | 0.075, 0.547, 545                    |                     0.08  | 0.546 (185)  | 0.583 (156)  | 0.518 (135) |
| lasso            | lasso      | total    |          13.42 |             0.506 | 0.065, 0.535, 874                    |                     0.08  | 0.523 (262)  | 0.569 (197)  | 0.507 (150) |
| lasso            | forward    | total    |          13.29 |             0.518 | 0.085, 0.587, 501                    |                     0.075 | 0.596 (208)  | 0.589 (246)  | 0.541 (209) |
| hgb              | live       | points   |          13.37 |             0.528 | 0.08, 0.579, 705                     |                     0.085 | 0.609 (225)  | 0.581 (210)  | 0.538 (184) |
| hgb              | wide       | points   |          13.44 |             0.513 | 0.085, 0.546, 520                    |                     0.085 | 0.551 (196)  | 0.526 (171)  | 0.562 (153) |
| hgb              | lasso      | points   |          13.45 |             0.509 | 0.055, 0.526, 1094                   |                     0.09  | 0.537 (188)  | 0.480 (154)  | 0.535 (129) |
| hgb              | forward    | points   |          13.42 |             0.522 | 0.09, 0.552, 514                     |                     0.09  | 0.574 (183)  | 0.539 (193)  | 0.543 (138) |
| hgb              | live       | total    |          13.45 |             0.506 | 0.085, 0.553, 674                    |                     0.06  | 0.561 (428)  | 0.543 (409)  | 0.526 (310) |
| hgb              | wide       | total    |          13.44 |             0.515 | 0.09, 0.539, 573                     |                     0.06  | 0.556 (396)  | 0.517 (383)  | 0.513 (316) |
| hgb              | lasso      | total    |          13.4  |             0.514 | 0.08, 0.544, 724                     |                     0.09  | 0.554 (213)  | 0.549 (204)  | 0.503 (175) |
| hgb              | forward    | total    |          13.43 |             0.513 | 0.075, 0.556, 843                    |                     0.07  | 0.595 (341)  | 0.526 (327)  | 0.527 (262) |
| rf               | live       | points   |          13.41 |             0.512 | 0.08, 0.544, 502                     |                     0.075 | 0.548 (188)  | 0.529 (210)  | 0.515 (196) |
| rf               | wide       | points   |          13.47 |             0.489 | 0.06, 0.510, 855                     |                     0.065 | 0.533 (242)  | 0.493 (274)  | 0.504 (228) |
| rf               | lasso      | points   |          13.45 |             0.497 | 0.065, 0.511, 714                    |                     0.07  | 0.522 (203)  | 0.477 (239)  | 0.541 (172) |
| rf               | forward    | points   |          13.43 |             0.511 | 0.06, 0.514, 846                     |                     0.07  | 0.529 (210)  | 0.488 (252)  | 0.523 (176) |
| rf               | live       | total    |          13.44 |             0.501 | 0.06, 0.535, 927                     |                     0.06  | 0.564 (323)  | 0.535 (327)  | 0.502 (277) |
| rf               | wide       | total    |          13.48 |             0.498 | 0.06, 0.517, 890                     |                     0.05  | 0.515 (404)  | 0.520 (394)  | 0.503 (320) |
| rf               | lasso      | total    |          13.43 |             0.499 | 0.08, 0.522, 502                     |                     0.07  | 0.506 (233)  | 0.542 (238)  | 0.498 (207) |
| rf               | forward    | total    |          13.42 |             0.513 | 0.09, 0.561, 504                     |                     0.085 | 0.577 (201)  | 0.552 (201)  | 0.518 (168) |
| mlp              | live       | points   |          13.59 |             0.51  | 0.095, 0.534, 689                    |                     0.09  | 0.533 (315)  | 0.552 (270)  | 0.477 (178) |
| mlp              | wide       | points   |          13.86 |             0.508 | 0.07, 0.523, 1282                    |                     0.075 | 0.532 (453)  | 0.515 (439)  | 0.503 (298) |
| mlp              | lasso      | points   |          13.72 |             0.499 | 0.005, 0.501, 2657                   |                     0.01  | 0.493 (933)  | 0.503 (929)  | 0.507 (680) |
| mlp              | forward    | points   |          13.67 |             0.503 | 0.1, 0.536, 651                      |                     0.1   | 0.568 (264)  | 0.530 (247)  | 0.486 (140) |
| mlp              | live       | total    |          13.5  |             0.502 | 0.085, 0.535, 731                    |                     0.085 | 0.540 (272)  | 0.548 (248)  | 0.512 (211) |
| mlp              | wide       | total    |          14.06 |             0.513 | 0.025, 0.516, 2298                   |                     0.03  | 0.517 (789)  | 0.505 (813)  | 0.522 (599) |
| mlp              | lasso      | total    |          13.94 |             0.508 | 0.05, 0.511, 1693                    |                     0.085 | 0.507 (414)  | 0.522 (391)  | 0.462 (273) |
| mlp              | forward    | total    |          13.49 |             0.509 | 0.09, 0.572, 687                     |                     0.08  | 0.597 (305)  | 0.556 (333)  | 0.541 (207) |

**Spreads**

| model            | features   | target   |   RMSE 2015-25 |   acc, every game | look-ahead best (share, acc, bets)   |   share picked on 2015-18 | 2015-18     | 2019-22     | 2023-25     |
|:-----------------|:-----------|:---------|---------------:|------------------:|:-------------------------------------|--------------------------:|:------------|:------------|:------------|
| live model       | live       | live     |          12.88 |             0.512 | 0.5, 0.522, 1005                     |                      0.45 | 0.540 (415) | 0.520 (394) | 0.495 (313) |
| live ridge alone | live       | points   |          12.89 |             0.506 | 0.5, 0.519, 993                      |                      0.35 | 0.525 (491) | 0.518 (498) | 0.503 (378) |
| live trees alone | live       | points   |          13.04 |             0.512 | 0.5, 0.528, 1298                     |                      0.5  | 0.539 (516) | 0.529 (463) | 0.511 (319) |
| ridge            | live       | points   |          12.89 |             0.506 | 0.5, 0.519, 993                      |                      0.35 | 0.525 (491) | 0.518 (498) | 0.503 (378) |
| ridge            | wide       | points   |          13.04 |             0.509 | 0.35, 0.525, 1615                    |                      0.35 | 0.528 (597) | 0.518 (583) | 0.531 (435) |
| ridge            | lasso      | points   |          12.99 |             0.511 | 0.5, 0.536, 1183                     |                      0.5  | 0.556 (437) | 0.513 (427) | 0.539 (319) |
| ridge            | forward    | points   |          12.88 |             0.518 | 0.5, 0.537, 1092                     |                      0.5  | 0.554 (404) | 0.533 (403) | 0.519 (285) |
| lasso            | live       | points   |          12.91 |             0.513 | 0.35, 0.519, 1359                    |                      0.35 | 0.530 (496) | 0.520 (488) | 0.501 (375) |
| lasso            | wide       | points   |          12.95 |             0.513 | 0.4, 0.530, 1276                     |                      0.35 | 0.548 (536) | 0.527 (510) | 0.499 (367) |
| lasso            | lasso      | points   |          12.97 |             0.513 | 0.5, 0.532, 1149                     |                      0.5  | 0.549 (432) | 0.510 (416) | 0.538 (301) |
| lasso            | forward    | points   |          12.89 |             0.509 | 0.5, 0.529, 1043                     |                      0.5  | 0.544 (388) | 0.513 (376) | 0.530 (279) |
| hgb              | live       | points   |          12.99 |             0.507 | 0.5, 0.523, 1190                     |                      0.3  | 0.524 (653) | 0.505 (616) | 0.510 (437) |
| hgb              | wide       | points   |          13.02 |             0.509 | 0.5, 0.525, 1169                     |                      0.35 | 0.526 (605) | 0.535 (544) | 0.494 (399) |
| hgb              | lasso      | points   |          13.01 |             0.519 | 0.5, 0.534, 1170                     |                      0.5  | 0.528 (462) | 0.570 (407) | 0.495 (301) |
| hgb              | forward    | points   |          12.96 |             0.518 | 0.5, 0.541, 1187                     |                      0.5  | 0.563 (465) | 0.534 (416) | 0.516 (306) |
| rf               | live       | points   |          13.03 |             0.514 | 0.1, 0.519, 2385                     |                      0.1  | 0.515 (891) | 0.535 (867) | 0.504 (627) |
| rf               | wide       | points   |          13.11 |             0.52  | 0.35, 0.539, 1639                    |                      0.35 | 0.533 (629) | 0.567 (582) | 0.512 (428) |
| rf               | lasso      | points   |          13.07 |             0.517 | 0.5, 0.537, 1192                     |                      0.5  | 0.538 (474) | 0.540 (417) | 0.532 (301) |
| rf               | forward    | points   |          13.03 |             0.526 | 0.45, 0.548, 1333                    |                      0.45 | 0.557 (513) | 0.553 (488) | 0.527 (332) |
| mlp              | live       | points   |          13.15 |             0.495 | 0.45, 0.504, 1455                    |                      0.3  | 0.506 (707) | 0.499 (653) | 0.495 (444) |
| mlp              | wide       | points   |          13.36 |             0.501 | 0.5, 0.512, 1572                     |                      0.5  | 0.524 (618) | 0.511 (568) | 0.495 (386) |
| mlp              | lasso      | points   |          13.13 |             0.514 | 0.4, 0.535, 1626                     |                      0.5  | 0.558 (538) | 0.516 (500) | 0.504 (371) |
| mlp              | forward    | points   |          13.11 |             0.526 | 0.35, 0.528, 1768                    |                      0.5  | 0.559 (587) | 0.517 (520) | 0.459 (344) |

### Runtimes

- one refit, largest training set (2025 wk 17, 7,034 team-games / 3,517 games), set 1 / set 2: ridge 0.0 / 0.2s; lasso (LassoCV) 0.1 / 0.3s; boosting 0.9 / 2.5s; forest 4.7 / 27s at 250 trees (cut to 150 trees on half-samples before the runs); MLP 4.4 / 1.6s. Totals about half
- frames (team 7,668 x 105, game 3,834 x 112): 5s
- forward selection, ridge, 2013-18: 255s (19 points inputs, 11 total inputs)
- tuning on 2013-18 (season refits), in parallel: boosting 226s (5 settings), MLP 211s (5), forest 171s (3)
- walk-forward 2015-25, both targets, four sets, in parallel on a shared 4-core machine: ridge 95s and lasso 211s (weekly); boosting 935s points + 877s total (weekly); forest 993s and MLP 789s (every 4 weeks)
- wall clock, frames to last run: about 30 minutes

### Verdict against the rule

Passing on spreads: none. Passing on totals: none.
