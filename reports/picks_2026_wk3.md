# Week 3, 2026: model picks

Our line is home spread / total. Edge = model minus Vegas (spread: positive favours the home side; total: positive favours the over). Win, cover and total are the model's chances for each side at the current line; 52.4% is break-even at -110.
Bet flag: spread when the edge is 5+ points, total when 6+. These are the thresholds with the best ROI that held in both backtest windows (2019 to 2022 and 2023 to 2025), but the samples are small: 127 spread bets at 5+ went 53.5% (+2.2% ROI), 61 total bets at 6+ went 60.7% (+15.8%). Edges under those thresholds have lost money in every window. No flags in Week 18, where resting starters make the line smarter than the ratings (flags there went 7-11). Full table in docs/how_it_works.md.

| Game      | Date       | Our score          | Old model   | Our line        | Vegas            | Edge (spread / total)   | Win               | Cover the spread   | Total                | Flag      |
|:----------|:-----------|:-------------------|:------------|:----------------|:-----------------|:------------------------|:------------------|:-------------------|:---------------------|:----------|
| ATL @ GB  | 2026-09-24 | ATL 19.8, GB 25.8  | -10.8-14.3  | GB -6.0 / 45.6  | GB -6 / 43.5     | -0.0 / +2.1             | GB 67% / ATL 33%  | GB 48% / ATL 52%   | Over 56% / Under 44% |           |
| LAC @ BUF | 2026-09-27 | LAC 21.1, BUF 28.9 | 12.6-52.6   | BUF -7.8 / 50.0 | BUF -7 / 50.5    | +0.8 / -0.5             | BUF 72% / LAC 28% | BUF 49% / LAC 51%  | Over 49% / Under 51% |           |
| CAR @ CLE | 2026-09-27 | CAR 21.4, CLE 23.1 | 37.5-15.8   | CLE -1.7 / 44.5 | CLE +2.5 / 42.5  | +4.2 / +2.0             | CLE 55% / CAR 45% | CLE 60% / CAR 40%  | Over 56% / Under 44% |           |
| NYJ @ DET | 2026-09-27 | NYJ 22.7, DET 28.3 | 32.6-27.5   | DET -5.6 / 51.0 | DET -6.5 / 48.5  | -0.9 / +2.5             | DET 66% / NYJ 34% | DET 45% / NYJ 55%  | Over 57% / Under 43% |           |
| HOU @ IND | 2026-09-27 | HOU 23.9, IND 23.1 | 27.0-27.9   | IND +0.7 / 47.0 | IND +2.5 / 43.5  | +1.8 / +3.5             | IND 48% / HOU 52% | IND 53% / HOU 47%  | Over 60% / Under 40% |           |
| NE @ JAX  | 2026-09-27 | NE 20.7, JAX 21.7  | 5.1-16.4    | JAX -1.0 / 42.5 | JAX -3 / 45.5    | -2.0 / -3.0             | JAX 53% / NE 47%  | JAX 43% / NE 57%   | Over 41% / Under 59% |           |
| KC @ MIA  | 2026-09-27 | KC 26.2, MIA 21.1  | 48.8-10.6   | MIA +5.0 / 47.3 | MIA +11.5 / 46.5 | +6.5 / +0.8             | MIA 35% / KC 65%  | MIA 70% / KC 30%   | Over 52% / Under 48% | MIA +11.5 |
| TEN @ NYG | 2026-09-27 | TEN 18.4, NYG 24.5 | 23.1-40.7   | NYG -6.1 / 42.9 | NYG -3.5 / 40.5  | +2.6 / +2.4             | NYG 68% / TEN 32% | NYG 55% / TEN 45%  | Over 57% / Under 43% |           |
| CIN @ PIT | 2026-09-27 | CIN 22.7, PIT 21.6 | 13.8-5.1    | PIT +1.0 / 44.3 | PIT +3.5 / 42.5  | +2.5 / +1.8             | PIT 47% / CIN 53% | PIT 60% / CIN 40%  | Over 55% / Under 45% |           |
| SEA @ WAS | 2026-09-27 | SEA 24.1, WAS 20.3 | 37.0-15.6   | WAS +3.8 / 44.4 | WAS +7 / 40.5    | +3.2 / +3.9             | WAS 39% / SEA 61% | WAS 64% / SEA 36%  | Over 62% / Under 38% |           |
| ARI @ SF  | 2026-09-27 | ARI 18.7, SF 29.3  | 16.2-38.7   | SF -10.6 / 47.9 | SF -8.5 / 47.5   | +2.1 / +0.4             | SF 79% / ARI 21%  | SF 52% / ARI 48%   | Over 51% / Under 49% |           |
| MIN @ TB  | 2026-09-27 | MIN 21.9, TB 20.8  | 27.1-8.5    | TB +1.1 / 42.8  | TB +1.5 / 42.5   | +0.4 / +0.3             | TB 46% / MIN 54%  | TB 49% / MIN 51%   | Over 51% / Under 49% |           |
| BAL @ DAL | 2026-09-27 | BAL 26.1, DAL 26.2 | 35.9-39.1   | DAL -0.1 / 52.3 | DAL +3 / 52.5    | +3.1 / -0.2             | DAL 50% / BAL 50% | DAL 60% / BAL 40%  | Over 49% / Under 51% |           |
| LV @ NO   | 2026-09-27 | LV 21.5, NO 23.5   | 27.0-14.0   | NO -2.0 / 45.0  | NO -3 / 43.5     | -1.0 / +1.5             | NO 56% / LV 44%   | NO 46% / LV 54%    | Over 54% / Under 46% |           |
| LA @ DEN  | 2026-09-27 | LA 23.5, DEN 22.3  | 11.0-18.9   | DEN +1.2 / 45.8 | DEN +2.5 / 45.5  | +1.3 / +0.3             | DEN 46% / LA 54%  | DEN 51% / LA 49%   | Over 51% / Under 49% |           |
| PHI @ CHI | 2026-09-28 | PHI 22.7, CHI 22.6 | 22.8-25.6   | CHI +0.1 / 45.3 | CHI +3 / 44.5    | +2.9 / +0.8             | CHI 49% / PHI 51% | CHI 59% / PHI 41%  | Over 52% / Under 48% |           |
