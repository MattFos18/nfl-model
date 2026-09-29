# Game-script variants and absorption when a starter is out

29 Sep 2026. experiments/props_gs_absorb.py, reports/props_gs_absorb.csv. Two claims on the live player-prop rule (nflmodel/props.py), walk-forward, as-of only, no market input: part 1, the game script on the team's plays (the live line, a refit, a win-probability form, a quadratic form, opponent pace); part 2, absorption of an absent starter's share by his teammates at a fitted fraction, a different form from round ten's pro rata (which lost on both windows). Scores: mean absolute error per player-game of the volume (targets, carries, dropbacks) and of the yards line, signed bias, the paired standard error against base, 2019-22 and 2023-25 with 2017-18 beside them as the fit window, and by tier of the base yards line.

## Adoption rule (set before the run)

On the touch frame (every player-game with a touch of the kind; the frame the rule's constants were chosen on and reports/props_by_season.csv grades), a variant is adopted only if it lowers yards MAE on both windows (2019-22 and 2023-25) and does not raise volume MAE (targets, carries, dropbacks) on either. The active frame (plus every game a projected receiver or rusher played snaps in without a touch, actual 0: the population the card projects) is a check beside it: a variant that passes on the touch frame but raises yards MAE on the active frame on either window is flagged, not adopted. Every constant is fitted on the fit window only (part 1: team-games 2016-18; part 2: the frame's 2017-18, since 2016 is the first charted season and its players have no history). No market input anywhere: the game script reads the game model's expected points (pred_v3; margin = own minus the opponent's, total = their sum), never the closing spread or total.

## Frames

- rec: touch frame 36630 player-games 2017-25 (7518 in 2017-18, 16076 in 2019-22, 12383 in 2023-25); active frame 46327 (9697 zero-touch games).
- rush: touch frame 17788 player-games 2017-25 (3497 in 2017-18, 7778 in 2019-22, 6196 in 2023-25); active frame 25089 (7301 zero-touch games).
- pass: touch frame 5031 player-games 2017-25 (1046 in 2017-18, 2176 in 2019-22, 1712 in 2023-25).

## Part 1: the game script on the team's plays

Fitted on 1506 team-games of 2016-18 (each team in each game, with 3+ previous games for the team and the opponent). The target is the team's plays of the kind in the game minus its live base (its last-17 average, blended props.PACE toward the opponent's allowed per game: 0 for pass plays and runs, 0.25 for dropbacks); the model's margin is from the team's side, the total is the model's, centred on GS_TOTAL = 43.5674 (the model's mean total over the frame is about 45.5, so the intercept of a refit absorbs the two-point difference from the closing-total mean the live line was centred on). The line is constant + b1 x margin + b2 x (total - GS_TOTAL); winprob replaces the margin by p - 0.5 with p = Phi(margin / 13); quad adds b3 x margin^2 + b4 x margin x total. In-sample MAE of the plays beyond the base, 2016-18, beside each.

| kind | variant | constants | fit MAE (plays) |
|:--|:--|:--|--:|
| rec (tp) | base | -0.5969, -0.0460, 0.1636 | 6.864 |
| rec (tp) | refit | -0.6477, -0.0403, 0.1589 | 6.863 |
| rec (tp) | winprob | -0.6477, -1.4115, 0.1589 | 6.863 |
| rec (tp) | quad | -0.5370, -0.0021, 0.1577, -0.0034, -0.0183 | 6.859 |
| rush (tr) | base | 0.3413, 0.1030, -0.1713 | 6.114 |
| rush (tr) | refit | 0.3890, 0.1435, -0.1609 | 6.108 |
| rush (tr) | winprob | 0.3890, 5.0953, -0.1609 | 6.106 |
| rush (tr) | quad | 0.3453, 0.1258, -0.1604, 0.0014, 0.0085 | 6.105 |
| pass (tdb) | base | -0.5967, -0.0461, 0.1638 | 6.774 |
| pass (tdb) | refit | -0.6130, -0.0229, 0.1398 | 6.771 |
| pass (tdb) | winprob | -0.6130, -0.8196, 0.1398 | 6.771 |
| pass (tdb) | quad | -0.5063, 0.0118, 0.1387, -0.0033, -0.0166 | 6.772 |

The standard deviation of the target (plays beyond the base) is rec 8.62, rush 7.65, pass 8.48. pace_w: the team's last-17 average blended w toward the opponent's allowed plays per game (w = 0.25, 0.5), the live line on top.

### rec, touch frame

targets (volume)

| variant | 2017-18 MAE | bias | SE vs base | 2019-22 MAE | bias | SE vs base | 2023-25 MAE | bias | SE vs base |
|:--|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| base | 1.8787 | -0.26 | 0.0000 | 1.8302 | -0.25 | 0.0000 | 1.7186 | -0.25 | 0.0000 |
| refit | 1.8782 | -0.26 | 0.0001 | 1.8298 | -0.26 | 0.0001 | 1.7182 | -0.25 | 0.0001 |
| winprob | 1.8782 | -0.26 | 0.0001 | 1.8298 | -0.26 | 0.0001 | 1.7182 | -0.25 | 0.0001 |
| quad | 1.8774 | -0.27 | 0.0007 | 1.8292 | -0.26 | 0.0005 | 1.7183 | -0.26 | 0.0005 |
| pace_0.25 | 1.8751 | -0.26 | 0.0013 | 1.8264 | -0.26 | 0.0010 | 1.7142 | -0.25 | 0.0011 |
| pace_0.5 | 1.8751 | -0.26 | 0.0025 | 1.8275 | -0.26 | 0.0021 | 1.7146 | -0.24 | 0.0022 |

yards

| variant | 2017-18 MAE | bias | SE vs base | 2019-22 MAE | bias | SE vs base | 2023-25 MAE | bias | SE vs base |
|:--|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| base | 19.706 | -6.65 | 0.000 | 19.157 | -6.28 | 0.000 | 18.157 | -6.09 | 0.000 |
| refit | 19.706 | -6.68 | 0.001 | 19.157 | -6.31 | 0.000 | 18.158 | -6.12 | 0.000 |
| winprob | 19.706 | -6.68 | 0.001 | 19.156 | -6.31 | 0.000 | 18.157 | -6.12 | 0.000 |
| quad | 19.706 | -6.69 | 0.004 | 19.159 | -6.32 | 0.003 | 18.158 | -6.13 | 0.003 |
| pace_0.25 | 19.706 | -6.64 | 0.007 | 19.154 | -6.28 | 0.006 | 18.142 | -6.08 | 0.006 |
| pace_0.5 | 19.716 | -6.64 | 0.013 | 19.164 | -6.28 | 0.011 | 18.139 | -6.06 | 0.012 |

### rec, active frame

targets (volume)

