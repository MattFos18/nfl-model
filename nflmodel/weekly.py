"""The weekly run. Tuesday (after MNF) does everything; Saturday refreshes lines, weather and the picks.

Steps, each logged to data/runs/run_log.csv with its status; a failed pull is reported, never papered over:
  1. pull      nflverse schedules, play-by-play, injuries, snap counts for the current season (and last, once)
  2. build     games.parquet, team_games.parquet, team_box.parquet, qb_games.parquet
  3. verify    the accuracy checks; the run stops if scores or mirrors break
  4. weather   kickoff forecasts for the next 10 days (Open-Meteo), applied to unplayed outdoor games
  5. ratings   as-of feature table, trends and injuries
  6. model     3.0 walk-forward through the current season; old model too for the comparison column
  7. grade     last week's flagged picks and Matt's bets (tracker), closing line value where a line was logged
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


def step(name, fn, log):
    t0 = time.time()
    try:
        out = fn()
        log.append({"step": name, "status": "ok", "detail": str(out)[:200] if out is not None else "", "seconds": round(time.time() - t0, 1)})
        print(f"[ok] {name} ({time.time() - t0:.0f}s)", flush=True)
        return out
    except Exception as e:  # noqa
        log.append({"step": name, "status": "error", "detail": f"{type(e).__name__}: {str(e)[:200]}", "seconds": round(time.time() - t0, 1)})
        print(f"[ERROR] {name}: {e}", flush=True)
        traceback.print_exc()
        return None


def sh(cmd):
    r = subprocess.run([sys.executable, "-m"] + cmd, cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError((r.stderr or r.stdout)[-400:])
    return (r.stdout or "").strip().splitlines()[-1] if r.stdout.strip() else ""


def main(full=False, skip_network=False):
    from . import pull, picks as P, tracker, weather, export_web, tie_check
    log = []
    run_at = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    games0 = pd.read_parquet(OUT / "games.parquet")
    season = int(games0.season.max())
    if not skip_network:
        seasons = list(range(2012, season + 1)) if full else [season - 1, season]
        step("pull", lambda: pull.pull(seasons, ["schedules", "pbp", "injuries", "snap_counts", "rosters", "depth_charts", "pfr_advstats", "pfr_pass", "pfr_rush", "pfr_rec", "participation", "ftn"]), log)
    step("build", lambda: sh(["nflmodel.build"]), log)
    step("features", lambda: sh(["nflmodel.features"]), log)
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
    step("ratings", lambda: sh(["nflmodel.ratings"]), log)
    step("trends", lambda: sh(["nflmodel.trends"]), log)
    step("players", lambda: sh(["nflmodel.players"]), log)
    step("positions", lambda: sh(["nflmodel.positions"]), log)
    step("scheme", lambda: sh(["nflmodel.scheme"]), log)   # scheme and play-calling profiles (readings; participation and FTN charting)
    step("props", lambda: sh(["nflmodel.props"]), log)     # player-against-scheme projections for the week, and last week's graded
    step("model", lambda: sh(["nflmodel.model", "--seasons", f"2015-{season}"]), log)   # 2015 to 2018 priced too (untouched by every choice; shown, never tuned on)
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
    step("audit reports", lambda: sh(["nflmodel.report"]), log)
    step("legitimacy tests", lambda: sh(["experiments.legitimacy"]), log)
    _write(log, run_at, cur_season, cur_week, pk)
    return log


def _write(log, run_at, season, week, pk, halted=False):
    RUNS.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(log).assign(run_at=run_at)
    df.to_csv(RUNS / "run_log.csv", mode="a", header=not (RUNS / "run_log.csv").exists(), index=False)
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
    ap.add_argument("--skip-network", action="store_true")
    a = ap.parse_args()
    main(a.full, a.skip_network)
