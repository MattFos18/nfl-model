# How NFL Model 3.0 works, end to end

Everything the model does, why, and with what numbers. Written 21 September 2026. Code references are the
files in `nflmodel/`; every number below comes from `reports/`.

## 1. What is built in today, and what is not

Updated 23 Sep 2026. The model has twenty-two inputs (section 4); everything below says whether a thing is one of them.

| Thing | Status | Where |
|---|---|---|
| Recent form vs whole season | Built in. Every game is weighted by age: 0.94 per week (0.90 until 22 Sep 2026), so a game 8 weeks old counts 61% of last week's | `ratings.py` |
| Last season | Built in. Last season's games count at 0.8 weight (0.5 until 22 Sep 2026) and keep decaying; this season takes over by about Week 7 | `ratings.py` |
| Opponent strength | Built in. Ratings are solved jointly, so an offense that scored on bad defenses is marked down | `ratings.py` |
| Starting QB | Built in. The schedule names each starter; his own EPA per dropback (decayed, shrunk) is the single biggest input. When last game's starter is out and the replacement has no rating yet, a QB-out flag (about -1.7 points) applies | `ratings.py`, `model.py` |
| Offseason turnover | Built in since 23 Sep 2026 for weeks 1 to 8: the share of last season's snaps that left the roster, for the team's offense and the defense it faces | `trends.py` |
| Out of the race | Built in since 23 Sep 2026 for Week 12 on: a flag when the team's (or the opponent's) win rate through the previous week is 40% or under; the model had been overrating such teams late | `model.py` (`record_before`) |
| Injuries beyond the QB | Built in since 22 Sep 2026: the value lost to RB, WR and TE listed Out or Doubtful or on IR (own and opponent), and the share of last game's snaps now out on offense and on the defense faced. Every other position is valued on the Players tab but none of those values beat the snap shares as inputs | `players.py`, `positions.py`, `trends.py` |
| Home field | Built in as one fitted league number, about 1.9 points. Team-specific home edges were tested and made the miss worse; they are shown, not used | `model.py` |
| Dome, wind, cold, rain, warm team in the cold | Built in. Wind about -0.13 points per mph outdoors; cold under 35F; rain; a warm-climate or dome team outdoors under 35F. Forecasts are used only within 4 days of kickoff | `model.py`, `weather.py` |
| Division game | Built in since 22 Sep 2026 (about -0.7 points for each team) | `model.py` |
| Rest, short week, bye, primetime | Tested and not in: none lowered the miss on both windows once the ratings were in | `experiments/` |
| Referees, head-to-head, coach and QB against-the-spread records, off a loss, travel, time zones, snow, special teams, sack rates, pace, new coach | Tested and not in (section 14 and the decision log). Head-to-head, coaches and QBs are shown on each card as reference | `experiments/` |
| Line movement, splits, sharp money | Not in. Nothing to backtest with until the line log has a season behind it. The best available number across books is used for the flagged bet and shown on the card | `lines.py`, `picks.py` |
| Bet flag | A spread edge of 4 points or more (5 until 23 Sep 2026), no flags in Week 18, totals not flagged. Cover odds on the cards are calibrated on the backtest | `picks.py` |

## 2. The data

nflverse play-by-play, 2012 to today, every play with EPA (expected points added), success, win probability,
down, distance, yards, passer, and the drive it belonged to. The schedule file gives scores, closing spread,
total and moneylines, rest days, roof, surface, temperature, wind, starting QBs, coaches, referee and
kickoff time back to 1999. `build.py` turns the plays into one row per team per game with 140 stats
(`team_games.parquet`); `features.py` adds box-score counts (completions, sacks, red zone trips, penalties,
drive starts) and one row per passer per game.

## 3. Ratings: how a team's number is calculated

For each stat we rate (EPA per play, pass EPA per play, rush EPA per play, points scored, plays per game),
every game a team has played is one observation:

    what the offense did = league average + offense rating of the team - defense rating of the opponent + home bump + noise

with all 32 offenses and 32 defenses solved together by weighted least squares (`ratings.solve`). Three
things shape the weights:

- **Age.** Weight = 0.94 to the power of weeks ago (0.90 until 22 Sep 2026). Last week 1.0, four weeks ago
  0.78, eight weeks ago 0.61, the whole of last season 0.2 to 0.3 after the offseason multiplier.
- **Offseason reset.** Last season's games are multiplied by 0.8 on top of their age (0.5 until 22 Sep 2026),
  so a team starts the year at most of last year's rating pulled toward average, and each new game moves it.
  This is the fix for the Week 2 problem (KC at 93%).
- **Pull toward average.** A ridge penalty of 16 (in game-weight units) shrinks every rating toward zero.
  After one game a team's rating is about 6% of what that one game would say; after four games about 20%;
  by midseason the current season dominates. Defense is shrunk hardest in effect because defense stats are
  the noisiest (section 5).

The three numbers were first chosen by grid search on 2019 to 2022 points miss (`reports/tuning_ratings.csv`,
35 settings: 0.90, 0.5, 16). On 22 Sep 2026 they were re-checked under the weekly refit with the eighteen
inputs on both windows (`reports/retune.csv`, `retune2.csv`): slower decay and a heavier last season won on
both, 0.94 and 0.8 (margin miss 10.052 / 10.040 against 10.098 / 10.063; points 7.403 / 7.304 against
7.409 / 7.316), and 0.96 / 1.0 was worse again. The pull toward average (16), the QB shrinkage and the QB
decay did not move. With the regression refit every week on the season's games, the ratings can afford to
move slower: the equation carries the adaptation.

**QB rating.** For the named starter, EPA per dropback over every game he has played (any team), decayed
0.985 per game, shrunk toward -0.12 (replacement level; -0.05 until 23 Sep 2026) with a 150-dropback prior. A rookie with no
history starts at replacement level. Ablation: dropping it costs 0.08 points of miss, the most of any
input (`reports/ablation.csv`).

## 4. From ratings to points: the regression

`model.py` fits a ridge regression (penalty 10, inputs standardised) from the ratings and situation each
team carried into a game to the points it scored. Since 23 Sep 2026 the model has twenty-two inputs, each with one
plain meaning (fit on 2013 to 2025, points per one standard deviation of the input; the live coefficients are
printed on the page, Model → How it was built, and refit before every week):

