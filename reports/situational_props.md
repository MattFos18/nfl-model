# Situational, kickoff, weather, injury and player-vs-player ideas on the per-game props (round 3, 29 Sep 2026)

`experiments/situational_props.py` (+ `experiments/situational_props_feats.py`); every number in `reports/situational_props.csv`.
The rule is `reports/round3_rule.md`, written before any result, read for props as: (1) the miss lower on 2017-18, 2019-22
and 2023-25 (yards MAE per player-game; receptions, targets, carries and dropbacks MAE; touchdown and interception Poisson
log loss); an input that has no data before 2018 is judged on the two later windows with 2017-18 not worse; (2) the
calibrated chance on the lines (props.chance_over: the K nearest past lines of the variant's own reference table) no worse
in log loss on any window (2017-18 = 2018, the first season with a reference), at book numbers x = the rule's line + delta
(+-15 yards by 5, passing +-45 by 15, receptions +-2), and the lean record against the real book lines where the harness
has them (data/lines/props_log.csv, the consensus of each book's last pre-kickoff line: 2026 Week 3 only, about 80 to 160
decided sides per stat) not worse; (3) 50 within-season shuffles of the input, each refitted the same way, and the real gain
above the placebo's in at least 45 of 50 on every window; (4) as of before the game, no market input, no new source;
(5) the passing pieces refitted together must pass 1 and 2.

**How each idea is applied.** A multiplicative factor on the live line (after the median factor, the team reconciliation
and the injury/snap factor), exp(size x input). The size (and for a player's own history its shrinkage k) is refitted
walk-forward: every season is scored with the value that minimises the miss over all earlier seasons from 2016 (the build
keeps the 2016 player-games only as fitting rows; the harness scores from 2017), never on the season scored. Three shapes:
L, a condition or level centred on the player's own 0.85-decayed history of it (his rate already carries the conditions he
played in), pooled and, for receivers and rushers, a separate size per position group (WR / TE / RB; RB / QB); P, his own
split of a condition in log residual against the rule's line, shrunk toward the league's split (k player-games), applied to
the centred condition; H / C, his residual history at a key (stadium, opposing head coach, opponent, this week's corners)
over his own average, shrunk with k. The frames reproduce data/processed/props_reference.parquet's lines exactly (max
difference 1e-14).

**Scope limits, stated plainly.** Weather: the backtest has no archive of the kickoff forecast; the only historical weather
is the recorded kickoff reading (the schedule's wind and temperature, the play-by-play's weather text for rain and snow),
the same stand-in the game model's backtest and the props' own wind rule (WIND_C) were fitted on. Live, the Open-Meteo
kickoff forecast takes its place, which is noisier, so any weather gain here is an upper bound. Kickers and QB sacks are not
scored by this harness (kickers live in props_backtest9), so the FG / kicker props and the sack side of pass rush vs
protection are not tested. Injuries: only this week's final report (Out / Doubtful) and the weekly roster's active flag,
never game-day actives. The defensive play-caller is not in any pulled data (the schedule names head coaches only).


## Tally

1221 idea x stat x variant tests in Task A and the four added families: 60 pass rule 1 (every window lower), 30 pass rules 1-2, 13 pass rules 1-3 (Task B and the combinations are counted in their own sections). The walk-forward fit often keeps no effect for a season (a window with no change counts as not better), so fewer than the one in eight a coin flip per window would give pass rule 1; the placebo, not rule 1, is what separates a small real gain.


## Situational

Surface, roof, home, division, rest, travel (the static stadium table), time zones, altitude, former team; his own turf / indoor / home / division splits; his history at the stadium, against the opposing head coach and against the opponent.

347 tests; 13 pass rule 1. Every test that passes rule 1 (the rest, with every number, are in reports/situational_props.csv):

| idea | variant | stat | miss 2017-18 | 2019-22 | 2023-25 | chance LL 2018 / 19-22 / 23-25 | lean rule / variant | placebo (beaten of 50, worst window) | verdict |
|---|---|---|---|---|---|---|---|---|---|
| turf | pooled | rush_carries | -0.0014 | -0.0002 | -0.0008 |  /  /  | 44-40 / 42-42 |  | fails 2 (lean record) |
| indoor | pooled | rec_td | -0.0000 | -0.0001 | -0.0000 |  /  /  | 156-68 / 157-67 | 40 | fails 3 (placebo, worst window beaten in 40/50) |
| indoor | by position | rec_td | -0.0001 | -0.0000 | -0.0000 |  /  /  | 156-68 / 158-66 | 43 | fails 3 (placebo, worst window beaten in 43/50) |
| rest_days | pooled | rec_catches | -0.0005 | -0.0004 | -0.0007 | -0.00038 / -0.00023 / -0.00021 | 81-81 / 81-81 | 49 | passes 1-3 |
| rest_days | by position | rec_catches | -0.0008 | -0.0004 | -0.0003 | -0.00089 / -0.00034 / -0.00008 | 81-81 / 82-80 | 49 | passes 1-3 |
| rest_days | pooled | rec_targets | -0.0005 | -0.0001 | -0.0004 |  /  /  | 84-63 / 84-63 | 46 | passes 1-3 |
| rest_diff | pooled | rec_catches | -0.0002 | -0.0003 | -0.0002 | -0.00047 / -0.00026 / -0.00011 | 81-81 / 83-79 | 43 | fails 3 (placebo, worst window beaten in 43/50) |
| rest_diff | pooled | rec_targets | -0.0005 | -0.0001 | -0.0002 |  /  /  | 84-63 / 84-63 | 44 | fails 3 (placebo, worst window beaten in 44/50) |
| rest_diff | pooled | rush_yards | -0.0073 | -0.0005 | -0.0042 | -0.00061 / +0.00050 / +0.00011 | 40-46 / 39-47 |  | fails 2 (chance 2019-22, chance 2023-25, lean record) |
| rest_diff | pooled | rush_carries | -0.0005 | -0.0002 | -0.0018 |  /  /  | 44-40 / 43-41 |  | fails 2 (lean record) |
| travel | pooled | rec_catches | -0.0001 | -0.0001 | -0.0001 | -0.00014 / +0.00003 / -0.00012 | 81-81 / 82-80 |  | fails 2 (chance 2019-22) |
| altitude | by position | rush_td | -0.0001 | -0.0002 | -0.0002 |  /  /  | 71-30 / 69-32 |  | fails 2 (lean record) |
| vs_opponent | pooled | rec_td | -0.0000 | -0.0002 | -0.0000 |  /  /  | 156-68 / 155-69 |  | fails 2 (lean record) |

Every idea x stat, the furthest any variant got (1 = fails the windows, 2 = fails the chance or lean record, 3 = fails its placebo, A = passes 1-3, . = not tested):

| idea | rec_yards | rec_catches | rec_targets | rec_td | rush_yards | rush_carries | rush_td | pass_yards | pass_dropbacks | pass_td | pass_int |
|---|---|---|---|---|---|---|---|---|---|---|---|
| turf | 1 | 1 | 1 | 1 | 1 | 2 | 1 | 1 | 1 | 1 | 1 |
| indoor | 1 | 1 | 1 | 3 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| dome_fixed | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| home | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| division | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| short_week | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| off_bye | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| rest_days | 1 | A | A | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| rest_diff | 1 | 3 | 3 | 1 | 2 | 2 | 1 | 1 | 1 | 1 | 1 |
| opp_off_bye | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| travel | 1 | 2 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| tz_signed | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| tz_abs | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| altitude | 1 | 1 | 1 | 1 | 1 | 1 | 2 | 1 | 1 | 1 | 1 |
| vs_former_team | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| own_turf_split | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| own_indoor_split | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| own_home_split | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| own_division_split | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| at_stadium | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| vs_head_coach | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| vs_opponent | 1 | 1 | 1 | 2 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |

Readings: the size the last walk-forward refit (on 2016-2025) carries, per unit of the input for an on/off input (per standard deviation otherwise), and in the stat's units at the group's mean line over 2019-25. A size of 0 means the fit found nothing worth moving:

| idea | stat | size |
|---|---|---|
| turf | rec_yards | WR +3.69% on vs off (+1.24 at a 33.6 line); TE +0.00% on vs off (+0.00 at a 20.9 line); RB +4.77% on vs off (+0.68 at a 14.3 line); other +86.04% on vs off (+8.21 at a 9.5 line) |
| turf | rec_targets | WR +0.00% on vs off (+0.00 at a 5.0 line); TE +1.56% on vs off (+0.05 at a 3.4 line); RB +0.00% on vs off (+0.00 at a 2.7 line); other +28.85% on vs off (+0.51 at a 1.8 line) |
| turf | rush_yards | RB +0.52% on vs off (+0.18 at a 34.8 line); QB +5.85% on vs off (+0.85 at a 14.6 line); other +20.44% on vs off (+0.68 at a 3.3 line) |
| turf | rush_carries | RB +2.62% on vs off (+0.24 at a 9.1 line); QB +2.09% on vs off (+0.08 at a 3.7 line); other +13.20% on vs off (+0.10 at a 0.7 line) |
| turf | pass_yards | all +0.52% on vs off (+1.19 at a 228.9 line) |
| indoor | rec_yards | WR +6.92% on vs off (+2.32 at a 33.6 line); TE -0.61% on vs off (-0.13 at a 20.9 line); RB +3.09% on vs off (+0.44 at a 14.3 line); other +107.42% on vs off (+10.25 at a 9.5 line) |
| indoor | rec_targets | WR +0.61% on vs off (+0.03 at a 5.0 line); TE -1.21% on vs off (-0.04 at a 3.4 line); RB +0.00% on vs off (+0.00 at a 2.7 line); other +53.98% on vs off (+0.96 at a 1.8 line) |
| indoor | rush_yards | RB -0.61% on vs off (-0.21 at a 34.8 line); QB +5.63% on vs off (+0.82 at a 14.6 line); other -9.82% on vs off (-0.32 at a 3.3 line) |
| indoor | rush_carries | RB +1.22% on vs off (+0.11 at a 9.1 line); QB +2.46% on vs off (+0.09 at a 3.7 line); other -4.17% on vs off (-0.03 at a 0.7 line) |
| indoor | pass_yards | all +1.83% on vs off (+4.19 at a 228.9 line) |
| dome_fixed | rec_yards | WR +6.92% on vs off (+2.32 at a 33.6 line); TE -4.10% on vs off (-0.86 at a 20.9 line); RB -0.83% on vs off (-0.12 at a 14.3 line); other +82.67% on vs off (+7.89 at a 9.5 line) |
| dome_fixed | rec_targets | WR +1.69% on vs off (+0.08 at a 5.0 line); TE -0.83% on vs off (-0.03 at a 3.4 line); RB -0.83% on vs off (-0.02 at a 2.7 line); other +69.41% on vs off (+1.24 at a 1.8 line) |
| dome_fixed | rush_yards | RB -2.51% on vs off (-0.87 at a 34.8 line); QB +10.70% on vs off (+1.56 at a 14.6 line); other -26.28% on vs off (-0.87 at a 3.3 line) |
| dome_fixed | rush_carries | RB +1.71% on vs off (+0.16 at a 9.1 line); QB +5.21% on vs off (+0.19 at a 3.7 line); other +10.70% on vs off (+0.08 at a 0.7 line) |
| dome_fixed | pass_yards | all +0.84% on vs off (+1.92 at a 228.9 line) |
| home | rec_yards | WR +1.79% on vs off (+0.60 at a 33.6 line); TE +0.00% on vs off (+0.00 at a 20.9 line); RB +3.15% on vs off (+0.45 at a 14.3 line); other +65.05% on vs off (+6.21 at a 9.5 line) |
| home | rec_targets | WR +0.44% on vs off (+0.02 at a 5.0 line); TE +0.89% on vs off (+0.03 at a 3.4 line); RB +0.44% on vs off (+0.01 at a 2.7 line); other +62.14% on vs off (+1.11 at a 1.8 line) |
| home | rush_yards | RB +1.78% on vs off (+0.62 at a 34.8 line); QB +1.34% on vs off (+0.19 at a 14.6 line); other -21.24% on vs off (-0.70 at a 3.3 line) |
| home | rush_carries | RB +1.34% on vs off (+0.12 at a 9.1 line); QB +4.06% on vs off (+0.15 at a 3.7 line); other -10.47% on vs off (-0.08 at a 0.7 line) |
| home | pass_yards | all +0.45% on vs off (+1.03 at a 228.9 line) |
| division | rec_yards | WR -0.93% on vs off (-0.31 at a 33.6 line); TE +0.94% on vs off (+0.20 at a 20.9 line); RB -2.76% on vs off (-0.39 at a 14.3 line); other -38.78% on vs off (-3.70 at a 9.5 line) |
| division | rec_targets | WR -0.47% on vs off (-0.02 at a 5.0 line); TE +0.94% on vs off (+0.03 at a 3.4 line); RB -1.39% on vs off (-0.04 at a 2.7 line); other -37.91% on vs off (-0.68 at a 1.8 line) |
| division | rush_yards | RB +1.89% on vs off (+0.66 at a 34.8 line); QB +0.00% on vs off (+0.00 at a 14.6 line); other +25.16% on vs off (+0.83 at a 3.3 line) |
| division | rush_carries | RB -0.93% on vs off (-0.08 at a 9.1 line); QB -3.22% on vs off (-0.12 at a 3.7 line); other +5.28% on vs off (+0.04 at a 0.7 line) |
| division | pass_yards | all -3.66% on vs off (-8.38 at a 228.9 line) |
| short_week | rec_yards | WR +9.64% on vs off (+3.24 at a 33.6 line); TE +2.80% on vs off (+0.59 at a 20.9 line); RB -7.10% on vs off (-1.01 at a 14.3 line); other +94.00% on vs off (+8.97 at a 9.5 line) |
| short_week | rec_targets | WR +3.75% on vs off (+0.19 at a 5.0 line); TE +0.92% on vs off (+0.03 at a 3.4 line); RB +0.92% on vs off (+0.03 at a 2.7 line); other +201.78% on vs off (+3.60 at a 1.8 line) |
| short_week | rush_yards | RB +0.00% on vs off (+0.00 at a 34.8 line); QB -12.96% on vs off (-1.89 at a 14.6 line); other -67.07% on vs off (-2.22 at a 3.3 line) |
| short_week | rush_carries | RB +2.82% on vs off (+0.26 at a 9.1 line); QB -2.74% on vs off (-0.10 at a 3.7 line); other +22.58% on vs off (+0.16 at a 0.7 line) |
| short_week | pass_yards | all +1.88% on vs off (+4.30 at a 228.9 line) |
| off_bye | rec_yards | WR -5.92% on vs off (-1.99 at a 33.6 line); TE -6.74% on vs off (-1.41 at a 20.9 line); RB -4.27% on vs off (-0.61 at a 14.3 line); other +26.54% on vs off (+2.53 at a 9.5 line) |
| off_bye | rec_targets | WR -3.43% on vs off (-0.17 at a 5.0 line); TE +0.00% on vs off (+0.00 at a 3.4 line); RB -2.58% on vs off (-0.07 at a 2.7 line); other +23.27% on vs off (+0.41 at a 1.8 line) |
| off_bye | rush_yards | RB +1.71% on vs off (+0.60 at a 34.8 line); QB +4.34% on vs off (+0.63 at a 14.6 line); other +31.25% on vs off (+1.03 at a 3.3 line) |
| off_bye | rush_carries | RB +1.71% on vs off (+0.16 at a 9.1 line); QB +15.54% on vs off (+0.57 at a 3.7 line); other +5.23% on vs off (+0.04 at a 0.7 line) |
| off_bye | pass_yards | all -0.87% on vs off (-2.00 at a 228.9 line) |
| rest_days | rec_yards | WR -2.70% per sd (2.02) (-0.91 at a 33.6 line); TE -1.25% per sd (2.02) (-0.26 at a 20.9 line); RB +0.21% per sd (2.02) (+0.03 at a 14.3 line); other +7.42% per sd (2.02) (+0.71 at a 9.5 line) |
| rest_days | rec_targets | WR -1.25% per sd (2.02) (-0.06 at a 5.0 line); TE +0.63% per sd (2.02) (+0.02 at a 3.4 line); RB -0.63% per sd (2.02) (-0.02 at a 2.7 line); other -8.46% per sd (2.02) (-0.15 at a 1.8 line) |
| rest_days | rush_yards | RB +0.63% per sd (2.03) (+0.22 at a 34.8 line); QB +4.05% per sd (2.03) (+0.59 at a 14.6 line); other +5.14% per sd (2.03) (+0.17 at a 3.3 line) |
| rest_days | rush_carries | RB +0.63% per sd (2.03) (+0.06 at a 9.1 line); QB +3.83% per sd (2.03) (+0.14 at a 3.7 line); other +0.42% per sd (2.03) (+0.00 at a 0.7 line) |
| rest_days | pass_yards | all -0.42% per sd (2.01) (-0.97 at a 228.9 line) |
| rest_diff | rec_yards | WR -1.21% per sd (2.45) (-0.41 at a 33.6 line); TE -2.40% per sd (2.45) (-0.50 at a 20.9 line); RB -0.61% per sd (2.45) (-0.09 at a 14.3 line); other +7.57% per sd (2.45) (+0.72 at a 9.5 line) |
| rest_diff | rec_targets | WR -1.21% per sd (2.45) (-0.06 at a 5.0 line); TE -0.40% per sd (2.45) (-0.01 at a 3.4 line); RB -0.81% per sd (2.45) (-0.02 at a 2.7 line); other -9.27% per sd (2.45) (-0.17 at a 1.8 line) |
| rest_diff | rush_yards | RB +1.62% per sd (2.46) (+0.56 at a 34.8 line); QB +1.82% per sd (2.46) (+0.27 at a 14.6 line); other +10.77% per sd (2.46) (+0.36 at a 3.3 line) |
| rest_diff | rush_carries | RB +1.01% per sd (2.46) (+0.09 at a 9.1 line); QB +3.06% per sd (2.46) (+0.11 at a 3.7 line); other +6.20% per sd (2.46) (+0.04 at a 0.7 line) |
| rest_diff | pass_yards | all -0.62% per sd (2.43) (-1.41 at a 228.9 line) |
| opp_off_bye | rec_yards | WR +0.00% on vs off (+0.00 at a 33.6 line); TE +6.57% on vs off (+1.37 at a 20.9 line); RB -0.90% on vs off (-0.13 at a 14.3 line); other +101.34% on vs off (+9.67 at a 9.5 line) |
| opp_off_bye | rec_targets | WR +0.91% on vs off (+0.05 at a 5.0 line); TE +0.91% on vs off (+0.03 at a 3.4 line); RB -1.80% on vs off (-0.05 at a 2.7 line); other -5.31% on vs off (-0.09 at a 1.8 line) |
| opp_off_bye | rush_yards | RB -4.40% on vs off (-1.53 at a 34.8 line); QB +12.40% on vs off (+1.81 at a 14.6 line); other -6.10% on vs off (-0.20 at a 3.3 line) |
| opp_off_bye | rush_carries | RB -2.66% on vs off (-0.24 at a 9.1 line); QB +3.66% on vs off (+0.13 at a 3.7 line); other -33.87% on vs off (-0.25 at a 0.7 line) |
| opp_off_bye | pass_yards | all +1.87% on vs off (+4.27 at a 228.9 line) |
| travel | rec_yards | WR -1.29% per sd (1.29) (-0.43 at a 33.6 line); TE -2.98% per sd (1.29) (-0.62 at a 20.9 line); RB +0.22% per sd (1.29) (+0.03 at a 14.3 line); other -22.82% per sd (1.29) (-2.18 at a 9.5 line) |
| travel | rec_targets | WR -0.43% per sd (1.29) (-0.02 at a 5.0 line); TE -1.07% per sd (1.29) (-0.04 at a 3.4 line); RB +0.00% per sd (1.29) (+0.00 at a 2.7 line); other -22.82% per sd (1.29) (-0.41 at a 1.8 line) |
| travel | rush_yards | RB -0.85% per sd (1.28) (-0.29 at a 34.8 line); QB -0.42% per sd (1.28) (-0.06 at a 14.6 line); other +3.46% per sd (1.28) (+0.11 at a 3.3 line) |
| travel | rush_carries | RB -0.85% per sd (1.28) (-0.08 at a 9.1 line); QB -0.64% per sd (1.28) (-0.02 at a 3.7 line); other +3.46% per sd (1.28) (+0.03 at a 0.7 line) |
| travel | pass_yards | all +0.00% per sd (1.3) (+0.00 at a 228.9 line) |
| tz_signed | rec_yards | WR +0.00% per sd (1.22) (+0.00 at a 33.6 line); TE -0.71% per sd (1.22) (-0.15 at a 20.9 line); RB -0.24% per sd (1.22) (-0.03 at a 14.3 line); other -17.54% per sd (1.22) (-1.67 at a 9.5 line) |
| tz_signed | rec_targets | WR -0.48% per sd (1.22) (-0.02 at a 5.0 line); TE +0.48% per sd (1.22) (+0.02 at a 3.4 line); RB +0.00% per sd (1.22) (+0.00 at a 2.7 line); other -24.85% per sd (1.22) (-0.44 at a 1.8 line) |
| tz_signed | rush_yards | RB +0.00% per sd (1.21) (+0.00 at a 34.8 line); QB +1.66% per sd (1.21) (+0.24 at a 14.6 line); other +12.78% per sd (1.21) (+0.42 at a 3.3 line) |
| tz_signed | rush_carries | RB +0.00% per sd (1.21) (+0.00 at a 9.1 line); QB +0.00% per sd (1.21) (+0.00 at a 3.7 line); other -0.70% per sd (1.21) (-0.01 at a 0.7 line) |
| tz_signed | pass_yards | all +0.46% per sd (1.23) (+1.05 at a 228.9 line) |
| tz_abs | rec_yards | WR -1.12% per sd (1.09) (-0.38 at a 33.6 line); TE -4.42% per sd (1.09) (-0.92 at a 20.9 line); RB +0.23% per sd (1.09) (+0.03 at a 14.3 line); other -23.76% per sd (1.09) (-2.27 at a 9.5 line) |
| tz_abs | rec_targets | WR -0.68% per sd (1.09) (-0.03 at a 5.0 line); TE -1.57% per sd (1.09) (-0.05 at a 3.4 line); RB +0.00% per sd (1.09) (+0.00 at a 2.7 line); other -23.76% per sd (1.09) (-0.42 at a 1.8 line) |
| tz_abs | rush_yards | RB -0.66% per sd (1.08) (-0.23 at a 34.8 line); QB -1.32% per sd (1.08) (-0.19 at a 14.6 line); other -1.32% per sd (1.08) (-0.04 at a 3.3 line) |
| tz_abs | rush_carries | RB -0.88% per sd (1.08) (-0.08 at a 9.1 line); QB -0.66% per sd (1.08) (-0.02 at a 3.7 line); other +0.67% per sd (1.08) (+0.00 at a 0.7 line) |
| tz_abs | pass_yards | all +0.22% per sd (1.1) (+0.50 at a 228.9 line) |
| altitude | rec_yards | WR -9.26% on vs off (-3.11 at a 33.6 line); TE -9.26% on vs off (-1.94 at a 20.9 line); RB +12.37% on vs off (+1.76 at a 14.3 line); other -38.49% on vs off (-3.67 at a 9.5 line) |
| altitude | rec_targets | WR -1.93% on vs off (-0.10 at a 5.0 line); TE -3.81% on vs off (-0.13 at a 3.4 line); RB -14.40% on vs off (-0.40 at a 2.7 line); other -47.35% on vs off (-0.84 at a 1.8 line) |
| altitude | rush_yards | RB +1.84% on vs off (+0.64 at a 34.8 line); QB -30.60% on vs off (-4.46 at a 14.6 line); other -72.67% on vs off (-2.40 at a 3.3 line) |
| altitude | rush_carries | RB -1.81% on vs off (-0.16 at a 9.1 line); QB -18.20% on vs off (-0.66 at a 3.7 line); other -1.81% on vs off (-0.01 at a 0.7 line) |
| altitude | pass_yards | all -5.62% on vs off (-12.86 at a 228.9 line) |
| vs_former_team | rec_yards | WR +4.08% on vs off (+1.37 at a 33.6 line); TE +24.59% on vs off (+5.14 at a 20.9 line); RB +6.18% on vs off (+0.88 at a 14.3 line); other -50.32% on vs off (-4.80 at a 9.5 line) |
| vs_former_team | rec_targets | WR +2.02% on vs off (+0.10 at a 5.0 line); TE +19.71% on vs off (+0.67 at a 3.4 line); RB -3.92% on vs off (-0.11 at a 2.7 line); other +34.96% on vs off (+0.62 at a 1.8 line) |
| vs_former_team | rush_yards | RB +9.64% on vs off (+3.36 at a 34.8 line); QB -15.26% on vs off (-2.23 at a 14.6 line); other -89.01% on vs off (-2.95 at a 3.3 line) |
| vs_former_team | rush_carries | RB +5.68% on vs off (+0.52 at a 9.1 line); QB -1.82% on vs off (-0.07 at a 3.7 line); other -89.01% on vs off (-0.64 at a 0.7 line) |
| vs_former_team | pass_yards | all -2.08% on vs off (-4.77 at a 228.9 line) |

## Primetime and kickoff time

Slots (Sunday 1 PM, 4 PM, night), days (Thursday, Saturday, Sunday, Monday), SNF / MNF / TNF each alone, the body clock (a Pacific or Mountain team at 1 PM ET; an Eastern team at a Pacific venue at 8 PM ET or later; the kickoff hour on the team's home clock), holidays and international venues; his own primetime and night splits. The Thursday short-week shift by position is the TNF and short-week rows by position group (carries for RB vs QB, targets for WR / TE / RB).

310 tests; 2 pass rule 1. Every test that passes rule 1 (the rest, with every number, are in reports/situational_props.csv):

| idea | variant | stat | miss 2017-18 | 2019-22 | 2023-25 | chance LL 2018 / 19-22 / 23-25 | lean rule / variant | placebo (beaten of 50, worst window) | verdict |
|---|---|---|---|---|---|---|---|---|---|
| TNF | pooled | pass_dropbacks | -0.0003 | -0.0003 | -0.0046 |  /  /  |  | 35 | fails 3 (placebo, worst window beaten in 35/50) |
| thursday | pooled | pass_dropbacks | -0.0003 | -0.0003 | -0.0046 |  /  /  |  | 37 | fails 3 (placebo, worst window beaten in 37/50) |

Every idea x stat, the furthest any variant got (1 = fails the windows, 2 = fails the chance or lean record, 3 = fails its placebo, A = passes 1-3, . = not tested):

| idea | rec_yards | rec_catches | rec_targets | rec_td | rush_yards | rush_carries | rush_td | pass_yards | pass_dropbacks | pass_td | pass_int |
|---|---|---|---|---|---|---|---|---|---|---|---|
| primetime | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| night | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| slot_early | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| slot_late | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| SNF | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| MNF | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| TNF | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 3 | 1 | 1 |
| thursday | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 3 | 1 | 1 |
| saturday | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| sunday | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| monday | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| west_team_1pm | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| east_team_late_west | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| body_clock_hour | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| holiday | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| international | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| own_primetime_split | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| own_night_split | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |

Readings: the size the last walk-forward refit (on 2016-2025) carries, per unit of the input for an on/off input (per standard deviation otherwise), and in the stat's units at the group's mean line over 2019-25. A size of 0 means the fit found nothing worth moving:

| idea | stat | size |
|---|---|---|
| primetime | rec_yards | WR -0.57% on vs off (-0.19 at a 33.6 line); TE +1.16% on vs off (+0.24 at a 20.9 line); RB -0.57% on vs off (-0.08 at a 14.3 line); other -43.48% on vs off (-4.15 at a 9.5 line) |
| primetime | rec_targets | WR +1.16% on vs off (+0.06 at a 5.0 line); TE +1.16% on vs off (+0.04 at a 3.4 line); RB +2.33% on vs off (+0.06 at a 2.7 line); other +67.02% on vs off (+1.19 at a 1.8 line) |
| primetime | rush_yards | RB -3.90% on vs off (-1.36 at a 34.8 line); QB +6.45% on vs off (+0.94 at a 14.6 line); other +18.58% on vs off (+0.61 at a 3.3 line) |
| primetime | rush_carries | RB -0.57% on vs off (-0.05 at a 9.1 line); QB +5.85% on vs off (+0.21 at a 3.7 line); other +8.90% on vs off (+0.06 at a 0.7 line) |
| primetime | pass_yards | all -0.58% on vs off (-1.33 at a 228.9 line) |
| night | rec_yards | WR -0.56% on vs off (-0.19 at a 33.6 line); TE +2.29% on vs off (+0.48 at a 20.9 line); RB -1.68% on vs off (-0.24 at a 14.3 line); other -43.23% on vs off (-4.13 at a 9.5 line) |
| night | rec_targets | WR +0.57% on vs off (+0.03 at a 5.0 line); TE +0.57% on vs off (+0.02 at a 3.4 line); RB +1.71% on vs off (+0.05 at a 2.7 line); other +65.52% on vs off (+1.17 at a 1.8 line) |
| night | rush_yards | RB -3.84% on vs off (-1.34 at a 34.8 line); QB +7.54% on vs off (+1.10 at a 14.6 line); other +18.93% on vs off (+0.63 at a 3.3 line) |
| night | rush_carries | RB -0.56% on vs off (-0.05 at a 9.1 line); QB +6.35% on vs off (+0.23 at a 3.7 line); other +9.36% on vs off (+0.07 at a 0.7 line) |
| night | pass_yards | all -0.57% on vs off (-1.30 at a 228.9 line) |
| slot_early | rec_yards | WR +0.00% on vs off (+0.00 at a 33.6 line); TE -2.90% on vs off (-0.61 at a 20.9 line); RB +0.49% on vs off (+0.07 at a 14.3 line); other +5.54% on vs off (+0.53 at a 9.5 line) |
| slot_early | rec_targets | WR +0.00% on vs off (+0.00 at a 5.0 line); TE -0.97% on vs off (-0.03 at a 3.4 line); RB +0.00% on vs off (+0.00 at a 2.7 line); other -44.17% on vs off (-0.79 at a 1.8 line) |
| slot_early | rush_yards | RB -0.98% on vs off (-0.34 at a 34.8 line); QB +0.00% on vs off (+0.00 at a 14.6 line); other -0.49% on vs off (-0.02 at a 3.3 line) |
| slot_early | rush_carries | RB +0.49% on vs off (+0.04 at a 9.1 line); QB -5.73% on vs off (-0.21 at a 3.7 line); other -5.73% on vs off (-0.04 at a 0.7 line) |
| slot_early | pass_yards | all +0.50% on vs off (+1.14 at a 228.9 line) |
| slot_late | rec_yards | WR -1.14% on vs off (-0.38 at a 33.6 line); TE -0.57% on vs off (-0.12 at a 20.9 line); RB +2.91% on vs off (+0.41 at a 14.3 line); other +28.66% on vs off (+2.74 at a 9.5 line) |
| slot_late | rec_targets | WR -1.14% on vs off (-0.06 at a 5.0 line); TE +0.57% on vs off (+0.02 at a 3.4 line); RB -1.14% on vs off (-0.03 at a 2.7 line); other +66.50% on vs off (+1.19 at a 1.8 line) |
| slot_late | rush_yards | RB +4.13% on vs off (+1.44 at a 34.8 line); QB -6.71% on vs off (-0.98 at a 14.6 line); other -15.45% on vs off (-0.51 at a 3.3 line) |
| slot_late | rush_carries | RB -1.15% on vs off (-0.10 at a 9.1 line); QB +1.75% on vs off (+0.06 at a 3.7 line); other +1.16% on vs off (+0.01 at a 0.7 line) |
| slot_late | pass_yards | all +0.00% on vs off (+0.00 at a 228.9 line) |
| SNF | rec_yards | WR -1.80% on vs off (-0.61 at a 33.6 line); TE +3.71% on vs off (+0.78 at a 20.9 line); RB -3.57% on vs off (-0.51 at a 14.3 line); other -47.59% on vs off (-4.54 at a 9.5 line) |
| SNF | rec_targets | WR +0.91% on vs off (+0.05 at a 5.0 line); TE +0.91% on vs off (+0.03 at a 3.4 line); RB -2.69% on vs off (-0.07 at a 2.7 line); other -37.13% on vs off (-0.66 at a 1.8 line) |
| SNF | rush_yards | RB -0.87% on vs off (-0.30 at a 34.8 line); QB +10.09% on vs off (+1.47 at a 14.6 line); other +17.03% on vs off (+0.56 at a 3.3 line) |
| SNF | rush_carries | RB -0.87% on vs off (-0.08 at a 9.1 line); QB +9.13% on vs off (+0.33 at a 3.7 line); other +16.01% on vs off (+0.12 at a 0.7 line) |
| SNF | pass_yards | all +0.00% on vs off (+0.00 at a 228.9 line) |
| MNF | rec_yards | WR -3.59% on vs off (-1.21 at a 33.6 line); TE +0.92% on vs off (+0.19 at a 20.9 line); RB +7.59% on vs off (+1.08 at a 14.3 line); other -66.64% on vs off (-6.36 at a 9.5 line) |
| MNF | rec_targets | WR -1.81% on vs off (-0.09 at a 5.0 line); TE +2.78% on vs off (+0.10 at a 3.4 line); RB +8.58% on vs off (+0.24 at a 2.7 line); other +49.57% on vs off (+0.88 at a 1.8 line) |
| MNF | rush_yards | RB -6.16% on vs off (-2.15 at a 34.8 line); QB +12.53% on vs off (+1.83 at a 14.6 line); other +19.92% on vs off (+0.66 at a 3.3 line) |
| MNF | rush_carries | RB -0.90% on vs off (-0.08 at a 9.1 line); QB +3.70% on vs off (+0.14 at a 3.7 line); other -13.52% on vs off (-0.10 at a 0.7 line) |
| MNF | pass_yards | all -1.88% on vs off (-4.31 at a 228.9 line) |
| TNF | rec_yards | WR +7.47% on vs off (+2.51 at a 33.6 line); TE +0.00% on vs off (+0.00 at a 20.9 line); RB -6.95% on vs off (-0.99 at a 14.3 line); other +103.71% on vs off (+9.90 at a 9.5 line) |
| TNF | rec_targets | WR +3.67% on vs off (+0.18 at a 5.0 line); TE -0.90% on vs off (-0.03 at a 3.4 line); RB +2.74% on vs off (+0.08 at a 2.7 line); other +194.69% on vs off (+3.47 at a 1.8 line) |
| TNF | rush_yards | RB -0.90% on vs off (-0.31 at a 34.8 line); QB -11.09% on vs off (-1.62 at a 14.6 line); other -1.79% on vs off (-0.06 at a 3.3 line) |
| TNF | rush_carries | RB +1.82% on vs off (+0.17 at a 9.1 line); QB +2.75% on vs off (+0.10 at a 3.7 line); other +12.47% on vs off (+0.09 at a 0.7 line) |
| TNF | pass_yards | all +1.83% on vs off (+4.19 at a 228.9 line) |
| thursday | rec_yards | WR +7.47% on vs off (+2.51 at a 33.6 line); TE +0.00% on vs off (+0.00 at a 20.9 line); RB -6.95% on vs off (-0.99 at a 14.3 line); other +103.71% on vs off (+9.90 at a 9.5 line) |
| thursday | rec_targets | WR +3.67% on vs off (+0.18 at a 5.0 line); TE -0.90% on vs off (-0.03 at a 3.4 line); RB +2.74% on vs off (+0.08 at a 2.7 line); other +194.69% on vs off (+3.47 at a 1.8 line) |
| thursday | rush_yards | RB -0.90% on vs off (-0.31 at a 34.8 line); QB -11.09% on vs off (-1.62 at a 14.6 line); other -1.79% on vs off (-0.06 at a 3.3 line) |
| thursday | rush_carries | RB +1.82% on vs off (+0.17 at a 9.1 line); QB +2.75% on vs off (+0.10 at a 3.7 line); other +12.47% on vs off (+0.09 at a 0.7 line) |
| thursday | pass_yards | all +1.83% on vs off (+4.19 at a 228.9 line) |
| saturday | rec_yards | WR +4.98% on vs off (+1.67 at a 33.6 line); TE +3.71% on vs off (+0.78 at a 20.9 line); RB -12.50% on vs off (-1.78 at a 14.3 line); other -49.94% on vs off (-4.77 at a 9.5 line) |
| saturday | rec_targets | WR -1.21% on vs off (-0.06 at a 5.0 line); TE -7.02% on vs off (-0.24 at a 3.4 line); RB -9.26% on vs off (-0.25 at a 2.7 line); other -50.54% on vs off (-0.90 at a 1.8 line) |
| saturday | rush_yards | RB +12.13% on vs off (+4.22 at a 34.8 line); QB +9.31% on vs off (+1.36 at a 14.6 line); other -32.58% on vs off (-1.08 at a 3.3 line) |
| saturday | rush_carries | RB +6.56% on vs off (+0.60 at a 9.1 line); QB +1.28% on vs off (+0.05 at a 3.7 line); other +30.61% on vs off (+0.22 at a 0.7 line) |
| saturday | pass_yards | all +0.00% on vs off (+0.00 at a 228.9 line) |
| sunday | rec_yards | WR -1.79% on vs off (-0.60 at a 33.6 line); TE -2.96% on vs off (-0.62 at a 20.9 line); RB +3.05% on vs off (+0.44 at a 14.3 line); other +63.73% on vs off (+6.08 at a 9.5 line) |
| sunday | rec_targets | WR -1.20% on vs off (-0.06 at a 5.0 line); TE +0.00% on vs off (+0.00 at a 3.4 line); RB -1.79% on vs off (-0.05 at a 2.7 line); other -31.53% on vs off (-0.56 at a 1.8 line) |
| sunday | rush_yards | RB +1.84% on vs off (+0.64 at a 34.8 line); QB -1.21% on vs off (-0.18 at a 14.6 line); other +3.08% on vs off (+0.10 at a 3.3 line) |
| sunday | rush_carries | RB -0.60% on vs off (-0.06 at a 9.1 line); QB -2.99% on vs off (-0.11 at a 3.7 line); other -7.58% on vs off (-0.05 at a 0.7 line) |
| sunday | pass_yards | all +0.62% on vs off (+1.41 at a 228.9 line) |
| monday | rec_yards | WR -3.59% on vs off (-1.21 at a 33.6 line); TE +0.92% on vs off (+0.19 at a 20.9 line); RB +7.59% on vs off (+1.08 at a 14.3 line); other -66.64% on vs off (-6.36 at a 9.5 line) |
| monday | rec_targets | WR -1.81% on vs off (-0.09 at a 5.0 line); TE +2.78% on vs off (+0.10 at a 3.4 line); RB +8.58% on vs off (+0.24 at a 2.7 line); other +49.57% on vs off (+0.88 at a 1.8 line) |
| monday | rush_yards | RB -6.16% on vs off (-2.15 at a 34.8 line); QB +12.53% on vs off (+1.83 at a 14.6 line); other +19.92% on vs off (+0.66 at a 3.3 line) |
| monday | rush_carries | RB -0.90% on vs off (-0.08 at a 9.1 line); QB +3.70% on vs off (+0.14 at a 3.7 line); other -13.52% on vs off (-0.10 at a 0.7 line) |
| monday | pass_yards | all -1.88% on vs off (-4.31 at a 228.9 line) |
| west_team_1pm | rec_yards | WR +2.28% on vs off (+0.76 at a 33.6 line); TE -12.64% on vs off (-2.64 at a 20.9 line); RB -2.23% on vs off (-0.32 at a 14.3 line); other -10.65% on vs off (-1.02 at a 9.5 line) |
| west_team_1pm | rec_targets | WR +2.28% on vs off (+0.11 at a 5.0 line); TE -6.53% on vs off (-0.22 at a 3.4 line); RB -2.23% on vs off (-0.06 at a 2.7 line); other +46.64% on vs off (+0.83 at a 1.8 line) |
| west_team_1pm | rush_yards | RB -1.15% on vs off (-0.40 at a 34.8 line); QB -15.96% on vs off (-2.33 at a 14.6 line); other -5.63% on vs off (-0.19 at a 3.3 line) |
| west_team_1pm | rush_carries | RB -3.42% on vs off (-0.31 at a 9.1 line); QB -5.63% on vs off (-0.21 at a 3.7 line); other +14.92% on vs off (+0.11 at a 0.7 line) |
| west_team_1pm | pass_yards | all +3.50% on vs off (+8.02 at a 228.9 line) |
| east_team_late_west | rec_yards | WR +0.00% on vs off (+0.00 at a 33.6 line); TE -42.92% on vs off (-8.98 at a 20.9 line); RB -13.72% on vs off (-1.96 at a 14.3 line); other +3350.93% on vs off (+319.78 at a 9.5 line) |
| east_team_late_west | rec_targets | WR +2.99% on vs off (+0.15 at a 5.0 line); TE -18.66% on vs off (-0.64 at a 3.4 line); RB -11.13% on vs off (-0.31 at a 2.7 line); other -97.10% on vs off (-1.73 at a 1.8 line) |
| east_team_late_west | rush_yards | RB -7.70% on vs off (-2.68 at a 34.8 line); QB +8.34% on vs off (+1.22 at a 14.6 line); other -50.07% on vs off (-1.66 at a 3.3 line) |
| east_team_late_west | rush_carries | RB +8.34% on vs off (+0.76 at a 9.1 line); QB +14.29% on vs off (+0.52 at a 3.7 line); other -88.20% on vs off (-0.64 at a 0.7 line) |
| east_team_late_west | pass_yards | all -8.27% on vs off (-18.92 at a 228.9 line) |
| body_clock_hour | rec_yards | WR -0.46% per sd (2.9) (-0.16 at a 33.6 line); TE +0.93% per sd (2.9) (+0.19 at a 20.9 line); RB -1.15% per sd (2.9) (-0.16 at a 14.3 line); other -7.15% per sd (2.9) (-0.68 at a 9.5 line) |
| body_clock_hour | rec_targets | WR +0.00% per sd (2.9) (+0.00 at a 5.0 line); TE +0.23% per sd (2.9) (+0.01 at a 3.4 line); RB +0.23% per sd (2.9) (+0.01 at a 2.7 line); other +21.22% per sd (2.9) (+0.38 at a 1.8 line) |
| body_clock_hour | rush_yards | RB -0.69% per sd (2.9) (-0.24 at a 34.8 line); QB +0.69% per sd (2.9) (+0.10 at a 14.6 line); other +5.44% per sd (2.9) (+0.18 at a 3.3 line) |
| body_clock_hour | rush_carries | RB -0.46% per sd (2.9) (-0.04 at a 9.1 line); QB +2.57% per sd (2.9) (+0.09 at a 3.7 line); other +2.33% per sd (2.9) (+0.02 at a 0.7 line) |
| body_clock_hour | pass_yards | all -0.47% per sd (2.91) (-1.07 at a 228.9 line) |
| holiday | rec_yards | WR +13.29% on vs off (+4.46 at a 33.6 line); TE +6.44% on vs off (+1.35 at a 20.9 line); RB -14.44% on vs off (-2.06 at a 14.3 line); other +80.88% on vs off (+7.72 at a 9.5 line) |
| holiday | rec_targets | WR +3.17% on vs off (+0.16 at a 5.0 line); TE +11.54% on vs off (+0.39 at a 3.4 line); RB +6.44% on vs off (+0.18 at a 2.7 line); other +32.41% on vs off (+0.58 at a 1.8 line) |
| holiday | rush_yards | RB -3.28% on vs off (-1.14 at a 34.8 line); QB -1.66% on vs off (-0.24 at a 14.6 line); other +64.99% on vs off (+2.15 at a 3.3 line) |
| holiday | rush_carries | RB -1.66% on vs off (-0.15 at a 9.1 line); QB -9.53% on vs off (-0.35 at a 3.7 line); other +54.33% on vs off (+0.39 at a 0.7 line) |
| holiday | pass_yards | all +1.75% on vs off (+4.00 at a 228.9 line) |
| international | rec_yards | WR -6.17% on vs off (-2.07 at a 33.6 line); TE -7.65% on vs off (-1.60 at a 20.9 line); RB +19.14% on vs off (+2.73 at a 14.3 line); other +575.77% on vs off (+54.95 at a 9.5 line) |
| international | rec_targets | WR -1.58% on vs off (-0.08 at a 5.0 line); TE +3.24% on vs off (+0.11 at a 3.4 line); RB +15.41% on vs off (+0.42 at a 2.7 line); other -85.20% on vs off (-1.52 at a 1.8 line) |
| international | rush_yards | RB -1.59% on vs off (-0.55 at a 34.8 line); QB +37.70% on vs off (+5.50 at a 14.6 line); other +105.41% on vs off (+3.49 at a 3.3 line) |
| international | rush_carries | RB -4.69% on vs off (-0.43 at a 9.1 line); QB +4.92% on vs off (+0.18 at a 3.7 line); other -85.33% on vs off (-0.62 at a 0.7 line) |
| international | pass_yards | all +3.10% on vs off (+7.09 at a 228.9 line) |

## Weather

Wind above 10 mph (for passing on top of the live WIND_C), rain, snow, cold, any bad weather, a warm or dome team in the cold, bad weather x turf, x grass, x night, wind x turf; his own bad-weather split. Weather x roof is degenerate here (indoor games carry no weather), so it is the turf / grass and indoor rows. Every weather input is 0 indoors.

191 tests; 21 pass rule 1. Every test that passes rule 1 (the rest, with every number, are in reports/situational_props.csv):

| idea | variant | stat | miss 2017-18 | 2019-22 | 2023-25 | chance LL 2018 / 19-22 / 23-25 | lean rule / variant | placebo (beaten of 50, worst window) | verdict |
|---|---|---|---|---|---|---|---|---|---|
| wind_over_10 | pooled | rec_catches | -0.0000 | -0.0000 | -0.0001 | +0.00001 / +0.00003 / -0.00007 | 81-81 / 81-81 |  | fails 2 (chance 2017-18, chance 2019-22) |
| rain | pooled | rec_td | -0.0002 | -0.0002 | -0.0001 |  /  /  | 156-68 / 158-66 | 49 | passes 1-3 |
| rain | by position | rec_td | -0.0000 | -0.0000 | -0.0001 |  /  /  | 156-68 / 159-65 | 44 | fails 3 (placebo, worst window beaten in 44/50) |
| snow | pooled | rec_catches | -0.0007 | -0.0002 | -0.0003 | +0.00016 / -0.00008 / -0.00023 | 81-81 / 81-81 |  | fails 2 (chance 2017-18) |
| snow | by position | rec_catches | -0.0002 | -0.0001 | -0.0001 | +0.00017 / -0.00000 / -0.00008 | 81-81 / 81-81 |  | fails 2 (chance 2017-18) |
| snow | pooled | pass_td | -0.0003 | -0.0001 | -0.0000 |  /  /  | 18-14 / 18-14 | 40 | fails 3 (placebo, worst window beaten in 40/50) |
| cold | pooled | rush_yards | -0.0098 | -0.0093 | -0.0039 | -0.00049 / -0.00004 / -0.00026 | 40-46 / 40-46 | 46 | passes 1-3 |
| bad_weather | pooled | rec_yards | -0.0026 | -0.0119 | -0.0042 | -0.00032 / -0.00052 / -0.00032 | 91-80 / 90-81 |  | fails 2 (lean record) |
| bad_weather | pooled | rush_yards | -0.0023 | -0.0022 | -0.0007 | -0.00035 / -0.00014 / -0.00009 | 40-46 / 40-46 | 36 | fails 3 (placebo, worst window beaten in 36/50) |
| bad_weather | pooled | pass_dropbacks | -0.0000 | -0.0036 | -0.0043 |  /  /  |  | 38 | fails 3 (placebo, worst window beaten in 38/50) |
| warm_team_in_cold | pooled | rec_catches | -0.0001 | -0.0001 | -0.0002 | +0.00030 / -0.00003 / -0.00004 | 81-81 / 81-81 |  | fails 2 (chance 2017-18) |
| bad_x_turf | pooled | rec_yards | -0.0018 | -0.0023 | -0.0035 | -0.00030 / -0.00013 / -0.00014 | 91-80 / 90-81 |  | fails 2 (lean record) |
| bad_x_grass | pooled | rec_td | -0.0001 | -0.0000 | -0.0000 |  /  /  | 156-68 / 154-70 |  | fails 2 (lean record) |
| bad_x_grass | pooled | pass_yards | -0.0250 | -0.1552 | -0.1422 | -0.00094 / -0.00181 / +0.00070 | 15-17 / 15-17 |  | fails 2 (chance 2023-25) |
| bad_x_grass | pooled | pass_dropbacks | -0.0000 | -0.0041 | -0.0032 |  /  /  |  | 39 | fails 3 (placebo, worst window beaten in 39/50) |
| wind_x_turf | pooled | rec_catches | -0.0001 | -0.0001 | -0.0002 | +0.00004 / -0.00008 / -0.00004 | 81-81 / 82-80 |  | fails 2 (chance 2017-18) |
| wind_x_turf | pooled | rush_carries | -0.0002 | -0.0001 | -0.0003 |  /  /  | 44-40 / 44-40 | 44 | fails 3 (placebo, worst window beaten in 44/50) |
| wind_x_turf | pooled | rush_td | -0.0001 | -0.0001 | -0.0002 |  /  /  | 71-30 / 71-30 | 46 | passes 1-3 |
| wind_x_turf | pooled | pass_yards | -0.0268 | -0.0164 | -0.0037 | -0.00037 / -0.00018 / +0.00068 | 15-17 / 15-17 |  | fails 2 (chance 2023-25) |
| own_bad_weather_split | pooled | rush_carries | -0.0001 | -0.0001 | -0.0006 |  /  /  | 44-40 / 44-40 | 41 | fails 3 (placebo, worst window beaten in 41/50) |
| own_bad_weather_split | pooled | pass_yards | -0.0698 | -0.1258 | -0.3003 | -0.00040 / -0.00139 / -0.00177 | 15-17 / 14-18 |  | fails 2 (lean record) |

Every idea x stat, the furthest any variant got (1 = fails the windows, 2 = fails the chance or lean record, 3 = fails its placebo, A = passes 1-3, . = not tested):

| idea | rec_yards | rec_catches | rec_targets | rec_td | rush_yards | rush_carries | rush_td | pass_yards | pass_dropbacks | pass_td | pass_int |
|---|---|---|---|---|---|---|---|---|---|---|---|
| wind_over_10 | 1 | 2 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| rain | 1 | 1 | 1 | A | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| snow | 1 | 2 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 3 | 1 |
| cold | 1 | 1 | 1 | 1 | A | 1 | 1 | 1 | 1 | 1 | 1 |
| bad_weather | 2 | 1 | 1 | 1 | 3 | 1 | 1 | 1 | 3 | 1 | 1 |
| warm_team_in_cold | 1 | 2 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| bad_x_turf | 2 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| bad_x_grass | 1 | 1 | 1 | 2 | 1 | 1 | 1 | 2 | 3 | 1 | 1 |
| bad_x_night | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| wind_x_turf | 1 | 2 | 1 | 1 | 1 | 3 | A | 2 | 1 | 1 | 1 |
| own_bad_weather_split | 1 | 1 | 1 | 1 | 1 | 3 | 1 | 2 | 1 | 1 | 1 |

Readings: the size the last walk-forward refit (on 2016-2025) carries, per unit of the input for an on/off input (per standard deviation otherwise), and in the stat's units at the group's mean line over 2019-25. A size of 0 means the fit found nothing worth moving:

| idea | stat | size |
|---|---|---|
| wind_over_10 | rec_yards | WR -1.35% per sd (2.35) (-0.45 at a 33.6 line); TE -1.54% per sd (2.35) (-0.32 at a 20.9 line); RB +0.78% per sd (2.35) (+0.11 at a 14.3 line); other +17.95% per sd (2.35) (+1.71 at a 9.5 line) |
| wind_over_10 | rec_targets | WR +0.19% per sd (2.35) (+0.01 at a 5.0 line); TE +0.19% per sd (2.35) (+0.01 at a 3.4 line); RB -0.58% per sd (2.35) (-0.02 at a 2.7 line); other -16.85% per sd (2.35) (-0.30 at a 1.8 line) |
| wind_over_10 | rush_yards | RB +1.04% per sd (2.4) (+0.36 at a 34.8 line); QB +1.46% per sd (2.4) (+0.21 at a 14.6 line); other +7.05% per sd (2.4) (+0.23 at a 3.3 line) |
| wind_over_10 | rush_carries | RB +0.21% per sd (2.4) (+0.02 at a 9.1 line); QB +0.21% per sd (2.4) (+0.01 at a 3.7 line); other +0.83% per sd (2.4) (+0.01 at a 0.7 line) |
| wind_over_10 | pass_yards | all -2.28% per sd (2.38) (-5.23 at a 228.9 line) |
| rain | rec_yards | WR -10.21% on vs off (-3.43 at a 33.6 line); TE -11.96% on vs off (-2.50 at a 20.9 line); RB -10.21% on vs off (-1.46 at a 14.3 line); other -35.01% on vs off (-3.34 at a 9.5 line) |
| rain | rec_targets | WR -3.84% on vs off (-0.19 at a 5.0 line); TE +0.00% on vs off (+0.00 at a 3.4 line); RB -3.84% on vs off (-0.11 at a 2.7 line); other -36.27% on vs off (-0.65 at a 1.8 line) |
| rain | rush_yards | RB -1.91% on vs off (-0.67 at a 34.8 line); QB +10.13% on vs off (+1.48 at a 14.6 line); other +9.08% on vs off (+0.30 at a 3.3 line) |
| rain | rush_carries | RB +1.95% on vs off (+0.18 at a 9.1 line); QB +15.58% on vs off (+0.57 at a 3.7 line); other -6.53% on vs off (-0.05 at a 0.7 line) |
| rain | pass_yards | all -7.57% on vs off (-17.34 at a 228.9 line) |
| snow | rec_yards | WR -20.19% on vs off (-6.78 at a 33.6 line); TE -21.97% on vs off (-4.60 at a 20.9 line); RB -18.37% on vs off (-2.62 at a 14.3 line); other +1396.87% on vs off (+133.30 at a 9.5 line) |
| snow | rec_targets | WR -8.63% on vs off (-0.43 at a 5.0 line); TE -6.54% on vs off (-0.22 at a 3.4 line); RB -18.37% on vs off (-0.50 at a 2.7 line); other -93.32% on vs off (-1.66 at a 1.8 line) |
| snow | rush_yards | RB +11.03% on vs off (+3.84 at a 34.8 line); QB +2.11% on vs off (+0.31 at a 14.6 line); other -91.88% on vs off (-3.04 at a 3.3 line) |
| snow | rush_carries | RB +4.27% on vs off (+0.39 at a 9.1 line); QB -6.08% on vs off (-0.22 at a 3.7 line); other -91.88% on vs off (-0.67 at a 0.7 line) |
| snow | pass_yards | all -11.06% on vs off (-25.32 at a 228.9 line) |
| cold | rec_yards | WR -7.18% on vs off (-2.41 at a 33.6 line); TE -9.74% on vs off (-2.04 at a 20.9 line); RB -3.66% on vs off (-0.52 at a 14.3 line); other +205.93% on vs off (+19.65 at a 9.5 line) |
| cold | rec_targets | WR -3.66% on vs off (-0.18 at a 5.0 line); TE -7.18% on vs off (-0.25 at a 3.4 line); RB -5.44% on vs off (-0.15 at a 2.7 line); other -67.31% on vs off (-1.20 at a 1.8 line) |
| cold | rush_yards | RB +10.80% on vs off (+3.76 at a 34.8 line); QB +6.75% on vs off (+0.98 at a 14.6 line); other -2.76% on vs off (-0.09 at a 3.3 line) |
| cold | rush_carries | RB +4.77% on vs off (+0.43 at a 9.1 line); QB -2.76% on vs off (-0.10 at a 3.7 line); other +4.77% on vs off (+0.03 at a 0.7 line) |
| cold | pass_yards | all -7.59% on vs off (-17.37 at a 228.9 line) |
| bad_weather | rec_yards | WR -6.52% on vs off (-2.19 at a 33.6 line); TE -11.54% on vs off (-2.41 at a 20.9 line); RB -5.37% on vs off (-0.77 at a 14.3 line); other -35.30% on vs off (-3.37 at a 9.5 line) |
| bad_weather | rec_targets | WR -1.82% on vs off (-0.09 at a 5.0 line); TE -3.02% on vs off (-0.10 at a 3.4 line); RB -4.20% on vs off (-0.12 at a 2.7 line); other -39.89% on vs off (-0.71 at a 1.8 line) |
| bad_weather | rush_yards | RB +3.75% on vs off (+1.30 at a 34.8 line); QB +5.02% on vs off (+0.73 at a 14.6 line); other +28.56% on vs off (+0.95 at a 3.3 line) |
| bad_weather | rush_carries | RB +1.23% on vs off (+0.11 at a 9.1 line); QB +2.48% on vs off (+0.09 at a 3.7 line); other -2.42% on vs off (-0.02 at a 0.7 line) |
| bad_weather | pass_yards | all -7.24% on vs off (-16.57 at a 228.9 line) |
| warm_team_in_cold | rec_yards | WR -12.26% on vs off (-4.12 at a 33.6 line); TE -21.57% on vs off (-4.51 at a 20.9 line); RB -13.89% on vs off (-1.98 at a 14.3 line); other +841.73% on vs off (+80.33 at a 9.5 line) |
| warm_team_in_cold | rec_targets | WR +0.00% on vs off (+0.00 at a 5.0 line); TE -15.48% on vs off (-0.53 at a 3.4 line); RB -13.89% on vs off (-0.38 at a 2.7 line); other -89.38% on vs off (-1.59 at a 1.8 line) |
| warm_team_in_cold | rush_yards | RB +14.17% on vs off (+4.94 at a 34.8 line); QB -14.06% on vs off (-2.05 at a 14.6 line); other -89.69% on vs off (-2.97 at a 3.3 line) |
| warm_team_in_cold | rush_carries | RB +14.17% on vs off (+1.29 at a 9.1 line); QB +0.00% on vs off (+0.00 at a 3.7 line); other -89.69% on vs off (-0.65 at a 0.7 line) |
| warm_team_in_cold | pass_yards | all -10.56% on vs off (-24.18 at a 228.9 line) |
| bad_x_turf | rec_yards | WR -7.71% on vs off (-2.59 at a 33.6 line); TE -13.96% on vs off (-2.92 at a 20.9 line); RB +2.03% on vs off (+0.29 at a 14.3 line); other -35.02% on vs off (-3.34 at a 9.5 line) |
| bad_x_turf | rec_targets | WR -1.99% on vs off (-0.10 at a 5.0 line); TE +0.00% on vs off (+0.00 at a 3.4 line); RB -3.93% on vs off (-0.11 at a 2.7 line); other -36.31% on vs off (-0.65 at a 1.8 line) |
| bad_x_turf | rush_yards | RB +2.00% on vs off (+0.70 at a 34.8 line); QB +1.00% on vs off (+0.15 at a 14.6 line); other +28.13% on vs off (+0.93 at a 3.3 line) |
| bad_x_turf | rush_carries | RB +2.00% on vs off (+0.18 at a 9.1 line); QB +0.00% on vs off (+0.00 at a 3.7 line); other -69.57% on vs off (-0.50 at a 0.7 line) |
| bad_x_turf | pass_yards | all -4.10% on vs off (-9.39 at a 228.9 line) |
| bad_x_grass | rec_yards | WR -4.96% on vs off (-1.66 at a 33.6 line); TE -9.67% on vs off (-2.02 at a 20.9 line); RB -8.35% on vs off (-1.19 at a 14.3 line); other -50.23% on vs off (-4.79 at a 9.5 line) |
| bad_x_grass | rec_targets | WR -1.44% on vs off (-0.07 at a 5.0 line); TE -3.57% on vs off (-0.12 at a 3.4 line); RB -4.27% on vs off (-0.12 at a 2.7 line); other -39.88% on vs off (-0.71 at a 1.8 line) |
| bad_x_grass | rush_yards | RB +3.71% on vs off (+1.29 at a 34.8 line); QB +6.78% on vs off (+0.99 at a 14.6 line); other +4.47% on vs off (+0.15 at a 3.3 line) |
| bad_x_grass | rush_carries | RB +0.73% on vs off (+0.07 at a 9.1 line); QB +4.47% on vs off (+0.16 at a 3.7 line); other -4.98% on vs off (-0.04 at a 0.7 line) |
| bad_x_grass | pass_yards | all -7.75% on vs off (-17.74 at a 228.9 line) |
| bad_x_night | rec_yards | WR -7.28% on vs off (-2.44 at a 33.6 line); TE +0.00% on vs off (+0.00 at a 20.9 line); RB +0.00% on vs off (+0.00 at a 14.3 line); other +102.41% on vs off (+9.77 at a 9.5 line) |
| bad_x_night | rec_targets | WR -3.71% on vs off (-0.18 at a 5.0 line); TE +3.85% on vs off (+0.13 at a 3.4 line); RB +1.27% on vs off (+0.03 at a 2.7 line); other -34.00% on vs off (-0.61 at a 1.8 line) |
| bad_x_night | rush_yards | RB +1.31% on vs off (+0.46 at a 34.8 line); QB +8.12% on vs off (+1.18 at a 14.6 line); other -15.57% on vs off (-0.52 at a 3.3 line) |
| bad_x_night | rush_carries | RB -1.29% on vs off (-0.12 at a 9.1 line); QB +3.98% on vs off (+0.15 at a 3.7 line); other -8.71% on vs off (-0.06 at a 0.7 line) |
| bad_x_night | pass_yards | all -5.18% on vs off (-11.86 at a 228.9 line) |
| wind_x_turf | rec_yards | WR -0.83% per sd (1.2) (-0.28 at a 33.6 line); TE -0.67% per sd (1.2) (-0.14 at a 20.9 line); RB +0.50% per sd (1.2) (+0.07 at a 14.3 line); other +22.19% per sd (1.2) (+2.12 at a 9.5 line) |
| wind_x_turf | rec_targets | WR -0.17% per sd (1.2) (-0.01 at a 5.0 line); TE +1.01% per sd (1.2) (+0.03 at a 3.4 line); RB -0.17% per sd (1.2) (-0.00 at a 2.7 line); other -18.16% per sd (1.2) (-0.32 at a 1.8 line) |
| wind_x_turf | rush_yards | RB +0.52% per sd (1.27) (+0.18 at a 34.8 line); QB +2.11% per sd (1.27) (+0.31 at a 14.6 line); other +4.82% per sd (1.27) (+0.16 at a 3.3 line) |
| wind_x_turf | rush_carries | RB +0.35% per sd (1.27) (+0.03 at a 9.1 line); QB +0.35% per sd (1.27) (+0.01 at a 3.7 line); other -18.86% per sd (1.27) (-0.14 at a 0.7 line) |
| wind_x_turf | pass_yards | all -0.85% per sd (1.22) (-1.95 at a 228.9 line) |

## Injuries

The live injury pieces re-checked alone (readings: the rule without ABSORB, and without the own-report factor; a positive difference means the live piece helps), then: known-out starters at his own group (on top of ABSORB) and at the other groups (WR1 out -> TE / RB targets), RB starters out (RB2 carries and receptions), the backup QB (the usual starter listed out; this week's starter's rating against his history; each receiver's own backup-QB split), OL starters out (pass yards, dropbacks, rushing), offensive starters out, the opponent's expected starters known out by position (CB -> WR, LB -> TE / RB, DL -> rushing), and injuries x bad weather, x short week.

279 tests; 14 pass rule 1. Every test that passes rule 1 (the rest, with every number, are in reports/situational_props.csv):

| idea | variant | stat | miss 2017-18 | 2019-22 | 2023-25 | chance LL 2018 / 19-22 / 23-25 | lean rule / variant | placebo (beaten of 50, worst window) | verdict |
|---|---|---|---|---|---|---|---|---|---|
| teammate_out_same_group | pooled | rec_catches | -0.0031 | -0.0009 | -0.0019 | -0.00182 / -0.00034 / -0.00082 | 81-81 / 81-81 | 50 | passes 1-3 |
| teammate_out_same_group | by position | rec_catches | -0.0027 | -0.0004 | -0.0019 | -0.00121 / -0.00028 / -0.00076 | 81-81 / 81-81 | 50 | passes 1-3 |
| teammate_out_same_group | pooled | rec_targets | -0.0016 | -0.0012 | -0.0024 |  /  /  | 84-63 / 85-62 | 50 | passes 1-3 |
| teammate_out_same_group | pooled | rec_td | -0.0002 | -0.0001 | -0.0001 |  /  /  | 156-68 / 155-69 |  | fails 2 (lean record) |
| teammate_out_same_group | pooled | rush_td | -0.0000 | -0.0002 | -0.0004 |  /  /  | 71-30 / 70-31 |  | fails 2 (lean record) |
| teammate_out_same_group | by position | rush_td | -0.0002 | -0.0002 | -0.0004 |  /  /  | 71-30 / 70-31 |  | fails 2 (lean record) |
| te_out | pooled | rec_targets | -0.0002 | -0.0004 | -0.0000 |  /  /  | 84-63 / 84-63 | 38 | fails 3 (placebo, worst window beaten in 38/50) |
| te_out | by position | rec_targets | -0.0002 | -0.0004 | -0.0005 |  /  /  | 84-63 / 84-63 | 44 | fails 3 (placebo, worst window beaten in 44/50) |
| te_out | pooled | rec_td | -0.0000 | -0.0000 | -0.0000 |  /  /  | 156-68 / 156-68 | 37 | fails 3 (placebo, worst window beaten in 37/50) |
| rb_out | pooled | rec_catches | -0.0008 | -0.0004 | -0.0003 | -0.00122 / -0.00012 / -0.00064 | 81-81 / 82-80 | 49 | passes 1-3 |
| qb_rating | pooled | rec_yards | -0.0110 | -0.0080 | -0.0106 | -0.00192 / -0.00015 / -0.00016 | 91-80 / 87-84 |  | fails 2 (lean record) |
| qb_rating | by position | rec_yards | -0.0035 | -0.0034 | -0.0163 | -0.00151 / -0.00008 / -0.00035 | 91-80 / 89-82 |  | fails 2 (lean record) |
| qb_rating | pooled | rec_catches | -0.0007 | -0.0002 | -0.0001 | -0.00019 / -0.00013 / +0.00005 | 81-81 / 80-82 |  | fails 2 (chance 2023-25, lean record) |
| qb_rating | pooled | rec_td | -0.0007 | -0.0000 | -0.0002 |  /  /  | 156-68 / 156-68 | 47 | passes 1-3 |
| live rule without ABSORB (round 18) | reading | rec_yards | +0.0164 | +0.0255 | +0.0119 |  |  |  | reading |
| live rule without the own injury-report factor (round 13) | reading | rec_yards | +0.0120 | +0.0233 | -0.0032 |  |  |  | reading |
| live rule without ABSORB (round 18) | reading | rush_yards | +0.0302 | +0.0803 | +0.0675 |  |  |  | reading |
| live rule without the own injury-report factor (round 13) | reading | rush_yards | +0.0149 | +0.0050 | +0.0127 |  |  |  | reading |

Every idea x stat, the furthest any variant got (1 = fails the windows, 2 = fails the chance or lean record, 3 = fails its placebo, A = passes 1-3, . = not tested):

| idea | rec_yards | rec_catches | rec_targets | rec_td | rush_yards | rush_carries | rush_td | pass_yards | pass_dropbacks | pass_td | pass_int |
|---|---|---|---|---|---|---|---|---|---|---|---|
| teammate_out_same_group | 1 | A | A | 2 | 1 | 1 | 2 | . | . | . | . |
| teammate_out_cross | 1 | 1 | 1 | 1 | . | . | . | . | . | . | . |
| wr_out | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| te_out | 1 | 1 | 3 | 3 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| rb_out | 1 | A | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| qb_out | 1 | 1 | 1 | 1 | 1 | 1 | 1 | . | . | . | . |
| qb_rating | 2 | 2 | 1 | A | 1 | 1 | 1 | . | . | . | . |
| own_backup_qb_split | 1 | 1 | 1 | 1 | 1 | 1 | 1 | . | . | . | . |
| ol_out | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| off_starters_out | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| opp_cb_out | 1 | 1 | 1 | 1 | . | . | . | 1 | 1 | 1 | 1 |
| opp_s_out | 1 | 1 | 1 | 1 | . | . | . | 1 | 1 | 1 | 1 |
| opp_lb_out | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| opp_dl_out | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| opp_def_starters_out | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| injuries_x_bad_weather | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| qb_out_x_bad_weather | 1 | 1 | 1 | 1 | 1 | 1 | 1 | . | . | . | . |
| injuries_x_short_week | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| live rule without ABSORB (round 18) | r | . | . | . | r | . | . | . | . | . | . |
| live rule without the own injury-report factor (round 13) | r | . | . | . | r | . | . | . | . | . | . |

Readings: the size the last walk-forward refit (on 2016-2025) carries, per unit of the input for an on/off input (per standard deviation otherwise), and in the stat's units at the group's mean line over 2019-25. A size of 0 means the fit found nothing worth moving:

| idea | stat | size |
|---|---|---|
| teammate_out_same_group | rec_yards | WR +0.00% per sd (0.112) (+0.00 at a 33.6 line); TE +7.09% per sd (0.112) (+1.48 at a 20.9 line); RB +3.95% per sd (0.112) (+0.56 at a 14.3 line); other +42.94% per sd (0.112) (+4.10 at a 9.5 line) |
| teammate_out_same_group | rec_targets | WR +3.02% per sd (0.112) (+0.15 at a 5.0 line); TE +12.65% per sd (0.112) (+0.43 at a 3.4 line); RB +3.95% per sd (0.112) (+0.11 at a 2.7 line); other +25.77% per sd (0.112) (+0.46 at a 1.8 line) |
| teammate_out_same_group | rush_yards | RB +2.55% per sd (0.158) (+0.89 at a 34.8 line); QB +32.69% per sd (0.158) (+4.77 at a 14.6 line); other -28.54% per sd (0.158) (-0.94 at a 3.3 line) |
| teammate_out_same_group | rush_carries | RB +4.58% per sd (0.158) (+0.42 at a 9.1 line); QB +33.81% per sd (0.158) (+1.23 at a 3.7 line); other -7.28% per sd (0.158) (-0.05 at a 0.7 line) |
| teammate_out_cross | rec_yards | WR +2.32% per sd (0.0603) (+0.78 at a 33.6 line); TE +1.15% per sd (0.0603) (+0.24 at a 20.9 line); RB +0.00% per sd (0.0603) (+0.00 at a 14.3 line); other +41.09% per sd (0.0603) (+3.92 at a 9.5 line) |
| teammate_out_cross | rec_targets | WR +3.80% per sd (0.0603) (+0.19 at a 5.0 line); TE +2.32% per sd (0.0603) (+0.08 at a 3.4 line); RB +1.15% per sd (0.0603) (+0.03 at a 2.7 line); other +1.44% per sd (0.0603) (+0.03 at a 1.8 line) |
| wr_out | rec_yards | WR +0.00% per sd (0.0721) (+0.00 at a 33.6 line); TE +1.41% per sd (0.0721) (+0.29 at a 20.9 line); RB +1.41% per sd (0.0721) (+0.20 at a 14.3 line); other +39.85% per sd (0.0721) (+3.80 at a 9.5 line) |
| wr_out | rec_targets | WR +1.98% per sd (0.0721) (+0.10 at a 5.0 line); TE +2.55% per sd (0.0721) (+0.09 at a 3.4 line); RB +1.98% per sd (0.0721) (+0.05 at a 2.7 line); other +1.41% per sd (0.0721) (+0.03 at a 1.8 line) |
| wr_out | rush_yards | RB +0.85% per sd (0.0725) (+0.30 at a 34.8 line); QB -2.78% per sd (0.0725) (-0.41 at a 14.6 line); other -20.18% per sd (0.0725) (-0.67 at a 3.3 line) |
| wr_out | rush_carries | RB +1.13% per sd (0.0725) (+0.10 at a 9.1 line); QB -0.84% per sd (0.0725) (-0.03 at a 3.7 line); other -3.32% per sd (0.0725) (-0.02 at a 0.7 line) |
| wr_out | pass_yards | all -1.14% per sd (0.073) (-2.61 at a 228.9 line) |
| te_out | rec_yards | WR +1.15% per sd (0.0297) (+0.39 at a 33.6 line); TE +2.91% per sd (0.0297) (+0.61 at a 20.9 line); RB -2.55% per sd (0.0297) (-0.36 at a 14.3 line); other +41.04% per sd (0.0297) (+3.92 at a 9.5 line) |
| te_out | rec_targets | WR +1.73% per sd (0.0297) (+0.09 at a 5.0 line); TE +3.20% per sd (0.0297) (+0.11 at a 3.4 line); RB -0.86% per sd (0.0297) (-0.02 at a 2.7 line); other +41.04% per sd (0.0297) (+0.73 at a 1.8 line) |
| te_out | rush_yards | RB +1.12% per sd (0.0304) (+0.39 at a 34.8 line); QB -0.83% per sd (0.0304) (-0.12 at a 14.6 line); other +9.92% per sd (0.0304) (+0.33 at a 3.3 line) |
| te_out | rush_carries | RB +0.00% per sd (0.0304) (+0.00 at a 9.1 line); QB +1.68% per sd (0.0304) (+0.06 at a 3.7 line); other -23.65% per sd (0.0304) (-0.17 at a 0.7 line) |
| te_out | pass_yards | all -0.82% per sd (0.0301) (-1.88 at a 228.9 line) |
| rb_out | rec_yards | WR +0.56% per sd (0.197) (+0.19 at a 33.6 line); TE -0.28% per sd (0.197) (-0.06 at a 20.9 line); RB +7.21% per sd (0.197) (+1.03 at a 14.3 line); other -27.20% per sd (0.197) (-2.60 at a 9.5 line) |
| rb_out | rec_targets | WR +1.12% per sd (0.197) (+0.06 at a 5.0 line); TE +0.84% per sd (0.197) (+0.03 at a 3.4 line); RB +6.91% per sd (0.197) (+0.19 at a 2.7 line); other -4.62% per sd (0.197) (-0.08 at a 1.8 line) |
| rb_out | rush_yards | RB +3.19% per sd (0.194) (+1.11 at a 34.8 line); QB -3.09% per sd (0.194) (-0.45 at a 14.6 line); other -17.39% per sd (0.194) (-0.58 at a 3.3 line) |
| rb_out | rush_carries | RB +5.57% per sd (0.194) (+0.51 at a 9.1 line); QB +0.00% per sd (0.194) (+0.00 at a 3.7 line); other +2.31% per sd (0.194) (+0.02 at a 0.7 line) |
| rb_out | pass_yards | all +0.55% per sd (0.203) (+1.26 at a 228.9 line) |
| qb_out | rec_yards | WR -7.62% on vs off (-2.56 at a 33.6 line); TE +1.60% on vs off (+0.33 at a 20.9 line); RB +1.60% on vs off (+0.23 at a 14.3 line); other +570.68% on vs off (+54.46 at a 9.5 line) |
| qb_out | rec_targets | WR -3.12% on vs off (-0.15 at a 5.0 line); TE +3.22% on vs off (+0.11 at a 3.4 line); RB +1.60% on vs off (+0.04 at a 2.7 line); other -85.09% on vs off (-1.52 at a 1.8 line) |
| qb_out | rush_yards | RB -6.88% on vs off (-2.40 at a 34.8 line); QB +26.07% on vs off (+3.80 at a 14.6 line); other -19.25% on vs off (-0.64 at a 3.3 line) |
| qb_out | rush_carries | RB -6.88% on vs off (-0.63 at a 9.1 line); QB +15.32% on vs off (+0.56 at a 3.7 line); other +48.00% on vs off (+0.35 at a 0.7 line) |
| qb_rating | rec_yards | WR +4.94% per sd (0.0976) (+1.66 at a 33.6 line); TE +5.40% per sd (0.0976) (+1.13 at a 20.9 line); RB +0.44% per sd (0.0976) (+0.06 at a 14.3 line); other +69.17% per sd (0.0976) (+6.60 at a 9.5 line) |
| qb_rating | rec_targets | WR +0.88% per sd (0.0976) (+0.04 at a 5.0 line); TE +0.00% per sd (0.0976) (+0.00 at a 3.4 line); RB -0.44% per sd (0.0976) (-0.01 at a 2.7 line); other +62.63% per sd (0.0976) (+1.12 at a 1.8 line) |
| qb_rating | rush_yards | RB +2.81% per sd (0.0973) (+0.98 at a 34.8 line); QB -9.25% per sd (0.0973) (-1.35 at a 14.6 line); other -6.70% per sd (0.0973) (-0.22 at a 3.3 line) |
| qb_rating | rush_carries | RB -0.46% per sd (0.0973) (-0.04 at a 9.1 line); QB -4.96% per sd (0.0973) (-0.18 at a 3.7 line); other +6.19% per sd (0.0973) (+0.04 at a 0.7 line) |
| ol_out | rec_yards | WR +0.49% per sd (0.392) (+0.16 at a 33.6 line); TE -0.24% per sd (0.392) (-0.05 at a 20.9 line); RB -0.24% per sd (0.392) (-0.03 at a 14.3 line); other +12.69% per sd (0.392) (+1.21 at a 9.5 line) |
| ol_out | rec_targets | WR +0.98% per sd (0.392) (+0.05 at a 5.0 line); TE +0.49% per sd (0.392) (+0.02 at a 3.4 line); RB -0.24% per sd (0.392) (-0.01 at a 2.7 line); other -2.88% per sd (0.392) (-0.05 at a 1.8 line) |
| ol_out | rush_yards | RB -1.21% per sd (0.39) (-0.42 at a 34.8 line); QB -1.93% per sd (0.39) (-0.28 at a 14.6 line); other -4.05% per sd (0.39) (-0.13 at a 3.3 line) |
| ol_out | rush_carries | RB -1.21% per sd (0.39) (-0.11 at a 9.1 line); QB -1.45% per sd (0.39) (-0.05 at a 3.7 line); other +2.46% per sd (0.39) (+0.02 at a 0.7 line) |
| ol_out | pass_yards | all +0.25% per sd (0.391) (+0.57 at a 228.9 line) |
| off_starters_out | rec_yards | WR +0.00% per sd (0.589) (+0.00 at a 33.6 line); TE -0.80% per sd (0.589) (-0.17 at a 20.9 line); RB +0.27% per sd (0.589) (+0.04 at a 14.3 line); other -27.50% per sd (0.589) (-2.62 at a 9.5 line) |
| off_starters_out | rec_targets | WR +1.62% per sd (0.589) (+0.08 at a 5.0 line); TE +0.54% per sd (0.589) (+0.02 at a 3.4 line); RB +1.08% per sd (0.589) (+0.03 at a 2.7 line); other +5.22% per sd (0.589) (+0.09 at a 1.8 line) |
| off_starters_out | rush_yards | RB -1.07% per sd (0.586) (-0.37 at a 34.8 line); QB -2.65% per sd (0.586) (-0.39 at a 14.6 line); other -14.87% per sd (0.586) (-0.49 at a 3.3 line) |
| off_starters_out | rush_carries | RB -0.54% per sd (0.586) (-0.05 at a 9.1 line); QB -0.54% per sd (0.586) (-0.02 at a 3.7 line); other +3.55% per sd (0.586) (+0.03 at a 0.7 line) |
| off_starters_out | pass_yards | all +0.00% per sd (0.584) (+0.00 at a 228.9 line) |
| opp_cb_out | rec_yards | WR +2.02% per sd (0.353) (+0.68 at a 33.6 line); TE +0.86% per sd (0.353) (+0.18 at a 20.9 line); RB -0.28% per sd (0.353) (-0.04 at a 14.3 line); other -25.67% per sd (0.353) (-2.45 at a 9.5 line) |
| opp_cb_out | rec_targets | WR +0.86% per sd (0.353) (+0.04 at a 5.0 line); TE -1.13% per sd (0.353) (-0.04 at a 3.4 line); RB -0.28% per sd (0.353) (-0.01 at a 2.7 line); other -18.10% per sd (0.353) (-0.32 at a 1.8 line) |
| opp_cb_out | pass_yards | all +1.13% per sd (0.353) (+2.58 at a 228.9 line) |
| opp_s_out | rec_yards | WR -0.29% per sd (0.291) (-0.10 at a 33.6 line); TE -0.29% per sd (0.291) (-0.06 at a 20.9 line); RB -1.73% per sd (0.291) (-0.25 at a 14.3 line); other +25.86% per sd (0.291) (+2.47 at a 9.5 line) |
| opp_s_out | rec_targets | WR -0.29% per sd (0.291) (-0.01 at a 5.0 line); TE +0.00% per sd (0.291) (+0.00 at a 3.4 line); RB -0.87% per sd (0.291) (-0.02 at a 2.7 line); other +41.82% per sd (0.291) (+0.75 at a 1.8 line) |
| opp_s_out | pass_yards | all -0.57% per sd (0.288) (-1.32 at a 228.9 line) |
| opp_lb_out | rec_yards | WR +0.52% per sd (0.256) (+0.17 at a 33.6 line); TE -1.53% per sd (0.256) (-0.32 at a 20.9 line); RB +0.52% per sd (0.256) (+0.07 at a 14.3 line); other +3.67% per sd (0.256) (+0.35 at a 9.5 line) |
| opp_lb_out | rec_targets | WR +0.00% per sd (0.256) (+0.00 at a 5.0 line); TE +0.52% per sd (0.256) (+0.02 at a 3.4 line); RB +1.03% per sd (0.256) (+0.03 at a 2.7 line); other -2.54% per sd (0.256) (-0.05 at a 1.8 line) |
| opp_lb_out | rush_yards | RB +1.29% per sd (0.263) (+0.45 at a 34.8 line); QB -0.51% per sd (0.263) (-0.07 at a 14.6 line); other -2.53% per sd (0.263) (-0.08 at a 3.3 line) |
| opp_lb_out | rush_carries | RB +0.51% per sd (0.263) (+0.05 at a 9.1 line); QB +0.00% per sd (0.263) (+0.00 at a 3.7 line); other -0.26% per sd (0.263) (-0.00 at a 0.7 line) |
| opp_lb_out | pass_yards | all +0.54% per sd (0.26) (+1.23 at a 228.9 line) |
| opp_dl_out | rec_yards | WR +0.61% per sd (0.271) (+0.21 at a 33.6 line); TE +0.00% per sd (0.271) (+0.00 at a 20.9 line); RB +1.85% per sd (0.271) (+0.26 at a 14.3 line); other -18.05% per sd (0.271) (-1.72 at a 9.5 line) |
| opp_dl_out | rec_targets | WR +0.00% per sd (0.271) (+0.00 at a 5.0 line); TE -0.91% per sd (0.271) (-0.03 at a 3.4 line); RB -0.31% per sd (0.271) (-0.01 at a 2.7 line); other -14.46% per sd (0.271) (-0.26 at a 1.8 line) |
| opp_dl_out | rush_yards | RB +0.31% per sd (0.272) (+0.11 at a 34.8 line); QB +0.00% per sd (0.272) (+0.00 at a 14.6 line); other +5.15% per sd (0.272) (+0.17 at a 3.3 line) |
| opp_dl_out | rush_carries | RB -0.31% per sd (0.272) (-0.03 at a 9.1 line); QB +0.63% per sd (0.272) (+0.02 at a 3.7 line); other +3.52% per sd (0.272) (+0.03 at a 0.7 line) |
| opp_dl_out | pass_yards | all +0.64% per sd (0.269) (+1.46 at a 228.9 line) |
| opp_def_starters_out | rec_yards | WR +2.19% per sd (0.594) (+0.73 at a 33.6 line); TE +0.54% per sd (0.594) (+0.11 at a 20.9 line); RB -0.27% per sd (0.594) (-0.04 at a 14.3 line); other +3.30% per sd (0.594) (+0.31 at a 9.5 line) |
| opp_def_starters_out | rec_targets | WR +0.54% per sd (0.594) (+0.03 at a 5.0 line); TE -0.54% per sd (0.594) (-0.02 at a 3.4 line); RB -0.54% per sd (0.594) (-0.01 at a 2.7 line); other -16.12% per sd (0.594) (-0.29 at a 1.8 line) |
| opp_def_starters_out | rush_yards | RB -0.80% per sd (0.6) (-0.28 at a 34.8 line); QB -1.07% per sd (0.6) (-0.16 at a 14.6 line); other +1.90% per sd (0.6) (+0.06 at a 3.3 line) |
| opp_def_starters_out | rush_carries | RB -0.27% per sd (0.6) (-0.02 at a 9.1 line); QB +0.00% per sd (0.6) (+0.00 at a 3.7 line); other +4.68% per sd (0.6) (+0.03 at a 0.7 line) |
| opp_def_starters_out | pass_yards | all -0.27% per sd (0.593) (-0.62 at a 228.9 line) |
| injuries_x_bad_weather | rec_yards | WR -1.34% per sd (0.26) (-0.45 at a 33.6 line); TE -3.18% per sd (0.26) (-0.67 at a 20.9 line); RB -1.34% per sd (0.26) (-0.19 at a 14.3 line); other -16.51% per sd (0.26) (-1.58 at a 9.5 line) |
| injuries_x_bad_weather | rec_targets | WR -0.54% per sd (0.26) (-0.03 at a 5.0 line); TE -0.27% per sd (0.26) (-0.01 at a 3.4 line); RB +0.27% per sd (0.26) (+0.01 at a 2.7 line); other -11.17% per sd (0.26) (-0.20 at a 1.8 line) |
| injuries_x_bad_weather | rush_yards | RB +0.28% per sd (0.258) (+0.10 at a 34.8 line); QB +0.28% per sd (0.258) (+0.04 at a 14.6 line); other +23.28% per sd (0.258) (+0.77 at a 3.3 line) |
| injuries_x_bad_weather | rush_carries | RB +0.57% per sd (0.258) (+0.05 at a 9.1 line); QB +0.85% per sd (0.258) (+0.03 at a 3.7 line); other +1.71% per sd (0.258) (+0.01 at a 0.7 line) |
| injuries_x_bad_weather | pass_yards | all -1.23% per sd (0.255) (-2.82 at a 228.9 line) |
| qb_out_x_bad_weather | rec_yards | WR -14.76% on vs off (-4.96 at a 33.6 line); TE +12.73% on vs off (+2.66 at a 20.9 line); RB -11.29% on vs off (-1.61 at a 14.3 line); other +11961.49% on vs off (+1141.48 at a 9.5 line) |
| qb_out_x_bad_weather | rec_targets | WR -7.68% on vs off (-0.38 at a 5.0 line); TE +8.32% on vs off (+0.28 at a 3.4 line); RB +0.00% on vs off (+0.00 at a 2.7 line); other -99.17% on vs off (-1.77 at a 1.8 line) |
| qb_out_x_bad_weather | rush_yards | RB -8.69% on vs off (-3.03 at a 34.8 line); QB +915.46% on vs off (+133.51 at a 14.6 line); other -99.57% on vs off (-3.29 at a 3.3 line) |
| qb_out_x_bad_weather | rush_carries | RB +0.00% on vs off (+0.00 at a 9.1 line); QB +50.54% on vs off (+1.85 at a 3.7 line); other -99.57% on vs off (-0.72 at a 0.7 line) |
| injuries_x_short_week | rec_yards | WR +0.89% per sd (0.185) (+0.30 at a 33.6 line); TE -0.44% per sd (0.185) (-0.09 at a 20.9 line); RB -0.22% per sd (0.185) (-0.03 at a 14.3 line); other -23.34% per sd (0.185) (-2.23 at a 9.5 line) |
| injuries_x_short_week | rec_targets | WR +0.89% per sd (0.185) (+0.04 at a 5.0 line); TE +1.79% per sd (0.185) (+0.06 at a 3.4 line); RB +0.89% per sd (0.185) (+0.02 at a 2.7 line); other +30.44% per sd (0.185) (+0.54 at a 1.8 line) |
| injuries_x_short_week | rush_yards | RB -0.26% per sd (0.182) (-0.09 at a 34.8 line); QB -3.54% per sd (0.182) (-0.52 at a 14.6 line); other -6.00% per sd (0.182) (-0.20 at a 3.3 line) |
| injuries_x_short_week | rush_carries | RB +0.78% per sd (0.182) (+0.07 at a 9.1 line); QB -1.28% per sd (0.182) (-0.05 at a 3.7 line); other -1.53% per sd (0.182) (-0.01 at a 0.7 line) |
| injuries_x_short_week | pass_yards | all +0.82% per sd (0.181) (+1.89 at a 228.9 line) |

## Player vs player

**What the free data can say about who covers whom.** Nothing assigns a defender to a receiver: nflverse's play-by-play has no coverage assignment; the participation file lists the 11 defenders on the field, the man / zone call (defense_man_zone_type, 2018 on) and the coverage shell (defense_coverage_type), with the route only for the targeted receiver and no alignment for anyone (no wide / slot for corners or receivers), and it is published after a season, so it can enter only later seasons; FTN charting (2022 on, weekly) has box counts, blitzers and catchable / contested flags but no coverage or alignment; the play-by-play credits a pass defensed, an interception or a tackle, which is the defender near the ball at the end, not the one in coverage. The depth charts name starting corners (LCB / RCB / NB in the 2025-26 format) without saying who they follow. So every proxy here is indirect: this week's expected corners (the top three by snap share over the team's last three games, less the known-out) rated by the positions.py corner recipe (PFR coverage, 2018 on); a receiver's history against a specific corner counting only his targets with that corner on the field (earlier seasons; 618664.0 receiver x defender x game rows); a shadow index from the credits (a corner's credits on the offense's WR1 targets above the WR1's share of WR targets, shrunk: it flags only 1.3% of expected-corner rows, 45.0 WR1 rows in all, and its season-to-season correlation is 0.13, so a credits-based shadow reading is mostly noise); the receiver's and the QB's man / zone split from earlier seasons x the opponent's man rate last season; LBs and safeties against TE / RB receiving; the front (IDL, LB, EDGE) and last season's 8+ box rate against rushing; the pass rush (EDGE, IDL) and his line's sacks and hits allowed against passing. The play-caller's coverage mix is the defense's man rate. How thin the corner pair histories are: of 83,665 receiver x expected-corner pairs in 2019-25, 70% have no earlier-season target with that corner on the field; among the rest the median is 5 such targets (about one game's worth), the 90th percentile 17, and 2.3% reach 20. Man / zone is known on about 40% of pass plays from 2018 (none before).

98 tests; 10 pass rule 1. Every test that passes rule 1 (the rest, with every number, are in reports/situational_props.csv):

| idea | variant | stat | miss 2017-18 | 2019-22 | 2023-25 | chance LL 2018 / 19-22 / 23-25 | lean rule / variant | placebo (beaten of 50, worst window) | verdict |
|---|---|---|---|---|---|---|---|---|---|
| opp_cb_unit_rating | pooled | rec_yards | +0.0000 (no data) | -0.0045 | -0.0025 | +0.00000 / -0.00007 / +0.00006 | 91-80 / 91-80 |  | fails 2 (chance 2023-25) |
| opp_cb_unit_rating | pooled | rec_catches | +0.0000 (no data) | -0.0002 | -0.0011 | +0.00000 / -0.00002 / -0.00036 | 81-81 / 81-81 | 49 | passes 1-3 |
| opp_cb_unit_rating | pooled | pass_int | +0.0000 (no data) | -0.0010 | -0.0012 |  /  /  | 18-14 / 15-17 |  | fails 2 (lean record) |
| opp_cb_unit_change | pooled | rec_td | +0.0000 (no data) | -0.0000 | -0.0000 |  /  /  | 156-68 / 158-66 | 43 | fails 3 (placebo, worst window beaten in 43/50) |
| opp_cb_unit_change | pooled | pass_yards | +0.0000 (no data) | -0.0106 | -0.0165 | +0.00000 / -0.00017 / +0.00099 | 15-17 / 15-17 |  | fails 2 (chance 2023-25) |
| opp_cb_unit_change | pooled | pass_td | +0.0000 (no data) | -0.0001 | -0.0003 |  /  /  | 18-14 / 18-14 | 46 | passes 1-3 |
| opp_cb_unit_change | pooled | pass_int | +0.0000 (no data) | -0.0003 | -0.0011 |  /  /  | 18-14 / 16-16 |  | fails 2 (lean record) |
| cb_unit_wr_only | pooled | rec_yards | +0.0000 (no data) | -0.0041 | -0.0002 | +0.00000 / -0.00012 / +0.00003 | 91-80 / 92-79 |  | fails 2 (chance 2023-25) |
| cb_shadow_assigned | pooled | rec_yards | +0.0000 (no data) | -0.0030 | -0.0005 | +0.00000 / -0.00010 / +0.00010 | 91-80 / 92-79 |  | fails 2 (chance 2023-25) |
| opp_lb_s_rating | pooled | rec_yards | +0.0000 (no data) | -0.0004 | -0.0033 | +0.00000 / -0.00002 / -0.00007 | 91-80 / 88-83 |  | fails 2 (lean record) |

Every idea x stat, the furthest any variant got (1 = fails the windows, 2 = fails the chance or lean record, 3 = fails its placebo, A = passes 1-3, . = not tested):

| idea | rec_yards | rec_catches | rec_targets | rec_td | rush_yards | rush_carries | rush_td | pass_yards | pass_dropbacks | pass_td | pass_int |
|---|---|---|---|---|---|---|---|---|---|---|---|
| opp_cb_unit_rating | 2 | A | 1 | 1 | . | . | . | 1 | 1 | 1 | 2 |
| opp_cb_unit_change | 1 | 1 | 1 | 3 | . | . | . | 2 | 1 | A | 2 |
| cb_unit_wr_only | 2 | 1 | 1 | 1 | . | . | . | . | . | . | . |
| cb_shadow_assigned | 2 | 1 | 1 | 1 | . | . | . | . | . | . | . |
| vs_shadow_corner_wr1 | 1 | 1 | 1 | 1 | . | . | . | . | . | . | . |
| man_zone_x_opp_man | 1 | 1 | 1 | 1 | . | . | . | 1 | 1 | 1 | 1 |
| opp_lb_s_rating | 2 | 1 | 1 | 1 | . | . | . | . | . | . | . |
| opp_lb_s_change | 1 | 1 | 1 | 1 | . | . | . | . | . | . | . |
| opp_front_rating | . | . | . | . | 1 | 1 | 1 | . | . | . | . |
| opp_front_change | . | . | . | . | 1 | 1 | 1 | . | . | . | . |
| opp_heavy_box_last_season | . | . | . | . | 1 | 1 | 1 | . | . | . | . |
| opp_pass_rush_rating | . | . | . | . | . | . | . | 1 | 1 | 1 | 1 |
| opp_pass_rush_change | . | . | . | . | . | . | . | 1 | 1 | 1 | 1 |
| pass_rush_vs_protection | . | . | . | . | . | . | . | 1 | 1 | 1 | 1 |
| vs_specific_corners | 1 | 1 | 1 | 1 | . | . | . | . | . | . | . |

Readings: the size the last walk-forward refit (on 2016-2025) carries, per unit of the input for an on/off input (per standard deviation otherwise), and in the stat's units at the group's mean line over 2019-25. A size of 0 means the fit found nothing worth moving:

| idea | stat | size |
|---|---|---|
| opp_cb_unit_rating | rec_yards | WR -1.86% per sd (0.00333) (-0.62 at a 33.6 line); TE -3.16% per sd (0.00333) (-0.66 at a 20.9 line); RB -1.60% per sd (0.00333) (-0.23 at a 14.3 line); other +29.34% per sd (0.00333) (+2.80 at a 9.5 line) |
| opp_cb_unit_rating | rec_targets | WR +0.27% per sd (0.00333) (+0.01 at a 5.0 line); TE -1.86% per sd (0.00333) (-0.06 at a 3.4 line); RB -0.53% per sd (0.00333) (-0.01 at a 2.7 line); other -10.65% per sd (0.00333) (-0.19 at a 1.8 line) |
| opp_cb_unit_rating | pass_yards | all -0.53% per sd (0.00333) (-1.22 at a 228.9 line) |
| opp_cb_unit_change | rec_yards | WR -1.29% per sd (0.00155) (-0.43 at a 33.6 line); TE -2.81% per sd (0.00155) (-0.59 at a 20.9 line); RB +1.04% per sd (0.00155) (+0.15 at a 14.3 line); other +5.04% per sd (0.00155) (+0.48 at a 9.5 line) |
| opp_cb_unit_change | rec_targets | WR +0.00% per sd (0.00155) (+0.00 at a 5.0 line); TE -1.03% per sd (0.00155) (-0.04 at a 3.4 line); RB +0.00% per sd (0.00155) (+0.00 at a 2.7 line); other -15.06% per sd (0.00155) (-0.27 at a 1.8 line) |
| opp_cb_unit_change | pass_yards | all -0.78% per sd (0.00154) (-1.79 at a 228.9 line) |
| cb_unit_wr_only | rec_yards | all -1.89% per sd (0.00334) (-0.48 at a 25.4 line) |
| cb_unit_wr_only | rec_targets | all +0.38% per sd (0.00334) (+0.02 at a 4.0 line) |
| cb_shadow_assigned | rec_yards | all -1.52% per sd (0.00337) (-0.39 at a 25.4 line) |
| cb_shadow_assigned | rec_targets | all +0.38% per sd (0.00337) (+0.02 at a 4.0 line) |
| vs_shadow_corner_wr1 | rec_yards | all +7.36% on vs off (+1.87 at a 25.4 line) |
| vs_shadow_corner_wr1 | rec_targets | all -13.24% on vs off (-0.53 at a 4.0 line) |
| man_zone_x_opp_man | rec_yards | WR +0.00% per sd (0.0129) (+0.00 at a 33.6 line); TE +1.94% per sd (0.0129) (+0.41 at a 20.9 line); RB -1.09% per sd (0.0129) (-0.16 at a 14.3 line); other -2.18% per sd (0.0129) (-0.21 at a 9.5 line) |
| man_zone_x_opp_man | rec_targets | WR -0.55% per sd (0.0129) (-0.03 at a 5.0 line); TE +0.55% per sd (0.0129) (+0.02 at a 3.4 line); RB -1.37% per sd (0.0129) (-0.04 at a 2.7 line); other +7.12% per sd (0.0129) (+0.13 at a 1.8 line) |
| man_zone_x_opp_man | pass_yards | all -0.55% per sd (0.00728) (-1.26 at a 228.9 line) |
| opp_lb_s_rating | rec_yards | WR -1.15% per sd (0.0105) (-0.39 at a 33.6 line); TE -0.87% per sd (0.0105) (-0.18 at a 20.9 line); RB -2.29% per sd (0.0105) (-0.33 at a 14.3 line); other +4.75% per sd (0.0105) (+0.45 at a 9.5 line) |
| opp_lb_s_rating | rec_targets | WR -0.29% per sd (0.0105) (-0.01 at a 5.0 line); TE +0.00% per sd (0.0105) (+0.00 at a 3.4 line); RB -0.29% per sd (0.0105) (-0.01 at a 2.7 line); other -11.47% per sd (0.0105) (-0.20 at a 1.8 line) |
| opp_lb_s_change | rec_yards | WR -0.51% per sd (0.00596) (-0.17 at a 33.6 line); TE -1.28% per sd (0.00596) (-0.27 at a 20.9 line); RB -0.26% per sd (0.00596) (-0.04 at a 14.3 line); other -12.55% per sd (0.00596) (-1.20 at a 9.5 line) |
| opp_lb_s_change | rec_targets | WR +0.00% per sd (0.00596) (+0.00 at a 5.0 line); TE +0.00% per sd (0.00596) (+0.00 at a 3.4 line); RB -0.51% per sd (0.00596) (-0.01 at a 2.7 line); other -6.24% per sd (0.00596) (-0.11 at a 1.8 line) |
| opp_front_rating | rush_yards | RB -1.73% per sd (0.00938) (-0.60 at a 34.8 line); QB -0.29% per sd (0.00938) (-0.04 at a 14.6 line); other -8.62% per sd (0.00938) (-0.29 at a 3.3 line) |
| opp_front_rating | rush_carries | RB +0.00% per sd (0.00938) (+0.00 at a 9.1 line); QB +0.29% per sd (0.00938) (+0.01 at a 3.7 line); other +14.99% per sd (0.00938) (+0.11 at a 0.7 line) |
| opp_front_change | rush_yards | RB -1.51% per sd (0.0047) (-0.53 at a 34.8 line); QB -2.26% per sd (0.0047) (-0.33 at a 14.6 line); other -8.04% per sd (0.0047) (-0.27 at a 3.3 line) |
| opp_front_change | rush_carries | RB +0.25% per sd (0.0047) (+0.02 at a 9.1 line); QB -1.26% per sd (0.0047) (-0.05 at a 3.7 line); other +3.62% per sd (0.0047) (+0.03 at a 0.7 line) |
| opp_heavy_box_last_season | rush_yards | RB -0.36% per sd (0.0866) (-0.13 at a 34.8 line); QB -1.78% per sd (0.0866) (-0.26 at a 14.6 line); other +5.93% per sd (0.0866) (+0.20 at a 3.3 line) |
| opp_heavy_box_last_season | rush_carries | RB +0.36% per sd (0.0866) (+0.03 at a 9.1 line); QB -0.72% per sd (0.0866) (-0.03 at a 3.7 line); other -6.61% per sd (0.0866) (-0.05 at a 0.7 line) |
| opp_pass_rush_rating | pass_yards | all -0.57% per sd (0.00701) (-1.30 at a 228.9 line) |
| opp_pass_rush_change | pass_yards | all -0.78% per sd (0.00365) (-1.79 at a 228.9 line) |
| pass_rush_vs_protection | pass_yards | all -0.94% per sd (1.26) (-2.16 at a 228.9 line) |

## Task B


| idea | variant | stat | miss 2017-18 | 2019-22 | 2023-25 | chance LL 2018 / 19-22 / 23-25 | lean rule / variant | placebo (beaten of 50, worst window) | verdict |
|---|---|---|---|---|---|---|---|---|---|
| rushing median factor: flat refit | pooled | rush_yards | -0.0194 | +0.0043 | +0.0018 |  |  |  | fails 1 (2019-22, 2023-25) |
| rushing median factor: linear | pooled | rush_yards | -0.0164 | +0.0094 | +0.0016 |  |  |  | fails 1 (2019-22, 2023-25) |
| rushing median factor: logistic, scale 5 | pooled | rush_yards | -0.0104 | +0.0098 | -0.0049 |  |  |  | fails 1 (2019-22) |
| rushing median factor: logistic, free scale | pooled | rush_yards | +0.0026 | +0.0040 | -0.0066 |  |  |  | fails 1 (2017-18, 2019-22) |
| receiving shares capped at one: Out/Doubtful removed (as specified) | pooled | rec_yards | +0.0307 | +0.0350 | +0.0007 |  |  |  | fails 1 (2017-18, 2019-22, 2023-25) |
| receiving shares capped at one: Out/Doubtful removed (as specified) | pooled | rec_catches | +0.0057 | +0.0054 | +0.0031 |  |  |  | fails 1 (2017-18, 2019-22, 2023-25) |
| receiving shares capped at one: Out/Doubtful removed (as specified) | pooled | rec_targets | -0.0036 | -0.0005 | -0.0028 |  /  /  | 84-63 / 83-64 |  | fails 2 (lean record) |
| receiving shares capped at one: Out/Doubtful and inactive roster removed | pooled | rec_yards | +0.0239 | +0.0184 | -0.0029 |  |  |  | fails 1 (2017-18, 2019-22) |
| receiving shares capped at one: Out/Doubtful and inactive roster removed | pooled | rec_catches | +0.0021 | +0.0016 | +0.0007 |  |  |  | fails 1 (2017-18, 2019-22, 2023-25) |
| receiving shares capped at one: Out/Doubtful and inactive roster removed | pooled | rec_targets | -0.0056 | -0.0022 | -0.0027 |  /  /  | 84-63 / 85-62 | 49 | passes 1-3 |

## Together


| idea | variant | stat | miss 2017-18 | 2019-22 | 2023-25 | chance LL 2018 / 19-22 / 23-25 | lean rule / variant | placebo (beaten of 50, worst window) | verdict |
|---|---|---|---|---|---|---|---|---|---|
| teammate_out_same_group[pooled] + opp_cb_unit_rating[pooled] + rest_days[pooled] + rb_out[pooled] | together (all) | rec_catches | -0.0038 (no data) | -0.0008 | -0.0034 | -0.00249 / -0.00067 / -0.00125 | 81-81 / 82-80 |  | passes 1-2 together (rule 5 met) |
| receiving shares capped at one: Out/Doubtful and inactive roster removed + teammate_out_same_group[pooled] + rest_days[pooled] | together (all) | rec_targets | -0.0085 | -0.0032 | -0.0054 |  /  /  | 84-63 / 86-61 |  | passes 1-2 together (rule 5 met) |
| qb_rating[pooled] + rain[pooled] | together (all) | rec_td | -0.0009 | -0.0002 | -0.0003 |  /  /  | 156-68 / 158-66 |  | passes 1-2 together (rule 5 met) |
| cold[pooled] | together (all) | rush_yards | -0.0098 | -0.0093 | -0.0039 | -0.00049 / -0.00004 / -0.00026 | 40-46 / 40-46 |  | passes 1-2 together (rule 5 met) |
| wind_x_turf[pooled] | together (all) | rush_td | -0.0001 | -0.0001 | -0.0002 |  /  /  | 71-30 / 71-30 |  | passes 1-2 together (rule 5 met) |
| opp_cb_unit_change[pooled] | together (all) | pass_td | +0.0000 (no data) | -0.0001 | -0.0003 |  /  /  | 18-14 / 18-14 |  | passes 1-2 together (rule 5 met) |

## What passed, and the code change it would need (described, not applied)

Every piece below passes rules 1-3 alone and its stat's pieces pass rules 1-2 refitted together (rule 5). Each is a factor
on the final line of one stat only, after round 13's injury/snap factor, exp(b x (z - q)): z the input for this game, q the
player's own 0.85-decayed mean of z over his earlier player-games (weight 1 on his latest game, 0.85 on the one before, ...,
over the same games the profile counts). b is the last walk-forward refit (on 2016-2025); rerunning the study re-derives it.

| stat | input z (as of before kickoff) | b per unit of z | size | gain per player-game 2017-18 / 2019-22 / 2023-25 |
|---|---|---|---|---|
| receptions | known-out starters' share at his own position group (the share ABSORB already hands on; `absorbed` share of the absent starters, the report's Out/Doubtful or no active listing) | +0.425 | +4.9% per 0.11 of out share | 0.0031 / 0.0009 / 0.0019 catches |
| receptions | this week's expected starting corners' rating (top three by snap share over the last 3 games, less the known-out; positions.py CB recipe) | -5.64 | -1.9% per sd | - / 0.0002 / 0.0011 |
| receptions | days of rest (4 to 14) | -0.0094 | -1.9% per 2 days | 0.0005 / 0.0004 / 0.0007 |
| receptions | known-out RB starters' share (ABSORB's rushing table) | +0.113 | +2.3% per 0.2 | 0.0008 / 0.0004 / 0.0003 |
| targets | the shares capped at one over the roster the card can know, Out / Doubtful AND anyone without an active roster listing removed (props._KNOWN_OUT's definition); the as-specified version (Out / Doubtful only) fails rule 2 by one lean (83-64 against 84-63) | - | shares x min(1, 1/sum) | 0.0056 / 0.0022 / 0.0028 targets |
| targets | known-out starters' share at his group | +0.319 | +3.6% per 0.11 | 0.0016 / 0.0012 / 0.0024 |
| targets | days of rest | -0.0042 | -0.8% per 2 days | 0.0005 / 0.0001 / 0.0004 |
| receiving TDs | this week's starter's QB rating (the game model's qb_rating) | +0.943 | +9.6% per sd | 0.0007 / 0.0000 / 0.0002 log loss |
| receiving TDs | rain at kickoff (the game model's rain call; outdoors) | -0.186 | -17% in rain | 0.0002 / 0.0002 / 0.0001 |
| rushing yards | cold: under 35 F outdoors (the game model's cold call) | +0.1026 | +10.8% (+2.8 yards on a 26-yard line) | 0.0098 / 0.0093 / 0.0039 yards |
| rushing TDs | mph of kickoff wind above 10 on turf | +0.0343 | +4.5% per sd | 0.0001 / 0.0001 / 0.0002 log loss |
| passing TDs | expected starting corners' rating minus the corners who played the defense's last 8 games | -11.9 | -1.8% per sd | - / 0.0001 / 0.0003 |

In nflmodel/props.py this is: (1) a table SIT = {stat: [(input, b)]} of the rows above; (2) in project_game, after the
injury/snap factor, line *= exp(sum b x (z - q)) per stat, with z read from what the weekly run already builds (rest and cold
and rain from the game's features row, qb_rating from the same row, wind from the forecast with the schedule's surface,
the known-out shares from the absorb step, the corner ratings from positions.role_rates and the snap counts) and q from the
player's profile games (a decayed mean kept in receivers()/rushers() beside the share); (3) the targets line
(share_yds x pass plays x TARGETABLE) scaled by min(1, 1 / the team's share_yds sum over the rows not out) for the targets
market only; (4) experiments/props_by_season.py applies the same factors so props_reference.parquet (the chance's table)
carries them. Every gain is under a hundredth of a catch or target, a hundredth of a yard of rushing, a thousandth of log
loss: real by the rule's placebo, too small to see on a card. The cap on targets makes the targets line disagree with the
receptions and yards lines it feeds (both lose with the cap: receptions +0.002 / +0.002 / +0.001, yards +0.024 / +0.018 /
-0.003), so it is the one to weigh before adopting.

