# Week 3, 2026: model picks

Our line is home spread / total. Edge = model minus Vegas (spread: positive favours the home side; total: positive favours the over). Win, cover and total are the model's chances for each side at the current line; 52.4% is break-even at -110.
Bet flag: spread when the edge is 5+ points, total when 6+. These are the thresholds with the best ROI that held in both backtest windows (2019 to 2022 and 2023 to 2025), but the samples are small: 127 spread bets at 5+ went 53.5% (+2.2% ROI), 61 total bets at 6+ went 60.7% (+15.8%). Edges under those thresholds have lost money in every window. No flags in Week 18, where resting starters make the line smarter than the ratings (flags there went 7-11). Full table in docs/how_it_works.md.

| Game      | Date       | Our score          | Old model   | Our line        | Vegas            | Edge (spread / total)   | Win               | Cover the spread   | Total                | Flag      |
|:----------|:-----------|:-------------------|:------------|:----------------|:-----------------|:------------------------|:------------------|:-------------------|:---------------------|:----------|
| ATL @ GB  | 2026-09-24 | ATL 20.3, GB 26.3  | -10.8-14.3  | GB -6.0 / 46.6  | GB -6 / 43.5     | -0.0 / +3.1             | GB 67% / ATL 33%  | GB 48% / ATL 52%   | Over 59% / Under 41% |           |
| LAC @ BUF | 2026-09-27 | LAC 21.4, BUF 29.1 | 12.6-52.6   | BUF -7.8 / 50.5 | BUF -7 / 50.5    | +0.8 / -0.0             | BUF 72% / LAC 28% | BUF 49% / LAC 51%  | Over 50% / Under 50% |           |
| CAR @ CLE | 2026-09-27 | CAR 21.4, CLE 23.1 | 37.5-15.8   | CLE -1.7 / 44.5 | CLE +2.5 / 42.5  | +4.2 / +2.0             | CLE 55% / CAR 45% | CLE 60% / CAR 40%  | Over 56% / Under 44% |           |
| NYJ @ DET | 2026-09-27 | NYJ 22.7, DET 28.3 | 32.6-27.5   | DET -5.6 / 51.0 | DET -6.5 / 48.5  | -0.9 / +2.5             | DET 66% / NYJ 34% | DET 45% / NYJ 55%  | Over 57% / Under 43% |           |
| HOU @ IND | 2026-09-27 | HOU 24.1, IND 23.3 | 27.0-27.9   | IND +0.7 / 47.4 | IND +2.5 / 43.5  | +1.8 / +3.9             | IND 48% / HOU 52% | IND 53% / HOU 47%  | Over 61% / Under 39% |           |
| NE @ JAX  | 2026-09-27 | NE 20.4, JAX 21.4  | 5.1-16.4    | JAX -1.0 / 41.8 | JAX -3 / 45.5    | -2.0 / -3.7             | JAX 53% / NE 47%  | JAX 43% / NE 57%   | Over 39% / Under 61% |           |
| KC @ MIA  | 2026-09-27 | KC 24.3, MIA 19.3  | 48.8-10.6   | MIA +5.0 / 43.6 | MIA +11.5 / 46.5 | +6.5 / -2.9             | MIA 35% / KC 65%  | MIA 70% / KC 30%   | Over 42% / Under 58% | MIA +11.5 |
| TEN @ NYG | 2026-09-27 | TEN 17.8, NYG 23.9 | 23.1-40.7   | NYG -6.1 / 41.7 | NYG -3.5 / 40.5  | +2.6 / +1.2             | NYG 68% / TEN 32% | NYG 55% / TEN 45%  | Over 54% / Under 46% |           |
| CIN @ PIT | 2026-09-27 | CIN 23.0, PIT 22.0 | 13.8-5.1    | PIT +1.0 / 45.0 | PIT +3.5 / 42.5  | +2.5 / +2.5             | PIT 47% / CIN 53% | PIT 60% / CIN 40%  | Over 58% / Under 42% |           |
| SEA @ WAS | 2026-09-27 | SEA 23.8, WAS 20.0 | 37.0-15.6   | WAS +3.8 / 43.8 | WAS +7 / 40.5    | +3.2 / +3.3             | WAS 39% / SEA 61% | WAS 64% / SEA 36%  | Over 60% / Under 40% |           |
| ARI @ SF  | 2026-09-27 | ARI 18.3, SF 28.9  | 16.2-38.7   | SF -10.6 / 47.2 | SF -8.5 / 47.5   | +2.1 / -0.3             | SF 79% / ARI 21%  | SF 52% / ARI 48%   | Over 49% / Under 51% |           |
| MIN @ TB  | 2026-09-27 | MIN 21.4, TB 20.3  | 27.1-8.5    | TB +1.1 / 41.6  | TB +1.5 / 42.5   | +0.4 / -0.9             | TB 46% / MIN 54%  | TB 49% / MIN 51%   | Over 47% / Under 53% |           |
| BAL @ DAL | 2026-09-27 | BAL 26.1, DAL 26.2 | 35.9-39.1   | DAL -0.1 / 52.3 | DAL +3 / 52.5    | +3.1 / -0.2             | DAL 50% / BAL 50% | DAL 60% / BAL 40%  | Over 49% / Under 51% |           |
| LV @ NO   | 2026-09-27 | LV 21.5, NO 23.5   | 27.0-14.0   | NO -2.0 / 45.0  | NO -3 / 43.5     | -1.0 / +1.5             | NO 56% / LV 44%   | NO 46% / LV 54%    | Over 54% / Under 46% |           |
| LA @ DEN  | 2026-09-27 | LA 23.5, DEN 22.3  | 11.0-18.9   | DEN +1.2 / 45.8 | DEN +2.5 / 45.5  | +1.3 / +0.3             | DEN 46% / LA 54%  | DEN 51% / LA 49%   | Over 51% / Under 49% |           |
| PHI @ CHI | 2026-09-28 | PHI 22.7, CHI 22.6 | 22.8-25.6   | CHI +0.1 / 45.3 | CHI +3 / 43.5    | +2.9 / +1.8             | CHI 49% / PHI 51% | CHI 59% / PHI 41%  | Over 55% / Under 45% |           |
