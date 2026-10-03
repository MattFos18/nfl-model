"""Relative pace in the totals equation (3 Oct 2026). Follow-up to experiments/totals_new_ideas.py V1 (pace, seconds per
snap), chosen after seeing that study's results (snooping caveat in the report). Pre-registered in reports/relative_pace.md.

R1 both teams' pace relative to the league's average as of that week (this season's earlier games, shrunk toward last
season early on); R2 R1 plus neutral-situation pace relative to the league; R3 R1 with the team's pace recency-weighted
(ratings.window, the ratings' decay). Each refit walk-forward 2015-2025 with totals_new_ideas' rebuild of the totals side
(checked equal to the live walk-forward), scored through nflmodel.study_gate; the 50-draw within-season placebo for a
variant that passes parts 1 and 2. Writes reports/relative_pace.{md,csv}.

    python -m experiments.relative_pace
"""
from __future__ import annotations
import sys, time
import numpy as np, pandas as pd
from experiments import totals_new_ideas as T
from nflmodel import model as M, ratings as R, study_gate as G
from nflmodel.features import OUT, ROOT

REP = ROOT / "reports"
WIN, SEASONS = T.WIN, T.SEASONS
SEED, DRAWS = 20261003, 50
TEAM_K, LEAGUE_K = 4.0, 32.0
BASE_T = list(M.TOTAL_FEATS)
FEATS = {"R1": ["rpace_sum"], "R2": ["rpace_sum", "rnpace_sum"], "R3": ["rwpace_sum"]}
NAMES = {"R1": "relative pace", "R2": "relative pace + relative neutral pace", "R3": "recency-weighted relative pace"}


# ---------- inputs, as of before each game ----------
def rel_season(tab: pd.DataFrame, col: str, keys: pd.DataFrame) -> dict:
    """(season, week, team) -> n/(n+4) * (team's this-season mean - league average) + 4/(n+4) * (team's last-season mean -
    last season's league mean). League average: this season's earlier team-games, shrunk toward last season's mean with 32
    team-games of weight. Only weeks before `week` of this season, and last season."""
    t = tab[tab[col].notna()][["season", "week", "team", col]]
    out = {}
    for (s, w), k in keys.groupby(["season", "week"]):
        s, w = int(s), int(w)
        cur = t[(t.season == s) & (t.week < w)]; last = t[t.season == s - 1]
        lg_last = float(last[col].mean()) if len(last) else np.nan
        if len(cur):
            lg = float(cur[col].mean()) if np.isnan(lg_last) else (float(cur[col].sum()) + LEAGUE_K * lg_last) / (len(cur) + LEAGUE_K)
        else:
            lg = lg_last
        prior = (last.groupby("team")[col].mean() - lg_last) if len(last) else pd.Series(dtype=float)
        cg = cur.groupby("team")[col].agg(["mean", "count"])
        for tm in k.team.unique():
            n = float(cg["count"].get(tm, 0.0)); p0 = float(prior.get(tm, 0.0))
            rc = float(cg["mean"].get(tm)) - lg if n > 0 else 0.0
            out[(s, w, tm)] = (n * rc + TEAM_K * p0) / (n + TEAM_K)
    return out


def rel_window(tab: pd.DataFrame, col: str, keys: pd.DataFrame) -> dict:
    """(season, week, team) -> the team's ratings.window weighted mean minus the window's weighted league mean, pulled toward
    0 with 4 games of weight."""
    t = tab[tab[col].notna()][["season", "week", "team", col]]
    out = {}
    for (s, w), k in keys.groupby(["season", "week"]):
        rows, wt = R.window(t, int(s), int(w), R.DEFAULT["decay"], R.DEFAULT["prior"])
        if len(rows) == 0:
            continue
        lg = float(np.average(rows[col].values, weights=wt))
        d = pd.DataFrame({"team": rows.team.values, "x": (rows[col].values - lg) * wt, "w": wt}).groupby("team").sum()
        v = d.x / (d.w + TEAM_K)
        for tm in k.team.unique():
            out[(int(s), int(w), tm)] = float(v.get(tm, 0.0))
    return out


