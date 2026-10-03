# New totals ideas (3 Oct 2026)

`experiments/totals_new_ideas.py`, `reports/totals_new_ideas.csv`.

**Claim.** Matt (3 Oct 2026): "improve TOTALS accuracy and the totals rules' wins/units against Vegas with NEW ideas from
all angles." Some untested input to the totals equation (`model.total_model`, `TOTAL_FEATS`), or a better way to turn the
model total into the over chance (`p_over_emp`), lowers the total miss (or the over chance's log loss) on every window and
wins at least as many totals-flag bets.

## Pre-registration (written before any result; not changed after)

### What was already tried (decision log), so not re-run
- Plays per game (pace) in the totals equation: 22 Sep (totals_experiments_2, three forms), totals_inputs (one), overs_deep
  (diagnosis and an over rule); no-huddle rate (scheme_qb_totals). All failed a window.
- Turnovers in the totals equation (totals_turnover), turnover luck in the ratings (luck, turnover2): failed.
- Defensive and offensive snaps out, skill value out summed (totals_players, totals_div), Questionable defenders
  (questionable_totals): failed. A secondary-only absence would be a cut of the same snaps-out input, so it is not run.
- Cold and temperature on forecasts (forecast_weather_inputs, weather_forecast_retest): failed every window or the placebo.
  Not re-run.
- The over chance: skewed residuals (totals_fix, adopted), calibrated logistic (total_prob), M1/M2 corrections
  (overs_deep), total-dependent margin sigma: the residuals scaled by the total and key totals were not tried.
- Kicker value and turf were tried on team points and the margin (special_teams, rest_more), never in the totals equation.

### Variants (every one counted)
Team-level stats are as-of: the decayed weighted mean of the team's earlier games only, with the live ratings' window
(`ratings.window`, decay 0.94 a week, last season at 0.8 weight), pulled toward that window's league mean with 4 games of
weight. Each "sum" is the game's two offenses plus its two defenses (what each defense allowed), one input.

| # | Variant | Input or change | Source and timing |
|---|---|---|---|
| V1 | Pace (seconds per play) | sum of offense seconds per snap and defense seconds per snap allowed (`sec_per_play`, `def_sec_per_play`) | team_games (play-by-play), earlier games only |
| V2 | Neutral pace | the same, only snaps with win chance 20-80% on first or second down (`scheme_plays.neutral`) | scheme_plays, 2016 on; 2015 priced at the league mean (no data) |
| V3 | Finishing drives | red-zone TD rate (`rz_td_rate`, `def_rz_td_rate`) | team_games, earlier games only |
| V4 | Explosive plays | share of plays gaining 20+ passing / 12+ rushing (`explosive_rate`, `def_explosive_rate`) | team_games, earlier games only |
| V5 | Kicker quality | both teams' kicker value above replacement (`special_teams_asof.kicker_value`: last game's kicker, as-of value) | special_teams_asof, earlier games only |
| V6 | Artificial turf | 1 when the schedule's surface is not grass | games.surface (known before the game) |
| V7 | Altitude | 1 for Denver home games at its stadium | games home_team / stadium_id |
| V8 | Spread grows with the total | `p_over_emp` from the training misses scaled by sqrt(model total / mean training prediction) (variance proportional to the mean, as in a Poisson count) | the fit's own training games |
| V9 | Key totals | `p_over_emp` read off a whole-number pmf: the training misses' smoothed density (bandwidth 1.5 points) at each total, times key-total weights (observed count of each final total / expected count over the training games, +1 smoothing, as the margin's `key_weights`) | the fit's own training games |

V1 to V7 each add one input to `TOTAL_FEATS`, refit walk-forward 2015-2025 with the weekly refit (the totals equation, wind
points and `p_over_emp` rebuilt exactly as `model.walk_forward` does; the points equations, and so the spread, untouched).
V8 and V9 leave the total unchanged and change only the over chance.

### Pass bar
- V1-V7: `study_gate.gate` on the total miss (regular season) for 2015-18 (untouched), 2019-22 (tuning) and 2023-25 (held
  out): lower on every window; no bet cost: the totals flag (55%+ under), the wind under (10+ mph) and the spread flag (4+),
  weeks 1-17, wins minus losses not worse on any window; then the placebo: the input's values shuffled among the games of
  each season (`study_gate.shuffle_within_season`), 50 draws, seed 20261003, the real gain above at least 45 of 50 on every
  window. The placebo runs only for a variant that passes parts 1 and 2.
