# Relative pace in the totals equation (3 Oct 2026)

`experiments/relative_pace.py`, `reports/relative_pace.csv`.

**Claim.** Follow-up to `reports/totals_new_ideas.md` (V1 pace, seconds per snap): pace helped the total miss on 2015-18 and
2019-22 (10.7037 / 10.5055; totals flag 181-141 / 225-172) and failed 2023-25 (10.1421; 117-104), likely because the whole
league slowed in 2024-25, so an input fit on the absolute level of pace drifts. Pace measured **relative to the league's
own average as of that week** lowers the total miss on every window and wins at least as many bets.

**Snooping caveat.** This idea was chosen after seeing the totals_new_ideas results, including V1's held-out failure. The
three variants below are counted as new variants on top of that study's nine (12 in the line), and on top of the earlier
pace tries in the decision log. A pass here is weaker evidence than a pass on an idea fixed before any result.

## Pre-registration (written before any result; not changed after)

### Variants (every one counted; at most three)
All inputs use only games already played (strictly earlier weeks), from `team_games` (`sec_per_play`, `def_sec_per_play`,
play-by-play) and, for R2, `scheme_plays` (neutral snaps: win chance 20-80% on first or second down, as V2 of
totals_new_ideas; 2016 on). As in V1, each input is one number per game: both offenses' value plus both defenses' value
(what each defense allowed).

| # | Variant | Team value (offense, and the same for defense allowed) |
|---|---|---|
| R1 | Relative pace | `n/(n+4) * (team's this-season mean - league average) + 4/(n+4) * (team's last-season mean - last season's league mean)`, `n` = the team's games this season so far (equal weights). League average = this season's mean over all earlier team-games, shrunk toward last season's league mean with 32 team-games of weight (one week). Week 1: last season's relative value. A team with no games either season: 0. |
| R2 | R1 + neutral pace | R1's input plus a second input built the same way from neutral-situation seconds per snap. 2015 (no neutral data, and no prior season for 2016 week 1) is 0, the league average. |
| R3 | Recency-weighted relative pace | The ratings' window (`ratings.window`: decay 0.94 a week, last season at 0.8, the same weights the ratings use): the team's weighted mean minus the window's weighted league mean, pulled toward 0 with 4 games of weight. (V1's team value minus the window's league mean.) |

Each variant adds its input(s) to `model.TOTAL_FEATS` and refits walk-forward 2015-2025 with the weekly refit (the totals
equation, wind points and `p_over_emp` rebuilt exactly as `model.walk_forward` does, checked against the live walk-forward to
1e-9; the points equations and the spread untouched), reusing `experiments/totals_new_ideas.py`'s rebuild.

### Pass bar
- `study_gate.gate` on the total miss (regular season) for 2015-18 (untouched), 2019-22 (tuning) and 2023-25 (held out):
  lower on every window; no bet cost: totals flag (55%+ under), wind under (10+ mph) and spread flag (4+), weeks 1-17, wins
  minus losses not worse on any window.
- The placebo for a variant that passes parts 1 and 2: its input values shuffled among the games of each season
  (`study_gate.shuffle_within_season`), 50 draws, seed 20261003, the real gain above at least 45 of 50 on every window.
- The model-auditor on any variant that passes everything. If one passes every part and the auditor, it is rerun with the
  current model (round-3 part 5; the base here is the current model, so the variant run is the together run) and adopted
  under Matt's standing approval: added to `model.TOTAL_FEATS` and the live pipeline with a standing check that its input is
  as-of. If two pass, the one with the lower 2019-22 miss (not 2023-25) is taken.
- No market input (the line only grades and prices the over chance at the line, as now); no look-ahead.

## Results

Rebuilt totals side against the live walk-forward: 3028 games, largest difference 0.0e+00 points in the total and 0.0e+00 in the over chance.

