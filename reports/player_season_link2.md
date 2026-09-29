# Player season totals, round 3: the team link and age priors rerun on today's availability, and new as-of ideas (29 Sep 2026)

`experiments/player_season_link2.py`. The rule is `reports/round3_rule.md`, written before any result, followed as written: (1) lower season-total miss on every window, (3) beats its own within-season shuffle placebo on every window in at least 45 of 50 draws, (4) no market input, no look-ahead, no new data source, (5) the passing pieces rerun together must pass (1). Rule 2 (bet records) does not apply: season totals do not touch the game model.

## Set-up

- Rows: the harness cache `reports/player_season_rows.csv` (today's `player_season.project` with the availability logit; checked: a fresh build of 2019 week 5 from today's code matches it, same players True, max difference 0.0005) for 2016-25, plus 2015 built with the same code on 2014-15 plays read through `nflmodel.scheme.load_plays` (the loader behind scheme_plays.parquet) and the 2015 weekly roster with its team codes normalised. As-of weeks 1, 5, 9, 13 (2016 week 1 absent, as in the harness).
- Windows: **2015** (early, never used to choose anything; the only season before the fit window the plays reach), **2016-18** (fit window of AVAIL, BLEND, the availability logit and every fitted piece here), **2019-22**, **2023-25**. Rule 1 needs a lower miss on all four.
- Targets: the harness's actual totals count every game with week <= 18, which for 2015-2020 includes the wild-card round (week 18 of those seasons is a playoff week: a bug in `player_season.season_actuals`, see the note at the end). Every variant is scored on the harness target and on the regular-season-only total (**reg**); rule 1 must hold on both. The placebo is counted on both.
- Configs: **fixed** = today's AVAIL and BLEND unchanged (the code change is the variant alone); **refit** = AVAIL and BLEND refit on 2016-18 on the harness grids for the base and for each variant (the change then includes the refit constants).
- The miss is the mean absolute error of the season total (yards), all players projected at the as-of week, as-of weeks pooled. Gain = base miss - variant miss (positive = better).

## Base

| config | target | kind | AVAIL | BLEND | 2015 | 2016-18 | 2019-22 | 2023-25 |
|---|---|---|---|---|---|---|---|---|
| fixed | reg | rec | 0.7 | 0.25 | 117.9 | 111.9 | 121.3 | 120.5 |
| fixed | reg | rush | 0.675 | 0.25 | 135.4 | 142.1 | 145.3 | 140.0 |
| fixed | reg | pass | 0.625 | 0.5 | 516.9 | 485.3 | 568.4 | 602.9 |
| fixed | harness | rec | 0.7 | 0.25 | 121.0 | 115.0 | 123.1 | 120.5 |
| fixed | harness | rush | 0.675 | 0.25 | 139.0 | 147.3 | 148.1 | 140.0 |
| fixed | harness | pass | 0.625 | 0.5 | 526.7 | 507.8 | 575.8 | 602.9 |
| refit | reg | rec | 0.675 | 0.25 | 119.0 | 111.8 | 120.6 | 120.1 |
| refit | reg | rush | 0.65 | 0.25 | 135.6 | 141.8 | 145.3 | 140.5 |
| refit | reg | pass | 0.65 | 0.25 | 556.1 | 472.2 | 572.5 | 615.8 |
| refit | harness | rec | 0.7 | 0.25 | 121.0 | 115.0 | 123.1 | 120.5 |
| refit | harness | rush | 0.675 | 0.25 | 139.0 | 147.3 | 148.1 | 140.0 |
| refit | harness | pass | 0.675 | 0.25 | 553.6 | 495.9 | 584.2 | 620.5 |

Rows per window and kind: 2015 pass 121, 2015 rec 742, 2015 rush 265, 2016-18 pass 299, 2016-18 rec 2003, 2016-18 rush 749, 2019-22 pass 460, 2019-22 rec 3227, 2019-22 rush 1214, 2023-25 pass 335, 2023-25 rec 2268, 2023-25 rush 915

## Every variant, fixed config

Gains in yards of season-total miss, reg target / harness target. Worst week = the largest loss in any window x as-of week cell (reg target), and in any single season x as-of week (reg). Placebo = the lowest, over the four windows, of the share of the 50 shuffles the real gain beats (reg target); blank when rule 1 fails.

