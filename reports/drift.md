# Drift monitor, 2026

**0 alerts, 0 to watch.** Long run = 2015 to 2024; recent = 2025 and 2026 so far. ALERT at |z| >= 2.5 or a CUSUM trip (h 5); WATCH at |z| >= 2.0.


| group   | measure                                                   |   long_run |   long_run_n |   recent |   recent_n |   this_season |   this_season_n |     z |   cusum | level   |
|:--------|:----------------------------------------------------------|-----------:|-------------:|---------:|-----------:|--------------:|----------------:|------:|--------:|:--------|
| home    | Home margin (points)                                      |     1.7203 |         2581 |   2.0985 |        325 |        1.7167 |              60 |  0.45 |    2.67 | ok      |
| home    | Home cover margin vs the line                             |    -0.1019 |         2581 |   0.4154 |        325 |       -0.4333 |              60 |  0.69 |    3.1  | ok      |
| side    | Home favorite cover margin (road dog: the same, reversed) |    -0.1792 |         1624 |   0.4975 |        198 |       -1.225  |              40 |  0.71 |    3.17 | ok      |
| side    | Road favorite cover margin (home dog: the same, reversed) |    -0.0362 |          995 |   0.0365 |        137 |        0.5652 |              23 |  0.06 |    2.15 | ok      |
| total   | Final total minus the closing total                       |     0.3223 |         2623 |   1.106  |        335 |        0.9127 |              63 |  1.02 |    2.68 | ok      |
| total   | Over rate                                                 |     0.4852 |         2597 |   0.5164 |        335 |        0.4921 |              63 |  1.08 |    2.99 | ok      |
| key     | Margin exactly 3                                          |     0.146  |         2623 |   0.1522 |        335 |        0.1587 |              63 |  0.3  |    2.48 | ok      |
| key     | Margin exactly 7                                          |     0.0858 |         2623 |   0.0955 |        335 |        0.0952 |              63 |  0.6  |    2.56 | ok      |
| model   | Model miss minus the line's miss                          |     0.13   |         2623 |   0.1571 |        335 |        0.0597 |              63 |  0.19 |    1.4  | ok      |
| model   | Model home lean (model margin minus real)                 |     0.3946 |         2581 |   0.0157 |        325 |        0.6041 |              60 | -0.5  |    3.01 | ok      |
| model   | 4+ flag win rate                                          |     0.5938 |          288 |   0.68   |         25 |        0.6    |               5 |  0.84 |    2.33 | ok      |
