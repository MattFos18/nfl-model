# Drift monitor, 2026

**0 alerts, 0 to watch.** Long run = 2015 to 2024; recent = 2025 and 2026 so far. ALERT at |z| >= 2.5 or a CUSUM trip (h 5); WATCH at |z| >= 2.0.


| group   | measure                                                   |   long_run |   long_run_n |   recent |   recent_n |   this_season |   this_season_n |     z |   cusum | level   |
|:--------|:----------------------------------------------------------|-----------:|-------------:|---------:|-----------:|--------------:|----------------:|------:|--------:|:--------|
| home    | Home margin (points)                                      |     1.7203 |         2581 |   1.6081 |        421 |        0.6282 |             156 | -0.15 |    2.91 | ok      |
| home    | Home cover margin vs the line                             |    -0.1019 |         2581 |  -0.0285 |        421 |       -1.109  |             156 |  0.11 |    3.1  | ok      |
| side    | Home favorite cover margin (road dog: the same, reversed) |    -0.1792 |         1624 |   0.4903 |        258 |       -0.21   |             100 |  0.79 |    3.17 | ok      |
| side    | Road favorite cover margin (home dog: the same, reversed) |    -0.0362 |          995 |   0.9218 |        179 |        2.6615 |              65 |  0.9  |    2.44 | ok      |
| total   | Final total minus the closing total                       |     0.3223 |         2623 |   1.1476 |        437 |        1.1424 |             165 |  1.21 |    2.68 | ok      |
| total   | Over rate                                                 |     0.4852 |         2597 |   0.524  |        437 |        0.5273 |             165 |  1.5  |    2.99 | ok      |
| key     | Margin exactly 3                                          |     0.146  |         2623 |   0.1556 |        437 |        0.1636 |             165 |  0.53 |    2.48 | ok      |
| key     | Margin exactly 7                                          |     0.0858 |         2623 |   0.0892 |        437 |        0.0788 |             165 |  0.24 |    2.56 | ok      |
| model   | Model miss minus the line's miss                          |     0.13   |         2623 |   0.2089 |        437 |        0.2571 |             165 |  0.63 |    1.4  | ok      |
| model   | Model home lean (model margin minus real)                 |     0.3946 |         2581 |   0.4093 |        421 |        1.3042 |             156 |  0.02 |    3.01 | ok      |
| model   | 4+ flag win rate                                          |     0.5938 |          288 |   0.6429 |         28 |        0.5    |               8 |  0.5  |    2.33 | ok      |
