# Are the player rankings predictive?

Every player-week 2019-2025 (weeks 2-18): how well each predictor, as of the week, predicts the player's EPA per play over his next four games in that role (same season, all four required; passers 80+ dropbacks, rushers 20+ carries, receivers 12+ targets, defenders 100+ snaps over the four).
`value` is the live value (PlayerValues with DEFAULT, decay 0.985 / k 480 / 10th percentile prior; role_rates for defenders). `last4/8/17` are unshrunk trailing averages, `season_to_date` is season to date, `last_season` last season's rate; a predictor with no history is the replacement level. `d{decay}_k{k}` is the live value at other knobs. Defenders also get `def_plain_page`: the plain decayed, shrunk EPA per snap at the page's DEF_DECAY 0.92 / fade 0.8 / K 300.

Metrics: `corr` plays-weighted Pearson correlation with next-4 EPA per play; `mae` plays-weighted mean absolute error; `spearman` per-week Spearman rank correlation among regulars (100+ plays in the window), averaged over weeks; `corr_total` / `spearman_total` the same against next-4 total EPA; `corr_own` / `spearman_own` (defenders) against the recipe's own target per snap (coverage for CB; coverage plus half the rest for S and IDL; everything plus 0.75 a credited play for LB; everything for EDGE); `churn_top40` mean absolute week-to-week rank change of the top 40 among players active that season. Nothing was fit on 2023-25; k 60 is beyond the asked grid, added because the grid's edge (120) won everywhere.

## Summary (29 Sep 2026)

**Skill players: yes, and the value beats the plain averages.** For passers, rushers and receivers the live value's
correlation with the next four games' EPA per play is above every trailing average, the season to date and last
season on both windows (passer 0.383 / 0.505 against last17's 0.371 / 0.404; rusher 0.271 / 0.286 against 0.251 /
0.285; receiver 0.204 / 0.216 against 0.146 / 0.190). The one place a plain average keeps up is the rank order among
regulars: an unshrunk 17-game average ranks passers and rushers about as well as the value (Spearman 0.347 / 0.508
against 0.335 / 0.482 for passers, 0.230 / 0.223 against 0.179 / 0.156 for rushers), because 480 plays of shrinkage
toward the 10th percentile pulls regulars with a season of evidence toward one another. The value's MAE is also
worse than last17's for passers for the same reason (the prior is replacement level, so every estimate is biased
low); the correlation and rank measures are what a ranking is judged on.

**Knobs: the shrinkage is too heavy for the ranking; the decay is fine.** In the decay x k grid, k is what moves
the result and lighter is better everywhere: at decay 0.985, k 120 beats DEFAULT's k 480 on both windows for all
three roles on correlation, rank correlation and MAE (passer 0.397 / 0.530 against 0.383 / 0.505; rusher 0.344 /
0.345 against 0.271 / 0.286; receiver 0.212 / 0.237 against 0.204 / 0.216), and k 60 (beyond the asked grid, added
because the grid's edge won) is better still for rushers (0.363 / 0.367) and about level for passers and receivers.
Decay 0.97 against 0.985 is worth about 0.005 for passers and receivers and nothing for rushers; 1.0 is worse for
passers and receivers. The cost is churn: the top 40 move 0.9 places a week at k 480 and 1.1 at k 120 for passers,
1.6 to 1.6 for rushers, 1.5 to 2.3 for receivers; still far below any trailing average (last17: 2.6, 5.7, 12.4).
Recommendation: keep decay 0.985, and for the ranking use k 120 (better on both windows for every role, and the
same direction the All-Pro check found on 24 Sep: allpro_skill_k120.csv). The catch is that DEFAULT is shared with
the game model's skill-out inputs, where the 23 Sep sweep chose 480 on team-points miss (reports/player_knobs.csv).
That sweep was about a different question (how much a listed-out player costs his team, where usage carries the
value and the rate is mostly noise); this one is about ordering players by their own rate. So either the page's
ranking gets its own k (120) and the game model keeps 480, or player_knobs is re-run at 120 before any shared change.
Nothing under nflmodel/ was changed here.

**Defenders: EDGE and IDL are predictive and the recipes earn their keep; CB, S and LB are weak.** The group
recipes (positions.role_rates) for edge rushers and interior linemen beat every trailing average, last season and
the plain decayed EPA per snap at the page's recency on both windows (EDGE 0.300 / 0.296, IDL 0.336 / 0.221 on
correlation; Spearman about 0.30 and 0.33 / 0.24). Cornerbacks are the weak spot: the CB rate's correlation with
the next four games is 0.138 / 0.053 and its rank correlation among regulars 0.137 / 0.035, and the picture is the
same against its own target, coverage per snap (0.117 / 0.066; Spearman 0.119 / 0.039): a corner's next month is
close to unpredictable from his last one at this horizon, and the plain decayed EPA per snap (0.161 / 0.111 at
0.985 / 480) does better than the coverage recipe on both windows. Safeties (0.139 / 0.129) and linebackers (0.084 /
0.091) are the same story: the plain rate beats the recipe on both windows (S 0.181 / 0.165, LB 0.170 / 0.136), and
the LB recipe's 0.75 EPA per credited play, chosen on All-Pro placement, does not help it predict even its own
target (0.128 / 0.092). These recipes were picked on where All-Pros land and on a corner's coverage the next season,
not on a four-game forecast, so this is a second yardstick rather than a reversal; but on this yardstick the CB, S
and LB rankings carry little signal and the plain rate would be the better choice. Churn for defenders is 1.1 to 3.0
places a week for the live values against 5 to 17 for the trailing averages.

**Sizes.** 3,615 passer, 6,802 rusher and 16,812 receiver player-weeks; 7,500 to 11,200 per defender group.

## Tables

## passer

Player-weeks: 1992 (2019-22), 1623 (2023-25).

