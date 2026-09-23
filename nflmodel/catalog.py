"""Data catalog (23 Sep 2026): every data store the model keeps, what it holds, how big it is, when it was built, which
step writes it and where it shows on the site. Exported to web/data/catalog.js by export_web (Model -> Every data store).

Raw downloads (data/raw, git-ignored, rebuilt by pull.py and cached on the runner) are read from the files on disk
and the pull log; built tables (data/processed) from the files; the line, weather, tracker and run logs from their
CSVs; reports and the page's own files by listing. Columns come from the file itself (parquet schema or CSV header),
never from a hand-kept list, so the catalog cannot drift from the data.
"""
from __future__ import annotations
import datetime as dt, json
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW, OUT, LN, TR, WX, RUNS, REP, WEB = ROOT / "data" / "raw", ROOT / "data" / "processed", ROOT / "data" / "lines", ROOT / "data" / "tracker", ROOT / "data" / "weather", ROOT / "data" / "runs", ROOT / "reports", ROOT / "web" / "data"

RAW_WHAT = {
    "schedules": ("nflverse schedules: every game 1999 on with kickoff, teams, scores, closing spread, total and moneylines, roof, surface, weather at kickoff, QBs, coaches, referee", "pull", "games.parquet; This week, Team game logs"),
    "pbp": ("nflverse play-by-play: every play with EPA, success, win probability, the players involved, formation and personnel where charted", "pull", "team_games, scheme_plays, player logs, props"),
    "injuries": ("nflverse injury reports (the league's Wednesday to Friday reports, with a lag); beside it espn_injuries.csv, ESPN's same-day page pulled every run", "pull", "players.load_injuries: absences in the game model, rosters, props"),
    "snap_counts": ("nflverse snap counts per player-game (offense, defense, special teams, share)", "pull", "snaps-out inputs (trends), roster snap shares"),
    "depth_charts": ("nflverse depth charts by week", "pull", "Team -> Roster and depth chart"),
    "rosters": ("nflverse weekly rosters: status (active, IR, practice squad), position, ids", "pull", "who is available; player season totals"),
    "ftn": ("FTN charting 2022 on: motion, play action, RPO, screens, blitzers and pass rushers, box count, QB location, out of pocket, catchable and contested balls, interception-worthy throws, trick plays", "pull", "scheme profiles, player splits (no route data: no public source charts routes)"),
    "participation": ("nflverse participation 2016 on: offense and defense personnel, players on the field, defenders in box, pass rushers, coverage type (man or zone, coverage family), time to throw, pressure", "pull", "scheme profiles, player splits (2026 not published yet)"),
    "pfr_advstats": ("Pro-Football-Reference advanced stats by week (pressures, hurries, drops, air yards)", "pull", "readings"),
}
PROCESSED_WHAT = {
    "games.parquet": ("one row per game: schedule, kickoff in ET, scores, closing lines, roof, weather, QBs; the spine every table joins to", "build", "everywhere"),
    "team_games.parquet": ("one row per team-game: box score, EPA and success by play type, pace, situation", "build", "Team -> Game log; ratings"),
    "team_box.parquet": ("one row per team-game: the box score (yards, turnovers, penalties, third downs, time of possession)", "build", "Team -> Game log"),
    "features_asof.parquet": ("one row per team-game: the ratings and QB each side carried into the game (nothing from the game itself), the situation, the closing line", "features", "the game model's input frame; Team -> Ratings; Rankings"),
    "trends_asof.parquet": ("one row per team-game: situational trends and absences as of the game (home edge, head-to-head, coach and QB against the spread, referee rates, rest, travel, starters out, QB out, snaps out, continuity)", "trends", "game model inputs; card 'Why these numbers'"),
    "player_injury.parquet": ("one row per team-game: value lost to skill players listed out (the player model), own and opponent", "players", "game model inputs"),
    "player_values.parquet": ("every rostered skill player valued as of the coming week (EPA per touch above replacement, share, touches)", "players", "Players tab; Team -> Roster"),
    "player_values_all.parquet": ("the same for every player on a roster, every unit", "players", "Players tab"),
    "player_history.parquet": ("one row per player-season-team-role: games, plays, EPA", "players", "Players tab history"),
    "player_games.parquet": ("one row per player-game-role: plays and EPA", "players", "Players tab game log"),
    "roster_now.parquet": ("the current roster with depth chart slot, injury report, practice status, snap shares and value", "players", "Team -> Roster and depth chart"),
    "positions_asof.parquet": ("position-group values as of each game (OL, skill, defense, kickers)", "positions", "Rankings -> Positions"),
    "special_teams_asof.parquet": ("special-teams readings as of each game", "positions", "Rankings -> Positions"),
    "scheme_plays.parquet": ("every pass and run since 2016 tagged with the look: formation, personnel, box, rushers, blitz, pressure, coverage, motion, play action, RPO, screen, tempo (participation and FTN joined to the play-by-play)", "scheme", "scheme profiles, player splits, props, player logs"),
    "scheme_profiles.json": ("each team's offense and defense profile over its last 17 games (rates, tendencies, EPA by look) and the league's, as of the current week", "scheme", "Team -> Scheme; card Scheme matchup"),
    "qb_games.parquet": ("one row per QB-game: dropbacks, EPA per dropback, the inputs of the QB rating", "ratings", "QB rating; Rankings"),
    "def_games.parquet": ("one row per defense-game: plays faced, tackles, sacks by defender (for the defender props)", "props", "props (defenders)"),
    "defender_games.parquet": ("one row per defender-game: tackles, solo tackles, sacks, plays faced", "props", "props (defenders); Players tab"),
    "kicking_games.parquet": ("one row per kicker-game: field goals and extra points attempted and made, kicking points", "props", "props (kickers)"),
    "pred_v3.parquet": ("one row per game since 2015: the model's expected points, spread, total, win and cover odds, and the fit that priced it (coefficients, means, intercept, residual scale)", "model", "This week, Backtest, Season"),
    "pred_baseline.parquet": ("the old spreadsheet model's predictions, for the record", "baseline", "reports/baseline_backtest.md"),
    "props.json": ("this week's player projections for every game with the book lines beside them, the rule's constants and the record", "props", "card Player props; Players tab"),
    "props_profiles.json": ("every player's last-17 profile with splits, every defense and the league", "props", "Players tab"),
}
LOG_WHAT = {
    "lines/lines_log.csv": ("every game line snapshot from the line watch (ESPN scoreboard provider line, DraftKings when reachable, The Odds API books): spread, total, moneylines, timestamp", "line watch (every 10 minutes)", "cards: Vegas line, line history, best number"),
    "lines/props_log.csv": ("every player prop line pulled (The Odds API books, PrizePicks, Underdog): stat, line, prices, timestamp", "line watch", "card Player props; props record"),
    "lines/watch_log.csv": ("one row per line-watch run: rows logged, errors", "line watch", "health"),
    "lines/raw": ("the raw JSON and HTML of every source pull, by timestamp", "line watch", "the record"),
    "weather/forecast_latest.csv": ("the latest Open-Meteo kickoff forecast per unplayed outdoor game", "weekly run", "cards; game model wind, cold, rain"),
    "weather/forecast_log.csv": ("every forecast pulled, by run", "weekly run", "the record"),
    "weather/archive_kickoff.csv": ("weather at kickoff for played games (Open-Meteo archive)", "weather archive workflow", "backtest inputs"),
    "tracker/model_picks.csv": ("every model flag with the line at the run, graded with closing line value", "weekly run", "Bets tab"),
    "tracker/my_bets.csv": ("Matt's bets", "hand-kept", "Bets tab"),
    "tracker/graded.csv": ("graded picks and bets", "weekly run", "Bets tab"),
    "tracker/shadow45_picks.csv": ("the 4.5+ edge shadow rule, logged never bet", "weekly run", "Bets tab"),
    "tracker/shadowdog_picks.csv": ("the 4+ edge, underdog side shadow rule", "weekly run", "Bets tab"),
    "tracker/shadowearly_picks.csv": ("the 4+ edge, weeks 1 to 13 shadow rule", "weekly run", "Bets tab"),
    "tracker/props_graded.csv": ("every player projection graded against what happened, live or after the fact", "weekly run", "Backtest -> Player projections, live"),
    "tracker/props_vs_market.csv": ("every graded projection with a closing book line: side, result, both errors", "weekly run", "Backtest -> Player projections"),
    "runs/run_log.csv": ("every weekly run: each step's status and seconds", "weekly run", "health"),
    "runs/pred_history.csv": ("every run's prediction for every game of the week (the model's own line history)", "weekly run", "cards: how the model's number moved"),
    "raw/pull_log.csv": ("every raw download with its size and hash", "pull", "Model -> Data pulls"),
    "raw/injuries/espn_injuries.csv": ("ESPN's injury page, every team, as pulled", "pull", "players.load_injuries fill"),
}