| kind | variant | 2015 | 2016-18 | 2019-22 | 2023-25 | worst window-week | worst season-week | placebo | verdict |
|---|---|---|---|---|---|---|---|---|---|
| rec | b25 | -0.03 / +0.00 | -0.05 / +0.01 | +0.29 / +0.35 | +0.22 / +0.22 | -0.36 (2015 wk5) | -0.65 (2016 wk9) |  | fail: rule 1 (2015, 2016-18 on reg) |
| rec | b50 | -0.17 / -0.11 | -0.19 / -0.08 | +0.44 / +0.53 | +0.26 / +0.26 | -1.04 (2015 wk5) | -1.49 (2016 wk9) |  | fail: rule 1 (2015, 2016-18) |
| rec | c25 | +0.09 / -0.04 | -0.02 / +0.04 | +0.04 / +0.02 | +0.06 / +0.06 | -0.23 (2016-18 wk9) | -0.57 (2019 wk9) |  | fail: rule 1 (2015, 2016-18) |
| rec | c50 | +0.12 / -0.13 | -0.11 / +0.01 | +0.03 / -0.01 | +0.06 / +0.06 | -0.57 (2016-18 wk9) | -1.24 (2019 wk9) |  | fail: rule 1 (2015, 2016-18, 2019-22) |
| rec | d | -0.47 / -0.62 | +0.06 / -0.06 | +0.21 / +0.08 | +0.20 / +0.20 | -1.15 (2015 wk1) | -1.15 (2015 wk1) |  | fail: rule 1 (2015, 2016-18) |
| rec | d_m | -0.01 / -0.03 | -0.05 / -0.07 | -0.10 / -0.12 | -0.03 / -0.03 | -0.18 (2019-22 wk1) | -0.25 (2022 wk1) |  | fail: rule 1 (2015, 2016-18, 2019-22, 2023-25) |
| rec | e_c25_d | -0.42 / -0.68 | +0.03 / -0.03 | +0.26 / +0.11 | +0.29 / +0.29 | -1.13 (2015 wk1) | -1.13 (2015 wk1) |  | fail: rule 1 (2015, 2016-18) |
| rec | e_c25_d_m | +0.07 / -0.08 | -0.07 / -0.03 | -0.06 / -0.10 | +0.04 / +0.04 | -0.27 (2016-18 wk9) | -0.58 (2019 wk9) |  | fail: rule 1 (2015, 2016-18, 2019-22) |
| rec | e_c50_d | -0.40 / -0.76 | -0.06 / -0.07 | +0.27 / +0.10 | +0.32 / +0.32 | -1.11 (2015 wk1) | -1.11 (2015 wk1) |  | fail: rule 1 (2015, 2016-18) |
| rec | e_c50_d_m | +0.09 / -0.17 | -0.16 / -0.06 | -0.07 / -0.12 | +0.04 / +0.04 | -0.59 (2016-18 wk9) | -1.23 (2019 wk9) |  | fail: rule 1 (2015, 2016-18, 2019-22) |
| rec | p2 | -1.78 / -2.35 | -0.20 / -0.73 | +1.03 / +0.70 | +1.22 / +1.22 | -3.29 (2016-18 wk1) | -3.42 (2018 wk1) |  | fail: rule 1 (2015, 2016-18) |
| rec | p2_all | -9.17 / -10.47 | -4.09 / -5.25 | -2.03 / -2.73 | -1.56 / -1.56 | -13.23 (2015 wk1) | -13.23 (2015 wk1) |  | fail: rule 1 (2015, 2016-18, 2019-22, 2023-25) |
| rec | p2+best1 | -1.78 / -2.35 | -0.20 / -0.73 | +1.03 / +0.70 | +1.22 / +1.22 | -3.29 (2016-18 wk1) | -3.42 (2018 wk1) |  | fail: rule 1 (2015, 2016-18) |
| rec | p2_all+best1 | -9.17 / -10.47 | -4.09 / -5.25 | -2.03 / -2.73 | -1.56 / -1.56 | -13.23 (2015 wk1) | -13.23 (2015 wk1) |  | fail: rule 1 (2015, 2016-18, 2019-22, 2023-25) |
| rec | sos | +0.16 / +0.15 | -0.01 / -0.01 | +0.07 / +0.05 | -0.06 / -0.06 | -0.15 (2023-25 wk1) | -0.21 (2024 wk1) |  | fail: rule 1 (2016-18, 2023-25) |
| rec | sos_h | +0.08 / +0.08 | -0.00 / -0.00 | +0.04 / +0.03 | -0.03 / -0.03 | -0.08 (2023-25 wk1) | -0.10 (2024 wk1) |  | fail: rule 1 (2016-18, 2023-25) |
| rec | coach25 | +0.07 / +0.07 | -0.06 / -0.04 | +0.00 / +0.02 | +0.06 / +0.06 | -0.12 (2016-18 wk5) | -0.38 (2016 wk5) |  | fail: rule 1 (2016-18) |
| rec | coach50 | +0.14 / +0.14 | -0.13 / -0.09 | -0.02 / -0.00 | +0.11 / +0.11 | -0.25 (2016-18 wk5) | -0.84 (2022 wk1) |  | fail: rule 1 (2016-18, 2019-22) |
| rec | comp25 | +0.66 / +0.69 | -0.56 / -0.49 | +0.35 / +0.23 | +0.41 / +0.41 | -1.94 (2016-18 wk1) | -3.26 (2018 wk1) |  | fail: rule 1 (2016-18) |
| rec | comp50 | +0.93 / +1.02 | -1.40 / -1.31 | +0.11 / -0.09 | +0.28 / +0.28 | -4.27 (2016-18 wk1) | -6.78 (2018 wk1) |  | fail: rule 1 (2016-18, 2019-22) |
| rec | recon | +0.56 / +0.55 | -0.53 / -0.37 | +0.73 / +0.71 | +0.44 / +0.44 | -1.71 (2016-18 wk1) | -3.59 (2018 wk1) |  | fail: rule 1 (2016-18) |
| rec | recon_h | +0.31 / +0.32 | -0.19 / -0.10 | +0.48 / +0.46 | +0.32 / +0.32 | -0.69 (2016-18 wk1) | -1.75 (2018 wk1) |  | fail: rule 1 (2016-18) |
| rush | b25 | +0.04 / -0.04 | +0.35 / +0.11 | -0.14 / -0.32 | +0.12 / +0.12 | -0.75 (2019-22 wk1) | -1.86 (2019 wk1) |  | fail: rule 1 (2015, 2019-22) |
| rush | b50 | -0.34 / -0.52 | +0.37 / -0.02 | -0.46 / -0.86 | -0.06 / -0.06 | -2.45 (2015 wk1) | -4.24 (2019 wk1) |  | fail: rule 1 (2015, 2016-18, 2019-22, 2023-25) |
| rush | c25 | +0.46 / +0.45 | +0.25 / +0.18 | +0.20 / +0.21 | +0.13 / +0.13 | -0.12 (2015 wk1) | -0.94 (2017 wk5) | 48% | fail: rule 3 (placebo: reg 2015, reg 2016-18, reg 2023-25, harness 2016-18, harness 2023-25) |
| rush | c50 | +0.83 / +0.81 | +0.26 / +0.14 | +0.35 / +0.40 | +0.20 / +0.20 | -0.25 (2015 wk1) | -2.15 (2017 wk5) | 60% | fail: rule 3 (placebo: reg 2016-18, reg 2023-25, harness 2016-18, harness 2023-25) |
| rush | d | -0.19 / -0.07 | -0.35 / -0.20 | +0.09 / +0.23 | +0.24 / +0.24 | -1.69 (2015 wk1) | -1.69 (2015 wk1) |  | fail: rule 1 (2015, 2016-18) |
| rush | d_m | -0.17 / -0.10 | -0.18 / -0.16 | +0.20 / +0.24 | +0.16 / +0.16 | -0.53 (2015 wk1) | -0.74 (2017 wk1) |  | fail: rule 1 (2015, 2016-18) |
| rush | e_c25_d | +0.27 / +0.37 | -0.07 / +0.02 | +0.29 / +0.44 | +0.42 / +0.42 | -1.81 (2015 wk1) | -1.81 (2015 wk1) |  | fail: rule 1 (2016-18 on reg) |
| rush | e_c25_d_m | +0.30 / +0.35 | +0.07 / +0.04 | +0.38 / +0.45 | +0.32 / +0.32 | -0.65 (2015 wk1) | -1.23 (2017 wk5) | 28% | fail: rule 3 (placebo: reg 2015, reg 2016-18, reg 2023-25, harness 2015, harness 2016-18, harness 2023-25) |
| rush | e_c50_d | +0.63 / +0.72 | -0.04 / -0.01 | +0.45 / +0.63 | +0.50 / +0.50 | -1.93 (2015 wk1) | -2.46 (2017 wk5) |  | fail: rule 1 (2016-18) |
| rush | e_c50_d_m | +0.67 / +0.70 | +0.07 / -0.03 | +0.54 / +0.63 | +0.41 / +0.41 | -0.77 (2015 wk1) | -2.39 (2017 wk5) |  | fail: rule 1 (2016-18 on harness) |
| rush | p2 | -0.56 / -0.76 | +0.53 / +0.44 | -0.57 / -0.50 | -0.57 / -0.57 | -1.48 (2015 wk13) | -5.55 (2025 wk1) |  | fail: rule 1 (2015, 2019-22, 2023-25) |
| rush | p2_all | -1.38 / -3.31 | -2.17 / -3.54 | -4.69 / -5.14 | -6.15 / -6.15 | -9.66 (2023-25 wk9) | -19.54 (2025 wk1) |  | fail: rule 1 (2015, 2016-18, 2019-22, 2023-25) |
| rush | p2+best1 | +0.31 / -0.03 | +0.54 / +0.34 | -0.17 / -0.06 | -0.51 / -0.51 | -1.36 (2019-22 wk1) | -5.15 (2025 wk1) |  | fail: rule 1 (2015, 2019-22, 2023-25) |
| rush | p2_all+best1 | -0.62 / -2.59 | -2.57 / -3.95 | -4.31 / -4.74 | -6.17 / -6.17 | -9.82 (2023-25 wk9) | -19.04 (2025 wk1) |  | fail: rule 1 (2015, 2016-18, 2019-22, 2023-25) |
| rush | sos | +0.14 / +0.14 | -0.08 / -0.06 | +0.06 / +0.05 | -0.11 / -0.11 | -0.24 (2023-25 wk5) | -0.35 (2017 wk5) |  | fail: rule 1 (2016-18, 2023-25) |
| rush | sos_h | +0.07 / +0.07 | -0.04 / -0.03 | +0.03 / +0.03 | -0.05 / -0.05 | -0.12 (2023-25 wk5) | -0.17 (2024 wk5) |  | fail: rule 1 (2016-18, 2023-25) |
| rush | coach25 | +0.03 / +0.03 | +0.03 / -0.03 | -0.19 / -0.19 | -0.12 / -0.12 | -0.65 (2019-22 wk1) | -2.10 (2021 wk1) |  | fail: rule 1 (2016-18, 2019-22, 2023-25) |
| rush | coach50 | -0.15 / -0.15 | +0.02 / -0.08 | -0.39 / -0.39 | -0.25 / -0.25 | -1.34 (2019-22 wk1) | -4.37 (2021 wk1) |  | fail: rule 1 (2015, 2016-18, 2019-22, 2023-25) |
| rush | comp25 | +1.30 / +1.39 | +0.55 / +0.32 | +0.05 / -0.12 | -0.14 / -0.14 | -1.62 (2019-22 wk1) | -7.73 (2019 wk1) |  | fail: rule 1 (2019-22, 2023-25) |
| rush | comp50 | +1.26 / +1.55 | +0.31 / -0.13 | -0.47 / -0.82 | -1.14 / -1.14 | -4.63 (2019-22 wk1) | -11.19 (2019 wk1) |  | fail: rule 1 (2016-18, 2019-22, 2023-25) |
| rush | recon | +1.91 / +1.84 | +0.96 / +0.45 | +0.38 / -0.01 | +0.02 / +0.02 | -1.44 (2019-22 wk1) | -8.47 (2019 wk1) |  | fail: rule 1 (2019-22 on harness) |
| rush | recon_h | +1.17 / +1.13 | +0.68 / +0.39 | +0.29 / +0.13 | +0.23 / +0.23 | -0.45 (2019-22 wk1) | -4.04 (2019 wk1) | 92% | fail: rule 3 (placebo: harness 2019-22) |
| pass | b25 | -1.39 / -1.11 | -1.24 / -1.06 | -0.54 / -0.40 | +2.13 / +2.13 | -6.43 (2015 wk5) | -12.43 (2022 wk1) |  | fail: rule 1 (2015, 2016-18, 2019-22) |
| pass | b50 | -3.09 / -2.27 | -2.97 / -2.50 | -2.13 / -1.61 | +3.94 / +3.94 | -13.13 (2015 wk5) | -25.70 (2022 wk1) |  | fail: rule 1 (2015, 2016-18, 2019-22) |
| pass | c25 | +1.13 / +1.31 | +0.01 / +0.88 | +0.35 / +0.46 | +0.31 / +0.31 | -1.36 (2016-18 wk9) | -6.29 (2016 wk5) | 20% | fail: rule 3 (placebo: reg 2019-22, reg 2023-25, harness 2019-22, harness 2023-25) |
| pass | c50 | +2.26 / +2.63 | -0.27 / +1.44 | +0.59 / +0.63 | +0.51 / +0.51 | -2.81 (2016-18 wk9) | -12.57 (2016 wk5) |  | fail: rule 1 (2016-18 on reg) |
| pass | d | -2.90 / -3.04 | +0.80 / -0.88 | +0.09 / -0.73 | +0.83 / +0.83 | -7.42 (2015 wk1) | -7.97 (2021 wk1) |  | fail: rule 1 (2015, 2016-18, 2019-22) |
| pass | d_m | -0.11 / -0.10 | -0.06 / -0.21 | -0.56 / -0.75 | -0.04 / -0.04 | -1.48 (2019-22 wk5) | -1.85 (2021 wk1) |  | fail: rule 1 (2015, 2016-18, 2019-22, 2023-25) |
| pass | e_c25_d | -1.77 / -1.73 | +0.90 / -0.06 | +0.37 / -0.38 | +1.18 / +1.18 | -6.24 (2015 wk1) | -9.06 (2021 wk1) |  | fail: rule 1 (2015, 2016-18, 2019-22) |
| pass | e_c25_d_m | +1.02 / +1.21 | -0.05 / +0.65 | -0.21 / -0.29 | +0.29 / +0.29 | -1.69 (2016-18 wk9) | -6.96 (2016 wk5) |  | fail: rule 1 (2016-18, 2019-22) |
| pass | e_c50_d | -0.66 / -0.43 | +0.70 / +0.64 | +0.64 / -0.08 | +1.38 / +1.38 | -5.06 (2015 wk1) | -12.28 (2016 wk9) |  | fail: rule 1 (2015, 2019-22) |
| pass | e_c50_d_m | +2.15 / +2.53 | -0.31 / +1.22 | +0.04 / -0.09 | +0.50 / +0.50 | -3.14 (2016-18 wk9) | -13.25 (2016 wk5) |  | fail: rule 1 (2016-18, 2019-22) |
| pass | p2 | -5.20 / -5.85 | -0.71 / -5.95 | -0.15 / -3.12 | +2.28 / +2.28 | -13.27 (2015 wk1) | -24.06 (2018 wk1) |  | fail: rule 1 (2015, 2016-18, 2019-22) |
| pass | p2_all | -23.74 / -28.27 | -18.78 / -32.77 | -16.17 / -25.08 | +4.20 / +4.20 | -54.28 (2016-18 wk1) | -95.31 (2018 wk1) |  | fail: rule 1 (2015, 2016-18, 2019-22) |
| pass | p2+best1 | -4.11 / -4.39 | -0.31 / -5.12 | +0.39 / -2.51 | +2.55 / +2.55 | -12.17 (2015 wk1) | -24.89 (2018 wk1) |  | fail: rule 1 (2015, 2016-18, 2019-22) |
| pass | p2_all+best1 | -23.06 / -27.71 | -18.32 / -32.12 | -16.03 / -25.03 | +4.45 / +4.45 | -54.55 (2016-18 wk1) | -95.89 (2018 wk1) |  | fail: rule 1 (2015, 2016-18, 2019-22) |
| pass | sos | +0.56 / +0.58 | -0.65 / -0.55 | +1.01 / +1.08 | -0.62 / -0.62 | -2.35 (2023-25 wk1) | -5.08 (2023 wk1) |  | fail: rule 1 (2016-18, 2023-25) |
| pass | sos_h | +0.28 / +0.29 | -0.27 / -0.26 | +0.52 / +0.55 | -0.29 / -0.29 | -1.15 (2023-25 wk1) | -2.54 (2023 wk1) |  | fail: rule 1 (2016-18, 2023-25) |
| pass | coach25 | -0.76 / -0.76 | -0.17 / +0.01 | -0.67 / -0.67 | +0.13 / +0.13 | -2.45 (2015 wk1) | -4.72 (2019 wk1) |  | fail: rule 1 (2015, 2016-18, 2019-22) |
| pass | coach50 | -1.53 / -1.53 | -0.36 / -0.02 | -1.49 / -1.49 | +0.26 / +0.26 | -4.89 (2015 wk1) | -10.71 (2019 wk1) |  | fail: rule 1 (2015, 2016-18, 2019-22) |
| pass | recon | -4.55 / -4.32 | +0.07 / +0.09 | -3.75 / -3.50 | -0.54 / -0.54 | -15.99 (2015 wk5) | -22.47 (2021 wk1) |  | fail: rule 1 (2015, 2019-22, 2023-25) |
| pass | recon_h | -1.80 / -1.68 | +0.44 / +0.40 | -1.41 / -1.21 | -0.07 / -0.07 | -8.00 (2015 wk5) | -9.42 (2021 wk1) |  | fail: rule 1 (2015, 2019-22, 2023-25) |