def game_sum(f: pd.DataFrame, off: dict, dfn: dict) -> dict:
    """game_id -> both offenses' plus both defenses' relative values; no earlier data: 0 (the league average)."""
    v = [off.get((s, w, t), 0.0) + dfn.get((s, w, t), 0.0) for s, w, t in zip(f.season, f.week, f.team)]
    return pd.Series(v, index=f.index).groupby(f.game_id.values).sum().to_dict()


def build_inputs(f: pd.DataFrame) -> tuple[dict, dict]:
    keys = f[["season", "week", "team"]].drop_duplicates()
    tg = pd.read_parquet(OUT / "team_games.parquet"); tg = tg[tg.pf.notna()]
    npc = T.neutral_pace_table()
    X = {"rpace_sum": game_sum(f, rel_season(tg, "sec_per_play", keys), rel_season(tg, "def_sec_per_play", keys)),
         "rnpace_sum": game_sum(f, rel_season(npc, "npace", keys), rel_season(npc, "def_npace", keys)),
         "rwpace_sum": game_sum(f, rel_window(tg, "sec_per_play", keys), rel_window(tg, "def_sec_per_play", keys)),
         # V1 of totals_new_ideas, for the drift table only (not a variant here)
         "pace_sum": T.game_sum(f, T.asof_team(tg, "sec_per_play", keys), T.asof_team(tg, "def_sec_per_play", keys))}
    sc = f[f.season.between(2015, 2025) & (f.home == 1)][["game_id", "season"]]
    cov, drift = {}, []
    for k, d in X.items():
        vals = np.array([d.get(g, np.nan) for g in sc.game_id], dtype=float)
        cov[k] = {"games": int(len(vals)), "missing": int(np.isnan(vals).sum()), "mean": float(np.nanmean(vals)), "sd": float(np.nanstd(vals))}
    for s in SEASONS:
        ids = sc.game_id[sc.season == s]
        drift.append({"season": s, **{k: round(float(np.nanmean([X[k].get(g, np.nan) for g in ids])), 3) for k in X}})
    return X, {"cov": cov, "drift": drift}


