# Legitimacy tests, 2026-09-25

1791 regular-season games 2019 to 2025, weeks 1 to 17, walk-forward predictions.

- Encompassing, 2019-22: margin = -0.89 + 0.728 x line + 0.317 x model (model t = 1.88). A model weight above zero with t past 2 means the line does not already contain what the model knows.
- Encompassing, 2023-25: margin = 0.16 + 0.964 x line + 0.217 x model (model t = 1.06). A model weight above zero with t past 2 means the line does not already contain what the model knows.
- Encompassing, all: margin = -0.44 + 0.803 x line + 0.292 x model (model t = 2.25). A model weight above zero with t past 2 means the line does not already contain what the model knows.

- Placebo: the real 4+ record is 121-78 (60.8%). Shuffling the model's lines within each week 2,000 times gives a mean of 51.2% and a 95th percentile of 53.1%; 0.00% of shuffles reach the real record.

- Bootstrap on the 199 real 4+ flags: 90% interval for the win rate 55.3% to 66.3%; 0.9% of resamples fall under the 52.4% break-even.

| Season | Games | 4+ flags | Spread miss, model | Spread miss, line | Model closer |
|---|---|---|---|---|---|
| 2019 | 256 | 22-13 | 10.29 | 10.21 | no |
| 2020 | 256 | 25-12 | 9.84 | 9.83 | no |
| 2021 | 256 | 20-12 | 10.95 | 10.83 | no |
| 2022 | 255 | 14-18 | 9.15 | 8.82 | no |
| 2023 | 256 | 8-4 | 10.14 | 9.93 | no |
| 2024 | 256 | 19-8 | 9.67 | 9.62 | no |
| 2025 | 256 | 13-11 | 10.02 | 9.83 | no |

- Leave-one-season-out 4+ records (each season dropped in turn): 99-65, 96-66, 101-66, 107-60, 113-74, 102-70, 108-67. No single season carries the record if every one of these stays above break-even.

Reading: the line beats the model on the miss every season (it should; it is the market). The question the flag rests on is whether the model's disagreements with the line carry information, which the encompassing weight, the placebo and the bootstrap answer.