## Every variant, refit config

Gains in yards of season-total miss, reg target / harness target. Worst week = the largest loss in any window x as-of week cell (reg target), and in any single season x as-of week (reg). Placebo = the lowest, over the four windows, of the share of the 50 shuffles the real gain beats (reg target); blank when rule 1 fails.

| kind | variant | 2015 | 2016-18 | 2019-22 | 2023-25 | worst window-week | worst season-week | placebo | verdict |
|---|---|---|---|---|---|---|---|---|---|
| rec | b25 | -0.07 / +0.00 | +0.00 / +0.01 | +0.23 / +0.35 | +0.21 / +0.22 | -0.62 (2015 wk5) | -0.72 (2016 wk9) |  | fail: rule 1 (2015 on reg) |
| rec | b50 | -0.22 / -1.57 | -0.08 / -0.04 | +0.36 / +0.96 | +0.31 / +0.76 | -1.27 (2015 wk5) | -1.55 (2016 wk9) |  | fail: rule 1 (2015, 2016-18) |
| rec | c25 | +0.04 / -0.04 | -0.03 / +0.04 | +0.05 / +0.02 | +0.12 / +0.06 | -0.29 (2016-18 wk9) | -0.63 (2019 wk9) |  | fail: rule 1 (2015, 2016-18) |
| rec | c50 | +0.03 / -0.13 | -0.11 / +0.01 | +0.07 / -0.01 | +0.17 / +0.06 | -0.64 (2016-18 wk9) | -1.26 (2019 wk9) |  | fail: rule 1 (2015, 2016-18, 2019-22) |
| rec | d | -0.60 / -0.62 | -0.06 / -0.06 | +0.07 / +0.08 | +0.05 / +0.20 | -1.18 (2015 wk1) | -1.18 (2015 wk1) |  | fail: rule 1 (2015, 2016-18) |
| rec | d_m | -0.04 / -0.03 | -0.05 / -0.07 | -0.10 / -0.12 | -0.03 / -0.03 | -0.18 (2019-22 wk5) | -0.27 (2022 wk1) |  | fail: rule 1 (2015, 2016-18, 2019-22, 2023-25) |
| rec | e_c25_d | -0.55 / -0.68 | -0.07 / -0.03 | +0.13 / +0.11 | +0.17 / +0.29 | -1.16 (2015 wk1) | -1.16 (2015 wk1) |  | fail: rule 1 (2015, 2016-18) |
| rec | e_c25_d_m | +0.01 / -0.08 | -0.07 / -0.03 | -0.05 / -0.10 | +0.10 / +0.04 | -0.32 (2016-18 wk9) | -0.63 (2019 wk9) |  | fail: rule 1 (2015, 2016-18, 2019-22) |
| rec | e_c50_d | -0.57 / -0.76 | -0.16 / -0.07 | +0.15 / +0.10 | +0.26 / +0.32 | -1.14 (2015 wk1) | -1.42 (2016 wk9) |  | fail: rule 1 (2015, 2016-18) |
| rec | e_c50_d_m | +0.00 / -0.17 | -0.16 / -0.06 | -0.03 / -0.12 | +0.15 / +0.04 | -0.68 (2016-18 wk9) | -1.27 (2019 wk9) |  | fail: rule 1 (2015, 2016-18, 2019-22) |
| rec | p2 | +0.58 / +0.45 | -0.21 / -0.20 | -0.05 / +0.09 | +0.73 / +0.82 | -1.23 (2016-18 wk1) | -2.07 (2017 wk1) |  | fail: rule 1 (2016-18, 2019-22) |
| rec | p2_all | -1.79 / -2.07 | -2.58 / -2.63 | -3.18 / -1.99 | -0.91 / -1.44 | -5.83 (2016-18 wk1) | -7.84 (2017 wk1) |  | fail: rule 1 (2015, 2016-18, 2019-22, 2023-25) |
| rec | p2+best1 | +0.58 / +0.45 | -0.21 / -0.20 | -0.05 / +0.09 | +0.73 / +0.82 | -1.23 (2016-18 wk1) | -2.07 (2017 wk1) |  | fail: rule 1 (2016-18, 2019-22) |
| rec | p2_all+best1 | -1.79 / -2.07 | -2.58 / -2.63 | -3.18 / -1.99 | -0.91 / -1.44 | -5.83 (2016-18 wk1) | -7.84 (2017 wk1) |  | fail: rule 1 (2015, 2016-18, 2019-22, 2023-25) |
| rec | sos | +0.15 / +0.15 | +0.01 / -0.01 | +0.06 / +0.05 | -0.07 / -0.06 | -0.16 (2023-25 wk1) | -0.24 (2024 wk1) |  | fail: rule 1 (2016-18, 2023-25) |
| rec | sos_h | +0.08 / +0.08 | +0.01 / -0.00 | +0.03 / +0.03 | -0.03 / -0.03 | -0.08 (2023-25 wk1) | -0.12 (2024 wk1) |  | fail: rule 1 (2016-18, 2023-25) |
| rec | coach25 | +0.07 / +0.07 | -0.04 / -0.04 | -0.03 / +0.02 | +0.06 / +0.06 | -0.11 (2019-22 wk1) | -0.36 (2016 wk5) |  | fail: rule 1 (2016-18, 2019-22) |
| rec | coach50 | +0.14 / +0.14 | -0.11 / -0.09 | -0.06 / -0.00 | +0.11 / +0.11 | -0.23 (2019-22 wk1) | -0.72 (2016 wk5) |  | fail: rule 1 (2016-18, 2019-22) |
| rec | comp25 | +0.88 / -0.52 | -0.48 / -0.48 | +0.15 / +0.53 | +0.35 / +0.80 | -1.84 (2016-18 wk1) | -3.19 (2018 wk1) |  | fail: rule 1 (2015, 2016-18) |
| rec | comp50 | +0.28 / -0.02 | -1.31 / -1.27 | -0.03 / +0.10 | +0.13 / +0.65 | -5.48 (2016-18 wk1) | -8.13 (2018 wk1) |  | fail: rule 1 (2015, 2016-18, 2019-22) |
| rec | recon | +0.60 / -0.82 | -0.46 / -0.37 | +0.52 / +0.97 | +0.50 / +0.95 | -1.74 (2016-18 wk1) | -3.56 (2018 wk1) |  | fail: rule 1 (2015, 2016-18) |
| rec | recon_h | +0.35 / +0.32 | -0.14 / -0.10 | +0.34 / +0.46 | +0.31 / +0.32 | -0.64 (2016-18 wk1) | -1.73 (2018 wk1) |  | fail: rule 1 (2016-18) |
| rush | b25 | +0.04 / -0.04 | +0.15 / +0.11 | -0.09 / -0.32 | +0.11 / +0.12 | -0.64 (2019-22 wk1) | -1.82 (2019 wk1) |  | fail: rule 1 (2015, 2019-22) |
| rush | b50 | -0.14 / -0.71 | +0.11 / +0.06 | -0.46 / -0.87 | +0.50 / +0.07 | -5.71 (2015 wk1) | -5.71 (2015 wk1) |  | fail: rule 1 (2015, 2019-22) |
| rush | c25 | +0.46 / +0.45 | +0.09 / +0.18 | +0.20 / +0.21 | +0.10 / +0.13 | -0.19 (2023-25 wk5) | -1.16 (2017 wk5) | 44% | fail: rule 3 (placebo: reg 2015, reg 2016-18, reg 2023-25, harness 2016-18, harness 2023-25) |
| rush | c50 | +0.90 / +0.81 | +0.02 / +0.14 | +0.35 / +0.40 | +0.13 / +0.20 | -0.45 (2023-25 wk5) | -2.32 (2017 wk5) | 56% | fail: rule 3 (placebo: reg 2016-18, reg 2023-25, harness 2016-18, harness 2023-25) |
| rush | d | -0.02 / -0.27 | -0.22 / -0.17 | +0.25 / +0.10 | +0.43 / -0.13 | -1.62 (2015 wk1) | -1.62 (2015 wk1) |  | fail: rule 1 (2015, 2016-18, 2023-25) |
| rush | d_m | -0.13 / -0.10 | -0.22 / -0.16 | +0.21 / +0.24 | +0.21 / +0.16 | -0.51 (2015 wk1) | -1.04 (2017 wk1) |  | fail: rule 1 (2015, 2016-18) |
| rush | e_c25_d | +0.44 / +0.37 | -0.09 / +0.02 | +0.44 / +0.44 | +0.57 / +0.42 | -1.74 (2015 wk1) | -1.74 (2015 wk1) |  | fail: rule 1 (2016-18 on reg) |
| rush | e_c25_d_m | +0.34 / +0.35 | -0.12 / +0.04 | +0.41 / +0.45 | +0.34 / +0.32 | -0.63 (2015 wk1) | -1.39 (2017 wk5) |  | fail: rule 1 (2016-18 on reg) |
| rush | e_c50_d | +0.85 / +0.72 | -0.10 / -0.01 | +0.60 / +0.63 | +0.66 / +0.50 | -1.86 (2015 wk1) | -2.62 (2017 wk5) |  | fail: rule 1 (2016-18) |
| rush | e_c50_d_m | +0.79 / +0.70 | -0.15 / -0.03 | +0.57 / +0.63 | +0.41 / +0.41 | -0.75 (2015 wk1) | -2.55 (2017 wk5) |  | fail: rule 1 (2016-18) |
| rush | p2 | -0.60 / -0.68 | +0.37 / +0.51 | -0.70 / -0.41 | -0.86 / -0.05 | -1.84 (2023-25 wk1) | -5.34 (2025 wk1) |  | fail: rule 1 (2015, 2019-22, 2023-25) |
| rush | p2_all | +0.16 / +0.50 | -1.51 / -1.51 | -3.15 / -3.32 | -2.50 / -1.08 | -7.17 (2023-25 wk1) | -18.03 (2025 wk1) |  | fail: rule 1 (2016-18, 2019-22, 2023-25) |
| rush | p2+best1 | +0.32 / +0.07 | +0.29 / +0.45 | -0.29 / -0.01 | -0.81 / +0.01 | -1.75 (2023-25 wk1) | -4.96 (2025 wk1) |  | fail: rule 1 (2019-22, 2023-25) |
| rush | p2_all+best1 | +1.09 / +1.04 | -1.51 / -1.48 | -3.30 / -2.95 | -1.71 / -0.99 | -5.89 (2019-22 wk5) | -15.12 (2019 wk5) |  | fail: rule 1 (2016-18, 2019-22, 2023-25) |
| rush | sos | +0.16 / +0.14 | -0.07 / -0.06 | +0.08 / +0.05 | -0.12 / -0.11 | -0.28 (2023-25 wk5) | -0.33 (2016 wk9) |  | fail: rule 1 (2016-18, 2023-25) |
| rush | sos_h | +0.08 / +0.07 | -0.03 / -0.03 | +0.04 / +0.03 | -0.06 / -0.05 | -0.14 (2023-25 wk5) | -0.17 (2016 wk9) |  | fail: rule 1 (2016-18, 2023-25) |
| rush | coach25 | +0.09 / +0.03 | -0.00 / -0.03 | -0.12 / -0.19 | -0.08 / -0.12 | -0.50 (2019-22 wk1) | -1.62 (2021 wk1) |  | fail: rule 1 (2016-18, 2019-22, 2023-25) |
| rush | coach50 | +0.12 / -0.15 | -0.09 / -0.08 | -0.30 / -0.39 | -0.18 / -0.25 | -1.12 (2019-22 wk1) | -3.69 (2021 wk1) |  | fail: rule 1 (2015, 2016-18, 2019-22, 2023-25) |
| rush | comp25 | +1.36 / +1.39 | +0.42 / +0.32 | -0.05 / -0.12 | -0.11 / -0.14 | -1.98 (2019-22 wk1) | -7.37 (2019 wk1) |  | fail: rule 1 (2019-22, 2023-25) |
| rush | comp50 | +1.51 / +1.55 | +0.27 / -0.13 | -0.55 / -0.82 | -0.98 / -1.14 | -5.03 (2019-22 wk1) | -11.39 (2019 wk1) |  | fail: rule 1 (2016-18, 2019-22, 2023-25) |
| rush | recon | +2.11 / +1.84 | +0.70 / +0.45 | +0.39 / -0.01 | +0.58 / +0.02 | -1.53 (2019-22 wk1) | -5.85 (2019 wk1) |  | fail: rule 1 (2019-22 on harness) |
| rush | recon_h | +1.17 / +1.13 | +0.53 / +0.39 | +0.26 / +0.13 | +0.16 / +0.23 | -0.41 (2019-22 wk1) | -3.69 (2019 wk1) | 86% | fail: rule 3 (placebo: reg 2023-25) |
| pass | b25 | -5.11 / -4.59 | -1.30 / -1.52 | -0.96 / -0.48 | +3.39 / +3.86 | -11.69 (2015 wk5) | -21.57 (2022 wk1) |  | fail: rule 1 (2015, 2016-18, 2019-22) |
| pass | b50 | -10.30 / -10.22 | -4.08 / -4.04 | -3.27 / -1.67 | +6.20 / +6.29 | -23.73 (2015 wk5) | -43.13 (2022 wk1) |  | fail: rule 1 (2015, 2016-18, 2019-22) |
| pass | c25 | +2.03 / +2.62 | +0.32 / +1.69 | +0.29 / +0.69 | +0.31 / +0.24 | -1.97 (2023-25 wk1) | -9.81 (2016 wk5) | 18% | fail: rule 3 (placebo: reg 2019-22, reg 2023-25, harness 2019-22, harness 2023-25) |
| pass | c50 | +4.05 / +4.94 | -0.18 / +3.18 | +0.19 / +0.70 | +0.19 / +0.21 | -3.94 (2023-25 wk1) | -23.86 (2016 wk5) |  | fail: rule 1 (2016-18 on reg) |
| pass | d | -2.81 / +3.92 | -0.63 / -0.33 | -0.45 / -4.26 | +0.38 / -4.44 | -6.43 (2016-18 wk1) | -7.70 (2020 wk9) |  | fail: rule 1 (2015, 2016-18, 2019-22, 2023-25) |
| pass | d_m | -0.37 / -0.38 | -0.31 / -0.50 | -1.02 / -1.16 | -0.32 / +0.04 | -1.92 (2019-22 wk5) | -3.64 (2021 wk1) |  | fail: rule 1 (2015, 2016-18, 2019-22, 2023-25) |
| pass | e_c25_d | -0.79 / +6.21 | +0.01 / +1.69 | -0.18 / -3.62 | +0.88 / -3.85 | -7.46 (2016-18 wk1) | -13.05 (2016 wk9) |  | fail: rule 1 (2015, 2019-22, 2023-25) |
| pass | e_c25_d_m | +1.66 / +2.23 | +0.07 / +1.23 | -0.74 / -0.55 | +0.06 / +0.25 | -2.56 (2023-25 wk1) | -10.86 (2016 wk5) |  | fail: rule 1 (2019-22) |
| pass | e_c50_d | +1.24 / +8.41 | -0.46 / +2.97 | -0.28 / -3.29 | +1.11 / -3.57 | -8.49 (2016-18 wk1) | -22.00 (2016 wk9) |  | fail: rule 1 (2016-18, 2019-22, 2023-25) |
| pass | e_c50_d_m | +3.68 / +4.50 | -0.34 / +2.76 | -0.83 / -0.51 | +0.10 / +0.16 | -4.53 (2023-25 wk1) | -24.15 (2016 wk5) |  | fail: rule 1 (2016-18, 2019-22) |
| pass | p2 | +4.90 / +7.52 | -5.09 / -8.38 | -2.06 / -5.15 | -0.30 / -6.14 | -12.45 (2016-18 wk1) | -24.56 (2018 wk1) |  | fail: rule 1 (2016-18, 2019-22, 2023-25) |
| pass | p2_all | +27.20 / +23.21 | -26.51 / -33.69 | -6.51 / -5.61 | +16.65 / +15.21 | -86.73 (2016-18 wk1) | -126.89 (2018 wk1) |  | fail: rule 1 (2016-18, 2019-22) |
| pass | p2+best1 | +7.05 / +10.07 | -4.48 / -6.17 | -1.84 / -4.49 | -0.05 / -5.70 | -13.45 (2016-18 wk1) | -25.90 (2018 wk1) |  | fail: rule 1 (2016-18, 2019-22, 2023-25) |
| pass | p2_all+best1 | +28.35 / +24.67 | -25.70 / -32.22 | -6.00 / -4.94 | +16.81 / +15.64 | -86.82 (2016-18 wk1) | -127.55 (2018 wk1) |  | fail: rule 1 (2016-18, 2019-22) |
| pass | sos | +0.62 / +0.80 | -0.90 / -1.49 | +1.38 / +1.74 | -1.11 / -0.73 | -2.55 (2016-18 wk1) | -6.02 (2023 wk1) |  | fail: rule 1 (2016-18, 2023-25) |
| pass | sos_h | +0.31 / +0.47 | -0.41 / -0.70 | +0.77 / +0.97 | -0.55 / -0.33 | -1.27 (2023-25 wk1) | -3.01 (2023 wk1) |  | fail: rule 1 (2016-18, 2023-25) |
| pass | coach25 | -1.25 / -1.30 | -0.29 / -0.31 | -1.14 / -0.92 | +0.02 / +0.04 | -3.82 (2015 wk1) | -9.36 (2019 wk1) |  | fail: rule 1 (2015, 2016-18, 2019-22) |
| pass | coach50 | -2.50 / -2.60 | -0.57 / -0.63 | -2.61 / -1.84 | +0.05 / +0.07 | -7.63 (2015 wk1) | -18.71 (2019 wk1) |  | fail: rule 1 (2015, 2016-18, 2019-22) |
| pass | recon | -14.80 / -15.14 | -2.20 / -1.16 | -7.97 / -6.45 | -0.37 / -3.89 | -31.37 (2015 wk5) | -34.59 (2022 wk1) |  | fail: rule 1 (2015, 2016-18, 2019-22, 2023-25) |
| pass | recon_h | -7.08 / -6.71 | -0.26 / +0.40 | -3.14 / -2.57 | +0.61 / -0.91 | -15.68 (2015 wk5) | -17.30 (2022 wk1) |  | fail: rule 1 (2015, 2016-18, 2019-22, 2023-25) |