def main():
    t0 = time.time()
    f0 = M.with_trends(pd.read_parquet(OUT / "features_asof.parquet"))
    with M.trees_cache_read_only():
        live = M.walk_forward(f0, SEASONS, M.RIDGE)
    print(f"live walk-forward {time.time() - t0:.0f}s", flush=True)
    fp = M.prep(f0); played = fp[fp.pf.notna()]; fpr = M.priced_weather(fp)
    X, info = build_inputs(fp); print("inputs", info["cov"], f"{time.time() - t0:.0f}s", flush=True)
    tb = T.totals_wf(fp, played, fpr, X, BASE_T)
    chk = live[["game_id", "model_total", "p_over_emp"]].merge(tb, on="game_id", suffixes=("", "_re"))
    dmt, dpo = float((chk.model_total - chk.model_total_re).abs().max()), float((chk.p_over_emp - chk.p_over_emp_re).abs().max())
    print(f"rebuilt base vs live walk-forward: {len(chk)} of {len(live)} games, max diff total {dmt:.2e}, over chance {dpo:.2e}", flush=True)
    if len(chk) != len(live) or dmt > 1e-9 or dpo > 1e-9:
        sys.exit("the rebuilt totals side does not reproduce the live walk-forward")
    res = {"base": T.score(live)}
    for v, fs in FEATS.items():
        t = T.totals_wf(fp, played, fpr, X, BASE_T + fs); res[v] = T.score(T.merged(live, t))
        print(v, {w: (round(res[v][w]["total"], 4), "%d-%d" % res[v][w]["totals"]) for w in WIN}, f"{time.time() - t0:.0f}s", flush=True)
    gates = {v: T.gate_rows(res["base"], res[v], "V1") for v in FEATS}
    games_f = fp[fp.home == 1][["game_id", "season"]].drop_duplicates("game_id")
    ids = games_f.game_id.values; seas = games_f.season.values
    placebo = {}
    for v, fs in FEATS.items():
        if not T.p12(gates[v]):
            continue
        rng = np.random.default_rng(SEED); gains = {w: [] for w in WIN}
        for i in range(DRAWS):
            perm = G.shuffle_within_season(np.arange(len(ids), dtype=float), seas, rng).astype(int)   # one shuffle for all of a variant's inputs
            Xs = dict(X)
            for k in fs:
                vals = np.array([X[k].get(g, np.nan) for g in ids]); Xs[k] = dict(zip(ids, vals[perm]))
            sc_ = T.score(T.merged(live, T.totals_wf(fp, played, fpr, Xs, BASE_T + fs)))
            for w in WIN:
                gains[w].append(res["base"][w]["total"] - sc_[w]["total"])
            print(f"{v} placebo {i + 1}/{DRAWS}", {w: round(gains[w][-1], 4) for w in WIN}, f"{time.time() - t0:.0f}s", flush=True)
        placebo[v] = gains; gates[v] = T.gate_rows(res["base"], res[v], "V1", gains)
        pd.DataFrame(gains).to_csv(REP / f"relative_pace_placebo_{v}.csv", index=False)
    rows = [{"variant": v, "name": NAMES.get(v, v), "window": w, "total_miss": round(sc[w]["total"], 4), "over_logloss": round(sc[w]["logloss"], 5),
             "team_miss": round(sc[w]["team"], 4), "spread_flag": "%d-%d" % sc[w]["spread"], "totals_flag": "%d-%d" % sc[w]["totals"],
             "totals_units": sc[w]["units"], "wind_under": "%d-%d" % sc[w]["wind"]} for v, sc in res.items() for w in WIN]
    pd.DataFrame(rows).to_csv(REP / "relative_pace.csv", index=False)
    md = REP / "relative_pace.md"; old = md.read_text(encoding="utf-8"); head = old.split("\n## Results")[0]
    tail = ("\n## Decision" + old.split("\n## Decision", 1)[1]) if "\n## Decision" in old else ""
    L = [head.rstrip(), "", "## Results", "",
         f"Rebuilt totals side against the live walk-forward: {len(chk)} games, largest difference {dmt:.1e} points in the total and {dpo:.1e} in the over chance.", "",
         "Inputs, regular-season games 2015-2025 (one value per game; `pace_sum` is totals_new_ideas' V1, shown for the drift only):", "",
         "| Input | Games | Missing | Mean | SD |", "|---|---|---|---|---|"]
    L += [f"| {k} | {c['games']} | {c['missing']} | {c['mean']:.4f} | {c['sd']:.4f} |" for k, c in info["cov"].items()]
    L += ["", "Season mean of each input (seconds; the absolute V1 input drifts with the league, the relative ones should sit near 0):", "",
          "| Season | " + " | ".join(X) + " |", "|---|" + "---|" * len(X)]
    L += [f"| {d['season']} | " + " | ".join(f"{d[k]:.3f}" for k in X) + " |" for d in info["drift"]]
    L += ["", "Each variant refit walk-forward 2015-2025, regular season scored; flags at the live rules, weeks 1-17; totals units at -110.", "",
          "| Variant | Window | Total miss | Over log loss | Team miss | Spread flag | Totals flag | Totals units | Wind under |", "|---|---|---|---|---|---|---|---|---|"]
    L += [f"| {r['variant']} {r['name'] if r['variant'] in NAMES else ''} | {r['window']} | {r['total_miss']:.4f} | {r['over_logloss']:.5f} | {r['team_miss']:.4f} | {r['spread_flag']} | {r['totals_flag']} | {r['totals_units']:+.2f} | {r['wind_under']} |" for r in rows]
    for v, g_ in gates.items():
        L += ["", f"## Gate, {v} {NAMES[v]}" + ("" if v in placebo else " (parts 1 and 2; the placebo runs only for a variant that passes them)"), "", G.markdown(g_)]
    md.write_text("\n".join(L) + "\n" + tail, encoding="utf-8")
    print("\n".join(L)); print(f"done {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
