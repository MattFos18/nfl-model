# Tie-out (sources and page), 2026-09-23 07:17 UTC

The same number must read the same everywhere it appears. Each row: what was compared, what it says, what it should say.

| Check | Reads | Should read | Ties |
|---|---|---|---|
| README flag record, held out | 49-27 | 49-27 | yes |
| README flag record, 2019 to 2025 | 141-90 | 141-90 | yes |
| README flag record, outside Week 18 | 132-80 | 132-80 | yes |
| README held-out margin miss | 9.95 | 9.95 | yes |
| threshold sweep, cut 4, 2019-22 | 87-59 | 87-59 | yes |
| threshold sweep, cut 4, 2023-25 | 45-21 | 45-21 | yes |
| docs section 9 row, cut 4, 2019-22 | 87-59 | 87-59 | yes |
| docs section 9 row, cut 4, 2023-25 | 45-21 | 45-21 | yes |
| docs: live cut named in section 9 | True | True | yes |
| docs: QB replacement level | True | True | yes |
| model inputs counted | 22 | 22 | yes |
| docs: input count | True | True | yes |
| picks file flags = tracker rows (games) | ['2026_03_CIN_PIT', '2026_03_KC_MIA', '2026_03_TEN_NYG'] | ['2026_03_CIN_PIT', '2026_03_KC_MIA', '2026_03_TEN_NYG'] | yes |
| picks file flags = tracker rows (bets) | ['MIA +11.5', 'NYG -2.5', 'PIT +3.5'] | ['MIA +11.5', 'NYG -2.5', 'PIT +3.5'] | yes |
| picks file stakes = tracker stakes | [0.54, 0.63, 0.97] | [0.54, 0.63, 0.97] | yes |
| picks markdown names the live cut | True | True | yes |
| page backtest file: games | 3060 | 3060 | yes |
| page backtest file: model spread equals the prediction table | 0.0 | 0.0 | yes |
| page backtest file: model total equals the prediction table | 0.0 | 0.0 | yes |
| page inputs = model inputs | ['off_epa_play', 'def_epa_play', 'off_pf', 'def_pf', 'qb_rating', 'home', 'neutr | ['off_epa_play', 'def_epa_play', 'off_pf', 'def_pf', 'qb_rating', 'home', 'neutr | yes |
| page flag threshold = picks threshold | 4.0 | 4.0 | yes |
| page week = picks file (games) | ['2026_03_ARI_SF', '2026_03_ATL_GB', '2026_03_BAL_DAL', '2026_03_CAR_CLE', '2026 | ['2026_03_ARI_SF', '2026_03_ATL_GB', '2026_03_BAL_DAL', '2026_03_CAR_CLE', '2026 | yes |
| page week = picks file (bets) | ['', '', '', '', '', '', '', '', '', '', '', '', '', 'MIA +11.5', 'NYG -2.5', 'P | ['', '', '', '', '', '', '', '', '', '', '', '', '', 'MIA +11.5', 'NYG -2.5', 'P | yes |
| page week = picks file (model spread) | 0.0 | 0.0 | yes |
| page live table = tracker (pending model rows) | ['MIA +11.5', 'NYG -2.5', 'PIT +3.5'] | ['MIA +11.5', 'NYG -2.5', 'PIT +3.5'] | yes |
| page rankings: QB replacement level | -0.12 | -0.12 | yes |

Result: PASS (26 of 26 tie)
