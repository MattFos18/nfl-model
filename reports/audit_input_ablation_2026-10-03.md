# Audit: input_ablation (model-auditor, 3 Oct 2026)

**Verdict: holds with caveats.** The numbers are right, and "drop nothing, give the set of seven to Matt" follows the
pre-registered rule. Three things are off: C4's "fails" is an artifact of a broken placebo; the blend, share-out and
calibration placebos are too weak to judge anything; and every gain or cost in the drop decision is inside the noise.

What I checked: worktree `agent-a7d72c2c3745b3b03` (branch input-ablation, origin/main c1e38081). I used the saved runs in
`%TEMP%/input_ablation`. I did not rerun the whole script (it takes hours). `git diff origin/main -- nflmodel/` is empty,
so the study changes no live code.

## Checks

**1. Look-ahead: pass.** The study adds no inputs. It only removes or shuffles inputs the live model already has, and
`nflmodel/` is unchanged from main. Weather is still priced on the forecast (`model.priced_weather`), and training rows
still use the recorded weather, as live. Placebo shuffles stay within a season and only move pre-game values between games.
I ran `audit.leakage_test()` directly, inside `trees_cache_read_only` (save also stubbed). I did not use
`python -m nflmodel.audit`, because its main block rewrites `reports/audit.md`. Results: 276 rating rows, largest rating
change after corrupting future data 0.0, largest prediction change after corrupting targets 0.0, after corrupting the
game's own score 0.0. `data/processed/trees_cache.parquet` was not touched (mtime 01:05, before the study).

**2. Market inputs: pass.** `FEATS` and `TOTAL_FEATS` contain no line, split or price. `spread_line` and `total_line` are
used only to grade bets and to price `p_over_emp` at the line, the same as the live flag rule. No filter or weight reads
the market.

**3. Every window: pass (the numbers recheck exactly).** I recomputed every P and T gain and placebo count from
`var_*.parquet` and `plac/*.json`. All 33 pieces match `reports/input_ablation.csv` with no mismatches.

- The baseline matches the published `data/processed/pred_v3.parquet` exactly on every record (spread flag 68-58 / 78-49 /
  37-19, totals flag 132-111 / 175-140 / 76-55, wind under 119-97 / 143-88 / 77-52). Team miss is within 0.0001.
- The combined run rechecks: team miss 7.3891 / 7.3681 / 7.2288, total miss 10.7238 / 10.5343 / 10.1037, spread flag
  67-54 / 81-53 / 38-17, totals flag 142-117 / 183-134 / 86-61.
- Each P variant leaves `model_total` exactly the same as the baseline, and each T variant leaves `model_spread` exactly
  the same. So the base rerun at 01:50, after the variants, is consistent with them, and `base_mt.parquet` equals
  `base.parquet` to 0.0.
- The trees really are refit when an input is dropped. P10's trees differ from the baseline's by up to 2.6 points: the
  cache key includes `FEATS`, so a stale read is impossible.
- Sign convention, `verdict()` and `drop_costs_wins()` are correct:
  - gain = miss without minus miss with, so positive means the piece helps;
  - the gate is called with base = without and new = with;
  - "fails" means 2 or more windows lost, or 1 window lost plus 2 or more placebo windows lost, as pre-registered;
  - a cost is counted when the net wins without the piece are below the live record's.
- P7's "fails" turns on gains of +0.0000032 and +0.0000026 on 2019-22 and 2023-25 (counted as better) and -0.0001 on
  2015-18. It is effectively zero everywhere.

**4. Placebo: pass for P, T and W1; fail for B, S1 and C.**

- **Fast refits are faithful.** I spot-checked three draws myself: P14 draw 0 (team-level shuffle), P13 draw 3 (game-level
  shuffle) and T6 draw 7 (totals). Each `fast_points` / `fast_totals` rerun reproduces its stored json to 0.0. A full
  `model.walk_forward` with the same shuffle (monkeypatched `prep`, `priced_weather`, `_game_frame`) on 2015-16 (534 games)
  equals the fast refit to 0.0 on `model_spread`, `home_m_trees`, `home_m_ridge`, `model_total` and `p_over_emp`. The
  shuffles really move the model: mean absolute change 0.28 / 0.12 points on the spread and 0.59 on the total.
- **The `col__sh` / `col__tot` method is sound.** Points shuffles leave `home` structure and the totals equation alone.
  Totals shuffles rebuild the sums from the donor game's two rows. Training rows get the donor's recorded value, priced
  rows the donor's priced value.