- V8-V9: the total miss cannot move, so part 1 is the over chance's log loss at the closing total (pushes out, regular
  season) lower on every window; the same records; placebo: V8 the scale factors shuffled within season, V9 the key-total
  weights shuffled among the totals of each fit, 50 draws each.
- Passers are rerun together and must pass parts 1 and 2 together; the model-auditor runs on every passer. A clear winner
  that passes every part, the auditor and the together test is adopted under Matt's standing approval; otherwise reported.
- No market input anywhere (the line is used only to grade and to price the over chance at the line, as now); no look-ahead.

## Results

Rebuilt totals side against the live walk-forward: 3028 games, largest difference 0.0e+00 points in the total and 0.0e+00 in the over chance.

Inputs, regular-season games 2015-2025 (one value per game):

| Input | Games | Missing | Mean | SD |
|---|---|---|---|---|
| pace_sum | 3028 | 0 | 118.3459 | 1.9124 |
| rz_td_sum | 3028 | 0 | 2.2764 | 0.1425 |
| explosive_sum | 3028 | 0 | 0.3221 | 0.0182 |
| npace_sum | 3028 | 0 | 127.0343 | 2.4227 |
| kicker_sum | 3028 | 0 | 0.1230 | 0.1061 |
| turf | 3028 | 0 | 0.4257 | 0.4944 |
| altitude | 3028 | 0 | 0.0314 | 0.1743 |

Each variant refit walk-forward 2015-2025, regular season scored; flags at the live rules, weeks 1-17; totals units at -110.

| Variant | Window | Total miss | Over log loss | Team miss | Spread flag | Totals flag | Totals units | Wind under |
|---|---|---|---|---|---|---|---|---|
| base  | 2015-18 | 10.7484 | 0.70446 | 7.3993 | 68-58 | 132-111 | +9.90 | 119-97 |
| base  | 2019-22 | 10.5340 | 0.69255 | 7.3740 | 78-49 | 175-140 | +21.00 | 143-88 |
| base  | 2023-25 | 10.1040 | 0.69000 | 7.2357 | 37-19 | 76-55 | +15.50 | 77-52 |
| V1 pace (seconds per snap) | 2015-18 | 10.7037 | 0.70173 | 7.3781 | 68-58 | 181-141 | +25.90 | 119-97 |
| V1 pace (seconds per snap) | 2019-22 | 10.5055 | 0.68990 | 7.3629 | 78-49 | 225-172 | +35.80 | 143-88 |
| V1 pace (seconds per snap) | 2023-25 | 10.1421 | 0.69459 | 7.2392 | 37-19 | 117-104 | +2.60 | 77-52 |
| V2 neutral pace | 2015-18 | 10.7567 | 0.70534 | 7.4040 | 68-58 | 126-114 | +0.60 | 119-97 |
| V2 neutral pace | 2019-22 | 10.5176 | 0.69159 | 7.3671 | 78-49 | 187-149 | +23.10 | 143-88 |
| V2 neutral pace | 2023-25 | 10.1266 | 0.69233 | 7.2346 | 37-19 | 96-81 | +6.90 | 77-52 |
| V3 red-zone TD rate | 2015-18 | 10.7664 | 0.70621 | 7.4009 | 68-58 | 136-121 | +2.90 | 119-97 |
| V3 red-zone TD rate | 2019-22 | 10.5384 | 0.69318 | 7.3766 | 78-49 | 184-150 | +19.00 | 143-88 |
| V3 red-zone TD rate | 2023-25 | 10.1041 | 0.68990 | 7.2355 | 37-19 | 75-55 | +14.50 | 77-52 |
| V4 explosive-play rate | 2015-18 | 10.7477 | 0.70466 | 7.4002 | 68-58 | 123-109 | +3.10 | 119-97 |
| V4 explosive-play rate | 2019-22 | 10.5270 | 0.69209 | 7.3679 | 78-49 | 173-134 | +25.60 | 143-88 |
| V4 explosive-play rate | 2023-25 | 10.0744 | 0.68870 | 7.2283 | 37-19 | 80-60 | +14.00 | 77-52 |
| V5 kicker value | 2015-18 | 10.7727 | 0.70568 | 7.4070 | 68-58 | 124-94 | +20.60 | 119-97 |
| V5 kicker value | 2019-22 | 10.5459 | 0.69336 | 7.3799 | 78-49 | 168-135 | +19.50 | 143-88 |
| V5 kicker value | 2023-25 | 10.1141 | 0.69041 | 7.2365 | 37-19 | 73-52 | +15.80 | 77-52 |
| V6 artificial turf | 2015-18 | 10.7423 | 0.70432 | 7.3976 | 68-58 | 126-113 | +1.70 | 119-97 |
| V6 artificial turf | 2019-22 | 10.5461 | 0.69311 | 7.3775 | 78-49 | 169-145 | +9.50 | 143-88 |
| V6 artificial turf | 2023-25 | 10.1027 | 0.68992 | 7.2347 | 37-19 | 72-57 | +9.30 | 77-52 |
| V7 altitude (Denver home) | 2015-18 | 10.7871 | 0.70673 | 7.4078 | 68-58 | 131-113 | +6.70 | 119-97 |
| V7 altitude (Denver home) | 2019-22 | 10.5326 | 0.69236 | 7.3742 | 78-49 | 175-142 | +18.80 | 143-88 |
| V7 altitude (Denver home) | 2023-25 | 10.1034 | 0.69001 | 7.2339 | 37-19 | 79-56 | +17.40 | 77-52 |
| V8 spread grows with the total | 2015-18 | 10.7484 | 0.70409 | 7.3993 | 68-58 | 130-111 | +7.90 | 119-97 |
| V8 spread grows with the total | 2019-22 | 10.5340 | 0.69270 | 7.3740 | 78-49 | 178-140 | +24.00 | 143-88 |
| V8 spread grows with the total | 2023-25 | 10.1040 | 0.68962 | 7.2357 | 37-19 | 78-54 | +18.60 | 77-52 |
| V9 key totals | 2015-18 | 10.7484 | 0.70485 | 7.3993 | 68-58 | 152-133 | +5.70 | 119-97 |
| V9 key totals | 2019-22 | 10.5340 | 0.69306 | 7.3740 | 78-49 | 198-159 | +23.10 | 143-88 |
| V9 key totals | 2023-25 | 10.1040 | 0.69000 | 7.2357 | 37-19 | 89-66 | +16.40 | 77-52 |