def _mb(n: int) -> float:
    return round(n / 1e6, 2)


def _parquet_meta(f: Path) -> tuple[int, list]:
    try:
        import pyarrow.parquet as pq
        m = pq.ParquetFile(f)
        return int(m.metadata.num_rows), [c for c in m.schema_arrow.names]
    except Exception:  # noqa
        return -1, []


def _csv_meta(f: Path) -> tuple[int, list]:
    try:
        cols = pd.read_csv(f, nrows=0).columns.tolist()
        n = sum(1 for _ in open(f, "rb")) - 1
        return n, cols
    except Exception:  # noqa
        return -1, []


def _mtime(f: Path) -> str:
    return dt.datetime.utcfromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M UTC")


def build() -> dict:
    out = {"built": pd.Timestamp.now("UTC").strftime("%Y-%m-%d %H:%M UTC"), "raw": [], "processed": [], "logs": [], "reports": [], "page": []}
    pull = pd.read_csv(RAW / "pull_log.csv") if (RAW / "pull_log.csv").exists() else pd.DataFrame(columns=["pulled_at", "dataset", "season", "status", "bytes"])
    for name, (what, step, shows) in RAW_WHAT.items():
        d = RAW / name
        files = sorted(d.glob("*.parquet")) + sorted(d.glob("*.csv")) if d.exists() else []
        seasons = sorted({int(s) for f in files for s in [f.stem.split("_")[-1]] if s.isdigit()})
        latest = [f for f in files if f.suffix == ".parquet"]; latest = latest[-1] if latest else (files[-1] if files else None)
        rows, cols = (_parquet_meta(latest) if latest and latest.suffix == ".parquet" else (_csv_meta(latest) if latest else (-1, [])))
        pl = pull[pull.dataset == name]
        out["raw"].append({"name": name, "what": what, "step": step, "shows": shows, "files": len(files), "seasons": (f"{seasons[0]} to {seasons[-1]}" if seasons else ("one file" if files else "not on this machine")),
                           "mb": _mb(sum(f.stat().st_size for f in files)), "latest_file": (latest.name if latest else None), "latest_rows": rows, "columns": cols, "last_pulled": (str(pl.iloc[-1].pulled_at) if len(pl) and "pulled_at" in pl.columns else None)})
    for f in sorted(OUT.iterdir()):
        if not f.is_file():
            continue
        what, step, shows = PROCESSED_WHAT.get(f.name, ("", "", ""))
        if f.suffix == ".parquet":
            rows, cols = _parquet_meta(f)
        elif f.suffix == ".json":
            try:
                j = json.loads(f.read_text()); rows = len(j) if isinstance(j, list) else len(j.get("games", j) if isinstance(j, dict) else j); cols = list(j)[:60] if isinstance(j, dict) else []
            except Exception:  # noqa
                rows, cols = -1, []
        else:
            rows, cols = _csv_meta(f)
        out["processed"].append({"name": f.name, "what": what, "step": step, "shows": shows, "rows": rows, "n_cols": len(cols), "columns": cols, "mb": _mb(f.stat().st_size), "built": _mtime(f)})
    for rel, (what, step, shows) in LOG_WHAT.items():
        f = ROOT / "data" / rel
        if f.is_dir():
            files = list(f.iterdir()); out["logs"].append({"name": rel, "what": what, "step": step, "shows": shows, "rows": len(files), "columns": [], "mb": _mb(sum(x.stat().st_size for x in files if x.is_file())), "built": (_mtime(max(files, key=lambda x: x.stat().st_mtime)) if files else None)})
        elif f.exists():
            rows, cols = _csv_meta(f); out["logs"].append({"name": rel, "what": what, "step": step, "shows": shows, "rows": rows, "columns": cols, "mb": _mb(f.stat().st_size), "built": _mtime(f)})
        else:
            out["logs"].append({"name": rel, "what": what, "step": step, "shows": shows, "rows": 0, "columns": [], "mb": 0.0, "built": None, "missing": True})
    for f in sorted(REP.iterdir()):
        if f.is_file():
            rows, cols = _csv_meta(f) if f.suffix == ".csv" else (-1, [])
            out["reports"].append({"name": f.name, "rows": rows, "columns": cols, "mb": _mb(f.stat().st_size), "built": _mtime(f)})
    for f in sorted(WEB.iterdir()):
        if f.is_file():
            out["page"].append({"name": f.name, "mb": _mb(f.stat().st_size), "built": _mtime(f)})
    out["totals"] = {"raw_mb": round(sum(r["mb"] for r in out["raw"]), 1), "processed_mb": round(sum(r["mb"] for r in out["processed"]), 1), "logs_mb": round(sum(r["mb"] for r in out["logs"]), 1), "page_mb": round(sum(r["mb"] for r in out["page"]), 1)}
    out["routes"] = "No public source charts routes run. FTN (2022 on) charts motion, play action, RPO, screens, blitzers and pass rushers, the box, QB location and pocket, catchable and contested balls; nflverse participation (2016 on) gives personnel, the players on the field, coverage (man or zone and the coverage family), time to throw and pressure. Depth of target and air yards come from the play-by-play. Those are the route-adjacent readings the site carries (Players tab splits, Team -> Scheme)."
    return out


if __name__ == "__main__":
    c = build()
    print(json.dumps({k: (len(v) if isinstance(v, list) else v) for k, v in c.items() if k != "routes"}, indent=1))
