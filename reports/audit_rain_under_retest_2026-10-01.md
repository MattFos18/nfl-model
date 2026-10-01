# Audit: rain under on top of the live totals bets (1 Oct 2026)

Study: `experiments/rain_under_retest.py`, `reports/rain_under_retest.md` / `.csv`. Origin: `reports/weather_forecast_retest.md`.
Claim: the blind under at a GFS MOS rain chance of 50%+ adds 22-9 (+12.1u) on games neither live totals rule bets, helps
every window when added, 0.5% of 200 shuffles as good. Proposal: a hidden shadow, graded live, not bet.

**Verdict: holds with caveats, as a hidden shadow only. It is not strong enough to bet.**

## Checks

1. **Look-ahead: pass.** `gfs_pop_d0` is the GFS MOS run `forecast_history.last_run`: the newest 00/06/12/18Z run at least 5 hours
   before kickoff. Stored history: lead time 5 to 10 hours (median 6), 0 rows missing a run time. 2 of 1,558 games use the
   day-before run instead, and none of the 31 extra bets does. The rain chance is the largest 6-hour chance overlapping the first 3 hours, read
   from that run, not the observed weather. The totals flag uses `p_over_emp` from `model.walk_forward`: each week is refit on
   earlier games only, and the misses come from that fit's training games. One gap: the flag set itself includes `model.RAIN_FC` (the
   50% rain input), which was picked on these 2018-25 results the same day. That reuses the data, but it is not a leak.
2. **Market inputs: pass.** The rain under reads only the forecast. The closing total is used only to grade the bet and, through
   the existing flag, to decide which games are "already bet".
3. **Every window: pass, but thin.** Rerun (79 s): the md and csv match the report exactly. The extra bets went 3-1 / 10-5 / 9-3. The combined
   record is better on 2018, 2019-22 and 2023-25 in both wins minus losses and units. "2015-18" is really only 2018: 4 extra bets, since there are no forecasts before 2018.
   By season the extra bets went 2018 3-1, 2019 1-3, 2020 1-0, 2021 5-0, 2022 3-2, 2023 5-2, 2024 2-0, 2025 2-1. The blind rule went 7-8 in 2025.
4. **Placebo: pass.** I reran the study's own statistic with 2,000 within-season shuffles: 0.006 as good (study: 0.005 of 200). The shuffle
   median is -10.1u (non-live games go under only 46.4% of the time), the 90th percentile +1.5u and the 99th +10.7u. The real result is +12.1u.
5. **Snooping: fail (so this is a shadow, as proposed).** The 50% cut came from looking at results. The earlier study tried 10 blind cuts
   (plus wind for reference) and 8 band ideas, `rain_points.py` tried about 10 rain variants, and this study tried 2 more. The cut sits at a sharp peak
   on the extra games: 40% +2.7u (2019-22 13-14), 45% +7.5u (2019-22 11-10), 50% +12.1u, 55% +10.2u, 60% +7.3u
   (2018 0-1). Taking about 13 cuts into account, the 0.005 to 0.006 placebo share becomes about 0.07 to 0.08. That is not
   significant. It also depends on which forecast run is used: with the day-before run, the same rule goes 22-18 (+2.2u).
6. **Sample size: fail as a bet, fine as a shadow.** 31 bets at 71%. The standard error at that size is about 0.5 / sqrt(31) = 9 points, so the result is
   about 2 standard errors above the 52.4% needed to break even at -110 (one-sided binomial p = 0.028 before counting the other cuts tried).
   Per window: 4 / 15 / 12 bets, so standard errors of about 25 / 13 / 14 points. On 21 of the 31 bets the model already gave the
   under a 50-55% chance (15-6). In effect this is a lower totals-flag threshold in rain games.
7. **Leak test: not applicable.** No feature or walk-forward change. Not run.

Side effect: running the script rewrites `data/processed/trees_cache.parquet`, which was already modified before this audit. Do not commit it.

## What would change the verdict
- Live shadow record over the next 1-2 seasons. Expect only about 4 extra bets a season, so it will take years to show anything.
  If it is near 50% after about 30 live bets, drop it.
- The live reading must be the last GFS run at least 5 hours before kickoff (`wind_live` does this only when a line watch
  runs within about 10 hours of kickoff). An earlier, day-before reading would grade a different rule (22-18 in the backtest).
- To bet it, a pre-registered cut (keep 50%) would have to stay above break-even on fresh games, and the cut-curve peak
  would have to hold.