## Placebo detail (variants passing rule 1 on both targets)

Real gain, the 90th percentile of the 50 shuffled gains, and how many of 50 the real gain beats, per window (reg target; harness in the csv).

| kind | variant | config | 2015 | 2016-18 | 2019-22 | 2023-25 | joint (all four) reg / harness | rule 3 |
|---|---|---|---|---|---|---|---|---|
| pass | c25 | fixed | +1.13 vs +0.63 (47/50) | +0.01 vs -0.06 (47/50) | +0.35 vs +1.07 (36/50) | +0.31 vs +3.73 (10/50) | 6 / 6 | fail |
| pass | c25 | refit | +2.03 vs -0.55 (47/50) | +0.32 vs -0.30 (48/50) | +0.29 vs +1.40 (36/50) | +0.31 vs +5.36 (9/50) | 6 / 6 | fail |
| rush | c25 | fixed | +0.46 vs +0.49 (43/50) | +0.25 vs +0.65 (24/50) | +0.20 vs +0.12 (45/50) | +0.13 vs +0.50 (31/50) | 11 / 18 | fail |
| rush | c25 | refit | +0.46 vs +0.66 (38/50) | +0.09 vs +0.47 (22/50) | +0.20 vs +0.15 (48/50) | +0.10 vs +0.54 (25/50) | 6 / 18 | fail |
| rush | c50 | fixed | +0.83 vs +0.40 (46/50) | +0.26 vs +0.86 (30/50) | +0.35 vs -0.04 (49/50) | +0.20 vs +0.36 (41/50) | 23 / 30 | fail |
| rush | c50 | refit | +0.90 vs +0.61 (46/50) | +0.02 vs +0.61 (28/50) | +0.35 vs -0.10 (49/50) | +0.13 vs +0.73 (34/50) | 17 / 29 | fail |
| rush | e_c25_d_m | fixed | +0.30 vs +0.53 (39/50) | +0.07 vs +0.72 (14/50) | +0.38 vs +0.21 (48/50) | +0.32 vs +0.47 (39/50) | 9 / 19 | fail |
| rush | recon_h | fixed | +1.17 vs +0.21 (50/50) | +0.68 vs +0.08 (50/50) | +0.29 vs +0.21 (48/50) | +0.23 vs +0.12 (46/50) | 44 / 36 | fail |
| rush | recon_h | refit | +1.17 vs +0.56 (50/50) | +0.53 vs +0.15 (50/50) | +0.26 vs +0.11 (46/50) | +0.16 vs +0.19 (43/50) | 39 / 43 | fail |