| predictor | corr 19-22 | corr 23-25 | mae 19-22 | mae 23-25 | spearman 19-22 | spearman 23-25 | corr_total 19-22 | corr_total 23-25 | churn 19-22 | churn 23-25 |
|---|---|---|---|---|---|---|---|---|---|---|
| value | 0.383 | 0.505 | 0.1481 | 0.1533 | 0.335 | 0.482 | 0.404 | 0.513 | 0.9 | 0.9 |
| last4 | 0.274 | 0.345 | 0.1794 | 0.1811 | 0.227 | 0.386 | 0.278 | 0.337 | 4.8 | 5.1 |
| last8 | 0.323 | 0.384 | 0.1554 | 0.1576 | 0.303 | 0.443 | 0.329 | 0.376 | 3.5 | 3.4 |
| last17 | 0.371 | 0.404 | 0.1427 | 0.1476 | 0.347 | 0.508 | 0.376 | 0.394 | 2.6 | 2.4 |
| season_to_date | 0.329 | 0.389 | 0.1748 | 0.1893 | 0.330 | 0.440 | 0.335 | 0.384 | 3.4 | 3.1 |
| last_season | 0.328 | 0.345 | 0.1622 | 0.1715 | 0.332 | 0.383 | 0.341 | 0.345 | 0.8 | 0.7 |
| d0.97_k60 | 0.400 | 0.539 | 0.1341 | 0.1316 | 0.367 | 0.524 | 0.416 | 0.541 | 1.6 | 1.4 |
| d0.97_k120 | 0.402 | 0.539 | 0.1352 | 0.1351 | 0.366 | 0.522 | 0.419 | 0.542 | 1.4 | 1.3 |
| d0.97_k240 | 0.400 | 0.533 | 0.1406 | 0.1442 | 0.361 | 0.513 | 0.418 | 0.538 | 1.2 | 1.2 |
| d0.97_k480 | 0.393 | 0.521 | 0.1539 | 0.1622 | 0.356 | 0.499 | 0.414 | 0.528 | 1.1 | 1.1 |
| d0.97_k960 | 0.384 | 0.505 | 0.1775 | 0.1892 | 0.346 | 0.486 | 0.406 | 0.514 | 1.0 | 1.1 |
| d0.985_k60 | 0.395 | 0.531 | 0.1349 | 0.1317 | 0.357 | 0.512 | 0.411 | 0.534 | 1.3 | 1.2 |
| d0.985_k120 | 0.397 | 0.530 | 0.1357 | 0.1338 | 0.353 | 0.514 | 0.414 | 0.534 | 1.1 | 1.1 |
| d0.985_k240 | 0.393 | 0.522 | 0.1390 | 0.1400 | 0.347 | 0.506 | 0.412 | 0.527 | 1.0 | 1.0 |
| d0.985_k480 | 0.383 | 0.505 | 0.1481 | 0.1533 | 0.335 | 0.482 | 0.404 | 0.513 | 0.9 | 0.9 |
| d0.985_k960 | 0.368 | 0.484 | 0.1655 | 0.1744 | 0.324 | 0.466 | 0.390 | 0.494 | 0.8 | 0.9 |
| d1_k60 | 0.391 | 0.518 | 0.1359 | 0.1334 | 0.347 | 0.496 | 0.407 | 0.522 | 1.1 | 1.0 |
| d1_k120 | 0.392 | 0.516 | 0.1367 | 0.1348 | 0.344 | 0.495 | 0.409 | 0.521 | 0.9 | 0.9 |
| d1_k240 | 0.387 | 0.506 | 0.1392 | 0.1390 | 0.339 | 0.485 | 0.406 | 0.513 | 0.8 | 0.9 |
| d1_k480 | 0.373 | 0.486 | 0.1455 | 0.1480 | 0.329 | 0.463 | 0.394 | 0.495 | 0.7 | 0.8 |
| d1_k960 | 0.352 | 0.459 | 0.1570 | 0.1626 | 0.315 | 0.440 | 0.375 | 0.470 | 0.6 | 0.8 |

**Verdict (passer).** The live value's correlation with the next four games is 0.383 (2019-22) and 0.505 (2023-25); rank correlation among regulars 0.335 and 0.482. It does not beat every simple average on both windows: last17 (beaten on 2/2 windows by correlation, 0/2 by rank correlation). The strongest simple alternative is last17 (corr 0.371 / 0.404).
Knobs: the best grid cell on 2019-22 is d0.97_k120 (corr 0.402, held out 0.539); DEFAULT d0.985_k480 is 0.383 / 0.505. Cells better than DEFAULT on both windows (correlation up, rank correlation not down): d0.97_k60 (0.400 / 0.539), d0.97_k120 (0.402 / 0.539), d0.97_k240 (0.400 / 0.533), d0.97_k480 (0.393 / 0.521), d0.985_k60 (0.395 / 0.531), d0.985_k120 (0.397 / 0.530), d0.985_k240 (0.393 / 0.522), d1_k60 (0.391 / 0.518), d1_k120 (0.392 / 0.516), d1_k240 (0.387 / 0.506).
Churn: the top 40 by the live value move 0.9 places a week (2019-22) and 0.9 (2023-25); by last4 4.8 / 5.1, by last17 2.6 / 2.4.

## rusher

Player-weeks: 3902 (2019-22), 2900 (2023-25).

| predictor | corr 19-22 | corr 23-25 | mae 19-22 | mae 23-25 | spearman 19-22 | spearman 23-25 | corr_total 19-22 | corr_total 23-25 | churn 19-22 | churn 23-25 |
|---|---|---|---|---|---|---|---|---|---|---|
| value | 0.271 | 0.286 | 0.1479 | 0.1438 | 0.179 | 0.156 | 0.254 | 0.255 | 1.6 | 1.3 |
| last4 | 0.179 | 0.231 | 0.1853 | 0.1819 | 0.135 | 0.199 | 0.167 | 0.212 | 9.7 | 10.9 |
| last8 | 0.207 | 0.248 | 0.1646 | 0.1634 | 0.149 | 0.212 | 0.188 | 0.223 | 7.0 | 6.7 |
| last17 | 0.251 | 0.285 | 0.1484 | 0.1513 | 0.230 | 0.223 | 0.225 | 0.253 | 5.7 | 5.2 |
| season_to_date | 0.201 | 0.262 | 0.1787 | 0.1740 | 0.181 | 0.233 | 0.185 | 0.236 | 8.8 | 8.2 |
| last_season | 0.168 | 0.221 | 0.1659 | 0.1627 | 0.180 | 0.130 | 0.156 | 0.201 | 1.5 | 1.2 |
| d0.97_k60 | 0.358 | 0.360 | 0.1340 | 0.1322 | 0.237 | 0.218 | 0.330 | 0.322 | 2.2 | 2.1 |
| d0.97_k120 | 0.339 | 0.335 | 0.1371 | 0.1346 | 0.221 | 0.200 | 0.314 | 0.300 | 2.2 | 1.9 |
| d0.97_k240 | 0.309 | 0.304 | 0.1428 | 0.1400 | 0.204 | 0.183 | 0.289 | 0.273 | 2.2 | 1.9 |
| d0.97_k480 | 0.274 | 0.272 | 0.1506 | 0.1474 | 0.188 | 0.165 | 0.259 | 0.245 | 2.0 | 1.8 |
| d0.97_k960 | 0.242 | 0.244 | 0.1583 | 0.1552 | 0.171 | 0.147 | 0.230 | 0.221 | 2.0 | 1.8 |
| d0.985_k60 | 0.363 | 0.367 | 0.1334 | 0.1316 | 0.238 | 0.218 | 0.332 | 0.327 | 1.8 | 1.7 |
| d0.985_k120 | 0.344 | 0.345 | 0.1359 | 0.1332 | 0.223 | 0.199 | 0.316 | 0.306 | 1.6 | 1.5 |
| d0.985_k240 | 0.311 | 0.317 | 0.1408 | 0.1373 | 0.202 | 0.176 | 0.289 | 0.281 | 1.6 | 1.4 |
| d0.985_k480 | 0.271 | 0.286 | 0.1479 | 0.1438 | 0.179 | 0.156 | 0.254 | 0.255 | 1.6 | 1.3 |
| d0.985_k960 | 0.232 | 0.256 | 0.1557 | 0.1515 | 0.151 | 0.142 | 0.219 | 0.231 | 1.5 | 1.3 |
| d1_k60 | 0.363 | 0.369 | 0.1333 | 0.1315 | 0.237 | 0.215 | 0.331 | 0.328 | 1.4 | 1.4 |
| d1_k120 | 0.344 | 0.349 | 0.1353 | 0.1325 | 0.222 | 0.194 | 0.315 | 0.308 | 1.3 | 1.1 |
| d1_k240 | 0.309 | 0.324 | 0.1393 | 0.1353 | 0.199 | 0.171 | 0.285 | 0.285 | 1.2 | 1.0 |
| d1_k480 | 0.264 | 0.295 | 0.1454 | 0.1403 | 0.166 | 0.147 | 0.245 | 0.261 | 1.2 | 0.9 |
| d1_k960 | 0.217 | 0.267 | 0.1526 | 0.1470 | 0.133 | 0.132 | 0.202 | 0.238 | 1.2 | 0.9 |

