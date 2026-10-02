# Gotchas

Traps this repo has already hit, each with where it lives. Read at the start of every session. When a new one bites,
add it here (newest at the top of its group) with the file and the date, and a line in `log.md`.

## Signs and ids

- **`spread_line` positive = home favored.** nflverse's sign, and every `home_spread` in our logs uses it
  (`lines.py` ~line 120, `build.py` `home_implied = (total_line + spread_line) / 2`, `clv.side_handicap`). The home
  side's handicap is `-home_spread`. Most books and sites print the opposite (home -3.5).
- **Action Network's spread sign is the opposite of nflverse's.** `data/lines/books_log.csv` stores Action Network's
  own `home_spread` (home handicap, home favored < 0); it is flipped only when exported to the cards
  (`export_web._add_consensus`, `pt()`). Anything new that reads `books_log.csv` must flip it too.
- **ESPN's `spread` is the home handicap (positive = home underdog).** Flipped in `lines._parse_espn`; the text form
  ("KC -3.5") is parsed separately. Checked 21 Sep 2026.
- **Join players by id, never by name.** The rosters carry no PFR id for offensive linemen, so until 24 Sep 2026
  linemen were matched by name: 579 games went to a namesake and 1,411 were dropped (decision log 24 Sep 2026). One
  map now: `ids.pfr_ids()` (PFR id -> gsis id; six conflicts such as two Jonah Williamses settled by name).
- **Team codes moved.** OAK -> LV, SD -> LAC, STL -> LA in nflverse files (`players.load_injuries`); ESPN uses WSH, JAC,
  LAR (`lines.ESPN_ABBR`).

## Timing and look-ahead

