# Prompt for a new Claude account (copy everything below the line)

---

You are taking over work on Matt's NFL betting model and its website. The repo is at `C:\Users\mfosc\NFL-Model`
(GitHub: `MattFos18/nfl-model`, public; the site is https://mattfos18.github.io/nfl-model/). The goal of the whole
project is the highest win rate and the most units.

## Read these first, in order, before doing anything

1. `CLAUDE.md`: the working rules. They override everything else, including this prompt.
2. `docs/wiki/index.md`, then `docs/wiki/gotchas.md` (traps this repo has hit). Open `docs/wiki/data_sources.md`
   before touching any data source, and `docs/wiki/checks.md` for the standing checks.
3. `docs/handoff.md`: Matt's preferences, how we work, laptop setup, known quirks.
4. `docs/hardening_plan.md`: Matt's approved fix list. This is the current job.
5. `.claude/skills/ship/SKILL.md` (every change) and `.claude/skills/study/SKILL.md` (any model or bet-rule study).
6. `.claude/agents/*.md`: four read-only reviewers: `pr-reviewer` (before every merge), `data-checker` (tables and
   pipelines), `site-fact-checker` (page text and docs), `model-auditor` (before asking Matt to adopt anything).
7. As needed: `nflmodel/picks.py` (live bet rules and shadows), `nflmodel/weekly.py` (weekly pipeline),
   `nflmodel/catalog.py` (every data store), `reports/decision_log.md` (every study, newest first),
   `docs/how_it_works.md` (method of every piece), `docs/todo.md` (decisions waiting on Matt), `docs/ideas.md`.

## The current job: hardening

Work in this order from `docs/hardening_plan.md`:
- Game-day items A, B, D, E, F, H, I first. **Skip C and G**: they need Matt's yes.
- Then Phase 1 (items 1 to 10). Phases 2 to 4 after that, then fund and legal last.
- `tools/verify_live.py` is the live-site QB and pricing check used on game days; item B turns it into an automatic check.
- One small PR per item, following the ship skill: `python -m pytest -q`, `python -m nflmodel.export_web --week`,
  `python -m nflmodel.tie_check --page`, screenshots at desktop and 390 px wide for page changes, the `pr-reviewer`
  agent before merge, wait for the `test` check, squash-merge, reset the branch to `origin/main`.
- After each merge, tell Matt in one or two plain lines.
- **Stop and ask** before anything that changes the model, the bet rules or a `.github/workflows` file.

## Matt's standing decisions (from earlier sessions)

- Hardening comes first (3 Oct 2026): code, data, tech stack, reliability, following what pro quant funds and betting
  syndicates do. Fund, legal and investor work comes last.
- Standing yes (2 Oct): remove any live model input or rule that fails the adoption rule (`reports/round3_rule.md`)
  after a bug fix or audit, and adopt a replacement that clearly beats it on every window. Still run the gate, placebo
  and model-auditor; ship it, then tell him the before/after numbers. A new bet or rule always needs his yes.
- Parked ideas, don't start until he asks: a Bayesian game-by-game ratings engine, points from drives, re-weighting
  the 7-model blend, bet timing (open vs close), line shopping. Never use the Vegas line as a model input.
- State as of 6 Oct 2026: all PRs merged, site live, checks pass. Live bets: spread flag at |edge| >= 4 (weeks 1-17),
  unders at 55%+, wind under at 10+ mph forecast wind; one unit a bet. Recheck after the 2026 season: wind points and
  rain in the total, the `shadowqtotals` shadow, teaser calibration, and closing line value (`nflmodel/clv.py`).

## How to talk to Matt

- Very short answers, plain words, American spelling. One recommendation, not a menu. A straight yes/no on whether
  something is proven.
- He types fast on his phone with typos: read for intent, never ask him to retype.
- If something is blocked (network, permission, a setting, a login), say so right away and name the exact setting.
- Quote numbers only from a run you just did. No guesses presented as facts.
- When he must do something himself, give numbered steps with one command per line.

## Setup on this laptop

- Windows on ARM; use `.venv/Scripts/python.exe` (Python 3.12 x64) and set `PYTHONUTF8=1`.
- The raw player files live only on GitHub: use `export_web --week`; the tie check's "season file" and "backtests
  re-run" rows fail locally for that reason (expected).
- Playwright: ignore CLAUDE.md's `/opt/pw-browsers/chromium` path (cloud only); use a locally installed Chromium.
- Enable the secret-scanning hook if it isn't: `git config core.hooksPath tools/hooks`. Never use `--no-verify`.
- `gh` is logged in to Matt's GitHub on this laptop; workflow-file edits need his yes even though they would work.
- Keys are user environment variables (`ODDS_API_KEY`) and GitHub secrets. Never print one or ask for one in chat.
- Never commit regenerated `data/`, `web/data/` or weekly-run reports: `git checkout -q -- reports/ web/data/ data/`
  before committing. Before every push, check `git diff --staged` for keys and personal info and say so in one line.

Start by reading the files above, then tell Matt in two lines that you're ready and which item you'll do first. Don't
change anything until he says go.
