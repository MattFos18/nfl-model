# Drift monitor, 2026

**0 alerts, 0 to watch.** Long run = 2015 to 2024; recent = 2025 and 2026 so far. ALERT at |z| >= 2.5 or a CUSUM trip (h 5); WATCH at |z| >= 2.0.


| group   | measure                                                   |   long_run |   long_run_n |   recent |   recent_n |   this_season |   this_season_n |     z |   cusum | level   |
|:--------|:----------------------------------------------------------|-----------:|-------------:|---------:|-----------:|--------------:|----------------:|------:|--------:|:--------|
| home    | Home margin (points)                                      |     1.7203 |         2581 |   2.0531 |        320 |        1.4182 |              55 |  0.4  |    2.67 | ok      |
| home    | Home cover margin vs the line                             |    -0.1019 |         2581 |   0.3781 |        320 |       -0.7273 |              55 |  0.64 |    3.1  | ok      |
| side    | Home favorite cover margin (road dog: the same, reversed) |    -0.1792 |         1624 |   0.4949 |        195 |       -1.3784 |              37 |  0.71 |    3.17 | ok      |
| side    | Road favorite cover margin (home dog: the same, reversed) |    -0.0362 |          995 |   0.1259 |        135 |        1.1905 |              21 |  0.14 |    2.15 | ok      |
| total   | Final total minus the closing total                       |     0.3223 |         2623 |   1.1182 |        330 |        0.9655 |              58 |  1.03 |    2.68 | ok      |
| total   | Over rate                                                 |     0.4852 |         2597 |   0.5152 |        330 |        0.4828 |              58 |  1.03 |    2.99 | ok      |
| key     | Margin exactly 3                                          |     0.146  |         2623 |   0.1515 |        330 |        0.1552 |              58 |  0.27 |    2.48 | ok      |
| key     | Margin exactly 7                                          |     0.0858 |         2623 |   0.0939 |        330 |        0.0862 |              58 |  0.5  |    2.56 | ok      |
| model   | Model miss minus the line's miss                          |     0.13   |         2623 |   0.1454 |        330 |       -0.0155 |              58 |  0.11 |    1.4  | ok      |
| model   | Model home lean (model margin minus real)                 |     0.3946 |         2581 |   0.0622 |        320 |        0.9279 |              55 | -0.44 |    3.01 | ok      |
| model   | 4+ flag win rate                                          |     0.5938 |          288 |   0.68   |         25 |        0.6    |               5 |  0.84 |    2.33 | ok      |
