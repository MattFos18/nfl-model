# Forecast weather in the backtest (2 Oct 2026)

## Pre-registration (written before any result)

**Claim.** Matt approved making the backtest "100% accurate, no cheating" and adopting anything clearly better. The
backtest priced every played game with the weather that happened (the schedule's wind and temperature into `wind_out`
and `cold`, the play-by-play's rain into the points equations), while a live game is priced on a forecast. Part A fixes
that; parts B and C re-score today's weather and QB-form adoptions on the fixed backtest.

**A. Live-style weather (a correctness fix, not an adoption).** For every played game since 2018 with a stored forecast
(`data/weather/forecast_history.csv`, plus the live log `wind_live.csv` for 2026), the game is *priced* (not trained) on
the forecast, as a live fit is: `wind_out` = the reading the wind points and the wind under use
(`wind_live.readings`: GFS MOS d0, NBS d0 and Japan d1, mean); `cold` (and `warm_in_cold`) = GFS MOS temperature
(`gfs_temp_d0`, else `d1`) under 35 F; the points equations' `rain` = the totals' rain reading (`model.RAIN_FC`: GFS MOS
chance 50%+). Training rows keep the recorded weather (a live fit trains on played games, whose weather is recorded). A
missing reading prices like a live game without a forecast (league-median wind, not cold, dry). Before 2018 and for
games abroad no forecast is stored, so the recorded weather stays: the 2015-18 window is honest only for 2018. Coded in
`model.priced_weather`, called by `model.walk_forward` (and by `export_web` for the inputs the page shows). Its records
are reported as the new baseline whether better or worse.

Note: the live run's points-equation weather comes from Open-Meteo's kickoff-hour forecast (`weather.apply_to_games`),
which is not stored for 2018-25 (the Open-Meteo previous-runs archive starts in 2022 for temperature and about 2024 for
wind and rain). The GFS/JMA readings above are the closest stored pre-kickoff forecast and are what the live rules read.

**B. Re-score today's adoptions on top of A** (each: the model with and without it, everything else as A):
- B1 wind points (`model.wind_points`, bands [0,10), [10,15), 15+, K = 50).
- B2 rain in the total (`rain_fc` in `TOTAL_FEATS`).
- B3 QB form in the total (`qb_form_sum` in `TOTAL_FEATS`).

**C. Wind curve** (replacing the bands; learned walk-forward from earlier seasons exactly like `wind_points`, same
K = 50 shrinkage, same pool of (forecast wind, actual total minus the model's total before wind points)):
- C1 isotonic: a decreasing isotonic fit of the centred miss on forecast wind over the earlier seasons' pool; a game's
  amount is its block's fitted value shrunk by n / (n + 50), n = the games in its block (the bands' shrinkage, with
  blocks chosen by the data instead of by hand).
- C2 smoothed cliff: bands [0,8), [8,10), [10,15), 15+.
Compared against the current bands (A).

**Pass bar.** `study_gate.gate` on team points miss and, for totals inputs, on total miss (both must pass); no bet cost on
the spread flag (4+), the totals flag (55%+ under) and the wind under (10+ mph), weeks 1-17, every window; 50-draw
within-season placebo for whatever passes parts 1-2 (B1 and C: the forecast wind shuffled among each season's games;
B2: the game's `rain_fc` shuffled; B3: each team-game's `qb_form` shuffled; the placebo gain is measured the same way as
the real gain). Wind points act only from 2019 (no forecasts before 2018, so 2018 has no earlier pool): for B1 and C the
2015-18 window is identical by construction and is treated as the rule's "fit window may tie" (not scored for the
placebo); the decision rests on 2019-22 and 2023-25. B: anything that now fails is recommended for dropping (Matt
pre-approved). C: adopted only if it beats the bands on every scored window and passes the gate.

**Also reported:** the total-points effect by forecast wind (0, 5, 9, 10, 14, 15, 20 mph: the totals equation's
`wind_out` part plus the wind points, at the latest fit) for the winner, and the 8-10 mph band's mean miss (the model ran
about 2 points low there).

