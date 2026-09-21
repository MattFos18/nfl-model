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
- `nflmodel/picks.py`     weekly picks table with our score, line, edge, win / cover / over odds for both sides, and the flag.
- `nflmodel/trends.py`    situational trends and injuries as-of each game (team home edge, head-to-head, coach and QB ATS, referee rates, slots, cold/wind edges, starters out, QB out) plus the persistence test.
- `nflmodel/export_web.py` exports every stat, rating, trend and model input per team to `web/data/` for the data room page (`web/index.html`, published at https://claude.ai/artifact/YMKPCSDvPLUZHnd81zBMfz).
- `nflmodel/verify.py`    accuracy checks against Pro-Football-Reference and the schedule; fails the build on a mismatch.
- `data/raw/`             raw downloads (git-ignored, rebuilt by `pull.py`)
- `data/processed/`       built tables (committed so the dashboard and backtest can read them)
- `reports/`              backtest reports, tuning results, decision log, weekly picks:
  - `backtest_v3.md` the go / no-go numbers: 3.0 vs old model vs Vegas, tuning window vs held-out, thresholds, market blend
  - `baseline_backtest.md` the old model's full record; `v3_backtest_full.md` the same tables for 3.0 over 2019 to 2026
  - `decision_log.md` every claim tested, the result, and what was decided
  - `lab.md` stat correlations (predictive vs same-season) and reliability; `ablation.csv`, `tuning_ratings.csv`, `v3_coefficients.txt`
  - `picks_2026_wk3.md`, `picks_2026_wk4.md` the weekly picks tables (Week 4 fills in once lines post)

## Headline results (held-out 2023 to 2025, 816 games)

| | 3.0 | Old model | Vegas close |
|---|---|---|---|
| Team points miss | 7.35 | 9.00 | 7.21 |
| Margin miss | 10.16 | 12.61 | 9.74 |
| Total miss | 10.35 | 12.75 | 10.12 |
| Brier (win odds) | 0.220 | 0.294 | 0.210 |
| Spreads at 3+ pt edge | 109-105, -2.8% ROI | old model 51.5%, -1.7% | |
| Spreads at 5+ pt edge (the flag) | 31-28, +0.3% (2019 to 2025: 68-59, +2.2%) | | |
| Totals at 6+ pt edge (the flag) | 14-8, +21.5% (2019 to 2025: 37-24, +15.8%) | | |

3.0 is far more accurate than the old model and close to the closing line on points. Small disagreements with the close lose;
5+ point spread edges and 6+ point total edges have won in both backtest windows, on small samples (a lead, not proof).
Every number in the tables is checked against Pro-Football-Reference and the schedule by `verify.py` (`reports/verification.md`).

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

Tuning (writes `reports/tuning_ratings.csv` and `reports/ablation.csv`, about 10 minutes):

```
python -m nflmodel.tune --grid --ablation
```
