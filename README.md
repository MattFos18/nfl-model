# NFL Model

An NFL betting model and its site: team ratings from nflverse play-by-play, a points equation and a totals equation
refit every week, weather and injuries, backtested walk-forward on 2015-2025, and live bet rules graded every week.
The site: https://mattfos18.github.io/nfl-model/ (Breakdown, Picks, Bets, Backtest, Info).

## Start here

| If you want | Read |
|---|---|
| The rules every change follows | `CLAUDE.md` |
| How the model works, input by input | `docs/how_it_works.md` |
| Every data source, and the known traps | `docs/wiki/index.md`, `docs/wiki/gotchas.md` |
| Every decision and the test behind it (newest first) | `reports/decision_log.md` |
| What is next, and what waits on Matt | `docs/todo.md`, `docs/ideas.md` |

## Folders

| Folder | What is in it |
|---|---|
| `nflmodel/` | The model and the pipeline: pulls (`pull.py`, `lines.py`, `weather.py`, `wind_live.py`), tables (`build.py`, `features.py`, `ratings.py`, `trends.py`, `players.py`), the model (`model.py`), bet rules (`picks.py`), grading (`backtest.py`, `tracker.py`, `clv.py`), checks (`verify.py`, `data_checks.py`, `tie_check.py`, `health.py`), the weekly run (`weekly.py`) and the site export (`export_web.py`). `catalog.py` lists every data store. |
| `experiments/` | One script per study (about 150), each with its report in `reports/`. |
| `reports/` | Study results (`.md` and `.csv`), the decision log, and the reports the weekly run rewrites. |
| `docs/` | The method (`how_it_works.md`), the wiki, the handoff note, the to-do and parked ideas. |
| `data/` | `processed/` tables the model reads, `lines/` line and splits logs, `tracker/` graded bets, `weather/` forecasts, `runs/` run logs. `raw/` is downloaded and not in git. |
| `web/` | The site: one page (`index.html`) and the data it shows (`data/*.js`, written by Python). |
| `tests/` | `python -m pytest -q`. |
| `tools/hooks/` | The Gitleaks hook that blocks commits holding a key. |
| `.claude/` | Claude's reviewer agents and the study and ship skills. |
| `.github/workflows/` | The weekly run, the 30-minute line watch, the site deploy and the checks. |

<!-- results:start -->
## Headline results (held-out 2023 to 2025, 816 games)

| | 3.0 | Vegas close |
|---|---|---|
| Team points miss | 7.24 | 7.21 |
| Margin miss | 9.90 | 9.74 |
| Total miss | 10.12 | 10.12 |
| Brier (win odds) | 0.216 | 0.210 |
| Spreads at 3+ pt edge | 83-64 | |
| Spreads at 4+ pt edge (the flag) | 41-23 (2019 to 2025: 123-77; 116-69 outside Week 18) | |
| Totals at 4+ pt edge (not flagged: no total cutoff wins in both windows) | 72-53 (2019 to 2025: 173-124) | |

These rows are written by `report.py` from the same prediction table as the page and the reports, on every run. Ridge strength and thresholds were tuned on 2019 to 2022 only; since 22 Sep 2026 new inputs and the rating decay are accepted only when they help on both windows, so 2023 to 2025 is a second test window for those, and the live season is the only fully unseen test.
<!-- results:end -->

3.0 is close to the closing line on points, and the closing line is still the more accurate of the two. Small
disagreements with the close lose; 4+ point spread edges win across 2019 to 2025 (the block above, rewritten every run), below break-even
in 2022, and near break-even on the untouched 2015 to 2018 window (a lead, not proof); the live tracker is what settles it. The model has twenty-two inputs, each with one plain meaning
(`docs/how_it_works.md` section 4), the regression is refit before every week on every played game since 2013, and
there are no flags in Week 18, where resting starters make the line smarter than the ratings. Every number in the
tables is checked against Pro-Football-Reference and the schedule by `verify.py` (`reports/verification.md`).

## Run

```
pip install -r requirements.txt
python -m nflmodel.pull --seasons 2012-2026 --only schedules,pbp   # ~270 MB
python -m nflmodel.build
python -m nflmodel.features
python -m nflmodel.baseline --seasons 2019-2025                     # old model, ~1 min
python -m nflmodel.ratings                                          # as-of ratings, ~30 s
python -m nflmodel.model --seasons 2019-2026                        # 3.0
python -m nflmodel.backtest data/processed/pred_v3.parquet --name "3.0"
python -m nflmodel.report
python -m nflmodel.picks --season 2026 --week 4
python -m nflmodel.verify
python -m nflmodel.trends
python -m nflmodel.export_web
```

Weekly run by hand (about 6 minutes; `--skip-network` in a sandbox that cannot reach nflverse, ESPN or Open-Meteo):

```
python -m nflmodel.weekly
python -m nflmodel.lines        # one line snapshot
```

Tuning (writes `reports/tuning_ratings.csv` and `reports/ablation.csv`, about 10 minutes):

```
python -m nflmodel.tune --grid --ablation
```
