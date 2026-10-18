# Drift monitor, 2026

**0 alerts, 0 to watch.** Long run = 2015 to 2024; recent = 2025 and 2026 so far. ALERT at |z| >= 2.5 or a CUSUM trip (h 5); WATCH at |z| >= 2.0.


| group   | measure                                                   |   long_run |   long_run_n |   recent |   recent_n |   this_season |   this_season_n |     z |   cusum | level   |
|:--------|:----------------------------------------------------------|-----------:|-------------:|---------:|-----------:|--------------:|----------------:|------:|--------:|:--------|
| home    | Home margin (points)                                      |     1.7203 |         2581 |   1.7867 |        347 |        0.5    |              82 |  0.08 |    2.67 | ok      |
| home    | Home cover margin vs the line                             |    -0.1019 |         2581 |   0.183  |        347 |       -1.189  |              82 |  0.39 |    3.1  | ok      |
| side    | Home favorite cover margin (road dog: the same, reversed) |    -0.1792 |         1624 |   0.2085 |        211 |       -1.9528 |              53 |  0.42 |    3.17 | ok      |
| side    | Road favorite cover margin (home dog: the same, reversed) |    -0.0362 |          995 |   0.223  |        148 |        1.2059 |              34 |  0.22 |    2.15 | ok      |
| total   | Final total minus the closing total                       |     0.3223 |         2623 |   1.2883 |        359 |        1.7184 |              87 |  1.3  |    2.68 | ok      |
| total   | Over rate                                                 |     0.4852 |         2597 |   0.5209 |        359 |        0.5172 |              87 |  1.27 |    2.99 | ok      |
| key     | Margin exactly 3                                          |     0.146  |         2623 |   0.156  |        359 |        0.1724 |              87 |  0.5  |    2.48 | ok      |
| key     | Margin exactly 7                                          |     0.0858 |         2623 |   0.1003 |        359 |        0.1149 |              87 |  0.92 |    2.56 | ok      |
| model   | Model miss minus the line's miss                          |     0.13   |         2623 |   0.1676 |        359 |        0.1297 |              87 |  0.28 |    1.4  | ok      |
| model   | Model home lean (model margin minus real)                 |     0.3946 |         2581 |   0.2456 |        347 |        1.4193 |              82 | -0.2  |    3.01 | ok      |
| model   | 4+ flag win rate                                          |     0.5938 |          288 |   0.68   |         25 |        0.6    |               5 |  0.84 |    2.33 | ok      |
