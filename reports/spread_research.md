# Spread research: the hook, team bias, dogs and matchups (30 Sep 2026)

Research only. Nothing here changes the site or the picks. Script `experiments/spread_research.py`. Every rule and window is in `reports/spread_research.csv` (one row per rule and window; team rows carry the team-miss columns).

The data is the walk-forward table the site grades (`backtest.join(pred_v3, games)`), regular season, with a closing line. The live rule is the model's side at 4+ points off the close, weeks 1-17, pushes out, -110: 68-55, 80-51, 40-21 (+7.5u, +23.9u, +16.9u) on 2015-18 / 2019-22 / 2023-25, and 1-2 in 2026.

## Headlines: what was tested, and the outcome

- **A. Buying the hook.** Tested: where the final margin landed on the 316 bets at 4+ (2015-25), and buying half a point on seven kinds of bet at three prices. **Outcome: the hook almost never costs us, and buying pays only on or off 3, and only at -125 or better.**
  - In 11 seasons the flag lost 6 bets by half a point (4 of them with the game on 3, none on 7) and pushed once (on 3).
  - Buying on every bet: -0.6u at -120 (the price of buying off 3), -1.9u at -125 and -3.2u at -130, 2015-25.
  - Buying only when the half point moves on or off 3: +1.2u / +0.9u / +0.6u at -120 and +0.7u / +0.2u / +0.4u at -125 on the three windows, and about zero at -130. That is roughly +0.1u to +0.25u a season.
  - Over every game the model has a side on (723 bets on or off 3), the half point is worth about 33-35 cents. It breaks even at about -133 to -135.
  - Off 7 and on other numbers it gains nothing. Buying on bets that cross 3 or 7, or on lines of 2.5, 3.5, 6.5 or 7.5, goes one way on some windows and the other way on others.
- **B. Team bias.** Tested: the model's margin miss by team, its record against the spread by team, whether a team's bias carries from one season to the next, and six walk-forward corrections (shrunk, prior seasons only). **Outcome: there is no team bias to use.**
  - A team's miss in one season has a correlation of -0.01 with its miss the next season (320 pairs; -0.01 / +0.05 / -0.08 by window). The mean of the two prior seasons gives +0.005.
  - Every correction made the margin miss worse on all three windows, by 0.03 to 0.26 points.
  - The model's long-run misses by team are the market's too (correlation 0.90 across teams). So the teams it "misses" are teams that beat or fell short of everyone's expectations. Its bets in their games are ordinary.
- **C. Dogs, thresholds and matchups.** Tested: 176 rules. They cover favourite, dog and pick'em; home and road, favourite and dog; and the size of the dog, each at cuts of 3 to 7. They also cover rating thirds, division and conference, rematches, teams off a 14+ win or loss, 2+ game streaks and dogs off a blowout, each at 4+ and on every game, with blind baselines. **Outcome: nothing earns more units than live on all three windows.**
  - The dog and favourite results repeat today's sweep exactly. Road dogs are the best subset (30-11, 34-17, 15-7) but have only 22 bets held out.
  - "4+ only when our side is the dog or pick'em" is **not** better than live on every window. It goes 32-18 (+12.2u) against 40-21 (+16.9u) on 2023-25, where the model's favourites went 8-3.
  - Every matchup filter at 4+ is noise: 2 to 27 bets a window, no steady sign, and no placebo that holds.

**Worth a tracking-only rule**
- **One, as a price and not a pick:** on flag bets where our number is -3, +3, +2.5 or -3.5, log the price to buy the half point on or off 3, and grade the bet both ways. Buy only at -125 or better. This is about 7 bets a season. It is under 40 bets a window on the flag itself (30 / 29 / 19 bought), so it is not a recommendation. The every-game sample (723 bets, positive at -120 and -125 on all three windows) says the value is structural and not luck.
- **Watch only (too small):** small dogs (+0.5 to +3) at 4+: 20-11, 24-15, 19-6, placebo 0.04, 25 bets a window. It overlaps the dog shadow and the road dogs already watched.

**Noise**
- Every per-team correction.
- Team records against the spread. They do not carry from one window to the next (correlation +0.31 / -0.08 / -0.29 on every game).
- Rating-third matchups, division, conference, rematches, off a 14+ win or loss, streaks, and dogs off a blowout, all as filters of the flag.
- Dogs of +3.5 and up as a split.
- Buying off 7, buying on every bet, and buying on lines that cross 3 or 7.

