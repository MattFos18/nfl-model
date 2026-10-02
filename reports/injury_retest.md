# Injuries re-tested: Questionable players, linemen, defenders (1 Oct 2026)

Script: `experiments/injury_retest.py`. Nothing in the live model changes with this study.

## Pre-registered variants (written before any result)

Matt asked for better injury accuracy on Questionable players, offensive linemen and any other player who raises a flag.
Prior results, stated plainly: Questionable at guessed weights (0.3 / 0.5, plus 0.7 / 0.8 for no practice) in the skill
value out was a shade better on 2019-22 and worse held out (23 Sep, `experiments/questionable.py`); the linemen's on/off
value out and the defenders' value out were not adopted on 22 Sep (`experiments/positions.py`, linemen then matched by
name: 579 games to a namesake, 1,411 dropped); the defenders' value out was re-tested on 24 Sep on an interim value
(`experiments/def_value_out.py`, worse on both windows) before the per-group recipes (corners on coverage per target)
were adopted. The linemen's value out has not been tested on the fixed ids and unit rating, nor the defenders' on the
current recipes.

Each variant is refit walk-forward 2015-2025 exactly as the live model (`model.walk_forward`, ridge 10, weekly refit),
and scored through `nflmodel.study_gate.gate()`: team points miss on 2015-18, 2019-22 and 2023-25, with the live spread
flag (edge 4) and totals flag (55% under) records for the no-bet-cost part.

- **Q1.** A Questionable RB, WR or TE (not Out, Doubtful or off the active roster) counts as out times the chance he
  sits: the share of earlier Questionable players who took no snap (snap counts, by id), by position group and the
  week's last practice status (did not practice, limited, full, none), from seasons before the one priced (2013 on);
  each cell shrunk toward its practice status's rate with 20 listings. Added to `skill_out_value` (own and opponent)
  and to `off_snap_out` (his last-game snap share times the chance).
- **Q2.** Q1 at every position: `off_snap_out` and the opponent's `def_snap_out` take every Questionable player's
  last-game snap share times his chance to sit, and `qb_out` becomes that chance when last game's starting QB is
  Questionable (the QB is in the model only through `qb_out`; feasible, so included).
- **L1.** Own and opponent offensive linemen's value out, added: for linemen Out, Doubtful or off the roster, (unit
  rating minus replacement) x snap share over his last eight games, by id (`ol_games`, as on the Players tab).
- **D1.** Opponent defenders' value out, added: the same for defenders, with each group's current recipe
  (`positions.role_rates`). Own defenders out is the same column seen from the other team's row, so not added.
- **C.** The variants that pass parts 1 and 2, together; if fewer than two pass, the best two by summed gain.

