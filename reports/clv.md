# Closing line value, 2026

Each live bet's consensus line when the game first flagged for that side (the tracker row where no run history exists, marked) against the consensus at the last lines-log snapshot before kickoff (nflmodel/clv.py). line_best is the best-book number the spread flag was recorded at, shown apart; CLV uses the consensus line. Positive CLV means the bet beat the close. Grading only: nothing here changes a rule or a pick.

| Rule | Closed bets | Avg CLV (pts) | Beat the close | Same | Worse | Pending | Avg CLV (no-vig prob) |
|---|---|---|---|---|---|---|---|
| Spreads, 4+ edge | 0 |  |  | 0 | 0 | 3 |  |
| Unders, 55%+ chance | 3 | +0.33 | 33% | 2 | 0 | 4 | +0.0% (2) |
| Wind unders, 10+ mph | 1 | +0.00 | 0% | 1 | 0 | 0 | +0.0% (1) |
| All live bets | 4 | +0.25 | 25% | 3 | 0 | 7 | +0.0% (3) |

## Every bet

| rule        |   week | game_id         | bet        | taken_at             | taken_from   |   line |   line_best |   close |   clv_pts | clv_prob   | close_ts             | status   |
|:------------|-------:|:----------------|:-----------|:---------------------|:-------------|-------:|------------:|--------:|----------:|:-----------|:---------------------|:---------|
| model       |      4 | 2026_04_IND_WAS | WAS +4.5   | 2026-09-27 20:12 UTC | first flag   |    4.5 |         4.5 |   nan   |       nan |            | nan                  | pending  |
| model       |      4 | 2026_04_JAX_CIN | JAX +2.5   | 2026-09-27 20:41 UTC | first flag   |    3   |         2.5 |   nan   |       nan |            | nan                  | pending  |
| model       |      4 | 2026_04_ARI_NYG | NYG +2.5   | 2026-09-29 14:19 UTC | first flag   |    1.5 |         2.5 |   nan   |       nan |            | nan                  | pending  |
| shadowunder |      3 | 2026_03_LAC_BUF | Under 50.5 | 2026-09-27 16:15 UTC | tracker row  |   50.5 |       nan   |    50.5 |         0 | +0.0%      | 2026-09-27 16:21 UTC | closed   |
| shadowunder |      3 | 2026_03_NE_JAX  | Under 46.5 | 2026-09-27 16:15 UTC | tracker row  |   46.5 |       nan   |    46.5 |         0 | +0.0%      | 2026-09-27 16:21 UTC | closed   |
| shadowunder |      3 | 2026_03_LA_DEN  | Under 44.5 | 2026-09-27 23:16 UTC | tracker row  |   44.5 |       nan   |    43.5 |         1 |            | 2026-09-28 00:12 UTC | closed   |
| shadowunder |      4 | 2026_04_NE_BUF  | Under 49.5 | 2026-10-02 05:35 UTC | first flag   |   48.5 |       nan   |   nan   |       nan |            | nan                  | pending  |
| shadowunder |      4 | 2026_04_ARI_NYG | Under 44.5 | 2026-10-02 05:35 UTC | first flag   |   44.5 |       nan   |   nan   |       nan |            | nan                  | pending  |
| shadowunder |      4 | 2026_04_LA_PHI  | Under 42.5 | 2026-10-02 05:35 UTC | first flag   |   42.5 |       nan   |   nan   |       nan |            | nan                  | pending  |
| shadowunder |      4 | 2026_04_DET_CAR | Under 50.5 | 2026-10-02 11:57 UTC | first flag   |   51   |       nan   |   nan   |       nan |            | nan                  | pending  |
| windunder   |      4 | 2026_04_PIT_CLE | Under 38.5 | 2026-10-01 23:22 UTC | tracker row  |   38.5 |       nan   |    38.5 |         0 | +0.0%      | 2026-10-02 00:12 UTC | closed   |
