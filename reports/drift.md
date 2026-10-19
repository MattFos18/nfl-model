# Drift monitor, 2026

**0 alerts, 0 to watch.** Long run = 2015 to 2024; recent = 2025 and 2026 so far. ALERT at |z| >= 2.5 or a CUSUM trip (h 5); WATCH at |z| >= 2.0.


| group   | measure                                                   |   long_run |   long_run_n |   recent |   recent_n |   this_season |   this_season_n |     z |   cusum | level   |
|:--------|:----------------------------------------------------------|-----------:|-------------:|---------:|-----------:|--------------:|----------------:|------:|--------:|:--------|
| home    | Home margin (points)                                      |     1.7203 |         2581 |   1.8011 |        352 |        0.6322 |              87 |  0.1  |    2.67 | ok      |
| home    | Home cover margin vs the line                             |    -0.1019 |         2581 |   0.1903 |        352 |       -1.0805 |              87 |  0.4  |    3.1  | ok      |
| side    | Home favorite cover margin (road dog: the same, reversed) |    -0.1792 |         1624 |   0.1784 |        213 |       -1.9909 |              55 |  0.39 |    3.17 | ok      |
| side    | Road favorite cover margin (home dog: the same, reversed) |    -0.0362 |          995 |   0.1556 |        151 |        0.8514 |              37 |  0.17 |    2.15 | ok      |
| total   | Final total minus the closing total                       |     0.3223 |         2623 |   1.1813 |        364 |        1.2717 |              92 |  1.16 |    2.68 | ok      |
| total   | Over rate                                                 |     0.4852 |         2597 |   0.5192 |        364 |        0.5109 |              92 |  1.22 |    2.99 | ok      |
| key     | Margin exactly 3                                          |     0.146  |         2623 |   0.1566 |        364 |        0.1739 |              92 |  0.54 |    2.48 | ok      |
| key     | Margin exactly 7                                          |     0.0858 |         2623 |   0.1016 |        364 |        0.1196 |              92 |  1.01 |    2.56 | ok      |
| model   | Model miss minus the line's miss                          |     0.13   |         2623 |   0.1526 |        364 |        0.0725 |              92 |  0.17 |    1.4  | ok      |
| model   | Model home lean (model margin minus real)                 |     0.3946 |         2581 |   0.2365 |        352 |        1.315  |              87 | -0.22 |    3.01 | ok      |
| model   | 4+ flag win rate                                          |     0.5938 |          288 |   0.68   |         25 |        0.6    |               5 |  0.84 |    2.33 | ok      |
