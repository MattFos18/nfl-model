# Drift monitor, 2026

**0 alerts, 0 to watch.** Long run = 2015 to 2024; recent = 2025 and 2026 so far. ALERT at |z| >= 2.5 or a CUSUM trip (h 5); WATCH at |z| >= 2.0.


| group   | measure                                                   |   long_run |   long_run_n |   recent |   recent_n |   this_season |   this_season_n |     z |   cusum | level   |
|:--------|:----------------------------------------------------------|-----------:|-------------:|---------:|-----------:|--------------:|----------------:|------:|--------:|:--------|
| home    | Home margin (points)                                      |     1.7203 |         2581 |   1.3775 |        408 |       -0.1189 |             143 | -0.45 |    2.91 | ok      |
| home    | Home cover margin vs the line                             |    -0.1019 |         2581 |  -0.1716 |        408 |       -1.6154 |             143 | -0.1  |    3.1  | ok      |
| side    | Home favorite cover margin (road dog: the same, reversed) |    -0.1792 |         1624 |   0.2863 |        248 |       -0.85   |              90 |  0.54 |    3.17 | ok      |
| side    | Road favorite cover margin (home dog: the same, reversed) |    -0.0362 |          995 |   1.0743 |        175 |        3.2131 |              61 |  1.04 |    2.44 | ok      |
| total   | Final total minus the closing total                       |     0.3223 |         2623 |   1.065  |        423 |        0.9106 |             151 |  1.07 |    2.68 | ok      |
| total   | Over rate                                                 |     0.4852 |         2597 |   0.5225 |        423 |        0.5232 |             151 |  1.42 |    2.99 | ok      |
| key     | Margin exactly 3                                          |     0.146  |         2623 |   0.156  |        423 |        0.1656 |             151 |  0.54 |    2.48 | ok      |
| key     | Margin exactly 7                                          |     0.0858 |         2623 |   0.0922 |        423 |        0.0861 |             151 |  0.44 |    2.56 | ok      |
| model   | Model miss minus the line's miss                          |     0.13   |         2623 |   0.2015 |        423 |        0.2409 |             151 |  0.56 |    1.77 | ok      |
| model   | Model home lean (model margin minus real)                 |     0.3946 |         2581 |   0.5709 |        408 |        1.8466 |             143 |  0.26 |    3.01 | ok      |
| model   | 4+ flag win rate                                          |     0.5938 |          288 |   0.6296 |         27 |        0.4286 |               7 |  0.36 |    2.33 | ok      |
