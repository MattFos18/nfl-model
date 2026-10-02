# Project wiki

Short pages a new Claude session reads before working. At session start read this page and `gotchas.md`; open the
others when the task touches them. Keep pages short, cite code paths and reports, and say "unverified" for anything
nobody has checked.

| Page | What it holds |
|---|---|
| [gotchas.md](gotchas.md) | Traps this repo has hit (signs, ids, timing, look-ahead, bad values, machines), each with its file |
| [data_sources.md](data_sources.md) | Every outside source: what we use, where in code, timing and lag, terms, quirks |
| [log.md](log.md) | Dated one-liners of what changed, newest first |
| [checks.md](checks.md) | Standing checks: every fixed bug class, the check that catches it again, and where it runs |

## Where everything else lives

| Need | File |
|---|---|
| Working rules | `CLAUDE.md` |
| Context from the cloud session, Matt's preferences, laptop setup | `docs/handoff.md` |
| Every study's result and decision, newest first | `reports/decision_log.md` |
| How each piece of the model works | `docs/how_it_works.md` |
| The adoption rule | `reports/round3_rule.md`, coded in `nflmodel/study_gate.py` |
| Decisions waiting on Matt | `docs/todo.md` |
| Parked ideas | `docs/ideas.md` |
| Every data store, its columns and where it shows | `nflmodel/catalog.py` (Info -> Every data store on the site) |
| Live bet rules and shadows | `nflmodel/picks.py` |
| The weekly pipeline | `nflmodel/weekly.py`, `.github/workflows/weekly.yml` |

## Skills and agents

- `.claude/skills/study/SKILL.md`: the procedure for any model or bet-rule study.
- `.claude/skills/ship/SKILL.md`: branch, test, PR, merge, weekly run.
- `.claude/agents/model-auditor.md`: tries to break a study before Matt is asked to adopt it.
- `.claude/agents/data-checker.md`: checks a table or pipeline change for bad data.
- `.claude/agents/site-fact-checker.md`: checks page text and docs against Python outputs and sources.
- `.claude/agents/pr-reviewer.md`: reviews a diff for silent failures and missing tests.

## Keeping it current

- A new trap: a line in `gotchas.md` with its file, and a row in `checks.md` naming the check that catches it again. A new source or a change in one: its section in `data_sources.md`.
- Every merged change to the model, rules, sources or workflow: one line in `log.md`.
- Nothing personal here: the repo is public (`CLAUDE.md`).
