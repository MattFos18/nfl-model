# Gotchas

Traps this repo has already hit, each with where it lives. Read at the start of every session. When a new one bites,
add it here (newest at the top of its group) with the file and the date, and a line in `log.md`. The check that catches
each one again is in `checks.md`.

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
  most-used QB this season); `tests/test_qb_out_swap.py`.
- **A failed injury load priced every ruled-out starter silently.** `ratings.qbs_out_now` returned "nobody out" on any
  exception. Fixed 2 Oct 2026: only a missing league injury file is quiet; any other error (or ESPN's page not merging,
  `players.ESPN_MERGE`) warns, goes to `data/runs/qb_swaps.json` and fails the ratings step and a health row.
- **ESPN and the roster disagree on suffixes** ("Travis Etienne Jr." against "Travis Etienne"): four Out players went
  uncounted. Match names with `players.name_key` (suffixes and punctuation dropped); nicknames (Rob/Robert) still miss
  and show as a health warning (2 Oct 2026).
- **A failed model step still picked and recorded bets** from the previous run's predictions. `weekly.pick_week` skips
  picks, log run, record picks and the fingerprint when the model step failed (2 Oct 2026).
- **`roster_now` is the previous run's depth chart** (ratings runs before positions in `weekly.py`). A backup released or
  inactive since could have been priced; `ratings.replacement_qb` now requires ACT on the weekly roster (2 Oct 2026).
- **After a QB swap the card showed the starter ruled out**: the backup has no schedule name and the schedule's starter
  overrode the blank. `export_web.card_qb` names the QB priced from `qb_swap_from`; the tie check compares (2 Oct 2026).
- **Starters are named only for played games and the coming week.** Later weeks fell to the replacement-level QB prior
  and dragged every team's power down; the last starter is carried forward (decision log 22 Sep 2026).
- **ESPN's injury statuses lead the league report (nflverse) by hours to a day.** `players.load_injuries` fills, player
  by player, every player the league file has no game status for this week; the league's status wins where it has one;
  ESPN pages older than 4 days, or fetched before the week before's last kickoff, are ignored (`players.espn_fresh`;
  until 2 Oct 2026 the age limit alone let last Sunday's statuses count for the new week at the Tuesday week change). Before 1 Oct 2026 (#360) it filled only teams with no league file at all,
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
  fit does; games abroad have no stored forecast and keep it (2015-17 too until 2 Oct 2026, reports/forecast_history_2015.md) (reports/forecast_weather_backtest.md). A new
  weather input must be learned from the forecast it will be priced on, and priced through `priced_weather`.
- **Live games were priced on a different forecast than the backtest.** Until 2 Oct 2026 an unplayed game's wind_out,
  cold and points-equation rain came from Open-Meteo (`weather.apply_to_games`, trends rain) while the backtest priced on
  GFS MOS / Japan (DAL@HOU 9.9 against 11.4 mph). Now `weather.live_source` gives both the MOS reading wind_live keeps,
  Open-Meteo only where none exists yet (66 to 96 hours out, or a failed pull: a `live weather` warning and a health
  row). The props still read Open-Meteo (`apply_to_games(mos=False)`). Follow-ups the same day: a reading whose GFS run
  is more than one run behind the newest for that game is dropped (`wind_live._fresh`, `MAX_RUN_LAG_H`); health fails a
  US outdoor game within `wind_live.DUE_H` (59) hours with no MOS reading (from 66 to 59 hours out the newest run may
  not reach the game yet); a source change re-prices (`refresh.diff`).
- **Before Nov 2018 the wind reading is fewer models.** The stored reading is the mean of the pre-kickoff forecasts that exist (`forecast_history.PRE_KICKOFF_WIND`): GFS alone for 2015's regular season (Open-Meteo's Japan archive starts 1 Jan 2016), GFS and Japan for 2016 to Nov 2018 (NBS starts 7 Nov 2018), all three after. Live does the same when a source is missing. The stored forecasts also train the rain input and the wind points' pool, so extending the history moves the live total (reports/forecast_history_2015.md).
- **The forecast history skips games by the roof as it was on game day** (unverified size; audit of 2 Oct 2026,
  reports/audit_forecast_weather_backtest_2026-10-02.md): 295 closed-roof games at ARI, ATL, DAL, HOU and IND have no
  stored forecast, while a live run sees their roof as unknown and prices them as outdoor, so the weather backtests skip games live bets could
  include.
