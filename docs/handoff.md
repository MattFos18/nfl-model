# Handoff: everything a new Claude session should know

Written 1 Oct 2026 by the cloud session that built most of this repo (moving to a local session on Matt's laptop). Read
CLAUDE.md first; this file adds what is not written anywhere else. The record of every study is `reports/decision_log.md`
(newest first), the method of every piece is `docs/how_it_works.md`, the parked ideas are `docs/ideas.md`, and the
decisions waiting on Matt are `docs/todo.md`.

## Matt

- Runs this NFL betting model and its site. The goal is one thing: the highest win rate and the most units. Every idea is
  judged on that.
- Is also building a separate software startup, in its own local folder that he pushes to GitHub. A systems analyst (Ken)
  gave him Claude tools, agents and advice that he says made his other Claude much stronger. He is having that Claude
  package the tools, Ken's advice and the startup context for this project; when it arrives, read every file before
  using anything, and copy what helps into `.claude/` here.
- Writes fast on his phone with many typos: read for intent, never ask him to retype. He sends screenshots of bugs.
- Wants: very short answers, plain words, one recommendation (not a menu), a straight yes/no on whether something is
  proven. Says "you make the decisions" for building; still nothing in the live model or bet rules changes without his yes.
- Gets frustrated when he learns late that something was possible or blocked (he was not told early that full network
  access would unblock work). Tell him up front what a setting, tool or access would unlock, and name the exact setting.
- Asked for "no false claims, no false data, no hallucination": quote numbers only from a run you just did, and re-verify
  after any data fix (1 Oct: one bad forecast reading changed several quoted records; every place was corrected).
- Wants weather and other findings as points in the model, not just flags ("quantify the points"), and wants every
  finding visible in the Backtest tab and the records, not only in reports.
- Likes clean, colorful, easy-to-read tables and bars on the site; dislikes text, captions and clutter on cards.
- When he must do something himself (settings, installs), give numbered copy-paste steps, one command per line (he once
  pasted two commands onto one line). Better: do it for him when you can.
- Works mostly from the Claude app on his phone. His laptop is Windows on ARM (see Setup).

## How we work (what proved right)

- The adoption rule (reports/round3_rule.md, CLAUDE.md): better on all three windows, no bet cost, beats its own
  within-season shuffle, no market inputs, no look-ahead. Ideas found by looking at results become shadows, graded live.
- Matt asked whether leaning on betting markets (lines, splits, moves) as inputs would raise profits. The standing answer:
  never as model inputs (the model would become the line); test them only as separate rules once there is history
  (closing-line value and best-number shopping are parked in docs/todo.md until a season of our own logs exists).
- Every study: script in `experiments/`, report in `reports/`, a decision-log row, a docs paragraph. Then PR, wait for the
  `test` check, squash-merge, reset the branch to main, dispatch `weekly.yml`.
- After any change to the game model's totals or spreads: rerun `experiments.props_by_season` and update
  `props.BACKTEST` / `BACKTEST_COUNTS` from `reports/props_by_season.csv`, or the health check fails after the weekly run.
  Merge the latest main first: local runs reproduce GitHub's numbers exactly, but only on the same data.
- `nflmodel.report` rewrites the `<!-- auto:... -->` blocks in docs/how_it_works.md and the README; the weekly run does it.
- Health: `tie_check` (sources and page), `health_alert` (opens and closes `site-health` issues), `ready_checks` (opens
  `ready-check` issues when a shadow pulls clear), `picks_final` (opens a `picks-final` issue when a slate's injury
  reports are final). GitHub notifies Matt's phone for these.

## Done on 1 Oct 2026 (the last day of the cloud session)

- #360 ESPN injuries filled per player (four Thursday-night starters listed Out were not counted).
- #362 Wind under as a live bet (forecast wind 10+ mph, outdoor, weeks 1-17; GFS MOS plus Japan's model; 249-160 on
  2018-25); injury report shows each undecided player's "if out" effect and the worst-case swing bar.
- #363 Wind points in the model's total (about -2 points at 10-15 mph).
- #365 Weather retest (rain, cold, gusts as total points: all rejected) and a data fix: the MOS writes 99 for a missing
  wind hour; one 2018 game had a 20 mph forecast from it; masked and refetched.
