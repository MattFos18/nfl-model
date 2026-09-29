# Situational ideas for the game model, under the round-3 rule (29 Sep 2026)

`experiments/situational_game.py` (engine, ideas, runs), `experiments/situational_feats.py` (the inputs), `experiments/situational_report.py` (this page). Full numbers for every row: `reports/situational_game.csv`.

**Verdict: nothing is adopted.** 121 ideas were added to the live model one at a time (85 in the points equation, 36 in the total equation) across six families, and 13 live terms were re-checked by dropping them, all on 2015-18, 2019-22 and 2023-25 with the weekly refit. Seven ideas lower the team points miss on all three windows (rule 1), fewer than the fifteen that chance alone would hand over at one in eight. Six of those seven cost a bet record or the win chance's calibration on some window (rule 2). The one that passes rules 1 and 2, a plain artificial-turf flag in the points equation, gains 0.001 to 0.002 points a window, and its within-season shuffle did as well or better on some window in 26 of 50 draws (rule 3 needs 5 or fewer). There is nothing to combine (rule 5) and no code change to make.

The owner's named ideas, in one line each: coach against coach does not predict (next section); coaches and teams at a given stadium, and teams on the road there, do not predict; travel distance and time zones help one or two windows and hurt another; turf against grass is real in the raw scores (about 2.3 more points a game on turf, 1.4 outdoors only) but the model's existing inputs already carry most of it, and what is left does not survive the placebo.

## The rule and how each idea was run

The rule is `reports/round3_rule.md`, written before any result, applied as written: (1) the team points miss lower on 2015-18, 2019-22 and 2023-25 (for an idea in the total equation, the total miss lower on all three too); (2) the spread flag (4+ points off the line, weeks 1-17) and the totals flag (under at a 55%+ raw chance, weeks 1-17) not worse on any window in wins minus losses, and the calibrated win chance's log loss not worse on any window; (3) the idea's own values shuffled within each season, 50 draws, and the real gain must beat the shuffled gain on every window in at least 45 of 50 draws; (4) no market input, no look-ahead, no new data source; (5) whatever passes is rerun together.

Each idea is added on its own to the live model as it runs: a points idea joins the points inputs, so the live ridge, the five blend ridges and the boosted trees all carry it; a total idea joins the total equation. The weekly walk-forward (refit before every regular-season week on every played game since 2013) is reproduced step for step and was checked against `M.walk_forward` on a random candidate for 2019: largest differences 0.0e+00 points on the spread, 0.0e+00 on the total, 5.6e-16 on the win chance, 0.0e+00 on the over chance (256 games). The boosted trees are refit fresh on this machine for the base and every idea (the live trees' cache holds fits from GitHub's runners; fresh fits move the base spread by 0.008 points on average, at most 0.19), so base and idea are compared like for like. Nothing under nflmodel/, web/ or data/processed was written.

Every input is as of before its game: a history uses the key's games in earlier weeks only (a Thursday result never reaches that week's Sunday game, as the weekly run prices a whole week at once), and uses the result against the model's own expectation (the residual), never against a line: the live model's walk-forward number for 2014-2025 regular-season games, and a plain as-of scoring rating from scores alone for 1999-2013 and playoff games. Histories are shrunk with 20 games of weight toward zero (sum / (games + 20)), one value for every history, fixed before any result. "Favourite" is always the model's own favourite.

Scored on the regular season. Base (fresh trees): team points miss 7.4096 / 7.3475 / 7.2626, total miss 10.7437 / 10.5406 / 10.1767, spread flag 68-55 / 79-51 / 40-21, totals flag 135-127 / 175-128 / 71-59, calibrated log loss 0.6194 / 0.6242 / 0.6202, Brier 0.2154 / 0.2172 / 0.2153, moneyline record of the model's side 472-547 (+39.6u) / 511-539 (-31.5u) / 372-443 (-63.5u) (2015-18 / 2019-22 / 2023-25).

**Count.** 121 ideas added and 13 live terms re-checked by dropping them. 7 of the 121 lower the miss on all three windows (rule 1); by chance alone, with three windows each a coin flip, about one in eight would. 1 of them also passes rule 2. Passing all of 1 to 3: 0.

Reading the tables: every change is idea minus base, per window 2015-18 / 2019-22 / 2023-25. Misses in points (below zero is better). Flag records as the change in wins minus losses (above zero is better). Log loss of the calibrated win chance, times 1000 (below zero is better). Moneyline: the change in units won by the model's side at the closing moneyline (a reading; the rule does not use it). Placebo percentile: the share of shuffled draws whose gain the real idea beats, per window; run in full (50 draws) for the idea passing rules 1 and 2 (the rule's gate); the six that pass rule 1 but fail rule 2 were given an informational run of up to 20 draws, stopped once 3 draws matched or beat them on some window (at 20 draws the rule allows 2), so their percentiles rest on the draws shown.

## Situational

**Coach against coach.** Each head coach's margin against the model's expectation in earlier games against this opposing head coach, shrunk with 20 games of weight. Most pairings are thin: before a 2015-25 game, 45% of pairings had never met, 37% had met twice or more, 6% eight times or more. The history does not predict the next meeting. Unshrunk, the average residual in earlier meetings against the next meeting's residual has a correlation of -0.015 (1,580 games), -0.046 for pairs with 4+ earlier meetings and +0.062 for 8+ (183 games, t 0.8): noise either way. In the model it moves the team points miss +0.002 / -0.003 / +0.000 and costs 6 spread wins on 2015-18. The same holds for a coach against this opposing franchise (correlation -0.006), a team against a team (+0.025) and a QB against this defense.

**Stadiums and surface.** A coach's residual at this stadium (correlation 0.001 with the next game there), a team's (0.012), and a team's on the road there all fail rule 1; the team-at-stadium history is worse on all three windows. A team's residual on this surface class has a small raw correlation (0.032, t 2.4) but worsens the miss on all three windows once in the model.

**Turf against grass.** Raw, 2015-25 regular season: 46.9 points a game on artificial turf (1,248 games) against 44.6 on grass (1,644); outdoors only, 45.7 on turf (578) against 44.3 on grass (1,493). Most of that is roofs (domes are turf) and the teams that play there, which the model already carries: after the model, turf games still ran 0.5 points over its total and grass games 0.5 under (outdoor turf +0.8, outdoor grass -0.5). A turf flag in the total equation (+0.83 points a game fitted) lowers the total miss on 2015-18 and 2023-25 and raises it on 2019-22 (+0.012). In the points equation (+0.41 points per team fitted) it is the one idea to pass rules 1 and 2, by 0.001 to 0.002 points, and fails the placebo. The home edge on turf, the away team's home surface differing from the game's, dome teams outdoors and outdoor teams in domes fail too (an outdoor team in a dome lowers the points miss on all three windows but loses spread wins on all three, 10 of them on 2023-25).

**Travel and time zones.** Travel miles (own and opponent) lower the miss on 2015-18 and 2023-25 and raise it on 2019-22 (+0.0002); east- and west-bound time-zone shifts help 2019-22 and 2023-25 and hurt 2015-18 (+0.003). Visiting teams that flew 2,000+ miles beat the model's margin by 1.6 points on 302 games, but teams that flew 500 to 2,000 miles were within 0.1, so the curve is not a slope the equation can use. Consecutive road games, miles over two weeks and altitude (Denver, Mexico City) all fail rule 1.

**Schedule, standings, coaches.** Rest difference, off a bye, short week, first-year coach, coach tenure and experience, 4th-down aggressiveness (the coach's go rate on 4th and 3 or less from the opponent's 60 in, from the play-by-play), clinched, clinched in the final week, mathematically eliminated (the live out-of-the-race input already carries this), the rematch residual, a coach or QB against his former team and a look-ahead to a primetime game next week: none lowers the miss on all three windows. A coach's career residual is the one reading with some persistence (correlation 0.036 with the next game, t 2.7), and it lowers the miss on 2015-18 (-0.014) and 2019-22 but raises it on 2023-25 (+0.004) and costs 17 spread wins on 2019-22.

Clinched and eliminated are exact bounds with ties and tiebreakers ignored (strict, so they flag fewer teams than the real standings: 1% and 6% of team-games).

