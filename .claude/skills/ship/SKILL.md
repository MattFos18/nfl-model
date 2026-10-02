---
name: ship
description: Use to ship any change in this repo (code, page, docs, a study): branch, tests, page export and tie check, page screenshots, revert regenerated data, the staged-diff privacy check, PR, wait for the test check, squash-merge, reset, and the weekly run.
---

# Shipping a change

The repo is public and runs live bets: every step below exists because skipping it once cost something.

## 1. Branch
Work on the session's branch, never on `main`. Start from the newest main: `git fetch origin` and branch from
`origin/main` (local runs reproduce GitHub's numbers only on the same data).

## 2. Test
On Matt's laptop prefix Python with `PYTHONUTF8=1` and use `.venv/Scripts/python.exe`.
1. `python -m pytest -q`: all pass.
2. Export the page data: `python -m nflmodel.export_web --week` on the laptop (the raw player files live only on
   GitHub); `python -m nflmodel.export_web` where they exist.
3. `python -m nflmodel.tie_check --page`. Compare with the same command on main before your change: the rows that fail
   locally on main (on the laptop: "season file", "backtests re-run") may fail; any new failing row is yours to fix.
4. Page changes: screenshot at desktop and at 390 px wide with Playwright; no page errors in the console, no sideways
   scroll. Locally install a browser with `npx playwright install chromium` and drop the cloud `executablePath`.
5. Code changes: run the `pr-reviewer` agent; data or pipeline changes: `data-checker`; page or doc text:
   `site-fact-checker`.

## 3. Commit source only
- `git checkout -q -- reports/ web/data/ data/` to drop what the export and checks regenerated (keep a study's own new
  report files: add them by name).
- `git add` files by name, never `git add -A` (untracked raw files sit in `data/raw/`).
- Commit message ends with the attribution line the session gives.
- The Gitleaks hook runs on commit (`git config core.hooksPath tools/hooks` once per clone). Never `--no-verify`.

## 4. Privacy check before every push
Read `git diff --staged` (or `git diff origin/main...HEAD` after committing) for: keys or tokens, personal information
(address, phone, school, emails, sportsbook accounts, bet slips, balances, real-money stakes), files from Matt's
private repos or other projects, licensed raw data. Tell Matt in one line that it is clean.

## 5. PR and merge
1. `git push -u origin <branch>`, then `gh pr create --base main` with a short body (what, why, how tested).
2. Wait for the `test` check to pass: `gh pr checks <n> --watch`. Do not merge on pending or failing.
3. `gh pr merge <n> --squash --delete-branch`.
4. Reset the branch: `git fetch origin && git reset --hard origin/main`.
5. One line in `docs/wiki/log.md` for anything that changes the model, rules, sources or workflow (in the PR itself).

## 6. Regenerate the page data
When the page's data must change: `gh workflow run weekly.yml`. Then `gh run list --workflow weekly.yml` and cancel any
run that started before the merge (`gh run cancel <id>`): it would publish numbers from the old code. Check the new
run finishes and its health checks pass.

## Limits
- `.github/workflows` edits may be blocked by permissions; say so to Matt and name the setting
  (`gh auth refresh -s workflow` locally). Use `probe.yml` to run a command on GitHub's network.
- Nothing in the live model or bet rules changes without Matt's yes.