**Against earlier findings**
- **Confirmed:**
  - Today's sweep: road dogs real but thin; the model's favourites losing on 2015-18 and 2019-22 at every cut from 3 to 6; the dog-only rule not beating live; key-number splits as noise for picking bets.
  - 21-22 Sep: per-team home edges, head-to-head, and coach and QB records against the spread do not carry.
  - 25 Sep: win streak and letdown inputs are noise. Here they are also noise as bet filters.
  - 29 Sep (situational): rematch is noise, as a filter too.
  - 23 Sep dog shadow: dog-side flags win on all three windows (50-38, 73-42, 32-18). But dropping the favourites costs units held out.
- **Refined, not overturned:** the sweep's "key numbers are noise" is right for choosing bets. The price of the hook on 3 is a separate question, and there the half point does carry value (above).
- **Overturned:** nothing.

## A. The hook

Where the 4+ bets landed (our side; "lost by the hook" means we lost against the line by exactly half a point):

| Window | Bets (with pushes) | Losses | Losses where the game ended by exactly 3 / 7 | Lost by half a point (game on 3 / on 7) | Lost by 1 | Pushes (line on 3 / 7) | Won by half a point |
|---|---|---|---|---|---|---|---|
| 2015-18 | 123 | 55 | 8 / 2 | 3 (2 / 0) | 2 | 0 | 1 |
| 2019-22 | 131 | 51 | 4 / 7 | 2 (2 / 0) | 2 | 0 | 1 |
| 2023-25 | 62 | 21 | 3 / 0 | 1 (0 / 0) | 1 | 1 (1 / 0) | 4 |
| 2015-25 | 316 | 127 | 15 / 9 | 6 (4 / 0) | 5 | 1 (1 / 0) | 6 |

With half a point more, 6 losses would have pushed and 1 push would have won. That is worth about +7.6u gross in 11 seasons, against roughly 8u of extra juice for buying on every bet.

**Price assumption.** Half a point costs -120 when it moves on or off 3 (for example -3 to -2.5, or +2.5 to +3), -120 on or off 7, and -115 on any other number. -125 and -130 on 3 are shown as well. Books vary, and many charge more than -125 on 3. A bought bet risks the price to win 1. Units are compared with the same bets at -110.

Buying on the 4+ bets (gain against live on the same bets in brackets):

| Buy half a point on | Price on/off 3 | 2015-18 | 2019-22 | 2023-25 | 2015-25 gain vs -110 | Bought per window |
|---|---|---|---|---|---|---|
| every 4+ bet | -120 | 68-52-3, +7.4u (-0.1u) | 80-49-2, +22.8u (-1.1u) | 41-20-1, +17.6u (+0.7u) | -0.6u | 123/131/62 |
| every 4+ bet | -130 | +6.4u (-1.1u) | +21.4u (-2.5u) | +17.2u (+0.3u) | -3.2u | |
| line on 2.5 / 3.5 / 6.5 / 7.5 | -120 | +9.4u (+1.9u) | +25.4u (+1.5u) | +16.2u (-0.7u) | +2.8u | 38/27/27 |
| our number crosses 3 or 7 | -120 | +8.4u (+0.9u) | +21.7u (-2.2u) | +17.0u (+0.1u) | -1.1u | 87/89/41 |
| on or off 3 only | -120 | +8.7u (+1.2u) | +24.8u (+0.9u) | +17.5u (+0.6u) | +2.7u | 30/29/19 |
| on or off 3 only | -125 | +8.2u (+0.7u) | +24.1u (+0.2u) | +17.3u (+0.4u) | +1.4u | |
| on or off 3 only | -130 | +7.7u (+0.2u) | +23.5u (-0.4u) | +17.1u (+0.2u) | +0.0u | |
| on or off 7 only | -120 | +6.9u (-0.6u) | +23.4u (-0.5u) | +16.5u (-0.4u) | -1.5u | 10/11/9 |
| touches neither 3 nor 7 (-115) | | +6.8u (-0.7u) | +22.4u (-1.6u) | +17.4u (+0.5u) | -1.8u | 83/91/34 |
| LIVE, -110 | | 68-55-0, +7.5u | 80-51-0, +23.9u | 40-21-1, +16.9u | | |

