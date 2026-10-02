# Calibration recheck on the honest backtest (2 Oct 2026)

## Pre-registration (written before any result)

**Claim.** The calibrated chances the site shows were fit on backtest rows that had leaks (#381, #384, #387) and priced
played games on the weather that happened (#389). On main's predictions rerun walk-forward 2015-2025 with every fix in,
each calibration should still be better than its raw chance on every window. Asked by the session lead after the leak
fixes; a calibration that now loses to raw on any window gets a correctness fix (refit or the identity), pre-approved by
Matt for fixes that clearly win.

**What is checked (no variants of a rule; each item is one fixed check).**
- C1 cover calibration (`picks.calibration`, the cards' cover odds and the Kelly stake): the model side's chance,
  logistic on |edge| capped at 7, fit on regular-season games from `CAL_FROM` (2019) to the season before; raw = the
  bell-curve `p_cover_home` for the model's side.
- C2 over calibration (`picks.over_calibration`, `p_over_cal`): raw = `p_over_emp`.
- C3 home win calibration (`picks.home_calibration`, `p_home_cal`): raw = `p_home`.
- C4 teaser legs (`picks.tease_calibration`), spread legs (C4s, a shift) and total legs (C4t, intercept and slope):
  raw = the bell curve's 6-point teased chance.
- Each season is scored with the fit that would have been in force for it (fit on earlier seasons of the same rerun
  table only), exactly as the code does it, the identity (or C1's flat 50%) where the code has too few games.
- S spread flag cutoffs: the record at |edge| >= 3, 3.5, 4, 4.5, 5, weeks 1-17, against the closing line. Report only:
  `SPREAD_EDGE` is not changed whatever this shows (a cutoff picked by looking is snooping; `shadowhalf` /
  4.5 is already tracked).

**Data and timing.** `model.walk_forward` on `features_asof` with trends, 2015-2025, weekly refit, priced weather on the
stored forecast (`model.priced_weather`), trees read from the stored cache and never written. Lines and results from
`games.parquet` (closing line) are used only to grade and to fit the calibrations, never as model inputs.

**Windows.** 2016-18 (the first season with an earlier-season fit is 2016; 2017 for C3, whose identity runs under 500
games), 2019-22, 2023-25, regular season. For C1 the code has no fit before 2020 (`CAL_FROM` 2019), so 2016-19 carry the
flat 50% the code would show; also reported, for the record only, the same form fit from 2015.

**Pass bar (per calibration).** Calibrated log loss and Brier both lower than raw on every window (study gate: miss =
log loss, calibration = Brier). Reliability by band (z per band) reported. A calibration that fails any window: fix to
whichever of (a) the identity / raw chance or (b) a refit form already in the code family wins every window; if
neither wins every window, the identity (the raw chance) is the safe default and is reported to Matt.

**Not applicable.** A within-season placebo: a calibration is a monotone mapping of one model chance fit on earlier
seasons, not a new input; it adds no information to the model and cannot be shuffled meaningfully. No bet record
moves: C2 and C3 are monotone and the flags read the raw chance; C1 only sizes the stake.

## Results (rerun of 2 Oct 2026, `python -m experiments.calibration_recheck`)

Rerun table: 3,028 games 2015-2025 (main at cdaa0ca3, every leak fix and the forecast-priced weather in). Full tables,
gates and reliability by band: `reports/calibration_recheck_results.md`; every number: `reports/calibration_recheck.csv`.

| Calibration | 2016-18 log loss raw -> cal | 2019-22 | 2023-25 | Brier better on all three | Verdict |
|---|---|---|---|---|---|
| C1 cover (cards' cover odds, Kelly stake) | 0.7067 -> 0.6932 | 0.7002 -> 0.6946 | 0.6986 -> 0.6929 | yes | holds |
| C2 over (`p_over_cal`) | 0.7065 -> 0.6951 | 0.6913 -> 0.6900 | 0.6902 -> 0.6900 | yes | holds |
| C3 home win (`p_home_cal`; 2017-18 scored) | 0.6069 -> 0.6044 | 0.6260 -> 0.6244 | 0.6218 -> 0.6205 | yes | holds |
| C4s teaser spread leg (shift) | 0.6036 -> **0.6041** | 0.6125 -> 0.6113 | 0.6009 -> 0.6001 | no (2016-18 0.2058 -> 0.2060) | loses on 2016-18 |
| C4t teaser total leg (intercept and slope) | 0.6470 -> 0.6349 | 0.6257 -> 0.6212 | 0.5901 -> **0.5914** | no (2023-25 0.2001 -> 0.2007) | loses on 2023-25 |

Study gate (log loss as the miss, Brier as calibration; the gate's 2015-18 is 2016-18 here): C1, C2, C3 PASS 6 of 6;
C4s and C4t FAIL 4 of 6. Tables in `reports/calibration_recheck_results.md`.

**Reliability.** C1 is flat and conservative as before: 2016-19 carry the flat 50% the code shows (`CAL_FROM` 2019, no
fit before 2020); 4-5 point edges said 55% and covered 67% (2019-22, n 63, z +1.8), said 54% and covered 62% (2023-25,
n 39); no calibrated band past |z| 2. The raw bell curve stays hot at nearly every edge (3-4 points 2019-22: said 61%,
covered 47%, z -3.3). C2 calibrated is within |z| 1.4 in every band of every window (raw 2016-18: said 54%, came 46%,
z -2.9). C3 calibrated keeps the known 2023-25 pair: said 45%, won 35% (n 148, z -2.6) and said 65%, won 75% (n 144,
z +2.5), each under the health check's 150-game floor; raw shows the same pair (z -2.8, +2.0). C4t calibrated
undershoots 2023-25 (said 68.5%, hit 72.2%, n 709, z +2.1); raw says 73% every window and hit 67%, 69% and 73%.

**Fix candidates for the teaser legs (pre-registered (b), one each).** The other form in the code family, refit the same
way: spread legs with intercept and slope 0.6036 -> 0.6009 / 0.6125 -> 0.6065 / 0.6009 -> **0.6033** (loses 2023-25);
total legs as a shift 0.6470 -> 0.6402 / 0.6257 -> 0.6214 / 0.5901 -> **0.5931** (loses 2023-25). Neither wins every
window. The identity (the raw chance) is worse than today's calibration on two windows of three for each kind and on
2016-25 pooled (log loss: spread legs 0.6063 raw against 0.6058 calibrated; total legs 0.6209 against 0.6160).

**Spread flag by cut (report only, `SPREAD_EDGE` unchanged).** Weeks 1-17, closing line, -110:

| Cut | 2015-18 | 2019-22 | 2023-25 |
|---|---|---|---|
| 3 | 119-115 (50.8%, -7.5u) | 132-113 (53.9%, +7.7u) | 80-57 (58.4%, +17.3u) |
| 3.5 | 88-80 (52.4%, +0.0u) | 107-81 (56.9%, +17.9u) | 53-34 (60.9%, +15.6u) |
| 4 (live) | 69-55 (55.6%, +8.5u) | 77-48 (61.6%, +24.2u) | 37-20 (64.9%, +15.0u) |
| 4.5 (shadow) | 42-37 (53.2%, +1.3u) | 53-38 (58.2%, +11.2u) | 24-15 (61.5%, +7.5u) |
| 5 | 29-22 (56.9%, +4.8u) | 36-28 (56.2%, +5.2u) | 13-5 (72.2%, +7.5u) |

4 has the most units on 2015-18 and 2019-22 and the best rate of 3 to 4.5 on every window; on 2023-25 the looser 3 and
3.5 (+17.3, +15.6 units) edge it (+15.0). 4.5 trails 4 on every window. The cut was chosen on 2019-22 (decision log
23 Sep 2026), so this is a description, not a test; the 4.5 shadow keeps grading live.

**Variants counted.** Five calibrations checked as coded (no choice); one record-only C1 refit from 2015; one fix
candidate per teaser leg kind. Nothing picked on 2023-25.

## Decision

- C1, C2, C3: still better than raw on every window of the honest backtest. No change.
- Teaser legs (C4s, C4t): each loses to the raw chance on one window, by 0.0005 (spreads, 2016-18) and 0.0013 (totals,
  2023-25) log loss. The pre-registration named the identity as the default when no candidate wins every window, but
  the identity is worse than today's calibration on the other two windows and pooled, so it is not a fix that clearly
  wins and falls outside Matt's pre-approval. **Left as is; Matt to decide.** Recommendation: keep today's teaser
  calibration (better than raw on two windows of three for each kind and on 2016-25 pooled; each shortfall smaller than
  its gains) and recheck it after the 2026 season.
- Spread cut: no change (report only).

## Audit

model-auditor (`reports/audit_calibration_recheck_2026-10-02.md`): **holds with caveats.** A full rerun reproduces the
csv and results byte for byte; an independent re-score with picks.py's functions matches to 5 decimals; wiping later
seasons leaves every fit unchanged (no look-ahead in the calibrations). Caveats it raised, added here after results:
- Most of the calibrations' wins after 2018 are inside the noise (C2 2023-25 and C3 small), and so are both teaser
  shortfalls; the teaser decision (no switch to the identity without Matt) is sound.
- C1's 2016-18 pass is the flat 50% the code shows before 2020, not a fitted curve.
- 2015-17 are still priced on the weather that happened (no stored forecast before 2018), so the 2016-17 raw chances and
  every fit that includes 2015-17 rows carry that look-ahead.
- The trees were not all read from the cache: 168 of 404 tree fits were refit in this run (none written to
  `data/processed/trees_cache.parquet`), against the pre-registration's "trees read from the stored cache".
