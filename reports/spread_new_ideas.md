# Spread: new rating-construction ideas (3 Oct 2026)

Script: `experiments/spread_new_ideas.py`. Nothing in the live model changes with this study unless a variant passes
every part of the rule, the model-auditor and the together test (Matt's standing approval for a clear winner).

## Pre-registered (written before any result)

**Claim.** Matt (3 Oct 2026): improve spread accuracy and the spread flag's wins and units against Vegas with new ideas
from all angles. Tested here: eight changes to how the team ratings are built, none of them tried before.

**What was already tried and is not re-tested** (decision log): one decay, last-season weight and ridge for all
ratings (retune, sweep_all, season_fade: about 40 settings), recent seasons weighted more in the refit, rolling
training windows, success rate and the pass/rush split as inputs, garbage-time EPA in the lab correlation (0.46 against
0.50, never in the model), clipped and turnover-neutral EPA, the QB rating adjusted for defenses, QB rushing, sacks out,
QB prior by draft slot, new coach / new QB / line continuity as inputs, roster continuity as an input (adopted),
per-team and per-era home field, travel distance, time-zone shift, West Coast at 1pm, rest and short weeks (four
times), the scheme profiles. Opponent-adjustment iterations do not apply: the ratings are one joint weighted solve of
all 32 offenses and defenses, already exact.

**Variants** (each rebuilds the ratings 2013-2026 with `ratings.build_features`'s own loop, the live QB rating and
every other input unchanged, then refits the live pipeline walk-forward 2015-2025: weekly refit, the seven-model blend,
the totals equation, forecast weather for played games). Live: weight = 0.94^weeks ago, last season x0.8, ridge 16
on offenses and defenses alike, every game one row of equal weight, all plays.

- **V1. Carryover by roster continuity.** Last season's games count by how much of each unit came back: a last-season
  row (offense i against defense j) is weighted x m_off(i) x m_def(j), m = this season's week-1 share of last season's
  snaps on the active roster (trends.continuity_table) over the league mean that season, clipped to 0.5-1.5. This
  season's games unchanged.
- **V2. Rows with the current QB.** Any past game (this or last season) whose starting QB for that offense is not the QB
  the team starts in the priced week counts half (x0.5) in the team's ratings. The priced week's QB is the one the
  ratings already use (the starter named for the game; the last named starter carried forward).
- **V3. Defense shrunk twice as hard.** Ridge 32 on the defense ratings, 16 on the offense ratings (defense is the
  noisier side: nothing defensive predicts above 0.26 in the lab table).
- **V4. Defense carries less of last season.** Defense ratings from a solve with last season x0.5; offense ratings keep
  x0.8.
- **V5. Games weighted by plays.** For the per-play ratings (EPA per play and success rate by plays, pass EPA by pass
  plays, rush EPA by rush plays), each game's weight is multiplied by its play count over the window's mean, so a
  48-play game counts less than a 75-play one. Points and plays per game unchanged.
- **V6. Early-down EPA.** The EPA rating (off_epa_play, def_epa_play) built from first- and second-down plays only
  (team_games.early_down_epa), the common finding that early downs carry the signal and third downs the noise.
- **V7. Garbage time at half weight.** EPA per play and success rate with plays at a win chance under 10% or over 90%
  (nflverse `wp`, the no-market win model) counted half: (ng sum + 0.5 x garbage sum) / (ng plays + 0.5 x garbage plays).
- **V8. Longer memory for the per-play stats.** EPA per play, pass and rush EPA and success rate decay 0.96 a week;
  points and plays per game keep 0.94 (EPA per play is the steadier stat).

**Data and timing.** Every input is from games before the week priced (the ratings window is unchanged: this season's
earlier weeks and last season). Continuity is the week-1 active roster against last season's snaps (known before the
season, already a live input). The QB for the priced week is the one the QB rating already prices. `wp` is a
pre-snap number inside past games. No line, split or price enters anything.

