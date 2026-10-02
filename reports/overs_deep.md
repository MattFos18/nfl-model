# Overs, in depth (2 Oct 2026)

## Pre-registration (written before any result)

**Claim.** Matt: "an in-depth study on the overs: see what's going on, fine-tune, look for flags and things that can
improve this, thresholds, whatever." Overs lost every way tried on 25 Sep (`experiments/totals_fix.py`: totals are
right-skewed, the typical game lands under while the mean lands over); the live totals rule bets only unders at a 55%+
raw chance (`p_over_emp`). Since then the backtest was made honest (#381 data fixes, #384 leak fixes, #387 `ref_tot`
dropped, #389 forecast weather for played games 2018+). This study re-asks, on main's current code:

- Q1. Why do overs lose, and where (if anywhere) do they not?
- Q2. Is there an over rule worth tracking live?
- Q3. Is the model's total, or its over chance, biased in a way a model change could fix?

**Data and timing.** Everything comes from one walk-forward run of the live model (`model.walk_forward`, weekly refit,
2014-2025; 2014 is priced only so the model-change fits of 2015 have an earlier season). Each input as of before kickoff:

| Input | Source | Known when |
|---|---|---|
| Model total, `p_over_emp` | `model.walk_forward` (earlier games only; played games 2018+ priced on the stored forecast) | before the game |
| `p_over_cal` | `picks.over_calibration`, fit on seasons before the one priced | before Week 1 |
| Dome | `games.dome` (the roof) | schedule |
| Forecast wind, rain | `wind_live.readings`, `rain_readings` (stored pre-kickoff forecasts, 2018+, outdoor games) | before kickoff |
| Pace | both offenses' plays per game (`off_plays`, ratings as of the game) | before the game |
| QB form, QB rating | `model.qb_form` (this season before the game), `qb_rating` | before the game |
| Prime time | `games.primetime` | schedule |
| Total line, spread line | the closing line: grading, and slicing / rule conditions only | close |

No line, split or price is a model input. The two line-size cuts (O9, O10) and the favourite-size slice use the closing
line as a rule condition, as the existing dog and under rules do; they never feed the model.

**Windows.** 2015-18 (untouched), 2019-22 (tuning), 2023-25 (held out); regular season, weeks 1-17 for every bet record,
at the closing total, -110, pushes dropped.

### Part 1. Diagnosis (description only, nothing adopted from it)

- D1 Base rates: blind over record, mean and median of (actual - line), skew, per window.
- D2 The model's over side (p_over_emp >= 0.5) by raw chance band: [0.50, 0.53), [0.53, 0.55), [0.55, 0.58),
  [0.58, 0.62), 0.62+.
- D3 Calibration on the over side: said against came for `p_over_emp` and `p_over_cal`, by band, with z.
- D4 Over side by model edge in points (model total - line): [0, 1), [1, 2), [2, 3), [3, 4), [4, 6), 6+.
- D5 By total line: under 40, 40-43.5, 44-46.5, 47-49.5, 50+ (blind over and the model's over calls at 55%+ raw).
- D6 By week: 1-4, 5-8, 9-13, 14-17.
- D7 Weather: dome vs outdoor; forecast wind 0-5, 5-10, 10-15, 15+ mph (2018+); forecast rain 50%+.
- D8 Pace (sum of both offenses' plays per game, terciles within season), QB form (sum, terciles within season), QB
  rating sum (terciles within season).
- D9 Favourite size: 0-3, 3.5-6.5, 7-9.5, 10+.
- D10 Prime time vs not.
- D11 Bias: mean (model total - actual) and mean (model total - line) by model-total band (under 40, 40-44, 44-48,
  48-52, 52+) and by line band, per window.
- D12 Key numbers: share of games landing on each final total; the over record when the line sits on a key total
  (37, 41, 43, 44, 47, 51) against half a point either side.

Each slice reports the blind over record and the model's over calls at 55%+ raw.

### Part 2. Over rules (each a variant)

Over side only, weeks 1-17:

| # | Rule |
|---|---|
| O1 | `p_over_cal` >= 0.55 |
| O2 | `p_over_cal` >= 0.58 |
| O3 | `p_over_cal` >= 0.60 |
| O4 | `p_over_cal` >= 0.62 |
| O5 | `p_over_emp` >= 0.60 |
| O6 | `p_over_emp` >= 0.65 |
| O7 | dome, `p_over_emp` >= 0.55 |
| O8 | both starters' QB form above 0 (each playing above his career rating this season), `p_over_emp` >= 0.55 |
| O9 | total line 41 or lower, `p_over_emp` >= 0.55 |
| O10 | blind over, total line 40 or lower |
| O11 | blind over, dome |
| O12 | model total 4+ points over the line |
| O13 | outdoor, forecast wind under 5 mph, `p_over_emp` >= 0.55 (2018+) |
| O14 | pace above the median of earlier seasons' games, `p_over_emp` >= 0.55 |

**Pass bar for a rule** (a candidate hidden shadow, never a bet, since it is chosen from a list after looking at
slices): positive units at -110 on every window (better than 52.4%); at least 20 bets on every window; its pooled units
beat at least 190 of 200 within-season shuffles of its reading (the chance, flag or cut shuffled among each season's
games); no bet cost to the live rules (an over rule bets on its own games; any game it shares with the totals flag or the
wind under is counted and reported). **Snooping:** the 14 rules here plus the earlier over variants in the decision log
(25 Sep `totals_fix`: 5 models x 2 cuts and 2 chances x 2 thresholds on the over side, 8 situation splits; 25 Sep
`bet_wins`: overs at every edge; 2 Oct: total 6+ either side). The best rule's strength is also scored family-wise:
outcomes permuted within season 1,000 times, the best of the 14 rules' units each time.

### Part 3. Model changes (tested whatever the diagnosis says)

- M1 Linear recalibration of the total: actual = a + b x model total, least squares on every earlier season's
  walk-forward regular-season games (from 2014), applied to the season priced; the identity under 200 games.
- M2 Band correction: model-total bands under 40, 40-44, 44-48, 48-52, 52+; each band's mean walk-forward miss
  (actual - model total) over earlier seasons, shrunk toward 0 by K = 100 games, added to the total.

For both, `p_over_emp` is re-priced at the corrected total with the same fit's training misses, and the team points are
the corrected total shared out by the spread. **Pass bar** (round-3 rule, `nflmodel.study_gate`): total miss and team
points miss lower on all three windows; no bet cost on the spread flag (4+), the totals flag (55%+ under) and the wind
under (10+ mph), every window; over-chance log loss not worse; 50-draw placebo (earlier seasons' misses shuffled within
season before the correction is fit) beaten 45 of 50 on every window, on both misses. Adopted only if it passes every
part (Matt pre-approved clear winners); otherwise reported.

**Variants:** D1-D12 (description), O1-O14, M1-M2: 16 tested variants.

## Results

`experiments/overs_deep.py`; every table in `reports/overs_deep_results.md` and, long form, `reports/overs_deep.csv`. The
base run is the honest backtest: totals flag 132-117 / 190-146 / 82-59, wind under 24-20 / 143-88 / 77-52, total miss
10.7507 / 10.5161 / 10.1029, as in reports/forecast_weather_backtest.md; the spread flag 69-55 / 77-48 / 37-20 and
team points miss 7.4046 / 7.3645 / 7.2345 differ from it by a game or a ten-thousandth (76-48 / 37-19, 7.2343; likely the
boosted-tree fits, refit in this run). Records: weeks 1-17, closing total, -110.

### Q1. Why overs lose, and where

- **The line is set a little high for the typical game (2015-22; in 2023-25 overs lost only to the vig).** Blind overs went 493-522 (48.6%) / 480-531 (47.5%) / 385-378
  (50.5%). Finals are right-skewed (skew +0.26 / +0.35 / +0.38): the median game landed 0.5 under, 1.0 under and 0.5
  over the line while the mean landed 0.0, +0.2 and +1.2 over. A model of the average total sees the mean; a bet is paid
  on the median.
- **The model's over calls are now near break-even, not clearly losing.** At a 55%+ raw chance: 133-139 (48.9%) /
  111-93 (54.4%) / 138-116 (54.3%), 382-348 (52.3%) overall, just under the 52.4% needed. Its 3+ point over calls went
  231-220 (51.2%), against 49.5% on the 25 Sep backtest. More edge does not help: 4-6 points over the line went
  24-21 / 21-20 / 41-38.
- **The raw chance is too sure of itself on the over side.** Said 60% (58-62% band), came 49.5% / 55.1% / 54.5%; said
  65% (62%+), came 48.1% / 52.8% / 53.4% (z -2.7 / -1.5 / -1.8). The calibrated chance (`p_over_cal`) is honest there
  (every band within z 1.9) but almost never says more than 53% after 2018 (19 games in 2019-22, 42 in 2023-25): the
  model has little over information, and the calibrated chance says so.
- **Where overs lose hardest** (blind): forecast wind 10-15 mph 16-20 / 56-107 / 37-54, forecast rain 50%+ 9-11 / 30-55 /
  21-36, lines on 43 (46-72) and 44.5 (63-91), favourites of 3 or less 44% in 2019-22 and 2023-25. The model's 55%+
  overs already avoid wind and rain (19 calls in wind 10+ and 4 in rain 50%+, 2018-25).
- **Where the model's overs did best:** lines under 40 at 55%+ 20-15 / 15-14 / 34-28 (2019-22 -0.4u at -110), and
  outdoor games at 55%+ 94-83 / 65-59 / 88-63 (+2.5 / +0.1 / +17.0u, 2019-22 at break-even; the mirror of the losing
  dome slice). Description only: neither slice was a pre-registered rule.
- **The rest flip between windows.** Domes, pace, QB form and rating, week, favourite size and prime time all change
  sign from window to window (dome overs at 55%+: 39-56 / 46-34 / 50-53; weeks 14-17 blind: 43% / 51% / 57%).
- **Key numbers.** Of the totals checked, finals land most on 51, 44, 43, 40, 41, 47 and 37 (3.3-3.8% each). Blind
  overs around key numbers are mixed (40.5: 36-25 and 41.5: 53-63 either side of 41 at 48-49; 43: 46-72, 43.5: 67-76,
  44.5: 63-91), one or two hundred games each, many cuts, no window split: description only.

### Q3. Bias the model could fix

The model's total sits above the line on average by +0.37 / -0.34 / +1.03 and above the result by +0.37 / -0.50 /
-0.16. By band of its own total the bias changes sign from window to window (44-48: +0.6 / -1.2 / -0.5; 48-52:
+0.2 / -0.2 / +1.1), so there is no steady shape to correct, and both corrections fail:

| Change | Total miss (2015-18 / 2019-22 / 2023-25) | Team points miss | Totals flag | Placebo, total miss | Gate |
|---|---|---|---|---|---|
| Live | 10.7507 / 10.5161 / 10.1029 | 7.4046 / 7.3645 / 7.2345 | 132-117 / 190-146 / 82-59 | | |
| M1 linear | 10.7245 / 10.5813 / 10.1167 | 7.4043 / 7.3916 / 7.2369 | 186-170 / 202-172 / 80-59 | 46 / 0 / 1 of 50 | FAIL |
| M2 bands | 10.7489 / 10.5503 / 10.1215 | 7.4089 / 7.3804 / 7.2435 | 160-143 / 202-155 / 82-64 | 32 / 8 / 6 of 50 | FAIL |

The over chance's over-confidence likely comes from the line knowing things the model does not (not tested here), which
no line-free change can fix; `p_over_cal` already corrects it for display. Gate tables (as `nflmodel.study_gate` printed them):

M1, total miss:

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | yes | miss 10.7507 -> 10.7245 |
| better on 2019-22 | NO | miss 10.5161 -> 10.5813 |
| better on 2023-25 | NO | miss 10.1029 -> 10.1167 |
| no bet cost: spread flag, 2015-18 | yes | 69-55 -> 69-55 |
| no bet cost: totals flag, 2015-18 | yes | 132-117 -> 186-170 |
| no bet cost: wind under, 2015-18 | yes | 24-20 -> 24-20 |
| no bet cost: spread flag, 2019-22 | yes | 77-48 -> 77-48 |
| no bet cost: totals flag, 2019-22 | NO | 190-146 -> 202-172 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 37-20 -> 37-20 |
| no bet cost: totals flag, 2023-25 | NO | 82-59 -> 80-59 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |
| calibration not worse, 2015-18 | yes | 0.7041 -> 0.7031 |
| calibration not worse, 2019-22 | NO | 0.6913 -> 0.6954 |
| calibration not worse, 2023-25 | NO | 0.6902 -> 0.6911 |
| beats its placebo on 2015-18 | yes | 46 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2019-22 | NO | 0 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2023-25 | NO | 1 of 50 draws (need 45 of at least 50) |

Gate: FAIL (10 of 18); no market input and no look-ahead checked by the model-auditor agent

M2, total miss:

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | yes | miss 10.7507 -> 10.7489 |
| better on 2019-22 | NO | miss 10.5161 -> 10.5503 |
| better on 2023-25 | NO | miss 10.1029 -> 10.1215 |
| no bet cost: spread flag, 2015-18 | yes | 69-55 -> 69-55 |
| no bet cost: totals flag, 2015-18 | yes | 132-117 -> 160-143 |
| no bet cost: wind under, 2015-18 | yes | 24-20 -> 24-20 |
| no bet cost: spread flag, 2019-22 | yes | 77-48 -> 77-48 |
| no bet cost: totals flag, 2019-22 | yes | 190-146 -> 202-155 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 37-20 -> 37-20 |
| no bet cost: totals flag, 2023-25 | NO | 82-59 -> 82-64 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |
| calibration not worse, 2015-18 | yes | 0.7041 -> 0.7040 |
| calibration not worse, 2019-22 | NO | 0.6913 -> 0.6932 |
| calibration not worse, 2023-25 | NO | 0.6902 -> 0.6918 |
| beats its placebo on 2015-18 | NO | 32 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2019-22 | NO | 8 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2023-25 | NO | 6 of 50 draws (need 45 of at least 50) |

Gate: FAIL (10 of 18); no market input and no look-ahead checked by the model-auditor agent

The team points gates (in `reports/overs_deep_results.md`) fail the same way: FAIL 9 of 18 for both.

### Q2. Over rules

| Rule | 2015-18 | 2019-22 | 2023-25 | All | Placebo beaten (of 200) | Passes |
|---|---|---|---|---|---|---|
| O1 cal 55%+ | 33-35 | 0-1 | 3-1 | 36-37 | 109 | no |
| O2 cal 58%+ | 17-21 | 0-0 | 0-0 | 17-21 | 67 | no |
| O3 cal 60%+ | 8-11 | 0-0 | 0-0 | 8-11 | 36 | no |
| O4 cal 62%+ | 8-9 | 0-0 | 0-0 | 8-9 | 86 | no |
| O5 raw 60%+ | 44-45 | 28-33 | 49-44 | 121-122 | 126 | no |
| O6 raw 65%+ | 9-13 | 6-5 | 12-9 | 27-27 | 120 | no |
| O7 dome, raw 55%+ | 39-56 | 46-34 | 50-53 | 135-143 | 92 | no |
| O8 both QBs' form > 0, raw 55%+ | 60-64 | 47-36 | 48-46 | 155-146 | 174 | no |
| **O9 line 41 or lower, raw 55%+** | **42-35** | **29-25** | **56-37** | **127-97 (56.7%, +18.5u)** | **200** | **yes** |
| O10 blind, line 40 or lower | 55-47 | 41-45 | 65-60 | 161-152 | 183 | no |
| O11 blind, dome | 110-130 | 163-137 | 119-127 | 392-394 | 148 | no |
| O12 model 4+ over the line | 32-32 | 26-22 | 48-41 | 106-95 | 169 | no |
| O13 outdoor, wind under 5, raw 55%+ (2018+) | 14-9 | 31-26 | 28-26 | 73-61 | 192 | no (2023-25 loses) |
| O14 pace above earlier median, raw 55%+ | 60-58 | 58-45 | 62-51 | 180-154 | 198 | no (2015-18 loses) |

**O9 passes the pre-registered bar** (whose placebo was pooled over 2015-25), with its cut set in the pre-registration.
How strong it is: not very.
- Snooping: the best of 14 rules made +18.5u; 3.3% of 1,000 within-season outcome shuffles had a best rule as good.
  Earlier over rules on these same games: about 30 in the decision log (25 Sep `totals_fix` and `bet_wins`, 2 Oct
  `more_shadows`) and 300 in `reports/totals_sides.md` (29 Sep: 100, then 200 more), whose one three-window winner was
  already a low-total over (chance 60%+, line under 43). Counting about 330, the chance O9 is luck is high, well above
  0.3 (the rules overlap, so a full Bonferroni would overstate it). The low-total over was a pattern seen before,
  not a fresh hypothesis. Worth tracking, not betting.
- Inside the noise on every window: 77 / 54 / 93 bets at 54.5% / 53.7% / 60.2% against 52.4% break-even
  (z 0.38 / 0.19 / 1.51; pooled z 1.29).
- Added after results (none changes the verdict): the chance shuffled only among line-41-or-lower games, so it must
  beat blind low-total overs: 193 of 200 pooled. The pre-registered placebo was pooled too; per window, at the round-3
  strength (above the 90th percentile), O9 fails 2015-18 and 2019-22 (the auditor's 500-draw rerun: strict placebo
  297 / 448 / 486 of 500, the study's mask placebo 445 / 414 / 491). On 2015-18 blind overs at 41 or lower went 91-80,
  so the model's chance added nothing there. Neighbours: line 40 and the 57% cut at line 41 hold on all three windows;
  line 42 loses 2019-22, line 43 loses 2015-18, 53% at line 41 loses 2019-22. By season: 2017, 2018 and 2020 lost; most
  of the units are 2023-25 (+13.9u of +18.5u); 2019-22 is thin (29-25, +1.4u).
- Fragile to the backtest itself: on the prediction table published before the forecast-weather fix (the first 2 Oct
  weekly run's `pred_v3`) the same rule is 42-34 / 29-28 / 58-40, under break-even on 2019-22. The next weekly run's
  `pred_v3` (on the fixed code) gives the study's 42-35 / 29-25 / 56-37, which the docs rule table carries.
- Overlap with live bets: none with the totals flag (opposite sides by construction); 15 games with the wind under,
  where the over went 5-10 (without them 122-87). The live record will carry those games.

- Live reads the bet-time consensus total (and re-prices the chance there), not the close: a game at 41.5 when the run
  bets and 41 at the close is in the backtest set but not the live one.

## Model-auditor

`reports/audit_overs_deep_2026-10-02.md`: "**Verdict: holds with caveats.** The numbers reproduce exactly, there is no
look-ahead, and 'no over bet, no model change' stands. But O9 is not evidence of a real edge." It reproduced every table
byte for byte, matched the shadow's mask to O9 game for game (225 games), ran the leak test (all changes 0.0), and found
the per-window placebo failures, the undercounted snooping and the small samples quoted above. M1, M2 and the diagnosis
hold.

## Decision

- No over bet. Overs as a whole still do not clear break-even (52.3% at 55%+ raw).
- O9 tracked as a hidden shadow, `shadowoverlow` (`picks.OVER_LOW`: the over when the total is 41 or lower and the raw
  chance 55%+, weeks 1-17), graded live, never bet, off the page; the shadow watch measures it against the totals flag.
  Its backtest through `picks.rule_records` on the study's walk-forward: 42-35 / 29-25 / 56-37.
- No model change: M1 and M2 fail the round-3 rule on 2019-22 and 2023-25 and their placebos.
- Variants: 16 tested here (O1-O14, M1, M2) plus the O9 checks added after results; about 330 earlier over rules.