- **nflverse names the coming week's starting QB before the injury news.** The WAS card priced Jayden Daniels after
  ESPN ruled him Out and flagged WAS +3.5 on his rating. Fixed 2 Oct 2026 (#376): `ratings.qbs_out_now` swaps a named
  starter who is Out, Doubtful or off the active roster for `ratings.replacement_qb` (next on the depth chart, else the
  most-used QB this season); `tests/test_qb_out_swap.py`. Note `qbs_out_now` returns "nobody out" on any exception, so
  missing injury data silently prices the named starter.
- **Starters are named only for played games and the coming week.** Later weeks fell to the replacement-level QB prior
  and dragged every team's power down; the last starter is carried forward (decision log 22 Sep 2026).
- **ESPN's injury statuses lead the league report (nflverse) by hours to a day.** `players.load_injuries` fills, player
  by player, every player the league file has no game status for this week; the league's status wins where it has one;
  ESPN pages older than 4 days are ignored. Before 1 Oct 2026 (#360) it filled only teams with no league file at all,
  so four PIT and CLE starters listed Out on ESPN were not counted.
- **ESPN's inactives flag shows up before the official list and can be wrong** (Joey Porter Jr., 1 Oct 2026, practiced
  in full). `inactives.py` logs it; nothing prices it yet (`docs/handoff.md`).
- **The lines log keeps pulling after kickoff (live lines).** Any closing line, CLV or "line at bet time" must take the
  last snapshot strictly before kickoff, as `clv.py` does and `lines.live_lines` does through `lines.before_kickoff` (2 Oct 2026:
  a snapshot 1m41s after kickoff had become 2026_03_LA_DEN's line). Log timestamps are UTC (`2026-10-02T14-20-00Z`); `kickoff_et`
  in `games.parquet` is Eastern with no zone. Convert before comparing.
- **Recorded weather is not a forecast.** The schedule's `temp` and `wind` and the play-by-play's rain are the weather
  that happened. Until 2 Oct 2026 the backtest priced played games with them (a look-ahead the live run never has).
  Fixed: `model.priced_weather` (called by `walk_forward` and by `export_web` for the inputs the page shows) prices a
  played game with a stored forecast (2018 on) on that forecast: `wind_out` from `wind_live.readings`, cold from
  `gfs_temp`, the points equations' rain from the `RAIN_FC` reading. Training rows keep the recorded weather, as a live
  fit does; 2015-17 and games abroad have no stored forecast and keep it (reports/forecast_weather_backtest.md). Still
  different: an unplayed game's points-equation wind, cold and rain come from Open-Meteo's kickoff hour
  (`weather.apply_to_games`, trends rain), which is not stored for 2018-25. A new weather input must be learned from the
  forecast it will be priced on, and priced through `priced_weather`.
- **The forecast history skips games by the roof as it was on game day** (unverified size; audit of 2 Oct 2026,
  reports/audit_forecast_weather_backtest_2026-10-02.md): 295 closed-roof games at ARI, ATL, DAL, HOU and IND have no
  stored forecast, while a live run sees their roof as unknown and prices them as outdoor, so the weather backtests skip games live bets could
  include.
- **A prior built from team-game rows can count the same game.** `trends._prior_mean` walked rows in order, so the home
  row's referee prior counted the away row of the same game, that game's own total. Fixed 2 Oct 2026 (#384): a prior
  counts only games that kicked off strictly before this one (`reports/leak_fix_rescore.md`).
- **Japan's newest model run is after kickoff for a played game.** `jma_wind_d0` for 2018-2025 is a run issued at or
  after kickoff; the backtest reads the day-before run (`jma_wind_d1`, `forecast_history.PRE_KICKOFF_WIND`). Fixed
  2 Oct 2026 (#384).
- **A game kept its forecast only until kickoff.** On 27 Sep 2026 the 1pm games were re-priced as typical weather
  after kickoff ("Weather TBD"). Fixed: `weather.py` reaches back a day and carries the last good reading
  (`status = carried`).
- **The live wind and rain readings start about 66 hours before kickoff** (`wind_live.RANGE_H`): Sunday games get them
  from Friday evening; until then they are priced without weather points.
- **Old injury reasons leaked onto the page.** Reserve-list players showed last season's reason ("Teeth"); reasons now
  come from this season only, and a tie check fails if an older one reaches the page (decision log 26 Sep 2026).

## Data values

- **NWS MOS writes 99 for a missing wind or gust hour (999 for temperature).** 2018_16_BAL_LAC had a 20 mph forecast
  built from it; masked in `forecast_history.py` (~line 95) and refetched (7.4 / 5.5 mph). Every number quoted from
  before the fix was redone (decision log 1 Oct 2026). Check any new weather feed for sentinel values.
- **The schedule's venue and roof can be wrong, and stadium names never carry the city.** The 2025 games abroad were listed at the home team's US stadium (2025_01_KC_LAC "SoFi Stadium" dome, 2025_10_ATL_IND "Lucas Oil" closed, London at TIAA Bank, Madrid at Hard Rock) and 2026 Melbourne, Paris and Munich as domes; the old lookup matched city names ("London") against stadium names ("Wembley") and fell back to the home team's stadium, so London games and Oakland's and San Diego's read the wrong place. Fixed 2 Oct 2026: `nflmodel/venues.py` places games by `stadium_id` with a `GAME_VENUE` override table, every weather reader uses `venues.site`, and `data_checks` fails a neutral game at a home stadium or an open-air stadium abroad marked dome. A new game abroad needs its stadium in `venues.VENUE`.
- **nflverse's listed starting QB can be a QB who never played** (44 team-games 2022-2025: Mariota for WAS Weeks 9-13 2024, Hurts in 2024_17_DAL_PHI). Fixed 2 Oct 2026 in `build.fix_starters` (played games only; the id nflverse gave is `*_qb_id_listed`); `data_checks` fails a played game's starter with no dropback.
- **The schedule's recorded wind has typos** (71 mph at Pittsburgh, 44 at Philadelphia). `build.fix_wind` checks it against the Open-Meteo archive and the GFS forecast (2 Oct 2026); the schedule's figure is `wind_listed`.
- **The listed home team gets the full home edge at neutral and international sites** (decision log 30 Sep 2026,
  `experiments/home_field.py`); zeroing it helped 2015-22 and hurt 2023-25, so it stays.
- **Defenders who changed teams had a snap share of 0** (divided by the new team's snaps in games he did not play;
  Myles Garrett among 99). Fixed with a tie check (decision log 24 Sep 2026).
- **The opener archive has 23 bad rows** that inflate the Opener Study (decision log 30 Sep 2026, bet rules sweep).
- **One cancelled game.** BUF-CIN (2 Jan 2023) was never replayed: both teams have 16 games in 2022
  (`data_checks.SHORT`).
- **"Probable" existed until 2016.** Questionable players sat 39-44% of the time before, 26-36% after (decision log
  1 Oct 2026, injury retest). Do not pool injury rates across 2016.

## Runs and machines

- **The boosted trees gave different numbers on different runners** (thread order and hardware rounding). Fixed by
  one thread and a cache of every fit keyed by its inputs (`model.trees_key`, `data/processed/trees_cache.parquet`;
  decision log 27-28 Sep 2026). A tie fails when past seasons' numbers move with no code change.
- **The line watch runs every 30 minutes, not 10.** `lines.yml` cron is `*/30` (GitHub never started a `*/10`), backed
  by `heartbeat.yml` and an hourly push to the `kick` branch (`catalog.LOG_WHAT` said "every 10 minutes" until 2 Oct 2026).
- **Generated files fight merges.** Weekly runs commit `data/`, `web/data/` and reports; never commit them from a
  branch (`git checkout -q -- reports/ web/data/ data/`). The workflows rebase with `-X theirs` (decision log
  23 Sep 2026).
- **Matt's laptop:** Windows on ARM; Python 3.12 x64 in `.venv` (no pyarrow for ARM); set `PYTHONUTF8=1` or files read
  as cp1252; raw player files are not local, so use `export_web --week`, and the tie check's "season file" and
  "backtests re-run" rows fail locally for that reason (`docs/handoff.md`).
- **The raw-data cache had one fixed key** and kept restoring an old copy without the players table (decision log
  26 Sep 2026); each weekly run now saves its own copy.