- #366 Forecast rain in the totals equation (Matt's yes): it learned rain from the weather that happened but priced on
  the forecast; now it learns from the GFS MOS chance 50%+. Total miss better on all three windows, totals flag
  137-127 / 202-146 / 98-73, worth about -4.2 points on the card ("rain -X"). Backtest -> Totals has a "Weather in the
  Total" table. The weekly run after it passed every check (206 of 206).
- New today and logging, not priced: `nflmodel/inactives.py` (ESPN game-day inactive flags), `nflmodel/wind_live.py`
  (live wind and rain chance each line watch), `nflmodel/picks_final.py` (the picks-final alert).

## Waiting on Matt or on data

1. **Inactives pricing.** ESPN's game roster marks players "didNotPlay" before the official list (90 minutes before
   kickoff) and has been wrong (Joey Porter Jr., 1 Oct, practiced in full). Planned check tonight (PIT at CLE, ESPN event
   401872964, kickoff 8:15pm ET): compare the flags logged before 6:45pm ET in `data/lines/inactives_log.csv` with the
   official inactives. Price inactives only if the early flags prove reliable over a few game days; otherwise keep logging.
   The cloud session had this scheduled at 7:05pm ET; if that session is gone, do it here.
2. **Rain under as a hidden shadow** (blind under at a GFS rain chance 50%+, 102-60 on 2018-25). Superseded in part:
   rain is now points in the total, so the totals flag picks up most of those games (74-46 there). Recommended next step:
   re-test the blind rain under on top of the new model before asking Matt to add it as a shadow.
3. **Gusts.** The only gust forecast archive found so far is Open-Meteo's historical forecasts (about 2021 on); too
   short for the every-window rule, but worth one test. Matt wants to try his new tools first for more data.
4. **Snow and sleet.** About 16 games 2018-25 with a freezing forecast and a real precipitation chance: too few to prove
   anything. Not tested.
5. **Line moves and splits:** re-test once about nine weeks of our own logs exist. **Lineman quality:** re-test idea.
6. **docs/todo.md** decisions: public or private repo, buying historical splits or prop lines, coverage charting.
7. **Matt's toolkit package** from his other Claude (Ken's advice, tools, skills found online, the web scraper). Scrape
   only within a site's terms: no getting around blocks, and never sportsbooks (account and IP bans risk his bankroll).

## Known problems and quirks

- Issue #337 "Site checks failing" (30 Sep): the line watch closes it on its own when every check passes; the run
  after #366 passed 206 of 206, so it should close at the next line watch. Close it by hand if it lingers.
- Issue #193 "Weekly audit failing" (28 Sep): from the weekly audit (health.yml), about sub-view buttons that have since
  been fixed; it closes when the next audit passes, or close it by hand after checking reports/health.md.
- Branches: `claude/sharp-cray-vbvt7i` is the cloud session's branch, equal to main (safe to delete). `kick` is a
  trigger: lines.yml runs on a push to it (an old workaround for GitHub's cron; heartbeat.yml now kicks the line watch).
  Deleting it is harmless; keeping it is too.
- Workflow files: the cloud session's permissions blocked edits to `.github/workflows`. Locally they work once Matt ran
  `gh auth refresh -s workflow`.
- Forecast range: the live wind and rain readings start about 66 hours before kickoff, so Sunday games get them from
  Friday evening; until then those games are priced without weather points.
- The backtest's other weather inputs (wind_out, cold, and the points equations' rain) read the weather that happened for
  past games, a small look-ahead in the backtest only; the totals' rain and the wind points use forecasts.
- Open-Meteo rate-limits (HTTP 429) when hit hard; one 2026 game's Japan-model wind is missing for that reason.
- The props round tie check allows 0.15 yards: the game-model gains since the rounds moved passing by about 0.1.

## Setup on Matt's laptop

- Windows on ARM. pyarrow has no Windows ARM build, so the repo runs in `.venv` made with Python 3.12 x64 (installed with
  winget; it runs under emulation). Use `.venv\Scripts\python.exe`. pytest is installed in the venv (not in
  requirements.txt). All 20 tests pass.
- The repo is at `C:\Users\mfosc\nfl-model`. The empty folder `C:\Users\mfosc\NFL Model` is not the repo.
- CLAUDE.md's Playwright path (`/opt/pw-browsers/chromium`) is the cloud container's; locally install a browser with
  `npx playwright install chromium` and drop the executablePath.
- `ODDS_API_KEY` must be set as a user environment variable for live lines when run locally (GitHub Actions has it as a
  secret).
