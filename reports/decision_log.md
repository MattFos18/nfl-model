# Decision log

Every stat, adjustment, weight and rule is a claim that had to pass a test before it counts. Newest first.
Yardsticks: model pieces on points miss (mean absolute error on team points, margin, total); betting signals
on record, ROI at -110 and, once logged, closing line value. Tuned on 2019 to 2022, judged on 2023 to 2025.

| Date | Claim | Test | Result | Decision |
|---|---|---|---|---|
| 21 Sep 2026 | 3.0 beats the old model | Both run walk-forward on the same 1,871 games, 2019 to 2025 (`reports/backtest_v3.md`) | Held-out 2023 to 2025 team points miss 7.34 vs 9.02; margin 10.16 vs 12.66; total 10.32 vs 12.80. Brier 0.220 vs 0.294 | 3.0 replaces the old model as the points engine |
| 21 Sep 2026 | 3.0 matches the closing line on points | Same games, model vs Vegas implied totals and closing spread and total | Held-out: team points 7.34 vs Vegas 7.21; margin 10.16 vs 9.74; total 10.32 vs 10.12. Brier 0.220 vs market 0.210 | Within 0.13 points per team of the target. Not there yet on margin (0.4 behind) |
| 21 Sep 2026 | 3.0 beats the closing line after the vig with the sheet's rules (3 pt spread, 4 pt total) | Held-out 2023 to 2025 | Spreads 107-107 (50.0%), -4.5% ROI over 214 bets. Totals 71-65 (52.2%), -0.3% ROI over 136 bets. 2023 to 2025 by season: spreads -3.2%, +4.6%, -15.8% | Fails. The model's disagreements with the close do not carry money at this stage. Picks are readings, not bets |
| 21 Sep 2026 | Tuning the thresholds helps | Threshold sweep on 2019 to 2022 (best with 100+ bets: 2 pt spread, 3 pt total), then held-out | Held-out with 2 / 3: spreads 49.2% (-6.1%), totals 49.2% (-6.1%), worse than 3 / 4 | Keep 3 / 4 as the display rule. Nothing in the sweep is stable across windows |
| 21 Sep 2026 | The old model's 2024 slip (130-102) reflects the model | Python copy of the sheet, 2024 regular season, 3 / 4 rules | Model alone 112-91 on spreads (55.2%), 98-86 on totals; across 2019 to 2025 it is 49.4% and 50.2%. Calibration: games the sheet called 91% for the favourite won 66% | 2024 was the good year of seven. The Poisson grid is the reason the win odds were far too confident |
| 21 Sep 2026 | Market plus model beats model alone | pred = a x model line + (1 - a) x closing line, a fit on 2019 to 2022 by margin miss | Best a = 0.1, and it improves margin miss by 0.001 on the tuning window and makes it 0.01 worse held out. Every share above 0.1 is worse | The close is the better line, and the model adds nothing to it yet. Shown on the game card; bet selection is unchanged by it |
| 21 Sep 2026 | The QB rating earns its place | Ablation on 2019 to 2022 (`reports/ablation.csv`): drop the starting QB's decayed EPA per dropback | Team points miss rises 0.080, the largest of any group | Keep. Largest single input in the regression (1.5 points per standard deviation) |
| 21 Sep 2026 | Weather and dome earn their place | Same ablation | Miss rises 0.040 without wind, cold and dome | Keep. Wind is worth -0.13 points per mph on the outdoor team's score |
| 21 Sep 2026 | Points ratings, EPA ratings, rest, division, primetime, pace earn their place | Same ablation | Points ratings +0.017, EPA +0.008; rest, division, primetime and pace all within 0.007 of zero | Keep points and EPA. Rest, division, primetime and pace kept as neutral; retest each offseason |
| 21 Sep 2026 | Success rate earns its place | Same ablation | Miss falls 0.013 without it | Dropped from the regression. Still computed and shown |
| 21 Sep 2026 | Pass/rush split earns its place | Same ablation | Miss unchanged (0.000) | Kept for the matchup breakdown on the game card; adds nothing to the score |
| 21 Sep 2026 | How far back the data goes | Grid on 2019 to 2022: game weight = decay per week (0.85 to 0.99) x offseason multiplier (0.3 to 0.8), ridge pull to average (2 to 32) (`reports/tuning_ratings.csv`) | Best: decay 0.90 per week, last season at 0.5 face value, pull 16. Spread of all 35 settings is 0.04 points; decay 0.99 (nearly flat) is the worst | Locked. A game from 8 weeks ago counts 43% of last week's; a game from last December about 15% |
| 21 Sep 2026 | Which stats predict future points | Correlation of each stat through Week 8 with points per game in Weeks 9 to 17, 2012 to 2025 (`reports/lab.md`) | Offense: EPA per play 0.50, points 0.49, pass EPA 0.49, success 0.45. Defense: nothing above 0.26. Same-season correlations run 0.7 to 0.9 and overstate everything | Rate offenses on EPA. Defense is mostly noise season to season, so the ridge pull matters most there |
| 21 Sep 2026 | Garbage-time filtering helps | Same lab table, `_ng` versions | EPA per play 0.50 with garbage time vs 0.46 without; success 0.45 vs 0.47 | Not adopted. Filtered EPA predicts no better |
| 21 Sep 2026 | Vegas sets the accuracy bar | Closing line miss, 2015 to 2025 | Team points miss 7.28, margin 9.82, total 10.45 | Targets for the points model |
| 21 Sep 2026 | Referee under trends persist | Top under refs 2012 to 2018, then 2019 to 2025 | 61 to 62% dropped to 49%. Correlation between the periods -0.25 | Not a signal. Shown as noise |
| 21 Sep 2026 | Referee home cover trends persist | Same split | Correlation +0.37, but only 8 refs | Weak. Retest with shrinkage |
| 21 Sep 2026 | Market misses QB changes | ATS after a starting QB change, 2012 to 2025 | 50.3% over 671 games. Miss 10.35 vs 9.99 normally | Priced by close. The player model's value is speed |
| 21 Sep 2026 | Last season still matters early | Regress rest-of-season margin on last season and season-to-date margin, 2012 to 2025 | This season's share of weight: 38% after 2 games, 60% after 4, 79% after 8. Last season is worth 0.40 of its face value in Week 1 | Use a decaying blend. Refit on EPA-based ratings (done above: 0.5) |

## What the held-out result means

The number one goal (accurate points for and against) is close: 7.34 per team against Vegas's 7.21, from 9.02 for
the old model. The betting goal (54% over 300+ bets) is not met: 50% on 214 spread bets. A model that
matches the close on points will not beat it by betting against it, because its errors and the market's
overlap. The paths that could still produce an edge, in order:

1. Timing. Bet at the opener or midweek, not the close, and measure closing line value. Needs the line log
   that starts in the first live week.
2. Information the close prices late: injuries and the player model, weather at kickoff.
3. Market signals: splits and reverse line movement, testable after a season of logging.

None of these can be backtested on the data we have today. That is the honest position for the go / no-go.