## Gate, V1 pace (seconds per snap) (parts 1 and 2; the placebo runs only for a variant that passes them)

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | yes | miss 10.7484 -> 10.7037 |
| better on 2019-22 | yes | miss 10.5340 -> 10.5055 |
| better on 2023-25 | NO | miss 10.1040 -> 10.1421 |
| no bet cost: spread flag, 2015-18 | yes | 68-58 -> 68-58 |
| no bet cost: totals flag, 2015-18 | yes | 132-111 -> 181-141 |
| no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| no bet cost: spread flag, 2019-22 | yes | 78-49 -> 78-49 |
| no bet cost: totals flag, 2019-22 | yes | 175-140 -> 225-172 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 37-19 -> 37-19 |
| no bet cost: totals flag, 2023-25 | NO | 76-55 -> 117-104 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |

Gate: FAIL (10 of 12); no market input and no look-ahead checked by the model-auditor agent

## Gate, V2 neutral pace (parts 1 and 2; the placebo runs only for a variant that passes them)

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | NO | miss 10.7484 -> 10.7567 |
| better on 2019-22 | yes | miss 10.5340 -> 10.5176 |
| better on 2023-25 | NO | miss 10.1040 -> 10.1266 |
| no bet cost: spread flag, 2015-18 | yes | 68-58 -> 68-58 |
| no bet cost: totals flag, 2015-18 | NO | 132-111 -> 126-114 |
| no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| no bet cost: spread flag, 2019-22 | yes | 78-49 -> 78-49 |
| no bet cost: totals flag, 2019-22 | yes | 175-140 -> 187-149 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 37-19 -> 37-19 |
| no bet cost: totals flag, 2023-25 | NO | 76-55 -> 96-81 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |

Gate: FAIL (8 of 12); no market input and no look-ahead checked by the model-auditor agent

