# Old ideas retested on the honest backtest (3 Oct 2026)

**Claim.** Some ideas rejected before the backtest was fixed on 1-2 Oct 2026 would pass now. Matt (3 Oct 2026): test old
ideas again "from everything we have learned". The fixes that could change an old verdict: the wrong starting QB in 44
team-games 2022-25 (#381, `build.fix_starters`); linemen matched by name until 24 Sep (`ids.pfr_ids`); the referee prior's
same-game leak (#384, it sat in the totals equation of every totals test from 28 Sep to 2 Oct); recorded instead of
forecast weather in the priced games (#389, #398, 2015-17 forecasts added the same day); games abroad placed at the home
team's US stadium or under a dome (`venues.py`); schedule wind typos (`build.fix_wind`).

Script: `experiments/old_ideas_retest.py`. Full table: `reports/old_ideas_retest.csv`.

## Step 1: every model-input and bet-rule idea not adopted (from reports/decision_log.md and round 3)

(a) = rejected narrowly (one window, one bet or the placebo by a few draws). (b) = its test used one of the flawed inputs
above (on its own data, or on a base model that carried them). Market inputs (ATS records, the line, the referee's over
rate against the closing total, splits, prices) are excluded as model inputs. Rules already tracked as shadows
(`picks.SHADOWS`) are listed but not re-picked: a passing bet rule could only become the shadow it already is.
Margins are idea minus base, per window 2015-18 / 2019-22 / 2023-25 unless two windows are named (2019-22 / 2023-25).

| Date | Idea (study) | Original verdict and margin | (a) | (b) | Retest |
|---|---|---|---|---|---|
| 2 Oct | Questionable in the totals equation T1, T2 (questionable_totals) | total miss worse 2015-18 (T2 +0.049) | no | no (honest backtest) | no: hidden shadow `shadowqtotals` |
| 2 Oct | Over corrections M1 linear, M2 bands (overs_deep) | M1 worse 2019-22 (+0.065) and 2023-25; M2 worse 2019-22, 2023-25 | no | no | no |
| 2 Oct | Wind curve: isotonic C1, bands 0/8/10/15 C2 (forecast_weather_backtest) | C1 worse 2019-22, C2 worse 2023-25 | no | no | no |
| 2 Oct | Not-added shadows: rain 70+, Under 4+, blind prime-time unders, favourite teaser legs (more_shadows) | subsets or losing | no | no | no |
| 1 Oct | Questionable skill players at the chance they sit Q1 (injury_retest) | team miss worse 2015-18 (+0.0052), 2023-25 (+0.0033) | no | yes | no |
| 1 Oct | Questionable at every position Q2 (injury_retest) | miss better all three; spread flag net -4 / -8 / -8 | no | yes | no (its totals form is a shadow) |
| 1 Oct | Linemen's value out L1 (injury_retest) | worse 2015-18 (+0.019), 2023-25 (+0.003) | no | yes | no |
| 1 Oct | Opponent defenders' value out D1 (injury_retest) | team miss worse 2015-18 only (+0.0037), better 2019-22 (-0.0054), 2023-25 (-0.0016); spread flag 80-51 -> 77-49 on 2019-22 | yes | yes | **V8** |
| 1 Oct | Q2 + D1 together C (injury_retest) | spread flag worse 2019-22, 2023-25 | no | yes | no |
| 1 Oct | Wind learned from the forecast W (forecast_weather_inputs) | worse 2015-18 (+0.0043), 2023-25 (+0.0032); flags cost 2015-18 | yes (small) | yes (tested before played games were priced on forecasts) | **V10** |
| 1 Oct | Cold learned from the forecast C, and W+C (forecast_weather_inputs) | C worse on every window | no | yes | no |
| 1 Oct | Rain-chance bands on the total, last run and day-before (weather_forecast_retest) | worse 2019-22 (+0.015); placebo 11 of 50 | no | yes | no (rain is in the total since 1 Oct) |
| 1 Oct | Temperature bands on the total, last run (weather_forecast_retest) | worse 2023-25 (+0.002); placebo 28 of 50 | yes | yes | no (the day-before form is the nearer miss) |
| 1 Oct | Temperature bands on the total, day-before run (weather_forecast_retest) | better both scored windows (-0.027 / -0.010), flags not worse; placebo 44 of 50, one short | yes | yes (leaky referee input in the base; 2015-18 unscored) | **V6** |
| 1 Oct | Rain x wind, cold x wind cells (weather_forecast_retest) | worse 2019-22 (+0.002, +0.024) | rain x wind yes | yes | no (rain x wind: rain now in the total) |
| 1 Oct | Wet or cold band (rain 50+ or below 32 F) (weather_forecast_retest) | better both scored windows (-0.041 / -0.055), placebo 50 of 50; totals flag 2019-22 net 53 -> 48 | yes | yes | **V7** |
| 1 Oct | Gust in the total (friend_ideas) | miss -0.006 each window; placebo 18 of 50; totals flag worse 2015-18, 2019-22 | no | yes (recorded gusts) | no: no live gust source (rule part 4) |
| 1 Oct | Points-per-drive rating (friend_ideas) | never lower on all three; costs flag wins | no | no | no |
| 1 Oct | Blind rain under 70+ (rain_under_retest) | fails 2018 | no | no | no (50+ is a shadow) |
| 30 Sep | Home-side bet rules: home 4.5 / 5 / 6, road only, road 3.5+, lean removed (home_side_rules) | each loses units on 2019-22 | no | no | no (shadows `shadowroad`, `shadowroad6`) |
| 30 Sep | 17 favourite fixes (favorite_review) | none passes rule 1 | no | no | no |
| 30 Sep | Home edge x visitor's travel miles (home_field) | team miss better 2015-18 and 2023-25, better 2019-22 by only 0.0001, margin miss worse on 2019-22 (+0.0034, rule 1 as that study wrote it); calibration and spread cost; informational placebo 9 of 12 beat it | yes | yes (games abroad listed at US stadiums) | **V11** |
| 30 Sep | Home edge x visitor's time-zone change (home_field) | team miss better all three (-0.008 at most); calibration or spread cost; placebo 7 of 20 beat it | yes | yes (as above) | **V12** |
| 30 Sep | Neutral sites: home edge set to zero (home_field) | better 2015-18, 2019-22, worse 2023-25 (+0.0030); spread -1 / -1 / -4 | yes | yes (2025 games abroad not flagged neutral) | **V13** |
| 30 Sep | Neutral own term, Denver, dome home, division home, early/late, cold December, team EB edges, visitor road form, partial pooling (home_field) | fail rule 1 on 1 to 3 windows | no | partly | no |
| 30 Sep | Team ATS corrections, dog and matchup rules (spread_research) | worsen the margin; no rule beats live every window | no | no | no (hook, road dog, small dog are shadows) |
| 30 Sep | Usual snaps out, 10 forms (usual_snaps) | best L4_G4: team miss better all three, placebo 48 of 50; margin +0.007 2019-22, spread flag 59-50 vs 68-54 on 2015-18 | yes | yes (base before #381, #384, #389) | **V9** |
| 30 Sep | 283 bet rules (bet_rules_sweep) | thresholds, weeks, kinds of game: nothing beats live everywhere | no | yes | no (candidates are shadows: weeks 1-3 unders, 6+, weeks 1-4) |
| 29 Sep | Round 3, 121 situational inputs (situational_game): turf points | passes rules 1-2 by 0.001-0.002; placebo 26 of 50 | no | yes | no |
| 29 Sep | Round 3: outdoor team in a dome; home edge in prime time; Thanksgiving; opponent secondary / front-seven out; injuries both teams in the total; referee residual, flags, yards in the total | rule 1 passes, rule 2 fails (spread -10 on 2023-25; -4 / -4; ...) | no | yes | no |
| 29 Sep | Round 3 re-check: drop QB out from the points equation | miss better all three (-0.004 / -0.004 / -0.002), spread +2 / +1 / +2; calibrated log loss +0.0004 on 2019-22 | yes | yes (wrong starters #381) | **V1** |
| 29 Sep | Round 3 re-check: drop cold from the totals equation | total miss better all three (-0.054 / -0.002 / -0.001); totals flag -1 on 2023-25 | yes | yes (cold read recorded weather) | **V2** |
| 29 Sep | Round 3 re-check: drop dome from the totals equation | total miss better all three (-0.007 / -0.009 / -0.005); totals flag -1 on 2019-22 | yes | yes (domes abroad, retractable roofs) | **V3** |
| 29 Sep | Round 3 re-check: drop dome from the points equation | team miss better all three (-0.001 / -0.000 / -0.000); spread -1 and calibrated log loss worse on 2023-25 | yes | yes (as above) | **V4** |
| 29 Sep | Round 3 other re-checks (rain, wind, cold, warm-in-cold, skill value, snaps out, QB out in the total) | dropping is mixed or worse | no | yes | no |
| 29 Sep | Trusting the forecast less, six ways (weather_forecast) | none passed | no | yes | no (superseded by forecast pricing) |
| 28 Sep | Faster season fade x0.65 / x0.5 / ... (season_fade) | weeks 1-4 miss worse all three | no | no | no |
| 28 Sep | Key numbers in the teaser chance; moneyline value | worse 2016-18, 2019-22; loses | no | no | no |
| 27 Sep | Home field by recent seasons A / A2 / B / C / D (home_field_recency) | mixed miss, flags lose a window | no | yes | no |
| 25 Sep | QB form in the points equation, k 50 / 100 / 200, +opponent (qb_form) | k100: team miss better all three (7.378 / 7.337 / 7.250 vs 7.397 / 7.344 / 7.274); 4+ flag 66-53 vs 81-55 on 2019-22 | yes (rule 1 passes) | yes (wrong starters #381, the input is the starter's form) | **V5** |
| 25 Sep | New QB, new coach, line returning early (team_signals a3) | worse both windows | no | yes | no |
| 25 Sep | Pass/rush split, success rate (team_signals a4) | team miss worse 2019-22 (+0.007, +0.012) | no | no | no (both sit in the blend) |
| 25 Sep | 17 signal families (new_signals): clutch, explosive plays, penalties, 4th downs, altitude, revenge, tempo... | none better on all three; explosive: margin better, team miss worse on two | no | no | no |
| 25 Sep | Value-weighted offseason turnover (value_turnover) | margin worse 2015-18, 2019-22 | no | no | no |
| 25 Sep | Cover-chance flag; moneyline on the flag's side (bet_rules2) | worse two windows; better one | no | no | no |
| 25 Sep | Every knob re-swept (sweep_all): last season 0.65, +QB shrink 100, decay, windows, ridge, blend weights | best within noise; 0.65 loses bets | no | yes | no |
| 25 Sep | Totals by pace, efficiency, availability, trees, blends (bet_wins, totals_fix) | no totals rule wins every window | no | yes | no |
| 24 Sep | Huber loss (robust_loss) | points better both, spread miss worse 2019-22 | yes (two windows) | yes | no (structural, pre-blend harness) |
| 24 Sep | Defender value as a game input (def_value) | worse both windows | no | yes (ids fixed that day) | no (D1 is its retest) |
| 24 Sep | Opponent-adjusted player values in the model (opp_adjust_model) | no difference | no | no | no |
| 23 Sep | Recency weights, margin direct, QB adjusted for defenses, new coach, QB change early, value retained, home x division, home x short week, QB designed runs, sacks, turnover in total, sigma by total, clipped / turnover-neutral EPA, rest pairs, rest difference, turf, record so far, ridge, dead team 30%, rolling window, trees alone, non-sack QB rating, kickoff-hour weather, usage windows, scheme inputs, scheme QB / totals, skill out x matchup | one window each way or worse on both | no | some (weather, linemen) | no |
| 23 Sep | QB shrinkage 80 dropbacks (qb_k) | team miss -0.0009 / -0.0010, spread miss better both: rejected by the old 0.001 bar | yes | yes | no (needs the ratings rebuilt; sweep_all found 100 cost bets) |
| 23 Sep | Cold cutoff 30 / 40 / 45 F (weather_knobs) | worse both (+0.004 to +0.012) | no | yes | no |
| 23 Sep | Player model in the total: skill value, snaps out, turnover (totals_players) | worse both (+0.004 to +0.023) | no | yes (linemen by name) | no |
| 23 Sep | Training from 2015 (history_depth) | better both windows | yes | no | no (cannot price 2015-18) |
| 22 Sep | Learn from misses; starter share weights; division / skill value in the total; own and opponent defenders, linemen on/off, availability-weighted (positions); kicker, team special teams, punter; QB draft prior; total gap and pace; roof split; mismatch; 32 team home edges; climate pairs; snow, travel (additions, combo) | one window each way or worse | no | some (linemen by name) | no (positions' defenders: D1 is their retest) |
| 21 Sep | Starters-out count; referee tendencies; home/away split; cold and windy team form; late slot, West Coast, off a loss | inside noise or worse (one window scored) | no | cold/windy team form (recorded weather) | no |
| 23-27 Sep | Player props rounds 1-17 inputs not adopted (coverage, routes, coach, matchup history, position, momentum, per-tier factors...) | worse or within noise | no | no | no (the props model; none of the fixes touch it) |
| 24-25 Sep | Season totals: games played, rest-of-season rate, game by game, preseason breakouts | not better on both windows | no | no | no (season model) |

Excluded as market inputs: head-to-head, coach and QB ATS records (cover margins against the spread), the referee's over
rate (against the closing total), the line or the market total as inputs, opener and splits rules.

## Step 2: pre-registration (written before any rerun)

Thirteen ideas, one variant each, each **as originally specified** (no cutoff, band, weight or k changed), on main's
honest backtest (c1e38081, the weekly run of 3 Oct 2026: fixed starters, ids, venues, wind; forecast pricing 2015-2025;
no referee input):

| Variant | Idea | Equation | What changes | Yardstick |
|---|---|---|---|---|
| V1 | Drop QB out | points | `qb_out` removed from `model.FEATS` | team points miss |
| V2 | Drop cold | total | `cold` removed from `model.TOTAL_FEATS` | total miss |
| V3 | Drop dome | total | `dome` removed from `model.TOTAL_FEATS` | total miss |
| V4 | Drop dome | points | `dome` removed from `model.FEATS` | team points miss |
| V5 | QB form in the points equation | points | `qb_form` (k = 100, the live `QB_FORM_K`) added to `FEATS` | team points miss |
| V6 | Temperature bands, day-before GFS run | on the total | bands <32, 32-45, 45+ F on `gfs_temp_d1`, each band's mean miss against all earlier seasons' forecast games, shrunk by K = 50, added to the total (team points +half each) | total miss |
| V7 | Wet or cold | on the total | one band: rain chance 50+ or below 32 F (last run before kickoff, else day-before), K = 50, as V6 | total miss |
| V8 | Opponent defenders' value out | points | `opp_def_value_out` (injury_retest's build: role recipes against replacement, PFR 2018 on, zero before) added | team points miss |
| V9 | Usual snaps out (L4_G4) | points | `off_snap_out` and `def_snap_out` (so `opp_def_snap_out`) = each out player's mean share over his last 4 games played, only if he played in one of the team's last 4 (usual_snaps' build) | team points miss |
| V10 | Wind learned from the forecast (W) | both | a played game's `wind` = the stored forecast reading (`model._wind_readings`) where one exists, for training as well as pricing | team points miss |
| V11 | Home edge x visitor's travel miles | points | signed column (+v home row, -v visitor row, 0 at neutral sites): miles / 1000 from the visitor's usual home stadium to the game's stadium (home_field's definition, on today's venues) | team points miss |
| V12 | Home edge x visitor's time-zone change | points | the same with the absolute time-zone difference | team points miss |
| V13 | Neutral sites: home edge zero | points | `home` replaced by `home x (not neutral)` | team points miss |

**Data and timing.** Every input is as of before the game and already pulled by the weekly run: the forecast history
(`data/weather/forecast_history.csv`, runs 5+ hours before kickoff), the injury report and rosters as the live model reads
them, last games' snap counts, PFR defender charting through the week before, the schedule's venue (fixed by `venues.py`).
No line, split or price is an input. V6 and V7: the band amounts are learned walk-forward from earlier seasons' regular-
season forecast games only (the history now starts in 2015, so 2016 is the first season with amounts; 2015-18 is scored
on 2016-18). V8 and V9 need the league injury files and snap counts 2012-2025, pulled locally with `nflmodel.pull`.

**Pass bar** (`reports/round3_rule.md`, `nflmodel.study_gate.gate`). Windows 2015-18, 2019-22, 2023-25, regular season:
1. the yardstick lower on every window;
2. no bet cost: the spread flag (4+), the totals flag (55%+ under) and the wind under (10+ mph), weeks 1-17, wins minus
   losses not worse on any window; for points-equation variants also the calibrated home win chance's log loss
   (`picks.home_calibrations`, each season's fit from earlier seasons) not worse;
3. beats its placebo: the idea's own values shuffled within season (`study_gate.shuffle_within_season`, fixed seed),
   50 draws, the real gain above the draw's gain in at least 45 of 50 on every window. Run for every variant that passes
   parts 1 and 2 (a variant failing 1 or 2 fails the rule either way). V1-V4 are removals: the kept input is the idea
   being judged, and a removal that is better on every window means the input fails parts 1 and 3 of the rule on its
   own, so the removal is decided by parts 1 and 2 (as ref_tot was on 2 Oct).
4. model-auditor on anything passing 1-3; 5. all passers rerun together, adopted only if the combination passes parts 1
   and 2. Model inputs that pass everything are adopted under Matt's standing approval; a new bet rule would go in as a
   hidden shadow (none is pre-registered here: every bet-rule candidate is already a shadow).

**Like for like.** Every run here (base and variants) fits its boosted trees fresh on this machine and never reads or
writes `data/processed/trees_cache.parquet` (the stored fits come from GitHub's runners; a fresh fit moves the base spread
by about 0.01 points). The base with the stored fits is shown for reference.

**Count.** 13 variants here. Earlier tries of the same ideas: QB out 1 (round 3), cold and dome 3 (round 3 re-checks),
QB form 6 (qb_form), temperature bands 2 and wet-or-cold 1 plus 5 other weather bands (weather_forecast_retest), defender
value out 3 (positions, def_value_out, injury_retest D1), usual snaps 10, wind from the forecast 3, travel / time zones 4
(additions, combo, round 3, home_field), neutral sites 2: about 40 variants of these 13 ideas before this study, and the
decision log holds several hundred model and rule variants in all. The 13 were picked by looking at which earlier
results came close, so a pass here carries that selection: it must clear every part on all three windows, not one.

## Results

Input checks: V8 rebuilt skill value out = live (share within 0.001): 1.0000; V8 rebuilt offensive snaps out = live (share within 0.01): 0.9999; V8 team-games with a defender out valued (2018-25): 4104; V9 'current' off_snap_out = live (share within 1e-6): 0.9909; V9 'current' def_snap_out = live (share within 1e-6): 0.9914; V9 team-games where L4_G4 differs from live: 6554; V9 worst season reproducing the live snaps out, 2015-25: 0.9963; V8 fewest team-games with a defender out valued in a season, 2018-25: 412; V11-V13 neutral games 2015-25: 61; V11-V13 games with no stadium coordinates: 565.

Every run is the live walk-forward 2015-2025 with fresh trees; regular season scored; flags weeks 1-17 at the close; log loss = the calibrated home win chance.

| Variant | Window | Team miss | Total miss | Margin miss | Log loss | Spread flag | Totals flag | Wind under |
|---|---|---|---|---|---|---|---|---|
| base (stored fits, reference) | 2015-18 | 7.3993 | 10.7484 | 9.9471 | 0.61917 | 68-58 | 132-111 | 119-97 |
| base (stored fits, reference) | 2019-22 | 7.3740 | 10.5341 | 10.0116 | 0.62448 | 78-49 | 175-140 | 143-88 |
| base (stored fits, reference) | 2023-25 | 7.2357 | 10.1040 | 9.9069 | 0.62051 | 37-19 | 76-55 | 77-52 |
| base | 2015-18 | 7.3993 | 10.7484 | 9.9467 | 0.61918 | 68-58 | 132-111 | 119-97 |
| base | 2019-22 | 7.3739 | 10.5341 | 10.0118 | 0.62450 | 78-49 | 175-140 | 143-88 |
| base | 2023-25 | 7.2357 | 10.1040 | 9.9072 | 0.62053 | 37-19 | 76-55 | 77-52 |
| V1 | 2015-18 | 7.3956 | 10.7484 | 9.9407 | 0.61814 | 69-55 | 132-111 | 119-97 |
| V1 | 2019-22 | 7.3713 | 10.5341 | 10.0102 | 0.62501 | 79-49 | 175-140 | 143-88 |
| V1 | 2023-25 | 7.2342 | 10.1040 | 9.9008 | 0.62016 | 38-19 | 76-55 | 77-52 |
| V2 | 2015-18 | 7.3737 | 10.6799 | 9.9467 | nan | 68-58 | 126-102 | 119-97 |
| V2 | 2019-22 | 7.3719 | 10.5306 | 10.0118 | nan | 78-49 | 174-141 | 143-88 |
| V2 | 2023-25 | 7.2353 | 10.0992 | 9.9072 | nan | 37-19 | 76-53 | 77-52 |
| V3 | 2015-18 | 7.3971 | 10.7506 | 9.9467 | nan | 68-58 | 131-114 | 119-97 |
| V3 | 2019-22 | 7.3672 | 10.5187 | 10.0118 | nan | 78-49 | 173-141 | 143-88 |
| V3 | 2023-25 | 7.2379 | 10.1104 | 9.9072 | nan | 37-19 | 77-53 | 77-52 |
| V4 | 2015-18 | 7.3991 | 10.7484 | 9.9462 | 0.61915 | 69-54 | 132-111 | 119-97 |
| V4 | 2019-22 | 7.3737 | 10.5341 | 10.0101 | 0.62441 | 77-48 | 175-140 | 143-88 |
| V4 | 2023-25 | 7.2355 | 10.1040 | 9.9076 | 0.62060 | 37-19 | 76-55 | 77-52 |
| V5 | 2015-18 | 7.3953 | 10.7484 | 9.9359 | 0.61735 | 64-48 | 132-111 | 119-97 |
| V5 | 2019-22 | 7.3774 | 10.5341 | 10.0359 | 0.62596 | 59-44 | 175-140 | 143-88 |
| V5 | 2023-25 | 7.2268 | 10.1040 | 9.8855 | 0.62008 | 42-23 | 76-55 | 77-52 |
| V6 | 2015-18 | 7.3943 | 10.7291 | 9.9467 | nan | 68-58 | 123-105 | 119-97 |
| V6 | 2019-22 | 7.3721 | 10.5404 | 10.0118 | nan | 78-49 | 169-136 | 143-88 |
| V6 | 2023-25 | 7.2356 | 10.0886 | 9.9072 | nan | 37-19 | 68-45 | 77-52 |
| V7 | 2015-18 | 7.3874 | 10.7245 | 9.9467 | nan | 68-58 | 124-101 | 119-97 |
| V7 | 2019-22 | 7.3839 | 10.5501 | 10.0118 | nan | 78-49 | 166-134 | 143-88 |
| V7 | 2023-25 | 7.2299 | 10.0808 | 9.9072 | nan | 37-19 | 77-50 | 77-52 |
| V8 | 2015-18 | 7.4025 | 10.7484 | 9.9768 | 0.61836 | 75-59 | 132-111 | 119-97 |
| V8 | 2019-22 | 7.3681 | 10.5341 | 10.0023 | 0.62362 | 77-48 | 175-140 | 143-88 |
| V8 | 2023-25 | 7.2349 | 10.1040 | 9.8981 | 0.62031 | 38-18 | 76-55 | 77-52 |
| V9 | 2015-18 | 7.3795 | 10.7484 | 9.9295 | 0.61808 | 54-53 | 132-111 | 119-97 |
| V9 | 2019-22 | 7.3663 | 10.5341 | 10.0136 | 0.62188 | 80-49 | 175-140 | 143-88 |
| V9 | 2023-25 | 7.2193 | 10.1040 | 9.8827 | 0.61854 | 38-21 | 76-55 | 77-52 |
| V10 | 2015-18 | 7.4024 | 10.7495 | 9.9464 | 0.61954 | 69-56 | 122-107 | 119-97 |
| V10 | 2019-22 | 7.3741 | 10.5368 | 10.0091 | 0.62447 | 81-48 | 171-139 | 143-88 |
| V10 | 2023-25 | 7.2359 | 10.1036 | 9.9092 | 0.62072 | 36-18 | 80-55 | 77-52 |
| V11 | 2015-18 | 7.3975 | 10.7484 | 9.9424 | 0.61961 | 70-53 | 132-111 | 119-97 |
| V11 | 2019-22 | 7.3738 | 10.5341 | 10.0106 | 0.62444 | 81-48 | 175-140 | 143-88 |
| V11 | 2023-25 | 7.2319 | 10.1040 | 9.8957 | 0.61974 | 37-21 | 76-55 | 77-52 |
| V12 | 2015-18 | 7.4004 | 10.7484 | 9.9507 | 0.61988 | 69-54 | 132-111 | 119-97 |
| V12 | 2019-22 | 7.3717 | 10.5341 | 10.0108 | 0.62393 | 83-53 | 175-140 | 143-88 |
| V12 | 2023-25 | 7.2286 | 10.1040 | 9.8986 | 0.61974 | 36-25 | 76-55 | 77-52 |
| V13 | 2015-18 | 7.3983 | 10.7484 | 9.9403 | 0.61945 | 65-55 | 132-111 | 119-97 |
| V13 | 2019-22 | 7.3745 | 10.5341 | 10.0076 | 0.62407 | 78-45 | 175-140 | 143-88 |
| V13 | 2023-25 | 7.2394 | 10.1040 | 9.9239 | 0.62146 | 34-18 | 76-55 | 77-52 |

| Variant | Idea | Parts 1-2 | Placebo | Gate |
|---|---|---|---|---|
| V1 | Drop QB out (points) | fail: calibration not worse, 2019-22 | removal: parts 1-2 decide | FAIL |
| V2 | Drop cold (total) | fail: no bet cost: totals flag, 2019-22 | removal: parts 1-2 decide | FAIL |
| V3 | Drop dome (total) | fail: better on 2015-18, better on 2023-25, no bet cost: totals flag, 2015-18, no bet cost: totals flag, 2019-22 | removal: parts 1-2 decide | FAIL |
| V4 | Drop dome (points) | fail: calibration not worse, 2023-25 | removal: parts 1-2 decide | FAIL |
| V5 | QB form in the points equation | fail: better on 2019-22, no bet cost: spread flag, 2019-22, calibration not worse, 2019-22 | not run (fails 1 or 2) | FAIL |
| V6 | Temperature bands, day-before run | fail: better on 2019-22, no bet cost: totals flag, 2015-18, no bet cost: totals flag, 2019-22 | not run (fails 1 or 2) | FAIL |
| V7 | Wet or cold band | fail: better on 2019-22, no bet cost: totals flag, 2019-22 | not run (fails 1 or 2) | FAIL |
| V8 | Opponent defenders' value out | fail: better on 2015-18 | not run (fails 1 or 2) | FAIL |
| V9 | Usual snaps out (L4_G4) | fail: no bet cost: spread flag, 2015-18, no bet cost: spread flag, 2023-25 | 50 of 50 draws (need 45 of at least 50); 50 of 50 draws (need 45 of at least 50); 50 of 50 draws (need 45 of at least 50) (informational, added after results) | FAIL |
| V10 | Wind learned from the forecast | fail: better on 2015-18, better on 2019-22, better on 2023-25, no bet cost: totals flag, 2015-18, no bet cost: totals flag, 2019-22, calibration not worse, 2015-18, calibration not worse, 2023-25 | not run (fails 1 or 2) | FAIL |
| V11 | Home edge x visitor's travel miles | fail: no bet cost: spread flag, 2023-25, calibration not worse, 2015-18 | not run (fails 1 or 2) | FAIL |
| V12 | Home edge x visitor's time-zone change | fail: better on 2015-18, no bet cost: spread flag, 2023-25, calibration not worse, 2015-18 | not run (fails 1 or 2) | FAIL |
| V13 | Neutral sites: home edge zero | fail: better on 2019-22, better on 2023-25, no bet cost: spread flag, 2023-25, calibration not worse, 2015-18, calibration not worse, 2023-25 | not run (fails 1 or 2) | FAIL |

### Gate, V1: Drop QB out (points) (team points miss)

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | yes | miss 7.3993 -> 7.3956 |
| better on 2019-22 | yes | miss 7.3739 -> 7.3713 |
| better on 2023-25 | yes | miss 7.2357 -> 7.2342 |
| no bet cost: spread flag, 2015-18 | yes | 68-58 -> 69-55 |
| no bet cost: totals flag, 2015-18 | yes | 132-111 -> 132-111 |
| no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| no bet cost: spread flag, 2019-22 | yes | 78-49 -> 79-49 |
| no bet cost: totals flag, 2019-22 | yes | 175-140 -> 175-140 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 37-19 -> 38-19 |
| no bet cost: totals flag, 2023-25 | yes | 76-55 -> 76-55 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |
| calibration not worse, 2015-18 | yes | 0.6192 -> 0.6181 |
| calibration not worse, 2019-22 | NO | 0.6245 -> 0.6250 |
| calibration not worse, 2023-25 | yes | 0.6205 -> 0.6202 |

Gate: FAIL (14 of 15); no market input and no look-ahead checked by the model-auditor agent

### Gate, V2: Drop cold (total) (total miss)

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | yes | miss 10.7484 -> 10.6799 |
| better on 2019-22 | yes | miss 10.5340 -> 10.5306 |
| better on 2023-25 | yes | miss 10.1040 -> 10.0993 |
| no bet cost: spread flag, 2015-18 | yes | 68-58 -> 68-58 |
| no bet cost: totals flag, 2015-18 | yes | 132-111 -> 126-102 |
| no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| no bet cost: spread flag, 2019-22 | yes | 78-49 -> 78-49 |
| no bet cost: totals flag, 2019-22 | NO | 175-140 -> 174-141 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 37-19 -> 37-19 |
| no bet cost: totals flag, 2023-25 | yes | 76-55 -> 76-53 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |

Gate: FAIL (11 of 12); no market input and no look-ahead checked by the model-auditor agent

### Gate, V3: Drop dome (total) (total miss)

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | NO | miss 10.7484 -> 10.7505 |
| better on 2019-22 | yes | miss 10.5340 -> 10.5187 |
| better on 2023-25 | NO | miss 10.1040 -> 10.1104 |
| no bet cost: spread flag, 2015-18 | yes | 68-58 -> 68-58 |
| no bet cost: totals flag, 2015-18 | NO | 132-111 -> 131-114 |
| no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| no bet cost: spread flag, 2019-22 | yes | 78-49 -> 78-49 |
| no bet cost: totals flag, 2019-22 | NO | 175-140 -> 173-141 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 37-19 -> 37-19 |
| no bet cost: totals flag, 2023-25 | yes | 76-55 -> 77-53 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |

Gate: FAIL (8 of 12); no market input and no look-ahead checked by the model-auditor agent

### Gate, V4: Drop dome (points) (team points miss)

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | yes | miss 7.3993 -> 7.3991 |
| better on 2019-22 | yes | miss 7.3739 -> 7.3737 |
| better on 2023-25 | yes | miss 7.2357 -> 7.2355 |
| no bet cost: spread flag, 2015-18 | yes | 68-58 -> 69-54 |
| no bet cost: totals flag, 2015-18 | yes | 132-111 -> 132-111 |
| no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| no bet cost: spread flag, 2019-22 | yes | 78-49 -> 77-48 |
| no bet cost: totals flag, 2019-22 | yes | 175-140 -> 175-140 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 37-19 -> 37-19 |
| no bet cost: totals flag, 2023-25 | yes | 76-55 -> 76-55 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |
| calibration not worse, 2015-18 | yes | 0.6192 -> 0.6192 |
| calibration not worse, 2019-22 | yes | 0.6245 -> 0.6244 |
| calibration not worse, 2023-25 | NO | 0.6205 -> 0.6206 |

Gate: FAIL (14 of 15); no market input and no look-ahead checked by the model-auditor agent

### Gate, V5: QB form in the points equation (team points miss)

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | yes | miss 7.3993 -> 7.3953 |
| better on 2019-22 | NO | miss 7.3739 -> 7.3774 |
| better on 2023-25 | yes | miss 7.2357 -> 7.2268 |
| no bet cost: spread flag, 2015-18 | yes | 68-58 -> 64-48 |
| no bet cost: totals flag, 2015-18 | yes | 132-111 -> 132-111 |
| no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| no bet cost: spread flag, 2019-22 | NO | 78-49 -> 59-44 |
| no bet cost: totals flag, 2019-22 | yes | 175-140 -> 175-140 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 37-19 -> 42-23 |
| no bet cost: totals flag, 2023-25 | yes | 76-55 -> 76-55 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |
| calibration not worse, 2015-18 | yes | 0.6192 -> 0.6173 |
| calibration not worse, 2019-22 | NO | 0.6245 -> 0.6260 |
| calibration not worse, 2023-25 | yes | 0.6205 -> 0.6201 |

Gate: FAIL (12 of 15); no market input and no look-ahead checked by the model-auditor agent

### Gate, V6: Temperature bands, day-before run (total miss)

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | yes | miss 10.7484 -> 10.7291 |
| better on 2019-22 | NO | miss 10.5340 -> 10.5404 |
| better on 2023-25 | yes | miss 10.1040 -> 10.0886 |
| no bet cost: spread flag, 2015-18 | yes | 68-58 -> 68-58 |
| no bet cost: totals flag, 2015-18 | NO | 132-111 -> 123-105 |
| no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| no bet cost: spread flag, 2019-22 | yes | 78-49 -> 78-49 |
| no bet cost: totals flag, 2019-22 | NO | 175-140 -> 169-136 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 37-19 -> 37-19 |
| no bet cost: totals flag, 2023-25 | yes | 76-55 -> 68-45 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |

Gate: FAIL (9 of 12); no market input and no look-ahead checked by the model-auditor agent

### Gate, V7: Wet or cold band (total miss)

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | yes | miss 10.7484 -> 10.7245 |
| better on 2019-22 | NO | miss 10.5340 -> 10.5501 |
| better on 2023-25 | yes | miss 10.1040 -> 10.0808 |
| no bet cost: spread flag, 2015-18 | yes | 68-58 -> 68-58 |
| no bet cost: totals flag, 2015-18 | yes | 132-111 -> 124-101 |
| no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| no bet cost: spread flag, 2019-22 | yes | 78-49 -> 78-49 |
| no bet cost: totals flag, 2019-22 | NO | 175-140 -> 166-134 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 37-19 -> 37-19 |
| no bet cost: totals flag, 2023-25 | yes | 76-55 -> 77-50 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |

Gate: FAIL (10 of 12); no market input and no look-ahead checked by the model-auditor agent

### Gate, V8: Opponent defenders' value out (team points miss)

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | NO | miss 7.3993 -> 7.4026 |
| better on 2019-22 | yes | miss 7.3739 -> 7.3681 |
| better on 2023-25 | yes | miss 7.2357 -> 7.2349 |
| no bet cost: spread flag, 2015-18 | yes | 68-58 -> 75-59 |
| no bet cost: totals flag, 2015-18 | yes | 132-111 -> 132-111 |
| no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| no bet cost: spread flag, 2019-22 | yes | 78-49 -> 77-48 |
| no bet cost: totals flag, 2019-22 | yes | 175-140 -> 175-140 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 37-19 -> 38-18 |
| no bet cost: totals flag, 2023-25 | yes | 76-55 -> 76-55 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |
| calibration not worse, 2015-18 | yes | 0.6192 -> 0.6184 |
| calibration not worse, 2019-22 | yes | 0.6245 -> 0.6236 |
| calibration not worse, 2023-25 | yes | 0.6205 -> 0.6203 |

Gate: FAIL (14 of 15); no market input and no look-ahead checked by the model-auditor agent

### Gate, V9: Usual snaps out (L4_G4) (team points miss)

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | yes | miss 7.3993 -> 7.3795 |
| better on 2019-22 | yes | miss 7.3739 -> 7.3664 |
| better on 2023-25 | yes | miss 7.2357 -> 7.2193 |
| no bet cost: spread flag, 2015-18 | NO | 68-58 -> 54-53 |
| no bet cost: totals flag, 2015-18 | yes | 132-111 -> 132-111 |
| no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| no bet cost: spread flag, 2019-22 | yes | 78-49 -> 80-49 |
| no bet cost: totals flag, 2019-22 | yes | 175-140 -> 175-140 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | NO | 37-19 -> 38-21 |
| no bet cost: totals flag, 2023-25 | yes | 76-55 -> 76-55 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |
| calibration not worse, 2015-18 | yes | 0.6192 -> 0.6181 |
| calibration not worse, 2019-22 | yes | 0.6245 -> 0.6219 |
| calibration not worse, 2023-25 | yes | 0.6205 -> 0.6185 |
| beats its placebo on 2015-18 | yes | 50 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2019-22 | yes | 50 of 50 draws (need 45 of at least 50) |
| beats its placebo on 2023-25 | yes | 50 of 50 draws (need 45 of at least 50) |

Gate: FAIL (16 of 18); no market input and no look-ahead checked by the model-auditor agent

### Gate, V10: Wind learned from the forecast (team points miss)

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | NO | miss 7.3993 -> 7.4024 |
| better on 2019-22 | NO | miss 7.3739 -> 7.3741 |
| better on 2023-25 | NO | miss 7.2357 -> 7.2359 |
| no bet cost: spread flag, 2015-18 | yes | 68-58 -> 69-56 |
| no bet cost: totals flag, 2015-18 | NO | 132-111 -> 122-107 |
| no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| no bet cost: spread flag, 2019-22 | yes | 78-49 -> 81-48 |
| no bet cost: totals flag, 2019-22 | NO | 175-140 -> 171-139 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | yes | 37-19 -> 36-18 |
| no bet cost: totals flag, 2023-25 | yes | 76-55 -> 80-55 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |
| calibration not worse, 2015-18 | NO | 0.6192 -> 0.6195 |
| calibration not worse, 2019-22 | yes | 0.6245 -> 0.6245 |
| calibration not worse, 2023-25 | NO | 0.6205 -> 0.6207 |

Gate: FAIL (8 of 15); no market input and no look-ahead checked by the model-auditor agent

### Gate, V11: Home edge x visitor's travel miles (team points miss)

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | yes | miss 7.3993 -> 7.3975 |
| better on 2019-22 | yes | miss 7.3739 -> 7.3738 |
| better on 2023-25 | yes | miss 7.2357 -> 7.2319 |
| no bet cost: spread flag, 2015-18 | yes | 68-58 -> 70-53 |
| no bet cost: totals flag, 2015-18 | yes | 132-111 -> 132-111 |
| no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| no bet cost: spread flag, 2019-22 | yes | 78-49 -> 81-48 |
| no bet cost: totals flag, 2019-22 | yes | 175-140 -> 175-140 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | NO | 37-19 -> 37-21 |
| no bet cost: totals flag, 2023-25 | yes | 76-55 -> 76-55 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |
| calibration not worse, 2015-18 | NO | 0.6192 -> 0.6196 |
| calibration not worse, 2019-22 | yes | 0.6245 -> 0.6244 |
| calibration not worse, 2023-25 | yes | 0.6205 -> 0.6197 |

Gate: FAIL (13 of 15); no market input and no look-ahead checked by the model-auditor agent

### Gate, V12: Home edge x visitor's time-zone change (team points miss)

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | NO | miss 7.3993 -> 7.4003 |
| better on 2019-22 | yes | miss 7.3739 -> 7.3717 |
| better on 2023-25 | yes | miss 7.2357 -> 7.2286 |
| no bet cost: spread flag, 2015-18 | yes | 68-58 -> 69-54 |
| no bet cost: totals flag, 2015-18 | yes | 132-111 -> 132-111 |
| no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| no bet cost: spread flag, 2019-22 | yes | 78-49 -> 83-53 |
| no bet cost: totals flag, 2019-22 | yes | 175-140 -> 175-140 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | NO | 37-19 -> 36-25 |
| no bet cost: totals flag, 2023-25 | yes | 76-55 -> 76-55 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |
| calibration not worse, 2015-18 | NO | 0.6192 -> 0.6199 |
| calibration not worse, 2019-22 | yes | 0.6245 -> 0.6239 |
| calibration not worse, 2023-25 | yes | 0.6205 -> 0.6197 |

Gate: FAIL (12 of 15); no market input and no look-ahead checked by the model-auditor agent

### Gate, V13: Neutral sites: home edge zero (team points miss)

| Check | Passes | Detail |
|---|---|---|
| better on 2015-18 | yes | miss 7.3993 -> 7.3983 |
| better on 2019-22 | NO | miss 7.3739 -> 7.3745 |
| better on 2023-25 | NO | miss 7.2357 -> 7.2394 |
| no bet cost: spread flag, 2015-18 | yes | 68-58 -> 65-55 |
| no bet cost: totals flag, 2015-18 | yes | 132-111 -> 132-111 |
| no bet cost: wind under, 2015-18 | yes | 119-97 -> 119-97 |
| no bet cost: spread flag, 2019-22 | yes | 78-49 -> 78-45 |
| no bet cost: totals flag, 2019-22 | yes | 175-140 -> 175-140 |
| no bet cost: wind under, 2019-22 | yes | 143-88 -> 143-88 |
| no bet cost: spread flag, 2023-25 | NO | 37-19 -> 34-18 |
| no bet cost: totals flag, 2023-25 | yes | 76-55 -> 76-55 |
| no bet cost: wind under, 2023-25 | yes | 77-52 -> 77-52 |
| calibration not worse, 2015-18 | NO | 0.6192 -> 0.6195 |
| calibration not worse, 2019-22 | yes | 0.6245 -> 0.6241 |
| calibration not worse, 2023-25 | NO | 0.6205 -> 0.6215 |

Gate: FAIL (10 of 15); no market input and no look-ahead checked by the model-auditor agent

## Verdict

**Nothing passes; nothing changes.** None of the 13 variants passes parts 1 and 2 of the rule on main's honest
backtest, so no placebo was owed, there was nothing to rerun together (part 5) and nothing for the model-auditor to
audit. The model and the bet rules stay as they are.

The fixes did not turn any old near miss into a pass; the same three removals miss again by one bet or a hair of calibration, as in round 3 (V2 then failed on the 2023-25 totals flag, now on 2019-22):
- **V1, drop QB out (points):** team miss and spread flag better on every window (69-55, 79-49, 38-19), but the
  calibrated win chance is 0.0005 worse in log loss on 2019-22 (0.62450 -> 0.62501).
- **V2, drop cold (total):** total miss better on every window (10.7484 -> 10.6799, 10.5341 -> 10.5306, 10.1040 -> 10.0992)
  and the totals flag better on 2015-18 and 2023-25, but one game worse on 2019-22 (175-140 -> 174-141).
- **V4, drop dome (points):** team miss better on every window by 0.0002 or less; log loss 0.0001 worse on 2023-25.
These three stay for the re-check after the 2026 season.

**V9, usual snaps out**, is the largest accuracy gain here (team miss -0.020 / -0.008 / -0.016, calibration better on every
window) and, in a placebo added after the results (informational, not part of the pre-registration), beats all 50
within-season shuffles on every window: the gain is real. It fails on bets: the spread flag drops from 68-58 to 54-53 on
2015-18 and from 37-19 to 38-21 on 2023-25, and the margin miss is a little worse on 2019-22 (10.0118 -> 10.0136), as
on 30 Sep. Not adopted under the rule.

The rest: V8 (opponent defenders out) helps or ties the spread flag and helps the calibration on every window but its team miss is worse
on 2015-18 (7.3993 -> 7.4025), as on 1 Oct; V5 (QB form) costs the spread flag on 2019-22 (78-49 -> 59-44); the two weather
bands (V6, V7) are worse on 2019-22 and cost totals-flag games; V10, V12 and V13 are worse on one to three windows; V3 and
V11 cost bets.

**Count.** 13 variants here, all pre-registered; one informational placebo added after the results (V9). About 40 earlier
variants of the same 13 ideas. No cutoff, band or weight was tuned here; the 13 were chosen from earlier results on all three windows (see the pre-registration).

**Changed after the pre-registration (no result depends on it):** the V6 and V7 readings drop the two 2025 games abroad
and roofed games, as the live readers do (`wind_live._history`, `_roofed`), after the code review; 2023-25 moved by under
0.001. The V5 placebo was corrected to shuffle a copy of `qb_form` (the totals equation reads the original); V5 failed
parts 1-2, so its placebo never ran. Input checks added per season (V8, V9). After the fact check, the Step 1 rows for V4, V8 and V11 quote their original results in full (V11 had failed rule 1 on the margin miss, not the team miss); no variant changed.

**Audit.** The model-auditor runs on what passes; nothing passed. The `pr-reviewer` agent reviewed the script (one
placebo bug in V5, fixed; the other twelve variants match this pre-registration).

