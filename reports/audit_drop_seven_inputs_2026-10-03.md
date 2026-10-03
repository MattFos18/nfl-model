# Audit: drop_seven_inputs (3 Oct 2026, model-auditor)

**Verdict: holds with caveats.** Matt's margin condition is met on every window. It still holds when the boosted trees
are refit, and the live code reproduces the tested run exactly. Every gain is inside the noise, and three statements in
the report need fixing (below). Nothing blocks the change.

Worktree `agent-ad3f8b4390d79e554`, branch drop-seven-inputs, commit 78e26e37 on 0788403f. Stored runs: `%TEMP%/drop_seven_inputs/{live,drop}.parquet`
and `%TEMP%/input_ablation/{base,combined_P7_P8_P11_P13_P14_T3_T6}.parquet`. I rescored all four with my own scorer. It joins
games.parquet, uses the closing line, regular season, weeks 1-17 for the flags, and pushes out.

## Checks

**1. Numbers recompute: pass.** Every cell of the report's table matches my rescore. That covers the margin, team and
total miss, the raw and calibrated Brier, the calibration error and all three records:
- Margin miss: 9.9471 -> 9.9429, 10.0116 -> 10.0040, 9.9069 -> 9.8997.
- Spread flag: 68-58 -> 66-53, 78-49 -> 81-53, 37-19 -> 38-17.
- Totals flag: 132-111 -> 142-117, 175-140 -> 183-134, 76-55 -> 86-61.
- Wind under: unchanged.
- Calibrated chance: 1,020 / 1,050 / 815 games.

**2. Margin rule applied correctly: pass.** The tie limit is 0.0005. The changes are -0.0042, -0.0077 and -0.0072, all
better. The code applies the rule as `drop - live <= 0.0005` on each window.

**3. Look-ahead and market inputs: pass.** The change only removes inputs. Nothing new reaches either equation, and
lines are still used only for grading and pricing. I ran the leak test alone with the 17/9 input lists and the trees
cache stubbed (`audit.leakage_test()`, not the full audit, which rewrites reports/audit.md). All three changes were 0.0:
- ratings after corrupting future data;
- predictions after corrupting 2024 Week 10+ points;
- predictions after corrupting each game's own score.

**4. Live code matches what was tested: pass, with small caveats.**
- `model.FEATS` (17) and `TOTAL_FEATS` (9) equal the script's drop lists, element by element and in the same order.
- The background run of `python -m nflmodel.model` with the new code finished at 10:47. Its pred_v3.parquet is identical
  to drop.parquet on all 3,028 tested games: max difference 0.000000 on home/away expected points, spread, total, trees,
  p_home and p_over_emp.
- The tests that touch these inputs pass (qt_shadow, same_game_leak, live_hardening, data_fixes, standing_checks: 60 passed).
- qb_out and rain still reach the cards through `M.TREND_FEATS`, so the QB-out chip and the injury report's QB swap row
  (gated on `sd.get("qb_out")`) keep working. The QB-out term is now 0.
- neutral and div_game no longer reach the card `sides` (export_web line 1018). I found nothing on the page that reads
  them from there.
- Caveat: the hidden `shadowqtotals` equation also lost pf_sum, because it follows the live list. The report says only
  that it keeps its QB term, so its graded history will move.
- Caveat: docs/how_it_works.md still says "twenty-two" in present-tense places (line 73, "each of the 22 inputs" at
  line 1259). That is for site-fact-checker.
- Could not check: tie_check and export_web. Both rewrite reports/ and web/data, which this audit may not do.

**5. Run-to-run tree differences: pass. The decision does not depend on them.**
- Drop vs input_ablation's combined run: trees differ on 1,016 games (up to 0.98 points on a team, 0.21 on the spread).
  The ridge members and the total are identical.
- **The report's "the live run reproduces input_ablation's baseline exactly" is wrong.** Live vs base: trees differ on
  1,314 games (up to 0.89 points, 0.17 on the spread). The margin miss is 9.9471 vs 9.9467, 10.0116 vs 10.0118 and
  9.9069 vs 9.9072. Only the 4-decimal team miss and the records happen to match.
- Rerunning the trees moves the margin miss by at most 0.0012. The smallest gap in any pairing is 0.0035. All four
  pairings are better on every window:
  - drop vs live: -0.0042 / -0.0077 / -0.0072;
  - combined vs base: -0.0035 / -0.0081 / -0.0063;
  - drop vs base: -0.0038 / -0.0078 / -0.0075;
  - combined vs live: -0.0039 / -0.0079 / -0.0060.
- The records move by about one bet between reruns (2015-18 spread flag 66-53 vs 67-54). GitHub will refit the trees,
  so the published records will differ a little from the table.

**6. Sample size: the gains are inside the noise.**
- Paired standard error of the per-game margin change: 0.013 / 0.008 / 0.008 against gains of 0.004 / 0.008 / 0.007.
  The margin is "not worse" as a point estimate, not shown better.
- Bets per window (drop) and the standard error at that size:

| Rule | Bets 2015-18 / 2019-22 / 2023-25 | Standard error |
|---|---|---|
| Spread flag | 119 / 134 / 55 | 0.046 / 0.043 / 0.067 |
| Totals flag | 259 / 317 / 147 | 0.031 / 0.028 / 0.041 |

- Every record change (spread +3 / -1 / +3 net, totals +4 / +14 / +4) is within one standard error. The bets mostly
  overlap: spread flag 109 of 126, 123 of 127 and 55 of 57 shared; totals 190 / 283 / 122 shared.

**Placebo: not applicable.** This is a removal. Each of the seven failed its own 50-draw placebo in input_ablation.

**Snooping: minor.** There was one variant. The seven were picked by input_ablation's written fail rule, which scored
all three windows. The report's "not on 2023-25" overstates this: the held-out window did feed the choice, but through a
fixed rule, not by picking a winner. The pre-registration and the results sit in the same WIP commit, so the order is
unproven. The rule was Matt's own one-line condition.

**Other facts Matt should know (not part of his condition).**
- Under the strict round-3 rule the drop still fails part 2 on the 2019-22 spread flag (one net win) and part 1 on the
  2019-22 total miss (+0.0003).
- Calibration is also slightly worse on 2019-22 (calibrated Brier 0.2173 -> 0.2174). The calibration error is worse on
  2015-18 and 2019-22 (0.0350 -> 0.0364, 0.0267 -> 0.0310) and better on 2023-25 (0.0610 -> 0.0488).
- The report names the first two but leaves the 2019-22 calibration out of its fail summary.
- All of these moves are noise-sized.

## What would change the verdict
- A trees refit on GitHub's runners that leaves the margin miss worse by more than 0.0005 on any window. Unlikely: the
  observed rerun spread is 0.0012 against a 0.0035+ gap. Check the first weekly run's backtest.
- Something on the page or in the season sims that reads neutral, div_game, qb_out or dome as model inputs and that
  `tie_check --page` catches. Not run here.
- Fixes needed in reports/drop_seven_inputs.md:
  1. Replace "reproduces input_ablation's baseline exactly" with the real difference.
  2. Note that shadowqtotals also lost pf_sum.
  3. Add the 2019-22 calibration to the fail summary.
