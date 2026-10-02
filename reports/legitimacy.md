# Legitimacy tests, 2026-10-02

1791 regular-season games 2019 to 2025, weeks 1 to 17, walk-forward predictions.

- Encompassing, 2019-22: margin = -0.87 + 0.725 x line + 0.321 x model (model t = 1.90). A model weight above zero with t past 2 means the line does not already contain what the model knows.
- Encompassing, 2023-25: margin = 0.18 + 0.958 x line + 0.221 x model (model t = 1.05). A model weight above zero with t past 2 means the line does not already contain what the model knows.
- Encompassing, all: margin = -0.43 + 0.795 x line + 0.301 x model (model t = 2.30). A model weight above zero with t past 2 means the line does not already contain what the model knows.

- Placebo: the real 4+ record is 113-67 (62.8%). Shuffling the model's lines within each week 2,000 times gives a mean of 51.2% and a 95th percentile of 53.1%; 0.00% of shuffles reach the real record.

- Bootstrap on the 180 real 4+ flags: 90% interval for the win rate 56.7% to 68.3%; 0.2% of resamples fall under the 52.4% break-even.

| Season | Games | 4+ flags | Spread miss, model | Spread miss, line | Model closer |
|---|---|---|---|---|---|
| 2019 | 256 | 22-11 | 10.24 | 10.21 | no |
| 2020 | 256 | 22-9 | 9.82 | 9.83 | yes |
| 2021 | 256 | 18-9 | 10.96 | 10.83 | no |
| 2022 | 255 | 14-18 | 9.13 | 8.82 | no |
| 2023 | 256 | 6-3 | 10.10 | 9.93 | no |
| 2024 | 256 | 18-10 | 9.71 | 9.62 | no |
| 2025 | 256 | 13-7 | 9.99 | 9.83 | no |

- Leave-one-season-out 4+ records (each season dropped in turn): 91-56, 91-58, 95-58, 99-49, 107-64, 95-57, 100-60. No single season carries the record if every one of these stays above break-even.

Reading: the line beats the model on the miss every season (it should; it is the market). The question the flag rests on is whether the model's disagreements with the line carry information, which the encompassing weight, the placebo and the bootstrap answer.