**Verdict (rusher).** The live value's correlation with the next four games is 0.271 (2019-22) and 0.286 (2023-25); rank correlation among regulars 0.179 and 0.156. It does not beat every simple average on both windows: last4 (beaten on 2/2 windows by correlation, 1/2 by rank correlation), last8 (beaten on 2/2 windows by correlation, 1/2 by rank correlation), last17 (beaten on 2/2 windows by correlation, 0/2 by rank correlation), season_to_date (beaten on 2/2 windows by correlation, 0/2 by rank correlation), last_season (beaten on 2/2 windows by correlation, 1/2 by rank correlation). The strongest simple alternative is last17 (corr 0.251 / 0.285).
Knobs: the best grid cell on 2019-22 is d1_k60 (corr 0.363, held out 0.369); DEFAULT d0.985_k480 is 0.271 / 0.286. Cells better than DEFAULT on both windows (correlation up, rank correlation not down): d0.97_k60 (0.358 / 0.360), d0.97_k120 (0.339 / 0.335), d0.97_k240 (0.309 / 0.304), d0.985_k60 (0.363 / 0.367), d0.985_k120 (0.344 / 0.345), d0.985_k240 (0.311 / 0.317), d1_k60 (0.363 / 0.369), d1_k120 (0.344 / 0.349), d1_k240 (0.309 / 0.324).
Churn: the top 40 by the live value move 1.6 places a week (2019-22) and 1.3 (2023-25); by last4 9.7 / 10.9, by last17 5.7 / 5.2.

## receiver

Player-weeks: 9672 (2019-22), 7140 (2023-25).

| predictor | corr 19-22 | corr 23-25 | mae 19-22 | mae 23-25 | spearman 19-22 | spearman 23-25 | corr_total 19-22 | corr_total 23-25 | churn 19-22 | churn 23-25 |
|---|---|---|---|---|---|---|---|---|---|---|
| value | 0.204 | 0.216 | 0.3095 | 0.3230 | 0.193 | 0.210 | 0.316 | 0.327 | 1.5 | 1.4 |
| last4 | 0.087 | 0.122 | 0.3987 | 0.3986 | 0.112 | 0.113 | 0.108 | 0.147 | 24.4 | 24.0 |
| last8 | 0.112 | 0.163 | 0.3469 | 0.3451 | 0.147 | 0.158 | 0.132 | 0.189 | 15.2 | 15.7 |
| last17 | 0.146 | 0.190 | 0.3156 | 0.3158 | 0.211 | 0.193 | 0.163 | 0.220 | 12.4 | 11.6 |
| season_to_date | 0.077 | 0.121 | 0.4089 | 0.3925 | 0.120 | 0.132 | 0.091 | 0.144 | 18.4 | 18.9 |
| last_season | 0.137 | 0.153 | 0.3241 | 0.3235 | 0.177 | 0.176 | 0.163 | 0.182 | 1.1 | 0.9 |
| d0.97_k60 | 0.213 | 0.246 | 0.2804 | 0.2915 | 0.215 | 0.233 | 0.304 | 0.338 | 3.5 | 3.3 |
| d0.97_k120 | 0.216 | 0.243 | 0.2872 | 0.3005 | 0.210 | 0.231 | 0.319 | 0.346 | 3.1 | 2.7 |
| d0.97_k240 | 0.214 | 0.237 | 0.3007 | 0.3148 | 0.206 | 0.227 | 0.326 | 0.349 | 2.6 | 2.4 |
| d0.97_k480 | 0.210 | 0.230 | 0.3173 | 0.3314 | 0.202 | 0.222 | 0.328 | 0.348 | 2.3 | 2.2 |
| d0.97_k960 | 0.204 | 0.224 | 0.3323 | 0.3458 | 0.199 | 0.219 | 0.324 | 0.345 | 2.1 | 2.0 |
| d0.985_k60 | 0.211 | 0.241 | 0.2799 | 0.2899 | 0.211 | 0.229 | 0.299 | 0.331 | 2.7 | 2.3 |
| d0.985_k120 | 0.212 | 0.237 | 0.2844 | 0.2965 | 0.205 | 0.225 | 0.311 | 0.335 | 2.3 | 1.9 |
| d0.985_k240 | 0.209 | 0.228 | 0.2947 | 0.3079 | 0.199 | 0.217 | 0.316 | 0.333 | 1.8 | 1.6 |
| d0.985_k480 | 0.204 | 0.216 | 0.3095 | 0.3230 | 0.193 | 0.210 | 0.316 | 0.327 | 1.5 | 1.4 |
| d0.985_k960 | 0.197 | 0.206 | 0.3253 | 0.3383 | 0.188 | 0.204 | 0.311 | 0.319 | 1.5 | 1.2 |
| d1_k60 | 0.204 | 0.234 | 0.2808 | 0.2895 | 0.203 | 0.224 | 0.288 | 0.318 | 2.1 | 1.6 |
| d1_k120 | 0.205 | 0.228 | 0.2834 | 0.2942 | 0.196 | 0.216 | 0.298 | 0.320 | 1.6 | 1.3 |
| d1_k240 | 0.201 | 0.216 | 0.2905 | 0.3024 | 0.189 | 0.205 | 0.300 | 0.312 | 1.2 | 1.0 |
| d1_k480 | 0.193 | 0.200 | 0.3020 | 0.3147 | 0.179 | 0.194 | 0.295 | 0.298 | 1.0 | 0.8 |
| d1_k960 | 0.184 | 0.182 | 0.3161 | 0.3284 | 0.173 | 0.184 | 0.287 | 0.281 | 0.8 | 0.7 |

