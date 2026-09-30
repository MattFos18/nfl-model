# Team- and stadium-specific home field, under the round-3 rule (30 Sep 2026)

`experiments/home_field.py` (engine, ideas, facts, this page). Every number per idea: `reports/home_field.csv`.

**Headline: no.** None of the 21 team-, stadium-, visitor- or season-stage home edges beats the one league home-field number under the rule, so there is nothing to adopt and no code change to make. 0 of 21 lower both the team points miss and the margin miss on all three windows (rule 1 as written for this study); 2 lower the team points miss alone on all three (the round-3 reading of rule 1), by 0.0002 to 0.009 points a window, and both cost spread wins or the win chance's calibration on some window (rule 2). Both also fail their placebo: shuffled within season, the travel-miles values matched or beat the real gain on some window in 8 of 12 draws and the time-zone values in 7 of 20 (the rule allows 5 of 50). Every idea moves the team points miss by less than a hundredth of a point on every window, the size of noise.

**No team truly differs from the league once shrunk.** After the model, the spread of home edges between teams is estimated at zero: a team's home-minus-road residual varies from season to season *less* than its sampling noise alone would make it vary, it does not carry from one season to the next (correlation -0.05), and last seasons' edge does not predict this season's (-0.01). So every team's shrunk edge is 0.0 points with a standard error of 0.0 around the league value. Even unshrunk, pooling every season at the current stadium, no team sits two standard errors from the league (the largest are Washington -2.3 points, z -1.8, and the Jets +2.6, z +1.6); with 32 teams, one or two would be expected past two standard errors by chance alone. Arrowhead (KC +0.2), Lambeau (GB +1.4), Seattle (+0.7) and Denver's altitude (+1.4, z +1.0) are all inside noise.

