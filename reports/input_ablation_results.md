# Input ablation: results (written by experiments/input_ablation.py)

Live model refit walk-forward 2015-2025 on main (regular season scored; flags weeks 1-17 at the close, -110).

| Window | Team miss | Total miss | Spread flag | Totals flag | Wind under |
|---|---|---|---|---|---|
| 2015-18 | 7.3993 | 10.7484 | 68-58 | 132-111 | 119-97 |
| 2019-22 | 7.3739 | 10.5340 | 78-49 | 175-140 | 143-88 |
| 2023-25 | 7.2357 | 10.1040 | 37-19 | 76-55 | 77-52 |

## Summary (gain = miss without minus miss with; placebo = draws beaten of 50)

| Piece | Scored on | Gain 2015-18 | Gain 2019-22 | Gain 2023-25 | Bet records without it (spread / totals flag) | Placebo | Verdict | Dropping costs flag wins |
|---|---|---|---|---|---|---|---|---|
| P1 off_epa_play | team | -0.0024 | -0.0006 | -0.0009 | 71-53, 132-111 / 77-46, 175-140 / 36-20, 76-55 | 16 / 22 / 15 | fails | yes: spread 2023-25 37-19 -> 36-20 |
| P2 def_epa_play | team | -0.0064 | -0.0047 | +0.0026 | 67-54, 132-111 / 84-59, 175-140 / 39-22, 76-55 | 4 / 4 / 47 | fails | yes: spread 2019-22 78-49 -> 84-59; spread 2023-25 37-19 -> 39-22 |
| P3 off_pf | team | +0.0039 | -0.0012 | +0.0030 | 79-62, 132-111 / 79-62, 175-140 / 39-34, 76-55 | 48 / 17 / 48 | thin | yes: spread 2019-22 78-49 -> 79-62; spread 2023-25 37-19 -> 39-34 |
| P4 def_pf | team | +0.0332 | +0.0147 | +0.0161 | 80-76, 132-111 / 82-60, 175-140 / 32-18, 76-55 | 50 / 50 / 50 | earns its spot | yes: spread 2015-18 68-58 -> 80-76; spread 2019-22 78-49 -> 82-60; spread 2023-25 37-19 -> 32-18 |
| P5 qb_rating | team | +0.0307 | +0.0188 | +0.0267 | 66-72, 132-111 / 99-76, 175-140 / 64-48, 76-55 | 50 / 50 / 50 | earns its spot | yes: spread 2015-18 68-58 -> 66-72; spread 2019-22 78-49 -> 99-76; spread 2023-25 37-19 -> 64-48 |
| P6 home | team | +0.0596 | -0.0215 | +0.0542 | 120-92, 132-111 / 93-82, 175-140 / 48-50, 76-55 | 50 / 0 / 50 | thin | yes: spread 2019-22 78-49 -> 93-82; spread 2023-25 37-19 -> 48-50 |
| P7 neutral | team | -0.0001 | +0.0000 | +0.0000 | 68-57, 132-111 / 78-49, 175-140 / 37-19, 76-55 | 8 / 16 / 31 | fails | no |
| P8 dome | team | -0.0002 | -0.0002 | -0.0002 | 69-54, 132-111 / 77-48, 175-140 / 37-19, 76-55 | 30 / 10 / 18 | fails | no |
| P9 wind_out | team | -0.0015 | -0.0004 | +0.0019 | 68-53, 132-111 / 78-50, 175-140 / 36-20, 76-55 | 3 / 7 / 50 | fails | yes: spread 2019-22 78-49 -> 78-50; spread 2023-25 37-19 -> 36-20 |
| P10 cold | team | +0.0029 | +0.0014 | +0.0004 | 69-60, 132-111 / 76-47, 175-140 / 37-20, 76-55 | 50 / 47 / 43 | thin | yes: spread 2015-18 68-58 -> 69-60; spread 2023-25 37-19 -> 37-20 |
| P11 rain | team | +0.0009 | +0.0000 | -0.0018 | 69-57, 132-111 / 77-46, 175-140 / 39-18, 76-55 | 48 / 19 / 0 | fails | no |
| P12 warm_in_cold | team | +0.0013 | +0.0045 | +0.0023 | 68-57, 132-111 / 77-50, 175-140 / 36-19, 76-55 | 46 / 48 / 49 | thin | yes: spread 2019-22 78-49 -> 77-50; spread 2023-25 37-19 -> 36-19 |
| P13 div_game | team | -0.0005 | -0.0008 | -0.0003 | 66-56, 132-111 / 78-48, 175-140 / 37-19, 76-55 | 20 / 2 / 19 | fails | no |
| P14 qb_out | team | -0.0037 | -0.0026 | -0.0016 | 69-55, 132-111 / 79-49, 175-140 / 38-19, 76-55 | 1 / 5 / 8 | fails | no |
| P15 skill_out_value | team | +0.0033 | +0.0099 | +0.0167 | 69-58, 132-111 / 65-48, 175-140 / 30-19, 76-55 | 44 / 50 / 50 | thin | yes: spread 2019-22 78-49 -> 65-48; spread 2023-25 37-19 -> 30-19 |
| P16 opp_skill_out_value | team | -0.0006 | +0.0034 | +0.0066 | 58-50, 132-111 / 73-47, 175-140 / 36-19, 76-55 | 29 / 48 / 50 | thin | yes: spread 2015-18 68-58 -> 58-50; spread 2019-22 78-49 -> 73-47; spread 2023-25 37-19 -> 36-19 |
| P17 off_snap_out | team | -0.0018 | -0.0005 | +0.0023 | 64-51, 132-111 / 81-50, 175-140 / 36-22, 76-55 | 6 / 24 / 44 | fails | yes: spread 2023-25 37-19 -> 36-22 |
| P18 opp_def_snap_out | team | +0.0018 | +0.0022 | +0.0071 | 67-51, 132-111 / 82-52, 175-140 / 38-25, 76-55 | 40 / 43 / 50 | thin | yes: spread 2023-25 37-19 -> 38-25 |
| P19 off_turnover_early | team | +0.0019 | +0.0059 | +0.0101 | 63-54, 132-111 / 73-55, 175-140 / 43-18, 76-55 | 46 / 50 / 50 | thin | yes: spread 2015-18 68-58 -> 63-54; spread 2019-22 78-49 -> 73-55 |
| P20 opp_def_turnover_early | team | +0.0060 | +0.0103 | +0.0114 | 63-57, 132-111 / 78-54, 175-140 / 42-18, 76-55 | 50 / 50 / 50 | thin | yes: spread 2015-18 68-58 -> 63-57; spread 2019-22 78-49 -> 78-54 |
| P21 dead_late | team | +0.0039 | -0.0027 | -0.0008 | 63-54, 132-111 / 80-51, 175-140 / 37-21, 76-55 | 48 / 4 / 13 | fails | yes: spread 2015-18 68-58 -> 63-54; spread 2023-25 37-19 -> 37-21 |
| P22 opp_dead_late | team | +0.0028 | -0.0035 | +0.0004 | 67-52, 132-111 / 84-50, 175-140 / 36-27, 76-55 | 45 / 6 / 41 | fails | yes: spread 2023-25 37-19 -> 36-27 |
| T1 off_sum | total | +0.0066 | -0.0053 | +0.0013 | 68-58, 130-112 / 78-49, 183-140 / 37-19, 74-50 | 47 / 10 / 42 | fails | yes: totals 2015-18 132-111 -> 130-112 |
| T2 def_sum | total | +0.0276 | -0.0034 | +0.0069 | 68-58, 134-110 / 78-49, 173-134 / 37-19, 82-51 | 49 / 22 / 47 | thin | no |
| T3 pf_sum | total | -0.0064 | -0.0166 | +0.0238 | 68-58, 139-111 / 78-49, 183-132 / 37-19, 82-60 | 21 / 1 / 50 | fails | no |
| T4 pa_sum | total | -0.0065 | +0.0054 | +0.0048 | 68-58, 129-114 / 78-49, 179-140 / 37-19, 77-60 | 19 / 43 / 44 | fails | yes: totals 2015-18 132-111 -> 129-114; totals 2023-25 76-55 -> 77-60 |
| T5 qb_sum | total | +0.0504 | +0.1161 | +0.0921 | 68-58, 136-126 / 78-49, 185-165 / 37-19, 85-61 | 50 / 50 / 50 | thin | yes: totals 2015-18 132-111 -> 136-126; totals 2019-22 175-140 -> 185-165 |
| T6 qb_out_sum | total | -0.0116 | +0.0115 | -0.0223 | 68-58, 130-109 / 78-49, 170-134 / 37-19, 79-57 | 14 / 48 / 0 | fails | no |
| T7 wind_out | total | +0.0174 | +0.0079 | +0.0228 | 68-58, 127-112 / 78-49, 162-131 / 37-19, 69-54 | 48 / 43 / 50 | thin | yes: totals 2015-18 132-111 -> 127-112; totals 2019-22 175-140 -> 162-131; totals 2023-25 76-55 -> 69-54 |
| T8 rain_fc (RAIN_FC) | total | +0.0359 | +0.0640 | +0.0795 | 68-58, 124-108 / 78-49, 164-141 / 37-19, 66-52 | 50 / 50 / 50 | earns its spot | yes: totals 2015-18 132-111 -> 124-108; totals 2019-22 175-140 -> 164-141; totals 2023-25 76-55 -> 66-52 |
| T9 cold | total | -0.0685 | -0.0034 | -0.0048 | 68-58, 126-102 / 78-49, 174-141 / 37-19, 76-53 | 0 / 21 / 18 | fails | yes: totals 2019-22 175-140 -> 174-141 |
| T10 dome | total | +0.0021 | -0.0154 | +0.0064 | 68-58, 131-114 / 78-49, 173-141 / 37-19, 77-53 | 40 / 2 / 46 | fails | yes: totals 2015-18 132-111 -> 131-114; totals 2019-22 175-140 -> 173-141 |
| T11 qb_form_sum (QB form) | total | +0.0614 | +0.0510 | +0.0695 | 68-58, 135-120 / 78-49, 189-144 / 37-19, 72-59 | 50 / 49 / 50 | thin | yes: totals 2015-18 132-111 -> 135-120; totals 2023-25 76-55 -> 72-59 |
| B1 The equation shown | team | -0.0006 | +0.0001 | +0.0000 | 70-54, 132-111 / 78-47, 175-140 / 38-20, 76-55 | 50 / 45 / 50 | thin | no |
| B2 + success rate | team | -0.0007 | +0.0006 | +0.0011 | 66-56, 132-111 / 79-50, 175-140 / 38-20, 76-55 | 50 / 46 / 50 | thin | no |
| B3 + pass and rush ratings | team | +0.0010 | +0.0006 | -0.0002 | 68-52, 132-111 / 76-47, 175-140 / 38-19, 76-55 | 50 / 46 / 50 | thin | no |
| B4 + plays per game | team | -0.0010 | +0.0000 | -0.0018 | 68-55, 132-111 / 77-46, 175-140 / 38-21, 76-55 | 50 / 44 / 49 | fails | yes: spread 2023-25 37-19 -> 38-21 |
| B5 Less shrinkage | team | -0.0006 | +0.0000 | +0.0001 | 70-54, 132-111 / 78-47, 175-140 / 38-20, 76-55 | 50 / 45 / 50 | thin | no |
| B6 More shrinkage | team | -0.0006 | +0.0001 | +0.0000 | 70-54, 132-111 / 78-46, 175-140 / 38-20, 76-55 | 50 / 46 / 50 | thin | no |
| B7 Boosted trees | team | +0.0042 | -0.0001 | +0.0025 | 63-58, 132-111 / 80-53, 175-140 / 38-22, 76-55 | 50 / 44 / 50 | thin | yes: spread 2015-18 68-58 -> 63-58; spread 2019-22 78-49 -> 80-53; spread 2023-25 37-19 -> 38-22 |
| W1 wind points | total | -0.0024 | -0.0031 | +0.0110 | 68-58, 131-116 / 78-49, 171-136 / 37-19, 68-52 | 26 / 23 / 49 | fails | yes: totals 2015-18 132-111 -> 131-116; totals 2023-25 76-55 -> 68-52 |
| S1 share-out | team | -0.0150 | -0.0254 | +0.0183 | 68-58, 132-111 / 78-49, 175-140 / 37-19, 76-55 | 49 / 43 / 50 | fails | no |
| C1 cover | log loss | +0.0132 | +0.0061 | +0.0059 | unchanged | 50 / 49 / 41 | thin | no |
| C2 over | log loss | +0.0111 | +0.0023 | -0.0001 | unchanged | 50 / 47 / 42 | thin | no |
| C3 home win | log loss | +0.0027 | +0.0015 | +0.0013 | unchanged | 49 / 49 / 40 | thin | no |
| C4 teaser spread leg | log loss | -0.0004 | +0.0013 | +0.0011 | unchanged | not defined | thin | no |
| C5 teaser total leg | log loss | +0.0099 | +0.0048 | -0.0010 | unchanged | 50 / 50 / 47 | thin | no |

