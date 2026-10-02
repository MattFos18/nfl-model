"""Questionable players in the totals equation only (2 Oct 2026).

Lead, found by looking at results (so a snooping caveat): in experiments/injury_retest.py (1 Oct 2026) variant Q2,
Questionable players at every position priced at the chance they sit, lowered the team points miss on every window and
helped the totals flag on all three, but cost the spread flag. Here the same input goes into the totals equation only
(model.TOTAL_FEATS); the points equations (model.FEATS), and so the spread, are untouched.

Variants, pre-registered in reports/questionable_totals.md before the results, each refit walk-forward 2015-2025:
  T1  three totals inputs summed over both teams: q_skill_sum (Questionable skill value out times the chance to sit),
      q_off_sum (Questionable offensive snap share times the chance), q_def_sum (the same for defensive snaps).
  T2  T1, and the totals' qb_out_sum takes each team's max(qb_out, chance last game's starter sits). Primary.
The input is injury_retest's (experiments.injury_retest.build: rates from earlier seasons only, last game's snaps).
Scored through nflmodel.study_gate on the total miss (2015-18 / 2019-22 / 2023-25, regular season) with the spread flag
(4+), the totals flag (55%+ under) and the wind under (10+ mph), weeks 1-17, for no bet cost; a variant that passes those
gets the placebo: its four pieces of each team-game moved together to another team-game of the same season
(study_gate.shuffle_within_season on the row index), 50 draws, seed 20261002. Writes reports/questionable_totals.{md,csv}.

    python -m experiments.questionable_totals
"""
from __future__ import annotations
import time
import numpy as np, pandas as pd
from nflmodel import backtest as B, model as M, picks as P, study_gate as G
from nflmodel.features import OUT, ROOT
from experiments import injury_retest as IR

REP = ROOT / "reports"
WIN = {"2015-18": (2015, 2018), "2019-22": (2019, 2022), "2023-25": (2023, 2025)}
GAMES = pd.read_parquet(OUT / "games.parquet")
SEED, DRAWS = 20261002, 50
PIECES = {"q_skill": "q1_skill", "q_off": "q2_off", "q_def": "q2_def", "q_qb": "q2_qb"}
BASE_T = list(M.TOTAL_FEATS)
VARIANTS = {"T1": BASE_T + ["q_skill_sum", "q_off_sum", "q_def_sum"],
            "T2": [("qb_out_t_sum" if c == "qb_out_sum" else c) for c in BASE_T] + ["q_skill_sum", "q_off_sum", "q_def_sum"]}
_GF = M._game_frame


def game_frame(f: pd.DataFrame) -> pd.DataFrame:
    """model._game_frame plus the Questionable sums over both teams (same game order)."""
    g = _GF(f)
    h, a = f[f.home == 1].set_index("game_id"), f[f.home == 0].set_index("game_id"); ids = h.index.intersection(a.index)
    for c in ("q_skill", "q_off", "q_def", "qb_out_t"):
        if c in f.columns:
            g[c + "_sum"] = (h.loc[ids, c] + a.loc[ids, c]).values
    return g


def attach(f0: pd.DataFrame, X: pd.DataFrame) -> pd.DataFrame:
    """Each team-game's own Questionable pieces (zero where it has none: postseason, 2013, no report)."""
    f = f0.copy(); x = X.set_index(["game_id", "team"]); own = pd.MultiIndex.from_arrays([f.game_id, f.team])
    for c, src in PIECES.items():
        f[c] = x[src].reindex(own).fillna(0.0).values
    f["qb_out_t"] = np.maximum(f.qb_out.values, f.q_qb.values)
    return f


def score(pred: pd.DataFrame) -> dict:
    d = B.join(pred, GAMES); d = d[(d.game_type == "REG") & d.season.between(2015, 2025)]
    out = {"by_season": d.groupby("season").total_err.apply(lambda e: float(e.abs().mean())).to_dict()}
    for w, (lo, hi) in WIN.items():
        x = d[d.season.between(lo, hi)]
        out[w] = {"total": float(x.total_err.abs().mean()), "team": float(np.r_[x.home_err.abs(), x.away_err.abs()].mean()),
                  "margin": float(x.margin_err.abs().mean()),
                  "spread": P.record(x, P.rule_mask(x, P.SPREAD_EDGE)),
                  "totals": P.record(x, P.rule_mask(x, P.TOTAL_SHADOW["prob"], "under_prob"), "under_prob"),
                  "wind": P.record(x, P.rule_mask(x, P.WIND_UNDER["mph"], "wind_under"), "wind_under")}
    return out


def run(f: pd.DataFrame, feats: list[str]) -> dict:
    M.TOTAL_FEATS, M._game_frame = list(feats), game_frame
    try:
        return score(M.walk_forward(f, range(2015, 2026), M.RIDGE))
    finally:
        M.TOTAL_FEATS, M._game_frame = BASE_T, _GF


def gate_rows(base, new, placebo=None):
    return G.gate({w: (base[w]["total"], new[w]["total"]) for w in WIN},
                  {w: {"spread flag": (base[w]["spread"], new[w]["spread"]), "totals flag": (base[w]["totals"], new[w]["totals"]),
                       "wind under": (base[w]["wind"], new[w]["wind"])} for w in WIN}, placebo)


def p12(rows) -> bool:
    return all(ok for what, ok, _ in rows if not what.startswith("beats"))