What half a point is worth on every game the model has a side on (weeks 1-17, units gained per 100 bets bought, against -110):

| Our line | Bets 2015-25 | Pushes turned to wins | Half-point losses turned to pushes | At -120: 2015-18 / 2019-22 / 2023-25 | 2015-25 at -120 / -125 / -130 |
|---|---|---|---|---|---|
| -3 (to -2.5, off 3) | 149 | 16 | 0 | +11.1 / -1.3 / +9.4 | +6.3 / +4.1 / +1.9 |
| +3 (to +3.5, off 3) | 259 | 28 | 0 | +7.5 / +6.8 / +4.7 | +6.5 / +4.3 / +2.1 |
| +2.5 (to +3, onto 3) | 196 | 0 | 16 | +0.8 / +4.6 / +10.7 | +5.0 / +3.1 / +1.1 |
| -3.5 (to -3, onto 3) | 119 | 0 | 10 | +9.0 / +1.1 / +3.8 | +5.2 / +3.2 / +1.2 |
| all on or off 3 | 723 | 44 | 26 | +6.8 / +3.6 / +7.1 | +5.8 / +3.7 / +1.6 (2019-22 at -130: -0.8) |
| -7 (off 7) | 70 | 7 | 0 | +18.4 / +2.1 / +0.0 | +5.9 |
| +7 (off 7) | 91 | 3 | 0 | +0.0 / -4.8 / +0.6 | -1.5 |
| +6.5 (onto 7) | 83 | 0 | 5 | +0.4 / +7.4 / -4.3 | +2.5 |
| -7.5 (onto 7) | 54 | 0 | 4 | +6.2 / -0.5 / +2.1 | +2.8 |
| any other number (-115) | 1,794 | 18 | 29 | -0.5 / +0.4 / +1.7 | +0.5 |

## B. Team bias

The miss is the model's margin minus the actual margin, with each team as "the team" (above 0 means the model rated the team too high). It covers all regular-season games from 2015-25, about 181 a team. The six most under-rated and six most over-rated teams:

| Team | Model miss (pts/game) | t | Market miss | By window 2015-18 / 2019-22 / 2023-25 | Model's side, every game | 4+ bets in its games | 4+ on / against it |
|---|---|---|---|---|---|---|---|
| BAL | -2.37 | -2.3 | -2.31 | -0.7 / -3.0 / -3.6 | 94-78, +8.2u | 9-9, -0.9u | 5-3 / 4-6 |
| NE | -1.82 | -1.8 | -1.50 | -3.2 / -1.8 / -0.1 | 85-85, -8.5u | 12-11, -0.1u | 5-3 / 7-8 |
| MIN | -1.64 | -1.9 | -0.94 | -2.1 / +0.1 / -3.3 | 80-90, -19.0u | 13-4, +8.6u | 4-0 / 9-4 |
| BUF | -1.52 | -1.5 | -2.14 | +0.5 / -3.5 / -1.6 | 92-76, +8.4u | 14-8, +5.2u | 9-5 / 5-3 |
| NO | -1.48 | -1.5 | -1.52 | -2.1 / -2.5 / +0.6 | 80-93, -22.3u | 10-5, +4.5u | 7-1 / 3-4 |
| SEA | -1.23 | -1.4 | -1.16 | -0.9 / -0.4 / -2.7 | 89-80, +1.0u | 10-5, +4.5u | 5-2 / 5-3 |
| WAS | +1.08 | +1.1 | +0.62 | +1.0 / +0.7 / +1.8 | 89-84, -3.4u | 12-6, +5.4u | 10-4 / 2-2 |
| CLE | +1.28 | +1.5 | +2.64 | +2.7 / +0.4 / +0.6 | 89-84, -3.4u | 21-16, +3.4u | 1-5 / 20-11 |
| MIA | +1.29 | +1.2 | +0.75 | +2.6 / +0.6 / +0.6 | 81-91, -19.1u | 18-12, +4.8u | 11-10 / 7-2 |
| ATL | +1.61 | +1.7 | +0.99 | +0.2 / +2.1 / +2.8 | 83-91, -17.1u | 9-7, +1.3u | 7-7 / 2-0 |
| LV | +1.71 | +1.9 | +2.06 | +0.9 / +1.1 / +3.5 | 93-79, +6.1u | 15-6, +8.4u | 3-1 / 12-5 |
| NYJ | +1.99 | +2.1 | +2.03 | +1.5 / +1.3 / +3.5 | 83-88, -13.8u | 16-14, +0.6u | 6-7 / 10-7 |

