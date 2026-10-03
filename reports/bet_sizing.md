# Bet sizing: flat units against bankroll and confidence stakes (3 Oct 2026)

## In plain words

**This is a backtest, not a promise, and not financial advice.** It replays the model's live bets on 2015-2025 games
the model did not train on, at -110. Real results will very likely be worse: the stress test below assumes a win rate
2.5 points lower.

- **Betting a fixed share of the bankroll (S2 1%, S3 2%) beat flat units on 2019-22 and 2023-25, but not on 2015-18**,
  the stretch where the bets only just made money. It wins when the record is good and gives back more when it is
  thin. 2% grew most but more than doubled the worst fall (37% of the bankroll against 18% flat).
- **Sizing by the model's confidence (Kelly, S4 and S5) did not help.** It lost money on 2015-18 (ending 78 and 65 of
  100) where flat units made money, and its worst falls were about twice flat's. The reason: the calibrated chances
  barely separate good bets from bad ones. Kelly staked nothing on 410 of the 1,324 bets (most of the wind unders,
  whose calibrated chance sat at or under break-even), and those bets won 58.3%, more than the 56.8% it did stake.
- **If the true win rate is 2.5 points lower**, every strategy loses money on 2015-18 and Kelly loses the most.
  Over 2015-25 1% of the bankroll ends near flat (171 against 160); Kelly ends lower than flat at the 10th percentile.
- **Recommendation: keep one unit a bet.** If Matt ever wants to compound, 1% of the current bankroll is the only
  option that was close to flat in the bad stretch; Kelly sizing should not be used with today's calibrated chances.

All 1,324 bets, 2015-25 (753-562, 57.3%), starting bankroll 100:

| Strategy | Ending bankroll | Avg yearly growth | Worst drawdown | Longest losing streak | Seasons losing | Kelly bets staked 0 |
|---|---|---|---|---|---|---|
| S1 flat 1 unit | 222.5 | +7.5% | 18.2% | 6 | 1 of 11 | 0 |
| S2 1% of bankroll | 320.2 | +11.2% | 19.9% | 6 | 1 of 11 | 0 |
| S3 2% of bankroll | 908.4 | +22.2% | 37% | 6 | 1 of 11 | 0 |
| S4 quarter Kelly | 259.1 | +9.0% | 37.1% | 7 | 3 of 11 | 414 |
| S5 half Kelly | 368.9 | +12.6% | 44.6% | 7 | 3 of 11 | 411 |


## Pre-registration (written before any result)

**Claim.** Matt (3 Oct 2026) asked whether sizing bets by bankroll or by confidence would increase return. Report
only: the live rule stays one unit a bet; nothing on the page or in the rules changes.

