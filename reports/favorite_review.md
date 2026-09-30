# Why the model's favourites lose at 4+ and 5+, and whether a fix to the model helps (30 Sep 2026)

Research only: nothing on the site or in the picks changes. Script: `experiments/favorite_review.py`. Case list: `reports/favorite_review.csv`, with every favourite bet at 3+ and every dog bet at 4+, 2015-2026. Other tables: `favorite_review_patterns.csv`, `favorite_review_fixes.csv` and `favorite_review_rules.csv`.

The bets are the live flag: the model's side at 4+ points off the closing line, weeks 1-17, pushes out, -110. "Favourite" means our side is the market favourite. The years are 2015-25. 2026 has no favourite bets yet; the dogs are 1-2.

## Headline

**Mostly, the favourites are not failing. There are too few of them to tell.** At the live 4+ cut they are 33-29 and beat the close by **+2.3 points a bet**. The dogs beat it by +2.5. The win-rate gap (53% against 61%) is within chance: Fisher p 0.25, and 0.15 when the favourite label is shuffled within each season.

"Worse as the edge grows" does not hold up either:
- Inside the 3+ favourite bets, the win rate moves -0.5% per point of edge (se 3.7%).
- The worst band is 3-4 points (33-45). The best is 4-5 (24-13).
- The 5+ cell (9-16) is 25 bets, and in points it breaks even with the close (+0.0 ± 2.9).
- The win-rate gap is significant only at the 3.5 and 5 cuts (p about 0.01), not at 3, 4 or 6. No cut shows it in points (|t| < 1.9).

Two readings explain most of the gap that is there. Neither is peculiar to favourites.

1. **Favourite bets are home teams, and the flag's home sides lose on both sides of the line.**
   - 79% of favourite bets are at home, against 55% of dog bets.
   - At 4+: home favourites 24-25, road favourites 9-4, home dogs 76-63, road dogs 79-35.
   - The model leans 0.26 / 0.40 / 0.40 points more to the home side than the close on the three windows.
   - Home field was settled on 27 and 30 Sep: one league number stays. An offset fit here on past results fails too (below).
2. **The boosted trees do not back the edge.**
   - 37% of favourite bets have the trees' own edge under 4, against 29% of dog bets.
   - Those favourites went 8-15; the rest went 25-14 (placebo 0.04).
   - The dogs show the same split: 39-34 against 116-64 (placebo 0.04).
   - The six ridges extrapolate a line. On favourite bets at 3+ the trees sit 0.47 points short of the ridge on average; on dog bets they sit +0.19 points beyond it.

A weaker third: **injury-driven favourites.**
- 34% of favourite bets get 1.5+ points from the injury and QB-out inputs, against 15% of dogs.
- Those favourites went 9-12, against 24-17 (placebo 0.08; at 3+ the placebo is 0.25). The dogs show nothing.

Home side, trees under 4 and injury pull together take the favourite penalty from -8.0 (7.0) to -2.4 (7.2) win-rate points (se in brackets).

**No model fix works.** 17 walk-forward fixes to the model's number were scored under `reports/round3_rule.md`. Every parameter was fit on earlier seasons only.
- None lowers both the margin miss and the team-points miss on all three windows (0 pass rule 1).
- None passes the placebo: at best, 30 of 50 shuffled draws do as well.
- The market-free fix (shrink big margins toward zero) is the wrong direction. The model's number is already narrower than the line and than the results:
  - SD 5.56 against the line's 5.99.
  - Result = 1.07 × model.
  - At the top it is on the money: home by 9-12, model 10.3, result 10.5; home by 12+, model 14.3, result 15.2.
  - So there is no rating ceiling to cap. Shrinking costs miss on the windows it is fit on.

**Bet rules do not beat live on all three windows either.** Live is 68-55, +7.5u / 80-51, +23.9u / 40-21, +16.9u.
- Dogs 3.5+ with favourites at 4+: 85-68, +10.2u / 100-72, +20.8u / 55-31, +20.9u (loses 2019-22).
- Dogs 3.5+, no favourites: 67-51, +10.9u / 93-63, +23.7u / 47-28, +16.2u (loses 2019-22 and 2023-25, by under a unit each).
- Favourites at 5+: 54-47, +2.3u / 76-47, +24.3u / 34-20, +12.0u (loses 2015-18 and 2023-25).
- Favourites at 6+: 51-42, +4.8u / 74-43, +26.7u / 34-19, +13.1u (loses 2015-18 and 2023-25).
- No favourites at all: 50-38, +8.2u / 73-42, +26.8u / 32-18, +12.2u. It loses 4.7u on 2023-25, where favourites went 8-3.

**What to decide.**
- Keep the 4+ rule on both sides, and do not change the model.
- The dog shadow already tracks the alternative.
- If one watch item is wanted, log whether the trees also show 4+ on each flagged favourite. As a rule it earns 64-44, +15.6u / 80-48, +27.2u / 36-20, +14.0u. It was found by looking and loses on 2023-25, so it is a reading, not a rule.
- Revisit after 2026, with about 6 more favourite bets.

**Against earlier findings**
- **Confirmed:**
  - The sweep and spread research (30 Sep): no favourite/dog rule beats live on every window, and road dogs are the strong cell.
  - The postmortem (29 Sep): the 1-point injury cap has no dose response. Here it worsens the margin miss on 2019-22 and 2023-25.
  - The situational round (29 Sep): the injury inputs earn their place.
  - Home field (27 and 30 Sep): one number stays.
  - Season odds (23 Sep): shrinking margins does not hold across windows. Here it worsens the margin miss wherever it is fit.
- **Refined:**
  - The sweep's "the model's favourites never earn their keep" is true of units at 5+. At 4+, though, they beat the close by as many points as the dogs.
  - The postmortem's "skip when the trees disagree" (side flipped) has a cousin: trees under 4. It sorts dogs as well as favourites, so it is not a favourite problem.
- **Overturned:** the premise that favourites get worse as the edge grows. There is no trend inside the favourite bets.

## 1. The gap, cut by cut

|   cut | favourites   |   fav win % | dogs    |   dog win % |   Fisher p |   placebo p (fav label shuffled in season) |   fav pts vs close |   dog pts vs close |   t (points) |
|------:|:-------------|------------:|:--------|------------:|-----------:|-------------------------------------------:|-------------------:|-------------------:|-------------:|
|   3   | 66-74        |        47.1 | 264-217 |        54.9 |      0.124 |                                      0.069 |               0.4  |               1.33 |        -0.73 |
|   3.5 | 44-55        |        44.4 | 207-142 |        59.3 |      0.011 |                                      0.011 |              -0.73 |               2.11 |        -1.86 |
|   4   | 33-29        |        53.2 | 155-98  |        61.3 |      0.252 |                                      0.151 |               2.31 |               2.53 |        -0.12 |
|   5   | 9-16         |        36   | 73-42   |        63.5 |      0.014 |                                      0.001 |               0    |               2.96 |        -0.93 |
|   6   | 4-6          |        40   | 26-20   |        56.5 |      0.487 |                                      0.231 |               3.65 |               1.7  |         0.43 |