**Verdict (receiver).** The live value's correlation with the next four games is 0.204 (2019-22) and 0.216 (2023-25); rank correlation among regulars 0.193 and 0.210. It does not beat every simple average on both windows: last17 (beaten on 2/2 windows by correlation, 1/2 by rank correlation). The strongest simple alternative is last17 (corr 0.146 / 0.190).
Knobs: the best grid cell on 2019-22 is d0.97_k120 (corr 0.216, held out 0.243); DEFAULT d0.985_k480 is 0.204 / 0.216. Cells better than DEFAULT on both windows (correlation up, rank correlation not down): d0.97_k60 (0.213 / 0.246), d0.97_k120 (0.216 / 0.243), d0.97_k240 (0.214 / 0.237), d0.97_k480 (0.210 / 0.230), d0.985_k60 (0.211 / 0.241), d0.985_k120 (0.212 / 0.237), d0.985_k240 (0.209 / 0.228), d1_k60 (0.204 / 0.234), d1_k120 (0.205 / 0.228).
Churn: the top 40 by the live value move 1.5 places a week (2019-22) and 1.4 (2023-25); by last4 24.4 / 24.0, by last17 12.4 / 11.6.

## CB

Player-weeks: 5999 (2019-22), 4764 (2023-25).

| predictor | corr 19-22 | corr 23-25 | mae 19-22 | mae 23-25 | spearman 19-22 | spearman 23-25 | corr_total 19-22 | corr_total 23-25 | corr_own 19-22 | corr_own 23-25 | spearman_own 19-22 | spearman_own 23-25 | churn 19-22 | churn 23-25 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| value | 0.138 | 0.053 | 0.0227 | 0.0229 | 0.137 | 0.035 | 0.170 | 0.093 | 0.117 | 0.066 | 0.119 | 0.039 | 3.0 | 2.5 |
| last4 | 0.070 | 0.047 | 0.0317 | 0.0305 | 0.095 | 0.041 | 0.073 | 0.042 | 0.065 | 0.008 | 0.083 | -0.002 | 15.2 | 15.9 |
| last8 | 0.077 | 0.051 | 0.0282 | 0.0266 | 0.111 | 0.051 | 0.078 | 0.048 | 0.065 | 0.011 | 0.080 | -0.005 | 10.0 | 10.2 |
| last17 | 0.082 | 0.069 | 0.0264 | 0.0245 | 0.134 | 0.062 | 0.082 | 0.066 | 0.068 | 0.027 | 0.091 | 0.002 | 6.9 | 7.5 |
| season_to_date | -0.006 | 0.010 | 0.0323 | 0.0301 | 0.087 | 0.044 | 0.002 | 0.012 | -0.023 | -0.017 | 0.066 | 0.001 | 10.1 | 9.9 |
| last_season | 0.077 | 0.058 | 0.0258 | 0.0245 | 0.106 | 0.036 | 0.081 | 0.064 | 0.038 | 0.034 | 0.060 | 0.003 | 0.5 | 0.7 |
| def_plain_page | 0.145 | 0.091 | 0.0215 | 0.0213 | 0.147 | 0.077 | 0.164 | 0.115 | 0.098 | 0.034 | 0.110 | 0.021 | 6.8 | 7.7 |
| d0.97_k60 | 0.147 | 0.092 | 0.0225 | 0.0219 | 0.149 | 0.070 | 0.158 | 0.108 | 0.102 | 0.037 | 0.107 | 0.012 | 5.2 | 5.8 |
| d0.97_k120 | 0.153 | 0.098 | 0.0220 | 0.0215 | 0.153 | 0.073 | 0.167 | 0.119 | 0.103 | 0.041 | 0.110 | 0.016 | 4.7 | 5.3 |
| d0.97_k240 | 0.157 | 0.102 | 0.0215 | 0.0212 | 0.154 | 0.077 | 0.175 | 0.128 | 0.105 | 0.046 | 0.112 | 0.022 | 4.2 | 4.6 |
| d0.97_k480 | 0.159 | 0.105 | 0.0212 | 0.0210 | 0.153 | 0.077 | 0.181 | 0.135 | 0.106 | 0.051 | 0.113 | 0.025 | 3.8 | 4.0 |
| d0.97_k960 | 0.159 | 0.105 | 0.0212 | 0.0210 | 0.151 | 0.077 | 0.184 | 0.140 | 0.106 | 0.055 | 0.112 | 0.029 | 3.5 | 3.6 |
| d0.985_k60 | 0.147 | 0.097 | 0.0225 | 0.0219 | 0.150 | 0.072 | 0.159 | 0.113 | 0.102 | 0.043 | 0.107 | 0.016 | 4.7 | 5.2 |
| d0.985_k120 | 0.153 | 0.103 | 0.0220 | 0.0215 | 0.153 | 0.076 | 0.168 | 0.124 | 0.104 | 0.048 | 0.110 | 0.022 | 4.1 | 4.5 |
| d0.985_k240 | 0.158 | 0.108 | 0.0216 | 0.0212 | 0.154 | 0.079 | 0.176 | 0.134 | 0.105 | 0.053 | 0.112 | 0.028 | 3.6 | 3.9 |
| d0.985_k480 | 0.161 | 0.111 | 0.0212 | 0.0210 | 0.152 | 0.080 | 0.182 | 0.141 | 0.107 | 0.058 | 0.111 | 0.032 | 3.2 | 3.3 |
| d0.985_k960 | 0.161 | 0.111 | 0.0211 | 0.0210 | 0.148 | 0.077 | 0.186 | 0.145 | 0.107 | 0.062 | 0.108 | 0.033 | 2.9 | 2.8 |
| d1_k60 | 0.146 | 0.102 | 0.0225 | 0.0220 | 0.149 | 0.073 | 0.158 | 0.119 | 0.102 | 0.050 | 0.106 | 0.022 | 4.2 | 4.6 |
| d1_k120 | 0.153 | 0.110 | 0.0220 | 0.0216 | 0.151 | 0.077 | 0.168 | 0.130 | 0.103 | 0.055 | 0.108 | 0.027 | 3.5 | 3.8 |
| d1_k240 | 0.158 | 0.115 | 0.0216 | 0.0212 | 0.152 | 0.079 | 0.176 | 0.141 | 0.105 | 0.061 | 0.110 | 0.032 | 3.0 | 3.3 |
| d1_k480 | 0.161 | 0.118 | 0.0213 | 0.0210 | 0.150 | 0.079 | 0.183 | 0.148 | 0.107 | 0.066 | 0.110 | 0.036 | 2.6 | 2.6 |
| d1_k960 | 0.161 | 0.118 | 0.0211 | 0.0209 | 0.146 | 0.076 | 0.186 | 0.151 | 0.108 | 0.070 | 0.106 | 0.036 | 2.4 | 2.1 |