**Pass bar** (`nflmodel.study_gate.gate`, reports/round3_rule.md), all of:
1. Margin miss **and** team points miss lower on 2015-18 (untouched), 2019-22 (tuning) and 2023-25 (held out),
   regular season.
2. No bet cost on any window: the spread flag (edge 4+, weeks 1-17), the totals flag (55%+ under) and the wind under
   (10+ mph) each with wins minus losses not worse; the home win chance's Brier score not worse.
3. Beats its placebo on both misses: the variant's change to each team-game's ratings (new minus live, all rating
   columns together) moved to another team-game of the same season (`study_gate.shuffle_within_season`), 50 draws, seed
   20261003, the real gain larger in at least 45 of 50 on every window. Run for a variant that passes parts 1 and 2.
4. Model-auditor on any variant that passes 1 to 3.
5. Together: every passer rerun together must pass parts 1 and 2. A clear single winner that passes every part may be
   adopted (Matt's standing yes); otherwise the result is reported.

Descriptive only (not part of the bar): the spread flag and margin miss in weeks 1-4.

**Count.** Eight variants here. Earlier studies of rating construction: about 40 decay / last-season / ridge settings
(retune, retune2, sweep_all, season_fade), clipped and turnover-neutral EPA (2), success and split ratings (2), the
garbage-time lab check (1). A variant chosen as best of eight is judged with that in mind.

## Results

The rebuilt live ratings equal the stored ones (largest difference 2.2e-13); the variant code with every switch off equals them too (0.0e+00).

Each variant refit walk-forward 2015-2025, regular season scored; flags at the live rules, weeks 1-17. Units at -110 = wins - 1.1 x losses.

| Variant | Window | Margin miss | Team miss | Total miss | Brier (home win) | Spread flag | Units | Totals flag | Wind under | Spread flag wk 1-4 | Margin miss wk 1-4 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| live | 2015-18 | 9.9469 | 7.3995 | 10.7484 | 0.21504 | 68-57 | +5.3 | 132-111 | 119-97 | 23-14 | 10.2542 |
| live | 2019-22 | 10.0108 | 7.3735 | 10.5340 | 0.21740 | 78-49 | +24.1 | 175-140 | 143-88 | 18-13 | 9.3538 |
| live | 2023-25 | 9.9070 | 7.2356 | 10.1040 | 0.21609 | 37-19 | +16.1 | 76-55 | 77-52 | 19-5 | 10.1904 |
| V1 last season weighted by roster continuity | 2015-18 | 9.9609 | 7.4037 | 10.7589 | 0.21564 | 67-55 | +6.5 | 131-116 | 119-97 | 23-13 | 10.2962 |
| V1 last season weighted by roster continuity | 2019-22 | 10.0047 | 7.3735 | 10.5375 | 0.21736 | 80-51 | +23.9 | 178-145 | 143-88 | 17-13 | 9.3362 |
| V1 last season weighted by roster continuity | 2023-25 | 9.8966 | 7.2318 | 10.1060 | 0.21547 | 37-20 | +15.0 | 77-55 | 77-52 | 16-4 | 10.1905 |
| V2 games with another QB at half weight | 2015-18 | 9.9533 | 7.3983 | 10.7301 | 0.21500 | 62-60 | -4.0 | 130-108 | 119-97 | 21-13 | 10.2786 |
| V2 games with another QB at half weight | 2019-22 | 10.0142 | 7.3776 | 10.5459 | 0.21754 | 80-52 | +22.8 | 180-144 | 143-88 | 21-12 | 9.3785 |
| V2 games with another QB at half weight | 2023-25 | 9.9237 | 7.2431 | 10.1156 | 0.21637 | 39-21 | +15.9 | 76-60 | 77-52 | 20-4 | 10.1794 |
| V3 defense ridge 32 | 2015-18 | 9.9516 | 7.3989 | 10.7484 | 0.21516 | 67-52 | +9.8 | 134-113 | 119-97 | 23-12 | 10.2583 |
| V3 defense ridge 32 | 2019-22 | 10.0077 | 7.3740 | 10.5357 | 0.21736 | 80-52 | +22.8 | 171-142 | 143-88 | 17-12 | 9.3506 |
| V3 defense ridge 32 | 2023-25 | 9.9030 | 7.2358 | 10.1063 | 0.21591 | 36-18 | +16.2 | 77-55 | 77-52 | 19-5 | 10.1930 |
| V4 defense last season x0.5 | 2015-18 | 9.9595 | 7.4125 | 10.7707 | 0.21526 | 63-55 | +2.5 | 130-110 | 119-97 | 19-13 | 10.2672 |
| V4 defense last season x0.5 | 2019-22 | 10.0086 | 7.3743 | 10.5373 | 0.21767 | 80-54 | +20.6 | 173-136 | 143-88 | 17-14 | 9.3673 |
| V4 defense last season x0.5 | 2023-25 | 9.8994 | 7.2392 | 10.1132 | 0.21581 | 37-21 | +13.9 | 78-55 | 77-52 | 18-5 | 10.2190 |
| V5 games weighted by plays (per-play stats) | 2015-18 | 9.9548 | 7.3931 | 10.7389 | 0.21515 | 69-55 | +8.5 | 133-107 | 119-97 | 24-12 | 10.2689 |
| V5 games weighted by plays (per-play stats) | 2019-22 | 10.0070 | 7.3735 | 10.5368 | 0.21728 | 78-47 | +26.3 | 177-141 | 143-88 | 17-11 | 9.3628 |
| V5 games weighted by plays (per-play stats) | 2023-25 | 9.9055 | 7.2347 | 10.1076 | 0.21603 | 38-20 | +16.0 | 75-53 | 77-52 | 19-5 | 10.1823 |
| V6 early-down EPA as the EPA rating | 2015-18 | 9.9504 | 7.3883 | 10.7897 | 0.21529 | 60-55 | -0.5 | 138-117 | 119-97 | 24-12 | 10.2388 |
| V6 early-down EPA as the EPA rating | 2019-22 | 10.0103 | 7.3663 | 10.5348 | 0.21732 | 79-54 | +19.6 | 174-133 | 143-88 | 16-14 | 9.3585 |
| V6 early-down EPA as the EPA rating | 2023-25 | 9.8992 | 7.2299 | 10.0967 | 0.21580 | 33-20 | +11.0 | 77-52 | 77-52 | 18-5 | 10.1793 |
| V7 garbage-time plays at half weight | 2015-18 | 9.9495 | 7.3970 | 10.7490 | 0.21512 | 69-57 | +6.3 | 128-113 | 119-97 | 22-13 | 10.2488 |
| V7 garbage-time plays at half weight | 2019-22 | 10.0042 | 7.3692 | 10.5344 | 0.21713 | 78-50 | +23.0 | 177-141 | 143-88 | 18-11 | 9.3531 |
| V7 garbage-time plays at half weight | 2023-25 | 9.8975 | 7.2379 | 10.1094 | 0.21572 | 36-19 | +15.1 | 72-56 | 77-52 | 19-5 | 10.1873 |
| V8 per-play stats decay 0.96 | 2015-18 | 9.9499 | 7.3926 | 10.7377 | 0.21531 | 71-55 | +10.5 | 130-112 | 119-97 | 23-12 | 10.2602 |
| V8 per-play stats decay 0.96 | 2019-22 | 10.0152 | 7.3780 | 10.5422 | 0.21738 | 80-48 | +27.2 | 174-142 | 143-88 | 17-11 | 9.3749 |
| V8 per-play stats decay 0.96 | 2023-25 | 9.9059 | 7.2384 | 10.1014 | 0.21610 | 36-21 | +12.9 | 74-54 | 77-52 | 18-5 | 10.1757 |

## Gate, V1 last season weighted by roster continuity (parts 1 and 2; the placebo runs only for a variant that passes them)

| Check | Passes | Detail |
|---|---|---|
| margin: better on 2015-18 | NO | miss 9.9469 -> 9.9609 |
| margin: better on 2019-22 | yes | miss 10.0108 -> 10.0047 |
| margin: better on 2023-25 | yes | miss 9.9070 -> 9.8966 |
| margin: no bet cost: spread flag, 2015-18 | yes | 68-57 -> 67-55 |
| margin: no bet cost: totals flag, 2015-18 | NO | 132-111 -> 131-116 |
| margin: no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| margin: no bet cost: spread flag, 2019-22 | yes | 78-49 -> 80-51 |
| margin: no bet cost: totals flag, 2019-22 | NO | 175-140 -> 178-145 |
| margin: no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| margin: no bet cost: spread flag, 2023-25 | NO | 37-19 -> 37-20 |
| margin: no bet cost: totals flag, 2023-25 | yes | 76-55 -> 77-55 |
| margin: no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |
| margin: calibration not worse, 2015-18 | NO | 0.2150 -> 0.2156 |
| margin: calibration not worse, 2019-22 | yes | 0.2174 -> 0.2174 |
| margin: calibration not worse, 2023-25 | yes | 0.2161 -> 0.2155 |
| team points: better on 2015-18 | NO | miss 7.3995 -> 7.4037 |
| team points: better on 2019-22 | yes | miss 7.3735 -> 7.3735 |
| team points: better on 2023-25 | yes | miss 7.2356 -> 7.2318 |

Gate: FAIL (12 of 18); no market input and no look-ahead checked by the model-auditor agent

## Gate, V2 games with another QB at half weight (parts 1 and 2; the placebo runs only for a variant that passes them)

| Check | Passes | Detail |
|---|---|---|
| margin: better on 2015-18 | NO | miss 9.9469 -> 9.9533 |
| margin: better on 2019-22 | NO | miss 10.0108 -> 10.0142 |
| margin: better on 2023-25 | NO | miss 9.9070 -> 9.9237 |
| margin: no bet cost: spread flag, 2015-18 | NO | 68-57 -> 62-60 |
| margin: no bet cost: totals flag, 2015-18 | yes | 132-111 -> 130-108 |
| margin: no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| margin: no bet cost: spread flag, 2019-22 | NO | 78-49 -> 80-52 |
| margin: no bet cost: totals flag, 2019-22 | yes | 175-140 -> 180-144 |
| margin: no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| margin: no bet cost: spread flag, 2023-25 | yes | 37-19 -> 39-21 |
| margin: no bet cost: totals flag, 2023-25 | NO | 76-55 -> 76-60 |
| margin: no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |
| margin: calibration not worse, 2015-18 | yes | 0.2150 -> 0.2150 |
| margin: calibration not worse, 2019-22 | NO | 0.2174 -> 0.2175 |
| margin: calibration not worse, 2023-25 | NO | 0.2161 -> 0.2164 |
| team points: better on 2015-18 | yes | miss 7.3995 -> 7.3983 |
| team points: better on 2019-22 | NO | miss 7.3735 -> 7.3776 |
| team points: better on 2023-25 | NO | miss 7.2356 -> 7.2431 |

Gate: FAIL (8 of 18); no market input and no look-ahead checked by the model-auditor agent

## Gate, V3 defense ridge 32 (parts 1 and 2; the placebo runs only for a variant that passes them)

| Check | Passes | Detail |
|---|---|---|
| margin: better on 2015-18 | NO | miss 9.9469 -> 9.9516 |
| margin: better on 2019-22 | yes | miss 10.0108 -> 10.0077 |
| margin: better on 2023-25 | yes | miss 9.9070 -> 9.9030 |
| margin: no bet cost: spread flag, 2015-18 | yes | 68-57 -> 67-52 |
| margin: no bet cost: totals flag, 2015-18 | yes | 132-111 -> 134-113 |
| margin: no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| margin: no bet cost: spread flag, 2019-22 | NO | 78-49 -> 80-52 |
| margin: no bet cost: totals flag, 2019-22 | NO | 175-140 -> 171-142 |
| margin: no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| margin: no bet cost: spread flag, 2023-25 | yes | 37-19 -> 36-18 |
| margin: no bet cost: totals flag, 2023-25 | yes | 76-55 -> 77-55 |
| margin: no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |
| margin: calibration not worse, 2015-18 | NO | 0.2150 -> 0.2152 |
| margin: calibration not worse, 2019-22 | yes | 0.2174 -> 0.2174 |
| margin: calibration not worse, 2023-25 | yes | 0.2161 -> 0.2159 |
| team points: better on 2015-18 | yes | miss 7.3995 -> 7.3989 |
| team points: better on 2019-22 | NO | miss 7.3735 -> 7.3740 |
| team points: better on 2023-25 | NO | miss 7.2356 -> 7.2358 |

Gate: FAIL (12 of 18); no market input and no look-ahead checked by the model-auditor agent

## Gate, V4 defense last season x0.5 (parts 1 and 2; the placebo runs only for a variant that passes them)

| Check | Passes | Detail |
|---|---|---|
| margin: better on 2015-18 | NO | miss 9.9469 -> 9.9595 |
| margin: better on 2019-22 | yes | miss 10.0108 -> 10.0086 |
| margin: better on 2023-25 | yes | miss 9.9070 -> 9.8994 |
| margin: no bet cost: spread flag, 2015-18 | NO | 68-57 -> 63-55 |
| margin: no bet cost: totals flag, 2015-18 | NO | 132-111 -> 130-110 |
| margin: no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| margin: no bet cost: spread flag, 2019-22 | NO | 78-49 -> 80-54 |
| margin: no bet cost: totals flag, 2019-22 | yes | 175-140 -> 173-136 |
| margin: no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| margin: no bet cost: spread flag, 2023-25 | NO | 37-19 -> 37-21 |
| margin: no bet cost: totals flag, 2023-25 | yes | 76-55 -> 78-55 |
| margin: no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |
| margin: calibration not worse, 2015-18 | NO | 0.2150 -> 0.2153 |
| margin: calibration not worse, 2019-22 | NO | 0.2174 -> 0.2177 |
| margin: calibration not worse, 2023-25 | yes | 0.2161 -> 0.2158 |
| team points: better on 2015-18 | NO | miss 7.3995 -> 7.4125 |
| team points: better on 2019-22 | NO | miss 7.3735 -> 7.3743 |
| team points: better on 2023-25 | NO | miss 7.2356 -> 7.2392 |

Gate: FAIL (8 of 18); no market input and no look-ahead checked by the model-auditor agent

## Gate, V5 games weighted by plays (per-play stats) (parts 1 and 2; the placebo runs only for a variant that passes them)

| Check | Passes | Detail |
|---|---|---|
| margin: better on 2015-18 | NO | miss 9.9469 -> 9.9548 |
| margin: better on 2019-22 | yes | miss 10.0108 -> 10.0070 |
| margin: better on 2023-25 | yes | miss 9.9070 -> 9.9055 |
| margin: no bet cost: spread flag, 2015-18 | yes | 68-57 -> 69-55 |
| margin: no bet cost: totals flag, 2015-18 | yes | 132-111 -> 133-107 |
| margin: no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| margin: no bet cost: spread flag, 2019-22 | yes | 78-49 -> 78-47 |
| margin: no bet cost: totals flag, 2019-22 | yes | 175-140 -> 177-141 |
| margin: no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| margin: no bet cost: spread flag, 2023-25 | yes | 37-19 -> 38-20 |
| margin: no bet cost: totals flag, 2023-25 | yes | 76-55 -> 75-53 |
| margin: no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |
| margin: calibration not worse, 2015-18 | NO | 0.2150 -> 0.2152 |
| margin: calibration not worse, 2019-22 | yes | 0.2174 -> 0.2173 |
| margin: calibration not worse, 2023-25 | yes | 0.2161 -> 0.2160 |
| team points: better on 2015-18 | yes | miss 7.3995 -> 7.3931 |
| team points: better on 2019-22 | yes | miss 7.3735 -> 7.3735 |
| team points: better on 2023-25 | yes | miss 7.2356 -> 7.2347 |

Gate: FAIL (16 of 18); no market input and no look-ahead checked by the model-auditor agent

## Gate, V6 early-down EPA as the EPA rating (parts 1 and 2; the placebo runs only for a variant that passes them)

| Check | Passes | Detail |
|---|---|---|
| margin: better on 2015-18 | NO | miss 9.9469 -> 9.9504 |
| margin: better on 2019-22 | yes | miss 10.0108 -> 10.0103 |
| margin: better on 2023-25 | yes | miss 9.9070 -> 9.8992 |
| margin: no bet cost: spread flag, 2015-18 | NO | 68-57 -> 60-55 |
| margin: no bet cost: totals flag, 2015-18 | yes | 132-111 -> 138-117 |
| margin: no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| margin: no bet cost: spread flag, 2019-22 | NO | 78-49 -> 79-54 |
| margin: no bet cost: totals flag, 2019-22 | yes | 175-140 -> 174-133 |
| margin: no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| margin: no bet cost: spread flag, 2023-25 | NO | 37-19 -> 33-20 |
| margin: no bet cost: totals flag, 2023-25 | yes | 76-55 -> 77-52 |
| margin: no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |
| margin: calibration not worse, 2015-18 | NO | 0.2150 -> 0.2153 |
| margin: calibration not worse, 2019-22 | yes | 0.2174 -> 0.2173 |
| margin: calibration not worse, 2023-25 | yes | 0.2161 -> 0.2158 |
| team points: better on 2015-18 | yes | miss 7.3995 -> 7.3883 |
| team points: better on 2019-22 | yes | miss 7.3735 -> 7.3663 |
| team points: better on 2023-25 | yes | miss 7.2356 -> 7.2299 |

Gate: FAIL (13 of 18); no market input and no look-ahead checked by the model-auditor agent

## Gate, V7 garbage-time plays at half weight (parts 1 and 2; the placebo runs only for a variant that passes them)

| Check | Passes | Detail |
|---|---|---|
| margin: better on 2015-18 | NO | miss 9.9469 -> 9.9495 |
| margin: better on 2019-22 | yes | miss 10.0108 -> 10.0042 |
| margin: better on 2023-25 | yes | miss 9.9070 -> 9.8975 |
| margin: no bet cost: spread flag, 2015-18 | yes | 68-57 -> 69-57 |
| margin: no bet cost: totals flag, 2015-18 | NO | 132-111 -> 128-113 |
| margin: no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| margin: no bet cost: spread flag, 2019-22 | NO | 78-49 -> 78-50 |
| margin: no bet cost: totals flag, 2019-22 | yes | 175-140 -> 177-141 |
| margin: no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| margin: no bet cost: spread flag, 2023-25 | NO | 37-19 -> 36-19 |
| margin: no bet cost: totals flag, 2023-25 | NO | 76-55 -> 72-56 |
| margin: no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |
| margin: calibration not worse, 2015-18 | NO | 0.2150 -> 0.2151 |
| margin: calibration not worse, 2019-22 | yes | 0.2174 -> 0.2171 |
| margin: calibration not worse, 2023-25 | yes | 0.2161 -> 0.2157 |
| team points: better on 2015-18 | yes | miss 7.3995 -> 7.3970 |
| team points: better on 2019-22 | yes | miss 7.3735 -> 7.3692 |
| team points: better on 2023-25 | NO | miss 7.2356 -> 7.2379 |

Gate: FAIL (11 of 18); no market input and no look-ahead checked by the model-auditor agent

## Gate, V8 per-play stats decay 0.96 (parts 1 and 2; the placebo runs only for a variant that passes them)

| Check | Passes | Detail |
|---|---|---|
| margin: better on 2015-18 | NO | miss 9.9469 -> 9.9499 |
| margin: better on 2019-22 | NO | miss 10.0108 -> 10.0152 |
| margin: better on 2023-25 | yes | miss 9.9070 -> 9.9059 |
| margin: no bet cost: spread flag, 2015-18 | yes | 68-57 -> 71-55 |
| margin: no bet cost: totals flag, 2015-18 | NO | 132-111 -> 130-112 |
| margin: no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| margin: no bet cost: spread flag, 2019-22 | yes | 78-49 -> 80-48 |
| margin: no bet cost: totals flag, 2019-22 | NO | 175-140 -> 174-142 |
| margin: no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| margin: no bet cost: spread flag, 2023-25 | NO | 37-19 -> 36-21 |
| margin: no bet cost: totals flag, 2023-25 | NO | 76-55 -> 74-54 |
| margin: no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |
| margin: calibration not worse, 2015-18 | NO | 0.2150 -> 0.2153 |
| margin: calibration not worse, 2019-22 | yes | 0.2174 -> 0.2174 |
| margin: calibration not worse, 2023-25 | NO | 0.2161 -> 0.2161 |
| team points: better on 2015-18 | yes | miss 7.3995 -> 7.3926 |
| team points: better on 2019-22 | NO | miss 7.3735 -> 7.3780 |
| team points: better on 2023-25 | NO | miss 7.2356 -> 7.2384 |

Gate: FAIL (8 of 18); no market input and no look-ahead checked by the model-auditor agent

## Count, audit and decision

**Count.** Eight variants, all pre-registered, none added after the results. With the earlier rating-construction
studies (about 80 settings: tuning_ratings 35, retune / retune2, sweep_all, season_fade 8, luck 2, team_signals a4 2)
this is at least the seventh round on how the ratings are built. No variant was picked on 2023-25.

**Corrections to the pre-registration** (found by the fact check after the results; the variants and the bar are
unchanged): the earlier-studies list left out the 21 Sep 2026 grid (reports/tuning_ratings.csv, 35 settings), and
early-down EPA was in the lab correlation table already (reports/lab.md: 0.45 against 0.50 for EPA per play), though
never in the model. V6's "common finding that early downs carry the signal" has no source here, and our own lab table
points the other way. V2's QB for a played game is the schedule's starter after `build.fix_starters` (the QB who
dropped back), the same QB the live QB rating prices in the backtest; live, it is the named starter. V1 reads each
team's week-1 continuity only (the code's review caught an earlier version taking the first game with a value, which
used a week-2 roster for MIA and TB in 2017; the numbers above are from the rerun on the fixed code and main's data of 3 Oct 2026; every conclusion held).

**Result.** None passes. Every variant misses the margin worse on 2015-18, the window nobody tuned on (live 9.9469;
variants 9.9495 to 9.9609), so each fails part 1. Seven of eight lower the margin miss on 2023-25 (best V1 9.8966
against 9.9070) and six on 2019-22, consistent with changes that fit recent seasons and not older ones. Two came
closest. V5 (games weighted by plays) passes 16 of 18 checks: spread flag 69-55 / 78-47 / 38-20 against 68-57 / 78-49 /
37-19 (wins minus losses +3, +2, 0, inside the noise), totals flag and wind under no worse, team points lower on all
three windows, but margin 9.9548 against 9.9469 on 2015-18 and the Brier score worse there (0.21515 against 0.21504).
V6 (early-down EPA) lowers the team points miss on all three windows (7.3883 / 7.3663 / 7.2299 against 7.3995 / 7.3735
/ 7.2356) but misses the margin worse on 2015-18 and has a worse spread-flag record on all three (60-55 / 79-54 / 33-20).

**Placebo, together test, audit.** The placebo runs only for a variant that passes parts 1 and 2, the together test
only for passers, and the model-auditor before asking Matt to adopt something: none passed, so none of the three ran.

**Decision.** No change. The live ratings (decay 0.94, last season x0.8, ridge 16 on both sides, equal game weights,
all plays) stay. Nothing goes to a shadow: these are rating constructions, not bet rules, and none is close enough on
every window to justify a second live model.
