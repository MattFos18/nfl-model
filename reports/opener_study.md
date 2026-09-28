# The opener study

The full model (the one that prices the week, injuries and weather in) and a Tuesday model (the same fits with skill_out_value, opp_skill_out_value, off_snap_out, opp_def_snap_out, qb_out, wind_out, cold, rain, warm_in_cold at zero: what a Tuesday does not know), each graded on the model's side against the closing line (nflverse) and against the opening line (data/archive/openers_2015_2021.csv, 1786 regular-season games, 2015-2021). Flags: the model's side the cut or more points from the line, at 3 and 4 points (the second is the site's spread flag); units at -110. Every game ATS counts every game with a line. Rebuilt every weekly run (nflmodel/opener_study.py).

## Against the opener and the close, the archive's games

| Cut | Model | Line | Window | Games | ATS every game | % | Flags | % | Units | Totals every game | % | Totals flagged | % | Units |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 3+ | Full model (Sunday: injuries and weather in) | close | 2015-18 | 1008 | 498-480-30 | 50.9 | 116-113-3 | 50.7 | -7.5 | 503-496-9 | 50.4 | 134-121-3 | 52.5 | 0.8 |
| 3+ | Full model (Sunday: injuries and weather in) | close | 2019-21 | 778 | 401-363-14 | 52.5 | 108-82-1 | 56.8 | 16.2 | 406-363-9 | 52.8 | 141-89-1 | 61.3 | 39.2 |
| 3+ | Tuesday model (no injury report, no weather) | close | 2015-18 | 1008 | 494-484-30 | 50.5 | 124-90-3 | 57.9 | 22.7 | 507-492-9 | 50.8 | 113-110-2 | 50.7 | -7.3 |
| 3+ | Tuesday model (no injury report, no weather) | close | 2019-21 | 778 | 399-365-14 | 52.2 | 106-86-3 | 55.2 | 10.4 | 402-367-9 | 52.3 | 128-89-1 | 59.0 | 27.4 |
| 3+ | Tuesday model (no injury report, no weather) | open | 2015-18 | 1008 | 505-467-36 | 52.0 | 120-75-10 | 61.5 | 34.1 | 548-442-18 | 55.4 | 148-105-5 | 58.5 | 29.5 |
| 3+ | Tuesday model (no injury report, no weather) | open | 2019-21 | 778 | 430-328-20 | 56.7 | 119-73-7 | 62.0 | 35.2 | 410-352-16 | 53.8 | 171-118-3 | 59.2 | 37.5 |
| 3+ | Full model (Sunday: injuries and weather in) | open | 2015-18 | 1008 | 505-467-36 | 52.0 | 112-95-7 | 54.1 | 6.8 | 546-444-18 | 55.2 | 162-113-9 | 58.9 | 34.3 |
| 3+ | Full model (Sunday: injuries and weather in) | open | 2019-21 | 778 | 420-338-20 | 55.4 | 138-72-7 | 65.7 | 53.5 | 423-339-16 | 55.5 | 174-118-4 | 59.6 | 40.2 |
| 4+ | Full model (Sunday: injuries and weather in) | close | 2015-18 | 1008 | 498-480-30 | 50.9 | 64-52-0 | 55.2 | 6.2 | 503-496-9 | 50.4 | 83-65-2 | 56.1 | 10.5 |
| 4+ | Full model (Sunday: injuries and weather in) | close | 2019-21 | 778 | 401-363-14 | 52.5 | 66-33-0 | 66.7 | 27.0 | 406-363-9 | 52.8 | 84-45-1 | 65.1 | 31.4 |
| 4+ | Tuesday model (no injury report, no weather) | close | 2015-18 | 1008 | 494-484-30 | 50.5 | 62-47-0 | 56.9 | 9.4 | 507-492-9 | 50.8 | 67-57-1 | 54.0 | 3.9 |
| 4+ | Tuesday model (no injury report, no weather) | close | 2019-21 | 778 | 399-365-14 | 52.2 | 62-43-2 | 59.0 | 13.4 | 402-367-9 | 52.3 | 79-46-1 | 63.2 | 25.8 |
| 4+ | Tuesday model (no injury report, no weather) | open | 2015-18 | 1008 | 505-467-36 | 52.0 | 50-41-2 | 54.9 | 4.5 | 548-442-18 | 55.4 | 73-50-1 | 59.3 | 16.4 |
| 4+ | Tuesday model (no injury report, no weather) | open | 2019-21 | 778 | 430-328-20 | 56.7 | 64-33-3 | 66.0 | 25.2 | 410-352-16 | 53.8 | 110-71-1 | 60.8 | 29.0 |
| 4+ | Full model (Sunday: injuries and weather in) | open | 2015-18 | 1008 | 505-467-36 | 52.0 | 62-43-1 | 59.0 | 13.4 | 546-444-18 | 55.2 | 84-58-3 | 59.2 | 18.4 |
| 4+ | Full model (Sunday: injuries and weather in) | open | 2019-21 | 778 | 420-338-20 | 55.4 | 87-42-3 | 67.4 | 37.1 | 423-339-16 | 55.5 | 109-67-2 | 61.9 | 32.1 |

## At the close, the backtest's windows

| Cut | Model | Window | Games | ATS every game | % | Flags | % | Units | Totals every game | % | Totals flagged | % | Units |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 3+ | Full model (Sunday: injuries and weather in) | 2015-18 | 1024 | 507-487-30 | 51.0 | 120-117-3 | 50.6 | -7.9 | 513-502-9 | 50.5 | 137-122-3 | 52.9 | 2.5 |
| 3+ | Full model (Sunday: injuries and weather in) | 2019-22 | 1055 | 543-488-24 | 52.7 | 139-120-2 | 53.7 | 6.4 | 541-502-12 | 51.9 | 181-126-2 | 59.0 | 38.5 |
| 3+ | Full model (Sunday: injuries and weather in) | 2023-25 | 816 | 402-395-19 | 50.4 | 83-67-3 | 55.3 | 8.5 | 429-382-5 | 52.9 | 109-98-1 | 52.7 | 1.1 |
| 3+ | Tuesday model (no injury report, no weather) | 2015-18 | 1024 | 503-491-30 | 50.6 | 126-92-3 | 57.8 | 22.5 | 517-498-9 | 50.9 | 117-111-2 | 51.3 | -4.6 |
| 3+ | Tuesday model (no injury report, no weather) | 2019-22 | 1055 | 528-503-24 | 51.2 | 139-131-4 | 51.5 | -4.6 | 543-500-12 | 52.1 | 170-131-2 | 56.5 | 23.5 |
| 3+ | Tuesday model (no injury report, no weather) | 2023-25 | 816 | 405-392-19 | 50.8 | 91-80-4 | 53.2 | 2.7 | 414-397-5 | 51.0 | 101-93-2 | 52.1 | -1.2 |
| 4+ | Full model (Sunday: injuries and weather in) | 2015-18 | 1024 | 507-487-30 | 51.0 | 68-55-0 | 55.3 | 6.8 | 513-502-9 | 50.5 | 86-65-2 | 57.0 | 13.2 |
| 4+ | Full model (Sunday: injuries and weather in) | 2019-22 | 1055 | 543-488-24 | 52.7 | 83-54-0 | 60.6 | 21.5 | 541-502-12 | 51.9 | 109-60-1 | 64.5 | 39.1 |
| 4+ | Full model (Sunday: injuries and weather in) | 2023-25 | 816 | 402-395-19 | 50.4 | 44-26-1 | 62.9 | 14.0 | 429-382-5 | 52.9 | 54-55-0 | 49.5 | -5.9 |
| 4+ | Tuesday model (no injury report, no weather) | 2015-18 | 1024 | 503-491-30 | 50.6 | 64-48-0 | 57.1 | 10.2 | 517-498-9 | 50.9 | 69-57-1 | 54.8 | 5.7 |
| 4+ | Tuesday model (no injury report, no weather) | 2019-22 | 1055 | 528-503-24 | 51.2 | 81-62-3 | 56.6 | 11.6 | 543-500-12 | 52.1 | 101-61-1 | 62.3 | 30.8 |
| 4+ | Tuesday model (no injury report, no weather) | 2023-25 | 816 | 405-392-19 | 50.8 | 42-34-1 | 55.3 | 4.2 | 414-397-5 | 51.0 | 51-48-1 | 51.5 | -1.6 |
