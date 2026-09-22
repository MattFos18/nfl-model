# Analysis lab

## Stat correlations: through Week 8 vs points per game in Weeks 9 to 17 (2012 to 2025 average)

predictive_r = correlation of the stat through Week 8 with future points; same_season_r = with points over the same weeks (what the old sheet measured). 'drop' is how much of the same-season correlation disappears when you ask the stat to predict.

| stat               | target   |   predictive_r |   same_season_r |   seasons |   drop |
|:-------------------|:---------|---------------:|----------------:|----------:|-------:|
| pa                 | pa       |          0.262 |           1     |        14 |  0.738 |
| def_td_rate        | pa       |          0.214 |           0.841 |        14 |  0.627 |
| def_explosive_rate | pa       |          0.211 |           0.479 |        14 |  0.268 |
| def_epa_play_ng    | pa       |          0.21  |           0.725 |        14 |  0.515 |
| def_score_rate     | pa       |          0.197 |           0.829 |        14 |  0.632 |
| def_yards_play     | pa       |          0.196 |           0.685 |        14 |  0.489 |
| def_epa_play       | pa       |          0.196 |           0.807 |        14 |  0.611 |
| def_pass_epa       | pa       |          0.192 |           0.796 |        14 |  0.604 |
| def_early_down_epa | pa       |          0.187 |           0.663 |        14 |  0.476 |
| def_avg_start_ytg  | pa       |         -0.179 |          -0.46  |        14 |  0.28  |
| def_int_rate       | pa       |         -0.143 |          -0.38  |        14 |  0.237 |
| def_rz_td_rate     | pa       |          0.121 |           0.394 |        14 |  0.273 |
| def_turnover_rate  | pa       |         -0.119 |          -0.443 |        14 |  0.324 |
| def_success        | pa       |          0.116 |           0.554 |        14 |  0.439 |
| def_rush_epa       | pa       |          0.097 |           0.359 |        14 |  0.262 |
| def_sack_rate      | pa       |         -0.084 |          -0.44  |        14 |  0.356 |
| def_third_conv     | pa       |          0.084 |           0.497 |        14 |  0.413 |
| epa_play           | pf       |          0.502 |           0.86  |        14 |  0.358 |
| pf                 | pf       |          0.492 |           1     |        14 |  0.508 |
| pass_epa           | pf       |          0.489 |           0.814 |        14 |  0.326 |
| success_ng         | pf       |          0.465 |           0.734 |        14 |  0.269 |
| epa_play_ng        | pf       |          0.463 |           0.79  |        14 |  0.328 |
| early_down_epa     | pf       |          0.451 |           0.768 |        14 |  0.318 |
| td_rate            | pf       |          0.448 |           0.883 |        14 |  0.435 |
| score_rate         | pf       |          0.447 |           0.837 |        14 |  0.391 |
| success            | pf       |          0.446 |           0.7   |        14 |  0.253 |
| yards_play         | pf       |          0.442 |           0.765 |        14 |  0.323 |
| pass_epa_ng        | pf       |          0.432 |           0.744 |        14 |  0.312 |
| early_down_success | pf       |          0.399 |           0.601 |        14 |  0.203 |
| third_conv         | pf       |          0.354 |           0.601 |        14 |  0.247 |
| explosive_rate     | pf       |          0.33  |           0.57  |        14 |  0.24  |
| cpoe               | pf       |          0.315 |           0.527 |        14 |  0.212 |
| rush_success       | pf       |          0.293 |           0.415 |        14 |  0.122 |
| rush_epa           | pf       |          0.274 |           0.476 |        14 |  0.202 |
| turnover_rate      | pf       |         -0.262 |          -0.397 |        14 |  0.135 |
| avg_start_ytg      | pf       |         -0.26  |          -0.444 |        14 |  0.184 |
| sack_rate          | pf       |         -0.243 |          -0.427 |        14 |  0.184 |
| int_rate           | pf       |         -0.241 |          -0.377 |        14 |  0.135 |
| pass_rate          | pf       |         -0.197 |          -0.268 |        14 |  0.071 |
| drive_to_rate      | pf       |         -0.195 |          -0.328 |        14 |  0.133 |
| rz_td_rate         | pf       |          0.193 |           0.466 |        14 |  0.272 |
| rz_epa             | pf       |          0.171 |           0.452 |        14 |  0.281 |
| pass_oe            | pf       |          0.125 |           0.262 |        14 |  0.137 |
| sec_per_play       | pf       |          0.123 |           0.231 |        14 |  0.108 |
| plays              | pf       |          0.094 |           0.224 |        14 |  0.13  |
| drives             | pf       |         -0.092 |          -0.01  |        14 | -0.082 |
| air_yards_att      | pf       |          0.078 |           0.116 |        14 |  0.038 |

## Reliability: split-half correlation within a season (odd vs even games)

| stat               |   split_half_r |
|:-------------------|---------------:|
| pass_oe            |          0.687 |
| epa_play           |          0.58  |
| success            |          0.559 |
| pass_epa           |          0.544 |
| td_rate            |          0.542 |
| pf                 |          0.54  |
| success_ng         |          0.536 |
| yards_play         |          0.532 |
| sec_per_play       |          0.532 |
| epa_play_ng        |          0.518 |
| early_down_epa     |          0.503 |
| score_rate         |          0.5   |
| air_yards_att      |          0.499 |
| cpoe               |          0.489 |
| pass_epa_ng        |          0.485 |
| pass_rate          |          0.476 |
| early_down_success |          0.468 |
| sack_rate          |          0.46  |
| explosive_rate     |          0.374 |
| def_success        |          0.36  |
| third_conv         |          0.351 |
| def_yards_play     |          0.335 |
| plays              |          0.332 |
| def_epa_play       |          0.317 |
| pa                 |          0.307 |
| def_explosive_rate |          0.29  |
| rush_success       |          0.277 |
| drives             |          0.27  |
| def_epa_play_ng    |          0.267 |
| def_early_down_epa |          0.262 |
| def_score_rate     |          0.255 |
| rush_epa           |          0.253 |
| def_pass_epa       |          0.246 |
| def_td_rate        |          0.215 |
| def_avg_start_ytg  |          0.215 |
| def_turnover_rate  |          0.201 |
| avg_start_ytg      |          0.2   |
| def_rush_epa       |          0.194 |
| int_rate           |          0.169 |
| turnover_rate      |          0.165 |
| def_int_rate       |          0.163 |
| def_third_conv     |          0.121 |
| def_sack_rate      |          0.111 |
| rz_epa             |          0.094 |
| drive_to_rate      |          0.077 |
| def_rz_td_rate     |          0.053 |
| rz_td_rate         |          0.043 |
