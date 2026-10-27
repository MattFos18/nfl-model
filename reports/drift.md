# Drift monitor, 2026

**0 alerts, 0 to watch.** Long run = 2015 to 2024; recent = 2025 and 2026 so far. ALERT at |z| >= 2.5 or a CUSUM trip (h 5); WATCH at |z| >= 2.0.


| group   | measure                                                   |   long_run |   long_run_n |   recent |   recent_n |   this_season |   this_season_n |     z |   cusum | level   |
|:--------|:----------------------------------------------------------|-----------:|-------------:|---------:|-----------:|--------------:|----------------:|------:|--------:|:--------|
| home    | Home margin (points)                                      |     1.7203 |         2581 |   1.5628 |        366 |       -0.0693 |             101 | -0.2  |    2.67 | ok      |
| home    | Home cover margin vs the line                             |    -0.1019 |         2581 |  -0.0423 |        366 |       -1.7475 |             101 |  0.08 |    3.1  | ok      |
| side    | Home favorite cover margin (road dog: the same, reversed) |    -0.1792 |         1624 |  -0.0136 |        221 |       -2.3889 |              63 |  0.18 |    3.17 | ok      |
| side    | Road favorite cover margin (home dog: the same, reversed) |    -0.0362 |          995 |   0.4304 |        158 |        1.7273 |              44 |  0.42 |    2.15 | ok      |
| total   | Final total minus the closing total                       |     0.3223 |         2623 |   1.1069 |        379 |        0.9953 |             107 |  1.08 |    2.68 | ok      |
| total   | Over rate                                                 |     0.4852 |         2597 |   0.5224 |        379 |        0.5234 |             107 |  1.36 |    2.99 | ok      |
| key     | Margin exactly 3                                          |     0.146  |         2623 |   0.1583 |        379 |        0.1776 |             107 |  0.63 |    2.48 | ok      |
| key     | Margin exactly 7                                          |     0.0858 |         2623 |   0.0976 |        379 |        0.1028 |             107 |  0.77 |    2.56 | ok      |
| model   | Model miss minus the line's miss                          |     0.13   |         2623 |   0.1792 |        379 |        0.178  |             107 |  0.37 |    1.4  | ok      |
| model   | Model home lean (model margin minus real)                 |     0.3946 |         2581 |   0.4551 |        366 |        1.9574 |             101 |  0.08 |    3.01 | ok      |
| model   | 4+ flag win rate                                          |     0.5938 |          288 |   0.68   |         25 |        0.6    |               5 |  0.84 |    2.33 | ok      |
