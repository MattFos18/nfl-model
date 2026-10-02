# More shadows (2 Oct 2026)

Every rule a study found promising but did not adopt, checked for whether it can be tracked live: a `picks.rule_mask` side rule with a
reading known before kickoff, live and on the backtest, and no market input beyond the closing line used for grading. Each one that
can is added to `picks.SHADOWS` and `picks.HIDDEN_SHADOWS`: graded every run, never bet, never shown on the page; `nflmodel/shadow_watch.py`
measures it against the rule it would replace (the spread flag, the totals flag for a totals rule, break-even for a rule that ignores
the model) and `ready_checks` opens a ready-check issue if one pulls clear. Nothing in the live rules, thresholds, model or page changes.

Records: regular season, weeks 1 to 17, at the closing line, pushes dropped (`picks.rule_records`), on the stored prediction table.
The forecast rules (rain, cold, the totals flag in wind) start in 2018, so their 2015-18 column is 2018 alone. These rules were
found by looking at past results, so none of these records is evidence the rule wins; the live record decides.

| Candidate | Source | 2015-18 | 2019-22 | 2023-25 | Status |
|---|---|---|---|---|---|
| Under, forecast rain chance 50%+ (outdoor games) (`shadowrain`) | reports/rain_under_retest.md, reports/weather_forecast_retest.md | 11-9 | 55-30 | 36-21 | added (hidden) |
| Under, forecast temperature below 32 F (outdoor games) (`shadowcold`) | reports/weather_forecast_retest.md | 4-2 | 21-15 | 11-10 | added (hidden); the study rejected it (27.5% of shuffles as good), tracked anyway as possible |
| Under, model total 3+ points below the line (`shadowunder3`) | decision log 25 Sep 2026; docs/todo.md | 64-48 | 113-63 | 28-23 | added (hidden) |
| Under, 55%+ chance and forecast wind 10+ mph (`shadowunderwind`) | reports/friend_ideas.md, reports/wind_forecast.md | 10-9 | 81-49 | 46-27 | added (hidden); the friend's study's version on the wind that happened failed its placebo |
| Total, boosted trees' own total 9.5%+ of the line off it, either side (`shadowtreestotal`) | reports/ml_compare.md; docs/todo.md | 139-99 | 114-88 | 96-63 | added (hidden) |
| West Coast or Mountain team on the road at 1pm ET, any game (`shadowwestcoast`) | reports/audit.md section 4; decision log 21 Sep 2026 | 42-58 | 57-43 | 48-38 | added (hidden); loses 2015-18 |
| 4+ edge, model's side the road underdog (`shadowroaddog`) | reports/bet_rules_sweep.md, reports/spread_research.md | 30-11 | 34-17 | 15-7 | added (hidden) |
| 4+ edge, model's side a dog at +0.5 to +3 (`shadowsmalldog`) | reports/spread_research.md | 20-11 | 24-15 | 19-6 | added (hidden) |
| 3.5+ edge on dogs, 4+ on every other side (`shadowdog35`) | reports/favorite_review.md | 85-68 | 100-72 | 55-31 | added (hidden) |
| 4+ edge, weeks 1 to 4 only (`shadowwk4`) | reports/bet_rules_sweep.md | 23-12 | 19-12 | 19-5 | added (hidden) |
| 4+ edge, weeks 1 to 15 only (`shadowwk15`) | reports/bet_rules_sweep.md | 59-46 | 73-42 | 36-16 | added (hidden) |
| 6+ edge (`shadow6`) | decision log 21 Sep 2026 | 7-11 | 15-12 | 8-3 | added (hidden); loses 2015-18 |
| Under, forecast rain chance 70%+ | reports/rain_under_retest.md | 6-6 | 34-22 | 14-11 | not added: a subset of the 50%+ rule, fails 2018 and 6% of shuffles as good (the study's own verdict) |
| Under, model total 4+ points below the line | decision log 25 Sep 2026 | 35-24 | 75-33 | 15-11 | not added: a subset of the Under 3+ shadow |
| Under in every prime-time game, blind | reports/bet_rules_sweep.md | 105-104 | 122-82 | 89-82 | not added: loses units on 2015-18 and 2023-25 at -110; the totals flag in prime time is already tracked (shadowunderprime) |
| Total 6+ points off the line, either side | decision log 21 Sep 2026 | 19-15 | 34-18 | 13-11 | not added: overs lose every way tried (experiments/totals_fix.py); the under side is the Under 3+ shadow |
| Chance the wind reaches 10+ mph (walk-forward fit) | reports/wind_forecast.md | n/a | n/a | n/a | not added: needs a fitted wind-chance model that does not run live |
| Under at a Blend gust of 25+ mph | reports/weather_forecast_retest.md | n/a | n/a | n/a | not added: the gust exists Nov 2018 to 2019 only; no live reading |
| Totals flag, or wind 10+ at a 50%+ chance | reports/friend_ideas.md | n/a | n/a | n/a | not added: the wind under already bets every 10+ game, so this is the totals flag plus the wind under, both tracked |
| Teaser legs on favourites at -1.5 to -2.5 | reports/friend_ideas.md | n/a | n/a | n/a | not added: 61.7% on 2023-25, under a leg's break-even at -130 (75%) |
| Moneyline on the flag's side | reports/bet_rules_sweep.md | n/a | n/a | n/a | not added: better than the spread on one window only, and needs each bet's moneyline price, which the tracker does not log for shadows |
| Rules on the opener or line moves (bet timing) | reports/bet_rules_sweep.md | n/a | n/a | n/a | not added: a market input |
| Betting splits (money and bet share) | docs/todo.md | n/a | n/a | n/a | not added: a market input; Matt, 29 Sep: build nothing on splits until a history can be tested |
| Rain, cold, gust and wet-or-cold points in the total | reports/weather_forecast_retest.md, reports/friend_ideas.md | n/a | n/a | n/a | not added: model changes, not side rules (all rejected) |
| Game situations (121 ideas; the closest, turf) | reports/situational_game.md | n/a | n/a | n/a | not added: none passed; the closest did no better than luck |
| Already tracked: 4.5+, dogs, weeks 1-13, trees 5+, the hook, unders 59% early, road sides, road 4 / home 6, unders 60%+, prime-time unders, dog teaser legs, the wind under | picks.SHADOWS | n/a | n/a | n/a | already tracked |
