# Input ablation: does every live piece earn its spot? (pre-registered 3 Oct 2026, before any result)

## Claim
Matt (3 Oct 2026): "ensure everything used in the predictions earns its spot fully and accurately, not biased, no
cheating, no errors." The backtest became honest on 1-2 Oct 2026 (data fixes, leak fixes, forecast-priced weather
2015-2025, ref_tot dropped). Claim tested: every live piece of the prediction still beats the same model without it,
on every window, at no bet cost, and beats its own within-season shuffle.

## Pieces (one drop-one variant each; numbered)
Points equations (`model.FEATS`, every model of the blend; scored on team points miss):
P1 off_epa_play, P2 def_epa_play, P3 off_pf, P4 def_pf, P5 qb_rating, P6 home, P7 neutral, P8 dome, P9 wind_out,
P10 cold, P11 rain, P12 warm_in_cold, P13 div_game, P14 qb_out, P15 skill_out_value, P16 opp_skill_out_value,
P17 off_snap_out, P18 opp_def_snap_out, P19 off_turnover_early, P20 opp_def_turnover_early, P21 dead_late,
P22 opp_dead_late.

Totals equation (`model.TOTAL_FEATS`; scored on total miss):
T1 off_sum, T2 def_sum, T3 pf_sum, T4 pa_sum, T5 qb_sum, T6 qb_out_sum, T7 wind_out, T8 rain_fc (RAIN_FC),
T9 cold, T10 dome, T11 qb_form_sum (QB form).

Blend members (`model.BLEND_LABEL`; scored on team points miss): B1 ridge (the equation shown), B2 success,
B3 split, B4 plays, B5 alpha3, B6 alpha30, B7 trees (the boosted trees).

Other pieces: W1 wind points (`model.wind_points`; total miss), S1 the share-out of the total to the two teams (team
points miss), C1 cover calibration, C2 over calibration, C3 home win calibration, C4 teaser spread-leg calibration,
C5 teaser total-leg calibration (log loss, Brier as the calibration row; windows 2016-18 / 2019-22 / 2023-25 as in
reports/calibration_recheck.md, since 2015 has no earlier fit).

48 drop-one variants plus the live baseline; 50 placebo draws each (2,400 draws); one combined rerun if anything is
dropped. No variant is added after results; any that is will be listed under "added after results".

## Method
- Main's code and data (origin/main c1e38081, 3 Oct 2026). Every model variant refit walk-forward 2015-2025 with
  `model.walk_forward` (weekly refit, trees refit wherever their inputs change; `data/processed/trees_cache.parquet`
  never written). P and T variants: the input removed from `FEATS` / `TOTAL_FEATS`. B variants: the member left out of
  the average (the six others unchanged). W1: the model total without wind points, over chance re-priced from the same
  fit's training misses. S1: each team's points from the points equations themselves (`home_pts_eq`, `away_pts_eq`).
  C variants: the raw chance in place of the calibrated one.
- Timing: every input as of before the game, as live (forecast weather priced through `model.priced_weather`; injury
  and continuity inputs from the as-of tables). No line, split or price is an input; lines are used only to grade.
- Bet records (weeks 1-17, closing line, -110): the spread flag (|edge| 4+), the totals flag (55%+ raw under chance)
  and the wind under (10+ mph forecast). Calibrations feed no bet rule; their records are unchanged by construction.
- Placebo (50 draws, fixed seed, `study_gate.shuffle_within_season`): that piece's values shuffled within season,
  everything else as live, model refit. Game-level inputs (neutral, dome, wind_out, cold, rain, div_game and every
  totals input) shuffle whole games; team-level inputs shuffle team-games. A points-equation placebo leaves the totals
  equation on the real values and the other way round. Blend members: the member's predictions shuffled among the
  season's team-games. Wind points: the forecast wind shuffled among the season's forecast games. Share-out: the
  game's shift shuffled among the season's games. Calibrations: the calibrated-minus-raw logit shuffled within season.
- Gate (`nflmodel.study_gate.gate`), base = the model without the piece, new = the live model with it: part 1 lower
  miss on 2015-18, 2019-22 and 2023-25; part 2 the three bet records not worse (wins minus losses) on any window;
  part 3 the real gain above the placebo gain in 45+ of 50 draws on every window.

## Verdicts (fixed before results)
- **Earns its spot**: the gate passes every row.
- **Fails**: the model is at least as good without it (miss not lower with the piece) on two or more windows, or it
  fails part 1 on a window and its placebo on two or more windows.
