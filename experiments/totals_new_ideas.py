"""New totals ideas (3 Oct 2026, Matt: "improve TOTALS accuracy and the totals rules' wins/units against Vegas with NEW
ideas from all angles"). Pre-registered in reports/totals_new_ideas.md before any result.

V1-V7 add one input to the totals equation (model.TOTAL_FEATS): pace (seconds per snap), neutral pace, red-zone TD rate,
explosive-play rate, kicker value, artificial turf, altitude. V8-V9 change only the over chance (p_over_emp): the training
misses scaled with the total (variance proportional to the mean), and key totals (a whole-number pmf with key weights).

The points equations and the spread are untouched by every variant, so the walk-forward's points side is run once (the
live model.walk_forward, trees cache read-only) and the totals side is rebuilt here exactly as walk_forward builds it (the
totals equation refit every week on every played game, wind points from earlier seasons' forecast games, p_over_emp from the
fit's training misses); the base rebuilt this way must equal the live walk-forward to 1e-9 (checked, printed).

Scored through nflmodel.study_gate: total miss (V8-V9: the over chance's log loss at the closing total), the totals flag,
wind under and spread flag, weeks 1-17, 2015-18 / 2019-22 / 2023-25; the 50-draw within-season placebo for a variant that
passes parts 1 and 2. Writes reports/totals_new_ideas.{md,csv}.

    python -m experiments.totals_new_ideas
"""
from __future__ import annotations
import sys, time
import numpy as np, pandas as pd
from scipy.stats import norm
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from nflmodel import backtest as B, model as M, picks as P, ratings as R, study_gate as G
from nflmodel.features import OUT, ROOT

REP = ROOT / "reports"
WIN = {"2015-18": (2015, 2018), "2019-22": (2019, 2022), "2023-25": (2023, 2025)}
SEASONS = range(2015, 2026)
SEED, DRAWS, PULL = 20261003, 50, 4.0
GAMES = pd.read_parquet(OUT / "games.parquet")
BASE_T = list(M.TOTAL_FEATS)
INPUTS = {"V1": "pace_sum", "V2": "npace_sum", "V3": "rz_td_sum", "V4": "explosive_sum", "V5": "kicker_sum", "V6": "turf", "V7": "altitude"}
NAMES = {"V1": "pace (seconds per snap)", "V2": "neutral pace", "V3": "red-zone TD rate", "V4": "explosive-play rate", "V5": "kicker value",
         "V6": "artificial turf", "V7": "altitude (Denver home)", "V8": "spread grows with the total", "V9": "key totals"}
CHANCE = ("V8", "V9")
GRID = np.arange(0, 131)   # whole-number game totals for V9


# ---------- inputs, as of before each game ----------
def asof_team(tab: pd.DataFrame, col: str, keys: pd.DataFrame) -> dict:
    """(season, week, team) -> the team's decayed mean of col over its earlier games (ratings.window: decay 0.94 a week, last
    season at 0.8), pulled toward the window's league mean with PULL games of weight."""
    t = tab[tab[col].notna()][["season", "week", "team", col]]
    out = {}
    for (s, w), k in keys.groupby(["season", "week"]):
        rows, wt = R.window(t, int(s), int(w), R.DEFAULT["decay"], R.DEFAULT["prior"])
        if len(rows) == 0:
            continue
        lg = float(np.average(rows[col].values, weights=wt))
        d = pd.DataFrame({"team": rows.team.values, "x": rows[col].values * wt, "w": wt}).groupby("team").sum()
        v = (d.x + PULL * lg) / (d.w + PULL)
        for tm in k.team.unique():
            out[(int(s), int(w), tm)] = float(v.get(tm, lg))
    return out


def game_sum(f: pd.DataFrame, off: dict, dfn: dict) -> dict:
    """game_id -> both offenses' plus both defenses' as-of values (one input); a team with no earlier game: the mean."""
    fill = float(np.mean(list(off.values()) + list(dfn.values())))
    v = [off.get((s, w, t), fill) + dfn.get((s, w, t), fill) for s, w, t in zip(f.season, f.week, f.team)]
    return pd.Series(v, index=f.index).groupby(f.game_id.values).sum().to_dict()