- **A season's league average includes its later weeks.** `players.opponent_strength` centred each defense on the
  full season's mean (later weeks in). Now `players.league_mean_before` (weeks before; week 1 uses the season before).
  It feeds only the Players tab's EPA against an average defense, not the game model or the props (2 Oct 2026).
- **A prior built from team-game rows can count the same game.** `trends._prior_mean` walked rows in order, so the home
  row's referee prior counted the away row of the same game, that game's own total. Fixed 2 Oct 2026 (#384): a prior
  counts only games that kicked off strictly before this one (`reports/leak_fix_rescore.md`).
- **Japan's newest model run is after kickoff for a played game.** `jma_wind_d0` for 2018-2025 is a run issued at or
  after kickoff; the backtest reads the day-before run (`jma_wind_d1`, `forecast_history.PRE_KICKOFF_WIND`). Fixed
  2 Oct 2026 (#384).
- **A game kept its forecast only until kickoff.** On 27 Sep 2026 the 1pm games were re-priced as typical weather
  after kickoff ("Weather TBD"). Fixed: `weather.py` reaches back a day and carries the last good reading
  (`status = carried`).
- **Weather fallbacks were silent.** A MOS pull with no rain or temperature kept an older reading, the wind mean became
  one model, a games-table failure let games abroad back into the stored forecasts, and `model.py`'s readers priced
  games calm on any error. Each still falls back but calls `warnlog.warn` (stderr plus a health warning,
  `data/weather/warnings.json`); use it for any new fallback (2 Oct 2026).
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

- **The picks week can move partway through a weekly run (6 Oct 2026).** `lines.current_week` advances only once last
  week's games are in `player_games` and `scheme_plays`, written by the players and scheme steps; ratings and trends ran
  before them on the old week, so week 5 was priced with no injuries and ruled-out QBs counted as playing.
  `weekly.rerun_if_week_moved` runs the input steps again when the week moves.
- **Fresh tree fits differ run to run on one machine too.** A new input set has no stored fits, so the trees are fit
  fresh: the same seven-input drop run twice locally (input_ablation's combined run, drop_seven_inputs) moved 1,016 games' trees by up to
  1.0 point (one spread-flag bet on 2015-18); the ridge members and the total were identical. Compare a change only against a baseline
  from the same run, and expect GitHub's first refit to move the published records a bet or so (3 Oct 2026, reports/drop_seven_inputs.md).
- **qb_out, dome, rain, neutral and div_game are readings, not points-equation inputs, since 3 Oct 2026.** Code that reads
  `coef_qb_out` (or any of them) from pred_v3 gets nothing for new rows; read `model.FEATS`, never a fixed list (`export_web`, `tie_check`).

- **Log csvs appended by position.** `data/runs/rule_history.csv` wrote its header once, so a new or dropped `*_bet`
  rule column would have shifted every later row. Appends now go through `picks.append_csv` (by column name; a new
  column widens the header). Use it for any new appended log (2 Oct 2026).

- **The boosted trees gave different numbers on different runners** (thread order and hardware rounding). Fixed by
  one thread and a cache of every fit keyed by its inputs (`model.trees_key`, `data/processed/trees_cache.parquet`;
  decision log 27-28 Sep 2026). A tie fails when past seasons' numbers move with no code change. Any check, test or
  experiment that calls `walk_forward` must run inside `with M.trees_cache_read_only():` (until 2 Oct 2026 the leak
  checks and the planted-leak test rewrote the tracked cache to 2024's 71 keys).
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
- **Retractable roofs are blank until game day.** The schedule leaves an unplayed retractable-roof game's roof empty; it read as outdoors and the wind under fired on 2026_04_DAL_HOU. Unplayed games at ATL, DAL, HOU, IND, ARI (and the Bernabeu) with no roof count as closed (`nflmodel/build.py` RETRACTABLE_HOME; `wind_live._roofed`).
- **A try/except around an alert hides a NameError.** `health_alert.main()` wraps each alert in `except Exception` so it never fails the run; when #343 deleted `_sync_issue`, the call raised NameError, got printed and swallowed, and alerts were dead for three days. Any function called inside such a guard needs a test that calls `main()` (`tests/test_health_alert_sync.py`).
- **The schedule's named starter can be stale.** nflverse named Drew Lock (a week-2 fill-in) as SEA's week-4 starter after Sam Darnold had come back in week 3. `ratings.check_named` now prices the regular starter when he is not ruled out; a fill-in is a start made while the regular was Out/Doubtful on the league's report.
