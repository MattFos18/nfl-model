"""Player against scheme, matchup projections and the props track record (23 Sep 2026).

From data/processed/scheme_plays.parquet (every play since 2016 with the participation and FTN tags): each QB,
receiver and rusher's numbers over his last WINDOW games, split by the looks he faced (man, zone, pressure, clean,
blitz, light and heavy boxes), and each defense's allowed numbers and mix over its last WINDOW games. For every
game of the current week, each player's projected volume and yards against that defense, by the rule three rounds
of walk-forward backtest chose (experiments/props_backtest.py, props_backtest2.py, props_backtest3.py and their
reports; 2019 to 2025 on both windows, every constant fitted on 2016 to 2018 only):
  volume:   the team's pass plays (or runs, or dropbacks) per game over its last 17, moved by the game script (a
            fitted line on the closing spread and total: favourites run more and pass less, high totals add pass
            plays; GS), shared among the players who are playing in proportion to their usage share, where usage
            is decayed by DECAY per game back so the current role counts most (an absent player's targets go to
            his teammates). Round 17: the share behind the yards and receptions lines is moved SHARE_A_W of the
            way (receiving three quarters, rushing all) from his share over his games with a touch toward his
            share over every game he was active for, a game without a touch counting 0 (a backup's empty games
            pull his volume down; scored on every game a projected player played snaps in, as the card projects)
  rate:     the player's yards per touch shrunk toward the league's with K touches of weight (receivers 100 targets,
            rushers 25 carries, QBs 50 dropbacks), then moved W of the way toward what the defense allows per touch
            relative to the league (receivers 0.25, rushers 0.25, QBs 0.5)
  line:     volume x rate x the median factor: yards in a game are right-skewed, so the line that is off by least sits
            below the mean, as a book's over/under does. The factor rises with the player's mean (MED_TIER, round 15:
            a small role's median sits far below its mean, a star's close to it; receivers 0.69 to 0.87, QBs 0.81 at
            200 mean yards to 0.90 at 300; rushers flat 0.84). The mean is kept beside it.
  counts:   receptions = targets x catch rate shrunk toward the league (K_CATCH) x MED_CATCH; touchdowns = volume x
            his rate shrunk toward the league (K_TD), receiving and passing scores moved TD_MARGIN per point of
            expected margin; interceptions = dropbacks x the league rate (his own rate carried no information).
            Chosen in round 5 by absolute error (receptions) and Poisson log loss (scores, picks) on both windows.
            Round 14 (the anytime price): the touchdown volume uses his usage over every game he was active for,
            a game without a touch counting 0 (share_td; round 17 then moved the yards and receptions lines most of
            the way to the same share, SHARE_A_W), the rate is
            shrunk toward the league's for his position (TD_POS), and the injury report cuts receiving scores
            (INJ_TD); scored on every game a projected player played snaps in (BACKTEST_TD)
  team:     each team's players are then moved part of the way (RECON_W) toward what the game model expects of the
            team: its expected points (the game model's own, priced before the game) give the team's expected
            receiving, rushing and passing yards and touchdowns (TEAM_FIT), and every player's line is scaled by
            the ratio of that to what the players add up to (round 6: helps every stat on both windows, passing
            yards by three yards; the game model's margin in place of the closing line changed nothing)
  defense:  each team's defenders too (round 7): tackles plus assists = his decayed share of the team's tackles x the
            team's tackles per play faced x the opponent's plays with the game script x DEF_MED; sacks = his rate per
            play faced shrunk toward the league (K_SACK), x the opponent's plays
  passing:  the team's dropbacks are blended PACE (a quarter) toward what the opponent has allowed per game, and the
            line is cut WIND_C per mph of wind above 10 at kickoff once a forecast is usable (round 4: both helped
            passing yards on both windows; for receiving and rushing every round-4 layer was inside the noise)
The look-by-look splits (man/zone, box, pressure), routes, coverage-specific usage, defense by position and the
coach's pass rate are shown as readings only: projecting with them was worse than not on both windows.
Projections are readings and get graded every run against what happened (data/tracker/props_graded.csv), and
against the closing book line where one was logged (nflmodel/props_lines.py; data/tracker/props_vs_market.csv: the
side the projection took, the result, and the book's own error beside ours), so they build a record before anyone
bets on them. Nothing here feeds the game model.
Usage: python -m nflmodel.props   writes data/processed/props.json, reports/props_<season>_wk<week>.csv and .md, grades last week"""
from __future__ import annotations
import json
import numpy as np, pandas as pd
from .features import RAW, OUT, ROOT
WINDOW, MIN_SPLIT, MIN_VOL = 17, 15, 8
K = {"rec": 100.0, "rush": 25.0, "pass": 50.0}       # touches of league-average weight the player's rate is shrunk with (backtest, 23 Sep 2026)
W = {"rec": 0.25, "rush": 0.25, "pass": 0.5}         # weight toward what the defense allows per touch, relative to the league
DEF_WEIGHT = W["rec"]                                # kept for the page's note
DECAY = 0.85                                         # usage share: weight per game back (0.85 beat 0.90 and flat on both windows, round 3)
GS_TOTAL = 43.5674                                   # league mean closing total the game-script line is centred on (all games in games.parquet)
GS = {"rec": (-0.5969, -0.046, 0.1636), "rush": (0.3413, 0.103, -0.1713), "pass": (-0.5967, -0.0461, 0.1638)}   # plays per game beyond the team's last-17 average: intercept, per point of expected margin, per point of total above GS_TOTAL; least squares on 2016 to 2018 (pass plays, runs, dropbacks)
MED = {"rec": 0.81, "rush": 0.84, "pass": 0.88}      # the flat median factor on the yards line. Rushing 0.84 fitted on 2016 to 2018 in round 3; receiving and passing refit on 2017-18 with today's rule in round 11 (the round-3 values 0.88 and 0.90 had gone stale as rounds 4 to 10 changed the rule under them; reports/props_backtest11.csv, better on both windows)   # 24 Sep 2026: passing refit to 0.88 (and TEAM_FIT pass yds to 103.23 + 6.268 x exp pts, refit after the QB season fade) once passing yards became gross, the yards the books settle on (experiments/props_official.py)   # 27 Sep 2026: receiving and passing now take the curve MED_TIER below; the flat values stay as the rushing factor, the fallback for a kind without a curve, and the reference round 15 scored against
# round 15 (27 Sep 2026, reports/props_backtest15.csv): the median factor rises with the player's mean. One flat factor turns every
# mean into the line, but the median of a right-skewed yardage distribution sits far below the mean for a 3-target player and close
# to it for a 10-target one, so a flat factor over-shrinks the stars (the top decile of receiving lines sat 10 yards under what
# happened) and under-shrinks small roles. Receivers: 0.690 for a small mean rising to 0.869 for a large one, a logistic curve
# centred at 32.6 mean yards with a scale of 5 (0.72 at 25 yards, 0.78 at 32.6, 0.84 at 40, 0.86 at 50); QBs: 0.630 + 0.00091 x
# mean yards (0.81 at 200, 0.86 at 250, 0.90 at 300), clipped to 0.5 to 1.2. Fitted on 2017-18 by mean absolute error with the
# team reconciliation applied at every candidate, as the live rule orders them; receiving yards 19.17 / 18.16 against the flat
# factor's 19.28 / 18.25 (five paired standard errors), passing 56.56 / 56.06 against 56.74 / 56.21 (two). Rushing stays flat:
# every form gained under 0.02 yards, inside one standard error. Tested beside it and not adopted: usage shares capped at one
# (lost on rushing, inside the noise on receiving), the snap trend at half weight or on the volume, a faster usage decay.
MED_TIER = {"rec": ("logistic", 0.690, 0.869, 32.6, 5.0), "pass": ("linear", 0.630, 0.00091)}
K_CATCH, MED_CATCH = 25.0, 0.9                     # catch rate shrunk toward the league with 25 targets of weight (round 5); receptions line x 0.9, refit on 2017-18 in round 11 (was 0.88; reports/props_backtest11.csv, better on both windows)
K_TD = {"rec": 200.0, "rush": 200.0, "pass": 400.0}  # touchdown rate per touch shrunk toward the league (round 5: best Poisson fit on 2016 to 2018, held on both windows)
TD_MARGIN = {"rec": 0.020, "rush": 0.0, "pass": 0.020}   # touchdown rate x (1 + TD_MARGIN x expected margin): favourites score more; fitted on 2016 to 2018 (rushing: no gain on both windows, so 0)
BACKTEST_COUNTS = {'rec_catches': [1.44, 1.36], 'rec_td_ll': [0.5104, 0.4873], 'rush_td_ll': [0.5824, 0.5517], 'pass_td_ll': [1.4643, 1.4183], 'pass_int_ll': [1.1455, 1.1036]}   # (1 Oct 2026: the forecast rain in the game total, every count moved by 0.001 or less)   # (1 Oct 2026: wind points in the game total, every count moved by 0.001 or less)   # (29 Sep 2026, round 3's situational factors SIT: receptions 1.44 / 1.37 -> 1.44 / 1.36, touchdowns 0.5108 / 0.4877 -> 0.5106 / 0.4874 receiving, 0.5823 / 0.5521 -> 0.5822 / 0.5519 rushing, 1.4664 / 1.4201 -> 1.4663 / 1.4198 passing)   # the same run: receptions mean absolute error, touchdown and interception Poisson log loss, 2019-22 / 2023-25 (reports/props_by_season.csv). The by-season frame grades only player-games with a touch, so the round-14 touchdown rule reads worse there (0.5095 / 0.4857 and 0.5767 / 0.5482 before it), as does the round-17 share on receptions (1.43 / 1.35 before it; on every game a projected player played, 1.343 / 1.259 against 1.411 / 1.326): the number that counts for a score is BACKTEST_TD, on every game a projected player played
RECON_W = {"rec": {"yds": 0.25, "td": 0.5}, "rush": {"yds": 0.25, "td": 0.5}, "pass": {"yds": 0.5, "td": 1.0}}   # round 6: weight of the move toward the team's expected yards and touchdowns from the game model's expected points (best row on both windows per stat)
TEAM_FIT = {"rec": {"td": (-0.2529, 0.07481), "yds": (86.16, 6.483)}, "rush": {"td": (-0.1856, 0.04091), "yds": (71.47, 1.388)}, "pass": {"td": (-0.2618, 0.079), "yds": (103.23, 6.268)}}   # team touchdowns and yards of each kind = intercept + slope x the game model's expected points, least squares on 2016 to 2018 (reports/props_backtest6.csv, *_team_fit rows)
PROP_EDGE = None   # {"rec_yards": 7.5, ...}: the edge (projection minus book line, absolute) at which a prop is flagged, per stat; None until reports/props_vs_market_cuts.csv chooses one that holds on both windows (experiments/props_vs_market_backtest.py). No cut, no flags.
DEF_DECAY, DEF_MED, K_SACK = 0.85, 0.90, 300.0         # round 7 (reports/props_backtest7.csv): tackles = his decayed share of the team's tackles x the team's tackles per play faced x the opponent's plays with the game script, x 0.90; sacks = his rate per play faced shrunk toward the league with 300 plays of weight (best Poisson fit both windows)
BACKTEST_DEF = {"def_tackles": [1.648, 1.633], "def_sacks_ll": [0.3813, 0.3887]}   # tk_85gs_med and sk_K300 in props_backtest7.csv
LONGEST = {"rec": (6.9084, 0.3362, 0.1291, 0.84), "rush": (6.9330, 0.1545, 0.1153, 0.78), "pass": (16.3327, 0.2340, 0.0547, 0.92)}   # round 8 (reports/props_backtest8.csv, l_blend_med): longest gain of the game = median factor x (a + b x his game-longest decayed 0.85 per game back + c x his yards per game); fitted on 2016 to 2018
BACKTEST_LONGEST = {"rec_longest": [9.256, 9.274], "rush_longest": [7.575, 7.309], "pass_longest": [11.803, 11.686]}   # l_blend_med in props_backtest8.csv
FADE = {"rec": (0.5, 0.5), "rush": (0.25, 0.5)}   # round 10 (reports/props_backtest10.csv): the usage share's weights take an extra factor across a season boundary and across a change of team (last year's role counts for less in September); no redistribution of an absent player's share (every form of it lost on both windows)
KICK = {"pts": (2.4861, 0.1843, 0.1489), "fgm": (1.0165, 0.1757, 0.0155)}   # round 9 (reports/props_backtest9.csv, k_blend_team and g_blend_team): kicking points = a + b x his team's kicking points per game decayed 0.85 + c x the team's implied total ((closing total + expected margin) / 2); field goals made the same; fitted on 2016 to 2018
BACKTEST_KICK = {"kick_points": [2.832, 2.925], "field_goals": [0.969, 1.001]}   # k_blend_team and g_blend_team in props_backtest9.csv
PACE = {"rec": 0.0, "rush": 0.25, "pass": 0.25}       # weight on the opponent's allowed plays per game in the team's volume (round 4: helps passing on both windows, nothing on the others)
# round 18 (29 Sep 2026, experiments/props_gs_absorb.py, reports/props_gs_absorb.md): rushing volume a quarter of the way toward the
# opponent's allowed runs per game (PACE["rush"], carries better by 3-4 standard errors on both windows and both frames); and when a
# starter is out (the report's Out/Doubtful/IR/roster status, as the live rule can know it), ABSORB of his share_yds goes to his
# same-position teammates who play, in proportion to their own shares: half the fraction fitted on 2017-18 (WR 0.422, TE 0.249,
# RB 0.348; the half chosen on the fit window). Never pro rata of the whole share and never to other positions: every such form
# lost in round ten. A starter: share_yds at least ABSORB_THR, a snap in one of the team's last ABSORB_LOOKBACK games.
ABSORB = {"rec": {"WR": 0.211, "TE": 0.125}, "rush": {"RB": 0.174}}
ABSORB_THR = {"rec": 0.15, "rush": 0.25}; ABSORB_LOOKBACK = 3
ABSORB_GROUP = {"WR": "WR", "TE": "TE", "RB": "RB", "FB": "RB", "HB": "RB"}
# the chance of a book number (experiments/props_chance.py, reports/props_chance.md, 29 Sep 2026): read off the past player-games
# whose line was closest to ours (data/processed/props_reference.parquet, every projected player-game of the by-season backtest,
# 2017 to the season before this one): the K nearest in the line, K a tenth of the table between 300 and 1500, and the share of
# them that beat the book number the same way (actual over the line as a ratio for receiving yards and receptions, as a
# difference for passing and rushing yards). Calibrated within 3 points in every band on both windows; rushing only from a
# 10-yard line (the tiny lines below it are the one band that missed). A zero-touch game is not in the table, so the chance
# is conditional on the player getting on the stat sheet.
CHANCE = {"rec_yards": ("rec", "ratio"), "rec_catches": ("rec_catch", "ratio"), "rush_yards": ("rush", "diff"), "pass_yards": ("pass", "diff")}
CHANCE_MIN_LINE = {"rush_yards": 10.0}
_OWN = {"rec_yards": "proj_rec_yards", "rec_catches": "proj_catches", "rush_yards": "proj_rush_yards", "pass_yards": "proj_pass_yards"}   # each chance-bearing market's own line on the row
CHANCE_K = (0.10, 300, 1500)
_REF: dict = {}
# round 13 (25 Sep 2026, reports/props_backtest13.csv): a player who plays while listed Questionable, or after a limited
# practice on the final report, gets less (the group's actual over line against the unlisted players', fitted on 2017-18);
# and his snap share over his last 3 games against his last 10 moves the yards line a quarter of the way. Together
# better on both windows for receiving (19.277 / 18.257 against 19.305 / 18.278) and rushing (17.806 / 17.027
# against 17.858 / 17.037); passing unchanged (the snap trend made it worse)
INJ_F = {"rec": {"Q": 0.907, "LIM": 0.913}, "rush": {"Q": 0.928}}
SNAP_W = {"rec": 0.25, "rush": 0.25}
# round 14 (27 Sep 2026, reports/props_backtest14.csv): the anytime-touchdown price. Scored on the "active" frame (every
# game a projected player played snaps in, a game without a touch as 0: the population the card projects; the touch-only
# frame of rounds 5 to 13 never graded a backup who got nothing, so over-projecting him was invisible), Poisson log loss
# on the count, 2019-22 / 2023-25. Adopted, each better on both windows on top of the last:
#   the touchdown volume uses his usage share over every game he was active for (snap counts), a game without a touch
#   counting 0 over the team's plays: _share saw only his games with a touch, so a backup's share was that of his good
#   days (receiving 0.4231 / 0.3962 -> 0.4194 / 0.3922; rushing 0.4237 / 0.3840 -> 0.4202 / 0.3770). The yards and
#   receptions lines keep the touch-games share rounds one to thirteen chose on their own frame;
#   the prior his rate per touch is shrunk toward is the league's x his position's factor (TD_POS: touchdowns per touch
#   by position over the league's, 2017-18; a running back's target is worth two thirds of a wideout's, a quarterback's
#   carry a quarter more than a back's) (-> 0.4173 / 0.3905 receiving, 0.4195 / 0.3768 rushing);
#   the injury-report factor on receiving touchdowns (INJ_TD; 0.4171 / 0.3905, inside the noise but no worse anywhere).
# Not adopted: the snap trend on touchdowns (worse at every weight), shares capped at 1 over the playing players (no gain
# once the share counts his empty games), team reconcile weights 0.75 and 1.0 (worse on top of the new share), the
# prior by usage tier (no gain beyond position). Anytime price, receiving plus rushing: log loss 0.4359 / 0.4141 ->
# 0.4313 / 0.4091; the 5-10% bucket's actual rate 5.0% -> 7.0% against a mean prediction of 7.6% -> 7.3%
TD_POS = {"rec": {"WR": 1.047, "TE": 1.182, "RB": 0.671}, "rush": {"QB": 1.265, "RB": 0.965, "WR": 0.72}}
TD_POS_GROUP = {"rec": {"WR": "WR", "TE": "TE", "RB": "RB", "FB": "RB", "HB": "RB"}, "rush": {"QB": "QB", "RB": "RB", "FB": "RB", "HB": "RB", "WR": "WR", "TE": "WR"}}
INJ_TD = ("rec",)
SKILL = {"rec": {"WR", "TE", "RB", "FB", "HB"}, "rush": {"RB", "FB", "HB", "QB", "WR", "TE"}}   # the roster positions whose snaps without a touch count in the touchdown share
BACKTEST_TD = {"rec_td_ll": [0.4171, 0.3905], "rush_td_ll": [0.4195, 0.3768], "any_td_ll": [0.4313, 0.4091]}   # the adopted rule on the active frame: Poisson log loss on the count (receiving, rushing), log loss of the anytime price (both together), 2019-22 / 2023-25 (reports/props_backtest14.csv, V5_combo rows)
# round 17 (27 Sep 2026, reports/props_backtest17.csv, _tiers.csv): the active-games share on the yards and receptions lines too.
# Scored on both frames by mean absolute error per player-game: the touch frame (player-games with a touch, the frame rounds
# one to thirteen chose the touch-games share on) and the active frame (plus every game a projected player played snaps in
# without a touch, actual 0: the population the card projects). The active share alone wins the active frame by 0.7 yards
# receiving (17.40 / 16.29 -> 16.69 / 15.54) and a yard rushing (14.54 / 13.47 -> 13.56 / 12.32) and loses the touch frame
# by 0.05 / 0.07 receiving (19.17 / 18.16 -> 19.22 / 18.22), all of that loss in the 0-20 tier (a backup's good days); from
# 20 yards up every tier improves on both frames, the stars' lines rising toward what happened. Adopted, the share behind
# the yards and receptions volume = (1 - w) x touch-games share + w x active-games share, w chosen on 2017-18 on the active
# frame: receiving w = 0.75 (touch 19.16 / 18.16, active 16.84 / 15.70; receptions 1.445 / 1.373 touch against 1.435 / 1.355,
# 1.343 / 1.259 active against 1.411 / 1.326), rushing w = 1 (touch 17.77 / 17.04, active 13.56 / 12.32). The receptions line
# follows the targets volume: a receiver has one projected targets figure. Not adopted: the active share capped at 1 over the
# players who play (better again on both frames, rushing 17.72 / 17.00 and 13.48 / 12.27, but the sum needs to know who plays;
# rounds 14 and 15 found the roster the card can know inflates the sum and the cap loses). Season totals (player_season.py)
# still read the touch-games share, untested there.
SHARE_A_W = {"rec": 0.75, "rush": 1.0}   # weight on the active-games share in the yards and receptions volume; the rest on the touch-games share
# round 3 of the props (29 Sep 2026, experiments/situational_props.py, reports/situational_props.md, under reports/round3_rule.md):
# the situational pieces that passed rules 1-3 alone and, per stat, rules 1-2 refitted together (rule 5). Each is a factor on
# one stat's final line, after the injury/snap factor: exp(b x (z - q)), z the input for this game (as of before kickoff, no
# market input; nflmodel/props_sit.py builds them) and q the player's own 0.85-decayed mean of z over his earlier projected
# games (the by-season backtest's frame, from 2016; props_sit_state.parquet), each term clipped to +-SIT_CLIP. b is the
# study's walk-forward refit with the stat's pieces fitted together in its order: SIT the last refit (on 2016-2025, the live
# sizes), SIT_WALK each season's (fitted on the seasons before it, 2017 to 2025; the by-season backtest scores with these).
# Inputs: same_out, the known-out starters' share at his own position group (the share the absorb step hands on: WR / TE
# from the receiving table, RB from the rushing one); rb_out, the known-out RB starters' share; opp_cb_r, this week's
# expected starting corners' rating (the top three by snap share over the defence's last three games, less the known-out;
# the positions.py corner recipe); opp_cb_chg, that less the corners who played its last eight games; rest_days (4 to 14);
# qb_rating (the game model's, this week's starter); rain (the game model's rain call, outdoors); cold (under 35 F
# outdoors); wind_turf (mph of kickoff wind above 10 on an artificial surface). Live weather is the kickoff forecast in use.
# The study's shares capped at one on the targets line is left out: it made the targets line disagree with the receptions
# and yards lines it feeds (both worse with it); without it the targets pieces still pass rules 1-2 together (miss
# -0.0021 / -0.0013 / -0.0027 targets per player-game on 2017-18 / 2019-22 / 2023-25, lean record 84-63 -> 85-62).
SIT = {"rec_catches": [("same_out", 0.425443), ("opp_cb_r", -5.6261), ("rest_days", -0.0083227), ("rb_out", 0.0566034)],
       "rec_targets": [("same_out", 0.319082), ("rest_days", -0.00416135)],
       "rec_td": [("qb_rating", 0.942175), ("rain", -0.18611)],
       "rush_yards": [("cold", 0.102587)], "rush_td": [("wind_turf", 0.0341646)], "pass_td": [("opp_cb_chg", -11.9516)]}