| Idea | Equation | Team points miss change | Total miss change | Spread flag W-L change | Totals flag W-L change | Log loss change (x1000) | Moneyline units change | Placebo percentile | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| Coach vs coach (residual history) | points | +0.002 / -0.003 / +0.000 |  | -6 / +2 / -1 | +0 / +0 / +0 | +0.4 / -0.1 / +0.3 | +9.6 / +1.2 / -5.4 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18, 2023-25); 2 (2015-18 spread/log loss; 2023-25 spread/log loss) |
| Coach vs this opponent team | points | -0.004 / +0.006 / +0.003 |  | -7 / -4 / -5 | +0 / +0 / +0 | +0.4 / +0.3 / -0.2 | +11.1 / -6.5 / -1.7 | not run (fails 1 or 2) | not adopted: rule 1 (2019-22, 2023-25); 2 (2015-18 spread/log loss; 2019-22 spread/log loss; 2023-25 spread) |
| Team vs team (residual history) | points | -0.006 / +0.005 / -0.007 |  | +3 / +0 / -4 | +0 / +0 / +0 | +0.4 / -0.2 / -0.1 | +0.6 / -11.6 / +1.6 | not run (fails 1 or 2) | not adopted: rule 1 (2019-22); 2 (2015-18 log loss; 2023-25 spread) |
| QB vs this opponent (points residual) | points | -0.005 / -0.001 / +0.002 |  | -15 / -8 / -7 | +0 / +0 / +0 | -0.3 / +0.1 / +0.9 | +7.8 / +14.0 / +6.7 | not run (fails 1 or 2) | not adopted: rule 1 (2023-25); 2 (2015-18 spread; 2019-22 spread/log loss; 2023-25 spread/log loss) |
| Coach career residual | points | -0.014 / -0.004 / +0.004 |  | -3 / -17 / -3 | +0 / +0 / +0 | -2.4 / +0.6 / -0.7 | +16.9 / -24.4 / -1.5 | not run (fails 1 or 2) | not adopted: rule 1 (2023-25); 2 (2015-18 spread; 2019-22 spread/log loss; 2023-25 spread) |
| Coach at this stadium | points | +0.010 / -0.001 / +0.005 |  | -3 / -9 / -2 | +0 / +0 / +0 | +0.8 / -0.1 / +0.4 | -1.6 / +10.3 / +4.1 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18, 2023-25); 2 (2015-18 spread/log loss; 2019-22 spread; 2023-25 spread/log loss) |
| Team at this stadium | points | +0.012 / +0.004 / +0.002 |  | +3 / +5 / -11 | +0 / +0 / +0 | +3.7 / +0.1 / +0.5 | -1.0 / +8.9 / -20.7 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18, 2019-22, 2023-25); 2 (2015-18 log loss; 2019-22 log loss; 2023-25 spread/log loss) |
| Team on the road at this stadium | points | +0.000 / +0.006 / -0.003 |  | +0 / +4 / -4 | +0 / +0 / +0 | +1.9 / +0.1 / +0.2 | +11.9 / +3.4 / +2.9 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18, 2019-22); 2 (2015-18 log loss; 2019-22 log loss; 2023-25 spread/log loss) |
| Team on this surface | points | +0.003 / +0.005 / +0.003 |  | +1 / -16 / -2 | +0 / +0 / +0 | +1.9 / +1.8 / +1.1 | -48.1 / +22.4 / -8.6 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18, 2019-22, 2023-25); 2 (2015-18 log loss; 2019-22 spread/log loss; 2023-25 spread/log loss) |
| Turf (points) | points | -0.002 / -0.001 / -0.001 |  | +3 / +0 / +0 | +0 / +0 / +0 | -0.2 / -0.1 / -0.2 | -0.9 / +3.6 / -3.9 | 92 / 56 / 96 (50 draws) | not adopted: rule 3 (26 of 50 shuffles matched it) |
| Home edge on turf | points | +0.002 / +0.001 / -0.001 |  | -3 / -3 / -4 | +0 / +0 / +0 | +0.6 / +0.3 / +0.1 | +14.8 / -2.9 / +2.4 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18, 2019-22); 2 (2015-18 spread/log loss; 2019-22 spread/log loss; 2023-25 spread/log loss) |
| Turf (total) | total | -0.001 / +0.003 / -0.004 | -0.002 / +0.012 / -0.001 | +0 / +0 / +0 | +1 / -7 / -1 | +0.0 / +0.0 / +0.0 | +0.0 / +0.0 / +0.0 | not run (fails 1 or 2) | not adopted: rule 1 (2019-22); 2 (2019-22 totals; 2023-25 totals) |
| Away team's home surface differs | points | -0.001 / +0.005 / +0.006 |  | -8 / -16 / +0 | +0 / +0 / +0 | -2.2 / +0.8 / +1.3 | +32.0 / +7.1 / +27.5 | not run (fails 1 or 2) | not adopted: rule 1 (2019-22, 2023-25); 2 (2015-18 spread; 2019-22 spread/log loss; 2023-25 log loss) |
| Surface mismatch (total) | total | +0.003 / +0.001 / +0.001 | +0.011 / +0.000 / +0.001 | +0 / +0 / +0 | -2 / +0 / -4 | +0.0 / +0.0 / +0.0 | +0.0 / +0.0 / +0.0 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18, 2019-22, 2023-25); 2 (2015-18 totals; 2023-25 totals) |
| Dome team outdoors | points | +0.006 / +0.000 / -0.002 |  | -4 / +3 / -1 | +0 / +0 / +0 | +1.0 / +0.1 / +0.0 | -6.9 / +3.0 / -2.8 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18, 2019-22); 2 (2015-18 spread/log loss; 2019-22 log loss; 2023-25 spread/log loss) |
| Dome team outdoors (total) | total | +0.001 / +0.001 / +0.001 | +0.003 / +0.004 / -0.001 | +0 / +0 / +0 | -4 / -1 / +2 | +0.0 / +0.0 / +0.0 | +0.0 / +0.0 / +0.0 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18, 2019-22, 2023-25); 2 (2015-18 totals; 2019-22 totals) |
| Outdoor team in a dome | points | -0.001 / -0.001 / -0.000 |  | -2 / -1 / -10 | +0 / +0 / +0 | +0.3 / -0.8 / -0.2 | +6.5 / +1.4 / +1.3 | 50 / 100 / 25 (4 draws) | not adopted: rule 2 (2015-18 spread/log loss; 2019-22 spread; 2023-25 spread) |
| Outdoor team in a dome (total) | total | +0.003 / -0.003 / -0.009 | +0.012 / -0.008 / -0.000 | +0 / +0 / +0 | +5 / +6 / +2 | +0.0 / +0.0 / +0.0 | +0.0 / +0.0 / +0.0 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18) |
| Roof open / closed (total) | total | +0.003 / -0.001 / +0.004 | -0.002 / +0.001 / +0.012 | +0 / +0 / +0 | +9 / -4 / -8 | +0.0 / +0.0 / +0.0 | +0.0 / +0.0 / +0.0 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18, 2019-22, 2023-25); 2 (2019-22 totals; 2023-25 totals) |
| Travel miles | points | -0.002 / +0.000 / -0.005 |  | +1 / +3 / -2 | +0 / +0 / +0 | +0.2 / +0.1 / -0.5 | +2.0 / +11.2 / +14.2 | not run (fails 1 or 2) | not adopted: rule 1 (2019-22); 2 (2015-18 log loss; 2019-22 log loss; 2023-25 spread) |
| Travel miles (total) | total | -0.003 / -0.000 / +0.003 | -0.009 / -0.001 / +0.012 | +0 / +0 / +0 | +3 / +0 / -5 | +0.0 / +0.0 / +0.0 | +0.0 / +0.0 / +0.0 | not run (fails 1 or 2) | not adopted: rule 1 (2023-25); 2 (2023-25 totals) |
| Time-zone shift, east- and west-bound | points | +0.003 / -0.005 / -0.010 |  | +0 / +0 / -5 | +0 / +0 / +0 | +0.7 / -0.6 / -0.8 | +4.9 / +6.7 / +18.6 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18); 2 (2015-18 log loss; 2023-25 spread) |
| Time-zone shift (total) | total | -0.006 / +0.001 / +0.003 | -0.009 / +0.002 / +0.011 | +0 / +0 / +0 | +4 / -5 / -6 | +0.0 / +0.0 / +0.0 | +0.0 / +0.0 / +0.0 | not run (fails 1 or 2) | not adopted: rule 1 (2019-22, 2023-25); 2 (2019-22 totals; 2023-25 totals) |
| Consecutive road games | points | +0.001 / -0.001 / +0.001 |  | -2 / +0 / -2 | +0 / +0 / +0 | +0.4 / -0.1 / -0.1 | +14.4 / +4.9 / +11.8 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18, 2023-25); 2 (2015-18 spread/log loss; 2023-25 spread) |
| Miles over the last two weeks | points | -0.003 / +0.001 / -0.002 |  | -4 / +1 / +2 | +0 / +0 / +0 | +0.7 / -0.4 / -0.2 | +18.5 / +7.0 / +3.5 | not run (fails 1 or 2) | not adopted: rule 1 (2019-22); 2 (2015-18 spread/log loss) |
| Altitude (visitor at Denver or Mexico City) | points | -0.002 / +0.000 / -0.003 |  | -3 / +0 / +0 | +0 / +0 / +0 | +0.2 / +0.1 / -0.7 | +15.8 / -4.9 / +11.0 | not run (fails 1 or 2) | not adopted: rule 1 (2019-22); 2 (2015-18 spread/log loss; 2019-22 log loss) |
| Altitude (total) | total | +0.009 / -0.002 / -0.001 | +0.025 / +0.000 / +0.007 | +0 / +0 / +0 | -2 / -1 / +0 | +0.0 / +0.0 / +0.0 | +0.0 / +0.0 / +0.0 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18, 2019-22, 2023-25); 2 (2015-18 totals; 2019-22 totals) |
| Rest difference (days) | points | +0.003 / -0.000 / -0.002 |  | -5 / +0 / -4 | +0 / +0 / +0 | +1.3 / +0.1 / +0.1 | -0.6 / -1.1 / -11.5 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18); 2 (2015-18 spread/log loss; 2019-22 log loss; 2023-25 spread/log loss) |
| Off a bye | points | -0.000 / +0.001 / -0.001 |  | -4 / -2 / -2 | +0 / +0 / +0 | +0.3 / +0.3 / +0.1 | +2.7 / -2.6 / -4.9 | not run (fails 1 or 2) | not adopted: rule 1 (2019-22); 2 (2015-18 spread/log loss; 2019-22 spread/log loss; 2023-25 spread/log loss) |
| Short week | points | -0.000 / +0.001 / -0.000 |  | +1 / -1 / +0 | +0 / +0 / +0 | -0.1 / +0.2 / +0.1 | +3.4 / +0.0 / -2.9 | not run (fails 1 or 2) | not adopted: rule 1 (2019-22); 2 (2019-22 spread/log loss; 2023-25 log loss) |
| Short week (total) | total | +0.002 / +0.001 / +0.001 | +0.005 / +0.002 / +0.003 | +0 / +0 / +0 | +0 / +0 / -5 | +0.0 / +0.0 / +0.0 | +0.0 / +0.0 / +0.0 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18, 2019-22, 2023-25); 2 (2023-25 totals) |
| Off a bye (total) | total | -0.001 / +0.002 / -0.001 | -0.002 / +0.002 / -0.002 | +0 / +0 / +0 | +1 / -9 / +2 | +0.0 / +0.0 / +0.0 | +0.0 / +0.0 / +0.0 | not run (fails 1 or 2) | not adopted: rule 1 (2019-22); 2 (2019-22 totals) |
| Division game (total) | total | +0.016 / -0.003 / -0.004 | +0.009 / +0.010 / +0.013 | +0 / +0 / +0 | +0 / +2 / -11 | +0.0 / +0.0 / +0.0 | +0.0 / +0.0 / +0.0 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18, 2019-22, 2023-25); 2 (2023-25 totals) |
| International game (total) | total | -0.002 / +0.001 / +0.001 | -0.005 / +0.001 / +0.005 | +0 / +0 / +0 | -3 / -1 / -3 | +0.0 / +0.0 / +0.0 | +0.0 / +0.0 / +0.0 | not run (fails 1 or 2) | not adopted: rule 1 (2019-22, 2023-25); 2 (2015-18 totals; 2019-22 totals; 2023-25 totals) |
| Home edge at an international game | points | -0.001 / -0.000 / +0.002 |  | -4 / +2 / +0 | +0 / +0 / +0 | +0.4 / -0.0 / +0.4 | -1.6 / -6.7 / +1.4 | not run (fails 1 or 2) | not adopted: rule 1 (2023-25); 2 (2015-18 spread/log loss; 2023-25 log loss) |
| Coach tenure with the team | points | +0.000 / -0.004 / +0.007 |  | -5 / -4 / -5 | +0 / +0 / +0 | +1.3 / -0.7 / +1.0 | +5.9 / +21.1 / +2.5 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18, 2023-25); 2 (2015-18 spread/log loss; 2019-22 spread; 2023-25 spread/log loss) |
| First-year head coach | points | +0.001 / -0.002 / +0.003 |  | +0 / +2 / -1 | +0 / +0 / +0 | +0.3 / -0.1 / +0.8 | +9.3 / -8.9 / -9.1 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18, 2023-25); 2 (2015-18 log loss; 2023-25 spread/log loss) |
| Head coach experience (games) | points | +0.001 / -0.003 / +0.006 |  | -3 / -10 / -1 | +0 / +0 / +0 | +0.7 / -0.3 / +0.4 | -10.9 / +3.5 / +15.1 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18, 2023-25); 2 (2015-18 spread/log loss; 2019-22 spread; 2023-25 spread/log loss) |
| Coach's 4th-down aggressiveness | points | +0.002 / +0.000 / +0.002 |  | -1 / -3 / -1 | +0 / +0 / +0 | +0.3 / -0.4 / -0.1 | +14.0 / -4.0 / +5.4 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18, 2019-22, 2023-25); 2 (2015-18 spread/log loss; 2019-22 spread; 2023-25 spread) |
| Coach's 4th-down aggressiveness (total) | total | +0.000 / +0.007 / -0.015 | -0.004 / +0.015 / -0.018 | +0 / +0 / +0 | +3 / -3 / -2 | +0.0 / +0.0 / +0.0 | +0.0 / +0.0 / +0.0 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18, 2019-22); 2 (2019-22 totals; 2023-25 totals) |
| Clinched a playoff spot | points | +0.002 / +0.001 / +0.001 |  | -1 / +2 / +0 | +0 / +0 / +0 | +0.5 / +0.2 / +0.1 | +5.1 / +2.6 / -2.5 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18, 2019-22, 2023-25); 2 (2015-18 spread/log loss; 2019-22 log loss; 2023-25 log loss) |
| Clinched, final week | points | -0.002 / +0.003 / -0.001 |  | +1 / -2 / +1 | +0 / +0 / +0 | -0.2 / -0.1 / -0.0 | +1.4 / -7.8 / +2.7 | not run (fails 1 or 2) | not adopted: rule 1 (2019-22); 2 (2019-22 spread) |
| Mathematically eliminated | points | +0.009 / -0.001 / -0.002 |  | -2 / +0 / +1 | +0 / +0 / +0 | +0.8 / +0.2 / +0.2 | +20.2 / -10.4 / -7.6 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18); 2 (2015-18 spread/log loss; 2019-22 log loss; 2023-25 log loss) |
| Rematch: first meeting's residual | points | +0.002 / +0.001 / -0.001 |  | -1 / +0 / +0 | +0 / +0 / +0 | +0.7 / +0.0 / +0.0 | -0.7 / -0.6 / -3.6 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18, 2019-22); 2 (2015-18 spread/log loss; 2019-22 log loss; 2023-25 log loss) |
| Coach against his former team | points | +0.007 / +0.001 / +0.001 |  | -1 / -1 / +0 | +0 / +0 / +0 | +1.3 / +0.0 / +0.1 | -7.6 / -1.4 / -2.7 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18, 2019-22, 2023-25); 2 (2015-18 spread/log loss; 2019-22 spread/log loss; 2023-25 log loss) |
| QB against his former team | points | -0.004 / +0.001 / -0.004 |  | +5 / -4 / -2 | +0 / +0 / +0 | -0.5 / +0.1 / -0.4 | -3.1 / -6.6 / +0.8 | not run (fails 1 or 2) | not adopted: rule 1 (2019-22); 2 (2019-22 spread/log loss; 2023-25 spread) |
| Look-ahead: next game in primetime | points | +0.001 / +0.001 / +0.000 |  | -2 / -4 / +1 | +0 / +0 / +0 | +0.2 / -0.3 / -0.3 | -0.8 / +7.4 / +6.9 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18, 2019-22, 2023-25); 2 (2015-18 spread/log loss; 2019-22 spread) |
| Stadium scoring (park factor, total residual) | total | -0.008 / +0.004 / -0.004 | -0.027 / +0.019 / -0.004 | +0 / +0 / +0 | +5 / -6 / +0 | +0.0 / +0.0 / +0.0 | +0.0 / +0.0 / +0.0 | not run (fails 1 or 2) | not adopted: rule 1 (2019-22); 2 (2019-22 totals) |
| Coach pair scoring (total residual) | total | +0.003 / +0.003 / +0.000 | -0.002 / +0.017 / -0.001 | +0 / +0 / +0 | -4 / -10 / -1 | +0.0 / +0.0 / +0.0 | +0.0 / +0.0 / +0.0 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18, 2019-22, 2023-25); 2 (2015-18 totals; 2019-22 totals; 2023-25 totals) |

