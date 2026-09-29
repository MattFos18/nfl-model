"""Season simulation, two in-season knobs (29 Sep 2026), on the season_backtest.py harness: as of weeks 1, 5, 9, 13, 17 of
every season 2019 to 2025, the same metrics (wins error, division Brier, playoff Brier, Super Bowl log loss), the same
windows (2019-22, 2023-25) and the same adoption rule (better on wins_mae, div_brier and po_brier on both windows).

Part 1, in-season update weight. The ratings the simulation carries into future games are the game model's as-of
ratings (decay 0.94 a week, last season at 0.8). Each team's rating inputs (off_epa_play, own_def_epa_play, off_pf,
own_def_pf, qb_rating; not continuity or record) are pulled toward the league mean of that input as of the week by a
games-played factor, r' = mean + (r - mean) * n / (n + k), n = the team's games played this season (profiles' n_games),
k in {2, 4, 8}; and the opposite, sharpened by (n + k) / n capped at 1.5, k in {1, 2}. Future games only: the week being
priced still comes from the prediction table where the harness uses it. Note n = 0 at week 1, so shrinking collapses
every rating to the league mean there and sharpening sits at its cap.

Part 2, injuries carried forward. The base simulation sets every absence input to zero for future games. Here each
team's absence inputs as of the week (skill_out_value, qb_out, off_snap_out and def_snap_out from its week-w row of the
model's frame, a bye team's from its last game before the week) apply to its future games decayed by d per week ahead,
d in {0.5, 0.75}; the opponent-side inputs (opp_skill_out_value, opp_def_snap_out) follow from the opponent's own
values. Done through the `overrides` argument of season.expected_points from a copy of margin_matrices bound in place
of the module's for the run (season.py itself is untouched); the playoff bracket decays the same way.

Output: reports/season_update.csv (one row per variant x season x as-of week, plus per-week and window means, season =
"mean"), reports/season_update.md. Usage: python experiments/season_update.py [n_sims] [--time].
"""
from __future__ import annotations
import sys, time
import numpy as np, pandas as pd
from pathlib import Path
from multiprocessing import Pool
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from nflmodel import season as SE

OUT, REP = SE.OUT, SE.REP
WEEKS = [1, 5, 9, 13, 17]
SEASONS = list(range(2019, 2026))
WINDOW = {s: "2019-22" if s <= 2022 else "2023-25" for s in SEASONS}
N_SIMS = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 2000
N_PROC = 2
RATING_KEYS = ["off_epa_play", "own_def_epa_play", "off_pf", "own_def_pf", "qb_rating"]
INJ_KEYS = ["skill_out_value", "qb_out", "off_snap_out", "def_snap_out"]
# variant name -> (k shrink toward the mean, k sharpen, d injury decay); None = off
VARIANTS = {"base": (None, None, None),
            "shrink_k2": (2, None, None), "shrink_k4": (4, None, None), "shrink_k8": (8, None, None),
            "sharp_k1": (None, 1, None), "sharp_k2": (None, 2, None),
            "inj_d0.5": (None, None, 0.5), "inj_d0.75": (None, None, 0.75)}
METRICS = ["wins_mae", "pace_mae", "div_brier", "div_brier_leader", "div_brier_flat", "div_ll", "div_ll_flat", "div_hit", "po_brier", "po_brier_flat", "sb_ll", "sb_ll_flat", "conf_ll", "conf_ll_flat", "champ_rank"]
ADOPT_ON = ("wins_mae", "div_brier", "po_brier")


def adjust_profiles(P: dict, k_shrink: int | None, k_sharp: int | None) -> dict:
    """Part 1: each rating input pulled toward (or pushed from) the league mean of the 32 as-of values by the team's games played."""
    Q = {t: dict(v) for t, v in P.items()}
    if k_shrink is None and k_sharp is None:
        return Q
    for key in RATING_KEYS:
        mean = float(np.mean([P[t][key] for t in SE.TEAMS]))
        for t in SE.TEAMS:
            n = P[t]["n_games"]
            if k_shrink is not None:
                fac = n / (n + k_shrink)
            else:
                fac = min(1.5, (n + k_sharp) / n) if n > 0 else 1.5
            Q[t][key] = mean + (P[t][key] - mean) * fac
    return Q


def injuries_asof(f: pd.DataFrame, season: int, week: int) -> dict:
    """Part 2: each team's absence inputs as the game model saw them for its week-`week` game (a bye team's: its last
    game before the week; none: zeros)."""
    out = {}
    fs = f[f.season == season]
    for t, g in fs.groupby("team"):
        g = g.sort_values("week")
        r = g[g.week == week]
        if not len(r):
            r = g[g.week < week]
        out[t] = {k: float(r.iloc[-1][k]) for k in INJ_KEYS} if len(r) else {k: 0.0 for k in INJ_KEYS}
    return out