def neutral_pace_table() -> pd.DataFrame:
    """Seconds per snap in neutral situations per (game, offense), as team_game_stats builds sec_per_play but only snaps with
    win chance 20-80% on first or second down (scheme.py's neutral); defense = the same joined on the defense."""
    s = pd.read_parquet(OUT / "scheme_plays.parquet", columns=["game_id", "season", "week", "posteam", "defteam", "play_type", "game_seconds_remaining", "neutral"])
    s = s[s.play_type.isin(["pass", "run"]) & s.posteam.notna()].sort_values(["game_id", "posteam", "game_seconds_remaining"], ascending=[True, True, False])
    s["gap"] = -s.groupby(["game_id", "posteam"]).game_seconds_remaining.diff()
    s = s[(s.gap > 0) & (s.gap < 60) & s.neutral.astype(bool)]
    g = s.groupby(["game_id", "season", "week", "posteam", "defteam"]).gap.mean().reset_index()
    off = g.rename(columns={"posteam": "team", "gap": "npace"})[["game_id", "season", "week", "team", "npace"]]
    dfn = g.rename(columns={"defteam": "team", "gap": "def_npace"})[["game_id", "season", "week", "team", "def_npace"]]
    return off.merge(dfn, on=["game_id", "season", "week", "team"], how="outer")


def build_inputs(f: pd.DataFrame) -> tuple[dict, dict]:
    """game_id -> value for every V1-V7 input, and coverage counts for the report."""
    keys = f[["season", "week", "team"]].drop_duplicates()
    tg = pd.read_parquet(OUT / "team_games.parquet"); tg = tg[tg.pf.notna()]
    X, cov = {}, {}
    for v, (oc, dc) in {"V1": ("sec_per_play", "def_sec_per_play"), "V3": ("rz_td_rate", "def_rz_td_rate"), "V4": ("explosive_rate", "def_explosive_rate")}.items():
        X[INPUTS[v]] = game_sum(f, asof_team(tg, oc, keys), asof_team(tg, dc, keys))
    npc = neutral_pace_table()
    # no neutral-pace data before 2016: a team-game with no earlier data takes the mean (game_sum's fill), as pre-registered
    X["npace_sum"] = game_sum(f, asof_team(npc, "npace", keys), asof_team(npc, "def_npace", keys))
    st = pd.read_parquet(OUT / "special_teams_asof.parquet", columns=["game_id", "team", "kicker_value"])
    kv = f[["game_id", "team"]].merge(st, on=["game_id", "team"], how="left").kicker_value.fillna(0.0)
    X["kicker_sum"] = kv.groupby(f.game_id.values).sum().to_dict()
    gi = GAMES.set_index("game_id")
    surf = gi.surface.fillna("").str.strip().str.lower()
    X["turf"] = (~surf.isin(["grass", "dessograss", ""])).astype(float).to_dict()
    X["altitude"] = ((gi.home_team == "DEN") & gi.stadium_id.fillna("").str.startswith("DEN") & (gi.neutral.fillna(0) != 1)).astype(float).to_dict()
    sc = f[f.season.between(2015, 2025) & (f.home == 1)]
    for k, d in X.items():
        vals = np.array([d.get(g, np.nan) for g in sc.game_id], dtype=float)
        cov[k] = {"games": int(len(vals)), "missing": int(np.isnan(vals).sum()), "mean": float(np.nanmean(vals)), "sd": float(np.nanstd(vals))}
    return X, cov


# ---------- the totals side of model.walk_forward, rebuilt ----------
def gframe(f: pd.DataFrame, X: dict) -> pd.DataFrame:
    g = M._game_frame(f)
    for k, d in X.items():
        g[k] = g.index.map(d).astype(float)
        g[k] = g[k].fillna(float(np.nanmean(list(d.values()))))
    return g


def tfit(tr: pd.DataFrame, feats):
    return make_pipeline(StandardScaler(), Ridge(alpha=10.0)).fit(tr[feats].values, tr.total.values)


def p_emp(mt, tl, tres):
    if pd.isna(tl):
        return np.nan
    return float(np.mean(mt + tres > tl) / max(1e-9, np.mean(mt + tres != tl)))