## Gate, V3 red-zone TD rate (parts 1 and 2; the placebo runs only for a variant that passes them)

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | NO | miss 10.7484 -> 10.7664 |
| better on 2019-22 | NO | miss 10.5340 -> 10.5384 |
| better on 2023-25 | NO | miss 10.1040 -> 10.1041 |
| no bet cost: spread flag, 2015-18 | yes | 68-58 -> 68-58 |
| no bet cost: totals flag, 2015-18 | NO | 132-111 -> 136-121 |
| no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| no bet cost: spread flag, 2019-22 | yes | 78-49 -> 78-49 |
| no bet cost: totals flag, 2019-22 | NO | 175-140 -> 184-150 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 37-19 -> 37-19 |
| no bet cost: totals flag, 2023-25 | NO | 76-55 -> 75-55 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |

Gate: FAIL (6 of 12); no market input and no look-ahead checked by the model-auditor agent

## Gate, V4 explosive-play rate (parts 1 and 2; the placebo runs only for a variant that passes them)

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | yes | miss 10.7484 -> 10.7477 |
| better on 2019-22 | yes | miss 10.5340 -> 10.5270 |
| better on 2023-25 | yes | miss 10.1040 -> 10.0744 |
| no bet cost: spread flag, 2015-18 | yes | 68-58 -> 68-58 |
| no bet cost: totals flag, 2015-18 | NO | 132-111 -> 123-109 |
| no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| no bet cost: spread flag, 2019-22 | yes | 78-49 -> 78-49 |
| no bet cost: totals flag, 2019-22 | yes | 175-140 -> 173-134 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 37-19 -> 37-19 |
| no bet cost: totals flag, 2023-25 | NO | 76-55 -> 80-60 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |

Gate: FAIL (10 of 12); no market input and no look-ahead checked by the model-auditor agent

## Gate, V5 kicker value (parts 1 and 2; the placebo runs only for a variant that passes them)

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | NO | miss 10.7484 -> 10.7727 |
| better on 2019-22 | NO | miss 10.5340 -> 10.5459 |
| better on 2023-25 | NO | miss 10.1040 -> 10.1141 |
| no bet cost: spread flag, 2015-18 | yes | 68-58 -> 68-58 |
| no bet cost: totals flag, 2015-18 | yes | 132-111 -> 124-94 |
| no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| no bet cost: spread flag, 2019-22 | yes | 78-49 -> 78-49 |
| no bet cost: totals flag, 2019-22 | NO | 175-140 -> 168-135 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 37-19 -> 37-19 |
| no bet cost: totals flag, 2023-25 | yes | 76-55 -> 73-52 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |

Gate: FAIL (8 of 12); no market input and no look-ahead checked by the model-auditor agent

## Gate, V6 artificial turf (parts 1 and 2; the placebo runs only for a variant that passes them)

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | yes | miss 10.7484 -> 10.7423 |
| better on 2019-22 | NO | miss 10.5340 -> 10.5461 |
| better on 2023-25 | yes | miss 10.1040 -> 10.1027 |
| no bet cost: spread flag, 2015-18 | yes | 68-58 -> 68-58 |
| no bet cost: totals flag, 2015-18 | NO | 132-111 -> 126-113 |
| no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| no bet cost: spread flag, 2019-22 | yes | 78-49 -> 78-49 |
| no bet cost: totals flag, 2019-22 | NO | 175-140 -> 169-145 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 37-19 -> 37-19 |
| no bet cost: totals flag, 2023-25 | NO | 76-55 -> 72-57 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |

Gate: FAIL (8 of 12); no market input and no look-ahead checked by the model-auditor agent

## Gate, V7 altitude (Denver home) (parts 1 and 2; the placebo runs only for a variant that passes them)

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | NO | miss 10.7484 -> 10.7871 |
| better on 2019-22 | yes | miss 10.5340 -> 10.5326 |
| better on 2023-25 | yes | miss 10.1040 -> 10.1034 |
| no bet cost: spread flag, 2015-18 | yes | 68-58 -> 68-58 |
| no bet cost: totals flag, 2015-18 | NO | 132-111 -> 131-113 |
| no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| no bet cost: spread flag, 2019-22 | yes | 78-49 -> 78-49 |
| no bet cost: totals flag, 2019-22 | NO | 175-140 -> 175-142 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 37-19 -> 37-19 |
| no bet cost: totals flag, 2023-25 | yes | 76-55 -> 79-56 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |

