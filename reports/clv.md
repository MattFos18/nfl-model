# Closing line value, 2026

Each live bet's consensus line when the game first flagged for that side (the tracker row where no run history exists, marked) against the consensus at the last lines-log snapshot before kickoff (nflmodel/clv.py). line_best is the best-book number the spread flag was recorded at, shown apart; CLV uses the consensus line. Positive CLV means the bet beat the close. Grading only: nothing here changes a rule or a pick.

| Rule | Closed bets | Avg CLV (pts) | Beat the close | Same | Worse | Pending | Avg CLV (no-vig prob) |
|---|---|---|---|---|---|---|---|
| Spreads, 4+ edge | 3 | -0.17 | 33% | 1 | 1 | 2 | -1.4% (1) |
| Unders, 55%+ chance | 11 | +0.00 | 18% | 6 | 3 | 3 | -0.3% (6) |
| Wind unders, 10+ mph | 6 | -0.50 | 17% | 3 | 2 | 3 | +0.3% (3) |
| All live bets | 20 | -0.17 | 20% | 10 | 6 | 8 | -0.2% (10) |

## Every bet

| rule        |   week | game_id         | bet        | taken_at             | taken_from   |   line |   line_best |   close |   clv_pts | clv_prob   | close_ts             | status   |
|:------------|-------:|:----------------|:-----------|:---------------------|:-------------|-------:|------------:|--------:|----------:|:-----------|:---------------------|:---------|
| model       |      4 | 2026_04_IND_WAS | WAS +4.5   | 2026-09-27 20:12 UTC | first flag   |    4.5 |         4.5 |     4.5 |       0   | -1.4%      | 2026-10-04 13:03 UTC | closed   |
| model       |      4 | 2026_04_JAX_CIN | JAX +2.5   | 2026-09-27 20:41 UTC | first flag   |    3   |         2.5 |     2.5 |       0.5 |            | 2026-10-04 16:56 UTC | closed   |
| model       |      4 | 2026_04_ARI_NYG | NYG +2.5   | 2026-09-29 14:19 UTC | first flag   |    1.5 |         2.5 |     2.5 |      -1   |            | 2026-10-04 16:56 UTC | closed   |
| model       |      6 | 2026_06_CHI_ATL | ATL +1.5   | 2026-10-13 14:29 UTC | first flag   |    3   |         1.5 |   nan   |     nan   |            | nan                  | pending  |
| model       |      6 | 2026_06_CAR_PHI | PHI +3     | 2026-10-13 18:09 UTC | first flag   |   -1.5 |         3   |   nan   |     nan   |            | nan                  | pending  |
| shadowunder |      3 | 2026_03_LAC_BUF | Under 50.5 | 2026-09-27 16:15 UTC | tracker row  |   50.5 |       nan   |    50.5 |       0   | +0.0%      | 2026-09-27 16:21 UTC | closed   |
| shadowunder |      3 | 2026_03_NE_JAX  | Under 46.5 | 2026-09-27 16:15 UTC | tracker row  |   46.5 |       nan   |    46.5 |       0   | +0.0%      | 2026-09-27 16:21 UTC | closed   |
| shadowunder |      3 | 2026_03_LA_DEN  | Under 44.5 | 2026-09-27 23:16 UTC | tracker row  |   44.5 |       nan   |    43.5 |       1   |            | 2026-09-28 00:12 UTC | closed   |
| shadowunder |      4 | 2026_04_NE_BUF  | Under 49.5 | 2026-10-02 05:35 UTC | first flag   |   48.5 |       nan   |    49.5 |      -1   |            | 2026-10-04 16:56 UTC | closed   |
| shadowunder |      4 | 2026_04_JAX_CIN | Under 51.5 | 2026-10-02 18:08 UTC | first flag   |   51.5 |       nan   |    51.5 |       0   | -1.7%      | 2026-10-04 16:56 UTC | closed   |
| shadowunder |      5 | 2026_05_CHI_GB  | Under 47.5 | 2026-10-07 17:10 UTC | first flag   |   45.5 |       nan   |    47.5 |      -2   |            | 2026-10-11 16:13 UTC | closed   |
| shadowunder |      5 | 2026_05_LV_NE   | Under 45.5 | 2026-10-06 16:28 UTC | first flag   |   45.5 |       nan   |    45.5 |       0   | +0.0%      | 2026-10-11 16:13 UTC | closed   |
| shadowunder |      5 | 2026_05_IND_PIT | Under 41.5 | 2026-10-06 16:28 UTC | first flag   |   44.5 |       nan   |    41.5 |       3   |            | 2026-10-11 16:13 UTC | closed   |
| shadowunder |      5 | 2026_05_DET_ARI | Under 55.5 | 2026-10-11 18:38 UTC | first flag   |   55.5 |       nan   |    55.5 |       0   | +0.0%      | 2026-10-11 20:06 UTC | closed   |
| shadowunder |      5 | 2026_05_BUF_LA  | Under 55.5 | 2026-10-06 16:28 UTC | first flag   |   54.5 |       nan   |    55.5 |      -1   |            | 2026-10-13 00:09 UTC | closed   |
| shadowunder |      6 | 2026_06_SEA_DEN | Under 40.5 | 2026-10-13 14:29 UTC | first flag   |   40.5 |       nan   |    40.5 |       0   | +0.0%      | 2026-10-15 23:59 UTC | closed   |
| shadowunder |      6 | 2026_06_CHI_ATL | Under 51.5 | 2026-10-13 14:29 UTC | first flag   |   49.5 |       nan   |   nan   |     nan   |            | nan                  | pending  |
| shadowunder |      6 | 2026_06_NO_NYG  | Under 46.5 | 2026-10-13 14:29 UTC | first flag   |   45.5 |       nan   |   nan   |     nan   |            | nan                  | pending  |
| shadowunder |      6 | 2026_06_DAL_GB  | Under 53.5 | 2026-10-14 15:24 UTC | first flag   |   53.5 |       nan   |   nan   |     nan   |            | nan                  | pending  |
| windunder   |      4 | 2026_04_PIT_CLE | Under 38.5 | 2026-10-01 23:22 UTC | tracker row  |   38.5 |       nan   |    38.5 |       0   | +0.0%      | 2026-10-02 00:12 UTC | closed   |
| windunder   |      4 | 2026_04_NE_BUF  | Under 49.5 | 2026-10-03 23:00 UTC | first flag   |   49.5 |       nan   |    49.5 |       0   | +0.9%      | 2026-10-04 16:56 UTC | closed   |
| windunder   |      5 | 2026_05_CHI_GB  | Under 47.5 | 2026-10-09 10:49 UTC | first flag   |   45.5 |       nan   |    47.5 |      -2   |            | 2026-10-11 16:13 UTC | closed   |
| windunder   |      5 | 2026_05_CIN_MIA | Under 44.5 | 2026-10-08 23:06 UTC | first flag   |   42.5 |       nan   |    44.5 |      -2   |            | 2026-10-11 16:13 UTC | closed   |
| windunder   |      5 | 2026_05_CLE_NYJ | Under 38.5 | 2026-10-08 23:06 UTC | first flag   |   39.5 |       nan   |    38.5 |       1   |            | 2026-10-11 16:13 UTC | closed   |
| windunder   |      6 | 2026_06_SEA_DEN | Under 40.5 | 2026-10-13 15:30 UTC | first flag   |   40.5 |       nan   |    40.5 |       0   | +0.0%      | 2026-10-15 23:59 UTC | closed   |
| windunder   |      6 | 2026_06_CAR_PHI | Under 39.5 | 2026-10-16 10:55 UTC | first flag   |   38.5 |       nan   |   nan   |     nan   |            | nan                  | pending  |
| windunder   |      6 | 2026_06_PIT_TB  | Under 39.5 | 2026-10-15 23:07 UTC | first flag   |   39.5 |       nan   |   nan   |     nan   |            | nan                  | pending  |
| windunder   |      6 | 2026_06_LAC_KC  | Under 41.5 | 2026-10-16 16:23 UTC | first flag   |   41.5 |       nan   |   nan   |     nan   |            | nan                  | pending  |
