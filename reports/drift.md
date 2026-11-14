# Drift monitor, 2026

**0 alerts, 0 to watch.** Long run = 2015 to 2024; recent = 2025 and 2026 so far. ALERT at |z| >= 2.5 or a CUSUM trip (h 5); WATCH at |z| >= 2.0.


| group   | measure                                                   |   long_run |   long_run_n |   recent |   recent_n |   this_season |   this_season_n |     z |   cusum | level   |
|:--------|:----------------------------------------------------------|-----------:|-------------:|---------:|-----------:|--------------:|----------------:|------:|--------:|:--------|
| home    | Home margin (points)                                      |     1.7203 |         2581 |   1.6203 |        395 |        0.4692 |             130 | -0.13 |    2.67 | ok      |
| home    | Home cover margin vs the line                             |    -0.1019 |         2581 |  -0.0215 |        395 |       -1.3038 |             130 |  0.12 |    3.1  | ok      |
| side    | Home favorite cover margin (road dog: the same, reversed) |    -0.1792 |         1624 |   0.2469 |        241 |       -1.0602 |              83 |  0.49 |    3.17 | ok      |
| side    | Road favorite cover margin (home dog: the same, reversed) |    -0.0362 |          995 |   0.8185 |        168 |        2.6944 |              54 |  0.78 |    2.15 | ok      |
| total   | Final total minus the closing total                       |     0.3223 |         2623 |   1.0281 |        409 |        0.7847 |             137 |  1.01 |    2.68 | ok      |
| total   | Over rate                                                 |     0.4852 |         2597 |   0.5208 |        409 |        0.5182 |             137 |  1.34 |    2.99 | ok      |
| key     | Margin exactly 3                                          |     0.146  |         2623 |   0.154  |        409 |        0.1606 |             137 |  0.43 |    2.48 | ok      |
| key     | Margin exactly 7                                          |     0.0858 |         2623 |   0.0954 |        409 |        0.0949 |             137 |  0.64 |    2.56 | ok      |
| model   | Model miss minus the line's miss                          |     0.13   |         2623 |   0.1914 |        409 |        0.2146 |             137 |  0.48 |    1.4  | ok      |
| model   | Model home lean (model margin minus real)                 |     0.3946 |         2581 |   0.4279 |        395 |        1.5397 |             130 |  0.05 |    3.01 | ok      |
| model   | 4+ flag win rate                                          |     0.5938 |          288 |   0.6538 |         26 |        0.5    |               6 |  0.6  |    2.33 | ok      |
