"""Data checks (1 Oct 2026): the tables the model reads have the shape they must have, before anything is priced.

verify.py checks the numbers against published sources; health.py checks that runs happened and are fresh. This checks
the tables themselves: columns present, one row per game, every team's full schedule, scores and lines in range, the
two team rows of a game mirroring each other, predictions for every graded game; and (2 Oct 2026, data audit) the inputs
nflverse got wrong before: a played game's listed starting QB who took no dropback, a game abroad or at a neutral site
listed at a home stadium or under a dome it does not have, a kickoff wind no game reaches. A failure is a step error in the
weekly run (data/runs/run_log.csv), which health.py turns into a site-health issue; the run itself carries on.

Usage: python -m nflmodel.data_checks   (writes reports/data_checks.md, exits 1 if any check fails)
"""
from __future__ import annotations
import sys
import numpy as np, pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT, REP = ROOT / "data" / "processed", ROOT / "reports"
FIRST = 2015   # the backtest's first season
GAME_COLS = ["game_id", "season", "game_type", "week", "kickoff_et", "away_team", "home_team", "away_score", "home_score",
             "result", "total", "spread_line", "total_line", "roof", "neutral", "div_game"]
# regular-season games per team: 16 to 2020, 17 from 2021; BUF-CIN (2 Jan 2023) was cancelled and never replayed
SHORT = {(2022, "BUF"): 16, (2022, "CIN"): 16}


def _games_per_team(season: int) -> int:
    return 16 if season <= 2020 else 17


def check(games: pd.DataFrame, team_games: pd.DataFrame, pred: pd.DataFrame | None = None) -> list[tuple[str, bool, str]]:
    rows = []
    def add(what, ok, detail): rows.append((what, bool(ok), detail))
    miss = [c for c in GAME_COLS if c not in games.columns]
    add("games: every column the model reads", not miss, f"missing {miss}" if miss else f"{len(GAME_COLS)} present")
    if miss:
        return rows
    dup = games.game_id.duplicated().sum()
    add("games: one row per game", dup == 0, f"{dup} duplicate game ids")
    reg = games[(games.game_type == "REG") & (games.season >= FIRST)]
    played = reg[reg.home_score.notna()]
    # every finished season: each team's full regular season
    bad = []
    done = [s for s in sorted(reg.season.unique()) if reg[reg.season == s].home_score.notna().all()]
    for s in done:
        r = reg[reg.season == s]; n = pd.concat([r.home_team, r.away_team]).value_counts()
        for t, k in n.items():
            if k != SHORT.get((s, t), _games_per_team(s)):
                bad.append(f"{s} {t} {k}")
        if len(n) != 32:
            bad.append(f"{s}: {len(n)} teams")
    add("games: every team's full regular season (finished seasons)", not bad, "; ".join(bad[:8]) or f"{len(done)} seasons, {FIRST} to {max(done) if done else '-'}")
    # this season: no team plays twice in a week
    cur = reg[reg.season == reg.season.max()]
    twice = pd.concat([cur[["week", "home_team"]].rename(columns={"home_team": "t"}), cur[["week", "away_team"]].rename(columns={"away_team": "t"})]).duplicated().sum()
    add("games: no team twice in one week", twice == 0, f"{twice} repeats in {int(cur.season.max()) if len(cur) else '-'}")
    sc = played[["home_score", "away_score"]]
    add("games: scores whole numbers from 0 to 80", bool(((sc >= 0) & (sc <= 80) & (sc % 1 == 0)).all().all()), f"{len(played)} played games")
    arith = ((played.result != played.home_score - played.away_score) | (played.total != played.home_score + played.away_score)).sum()
    add("games: result and total add up from the scores", arith == 0, f"{arith} games off")
    nol = played.spread_line.isna().sum() + played.total_line.isna().sum()
    add("games: closing spread and total for every played game", nol == 0, f"{nol} missing")
    rng_bad = int((played.spread_line.abs() > 30).sum() + (~played.total_line.between(25, 70)).sum())
    add("games: lines in range (spread within 30, total 25 to 70)", rng_bad == 0, f"{rng_bad} out of range")
    # team_games: two mirrored rows per game
    tg = team_games[(team_games.game_type == "REG") & (team_games.season >= FIRST) & team_games.pf.notna()]
    per = tg.groupby("game_id").size()
    add("team games: two rows per played game", bool((per == 2).all()) and set(per.index) == set(played.game_id),
        f"{int((per != 2).sum())} games without two rows; {len(set(played.game_id) - set(per.index))} played games missing")
    m = tg.merge(tg[["game_id", "team", "pf", "pa"]], left_on=["game_id", "opp"], right_on=["game_id", "team"], suffixes=("", "_o"))
    mir = int(((m.pf != m.pa_o) | (m.pa != m.pf_o)).sum())
    add("team games: each side's points mirror the other's", mir == 0, f"{mir} rows off")
    if pred is not None:
        need = ["game_id", "home_exp", "away_exp", "model_spread", "model_total"]
        pm = [c for c in need if c not in pred.columns]
        add("predictions: every column the page and records read", not pm, f"missing {pm}" if pm else "present")
        if not pm:
            p = pred[pred.game_id.isin(reg.game_id)]
            add("predictions: one row per game", p.game_id.duplicated().sum() == 0, f"{int(p.game_id.duplicated().sum())} duplicates")
            gone = sorted(set(played.game_id) - set(p.game_id))
            add("predictions: every played regular-season game priced", not gone, f"{len(gone)} missing" + (f": {', '.join(gone[:5])}" if gone else ""))
            v = p[need[1:]]
            ok = np.isfinite(v.values).all() and p.model_total.between(20, 75).all() and (p.model_spread.abs() <= 35).all()
            add("predictions: finite and in range (total 20 to 75, spread within 35)", ok, f"{len(p)} games")
    return rows


