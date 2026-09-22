# Backtest audit

## 1. Leakage test

Every game from Week 10 of 2024 onward was corrupted (EPA flipped, 20 points added, QB EPA set to -50, results changed) and the ratings for 2024 Weeks 1 to 9 rebuilt. Then the 2024 regression was refit with 2024-onward targets corrupted.

- Rating rows compared: 276; largest change in any rating: 0.000000
- Largest change in any 2024 prediction: 0.000000

A zero means nothing after a game reaches the numbers used to predict it.

## 2. Coverage

|                                |   value |
|:-------------------------------|--------:|
| regular_season_games_2019_2025 |    1871 |
| graded_v3                      |    1871 |
| graded_old                     |    1871 |
| duplicates_v3                  |       0 |
| same_games                     |    True |
| games_without_closing_spread   |       0 |

## 3. How sure the keep/drop decisions are

For each rejected input, the change in team points miss when it is added to the locked model (negative = it would help), with a paired bootstrap 90% interval over games, on the tuning window and the held-out window, and the ATS record at a 5 point edge with it added. base ATS at 5+: tune 48-40 (+0.041), test 29-18 (+0.178).

| input                                  |   tune_delta_mae |   tune_90pct_lo |   tune_90pct_hi | tune_ats5      |   test_delta_mae |   test_90pct_lo |   test_90pct_hi | test_ats5      |
|:---------------------------------------|-----------------:|----------------:|----------------:|:---------------|-----------------:|----------------:|----------------:|:---------------|
| team home edge                         |           0.0008 |         -0.0023 |          0.0041 | 48-40 (+0.041) |           0.0004 |         -0.0006 |          0.0014 | 29-18 (+0.178) |
| head-to-head                           |           0.0052 |         -0.0032 |          0.0139 | 49-41 (+0.039) |          -0.008  |         -0.0179 |          0.0016 | 26-19 (+0.103) |
| coach ATS                              |          -0.0059 |         -0.0199 |          0.0076 | 51-44 (+0.025) |           0.0087 |         -0.0043 |          0.0227 | 22-17 (+0.077) |
| QB ATS                                 |           0.0098 |         -0.0037 |          0.0234 | 50-37 (+0.097) |          -0.0038 |         -0.0159 |          0.0091 | 27-18 (+0.145) |
| off a loss                             |           0.0001 |         -0.0013 |          0.0014 | 47-38 (+0.056) |           0.0018 |         -0      |          0.0038 | 29-18 (+0.178) |
| referee over/under                     |          -0.0027 |         -0.0173 |          0.0115 | 47-39 (+0.043) |           0.0053 |         -0.0048 |          0.0159 | 29-18 (+0.178) |
| referee home cover                     |          -0.0041 |         -0.0111 |          0.0027 | 48-40 (+0.041) |          -0.0013 |         -0.0076 |          0.0053 | 29-18 (+0.178) |
| referee penalties                      |          -0.0032 |         -0.0149 |          0.0081 | 48-40 (+0.041) |           0.0036 |         -0.0015 |          0.0087 | 29-18 (+0.178) |
| late slot / body clock                 |           0.0053 |          0.0013 |          0.0093 | 48-42 (+0.018) |           0.0015 |         -0.0015 |          0.0048 | 29-19 (+0.153) |
| cold and wind team edges               |           0.0021 |         -0.0006 |          0.005  | 51-39 (+0.082) |          -0.0009 |         -0.0037 |          0.0019 | 30-18 (+0.193) |
| home/away EPA split                    |           0.002  |         -0.001  |          0.005  | 48-40 (+0.041) |           0.0006 |         -0.0009 |          0.0019 | 28-18 (+0.162) |
| injuries: starters out                 |          -0.0035 |         -0.0121 |          0.0051 | 40-37 (-0.008) |           0.0043 |         -0.0057 |          0.0141 | 28-19 (+0.137) |
| primetime                              |           0.001  |         -0.0014 |          0.0035 | 48-40 (+0.041) |          -0.0035 |         -0.0101 |          0.0032 | 29-18 (+0.178) |
| division game                          |           0      |          0      |          0      | 48-40 (+0.041) |           0      |          0      |          0      | 29-18 (+0.178) |
| rest: short week and bye (both teams)  |           0.0122 |          0.0044 |          0.02   | 49-42 (+0.028) |           0.0013 |         -0.0044 |          0.0067 | 27-17 (+0.171) |
| snow                                   |           0.0046 |         -0.0028 |          0.0119 | 48-40 (+0.041) |          -0.0033 |         -0.0104 |          0.004  | 29-18 (+0.178) |
| travel distance (miles)                |          -0.0011 |         -0.0051 |          0.0032 | 50-38 (+0.085) |           0.0006 |         -0.0049 |          0.0064 | 24-20 (+0.041) |
| time-zone shift (hours)                |           0.0017 |          0.0008 |          0.0025 | 48-40 (+0.041) |           0.0003 |         -0.0005 |          0.0012 | 29-18 (+0.178) |
| West Coast team at 1pm ET              |           0.0034 |          0.0003 |          0.0067 | 48-42 (+0.018) |           0.0006 |         -0.0002 |          0.0015 | 29-18 (+0.178) |
| pass/rush EPA split                    |          -0.0023 |         -0.0106 |          0.0058 | 45-39 (+0.023) |          -0.0132 |         -0.0272 |          0.0006 | 24-19 (+0.066) |
| pace (plays per game)                  |          -0.0096 |         -0.0234 |          0.0041 | 49-42 (+0.028) |           0.0148 |          0.0018 |          0.0285 | 24-18 (+0.091) |
| opponent QB and other side of the ball |           0.002  |         -0.0199 |          0.0222 | 36-30 (+0.041) |          -0.008  |         -0.0323 |          0.0152 | 27-21 (+0.074) |
| success rate (dropped)                 |           0.0168 |          0.0008 |          0.0318 | 50-41 (+0.049) |           0.0014 |         -0.01   |          0.0129 | 30-17 (+0.219) |

