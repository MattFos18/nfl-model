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

Scores are not Poisson (the old sheet's grid gave 91% favorites that won 66% of the time). 3.0 takes the
residuals of the training games: margin error has a standard deviation of 13.1 points, total error 13.4.
The margin distribution is a normal centered on the predicted spread, then reshaped by key-number weights:
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

<!-- auto:threshold -->
| Cut | 2019-22 | 2023-25 | 2015-18 (untouched) | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|---|---|---|
| 4 | 80-51, 61.1% | 40-21, 65.6% | 68-55, 55.3% | 66.7% | 72.7% | 64.3% | 41.2% (14-20) | 66.7% | 70.0% | 59.1% |
| 4.5 | 52-37, 58.4% | 25-15, 62.5% | 43-36, 54.4% | 58.3% | 68.2% | 68.4% | 41.7% (10-14) | 66.7% | 63.2% | 60.0% |
| 5 | 36-28, 56.2% | 16-6, 72.7% | 29-24, 54.7% | 60.0% | 64.7% | 64.3% | 38.9% (7-11) | 75.0% (3-1) | 85.7% | 63.6% |
<!-- /auto:threshold -->

**24 Sep 2026, after the QB rating began counting scrambles and designed runs and fading 0.8 per season:** the flag stays at 4. Across 2019 to 2025 it is 123-78 (61.2%). 4.5 is 83-50 (62.4%): a little better on both windows (60.4% and 66.7% against 59.1% and 66.1%) at two thirds of the volume, and worse on the untouched 2015 to 2018 (39-40 against 61-59). The cut was set on 22 Sep and moves only on live results, not on a backtest this close; the 4.5 shadow rule logs it live. Counting scrambles and designed runs alone made every window's flag record a little worse (docs section 25); the season fade then made it better on both windows.
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

Third caveat (24 Sep 2026): on the current model the untouched window sits near the 52.4% break-even at the
4-point cut (the table above, rewritten from the backtest on every run). The model is more accurate there than
before (docs section 25); its flag record there is not, and that is reported rather than tuned away.

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
by side: home 52.8% on 303 bets at 3+, away 46.6% on 161; favorites and dogs the same.

**Shadow rules (23 Sep 2026).** Three rules are logged and graded alongside the 4-point flag from Week 3 of 2026
(`picks.SHADOWS`, `data/tracker/shadow45_picks.csv`, `shadowdog_picks.csv` and `shadowearly_picks.csv`, who =
shadow45 / shadowdog / shadowearly in the graded table) but never bet, and appear only as one summary line each
under "Rules compared" on the live tab: a 4.5-point cut, the 4-point cut on underdogs only, and the 4-point cut in
weeks 1 to 13 only. Their backtest records, regular season weeks 1 to 17 (`picks.rule_records`, recomputed by the
tie check on every run; the live table carries the same columns):

<!-- auto:rules -->
| Rule | 2015 to 2018 (untouched) | 2019 to 2022 (tuning) | 2023 to 2025 (held out) |
|---|---|---|---|
| 4+ edge (the flag) | 68-55 | 80-51 | 40-21 |
| 4.5+ edge | 43-36 | 52-37 | 25-15 |
| 4+ edge, model's side the underdog or pick'em | 50-38 | 73-42 | 32-18 |
| 4+ edge, weeks 1 to 13 only | 54-41 | 68-37 | 33-16 |
| boosted trees alone, 5+ edge | 94-67 | 84-61 | 33-18 |
| Under, 55%+ chance (the totals flag) | 145-124 | 190-146 | 76-62 |
<!-- /auto:rules -->

The underdog rule came from looking at where the flag's record lives: when the model's side is the favorite the
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

<!-- auto:byweek -->
| Weeks | Games | Gap to the line | Every game ATS | Flags at 4 |
|---|---|---|---|---|
| 1 | 175 | -0.01 | 53% | 18-9 (67%) |
| 2 | 176 | -0.14 | 59% | 17-7 (71%) |
| 3 | 176 | +0.08 | 53% | 14-8 (64%) |
| 4 | 171 | +0.24 | 51% | 12-5 (71%) |
| 5 to 8 | 632 | +0.14 | 51% | 43-32 (57%) |
| 9 to 13 | 793 | +0.16 | 49% | 51-33 (61%) |
| 14 to 17 | 692 | +0.19 | 51% | 33-33 (50%) |
| 18 | 80 | +0.50 | 59% | 7-8 (47%) |
| Playoffs | 133 | +0.29 | 47% | 6-5 (55%) |
<!-- /auto:byweek -->

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

When any section fails the workflow opens a GitHub issue labeled `health` with the report (or comments on the
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
plays, otherwise last season, labeled. Each game card: "Scheme matchup", the away offense against the home
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

**Projection for a game.** Volume: the team's pass plays (or runs, or dropbacks) per game over its last 17,
moved by the game script (a line fitted on 2016 to 2018 to the closing spread and total: a team's pass plays run
-0.60 -0.046 x its expected margin +0.164 x (total -43.57), its runs +0.34 +0.103 x margin -0.171 x (total -43.57),
dropbacks the same as pass plays; favorites run more and pass less, high totals add pass plays), then shared out
among the players who are playing in proportion to their usage share, where usage is his plays over his team's in
the games he played, both decayed 0.85 per game back from his most recent game (a player traded in keeps the usage
he had elsewhere; the current role counts most). A listed-out player's targets go to his teammates rather than
vanishing, and the team's targets add up to 97% of its pass plays (the rest are throwaways). Rate: the player's
yards per touch shrunk toward the league's with a fixed weight of touches (receivers 100 targets, rushers 25
carries, QBs 50 dropbacks), then moved part of the way toward what that defense allows per touch relative to the
league (receivers and rushers a quarter, QBs half). Line: volume x rate x a median factor (receivers 0.88, rushers
0.84, QBs 0.90), fitted on 2016 to 2018 as the multiplier that minimizes absolute error: yards in a game are
right-skewed (a few long plays, many quiet games), so the line that is off by least sits below the mean, which is
where a book sets an over/under. The mean sits in the cell's tooltip; touchdowns = volume x his touchdown rate. The
look-by-look splits are shown beside the projection as readings and do not enter it.

**Why that rule: round one** (`experiments/props_backtest.py`, `reports/props_backtest.csv`; walk-forward 2019 to
2025, every player-game with a touch, projected from the previous 17 games of the player, his team and the opponent;
mean absolute error in yards per player-game, tuning window / held out):

| Receiving yards | 2019-22 | 2023-25 |
|---|---|---|
| League average per target x his volume | 20.06 | 19.07 |
| His own rate x volume | 20.21 | 19.30 |
| His man/zone split weighted by the defense's man rate (the first version) | 20.28 | 19.33 |
| That, moved half way toward the defense (the first version on the page) | 20.28 | 19.28 |
| His rate shrunk toward the league (100 targets), moved a quarter toward the defense (round one's pick) | 19.81 | 18.85 |

| Rushing yards | 2019-22 | 2023-25 |
|---|---|---|
| His own rate x volume | 19.33 | 18.64 |
| His light/heavy box split weighted by the defense's heavy-box rate | 19.80 | 18.98 |
| Shrunk (25 carries), moved a quarter toward the defense (round one's pick) | 19.24 | 18.51 |

| Passing yards | 2019-22 | 2023-25 |
|---|---|---|
| His own rate x volume | 62.96 | 62.65 |
| His pressure/clean split weighted by the defense's pressure rate | 73.28 | 65.50 |
| Shrunk (50 dropbacks), moved half way toward the defense (round one's pick) | 62.31 | 62.45 |

The splits are too noisy at fifteen to seventeen games to project with: every look-weighted version is worse than
the player's plain rate, and for receivers the league average per target beats the player's own rate outright,
which is why the shrinkage weight is heavy. Volume from usage share beats his plain targets per game by a hair
(1.91 against 1.92 targets of error). The defense adjustment is worth a tenth of a yard or so.

**Round two** (`experiments/props_backtest2.py`, `reports/props_backtest2.csv`): how books and projection shops
build a prop line, read and tested one layer at a time on receiving yards, each added to round one's rule. The
baseline here is round one's rule re-implemented in this script (its league rate is per target; round three's is
per pass play, throwaways included, which is the whole difference between the two scripts' baselines), so read
each change against its own row.

| Receiving yards, layer added to round one's rule | 2019-22 | 2023-25 |
|---|---|---|
| Baseline (round one's rule) | 20.26 | 19.33 |
| A. Usage and rate decayed 0.90 per game back instead of a flat 17 | 20.16 | 19.24 |
| A. Decayed 0.95 | 20.30 | 19.46 |
| A. Usage decayed 0.90, rate flat | 20.12 | 19.21 |
| B. Game script: the team's pass plays from the closing spread and total | 20.23 | 19.24 |
| C. Defense by position: yards allowed per target to WR, TE and RB, a quarter of the way | 20.26 | 19.32 |
| C. Half of the way | 20.28 | 19.32 |
| D. Coverage-specific usage: his target share against man and zone, weighted by the defense's man rate | 21.19 | 19.58 |
| D. Half that, half plain usage | 20.66 | 19.44 |
| E. Route mix x what the defense allows per route, a quarter | 20.28 | 19.33 |
| E. Half | 20.32 | 19.32 |
| E. Fully | 20.43 | 19.33 |
| F. The head coach's pass rate over expected on the team's pass plays | 20.27 | 19.28 |
| G. Yards per target rebuilt from catch rate, depth of target and yards after catch, each shrunk | 21.67 | 20.76 |

Targets alone: 1.91 / 1.80 from usage share, 1.91 / 1.79 with the game script, 1.91 / 1.81 decayed 0.95.
Recency (A) and game script (B) help on both windows; everything scheme- or route-specific hurts or does
nothing, the coach's pass rate is inside the noise, and taking yards per target apart makes it worse. The
scheme data describe how the yards happened, not how many will come.

**Round three** (`experiments/props_backtest3.py`, `reports/props_backtest3.csv`): the two layers that helped,
combined, with a median factor, for all three stats. Every constant (the game-script line, the median factor) is
fitted on 2016 to 2018 only and applied forward.

| Rule | Receiving 2019-22 | 2023-25 | Rushing 2019-22 | 2023-25 | Passing 2019-22 | 2023-25 |
|---|---|---|---|---|---|---|
| Round one's rule (flat 17 games) | 19.99 | 19.04 | 19.24 | 18.51 | 64.31 | 64.27 |
| Usage decayed 0.90 | 19.84 | 18.91 | 19.00 | 18.28 | 64.31 | 64.27 |
| Usage decayed 0.85 | 19.79 | 18.83 | 18.89 | 18.15 | 64.31 | 64.27 |
| Game script only | 19.96 | 18.97 | 19.21 | 18.55 | 63.92 | 63.61 |
| Decayed 0.90 and game script | 19.82 | 18.84 | 18.98 | 18.31 | 63.92 | 63.61 |
| Decayed 0.85 and game script | 19.77 | 18.76 | 18.86 | 18.18 | 63.92 | 63.61 |
| Round one's rule x median factor | 19.62 | 18.65 | 18.67 | 17.94 | 61.42 | 61.63 |
| Decayed 0.90, game script, median factor | 19.50 | 18.53 | 18.48 | 17.74 | 61.24 | 61.56 |
| Decayed 0.85, game script, median factor (adopted) | 19.44 | 18.46 | 18.36 | 17.60 | 61.24 | 61.56 |

Volume alone (targets, carries): flat 1.91 / 1.80 and 3.14 / 3.03; decayed 0.90 1.88 / 1.77 and 3.06 / 2.95;
with the game script 1.88 / 1.76 and 3.06 / 2.96. Passing volume is the team's dropbacks either way, so the
decay does nothing there. Median factors as fitted: receivers 0.88 (0.86 on the flat rule), rushers 0.84, QBs
0.90. Player-games scored: receiving 16,089 / 12,399, rushing 7,554 / 6,012, passing 2,177 / 1,712. The adopted
rule is the best row on both windows for every stat; against round one it takes about half a yard off receiving
and a yard off rushing, and three yards off passing, most of that from the median factor. One convention differs
between the page and the script: the page's defense rate is yards allowed per pass play, the script's per target
(about 3% apart, inside a quarter-weight adjustment). A projection that is 19 yards off on average on a receiving
line is still a weak instrument; the live record will say whether it is worth anything against a market line,
once those are logged.

**Round four** (`experiments/props_backtest4.py`, `reports/props_backtest4.csv`): the layers a book adds that rounds
two and three did not test, each on top of the adopted rule (constants fitted on 2016 to 2018; base = the round-three
rule, and the same rows for receiving and rushing).

| Layer added to the round-three rule | Receiving 2019-22 | 2023-25 | Rushing 2019-22 | 2023-25 | Passing 2019-22 | 2023-25 |
|---|---|---|---|---|---|---|
| Base (round three's rule) | 19.44 | 18.46 | 18.36 | 17.60 | 61.24 | 61.56 |
| Wind: the line cut 0.5% per mph above 10 at kickoff | 19.43 | 18.46 | | | 61.06 | 61.47 |
| Wind, linear in every mph (0.4% / 0.2%) | 19.42 | 18.44 | | | 61.12 | 61.51 |
| Opponent pace: its allowed plays per game blended in, a quarter | 19.43 | 18.44 | 18.32 | 17.58 | 60.90 | 61.15 |
| Opponent pace, half | 19.44 | 18.44 | 18.32 | 17.59 | 60.98 | 61.06 |
| The QB's as-of rating, as a level (fitted 0.5 per EPA point) | 19.43 | 18.44 | | | | |
| The QB's rating as the change from the QBs he had over his window (fitted 1.0) | 19.46 | 18.46 | | | | |
| His own long-run rate (decayed 0.95) as the shrinkage prior instead of the league | 19.41 | 18.44 | 18.35 | 17.60 | 61.25 | 61.55 |
| Home and away (fitted +4% / +6% / +6% at home) | 19.44 | 18.44 | 18.37 | 17.62 | 61.37 | 61.43 |
| Pace a quarter and wind together (adopted for passing) | 19.42 | 18.44 | | | **60.71** | **61.08** |

Re-tuning the shrinkage weight K and the defense weight W on the new rule moved receiving by at most 0.05 (K 50
with no defense adjustment 19.39 / 18.42; K 400 19.68 / 18.70), rushing by 0.03 or less, and passing by up to 0.6
(no defense adjustment is worse: 61.84 / 61.59 at K 25), so they stay as they were. Passing yards gain half a
yard on both windows from the opponent's pace and the wind, and both are adopted: the team's dropbacks are blended
a quarter of the way toward what the opponent has allowed per game, and the line drops 0.5% per mph of kickoff
wind above 10, once a usable forecast exists (the game model's own kickoff-forecast rule, section 14; until then,
and in a dome, the factor is 1, as in the backtest). For receiving and rushing every layer is inside 0.05 yards,
which is noise at this sample, so nothing changes there: the QB's identity, home field, pace and wind are already
mostly inside the player's own recent rate and the game script. The projection remains about 19 yards off on a
receiving line and 61 on a passing line.

**Round five** (`experiments/props_backtest5.py`, `reports/props_backtest5.csv`): the other columns on the table,
receptions, touchdowns and interceptions, which the first four rounds left at the player's raw rate. Volume is the
adopted rule's; the rate per touch is his over his last 17 games, raw, the league's, or shrunk toward the league's
with K touches of weight, and for touchdowns also moved by the expected margin (favorites score more), fitted on
2016 to 2018. Receptions are scored by absolute error; touchdowns and interceptions by the Poisson log loss as
well, since a count that is usually 0 makes the absolute-error-best line degenerate (predicting none is "best")
and an anytime-scorer price needs the whole distribution. Lower is better throughout.

| Receptions | 2019-22 | 2023-25 |
|---|---|---|
| His raw catch rate (as the page had it) | 1.466 | 1.384 |
| League catch rate | 1.467 | 1.391 |
| Shrunk, K 25 | 1.459 | 1.377 |
| Shrunk, K 50 / 100 / 200 | 1.458 / 1.458 / 1.460 | 1.377 / 1.379 / 1.381 |
| Shrunk K 25 x median factor 0.88 (adopted) | 1.438 | 1.359 |

| Touchdowns and interceptions, Poisson log loss (absolute error in brackets) | 2019-22 | 2023-25 |
|---|---|---|
| Receiving TD, raw rate | 0.5737 (0.307) | 0.5448 (0.288) |
| Receiving TD, league rate | 0.5157 (0.313) | 0.4918 (0.298) |
| Receiving TD, shrunk K 50 / 100 / 200 / 400 / 800 | 0.5139 / 0.5121 / 0.5121 / 0.5129 / 0.5139 | 0.4899 / 0.4885 / 0.4885 / 0.4893 / 0.4902 |
| Receiving TD, K 200 x (1 + 0.020 x expected margin) (adopted) | 0.5101 (0.310) | 0.4869 (0.295) |
| Rushing TD, raw rate | 0.6612 (0.356) | 0.6370 (0.342) |
| Rushing TD, league rate | 0.6018 | 0.5739 |
| Rushing TD, shrunk K 50 / 100 / 200 / 400 / 800 | 0.5972 / 0.5949 / 0.5948 / 0.5961 / 0.5979 | 0.5695 / 0.5662 / 0.5655 / 0.5668 / 0.5689 |
| Rushing TD, K 200 (adopted) | 0.5948 (0.356) | 0.5655 (0.346) |
| Rushing TD, K 200 x (1 + 0.025 x margin) | 0.5953 | 0.5641 |
| Passing TD, raw rate | 1.5364 (0.950) | 1.4979 (0.928) |
| Passing TD, league rate | 1.5211 | 1.4853 |
| Passing TD, shrunk K 50 / 100 / 200 / 400 / 800 | 1.4990 / 1.4966 / 1.4954 / 1.4961 / 1.4996 | 1.4704 / 1.4676 / 1.4657 / 1.4659 / 1.4686 |
| Passing TD, K 400 x (1 + 0.020 x margin) (adopted) | 1.4868 (0.933) | 1.4543 (0.904) |
| Interceptions, raw rate | 1.2089 (0.761) | 1.1625 (0.716) |
| Interceptions, shrunk K 50 / 200 / 800 | 1.1785 / 1.1596 / 1.1454 | 1.1284 / 1.1129 / 1.1034 |
| Interceptions, league rate (adopted) | 1.1449 (0.720) | 1.1047 (0.704) |

The raw rates the page carried were the worst row for every count: a player's touchdown or interception rate over
17 games is nearly all noise, so it is shrunk hard (200 to 400 touches), and for interceptions the league rate
alone is best on both windows, so his own rate is not used at all. The expected margin adds a little to receiving
and passing scores on both windows (2% per point: a 7-point favorite's passer projects 14% more touchdowns) and
nothing consistent to rushing scores (better held out, worse on the tuning window), so it applies to the first two
only. The shrinkage weight was chosen on 2016 to 2018 by the Poisson fit (K 200 receiving, 200 rushing, 400
passing; on the two scoring windows K 200 is a hair better than 400 for passing, 1.4954 / 1.4657 against 1.4961 /
1.4659, but the fit window decides). Every column on the table is now graded live: receptions, receiving and
rushing touchdowns, passing touchdowns and interceptions join the yards in `data/tracker/props_graded.csv`.

**Round six: tied to the game model** (`experiments/props_backtest6.py`, `reports/props_backtest6.csv`). The player
projections and the game model priced the same games separately: the game model from ratings, the QB and the
weather; the players from the closing spread and total, adding up to nothing at the team level (Week 3 of 2026: the
players' touchdowns summed to 2.57 a team against 3.08 implied by the game model's points, correlation 0.72 across
the 32 teams). Two links, each on the round-five rule, walk-forward with the game model's own as-of expected points
(`pred_v3.parquet`, priced before each game):

| Link, on the adopted rule | Receiving yds | Rushing yds | Passing yds | Receiving TD (log loss) | Rushing TD | Passing TD |
|---|---|---|---|---|---|---|
| As adopted (closing spread and total) | 19.444 / 18.460 | 18.362 / 17.602 | 60.705 / 61.076 | 0.5101 / 0.4869 | 0.5948 / 0.5655 | 1.4868 / 1.4543 |
| A. Game script from the model's expected margin and total | 19.443 / 18.462 | 18.362 / 17.604 | 60.579 / 61.124 | 0.5104 / 0.4870 | 0.5948 / 0.5655 | 1.4892 / 1.4554 |
| A. Half and half with the closing line | 19.443 / 18.461 | 18.360 / 17.602 | 60.632 / 61.094 | 0.5102 / 0.4869 | 0.5948 / 0.5655 | 1.4875 / 1.4544 |
| B. Reconciled to the team's expected points, a quarter of the way | **19.397 / 18.421** | **18.231 / 17.435** | 58.800 / 58.660 | 0.5090 / 0.4861 | 0.5926 / 0.5634 | 1.4754 / 1.4422 |
| B. Half of the way | 19.464 / 18.524 | 18.245 / 17.400 | **57.683 / 57.305** | **0.5086 / 0.4858** | **0.5922 / 0.5629** | 1.4674 / 1.4328 |
| B. All of the way | 19.935 / 19.119 | 18.689 / 17.724 | 58.019 / 57.784 | 0.5093 / 0.4867 | 0.5971 / 0.5676 | **1.4632 / 1.4226** |

Link A does nothing: the closing line and the model's margin carry the same information for volume. Link B helps
every stat on both windows. The team's expected receiving, rushing and passing yards and touchdowns are lines on
its expected points fitted on 2016 to 2018 (receiving touchdowns -0.253 + 0.0748 x points, yards 86.2 + 6.48 x
points; rushing -0.186 + 0.0409 x and 71.5 + 1.39 x; passing -0.262 + 0.0790 x and 73.8 + 6.89 x), and every
player's line is scaled by the ratio of that to what his team's players add up to (the ratio clipped to 0.5 to 2),
with the move weighted: yards a quarter of the way for receiving and rushing, half for passing; touchdowns half
for receiving and rushing, all the way for passing. Adopted (bold): passing yards gain three yards on both windows,
the rest a tenth or so, and the projections now carry the game model's read of the game. On the card each team
shows its expected points and the two factors applied.

**Round seven: defenders** (`experiments/props_backtest7.py`, `reports/props_backtest7.csv`; `nflmodel/props.py`
`defender_games`, `defenders`, `project_defense`). The books post tackles plus assists and sacks, so the play-by-play's
tackle credits since 2016 (every solo, assist and tackle-with-assist credit; sacks with half sacks as 0.5;
interceptions; passes defended; the plays the defense faced) build one row per defender and game
(`data/processed/def_games.parquet`, 93,877 rows), and the same walk-forward machinery projects them. Tackles: his
share of his team's tackles (decayed 0.85 per game back) x the team's tackles per play faced x the opponent's plays
(its last-17 average moved by the game script from its side of the line) x a median factor of 0.90, fitted on 2016
to 2018. Tested (absolute error, tuning / held out): his plain average 1.679 / 1.673; flat share 1.693 / 1.694; share
decayed 0.85 1.676 / 1.672, 0.90 1.674 / 1.672; decayed with the game script 1.673 / 1.668; that shrunk toward his own
average with 2, 4 and 8 games of weight 1.670 / 1.665, 1.668 / 1.663, 1.667 / 1.662; decayed, game script, median
factor **1.648 / 1.633** (adopted). Sacks by Poisson log loss: his plain average 0.4190 / 0.4219, the league rate
0.4429 / 0.4513, his rate per play faced shrunk toward the league with 100 plays of weight 0.3854 / 0.3922, **300
plays 0.3813 / 0.3887** (adopted), 600 0.3840 / 0.3916, 1,000 0.3892 / 0.3968. The card's Player props panel lists
each team's top eight defenders by projected tackles with the book's tackles-plus-assists line beside them (the sixth
market in the twice-weekly pull, which moved the game-line pull to once a day to stay inside the free 500 credits);
both stats are graded live from the same tackle credits.

**The rule over the years** (`experiments/props_by_season.py`; `reports/props_by_season.csv`, `props_by_position.csv`,
`props_by_bucket.csv`; on the page under Results, Player projections). The adopted rule for all eight stats, run
walk-forward over every charted season from 2017 (2016 is the first charted season, so its players have no history)
to the current week, set against the raw rule the page started with (flat 17-game rates, no game script, no
shrinkage, no median factor). Receiving yards by season: 2017 19.64 against 20.40 raw, 2018 20.05 / 20.78, 2019
19.99 / 20.82, 2020 19.66 / 20.36, 2021 19.47 / 20.37, 2022 18.71 / 19.37, 2023 18.57 / 19.45, 2024 18.73 / 19.38,
2025 18.08 / 19.08; the rule beats the raw one in every season for every yards stat, and the two windows read
exactly what the rounds found (19.44 / 18.46 receiving, 18.36 / 17.60 rushing, 60.71 / 61.08 passing), which the
tie check holds. The over rate (share of player-games where the actual beat the line) sits at 47% on receiving
yards, 48 to 49% on rushing and 52% on passing, so the receiving line still sits a little above the median even
after the median factor, and the bias (line minus actual) is about -4.5 yards on every yards stat: the mean of a
right-skewed stat sits above its median, which is what a line at the median should show. Receptions: 1.44 / 1.36
against 1.49 / 1.41 raw, over rate 51 to 52%. Scores and picks: the Poisson fit improves on the raw rate on both
windows for all four, and the anytime rate (the predicted chance of at least one against how often one came) reads
17.9% against 17.5% on receiving touchdowns, 20.8% against 21.4% rushing, 79.3% against 78.3% passing, and 55.9%
against 50.4% on interceptions (2019 to 2022), so the Poisson overstates the chance of a pick: interceptions come
in fewer games than a Poisson at that rate would give. The tables also split by position (WR, TE, RB for receiving
stats; RB, QB and others for rushing) and by size of the line, where the over rate by bucket shows whether small
and large lines are set alike.

**Absences.** A listed-out player still shows on the card with what he would have projected against this defense,
so the size of the loss in this matchup is visible, and his volume is redistributed as above. The game model's
own absence inputs are unchanged by this (section 15); a matchup-adjusted version is tested in section 14.

**Round eight: the longest-play markets** (`experiments/props_backtest8.py`, `reports/props_backtest8.csv`; `_longest`
in `nflmodel/props.py`). PrizePicks posts longest reception, longest rush and longest completion, which sat on the
card with a line and no projection. Per player and game the longest gain of his kind (completed passes for
receivers and passers, runs for rushers; 0 when he had none) since 2016, projected walk-forward from his previous
games, scored by absolute error in yards (tuning / held out). Longest reception: his plain average over his last 17
games 9.802 / 9.777 (baseline); decayed 0.85 per game back 9.781 / 9.794, 0.90 9.730 / 9.731; decayed and shrunk
toward his position's league average from the previous season with 2, 4, 8 and 16 games of weight 9.700 / 9.704,
9.660 / 9.658, 9.630 / 9.618, 9.631 / 9.614; a blend fitted on 2016 to 2018 (6.9084 + 0.3362 x decayed longest +
0.1291 x his yards per game) 9.598 / 9.573; shrunk (8 games) x median factor 0.84 9.296 / 9.326; **the blend x
median factor 0.84 9.256 / 9.274** (adopted). Longest rush, the same variants: baseline 8.479 / 8.253; **the blend
(6.9330 + 0.1545 x decayed longest + 0.1153 x yards per game) x 0.78 7.575 / 7.309** (adopted). Longest completion:
baseline 12.218 / 12.237; **the blend (16.3327 + 0.2340 x decayed longest + 0.0547 x passing yards per game) x 0.92
11.803 / 11.686** (adopted). Every variant beat the baseline on both windows; the blend with the median factor won
every stat on both. On the card the three lines sit beside the book's under Player props, in the calculation
walk-through, in the weekly file and the grading (the longest gain per player-game from the same play-by-play).

**Round nine: kickers** (`experiments/props_backtest9.py`, `reports/props_backtest9.csv`; `kicker_games`, `kickers`,
`project_kicker` in `nflmodel/props.py`). PrizePicks posts kicking points and field goals made. One kicker per team
and game from the raw play-by-play since 2016 (field goals made and tried, extra points made and tried; points =
3 x field goals + extra points), projected walk-forward and scored by absolute error (tuning / held out). Kicking
points: his own points a game over his last 17 2.919 / 3.051 (baseline); his own decayed 0.85 2.936 / 3.073; his
team's points a game decayed 0.85, whoever kicked, 2.922 / 3.043; a line on the team's implied total from the
closing line ((total + expected margin) / 2) 2.837 / 2.926; a blend of his own decayed rate and the implied total
2.833 / 2.926; **the team's decayed rate and the implied total (2.4861 + 0.1843 x team points + 0.1489 x implied
total) 2.832 / 2.925** (adopted); that x a median factor 0.96 2.817 / 2.933, better on tuning and worse held out,
so not taken. Field goals made: baseline 0.979 / 1.018; **the team blend (1.0165 + 0.1757 x team field goals a
game + 0.0155 x implied total) 0.969 / 1.001** (adopted); the median factor 1.02 0.970 / 0.999, mixed again. The
team's rate was taken over his own because it scored the same or better on both windows and a new kicker inherits
the offense that feeds him. The card's Player props panel gains a Kicking section with the roster's kicker, his two
lines beside the book's, the walk-through, and the grading from the same kick plays.

**Round ten: redistribution, red-zone role, offseason fade** (`experiments/props_backtest10.py`,
`reports/props_backtest10.csv`; `_share` and `FADE` in `nflmodel/props.py`). Three player-side claims on the adopted
rule, walk-forward, tuning / held out. (A) When a teammate is out, the page handed his share of the team's targets
or carries to the others pro rata among the listed players who were playing. Tested with hindsight absences (a
player with 5%+ of usage, seen in the team's last three games, not in this one; someone is out in 89% of
team-games for receivers, 80% for rushers): no redistribution 19.397 / 18.421 receiving yards, 18.231 / 17.435
rushing; pro rata 20.393 / 19.238 and 19.203 / 18.249; half pro rata 19.733 / 18.717 and 18.512 / 17.664; to the
same position group 20.153 / 19.061 and 18.781 / 17.865; half of that 19.633 / 18.624 and 18.356 / 17.517. Every form
lost on both windows, on volume too (targets 1.868 / 1.748 with none against 2.264 / 2.076 pro rata), so the page
no longer redistributes: an absent player's share is simply not projected, and the freed touches show up as the
team's expected points do, through the round-6 scaling. (B) Red-zone role: expected touchdowns per touch from the
yard line of his targets or carries (league scoring rate by bucket, 2016 to 2018) as the prior his own rate is
shrunk toward instead of the league average, and on its own. Receiving, Poisson log loss: the rule 0.5086 /
0.4858; expected alone 0.5143 / 0.4886; shrunk toward expected with 100 to 800 touches 0.5126 to 0.5133 /
0.4875 to 0.4881; expected itself shrunk 0.5091 / 0.4855. Rushing: the rule 0.5922 / 0.5629, the best variant
0.5928 / 0.5629. Passing: the rule 1.4632 / 1.4226, the best variant 1.4630 / 1.4223, a gain in the fourth
decimal. Nothing beat the rule on both windows by a size worth carrying, so the league prior stays. (C) Offseason
fade: an extra factor on the usage share's weights across a season boundary and across a change of team.
Receiving: none 19.397 / 18.421; season half 19.361 / 18.358; season a quarter 19.378 / 18.341; team half 19.373 /
18.378; team a quarter 19.363 / 18.353; **both half 19.354 / 18.332** (adopted); both a quarter 19.387 / 18.326;
season a quarter and team half 19.380 / 18.329; season half and team a quarter 19.356 / 18.321. Rushing: none
18.231 / 17.435; season half 18.157 / 17.336; season a quarter 18.127 / 17.294; team half 18.205 / 17.390; team a
quarter 18.190 / 17.368; both half 18.141 / 17.314; both a quarter 18.124 / 17.290; **season a quarter and team
half 18.121 / 17.285** (adopted); season half and team a quarter 18.137 / 17.305. The gains sit in weeks 1 to 8 as
expected (receiving 20.166 / 18.709 to 20.120 / 18.598; rushing 18.098 / 17.736 to 17.930 / 17.521). The page's
receiving and rushing errors are the fade rows; the by-season run carries the fade too.

**Cards, 23 Sep 2026 evening (Matt).** The game rail shows the game on screen as a dark filled row and the flagged games
in green, so the two no longer look alike. The Player props table lists only the markets the rule projects, with
"no line" where no book has posted one; the opening line moved into the Book cell's hover, the "Other book lines"
section (lines on players without a projection) is gone, and clicking any market row opens the player's
calculation with that step lit; the Model tab holds the why. The win-band chip and the "moved" chip under the
line graphs are gone (the calibration table is on the Backtest tab; the graph shows the move). PrizePicks'
adjusted-odds lines (a 0.5-yard "line" at a cut payout) are dropped by the parser and filtered out of the log
when it is read. Underdog's pick'em search endpoint answers from the runner (100 lines a page, real higher/lower
prices), so the parser reads that shape and pages through it; whether it returns every game is checked on the
next pull. American spelling throughout.

**Every breakdown adds up to the cent (23 Sep 2026, evening).** The game deep dive summed to 19.96 against the model's
18.2 for ARI at LAC, Week 1: the per-team rows lacked the inputs the regression computes for itself (offseason
turnover, out of the race, warm-climate team in the cold) and the page used the season-start coefficients where the
model refits before every week. Two fixes. `model.walk_forward` now writes, on every priced game, the fit that
priced it: the coefficient and training mean of each of the 22 inputs and the intercept (`coef_*`, `mean_*`,
`intercept` in `pred_v3.parquet`), and the export carries them on the week file's games and the backtest file's rows;
the page's card breakdowns and the deep dive use that fit (`coefsForGame`), the season table only as a fallback.
And every team's game rows carry the inputs exactly as the regression saw them (`mf_<input>`, from `model.prep` on
the as-of features), shown in the game log under Model inputs and read first by the deep dive. The tie check
rebuilds the expected points from the page's own files for every side this week and for the newest sixty priced
games, and requires the gap under 0.01 points. Also this evening (Matt): the Team tab's Players sub-tab is gone
(the roster's Above replacement column and the Players tab carry it), the roster tables stack full width so nothing
scrolls sideways, the ratings-by-week chart carries its latest values as a caption instead of labels over the lines,
the player game logs gain the longest gain and air yards (the round-8 input and the depth of target), and the
Positions and Players notes say what the value window is: the last eight games across seasons (swept on both
windows, `players.DEFAULT`), where the props profiles use the last 17 (round 1). PrizePicks' adjusted-odds lines
are kept (they cover most of its board); only the impossible ones (a yardage line under 2, a count under 1) are
dropped when the log is read. Underdog's search endpoint returned one game from the runner; the fetcher pages it
and, when fewer than three games come back, probes the other feeds and prints what answered.

**The card follows the line log (23 Sep 2026, evening; Matt).** A card showed Vegas GB -4.5 while its own graph and best-number
chip read -5.5: the card's Vegas line came from the weekly run's snapshot (4:52 PM ET) and the graph from the line
log (5:15 PM). Now the card's Vegas line is the latest logged consensus (`latestLine`), and the edge, the cover odds
and the best number follow it; the cover odds are re-priced on the page with the same calibration the run used
(`picks.calibration`'s logistic on the edge, exported with the week as `cal`; the tie check confirms the page's
curve reproduces the run's calibrated odds at the run's line). The flag and its bet stay as recorded at the run, so
a flagged card can show a line that has since moved; the week header says "lines as of" the last snapshot. And the
page itself no longer waits for a weekly run to refresh: `python -m nflmodel.export_web --week` rebuilds only
`web/data/week.js` from the log (about a minute), and the hourly routine that kicks the line watch now also pulls
main, runs it and republishes that one file, so the cards are never more than about an hour behind the log.

**Injuries: the source and how fresh it is (23 Sep 2026, evening; Matt).** Statuses come from nflverse's injury
file, which follows the league's official reports (Wednesday to Friday) with a lag of hours to a day, and from the
weekly rosters for IR, PUP and suspensions. On Wednesday evening of Week 3 nflverse carried Week 3 reports for ATL
and GB only (the Thursday game), so a Giant like Jaxson Dart read Active with no report. ESPN's injury page posts
the same reports the same afternoon, so the pull now fetches it beside the nflverse file
(`pull.espn_injuries`, `data/raw/injuries/espn_injuries.csv`) and `players.load_injuries` fills the current week
from it for any team whose nflverse report is not in yet (Out, Doubtful, Questionable, IR, suspension and PUP
mapped to the report statuses; matched to a gsis id through the weekly roster by team and name). The weekly run
picks it up on its Tuesday, Thursday, Saturday and Sunday schedule. The first run from GitHub's network got a 403
from ESPN's main host, so the page is now fetched the way the line watch fetches the scoreboard (browser headers,
`site.api` then `site.web.api` then `cdn`, the first to answer wins); when every host refuses, the previous file is
kept and the pull says so rather than failing. The fill is used only when the file was fetched within four days
(`players.ESPN_MAX_AGE_DAYS`), so an old page can never stand in as this week's report, and the health check counts
the teams with a report for the week being priced (league plus fill) against the time to kickoff. A `probe`
workflow runs one command on the runner and prints what it wrote, for testing a source from GitHub's network.

**Why the stale line passed every check, and what now fails (23 Sep 2026, evening; Matt).** The tie check and the
health check compared the page's data to the picks file, and both came from the same weekly-run snapshot, so they
agreed with each other while both lagged the line log; nothing compared a card to the newest snapshot. Now: the
line watch rebuilds the cards after every snapshot (`nflmodel.props --markets` puts the newest prop lines beside
the projections in seconds; `export_web --week` rewrites `week.js` and `props.js`) and commits them with the log;
the tie check ties the cards' newest line snapshot to the log's newest; the health check (the Monday audit) fails
when the cards' newest snapshot is not the log's or the props panel's pull is not the props log's newest; and the
hourly routine republishes the two files. The page also refuses to half-render: with its core data file missing it
says so in one line instead of failing part way. A break-it walk (every tab, sub-tab, select value, chip, sortable
header, card panel, market row and calc, at desktop and phone width, then again with each data file blocked one at
a time) found no other error.

**Phones** (23 Sep 2026). The page declares a viewport, so a phone renders it at its own width instead of shrinking
a 980-pixel desktop page. Below 700 pixels the same page reflows: tighter header and tabs, tiles two across, the
game rail a scrolling strip pinned to the top, wide tables scrolling inside their own box (grid children may not
stretch past the screen), the props table without its Open column and with names wrapped. Nothing changes above
that width.

**Against the market** (`nflmodel/props_lines.py`, `data/lines/props_log.csv`, `data/tracker/props_vs_market.csv`).
No historical player prop lines exist in the repo or in any free source: The Odds API keeps them from May 2023 on
paid plans only, so the market comparison is live from Week 3 of 2026. The line watch pulls the player props from
The Odds API twice a week inside the free 500-credit month: the Thursday game on Thursday at 20:00 UTC (six
credits) and the rest of the week on Sunday at 14:00 UTC (about 90), with the game-line pull cut to once a day
to make room (ESPN carries the game lines every half hour anyway). Markets: receiving yards, receptions, rushing
yards, passing yards, anytime touchdown, tackles plus assists, every US book, appended with the raw response saved.
PrizePicks' pick'em board is logged too, every six hours with no key and no credits (`prizepicks()` in the same
module, the `force_dfs` input on the line watch runs it alone): every market at even odds by construction,
standard lines only (no demon or goblin alternates, promo "flash sale" copies of a line dropped), touchdown
markets left out because a pick'em 0.5 line carries no price. The first run from the GitHub runner (23 Sep 2026)
logged 774 lines across 17 markets, among them longest reception, longest rush, targets, pass plus rush yards,
kicking points and field goals, which the free Odds API tier cannot afford. Underdog's over/under feed refuses
the runner on every version tried (v6, v5, v3: 426 Upgrade Required), so it is not a source. Two projections were
added so those lines have a comparison: targets (the projected targets already inside the receiving line) and pass
plus rush yards (the QB's passing line plus his rushing line), graded like the rest. The longest-play markets got their
projections in round eight and the kicking markets in round nine, so every PrizePicks market on the board has a
projection beside it. The props builder takes the last pull for each game, the median
line across books, and puts it beside each projection on the card with the side the projection leans (over above
the line, under below; for the anytime touchdown the book's price as an implied probability beside the
projection's chance of at least one score, 1 - exp(-(receiving + rushing expected touchdowns))). When the game is
played, every projection with a line is graded: the side, the result, and the projection's error beside the
book's own on the same player-games, so the two can be compared directly; the record by stat and by size of the
edge is shown under Results, Player projections. Names are matched between the book and the roster on a
normalized form (lower case, letters only, suffixes dropped). A record needs hundreds of graded lines before it
says anything, and the honest prior is that the closing line is better than a 19-yard projection.

**Historical lines, the pull that is ready.** The Odds API keeps player-prop snapshots from 3 May 2023 at five-minute
intervals on its paid plans; the key already in the repo just needs the plan changed for one month. The history
endpoint charges 10 x markets x regions per game (the docs' own rule), so five markets from the US books cost 50
credits a game: 887 games from 2023 to Week 2 of 2026 in 425 kickoff slots come to about 44,800 credits per
snapshot, which is the 100K plan ($59). `nflmodel/props_history.py` and the `historical prop lines` workflow pull
one of two snapshots: the close (one hour before kickoff) or the open (the Tuesday of the game's week at 16:00
UTC), resume where they stop, cap at a credit budget, and a probe mode pulls one game first and prints what it
cost and what remains, so the plan is proven before the run. Both snapshots fit in one month of the 100K plan
(about 89,300 credits together). Rows go to `data/lines/props_history.csv` with the raw responses kept.
`experiments/props_vs_market_backtest.py` then grades the walk-forward projection against the closing lines: the
side it takes at every edge cut on a tuning window (2023 to 2024) and held out (2025 on), the same side against
the best line across the books (line shopping), the book's own error beside the projection's and beside a blend
of the two, the anytime touchdown on both sides and on the yes side alone, and, with the opening snapshot, the
record at the opener and the closing line value. It also chooses the cut to flag at per stat the way the game
model's was chosen: the largest cut clearing 52.4% on both windows with at least a hundred decided bets on each,
or none; `props.py` flags a prop on the card only once such a cut exists (`PROP_EDGE`, None until then). The
tables land under Results, Player projections, once the file exists; the pipeline was exercised end to end on a
synthetic history built from the actual outcomes plus noise, then deleted, so nothing synthetic is in the repo.

**Where the player data is on the page.** Players tab: every rostered player with a value, and a search that also
finds anyone with a game log since 2016. A player's page carries his value and its basis; his profile (the last 17
games the projections start from: usage share, rates, catch rate, depth of target, touchdown rates, and the splits
against man and zone, blitz and pressure, light and heavy boxes); every projection written for him with the grade
once the game was played and the book line where one was logged; his game log from the charted plays, one row per
game with volume, yards, touchdowns, EPA and the same splits (blank where the plays were not charted, 2026 included
until the participation data is published); and his season history from the play-by-play. The exports
(`web/data/player_profiles.js`, `plogs/<season>.js`, `player_careers.js`, `props_record.js`) are rebuilt by every weekly run from the same
tables the projections use, and the tie check holds their counts to the sources.

**Track record.** Every projection is written to the week's props file at each run; on the next run every earlier
week's projections are graded against the players' actual yards from the play-by-play (receiving, rushing, passing),
with the error kept per player and stat in `data/tracker/props_graded.csv`, and the mean absolute error and bias
by stat shown on the cards. Nothing is compared with a market line yet: player prop lines are not logged. The
projections are readings until the record says otherwise.

## 19. Season: win totals, divisions, playoffs, the Super Bowl, player season totals (23 Sep 2026)

**Team odds** (`nflmodel/season.py`, `web/data/season.js`, `reports/season_odds.csv`). The rest of the regular
season is played out 10,000 times. Every remaining game gets an expected margin from the game model's own equation
(section 5: the fit's coefficients, training means and intercept as of the week, applied to each team's ratings as
of the week: its offense and defense ratings, its QB, its offseason turnover, its record for the out-of-the-race
input), and the week being priced uses the model's actual predictions for those games (`pred_v3`, forecast and
absences included). Games further out carry no forecast or absences: wind at the league-typical 7 mph outdoors, no
one out. Margins are drawn from a normal with the model's residual scale (13.0 points); a margin within 0.07 of
zero is a tie (about one game in 230, the league's rate). Standings settle by win share, then the league's
tiebreakers as far as records go: head-to-head share among the tied, division record, conference record, then a
coin flip (the strength-of-victory and points rules beyond those are not applied; on a probability they move
nothing visible). The four division winners and the wild cards (three from 2020, two before) seed by the same
order, the bracket plays with the higher seed at home and the Super Bowl on a neutral field. Each team's share of
the runs is its odds; the tie check requires the odds to add up (one champion, two conference champions, eight
division winners, fourteen playoff teams, two byes) and the expected wins across the league to equal the games.
The equation is tied to the model every run: with the week's own situational inputs, it must rebuild the model's
expected points for the week's games to a hundredth (it does, to zero).

**Backtest** (`experiments/season_backtest.py`, `reports/season_backtest.csv`). The same odds made as of weeks 1,
5, 9, 13 and 17 of every season 2019 to 2025 (the simulation sees the games before that week and the model's
ratings and fit as of it), scored against what happened. Averaged over the as-of weeks, 2019-22 / 2023-25: expected
wins off by 1.36 / 1.58 games per team against 1.61 / 1.73 for pace (current wins plus half the games left);
division odds Brier 0.084 / 0.138 against 0.114 / 0.174 for "the current leader takes it" and 0.1875 flat; the
division favorite won it 75% / 56% of the time; playoff odds Brier 0.122 / 0.147 against 0.243 / 0.246 flat; Super
Bowl log loss 2.48 / 2.86 against 3.47 flat, the eventual champion ranked 4.8 / 7.4 on average in the Super Bowl
odds (the 2023-25 window holds a champion the odds had far down the list). Two knobs were tested: shrinking the
future-game margins toward zero (0.1, 0.2, 0.3) and widening the residual scale (1.15x). Every combination helped
the held-out window and hurt the tuning window, so none is used; the simulation has no fitted knob of its own.

**Player season totals** (`nflmodel/player_season.py`, `reports/player_season_totals.csv`). A player's season
total = what he has so far + his per-game mean against an average defense x the games his team has left x a
fitted share, blended with pace (his own per-game so far over the whole schedule; last season's total before
anything is played). The per-game mean is the props rule's own volume and rate (section 18: his usage share
decayed 0.85 per game back with the season and team fades, x his team's plays per game over its last 17, x his
yards per touch shrunk toward the league), without the game script, the opponent and the median factor, since a
season total is a sum of means. The share and the pace weight are fitted on 2016 to 2018 as of the same weeks on
the season-total error: receivers 0.65 and 0.5, rushers 0.625 and 0.5, passers 0.525 and 0.75 (rushers 0.6 and passers 0.5 until 24 Sep 2026, before kneels, two-point tries and gross passing yards were put on the official terms). The share sits below
the share of remaining games such players actually play (0.77, 0.75, 0.74) because the misses are one-sided (a
player who is hurt loses everything, one who stays healthy gains nothing) and the pace half carries part of the
load. A player is projected when he is active on his team's roster, has a profile and reaches 2.5 targets, 4
carries or 20 dropbacks per game (the starting QB by dropbacks per team). Backtest
(`experiments/player_season_backtest.py`, `reports/player_season_backtest.csv`): as of weeks 1, 5, 9 and 13 of
2019 to 2025, mean absolute error of the season yards, 2019-22 / 2023-25: receiving 125 / 124 against pace 142 /
140 and last season 232 / 226; rushing 162 / 149 against 180 / 162 and 298 / 305; passing 556 / 591 against 594 /
634 and 978 / 1,031. Before the fit (the mean share of games played, no blend) passing was worse than pace on both
windows (778 / 865), which is what the fit on 2016 to 2018 repaired. Breakout watch: a top-24 receiver, top-24
rusher or top-12 passer projection at a per-game rate at least 1.25x his previous season's (so a return from a
short injury season is not one); scored by whether he finished inside the top N at such a rate: receivers 66% /
69% came true against a base rate of 16% / 19% among every top-24 projection, rushers 78% / 89% against 20% / 27%,
passers 46% / 92% against 5% / 9% (13 and 12 flagged). "New to the top": a top projection with no previous season.

**Props record, live** (Backtest tab, "Player props"). Every projection graded against what the player
did, by week and by stat, with the book line and the side where one was logged, and every row. The projections
went live in Week 3 of 2026; Weeks 1 and 2 were projected after the fact with the data as of each week and the
same rule (`python -m nflmodel.props --backfill 2026 1`, marked "after the fact" in the record) so the season's
record starts at Week 1. Those two weeks already say something: passing-yard projections ran about 40 yards high
(bias -40 and -48 on 29 and 32 QB-games), receiving and rushing a few yards high; the record is there to watch
whether that holds.

## 20. Every data store on the site (23 Sep 2026)

Matt asked where the scheme, play-calling and route data live and to see every store on the site. Model → Every
data store (`nflmodel/catalog.py`, `web/data/catalog.js`) lists each file the model keeps, read from the files
themselves on every build so it cannot drift: the raw downloads (what each holds, seasons, files, size, rows and
columns of the latest file, when last pulled), the built tables (rows, columns, the step that writes each, where
it shows on the site), the line, weather, tracker and run logs, the reports and the page's own files. Team →
Scheme and play calling shows a team's offense and defense profile this season against the league with its rank
among the 32 (pass rate and pass rate over expected, shotgun, motion, play action, RPO, screens, tempo, time to
throw, EPA and success by play type; coverage mix, blitz and pressure rates, rushers, box counts, DB packages)
and its EPA by the look it faced or played. Routes: no public source charts routes run. FTN (2022 on) charts
motion, play action, RPO, screens, blitzers and pass rushers, the box, QB location and pocket, catchable and
contested balls; nflverse participation (2016 on) gives personnel, the players on the field, coverage (man or
zone and the family), time to throw and pressure; depth of target and air yards come from the play-by-play. Those
route-adjacent readings are what the site carries (Players tab splits, Team → Scheme). 2026 participation is not
published yet, so coverage, personnel and time to throw are blank for this season until it is.

## 21. Accuracy and legitimacy round (23 to 24 Sep 2026)

Every claim on both windows, as before. What changed, what did not, and what it says about the edge.

**A look-ahead removed from the props backtests.** Every props round, and the by-season run behind the page's
numbers, shrank each player's rate toward a league average taken over every season in the data, future seasons
included. The live rule uses last season and this season to date (`props._asof`). The by-season run now uses the
same as-of average (`experiments/props_by_season.py`, `LEAGUE_ASOF`). The look-ahead was small: at most 0.05 yards
on passing, under 0.01 elsewhere, so no constant changes because of it; the page's props backtest numbers now come
from the as-of run, and a tie holds them to it.

**Round eleven: three stale constants** (`experiments/props_backtest11.py`, `reports/props_backtest11.csv`). The
median factors that turn a mean into the line that misses by least were fitted in rounds 3 and 5, before rounds 4
to 10 changed the rule under them. Refit on the fitting seasons (2017-18) with today's rule, and tested beside
walk-forward versions (expanding, last three, last two seasons):

| Line | Factor | 2019-22 | 2023-25 | Verdict |
|---|---|---|---|---|
| Receiving yards | 0.88 to 0.81 | 19.36 to 19.30 | 18.32 to 18.27 | adopted |
| Receptions | 0.88 to 0.90 | 1.435 to 1.435 | 1.356 to 1.355 | adopted |
| Passing yards | 0.90 to 0.89 | 57.70 to 57.68 | 57.36 to 57.24 | adopted |
| Rushing yards | 0.84 | no variant better on both | | kept |
| Passing, rolling factor | 0.79 to 0.93 by season | 57.77 | 56.94 | not adopted: fixes the 2023-25 drift (bias +6.4 to +0.8), costs 2019-22 |

**Robust loss for the points equation** (`experiments/robust_loss.py`, `reports/robust_loss.csv`). Scores have
blowouts and the model is judged on absolute error, so a Huber loss was tried: team points miss better on both
windows, spread miss worse on 2019-22 and better on 2023-25. Not adopted (the spread is what is bet; the same
test rejected the pass and rush split). Median regression was too slow to score.

**Which seasons the cover odds learn from** (`experiments/calibration_start.py`, `reports/calibration_start.csv`).
The cards' cover odds are a logistic fit on |edge| over 2019 to the season before. Starting in 2015, 2016 or 2017,
or a rolling window, was scored walk-forward on the season after: earlier starts score slightly better on all
games and worse on the flagged games, on both windows; every difference is under 0.001. No change. The finding
that matters: the odds are conservative on the flags. Flagged games were stated at 55 to 58% and won 60% (2020-22)
and 68% (2023-25). The fit is dominated by the many small-edge games, so it is nearly flat.

**Staking and luck** (`experiments/sizing_backtest.py`, `reports/sizing_backtest.csv`). The flag's bets at the
closing line and -110:

<!-- auto:sizing -->
| Window | Record | Units | Drawdown (units) | Quarter Kelly | Chance of this by luck |
|---|---|---|---|---|---|
| 2016-18 (never used to choose) | 39-39 | -3.5 | 14.4 | -12.1% | 70% |
| 2019-22 (the threshold was chosen here) | 80-51 | +21.7 | 12.4 | +18.2% | 2.8% |
| 2023-25 (held out) | 40-21 | +15.4 | 5.0 | +15.7% | 2.6% |
<!-- /auto:sizing -->

The table is rewritten from `reports/sizing_backtest.csv` on every run. The held-out and tuning records are
unlikely to be luck (a few in 100 each); the earliest seasons lost. They were thin (fewer flags than 2019-22; the
model trained on two to five seasons), so the honest statement is: the edge shows from 2019 on, held out, and not
before. Full Kelly's worst fall is several times quarter Kelly's (never bet it). The track record now states each week
whether the live record sits inside the range the backtest rate implies for that many bets.

**Season odds reliability** (`reports/season_calibration.csv`, Backtest -> Season odds and player totals). When the odds said x%, how
often it happened: 2019-22 is close in every band. In 2023-25 the confident end was too confident (a 70-85%
division favorite won 55% of the time, a 85-95% playoff chance came in 82%) and the long shots came in too often.
The two knobs tested (shrinking future margins, widening the scale) both help 2023-25 and hurt 2019-22, so the odds
are shown as they are, with this table beside them.

**What is left for the game model.** Every public input and form has now been through both windows: the matchup
histories, referees, travel, rest, pace, primetime, the pass and rush split, interactions and trees, recency
weights, rolling training windows, turnover-luck ratings, the direct margin fit, robust loss, the rating knobs.
The equation is saturated on what nflverse publishes. The next real gains need information it does not have yet,
which the site now logs every day: line movement from open to close (for closing line value on every flag), the
2026 participation charting when nflverse publishes it (coverage and pressure for this season), and a live record
long enough to judge. The props rule has more room (the passing drift is real and a both-window fix has not been
found yet); it gets the next rounds.

## 22. Everything live, pulled together (24 Sep 2026)

Matt asked when "Last updated" moves and for every number that can be live to be pulled at the same time. Before
today it was the time of the last full model run (four scheduled runs a week plus any started by hand), while the
line watch refreshed the cards' lines every 30 minutes without touching it, and starters, injuries and forecasts
were pulled only by the model run.

Now every line-watch run (every 30 minutes) also pulls the schedule's named starting QBs and kickoff times, the
league's injury reports and ESPN's same-day page, and the kickoff forecasts (`nflmodel/refresh.py`). It compares
what the model would see for the week being priced with what the last model run priced with
(`data/runs/inputs_fingerprint.json`): a named QB or kickoff changed, a player moved into or out of Out or Doubtful,
or, inside the forecast window the model uses, the wind moved 2 mph or the cold or rain call flipped. When any of
those changed, the line watch starts the model run, which pulls the lines first and re-prices every game, prop,
season odd and player total from the same moment's data. Weather-only changes re-price at most once every two
hours. Every check is logged (`data/runs/refresh_log.csv`) and the page shows it: "Last updated" is the newest
time any data on the page was pulled, with each source's own time on hover (model re-priced, game lines, prop
lines, the last live check and what it found).

Times on the page read 8:15 PM style everywhere, including the game rail.

A duplicate element id (the new Season tab and the Teams tab's season picker shared "season") had emptied the
picker; the tab was renamed, a browser that had saved the old tab name is sent to the right one, and the page tie
check now fails on any duplicate id.

## 23. Player pages and game logs (24 Sep 2026)

The Players tab is a ranked list with a search box and team, position and status filters. Clicking a player opens his page:
value over a backup, this season's totals, the season projection, projections against results, a game log for any season
since 2016, career by season, and his results against the looks defenses showed him. The Game deep dive under Teams was
removed because the game card already shows the same model inputs.

`nflmodel/player_logs.py` builds one row per player and game (regular season and playoffs) from:

| Source | Columns |
|---|---|
| nflverse play-by-play | targets, catches, carries, attempts, yards, touchdowns, longest, air yards, yards after catch, first downs, red-zone looks, fumbles, sacks, interceptions, EPA, tackles, sacks and interceptions on defense, kicks |
| nflverse snap counts | snaps, snap share |
| Pro-Football-Reference charting via nflverse (2018 on) | drops, broken tackles, yards before and after contact, bad throws, pressured, blitzed, hit, coverage allowed, missed tackles, pressures |
| nflverse participation charting | against man, zone, pressure, light and heavy boxes |

Participation is published some time after a season ends, so the current season's split columns are empty until it
appears. The page says which seasons are charted. The weekly run pulls it every time and the columns fill in on the
first run after it is published. Output: `web/data/plogs/<season>.js` (loaded when a season is opened) and
`web/data/player_careers.js`. Tie check: the last complete season's logs sum to the play-by-play totals, and careers
sum to the logs.

EPA: nflverse's expected points model gives every down, distance, yard line, time and score an expected number of
points for the offense. A play's EPA is expected points after minus before. A player's EPA is the sum over his plays:
targets for receivers, carries for backs, dropbacks (passes, sacks, scrambles) for quarterbacks.

## 24. Player numbers on the official box score (24 Sep 2026)

Every player number was checked against nflverse's official player stats (`stats_player_week`, now pulled every
run as `player_stats`). The play-by-play had been read on its own terms in four places, and each is fixed:

| What | Was | Now |
|---|---|---|
| Passing yards (props, season totals, game logs) | yards on every dropback, so a sack's lost yards came off (13 yards a QB-game low in 2025) | the yards on completions, as the league and the books count them |
| Pass attempts (props grading, game logs) | sacks counted as attempts | passes and spikes, not sacks |
| Carries and rushing yards | kneel-downs left out | a kneel is a carry, as in the box score |
| Targets, receiving yards, carries | two-point tries counted | two-point tries are not plays (dropped at the source, `scheme.load_plays`) |
| Tackles in the game logs | defensive plays only | the official total, special-teams tackles included |

After the fix the 2025 game logs tie to the official stats exactly on targets, catches, carries, rushing yards,
touchdowns, completions, interceptions, sacks and every defensive column, and within 17 yards on a season of passing
and receiving yards (laterals). The tie check holds the logs and the props grading to the official file every run.

Passing yards changed what the props project, so the two constants fitted on passing yards were refit the way they
were first fitted (`experiments/props_official.py`, `reports/props_official.csv`): the team's passing yards from the
game model's expected points (2016 to 2018: 100.83 + 6.379 x expected points, was 73.77 + 6.894 on net yards) and the
median factor (2017-18: 0.88, was 0.89). Error per QB-game against the official yards: 56.60 and 56.38 on 2019-22
and 2023-25 (the old constants on the same target: 56.94 and 56.42). Receiving and rushing refits did not lower the
error on both windows, so their constants stay.

Tackle projections stay on defensive plays only, labelled as such. Books differ: bet365 counts defensive plays only,
FanDuel adds special-teams tackles (about a tenth of a tackle a game for a regular defender in 2025).

The card's Vegas win chance now comes from the newest line-watch snapshot's moneylines (ESPN moved its moneyline to a
new place in its feed, so the log had missed it and the card fell back to the schedule's). The chip under the bars is
the difference of the two rounded bars.

Teams -> Player box scores shows every player's line in any game since 2016 for both teams, from the same game logs.

## 25. The QB rating: scrambles, designed runs, and how old games fade (24 Sep 2026)

Matt asked how Jaxson Dart could rate below Jameis Winston. Two faults, one a plain bug:

1. **Scrambles were dropped.** The rating counted dropbacks with nflverse's `passer_player_id`, which is empty on every
   scramble (the league scores a scramble as a run; nflverse names the scrambler in `passer_id`). Scrambles average
   about +0.5 EPA, so every mobile quarterback was rated low: Dart's 40 scrambles at +0.71 each, none counted.
2. **Designed runs were left out.** QBR, rbsdm's composite and the 538 / nfelo QB value all count a quarterback's
   designed runs. Dart's 47 averaged +0.41 EPA; Winston's 75 averaged -0.17.

`experiments/qb_fix.py` (`reports/qb_fix.csv`), features rebuilt each time, weekly refit:

| QB rating counts | Team points 2019-22 | 2023-25 | Spread miss 2019-22 | 2023-25 | Team points 2015-18 | Spread miss 2015-18 |
|---|---|---|---|---|---|---|
| passes and sacks only (before) | 7.3587 | 7.2863 | 10.0329 | 9.9490 | 7.4108 | 9.9895 |
| + scrambles | 7.3498 | 7.2845 | 10.0240 | 9.9303 | 7.4044 | 9.9763 |
| + scrambles and designed runs (adopted) | 7.3486 | 7.2830 | 10.0174 | 9.9262 | 7.4004 | 9.9705 |

Better on every measure on all three windows. As of Week 3, 2026: Dart +0.085 per play, Winston +0.054 (before:
+0.013 and +0.032); Allen +0.204, Jackson +0.157, Hurts +0.121.

**How old games fade** was tested too, because the published models age a quarterback's games by time (PFF about
0.7 a year; nfelo and 538 regress across the offseason) while this one ages them by his own games played, so a
backup's starts from years ago keep much of their weight (Winston's 2015 to 2019 seasons). Aging by league weeks,
or counting the weeks he sat at 0.5, 0.25 or 0.10 of a game, all helped the held-out window and hurt the tuning
window's spread miss (or moved it by less than 0.001), so the rating keeps aging by games played. Shrinkage of 100
and 200 dropbacks (tested with aging by weeks) did not pass either. A draft-capital prior for young quarterbacks (538,
nfelo) is the next thing worth testing.

**How old seasons fade** was then tested once more in the form PFF uses: the per-game decay as before, times 0.9, 0.8
or 0.6 for each season back (Matt: the rating should be how he would play tomorrow, not his career). Team points
improve on all three windows at 0.8; the spread miss improves on 2023-25 and 2015-18 and slips on 2019-22, the same
standard the replacement level was adopted under, so **0.8 per season is adopted** (`ratings.DEFAULT["qb_season_fade"]`).
Winston goes from +0.054 to -0.005 per play (24th of this week's 32 starters, the median starter +0.045); Dart +0.082.
The same fade for skill players' values helped 2019-22 and hurt 2023-25, so it is not used there.

**The flag record.** Counting scrambles and designed runs alone made the 4-point record a little worse on every window
(2019-22 87-59 to 86-60, 2023-25 45-21 to 42-24, 2015-18 67-57 to 62-57); with the season fade it reads 81-56 / 41-21 /
61-59, and the chance of the held-out record by luck is about 2%. The rating now misses by less on all three windows.

The market moved the TEN at NYG line about 3 points for Dart to Winston. With the season fade the rating gap is about
0.087 per play, about 1.5 points through the refit QB coefficient (about 17 points per unit of rating), before the other inputs. The published models agree the gap is small (nfelo about 0.4 points); the books price the
starter more heavily.

## 26. Health checks on the site (24 Sep 2026)

Every tie check (the same number must read the same everywhere it appears: the page files against the reports,
the reports against the prediction table, the game logs and the props grading against nflverse's official player
stats, the cards against the line log, the season odds adding up) runs on every weekly run and every line-watch
run, every 30 minutes, and writes `web/data/health.js`. The chip beside "Last updated" reads it: green when all
pass, red with the count when anything fails or a source is late (lines or the live check older than two hours,
the model older than four days). Model -> Health checks lists what is failing, how fresh each source is, and every
check. `nflmodel/health_alert.py` keeps one GitHub issue labelled `site-health` in step: opened when a check
fails (GitHub emails the owner), updated while it stays broken, closed when everything passes.

## 27. Games a player left early (24 Sep 2026)

Matt asked whether a 5-play injury exit or a 1-play cameo should count as a game. `nflmodel/exposure.py` builds each
player's snap share in every game since 2013 from nflverse snap counts. A regular skill player plays under half his
usual snaps in about 8% of games (2.6 touches in them against 7.6 usually), so an eight-game window holds about one.

Tested (`experiments/partial_games.py`, `experiments/partial_props.py`, `reports/partial_games.csv`): counting every
game (the rule), dropping games under half his usual snaps, dropping only games under a quarter, and weighting each
game by its snap share; for the props each version had its median factors refit on 2017-18.

| Version | Game model team points 2019-22 / 2023-25 | Receiving yards 2019-22 / 2023-25 | Rushing yards 2019-22 / 2023-25 |
|---|---|---|---|
| Every game counts (kept) | 7.3486 / 7.2833 | 19.31 / 18.28 | 17.87 / 17.04 |
| Drop under half his usual snaps | 7.3485 / 7.2838 | 19.48 / 18.44 | 18.16 / 17.33 |
| Drop under a quarter | not run | 19.36 / 18.31 | 17.97 / 17.15 |
| Weight by snap share | 7.3479 / 7.2840 | 19.68 / 18.65 | 18.35 / 17.65 |

Every version is worse for the props on both windows, and the game model does not move by 0.001. The reason is in
the data: in the game after a short one, a player gets 67% of his usual touches and 65% of his usual snaps, and 37%
of the time he leaves early again (5% after a normal game). A short game usually means a lingering injury or a
smaller role, and it carries into the next week. So the short games stay in the model's inputs.

What changed is the display. A QB's dropbacks a game now averages only his starts (at least half his team's
dropbacks), and "points a game over a backup" is his value per play times the model's fitted points per unit of QB
rating, the same for every team, so neither a short game nor a blowout moves it.

## 28. When every line was pulled (24 Sep 2026)

The top of This week shows each line source's last pull in ET with its age, and the age keeps counting while the
page is open, so an old page shows how old it is. The times come from the logs (`nflmodel/pulls.py`, written into
`web/data/fresh.js` on every line-watch run and at the end of every model run), and a tie check holds them to the
newest rows in `data/lines/lines_log.csv` and `props_log.csv`. A source turns red once it is past its cadence plus
slack, and a late paid source also turns the health chip red:

| Source | Cadence | Late after |
|---|---|---|
| ESPN game lines (DraftKings) | every line-watch run | 2 hours |
| Sportsbook game lines (The Odds API) | once a day, from 8:00 AM ET | 3 hours past the next scheduled time |
| Sportsbook props (The Odds API) | Thursday 4:00 PM and Sunday 10:00 AM ET | 3 hours past the next scheduled time |
| PrizePicks, Underdog | every 6 hours | 8 hours |
| Kickoff forecasts, injuries and starters | every line-watch run | 2 hours |

GitHub's cron is irregular on this repo, so the scheduled pulls used to be missed whenever no run landed inside their
exact window (the daily sportsbook pull needed a run between 8:00 and 8:30 AM ET and missed 23 Sep; the pick'em pull
needed one on the hour every six hours). They now run at the first line-watch run after their scheduled time, once:
`data/lines/pull_state.json` records each paid attempt, so a failing pull is tried once per scheduled time, not on
every run, and the credit use is unchanged. The Thursday props pull also no longer counts pick'em rows as a recent
pull (a pick'em pull two hours earlier used to block it).

## 29. Player values audited, defenders and linemen rebuilt (24 Sep 2026)

Matt: Christian Gonzalez and Myles Garrett ranked far too low; the player values could not be trusted. Every list was
checked against its own stats and the consensus stars at each position. Quarterbacks, skill players, kickers and
punters read sensibly. Defenders and linemen did not, for these reasons:

1. **Credits summed per game, not per play.** `defender_credits` grouped a defender's credits by game, capped them at
   one, and multiplied by his first credited play's EPA: every game counted about one play (0.95 credited plays a
   game against 3.1 real ones).
2. **Snaps matched by name.** "Patrick Surtain II" in the snap counts is "Pat Surtain II" on the roster, so Surtain
   had no games at all; and a defender's game existed only if he was credited on a play, so a corner who was not
   thrown at or tackled near lost those games. The table is now every defensive snap, matched by PFR id (100% of
   2025's defensive snaps).
3. **Team changes.** A defender who changed teams was divided by his new team's snaps: 99 regulars had a share of 0
   (Garrett among them).
4. **What was measured.** Credited plays count tackles, so a tackle after a long catch or run counted against the
   tackler and a corner nobody throws at had nothing. Even with the per-play fix they add nothing to predicting a
   defense (below).
5. **Groups.** The roster's DL / LB / DB put edge rushers with nose tackles and with off-ball linebackers. Groups are
   now edge, interior line, linebacker, corner and safety (depth chart; a linebacker who pressures on 1.5%+ of his
   snaps is an edge), each with its own replacement level and its own average starter (2, 2, 2, 3, 2 per team).
6. **Old games.** The value decayed 0.99 a game with no season fade, so a game two seasons back kept about 70% weight.

**The defender value now** is what his plays were worth to the defense's EPA, per snap, weights measured on 2016-18
plays so both test windows stay untouched: coverage yards saved against the league's yards per target (0.095 EPA a
yard, the EPA of a completion yard), interceptions (3.6 EPA over an incompletion), sacks (2.05) and other pressures
(0.39) from Pro Football Reference, run stops (the -EPA of runs he is credited on that lost the offense EPA) and
forced fumbles. Recency 0.92 a game and 0.8 a season back.

**Tested** (`experiments/def_value.py`, `def_value_decay.py`): each team-game's defensive EPA per play from the team's
own prior plus the snap-weighted values of the defenders who played it, leave-one-season-out in each window.

| Error, defensive EPA per play | 2019-22 | 2023-25 |
|---|---|---|
| Team prior only | 0.20199 | 0.21174 |
| + credited plays (old value, per-play fix) | 0.20197 | 0.21187 |
| + new value | 0.20144 | 0.21104 |
| + new value, recency 0.92 / 0.8 | 0.20052 | 0.21076 |

Pass plays alone: 0.30286 / 0.31438 against 0.30490 / 0.31576. As a game-model input (defenders out, own or opponent,
`experiments/def_value_out.py`) it is worse on both windows, so it stays a Players-tab value.

**Offensive linemen** are rated with their unit in the snaps they played: pressures allowed per dropback (0.84 EPA a
pressure) and rushing yards before contact per carry (0.135 EPA a yard) against the league, from PFR. No public data
splits a line's blocking by player; the on/off split it replaced put every lineman who never missed a game at exactly
zero. It does not predict an offense beyond the team's own history (`experiments/ol_value.py`), which is what a unit
measure made from the team's numbers should do, so the page labels it a unit rating.

Health checks added: every rostered defender with 300+ snaps last season has a value; the defender table holds 97%+ of
last season's defensive snaps; no regular defender has a snap share of 0.

## 30. Cornerbacks against the consensus (24 Sep 2026)

Matt: the corner list was nothing like a consensus view (Nahshon Wright 2nd, Surtain 27th, Sauce Gardner 109th). Per
snap, a corner's value swung with how often he was thrown at, and the fast fade (0.92 a game) rode a few games.

Two yardsticks (`experiments/cb_value.py`, `reports/cb_value.csv`), so no single list is fitted: the confirmed 2026
consensus ranks (FOX Sports' top 10; PFF's top 32 where confirmed), and each corner's rating before a season against
his coverage per target that season, on both windows.

| Variant | Next season 2019-22 | 2023-25 | Consensus 17 in our top 15 | Median rank |
|---|---|---|---|---|
| Per snap, every part, 0.92 / 0.8 (was) | 0.142 | 0.178 | 4 | 54 |
| Per target, 0.99 / 1.0, K150 (adopted) | 0.191 | 0.184 | 7 | 36 |
| Per target + draft-round prior + run share | 0.148 | 0.194 | 9 | 13 |

Adopted: coverage per target (coverage yards saved and interceptions, in EPA, over targets plus 150), times the
league's corner targets per snap, 0.99 a game with no season fade; best on 2019-22 and better held out. The draft-round
prior matches the consensus lists more closely and is the best held out, but not on 2019-22. Corner coverage is noisy
(a season's rating predicts next season's coverage at about 0.19 correlation), which is also why published lists
disagree: PFN's stats-only ranking has James Pierre second. Corners valued more for run defense and blitzing than
coverage (Witherspoon, DeJean) sit lower here than in film-based lists.

## 31. Every defensive group against the All-Pro teams; player ids instead of names (24 Sep 2026)

**Yardstick.** The AP All-Pro first and second teams since 2016 (`data/reference/allpro.csv`, parsed from the
Wikipedia pages the `reference pages` workflow saves monthly; all 437 selections matched to gsis ids) and the
published 2026 rankings (PFF, FOX, SI; `data/reference/consensus_2026.csv`). `experiments/allpro_check.py` values
every regular in each group at each season's end and asks where that season's All-Pros land, on 2019-22 and 2023-25.
Per group, the variant best on 2019-22 among those better than the old one on both windows was adopted
(average percentile of the All-Pros in our list, 2019-22 / 2023-25):

| Group | Before | Adopted | After |
|---|---|---|---|
| CB | 0.791 / 0.768 | coverage per target, 0.99 a game (section 30) | 0.892 / 0.835 |
| S | 0.816 / 0.777 | coverage per target plus half the run stops and pass rush per snap | 0.865 / 0.850 |
| LB | 0.812 / 0.779 | every part per snap plus 0.75 EPA per credited play, 0.98 / 0.9 (weight swept 0.1 to 1.5) | 0.878 / 0.816 |
| EDGE | 0.913 / 0.951 | every part per snap, 0.98 / 0.9 | 0.927 / 0.956 |
| IDL | 0.932 / 0.890 | run stops and pass rush per snap (half) plus coverage per target, 0.99 | 0.957 / 0.907 |

Receivers, backs and tight ends were checked the same way (`experiments/allpro_skill.py`) and already agree: the
All-Pros' median rank is 3 to 6 on both windows. A lighter shrinkage (120 or 60 touches against 480) agrees a little
better but would split the displayed value from the one the game model uses and was left alone; first-year players
(Nacua in 2023, Bowers in 2024) rank low in their first season because 480 touches of shrinkage outweigh one season.

**Ids, not names.** Names had failed three times (Pat Surtain II missing from the defender table; Garrett-style
misses). Every join now uses an id where one exists: the snap counts' PFR id through the rosters' pfr_id; injury
reports and roster statuses by gsis id (the game model's snaps-out inputs had joined them by name: 162 of 7,668
team-games changed on offense, 225 on defense; flag at 4 now 82-57 / 41-21 / 62-61 against 81-56 / 41-21 / 61-59,
team points better on both windows); ESPN's injury page by its athlete id against the roster's espn_id; the roster
view's last-game snap share by PFR id. Sportsbooks send names only, so each book name is resolved against the two
teams' rosters (exact, the roster nickname, a last name unique on the two teams, reversed order, a short alias list):
99.6% of this week's book players resolve, and a health check fails under 99% and names the misses.

## 32. Linemen by id; the offensive line against PFF (24 Sep 2026)

**Linemen were still matched by name.** The weekly rosters carry no PFR id for any offensive lineman, so section 31's
id join fell back to the name for every lineman, league-wide: 579 lineman games went to a namesake (two Connor
McGoverns, the 2020 center Aaron Brewer and a 2012 long snapper, two Spencer Browns, two Josh Joneses) and 1,411
were dropped. `nflmodel/ids.py` is now the one PFR-to-gsis map every PFR join uses (snap counts, PFR advanced
stats, the exposure table, the game logs, the roster view, the injury inputs): the rosters first, then nflverse's
players table (pulled every run) for the ids the rosters lack; where the two disagree (six ids) the one whose name
matches the snap counts wins. A PFR id no table knows falls back to the name only where it is unique on that team's
roster that season, never league-wide. 99.9% of snap rows now match by id; a health check fails when any position
group falls under 99%. 27 more linemen now have a value. The game model's snaps-out inputs use the same map, so a few games a season changed
(linemen out now counted by id): margin miss 10.0324 to 10.0300 on 2019-22 and 9.9141 to 9.9137 on 2023-25 (2015-18
9.9604 to 9.9620); the flag at 4 is now 81-55 / 40-23 / 61-58 against 82-57 / 41-21 / 62-61. A data fix, better on
both windows on the measure the model is fitted to, so kept.

**Docs tables written by the run.** The threshold table (section 9), the rule table, the by-week table (section 14)
and the staking table are now rewritten by `nflmodel/report.py` on every run, between `auto` markers, like the
README's results block, which the run now writes before the tie check reads it (it was written after, so the check
compared a run-old README). The staking table had been a run behind unnoticed.

**Build order.** The Players tab's history was built before the run's defender, kicker and lineman tables, so any fix
to them reached the history a run late. It is now built after them (and includes linemen), and a health check fails
when a player table is older than a table it reads.

**Against PFF's 2026 line rankings** (`experiments/ol_vs_pff.py`, `reports/ol_vs_pff.csv`): rank agreement 0.46 for
the unit rating, 0.62 for the roster view (the sum of the current top five linemen's values). The biggest gaps are
lines PFF projects healthy that played hurt (Chargers, Vikings, Raiders) and lines helped by running quarterbacks:
yards before contact counts quarterback runs (Ravens, Commanders). Counting only non-quarterback carries raises the
agreement to 0.55 and improves the All-Pro linemen's median rank on both windows (36.6 to 32.5, 57.7 to 51.7;
`experiments/ol_allpro.py`), but their average percentile, the measure used for every other group, is 0.712 to
0.710 on 2019-22 and 0.645 to 0.668 on 2023-25: not better on both windows, so not adopted. The unit rating stays a
unit rating: every lineman on a line shares it per snap.

## 33. Who a player faced: opponent-adjusted values (24 Sep 2026)

EPA per play is nflfastR's expected points added: each play scored by down, distance, yard line and time before and
after it. It does not know the defense. `experiments/opp_adjust.py` re-scores every past game against an average
defense (the game's EPA less the opponent defense's EPA allowed per pass play, or per run for a rusher, coming into
that game, against that season's league) and asks which rate predicts the player's next game. Error lower than the
raw rate (percent, 2015-18 / 2019-22 / 2023-25):

| Role | Past games adjusted | Next opponent added too |
|---|---|---|
| Passers | 0.23 / 0.17 / 0.13 | 1.35 / 1.48 / 1.15 |
| Receivers | 0.19 / 0.25 / 0.17 | -0.85 / 0.11 / -0.78 |
| Rushers | 0.93 / 0.18 / 0.35 | -1.58 / -0.36 / -1.36 |

Adjusting a player's past games is better for every role on every window, so player pages show it ("Against an
average defense"). Adding the next opponent helps passers and hurts receivers and rushers; the game model already has
the opponent defense as an input, so no matchup term is added to player values. In the game model (skill players
listed out, `experiments/opp_adjust_model.py`) the adjusted values made no difference that passes both windows (margin
miss 10.0324 both ways on 2019-22, 9.9141 against 9.9143 on 2023-25), so the model keeps the raw values.

## 34. Players, teams and season totals, reorganized (24 Sep 2026)

**Player pages** are in sections: Summary (value, rank at his position, this season, season projection, value by
season), Game log (every stat, the full box score, career), Matchups and schemes (`nflmodel/player_splits.py`: every
target, carry or dropback split by coverage, each coverage family, blitz, pressure, box count, play action, motion,
formation, personnel, down, red zone and score; this season, last season and since 2016; plus every opponent),
Tracking (NFL Next Gen Stats by season: time to throw, air yards, CPOE, separation, cushion, YAC and rush yards over
expected), Projections, Injuries. The Players list splits receivers, backs and tight ends.

**Teams**: the Overview sub-tab is gone (each part repeated another tab); its record, power, points and next game sit
above every Team sub-tab. The Roster opens first, with a table of everyone the model prices as unavailable and why
(`players.unavailable_reasons`: this week's league report, ESPN's injury page matched by its athlete id, the last report
that listed him, the reserve list and the week the stint began; roster codes R01 IR, R48 IR designated to return, R04
PUP). The Scheme tab shows last season beside this one: coverage, pressure, time to throw and personnel come from the
participation file, which nflverse publishes after each season; this season's time to throw now comes from Next Gen
Stats. Splits under 20 plays show greyed rather than blank.

**Season totals at a point in time**: Season -> Player totals -> "As projected at the time" shows every backtest
snapshot (before Week 1, going into Weeks 5, 9, 13, 2016 to 2025) with what each player finished with, and this
season's every week (`data/tracker/player_season_snapshots.csv`, kept as made). Before Week 1 the projection has only
last season's games and flags no breakout; the books' season-long player lines have no free archive to score against.

Preseason offseason information was tested (`experiments/preseason_totals.py`, `reports/preseason_totals.csv`): age,
a team change, the team's vacated volume, the player's share of it, years in the league and a season before last,
fitted on 2017-18. None beat the plain Week 1 projection on both windows, so the preseason number stays last season
carried forward, and no breakout is flagged before Week 5.

**Against the books' win totals** (`nflmodel/wintotals.py`, `reports/win_totals_vs_vegas.csv`): before Week 1 the
books missed a team's final wins by 2.06 / 2.32 (2019-22 / 2023-25), the model by 2.17 / 2.54. They agree closely
(correlation 0.87 / 0.85), their average does not beat the books, and the model's side at a win or more off the line
went 30-28-3. The market is the better preseason number. Only the preseason line is archived, so the model's weekly
re-pricing cannot be scored against the market.

## 35. Season totals game by game, accuracy in percentages, the books' season markets (24 Sep 2026)

Projecting each remaining game on its own (the defense's allowed yards per touch, the opponent's pace, the game
model's expected margin and total; `experiments/season_by_game.py`) moved the season-total miss by under a yard on
every kind and window, so the season total stays one per-game number over the games left. Accuracy is now shown as
shares: a season total within 10% and 20% of the final, and for teams wins within 1 and 2, the playoff call (50%) and
the division favorite. `nflmodel/futures.py` fetches ESPN's futures feed (DraftKings) and The Odds API's outright
markets once a day; the Season tab shows the books' Super Bowl, conference and division chances (margin removed)
beside the model's, and each player's chance to lead the league in yards. Every number on Season → Team odds and
Player totals shows its math under its column on a click (wins = record + the chance in each game left; each share =
the runs out of 10,000; a player's total = his rate, his own projection, pace and the blend).

## 36. Who plays, how his role moves, and the offseason (25 Sep 2026)

Four accuracy projects, our own data only (the books stay the benchmark, never an input), each adopted only if better
on 2019-22 and 2023-25.

**Adopted: player lines move with this week's injury report and his snap trend** (`experiments/props_backtest13.py`).
A receiver listed Questionable gets 0.907 of his line, one with a limited practice 0.913; a Questionable rusher 0.928
(each group's actual over line against unlisted players', fitted on 2017-18). Then the line moves a quarter of the way
by his offensive snap share over his last 3 games against his last 10 (clipped 0.4 to 2). Receiving yards 19.31 /
18.28 → 19.28 / 18.26 per player-game; rushing 17.86 / 17.04 → 17.81 / 17.03. Passing: the snap trend was worse at
every weight, so it is left alone. His target or carry share over the last 3 games (role momentum) was worse on both.

**Not adopted:**
- Games played for season totals (`experiments/availability.py`): the report, practice, share of games played this
  season and last, two seasons of injury history and age predict games played better (receivers 2.72 → 2.37 games
  off), but the season total comes out mixed (within 20% worse on 2023-25).
- Offseason signals in Weeks 1 to 8 (`experiments/team_signals.py`, `reports/team_signals_a3.csv`): a new starting
  QB, a new head coach, the share of last season's line snaps returning. Each, and all three, made the margin worse
  on both windows.
- Finer team ratings (`reports/team_signals_a4.csv`): pass and rush EPA split, success rate. Success rate helps the
  margin on both windows (10.030 → 10.025, 9.914 → 9.907) but worsens team points on 2019-22 and 2015-18; the split
  worsens team points on 2019-22.

## 37. Seven models averaged; the referee in the totals (25 Sep 2026)

The rule for a change is unchanged in spirit (it must not just fit one stretch of seasons) but is scored on bets won as
well as the miss. `experiments/bet_wins.py` priced every game of 2015-2025 under several models at once.

**Adopted: team points are the average of seven models**, each refit every week on the same games: the live equation,
three equations with one more set of ratings (success rate; pass and rush EPA; plays per game), the live inputs with
less and more shrinkage, and gradient-boosted trees on the live inputs. The card's breakdown still shows the equation
term by term, then one line, "Six more models, averaged in", which opens to each model's number.

| | 2015-18 | 2019-22 | 2023-25 |
|---|---|---|---|
| Margin miss, live equation | 9.962 | 10.059 | 9.942 |
| Margin miss, seven-model average | 9.949 | 10.047 | 9.929 |
| 4+ flag, live equation | 61-58 | 81-55 | 40-23 |
| 4+ flag, seven-model average | 68-55 | 80-50 | 40-21 |

The gain held with every tree setting tried (`experiments/bet_wins_gbm.py`). The trees alone miss by more but at a
5-point edge went 95-66, 84-60 and 34-17; that rule is logged and graded live beside the flag, never bet.

**Totals:** the referee's over rate (prior games, shrunk) joins the total equation: the miss fell on all three windows.
The totals flag stays retired: across every model and cut, 2023-25 lost.

## 38. The totals flag, and why overs lose (25 Sep 2026)

Game totals are lopsided: a few shootouts pull the average up, so the typical game lands about half a point under the
book's number while the average lands 0.4 over, and unders win 51.3% of games at the close. The total equation
predicts the average, so its over calls were right on average (+0.7 points over the line) and still lost more than
they won (49.5%). It also learns the league's scoring level from past seasons, so it kept calling overs through the
scoring drops of 2017, 2022 and 2023.

The flag now reads the chance of the under off the real spread of totals (the training games' own misses, shifted to
this game's predicted total) and flags an under at 55% or more: 159-130, 202-150 and 68-61 on 2015-18, 2019-22 and
2023-25, positive at every cut from 54% to 56%. It is graded live beside the spread rules and not bet until it holds
on live games; 2024 and 2025 were losing seasons for it. No over rule tried (median totals, a league-scoring input,
trees, a fitted chance, pace, roof, wind, passing strength) won on two windows (`experiments/totals_fix.py`).

Every setting was also re-swept (`experiments/sweep_all.py`, `sweep_confirm.py`): fade speed, last season's weight,
the pull toward average, the QB rating's settings, the training window and weights, the penalties, and the blend's
weights. None beat today's settings on both the miss and the bets.

## 39. Team scores add up to the game total (25 Sep 2026)

The spread (seven models averaged) and the total (the total equation) were priced apart, so the two team scores
added up to about 1.9 points off the game total on average. Each team's score is now split from the two numbers
that are priced and bet: home = (total + spread) / 2, away = (total - spread) / 2. The spread and total do not move;
the team-points miss goes 7.381 / 7.340 / 7.268 to 7.398 / 7.353 / 7.259 on 2015-18 / 2019-22 / 2023-25. The card's
breakdown shows the step as one line, "Matched to the game total".
