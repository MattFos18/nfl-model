# Drift monitor, 2026

**0 alerts, 0 to watch.** Long run = 2015 to 2024; recent = 2025 and 2026 so far. ALERT at |z| >= 2.5 or a CUSUM trip (h 5); WATCH at |z| >= 2.0.


| group   | measure                                                   |   long_run |   long_run_n |   recent |   recent_n |   this_season |   this_season_n |     z |   cusum | level   |
|:--------|:----------------------------------------------------------|-----------:|-------------:|---------:|-----------:|--------------:|----------------:|------:|--------:|:--------|
| home    | Home margin (points)                                      |     1.7203 |         2581 |   2.0737 |        312 |        1.4468 |              47 |  0.42 |    2.67 | ok      |
| home    | Home cover margin vs the line                             |    -0.1019 |         2581 |   0.4151 |        312 |       -0.6702 |              47 |  0.68 |    3.1  | ok      |
| side    | Home favorite cover margin (road dog: the same, reversed) |    -0.1792 |         1624 |   0.6263 |        190 |       -0.8906 |              32 |  0.83 |    3.17 | ok      |
| side    | Road favorite cover margin (home dog: the same, reversed) |    -0.0362 |          995 |   0.1412 |        131 |        1.5588 |              17 |  0.15 |    2.15 | ok      |
| total   | Final total minus the closing total                       |     0.3223 |         2623 |   1.1324 |        321 |        1.0306 |              49 |  1.04 |    2.68 | ok      |
| total   | Over rate                                                 |     0.4852 |         2597 |   0.5171 |        321 |        0.4898 |              49 |  1.08 |    2.99 | ok      |
| key     | Margin exactly 3                                          |     0.146  |         2623 |   0.1495 |        321 |        0.1429 |              49 |  0.17 |    2.48 | ok      |
| key     | Margin exactly 7                                          |     0.0858 |         2623 |   0.0966 |        321 |        0.102  |              49 |  0.65 |    2.56 | ok      |
| model   | Model miss minus the line's miss                          |     0.13   |         2623 |   0.1662 |        321 |        0.0911 |              49 |  0.25 |    1.4  | ok      |
| model   | Model home lean (model margin minus real)                 |     0.3946 |         2581 |   0.03   |        312 |        0.8617 |              47 | -0.47 |    3.01 | ok      |
| model   | 4+ flag win rate                                          |     0.5938 |          288 |   0.6818 |         22 |        0.5    |               2 |  0.81 |    2.33 | ok      |
