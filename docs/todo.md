# Matt's list (kept up to date by Claude)

Last updated 29 Sep 2026.

## Decisions for Matt, when ready
- **Private or public.** Staying public for now. Going private means Actions minutes count against a plan. Options: run the line watch every 30 to 60 minutes on weekdays (every 10 on game days) and pay for extra minutes; or run the jobs on your own always-on computer (free); plus a Cloudflare login in front of the site.
- **Buy historical betting splits** (Action Network / Bet Labs, SportsDataIO). The live splits are logged every 10 minutes from 29 Sep 2026 (`data/lines/splits_log.csv`); past seasons let us test them now. Matt, 29 Sep: build nothing on splits and highlight nothing (no shadow rule, no flags) until a bought history or a season of our own log can be tested.
- **Buy historical player prop lines** (The Odds API historical). Every props idea could then be judged on real bets from 2019 to 2025, not one week.
- **Coverage and alignment charting** (Sports Info Solutions DataHub, or PFF). The only honest way to test receiver against corner.
- **Workflow file edits.** Claude's permissions block edits to `.github/workflows`. Changing the line watch schedule, or anything in a workflow, needs you to paste the change or allow it.

## Claude is working on
- Game situation study: coaches, stadiums, travel, time zones, turf, primetime and kickoff time, referees, weather and injuries crossed with everything, coordinator and scheme matchups. Anything that passes the round-3 rule gets built in and retested together.
- The 13 small player-prop gains that passed (cold rushing yards, teammates out, rest days, corners faced, touchdown chances): build in with the game study's passers.
- Season totals wild-card fix: 2016-20 totals counted a playoff game. Retest the fitted settings on corrected totals.
- Weather on forecasts: day-before forecasts exist from about 2022 on; retest the weather effects on what was knowable before kickoff.
- Coordinators: 2013-2025 table from Wikipedia (2026 staff lists not up yet; play-callers are in no free source). Then test offensive against defensive coordinator.

## Ideas parked, to revisit
- **A look of its own** (Matt, 29 Sep: keep the simple, easy-to-read layout, but it reads as Claude-made). The cream background, muted greens, rounded pale cards and the IBM Plex type are the tell. Options: a darker sports-data palette (near-black or navy with one team-agnostic accent), a sharper sans such as Inter or Barlow with condensed numerals, square-edged tiles, a proper header with a logo and name. Same layout, new skin; one pass, shown to Matt before it goes live.
- Expected return (EV %) column on the Bet ranking, and the median total on each card.
- Track the Under 3+ totals rule live before using it.
- The boosted trees' own summed total as a totals lead (60.9% / 58.1% / 53.8%, one of about 45 rows tried; watch, not an edge).
- A listed starting QB on the injury report or a reserve list: flag it by eye.

## Done today
- Health failures fixed (stale data copy), and the old cache entry deleted.
- Model tab shows the seven models and the total model.
- Win, loss and push marks removed from Picks and the cards.
- Live betting splits (bets and money) on every Breakdown card, every 10 minutes.