| variant | 2017-18 MAE | bias | SE vs base | 2019-22 MAE | bias | SE vs base | 2023-25 MAE | bias | SE vs base |
|:--|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| base | 1.8427 | +0.10 | 0.0000 | 1.7780 | +0.13 | 0.0000 | 1.6507 | +0.13 | 0.0000 |
| refit | 1.8419 | +0.10 | 0.0001 | 1.7771 | +0.12 | 0.0001 | 1.6499 | +0.12 | 0.0001 |
| winprob | 1.8419 | +0.10 | 0.0001 | 1.7771 | +0.12 | 0.0001 | 1.6499 | +0.12 | 0.0001 |
| quad | 1.8412 | +0.10 | 0.0005 | 1.7764 | +0.12 | 0.0004 | 1.6499 | +0.12 | 0.0004 |
| pace_0.25 | 1.8402 | +0.10 | 0.0011 | 1.7753 | +0.13 | 0.0008 | 1.6477 | +0.13 | 0.0009 |
| pace_0.5 | 1.8406 | +0.11 | 0.0021 | 1.7765 | +0.13 | 0.0017 | 1.6485 | +0.13 | 0.0017 |

yards

| variant | 2017-18 MAE | bias | SE vs base | 2019-22 MAE | bias | SE vs base | 2023-25 MAE | bias | SE vs base |
|:--|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| base | 17.624 | -4.27 | 0.000 | 16.835 | -3.77 | 0.000 | 15.697 | -3.58 | 0.000 |
| refit | 17.623 | -4.30 | 0.000 | 16.833 | -3.80 | 0.000 | 15.696 | -3.60 | 0.000 |
| winprob | 17.623 | -4.30 | 0.001 | 16.833 | -3.80 | 0.000 | 15.696 | -3.60 | 0.000 |
| quad | 17.623 | -4.30 | 0.003 | 16.834 | -3.81 | 0.002 | 15.696 | -3.61 | 0.002 |
| pace_0.25 | 17.625 | -4.27 | 0.005 | 16.835 | -3.77 | 0.004 | 15.686 | -3.57 | 0.005 |
| pace_0.5 | 17.632 | -4.26 | 0.011 | 16.844 | -3.78 | 0.009 | 15.686 | -3.56 | 0.009 |

### rush, touch frame

carries (volume)

| variant | 2017-18 MAE | bias | SE vs base | 2019-22 MAE | bias | SE vs base | 2023-25 MAE | bias | SE vs base |
|:--|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| base | 3.1066 | -0.34 | 0.0000 | 2.9828 | -0.45 | 0.0000 | 2.8765 | -0.33 | 0.0000 |
| refit | 3.1083 | -0.32 | 0.0014 | 2.9869 | -0.43 | 0.0009 | 2.8774 | -0.31 | 0.0010 |
| winprob | 3.1080 | -0.32 | 0.0014 | 2.9870 | -0.43 | 0.0009 | 2.8770 | -0.31 | 0.0010 |
| quad | 3.1070 | -0.32 | 0.0017 | 2.9880 | -0.43 | 0.0012 | 2.8791 | -0.31 | 0.0012 |
| pace_0.25 | 3.0935 | -0.35 | 0.0049 | 2.9677 | -0.45 | 0.0035 | 2.8657 | -0.33 | 0.0038 |
| pace_0.5 | 3.0920 | -0.36 | 0.0096 | 2.9674 | -0.45 | 0.0070 | 2.8708 | -0.33 | 0.0075 |

yards

| variant | 2017-18 MAE | bias | SE vs base | 2019-22 MAE | bias | SE vs base | 2023-25 MAE | bias | SE vs base |
|:--|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| base | 18.080 | -4.45 | 0.000 | 17.780 | -5.22 | 0.000 | 17.041 | -4.69 | 0.000 |
| refit | 18.079 | -4.39 | 0.004 | 17.783 | -5.16 | 0.003 | 17.031 | -4.63 | 0.003 |
| winprob | 18.079 | -4.39 | 0.004 | 17.784 | -5.16 | 0.003 | 17.031 | -4.63 | 0.003 |
| quad | 18.075 | -4.39 | 0.005 | 17.780 | -5.16 | 0.004 | 17.034 | -4.63 | 0.004 |
| pace_0.25 | 18.071 | -4.47 | 0.014 | 17.767 | -5.23 | 0.011 | 17.036 | -4.71 | 0.011 |
| pace_0.5 | 18.080 | -4.50 | 0.027 | 17.771 | -5.25 | 0.021 | 17.053 | -4.73 | 0.022 |

### rush, active frame

carries (volume)

| variant | 2017-18 MAE | bias | SE vs base | 2019-22 MAE | bias | SE vs base | 2023-25 MAE | bias | SE vs base |
|:--|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| base | 2.8214 | -0.00 | 0.0000 | 2.3925 | -0.02 | 0.0000 | 2.1748 | +0.03 | 0.0000 |
| refit | 2.8233 | +0.01 | 0.0011 | 2.3962 | -0.01 | 0.0007 | 2.1761 | +0.05 | 0.0007 |
| winprob | 2.8231 | +0.01 | 0.0012 | 2.3962 | -0.01 | 0.0007 | 2.1758 | +0.05 | 0.0007 |
| quad | 2.8221 | +0.01 | 0.0014 | 2.3971 | -0.01 | 0.0009 | 2.1773 | +0.05 | 0.0008 |
| pace_0.25 | 2.8110 | -0.01 | 0.0040 | 2.3822 | -0.02 | 0.0025 | 2.1668 | +0.03 | 0.0026 |
| pace_0.5 | 2.8101 | -0.02 | 0.0079 | 2.3823 | -0.02 | 0.0049 | 2.1694 | +0.03 | 0.0050 |

yards

| variant | 2017-18 MAE | bias | SE vs base | 2019-22 MAE | bias | SE vs base | 2023-25 MAE | bias | SE vs base |
|:--|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| base | 15.782 | -2.89 | 0.000 | 13.561 | -2.86 | 0.000 | 12.320 | -2.44 | 0.000 |
| refit | 15.780 | -2.85 | 0.003 | 13.564 | -2.82 | 0.002 | 12.316 | -2.40 | 0.002 |
| winprob | 15.780 | -2.85 | 0.003 | 13.564 | -2.82 | 0.002 | 12.315 | -2.40 | 0.002 |
| quad | 15.777 | -2.84 | 0.004 | 13.563 | -2.82 | 0.003 | 12.317 | -2.40 | 0.002 |
| pace_0.25 | 15.772 | -2.91 | 0.011 | 13.551 | -2.87 | 0.007 | 12.316 | -2.46 | 0.008 |
| pace_0.5 | 15.777 | -2.93 | 0.022 | 13.554 | -2.88 | 0.015 | 12.327 | -2.47 | 0.015 |