def kde_density(tres: np.ndarray, bw: float = 1.5):
    """The training misses' density as a function (Gaussian kernel, bandwidth bw), on a 0.05 grid, interpolated."""
    x = np.arange(-80, 80.001, 0.05)
    h, e = np.histogram(tres, bins=np.append(x - 0.025, x[-1] + 0.025)); h = h.astype(float)
    k = norm.pdf(np.arange(-6 * bw, 6 * bw + 1e-9, 0.05) / bw); k /= k.sum()
    d = np.convolve(h, k, mode="same"); d /= d.sum() * 0.05
    return lambda r: np.interp(r, x, d, left=0.0, right=0.0)


def key_total_weights(tr_total, tr_mu, dens) -> np.ndarray:
    obs = np.bincount(np.clip(np.round(tr_total).astype(int), 0, GRID[-1]), minlength=len(GRID)).astype(float)
    exp = dens(GRID[None, :] - np.asarray(tr_mu)[:, None]).sum(axis=0)
    return (obs + 1.0) / (exp + 1.0)


def p_key(mt, tl, dens, K):
    if pd.isna(tl):
        return np.nan
    pm = dens(GRID - mt) * K; pm = pm / pm.sum()
    push = pm[GRID == tl].sum() if float(tl).is_integer() else 0.0
    return float(pm[GRID > tl].sum() / (1 - push)) if push < 1 else np.nan


def totals_wf(fp, played, fpr, X, feats, chance=None, perm=None, rng=None) -> pd.DataFrame:
    """game_id, model_total, p_over_emp for 2015-2025 as model.walk_forward makes them (chance: None / "V8" / "V9";
    perm: a placebo for V8 (dict game_id -> shuffled scale) or V9 (rng to shuffle the key weights))."""
    gp, gt = gframe(played, X), gframe(fpr, X)
    wind = M._wind_readings(); wpool = {}
    act = gp.total.to_dict(); rows = []
    hp = played[played.home == 1].set_index("game_id"); ht = fpr[fpr.home == 1].set_index("game_id")
    for s in SEASONS:
        tall = ht[ht.season == s]
        for wk in sorted(tall.week.unique()):
            tr_ids = hp.index[(hp.season >= M.TRAIN_FROM) & ((hp.season < s) | ((hp.season == s) & (hp.week < wk)))]
            te_ids = tall.index[tall.week == wk]
            tr = gp[gp.index.isin(tr_ids)]; te = gt[gt.index.isin(te_ids)]
            if len(te) == 0:
                continue
            m = tfit(tr, feats); raw = m.predict(te[feats].values); trmu = m.predict(tr[feats].values)
            pool_ = [x for s_, v in wpool.items() if s_ < s for x in v]
            wfc = te.index.map(wind).astype(float)
            mt = raw + np.array([M.wind_points(pool_, fw) for fw in wfc])
            tres = tr.total.values - trmu
            tl = tall.total_line.reindex(te.index).values   # the line walk_forward prices at (the feature table's)
            if chance is None:
                pe = [p_emp(a, b, tres) for a, b in zip(mt, tl)]
            elif chance == "V8":
                base = float(trmu.mean())
                sc = np.sqrt(np.clip(mt, 1, None) / base) if perm is None else np.array([perm[g] for g in te.index])
                pe = [p_emp(a, b, tres * c) for a, b, c in zip(mt, tl, sc)]
            else:
                dens = kde_density(tres); K = key_total_weights(tr.total.values, trmu, dens)
                if rng is not None:
                    K = rng.permutation(K)
                pe = [p_key(a, b, dens, K) for a, b in zip(mt, tl)]
            rows.append(pd.DataFrame({"game_id": te.index, "model_total": mt, "p_over_emp": pe, "scale": np.sqrt(np.clip(mt, 1, None) / float(trmu.mean()))}))
            gtype = tall.game_type.reindex(te.index).values
            for gid, fw, r_, gty in zip(te.index, wfc, raw, gtype):
                if pd.notna(fw) and gty == "REG" and gid in act:
                    wpool.setdefault(s, []).append((float(fw), float(act[gid]) - float(r_)))
    return pd.concat(rows, ignore_index=True)


# ---------- scoring ----------
def merged(base_pred: pd.DataFrame, t: pd.DataFrame) -> pd.DataFrame:
    p = base_pred.drop(columns=["model_total", "p_over_emp"]).merge(t[["game_id", "model_total", "p_over_emp"]], on="game_id")
    p["home_exp"] = (p.model_total + p.model_spread) / 2; p["away_exp"] = (p.model_total - p.model_spread) / 2
    return p


