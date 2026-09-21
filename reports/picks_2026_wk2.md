# Week 2, 2026: model picks

Our line is home spread / total. Edge = model minus Vegas (spread: positive favours the home side; total: positive favours the over). Win, cover and total are the model's chances for each side at the current line; 52.4% is break-even at -110.
Bet flag: spread when the edge is 5+ points, total when 6+. These are the thresholds with the best ROI that held in both backtest windows (2019 to 2022 and 2023 to 2025), but the samples are small: 127 spread bets at 5+ went 53.5% (+2.2% ROI), 61 total bets at 6+ went 60.7% (+15.8%). Edges under those thresholds have lost money in every window. Full table in docs/how_it_works.md.

| Game      | Date       | Our score          | Old model   | Our line        | Vegas           | Edge (spread / total)   | Win               | Cover the spread   | Total                | Flag     |
|:----------|:-----------|:-------------------|:------------|:----------------|:----------------|:------------------------|:------------------|:-------------------|:---------------------|:---------|
| DET @ BUF | 2026-09-17 | DET 24.4, BUF 29.1 | 39.0-34.1   | BUF -4.8 / 53.5 | BUF -5.5 / 54.5 | -0.7 / -1.0             | BUF 64% / DET 36% | BUF 46% / DET 54%  | Over 47% / Under 53% |          |
| CAR @ ATL | 2026-09-20 | CAR 19.6, ATL 27.7 | 22.0-2.9    | ATL -8.1 / 47.4 | ATL +2.5 / 43.5 | +10.6 / +3.9            | ATL 73% / CAR 27% | ATL 77% / CAR 23%  | Over 61% / Under 39% | ATL +2.5 |
| NO @ BAL  | 2026-09-20 | NO 19.2, BAL 27.7  | 20.5-50.9   | BAL -8.6 / 46.9 | BAL -8.5 / 45.5 | +0.1 / +1.4             | BAL 74% / NO 26%  | BAL 45% / NO 55%   | Over 54% / Under 46% |          |
| MIN @ CHI | 2026-09-20 | MIN 22.0, CHI 24.0 | 42.2-36.4   | CHI -2.0 / 46.0 | CHI -4.5 / 46.5 | -2.5 / -0.5             | CHI 56% / MIN 44% | CHI 40% / MIN 60%  | Over 49% / Under 51% |          |
| CIN @ HOU | 2026-09-20 | CIN 24.7, HOU 25.8 | 45.7-25.9   | HOU -1.1 / 50.5 | HOU -3 / 45.5   | -1.9 / +5.0             | HOU 53% / CIN 47% | HOU 43% / CIN 57%  | Over 64% / Under 36% |          |
| PIT @ NE  | 2026-09-20 | PIT 19.4, NE 23.9  | 15.0-4.2    | NE -4.6 / 43.3  | NE -4.5 / 41.5  | +0.1 / +1.8             | NE 63% / PIT 37%  | NE 47% / PIT 53%   | Over 55% / Under 45% |          |
| GB @ NYJ  | 2026-09-20 | GB 24.0, NYJ 22.3  | 9.8-39.6    | NYJ +1.7 / 46.2 | NYJ +3.5 / 44.5 | +1.8 / +1.7             | NYJ 45% / GB 55%  | NYJ 58% / GB 42%   | Over 55% / Under 45% |          |
| CLE @ TB  | 2026-09-20 | CLE 20.7, TB 25.0  | 3.5-16.6    | TB -4.3 / 45.6  | TB -8.5 / 41.5  | -4.2 / +4.1             | TB 62% / CLE 38%  | TB 32% / CLE 68%   | Over 62% / Under 38% |          |
| PHI @ TEN | 2026-09-20 | PHI 24.4, TEN 18.6 | 32.7-12.2   | TEN +5.9 / 43.0 | TEN +7 / 39.5   | +1.1 / +3.5             | TEN 33% / PHI 67% | TEN 59% / PHI 41%  | Over 60% / Under 40% |          |
| JAX @ DEN | 2026-09-20 | JAX 23.1, DEN 20.5 | 46.7-5.7    | DEN +2.6 / 43.6 | DEN -2.5 / 45.5 | -5.1 / -1.9             | DEN 42% / JAX 58% | DEN 37% / JAX 63%  | Over 44% / Under 56% | JAX +2.5 |
| LV @ LAC  | 2026-09-20 | LV 20.8, LAC 22.6  | 33.6-8.3    | LAC -1.7 / 43.4 | LAC -6.5 / 43.5 | -4.8 / -0.1             | LAC 55% / LV 45%  | LAC 33% / LV 67%   | Over 50% / Under 50% |          |
| SEA @ ARI | 2026-09-20 | SEA 22.9, ARI 20.4 | 12.2-15.6   | ARI +2.5 / 43.3 | ARI +3.5 / 40.5 | +1.0 / +2.8             | ARI 43% / SEA 57% | ARI 56% / SEA 44%  | Over 58% / Under 42% |          |
| WAS @ DAL | 2026-09-20 | WAS 24.2, DAL 26.8 | 43.5-37.1   | DAL -2.6 / 51.0 | DAL -3.5 / 51.5 | -0.9 / -0.5             | DAL 58% / WAS 42% | DAL 44% / WAS 56%  | Over 49% / Under 51% |          |
| MIA @ SF  | 2026-09-20 | MIA 18.6, SF 28.3  | 5.3-34.4    | SF -9.7 / 46.9  | SF -12.5 / 44.5 | -2.8 / +2.4             | SF 77% / MIA 23%  | SF 40% / MIA 60%   | Over 57% / Under 43% |          |
| IND @ KC  | 2026-09-20 | IND 18.0, KC 27.5  | 11.5-46.8   | KC -9.5 / 45.5  | KC -6 / 46.5    | +3.5 / -1.0             | KC 76% / IND 24%  | KC 58% / IND 42%   | Over 47% / Under 53% |          |
| NYG @ LA  | 2026-09-21 | NYG 23.3, LA 27.0  | 44.8-12.4   | LA -3.7 / 50.4  | LA -6.5 / 47.5  | -2.8 / +2.9             | LA 61% / NYG 39%  | LA 39% / NYG 61%   | Over 58% / Under 42% |          |