**Verdict (CB).** The live value's correlation with the next four games is 0.138 (2019-22) and 0.053 (2023-25); rank correlation among regulars 0.137 and 0.035. It does not beat every simple average on both windows: last4 (beaten on 2/2 windows by correlation, 1/2 by rank correlation), last8 (beaten on 2/2 windows by correlation, 1/2 by rank correlation), last17 (beaten on 1/2 windows by correlation, 1/2 by rank correlation), season_to_date (beaten on 2/2 windows by correlation, 1/2 by rank correlation), last_season (beaten on 1/2 windows by correlation, 1/2 by rank correlation). The strongest simple alternative is last17 (corr 0.082 / 0.069).
Against the plain decayed EPA per snap at the page's recency (def_plain_page: corr 0.145 / 0.091, spearman 0.147 / 0.077) the group recipe is not better on both windows. Best plain grid cell on 2019-22: d1_k480 (0.161 / 0.118).
Churn: the top 40 by the live value move 3.0 places a week (2019-22) and 2.5 (2023-25); by last4 15.2 / 15.9, by last17 6.9 / 7.5.

## S

Player-weeks: 5082 (2019-22), 3869 (2023-25).

| predictor | corr 19-22 | corr 23-25 | mae 19-22 | mae 23-25 | spearman 19-22 | spearman 23-25 | corr_total 19-22 | corr_total 23-25 | corr_own 19-22 | corr_own 23-25 | spearman_own 19-22 | spearman_own 23-25 | churn 19-22 | churn 23-25 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| value | 0.139 | 0.129 | 0.0201 | 0.0201 | 0.147 | 0.131 | 0.182 | 0.151 | 0.147 | 0.131 | 0.142 | 0.118 | 2.7 | 2.3 |
| last4 | 0.055 | 0.091 | 0.0274 | 0.0282 | 0.109 | 0.084 | 0.055 | 0.088 | 0.069 | 0.082 | 0.095 | 0.069 | 12.8 | 14.0 |
| last8 | 0.052 | 0.123 | 0.0241 | 0.0241 | 0.123 | 0.128 | 0.053 | 0.112 | 0.061 | 0.105 | 0.093 | 0.099 | 8.2 | 8.9 |
| last17 | 0.062 | 0.138 | 0.0219 | 0.0222 | 0.161 | 0.145 | 0.064 | 0.122 | 0.070 | 0.119 | 0.122 | 0.121 | 5.4 | 5.5 |
| season_to_date | 0.046 | 0.074 | 0.0280 | 0.0277 | 0.103 | 0.105 | 0.049 | 0.074 | 0.060 | 0.065 | 0.085 | 0.088 | 7.4 | 7.4 |
| last_season | 0.131 | 0.080 | 0.0218 | 0.0231 | 0.112 | 0.091 | 0.132 | 0.077 | 0.114 | 0.058 | 0.094 | 0.068 | 0.5 | 0.4 |
| def_plain_page | 0.160 | 0.173 | 0.0193 | 0.0194 | 0.164 | 0.165 | 0.181 | 0.184 | 0.130 | 0.153 | 0.133 | 0.141 | 5.9 | 6.0 |
| d0.97_k60 | 0.168 | 0.170 | 0.0199 | 0.0202 | 0.176 | 0.169 | 0.180 | 0.164 | 0.138 | 0.153 | 0.141 | 0.147 | 4.3 | 3.8 |
| d0.97_k120 | 0.174 | 0.173 | 0.0196 | 0.0199 | 0.178 | 0.171 | 0.191 | 0.173 | 0.144 | 0.157 | 0.145 | 0.149 | 4.2 | 3.6 |
| d0.97_k240 | 0.179 | 0.175 | 0.0192 | 0.0195 | 0.181 | 0.172 | 0.202 | 0.181 | 0.149 | 0.158 | 0.148 | 0.150 | 3.8 | 3.4 |
| d0.97_k480 | 0.180 | 0.172 | 0.0190 | 0.0192 | 0.181 | 0.172 | 0.208 | 0.185 | 0.152 | 0.156 | 0.150 | 0.151 | 3.5 | 3.1 |
| d0.97_k960 | 0.177 | 0.166 | 0.0190 | 0.0191 | 0.179 | 0.171 | 0.208 | 0.184 | 0.152 | 0.151 | 0.150 | 0.150 | 3.2 | 2.9 |
| d0.985_k60 | 0.168 | 0.164 | 0.0199 | 0.0203 | 0.174 | 0.160 | 0.181 | 0.158 | 0.140 | 0.148 | 0.141 | 0.139 | 3.8 | 3.2 |
| d0.985_k120 | 0.175 | 0.167 | 0.0196 | 0.0200 | 0.177 | 0.162 | 0.193 | 0.167 | 0.145 | 0.152 | 0.144 | 0.140 | 3.6 | 3.0 |
| d0.985_k240 | 0.180 | 0.168 | 0.0192 | 0.0196 | 0.179 | 0.163 | 0.203 | 0.174 | 0.151 | 0.153 | 0.148 | 0.142 | 3.3 | 2.7 |
| d0.985_k480 | 0.181 | 0.165 | 0.0190 | 0.0194 | 0.181 | 0.164 | 0.210 | 0.177 | 0.155 | 0.151 | 0.150 | 0.143 | 2.9 | 2.5 |
| d0.985_k960 | 0.177 | 0.158 | 0.0189 | 0.0192 | 0.178 | 0.163 | 0.210 | 0.176 | 0.155 | 0.145 | 0.149 | 0.144 | 2.7 | 2.2 |
| d1_k60 | 0.167 | 0.155 | 0.0200 | 0.0204 | 0.172 | 0.148 | 0.180 | 0.149 | 0.140 | 0.140 | 0.141 | 0.127 | 3.4 | 2.8 |
| d1_k120 | 0.174 | 0.158 | 0.0196 | 0.0201 | 0.174 | 0.147 | 0.192 | 0.158 | 0.146 | 0.143 | 0.144 | 0.126 | 3.2 | 2.5 |
| d1_k240 | 0.179 | 0.158 | 0.0193 | 0.0198 | 0.177 | 0.148 | 0.203 | 0.164 | 0.152 | 0.144 | 0.147 | 0.128 | 2.8 | 2.3 |
| d1_k480 | 0.180 | 0.154 | 0.0190 | 0.0196 | 0.178 | 0.146 | 0.210 | 0.166 | 0.156 | 0.141 | 0.150 | 0.127 | 2.4 | 1.9 |
| d1_k960 | 0.176 | 0.146 | 0.0189 | 0.0194 | 0.177 | 0.145 | 0.210 | 0.163 | 0.156 | 0.134 | 0.150 | 0.126 | 2.2 | 1.6 |

