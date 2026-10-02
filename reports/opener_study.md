# The opener study

The full model (the one that prices the week, injuries and weather in) and a Tuesday model (the same fits with skill_out_value, opp_skill_out_value, off_snap_out, opp_def_snap_out, qb_out, wind_out, cold, rain, warm_in_cold at zero: what a Tuesday does not know), each graded on the model's side against the closing line (nflverse) and against the opening line (data/archive/openers_2015_2021.csv, 1786 regular-season games, 2015-2021). Spreads: every game with a line, and the site's flag (the model's side 4+ points from the line). Totals: every game with a line (the totals flag is a chance rule, not re-priced at the opener). Units at -110, one unit a bet. Rebuilt every weekly run (nflmodel/opener_study.py).

## Against the opener and the close, the archive's games

| Model | Line | Window | Games | ATS every game | % | Units | Flag | % | Units | Totals every game | % | Units |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Full model (Sunday: injuries and weather in) | close | 2015-18 | 1008 | 495-483-30 | 50.6 | -33.0 | 64-55-0 | 53.8 | 3.2 | 497-502-9 | 49.7 | -50.2 |
| Full model (Sunday: injuries and weather in) | close | 2019-21 | 778 | 400-364-14 | 52.4 | -0.4 | 63-32-0 | 66.3 | 25.3 | 410-359-9 | 53.3 | 13.7 |
| Tuesday model (no injury report, no weather) | close | 2015-18 | 1008 | 501-477-30 | 51.2 | -21.5 | 59-49-0 | 54.6 | 4.6 | 496-503-9 | 49.6 | -52.1 |
| Tuesday model (no injury report, no weather) | close | 2019-21 | 778 | 399-365-14 | 52.2 | -2.3 | 65-44-2 | 59.6 | 15.1 | 407-362-9 | 52.9 | 8.0 |
| Tuesday model (no injury report, no weather) | open | 2015-18 | 1008 | 503-469-36 | 51.7 | -11.7 | 50-39-2 | 56.2 | 6.5 | 528-462-18 | 53.3 | 18.0 |
| Tuesday model (no injury report, no weather) | open | 2019-21 | 778 | 422-336-20 | 55.7 | 47.6 | 64-35-3 | 64.6 | 23.2 | 408-354-16 | 53.5 | 16.9 |
| Full model (Sunday: injuries and weather in) | open | 2015-18 | 1008 | 504-468-36 | 51.9 | -9.8 | 62-44-1 | 58.5 | 12.4 | 527-463-18 | 53.2 | 16.1 |
| Full model (Sunday: injuries and weather in) | open | 2019-21 | 778 | 421-337-20 | 55.5 | 45.7 | 86-45-3 | 65.6 | 33.2 | 410-352-16 | 53.8 | 20.7 |

## At the close, the backtest's windows

| Model | Window | Games | ATS every game | % | Units | Flag | % | Units | Totals every game | % | Units |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Full model (Sunday: injuries and weather in) | 2015-18 | 1024 | 504-490-30 | 50.7 | -31.8 | 68-58-0 | 54.0 | 3.8 | 507-508-9 | 50.0 | -47.1 |
| Full model (Sunday: injuries and weather in) | 2019-22 | 1055 | 541-490-24 | 52.5 | 1.8 | 81-52-0 | 60.9 | 21.6 | 554-489-12 | 53.1 | 14.6 |
| Full model (Sunday: injuries and weather in) | 2023-25 | 816 | 400-397-19 | 50.2 | -33.4 | 41-24-1 | 63.1 | 13.3 | 434-377-5 | 53.5 | 17.5 |
| Tuesday model (no injury report, no weather) | 2015-18 | 1024 | 510-484-30 | 51.3 | -20.4 | 61-50-0 | 55.0 | 5.5 | 506-509-9 | 49.9 | -49.0 |
| Tuesday model (no injury report, no weather) | 2019-22 | 1055 | 530-501-24 | 51.4 | -19.2 | 84-65-3 | 56.4 | 11.4 | 552-491-12 | 52.9 | 10.8 |
| Tuesday model (no injury report, no weather) | 2023-25 | 816 | 399-398-19 | 50.1 | -35.3 | 39-35-1 | 52.7 | 0.5 | 443-368-5 | 54.6 | 34.7 |