- **Thin**: anything else (helps, but misses one test).

## What may change (Matt's standing approval)
A piece that fails is dropped from the live model only if (a) dropping it costs no flag wins on any window (spread
flag, totals flag, wind under: wins minus losses without it at least equal on every window); (b) the model-auditor
agrees; (c) every piece to be dropped is removed together and the reduced model, refit walk-forward 2015-2025, passes
parts 1 and 2 of the gate against the live model (round-3 rule part 5; team points miss and total miss both not worse on any window).
If dropping costs flag wins on any window it is not dropped and is reported for Matt. Thin pieces stay.

---

# Results (3 Oct 2026; everything below was written after the runs)

Script `experiments/input_ablation.py`; every per-piece gate table is in `reports/input_ablation_results.md`, the full
rows in `reports/input_ablation.csv`, the combined rerun in `reports/input_ablation_combined.md`.

**Live model, refit walk-forward 2015-2025 on main** (team and total miss within 0.0001 of the published pred_v3,
identical on every record):

| Window | Team miss | Total miss | Spread flag | Totals flag | Wind under |
|---|---|---|---|---|---|
| 2015-18 | 7.3993 | 10.7484 | 68-58 | 132-111 | 119-97 |
| 2019-22 | 7.3739 | 10.5340 | 78-49 | 175-140 | 143-88 |
| 2023-25 | 7.2357 | 10.1040 | 37-19 | 76-55 | 77-52 |

## Every piece (gain = miss without it minus miss with it; positive = it helps; placebo = draws beaten of 50)