Points vs close is the mean of (final margin minus the line) toward our side. The t compares favourites with dogs.

## 2. What drives a favourite edge, and what each part is worth

Contributions are coef × (home input − away input) in the ridge that priced the game; the training mean cancels. They rebuild the ridge spread to 1e-14. They are signed toward our side.

The worth columns come from regressions over every game, 2015-25:
- **Worth vs the result:** the result regressed on the parts. 1 means the part earns its face value.
- **Worth beyond the close:** the result minus the line, regressed on the parts and the line. 0 means the line already has it.

| part                   |   pull toward our side, favourites 4+ |   dogs 4+ | worth vs the result, per point (se)   | worth beyond the close, per point (se)   |
|:-----------------------|--------------------------------------:|----------:|:--------------------------------------|:-----------------------------------------|
| QB                     |                                  2.25 |     -0.54 | 1.18 (0.12)                           | 0.29 (0.16)                              |
| ratings                |                                  3.53 |     -0.94 | 1.02 (0.10)                           | 0.08 (0.15)                              |
| injuries               |                                  1.18 |      0.39 | 0.83 (0.23)                           | 0.40 (0.24)                              |
| offseason turnover     |                                  0.76 |      0.04 | 1.34 (0.37)                           | 0.96 (0.36)                              |
| weather                |                                  0.07 |      0    | 1.43 (0.94)                           | 1.18 (0.93)                              |
| out of the race        |                                  0.55 |     -0    | 0.95 (0.37)                           | 0.46 (0.37)                              |
| six other models' pull |                                 -0    |      0.03 | 1.48 (0.68)                           | 1.04 (0.67)                              |

- A favourite edge is the model's number going past the line: 9.6 against 4.4 on average at 4+. Ratings (+3.5), QB (+2.3), home (+1.2), injuries (+1.2) and offseason turnover (+0.8) carry it.
- A dog edge is mostly the line being wider than the model: the model says -0.8, the line -6.1.
- Every part is worth about its face value against the result. Injuries are the lowest at 0.83.
- The ratings part adds nothing beyond the close (0.08). Across every game the line itself runs -0.15 (0.10) per point too far.
- Plugging the favourites' average parts into that regression predicts them to beat the close by more than the dogs, not less. So no part is over-weighted in a way that singles favourites out.

The model's number against results (every game, weeks 1-17, 2015-25). It is not over-extended at the top:

| model spread (home)   |   games |   model |   line |   result |
|:----------------------|--------:|--------:|-------:|---------:|
| (-30, -9]             |      56 |  -11.1  | -11.32 |    -9.23 |
| (-9, -6]              |     149 |   -7.26 |  -7.59 |    -8.79 |
| (-6, -3]              |     309 |   -4.4  |  -4.59 |    -5.49 |
| (-3, 0]               |     504 |   -1.42 |  -1.8  |    -2.44 |
| (0, 3]                |     578 |    1.58 |   1.32 |     0.98 |
| (3, 6]                |     529 |    4.46 |   4.31 |     4.42 |
| (6, 9]                |     390 |    7.43 |   6.85 |     7.39 |
| (9, 12]               |     199 |   10.27 |   9.59 |    10.49 |
| (12, 30]              |     101 |   14.34 |  13.54 |    15.2  |

## 3. Every candidate reason

Each row is a yes/no factor from our side's view:
- **Share:** how often the factor appears among favourite bets at 4+, dog bets at 4+ and every game.
- **Records:** with the factor and without it.
- **Placebo p:** the factor shuffled within season, 2000 draws. It is one-sided, testing that the factor hurts.

All columns, including the 3+ records and the dog placebos, are in `favorite_review_patterns.csv`.

| factor                                                 |   share fav 4+ |   share dog 4+ |   share all | fav 4+ with   | fav 4+ without   |   placebo p | fav 3+ with   | fav 3+ without   |   placebo p (3+) | dog 4+ with   | dog 4+ without   |   placebo p (dog) |
|:-------------------------------------------------------|---------------:|---------------:|------------:|:--------------|:-----------------|------------:|:--------------|:-----------------|-----------------:|:--------------|:-----------------|------------------:|
| Weeks 1-4                                              |          0.306 |          0.28  |       0.248 | 13-6          | 20-23            |      0.942  | 22-19         | 44-55            |           0.8165 | 48-23         | 107-75           |            0.9545 |
| Weeks 15-17                                            |          0.177 |          0.173 |       0.187 | 5-6           | 28-23            |      0.705  | 13-12         | 53-62            |           0.712  | 23-21         | 132-77           |            0.138  |
| Our side has 3 or fewer games this season              |          0.306 |          0.283 |       0.252 | 13-6          | 20-23            |      0.943  | 22-19         | 44-55            |           0.827  | 49-23         | 106-75           |            0.954  |
| Our side off a 14+ point win                           |          0.226 |          0.11  |       0.148 | 7-7           | 26-22            |      0.4475 | 15-20         | 51-54            |           0.376  | 22-6          | 133-92           |            0.9865 |
| Opponent off a 14+ point loss                          |          0.161 |          0.142 |       0.148 | 4-6           | 29-23            |      0.6115 | 12-19         | 54-55            |           0.344  | 24-12         | 131-86           |            0.7855 |
| Our side covered last week by 10+                      |          0.306 |          0.169 |       0.194 | 10-9          | 23-20            |      0.5115 | 18-18         | 48-56            |           0.7695 | 31-11         | 124-87           |            0.9465 |
| Injury inputs + QB-out pull 1.5+ pts our way           |          0.339 |          0.146 |       0.1   | 9-12          | 24-17            |      0.0815 | 17-26         | 49-48            |           0.2475 | 22-15         | 133-83           |            0.3415 |
| Opponent QB changed or listed out                      |          0.21  |          0.118 |       0.109 | 7-6           | 26-23            |      0.524  | 14-16         | 52-58            |           0.62   | 20-10         | 135-88           |            0.8895 |
| Our QB changed from last game                          |          0.113 |          0.228 |       0.127 | 3-4           | 30-25            |      0.6705 | 7-8           | 59-66            |           0.7235 | 34-24         | 121-74           |            0.2825 |
| Trees' edge 1+ pt below the ridge's                    |          0.387 |          0.315 |       0.333 | 8-16          | 25-13            |      0.031  | 26-37         | 40-37            |           0.0845 | 46-33         | 109-65           |            0.2405 |
| Trees' edge under 4                                    |          0.371 |          0.287 |       0.801 | 8-15          | 25-14            |      0.035  | 34-43         | 32-31            |           0.091  | 39-34         | 116-64           |            0.0445 |
| Seven models disagree (top third of SD)                |          0.419 |          0.335 |       0.334 | 12-14         | 21-15            |      0.273  | 22-31         | 44-43            |           0.332  | 52-33         | 103-65           |            0.494  |
| Line 7+ (either side)                                  |          0.21  |          0.354 |       0.281 | 8-5           | 25-24            |      0.5405 | 17-22         | 49-52            |           0.4975 | 49-41         | 106-57           |            0.0455 |
| Our side at home                                       |          0.79  |          0.551 |       0.559 | 24-25         | 9-4              |      0.09   | 54-65         | 12-9             |           0.282  | 76-63         | 79-35            |            0.0115 |
| Model has our side by 10+                              |          0.419 |          0     |       0.052 | 14-12         | 19-17            |      0.3675 | 24-29         | 42-45            |           0.4495 | 0-0           | 155-98           |          nan      |
| Rating pull 3+ pts our way                             |          0.581 |          0.063 |       0.161 | 20-16         | 13-13            |      0.794  | 38-44         | 28-30            |           0.3445 | 10-6          | 145-92           |            0.764  |
| QB pull 3+ pts our way                                 |          0.306 |          0.043 |       0.092 | 11-8          | 22-21            |      0.5925 | 23-20         | 43-54            |           0.8515 | 9-2           | 146-96           |            0.977  |
| Offseason-turnover pull 1+ pt our way                  |          0.306 |          0.079 |       0.09  | 11-8          | 22-21            |      0.5585 | 20-23         | 46-51            |           0.373  | 16-4          | 139-94           |            0.9895 |
| Out-of-the-race pull 1+ pt our way                     |          0.29  |          0.063 |       0.093 | 8-10          | 25-19            |      0.549  | 18-23         | 48-51            |           0.445  | 6-10          | 149-88           |            0.1095 |
| Close moved 1+ pt against us from the opener (2015-21) |          0.564 |          0.581 |       0.396 | 11-11         | 11-6             |      0.2485 | 20-22         | 20-24            |           0.635  | 57-40         | 46-24            |            0.202  |