Drop candidates (verdict fails and dropping costs no flag wins): P7, P8, P11, P13, P14, T3, T6, S1

## P1 off_epa_play: study_gate on team

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | NO | miss 7.3969 -> 7.3993 |
| better on 2019-22 | NO | miss 7.3733 -> 7.3739 |
| better on 2023-25 | NO | miss 7.2348 -> 7.2357 |
| no bet cost: spread flag, 2015-18 | NO | 71-53 -> 68-58 |
| no bet cost: totals flag, 2015-18 | yes | 132-111 -> 132-111 |
| no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| no bet cost: spread flag, 2019-22 | NO | 77-46 -> 78-49 |
| no bet cost: totals flag, 2019-22 | yes | 175-140 -> 175-140 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 36-20 -> 37-19 |
| no bet cost: totals flag, 2023-25 | yes | 76-55 -> 76-55 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |
| beats its placebo on 2015-18 | NO | 16 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2019-22 | NO | 22 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2023-25 | NO | 15 of 50 draws (need 45 of at least 50) |

Gate: FAIL (7 of 15); no market input and no look-ahead checked by the model-auditor agent

## P2 def_epa_play: study_gate on team

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | NO | miss 7.3929 -> 7.3993 |
| better on 2019-22 | NO | miss 7.3692 -> 7.3739 |
| better on 2023-25 | yes | miss 7.2383 -> 7.2357 |
| no bet cost: spread flag, 2015-18 | NO | 67-54 -> 68-58 |
| no bet cost: totals flag, 2015-18 | yes | 132-111 -> 132-111 |
| no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| no bet cost: spread flag, 2019-22 | yes | 84-59 -> 78-49 |
| no bet cost: totals flag, 2019-22 | yes | 175-140 -> 175-140 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 39-22 -> 37-19 |
| no bet cost: totals flag, 2023-25 | yes | 76-55 -> 76-55 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |
| beats its placebo on 2015-18 | NO | 4 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2019-22 | NO | 4 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2023-25 | yes | 47 of 50 draws (need 45 of at least 50) |

Gate: FAIL (10 of 15); no market input and no look-ahead checked by the model-auditor agent

