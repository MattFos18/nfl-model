# Drift monitor, 2026

**0 alerts, 0 to watch.** Long run = 2015 to 2024; recent = 2025 and 2026 so far. ALERT at |z| >= 2.5 or a CUSUM trip (h 5); WATCH at |z| >= 2.0.


| group   | measure                                                   |   long_run |   long_run_n |   recent |   recent_n |   this_season |   this_season_n |     z |   cusum | level   |
|:--------|:----------------------------------------------------------|-----------:|-------------:|---------:|-----------:|--------------:|----------------:|------:|--------:|:--------|
| home    | Home margin (points)                                      |     1.7203 |         2581 |   2.0707 |        311 |        1.413  |              46 |  0.41 |    2.67 | ok      |
| home    | Home cover margin vs the line                             |    -0.1019 |         2581 |   0.3987 |        311 |       -0.8043 |              46 |  0.65 |    3.1  | ok      |
| side    | Home favorite cover margin (road dog: the same, reversed) |    -0.1792 |         1624 |   0.6263 |        190 |       -0.8906 |              32 |  0.83 |    3.17 | ok      |
| side    | Road favorite cover margin (home dog: the same, reversed) |    -0.0362 |          995 |   0.1846 |        130 |        2      |              16 |  0.18 |    2.15 | ok      |
| total   | Final total minus the closing total                       |     0.3223 |         2623 |   1.0969 |        320 |        0.7917 |              48 |  0.99 |    2.68 | ok      |
| total   | Over rate                                                 |     0.4852 |         2597 |   0.5156 |        320 |        0.4792 |              48 |  1.03 |    2.99 | ok      |
| key     | Margin exactly 3                                          |     0.146  |         2623 |   0.1469 |        320 |        0.125  |              48 |  0.04 |    2.48 | ok      |
| key     | Margin exactly 7                                          |     0.0858 |         2623 |   0.0969 |        320 |        0.1042 |              48 |  0.67 |    2.56 | ok      |
| model   | Model miss minus the line's miss                          |     0.1356 |         2623 |   0.2255 |        320 |        0.2137 |              48 |  0.63 |    2.08 | ok      |
| model   | Model home lean (model margin minus real)                 |     0.405  |         2581 |   0.0315 |        311 |        1.0377 |              46 | -0.48 |    3.07 | ok      |
| model   | 4+ flag win rate                                          |     0.5973 |          293 |   0.56   |         25 |        0.3333 |               3 | -0.36 |    2.82 | ok      |