Effect sizes (the live equation fit on every regular-season game 2013-2025 with the idea added: points per unit and per standard deviation; share of games where the input is not zero):

- Coach vs coach (residual history): cvc: -0.232/unit, -0.161/sd, nonzero 54%
- Coach vs this opponent team: coach_vs_team: +0.089/unit, +0.087/sd, nonzero 74%; opp_coach_vs_team: +0.071/unit, +0.069/sd, nonzero 74%
- Team vs team (residual history): team_vs_team: +0.133/unit, +0.182/sd, nonzero 100%
- QB vs this opponent (points residual): qb_vs_team: +0.100/unit, +0.065/sd, nonzero 70%; opp_qb_vs_team: -0.241/unit, -0.156/sd, nonzero 70%
- Coach career residual: coach_career: +0.235/unit, +0.301/sd, nonzero 99%; opp_coach_career: -0.362/unit, -0.464/sd, nonzero 99%
- Coach at this stadium: coach_at_stadium: +0.086/unit, +0.091/sd, nonzero 77%; opp_coach_at_stadium: -0.111/unit, -0.118/sd, nonzero 77%
- Team at this stadium: team_at_stadium: +0.018/unit, +0.020/sd, nonzero 96%; opp_team_at_stadium: -0.213/unit, -0.244/sd, nonzero 96%
- Team on the road at this stadium: road_at_stadium: -0.006/unit, -0.005/sd, nonzero 47%; opp_road_at_stadium: -0.265/unit, -0.219/sd, nonzero 47%
- Team on this surface: team_on_surface: +0.241/unit, +0.282/sd, nonzero 100%; opp_team_on_surface: -0.256/unit, -0.300/sd, nonzero 100%
- Turf (points): turf_same: +0.408/unit, +0.202/sd, nonzero 43%
- Home edge on turf: turf_home: +0.543/unit, +0.224/sd, nonzero 22%
- Turf (total): x_turf: +0.834/unit, +0.413/sd, nonzero 43%
- Away team's home surface differs: surf_mismatch: -0.274/unit, -0.121/sd, nonzero 26%; opp_surf_mismatch: +0.231/unit, +0.102/sd, nonzero 26%
- Surface mismatch (total): x_surf_mismatch_sum: -0.091/unit, -0.046/sd, nonzero 53%
- Dome team outdoors: dome_team_out: +0.000/unit, +0.000/sd, nonzero 11%; opp_dome_team_out: -0.352/unit, -0.109/sd, nonzero 11%
- Dome team outdoors (total): x_dome_team_out_sum: -0.232/unit, -0.096/sd, nonzero 22%
- Outdoor team in a dome: out_team_in_dome: +1.307/unit, +0.391/sd, nonzero 10%; opp_out_team_in_dome: +0.478/unit, +0.143/sd, nonzero 10%
- Outdoor team in a dome (total): x_out_team_in_dome_sum: +1.773/unit, +0.723/sd, nonzero 20%
- Roof open / closed (total): x_roof_open: +3.183/unit, +0.399/sd, nonzero 2%; x_roof_closed: -0.412/unit, -0.139/sd, nonzero 13%
- Travel miles: miles: +0.230/unit, +0.178/sd, nonzero 51%; opp_miles: -0.289/unit, -0.224/sd, nonzero 51%
- Travel miles (total): x_miles_sum: +0.081/unit, +0.083/sd, nonzero 100%
- Time-zone shift, east- and west-bound: tz_east: +0.243/unit, +0.215/sd, nonzero 16%; tz_west: +0.214/unit, +0.141/sd, nonzero 14%; opp_tz_east: -0.416/unit, -0.368/sd, nonzero 16%; opp_tz_west: -0.085/unit, -0.056/sd, nonzero 14%
- Time-zone shift (total): x_tz_abs_sum: +0.032/unit, +0.048/sd, nonzero 59%
- Consecutive road games: road_streak: -0.207/unit, -0.087/sd, nonzero 15%; opp_road_streak: -0.080/unit, -0.034/sd, nonzero 15%
- Miles over the last two weeks: miles_2wk: +0.117/unit, +0.120/sd, nonzero 83%; opp_miles_2wk: -0.100/unit, -0.102/sd, nonzero 83%
- Altitude (visitor at Denver or Mexico City): altitude: -1.486/unit, -0.191/sd, nonzero 2%; opp_altitude: +0.413/unit, +0.053/sd, nonzero 2%
- Altitude (total): x_altitude_game: -1.370/unit, -0.245/sd, nonzero 3%
- Rest difference (days): rest_diff: +0.030/unit, +0.074/sd, nonzero 35%
- Off a bye: off_bye: -0.000/unit, -0.000/sd, nonzero 6%; opp_off_bye: -0.239/unit, -0.057/sd, nonzero 6%
- Short week: short_week: +0.742/unit, +0.181/sd, nonzero 6%; opp_short_week: -0.519/unit, -0.127/sd, nonzero 6%
- Short week (total): x_short_week_sum: -0.002/unit, -0.001/sd, nonzero 6%
- Off a bye (total): x_off_bye_sum: -0.347/unit, -0.131/sd, nonzero 12%
- Division game (total): x_div_game: -1.326/unit, -0.635/sd, nonzero 36%
- International game (total): x_intl: +0.230/unit, +0.025/sd, nonzero 1%
- Home edge at an international game: intl_home: -1.061/unit, -0.084/sd, nonzero 1%
- Coach tenure with the team: coach_tenure_l: +0.048/unit, +0.042/sd, nonzero 77%; opp_coach_tenure_l: -0.371/unit, -0.325/sd, nonzero 77%
- First-year head coach: first_year_coach: +0.066/unit, +0.028/sd, nonzero 23%; opp_first_year_coach: +0.509/unit, +0.213/sd, nonzero 23%
- Head coach experience (games): coach_exp_l: +0.030/unit, +0.037/sd, nonzero 99%; opp_coach_exp_l: -0.227/unit, -0.275/sd, nonzero 99%
- Coach's 4th-down aggressiveness: coach_go4: +3.472/unit, +0.222/sd, nonzero 99%; opp_coach_go4: +2.906/unit, +0.186/sd, nonzero 99%
- Coach's 4th-down aggressiveness (total): x_go4_sum: +5.899/unit, +0.555/sd, nonzero 100%
- Clinched a playoff spot: clinched: -0.146/unit, -0.015/sd, nonzero 1%; opp_clinched: +0.100/unit, +0.010/sd, nonzero 1%
- Clinched, final week: clinched_final: -1.989/unit, -0.158/sd, nonzero 1%; opp_clinched_final: +0.077/unit, +0.006/sd, nonzero 1%
- Mathematically eliminated: eliminated: -0.043/unit, -0.010/sd, nonzero 6%; opp_eliminated: +0.467/unit, +0.111/sd, nonzero 6%
- Rematch: first meeting's residual: rematch_r: +0.018/unit, +0.098/sd, nonzero 18%
- Coach against his former team: coach_vs_former: +1.352/unit, +0.139/sd, nonzero 1%; opp_coach_vs_former: +0.994/unit, +0.102/sd, nonzero 1%
- QB against his former team: qb_vs_former: -1.143/unit, -0.162/sd, nonzero 2%; opp_qb_vs_former: +0.499/unit, +0.071/sd, nonzero 2%
- Look-ahead: next game in primetime: next_prime: +0.319/unit, +0.126/sd, nonzero 20%; opp_next_prime: -0.221/unit, -0.088/sd, nonzero 20%
- Stadium scoring (park factor, total residual): x_stadium_total_r: +0.438/unit, +0.485/sd, nonzero 100%
- Coach pair scoring (total residual): x_coach_pair_total_r: -0.161/unit, -0.120/sd, nonzero 56%

