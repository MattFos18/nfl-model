# Props: player tracking and charting measures (29 Sep 2026)

`experiments/props_tracking.py`; rows in `reports/props_tracking.csv` (`table` = window or tier).

**Question.** Can player-level tracking (NGS) and charting measures, as of before each game, make the per-game yards
projection more accurate than the adopted rule (round 18: share x game-script plays, rate shrunk toward the league
with K and moved W toward the defense, MED_TIER, round-6 team reconciliation, round-13 injury and snap factors, PACE
and ABSORB)? No market input anywhere.

**Frame.** `props_by_season.build(kind)` run once per kind (exec of the module header, as `props_backtest17.py` does),
cached: receiving 36,630, rushing 17,788, passing 5,031 player-games 2017-25. The rule is re-run from the frame's
own inputs and reproduces `build`'s `yds_line` to 1e-13 (checks below), so every variant differs from the rule only
by the signal it adds.

**Signals, each as of before the game** (weekly rows of week w enter only games after week w; NGS and PFR rows are
regular season only; a player's rows are decayed DECAY = 0.85 per game with the round-10 season fade, as the live
usage; each shrunk toward the league or his position with its own k chosen on 2017-18):

- receivers: (1) air-yards share (his air yards over the team's, charted plays, every target) as a second volume
  signal: `share + a x (air share - target share)` (literal blend) and `share x (air share / target share over his
  position's)^a`; (2) ADOT x catch rate (each shrunk toward his position's) as the rate prior; (3) NGS YAC over
  expected per catch; (4) NGS separation per target (against his position's); (5) PFR drops per target (2018 on).
  Control: his position's yards per target as the prior (no player information), to separate a position effect from
  the signal.
- rushers: (6) NGS rush yards over expected per carry (2018 on; games with 10+ carries) as the rate prior; (7) his
  share of carries inside the opponent's 10 (for touchdowns, scored on the touchdown line's Poisson log loss).
- passers: (8) NGS CPOE (games with 15+ attempts); (9) ADOT (charted air yards per attempt); (10) NGS time to throw x
  the opponent's pressure rate (sacks plus QB hits per dropback over its last 17; charted pressure exists only in the
  2025 plays).

**Forms.** A rate signal z (the shrunk deviation over its standard deviation on 2017-18) enters two ways: `prior`
(the league rate the player's own rate is shrunk toward becomes league x (1 + c z)) and `direct` (the rate x (1 + c z)).
The literal forms asked for are scored too, with no c: ADOT x catch over the league's as the prior
(`adot_x_catch[prior_lit]`), league + RYOE per carry as the prior (`ryoe[prior_lit]`) and as his rate outright
(`ryoe[rate_lit]`). k and c (or the blend weight a) are chosen on 2017-18 by yards MAE. The combination: forward
selection on 2017-18 among the signals that beat the rule there, weights refitted at each step.

**Scores.** Yards MAE and volume MAE (targets, carries, dropbacks) per player-game, 2019-22 and 2023-25 (2017-18 is
the fit window; 2019-25 pooled is a reading beside the rule), the paired standard error of the difference from the
rule, and the rule's yards-line tiers (0-20 ... 80+; passing 0-150 ... 300+).

## Adoption rule (set before the run)

A variant is adopted only if its yards MAE is lower than the rule's on both 2019-22 and 2023-25, by more than one
paired standard error on at least one of them, and it is not worse than the rule by more than 0.1 yards in any tier
on either window. Where more than one form of the same signal passes, the one with the lower 2017-18 MAE is taken.
The inside-10 touchdown signal cannot move a yards line; it is judged by the same rule on the rushing touchdown
Poisson log loss (no tier test), on this touch frame, as a side reading. A placebo check follows the verdict: each
passing variant is refitted and rescored 40 times with its signal shuffled among the same season's rows (the
player linkage broken), to show how often noise passes the same rule.


## Checks

- `rec_line_repro_maxdiff`: 4.263256414560601e-14
- `rec_share_state_maxdiff`: 0.0
- `rec_coverage`: {'sep_den': {'2017-18': 0.665, '2019-22': 0.675, '2023-25': 0.695, '2019-25': 0.684}, 'yacoe_den': {'2017-18': 0.665, '2019-22': 0.675, '2023-25': 0.694, '2019-25': 0.683}, 'drop_den': {'2017-18': 0.458, '2019-22': 0.999, '2023-25': 1.0, '2019-25': 0.999}, 'raw_n_ay': {'2017-18': 1.0, '2019-22': 1.0, '2023-25': 1.0, '2019-25': 1.0}}
- `rush_line_repro_maxdiff`: 2.842170943040401e-14
- `rush_td_repro_maxdiff`: 3.3306690738754696e-16
- `rush_coverage`: {'ryoe_den': {'2017-18': 0.217, '2019-22': 0.566, '2023-25': 0.555, '2019-25': 0.561}, 'i10_den': {'2017-18': 1.0, '2019-22': 1.0, '2023-25': 1.0, '2019-25': 1.0}}
- `pass_line_repro_maxdiff`: 1.7053025658242404e-13
- `pass_coverage`: {'ngs_den': {'2017-18': 1.0, '2019-22': 0.998, '2023-25': 1.0, '2019-25': 0.999}, 'adot_den': {'2017-18': 1.0, '2019-22': 1.0, '2023-25': 1.0, '2019-25': 1.0}}
- `rec_integration_mae`: {'2017-18': 19.6888, '2019-22': 19.1251, '2023-25': 18.1437, '2019-25': 18.6981}
- `rec_scored_mae`: {'2017-18': 19.6885, '2019-22': 19.125, '2023-25': 18.1437, '2019-25': 18.698}
- `rec_live_vs_frame_maxdiff`: 2.220446049250313e-16
- `rush_integration_mae`: {'2017-18': 18.0247, '2019-22': 17.6711, '2023-25': 16.9584, '2019-25': 17.3551}
- `rush_scored_mae`: {'2017-18': 18.0247, '2019-22': 17.6711, '2023-25': 16.9584, '2019-25': 17.3551}
- `rush_live_vs_frame_maxdiff`: 6.661338147750939e-16
- `pass_integration_mae`: {'2017-18': 60.6706, '2019-22': 56.5638, '2023-25': 56.0377, '2019-25': 56.3321}
- `pass_scored_mae`: {'2017-18': 60.6706, '2019-22': 56.5637, '2023-25': 56.0377, '2019-25': 56.3321}
- `pass_live_vs_frame_maxdiff`: 2.6645352591003757e-15

## Results: yards and volume MAE per player-game, paired standard error against the adopted rule

diff = variant MAE minus the rule's (negative is better); SE = paired standard error of that difference. 2017-18 is the fit window (k and c chosen there for each form).


### rec_yards

| variant | window | yards MAE | diff | SE | volume MAE | diff | SE | params |
|---|---|---|---|---|---|---|---|---|
| rule | 2017-18 | 19.689 | +0.0000 | 0.0000 | 1.875 | +0.0000 | 0.0000 |  |
| rule | 2019-22 | 19.131 | +0.0000 | 0.0000 | 1.826 | +0.0000 | 0.0000 |  |
| rule | 2023-25 | 18.145 | +0.0000 | 0.0000 | 1.713 | +0.0000 | 0.0000 |  |
| rule | 2019-25 | 18.702 | +0.0000 | 0.0000 | 1.777 | +0.0000 | 0.0000 |  |
| air_share_blend[vol_blend] | 2017-18 | 19.672 | -0.0173 | 0.0119 | 1.879 | +0.0035 | 0.0017 | k=100 c=+0.250 |
| air_share_blend[vol_blend] | 2019-22 | 19.110 | -0.0213 | 0.0077 | 1.829 | +0.0037 | 0.0011 | k=100 c=+0.250 |
| air_share_blend[vol_blend] | 2023-25 | 18.146 | +0.0007 | 0.0086 | 1.719 | +0.0062 | 0.0012 | k=100 c=+0.250 |
| air_share_blend[vol_blend] | 2019-25 | 18.690 | -0.0117 | 0.0057 | 1.781 | +0.0048 | 0.0008 | k=100 c=+0.250 |
| air_share_ratio[vol_ratio] | 2017-18 | 19.689 | -0.0000 | 0.0012 | 1.875 | -0.0001 | 0.0002 | k=200 c=-0.050 |
| air_share_ratio[vol_ratio] | 2019-22 | 19.133 | +0.0020 | 0.0011 | 1.826 | +0.0003 | 0.0002 | k=200 c=-0.050 |
| air_share_ratio[vol_ratio] | 2023-25 | 18.149 | +0.0041 | 0.0031 | 1.714 | +0.0015 | 0.0005 | k=200 c=-0.050 |
| air_share_ratio[vol_ratio] | 2019-25 | 18.705 | +0.0029 | 0.0015 | 1.777 | +0.0008 | 0.0002 | k=200 c=-0.050 |
| adot_x_catch[prior] | 2017-18 | 19.665 | -0.0241 | 0.0133 | 1.875 | +0.0000 | 0.0000 | k=25 c=+0.075 per sd; sd=0.4675, c per unit=+0.1604 |
| adot_x_catch[prior] | 2019-22 | 19.106 | -0.0247 | 0.0087 | 1.826 | +0.0000 | 0.0000 | k=25 c=+0.075 per sd; sd=0.4675, c per unit=+0.1604 |
| adot_x_catch[prior] | 2023-25 | 18.149 | +0.0037 | 0.0098 | 1.713 | +0.0000 | 0.0000 | k=25 c=+0.075 per sd; sd=0.4675, c per unit=+0.1604 |
| adot_x_catch[prior] | 2019-25 | 18.690 | -0.0123 | 0.0065 | 1.777 | +0.0000 | 0.0000 | k=25 c=+0.075 per sd; sd=0.4675, c per unit=+0.1604 |
| adot_x_catch[direct] | 2017-18 | 19.661 | -0.0280 | 0.0167 | 1.875 | +0.0000 | 0.0000 | k=25 c=+0.050 per sd; sd=0.4675, c per unit=+0.107 |
| adot_x_catch[direct] | 2019-22 | 19.108 | -0.0233 | 0.0111 | 1.826 | +0.0000 | 0.0000 | k=25 c=+0.050 per sd; sd=0.4675, c per unit=+0.107 |
| adot_x_catch[direct] | 2023-25 | 18.154 | +0.0089 | 0.0123 | 1.713 | +0.0000 | 0.0000 | k=25 c=+0.050 per sd; sd=0.4675, c per unit=+0.107 |
| adot_x_catch[direct] | 2019-25 | 18.693 | -0.0093 | 0.0082 | 1.777 | +0.0000 | 0.0000 | k=25 c=+0.050 per sd; sd=0.4675, c per unit=+0.107 |
| adot_x_catch[prior_lit] | 2017-18 | 20.079 | +0.3898 | 0.0635 | 1.875 | +0.0000 | 0.0000 | k=200 (literal, no c) |
| adot_x_catch[prior_lit] | 2019-22 | 19.476 | +0.3447 | 0.0405 | 1.826 | +0.0000 | 0.0000 | k=200 (literal, no c) |
| adot_x_catch[prior_lit] | 2023-25 | 18.580 | +0.4351 | 0.0432 | 1.713 | +0.0000 | 0.0000 | k=200 (literal, no c) |
| adot_x_catch[prior_lit] | 2019-25 | 19.086 | +0.3840 | 0.0296 | 1.777 | +0.0000 | 0.0000 | k=200 (literal, no c) |
| pos_ypt_control[prior] | 2017-18 | 19.667 | -0.0223 | 0.0131 | 1.875 | +0.0000 | 0.0000 | k=5 c=+0.075 per sd; sd=0.09562, c per unit=+0.7844 |
| pos_ypt_control[prior] | 2019-22 | 19.113 | -0.0185 | 0.0105 | 1.826 | +0.0000 | 0.0000 | k=5 c=+0.075 per sd; sd=0.09562, c per unit=+0.7844 |
| pos_ypt_control[prior] | 2023-25 | 18.156 | +0.0105 | 0.0109 | 1.713 | +0.0000 | 0.0000 | k=5 c=+0.075 per sd; sd=0.09562, c per unit=+0.7844 |
| pos_ypt_control[prior] | 2019-25 | 18.696 | -0.0059 | 0.0076 | 1.777 | +0.0000 | 0.0000 | k=5 c=+0.075 per sd; sd=0.09562, c per unit=+0.7844 |
| pos_ypt_control[direct] | 2017-18 | 19.666 | -0.0237 | 0.0160 | 1.875 | +0.0000 | 0.0000 | k=5 c=+0.050 per sd; sd=0.09562, c per unit=+0.5229 |
| pos_ypt_control[direct] | 2019-22 | 19.116 | -0.0153 | 0.0133 | 1.826 | +0.0000 | 0.0000 | k=5 c=+0.050 per sd; sd=0.09562, c per unit=+0.5229 |
| pos_ypt_control[direct] | 2023-25 | 18.166 | +0.0203 | 0.0135 | 1.713 | +0.0000 | 0.0000 | k=5 c=+0.050 per sd; sd=0.09562, c per unit=+0.5229 |
| pos_ypt_control[direct] | 2019-25 | 18.702 | +0.0002 | 0.0095 | 1.777 | +0.0000 | 0.0000 | k=5 c=+0.050 per sd; sd=0.09562, c per unit=+0.5229 |
| yac_over_exp[prior] | 2017-18 | 19.689 | -0.0008 | 0.0056 | 1.875 | +0.0000 | 0.0000 | k=100 c=+0.025 per sd; sd=0.101, c per unit=+0.2474 |
| yac_over_exp[prior] | 2019-22 | 19.125 | -0.0060 | 0.0044 | 1.826 | +0.0000 | 0.0000 | k=100 c=+0.025 per sd; sd=0.101, c per unit=+0.2474 |
| yac_over_exp[prior] | 2023-25 | 18.144 | -0.0017 | 0.0047 | 1.713 | +0.0000 | 0.0000 | k=100 c=+0.025 per sd; sd=0.101, c per unit=+0.2474 |
| yac_over_exp[prior] | 2019-25 | 18.698 | -0.0041 | 0.0032 | 1.777 | +0.0000 | 0.0000 | k=100 c=+0.025 per sd; sd=0.101, c per unit=+0.2474 |
| yac_over_exp[direct] | 2017-18 | 19.689 | +0.0000 | 0.0000 | 1.875 | +0.0000 | 0.0000 | k=5 c=+0.000 per sd; sd=0.531, c per unit=+0 |
| yac_over_exp[direct] | 2019-22 | 19.131 | +0.0000 | 0.0000 | 1.826 | +0.0000 | 0.0000 | k=5 c=+0.000 per sd; sd=0.531, c per unit=+0 |
| yac_over_exp[direct] | 2023-25 | 18.145 | +0.0000 | 0.0000 | 1.713 | +0.0000 | 0.0000 | k=5 c=+0.000 per sd; sd=0.531, c per unit=+0 |
| yac_over_exp[direct] | 2019-25 | 18.702 | +0.0000 | 0.0000 | 1.777 | +0.0000 | 0.0000 | k=5 c=+0.000 per sd; sd=0.531, c per unit=+0 |
| separation[prior] | 2017-18 | 19.682 | -0.0075 | 0.0097 | 1.875 | +0.0000 | 0.0000 | k=5 c=+0.050 per sd; sd=0.3474, c per unit=+0.1439 |
| separation[prior] | 2019-22 | 19.154 | +0.0229 | 0.0072 | 1.826 | +0.0000 | 0.0000 | k=5 c=+0.050 per sd; sd=0.3474, c per unit=+0.1439 |
| separation[prior] | 2023-25 | 18.141 | -0.0041 | 0.0077 | 1.713 | +0.0000 | 0.0000 | k=5 c=+0.050 per sd; sd=0.3474, c per unit=+0.1439 |
| separation[prior] | 2019-25 | 18.713 | +0.0111 | 0.0053 | 1.777 | +0.0000 | 0.0000 | k=5 c=+0.050 per sd; sd=0.3474, c per unit=+0.1439 |
| separation[direct] | 2017-18 | 19.686 | -0.0037 | 0.0100 | 1.875 | +0.0000 | 0.0000 | k=5 c=+0.025 per sd; sd=0.3474, c per unit=+0.07197 |
| separation[direct] | 2019-22 | 19.152 | +0.0208 | 0.0074 | 1.826 | +0.0000 | 0.0000 | k=5 c=+0.025 per sd; sd=0.3474, c per unit=+0.07197 |
| separation[direct] | 2023-25 | 18.144 | -0.0016 | 0.0082 | 1.713 | +0.0000 | 0.0000 | k=5 c=+0.025 per sd; sd=0.3474, c per unit=+0.07197 |
| separation[direct] | 2019-25 | 18.713 | +0.0110 | 0.0055 | 1.777 | +0.0000 | 0.0000 | k=5 c=+0.025 per sd; sd=0.3474, c per unit=+0.07197 |
| drop_rate[prior] | 2017-18 | 19.680 | -0.0096 | 0.0082 | 1.875 | +0.0000 | 0.0000 | k=5 c=-0.050 per sd; sd=0.02565, c per unit=-1.949 |
| drop_rate[prior] | 2019-22 | 19.138 | +0.0071 | 0.0068 | 1.826 | +0.0000 | 0.0000 | k=5 c=-0.050 per sd; sd=0.02565, c per unit=-1.949 |
| drop_rate[prior] | 2023-25 | 18.157 | +0.0115 | 0.0071 | 1.713 | +0.0000 | 0.0000 | k=5 c=-0.050 per sd; sd=0.02565, c per unit=-1.949 |
| drop_rate[prior] | 2019-25 | 18.711 | +0.0090 | 0.0049 | 1.777 | +0.0000 | 0.0000 | k=5 c=-0.050 per sd; sd=0.02565, c per unit=-1.949 |
| drop_rate[direct] | 2017-18 | 19.678 | -0.0108 | 0.0082 | 1.875 | +0.0000 | 0.0000 | k=5 c=-0.025 per sd; sd=0.02565, c per unit=-0.9746 |
| drop_rate[direct] | 2019-22 | 19.134 | +0.0032 | 0.0067 | 1.826 | +0.0000 | 0.0000 | k=5 c=-0.025 per sd; sd=0.02565, c per unit=-0.9746 |
| drop_rate[direct] | 2023-25 | 18.152 | +0.0067 | 0.0071 | 1.713 | +0.0000 | 0.0000 | k=5 c=-0.025 per sd; sd=0.02565, c per unit=-0.9746 |
| drop_rate[direct] | 2019-25 | 18.707 | +0.0047 | 0.0049 | 1.777 | +0.0000 | 0.0000 | k=5 c=-0.025 per sd; sd=0.02565, c per unit=-0.9746 |
| combo | 2017-18 | 19.646 | -0.0434 | 0.0226 | 1.875 | -0.0002 | 0.0004 | adot_x_catch[direct] k=25 c=+0.050; separation[prior] k=5 c=+0.050; drop_rate[direct] k=5 c=-0.025; yac_over_exp[prior] k=100 c=+0.025; air_share_ratio[vol_ratio] k=200 c=-0.100 |
| combo | 2019-22 | 19.132 | +0.0007 | 0.0155 | 1.827 | +0.0008 | 0.0003 | adot_x_catch[direct] k=25 c=+0.050; separation[prior] k=5 c=+0.050; drop_rate[direct] k=5 c=-0.025; yac_over_exp[prior] k=100 c=+0.025; air_share_ratio[vol_ratio] k=200 c=-0.100 |
| combo | 2023-25 | 18.161 | +0.0153 | 0.0171 | 1.717 | +0.0043 | 0.0010 | adot_x_catch[direct] k=25 c=+0.050; separation[prior] k=5 c=+0.050; drop_rate[direct] k=5 c=-0.025; yac_over_exp[prior] k=100 c=+0.025; air_share_ratio[vol_ratio] k=200 c=-0.100 |
| combo | 2019-25 | 18.709 | +0.0071 | 0.0115 | 1.779 | +0.0023 | 0.0005 | adot_x_catch[direct] k=25 c=+0.050; separation[prior] k=5 c=+0.050; drop_rate[direct] k=5 c=-0.025; yac_over_exp[prior] k=100 c=+0.025; air_share_ratio[vol_ratio] k=200 c=-0.100 |

### rush_yards

| variant | window | yards MAE | diff | SE | volume MAE | diff | SE | params |
|---|---|---|---|---|---|---|---|---|
| rule | 2017-18 | 18.041 | +0.0000 | 0.0000 | 3.082 | +0.0000 | 0.0000 |  |
| rule | 2019-22 | 17.687 | +0.0000 | 0.0000 | 2.933 | +0.0000 | 0.0000 |  |
| rule | 2023-25 | 16.968 | +0.0000 | 0.0000 | 2.839 | +0.0000 | 0.0000 |  |
| rule | 2019-25 | 17.368 | +0.0000 | 0.0000 | 2.891 | +0.0000 | 0.0000 |  |
| ryoe[prior] | 2017-18 | 18.006 | -0.0355 | 0.0331 | 3.082 | +0.0000 | 0.0000 | k=5 c=+0.400 per sd; sd=0.3447, c per unit=+1.16 |
| ryoe[prior] | 2019-22 | 17.689 | +0.0028 | 0.0292 | 2.933 | +0.0000 | 0.0000 | k=5 c=+0.400 per sd; sd=0.3447, c per unit=+1.16 |
| ryoe[prior] | 2023-25 | 16.998 | +0.0295 | 0.0322 | 2.839 | +0.0000 | 0.0000 | k=5 c=+0.400 per sd; sd=0.3447, c per unit=+1.16 |
| ryoe[prior] | 2019-25 | 17.383 | +0.0146 | 0.0216 | 2.891 | +0.0000 | 0.0000 | k=5 c=+0.400 per sd; sd=0.3447, c per unit=+1.16 |
| ryoe[direct] | 2017-18 | 18.033 | -0.0083 | 0.0161 | 3.082 | +0.0000 | 0.0000 | k=5 c=+0.025 per sd; sd=0.3447, c per unit=+0.07252 |
| ryoe[direct] | 2019-22 | 17.658 | -0.0284 | 0.0138 | 2.933 | +0.0000 | 0.0000 | k=5 c=+0.025 per sd; sd=0.3447, c per unit=+0.07252 |
| ryoe[direct] | 2023-25 | 16.943 | -0.0249 | 0.0181 | 2.839 | +0.0000 | 0.0000 | k=5 c=+0.025 per sd; sd=0.3447, c per unit=+0.07252 |
| ryoe[direct] | 2019-25 | 17.341 | -0.0268 | 0.0111 | 2.891 | +0.0000 | 0.0000 | k=5 c=+0.025 per sd; sd=0.3447, c per unit=+0.07252 |
| ryoe[prior_lit] | 2017-18 | 18.025 | -0.0163 | 0.0091 | 3.082 | +0.0000 | 0.0000 | k=5 (literal, no c) |
| ryoe[prior_lit] | 2019-22 | 17.671 | -0.0155 | 0.0072 | 2.933 | +0.0000 | 0.0000 | k=5 (literal, no c) |
| ryoe[prior_lit] | 2023-25 | 16.958 | -0.0097 | 0.0093 | 2.839 | +0.0000 | 0.0000 | k=5 (literal, no c) |
| ryoe[prior_lit] | 2019-25 | 17.355 | -0.0129 | 0.0058 | 2.891 | +0.0000 | 0.0000 | k=5 (literal, no c) |
| ryoe[rate_lit] | 2017-18 | 18.236 | +0.1950 | 0.0664 | 3.082 | +0.0000 | 0.0000 | k=10 (literal, no c) |
| ryoe[rate_lit] | 2019-22 | 17.880 | +0.1935 | 0.0389 | 2.933 | +0.0000 | 0.0000 | k=10 (literal, no c) |
| ryoe[rate_lit] | 2023-25 | 17.107 | +0.1385 | 0.0434 | 2.839 | +0.0000 | 0.0000 | k=10 (literal, no c) |
| ryoe[rate_lit] | 2019-25 | 17.537 | +0.1691 | 0.0290 | 2.891 | +0.0000 | 0.0000 | k=10 (literal, no c) |
| inside10_share[td_prior] | 2017-18 | 18.041 | +0.0000 | 0.0000 | 3.082 | +0.0000 | 0.0000 | k=400 c=+1.500 |
| inside10_share[td_prior] | 2019-22 | 17.687 | +0.0000 | 0.0000 | 2.933 | +0.0000 | 0.0000 | k=400 c=+1.500 |
| inside10_share[td_prior] | 2023-25 | 16.968 | +0.0000 | 0.0000 | 2.839 | +0.0000 | 0.0000 | k=400 c=+1.500 |
| inside10_share[td_prior] | 2019-25 | 17.368 | +0.0000 | 0.0000 | 2.891 | +0.0000 | 0.0000 | k=400 c=+1.500 |

Rushing touchdowns (the inside-10 signal; Poisson log loss on the same rows, the touch frame):

| variant | window | log loss | diff | SE |
|---|---|---|---|---|
| inside10_share[td_prior] | 2017-18 | 0.54016 | -0.00028 | 0.00029 |
| inside10_share[td_prior] | 2019-22 | 0.58222 | -0.00004 | 0.00018 |
| inside10_share[td_prior] | 2023-25 | 0.55170 | -0.00036 | 0.00022 |
| inside10_share[td_prior] | 2019-25 | 0.56869 | -0.00018 | 0.00014 |

### pass_yards

| variant | window | yards MAE | diff | SE | volume MAE | diff | SE | params |
|---|---|---|---|---|---|---|---|---|
| rule | 2017-18 | 60.722 | +0.0000 | 0.0000 | 7.594 | +0.0000 | 0.0000 |  |
| rule | 2019-22 | 56.574 | +0.0000 | 0.0000 | 7.686 | +0.0000 | 0.0000 |  |
| rule | 2023-25 | 56.109 | +0.0000 | 0.0000 | 7.701 | +0.0000 | 0.0000 |  |
| rule | 2019-25 | 56.369 | +0.0000 | 0.0000 | 7.692 | +0.0000 | 0.0000 |  |
| cpoe[prior] | 2017-18 | 60.671 | -0.0515 | 0.1043 | 7.594 | +0.0000 | 0.0000 | k=25 c=+0.125 per sd; sd=3.34, c per unit=+0.03743 |
| cpoe[prior] | 2019-22 | 56.564 | -0.0100 | 0.0491 | 7.686 | +0.0000 | 0.0000 | k=25 c=+0.125 per sd; sd=3.34, c per unit=+0.03743 |
| cpoe[prior] | 2023-25 | 56.038 | -0.0715 | 0.0649 | 7.701 | +0.0000 | 0.0000 | k=25 c=+0.125 per sd; sd=3.34, c per unit=+0.03743 |
| cpoe[prior] | 2019-25 | 56.332 | -0.0371 | 0.0396 | 7.692 | +0.0000 | 0.0000 | k=25 c=+0.125 per sd; sd=3.34, c per unit=+0.03743 |
| cpoe[direct] | 2017-18 | 60.557 | -0.1654 | 0.2267 | 7.594 | +0.0000 | 0.0000 | k=1600 c=-0.050 per sd; sd=0.3876, c per unit=-0.129 |
| cpoe[direct] | 2019-22 | 57.011 | +0.4368 | 0.1328 | 7.686 | +0.0000 | 0.0000 | k=1600 c=-0.050 per sd; sd=0.3876, c per unit=-0.129 |
| cpoe[direct] | 2023-25 | 56.401 | +0.2917 | 0.1386 | 7.701 | +0.0000 | 0.0000 | k=1600 c=-0.050 per sd; sd=0.3876, c per unit=-0.129 |
| cpoe[direct] | 2019-25 | 56.742 | +0.3729 | 0.0962 | 7.692 | +0.0000 | 0.0000 | k=1600 c=-0.050 per sd; sd=0.3876, c per unit=-0.129 |
| adot[prior] | 2017-18 | 60.588 | -0.1338 | 0.1648 | 7.594 | +0.0000 | 0.0000 | k=1600 c=-0.375 per sd; sd=0.1065, c per unit=-3.523 |
| adot[prior] | 2019-22 | 56.754 | +0.1806 | 0.1028 | 7.686 | +0.0000 | 0.0000 | k=1600 c=-0.375 per sd; sd=0.1065, c per unit=-3.523 |
| adot[prior] | 2023-25 | 56.124 | +0.0149 | 0.1141 | 7.701 | +0.0000 | 0.0000 | k=1600 c=-0.375 per sd; sd=0.1065, c per unit=-3.523 |
| adot[prior] | 2019-25 | 56.477 | +0.1077 | 0.0764 | 7.692 | +0.0000 | 0.0000 | k=1600 c=-0.375 per sd; sd=0.1065, c per unit=-3.523 |
| adot[direct] | 2017-18 | 60.624 | -0.0976 | 0.1190 | 7.594 | +0.0000 | 0.0000 | k=25 c=-0.025 per sd; sd=0.8672, c per unit=-0.02883 |
| adot[direct] | 2019-22 | 56.674 | +0.1002 | 0.0747 | 7.686 | +0.0000 | 0.0000 | k=25 c=-0.025 per sd; sd=0.8672, c per unit=-0.02883 |
| adot[direct] | 2023-25 | 56.048 | -0.0613 | 0.0807 | 7.701 | +0.0000 | 0.0000 | k=25 c=-0.025 per sd; sd=0.8672, c per unit=-0.02883 |
| adot[direct] | 2019-25 | 56.398 | +0.0291 | 0.0549 | 7.692 | +0.0000 | 0.0000 | k=25 c=-0.025 per sd; sd=0.8672, c per unit=-0.02883 |
| ttt_x_opp_pressure[direct] | 2017-18 | 60.722 | +0.0000 | 0.0000 | 7.594 | +0.0000 | 0.0000 | k=25 c=+0.000 per sd; sd=0.002644, c per unit=+0 |
| ttt_x_opp_pressure[direct] | 2019-22 | 56.574 | +0.0000 | 0.0000 | 7.686 | +0.0000 | 0.0000 | k=25 c=+0.000 per sd; sd=0.002644, c per unit=+0 |
| ttt_x_opp_pressure[direct] | 2023-25 | 56.109 | +0.0000 | 0.0000 | 7.701 | +0.0000 | 0.0000 | k=25 c=+0.000 per sd; sd=0.002644, c per unit=+0 |
| ttt_x_opp_pressure[direct] | 2019-25 | 56.369 | +0.0000 | 0.0000 | 7.692 | +0.0000 | 0.0000 | k=25 c=+0.000 per sd; sd=0.002644, c per unit=+0 |
| combo | 2017-18 | 60.352 | -0.3696 | 0.2947 | 7.594 | +0.0000 | 0.0000 | cpoe[direct] k=1600 c=-0.050; adot[prior] k=1600 c=-0.475 |
| combo | 2019-22 | 57.218 | +0.6438 | 0.1804 | 7.686 | +0.0000 | 0.0000 | cpoe[direct] k=1600 c=-0.050; adot[prior] k=1600 c=-0.475 |
| combo | 2023-25 | 56.504 | +0.3953 | 0.1920 | 7.701 | +0.0000 | 0.0000 | cpoe[direct] k=1600 c=-0.050; adot[prior] k=1600 c=-0.475 |
| combo | 2019-25 | 56.904 | +0.5344 | 0.1317 | 7.692 | +0.0000 | 0.0000 | cpoe[direct] k=1600 c=-0.050; adot[prior] k=1600 c=-0.475 |

## Fits on 2017-18 (best k and c per signal and form)

| stat | signal | form | k | c | sd of the deviation | fit loss | rule's fit loss |
|---|---|---|---|---|---|---|---|
| rec_yards | air_share_blend | vol_blend | 100 | +0.250 | 1 | 19.6721 | 19.6893 |
| rec_yards | air_share_ratio | vol_ratio | 200 | -0.050 | 1 | 19.6893 | 19.6893 |
| rec_yards | adot_x_catch | prior | 25 | +0.075 | 0.4675 | 19.6652 | 19.6893 |
| rec_yards | adot_x_catch | direct | 25 | +0.050 | 0.4675 | 19.6613 | 19.6893 |
| rec_yards | adot_x_catch | prior_lit | 200 | +1.000 | 1 | 20.0791 | 19.6893 |
| rec_yards | pos_ypt_control | prior | 5 | +0.075 | 0.09562 | 19.667 | 19.6893 |
| rec_yards | pos_ypt_control | direct | 5 | +0.050 | 0.09562 | 19.6657 | 19.6893 |
| rec_yards | yac_over_exp | prior | 100 | +0.025 | 0.101 | 19.6885 | 19.6893 |
| rec_yards | yac_over_exp | direct | 5 | +0.000 | 0.531 | 19.6893 | 19.6893 |
| rec_yards | separation | prior | 5 | +0.050 | 0.3474 | 19.6818 | 19.6893 |
| rec_yards | separation | direct | 5 | +0.025 | 0.3474 | 19.6856 | 19.6893 |
| rec_yards | drop_rate | prior | 5 | -0.050 | 0.02565 | 19.6797 | 19.6893 |
| rec_yards | drop_rate | direct | 5 | -0.025 | 0.02565 | 19.6785 | 19.6893 |
| rush_yards | ryoe | prior | 5 | +0.400 | 0.3447 | 18.0055 | 18.041 |
| rush_yards | ryoe | direct | 5 | +0.025 | 0.3447 | 18.0327 | 18.041 |
| rush_yards | ryoe | prior_lit | 5 | +1.000 | 1 | 18.0247 | 18.041 |
| rush_yards | ryoe | rate_lit | 10 | +1.000 | 1 | 18.236 | 18.041 |
| rush_td | inside10_share | td_prior | 400 | +1.500 | 1 | 0.54016 | 0.54044 |
| pass_yards | cpoe | prior | 25 | +0.125 | 3.34 | 60.6706 | 60.7221 |
| pass_yards | cpoe | direct | 1600 | -0.050 | 0.3876 | 60.5567 | 60.7221 |
| pass_yards | adot | prior | 1600 | -0.375 | 0.1065 | 60.5883 | 60.7221 |
| pass_yards | adot | direct | 25 | -0.025 | 0.8672 | 60.6245 | 60.7221 |
| pass_yards | ttt_x_opp_pressure | direct | 25 | +0.000 | 0.002644 | 60.7221 | 60.7221 |

Combinations (forward selection on 2017-18 among the signals that beat the rule there):

- rec: adot_x_catch[direct] k=25 c=+0.050; separation[prior] k=5 c=+0.050; drop_rate[direct] k=5 c=-0.025; yac_over_exp[prior] k=100 c=+0.025; air_share_ratio[vol_ratio] k=200 c=-0.100 (fit MAE 19.6459)
- rush: fewer than two signals beat the rule on 2017-18: no combination (only ryoe)
- pass: cpoe[direct] k=1600 c=-0.050; adot[prior] k=1600 c=-0.475 (fit MAE 60.3525)

## Verdict per variant (the rule above)

| stat | variant | better on both windows | beyond one SE on one | worst tier diff (either window) | adopted |
|---|---|---|---|---|---|
| rec_yards | air_share_blend[vol_blend] | False | True | +0.275 | no |
| rec_yards | air_share_ratio[vol_ratio] | False | False | +0.012 | no |
| rec_yards | adot_x_catch[prior] | False | True | +0.136 | no |
| rec_yards | adot_x_catch[direct] | False | True | +0.291 | no |
| rec_yards | adot_x_catch[prior_lit] | False | False | +0.904 | no |
| rec_yards | pos_ypt_control[prior] | False | True | +0.131 | no |
| rec_yards | pos_ypt_control[direct] | False | True | +0.286 | no |
| rec_yards | yac_over_exp[prior] | True | True | +0.013 | **passes** |
| rec_yards | yac_over_exp[direct] | False | False | +0.000 | no |
| rec_yards | separation[prior] | False | False | +0.059 | no |
| rec_yards | separation[direct] | False | False | +0.054 | no |
| rec_yards | drop_rate[prior] | False | False | +0.131 | no |
| rec_yards | drop_rate[direct] | False | False | +0.207 | no |
| rec_yards | combo | False | False | +0.470 | no |
| rush_yards | ryoe[prior] | False | False | +0.134 | no |
| rush_yards | ryoe[direct] | True | True | +0.006 | **passes** |
| rush_yards | ryoe[prior_lit] | True | True | +0.045 | **passes** |
| rush_yards | ryoe[rate_lit] | False | False | +0.436 | no |
| rush_td | inside10_share[td_prior] | True | True |  | passes (side reading, log loss) |
| pass_yards | cpoe[prior] | True | True | +0.033 | **passes** |
| pass_yards | cpoe[direct] | False | False | +6.906 | no |
| pass_yards | adot[prior] | False | False | +3.172 | no |
| pass_yards | adot[direct] | False | False | +2.947 | no |
| pass_yards | ttt_x_opp_pressure[direct] | False | False | +0.000 | no |
| pass_yards | combo | False | False | +11.133 | no |

## Placebo (the signal shuffled within season, refitted on 2017-18, 40 draws)

| stat | variant | placebo passes | real pooled 2019-25 diff | placebo mean | placebo min | p (placebo <= real) |
|---|---|---|---|---|---|---|
| rec_yards | yac_over_exp[prior] | 0 / 40 | -0.0041 | +0.0029 | +0.0000 | 0.024 |
| rush_yards | ryoe[direct] | 1 / 40 | -0.0268 | +0.0135 | -0.0114 | 0.024 |
| rush_yards | ryoe[prior_lit] | 8 / 40 | -0.0129 | +0.0007 | -0.0094 | 0.024 |
| pass_yards | cpoe[prior] | 1 / 40 | -0.0371 | +0.0404 | -0.0189 | 0.024 |

## Tier check (tiers of the rule's yards line; diff = variant MAE minus the rule's)


rec_yards yac_over_exp[prior]

| window | tier | n | MAE | rule MAE | diff | bias |
|---|---|---|---|---|---|---|
| 2017-18 | 0-20 | 3624 | 13.880 | 13.878 | +0.001 | -7.486 |
| 2017-18 | 20-40 | 2164 | 21.867 | 21.868 | -0.002 | -6.816 |
| 2017-18 | 40-60 | 1183 | 27.727 | 27.747 | -0.020 | -2.892 |
| 2017-18 | 60-80 | 477 | 31.760 | 31.711 | +0.050 | -6.845 |
| 2017-18 | 80+ | 70 | 34.958 | 35.071 | -0.113 | +1.438 |
| 2019-22 | 0-20 | 8193 | 13.224 | 13.225 | -0.001 | -6.793 |
| 2019-22 | 20-40 | 4153 | 20.933 | 20.941 | -0.008 | -5.327 |
| 2019-22 | 40-60 | 2543 | 28.897 | 28.909 | -0.012 | -6.143 |
| 2019-22 | 60-80 | 1002 | 31.859 | 31.875 | -0.016 | -4.041 |
| 2019-22 | 80+ | 185 | 36.598 | 36.629 | -0.032 | +0.080 |
| 2023-25 | 0-20 | 6759 | 12.532 | 12.531 | +0.001 | -6.036 |
| 2023-25 | 20-40 | 3015 | 21.062 | 21.071 | -0.009 | -6.274 |
| 2023-25 | 40-60 | 1803 | 27.399 | 27.404 | -0.006 | -5.533 |
| 2023-25 | 60-80 | 657 | 32.407 | 32.395 | +0.013 | -4.466 |
| 2023-25 | 80+ | 149 | 38.759 | 38.748 | +0.011 | -3.342 |
| 2019-25 | 0-20 | 14952 | 12.911 | 12.911 | -0.000 | -6.450 |
| 2019-25 | 20-40 | 7168 | 20.987 | 20.996 | -0.008 | -5.725 |
| 2019-25 | 40-60 | 4346 | 28.276 | 28.285 | -0.009 | -5.890 |
| 2019-25 | 60-80 | 1659 | 32.076 | 32.081 | -0.004 | -4.209 |
| 2019-25 | 80+ | 334 | 37.562 | 37.575 | -0.013 | -1.447 |

rush_yards ryoe[direct]

| window | tier | n | MAE | rule MAE | diff | bias |
|---|---|---|---|---|---|---|
| 2017-18 | 0-20 | 1655 | 10.890 | 10.896 | -0.006 | -4.492 |
| 2017-18 | 20-40 | 870 | 20.197 | 20.280 | -0.082 | -4.396 |
| 2017-18 | 40-60 | 655 | 26.480 | 26.438 | +0.042 | -4.718 |
| 2017-18 | 60-80 | 262 | 31.558 | 31.454 | +0.104 | -2.093 |
| 2017-18 | 80+ | 55 | 33.691 | 33.736 | -0.045 | +7.105 |
| 2019-22 | 0-20 | 3917 | 10.416 | 10.412 | +0.003 | -4.234 |
| 2019-22 | 20-40 | 1815 | 20.794 | 20.829 | -0.034 | -4.313 |
| 2019-22 | 40-60 | 1349 | 26.966 | 27.015 | -0.050 | -6.992 |
| 2019-22 | 60-80 | 583 | 31.368 | 31.533 | -0.165 | -3.843 |
| 2019-22 | 80+ | 114 | 36.320 | 36.397 | -0.078 | -7.153 |
| 2023-25 | 0-20 | 3132 | 10.471 | 10.464 | +0.006 | -4.534 |
| 2023-25 | 20-40 | 1417 | 18.591 | 18.633 | -0.042 | -3.056 |
| 2023-25 | 40-60 | 1068 | 26.368 | 26.438 | -0.070 | -6.311 |
| 2023-25 | 60-80 | 493 | 29.702 | 29.758 | -0.056 | -3.762 |
| 2023-25 | 80+ | 86 | 35.339 | 35.475 | -0.137 | +3.467 |
| 2019-25 | 0-20 | 7049 | 10.440 | 10.435 | +0.005 | -4.367 |
| 2019-25 | 20-40 | 3232 | 19.828 | 19.866 | -0.038 | -3.762 |
| 2019-25 | 40-60 | 2417 | 26.701 | 26.760 | -0.059 | -6.691 |
| 2019-25 | 60-80 | 1076 | 30.605 | 30.720 | -0.115 | -3.806 |
| 2019-25 | 80+ | 200 | 35.898 | 36.001 | -0.103 | -2.586 |

rush_yards ryoe[prior_lit]

| window | tier | n | MAE | rule MAE | diff | bias |
|---|---|---|---|---|---|---|
| 2017-18 | 0-20 | 1655 | 10.889 | 10.896 | -0.007 | -4.491 |
| 2017-18 | 20-40 | 870 | 20.226 | 20.280 | -0.053 | -4.337 |
| 2017-18 | 40-60 | 655 | 26.423 | 26.438 | -0.015 | -4.696 |
| 2017-18 | 60-80 | 262 | 31.494 | 31.454 | +0.041 | -2.394 |
| 2017-18 | 80+ | 55 | 33.727 | 33.736 | -0.009 | +6.804 |
| 2019-22 | 0-20 | 3917 | 10.412 | 10.412 | -0.000 | -4.236 |
| 2019-22 | 20-40 | 1815 | 20.804 | 20.829 | -0.025 | -4.277 |
| 2019-22 | 40-60 | 1349 | 26.982 | 27.015 | -0.033 | -6.935 |
| 2019-22 | 60-80 | 583 | 31.475 | 31.533 | -0.058 | -4.325 |
| 2019-22 | 80+ | 114 | 36.443 | 36.397 | +0.045 | -9.244 |
| 2023-25 | 0-20 | 3132 | 10.467 | 10.464 | +0.003 | -4.532 |
| 2023-25 | 20-40 | 1417 | 18.618 | 18.633 | -0.015 | -2.933 |
| 2023-25 | 40-60 | 1068 | 26.397 | 26.438 | -0.041 | -6.354 |
| 2023-25 | 60-80 | 493 | 29.756 | 29.758 | -0.002 | -4.406 |
| 2023-25 | 80+ | 86 | 35.444 | 35.475 | -0.032 | +1.332 |
| 2019-25 | 0-20 | 7049 | 10.436 | 10.435 | +0.001 | -4.367 |
| 2019-25 | 20-40 | 3232 | 19.846 | 19.866 | -0.020 | -3.688 |
| 2019-25 | 40-60 | 2417 | 26.723 | 26.760 | -0.037 | -6.678 |
| 2019-25 | 60-80 | 1076 | 30.687 | 30.720 | -0.032 | -4.363 |
| 2019-25 | 80+ | 200 | 36.013 | 36.001 | +0.012 | -4.696 |

pass_yards cpoe[prior]

| window | tier | n | MAE | rule MAE | diff | bias |
|---|---|---|---|---|---|---|
| 2017-18 | 0-150 | 15 | 38.336 | 46.727 | -8.391 | +29.488 |
| 2017-18 | 150-200 | 88 | 63.003 | 62.910 | +0.094 | +5.568 |
| 2017-18 | 200-250 | 643 | 62.154 | 62.067 | +0.087 | -9.913 |
| 2017-18 | 250-300 | 290 | 57.209 | 57.225 | -0.016 | -7.567 |
| 2017-18 | 300+ | 10 | 78.623 | 77.382 | +1.241 | +15.777 |
| 2019-22 | 0-150 | 24 | 45.207 | 46.113 | -0.906 | +32.154 |
| 2019-22 | 150-200 | 220 | 59.040 | 59.286 | -0.246 | +20.016 |
| 2019-22 | 200-250 | 1304 | 55.031 | 55.000 | +0.031 | -7.080 |
| 2019-22 | 250-300 | 613 | 59.571 | 59.539 | +0.032 | -10.403 |
| 2019-22 | 300+ | 15 | 48.776 | 49.138 | -0.362 | +10.392 |
| 2023-25 | 0-150 | 51 | 54.064 | 55.034 | -0.970 | +43.361 |
| 2023-25 | 150-200 | 257 | 60.505 | 60.918 | -0.414 | +12.926 |
| 2023-25 | 200-250 | 1133 | 54.599 | 54.566 | +0.033 | -3.523 |
| 2023-25 | 250-300 | 270 | 58.298 | 58.310 | -0.012 | +3.013 |
| 2023-25 | 300+ | 1 | 28.205 | 29.014 | -0.809 | +28.205 |
| 2019-25 | 0-150 | 75 | 51.230 | 52.179 | -0.949 | +39.775 |
| 2019-25 | 150-200 | 477 | 59.829 | 60.166 | -0.336 | +16.196 |
| 2019-25 | 200-250 | 2437 | 54.830 | 54.798 | +0.032 | -5.426 |
| 2019-25 | 250-300 | 883 | 59.182 | 59.163 | +0.019 | -6.300 |
| 2019-25 | 300+ | 16 | 47.491 | 47.881 | -0.390 | +11.506 |

## Runtime

build (props_by_season.build x 3, cached; once): 54s on the shared machine; this scoring run, placebo included: 119s.

## Verdict

**Three variants pass the rule, one per stat, each by a few hundredths of a yard or less:**

| stat | variant (constants fitted on 2017-18) | 2019-22 rule -> variant (diff, SE) | 2023-25 rule -> variant (diff, SE) | worst tier | placebo |
|---|---|---|---|---|---|
| receiving yards | YAC over expected as the prior: prior = league x (1 + 0.2474 x (YACOE - league's)), YACOE shrunk with k = 100 catches | 19.131 -> 19.125 (-0.0060, 0.0044) | 18.145 -> 18.144 (-0.0017, 0.0047) | +0.013 | 0 / 40 pass; real beats all 40 |
| rushing yards | RYOE as the prior, literally: prior = league ypc + (RYOE per carry - league's), RYOE shrunk with k = 5 carries | 17.687 -> 17.671 (-0.0155, 0.0072) | 16.968 -> 16.958 (-0.0097, 0.0093) | +0.045 | 8 / 40 pass; real beats all 40 |
| passing yards | CPOE as the prior: prior = league x (1 + 0.03743 x (CPOE - league's)), CPOE shrunk with k = 25 attempts | 56.574 -> 56.564 (-0.0100, 0.0491) | 56.109 -> 56.038 (-0.0715, 0.0649) | +0.033 | 1 / 40 pass; real beats all 40 |

Volume MAE is unchanged by all three (they move the rate, not the volume). The rushing direct form (the rate x (1 +
0.0725 per yard of RYOE over the league's, k = 5)) also passes with a larger gain on both windows (-0.028 / -0.025,
pooled -0.027 against -0.013), but its 2017-18 MAE is higher (18.033 against 18.025), so the tie-break set before the
run takes the literal prior. Where CPOE helps is the backups and spot starters (the 0-150 and 150-200 tiers), whose
few dropbacks leave the league prior most of the weight; the starters' tiers move by 0.03 yards.

**Read it for what it is.** The question was whether tracking and charting measures make the per-game yards
projection more accurate. They barely do: the three that pass change the error by 0.002 to 0.07 yards per
player-game (0.01% to 0.13% of it). Each beat every one of 40 refits of the same variant on a shuffled signal
(pooled 2019-25), so each carries some information. But 22 single-signal yards variants (and two combinations) were
scored, and the rule is loose: two independent windows let a pure-noise variant through about one time in eight,
and the placebo refits passed 10 times in 160 (8 of 40 for the RYOE literal prior, whose paired errors are so
tightly matched that a hundredth of a yard is one standard error). The fit window is thin for these signals: RYOE
and PFR drops start in 2018, so 2017-18 is effectively 2018 for them (22% of rushing rows carry an RYOE reading
there), and the RYOE k = 5 sits at the grid's lower edge (nearly unshrunk). NGS's own
expected-yards and expected-completion models are fitted by NGS on seasons that may include the test windows, a
look-ahead this study cannot remove.

**What lost** (each against the rule, 2019-22 / 2023-25; details in the tables above):
- Air-yards share as a second volume signal: the literal blend (a = 0.25 on the air-yards share) helps 2019-22
  receiving yards (-0.021, 2.8 SE) and nothing on 2023-25 (+0.001), makes targets worse on both (+0.004 / +0.006,
  3-5 SE) and the 80+ tier worse by 0.28 / 0.19 (the stars' targets pulled toward their air yards); the
  position-relative ratio form fits to almost nothing and is worse on both (+0.002 / +0.004).
- ADOT x catch rate as the prior: -0.025 / +0.004 (the fitted tilt), +0.34 / +0.44 literally (league x his ADOT x catch
  rate over the league's: the round-2 lesson again, taking yards per target apart makes it worse). His position's
  yards per target alone, with no player information (the control), gets most of the 2019-22 gain (-0.019 / +0.011).
- Separation: +0.023 / -0.004 (worse on 2019-22 by 3 SE). Drop rate: worse on both. YAC over expected as a direct
  factor: fitted to zero.
- Rushing RYOE as his rate outright (league + RYOE, his yards per carry dropped): +0.19 / +0.14.
- Passing ADOT: +0.14 / -0.01 (prior), +0.10 / -0.06 (direct); CPOE as a direct factor +0.44 / +0.29; time to throw x
  the opponent's pressure rate: fitted to zero.
- Combinations (forward selection on 2017-18): receiving (ADOT x catch, separation, drops, YACOE, air share ratio)
  -0.043 on the fit window, +0.001 / +0.015 after; passing (CPOE direct, ADOT prior) +0.64 / +0.40, fitted to 1,046
  QB-games. Rushing has one yards signal, so no combination; the three passing variants are one per stat and do not
  interact (each moves one kind's line).
- Side reading, touchdowns: the share of his carries inside the 10 as a tilt of the rushing touchdown prior lowers the
  Poisson log loss by 0.00004 / 0.00036 (0.2 / 1.6 SE) on this touch frame, with the tilt at the grid's edge. Round 10
  (B) lost with a yard-line prior; a touchdown change is judged on the active frame (BACKTEST_TD), which this study
  did not build. Not proposed.

## Integration (if taken)

The three pass the rule; the gains are small enough that leaving the rule alone is also defensible, and each adds a
dependency on the weekly NGS pull (a player or week without an NGS row gets 0 deviation, which is the rule as
before). The code below is checked in this script (`integration_check`): the backtest function reproduces the scored
MAE to the fourth decimal (constants rounded to four significant figures) and the live function returns the same
deviation as the backtest for every projected player in five sample weeks (max difference 3e-15).

**nflmodel/props.py**, beside the other round constants (after `SHARE_A_W`):

```python
# round 19 (29 Sep 2026, experiments/props_tracking.py, reports/props_tracking.md): a tracking signal moves the league rate a
# player's own rate is shrunk toward. Receivers: NGS YAC over expected per catch; rushers: NGS rush yards over expected per
# carry (league ypc + his RYOE over the league's); QBs: NGS CPOE. Each from his NGS weekly rows before the week (games the
# NGS pages list: 5+ targets, 10+ carries, 15+ attempts), decayed DECAY per row with FADE's season factor, shrunk toward the
# league's (last season and this season before the week) with k of its own weight. Fitted on 2017-18. Each passed the
# pre-set rule (better on both windows, beyond one paired SE on one, no tier worse by 0.1): receiving 19.131 / 18.145 ->
# 19.125 / 18.144, rushing 17.687 / 16.968 -> 17.671 / 16.958, passing 56.574 / 56.109 -> 56.564 / 56.038.
# Entries: NGS file under RAW, value column, weight column, value is a total (else a per-weight average), k, form, c.
TRACK = {"rec": ("ngs_rec/ngs_receiving.parquet", "avg_yac_above_expectation", "receptions", False, 100.0, "mul", 0.2474),
         "rush": ("ngs_rush/ngs_rushing.parquet", "rush_yards_over_expected", "rush_attempts", True, 5.0, "add", 1.0),
         "pass": ("ngs/ngs_passing.parquet", "completion_percentage_above_expectation", "attempts", False, 25.0, "mul", 0.03743)}


def track_prior(kind: str, league: float, dev: float):
    """The league rate his own rate is shrunk toward, moved by his tracking signal's deviation (round 19)."""
    _, _, _, _, _, form, c = TRACK[kind]
    return league + c * dev if form == "add" else league * (1 + c * dev)


def tracking(season: int, week: int) -> dict:
    """kind -> player id -> his NGS signal (TRACK) decayed and shrunk toward the league's, minus the league's, as of
    (season, week). A player without an NGS row gets nothing (0 in project_game), the rule as before."""
    out = {}
    for kind, (path, col, wcol, total, k, _, _) in TRACK.items():
        f = RAW / path; out[kind] = {}
        if not f.exists():
            continue
        x = pd.read_parquet(f); x = x[(x.week > 0) & (x.season_type == "REG") & x.player_gsis_id.notna() & x[col].notna()].drop_duplicates(["player_gsis_id", "season", "week"])
        x = x[(x.season < season) | ((x.season == season) & (x.week < week))].assign(v=lambda y: (y[col] if total else y[col] * y[wcol]).astype(float), w=lambda y: y[wcol].astype(float))
        lg = x[x.season >= season - 1]; ref = float(lg.v.sum() / lg.w.sum()) if lg.w.sum() > 0 else None
        if ref is None:
            continue
        sf = FADE.get(kind, (1.0, 1.0))[0]
        for pid, g in x.sort_values(["season", "week"], ascending=False).groupby("player_gsis_id"):
            sn = g.season.values; bnd = np.r_[int(sn[0] < season), (sn[1:] != sn[:-1]).astype(int)].cumsum()
            wts = DECAY ** np.arange(len(g)) * sf ** bnd
            out[kind][pid] = ((g.v.values * wts).sum() + k * ref) / ((g.w.values * wts).sum() + k) - ref
    return out
```

in `run()`, after `R, RU, Q, D, V, L = ...`:

```python
TK = tracking(season, week)   # round 19
for kind_, P_ in (("rec", R), ("rush", RU), ("pass", Q)):
    for pid_, p_ in P_.items(): p_["track_dev"] = round(float(TK[kind_].get(pid_, 0.0)), 4)
```

in `project_game`, the three shrinkage lines (the defense move `_toward` keeps the plain league rate):

```python
ypt_s = _shrunk(p["ypt"], p["targets"], track_prior("rec", L["ypt"], p.get("track_dev", 0.0)), K["rec"])
ypc_s = _shrunk(p["ypc"], p["carries"], track_prior("rush", L["ypc"], p.get("track_dev", 0.0)), K["rush"])
ypd_s = _shrunk(p["ypd"], p["dropbacks"], track_prior("pass", L["ypd"], p.get("track_dev", 0.0)), K["pass"])
```

and `BACKTEST` from the next `props_by_season.py` run (this frame: receiving 19.13 / 18.14, rushing 17.67 / 16.96,
passing 56.56 / 56.04). Optionally carry `track_dev` onto the card rows beside `ypt_shrunk` / `ypc_shrunk` /
`ypd_shrunk` as a reading.

**experiments/props_by_season.py**: add the function (before `build`) and, in `build`, the prior:

```python
def track_dev(kind, f):
    """Round 19 (experiments/props_tracking.py): his NGS signal (props.TRACK) as of before each game, decayed like the
    usage (DECAY per row, FADE's season factor per season boundary), shrunk toward the league's as of the game (last
    season and this season before the week) with k, minus the league's; 0 without a league reading."""
    from nflmodel.features import RAW
    path, col, wcol, total, k, _, _ = PR.TRACK[kind]; sf = PR.FADE.get(kind, (1.0, 1.0))[0]
    x = pd.read_parquet(RAW / path); x = x[(x.week > 0) & (x.season_type == "REG") & x.player_gsis_id.notna() & x[col].notna()].drop_duplicates(["player_gsis_id", "season", "week"])
    x = x.assign(pid=x.player_gsis_id, v=(x[col] if total else x[col] * x[wcol]).astype(float), w=x[wcol].astype(float)).sort_values(["pid", "season", "week"]).reset_index(drop=True)
    v, w, pid, sn = x.v.values, x.w.values, x.pid.values, x.season.values; sv, sw = np.zeros(len(x)), np.zeros(len(x)); a = b = 0.0
    for i in range(len(x)):
        if i == 0 or pid[i] != pid[i - 1]: a = b = 0.0
        elif sn[i] != sn[i - 1]: a, b = a * sf, b * sf
        a, b = PR.DECAY * a + v[i], PR.DECAY * b + w[i]; sv[i], sw[i] = a, b
    st = pd.DataFrame({"pid": pid, "s_season": sn, "key": sn.astype("int64") * 100 + x.week.values.astype("int64"), "sv": sv, "sw": sw})
    q = pd.DataFrame({"pid": f.pid.values, "season": f.season.values, "key": f.season.values.astype("int64") * 100 + f.week.values.astype("int64"), "_i": np.arange(len(f))})
    m = pd.merge_asof(q.sort_values("key"), st.sort_values("key"), on="key", by="pid", allow_exact_matches=False).sort_values("_i")
    fac = np.where(m.s_season.notna() & (m.s_season < m.season), sf, 1.0); Sv, Sw = m.sv.fillna(0.0).values * fac, m.sw.fillna(0.0).values * fac
    g = x.groupby(["season", "week"])[["v", "w"]].sum().reset_index(); ref = np.full(len(f), np.nan)
    for s_ in np.unique(f.season.values):
        gp, gs = g[g.season == s_ - 1], g[g.season == s_]; cv, cw = np.r_[0.0, gs.v.cumsum().values], np.r_[0.0, gs.w.cumsum().values]
        mr = f.season.values == s_; j = np.searchsorted(gs.week.values, f.week.values[mr], side="left"); den = gp.w.sum() + cw[j]
        ref[mr] = np.where(den > 0, (gp.v.sum() + cv[j]) / np.where(den > 0, den, 1.0), np.nan)
    return np.where(np.isnan(ref), 0.0, (Sv + k * np.nan_to_num(ref)) / (Sw + k) - np.nan_to_num(ref))
```

```python
# in build(kind), replacing the mean_line line:
prior = PR.track_prior(kind, lg, track_dev(kind, f))   # round 19: the tracking signal moves the prior (props.TRACK)
f["mean_line"] = adj(f.vol * (f.yds + K * prior) / (f.n + K)) * wind
```

