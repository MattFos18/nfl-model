# Log

One dated line per change to the model, the bet rules, the data sources or the way we work. Newest first. The full
record of every study stays in `reports/decision_log.md`; this is the short version to skim at session start.

## 2 Oct 2026
- The backtest prices played games (2018 on) on the stored pre-kickoff forecast, not the weather that happened: `model.priced_weather`; QB form re-passes, wind points and the totals' rain fail the pre-registered bar (one and two checks), left for Matt; no wind curve beats the bands (reports/forecast_weather_backtest.md).
- Referee input (`ref_tot`) dropped from the totals equation: with the same-game leak fixed it fails the rule (#387).
- Two backtest leaks fixed: the referee prior counted the same game; Japan's wind used its post-kickoff run (now the day-before run); rescored in reports/leak_fix_rescore.md (#384).
- One unit a bet; quarter-Kelly retired from the page (#385).
- Data fixes: the starting QB who played, games abroad at their real site, recorded wind checked against the archive, the line before kickoff; new data checks (reports/data_fixes.md).
- Project wiki (`docs/wiki/`), `study` and `ship` skills, and the data-checker, site-fact-checker and pr-reviewer agents added.
- A named starter ruled out this week sets `qb_out` (#380).
- Every promising rule not adopted tracked as a hidden shadow, the rain under (`shadowrain`) among them (#379).
- Cards show only real bets; reverse line move chip (#377).
- A QB ruled out this week is priced at his replacement, not the named starter: `ratings.qbs_out_now` (#376).
- Cards' live badge comes from the page's own ESPN fetch (#375).

## 1 Oct 2026
- Injury retest (Questionable at the measured sit chance, linemen and defenders out): not adopted, costs the spread flag or fails a window (#374).
- Closing line value tracked on the live bets (`nflmodel/clv.py`); tracking only (#373).
- Wind and cold learned from forecasts instead of the weather that happened: not adopted.
- Blind rain under (GFS rain chance 50%+) re-tested on top of the new model: candidate hidden shadow (added 2 Oct as `shadowrain`, #379).
- Forecast rain (GFS MOS 50%+) in the totals equation: adopted with Matt's yes (`model.RAIN_FC`, #366).
- Rain, cold and gust bands re-tested on forecasts: none adopted; MOS 99 missing-wind bug fixed (#365).
- Wind points in the model's total: adopted (`model.wind_points`, #363).
- Wind under (forecast wind 10+ mph, outdoor, weeks 1-17) adopted as a bet (`picks.WIND_UNDER`, `wind_live.py`, #362).
- ESPN fills injury statuses player by player (#360); inactives logged from ESPN game rosters, not priced (#361).
- Study gate, data checks and bet-math tests (#370); Gitleaks hook, public-repo rules, model-auditor agent (#369).
- Unders at 60%+ and prime-time unders tracked as hidden shadows (`shadowunder60`, `shadowunderprime`).