## P3 off_pf: study_gate on team

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | yes | miss 7.4031 -> 7.3993 |
| better on 2019-22 | NO | miss 7.3727 -> 7.3739 |
| better on 2023-25 | yes | miss 7.2388 -> 7.2357 |
| no bet cost: spread flag, 2015-18 | NO | 79-62 -> 68-58 |
| no bet cost: totals flag, 2015-18 | yes | 132-111 -> 132-111 |
| no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| no bet cost: spread flag, 2019-22 | yes | 79-62 -> 78-49 |
| no bet cost: totals flag, 2019-22 | yes | 175-140 -> 175-140 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 39-34 -> 37-19 |
| no bet cost: totals flag, 2023-25 | yes | 76-55 -> 76-55 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |
| beats its placebo on 2015-18 | yes | 48 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2019-22 | NO | 17 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2023-25 | yes | 48 of 50 draws (need 45 of at least 50) |

Gate: FAIL (12 of 15); no market input and no look-ahead checked by the model-auditor agent

## P4 def_pf: study_gate on team

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | yes | miss 7.4324 -> 7.3993 |
| better on 2019-22 | yes | miss 7.3886 -> 7.3739 |
| better on 2023-25 | yes | miss 7.2518 -> 7.2357 |
| no bet cost: spread flag, 2015-18 | yes | 80-76 -> 68-58 |
| no bet cost: totals flag, 2015-18 | yes | 132-111 -> 132-111 |
| no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| no bet cost: spread flag, 2019-22 | yes | 82-60 -> 78-49 |
| no bet cost: totals flag, 2019-22 | yes | 175-140 -> 175-140 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 32-18 -> 37-19 |
| no bet cost: totals flag, 2023-25 | yes | 76-55 -> 76-55 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |
| beats its placebo on 2015-18 | yes | 50 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2019-22 | yes | 50 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2023-25 | yes | 50 of 50 draws (need 45 of at least 50) |

Gate: PASS (15 of 15); no market input and no look-ahead checked by the model-auditor agent

## P5 qb_rating: study_gate on team

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | yes | miss 7.4300 -> 7.3993 |
| better on 2019-22 | yes | miss 7.3927 -> 7.3739 |
| better on 2023-25 | yes | miss 7.2624 -> 7.2357 |
| no bet cost: spread flag, 2015-18 | yes | 66-72 -> 68-58 |
| no bet cost: totals flag, 2015-18 | yes | 132-111 -> 132-111 |
| no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| no bet cost: spread flag, 2019-22 | yes | 99-76 -> 78-49 |
| no bet cost: totals flag, 2019-22 | yes | 175-140 -> 175-140 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 64-48 -> 37-19 |
| no bet cost: totals flag, 2023-25 | yes | 76-55 -> 76-55 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |
| beats its placebo on 2015-18 | yes | 50 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2019-22 | yes | 50 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2023-25 | yes | 50 of 50 draws (need 45 of at least 50) |

Gate: PASS (15 of 15); no market input and no look-ahead checked by the model-auditor agent

## P6 home: study_gate on team

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | yes | miss 7.4589 -> 7.3993 |
| better on 2019-22 | NO | miss 7.3524 -> 7.3739 |
| better on 2023-25 | yes | miss 7.2899 -> 7.2357 |
| no bet cost: spread flag, 2015-18 | NO | 120-92 -> 68-58 |
| no bet cost: totals flag, 2015-18 | yes | 132-111 -> 132-111 |
| no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| no bet cost: spread flag, 2019-22 | yes | 93-82 -> 78-49 |
| no bet cost: totals flag, 2019-22 | yes | 175-140 -> 175-140 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 48-50 -> 37-19 |
| no bet cost: totals flag, 2023-25 | yes | 76-55 -> 76-55 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |
| beats its placebo on 2015-18 | yes | 50 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2019-22 | NO | 0 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2023-25 | yes | 50 of 50 draws (need 45 of at least 50) |

Gate: FAIL (12 of 15); no market input and no look-ahead checked by the model-auditor agent

## P7 neutral: study_gate on team

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | NO | miss 7.3992 -> 7.3993 |
| better on 2019-22 | yes | miss 7.3739 -> 7.3739 |
| better on 2023-25 | yes | miss 7.2357 -> 7.2357 |
| no bet cost: spread flag, 2015-18 | NO | 68-57 -> 68-58 |
| no bet cost: totals flag, 2015-18 | yes | 132-111 -> 132-111 |
| no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| no bet cost: spread flag, 2019-22 | yes | 78-49 -> 78-49 |
| no bet cost: totals flag, 2019-22 | yes | 175-140 -> 175-140 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 37-19 -> 37-19 |
| no bet cost: totals flag, 2023-25 | yes | 76-55 -> 76-55 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |
| beats its placebo on 2015-18 | NO | 8 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2019-22 | NO | 16 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2023-25 | NO | 31 of 50 draws (need 45 of at least 50) |

Gate: FAIL (10 of 15); no market input and no look-ahead checked by the model-auditor agent

## P8 dome: study_gate on team

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | NO | miss 7.3991 -> 7.3993 |
| better on 2019-22 | NO | miss 7.3737 -> 7.3739 |
| better on 2023-25 | NO | miss 7.2355 -> 7.2357 |
| no bet cost: spread flag, 2015-18 | NO | 69-54 -> 68-58 |
| no bet cost: totals flag, 2015-18 | yes | 132-111 -> 132-111 |
| no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| no bet cost: spread flag, 2019-22 | yes | 77-48 -> 78-49 |
| no bet cost: totals flag, 2019-22 | yes | 175-140 -> 175-140 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 37-19 -> 37-19 |
| no bet cost: totals flag, 2023-25 | yes | 76-55 -> 76-55 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |
| beats its placebo on 2015-18 | NO | 30 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2019-22 | NO | 10 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2023-25 | NO | 18 of 50 draws (need 45 of at least 50) |

Gate: FAIL (8 of 15); no market input and no look-ahead checked by the model-auditor agent

## P9 wind_out: study_gate on team

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | NO | miss 7.3978 -> 7.3993 |
| better on 2019-22 | NO | miss 7.3735 -> 7.3739 |
| better on 2023-25 | yes | miss 7.2376 -> 7.2357 |
| no bet cost: spread flag, 2015-18 | NO | 68-53 -> 68-58 |
| no bet cost: totals flag, 2015-18 | yes | 132-111 -> 132-111 |
| no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| no bet cost: spread flag, 2019-22 | yes | 78-50 -> 78-49 |
| no bet cost: totals flag, 2019-22 | yes | 175-140 -> 175-140 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 36-20 -> 37-19 |
| no bet cost: totals flag, 2023-25 | yes | 76-55 -> 76-55 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |
| beats its placebo on 2015-18 | NO | 3 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2019-22 | NO | 7 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2023-25 | yes | 50 of 50 draws (need 45 of at least 50) |

Gate: FAIL (10 of 15); no market input and no look-ahead checked by the model-auditor agent

## P10 cold: study_gate on team

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | yes | miss 7.4022 -> 7.3993 |
| better on 2019-22 | yes | miss 7.3752 -> 7.3739 |
| better on 2023-25 | yes | miss 7.2362 -> 7.2357 |
| no bet cost: spread flag, 2015-18 | yes | 69-60 -> 68-58 |
| no bet cost: totals flag, 2015-18 | yes | 132-111 -> 132-111 |
| no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| no bet cost: spread flag, 2019-22 | yes | 76-47 -> 78-49 |
| no bet cost: totals flag, 2019-22 | yes | 175-140 -> 175-140 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 37-20 -> 37-19 |
| no bet cost: totals flag, 2023-25 | yes | 76-55 -> 76-55 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |
| beats its placebo on 2015-18 | yes | 50 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2019-22 | yes | 47 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2023-25 | NO | 43 of 50 draws (need 45 of at least 50) |