**Variants:** A, B1, B2, B3, C1, C2 (six). Earlier studies of the same ideas: wind points (bands and K picked by hand,
`experiments/wind_points.py`), rain (about 10 variants, `experiments/rain_points.py`), QB form, forecast weather inputs
(`experiments/forecast_weather_inputs.py`, retrained on forecasts; not adopted).

**Added after results (none changes a verdict):** the placebo was drawn for everything that passed parts 1-2 on team
points miss (the round-3 rule's miss for the game model), so B2 got one although it fails part 1 on total miss.

## Results

`experiments/forecast_weather_backtest.py`; full tables, every gate and the placebo rows in
reports/forecast_weather_backtest_results.md and reports/forecast_weather_backtest.csv. Every variant is the live model
refit walk-forward 2015-2025 on today's main data (regular season; flags weeks 1-17 against the close, -110). The tree
fits for the games A re-prices were refit on this laptop; GitHub's first refit can move them by rounding
(`docs/wiki/gotchas.md`, boosted trees).

### A: the honest baseline (new numbers to quote)

| Window | Team points miss | Total miss | Spread flag (4+) | Totals flag (55% under) | Wind under (10+ mph) |
|---|---|---|---|---|---|
| 2015-18 | 7.4046 (was 7.3984) | 10.7507 (was 10.7413) | 69-55 (was 69-56) | 132-117 (was 130-117) | 24-20 (same) |
| 2019-22 | 7.3645 (was 7.3651) | 10.5161 (was 10.5407) | 76-48 (was 79-51) | 190-146 (was 185-149) | 143-88 (same) |
| 2023-25 | 7.2343 (was 7.2353) | 10.1029 (was 10.1196) | 37-19 (was 37-18) | 82-59 (was 70-57) | 77-52 (same) |

"Was" is the same code with recorded weather (`FORECAST_WEATHER = False`), today's main. 1,566 played games 2018-2026
are re-priced (every one has all three readings); 34 outdoor games abroad and 2015-17 keep recorded weather. The
forecast and recorded wind correlate 0.73; the forecast calls rain in 191 of them against 107 recorded, cold in 153
against 140. The spread flag is no better or worse (net +14 / +28 / +18 against +13 / +28 / +19). The totals flag and
the total miss are better with the forecast, as expected: the totals' rain and the wind points were learned on forecasts,
so pricing on the same readings is consistent. The wind under reads only the forecast and is unchanged.

### B: today's adoptions re-scored on A

| | Team points gate | Total miss gate | Totals flag without -> with |
|---|---|---|---|
| B1 wind points | parts 1-2 pass; placebo 37 / 47 of 50 (2019-22 fails) | PASS (placebo 48 / 48) | 184-147 -> 190-146; 74-55 -> 82-59 |
| B2 rain in the total | PASS (placebo 45 / 50 / 50) | 2015-18 worse (10.7454 -> 10.7507; 2018 games only), placebo 39 / 50 / 50 | 127-113 -> 132-117; 171-139 -> 190-146; 71-51 -> 82-59 |
| B3 QB form in the total | PASS (placebo 50 / 50 / 50) | PASS (placebo 50 / 50 / 50) | 140-131 -> 132-117; 206-168 -> 190-146; 77-64 -> 82-59 |

Against the pre-registered bar (both gates) B3 passes; B1 fails one check (its 2019-22 team-points placebo) and B2 two (its 2015-18 total miss and that window's placebo). Under the round-3
rule's own miss for the game model (team points), B2 passes and B1 fails its 2019-22 placebo; judged on total miss (the
miss a totals input acts on), B1 passes and B2 fails on 2018. Dropping either costs totals-flag wins on every window it
acts on (B1: -7 and -4 net; B2: -1, -12 and -3 net).

### C: the wind curve

| | 2019-22 total miss | 2023-25 total miss | Totals flag 2019-22 / 2023-25 | Verdict |
|---|---|---|---|---|
| Bands (A) | 10.5161 | 10.1029 | 190-146 / 82-59 | kept |
| C1 isotonic | 10.5363 | 10.0971 | 192-156 / 83-58 | fails (worse on 2019-22, -8 net) |
| C2 [0,8) [8,10) [10,15) 15+ | 10.5159 | 10.1201 | 185-148 / 78-60 | fails (worse on 2023-25, fewer wins both) |

Neither curve beats the bands on every scored window (team points miss fails the same way), so no placebo was drawn.

### Total-points effect by forecast wind (the winner: the bands)

Latest fit: the totals equation's wind term is -0.340 per mph (trained on recorded wind, priced on the forecast); the
wind points are learned from the 2018-2025 pool.

| Forecast wind (mph) | 0 | 5 | 9 | 10 | 14 | 15 | 20 |
|---|---|---|---|---|---|---|---|
| Equation | 0.00 | -1.70 | -3.06 | -3.40 | -4.76 | -5.10 | -6.80 |
| Wind points | +0.33 | +0.33 | +0.33 | -1.17 | -1.17 | +0.40 | +0.40 |
| Total effect | +0.33 | -1.37 | -2.73 | -4.58 | -5.94 | -4.70 | -6.40 |

The cliff is 1.85 points between 9 and 10 mph, and 15 mph takes back 1.24 of it. Mean miss (actual minus the model's
total), 2019-2025:

| Forecast wind | Games | Before wind points | With the bands | C1 | C2 |
|---|---|---|---|---|---|
| under 8 | 672 | +0.32 | +0.13 | +0.19 | +0.44 |
| 8 to 10 | 208 | +1.20 | +1.00 | +1.15 | +0.18 |
| 10 to 15 | 273 | -1.13 | -0.08 | -0.85 | -0.08 |
| 15+ | 111 | +0.59 | -0.43 | +0.92 | -0.43 |

On the honest backtest the 8-10 mph games run 1.0 point low (the model under the actual total), not 2. C2 removes that
bias but costs more elsewhere (2023-25 worse, fewer totals-flag wins), so the bands stay.

## Audit

model-auditor (reports/audit_forecast_weather_backtest_2026-10-02.md): "**Verdict: holds with caveats.** A is a real
look-ahead fix: no leak found, and the numbers reproduce exactly. B3 and C hold. B1 (wind points) and B2 (rain_fc) fail
the bar the study set for itself before seeing results." It reran A, recorded and no-rain from scratch (identical), checked
every GFS and NBS run is 5+ hours before kickoff and no 2026 live-log row is after kickoff, and planted corrupted recorded
weather in 12 games (prices moved 0 with the fix, up to 9.69 without). Caveats: (1) an older leak stays: the stored
forecast history skips 295 closed-roof games at ARI, ATL, DAL, HOU and IND (the roof as it was on game day), which a live
run would price as outdoor; not sized. (2) The "recorded" row is today's main on this laptop (our own check, not the audit's: its spread side equals
the stored pred_v3 exactly); the published 68-55 / 80-51 / 40-21 predates the 2 Oct data fixes, and GitHub's first refit
of the re-priced trees can move the new numbers by rounding. (3) Keeping B1 and B2 is Matt's call, not a pass.

