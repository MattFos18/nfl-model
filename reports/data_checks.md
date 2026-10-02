# Data checks

The tables the model reads, checked for shape before pricing (nflmodel/data_checks.py).

| Check | Passes | Detail |
|---|---|---|
| games: every column the model reads | yes | 16 present |
| games: one row per game | yes | 0 duplicate game ids |
| games: every team's full regular season (finished seasons) | yes | 11 seasons, 2015 to 2025 |
| games: no team twice in one week | yes | 0 repeats in 2026 |
| games: scores whole numbers from 0 to 80 | yes | 2944 played games |
| games: result and total add up from the scores | yes | 0 games off |
| games: closing spread and total for every played game | yes | 0 missing |
| games: lines in range (spread within 30, total 25 to 70) | yes | 0 out of range |
| team games: two rows per played game | yes | 0 games without two rows; 0 played games missing |
| team games: each side's points mirror the other's | yes | 0 rows off |
| predictions: every column the page and records read | yes | present |
| predictions: one row per game | yes | 0 duplicates |
| predictions: every played regular-season game priced | yes | 0 missing |
| predictions: finite and in range (total 20 to 75, spread within 35) | yes | 3167 games |

Result: PASS (14 of 14)
