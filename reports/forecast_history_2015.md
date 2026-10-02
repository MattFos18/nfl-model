# Forecast history back to 2015

2 Oct 2026. `experiments/forecast_history_2015.py`; data `data/weather/forecast_history.csv` (fetched by `nflmodel/forecast_history.py`, `FIRST = 2015`).

Approved goal (Matt): the backtest prices every played game exactly as live, on the pre-kickoff forecast. Until now 2015-2017 used the weather that happened, because the stored forecasts began in 2018.

## What reaches back

- GFS MOS (Iowa Environmental Mesonet MOS archive): yes, every 2015-2017 run asked.
- Japan's model (Open-Meteo previous runs): from 1 Jan 2016 only (an earlier start date is refused). None for the 2015 regular season; all of 2016-2017.
- National Blend (NBS): from 7 Nov 2018. None.

The wind reading stays the mean of the pre-kickoff forecasts that exist (`wind_live.readings`): GFS alone for 2015, GFS and Japan's day-before run for 2016-2017, as live when one source is missing.

## Data checks (2015-2017 rows)

| Season | Outdoor US games | Stored | GFS wind d0 | GFS wind d1 | GFS temp d0 | GFS rain d0 | Japan d1 | NBS |
|---|---|---|---|---|---|---|---|---|
| 2015 | 202 | 202 | 202 | 202 | 202 | 202 | 20 | 0 |
| 2016 | 196 | 196 | 196 | 196 | 196 | 196 | 196 | 0 |
| 2017 | 200 | 200 | 200 | 200 | 200 | 200 | 200 | 0 |

- GFS last run before kickoff: 5.0 to 9.7 hours (every run 598 of 598 at 5+ hours); the day-before run is 12Z the Eastern day before.
- Largest wind 29.3 mph, largest temperature 90.3 F, rain chance 0 to 100%: no 99 / 999 sentinels (0 wind values at 99+, 0 temperatures at 900+).
- Japan's model before 1 Jan 2016: 0 values (none asked); games abroad stored: 0; duplicates: 0.
- GFS d0 against Japan d1: correlation 0.64 on 416 games 2016-2017, 0.68 on 1451 games 2018 on; mean GFS d0 9.0 mph 2015-2017, 9.5 2018 on.
- build.fix_wind with the 2015-2017 forecasts: 5 schedule winds decided differently (2015_02_DEN_KC, 2015_10_MIN_OAK, 2015_16_SD_OAK, 2016_05_ARI_SF, 2016_12_KC_DEN). The walk-forward below reads `features_asof.parquet` as built; the weekly build applies this.

## Walk-forward 2015-2025, before -> after

Before: the history cut to 2018 on. After: the full history (2015-2017 priced on the forecast, the wind points' pool and the rain input's training rows from 2015).

| Window | Spread flag (4+) | Totals flag (55% under) | Wind under (10+ mph) | Team points miss | Total miss | Margin miss |
|---|---|---|---|---|---|---|
| 2015-18 | 69-55 -> 69-56 | 132-117 -> 128-113 | 24-20 -> 118-94 | 7.4046 -> 7.3991 | 10.7507 -> 10.7472 | 9.9508 -> 9.9492 |
| 2019-22 | 77-48 -> 77-48 | 190-146 -> 176-142 | 143-88 -> 143-88 | 7.3645 -> 7.3731 | 10.5161 -> 10.5303 | 10.0109 -> 10.0109 |
| 2023-25 | 37-20 -> 37-20 | 82-59 -> 78-54 | 77-52 -> 77-52 | 7.2345 -> 7.2349 | 10.1029 -> 10.1032 | 9.9061 -> 9.9061 |

## Study gate (total miss)

| Check | Pass | Detail |
|---|---|---|
| better on 2015-18 | yes | miss 10.7507 -> 10.7472 |
| better on 2019-22 | no | miss 10.5161 -> 10.5303 |
| better on 2023-25 | no | miss 10.1029 -> 10.1032 |
| no bet cost: spread flag, 2015-18 | no | 69-55 -> 69-56 |
| no bet cost: totals flag, 2015-18 | yes | 132-117 -> 128-113 |
| no bet cost: wind under, 2015-18 | yes | 24-20 -> 118-94 |
| no bet cost: spread flag, 2019-22 | yes | 77-48 -> 77-48 |
| no bet cost: totals flag, 2019-22 | no | 190-146 -> 176-142 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 37-20 -> 37-20 |
| no bet cost: totals flag, 2023-25 | yes | 82-59 -> 78-54 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |

Not a new input: the approved honest pricing. The gate is shown for the record; no placebo is run (nothing is chosen from these numbers).

## Why 2019-2025 move too: the live model changes

The stored forecasts are training data as well as prices. With 2015-2017 stored, the totals equation's rain input (`rain_fc`, the GFS chance 50%+) is learned on 2015-2017 rows that were 0 before, and the wind points' pool (each season's band amounts from earlier seasons) starts in 2015 instead of 2018. So the live total moves: on 2019-22 the total miss rises and the totals flag gives back 10 net wins; 2023-25 is flat. The spread flag and the wind under there do not move (the wind under reads the reading, not the model).

## Storage

`data/weather/forecast_history.csv` is rewritten by the weekly run (`forecast_history.backfill` appends each week's played games and `weekly.yml` commits `data/weather`), so the PR commits code only: with `FIRST = 2015` the weekly run fetches the 598 games itself on GitHub's network, ten minutes a run (about two runs). The numbers above are from the same fetch path run here.