| Piece | Gain 2015-18 / 2019-22 / 2023-25 | Bet records without it | Placebo | Verdict |
|---|---|---|---|---|
| P1 offense EPA rating | -0.0024 / -0.0006 / -0.0009 (team) | spread 71-53 / 77-46 / 36-20 | 16 / 22 / 15 | fails (dropping costs 2 net spread wins on 2023-25) |
| P2 defense EPA rating | -0.0064 / -0.0047 / +0.0026 | spread 67-54 / 84-59 / 39-22 | 4 / 4 / 47 | fails (costs spread wins 2019-22, 2023-25) |
| P3 offense points rating | +0.0039 / -0.0012 / +0.0030 | spread 79-62 / 79-62 / 39-34 | 48 / 17 / 48 | thin (bet cost 2015-18) |
| P4 defense points rating | +0.0332 / +0.0147 / +0.0161 | spread 80-76 / 82-60 / 32-18 | 50 / 50 / 50 | earns its spot |
| P5 QB rating | +0.0307 / +0.0188 / +0.0267 | spread 66-72 / 99-76 / 64-48 | 50 / 50 / 50 | earns its spot |
| P6 home | +0.0596 / -0.0215 / +0.0542 | spread 120-92 / 93-82 / 48-50 | 50 / 0 / 50 | thin (bet cost 2015-18) |
| P7 neutral site | -0.0001 / +0.0000 / +0.0000 | spread 68-57 / 78-49 / 37-19 | 8 / 16 / 31 | fails, no flag cost |
| P8 dome | -0.0002 / -0.0002 / -0.0002 | spread 69-54 / 77-48 / 37-19 | 30 / 10 / 18 | fails, no flag cost |
| P9 wind (points) | -0.0015 / -0.0004 / +0.0019 | spread 68-53 / 78-50 / 36-20 | 3 / 7 / 50 | fails (costs spread wins 2019-22, 2023-25) |
| P10 cold (points) | +0.0029 / +0.0014 / +0.0004 | spread 69-60 / 76-47 / 37-20 | 50 / 47 / 43 | thin |
| P11 rain (points) | +0.0009 / +0.0000 / -0.0018 | spread 69-57 / 77-46 / 39-18 | 48 / 19 / 0 | fails, no flag cost |
| P12 warm team in the cold | +0.0013 / +0.0045 / +0.0023 | spread 68-57 / 77-50 / 36-19 | 46 / 48 / 49 | thin (bet cost 2015-18) |
| P13 division game | -0.0005 / -0.0008 / -0.0003 | spread 66-56 / 78-48 / 37-19 | 20 / 2 / 19 | fails, no flag cost |
| P14 QB out (points) | -0.0037 / -0.0026 / -0.0016 | spread 69-55 / 79-49 / 38-19 | 1 / 5 / 8 | fails, no flag cost |
| P15 skill players out | +0.0033 / +0.0099 / +0.0167 | spread 69-58 / 65-48 / 30-19 | 44 / 50 / 50 | thin (bet cost 2015-18) |
| P16 opponent's skill players out | -0.0006 / +0.0034 / +0.0066 | spread 58-50 / 73-47 / 36-19 | 29 / 48 / 50 | thin |
| P17 offense snaps out | -0.0018 / -0.0005 / +0.0023 | spread 64-51 / 81-50 / 36-22 | 6 / 24 / 44 | fails (costs spread wins 2023-25) |
| P18 opponent defense snaps out | +0.0018 / +0.0022 / +0.0071 | spread 67-51 / 82-52 / 38-25 | 40 / 43 / 50 | thin (bet cost 2015-18, 2019-22) |
| P19 offseason turnover, offense | +0.0019 / +0.0059 / +0.0101 | spread 63-54 / 73-55 / 43-18 | 46 / 50 / 50 | thin (bet cost 2023-25) |
| P20 offseason turnover, opponent defense | +0.0060 / +0.0103 / +0.0114 | spread 63-57 / 78-54 / 42-18 | 50 / 50 / 50 | thin (bet cost 2023-25) |
| P21 out of the race | +0.0039 / -0.0027 / -0.0008 | spread 63-54 / 80-51 / 37-21 | 48 / 4 / 13 | fails (costs spread wins 2015-18, 2023-25) |
| P22 opponent out of the race | +0.0028 / -0.0035 / +0.0004 | spread 67-52 / 84-50 / 36-27 | 45 / 6 / 41 | fails (costs spread wins 2023-25) |
| T1 both offenses' EPA | +0.0066 / -0.0053 / +0.0013 (total) | totals 130-112 / 183-140 / 74-50 | 47 / 10 / 42 | fails (costs 3 net totals wins 2015-18) |
| T2 both defenses' EPA | +0.0276 / -0.0034 / +0.0069 | totals 134-110 / 173-134 / 82-51 | 49 / 22 / 47 | thin (bet cost all three windows) |
| T3 both offenses' points ratings | -0.0064 / -0.0166 / +0.0238 | totals 139-111 / 183-132 / 82-60 | 21 / 1 / 50 | fails, no flag cost |
| T4 both defenses' points ratings | -0.0065 / +0.0054 / +0.0048 | totals 129-114 / 179-140 / 77-60 | 19 / 43 / 44 | fails (costs totals wins 2015-18, 2023-25) |
| T5 both QB ratings | +0.0504 / +0.1161 / +0.0921 | totals 136-126 / 185-165 / 85-61 | 50 / 50 / 50 | thin (bet cost 2023-25) |
| T6 QBs out (totals) | -0.0116 / +0.0115 / -0.0223 | totals 130-109 / 170-134 / 79-57 | 14 / 48 / 0 | fails, no flag cost |
| T7 wind (totals) | +0.0174 / +0.0079 / +0.0228 | totals 127-112 / 162-131 / 69-54 | 48 / 43 / 50 | thin |
| T8 forecast rain (RAIN_FC) | +0.0359 / +0.0640 / +0.0795 | totals 124-108 / 164-141 / 66-52 | 50 / 50 / 50 | earns its spot |
| T9 cold (totals) | -0.0685 / -0.0034 / -0.0048 | totals 126-102 / 174-141 / 76-53 | 0 / 21 / 18 | fails (costs 2 net totals wins 2019-22) |
| T10 dome (totals) | +0.0021 / -0.0154 / +0.0064 | totals 131-114 / 173-141 / 77-53 | 40 / 2 / 46 | fails (costs totals wins 2015-18, 2019-22) |
| T11 QB form | +0.0614 / +0.0510 / +0.0695 | totals 135-120 / 189-144 / 72-59 | 50 / 49 / 50 | thin (bet cost 2019-22) |
| B1 ridge (the equation shown) | -0.0006 / +0.0001 / +0.0000 (team) | spread 70-54 / 78-47 / 38-20 | 50 / 45 / 50 | thin (bet cost 2015-18, 2019-22) |
| B2 + success rate | -0.0007 / +0.0006 / +0.0011 | spread 66-56 / 79-50 / 38-20 | 50 / 46 / 50 | thin |
| B3 + pass and rush ratings | +0.0010 / +0.0006 / -0.0002 | spread 68-52 / 76-47 / 38-19 | 50 / 46 / 50 | thin (bet cost 2015-18, 2023-25) |
| B4 + plays per game | -0.0010 / +0.0000 / -0.0018 | spread 68-55 / 77-46 / 38-21 | 50 / 44 / 49 | fails (costs 1 net spread win 2023-25) |
| B5 less shrinkage | -0.0006 / +0.0000 / +0.0001 | spread 70-54 / 78-47 / 38-20 | 50 / 45 / 50 | thin (bet cost 2015-18, 2019-22) |
| B6 more shrinkage | -0.0006 / +0.0001 / +0.0000 | spread 70-54 / 78-46 / 38-20 | 50 / 46 / 50 | thin (bet cost 2015-18, 2019-22) |
| B7 boosted trees | +0.0042 / -0.0001 / +0.0025 | spread 63-58 / 80-53 / 38-22 | 50 / 44 / 50 | thin |
| W1 wind points | -0.0024 / -0.0031 / +0.0110 (total) | totals 131-116 / 171-136 / 68-52 | 26 / 23 / 49 | fails (costs totals wins 2015-18, 2023-25) |
| S1 share-out of the total | -0.0150 / -0.0254 / +0.0183 (team) | unchanged (moves no bet) | 49 / 43 / 50 | fails, no flag cost |
| C1 cover calibration | +0.0132 / +0.0061 / +0.0059 (log loss) | none (feeds no bet) | 50 / 49 / 41 | thin |
| C2 over calibration | +0.0111 / +0.0023 / -0.0001 | none | 50 / 47 / 42 | thin |
| C3 home win calibration | +0.0027 / +0.0015 / +0.0013 | none | 49 / 49 / 40 | thin |
| C4 teaser spread-leg calibration | -0.0004 / +0.0013 / +0.0011 | none | not defined (one shift per season) | thin |
| C5 teaser total-leg calibration | +0.0099 / +0.0048 / -0.0010 | none | 50 / 50 / 47 | thin |

