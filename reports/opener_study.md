# The opener study

The full model (the one that prices the week, injuries and weather in) and a Tuesday model (the same fits with skill_out_value, opp_skill_out_value, off_snap_out, opp_def_snap_out, qb_out, wind_out, cold, rain, warm_in_cold at zero: what a Tuesday does not know), each graded on the model's side against the closing line (nflverse) and against the opening line (data/archive/openers_2015_2021.csv, 1786 regular-season games, 2015-2021). Spreads: every game with a line, and the site's flag (the model's side 4+ points from the line). Totals: every game with a line (the totals flag is a chance rule, not re-priced at the opener). Units at -110, one unit a bet. Rebuilt every weekly run (nflmodel/opener_study.py).

## Against the opener and the close, the archive's games

| Model | Line | Window | Games | ATS every game | % | Units | Flag | % | Units | Totals every game | % | Units |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Full model (Sunday: injuries and weather in) | close | 2015-18 | 1008 | 492-486-30 | 50.3 | -38.7 | 65-53-0 | 55.1 | 6.1 | 511-488-9 | 51.2 | -23.5 |
| Full model (Sunday: injuries and weather in) | close | 2019-21 | 778 | 400-364-14 | 52.4 | -0.4 | 64-33-0 | 66.0 | 25.2 | 413-356-9 | 53.7 | 19.5 |
| Tuesday model (no injury report, no weather) | close | 2015-18 | 1008 | 497-481-30 | 50.8 | -29.2 | 60-46-0 | 56.6 | 8.5 | 517-482-9 | 51.8 | -12.0 |
| Tuesday model (no injury report, no weather) | close | 2019-21 | 778 | 401-363-14 | 52.5 | 1.5 | 66-46-2 | 58.9 | 14.0 | 415-354-9 | 54.0 | 23.3 |
| Tuesday model (no injury report, no weather) | open | 2015-18 | 1008 | 503-469-36 | 51.7 | -11.7 | 49-42-2 | 53.8 | 2.5 | 545-445-18 | 55.1 | 50.5 |
| Tuesday model (no injury report, no weather) | open | 2019-21 | 778 | 432-326-20 | 57.0 | 66.7 | 65-34-3 | 65.7 | 25.1 | 419-343-16 | 55.0 | 37.9 |
| Full model (Sunday: injuries and weather in) | open | 2015-18 | 1008 | 507-465-36 | 52.2 | -4.1 | 63-44-1 | 58.9 | 13.3 | 535-455-18 | 54.0 | 31.4 |
| Full model (Sunday: injuries and weather in) | open | 2019-21 | 778 | 420-338-20 | 55.4 | 43.8 | 84-44-3 | 65.6 | 32.4 | 422-340-16 | 55.4 | 43.6 |

## At the close, the backtest's windows

| Model | Window | Games | ATS every game | % | Units | Flag | % | Units | Totals every game | % | Units |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Full model (Sunday: injuries and weather in) | 2015-18 | 1024 | 501-493-30 | 50.4 | -37.5 | 69-56-0 | 55.2 | 6.7 | 519-496-9 | 51.1 | -24.2 |
| Full model (Sunday: injuries and weather in) | 2019-22 | 1055 | 540-491-24 | 52.4 | -0.1 | 82-54-0 | 60.3 | 20.5 | 560-483-12 | 53.7 | 26.1 |
| Full model (Sunday: injuries and weather in) | 2023-25 | 816 | 403-394-19 | 50.6 | -27.6 | 41-23-1 | 64.1 | 14.3 | 450-361-5 | 55.5 | 48.1 |
| Tuesday model (no injury report, no weather) | 2015-18 | 1024 | 506-488-30 | 50.9 | -28.0 | 62-47-0 | 56.9 | 9.4 | 527-488-9 | 51.9 | -8.9 |
| Tuesday model (no injury report, no weather) | 2019-22 | 1055 | 528-503-24 | 51.2 | -23.0 | 86-65-3 | 57.0 | 13.2 | 559-484-12 | 53.6 | 24.2 |
| Tuesday model (no injury report, no weather) | 2023-25 | 816 | 400-397-19 | 50.2 | -33.4 | 39-33-1 | 54.2 | 2.5 | 439-372-5 | 54.1 | 27.1 |
