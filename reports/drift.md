# Drift monitor, 2026

**0 alerts, 0 to watch.** Long run = 2015 to 2024; recent = 2025 and 2026 so far. ALERT at |z| >= 2.5 or a CUSUM trip (h 5); WATCH at |z| >= 2.0.


| group   | measure                                                   |   long_run |   long_run_n |   recent |   recent_n |   this_season |   this_season_n |     z |   cusum | level   |
|:--------|:----------------------------------------------------------|-----------:|-------------:|---------:|-----------:|--------------:|----------------:|------:|--------:|:--------|
| home    | Home margin (points)                                      |     1.7203 |         2581 |   1.5943 |        419 |        0.5779 |             154 | -0.17 |    2.91 | ok      |
| home    | Home cover margin vs the line                             |    -0.1019 |         2581 |  -0.0477 |        419 |       -1.1753 |             154 |  0.08 |    3.1  | ok      |
| side    | Home favorite cover margin (road dog: the same, reversed) |    -0.1792 |         1624 |   0.4514 |        257 |       -0.3182 |              99 |  0.75 |    3.17 | ok      |
| side    | Road favorite cover margin (home dog: the same, reversed) |    -0.0362 |          995 |   0.9129 |        178 |        2.6641 |              64 |  0.89 |    2.44 | ok      |
| total   | Final total minus the closing total                       |     0.3223 |         2623 |   1.123  |        435 |        1.0767 |             163 |  1.17 |    2.68 | ok      |
| total   | Over rate                                                 |     0.4852 |         2597 |   0.5241 |        435 |        0.5276 |             163 |  1.5  |    2.99 | ok      |
| key     | Margin exactly 3                                          |     0.146  |         2623 |   0.1563 |        435 |        0.1656 |             163 |  0.56 |    2.48 | ok      |
| key     | Margin exactly 7                                          |     0.0858 |         2623 |   0.0897 |        435 |        0.0798 |             163 |  0.27 |    2.56 | ok      |
| model   | Model miss minus the line's miss                          |     0.13   |         2623 |   0.201  |        435 |        0.2366 |             163 |  0.57 |    1.4  | ok      |
| model   | Model home lean (model margin minus real)                 |     0.3946 |         2581 |   0.4216 |        419 |        1.3493 |             154 |  0.04 |    3.01 | ok      |
| model   | 4+ flag win rate                                          |     0.5938 |          288 |   0.6429 |         28 |        0.5    |               8 |  0.5  |    2.33 | ok      |
