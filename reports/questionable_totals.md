# Questionable players in the totals equation only (2 Oct 2026)

Script: `experiments/questionable_totals.py`. Nothing in the live model changes with this study.

## Pre-registered (written before any result)

**Claim.** Questionable players priced at the chance they sit (injury_retest's Q2 input) lower the total miss when they
enter the totals equation only, with the points equations, and so the spread, untouched.

**Snooping caveat.** This is not a fresh idea. In `experiments/injury_retest.py` (1 Oct 2026) Q2 was one of five
variants; it lowered the team points miss on every window and helped the totals flag on all three, but cost the spread
flag. Putting it into the totals equation only was chosen after seeing that result, so a pass here is weaker evidence
than a pre-registered first try: it counts as the sixth and seventh variants of the injury idea (Q1, Q2, L1, D1, C, then
T1, T2 here), all on the same 2015-2025 games.

**Input (unchanged from injury_retest's Q2, rebuilt by `experiments.injury_retest.build` on main's current data).** For each
team-game, every player listed Questionable (not Out, Doubtful or off the active roster) on the league's injury report
for that week counts as out times his chance to sit: the share of earlier Questionable players who took no snap (snap
counts, by id), by position group and the week's last practice status, from seasons before the one priced (2013 on),
each cell shrunk toward its practice status's rate with 20 listings. Known at bet time: the injury report and practice
statuses of the week, the snap shares of the team's last game, and rates from earlier seasons. No line, split or price.
Pieces per team-game: `q1_skill` (Questionable RB / WR / TE's skill value out times the chance), `q2_off` (every
Questionable player's last-game offensive snap share times the chance), `q2_def` (the same for defensive snaps),
`q2_qb` (the chance to sit when last game's starting QB is Questionable).

**Variants** (each refit walk-forward 2015-2025 on main's code: weekly refit, forecast weather for played games, the
totals equation `model.TOTAL_FEATS` plus wind points; the points equations, `model.FEATS`, untouched):

- **T1.** Three new totals inputs, each summed over both teams: `q_skill_sum` (q1_skill), `q_off_sum` (q2_off),
  `q_def_sum` (q2_def). Offense and defense are kept apart because they should push the total opposite ways.
- **T2.** T1, plus the QB part: the totals equation's `qb_out_sum` takes each team's max(qb_out, q2_qb) instead of qb_out.
  T2 is Q2 as tested, moved to the totals equation; it is the primary variant.

**Pass bar** (`nflmodel.study_gate.gate`, reports/round3_rule.md): total miss lower on 2015-18 (untouched), 2019-22
(tuning) and 2023-25 (held out); no bet cost on any window for the spread flag (edge 4+), the totals flag (55%+ under)
and the wind under (10+ mph), weeks 1-17; beats its placebo: the variant's new values (all four pieces of a team-game
together) shuffled among the team-games of each season, 50 draws, fixed seed, the real gain larger in at least 45 of 50
on every window. The placebo runs for a variant that passes parts 1 and 2. If both pass every part, T2 is the candidate;
T1 only if T2 fails. A pass is a model-input addition: it goes to Matt for his yes, not live.

## Results

Rebuilt inputs against the live ones: skill value out, rebuilt vs live: share within 0.001 100.00%; offensive snaps out, rebuilt vs live: share within 0.01 98.31%.

Team-games with a Questionable input, by season (regular season):

| Season | Questionable listed | Team-games with a value | Starting QB Questionable | Mean offense snaps | Mean defense snaps |
|---|---|---|---|---|---|
| 2015 | 978 | 336 | 11 | 0.170 | 0.156 |
| 2016 | 1745 | 426 | 13 | 0.335 | 0.285 |
| 2017 | 1470 | 404 | 12 | 0.230 | 0.208 |
| 2018 | 1281 | 372 | 13 | 0.192 | 0.189 |
| 2019 | 1267 | 362 | 15 | 0.173 | 0.176 |
| 2020 | 1383 | 389 | 15 | 0.202 | 0.195 |
| 2021 | 1433 | 420 | 16 | 0.188 | 0.221 |
| 2022 | 1452 | 429 | 23 | 0.212 | 0.191 |
| 2023 | 1458 | 423 | 22 | 0.202 | 0.185 |
| 2024 | 1350 | 384 | 14 | 0.184 | 0.176 |
| 2025 | 1145 | 359 | 12 | 0.150 | 0.125 |

Each variant refit walk-forward 2015-2025 (regular season scored). Total miss is the yardstick; flags at the live rules (weeks 1-17).

| Variant | Window | Total miss | Team miss | Margin miss | Spread flag | Totals flag | Wind under |
|---|---|---|---|---|---|---|---|
| base | 2015-18 | 10.7507 | 7.4046 | 9.9508 | 69-55 | 132-117 | 24-20 |
| base | 2019-22 | 10.5161 | 7.3645 | 10.0109 | 77-48 | 190-146 | 143-88 |
| base | 2023-25 | 10.1029 | 7.2345 | 9.9061 | 37-20 | 82-59 | 77-52 |
| T1 | 2015-18 | 10.8106 | 7.4265 | 9.9508 | 69-55 | 148-133 | 24-20 |
| T1 | 2019-22 | 10.4969 | 7.3608 | 10.0109 | 77-48 | 203-155 | 143-88 |
| T1 | 2023-25 | 10.0999 | 7.2330 | 9.9061 | 37-20 | 90-61 | 77-52 |
| T2 | 2015-18 | 10.7999 | 7.4220 | 9.9508 | 69-55 | 157-126 | 24-20 |
| T2 | 2019-22 | 10.4877 | 7.3534 | 10.0109 | 77-48 | 213-158 | 143-88 |
| T2 | 2023-25 | 10.0883 | 7.2293 | 9.9061 | 37-20 | 89-60 | 77-52 |

Total miss by season (descriptive, added after the results to show where 2015-18 moved; not a variant):

| Season | base | T1 | T2 |
|---|---|---|---|
| 2015 | 10.4762 | 10.5602 | 10.5676 |
| 2016 | 10.2765 | 10.3868 | 10.3306 |
| 2017 | 11.3622 | 11.4256 | 11.4362 |
| 2018 | 10.8877 | 10.8697 | 10.8651 |
| 2019 | 10.6900 | 10.6895 | 10.7052 |
| 2020 | 10.3291 | 10.3155 | 10.2905 |
| 2021 | 10.6570 | 10.6259 | 10.6099 |
| 2022 | 10.3870 | 10.3567 | 10.3459 |
| 2023 | 10.3517 | 10.3223 | 10.3063 |
| 2024 | 9.6068 | 9.6040 | 9.5689 |
| 2025 | 10.3502 | 10.3735 | 10.3896 |

## Gate, variant T1 (parts 1 and 2; the placebo runs only for a variant that passes them)

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | NO | miss 10.7507 -> 10.8106 |
| better on 2019-22 | yes | miss 10.5161 -> 10.4969 |
| better on 2023-25 | yes | miss 10.1029 -> 10.0999 |
| no bet cost: spread flag, 2015-18 | yes | 69-55 -> 69-55 |
| no bet cost: totals flag, 2015-18 | yes | 132-117 -> 148-133 |
| no bet cost: wind under, 2015-18 | yes | 24-20 -> 24-20 |
| no bet cost: spread flag, 2019-22 | yes | 77-48 -> 77-48 |
| no bet cost: totals flag, 2019-22 | yes | 190-146 -> 203-155 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 37-20 -> 37-20 |
| no bet cost: totals flag, 2023-25 | yes | 82-59 -> 90-61 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |

Gate: FAIL (11 of 12); no market input and no look-ahead checked by the model-auditor agent

## Gate, variant T2 (parts 1 and 2; the placebo runs only for a variant that passes them)

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | NO | miss 10.7507 -> 10.7999 |
| better on 2019-22 | yes | miss 10.5161 -> 10.4877 |
| better on 2023-25 | yes | miss 10.1029 -> 10.0883 |
| no bet cost: spread flag, 2015-18 | yes | 69-55 -> 69-55 |
| no bet cost: totals flag, 2015-18 | yes | 132-117 -> 157-126 |
| no bet cost: wind under, 2015-18 | yes | 24-20 -> 24-20 |
| no bet cost: spread flag, 2019-22 | yes | 77-48 -> 77-48 |
| no bet cost: totals flag, 2019-22 | yes | 190-146 -> 213-158 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 37-20 -> 37-20 |
| no bet cost: totals flag, 2023-25 | yes | 82-59 -> 89-60 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |

Gate: FAIL (11 of 12); no market input and no look-ahead checked by the model-auditor agent

## Placebo

Not run: neither variant passes parts 1 and 2 of the gate (the pre-registered rule runs the 50-draw placebo only then).

## Variants counted

Seven variants of the Questionable / injury idea on the same 2015-2025 games: Q1, Q2, L1, D1 and C in injury_retest
(1 Oct 2026), T1 and T2 here. T1 and T2 were chosen after seeing Q2's result in injury_retest (snooping). Neither was
picked on 2023-25.

## Verdict

Fails; nothing adopted, the totals equation stays as it is. No model-auditor run: the auditor is for a result put to
Matt for adoption, and this one fails part 1. The base reproduces main's honest backtest exactly (total miss 10.7507 /
10.5161 / 10.1029, as in reports/forecast_weather_backtest.md), and the spread flag and margin miss are unchanged by
construction (the points equations are untouched).

- **T2 (primary: Q2 in the totals equation, QB included)** lowers the total miss on 2019-22 (10.5161 -> 10.4877) and
  2023-25 (10.1029 -> 10.0883) and adds net totals-flag wins on all three windows (132-117 -> 157-126, 190-146 ->
  213-158, 82-59 -> 89-60), but its total miss is worse on 2015-18 (10.7507 -> 10.7999). It fails part 1.
- **T1 (no QB part)** fails the same way, by more on 2015-18 (10.8106) and with less gain on the other two windows.
- By season, T2 is worse in 2015, 2016, 2017, 2019 and 2025 and better in 2018 and 2020-24. The 2015-17 fits learn the
  input from 2013-16, when "Probable" still existed and Questionable players sat more often (39-44% against 26-36%
  after), and 2013 carries no value (no earlier rates), so the early fits see the input on few, different seasons.
- The totals flag bets more games with the input (283 against 249 on 2015-18, 371 against 336 on 2019-22): more wins,
  and more losses on 2015-18 and 2019-22.
- The rebuilt offensive snaps out matches the live input on 98.31% of team-games (99.99% in injury_retest, before the
  2 Oct data fixes); the variants add only the Questionable pieces to the live inputs, so this does not touch the base.
