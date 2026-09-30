# Usual snaps: pricing an out player by his usual role (30 Sep 2026)

`experiments/usual_snaps.py`; every variant and window in `reports/usual_snaps.csv`. Rule: `reports/round3_rule.md`.

**Verdict: nothing is adopted; the live last-game share stays.** The best variant is 6b: an out player's mean share over his
last 4 games played, counted only if he played in one of the team's last 4 games. It lowers the team points miss on all three
windows (-0.017 / -0.004 / -0.020 points on 2015-18 / 2019-22 / 2023-25), improves the win chance's log loss and Brier on all three,
and beats its placebo on all three windows in 48 of 50 draws. It fails two parts of the rule. The margin miss rises on 2019-22
(+0.007). The spread flag loses 5 wins net on 2015-18 (68-54 to 59-50), though it gains 6 on 2019-22 and 2 on 2023-25. The totals
flag does not move.

Plain usual shares with no time limit (variants 1 to 5: last 3, 4 or 8 games played, season to date, the max of last game and
last 4) are worse. They keep counting players who have been on IR for months, whose absence is already in the team's ratings,
and they raise both misses on 2019-22 and lose spread wins. Every gated version (last 2, 4 or 8 team games, and two more built on
the 4-game gate) also fails rule 2, and all but the 2-game gate raise the margin miss on 2019-22. The owner's case is real: in
2025, 474 times a 90%+ starter who had also missed the previous game was out and priced at 0. But no version of "usual role"
tested here prices those players better without costing spread bets somewhere.

## The rule, variant by variant

Each variant replaces the live last-game share in `off_snap_out` and `def_snap_out` (so also the opponent's
`opp_def_snap_out`), the only snaps-out inputs the model reads. Changes against the base, per window 2015-18 / 2019-22 / 2023-25
(misses in points, below zero is better; flag records as the change in wins minus losses; log loss and Brier of the calibrated
win chance, times 1000, below zero is better). Rule 1 here needs both the team points miss and the margin miss lower on all three
windows; rule 2 needs both flag records not worse and log loss and Brier not worse on all three. The totals flag never moves: the
total equation has no snaps-out input. The placebo ran for the four variants that lower the team points miss on every window
(50 draws for the best, 20 for the others, as a reading: none of them passes rule 2, which gates the placebo).