Team-points gains are mean absolute error in points per team-game, total gains per game, calibration gains log loss
(calibration windows 2016-18 / 2019-22 / 2023-25). Live records: spread 68-58 / 78-49 / 37-19, totals 132-111 /
175-140 / 76-55. A "bet cost" means the live record (with the piece) has fewer net wins than without it on that window.

**Tally:** 3 earn their spot (P4 defense points rating, P5 QB rating, T8 forecast rain), 24 thin, 20 fail.

C4's placebo is not defined: its calibration is one shift per season, so a within-season shuffle returns the same
values (found by the audit; the first summary scored C4 "fails" on floating-point noise in those rows). Scored on
parts 1 and 2 only, it is thin. The blend-member (B), share-out (S1) and calibration (C) placebos are not informative:
a shuffled member or shift mostly adds noise, so almost anything beats it (audit check 4). Their verdicts rest on
parts 1 and 2.

## The drop rule (pre-registered)
Fail with no flag cost: P7 neutral, P8 dome, P11 rain, P13 division game, P14 QB out (points equations), T3 both
offenses' points ratings, T6 QBs out (totals), plus S1 (a display piece, below). The seven model inputs were dropped
together and the model refit walk-forward 2015-2025 (round-3 part 5). That run was made after the variants and the
totals draws but before the last P7 and P11 placebo draws were in, and those two fail only through their placebo rows
(each loses one window on the miss; P7's other two gains are +0.000003); so the set was named before the rule could
fully select it. It equals the rule's final output and only one combined run was made, but the order was not as
pre-registered (audit check 5):

| Window | Team miss live -> without | Total miss | Spread flag | Totals flag |
|---|---|---|---|---|
| 2015-18 | 7.3993 -> 7.3891 | 10.7484 -> 10.7238 | 68-58 -> 67-54 | 132-111 -> 142-117 |
| 2019-22 | 7.3739 -> 7.3681 | 10.5340 -> 10.5343 | 78-49 -> 81-53 | 175-140 -> 183-134 |
| 2023-25 | 7.2357 -> 7.2288 | 10.1040 -> 10.1037 | 37-19 -> 38-17 | 76-55 -> 86-61 |

Wind under unchanged (119-97 / 143-88 / 77-52). The combined drop fails part 2 (the spread flag loses one net win on
2019-22, +29 to +28, -1.4 units) and part 1 on total miss 2019-22 (0.0003 worse). **Per the pre-registration nothing
is dropped**; the set goes to Matt. Every other row is better: team miss on every window, the totals flag +4 / +14 /
+4 net wins (+3.4 / +14.6 / +3.4 units), the spread flag +3 / -1 / +3 net wins.

S1 (the share-out) fails with no bet cost, but it feeds no bet: it makes the two team scores on a card add up to the
game total (Matt's rule, 25 Sep 2026). The pre-registered rule already keeps it (part (c): the combined drop failed,
and adding S1 moves no bet so it cannot fix the spread-flag cost); it is also a display choice, so it is reported for
Matt (round-3 part 4: no page change beyond the number it moves).

## Pieces that fail but cost flag wins if dropped (for Matt)
P1, P2, P9, P17, P21, P22 (points equations), T1, T4, T9, T10 (totals), B4 (the plays model), W1 (wind points). Each
is worse on the miss on two or more windows (or one window plus its placebo on two), yet the live bets win more with it
on at least one window. Notable: cold in the totals equation (T9) is worse on all three windows (0.0685 on 2015-18) and
costs 2 net totals wins on 2019-22 if dropped; wind points (W1) are worse on 2015-18 and 2019-22 on the honest backtest,
and dropping them costs 6 and 5 net totals-flag wins on 2015-18 and 2023-25.

## Count and caveats
- Variants: 1 live baseline, 47 drop-one variants (the pre-registration said 48: a miscount of the same list; nothing
  was added after results), 2,350 placebo draws, 1 combined rerun. Earlier single-piece studies in the decision log
  (ref_tot, wind points, rain, QB form, the calibrations, home field, the input set of 22 Sep) are not re-counted here.
- Placebo draws for P and T pieces refit only the equation the shuffle touches (`fast_totals`, `fast_points`: the same
  weekly loop, rows and fits as `model.walk_forward`). `check_fast()` printed a largest difference of 0.0 against
  `walk_forward` on all 3,028 games for the baseline (model_total, p_over_emp, model_spread, home_m_trees), dropped rain_fc
  (model_total, p_over_emp) and dropped cold (model_spread); two totals draws made by full refits (T1 draw 0, T3 draw 1)
  were remade by `fast_totals` with differences of 0.0 on both misses in every window.
- The blend-member placebo (a member's predictions shuffled) mostly adds noise to the average, so nearly every member
  beats it; it says little. The share-out and calibration placebos shuffle the adjustment within season.
- The run was interrupted twice (an app restart and the 2-hour background limit); every finished run and draw is a file,
  so it resumed where it stopped (the last draws in bounded batches); the baseline was rerun with one thread per process
  and matched the first run to 0.0.

## Audit
model-auditor (reports/audit_input_ablation_2026-10-03.md): **"holds with caveats. The numbers are right, and 'drop
nothing, give the set of seven to Matt' follows the pre-registered rule."** It rechecked every P and T gain and placebo
count, the baseline against pred_v3 and the combined run; three stored draws (P14, P13, T6) were reproduced to 0.0 and one full walk-forward with the same shuffle (2015-16) matched the fast refit to 0.0;
the leak test gave 0.0 with the trees cache read only; no look-ahead or market input (`nflmodel/` unchanged). Caveats: C4's placebo was broken (now not defined, verdict thin), the blend, share-out and calibration
placebos are not informative, the combined run preceded the last P7 and P11 draws, and the bet-cost marks on P3, P15
and P18 were missing (added, with P6, T2, B1, B3, B5, B6). The pre-registration was not committed before the results, so its timing cannot be proven from the repo
(it sits above the Results line, unchanged). On sample size: every gain and cost in the drop decision is
inside one standard error (spread flag about 4.4 points on 127 bets in 2019-22; team-miss noise about 0.006), so "fails"
here means "no detectable value", not "proven harmful", and the one spread win that blocks the drop is not a real cost
either. The 2026 season is the next real test.

## Decision
No piece is dropped: the seven inputs that fail with no flag cost, dropped together, cost one net spread-flag win on
2019-22 and 0.0003 of total miss on 2019-22, which the pre-registered rule does not allow. Reported for Matt: that set
(better everywhere else, totals flag +22 net wins over the three windows, all inside the noise), the share-out (display
only), and the twelve pieces that fail but whose removal costs flag wins. Nothing in the live model or bet rules changes.
