# Leak fixes rescored (2 Oct 2026)

Fix 1: the referee prior (ref_tot, also ref_over and ref_pen) now counts only games that kicked off strictly before this one; the home row used to count the away row of the same game, this game's own total. Fix 2: the wind reading uses Japan's day-before run (jma_wind_d1), not its newest run (issued at or after kickoff); Open-Meteo keeps no 2018-2025 single runs to refetch.

Each variant is the live model refit walk-forward 2015-2025 (regular season; flags weeks 1-17 against the close).

| Variant | Window | Team miss | Total miss | Margin miss | Spread flag (4+) | Totals flag (55% under) | Wind under (10+ mph) |
|---|---|---|---|---|---|---|---|
| before | 2015-18 | 7.4082 | 10.7382 | 9.9491 | 68-55 | 137-127 | 23-19 |
| before | 2019-22 | 7.3426 | 10.4934 | 10.0204 | 80-51 | 202-146 | 143-89 |
| before | 2023-25 | 7.2439 | 10.1081 | 9.9041 | 40-21 | 98-73 | 83-52 |
| after | 2015-18 | 7.4107 | 10.7677 | 9.9491 | 68-55 | 133-122 | 24-20 |
| after | 2019-22 | 7.3635 | 10.5334 | 10.0204 | 80-51 | 183-141 | 141-88 |
| after | 2023-25 | 7.2454 | 10.1406 | 9.9041 | 40-21 | 75-62 | 77-52 |
| after_no_ref | 2015-18 | 7.4064 | 10.7624 | 9.9491 | 68-55 | 138-126 | 24-20 |
| after_no_ref | 2019-22 | 7.3635 | 10.5324 | 10.0204 | 80-51 | 182-142 | 141-88 |
| after_no_ref | 2023-25 | 7.2445 | 10.1410 | 9.9041 | 40-21 | 75-57 | 77-52 |

## ref_tot after the fix (study_gate: total miss, no ref_tot -> ref_tot)

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | NO | miss 10.7624 -> 10.7677 |
| better on 2019-22 | NO | miss 10.5324 -> 10.5334 |
| better on 2023-25 | yes | miss 10.1410 -> 10.1406 |
| no bet cost: spread flag, 2015-18 | yes | 68-55 -> 68-55 |
| no bet cost: totals flag, 2015-18 | NO | 138-126 -> 133-122 |
| no bet cost: wind under, 2015-18 | yes | 24-20 -> 24-20 |
| no bet cost: spread flag, 2019-22 | yes | 80-51 -> 80-51 |
| no bet cost: totals flag, 2019-22 | yes | 182-142 -> 183-141 |
| no bet cost: wind under, 2019-22 | yes | 141-88 -> 141-88 |
| no bet cost: spread flag, 2023-25 | yes | 40-21 -> 40-21 |
| no bet cost: totals flag, 2023-25 | NO | 75-57 -> 75-62 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |
| beats its placebo on 2015-18 | NO | 25 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2019-22 | NO | 31 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2023-25 | NO | 29 of 50 draws (need 45 of at least 50) |

Gate: FAIL (8 of 15); no market input and no look-ahead checked by the model-auditor agent

## What was checked for the same bug

`trends._prior_mean` is the one place a prior is built from team-game rows in row order. Rebuilt with the fix, only the
referee priors moved (ref_tot 6,766 rows, ref_over 7,016, ref_pen 7,366; ref_home_cover 2 rows, the one game pair where
the schedule lists the same referee at the same kickoff, 2024 Week 2). Unchanged: team_home_edge, h2h_cover, coach_ats,
qb_ats, off_loss, cold_edge, wind_edge, off_home_split (keyed one row per team per game). Filtered on earlier weeks and
not affected: ratings.window, the QB rating and qb_form, injury_table (previous game's snaps), continuity (last season),
model.record_before (cumulative wins minus the game's own), the wind-points pool (earlier seasons), player and position
values. ref_pen was also centred on the same season's league mean (games still to come); now the previous season's.
After the fix both rows of a game read the same ref_tot, and corr(ref_tot, the game's total) is -0.002 (it was 0.062).

## Japan-model wind

Open-Meteo's single-runs API returns no jma_gsm run for 2018 or 2024 (tried 2018-12-09 and 2024-12-08; a run from 27 Sep
2026 works), so the run 5+ hours before kickoff cannot be refetched. The reading uses the stored day-before value
(jma_wind_d1, lead 24-47 hours, present for every game that has d0). Live, Open-Meteo fills a future hour's d1 with the
newest run, so the live reading is never newer than the GFS cutoff; d0 is used only when d1 is missing and the run cannot
be past the cutoff. Not changed here: the current season's live log keeps the Japan value it recorded before kickoff.

## Variant count and decision

Three variants, fixed before the run (before, after, after without ref_tot); the placebo is ref_tot's own (seed 7).
ref_tot was one of three referee readings tried on 28 Sep (experiments/ref_noline.py). Clean, it fails parts 1, 2 and 3
of the round-3 rule. Recommendation: drop ref_tot from TOTAL_FEATS (needs Matt's yes; this change keeps it live).
The other 1 Oct adoptions (rain_fc, wind points) were measured with the leaky ref_tot in and are not rescored here.

## Audit

model-auditor (reports/audit_leak_fix_rescore_2026-10-02.md): "holds with caveats". Both leaks fixed (home and away rows
disagreed on ref_tot in 6,767 of 7,239 games before, 0 after), numbers and placebo reproduced exactly. Caveat: most of
the totals-flag drop is the referee fix (referee fix alone: 187-145 and 79-63 on 2019-22 and 2023-25), so wind points,
rain in the total, QB form in the total and the totals shadows were scored with the leak in and need rescoring. The
day-before Japan run's issue time is from Open-Meteo's lead-time definition, not confirmed run by run.

The sections from "What was checked" down are written by hand; the tables above are the script's output.
