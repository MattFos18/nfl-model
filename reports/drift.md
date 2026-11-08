# Drift monitor, 2026

**0 alerts, 0 to watch.** Long run = 2015 to 2024; recent = 2025 and 2026 so far. ALERT at |z| >= 2.5 or a CUSUM trip (h 5); WATCH at |z| >= 2.0.


| group   | measure                                                   |   long_run |   long_run_n |   recent |   recent_n |   this_season |   this_season_n |     z |   cusum | level   |
|:--------|:----------------------------------------------------------|-----------:|-------------:|---------:|-----------:|--------------:|----------------:|------:|--------:|:--------|
| home    | Home margin (points)                                      |     1.7203 |         2581 |   1.7638 |        381 |        0.8017 |             116 |  0.06 |    2.67 | ok      |
| home    | Home cover margin vs the line                             |    -0.1019 |         2581 |   0.0932 |        381 |       -1.0819 |             116 |  0.28 |    3.1  | ok      |
| side    | Home favorite cover margin (road dog: the same, reversed) |    -0.1792 |         1624 |   0.2585 |        234 |       -1.1447 |              76 |  0.5  |    3.17 | ok      |
| side    | Road favorite cover margin (home dog: the same, reversed) |    -0.0362 |          995 |   0.587  |        161 |        2.1809 |              47 |  0.56 |    2.15 | ok      |
| total   | Final total minus the closing total                       |     0.3223 |         2623 |   1.1025 |        395 |        0.9959 |             123 |  1.1  |    2.68 | ok      |
| total   | Over rate                                                 |     0.4852 |         2597 |   0.5215 |        395 |        0.5203 |             123 |  1.35 |    2.99 | ok      |
| key     | Margin exactly 3                                          |     0.146  |         2623 |   0.1544 |        395 |        0.1626 |             123 |  0.44 |    2.48 | ok      |
| key     | Margin exactly 7                                          |     0.0858 |         2623 |   0.0962 |        395 |        0.0976 |             123 |  0.69 |    2.56 | ok      |
| model   | Model miss minus the line's miss                          |     0.13   |         2623 |   0.173  |        395 |        0.1581 |             123 |  0.33 |    1.4  | ok      |
| model   | Model home lean (model margin minus real)                 |     0.3946 |         2581 |   0.3106 |        381 |        1.2888 |             116 | -0.12 |    3.01 | ok      |
| model   | 4+ flag win rate                                          |     0.5938 |          288 |   0.68   |         25 |        0.6    |               5 |  0.84 |    2.33 | ok      |
