# Tie-out (sources and page), 2026-09-23 02:45 UTC

The same number must read the same everywhere it appears. Each row: what was compared, what it says, what it should say.

| Check | Reads | Should read | Ties |
|---|---|---|---|
| README flag record, held out | 46-28 | 46-28 | yes |
| README flag record, 2019 to 2025 | 139-97 | 139-97 | yes |
| README flag record, outside Week 18 | 131-87 | 131-87 | yes |
| README held-out margin miss | 9.97 | 9.97 | yes |
| threshold sweep, cut 4, 2019-22 | 89-65 | 89-65 | yes |
| threshold sweep, cut 4, 2023-25 | 42-22 | 42-22 | yes |
| docs section 9 row, cut 4, 2019-22 | 89-65 | 89-65 | yes |
| docs section 9 row, cut 4, 2023-25 | 42-22 | 42-22 | yes |
| docs: live cut named in section 9 | True | True | yes |
| docs: QB replacement level | True | True | yes |
| model inputs counted | 20 | 20 | yes |
| docs: input count | True | True | yes |
| picks file flags = tracker rows (games) | ['2026_03_CIN_PIT', '2026_03_KC_MIA', '2026_03_TEN_NYG'] | ['2026_03_CIN_PIT', '2026_03_KC_MIA', '2026_03_TEN_NYG'] | yes |
| picks file flags = tracker rows (bets) | ['MIA +11.5', 'NYG -3', 'PIT +3.5'] | ['MIA +11.5', 'NYG -3', 'PIT +3.5'] | yes |
| picks file stakes = tracker stakes | [0.82, 1.11, 1.37] | [0.82, 1.11, 1.37] | yes |
| picks markdown names the live cut | True | True | yes |
| page backtest file: games | 1903 | 1903 | yes |
| page backtest file: model spread equals the prediction table | 0.0 | 0.0 | yes |
| page backtest file: model total equals the prediction table | 0.0 | 0.0 | yes |
| page inputs = model inputs | ['off_epa_play', 'def_epa_play', 'off_pf', 'def_pf', 'qb_rating', 'home', 'neutr | ['off_epa_play', 'def_epa_play', 'off_pf', 'def_pf', 'qb_rating', 'home', 'neutr | yes |
| page flag threshold = picks threshold | 4.0 | 4.0 | yes |
| page week = picks file (games) | ['2026_03_ARI_SF', '2026_03_ATL_GB', '2026_03_BAL_DAL', '2026_03_CAR_CLE', '2026 | ['2026_03_ARI_SF', '2026_03_ATL_GB', '2026_03_BAL_DAL', '2026_03_CAR_CLE', '2026 | yes |
| page week = picks file (bets) | ['', '', '', '', '', '', '', '', '', '', '', '', '', 'MIA +11.5', 'NYG -3', 'PIT | ['', '', '', '', '', '', '', '', '', '', '', '', '', 'MIA +11.5', 'NYG -3', 'PIT | yes |
| page week = picks file (model spread) | 0.0 | 0.0 | yes |
| page live table = tracker (pending model rows) | ['MIA +11.5', 'NYG -3', 'PIT +3.5'] | ['MIA +11.5', 'NYG -3', 'PIT +3.5'] | yes |
| page rankings: QB replacement level | -0.12 | -0.12 | yes |

Result: PASS (26 of 26 tie)
