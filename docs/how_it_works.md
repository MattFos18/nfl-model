# How NFL Model 3.0 works, end to end

Everything the model does, why, and with what numbers. Written 21 September 2026. Code references are the
files in `nflmodel/`; every number below comes from `reports/`.

## 1. What is built in today, and what is not

| Thing | Status | Where |
|---|---|---|
| Recent form vs whole season | Built in. Every game is weighted by age: 0.94 per week since 22 Sep 2026 (0.90 before), so a game 8 weeks old counts 61% of last week's. Fit, not picked (section 4) | `ratings.py` |
| Last season | Built in. Last season's games count at 0.8 weight (0.5 before 22 Sep 2026) and keep decaying, so Week 1 is mostly last year pulled toward average, and this season takes over by about Week 7 | `ratings.py` |
| Opponent strength | Built in. Ratings are solved jointly, so an offense that scored on bad defenses is marked down | `ratings.py` |
| Starting QB | Built in. The schedule names each starter; his own EPA per dropback over his career (decayed, shrunk) is the single biggest input. A QB change moves the number the moment nflverse lists the new starter | `ratings.py`, `model.py` |
| Home field | Built in as one fitted league number, 1.9 points. Team-specific home edges were tested (each team's home-minus-away margin over three seasons, shrunk) and made the points miss worse, so they are shown but not used | `model.py`, `trends.py` |
| Rest, short week, bye | Built in as fitted adjustments (short week +1.5 for the team on it, -1.1 for its opponent, off a bye +0.3) | `model.py` |
| Dome, wind, cold | Built in. Wind is -0.13 points per mph for an outdoor game (a 15 mph day takes 2 points off each side); dome +0.3; cold under 35F +0.07. Uses the game-time weather in the schedule file for past games. For upcoming games nflverse has no forecast yet, so the model uses the median wind until the kickoff forecast pull (Open-Meteo) is added in Phase 5 | `model.py` |
| Division game, primetime | Built in as fitted adjustments (-0.8 and -0.3 points per team). Both small and neutral in the ablation | `model.py` |
| Injuries | Partly. QB out (previous game's starter listed Out or Doubtful) is in, on top of the QB rating. Starters out on offense and defense (50%+ snaps last game, now Out/Doubtful) were tested and did not move the score, because a player out for weeks is already out of the ratings and the count only catches new absences. Full player model is Phase 6 | `trends.py` |
| Referees | Computed (over rate, home cover rate, penalty rate, all as-of and shrunk) and shown as noise. Failed both tests: no persistence across periods (top-five over refs 52.6% then 48.4%) and no gain in the regression | `trends.py` |
| Head-to-head history | Computed (last six meetings' cover margin, shrunk) and shown as weak: it does persist across periods (+0.36) but adds nothing to the score once the ratings are known | `trends.py` |
| Coach and QB against-the-spread records, off a loss | Computed and shown as noise. Coach cover rates do not persist (top five 56.8% then 47.6%), QB cover rates do not (56.2% then 47.7%), and neither helps the score. 'Off a loss' adds nothing | `trends.py` |
| Team-specific weather performance | Computed (each team's margin in cold or windy games minus its other games, shrunk, applied when this game is cold or windy) and rejected: it raises the miss. Wind and cold themselves stay in | `trends.py` |
| Home/away split stats | Tested as the old sheet's HOME/AWAY idea (home-minus-away EPA per play, shrunk): raises the miss, not used. Late-window slot and the West Coast-at-1pm body clock: same result | `trends.py` |
| Line movement, splits, sharp money | Not built in. Nothing to backtest with: nflverse stores closing lines only. The line log starts in the first live week | |
| Old sheet stats (passer rating, red zone TDs, Sc%, ANY/A and so on) | Computed in `features.py` and used by the baseline copy of the old model. Not in 3.0, because EPA per play predicts future points better than each of them (section 5) | `baseline.py`, `lab.py` |

So: recent trends, last year, opponent adjustment, QB and QB out, home, rest, weather and the situational adjustments
are in. Referees, head-to-head, coach/QB angles, per-team home and weather edges and starters-out were all built,
tested and left out of the score because they made it worse or no better; they are still computed every week so
the game card can show them, labelled noise or weak. Market signals wait on the line log.

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
0.985 per game, shrunk toward -0.05 (replacement level) with a 150-dropback prior. A rookie with no
history starts at replacement level. Ablation: dropping it costs 0.08 points of miss, the most of any
input (`reports/ablation.csv`).

## 4. From ratings to points: the regression

`model.py` fits a ridge regression (penalty 10, inputs standardised) from the ratings and situation each
team carried into a game to the points it scored. Since 22 Sep 2026 the model has eighteen inputs, each with one
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

Two expected scores per game give the spread (home minus away) and the total. The QB rating and the offense
ratings overlap (correlation 0.68) and the regression sorts that out: drop the QB and refit, and the offense EPA
coefficient rises from 0.6 to 1.4 per SD, so the credit is shared, not counted twice.

**Why eighteen and not twenty-six.** Until 22 Sep the model also carried the pass and rush EPA splits, pace, the
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
EPA came out negative because EPA per play already carries it. Eighteen inputs a reader can check beats twenty-six that
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

The production build with weekly refit (`reports/backtest_v3.md`, the History tab) grades the same rule at 64-56 (53.3%) over
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

**Update, 22 Sep 2026, on the twelve-input model.** The sweep below is from the first build and is kept for the record; the live
sweep, recomputed from the backtest on every run, is on the History tab (Every threshold, tested). On the current model, spread
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
moves; (3) splits and reverse line movement after a season of logging. None can be tested on today's data.

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

**The line watch without GitHub's cron.** GitHub never fired the scheduled line watch on this repository. The
workflow now also runs on any push to the branch `kick`, and a standing Claude routine pushes an empty commit
there every hour. GitHub's cron, if it ever starts, simply adds runs.

## 15. The player model

Phase 1 (`nflmodel/players.py`, `data/processed/player_games.parquet`): one row per game, team, player and role
(passer, rusher, receiver) from the play-by-play since 2013, with plays and EPA; about 95,000 rows, 2,400 players.
`PlayerValues` gives any player a decayed (0.985 per game), shrunk (k = 80 touches) EPA per play as of a week,
toward a replacement level set at the 25th percentile of players with 100+ plays in earlier seasons.

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
carried or was targeted on, decayed 0.985 per game and shrunk toward replacement level with 80 touches of weight
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

So the model has eighteen inputs: the pair went in (flags 48-40 and 29-18 against 42-35 and 28-19 without).
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
| RB, WR, TE | EPA per carry or target (phase 1) | touches | share of the team's touches, last eight games on any team |
| Offensive line | on/off: team EPA per play in games he played 50%+ of the snaps minus the team's games without him, last 34 games, shrunk by the smaller side's games | games | snap share |
| Defense | impact plays: the EPA taken away on every play he is credited on (tackle 1, assist 0.5, tackle for loss +0.5, sack 1, QB hit 0.5, pass defended 1, interception 1, forced or recovered fumble 0.5; one credit per play at most), per defensive snap; decayed 0.99, shrunk with 300 snaps | defensive snaps (snap counts, matched by name) | snap share |
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
