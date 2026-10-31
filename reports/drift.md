# Drift monitor, 2026

**0 alerts, 0 to watch.** Long run = 2015 to 2024; recent = 2025 and 2026 so far. ALERT at |z| >= 2.5 or a CUSUM trip (h 5); WATCH at |z| >= 2.0.


| group   | measure                                                   |   long_run |   long_run_n |   recent |   recent_n |   this_season |   this_season_n |     z |   cusum | level   |
|:--------|:----------------------------------------------------------|-----------:|-------------:|---------:|-----------:|--------------:|----------------:|------:|--------:|:--------|
| home    | Home margin (points)                                      |     1.7203 |         2581 |   1.5804 |        367 |        0.0098 |             102 | -0.18 |    2.67 | ok      |
| home    | Home cover margin vs the line                             |    -0.1019 |         2581 |  -0.03   |        367 |       -1.6863 |             102 |  0.1  |    3.1  | ok      |
| side    | Home favorite cover margin (road dog: the same, reversed) |    -0.1792 |         1624 |   0.0068 |        222 |       -2.2812 |              64 |  0.21 |    3.17 | ok      |
| side    | Road favorite cover margin (home dog: the same, reversed) |    -0.0362 |          995 |   0.4304 |        158 |        1.7273 |              44 |  0.42 |    2.15 | ok      |
| total   | Final total minus the closing total                       |     0.3223 |         2623 |   1.1    |        380 |        0.9722 |             108 |  1.07 |    2.68 | ok      |
| total   | Over rate                                                 |     0.4852 |         2597 |   0.5211 |        380 |        0.5185 |             108 |  1.31 |    2.99 | ok      |
| key     | Margin exactly 3                                          |     0.146  |         2623 |   0.1579 |        380 |        0.1759 |             108 |  0.61 |    2.48 | ok      |
| key     | Margin exactly 7                                          |     0.0858 |         2623 |   0.0974 |        380 |        0.1019 |             108 |  0.75 |    2.56 | ok      |
| model   | Model miss minus the line's miss                          |     0.13   |         2623 |   0.1684 |        380 |        0.1398 |             108 |  0.29 |    1.4  | ok      |
| model   | Model home lean (model margin minus real)                 |     0.3946 |         2581 |   0.4523 |        367 |        1.9328 |             102 |  0.08 |    3.01 | ok      |
| model   | 4+ flag win rate                                          |     0.5938 |          288 |   0.68   |         25 |        0.6    |               5 |  0.84 |    2.33 | ok      |