## Primetime and kickoff time

Kickoff slot (early, late, night by ET kickoff), day of week (Thursday, Saturday, Monday against Sunday), SNF, MNF and TNF each on their own, holidays, Saturday late-season games, the body clock (a Pacific or Mountain team at 1pm ET; an Eastern team at 8pm ET or later against a western team; the night-game time-zone gap), a primetime road team off a short week and a team's first game after SNF or MNF. Each game-level flag was tried in the total equation, and in the points equation as a home-field term (the home edge in that slot), since a flag both teams share cancels out of the margin.

Raw, night games are not lower-scoring before the model (MNF 44.6, SNF 45.7, TNF 46.2, Sunday early 45.4, Sunday late 46.2 points a game), but after the model MNF games ran 1.7 points under its total and SNF 1.1 under (200 and 190 games). As inputs to the total equation, though, the slot, the day and the three primetime flags each worsen the total miss on at least one window. The home edge in primetime is the closest call: it lowers the points miss on all three windows (-0.005 / -0.005 / -0.002; the MNF home side ran 1.4 points under the model) but loses 4 spread wins on 2015-18 and 2019-22. The Thanksgiving home edge (Detroit and Dallas at home: 4.9 points under the model's margin in 32 games) also lowers the miss on all three windows and loses 1 spread win on 2023-25. Each team's, coach's and QB's own primetime or slot residual history fails rule 1.

The body clock: a West Coast team at 1pm ET fails rule 1 (+0.003 on 2015-18), and so do the late-night Eastern team and the night-game time-zone gap.

| Idea | Equation | Team points miss change | Total miss change | Spread flag W-L change | Totals flag W-L change | Log loss change (x1000) | Moneyline units change | Placebo percentile | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| Kickoff slot: late, night (total) | total | +0.019 / +0.010 / -0.000 | +0.029 / +0.026 / -0.010 | +0 / +0 / +0 | +1 / -9 / -6 | +0.0 / +0.0 / +0.0 | +0.0 / +0.0 / +0.0 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18, 2019-22); 2 (2019-22 totals; 2023-25 totals) |
| Day of week: Thu, Sat, Mon (total) | total | +0.010 / -0.001 / +0.000 | +0.016 / -0.002 / +0.000 | +0 / +0 / +0 | -3 / -2 / +4 | +0.0 / +0.0 / +0.0 | +0.0 / +0.0 / +0.0 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18, 2023-25); 2 (2015-18 totals; 2019-22 totals) |
| SNF, MNF, TNF separately (total) | total | -0.000 / +0.009 / +0.003 | -0.020 / +0.024 / +0.007 | +0 / +0 / +0 | -5 / -6 / +5 | +0.0 / +0.0 / +0.0 | +0.0 / +0.0 / +0.0 | not run (fails 1 or 2) | not adopted: rule 1 (2019-22, 2023-25); 2 (2015-18 totals; 2019-22 totals) |
| Home edge in SNF, MNF, TNF | points | -0.005 / -0.004 / -0.002 |  | -4 / -4 / +1 | +0 / +0 / +0 | +0.1 / -0.4 / -0.6 | +2.5 / -8.6 / -1.4 | 92 / 100 / 75 (12 draws) | not adopted: rule 2 (2015-18 spread/log loss; 2019-22 spread) |
| Home edge by slot (late, night) | points | +0.009 / -0.004 / +0.001 |  | -5 / -3 / -1 | +0 / +0 / +0 | +1.5 / -0.8 / +0.2 | -11.7 / -18.3 / -5.5 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18, 2023-25); 2 (2015-18 spread/log loss; 2019-22 spread; 2023-25 spread/log loss) |
| Home edge by day (Thu, Sat, Mon) | points | +0.001 / -0.001 / -0.001 |  | -4 / +4 / +2 | +0 / +0 / +0 | +0.2 / +0.0 / -0.6 | +2.2 / +2.4 / +1.9 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18); 2 (2015-18 spread/log loss; 2019-22 log loss) |
| Team's primetime residual history | points | +0.002 / +0.006 / -0.008 |  | -3 / -9 / -1 | +0 / +0 / +0 | +1.4 / +0.8 / -1.3 | +31.6 / -10.1 / +6.8 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18, 2019-22); 2 (2015-18 spread/log loss; 2019-22 spread/log loss; 2023-25 spread) |
| Team's residual in this slot | points | +0.003 / +0.005 / -0.006 |  | +4 / -10 / -5 | +0 / +0 / +0 | +1.2 / +0.8 / -0.1 | +8.0 / -19.8 / +6.1 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18, 2019-22); 2 (2015-18 log loss; 2019-22 spread/log loss; 2023-25 spread) |
| Coach's primetime residual history | points | +0.004 / +0.002 / -0.006 |  | -2 / -4 / +1 | +0 / +0 / +0 | +0.1 / -0.0 / -0.2 | -4.9 / +4.1 / -7.4 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18, 2019-22); 2 (2015-18 spread/log loss; 2019-22 spread) |
| Coach's residual in this slot | points | -0.005 / +0.000 / -0.005 |  | +6 / -24 / -6 | +0 / +0 / +0 | -1.7 / +1.7 / +0.1 | -12.5 / -7.7 / +19.3 | not run (fails 1 or 2) | not adopted: rule 1 (2019-22); 2 (2019-22 spread/log loss; 2023-25 spread/log loss) |
| QB's primetime residual history | points | -0.002 / -0.001 / +0.003 |  | -4 / +3 / +0 | +0 / +0 / +0 | -0.1 / -0.3 / +0.2 | +4.9 / +1.3 / -2.2 | not run (fails 1 or 2) | not adopted: rule 1 (2023-25); 2 (2015-18 spread; 2023-25 log loss) |
| QB's residual in this slot | points | -0.004 / -0.001 / +0.007 |  | -5 / -3 / +0 | +0 / +0 / +0 | -1.0 / +0.5 / +1.7 | +14.4 / -11.0 / +3.6 | not run (fails 1 or 2) | not adopted: rule 1 (2023-25); 2 (2015-18 spread; 2019-22 spread/log loss; 2023-25 log loss) |
| Holidays: Thanksgiving, Christmas (total) | total | +0.011 / +0.003 / +0.001 | +0.036 / +0.006 / +0.008 | +0 / +0 / +0 | +0 / +0 / -5 | +0.0 / +0.0 / +0.0 | +0.0 / +0.0 / +0.0 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18, 2019-22, 2023-25); 2 (2023-25 totals) |
| Home edge on Thanksgiving | points | -0.004 / -0.004 / -0.002 |  | +0 / +3 / -1 | +0 / +0 / +0 | -0.4 / -0.9 / -0.2 | +3.5 / -8.7 / -2.8 | 94 / 94 / 88 (16 draws) | not adopted: rule 2 (2023-25 spread) |
| Saturday late-season games (total) | total | +0.011 / -0.000 / +0.001 | +0.021 / +0.006 / -0.003 | +0 / +0 / +0 | -4 / -2 / -2 | +0.0 / +0.0 / +0.0 | +0.0 / +0.0 / +0.0 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18, 2019-22, 2023-25); 2 (2015-18 totals; 2019-22 totals; 2023-25 totals) |
| Home edge in Saturday late-season games | points | +0.003 / +0.000 / +0.001 |  | -4 / -1 / +0 | +0 / +0 / +0 | +1.2 / +0.0 / +0.1 | -0.0 / +4.0 / -0.1 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18, 2019-22, 2023-25); 2 (2015-18 spread/log loss; 2019-22 spread/log loss; 2023-25 log loss) |
| Body clock: West Coast team at 1pm ET | points | +0.003 / +0.001 / -0.001 |  | -3 / -2 / -1 | +0 / +0 / +0 | +0.5 / +0.2 / -0.2 | +3.4 / -5.6 / -1.2 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18, 2019-22); 2 (2015-18 spread/log loss; 2019-22 spread/log loss; 2023-25 spread) |
| Body clock: East Coast team late at night vs a western team | points | +0.001 / +0.001 / +0.000 |  | -1 / +1 / +1 | +0 / +0 / +0 | +0.5 / +0.2 / +0.1 | +7.0 / +2.1 / -4.5 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18, 2019-22, 2023-25); 2 (2015-18 spread/log loss; 2019-22 log loss; 2023-25 log loss) |
| Body clock: night-game time-zone edge | points | +0.006 / -0.001 / -0.004 |  | +2 / -1 / -1 | +0 / +0 / +0 | +0.5 / +0.7 / -0.3 | +5.6 / -3.7 / +0.6 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18); 2 (2015-18 log loss; 2019-22 spread/log loss; 2023-25 spread) |
| Primetime road team off a short week | points | +0.001 / +0.001 / -0.001 |  | -2 / -1 / -1 | +0 / +0 / +0 | -0.1 / +0.2 / -0.1 | +10.2 / +10.2 / +5.1 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18, 2019-22); 2 (2015-18 spread; 2019-22 spread/log loss; 2023-25 spread) |
| First game after SNF or MNF | points | +0.005 / -0.000 / +0.001 |  | +0 / +3 / -1 | +0 / +0 / +0 | +2.8 / -0.2 / -0.3 | -14.2 / -6.4 / +0.8 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18, 2023-25); 2 (2015-18 log loss; 2023-25 spread) |
| Night game outdoors (total) | total | +0.004 / +0.005 / +0.001 | +0.014 / +0.016 / +0.002 | +0 / +0 / +0 | -9 / -9 / -2 | +0.0 / +0.0 / +0.0 | +0.0 / +0.0 / +0.0 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18, 2019-22, 2023-25); 2 (2015-18 totals; 2019-22 totals; 2023-25 totals) |
| Night and cold (total) | total | +0.007 / +0.002 / +0.001 | +0.002 / +0.002 / +0.004 | +0 / +0 / +0 | +1 / -1 / -2 | +0.0 / +0.0 / +0.0 | +0.0 / +0.0 / +0.0 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18, 2019-22, 2023-25); 2 (2019-22 totals; 2023-25 totals) |
| Night and wind (total) | total | -0.000 / +0.009 / +0.001 | +0.003 / +0.028 / +0.007 | +0 / +0 / +0 | -2 / -14 / -2 | +0.0 / +0.0 / +0.0 | +0.0 / +0.0 / +0.0 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18, 2019-22, 2023-25); 2 (2015-18 totals; 2019-22 totals; 2023-25 totals) |