Gate: FAIL (14 of 15); no market input and no look-ahead checked by the model-auditor agent

## P11 rain: study_gate on team

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | yes | miss 7.4002 -> 7.3993 |
| better on 2019-22 | yes | miss 7.3739 -> 7.3739 |
| better on 2023-25 | NO | miss 7.2339 -> 7.2357 |
| no bet cost: spread flag, 2015-18 | NO | 69-57 -> 68-58 |
| no bet cost: totals flag, 2015-18 | yes | 132-111 -> 132-111 |
| no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| no bet cost: spread flag, 2019-22 | NO | 77-46 -> 78-49 |
| no bet cost: totals flag, 2019-22 | yes | 175-140 -> 175-140 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | NO | 39-18 -> 37-19 |
| no bet cost: totals flag, 2023-25 | yes | 76-55 -> 76-55 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |
| beats its placebo on 2015-18 | yes | 48 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2019-22 | NO | 19 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2023-25 | NO | 0 of 50 draws (need 45 of at least 50) |

Gate: FAIL (9 of 15); no market input and no look-ahead checked by the model-auditor agent

## P12 warm_in_cold: study_gate on team

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | yes | miss 7.4006 -> 7.3993 |
| better on 2019-22 | yes | miss 7.3783 -> 7.3739 |
| better on 2023-25 | yes | miss 7.2380 -> 7.2357 |
| no bet cost: spread flag, 2015-18 | NO | 68-57 -> 68-58 |
| no bet cost: totals flag, 2015-18 | yes | 132-111 -> 132-111 |
| no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| no bet cost: spread flag, 2019-22 | yes | 77-50 -> 78-49 |
| no bet cost: totals flag, 2019-22 | yes | 175-140 -> 175-140 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 36-19 -> 37-19 |
| no bet cost: totals flag, 2023-25 | yes | 76-55 -> 76-55 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |
| beats its placebo on 2015-18 | yes | 46 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2019-22 | yes | 48 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2023-25 | yes | 49 of 50 draws (need 45 of at least 50) |

Gate: FAIL (14 of 15); no market input and no look-ahead checked by the model-auditor agent

## P13 div_game: study_gate on team

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | NO | miss 7.3988 -> 7.3993 |
| better on 2019-22 | NO | miss 7.3731 -> 7.3739 |
| better on 2023-25 | NO | miss 7.2354 -> 7.2357 |
| no bet cost: spread flag, 2015-18 | yes | 66-56 -> 68-58 |
| no bet cost: totals flag, 2015-18 | yes | 132-111 -> 132-111 |
| no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| no bet cost: spread flag, 2019-22 | NO | 78-48 -> 78-49 |
| no bet cost: totals flag, 2019-22 | yes | 175-140 -> 175-140 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 37-19 -> 37-19 |
| no bet cost: totals flag, 2023-25 | yes | 76-55 -> 76-55 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |
| beats its placebo on 2015-18 | NO | 20 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2019-22 | NO | 2 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2023-25 | NO | 19 of 50 draws (need 45 of at least 50) |

Gate: FAIL (8 of 15); no market input and no look-ahead checked by the model-auditor agent

## P14 qb_out: study_gate on team

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | NO | miss 7.3956 -> 7.3993 |
| better on 2019-22 | NO | miss 7.3713 -> 7.3739 |
| better on 2023-25 | NO | miss 7.2342 -> 7.2357 |
| no bet cost: spread flag, 2015-18 | NO | 69-55 -> 68-58 |
| no bet cost: totals flag, 2015-18 | yes | 132-111 -> 132-111 |
| no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| no bet cost: spread flag, 2019-22 | NO | 79-49 -> 78-49 |
| no bet cost: totals flag, 2019-22 | yes | 175-140 -> 175-140 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | NO | 38-19 -> 37-19 |
| no bet cost: totals flag, 2023-25 | yes | 76-55 -> 76-55 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |
| beats its placebo on 2015-18 | NO | 1 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2019-22 | NO | 5 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2023-25 | NO | 8 of 50 draws (need 45 of at least 50) |

Gate: FAIL (6 of 15); no market input and no look-ahead checked by the model-auditor agent

## P15 skill_out_value: study_gate on team

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | yes | miss 7.4026 -> 7.3993 |
| better on 2019-22 | yes | miss 7.3838 -> 7.3739 |
| better on 2023-25 | yes | miss 7.2525 -> 7.2357 |
| no bet cost: spread flag, 2015-18 | NO | 69-58 -> 68-58 |
| no bet cost: totals flag, 2015-18 | yes | 132-111 -> 132-111 |
| no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| no bet cost: spread flag, 2019-22 | yes | 65-48 -> 78-49 |
| no bet cost: totals flag, 2019-22 | yes | 175-140 -> 175-140 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 30-19 -> 37-19 |
| no bet cost: totals flag, 2023-25 | yes | 76-55 -> 76-55 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |
| beats its placebo on 2015-18 | NO | 44 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2019-22 | yes | 50 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2023-25 | yes | 50 of 50 draws (need 45 of at least 50) |

Gate: FAIL (13 of 15); no market input and no look-ahead checked by the model-auditor agent

## P16 opp_skill_out_value: study_gate on team

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | NO | miss 7.3987 -> 7.3993 |
| better on 2019-22 | yes | miss 7.3773 -> 7.3739 |
| better on 2023-25 | yes | miss 7.2423 -> 7.2357 |
| no bet cost: spread flag, 2015-18 | yes | 58-50 -> 68-58 |
| no bet cost: totals flag, 2015-18 | yes | 132-111 -> 132-111 |
| no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| no bet cost: spread flag, 2019-22 | yes | 73-47 -> 78-49 |
| no bet cost: totals flag, 2019-22 | yes | 175-140 -> 175-140 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 36-19 -> 37-19 |
| no bet cost: totals flag, 2023-25 | yes | 76-55 -> 76-55 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |
| beats its placebo on 2015-18 | NO | 29 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2019-22 | yes | 48 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2023-25 | yes | 50 of 50 draws (need 45 of at least 50) |

Gate: FAIL (13 of 15); no market input and no look-ahead checked by the model-auditor agent

## P17 off_snap_out: study_gate on team

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | NO | miss 7.3975 -> 7.3993 |
| better on 2019-22 | NO | miss 7.3734 -> 7.3739 |
| better on 2023-25 | yes | miss 7.2380 -> 7.2357 |
| no bet cost: spread flag, 2015-18 | NO | 64-51 -> 68-58 |
| no bet cost: totals flag, 2015-18 | yes | 132-111 -> 132-111 |
| no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| no bet cost: spread flag, 2019-22 | NO | 81-50 -> 78-49 |
| no bet cost: totals flag, 2019-22 | yes | 175-140 -> 175-140 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 36-22 -> 37-19 |
| no bet cost: totals flag, 2023-25 | yes | 76-55 -> 76-55 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |
| beats its placebo on 2015-18 | NO | 6 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2019-22 | NO | 24 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2023-25 | NO | 44 of 50 draws (need 45 of at least 50) |

Gate: FAIL (8 of 15); no market input and no look-ahead checked by the model-auditor agent

## P18 opp_def_snap_out: study_gate on team

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | yes | miss 7.4011 -> 7.3993 |
| better on 2019-22 | yes | miss 7.3761 -> 7.3739 |
| better on 2023-25 | yes | miss 7.2428 -> 7.2357 |
| no bet cost: spread flag, 2015-18 | NO | 67-51 -> 68-58 |
| no bet cost: totals flag, 2015-18 | yes | 132-111 -> 132-111 |
| no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| no bet cost: spread flag, 2019-22 | NO | 82-52 -> 78-49 |
| no bet cost: totals flag, 2019-22 | yes | 175-140 -> 175-140 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 38-25 -> 37-19 |
| no bet cost: totals flag, 2023-25 | yes | 76-55 -> 76-55 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |
| beats its placebo on 2015-18 | NO | 40 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2019-22 | NO | 43 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2023-25 | yes | 50 of 50 draws (need 45 of at least 50) |

