# Legitimacy tests, 2026-09-23

1791 regular-season games 2019 to 2025, weeks 1 to 17, walk-forward predictions.

- Encompassing, 2019-22: margin = -0.88 + 0.770 x line + 0.279 x model (model t = 1.68). A model weight above zero with t past 2 means the line does not already contain what the model knows.
- Encompassing, 2023-25: margin = 0.20 + 1.039 x line + 0.140 x model (model t = 0.70). A model weight above zero with t past 2 means the line does not already contain what the model knows.
- Encompassing, all: margin = -0.42 + 0.861 x line + 0.236 x model (model t = 1.86). A model weight above zero with t past 2 means the line does not already contain what the model knows.

- Placebo: the real 4+ record is 131-87 (60.1%). Shuffling the model's lines within each week 2,000 times gives a mean of 51.3% and a 95th percentile of 53.2%; 0.00% of shuffles reach the real record.

- Bootstrap on the 218 real 4+ flags: 90% interval for the win rate 54.6% to 65.1%; 1.1% of resamples fall under the 52.4% break-even.

| Season | Games | 4+ flags | Spread miss, model | Spread miss, line | Model closer |
|---|---|---|---|---|---|
| 2019 | 256 | 18-14 | 10.31 | 10.21 | no |
| 2020 | 256 | 28-13 | 9.86 | 9.83 | no |
| 2021 | 256 | 26-20 | 11.01 | 10.83 | no |
| 2022 | 255 | 17-18 | 9.07 | 8.82 | no |
| 2023 | 256 | 9-4 | 10.18 | 9.93 | no |
| 2024 | 256 | 20-9 | 9.80 | 9.62 | no |
| 2025 | 256 | 13-9 | 10.02 | 9.83 | no |

- Leave-one-season-out 4+ records (each season dropped in turn): 113-73, 103-74, 105-67, 114-69, 122-83, 111-78, 118-78. No single season carries the record if every one of these stays above break-even.

Reading: the line beats the model on the miss every season (it should; it is the market). The question the flag rests on is whether the model's disagreements with the line carry information, which the encompassing weight, the placebo and the bootstrap answer.
