# Week 3, 2026: model picks

Our line is home spread / total. Edge = model minus Vegas (spread: positive favours the home side; total: positive favours the over).
Bet flag: spread when the edge is 5+ points, total when 6+. These are the thresholds with the best ROI that held in both backtest windows (2019 to 2022 and 2023 to 2025), but the samples are small: 131 spread bets at 5+ went 54.2% (+3.5% ROI), 57 total bets at 6+ went 61.4%. Edges under those thresholds have lost money in every window. Full table in docs/how_it_works.md.

| Game      | Date       | Our score          | Old model   | Our line        | Vegas            | Edge (spread / total)   | Home win   | Home cover   | Over   | Bet       |
|:----------|:-----------|:-------------------|:------------|:----------------|:-----------------|:------------------------|:-----------|:-------------|:-------|:----------|
| ATL @ GB  | 2026-09-24 | ATL 20.1, GB 25.7  | -10.9-14.1  | GB -5.6 / 45.7  | GB -7 / 43.5     | -1.4 / +2.2             | 66%        | 41%          | 57%    |           |
| LAC @ BUF | 2026-09-27 | LAC 19.7, BUF 29.3 | 12.5-52.6   | BUF -9.6 / 49.0 | BUF -7 / 50.5    | +2.6 / -1.5             | 76%        | 54%          | 45%    |           |
| CAR @ CLE | 2026-09-27 | CAR 21.0, CLE 23.4 | 40.4-14.9   | CLE -2.4 / 44.4 | CLE +3 / 42.5    | +5.4 / +1.9             | 57%        | 67%          | 56%    | CLE +3    |
| NYJ @ DET | 2026-09-27 | NYJ 22.6, DET 28.5 | 32.7-27.5   | DET -5.9 / 51.1 | DET -6.5 / 48.5  | -0.6 / +2.6             | 67%        | 45%          | 58%    |           |
| HOU @ IND | 2026-09-27 | HOU 23.2, IND 22.6 | 27.0-27.8   | IND +0.7 / 45.8 | IND +2.5 / 43.5  | +1.8 / +2.3             | 48%        | 53%          | 57%    |           |
| NE @ JAX  | 2026-09-27 | NE 21.0, JAX 22.3  | 5.0-16.4    | JAX -1.3 / 43.3 | JAX -3 / 45.5    | -1.7 / -2.2             | 54%        | 44%          | 43%    |           |
| KC @ MIA  | 2026-09-27 | KC 26.8, MIA 20.4  | 49.3-10.3   | MIA +6.3 / 47.2 | MIA +11.5 / 45.5 | +5.2 / +1.7             | 32%        | 67%          | 55%    | MIA +11.5 |
| TEN @ NYG | 2026-09-27 | TEN 17.8, NYG 26.3 | 23.2-40.9   | NYG -8.5 / 44.1 | NYG -6 / 43.5    | +2.5 / +0.6             | 74%        | 55%          | 52%    |           |
| CIN @ PIT | 2026-09-27 | CIN 22.9, PIT 21.3 | 13.6-5.1    | PIT +1.6 / 44.2 | PIT +3.5 / 42.5  | +1.9 / +1.7             | 45%        | 59%          | 55%    |           |
| SEA @ WAS | 2026-09-27 | SEA 23.6, WAS 20.3 | 37.1-15.7   | WAS +3.3 / 43.9 | WAS +6.5 / 39.5  | +3.2 / +4.4             | 40%        | 63%          | 63%    |           |
| ARI @ SF  | 2026-09-27 | ARI 17.1, SF 28.7  | 16.2-39.2   | SF -11.6 / 45.8 | SF -8.5 / 47.5   | +3.1 / -1.7             | 81%        | 54%          | 45%    |           |
| MIN @ TB  | 2026-09-27 | MIN 21.9, TB 21.6  | 26.7-8.4    | TB +0.3 / 43.5  | TB +1.5 / 42.5   | +1.2 / +1.0             | 49%        | 52%          | 53%    |           |
| BAL @ DAL | 2026-09-27 | BAL 26.2, DAL 24.8 | 36.0-39.4   | DAL +1.4 / 51.0 | DAL +3 / 52.5    | +1.6 / -1.5             | 46%        | 55%          | 45%    |           |
| LV @ NO   | 2026-09-27 | LV 22.5, NO 23.7   | 27.2-13.8   | NO -1.2 / 46.2  | NO -3 / 43.5     | -1.8 / +2.7             | 53%        | 44%          | 58%    |           |
| LA @ DEN  | 2026-09-27 | LA 23.1, DEN 23.5  | 11.2-19.1   | DEN -0.4 / 46.6 | DEN +2.5 / 45.5  | +2.9 / +1.1             | 51%        | 57%          | 53%    |           |
| PHI @ CHI | 2026-09-28 | PHI 22.8, CHI 21.8 | 24.0-22.8   | CHI +1.0 / 44.6 | CHI +3.5 / 44.5  | +2.5 / +0.1             | 47%        | 60%          | 50%    |           |