SIT_WALK_FROM = 2017   # SIT_WALK's first season; 2016 (fitting rows only) carries no factor, 2026 on the live SIT
SIT_WALK = {"rec_catches": {"same_out": (0.398853, 0.478623, 0.584984, 0.452033, 0.425443, 0.425443, 0.398853, 0.398853, 0.452033), "opp_cb_r": (0.0, 0.0, -4.01865, -3.21492, -4.01865, -3.21492, -2.41119, -4.82238, -4.82238),
                            "rest_days": (-0.00624203, -0.00520169, -0.00728236, -0.0083227, -0.00728236, -0.0083227, -0.00728236, -0.00728236, -0.0083227), "rb_out": (0.141509, 0.0707543, 0.141509, 0.099056, 0.0707543, 0.0707543, 0.0566034, 0.0283017, 0.0566034)},
            "rec_targets": {"same_out": (0.558394, 0.372263, 0.425443, 0.398853, 0.345673, 0.319082, 0.292492, 0.265902, 0.319082), "rest_days": (-0.00312101, -0.00312101, -0.00416135, -0.00312101, -0.00312101, -0.00416135, -0.00416135, -0.00416135, -0.00416135)},
            "rec_td": {"qb_rating": (1.4357, 1.66002, 1.52543, 1.07677, 1.12164, 1.03191, 0.98704, 0.897309, 0.98704), "rain": (-0.0979526, -0.166519, -0.195905, -0.254677, -0.254677, -0.235086, -0.195905, -0.195905, -0.18611)},
            "rush_yards": {"cold": (0.130565, 0.111913, 0.111913, 0.121239, 0.121239, 0.139892, 0.111913, 0.111913, 0.111913)},
            "rush_td": {"wind_turf": (0.0109327, 0.0109327, 0.016399, 0.0136658, 0.0368978, 0.0204988, 0.032798, 0.0314314, 0.0314314)},
            "pass_td": {"opp_cb_chg": (0.0, 0.0, -17.0737, -10.2442, -10.2442, -10.2442, -10.2442, -8.53686, -8.53686)}}
SIT_KIND = {"rec_catches": "rec", "rec_targets": "rec", "rec_td": "rec", "rush_yards": "rush", "rush_td": "rush", "pass_td": "pass"}
SIT_CLIP = 0.7


def sit_b(stat: str, season: int | None = None) -> list:
    """[(input, b)] for a stat: the live SIT, or for a backtest season SIT_WALK's (0 before SIT_WALK_FROM)."""
    if season is None or season >= SIT_WALK_FROM + len(next(iter(SIT_WALK[stat].values()))):
        return SIT.get(stat, [])
    return [(i, (SIT_WALK[stat][i][season - SIT_WALK_FROM] if season >= SIT_WALK_FROM else 0.0)) for i, _ in SIT.get(stat, [])]


def sit_factor(stat: str, z: dict, q: dict, season: int | None = None) -> float:
    """exp(sum of b x (z - q)) over the stat's SIT inputs, each term clipped to +-SIT_CLIP; an input missing this week
    (None or NaN) adds nothing."""
    s = 0.0
    for inp, b in sit_b(stat, season):
        v = z.get(inp); qq = q.get(inp)
        if v is None or qq is None or pd.isna(v) or pd.isna(qq):
            continue
        s += min(max(b * (float(v) - float(qq)), -SIT_CLIP), SIT_CLIP)
    return float(np.exp(s))


def td_prior(kind: str, pos: str | None, league: float) -> float:
    """The league's touchdown rate per touch x his position's factor (round 14); the league's alone for a position not listed."""
    return league * TD_POS.get(kind, {}).get(TD_POS_GROUP.get(kind, {}).get(pos or "", ""), 1.0)


def active_games(season: int, week: int) -> pd.DataFrame:
    """Every offensive player-game with a snap (snap counts) before (season, week), last season and this: player_id,
    game_id, season, week, posteam, position. The games a player was active for without a touch, for the touchdown share."""
    f = OUT / "snap_exposure.parquet"
    if not f.exists():
        return pd.DataFrame(columns=["player_id", "game_id", "season", "week", "posteam", "position"])
    e = pd.read_parquet(f, columns=["player_id", "game_id", "season", "week", "team", "position", "off_pct"]).dropna(subset=["off_pct"]).rename(columns={"team": "posteam"})
    e = e[(e.off_pct > 0) & ((e.season < season) | ((e.season == season) & (e.week < week))) & (e.season >= season - 1)]
    return e.drop(columns=["off_pct"]).drop_duplicates(["player_id", "game_id"])


def _by_player(active: pd.DataFrame | None, kind: str) -> dict:
    """player_id -> his active games at a position whose snaps count for this kind (SKILL); {} when no snap counts."""
    if active is None or not len(active):
        return {}
    a = active[active.position.isin(SKILL[kind])]
    return {pid: g for pid, g in a.groupby("player_id")}


def inj_group(report, practice) -> str:
    """This week's report for a player who plays: Q (Questionable), DNP or LIM (the practice status), else none."""
    rep = report if isinstance(report, str) else ""; pr = practice if isinstance(practice, str) else ""
    return "Q" if rep.startswith("Questionable") else ("DNP" if pr.startswith("Did Not") else ("LIM" if pr.startswith("Limited") else "none"))


def snap_ratio(s3, s10) -> float:
    """His snap share over his last 3 games over his last 10, clipped to [0.4, 2]; 1 when either is missing."""
    try:
        r = float(s3) / float(s10)
    except (TypeError, ValueError, ZeroDivisionError):
        return 1.0
    return 1.0 if not np.isfinite(r) else min(max(r, 0.4), 2.0)


def med_factor(kind: str, mean):
    """The median factor for a player whose mean is `mean` yards (a number or an array): the round-15 curve for the kind
    (MED_TIER: a logistic from lo to hi around a centre, or a straight line clipped to 0.5 to 1.2), else the flat MED."""
    t = MED_TIER.get(kind)
    if t is None:
        return MED[kind] if np.isscalar(mean) else np.full(np.shape(mean), MED[kind])
    if t[0] == "logistic":
        lo, hi, centre, scale = t[1:]; out = lo + (hi - lo) / (1 + np.exp(-(np.asarray(mean, float) - centre) / scale))
    else:
        a, b = t[1:]; out = np.clip(a + b * np.asarray(mean, float), 0.5, 1.2)
    return float(out) if np.isscalar(mean) else out


