# How NFL Model 3.0 works, end to end

Everything the model does, why, and with what numbers. Written 21 September 2026. Code references are the
files in `nflmodel/`; every number below comes from `reports/`.

## 1. What is built in today, and what is not

| Thing | Status | Where |
|---|---|---|
| Recent form vs whole season | Built in. Every game is weighted by age: 0.90 per week, so a game 8 weeks old counts 43% of last week's. Fit, not picked (section 4) | `ratings.py` |
| Last season | Built in. Last season's games count at half weight and keep decaying, so Week 1 is mostly last year pulled toward average, and this season takes over by about Week 5 | `ratings.py` |
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

- **Age.** Weight = 0.90 to the power of weeks ago. Last week 1.0, four weeks ago 0.66, eight weeks ago 0.43,
  the whole of last season 0.10 to 0.15 after the offseason multiplier.
- **Offseason reset.** Last season's games are multiplied by 0.5 on top of their age, so a team starts the
  year at roughly half of last year's rating pulled toward average, and each new game moves it. This is the
  fix for the Week 2 problem (KC at 93%).
- **Pull toward average.** A ridge penalty of 16 (in game-weight units) shrinks every rating toward zero.
  After one game a team's rating is about 6% of what that one game would say; after four games about 20%;
  by midseason the current season dominates. Defense is shrunk hardest in effect because defense stats are
  the noisiest (section 5).

The three numbers (0.90, 0.5, 16) were chosen by grid search on 2019 to 2022 points miss
(`reports/tuning_ratings.csv`, 35 settings). The spread across all settings is only 0.04 points, so the
model is not sensitive to them; a nearly flat weighting (0.99) was the worst.

**QB rating.** For the named starter, EPA per dropback over every game he has played (any team), decayed
0.985 per game, shrunk toward -0.05 (replacement level) with a 150-dropback prior. A rookie with no
history starts at replacement level. Ablation: dropping it costs 0.08 points of miss, the most of any
input (`reports/ablation.csv`).

## 4. From ratings to points: the regression

`model.py` fits a ridge regression (penalty 10, inputs standardised) from the ratings and situation each
team carried into a game to the points it scored. Inputs and what they were worth (fit on 2013 to 2022,
points per one standard deviation of the input, from `reports/v3_coefficients.txt`):

| Input | Points per SD | Reading |
|---|---|---|
| Starting QB rating | +1.52 | A QB one SD above average adds 1.5 points a game to his team |
| Own offense points rating | +1.09 | |
| Home | +0.94 (1.88 points home vs away) | League home field, 2013 to 2025 |
| Opponent defense points rating | -0.85 | |
| Wind (outdoor) | -0.74 (-0.13 per mph) | |
| Own offense EPA per play | +0.65 | |
| Opponent defense EPA per play | -0.53 | |
| Opponent offense EPA per play | -0.44 | Good opposing offenses hold the ball; fewer possessions for you |
| Opponent defense pace (plays allowed) | -0.43 | |
| Division game | -0.37 (-0.78 points per team) | |
| Short week (Thursday) | +0.35 for the short-week team, -0.26 for its opponent | |
| Own rush EPA rating | +0.23 | |
| Own defense EPA | +0.19 | Good own defense gives the offense field position |
| Own pass EPA rating | -0.18 | Negative because overall EPA already carries it (collinear) |
| Opponent QB rating | -0.17 | |
| Dome | +0.13 | |
| Primetime | -0.13 | |
| Off a bye | +0.09 | |
| Cold under 35F | +0.02 | |

The regression is refit every season on all seasons before it (2013 to S-1), so a 2024 prediction has never
seen a 2024 game. Two expected scores per game give the spread (home minus away) and the total.

**Ablation** (`reports/ablation.csv`, drop one group at a time, 2019 to 2022 points miss): QB +0.080,
weather/dome +0.040, points ratings +0.017, EPA ratings +0.008; rest, division, primetime, pace within 0.007
of zero; success rate -0.013 (dropped); pass/rush split 0.000 (kept for the matchup display only).

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

## 7. The old model, for comparison

