"""The weekly run. Tuesday (after MNF) does everything; Saturday refreshes lines, weather and the picks.

Steps, each logged to data/runs/run_log.csv with its status; a failed pull is reported, never papered over:
  1. pull      nflverse schedules, play-by-play, injuries, snap counts for the current season (and last, once)
  2. build     games.parquet, team_games.parquet, team_box.parquet, qb_games.parquet
  3. verify    the accuracy checks; the run stops if scores or mirrors break
  4. weather   kickoff forecasts for the next 10 days (Open-Meteo), applied to unplayed outdoor games
  5. ratings   as-of feature table, trends and injuries
  6. model     3.0 walk-forward through the current season; old model too for the comparison column
  7. grade     last week's flagged picks and Matt's bets (tracker), closing line value where a line was logged;
               the live results (ESPN's scores, the model's pre-kickoff calls graded) right after the lines
  8. picks     this week's table and flags; export the data room
  9. recap     reports/weekly_<date>.md: what was pulled, what changed, this week's flags, last week's record

Usage: python -m nflmodel.weekly [--full] [--skip-network]   (--skip-network for a dry run in a sandbox)
"""
from __future__ import annotations
import argparse, datetime as dt, subprocess, sys, time, traceback
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT, RUNS, REP = ROOT / "data" / "processed", ROOT / "data" / "runs", ROOT / "reports"


_RUN_AT = {"run_at": None}   # the run being logged: every step's row goes to data/runs/run_log.csv as it finishes

# the backtests built from the model's predictions (and the props rule) that the pages quote: re-run after every model
# run (26 Sep 2026: calibration_start, the season backtest and the props by-season run had not been re-run since the
# model changed; about three minutes in all). Each writes a stamp of the inputs it read (reports/backtest_inputs.json),
# and the tie check fails when an input has changed since (a skipped or failed re-run can never pass unseen).
_P = "data/processed/"
BACKTESTS = {
    "sizing backtest": ("experiments.sizing_backtest", [_P + "pred_v3.parquet", _P + "games.parquet", "nflmodel/picks.py", "experiments/sizing_backtest.py"]),
    "threshold sweep": ("experiments.threshold", [_P + "pred_v3.parquet", _P + "games.parquet", "experiments/threshold.py"]),
    "calibration start": ("experiments.calibration_start", [_P + "pred_v3.parquet", _P + "games.parquet", "nflmodel/picks.py", "experiments/calibration_start.py"]),
    "season backtest": ("experiments.season_backtest", [_P + "pred_v3.parquet", _P + "games.parquet", _P + "features_asof.parquet", "nflmodel/season.py", "nflmodel/model.py", "experiments/season_backtest.py"]),
    "props by season": ("experiments.props_by_season", [_P + "pred_v3.parquet", _P + "games.parquet", _P + "scheme_plays.parquet", _P + "snap_exposure.parquet", _P + "features_asof.parquet", "nflmodel/props.py", "experiments/props_by_season.py"]),
    "legitimacy tests": ("experiments.legitimacy", [_P + "pred_v3.parquet", _P + "games.parquet", "experiments/legitimacy.py"]),
}
STAMPS = REP / "backtest_inputs.json"


def input_hashes(paths) -> dict:
    """sha1 of each input file's bytes (the checkout's file times are all the same, so contents are compared)."""
    import hashlib
    return {p: (hashlib.sha1((ROOT / p).read_bytes()).hexdigest()[:16] if (ROOT / p).exists() else "missing") for p in paths}


def run_backtest(name: str) -> str:
    """Run one backtest and stamp the inputs it read."""
    import json
    mod, ins = BACKTESTS[name]
    out = sh([mod])
    st = json.loads(STAMPS.read_text()) if STAMPS.exists() else {}
    st[name] = {"ran_at": _RUN_AT["run_at"], "inputs": input_hashes(ins)}
    STAMPS.write_text(json.dumps(st, indent=1, sort_keys=True))
    return out


def step(name, fn, log):
    t0 = time.time()
    try:
        out = fn()
        row = {"step": name, "status": "ok", "detail": str(out)[:200] if out is not None else "", "seconds": round(time.time() - t0, 1)}
        print(f"[ok] {name} ({time.time() - t0:.0f}s)", flush=True)
    except Exception as e:  # noqa
        out = None
        row = {"step": name, "status": "error", "detail": f"{type(e).__name__}: {str(e)[:200]}", "seconds": round(time.time() - t0, 1)}
        print(f"[ERROR] {name}: {e}", flush=True)
        traceback.print_exc()
    log.append(row)
    if _RUN_AT["run_at"]:   # logged as it finishes, so the tie check later in this run sees a failed step (and fails)
        RUNS.mkdir(parents=True, exist_ok=True); f = RUNS / "run_log.csv"
        pd.DataFrame([row]).assign(run_at=_RUN_AT["run_at"]).to_csv(f, mode="a", header=not f.exists(), index=False)
    return out


