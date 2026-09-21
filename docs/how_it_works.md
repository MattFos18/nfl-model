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
| Home field | Built in as one fitted league number, 1.9 points. Team-specific home edges (Denver and so on): not yet | `model.py` |
| Rest, short week, bye | Built in as fitted adjustments (short week +1.5 for the team on it, -1.1 for its opponent, off a bye +0.3) | `model.py` |
| Dome, wind, cold | Built in. Wind is -0.13 points per mph for an outdoor game (a 15 mph day takes 2 points off each side); dome +0.3; cold under 35F +0.07. Uses the game-time weather in the schedule file for past games. For upcoming games nflverse has no forecast yet, so the model uses the median wind until the kickoff forecast pull (Open-Meteo) is added in Phase 5 | `model.py` |
| Division game, primetime | Built in as fitted adjustments (-0.8 and -0.3 points per team). Both small and neutral in the ablation | `model.py` |
| Injuries beyond the QB | Not built in. The injury report is downloaded (`pull.py`) but not used. Planned as the player model in Phase 6 | |
| Referees | Not built in. Tested and failed the persistence test (under trends went from 61% to 49% across periods). Will be shown on the game card as noise, not used | `reports/decision_log.md` |
| Head-to-head history | Not built in. Not tested yet; the plan marks it as likely noise | |
| Coach and QB records in primetime, off a loss, as favourite or dog | Not built in. Not tested yet; small samples | |
| Team-specific weather performance (cold-weather teams and so on) | Not built in. Not tested yet | |
| Home/away split stats | Not built in as separate ratings. The old sheet had a HOME/AWAY tab; 3.0 uses one home-field number plus the fitted adjustments. A test of team-specific home edges is on the list | |
| Line movement, splits, sharp money | Not built in. Nothing to backtest with: nflverse stores closing lines only. The line log starts in the first live week | |
| Old sheet stats (passer rating, red zone TDs, Sc%, ANY/A and so on) | Computed in `features.py` and used by the baseline copy of the old model. Not in 3.0, because EPA per play predicts future points better than each of them (section 5) | `baseline.py`, `lab.py` |

So: recent trends, last year, opponent adjustment, QB, home, rest, weather and the situational adjustments
are in. Injuries beyond the QB, referees, head-to-head, coach/QB angles and market signals are not.

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
| 3+ | 464, 50.6%, -3.3% | 250, 51.2%, -2.3% | 214, 50.0%, -4.5% |
| 4+ | 257, 50.6%, -3.4% | 148, 51.4%, -2.0% | 109, 49.5%, -5.4% |
| 4.5+ | 182, 52.7%, +0.7% | 97, 52.6%, +0.4% | 85, 52.9%, +1.1% |
| 5+ | 131, 54.2%, +3.5% | 69, 53.6%, +2.4% | 62, 54.8%, +4.7% |
| 6+ | 65, 60.0%, +14.5% | 34, 61.8%, +17.9% | 31, 58.1%, +10.9% |
| 7+ | 37, 56.8%, +8.4% | 24, 62.5%, +19.3% | 13, 46.2%, -11.9% |

Totals: 5+ is 149 bets, 52.3%, -0.1% (the two windows disagree: -6.6% then +10.5%); 6+ is 57 bets, 61.4%,
+17.2% (+9.1% then +30.2%).

Reading: bets where the model is within 4 points of the line lose at every threshold in every window. Bets
where it disagrees by 5 or more win in both windows, and by 6 or more win big in both, but on 65 bets over
seven seasons, about nine a year. The bootstrap (2,000 resamples) puts the chance that the 5+ spread ROI is
really above zero at 69% and for 6+ at 87% (totals 6+: 93%); the plan's bar is 95%. So the display rule is now 5 for
spreads and 6 for totals (the ROI-best thresholds that hold in both windows), with the sample size printed
next to every pick, and the 3 point rule is retired. It is a lead, not a proven edge. The 5+ bets split
by side: home 52.8% on 303 bets at 3+, away 46.6% on 161; favourites and dogs the same.

## 9. What would make it a real edge

In order of what the data says: (1) bet at the opener or midweek and measure closing line value, which needs
the line log that starts in the first live week; (2) price injuries and the player model before the line
moves; (3) splits and reverse line movement after a season of logging. None can be tested on today's data.