- **Named teams.** The model has under-rated Baltimore the most (-2.4 a game, and it has grown each window) and over-rated the Jets (+2.0) and the Raiders (+1.7), both steady and largest on 2023-25. New England's under-rating faded to nothing by 2023-25. Minnesota's flips between windows. Only 2 of 32 teams sit at |t| of 2 or more, where chance alone gives about 1.6. The spread of the team misses is 1.15 points, against about 0.96 from noise alone.
- **Persistence.** One season to the next: correlation -0.01, slope -0.01 (320 team pairs). Between windows: 0.14 (2015-18 against 2019-22), 0.13 (2019-22 against 2023-25) and 0.23 (2015-18 against 2023-25). Split halves (2015-19 against 2020-25): 0.36 (p 0.05). So a small long-run lean exists, but a season tells you nothing about the next one. The market's team misses carry about as much (0.23 to 0.28 between windows), which is why the model gains nothing.
- **Correction.** Each team's shrunk miss from prior seasons was subtracted from its side of the model's margin (b = sum of misses / (games + k)). 2015 has no prior season in pred_v3, so it is left alone. The flag was then re-cut on the corrected number:

| Correction | Margin miss change 2015-18 / 2019-22 / 2023-25 (below 0 is better) | Mean size (pts) | 4+ flag: 2015-18 | 2019-22 | 2023-25 |
|---|---|---|---|---|---|
| prior season, k=17 | +0.159 / +0.161 / +0.262 | 1.73 | 121-96-6, +15.4u | 136-117-4, +7.3u | 96-86-4, +1.4u |
| prior season, k=34 | +0.077 / +0.070 / +0.133 | 1.15 | 85-61-1, +17.9u | 100-81-2, +10.9u | 71-65-2, -0.5u |
| prior season, k=68 | +0.035 / +0.026 / +0.056 | 0.69 | 75-53-1, +16.7u | 84-69-1, +8.1u | 50-44-2, +1.6u |
| 3 prior seasons (decay 0.5), k=17 | +0.144 / +0.145 / +0.166 | 1.49 | 111-89-3, +13.1u | 135-111-3, +12.9u | 71-68-2, -3.8u |
| 3 prior seasons (decay 0.5), k=34 | +0.076 / +0.076 / +0.101 | 1.07 | 90-62-1, +21.8u | 104-90-2, +5.0u | 63-47-2, +11.3u |
| 3 prior seasons (decay 0.5), k=68 | +0.036 / +0.034 / +0.049 | 0.69 | 78-57-0, +15.3u | 86-70-1, +9.0u | 50-37-2, +9.3u |
| LIVE (no correction) | | | 68-55-0, +7.5u | 80-51-0, +23.9u | 40-21-1, +16.9u |

The miss gets worse in every row and every window, and the smaller the shrinkage, the worse it gets. The corrected flag adds bets but earns fewer units than live on 2019-22 and on 2023-25 in every variant.

## C. Underdogs, thresholds and matchups

Cells show W-L-P, win % and units at -110. Luck p is the one-sided binomial against 52.38% on 2015-25. Placebo p is the share of 200 within-season shuffles of the selection inside its parent pool that earn at least as many units: pooled 2015-25, then by window. The parent pool is the flag for a 4+ filter, every game for an every-game split, and the cut's own bets for other cuts.

**Favourite, dog and pick'em by cut.** No 4+ bet is ever a pick'em (0 bets at every cut from 3.5 up). All the other cuts, and the size-of-dog cells, are in the CSV.

