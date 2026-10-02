# Audit: calibration_recheck (2 Oct 2026)

**Verdict: holds with caveats.** The numbers are right and reproduce exactly. The fits use only earlier seasons and match picks.py. But most of the "beats raw" wins after 2018 are inside the noise, and so are both teaser shortfalls.

Sources: `experiments/calibration_recheck.py`, `reports/calibration_recheck.md`, `reports/calibration_recheck.csv`,
`reports/calibration_recheck_results.md`, `nflmodel/picks.py`, `nflmodel/model.py`, `nflmodel/backtest.py`. My scripts are
in the session scratchpad: `rerun.py` (a full rerun with outputs sent to the scratchpad), `audcal_indep.py` (an independent
re-score and leak test) and `audcal_lines.py`.

## Checks

1. **Look-ahead: pass, with one inherited caveat.**
   - **Leak test.** I wiped the outcomes and predictions of season s and later (s = 2017, 2020, 2023, 2025) in both the
     prediction table and games, then refit. `picks.calibration`, `over_calibration`, `home_calibration` and
     `tease_calibration` for season s came out identical every time (0 failures).
   - **Fit in force.** Every season is scored with the fit from seasons before it. The fits are made before Week 1, with
     no in-season updating. The line each game was priced at equals the `games.parquet` closing line on all 2,895
     regular-season rows.
   - **Caveat.** 2015-17 are still priced on the weather that happened, because no forecasts are stored before 2018. The
     rerun matches the stored pre-#389 `pred_v3` exactly for 2015-17, and it differs on 131-201 games a season from 2018.
     So the 2016-17 raw chances, and every fit that includes 2015-17 rows, still carry that look-ahead. The report does
     not say this.
2. **Market inputs: pass.**
   - The closing line and results are used only to grade and to fit the mappings. Cover is defined against the line.
   - Nothing in the study changes a model input or a flag.
3. **Every window: pass as computed.**
   - **Rerun.** The full rerun (about 3 minutes, reading a copy of HEAD's trees cache) reproduced
     `calibration_recheck.csv` and `_results.md` byte for byte.
   - **Independent re-score.** My own row building, using the production `cal_p` / `over_cal_p` / `home_cal_p` /
     `tease_raw` / `tease_cal_p` with the raw chances unclipped, matches every csv log loss and Brier to 5 decimals.
   - **Report vs csv.** Every number in the report matches the csv, including the pooled teaser figures (0.60631 /
     0.60575, 0.62088 / 0.61597) and all 15 spread-cut records. One cosmetic slip: C1's 2016-18 calibrated log loss is
     ln 2 = 0.69315, printed as 0.6932 because it was rounded twice (it should read 0.6931).
   - **Rows and rules match picks.py.** Same rows, clipping, push and tie drops. Identity rules: home 2016 is the identity
     (256 games, under 500), and 2017 is fit on 510. Cover 2016-19 is flat (0, 0), and 2020 is fit on 2019. So
     "2016-18; C3 from 2017; C1 flat before 2020" is stated correctly. Dropping 2016 from C3 cannot change the result,
     because raw and calibrated are equal there; with 2016 in, it is still better (0.61466 -> 0.61301).
   - **Window caveat.** C1's 2016-18 "pass" (and 2019 within 2019-22) only tests a flat 50% against a hot raw curve, not
     the fitted calibration. The record-only fit from 2015 does beat raw on all three windows (0.6952 / 0.6927 / 0.6924).
   - **Pipeline caveat.** "Trees read from the stored cache" is only partly true. The rerun reused 236 cached fits and
     refit 168, the weeks whose test rows changed with the forecast weather. Same laptop, same result. GitHub's runner
     will refit those itself (`model.py` notes cross-machine rounding).
4. **Placebo: not applicable (agreed).** No new input is added. As a noise check instead, I computed the paired standard
   error of (calibrated minus raw) log loss.
5. **Snooping: pass.**
   - **Variants.** Five calibrations as coded, one record-only refit and two fix candidates. The fix candidates were
     added in a second run after the teaser legs failed (scratchpad `run1.log` / `run2.log`). That follows the
     pre-registered step (b), and both failed, so nothing was gained by looking. The cut table is labeled
     description-only.
   - **Caveats.**
     - I cannot verify when the pre-registration was written; it sits in the same file as the results.
     - `TEASE_SLOPE` (shift for spreads) was chosen on 28 Sep partly from 2023-25, so that window is not held out for the
       teaser form.
6. **Sample size: inside the noise for most claims.**
   - **Teaser shortfalls.** Change in log loss (t value): spreads 2016-18 +0.00046 (t +0.41), totals 2023-25 +0.00132
     (t +0.31). Pure noise.
   - **Wins that are also noise:**
     - C2: 2019-22 t -0.31, 2023-25 t -0.07 (calibrated better in 1 of 3 seasons).
     - C3: t -1.09 / -0.58 / -0.53.
     - C1: 2019-22 t -1.25, 2023-25 t -1.43.
     - C4s: t -1.09 / -0.56.
   - **Clear wins (|t| > 2):** C1 2016-18 (the flat 50%), C2 2016-18 and C4t 2016-18.
   - **Total-leg slope.** The total-leg fit's slope is about 0 (-0.07 to +0.20 across 2016-20), so the calibrated total
     leg is close to a constant hit rate. It beats raw because raw runs hot, not because it ranks games.
7. **Leak test (`nflmodel.audit`): not run.** The study touches no feature or walk-forward code; my calibration leak test
   (check 1) covers the fits.

**Teaser decision: sound, and openly disclosed.**
- The identity is raw, which is worse than today's calibration on two windows of three and pooled. Matt's pre-approval
  covers only fixes that "clearly win", so applying the default without his yes would break the CLAUDE.md rule.
- The report should say plainly that this departs from the pre-registered default.
- The `picks.py` comment at TEASE_SLOPE ("both forms beat the raw chance on ... every window") is now stale.

**Worktree hygiene (not the study's fault).**
- Something else in this worktree rewrote `data/processed/trees_cache.parquet` at 14:00:29 and again at 14:01:01. It
  went from HEAD's 114 KB to 16 KB, then 28 KB. The study's own run ended at 13:57 with saving disabled, and my rerun used
  a scratchpad copy.
- Run `git checkout -- data/` before any commit.
- The HEAD `pred_v3` predates #389, so the site's calibrations are fit on the old table until the next weekly run.

## What would change the verdict

- **The next weekly run.** After it rebuilds `pred_v3` with the forecast weather (trees refit on GitHub), the teaser
  margins (0.0005, 0.0013) could flip sign, and C2 / C3 2023-25 could too. Rescore them on that table.
- **A season-blocked or bootstrap test.** If it showed C2, C3 or C4 no better than raw pooled, "holds" would become "no
  measurable effect either way".
- **Forecasts for 2015-17.** Stored forecasts there would remove the remaining weather look-ahead from 2016-18 and from
  every fit.
