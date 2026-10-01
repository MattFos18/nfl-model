# Five ideas from a friend's model (1 Oct 2026)

`experiments/friend_ideas.py`; every row in `reports/friend_ideas.csv`. Rule: `reports/round3_rule.md` (better on 2015-18, 2019-22 and 2023-25; no bet cost; beats its own placebo, 50 within-season shuffles, at most 5 matching it on any window; no market input, no look-ahead, no new source). Regular season, weeks 1 to 17, graded at the closing line, pushes out. Straight bets at -110: a win is +1 unit, a loss -1.1; ROI is units over the amount risked.

The live totals flag (unders at a raw 55%+ chance) for reference: 135-127 (-4.7u), 175-128 (+34.2u), 71-59 (+6.1u).

## Verdicts

| idea | verdict | why |
|---|---|---|
| 1. Wind/gust under rule | **track as a hidden shadow** | On the weather that happened, unders at wind 10+ mph (schedule wind) went 139-102, 141-96, 78-59 (+75.3u) and beat its placebo (2 of 50), but that weather is look-ahead; the day-before forecast, the only reading known before kickoff, exists for 2024-25 only (wind 10+: 52-47, +0.3u; gust 20+: 47-35, +8.5u); the model adds nothing inside windy games, and no wind-plus-flag rule beats the flag on every window. Not bet; worth wiring in as a hidden shadow on the live forecast (outdoor unders at forecast wind 10+ mph) so it earns a forecast record. |
| 2. Gusts in the total equation | **reject** | The outdoor kickoff gust lowers the total miss on every window (-0.0057 / -0.0050 / -0.0059) but no more than the same column shuffled within season (18 of 50 draws match it: the gain is the outdoor-or-roof split, not the gust), it costs totals-flag wins on 2015-18, 2019-22, the gust-over-wind and gust-for-wind forms are worse on at least one window, and the gust is observed weather. |
| 3. Forecast history to 2018 | **reject for now (needs data)** | Our day-before forecasts carry wind and gusts only from Jan 2024, and the free sources that reach 2018 are a coarse wind-only model (Open-Meteo previous runs, JMA GSM) or airport station guidance (Iowa Mesonet MOS archive), so a three-window forecast test needs a fetch from GitHub's network first. |
| 4. Fixed teaser rule | **track as a hidden shadow (dog legs only, blind)** | Dog legs (+1.5 to +2.5) won 77.0%, 77.7% and 77.2% and their teasers made +7.4, +6.9, +12.2 units even at -130, but favorite legs fell to 61.7% on 2023-25 and the model filter does not beat its placebo on any leg set; a known market angle on the closing line, so tracked, not bet. |
| 5. Points-per-drive rating | **reject** | Points per drive is close to the ratings already in (correlation 0.94 with the offense's points rating, 0.95 with its EPA per play); no form lowers the team points miss on all three windows (added to the points equation +0.0024 / -0.0047 / +0.0019; added to the points and total equations +0.0057 / +0.0006 / +0.0028; in place of EPA per play +0.0043 / -0.0065 / +0.0018; in place of the points rating +0.0152 / +0.0091 / +0.0120), 4 of 4 cost flag wins or calibration, and only in place of the points rating (5 of 50) beats its placebo, and only because a shuffled rating in place of a live one is worse still. |

## 1. Wind and gust unders

Outdoor and open-roof games. Every weather reading here is the weather that happened (look-ahead): the market closed on a forecast, so a record on observed wind overstates what a bettor could have had. Readings by season (outdoor games, weeks 1-17):

| season | outdoor games | wind_s | wind_r | gust_r | wind_f | gust_f |
|---|---|---|---|---|---|---|
| 2015 | 196 | 192 | 196 | 196 | 0 | 0 |
| 2016 | 194 | 192 | 194 | 194 | 0 | 0 |
| 2017 | 197 | 192 | 197 | 197 | 0 | 0 |
| 2018 | 196 | 191 | 196 | 196 | 0 | 0 |
| 2019 | 197 | 190 | 197 | 197 | 0 | 0 |
| 2020 | 165 | 165 | 165 | 165 | 0 | 0 |
| 2021 | 183 | 173 | 183 | 183 | 0 | 0 |
| 2022 | 175 | 84 | 175 | 175 | 0 | 0 |
| 2023 | 181 | 140 | 181 | 181 | 0 | 0 |
| 2024 | 169 | 164 | 169 | 169 | 169 | 169 |
| 2025 | 169 | 165 | 169 | 169 | 167 | 167 |

The schedule's wind is missing for half the 2022 and a fifth of the 2023 outdoor games (the model fills them with the median); the ERA5 kickoff archive covers every season.

### Blind: the under in every qualifying game

W-L (win %, units at -110) per window.

| rule | 2015-18 | 2019-22 | 2023-25 | ROI 2015-18 / 19-22 / 23-25 | placebo (draws of 50 that matched it) |
|---|---|---|---|---|---|
| Under, wind 10+ mph (schedule wind (observed)) | 139-102 (57.7%, +26.8u) | 141-96 (59.5%, +35.4u) | 78-59 (56.9%, +13.1u) | 10.1% / 13.6% / 8.7% | 2 (pass) |
| Under, wind 12+ mph (schedule wind (observed)) | 91-64 (58.7%, +20.6u) | 98-72 (57.6%, +18.8u) | 49-41 (54.4%, +3.9u) | 12.1% / 10.1% / 3.9% | 13 (fail) |
| Under, wind 15+ mph (schedule wind (observed)) | 45-34 (57.0%, +7.6u) | 46-41 (52.9%, +0.9u) | 21-20 (51.2%, -1.0u) | 8.7% / 0.9% / -2.2% | 37 (fail) |
| Under, wind 20+ mph (schedule wind (observed)) | 9-7 (56.2%, +1.3u) | 10-12 (45.5%, -3.2u) | 3-4 (42.9%, -1.4u) | 7.4% / -13.2% / -18.2% | 50 (fail) |
| Under, wind 10+ mph (kickoff wind, ERA5 archive (observed)) | 108-84 (56.2%, +15.6u) | 151-116 (56.6%, +23.4u) | 77-49 (61.1%, +23.1u) | 7.4% / 8.0% / 16.7% | 19 (fail) |
| Under, wind 12+ mph (kickoff wind, ERA5 archive (observed)) | 63-42 (60.0%, +16.8u) | 100-71 (58.5%, +21.9u) | 42-30 (58.3%, +9.0u) | 14.5% / 11.6% / 11.4% | 11 (fail) |
| Under, wind 15+ mph (kickoff wind, ERA5 archive (observed)) | 27-18 (60.0%, +7.2u) | 48-37 (56.5%, +7.3u) | 15-15 (50.0%, -1.5u) | 14.5% / 7.8% / -4.5% | 41 (fail) |
| Under, wind 20+ mph (kickoff wind, ERA5 archive (observed)) | 8-1 (88.9%, +6.9u) | 10-7 (58.8%, +2.3u) | 1-2 (33.3%, -1.2u) | 69.7% / 12.3% / -36.4% | 47 (fail) |
| Under, gust 15+ mph (kickoff gust, ERA5 archive (observed)) | 227-211 (51.8%, -5.1u) | 256-191 (57.3%, +45.9u) | 142-134 (51.4%, -5.4u) | -1.1% / 9.3% / -1.8% | 23 (fail) |
| Under, gust 20+ mph (kickoff gust, ERA5 archive (observed)) | 124-102 (54.9%, +11.8u) | 159-113 (58.5%, +34.7u) | 91-51 (64.1%, +34.9u) | 4.7% / 11.6% / 22.3% | 9 (fail) |
| Under, gust 25+ mph (kickoff gust, ERA5 archive (observed)) | 74-37 (66.7%, +33.3u) | 89-60 (59.7%, +23.0u) | 40-21 (65.6%, +16.9u) | 27.3% / 14.0% / 25.2% | 6 (fail) |
| Under, gust 30+ mph (kickoff gust, ERA5 archive (observed)) | 30-17 (63.8%, +11.3u) | 39-27 (59.1%, +9.3u) | 14-13 (51.9%, -0.3u) | 21.9% / 12.8% / -1.0% | 28 (fail) |

The claim checks out on the schedule's wind: unders at 10+ mph went 139-102, 141-96, 78-59 (57.7%, 59.5%, 56.9%), a little better than 55%. On the kickoff archive the cleanest split is the gust: 25+ mph went 74-37, 89-60, 40-21 (+33.3, +23.0, +16.9 units).

### Does the model add anything in windy games?

Windy games split by the model's raw under chance (W-L, under win %):

| windy games | model's under chance | 2015-18 | 2019-22 | 2023-25 | 2015-25 |
|---|---|---|---|---|---|
| wind_s 10+ | model under chance under 50% | 44-36 (55.0%) | 37-24 (60.7%) | 31-25 (55.4%) | 112-85 (56.9%) |
| wind_s 10+ | 50% to 55% | 46-24 (65.7%) | 29-28 (50.9%) | 23-16 (59.0%) | 98-68 (59.0%) |
| wind_s 10+ | 55%+ (the flag) | 49-42 (53.8%) | 75-44 (63.0%) | 24-18 (57.1%) | 148-104 (58.7%) |
| wind_s 10+ | all windy games | 139-102 (57.7%) | 141-96 (59.5%) | 78-59 (56.9%) | 358-257 (58.2%) |
| wind_s 10+ | flag in the other games (calm or under a roof) | 86-85 (50.3%) | 100-84 (54.3%) | 47-41 (53.4%) | 233-210 (52.6%) |
| wind_r 12+ | model under chance under 50% | 25-14 (64.1%) | 32-21 (60.4%) | 19-14 (57.6%) | 76-49 (60.8%) |
| wind_r 12+ | 50% to 55% | 16-10 (61.5%) | 22-20 (52.4%) | 10-8 (55.6%) | 48-38 (55.8%) |
| wind_r 12+ | 55%+ (the flag) | 22-18 (55.0%) | 46-30 (60.5%) | 13-8 (61.9%) | 81-56 (59.1%) |
| wind_r 12+ | all windy games | 63-42 (60.0%) | 100-71 (58.5%) | 42-30 (58.3%) | 205-143 (58.9%) |
| wind_r 12+ | flag in the other games (calm or under a roof) | 113-109 (50.9%) | 129-98 (56.8%) | 58-51 (53.2%) | 300-258 (53.8%) |
| gust_r 25+ | model under chance under 50% | 28-11 (71.8%) | 33-15 (68.8%) | 20-11 (64.5%) | 81-37 (68.6%) |
| gust_r 25+ | 50% to 55% | 22-10 (68.8%) | 16-18 (47.1%) | 10-5 (66.7%) | 48-33 (59.3%) |
| gust_r 25+ | 55%+ (the flag) | 24-16 (60.0%) | 40-27 (59.7%) | 10-5 (66.7%) | 74-48 (60.7%) |
| gust_r 25+ | all windy games | 74-37 (66.7%) | 89-60 (59.7%) | 40-21 (65.6%) | 203-118 (63.2%) |
| gust_r 25+ | flag in the other games (calm or under a roof) | 111-111 (50.0%) | 135-101 (57.2%) | 61-54 (53.0%) | 307-266 (53.6%) |

No. Inside windy games the under wins about as often whatever the model says (schedule wind 10+, 2015-25: under 50% 56.9%, 50% to 55% 59.0%, 55%+ 58.7%); with the gust at 25+ the games the model leaned over won the under most often. Outside windy games the totals flag wins 52.6%, so part of the flag's record is windy games it would have won blind.

### With the totals flag

AND: the flag's bets in windy games only. Or: the flag plus windy games at a lower chance. Units against the live flag per window.

| rule | 2015-18 | 2019-22 | 2023-25 | units vs the flag | placebo | all 3 better |
|---|---|---|---|---|---|---|
| Totals flag AND wind 10+ (schedule wind (observed)) | 49-42 (53.8%, +2.8u) | 75-44 (63.0%, +26.6u) | 24-18 (57.1%, +4.2u) | +7.5 / -7.6 / -1.9 | 15 (fail) | no |
| Totals flag, or wind 10+ at a 50%+ chance (schedule wind (observed)) | 181-151 (54.5%, +14.9u) | 204-156 (56.7%, +32.4u) | 94-75 (55.6%, +11.5u) | +19.6 / -1.8 / +5.4 | 12 (fail) | no |
| Totals flag, or wind 10+ at a 52%+ chance (schedule wind (observed)) | 161-139 (53.7%, +8.1u) | 195-149 (56.7%, +31.1u) | 89-67 (57.1%, +15.3u) | +12.8 / -3.1 / +9.2 | 25 (fail) | no |
| Totals flag AND wind 12+ (schedule wind (observed)) | 37-29 (56.1%, +5.1u) | 53-33 (61.6%, +16.7u) | 17-15 (53.1%, +0.5u) | +9.8 / -17.5 / -5.6 | 29 (fail) | no |
| Totals flag, or wind 12+ at a 50%+ chance (schedule wind (observed)) | 164-146 (52.9%, +3.4u) | 196-150 (56.6%, +31.0u) | 83-72 (53.5%, +3.8u) | +8.1 / -3.2 / -2.3 | 39 (fail) | no |
| Totals flag, or wind 12+ at a 52%+ chance (schedule wind (observed)) | 149-135 (52.5%, +0.5u) | 188-145 (56.5%, +28.5u) | 80-65 (55.2%, +8.5u) | +5.2 / -5.7 / +2.4 | 43 (fail) | no |
| Totals flag AND wind 15+ (schedule wind (observed)) | 20-17 (54.1%, +1.3u) | 26-22 (54.2%, +1.8u) | 9-9 (50.0%, -0.9u) | +6.0 / -32.4 / -7.0 | 45 (fail) | no |
| Totals flag, or wind 15+ at a 50%+ chance (schedule wind (observed)) | 148-138 (51.7%, -3.8u) | 185-143 (56.4%, +27.7u) | 73-65 (52.9%, +1.5u) | +0.9 / -6.5 / -4.6 | 48 (fail) | no |
| Totals flag, or wind 15+ at a 52%+ chance (schedule wind (observed)) | 140-132 (51.5%, -5.2u) | 181-139 (56.6%, +28.1u) | 73-59 (55.3%, +8.1u) | -0.5 / -6.1 / +2.0 | 49 (fail) | no |
| Totals flag AND wind 10+ (kickoff wind, ERA5 archive (observed)) | 34-32 (51.5%, -1.2u) | 63-45 (58.3%, +13.5u) | 18-13 (58.1%, +3.7u) | +3.5 / -20.7 / -2.4 | 42 (fail) | no |
| Totals flag, or wind 10+ at a 50%+ chance (kickoff wind, ERA5 archive (observed)) | 167-148 (53.0%, +4.2u) | 209-159 (56.8%, +34.1u) | 94-74 (56.0%, +12.6u) | +8.9 / -0.1 / +6.5 | 10 (fail) | no |
| Totals flag, or wind 10+ at a 52%+ chance (kickoff wind, ERA5 archive (observed)) | 153-137 (52.8%, +2.3u) | 195-151 (56.4%, +28.9u) | 84-68 (55.3%, +9.2u) | +7.0 / -5.3 / +3.1 | 38 (fail) | no |
| Totals flag AND wind 12+ (kickoff wind, ERA5 archive (observed)) | 22-18 (55.0%, +2.2u) | 46-30 (60.5%, +13.0u) | 13-8 (61.9%, +4.2u) | +6.9 / -21.2 / -1.9 | 26 (fail) | no |
| Totals flag, or wind 12+ at a 50%+ chance (kickoff wind, ERA5 archive (observed)) | 151-137 (52.4%, +0.3u) | 197-148 (57.1%, +34.2u) | 81-67 (54.7%, +7.3u) | +5.0 / +0.0 / +1.2 | 32 (fail) | no |
| Totals flag, or wind 12+ at a 52%+ chance (kickoff wind, ERA5 archive (observed)) | 141-132 (51.6%, -4.2u) | 189-142 (57.1%, +32.8u) | 77-61 (55.8%, +9.9u) | +0.5 / -1.4 / +3.8 | 38 (fail) | no |
| Totals flag AND wind 15+ (kickoff wind, ERA5 archive (observed)) | 8-8 (50.0%, -0.8u) | 19-17 (52.8%, +0.3u) | 2-4 (33.3%, -2.4u) | +3.9 / -33.9 / -8.5 | 47 (fail) | no |
| Totals flag, or wind 15+ at a 50%+ chance (kickoff wind, ERA5 archive (observed)) | 146-130 (52.9%, +3.0u) | 185-138 (57.3%, +33.2u) | 75-65 (53.6%, +3.5u) | +7.7 / -1.0 / -2.6 | 46 (fail) | no |
| Totals flag, or wind 15+ at a 52%+ chance (kickoff wind, ERA5 archive (observed)) | 140-129 (52.0%, -1.9u) | 181-135 (57.3%, +32.5u) | 73-59 (55.3%, +8.1u) | +2.8 / -1.7 / +2.0 | 33 (fail) | no |
| Totals flag AND gust 20+ (kickoff gust, ERA5 archive (observed)) | 41-38 (51.9%, -0.8u) | 63-42 (60.0%, +16.8u) | 24-14 (63.2%, +8.6u) | +3.9 / -17.4 / +2.5 | 38 (fail) | no |
| Totals flag, or gust 20+ at a 50%+ chance (kickoff gust, ERA5 archive (observed)) | 173-150 (53.6%, +8.0u) | 209-160 (56.6%, +33.0u) | 99-74 (57.2%, +17.6u) | +12.7 / -1.2 / +11.5 | 15 (fail) | no |
| Totals flag, or gust 20+ at a 52%+ chance (kickoff gust, ERA5 archive (observed)) | 155-138 (52.9%, +3.2u) | 193-151 (56.1%, +26.9u) | 91-67 (57.6%, +17.3u) | +7.9 / -7.3 / +11.2 | 39 (fail) | no |
| Totals flag AND gust 25+ (kickoff gust, ERA5 archive (observed)) | 24-16 (60.0%, +6.4u) | 40-27 (59.7%, +10.3u) | 10-5 (66.7%, +4.5u) | +11.1 / -23.9 / -1.6 | 19 (fail) | no |
| Totals flag, or gust 25+ at a 50%+ chance (kickoff gust, ERA5 archive (observed)) | 157-137 (53.4%, +6.3u) | 191-146 (56.7%, +30.4u) | 81-64 (55.9%, +10.6u) | +11.0 / -3.8 / +4.5 | 27 (fail) | no |
| Totals flag, or gust 25+ at a 52%+ chance (kickoff gust, ERA5 archive (observed)) | 146-133 (52.3%, -0.3u) | 183-139 (56.8%, +30.1u) | 78-59 (56.9%, +13.1u) | +4.4 / -4.1 / +7.0 | 38 (fail) | no |

Best combination by its worst window: Totals flag, or wind 12+ at a 50%+ chance (kickoff wind, ERA5 archive (observed)) (+5.0 / +0.0 / +1.2 units against the flag).

## 2. Gusts in the total equation

Total miss per window (change against the live total equation in brackets); totals-flag W-L 2015-18 / 2019-22 / 2023-25. The spread and the win chance do not move (the total has its own equation). The gust is the ERA5 kickoff reading (observed), as the model's wind is the schedule's observed reading; outdoor games the archive lacks take the 2013-14 outdoor median, games under a roof 0.

Engine check: the total walk-forward here reproduces the live total equation to 0.0e+00 points.

| variant | 2015-18 | 2019-22 | 2023-25 | totals flag | placebo |
|---|---|---|---|---|---|
| live total equation (base) | 10.7437 | 10.5406 | 10.1767 | 135-127 / 175-128 / 71-59 |  |
| gust (outdoor kickoff gust, 0 under a roof) | 10.7380 (-0.0057) | 10.5357 (-0.0050) | 10.1708 (-0.0059) | 134-127 / 177-134 / 72-59 | 18 (fail) |
| gust over the sustained wind | 10.7491 (+0.0054) | 10.5438 (+0.0032) | 10.1773 (+0.0006) | 133-128 / 177-131 / 71-61 | 47 (fail) |
| gust in place of the wind | 10.7568 (+0.0132) | 10.5210 (-0.0196) | 10.1767 (+0.0000) | 146-132 / 177-136 / 78-72 | 0 (not a test of the gust: see below) |

The placebo shuffles the gust among outdoor games only, so a shuffled column still says outdoors (some gust) or under a roof (0). That the shuffled column gains about as much as the real one says the small gain is the roof split, which the equation's dome input only partly holds, not the gust itself. The gust-for-wind placebo is not a test of the gust (shuffling it removes all wind), and that form fails rule 1 anyway.

What survives a forecast: the same fits, the 2024 and 2025 games priced with the day-before forecast gust instead of the archive's (total miss):

| variant | 2024 base | 2024 gust observed | 2024 gust forecast | 2025 base | 2025 gust observed | 2025 gust forecast |
|---|---|---|---|---|---|---|
| gust (outdoor kickoff gust, 0 under a roof) | 9.6851 | 9.7001 | 9.6558 | 10.4124 | 10.4001 | 10.3823 |
| gust over the sustained wind | 9.6851 | 9.6848 | 9.6790 | 10.4124 | 10.4141 | 10.4163 |
| gust in place of the wind | 9.6851 | 9.7036 | 9.6294 | 10.4124 | 10.4142 | 10.3804 |

## 3. Forecast history back to 2018

**What we have.** `data/weather/forecast_archive.csv` (Open-Meteo Previous Runs API, `nflmodel/forecast_archive.py`): the forecast one and two days before each played outdoor kickoff hour. Temperature from 2022 (GFS 2 m temperature is archived from March 2021); wind, gust and precipitation only from 2024-01-20 (the Previous Runs API keeps most models from January 2024). So 2024 and 2025 are the only seasons with a pre-kickoff wind or gust; the 2026 live log (`data/weather/forecast_log.csv`) adds 2026 from here on. The ERA5 archive (`archive_kickoff.csv`, 2013-2025) is the weather that happened.

**What the free sources cover (docs read 1 Oct 2026; this sandbox cannot reach open-meteo.com or mesonet.agron.iastate.edu, so nothing was fetched):**

| source | what it is | wind | gust | from | pre-kickoff? |
|---|---|---|---|---|---|
| Open-Meteo Previous Runs API (`previous-runs-api.open-meteo.com/v1/forecast`, `<var>_previous_day1`) | each model's value at a fixed 1-7 day lead | yes | yes (most models) | Jan 2024 (most models); GFS temperature Mar 2021; **JMA GSM and MSM 2018** | yes |
| same, `models=jma_gsm` | Japan's global model, 0.5 deg (~55 km), 6-hourly interpolated | yes | **no** (JMA publishes no gusts) | 2018 | yes |
| Open-Meteo Historical Forecast API (`historical-forecast-api.open-meteo.com/v1/forecast`) | the first hours of each run stitched into one series | yes | yes | ~2021-22 (GFS 2021-03-23; ECMWF IFS HRES 2017; HRRR 2018-01-01) | **no**: the first hours of each run track what happened, so it is close to an analysis, not a forecast |
| Open-Meteo Single Runs API (`run=` an init time) | a whole run as issued | yes | yes | ECMWF IFS HRES Mar 2024; others Apr 2026 | yes, but too late |
| Iowa Environmental Mesonet MOS archive (`mesonet.agron.iastate.edu/api/1/mos.json?station=KBUF&model=GFS&runtime=2018-12-01%2012:00Z`) | NWS model output statistics at airports, runs 00/06/12/18Z, 3-hourly to 72 h | yes (knots) | GFS MOS no; **NBM text (NBS) yes, from 7 Nov 2018**; LAMP from Jul 2020 | GFS MOS Dec 2003; NAM MOS Dec 2008 | yes |
| NOAA NDFD (NCEI THREDDS, NetcdfSubset by point; AWS `noaa-ndfd-pds` from Apr 2020) | the official NWS gridded forecast | yes | yes | about ten years online (AIRS orders back to 2004) | yes, but GRIB2 grids and slow |

**What would be fetched (from GitHub's network, as `nflmodel/forecast_archive.py` already does):**

1. Open-Meteo Previous Runs, `models=jma_gsm`, `hourly=wind_speed_10m_previous_day1,wind_speed_10m_previous_day2,temperature_2m_previous_day1`, `wind_speed_unit=mph`, one request per stadium-season over the season's date span (the site's local time zone), the kickoff hour picked out per game. Wind only.
2. Iowa Mesonet MOS: per game, the GFS MOS run issued at 12Z the day before kickoff (`model=GFS`) at the stadium's airport, the 3-hourly wind speed (knots, x 1.151 for mph) at the forecast hours around kickoff, interpolated; and the NBM text run (`model=NBS`) for the gust (GST) from 7 Nov 2018. One request per game per model. A stadium-to-airport table is drafted in `MOS_STATION` (check each before use).
3. Ask Open-Meteo to reconstruct wind and gust Previous Runs (GFS or ECMWF) for 2018-2023 at the 31 sites (their docs offer this on request).

Request counts (outdoor and open-roof games, regular season and playoffs):

| season | games | sites | have_wind_forecast | site_seasons | nbm_text_from_2018-11-07 |
|---|---|---|---|---|---|
| 2018 | 202 | 25 | 0 | 25 | 100 |
| 2019 | 206 | 26 | 0 | 26 | 206 |
| 2020 | 176 | 21 | 0 | 21 | 176 |
| 2021 | 202 | 27 | 0 | 27 | 202 |
| 2022 | 198 | 26 | 0 | 26 | 198 |
| 2023 | 199 | 26 | 4 | 26 | 199 |

About 1183 games and 151 site-seasons: ~151 requests for option 1, ~1183 GFS MOS requests plus ~1081 NBM text requests for option 2. None of these is a source the weekly run pulls (it reads Open-Meteo's best-match forecast), so a rule trained on them would also need the live run to read the same model (rule 4).

**Does forecast wind behave like observed wind?** On the 2024-25 outdoor games that have the day-before forecast (336 games): forecast and ERA5 wind correlate 0.78 (mean absolute gap 2.2 mph, forecast +0.8 mph), gusts 0.77 (gap 4.6 mph, -1.6); schedule wind against forecast 0.76. The totals flag on these games: 32-35 (-6.5u).

Blind unders on the same games, by reading (the last column: the share of the forecast rule's and this reading's games they have in common):

| rule | reading | 2024 | 2025 | 2024-25 | same games as the forecast picks |
|---|---|---|---|---|---|
| Under, wind 10+ mph | wind forecast the day before | 23-28 (-7.8u) | 29-19 (+8.1u) | 52-47 (52.5%, +0.3u) |  |
| Under, wind 10+ mph | schedule wind (observed) | 23-25 (-4.5u) | 25-22 (+0.8u) | 48-47 (50.5%, -3.7u) | 51.2% |
| Under, wind 10+ mph | kickoff wind, ERA5 archive (observed) | 21-22 (-3.2u) | 20-13 (+5.7u) | 41-35 (53.9%, +2.5u) | 54.9% |
| Under, wind 12+ mph | wind forecast the day before | 13-14 (-2.4u) | 19-12 (+5.8u) | 32-26 (55.2%, +3.4u) |  |
| Under, wind 12+ mph | schedule wind (observed) | 15-17 (-3.7u) | 16-17 (-2.7u) | 31-34 (47.7%, -6.4u) | 53.8% |
| Under, wind 12+ mph | kickoff wind, ERA5 archive (observed) | 8-15 (-8.5u) | 13-9 (+3.1u) | 21-24 (46.7%, -5.4u) | 47.1% |
| Under, wind 15+ mph | wind forecast the day before | 3-3 (-0.3u) | 9-7 (+1.3u) | 12-10 (54.5%, +1.0u) |  |
| Under, wind 15+ mph | schedule wind (observed) | 5-8 (-3.8u) | 10-9 (+0.1u) | 15-17 (46.9%, -3.7u) | 45.9% |
| Under, wind 15+ mph | kickoff wind, ERA5 archive (observed) | 4-5 (-1.5u) | 4-8 (-4.8u) | 8-13 (38.1%, -6.3u) | 59.3% |
| Under, wind 20+ mph | wind forecast the day before | 0-0 (+0.0u) | 1-3 (-2.3u) | 1-3 (25.0%, -2.3u) |  |
| Under, wind 20+ mph | schedule wind (observed) | 0-1 (-1.1u) | 3-2 (+0.8u) | 3-3 (50.0%, -0.3u) | 25.0% |
| Under, wind 20+ mph | kickoff wind, ERA5 archive (observed) | 0-0 (+0.0u) | 1-2 (-1.2u) | 1-2 (33.3%, -1.2u) | 75.0% |
| Under, gust 15+ mph | gust forecast the day before | 35-42 (-11.2u) | 40-30 (+7.0u) | 75-72 (51.0%, -4.2u) |  |
| Under, gust 15+ mph | kickoff gust, ERA5 archive (observed) | 40-53 (-18.3u) | 46-41 (+0.9u) | 86-94 (47.8%, -17.4u) | 59.4% |
| Under, gust 20+ mph | gust forecast the day before | 21-18 (+1.2u) | 26-17 (+7.3u) | 47-35 (57.3%, +8.5u) |  |
| Under, gust 20+ mph | kickoff gust, ERA5 archive (observed) | 23-24 (-3.4u) | 32-17 (+13.3u) | 55-41 (57.3%, +9.9u) | 49.2% |
| Under, gust 25+ mph | gust forecast the day before | 9-8 (+0.2u) | 16-10 (+5.0u) | 25-18 (58.1%, +5.2u) |  |
| Under, gust 25+ mph | kickoff gust, ERA5 archive (observed) | 4-10 (-7.0u) | 16-8 (+7.2u) | 20-18 (52.6%, +0.2u) | 52.8% |
| Under, gust 30+ mph | gust forecast the day before | 5-3 (+1.7u) | 7-6 (+0.4u) | 12-9 (57.1%, +2.1u) |  |
| Under, gust 30+ mph | kickoff gust, ERA5 archive (observed) | 3-4 (-1.4u) | 7-7 (-0.7u) | 10-11 (47.6%, -2.1u) | 35.5% |

With the flag, 2024-25:

| rule | reading | 2024-25 |
|---|---|---|
| Flag AND wind 10+ | wind forecast the day before | 11-13 (-3.3u) |
| Flag, or windy at 52%+: wind 10+ | wind forecast the day before | 46-41 (+0.9u) |
| Flag AND wind 10+ | kickoff wind, ERA5 archive (observed) | 9-11 (-3.1u) |
| Flag, or windy at 52%+: wind 10+ | kickoff wind, ERA5 archive (observed) | 40-42 (-6.2u) |
| Flag AND wind 12+ | wind forecast the day before | 7-8 (-1.8u) |
| Flag, or windy at 52%+: wind 12+ | wind forecast the day before | 40-38 (-1.8u) |
| Flag AND wind 12+ | kickoff wind, ERA5 archive (observed) | 6-7 (-1.7u) |
| Flag, or windy at 52%+: wind 12+ | kickoff wind, ERA5 archive (observed) | 37-36 (-2.6u) |
| Flag AND wind 15+ | wind forecast the day before | 2-2 (-0.2u) |
| Flag, or windy at 52%+: wind 15+ | wind forecast the day before | 34-35 (-4.5u) |
| Flag AND wind 15+ | kickoff wind, ERA5 archive (observed) | 1-3 (-2.3u) |
| Flag, or windy at 52%+: wind 15+ | kickoff wind, ERA5 archive (observed) | 33-35 (-5.5u) |
| Flag AND wind 20+ | wind forecast the day before | 0-1 (-1.1u) |
| Flag, or windy at 52%+: wind 20+ | wind forecast the day before | 32-35 (-6.5u) |
| Flag AND wind 20+ | kickoff wind, ERA5 archive (observed) | 0-1 (-1.1u) |
| Flag, or windy at 52%+: wind 20+ | kickoff wind, ERA5 archive (observed) | 32-35 (-6.5u) |
| Flag AND gust 15+ | gust forecast the day before | 17-17 (-1.7u) |
| Flag, or windy at 52%+: gust 15+ | gust forecast the day before | 52-46 (+1.4u) |
| Flag AND gust 15+ | kickoff gust, ERA5 archive (observed) | 21-25 (-6.5u) |
| Flag, or windy at 52%+: gust 15+ | kickoff gust, ERA5 archive (observed) | 53-53 (-5.3u) |
| Flag AND gust 20+ | gust forecast the day before | 11-9 (+1.1u) |
| Flag, or windy at 52%+: gust 20+ | gust forecast the day before | 42-42 (-4.2u) |
| Flag AND gust 20+ | kickoff gust, ERA5 archive (observed) | 15-13 (+0.7u) |
| Flag, or windy at 52%+: gust 20+ | kickoff gust, ERA5 archive (observed) | 45-41 (-0.1u) |
| Flag AND gust 25+ | gust forecast the day before | 8-5 (+2.5u) |
| Flag, or windy at 52%+: gust 25+ | gust forecast the day before | 36-36 (-3.6u) |
| Flag AND gust 25+ | kickoff gust, ERA5 archive (observed) | 4-4 (-0.4u) |
| Flag, or windy at 52%+: gust 25+ | kickoff gust, ERA5 archive (observed) | 37-35 (-1.5u) |
| Flag AND gust 30+ | gust forecast the day before | 4-2 (+1.8u) |
| Flag, or windy at 52%+: gust 30+ | gust forecast the day before | 33-35 (-5.5u) |
| Flag AND gust 30+ | kickoff gust, ERA5 archive (observed) | 2-3 (-1.3u) |
| Flag, or windy at 52%+: gust 30+ | kickoff gust, ERA5 archive (observed) | 36-35 (-2.5u) |

## 4. Six-point two-team teasers

Legs: dogs at +1.5 to +2.5 teased to +7.5 to +8.5, favorites at -7.5 to -8.5 teased to -1.5 to -2.5 (both through 3 and 7), at the closing line. The model filter keeps a leg when the model's spread leans to that side (by more than 0, or by 1, 2, 3+ points). Teasers pair each week's legs in kickoff order; units per teaser at -110 / -120 / -130. Break-even per leg (legs independent): -110 72.4%, -120 73.9%, -130 75.2%. Six-point two-teamers run -120 at most books now, -125 at Caesars, -130 to -140 at several. Placebo: the model's edges shuffled within season (50 draws); the gain is the leg win rate over the same legs blind.

| legs | filter | 2015-18 | 2019-22 | 2023-25 | placebo (leg rate over blind) |
|---|---|---|---|---|---|
| both leg kinds | blind | legs 187-56-2 (77.0%); teasers 60-44-2: +11.6 / +7.2 / +2.8u | legs 166-48 (77.6%); teasers 53-38: +11.2 / +7.4 / +3.6u | legs 166-61 (73.1%); teasers 56-48: +3.2 / -1.6 / -6.4u |  |
| both leg kinds | model agrees | legs 111-30-2 (78.7%); teasers 33-22-1: +8.8 / +6.6 / +4.4u | legs 90-34 (72.6%); teasers 28-19: +7.1 / +5.2 / +3.3u | legs 101-33 (75.4%); teasers 37-18: +17.2 / +15.4 / +13.6u | 49 (fail) |
| both leg kinds | model agrees by 1+ | legs 80-20-1 (80.0%); teasers 21-14-1: +5.6 / +4.2 / +2.8u | legs 63-23 (73.3%); teasers 16-14: +0.6 / -0.8 / -2.2u | legs 78-25 (75.7%); teasers 30-13: +15.7 / +14.4 / +13.1u | 45 (fail) |
| both leg kinds | model agrees by 2+ | legs 45-12 (78.9%); teasers 9-6: +2.4 / +1.8 / +1.2u | legs 45-13 (77.6%); teasers 8-7: +0.3 / -0.4 / -1.1u | legs 56-17 (76.7%); teasers 18-8: +9.2 / +8.4 / +7.6u | 39 (fail) |
| both leg kinds | model agrees by 3+ | legs 29-8 (78.4%); teasers 4-4: -0.4 / -0.8 / -1.2u | legs 30-10 (75.0%); teasers 3-5: -2.5 / -3.0 / -3.5u | legs 32-5 (86.5%); teasers 6-1: +4.9 / +4.8 / +4.7u | 38 (fail) |
| dogs only | blind | legs 117-35-2 (77.0%); teasers 36-22-1: +11.8 / +9.6 / +7.4u | legs 101-29 (77.7%); teasers 29-17: +10.3 / +8.6 / +6.9u | legs 129-38 (77.2%); teasers 46-26: +17.4 / +14.8 / +12.2u |  |
| dogs only | model agrees | legs 87-22-2 (79.8%); teasers 28-11-2: +15.9 / +14.8 / +13.7u | legs 71-22 (76.3%); teasers 20-14: +4.6 / +3.2 / +1.8u | legs 90-24 (78.9%); teasers 36-12: +22.8 / +21.6 / +20.4u | 36 (fail) |
| dogs only | model agrees by 1+ | legs 62-16-1 (79.5%); teasers 14-10-1: +3.0 / +2.0 / +1.0u | legs 53-15 (77.9%); teasers 12-8: +3.2 / +2.4 / +1.6u | legs 68-17 (80.0%); teasers 27-8: +18.2 / +17.4 / +16.6u | 31 (fail) |
| dogs only | model agrees by 2+ | legs 35-9 (79.5%); teasers 4-5: -1.5 / -2.0 / -2.5u | legs 39-11 (78.0%); teasers 6-6: -0.6 / -1.2 / -1.8u | legs 50-10 (83.3%); teasers 17-4: +12.6 / +12.2 / +11.8u | 30 (fail) |
| dogs only | model agrees by 3+ | legs 21-5 (80.8%); teasers 2-2: -0.2 / -0.4 / -0.6u | legs 28-8 (77.8%); teasers 3-4: -1.4 / -1.8 / -2.2u | legs 30-3 (90.9%); teasers 6-0: +6.0 / +6.0 / +6.0u | 34 (fail) |
| favorites only | blind | legs 70-21 (76.9%); teasers 17-9: +7.1 / +6.2 / +5.3u | legs 65-19 (77.4%); teasers 15-8: +6.2 / +5.4 / +4.6u | legs 37-23 (61.7%); teasers 9-10: -2.0 / -3.0 / -4.0u |  |
| favorites only | model agrees | legs 24-8 (75.0%); teasers 4-1: +2.9 / +2.8 / +2.7u | legs 19-12 (61.3%); teasers 4-2: +1.8 / +1.6 / +1.4u | legs 11-9 (55.0%); teasers 2-1: +0.9 / +0.8 / +0.7u | 50 (fail) |
| favorites only | model agrees by 1+ | legs 18-4 (81.8%); teasers 3-1: +1.9 / +1.8 / +1.7u | legs 10-8 (55.6%); teasers 1-2: -1.2 / -1.4 / -1.6u | legs 10-8 (55.6%); teasers 2-1: +0.9 / +0.8 / +0.7u | 50 (fail) |
| favorites only | model agrees by 2+ | legs 10-3 (76.9%); teasers 2-1: +0.9 / +0.8 / +0.7u | legs 6-2 (75.0%); teasers 0-0: +0.0 / +0.0 / +0.0u | legs 6-7 (46.2%); teasers 0-1: -1.1 / -1.2 / -1.3u | 50 (fail) |
| favorites only | model agrees by 3+ | legs 8-3 (72.7%); teasers 1-1: -0.1 / -0.2 / -0.3u | legs 2-2 (50.0%); teasers 0-0: +0.0 / +0.0 / +0.0u | legs 2-2 (50.0%); teasers 0-0: +0.0 / +0.0 / +0.0u | 50 (fail) |

Blind, both kinds: legs 77.0%, 77.6%, 73.1%.

The same six points on other lines (legs W-L, win %), to show the key numbers doing the work:

| line | 2015-18 | 2019-22 | 2023-25 |
|---|---|---|---|
| dog +0.5 to +1 | 50-27 (64.9%) | 68-21 (76.4%) | 21-4 (84.0%) |
| dog +1.5 to +2.5 (basic strategy) | 117-35 (77.0%) | 101-29 (77.7%) | 129-38 (77.2%) |
| dog +3 to +3.5 | 193-70 (73.4%) | 176-59 (74.9%) | 134-61 (68.7%) |
| dog +4 to +6.5 | 168-68 (71.2%) | 187-55 (77.3%) | 125-61 (67.2%) |
| dog +7 to +10 | 128-68 (65.3%) | 132-64 (67.3%) | 83-50 (62.4%) |
| favorite -1 to -2.5 | 151-85 (64.0%) | 143-80 (64.1%) | 137-56 (71.0%) |
| favorite -3 to -6.5 | 343-148 (69.9%) | 302-164 (64.8%) | 280-95 (74.7%) |
| favorite -7 | 47-12 (79.7%) | 43-15 (74.1%) | 27-13 (67.5%) |
| favorite -7.5 to -8.5 (basic strategy) | 70-21 (76.9%) | 65-19 (77.4%) | 37-23 (61.7%) |
| favorite -9 to -10.5 | 34-28 (54.8%) | 57-28 (67.1%) | 30-11 (73.2%) |

## 5. Points-per-drive rating

Offensive points per drive (7 a touchdown drive, 3 a field-goal drive, kneel-only drives out, from `team_box.parquet`, which the weekly run builds from the play-by-play it already pulls), opponent-adjusted and decayed like the live ratings. Full walk-forward, fresh trees, every blend model carries the inputs. Cells: team points miss (change) / margin miss / total miss. The placebo stops once 6 draws match the real gain (the outcome is then settled).

| variant | 2015-18 | 2019-22 | 2023-25 | spread flag | totals flag | cal. log loss | placebo |
|---|---|---|---|---|---|---|---|
| live model (base) | 7.4095 / 9.949 / 10.744 | 7.3478 / 10.020 / 10.541 | 7.2623 / 9.904 / 10.177 | 68-55 / 80-51 / 40-21 | 135-127 / 175-128 / 71-59 | 0.6194 / 0.6243 / 0.6202 |  |
| PPD added to the points equation | 7.4119 (+0.0024) / 9.962 / 10.744 | 7.3431 (-0.0047) / 10.017 / 10.541 | 7.2642 (+0.0019) / 9.905 / 10.177 | 62-59 / 76-51 / 38-22 | 135-127 / 175-128 / 71-59 | 0.6204 / 0.6236 / 0.6204 | 6 of 6 draws (stopped) (fail) |
| PPD added to the points and total equations | 7.4152 (+0.0057) / 9.962 / 10.754 | 7.3485 (+0.0006) / 10.017 / 10.556 | 7.2650 (+0.0028) / 9.905 / 10.183 | 62-59 / 76-51 / 38-22 | 131-123 / 174-134 / 71-68 | 0.6204 / 0.6236 / 0.6204 | 7 of 9 draws (stopped) (fail) |
| PPD in place of EPA per play (points and total) | 7.4138 (+0.0043) / 9.959 / 10.781 | 7.3414 (-0.0065) / 10.022 / 10.546 | 7.2641 (+0.0018) / 9.915 / 10.190 | 68-57 / 82-56 / 41-23 | 125-128 / 178-137 / 69-66 | 0.6203 / 0.6240 / 0.6201 | 6 of 6 draws (stopped) (fail) |
| PPD in place of the points rating (points and total) | 7.4247 (+0.0152) / 9.972 / 10.739 | 7.3569 (+0.0091) / 10.045 / 10.528 | 7.2743 (+0.0120) / 9.944 / 10.211 | 85-67 / 82-60 / 36-27 | 152-129 / 182-138 / 78-73 | 0.6213 / 0.6257 / 0.6218 | 5 of 50 draws (pass) |