| variant | team points miss | margin miss | spread flag W-L | totals flag W-L | log loss x1000 | Brier x1000 | placebo (real beats, per window) | 2026 team miss | verdict |
|---|---|---|---|---|---|---|---|---|---|
| 1. Mean of last 3 games played | -0.0171 / +0.0038 / -0.0201 | -0.0266 / +0.0389 / -0.0192 | -3 / -4 / -11 | +0 / +0 / +0 | -2.43 / +0.68 / -1.64 | -0.98 / +0.25 / -0.64 | not run | -0.0042 | no: 1: team miss up 2019-22; 1: margin miss up 2019-22; 2: spread flag down 2015-18, 2019-22, 2023-25; 2: log loss / Brier up 2019-22 |
| 2. Mean of last 4 games played | -0.0162 / +0.0032 / -0.0242 | -0.0306 / +0.0400 / -0.0324 | -1 / -3 / -5 | +0 / +0 / +0 | -2.63 / +0.69 / -2.21 | -1.08 / +0.24 / -0.90 | not run | -0.0014 | no: 1: team miss up 2019-22; 1: margin miss up 2019-22; 2: spread flag down 2015-18, 2019-22, 2023-25; 2: log loss / Brier up 2019-22 |
| 3. Mean of last 8 games played | -0.0151 / +0.0051 / -0.0240 | -0.0241 / +0.0455 / -0.0402 | -3 / -2 / -6 | +0 / +0 / +0 | -1.82 / +0.97 / -2.62 | -0.73 / +0.38 / -1.08 | not run | -0.0046 | no: 1: team miss up 2019-22; 1: margin miss up 2019-22; 2: spread flag down 2015-18, 2019-22, 2023-25; 2: log loss / Brier up 2019-22 |
| 4. Season to date (last season if none) | -0.0144 / +0.0025 / -0.0217 | -0.0162 / +0.0322 / -0.0239 | +0 / -4 / -6 | +0 / +0 / +0 | -1.52 / +0.12 / -1.68 | -0.56 / +0.08 / -0.65 | not run | +0.0132 | no: 1: team miss up 2019-22; 1: margin miss up 2019-22; 2: spread flag down 2019-22, 2023-25; 2: log loss / Brier up 2019-22 |
| 5. max(last game, last 4 played) | -0.0162 / +0.0031 / -0.0258 | -0.0291 / +0.0332 / -0.0344 | -4 / -1 / -9 | +0 / +0 / +0 | -2.63 / +0.31 / -2.35 | -1.12 / +0.09 / -0.96 | not run | -0.0035 | no: 1: team miss up 2019-22; 1: margin miss up 2019-22; 2: spread flag down 2015-18, 2019-22, 2023-25; 2: log loss / Brier up 2019-22 |
| 6a. Last 4 played, only if he played in the team's last 2 | -0.0055 / -0.0036 / +0.0030 | -0.0094 / -0.0057 / +0.0001 | +0 / -4 / +2 | +0 / +0 / +0 | -0.47 / -0.42 / +0.01 | -0.24 / -0.23 / -0.09 | not run | +0.0063 | no: 1: team miss up 2023-25; 1: margin miss up 2023-25; 2: spread flag down 2019-22; 2: log loss / Brier up 2023-25 |
| 6b. Last 4 played, only if he played in the team's last 4 | -0.0174 / -0.0036 / -0.0203 | -0.0225 / +0.0073 / -0.0214 | -5 / +6 / +2 | +0 / +0 / +0 | -1.49 / -2.41 / -1.41 | -0.61 / -0.93 / -0.70 | 50 / 48 / 50 of 50 | +0.0250 | no: 1: margin miss up 2019-22; 2: spread flag down 2015-18; (3 passes: 48 of 50) |
| 6c. Last 4 played, only if he played in the team's last 8 | -0.0140 / -0.0092 / -0.0209 | -0.0306 / +0.0256 / -0.0059 | -3 / -3 / -2 | +0 / +0 / +0 | -2.04 / -1.94 / -1.52 | -0.79 / -0.74 / -0.56 | 20 / 20 / 20 of 20 | +0.0177 | no: 1: margin miss up 2019-22; 2: spread flag down 2015-18, 2019-22, 2023-25; 3: beats the placebo on all three windows in 20 of 20 (needs 45 of 50; a reading at 20 draws) |
| 6d. max(last game, last 4 played), the usual part only if he played in the team's last 4 | -0.0158 / -0.0035 / -0.0237 | -0.0227 / +0.0032 / -0.0257 | -8 / -1 / +1 | +0 / +0 / +0 | -1.41 / -2.47 / -1.66 | -0.59 / -0.96 / -0.79 | 20 / 20 / 20 of 20 | +0.0280 | no: 1: margin miss up 2019-22; 2: spread flag down 2015-18, 2019-22; 3: beats the placebo on all three windows in 20 of 20 (needs 45 of 50; a reading at 20 draws) |
| 6e. Season to date, only if he played in the team's last 4 | -0.0194 / -0.0005 / -0.0176 | -0.0267 / +0.0092 / -0.0157 | -6 / +1 / -3 | +0 / +0 / +0 | -1.92 / -1.85 / -1.36 | -0.78 / -0.65 / -0.65 | 20 / 17 / 20 of 20 | +0.0229 | no: 1: margin miss up 2019-22; 2: spread flag down 2015-18, 2023-25; 3: beats the placebo on all three windows in 17 of 20 (needs 45 of 50; a reading at 20 draws) |

Base (the live inputs rebuilt by the script, same code path as every variant, fresh trees):