### pass, touch frame

dropbacks (volume)

| variant | 2017-18 MAE | bias | SE vs base | 2019-22 MAE | bias | SE vs base | 2023-25 MAE | bias | SE vs base |
|:--|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| base | 7.5939 | +2.76 | 0.0000 | 7.6860 | +3.11 | 0.0000 | 7.7009 | +3.67 | 0.0000 |
| refit | 7.5774 | +2.69 | 0.0055 | 7.6634 | +3.04 | 0.0040 | 7.6814 | +3.61 | 0.0042 |
| winprob | 7.5776 | +2.69 | 0.0055 | 7.6629 | +3.04 | 0.0040 | 7.6814 | +3.61 | 0.0042 |
| quad | 7.5812 | +2.69 | 0.0134 | 7.6517 | +3.02 | 0.0099 | 7.6743 | +3.60 | 0.0109 |
| pace_0.25 | 7.5939 | +2.76 | 0.0000 | 7.6860 | +3.11 | 0.0000 | 7.7009 | +3.67 | 0.0000 |
| pace_0.5 | 7.5657 | +2.76 | 0.0273 | 7.7081 | +3.11 | 0.0230 | 7.6836 | +3.67 | 0.0241 |

yards

| variant | 2017-18 MAE | bias | SE vs base | 2019-22 MAE | bias | SE vs base | 2023-25 MAE | bias | SE vs base |
|:--|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| base | 60.722 | -6.69 | 0.000 | 56.574 | -4.63 | 0.000 | 56.109 | +1.58 | 0.000 |
| refit | 60.742 | -6.95 | 0.021 | 56.617 | -4.90 | 0.015 | 56.110 | +1.37 | 0.015 |
| winprob | 60.743 | -6.95 | 0.021 | 56.617 | -4.90 | 0.015 | 56.110 | +1.37 | 0.015 |
| quad | 60.675 | -6.96 | 0.052 | 56.612 | -4.95 | 0.036 | 56.114 | +1.37 | 0.037 |
| pace_0.25 | 60.722 | -6.69 | 0.000 | 56.574 | -4.63 | 0.000 | 56.109 | +1.58 | 0.000 |
| pace_0.5 | 60.683 | -6.73 | 0.107 | 56.690 | -4.67 | 0.089 | 56.004 | +1.65 | 0.090 |

### Part 1 by tier of the base yards line (yards MAE, n), touch frame

rec

| variant | window | 0-20 (n) | 20-40 (n) | 40-60 (n) | 60-80 (n) | 80+ (n) |
|:--|:--|--:|--:|--:|--:|--:|
| base | 2019-22 | 13.309 (8248) | 21.071 (4172) | 28.906 (2521) | 32.208 (965) | 37.207 (170) |
| base | 2023-25 | 12.598 (6800) | 21.233 (3003) | 27.312 (1792) | 32.606 (651) | 38.283 (137) |
| refit | 2019-22 | 13.310 (8248) | 21.070 (4172) | 28.905 (2521) | 32.208 (965) | 37.209 (170) |
| refit | 2023-25 | 12.598 (6800) | 21.233 (3003) | 27.312 (1792) | 32.605 (651) | 38.286 (137) |
| winprob | 2019-22 | 13.310 (8248) | 21.069 (4172) | 28.905 (2521) | 32.208 (965) | 37.208 (170) |
| winprob | 2023-25 | 12.598 (6800) | 21.233 (3003) | 27.311 (1792) | 32.605 (651) | 38.286 (137) |
| quad | 2019-22 | 13.311 (8248) | 21.073 (4172) | 28.908 (2521) | 32.225 (965) | 37.164 (170) |
| quad | 2023-25 | 12.597 (6800) | 21.244 (3003) | 27.299 (1792) | 32.613 (651) | 38.325 (137) |
| pace_0.25 | 2019-22 | 13.303 (8248) | 21.060 (4172) | 28.920 (2521) | 32.236 (965) | 37.190 (170) |
| pace_0.25 | 2023-25 | 12.598 (6800) | 21.197 (3003) | 27.276 (1792) | 32.549 (651) | 38.440 (137) |
| pace_0.5 | 2019-22 | 13.301 (8248) | 21.069 (4172) | 28.952 (2521) | 32.289 (965) | 37.181 (170) |
| pace_0.5 | 2023-25 | 12.600 (6800) | 21.182 (3003) | 27.262 (1792) | 32.533 (651) | 38.620 (137) |

rush

| variant | window | 0-20 (n) | 20-40 (n) | 40-60 (n) | 60-80 (n) | 80+ (n) |
|:--|:--|--:|--:|--:|--:|--:|
| base | 2019-22 | 10.625 (3990) | 21.443 (1805) | 27.490 (1315) | 30.420 (557) | 36.975 (111) |
| base | 2023-25 | 10.746 (3157) | 18.907 (1420) | 26.065 (1069) | 29.925 (468) | 35.928 (82) |
| refit | 2019-22 | 10.627 (3990) | 21.449 (1805) | 27.488 (1315) | 30.428 (557) | 36.989 (111) |
| refit | 2023-25 | 10.746 (3157) | 18.909 (1420) | 26.022 (1069) | 29.885 (468) | 35.951 (82) |
| winprob | 2019-22 | 10.627 (3990) | 21.450 (1805) | 27.492 (1315) | 30.427 (557) | 36.980 (111) |
| winprob | 2023-25 | 10.746 (3157) | 18.906 (1420) | 26.023 (1069) | 29.881 (468) | 35.959 (82) |
| quad | 2019-22 | 10.625 (3990) | 21.453 (1805) | 27.485 (1315) | 30.418 (557) | 36.876 (111) |
| quad | 2023-25 | 10.746 (3157) | 18.914 (1420) | 26.032 (1069) | 29.862 (468) | 36.020 (82) |
| pace_0.25 | 2019-22 | 10.624 (3990) | 21.453 (1805) | 27.462 (1315) | 30.292 (557) | 36.892 (111) |
| pace_0.25 | 2023-25 | 10.745 (3157) | 18.914 (1420) | 26.007 (1069) | 30.007 (468) | 35.720 (82) |
| pace_0.5 | 2019-22 | 10.627 (3990) | 21.480 (1805) | 27.463 (1315) | 30.234 (557) | 36.917 (111) |
| pace_0.5 | 2023-25 | 10.750 (3157) | 18.945 (1420) | 25.993 (1069) | 30.159 (468) | 35.624 (82) |

pass