**Bets.** Every live bet on main's honest backtest (`pred_v3.parquet`), 2015 to 2025, regular season, weeks 1 to 17:
the spread flag (|edge| 4+), the totals flag (unders at a 55%+ raw chance, `p_over_emp`) and the wind under
(forecast wind 10+ mph, outdoor games). A game bet by both under rules counts once. Graded at -110 at the closing
line (the schedule's `spread_line`, `total_line`); a push returns the stake.

**Order.** Bets in date order (game day, then kickoff). Every bet on the same day is sized from the bankroll at the
start of that day.

**Variants (the strategies), bankroll starts at 100:**
- S1: flat, 1 unit a bet (1 point of the starting bankroll; the live rule).
- S2: 1% of the current bankroll (compounding).
- S3: 2% of the current bankroll.
- S4: quarter Kelly (`picks.kelly_stake`, fraction 0.25, at -110) from the calibrated win chance the card shows,
  capped at 3% of the bankroll a bet.
- S5: half Kelly, same cap.

**Chances (known before the game only).** Spreads: the cover calibration (`picks.calibration`'s form: a logistic on
|edge| capped at 7) fit on regular-season games from 2015 to the season before the bet's season, needing 200 games
(the live fit starts in 2019; the backtest needs earlier seasons to have one, as `experiments/sizing_backtest.py`
does). Unders, both rules: 1 - `p_over_cal`, from `picks.over_calibrations` (each season on the fit made before it;
the identity in 2015, as the card had). A bet with no chance known (2015's spreads: no earlier season) or a chance
below the 52.4% break-even gets a Kelly stake of 0 under S4 and S5; these are counted.

**Reported per strategy**, for 2015-25 and for each window 2015-18 / 2019-22 / 2023-25 (each window starting again at
100): ending bankroll, average yearly growth (compound, per season), worst drawdown (peak to trough, %), longest losing
streak (bets, pushes skipped), seasons losing money.

**Stress test.** The backtest is likely optimistic. For each of 200 draws (seed 2026), flip randomly chosen wins to
losses until the win rate is 2.5 points lower (round(0.025 x decided bets) flips, over the period being simulated),
the same flips for every strategy; report the median and 10th-percentile ending bankroll.

**Pass bar.** None: this is a description, not a rule change. The adoption gate (`study_gate.gate`) scores model miss
and bet records, which sizing does not change (every strategy bets the same games); no placebo applies.

**This is a backtest, not a promise, and not financial advice.**

## Results

Bets: spread flag 185-123 (310 with pushes), unders 568 wins in 1,014 games (totals flag and wind under, once per
game); these match `picks.record` on every window (2015-18 flag 67-54, totals flag 142-117, wind 119-97; 2019-22 80-52,
183-134, 143-88; 2023-25 38-17, 86-61, 77-52). Every strategy bets the same games; only the stake changes.

### 2015-18 (untouched)

| Strategy | Ending bankroll | Avg yearly growth | Worst drawdown | Longest losing streak | Seasons losing | Kelly bets staked 0 |
|---|---|---|---|---|---|---|
| S1 flat 1 unit | 118.4 | +4.3% | 18.2% | 6 | 1 of 4 | 0 |
| S2 1% of bankroll | 117.8 | +4.2% | 19.9% | 6 | 1 of 4 | 0 |
| S3 2% of bankroll | 133.3 | +7.4% | 37% | 6 | 1 of 4 | 0 |
| S4 quarter Kelly | 78.4 | -5.9% | 35.4% | 7 | 3 of 4 | 243 |
| S5 half Kelly | 64.8 | -10.3% | 44.3% | 7 | 3 of 4 | 242 |

### 2019-22 (tuning)

| Strategy | Ending bankroll | Avg yearly growth | Worst drawdown | Longest losing streak | Seasons losing | Kelly bets staked 0 |
|---|---|---|---|---|---|---|
| S1 flat 1 unit | 168.5 | +13.9% | 7.4% | 6 | 0 of 4 | 0 |
| S2 1% of bankroll | 193.3 | +17.9% | 8.9% | 6 | 0 of 4 | 0 |
| S3 2% of bankroll | 354.5 | +37.2% | 17.5% | 6 | 0 of 4 | 0 |
| S4 quarter Kelly | 201.6 | +19.2% | 13.5% | 6 | 0 of 4 | 123 |
| S5 half Kelly | 277.7 | +29.1% | 16.9% | 5 | 0 of 4 | 121 |

### 2023-25 (held out)

| Strategy | Ending bankroll | Avg yearly growth | Worst drawdown | Longest losing streak | Seasons losing | Kelly bets staked 0 |
|---|---|---|---|---|---|---|
| S1 flat 1 unit | 135.6 | +10.7% | 8.7% | 6 | 0 of 3 | 0 |
| S2 1% of bankroll | 140.7 | +12.1% | 11% | 6 | 0 of 3 | 0 |
| S3 2% of bankroll | 192.3 | +24.4% | 21.1% | 6 | 0 of 3 | 0 |
| S4 quarter Kelly | 164 | +17.9% | 15.3% | 6 | 0 of 3 | 48 |
| S5 half Kelly | 205 | +27.0% | 21.7% | 6 | 0 of 3 | 48 |

Each window starts again at 100. "Kelly bets staked 0": no chance known before the game (43 spreads in 2015, the first
season, have no earlier season to calibrate on) or a calibrated chance at or under 52.4%. By kind, Kelly staked nothing
on 250 of 285 wind-only unders, 77 of 434 totals-flag-only unders, 23 of 295 unders both rules bet, and 60 of 310
spreads. The calibrated chances average 55.6% on spreads, 55.4% on unders bet by both rules, 54.2% on totals-flag
unders and 50.3% on wind-only unders, while those groups won 59.7%, 61.7%, 52.8% and 55.1%: the confidence the card
shows does not rank the bets well enough for Kelly to add anything.

### Stress test: win rate 2.5 points lower

200 draws, wins flipped to losses at random (the same flips for every strategy in a draw). Median / 10th-percentile
ending bankroll, starting at 100. Flat units do not vary across draws (the result depends only on the count of wins).

| Period (stressed win rate) | S1 flat | S2 1% | S3 2% | S4 quarter Kelly | S5 half Kelly |
|---|---|---|---|---|---|
| 2015-25 (54.8%) | 159.5 / 159.5 | 170.9 / 170.5 | 259.8 / 256.9 | 147.5 / 126.5 | 156 / 131.2 |
| 2015-18 (51.9%) | 95.5 / 95.5 | 93.7 / 93.5 | 84.3 / 83.6 | 65.6 / 59.9 | 51.1 / 45.6 |
| 2019-22 (56.4%) | 141.8 / 141.8 | 148.1 / 147.8 | 208.8 / 207.1 | 156.1 / 144.6 | 187.3 / 170.3 |
| 2023-25 (56.8%) | 122.3 / 122.3 | 123.2 / 123 | 147.7 / 146.9 | 139.4 / 131 | 158.1 / 147.3 |

In the 2015-18 stress case every strategy ends under 100 in every draw. Full table: `reports/bet_sizing_stress.csv`.

## Variants and gate

Five strategies, all pre-registered, none added after results. The adoption gate (`study_gate.gate`) does not apply:
sizing changes no model number and no bet (every strategy bets the same games, so miss, records and placebo are
identical across them). Nothing is proposed for adoption, so the model-auditor was not run; it must be before any
sizing change is put to Matt.

## Decision

Report only. The live rule stays one unit a bet (`picks.py`, #385); nothing on the page or in the rules changes.

Script `experiments/bet_sizing.py`; tables `reports/bet_sizing.csv`, `reports/bet_sizing_stress.csv`.