Read:
- **Early season is not it.** Favourites are best in weeks 1-4 (13-6).
- **Off a big win is not it** (7-7).
- **Big lines are not it** (7+: 8-5).
- **Model disagreement is not it** (placebo 0.27).
- **A rating ceiling is not it.** The model has our side by 10+ in 14-12 of them.
- **QB changes and out-of-the-race are not it.**

The line move, late finishes and luck:

| bets          |    n | close moved against us (2015-21)   |   mean move toward us | record with 5:00 left (2016+)   | final record, same games   | lost / won in the last 5 min   |   luck toward us, pts (postmortem) | record with luck taken out   | our QB lost in the game   |
|:--------------|-----:|:-----------------------------------|----------------------:|:--------------------------------|:---------------------------|:-------------------------------|-----------------------------------:|:-----------------------------|:--------------------------|
| favourites 4+ |   62 | 72% of 39                          |                 -1.15 | 21-17                           | 21-19                      | 2 / 1                          |                               2.36 | 33-29                        | 3 of 62                   |
| favourites 5+ |   25 | 83% of 18                          |                 -2.03 | 8-9                             | 6-12                       | 2 / 0                          |                               1.48 | 11-14                        | 1 of 25                   |
| dogs 4+       |  254 | 72% of 167                         |                 -1.86 | 133-94                          | 138-92                     | 9 / 14                         |                              -1.72 | 179-75                       | 22 of 254                 |
| every game    | 2815 | 51% of 1747                        |                 -0.53 | 1240-1220                       | 1270-1225                  | 131 / 145                      |                             nan    |                              |                           |

- **The market moving against us is not favourite-specific.** For both favourites and dogs, the close moved against the model's side 72% of the time. That is the selection effect of measuring the edge at the close.
- **Late covers are not it.** With 5:00 left, favourites stood 21-17 against the line and finished 21-19 on the same games. The dogs went 133-94 to 138-92.
- **Luck ran for the favourites.** With luck removed they are still 33-29, while the dogs would be 179-75.

Home and road, favourite and dog, at 4+:

| our side        | 2015-18   | 2019-22   | 2023-25   | 2015-25   |   win % |
|:----------------|:----------|:----------|:----------|:----------|--------:|
| favourite, home | 10-15     | 6-7       | 8-3       | 24-25     |    49   |
| favourite, road | 8-2       | 1-2       | 0-0       | 9-4       |    69.2 |
| dog, home       | 20-27     | 39-25     | 17-11     | 76-63     |    54.7 |
| dog, road       | 30-11     | 34-17     | 15-7      | 79-35     |    69.3 |

A linear probability model on the 4+ bets shows how much of the favourite penalty the three readings take up. Each cell is the win-rate change in percentage points, with its se:

| controls                                              | favourite   | home side   | trees under 4   | injury pull 1.5+   |
|:------------------------------------------------------|:------------|:------------|:----------------|:-------------------|
| favourite                                             | -8.0 (7.0)  |             |                 |                    |
| favourite, home side                                  | -4.3 (7.0)  | -15.4 (5.7) |                 |                    |
| favourite, trees under 4                              | -6.8 (6.9)  |             | -15.0 (6.0)     |                    |
| favourite, injury pull 1.5+                           | -6.8 (7.1)  |             |                 | -6.3 (7.3)         |
| favourite, home side, trees under 4, injury pull 1.5+ | -2.4 (7.2)  | -13.9 (5.8) | -11.8 (6.1)     | -6.6 (7.3)         |

## 4. Fixes to the model's number (walk-forward, round-3 rule)

How the fixes were built and scored:
- Each fix changes the model's spread game by game. Parameters are chosen on earlier seasons' margin miss only. 2015 keeps the base number because pred_v3 has nothing before it.
- The scale, shrink, early-season, stacking, trees'-share and home fixes are exact: the blend is the average of the stored seven models.
- The injury, rating and QB caps move only the ridge's share of those inputs. The other six models carry them too, so these are approximate.
- The win chance is read on a normal curve with each fit's residual scale, for base and fix alike.
- Placebo: the fix's change to each game's number is shuffled within season (50 draws). Rule 3 needs the real gain to beat 45 of them on every window.
- Refits were not needed. The situational round (29 Sep) already refit the model without each injury input: dropping skill value costs, the snaps pair is mixed, and QB-out fails on log loss.

Changes against base. Miss below 0 is better. The flag cells are the fix's own records:

