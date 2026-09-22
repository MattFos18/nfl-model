# Week 3, 2026: model picks

Our line is home spread / total. Edge = model minus Vegas (spread: positive favours the home side; total: positive favours the over). Win, cover and total are the model's chances for each side at the current line; 52.4% is break-even at -110.
Bet flag: spread when the edge is 5+ points, total when 6+. These are the thresholds with the best ROI that held in both backtest windows (2019 to 2022 and 2023 to 2025), but the samples are small: 127 spread bets at 5+ went 53.5% (+2.2% ROI), 61 total bets at 6+ went 60.7% (+15.8%). Edges under those thresholds have lost money in every window. No flags in Week 18, where resting starters make the line smarter than the ratings (flags there went 7-11). Full table in docs/how_it_works.md.

| Game      | Date       | Our score          | Old model   | Our line        | Vegas            | Edge (spread / total)   | Win               | Cover the spread   | Total                | Flag      |
|:----------|:-----------|:-------------------|:------------|:----------------|:-----------------|:------------------------|:------------------|:-------------------|:---------------------|:----------|
| ATL @ GB  | 2026-09-24 | ATL 19.7, GB 25.6  | -10.8-14.3  | GB -6.0 / 45.3  | GB -6 / 43.5     | -0.0 / +1.8             | GB 67% / ATL 33%  | GB 48% / ATL 52%   | Over 55% / Under 45% |           |
| LAC @ BUF | 2026-09-27 | LAC 21.0, BUF 28.8 | 12.6-52.6   | BUF -7.8 / 49.8 | BUF -7 / 50.5    | +0.8 / -0.7             | BUF 72% / LAC 28% | BUF 49% / LAC 51%  | Over 48% / Under 52% |           |
| CAR @ CLE | 2026-09-27 | CAR 21.2, CLE 23.0 | 37.5-15.8   | CLE -1.7 / 44.2 | CLE +2.5 / 42.5  | +4.2 / +1.7             | CLE 55% / CAR 45% | CLE 60% / CAR 40%  | Over 55% / Under 45% |           |
| NYJ @ DET | 2026-09-27 | NYJ 22.7, DET 28.3 | 32.6-27.5   | DET -5.6 / 51.0 | DET -6.5 / 48.5  | -0.9 / +2.5             | DET 66% / NYJ 34% | DET 45% / NYJ 55%  | Over 57% / Under 43% |           |
| HOU @ IND | 2026-09-27 | HOU 23.7, IND 23.0 | 27.0-27.9   | IND +0.7 / 46.7 | IND +2.5 / 43.5  | +1.8 / +3.2             | IND 48% / HOU 52% | IND 53% / HOU 47%  | Over 59% / Under 41% |           |
| NE @ JAX  | 2026-09-27 | NE 20.6, JAX 21.6  | 5.1-16.4    | JAX -1.0 / 42.2 | JAX -3 / 45.5    | -2.0 / -3.3             | JAX 53% / NE 47%  | JAX 43% / NE 57%   | Over 40% / Under 60% |           |
| KC @ MIA  | 2026-09-27 | KC 26.1, MIA 21.0  | 48.8-10.6   | MIA +5.0 / 47.1 | MIA +11.5 / 46.5 | +6.5 / +0.6             | MIA 35% / KC 65%  | MIA 70% / KC 30%   | Over 52% / Under 48% | MIA +11.5 |
| TEN @ NYG | 2026-09-27 | TEN 18.2, NYG 24.4 | 23.1-40.7   | NYG -6.2 / 42.6 | NYG -3.5 / 40.5  | +2.7 / +2.1             | NYG 68% / TEN 32% | NYG 55% / TEN 45%  | Over 56% / Under 44% |           |
| CIN @ PIT | 2026-09-27 | CIN 22.5, PIT 21.5 | 13.8-5.1    | PIT +1.0 / 44.0 | PIT +3.5 / 42.5  | +2.5 / +1.5             | PIT 47% / CIN 53% | PIT 60% / CIN 40%  | Over 55% / Under 45% |           |
| SEA @ WAS | 2026-09-27 | SEA 24.0, WAS 20.2 | 37.0-15.6   | WAS +3.8 / 44.2 | WAS +7 / 40.5    | +3.2 / +3.7             | WAS 39% / SEA 61% | WAS 64% / SEA 36%  | Over 61% / Under 39% |           |
| ARI @ SF  | 2026-09-27 | ARI 18.5, SF 29.2  | 16.2-38.7   | SF -10.6 / 47.7 | SF -8.5 / 47.5   | +2.1 / +0.2             | SF 79% / ARI 21%  | SF 52% / ARI 48%   | Over 51% / Under 49% |           |
| MIN @ TB  | 2026-09-27 | MIN 21.8, TB 20.7  | 27.1-8.5    | TB +1.1 / 42.5  | TB +1.5 / 42.5   | +0.4 / -0.0             | TB 46% / MIN 54%  | TB 49% / MIN 51%   | Over 50% / Under 50% |           |
| BAL @ DAL | 2026-09-27 | BAL 25.9, DAL 26.0 | 35.9-39.1   | DAL -0.1 / 51.9 | DAL +3 / 52.5    | +3.1 / -0.6             | DAL 50% / BAL 50% | DAL 60% / BAL 40%  | Over 48% / Under 52% |           |
| LV @ NO   | 2026-09-27 | LV 21.5, NO 23.5   | 27.0-14.0   | NO -2.0 / 45.0  | NO -3 / 43.5     | -1.0 / +1.5             | NO 56% / LV 44%   | NO 46% / LV 54%    | Over 54% / Under 46% |           |
| LA @ DEN  | 2026-09-27 | LA 23.4, DEN 22.2  | 11.0-18.9   | DEN +1.2 / 45.6 | DEN +2.5 / 45.5  | +1.3 / +0.1             | DEN 46% / LA 54%  | DEN 51% / LA 49%   | Over 50% / Under 50% |           |
| PHI @ CHI | 2026-09-28 | PHI 22.6, CHI 22.4 | 22.8-25.6   | CHI +0.2 / 45.0 | CHI +3 / 44.5    | +2.8 / +0.5             | CHI 49% / PHI 51% | CHI 59% / PHI 41%  | Over 51% / Under 49% |           |