Effect sizes (the live equation fit on every regular-season game 2013-2025 with the idea added: points per unit and per standard deviation; share of games where the input is not zero):

- Kickoff slot: late, night (total): x_slot_late: +0.197/unit, +0.087/sd, nonzero 27%; x_slot_night: -0.701/unit, -0.289/sd, nonzero 22%
- Day of week: Thu, Sat, Mon (total): x_thu: -0.040/unit, -0.010/sd, nonzero 7%; x_sat: -0.197/unit, -0.037/sd, nonzero 4%; x_mon: -1.326/unit, -0.336/sd, nonzero 7%
- SNF, MNF, TNF separately (total): x_snf: -0.576/unit, -0.144/sd, nonzero 7%; x_mnf: -1.370/unit, -0.347/sd, nonzero 7%; x_tnf: -0.083/unit, -0.020/sd, nonzero 7%
- Home edge in SNF, MNF, TNF: snf_home: +0.168/unit, +0.030/sd, nonzero 3%; mnf_home: -1.262/unit, -0.232/sd, nonzero 4%; tnf_home: +0.032/unit, +0.006/sd, nonzero 3%
- Home edge by slot (late, night): slot_late_home: -0.214/unit, -0.072/sd, nonzero 13%; slot_night_home: -0.440/unit, -0.134/sd, nonzero 10%
- Home edge by day (Thu, Sat, Mon): thu_home: -0.005/unit, -0.001/sd, nonzero 3%; sat_home: -0.910/unit, -0.095/sd, nonzero 1%; mon_home: -1.300/unit, -0.239/sd, nonzero 4%
- Team's primetime residual history: team_prime_r: +0.261/unit, +0.205/sd, nonzero 21%; opp_team_prime_r: -0.202/unit, -0.158/sd, nonzero 21%
- Team's residual in this slot: team_slot_r: +0.158/unit, +0.194/sd, nonzero 100%; opp_team_slot_r: -0.316/unit, -0.387/sd, nonzero 100%
- Coach's primetime residual history: coach_prime_r: -0.037/unit, -0.028/sd, nonzero 20%; opp_coach_prime_r: -0.440/unit, -0.335/sd, nonzero 20%
- Coach's residual in this slot: coach_slot_r: +0.128/unit, +0.180/sd, nonzero 97%; opp_coach_slot_r: -0.393/unit, -0.552/sd, nonzero 97%
- QB's primetime residual history: qb_prime_r: -0.154/unit, -0.071/sd, nonzero 19%; opp_qb_prime_r: -0.476/unit, -0.221/sd, nonzero 19%
- QB's residual in this slot: qb_slot_r: +0.015/unit, +0.014/sd, nonzero 95%; opp_qb_slot_r: -0.284/unit, -0.265/sd, nonzero 95%
- Holidays: Thanksgiving, Christmas (total): x_thanksgiving: -1.470/unit, -0.151/sd, nonzero 1%; x_christmas: +0.679/unit, +0.103/sd, nonzero 2%
- Home edge on Thanksgiving: thanksgiving_home: -2.707/unit, -0.202/sd, nonzero 1%
- Saturday late-season games (total): x_sat_late: -0.154/unit, -0.022/sd, nonzero 2%
- Home edge in Saturday late-season games: sat_late_home: -0.815/unit, -0.085/sd, nonzero 1%
- Body clock: West Coast team at 1pm ET: bc_early_west: +0.047/unit, +0.010/sd, nonzero 5%; opp_bc_early_west: -0.282/unit, -0.061/sd, nonzero 5%
- Body clock: East Coast team late at night vs a western team: bc_late_east: -1.132/unit, -0.136/sd, nonzero 1%; opp_bc_late_east: -0.700/unit, -0.084/sd, nonzero 1%
- Body clock: night-game time-zone edge: bc_night_edge: +0.385/unit, +0.235/sd, nonzero 12%
- Primetime road team off a short week: prime_road_short: +0.149/unit, +0.027/sd, nonzero 3%; opp_prime_road_short: +0.500/unit, +0.090/sd, nonzero 3%
- First game after SNF or MNF: after_prime: +0.094/unit, +0.032/sd, nonzero 13%; opp_after_prime: +0.671/unit, +0.229/sd, nonzero 13%
- Night game outdoors (total): x_night_outdoor: -0.235/unit, -0.085/sd, nonzero 16%
- Night and cold (total): x_night_cold: -0.016/unit, -0.002/sd, nonzero 2%
- Night and wind (total): x_night_wind: +0.036/unit, +0.116/sd, nonzero 15%

## Referees

The schedule names the referee only, not his crew, so crew changes year to year cannot be read; a first-year referee (his first season in the data) stands in. All readings are residuals against the model's own expectation; the model favourite is the side of the model's own spread. The home-cover-rate test from before (a market reading) is redone market-free as the referee's home-team margin residual.

The referee's own total residual (games he worked against the model's total, which already carries the live referee input) is the one striking reading: it cuts the total miss on 2019-22 by 0.083 and on 2015-18 by 0.009 and adds 13, 6 and 2 totals-flag wins, but raises the total miss on 2023-25 by 0.012, so it fails rule 1. Its fitted weight is negative (-1.5 points per point of history): it corrects the live referee input where that input overshoots, which is a fit to the earlier seasons that 2023-25 did not repeat. The referee's flags per game lower the total miss on all three windows (-0.029 / -0.006 / -0.002) but raise the team points miss on 2023-25 (+0.0003) and lose totals-flag wins on 2019-22 and 2023-25 (-2, -4); penalty yards per game help 2015-18 only. Referee x team, the referee's home residual, the referee x model favourite and referee x division game all fail rule 1.

| Idea | Equation | Team points miss change | Total miss change | Spread flag W-L change | Totals flag W-L change | Log loss change (x1000) | Moneyline units change | Placebo percentile | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| Referee x team (margin residual) | points | -0.001 / -0.001 / +0.003 |  | -13 / +0 / -3 | +0 / +0 / +0 | +0.2 / -0.0 / -0.1 | +5.5 / +10.5 / -0.9 | not run (fails 1 or 2) | not adopted: rule 1 (2023-25); 2 (2015-18 spread/log loss; 2023-25 spread) |
| Referee x team (points residual) | points | +0.003 / -0.002 / +0.001 |  | -10 / -2 / -5 | +0 / +0 / +0 | +1.3 / -0.2 / -0.0 | +4.5 / +13.2 / -1.7 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18, 2023-25); 2 (2015-18 spread/log loss; 2019-22 spread; 2023-25 spread) |
| Referee x team at home / on the road | points | -0.003 / +0.001 / +0.004 |  | -12 / +0 / -4 | +0 / +0 / +0 | +1.4 / +0.2 / -0.7 | -20.1 / -8.7 / +4.9 | not run (fails 1 or 2) | not adopted: rule 1 (2019-22, 2023-25); 2 (2015-18 spread/log loss; 2019-22 log loss; 2023-25 spread) |
| Referee home-team residual (market-free home cover) | points | -0.001 / +0.000 / +0.003 |  | -2 / +2 / -2 | +0 / +0 / +0 | +0.1 / -0.1 / +0.1 | +13.1 / -4.0 / +3.8 | not run (fails 1 or 2) | not adopted: rule 1 (2019-22, 2023-25); 2 (2015-18 spread/log loss; 2023-25 spread/log loss) |
| Referee x model favourite | points | +0.002 / +0.002 / -0.004 |  | -6 / +1 / -4 | +0 / +0 / +0 | +0.1 / -0.1 / -0.5 | +8.8 / -17.0 / +20.7 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18, 2019-22); 2 (2015-18 spread/log loss; 2023-25 spread) |
| Referee x division game (home residual) | points | -0.004 / +0.001 / -0.005 |  | -5 / +0 / +0 | +0 / +0 / +0 | -0.1 / +0.3 / -0.4 | +22.7 / -25.6 / -0.9 | not run (fails 1 or 2) | not adopted: rule 1 (2019-22); 2 (2015-18 spread; 2019-22 log loss) |
| Referee total residual (vs the model, total) | total | -0.007 / -0.041 / -0.004 | -0.009 / -0.083 / +0.012 | +0 / +0 / +0 | +13 / +6 / +2 | +0.0 / +0.0 / +0.0 | +0.0 / +0.0 / +0.0 | not run (fails 1 or 2) | not adopted: rule 1 (2023-25) |
| Referee flags per game (total) | total | -0.009 / -0.001 / +0.000 | -0.029 / -0.006 / -0.002 | +0 / +0 / +0 | +16 / -2 / -4 | +0.0 / +0.0 / +0.0 | +0.0 / +0.0 / +0.0 | not run (fails 1 or 2) | not adopted: rule 1 (2023-25); 2 (2019-22 totals; 2023-25 totals) |
| Referee penalty yards per game (total) | total | -0.007 / -0.000 / -0.000 | -0.024 / +0.001 / -0.001 | +0 / +0 / +0 | +16 / -3 / -2 | +0.0 / +0.0 / +0.0 | +0.0 / +0.0 / +0.0 | not run (fails 1 or 2) | not adopted: rule 1 (2019-22); 2 (2019-22 totals; 2023-25 totals) |
| Referee pace: plays per game (total) | total | +0.003 / +0.003 / +0.000 | +0.003 / +0.005 / +0.001 | +0 / +0 / +0 | -2 / -2 / -1 | +0.0 / +0.0 / +0.0 | +0.0 / +0.0 / +0.0 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18, 2019-22, 2023-25); 2 (2015-18 totals; 2019-22 totals; 2023-25 totals) |
| Referee x primetime (total residual) | total | +0.003 / +0.001 / +0.002 | +0.007 / +0.002 / -0.003 | +0 / +0 / +0 | -2 / +0 / -4 | +0.0 / +0.0 / +0.0 | +0.0 / +0.0 / +0.0 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18, 2019-22, 2023-25); 2 (2015-18 totals; 2023-25 totals) |
| First-year referee (total) | total | +0.002 / +0.000 / +0.001 | +0.001 / +0.001 / -0.002 | +0 / +0 / +0 | +5 / +0 / -3 | +0.0 / +0.0 / +0.0 | +0.0 / +0.0 / +0.0 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18, 2019-22, 2023-25); 2 (2023-25 totals) |
| Home edge with a first-year referee | points | +0.001 / +0.001 / -0.001 |  | +0 / +4 / +2 | +0 / +0 / +0 | +0.4 / +0.1 / -0.2 | -3.0 / -1.1 / -2.0 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18, 2019-22); 2 (2015-18 log loss; 2019-22 log loss) |

Effect sizes (the live equation fit on every regular-season game 2013-2025 with the idea added: points per unit and per standard deviation; share of games where the input is not zero):