An interval that includes zero means the data cannot tell the input apart from nothing. None of the rejected inputs has an interval entirely below zero on both windows.

## 4. Rejected ideas as standalone betting signals, 2019 to 2025

Bet the side each trend favours (top or bottom quartile of the as-of reading) against the closing line. Break-even is 52.4%.

| signal                                                       |   bets |   win_pct |    roi | 2019-22         | 2023-25         |
|:-------------------------------------------------------------|-------:|----------:|-------:|:----------------|:----------------|
| team home edge, home team in top quartile (bet the team)     |    458 |     0.485 | -0.075 | 96-106 (0.475)  | 126-130 (0.492) |
| team home edge, home team in bottom quartile (fade the team) |    451 |     0.488 | -0.069 | 161-159 (0.503) | 59-72 (0.450)   |
| head-to-head, top quartile (bet the team)                    |    913 |     0.504 | -0.038 | 262-262 (0.500) | 198-191 (0.509) |
| head-to-head, bottom quartile (fade the team)                |    913 |     0.504 | -0.038 | 262-262 (0.500) | 198-191 (0.509) |
| coach ATS, top quartile (bet the team)                       |    915 |     0.493 | -0.059 | 261-278 (0.484) | 190-186 (0.505) |
| coach ATS, bottom quartile (fade the team)                   |    918 |     0.519 | -0.01  | 244-234 (0.510) | 232-208 (0.527) |
| QB ATS, top quartile (bet the team)                          |    916 |     0.496 | -0.054 | 300-306 (0.495) | 154-156 (0.497) |
| QB ATS, bottom quartile (fade the team)                      |    921 |     0.483 | -0.078 | 227-248 (0.478) | 218-228 (0.489) |
| cold-weather edge > 0 in a cold game (bet the team)          |    104 |     0.529 |  0.01  | 28-24 (0.538)   | 27-25 (0.519)   |
| cold-weather edge < 0 in a cold game (fade the team)         |     82 |     0.537 |  0.024 | 25-21 (0.543)   | 19-17 (0.528)   |
| wind edge > 0 in a windy game (bet the team)                 |    149 |     0.503 | -0.039 | 53-53 (0.500)   | 22-21 (0.512)   |
| wind edge < 0 in a windy game (fade the team)                |    119 |     0.504 | -0.037 | 36-36 (0.500)   | 24-23 (0.511)   |
| home/away split, top quartile (bet the team)                 |    922 |     0.483 | -0.079 | 278-283 (0.496) | 167-194 (0.463) |
| home/away split, bottom quartile (fade the team)             |    913 |     0.492 | -0.061 | 286-277 (0.508) | 163-187 (0.466) |
| team off a loss (bet it)                                     |   1823 |     0.501 | -0.044 | 510-514 (0.498) | 403-396 (0.504) |
| West Coast team at 1pm ET on the road (bet it)               |    186 |     0.565 |  0.078 | 57-43 (0.570)   | 48-38 (0.558)   |
| QB out (bet the team)                                        |    108 |     0.565 |  0.078 | 36-27 (0.571)   | 25-20 (0.556)   |
| QB out (fade the team)                                       |    108 |     0.435 | -0.169 | 27-36 (0.429)   | 20-25 (0.444)   |
| referee over rate top quartile, bet the over                 |    466 |     0.521 | -0.004 | 165-152 (0.521) | 78-71 (0.523)   |
| referee over rate bottom quartile, bet the under             |    462 |     0.543 |  0.037 | 151-117 (0.563) | 100-94 (0.515)  |
| referee home cover rate top quartile, bet the home side      |    457 |     0.499 | -0.048 | 139-141 (0.496) | 89-88 (0.503)   |
| referee home cover rate bottom quartile, bet the away side   |    459 |     0.501 | -0.043 | 115-112 (0.507) | 115-117 (0.496) |

## 5. Noise floor

The paired-bootstrap 90% intervals above are about plus or minus 0.007 points wide on the tuning window (largest 0.021) and 0.006 on the held-out window. A benefit smaller than that is invisible at this sample size: 2,110 team-games tuning, 1,632 held out. The only inputs whose effect clears it are the QB rating (+0.080 when dropped) and weather (+0.040). 'No benefit' for the rejected inputs therefore means: no benefit the data can detect, and in most cases a point estimate on the wrong side of zero. It is not a proof of zero; nothing on this sample can be.