| fix                                                   |   margin miss 2015-18 |   team miss 2015-18 | flag 2015-18   | favourites 2015-18   | dogs 2015-18   |   margin miss 2019-22 |   team miss 2019-22 | flag 2019-22   | favourites 2019-22   | dogs 2019-22   |   margin miss 2023-25 |   team miss 2023-25 | flag 2023-25   | favourites 2023-25   | dogs 2023-25   | rule 1 (miss better on all 3)   | rule 2 (no bet or calibration cost)   |   placebo draws beating it (of 50) | passes   |
|:------------------------------------------------------|----------------------:|--------------------:|:---------------|:---------------------|:---------------|----------------------:|--------------------:|:---------------|:---------------------|:---------------|----------------------:|--------------------:|:---------------|:---------------------|:---------------|:--------------------------------|:--------------------------------------|-----------------------------------:|:---------|
| A. Scale the margin (k fit on past seasons)           |                 0.029 |               0.011 | 72-55, +11.5u  | 15-15                | 57-40          |                 0.001 |               0     | 80-51, +23.9u  | 7-9                  | 73-42          |                 0.009 |               0.008 | 38-23, +12.7u  | 5-3                  | 33-20          | False                           | False                                 |                                 50 | False    |
| B. Shrink margins beyond T toward zero (T, k fit)     |                 0.025 |               0.017 | 80-63, +10.7u  | 16-14                | 64-49          |                 0.041 |               0.014 | 87-58, +23.2u  | 5-9                  | 82-49          |                 0.005 |               0.008 | 38-24, +11.6u  | 5-2                  | 33-22          | False                           | False                                 |                                 50 | False    |
| B'. Shrink beyond 5 by 0.7 (fixed)                    |                -0.01  |               0.007 | 67-55, +6.5u   | 8-10                 | 59-45          |                 0.002 |               0.004 | 93-59, +28.1u  | 2-5                  | 91-54          |                 0.014 |               0.015 | 42-28, +11.2u  | 3-1                  | 39-27          | False                           | False                                 |                                 30 | False    |
| B'. Shrink beyond 7 by 0.5 (fixed)                    |                -0.016 |               0.005 | 71-54, +11.6u  | 10-9                 | 61-45          |                 0.034 |               0.012 | 96-61, +28.9u  | 3-6                  | 93-55          |                 0.015 |               0.014 | 47-30, +14.0u  | 4-2                  | 43-28          | False                           | False                                 |                                 44 | False    |
| C. Scale the injury + QB-out pull (k fit)             |                 0.004 |              -0.001 | 69-56, +7.4u   | 16-18                | 53-38          |                 0.007 |               0.005 | 74-46, +23.4u  | 7-9                  | 67-37          |                 0.002 |               0.008 | 39-21, +15.9u  | 8-4                  | 31-17          | False                           | False                                 |                                 41 | False    |
| C'. Cap the injury + QB-out pull at 1 pt (postmortem) |                -0.021 |              -0.006 | 59-45, +9.5u   | 10-9                 | 49-36          |                 0.007 |               0.004 | 80-46, +29.4u  | 7-9                  | 73-37          |                 0.01  |               0.009 | 42-22, +17.8u  | 9-3                  | 33-19          | False                           | False                                 |                                 34 | False    |
| D. Re-weight the model's parts on past results        |                 0.079 |               0.027 | 83-78, -2.8u   | 23-24                | 59-54          |                 0.032 |               0     | 77-60, +11.0u  | 17-25                | 60-35          |                 0.008 |               0.013 | 41-24, +14.6u  | 12-8                 | 29-16          | False                           | False                                 |                                 46 | False    |
| E. Stack the seven models (non-negative weights fit)  |                 0.024 |               0.008 | 73-62, +4.8u   | 17-18                | 56-44          |                 0.009 |               0.003 | 76-55, +15.5u  | 10-13                | 66-42          |                 0.004 |               0.002 | 41-25, +13.5u  | 10-7                 | 31-18          | False                           | False                                 |                                 49 | False    |
| G. Scale weeks 1-4 only (k fit)                       |                -0.008 |              -0     | 66-55, +5.5u   | 16-16                | 50-39          |                 0.003 |               0.005 | 78-55, +17.5u  | 5-9                  | 73-46          |                 0.007 |               0.007 | 39-20, +17.0u  | 7-2                  | 32-18          | False                           | False                                 |                                 37 | False    |
| H. Cap the rating pull at c (fit)                     |                -0.001 |              -0.001 | 69-56, +7.4u   | 18-17                | 51-39          |                 0.015 |               0.005 | 83-52, +25.8u  | 6-9                  | 77-43          |                 0     |               0     | 40-21, +16.9u  | 8-3                  | 32-18          | False                           | False                                 |                                 50 | False    |
| H'. Cap the QB pull at c (fit)                        |                 0.013 |               0.005 | 68-57, +5.3u   | 18-17                | 50-40          |                -0.002 |              -0     | 81-51, +24.9u  | 7-9                  | 74-42          |                -0.001 |              -0.003 | 39-21, +15.9u  | 7-3                  | 32-18          | False                           | False                                 |                                 48 | False    |
| I. Home-field offset (c fit)                          |                 0.013 |               0.003 | 72-56, +10.4u  | 16-16                | 56-40          |                -0.007 |              -0.003 | 72-49, +18.1u  | 7-8                  | 65-41          |                -0.007 |               0.008 | 36-25, +8.5u   | 6-4                  | 30-21          | False                           | False                                 |                                 50 | False    |
| F. Trees' share of the blend (w fit)                  |                 0.03  |               0.013 | 79-63, +9.7u   | 19-18                | 60-45          |                 0.005 |               0.002 | 82-51, +25.9u  | 8-9                  | 74-42          |                -0     |              -0.001 | 42-19, +21.1u  | 8-3                  | 34-16          | False                           | False                                 |                                 48 | False    |
| F'. Trees' share 0 (fixed; live 1/7 = 0.14)           |                 0.008 |               0.003 | 64-58, +0.2u   | 17-21                | 47-37          |                 0.004 |               0.002 | 78-55, +17.5u  | 8-12                 | 70-43          |                 0.01  |               0.002 | 40-24, +13.6u  | 8-6                  | 32-18          | False                           | False                                 |                                 48 | False    |
| F'. Trees' share 0.25 (fixed; live 1/7 = 0.14)        |                -0     |               0.001 | 70-56, +8.4u   | 17-18                | 53-38          |                 0.001 |              -0     | 82-51, +25.9u  | 9-9                  | 73-42          |                -0.003 |              -0.001 | 40-19, +19.1u  | 6-4                  | 34-15          | False                           | False                                 |                                 48 | False    |
| F'. Trees' share 0.33 (fixed; live 1/7 = 0.14)        |                 0.003 |               0.002 | 74-56, +12.4u  | 17-16                | 57-40          |                 0.005 |               0     | 86-56, +24.4u  | 10-10                | 76-46          |                -0.004 |              -0.001 | 38-21, +14.9u  | 6-5                  | 32-16          | False                           | False                                 |                                 39 | False    |
| F'. Trees' share 0.5 (fixed; live 1/7 = 0.14)         |                 0.015 |               0.009 | 82-66, +9.4u   | 21-19                | 61-47          |                 0.022 |               0.005 | 91-67, +17.3u  | 11-16                | 80-51          |                 0.007 |               0.002 | 41-23, +15.7u  | 7-4                  | 34-19          | False                           | False                                 |                                 43 | False    |

Base: margin miss 9.949 / 10.047 / 9.929; team miss 7.409 / 7.367 / 7.273.
Base flag: 68-55, +7.5u / 80-51, +23.9u / 40-21, +16.9u. Favourites 18-17 / 7-9 / 8-3; dogs 50-38 / 73-42 / 32-18.