`baseline.py` is the Google Sheet formula for formula: seven tabs (OVERALL, 2.0, LAST 3, HOME/AWAY, PF/PA,
two last-year tabs), each computing offense strength x opponent defense strength x league average x home
factor from both the points-for and points-against side, blended 10/35/35/15/5/0/0, then the Poisson grid.
Strength indexes are the sheet's own: the teamrankings one (3 PPG + RZ TD + rating - 2 giveaways + ... over
4.5) and the 2.0 one (ten PFR stats weighted by same-season correlation). Run walk-forward on the same games
it is 49.4% against the spread over 2019 to 2025 and misses team points by 9.0 against 3.0's 7.3.

## 8. Betting thresholds: what the sweep says

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

## 9. Your method and this one, piece by piece

Your sheet did one thing that this model keeps exactly: each team's expected score is its offense strength
against the opponent's defense strength, scaled to the league scoring level, adjusted for home, blended
across recent form and the season. What changes is where each number comes from.

| Piece | Your sheet | 3.0 | Why the change |
|---|---|---|---|
| Choosing stats | Correlation of each stat with wins, spread and points over about five seasons, same-season | Correlation of each stat through Week 8 with points in Weeks 9 to 17 (predictive), then an ablation that removes each input and measures the miss | Same-season correlations reward outcomes (PF, red zone TD%, Sc%) that do not repeat. Red zone TD% is 0.47 same-season and 0.19 predictive. EPA per play is the best predictor at 0.50 |
| Stat weights | The correlations themselves, 3x on PPG in the OVERALL index | Fitted by ridge regression on 14,000 team-games, refit every season | Lets the data set the weights and shrinks the ones that do not earn their place |
| Opponent adjustment | None: a team's stats were taken as is | All 32 offenses and defenses solved together | Stats against bad defenses count less |
| Recent form | LAST 3 tab at weight 35, whole season at 35 + 10 + 5 | One decay curve, 0.90 per week, fit by grid search | A fixed last-3 window throws away the fourth game and treats the third as equal to the first |
| Last year | Weight 0 by Week 2 | Half weight, decaying, pulled toward average | Week 1 and 2 ratings on one game are mostly noise; last year at 0.4 to 0.5 of face value is what the data says |
| Home field | 0.92 / 1.08 on OVERALL, 0.98 / 1.02 elsewhere, hand-set | One fitted number, 1.9 points, plus fitted rest, wind, dome, division, primetime | The multipliers were guesses; a 1.08 on a 24-point team is 1.9 points, so they were not far off, but only on one tab |
| Home/away splits | HOME/AWAY tab at weight 15 | Tested, not used | Split stats double the noise and did not help |
| QB | Not in the model (injuries typed by hand) | The starter's own career EPA per dropback, plus a QB-out flag | Biggest single input, 1.5 points per standard deviation |
| Win % | Poisson grid | Normal on the margin with key-number weights, calibrated | The grid said 91% for favourites that won 66% |
| Cover % | Not computed | Both sides on every game, at the current line | |
| Bet rule | 3 points on spreads, 4 to 5 on totals | 5 and 6, the ROI-best thresholds that hold in both windows, with the sample size shown | Under 4.5 lost in every window |
| Refs, coaches, head-to-head, weather teams | Typed in from memory and sites | Computed as-of, tested, shown with a label | None of them improved the score; refs and coaches do not persist |
| Tracking | SLIP tab by hand | Graded automatically, model picks and your bets kept apart (Phase 5) | |

## 10. Verification

`verify.py` runs after every data rebuild (`reports/verification.md`). It checks the 2024 season totals
from play-by-play against the Pro-Football-Reference table that was pasted into your sheet, 24 stats for 32
teams: points, completions, attempts, passing yards, passing TDs, interceptions, rushing TDs, third- and
fourth-down attempts and conversions are exact for all 32; plays, turnovers and rush attempts within one;
first downs and red zone within two; drives within two (PFR has its own drive-counting rules). It also
checks that every team-game's points equal the schedule score (7,720 rows, 0 mismatches) and that what
one offense gained equals what the other defense allowed (0 mismatches). The first pass found real errors
(pass attempts counted sacks and two-point tries, return fumbles were charged to the kicking team) and they
are fixed.

## 11. What would make it a real edge

In order of what the data says: (1) bet at the opener or midweek and measure closing line value, which needs
the line log that starts in the first live week; (2) price injuries and the player model before the line
moves; (3) splits and reverse line movement after a season of logging. None can be tested on today's data.