- Referee x team (margin residual): ref_team_r: -0.141/unit, -0.172/sd, nonzero 92%; opp_ref_team_r: -0.180/unit, -0.219/sd, nonzero 92%
- Referee x team (points residual): ref_team_pts: -0.148/unit, -0.128/sd, nonzero 92%; opp_ref_team_pts: -0.188/unit, -0.163/sd, nonzero 92%
- Referee x team at home / on the road: ref_team_venue: -0.149/unit, -0.152/sd, nonzero 86%; opp_ref_team_venue: -0.188/unit, -0.192/sd, nonzero 86%
- Referee home-team residual (market-free home cover): ref_home_r: +0.001/unit, +0.001/sd, nonzero 98%
- Referee x model favourite: ref_fav_r: +0.106/unit, +0.131/sd, nonzero 99%
- Referee x division game (home residual): ref_div_home: +0.242/unit, +0.237/sd, nonzero 36%
- Referee total residual (vs the model, total): x_ref_total_r: -1.469/unit, -1.248/sd, nonzero 99%
- Referee flags per game (total): x_ref_flags: +0.181/unit, +0.115/sd, nonzero 99%
- Referee penalty yards per game (total): x_ref_yards: +0.009/unit, +0.052/sd, nonzero 99%
- Referee pace: plays per game (total): x_ref_pace: -0.022/unit, -0.024/sd, nonzero 99%
- Referee x primetime (total residual): x_ref_prime_total_r: +0.187/unit, +0.102/sd, nonzero 20%
- First-year referee (total): x_ref_new: +0.476/unit, +0.124/sd, nonzero 7%
- Home edge with a first-year referee: ref_new_home: +0.744/unit, +0.143/sd, nonzero 4%

## Weather

The weather in every backtest is the record the live model's own backtest uses: the schedule's temperature and wind, and rain and snow from the play-by-play weather text (open-air games). Historical kickoff forecasts are not in the pulled data (the forecast log starts in 2026), so no backtest can use the forecast; the live model prices this season's games off the forecast, as before.

Re-checks of the live terms, each dropped on its own. In the points equation, dropping cold or the warm-or-dome-team-in-cold flag worsens the miss on all three windows: both earn their place. Dropping rain or wind is mixed. Dropping dome lowers the points miss on all three windows by 0.0002 to 0.0008 but loses a spread win on 2023-25, so it stays. In the total equation, dropping wind worsens every window and dropping rain worsens 2019-22 and 2023-25 (+0.03, +0.06): they earn their place. Dropping cold (-0.054 / -0.002 / -0.001 on the total miss) and dropping dome (-0.007 / -0.009 / -0.005) both lower the total miss on all three windows but each loses one totals-flag win on one window (cold on 2023-25, dome on 2019-22), so both stay; they are the first things to re-check after 2026.

Interactions: warm-or-dome teams in wind, rain or snow; a cold-weather team in a dome in December or later; travel and time-zone shift in the cold; a pass-heavy team (pass rate over expected, last 16 games) in wind; each QB's own bad-weather residual; rain on grass against rain on turf; snow and open-air temperature in the total; wind x the referee's flag rate. None lowers the miss on all three windows. Travel in the cold and warm-or-dome teams in snow keep every record but fail rule 1.

| Idea | Equation | Team points miss change | Total miss change | Spread flag W-L change | Totals flag W-L change | Log loss change (x1000) | Moneyline units change | Placebo percentile | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| Re-check: drop rain (points) | points, dropped | -0.000 / +0.000 / -0.002 |  | +0 / +3 / +1 | +0 / +0 / +0 | -0.1 / +0.0 / -0.2 | +4.0 / -5.2 / +3.0 | not run (fails 1 or 2) | stays: dropping it is mixed across windows |
| Re-check: drop wind (points) | points, dropped | -0.001 / -0.000 / +0.001 |  | +1 / -1 / -3 | +0 / +0 / +0 | -0.0 / -0.2 / +0.2 | +2.2 / -7.2 / -4.8 | not run (fails 1 or 2) | stays: dropping it is mixed across windows |
| Re-check: drop cold (points) | points, dropped | +0.003 / +0.001 / +0.001 |  | -1 / +0 / +1 | +0 / +0 / +0 | +0.3 / +0.0 / +0.1 | +11.3 / -0.0 / -5.6 | not run (fails 1 or 2) | stays: dropping it worsens the miss on every window |
| Re-check: drop warm-or-dome team in cold | points, dropped | +0.002 / +0.004 / +0.005 |  | +2 / -1 / -1 | +0 / +0 / +0 | -0.0 / +0.5 / +0.2 | +4.2 / -3.3 / -4.1 | not run (fails 1 or 2) | stays: dropping it worsens the miss on every window |
| Re-check: drop dome (points) | points, dropped | -0.001 / -0.000 / -0.000 |  | +0 / +3 / -1 | +0 / +0 / +0 | -0.1 / -0.1 / +0.0 | +11.5 / +3.5 / -2.7 | not run (fails 1 or 2) | stays: dropping it lowers the miss on every window but fails rule 2 (2023-25 spread/log loss) |
| Re-check: drop rain (total) | total, dropped | -0.000 / +0.011 / +0.010 | -0.008 / +0.029 / +0.057 | +0 / +0 / +0 | +0 / -19 / -7 | +0.0 / +0.0 / +0.0 | +0.0 / +0.0 / +0.0 | not run (fails 1 or 2) | stays: dropping it is mixed across windows |
| Re-check: drop wind (total) | total, dropped | +0.011 / +0.005 / +0.028 | +0.042 / +0.007 / +0.043 | +0 / +0 / +0 | -5 / -8 / +1 | +0.0 / +0.0 / +0.0 | +0.0 / +0.0 / +0.0 | not run (fails 1 or 2) | stays: dropping it worsens the miss on every window |
| Re-check: drop cold (total) | total, dropped | -0.018 / -0.001 / -0.000 | -0.054 / -0.002 / -0.001 | +0 / +0 / +0 | +10 / +0 / -1 | +0.0 / +0.0 / +0.0 | +0.0 / +0.0 / +0.0 | not run (fails 1 or 2) | stays: dropping it lowers the miss on every window but fails rule 2 (2023-25 totals) |
| Re-check: drop dome (total) | total, dropped | -0.004 / -0.002 / -0.002 | -0.007 / -0.009 / -0.005 | +0 / +0 / +0 | +8 / -1 / +0 | +0.0 / +0.0 / +0.0 | +0.0 / +0.0 / +0.0 | not run (fails 1 or 2) | stays: dropping it lowers the miss on every window but fails rule 2 (2019-22 totals) |
| Snow (total) | total | +0.001 / +0.003 / -0.004 | -0.000 / +0.002 / +0.001 | +0 / +0 / +0 | +2 / +0 / +3 | +0.0 / +0.0 / +0.0 | +0.0 / +0.0 / +0.0 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18, 2019-22, 2023-25) |
| Snow (points) | points | -0.001 / +0.000 / +0.000 |  | +3 / +1 / +0 | +0 / +0 / +0 | -0.1 / -0.0 / +0.0 | +9.9 / +3.3 / +2.2 | not run (fails 1 or 2) | not adopted: rule 1 (2019-22, 2023-25); 2 (2023-25 log loss) |
| Temperature, open air (total) | total | +0.003 / +0.003 / -0.001 | +0.010 / +0.006 / -0.004 | +0 / +0 / +0 | -8 / -6 / -6 | +0.0 / +0.0 / +0.0 | +0.0 / +0.0 / +0.0 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18, 2019-22); 2 (2015-18 totals; 2019-22 totals; 2023-25 totals) |
| Rain on grass / rain on turf (total) | total | +0.007 / +0.001 / +0.001 | +0.015 / +0.003 / -0.002 | +0 / +0 / +0 | +0 / -1 / -1 | +0.0 / +0.0 / +0.0 | +0.0 / +0.0 / +0.0 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18, 2019-22, 2023-25); 2 (2019-22 totals; 2023-25 totals) |
| Warm-or-dome team in wind | points | +0.001 / -0.000 / +0.003 |  | -3 / -5 / -3 | +0 / +0 / +0 | +2.1 / -0.5 / +0.1 | +0.3 / -3.7 / +4.1 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18, 2023-25); 2 (2015-18 spread/log loss; 2019-22 spread; 2023-25 spread/log loss) |
| Warm-or-dome team in rain | points | +0.004 / -0.001 / +0.001 |  | -4 / +5 / +0 | +0 / +0 / +0 | +0.0 / -1.1 / -0.2 | +16.5 / -4.6 / +8.6 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18, 2023-25); 2 (2015-18 spread/log loss) |
| Warm-or-dome team in snow | points | +0.000 / +0.000 / -0.003 |  | +1 / +4 / +2 | +0 / +0 / +0 | -0.0 / -0.1 / -0.3 | +6.3 / +1.5 / +1.4 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18, 2019-22) |
| Cold-weather team in a dome in December+ | points | +0.001 / +0.003 / +0.000 |  | -1 / -2 / +1 | +0 / +0 / +0 | +0.3 / -0.1 / +0.0 | -1.4 / +8.4 / -5.4 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18, 2019-22, 2023-25); 2 (2015-18 spread/log loss; 2019-22 spread; 2023-25 log loss) |
| Travel x cold | points | -0.002 / +0.000 / -0.006 |  | +2 / +6 / +1 | +0 / +0 / +0 | -0.1 / -0.2 / -0.2 | +3.0 / -2.6 / +4.7 | not run (fails 1 or 2) | not adopted: rule 1 (2019-22) |
| Time-zone shift x cold | points | +0.001 / +0.000 / -0.002 |  | +0 / +3 / +1 | +0 / +0 / +0 | +0.2 / -0.1 / +0.2 | +6.0 / +4.7 / -5.9 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18, 2019-22); 2 (2015-18 log loss; 2023-25 log loss) |
| Pass-heavy team in wind | points | +0.002 / +0.003 / +0.001 |  | +3 / -6 / -3 | +0 / +0 / +0 | +1.2 / +0.4 / -0.3 | -5.5 / -4.7 / -0.2 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18, 2019-22, 2023-25); 2 (2015-18 log loss; 2019-22 spread/log loss; 2023-25 spread) |
| Pass-heavy teams in wind (total) | total | -0.003 / +0.003 / +0.001 | -0.003 / +0.014 / +0.002 | +0 / +0 / +0 | +1 / -5 / +0 | +0.0 / +0.0 / +0.0 | +0.0 / +0.0 / +0.0 | not run (fails 1 or 2) | not adopted: rule 1 (2019-22, 2023-25); 2 (2019-22 totals) |
| QB's bad-weather residual history | points | +0.003 / +0.001 / -0.000 |  | +5 / +1 / -1 | +0 / +0 / +0 | +0.3 / +0.0 / +0.1 | -4.2 / +5.0 / -0.9 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18, 2019-22); 2 (2015-18 log loss; 2019-22 log loss; 2023-25 spread/log loss) |
| Wind x referee flag rate (total) | total | +0.002 / -0.001 / +0.001 | +0.004 / +0.001 / +0.001 | +0 / +0 / +0 | +3 / -2 / -9 | +0.0 / +0.0 / +0.0 | +0.0 / +0.0 / +0.0 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18, 2019-22, 2023-25); 2 (2019-22 totals; 2023-25 totals) |

