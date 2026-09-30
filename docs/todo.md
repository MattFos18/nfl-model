# Matt's list (kept up to date by Claude)

Last updated 29 Sep 2026.

## Decisions for Matt, when ready
- **Private or public.** Staying public for now. Going private means Actions minutes count against a plan. Options: run the line watch every 30 to 60 minutes on weekdays (every 10 on game days) and pay for extra minutes; or run the jobs on your own always-on computer (free); plus a Cloudflare login in front of the site.
- **Buy historical betting splits** (Action Network / Bet Labs, SportsDataIO). The live splits are logged every 10 minutes from 29 Sep 2026 (`data/lines/splits_log.csv`); past seasons let us test them now. Matt, 29 Sep: build nothing on splits and highlight nothing (no shadow rule, no flags) until a bought history or a season of our own log can be tested.
- **Buy historical player prop lines** (The Odds API historical). Every props idea could then be judged on real bets from 2019 to 2025, not one week.
- **Coverage and alignment charting** (Sports Info Solutions DataHub, or PFF). The only honest way to test receiver against corner.
- **Workflow file edits.** Claude's permissions block edits to `.github/workflows`. Changing the line watch schedule, or anything in a workflow, needs you to paste the change or allow it.

## Claude is working on
- Weather on forecasts: day-before forecasts from 2022 on. Weeks 1-6 of 2022-25 are stored; weeks 7 on are being fetched. Then retest the weather effects on what was knowable before kickoff.

## Where every finding and every piece of data lives
- **Findings:** each study's full table in `reports/` (CSV beside a Markdown write-up), a paragraph per study in `docs/how_it_works.md`, and on the site under Info → Game model → Tested and not used (Round 3 has its own section).
  - Game situations (121 ideas, nothing adopted): `reports/situational_game.*`; every shuffle draw in `reports/situational_game_placebo.csv`.
  - Player props (1,235 tests, 14 pass): `reports/situational_props.*`.
  - Season totals linked to the team (nothing adopted): `reports/player_season_link2.*`.
  - The rule every change is judged by: `reports/round3_rule.md`.
- **Data:** every file is listed on the site under Info → Data with what it is, what writes it and where it shows. New this round: `data/lines/splits_log.csv` (betting splits every 10 minutes), `data/reference/coordinators.csv`, `data/weather/forecast_archive*.csv`.

## Ideas parked, to revisit
- **A look of its own** (Matt, 29 Sep: keep the simple, easy-to-read layout, but it reads as Claude-made). The cream background, muted greens, rounded pale cards and the IBM Plex type are the tell. Options: a darker sports-data palette (near-black or navy with one team-agnostic accent), a sharper sans such as Inter or Barlow with condensed numerals, square-edged tiles, a proper header with a logo and name. Same layout, new skin; one pass, shown to Matt before it goes live.
- Expected return (EV %) column on the Bet ranking, and the median total on each card.
- Track the Under 3+ totals rule live before using it.
- The boosted trees' own summed total as a totals lead (60.9% / 58.1% / 53.8%, one of about 45 rows tried; watch, not an edge).
- A listed starting QB on the injury report or a reserve list: flag it by eye.

## Done today
- The small player-prop gains that passed are built in (receptions, targets, rushing yards, touchdown lines): each stat a hair more accurate on every window; the capped target shares left out.
- Season totals wild-card fix: 2016-20 totals had counted a playoff game. Corrected; the receiving availability share refit to 0.675 (better on every window).
- Game situation study finished: 121 ideas, coach vs coach, stadiums, travel, turf, primetime, referees, weather, injuries, coordinators. None passed; the closest (turf) did no better than luck.
- Every round-3 finding on the site (Info → Game model → Tested and not used → Round 3).
- Health failures fixed (stale data copy), and the old cache entry deleted.
- Model tab shows the seven models and the total model.
- Win, loss and push marks removed from Picks and the cards.
- Live betting splits (bets and money) on every Breakdown card, every 10 minutes.
