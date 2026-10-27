# Closing line value, 2026

Each live bet's consensus line when the game first flagged for that side (the tracker row where no run history exists, marked) against the consensus at the last lines-log snapshot before kickoff (nflmodel/clv.py). line_best is the best-book number the spread flag was recorded at, shown apart; CLV uses the consensus line. Positive CLV means the bet beat the close. Grading only: nothing here changes a rule or a pick.

| Rule | Closed bets | Avg CLV (pts) | Beat the close | Same | Worse | Pending | Avg CLV (no-vig prob) |
|---|---|---|---|---|---|---|---|
| Spreads, 4+ edge | 5 | +0.20 | 40% | 2 | 1 | 1 | -1.3% (2) |
| Unders, 55%+ chance | 17 | -0.26 | 12% | 8 | 7 | 2 | -0.3% (8) |
| Wind unders, 10+ mph | 8 | -0.12 | 25% | 4 | 2 | 0 | -0.2% (4) |
| All live bets | 30 | -0.15 | 20% | 14 | 10 | 3 | -0.4% (14) |

## Every bet

| rule        |   week | game_id         | bet        | taken_at             | taken_from   |   line |   line_best |   close |   clv_pts | clv_prob   | close_ts             | status   |
|:------------|-------:|:----------------|:-----------|:---------------------|:-------------|-------:|------------:|--------:|----------:|:-----------|:---------------------|:---------|
| model       |      4 | 2026_04_IND_WAS | WAS +4.5   | 2026-09-27 20:12 UTC | first flag   |    4.5 |         4.5 |     4.5 |       0   | -1.4%      | 2026-10-04 13:03 UTC | closed   |
| model       |      4 | 2026_04_JAX_CIN | JAX +2.5   | 2026-09-27 20:41 UTC | first flag   |    3   |         2.5 |     2.5 |       0.5 |            | 2026-10-04 16:56 UTC | closed   |
| model       |      4 | 2026_04_ARI_NYG | NYG +2.5   | 2026-09-29 14:19 UTC | first flag   |    1.5 |         2.5 |     2.5 |      -1   |            | 2026-10-04 16:56 UTC | closed   |
| model       |      6 | 2026_06_CHI_ATL | ATL +1.5   | 2026-10-13 14:29 UTC | first flag   |    3   |         1.5 |     1.5 |       1.5 |            | 2026-10-18 16:58 UTC | closed   |
| model       |      7 | 2026_07_CIN_BAL | BAL +1.5   | 2026-10-21 19:17 UTC | first flag   |    1.5 |         1.5 |     1.5 |       0   | -1.1%      | 2026-10-24 17:12 UTC | closed   |
| model       |      8 | 2026_08_KC_DEN  | DEN +1.5   | 2026-10-27 15:42 UTC | first flag   |    1.5 |         1.5 |   nan   |     nan   |            | nan                  | pending  |
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
| shadowunder |      6 | 2026_06_CHI_ATL | Under 51.5 | 2026-10-13 14:29 UTC | first flag   |   49.5 |       nan   |    51.5 |      -2   |            | 2026-10-18 16:58 UTC | closed   |
| shadowunder |      6 | 2026_06_NO_NYG  | Under 46.5 | 2026-10-13 14:29 UTC | first flag   |   45.5 |       nan   |    46.5 |      -1   |            | 2026-10-18 16:58 UTC | closed   |
| shadowunder |      6 | 2026_06_DAL_GB  | Under 53.5 | 2026-10-14 15:24 UTC | first flag   |   53.5 |       nan   |    54.5 |      -1   |            | 2026-10-19 00:19 UTC | closed   |
| shadowunder |      7 | 2026_07_NE_CHI  | Under 51   | 2026-10-20 14:25 UTC | first flag   |   50.5 |       nan   |    51   |      -0.5 |            | 2026-10-22 21:26 UTC | closed   |
| shadowunder |      7 | 2026_07_PIT_NO  | Under 44.5 | 2026-10-20 14:25 UTC | first flag   |   44.5 |       nan   |    44.5 |       0   | -0.4%      | 2026-10-24 17:12 UTC | closed   |
| shadowunder |      7 | 2026_07_GB_DET  | Under 55.5 | 2026-10-25 16:57 UTC | first flag   |   55.5 |       nan   |    55.5 |       0   | +0.0%      | 2026-10-25 17:02 UTC | closed   |
| shadowunder |      8 | 2026_08_ATL_TB  | Under 46.5 | 2026-10-27 15:42 UTC | first flag   |   46.5 |       nan   |   nan   |     nan   |            | nan                  | pending  |
| shadowunder |      8 | 2026_08_CHI_SEA | Under 46.5 | 2026-10-27 15:42 UTC | first flag   |   46.5 |       nan   |   nan   |     nan   |            | nan                  | pending  |
| windunder   |      4 | 2026_04_PIT_CLE | Under 38.5 | 2026-10-01 23:22 UTC | tracker row  |   38.5 |       nan   |    38.5 |       0   | +0.0%      | 2026-10-02 00:12 UTC | closed   |
| windunder   |      4 | 2026_04_NE_BUF  | Under 49.5 | 2026-10-03 23:00 UTC | first flag   |   49.5 |       nan   |    49.5 |       0   | +0.9%      | 2026-10-04 16:56 UTC | closed   |
| windunder   |      5 | 2026_05_CHI_GB  | Under 47.5 | 2026-10-09 10:49 UTC | first flag   |   45.5 |       nan   |    47.5 |      -2   |            | 2026-10-11 16:13 UTC | closed   |
| windunder   |      5 | 2026_05_CIN_MIA | Under 44.5 | 2026-10-08 23:06 UTC | first flag   |   42.5 |       nan   |    44.5 |      -2   |            | 2026-10-11 16:13 UTC | closed   |
| windunder   |      5 | 2026_05_CLE_NYJ | Under 38.5 | 2026-10-08 23:06 UTC | first flag   |   39.5 |       nan   |    38.5 |       1   |            | 2026-10-11 16:13 UTC | closed   |
| windunder   |      6 | 2026_06_SEA_DEN | Under 40.5 | 2026-10-13 15:30 UTC | first flag   |   40.5 |       nan   |    40.5 |       0   | +0.0%      | 2026-10-15 23:59 UTC | closed   |
| windunder   |      6 | 2026_06_PIT_TB  | Under 38.5 | 2026-10-15 23:07 UTC | first flag   |   39.5 |       nan   |    37.5 |       2   |            | 2026-10-18 16:58 UTC | closed   |
| windunder   |      6 | 2026_06_LAC_KC  | Under 41.5 | 2026-10-16 16:23 UTC | first flag   |   41.5 |       nan   |    41.5 |       0   | -1.5%      | 2026-10-18 19:53 UTC | closed   |