What each fix does to favourites and dogs:
- **Shrinking (A, B):** fewer favourite bets and more dog bets. The margin miss gets worse where it is fit.
- **Injury scale or cap (C):** it barely touches the favourites (7-9 stays 7-9 on 2019-22).
- **Rating and QB caps (H):** they change little. The fitted caps mostly sit at 6 to 10 points, which few games reach.
- **Stacked or re-weighted parts (D, E):** they add favourite bets and lose them.
- **Trees' share (F):**
  - At a quarter it is the closest to neutral: miss -0.000 / +0.001 / -0.003, flag +1 / +2 / +2 net wins.
  - It still fails rule 1 on 2019-22, and 48 of 50 placebo draws match it.
- The per-season parameters are in the CSV.

## 5. Bet rules (the fallback)

How the rules are graded:
- Luck p is one-sided binomial against 52.38%, 2015-25.
- Placebo p is the share of 1000 random draws that earn at least as many units. Each draw takes the same number of bets per season from the rule's parent pool: every game at its lowest cut.

| rule                                             | 2015-18       | 2019-22        | 2023-25       | 2015-25         |   luck p |   placebo p | more units than live on all 3   |   fewest bets in a window |
|:-------------------------------------------------|:--------------|:---------------|:--------------|:----------------|---------:|------------:|:--------------------------------|--------------------------:|
| LIVE: 4+ either side                             | 68-55, +7.5u  | 80-51, +23.9u  | 40-21, +16.9u | 188-127, +48.3u |    0.005 |             |                                 |                        61 |
| Favourites 5+, dogs 4+                           | 54-47, +2.3u  | 76-47, +24.3u  | 34-20, +12.0u | 164-114, +38.6u |    0.016 |       0.85  | no                              |                        54 |
| Favourites 6+, dogs 4+                           | 51-42, +4.8u  | 74-43, +26.7u  | 34-19, +13.1u | 159-104, +44.6u |    0.005 |       0.356 | no                              |                        53 |
| No favourites, dogs 4+ (the dog shadow)          | 50-38, +8.2u  | 73-42, +26.8u  | 32-18, +12.2u | 155-98, +47.2u  |    0.003 |       0.161 | no                              |                        50 |
| Dogs 3.5+, favourites 4+                         | 85-68, +10.2u | 100-72, +20.8u | 55-31, +20.9u | 240-171, +51.9u |    0.008 |       0     | no                              |                        86 |
| Dogs 3.5+, favourites 5+                         | 71-60, +5.0u  | 96-68, +21.2u  | 49-30, +16.0u | 216-158, +42.2u |    0.021 |       0.105 | no                              |                        79 |
| Dogs 3.5+, favourites 6+                         | 68-55, +7.5u  | 94-64, +23.6u  | 49-29, +17.1u | 211-148, +48.2u |    0.009 |       0.021 | no                              |                        78 |
| Dogs 3.5+, no favourites                         | 67-51, +10.9u | 93-63, +23.7u  | 47-28, +16.2u | 207-142, +50.8u |    0.005 |       0.006 | no                              |                        75 |
| 4+, favourites only when the trees also say 4+   | 64-44, +15.6u | 80-48, +27.2u  | 36-20, +14.0u | 180-112, +56.8u |    0.001 |       0.022 | no                              |                        56 |
| 4+, only when the trees also say 4+ (both sides) | 49-29, +17.1u | 62-38, +20.2u  | 30-11, +17.9u | 141-78, +55.2u  |    0     |       0.007 | no                              |                        41 |
| Favourites 4+ alone                              | 18-17, -0.7u  | 7-9, -2.9u     | 8-3, +4.7u    | 33-29, +1.1u    |    0.498 |       0.906 | no                              |                        11 |
| Favourites 5+ alone                              | 4-9, -5.9u    | 3-5, -2.5u     | 2-2, -0.2u    | 9-16, -8.6u     |    0.968 |       1     | no                              |                         4 |

- **No rule earns more units than live on all three windows.**
- **Dogs at 3.5 with favourites at 4:**
  - It adds about 9 bets a season and 3.6 units over 2015-25.
  - It loses 3.1u on 2019-22, the window where 4 was chosen.
  - It is the one variant worth a shadow line if Matt wants more dog volume. The 3.5-4 dog band is a thin +0.3u a season.
- **Favourites alone at 5+** lose on every window: 4-9, 3-5, 2-2. That is 25 bets, and in points they tie the close.

## 6. The favourite bets at 4+ (all 62; the 3-4 band and the dogs are in the CSV)

How to read the table:
- **Line and model:** as our side reads them. -7 means we lay 7.
- **Pulls:** points toward our side.
- **Trees:** the trees' own edge.
- **SD:** the seven models' spread.
- **Games:** our side's games this season, then the opponent's.
- **QB chg:** our side's starter / the opponent's starter changed from the last game.
- **Move:** the close minus the opener toward us (2015-21).
- **5:00:** where the bet stood against the line with five minutes left (2016+).

