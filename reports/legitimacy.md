# Legitimacy tests, 2026-09-24

1791 regular-season games 2019 to 2025, weeks 1 to 17, walk-forward predictions.

- Encompassing, 2019-22: margin = -0.89 + 0.729 x line + 0.315 x model (model t = 1.88). A model weight above zero with t past 2 means the line does not already contain what the model knows.
- Encompassing, 2023-25: margin = 0.17 + 0.964 x line + 0.217 x model (model t = 1.05). A model weight above zero with t past 2 means the line does not already contain what the model knows.
- Encompassing, all: margin = -0.44 + 0.804 x line + 0.291 x model (model t = 2.24). A model weight above zero with t past 2 means the line does not already contain what the model knows.

- Placebo: the real 4+ record is 123-78 (61.2%). Shuffling the model's lines within each week 2,000 times gives a mean of 51.2% and a 95th percentile of 53.1%; 0.00% of shuffles reach the real record.

- Bootstrap on the 201 real 4+ flags: 90% interval for the win rate 55.2% to 66.7%; 0.4% of resamples fall under the 52.4% break-even.

| Season | Games | 4+ flags | Spread miss, model | Spread miss, line | Model closer |
|---|---|---|---|---|---|
| 2019 | 256 | 22-14 | 10.29 | 10.21 | no |
| 2020 | 256 | 25-12 | 9.84 | 9.83 | no |
| 2021 | 256 | 20-12 | 10.95 | 10.83 | no |
| 2022 | 255 | 15-19 | 9.15 | 8.82 | no |
| 2023 | 256 | 8-4 | 10.14 | 9.93 | no |
| 2024 | 256 | 19-7 | 9.67 | 9.62 | no |
| 2025 | 256 | 14-10 | 10.02 | 9.83 | no |

- Leave-one-season-out 4+ records (each season dropped in turn): 101-64, 98-66, 103-66, 108-59, 115-74, 104-71, 109-68. No single season carries the record if every one of these stays above break-even.

Reading: the line beats the model on the miss every season (it should; it is the market). The question the flag rests on is whether the model's disagreements with the line carry information, which the encompassing weight, the placebo and the bootstrap answer.
