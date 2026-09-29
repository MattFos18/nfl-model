# Season simulation: in-season update weight and injuries carried forward (29 Sep 2026)

Harness: experiments/season_update.py, a copy of experiments/season_backtest.py. As of weeks 1, 5, 9, 13 and 17 of every
season 2019 to 2025, the games before the week are real, the week being priced comes from the prediction table, later
games from the model's equation on the as-of ratings; 5000 runs per simulation, the same seed per (season, week) across
variants. Metrics: wins_mae (mean absolute error of expected wins), div_brier, po_brier, sb_ll (log loss of the champion).
Windows 2019-22 and 2023-25, means over the as-of weeks.

## Adoption rule (written before the results)

A variant is adopted only if wins_mae, div_brier and po_brier all improve (strictly lower) on both windows, 2019-22 and
2023-25, versus base (the current simulation: as-of ratings unchanged, absence inputs zero for future games), averaged
over the five as-of weeks. sb_ll is reported, not decisive. If several variants pass, the one with the lowest mean
wins_mae over both windows is the one to integrate; a part's k or d family that passes at one value only is adopted
at that value, not extended.

## Variants

Part 1, update weight, on future games' profiles only (rating inputs off_epa_play, own_def_epa_play, off_pf, own_def_pf,
qb_rating; continuity and record untouched), n = the team's games played this season:
- shrink_k{2,4,8}: r' = mean + (r - mean) * n / (n + k), mean = the league mean of that input as of the week.
- sharp_k{1,2}: r' = mean + (r - mean) * min(1.5, (n + k) / n).
At week 1 n = 0, so shrinking sets every rating to the league mean and sharpening sits at the 1.5 cap.

Part 2, absences carried forward: each team's skill_out_value, qb_out, off_snap_out and def_snap_out as of the week
(its week-w row of the model's frame; a bye team's last game before the week) applied to its future games at d ** (weeks
ahead), d in {0.5, 0.75}; opp_skill_out_value and opp_def_snap_out from the opponent's own values; the bracket decays
the same way.

## Results (means over the as-of weeks; delta = variant minus base, lower is better)

| variant | window | wins_mae | div_brier | po_brier | sb_ll | d wins_mae | d div_brier | d po_brier | d sb_ll |
|---|---|---|---|---|---|---|---|---|---|
| base | 2019-22 | 1.3567 | 0.0844 | 0.1218 | 2.4863 | | | | |
| base | 2023-25 | 1.5789 | 0.1376 | 0.1472 | 2.8541 | | | | |
| shrink_k2 | 2019-22 | 1.4341 | 0.0905 | 0.1244 | 2.6266 | +0.0774 | +0.0061 | +0.0026 | +0.1403 |
| shrink_k2 | 2023-25 | 1.6084 | 0.1360 | 0.1432 | 2.8243 | +0.0295 | -0.0016 | -0.0040 | -0.0298 |
| shrink_k4 | 2019-22 | 1.4457 | 0.0912 | 0.1244 | 2.6467 | +0.0890 | +0.0068 | +0.0026 | +0.1604 |
| shrink_k4 | 2023-25 | 1.6130 | 0.1359 | 0.1423 | 2.8206 | +0.0341 | -0.0017 | -0.0049 | -0.0335 |
| shrink_k8 | 2019-22 | 1.4641 | 0.0923 | 0.1248 | 2.6803 | +0.1074 | +0.0079 | +0.0030 | +0.1940 |
| shrink_k8 | 2023-25 | 1.6245 | 0.1359 | 0.1413 | 2.8427 | +0.0456 | -0.0017 | -0.0059 | -0.0114 |
| sharp_k1 | 2019-22 | 1.3475 | 0.0852 | 0.1251 | 2.4927 | -0.0092 | +0.0008 | +0.0033 | +0.0064 |
| sharp_k1 | 2023-25 | 1.5990 | 0.1403 | 0.1516 | 2.9815 | +0.0201 | +0.0027 | +0.0044 | +0.1274 |
| sharp_k2 | 2019-22 | 1.3464 | 0.0855 | 0.1261 | 2.5026 | -0.0103 | +0.0011 | +0.0043 | +0.0163 |
| sharp_k2 | 2023-25 | 1.6025 | 0.1410 | 0.1531 | 3.0349 | +0.0236 | +0.0034 | +0.0059 | +0.1808 |
| inj_d0.5 | 2019-22 | 1.3547 | 0.0839 | 0.1213 | 2.4833 | -0.0021 | -0.0005 | -0.0005 | -0.0030 |
| inj_d0.5 | 2023-25 | 1.5780 | 0.1376 | 0.1473 | 2.8518 | -0.0008 | +0.00001 | +0.00005 | -0.0023 |
| inj_d0.75 | 2019-22 | 1.3514 | 0.0832 | 0.1207 | 2.4916 | -0.0053 | -0.0012 | -0.0011 | +0.0052 |
| inj_d0.75 | 2023-25 | 1.5775 | 0.1376 | 0.1475 | 2.8612 | -0.0013 | +0.00005 | +0.0003 | +0.0071 |

