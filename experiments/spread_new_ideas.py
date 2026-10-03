"""Spread: new rating-construction ideas (3 Oct 2026, Matt: improve spread accuracy and the spread flag with new ideas).

Eight variants of how the team ratings are built, pre-registered in reports/spread_new_ideas.md before any result:
V1 last season's games weighted by roster continuity, V2 games with a different QB at half weight, V3 defense ridge 32,
V4 defense with last season x0.5, V5 games weighted by plays (per-play stats), V6 early-down EPA as the EPA rating,
V7 garbage-time plays at half weight, V8 per-play stats decay 0.96.

Each variant rebuilds the ratings with ratings.build_features (its own team_ratings swapped in; the QB rating and every
other input unchanged) and refits the live pipeline walk-forward 2015-2025 (model.walk_forward: weekly refit, the seven-
model blend, the totals equation, forecast weather), the stored tree fits read but never written. Scored through
nflmodel.study_gate on the margin miss and the team points miss (2015-18 / 2019-22 / 2023-25, regular season) with
the spread flag (4+), the totals flag (55%+ under) and the wind under (10+ mph), weeks 1-17, and the home win chance's
Brier score. A variant that passes parts 1 and 2 gets the placebo: its change to each team-game's ratings (all rating
columns together) moved to another team-game of the same season, 50 draws, seed 20261003. Passers are rerun together.
Writes reports/spread_new_ideas.{md,csv} (the results appended under the pre-registration).

    python -m experiments.spread_new_ideas            (all variants, placebo for passers, together test)
    python -m experiments.spread_new_ideas V3 V5      (just these, no placebo)
"""
from __future__ import annotations
import sys, time
import numpy as np, pandas as pd
from nflmodel import backtest as B, model as M, picks as P, ratings as R, study_gate as G
from nflmodel.features import OUT, ROOT

REP = ROOT / "reports"
WIN = {"2015-18": (2015, 2018), "2019-22": (2019, 2022), "2023-25": (2023, 2025)}
SEED, DRAWS = 20261003, 50
PER_PLAY = {"epa_play": "plays", "success": "plays", "pass_epa": "pass_plays", "rush_epa": "rush_plays"}
VARIANTS = {
    "V1": dict(cont=True, label="last season weighted by roster continuity"),
    "V2": dict(qb_match=0.5, label="games with another QB at half weight"),
    "V3": dict(alpha_d=32.0, label="defense ridge 32"),
    "V4": dict(prior_d=0.5, label="defense last season x0.5"),
    "V5": dict(plays_w=True, label="games weighted by plays (per-play stats)"),
    "V6": dict(early_down=True, label="early-down EPA as the EPA rating"),
    "V7": dict(garbage_half=True, label="garbage-time plays at half weight"),
    "V8": dict(decay_pp=0.96, label="per-play stats decay 0.96"),
}
GAMES = pd.read_parquet(OUT / "games.parquet")
RCOLS = [f"{p}_{s}" for s in R.STATS for p in ("off", "def", "own_def", "opp_off")]


# ---------- the variant ratings ----------

def starters_by_week(games: pd.DataFrame) -> dict:
    """(season, week) -> {team: QB the ratings price that week}: the named starter, else the last named one (as
    ratings.build_features carries it)."""
    named = games[games.home_qb_id.notna() | games.away_qb_id.notna()].sort_values(["season", "week"])
    last, out = {}, {}
    for (s, w), g in games.sort_values(["season", "week"]).groupby(["season", "week"], sort=True):
        for r in named[(named.season == s) & (named.week == w)].itertuples():
            if isinstance(r.home_qb_id, str):
                last[r.home_team] = r.home_qb_id
            if isinstance(r.away_qb_id, str):
                last[r.away_team] = r.away_qb_id
        out[(s, w)] = dict(last)
    return out