| Rule | 2015-18 | 2019-22 | 2023-25 | ROI 2015-25 | Luck p | Placebo p | Beats live, all 3 (units / %) | Fewest bets |
|---|---|---|---|---|---|---|---|---|
| LIVE: 4+ edge, weeks 1-17 | 68-55-0, 55.3%, +7.5u | 80-51-0, 61.1%, +23.9u | 40-21-1, 65.6%, +16.9u | +13.9% | 0.005 | 0.00; 0.24/0.01/0.01 |  | 61 |
| 3+ edge, our side the underdog | 88-84-2, 51.2%, -4.4u | 117-88-1, 57.1%, +20.2u | 59-45-2, 56.7%, +9.5u | +4.8% | 0.146 | 0.10 | no / no | 104 |
| 3+ edge, our side the favourite | 31-33-1, 48.4%, -5.3u | 15-28-1, 34.9%, -15.8u | 20-13-1, 60.6%, +5.7u | -10.0% | 0.907 | 0.95 | no / no | 33 |
| 3.5+ edge, our side the underdog | 67-51-2, 56.8%, +10.9u | 93-63-1, 59.6%, +23.7u | 47-28-1, 62.7%, +16.2u | +13.2% | 0.005 | 0.00; 0.02/0.12/0.28 | no / no | 75 |
| 4+ edge, underdog or pick'em (the dog shadow) | 50-38-0, 56.8%, +8.2u | 73-42-0, 63.5%, +26.8u | 32-18-1, 64.0%, +12.2u | +17.0% | 0.003 | 0.10 | no / no | 50 |
| 4+ edge, our side the favourite | 18-17-0, 51.4%, -0.7u | 7-9-0, 43.8%, -2.9u | 8-3-0, 72.7%, +4.7u | +1.6% | 0.498 | 0.94 | no / no | 11 |
| 5+ edge, our side the underdog | 25-15-0, 62.5%, +8.5u | 34-23-0, 59.7%, +8.7u | 14-4-1, 77.8%, +9.6u | +21.2% | 0.011 | 0.01 | no / no | 18 |
| 5+ edge, our side the favourite | 4-9-0, 30.8%, -5.9u | 3-5-0, 37.5%, -2.5u | 2-2-0, 50.0%, -0.2u | -31.3% | 0.968 | 1.00 | no / no | 4 |
| every game, our side the underdog | 319-302-16, 51.4%, -13.2u | 362-296-16, 55.0%, +36.4u | 230-242-12, 48.7%, -36.2u | -0.7% | 0.626 | 0.12 | no / no | 472 |
| every game, our side the favourite | 186-183-14, 50.4%, -15.3u | 161-181-7, 47.1%, -38.1u | 145-132-7, 52.3%, -0.2u | -4.9% | 0.951 | 0.86 | no / no | 277 |

**Home and road, favourite and dog; size of the dog (4+):**

| Rule | 2015-18 | 2019-22 | 2023-25 | ROI 2015-25 | Luck p | Placebo p | Beats live, all 3 (units / %) | Fewest bets |
|---|---|---|---|---|---|---|---|---|
| 4+ edge, road dog | 30-11-0, 73.2%, +17.9u | 34-17-0, 66.7%, +15.3u | 15-7-0, 68.2%, +7.3u | +32.3% | 0.000 | 0.01; 0.00/0.15/0.41 | no / yes | 22 |
| 4+ edge, home dog | 20-27-0, 42.5%, -9.7u | 39-25-0, 60.9%, +11.5u | 17-11-1, 60.7%, +4.9u | +4.4% | 0.324 | 1.00 | no / no | 28 |
| 4+ edge, road favourite | 8-2-0, 80.0%, +5.8u | 1-2-0, 33.3%, -1.2u | 0 bets | +32.2% | 0.174 | 0.34 | no / no | 0 |
| 4+ edge, home favourite | 10-15-0, 40.0%, -6.5u | 6-7-0, 46.2%, -1.7u | 8-3-0, 72.7%, +4.7u | -6.5% | 0.733 | 0.93 | no / no | 11 |
| 3+ edge, road dog | 49-35-2, 58.3%, +10.5u | 50-36-1, 58.1%, +10.4u | 26-19-1, 57.8%, +5.1u | +11.0% | 0.052 | 0.04 | no / no | 45 |
| 4+ edge, dog +0.5 to +3 | 20-11-0, 64.5%, +7.9u | 24-15-0, 61.5%, +7.5u | 19-6-1, 76.0%, +12.4u | +26.6% | 0.004 | 0.04; 0.05/0.51/0.10 | no / yes | 25 |
| 4+ edge, dog +3.5 to +6.5 | 10-11-0, 47.6%, -2.1u | 27-7-0, 79.4%, +19.3u | 6-7-0, 46.2%, -1.7u | +20.7% | 0.047 | 0.32 | no / no | 13 |
| 4+ edge, dog +7 and up | 20-16-0, 55.6%, +2.4u | 22-20-0, 52.4%, -0.0u | 7-5-0, 58.3%, +1.5u | +3.9% | 0.388 | 0.95 | no / no | 12 |
| BLIND: every road dog | 331-312-21, 51.5%, -12.2u | 332-265-16, 55.6%, +40.5u | 216-227-11, 48.8%, -33.7u | -0.3% | 0.560 | | | 443 |

