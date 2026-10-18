# Drift monitor, 2026

**0 alerts, 0 to watch.** Long run = 2015 to 2024; recent = 2025 and 2026 so far. ALERT at |z| >= 2.5 or a CUSUM trip (h 5); WATCH at |z| >= 2.0.


| group   | measure                                                   |   long_run |   long_run_n |   recent |   recent_n |   this_season |   this_season_n |     z |   cusum | level   |
|:--------|:----------------------------------------------------------|-----------:|-------------:|---------:|-----------:|--------------:|----------------:|------:|--------:|:--------|
| home    | Home margin (points)                                      |     1.7203 |         2581 |   1.7615 |        348 |        0.4096 |              83 |  0.05 |    2.67 | ok      |
| home    | Home cover margin vs the line                             |    -0.1019 |         2581 |   0.1695 |        348 |       -1.2289 |              83 |  0.37 |    3.1  | ok      |
| side    | Home favorite cover margin (road dog: the same, reversed) |    -0.1792 |         1624 |   0.2085 |        211 |       -1.9528 |              53 |  0.42 |    3.17 | ok      |
| side    | Road favorite cover margin (home dog: the same, reversed) |    -0.0362 |          995 |   0.2517 |        149 |        1.3    |              35 |  0.25 |    2.15 | ok      |
| total   | Final total minus the closing total                       |     0.3223 |         2623 |   1.3028 |        360 |        1.7727 |              88 |  1.32 |    2.68 | ok      |
| total   | Over rate                                                 |     0.4852 |         2597 |   0.5222 |        360 |        0.5227 |              88 |  1.32 |    2.99 | ok      |
| key     | Margin exactly 3                                          |     0.146  |         2623 |   0.1556 |        360 |        0.1705 |              88 |  0.48 |    2.48 | ok      |
| key     | Margin exactly 7                                          |     0.0858 |         2623 |   0.1028 |        360 |        0.125  |              88 |  1.08 |    2.56 | ok      |
| model   | Model miss minus the line's miss                          |     0.13   |         2623 |   0.1762 |        360 |        0.1656 |              88 |  0.34 |    1.57 | ok      |
| model   | Model home lean (model margin minus real)                 |     0.3946 |         2581 |   0.2673 |        348 |        1.496  |              83 | -0.17 |    3.01 | ok      |
| model   | 4+ flag win rate                                          |     0.5938 |          288 |   0.68   |         25 |        0.6    |               5 |  0.84 |    2.33 | ok      |
