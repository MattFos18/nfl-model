# Hardening plan (3 Oct 2026)

Goal: a professional-grade, foolproof system before any fund work. Built from six reviews on 3 Oct: code, data
pipeline, operations and security, how quant funds and betting syndicates build their tech, how pros run live models,
and a fact-check of the earlier research. Fund, legal and investor tooling come last.

**Bottom line.** The research side already matches or beats common pro practice (written adoption rule, held-out
window, placebo, shadows graded live, tie check, leak tests, drift monitor). The weak side is the plumbing: the
pipeline keeps going when a step fails, some failures turn into plausible-looking numbers, data lives in git, and
package versions aren't pinned. The big-firm tools (kdb+, Airflow, Kubernetes, MLflow, Great Expectations) are
overkill at our size; the right tools for us are free.

Done already: the site-health alert had been silently dead since 30 Sep (#421, fixed and tested).

Note (5 Oct): the six research reports behind this plan (code, data, ops, pro tech stacks, pro modeling practice, tools)
were in a temp folder that was cleared; their findings are summarized here. `tools/verify_live.py` (not yet committed)
is the live-site QB/pricing check used on 3-4 Oct; item B turns it into an automatic check.

Tool picks from the research (free unless noted): uv (`uv pip compile --universal`) for pinned versions; ruff as a
pytest test; pytest-cov, pytest-randomly, pytest-regressions (frozen-week test), Hypothesis (odds, grading, CLV math);
Pandera for the tables the model reads; GitHub Releases for raw data out of git (Cloudflare R2 needs a card on file);
Healthchecks.io for the alarm (Matt signs up); opentimestamps-client plus `openssl ts` with FreeTSA and DigiCert for
ledger receipts; pip-audit and zizmor as tests; stdlib logging. Do not hash-lock requirements until Matt removes the
bare `pytest` from tests.yml. Overkill at our size: Airflow, Dagster, MLflow, Great Expectations, dbt, Kubernetes.

## Found on game day (3-4 Oct), first in line

| # | Fix | Why |
|---|---|---|
| A | Freeze each card at kickoff: a game under way keeps its last pre-kickoff price, edge and flag on the page | 4 Oct: the WAS card re-priced mid-game with Mariota out (edge 1.7, no flag) while the record kept WAS +4.5 |
| B | Automatic QB cross-check every run: the QB priced (game model and props) against ESPN's depth chart, a failing check on a mismatch | 3 Oct: SEA priced Drew Lock (stale schedule starter); props kept him after the game model was fixed |
| C | Price game-day inactives (needs Matt's yes): an inactive Questionable player counted like Out | 4 Oct: inactives are logged and shown, not priced; checked by hand |
| D | Rename "shadowunder" to the live totals flag everywhere in code and page data | The live under rule is labeled a shadow |
| F | Props book prices: the "median" price crosses the -100/+100 gap (e.g. -49, -65, -78, impossible American odds) and lines like 4.75 mix books on different lines; take each book's line and price as a pair, or the median of no-vig chances | 4 Oct: found while ranking props |
| G | The rain term is a cliff: forecast rain 50%+ takes about 4.3 points off a total, 49% takes none, so one forecast update flips an under (study a smooth version through the gate; any change needs Matt's yes) | 4 Oct: DET-CAR Under 50.5 flagged Saturday; the 6:40am MOS run dropped the rain chance under 50%, the total jumped 48.9 -> 52.7 and the flag vanished |
| H | Published page size: 60.1 MB against the 60 MB check (the hard cap is 64 MB); trim or split the biggest data files before a deploy fails | 4 Oct: the check failed, and with it the weekly run's tie check |
| I | Betting splits labels and sources, one source per market, always labeled: (1) the DraftKings fill for a moneyline split the consensus feed never posted disappears once the game is played (DraftKings drops finished games, so TEN-BAL, NE-BUF, MIA-MIN, LAC-SEA show none again); keep the last pre-kickoff split. (2) The tooltip's "read" time is the consensus time even on a DraftKings-filled market. (3) The reverse-move chip checks only the card-level source, so it could fire on DraftKings bets labeled consensus. (4) The price beside each side comes from the consensus line history on consensus splits and from DraftKings on filled ones; label which | 5 Oct: checked on the week 4 cards |
| E | Props vs Vegas study, low lines (0.5 catches and the like) apart from normal lines, and established starters apart from small-sample players; through the study gate | 4 Oct: the biggest model-vs-book gaps were all 0.5-catch overs on backups; no props cut has held on both windows |

## Phase 1: stop silent failures (bug fixes, no rule changes; about 1 week)

| # | Fix | Why |
|---|---|---|
| 1 | Quote the pull log (real CSV writer) and fail the pull step when a current-season file doesn't download | A network error with a comma can crash the next weekly run; failed downloads are logged as ok today |
| 2 | Weekly run: skip later steps when an earlier one fails; record picks only after the tie and standing checks pass | Today bets can be recorded from stale inputs, and checks run after the bets are on record |
| 3 | Props closing lines cut at kickoff | 2,038 props rows after kickoff feed the props-vs-market numbers |
| 4 | The ESPN injury fill never rewrites games already played | It changed 9 rows for 2026_04_PIT_CLE, 3 dated after kickoff |
| 5 | Raw snapshots saved whole (gzip), not cut at 5 MB | 67 raw files are cut off and can't be read back |
| 6 | Log files: atomic writes, a real CSV reader, and a check that no rows disappear | A merge on 3 Oct dropped 15 lines-log rows; the reader drops odd rows silently |
| 7 | No made-up defaults: a bad price is not -119, a missing price is not -110, a failed injury pull is not "nobody out"; mark the row and warn | Broken data turns into believable numbers today |
| 8 | One `current_season()` instead of `2027` typed in 15 places | Next season would be silently left out |
| 9 | Keep the Odds API key out of error text | It is truncated just before the key today, by luck |
| 10 | Fill missing wind with the training-rows median, not the all-seasons median | A small look-ahead in the backtest |

## Phase 2: reproducible runs and a locked record (about 2 weeks)

| # | Build | Why |
|---|---|---|
| 11 | Pinned package versions (`uv pip compile --universal`), including scipy, threadpoolctl and pytest | A library release can change picks with no code change |
| 12 | Append-only bet ledger; every row carries the git commit and a hash of the live rules | The tracker overwrites picks today; the record mixes model versions |
| 13 | Daily timestamp receipts on the ledger (OpenTimestamps plus an RFC 3161 stamp), with a verify script | Proof an outsider can check that no pick was changed later |
| 14 | Frozen-week test: re-run a stored past week and match the published picks exactly | Proves the system is reproducible |
| 15 | Move raw odds files and bulky generated data out of git (GitHub Releases or a free Cloudflare R2 bucket) | The repo grows about 35 MB a day and passes 1 GB around 20 Oct |

## Phase 3: code quality to pro standard (about 2 weeks)

| # | Build | Why |
|---|---|---|
| 16 | ruff (lint and format) run as a test | Catches cut-and-paste bugs and swallowed errors |
| 17 | Tests for untested modules (props, results, pull and 33 others), small frozen fixtures, no quiet skips, Hypothesis tests on the odds, grading and CLV math | 36 of 69 modules have no tests |
| 18 | One shared module each for odds math, paths, reading page data and the closing line | Two CLV definitions can disagree on the page today |
| 19 | Move the six backtests the page uses out of `experiments/` into the package; archive numbered copies | A research-script edit can break the weekly run |
| 20 | Split the two 1,200-line modules; proper logging with full step logs | Easier review, clearer failures |
| 21 | Page: escape quotes in text (a small security fix), load tab data only when opened | 15 MB loads up front on phones |

## Phase 4: how pros run live models (about 1 week)

| # | Build | Why |
|---|---|---|
| 22 | A rule card per live rule: expected win rate and CLV, expected range, and a pause test fixed in advance; a breach opens an issue and Matt decides | Pros pause on evidence, not losing streaks |
| 23 | CLV next to the record in the shadow watch and ready checks | CLV shows skill far faster than wins and losses |
| 24 | Measure the study gate's false-pass rate on pure noise | The honest version of the pros' overfitting corrections |

## Matt's to-dos in GitHub (I can't do these; about 5 minutes each)

1. Settings -> Rules: add a ruleset on `main` that blocks force-push and deletion.
2. Settings -> Code security: turn on Dependabot alerts.
3. Confirm two-factor login on the GitHub account.
4. Sign up for Healthchecks.io (free) and add its ping link as a secret; I'll write the code (an alarm when a run never starts).
5. Apply workflow edits I'll draft: Python 3.12 in CI to match the laptop, the page check on every PR, no Pages deploy when the tie check fails.

## Needs Matt's yes (bet-rule questions found along the way)

- A maximum age for a line before a pick uses it (today the newest line is used however old).
- One game can carry two units on the same under (totals flag plus wind under).

## Last: fund and legal (after all of the above)

A gaming and securities lawyer's opinion before any outside money; then a fund administrator, a private database
for the ledger and investor records, and written security and continuity policies.