def snap_trends(season: int, week: int) -> dict:
    """player id -> (snap share over his last 3 games, over his last 10), games before (season, week) (snap counts)."""
    f = OUT / "snap_exposure.parquet"
    if not f.exists():
        return {}
    e = pd.read_parquet(f, columns=["player_id", "season", "week", "off_pct"]).dropna(subset=["off_pct"])
    e = e[(e.off_pct > 0) & ((e.season < season) | ((e.season == season) & (e.week < week)))].sort_values(["player_id", "season", "week"])
    out = {}
    for pid, g in e.groupby("player_id"):
        v = g.off_pct.values
        if len(v) >= 4:
            out[pid] = (float(v[-3:].mean()), float(v[-10:].mean()))
    return out


WIND_FROM = 10.0   # mph at kickoff above which the wind cuts a yards line
TARGETABLE = 0.97   # share of a team's pass plays that are targets (the rest are throwaways and spikes)
WIND_C = {"rec": 0.0, "rush": 0.0, "pass": -0.005}   # yards line x (1 + WIND_C x mph of wind above WIND_FROM at kickoff), fitted on 2016 to 2018 (round 4: passing only)
BACKTEST = {'rec_yards': [19.12, 18.14], 'rush_yards': [17.68, 16.96], 'pass_yards': [56.56, 56.04]}   # (3 Oct 2026: seven inputs dropped (#414); 2 Oct 2026 evening: the forecast history back to 2015 (#398); 2 Oct 2026 afternoon: ref_tot dropped (#387) and forecast weather in the backtest (#389) moved the game model; 2 Oct 2026: the data fixes (#381), passing 55.99 -> 55.94 on 2023-25; 1 Oct 2026: the forecast rain in the game total; passing 56.53 / 56.06 -> 56.48 / 55.99, receiving 19.13 -> 19.12)   # (1 Oct 2026: wind points in the game total the game script reads; passing 56.57 / 56.11 -> 56.53 / 56.06, receiving 18.15 -> 18.14)   # (29 Sep 2026: round 3's cold factor on rushing, SIT: 17.69 / 16.97 -> 17.68 / 16.96)   # (28 Sep 2026: the game script reads the model's margin and total, never the line; passing moved 56.56 / 56.06 -> 56.55 / 56.05)   # mean absolute error per player-game, 2019-22 / 2023-25, of the adopted rule run walk-forward with league averages as of each game (reports/props_by_season.csv; round 11 factors, round 13 injury report and snap trend, round 15 median curve: receiving was 19.28 / 18.25 and passing 56.74 / 56.21 with the flat factors; round 17 active-games share: receiving was 19.17 / 18.16 and rushing 17.80 / 17.03 with the touch-games share on this frame, which grades only games with a touch; the gain is on the active frame, reports/props_backtest17.csv). The rounds chose the constants with a league average over every season, a small look-ahead: removing it moves the errors by at most 0.05 yards (23 Sep 2026)
TR, REP = ROOT / "data" / "tracker", ROOT / "reports"


def _asof(d: pd.DataFrame, season: int, week: int) -> pd.DataFrame:
    return d[((d.season < season) | ((d.season == season) & (d.week < week))) & (d.season >= season - 1)]


def _last(g: pd.DataFrame, n: int = WINDOW) -> pd.DataFrame:
    ids = g.drop_duplicates("game_id").sort_values(["season", "week"]).game_id.tail(n)
    return g[g.game_id.isin(ids)]


def _stat(x: pd.DataFrame, min_n: int) -> dict | None:
    if len(x) < min_n:
        return None
    return {"n": int(len(x)), "epa": round(float(x.epa.mean()), 3), "yds": round(float(x.yards_gained.fillna(0).mean()), 2), "success": round(float(x.success.mean()), 3)}


def _longest(g_all: pd.DataFrame, g: pd.DataFrame, kind: str) -> dict:
    """His longest gain of the game (completed passes for receivers and passers, runs for rushers; 0 when none),
    decayed DECAY per game back over the as-of frame, and his yards per game over the window: the two inputs of the
    round-8 line. Returns the projected line too."""
    lg = g_all.yards_gained.fillna(0.0) if kind == "rush" else g_all.yards_gained.fillna(0.0).where(g_all.complete_pass.fillna(0).eq(1), 0.0)
    per = lg.groupby([g_all.season, g_all.week, g_all.game_id]).max().reset_index().sort_values(["season", "week"], ascending=False)
    wts = DECAY ** np.arange(len(per)); dec = float((per.iloc[:, -1].values * wts).sum() / wts.sum()) if len(per) else 0.0
    ypg = float(g.yards_gained.fillna(0).sum() / max(g.game_id.nunique(), 1)); a, b, c, med = LONGEST[kind]
    return {"longest_dec": round(dec, 2), "ypg": round(ypg, 2), "proj_longest": round(med * (a + b * dec + c * ypg), 1)}


def _share(g: pd.DataFrame, team_by_game: pd.Series, kind: str = "rec", active: pd.DataFrame | None = None) -> float:
    """His plays over his teams' plays in the same games, both decayed by DECAY per game back from his most recent
    game, over every game in the as-of frame (a player traded in keeps the usage he had elsewhere), with the round-10
    fade: an extra factor on every game before a season boundary and before a change of team. With `active` (his
    games with a snap, round 14), a game he played without a touch counts too, as 0 over the team's plays."""
    pairs = g.groupby(["game_id", "posteam", "season", "week"]).size().reset_index(name="n")
    if active is not None and len(active):
        extra = active[~active.game_id.isin(pairs.game_id)][["game_id", "posteam", "season", "week"]].assign(n=0)
        pairs = pd.concat([pairs, extra], ignore_index=True)
    pairs = pairs.sort_values(["season", "week"], ascending=False)
    sf, tf = FADE.get(kind, (1.0, 1.0)); sn = pairs.season.values; tm = pairs.posteam.values
    sc = np.cumsum(np.r_[0, sn[1:] != sn[:-1]]) if len(pairs) else np.array([]); tc = np.cumsum(np.r_[0, tm[1:] != tm[:-1]]) if len(pairs) else np.array([])
    wts = DECAY ** np.arange(len(pairs)) * sf ** sc * tf ** tc
    mine = float((pairs.n.values * wts).sum())
    tot = float(sum(w * team_by_game.get((r.game_id, r.posteam), 0) for w, r in zip(wts, pairs.itertuples())))
    return mine / tot if tot else 0.0


def share_blend(kind: str, share: float, share_active: float) -> float:
    """The share behind the yards and receptions volume (round 17): SHARE_A_W of the way from his touch-games share
    toward his share over every game he was active for. The two are equal without snap counts."""
    w = SHARE_A_W.get(kind, 0.0)
    return (1 - w) * share + w * share_active


def game_script(kind: str, per_game: float, margin: float | None, total: float | None, opp_allowed: float | None = None) -> float:
    """The team's plays of this kind expected in this game: its last-17 average (blended PACE of the way toward what
    the opponent has allowed per game) plus the fitted game-script line (expected margin from the closing spread,
    from the team's side; total above the league mean). Missing lines count as zero, as in the backtest."""
    b = GS[kind]
    me = 0.0 if margin is None or pd.isna(margin) else float(margin)
    tc = 0.0 if total is None or pd.isna(total) else float(total) - GS_TOTAL
    if PACE[kind] and opp_allowed is not None and not pd.isna(opp_allowed):
        per_game = (1 - PACE[kind]) * per_game + PACE[kind] * float(opp_allowed)
    return max(per_game + b[0] + b[1] * me + b[2] * tc, 0.0)


def recent_players(active: pd.DataFrame | None, team: str, n: int = ABSORB_LOOKBACK) -> set:
    """The players with a snap in one of the team's last n games (active_games), the ones whose absence counts (round 18)."""
    if active is None or not len(active):
        return set()
    a = active[active.posteam == team]
    last = a.drop_duplicates("game_id").sort_values(["season", "week"]).game_id.tail(n)
    return set(a[a.game_id.isin(last)].player_id)


def _absorb_from(rows: list, kind: str, recent: set) -> list:
    """The out starters whose share absorb hands on: out, a snap in one of the team's last games, share_yds at least ABSORB_THR."""
    return [r for r in rows if r["out"] and r["player_id"] in recent and r["share_yds"] >= ABSORB_THR[kind] and ABSORB_GROUP.get(r["pos"], "") in ABSORB[kind]]


def out_shares(rows: list, kind: str, recent: set) -> dict:
    """{position group: the known-out starters' share_yds} (the same starters absorb hands on; round 3's same_out / rb_out)."""
    out: dict = {}
    for a in _absorb_from(rows, kind, recent):
        out[ABSORB_GROUP[a["pos"]]] = out.get(ABSORB_GROUP[a["pos"]], 0.0) + a["share_yds"]
    return out


def absorb(rows: list, kind: str, recent: set) -> None:
    """Round 18: an out starter's share_yds, ABSORB of it, to his same-position teammates who play, in proportion to theirs.
    Only share_yds moves (the yards and receptions volume); the touchdown share stays as it was."""
    for a in _absorb_from(rows, kind, recent):
        grp = ABSORB_GROUP[a["pos"]]; to = [r for r in rows if not r["out"] and ABSORB_GROUP.get(r["pos"], "") == grp]; tot = sum(r["share_yds"] for r in to)
        if tot <= 0:
            continue
        for r in to:
            r["share_yds"] = round(r["share_yds"] + ABSORB[kind][grp] * a["share_yds"] * r["share_yds"] / tot, 3); r["absorbed_from"] = a["name"]


def load_reference(season: int) -> dict:
    """The chance's reference table for `season`: per stat, the lines and actuals of every projected player-game of the seasons
    before it, sorted by the line. {} when the by-season backtest has not written the table yet."""
    if season in _REF:
        return _REF[season]
    f = OUT / "props_reference.parquet"; out = {}
    if f.exists():
        ref = pd.read_parquet(f); ref = ref[(ref.season < season) & (ref.line > 0)]
        for kind, g in ref.groupby("kind"):
            g = g.sort_values("line"); out[kind] = (g.line.values.astype(float), g.actual.values.astype(float))
    _REF[season] = out
    return out