| Input | Points per SD | Reading |
|---|---|---|
| Starting QB rating | +1.4 | The starter's own career EPA per dropback, decayed and shrunk toward replacement level |
| Own offense points rating | +1.3 | Points the offense scores against an average defense, opponent-adjusted |
| Opponent defense points rating | -1.3 | Points the opponent's defense allows against an average offense |
| Home | +1.0 (1.98 points home vs away) | Home teams scored 1.90 more than away teams raw, 2013 to 2025 |
| Wind (outdoor) | -0.75 (-0.135 per mph) | Offenses average 23.8 points in calm air, 21.4 at 11 to 15 mph |
| Own offense EPA per play | +0.6 | What the offense adds beyond its points rating and its QB |
| Opponent defense EPA per play | -0.4 | |
| Last game's QB listed out | -0.25 (-1.8 points when it applies) | Those games scored about 4 fewer points than the ratings said |
| Cold under 35F | -0.07 | |
| Neutral site | -0.06 | |
| Dome | +0.06 | Indoor teams score more raw (+1.5), but the ratings already know who plays indoors |
| Warm-climate or dome team outdoors under 35F | about -1.5 points when it applies | Those teams score 19.7 in the cold against 22.3 for everyone in the cold (119 team-games). Cold teams in heat show nothing. Added 22 Sep 2026 |
| Rain at kickoff | about -1 point when it applies | From the play-by-play weather text; the kickoff forecast (50%+ chance of precipitation) for unplayed games. Added from the ideas test below: -0.010 and -0.013 on the points miss in the two windows |
| Division game | -0.67 points for each team when it applies | Familiar opponents score a little less. Added 22 Sep 2026 from the both-window test (section 14): -0.006 and -0.006 on the points miss; it moves both teams alike, so the spread barely changes |
| Skill players out: value lost | -13 points per unit of EPA per play lost (a star receiver out, about 0.03, is -0.4 points) | Player model (section 15): the EPA per touch above replacement of every RB, WR and TE listed Out or Doubtful, times their touch share, summed. Added 22 Sep 2026: with the opponent's loss, -0.009 and -0.012 on the margin miss in the two windows |
| Opponent's skill players out: value lost | +36 points per unit (the same star out on the other side is +1.1 points for this team) | The same loss on the other side of the ball, in this team's own points equation |
| Offensive snaps out | negative per share of snaps missing | Sum of last game's offensive snap shares of the players now out: linemen, fullbacks, anyone the touch value cannot see. Player model phase 3, 22 Sep 2026 |
| Opponent's defensive snaps out | positive | The same sum for the opponent's defense |
| Offseason turnover, offense (weeks 1 to 8) | -4.7 per unit (a team that lost 20% of last year's snaps: -0.9 points) | 1 minus the share of last season's offensive snaps still on this week's roster. Added 23 Sep 2026 |
| Opponent's offseason turnover, defense (weeks 1 to 8) | +4.8 per unit | The same share for the defense faced |
| Out of the race (week 12 on) | about -1 point | 1 when the team's win rate through the previous week is 40% or under, from Week 12 |
| Opponent out of the race (week 12 on) | about +1 point | The same flag for the opponent |

Two expected scores per game give the spread (home minus away) and the total. The QB rating and the offense
ratings overlap (correlation 0.68) and the regression sorts that out: drop the QB and refit, and the offense EPA
coefficient rises from 0.6 to 1.4 per SD, so the credit is shared, not counted twice.

**Why twenty and not twenty-six.** Until 22 Sep the model also carried the pass and rush EPA splits, pace, the
other side of the ball (own defense and opponent offense), the opponent's QB, rest (four flags), division game and
primetime. A walk-forward test of the sets (`reports/input_set_experiments.csv`):

| Input set | Team points miss 2019-22 | 2023-25 | Margin miss 2019-22 | 2023-25 |
|---|---|---|---|---|
| Full, 26 inputs | 7.453 | 7.346 | 10.159 | 10.152 |
| Eleven inputs (now) | 7.453 | 7.373 | 10.160 | 10.131 |
| Eleven plus the other side of the ball | 7.446 | 7.360 | 10.145 | 10.141 |
| Eleven plus the rest pair | 7.455 | 7.373 | 10.164 | 10.131 |

Same accuracy to within the noise (the bootstrap interval on these misses is about 0.01), and the dropped inputs
had readings that could not be defended one at a time: the two rest flags only ever appeared together (430 of 440
short-rest games were Thursday games with both teams short), so their separate sizes were arbitrary; primetime came
out negative after the ratings although primetime teams score more raw, because good teams get those slots; pass
EPA came out negative because EPA per play already carries it. Twenty-two inputs a reader can check beats twenty-six that
score the same.

**Every idea, tested against this model** (`reports/additions.csv`, each added alone, walk-forward 2019 to 2022, change in
the team points miss; noise about ±0.01). Injuries as counts of starters out +0.004; head-to-head +0.006; coach ATS -0.005;
QB ATS +0.007; referee over rate -0.002, home-cover rate -0.004, penalties 0.000; primetime 0.000; division game -0.007
(-0.005 held out: inside the noise, not adopted); rest flags +0.013; rain -0.010 (-0.013 held out: adopted); snow +0.006;
travel distance -0.004; time-zone shift +0.001; West Coast teams at 1pm ET +0.002; the pass/rush split -0.005; pace -0.007
(+0.018 held out); opponent QB and other side of the ball +0.002. Rain is the one idea that improved the model on both
windows. Every one of these is still computed for every game and shown on the game card as a reading, with its raw
gap in the data (Model → How it was built), so the test reruns automatically as seasons accumulate.

**Ablation** on the eleven (`reports/ablation.csv`, drop one group at a time, 2019 to 2022 points miss): QB +0.063,
weather/dome +0.036, points ratings +0.026, EPA ratings +0.002, home -0.019 (dropping home lowers the miss slightly on
that window but the home coefficient is the best-established number in football, 1.9 points raw on 3,400 games each
side; it stays).

**The total has its own equation** (22 Sep 2026). Adding the two team scores gave a total that missed by 10.66 and 10.32 on the
two windows. A ridge regression fit to the game total directly, from both teams' ratings summed, the two QB ratings, QB-out
flags, wind, rain, cold and the roof, misses by 10.64 and 10.30: a small gain, but on both windows (`reports/totals_experiments.csv`).
The team scores still drive the spread and the points shown on the cards; the total shown is this equation's number, so the two
team scores do not add exactly to it. Totals are still not flagged; the new equation's 4+ edges went 77-53 then 62-56, a lead to
re-sweep after the season.

**Home field is one number.** Giving every team its own home-field term (32 inputs) made the model worse on both windows, and
a team's raw home edge in the first half of the seasons predicts its second half with a correlation of only 0.34. Arrowhead's
reputation does not survive the data: KC's raw home edge is +2.4 against a league +3.8. The matchup tool shows each team's raw
edge as a reading.

**More training years do not help.** The regression's training start was tried at 2012, 2013, 2015 and 2017; every result was
within 0.01 on both windows. The game drifts enough that seasons before about 2013 would add nothing.

## 5. Why EPA and not the old stats

`reports/lab.md`: for every stat, the correlation of a team's average through Week 8 with its points per
game in Weeks 9 to 17, averaged over 2012 to 2025 (what predicts), next to the correlation with points over
the same Weeks 1 to 8 (what the old sheet measured, which just describes).

| Stat (offense) | Predicts future points | Same-season |
|---|---|---|
| EPA per play | 0.50 | 0.86 |
| Points per game | 0.49 | 1.00 |
| Pass EPA per play | 0.49 | 0.81 |
| Success rate | 0.45 | 0.70 |
| Yards per play | 0.44 | 0.77 |
| Third down % | 0.35 | 0.60 |
| Red zone TD % | 0.19 | 0.47 |

Every same-season correlation overstates. Red zone TD rate looks like 0.47 and predicts at 0.19. The old
sheet weighted stats by the same-season numbers, so it leaned on things like red zone and Sc% that are mostly
outcomes. Garbage-time-filtered EPA predicted no better (0.46 vs 0.50), so it is not used. Defense: nothing
predicts above 0.26, which is why defense ratings are shrunk so hard and why the model's points-against
side is the weaker half.

## 6. From points to probabilities

Scores are not Poisson (the old sheet's grid gave 91% favourites that won 66% of the time). 3.0 takes the
residuals of the training games: margin error has a standard deviation of 13.1 points, total error 13.4.
The margin distribution is a normal centred on the predicted spread, then reshaped by key-number weights:
for each integer margin m, K(m) = how often real games ended at exactly m divided by how often the normal
would put them there, estimated on the training games. 3 and 7 get about 1.6 to 1.8 times their normal
share, 1 and 2 less. Win probability is the mass above zero (ties split), cover probability the mass beyond
the line with pushes taken out, over probability from the normal on the total.

Calibration held out (2023 to 2025, `reports/backtest_v3.md`): games called 55% won 57%, called 65% won
64%, called 78% won 76%. Brier 0.220 against the market's 0.210 (the old model: 0.294).

## 7. Timing: what each game is priced with

Every number used to price a game is dated before that game's week. This is the walk-forward rule and it is
mechanical, not a matter of care:

- **Ratings.** `ratings.window` takes this season's games with `week < the game's week` plus last season's games,
  nothing else. A Thursday game and the Sunday games of the same week therefore see identical ratings, through the
  previous week. Nothing from the game itself or later can enter.
- **QB rating.** The starter's dropbacks and EPA from games with `week < the game's week`, decayed. For played games the
  starter is the one who actually started (nflverse); for the coming week it is the listed starter; for later unplayed
  weeks it is the team's most recent starter carried forward (until 22 Sep the fallback for those weeks was a
  replacement-level placeholder, which is why "going into Week 4" on the Rankings tab dragged every team down; that
  affected only unplayed future weeks, never a backtest row, and the selector now stops at the next unplayed week).
- **Regression.** Refit before every week on every played game so far, this season's included, never the week being
  priced or anything after it (section 8).
- **Lines.** The closing spread and total from nflverse for played games; the current line for unplayed ones. The
  backtest is therefore "the model against the close". Live, the tracker records the line the pick was made at and
  the closing line value once the game closes.
- **Situation.** Rest, division, primetime, roof and the kickoff forecast are known before kickoff; weather for played
  games is the recorded game-time weather.
- **Forecasts are used only within 4 days of kickoff.** Open-Meteo gives a 10-day hourly forecast, but five days out
  the wind and rain numbers are too loose to move a line on, and they change by the day. So `weather.apply_to_games`
  and the rain flag take a forecast only when it was fetched within `USE_WITHIN_DAYS = 4` of kickoff; any other
  unplayed outdoor game is priced as typical weather (7 mph, not cold, dry). With runs on Tuesday, Thursday, Saturday
  and Sunday that means a Thursday game is priced with its forecast from Tuesday, and Sunday and Monday games from
  Thursday and Saturday. The card says which applies ("Forecast 2 days out" or "5 days out, weather TBD, typical
  assumed until 4 days out"). A fetch that fails is retried four times and, failing that, the game is simply priced as
  typical; the next run tries again.

`audit.py` checks the rule by force: every game from Week 10 of 2024 onward was corrupted and the earlier weeks'
numbers rebuilt; not one changed (section 10).

## 8. Learning as the season goes

The regression is refit before every week on all played games since 2013, so each week's coefficients include last
week's results (18 refits a season instead of one). Tested walk-forward against the original once-a-season refit and
against a "learn from your misses" input (each team's mean out-of-sample miss over its last 8 games, shrunk):

| Build (experiment harness, `reports/learning_experiments.csv`) | Margin miss 2019-25 | Spread flags at 5+, 2019-22 | 2023-25 | 2019-25 |
|---|---|---|---|---|
| Refit once a season (original) | 10.164 | 36-30 | 29-28 | 65-58 (52.8%) |
| Refit every week (now) | 10.161 | 36-27 | 29-27 | 65-54 (54.6%) |
| Weekly + mean-miss input | 10.169 | 37-27 | 31-28 | 68-55 (55.3%), 3+ edges worse (48.5%) |

The production build with weekly refit (`reports/backtest_v3.md`, the Results tab) grades the same rule at 64-56 (53.3%) over
2019 to 2025, 30-28 held out, and 57-46 (55.3%) with Week 18 excluded; totals at 6+ are 35-23 (60.3%), 16-7 held out. The
harness and the production grader differ by a few bets in how pushes and the season's first week are handled.

Accuracy is the same to three decimals: the ratings already carry the season's information, so the regression's
weights barely move within a year. Weekly refit is kept because it is the natural rule and costs nothing; the
mean-miss input is rejected (no accuracy gain, and the 3+ record fell). Learning is in the ratings, which update
after every game, not in a memory of past misses. (`reports/learning_experiments.csv`.)

**Why 2025 went 6-11 on flags.** The model's accuracy in 2025 was normal: margin miss 10.17 against 10.0 to 10.3 in
other seasons, Vegas at 9.74 as usual. The flags simply lost: 17 bets, and a 6-11 run has about a 17% chance under a
coin flip and 7% at the model's earlier 56% rate. Four of the eleven losses were Week 18 games, where teams rest
starters and the line knows it before the ratings do. Week 18 flags went 7-10 over 2019 to 2025 in the production build, so Week 18 is no
longer flagged (the rest of the record becomes 57-46, 55.3%). Weeks 1 to 6 are also weak (17-20) because ratings on
few games are noisy; that is not made a rule, because 37 bets cannot carry one, but it is the reason the flag
thresholds are shown with their sample sizes. The whole 5+ record is +0.9 units after 129 bets: a lead, not an edge,
and the live tracker is what settles it.

## 9. Betting thresholds: what the sweep says

**Update, 23 Sep 2026, on the twenty-two-input model (QB replacement -0.12, player model 480 touches / 10th percentile, out-of-the-race flags): the flag is 4.** Re-swept
after every change of the day (`experiments/threshold.py`, `reports/threshold_sweep.csv`, weeks 1 to 17; until the tie-out of 23 Sep the sweep's held-out column also counted the live season's games, so its earlier held-out records ran two bets larger):

| Cut | 2019-22 | 2023-25 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|---|---|
| 4 | 87-59, 59.6% | 45-21, 68.2% | 58.1% | 64.9% | 63.2% | 52.5% (21-19) | 73.3% | 74.1% | 58.3% |
| 4.5 | 65-44, 59.6% | 32-15, 68.1% | 61.5% | 65.4% | 69.0% | 42.9% (12-16) | 70.0% | 76.2% | 56.2% |
| 5 | 39-29, 57.4% | 18-12, 60.0% | 63.2% | 57.1% | 66.7% | 45.0% (9-11) | 66.7% | 69.2% | 50.0% (7-7) |

The 4-point cut is the best overall (132-80, 62.3%, across 2019 to 2025; the live record is on the Results tab), the best on both windows at every volume, and after the out-of-the-race inputs went in it clears the 52.4% break-even in every season again (2022 is the closest at 21-19). 4.5 and 5 do not (2022 at 12-16 and 9-11). The cut is not chosen on this; it was set on 22 Sep and moves only on live results, and the shadow rules log the alternatives. The earlier "wins every season"
line is withdrawn; the flag stays at 4 because it is the widest cut at the best rate, not because of a streak.
Honest caveat: the cut is chosen on all the seasons the model was tested on, so the records above describe the
backtest, not a promise; the calibrated cover odds on the cards say what a 4-point edge has converted to (about
53%). The 2026 games played so far replay 0-2 at this cut in the backtest; the live record on the Results tab is
the one that counts, since it holds what was flagged at the time.

Second caveat, and how it moved (23 Sep 2026): on the untouched 2015 to 2018 window the 4-point cut went 58-54
(51.8%) in the morning's model, under break-even, which the docs said plainly. After the day's three adoptions
(QB replacement level, player-model shrinkage, out-of-the-race flags) it reads 67-57 (54.0%) there, above
break-even, while 4.5 (41-42) and 5 (25-29) still lose. Those seasons had no say in any input, knob or cut, so
that is the most honest number the backtest can give, and it is modest. The live record (Results tab) is still
the one that decides whether the flag earns its keep.

**Update, 22 Sep 2026, on the twelve-input model.** The sweep below is from the first build and is kept for the record; the live
sweep, recomputed from the backtest on every run, is on the Results tab (Every threshold, tested). On the current model, spread
cutoffs from 4 to 5.5 make money in both windows and 5 has the best return (68-48 over 2019 to 2025; 6 and up flip negative held
out). No total cutoff makes money in both windows (6+ went 27-26), so totals are no longer flagged; the edge is still shown.

The 3 point rule was the sheet's idea, so 3.0 was swept from 0 to 7 points of disagreement with the closing
line, on all of 2019 to 2025 and on the two windows separately (spreads; totals below):

| Edge | 2019 to 2025 | 2019 to 2022 | 2023 to 2025 |
|---|---|---|---|
| 1+ | 1275 bets, 49.5%, -5.5% | 703, 50.2%, -4.1% | 572, 48.6%, -7.2% |
| 2+ | 833, 50.9%, -2.8% | 459, 52.3%, -0.2% | 374, 49.2%, -6.1% |
| 3+ | 461, 50.5%, -3.5% | 247, 50.2%, -4.2% | 214, 50.9%, -2.8% |
| 4+ | 257, 50.6%, -3.4% | 148, 51.4%, -2.0% | 109, 49.5%, -5.4% |
| 4.5+ | 182, 52.7%, +0.7% | 97, 52.6%, +0.4% | 85, 52.9%, +1.1% |
| 5+ | 127, 53.5%, +2.2% | 68, 54.4%, +3.9% | 59, 52.5%, +0.3% |
| 6+ | 61, 60.7%, +15.8% | 32, 65.6%, +25.3% | 29, 55.2%, +5.3% |
| 7+ | 37, 56.8%, +8.4% | 24, 62.5%, +19.3% | 13, 46.2%, -11.9% |

Totals: 4+ is 296 bets, 51.0%, -2.6%; 6+ is 61 bets, 60.7%, +15.8% (+12.6% then +21.5%). (These rows are from the
final build with the corrected stat definitions and the QB-out flag; the 1+, 2+, 4+ and 4.5+ rows above are from the
build before it and differ by a few bets.)

Reading: bets where the model is within 4 points of the line lose at every threshold in every window. Bets
where it disagrees by 5 or more win in both windows, and by 6 or more win big in both, but on 65 bets over
seven seasons, about nine a year. The bootstrap (2,000 resamples) puts the chance that the 5+ spread ROI is
really above zero at 69% and for 6+ at 87% (totals 6+: 93%); the plan's bar is 95%. So the display rule is now 5 for
spreads and 6 for totals (the ROI-best thresholds that hold in both windows), with the sample size printed
next to every pick, and the 3 point rule is retired. It is a lead, not a proven edge. The 5+ bets split
by side: home 52.8% on 303 bets at 3+, away 46.6% on 161; favourites and dogs the same.

**Shadow rules (23 Sep 2026).** Three rules are logged and graded alongside the 4-point flag from Week 3 of 2026
(`picks.SHADOWS`, `data/tracker/shadow45_picks.csv`, `shadowdog_picks.csv` and `shadowearly_picks.csv`, who =
shadow45 / shadowdog / shadowearly in the graded table) but never bet, and appear only as one summary line each
under "Rules compared" on the live tab: a 4.5-point cut, the 4-point cut on underdogs only, and the 4-point cut in
weeks 1 to 13 only. Their backtest records, regular season weeks 1 to 17 (`picks.rule_records`, recomputed by the
tie check on every run; the live table carries the same columns):

| Rule | 2015 to 2018 (untouched) | 2019 to 2022 (tuning) | 2023 to 2025 (held out) |
|---|---|---|---|
| 4+ edge (the flag) | 67-57 | 87-59 | 45-21 |
| 4.5+ edge | 41-42 | 65-44 | 32-15 |
| 4+ edge, model's side the underdog or pick'em | 49-36 | 78-45 | 34-17 |
| 4+ edge, weeks 1 to 13 only | 54-42 | 71-41 | 34-16 |

The underdog rule came from looking at where the flag's record lives: when the model's side is the favourite the
flag is 18-21 untouched, 9-14 tuning and 11-4 held out. The 4.5 cut has the best rate on the two tuned windows and
loses on the untouched one. All three were found on the backtest, so none is bet on the backtest: the decision
between the rules is made on the live record, with a reminder set for January 2027.

## 10. How much to trust the backtest

**What is still held out, honestly.** The ridge strength and the bet thresholds were chosen on 2019 to 2022 and
2023 to 2025 never touched them. Since 22 Sep 2026 every candidate input, and the rating decay and last-season
weight, has been accepted only when it helps on both windows. That is a stricter filter than tuning on one window,
but it means 2023 to 2025 is a second test window for those choices, not an untouched one. The live season, graded
on the Results tab, is the only fully unseen test.

`nflmodel/audit.py` (`reports/audit.md`) checks the backtest itself:

- **No leakage.** Every game from Week 10 of 2024 onward was corrupted (EPA flipped, 20 points added, QB EPA
  set to -50, results changed) and the ratings for Weeks 1 to 9 rebuilt: not one number changed. The 2024
  regression was refit with 2024-onward targets corrupted: not one prediction changed. Nothing after a game
  reaches the numbers used to predict it.
- **Same games.** 3.0 and the old model are graded on the identical 1,871 regular-season games, no
  duplicates, every one with a closing line.
- **How sure each keep/drop call is.** Each rejected input was added back to the locked model and the change
  in points miss measured with a paired bootstrap (the same games, 2,000 resamples), on both windows. The
  90% intervals are about plus or minus 0.007 points. No rejected input has an interval entirely below zero
  on both windows, and most point estimates are on the wrong side. The QB rating (+0.080 when dropped) and
  weather (+0.040) are the only inputs whose effect is larger than the interval.
- **What "no benefit" means.** No benefit the data can detect, on 2,110 tuning and 1,632 held-out team-games.
  It is not a proof of zero; no sample can give that. A benefit of 0.003 points per team, which is what a
  real but small trend would look like, is invisible here and would also be worthless to bet on.
- **Rejected ideas as bets.** Each trend was also graded as a standalone bet against the closing line (bet the
  side it favours, top or bottom quartile). All lose or sit at break-even in both windows except one: West
  Coast teams at 1pm ET on the road went 105-81 (56.5%) with the sign holding in both windows. It is logged as a
  lead and tracked live; 186 bets is not proof.

## 11. Verification

`verify.py` runs after every data rebuild (`reports/verification.md`). It checks the 2024 season totals
from play-by-play against the Pro-Football-Reference table that was pasted into your sheet, 24 stats for 32
teams: points, completions, attempts, passing yards, passing TDs, interceptions, rushing TDs, third- and
fourth-down attempts and conversions are exact for all 32; plays, turnovers and rush attempts within one;
first downs and red zone within two; drives within two (PFR has its own drive-counting rules). It also
checks that every team-game's points equal the schedule score (7,720 rows, 0 mismatches) and that what
one offense gained equals what the other defense allowed (0 mismatches). The first pass found real errors
(pass attempts counted sacks and two-point tries, return fumbles were charged to the kicking team) and they
are fixed.

## 12. The weekly loop (Phase 5)

Two GitHub Actions workflows run from `main`. **Tuesday 06:00 ET and Saturday 10:00 ET** (`weekly.yml`):
pull the season's play-by-play, schedules, injuries and snap counts; rebuild every table; run the
verification (the run halts if scores or mirrors break, and says so); fetch kickoff forecasts for unplayed
outdoor games and put them in the wind and temperature fields the model reads; rebuild ratings, trends and
the model; grade last week's flagged picks and your bets; write this week's picks with the flags; export the
data room; write `reports/weekly_latest.md` with every step's status. **Every 10 minutes** (`lines.yml`):
log the spread, total and moneyline from the ESPN scoreboard (whose provider is DraftKings) and the
DraftKings feed to `data/lines/lines_log.csv`, raw responses kept. Picks are recorded with the line at the
time and never on a game that has kicked off; when the game is graded, closing line value is the recorded
line minus the close. The splits feed (bets % vs money %) is not wired: no stable public endpoint has been
confirmed, so the report says "none" rather than inventing one.

Not automated here: republishing the page. A Claude routine on the same schedule pulls the repo and
republishes the data room with the new files and writes the recap.

## 13. What would make it a real edge

In order of what the data says: (1) bet at the opener or midweek and measure closing line value, which needs
the line log that starts in the first live week; (2) price injuries and the player model before the line
moves; (3) splits and reverse line movement after a season of logging. The first two wait on the live log; kickoff-hour
weather, the other late-priced input, was tested on 23 Sep 2026 (section 14) and did not help.

## 14. Every idea, both windows, and what was adopted (22 Sep 2026)

Until today candidate inputs were screened on the tuning window (2019 to 2022) and only the promising ones were
checked held out. Today every candidate was run on both windows with the weekly refit, on its own and then in
combination (`experiments/additions_both.py`, `experiments/combo.py`; `reports/additions_both.csv`,
`reports/combo.csv`). The rule: an input goes in only if it lowers the miss on both windows on its own and still
does with the others present. Change in the average team points miss (below zero is better; noise about ±0.005):

| Idea | 2019-22 | 2023-25 | Verdict |
|---|---|---|---|
| Division game | -0.006 | -0.006 | adopted (points; the margin is unchanged) |
| Skill players' value out, own and opponent | -0.002 | -0.006 | adopted: the margin miss falls -0.009 and -0.012 |
| Pass and rush EPA split | -0.004 | -0.015 | rejected: the points miss falls but the margin miss rises on both windows (+0.003, +0.006), and the spread is what gets bet |
| Travel distance | -0.004 | -0.002 | rejected: with the others present the margin miss moves in opposite directions on the two windows |
| Head-to-head | +0.006 | -0.008 | one window only |
| Coach ATS | -0.004 | +0.005 | one window only |
| QB ATS | +0.007 | -0.004 | one window only |
| Team home edge | +0.002 | +0.000 | nothing |
| All four matchup-history factors together | +0.014 | -0.005 | one window only, and worse than any alone |
| Referee over rate, home-cover rate, penalties | 0 / -0.004 / -0.002 | +0.004 / 0 / +0.003 | nothing consistent |
| Primetime | 0 | -0.003 | one window only |
| Pace | -0.008 | +0.018 | one window only, and badly wrong held out |
| Starters out (counts) | +0.004 | +0.002 | nothing |
| Snow, time zones, West Coast at 1pm, late slot, cold and wind team edges, home/away split, off a loss | mixed | mixed | nothing |

So the matchup-history factors on the cards (head-to-head, the coaches, the QBs, the stadium) are readings, not
inputs: each helps one window and hurts the other, which is what noise looks like.

**Is the equation itself saturated?** (`experiments/equation_checks.py`, `reports/equation_checks.csv`)

- The ridge penalty does not matter: alpha 1 to 100 moves the miss by less than 0.001.
- Interactions and squares of the five ratings: worse on the tuning window (+0.015), better held out (-0.020),
  the same split as the noisy ideas above. Not adopted.
- Gradient-boosted trees on the same inputs: worse on both windows by 0.1 points or more (7.56 vs 7.45; 7.44 vs
  7.36). The relationship is linear at the resolution this data allows, and the weights are as fitted as they get.

**In-game QB injuries** (the Giants game: Dart hurt on the first drive, the model had LA 27-24, the final was
28-6). The QB rating was never fooled: it is computed per passer from the play-by-play, so Dart's rating took his
five dropbacks and the backup's took his twenty-nine. The team offense rating did take the whole game as a Giants
reading. Down-weighting games by the named starter's share of dropbacks (`experiments/starter_share.py`,
`reports/starter_share.csv`; 189 such games of 7,722) was tested three ways: none helped on both windows (the
best, quarter weight when the starter threw under half the dropbacks, was +0.005 tuning and -0.004 held out). Not
adopted; a game with the backup is still real evidence about the offense, and the next games repair the rating.
Before kickoff no model can price a first-drive injury; that game is noise for the model and for the line alike.

**Cover odds, calibrated** (22 Sep 2026, `picks.calibration`). The model's own cover probability comes from the
bell curve around its spread, and it runs about ten points hot: at a 4 to 5 point edge it says 64% and the
backtest covered 54%, because the line carries information the model does not. The cards now show a calibrated
figure instead: a logistic curve of "the model's side covered" against the size of the edge (capped at 7), fitted
on every graded regular-season game before the current season and refit every run. On the same buckets it reads
48%, 49%, 51%, 52%, 53%, 55%, 56%, 57% for edges of 0-1 up to 7+, against actual 49%, 44%, 50%, 52%, 54%, 57%,
52%, 58% over 2019 to 2025. The same is done for the total. The raw bell-curve figure stays in the picks file.

**Bet at the best number** (22 Sep 2026, `picks.best_number`). The flag is decided on the consensus line, but
a flagged spread is written at the best available number for the model's side across the books in the latest
line snapshot, with the book named, and the tracker records that as the line bet, so closing line value is
measured against what a bettor could actually have taken. The card shows the edge at the best number when it
differs from the consensus by a quarter point or more.

**Special teams and the kicking game** (22 Sep 2026, `experiments/special_teams.py`, `reports/special_teams.csv`):
a team special-teams EPA rating (own, opponent) and the kicker's and punter's value above replacement, each added
to the eighteen-input model on both windows. Nothing helps on both: the kicker value lowers the tuning-window
miss (-0.002 points, -0.007 margin) and raises the held-out points miss (+0.007); the team rating raises the
margin miss on both windows. Not adopted; the values stay on the Players tab.

**Totals inputs re-tested** (22 Sep 2026, `experiments/totals_inputs.py`, `reports/totals_inputs.csv`): the rating
gap (a mismatch runs short), pace, and the market total itself as inputs to the totals equation, both windows.
Gap and pace: nothing (-0.000 / -0.005 and +0.012 / +0.000). The market total: 10.510 / 10.124 against the
model's 10.636 / 10.271 and the closing line's 10.541 / 10.161. That equation beats the line by 0.03 points on
both windows, but nine tenths of it is the line, and what is left to bet on is thin: over/under on the residual
at half a point or more went 432-366 (54.1%) on the tuning window and 318-289 (52.4%, exactly break-even at
-110) held out; at 2 points, 73-57 then 39-39 (`reports/totals_blend_bets.csv`). The model total on the cards
stays the model's own, so the edge shown means what it says; totals stay unflagged.

**Your bets, with your read** (`data/tracker/my_bets.csv`: game_id, bet, odds, stake, note). Graded like the
model's picks, with closing line value, on Results -> Live picks and bets; the note travels with the bet and the
card shows it, so your judgment gets a track record next to the model's.

**The line watch and GitHub's cron.** GitHub did not fire the scheduled line watch for the first five hours
after the schedule was set; its first scheduled run came at 19:58 UTC on 22 Sep 2026, which is the delay GitHub
documents for new schedules. Two fallbacks exist: the workflow also runs on any push to the branch `kick` (an
empty commit there starts a run that checks out and logs to main), and a routine bound to the build session can
dispatch the workflow directly. A routine in a fresh session cannot push or dispatch (no GitHub credentials there),
so that version is disabled. The Saturday recap reads the watch log and reports the number of snapshots, which is
the check that the schedule is holding.

**A third window nobody tuned on** (23 Sep 2026, `experiments/third_window.py`, `reports/third_window.csv`).
Every input and knob was chosen on 2019 to 2022 and checked on 2023 to 2025; 2015 to 2018 was never looked
at. On those 1,024 games (the closing line's spread miss there: 9.805):

| Model | Spread miss | Points miss | Flags at 5+ |
|---|---|---|---|
| Twenty-two inputs, today's knobs (today, evening) | 9.990 | 7.411 | 25-29 |
| Twenty inputs, decay 0.94 / last season 0.8, QB replacement -0.12 (morning of 23 Sep) | 10.010 | 7.417 | 25-30 |
| 13 inputs, today's knobs | 9.990 | 7.403 | 32-28 |
| Twenty-two inputs, original knobs 0.90 / 0.5 | 10.011 | 7.415 | 24-29 |
| 13 inputs, original knobs | 10.003 | 7.403 | 17-31 |

(Re-run 23 Sep 2026 after the QB replacement level moved; the earlier run, on eighteen inputs at -0.05, read 10.031 /
7.436 / 21-30 for today's model.) The knob change holds on the spread miss (-0.02) and the player and turnover inputs
hold there too (-0.005 against 13 inputs at today's knobs). The team points miss is worse with those inputs on this
window (+0.013), the one place the two measures disagree, and the flag records on 45 to 60 bets are noise in both
directions. The honest reading is that the spread accuracy gains carry to seasons that had no say, the points miss
does not on this window, and the flag rate is a small-sample number that will only settle live.

**Recency-weighted refit** (`experiments/recency.py`, `reports/recency.csv`): weighting older training seasons
down (0.95 to 0.7 per season) helps the tuning window and hurts held out at every setting. Equal weight stays.

**Offseason turnover** (23 Sep 2026, `experiments/continuity.py`, `continuity2.py`; `trends.continuity_table`).
Early in a season the ratings lean on last season, but the roster may not be last season's. For each team and
week: the share of last season's offensive (and defensive) snaps taken by players on this week's active roster,
from the weekly rosters and the snap counts matched by name. The inputs are 1 minus that share for weeks 1 to 8
and 0 afterwards: `off_turnover_early` for the team's own offense and `opp_def_turnover_early` for the defense it
faces. Both windows: spread miss 10.019 / 9.993 against 10.052 / 10.040, points 7.365 / 7.300 against 7.403 /
7.304; the untouched 2015 to 2018 window agrees (10.013 against 10.031). Cutoffs of 4, 6, 8, 12 weeks and all
season were tried; 8 was best held out. Fitted: about -4.7 points per unit of turnover on offense (a team that
lost 20% of last year's snaps: -0.9 points early) and +4.8 for the opponent's defensive turnover. Twenty inputs then; twenty-two since the out-of-the-race flags.

**Turnover luck** (23 Sep 2026, `experiments/luck.py`, `reports/luck.csv`). EPA per play carries every
interception and lost fumble at full weight, and turnovers are the noisiest part of football (2.1% of plays). Two
rebuilds of the offense and defense EPA ratings: per-play EPA clipped to -4 / +4, and turnover plays replaced by
the average EPA of a turnover-free play of that type. Clipping: 7.3687 / 7.3010 against 7.3694 / 7.2995 on team
points (better by 0.001 on one window, worse by 0.002 on the other). Turnover-neutral: worse on both (7.3734 /
7.3016). Neither adopted; the raw EPA ratings stay. The same run scored the 2015 to 2018 window at the new 4-point
cut: 58-54, discussed under section 9.

**Rest, surface, dead teams, ridge penalty** (23 Sep 2026, `experiments/rest_more.py`, `reports/rest_more.csv`).
Rest had been dropped before the both-windows rule existed, so it was re-run: short week / off a bye for both
teams (+0.011 / +0.002 on team points), the rest difference in days (+0.001 / -0.001), artificial turf (+0.004 /
-0.001), teams out of the race after Week 13 at a 30% win rate or under, own and opponent (+0.0005 / -0.017), the
record so far (+0.008 / -0.006), and the ridge penalty at 3, 30 and 100 against 10 (all within 0.001). Nothing
helps on both windows. The dead-team flag is the one honest maybe: a clear held-out gain the tuning window does
not show, so it is parked and gets re-checked once 2026 is in the books.

**Stake** (23 Sep 2026, `picks.kelly_stake`). Each flagged spread now carries a stake: a quarter of the Kelly
fraction, (p x b - (1 - p)) / b with p the calibrated cover odds for the model's side and b the payout at the best
book's price (-110 when no price is logged), as a share of the bankroll. A 4-point edge at 53% supports about 0.4%,
at 54% about 0.8%; the calibrated odds are refit every run, so the same edge can carry a different stake week to week. Quarter Kelly because the cover odds are an estimate from a fitted curve, and full
Kelly at an overstated edge loses money. The picks markdown has a Stake column and the card shows it as a chip.

**QB replacement level** (23 Sep 2026, `experiments/qb_replacement.py`, `qb_third.py`; `reports/qb_replacement.csv`,
`qb_third.csv`). The level a thin QB history is shrunk toward had been set by hand at -0.05 EPA per dropback.
Swept from 0.00 to -0.30 with the features rebuilt each time. Team points miss falls the lower the level goes on
the tuning window (7.377 at 0.00, 7.369 at -0.05, 7.362 at -0.12, 7.357 at -0.30) and bottoms out at -0.12 to
-0.16 held out (7.2995 at -0.05, 7.2972 at -0.12, 7.2970 at -0.16, rising again below). Totals miss falls on both
windows at every step down. The spread miss splits: better held out (9.9965 to 9.977 at -0.12) and on 2015 to 2018
(10.014 to 10.010), a shade worse on the tuning window (10.024 to 10.032). Adopted at -0.12: the conservative half
of the range where both windows improve on team points, with the third window agreeing on the spread. A backup or
rookie now starts about 0.07 EPA per dropback (roughly 2 points a game) lower than before until his own history
takes over. The threshold sweep and the third-window table below were re-run on the rebuilt model.

**QB shrinkage weight re-checked at the new level** (23 Sep 2026, `experiments/qb_k.py`, `reports/qb_k.csv`). The
150-dropback weight was tuned at -0.05. At -0.12, weights of 40 to 400: 80 is the best on team points (7.3615 /
7.2962 against 7.3624 / 7.2972) and on the spread miss, but the gain is 0.001 on each window, under the adoption
bar, and 40 to 80 are indistinguishable. 150 stays.

**Cold cutoff** (23 Sep 2026, `experiments/weather_knobs.py`, `reports/weather_knobs.csv`). The cold flag fires
under 35F, a hand-set number. 30F, 40F and 45F, and a continuous "degrees under 45F" term, are all worse on both
windows (+0.004 to +0.012 on team points). 35F stays.

**Player-model knobs** (23 Sep 2026, `experiments/player_knobs.py`, `player_third.py`; `reports/player_knobs.csv`,
`player_third.csv`). The skill-player values behind the two injury inputs were decayed 0.985 per game, shrunk with
80 touches of weight toward the 25th percentile, all set by hand. Three rounds on both windows, the skill-out
inputs rebuilt each time: every step of more shrinkage helped (160, 240, 320, 480, 640 touches: -0.001 to -0.0035
tuning, -0.002 to -0.005 held out on team points) and so did a lower replacement level (10th percentile: -0.0007 /
-0.004; 5th too far on the tuning window). The combination of 480 touches at the 10th percentile is the best that
helps both windows (-0.0025 / -0.0083; spread miss 10.023 / 9.970 against 10.032 / 9.977) and the untouched 2015 to
2018 window agrees on both measures (7.4145 / 10.007 against 7.4167 / 10.010). Adopted. What it means: a player's
own EPA per touch is mostly noise, so his value is now largely his usage times a small, well-estimated gap; a
star still counts, a hot month does not. Decay 0.97 and 0.995 were worse or flat; 0.985 stays.

**Totals with the player inputs** (23 Sep 2026, `experiments/totals_players.py`, `reports/totals_players.csv`).
With the skill-out values rebuilt, the summed skill value out, the summed offensive snaps out and the summed
offseason turnover were tried as inputs to the total equation, alone and together. Every one is worse on both
windows (+0.004 to +0.023 on the total miss). The total equation keeps its ten inputs and totals stay unflagged.

**Legitimacy tests** (23 Sep 2026, `experiments/legitimacy.py`, `reports/legitimacy.md`, re-run on every weekly
run). Four questions about the 131-87 flag record on 2019 to 2025, on the walk-forward predictions with no refit:

- *Placebo.* Shuffle the model's lines across the games of each week 2,000 times and re-grade the 4+ flags: the
  shuffled records average 51.3% with a 95th percentile of 53.2%; none of 2,000 reaches the real 60.1%. The record
  is not something the selection rule produces from noise.
- *Bootstrap.* Resampling the 218 real flags: the 90% interval for the win rate is 54.6% to 65.1%, and 1.1% of
  resamples fall under the 52.4% break-even.
- *Leave one season out.* Dropping each season in turn leaves 103-74 to 122-83; no single season carries it.
- *Encompassing.* Regress the margin on the closing line and the model's line together: the model keeps a weight
  of 0.24 with t = 1.9 over all seasons, 0.28 (t = 1.7) on the tuning window and 0.14 (t = 0.7) held out. So on
  the average game the line already holds nearly everything the model knows, and the model's extra information is
  small and not statistically firm. That squares with the rest: the line beats the model on the spread miss in
  every season, and the value sits in the tail, the games where the two disagree by 4 or more.

Honest reading: the flag record is real in the sense that noise does not produce it, and thin in the sense that
the model's edge over the market is concentrated in a few games a week and not visible on the average game. The
live record is the test that matters.

**How much history** (23 Sep 2026, `experiments/history_depth.py`, `reports/history_depth.csv`). The regression
trains on every played game from 2013. Training from 2015 instead is better on both windows (team points 7.350 /
7.287 against 7.360 / 7.289, spread 10.005 / 9.962 against 10.023 / 9.970); from 2017 is mixed. So the oldest
seasons hurt a little rather than help, and pulling 2009 to 2012 (which lack snap counts and the player model
anyway) is not worth doing. The clean version of the idea, a rolling window of the most recent N seasons, is
tested separately (`experiments/rolling_window.py`, `reports/rolling_window.csv`): the last 10, 8 or 6 seasons
instead of everything since 2013. None helps on both windows (10: equal tuning, +0.002 held out on team points;
8: +0.004 / -0.001; 6: +0.008 / +0.018). So the gain from starting in 2015 is about those two particular seasons,
not a rule, and everything since 2013 stays.

**By week of the season** (23 Sep 2026; the table lives on the Results tab and is recomputed on every run, and the
tie check compares this copy with the prediction table). On 2015 to 2025, the model's spread miss minus the line's,
the every-game cover rate on the model's side, and the 4-point flag:

| Weeks | Games | Gap to the line | Every game ATS | Flags at 4 |
|---|---|---|---|---|
| 1 | 175 | +0.02 | 53% | 18-9 (67%) |
| 2 | 176 | -0.08 | 54% | 20-5 (80%) |
| 3 | 176 | +0.13 | 53% | 15-13 (54%) |
| 4 | 171 | +0.24 | 48% | 10-6 (62%) |
| 5 to 8 | 632 | +0.19 | 51% | 48-30 (62%) |
| 9 to 13 | 793 | +0.17 | 50% | 48-36 (57%) |
| 14 to 17 | 692 | +0.24 | 51% | 40-38 (51%) |
| 18 | 80 | +0.47 | 54% | 9-10 (47%) |
| Playoffs | 133 | +0.22 | 48% | 10-7 (59%) |

The intuition that the early weeks are the weak spot is wrong: Weeks 1 to 3 are where the model is closest to the
line (in Week 2 it is ahead of it) and where the flag has done best (53-27). The market seems to underweight last
season's ratings early, and the model leans on them. The weak stretch is late: Weeks 14 to 17 are the only span
where the flag sits under break-even (40-38, 51%; it was 34-39 before the out-of-the-race inputs went in on 23 Sep
2026), and Week 18 is worse still (9-10, the largest gap, and the model's disagreements with the line are widest
there, 3.1 points against 2.1). Week 18 is already skipped. The late-season slide is why the out-of-the-race inputs
get the January re-test with 2026 in the held-out window. The playoffs are 133 games; the model sits 0.22 behind
the line and the flag is 10-7 on seventeen bets, too few to mean anything, and playoff games are not flagged.

**A second model family** (23 Sep 2026, `experiments/gbm.py`, `reports/gbm.csv`). Gradient-boosted trees on the same
twenty inputs, refit before each season, against ridge refit the same way. Trees lose clearly on both windows at
every depth tried (team points 7.42 to 7.46 against ridge's 7.375 on the tuning window; 7.36 against 7.294 held
out; spread miss 0.1 to 0.2 worse). The linear equation is not leaving interactions on the table that a tree can
find with this much data. Ridge stays.

**Late season** (23 Sep 2026, `experiments/late_season.py`, `reports/late_season.csv`; `late_third.py`). Weeks 14
to 17 are the only stretch where the flag loses, and the model overrates teams out of the race late (about a
point kinder than the line to a team with a 30% record). Candidates: a dead-team input (win rate through the
previous week at or under 30% or 40%, from week 12 or 14, own and opponent), the record interacted with the late
season, a plain late flag. The plain flag and the 30% cuts help held out only. From week 12 at a 40% win rate helps
both windows (-0.0012 / -0.0026 on team points), narrowly, and the untouched 2015 to 2018 window agrees on every
measure (team points 7.4108 against 7.4145, spread miss 9.990 against 10.007, flags 67-57 against 62-59, the late
flags 13-15 against 10-15). Adopted as inputs 21 and 22: `dead_late` and `opp_dead_late`, 1 from Week 12 on when
the team's (or the opponent's) win rate through the previous week is 40% or under. Twenty-two inputs.

**The market as an input, side by side** (23 Sep 2026, `experiments/market_blend.py`, `reports/market_blend.csv`).
The line's implied points for each team added as a twenty-first input, walk-forward on both windows:

| Model | Team points, 2019-22 | Team points, 2023-25 | Spread miss, 2019-22 | Spread miss, 2023-25 |
|---|---|---|---|---|
| Pure model (today) | 7.360 | 7.289 | 10.023 | 9.970 |
| The line alone | 7.291 | 7.213 | 9.891 | 9.747 |
| Model + the line | 7.248 | 7.182 | 9.894 | 9.712 |

Two readings. First, the model carries information the line does not: model plus line beats the line alone by
0.04 on team points and by 0.03 on the held-out spread miss, which is the same finding as the encompassing test
above, now in points. Second, a blended model flags nothing: with the line inside it, it never disagrees with the
line by 4 points, so the flag would not exist. That is why the blend is not adopted and stays a side-by-side
number: the pure model is the one that can disagree, and the flag lives in its disagreements.

**The QB with sacks taken out** (23 Sep 2026, `experiments/qb_detail.py`, `reports/qb_detail.csv`). The QB rating
rebuilt on non-sack dropbacks only (EPA per non-sack dropback), so it measures throwing and scrambling rather
than protection. Tuning window better on team points (7.346 against 7.360), held out worse (7.294 against 7.289);
the held-out spread miss better (9.939 against 9.970), the tuning spread flat. Helps one window only; not adopted.
The QB stays one number, EPA per dropback with sacks included.

**Which games a player's usage is measured on** (23 Sep 2026, `experiments/usage_window.py`, `usage_gate.py`;
`reports/usage_window.csv`, `usage_gate.csv`). A skill player listed out is taken off his team at his value times his
share of the team's touches over his own last eight games, on any team. A.J. Brown, traded to New England and on
IR in Week 3 of 2026 after one game there, was taken off a team whose ratings had barely seen him. Two principled
windows were tried: the team's last eight games, and the window the ratings themselves use (this season and last,
0.94 per week of age, last season at 0.8), counting only his touches for that team. Both are worse on both windows
(team points 7.366 / 7.291 and 7.360 / 7.289 against 7.359 / 7.286; the flag 85-62 / 46-32 and 88-60 / 44-32 against
92-63 / 49-27): how a player was used, wherever he was, predicts the cost of his absence better than a pro-rated
share does. A gate on the same idea was then tried, keeping the original usage but taking nothing off for a player under a share
of the ratings window: a quarter and a half are worse on both windows; skipping only a player who has never played
for the team is 7.355 / 7.289 on team points (inside the noise) but costs the flag on every window in a full rebuild
(82-57 / 45-22 / 66-60 against 87-59 / 45-21 / 67-57). So the original usage stays, Brown's deduction included: the
cost of a player's absence follows the player, not the team's history with him. The code for the three windows is
kept (`players.TEAM_WINDOW`) for a re-test when more traded-and-out cases exist, and the other half of the trade
question, crediting a team for a player its ratings have not seen (`players.roster_delta`), is written and untested.

**Scheme inputs for the game model** (23 Sep 2026, `experiments/scheme_inputs.py`, `reports/scheme_inputs.csv`).
The first question of the matchup work is whether scheme moves the score. Candidates as of each game from the
team's and the opponent's previous 17 charted games: three matchup fits (the offense's EPA in the mix the
opponent plays, against its own passing average: coverage man/zone, pressure, blitz) and six raw tendencies (pass
rate over expected, motion, play action; the opponent's man, pressure and blitz rates), each added alone and in
groups to the twenty-two inputs, both windows. Nothing helps both: the coverage fit is flat (0.000 / +0.0006), the
blitz fit and the opponent's pressure rate each help one window (blitz fit +0.0013 / -0.0019; pressure rate +0.0027
/ -0.0081), the tendencies hurt (motion +0.013 / +0.011, all six together +0.025 / +0.011). The ratings already
carry what a team's scheme has produced; the scheme tags say how, not how much. Nothing adopted; the profiles stay
readings, and the next layers (player against scheme, player against player) are built for the props side first.

Two follow-ups (`experiments/scheme_qb_totals.py`, `reports/scheme_qb_totals.csv`). The QB, not the team, is the one
under pressure, so each starter's own EPA per dropback under pressure and in a clean pocket (league -0.19 and
+0.22), and blitzed and not, was decayed and shrunk like the QB rating and matched to the opponent's pressure and
blitz rates: the pressure fit is +0.002 / +0.003 on team points, the blitz fit +0.002 / -0.001, the pressure gap
(how much pressure hurts him) +0.004 / +0.007; nothing helps both. For the total, tempo and tendency sums
(no-huddle, pass rate over expected, motion, the two defenses' pressure and man rates) were added to the totals
equation: no-huddle -0.001 / +0.008, pass rate over expected 0 / 0, the rest worse, all five together +0.11 /
+0.08. Nothing adopted. A third idea, adjusting each offense's EPA for the looks it faced before the ratings solve,
was not run: the joint solve already credits the look to the defense that chose it, so the adjustment would move
that credit from the defense to the offense and count it twice. Last, the absence input read against the matchup
(`experiments/skill_out_matchup.py`, `reports/skill_out_matchup.csv`): each listed-out receiver's value scaled by
his yards per target in the opponent's man/zone mix against his own average (capped at a quarter to double).
0.000 / 0.000 on team points: few absent players have 15 targets against both looks in their window, and the
scaling moves little. Not adopted; the card's projection view (section 18) is where the matchup shows.

**Kickoff-hour weather for the backtest** (23 Sep 2026, `nflmodel/weather_archive.py`, `experiments/weather_kickoff.py`,
`reports/weather_kickoff.csv`). The backtest's wind, cold and rain come from the schedule's game-day readings. The
Open-Meteo archive gives the reading at the kickoff hour at each stadium (2,572 outdoor games 2013 to 2025 in
`data/weather/archive_kickoff.csv`; temperature agrees with the schedule at 0.97, wind at 0.68). Rebuilding the
three weather inputs from the archive is worse on both windows: team points 7.376 against 7.359 tuning and 7.287
against 7.286 held out; the spread miss flat and 9.957 against 9.949. Not adopted; the schedule readings stay,
and the live forecast keeps filling unplayed games within four days of kickoff. The archive is kept for re-tests.

## 15. The player model

Phase 1 (`nflmodel/players.py`, `data/processed/player_games.parquet`): one row per game, team, player and role
(passer, rusher, receiver) from the play-by-play since 2013, with plays and EPA; about 95,000 rows, 2,400 players.
`PlayerValues` gives any player a decayed (0.985 per game), shrunk (k = 480 touches; 80 until 23 Sep 2026) EPA per play as of a week,
toward a replacement level set at the 10th percentile (25th until 23 Sep 2026) of players with 100+ plays in earlier seasons.

Phase 2 (`injury_value`, `data/processed/player_injury.parquet`): for each game and team, the value lost to RB, WR
and TE listed Out or Doubtful on the final report: value above replacement times the player's usage share, summed.
Usage is the player's own share of his team's touches over his last eight games on any team, so a star who changed
teams in the offseason (A.J. Brown to New England, valued 0.045 EPA per team play above replacement from his
Eagles games) counts in full if he is listed out, even before he has played for the new team. A player the
play-by-play has never seen counts as nothing, which is right: there is no evidence he is above replacement.
Players on injured reserve are not on the weekly injury report, so the weekly rosters (nflverse, pulled with the
rest) supply them: a roster status of reserve/IR, PUP, suspended, exempt, non-football injury or retired for that
week counts the player as out, in the player model and in the starter and QB flags alike. Game-day inactives are
not used: they are known only ninety minutes before kickoff, so using them in the backtest would be cheating.

**How a player's impact is rated.** Each rusher or receiver has an EPA per touch: the average EPA of the plays he
carried or was targeted on, decayed 0.985 per game and shrunk toward replacement level with 480 touches of weight (80 until 23 Sep 2026)
(a rookie with 20 touches is mostly the prior; a veteran with 300 is mostly himself). Replacement level is the 25th
percentile of players with 100+ touches in earlier seasons, about 0.05 EPA per touch for receivers and -0.1 for
rushers. The player's value is (EPA per touch minus replacement) times his share of the team's touches, in EPA per
team play; a star receiver with 20% of the touches at 0.35 EPA per target is about 0.06. The model's fitted weight
(about -13 points per unit) turns that into points: about 0.8 points off the team's expected score when he sits.
Team -> Players lists every skill player with these numbers and this week's injury status; a card names who is out
under "Injuries beyond the QB". In the model since 22 Sep 2026, own and opponent
(`experiments/player_injury.py`, `reports/player_injury.csv`): margin miss 10.152 to 10.143 (2019-22) and 10.117
to 10.105 (2023-25). Small, but the same sign on both windows and larger than any situational input added this
year. The QB stays on its own flag (`qb_out`), which already carries the biggest injury effect.

Phase 3 (22 Sep 2026, `experiments/line_defense.py`, `experiments/snap_pair.py`): the line and the defense.
EPA does not attribute to linemen or defenders, so the handle is snaps: from the team's previous game, the sum of
the snap shares of every player now out (Out or Doubtful on the report, or IR, PUP, suspended or exempt on the
roster). Tested on both windows against the sixteen-input model:

| Input | Points 2019-22 | Margin 2019-22 | Points 2023-25 | Margin 2023-25 | Verdict |
|---|---|---|---|---|---|
| Own offensive-line starters out (count) | +0.001 | -0.004 | 0.000 | 0.000 | nothing |
| Own offensive snaps out | 0.000 | -0.008 | -0.001 | -0.004 | margin only |
| Opponent offensive-line starters out | -0.004 | -0.008 | +0.001 | -0.001 | mixed |
| Opponent defensive snaps out | -0.006 | -0.001 | -0.013 | -0.002 | points only |
| Own offensive snaps out + opponent defensive snaps out | -0.008 | -0.010 | -0.015 | -0.009 | adopted |
| The pair + the line count | -0.009 | -0.011 | -0.014 | -0.007 | the count adds nothing |

So the model had eighteen inputs at that point (twenty since the offseason turnover pair): the pair went in (flags 48-40 and 29-18 against 42-35 and 28-19 without).
The offensive line is inside "offensive snaps out" (a lineman at 100% of snaps counts a full share); a separate
line count added nothing once the snap share was there. The defense is covered the same way from the other side.

Still open: a full availability-weighted offense rating (every player's value times expected usage, rather than
only the ones listed out), and a defensive player value that would need a different attribution than EPA. Each is
a test like the ones above, and nothing goes in unless it helps on both windows.

**Phase 4: every position valued** (22 Sep 2026, `nflmodel/positions.py`, `data/processed/player_values_all.parquet`).
Nobody outside the skill positions has a play attributed to him in the play-by-play, so each unit gets the handle
the data allows, always the same shape: a decayed, shrunk rate per play as of a week, replacement level at the 25th
percentile of regulars in earlier seasons, and a value above replacement times the player's share of his unit's
plays, in EPA per team play.

| Unit | Rate | Plays | Share |
|---|---|---|---|
| QB | EPA per dropback (the QB rating, `ratings.QBRatings`) | dropbacks | one starter, so none |
| RB, WR, TE | EPA per carry or target (phase 1) | touches | share of the team's touches, last eight games on any team (a player traded in keeps the usage he had; the alternatives lost on every window, section 14) |
| Offensive line | on/off: team EPA per play in games he played 50%+ of the snaps minus the team's games without him, last 34 games, shrunk by the smaller side's games | games | snap share |
| Defense | impact plays: the EPA taken away on every play he is credited on (tackle 1, assist 0.5, tackle for loss +0.5, sack 1, QB hit 0.5, pass defended 1, interception 1, forced or recovered fumble 0.5; one credit per play at most), per defensive snap; decayed 0.99, shrunk with 300 snaps; replacement level per position group (DL, LB, DB) since 23 Sep 2026, because a corner is credited mostly on tackles after catches and a lineman on stops, so one pooled level ranked every corner below every lineman. Coverage that keeps the ball away is not a credited play, so the page also shows each defender's coverage line from Pro Football Reference's advanced defense table (nflverse `pfr_advstats`, 2018 on; targets, catch rate, yards per target, passer rating allowed and yards saved per game against the league's yards per target, over his last eight games), and the team overview ranks defensive backs on it | defensive snaps (snap counts, matched by name) | snap share |
| K, P | EPA per kick (field goals and extra points), EPA per punt | kicks, punts | one |

What each handle can and cannot see. The skill value is the cleanest: the play is his. The QB rating has been in
the model from the start. The defensive value rewards players who end plays and take the ball away, per snap, so
an edge rusher with sacks and a corner with interceptions rank high; a corner who is never thrown at ranks low,
which is the known blind spot of any credit-based defensive stat. The line value is the weakest: on/off at the
game level is noisy and a lineman who never misses a game sits at zero because the data cannot separate him from
his line. Values compare within a unit, never across.

**Phase 4 as model inputs** (`experiments/positions.py`, `reports/positions.csv`): each new value was tried on
both windows against the eighteen-input model. The opponent's defenders' value out: +0.003 / -0.005 on points,
+0.007 / -0.009 on the margin, one window each way. Own defenders: nothing. Linemen's on/off out, own or
opponent: nothing or worse. The availability-weighted skill offense (every regular who is playing): margin
-0.006 / -0.003 but points +0.001 / +0.005, and replacing the value-out input with it is worse on both windows.
None adopted. The snap-weighted absences already carry what the line and the defense lose; a value per defender
adds noise on top. The values stay on the page as readings, and the tests are printed under Inputs explained.

**Where the player data lives on the page.** Players (top tab): every skill player league-wide, ranked by value
above replacement, with a search, team and position filters, this week's status, and a click-through to his
history by season and team (raw play-by-play totals, so a trade shows as a new team row with the same player).
Team -> Roster and depth chart: this week's roster, the latest depth chart by slot and rank, the injury report with
practice status and the injury, last game's snap share, and the value for skill players, with everyone the model
prices as unavailable listed at the top. Team -> Players: every unit for that team, grouped, with the handle named. Teams -> Overview: record, power
and ratings with ranks, the next game with the model's line, the last five, who is out, and the most valuable
players by unit. The tabs are This week, Rankings, Teams, Players, Results (the backtest and the live picks and
bets) and Model (how it was built, the inputs, how a rating is built for any team, every column, data pulls,
the decision log, definitions and sources).

Neither the division flag nor the value out helps the totals equation (`reports/totals_div.csv`), so that stays as it was. The weekly run builds all of this (`players` step after `trends`); the card shows the value out under "Injuries
beyond the QB" in the breakdown.


## 16. Weekly audit (23 Sep 2026)

Every Monday at 9am ET, `.github/workflows/health.yml` ("weekly audit") runs `nflmodel/audit_weekly.py`, which is
everything a program can check about the site and the model, in one report with one result
(`reports/weekly_audit.md`):

1. **Health** (`nflmodel/health.py`, 19 rows): the weekly run is under 72 hours old with every step ok (verify,
   both tie-out steps, the export and the pick recording among them); at least three runs in the last seven days;
   the line watch logged a snapshot in the last 24 hours and is returning rows; kickoff forecasts under 96 hours
   old; the coming week has a picks file and the tracker holds the same flags; the page quotes the code's flag
   threshold, inputs and QB replacement level and was built in the last 96 hours.
2. **Data verification** (`nflmodel/verify.py`): team points equal the schedule scores, what one offense gained
   equals what the other defense allowed, 2024 totals against Pro-Football-Reference, known results.
3. **Tie-out** (`nflmodel/tie_check.py`, 26 rows): every headline number recomputed from the prediction table and
   compared with the README, the threshold sweep, the docs' threshold table, the picks file, the tracker and the
   page's data files.
4. **Leak test** (`nflmodel/audit.py`): every future game corrupted; no rating or prediction before the cut may move.
5. **Page JavaScript parses** and **every page data file parses**.
6. **Chromium walk** (`tools/page_walk.js`): every tab and sub-view rendered; no console or page errors, no
   "undefined" or "NaN" text, nothing empty.

When any section fails the workflow opens a GitHub issue labelled `health` with the report (or comments on the
open one) and goes red; when everything passes again it closes the issue. The report is committed to main with
the issue and run links at the bottom and sits first on Model → Data pulls and verification. At 9:45am ET a
Claude routine reads it and sends a one-line push and email: clean, or exactly what failed and the likely fix.
The same audit runs locally with `python -m nflmodel.audit_weekly` (about 30 seconds).

## 17. Scheme and play-calling profiles (23 Sep 2026)

The first layer of the matchup work: how each team plays and how it has gone, from what the participation data
and FTN charting say about every play since 2016 (`nflmodel/scheme.py`, `data/processed/scheme_plays.parquet`,
`scheme_profiles.json`, `web/data/scheme.js`).

**Sources.** nflverse participation (2016 on): the defense's man or zone call and coverage family (Cover 0 to 9,
2-man, combo), offensive formation and personnel, defenders in the box, pass rushers, pressure, time to throw, and
the eleven players on the field for each side. FTN charting (2022 on): motion, play action, RPO, screens, no-huddle,
QB location, blitzers, rushers, box count, catchable and contested throws, drops. Both join the play-by-play on the
game and play id; EPA, down, distance and win probability come from the play-by-play. The current season's
participation file appears on nflverse during the season; until it does, the current-season profile carries the
FTN fields (motion, play action, blitz, box) and leaves the coverage and pressure fields blank rather than guessing.

**What a profile holds.** Offense: pass rate and pass rate in neutral situations (win probability 20 to 80%, first
and second down), pass rate over expected, shotgun, motion, play action (of dropbacks), RPO, screens, no-huddle,
time to throw, personnel mix (11, 12, 21 and so on: running backs then tight ends), and EPA per play overall, on
passes, on runs, and in each look faced: man, zone, each coverage family, blitz, no blitz, pressure, clean pocket,
play action, motion, light box (6 or fewer on runs), heavy box (8 or more). Defense: man and zone shares, coverage
family shares, blitz rate (five or more rushers), pressure rate, average rushers, box on runs and heavy-box rate,
nickel and dime shares, and EPA allowed in the same looks. Every EPA figure carries its play count and is blank
under 20 plays. League baselines for the same season sit beside each number.

**As-of rule.** A profile as of Week N uses this season's games before Week N and last season in full; nothing
from Week N or later. The tie check confirms the built profiles are as of the current week.

**Where it shows.** Team -> Overview: "How they play" and "How they defend", the current season when it has 300
plays, otherwise last season, labelled. Each game card: "Scheme matchup", the away offense against the home
defense and the reverse, look by look: what the offense has done in it, what the defense has allowed in it, and
how often the defense uses it. These are readings. None of it is a model input; the by-look numbers are the raw
material for the next layers (player against scheme, player against player), each to be tested on both windows
before it can move a line.

## 18. Player against scheme, matchup projections, props track record (23 Sep 2026)

The second layer of the matchup work (`nflmodel/props.py`, `data/processed/props.json`, `web/data/props.js`,
`reports/props_<season>_wk<week>.csv`, `data/tracker/props_graded.csv`).

**Player profiles.** From the tagged plays, each QB, receiver and rusher over his last 17 games on any team:
volume (dropbacks, targets or carries per game and his share of his team's), yards and EPA per touch, catch rate,
depth of target, touchdown rate, and the same split by the looks he faced: receivers against man and zone, blitz
and pressure; rushers into light (6 or fewer), seven-man and heavy (8+) boxes; QBs under pressure and clean,
blitzed and not, against man and zone. A split shows only with 15 plays in it.

**Defense profiles.** Each defense over its last 17 games: yards, EPA and catch rate allowed per target, yards and
EPA allowed per carry and per dropback, and its mix: man rate, pressure rate, blitz rate, heavy- and light-box rates.

**Projection for a game.** Volume: the team's pass plays (or runs, or dropbacks) per game over its last 17, shared
out among the players who are playing in proportion to their usage, so a listed-out player's targets go to his
teammates rather than vanishing, and the team's targets add up to 97% of its pass plays (the rest are throwaways).
Rate: the player's yards per touch shrunk toward the league's with a fixed weight of touches (receivers 100 targets,
rushers 25 carries, QBs 50 dropbacks), then moved part of the way toward what that defense allows per touch
relative to the league (receivers and rushers a quarter, QBs half). Yards = volume x rate; touchdowns = volume x his
touchdown rate. The look-by-look splits are shown beside the projection as readings and do not enter it.

**Why that rule** (`experiments/props_backtest.py`, `reports/props_backtest.csv`; walk-forward 2019 to 2025, every
player-game with a touch, projected from the previous 17 games of the player, his team and the opponent; mean
absolute error in yards per player-game, tuning window / held out):

| Receiving yards | 2019-22 | 2023-25 |
|---|---|---|
| League average per target x his volume | 20.06 | 19.07 |
| His own rate x volume | 20.21 | 19.30 |
| His man/zone split weighted by the defense's man rate (the first version) | 20.28 | 19.33 |
| That, moved half way toward the defense (the first version on the page) | 20.28 | 19.28 |
| His rate shrunk toward the league (100 targets), moved a quarter toward the defense (adopted) | 19.81 | 18.85 |

| Rushing yards | 2019-22 | 2023-25 |
|---|---|---|
| His own rate x volume | 19.33 | 18.64 |
| His light/heavy box split weighted by the defense's heavy-box rate | 19.80 | 18.98 |
| Shrunk (25 carries), moved a quarter toward the defense (adopted) | 19.24 | 18.51 |

| Passing yards | 2019-22 | 2023-25 |
|---|---|---|
| His own rate x volume | 62.96 | 62.65 |
| His pressure/clean split weighted by the defense's pressure rate | 73.28 | 65.50 |
| Shrunk (50 dropbacks), moved half way toward the defense (adopted) | 62.31 | 62.45 |

The splits are too noisy at fifteen to seventeen games to project with: every look-weighted version is worse than
the player's plain rate, and for receivers the league average per target beats the player's own rate outright,
which is why the shrinkage weight is heavy. Volume from usage share beats his plain targets per game by a hair
(1.91 against 1.92 targets of error). The defense adjustment is worth a tenth of a yard or so. A projection that is
20 yards off on average on a receiving line is a weak instrument; the live record will say whether it is worth
anything against a market line, once those are logged.

**Absences.** A listed-out player still shows on the card with what he would have projected against this defense,
so the size of the loss in this matchup is visible, and his volume is redistributed as above. The game model's
own absence inputs are unchanged by this (section 15); a matchup-adjusted version is tested in section 14.

**Track record.** Every projection is written to the week's props file at each run; on the next run every earlier
week's projections are graded against the players' actual yards from the play-by-play (receiving, rushing, passing),
with the error kept per player and stat in `data/tracker/props_graded.csv`, and the mean absolute error and bias
by stat shown on the cards. Nothing is compared with a market line yet: player prop lines are not logged. The
projections are readings until the record says otherwise.