**Verdict (S).** The live value's correlation with the next four games is 0.139 (2019-22) and 0.129 (2023-25); rank correlation among regulars 0.147 and 0.131. It does not beat every simple average on both windows: last17 (beaten on 1/2 windows by correlation, 0/2 by rank correlation). The strongest simple alternative is last_season (corr 0.131 / 0.080).
Against the plain decayed EPA per snap at the page's recency (def_plain_page: corr 0.160 / 0.173, spearman 0.164 / 0.165) the group recipe is not better on both windows. Best plain grid cell on 2019-22: d0.985_k480 (0.181 / 0.165).
Churn: the top 40 by the live value move 2.7 places a week (2019-22) and 2.3 (2023-25); by last4 12.8 / 14.0, by last17 5.4 / 5.5.

## IDL

Player-weeks: 4634 (2019-22), 3606 (2023-25).

| predictor | corr 19-22 | corr 23-25 | mae 19-22 | mae 23-25 | spearman 19-22 | spearman 23-25 | corr_total 19-22 | corr_total 23-25 | corr_own 19-22 | corr_own 23-25 | spearman_own 19-22 | spearman_own 23-25 | churn 19-22 | churn 23-25 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| value | 0.336 | 0.221 | 0.0264 | 0.0249 | 0.327 | 0.243 | 0.464 | 0.369 | 0.331 | 0.267 | 0.314 | 0.258 | 1.4 | 1.1 |
| last4 | 0.205 | 0.101 | 0.0226 | 0.0229 | 0.232 | 0.161 | 0.260 | 0.141 | 0.216 | 0.133 | 0.231 | 0.178 | 13.1 | 13.6 |
| last8 | 0.227 | 0.145 | 0.0203 | 0.0199 | 0.266 | 0.194 | 0.285 | 0.202 | 0.244 | 0.180 | 0.266 | 0.211 | 7.6 | 8.4 |
| last17 | 0.284 | 0.182 | 0.0189 | 0.0182 | 0.315 | 0.234 | 0.358 | 0.260 | 0.289 | 0.228 | 0.306 | 0.250 | 4.5 | 5.5 |
| season_to_date | 0.201 | 0.102 | 0.0218 | 0.0220 | 0.244 | 0.186 | 0.266 | 0.148 | 0.217 | 0.134 | 0.249 | 0.196 | 6.5 | 6.7 |
| last_season | 0.248 | 0.187 | 0.0198 | 0.0180 | 0.283 | 0.241 | 0.299 | 0.235 | 0.247 | 0.220 | 0.272 | 0.255 | 0.2 | 0.3 |
| def_plain_page | 0.327 | 0.219 | 0.0168 | 0.0161 | 0.339 | 0.256 | 0.437 | 0.339 | 0.338 | 0.263 | 0.331 | 0.274 | 4.1 | 4.9 |
| d0.97_k60 | 0.334 | 0.233 | 0.0176 | 0.0166 | 0.331 | 0.271 | 0.434 | 0.346 | 0.337 | 0.281 | 0.323 | 0.290 | 2.7 | 3.0 |
| d0.97_k120 | 0.338 | 0.239 | 0.0173 | 0.0163 | 0.332 | 0.271 | 0.443 | 0.363 | 0.341 | 0.288 | 0.324 | 0.291 | 2.5 | 2.8 |
| d0.97_k240 | 0.342 | 0.245 | 0.0170 | 0.0160 | 0.335 | 0.271 | 0.454 | 0.379 | 0.345 | 0.293 | 0.327 | 0.290 | 2.3 | 2.4 |
| d0.97_k480 | 0.344 | 0.249 | 0.0167 | 0.0159 | 0.338 | 0.270 | 0.464 | 0.392 | 0.347 | 0.296 | 0.329 | 0.289 | 2.1 | 2.2 |
| d0.97_k960 | 0.344 | 0.251 | 0.0168 | 0.0159 | 0.339 | 0.268 | 0.471 | 0.401 | 0.347 | 0.298 | 0.330 | 0.286 | 2.0 | 2.0 |
| d0.985_k60 | 0.335 | 0.236 | 0.0177 | 0.0166 | 0.324 | 0.272 | 0.437 | 0.351 | 0.336 | 0.283 | 0.316 | 0.291 | 2.2 | 2.4 |
| d0.985_k120 | 0.339 | 0.242 | 0.0174 | 0.0164 | 0.325 | 0.273 | 0.445 | 0.367 | 0.340 | 0.289 | 0.318 | 0.292 | 2.0 | 2.2 |
| d0.985_k240 | 0.342 | 0.246 | 0.0171 | 0.0162 | 0.328 | 0.271 | 0.455 | 0.381 | 0.343 | 0.294 | 0.320 | 0.291 | 1.8 | 1.8 |
| d0.985_k480 | 0.343 | 0.248 | 0.0168 | 0.0160 | 0.330 | 0.268 | 0.463 | 0.391 | 0.344 | 0.296 | 0.321 | 0.286 | 1.7 | 1.6 |
| d0.985_k960 | 0.342 | 0.248 | 0.0168 | 0.0159 | 0.332 | 0.265 | 0.468 | 0.396 | 0.343 | 0.295 | 0.323 | 0.283 | 1.5 | 1.3 |
| d1_k60 | 0.333 | 0.233 | 0.0178 | 0.0167 | 0.317 | 0.264 | 0.437 | 0.348 | 0.332 | 0.279 | 0.310 | 0.283 | 1.9 | 2.0 |
| d1_k120 | 0.336 | 0.238 | 0.0176 | 0.0165 | 0.319 | 0.264 | 0.444 | 0.362 | 0.336 | 0.285 | 0.312 | 0.283 | 1.6 | 1.7 |
| d1_k240 | 0.339 | 0.242 | 0.0173 | 0.0163 | 0.321 | 0.261 | 0.452 | 0.373 | 0.338 | 0.288 | 0.314 | 0.280 | 1.5 | 1.4 |
| d1_k480 | 0.339 | 0.242 | 0.0170 | 0.0162 | 0.321 | 0.258 | 0.459 | 0.380 | 0.339 | 0.288 | 0.313 | 0.277 | 1.4 | 1.1 |
| d1_k960 | 0.336 | 0.239 | 0.0169 | 0.0160 | 0.321 | 0.255 | 0.461 | 0.381 | 0.336 | 0.285 | 0.312 | 0.272 | 1.3 | 0.9 |