| variant | window | 0-150 (n) | 150-200 (n) | 200-250 (n) | 250-300 (n) | 300+ (n) |
|:--|:--|--:|--:|--:|--:|--:|
| base | 2019-22 | 46.113 (24) | 59.286 (220) | 55.000 (1304) | 59.539 (613) | 49.138 (15) |
| base | 2023-25 | 55.034 (51) | 60.919 (257) | 54.566 (1133) | 58.310 (270) | 29.014 (1) |
| refit | 2019-22 | 46.023 (24) | 59.190 (220) | 55.037 (1304) | 59.650 (613) | 49.252 (15) |
| refit | 2023-25 | 54.930 (51) | 60.875 (257) | 54.570 (1133) | 58.359 (270) | 30.286 (1) |
| winprob | 2019-22 | 46.023 (24) | 59.191 (220) | 55.037 (1304) | 59.648 (613) | 49.236 (15) |
| winprob | 2023-25 | 54.927 (51) | 60.874 (257) | 54.569 (1133) | 58.362 (270) | 30.451 (1) |
| quad | 2019-22 | 46.418 (24) | 59.254 (220) | 54.999 (1304) | 59.695 (613) | 48.431 (15) |
| quad | 2023-25 | 54.502 (51) | 60.973 (257) | 54.577 (1133) | 58.352 (270) | 25.621 (1) |
| pace_0.25 | 2019-22 | 46.113 (24) | 59.286 (220) | 55.000 (1304) | 59.539 (613) | 49.138 (15) |
| pace_0.25 | 2023-25 | 55.034 (51) | 60.919 (257) | 54.566 (1133) | 58.310 (270) | 29.014 (1) |
| pace_0.5 | 2019-22 | 46.818 (24) | 59.508 (220) | 55.034 (1304) | 59.735 (613) | 50.700 (15) |
| pace_0.5 | 2023-25 | 55.812 (51) | 60.467 (257) | 54.466 (1133) | 58.398 (270) | 14.910 (1) |

## Part 2: absorption when a starter is out

Absent = a player with a snap at a skill position in one of the team's last 3 games and none this week (hindsight), whose decayed share as of the game (props.share_blend of his touch-games and active-games shares after his last game) is >= 0.15 for receivers, >= 0.25 for rushers. As-of = the same candidates the live rule could know were out before the game: listed Out or Doubtful on the week's injury report, or without an active listing on the week's roster (reserve / IR, PUP, suspended, cut), whether or not they then played. The teammates' added share = f x the absent share, split among the remaining players of the frame in proportion to their own shares (same-position teammates, or all teammates); f fitted on 2017-18 team-games of the active frame by least squares of the frame's players' actual share of the team's plays beyond their projected share on an intercept and the absent share by the absent player's position (only positions with 30+ fit-window absences get an f; the rest 0). The matrix below is recipient position (rows) by absent position (columns): the same-position f is the diagonal, the all-teammates f the 'all' row.

### rec

Absences: 1059 of 5084 frame team-games have a hindsight absence (1170 player-games, by position {'WR': 925, 'TE': 180, 'RB': 65}, mean absent share 0.188); 1016 as-of absences, 1012 of them also absent in hindsight, 4 listed out who then played. Fit: 1068 team-games 2017-18, absences by position {'WR': 183, 'TE': 35, 'RB': 18}, fitted positions ['WR', 'TE'].

| recipient \ absent | intercept | WR | TE |
|:--|--:|--:|--:|
| WR | -0.023 | +0.422 | +0.285 |
| TE | -0.010 | +0.028 | +0.249 |
| RB | -0.011 | +0.017 | -0.064 |
| all | -0.044 | +0.467 | +0.470 |

#### rec, touch frame

targets (volume)

| variant | 2017-18 MAE | bias | SE vs base | 2019-22 MAE | bias | SE vs base | 2023-25 MAE | bias | SE vs base |
|:--|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| base | 1.8787 | -0.26 | 0.0000 | 1.8302 | -0.25 | 0.0000 | 1.7186 | -0.25 | 0.0000 |
| hind_same | 1.8795 | -0.17 | 0.0036 | 1.8302 | -0.17 | 0.0025 | 1.7127 | -0.17 | 0.0027 |
| hind_same_half | 1.8746 | -0.22 | 0.0018 | 1.8256 | -0.21 | 0.0013 | 1.7125 | -0.21 | 0.0014 |
| hind_all | 1.8819 | -0.16 | 0.0031 | 1.8310 | -0.15 | 0.0021 | 1.7192 | -0.16 | 0.0023 |
| hind_all_half | 1.8775 | -0.21 | 0.0016 | 1.8278 | -0.20 | 0.0011 | 1.7166 | -0.20 | 0.0012 |
| asof_same | 1.8776 | -0.20 | 0.0030 | 1.8303 | -0.18 | 0.0024 | 1.7131 | -0.18 | 0.0027 |
| asof_same_half | 1.8750 | -0.23 | 0.0015 | 1.8258 | -0.21 | 0.0013 | 1.7128 | -0.21 | 0.0014 |
| asof_all | 1.8794 | -0.19 | 0.0025 | 1.8306 | -0.16 | 0.0020 | 1.7191 | -0.16 | 0.0023 |
| asof_all_half | 1.8771 | -0.22 | 0.0013 | 1.8276 | -0.21 | 0.0010 | 1.7167 | -0.21 | 0.0012 |

yards

| variant | 2017-18 MAE | bias | SE vs base | 2019-22 MAE | bias | SE vs base | 2023-25 MAE | bias | SE vs base |
|:--|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| base | 19.706 | -6.65 | 0.000 | 19.157 | -6.28 | 0.000 | 18.157 | -6.09 | 0.000 |
| hind_same | 19.689 | -6.21 | 0.025 | 19.146 | -5.82 | 0.018 | 18.154 | -5.71 | 0.019 |
| hind_same_half | 19.684 | -6.43 | 0.013 | 19.133 | -6.04 | 0.010 | 18.145 | -5.90 | 0.010 |
| hind_all | 19.727 | -6.15 | 0.017 | 19.163 | -5.76 | 0.012 | 18.167 | -5.64 | 0.014 |
| hind_all_half | 19.708 | -6.39 | 0.009 | 19.151 | -6.01 | 0.006 | 18.152 | -5.86 | 0.007 |
| asof_same | 19.694 | -6.34 | 0.021 | 19.143 | -5.85 | 0.018 | 18.156 | -5.73 | 0.018 |
| asof_same_half | 19.691 | -6.49 | 0.011 | 19.133 | -6.06 | 0.009 | 18.145 | -5.91 | 0.010 |
| asof_all | 19.719 | -6.29 | 0.014 | 19.165 | -5.80 | 0.012 | 18.163 | -5.66 | 0.013 |
| asof_all_half | 19.707 | -6.47 | 0.007 | 19.152 | -6.03 | 0.006 | 18.150 | -5.87 | 0.007 |

#### rec, active frame

targets (volume)