def continuity_multipliers(games: pd.DataFrame) -> dict:
    """season -> ({team: offense m}, {team: defense m}): week-1 continuity over the season's league mean, clipped to
    0.5-1.5. Week 1 only (a later week's roster would be look-ahead for the early solves); a team with no week-1 value
    (no game that week, or no roster) is left unweighted (m = 1), and the count is printed."""
    t = pd.read_parquet(OUT / "trends_asof.parquet", columns=["game_id", "team", "off_continuity", "def_continuity"])
    t = t.merge(games[["game_id", "season", "week"]], on="game_id")
    out = {}
    for s, g in t[t.week == 1].groupby("season"):
        first = g.dropna(subset=["off_continuity", "def_continuity"]).groupby("team").first()
        if not len(first):
            continue
        n_all = games[games.season == s].home_team.nunique()
        if len(first) < n_all:
            print(f"continuity {s}: {n_all - len(first)} teams with no week-1 value, unweighted", flush=True)
        mo = (first.off_continuity / first.off_continuity.mean()).clip(0.5, 1.5)
        md = (first.def_continuity / first.def_continuity.mean()).clip(0.5, 1.5)
        out[int(s)] = (mo.to_dict(), md.to_dict())
    return out


def solve2(rows, y, w, teams, alpha_o, alpha_d):
    """ratings.solve with separate ridge penalties on the offenses and the defenses (equal: identical to R.solve)."""
    n, T = len(rows), len(teams); idx = {t: k for k, t in enumerate(teams)}
    X = np.zeros((n, 2 + 2 * T)); X[:, 0] = 1.0; X[:, 1] = rows.home.values.astype(float)
    X[np.arange(n), 2 + rows.team.map(idx).values] = 1.0; X[np.arange(n), 2 + T + rows.opp.map(idx).values] = -1.0
    ok = ~np.isnan(y) & ~np.isnan(w)
    X, yv, wv = X[ok], y[ok], w[ok]
    Pn = np.zeros(2 + 2 * T); Pn[2:2 + T] = alpha_o; Pn[2 + T:] = alpha_d
    beta = np.linalg.solve(X.T @ (X * wv[:, None]) + np.diag(Pn), X.T @ (yv * wv))
    return pd.Series(beta[2:2 + T], index=teams), pd.Series(beta[2 + T:], index=teams), beta[0], beta[1]


def make_team_ratings(cfg: dict, starters: dict, cont: dict):
    """A drop-in for ratings.team_ratings (kind "model" only) carrying the variant's weights."""
    def team_ratings(tg, season, week, p, kind="model"):
        assert kind == "model"
        cur = tg[(tg.season == season) & (tg.week < week)]; last = tg[tg.season == season - 1]
        rows = pd.concat([cur, last])
        last_end = last.week.max() if len(last) else 18
        age = np.concatenate([(week - cur.week).values, week + (last_end + 1 - last.week).values]).astype(float)
        is_last = np.r_[np.zeros(len(cur), bool), np.ones(len(last), bool)]
        mult = np.ones(len(rows))
        if cfg.get("cont") and season in cont:
            mo, md = cont[season]
            m = rows.team.map(mo).fillna(1.0).values * rows.opp.map(md).fillna(1.0).values
            mult = np.where(is_last, mult * m, mult)
        if cfg.get("qb_match"):
            st = starters.get((season, week), {})
            now = rows.team.map(st)
            diff = now.notna().values & rows.qb_id.notna().values & (rows.qb_id.values != now.values)
            mult = np.where(diff, mult * cfg["qb_match"], mult)
        teams = sorted(set(tg[tg.season == season].team) | set(rows.team))
        out = pd.DataFrame(index=teams)
        for s in R.STATS:
            dec = cfg.get("decay_pp", p["decay"]) if s in PER_PLAY else p["decay"]
            base_w = dec ** age * mult
            if cfg.get("plays_w") and s in PER_PLAY:
                n = rows[PER_PLAY[s]].astype(float).values
                base_w = base_w * n / np.nanmean(n)
            y = rows[s].values.astype(float)
            w_o = np.where(is_last, p["prior"] * base_w, base_w)
            O, D, mu, h = solve2(rows, y, w_o, teams, p["alpha"], cfg.get("alpha_d", p["alpha"]))
            if cfg.get("prior_d") is not None:
                w_d = np.where(is_last, cfg["prior_d"] * base_w, base_w)
                _, D, _, _ = solve2(rows, y, w_d, teams, p["alpha"], cfg.get("alpha_d", p["alpha"]))
            out[f"off_{s}"] = O; out[f"def_{s}"] = D; out.attrs[f"mu_{s}"] = mu; out.attrs[f"hfa_{s}"] = h
        out["n_games"] = tg[(tg.season == season) & (tg.week < week)].groupby("team").size().reindex(teams).fillna(0)
        return out
    return team_ratings