| group         |   season |   wk | side   | opp   | venue   |   line |   model |   edge | score   | res   |   vs line |    QB |   ratings |   injury | top inputs                                                                  |   trees |   SD | games   | QB chg   |   move |   5:00 |
|:--------------|---------:|-----:|:-------|:------|:--------|-------:|--------:|-------:|:--------|:------|----------:|------:|----------:|---------:|:----------------------------------------------------------------------------|--------:|-----:|:--------|:---------|-------:|-------:|
| favourite 5+  |     2015 |    3 | CLE    | LV    | home    |   -3.5 |    8.63 |   5.13 | 20-27   | L     |     -10.5 |  1.36 |      3.46 |     1.16 | opp defense points +3.5; home +2.7; QB rating +1.4                          |    4.37 | 0.51 | 2/2     | Y/-      |   -1   |        |
| favourite 5+  |     2015 |    3 | GB     | KC    | home    |   -4.5 |   10.4  |   5.9  | 38-28   | W     |       5.5 |  2.21 |      0.81 |     3.61 | opp skill players out +3.1; home +2.7; offense points +2.3                  |    8.6  | 1.25 | 2/2     | -/-      |   -2   |        |
| favourite 5+  |     2015 |    8 | HOU    | TEN   | home    |   -3.5 |    9.5  |   6    | 20-6    | W     |      10.5 |  2.16 |      2.19 |     2.68 | home +2.5; QB rating +2.2; offense points +2.1                              |    3.26 | 1.42 | 7/6     | -/-      |   -1   |        |
| favourite 5+  |     2015 |    9 | LAC    | CHI   | home    |   -3.5 |   11.21 |   7.71 | 19-22   | L     |      -6.5 |  1.32 |      1.65 |     5.35 | opp skill players out +3.0; home +2.6; offense snaps out +1.8               |    6.72 | 0.72 | 8/7     | -/-      |   -1   |        |
| favourite 5+  |     2015 |   11 | ATL    | IND   | home    |   -3.5 |    8.61 |   5.11 | 21-24   | L     |      -6.5 |  3.85 |      0.42 |     1.67 | home +2.5; QB out +2.3; offense snaps out +1.6                              |    3.68 | 0.89 | 9/9     | -/Y      |   -3   |        |
| favourite 5+  |     2015 |   13 | WAS    | DAL   | home    |   -2   |    7.05 |   5.05 | 16-19   | L     |      -5   |  3.61 |     -1.35 |     0.9  | home +2.5; QB out +2.3; out of the race +1.6                                |    2.03 | 1.39 | 11/11   | -/Y      |   -3   |        |
| favourite 5+  |     2015 |   14 | GB     | DAL   | home    |   -6   |   11.65 |   5.65 | 28-7    | W     |      15   |  3.31 |      2.6  |     1.37 | QB rating +3.3; home +2.4; offense points +1.8                              |    6.01 | 0.39 | 12/12   | -/-      |   -1   |        |
| favourite 5+  |     2016 |   17 | PIT    | CLE   | home    |   -3.5 |   11.21 |   7.71 | 27-24   | L     |      -0.5 | -1.31 |      8.85 |    -0.34 | opp defense points +4.5; offense points +3.8; home +2.4                     |    2.36 | 2.38 | 15/15   | Y/-      |   -9   |    3.5 |
| favourite 5+  |     2017 |    4 | DAL    | LA    | home    |   -5   |   10.79 |   5.79 | 30-35   | L     |     -10   |  3.49 |      3.46 |     0.16 | QB rating +3.5; home +2.5; opp defense points +2.2                          |    9.23 | 1.56 | 3/3     | -/-      |   -3   |   -7   |
| favourite 5+  |     2017 |    6 | JAX    | LA    | home    |   -1   |    7    |   6    | 17-27   | L     |     -11   |  0.81 |      3.32 |    -0.05 | home +2.5; opp defense points +2.2; offense points +1.0                     |    3.36 | 1.21 | 5/5     | -/-      |    1   |   -8   |
| favourite 5+  |     2017 |   17 | PIT    | CLE   | home    |   -5   |   12.51 |   7.51 | 28-24   | L     |      -1   |  1.53 |      7.51 |    -0.61 | offense points +5.7; opp defense points +3.2; home +2.5                     |    2.93 | 2.05 | 15/15   | Y/-      |   -9   |   -1   |
| favourite 5+  |     2018 |    2 | DAL    | NYG   | home    |   -3   |    8.33 |   5.33 | 20-13   | W     |       4   |  1.53 |      2.55 |    -0.12 | home +2.5; opp defense points +1.6; QB rating +1.5                          |    6.41 | 0.63 | 1/1     | -/-      |   -0.5 |   14   |
| favourite 5+  |     2018 |    7 | ATL    | NYG   | home    |   -4.5 |   10.63 |   6.13 | 23-20   | L     |      -1.5 |  3.08 |      2.35 |     0.07 | QB rating +3.1; home +2.5; offense points +2.4                              |    7.85 | 0.83 | 6/6     | -/-      |    1   |    9.5 |
| favourite 5+  |     2019 |    8 | NE     | CLE   | home    |   -9.5 |   16.69 |   7.19 | 27-13   | W     |       4.5 |  3    |      9.51 |     1.12 | opp defense points +5.0; QB rating +3.0; offense points +2.9                |    6.29 | 0.77 | 7/6     | -/-      |   -1.5 |    7.5 |
| favourite 5+  |     2020 |    1 | BAL    | CLE   | home    |   -7   |   12.75 |   5.75 | 38-6    | W     |      25   |  2.36 |      5.46 |     0.95 | offense points +2.6; QB rating +2.4; opp defense points +2.4                |    9.43 | 1.64 | 0/0     | -/-      |   -1.5 |   25   |
| favourite 5+  |     2020 |    5 | ATL    | CAR   | home    |   -2.5 |    7.74 |   5.24 | 16-23   | L     |      -9.5 |  1.18 |      1.24 |     1.43 | home +2.0; offseason turnover (opp def) +1.5; skill players out +1.2        |    2.45 | 1.24 | 4/4     | -/-      |   -1   |   -9.5 |
| favourite 5+  |     2020 |    6 | PIT    | CLE   | home    |   -3   |    8.24 |   5.24 | 38-7    | W     |      28   |  1.98 |      1.83 |     0.82 | opp defense points +2.6; QB rating +2.0; home +2.0                          |    7.72 | 1.17 | 4/5     | -/-      |   -1   |   28   |
| favourite 5+  |     2021 |   12 | HOU    | NYJ   | home    |   -3   |    8.87 |   5.87 | 14-21   | L     |     -10   |  4.78 |      1.98 |     0.69 | QB rating +3.8; opp defense points +1.8; home +1.7                          |    5.88 | 0.24 | 10/10   | -/Y      |    0   |   -7   |
| favourite 5+  |     2022 |    4 | PIT    | NYJ   | home    |   -3   |    8.24 |   5.24 | 20-24   | L     |      -7   |  2.92 |      2.41 |     0.25 | QB rating +2.9; home +1.8; opp defense points +1.6                          |    3.34 | 0.92 | 3/3     | -/Y      |        |    0   |
| favourite 5+  |     2022 |   14 | TEN    | JAX   | home    |   -3   |    8.61 |   5.61 | 22-36   | L     |     -17   |  1.58 |      2.68 |     0.63 | opp defense points +2.1; home +1.8; QB rating +1.6                          |    6.7  | 0.6  | 12/12   | -/-      |        |  -17   |
| favourite 5+  |     2022 |   16 | CLE    | NO    | home    |   -3   |   10.55 |   7.55 | 10-17   | L     |     -10   |  1.89 |      0.19 |     2.82 | warm team in cold +2.3; QB rating +1.9; home +1.8                           |    5.29 | 1.1  | 14/14   | -/-      |        |  -10   |
| favourite 5+  |     2023 |    3 | JAX    | HOU   | home    |   -7.5 |   12.67 |   5.17 | 17-37   | L     |     -27.5 |  1.46 |      3.84 |     1.09 | offseason turnover (opp def) +2.3; offseason turnover (off) +1.9; home +1.8 |    6.33 | 0.64 | 2/2     | -/-      |        |  -24.5 |
| favourite 5+  |     2024 |    1 | NO     | CAR   | home    |   -3.5 |   11.92 |   8.42 | 47-10   | W     |      33.5 |  4    |      4.13 |    -0.08 | QB rating +4.0; offense points +3.0; offseason turnover (opp def) +2.1      |    7.7  | 0.36 | 0/0     | -/-      |        |   33.5 |
| favourite 5+  |     2024 |    1 | TB     | WAS   | home    |   -4   |   12.56 |   8.56 | 37-20   | W     |      13   |  2.65 |      4.51 |     0.07 | opp defense points +3.4; QB rating +2.6; offseason turnover (off) +2.5      |    8.94 | 0.26 | 0/0     | -/Y      |        |   12   |
| favourite 5+  |     2024 |    3 | NO     | PHI   | home    |   -2.5 |    9.14 |   6.64 | 12-15   | L     |      -5.5 | -1.01 |      5.05 |     1.75 | opp defense points +2.6; home +1.9; offense points +1.7                     |    7.57 | 0.42 | 2/2     | -/-      |        |   -3.5 |
| favourite 4-5 |     2015 |    1 | GB     | CHI   | away    |   -5.5 |    9.51 |   4.01 | 31-23   | W     |       2.5 |  3.32 |      5.29 |     3.23 | offense points +3.6; QB rating +3.3; home -2.7                              |    1.63 | 1.08 | 0/0     | -/-      |    0.5 |        |
| favourite 4-5 |     2015 |    2 | ARI    | CHI   | away    |   -2   |    6.38 |   4.38 | 48-23   | W     |      23   |  0.86 |      3.97 |     4.08 | opp defense points +3.4; home -2.7; offense snaps out +1.9                  |    4.27 | 0.67 | 1/1     | -/-      |   -0   |        |
| favourite 4-5 |     2015 |    4 | GB     | SF    | away    |   -7.5 |   12.12 |   4.62 | 17-3    | W     |       6.5 |  3.8  |      5.46 |     4.56 | offense points +4.7; home -2.6; QB rating +2.5                              |    6.94 | 1.03 | 3/3     | -/-      |    0.5 |        |
| favourite 4-5 |     2015 |    5 | ATL    | WAS   | home    |   -7.5 |   11.68 |   4.18 | 25-19   | L     |      -1.5 |  1.55 |      3.41 |     3.85 | offense points +3.5; home +2.6; opp skill players out +2.1                  |    3.91 | 0.98 | 4/4     | -/-      |   -0.5 |        |
| favourite 4-5 |     2015 |    5 | DEN    | LV    | away    |   -5   |    9.21 |   4.21 | 16-10   | W     |       1   |  2.89 |      6.57 |     2.17 | opp defense points +3.4; QB rating +2.9; offense points +2.7                |    5.55 | 0.66 | 4/4     | -/-      |   -0.5 |        |
| favourite 4-5 |     2015 |    6 | DET    | CHI   | home    |   -3.5 |    7.99 |   4.49 | 37-34   | L     |      -0.5 |  0.25 |      2.66 |     2.59 | home +2.5; opp defense points +2.1; opp skill players out +2.0              |    2.36 | 0.97 | 5/5     | -/-      |        |        |
| favourite 4-5 |     2015 |    6 | BAL    | SF    | away    |   -2.5 |    7.19 |   4.69 | 20-25   | L     |      -7.5 |  1.05 |      3.68 |     5.4  | offense points +3.1; offense snaps out +2.5; home -2.5                      |   -0.3  | 2.2  | 5/5     | -/-      |        |        |
| favourite 4-5 |     2015 |    8 | MIN    | CHI   | away    |   -1   |    5.93 |   4.93 | 23-20   | W     |       2   | -0.16 |      4.73 |     3.36 | opp defense points +4.2; home -2.5; opp skill players out +1.7              |    7.72 | 1.24 | 6/6     | -/-      |   -1.5 |        |
| favourite 4-5 |     2015 |    8 | LA     | SF    | home    |   -8   |   12.24 |   4.24 | 27-6    | W     |      13   |  1.09 |      3.69 |     4.25 | home +2.5; offense snaps out +2.3; QB out +1.8                              |    5.12 | 0.68 | 6/7     | -/-      |   -1   |        |
| favourite 4-5 |     2015 |   12 | CAR    | DAL   | away    |   -1   |    5.61 |   4.61 | 33-14   | W     |      18   |  0.93 |      3.62 |     1.66 | home -2.4; offense points +2.3; QB out +2.1                                 |    4.97 | 0.26 | 10/10   | -/-      |    2   |        |
| favourite 4-5 |     2015 |   12 | GB     | CHI   | home    |   -7.5 |   12.01 |   4.51 | 13-17   | L     |     -11.5 |  2.21 |      3.93 |     2.59 | home +2.4; QB rating +2.2; offense points +2.0                              |   -0.68 | 2.29 | 10/10   | -/-      |   -1.5 |        |
| favourite 4-5 |     2015 |   12 | ARI    | SF    | away    |   -7.5 |   11.54 |   4.04 | 19-13   | L     |      -1.5 |  3.42 |      6.28 |     1.7  | offense points +5.1; QB rating +3.4; home -2.4                              |    8.8  | 2.1  | 10/10   | -/-      |   -3   |        |
| favourite 4-5 |     2015 |   17 | HOU    | JAX   | home    |   -5   |    9.91 |   4.91 | 30-6    | W     |      19   |  0.23 |      4.56 |     0.28 | opp defense points +4.5; home +2.4; out of the race +1.5                    |    5.91 | 0.76 | 15/15   | Y/-      |   -1   |        |
| favourite 4-5 |     2015 |   17 | IND    | TEN   | home    |   -3.5 |    8.46 |   4.96 | 30-24   | W     |       2.5 |  0.84 |      3.34 |    -0.01 | home +2.4; offense points +1.6; out of the race +1.5                        |    4.65 | 0.38 | 15/15   | Y/Y      |   -0.5 |        |
| favourite 4-5 |     2015 |   17 | KC     | LV    | home    |   -6.5 |   11    |   4.5  | 23-17   | L     |      -0.5 |  2.18 |      6.47 |     0    | opp defense points +4.6; home +2.4; QB rating +2.2                          |    5.37 | 0.59 | 15/15   | -/-      |   -0.5 |        |
| favourite 4-5 |     2016 |    4 | MIN    | NYG   | home    |   -3.5 |    7.75 |   4.25 | 24-10   | W     |      10.5 | -0.86 |      4.65 |     0.55 | opp defense points +3.8; home +2.5; offseason turnover (opp def) +1.5       |    2.79 | 0.68 | 3/3     | -/-      |    0   |   10.5 |
| favourite 4-5 |     2016 |   15 | HOU    | JAX   | home    |   -3.5 |    7.58 |   4.08 | 21-20   | L     |      -2.5 |  0.08 |      3.09 |     0.05 | opp defense points +3.5; home +2.5; out of the race +1.3                    |   -0.15 | 1.92 | 13/13   | -/-      |   -2.5 |   -9.5 |
| favourite 4-5 |     2017 |    3 | IND    | CLE   | home    |   -1   |    5.3  |   4.3  | 31-28   | W     |       2   |  0.54 |      2.13 |     0.22 | home +2.5; offense points +1.6; offseason turnover (opp def) -0.8           |    3.17 | 0.64 | 2/2     | -/-      |    3.5 |    9   |
| favourite 4-5 |     2018 |    1 | NE     | HOU   | home    |   -6   |   10.39 |   4.39 | 27-20   | W     |       1   |  2.4  |      4.99 |    -0.62 | offense points +3.2; opp defense points +2.8; home +2.5                     |    7.98 | 1.59 | 0/0     | -/Y      |   -0.5 |    8   |
| favourite 4-5 |     2018 |    1 | LAC    | KC    | home    |   -3.5 |    7.63 |   4.13 | 28-38   | L     |     -13.5 |  2.99 |      1.17 |     0.14 | QB rating +3.0; home +2.5; opp defense points +1.7                          |    3.12 | 0.49 | 0/0     | -/Y      |    0.5 |  -13.5 |
| favourite 4-5 |     2018 |    6 | PHI    | NYG   | away    |   -1.5 |    6.1  |   4.6  | 34-13   | W     |      19.5 |  1.5  |      4.64 |    -0.45 | home -2.6; offense points +2.5; opp defense points +2.2                     |    8.81 | 1.87 | 5/5     | -/-      |   -1   |   19.5 |
| favourite 4-5 |     2018 |    8 | WAS    | NYG   | away    |   -1   |    5.08 |   4.08 | 20-13   | W     |       6   |  1.89 |      2.47 |     0.45 | home -2.5; QB rating +1.9; offseason turnover (opp def) +1.5                |    5.81 | 0.9  | 6/7     | -/-      |   -0   |    9   |
| favourite 4-5 |     2020 |    4 | KC     | NE    | home    |   -7   |   11.79 |   4.79 | 26-10   | W     |       9   |  6.1  |      1.07 |     0.66 | QB rating +6.1; home +2.0; offense points +1.9                              |    6.2  | 0.74 | 3/3     | -/Y      |        |    9   |
| favourite 4-5 |     2021 |    5 | ATL    | NYJ   | home    |   -3   |    7.99 |   4.99 | 27-20   | W     |       4   |  5.21 |      1.29 |    -2.29 | QB rating +5.2; offense points +2.1; home +1.8                              |    5.43 | 0.39 | 4/4     | -/-      |        |    0   |
| favourite 4-5 |     2021 |   13 | PHI    | NYJ   | away    |   -5   |    9.25 |   4.25 | 33-18   | W     |      10   |  3.41 |      5.08 |     0.41 | QB rating +3.4; opp defense points +2.8; offense points +1.9                |    5.76 | 0.67 | 12/11   | Y/-      |   -1.5 |   10   |
| favourite 4-5 |     2022 |    5 | GB     | NYG   | home    |   -8.5 |   13.02 |   4.52 | 22-27   | L     |     -13.5 |  3.72 |      3.24 |     1.42 | QB rating +3.7; offense points +2.0; home +1.8                              |    4.88 | 0.38 | 4/4     | -/-      |        |  -15.5 |
| favourite 4-5 |     2022 |    5 | MIA    | NYJ   | away    |   -3   |    7.39 |   4.39 | 17-40   | L     |     -26   |  3.75 |      3.64 |     0.11 | QB rating +3.8; opp defense points +2.0; home -1.8                          |    5.61 | 0.55 | 4/4     | Y/-      |        |  -19   |
| favourite 4-5 |     2022 |   11 | NE     | NYJ   | home    |   -3.5 |    8.46 |   4.96 | 10-3    | W     |       3.5 |  2.57 |      2.72 |     0.74 | QB rating +2.6; home +1.8; opp defense points +1.3                          |    8.3  | 1.49 | 9/9     | -/-      |        |   -3.5 |
| favourite 4-5 |     2022 |   13 | TB     | NO    | home    |   -3.5 |    7.65 |   4.15 | 17-16   | L     |      -2.5 |  2.24 |      1.5  |     0.42 | QB rating +2.2; home +1.7; opp out of the race +1.3                         |    2.81 | 0.62 | 11/12   | -/-      |        |  -16.5 |
| favourite 4-5 |     2022 |   15 | DAL    | JAX   | away    |   -4   |    8.88 |   4.88 | 34-40   | L     |     -10   |  1.58 |      6.28 |     0.88 | offense points +2.9; opp defense points +2.1; home -1.8                     |    5.2  | 0.35 | 13/13   | -/-      |        |   -8   |
| favourite 4-5 |     2023 |    9 | KC     | MIA   | home    |   -1   |    5.88 |   4.88 | 21-14   | W     |       6   |  2.15 |      1.23 |     0.61 | opp defense points +2.4; QB rating +2.1; home +1.8                          |    5.64 | 0.35 | 8/8     | -/-      |        |    6   |
| favourite 4-5 |     2023 |   15 | MIA    | NYJ   | home    |   -7.5 |   11.72 |   4.22 | 30-0    | W     |      22.5 |  4.92 |      3.4  |     0.08 | offense points +5.5; QB rating +4.9; home +1.8                              |    2.12 | 0.95 | 13/13   | -/-      |        |   22.5 |
| favourite 4-5 |     2024 |    7 | GB     | HOU   | home    |   -3   |    7.83 |   4.83 | 24-22   | L     |      -1   |  0.5  |      1.4  |     1.9  | home +1.8; offseason turnover (opp def) +1.8; opp defense snaps out +1.1    |    1.61 | 1.43 | 6/6     | -/-      |        |   -1   |
| favourite 4-5 |     2024 |   16 | KC     | HOU   | home    |   -3.5 |    8.28 |   4.78 | 27-19   | W     |       4.5 |  2.69 |      1.43 |     0.35 | QB rating +2.7; warm team in cold +2.0; home +1.8                           |    3.14 | 0.77 | 14/14   | -/-      |        |    4.5 |
| favourite 4-5 |     2024 |   17 | TB     | CAR   | home    |   -9.5 |   14.1  |   4.6  | 48-14   | W     |      24.5 |  3.63 |      6.63 |     0.58 | QB rating +3.6; offense points +3.3; opp defense points +2.6                |    2.55 | 0.91 | 15/15   | -/-      |        |   24.5 |
| favourite 4-5 |     2025 |    4 | DET    | CLE   | home    |  -10   |   14.28 |   4.28 | 34-10   | W     |      14   |  4.08 |      6.46 |     0.52 | offense points +5.6; QB rating +4.1; home +1.9                              |    1.72 | 1.15 | 3/3     | -/-      |        |    7   |
| favourite 4-5 |     2025 |   12 | GB     | MIN   | home    |   -6.5 |   11.22 |   4.72 | 23-6    | W     |      10.5 |  6.43 |      2.14 |    -0.87 | QB rating +6.4; home +1.9; opp out of the race +1.3                         |    4.02 | 0.35 | 10/10   | -/-      |        |   10.5 |

## Caveats

- **The samples are small.** There are 62 favourite bets at 4+ and 25 at 5+, over 11 seasons. The factor table tests 20 readings on 4 pools, so a couple of placebo p values under 0.05 are expected by chance.
- **The injury, rating and QB caps are post-hoc.** They use the ridge's coefficients as a stand-in for all seven models. A refit would move the six other models too. The situational round's refits of the injury inputs cover that case.
- **The opener archive covers 2015-21 only**, with the sweep's filter for bad rows. The play-by-play clock readings start in 2016.
- **"Luck" is the postmortem's definition**: turnovers, returns, kicks and garbage time. Its garbage-time part counts the leader's pile-on as luck.
- **All three windows were looked at.** Anything found here describes the backtest only.