def margin_matrices_inj(P: dict, fit: dict, game_week: int, dome_of: dict, inj: dict, asof_week: int, d: float) -> tuple[np.ndarray, np.ndarray]:
    """season.margin_matrices with each side's as-of absences carried into the game at d ** (weeks ahead)."""
    fac = d ** max(0, game_week - asof_week)
    TEAMS, IDX, SAME_DIV, ep = SE.TEAMS, SE.IDX, SE.SAME_DIV, SE.expected_points
    n = len(TEAMS); mh = np.zeros((n, n)); mn = np.zeros((n, n))
    ov = {}
    for a in TEAMS:
        for b in TEAMS:
            if a != b:
                ov[(a, b)] = {"qb_out": inj[a]["qb_out"] * fac, "skill_out_value": inj[a]["skill_out_value"] * fac, "off_snap_out": inj[a]["off_snap_out"] * fac,
                              "opp_skill_out_value": inj[b]["skill_out_value"] * fac, "opp_def_snap_out": inj[b]["def_snap_out"] * fac}
    for a in TEAMS:
        for b in TEAMS:
            if a == b:
                continue
            dg = 1.0 if SAME_DIV[IDX[a], IDX[b]] else 0.0
            dm = float(dome_of.get(a, 0.0))
            mh[IDX[a], IDX[b]] = ep(P[a], P[b], fit, 1.0, 0.0, dm, dg, game_week, overrides=ov[(a, b)]) - ep(P[b], P[a], fit, 0.0, 0.0, dm, dg, game_week, overrides=ov[(b, a)])
            mn[IDX[a], IDX[b]] = ep(P[a], P[b], fit, 0.0, 1.0, 0.0, dg, game_week, overrides=ov[(a, b)]) - ep(P[b], P[a], fit, 0.0, 1.0, 0.0, dg, game_week, overrides=ov[(b, a)])
    return mh, mn


def run_variant(name: str, season: int, week: int, games, P, fit, pred, inj, n_sims: int) -> dict:
    k_shrink, k_sharp, d = VARIANTS[name]
    Q = adjust_profiles(P, k_shrink, k_sharp)
    orig = SE.margin_matrices
    if d is not None:
        SE.margin_matrices = lambda P_, fit_, wk, dome_of: margin_matrices_inj(P_, fit_, wk, dome_of, inj, week, d)
    try:
        return SE.simulate(season, week, games, Q, fit, pred, n_sims=n_sims, seed=season * 100 + week)
    finally:
        SE.margin_matrices = orig


_G = {}


def _init():
    _G["games"] = pd.read_parquet(OUT / "games.parquet"); _G["pred"] = pd.read_parquet(OUT / "pred_v3.parquet"); _G["f"] = SE._frame()


def _task(args):
    s, w, n_sims = args
    games, pred, f = _G["games"], _G["pred"], _G["f"]
    act = SE.actuals(games, s)
    if act is None:
        return []
    P = SE.profiles(f, s, w); fit = SE.fit_asof(pred, s, w); inj = injuries_asof(f, s, w)
    rows = []; t0 = time.time()
    for name in VARIANTS:
        t1 = time.time()
        sim = run_variant(name, s, w, games, P, fit, pred, inj, n_sims)
        sc = SE.score(sim, act)
        k_shrink, k_sharp, d = VARIANTS[name]
        rows.append({"variant": name, "k_shrink": k_shrink, "k_sharp": k_sharp, "inj_decay": d, "season": s, "window": WINDOW[s], "asof_week": w, "games_left": sim["games_left"], "secs": round(time.time() - t1, 1), **sc})
    print(f"{s} week {w} done ({time.time() - t0:.0f}s)", flush=True)
    return rows


def main():
    if "--time" in sys.argv:   # one (season, week) with every variant, timed, no output files
        _init()
        for r in _task((2023, 9, N_SIMS)):
            print(r["variant"], r["secs"], "s", {m: round(r[m], 4) for m in ADOPT_ON + ("sb_ll",)})
        return
    t0 = time.time()
    tasks = [(s, w, N_SIMS) for s in SEASONS for w in WEEKS]
    with Pool(N_PROC, initializer=_init) as pool:
        rows = [r for rs in pool.imap_unordered(_task, tasks) for r in rs]
    d = pd.DataFrame(rows).sort_values(["variant", "season", "asof_week"])
    keys = ["variant", "k_shrink", "k_sharp", "inj_decay"]
    means = d.groupby(keys + ["window"], dropna=False)[METRICS].mean().reset_index()
    means["season"] = "mean"; means["asof_week"] = "all"; means["games_left"] = np.nan
    by_week = d.groupby(keys + ["window", "asof_week"], dropna=False)[METRICS].mean().reset_index()
    by_week["season"] = "mean"; by_week["games_left"] = np.nan
    out = pd.concat([d, by_week, means], ignore_index=True)
    base = means[means.variant == "base"].set_index("window")
    verdict = {}
    for v, g in means.groupby("variant"):
        g = g.set_index("window")
        ok = all(g.loc[w, m] < base.loc[w, m] for w in ("2019-22", "2023-25") for m in ADOPT_ON)
        verdict[v] = "base" if v == "base" else ("better on both windows" if ok else "not adopted")
    out["verdict"] = out.variant.map(verdict)
    REP.mkdir(exist_ok=True); out.round(4).to_csv(REP / "season_update.csv", index=False)
    print(means.round(4).sort_values(["window", "wins_mae"]).to_string(index=False))
    print(verdict)
    print(f"total {time.time() - t0:.0f}s, n_sims {N_SIMS}")


if __name__ == "__main__":
    main()
