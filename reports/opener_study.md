# The opener study

The full model (the one that prices the week, injuries and weather in) and a Tuesday model (the same fits with skill_out_value, opp_skill_out_value, off_snap_out, opp_def_snap_out, wind_out, cold, warm_in_cold at zero: what a Tuesday does not know), each graded on the model's side against the closing line (nflverse) and against the opening line (data/archive/openers_2015_2021.csv, 1786 regular-season games, 2015-2021). Spreads: every game with a line, and the site's flag (the model's side 4+ points from the line). Totals: every game with a line (the totals flag is a chance rule, not re-priced at the opener). Units at -110, one unit a bet. Rebuilt every weekly run (nflmodel/opener_study.py).

## Against the opener and the close, the archive's games

| Model | Line | Window | Games | ATS every game | % | Units | Flag | % | Units | Totals every game | % | Units |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Full model (Sunday: injuries and weather in) | close | 2015-18 | 1008 | 493-485-30 | 50.4 | -36.8 | 63-52-1 | 54.8 | 5.3 | 511-488-9 | 51.2 | -23.5 |
| Full model (Sunday: injuries and weather in) | close | 2019-21 | 778 | 405-359-14 | 53.0 | 9.2 | 63-35-0 | 64.3 | 22.3 | 413-356-9 | 53.7 | 19.5 |
| Tuesday model (no injury report, no weather) | close | 2015-18 | 1008 | 494-484-30 | 50.5 | -34.9 | 60-50-0 | 54.5 | 4.5 | 511-488-9 | 51.2 | -23.5 |
| Tuesday model (no injury report, no weather) | close | 2019-21 | 778 | 399-365-14 | 52.2 | -2.3 | 65-45-2 | 59.1 | 14.1 | 413-356-9 | 53.7 | 19.5 |
| Tuesday model (no injury report, no weather) | open | 2015-18 | 1008 | 508-464-36 | 52.3 | -2.2 | 50-41-2 | 54.9 | 4.5 | 529-461-18 | 53.4 | 19.9 |
| Tuesday model (no injury report, no weather) | open | 2019-21 | 778 | 427-331-20 | 56.3 | 57.2 | 64-33-3 | 66.0 | 25.2 | 421-341-16 | 55.2 | 41.7 |
| Full model (Sunday: injuries and weather in) | open | 2015-18 | 1008 | 503-469-36 | 51.7 | -11.7 | 60-42-2 | 58.8 | 12.5 | 529-461-18 | 53.4 | 19.9 |
| Full model (Sunday: injuries and weather in) | open | 2019-21 | 778 | 428-330-20 | 56.5 | 59.1 | 85-42-3 | 66.9 | 35.3 | 421-341-16 | 55.2 | 41.7 |

## At the close, the backtest's windows

| Model | Window | Games | ATS every game | % | Units | Flag | % | Units | Totals every game | % | Units |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Full model (Sunday: injuries and weather in) | 2015-18 | 1024 | 502-492-30 | 50.5 | -35.6 | 67-54-1 | 55.4 | 6.9 | 521-494-9 | 51.3 | -20.4 |
| Full model (Sunday: injuries and weather in) | 2019-22 | 1055 | 547-484-24 | 53.1 | 13.3 | 82-55-0 | 59.9 | 19.5 | 556-487-12 | 53.3 | 18.5 |
| Full model (Sunday: injuries and weather in) | 2023-25 | 816 | 399-398-19 | 50.1 | -35.3 | 42-22-1 | 65.6 | 16.2 | 451-360-5 | 55.6 | 50.0 |
| Tuesday model (no injury report, no weather) | 2015-18 | 1024 | 503-491-30 | 50.6 | -33.7 | 62-51-0 | 54.9 | 5.4 | 521-494-9 | 51.3 | -20.4 |
| Tuesday model (no injury report, no weather) | 2019-22 | 1055 | 529-502-24 | 51.3 | -21.1 | 84-65-3 | 56.4 | 11.4 | 556-487-12 | 53.3 | 18.5 |
| Tuesday model (no injury report, no weather) | 2023-25 | 816 | 398-399-19 | 49.9 | -37.2 | 40-36-1 | 52.6 | 0.4 | 451-360-5 | 55.6 | 50.0 |
