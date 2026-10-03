# Drop the seven failing inputs: margin check first (pre-registered 3 Oct 2026, before any result)

## Claim
Matt (3 Oct 2026) approved removing the seven inputs `input_ablation` found to fail with no meaningful cost: points
equations (`model.FEATS`) neutral, dome, rain, div_game, qb_out; totals equation (`model.TOTAL_FEATS`) pf_sum (both
offenses' points ratings), qb_out_sum. His condition: first measure the margin (spread) miss, which the combined run
(`reports/input_ablation_combined.md`) did not report.

## Variant
One: V1 the seven dropped together, against the live model. No other variant.

## Data and timing
Main at 0788403f (weekly run of 3 Oct 2026), its data. Both runs `model.walk_forward` 2015-2025 (weekly refit, trees
refit where their inputs change, `data/processed/trees_cache.parquet` read only, never written). Weather priced on the
forecast (`model.priced_weather`), injuries as of the run; no line, split or price is an input (lines grade only).
Kept as they are: the readings themselves (qb_out still feeds cards, checks and the QB-out swap; dome and RAIN_FC stay
in the totals equation; wind everywhere).

## Measured per window (2015-18, 2019-22, 2023-25; regular season)
Margin miss (|model spread - result|), team points miss, total miss; Brier score of the raw home win chance (`p_home`)
and of the calibrated one the page shows (`picks.home_calibrations`, seasons with a fit in force), with the calibration
error (10 equal-count bins, mean |said - happened|); the spread flag (|edge| 4+), the totals flag (55%+ raw under
chance) and the wind under (10+ mph forecast), weeks 1-17, closing line, -110. Study gate on margin, team and total miss.

## Decision rule (Matt's, fixed before results)
If the margin miss without the seven is not worse on any window (a worse value counts as a tie only within 0.0005),
implement the drop in the live model. If it is worse on any window by more than 0.0005, do not implement; report.
No placebo is run: the seven were each scored with 50 placebo draws in input_ablation; this is the combined check
Matt asked for.

---

# Results

Script `experiments/drop_seven_inputs.py` (run 3 Oct 2026 on main 0788403f); full rows in `reports/drop_seven_inputs.csv`,
gate tables in `reports/drop_seven_inputs_results.md`. The live run matches input_ablation's baseline on every miss to
0.0001 and on every record (its trees differ on 1,314 games: the live run read the stored fits, input_ablation fit fresh).

| Window | Margin miss | Team points miss | Total miss | Brier, raw win chance | Brier, calibrated | Calibration error | Spread flag | Totals flag | Wind under |
|---|---|---|---|---|---|---|---|---|---|
| 2015-18 | 9.9471 -> 9.9429 | 7.3993 -> 7.3889 | 10.7484 -> 10.7238 | 0.2158 -> 0.2155 | 0.2153 -> 0.2150 | 0.035 -> 0.036 | 68-58 -> 66-53 | 132-111 -> 142-117 | 119-97 -> 119-97 |
| 2019-22 | 10.0116 -> 10.0040 | 7.3740 -> 7.3681 | 10.5340 -> 10.5343 | 0.2184 -> 0.2185 | 0.2173 -> 0.2174 | 0.027 -> 0.031 | 78-49 -> 81-53 | 175-140 -> 183-134 | 143-88 -> 143-88 |
| 2023-25 | 9.9069 -> 9.8997 | 7.2357 -> 7.2285 | 10.1040 -> 10.1037 | 0.2163 -> 0.2161 | 0.2155 -> 0.2152 | 0.061 -> 0.049 | 37-19 -> 38-17 | 76-55 -> 86-61 | 77-52 -> 77-52 |

(live -> without the seven; calibrated chance on 1,020 / 1,050 / 815 games, the seasons with a home calibration in force.)

**Margin rule: met.** The margin miss is lower without the seven on every window (by 0.004, 0.008 and 0.007), so per
Matt's condition the drop is implemented. The rest: team points miss better on every window; total miss better on
2015-18 and 2023-25 and 0.0003 worse on 2019-22; the win chance's Brier score 0.0002-0.0003 better on 2015-18 and 2023-25 and
0.0001-0.0002 worse on 2019-22 (calibration error better on 2023-25, worse by 0.001 and 0.004 on the others); the spread flag +3 / -1 / +3 net wins (the 2019-22 net win the ablation flagged); the
totals flag +4 / +14 / +4 net wins; the wind under unchanged. As a study-gate result the drop still fails part 2 (that
one spread-flag net win on 2019-22) and, on total miss, part 1 on 2019-22, as in input_ablation; Matt approved it
knowing that, on the condition checked here. Every move is inside one standard error (audit of input_ablation).

**Run to run.** The boosted trees for the reduced input set are not in the stored cache, so they were fit fresh. The
same drop in input_ablation's run (`reports/input_ablation_combined.md`) gave the spread flag 67-54 on 2015-18 and team
miss 7.3891: only the trees differ (1,016 games, up to 1.0 point on a team, 0.21 on the spread; the ridge members and
the total identical). That run's margin miss was also lower on every window (9.9467 -> 9.9432, 10.0118 -> 10.0037,
9.9072 -> 9.9009, against its own fresh-fit baseline). The first weekly run on GitHub refits these trees again, so the
published backtest records may differ from the table above by a bet or so.

**What changed in the live model.** `model.FEATS` 22 -> 17 inputs (neutral, dome, rain, div_game, qb_out out);
`model.TOTAL_FEATS` 11 -> 9 (pf_sum, qb_out_sum out). The readings stay computed: dome feeds the totals equation and
the cards, the forecast rain (`RAIN_FC`) the totals equation, qb_out the cards' "starting QB out" chip, the injury
report and the standing check `qb_out_is_last_starter` (a data check, still meaningful), neutral and div_game the
cards and the season sims. The hidden shadow `shadowqtotals` inherits the live equation (so it loses pf_sum too) but keeps
its own QB term (`qb_out_t_sum`), so it still tests the idea it was registered with. The props backtest constants (`props_by_season`) will drift after the weekly run
because the game model's spreads and totals moved.

## Audit
model-auditor (reports/audit_drop_seven_inputs_2026-10-03.md): **"holds with caveats."** Matt's margin condition is met on every
window, also with the trees refit (they move the margin miss by at most 0.0012 against a smallest gap of 0.0035); the new
pred_v3 from the changed live code equals the tested run on all 3,028 games; leak test 0.0; no market input; every gain
inside one standard error. Its three wording fixes are made above.

## Decision
Implemented (Matt's yes of 3 Oct 2026, margin condition met).

## Count
One variant (V1), one run of each model; the seven were chosen by input_ablation (47 drop-one variants, 2,350 placebo
draws, one earlier combined run), not on 2023-25.