The OL unit rating and the defender recipes read PFR charting (2018 on), so L1 and D1 are zero before 2018 and the
2015-18 window can only move through 2018. A placebo (50 within-season shuffles of the variant's new values) runs only
for a variant that passes parts 1 and 2.

## Results

Rebuilt inputs against the live ones: skill value out, rebuilt vs live: share within 0.001 100.00%; offensive snaps out, rebuilt vs live: share within 0.01 99.99%.

Chance a Questionable player sat (took no snap), 2013-2025 listings not otherwise out, by group and last practice:

| Group | Practice | Listings | Sat |
|---|---|---|---|
| DB | dnp | 600 | 62% |
| DB | full | 739 | 17% |
| DB | limited | 2370 | 35% |
| DB | none | 36 | 39% |
| DL | dnp | 485 | 49% |
| DL | full | 471 | 14% |
| DL | limited | 1583 | 24% |
| LB | dnp | 352 | 52% |
| LB | full | 410 | 13% |
| LB | limited | 1535 | 28% |
| OL | dnp | 527 | 63% |
| OL | full | 507 | 20% |
| OL | limited | 1829 | 32% |
| OL | none | 32 | 41% |
| QB | dnp | 47 | 72% |
| QB | full | 69 | 33% |
| QB | limited | 251 | 57% |
| RB | dnp | 209 | 65% |
| RB | full | 257 | 23% |
| RB | limited | 909 | 33% |
| ST | dnp | 40 | 50% |
| ST | full | 48 | 21% |
| ST | limited | 117 | 17% |
| TE | dnp | 154 | 66% |
| TE | full | 223 | 15% |
| TE | limited | 643 | 30% |
| WR | dnp | 411 | 52% |
| WR | full | 375 | 13% |
| WR | limited | 1589 | 28% |

Team-games with a non-zero input, by season (Questionable players listed; Q1 skill value; linemen out; defenders out):

| Season | Questionable listed | Q1 skill rows | Linemen rows | Defender rows |
|---|---|---|---|---|
| 2013 | 0 | 0 | 0 | 0 |
| 2014 | 965 | 210 | 0 | 0 |
| 2015 | 978 | 206 | 0 | 0 |
| 2016 | 1745 | 303 | 0 | 0 |
| 2017 | 1470 | 249 | 0 | 0 |
| 2018 | 1281 | 232 | 302 | 412 |
| 2019 | 1267 | 224 | 350 | 499 |
| 2020 | 1383 | 246 | 392 | 504 |
| 2021 | 1433 | 263 | 478 | 537 |
| 2022 | 1452 | 281 | 468 | 538 |
| 2023 | 1458 | 280 | 424 | 535 |
| 2024 | 1350 | 243 | 463 | 541 |
| 2025 | 1145 | 210 | 479 | 538 |

Each variant refit walk-forward 2015-2025. Team points miss is the yardstick; flags at the live rules (weeks 1-17).

| Variant | Window | Team miss | Total miss | Margin miss | Spread flag | Totals flag |
|---|---|---|---|---|---|---|
| base | 2015-18 | 7.4082 | 10.7382 | 9.9491 | 68-55 | 137-127 |
| base | 2019-22 | 7.3426 | 10.4934 | 10.0204 | 80-51 | 202-146 |
| base | 2023-25 | 7.2439 | 10.1081 | 9.9041 | 40-21 | 98-73 |
| Q1 | 2015-18 | 7.4134 | 10.7382 | 9.9665 | 67-56 | 137-127 |
| Q1 | 2019-22 | 7.3392 | 10.4934 | 10.0023 | 76-46 | 202-146 |
| Q1 | 2023-25 | 7.2472 | 10.1081 | 9.9174 | 40-23 | 98-73 |
| Q2 | 2015-18 | 7.4043 | 10.7315 | 9.9505 | 67-58 | 141-125 |
| Q2 | 2019-22 | 7.3270 | 10.4732 | 9.9998 | 67-46 | 208-145 |
| Q2 | 2023-25 | 7.2394 | 10.1001 | 9.8996 | 35-24 | 98-70 |
| L1 | 2015-18 | 7.4272 | 10.7382 | 9.9919 | 64-60 | 137-127 |
| L1 | 2019-22 | 7.3406 | 10.4934 | 10.0197 | 79-47 | 202-146 |
| L1 | 2023-25 | 7.2471 | 10.1081 | 9.9089 | 40-21 | 98-73 |
| D1 | 2015-18 | 7.4119 | 10.7382 | 9.9804 | 74-57 | 137-127 |
| D1 | 2019-22 | 7.3372 | 10.4934 | 10.0127 | 77-49 | 202-146 |
| D1 | 2023-25 | 7.2423 | 10.1081 | 9.9016 | 40-20 | 98-73 |
| C (Q2+D1) | 2015-18 | 7.4080 | 10.7315 | 9.9823 | 73-58 | 141-125 |
| C (Q2+D1) | 2019-22 | 7.3214 | 10.4732 | 9.9961 | 75-50 | 208-145 |
| C (Q2+D1) | 2023-25 | 7.2371 | 10.1001 | 9.8906 | 35-24 | 98-70 |

Variant C combines fewer than two pass parts 1 and 2: the best two by summed gain.

## Gate, variant Q1 (parts 1 and 2; the placebo runs only for a variant that passes them)

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | NO | miss 7.4082 -> 7.4134 |
| better on 2019-22 | yes | miss 7.3426 -> 7.3392 |
| better on 2023-25 | NO | miss 7.2439 -> 7.2472 |
| no bet cost: spread flag, 2015-18 | NO | 68-55 -> 67-56 |
| no bet cost: totals flag, 2015-18 | yes | 137-127 -> 137-127 |
| no bet cost: spread flag, 2019-22 | yes | 80-51 -> 76-46 |
| no bet cost: totals flag, 2019-22 | yes | 202-146 -> 202-146 |
| no bet cost: spread flag, 2023-25 | NO | 40-21 -> 40-23 |
| no bet cost: totals flag, 2023-25 | yes | 98-73 -> 98-73 |

Gate: FAIL (5 of 9); no market input and no look-ahead checked by the model-auditor agent

## Gate, variant Q2 (parts 1 and 2; the placebo runs only for a variant that passes them)

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | yes | miss 7.4082 -> 7.4043 |
| better on 2019-22 | yes | miss 7.3426 -> 7.3270 |
| better on 2023-25 | yes | miss 7.2439 -> 7.2394 |
| no bet cost: spread flag, 2015-18 | NO | 68-55 -> 67-58 |
| no bet cost: totals flag, 2015-18 | yes | 137-127 -> 141-125 |
| no bet cost: spread flag, 2019-22 | NO | 80-51 -> 67-46 |
| no bet cost: totals flag, 2019-22 | yes | 202-146 -> 208-145 |
| no bet cost: spread flag, 2023-25 | NO | 40-21 -> 35-24 |
| no bet cost: totals flag, 2023-25 | yes | 98-73 -> 98-70 |

Gate: FAIL (6 of 9); no market input and no look-ahead checked by the model-auditor agent

## Gate, variant L1 (parts 1 and 2; the placebo runs only for a variant that passes them)

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | NO | miss 7.4082 -> 7.4272 |
| better on 2019-22 | yes | miss 7.3426 -> 7.3406 |
| better on 2023-25 | NO | miss 7.2439 -> 7.2471 |
| no bet cost: spread flag, 2015-18 | NO | 68-55 -> 64-60 |
| no bet cost: totals flag, 2015-18 | yes | 137-127 -> 137-127 |
| no bet cost: spread flag, 2019-22 | yes | 80-51 -> 79-47 |
| no bet cost: totals flag, 2019-22 | yes | 202-146 -> 202-146 |
| no bet cost: spread flag, 2023-25 | yes | 40-21 -> 40-21 |
| no bet cost: totals flag, 2023-25 | yes | 98-73 -> 98-73 |

Gate: FAIL (6 of 9); no market input and no look-ahead checked by the model-auditor agent

## Gate, variant D1 (parts 1 and 2; the placebo runs only for a variant that passes them)

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | NO | miss 7.4082 -> 7.4119 |
| better on 2019-22 | yes | miss 7.3426 -> 7.3372 |
| better on 2023-25 | yes | miss 7.2439 -> 7.2423 |
| no bet cost: spread flag, 2015-18 | yes | 68-55 -> 74-57 |
| no bet cost: totals flag, 2015-18 | yes | 137-127 -> 137-127 |
| no bet cost: spread flag, 2019-22 | NO | 80-51 -> 77-49 |
| no bet cost: totals flag, 2019-22 | yes | 202-146 -> 202-146 |
| no bet cost: spread flag, 2023-25 | yes | 40-21 -> 40-20 |
| no bet cost: totals flag, 2023-25 | yes | 98-73 -> 98-73 |

Gate: FAIL (7 of 9); no market input and no look-ahead checked by the model-auditor agent

## Gate, variant C (Q2+D1) (parts 1 and 2; the placebo runs only for a variant that passes them)

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | yes | miss 7.4082 -> 7.4080 |
| better on 2019-22 | yes | miss 7.3426 -> 7.3214 |
| better on 2023-25 | yes | miss 7.2439 -> 7.2371 |
| no bet cost: spread flag, 2015-18 | yes | 68-55 -> 73-58 |
| no bet cost: totals flag, 2015-18 | yes | 137-127 -> 141-125 |
| no bet cost: spread flag, 2019-22 | NO | 80-51 -> 75-50 |
| no bet cost: totals flag, 2019-22 | yes | 202-146 -> 208-145 |
| no bet cost: spread flag, 2023-25 | NO | 40-21 -> 35-24 |
| no bet cost: totals flag, 2023-25 | yes | 98-73 -> 98-70 |

Gate: FAIL (7 of 9); no market input and no look-ahead checked by the model-auditor agent

## Placebo

Not run: no variant passes parts 1 and 2 of the gate (the pre-registered rule runs the 50-draw placebo only then).

## Verdict

Nothing adopted; the live injury inputs stay as they are.

- **Q2 (Questionable at their measured chance to sit, every position, QB included)** lowers the team points miss on all
  three windows (7.4082 -> 7.4043, 7.3426 -> 7.3270, 7.2439 -> 7.2394) and helps the totals flag on all three
  (141-125, 208-145, 98-70), but the spread flag loses net wins on every window (68-55 -> 67-58, 80-51 -> 67-46,
  40-21 -> 35-24). It fails the no-bet-cost part.
- **Q1 (skill players only)** is better on 2019-22 only, the same pattern as the guessed weights on 23 Sep.
- **L1 (linemen's value out, fixed ids)** is better on 2019-22 only and costs the 2015-18 spread flag (68-55 -> 64-60).
- **D1 (opponent defenders' value out, current recipes)** is better on 2019-22 and 2023-25, worse on 2015-18 (which here
  is 2018 alone), and costs the 2019-22 spread flag (80-51 -> 77-49).
- **C (Q2 + D1)** is better on all three windows (7.4080 / 7.3214 / 7.2371) but costs the spread flag on 2019-22 and
  2023-25.

Data notes: the rebuilt base reproduces the live skill value out (100%) and offensive snaps out (99.99%), so the
variants differ from the live model only by what they add. Snap counts start in 2013 (the 2012 file is empty), so the
first sit rates (for 2015) come from 2013-14 listings. "Probable" existed until 2015: Questionable players sat 39-44% of
the time in 2013-15 and 26-36% from 2016 on, so 2016's rates (from 2013-15) overstate the chance to sit. A Questionable
QB sat 57% of the time after a limited week and 72% after no practice. The linemen's unit rating and the
defender recipes read PFR charting, 2018 on.
