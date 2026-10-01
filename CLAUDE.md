# NFL model: working rules (Matt)

Read first in every session. Matt runs an NFL betting model and its site from this repo; the goal is the highest win
rate and the most units.

## Talking to Matt
- Very concise answers. Plain words, American spelling. Recommend one option; don't list ones you won't take.
- When something is blocked (network, permissions, a setting), say so and name the setting; don't quietly work around it.
- Nothing in the live model or bet rules changes without Matt's yes.

## The repo is public (it must stay public: free Actions minutes)
- Treat every commit as published forever. Never commit keys or tokens, personal information (address, phone, school,
  sportsbook accounts, bet slips, balances, real-money stakes), files from Matt's private repos or other projects, or
  licensed data the license doesn't let us republish.
- Keys live in GitHub Actions secrets (`${{ secrets.NAME }}`) and, locally, user environment variables or a gitignored
  `.env`. Never print one, never ask Matt to paste one into chat. A committed key is stolen: rotate it at the provider.
- The Gitleaks pre-commit hook (`tools/hooks/pre-commit`, `.gitleaks.toml`) blocks commits that look like secrets; enable it
  in each new clone with `git config core.hooksPath tools/hooks`. Never skip it (no `--no-verify`).
- Before every push, check `git diff --staged` against this list and say so in one line.

## Adopting a change (reports/round3_rule.md)
- Better on every window: 2015-18 (untouched), 2019-22 (tuning), 2023-25 (held out); no bet cost; beats its own placebo
  (values shuffled within season); no market inputs (lines, splits, prices never feed the model); no look-ahead.
- A rule found by looking at past results is tracked as a shadow (`picks.SHADOWS`; hidden ones in `HIDDEN_SHADOWS`) and
  graded live, not bet. `nflmodel/shadow_watch.py` and `ready_checks.py` open a GitHub "ready-check" issue when one pulls clear.
- Every study: a script in `experiments/`, a report in `reports/`, a row in `reports/decision_log.md` (newest first) and a
  paragraph in `docs/how_it_works.md`.
- Before asking Matt to adopt anything, run the `model-auditor` agent (`.claude/agents/model-auditor.md`) on the study;
  it tries to break the result (leaks, snooping, small samples) and its verdict goes in the report.

## The page (web/index.html, one file)
- Every displayed number comes from Python (web/data/*.js); the tie check (`python -m nflmodel.tie_check --page`) proves it.
- Clean, professional, uncluttered: minimal text, no captions, no equations on cards. Formulas, models and methods go in the Info tab.
- Check at desktop and 390 px wide with Playwright (`executablePath: '/opt/pw-browsers/chromium'`, `NODE_PATH=$(npm root -g)`); no page errors, no sideways scroll.

## Workflow for every change
1. Work on the session's branch. Test: `python -m pytest -q`, `python -m nflmodel.export_web`, `python -m nflmodel.tie_check --page`, screenshots for page changes.
2. Commit source only. Never commit regenerated `data/`, `web/data/` or reports the weekly run rewrites
   (`git checkout -q -- reports/ web/data/ data/` before committing).
3. Push, open a PR, wait for the `test` check, squash-merge, then reset the branch to `origin/main`.
4. Dispatch `weekly.yml` when page data must regenerate; cancel a weekly run that predates the merge.
- `.github/workflows` edits are blocked here; work within the existing workflows (`probe.yml` runs a command on GitHub's network).
- On Matt's Windows laptop: use `.venv/Scripts/python.exe` (Python 3.12 x64; pyarrow has no Windows ARM build), set
  `PYTHONUTF8=1`, and use `export_web --week` (the raw player files live only on GitHub). See docs/handoff.md.

## Live rules (nflmodel/picks.py)
- Spreads: flag at |edge| >= 4, weeks 1-17. Totals: unders at a 55%+ raw chance (`p_over_emp`); overs never.
- Wind under (1 Oct 2026): the under in outdoor games with forecast wind 10+ mph (`picks.WIND_UNDER`, `nflmodel/wind_live.py`), weeks 1-17.
- Model total weather: wind points (`model.wind_points`) and forecast rain 50%+ in the totals equation (`model.RAIN_FC`, 1 Oct 2026).
- Data stores are listed in `nflmodel/catalog.py`; the weekly pipeline is `nflmodel/weekly.py`.
