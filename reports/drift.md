# Drift monitor, 2026

**0 alerts, 0 to watch.** Long run = 2015 to 2024; recent = 2025 and 2026 so far. ALERT at |z| >= 2.5 or a CUSUM trip (h 5); WATCH at |z| >= 2.0.


| group   | measure                                                   |   long_run |   long_run_n |   recent |   recent_n |   this_season |   this_season_n |     z |   cusum | level   |
|:--------|:----------------------------------------------------------|-----------:|-------------:|---------:|-----------:|--------------:|----------------:|------:|--------:|:--------|
| home    | Home margin (points)                                      |     1.7203 |         2581 |   1.8827 |        341 |        0.8289 |              76 |  0.2  |    2.67 | ok      |
| home    | Home cover margin vs the line                             |    -0.1019 |         2581 |   0.2654 |        341 |       -0.9276 |              76 |  0.5  |    3.1  | ok      |
| side    | Home favorite cover margin (road dog: the same, reversed) |    -0.1792 |         1624 |   0.2727 |        209 |       -1.7745 |              51 |  0.49 |    3.17 | ok      |
| side    | Road favorite cover margin (home dog: the same, reversed) |    -0.0362 |          995 |   0.1319 |        144 |        0.9    |              30 |  0.14 |    2.15 | ok      |
| total   | Final total minus the closing total                       |     0.3223 |         2623 |   1.2989 |        353 |        1.7963 |              81 |  1.31 |    2.68 | ok      |
| total   | Over rate                                                 |     0.4852 |         2597 |   0.5184 |        353 |        0.5062 |              81 |  1.17 |    2.99 | ok      |
| key     | Margin exactly 3                                          |     0.146  |         2623 |   0.1558 |        353 |        0.1728 |              81 |  0.49 |    2.96 | ok      |
| key     | Margin exactly 7                                          |     0.0858 |         2623 |   0.0963 |        353 |        0.0988 |              81 |  0.66 |    2.56 | ok      |
| model   | Model miss minus the line's miss                          |     0.13   |         2623 |   0.1345 |        353 |       -0.0171 |              81 |  0.03 |    1.4  | ok      |
| model   | Model home lean (model margin minus real)                 |     0.3946 |         2581 |   0.1362 |        341 |        1.0207 |              76 | -0.35 |    3.01 | ok      |
| model   | 4+ flag win rate                                          |     0.5938 |          288 |   0.68   |         25 |        0.6    |               5 |  0.84 |    2.33 | ok      |
