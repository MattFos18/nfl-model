# Data fixes: starting QB, venues abroad, recorded wind, line after kickoff (2 Oct 2026)

`experiments/data_fixes.py`, numbers in `reports/data_fixes.csv`. A data correction approved by Matt after the 2 Oct
2026 data audit: the backtest is meant to price the QB who started, the weather at the stadium where the game was
played, and the wind that blew. No bet rule, threshold or model input changes; records may move either way and are
reported as they came out.

## What was wrong and what changed

| # | Fault | Rows | Fix (code) | Check (`data_checks.check_inputs`) |
|---|---|---|---|---|
| 1 | nflverse's schedule lists a starting QB who took no dropback (a projected starter never reconciled: Mariota for WAS Weeks 9-13 2024, Hurts in 2024_17_DAL_PHI where Pickett started, Dalton for CAR, Flacco for IND) | 44 team-games 2022-2025 (4 / 33 / 7), 3 in 2026 | `build.fix_starters`: the played game's starter becomes the passer on the team's first dropback among passers with 3+ (a trick throw is not a start); a listed QB who dropped back at all keeps the game; unplayed games keep the announced starter; nflverse's id kept as `*_qb_id_listed` | a played game's starter with no dropback in `qb_games` fails |
| 2 | Games abroad listed at a US stadium (2025 Sao Paulo as SoFi dome, Dublin, London x3, Berlin as Lucas Oil closed, Madrid as Hard Rock) or under a dome (2026 Melbourne, Paris, Munich); Philadelphia at Jacksonville in London listed as a Jacksonville home game. The weather lookup matched city names that stadium names never carry ("Wembley"), so London and Mexico City games read the home team's US stadium; the forecast history read KJAX and KMIA for London and Madrid | 11 games | `nflmodel/venues.py`: `GAME_VENUE` overrides, every stadium abroad and every stadium a team has left (Oakland, San Diego, Carson, LA Coliseum, TCF Bank, Candlestick) by stadium id; `weather`, `weather_archive`, `forecast_archive`, `forecast_history`, `wind_live` and `trends`' travel read `venues.site`; stored forecast rows for games abroad are dropped | a neutral-site game at the home team's own stadium, a stadium abroad resolved to a US site, or an open-air stadium abroad marked dome fails |
| 3 | Recorded kickoff wind far off: 2016_13_NYG_PIT 71 mph (archive 6.4), 2023_13_SF_PHI 44 (archive 4.6, forecast 5.0) | 30 games 2013-2024 replaced (24 from 2015), 2008_02_TEN_CIN 70 blanked | `build.fix_wind`: more than 10 mph from the Open-Meteo archive's kickoff hour at the real site is replaced by the archive where no GFS forecast exists (before 2018) or the forecast sits closer to the archive; 5 games where the forecast sides with the schedule (three in Denver) keep it; above 40 mph with nothing to replace it is blanked; schedule figure kept as `wind_listed`. `data/weather/archive_kickoff.csv` refetched for the 213 rows fetched at the wrong site (plus Sao Paulo and Berlin 2025, which had none) | wind above 40 mph fails |
| 4 | `lines.latest()` had no kickoff cutoff: a snapshot 1m41s after kickoff became 2026_03_LA_DEN's line | 1 game | `lines.before_kickoff`, used by `live_lines` (picks, props, cards) and the tie check; CLV and results already cut | `tests/test_data_fixes.py` |

## Before and after (walk-forward 2015-2025, same raw data, same machine)

Regular season; records weeks 1-17. Team MAE is the miss per team score.

| window | team MAE | margin MAE | total MAE | spread flag (4+) | unders 55%+ | wind under |
|---|---|---|---|---|---|---|
| 2015-18 before | 7.4085 | 9.9483 | 10.7404 | 63-55 | 137-124 | 23-19 |
| 2015-18 after | 7.4005 | 9.9492 | 10.7132 | 64-53 | 137-121 | 23-19 |
| 2019-22 before | 7.3438 | 10.0258 | 10.4942 | 80-52 | 203-147 | 143-89 |
| 2019-22 after | 7.3478 | 10.0232 | 10.5047 | 83-50 | 210-152 | 143-89 |
| 2023-25 before | 7.2426 | 9.9039 | 10.1058 | 39-22 | 98-69 | 83-52 |
| 2023-25 after | 7.2356 | 9.8991 | 10.0867 | 37-18 | 99-72 | 83-52 |

Reading. Team points miss better on 2015-18 and 2023-25, 0.004 worse on 2019-22 (the wind fixes are the only change
there before 2022); margin miss better on 2019-22 and 2023-25, 0.001 worse on 2015-18. The spread flag gains on the
first two windows and on 2023-25 loses two wins and four losses (39-22, 63.9%, to 37-18, 67.3%). The 55% unders add
seven bets on 2019-22 at 7-5. The wind under is unchanged (no game abroad had a 10+ reading). Not a selection: the fixes
were fixed before this run and are kept whatever it showed.

Caveat. Both runs rebuilt the trend table from this laptop's raw files, which differ slightly from GitHub's (starters
out, snap shares), so the "before" records differ from the published ones; the
comparison is paired on the same inputs. The weekly run on GitHub will rebuild everything from the fixed code and set
the published numbers.