| variant | 2017-18 MAE | bias | SE vs base | 2019-22 MAE | bias | SE vs base | 2023-25 MAE | bias | SE vs base |
|:--|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| base | 1.8427 | +0.10 | 0.0000 | 1.7780 | +0.13 | 0.0000 | 1.6507 | +0.13 | 0.0000 |
| hind_same | 1.8464 | +0.17 | 0.0028 | 1.7824 | +0.19 | 0.0019 | 1.6510 | +0.18 | 0.0020 |
| hind_same_half | 1.8412 | +0.14 | 0.0015 | 1.7772 | +0.16 | 0.0010 | 1.6488 | +0.15 | 0.0010 |
| hind_all | 1.8520 | +0.19 | 0.0024 | 1.7853 | +0.20 | 0.0016 | 1.6574 | +0.19 | 0.0017 |
| hind_all_half | 1.8454 | +0.14 | 0.0012 | 1.7798 | +0.17 | 0.0008 | 1.6526 | +0.16 | 0.0009 |
| asof_same | 1.8443 | +0.15 | 0.0023 | 1.7818 | +0.19 | 0.0018 | 1.6510 | +0.18 | 0.0020 |
| asof_same_half | 1.8412 | +0.13 | 0.0012 | 1.7770 | +0.16 | 0.0010 | 1.6489 | +0.15 | 0.0010 |
| asof_all | 1.8477 | +0.16 | 0.0019 | 1.7842 | +0.20 | 0.0015 | 1.6570 | +0.19 | 0.0016 |
| asof_all_half | 1.8438 | +0.13 | 0.0010 | 1.7793 | +0.16 | 0.0008 | 1.6524 | +0.16 | 0.0008 |

yards

| variant | 2017-18 MAE | bias | SE vs base | 2019-22 MAE | bias | SE vs base | 2023-25 MAE | bias | SE vs base |
|:--|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| base | 17.624 | -4.27 | 0.000 | 16.835 | -3.77 | 0.000 | 15.697 | -3.58 | 0.000 |
| hind_same | 17.612 | -3.93 | 0.019 | 16.838 | -3.42 | 0.013 | 15.708 | -3.30 | 0.013 |
| hind_same_half | 17.607 | -4.10 | 0.009 | 16.823 | -3.59 | 0.007 | 15.694 | -3.44 | 0.007 |
| hind_all | 17.656 | -3.88 | 0.013 | 16.855 | -3.38 | 0.009 | 15.720 | -3.25 | 0.009 |
| hind_all_half | 17.634 | -4.08 | 0.006 | 16.839 | -3.57 | 0.005 | 15.702 | -3.41 | 0.005 |
| asof_same | 17.619 | -4.03 | 0.016 | 16.833 | -3.45 | 0.013 | 15.708 | -3.31 | 0.013 |
| asof_same_half | 17.613 | -4.15 | 0.008 | 16.821 | -3.61 | 0.007 | 15.694 | -3.44 | 0.007 |
| asof_all | 17.643 | -4.00 | 0.010 | 16.853 | -3.41 | 0.008 | 15.716 | -3.27 | 0.009 |
| asof_all_half | 17.629 | -4.13 | 0.005 | 16.839 | -3.59 | 0.004 | 15.701 | -3.42 | 0.005 |

#### rec by tier of the base yards line (yards MAE, n), touch frame

| variant | window | 0-20 (n) | 20-40 (n) | 40-60 (n) | 60-80 (n) | 80+ (n) |
|:--|:--|--:|--:|--:|--:|--:|
| base | 2019-22 | 13.309 (8248) | 21.071 (4172) | 28.906 (2521) | 32.208 (965) | 37.207 (170) |
| base | 2023-25 | 12.598 (6800) | 21.233 (3003) | 27.312 (1792) | 32.606 (651) | 38.283 (137) |
| hind_same | 2019-22 | 13.271 (8248) | 21.063 (4172) | 28.932 (2521) | 32.285 (965) | 37.443 (170) |
| hind_same | 2023-25 | 12.550 (6800) | 21.262 (3003) | 27.339 (1792) | 32.797 (651) | 38.504 (137) |
| hind_same_half | 2019-22 | 13.284 (8248) | 21.034 (4172) | 28.894 (2521) | 32.215 (965) | 37.304 (170) |
| hind_same_half | 2023-25 | 12.566 (6800) | 21.236 (3003) | 27.309 (1792) | 32.669 (651) | 38.380 (137) |
| hind_all | 2019-22 | 13.285 (8248) | 21.121 (4172) | 28.927 (2521) | 32.233 (965) | 37.346 (170) |
| hind_all | 2023-25 | 12.576 (6800) | 21.258 (3003) | 27.392 (1792) | 32.615 (651) | 38.599 (137) |
| hind_all_half | 2019-22 | 13.292 (8248) | 21.083 (4172) | 28.902 (2521) | 32.204 (965) | 37.259 (170) |
| hind_all_half | 2023-25 | 12.583 (6800) | 21.221 (3003) | 27.341 (1792) | 32.599 (651) | 38.412 (137) |
| asof_same | 2019-22 | 13.274 (8248) | 21.054 (4172) | 28.924 (2521) | 32.271 (965) | 37.412 (170) |
| asof_same | 2023-25 | 12.552 (6800) | 21.267 (3003) | 27.326 (1792) | 32.816 (651) | 38.504 (137) |
| asof_same_half | 2019-22 | 13.286 (8248) | 21.030 (4172) | 28.890 (2521) | 32.214 (965) | 37.309 (170) |
| asof_same_half | 2023-25 | 12.567 (6800) | 21.239 (3003) | 27.302 (1792) | 32.678 (651) | 38.380 (137) |
| asof_all | 2019-22 | 13.290 (8248) | 21.120 (4172) | 28.922 (2521) | 32.230 (965) | 37.341 (170) |
| asof_all | 2023-25 | 12.573 (6800) | 21.262 (3003) | 27.371 (1792) | 32.613 (651) | 38.599 (137) |
| asof_all_half | 2019-22 | 13.296 (8248) | 21.083 (4172) | 28.900 (2521) | 32.204 (965) | 37.277 (170) |
| asof_all_half | 2023-25 | 12.582 (6800) | 21.225 (3003) | 27.330 (1792) | 32.597 (651) | 38.412 (137) |

### rush

Absences: 1326 of 5084 frame team-games have a hindsight absence (1501 player-games, by position {'RB': 1434, 'QB': 67}, mean absent share 0.421); 1179 as-of absences, 1177 of them also absent in hindsight, 2 listed out who then played. Fit: 1068 team-games 2017-18, absences by position {'RB': 258, 'QB': 3, 'WR': 0, 'TE': 0}, fitted positions ['RB'].

| recipient \ absent | intercept | RB |
|:--|--:|--:|
| RB | -0.040 | +0.348 |
| QB | +0.002 | +0.010 |
| WR | -0.003 | +0.012 |
| all | -0.041 | +0.371 |