Inputs, regular-season games 2015-2025 (one value per game; `pace_sum` is totals_new_ideas' V1, shown for the drift only):

| Input | Games | Missing | Mean | SD |
|---|---|---|---|---|
| rpace_sum | 3028 | 0 | 0.0167 | 1.6758 |
| rnpace_sum | 3028 | 0 | 0.0241 | 2.1057 |
| rwpace_sum | 3028 | 0 | -0.0003 | 1.1513 |
| pace_sum | 3028 | 0 | 118.3459 | 1.9124 |

Season mean of each input (seconds; the absolute V1 input drifts with the league, the relative ones should sit near 0):

| Season | rpace_sum | rnpace_sum | rwpace_sum | pace_sum |
|---|---|---|---|---|
| 2015 | -0.050 | 0.000 | 0.017 | 116.088 |
| 2016 | 0.052 | 0.011 | 0.013 | 116.280 |
| 2017 | 0.018 | -0.041 | -0.027 | 117.538 |
| 2018 | -0.000 | 0.072 | -0.008 | 118.027 |
| 2019 | -0.004 | 0.082 | 0.042 | 118.440 |
| 2020 | -0.085 | -0.087 | -0.014 | 117.543 |
| 2021 | 0.036 | 0.041 | -0.007 | 118.015 |
| 2022 | -0.024 | -0.030 | -0.041 | 118.800 |
| 2023 | -0.002 | 0.038 | 0.019 | 118.928 |
| 2024 | 0.187 | 0.182 | 0.011 | 120.659 |
| 2025 | 0.044 | -0.008 | -0.007 | 121.105 |

Each variant refit walk-forward 2015-2025, regular season scored; flags at the live rules, weeks 1-17; totals units at -110.

| Variant | Window | Total miss | Over log loss | Team miss | Spread flag | Totals flag | Totals units | Wind under |
|---|---|---|---|---|---|---|---|---|
| base  | 2015-18 | 10.7484 | 0.70446 | 7.3993 | 68-58 | 132-111 | +9.90 | 119-97 |
| base  | 2019-22 | 10.5340 | 0.69255 | 7.3740 | 78-49 | 175-140 | +21.00 | 143-88 |
| base  | 2023-25 | 10.1040 | 0.69000 | 7.2357 | 37-19 | 76-55 | +15.50 | 77-52 |
| R1 relative pace | 2015-18 | 10.7251 | 0.70300 | 7.3892 | 68-58 | 137-108 | +18.20 | 119-97 |
| R1 relative pace | 2019-22 | 10.5188 | 0.68988 | 7.3694 | 78-49 | 171-136 | +21.40 | 143-88 |
| R1 relative pace | 2023-25 | 10.1503 | 0.69383 | 7.2376 | 37-19 | 73-61 | +5.90 | 77-52 |
| R2 relative pace + relative neutral pace | 2015-18 | 10.7591 | 0.70592 | 7.4078 | 68-58 | 137-116 | +9.40 | 119-97 |
| R2 relative pace + relative neutral pace | 2019-22 | 10.5266 | 0.69032 | 7.3715 | 78-49 | 168-138 | +16.20 | 143-88 |
| R2 relative pace + relative neutral pace | 2023-25 | 10.1542 | 0.69397 | 7.2373 | 37-19 | 72-61 | +4.90 | 77-52 |
| R3 recency-weighted relative pace | 2015-18 | 10.7197 | 0.70227 | 7.3860 | 68-58 | 136-107 | +18.30 | 119-97 |
| R3 recency-weighted relative pace | 2019-22 | 10.5246 | 0.69002 | 7.3725 | 78-49 | 172-138 | +20.20 | 143-88 |
| R3 recency-weighted relative pace | 2023-25 | 10.1526 | 0.69398 | 7.2384 | 37-19 | 74-64 | +3.60 | 77-52 |

## Gate, R1 relative pace (parts 1 and 2; the placebo runs only for a variant that passes them)

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | yes | miss 10.7484 -> 10.7251 |
| better on 2019-22 | yes | miss 10.5340 -> 10.5188 |
| better on 2023-25 | NO | miss 10.1040 -> 10.1503 |
| no bet cost: spread flag, 2015-18 | yes | 68-58 -> 68-58 |
| no bet cost: totals flag, 2015-18 | yes | 132-111 -> 137-108 |
| no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| no bet cost: spread flag, 2019-22 | yes | 78-49 -> 78-49 |
| no bet cost: totals flag, 2019-22 | yes | 175-140 -> 171-136 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 37-19 -> 37-19 |
| no bet cost: totals flag, 2023-25 | NO | 76-55 -> 73-61 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |

Gate: FAIL (10 of 12); no market input and no look-ahead checked by the model-auditor agent

## Gate, R2 relative pace + relative neutral pace (parts 1 and 2; the placebo runs only for a variant that passes them)

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | NO | miss 10.7484 -> 10.7591 |
| better on 2019-22 | yes | miss 10.5340 -> 10.5266 |
| better on 2023-25 | NO | miss 10.1040 -> 10.1542 |
| no bet cost: spread flag, 2015-18 | yes | 68-58 -> 68-58 |
| no bet cost: totals flag, 2015-18 | yes | 132-111 -> 137-116 |
| no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| no bet cost: spread flag, 2019-22 | yes | 78-49 -> 78-49 |
| no bet cost: totals flag, 2019-22 | NO | 175-140 -> 168-138 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 37-19 -> 37-19 |
| no bet cost: totals flag, 2023-25 | NO | 76-55 -> 72-61 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |

Gate: FAIL (8 of 12); no market input and no look-ahead checked by the model-auditor agent

## Gate, R3 recency-weighted relative pace (parts 1 and 2; the placebo runs only for a variant that passes them)

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | yes | miss 10.7484 -> 10.7197 |
| better on 2019-22 | yes | miss 10.5340 -> 10.5246 |
| better on 2023-25 | NO | miss 10.1040 -> 10.1526 |
| no bet cost: spread flag, 2015-18 | yes | 68-58 -> 68-58 |
| no bet cost: totals flag, 2015-18 | yes | 132-111 -> 136-107 |
| no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| no bet cost: spread flag, 2019-22 | yes | 78-49 -> 78-49 |
| no bet cost: totals flag, 2019-22 | NO | 175-140 -> 172-138 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 37-19 -> 37-19 |
| no bet cost: totals flag, 2023-25 | NO | 76-55 -> 74-64 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |

Gate: FAIL (9 of 12); no market input and no look-ahead checked by the model-auditor agent

## Decision

**No variant passes parts 1 and 2 of the rule, so no placebo, auditor or together test ran, and nothing is adopted.** The
live totals equation and the totals rules stay as they are.

- **The drift explanation does not hold up.** The relative inputs do sit near 0 every season (season means -0.09 to
  +0.19 seconds against an SD of 1.15 to 2.11, while the absolute V1 input rises from 116.1 in 2015 to 121.1 in 2025),
  yet all three still fail the held-out 2023-25 total miss, by a bit more than V1 did (10.1040 -> 10.1503 / 10.1542 /
  10.1526, +0.046 to +0.050, against V1's 10.1421, +0.038). So V1's 2023-25 failure was not the league-wide slowdown; a team's pace simply did not
  help predict the total in 2023-25.
- **R1 relative pace** and **R3 recency-weighted relative pace** help 2015-18 and 2019-22 (miss -0.023 / -0.015 and
  -0.029 / -0.009) but fail 2023-25 on the miss and on the totals flag (net +21 -> +12 and +10). R3 also costs the 2019-22
  totals flag (net +35 -> +34).
- **R2** (R1 plus relative neutral pace) is worse than the base on 2015-18 and 2023-25 and costs the totals flag on 2019-22
  and 2023-25.

**Count.** Three variants here, on top of totals_new_ideas' nine (12 in this line), none picked on 2023-25. Counting the
decision log, pace has now been tried in the totals equation about ten times (three forms on 22 Sep, totals_inputs,
no-huddle in scheme_qb_totals, totals_new_ideas V1 and V2, and R1-R3 here); none adopted. **Snooping caveat:** this
follow-up was chosen after seeing totals_new_ideas' results, so even a pass would have been weaker evidence; it did not pass.

**Auditor.** Not run: the rule asks for it on a passer, and no variant passed parts 1 and 2. The rebuilt totals side
reproduces the live walk-forward exactly (largest difference 0.0 in the total and the over chance); every input uses only
earlier weeks of this season and last season (`rel_season`, `rel_window` in the script); no line, split or price is an
input. The gate tables' footer about the auditor is the gate's standard text; the auditor was not run.