def score(pred: pd.DataFrame) -> dict:
    d = B.join(pred, GAMES); d = d[(d.game_type == "REG") & d.season.between(2015, 2025)]
    out = {}
    for w, (lo, hi) in WIN.items():
        x = d[d.season.between(lo, hi)]
        cm = x.home_score + x.away_score - x.total_line; ok = (cm != 0) & x.total_line.notna() & x.p_over_emp.notna()
        p = x.p_over_emp[ok].clip(1e-6, 1 - 1e-6); y = (cm[ok] > 0).astype(float)
        tf = P.rule_mask(x, P.TOTAL_SHADOW["prob"], "under_prob"); tw, tl_ = P.record(x, tf, "under_prob")
        out[w] = {"total": float(x.total_err.abs().mean()), "team": float(np.r_[x.home_err.abs(), x.away_err.abs()].mean()),
                  "logloss": float(-(y * np.log(p) + (1 - y) * np.log(1 - p)).mean()),
                  "spread": P.record(x, P.rule_mask(x, P.SPREAD_EDGE)), "totals": (tw, tl_),
                  "units": round(tw - 1.1 * tl_, 2),   # the totals flag at -110
                  "wind": P.record(x, P.rule_mask(x, P.WIND_UNDER["mph"], "wind_under"), "wind_under")}
    return out


def yard(v):
    return "logloss" if v in CHANCE else "total"


def gate_rows(base, new, v, placebo=None):
    return G.gate({w: (base[w][yard(v)], new[w][yard(v)]) for w in WIN},
                  {w: {"spread flag": (base[w]["spread"], new[w]["spread"]), "totals flag": (base[w]["totals"], new[w]["totals"]),
                       "wind under": (base[w]["wind"], new[w]["wind"])} for w in WIN}, placebo)


def p12(rows) -> bool:
    return all(ok for what, ok, _ in rows if not what.startswith("beats"))


