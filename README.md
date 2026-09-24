# NFL Model 3.0

Points-for / points-against prediction and betting model, built on free nflverse play-by-play data and
backtested walk-forward. Plan: "NFL Model 3.0 Plan" doc in the NFL Model project.

## Where things stand

| Phase | Status |
|---|---|
| 1. Setup: repo, data pulls 2012 to 2026, games and team-game tables | Done 21 Sep |
| 2. Baseline: the spreadsheet model rebuilt in Python and backtested 2019 to 2025 | Done 21 Sep, `reports/baseline_backtest.md` (kept in the repo for the record; no longer on the page) |
| 3. Build 3.0: EPA ratings, preseason prior, fitted adjustments, margin distribution, QB rating | Done 21 Sep; 22 Sep: twelve inputs, weekly refit, rain, a totals equation, every idea tested (`reports/backtest_v3.md`, `reports/decision_log.md`) |
| 4. Go / no-go: tuned on 2019 to 2022, judged on 2023 to 2025 | Numbers are in `reports/backtest_v3.md`; the decision is Matt's |
| 5. Automate + dashboard | Built 21 Sep: weekly run (Tue/Sat), 10-minute line watch, kickoff forecasts, bet tracker with CLV, data room with This-week and Track-record tabs. Merged to `main` 22 Sep; both GitHub Actions workflows are live (first runs: the weekly pipeline passed pull, build and features; the line feeds answered 403 from GitHub's runners, fallbacks added) |
| 6. Extras (player model, splits, sizing, timing tests on the logged lines) | After a few weeks of logs |

## Layout

- `nflmodel/pull.py`      download raw nflverse data (schedules, play-by-play, injuries, snap counts, depth charts, rosters, FTN). Logs every pull to `data/raw/pull_log.csv`.
- `nflmodel/build.py`     `data/processed/games.parquet` (one row per game, 1999 to now, closing lines and situation) and `team_games.parquet` (one row per team per game, 2012 to now, 140 EPA-style stats).
- `nflmodel/features.py`  `team_box.parquet` (box-score counts per team per game: completions, sacks, red zone trips, penalties, drive starts, kickoff yards) and `qb_games.parquet` (dropbacks and EPA per passer per game).
- `nflmodel/baseline.py`  the spreadsheet model, formula for formula (see the docstring for the mapping), run walk-forward. Writes `pred_baseline.parquet`.
- `nflmodel/ratings.py`   opponent-adjusted, time-decayed ratings (weighted ridge on team-game stats), QB rating, and the as-of feature table `features_asof.parquet`.
- `nflmodel/model.py`     3.0: ridge regression from ratings and situation to team points, refit per season on all prior seasons; key-number margin distribution; win, cover and over probabilities. Writes `pred_v3.parquet`.
- `nflmodel/backtest.py`  grades any prediction table: points miss vs Vegas, Brier and calibration, ATS and totals record and ROI at -110, by season and edge size, threshold sweeps.
- `nflmodel/tune.py`      parameter grid and feature ablation on 2019 to 2022 only.
- `nflmodel/report.py`    assembles `reports/backtest_v3.md` (3.0 vs Vegas, tuning vs held-out windows, market blend).
- `nflmodel/picks.py`     weekly picks table with our score, line, edge, win / cover / over odds for both sides, and the flag.
- `nflmodel/trends.py`    situational trends and injuries as-of each game (team home edge, head-to-head, coach and QB ATS, referee rates, slots, cold/wind edges, starters out, QB out) plus the persistence test.
- `nflmodel/season.py`    season simulation (win totals, divisions, seeds, the Super Bowl) from the game model's equation; `nflmodel/player_season.py` player season totals and the breakout watch; backtests in `experiments/season_backtest.py` and `experiments/player_season_backtest.py`.
- `nflmodel/weekly.py`    the weekly run: pull, build, verify, weather, ratings, trends, model, grade, picks, export, recap (`reports/weekly_latest.md`, `data/runs/run_log.csv`).
- `nflmodel/lines.py`     line watch every 10 minutes to `data/lines/lines_log.csv`: ESPN scoreboard (DraftKings-provider line, with fallbacks), The Odds API every eight hours, player prop lines Thursday and Sunday; two hours when the `ODDS_API_KEY` secret is set (free tier, ten US books), DraftKings direct (refused from GitHub's servers); raw JSON kept; splits hook pending a source.
- `nflmodel/weather.py`   Open-Meteo kickoff forecasts for unplayed outdoor games, applied before pricing, logged.
- `nflmodel/tracker.py`   model picks and Matt's bets (`data/tracker/my_bets.csv`) graded with closing line value (`reports/track_record.md`).
- `nflmodel/audit.py`     backtest audit: leakage test, coverage, bootstrap intervals on every rejected input, rejected ideas as standalone bets (`reports/audit.md`).
- `.github/workflows/`    `weekly.yml` (Tue 06:00, Thu 14:00, Sat 10:00 and Sun 09:00 ET) and `lines.yml` (every 10 minutes; The Odds API every eight hours, player prop lines Thursday and Sunday, when the key is set); both commit their outputs.
- `nflmodel/export_web.py` exports every stat, rating, trend and model input per team to `web/data/` for the data room page (`web/index.html`, published at https://claude.ai/artifact/YMKPCSDvPLUZHnd81zBMfz). `--rankings` also writes the per-week rankings and the full backtest table. The page's tabs:
  - **This week**: one card per game, model vs Vegas vs actual, win / cover / over odds for both sides, the flag, and "Why these numbers" (every input's contribution to each team's expected points).
  - **Season**: win totals, division, playoff and Super Bowl odds from playing the season out 10,000 times on the model's numbers; player season totals with a breakout watch; both backtested on both windows (docs section 19).
  - **Rankings**: every team on every rating as of any week, sortable with ranks, offense-vs-defense plot and power bars, plus the old sheet's indexes.
  - **History**: every priced game since 2015 (2015 to 2018 were never used to choose anything), model expected vs Vegas implied vs actual, by-season record, cumulative units on the flags.
  - **Team**: the raw game log (box score, EPA, ratings into the game, trends, injuries), ratings by week, how a rating is built (every game and weight, summed and checked), and the game deep dive (every coefficient times input).
  - **Model**: what kind of model it is and the full fitted equation, the stat analysis (predictive vs same-season correlations, reliability, ablation, additions, persistence, tuning), methods compared, every column's definition and source, data pulls and verification, decision log and audit.
  - **Track record**: model picks and Matt's bets graded with closing line value.
- `nflmodel/verify.py`    accuracy checks against Pro-Football-Reference (`data/reference/`) and the schedule; fails the build on a mismatch.
- `data/raw/`             raw downloads (git-ignored, rebuilt by `pull.py`)
- `data/processed/`       built tables (committed so the dashboard and backtest can read them)
- `reports/`              backtest reports, tuning results, decision log, weekly picks:
  - `backtest_v3.md` the go / no-go numbers: 3.0 vs Vegas, tuning window vs held-out, thresholds, market blend; `learning_experiments.csv` weekly refit and residual-learning tests; `input_set_experiments.csv` the input-set test; `additions.csv` every idea (injuries, referees, primetime, head-to-head, division, travel, time zones, rain, snow, rest) added and tested
  - `baseline_backtest.md` the old model's full record; `v3_backtest_full.md` the same tables for 3.0 over 2019 to 2026
  - `decision_log.md` every claim tested, the result, and what was decided
  - `lab.md` stat correlations (predictive vs same-season) and reliability; `ablation.csv`, `tuning_ratings.csv`, `v3_coefficients.txt`
  - `picks_2026_wk3.md`, `picks_2026_wk4.md` the weekly picks tables (Week 4 fills in once lines post)

<!-- results:start -->
## Headline results (held-out 2023 to 2025, 816 games)

| | 3.0 | Vegas close |
|---|---|---|
| Team points miss | 7.28 | 7.21 |
| Margin miss | 9.93 | 9.74 |
| Total miss | 10.27 | 10.12 |
| Brier (win odds) | 0.217 | 0.210 |
| Spreads at 3+ pt edge | 86-72 | |
| Spreads at 4+ pt edge (the flag) | 46-30 (2019 to 2025: 135-94; 128-84 outside Week 18) | |
| Totals at 4+ pt edge (not flagged: no total cutoff wins in both windows) | 70-61 (2019 to 2025: 146-125) | |

These rows are written by `report.py` from the same prediction table as the page and the reports, on every run. Ridge strength and thresholds were tuned on 2019 to 2022 only; since 22 Sep 2026 new inputs and the rating decay are accepted only when they help on both windows, so 2023 to 2025 is a second test window for those, and the live season is the only fully unseen test.
<!-- results:end -->

3.0 is close to the closing line on points, and the closing line is still the more accurate of the two. Small
disagreements with the close lose; 4+ point spread edges are 128-84 (60.4%) across 2019 to 2025 in weeks 1 to 17 on the current model, below break-even
in 2022 (16-19) and 2025 (13-12), and 62-57 on the untouched 2015 to 2018 window (a lead, not proof); the live tracker is what settles it. The model has twenty-two inputs, each with one plain meaning
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
