# NFL Model 3.0

Points-for / points-against prediction and betting model, built on free nflverse play-by-play data and
backtested walk-forward. Plan: "NFL Model 3.0 Plan" doc in the NFL Model project.

## Where things stand

| Phase | Status |
|---|---|
| 1. Setup: repo, data pulls 2012 to 2026, games and team-game tables | Done 21 Sep |
| 2. Baseline: the spreadsheet model rebuilt in Python and backtested 2019 to 2025 | Done 21 Sep, `reports/baseline_backtest.md` |
| 3. Build 3.0: EPA ratings, preseason prior, fitted adjustments, margin distribution, QB rating | Done 21 Sep, `reports/backtest_v3.md`, `reports/decision_log.md` |
| 4. Go / no-go: tuned on 2019 to 2022, judged on 2023 to 2025 | Numbers are in `reports/backtest_v3.md`; the decision is Matt's |
| 5. Automate + dashboard | Not started |
| 6. Extras (player model, line history, splits, sizing) | Not started |

## Layout

- `nflmodel/pull.py`      download raw nflverse data (schedules, play-by-play, injuries, snap counts, depth charts, rosters, FTN). Logs every pull to `data/raw/pull_log.csv`.
- `nflmodel/build.py`     `data/processed/games.parquet` (one row per game, 1999 to now, closing lines and situation) and `team_games.parquet` (one row per team per game, 2012 to now, 140 EPA-style stats).
- `nflmodel/features.py`  `team_box.parquet` (box-score counts per team per game: completions, sacks, red zone trips, penalties, drive starts, kickoff yards) and `qb_games.parquet` (dropbacks and EPA per passer per game).
- `nflmodel/baseline.py`  the spreadsheet model, formula for formula (see the docstring for the mapping), run walk-forward. Writes `pred_baseline.parquet`.
- `nflmodel/ratings.py`   opponent-adjusted, time-decayed ratings (weighted ridge on team-game stats), QB rating, and the as-of feature table `features_asof.parquet`.
- `nflmodel/model.py`     3.0: ridge regression from ratings and situation to team points, refit per season on all prior seasons; key-number margin distribution; win, cover and over probabilities. Writes `pred_v3.parquet`.
- `nflmodel/backtest.py`  grades any prediction table: points miss vs Vegas, Brier and calibration, ATS and totals record and ROI at -110, by season and edge size, threshold sweeps.
- `nflmodel/tune.py`      parameter grid and feature ablation on 2019 to 2022 only.
- `nflmodel/report.py`    assembles `reports/backtest_v3.md` (3.0 vs old model vs Vegas, tuning vs held-out windows, market blend).
- `nflmodel/picks.py`     weekly picks table with our score, line, edge, probabilities and bet flag.
- `data/raw/`             raw downloads (git-ignored, rebuilt by `pull.py`)
- `data/processed/`       built tables (committed so the dashboard and backtest can read them)
- `reports/`              backtest reports, tuning results, decision log, weekly picks

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
```

Tuning (writes `reports/tuning_ratings.csv` and `reports/ablation.csv`, about 10 minutes):

```
python -m nflmodel.tune --grid --ablation
```