| window | games | team points miss | margin miss | total miss | spread flag | totals flag | log loss (cal) | Brier (cal) |
|---|---|---|---|---|---|---|---|---|
| 2015-18 | 1024 | 7.4088 | 9.9479 | 10.7437 | 68-54 | 135-127 | 0.6194 | 0.2154 |
| 2019-22 | 1055 | 7.3463 | 10.0168 | 10.5406 | 80-51 | 175-128 | 0.6240 | 0.2171 |
| 2023-25 | 816 | 7.2618 | 9.9027 | 10.1767 | 39-21 | 71-59 | 0.6200 | 0.2153 |
| 2026 | 48 | 8.1357 | 10.6238 | 11.4556 | 1-2 | 7-4 | 0.6499 | 0.2288 |

## How much each variant changes

Regular and postseason team-games 2015-2025 (the model's rows). "Changed" means `off_snap_out` or `def_snap_out` differs from the live
value. Spread move: the model spread against the base, 2015-25 regular season (2895 games).

| variant | team-games changed (of 6056) | changed by 0.5+ | mean off_snap_out 2023-25 (live 0.33) | mean |spread move| | games moved 0.5+ | ol_out changed | off starters changed | def starters changed |
|---|---|---|---|---|---|---|---|---|
| L3 | 5745 | 5341 | 2.0 | 0.66 | 1525 | 3264 | 4370 | 4233 |
| L4 | 5745 | 5347 | 2.03 | 0.68 | 1547 | 3278 | 4391 | 4286 |
| L8 | 5748 | 5377 | 2.08 | 0.68 | 1559 | 3300 | 4466 | 4377 |
| STD | 5727 | 5269 | 1.91 | 0.63 | 1480 | 3141 | 4288 | 4136 |
| MAX_L4 | 5715 | 5379 | 2.05 | 0.65 | 1494 | 3278 | 4411 | 4306 |
| L4_G2 | 5178 | 3090 | 0.7 | 0.36 | 735 | 1202 | 2177 | 2150 |
| L4_G4 | 5578 | 4467 | 1.06 | 0.6 | 1355 | 1983 | 3168 | 3138 |
| L4_G8 | 5701 | 5082 | 1.47 | 0.7 | 1577 | 2700 | 3925 | 3833 |
| MAX_L4_G4 | 5477 | 4530 | 1.08 | 0.57 | 1291 | 1982 | 3190 | 3148 |
| STD_G4 | 5561 | 4468 | 1.06 | 0.58 | 1342 | 1920 | 3141 | 3113 |

The ungated usual shares (1 to 5) carry every player still on IR or PUP for as long as he stays there, including players hurt a
season or more ago: the average team-game goes from 0.33 of a player's offensive snaps out to about 2. Those players are already out
of the team's ratings (every game they missed is in its EPA and points), so the input double counts, and all five raise the margin
miss on 2019-22 and lose spread wins on every window. Gating at the team's last 4 or 8 games removes most of that and lowers the
team points miss on every window, but still raises the margin miss on 2019-22 and loses spread wins on 2015-18.

## Sanity checks

This week, WAS (home to IND). Out players with any share, and the WAS inputs and model spread (home margin) under each variant:

| player | position | games_since_played | off_current | off_L4 | off_L4_G4 | off_L4_G8 | def_current | def_L4 | def_L4_G4 | def_L4_G8 |
|---|---|---|---|---|---|---|---|---|---|---|
| Laremy Tunsil | T | 6 | 0.0 | 0.87 | 0.0 | 0.87 | 0.0 | 0.0 | 0.0 | 0.0 |
| Leo Chenal | LB | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.24 | 0.49 | 0.49 | 0.49 |
| Jer'Zhan Newton | DT | 3 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.49 | 0.49 | 0.49 |
| Samuel Cosmi | G | 1 | 0.0 | 0.97 | 0.97 | 0.97 | 0.0 | 0.0 | 0.0 | 0.0 |
| Trey Amos | CB | 10 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.76 | 0.0 | 0.0 |
| Jordan Magee | LB | 2 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.39 | 0.39 | 0.39 |
| Nick Cross | S | 1 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.99 | 0.99 | 0.99 |
| Jeremy McNichols | RB | 3 | 0.0 | 0.35 | 0.35 | 0.35 | 0.0 | 0.0 | 0.0 | 0.0 |
| Nick Bellore | LB | 3 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.05 | 0.0 | 0.0 |
| Deatrich Wise Jr. | DE | 18 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.38 | 0.0 | 0.0 |

| variant | WAS off_snap_out | WAS def_snap_out | model spread (WAS) |
|---|---|---|---|
| current | 0.0 | 0.24 | 1.51 |
| L3 | 2.09 | 3.51 | -0.1 |
| L4 | 2.19 | 3.54 | -0.06 |
| L8 | 2.14 | 3.53 | -0.15 |
| STD | 2.19 | 3.23 | -0.37 |
| MAX_L4 | 2.19 | 3.54 | -0.19 |
| L4_G2 | 0.97 | 1.48 | 0.67 |
| L4_G4 | 1.32 | 2.36 | -0.21 |
| L4_G8 | 2.19 | 2.36 | 0.02 |
| MAX_L4_G4 | 1.32 | 2.36 | -0.04 |
| STD_G4 | 1.3 | 2.02 | 0.17 |

2025 regular season: 474 times an out player whose usual share (last 4 games played) was 90%+ had also missed the previous
game, on 306 team-games; the live input counted every one as 0. He had missed 1 game in 84 of them, 2 to 3 in
98, 4 to 7 in 122 and 8 or more in 170. Share still counted: last 4 gated at 2 games
18%, at 4 38%, at 8 64%; ungated 100%. Examples (missed 1 or 2 games):

| game_id | team | player | position | games_since_played | off_L4 | def_L4 |
|---|---|---|---|---|---|---|
| 2025_02_ATL_MIN | ATL | Kaleb McGary | T | 1 | 1.0 | 0.0 |
| 2025_02_CLE_BAL | BAL | Ar'Darius Washington | FS | 1 | 0.0 | 0.94 |
| 2025_02_JAX_CIN | CIN | Cordell Volson | G | 1 | 1.0 | 0.0 |
| 2025_02_CHI_DET | DET | Frank Ragnow | C | 1 | 1.0 | 0.0 |
| 2025_02_DEN_IND | IND | Jaylon Jones | CB | 1 | 0.0 | 0.96 |
| 2025_02_LAC_LV | LAC | Rashawn Slater | T | 1 | 0.97 | 0.0 |
| 2025_02_LAC_LV | LV | Aidan O'Connell | QB | 1 | 0.9 | 0.0 |
| 2025_02_ATL_MIN | MIN | Jordan Addison | WR | 1 | 0.9 | 0.0 |
| 2025_02_NE_MIA | NE | Layden Robinson | G | 1 | 1.0 | 0.0 |
| 2025_02_SF_NO | NO | Tyrann Mathieu | FS | 1 | 0.0 | 0.92 |
| 2025_02_SF_NO | NO | Trevor Penning | T | 1 | 1.0 | 0.0 |
| 2025_02_BUF_NYJ | NYJ | Alijah Vera-Tucker | G | 1 | 1.0 | 0.0 |

Biggest movers under 6b. Last 4 played, only if he played in the team's last 4 (2015-25 regular season; the players added, at their usual share):

| game_id | team | off_live | off_var | def_live | def_var | home_spread_move | players |
|---|---|---|---|---|---|---|---|
| 2022_17_DAL_TEN | TEN | 1.2 | 5.46 | 2.2 | 5.85 | -2.04 | Ben Jones (96%), Ryan Tannehill (91%), Nate Davis (88%), Amani Hooker (82%) |
| 2023_04_PIT_HOU | HOU | 1.0 | 5.43 | 0.0 | 2.89 | -2.48 | Laremy Tunsil (100%), Scott Quessenberry (100%), Denzel Perryman (98%), Derek Stingley Jr. (96%) |
| 2024_04_LA_CHI | LA | 0.0 | 4.91 | 0.0 | 2.04 | 1.69 | Jonah Jackson (100%), Cooper Kupp (88%), Steve Avila (87%), Aaron Donald (82%) |
| 2019_16_DET_DEN | DET | 0.67 | 4.89 | 0.19 | 2.74 | 1.6 | Jeff Driskel (100%), Marvin Jones (94%), Joe Dahl (93%), Jarrad Davis (78%) |
| 2021_18_IND_JAX | JAX | 0.0 | 3.72 | 0.13 | 3.16 | -1.46 | Andrew Wingard (100%), Cam Robinson (87%), Brandon Linder (86%), Rayshawn Jenkins (81%) |
| 2019_05_NYJ_PHI | NYJ | 1.0 | 4.54 | 0.0 | 2.93 | 1.74 | Avery Williamson (100%), Sam Darnold (100%), Quincy Enunwa (88%), Chris Herndon (73%) |
| 2020_17_WAS_PHI | PHI | 2.47 | 4.45 | 1.85 | 6.33 | -2.95 | Rodney McLeod (89%), Jason Peters (80%), Avonte Maddox (75%), Derek Barnett (64%) |
| 2022_18_ARI_SF | ARI | 0.78 | 3.52 | 1.36 | 5.04 | 1.95 | Budda Baker (100%), Antonio Hamilton (98%), DeAndre Hopkins (86%), Colt McCoy (82%) |
| 2019_03_NYJ_NE | NYJ | 0.39 | 3.65 | 0.16 | 3.28 | 2.22 | Avery Williamson (100%), Sam Darnold (100%), Quincy Enunwa (88%), Chris Herndon (73%) |
| 2021_04_SEA_SF | SF | 0.0 | 2.52 | 0.58 | 4.38 | -2.6 | Tarvarius Moore (100%), Jason Verrett (91%), Dre Greenlaw (83%), Richie James (66%) |

## Caveats

- The rule's base is the live input rebuilt by this script (it matches `trends_asof.parquet` to 1e-15 on all 7,870 team-games) and
  rounded to 9 decimals like every variant. Run straight from the live table, the base differs by last-digit float noise, which
  moves the boosted trees' bins: team points miss +0.0007 / +0.0012 / +0.0007. That is the noise floor of a single comparison. The gated variants' gains sit well above it on 2015-18 and 2023-25
  (0.005 to 0.024); on 2019-22 they are 0.0005 to 0.009, around it. The placebo is what separates the two.
- Fresh trees on this machine for base and every variant (the live trees' cache holds GitHub runners' fits; fresh fits move the
  base spread by 0.008 points on average). Weekly refit, 2013 on, as the live walk-forward.
- A player's history counts only games for this team (a player traded in or signed counts 0 until he plays for it), and only games
  with snap data (2012 on). The out set, snap source and id matching are the live ones; nothing new is pulled.
- The gate counts the team's games, across the offseason: in Weeks 1 to 4 a player who last played in the final games of last
  season still counts, including one since retired or released but still listed as unavailable (Aaron Donald, retired, counts
  for LA in 2024 Week 4 above). The ungated variants carry such players all season.
- `ol_out`, `off_starters_out` and `def_starters_out` are not model inputs (only readings on the page), so their changes, counted
  above, cannot move a prediction. `qb_out` was left as it is.
- 2026 is weeks 1 to 3 only (48 games): a reading, not part of the rule. The team points miss there is 0.018 to 0.028 worse under 6b to 6e and 0.006 worse under 6a; the
  ungated ones are within 0.005 either way except season to date (+0.013).
- Data snapshot: the weekly run rewrote `data/processed` at 16:23 while the study ran, so every run here reads one snapshot taken
  after it (scratch folder), base and variants alike.