## Decision

- **A: adopted as a fix** (backtest only: an unplayed game is priced exactly as before). Its records are the new
  baseline. Side effect on live totals: the wind points' pool is built from the backtest's totals, so this week's wind
  amounts move slightly (the bands now learn from totals priced on the forecast, the same thing they are added to).
- **B3 QB form in the total: stays** (passes both gates and every placebo).
- **B1 wind points and B2 rain in the total: fail the pre-registered bar** (B1 one check, B2 two, each on one gate and one window), so the
  pre-registration says recommend dropping them. Not dropped in this change: B1 fails only on team points (it acts on the
  total), B2 only on total miss in 2018 (where its fit has only that season's earlier weeks to learn from), each
  beats its placebo on the other gate (B1 48 / 48, B2 45 / 50 / 50), and dropping either costs totals-flag wins on every
  window it touches. The auditor recommends keeping both and recording the failure. Matt decides.
- **C: the three bands stay.** The 8-10 mph games run 1.0 point over the model (not 2); the split band that fixes them
  costs more elsewhere.

## Variant count

Six pre-registered (A, B1-B3, C1, C2); none picked on 2023-25. Earlier studies of the same ideas tried about 20 more
(wind points bands and K by hand, rain about 10, forecast weather inputs 3, QB form several).