#### rush, touch frame

carries (volume)

| variant | 2017-18 MAE | bias | SE vs base | 2019-22 MAE | bias | SE vs base | 2023-25 MAE | bias | SE vs base |
|:--|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| base | 3.1066 | -0.34 | 0.0000 | 2.9828 | -0.45 | 0.0000 | 2.8765 | -0.33 | 0.0000 |
| hind_same | 3.1014 | -0.02 | 0.0167 | 2.9532 | -0.14 | 0.0104 | 2.8413 | -0.10 | 0.0098 |
| hind_same_half | 3.0901 | -0.18 | 0.0087 | 2.9520 | -0.29 | 0.0055 | 2.8486 | -0.21 | 0.0051 |
| hind_all | 3.1211 | +0.00 | 0.0154 | 2.9705 | -0.11 | 0.0097 | 2.8606 | -0.09 | 0.0088 |
| hind_all_half | 3.1001 | -0.17 | 0.0079 | 2.9616 | -0.28 | 0.0051 | 2.8586 | -0.21 | 0.0045 |
| asof_same | 3.0999 | -0.15 | 0.0128 | 2.9411 | -0.18 | 0.0097 | 2.8415 | -0.13 | 0.0093 |
| asof_same_half | 3.0942 | -0.25 | 0.0066 | 2.9484 | -0.32 | 0.0052 | 2.8494 | -0.23 | 0.0049 |
| asof_all | 3.1109 | -0.14 | 0.0121 | 2.9599 | -0.16 | 0.0090 | 2.8615 | -0.11 | 0.0083 |
| asof_all_half | 3.0998 | -0.24 | 0.0063 | 2.9588 | -0.30 | 0.0047 | 2.8597 | -0.22 | 0.0043 |

yards

| variant | 2017-18 MAE | bias | SE vs base | 2019-22 MAE | bias | SE vs base | 2023-25 MAE | bias | SE vs base |
|:--|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| base | 18.080 | -4.45 | 0.000 | 17.780 | -5.22 | 0.000 | 17.041 | -4.69 | 0.000 |
| hind_same | 18.099 | -3.44 | 0.057 | 17.728 | -4.23 | 0.038 | 16.983 | -3.99 | 0.035 |
| hind_same_half | 18.040 | -3.93 | 0.031 | 17.715 | -4.71 | 0.020 | 16.975 | -4.33 | 0.019 |
| hind_all | 18.146 | -3.36 | 0.051 | 17.785 | -4.14 | 0.034 | 17.057 | -3.94 | 0.030 |
| hind_all_half | 18.076 | -3.89 | 0.028 | 17.752 | -4.66 | 0.019 | 17.026 | -4.30 | 0.016 |
| asof_same | 18.067 | -3.84 | 0.045 | 17.700 | -4.35 | 0.035 | 16.972 | -4.07 | 0.033 |
| asof_same_half | 18.053 | -4.13 | 0.024 | 17.702 | -4.77 | 0.019 | 16.973 | -4.37 | 0.018 |
| asof_all | 18.090 | -3.79 | 0.041 | 17.762 | -4.27 | 0.032 | 17.048 | -4.02 | 0.029 |
| asof_all_half | 18.071 | -4.11 | 0.022 | 17.742 | -4.73 | 0.018 | 17.024 | -4.34 | 0.015 |

#### rush, active frame

carries (volume)

| variant | 2017-18 MAE | bias | SE vs base | 2019-22 MAE | bias | SE vs base | 2023-25 MAE | bias | SE vs base |
|:--|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| base | 2.8214 | -0.00 | 0.0000 | 2.3925 | -0.02 | 0.0000 | 2.1748 | +0.03 | 0.0000 |
| hind_same | 2.8258 | +0.26 | 0.0134 | 2.3842 | +0.20 | 0.0072 | 2.1572 | +0.18 | 0.0064 |
| hind_same_half | 2.8128 | +0.13 | 0.0070 | 2.3787 | +0.09 | 0.0038 | 2.1593 | +0.11 | 0.0033 |
| hind_all | 2.8490 | +0.28 | 0.0120 | 2.4014 | +0.22 | 0.0064 | 2.1749 | +0.19 | 0.0055 |
| hind_all_half | 2.8255 | +0.14 | 0.0062 | 2.3882 | +0.10 | 0.0033 | 2.1688 | +0.11 | 0.0029 |
| asof_same | 2.8221 | +0.16 | 0.0103 | 2.3750 | +0.17 | 0.0067 | 2.1561 | +0.17 | 0.0060 |
| asof_same_half | 2.8146 | +0.08 | 0.0054 | 2.3755 | +0.07 | 0.0035 | 2.1591 | +0.10 | 0.0032 |
| asof_all | 2.8340 | +0.17 | 0.0094 | 2.3930 | +0.18 | 0.0060 | 2.1736 | +0.17 | 0.0052 |
| asof_all_half | 2.8216 | +0.08 | 0.0049 | 2.3855 | +0.08 | 0.0031 | 2.1686 | +0.10 | 0.0027 |

yards

| variant | 2017-18 MAE | bias | SE vs base | 2019-22 MAE | bias | SE vs base | 2023-25 MAE | bias | SE vs base |
|:--|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| base | 15.782 | -2.89 | 0.000 | 13.561 | -2.86 | 0.000 | 12.320 | -2.44 | 0.000 |
| hind_same | 15.805 | -2.08 | 0.045 | 13.551 | -2.19 | 0.025 | 12.287 | -1.98 | 0.022 |
| hind_same_half | 15.762 | -2.48 | 0.025 | 13.533 | -2.51 | 0.013 | 12.280 | -2.20 | 0.012 |
| hind_all | 15.869 | -2.03 | 0.039 | 13.606 | -2.13 | 0.021 | 12.354 | -1.95 | 0.019 |
| hind_all_half | 15.805 | -2.45 | 0.021 | 13.568 | -2.48 | 0.011 | 12.325 | -2.19 | 0.010 |
| asof_same | 15.784 | -2.40 | 0.036 | 13.528 | -2.27 | 0.024 | 12.279 | -2.03 | 0.021 |
| asof_same_half | 15.768 | -2.64 | 0.019 | 13.523 | -2.55 | 0.013 | 12.279 | -2.23 | 0.011 |
| asof_all | 15.818 | -2.37 | 0.030 | 13.586 | -2.22 | 0.020 | 12.347 | -2.00 | 0.018 |
| asof_all_half | 15.791 | -2.62 | 0.016 | 13.560 | -2.53 | 0.011 | 12.323 | -2.21 | 0.009 |

#### rush by tier of the base yards line (yards MAE, n), touch frame