**Verdict (IDL).** The live value's correlation with the next four games is 0.336 (2019-22) and 0.221 (2023-25); rank correlation among regulars 0.327 and 0.243. It beats every trailing average, the season to date and last season on both windows, on both correlation and rank correlation. The strongest simple alternative is last17 (corr 0.284 / 0.182).
Against the plain decayed EPA per snap at the page's recency (def_plain_page: corr 0.327 / 0.219, spearman 0.339 / 0.256) the group recipe is better on both windows. Best plain grid cell on 2019-22: d0.97_k480 (0.344 / 0.249).
Churn: the top 40 by the live value move 1.4 places a week (2019-22) and 1.1 (2023-25); by last4 13.1 / 13.6, by last17 4.5 / 5.5.

## EDGE

Player-weeks: 6297 (2019-22), 4885 (2023-25).

| predictor | corr 19-22 | corr 23-25 | mae 19-22 | mae 23-25 | spearman 19-22 | spearman 23-25 | corr_total 19-22 | corr_total 23-25 | corr_own 19-22 | corr_own 23-25 | spearman_own 19-22 | spearman_own 23-25 | churn 19-22 | churn 23-25 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| value | 0.300 | 0.296 | 0.0248 | 0.0241 | 0.298 | 0.298 | 0.402 | 0.376 | 0.300 | 0.296 | 0.298 | 0.298 | 2.4 | 2.1 |
| last4 | 0.155 | 0.151 | 0.0309 | 0.0308 | 0.186 | 0.194 | 0.186 | 0.178 | 0.155 | 0.151 | 0.186 | 0.194 | 16.8 | 16.2 |
| last8 | 0.198 | 0.238 | 0.0271 | 0.0264 | 0.218 | 0.264 | 0.238 | 0.264 | 0.198 | 0.238 | 0.218 | 0.264 | 9.9 | 9.0 |
| last17 | 0.229 | 0.275 | 0.0249 | 0.0245 | 0.245 | 0.275 | 0.275 | 0.307 | 0.229 | 0.275 | 0.245 | 0.275 | 6.4 | 5.8 |
| season_to_date | 0.170 | 0.137 | 0.0299 | 0.0303 | 0.201 | 0.211 | 0.205 | 0.171 | 0.170 | 0.137 | 0.201 | 0.211 | 7.9 | 7.2 |
| last_season | 0.240 | 0.288 | 0.0248 | 0.0242 | 0.237 | 0.292 | 0.287 | 0.308 | 0.240 | 0.288 | 0.237 | 0.292 | 0.3 | 0.2 |
| def_plain_page | 0.285 | 0.282 | 0.0221 | 0.0224 | 0.280 | 0.296 | 0.367 | 0.352 | 0.285 | 0.282 | 0.280 | 0.296 | 5.2 | 4.9 |
| d0.97_k60 | 0.292 | 0.310 | 0.0229 | 0.0228 | 0.286 | 0.299 | 0.356 | 0.352 | 0.292 | 0.310 | 0.286 | 0.299 | 4.0 | 3.2 |
| d0.97_k120 | 0.300 | 0.312 | 0.0225 | 0.0225 | 0.291 | 0.301 | 0.370 | 0.360 | 0.300 | 0.312 | 0.291 | 0.301 | 3.6 | 2.8 |
| d0.97_k240 | 0.306 | 0.313 | 0.0221 | 0.0222 | 0.296 | 0.303 | 0.384 | 0.369 | 0.306 | 0.313 | 0.296 | 0.303 | 3.1 | 2.8 |
| d0.97_k480 | 0.309 | 0.312 | 0.0219 | 0.0220 | 0.298 | 0.305 | 0.395 | 0.378 | 0.309 | 0.312 | 0.298 | 0.305 | 2.8 | 2.5 |
| d0.97_k960 | 0.310 | 0.309 | 0.0220 | 0.0221 | 0.299 | 0.303 | 0.402 | 0.385 | 0.310 | 0.309 | 0.299 | 0.303 | 2.6 | 2.3 |
| d0.985_k60 | 0.294 | 0.316 | 0.0229 | 0.0227 | 0.289 | 0.297 | 0.358 | 0.356 | 0.294 | 0.316 | 0.289 | 0.297 | 3.6 | 2.6 |
| d0.985_k120 | 0.302 | 0.319 | 0.0225 | 0.0225 | 0.294 | 0.300 | 0.373 | 0.363 | 0.302 | 0.319 | 0.294 | 0.300 | 3.0 | 2.2 |
| d0.985_k240 | 0.309 | 0.319 | 0.0222 | 0.0222 | 0.298 | 0.302 | 0.386 | 0.371 | 0.309 | 0.319 | 0.298 | 0.302 | 2.7 | 2.1 |
| d0.985_k480 | 0.312 | 0.318 | 0.0219 | 0.0220 | 0.300 | 0.304 | 0.396 | 0.378 | 0.312 | 0.318 | 0.300 | 0.304 | 2.3 | 1.9 |
| d0.985_k960 | 0.311 | 0.314 | 0.0219 | 0.0220 | 0.300 | 0.303 | 0.401 | 0.383 | 0.311 | 0.314 | 0.300 | 0.303 | 2.0 | 1.6 |
| d1_k60 | 0.295 | 0.320 | 0.0229 | 0.0227 | 0.288 | 0.296 | 0.359 | 0.356 | 0.295 | 0.320 | 0.288 | 0.296 | 3.1 | 2.1 |
| d1_k120 | 0.303 | 0.323 | 0.0226 | 0.0225 | 0.292 | 0.299 | 0.373 | 0.363 | 0.303 | 0.323 | 0.292 | 0.299 | 2.5 | 1.7 |
| d1_k240 | 0.309 | 0.323 | 0.0223 | 0.0223 | 0.297 | 0.302 | 0.385 | 0.370 | 0.309 | 0.323 | 0.297 | 0.302 | 2.2 | 1.5 |
| d1_k480 | 0.312 | 0.321 | 0.0220 | 0.0221 | 0.298 | 0.304 | 0.394 | 0.375 | 0.312 | 0.321 | 0.298 | 0.304 | 1.9 | 1.3 |
| d1_k960 | 0.310 | 0.316 | 0.0219 | 0.0220 | 0.298 | 0.300 | 0.398 | 0.377 | 0.310 | 0.316 | 0.298 | 0.300 | 1.7 | 1.0 |

**Verdict (EDGE).** The live value's correlation with the next four games is 0.300 (2019-22) and 0.296 (2023-25); rank correlation among regulars 0.298 and 0.298. It beats every trailing average, the season to date and last season on both windows, on both correlation and rank correlation. The strongest simple alternative is last_season (corr 0.240 / 0.288).
Against the plain decayed EPA per snap at the page's recency (def_plain_page: corr 0.285 / 0.282, spearman 0.280 / 0.296) the group recipe is better on both windows. Best plain grid cell on 2019-22: d1_k480 (0.312 / 0.321).
Churn: the top 40 by the live value move 2.4 places a week (2019-22) and 2.1 (2023-25); by last4 16.8 / 16.2, by last17 6.4 / 5.8.