Effect sizes (the live equation fit on every regular-season game 2013-2025 with the idea added: points per unit and per standard deviation; share of games where the input is not zero):

- Snow (total): x_snow: +4.552/unit, +0.443/sd, nonzero 1%
- Snow (points): snow_same: +2.247/unit, +0.223/sd, nonzero 1%
- Temperature, open air (total): x_temp_out: +0.019/unit, +0.277/sd, nonzero 66%
- Rain on grass / rain on turf (total): x_rain_grass: -1.667/unit, -0.284/sd, nonzero 3%; x_rain_turf: -2.087/unit, -0.292/sd, nonzero 2%
- Warm-or-dome team in wind: wd_wind: -0.005/unit, -0.021/sd, nonzero 30%; opp_wd_wind: +0.019/unit, +0.084/sd, nonzero 30%
- Warm-or-dome team in rain: wd_rain: -1.984/unit, -0.272/sd, nonzero 2%; opp_wd_rain: +0.751/unit, +0.103/sd, nonzero 2%
- Warm-or-dome team in snow: wd_snow: +0.333/unit, +0.015/sd, nonzero 0%; opp_wd_snow: +5.201/unit, +0.227/sd, nonzero 0%
- Cold-weather team in a dome in December+: cold_team_dome: -0.298/unit, -0.039/sd, nonzero 2%; opp_cold_team_dome: +0.595/unit, +0.079/sd, nonzero 2%
- Travel x cold: miles_cold: -2.653/unit, -0.382/sd, nonzero 3%; opp_miles_cold: -0.210/unit, -0.030/sd, nonzero 3%
- Time-zone shift x cold: tz_cold: -1.610/unit, -0.262/sd, nonzero 1%; opp_tz_cold: -0.599/unit, -0.098/sd, nonzero 1%
- Pass-heavy team in wind: passoe_wind: -0.006/unit, -0.189/sd, nonzero 70%; opp_passoe_wind: -0.002/unit, -0.054/sd, nonzero 70%
- Pass-heavy teams in wind (total): x_passoe_wind_sum: -0.001/unit, -0.044/sd, nonzero 70%
- QB's bad-weather residual history: qb_badwx_r: -0.069/unit, -0.022/sd, nonzero 15%; opp_qb_badwx_r: +0.018/unit, +0.006/sd, nonzero 15%
- Wind x referee flag rate (total): x_wind_refflags: +0.030/unit, +0.160/sd, nonzero 69%

## Injuries

Injury status is the final report the live model reads (Out or Doubtful, plus roster statuses that rule a player out, matched to last game's 50%+ snap players), never game-day actives. Re-checks: dropping the skill players' value out worsens 2019-22 and 2023-25 by 0.014 and 0.020: it earns its place. Dropping the snaps-out pair is mixed. Dropping the QB-out flag lowers the points miss on all three windows (-0.004 / -0.004 / -0.002) and adds spread wins on all three (+2 / +1 / +2) but worsens the win chance's log loss on 2019-22 (+0.0004), so it fails rule 2 and stays; the QB rating already follows the actual starter, which is why the flag has little left to add. It is the second thing to re-check after 2026.

New readings: starters out by unit (the opponent's secondary and front seven, from the snap counts' positions; both of last game's top two receivers), each against the matching strength (own passing or rushing rating; the opponent's sack rate against missing linemen); injuries x a bye, a short week, travel, wind and primetime; the backup QB's rating and experience; both sides' injuries together; the coach's residual when missing starters. The opponent's missing secondary and missing front seven each lower the points miss on all three windows by under 0.002 and each lose 5 or 6 spread wins on one window. Injuries on both teams in the total equation lower the total miss on all three windows but lose 6 and 13 totals-flag wins on 2019-22 and 2023-25. Injuries x the referee was not built: there is no honest mechanism.

| Idea | Equation | Team points miss change | Total miss change | Spread flag W-L change | Totals flag W-L change | Log loss change (x1000) | Moneyline units change | Placebo percentile | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| Re-check: drop QB out | points, dropped | -0.004 / -0.004 / -0.002 |  | +2 / +1 / +2 | +0 / +0 / +0 | -1.2 / +0.4 / -0.3 | +15.5 / -4.8 / +11.7 | not run (fails 1 or 2) | stays: dropping it lowers the miss on every window but fails rule 2 (2019-22 log loss) |
| Re-check: drop skill value out (both) | points, dropped | -0.002 / +0.014 / +0.020 |  | -3 / -13 / -11 | +0 / +0 / +0 | +1.4 / +1.8 / +2.6 | -12.2 / -15.4 / -3.5 | not run (fails 1 or 2) | stays: dropping it is mixed across windows |
| Re-check: drop snaps out (both) | points, dropped | -0.004 / +0.002 / +0.007 |  | -5 / +0 / +0 | +0 / +0 / +0 | +0.2 / -0.4 / -0.1 | +5.9 / +9.3 / +15.0 | not run (fails 1 or 2) | stays: dropping it is mixed across windows |
| Re-check: drop QB out (total) | total, dropped | +0.001 / +0.002 / -0.010 | -0.017 / +0.009 / -0.025 | +0 / +0 / +0 | +0 / -12 / +0 | +0.0 / +0.0 / +0.0 | +0.0 / +0.0 / +0.0 | not run (fails 1 or 2) | stays: dropping it is mixed across windows |
| Injuries x bye / short week | points | +0.007 / -0.001 / +0.002 |  | -1 / +3 / +1 | +0 / +0 / +0 | +1.1 / -0.0 / +0.9 | +1.4 / +7.0 / -2.0 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18, 2023-25); 2 (2015-18 spread/log loss; 2023-25 log loss) |
| Injuries x travel | points | +0.001 / -0.004 / -0.002 |  | -2 / +4 / -2 | +0 / +0 / +0 | +0.3 / -0.8 / -0.1 | +8.1 / -4.7 / -4.4 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18); 2 (2015-18 spread/log loss; 2023-25 spread) |
| Injuries x wind (OL out, skill value out) | points | -0.004 / +0.003 / -0.002 |  | -4 / -1 / +3 | +0 / +0 / +0 | +0.4 / +0.3 / +0.1 | -14.6 / -1.1 / -8.4 | not run (fails 1 or 2) | not adopted: rule 1 (2019-22); 2 (2015-18 spread/log loss; 2019-22 spread/log loss; 2023-25 log loss) |
| Injuries x primetime | points | -0.002 / +0.000 / +0.000 |  | +2 / +4 / +0 | +0 / +0 / +0 | -0.5 / +0.0 / -0.0 | +0.8 / +1.1 / +4.3 | not run (fails 1 or 2) | not adopted: rule 1 (2019-22, 2023-25); 2 (2019-22 log loss) |
| OL starters out x opponent pass rush | points | -0.000 / -0.001 / +0.000 |  | -3 / +2 / +0 | +0 / +0 / +0 | +0.7 / -0.2 / +0.2 | +10.5 / -1.7 / -3.6 | not run (fails 1 or 2) | not adopted: rule 1 (2023-25); 2 (2015-18 spread/log loss; 2023-25 log loss) |
| Opponent secondary starters out (and x own passing) | points | -0.001 / -0.002 / -0.001 |  | +1 / +1 / -5 | +0 / +0 / +0 | -0.3 / -0.3 / +0.6 | +9.2 / +10.3 / +6.5 | 50 / 25 / 25 (4 draws) | not adopted: rule 2 (2023-25 spread/log loss) |
| Opponent front-seven starters out (and x own rushing) | points | -0.002 / -0.001 / -0.001 |  | -6 / +1 / +1 | +0 / +0 / +0 | +0.8 / -0.4 / -0.4 | +0.4 / +0.4 / +1.6 | 75 / 88 / 62 (8 draws) | not adopted: rule 2 (2015-18 spread/log loss) |
| Top two receivers both out | points | +0.002 / -0.000 / +0.000 |  | +1 / +0 / +0 | +0 / +0 / +0 | +0.4 / -0.0 / -0.0 | +1.5 / +0.7 / -4.0 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18, 2023-25); 2 (2015-18 log loss) |
| Backup QB: QB out x his rating, x his experience | points | +0.002 / +0.002 / +0.000 |  | -4 / +4 / +0 | +0 / +0 / +0 | +1.1 / -0.3 / +0.1 | -1.0 / +5.1 / -4.4 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18, 2019-22, 2023-25); 2 (2015-18 spread/log loss; 2023-25 log loss) |
| Injuries on both sides (own defense, opponent offense) | points | +0.003 / -0.000 / +0.004 |  | +3 / -1 / -2 | +0 / +0 / +0 | +1.2 / -0.5 / +0.6 | +16.6 / +12.0 / +3.7 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18, 2023-25); 2 (2015-18 log loss; 2019-22 spread; 2023-25 spread/log loss) |
| Coach's residual when missing starters | points | +0.005 / +0.001 / -0.002 |  | -1 / +4 / +0 | +0 / +0 / +0 | +0.6 / +0.1 / -0.3 | +6.4 / -6.4 / -1.0 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18, 2019-22); 2 (2015-18 spread/log loss; 2019-22 log loss) |
| Injuries on both teams (total) | total | -0.001 / -0.004 / -0.000 | -0.004 / -0.018 / -0.001 | +0 / +0 / +0 | +6 / -6 / -13 | +0.0 / +0.0 / +0.0 | +0.0 / +0.0 / +0.0 | 100 / 100 / 62 (8 draws) | not adopted: rule 2 (2019-22 totals; 2023-25 totals) |

Effect sizes (the live equation fit on every regular-season game 2013-2025 with the idea added: points per unit and per standard deviation; share of games where the input is not zero):

- Injuries x bye / short week: inj_bye: -0.926/unit, -0.158/sd, nonzero 3%; inj_short: +0.506/unit, +0.105/sd, nonzero 4%
- Injuries x travel: inj_miles: +0.221/unit, +0.170/sd, nonzero 28%
- Injuries x wind (OL out, skill value out): ol_wind: -0.023/unit, -0.083/sd, nonzero 12%; skill_wind: -1.294/unit, -0.156/sd, nonzero 61%
- Injuries x primetime: inj_prime: -0.156/unit, -0.052/sd, nonzero 11%
- OL starters out x opponent pass rush: ol_x_rush: +4.631/unit, +0.029/sd, nonzero 17%
- Opponent secondary starters out (and x own passing): opp_db_out: +0.254/unit, +0.122/sd, nonzero 18%; opp_db_x_pass: -5.560/unit, -0.124/sd, nonzero 18%
- Opponent front-seven starters out (and x own rushing): opp_front_out: +0.091/unit, +0.047/sd, nonzero 18%; opp_front_x_rush: -0.033/unit, -0.000/sd, nonzero 18%
- Top two receivers both out: wr12_out: -0.103/unit, -0.005/sd, nonzero 0%
- Backup QB: QB out x his rating, x his experience: qbout_x_rating: +0.800/unit, +0.016/sd, nonzero 3%; qbout_x_exp: -0.071/unit, -0.074/sd, nonzero 3%
- Injuries on both sides (own defense, opponent offense): def_snap_out: +0.181/unit, +0.120/sd, nonzero 55%; opp_off_snap_out: +0.150/unit, +0.099/sd, nonzero 54%
- Coach's residual when missing starters: coach_inj_r: -0.173/unit, -0.064/sd, nonzero 17%; opp_coach_inj_r: -0.063/unit, -0.023/sd, nonzero 17%
- Injuries on both teams (total): x_snap_out_all: +0.318/unit, +0.550/sd, nonzero 89%