Gate: FAIL (11 of 15); no market input and no look-ahead checked by the model-auditor agent

## P19 off_turnover_early: study_gate on team

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | yes | miss 7.4012 -> 7.3993 |
| better on 2019-22 | yes | miss 7.3797 -> 7.3739 |
| better on 2023-25 | yes | miss 7.2458 -> 7.2357 |
| no bet cost: spread flag, 2015-18 | yes | 63-54 -> 68-58 |
| no bet cost: totals flag, 2015-18 | yes | 132-111 -> 132-111 |
| no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| no bet cost: spread flag, 2019-22 | yes | 73-55 -> 78-49 |
| no bet cost: totals flag, 2019-22 | yes | 175-140 -> 175-140 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | NO | 43-18 -> 37-19 |
| no bet cost: totals flag, 2023-25 | yes | 76-55 -> 76-55 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |
| beats its placebo on 2015-18 | yes | 46 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2019-22 | yes | 50 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2023-25 | yes | 50 of 50 draws (need 45 of at least 50) |

Gate: FAIL (14 of 15); no market input and no look-ahead checked by the model-auditor agent

## P20 opp_def_turnover_early: study_gate on team

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | yes | miss 7.4053 -> 7.3993 |
| better on 2019-22 | yes | miss 7.3842 -> 7.3739 |
| better on 2023-25 | yes | miss 7.2471 -> 7.2357 |
| no bet cost: spread flag, 2015-18 | yes | 63-57 -> 68-58 |
| no bet cost: totals flag, 2015-18 | yes | 132-111 -> 132-111 |
| no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| no bet cost: spread flag, 2019-22 | yes | 78-54 -> 78-49 |
| no bet cost: totals flag, 2019-22 | yes | 175-140 -> 175-140 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | NO | 42-18 -> 37-19 |
| no bet cost: totals flag, 2023-25 | yes | 76-55 -> 76-55 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |
| beats its placebo on 2015-18 | yes | 50 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2019-22 | yes | 50 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2023-25 | yes | 50 of 50 draws (need 45 of at least 50) |

Gate: FAIL (14 of 15); no market input and no look-ahead checked by the model-auditor agent

## P21 dead_late: study_gate on team

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | yes | miss 7.4032 -> 7.3993 |
| better on 2019-22 | NO | miss 7.3712 -> 7.3739 |
| better on 2023-25 | NO | miss 7.2349 -> 7.2357 |
| no bet cost: spread flag, 2015-18 | yes | 63-54 -> 68-58 |
| no bet cost: totals flag, 2015-18 | yes | 132-111 -> 132-111 |
| no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| no bet cost: spread flag, 2019-22 | yes | 80-51 -> 78-49 |
| no bet cost: totals flag, 2019-22 | yes | 175-140 -> 175-140 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 37-21 -> 37-19 |
| no bet cost: totals flag, 2023-25 | yes | 76-55 -> 76-55 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |
| beats its placebo on 2015-18 | yes | 48 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2019-22 | NO | 4 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2023-25 | NO | 13 of 50 draws (need 45 of at least 50) |

Gate: FAIL (11 of 15); no market input and no look-ahead checked by the model-auditor agent

## P22 opp_dead_late: study_gate on team

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | yes | miss 7.4021 -> 7.3993 |
| better on 2019-22 | NO | miss 7.3704 -> 7.3739 |
| better on 2023-25 | yes | miss 7.2361 -> 7.2357 |
| no bet cost: spread flag, 2015-18 | NO | 67-52 -> 68-58 |
| no bet cost: totals flag, 2015-18 | yes | 132-111 -> 132-111 |
| no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| no bet cost: spread flag, 2019-22 | NO | 84-50 -> 78-49 |
| no bet cost: totals flag, 2019-22 | yes | 175-140 -> 175-140 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 36-27 -> 37-19 |
| no bet cost: totals flag, 2023-25 | yes | 76-55 -> 76-55 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |
| beats its placebo on 2015-18 | yes | 45 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2019-22 | NO | 6 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2023-25 | NO | 41 of 50 draws (need 45 of at least 50) |

Gate: FAIL (10 of 15); no market input and no look-ahead checked by the model-auditor agent

## T1 off_sum: study_gate on total

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | yes | miss 10.7550 -> 10.7484 |
| better on 2019-22 | NO | miss 10.5287 -> 10.5340 |
| better on 2023-25 | yes | miss 10.1054 -> 10.1040 |
| no bet cost: spread flag, 2015-18 | yes | 68-58 -> 68-58 |
| no bet cost: totals flag, 2015-18 | yes | 130-112 -> 132-111 |
| no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| no bet cost: spread flag, 2019-22 | yes | 78-49 -> 78-49 |
| no bet cost: totals flag, 2019-22 | NO | 183-140 -> 175-140 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 37-19 -> 37-19 |
| no bet cost: totals flag, 2023-25 | NO | 74-50 -> 76-55 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |
| beats its placebo on 2015-18 | yes | 47 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2019-22 | NO | 10 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2023-25 | NO | 42 of 50 draws (need 45 of at least 50) |

Gate: FAIL (10 of 15); no market input and no look-ahead checked by the model-auditor agent

## T2 def_sum: study_gate on total

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | yes | miss 10.7760 -> 10.7484 |
| better on 2019-22 | NO | miss 10.5306 -> 10.5340 |
| better on 2023-25 | yes | miss 10.1109 -> 10.1040 |
| no bet cost: spread flag, 2015-18 | yes | 68-58 -> 68-58 |
| no bet cost: totals flag, 2015-18 | NO | 134-110 -> 132-111 |
| no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| no bet cost: spread flag, 2019-22 | yes | 78-49 -> 78-49 |
| no bet cost: totals flag, 2019-22 | NO | 173-134 -> 175-140 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 37-19 -> 37-19 |
| no bet cost: totals flag, 2023-25 | NO | 82-51 -> 76-55 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |
| beats its placebo on 2015-18 | yes | 49 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2019-22 | NO | 22 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2023-25 | yes | 47 of 50 draws (need 45 of at least 50) |

Gate: FAIL (10 of 15); no market input and no look-ahead checked by the model-auditor agent

## T3 pf_sum: study_gate on total

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | NO | miss 10.7420 -> 10.7484 |
| better on 2019-22 | NO | miss 10.5174 -> 10.5340 |
| better on 2023-25 | yes | miss 10.1279 -> 10.1040 |
| no bet cost: spread flag, 2015-18 | yes | 68-58 -> 68-58 |
| no bet cost: totals flag, 2015-18 | NO | 139-111 -> 132-111 |
| no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| no bet cost: spread flag, 2019-22 | yes | 78-49 -> 78-49 |
| no bet cost: totals flag, 2019-22 | NO | 183-132 -> 175-140 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 37-19 -> 37-19 |
| no bet cost: totals flag, 2023-25 | NO | 82-60 -> 76-55 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |
| beats its placebo on 2015-18 | NO | 21 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2019-22 | NO | 1 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2023-25 | yes | 50 of 50 draws (need 45 of at least 50) |

Gate: FAIL (8 of 15); no market input and no look-ahead checked by the model-auditor agent

