# Data sources

One section per outside source the repo reads. Every claim cites the code or report it comes from. "Terms" is what we
know about the source's license or terms of use; "unverified" means nobody here has read them, so check before showing
that source's raw data publicly or leaning on it harder. The list of stores each source fills is `nflmodel/catalog.py`.

When you add a source: add a section here (same headings), a row in `catalog.py`, and a line in `log.md`.

---

## nflverse (schedules, play-by-play, injuries, rosters, depth charts, snaps, charting)

- **What we use:** schedules (every game 1999 on: kickoff, teams, scores, closing `spread_line` / `total_line`,
  moneylines, roof, surface, recorded temp and wind, named QBs, coaches, referee); play-by-play with EPA; the league's
  injury reports; weekly rosters (status, ids); depth charts; snap counts; the players id table; FTN charting (2022 on);
  participation (2016 on); official player stats; PFR advanced stats by week. Full list: `catalog.RAW_WHAT`.
- **Where:** downloaded by `nflmodel/pull.py` from `github.com/nflverse/nflverse-data/releases` into `data/raw/`
  (git-ignored); built into `data/processed/games.parquet`, `team_games.parquet` and the rest by `build.py`,
  `features.py`, `players.py`, `scheme.py`.
- **Timing / lag:** play-by-play, stats, snaps and charting arrive hours to a day after games; the picks week does not
  advance until every source has the last game (`lines.current_week`, `week_complete`; weekly.yml retries Tuesday and
  Wednesday). Injury reports lag the league's own by hours to a day (decision log 23 Sep 2026; `pull.espn_injuries`
  docstring). Participation for 2026 was not published yet (`catalog.RAW_WHAT["participation"]`).
