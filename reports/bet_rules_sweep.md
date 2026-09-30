# Bet rules sweep (30 Sep 2026)

Matt's question: were the thresholds, the timing, the kinds of game, the kind of bet, favourite against underdog and the stake sizes all tested? This sweep tests 283 rules on the three windows (2015-18 never used for any choice, 2019-22 where 4 was chosen, 2023-25 held out), with 2026 to date shown apart. Research only: nothing here changes the site or the picks. Script `experiments/bet_rules_sweep.py`; every rule and window in `reports/bet_rules_sweep.csv` (plus `bet_rules_sweep_kelly.csv` and `bet_rules_sweep_clv.csv`).

The live rules for comparison: **spreads 4+ edge, weeks 1-17**: 68-55, 80-51, 40-21 (+7.5u, +23.9u, +16.9u); 2026 so far 1-2. **Unders at a 55%+ chance**: 135-127, 175-128, 71-59 (-4.7u, +34.2u, +6.1u); 2026 so far 7-4.

## Headline: tested, then the outcome

- **Thresholds.** Spread cuts 2 to 8 by 0.5 and four edge bands; unders at 52% to 62%; point-edge cuts on totals, unders and overs separately; overs at the same cutoffs. **Result: 4 stays.** The 3-4 band loses on all three windows (52-62, 52-65, 39-37). The 4-6 band holds the whole record (61-44, 65-39, 32-18). No other cut beats 4 on all three windows. 6+ goes 7-11, 15-12, 8-3, which overturns the 21 Sep finding that "6+ wins big". For unders, 55% holds. Cuts of 59% to 62% win more often on 2015-22 but earn fewer units than 55% on 2023-25 (61%+: 55-44, 91-43, 21-17). Overs lose at every chance cutoff and every point edge with a real sample, which confirms 25 Sep.
- **Timing.** Weeks 1-4, 5-8, 9-13, 14-17 and 18; every last bet week from 10 to 18; skipping weeks 1-2 or 1-3; a higher bar in weeks 1-3. **Result: the early weeks are the flag's best stretch, not its worst.** Weeks 1-4 go 23-12, 19-12, 19-5. Skipping them, or needing 5+ or 6+ there, costs units on every window. This confirms docs section 14 and overturns the 22 Sep note that weeks 1-6 were weak. Weeks 14-17 are the weak stretch (14-14, 12-14, 7-5) and week 18 is 3-3 and 4-5, so the week-18 skip stands. A last bet week of 15 beats live on all three windows in units and win % (59-46, 73-42, 36-16, placebo 0.04). But it is one of nine cutoffs tried on a pattern already known, and the weeks 1-13 shadow already tracks it. For unders, **needing 59%+ in weeks 1-3 (55% after)** beats the live unders rule on all three windows (124-106, 165-116, 65-53, placebo 0.00). The 57% version passes too. Most of the gain is on 2015-18, where early unders went 31-47 in weeks 1-4.
- **Kinds of game.** Division, primetime (and TNF / SNF / MNF / Sunday slots), dome, short rest, byes, rest edges, home or away side, big or small line, the line on 3 or 7, our number crossing 3 or 7, and high or low totals. **Result: for spreads it is mostly noise.** Crossing 3 or 7 adds nothing (59.5% against 60.2% for neither). Division, primetime, dome and rest all do no better than random subsets of the flag of the same size. The one strong split is the model's side on the road: 38-13, 35-19, 15-7 against 30-42, 45-32, 25-14 at home, which is the road-dog split below. This overturns the first build's docs note (section 9) that away sides were the weaker ones. **For unders, primetime carries the rule.** Primetime unders go 41-25, 45-23, 19-13 (63.2%). Every other under goes 94-102, 130-105, 52-46, near break-even. Blind primetime unders go 105-104, 122-82, 89-82 (54.1%), so the gain comes from the model, not a lean in the market. It has only 32 bets held out.
- **Favourite or underdog.** Our side the favourite, the underdog or a pick'em; home dog, road dog, home favourite, road favourite; at 3, 4, 5 and 6+ and in edge bands; blind market baselines alongside. **Result: the model's favourites never earn their keep, and its road dogs are the best subset in the sweep.** 4+ favourites go 18-17, 7-9, 8-3; 5+ favourites go 4-9, 3-5, 2-2. 4+ dogs, the existing shadow, go 50-38, 73-42, 32-18. Within the dogs, road dogs go 30-11, 34-17, 15-7 (69.3%, placebo 0.01) and home dogs go 20-27, 39-25, 17-11. Blind road dogs go 331-312, 332-265, 216-227, so this is the model's pick and not a market angle. With only 22 bets held out, it is too small to recommend.
- **Kind of bet.** Spread against moneyline on the same side; unders against overs; the model's win chance against the no-vig moneyline at 3, 5, 8 and 10%, calibrated and raw. **Result: nothing beats the spread flag.** The moneyline on the flag's side makes +38.6u, +21.3u and +8.7u (ROI 31%, 16%, 14% against the spread's 6%, 17%, 25%), so it is better on one window only. This confirms 25 Sep. Win chance against the moneyline loses on 2019-22 and 2023-25 at 3% and 5%, and makes nothing on 2023-25 at any cut (best: +0.1u at 10%). This confirms 28 Sep's "not added". Model unders beat blind unders; overs lose every way.
- **Sizing.** Flat staking; 1 / 1.5 / 2u by edge band; a linear stake; the tiers reversed; quarter and half Kelly from the walk-forward calibrated chance. **Result: bigger edges do not earn bigger stakes.** Win % by band: 4-5 106-69 (60.6%), 5-6 52-32 (61.9%), 6+ 30-26 (53.6%). Tiered staking makes ROI 12.8% against 13.9% flat. On spreads, quarter Kelly grew the bankroll less than flat over 2016-25 at about the same average stake: +24.5% against +33.5%, with a worst fall of 19.6% against 14.5%. The 24 Sep log's "quarter Kelly's worst fall 8%" is stale: the current `sizing_backtest.csv` shows 19.3% on 2019-22. On unders, quarter Kelly beat flat (+47.9% against +28.2%) but trailed it on 2023-25.
- **Line timing (2015-21, openers).** The 4+ rule against the opening line, graded at the close and at the opener; how often the close moved our way; whether those bets did better. **Result: the value is in the price you get, not the pick.** Picking against the opener but taking the closing number is worse than the live rule on the same games. Full model: 118-99 (54.4%, +9.1u) against 125-81 (60.7%, +35.9u). Tuesday model: 89-82 (52.0%, -1.2u). Taking the opener with the fair Tuesday model is about as good as the close: 99-67 (59.6%, +25.3u) against 118-86 (57.8%, +23.4u). When the line moved, the close moved toward the opener bet's side 72% of the time for the Tuesday model and 82% for the full model, by 1.7 and 2.1 points on average (every game: 63%). So the model does see where the market goes. Bets where the close moved toward us did *worse*, not better: 56-51 (52.3%, -0.1u) at the opener against 31-11 (73.8%, +18.9u) when it moved away. A move toward us is the market taking the edge.

**What to do with it**
- **Worth a live tracking-only rule (one):** unders needing 59%+ in weeks 1-3. It beats the live unders rule in units and win % on all three windows, has more than 100 bets in each, and its placebo is 0.00. Its gain is small after 2018 (+37.4u against +34.2u; +6.7u against +6.1u).
- **Real patterns that are too small to recommend (under 40 bets held out), to watch in the live log:** primetime unders; road dogs at 4+ (the existing dog shadow already holds them); spreads in weeks 1-4.
- **Already tracked; nothing to add:** the late-season fade (the weeks 1-13 shadow) and dogs (the dog shadow).
- **Noise:** every spread kind-of-game split except road or away; key numbers; the rest and bye splits; division; dome; spread cuts other than 4; stakes scaled by edge; moneyline value; overs.
- **Contradicts earlier notes:** 6+ as the best cut (21 Sep); weeks 1-6 weak (22 Sep); away sides weaker (docs section 9, first build); quarter Kelly's 8% worst fall (24 Sep); and the opener study's Tuesday 2019-21 record, which leans on bad archive rows (see Caveats).

## Tables (the most useful rows)

Each cell is W-L-P, win % and units at -110 (a win +1, a loss -1.1; moneylines risk 1 at the closing price). Luck p is the one-sided binomial against 52.38% on 2015-25 (for moneylines: simulated at the vig-free book chance). Placebo p is the share of 200 random same-size, same-season subsets of the rule's parent pool that earned at least as many units. The pool is the live flag for a filter of the flag, and every game the model has a side on for a new cut. 'Beats live' means more units / higher win % than the live rule on all three windows (for moneylines and stakes, ROI instead of win %).

### Spread thresholds

| Rule | 2015-18 | 2019-22 | 2023-25 | 2015-25 ROI | Seasons up | Luck p (2015-25) | Placebo p | Beats live, all 3 (units / %) | 2026 |
|---|---|---|---|---|---|---|---|---|---|
| LIVE: spread 4+ edge, weeks 1-17 | 68-55-0, 55.3%, +7.5u | 80-51-0, 61.1%, +23.9u | 40-21-1, 65.6%, +16.9u | +13.9% | 8/11 | 0.005 | 0.00 |  | 1-2-0, 33.3%, -1.2u |
| spread 3.5+ edge | 88-80-3, 52.4%, -0.0u | 106-80-1, 57.0%, +18.0u | 57-37-2, 60.6%, +16.3u | +7.0% | 7/11 | 0.067 | 0.03 | no / no | 1-3-0, 25.0%, -2.3u |
| spread 4.5+ edge | 43-36-0, 54.4%, +3.4u | 52-37-0, 58.4%, +11.3u | 25-15-1, 62.5%, +8.5u | +10.1% | 8/11 | 0.071 | 0.88 | no / no | 0-1-0, 0.0%, -1.1u |
| spread 5+ edge | 29-24-0, 54.7%, +2.6u | 37-28-0, 56.9%, +6.2u | 16-6-1, 72.7%, +9.4u | +11.8% | 8/11 | 0.083 | 0.52 | no / no | 0-1-0, 0.0%, -1.1u |
| spread 6+ edge | 7-11-0, 38.9%, -5.1u | 15-12-0, 55.6%, +1.8u | 8-3-0, 72.7%, +4.7u | +2.3% | 5/11 | 0.483 | 0.74 | no / no | 0-1-0, 0.0%, -1.1u |
| spread edge band 2-3 | 86-64-4, 57.3%, +15.6u | 89-85-3, 51.1%, -4.5u | 66-83-3, 44.3%, -25.3u | -2.7% | 4/11 | 0.748 | 0.53 | no / no | 4-3-0, 57.1%, +0.7u |
| spread edge band 3-4 | 52-62-3, 45.6%, -16.2u | 52-65-2, 44.4%, -19.5u | 39-37-2, 51.3%, -1.7u | -11.1% | 4/11 | 0.982 | 0.97 | no / no | 1-2-0, 33.3%, -1.2u |
| spread edge band 4-5 | 39-31-0, 55.7%, +4.9u | 43-23-0, 65.1%, +17.7u | 24-15-0, 61.5%, +7.5u | +15.6% | 8/11 | 0.018 | 0.47 | no / no | 1-1-0, 50.0%, -0.1u |
| spread edge band 5-6 | 22-13-0, 62.9%, +7.7u | 22-16-0, 57.9%, +4.4u | 8-3-1, 72.7%, +4.7u | +18.2% | 6/11 | 0.050 | 0.29 | no / no | 0 bets |
| spread edge band 6+ | 7-11-0, 38.9%, -5.1u | 15-12-0, 55.6%, +1.8u | 8-3-0, 72.7%, +4.7u | +2.3% | 5/11 | 0.483 | 0.79 | no / no | 0-1-0, 0.0%, -1.1u |
| spread edge band 4-6 | 61-44-0, 58.1%, +12.6u | 65-39-0, 62.5%, +22.1u | 32-18-1, 64.0%, +12.2u | +16.5% | 8/11 | 0.003 | 0.36 | no / no | 1-1-0, 50.0%, -0.1u |

### Totals thresholds

| Rule | 2015-18 | 2019-22 | 2023-25 | 2015-25 ROI | Seasons up | Luck p (2015-25) | Placebo p | Beats live, all 3 (units / %) | 2026 |
|---|---|---|---|---|---|---|---|---|---|
| LIVE: under at 55%+ chance, weeks 1-17 | 135-127-3, 51.5%, -4.7u | 175-128-4, 57.8%, +34.2u | 71-59-1, 54.6%, +6.1u | +4.7% | 8/11 | 0.106 | 0.00 |  | 7-4-0, 63.6%, +2.6u |
| under at 53%+ chance | 189-176-3, 51.8%, -4.6u | 222-187-4, 54.3%, +16.3u | 116-100-2, 53.7%, +6.0u | +1.6% | 7/11 | 0.307 | 0.06 | no / no | 9-6-0, 60.0%, +2.4u |
| under at 57%+ chance | 95-86-2, 52.5%, +0.4u | 143-99-3, 59.1%, +34.1u | 41-39-0, 51.2%, -1.9u | +5.9% | 8/11 | 0.090 | 0.45 | no / no | 6-3-0, 66.7%, +2.7u |
| under at 59%+ chance | 73-62-1, 54.1%, +4.8u | 113-68-3, 62.4%, +38.2u | 31-31-0, 50.0%, -3.1u | +9.6% | 7/11 | 0.028 | 0.10 | no / no | 4-1-0, 80.0%, +2.9u |
| under at 61%+ chance | 55-44-0, 55.6%, +6.6u | 91-43-1, 67.9%, +43.7u | 21-17-0, 55.3%, +2.3u | +17.6% | 7/11 | 0.001 | 0.00 | no / yes | 1-0-0, 100.0%, +1.0u |
| under chance band 53%-55% | 54-49-0, 52.4%, +0.1u | 47-59-0, 44.3%, -17.9u | 45-41-1, 52.3%, -0.1u | -5.5% | 5/11 | 0.854 | 0.74 | no / no | 2-2-0, 50.0%, -0.2u |
| under chance band 55%-57% | 40-41-1, 49.4%, -5.1u | 32-29-1, 52.5%, +0.1u | 30-20-1, 60.0%, +8.0u | +1.4% | 5/11 | 0.447 | 0.57 | no / no | 1-1-0, 50.0%, -0.1u |
| under chance band 57%-59% | 22-24-1, 47.8%, -4.4u | 30-31-0, 49.2%, -4.1u | 10-8-0, 55.6%, +1.2u | -5.3% | 5/11 | 0.762 | 0.93 | no / no | 2-2-0, 50.0%, -0.2u |
| under chance band 59%+ | 73-62-1, 54.1%, +4.8u | 113-68-3, 62.4%, +38.2u | 31-31-0, 50.0%, -3.1u | +9.6% | 7/11 | 0.028 | 0.09 | no / no | 4-1-0, 80.0%, +2.9u |
| under at a 3+ point total edge | 61-46-0, 57.0%, +10.4u | 95-50-1, 65.5%, +40.0u | 21-16-0, 56.8%, +3.4u | +16.9% | 10/11 | 0.002 | 0.00 | no / yes | 1-0-0, 100.0%, +1.0u |
| over at 55%+ chance | 121-124-2, 49.4%, -15.4u | 104-108-1, 49.1%, -14.8u | 132-123-2, 51.8%, -3.3u | -4.3% | 3/11 | 0.891 | 0.13 | no / no | 11-10-0, 52.4%, -0.0u |
| over at 60%+ chance | 57-45-2, 55.9%, +7.5u | 36-40-0, 47.4%, -8.0u | 46-47-1, 49.5%, -5.7u | -2.1% | 3/11 | 0.663 | 0.14 | no / no | 4-6-0, 40.0%, -2.6u |
| over at a 3+ point total edge | 70-66-2, 51.5%, -2.6u | 61-65-0, 48.4%, -10.5u | 86-85-2, 50.3%, -7.5u | -4.3% | 4/11 | 0.839 | 0.25 | no / no | 6-8-0, 42.9%, -2.8u |
| every under (blind, weeks 1-17) | 522-493-9, 51.4%, -20.3u | 531-480-12, 52.5%, +3.0u | 378-385-5, 49.5%, -45.5u | -2.1% | 5/11 | 0.875 | 1.00 | no / no | 25-23-0, 52.1%, -0.3u |
| every over (blind, weeks 1-17) | 493-522-9, 48.6%, -81.2u | 480-531-12, 47.5%, -104.1u | 385-378-5, 50.5%, -30.8u | -7.0% | 2/11 | 1.000 | 1.00 | no / no | 23-25-0, 47.9%, -4.5u |

### Timing, spreads

| Rule | 2015-18 | 2019-22 | 2023-25 | 2015-25 ROI | Seasons up | Luck p (2015-25) | Placebo p | Beats live, all 3 (units / %) | 2026 |
|---|---|---|---|---|---|---|---|---|---|
| LIVE: spread 4+ edge, weeks 1-17 | 68-55-0, 55.3%, +7.5u | 80-51-0, 61.1%, +23.9u | 40-21-1, 65.6%, +16.9u | +13.9% | 8/11 | 0.005 | 0.00 |  | 1-2-0, 33.3%, -1.2u |
| 4+ edge, weeks 1-4 | 23-12-0, 65.7%, +9.8u | 19-12-0, 61.3%, +5.8u | 19-5-0, 79.2%, +13.5u | +29.4% | 7/11 | 0.002 | 0.01 | no / yes | 1-2-0, 33.3%, -1.2u |
| 4+ edge, weeks 5-8 | 19-13-0, 59.4%, +4.7u | 22-11-0, 66.7%, +9.9u | 2-8-1, 20.0%, -6.8u | +9.4% | 6/11 | 0.229 | 0.66 | no / no | 0 bets |
| 4+ edge, weeks 9-13 | 12-16-0, 42.9%, -5.6u | 27-14-0, 65.8%, +11.6u | 12-3-0, 80.0%, +8.7u | +15.9% | 6/11 | 0.077 | 0.52 | no / no | 0 bets |
| 4+ edge, weeks 14-17 | 14-14-0, 50.0%, -1.4u | 12-14-0, 46.2%, -3.4u | 7-5-0, 58.3%, +1.5u | -4.5% | 5/11 | 0.696 | 0.95 | no / no | 0 bets |
| 4+ edge, weeks 18-18 | 0 bets | 3-3-0, 50.0%, -0.3u | 4-5-0, 44.4%, -1.5u | -10.9% | 2/5 | 0.758 | 0.86 | no / no | 0 bets |
| 4+ edge, last bet week 13 | 54-41-0, 56.8%, +8.9u | 68-37-0, 64.8%, +27.3u | 33-16-1, 67.3%, +15.4u | +18.8% | 8/11 | 0.001 | 0.07 | no / yes | 1-2-0, 33.3%, -1.2u |
| 4+ edge, last bet week 15 | 59-46-0, 56.2%, +8.4u | 73-42-0, 63.5%, +26.8u | 36-16-1, 69.2%, +18.4u | +17.9% | 8/11 | 0.001 | 0.04 | yes / yes | 1-2-0, 33.3%, -1.2u |
| 4+ edge, last bet week 16 | 61-48-0, 56.0%, +8.2u | 76-47-0, 61.8%, +24.3u | 38-20-1, 65.5%, +16.0u | +15.2% | 8/11 | 0.004 | 0.33 | no / no | 1-2-0, 33.3%, -1.2u |
| 4+ edge, last bet week 18 | 68-55-0, 55.3%, +7.5u | 83-54-0, 60.6%, +23.6u | 44-26-1, 62.9%, +15.4u | +12.8% | 8/11 | 0.008 | 1.00 | no / no | 1-2-0, 33.3%, -1.2u |
| 4+ edge, skip weeks 1-2 | 58-48-0, 54.7%, +5.2u | 68-44-0, 60.7%, +19.6u | 27-19-1, 58.7%, +6.1u | +10.6% | 7/11 | 0.040 | 0.96 | no / no | 1-0-0, 100.0%, +1.0u |
| 4+ edge, skip weeks 1-3 | 49-46-0, 51.6%, -1.6u | 64-41-0, 61.0%, +18.9u | 26-16-1, 61.9%, +8.4u | +9.7% | 7/11 | 0.065 | 0.94 | no / no | 0 bets |
| weeks 1-3 need 5+, else 4+ | 56-50-0, 52.8%, +1.0u | 75-48-0, 61.0%, +22.2u | 32-18-1, 64.0%, +12.2u | +11.5% | 8/11 | 0.025 | 0.93 | no / no | 0-1-0, 0.0%, -1.1u |
| weeks 1-3 need 6+, else 4+ | 49-47-0, 51.0%, -2.7u | 69-44-0, 61.1%, +20.6u | 30-17-1, 63.8%, +11.3u | +10.4% | 8/11 | 0.046 | 0.93 | no / no | 0-1-0, 0.0%, -1.1u |

### Timing, unders

| Rule | 2015-18 | 2019-22 | 2023-25 | 2015-25 ROI | Seasons up | Luck p (2015-25) | Placebo p | Beats live, all 3 (units / %) | 2026 |
|---|---|---|---|---|---|---|---|---|---|
| LIVE: under at 55%+ chance, weeks 1-17 | 135-127-3, 51.5%, -4.7u | 175-128-4, 57.8%, +34.2u | 71-59-1, 54.6%, +6.1u | +4.7% | 8/11 | 0.106 | 0.00 |  | 7-4-0, 63.6%, +2.6u |
| under 55%+, weeks 1-4 | 31-47-0, 39.7%, -20.7u | 46-40-2, 53.5%, +2.0u | 21-17-0, 55.3%, +2.3u | -7.4% | 5/11 | 0.879 | 1.00 | no / no | 7-4-0, 63.6%, +2.6u |
| under 55%+, weeks 5-8 | 36-35-1, 50.7%, -2.5u | 46-30-1, 60.5%, +13.0u | 16-14-1, 53.3%, +0.6u | +5.7% | 8/11 | 0.236 | 0.39 | no / no | 0 bets |
| under 55%+, weeks 9-13 | 44-24-2, 64.7%, +17.6u | 55-34-0, 61.8%, +17.6u | 24-14-0, 63.2%, +8.6u | +20.4% | 9/11 | 0.002 | 0.00 | no / yes | 0 bets |
| under 55%+, weeks 14-17 | 24-21-0, 53.3%, +0.9u | 28-24-1, 53.8%, +1.6u | 10-14-0, 41.7%, -5.4u | -2.2% | 5/11 | 0.634 | 0.82 | no / no | 0 bets |
| under 55%+, weeks 18-18 | 0 bets | 4-0-0, 100.0%, +4.0u | 3-5-0, 37.5%, -2.5u | +11.4% | 3/5 | 0.453 | 0.58 | no / no | 0 bets |
| BLIND: every under in weeks 9-13 (no model) | 149-136-4, 52.3%, -0.6u | 152-132-4, 53.5%, +6.8u | 113-100-3, 53.0%, +3.0u | +1.1% | 6/11 | 0.391 |  | no / no | 0 bets |
| under 55%+, skip weeks 1-3 | 112-91-3, 55.2%, +11.9u | 138-100-3, 58.0%, +28.0u | 53-47-1, 53.0%, +1.3u | +6.9% | 8/11 | 0.050 | 0.09 | no / no | 0 bets |
| under: weeks 1-3 need 57%+, else 55%+ | 128-114-3, 52.9%, +2.6u | 173-123-4, 58.5%, +37.7u | 68-56-1, 54.8%, +6.4u | +6.4% | 8/11 | 0.045 | 0.04 | yes / yes | 6-3-0, 66.7%, +2.7u |
| under: weeks 1-3 need 59%+, else 55%+ | 124-106-3, 53.9%, +7.4u | 165-116-4, 58.7%, +37.4u | 65-53-1, 55.1%, +6.7u | +7.4% | 9/11 | 0.027 | 0.00 | yes / yes | 4-1-0, 80.0%, +2.9u |

### Kinds of game, spreads (filters of the live flag)

| Rule | 2015-18 | 2019-22 | 2023-25 | 2015-25 ROI | Seasons up | Luck p (2015-25) | Placebo p | Beats live, all 3 (units / %) | 2026 |
|---|---|---|---|---|---|---|---|---|---|
| LIVE: spread 4+ edge, weeks 1-17 | 68-55-0, 55.3%, +7.5u | 80-51-0, 61.1%, +23.9u | 40-21-1, 65.6%, +16.9u | +13.9% | 8/11 | 0.005 | 0.00 |  | 1-2-0, 33.3%, -1.2u |
| 4+ edge, our side at home | 30-42-0, 41.7%, -16.2u | 45-32-0, 58.4%, +9.8u | 25-14-1, 64.1%, +9.6u | +1.6% | 5/11 | 0.441 | 1.00 | no / no | 1-1-0, 50.0%, -0.1u |
| 4+ edge, our side away | 38-13-0, 74.5%, +23.7u | 35-19-0, 64.8%, +14.1u | 15-7-0, 68.2%, +7.3u | +32.3% | 9/11 | 0.000 | 0.00 | no / yes | 0-1-0, 0.0%, -1.1u |
| BLIND: every away side ATS (no model), weeks 1-17 | 508-486-30, 51.1%, -26.6u | 524-476-23, 52.4%, +0.4u | 376-373-19, 50.2%, -34.3u | -2.0% | 2/11 | 0.869 |  | no / no | 21-24-3, 46.7%, -5.4u |
| 4+ edge, division game | 29-26-0, 52.7%, +0.4u | 28-20-0, 58.3%, +6.0u | 12-4-0, 75.0%, +7.6u | +10.7% | 7/11 | 0.129 | 0.64 | no / no | 0-2-0, 0.0%, -2.2u |
| 4+ edge, non-division game | 39-29-0, 57.4%, +7.1u | 52-31-0, 62.6%, +17.9u | 28-17-1, 62.2%, +9.3u | +15.9% | 8/11 | 0.011 | 0.48 | no / no | 1-0-0, 100.0%, +1.0u |
| 4+ edge, primetime | 17-13-0, 56.7%, +2.7u | 12-12-0, 50.0%, -1.2u | 8-5-0, 61.5%, +2.5u | +5.4% | 7/11 | 0.366 | 0.77 | no / no | 0-1-0, 0.0%, -1.1u |
| 4+ edge, not primetime | 51-42-0, 54.8%, +4.8u | 68-39-0, 63.5%, +25.1u | 32-16-1, 66.7%, +14.4u | +16.2% | 8/11 | 0.004 | 0.32 | no / no | 1-1-0, 50.0%, -0.1u |
| 4+ edge, dome or closed roof | 19-15-0, 55.9%, +2.5u | 20-11-0, 64.5%, +7.9u | 12-8-0, 60.0%, +3.2u | +14.5% | 8/11 | 0.097 | 0.53 | no / no | 0-1-0, 0.0%, -1.1u |
| 4+ edge, outdoor or open roof | 49-40-0, 55.1%, +5.0u | 60-40-0, 60.0%, +16.0u | 28-13-1, 68.3%, +13.7u | +13.7% | 8/11 | 0.017 | 0.61 | no / no | 1-1-0, 50.0%, -0.1u |
| 4+ edge, a team on short rest (<=5 days) | 5-3-0, 62.5%, +1.7u | 4-4-0, 50.0%, -0.4u | 2-2-0, 50.0%, -0.2u | +5.0% | 4/10 | 0.497 | 0.65 | no / no | 0 bets |
| 4+ edge, our side off a bye (rest >= 12) | 3-3-0, 50.0%, -0.3u | 8-1-0, 88.9%, +6.9u | 1-0-0, 100.0%, +1.0u | +43.2% | 6/9 | 0.057 | 0.11 | no / no | 0 bets |
| 4+ edge, opponent off a bye | 7-8-0, 46.7%, -1.8u | 9-2-0, 81.8%, +6.8u | 4-1-1, 80.0%, +2.9u | +23.2% | 7/11 | 0.120 | 0.23 | no / no | 0 bets |
| 4+ edge, big line \|line\| >= 7 | 22-19-0, 53.7%, +1.1u | 25-21-0, 54.4%, +1.9u | 10-6-0, 62.5%, +3.4u | +5.7% | 7/11 | 0.308 | 0.97 | no / no | 0 bets |
| 4+ edge, small line \|line\| < 7 | 46-36-0, 56.1%, +6.4u | 55-30-0, 64.7%, +22.0u | 30-15-1, 66.7%, +13.5u | +18.0% | 8/11 | 0.004 | 0.10 | no / yes | 1-2-0, 33.3%, -1.2u |
| 4+ edge, line on 3 exactly | 10-4-0, 71.4%, +5.6u | 10-8-0, 55.6%, +1.2u | 5-3-1, 62.5%, +1.7u | +19.3% | 6/11 | 0.130 | 0.30 | no / no | 0 bets |
| 4+ edge, our number crosses 3 | 28-23-0, 54.9%, +2.7u | 42-20-0, 67.7%, +20.0u | 17-14-0, 54.8%, +1.6u | +15.3% | 8/11 | 0.032 | 0.59 | no / no | 0-1-0, 0.0%, -1.1u |
| 4+ edge, our number crosses 7 | 24-20-0, 54.5%, +2.0u | 19-16-0, 54.3%, +1.4u | 9-5-0, 64.3%, +3.5u | +6.7% | 8/11 | 0.282 | 0.83 | no / no | 0 bets |
| 4+ edge, crosses neither 3 nor 7 | 21-15-0, 58.3%, +4.5u | 23-19-0, 54.8%, +2.1u | 15-5-1, 75.0%, +9.5u | +14.9% | 8/11 | 0.073 | 0.48 | no / no | 1-1-0, 50.0%, -0.1u |
| 4+ edge, high total (>= 47) | 18-16-0, 52.9%, +0.4u | 26-17-0, 60.5%, +7.3u | 10-8-0, 55.6%, +1.2u | +8.5% | 7/11 | 0.222 | 0.95 | no / no | 0 bets |
| 4+ edge, low total (<= 40) | 7-4-0, 63.6%, +2.6u | 9-7-0, 56.2%, +1.3u | 6-4-1, 60.0%, +1.6u | +13.5% | 5/11 | 0.243 | 0.29 | no / no | 0 bets |

### Kinds of game, unders

| Rule | 2015-18 | 2019-22 | 2023-25 | 2015-25 ROI | Seasons up | Luck p (2015-25) | Placebo p | Beats live, all 3 (units / %) | 2026 |
|---|---|---|---|---|---|---|---|---|---|
| LIVE: under at 55%+ chance, weeks 1-17 | 135-127-3, 51.5%, -4.7u | 175-128-4, 57.8%, +34.2u | 71-59-1, 54.6%, +6.1u | +4.7% | 8/11 | 0.106 | 0.00 |  | 7-4-0, 63.6%, +2.6u |
| under 55%+, primetime | 41-25-0, 62.1%, +13.5u | 45-23-1, 66.2%, +19.7u | 19-13-0, 59.4%, +4.7u | +20.8% | 8/11 | 0.003 | 0.00 | no / yes | 0-2-0, 0.0%, -2.2u |
| under 55%+, not primetime | 94-102-3, 48.0%, -18.2u | 130-105-3, 55.3%, +14.5u | 52-46-1, 53.1%, +1.4u | -0.4% | 4/11 | 0.555 | 0.99 | no / no | 7-2-0, 77.8%, +4.8u |
| BLIND: every primetime under (no model), weeks 1-17 | 105-104-1, 50.2%, -9.4u | 122-82-4, 59.8%, +31.8u | 89-82-2, 52.0%, -1.2u | +3.3% | 6/11 | 0.213 |  | no / no | 4-5-0, 44.4%, -1.5u |
| under 55%+, division game | 54-43-1, 55.7%, +6.7u | 49-36-2, 57.6%, +9.4u | 14-17-0, 45.2%, -4.7u | +4.9% | 7/11 | 0.250 | 0.35 | no / no | 1-0-0, 100.0%, +1.0u |
| under 55%+, dome or closed roof | 22-16-0, 57.9%, +4.4u | 30-33-2, 47.6%, -6.3u | 19-12-0, 61.3%, +5.8u | +2.7% | 7/11 | 0.407 | 0.70 | no / no | 0-1-0, 0.0%, -1.1u |
| under 55%+, outdoor or open roof | 113-111-3, 50.4%, -9.1u | 145-95-2, 60.4%, +40.5u | 52-47-1, 52.5%, +0.3u | +5.1% | 8/11 | 0.109 | 0.35 | no / no | 7-3-0, 70.0%, +3.7u |
| under 55%+, a team on short rest (<=5 days) | 9-4-0, 69.2%, +4.6u | 11-5-0, 68.8%, +5.5u | 7-6-0, 53.8%, +0.4u | +22.7% | 8/11 | 0.082 | 0.06 | no / no | 0-1-0, 0.0%, -1.1u |
| under 55%+, high total (>= 47) | 75-69-2, 52.1%, -0.9u | 105-86-4, 55.0%, +10.4u | 36-30-1, 54.5%, +3.0u | +2.8% | 7/11 | 0.293 | 0.79 | no / no | 1-3-0, 25.0%, -2.3u |
| under 55%+, low total (<= 40) | 7-7-0, 50.0%, -0.7u | 4-3-0, 57.1%, +0.7u | 3-3-0, 50.0%, -0.3u | -1.0% | 4/10 | 0.599 | 0.52 | no / no | 0 bets |
| under 55%+, wind 15+ mph outdoors | 20-17-1, 54.0%, +1.3u | 26-22-0, 54.2%, +1.8u | 9-9-0, 50.0%, -0.9u | +1.9% | 7/11 | 0.458 | 0.56 | no / no | 0 bets |

### Favourite or underdog

| Rule | 2015-18 | 2019-22 | 2023-25 | 2015-25 ROI | Seasons up | Luck p (2015-25) | Placebo p | Beats live, all 3 (units / %) | 2026 |
|---|---|---|---|---|---|---|---|---|---|
| LIVE: spread 4+ edge, weeks 1-17 | 68-55-0, 55.3%, +7.5u | 80-51-0, 61.1%, +23.9u | 40-21-1, 65.6%, +16.9u | +13.9% | 8/11 | 0.005 | 0.00 |  | 1-2-0, 33.3%, -1.2u |
| 4+ edge, our side the favourite | 18-17-0, 51.4%, -0.7u | 7-9-0, 43.8%, -2.9u | 8-3-0, 72.7%, +4.7u | +1.6% | 8/11 | 0.498 | 0.90 | no / no | 0 bets |
| 4+ edge, our side the underdog | 50-38-0, 56.8%, +8.2u | 73-42-0, 63.5%, +26.8u | 32-18-1, 64.0%, +12.2u | +17.0% | 8/11 | 0.003 | 0.15 | no / no | 1-2-0, 33.3%, -1.2u |
| 4+ edge, home dog | 20-27-0, 42.5%, -9.7u | 39-25-0, 60.9%, +11.5u | 17-11-1, 60.7%, +4.9u | +4.4% | 6/11 | 0.324 | 0.96 | no / no | 1-1-0, 50.0%, -0.1u |
| 4+ edge, road dog | 30-11-0, 73.2%, +17.9u | 34-17-0, 66.7%, +15.3u | 15-7-0, 68.2%, +7.3u | +32.3% | 10/11 | 0.000 | 0.01 | no / yes | 0-1-0, 0.0%, -1.1u |
| 4+ edge, home favourite | 10-15-0, 40.0%, -6.5u | 6-7-0, 46.2%, -1.7u | 8-3-0, 72.7%, +4.7u | -6.5% | 5/11 | 0.733 | 0.95 | no / no | 0 bets |
| 4+ edge, road favourite | 8-2-0, 80.0%, +5.8u | 1-2-0, 33.3%, -1.2u | 0 bets | +32.2% | 3/4 | 0.174 | 0.32 | no / no | 0 bets |
| 3+ edge, road dog | 49-35-2, 58.3%, +10.5u | 50-36-1, 58.1%, +10.4u | 26-19-1, 57.8%, +5.1u | +11.0% | 7/11 | 0.052 | 0.01 | no / no | 0-1-0, 0.0%, -1.1u |
| 5+ edge, road dog | 16-4-0, 80.0%, +11.6u | 17-10-0, 63.0%, +6.0u | 9-2-0, 81.8%, +6.8u | +38.2% | 9/11 | 0.002 | 0.01 | no / yes | 0 bets |
| 5+ edge, our side the favourite | 4-9-0, 30.8%, -5.9u | 3-5-0, 37.5%, -2.5u | 2-2-0, 50.0%, -0.2u | -31.3% | 3/10 | 0.968 | 1.00 | no / no | 0 bets |
| model's side a road dog, any edge, weeks 1-17 | 189-173-11, 52.2%, -1.3u | 199-146-11, 57.7%, +38.4u | 124-118-7, 51.2%, -5.8u | +3.0% | 7/11 | 0.175 | 0.02 | no / no | 7-9-0, 43.8%, -2.9u |
| BLIND: every road dog ATS (no model), weeks 1-17 | 331-312-21, 51.5%, -12.2u | 332-265-16, 55.6%, +40.5u | 216-227-11, 48.8%, -33.7u | -0.3% | 6/11 | 0.560 |  | no / no | 14-16-2, 46.7%, -3.6u |
| BLIND: every home dog ATS (no model), weeks 1-17 | 171-176-9, 49.3%, -22.6u | 211-192-7, 52.4%, -0.2u | 146-160-8, 47.7%, -30.0u | -4.5% | 3/11 | 0.943 |  | no / no | 8-7-1, 53.3%, +0.3u |
| edge band 4-6, our side the favourite | 17-13-0, 56.7%, +2.7u | 6-8-0, 42.9%, -2.8u | 6-2-0, 75.0%, +3.8u | +6.5% | 7/10 | 0.364 | 0.81 | no / no | 0 bets |
| edge band 4-6, our side the underdog | 44-31-0, 58.7%, +9.9u | 59-31-0, 65.6%, +24.9u | 26-16-1, 61.9%, +8.4u | +19.0% | 7/11 | 0.003 | 0.21 | no / no | 1-1-0, 50.0%, -0.1u |

### Kind of bet (moneylines: units risk 1 at the closing price)

| Rule | 2015-18 | 2019-22 | 2023-25 | 2015-25 ROI | Seasons up | Luck p (2015-25) | Placebo p | Beats live, all 3 (units / %) | 2026 |
|---|---|---|---|---|---|---|---|---|---|
| LIVE: spread 4+ edge, weeks 1-17 | 68-55-0, 55.3%, +7.5u | 80-51-0, 61.1%, +23.9u | 40-21-1, 65.6%, +16.9u | +13.9% | 8/11 | 0.005 | 0.00 |  | 1-2-0, 33.3%, -1.2u |
| moneyline on the 4+ spread side | 63-60-0, 51.2%, +38.6u | 57-73-1, 43.9%, +21.3u | 32-30-0, 51.6%, +8.7u | +21.8% | 8/11 | 0.003 |  | no / no | 1-2-0, 33.3%, -0.9u |
| moneyline on the 4+ spread side, our side the dog | 37-51-0, 42.0%, +33.6u | 49-65-1, 43.0%, +25.5u | 23-28-0, 45.1%, +6.7u | +26.0% | 8/11 | 0.003 |  | no / no | 1-2-0, 33.3%, -0.9u |
| moneyline on the 4+ spread side, our side the favourite | 26-9-0, 74.3%, +5.0u | 8-8-0, 50.0%, -4.2u | 9-2-0, 81.8%, +2.1u | +4.5% | 9/11 | 0.222 |  | no / no | 0 bets |
| moneyline on the 5+ spread side | 26-27-0, 49.1%, +25.8u | 28-37-0, 43.1%, +7.3u | 11-12-0, 47.8%, +4.5u | +26.7% | 8/11 | 0.015 |  | no / no | 0-1-0, 0.0%, -1.0u |
| moneyline, model win chance (cal) beats no-vig book by 3% | 304-360-2, 45.8%, +44.3u | 320-372-4, 46.2%, -33.0u | 227-273-0, 45.4%, -30.0u | -1.0% | 5/11 | 0.249 |  | no / no | 17-14-0, 54.8%, +9.0u |
| moneyline, model win chance (cal) beats no-vig book by 5% | 210-268-2, 43.9%, +36.0u | 217-272-3, 44.4%, -44.0u | 155-198-0, 43.9%, -31.8u | -3.0% | 5/11 | 0.504 |  | no / no | 13-11-0, 54.2%, +6.6u |
| moneyline, model win chance (cal) beats no-vig book by 8% | 114-155-0, 42.4%, +31.8u | 124-144-2, 46.3%, +6.6u | 75-106-0, 41.4%, -16.0u | +3.1% | 5/11 | 0.107 |  | no / no | 5-7-0, 41.7%, +1.2u |
| moneyline, model win chance (cal) beats no-vig book by 10% | 86-101-0, 46.0%, +41.7u | 81-96-2, 45.8%, +15.4u | 48-64-0, 42.9%, +0.1u | +12.0% | 9/11 | 0.009 |  | no / no | 1-3-0, 25.0%, -1.2u |
| moneyline, win chance (cal) beats book by 5%, dogs only | 126-233-0, 35.1%, +21.0u | 107-194-2, 35.5%, -15.7u | 70-153-0, 31.4%, -34.9u | -3.4% | 5/11 | 0.522 |  | no / no | 7-11-0, 38.9%, +2.3u |
| moneyline, model win chance (raw) beats no-vig book by 5% | 207-290-1, 41.6%, +31.9u | 170-320-4, 34.7%, -44.0u | 134-223-1, 37.5%, -24.5u | -2.7% | 6/11 | 0.468 |  | no / no | 12-11-0, 52.2%, +8.4u |

### Sizing

| Stakes | 2015-18 | 2019-22 | 2023-25 | ROI 2015-25 (on the amount risked) |
|---|---|---|---|---|
| LIVE: spread 4+ edge, weeks 1-17 | +7.5u | +23.9u | +16.9u | +13.9% |
| 4+ flag, tiered stakes (1u 4-5, 1.5u 5-6, 2u 6+) | +6.2u | +27.9u | +23.9u | +12.8% |
| 4+ flag, linear stakes (edge/4 units, capped at 2u) | +6.3u | +27.6u | +23.2u | +12.8% |
| 4+ flag, inverse tiers (2u 4-5, 1.5u 5-6, 1u 6+) | +16.2u | +43.8u | +26.8u | +14.8% |
| LIVE: under at 55%+ chance, weeks 1-17 | -4.7u | +34.2u | +6.1u | +4.7% |
| under 55%+, tiered stakes (1u 55-57%, 1.5u 57-59%, 2u 59%+) | -2.1u | +70.3u | +3.6u | +5.8% |
| under 55%+, linear stakes (1u + (chance-55%)/4%, capped 2u) | -1.8u | +68.6u | +5.2u | +5.4% |

Kelly (bankroll 100 at the start of each window, each week's bets sized from the bankroll at the start of the week; flat = 1 unit = 1% of the starting 100; the calibrated chance is walk-forward, so 2015 has no fit and the first window is 2016-18):

| Rule | Window | Staking | Record | Growth | Worst fall | Mean stake |
|---|---|---|---|---|---|---|
| spread 4+ flag | 2016-18 | flat 1u | 39-39 | -3.5% | 14.5% | 1.00% |
| spread 4+ flag | 2016-18 | quarter Kelly | 39-39 | -12.1% | 13.9% | 0.28% |
| spread 4+ flag | 2016-18 | half Kelly | 39-39 | -23.0% | 26.3% | 0.53% |
| spread 4+ flag | 2019-22 | flat 1u | 80-51 | +21.7% | 9.2% | 1.00% |
| spread 4+ flag | 2019-22 | quarter Kelly | 80-51 | +21.2% | 19.3% | 1.75% |
| spread 4+ flag | 2019-22 | half Kelly | 80-51 | +43.6% | 35.2% | 4.37% |
| spread 4+ flag | 2023-25 | flat 1u | 40-21 | +15.4% | 4.6% | 1.00% |
| spread 4+ flag | 2023-25 | quarter Kelly | 40-21 | +16.9% | 4.1% | 1.08% |
| spread 4+ flag | 2023-25 | half Kelly | 40-21 | +35.6% | 8.1% | 2.39% |
| spread 4+ flag | 2016-25 | flat 1u | 159-111 | +33.5% | 14.5% | 1.00% |
| spread 4+ flag | 2016-25 | quarter Kelly | 159-111 | +24.5% | 19.6% | 1.09% |
| spread 4+ flag | 2016-25 | half Kelly | 159-111 | +49.8% | 35.8% | 2.38% |
| under 55%+ | 2016-18 | flat 1u | 93-93 | -8.5% | 22.0% | 1.00% |
| under 55%+ | 2016-18 | quarter Kelly | 93-93 | -6.3% | 18.7% | 0.80% |
| under 55%+ | 2016-18 | half Kelly | 93-93 | -15.4% | 35.2% | 1.44% |
| under 55%+ | 2019-22 | flat 1u | 175-128 | +31.1% | 7.6% | 1.00% |
| under 55%+ | 2019-22 | quarter Kelly | 175-128 | +55.0% | 6.8% | 0.72% |
| under 55%+ | 2019-22 | half Kelly | 175-128 | +136.6% | 13.2% | 1.78% |
| under 55%+ | 2023-25 | flat 1u | 71-59 | +5.5% | 8.5% | 1.00% |
| under 55%+ | 2023-25 | quarter Kelly | 71-59 | +1.9% | 15.1% | 1.35% |
| under 55%+ | 2023-25 | half Kelly | 71-59 | +1.3% | 28.8% | 2.83% |
| under 55%+ | 2016-25 | flat 1u | 339-280 | +28.2% | 22.0% | 1.00% |
| under 55%+ | 2016-25 | quarter Kelly | 339-280 | +47.9% | 18.7% | 0.98% |
| under 55%+ | 2016-25 | half Kelly | 339-280 | +102.8% | 35.2% | 2.36% |

### Line timing (2015-21, 1763 games with an archive opener; 23 rows dropped as bad archive rows)

| Rule | 2015-18 | 2019-21 | 2015-21 |
|---|---|---|---|
| full model, 4+ edge vs close, graded at close | 64-52-0, 55.2%, +6.8u | 61-29-0, 67.8%, +29.1u | 125-81-0, 60.7%, +35.9u |
| full model, 4+ edge vs opener, graded at close | 55-48-0, 53.4%, +2.2u | 63-51-1, 55.3%, +6.9u | 118-99-1, 54.4%, +9.1u |
| full model, 4+ edge vs opener, graded at opener | 61-41-1, 59.8%, +15.9u | 74-38-3, 66.1%, +32.2u | 135-79-4, 63.1%, +48.1u |
| Tuesday model, 4+ edge vs close, graded at close | 62-47-0, 56.9%, +10.3u | 56-39-2, 59.0%, +13.1u | 118-86-2, 57.8%, +23.4u |
| Tuesday model, 4+ edge vs opener, graded at close | 46-44-0, 51.1%, -2.4u | 43-38-0, 53.1%, +1.2u | 89-82-0, 52.0%, -1.2u |
| Tuesday model, 4+ edge vs opener, graded at opener | 49-39-2, 55.7%, +6.1u | 50-28-3, 64.1%, +19.2u | 99-67-5, 59.6%, +25.3u |
| Tuesday model, 4+ edge vs opener, graded at opener, close moved toward our side | 24-26-1, 48.0%, -4.6u | 32-25-3, 56.1%, +4.5u | 56-51-4, 52.3%, -0.1u |
| Tuesday model, 4+ edge vs opener, graded at opener, close moved away | 19-9-1, 67.9%, +9.1u | 12-2-0, 85.7%, +9.8u | 31-11-1, 73.8%, +18.9u |
| Tuesday model, 4+ edge vs opener, graded at opener, close did not move | 6-4-0, 60.0%, +1.6u | 6-1-0, 85.7%, +4.9u | 12-5-0, 70.6%, +6.5u |
| Tuesday model, 3+ edge vs opener, graded at opener | 119-73-10, 62.0%, +38.7u | 103-67-7, 60.6%, +29.3u | 222-140-17, 61.3%, +68.0u |
| Tuesday model, 3+ edge vs close, graded at close | 124-90-3, 57.9%, +25.0u | 97-81-3, 54.5%, +7.9u | 221-171-6, 56.4%, +32.9u |
| Tuesday model, under at a 3+ point edge vs opener, graded at opener | 75-50-3, 60.0%, +20.0u | 103-75-1, 57.9%, +20.5u | 178-125-4, 58.8%, +40.5u |
| Tuesday model, under at a 3+ point edge vs close, graded at close | 52-39-0, 57.1%, +9.1u | 73-50-1, 59.4%, +18.0u | 125-89-1, 58.4%, +27.1u |

How often the close moved toward the opener bet's side (4+ against the opener, weeks 1-17):

| Model | Window | Bets | Toward | Away | No move | Toward, share of moves | Mean points toward |
|---|---|---|---|---|---|---|---|
| full model | 2015-18 | 103 | 66 | 24 | 13 | 73% | +1.37 |
| full model | 2019-21 | 115 | 93 | 12 | 10 | 89% | +2.76 |
| full model | 2015-21 | 218 | 159 | 36 | 23 | 82% | +2.10 |
| Tuesday model | 2015-18 | 90 | 51 | 29 | 10 | 64% | +1.08 |
| Tuesday model | 2019-21 | 81 | 60 | 14 | 7 | 81% | +2.34 |
| Tuesday model | 2015-21 | 171 | 111 | 43 | 17 | 72% | +1.68 |
| full model (every game) | 2015-21 | 1747 | 965 | 488 | 294 | 66% | +0.69 |
| Tuesday model (every game) | 2015-21 | 1747 | 917 | 536 | 294 | 63% | +0.61 |

### Every rule that beat the live rule on all three windows (units or win %), with the checks

| Rule | Beats in units / win % | Fewest bets in a window | Placebo p | Verdict |
|---|---|---|---|---|
| 4+ edge, weeks 1-4 | no / yes | 24 | 0.010 | too small (under 40 bets in a window) |
| 4+ edge, last bet week 10 | no / yes | 42 | 0.000 | a subset: higher win % but fewer units; watch only |
| 4+ edge, last bet week 11 | no / yes | 47 | 0.005 | a subset: higher win % but fewer units; watch only |
| 4+ edge, last bet week 12 | no / yes | 48 | 0.020 | a subset: higher win % but fewer units; watch only |
| 4+ edge, last bet week 13 | no / yes | 49 | 0.065 | a subset: higher win % but fewer units; watch only |
| 4+ edge, last bet week 14 | no / yes | 49 | 0.055 | a subset: higher win % but fewer units; watch only |
| 4+ edge, last bet week 15 | yes / yes | 52 | 0.035 | passes every check, but it is one of nine cutoffs tried on a known late-season fade that the weeks 1-13 shadow already tracks |
| 4+ edge, weeks 1-13 (the early shadow) | no / yes | 49 | 0.055 | a subset: higher win % but fewer units; watch only |
| 4+ edge, our side away | no / yes | 22 | 0.000 | too small (under 40 bets in a window) |
| 4+ edge, small line \|line\| < 7 | no / yes | 45 | 0.105 | a subset: higher win % but fewer units; watch only |
| 4+ edge, road dog | no / yes | 22 | 0.010 | too small (under 40 bets in a window) |
| 5+ edge, road dog | no / yes | 11 | 0.005 | too small (under 40 bets in a window) |
| under at 61%+ chance | no / yes | 38 | 0.000 | too small (under 40 bets in a window) |
| under at 62%+ chance | no / yes | 33 | 0.000 | too small (under 40 bets in a window) |
| under at a 3+ point total edge | no / yes | 37 | 0.000 | too small (under 40 bets in a window) |
| under at a 4+ point total edge | no / yes | 14 | 0.000 | too small (under 40 bets in a window) |
| under at a 5+ point total edge | no / yes | 8 | 0.005 | too small (under 40 bets in a window) |
| over at a 7+ point total edge | no / yes | 1 | 0.040 | too small (under 40 bets in a window) |
| under 55%+, weeks 9-13 | no / yes | 38 | 0.000 | too small (under 40 bets in a window) |
| under 55%+, last bet week 14 | no / yes | 112 | 0.160 | a subset: higher win % but fewer units; watch only |
| under: weeks 1-3 need 57%+, else 55%+ | yes / yes | 124 | 0.035 | passes every check (the 59% version is stronger) |
| under: weeks 1-3 need 59%+, else 55%+ | yes / yes | 118 | 0.000 | passes every check: the one new tracking-only candidate |
| under 55%+, primetime | no / yes | 32 | 0.000 | too small (under 40 bets in a window) |
| 4+ flag, inverse tiers (2u 4-5, 1.5u 5-6, 1u 6+) | yes / no | 61 |  | more units only because it stakes more; ROI barely moves |

## Caveats

- **Many tests.** 283 rules were graded. 183 of them have a placebo, and 30 of those have a placebo p of 0.05 or less. With this many tries, several will look good by luck. Many of the low placebo values are the same few patterns counted several times: late weeks, dogs and road sides, and big unders. That is why a rule has to beat live on every window, pass the placebo and have 40 bets a window before it counts. Two families do: a last bet week of 15 on spreads, and a higher bar for unders in weeks 1-3. Both are small changes.
- **The windows are not all clean.** 2015-18 never set a choice. 2019-22 set the 4-point cut. 2023-25 has been used as a second test for model inputs since 22 Sep. Any rule found here was found by looking at all three windows, so its record describes the backtest; only live games can confirm it.
- **The placebo tests the filter, not the model.** For a filter of the flag it asks whether the filter picks better bets than random bets from the flag. The flag itself, against random picks from every game the model has a side on, has a placebo of 0.00; the unders rule's, against random unders, is 0.00.
- **Moneyline results** are graded at nflverse's closing moneyline. The luck test for them is simulated at the vig-free book chance of each side, because a flat 52.4% break-even does not apply.
- **Openers.** The archive covers 2015-21 only. 23 rows were dropped because the archive's own close disagrees with nflverse's, a total is under 25, a 0 opener sits on a 7+ close, or the opener flips sign by more than 10 points (most are typing errors; a few may be real moves in week-17 rest games, such as CHI at MIN and TEN at HOU in 2019). On the Tuesday model, 4+ against the opener in 2019-21, those rows went 11-2. That is why `reports/opener_study.md` shows 64-33 there against 50-28 here (it also counts week 18). The full model's number includes Sunday's injury report and weather, so grading it at the opener flatters it; the Tuesday model is the fair early number.
- **Kelly** reads the walk-forward calibrated cover chance. It says 51-55% for 4+ edges, but those edges won about 60%, and it rises with the edge while the win rate does not. So Kelly adds variance rather than edge on spreads.
- **2026** to date is 1-2 on the spread flag and 7-4 on unders. It is shown in the CSV and the tables, and it is far too few games to move any conclusion.
