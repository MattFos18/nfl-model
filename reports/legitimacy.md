# Legitimacy tests, 2026-09-24

1791 regular-season games 2019 to 2025, weeks 1 to 17, walk-forward predictions.

- Encompassing, 2019-22: margin = -0.90 + 0.723 x line + 0.323 x model (model t = 1.93). A model weight above zero with t past 2 means the line does not already contain what the model knows.
- Encompassing, 2023-25: margin = 0.16 + 0.956 x line + 0.227 x model (model t = 1.10). A model weight above zero with t past 2 means the line does not already contain what the model knows.
- Encompassing, all: margin = -0.44 + 0.798 x line + 0.299 x model (model t = 2.31). A model weight above zero with t past 2 means the line does not already contain what the model knows.

- Placebo: the real 4+ record is 122-77 (61.3%). Shuffling the model's lines within each week 2,000 times gives a mean of 51.2% and a 95th percentile of 53.1%; 0.00% of shuffles reach the real record.

- Bootstrap on the 199 real 4+ flags: 90% interval for the win rate 55.8% to 66.8%; 0.4% of resamples fall under the 52.4% break-even.

| Season | Games | 4+ flags | Spread miss, model | Spread miss, line | Model closer |
|---|---|---|---|---|---|
| 2019 | 256 | 21-14 | 10.29 | 10.21 | no |
| 2020 | 256 | 25-12 | 9.83 | 9.83 | yes |
| 2021 | 256 | 20-12 | 10.94 | 10.83 | no |
| 2022 | 255 | 15-18 | 9.15 | 8.82 | no |
| 2023 | 256 | 8-3 | 10.14 | 9.93 | no |
| 2024 | 256 | 19-7 | 9.67 | 9.62 | no |
| 2025 | 256 | 14-11 | 10.02 | 9.83 | no |

- Leave-one-season-out 4+ records (each season dropped in turn): 101-63, 97-65, 102-65, 107-59, 114-74, 103-70, 108-66. No single season carries the record if every one of these stays above break-even.

Reading: the line beats the model on the miss every season (it should; it is the market). The question the flag rests on is whether the model's disagreements with the line carry information, which the encompassing weight, the placebo and the bootstrap answer.
