# Drift monitor, 2026

**0 alerts, 0 to watch.** Long run = 2015 to 2024; recent = 2025 and 2026 so far. ALERT at |z| >= 2.5 or a CUSUM trip (h 5); WATCH at |z| >= 2.0.


| group   | measure                                                   |   long_run |   long_run_n |   recent |   recent_n |   this_season |   this_season_n |     z |   cusum | level   |
|:--------|:----------------------------------------------------------|-----------:|-------------:|---------:|-----------:|--------------:|----------------:|------:|--------:|:--------|
| home    | Home margin (points)                                      |     1.7203 |         2581 |   1.8249 |        354 |        0.7528 |              89 |  0.13 |    2.67 | ok      |
| home    | Home cover margin vs the line                             |    -0.1019 |         2581 |   0.1935 |        354 |       -1.0393 |              89 |  0.41 |    3.1  | ok      |
| side    | Home favorite cover margin (road dog: the same, reversed) |    -0.1792 |         1624 |   0.1837 |        215 |       -1.8947 |              57 |  0.4  |    3.17 | ok      |
| side    | Road favorite cover margin (home dog: the same, reversed) |    -0.0362 |          995 |   0.1556 |        151 |        0.8514 |              37 |  0.17 |    2.15 | ok      |
| total   | Final total minus the closing total                       |     0.3223 |         2623 |   1.153  |        366 |        1.1596 |              94 |  1.13 |    2.68 | ok      |
| total   | Over rate                                                 |     0.4852 |         2597 |   0.5191 |        366 |        0.5106 |              94 |  1.22 |    2.99 | ok      |
| key     | Margin exactly 3                                          |     0.146  |         2623 |   0.1557 |        366 |        0.1702 |              94 |  0.49 |    2.48 | ok      |
| key     | Margin exactly 7                                          |     0.0858 |         2623 |   0.1011 |        366 |        0.117  |              94 |  0.98 |    2.56 | ok      |
| model   | Model miss minus the line's miss                          |     0.13   |         2623 |   0.1722 |        366 |        0.1506 |              94 |  0.31 |    1.65 | ok      |
| model   | Model home lean (model margin minus real)                 |     0.3946 |         2581 |   0.2225 |        354 |        1.2348 |              89 | -0.24 |    3.01 | ok      |
| model   | 4+ flag win rate                                          |     0.5938 |          288 |   0.68   |         25 |        0.6    |               5 |  0.84 |    2.33 | ok      |