## Rule 5: the passing pieces together

No variant passed rules 1, 3 and 4, so there is nothing to combine.

## Age ratios (fitted on 2016-18; touches over the games left / what the as-of share expected; shrunk toward 1 with 30 players)

p2 (games he played): pass QB 25-27 0.927 (n 30); pass QB 28-30 0.948 (n 50); pass QB 31+ 0.941 (n 105); pass QB <=24 0.947 (n 41); rec RB 25-27 0.846 (n 129); rec RB 28-30 0.778 (n 51); rec RB 31+ 0.876 (n 27); rec RB <=24 0.859 (n 151); rec TE 25-27 0.898 (n 97); rec TE 28-30 0.860 (n 79); rec TE 31+ 0.871 (n 62); rec TE <=24 0.998 (n 79); rec WR 25-27 0.887 (n 244); rec WR 28-30 0.865 (n 159); rec WR 31+ 0.951 (n 61); rec WR <=24 0.939 (n 259); rush QB 25-27 0.943 (n 13); rush QB 28-30 0.987 (n 23); rush QB 31+ 0.954 (n 10); rush QB <=24 1.035 (n 24); rush RB 25-27 0.922 (n 139); rush RB 28-30 0.929 (n 67); rush RB 31+ 0.981 (n 38); rush RB <=24 1.031 (n 213); rush WR 25-27 0.952 (n 3)

