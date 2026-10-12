# Drift monitor, 2026

**0 alerts, 0 to watch.** Long run = 2015 to 2024; recent = 2025 and 2026 so far. ALERT at |z| >= 2.5 or a CUSUM trip (h 5); WATCH at |z| >= 2.0.


| group   | measure                                                   |   long_run |   long_run_n |   recent |   recent_n |   this_season |   this_season_n |     z |   cusum | level   |
|:--------|:----------------------------------------------------------|-----------:|-------------:|---------:|-----------:|--------------:|----------------:|------:|--------:|:--------|
| home    | Home margin (points)                                      |     1.7203 |         2581 |   1.8938 |        339 |        0.8514 |              74 |  0.21 |    2.67 | ok      |
| home    | Home cover margin vs the line                             |    -0.1019 |         2581 |   0.2699 |        339 |       -0.9392 |              74 |  0.5  |    3.1  | ok      |
| side    | Home favorite cover margin (road dog: the same, reversed) |    -0.1792 |         1624 |   0.3333 |        207 |       -1.602  |              49 |  0.55 |    3.17 | ok      |
| side    | Road favorite cover margin (home dog: the same, reversed) |    -0.0362 |          995 |   0.1713 |        143 |        1.1207 |              29 |  0.18 |    2.15 | ok      |
| total   | Final total minus the closing total                       |     0.3223 |         2623 |   1.2286 |        350 |        1.5    |              78 |  1.21 |    2.68 | ok      |
| total   | Over rate                                                 |     0.4852 |         2597 |   0.5171 |        350 |        0.5    |              78 |  1.12 |    2.99 | ok      |
| key     | Margin exactly 3                                          |     0.146  |         2623 |   0.1486 |        350 |        0.141  |              78 |  0.13 |    2.48 | ok      |
| key     | Margin exactly 7                                          |     0.0858 |         2623 |   0.0971 |        350 |        0.1026 |              78 |  0.71 |    2.56 | ok      |
| model   | Model miss minus the line's miss                          |     0.13   |         2623 |   0.14   |        350 |        0.0017 |              78 |  0.07 |    1.4  | ok      |
| model   | Model home lean (model margin minus real)                 |     0.3946 |         2581 |   0.1294 |        339 |        1.0139 |              74 | -0.36 |    3.01 | ok      |
| model   | 4+ flag win rate                                          |     0.5938 |          288 |   0.68   |         25 |        0.6    |               5 |  0.84 |    2.33 | ok      |