def rec(t) -> str:
    return "%d-%d" % t


def main():
    t0 = time.time()
    X = IR.build()
    pi = pd.read_parquet(OUT / "player_injury.parquet").merge(X, on=["game_id", "team"])
    tr = pd.read_parquet(OUT / "trends_asof.parquet").merge(X, on=["game_id", "team"])
    chk = {"skill value out, rebuilt vs live: share within 0.001": float(((pi.skill_out_value - pi.base_skill).abs() < 1e-3).mean()),
           "offensive snaps out, rebuilt vs live: share within 0.01": float(((tr.off_snap_out - tr.base_off).abs() < 1e-2).mean())}
    print(chk, flush=True)
    f0 = M.with_trends(pd.read_parquet(OUT / "features_asof.parquet")); f = attach(f0, X)
    res = {"base": run(f, BASE_T)}; print("base", {w: round(res["base"][w]["total"], 4) for w in WIN}, f"{time.time() - t0:.0f}s", flush=True)
    for v, feats in VARIANTS.items():
        res[v] = run(f, feats); print(v, {w: round(res[v][w]["total"], 4) for w in WIN}, f"{time.time() - t0:.0f}s", flush=True)
    gates = {v: gate_rows(res["base"], res[v]) for v in VARIANTS}
    placebo = {}
    fr = f.reset_index(drop=True); seas = fr.season.values; idx = np.arange(len(fr)); cols = list(PIECES)
    for v in VARIANTS:
        if not p12(gates[v]):
            continue
        rng = np.random.default_rng(SEED); gains = {w: [] for w in WIN}
        for i in range(DRAWS):
            perm = G.shuffle_within_season(idx, seas, rng).astype(int)
            fs = fr.copy(); fs[cols] = fr[cols].values[perm]; fs["qb_out_t"] = np.maximum(fs.qb_out.values, fs.q_qb.values)
            sc = run(fs, VARIANTS[v])
            for w in WIN:
                gains[w].append(res["base"][w]["total"] - sc[w]["total"])
            print(f"{v} placebo {i + 1}/{DRAWS}", {w: round(gains[w][-1], 4) for w in WIN}, f"{time.time() - t0:.0f}s", flush=True)
        placebo[v] = gains; gates[v] = gate_rows(res["base"], res[v], gains)
        pd.DataFrame(gains).to_csv(REP / f"questionable_totals_placebo_{v}.csv", index=False)
    rows = [{"variant": v, "window": w, "total_miss": round(sc[w]["total"], 4), "team_miss": round(sc[w]["team"], 4),
             "margin_miss": round(sc[w]["margin"], 4), "spread_flag": rec(sc[w]["spread"]), "totals_flag": rec(sc[w]["totals"]),
             "wind_under": rec(sc[w]["wind"])} for v, sc in res.items() for w in WIN]
    yrs = sorted(res["base"]["by_season"])
    pd.DataFrame(rows).to_csv(REP / "questionable_totals.csv", index=False)
    cov = X[X.season >= 2015].assign(q=lambda d: (d.q1_skill != 0) | (d.q2_off != 0) | (d.q2_def != 0)).groupby("season").agg(
        listed=("n_q", "sum"), rows=("q", "sum"), qb=("q2_qb", lambda s_: int((s_ > 0).sum())), mean_off=("q2_off", "mean"), mean_def=("q2_def", "mean"))
    md = REP / "questionable_totals.md"; head = md.read_text(encoding="utf-8").split("\n## Results")[0]
    L = [head.rstrip(), "", "## Results", "", "Rebuilt inputs against the live ones: " + "; ".join(f"{k} {v:.2%}" for k, v in chk.items()) + ".", "",
         "Team-games with a Questionable input, by season (regular season):", "",
         "| Season | Questionable listed | Team-games with a value | Starting QB Questionable | Mean offense snaps | Mean defense snaps |", "|---|---|---|---|---|---|"]
    L += [f"| {s} | {int(r.listed)} | {int(r.rows)} | {int(r.qb)} | {r.mean_off:.3f} | {r.mean_def:.3f} |" for s, r in cov.iterrows()]
    L += ["", "Each variant refit walk-forward 2015-2025 (regular season scored). Total miss is the yardstick; flags at the live rules (weeks 1-17).", "",
          "| Variant | Window | Total miss | Team miss | Margin miss | Spread flag | Totals flag | Wind under |", "|---|---|---|---|---|---|---|---|"]
    L += [f"| {r['variant']} | {r['window']} | {r['total_miss']:.4f} | {r['team_miss']:.4f} | {r['margin_miss']:.4f} | {r['spread_flag']} | {r['totals_flag']} | {r['wind_under']} |" for r in rows]
    L += ["", "Total miss by season (descriptive, added after the results to show where 2015-18 moved; not a variant):", "",
          "| Season | base | " + " | ".join(VARIANTS) + " |", "|---|---|" + "---|" * len(VARIANTS)]
    L += [f"| {y} | {res['base']['by_season'][y]:.4f} | " + " | ".join(f"{res[v]['by_season'][y]:.4f}" for v in VARIANTS) + " |" for y in yrs]
    for v, g_ in gates.items():
        L += ["", f"## Gate, variant {v}" + ("" if v in placebo else " (parts 1 and 2; the placebo runs only for a variant that passes them)"), "", G.markdown(g_)]
    md.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L)); print(f"done {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