## Coaching matchups

**What the pulled data has.** No source the weekly run pulls names offensive or defensive coordinators or play-callers: the schedule carries head coaches only, and the participation file, FTN charting, the play-by-play and nflmodel/scheme.py carry no staff fields. A coordinator table is therefore a new data source (rule 4). I did not build one by hand: it could not be built reliably from pulled data, and a table typed from memory would put unverified inputs in front of the rule. While this study was running, another session wrote data/reference/coordinators.csv (nflmodel/coordinators.py, from Wikipedia's team-season articles, 22:35 on 29 Sep 2026). It has a clean OC and DC for about 80% of team-seasons 2013-2025 (82 rows failed on rate limits, 26 have no staff list, one is garbled) and nothing for 2026, and it names coordinators, not play-callers. It was used as found for two rows, both marked as failing rule 4 whatever they score: a new offensive coordinator (own) and a new defensive coordinator (the opponent's), against last season's; and the OC's points residual in earlier games against this DC. Both fail rule 1 as well (new coordinators -0.003 / +0.002 / +0.005; OC vs DC +0.002 / -0.002 / +0.001, and 7 spread wins lost on 2015-18). Mid-season coordinator changes cannot be dated from the table (it lists the names, not the weeks), so the first-listed coordinator is taken as the season's.

**The stand-in the data supports.** From the play-by-play (every season, as of each week, last 16 games): pass rate over expected, shotgun and no-huddle rates, and the defense's sack rate. From the participation file (published after each season, so only last season's is honest for this season; man/zone is known from 2018, so the coverage matchup exists from 2019, blitz and box from 2017): the defense's man rate, blitz rate and light-box rate, and the offense's EPA against man and zone, against a blitz and not, and running into a light and a heavy box, combined into the offense's expected gain against this defense's mix. FTN's play-action and motion exist from 2022 only, so they cannot be scored on 2015-18 or 2019-22 and cannot pass rule 1; they were not run. The head coach's residual against the defense's coverage family (man-heavy or zone-heavy last season) stands in for play-caller against coordinator. Every row fails rule 1; the worst is the run-into-light-box matchup (+0.019 on 2015-18).

| Idea | Equation | Team points miss change | Total miss change | Spread flag W-L change | Totals flag W-L change | Log loss change (x1000) | Moneyline units change | Placebo percentile | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| Scheme: pass rate over expected, shotgun, no-huddle; opponent sack rate | points | +0.011 / +0.004 / -0.000 |  | -9 / +3 / -2 | +0 / +0 / +0 | +3.6 / +0.9 / -0.3 | -4.1 / -10.7 / -6.2 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18, 2019-22); 2 (2015-18 spread/log loss; 2019-22 log loss; 2023-25 spread) |
| Pass rate over expected x opponent sack rate | points | -0.005 / +0.000 / +0.003 |  | +4 / +3 / +0 | +0 / +0 / +0 | +0.2 / -0.1 / +0.7 | +23.4 / +2.8 / +0.3 | not run (fails 1 or 2) | not adopted: rule 1 (2019-22, 2023-25); 2 (2015-18 log loss; 2023-25 log loss) |
| Offense vs man/zone, weighted by the defense's man rate (last season) | points | +0.000 / +0.005 / -0.000 |  | +0 / -3 / -2 | +0 / +0 / +0 | -0.0 / +0.8 / -0.3 | +0.0 / -14.9 / -2.7 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18, 2019-22); 2 (2019-22 spread/log loss; 2023-25 spread) |
| Offense vs blitz, weighted by the defense's blitz rate (last season) | points | +0.007 / +0.003 / -0.001 |  | +1 / -1 / +1 | +0 / +0 / +0 | -0.2 / +0.2 / +0.4 | +14.4 / +2.0 / +3.5 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18, 2019-22); 2 (2019-22 spread/log loss; 2023-25 log loss) |
| Run offense vs light box, weighted by the defense's light-box rate (last season) | points | +0.019 / +0.001 / -0.001 |  | +0 / +4 / -2 | +0 / +0 / +0 | +2.0 / +0.4 / -0.0 | -24.3 / +1.3 / +6.0 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18, 2019-22); 2 (2015-18 log loss; 2019-22 log loss; 2023-25 spread) |
| Head coach vs the defense's coverage family (residual history) | points | +0.000 / -0.007 / +0.006 |  | +0 / -8 / -8 | +0 / +0 / +0 | -0.0 / -1.7 / +0.2 | +0.0 / +30.6 / +49.6 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18, 2023-25); 2 (2019-22 spread; 2023-25 spread/log loss) |
| Scheme pace: shotgun and no-huddle (total) | total | +0.023 / +0.003 / -0.004 | +0.061 / +0.006 / +0.017 | +0 / +0 / +0 | -8 / -8 / -9 | +0.0 / +0.0 / +0.0 | +0.0 / +0.0 / +0.0 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18, 2019-22, 2023-25); 2 (2015-18 totals; 2019-22 totals; 2023-25 totals) |
| Coordinators: new OC (own), new DC (opponent's) | points | -0.003 / +0.002 / +0.005 |  | +1 / +2 / +1 | +0 / +0 / +0 | +0.8 / +0.1 / +0.3 | +1.5 / -15.7 / +2.8 | not run (fails 1 or 2) | not adopted: rule 1 (2019-22, 2023-25); 2 (2015-18 log loss; 2019-22 log loss; 2023-25 log loss); 4 (the coordinator table is not a weekly pull) |
| Coordinators: OC vs this DC (points residual history) | points | +0.002 / -0.002 / +0.001 |  | -7 / -1 / -2 | +0 / +0 / +0 | +0.1 / +0.8 / +0.3 | +15.0 / -20.3 / -7.2 | not run (fails 1 or 2) | not adopted: rule 1 (2015-18, 2023-25); 2 (2015-18 spread/log loss; 2019-22 spread/log loss; 2023-25 spread/log loss); 4 (the coordinator table is not a weekly pull) |

Effect sizes (the live equation fit on every regular-season game 2013-2025 with the idea added: points per unit and per standard deviation; share of games where the input is not zero):

- Scheme: pass rate over expected, shotgun, no-huddle; opponent sack rate: pass_oe_r: -0.017/unit, -0.066/sd, nonzero 100%; shotgun_r: -0.274/unit, -0.031/sd, nonzero 100%; nohuddle_r: +1.569/unit, +0.144/sd, nonzero 100%; opp_def_sack_r: -8.223/unit, -0.105/sd, nonzero 100%
- Pass rate over expected x opponent sack rate: passoe_x_rush: +0.515/unit, +0.027/sd, nonzero 100%; opp_passoe_x_rush: +1.175/unit, +0.061/sd, nonzero 100%
- Offense vs man/zone, weighted by the defense's man rate (last season): cov_match: -1.428/unit, -0.082/sd, nonzero 55%; opp_cov_match: +3.755/unit, +0.215/sd, nonzero 55%
- Offense vs blitz, weighted by the defense's blitz rate (last season): blitz_match: +1.483/unit, +0.022/sd, nonzero 70%; opp_blitz_match: -5.703/unit, -0.084/sd, nonzero 70%
- Run offense vs light box, weighted by the defense's light-box rate (last season): box_match: -5.218/unit, -0.084/sd, nonzero 70%; opp_box_match: -10.721/unit, -0.172/sd, nonzero 70%
- Head coach vs the defense's coverage family (residual history): coach_vs_family: +0.389/unit, +0.299/sd, nonzero 53%; opp_coach_vs_family: -0.290/unit, -0.223/sd, nonzero 53%
- Scheme pace: shotgun and no-huddle (total): x_shotgun_sum: +0.227/unit, +0.036/sd, nonzero 100%; x_nohuddle_sum: +3.411/unit, +0.445/sd, nonzero 100%
- Coordinators: new OC (own), new DC (opponent's): new_oc: +0.068/unit, +0.032/sd, nonzero 31%; opp_new_dc: +0.073/unit, +0.032/sd, nonzero 27%
- Coordinators: OC vs this DC (points residual history): oc_vs_dc: -0.283/unit, -0.070/sd, nonzero 19%

## Rule 5: the passing pieces together

Nothing passed rules 1 to 3, so there is nothing to combine.

## Code change

None. Nothing passed rules 1 to 3, so nothing in nflmodel/ changes. Had the turf flag passed, the change would have been one line: add "turf" to SIT_FEATS in nflmodel/model.py, with prep() setting it to 1.0 when the schedule's surface is anything other than grass or dessograss (a missing surface taken as the stadium's usual one), which the weekly run already pulls; the page would have gained one line in the breakdown.

## What the readings say, in plain words

- Coach against coach history predicts nothing: the next meeting's residual correlates with the earlier meetings' at -0.02 overall and +0.06 for the 183 games between coaches who had met eight or more times. With two meetings a year at most, the samples never get big enough to separate a real edge from noise, and shrinking them toward zero leaves almost nothing.
- The strongest persistent coach reading is the coach's whole career residual (correlation 0.036 with the next game), and it still splits the windows.
- Turf adds about 2.3 raw points a game over grass; after the model, turf games still run about 1 point higher in total than grass games, outdoors 1.4. It is real but already mostly carried by the dome input, the teams' ratings and the weather; the residual gain in the points equation is 0.001-0.002 points and a shuffled turf column does as well half the time.
- The Monday night home team ran 1.4 points under the model's margin and MNF totals 1.7 under, over 200 games each; the Thanksgiving home team ran 4.9 points under in 32 games. Each lowers the miss on every window as an input but costs spread wins somewhere, and neither survives the gate.
- The referee's residual against the model's total improves 2015-22 by a lot and hurts 2023-25: it is correcting the live referee input on the seasons it was fit to.
- Of the live terms, cold and dome in the total equation and the QB-out flag in the points equation would each lower the miss on all three windows if removed, but each removal costs one bet or the calibration on one window; they stay and are the ones to re-check after 2026.

## Recorded

Per the rule, everything that failed stays a reading only and is to be recorded in docs/how_it_works.md (not edited here, per this study's constraints). Every row, with all three markets on every window, is in reports/situational_game.csv.