- **Terms:** nflverse data is CC-BY 4.0 (attribution); FTN charting is CC-BY-SA 4.0, credit "FTN Data via nflverse"
  (nflreadr docs, https://nflreadr.nflverse.com/). The closing lines and recorded weather in schedules trace back to
  Pro-Football-Reference, and the `pfr_*` files are PFR's numbers; PFR's terms bar scraping and AI use
  (https://www.sports-reference.com/termsofuse.html). Whether republishing numbers derived from those PFR-sourced columns
  is fine: unverified, an open question for Matt.
- **Quirks:** `spread_line` positive = home favored. `temp` / `wind` are the weather that happened, not a forecast.
  Starting QBs are named only for played games and the coming week, and the coming week's name comes before injury news.
  Rosters carry no PFR id for offensive linemen. International games can carry the home team's own stadium and the
  wrong roof. Team codes changed (OAK/LV, SD/LAC, STL/LA; `players.load_injuries`). All in `gotchas.md`.

## ESPN (scoreboard, injuries, summaries, game rosters, futures, logos)

- **What we use:** the scoreboard's provider line per game (`lines._parse_espn`); the injury page for every team
  (`pull.espn_injuries` -> `data/raw/injuries/espn_injuries.csv`); each athlete's injury record for reserve-list reasons
  (`pull.reserve_reasons`); game summaries and play-by-play for the Live tab (`results.py`); game rosters' did-not-play
  flags (`inactives.py`, logged, not priced); season futures (`futures.py`); team logos (`logos.py`).
- **Hosts:** `site.api.espn.com`, `site.web.api.espn.com`, `cdn.espn.com`, `sports.core.api.espn.com`, tried in turn
  with browser headers (`lines._get_json`, `lines.H`).
- **Timing:** statuses post the same day as the team's report, ahead of nflverse; the fill is used only when the page
  was fetched within 4 days (`players.ESPN_MAX_AGE_DAYS`) and only for players the league file has no status for.
  Inactives flags appear before the official list (90 minutes before kickoff) and have been wrong (Joey Porter Jr.,
  1 Oct 2026; `inactives.py` docstring, `docs/handoff.md`).
- **Terms:** undocumented, unofficial endpoints; ESPN's terms of use: unverified.
- **Quirks:** the first runner pull got a 403 from `site.api` until browser headers and three hosts were used (decision
  log 23 Sep 2026). ESPN's `spread` is the home handicap (positive = home underdog), flipped to nflverse's sign at
  `lines.py` line ~120. Team names are full names, mapped to codes (`lines.team_from_name`, `ESPN_ABBR`).

## Action Network (every book's number)

- **What we use:** the public scoreboard API: each book's spread, total and moneyline with prices, plus its "Open" and
  "Consensus" rows (`market_logs.books` -> `data/lines/books_log.csv`, a row only when a number changes). Display and
  study only: the cards' consensus line chart (`export_web._add_consensus`); never a model input.
- **Where:** `nflmodel/market_logs.py` (`api.actionnetwork.com/web/v1`), called from the line watch.
- **Timing:** every line watch (`lines.yml`, every 30 minutes when GitHub honors it, plus the hourly `kick` push).
- **Terms:** unverified. Its own bet and money shares need a paid login and are not read (`market_logs.py` docstring).
- **Quirks:** `home_spread` in `books_log.csv` is Action Network's own sign (home handicap), the opposite of nflverse's;
  it is flipped only when exported (`export_web._add_consensus`, `pt()`). See `gotchas.md`.

## ScoresAndOdds (consensus splits)

- **What we use:** the consensus picks page: % of bets and % of money per side of the spread, total and moneyline,
  across its partner books (`market_logs.parse_sao` -> `data/lines/splits_consensus_log.csv`). Display only; replaces
  DraftKings' splits on a card when present (`export_web._add_consensus`).
- **Where:** `nflmodel/market_logs.py` (`www.scoresandodds.com/nfl/consensus-picks`), parsed from HTML.
- **Timing:** every line watch; a row only when a game's split changes.
- **Terms:** unverified.
- **Quirks:** HTML parsing by regex on CSS class names (`parse_sao`); a page redesign silently yields zero rows, so a
  run with no rows should be treated as a failure, not "no splits". Matt, 29 Sep 2026: build nothing on splits until a
  bought history or a season of our own log exists (`docs/todo.md`).

## DraftKings (splits page; retired sportsbook feed)

- **What we use:** DraftKings Network's public betting-splits page (share of tickets and handle per side), every line
  watch (`splits.py` -> `data/lines/splits_log.csv`, `splits_latest.csv`). Display only.
- **Retired 24 Sep 2026:** DraftKings' sportsbook event-group feed (403 on 61 of 62 runs) and the Covers splits page
  (no percentages on 59 of 62 runs). The functions stay in `lines.py` for the record; the run does not call them
  (`lines.py` docstring).
- **Terms:** the sportsbook's terms bar automated access
  (https://sportsbook.draftkings.com/legal/us-terms-of-use); do not revive the sportsbook feed. The DK Network media
  page's terms: unverified. Never scrape a sportsbook (account and IP bans risk Matt's bankroll; `docs/handoff.md`).
- **Quirks:** the page is server-rendered HTML keyed on team nicknames (`splits.NICK`).

## The Odds API

- **What we use:** every US book's spread, total and moneyline (`lines.py`, `odds_api_due`: about once a day, no second
  pull inside 12 hours); player prop lines twice a week (`props_lines.py`); outrights (`futures.py`); historical props
  (`props_history.py`, `props_history.yml`).
- **Key:** `ODDS_API_KEY`, a GitHub Actions secret and a user environment variable on the laptop; the pull is skipped
  without it (`lines.py` ~line 188).
- **Budget:** free tier, 500 credits a month, shared by lines and props (`lines.py` docstring; decision log 22 Sep 2026).
- **Terms:** whether its odds may be shown on a public site: unverified. Historical data needs a paid plan.

## Open-Meteo (kickoff forecasts, archives, Japan's model)

- **What we use:** (1) the kickoff-hour forecast for every unplayed outdoor game in the next 10 days (`weather.py` ->
  `data/weather/forecast_latest.csv`, `forecast_log.csv`); (2) the historical weather archive at kickoff
  (`weather_archive.py`, `weather_archive.yml`); (3) the previous-runs archive (`forecast_archive.py`); (4) Japan's
  global model (`jma_gsm`, the one it keeps back to 2018, wind only) for the wind under, both history
  (`forecast_history.py`) and live (`wind_live.py`).
- **Timing:** live forecasts within 10 days; the wind-under reading only within 66 hours (`wind_live.RANGE_H`).
- **Terms:** the free API is non-commercial only, under 10,000 calls a day, data CC-BY 4.0
  (https://open-meteo.com/en/terms). If the site ever carries ads or charges, a paid plan is needed.
- **Quirks:** rate-limits with HTTP 429 when hit hard (one 2026 game's Japan-model wind is missing for that reason;
  `docs/handoff.md`). A failed fetch is a row with `status = error:...`, not a crash (`weather.run`). A game keeps its
  last good reading after kickoff (`status = carried`) until scored (decision log 27 Sep 2026).

## NWS GFS MOS (via Iowa Environmental Mesonet)

- **What we use:** model output statistics at the stadium's airport: GFS MOS wind, temperature and 6/12-hour rain
  chance, and the National Blend (NBS) wind and gust from 7 Nov 2018 (`forecast_history.py`, `MOS` =
  `mesonet.agron.iastate.edu/api/1/mos.json`). History 2018-2025 in `data/weather/forecast_history.csv`; live readings
  in `data/weather/wind_live.csv` (`wind_live.py`). Feeds the wind under (`picks.WIND_UNDER`), the wind points
  (`model.wind_points`) and the rain input of the totals equation (`model.RAIN_FC`).
- **Timing:** GFS MOS runs out 72 hours; the live reading uses the newest run issued at least 4 hours ago and at least
  5 hours before kickoff (`wind_live.py` docstring). Sunday games get a reading from Friday evening.
- **Terms:** NWS products, served by Iowa State's mesonet; IEM's terms: unverified.
- **Quirks:** MOS writes 99 for a missing wind or gust hour and 999 for a missing temperature; masked in
  `forecast_history.py` (~line 95). Values are knots, converted to mph. US stadiums only: no reading abroad.

## Others (smaller)

| Source | Use | Code | Terms |
|---|---|---|---|
| Sleeper player file | injury body part for reserve-list players, at most every 12 hours | `pull.reserve_reasons` | unverified; Sleeper asks for about one pull a day |
| PrizePicks, Underdog | player prop lines beside the projections | `props_lines.py` | unverified |
| Wikipedia API | coordinators by season | `coordinators.py` | CC BY-SA (Wikipedia's text license) |
| PFF, ESPN, FOX, SI ranking pages | consensus position rankings for player-value checks; HTML kept local, not republished | `reference.py`, `.gitignore` | each publisher's; not republished |
| sportsoddshistory.com | past win totals | `reference.py` | unverified |