def sh(cmd):
    r = subprocess.run([sys.executable, "-m"] + cmd, cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError((r.stderr or r.stdout)[-400:])
    return (r.stdout or "").strip().splitlines()[-1] if r.stdout.strip() else ""


STATE = RUNS / "week_state.json"
PULL_SETS = ["schedules", "players", "ngs", "ngs_rec", "ngs_rush", "pbp", "injuries", "snap_counts", "rosters", "depth_charts", "pfr_advstats", "pfr_pass", "pfr_rush", "pfr_rec", "player_stats", "participation", "ftn"]
PULL_HISTORY = ["pfr_advstats", "pfr_pass", "pfr_rush", "pfr_rec", "player_stats"]


def keep_pull_log():
    """Put back the pull-log rows already committed on this checkout. The workflow restores an older raw copy over the
    checkout's data/raw, pull log included, and the commit then dropped the newer rows (29 Sep 2026: a retry committed
    76 deletions). Union of the committed and restored logs, oldest first."""
    import io, subprocess
    p = ROOT / "data" / "raw" / "pull_log.csv"
    try:
        head = subprocess.run(["git", "show", "HEAD:data/raw/pull_log.csv"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    except Exception:
        return
    if not head.strip():
        return
    h = pd.read_csv(io.StringIO(head), dtype=str)
    cur = pd.read_csv(p, dtype=str) if p.exists() else h.iloc[:0]
    if len(h.merge(cur, how="left", indicator=True).query("_merge == 'left_only'")) == 0:
        return
    both = pd.concat([h, cur], ignore_index=True).drop_duplicates().sort_values("pulled_at", kind="stable")
    p.parent.mkdir(parents=True, exist_ok=True); both.to_csv(p, index=False)
    print(f"pull log: {len(both) - len(cur)} committed rows put back")


def refresh_raw():
    """A retry with nothing to do still ends in the workflow's raw-data save (29 Sep 2026: the Tuesday retry restored an
    old copy without the current players table, saved it as the newest, and the next line watch failed two health
    checks on it). Pull the same files a run pulls so the copy saved is current; never fail the retry on a network error."""
    from . import pull
    try:
        keep_pull_log()
        season = int(pd.read_parquet(OUT / "games.parquet").season.max())
        pull.pull([season - 1, season], PULL_SETS)
        pull.pull(list(range(2016, season + 1)), PULL_HISTORY, force_current=False)
    except Exception as e:
        print(f"raw refresh failed: {type(e).__name__}: {e}")


def write_state():
    """data/runs/week_state.json: the picks week and whether a source is still outstanding (lines.week_state)."""
    import json
    from . import lines
    st = lines.week_state(pd.read_parquet(OUT / "games.parquet"))
    RUNS.mkdir(parents=True, exist_ok=True); STATE.write_text(json.dumps(st, indent=1))
    return st


def main(full=False, skip_network=False):
    from . import pull, picks as P, tracker, weather, export_web, tie_check
    log = []
    run_at = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    _RUN_AT["run_at"] = run_at
    games0 = pd.read_parquet(OUT / "games.parquet")
    season = int(games0.season.max())
    if not skip_network:
        keep_pull_log()
        seasons = list(range(2012, season + 1)) if full else [season - 1, season]
        step("pull", lambda: pull.pull(seasons, PULL_SETS), log)
        # the player-history sources for every season the game logs cover (only missing files are fetched): the cached
        # raw folder holds the recent seasons, and without these the logs' official tackles and Pro-Football-Reference
        # columns would go blank for older seasons
        step("pull player history", lambda: pull.pull(list(range(2016, season + 1)), PULL_HISTORY, force_current=False), log)
    step("build", lambda: sh(["nflmodel.build"]), log)
    step("features", lambda: sh(["nflmodel.features"]), log)
    step("snap exposure", lambda: sh(["nflmodel.exposure"]), log)   # every player's snap share by game (raw snap counts only), for the props' snap trend (26 Sep 2026: no step built it; it stopped at Week 2). Before every step that asks which week is current (29 Sep 2026): the picks week advances only once the week before is in this file too, so with the step after the player, position and scheme steps, the first run after Monday's snap counts landed built those as of the old week while the picks moved on
    v = step("verify", lambda: sh(["nflmodel.verify"]), log)
    if log[-1]["status"] == "error":
        _write(log, run_at, season, None, None, halted=True)
        return log
    if not skip_network:
        step("weather", lambda: weather.run(), log)
    games = pd.read_parquet(OUT / "games.parquet")
    games = weather.apply_to_games(games)
    games.to_parquet(OUT / "games.parquet", index=False)
    if not skip_network:
        step("lines", lambda: sh(["nflmodel.lines"]), log)   # every live number from the same moment: the lines are pulled with the starters, injuries and forecast above
    step("live results", lambda: sh(["nflmodel.results"] + (["--no-fetch"] if skip_network else [])), log)   # the ESPN scoreboard's scores and the pre-kickoff calls graded (27 Sep 2026; web/data/live.js)
    step("ratings", lambda: sh(["nflmodel.ratings"]), log)
    step("trends", lambda: sh(["nflmodel.trends"]), log)
    step("players", lambda: sh(["nflmodel.players"]), log)
    step("positions", lambda: sh(["nflmodel.positions"]), log)
    step("scheme", lambda: sh(["nflmodel.scheme"]), log)   # scheme and play-calling profiles (readings; participation and FTN charting)
    step("player splits", lambda: sh(["nflmodel.player_splits"]), log)   # every player by look, situation and opponent (Players -> Matchups and schemes)
    step("model", lambda: sh(["nflmodel.model", "--seasons", f"2015-{season}"]), log)
    step("opener study", lambda: sh(["nflmodel.opener_study"]), log)   # the Tuesday model and the archive openers, for the Backtest tab (28 Sep 2026)
    step("props", lambda: sh(["nflmodel.props"]), log)     # player-against-scheme projections for the week, and last week's graded; after the model, whose expected points they scale to (26 Sep 2026: before it, they carried the previous run's)
    for name in BACKTESTS:   # every backtest the pages quote, re-run on this model (sizing: 24 Sep 2026; the rest 26 Sep 2026); the legitimacy tests too, before the export that shows them (26 Sep 2026: they ran after it, so the page showed the run before's)
        step(name, lambda n=name: run_backtest(n), log)
    step("audit reports", lambda: sh(["nflmodel.report"]), log)   # the README's results block and backtest_v3.md, before the tie check reads them (24 Sep 2026: it ran after, so the check compared a run-old README)
    from . import lines
    cur_season, cur_week = lines.current_week(games)
    pk = step("picks", lambda: P.table(cur_season, cur_week), log)
    if pk is not None:
        (REP / f"picks_{cur_season}_wk{cur_week}.md").write_text(P.markdown(pk, cur_season, cur_week))
        pk.to_csv(REP / f"picks_{cur_season}_wk{cur_week}.csv", index=False)
        step("log run", lambda: P.log_run(pk, run_at), log)
        step("record picks", lambda: tracker.record_model_picks(pk, run_at), log)
        from . import refresh
        step("inputs fingerprint", lambda: refresh.write(), log)   # what this run priced with; the line watch re-prices when it changes
    step("grade", lambda: tracker.main(), log)
    step("tie check (sources)", lambda: tie_check.main(False) or (_ for _ in ()).throw(RuntimeError("numbers disagree: see reports/tie_check.md")), log)
    step("export data room", lambda: export_web.main(), log)
    step("tie check (page)", lambda: tie_check.main(True) or (_ for _ in ()).throw(RuntimeError("page files disagree with the sources: see reports/tie_check.md")), log)
    _write(log, run_at, cur_season, cur_week, pk)
    st = write_state()
    print(f"picks week {st['season']} week {st['week']}: " + ("complete" if st["complete"] else ("waiting on " + "; ".join(st["missing"]) if st["pending"] else "in play")), flush=True)
    return log


def _write(log, run_at, season, week, pk, halted=False):
    RUNS.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(log).assign(run_at=run_at)   # each row went to run_log.csv as its step finished (step())
    L = [f"# Weekly run, {run_at}", ""]
    if halted:
        L += ["**Halted: verification failed.** Nothing downstream was rebuilt; the last good picks stand.", ""]
    L += ["## Steps", "", df[["step", "status", "detail", "seconds"]].to_markdown(index=False), ""]
    errs = df[df.status == "error"]
    if len(errs):
        L += ["**Failed steps above were skipped, not filled with stale data.**", ""]
    if pk is not None and len(pk):
        flagged = pk[pk.bet != ""]
        L += [f"## Week {week}, {season}: {len(flagged)} flagged of {len(pk)} games", ""]
        L += [flagged[["away_team", "home_team", "away_exp", "home_exp", "spread_line", "total_line", "spread_edge", "total_edge", "bet"] + (["stake_pct"] if "stake_pct" in flagged.columns else [])].round(2).to_markdown(index=False) if len(flagged) else "No game clears the flag thresholds.", ""]
        L += [f"Full table: reports/picks_{season}_wk{week}.md", ""]
    if (REP / "track_record.md").exists():
        tr = (REP / "track_record.md").read_text().splitlines()
        L += ["## Track record", ""] + tr[4:16] + ["", "Full record: reports/track_record.md", ""]
    (REP / f"weekly_{run_at[:10]}.md").write_text("\n".join(L))
    (REP / "weekly_latest.md").write_text("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--if-pending", action="store_true", help="run only when the last run left the picks week waiting on a late source (the Tuesday and Wednesday retries)")
    ap.add_argument("--skip-network", action="store_true")
    a = ap.parse_args()
    if a.if_pending:
        import json
        st = json.loads(STATE.read_text()) if STATE.exists() else {}
        if not st.get("pending"):
            print(f"nothing pending: week {st.get('week')} " + ("complete" if st.get("complete") else "still in play") + "; no run")
            if not a.skip_network:
                refresh_raw()
            sys.exit(0)
        print(f"retry: week {st.get('week')} waiting on " + "; ".join(st.get("missing", [])))
    main(a.full, a.skip_network)
