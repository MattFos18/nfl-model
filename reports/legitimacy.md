# Legitimacy tests, 2026-09-24

1791 regular-season games 2019 to 2025, weeks 1 to 17, walk-forward predictions.

- Encompassing, 2019-22: margin = -0.87 + 0.766 x line + 0.276 x model (model t = 1.67). A model weight above zero with t past 2 means the line does not already contain what the model knows.
- Encompassing, 2023-25: margin = 0.20 + 1.024 x line + 0.153 x model (model t = 0.77). A model weight above zero with t past 2 means the line does not already contain what the model knows.
- Encompassing, all: margin = -0.41 + 0.851 x line + 0.240 x model (model t = 1.90). A model weight above zero with t past 2 means the line does not already contain what the model knows.

- Placebo: the real 4+ record is 132-80 (62.3%). Shuffling the model's lines within each week 2,000 times gives a mean of 51.3% and a 95th percentile of 53.2%; 0.00% of shuffles reach the real record.

- Bootstrap on the 212 real 4+ flags: 90% interval for the win rate 56.6% to 67.5%; 0.2% of resamples fall under the 52.4% break-even.

| Season | Games | 4+ flags | Spread miss, model | Spread miss, line | Model closer |
|---|---|---|---|---|---|
| 2019 | 256 | 18-13 | 10.30 | 10.21 | no |
| 2020 | 256 | 24-13 | 9.84 | 9.83 | no |
| 2021 | 256 | 24-14 | 10.97 | 10.83 | no |
| 2022 | 255 | 21-19 | 9.16 | 8.82 | no |
| 2023 | 256 | 11-4 | 10.17 | 9.93 | no |
| 2024 | 256 | 20-7 | 9.72 | 9.62 | no |
| 2025 | 256 | 14-10 | 10.02 | 9.83 | no |

- Leave-one-season-out 4+ records (each season dropped in turn): 114-67, 108-67, 108-66, 111-61, 121-76, 112-73, 118-70. No single season carries the record if every one of these stays above break-even.

Reading: the line beats the model on the miss every season (it should; it is the market). The question the flag rests on is whether the model's disagreements with the line carry information, which the encompassing weight, the placebo and the bootstrap answer.