The base row reproduces reports/season_backtest.csv's base (1.3570 / 1.5792 wins_mae there, 3000 runs).

## Verdict: nothing adopted. The simulation stays as it is (ratings unchanged, no absences in future games).

- Part 1, shrinking toward the league mean (k = 2, 4, 8): worse on every decisive metric on 2019-22 (wins_mae +0.08 to
  +0.11) and worse on wins_mae on 2023-25; it does lower the division and playoff Briers on 2023-25 (-0.002 / -0.004 to
  -0.006), and the SB log loss there, but that is one window and one side of the rule. Most of the damage is week 1, where
  n = 0 sets every team to the league mean (2019-22 week-1 wins_mae 2.50 against 2.18); from week 5 on the shrink is
  small either way (k = 2, weeks 5-17: wins_mae +0.00 to +0.03 on 2019-22, -0.00 on 2023-25). The as-of ratings' own
  decay (0.94 a week, last season at 0.8) already weights the season about right; no extra pull toward the mean helps.
- Part 1, sharpening (k = 1, 2): lowers wins_mae on 2019-22 (-0.009 / -0.010) but raises both Briers there and all
  three on 2023-25 (wins_mae +0.020 / +0.024, sb_ll +0.13 / +0.18), the week-1 cap of 1.5 doing most of it (2023-25
  week 1: wins_mae 2.64 against 2.54). Rejected on both windows' Briers.
- Part 2, absences carried forward (d = 0.5, 0.75): a small, consistent gain on 2019-22 (all three decisive metrics, d =
  0.75 the larger: wins_mae -0.005, div_brier -0.0012, po_brier -0.0011) and a smaller wins_mae gain on 2023-25
  (-0.001), but the division and playoff Briers on 2023-25 are flat to a hair worse (+0.00001 / +0.00005 at d = 0.5,
  +0.00005 / +0.0003 at d = 0.75), so the rule fails on that window. Per (season, week) it beats base on wins_mae in 22 of
  35, on either Brier in 20 of 35: a coin flip with a small mean edge. The effect is small because the as-of absences are
  mostly short (the mean margin moves 0.3 to 0.45 points one week ahead and half that or less two weeks on) and the
  current week, where absences matter most, already comes from the prediction table with its real injuries.

Best variant by as-of week (inj_d0.75 against base):

| window | week | wins_mae base | inj_d0.75 | div_brier base | inj_d0.75 | po_brier base | inj_d0.75 | sb_ll base | inj_d0.75 |
|---|---|---|---|---|---|---|---|---|---|
| 2019-22 | 1 | 2.1752 | 2.1655 | 0.1500 | 0.1489 | 0.2134 | 0.2117 | 2.7316 | 2.7630 |
| 2019-22 | 5 | 1.7661 | 1.7584 | 0.1043 | 0.1033 | 0.1480 | 0.1472 | 2.3398 | 2.3336 |
| 2019-22 | 9 | 1.3644 | 1.3562 | 0.0830 | 0.0805 | 0.1069 | 0.1050 | 2.4673 | 2.4695 |
| 2019-22 | 13 | 1.0348 | 1.0317 | 0.0717 | 0.0706 | 0.0909 | 0.0900 | 2.7431 | 2.7513 |
| 2019-22 | 17 | 0.4431 | 0.4453 | 0.0130 | 0.0126 | 0.0498 | 0.0496 | 2.1500 | 2.1404 |
| 2023-25 | 1 | 2.5425 | 2.5401 | 0.1917 | 0.1921 | 0.2527 | 0.2536 | 3.6292 | 3.6272 |
| 2023-25 | 5 | 2.0018 | 1.9960 | 0.1422 | 0.1412 | 0.1678 | 0.1680 | 3.2626 | 3.3164 |
| 2023-25 | 9 | 1.6656 | 1.6603 | 0.1496 | 0.1495 | 0.1578 | 0.1580 | 2.7065 | 2.7404 |
| 2023-25 | 13 | 1.1370 | 1.1458 | 0.1485 | 0.1495 | 0.1212 | 0.1215 | 2.3037 | 2.2758 |
| 2023-25 | 17 | 0.5474 | 0.5455 | 0.0557 | 0.0556 | 0.0367 | 0.0365 | 2.3686 | 2.3461 |

Not tested here (would be separate studies): a week-1 exemption for Part 1 (n = 0 is the degenerate case; from week 5 on
the knobs are near-neutral, so an exemption would most likely land at "no change" rather than a gain), and carrying only
the long absences (IR, the QB) rather than the whole week's report.

Runtime: 192 s for 35 (season, week) x 8 variants at 5000 runs on 2 processes (about 1.2 s per simulation; 0.5 s at
2000 runs), plus 2 s to load the frame. Files: experiments/season_update.py, reports/season_update.csv, this note.
