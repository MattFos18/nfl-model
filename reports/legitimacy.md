# Legitimacy tests, 2026-10-05

1791 regular-season games 2019 to 2025, weeks 1 to 17, walk-forward predictions.

- Encompassing, 2019-22: margin = -0.89 + 0.700 x line + 0.354 x model (model t = 2.12). A model weight above zero with t past 2 means the line does not already contain what the model knows.
- Encompassing, 2023-25: margin = 0.17 + 0.950 x line + 0.231 x model (model t = 1.10). A model weight above zero with t past 2 means the line does not already contain what the model knows.
- Encompassing, all: margin = -0.44 + 0.776 x line + 0.325 x model (model t = 2.50). A model weight above zero with t past 2 means the line does not already contain what the model knows.

- Placebo: the real 4+ record is 118-69 (63.1%). Shuffling the model's lines within each week 2,000 times gives a mean of 51.2% and a 95th percentile of 53.1%; 0.00% of shuffles reach the real record.

- Bootstrap on the 187 real 4+ flags: 90% interval for the win rate 57.2% to 68.4%; 0.1% of resamples fall under the 52.4% break-even.

| Season | Games | 4+ flags | Spread miss, model | Spread miss, line | Model closer |
|---|---|---|---|---|---|
| 2019 | 256 | 25-13 | 10.23 | 10.21 | no |
| 2020 | 256 | 22-10 | 9.80 | 9.83 | yes |
| 2021 | 256 | 17-10 | 10.95 | 10.83 | no |
| 2022 | 255 | 16-19 | 9.14 | 8.82 | no |
| 2023 | 256 | 6-3 | 10.09 | 9.93 | no |
| 2024 | 256 | 18-8 | 9.73 | 9.62 | no |
| 2025 | 256 | 14-6 | 9.97 | 9.83 | no |

- Leave-one-season-out 4+ records (each season dropped in turn): 93-56, 96-59, 101-59, 102-50, 112-66, 100-61, 104-63. No single season carries the record if every one of these stays above break-even.

Reading: the line beats the model on the miss every season (it should; it is the market). The question the flag rests on is whether the model's disagreements with the line carry information, which the encompassing weight, the placebo and the bootstrap answer.
