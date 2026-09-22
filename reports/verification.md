# Verification

## 1. 2024 season totals from play-by-play vs Pro-Football-Reference (the table in the old sheet)

PFR counts a few things differently from nflverse (sacks in plays, penalty first downs, aborted snaps), so small gaps are a definitions question, not a data error. Anything more than a handful per team would be.

| stat    |   teams |   exact_matches |   mean_abs_diff |   max_abs_diff | worst_team   |   ours_worst |   pfr_worst |
|:--------|--------:|----------------:|----------------:|---------------:|:-------------|-------------:|------------:|
| PF      |      32 |              32 |            0    |           0    | DET          |       564    |       564   |
| Yds     |      32 |              29 |            0.59 |          13    | IND          |      5679    |      5692   |
| Ply     |      32 |              31 |            0.03 |           1    | HOU          |      1057    |      1058   |
| TO      |      32 |              31 |            0.03 |           1    | CIN          |        21    |        22   |
| FL      |      32 |              31 |            0.03 |           1    | CIN          |        12    |        13   |
| 1stD    |      32 |              26 |            0.22 |           2    | TB           |       393    |       395   |
| Cmp     |      32 |              32 |            0    |           0    | DET          |       399    |       399   |
| Att     |      32 |              32 |            0    |           0    | DET          |       551    |       551   |
| PassYds |      32 |              32 |            0    |           0    | DET          |      4474    |      4474   |
| PassTD  |      32 |              32 |            0    |           0    | DET          |        39    |        39   |
| Int     |      32 |              32 |            0    |           0    | DET          |        12    |        12   |
| RushAtt |      32 |              31 |            0.03 |           1    | HOU          |       433    |       434   |
| RushYds |      32 |              29 |            0.59 |          13    | IND          |      2318    |      2331   |
| RushTD  |      32 |              32 |            0    |           0    | DET          |        29    |        29   |
| Pen     |      32 |              27 |            0.22 |           2    | WAS          |       109    |       111   |
| PenYds  |      32 |              27 |            2.47 |          27    | WAS          |       933    |       960   |
| Sc%     |      32 |              15 |            0.54 |           1.38 | MIN          |        42.78 |        41.4 |
| 3DAtt   |      32 |              32 |            0    |           0    | KC           |       nan    |       nan   |
| 3DConv  |      32 |              32 |            0    |           0    | KC           |       nan    |       nan   |
| 4DAtt   |      32 |              32 |            0    |           0    | KC           |       nan    |       nan   |
| RZAtt   |      32 |              24 |            0.38 |           2    | KC           |       nan    |       nan   |
| RZTD    |      32 |              27 |            0.19 |           2    | BAL          |       nan    |       nan   |
| Drives  |      32 |               7 |            1.91 |           5    | PHI          |       nan    |       nan   |
| Sc%     |      32 |              15 |            0.54 |           1.38 | MIN          |       nan    |       nan   |

## 2. Points in the team table equal the schedule scores

7722 team-game rows, 0 mismatches.

## 3. What one offense gained equals what the other defense allowed

7722 pairs, 0 mismatches.

## 4. Known results

| game           | field       |   expected |   got | ok   |
|:---------------|:------------|-----------:|------:|:-----|
| 2024_22_KC_PHI | away_score  |       22   |  22   | True |
| 2024_22_KC_PHI | home_score  |       40   |  40   | True |
| 2024_22_KC_PHI | spread_line |       -1.5 |  -1.5 | True |
| 2023_22_SF_KC  | home_score  |       25   |  25   | True |
| 2023_22_SF_KC  | away_score  |       22   |  22   | True |
| 2024_01_BAL_KC | home_score  |       27   |  27   | True |
| 2024_01_BAL_KC | away_score  |       20   |  20   | True |

Result: PASS