p2_all (every game left): pass QB 25-27 0.767 (n 31); pass QB 28-30 0.846 (n 52); pass QB 31+ 0.758 (n 112); pass QB <=24 0.875 (n 41); rec RB 25-27 0.687 (n 133); rec RB 28-30 0.699 (n 51); rec RB 31+ 0.765 (n 28); rec RB <=24 0.732 (n 153); rec TE 25-27 0.678 (n 102); rec TE 28-30 0.730 (n 81); rec TE 31+ 0.771 (n 63); rec TE <=24 0.884 (n 79); rec WR 25-27 0.728 (n 251); rec WR 28-30 0.721 (n 165); rec WR 31+ 0.805 (n 63); rec WR <=24 0.793 (n 267); rush QB 25-27 0.861 (n 13); rush QB 28-30 0.928 (n 24); rush QB 31+ 0.900 (n 11); rush QB <=24 0.945 (n 25); rush RB 25-27 0.697 (n 145); rush RB 28-30 0.826 (n 67); rush RB 31+ 0.851 (n 39); rush RB <=24 0.851 (n 218); rush WR 25-27 0.929 (n 3)

Best Part 1 piece by kind for p2+best1 (fixed config, rule 1 on both targets): {'rec': 'base', 'rush': 'c50', 'pass': 'c25'}.