Gate: FAIL (9 of 12); no market input and no look-ahead checked by the model-auditor agent

## Gate, V8 spread grows with the total (parts 1 and 2; the placebo runs only for a variant that passes them)

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | yes | miss 0.7045 -> 0.7041 |
| better on 2019-22 | NO | miss 0.6925 -> 0.6927 |
| better on 2023-25 | yes | miss 0.6900 -> 0.6896 |
| no bet cost: spread flag, 2015-18 | yes | 68-58 -> 68-58 |
| no bet cost: totals flag, 2015-18 | NO | 132-111 -> 130-111 |
| no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| no bet cost: spread flag, 2019-22 | yes | 78-49 -> 78-49 |
| no bet cost: totals flag, 2019-22 | yes | 175-140 -> 178-140 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 37-19 -> 37-19 |
| no bet cost: totals flag, 2023-25 | yes | 76-55 -> 78-54 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |

Gate: FAIL (10 of 12); no market input and no look-ahead checked by the model-auditor agent

## Gate, V9 key totals (parts 1 and 2; the placebo runs only for a variant that passes them)

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | NO | miss 0.7045 -> 0.7049 |
| better on 2019-22 | NO | miss 0.6925 -> 0.6931 |
| better on 2023-25 | NO | miss 0.6900 -> 0.6900 |
| no bet cost: spread flag, 2015-18 | yes | 68-58 -> 68-58 |
| no bet cost: totals flag, 2015-18 | NO | 132-111 -> 152-133 |
| no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| no bet cost: spread flag, 2019-22 | yes | 78-49 -> 78-49 |
| no bet cost: totals flag, 2019-22 | yes | 175-140 -> 198-159 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 37-19 -> 37-19 |
| no bet cost: totals flag, 2023-25 | yes | 76-55 -> 89-66 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |

Gate: FAIL (8 of 12); no market input and no look-ahead checked by the model-auditor agent

## Decision

**No variant passes parts 1 and 2 of the rule, so no placebo or together test ran, and nothing is adopted.** The live
totals equation and the totals rules stay as they are.

- **V4 explosive-play rate** is the only input that lowers the total miss on all three windows (10.7484 -> 10.7477 /
  10.5340 -> 10.5270 / 10.1040 -> 10.0744), but the 2015-18 gain is 0.0007 points and it costs the totals flag on 2015-18
  (net +21 -> +14) and 2023-25 (+21 -> +20). Fails no-bet-cost.
- **V1 pace (seconds per snap)** helps 2015-18 and 2019-22 (miss -0.045 / -0.029; totals flag net +21 -> +40 and
  +35 -> +53) and fails the held-out 2023-25 (miss 10.1040 -> 10.1421, flag net +21 -> +13). The league got slower
  (team_games, regular season: 28.9-29.8 seconds per snap a season in 2015-22, 29.9-30.5 in 2023-25, slowest in 2024-25),
  so likely an input fit on the level of pace misprices once the whole league moves (not tested). Same pattern as the
  earlier plays-per-game tests (22 Sep 2026).
- **V8 spread grows with the total** lowers the over chance's log loss on 2015-18 and 2023-25 but not 2019-22 (0.69255 ->
  0.69270) and costs two net totals-flag wins on 2015-18.
- V2 neutral pace, V3 red-zone TD rate, V5 kicker value, V6 turf, V7 altitude and V9 key totals each fail at least one
  window on their own yardstick and at least one totals-flag record.

**Count.** Nine variants here, none picked on 2023-25. Earlier tries of the same ideas (decision log): pace in the totals
equation five times (three forms on 22 Sep, totals_inputs, no-huddle in scheme_qb_totals), kicker value and turf once each
on team points (special_teams, rest_more), and about seven other constructions of the total or its spread (totals_fix,
reports/total_prob.csv, overs_deep M1/M2, total-dependent margin sigma): about 23 tries of these ideas in all, none adopted.

**Auditor.** Not run: the rule asks for it on a passer, and no variant passed parts 1 and 2. The rebuilt totals side
reproduces the live walk-forward exactly (largest difference 0.0 in the total and the over chance), every team input is a
decayed mean of strictly earlier games (`ratings.window`), and no line, split or price is an input. The gate tables'
footer line about the auditor is the gate's standard text; the auditor was not run. A blank schedule surface counts as grass
(V6).