def variant_tg(tg: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """The team-game stats the variant rates (V6, V7 change epa_play / success; the rest unchanged)."""
    tg = tg.copy()
    if cfg.get("early_down"):
        tg["epa_play"] = tg.early_down_epa.where(tg.early_down_epa.notna(), tg.epa_play)
    if cfg.get("garbage_half"):
        n, nn = tg.plays.astype(float), tg.plays_ng.astype(float).fillna(0.0)
        for s in ("epa_play", "success"):
            ng = tg[f"{s}_ng"].astype(float)
            tot, ngs = tg[s] * n, (ng * nn).where(nn > 0, 0.0)
            new = (ngs + 0.5 * (tot - ngs)) / (nn + 0.5 * (n - nn))
            tg[s] = new.where(new.notna(), tg[s])
    return tg


def build(cfg: dict | None, tg, qb, starters, cont) -> pd.DataFrame:
    keep = R.team_ratings
    try:
        if cfg:
            R.team_ratings = make_team_ratings(cfg, starters, cont)
        return R.build_features(R.DEFAULT, seasons=range(2013, 2027), tg=variant_tg(tg, cfg or {}), games=GAMES, qb=qb)
    finally:
        R.team_ratings = keep


# ---------- scoring ----------

def score(pred: pd.DataFrame) -> dict:
    d = B.join(pred, GAMES); d = d[(d.game_type == "REG") & d.season.between(2015, 2025)]
    out = {}
    for w, (lo, hi) in WIN.items():
        x = d[d.season.between(lo, hi)]
        mg = (x.home_score - x.away_score).values; hw = np.where(mg > 0, 1.0, np.where(mg < 0, 0.0, 0.5))
        e = x[x.week <= 4]
        out[w] = {"margin": float(x.margin_err.abs().mean()), "team": float(np.r_[x.home_err.abs(), x.away_err.abs()].mean()),
                  "total": float(x.total_err.abs().mean()), "brier": float(np.mean((x.p_home.values - hw) ** 2)),
                  "spread": P.record(x, P.rule_mask(x, P.SPREAD_EDGE)),
                  "totals": P.record(x, P.rule_mask(x, P.TOTAL_SHADOW["prob"], "under_prob"), "under_prob"),
                  "wind": P.record(x, P.rule_mask(x, P.WIND_UNDER["mph"], "wind_under"), "wind_under"),
                  "spread_w14": P.record(e, P.rule_mask(e, P.SPREAD_EDGE)), "margin_w14": float(e.margin_err.abs().mean())}
    return out


def run(f: pd.DataFrame) -> dict:
    return score(M.walk_forward(M.with_trends(f), range(2015, 2026), M.RIDGE))


def gates(base, new, placebo=None):
    rec = {w: {"spread flag": (base[w]["spread"], new[w]["spread"]), "totals flag": (base[w]["totals"], new[w]["totals"]),
               "wind under": (base[w]["wind"], new[w]["wind"])} for w in WIN}
    cal = {w: (base[w]["brier"], new[w]["brier"]) for w in WIN}
    gm = G.gate({w: (base[w]["margin"], new[w]["margin"]) for w in WIN}, rec, placebo and placebo["margin"], cal)
    gt = G.gate({w: (base[w]["team"], new[w]["team"]) for w in WIN}, None, placebo and placebo["team"])
    return [("margin: " + a, b, c) for a, b, c in gm] + [("team points: " + a, b, c) for a, b, c in gt]


def p12(rows) -> bool:
    return all(ok for what, ok, _ in rows if "placebo" not in what)


def placebo(fb: pd.DataFrame, fv: pd.DataFrame, base: dict, label: str, t0: float) -> dict:
    """The variant's rating change of each team-game (all rating columns together) moved within season."""
    fb = fb.reset_index(drop=True); fv = fv.set_index(["game_id", "team"]).reindex(pd.MultiIndex.from_arrays([fb.game_id, fb.team]))
    delta = fv[RCOLS].values - fb[RCOLS].values
    delta = np.where(np.isnan(delta), 0.0, delta)
    rng = np.random.default_rng(SEED); seas = fb.season.values; idx = np.arange(len(fb))
    gains = {"margin": {w: [] for w in WIN}, "team": {w: [] for w in WIN}}
    for i in range(DRAWS):
        perm = G.shuffle_within_season(idx, seas, rng).astype(int)
        fs = fb.copy(); fs[RCOLS] = fb[RCOLS].values + delta[perm]
        sc = run(fs)
        for k in gains:
            for w in WIN:
                gains[k][w].append(base[w][k] - sc[w][k])
        print(f"{label} placebo {i + 1}/{DRAWS}", {w: round(gains['margin'][w][-1], 4) for w in WIN}, f"{time.time() - t0:.0f}s", flush=True)
    pd.DataFrame({f"{k}_{w}": v for k, d_ in gains.items() for w, v in d_.items()}).to_csv(REP / f"spread_new_ideas_placebo_{label}.csv", index=False)
    return gains


def rec(t) -> str:
    return "%d-%d" % t


def main(only=None):
    t0 = time.time()
    tg = pd.read_parquet(OUT / "team_games.parquet"); tg = tg[tg.pf.notna()].copy()
    # the variants' inputs have no gaps on played games (the NaN fallbacks in variant_tg and the weights never fire)
    gaps = {c: int(tg[c].isna().sum()) for c in ["qb_id", "plays", "pass_plays", "rush_plays", "early_down_epa", "plays_ng", "epa_play_ng", "success_ng"]}
    assert not any(gaps.values()), f"missing values in team_games: {gaps}"
    qb = pd.read_parquet(OUT / "qb_games.parquet"); starters = starters_by_week(GAMES); cont = continuity_multipliers(GAMES)
    with M.trees_cache_read_only():
        fb = build(None, tg, qb, starters, cont)
        stored = pd.read_parquet(OUT / "features_asof.parquet")
        live = stored.merge(fb, on=["game_id", "team"], suffixes=("", "_r"))
        assert len(live) == len(stored) == len(fb), f"rebuilt rows {len(fb)}, stored {len(stored)}, matched {len(live)}"
        pl_ = live[live.pf.notna()]
        chk = max(float(np.nanmax(np.abs(pl_[c].values - pl_[c + "_r"].values))) for c in RCOLS + ["qb_rating"])
        assert chk < 1e-9 and not pl_[[c + "_r" for c in RCOLS]].isna().any().any(), f"rebuilt ratings differ from the stored ones ({chk:.2e})"
        # the rebuilt base and an identity variant (every switch off) must equal the live ratings
        fi = build({"label": "identity"}, tg, qb, starters, cont)
        idc = float(np.nanmax(np.abs(fi[RCOLS].values - fb[RCOLS].values)))
        assert idc == 0.0, f"identity variant differs from the rebuilt base ({idc:.2e})"
        print(f"rebuilt vs live max diff {chk:.2e}; identity variant vs rebuilt {idc:.2e}", flush=True)
        res = {"base": run(fb)}; print("base", {w: (round(res['base'][w]['margin'], 4), rec(res['base'][w]['spread'])) for w in WIN}, f"{time.time() - t0:.0f}s", flush=True)
        feats = {}
        for v, cfg in VARIANTS.items():
            if only and v not in only:
                continue
            feats[v] = build(cfg, tg, qb, starters, cont); res[v] = run(feats[v])
            print(v, {w: (round(res[v][w]['margin'], 4), round(res[v][w]['team'], 4), rec(res[v][w]['spread'])) for w in WIN}, f"{time.time() - t0:.0f}s", flush=True)
        gt = {v: gates(res["base"], res[v]) for v in feats}
        pl = {}
        if not only:
            for v in feats:
                if p12(gt[v]):
                    pl[v] = placebo(fb, feats[v], res["base"], v, t0); gt[v] = gates(res["base"], res[v], pl[v])
            passers = [v for v in feats if G.passes(gt[v])]
            if len(passers) > 1:
                cfg = {k: x for v in passers for k, x in VARIANTS[v].items() if k != "label"}; cfg["label"] = "together: " + " + ".join(passers)
                res["together"] = run(build(cfg, tg, qb, starters, cont)); gt["together"] = gates(res["base"], res["together"])
    write(res, gt, pl, chk, idc, only)
    print(f"done {time.time() - t0:.0f}s")


def write(res, gt, pl, chk, idc, only):
    lab = {"base": "live", "together": "together", **{v: f"{v} {c['label']}" for v, c in VARIANTS.items()}}
    rows = [{"variant": v, "label": lab[v], "window": w, "margin_miss": round(sc[w]["margin"], 4), "team_miss": round(sc[w]["team"], 4),
             "total_miss": round(sc[w]["total"], 4), "brier_home": round(sc[w]["brier"], 5), "spread_flag": rec(sc[w]["spread"]),
             "totals_flag": rec(sc[w]["totals"]), "wind_under": rec(sc[w]["wind"]), "spread_flag_w1_4": rec(sc[w]["spread_w14"]),
             "margin_miss_w1_4": round(sc[w]["margin_w14"], 4)} for v, sc in res.items() for w in WIN]
    out = "spread_new_ideas" + ("_partial" if only else "")
    pd.DataFrame(rows).to_csv(REP / f"{out}.csv", index=False)
    if only:
        return
    md = REP / "spread_new_ideas.md"; text = md.read_text(encoding="utf-8"); head = text.split("\n## Results")[0]
    cut = "\n## Count, audit and decision"   # the hand-written conclusion survives a rerun
    tail = (cut + text.split(cut, 1)[1]) if cut in text else ""
    L = [head.rstrip(), "", "## Results", "",
         f"The rebuilt live ratings equal the stored ones (largest difference {chk:.1e}); the variant code with every switch off equals them too ({idc:.1e}).", "",
         "Each variant refit walk-forward 2015-2025, regular season scored; flags at the live rules, weeks 1-17. Units at -110 = wins - 1.1 x losses.", "",
         "| Variant | Window | Margin miss | Team miss | Total miss | Brier (home win) | Spread flag | Units | Totals flag | Wind under | Spread flag wk 1-4 | Margin miss wk 1-4 |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        wv, lv = map(int, r["spread_flag"].split("-"))
        L.append(f"| {r['label']} | {r['window']} | {r['margin_miss']:.4f} | {r['team_miss']:.4f} | {r['total_miss']:.4f} | {r['brier_home']:.5f} | {r['spread_flag']} | {wv - 1.1 * lv:+.1f} | {r['totals_flag']} | {r['wind_under']} | {r['spread_flag_w1_4']} | {r['margin_miss_w1_4']:.4f} |")
    for v, g_ in gt.items():
        note = "" if v in pl or v == "together" else " (parts 1 and 2; the placebo runs only for a variant that passes them)"
        L += ["", f"## Gate, {lab[v]}{note}", "", G.markdown(g_)]
    md.write_text("\n".join(L) + "\n" + tail, encoding="utf-8")
    print("\n".join(L[L.index("## Results"):]))


if __name__ == "__main__":
    main(sys.argv[1:] or None)