## T4 pa_sum: study_gate on total

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | NO | miss 10.7420 -> 10.7484 |
| better on 2019-22 | yes | miss 10.5395 -> 10.5340 |
| better on 2023-25 | yes | miss 10.1088 -> 10.1040 |
| no bet cost: spread flag, 2015-18 | yes | 68-58 -> 68-58 |
| no bet cost: totals flag, 2015-18 | yes | 129-114 -> 132-111 |
| no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| no bet cost: spread flag, 2019-22 | yes | 78-49 -> 78-49 |
| no bet cost: totals flag, 2019-22 | NO | 179-140 -> 175-140 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 37-19 -> 37-19 |
| no bet cost: totals flag, 2023-25 | yes | 77-60 -> 76-55 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |
| beats its placebo on 2015-18 | NO | 19 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2019-22 | NO | 43 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2023-25 | NO | 44 of 50 draws (need 45 of at least 50) |

Gate: FAIL (10 of 15); no market input and no look-ahead checked by the model-auditor agent

## T5 qb_sum: study_gate on total

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | yes | miss 10.7989 -> 10.7484 |
| better on 2019-22 | yes | miss 10.6501 -> 10.5340 |
| better on 2023-25 | yes | miss 10.1961 -> 10.1040 |
| no bet cost: spread flag, 2015-18 | yes | 68-58 -> 68-58 |
| no bet cost: totals flag, 2015-18 | yes | 136-126 -> 132-111 |
| no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| no bet cost: spread flag, 2019-22 | yes | 78-49 -> 78-49 |
| no bet cost: totals flag, 2019-22 | yes | 185-165 -> 175-140 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 37-19 -> 37-19 |
| no bet cost: totals flag, 2023-25 | NO | 85-61 -> 76-55 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |
| beats its placebo on 2015-18 | yes | 50 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2019-22 | yes | 50 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2023-25 | yes | 50 of 50 draws (need 45 of at least 50) |

Gate: FAIL (14 of 15); no market input and no look-ahead checked by the model-auditor agent

## T6 qb_out_sum: study_gate on total

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | NO | miss 10.7369 -> 10.7484 |
| better on 2019-22 | yes | miss 10.5456 -> 10.5340 |
| better on 2023-25 | NO | miss 10.0817 -> 10.1040 |
| no bet cost: spread flag, 2015-18 | yes | 68-58 -> 68-58 |
| no bet cost: totals flag, 2015-18 | yes | 130-109 -> 132-111 |
| no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| no bet cost: spread flag, 2019-22 | yes | 78-49 -> 78-49 |
| no bet cost: totals flag, 2019-22 | NO | 170-134 -> 175-140 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 37-19 -> 37-19 |
| no bet cost: totals flag, 2023-25 | NO | 79-57 -> 76-55 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |
| beats its placebo on 2015-18 | NO | 14 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2019-22 | yes | 48 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2023-25 | NO | 0 of 50 draws (need 45 of at least 50) |

Gate: FAIL (9 of 15); no market input and no look-ahead checked by the model-auditor agent

## T7 wind_out: study_gate on total

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | yes | miss 10.7659 -> 10.7484 |
| better on 2019-22 | yes | miss 10.5419 -> 10.5340 |
| better on 2023-25 | yes | miss 10.1268 -> 10.1040 |
| no bet cost: spread flag, 2015-18 | yes | 68-58 -> 68-58 |
| no bet cost: totals flag, 2015-18 | yes | 127-112 -> 132-111 |
| no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| no bet cost: spread flag, 2019-22 | yes | 78-49 -> 78-49 |
| no bet cost: totals flag, 2019-22 | yes | 162-131 -> 175-140 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 37-19 -> 37-19 |
| no bet cost: totals flag, 2023-25 | yes | 69-54 -> 76-55 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |
| beats its placebo on 2015-18 | yes | 48 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2019-22 | NO | 43 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2023-25 | yes | 50 of 50 draws (need 45 of at least 50) |

Gate: FAIL (14 of 15); no market input and no look-ahead checked by the model-auditor agent

## T8 rain_fc (RAIN_FC): study_gate on total

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | yes | miss 10.7843 -> 10.7484 |
| better on 2019-22 | yes | miss 10.5981 -> 10.5340 |
| better on 2023-25 | yes | miss 10.1835 -> 10.1040 |
| no bet cost: spread flag, 2015-18 | yes | 68-58 -> 68-58 |
| no bet cost: totals flag, 2015-18 | yes | 124-108 -> 132-111 |
| no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| no bet cost: spread flag, 2019-22 | yes | 78-49 -> 78-49 |
| no bet cost: totals flag, 2019-22 | yes | 164-141 -> 175-140 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 37-19 -> 37-19 |
| no bet cost: totals flag, 2023-25 | yes | 66-52 -> 76-55 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |
| beats its placebo on 2015-18 | yes | 50 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2019-22 | yes | 50 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2023-25 | yes | 50 of 50 draws (need 45 of at least 50) |

Gate: PASS (15 of 15); no market input and no look-ahead checked by the model-auditor agent

## T9 cold: study_gate on total

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | NO | miss 10.6799 -> 10.7484 |
| better on 2019-22 | NO | miss 10.5306 -> 10.5340 |
| better on 2023-25 | NO | miss 10.0993 -> 10.1040 |
| no bet cost: spread flag, 2015-18 | yes | 68-58 -> 68-58 |
| no bet cost: totals flag, 2015-18 | NO | 126-102 -> 132-111 |
| no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| no bet cost: spread flag, 2019-22 | yes | 78-49 -> 78-49 |
| no bet cost: totals flag, 2019-22 | yes | 174-141 -> 175-140 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 37-19 -> 37-19 |
| no bet cost: totals flag, 2023-25 | NO | 76-53 -> 76-55 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |
| beats its placebo on 2015-18 | NO | 0 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2019-22 | NO | 21 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2023-25 | NO | 18 of 50 draws (need 45 of at least 50) |

Gate: FAIL (7 of 15); no market input and no look-ahead checked by the model-auditor agent

## T10 dome: study_gate on total

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | yes | miss 10.7505 -> 10.7484 |
| better on 2019-22 | NO | miss 10.5187 -> 10.5340 |
| better on 2023-25 | yes | miss 10.1104 -> 10.1040 |
| no bet cost: spread flag, 2015-18 | yes | 68-58 -> 68-58 |
| no bet cost: totals flag, 2015-18 | yes | 131-114 -> 132-111 |
| no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| no bet cost: spread flag, 2019-22 | yes | 78-49 -> 78-49 |
| no bet cost: totals flag, 2019-22 | yes | 173-141 -> 175-140 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 37-19 -> 37-19 |
| no bet cost: totals flag, 2023-25 | NO | 77-53 -> 76-55 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |
| beats its placebo on 2015-18 | NO | 40 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2019-22 | NO | 2 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2023-25 | yes | 46 of 50 draws (need 45 of at least 50) |

Gate: FAIL (11 of 15); no market input and no look-ahead checked by the model-auditor agent

## T11 qb_form_sum (QB form): study_gate on total

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | yes | miss 10.8098 -> 10.7484 |
| better on 2019-22 | yes | miss 10.5851 -> 10.5340 |
| better on 2023-25 | yes | miss 10.1735 -> 10.1040 |
| no bet cost: spread flag, 2015-18 | yes | 68-58 -> 68-58 |
| no bet cost: totals flag, 2015-18 | yes | 135-120 -> 132-111 |
| no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| no bet cost: spread flag, 2019-22 | yes | 78-49 -> 78-49 |
| no bet cost: totals flag, 2019-22 | NO | 189-144 -> 175-140 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 37-19 -> 37-19 |
| no bet cost: totals flag, 2023-25 | yes | 72-59 -> 76-55 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |
| beats its placebo on 2015-18 | yes | 50 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2019-22 | yes | 49 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2023-25 | yes | 50 of 50 draws (need 45 of at least 50) |

Gate: FAIL (14 of 15); no market input and no look-ahead checked by the model-auditor agent

