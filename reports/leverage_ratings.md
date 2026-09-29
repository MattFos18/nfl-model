# Leverage-weighted team EPA ratings (29 Sep 2026)

Question: do the team ratings (ratings.STATS: epa_play, pass_epa, rush_epa, success, pf, plays; opponent-adjusted,
decayed ridge in nflmodel/ratings.py) price games better when each play's EPA is weighted by its leverage (win
probability near 50%) instead of counting every play the same?

## Adoption rule (written before any result was looked at)

A variant is adopted only if its margin MAE and its team-points MAE are both strictly lower than base on all three
windows (2015-18, 2019-22, 2023-25). A tie on any window, or a gain on one or two windows only, is not adopted.
The 4+ edge ATS record and the total MAE are reported but do not decide.

## Variants (each is a replacement team_games frame handed to ratings.build_features; pf is never changed)

- base: the live frame, data/processed/team_games.parquet (control; reproduces the current numbers).
- ng: epa_play, pass_epa, rush_epa, success, plays replaced by the `_ng` columns build.py already writes
  (plays with pre-snap wp < 0.10 or > 0.90 dropped).
- lev: recomputed from the raw play-by-play with the smooth weight w = 1 - |2*wp - 1|^2 = 4*wp*(1-wp)
  (1.0 at wp 0.50, 0.64 at wp 0.20/0.80, 0.36 at 0.10/0.90, 0.19 at 0.05/0.95); every stat is the w-weighted mean
  over the same plays build.team_game_stats uses (posteam set, play_type pass/run, epa set, TEAM_FIX renames) and
  plays = the weight sum.
- ng2: recomputed, weight 1 if 0.05 <= wp <= 0.95 else 0 (a wider cut than ng).
- half: recomputed, weight 1 if 0.10 <= wp <= 0.90 else 0.5 (garbage plays kept at half weight).

Scoring: nflmodel.model.walk_forward, weekly refit, ridge alpha 10, REG games, on 2015-18 (untouched; report only),
2019-22 (tuning) and 2023-25 (held out), plus the 4+ record on 2019-2025 combined. No market input touches a rating
or a feature; spread_line and total_line appear only in the scoring. The trees cache is redirected to a scratch file
per variant so the live cache is untouched.

## Results (walk_forward, weekly refit; REG games)

| variant | window | team MAE | margin MAE | total MAE | 4+ ATS | 5+ ATS | n | vs base team / margin |
|---|---|---|---|---|---|---|---|---|
| base | 2015-18 | 7.4094 | 9.9493 | 10.7437 | 69-55 | 29-24 | 1024 | +0.0000 / +0.0000 |
| base | 2019-22 | 7.3473 | 10.0202 | 10.5406 | 83-54 | 39-30 | 1055 | +0.0000 / +0.0000 |
| base | 2023-25 | 7.2626 | 9.9050 | 10.1767 | 44-26 | 20-11 | 816 | +0.0000 / +0.0000 |
| base | 2019-25 | 7.3103 | 9.9699 | 10.3819 | 127-80 | 59-41 | 1871 | +0.0000 / +0.0000 |
| ng | 2015-18 | 7.3980 | 9.9334 | 10.7699 | 65-52 | 34-28 | 1024 | -0.0114 / -0.0159 |
| ng | 2019-22 | 7.3370 | 10.0221 | 10.5311 | 82-57 | 41-32 | 1055 | -0.0103 / +0.0019 |
| ng | 2023-25 | 7.2673 | 9.8916 | 10.1928 | 44-30 | 20-11 | 816 | +0.0047 / -0.0134 |
| ng | 2019-25 | 7.3066 | 9.9651 | 10.3835 | 126-87 | 61-43 | 1871 | -0.0037 / -0.0048 |
| lev | 2015-18 | 7.4012 | 9.9361 | 10.7709 | 60-57 | 29-24 | 1024 | -0.0082 / -0.0132 |
| lev | 2019-22 | 7.3383 | 10.0132 | 10.5349 | 83-54 | 39-31 | 1055 | -0.0090 / -0.0070 |
| lev | 2023-25 | 7.2671 | 9.8934 | 10.1885 | 44-27 | 20-11 | 816 | +0.0045 / -0.0116 |
| lev | 2019-25 | 7.3072 | 9.9610 | 10.3838 | 127-81 | 59-42 | 1871 | -0.0031 / -0.0089 |
| ng2 | 2015-18 | 7.4063 | 9.9460 | 10.7651 | 67-56 | 32-27 | 1024 | -0.0031 / -0.0033 |
| ng2 | 2019-22 | 7.3400 | 10.0171 | 10.5348 | 80-52 | 39-29 | 1055 | -0.0073 / -0.0031 |
| ng2 | 2023-25 | 7.2687 | 9.8885 | 10.1906 | 43-28 | 19-11 | 816 | +0.0061 / -0.0165 |
| ng2 | 2019-25 | 7.3089 | 9.9610 | 10.3847 | 123-80 | 58-40 | 1871 | -0.0014 / -0.0089 |
| half | 2015-18 | 7.4052 | 9.9435 | 10.7459 | 66-55 | 30-26 | 1024 | -0.0042 / -0.0058 |
| half | 2019-22 | 7.3416 | 10.0171 | 10.5368 | 81-54 | 41-30 | 1055 | -0.0057 / -0.0031 |
| half | 2023-25 | 7.2639 | 9.8954 | 10.1831 | 44-27 | 19-11 | 816 | +0.0013 / -0.0096 |
| half | 2019-25 | 7.3077 | 9.9640 | 10.3826 | 125-81 | 60-41 | 1871 | -0.0026 / -0.0059 |

## Verdict (by the adoption rule above)

- ng: not adopted (both MAEs lower than base on 1 of 3 windows: 2015-18)
- lev: not adopted (both MAEs lower than base on 2 of 3 windows: 2015-18, 2019-22)
- ng2: not adopted (both MAEs lower than base on 2 of 3 windows: 2015-18, 2019-22)
- half: not adopted (both MAEs lower than base on 2 of 3 windows: 2015-18, 2019-22)

Runtimes: base 280s (features 59s, walk-forward 220s), ng 831s (features 286s, walk-forward 544s), lev 811s (features 283s, walk-forward 523s), ng2 879s (features 395s, walk-forward 479s), half 890s (features 388s, walk-forward 495s)

Reading: every leverage variant lowers the margin miss on all three windows (by 0.003 to 0.017 points) and the
team-points miss on 2015-18 and 2019-22, but every one of them raises the team-points miss on the held-out 2023-25
window (+0.001 to +0.006) and none moves the 4+ record (base 127-80 on 2019-2025; the variants 123-80 to 127-81).
The rule fails on that one cell for lev, ng2 and half, and ng also gives back margin on 2019-22. Nothing is adopted;
the ratings keep counting every play the same. The gains are of the size the rule is meant to filter out.

Note: the raw pbp files did not yet hold 2026 week 3 when this ran; those 32 team-games keep their base values in the
recomputed frames. They are outside every scored window.