**A correction to the brief.** The brief says the home-field term has followed recent seasons since 27 Sep. It has not. `experiments/home_field_recency.py` tested that change on 27 Sep and it was *not adopted* (decision log, 27 Sep: "one league home-field term fit on 2013 on stays"). `nflmodel/model.py` still carries one input, `home` (1 on the home team's row), in the ridge, the five blend ridges and the trees, fit every week on every played game since 2013. It is worth about 1.83 points of margin in the 2013-2025 fit. This study tests against that model as it runs.

**Found on the way: the model gives the full home edge at neutral sites.** `neutral` is 1 on *both* rows of a neutral-site game, so its weight cancels out of the margin, while the designated home team keeps `home` = 1. London, Germany, Mexico City, Brazil, Dublin, Madrid and the Super Bowl are all priced with the full ~1.8-point home edge for the listed home team. The schedule's `stadium_id` for several 2025 international games is the home team's own stadium (KC-LAC in Brazil reads LAX01, MIN-PIT in Dublin reads PIT00), so only the `neutral` / `location` flag identifies them. Setting the home edge to zero there, or giving neutral sites their own term, is tested below (angle 2): the fit keeps about 1 point of edge for the listed home side (the own-term weight is -0.8 against the 1.8), and neither version passes.

## How it was run

Round 3's harness, reused by import from `experiments/situational_game.py`: `lean_walk_forward` (the live walk-forward, refit before every regular-season week on every played game since 2013, the seven-model blend, trees refit fresh on this machine, the live trees' cache never read or written), `finish` (team points = (total +/- spread) / 2) and `score` (graded at the closing line; spread flag 4+ points off the line, weeks 1-17; totals flag under at 55%+; win chance calibrated the live way on each variant's own earlier seasons). Windows 2015-18 (never used to choose anything), 2019-22, 2023-25, regular season.

Every idea is one *signed* home-edge column added to the live inputs: +v on the home team's row, -v on the visitor's, 0 at a neutral site. So its weight is half its margin effect, and it reaches the ridge, the five blend ridges and the trees as every live input does. Two ideas instead *replace* the live `home` column at neutral sites. Partial pooling (angle 5) puts one signed dummy per team-and-stadium into the six ridges with its own, heavier penalty (sigma^2 / (tau/2)^2, a random effect with prior sd tau). That needed one engine change, a scaler that leaves the live inputs untouched. With no dummies it reproduces `lean_walk_forward` to 6.4e-14 points on 2019. The trees get the live inputs only there.

Team histories are walk-forward from **prior seasons only**. "Residual" is the game's margin against the model's own number (the base walk-forward's spread, 2014-2026; before 2014 the plain as-of scoring rating round 3 used). A team's home edge in a season is its home-minus-road margin residual (rating errors hit both and cancel), centred on that season's league mean (the league value is what `home` already carries), with sampling variance sigma^2 (1/n_home + 1/n_road). The empirical-Bayes value for season S weights earlier seasons by recency (half-life 2, 3 or 4 seasons, last season in full). It drops seasons at an earlier stadium, which resets LV 2020, LAC 2017 and 2020, LA 2016 and 2020, ATL 2017, MIN 2014 and 2016, and SF 2014. It is shrunk toward zero by tau^2 / (tau^2 + V), where the between-team variance tau^2 comes by moments from the 32 teams' estimates and V is the weighted estimate's own sampling variance. The estimate of tau^2 is zero in almost every season, which makes that input all but identically zero, i.e. the base. So each per-team idea is also run with tau *forced* to 1 point of margin, a generous spread, to test the angle rather than the estimator.

Placebo (rule 3): per-team values have their team labels shuffled within season; game flags are shuffled across games within season (round 3's placebo). 50 draws, and the real gain must beat a draw's on every window in 45 of 50. The rule runs it only for ideas passing rules 1 and 2, and none does. It was still run as information. The two ideas that pass the team-points reading of rule 1 ran until 6 draws beat them, which settles the outcome (the rule allows 5 of 50). The flagship per-team edge (tau 1 point, half-life 3) and partial pooling (1 point) ran 20 draws each, for their percentiles.

Base (fresh trees), 2015-18 / 2019-22 / 2023-25: team points miss 7.4095 / 7.3474 / 7.2624, margin miss 9.9495 / 10.0210 / 9.9046, spread flag 69-55 / 80-51 / 40-21, totals flag 135-127 / 175-128 / 71-59, calibrated log loss 0.6194 / 0.6243 / 0.6202.

## The raw facts

- **Between-team spread of home edges, after the model: zero.** Over 2014-2025 (384 team-seasons with model residuals), the observed variance of a team's season home-minus-road residual is 35.7 points squared, and its sampling noise alone is 42.1 (residual sd 13.0 a game). Observed is below noise, so the variance-components estimate of true between-team variance is 0.0. In the rating-era residuals before 2014 it is 49.0 against 46.9, about 1.4 points of sd, but that rating is cruder than the model.
- **Persistence.** Consecutive seasons at the same stadium: correlation -0.045 (345 pairs; -0.060 with the pairs touching 2020 left out, 284 pairs). Odd against even seasons 2014-2025, each team at its current stadium: +0.15 over 32 teams (standard error about 0.18). Last seasons' shrunk edge (half-life 3) against this season's residual: -0.012 (352 team-seasons); the unshrunk all-season mean: -0.059. The decision log's 0.34 between halves (22 Sep) was on the raw margin, before the model. Some of a raw team home edge is team quality that differs home and away by schedule, which the model's ratings already carry.
- **Which teams differ:** none (table). The raw column, before the model, spreads wider (MIA +4.0, GB +3.5, NYJ +3.1, DEN +3.1 at the top; LAC +0.1, ARI +0.2, NO +0.2 at the bottom, against a league of about +1.9). After the model that spread is no wider than noise. The Giants and Jets share one stadium and sit at -1.8 and +2.6 unshrunk: the building is not what differs.

Each team's home edge beyond the league's, in margin points, at its current stadium (seasons at an earlier stadium dropped), as of the 2026 season from prior seasons only. 'Unshrunk' is the precision-weighted mean of the team's home-minus-road residual over every season at this stadium (1999 on; model residuals from 2014), with its standard error; z is the two divided. 'Shrunk (estimated)' is the empirical-Bayes value with the between-team variance estimated from the data: zero for every team, because that variance is estimated at zero. 'Shrunk (tau 1 pt, half-life 3)' is what a generous forced spread of 1 point would give. The raw column is half the team's home-minus-road margin 2014-2025 at this stadium, before the model (the league's own home edge is in it, about 1.9).

| Team | Stadium | Seasons | Unshrunk (SE) | z | Shrunk, estimated (SE) | Shrunk, tau 1 pt, half-life 3 (SE) | Raw half home-minus-road |
|---|---|---|---|---|---|---|---|
| NYJ | NYC01 | 16 | +2.65 (1.64) | +1.62 | +0.00 (0.00) | +0.35 (0.91) | +3.12 |
| PIT | PIT00 | 25 | +1.79 (1.33) | +1.35 | +0.00 (0.00) | +0.36 (0.91) | +2.80 |
| LV | VEG00 | 6 | +1.71 (2.55) | +0.67 | +0.00 (0.00) | +0.16 (0.94) | +2.47 |
| MIN | MIN01 | 10 | +1.42 (2.03) | +0.70 | +0.00 (0.00) | +0.43 (0.92) | +2.52 |
| BAL | BAL00 | 27 | +1.42 (1.28) | +1.11 | +0.00 (0.00) | -0.59 (0.91) | +0.97 |
| DEN | DEN00 | 25 | +1.36 (1.33) | +1.02 | +0.00 (0.00) | +0.47 (0.91) | +3.09 |
| GB | GNB00 | 27 | +1.36 (1.28) | +1.06 | +0.00 (0.00) | +0.06 (0.91) | +3.54 |
| DET | DET00 | 24 | +1.31 (1.35) | +0.97 | +0.00 (0.00) | +0.27 (0.91) | +2.14 |
| BUF | BUF00 | 27 | +1.12 (1.29) | +0.87 | +0.00 (0.00) | +0.28 (0.91) | +2.01 |
| JAX | JAX00 | 27 | +0.85 (1.30) | +0.66 | +0.00 (0.00) | +0.36 (0.91) | +2.74 |
| MIA | MIA00 | 27 | +0.79 (1.29) | +0.62 | +0.00 (0.00) | +0.58 (0.91) | +3.97 |
| IND | IND00 | 18 | +0.73 (1.56) | +0.47 | +0.00 (0.00) | +0.28 (0.91) | +2.49 |
| SEA | SEA00 | 24 | +0.68 (1.36) | +0.50 | +0.00 (0.00) | -0.64 (0.91) | +0.61 |
| CHI | CHI98 | 26 | +0.50 (1.30) | +0.39 | +0.00 (0.00) | +0.50 (0.91) | +2.92 |
| TEN | NAS00 | 27 | +0.47 (1.28) | +0.37 | +0.00 (0.00) | +0.17 (0.91) | +2.04 |
| CLE | CLE00 | 27 | +0.22 (1.28) | +0.18 | +0.00 (0.00) | +0.69 (0.91) | +2.84 |
| KC | KAN00 | 27 | +0.19 (1.28) | +0.15 | +0.00 (0.00) | -0.06 (0.91) | +1.51 |
| ATL | ATL97 | 9 | +0.18 (2.14) | +0.08 | +0.00 (0.00) | +0.03 (0.93) | +1.82 |
| HOU | HOU00 | 24 | -0.05 (1.36) | -0.04 | +0.00 (0.00) | -0.27 (0.91) | +1.99 |
| DAL | DAL00 | 17 | -0.34 (1.59) | -0.22 | +0.00 (0.00) | -0.01 (0.91) | +1.15 |
| ARI | PHO00 | 20 | -0.55 (1.48) | -0.37 | +0.00 (0.00) | -0.44 (0.91) | +0.23 |
| LA | LAX01 | 6 | -0.55 (2.56) | -0.22 | +0.00 (0.00) | -0.10 (0.94) | +1.61 |
| SF | SFO01 | 12 | -0.58 (1.87) | -0.31 | +0.00 (0.00) | -0.32 (0.92) | +1.34 |
| CAR | CAR00 | 27 | -0.76 (1.28) | -0.59 | +0.00 (0.00) | +0.24 (0.91) | +2.20 |
| PHI | PHI00 | 23 | -0.99 (1.38) | -0.71 | +0.00 (0.00) | -0.28 (0.91) | +1.89 |
| CIN | CIN00 | 26 | -1.14 (1.30) | -0.87 | +0.00 (0.00) | -0.17 (0.91) | +1.07 |
| NYG | NYC01 | 16 | -1.75 (1.64) | -1.06 | +0.00 (0.00) | -0.29 (0.91) | +0.51 |
| TB | TAM00 | 27 | -1.78 (1.28) | -1.39 | +0.00 (0.00) | -0.49 (0.91) | +0.41 |
| NE | BOS00 | 24 | -1.82 (1.36) | -1.34 | +0.00 (0.00) | -0.47 (0.91) | +1.64 |
| NO | NOR00 | 26 | -1.86 (1.30) | -1.43 | +0.00 (0.00) | -0.35 (0.91) | +0.24 |
| LAC | LAX01 | 6 | -2.15 (2.56) | -0.84 | +0.00 (0.00) | -0.22 (0.94) | +0.11 |
| WAS | WAS00 | 27 | -2.26 (1.28) | -1.77 | +0.00 (0.00) | -0.38 (0.91) | +0.59 |

The league's home margin each season, raw and after the model (actual minus the model's spread): 2014 +2.5 / -0.3; 2015 +1.5 / -0.9; 2016 +2.6 / +0.4; 2017 +2.5 / -0.1; 2018 +2.3 / -0.3; 2019 -0.0 / -2.2; 2020 +0.1 / -1.8; 2021 +1.6 / -0.3; 2022 +2.1 / +0.4; 2023 +2.7 / +0.9; 2024 +1.7 / -0.3; 2025 +2.2 / +0.1 (2026 so far, 46 games: +1.4 / -1.0).

## Every idea, under the rule

Changes are idea minus base, per window 2015-18 / 2019-22 / 2023-25. Misses in points (below zero is better); spread flag as the change in wins minus losses (the totals flag cannot move: these are points-equation ideas and the total has its own equation); calibrated log loss times 1000 (below zero is better). Rule 1 here needs both the team points miss and the margin miss lower on all three windows (the brief); the round-3 page used the team points miss alone, and the column 'team only' shows that reading.

### 1 Per-team home edge (empirical Bayes)

With tau estimated, the input is zero for 82% of team-seasons and at most 0.14 points otherwise, so these three runs are the base plus noise from a handful of values; their fitted weights are meaningless. With tau forced to 1 point, every team gets an edge (sd 0.32 points). The live ridge then fits it a *negative* weight (-0.1 to -0.6 of margin per point): a team's past home edge slightly anti-predicts its next. Every forced version is worse on the 2015-18 team points miss and on the calibrated log loss in 2015-18 and 2019-22. Leaving 2020 (no crowds) out of the history changes little, and scaling the edge by the visitor's trip is worse on all three windows.

| Idea | Team points miss | Margin miss | Spread flag W-L | Log loss x1000 | Rule 1 (team only) | Rule 2 | Placebo | Verdict |
|---|---|---|---|---|---|---|---|---|
| Team home edge, EB (estimated tau), half-life 2 | +0.0009 / -0.0002 / -0.0016 | +0.0017 / +0.0003 / -0.0033 | +1 / +0 / +1 | +0.17 / -0.09 / -0.21 | no (no) | no | not run | not adopted: rule 1 (2015-18, 2019-22); rule 2 (2015-18 log loss) |
| Team home edge, EB (estimated tau), half-life 3 | -0.0003 / -0.0003 / +0.0005 | -0.0049 / -0.0002 / +0.0017 | +0 / -3 / -1 | -0.23 / -0.07 / +0.08 | no (no) | no | not run | not adopted: rule 1 (2023-25); rule 2 (2019-22 spread; 2023-25 spread/log loss) |
| Team home edge, EB (estimated tau), half-life 4 | -0.0008 / -0.0006 / +0.0001 | -0.0028 / -0.0023 / -0.0007 | -3 / -2 / +0 | -0.06 / -0.22 / +0.09 | no (no) | no | not run | not adopted: rule 1 (2023-25); rule 2 (2015-18 spread; 2019-22 spread; 2023-25 log loss) |
| Team home edge, EB (tau forced to 1 pt), half-life 2 | +0.0035 / +0.0019 / -0.0008 | +0.0077 / +0.0093 / -0.0019 | +1 / -2 / -1 | +0.35 / +0.72 / +0.26 | no (no) | no | not run | not adopted: rule 1 (2015-18, 2019-22); rule 2 (2015-18 log loss; 2019-22 spread/log loss; 2023-25 spread/log loss) |
| Team home edge, EB (tau forced to 1 pt), half-life 3 | +0.0022 / +0.0002 / +0.0002 | +0.0062 / +0.0074 / +0.0018 | +1 / -4 / +1 | +0.38 / +0.40 / +0.13 | no (no) | no | beaten by 14 of 20; pct 50 / 70 / 65 | not adopted: rule 1 (2015-18, 2019-22, 2023-25); rule 2 (2015-18 log loss; 2019-22 spread/log loss; 2023-25 log loss) |
| Team home edge, EB (tau forced to 1 pt), half-life 4 | +0.0018 / +0.0016 / -0.0004 | +0.0040 / +0.0088 / +0.0018 | -2 / -3 / -1 | +0.55 / +0.63 / +0.01 | no (no) | no | not run | not adopted: rule 1 (2015-18, 2019-22, 2023-25); rule 2 (2015-18 spread/log loss; 2019-22 spread/log loss; 2023-25 spread/log loss) |
| Team home edge, EB (tau 1 pt), half-life 3, 2020 left out | +0.0022 / -0.0003 / +0.0002 | +0.0062 / +0.0037 / -0.0025 | +1 / +0 / -1 | +0.38 / +0.35 / +0.07 | no (no) | no | not run | not adopted: rule 1 (2015-18, 2019-22, 2023-25); rule 2 (2015-18 log loss; 2019-22 log loss; 2023-25 spread/log loss) |
| Team home edge, EB (tau 1 pt), half-life 3, x visitor travel | +0.0015 / +0.0029 / +0.0011 | +0.0020 / +0.0089 / -0.0007 | -3 / -4 / -3 | +0.27 / +0.07 / -0.02 | no (no) | no | not run | not adopted: rule 1 (2015-18, 2019-22, 2023-25); rule 2 (2015-18 spread/log loss; 2019-22 spread/log loss; 2023-25 spread) |

Fitted weights (live ridge, every regular-season game 2013-2025): Team home edge, EB (estimated tau), half-life 2: hf_x: -0.677/unit (margin -1.354), -0.099/sd, nonzero 22%; home: +1.830 | Team home edge, EB (estimated tau), half-life 3: hf_x: -0.083/unit (margin -0.167), -0.005/sd, nonzero 22%; home: +1.831 | Team home edge, EB (estimated tau), half-life 4: hf_x: +3.665/unit (margin +7.330), +0.067/sd, nonzero 7%; home: +1.831 | Team home edge, EB (tau forced to 1 pt), half-life 2: hf_x: -0.310/unit (margin -0.620), -0.088/sd, nonzero 96%; home: +1.835 | Team home edge, EB (tau forced to 1 pt), half-life 3: hf_x: -0.146/unit (margin -0.293), -0.047/sd, nonzero 96%; home: +1.833 | Team home edge, EB (tau forced to 1 pt), half-life 4: hf_x: -0.064/unit (margin -0.127), -0.022/sd, nonzero 96%; home: +1.832 | Team home edge, EB (tau 1 pt), half-life 3, 2020 left out: hf_x: -0.122/unit (margin -0.244), -0.038/sd, nonzero 96%; home: +1.833 | Team home edge, EB (tau 1 pt), half-life 3, x visitor travel: hf_x: +0.040/unit (margin +0.080), +0.018/sd, nonzero 96%; home: +1.830

### 2 Stadium features

Crowd size: skipped. No pulled source carries stadium capacity or attendance (the schedule has stadium, roof, surface, weather), and the brief said to skip rather than invent. Altitude uses round 3's static stadium table (elevation); travel and time zones use its coordinates and zones; both are fixed public facts round 3 used, not a data pull. Denver's home edge fits +1.9 points of margin, but 3% of games carry it and it loses on the 2015-18 margin. Travel and time zones interacted with the home edge both lower the team points miss on all three windows, and both fit the *wrong* sign for a travel story: the farther the visitor came, the *smaller* the home edge (-0.46 points of margin per 1,000 miles; -0.45 per time zone). The live home weight rises to 2.26 to compensate. So this is the short-trip and division games (angle 3) carrying more of the edge, not long trips wearing visitors down. Round 3 found the same: visitors flying 2,000+ miles beat the model's margin.

| Idea | Team points miss | Margin miss | Spread flag W-L | Log loss x1000 | Rule 1 (team only) | Rule 2 | Placebo | Verdict |
|---|---|---|---|---|---|---|---|---|
| Home edge at altitude (Denver) | -0.0018 / +0.0000 / -0.0028 | +0.0134 / -0.0041 / -0.0064 | +1 / -1 / +0 | +0.22 / -0.00 / -0.77 | no (no) | no | not run | not adopted: rule 1 (2015-18, 2019-22); rule 2 (2015-18 log loss; 2019-22 spread) |
| Home edge in a dome or closed roof | +0.0021 / -0.0025 / +0.0001 | +0.0066 / -0.0039 / +0.0077 | +2 / -4 / -1 | +0.37 / -0.52 / +0.17 | no (no) | no | not run | not adopted: rule 1 (2015-18, 2023-25); rule 2 (2015-18 log loss; 2019-22 spread; 2023-25 spread/log loss) |
| Home edge x visitor's travel miles | -0.0011 / -0.0002 / -0.0039 | -0.0028 / +0.0018 / -0.0067 | +3 / +3 / -1 | +0.24 / +0.17 / -0.47 | no (yes) | no | beaten by 8 of 12; pct 58 / 58 / 100 | not adopted: rule 1 (2019-22); rule 2 (2015-18 log loss; 2019-22 log loss; 2023-25 spread) |
| Home edge x visitor's time-zone change | -0.0002 / -0.0032 / -0.0088 | +0.0003 / -0.0033 / -0.0082 | +1 / -2 / -7 | +0.41 / -0.70 / -0.81 | no (yes) | no | beaten by 7 of 20; pct 70 / 95 / 100 | not adopted: rule 1 (2015-18); rule 2 (2015-18 log loss; 2019-22 spread; 2023-25 spread) |
| Neutral sites: home edge set to zero | -0.0021 / -0.0005 / +0.0027 | -0.0081 / -0.0079 / +0.0167 | -1 / +0 / -4 | +0.08 / -0.50 / +0.89 | no (no) | no | not run | not adopted: rule 1 (2023-25); rule 2 (2015-18 spread/log loss; 2023-25 spread/log loss) |
| Neutral sites: own home-edge term | -0.0010 / +0.0009 / +0.0015 | +0.0041 / -0.0044 / +0.0076 | -5 / +1 / -1 | +0.73 / -0.32 / +0.49 | no (no) | no | not run | not adopted: rule 1 (2015-18, 2019-22, 2023-25); rule 2 (2015-18 spread/log loss; 2023-25 spread/log loss) |

Fitted weights (live ridge, every regular-season game 2013-2025): Home edge at altitude (Denver): hf_den_home: +0.947/unit (margin +1.895), +0.168/sd, nonzero 3%; home: +1.772 | Home edge in a dome or closed roof: hf_dome_home: -0.237/unit (margin -0.474), -0.125/sd, nonzero 28%; home: +1.964 | Home edge x visitor's travel miles: hf_vis_miles: -0.229/unit (margin -0.457), -0.262/sd, nonzero 98%; home: +2.257 | Home edge x visitor's time-zone change: hf_vis_tz: -0.227/unit (margin -0.454), -0.318/sd, nonzero 57%; home: +2.261 | Neutral sites: home edge set to zero: home_nn: +1.844/unit (margin +1.844), +0.922/sd, nonzero 49% | Neutral sites: own home-edge term: hf_neutral: -0.408/unit (margin -0.816), -0.052/sd, nonzero 2%; home: +1.844

### 3 Home edge vs the visitor

Division games fit a smaller home edge (-0.58 points of margin: familiarity), but the idea is worse on all three windows and loses 15 spread wins on 2019-25. The visitor's own road record: the differenced home-minus-road residual cannot tell 'strong at home' from 'weak on the road' (the same number), so this uses the visitor's shrunk road residual *level*, which carries some rating error with it. Its estimated tau is positive from 2020 on (0.5 to 1.2 points), but as an input it raises the margin miss on 2019-22 by 0.048 and loses spread wins.

| Idea | Team points miss | Margin miss | Spread flag W-L | Log loss x1000 | Rule 1 (team only) | Rule 2 | Placebo | Verdict |
|---|---|---|---|---|---|---|---|---|
| Home edge in division games | +0.0013 / +0.0047 / +0.0009 | +0.0031 / +0.0174 / +0.0039 | +6 / -9 / -6 | -0.97 / +1.31 / -0.03 | no (no) | no | not run | not adopted: rule 1 (2015-18, 2019-22, 2023-25); rule 2 (2019-22 spread/log loss; 2023-25 spread) |
| Visitor travels well (road residual, EB estimated tau, half-life 3) | +0.0000 / +0.0000 / -0.0025 | +0.0000 / +0.0481 / -0.0158 | +0 / +0 / -1 | -0.00 / +2.13 / -0.56 | no (no) | no | not run | not adopted: rule 1 (2015-18, 2019-22); rule 2 (2019-22 log loss; 2023-25 spread) |
| Visitor travels well (road residual, EB tau 1 pt, half-life 3) | +0.0017 / +0.0012 / -0.0007 | +0.0008 / +0.0169 / -0.0109 | -7 / -4 / +1 | +1.49 / +0.09 / -0.23 | no (no) | no | not run | not adopted: rule 1 (2015-18, 2019-22); rule 2 (2015-18 spread/log loss; 2019-22 spread/log loss) |

Fitted weights (live ridge, every regular-season game 2013-2025): Home edge in division games: hf_div_home: -0.289/unit (margin -0.578), -0.174/sd, nonzero 36%; home: +2.040 | Visitor travels well (road residual, EB estimated tau, half-life 3): hf_x: +0.690/unit (margin +1.379), +0.201/sd, nonzero 47%; home: +1.832 | Visitor travels well (road residual, EB tau 1 pt, half-life 3): hf_x: +0.376/unit (margin +0.753), +0.169/sd, nonzero 98%; home: +1.830

### 4 Home edge by season stage

Early (weeks 1-4) and late (week 13 on, playoffs included) home edges fit -0.05 and +0.19 points of margin: nearly flat. The pair helps 2015-18 only and loses 6 spread wins there. A cold-weather home team (not warm or dome) from December fits +0.15 points and is worse on every window.

| Idea | Team points miss | Margin miss | Spread flag W-L | Log loss x1000 | Rule 1 (team only) | Rule 2 | Placebo | Verdict |
|---|---|---|---|---|---|---|---|---|
| Home edge early (weeks 1-4) and late (week 13 on) | -0.0036 / +0.0018 / +0.0025 | -0.0025 / +0.0080 / +0.0045 | -6 / +1 / -1 | +0.16 / +0.15 / +0.08 | no (no) | no | not run | not adopted: rule 1 (2019-22, 2023-25); rule 2 (2015-18 spread/log loss; 2019-22 log loss; 2023-25 spread/log loss) |
| Cold-weather home team in December on | +0.0012 / +0.0006 / +0.0013 | +0.0070 / +0.0030 / +0.0051 | -2 / +0 / +2 | +0.45 / -0.01 / +0.34 | no (no) | no | not run | not adopted: rule 1 (2015-18, 2019-22, 2023-25); rule 2 (2015-18 spread/log loss; 2023-25 log loss) |

Fitted weights (live ridge, every regular-season game 2013-2025): Home edge early (weeks 1-4) and late (week 13 on): hf_early_home: -0.026/unit (margin -0.053), -0.013/sd, nonzero 24%; hf_late_home: +0.096/unit (margin +0.191), +0.054/sd, nonzero 32%; home: +1.783 | Cold-weather home team in December on: hf_colddec_home: +0.075/unit (margin +0.150), +0.029/sd, nonzero 15%; home: +1.810

### 5 Partial pooling in the ridge

One signed dummy per team-and-stadium (41 active over 2013-2025) in the six ridges with a prior sd of 0.5 or 1 point of margin, in place of 32 free inputs. The variance-components estimate would set the prior sd at zero (an infinite penalty, the base), so it is set by hand. At 0.5 the fitted team edges run -0.39 to +0.28 points, barely move the misses and cost 3 spread wins on 2023-25; at 1 point, -1.14 to +0.82, worse on all three windows and 11 spread wins lost on 2023-25.

| Idea | Team points miss | Margin miss | Spread flag W-L | Log loss x1000 | Rule 1 (team only) | Rule 2 | Placebo | Verdict |
|---|---|---|---|---|---|---|---|---|
| Team home dummies, partial pooling (prior sd 0.5 pt) | +0.0000 / -0.0002 / +0.0005 | +0.0009 / -0.0009 / +0.0049 | +0 / +0 / -3 | +0.09 / +0.09 / -0.11 | no (no) | no | not run | not adopted: rule 1 (2015-18, 2023-25); rule 2 (2015-18 log loss; 2019-22 log loss; 2023-25 spread) |
| Team home dummies, partial pooling (prior sd 1 pt) | +0.0008 / +0.0013 / +0.0026 | +0.0060 / +0.0011 / +0.0171 | +5 / +5 / -11 | +0.47 / +0.49 / -0.08 | no (no) | no | beaten by 19 of 20; pct 55 / 60 / 20 | not adopted: rule 1 (2015-18, 2019-22, 2023-25); rule 2 (2015-18 log loss; 2019-22 log loss; 2023-25 spread) |

Fitted weights (live ridge, every regular-season game 2013-2025): Team home dummies, partial pooling (prior sd 0.5 pt): penalty 1436 (tau 0.50 margin pts, sigma 9.47); dummy margin effects sd 0.126, range -0.39 to +0.28 | Team home dummies, partial pooling (prior sd 1 pt): penalty 359 (tau 1.00 margin pts, sigma 9.47); dummy margin effects sd 0.375, range -1.14 to +0.82

## Caveats

- **Changes are small either way:** the largest margin-miss move is +0.048 (visitor road record, 2019-22); every team-points move is under 0.01.
- **Rule 1 as the brief wrote it** (team points *and* margin lower on every window) is stricter than round 3's (team points only). Both readings are in the table and the CSV. No idea passes rules 1 and 2 under either.
- **Placebo.** The rule's placebo gate (ideas passing 1 and 2) is empty. The information runs shuffle the team labels within season (per-team ideas) or the game flags within season (flags). The two travel ideas stopped once 6 draws beat them; the other two ran 20 draws. An idea already worse than base on some window is 'beaten' by any draw, so for those only the percentiles say anything.
- **Chance alone.** 21 ideas; about one in eight would pass the team-points reading of rule 1 by chance (2 to 3 expected); 2 did.
- **Forced tau.** The data say tau is zero; the tau = 1 point and partial-pooling runs deliberately impose more team spread than the data support, to test the angle and not just the estimator. That they fail is the expected result given the variance components.
- **Residual source.** Before 2014 the histories use round 3's plain scoring rating. With half-lives of 2 to 4 seasons its weight on 2017+ predictions is small; for 2015-16 it is most of the history.
- **2020** had no crowds and the model's home residual was -1.8 points that season (-2.2 in 2019). Centring each season on its league mean removes the level; dropping 2020 from the histories changes little.
- **No new data source, no market input, no look-ahead** (rule 4): every input comes from the schedule (`games.parquet`) and round 3's static stadium table, and team values use prior seasons only. Capacity and attendance would need a new source and were not built.
- **The neutral-site pricing** (full home edge for the listed home team) is not a rule-passing change either way: zeroing it helps 2015-18 and 2019-22 and costs 2023-25 (margin +0.017, 4 spread wins). It is recorded as a finding, not a recommendation.
- Fresh trees on this machine move the base slightly from the live `pred_v3` (round 3 measured 0.008 points on average), so base and idea are compared like for like, not against the live file.