- **Blend members (B1-B7): too weak to mean anything.** Shuffled member predictions add noise to the average. The median
  placebo gain is -0.007 to -0.030, against real gains of about ±0.004 (ridge, plays and trees, 10 draws each). So every
  member "beats" its placebo even when its real gain is negative (B1: -0.0006 on 2015-18, beats 50 of 50).
- **S1 (share-out): same problem.** The shuffled shift has an sd of 1.09 points: noise, not a fair null.
- **C4 (teaser spread leg): broken.** Its calibrated-minus-raw logit has a within-season sd of 0.0. It is a constant
  shift each season, so the shuffle returns identical values, and the placebo counts 4 / 0 / 31 are floating-point noise.
  C4's "fails" verdict comes only from these placebo rows (it loses one window, -0.0004 on 2016-18). With a working
  placebo it would be **thin**, not fails.
- C1, C2, C3 and C5 have real within-season spread (sd 0.16-0.22), so their placebo counts mean something. But a
  calibration's season-level shift survives the shuffle, so their placebo is lenient toward failing and harsh toward
  passing.

**5. Snooping: pass with caveats.**

- **Count.** The script and the pre-registration list the same 47 pieces (22 + 11 + 7 + 1 + 1 + 5). "48" is an arithmetic
  slip. No piece appears in the script that is not in the pre-registration.
- **Timing could not be proven.** `reports/input_ablation.md` is untracked, and the results were appended below a
  "Results" separator (mtime 07:15, after the 07:06 results). Lines 1-63 read as a pre-registration, but there is no
  timestamp or commit before the results to prove it.
- **The combined run came before two verdicts were known.** It ran at 03:01. The last draws for P7 and P11 were written
  at 04:06 and 05:01, and those two pieces count as "fails" only through their placebo rows. So the set was named before
  the rule could fully select it. It turned out to equal the rule's output, and only one combined run exists, so the
  outcome is unchanged. Still, the order was not as pre-registered.
- **Wording.** The S1/C4 "display piece" reason is stated as post-hoc. The pre-registered reason gives the same result:
  part (c) needs the combined drop to pass, it failed, so nothing is dropped. Adding S1 would not fix the spread-flag
  cost, because S1 moves no bet.
- **Report table.** The results table in `input_ablation.md` marks "bet cost" on some thin pieces but not on P3, P15 and
  P18. By the report's own definition, those three also have one (for example P15 2015-18: 69-58 without vs 68-58 with).
  Cosmetic; no verdict changes.

**6. Sample size: fail as evidence; the decision is driven by noise.**

- **Bets per window.** Spread flag: 126 / 127 / 56 bets (SE about 4.5 / 4.4 / 6.7 points on the win rate). Totals flag:
  243 / 315 / 131 (SE 3.2 / 2.8 / 4.4).
- **The combined drop's moves are all inside one SE.** The blocking cost is spread flag 2019-22 61.4% -> 60.4% (one net
  win). The gains are totals flag 54.3 -> 54.8 / 55.6 -> 57.7 / 58.0 -> 58.5%.
- **Misses.** The combined team-miss gains of 0.006-0.010 sit at the paired-bootstrap noise floor of about ±0.006-0.007
  (`reports/audit.md`, section 5). The 0.0003 total-miss loss is negligible.
- **Single pieces.** The seven pieces' single-drop gains are mostly under 0.004 on team miss, well inside that floor.
  T3 (+0.024 on 2023-25) and T6 (±0.011-0.022) on total miss are the largest.
- **What "fails" means here.** It means "no detectable value", not "proven harmful". Equally, the one spread win that
  blocks the drop is not a real cost.

**7. Leak test: pass.** The study does not touch features or the walk-forward. I ran the leak test anyway, as described
in check 1: all three numbers 0.0, with the trees cache read-only.

## What would change the verdict
- **To "does not hold":** a P or T draw that does not match a full `walk_forward`. Three of 2,350 checked; a fuller sweep
  could find one, though the fast refits share `walk_forward`'s loop line for line. Or evidence that the pre-registration
  text was changed after the results.
- **To "holds":**
  - a fixed C4 verdict (thin; drop its placebo row, or use a placebo that can vary, such as shuffling across seasons);
  - the blend, share-out and calibration placebo rows marked "not informative" in the report;
  - a note that the combined run preceded the P7/P11 placebo results.
- **For Matt's call on the seven:** more seasons. At today's sample neither dropping nor keeping them is distinguishable
  from noise. The 2026 season is the next real test.

Side effect of this audit: running the model code made `nflmodel/warnlog.py` append a wind_live warning to
`data/weather/warnings.json`. That file was already modified before the audit; it is regenerated data and is not to be
committed.