def chance_over(stat: str, line: float | None, x: float | None, season: int) -> float | None:
    """P(actual > x) for a card whose own line is `line`, from the K reference rows nearest in the line (see CHANCE)."""
    if stat not in CHANCE or line is None or x is None or pd.isna(line) or pd.isna(x) or line <= 0 or line < CHANCE_MIN_LINE.get(stat, 0.0):
        return None
    kind, how = CHANCE[stat]; ref = load_reference(season).get(kind)
    if ref is None:
        return None
    hL, hv = ref; n = len(hL)
    if n < CHANCE_K[1]:
        return None
    K = int(min(CHANCE_K[2], max(CHANCE_K[1], CHANCE_K[0] * n))); pos = int(np.clip(np.searchsorted(hL, line) - K // 2, 0, max(n - K, 0)))
    w = hv[pos:pos + K]; wl = hL[pos:pos + K]
    beat = (w / np.where(wl > 0, wl, np.nan) > x / line) if how == "ratio" else (w - wl > x - line)
    return round(float(np.nanmean(beat)), 3)


def wind_factor(kind: str, wind: float | None) -> float:
    """1 + WIND_C x mph above 10 at kickoff; 1 when the wind is unknown (domes, no forecast yet), as in the backtest."""
    if wind is None or pd.isna(wind) or not WIND_C[kind]:
        return 1.0
    return 1 + WIND_C[kind] * max(float(wind) - WIND_FROM, 0.0)


def official(d: pd.DataFrame) -> pd.DataFrame:
    """The charted plays on the official box score's terms (24 Sep 2026, checked against nflverse's player stats):
    a kneel-down is a run (a carry by the QB), a spike is a pass attempt and nothing else, two-point tries are not
    plays (dropped in scheme.load_plays). Passing yards per dropback use pass_yds, the yards on completions: a
    sack's lost yards are not passing yards, and the books settle passing yards gross."""
    d = d[d.play_type.isin(["pass", "run", "qb_kneel", "qb_spike"])].copy()
    d.loc[d.play_type.eq("qb_kneel"), "play_type"] = "run"
    spk = d.play_type.eq("qb_spike"); d.loc[spk, "pass_play"] = False; d.loc[spk, "dropback"] = False
    return d


def receivers(d: pd.DataFrame, names: dict, active: pd.DataFrame | None = None) -> dict:
    """Every receiver's profile over his last WINDOW games with a target. share: his usage over his games with a target;
    share_td: the same over every game he was active for (round 14, the touchdown volume), the share itself without snap
    counts; share_yds: the blend SHARE_A_W of the two behind the yards and receptions lines (round 17)."""
    out = {}
    t = d[d.pass_play & d.receiver_player_id.notna()]
    team_pass = t.groupby(["game_id", "posteam"]).size(); ag = _by_player(active, "rec")
    for pid, g in t.groupby("receiver_player_id"):
        if names.get(pid, ("", ""))[1] == "QB":
            continue
        g_all = g; g = _last(g); tgt = len(g)
        if tgt < MIN_VOL:
            continue
        team = g.sort_values(["season", "week"]).posteam.iloc[-1]
        share = _share(g_all, team_pass, "rec"); share_td = _share(g_all, team_pass, "rec", ag[pid]) if pid in ag else share
        out[pid] = {"name": names.get(pid, (pid, ""))[0], "pos": names.get(pid, ("", ""))[1], "team": team, "games": int(g.game_id.nunique()), "targets": int(tgt), "targets_pg": round(tgt / g.game_id.nunique(), 2), "share": round(share, 3), "share_td": round(share_td, 3), "share_yds": round(share_blend("rec", share, share_td), 3),
                    "catch": round(float(g.complete_pass.fillna(0).mean()), 3), "ypt": round(float(g.yards_gained.fillna(0).mean()), 2), "epa_pt": round(float(g.epa.mean()), 3), "adot": (round(float(g.air_yards.mean()), 1) if g.air_yards.notna().any() else None),
                    "td_pt": round(float(g.pass_touchdown.fillna(0).mean()), 3), "vs_man": _stat(g[g.man], MIN_SPLIT), "vs_zone": _stat(g[g.zone], MIN_SPLIT), "vs_blitz": _stat(g[g.blitz == 1], MIN_SPLIT), "vs_press": _stat(g[g.pressure == 1], MIN_SPLIT), **_longest(g_all, g, "rec")}
    return out


def rushers(d: pd.DataFrame, names: dict, active: pd.DataFrame | None = None) -> dict:
    out = {}
    t = d[d.play_type.eq("run") & d.rusher_player_id.notna()]
    team_run = t.groupby(["game_id", "posteam"]).size(); ag = _by_player(active, "rush")
    for pid, g in t.groupby("rusher_player_id"):
        g_all = g; g = _last(g); n = len(g)
        if n < MIN_VOL:
            continue
        team = g.sort_values(["season", "week"]).posteam.iloc[-1]
        share = _share(g_all, team_run, "rush"); share_td = _share(g_all, team_run, "rush", ag[pid]) if pid in ag else share   # round 14: the touchdown share counts his games without a carry; round 17: the yards line's share too (SHARE_A_W)
        out[pid] = {"name": names.get(pid, (pid, ""))[0], "pos": names.get(pid, ("", ""))[1], "team": team, "games": int(g.game_id.nunique()), "carries": int(n), "carries_pg": round(n / g.game_id.nunique(), 2), "share": round(share, 3), "share_td": round(share_td, 3), "share_yds": round(share_blend("rush", share, share_td), 3),
                    "ypc": round(float(g.yards_gained.fillna(0).mean()), 2), "epa_pc": round(float(g.epa.mean()), 3), "success": round(float(g.success.mean()), 3), "td_pc": round(float(g.rush_touchdown.fillna(0).mean()), 3),
                    "light": _stat(g[g.box <= 6], MIN_SPLIT), "heavy": _stat(g[g.box >= 8], MIN_SPLIT), "mid": _stat(g[g.box == 7], MIN_SPLIT), **_longest(g_all, g, "rush")}
    return out


def passers(d: pd.DataFrame, names: dict) -> dict:
    out = {}
    t = d[d.dropback & d.passer_player_id.notna()]
    for pid, g in t.groupby("passer_player_id"):
        g_all = g[g.pass_play]; g = _last(g); n = len(g)
        if n < MIN_VOL * 3:
            continue
        team = g.sort_values(["season", "week"]).posteam.iloc[-1]
        out[pid] = {"name": names.get(pid, (pid, ""))[0], "pos": names.get(pid, ("", ""))[1], "team": team, "games": int(g.game_id.nunique()), "dropbacks": int(n), "dropbacks_pg": round(n / g.game_id.nunique(), 1),
                    "epa_db": round(float(g.epa.mean()), 3), "ypd": round(float(g.pass_yds.mean()), 2), "sack_rate": round(float(g.sack.fillna(0).mean()), 3), "td_db": round(float(g.pass_touchdown.fillna(0).mean()), 3), "int_db": round(float(g.interception.fillna(0).mean()), 3),
                    "att_rate": round(float(g.pass_play.mean()), 3), "comp": round(float(g[g.pass_att].complete_pass.fillna(0).mean()), 3) if g.pass_att.any() else None,
                    "press": _stat(g[g.pressure == 1], MIN_SPLIT), "clean": _stat(g[g.pressure == 0], MIN_SPLIT), "blitz": _stat(g[g.blitz == 1], MIN_SPLIT), "noblitz": _stat(g[g.blitz == 0], MIN_SPLIT), "vs_man": _stat(g[g.man], MIN_SPLIT), "vs_zone": _stat(g[g.zone], MIN_SPLIT), **_longest(g_all, g[g.pass_play], "pass")}
    return out


def defenses(d: pd.DataFrame) -> dict:
    out = {}
    for team, g in d.groupby("defteam"):
        g = _last(g); ps = g[g.pass_play]; db = g[g.dropback]; run = g[g.play_type.eq("run")]; cv = ps[ps.cov_known]
        out[team] = {"games": int(g.game_id.nunique()), "ypt_allowed": round(float(ps.yards_gained.fillna(0).mean()), 2), "epa_pt_allowed": round(float(ps.epa.mean()), 3), "catch_allowed": round(float(ps.complete_pass.fillna(0).mean()), 3),
                     "ypc_allowed": round(float(run.yards_gained.fillna(0).mean()), 2), "epa_pc_allowed": round(float(run.epa.mean()), 3), "ypd_allowed": round(float(db[db.passer_player_id.notna()].pass_yds.mean()), 2),
                     "man": (round(float(cv.man.mean()), 3) if len(cv) >= 50 else None), "pressure": (round(float(db.pressure.mean()), 3) if db.pressure.notna().sum() >= 50 else None), "blitz": (round(float(db.blitz.mean()), 3) if db.blitz.notna().sum() >= 50 else None),
                     "heavy_box": (round(float((run.box >= 8).mean()), 3) if run.box.notna().sum() >= 30 else None), "light_box": (round(float((run.box <= 6).mean()), 3) if run.box.notna().sum() >= 30 else None),
                     "pass_plays_pg": round(len(ps) / max(g.game_id.nunique(), 1), 1), "runs_pg": round(len(run) / max(g.game_id.nunique(), 1), 1), "dropbacks_pg": round(len(db) / max(g.game_id.nunique(), 1), 1)}
    return out


def teams_volume(d: pd.DataFrame) -> dict:
    out = {}
    for team, g in d.groupby("posteam"):
        g = _last(g); n = max(g.game_id.nunique(), 1)
        out[team] = {"pass_plays_pg": round(float(g.pass_play.sum()) / n, 1), "runs_pg": round(float(g.play_type.eq("run").sum()) / n, 1), "dropbacks_pg": round(float(g.dropback.sum()) / n, 1)}
    return out


def league_baselines(d: pd.DataFrame) -> dict:
    ps = d[d.pass_play]; run = d[d.play_type.eq("run")]; db = d[d.dropback]; pdb = db[db.passer_player_id.notna()]; att = d[d.pass_att]   # pdb: the dropbacks a passer's own rates are counted on (scrambles are his runs)
    tg = ps[ps.receiver_player_id.notna()]
    return {"ypt": round(float(ps.yards_gained.fillna(0).mean()), 2), "epa_pt": round(float(ps.epa.mean()), 3), "catch": round(float(tg.complete_pass.fillna(0).mean()), 4), "ypc": round(float(run.yards_gained.fillna(0).mean()), 2), "ypd": round(float(pdb.pass_yds.mean()), 2),
            "td_pt": round(float(tg.pass_touchdown.fillna(0).mean()), 4), "td_pc": round(float(run.rush_touchdown.fillna(0).mean()), 4), "td_db": round(float(pdb.pass_touchdown.fillna(0).mean()), 4), "int_db": round(float(pdb.interception.fillna(0).mean()), 4),
            "comp_pp": round(float(att.complete_pass.fillna(0).mean()), 4), "att_rate": round(float(db.pass_play.mean()), 4),
            "man": round(float(ps[ps.cov_known].man.mean()), 3) if ps.cov_known.any() else None, "pressure": (round(float(db.pressure.mean()), 3) if db.pressure.notna().any() else None), "heavy_box": (round(float((run.box >= 8).mean()), 3) if run.box.notna().any() else None)}


TACKLE_COLS = ["solo_tackle_1_player_id", "solo_tackle_2_player_id", "assist_tackle_1_player_id", "assist_tackle_2_player_id", "assist_tackle_3_player_id", "assist_tackle_4_player_id", "tackle_with_assist_1_player_id", "tackle_with_assist_2_player_id"]


def defender_games(seasons=range(2016, 2027), force: bool = False) -> pd.DataFrame:
    """One row per defender and game from the raw play-by-play: tackles plus assists as the books count them (every
    solo, assist and tackle-with-assist credit), solo tackles, sacks (half sacks as 0.5), interceptions, passes
    defended, and the offense's plays he was on the field against (the team's plays faced). Cached in
    data/processed/def_games.parquet; rebuilt when the newest season's play-by-play is newer than the cache."""
    out = OUT / "def_games.parquet"; files = [RAW / "pbp" / f"play_by_play_{s}.parquet" for s in seasons]; files = [f for f in files if f.exists()]
    if out.exists() and not force and (not files or out.stat().st_mtime >= max(f.stat().st_mtime for f in files)):   # no raw play-by-play here (a job without the raw cache): the cache is the best there is
        return pd.read_parquet(out)
    rows = []
    for f in files:
        cols = ["season", "week", "game_id", "posteam", "defteam", "play_type", "sack_player_id", "half_sack_1_player_id", "half_sack_2_player_id", "interception_player_id", "pass_defense_1_player_id", "pass_defense_2_player_id"] + TACKLE_COLS
        d = pd.read_parquet(f, columns=cols); d = d[d.play_type.isin(["pass", "run"]) & d.defteam.notna()]
        plays = d.groupby(["season", "week", "game_id", "defteam"]).size().rename("plays_faced").reset_index()
        parts = []
        for c in TACKLE_COLS: parts.append(d[["season", "week", "game_id", "defteam", c]].rename(columns={c: "pid"}).dropna().assign(tk=1.0, solo=float(c.startswith("solo")), sack=0.0, int_=0.0, pd_=0.0))
        parts.append(d[["season", "week", "game_id", "defteam", "sack_player_id"]].rename(columns={"sack_player_id": "pid"}).dropna().assign(tk=0.0, solo=0.0, sack=1.0, int_=0.0, pd_=0.0))
        for c in ["half_sack_1_player_id", "half_sack_2_player_id"]: parts.append(d[["season", "week", "game_id", "defteam", c]].rename(columns={c: "pid"}).dropna().assign(tk=0.0, solo=0.0, sack=0.5, int_=0.0, pd_=0.0))
        parts.append(d[["season", "week", "game_id", "defteam", "interception_player_id"]].rename(columns={"interception_player_id": "pid"}).dropna().assign(tk=0.0, solo=0.0, sack=0.0, int_=1.0, pd_=0.0))
        for c in ["pass_defense_1_player_id", "pass_defense_2_player_id"]: parts.append(d[["season", "week", "game_id", "defteam", c]].rename(columns={c: "pid"}).dropna().assign(tk=0.0, solo=0.0, sack=0.0, int_=0.0, pd_=1.0))
        t = pd.concat(parts).groupby(["season", "week", "game_id", "defteam", "pid"]).agg(tackles=("tk", "sum"), solo=("solo", "sum"), sacks=("sack", "sum"), ints=("int_", "sum"), pd=("pd_", "sum")).reset_index().merge(plays, on=["season", "week", "game_id", "defteam"])
        rows.append(t)
    g = pd.concat(rows, ignore_index=True); g.to_parquet(out, index=False); return g


def kicker_games(seasons) -> pd.DataFrame:
    """One row per kicker and game from the raw play-by-play: field goals made and tried, extra points made and tried,
    kicking points (3 x field goals + extra points)."""
    parts = []
    for sn in seasons:
        f = RAW / "pbp" / f"play_by_play_{sn}.parquet"
        if not f.exists(): continue
        p = pd.read_parquet(f, columns=["game_id", "season", "week", "posteam", "field_goal_attempt", "field_goal_result", "extra_point_attempt", "extra_point_result", "kicker_player_id"])
        k = p[((p.field_goal_attempt == 1) | (p.extra_point_attempt == 1)) & p.kicker_player_id.notna()].copy()
        k["fgm"] = (k.field_goal_result == "made").astype(float); k["fga"] = (k.field_goal_attempt == 1).astype(float); k["xpm"] = (k.extra_point_result == "good").astype(float); k["xpa"] = (k.extra_point_attempt == 1).astype(float)
        parts.append(k.groupby(["game_id", "season", "week", "posteam", "kicker_player_id"]).agg(fgm=("fgm", "sum"), fga=("fga", "sum"), xpm=("xpm", "sum"), xpa=("xpa", "sum")).reset_index())
    if not parts: return pd.DataFrame(columns=["game_id", "season", "week", "team", "player_id", "fgm", "fga", "xpm", "xpa", "pts"])
    kg = pd.concat(parts, ignore_index=True).rename(columns={"posteam": "team", "kicker_player_id": "player_id"}); kg["pts"] = 3 * kg.fgm + kg.xpm
    return kg


def kickers(kg: pd.DataFrame, names: dict, season: int, week: int) -> dict:
    """Per team as of (season, week): kicking points and field goals per game decayed DECAY per game back over the
    team's games (the round-9 inputs), and each kicker's own line for the card."""
    a = kg[((kg.season < season) | ((kg.season == season) & (kg.week < week))) & (kg.season >= season - 1)]
    teams = {}
    for team, g in a.groupby("team"):
        per = g.groupby(["season", "week", "game_id"]).agg(pts=("pts", "sum"), fgm=("fgm", "sum"), fga=("fga", "sum")).reset_index().sort_values(["season", "week"], ascending=False)
        w = DECAY ** np.arange(len(per)); teams[team] = {"pts_dec": round(float((per.pts.values * w).sum() / w.sum()), 2), "fgm_dec": round(float((per.fgm.values * w).sum() / w.sum()), 3), "games": int(len(per))}
    players = {}
    for pid, g in a.groupby("player_id"):
        g = g.sort_values(["season", "week"]).tail(WINDOW); n = int(len(g))
        players[pid] = {"name": names.get(pid, (pid, ""))[0], "team": g.team.iloc[-1], "games": n, "pts_pg": round(float(g.pts.sum() / n), 2), "fgm": int(g.fgm.sum()), "fga": int(g.fga.sum()), "fg_pct": (round(float(g.fgm.sum() / g.fga.sum()), 3) if g.fga.sum() else None), "xpm": int(g.xpm.sum()), "xpa": int(g.xpa.sum())}
    return {"teams": teams, "players": players}


def project_kicker(team: str, KK: dict, roster: pd.DataFrame, margin: float | None, total: float | None, mk: pd.DataFrame | None) -> list:
    """The team's kicker (the roster's K) by the round-9 rule: his team's decayed kicking rate and the implied total."""
    ro = roster[(roster.team == team) & (roster.position == "K")] if len(roster) and "position" in roster else pd.DataFrame()
    tm = KK["teams"].get(team); me = 0.0 if margin is None or pd.isna(margin) else float(margin); tt = ((GS_TOTAL if total is None or pd.isna(total) else float(total)) + me) / 2
    OUT_WORDS = ("Out", "Doubtful", "IR", "PUP", "Suspended", "Exempt", "NFI", "Retired", "not on roster")
    rows = []
    for r in ro.itertuples():
        if tm is None: break
        st = (r.roster if isinstance(r.roster, str) and r.roster != "Active" else (r.report if isinstance(r.report, str) else "")) or ""; is_out = any(st.startswith(w) for w in OUT_WORDS)
        p = KK["players"].get(r.player_id, {"name": r.name, "games": 0, "pts_pg": None, "fgm": 0, "fga": 0, "fg_pct": None, "xpm": 0, "xpa": 0})
        a, b, c = KICK["pts"]; pts = a + b * tm["pts_dec"] + c * tt; a2, b2, c2 = KICK["fgm"]; fgm = a2 + b2 * tm["fgm_dec"] + c2 * tt
        rows.append({"player_id": r.player_id, "name": p["name"], "pos": "K", "status": st, "out": is_out, "games": p["games"], "pts_pg": p["pts_pg"], "fgm": p["fgm"], "fga": p["fga"], "fg_pct": p["fg_pct"], "xpm": p["xpm"], "xpa": p["xpa"],
                     "team_pts_dec": tm["pts_dec"], "team_fgm_dec": tm["fgm_dec"], "team_games": tm["games"], "implied_total": round(tt, 2), "proj_kick_points": round(pts, 1), "proj_field_goals": round(fgm, 2)})
    rows.sort(key=lambda r: (r["out"], -(r["games"] or 0)))
    rows = rows[:1]; attach_all_markets(rows, mk)
    return rows


def defenders(dg: pd.DataFrame, names: dict, season: int, week: int) -> dict:
    """Every defender's profile as of the week from the defender game table: last-17 tackles a game, solo, sacks,
    interceptions, passes defended; his decayed share of his team's tackles; the team's tackles per play faced."""
    a = dg[((dg.season < season) | ((dg.season == season) & (dg.week < week))) & (dg.season >= season - 1)].copy()
    tm = a.groupby(["defteam", "season", "week", "game_id"]).agg(team_tk=("tackles", "sum")).reset_index(); a = a.merge(tm, on=["defteam", "season", "week", "game_id"])
    tpp = {}
    for t, g in a.groupby("defteam"):
        gg = g.drop_duplicates("game_id").sort_values(["season", "week"]).tail(WINDOW); tpp[t] = round(float(gg.team_tk.sum() / max(gg.plays_faced.sum(), 1)), 3)
    out = {}
    for pid, g in a.groupby("pid"):
        g = g.sort_values(["season", "week"]); last = g.tail(WINDOW)
        if len(last) < 3: continue
        w = DEF_DECAY ** np.arange(len(g))[::-1]; share = float((g.tackles * w).sum() / max((g.team_tk * w).sum(), 1e-9))
        n = int(len(last)); team = g.defteam.iloc[-1]
        out[pid] = {"name": names.get(pid, (pid, ""))[0], "pos": names.get(pid, ("", ""))[1], "team": team, "games": n, "tackles_pg": round(float(last.tackles.mean()), 2), "solo_pg": round(float(last.solo.mean()), 2), "sacks_pg": round(float(last.sacks.mean()), 2), "ints": int(last.ints.sum()), "pd": int(last.pd.sum()),
                    "share": round(share, 3), "sack_rate": round(float(last.sacks.sum() / max(last.plays_faced.sum(), 1)), 4), "faced": int(last.plays_faced.sum()), "team_tpp": tpp.get(team)}
    lg_sack = round(float(a.sacks.sum() / max(a.plays_faced.sum(), 1)), 5)
    return {"players": out, "league_sack_rate": lg_sack}


def project_defense(team: str, opp: str, DF: dict, V: dict, roster: pd.DataFrame, margin: float | None, total: float | None, mk: pd.DataFrame | None, VS: dict | None) -> list:
    """The team's defenders against the opponent's offense: tackles plus assists and sacks, by the round-7 rule."""
    ro = roster[roster.team == team].set_index("player_id") if len(roster) else pd.DataFrame(); ov = V.get(opp, {})
    om = None if margin is None or pd.isna(margin) else -float(margin)   # the opponent's expected margin
    opp_plays = game_script("rec", ov.get("pass_plays_pg", 0), om, total) + game_script("rush", ov.get("runs_pg", 0), om, total)
    OUT_WORDS = ("Out", "Doubtful", "IR", "PUP", "Suspended", "Exempt", "NFI", "Retired", "not on roster")
    rows = []
    for pid, p in DF["players"].items():
        if p["team"] != team or pid not in ro.index: continue
        r = ro.loc[pid]; st = (r.roster if isinstance(r.roster, str) and r.roster != "Active" else (r.report if isinstance(r.report, str) else "")) or ""; is_out = any(st.startswith(w) for w in OUT_WORDS)
        tk = p["share"] * (p["team_tpp"] or 0.95) * opp_plays; sk = (p["sack_rate"] * p["faced"] + K_SACK * DF["league_sack_rate"]) / (p["faced"] + K_SACK) * opp_plays
        hist = (VS or {}).get(("def", pid, opp))
        rows.append({"player_id": pid, "name": p["name"], "pos": p["pos"], "status": st, "out": is_out, "tackles_pg": p["tackles_pg"], "solo_pg": p["solo_pg"], "share": p["share"], "games": p["games"], "sacks_pg": p["sacks_pg"], "ints": p["ints"], "pd": p["pd"],
                     "proj_tackles_mean": round(tk, 1), "proj_tackles": round(tk * DEF_MED, 1), "proj_solo_tackles": round(tk * DEF_MED * (p["solo_pg"] / p["tackles_pg"] if p["tackles_pg"] else 0.6), 1), "proj_sacks": round(sk, 2), "opp_plays": round(opp_plays, 1), "vs_opp": vs_summary(hist)})
    rows.sort(key=lambda r: (r["out"], -r["proj_tackles"]))
    attach_market(rows, mk, [("def_tackles", "mkt_tackles")])
    rows = rows[:8]; attach_all_markets(rows, mk)
    return rows


def vs_defense(d: pd.DataFrame) -> dict:
    """Every player's games against each defense since 2016: {(kind, player, defteam): [{season, week, n, yds, td}, ...]},
    newest first. The card shows a player's record against the defense he faces this week."""
    out = {}
    for kind, mask, pcol, tdcol in [("rec", d.pass_play & d.receiver_player_id.notna(), "receiver_player_id", "pass_touchdown"), ("rush", d.play_type.eq("run") & d.rusher_player_id.notna(), "rusher_player_id", "rush_touchdown"), ("pass", d.dropback & d.passer_player_id.notna(), "passer_player_id", "pass_touchdown")]:
        t = d[mask]; g = t.groupby([pcol, "defteam", "season", "week"]).agg(n=("play_id", "count"), yds=("yards_gained", "sum"), td=(tdcol, "sum")).reset_index().sort_values(["season", "week"], ascending=False)
        for r in g.itertuples():
            out.setdefault((kind, getattr(r, pcol), r.defteam), []).append({"season": int(r.season), "week": int(r.week), "n": int(r.n), "yds": round(float(r.yds), 0), "td": int(r.td)})
    return out


def vs_offense(dg: pd.DataFrame, games: pd.DataFrame) -> dict:
    """Every defender's games against each offense: {("def", player, posteam): [{season, week, n (tackles), yds (sacks), td (ints)}, ...]}, newest first."""
    opp = games.set_index("game_id")[["home_team", "away_team"]]
    g = dg.merge(opp, left_on="game_id", right_index=True, how="inner"); g["opp"] = np.where(g.defteam == g.home_team, g.away_team, g.home_team)
    out = {}
    for r in g.sort_values(["season", "week"], ascending=False).itertuples():
        out.setdefault(("def", r.pid, r.opp), []).append({"season": int(r.season), "week": int(r.week), "n": int(r.tackles), "yds": float(r.sacks), "td": int(r.ints)})
    return out


def vs_summary(hist: list | None) -> dict | None:
    if not hist:
        return None
    n = len(hist)
    return {"games": n, "n_pg": round(sum(h["n"] for h in hist) / n, 1), "yds_pg": round(sum(h["yds"] for h in hist) / n, 1), "td": int(sum(h["td"] for h in hist)), "last": hist[:5]}


def _mix(a: dict | None, b: dict | None, rate: float | None, key: str, fallback: float) -> float:
    """a in look x rate + b outside it x (1 - rate), when both splits and the rate exist; else the fallback."""
    if a is None or b is None or rate is None:
        return fallback
    return a[key] * rate + b[key] * (1 - rate)


def _toward(v: float, allowed: float | None, league: float, w: float) -> float:
    return v if (allowed is None or not league) else v * (1 + w * (allowed / league - 1))


def _shrunk(rate: float, n: float, league: float, k: float) -> float:
    return (rate * n + k * league) / (n + k)


MARKET_LABEL = {"pass_yards": "Pass yds", "pass_td": "Pass TD", "pass_completions": "Completions", "pass_attempts": "Attempts", "pass_int": "INT thrown", "pass_longest": "Longest completion", "rush_yards": "Rush yds", "rush_attempts": "Rush att", "rush_rec_yards": "Rush + rec yds", "rush_longest": "Longest rush", "pass_rush_yards": "Pass + rush yds", "rec_targets": "Targets",
                "rec_catches": "Receptions", "rec_yards": "Rec yds", "rec_longest": "Longest rec", "anytime_td": "Anytime TD", "def_tackles": "Tackles + ast (defense)", "def_solo_tackles": "Solo tackles", "def_sacks": "Sacks", "def_int": "INT", "kick_points": "Kicking pts", "field_goals": "Field goals"}


def attach_all_markets(rows: list, mk: pd.DataFrame, season: int | None = None) -> set:
    """Every market the book posts for each listed player: [{stat, line, books, over, under}] on the row. Returns the
    keys matched, so the leftovers (kickers, players without a profile) can be listed on their own."""
    matched = set()
    if mk is None or not len(mk):
        for r in rows: r["markets"] = []
        return matched
    from .props_lines import norm_name
    for r in rows:
        k = norm_name(r["name"]); hit = mk[mk.key == k]; matched.add(k)
        r["markets"] = [{"stat": h.stat, "line": (None if pd.isna(h.line) else float(h.line)), "chance": (chance_over(h.stat, r.get(_OWN.get(h.stat, "")), None if pd.isna(h.line) else float(h.line), season) if season is not None else None), "books": int(h.books), "over": (None if pd.isna(h.over_price) else int(h.over_price)), "under": (None if pd.isna(h.under_price) else int(h.under_price)), "open": (None if pd.isna(h.open_line) else float(h.open_line)), "open_over": (None if pd.isna(h.open_over) else int(h.open_over)), "pulls": int(h.pulls)} for h in hit.itertuples()]
    return matched


def attach_market(rows: list, mk: pd.DataFrame, pairs: list, season: int | None = None) -> None:
    """Put the closing book line beside each projection: pairs = [(stat in the log, key on the row)], matched on the
    player's normalised name. line, books and the prices; the anytime-touchdown price as an implied probability."""
    if mk is None or not len(mk):
        return
    from .props_lines import norm_name
    for r in rows:
        k = norm_name(r["name"])
        for stat, key in pairs:
            hit = mk[(mk.stat == stat) & (mk.key == k)]
            if not len(hit):
                continue
            h = hit.iloc[0]
            if stat == "anytime_td":
                p_ = h.over_price
                r["mkt_td_price"] = None if pd.isna(p_) else int(p_); r["mkt_td_prob"] = None if pd.isna(p_) else round(implied(p_), 3)
            else:
                r[key] = None if pd.isna(h.line) else float(h.line); r[key + "_books"] = int(h.books)
                _own = r.get({"mkt_rec_yards": "proj_rec_yards", "mkt_catches": "proj_catches", "mkt_rush_yards": "proj_rush_yards", "mkt_pass_yards": "proj_pass_yards", "mkt_tackles": "proj_tackles"}[key])
                r[key + "_chance"] = chance_over(stat, _own, r[key], season) if season is not None else None   # P(over the book line), round 18
                cut = (PROP_EDGE or {}).get(stat); proj = r.get({"mkt_rec_yards": "proj_rec_yards", "mkt_catches": "proj_catches", "mkt_rush_yards": "proj_rush_yards", "mkt_pass_yards": "proj_pass_yards", "mkt_tackles": "proj_tackles"}[key])
                if cut is not None and proj is not None and not pd.isna(h.line) and abs(proj - float(h.line)) >= cut:
                    r[key + "_flag"] = "over" if proj > h.line else "under"


def implied(price: float) -> float:
    """American price -> implied probability, vig included."""
    price = float(price)
    return 100 / (price + 100) if price > 0 else -price / (-price + 100)


def reconcile(rows: list, kind: str, exp_pts: float | None, yds_key: str, td_key: str, starter_only: bool = False) -> dict:
    """Scale the players' yards and touchdowns toward the team's expected totals from the game model's expected points:
    factor = 1 + w x (expected / what the players add up to - 1), the ratio clipped to [0.5, 2] as in the backtest. The
    sum is over the players who are playing (the starter alone for passing); every row gets the factor, so a listed-out
    player's "would have" line moves with his team."""
    out = {"exp_pts": None if exp_pts is None or pd.isna(exp_pts) else round(float(exp_pts), 1), "yds_factor": 1.0, "td_factor": 1.0}
    if out["exp_pts"] is None or not rows:
        return out
    act = [r for r in rows if not r["out"]]; act = act[:1] if starter_only else act
    if not act:
        return out
    fy, ft = TEAM_FIT[kind]["yds"], TEAM_FIT[kind]["td"]; wy, wt = RECON_W[kind]["yds"], RECON_W[kind]["td"]
    exp_y, exp_t = fy[0] + fy[1] * exp_pts, ft[0] + ft[1] * exp_pts; sum_y, sum_t = sum(r[yds_key] for r in act), sum(r[td_key] for r in act)
    fac_y = 1 + wy * (min(max(exp_y / sum_y, 0.5), 2.0) - 1) if sum_y > 0 else 1.0; fac_t = 1 + wt * (min(max(exp_t / sum_t, 0.5), 2.0) - 1) if sum_t > 0 else 1.0
    for r in rows:
        r[yds_key] = round(r[yds_key] * fac_y, 1); r[yds_key + "_mean"] = round(r[yds_key + "_mean"] * fac_y, 1); r[td_key] = round(r[td_key] * fac_t, 3)
    out.update({"team_yds_exp": round(exp_y, 1), "team_yds_players": round(sum_y, 1), "yds_factor": round(fac_y, 3), "team_td_exp": round(exp_t, 2), "team_td_players": round(sum_t, 2), "td_factor": round(fac_t, 3)})
    return out


def project_game(team: str, opp: str, R: dict, RU: dict, Q: dict, D: dict, V: dict, L: dict, roster: pd.DataFrame, margin: float | None = None, total: float | None = None, wind: float | None = None, mk: pd.DataFrame | None = None, exp_pts: float | None = None, VS: dict | None = None, starter: str | None = None, SN: dict | None = None, recent: set | None = None, season: int | None = None, sit: dict | None = None, SQ: dict | None = None) -> dict:
    """One offense against one defense: every rostered receiver, rusher and QB with a profile, projected. margin is the
    team's expected margin from the closing spread (positive when favoured), total the closing total, wind the mph at
    kickoff (None in a dome or before a usable forecast), exp_pts the game model's expected points for the team. sit: this
    game's situational inputs for the team (props_sit.week_inputs), SQ: each player's q (props_sit.load_state); without
    either, no SIT factor."""
    dd = D.get(opp, {}); base = V.get(team, {}); ro = roster[roster.team == team].set_index("player_id") if len(roster) else pd.DataFrame()
    me = 0.0 if margin is None or pd.isna(margin) else float(margin)
    vol = dict(base); vol.update({"pass_plays": round(game_script("rec", base.get("pass_plays_pg", 0), margin, total, dd.get("pass_plays_pg")), 1), "runs": round(game_script("rush", base.get("runs_pg", 0), margin, total, dd.get("runs_pg")), 1), "dropbacks": round(game_script("pass", base.get("dropbacks_pg", 0), margin, total, dd.get("dropbacks_pg")), 1), "margin": (None if margin is None or pd.isna(margin) else float(margin)), "total": (None if total is None or pd.isna(total) else float(total)), "wind": (None if wind is None or pd.isna(wind) else float(wind)), "wind_factor_pass": round(wind_factor("pass", wind), 3)})
    def status(pid):
        if pid not in ro.index: return "not on roster"
        r = ro.loc[pid]; lab = r.roster if isinstance(r.roster, str) and r.roster != "Active" else (r.report if isinstance(r.report, str) else "")
        return lab or ""
    OUT_WORDS = ("Out", "Doubtful", "IR", "PUP", "Suspended", "Exempt", "NFI", "Retired", "not on roster")
    rec = []
    for pid, p in R.items():
        if p["team"] != team or pid not in ro.index: continue
        st = status(pid); is_out = any(st.startswith(w) for w in OUT_WORDS)
        ypt_s = _shrunk(p["ypt"], p["targets"], L["ypt"], K["rec"]); ypt = _toward(ypt_s, dd.get("ypt_allowed"), L["ypt"], W["rec"])
        ypt_mix = _mix(p["vs_man"], p["vs_zone"], dd.get("man"), "yds", p["ypt"])   # reading only
        tdp = td_prior("rec", p.get("pos"), L["td_pt"])   # round 14: the league's rate x his position's factor
        catch_s = _shrunk(p["catch"], p["targets"], L["catch"], K_CATCH); td_s = _shrunk(p["td_pt"], p["targets"], tdp, K_TD["rec"]) * (1 + TD_MARGIN["rec"] * me)
        rec.append({"player_id": pid, "name": p["name"], "pos": p.get("pos", ""), "vs_opp": vs_summary((VS or {}).get(("rec", pid, opp))), "status": st, "out": is_out, "targets_pg": p["targets_pg"], "share": p["share"], "share_td": p.get("share_td", p["share"]), "share_yds": p.get("share_yds", p["share"]), "catch": p["catch"], "catch_shrunk": round(catch_s, 3), "td_pt": p["td_pt"], "td_prior": round(tdp, 4), "td_pt_proj": round(td_s, 4),
                    "ypt": p["ypt"], "ypt_shrunk": round(ypt_s, 2), "ypt_mix": round(ypt_mix, 2), "proj_ypt": round(ypt, 2),
                    "vs_man": p["vs_man"], "vs_zone": p["vs_zone"], "vs_press": p["vs_press"], "adot": p["adot"], "games": p["games"], "targets": p["targets"], "longest_dec": p["longest_dec"], "ypg": p["ypg"], "proj_rec_longest": p["proj_longest"]})
    # his share x the team's game-script pass plays (97%: the rest are throwaways and spikes). An absent teammate's share was
    # not handed to the others (every pro-rata form lost on both windows, round 10) until round 18: an out starter's share_yds,
    # a fitted fraction of it, goes to his same-position teammates (absorb)
    absorb(rec, "rec", recent or set())
    # round 14: the touchdown volume is his share over every game he was active for (a game without a target counts 0), so a
    # backup's empty games pull his volume down. Round 17: the yards and receptions volume moved three quarters of the way to
    # the same share (share_yds; the touch-games share alone had set a backup's line from his good days)
    for r in rec:
        tg = r["share_yds"] * vol["pass_plays"] * TARGETABLE; tg_td = r["share_td"] * vol["pass_plays"] * TARGETABLE; mean = tg * r["proj_ypt"]; m = med_factor("rec", mean)   # round 15: the median factor rises with his mean
        r.update({"proj_targets": round(tg, 1), "proj_targets_td": round(tg_td, 1), "proj_catches_mean": round(tg * r["catch_shrunk"], 1), "proj_catches": round(tg * r["catch_shrunk"] * MED_CATCH, 1), "med_factor": round(m, 3), "proj_rec_yards_mean": round(mean, 1), "proj_rec_yards": round(mean * m, 1), "proj_rec_td": round(tg_td * r["td_pt_proj"], 3)})
    rec.sort(key=lambda r: (r["out"], -r["proj_targets"]))
    rus = []
    for pid, p in RU.items():
        if p["team"] != team or pid not in ro.index: continue
        st = status(pid); is_out = any(st.startswith(w) for w in OUT_WORDS)
        ypc_s = _shrunk(p["ypc"], p["carries"], L["ypc"], K["rush"]); ypc = _toward(ypc_s, dd.get("ypc_allowed"), L["ypc"], W["rush"])
        ypc_mix = _mix(p["heavy"], p["light"] if p["light"] else p["mid"], dd.get("heavy_box"), "yds", p["ypc"])   # reading only
        tdp = td_prior("rush", p.get("pos"), L["td_pc"])   # round 14: a quarterback's carry scores more often than a back's, a wideout's less
        td_s = _shrunk(p["td_pc"], p["carries"], tdp, K_TD["rush"]) * (1 + TD_MARGIN["rush"] * me)
        rus.append({"player_id": pid, "name": p["name"], "pos": p.get("pos", ""), "vs_opp": vs_summary((VS or {}).get(("rush", pid, opp))), "status": st, "out": is_out, "carries_pg": p["carries_pg"], "share": p["share"], "share_td": p.get("share_td", p["share"]), "share_yds": p.get("share_yds", p["share"]), "td_pc": p["td_pc"], "td_prior": round(tdp, 4), "td_pc_proj": round(td_s, 4), "ypc": p["ypc"], "ypc_shrunk": round(ypc_s, 2), "ypc_mix": round(ypc_mix, 2), "proj_ypc": round(ypc, 2),
                    "light": p["light"], "heavy": p["heavy"], "games": p["games"], "carries": p["carries"], "longest_dec": p["longest_dec"], "ypg": p["ypg"], "proj_rush_longest": p["proj_longest"]})
    absorb(rus, "rush", recent or set())   # round 18
    for r in rus:
        ca = r["share_yds"] * vol["runs"]; ca_td = r["share_td"] * vol["runs"]; mean = ca * r["proj_ypc"]; m = med_factor("rush", mean)   # round 14: the touchdown volume from his share over every game he was active for; round 17: the yards line's too (SHARE_A_W["rush"] = 1, so the two agree); flat MED["rush"] (round 15 found no curve worth it for rushing)
        r.update({"proj_carries": round(ca, 1), "proj_carries_td": round(ca_td, 1), "med_factor": round(m, 3), "proj_rush_yards_mean": round(mean, 1), "proj_rush_yards": round(mean * m, 1), "proj_rush_td": round(ca_td * r["td_pc_proj"], 3)})
    rus.sort(key=lambda r: (r["out"], -r["proj_carries"]))
    qbs = []
    for pid, p in Q.items():
        if p["team"] != team or pid not in ro.index: continue
        st = status(pid); is_out = any(st.startswith(w) for w in OUT_WORDS)
        ypd_s = _shrunk(p["ypd"], p["dropbacks"], L["ypd"], K["pass"]); ypd = _toward(ypd_s, dd.get("ypd_allowed"), L["ypd"], W["pass"])
        epa_mix = _mix(p["press"], p["clean"], dd.get("pressure"), "epa", p["epa_db"])   # reading only
        dbs = vol["dropbacks"] if base else p["dropbacks_pg"]
        td_s = _shrunk(p["td_db"], p["dropbacks"], L["td_db"], K_TD["pass"]) * (1 + TD_MARGIN["pass"] * me)
        att = dbs * (1 - p["sack_rate"]); comp = att * _shrunk(p.get("comp") if p.get("comp") is not None else L["comp_pp"], p["dropbacks"], L["comp_pp"], 100.0)
        mean = dbs * ypd * wind_factor("pass", wind); m = med_factor("pass", mean)   # round 15: the median factor rises with his mean (the wind is in the mean, as in the backtest)
        qbs.append({"player_id": pid, "name": p["name"], "pos": p.get("pos", ""), "vs_opp": vs_summary((VS or {}).get(("pass", pid, opp))), "status": st, "out": is_out, "proj_pass_attempts": round(att, 1), "proj_pass_completions": round(comp, 1), "td_db": p["td_db"], "int_db": p["int_db"], "sack_rate": p["sack_rate"], "comp": p.get("comp"), "dropbacks_pg": p["dropbacks_pg"], "proj_dropbacks": round(dbs, 1), "epa_db": p["epa_db"], "epa_mix": round(epa_mix, 3), "ypd": p["ypd"], "ypd_shrunk": round(ypd_s, 2), "proj_ypd": round(ypd, 2),
                    "med_factor": round(m, 3), "proj_pass_yards_mean": round(mean, 1), "proj_pass_yards": round(mean * m, 1), "td_db_proj": round(td_s, 4), "proj_pass_td": round(dbs * td_s, 3), "proj_int": round(dbs * L["int_db"], 3), "press": p["press"], "clean": p["clean"], "blitz": p["blitz"], "noblitz": p["noblitz"], "vs_man": p["vs_man"], "vs_zone": p["vs_zone"], "games": p["games"], "dropbacks": p["dropbacks"], "longest_dec": p["longest_dec"], "ypg": p["ypg"], "proj_pass_longest": p["proj_longest"]})
    # the starter is the schedule's named QB when it names one (as the game model uses), else the most dropbacks per game
    qbs.sort(key=lambda r: (r["out"], 0 if (starter and r["player_id"] == starter) else 1, -r["dropbacks_pg"]))
    for u in rus: u["proj_rush_attempts"] = u["proj_carries"]
    recon = {"rec": reconcile(rec, "rec", exp_pts, "proj_rec_yards", "proj_rec_td"), "rush": reconcile(rus, "rush", exp_pts, "proj_rush_yards", "proj_rush_td"), "pass": reconcile(qbs, "pass", exp_pts, "proj_pass_yards", "proj_pass_td", starter_only=True)}
    # round 13: this week's injury report and his snap trend, on the yards lines (after the team scaling, as in the backtest)
    for kind, rows_, key in (("rec", rec, "proj_rec_yards"), ("rush", rus, "proj_rush_yards")):
        for r in rows_:
            rr = ro.loc[r["player_id"]] if r["player_id"] in ro.index else None
            grp = inj_group(getattr(rr, "report", None), getattr(rr, "practice", None)) if rr is not None else "none"
            s3, s10 = (SN or {}).get(r["player_id"], (None, None)); sr = snap_ratio(s3, s10)
            fac = INJ_F[kind].get(grp, 1.0) * (1 + SNAP_W[kind] * (sr - 1))
            r.update({"inj_group": grp, "inj_factor": INJ_F[kind].get(grp, 1.0), "snap_ratio": round(sr, 3), "r13_factor": round(fac, 3)})
            r[key] = round(r[key] * fac, 1); r[key + "_mean"] = round(r[key + "_mean"] * fac, 1)
            if kind in INJ_TD: r[f"proj_{kind}_td"] = round(r[f"proj_{kind}_td"] * INJ_F[kind].get(grp, 1.0), 3)   # round 14: the injury report on receiving touchdowns too (not the snap trend: worse at every weight)
    # round 3 of the props (29 Sep 2026): the situational factors SIT on the receptions, targets, receiving and rushing
    # touchdowns, rushing yards and passing touchdowns lines, after the injury/snap factor, as the by-season backtest orders them
    if sit is not None and SQ is not None:
        oo = {"rec": out_shares(rec, "rec", recent or set()), "rush": out_shares(rus, "rush", recent or set())}
        same = {"WR": oo["rec"].get("WR", 0.0), "TE": oo["rec"].get("TE", 0.0), "RB": oo["rush"].get("RB", 0.0), "FB": oo["rush"].get("RB", 0.0), "HB": oo["rush"].get("RB", 0.0)}
        z = dict(sit, same_out=0.0, rb_out=oo["rush"].get("RB", 0.0))
        def q_of(kind, pid, stat):
            return {i: (SQ[(kind, i)][0].get(pid, SQ[(kind, i)][1]) if (kind, i) in SQ else None) for i, _ in SIT[stat]}
        for rows_, stats, keys in ((rec, ("rec_catches", "rec_targets", "rec_td"), {"rec_catches": ("proj_catches", "proj_catches_mean"), "rec_targets": ("proj_targets",), "rec_td": ("proj_rec_td",)}),
                                   (rus, ("rush_yards", "rush_td"), {"rush_yards": ("proj_rush_yards", "proj_rush_yards_mean"), "rush_td": ("proj_rush_td",)}),
                                   (qbs, ("pass_td",), {"pass_td": ("proj_pass_td",)})):
            for r in rows_:
                zr = dict(z, same_out=same.get(r.get("pos", ""), 0.0)); fac = {st: sit_factor(st, zr, q_of(SIT_KIND[st], r["player_id"], st)) for st in stats}
                for st in stats:
                    for key in keys[st]: r[key] = round(r[key] * fac[st], 3 if key.endswith("_td") else 1)
                r["sit_factor"] = {st: round(f_, 4) for st, f_ in fac.items()}
                # each input behind the factor, for the card's calculation (30 Sep 2026, Matt: where do I see these): [input, this game, his usual, b]
                r["sit_terms"] = {st: [[i, round(float(zr[i]), 6), round(float(qv), 6), b] for i, b in SIT[st]
                                       for qv in [q_of(SIT_KIND[st], r["player_id"], st).get(i)]
                                       if zr.get(i) is not None and qv is not None and not pd.isna(zr[i]) and not pd.isna(qv)] for st in stats}
        vol["sit"] = {k: (None if v is None or pd.isna(v) else round(float(v), 4)) for k, v in z.items()} | {"same_out_by_group": {k: round(v, 3) for k, v in same.items() if k in ("WR", "TE", "RB")}}
    for r in rec: r["proj_td_any"] = round(1 - np.exp(-(r["proj_rec_td"] + next((u["proj_rush_td"] for u in rus if u["player_id"] == r["player_id"]), 0.0))), 3)
    for u in rus: u["proj_td_any"] = round(1 - np.exp(-(u["proj_rush_td"] + next((r["proj_rec_td"] for r in rec if r["player_id"] == u["player_id"]), 0.0))), 3)
    for q in qbs:
        u = next((u for u in rus if u["player_id"] == q["player_id"]), None); q["proj_rush_yards"] = u["proj_rush_yards"] if u else None; q["proj_rush_td"] = u["proj_rush_td"] if u else 0.0; q["proj_td_any"] = round(1 - np.exp(-q["proj_rush_td"]), 3); q["proj_pass_rush_yards"] = round(q["proj_pass_yards"] + (q["proj_rush_yards"] or 0.0), 1)
    for r in rec: r["proj_rush_rec_yards"] = round(r["proj_rec_yards"] + next((u["proj_rush_yards"] for u in rus if u["player_id"] == r["player_id"]), 0.0), 1)
    for u in rus: u["proj_rush_rec_yards"] = round(u["proj_rush_yards"] + next((r["proj_rec_yards"] for r in rec if r["player_id"] == u["player_id"]), 0.0), 1)
    attach_market(rec, mk, [("rec_yards", "mkt_rec_yards"), ("rec_catches", "mkt_catches"), ("anytime_td", "mkt_td")], season)
    attach_market(rus, mk, [("rush_yards", "mkt_rush_yards"), ("anytime_td", "mkt_td")], season)
    attach_market(qbs, mk, [("pass_yards", "mkt_pass_yards")], season)
    matched = attach_all_markets(rec, mk, season) | attach_all_markets(rus, mk, season) | attach_all_markets(qbs, mk, season)
    return {"defense": dd, "volume": vol, "recon": recon, "qb": qbs[:2], "receivers": rec[:8], "rushers": rus[:4], "market_ts": (str(mk.ts.iloc[0]) if mk is not None and len(mk) else None), "_matched": sorted(matched)}


MARKET_STATS = {k: k for k in ["rec_yards", "rush_yards", "pass_yards", "rec_catches", "def_tackles", "pass_td", "pass_int", "pass_attempts", "pass_completions", "rush_attempts", "rush_rec_yards", "def_sacks", "def_solo_tackles", "rec_targets", "pass_rush_yards", "rec_longest", "rush_longest", "pass_longest", "kick_points", "field_goals"]}


def grade_market(graded: pd.DataFrame, run_at: str) -> pd.DataFrame | None:
    """Every graded projection with a closing book line: the line, the side the projection took (over when above the
    line, under when below), and the result against what happened. Also the book's own error, so the two can be
    compared. Anytime touchdown: the projection's chance of a score against the book's implied price, graded on
    whether he scored. Kept in data/tracker/props_vs_market.csv."""
    from .props_lines import load_log, closing, norm_name
    log = load_log()
    if not len(log) or graded is None or not len(graded):
        return None
    done = pd.read_csv(TR / "props_vs_market.csv") if (TR / "props_vs_market.csv").exists() else pd.DataFrame(columns=["game_id", "player_id", "stat"])
    rows = []
    for gid, g in graded.groupby("game_id"):
        mk = closing(log, gid)
        if not len(mk): continue
        td = g[g.stat.isin(["rec_td", "rush_td"])].groupby(["player_id", "name", "team", "season", "week"]).agg(proj=("proj", "sum"), actual=("actual", "sum")).reset_index()
        for r in g[g.stat.isin(MARKET_STATS)].itertuples():
            if ((done.game_id == gid) & (done.player_id == r.player_id) & (done.stat == r.stat)).any(): continue
            hit = mk[(mk.stat == r.stat) & (mk.key == norm_name(r.name))]
            if not len(hit) or pd.isna(hit.iloc[0].line): continue
            h = hit.iloc[0]; ch = chance_over(r.stat, r.proj, float(h.line), int(r.season))   # round 18: the calibrated chance of the over
            side = ("over" if ch > 0.5 else ("under" if ch < 0.5 else "none")) if ch is not None else ("over" if r.proj > h.line else ("under" if r.proj < h.line else "none"))
            res = "push" if r.actual == h.line else ("win" if (r.actual > h.line) == (side == "over") else "loss") if side != "none" else "none"
            rows.append({"season": r.season, "week": r.week, "game_id": gid, "team": r.team, "player_id": r.player_id, "name": r.name, "stat": r.stat, "proj": r.proj, "line": float(h.line), "books": int(h.books), "over_price": h.over_price, "under_price": h.under_price, "side": side, "chance": ch, "edge": round(float(r.proj - h.line), 2), "actual": r.actual, "result": res, "proj_error": round(float(r.proj - r.actual), 2), "line_error": round(float(h.line - r.actual), 2), "graded_at": run_at})
        for r in td.itertuples():
            if ((done.game_id == gid) & (done.player_id == r.player_id) & (done.stat == "anytime_td")).any(): continue
            hit = mk[(mk.stat == "anytime_td") & (mk.key == norm_name(r.name))]
            if not len(hit) or pd.isna(hit.iloc[0].over_price): continue
            h = hit.iloc[0]; p_us = 1 - np.exp(-r.proj); p_bk = implied(h.over_price); side = "yes" if p_us > p_bk else "no"
            res = "win" if (r.actual >= 1) == (side == "yes") else "loss"
            rows.append({"season": r.season, "week": r.week, "game_id": gid, "team": r.team, "player_id": r.player_id, "name": r.name, "stat": "anytime_td", "proj": round(p_us, 3), "line": round(p_bk, 3), "books": int(h.books), "over_price": h.over_price, "under_price": None, "side": side, "edge": round(p_us - p_bk, 3), "actual": r.actual, "result": res, "proj_error": None, "line_error": None, "graded_at": run_at})
    if not rows: return None
    out = pd.concat([done, pd.DataFrame(rows)], ignore_index=True) if len(done) else pd.DataFrame(rows)
    TR.mkdir(parents=True, exist_ok=True); out.to_csv(TR / "props_vs_market.csv", index=False); return out


def market_summary(vm: pd.DataFrame) -> list[dict]:
    """Record against the closing line by stat, and by size of the edge: wins, losses, pushes, and the two errors."""
    out = []
    for stat, g in vm.groupby("stat"):
        g = g[g.side != "none"]
        buckets = [("all", g)] + ([(">= 5", g[g.edge.abs() >= 5]), (">= 10", g[g.edge.abs() >= 10])] if stat.endswith("yards") else [(">= 0.5", g[g.edge.abs() >= 0.5]), (">= 1", g[g.edge.abs() >= 1])] if stat in ("rec_catches", "def_tackles") else [(">= 0.05", g[g.edge.abs() >= 0.05])])
        for lab, x in buckets:
            if not len(x): continue
            w, l, p_ = int((x.result == "win").sum()), int((x.result == "loss").sum()), int((x.result == "push").sum())
            out.append({"stat": stat, "edge": lab, "n": int(len(x)), "wins": w, "losses": l, "pushes": p_, "pct": round(w / (w + l), 3) if w + l else None,
                        "proj_mae": (round(float(x.proj_error.abs().mean()), 2) if x.proj_error.notna().any() else None), "line_mae": (round(float(x.line_error.abs().mean()), 2) if x.line_error.notna().any() else None)})
    return out


def grade(d: pd.DataFrame, season: int, week: int, run_at: str) -> pd.DataFrame | None:
    """Grade every earlier week's projections that have not been graded, against the players' actual yards."""
    files = sorted(REP.glob(f"props_{season}_wk*.csv"))
    done = pd.read_csv(TR / "props_graded.csv") if (TR / "props_graded.csv").exists() else pd.DataFrame(columns=["game_id", "player_id", "stat"])
    rows = []
    for f in files:
        wk = int(f.stem.split("wk")[-1])
        if wk >= week: continue
        pr = pd.read_csv(f)
        plays = d[(d.season == season) & (d.week == wk)]
        if not len(plays): continue
        plays = plays.assign(lg=np.where(plays.play_type.eq("run"), plays.yards_gained.fillna(0.0), np.where(plays.complete_pass.fillna(0).eq(1), plays.yards_gained.fillna(0.0), 0.0)))   # the longest gain of the game: runs, or completed passes
        def agg(mask, col, val):   # val: the yards column (pass_yds for passers: the yards on completions, not net of sacks)
            return plays[mask].groupby(["game_id", col]).agg(yards=(val or "yards_gained", "sum"), catches=("complete_pass", "sum"), pass_td=("pass_touchdown", "sum"), rush_td=("rush_touchdown", "sum"), ints=("interception", "sum"), n=("play_id", "count"), longest=("lg", "max")).reset_index().rename(columns={col: "player_id"})
        ry = agg(plays.pass_play, "receiver_player_id", None); rr = agg(plays.play_type.eq("run"), "rusher_player_id", None); py = agg(plays.dropback, "passer_player_id", "pass_yds"); pa = agg(plays.pass_att, "passer_player_id", None)   # attempts: passes and spikes, not sacks
        rrr = rr.merge(ry[["game_id", "player_id", "yards"]].rename(columns={"yards": "rec_yds"}), on=["game_id", "player_id"], how="outer").fillna({"yards": 0, "rec_yds": 0, "n": 0}); rrr["both"] = rrr.yards + rrr.rec_yds
        prr = py.merge(rr[["game_id", "player_id", "yards"]].rename(columns={"yards": "rush_yds"}), on=["game_id", "player_id"], how="outer").fillna({"yards": 0, "rush_yds": 0, "n": 0}); prr["both"] = prr.yards + prr.rush_yds
        dgw = defender_games(); dgw = dgw[(dgw.season == season) & (dgw.week == wk)].rename(columns={"pid": "player_id"}); dgw["n"] = dgw.plays_faced
        kw = kicker_games([season]); kw = kw[kw.week == wk].copy(); kw["n"] = kw.fga + kw.xpa
        SRC = {"kick_points": (kw, "pts"), "field_goals": (kw, "fgm"), "rec_yards": (ry, "yards"), "rec_catches": (ry, "catches"), "rec_td": (ry, "pass_td"), "rush_yards": (rr, "yards"), "rush_td": (rr, "rush_td"), "pass_yards": (py, "yards"), "pass_td": (py, "pass_td"), "pass_int": (py, "ints"), "def_tackles": (dgw, "tackles"), "def_sacks": (dgw, "sacks"), "def_solo_tackles": (dgw, "solo"), "pass_attempts": (pa, "n"), "pass_completions": (pa, "catches"), "rush_attempts": (rr, "n"), "rush_rec_yards": (rrr, "both"), "rec_targets": (ry, "n"), "pass_rush_yards": (prr, "both"), "rec_longest": (ry, "longest"), "rush_longest": (rr, "longest"), "pass_longest": (pa, "longest")}
        played = set(plays.game_id)
        for _, r in pr.iterrows():
            if r.game_id not in played or ((done.game_id == r.game_id) & (done.player_id == r.player_id) & (done.stat == r.stat)).any(): continue
            src, col = SRC[r.stat]; hit = src[(src.game_id == r.game_id) & (src.player_id == r.player_id)]
            actual = float(hit[col].fillna(0).iloc[0]) if len(hit) else 0.0; vol_ = int(hit.n.iloc[0]) if len(hit) else 0
            rows.append({"season": season, "week": wk, "game_id": r.game_id, "team": r.team, "player_id": r.player_id, "name": r["name"], "stat": r.stat, "proj": r.proj, "proj_volume": r.proj_volume, "actual": actual, "actual_volume": vol_, "error": round(actual - r.proj, 3), "graded_at": run_at, "made": (r["made"] if "made" in pr.columns and isinstance(r.get("made"), str) else "live")})
    if not rows: return None
    g = pd.concat([done, pd.DataFrame(rows)], ignore_index=True) if len(done) else pd.DataFrame(rows)
    TR.mkdir(parents=True, exist_ok=True); g.to_csv(TR / "props_graded.csv", index=False); return g


def main(season: int | None = None, week: int | None = None, backfill: bool = False, live: bool = False):
    """The week's projections. backfill=True projects an earlier week of the season with the data as of that week (the
    same rule, nothing from the week itself), writes only its CSV and markdown with made = "after the fact", and
    leaves the live panel, profiles and grades alone; the next run grades it like any other week.
    live=True (the line watch, every run): the same projections re-made on the newest line snapshot, forecast and book
    lines, without re-grading last week (the weekly run grades; its summaries are carried over)."""
    from .lines import current_week, live_lines, load_log as lines_log
    from .positions import names_by_id
    from . import weather as WX
    games = pd.read_parquet(OUT / "games.parquet")
    if season is None or week is None:
        season, week = current_week(games)
    if not backfill:
        games = WX.apply_to_games(games, mos=False)   # the Open-Meteo kickoff forecast in use now (the line watch pulls it every run); the props keep it (2 Oct 2026: the game model moved to the GFS MOS reading)
    run_at = pd.Timestamp.now("UTC").strftime("%Y-%m-%d %H:%M UTC")
    d = official(pd.read_parquet(OUT / "scheme_plays.parquet"))
    graded = None if (backfill or live) else grade(d, season, week, run_at)
    vm = None if (backfill or live) else grade_market(graded, run_at)
    from .props_lines import load_log, closing
    plog = load_log()
    a = _asof(d, season, week); names = names_by_id(range(season - 2, season + 1))
    roster = pd.read_parquet(OUT / "roster_now.parquet") if (OUT / "roster_now.parquet").exists() else pd.DataFrame(columns=["team", "player_id", "roster", "report"])
    AG = active_games(season, week)   # round 14: the games a player was active for without a touch count in his touchdown share
    R, RU, Q, D, V, L = receivers(a, names, AG), rushers(a, names, AG), passers(a, names), defenses(a), teams_volume(a), league_baselines(a)
    VS = vs_defense(d[(d.season < season) | ((d.season == season) & (d.week < week))])   # every charted season, for the card's "against this defense" column
    dg = defender_games(); DF = defenders(dg, names, season, week); VS.update(vs_offense(dg[(dg.season < season) | ((dg.season == season) & (dg.week < week))], games))
    KK = kickers(kicker_games(range(season - 1, season + 1)), names, season, week); SN = snap_trends(season, week)
    wk = games[(games.season == season) & (games.week == week)].copy()
    if not backfill:   # the game script reads the current consensus line (lines.live_lines: the newest snapshot, median
        # across sources, to the half point), the same line the picks and the card are priced on (26 Sep 2026: the
        # Tuesday nflverse line, 43.5 on ATL@GB against a live 42.5)
        lv = live_lines(wk[["game_id", "spread_line", "total_line"]], lines_log()).set_index("game_id")
        wk["spread_line"] = wk.game_id.map(lv.spread_line); wk["total_line"] = wk.game_id.map(lv.total_line); wk["line_ts"] = wk.game_id.map(lv.total_ts.fillna(lv.spread_ts))
    from . import props_sit as PSI   # round 3 of the props: the situational inputs and each player's q (the by-season backtest's state)
    SQ = PSI.load_state(); SIT_IN, sit_note = {}, ("applied" if SQ is not None else "no state file (experiments/props_by_season.py writes it): no factor")
    if SQ is not None:
        try:
            SIT_IN = PSI.week_inputs(wk, season, week, roster, backfill)
        except Exception as e:  # noqa: a failed input build leaves the lines without the factor, said so in props.json
            SQ, sit_note = None, f"inputs failed ({type(e).__name__}: {str(e)[:120]}): no factor"; print("props: SIT", sit_note, flush=True)
    pv = OUT / "pred_v3.parquet"; xp = pd.read_parquet(pv, columns=["game_id", "home_exp", "away_exp"]).set_index("game_id") if pv.exists() else pd.DataFrame(columns=["home_exp", "away_exp"])   # the game model's expected points, priced before the game
    out = {"season": season, "week": week, "built": run_at, "window_games": WINDOW, "min_split": MIN_SPLIT, "k": K, "w": W, "decay": DECAY, "gs": GS, "gs_total": GS_TOTAL, "med": MED, "med_tier": MED_TIER, "pace": PACE, "absorb": ABSORB, "absorb_thr": ABSORB_THR, "chance": {"stats": list(CHANCE), "min_line": CHANCE_MIN_LINE, "k": CHANCE_K, "rows": {k: int(len(v[0])) for k, v in load_reference(season).items()}}, "wind_c": WIND_C, "wind_from": WIND_FROM, "targetable": TARGETABLE, "prop_edge": PROP_EDGE, "recon_w": RECON_W, "team_fit": TEAM_FIT, "k_catch": K_CATCH, "med_catch": MED_CATCH, "k_td": K_TD, "td_margin": TD_MARGIN, "td_pos": TD_POS, "inj_td": list(INJ_TD), "share_a_w": SHARE_A_W, "backtest_td": BACKTEST_TD, "backtest_counts": BACKTEST_COUNTS, "backtest_def": BACKTEST_DEF, "longest": LONGEST, "backtest_longest": BACKTEST_LONGEST, "fade": FADE, "kick": KICK, "backtest_kick": BACKTEST_KICK, "market_labels": MARKET_LABEL, "def_decay": DEF_DECAY, "def_med": DEF_MED, "k_sack": K_SACK, "sit": {"b": SIT, "clip": SIT_CLIP, "status": sit_note}, "league": L, "games": {},
           "backtest": dict(BACKTEST, note="mean absolute error in yards per player-game with this rule, 2019 to 2022 and 2023 to 2025, run walk-forward with league averages as of each game (reports/props_by_season.csv)")}
    fa = OUT / "features_asof.parquet"   # 3 Oct 2026 (Matt: the SEA props named Drew Lock): when ratings overrode a stale schedule starter, project the QB the game model priced
    over = {}
    if fa.exists():
        fx = pd.read_parquet(fa)
        if "qb_named_over" in fx.columns:
            fx = fx[fx.qb_named_over.notna() & fx.qb_id.notna()]
            over = {(r.game_id, r.team): r.qb_id for r in fx.itertuples()}
    rows = []
    for g in wk.itertuples():
        wd = None if (bool(g.dome) or pd.isna(g.wind)) else float(g.wind)   # kickoff forecast once one is usable (weather.apply_to_games), else unknown
        mk = closing(plog, g.game_id) if len(plog) else None
        ha = (float(xp.loc[g.game_id, "home_exp"]), float(xp.loc[g.game_id, "away_exp"])) if g.game_id in xp.index else (None, None)
        # the game script and the kicker's total read the game model's own margin and total, never the book's line
        # (28 Sep 2026, Matt: no market input anywhere in a projection; round 6 had found the model's margin in place
        # of the closing line changed nothing). Home side's margin, positive when the home team is favoured; a game
        # the model has not priced counts as zero, as a missing line did in the backtest.
        sp = None if ha[0] is None else ha[0] - ha[1]; mt = None if ha[0] is None else ha[0] + ha[1]
        aq = g.away_qb_id if isinstance(g.away_qb_id, str) else None; hq = g.home_qb_id if isinstance(g.home_qb_id, str) else None   # nflverse names the starters for played games and the coming week
        aq = over.get((g.game_id, g.away_team), aq); hq = over.get((g.game_id, g.home_team), hq)
        out["games"][g.game_id] = {g.away_team: project_game(g.away_team, g.home_team, R, RU, Q, D, V, L, roster, None if sp is None else -sp, mt, wd, mk, ha[1], VS, aq, SN, recent_players(AG, g.away_team), season, SIT_IN.get((g.game_id, g.away_team)), SQ), g.home_team: project_game(g.home_team, g.away_team, R, RU, Q, D, V, L, roster, sp, mt, wd, mk, ha[0], VS, hq, SN, recent_players(AG, g.home_team), season, SIT_IN.get((g.game_id, g.home_team)), SQ)}
        out["games"][g.game_id][g.away_team]["defenders"] = project_defense(g.away_team, g.home_team, DF, V, roster, None if sp is None else -sp, mt, mk, VS)
        out["games"][g.game_id][g.home_team]["defenders"] = project_defense(g.home_team, g.away_team, DF, V, roster, sp, mt, mk, VS)
        out["games"][g.game_id][g.away_team]["kicker"] = project_kicker(g.away_team, KK, roster, None if sp is None else -sp, mt, mk)
        out["games"][g.game_id][g.home_team]["kicker"] = project_kicker(g.home_team, KK, roster, sp, mt, mk)
        for team in (g.away_team, g.home_team):   # the line snapshot the game script read (lines.latest), beside the margin and total it used
            out["games"][g.game_id][team]["volume"]["line_ts"] = (None if backfill or pd.isna(g.line_ts) else str(g.line_ts)) if "line_ts" in wk.columns else None
        if mk is not None and len(mk):   # the book's lines on anyone not listed above (kickers, players without a profile), by team where the roster says
            from .props_lines import norm_name
            byname = {norm_name(r.name): r.team for r in roster[roster.team.isin([g.away_team, g.home_team])].itertuples()}
            for team in (g.away_team, g.home_team):
                side = out["games"][g.game_id][team]; listed = set(side.pop("_matched", [])) | {norm_name(r["name"]) for r in side.get("defenders", []) + side.get("kicker", [])}
                side["others"] = [{"name": h.player, "stat": h.stat, "line": (None if pd.isna(h.line) else float(h.line)), "books": int(h.books), "over": (None if pd.isna(h.over_price) else int(h.over_price)), "under": (None if pd.isna(h.under_price) else int(h.under_price)), "open": (None if pd.isna(h.open_line) else float(h.open_line)), "pulls": int(h.pulls)} for h in mk.itertuples() if h.key not in listed and byname.get(h.key) == team]
                side["market_open_ts"] = str(mk.open_ts.iloc[0]); side["market_pulls"] = int(mk.pulls.iloc[0])
        else:
            for team in (g.away_team, g.home_team): out["games"][g.game_id][team].pop("_matched", None); out["games"][g.game_id][team]["others"] = []
        for team, side in out["games"][g.game_id].items():
            def add(r, stat, proj, volume):
                rows.append({"season": season, "week": week, "game_id": g.game_id, "team": team, "player_id": r["player_id"], "name": r["name"], "stat": stat, "proj": proj, "proj_volume": volume, "run_at": run_at, "made": ("after the fact" if backfill else "live")})
            for r in side["receivers"]:
                if not r["out"]: add(r, "rec_yards", r["proj_rec_yards"], r["proj_targets"]); add(r, "rec_catches", r["proj_catches"], r["proj_targets"]); add(r, "rec_td", r["proj_rec_td"], r["proj_targets"]); add(r, "rec_targets", r["proj_targets"], r["proj_targets"]); add(r, "rec_longest", r["proj_rec_longest"], r["proj_targets"])
            for r in side["rushers"]:
                if not r["out"]: add(r, "rush_yards", r["proj_rush_yards"], r["proj_carries"]); add(r, "rush_td", r["proj_rush_td"], r["proj_carries"]); add(r, "rush_attempts", r["proj_rush_attempts"], r["proj_carries"]); add(r, "rush_rec_yards", r["proj_rush_rec_yards"], r["proj_carries"]); add(r, "rush_longest", r["proj_rush_longest"], r["proj_carries"])
            for r in side["qb"][:1]:
                if not r["out"]: add(r, "pass_yards", r["proj_pass_yards"], r["proj_dropbacks"]); add(r, "pass_td", r["proj_pass_td"], r["proj_dropbacks"]); add(r, "pass_int", r["proj_int"], r["proj_dropbacks"]); add(r, "pass_attempts", r["proj_pass_attempts"], r["proj_dropbacks"]); add(r, "pass_completions", r["proj_pass_completions"], r["proj_dropbacks"]); add(r, "pass_rush_yards", r["proj_pass_rush_yards"], r["proj_dropbacks"]); add(r, "pass_longest", r["proj_pass_longest"], r["proj_dropbacks"])
            for r in side.get("defenders", []):
                if not r["out"]: add(r, "def_tackles", r["proj_tackles"], r["opp_plays"]); add(r, "def_sacks", r["proj_sacks"], r["opp_plays"]); add(r, "def_solo_tackles", r["proj_solo_tackles"], r["opp_plays"])
            for r in side.get("kicker", []):
                if not r["out"]: add(r, "kick_points", r["proj_kick_points"], r["implied_total"]); add(r, "field_goals", r["proj_field_goals"], r["implied_total"])
    pr = pd.DataFrame(rows)
    if len(pr):
        pr.to_csv(REP / f"props_{season}_wk{week}.csv", index=False)
        if backfill:
            print(f"props backfill: {len(pr)} projections for week {week} of {season}, made after the fact with the data as of that week", flush=True); return
        md = [f"# Week {week}, {season}: player projections (readings, graded next run)", "", f"Volume (the team's plays per game moved by the game script from the current consensus spread and total (the newest line snapshot), shared among the players who are playing by usage decayed {DECAY} per game back, the share moved {SHARE_A_W['rec']:.0%} (receiving) and {SHARE_A_W['rush']:.0%} (rushing) of the way toward his usage over every game he was active for, a game without a touch counting 0; reports/props_backtest17.csv) x the player's yards per touch shrunk toward the league (receivers {K['rec']:.0f} targets, rushers {K['rush']:.0f} carries, QBs {K['pass']:.0f} dropbacks of weight) and moved toward what the defense allows (receivers {W['rec']:.0%}, rushers {W['rush']:.0%}, QBs {W['pass']:.0%}) x a median factor that rises with the player's mean, since a small role's median sits far below its mean and a star's close to it (receivers {MED_TIER['rec'][1]} to {MED_TIER['rec'][2]}, a logistic centred at {MED_TIER['rec'][3]} mean yards; rushers {MED['rush']} flat; QBs {MED_TIER['pass'][1]} + {MED_TIER['pass'][2]} x mean yards; reports/props_backtest15.csv). Passing yards also blend the opponent's allowed dropbacks (a quarter) and drop {abs(WIND_C['pass']):.1%} per mph of kickoff wind above 10. The rule the backtest rounds chose: {BACKTEST['rec_yards'][0]} / {BACKTEST['rec_yards'][1]} yards off on receiving, {BACKTEST['rush_yards'][0]} / {BACKTEST['rush_yards'][1]} on rushing and {BACKTEST['pass_yards'][0]} / {BACKTEST['pass_yards'][1]} on passing yards per player-game, 2019-22 / 2023-25 (reports/props_by_season.csv). Each team's players are then moved toward what the game model's expected points say the team should produce (yards a quarter of the way, passing half; touchdowns half, passing fully; reports/props_backtest6.csv). Receptions: targets x catch rate shrunk toward the league ({K_CATCH:.0f} targets) x {MED_CATCH}; touchdowns: volume x his rate shrunk toward the league's for his position ({K_TD['rec']:.0f} / {K_TD['rush']:.0f} / {K_TD['pass']:.0f} touches), receiving and passing scores moved {TD_MARGIN['rec']:.1%} per point of expected margin; the touchdown volume from his usage over every game he was active for, a game without a touch counting 0 (round 14: Poisson log loss {BACKTEST_TD['rec_td_ll'][0]} / {BACKTEST_TD['rec_td_ll'][1]} receiving and {BACKTEST_TD['rush_td_ll'][0]} / {BACKTEST_TD['rush_td_ll'][1]} rushing on every game a projected player played, reports/props_backtest14.csv); interceptions at the league rate (reports/props_backtest5.csv). Not a market comparison. Built {run_at}.", "", pr.drop(columns=["run_at"]).to_markdown(index=False), ""]
        (REP / f"props_{season}_wk{week}.md").write_text("\n".join(md))
    out["market_lines"] = int(sum(1 for gm in out["games"].values() for side in gm.values() for grp in ("receivers", "rushers", "qb") for r in side[grp] if any(k.startswith("mkt_") for k in r)))
    if (TR / "props_vs_market.csv").exists():
        vm_all = pd.read_csv(TR / "props_vs_market.csv"); out["market"] = market_summary(vm_all); out["market_rows"] = int(len(vm_all))
    if live and (OUT / "props.json").exists():   # the weekly run's grading summary, carried (a live re-projection does not re-grade)
        _old = json.loads((OUT / "props.json").read_text())
        if "graded" in _old: out["graded"] = _old["graded"]
    if graded is not None and len(graded):
        s = graded.groupby("stat").agg(n=("error", "size"), mae=("error", lambda e: round(float(e.abs().mean()), 2)), bias=("error", lambda e: round(float(e.mean()), 2))).reset_index()
        out["graded"] = s.to_dict("records")
    (OUT / "props.json").write_text(json.dumps(out, default=lambda v: None if (isinstance(v, float) and np.isnan(v)) else (v.item() if hasattr(v, "item") else str(v))))
    # every player's profile, every defense and the league, for the Players tab (the card shows only this week's games)
    if live:   # the profiles do not read the line or the book: the weekly run's stand
        print("props (live)", len(pr), "projections for week", week, "on the newest line snapshot; market lines on the cards", out["market_lines"], flush=True); return
    prof = {"season": season, "week": week, "built": run_at, "window_games": WINDOW, "min_split": MIN_SPLIT, "receivers": R, "rushers": RU, "passers": Q, "defenses": D, "volume": V, "league": L}
    (OUT / "props_profiles.json").write_text(json.dumps(prof, default=lambda v: None if (isinstance(v, float) and np.isnan(v)) else (v.item() if hasattr(v, "item") else str(v))))
    print("props", len(pr), "projections for week", week, "graded rows", 0 if graded is None else len(graded), "market lines on the cards", out["market_lines"], "graded against the market", out.get("market_rows", 0))


if __name__ == "__main__":
    import sys
    if "--live" in sys.argv or "--markets" in sys.argv:   # the line watch: re-project on the newest lines, forecast and book lines
        main(live=True)
    elif "--backfill" in sys.argv:   # python -m nflmodel.props --backfill 2026 1
        i = sys.argv.index("--backfill"); main(int(sys.argv[i + 1]), int(sys.argv[i + 2]), backfill=True)
    else:
        main()