WIND_MAX = 40.0   # mph (build.WIND_MAX): the windiest real kickoff in the data is 35 mph (2020_08_LV_CLE, forecast 36.8)


def check_inputs(games: pd.DataFrame, qb: pd.DataFrame | None = None) -> list[tuple[str, bool, str]]:
    """The schedule inputs the 2 Oct 2026 audit found wrong, after build.py's fixes (build.fix_starters, venues.fix_venues,
    build.fix_wind)."""
    from .venues import venue_problems
    rows = []
    def add(what, ok, detail): rows.append((what, bool(ok), detail))
    g = games[games.season >= FIRST]
    if qb is not None:
        played = g[g.home_score.notna()]
        have = set(zip(qb.game_id, qb.team)); dropped = set(zip(qb.game_id, qb.team, qb.qb_id))
        bad = []
        for side in ("home", "away"):
            for gid, t, q in zip(played.game_id, played[f"{side}_team"], played[f"{side}_qb_id"]):
                if (gid, t) in have and (gid, t, q) not in dropped:
                    bad.append(f"{gid} {t}")
        add("games: every played game's starting QB dropped back in it", not bad, f"{len(bad)} team-games" + (f": {', '.join(bad[:6])}" if bad else ""))
    vp = venue_problems(g)
    add("games: neutral-site and overseas games at their real stadium and roof (venues.py)", not vp, f"{len(vp)} games" + (f": {', '.join(vp[:6])}" if vp else ""))
    w = pd.to_numeric(g.wind, errors="coerce")
    hi = g.game_id[w > WIND_MAX].tolist()
    add(f"games: kickoff wind {WIND_MAX:g} mph or under", not hi, f"{len(hi)} games" + (f": {', '.join(hi[:6])}" if hi else ""))
    return rows


def main() -> bool:
    games = pd.read_parquet(OUT / "games.parquet"); tg = pd.read_parquet(OUT / "team_games.parquet")
    pf = OUT / "pred_v3.parquet"; pred = pd.read_parquet(pf) if pf.exists() else None
    qf = OUT / "qb_games.parquet"; qb = pd.read_parquet(qf, columns=["game_id", "team", "qb_id"]) if qf.exists() else None
    rows = check(games, tg, pred) + check_inputs(games, qb); ok = all(r[1] for r in rows)
    L = ["# Data checks", "", "The tables the model reads, checked for shape before pricing (nflmodel/data_checks.py).", "",
         "| Check | Passes | Detail |", "|---|---|---|"] + [f"| {w} | {'yes' if o else 'NO'} | {d} |" for w, o, d in rows]
    L += ["", f"Result: {'PASS' if ok else 'FAIL'} ({sum(r[1] for r in rows)} of {len(rows)})"]
    REP.mkdir(exist_ok=True); (REP / "data_checks.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(L[-1])
    return ok


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
