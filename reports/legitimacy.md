# Legitimacy tests, 2026-09-24

1791 regular-season games 2019 to 2025, weeks 1 to 17, walk-forward predictions.

- Encompassing, 2019-22: margin = -0.91 + 0.707 x line + 0.343 x model (model t = 2.08). A model weight above zero with t past 2 means the line does not already contain what the model knows.
- Encompassing, 2023-25: margin = 0.18 + 0.989 x line + 0.191 x model (model t = 0.94). A model weight above zero with t past 2 means the line does not already contain what the model knows.
- Encompassing, all: margin = -0.44 + 0.802 x line + 0.296 x model (model t = 2.32). A model weight above zero with t past 2 means the line does not already contain what the model knows.

- Placebo: the real 4+ record is 128-84 (60.4%). Shuffling the model's lines within each week 2,000 times gives a mean of 51.2% and a 95th percentile of 53.1%; 0.00% of shuffles reach the real record.

- Bootstrap on the 212 real 4+ flags: 90% interval for the win rate 54.7% to 65.6%; 1.1% of resamples fall under the 52.4% break-even.

| Season | Games | 4+ flags | Spread miss, model | Spread miss, line | Model closer |
|---|---|---|---|---|---|
| 2019 | 256 | 20-13 | 10.26 | 10.21 | no |
| 2020 | 256 | 26-13 | 9.82 | 9.83 | yes |
| 2021 | 256 | 24-15 | 10.95 | 10.83 | no |
| 2022 | 255 | 16-19 | 9.16 | 8.82 | no |
| 2023 | 256 | 9-4 | 10.13 | 9.93 | no |
| 2024 | 256 | 20-8 | 9.70 | 9.62 | no |
| 2025 | 256 | 13-12 | 10.03 | 9.83 | no |

- Leave-one-season-out 4+ records (each season dropped in turn): 108-71, 102-71, 104-69, 112-65, 119-80, 108-76, 115-72. No single season carries the record if every one of these stays above break-even.

Reading: the line beats the model on the miss every season (it should; it is the market). The question the flag rests on is whether the model's disagreements with the line carry information, which the encompassing weight, the placebo and the bootstrap answer.