## LB

Player-weeks: 4213 (2019-22), 3283 (2023-25).

| predictor | corr 19-22 | corr 23-25 | mae 19-22 | mae 23-25 | spearman 19-22 | spearman 23-25 | corr_total 19-22 | corr_total 23-25 | corr_own 19-22 | corr_own 23-25 | spearman_own 19-22 | spearman_own 23-25 | churn 19-22 | churn 23-25 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| value | 0.084 | 0.091 | 0.0503 | 0.0568 | 0.104 | 0.137 | 0.244 | 0.227 | 0.128 | 0.092 | 0.146 | 0.133 | 2.4 | 2.2 |
| last4 | 0.146 | 0.073 | 0.0273 | 0.0262 | 0.118 | 0.092 | 0.152 | 0.088 | 0.128 | 0.037 | 0.109 | 0.048 | 12.2 | 12.5 |
| last8 | 0.141 | 0.077 | 0.0241 | 0.0230 | 0.133 | 0.090 | 0.161 | 0.091 | 0.120 | 0.035 | 0.115 | 0.034 | 7.7 | 7.6 |
| last17 | 0.140 | 0.119 | 0.0224 | 0.0210 | 0.147 | 0.128 | 0.163 | 0.148 | 0.123 | 0.088 | 0.140 | 0.079 | 5.3 | 5.0 |
| season_to_date | 0.141 | 0.028 | 0.0274 | 0.0260 | 0.122 | 0.061 | 0.157 | 0.048 | 0.111 | 0.003 | 0.108 | 0.002 | 6.2 | 6.9 |
| last_season | 0.072 | 0.049 | 0.0242 | 0.0228 | 0.121 | 0.078 | 0.062 | 0.099 | 0.087 | 0.041 | 0.113 | 0.057 | 0.5 | 0.6 |
| def_plain_page | 0.170 | 0.123 | 0.0191 | 0.0187 | 0.168 | 0.138 | 0.236 | 0.184 | 0.153 | 0.077 | 0.153 | 0.070 | 5.5 | 5.8 |
| d0.97_k60 | 0.163 | 0.137 | 0.0199 | 0.0194 | 0.180 | 0.144 | 0.211 | 0.183 | 0.147 | 0.119 | 0.173 | 0.104 | 3.8 | 3.5 |
| d0.97_k120 | 0.166 | 0.139 | 0.0194 | 0.0191 | 0.180 | 0.145 | 0.224 | 0.191 | 0.153 | 0.118 | 0.172 | 0.102 | 3.6 | 3.5 |
| d0.97_k240 | 0.170 | 0.139 | 0.0191 | 0.0188 | 0.177 | 0.149 | 0.240 | 0.198 | 0.161 | 0.114 | 0.170 | 0.101 | 3.5 | 3.3 |
| d0.97_k480 | 0.172 | 0.135 | 0.0188 | 0.0185 | 0.175 | 0.151 | 0.255 | 0.202 | 0.168 | 0.107 | 0.168 | 0.102 | 3.3 | 3.0 |
| d0.97_k960 | 0.171 | 0.128 | 0.0188 | 0.0183 | 0.173 | 0.151 | 0.265 | 0.204 | 0.172 | 0.098 | 0.164 | 0.101 | 3.2 | 2.9 |
| d0.985_k60 | 0.161 | 0.139 | 0.0199 | 0.0194 | 0.178 | 0.148 | 0.209 | 0.184 | 0.146 | 0.130 | 0.174 | 0.117 | 3.4 | 3.1 |
| d0.985_k120 | 0.164 | 0.141 | 0.0194 | 0.0191 | 0.180 | 0.149 | 0.223 | 0.192 | 0.152 | 0.129 | 0.175 | 0.113 | 3.2 | 2.9 |
| d0.985_k240 | 0.167 | 0.140 | 0.0191 | 0.0188 | 0.176 | 0.150 | 0.239 | 0.198 | 0.160 | 0.124 | 0.172 | 0.109 | 3.0 | 2.7 |
| d0.985_k480 | 0.170 | 0.136 | 0.0188 | 0.0186 | 0.174 | 0.150 | 0.254 | 0.201 | 0.168 | 0.116 | 0.169 | 0.107 | 2.8 | 2.4 |
| d0.985_k960 | 0.168 | 0.128 | 0.0188 | 0.0183 | 0.169 | 0.147 | 0.264 | 0.201 | 0.172 | 0.105 | 0.163 | 0.104 | 2.7 | 2.3 |
| d1_k60 | 0.157 | 0.142 | 0.0199 | 0.0194 | 0.171 | 0.151 | 0.205 | 0.184 | 0.143 | 0.139 | 0.170 | 0.127 | 3.0 | 2.6 |
| d1_k120 | 0.160 | 0.144 | 0.0195 | 0.0192 | 0.173 | 0.152 | 0.219 | 0.192 | 0.149 | 0.139 | 0.172 | 0.123 | 2.8 | 2.3 |
| d1_k240 | 0.163 | 0.143 | 0.0192 | 0.0189 | 0.171 | 0.153 | 0.234 | 0.197 | 0.157 | 0.134 | 0.170 | 0.119 | 2.6 | 2.0 |
| d1_k480 | 0.165 | 0.138 | 0.0189 | 0.0187 | 0.166 | 0.151 | 0.249 | 0.199 | 0.165 | 0.126 | 0.166 | 0.115 | 2.4 | 1.8 |
| d1_k960 | 0.164 | 0.129 | 0.0188 | 0.0185 | 0.162 | 0.148 | 0.260 | 0.197 | 0.170 | 0.114 | 0.159 | 0.109 | 2.3 | 1.6 |

**Verdict (LB).** The live value's correlation with the next four games is 0.084 (2019-22) and 0.091 (2023-25); rank correlation among regulars 0.104 and 0.137. It does not beat every simple average on both windows: last4 (beaten on 1/2 windows by correlation, 1/2 by rank correlation), last8 (beaten on 1/2 windows by correlation, 1/2 by rank correlation), last17 (beaten on 0/2 windows by correlation, 1/2 by rank correlation), season_to_date (beaten on 1/2 windows by correlation, 1/2 by rank correlation), last_season (beaten on 2/2 windows by correlation, 1/2 by rank correlation). The strongest simple alternative is last17 (corr 0.140 / 0.119).
Against the plain decayed EPA per snap at the page's recency (def_plain_page: corr 0.170 / 0.123, spearman 0.168 / 0.138) the group recipe is not better on both windows. Best plain grid cell on 2019-22: d0.97_k480 (0.172 / 0.135).
Churn: the top 40 by the live value move 2.4 places a week (2019-22) and 2.2 (2023-25); by last4 12.2 / 12.5, by last17 5.3 / 5.0.
