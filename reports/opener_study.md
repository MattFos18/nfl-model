# The opener study

The full model (the one that prices the week, injuries and weather in) and a Tuesday model (the same fits with skill_out_value, opp_skill_out_value, off_snap_out, opp_def_snap_out, qb_out, wind_out, cold, rain, warm_in_cold at zero: what a Tuesday does not know), each graded on the model's side against the closing line (nflverse) and against the opening line (data/archive/openers_2015_2021.csv, 1786 regular-season games, 2015-2021). Spreads: every game with a line, and the site's flag (the model's side 4+ points from the line). Totals: every game with a line (the totals flag is a chance rule, not re-priced at the opener). Units at -110, one unit a bet. Rebuilt every weekly run (nflmodel/opener_study.py).

## Against the opener and the close, the archive's games

| Model | Line | Window | Games | ATS every game | % | Units | Flag | % | Units | Totals every game | % | Units |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Full model (Sunday: injuries and weather in) | close | 2015-18 | 1008 | 498-480-30 | 50.9 | -27.3 | 64-52-0 | 55.2 | 6.2 | 503-496-9 | 50.4 | -38.7 |
| Full model (Sunday: injuries and weather in) | close | 2019-21 | 778 | 401-363-14 | 52.5 | 1.5 | 66-33-0 | 66.7 | 27.0 | 406-363-9 | 52.8 | 6.1 |
| Tuesday model (no injury report, no weather) | close | 2015-18 | 1008 | 494-484-30 | 50.5 | -34.9 | 62-47-0 | 56.9 | 9.4 | 507-492-9 | 50.8 | -31.1 |
| Tuesday model (no injury report, no weather) | close | 2019-21 | 778 | 399-365-14 | 52.2 | -2.3 | 62-43-2 | 59.0 | 13.4 | 402-367-9 | 52.3 | -1.5 |
| Tuesday model (no injury report, no weather) | open | 2015-18 | 1008 | 505-467-36 | 52.0 | -7.9 | 50-41-2 | 54.9 | 4.5 | 548-442-18 | 55.4 | 56.2 |
| Tuesday model (no injury report, no weather) | open | 2019-21 | 778 | 430-328-20 | 56.7 | 62.9 | 64-33-3 | 66.0 | 25.2 | 410-352-16 | 53.8 | 20.7 |
| Full model (Sunday: injuries and weather in) | open | 2015-18 | 1008 | 505-467-36 | 52.0 | -7.9 | 62-43-1 | 59.0 | 13.4 | 546-444-18 | 55.2 | 52.4 |
| Full model (Sunday: injuries and weather in) | open | 2019-21 | 778 | 420-338-20 | 55.4 | 43.8 | 87-42-3 | 67.4 | 37.1 | 423-339-16 | 55.5 | 45.5 |

## At the close, the backtest's windows

| Model | Window | Games | ATS every game | % | Units | Flag | % | Units | Totals every game | % | Units |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Full model (Sunday: injuries and weather in) | 2015-18 | 1024 | 507-487-30 | 51.0 | -26.1 | 68-55-0 | 55.3 | 6.8 | 513-502-9 | 50.5 | -35.6 |
| Full model (Sunday: injuries and weather in) | 2019-22 | 1055 | 543-488-24 | 52.7 | 5.6 | 83-54-0 | 60.6 | 21.5 | 541-502-12 | 51.9 | -10.2 |
| Full model (Sunday: injuries and weather in) | 2023-25 | 816 | 402-395-19 | 50.4 | -29.5 | 44-26-1 | 62.9 | 14.0 | 429-382-5 | 52.9 | 8.0 |
| Tuesday model (no injury report, no weather) | 2015-18 | 1024 | 503-491-30 | 50.6 | -33.7 | 64-48-0 | 57.1 | 10.2 | 517-498-9 | 50.9 | -28.0 |
| Tuesday model (no injury report, no weather) | 2019-22 | 1055 | 528-503-24 | 51.2 | -23.0 | 81-62-3 | 56.6 | 11.6 | 543-500-12 | 52.1 | -6.4 |
| Tuesday model (no injury report, no weather) | 2023-25 | 816 | 405-392-19 | 50.8 | -23.8 | 42-34-1 | 55.3 | 4.2 | 414-397-5 | 51.0 | -20.6 |
