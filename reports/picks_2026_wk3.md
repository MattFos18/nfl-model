# Week 3, 2026: model picks

Our line is home spread / total. Edge = model minus Vegas (spread: positive favours the home side; total: positive favours the over). Win, cover and total are the model's chances for each side at the current line; 52.4% is break-even at -110.
Bet flag: spread when the edge is 5+ points, total when 6+. These are the thresholds with the best ROI that held in both backtest windows (2019 to 2022 and 2023 to 2025), but the samples are small: 127 spread bets at 5+ went 53.5% (+2.2% ROI), 61 total bets at 6+ went 60.7% (+15.8%). Edges under those thresholds have lost money in every window. No flags in Week 18, where resting starters make the line smarter than the ratings (flags there went 7-11). Full table in docs/how_it_works.md.

| Game      | Date       | Our score          | Old model   | Our line        | Vegas            | Edge (spread / total)   | Win               | Cover the spread   | Total                | Flag      |
|:----------|:-----------|:-------------------|:------------|:----------------|:-----------------|:------------------------|:------------------|:-------------------|:---------------------|:----------|
| ATL @ GB  | 2026-09-24 | ATL 20.2, GB 25.7  | -10.8-14.3  | GB -5.5 / 45.9  | GB -6.5 / 43.5   | -1.0 / +2.4             | GB 66% / ATL 34%  | GB 44% / ATL 56%   | Over 57% / Under 43% |           |
| LAC @ BUF | 2026-09-27 | LAC 19.7, BUF 29.3 | 12.6-52.6   | BUF -9.6 / 49.0 | BUF -7 / 50.5    | +2.6 / -1.5             | BUF 76% / LAC 24% | BUF 54% / LAC 46%  | Over 45% / Under 55% |           |
| CAR @ CLE | 2026-09-27 | CAR 21.1, CLE 23.4 | 37.5-15.8   | CLE -2.3 / 44.5 | CLE +3 / 42.5    | +5.3 / +2.0             | CLE 57% / CAR 43% | CLE 67% / CAR 33%  | Over 56% / Under 44% | CLE +3    |
| NYJ @ DET | 2026-09-27 | NYJ 22.6, DET 28.5 | 32.6-27.5   | DET -5.9 / 51.2 | DET -6.5 / 48.5  | -0.6 / +2.7             | DET 67% / NYJ 33% | DET 45% / NYJ 55%  | Over 58% / Under 42% |           |
| HOU @ IND | 2026-09-27 | HOU 23.2, IND 22.6 | 27.0-27.9   | IND +0.7 / 45.8 | IND +2.5 / 43.5  | +1.8 / +2.3             | IND 48% / HOU 52% | IND 53% / HOU 47%  | Over 57% / Under 43% |           |
| NE @ JAX  | 2026-09-27 | NE 21.0, JAX 22.3  | 5.1-16.4    | JAX -1.3 / 43.3 | JAX -3 / 45.5    | -1.7 / -2.2             | JAX 54% / NE 46%  | JAX 44% / NE 56%   | Over 44% / Under 56% |           |
| KC @ MIA  | 2026-09-27 | KC 26.8, MIA 20.5  | 48.8-10.6   | MIA +6.3 / 47.3 | MIA +11.5 / 45.5 | +5.2 / +1.8             | MIA 32% / KC 68%  | MIA 67% / KC 33%   | Over 55% / Under 45% | MIA +11.5 |
| TEN @ NYG | 2026-09-27 | TEN 17.9, NYG 26.4 | 23.1-40.7   | NYG -8.4 / 44.3 | NYG -6 / 43.5    | +2.4 / +0.8             | NYG 73% / TEN 27% | NYG 55% / TEN 45%  | Over 52% / Under 48% |           |
| CIN @ PIT | 2026-09-27 | CIN 22.9, PIT 21.3 | 13.8-5.1    | PIT +1.6 / 44.1 | PIT +3.5 / 42.5  | +1.9 / +1.6             | PIT 45% / CIN 55% | PIT 58% / CIN 42%  | Over 55% / Under 45% |           |
| SEA @ WAS | 2026-09-27 | SEA 23.7, WAS 20.3 | 37.0-15.6   | WAS +3.4 / 43.9 | WAS +6.5 / 39.5  | +3.1 / +4.4             | WAS 40% / SEA 60% | WAS 63% / SEA 37%  | Over 63% / Under 37% |           |
| ARI @ SF  | 2026-09-27 | ARI 17.2, SF 28.6  | 16.2-38.7   | SF -11.4 / 45.8 | SF -8.5 / 47.5   | +2.9 / -1.7             | SF 80% / ARI 20%  | SF 54% / ARI 46%   | Over 45% / Under 55% |           |
| MIN @ TB  | 2026-09-27 | MIN 21.9, TB 21.6  | 27.1-8.5    | TB +0.3 / 43.5  | TB +1.5 / 42.5   | +1.2 / +1.0             | TB 49% / MIN 51%  | TB 52% / MIN 48%   | Over 53% / Under 47% |           |
| BAL @ DAL | 2026-09-27 | BAL 26.1, DAL 24.7 | 35.9-39.1   | DAL +1.5 / 50.8 | DAL +3 / 52.5    | +1.5 / -1.7             | DAL 46% / BAL 54% | DAL 55% / BAL 45%  | Over 45% / Under 55% |           |
| LV @ NO   | 2026-09-27 | LV 22.5, NO 23.7   | 27.0-14.0   | NO -1.2 / 46.2  | NO -3 / 43.5     | -1.8 / +2.7             | NO 53% / LV 47%   | NO 44% / LV 56%    | Over 58% / Under 42% |           |
| LA @ DEN  | 2026-09-27 | LA 23.1, DEN 23.6  | 11.0-18.9   | DEN -0.4 / 46.7 | DEN +2.5 / 45.5  | +2.9 / +1.2             | DEN 51% / LA 49%  | DEN 57% / LA 43%   | Over 54% / Under 46% |           |
| PHI @ CHI | 2026-09-28 | PHI 22.9, CHI 21.9 | 22.8-25.6   | CHI +0.9 / 44.8 | CHI +3.5 / 44.5  | +2.6 / +0.3             | CHI 47% / PHI 53% | CHI 60% / PHI 40%  | Over 51% / Under 49% |           |