def main():
    t0 = time.time()
    f0 = M.with_trends(pd.read_parquet(OUT / "features_asof.parquet"))
    with M.trees_cache_read_only():
        live = M.walk_forward(f0, SEASONS, M.RIDGE)
    print(f"live walk-forward {time.time() - t0:.0f}s", flush=True)
    fp = M.prep(f0); played = fp[fp.pf.notna()]; fpr = M.priced_weather(fp)
    X, cov = build_inputs(fp); print("inputs", cov, f"{time.time() - t0:.0f}s", flush=True)
    tb = totals_wf(fp, played, fpr, X, BASE_T)
    chk = live[["game_id", "model_total", "p_over_emp"]].merge(tb, on="game_id", suffixes=("", "_re"))
    dmt, dpo = float((chk.model_total - chk.model_total_re).abs().max()), float((chk.p_over_emp - chk.p_over_emp_re).abs().max())
    print(f"rebuilt base vs live walk-forward: {len(chk)} of {len(live)} games, max diff total {dmt:.2e}, over chance {dpo:.2e}", flush=True)
    if len(chk) != len(live) or dmt > 1e-9 or dpo > 1e-9:
        sys.exit("the rebuilt totals side does not reproduce the live walk-forward")
    res = {"base": score(live)}
    preds = {}
    for v in NAMES:
        if v in CHANCE:
            t = totals_wf(fp, played, fpr, X, BASE_T, chance=v)
        else:
            t = totals_wf(fp, played, fpr, X, BASE_T + [INPUTS[v]])
        preds[v] = t; res[v] = score(merged(live, t))
        print(v, {w: (round(res[v][w][yard(v)], 4), "%d-%d" % res[v][w]["totals"]) for w in WIN}, f"{time.time() - t0:.0f}s", flush=True)
    gates = {v: gate_rows(res["base"], res[v], v) for v in NAMES}
    placebo = {}
    games_f = fp[fp.home == 1][["game_id", "season"]].drop_duplicates("game_id")
    for v in NAMES:
        if not p12(gates[v]):
            continue
        rng = np.random.default_rng(SEED); gains = {w: [] for w in WIN}
        for i in range(DRAWS):
            if v == "V8":
                sc = preds[v].merge(games_f, on="game_id")
                perm = dict(zip(sc.game_id, G.shuffle_within_season(sc.scale.values, sc.season.values, rng)))
                t = totals_wf(fp, played, fpr, X, BASE_T, chance="V8", perm=perm)
            elif v == "V9":
                t = totals_wf(fp, played, fpr, X, BASE_T, chance="V9", rng=rng)
            else:
                k = INPUTS[v]; ids = games_f.game_id.values
                vals = G.shuffle_within_season(np.array([X[k].get(g, np.nan) for g in ids]), games_f.season.values, rng)
                Xs = dict(X); Xs[k] = dict(zip(ids, vals))
                t = totals_wf(fp, played, fpr, Xs, BASE_T + [k])
            sc_ = score(merged(live, t))
            for w in WIN:
                gains[w].append(res["base"][w][yard(v)] - sc_[w][yard(v)])
            print(f"{v} placebo {i + 1}/{DRAWS}", {w: round(gains[w][-1], 4) for w in WIN}, f"{time.time() - t0:.0f}s", flush=True)
        placebo[v] = gains; gates[v] = gate_rows(res["base"], res[v], v, gains)
        pd.DataFrame(gains).to_csv(REP / f"totals_new_ideas_placebo_{v}.csv", index=False)
    # together: every variant that passes the whole gate, rerun as one
    passers = [v for v in NAMES if G.passes(gates[v])]
    together = None
    if len(passers) > 1:
        ins = [INPUTS[v] for v in passers if v in INPUTS]; ch = [v for v in passers if v in CHANCE]
        if len(ch) <= 1:
            t = totals_wf(fp, played, fpr, X, BASE_T + ins, chance=(ch[0] if ch else None))
            res["together"] = score(merged(live, t)); together = gate_rows(res["base"], res["together"], "V1")
    rows = [{"variant": v, "name": NAMES.get(v, v), "window": w, "total_miss": round(sc[w]["total"], 4), "over_logloss": round(sc[w]["logloss"], 5),
             "team_miss": round(sc[w]["team"], 4), "spread_flag": "%d-%d" % sc[w]["spread"], "totals_flag": "%d-%d" % sc[w]["totals"],
             "totals_units": sc[w]["units"], "wind_under": "%d-%d" % sc[w]["wind"]} for v, sc in res.items() for w in WIN]
    pd.DataFrame(rows).to_csv(REP / "totals_new_ideas.csv", index=False)
    md = REP / "totals_new_ideas.md"; old = md.read_text(encoding="utf-8"); head = old.split("\n## Results")[0]
    tail = ("\n## Decision" + old.split("\n## Decision", 1)[1]) if "\n## Decision" in old else ""   # the write-up, kept on a rerun
    L = [head.rstrip(), "", "## Results", "",
         f"Rebuilt totals side against the live walk-forward: {len(chk)} games, largest difference {dmt:.1e} points in the total and {dpo:.1e} in the over chance.", "",
         "Inputs, regular-season games 2015-2025 (one value per game):", "", "| Input | Games | Missing | Mean | SD |", "|---|---|---|---|---|"]
    L += [f"| {k} | {c['games']} | {c['missing']} | {c['mean']:.4f} | {c['sd']:.4f} |" for k, c in cov.items()]
    L += ["", "Each variant refit walk-forward 2015-2025, regular season scored; flags at the live rules, weeks 1-17; totals units at -110.", "",
          "| Variant | Window | Total miss | Over log loss | Team miss | Spread flag | Totals flag | Totals units | Wind under |", "|---|---|---|---|---|---|---|---|---|"]
    L += [f"| {r['variant']} {r['name'] if r['variant'] in NAMES else ''} | {r['window']} | {r['total_miss']:.4f} | {r['over_logloss']:.5f} | {r['team_miss']:.4f} | {r['spread_flag']} | {r['totals_flag']} | {r['totals_units']:+.2f} | {r['wind_under']} |" for r in rows]
    for v, g_ in gates.items():
        L += ["", f"## Gate, {v} {NAMES[v]}" + ("" if v in placebo else " (parts 1 and 2; the placebo runs only for a variant that passes them)"), "", G.markdown(g_)]
    if together is not None:
        L += ["", "## Together: " + ", ".join(passers), "", G.markdown(together)]
    md.write_text("\n".join(L) + "\n" + tail, encoding="utf-8")
    print("\n".join(L)); print(f"done {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
