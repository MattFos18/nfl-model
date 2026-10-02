# Audit: overs_deep (2 Oct 2026)

**Verdict: holds with caveats.** The numbers reproduce exactly, there is no look-ahead, and "no over bet, no model change" stands. But O9 is not evidence of a real edge: it is inside the noise on every window, the model's chance adds nothing over blind low-total overs on 2015-18, and the snooping count leaves out the 100 earlier over rules that already pointed at low totals. A hidden shadow (tracked, never bet) is the right place for it, and nothing stronger.

Scope: `experiments/overs_deep.py`, `reports/overs_deep.md`, `reports/overs_deep_results.md`, `reports/overs_deep.csv`, the `shadowoverlow` diff in `nflmodel/picks.py`, `tests/test_overs_deep.py`. Extra checks were run from scratch scripts outside the repo. No repo file was edited by this audit. (`data/processed/trees_cache.parquet`, `web/data/*`, `reports/tie_check.md` and others changed in the worktree during the audit. Their timestamps fall outside my runs, so another session changed them.)

## Checks

### 1. Look-ahead: pass
- `p_over_emp`: `model.walk_forward` trains on `season < s`, or the same season with `week < wk` (model.py 440-443). It is priced by `price_at` from that fit's training misses (`tres`). Played games from 2018 on are priced on the stored forecast (#389).
- Leak test, run as `audit.leakage_test()` with the trees cache write disabled so no file was written: rating change 0.0, prediction change after corrupting later targets 0.0, prediction change after corrupting the game's own score 0.0.
- `p_over_cal`: `picks.over_calibration` fits on `season < season` (picks.py 583). 2015 is the identity, because `OVER_CAL_FROM` is 2015 and `OVER_CAL_MIN_N` is 200.
- `qb_form`: weeks before the game, this season only (model.py 311, `v[0] < w`).
- Pace: `off_plays` from `features_asof`. The O14 cut is the median of earlier seasons only.
- Wind and rain: stored pre-kickoff forecasts (`wind_live.readings`, `rain_readings`).
- M1 and M2 are fit on `season < s` walk-forward misses only.
- None of the inputs reads results.

### 2. Market inputs: pass, with one note
- No line, split or price enters the model. M1 and M2 learn only from model totals and actual results.
- The closing total does enter O9 as a filter on the bet (line 41 or lower). That is the same kind of condition as `shadowdog`, `shadowsmalldog` and `shadowteasedog`, so it is acceptable for a shadow.
- If O9 is ever proposed as a real bet, Matt has to decide explicitly whether a line filter counts as a market input under round-3 part 4.
- Backtest and live do not read the same line:
  - The backtest conditions and grades on the closing total.
  - Live reads the run-time consensus (`LN.live_lines`) and re-prices `p_over_emp` there (`M.price_at` with the same fit, picks.py 420-436). The tracker then grades at that logged line.
  - A game that sits at 41.5 at bet time and closes at 41 is in the backtest set but not in the live one. Live records will not exactly match the backtest's basis.

### 3. Every window: pass on records (the claim reproduces), fail on strength
- Rerun with the cached base predictions and outputs sent to the scratchpad. `overs_deep_results.md` and `overs_deep.csv` came out byte-identical to the repo copies.
- O9: 42-35 / 29-25 / 56-37 (+3.2u / +1.4u / +13.9u).
- `picks.rule_records` gives the same 42-35 / 29-25 / 56-37. The shadow's mask equals O9's mask game for game (225 games each).
- 2019-22 makes +1.4u on 54 bets, and 13.9u of the 18.5u come from 2023-25.
- 2015-22 pooled: 71-60 (54.2%).
- The cut is fragile:
  - Of the 12 neighbour cuts in the results file, only 3 are positive on all three windows: line 40 at 55%, line 41 at 55%, line 41 at 57%.
  - Line 40 at 53% and at 57%, line 41 at 53%, and line 42 at every cut all lose 2019-22.
- No bet cost to the live rules: O9 never shares a game with the totals flag (opposite sides by construction).

### 4. Placebo: fail on a per-window reading
- The study's 200 of 200 is pooled 2015-25, and it shuffles the rule's games across all games. That only shows O9 beats random overs, which lose about 48-50% blind (D1).
- The study's stricter placebo (chance shuffled among line-41-or-lower games), 193 of 200, is also pooled.
- I reran the stricter placebo per window, 500 draws, gain above the 90th percentile:

| Window | Strict placebo (low-total games only) | Study's mask placebo |
|---|---|---|
| 2015-18 | 297 of 500 (real +3.2u, 90th percentile +8.9u) | 445 of 500 |
| 2019-22 | 448 of 500 (real +1.4u, 90th percentile +1.4u) | 414 of 500 |
| 2023-25 | 486 of 500 | 491 of 500 |

- At round-3 strength (90th percentile on every window), O9 fails 2015-18 and 2019-22 on both placebos.
- On 2015-18, blind overs at 41 or lower went 91-80 (53.2%) and the low-total games the model did not pick went 49-45. The chance added nothing there.
- The pass bar the study registered was pooled, so the study did meet its own bar. Its strength is overstated, not misreported.

### 5. Snooping: fail (understated)
- In this study: 14 rules, plus 12 neighbour cuts and a strict placebo added after results. The pass bar and the O9 cut are written in the pre-registration. I could not check that it predates the results: the files are untracked and the .md was last saved after the results.
- `reports/totals_sides.md` (29 Sep) was left out of the count:
  - It says "Over rules tried: 100; winning all three windows: 1".
  - That one winner was "over, chance 60%+, line under 43" (31-25 / 18-16 / 33-27).
  - The same file notes "Over calls on low lines are fine (line under 40: 50-40; 40-43: 74-68)".
  - `reports/postmortem.md` already used a "total line under 41" cut.
- So the low-total over was a pattern already seen on these same games, not a fresh hypothesis.
- The adjusted luck chance of "about 0.1" counts about 30 earlier variants. With about 130 earlier over rules it is well above 0.1, probably 0.3 or more on a rough Bonferroni scaling of the 3.3% family-wise figure. The rules overlap, so the true figure is lower than a full Bonferroni, but not 0.1.
- The family-wise test itself is sound: outcomes are permuted within season, the best of the 14 is taken each draw, 1,000 draws, and the 3.3% has a standard error of about 0.6 points.

### 6. Sample size: fail (inside the noise)
- Bets per window are 77 / 54 / 93, so the standard error on the win rate is 5.7 / 6.8 / 5.2 points.
- Win rates are 54.5% / 53.7% / 60.2% against 52.4% break-even: z of 0.38 / 0.19 / 1.51.
- Pooled: 127-97, 56.7%, standard error 3.3 points, z 1.29 against break-even.
- No single window is clear of break-even. Low-total games were rare in 2020-21: 11 and 19 games, giving 2 and 7 O9 bets.

### 7. Leak test: pass
- The change touches only `picks.py` (a hidden rule). The audit was run anyway as `leakage_test()` with `save_trees_cache` disabled, not `python -m nflmodel.audit`, which would rewrite `reports/audit.md`.
- All three prediction or rating changes were 0.0.

### Other claims
- **Claim 2 (M1, M2): holds.** Both are worse on total miss on 2019-22 and 2023-25 (10.5161 -> 10.5813 / 10.5503; 10.1029 -> 10.1167 / 10.1215), and their placebos are beaten 0-8 of 50 there. The rerun is identical.
- **Claim 3 (diagnosis): holds, as description.**
  - Blind overs went 48.6% / 47.5% / 50.5%, with skew +0.26 / +0.35 / +0.38.
  - The raw chance at 62%+ came in at 48.1% / 52.8% / 53.4% (z -2.66 / -1.49 / -1.79).
  - The calibrated chance's bands are all within |z| 1.82. It reads 53%+ on 19 games in 2019-22 and 42 in 2023-25.
  - One caution: in 2023-25 the median game landed 0.5 over and the mean 1.2 over. There, overs lost to the vig, not to the skew.
- **Wind-under conflict.** 15 O9 games were also live wind-under bets (by window 1-0, 2-5, 2-5 for the over). Live, the hidden shadow will log an Over on games where Matt bets the Under. That costs no money while it is hidden. Excluding those games (122-87) would be a rule chosen after looking, and should not be used to argue for O9.
- **Implementation.** The mask, its >= / <= edges, weeks 1-17, the requirement for a line, over grading (`OVER_RULES` in `record` and the bet text), the hidden flag, and the shadow watch's comparison with the totals flag all match O9 (tests/test_overs_deep.py; mask identical on 225 games).

## What would change the verdict
- **Toward "does not hold":** live records drifting under break-even, or treating O9 as a bet candidate on the current evidence. It fails a per-window placebo and the snooping count is too low.
- **Toward "holds":** a clean live sample, say 100+ settled O9 bets at the bet-time line, clearing break-even. The pass should come from the chance beating blind low-total overs on the same games, not from low totals going over in general.
- **For the report:** state the per-window strict placebo (297 / 448 / 486 of 500) and add totals_sides' 100 over rules to the snooping count.
