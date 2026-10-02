# The opener study

The full model (the one that prices the week, injuries and weather in) and a Tuesday model (the same fits with skill_out_value, opp_skill_out_value, off_snap_out, opp_def_snap_out, qb_out, wind_out, cold, rain, warm_in_cold at zero: what a Tuesday does not know), each graded on the model's side against the closing line (nflverse) and against the opening line (data/archive/openers_2015_2021.csv, 1786 regular-season games, 2015-2021). Spreads: every game with a line, and the site's flag (the model's side 4+ points from the line). Totals: every game with a line (the totals flag is a chance rule, not re-priced at the opener). Units at -110, one unit a bet. Rebuilt every weekly run (nflmodel/opener_study.py).

## Against the opener and the close, the archive's games

| Model | Line | Window | Games | ATS every game | % | Units | Flag | % | Units | Totals every game | % | Units |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Full model (Sunday: injuries and weather in) | close | 2015-18 | 1008 | 493-485-30 | 50.4 | -36.8 | 63-52-0 | 54.8 | 5.3 | 493-506-9 | 49.3 | -57.8 |
| Full model (Sunday: injuries and weather in) | close | 2019-21 | 778 | 402-362-14 | 52.6 | 3.5 | 62-31-0 | 66.7 | 25.4 | 401-368-9 | 52.1 | -3.5 |
| Tuesday model (no injury report, no weather) | close | 2015-18 | 1008 | 499-479-30 | 51.0 | -25.4 | 60-47-0 | 56.1 | 7.5 | 490-509-9 | 49.0 | -63.5 |
| Tuesday model (no injury report, no weather) | close | 2019-21 | 778 | 399-365-14 | 52.2 | -2.3 | 64-46-2 | 58.2 | 12.2 | 409-360-9 | 53.2 | 11.8 |
| Tuesday model (no injury report, no weather) | open | 2015-18 | 1008 | 502-470-36 | 51.6 | -13.6 | 49-42-2 | 53.8 | 2.5 | 531-459-18 | 53.6 | 23.7 |
| Tuesday model (no injury report, no weather) | open | 2019-21 | 778 | 429-329-20 | 56.6 | 61.0 | 63-35-3 | 64.3 | 22.3 | 412-350-16 | 54.1 | 24.5 |
| Full model (Sunday: injuries and weather in) | open | 2015-18 | 1008 | 505-467-36 | 52.0 | -7.9 | 62-44-1 | 58.5 | 12.4 | 532-458-18 | 53.7 | 25.6 |
| Full model (Sunday: injuries and weather in) | open | 2019-21 | 778 | 422-336-20 | 55.7 | 47.6 | 86-45-3 | 65.6 | 33.2 | 411-351-16 | 53.9 | 22.6 |

## At the close, the backtest's windows

| Model | Window | Games | ATS every game | % | Units | Flag | % | Units | Totals every game | % | Units |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Full model (Sunday: injuries and weather in) | 2015-18 | 1024 | 502-492-30 | 50.5 | -35.6 | 67-55-0 | 54.9 | 5.9 | 501-514-9 | 49.4 | -58.5 |
| Full model (Sunday: injuries and weather in) | 2019-22 | 1055 | 542-489-24 | 52.6 | 3.7 | 79-50-0 | 61.2 | 21.8 | 545-498-12 | 52.3 | -2.5 |
| Full model (Sunday: injuries and weather in) | 2023-25 | 816 | 402-395-19 | 50.4 | -29.5 | 41-25-1 | 62.1 | 12.3 | 433-378-5 | 53.4 | 15.6 |
| Tuesday model (no injury report, no weather) | 2015-18 | 1024 | 508-486-30 | 51.1 | -24.2 | 62-48-0 | 56.4 | 8.4 | 500-515-9 | 49.3 | -60.5 |
| Tuesday model (no injury report, no weather) | 2019-22 | 1055 | 529-502-24 | 51.3 | -21.1 | 83-65-3 | 56.1 | 10.5 | 556-487-12 | 53.3 | 18.5 |
| Tuesday model (no injury report, no weather) | 2023-25 | 816 | 399-398-19 | 50.1 | -35.3 | 39-33-1 | 54.2 | 2.5 | 443-368-5 | 54.6 | 34.7 |