## B1 The equation shown: study_gate on team

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | NO | miss 7.3987 -> 7.3993 |
| better on 2019-22 | yes | miss 7.3739 -> 7.3739 |
| better on 2023-25 | yes | miss 7.2358 -> 7.2357 |
| no bet cost: spread flag, 2015-18 | NO | 70-54 -> 68-58 |
| no bet cost: totals flag, 2015-18 | yes | 132-111 -> 132-111 |
| no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| no bet cost: spread flag, 2019-22 | NO | 78-47 -> 78-49 |
| no bet cost: totals flag, 2019-22 | yes | 175-140 -> 175-140 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 38-20 -> 37-19 |
| no bet cost: totals flag, 2023-25 | yes | 76-55 -> 76-55 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |
| beats its placebo on 2015-18 | yes | 50 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2019-22 | yes | 45 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2023-25 | yes | 50 of 50 draws (need 45 of at least 50) |

Gate: FAIL (12 of 15); no market input and no look-ahead checked by the model-auditor agent

## B2 + success rate: study_gate on team

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | NO | miss 7.3986 -> 7.3993 |
| better on 2019-22 | yes | miss 7.3745 -> 7.3739 |
| better on 2023-25 | yes | miss 7.2368 -> 7.2357 |
| no bet cost: spread flag, 2015-18 | yes | 66-56 -> 68-58 |
| no bet cost: totals flag, 2015-18 | yes | 132-111 -> 132-111 |
| no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| no bet cost: spread flag, 2019-22 | yes | 79-50 -> 78-49 |
| no bet cost: totals flag, 2019-22 | yes | 175-140 -> 175-140 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 38-20 -> 37-19 |
| no bet cost: totals flag, 2023-25 | yes | 76-55 -> 76-55 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |
| beats its placebo on 2015-18 | yes | 50 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2019-22 | yes | 46 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2023-25 | yes | 50 of 50 draws (need 45 of at least 50) |

Gate: FAIL (14 of 15); no market input and no look-ahead checked by the model-auditor agent

## B3 + pass and rush ratings: study_gate on team

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | yes | miss 7.4003 -> 7.3993 |
| better on 2019-22 | yes | miss 7.3745 -> 7.3739 |
| better on 2023-25 | NO | miss 7.2356 -> 7.2357 |
| no bet cost: spread flag, 2015-18 | NO | 68-52 -> 68-58 |
| no bet cost: totals flag, 2015-18 | yes | 132-111 -> 132-111 |
| no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| no bet cost: spread flag, 2019-22 | yes | 76-47 -> 78-49 |
| no bet cost: totals flag, 2019-22 | yes | 175-140 -> 175-140 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | NO | 38-19 -> 37-19 |
| no bet cost: totals flag, 2023-25 | yes | 76-55 -> 76-55 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |
| beats its placebo on 2015-18 | yes | 50 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2019-22 | yes | 46 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2023-25 | yes | 50 of 50 draws (need 45 of at least 50) |

Gate: FAIL (12 of 15); no market input and no look-ahead checked by the model-auditor agent

## B4 + plays per game: study_gate on team

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | NO | miss 7.3983 -> 7.3993 |
| better on 2019-22 | yes | miss 7.3739 -> 7.3739 |
| better on 2023-25 | NO | miss 7.2339 -> 7.2357 |
| no bet cost: spread flag, 2015-18 | NO | 68-55 -> 68-58 |
| no bet cost: totals flag, 2015-18 | yes | 132-111 -> 132-111 |
| no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| no bet cost: spread flag, 2019-22 | NO | 77-46 -> 78-49 |
| no bet cost: totals flag, 2019-22 | yes | 175-140 -> 175-140 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 38-21 -> 37-19 |
| no bet cost: totals flag, 2023-25 | yes | 76-55 -> 76-55 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |
| beats its placebo on 2015-18 | yes | 50 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2019-22 | NO | 44 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2023-25 | yes | 49 of 50 draws (need 45 of at least 50) |

Gate: FAIL (10 of 15); no market input and no look-ahead checked by the model-auditor agent

## B5 Less shrinkage: study_gate on team

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | NO | miss 7.3987 -> 7.3993 |
| better on 2019-22 | yes | miss 7.3739 -> 7.3739 |
| better on 2023-25 | yes | miss 7.2358 -> 7.2357 |
| no bet cost: spread flag, 2015-18 | NO | 70-54 -> 68-58 |
| no bet cost: totals flag, 2015-18 | yes | 132-111 -> 132-111 |
| no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| no bet cost: spread flag, 2019-22 | NO | 78-47 -> 78-49 |
| no bet cost: totals flag, 2019-22 | yes | 175-140 -> 175-140 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 38-20 -> 37-19 |
| no bet cost: totals flag, 2023-25 | yes | 76-55 -> 76-55 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |
| beats its placebo on 2015-18 | yes | 50 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2019-22 | yes | 45 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2023-25 | yes | 50 of 50 draws (need 45 of at least 50) |

Gate: FAIL (12 of 15); no market input and no look-ahead checked by the model-auditor agent

## B6 More shrinkage: study_gate on team

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | NO | miss 7.3987 -> 7.3993 |
| better on 2019-22 | yes | miss 7.3740 -> 7.3739 |
| better on 2023-25 | yes | miss 7.2357 -> 7.2357 |
| no bet cost: spread flag, 2015-18 | NO | 70-54 -> 68-58 |
| no bet cost: totals flag, 2015-18 | yes | 132-111 -> 132-111 |
| no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| no bet cost: spread flag, 2019-22 | NO | 78-46 -> 78-49 |
| no bet cost: totals flag, 2019-22 | yes | 175-140 -> 175-140 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 38-20 -> 37-19 |
| no bet cost: totals flag, 2023-25 | yes | 76-55 -> 76-55 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |
| beats its placebo on 2015-18 | yes | 50 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2019-22 | yes | 46 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2023-25 | yes | 50 of 50 draws (need 45 of at least 50) |

Gate: FAIL (12 of 15); no market input and no look-ahead checked by the model-auditor agent

## B7 Boosted trees: study_gate on team

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | yes | miss 7.4035 -> 7.3993 |
| better on 2019-22 | NO | miss 7.3738 -> 7.3739 |
| better on 2023-25 | yes | miss 7.2383 -> 7.2357 |
| no bet cost: spread flag, 2015-18 | yes | 63-58 -> 68-58 |
| no bet cost: totals flag, 2015-18 | yes | 132-111 -> 132-111 |
| no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| no bet cost: spread flag, 2019-22 | yes | 80-53 -> 78-49 |
| no bet cost: totals flag, 2019-22 | yes | 175-140 -> 175-140 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 38-22 -> 37-19 |
| no bet cost: totals flag, 2023-25 | yes | 76-55 -> 76-55 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |
| beats its placebo on 2015-18 | yes | 50 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2019-22 | NO | 44 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2023-25 | yes | 50 of 50 draws (need 45 of at least 50) |

Gate: FAIL (13 of 15); no market input and no look-ahead checked by the model-auditor agent

## W1 wind points: study_gate on total

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | NO | miss 10.7460 -> 10.7484 |
| better on 2019-22 | NO | miss 10.5310 -> 10.5340 |
| better on 2023-25 | yes | miss 10.1150 -> 10.1040 |
| no bet cost: spread flag, 2015-18 | yes | 68-58 -> 68-58 |
| no bet cost: totals flag, 2015-18 | yes | 131-116 -> 132-111 |
| no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| no bet cost: spread flag, 2019-22 | yes | 78-49 -> 78-49 |
| no bet cost: totals flag, 2019-22 | yes | 171-136 -> 175-140 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 37-19 -> 37-19 |
| no bet cost: totals flag, 2023-25 | yes | 68-52 -> 76-55 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |
| beats its placebo on 2015-18 | NO | 26 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2019-22 | NO | 23 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2023-25 | yes | 49 of 50 draws (need 45 of at least 50) |