**Matchups at 4+ (filters of the flag).** Rating thirds use the model's own pre-game rating. That is its points equation's weights for the game on the as-of EPA and points ratings and the QB (own offense's pull on its points minus own defense's pull on the opponent's). It correlates 0.96 with the model's spread, and teams are split into thirds among those playing each week.

| Rule | 2015-18 | 2019-22 | 2023-25 | ROI | Luck p | Placebo p | Beats live (units / %) | Fewest bets |
|---|---|---|---|---|---|---|---|---|
| our side top third vs opponent top third | 9-4-0, +4.6u | 9-5-0, +3.5u | 9-3-0, +5.7u | +32.2% | 0.025 | 0.17 | no / yes | 12 |
| our side top vs opponent bottom | 7-8-0, -1.8u | 4-3-0, +0.7u | 6-0-0, +6.0u | +15.9% | 0.245 | 0.44 | no / no | 6 |
| our side bottom vs opponent top | 4-8-0, -4.8u | 7-9-0, -2.9u | 2-3-0, -1.3u | -24.8% | 0.953 | 1.00 | no / no | 5 |
| our side mid vs opponent mid | 6-7-0, -1.7u | 8-5-0, +2.5u | 1-1-0, -0.1u | +2.3% | 0.526 | 0.65 | no / no | 2 |
| our side bottom vs opponent bottom | 11-8-0, +2.2u | 13-7-0, +5.3u | 6-2-1, +3.8u | +21.9% | 0.076 | 0.43 | no / yes | 8 |
| same third | 26-19-0, +5.1u | 30-17-0, +11.3u | 16-6-1, +9.4u | +20.6% | 0.013 | 0.15 | no / yes | 22 |
| our side the higher third | 26-16-0, +8.4u | 21-14-0, +5.6u | 17-5-0, +11.5u | +23.4% | 0.009 | 0.12 | no / no | 22 |
| our side the lower third | 16-20-0, -6.0u | 29-20-0, +7.0u | 7-10-0, -4.0u | -2.7% | 0.649 | 0.98 | no / no | 17 |
| division game | 29-26-0, +0.4u | 28-20-0, +6.0u | 12-4-0, +7.6u | +10.7% | 0.129 | 0.69 | no / no | 16 |
| conference, not division | 22-16-0, +4.4u | 28-19-0, +7.1u | 17-10-0, +6.0u | +14.2% | 0.069 | 0.59 | no / no | 27 |
| non-conference | 17-13-0, +2.7u | 24-12-0, +10.8u | 11-7-1, +3.3u | +18.2% | 0.050 | 0.34 | no / no | 18 |
| second meeting this season | 11-15-0, -5.5u | 9-8-0, +0.2u | 4-1-0, +2.9u | -4.5% | 0.683 | 0.89 | no / no | 5 |
| our side off a 14+ loss | 5-10-0, -6.0u | 14-11-0, +1.9u | 4-6-0, -2.6u | -12.2% | 0.852 | 0.99 | no / no | 10 |
| our side off a 14+ win | 10-6-0, +3.4u | 13-3-0, +9.7u | 6-4-0, +1.6u | +31.8% | 0.021 | 0.18 | no / no | 10 |
| our side on a 2+ game win streak | 18-7-0, +10.3u | 20-9-0, +10.1u | 5-5-0, -0.5u | +28.3% | 0.012 | 0.07 | no / no | 10 |
| our side on a 2+ game losing streak | 17-17-0, -1.7u | 25-16-0, +7.4u | 5-7-0, -2.7u | +3.1% | 0.422 | 0.89 | no / no | 12 |
| opponent on a 2+ game losing streak | 16-10-0, +5.0u | 18-6-0, +11.4u | 4-4-0, -0.4u | +25.1% | 0.030 | 0.33 | no / no | 8 |
| our side a dog off a 14+ loss | 4-9-0, -5.9u | 14-9-0, +4.1u | 3-6-0, -3.6u | -10.9% | 0.820 | 0.99 | no / no | 9 |
| our side a dog off a 14+ win | 7-1-0, +5.9u | 10-3-0, +6.7u | 5-2-0, +2.8u | +50.0% | 0.004 | 0.04 | no / yes | 7 |

**The same splits on every game (the model's side, any edge; every game as a whole goes 507-487, 523-477, 375-374, ROI -2.2%):**

| Rule | 2015-18 | 2019-22 | 2023-25 | ROI | Placebo p |
|---|---|---|---|---|---|
| our side mid vs opponent mid | 58-44-7, +9.6u | 59-46-4, +8.4u | 47-38-3, +5.2u | +7.2% | 0.03 |
| our side bottom vs opponent bottom | 56-48-5, +3.2u | 59-41-3, +13.9u | 35-30-5, +2.0u | +6.5% | 0.06 |
| our side top vs opponent top | 61-58-4, -2.8u | 59-65-3, -12.5u | 42-58-1, -21.8u | -9.8% | 0.92 |
| our side off a 14+ win | 67-76-5, -16.6u | 66-73-4, -14.3u | 58-65-3, -13.5u | -10.0% | 0.97 |
| opponent off a 14+ win | 81-85-5, -12.5u | 84-87-3, -11.7u | 58-67-1, -15.7u | -7.8% | 0.90 |
| our side the favourite, opponent a dog off a 14+ loss | 41-49-3, -12.9u | 32-39-2, -10.9u | 25-33-2, -11.3u | -14.6% | 0.97 |
| our side a dog off a 14+ loss | 68-59-1, +3.1u | 74-62-2, +5.8u | 43-60-2, -23.0u | -3.5% | 0.65 |
| second meeting this season | 91-98-3, -16.8u | 81-73-6, +0.7u | 49-45-2, -0.5u | -3.5% | 0.69 |
| division game | 193-181-10, -6.1u | 183-162-7, +4.8u | 119-116-5, -8.6u | -0.9% | 0.32 |
| BLIND: every dog off a 14+ loss | 117-100-4, +7.0u | 113-94-4, +9.6u | 76-85-4, -17.5u | -0.1% | |

Read of the every-game rows:
- The model backing a team off a big win loses on all three windows, and so does its favourite against a dog off a blowout loss. Both are about 5 to 12 points of ROI worse than every game.
- Mid-against-mid wins on all three.
- None of this touches the flag. At 4+ those spots are 0 to 18 bets a window with no steady sign. Of the 176 rules in C, 3 or 4 steady every-game patterns are what chance would hand over.

## Caveats

- **Many tests.** 176 rules in C, 161 of them with a placebo, and 17 of those at 0.05 or under. Many repeat the same few patterns (dogs, road dogs, small dogs). The bar (more units than live on all three windows, placebo passed, 40+ bets a window) is met by none.
- **Hook prices are assumed**, not read from a book. The break-even of about -133 on 3 is the useful number: buy only below it, and well below it given how much the per-window gains vary. The flag's own hook sample is small (19 to 30 bought a window).
- **Team correction** starts in 2016, because pred_v3 begins in 2015. The shrinkage k values (17, 34 and 68 games) were fixed before the run and not tuned, and all six give the same answer.
- **Streaks, off a 14+ result and rematches** use regular-season games of the same season, through the previous game (so week 1 has none). "Rematch" means the second or later meeting in one regular season.
- **Rating thirds** use only the ridge part of the model's points equation. The blend and the trees are left out, but that part tracks the full spread at 0.96.
- **Windows.** 2015-18 set no choice, 2019-22 set the 4-point cut, and 2023-25 has been used as a second test since 22 Sep. Anything found by looking at all three describes the backtest only.
- **2026** is 1-2 on the flag. Every rule's 2026 cell is in the CSV. It is too few games to move anything.