| variant | window | 0-20 (n) | 20-40 (n) | 40-60 (n) | 60-80 (n) | 80+ (n) |
|:--|:--|--:|--:|--:|--:|--:|
| base | 2019-22 | 10.625 (3990) | 21.443 (1805) | 27.490 (1315) | 30.420 (557) | 36.975 (111) |
| base | 2023-25 | 10.746 (3157) | 18.907 (1420) | 26.065 (1069) | 29.925 (468) | 35.928 (82) |
| hind_same | 2019-22 | 10.539 (3990) | 21.282 (1805) | 27.487 (1315) | 30.806 (557) | 37.127 (111) |
| hind_same | 2023-25 | 10.653 (3157) | 18.803 (1420) | 26.114 (1069) | 29.931 (468) | 36.191 (82) |
| hind_same_half | 2019-22 | 10.550 (3990) | 21.283 (1805) | 27.466 (1315) | 30.607 (557) | 37.021 (111) |
| hind_same_half | 2023-25 | 10.675 (3157) | 18.780 (1420) | 26.056 (1069) | 29.908 (468) | 36.038 (82) |
| hind_all | 2019-22 | 10.639 (3990) | 21.332 (1805) | 27.456 (1315) | 30.794 (557) | 37.103 (111) |
| hind_all | 2023-25 | 10.732 (3157) | 18.932 (1420) | 26.157 (1069) | 29.896 (468) | 36.173 (82) |
| hind_all_half | 2019-22 | 10.604 (3990) | 21.332 (1805) | 27.458 (1315) | 30.600 (557) | 37.013 (111) |
| hind_all_half | 2023-25 | 10.727 (3157) | 18.871 (1420) | 26.085 (1069) | 29.895 (468) | 36.022 (82) |
| asof_same | 2019-22 | 10.533 (3990) | 21.232 (1805) | 27.446 (1315) | 30.709 (557) | 37.127 (111) |
| asof_same | 2023-25 | 10.654 (3157) | 18.747 (1420) | 26.091 (1069) | 29.989 (468) | 36.340 (82) |
| asof_same_half | 2019-22 | 10.549 (3990) | 21.259 (1805) | 27.449 (1315) | 30.558 (557) | 37.021 (111) |
| asof_same_half | 2023-25 | 10.676 (3157) | 18.756 (1420) | 26.052 (1069) | 29.946 (468) | 36.135 (82) |
| asof_all | 2019-22 | 10.633 (3990) | 21.317 (1805) | 27.402 (1315) | 30.697 (557) | 37.103 (111) |
| asof_all | 2023-25 | 10.729 (3157) | 18.892 (1420) | 26.133 (1069) | 29.956 (468) | 36.319 (82) |
| asof_all_half | 2019-22 | 10.602 (3990) | 21.327 (1805) | 27.435 (1315) | 30.551 (557) | 37.013 (111) |
| asof_all_half | 2023-25 | 10.726 (3157) | 18.853 (1420) | 26.080 (1069) | 29.934 (468) | 36.123 (82) |

## Verdicts

| part | kind | variant | yards better on both (touch) | volume not worse on both (touch) | active-frame check | verdict |
|--:|:--|:--|:--|:--|:--|:--|
| 1 | rec | refit | False | True | passes | not adopted |
| 1 | rec | winprob | False | True | passes | not adopted |
| 1 | rec | quad | False | True | passes | not adopted |
| 1 | rec | pace_0.25 | True | True | fails | not adopted |
| 1 | rec | pace_0.5 | False | True | fails | not adopted |
| 1 | rush | refit | False | False | fails | not adopted |
| 1 | rush | winprob | False | False | fails | not adopted |
| 1 | rush | quad | True | False | fails | not adopted |
| 1 | rush | pace_0.25 | True | True | passes | ADOPT |
| 1 | rush | pace_0.5 | False | True | fails | not adopted |
| 1 | pass | refit | False | True | n/a | not adopted |
| 1 | pass | winprob | False | True | n/a | not adopted |
| 1 | pass | quad | False | True | n/a | not adopted |
| 1 | pass | pace_0.25 | False | True | n/a | not adopted |
| 1 | pass | pace_0.5 | False | False | n/a | not adopted |
| 2 | rec | hind_same | True | True | fails | not adopted |
| 2 | rec | hind_same_half | True | True | passes | ADOPT |
| 2 | rec | hind_all | False | False | fails | not adopted |
| 2 | rec | hind_all_half | True | True | fails | not adopted |
| 2 | rec | asof_same | True | False | fails | not adopted |
| 2 | rec | asof_same_half | True | True | passes | ADOPT |
| 2 | rec | asof_all | False | False | fails | not adopted |
| 2 | rec | asof_all_half | True | True | fails | not adopted |
| 2 | rush | hind_same | True | True | passes | ADOPT |
| 2 | rush | hind_same_half | True | True | passes | ADOPT |
| 2 | rush | hind_all | False | True | fails | not adopted |
| 2 | rush | hind_all_half | True | True | fails | not adopted |
| 2 | rush | asof_same | True | True | passes | ADOPT |
| 2 | rush | asof_same_half | True | True | passes | ADOPT |
| 2 | rush | asof_all | False | True | fails | not adopted |
| 2 | rush | asof_all_half | True | True | fails | not adopted |

## Decision

**Part 1.** The live line is not stale: refit on 2016-18 with today's frame (the model's margin and total) the constants move a little (the passing margin slope halves, -0.046 to -0.023) and the in-sample fit improves by hundredths of a play, but on the held-out windows the refit, the win-probability form and the quadratic form are each within one paired standard error of base on yards for every kind, and none lowers yards MAE on both windows for receiving or passing. Rushing: quad lowers yards on both windows (17.7805 / 17.0413 -> 17.7804 / 17.0337) but raises carries on both, so it fails the rule. Opponent pace at a quarter (pace_0.25) is the one game-script change that passes: rushing carries 2.9828 / 2.8765 -> 2.9677 / 2.8657 (4 and 3 paired standard errors) and rushing yards 17.7805 / 17.0413 -> 17.7669 / 17.0356 (1.3 and 0.5 standard errors), the active frame agreeing (carries 2.3925 / 2.1748 -> 2.3822 / 2.1668, yards 13.5611 / 12.3205 -> 13.5507 / 12.3160). Adopted by the rule as set; the yards gain is inside the noise, the carries gain is not. For receiving pace_0.25 lowers targets on both windows by 4 standard errors (1.8302 / 1.7186 -> 1.8264 / 1.7142) and yards on both (19.1565 / 18.1573 -> 19.1543 / 18.1419), but the active-frame check is a tie on 2019-22 (16.8346 -> 16.8349, +0.0003 yards, 0.07 standard errors), which the rule as written counts as a fail: flagged, not adopted by the letter of the rule; Matt's call whether a tie at the fourth decimal should block it (round 4 had found nothing for receiving pace on its frame). pace_0.5 loses to pace_0.25 everywhere. Passing keeps its 0.25 (pace_0.5 raises dropbacks and yards on 2019-22).