Gate: FAIL (11 of 15); no market input and no look-ahead checked by the model-auditor agent

## S1 share-out: study_gate on team

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | NO | miss 7.3843 -> 7.3993 |
| better on 2019-22 | NO | miss 7.3485 -> 7.3739 |
| better on 2023-25 | yes | miss 7.2541 -> 7.2357 |
| no bet cost: spread flag, 2015-18 | yes | 68-58 -> 68-58 |
| no bet cost: totals flag, 2015-18 | yes | 132-111 -> 132-111 |
| no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| no bet cost: spread flag, 2019-22 | yes | 78-49 -> 78-49 |
| no bet cost: totals flag, 2019-22 | yes | 175-140 -> 175-140 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 37-19 -> 37-19 |
| no bet cost: totals flag, 2023-25 | yes | 76-55 -> 76-55 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |
| beats its placebo on 2015-18 | yes | 49 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2019-22 | NO | 43 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2023-25 | yes | 50 of 50 draws (need 45 of at least 50) |

Gate: FAIL (12 of 15); no market input and no look-ahead checked by the model-auditor agent

## C1 cover: study_gate on log loss

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | yes | miss 0.7064 -> 0.6931 |
| better on 2019-22 | yes | miss 0.7002 -> 0.6941 |
| better on 2023-25 | yes | miss 0.6987 -> 0.6928 |
| no bet cost: spread flag, 2015-18 | yes | 68-58 -> 68-58 |
| no bet cost: totals flag, 2015-18 | yes | 132-111 -> 132-111 |
| no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| no bet cost: spread flag, 2019-22 | yes | 78-49 -> 78-49 |
| no bet cost: totals flag, 2019-22 | yes | 175-140 -> 175-140 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 37-19 -> 37-19 |
| no bet cost: totals flag, 2023-25 | yes | 76-55 -> 76-55 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |
| calibration not worse, 2015-18 | yes | 0.2562 -> 0.2500 |
| calibration not worse, 2019-22 | yes | 0.2533 -> 0.2505 |
| calibration not worse, 2023-25 | yes | 0.2526 -> 0.2498 |
| beats its placebo on 2015-18 | yes | 50 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2019-22 | yes | 49 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2023-25 | NO | 41 of 50 draws (need 45 of at least 50) |

Gate: FAIL (17 of 18); no market input and no look-ahead checked by the model-auditor agent

## C2 over: study_gate on log loss

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | yes | miss 0.7057 -> 0.6946 |
| better on 2019-22 | yes | miss 0.6925 -> 0.6903 |
| better on 2023-25 | NO | miss 0.6900 -> 0.6901 |
| no bet cost: spread flag, 2015-18 | yes | 68-58 -> 68-58 |
| no bet cost: totals flag, 2015-18 | yes | 132-111 -> 132-111 |
| no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| no bet cost: spread flag, 2019-22 | yes | 78-49 -> 78-49 |
| no bet cost: totals flag, 2019-22 | yes | 175-140 -> 175-140 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 37-19 -> 37-19 |
| no bet cost: totals flag, 2023-25 | yes | 76-55 -> 76-55 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |
| calibration not worse, 2015-18 | yes | 0.2560 -> 0.2507 |
| calibration not worse, 2019-22 | yes | 0.2496 -> 0.2486 |
| calibration not worse, 2023-25 | NO | 0.2484 -> 0.2485 |
| beats its placebo on 2015-18 | yes | 50 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2019-22 | yes | 47 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2023-25 | NO | 42 of 50 draws (need 45 of at least 50) |

Gate: FAIL (15 of 18); no market input and no look-ahead checked by the model-auditor agent

## C3 home win: study_gate on log loss

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | yes | miss 0.6066 -> 0.6039 |
| better on 2019-22 | yes | miss 0.6260 -> 0.6245 |
| better on 2023-25 | yes | miss 0.6218 -> 0.6205 |
| no bet cost: spread flag, 2015-18 | yes | 68-58 -> 68-58 |
| no bet cost: totals flag, 2015-18 | yes | 132-111 -> 132-111 |
| no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| no bet cost: spread flag, 2019-22 | yes | 78-49 -> 78-49 |
| no bet cost: totals flag, 2019-22 | yes | 175-140 -> 175-140 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 37-19 -> 37-19 |
| no bet cost: totals flag, 2023-25 | yes | 76-55 -> 76-55 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |
| calibration not worse, 2015-18 | yes | 0.2093 -> 0.2082 |
| calibration not worse, 2019-22 | yes | 0.2184 -> 0.2173 |
| calibration not worse, 2023-25 | yes | 0.2163 -> 0.2155 |
| beats its placebo on 2015-18 | yes | 49 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2019-22 | yes | 49 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2023-25 | NO | 40 of 50 draws (need 45 of at least 50) |

Gate: FAIL (17 of 18); no market input and no look-ahead checked by the model-auditor agent

## C4 teaser spread leg: study_gate on log loss

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | NO | miss 0.6062 -> 0.6066 |
| better on 2019-22 | yes | miss 0.6128 -> 0.6114 |
| better on 2023-25 | yes | miss 0.6037 -> 0.6026 |
| no bet cost: spread flag, 2015-18 | yes | 68-58 -> 68-58 |
| no bet cost: totals flag, 2015-18 | yes | 132-111 -> 132-111 |
| no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| no bet cost: spread flag, 2019-22 | yes | 78-49 -> 78-49 |
| no bet cost: totals flag, 2019-22 | yes | 175-140 -> 175-140 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 37-19 -> 37-19 |
| no bet cost: totals flag, 2023-25 | yes | 76-55 -> 76-55 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |
| calibration not worse, 2015-18 | NO | 0.2070 -> 0.2073 |
| calibration not worse, 2019-22 | yes | 0.2101 -> 0.2097 |
| calibration not worse, 2023-25 | yes | 0.2069 -> 0.2065 |
| beats its placebo on 2015-18 | yes | not defined: one shift per season, a within-season shuffle changes nothing |
| beats its placebo on 2019-22 | yes | not defined: one shift per season, a within-season shuffle changes nothing |
| beats its placebo on 2023-25 | yes | not defined: one shift per season, a within-season shuffle changes nothing |

Gate: FAIL (16 of 18); no market input and no look-ahead checked by the model-auditor agent

## C5 teaser total leg: study_gate on log loss

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | yes | miss 0.6389 -> 0.6290 |
| better on 2019-22 | yes | miss 0.6216 -> 0.6167 |
| better on 2023-25 | NO | miss 0.5941 -> 0.5951 |
| no bet cost: spread flag, 2015-18 | yes | 68-58 -> 68-58 |
| no bet cost: totals flag, 2015-18 | yes | 132-111 -> 132-111 |
| no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| no bet cost: spread flag, 2019-22 | yes | 78-49 -> 78-49 |
| no bet cost: totals flag, 2019-22 | yes | 175-140 -> 175-140 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 37-19 -> 37-19 |
| no bet cost: totals flag, 2023-25 | yes | 76-55 -> 76-55 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |
| calibration not worse, 2015-18 | yes | 0.2220 -> 0.2185 |
| calibration not worse, 2019-22 | yes | 0.2145 -> 0.2128 |
| calibration not worse, 2023-25 | NO | 0.2021 -> 0.2025 |
| beats its placebo on 2015-18 | yes | 50 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2019-22 | yes | 50 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2023-25 | yes | 47 of 50 draws (need 45 of at least 50) |

Gate: FAIL (16 of 18); no market input and no look-ahead checked by the model-auditor agent

