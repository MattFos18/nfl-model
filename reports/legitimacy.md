# Legitimacy tests, 2026-09-25

1791 regular-season games 2019 to 2025, weeks 1 to 17, walk-forward predictions.

- Encompassing, 2019-22: margin = -0.88 + 0.723 x line + 0.323 x model (model t = 1.91). A model weight above zero with t past 2 means the line does not already contain what the model knows.
- Encompassing, 2023-25: margin = 0.16 + 0.936 x line + 0.249 x model (model t = 1.19). A model weight above zero with t past 2 means the line does not already contain what the model knows.
- Encompassing, all: margin = -0.43 + 0.789 x line + 0.309 x model (model t = 2.36). A model weight above zero with t past 2 means the line does not already contain what the model knows.

- Placebo: the real 4+ record is 120-72 (62.5%). Shuffling the model's lines within each week 2,000 times gives a mean of 51.2% and a 95th percentile of 53.1%; 0.00% of shuffles reach the real record.

- Bootstrap on the 192 real 4+ flags: 90% interval for the win rate 56.8% to 68.2%; 0.1% of resamples fall under the 52.4% break-even.

| Season | Games | 4+ flags | Spread miss, model | Spread miss, line | Model closer |
|---|---|---|---|---|---|
| 2019 | 256 | 24-12 | 10.25 | 10.21 | no |
| 2020 | 256 | 24-9 | 9.81 | 9.83 | yes |
| 2021 | 256 | 18-10 | 10.96 | 10.83 | no |
| 2022 | 255 | 14-20 | 9.17 | 8.82 | no |
| 2023 | 256 | 6-3 | 10.09 | 9.93 | no |
| 2024 | 256 | 21-9 | 9.68 | 9.62 | no |
| 2025 | 256 | 13-9 | 10.02 | 9.83 | no |

- Leave-one-season-out 4+ records (each season dropped in turn): 96-60, 96-63, 102-62, 106-52, 114-69, 99-63, 107-63. No single season carries the record if every one of these stays above break-even.

Reading: the line beats the model on the miss every season (it should; it is the market). The question the flag rests on is whether the model's disagreements with the line carry information, which the encompassing weight, the placebo and the bootstrap answer.