**Part 2.** Absorption at a fitted fraction works where round ten's pro rata did not, and only to the same position: the fitted fractions say an absent wideout's share goes 0.42 to the other wideouts and 0.03 to the tight ends, an absent tight end's 0.25 to the tight ends and 0.29 to the wideouts, an absent back's 0.35 to the other backs, with negative intercepts (the frame's players' projected shares already add to more than what happens); handing the fraction to all teammates (hind_all, asof_all) raises volume MAE and fails on both kinds. The as-of absence (the injury report's Out / Doubtful or a roster status other than active, what the live rule can know) is as good as or better than the hindsight ceiling: the absences the report does not flag (a healthy scratch, a demoted player) are not worth absorbing. Rushing: asof_same (f = 0.348) lowers carries 2.9828 / 2.8765 -> 2.9411 / 2.8415 (4 standard errors each) and yards 17.7805 / 17.0413 -> 17.6997 / 16.9723 (2.3 and 2.1), the active frame 13.5611 / 12.3205 -> 13.5282 / 12.2792; asof_same_half (f = 0.174) the same yards at half the standard error (17.7020 / 16.9729, 4.2 and 3.9 standard errors; active 13.5232 / 12.2794) and carries 2.9484 / 2.8494. Receiving: asof_same at the fitted f raises targets on 2019-22 and yards on the active frame and fails; asof_same_half (f = 0.211 WR, 0.125 TE) passes everything: targets 1.8302 / 1.7186 -> 1.8258 / 1.7128 (3.4 and 4 standard errors), yards 19.1565 / 18.1573 -> 19.1328 / 18.1454 (2.6 and 1.2), active 16.8346 / 15.6969 -> 16.8210 / 15.6936. Both multipliers pass for rushing; the multiplier is chosen on the fit window, as round 17 chose its blend weight: on 2017-18 the half is better on both kinds (rushing yards 18.053 against 18.067, carries 3.094 against 3.100; receiving 19.691 against 19.694, targets 1.875 against 1.878), so the half is adopted for both. By tier the gains sit in the 0-60 tiers; the 80+ tier of the base line is 0.1 to 0.2 yards worse on both kinds (its lines rise), a small cost inside a small tier. Receptions were not scored here; they follow the targets figure (round 17), which improved.

**Adopted (rule as set):** part 1, PACE['rush'] 0 -> 0.25 (the live line on top, as passing already does); part 2, same-position absorption at half the fitted fraction for an absent teammate the injury report or roster says is out. Flagged for Matt: receiving pace_0.25 (a tie at the fourth decimal on the active check). Constants and the change to nflmodel/props.py:

```python
PACE = {"rec": 0.0, "rush": 0.25, "pass": 0.25}   # round 18: rushing a quarter toward the opponent's allowed runs per game (reports/props_gs_absorb.csv, part 1 pace_0.25)
# round 18 (29 Sep 2026, reports/props_gs_absorb.csv, part 2): when a teammate the report or roster says is out (project_game's OUT_WORDS) was
# active in one of the team's last ABSORB_LOOKBACK games and his share behind the yards line is >= ABSORB_THR, the players of his position
# group who play get ABSORB[kind][group] x his share, split in proportion to their own shares (half the least-squares fraction absorbed by
# the same position, fitted on 2017-18: WR 0.422, TE 0.249, RB 0.348; the half chosen on the fit window). Not to other positions, not
# to the touchdown share (untested), never pro rata of the whole (round ten).
ABSORB = {"rec": {"WR": 0.211, "TE": 0.125}, "rush": {"RB": 0.174}}
ABSORB_THR = {"rec": 0.15, "rush": 0.25}; ABSORB_LOOKBACK = 3
ABSORB_GROUP = {"WR": "WR", "TE": "TE", "RB": "RB", "FB": "RB", "HB": "RB"}


def recent_players(active: pd.DataFrame | None, team: str, n: int = ABSORB_LOOKBACK) -> set:
    """The players with a snap in one of the team's last n games (snap counts as of the week; props.active_games)."""
    if active is None or not len(active): return set()
    a = active[active.posteam == team]; last = a.drop_duplicates("game_id").sort_values(["season", "week"]).game_id.tail(n)
    return set(a[a.game_id.isin(last)].player_id)


def absorb(rows: list, kind: str, recent: set) -> None:
    """Round 18: part of an absent starter's share_yds to his same-position teammates who play, in proportion to their shares."""
    for a in [r for r in rows if r["out"] and r["player_id"] in recent and r["share_yds"] >= ABSORB_THR[kind] and ABSORB_GROUP.get(r["pos"], "") in ABSORB[kind]]:
        grp = ABSORB_GROUP[a["pos"]]; to = [r for r in rows if not r["out"] and ABSORB_GROUP.get(r["pos"], "") == grp]; tot = sum(r["share_yds"] for r in to)
        if tot <= 0: continue
        for r in to: r["absorbed"] = round(r.get("absorbed", 0.0) + ABSORB[kind][grp] * a["share_yds"] * r["share_yds"] / tot, 4); r["share_yds"] = round(r["share_yds"] + ABSORB[kind][grp] * a["share_yds"] * r["share_yds"] / tot, 3)
```

In project_game (which needs the as-of snap counts: add a `recent: set | None = None` argument and pass `recent_players(AG, team)` from main, AG being the active_games frame main already loads for round 14), call `absorb(rec, "rec", recent or set())` just before the loop that sets proj_targets from share_yds, and `absorb(rus, "rush", recent or set())` before the loop that sets proj_carries. The touchdown share (share_td) is untouched. The backtest's absent player is one with no active listing or an Out / Doubtful report; the live rule sees the roster's Out, Doubtful, IR, PUP, Suspended, Exempt, NFI, Retired (project_game's OUT_WORDS), the same set, and cannot see a player cut off the roster (his row is gone), a small under-count of the backtest's as-of set. PACE is already in the props.json header; add ABSORB and ABSORB_THR beside it. The two rushing changes were scored one at a time, not together; once both are in, the by-season run sets BACKTEST (about 19.13 / 18.15 receiving from 19.16 / 18.16, 17.70 / 16.97 rushing from 17.77 / 17.04, if they add).

## Runtime

part1 1s, part2_rec 2s, part2_rush 1s; total 6s (4 cores shared with other studies). The frames are built once and cached (/tmp/claude-0/-home-user/c1e0d18e-681a-50ba-b0bb-6c809c2e3dee/scratchpad/props_gs): the first run loaded props_by_season's state in 10s and built the receiving, rushing and passing frames in 13s, 9s and 3s; a run from the cache scores everything in about 6s (--rebuild forces a rebuild).