## Verdict

Nothing passes. Every variant fails at least one of rules 1 and 3 on at least one kind (the failing rule is in the tables above); nothing changes in nflmodel/player_season.py.


### On the regular-season target alone

- rush recon_h (fixed) passes rule 1 on both targets and the placebo on every window of the regular-season target (50/50, 50/50, 48/50, 46/50), but not on the harness target (2015 49/50, 2016-18 49/50, 2019-22 40/50, 2023-25 46/50). Gains reg +1.17, +0.68, +0.29, +0.23; worst window-week -0.45, worst season-week -4.04. The change it would be: in project(): for the kind, yards_pg x (1 + 0.5 x props.RECON_W[kind]['yds'] x (clip(r / R_MED[kind][week], 0.5, 2) - 1)), r = clip(team expected yards per game over the games left (props.TEAM_FIT[kind]['yds'] on season.py expected points) / sum of the team's projected yards_pg, 0.5, 2); R_MED[rush] by as-of week (2016-18 medians of r): wk1 1.1558, wk5 0.9508, wk9 0.9476, wk13 1.0143 (the page runs every week: weeks between would need the nearest or an interpolated value, which this study did not score). Under the joint reading of the placebo (all four windows at once) it beats 44 of 50 on the regular-season target.

## Rule 4 (no new risk)

Every variant reads only what the weekly run already pulls and only as of the week: plays (last-17 volumes, the previous regular season, the defenses' allowed rates), our own game model (season.py profiles, fit_asof and expected_points on features_asof and pred_v3, no lines or totals), the schedule's head coach (games.parquet, filled for unplayed games), birth dates (players.parquet, already read by the availability logit), and the rows' own projected shares. No market input anywhere. All pass rule 4; none reaches rule 5 under the rule as registered.

## Notes

- `nflmodel/player_season.season_actuals` filters `week <= 18` without `season_type`: for 2015-2020 week 18 is the wild-card round, so the harness's actual totals (and `prev_yards`, the week-1 pace baseline for 2016-21) include a playoff game for players on wild-card teams. The live page is unaffected for 2021 on (18 regular-season weeks), but the published backtest misses for 2016-20 are measured against partly-playoff totals. Not changed here (nflmodel/ is out of scope).
- The refit config refits AVAIL and BLEND on 2016-18 with that window's in-sample availability chances; for passers this flatters the fit and costs the test windows (base passing refit: 572.5 / 615.8 against today's 568.4 / 602.9 on the regular-season target), as the harness notes.
- recon for rushing: the team's expected rushing yards from props.TEAM_FIT (71.47 + 1.388 x expected points) barely moves with our game model (sd 3.8 yards a game over the team-weeks), so on rushing the reconciliation works mostly as a shrink of each team's summed rusher projections toward about 103 yards a game, not as information from the game model.
- The placebo for the previous-season volume (c) shuffles another team's previous season in, which on average pulls toward the league mean; its gains on rushing come close to the real one's, i.e. most of c's rushing gain is shrinkage, not the team's own history.

Runtime of the scoring run: 43s (build of the 2015 rows, the check and the team table: about 3 minutes).
