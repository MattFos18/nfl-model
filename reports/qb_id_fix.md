# The listed starting QB: audit and fix (experiments/qb_id_fix.py)

## Adoption rule (written 29 Sep 2026 before any variant was scored)

The fix is a data correction, so no gain is required. It is **adopted** if the strict version (the corrected QB id used
only for games before the one being priced; the priced game keeps the schedule's listed id) does **not worsen margin MAE
or the 4+ spread record on any of the three windows** (2015-18, 2019-22, 2023-25), against today's base reproduced first
in the same run. The first-dropback version (a) (every played game carries the QB who took its first dropback, the
priced game included) is used **for the backtest only if it improves margin MAE on all three windows**. The live week is
unchanged either way except that the carried-forward starter (`last_qb`) comes from the corrected played games.

Run 29 Sep 2026 20:17, 27s (features and predictions read back from the scratch dir when present; the first full run's timings are under Runtimes). Nothing under nflmodel/, data/processed/, web/ or docs/ was written; the features were rebuilt in memory and the trees cache pointed at `/tmp/claude-0/-home-user/c1e0d18e-681a-50ba-b0bb-6c809c2e3dee/scratchpad/qb_id_fix`.

## 1. Audit: the listed starter against who actually dropped back, 2013-2026

Every played team-game (regular season and playoffs). The first-dropback QB is the passer (`passer_id`, which also carries scrambles) on the team's first dropback by a player whose roster position is QB; the most-dropbacks QB counts every dropback. 'Listed QB came in relief' = he dropped back, but another QB took the first one. 'Started, replaced in game' is not an error (the listed QB took the first dropback, another QB took more). A trick play (a punter or receiver throwing first) is not counted as a start.

|   season |   team-games |   ok |   listed QB took no dropback |   listed QB came in relief |   listed id != first-dropback QB |   started, replaced in game |   first-dropback QB != most-dropbacks QB |   trick play took the first dropback |   no play-by-play |
|---------:|-------------:|-----:|-----------------------------:|---------------------------:|---------------------------------:|----------------------------:|-----------------------------------------:|-------------------------------------:|------------------:|
|     2013 |          534 |  522 |                            0 |                          0 |                                0 |                          12 |                                       12 |                                    1 |                 0 |
|     2014 |          534 |  518 |                            0 |                          1 |                                1 |                          15 |                                       16 |                                    1 |                 0 |
|     2015 |          534 |  520 |                            0 |                          1 |                                1 |                          13 |                                       14 |                                    0 |                 0 |
|     2016 |          534 |  520 |                            0 |                          3 |                                3 |                          11 |                                       14 |                                    0 |                 0 |
|     2017 |          534 |  518 |                            0 |                          2 |                                2 |                          14 |                                       16 |                                    0 |                 0 |
|     2018 |          534 |  524 |                            0 |                          2 |                                2 |                           8 |                                       10 |                                    0 |                 0 |
|     2019 |          534 |  520 |                            0 |                          1 |                                1 |                          13 |                                       14 |                                    2 |                 0 |
|     2020 |          538 |  528 |                            0 |                          1 |                                1 |                           9 |                                       10 |                                    0 |                 0 |
|     2021 |          570 |  555 |                            0 |                          1 |                                1 |                          14 |                                       15 |                                    0 |                 0 |
|     2022 |          568 |  549 |                            4 |                          3 |                                7 |                          12 |                                       14 |                                    0 |                 0 |
|     2023 |          570 |  553 |                            0 |                          0 |                                0 |                          17 |                                       17 |                                    0 |                 0 |
|     2024 |          570 |  519 |                           33 |                          4 |                               37 |                          14 |                                       16 |                                    0 |                 0 |
|     2025 |          570 |  547 |                            7 |                          1 |                                8 |                          15 |                                       15 |                                    0 |                 0 |
|     2026 |           96 |   60 |                            1 |                          0 |                                1 |                           3 |                                        3 |                                    0 |                32 |

Errors (took no dropback + came in relief): 2013: 0, 2014: 1, 2015: 1, 2016: 3, 2017: 2, 2018: 2, 2019: 1, 2020: 1, 2021: 1, 2022: 7, 2023: 0, 2024: 37, 2025: 8, 2026: 1.

`passer_player_id` agrees with `passer_id` on every dropback where both are filled; it is empty on scrambles, so reading the first non-empty `passer_player_id` instead gives a different starter in 0 team-games; `passer_id` is used.

## 2. Where the bad ids come from

The ids are nflverse's: `build.py` copies `home_qb_id` / `away_qb_id` straight from `data/raw/schedules/games.csv` (every bad id below is the same in the raw file). Checks against nflverse's other sources, for the error rows from 2022 on:

|   season |   errors |   in_raw_games_csv |   listed_is_depth_qb1 |   listed_was_prev_starter |   listed_started_earlier |   listed_inactive_or_reserve |
|---------:|---------:|-------------------:|----------------------:|--------------------------:|-------------------------:|-----------------------------:|
|     2022 |        7 |                  7 |                     6 |                         4 |                        6 |                            2 |
|     2024 |       37 |                 37 |                    20 |                        10 |                       28 |                            8 |
|     2025 |        8 |                  8 |                     3 |                         3 |                        8 |                            4 |
|     2026 |        1 |                  1 |                     0 |                         0 |                        0 |                            1 |

Depth chart QB1 before the game equals the first-dropback QB in this share of team-games (the chart is itself often stale, so it is no fix): 2013 91%, 2014 96%, 2015 90%, 2016 91%, 2017 91%, 2018 92%, 2019 90%, 2020 91%, 2021 88%, 2022 86%, 2023 87%, 2024 86%, 2025 92%, 2026 94%.

Reading of the sources. The bad ids are in nflverse's schedule file itself (`games.csv`), and they are not derived from nflverse's
play-by-play: the pbp's first dropback (`passer_id`; `passer_player_id` agrees wherever it is filled) names the real starter in every error row.
Two different faults show up:

- **2013-2021 (1-3 a season): the id and the name come from different sources.** In the relief rows the schedule's *name* is the starter and the
  *id* is the QB who threw the most (2017 Wk 17 PHI: name Nick Foles, id Nate Sudfeld; 2015 Wk 17 TEN: Mettenberger / Tanney; 2020 Wk 17 ARI:
  Kyler Murray / Streveler; 2018 Wk 17 GB, 2019 Wk 17 BUF, 2021 Wk 16 CAR the same pattern with name and id both the reliever). These are
  games where the starter left early, and the id follows the passing leader.
- **2022 on, and above all 2024 Weeks 8-18: a pre-game "projected starter" that was never reconciled with who played.** The listed QB took no
  dropback at all. In most rows he is the team's earlier starter or the depth chart's QB1 (a stale chart: Dalton for Carolina after Young
  took the job back, Rudolph for Tennessee after Levis returned, Flacco for Indianapolis around Richardson's benching, DeVito for the Giants
  while Lock started, Minshew / O'Connell swapped for Las Vegas), and in the rest he is the injured starter (the weekly roster already had
  him inactive or on reserve that week: Hurts 2024 Wk 17, Tua 2024 Wk 18, Winston, Daniels 2025 Wks 4 and 8, Young 2025 Wk 8, Tyrod Taylor
  2025 Wk 17). Mariota listed for Washington in Weeks 9-13 of 2024 was the QB who finished Week 7 after Daniels' rib injury. The depth chart is no
  fix: its QB1 matches the first-dropback QB in only 86-96% of team-games in any season 2013-2025.

Every error row:

| game_id         | team   | kind                       | listed_name       |   listed_n | first_qb_name       | most_name           |   team_db | listed_status   | listed_is_depth_qb1   | first_is_depth_qb1   | listed_was_prev_starter   | id_name_disagree   |
|:----------------|:-------|:---------------------------|:------------------|-----------:|:--------------------|:--------------------|----------:|:----------------|:----------------------|:---------------------|:--------------------------|:-------------------|
| 2014_17_BUF_NE  | NE     | listed QB came in relief   | Jimmy Garoppolo   |         22 | T.Brady             | J.Garoppolo         |        40 | ACT             | False                 | True                 | False                     | False              |
| 2015_17_TEN_IND | TEN    | listed QB came in relief   | Zach Mettenberger |         17 | Z.Mettenberger      | A.Tanney            |        31 | ACT             | False                 | False                | False                     | True               |
| 2016_13_CAR_SEA | CAR    | listed QB came in relief   | Cam Newton        |         33 | D.Anderson          | C.Newton            |        34 | ACT             | True                  | False                | True                      | False              |
| 2016_17_DAL_PHI | DAL    | listed QB came in relief   | Mark Sanchez      |         21 | D.Prescott          | M.Sanchez           |        34 | ACT             | False                 | True                 | False                     | False              |
| 2016_17_HOU_TEN | HOU    | listed QB came in relief   | Brock Osweiler    |         43 | T.Savage            | B.Osweiler          |        52 | ACT             | True                  | False                | False                     | False              |
| 2017_17_BUF_MIA | MIA    | listed QB came in relief   | Jay Cutler        |         46 | J.Cutler            | D.Fales             |        48 | ACT             | False                 | True                 | False                     | True               |
| 2017_17_DAL_PHI | PHI    | listed QB came in relief   | Nick Foles        |         27 | N.Foles             | N.Sudfeld           |        38 | ACT             | False                 | True                 | False                     | True               |
| 2018_14_NYJ_BUF | NYJ    | listed QB came in relief   | Sam Darnold       |         24 | J.McCown            | S.Darnold           |        25 | ACT             | False                 | True                 | False                     | False              |
| 2018_17_DET_GB  | GB     | listed QB came in relief   | DeShone Kizer     |         40 | A.Rodgers           | D.Kizer             |        46 | ACT             | False                 | True                 | False                     | False              |
| 2019_17_NYJ_BUF | BUF    | listed QB came in relief   | Matt Barkley      |         35 | J.Allen             | M.Barkley           |        40 | ACT             | False                 | True                 | False                     | False              |
| 2020_17_ARI_LA  | ARI    | listed QB came in relief   | Kyler Murray      |         18 | K.Murray            | C.Streveler         |        31 | ACT             | False                 | True                 | False                     | True               |
| 2021_16_TB_CAR  | CAR    | listed QB came in relief   | Sam Darnold       |         37 | C.Newton            | S.Darnold           |        53 | ACT             | False                 | True                 | False                     | False              |
| 2022_06_MIN_MIA | MIA    | listed QB came in relief   | Teddy Bridgewater |         41 | S.Thompson          | T.Bridgewater       |        56 | ACT             | True                  | False                | True                      | False              |
| 2022_08_LV_NO   | NO     | listed QB took no dropback | Jameis Winston    |          0 | A.Dalton            | A.Dalton            |        31 | ACT             | True                  | False                | False                     | False              |
| 2022_11_CAR_BAL | CAR    | listed QB took no dropback | Phillip Walker    |          0 | B.Mayfield          | B.Mayfield          |        39 | INA             | True                  | False                | True                      | False              |
| 2022_11_PHI_IND | IND    | listed QB took no dropback | Sam Ehlinger      |          0 | M.Ryan              | M.Ryan              |        36 | ACT             | True                  | False                | False                     | False              |
| 2022_15_KC_HOU  | HOU    | listed QB came in relief   | Davis Mills       |         27 | J.Driskel           | D.Mills             |        33 | ACT             | True                  | False                | True                      | False              |
| 2022_15_PIT_CAR | PIT    | listed QB took no dropback | Kenny Pickett     |          0 | M.Trubisky          | M.Trubisky          |        23 | INA             | True                  | False                | True                      | False              |
| 2022_18_TB_ATL  | TB     | listed QB came in relief   | Blaine Gabbert    |          8 | T.Brady             | T.Brady             |        34 | ACT             | False                 | True                 | False                     | False              |
| 2024_07_MIA_IND | MIA    | listed QB came in relief   | Tim Boyle         |         13 | T.Huntley           | T.Huntley           |        31 | ACT             | False                 | True                 | False                     | False              |
| 2024_08_ARI_MIA | MIA    | listed QB took no dropback | Tim Boyle         |          0 | T.Tagovailoa        | T.Tagovailoa        |        40 | ACT             | False                 | False                | False                     | False              |
| 2024_08_IND_HOU | IND    | listed QB took no dropback | Joe Flacco        |          0 | A.Richardson        | A.Richardson        |        38 | ACT             | False                 | True                 | False                     | False              |
| 2024_08_KC_LV   | LV     | listed QB took no dropback | Aidan O'Connell   |          0 | G.Minshew II        | G.Minshew II        |        34 | RES             | True                  | False                | True                      | False              |
| 2024_09_WAS_NYG | WAS    | listed QB took no dropback | Marcus Mariota    |          0 | J.Daniels           | J.Daniels           |        25 | ACT             | False                 | True                 | False                     | False              |
| 2024_10_NYG_CAR | CAR    | listed QB took no dropback | Andy Dalton       |          0 | B.Young             | B.Young             |        28 | ACT             | True                  | False                | False                     | False              |
| 2024_10_PIT_WAS | WAS    | listed QB took no dropback | Marcus Mariota    |          0 | J.Daniels           | J.Daniels           |        37 | ACT             | False                 | True                 | False                     | False              |
| 2024_10_TEN_LAC | TEN    | listed QB took no dropback | Mason Rudolph     |          0 | W.Levis             | W.Levis             |        33 | ACT             | True                  | False                | True                      | False              |
| 2024_11_IND_NYJ | IND    | listed QB took no dropback | Joe Flacco        |          0 | A.Richardson        | A.Richardson        |        33 | ACT             | True                  | False                | True                      | False              |
| 2024_11_MIN_TEN | TEN    | listed QB took no dropback | Mason Rudolph     |          0 | W.Levis             | W.Levis             |        38 | ACT             | True                  | False                | False                     | False              |
| 2024_11_WAS_PHI | WAS    | listed QB took no dropback | Marcus Mariota    |          0 | J.Daniels           | J.Daniels           |        40 | ACT             | False                 | True                 | False                     | False              |
| 2024_12_DAL_WAS | WAS    | listed QB took no dropback | Marcus Mariota    |          0 | J.Daniels           | J.Daniels           |        43 | ACT             | False                 | True                 | False                     | False              |
| 2024_12_DET_IND | IND    | listed QB took no dropback | Joe Flacco        |          0 | A.Richardson        | A.Richardson        |        30 | ACT             | True                  | False                | False                     | False              |
| 2024_12_KC_CAR  | CAR    | listed QB took no dropback | Andy Dalton       |          0 | B.Young             | B.Young             |        40 | ACT             | True                  | False                | False                     | False              |
| 2024_12_TEN_HOU | TEN    | listed QB took no dropback | Mason Rudolph     |          0 | W.Levis             | W.Levis             |        35 | ACT             | True                  | False                | False                     | False              |
| 2024_13_IND_NE  | IND    | listed QB took no dropback | Joe Flacco        |          0 | A.Richardson        | A.Richardson        |        25 | ACT             | True                  | False                | False                     | False              |
| 2024_13_LV_KC   | LV     | listed QB took no dropback | Gardner Minshew   |          0 | A.O'Connell         | A.O'Connell         |        37 | RES             | True                  | False                | True                      | False              |
| 2024_13_TB_CAR  | CAR    | listed QB took no dropback | Andy Dalton       |          0 | B.Young             | B.Young             |        50 | ACT             | True                  | False                | False                     | False              |
| 2024_13_TEN_WAS | TEN    | listed QB took no dropback | Mason Rudolph     |          0 | W.Levis             | W.Levis             |        40 | ACT             | True                  | False                | False                     | False              |
| 2024_13_TEN_WAS | WAS    | listed QB took no dropback | Marcus Mariota    |          0 | J.Daniels           | J.Daniels           |        38 | ACT             | False                 | True                 | False                     | False              |
| 2024_14_CAR_PHI | CAR    | listed QB took no dropback | Andy Dalton       |          0 | B.Young             | B.Young             |        41 | ACT             | True                  | False                | False                     | False              |
| 2024_14_JAX_TEN | TEN    | listed QB took no dropback | Mason Rudolph     |          0 | W.Levis             | W.Levis             |        34 | ACT             | False                 | True                 | False                     | False              |
| 2024_14_LV_TB   | LV     | listed QB took no dropback | Gardner Minshew   |          0 | A.O'Connell         | A.O'Connell         |        41 | RES             | False                 | True                 | False                     | False              |
| 2024_14_NO_NYG  | NYG    | listed QB took no dropback | Tommy DeVito      |          0 | D.Lock              | D.Lock              |        56 | ACT             | True                  | False                | False                     | False              |
| 2024_15_ATL_LV  | LV     | listed QB took no dropback | Aidan O'Connell   |          0 | D.Ridder            | D.Ridder            |        45 | INA             | True                  | False                | True                      | False              |
| 2024_16_CLE_CIN | CLE    | listed QB took no dropback | Jameis Winston    |          0 | D.Thompson-Robinson | D.Thompson-Robinson |        42 | INA             | True                  | False                | True                      | False              |
| 2024_16_NO_GB   | NO     | listed QB took no dropback | Jake Haener       |          0 | S.Rattler           | S.Rattler           |        38 | ACT             | False                 | False                | True                      | False              |
| 2024_16_NYG_ATL | NYG    | listed QB took no dropback | Tommy DeVito      |          0 | D.Lock              | D.Lock              |        42 | ACT             | False                 | True                 | True                      | False              |
| 2024_16_TEN_IND | IND    | listed QB took no dropback | Joe Flacco        |          0 | A.Richardson        | A.Richardson        |        14 | ACT             | False                 | True                 | False                     | False              |
| 2024_17_DAL_PHI | PHI    | listed QB took no dropback | Jalen Hurts       |          0 | K.Pickett           | K.Pickett           |        19 | INA             | True                  | False                | True                      | False              |
| 2024_17_IND_NYG | NYG    | listed QB took no dropback | Tommy DeVito      |          0 | D.Lock              | D.Lock              |        24 | ACT             | False                 | True                 | False                     | False              |
| 2024_17_LV_NO   | NO     | listed QB took no dropback | Jake Haener       |          0 | S.Rattler           | S.Rattler           |        42 | ACT             | False                 | False                | False                     | False              |
| 2024_17_MIA_CLE | CLE    | listed QB took no dropback | Jameis Winston    |          0 | D.Thompson-Robinson | D.Thompson-Robinson |        49 | INA             | True                  | False                | False                     | False              |
| 2024_18_BUF_NE  | NE     | listed QB came in relief   | Joe Milton III    |         31 | D.Maye              | J.Milton            |        33 | ACT             | False                 | True                 | False                     | False              |
| 2024_18_HOU_TEN | HOU    | listed QB came in relief   | Davis Mills       |         24 | C.Stroud            | D.Mills             |        30 | ACT             | False                 | True                 | False                     | False              |
| 2024_18_HOU_TEN | TEN    | listed QB came in relief   | Mason Rudolph     |         11 | W.Levis             | W.Levis             |        31 | ACT             | True                  | False                | True                      | False              |
| 2024_18_MIA_NYJ | MIA    | listed QB took no dropback | Tua Tagovailoa    |          0 | T.Huntley           | T.Huntley           |        48 | INA             | True                  | False                | False                     | False              |
| 2025_04_WAS_ATL | WAS    | listed QB took no dropback | Jayden Daniels    |          0 | M.Mariota           | M.Mariota           |        30 | INA             | True                  | False                | False                     | False              |
| 2025_08_BUF_CAR | CAR    | listed QB took no dropback | Bryce Young       |          0 | A.Dalton            | A.Dalton            |        32 | INA             | True                  | False                | True                      | False              |
| 2025_08_WAS_KC  | WAS    | listed QB took no dropback | Jayden Daniels    |          0 | M.Mariota           | M.Mariota           |        35 | INA             | True                  | False                | True                      | False              |
| 2025_10_CLE_NYJ | NYJ    | listed QB took no dropback | Tyrod Taylor      |          0 | J.Fields            | J.Fields            |        16 | ACT             | False                 | True                 | False                     | False              |
| 2025_11_NYJ_NE  | NYJ    | listed QB took no dropback | Tyrod Taylor      |          0 | J.Fields            | J.Fields            |        33 | ACT             | False                 | True                 | False                     | False              |
| 2025_14_WAS_MIN | WAS    | listed QB came in relief   | Marcus Mariota    |          7 | J.Daniels           | J.Daniels           |        32 | ACT             | False                 | True                 | True                      | False              |
| 2025_16_NYJ_NO  | NYJ    | listed QB took no dropback | Tyrod Taylor      |          0 | B.Cook              | B.Cook              |        44 | ACT             | False                 | True                 | False                     | False              |
| 2025_17_NE_NYJ  | NYJ    | listed QB took no dropback | Tyrod Taylor      |          0 | B.Cook              | B.Cook              |        35 | INA             | False                 | True                 | False                     | False              |
| 2026_02_CAR_ATL | ATL    | listed QB took no dropback | Tua Tagovailoa    |          0 | C.Rush              | C.Rush              |        39 | INA             | False                 | False                | False                     | False              |

## 3-4. Rebuilt features, walk-forward with the weekly refit, 2015-2025

Variants: base = today's inputs (listed ids; reproduces `features_asof.parquet`, largest input difference 8.0e-14); (a) every played game carries its first-dropback QB, the priced game included; (b) the most-dropbacks QB; strict = the fit's training rows carry the first-dropback QB, the priced game keeps the listed id (what the live week sees). Unplayed games are unchanged in all of them (only the carried-forward starter moves). The QB inputs that move: `qb_rating`, `opp_qb_rating` (not in the equation), `qb_form` (totals equation, `qb_form_sum`). `qb_out` is built from snap counts and the injury report (trends.py) and does not read the schedule id. The split walk-forward reproduces the live one on 2024 when both tables are the same (largest spread difference 0.0e+00).

4+ spread and 55%+ under: the postmortem's rules (regular season, Weeks 1-17, -110). '4+ all REG weeks' is `experiments/common.score`'s count. 'Fixed games': games where either side's listed id differs from its first-dropback QB (63 games 2013-2026).

| variant                                                         | window   |   team MAE |   margin MAE |   total MAE | 4+ spread (Wk 1-17)   | 55%+ under (Wk 1-17)   | 4+ all REG weeks   |   margin MAE, ridge alone | margin MAE, fixed games   |
|:----------------------------------------------------------------|:---------|-----------:|-------------:|------------:|:----------------------|:-----------------------|:-------------------|--------------------------:|:--------------------------|
| base (listed ids, today)                                        | 2015-18  |     7.4094 |       9.9491 |     10.7437 | 68-55 (+7.5u)         | 135-127-3 (-4.7u)      | 68-55              |                    9.962  | 13.433 (n=8)              |
| base (listed ids, today)                                        | 2019-22  |     7.3477 |      10.0204 |     10.5406 | 80-51 (+23.9u)        | 175-128-4 (+34.2u)     | 83-54              |                   10.03   | 11.348 (n=10)             |
| base (listed ids, today)                                        | 2023-25  |     7.2623 |       9.9041 |     10.1767 | 40-21-1 (+16.9u)      | 71-59-1 (+6.1u)        | 44-26              |                    9.9137 | 9.941 (n=43)              |
| (a) first-dropback QB, every played game                        | 2015-18  |     7.4178 |       9.9612 |     10.7584 | 66-59 (+1.1u)         | 136-125-3 (-1.5u)      | 66-59              |                    9.9716 | 14.497 (n=8)              |
| (a) first-dropback QB, every played game                        | 2019-22  |     7.3527 |      10.0175 |     10.5464 | 79-49 (+25.1u)        | 175-127-4 (+35.3u)     | 82-52              |                   10.0271 | 11.3 (n=10)               |
| (a) first-dropback QB, every played game                        | 2023-25  |     7.2532 |       9.8974 |     10.1661 | 38-20-1 (+16.0u)      | 69-57-1 (+6.3u)        | 43-25              |                    9.9024 | 9.739 (n=43)              |
| (b) most-dropbacks QB, every played game                        | 2015-18  |     7.4031 |       9.9082 |     10.7724 | 73-50-1 (+18.0u)      | 128-126-3 (-10.6u)     | 73-50              |                    9.9259 | 13.406 (n=8)              |
| (b) most-dropbacks QB, every played game                        | 2019-22  |     7.354  |      10.0189 |     10.5579 | 85-52 (+27.8u)        | 175-130-4 (+32.0u)     | 88-56              |                   10.0291 | 11.349 (n=10)             |
| (b) most-dropbacks QB, every played game                        | 2023-25  |     7.25   |       9.8579 |     10.1592 | 41-19-1 (+20.1u)      | 70-58 (+6.2u)          | 47-24              |                    9.8672 | 9.799 (n=43)              |
| strict: first-dropback QB for earlier games, priced game listed | 2015-18  |     7.413  |       9.9532 |     10.7478 | 67-59 (+2.1u)         | 137-125-3 (-0.5u)      | 67-59              |                    9.9639 | 13.479 (n=8)              |
| strict: first-dropback QB for earlier games, priced game listed | 2019-22  |     7.3483 |      10.0179 |     10.545  | 78-49 (+24.1u)        | 175-127-4 (+35.3u)     | 81-52              |                   10.0257 | 11.342 (n=10)             |
| strict: first-dropback QB for earlier games, priced game listed | 2023-25  |     7.265  |       9.9085 |     10.1769 | 40-22-1 (+15.8u)      | 70-59-1 (+5.1u)        | 44-27              |                    9.9163 | 9.95 (n=43)               |

## Verdict

- **Strict (the rule's test): not adopted: worse on a window.** Margin MAE against base: 2015-18 +0.0041, 2019-22 -0.0025, 2023-25 +0.0044; 4+ record: 2015-18 67-59 vs 68-55, 2019-22 78-49 vs 80-51, 2023-25 40-22-1 vs 40-21-1. The ridge equation alone: 2015-18 +0.0019, 2019-22 -0.0043, 2023-25 +0.0026.
- **(a) first-dropback QB for every played game: not used for the backtest: margin not better on all three.** Margin MAE: 2015-18 +0.0121, 2019-22 -0.0029, 2023-25 -0.0067; 4+ record: 2015-18 66-59 vs 68-55, 2019-22 79-49 vs 80-51, 2023-25 38-20-1 vs 40-21-1.
- (b) most-dropbacks QB (not a pre-game quantity: it knows who finished the game) margin MAE: 2015-18 -0.0409, 2019-22 -0.0015, 2023-25 -0.0462; 4+ record: 2015-18 73-50-1 vs 68-55, 2019-22 85-52 vs 80-51, 2023-25 41-19-1 vs 40-21-1.

What the numbers say. The fix touches few rows: 64 team-games 2013-2025 change QB under (a) (10 of them in 2014-2018). In the strict version only training rows move (64 of 7,124, under 1%), and every window moves by less than 0.005 of margin MAE in both directions, the blend and the ridge alone (no placebo was run, so this is read as refit noise rather than measured against it). On (a)'s 2015-18 loss of 0.012, the 8 fixed games account for about 0.008 (their miss rises 1.06 points each) and the refit for the rest. The priced game's own id is where (a)'s effects come from: on the fixed games themselves (the column above) (a) is better on 2019-22 and much better on 2023-25 (43 games), where the listed QB never played, and worse on the 8 games of 2015-18, which are relief games whose listed id was the reliever who threw most (e.g. Kizer for Rodgers): the first-dropback QB is the better pre-game guess there, but the game was played by the backup. So nearly all of (a)'s gain on 2023-25 is the priced game's own id, and the strict version shows no gain.

Caveat on (a): the first dropback is the announced starter in nearly every game, but not all: a starter benched for the first series (2016 Wk 13 CAR, Derek Anderson for Newton's dress-code benching), a planned one-series start (2024 Wk 18 NE, Maye before Milton), a surprise late switch. A handful of team-games in thirteen seasons.

### The code change, if the fix is taken anyway (nothing was integrated)

nflmodel/build.py: correct the played games' ids from the play-by-play and keep nflverse's as `*_qb_id_listed`; unplayed games keep the
schedule's announced starter, and `ratings.build_features` needs no change (its `last_qb` then comes from the corrected played games).

```python
def first_dropback_qb(seasons) -> pd.DataFrame:
    """(game_id, team, qb_id): the QB on each team's first dropback (passer_id, which also carries scrambles). A passer whose roster
    position is not QB is skipped, so a fake punt or a receiver's trick pass is not a start (if no QB dropped back, the first passer)."""
    pos = {}
    for s in seasons:
        f = RAW / "rosters" / f"roster_weekly_{s}.parquet"
        if f.exists():
            r = pd.read_parquet(f, columns=["gsis_id", "position"]).dropna().drop_duplicates("gsis_id", keep="last")
            pos.update({(s, g): p for g, p in zip(r.gsis_id, r.position)})
    out = []
    for s in seasons:
        f = RAW / "pbp" / f"play_by_play_{s}.parquet"
        if not f.exists():
            continue
        p = pd.read_parquet(f, columns=["game_id", "play_id", "posteam", "qb_dropback", "passer_id"])
        p = p[p.posteam.notna() & (pd.to_numeric(p.qb_dropback, errors="coerce") == 1) & p.passer_id.notna()].sort_values(["game_id", "play_id"])
        p["posteam"] = p.posteam.replace(TEAM_FIX)
        p["qb"] = [pos.get((s, q), "QB") == "QB" for q in p.passer_id]
        fq = p[p.qb].groupby(["game_id", "posteam"]).passer_id.first()
        fa = p.groupby(["game_id", "posteam"]).passer_id.first()
        out.append(fq.reindex(fa.index).fillna(fa).rename("qb_id").rename_axis(["game_id", "team"]).reset_index())
    return pd.concat(out, ignore_index=True)


def fix_starters(g: pd.DataFrame, seasons) -> pd.DataFrame:
    """Played games: the first-dropback QB replaces nflverse's listed id (wrong in 45 team-games 2022-2026, reports/qb_id_fix.md)."""
    fq = first_dropback_qb(seasons).set_index(["game_id", "team"]).qb_id
    for side in ("home", "away"):
        g[f"{side}_qb_id_listed"] = g[f"{side}_qb_id"]
        new = pd.Series([fq.get((k, t)) for k, t in zip(g.game_id, g[f"{side}_team"])], index=g.index)
        m = g.home_score.notna() & new.notna()
        g.loc[m, f"{side}_qb_id"] = new[m]
    return g

# in __main__, after games = build_games():
    games = fix_starters(games, seasons)
```

In the backtest this is variant (a) for every priced game (a played game's own first dropback); live it is the strict variant (the week being priced
is unplayed and keeps the announced starter). The strict variant in the backtest would also need `build_features` to carry the listed id's rating for
the priced row (e.g. a `qb_rating_listed` column that `walk_forward` swaps in for the test rows), which is more than a data fix.

## Runtimes

- build_features listed (load avg ~7): 224
- build_features first: 244
- build_features most: 156
- walk_forward base (listed ids, today): 107
- walk_forward (a) first-dropback QB, every played game: 216
- walk_forward (b) most-dropbacks QB, every played game: 207
- walk_forward strict: first-dropback QB for earlier games, priced game listed: 118
- total (first full run): 1305
- audit: 15.0
- check vs features_asof: max diff: 8.038014698286133e-14
- split walk_forward check (max |spread diff|, 2024): 0.0
- total (this run): 27.2
