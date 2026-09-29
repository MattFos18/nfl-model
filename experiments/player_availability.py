"""Per-player availability for the season totals (29 Sep 2026). The dominant miss in the season totals is games
missed, and the projection gives every player of a kind one flat share of his team's games left (player_season.AVAIL:
rec 0.65, rush 0.625, pass 0.525, fitted on 2016-18). An earlier test (experiments/availability.py, reports/availability.csv,
docs section 36) predicted the share with a linear fit on the report, practice, share of games played this season and
last, two seasons of Out/Doubtful listings and age, then multiplied by a fitted scale with the blend held at today's:
the games themselves came out better (receivers 2.72 -> 2.70 games off), the season total mixed. This study differs in
the inputs and the model:

  (a) this week's status: report Out / Doubtful / Questionable, practice DNP / Limited (nflverse injury reports; the
      report for the as-of week, published before its games), the roster status at the previous roster week
  (b) his own absences: team games missed of his last 34 (snap_exposure against the games of the teams he was
      rostered on, regular season), and whether he missed his team's last game
  (c) age band (on the as-of week's first game day) and position
  (d) games played so far this season against team games played (the row's games_so_far / team_games_played)
  (e) on reserve (IR, PUP, NFI) at the previous roster week, and on reserve at any point earlier this season
      (the rows only hold players ACT at the as-of week's roster, so "on IR now" is always 0 there)

Model: a binomial logistic regression (games he went on to play out of the team's games left, each row weighted by
its team games left), one pooled fit over the three kinds with kind and position terms, L2 penalty C=1 on the raw
0-1 scaled features (sklearn), fitted on 2016-18. For the constants fitted on 2016-18 afterwards (the blend, a scale),
the 2016-18 rows carry out-of-season predictions (each season predicted by a fit on the other two).

Variants, each with the blend toward pace refit on 2016-18 on the season-total error as the harness does:
  flat      today's rule, AVAIL and BLEND refit on the fresh rows (the harness grid)
  share     AVAIL replaced by the per-player predicted share p
  mult      AVAIL x a shrunk per-player multiplier: AVAIL' x (1 + lam x (p / mean p of the kind on 2016-18 - 1)),
            AVAIL' on the harness grid, lam in 0, 0.25, 0.5, 0.75, 1
  capped    p capped to 0.3 .. 1.0
  scaled    (extra, for the record) p x a fitted scale s in 0.5 .. 1.2, capped at 1

Rows are built fresh (the harness's rows_for) into the scratchpad, not over reports/player_season_rows.csv.
  python experiments/player_availability.py build [--only SEASON WEEK] [--jobs N]
  python experiments/player_availability.py study
Output: reports/player_availability.csv, reports/player_availability.md (the md's rule is written before the results).
"""
from __future__ import annotations
import sys, time, os
import numpy as np, pandas as pd
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from nflmodel import player_season as PS
from experiments import player_season_backtest as BT

RAW, OUT, REP = PS.RAW, PS.OUT, PS.REP
SCR = Path(os.environ.get("AVAIL_SCRATCH", "/tmp/claude-0/-home-user/c1e0d18e-681a-50ba-b0bb-6c809c2e3dee/scratchpad/availability"))
PARTS = SCR / "parts"; ROWS = SCR / "rows.csv"
KINDS = ("rec", "rush", "pass")
WINDOWS = {"2019-22": (2019, 2022), "2023-25": (2023, 2025)}
TEAM_FIX = {"ARZ": "ARI", "BLT": "BAL", "CLV": "CLE", "HST": "HOU", "SL": "LA", "STL": "LA", "OAK": "LV", "SD": "LAC"}
ON_TEAM = {"ACT", "INA", "RES", "PUP", "SUS", "NWT", "RSN", "RSR", "EXE", "NFI"}   # rostered (not cut, practice squad, retired, traded-away)
RESERVE = {"RES", "PUP", "NFI", "RSN", "RSR"}
HIST_N = 34
LAM_GRID = [0.0, 0.25, 0.5, 0.75, 1.0]
SCALE_GRID = np.round(np.arange(0.5, 1.2001, 0.025), 3)


# ---------------------------------------------------------------- build (fresh rows)
_D = {}


def _load():
    if not _D:
        from nflmodel.props import official
        from nflmodel.positions import names_by_id
        _D["games"] = pd.read_parquet(OUT / "games.parquet")
        _D["d"] = official(pd.read_parquet(OUT / "scheme_plays.parquet"))
        _D["names"] = names_by_id(range(2014, 2027))
    return _D


def _one(sw):
    s, w = sw
    f = PARTS / f"rows_{s}_{w:02d}.csv"
    if f.exists():
        return s, w, -1.0, 0
    t = time.time(); D = _load(); t_load = time.time() - t
    p = BT.rows_for(D["d"], D["games"], D["names"], s, w)
    tmp = f.with_suffix(".tmp"); p.round(3).to_csv(tmp, index=False); tmp.rename(f)
    return s, w, time.time() - t - t_load, len(p)


def build(only=None, jobs=1):
    PARTS.mkdir(parents=True, exist_ok=True)
    todo = [only] if only else [(s, w) for s in BT.FIT_SEASONS + BT.TEST_SEASONS for w in BT.WEEKS if not (s == 2016 and w == 1)]
    t0 = time.time()
    if jobs <= 1:
        for sw in todo:
            s, w, dt, n = _one(sw)
            print(f"{s} week {w}: {n} players, {dt:.1f}s (elapsed {time.time() - t0:.0f}s)" if dt >= 0 else f"{s} week {w}: cached", flush=True)
    else:
        from multiprocessing import Pool
        with Pool(jobs) as pool:
            for s, w, dt, n in pool.imap_unordered(_one, todo):
                print(f"{s} week {w}: {n} players, {dt:.1f}s (elapsed {time.time() - t0:.0f}s)" if dt >= 0 else f"{s} week {w}: cached", flush=True)
    if not only:
        R = pd.concat([pd.read_csv(f) for f in sorted(PARTS.glob("rows_*.csv"))], ignore_index=True)
        R.to_csv(ROWS, index=False); print(f"rows: {len(R)} -> {ROWS} ({time.time() - t0:.0f}s)", flush=True)


# ---------------------------------------------------------------- features (as of the week)
def team_games() -> pd.DataFrame:
    g = pd.read_parquet(OUT / "games.parquet", columns=["game_id", "season", "week", "game_type", "home_team", "away_team", "gameday"])
    g = g[(g.game_type == "REG") & (g.season >= 2013)]
    tg = pd.concat([g.rename(columns={"home_team": "team"})[["game_id", "season", "week", "team"]], g.rename(columns={"away_team": "team"})[["game_id", "season", "week", "team"]]])
    return tg


def rosters() -> pd.DataFrame:
    fr = []
    for s in range(2013, 2026):
        r = pd.read_parquet(RAW / "rosters" / f"roster_weekly_{s}.parquet", columns=["season", "week", "team", "gsis_id", "status", "game_type"]).dropna(subset=["gsis_id"])
        fr.append(r[r.game_type == "REG"].drop(columns="game_type"))
    r = pd.concat(fr, ignore_index=True); r["team"] = r.team.replace(TEAM_FIX)
    r["rank"] = r.status.map(lambda x: 0 if x == "ACT" else (1 if x in ON_TEAM else 2))
    return r.sort_values("rank").drop_duplicates(["gsis_id", "season", "week"]).drop(columns="rank")


def injuries() -> pd.DataFrame:
    fr = []
    for s in range(2016, 2026):
        x = pd.read_parquet(RAW / "injuries" / f"injuries_{s}.parquet")
        col = "season_type" if "season_type" in x.columns else "game_type"
        x = x[x[col] == "REG"].dropna(subset=["gsis_id"])
        if "date_modified" in x.columns:
            x = x.sort_values("date_modified")
        fr.append(x[["season", "week", "gsis_id", "report_status", "practice_status"]])
    return pd.concat(fr, ignore_index=True).drop_duplicates(["season", "week", "gsis_id"], keep="last")


def history(R: pd.DataFrame, ro: pd.DataFrame) -> pd.DataFrame:
    """Per row: team games missed of his last HIST_N before the as-of week, how many team games are on record (fewer
    for a young player), and whether he missed his team's last game. A team game is one of the teams he was rostered on
    that week (or any game he took an offensive snap in); missed = no offensive snap."""
    tg = team_games()
    snap = pd.read_parquet(OUT / "snap_exposure.parquet", columns=["player_id", "game_id", "season", "week", "team", "offense_snaps"])
    snap = snap[(snap.offense_snaps > 0) & snap.game_id.isin(set(tg.game_id))]
    pids = set(R.player_id)
    on = ro[ro.status.isin(ON_TEAM) & ro.gsis_id.isin(pids)].rename(columns={"gsis_id": "player_id"})
    a = on.merge(tg, on=["season", "week", "team"], how="inner")[["player_id", "game_id", "season", "week"]]
    b = snap[snap.player_id.isin(pids)][["player_id", "game_id", "season", "week"]]
    G = pd.concat([a, b]).drop_duplicates(["player_id", "season", "week"])
    played = set(zip(b.player_id, b.game_id))
    G["missed"] = [0 if (p, g) in played else 1 for p, g in zip(G.player_id, G.game_id)]
    G["t"] = G.season * 100 + G.week
    G = G.sort_values(["player_id", "t"])
    out = {}
    keys = R[["player_id", "season", "week"]].drop_duplicates()
    byp = {p: (x.t.values, np.cumsum(np.r_[0, x.missed.values])) for p, x in G.groupby("player_id")}
    for p, s, w in keys.itertuples(index=False):
        if p not in byp:
            out[(p, s, w)] = (0, 0, 0); continue
        t, cm = byp[p]; i = int(np.searchsorted(t, s * 100 + w, side="left"))   # games strictly before the as-of week
        j = max(0, i - HIST_N)
        last = int(cm[i] - cm[i - 1]) if i > 0 else 0
        out[(p, s, w)] = (int(cm[i] - cm[j]), i - j, last)
    k = list(zip(R.player_id, R.season, R.week))
    R = R.copy()
    R["miss34"] = [out[x][0] for x in k]; R["n34"] = [out[x][1] for x in k]; R["miss_last"] = [out[x][2] for x in k]
    return R


def features(R: pd.DataFrame) -> pd.DataFrame:
    t0 = time.time()
    ro = rosters(); R = history(R, ro); print(f"  history ({time.time() - t0:.0f}s)", flush=True)
    # (a) the report for the as-of week
    inj = injuries().set_index(["season", "week", "gsis_id"])
    k = list(zip(R.season, R.week, R.player_id))
    rs = inj.report_status.reindex(k).values; ps = inj.practice_status.reindex(k).fillna("").astype(str).values
    R["rep_out"] = (rs == "Out").astype(float); R["rep_doubt"] = (rs == "Doubtful").astype(float); R["rep_q"] = (rs == "Questionable").astype(float)
    R["prac_dnp"] = np.array([x.startswith("Did Not") for x in ps], float); R["prac_lim"] = np.array([x.startswith("Limited") for x in ps], float)
    # (e) roster status: now (the as-of week; always ACT in the rows), the previous roster week, any earlier week this season
    st = ro.set_index(["season", "week", "gsis_id"]).status
    R["status_now"] = st.reindex(k).fillna("NA").values
    R["ir_now"] = R.status_now.isin(RESERVE).astype(float)
    R["ir_prev"] = st.reindex(list(zip(R.season, R.week - 1, R.player_id))).isin(RESERVE).astype(float).values
    res = ro[ro.status.isin(RESERVE)][["gsis_id", "season", "week"]]
    first_res = res.groupby(["gsis_id", "season"]).week.min()
    fr = first_res.reindex(list(zip(R.player_id, R.season))).values
    R["ir_season"] = (pd.notna(fr) & (fr < R.week.values)).astype(float)
    # (c) age on the as-of week's first game day, position
    gd = pd.read_parquet(OUT / "games.parquet", columns=["season", "week", "gameday", "game_type"])
    gd = gd[gd.game_type == "REG"].groupby(["season", "week"]).gameday.min()
    day = pd.to_datetime(gd.reindex(list(zip(R.season, R.week))).values)
    pl = pd.read_parquet(RAW / "players" / "players.parquet", columns=["gsis_id", "birth_date"]).dropna().drop_duplicates("gsis_id")
    born = pd.to_datetime(pl.set_index("gsis_id").birth_date, errors="coerce")
    R["age"] = (day - pd.to_datetime(born.reindex(R.player_id).values)).days / 365.25
    R["age"] = R.age.fillna(R.groupby("kind").age.transform("median"))
    R["pos_g"] = np.where(R.pos.isin(["QB", "RB", "TE"]), R.pos, "WR")
    # (d) this season
    R["share_now"] = np.where(R.team_games_played > 0, R.games_so_far / R.team_games_played.clip(lower=1), 0.0).clip(0, 1)
    R["played_share"] = (R.games_left_played / R.team_games_left).clip(0, 1)
    print(f"  features done ({time.time() - t0:.0f}s)", flush=True)
    return R


FEATS = ["k_rush", "k_pass", "p_RB", "p_TE", "p_QB", "rep_out", "rep_doubt", "rep_q", "prac_dnp", "prac_lim", "ir_prev", "ir_season",
         "miss34_rate", "n34_short", "miss_last", "age_le23", "age_27_29", "age_30_32", "age_33p", "share_now", "wk1"]


def design(R: pd.DataFrame) -> pd.DataFrame:
    X = pd.DataFrame(index=R.index)
    X["k_rush"] = (R.kind == "rush").astype(float); X["k_pass"] = (R.kind == "pass").astype(float)
    for p in ("RB", "TE", "QB"):
        X[f"p_{p}"] = (R.pos_g == p).astype(float)
    for c in ("rep_out", "rep_doubt", "rep_q", "prac_dnp", "prac_lim", "ir_prev", "ir_season", "miss_last"):
        X[c] = R[c].astype(float)
    X["miss34_rate"] = np.where(R.n34 > 0, R.miss34 / R.n34.clip(lower=1), 0.0)
    X["n34_short"] = 1 - R.n34.clip(upper=HIST_N) / HIST_N          # the share of the 34 not on record (a young player)
    X["age_le23"] = (R.age < 24).astype(float); X["age_27_29"] = R.age.between(27, 30, inclusive="left").astype(float)
    X["age_30_32"] = R.age.between(30, 33, inclusive="left").astype(float); X["age_33p"] = (R.age >= 33).astype(float)
    X["share_now"] = R.share_now.astype(float); X["wk1"] = (R.team_games_played == 0).astype(float)
    return X[FEATS]


def fit_logit(R: pd.DataFrame, C=1.0):
    from sklearn.linear_model import LogisticRegression
    X = design(R).values; n = R.team_games_left.values.astype(float); y = R.games_left_played.clip(upper=R.team_games_left).values.astype(float)
    XX = np.vstack([X, X]); yy = np.r_[np.ones(len(X)), np.zeros(len(X))]; ww = np.r_[y, n - y]
    m = LogisticRegression(C=C, max_iter=5000).fit(XX, yy, sample_weight=ww)
    return m


def predict(m, R):
    return m.predict_proba(design(R).values)[:, 1]


# ---------------------------------------------------------------- scoring
def proj(R, share, b):
    return (1 - b) * (R.yards_so_far + R.yards_pg * R.team_games_left * share) + b * R.pace_yards


def mae(R, share, b):
    return float((proj(R, share, b) - R.actual_yards).abs().mean())


def fit_variant(v, F, k):
    """Constants of the variant fitted on the 2016-18 rows F of kind k (F carries the out-of-season prediction p)."""
    best = None
    if v == "flat":
        for a in BT.AVAIL_GRID:
            for b in BT.BLEND_GRID:
                e = mae(F, float(a), b); best = min(best or (1e18,), (e, {"avail": float(a), "blend": b}), key=lambda x: x[0])
    elif v == "share":
        for b in BT.BLEND_GRID:
            e = mae(F, F.p, b); best = min(best or (1e18,), (e, {"blend": b}), key=lambda x: x[0])
    elif v == "capped":
        for b in BT.BLEND_GRID:
            e = mae(F, F.p.clip(0.3, 1.0), b); best = min(best or (1e18,), (e, {"blend": b}), key=lambda x: x[0])
    elif v == "scaled":
        for s in SCALE_GRID:
            for b in BT.BLEND_GRID:
                e = mae(F, (s * F.p).clip(upper=1.0), b); best = min(best or (1e18,), (e, {"scale": float(s), "blend": b}), key=lambda x: x[0])
    elif v == "mult":
        pbar = float(F.p.mean())
        for lam in LAM_GRID:
            mlt = 1 + lam * (F.p / pbar - 1)
            for a in BT.AVAIL_GRID:
                for b in BT.BLEND_GRID:
                    e = mae(F, (a * mlt).clip(upper=1.0), b); best = min(best or (1e18,), (e, {"avail": float(a), "lam": lam, "pbar": round(pbar, 4), "blend": b}), key=lambda x: x[0])
    return best


def share_of(v, R, c):
    if v == "flat":
        return pd.Series(c["avail"], index=R.index)
    if v == "share":
        return R.p
    if v == "capped":
        return R.p.clip(0.3, 1.0)
    if v == "scaled":
        return (c["scale"] * R.p).clip(upper=1.0)
    if v == "mult":
        return (c["avail"] * (1 + c["lam"] * (R.p / c["pbar"] - 1))).clip(upper=1.0)


def stats(g, share, b):
    pj = proj(g, share, b); err = (pj - g.actual_yards).abs(); rel = err / g.actual_yards.clip(lower=1)
    return {"n": int(len(g)), "mae": float(err.mean()), "pace_mae": float((g.pace_yards - g.actual_yards).abs().mean()), "bias": float((pj - g.actual_yards).mean()),
            "within10": float((rel <= 0.10).mean()), "within20": float((rel <= 0.20).mean()),
            "games_miss": float((share * g.team_games_left - g.games_left_played).abs().mean()),
            "within20_top": float(rel[pj.groupby([g.season, g.week]).rank(ascending=False, method="first") <= PS.TOPW[g.kind.iloc[0]]].le(0.20).mean())}


VARIANTS = ["flat", "share", "mult", "capped", "scaled"]
TODAY = {"rec": (0.65, 0.5), "rush": (0.625, 0.5), "pass": (0.525, 0.75)}


def study(rows=ROWS):
    t0 = time.time()
    R = pd.read_csv(rows); R = R[R.team_games_left > 0].reset_index(drop=True)
    print(f"rows {len(R)}", flush=True)
    R = features(R)
    fitm = R.season.isin(BT.FIT_SEASONS)
    # out-of-season predictions on 2016-18, the full 2016-18 fit for everything after
    R["p"] = np.nan
    for s in BT.FIT_SEASONS:
        m = fit_logit(R[fitm & (R.season != s)]); R.loc[fitm & (R.season == s), "p"] = predict(m, R[fitm & (R.season == s)])
    M = fit_logit(R[fitm]); R.loc[~fitm, "p"] = predict(M, R[~fitm])
    R["p_insample"] = predict(M, R)
    coef = pd.Series(np.r_[M.intercept_, M.coef_[0]], index=["intercept"] + FEATS)
    print("logit coefficients:\n" + coef.round(3).to_string(), flush=True)
    print(f"  model fitted ({time.time() - t0:.0f}s)", flush=True)
    out = [{"row": "coef", "variant": "logit", "kind": "all", "window": "2016-18", "asof_week": "all", "feature": f, "value": float(c)} for f, c in coef.items()]
    # feature prevalence by window (the report features shift: from 2019 the roster marks game-day inactives INA, so
    # players ruled out are mostly not in the rows at all)
    R["win"] = np.where(fitm, "2016-18", np.where(R.season <= 2022, "2019-22", "2023-25"))
    X = design(R)
    for (w, k), idx in R.groupby(["win", "kind"]).groups.items():
        for f in ["rep_out", "rep_doubt", "rep_q", "prac_dnp", "prac_lim", "ir_prev", "ir_season", "miss_last", "miss34_rate", "share_now"]:
            out.append({"row": "prevalence", "variant": "", "kind": k, "window": w, "asof_week": "all", "feature": f, "value": float(X.loc[idx, f].mean())})
        out.append({"row": "prevalence", "variant": "", "kind": k, "window": w, "asof_week": "all", "feature": "ir_now", "value": float(R.loc[idx, "ir_now"].mean())})
    consts = {}
    for k in KINDS:
        F = R[fitm & (R.kind == k)]
        for v in VARIANTS:
            e, c = fit_variant(v, F, k); consts[(k, v)] = c
            out.append({"row": "fit", "variant": v, "kind": k, "window": "2016-18", "asof_week": "all", "mae": e, "n": len(F), "feature": str(c)})
            print(f"fit {k} {v}: {c} error {e:.1f}", flush=True)
        c = {"avail": TODAY[k][0], "blend": TODAY[k][1]}; consts[(k, "today")] = c
    print(f"  constants fitted ({time.time() - t0:.0f}s)", flush=True)
    T = R[~fitm].copy(); T["window"] = np.where(T.season <= 2022, "2019-22", "2023-25")
    for k in KINDS:
        for v in ["today"] + VARIANTS:
            c = consts[(k, v)]; vv = "flat" if v == "today" else v
            for (w, wk), g in T[T.kind == k].groupby(["window", "week"]):
                out.append({"row": "mae", "variant": v, "kind": k, "window": w, "asof_week": str(wk), **stats(g, share_of(vv, g, c), c["blend"])})
            for w, g in T[T.kind == k].groupby("window"):
                out.append({"row": "mae", "variant": v, "kind": k, "window": w, "asof_week": "all", **stats(g, share_of(vv, g, c), c["blend"])})
    # calibration: predicted share (p) against the realised share of the games left, in bands, test seasons (and 2016-18 out of season)
    bands = [0, 0.3, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0001]
    lab = ["<0.3", "0.3-0.5", "0.5-0.6", "0.6-0.7", "0.7-0.8", "0.8-0.9", "0.9-1"]
    R["band"] = pd.cut(R.p, bands, labels=lab, right=False)
    for (w, k, bd), g in R.groupby(["win", "kind", "band"], observed=True):
        out.append({"row": "calib", "variant": "logit", "kind": k, "window": w, "asof_week": "all", "feature": str(bd), "n": len(g),
                    "pred": float((g.p * g.team_games_left).sum() / g.team_games_left.sum()), "real": float(g.games_left_played.clip(upper=g.team_games_left).sum() / g.team_games_left.sum())})
    for (w, bd), g in R.groupby(["win", "band"], observed=True):
        out.append({"row": "calib", "variant": "logit", "kind": "all", "window": w, "asof_week": "all", "feature": str(bd), "n": len(g),
                    "pred": float((g.p * g.team_games_left).sum() / g.team_games_left.sum()), "real": float(g.games_left_played.clip(upper=g.team_games_left).sum() / g.team_games_left.sum())})
    # the share model's own fit: log loss and games-left miss against a flat kind rate (the 2016-18 mean share)
    for w, g in R.groupby("win"):
        for k, x in g.groupby("kind"):
            base = float(R[fitm & (R.kind == k)].games_left_played.sum() / R[fitm & (R.kind == k)].team_games_left.sum())
            y = x.games_left_played.clip(upper=x.team_games_left); n = x.team_games_left
            ll = lambda q: float(-(y * np.log(q) + (n - y) * np.log(1 - q)).sum() / n.sum())
            out.append({"row": "share_fit", "variant": "logit", "kind": k, "window": w, "asof_week": "all", "n": len(x),
                        "logloss": ll(x.p.clip(1e-4, 1 - 1e-4)), "logloss_flat": ll(np.full(len(x), base)),
                        "games_miss": float((x.p * n - y).abs().mean()), "games_miss_flat": float((base * n - y).abs().mean()), "value": base})
    o = pd.DataFrame(out)
    o.to_csv(REP / "player_availability.csv", index=False)
    R[["kind", "player_id", "season", "week", "p", "played_share", "team_games_left", "games_left_played"] + FEATS[:0]].to_csv(SCR / "pred.csv", index=False)
    print(f"done ({time.time() - t0:.0f}s)", flush=True)
    return o


def _md(df: pd.DataFrame) -> str:
    cols = list(df.columns); lines = ["| " + " | ".join(map(str, cols)) + " |", "|" + "---|" * len(cols)]
    for r in df.itertuples(index=False):
        lines.append("| " + " | ".join(("" if (isinstance(x, float) and np.isnan(x)) else (f"{x:.3f}" if isinstance(x, float) and abs(x) < 10 else (f"{x:.1f}" if isinstance(x, float) else str(x)))) for x in r) + " |")
    return "\n".join(lines)


def verdict(o: pd.DataFrame) -> pd.DataFrame:
    """The pre-registered rule per kind x variant against flat."""
    m = o[o.row == "mae"]; rows = []
    for k in KINDS:
        base = m[(m.kind == k) & (m.variant == "flat")].set_index(["window", "asof_week"]).mae
        for v in ["share", "mult", "capped", "scaled"]:
            x = m[(m.kind == k) & (m.variant == v)].set_index(["window", "asof_week"]).mae
            gains = {w: float(base[(w, "all")] - x[(w, "all")]) for w in WINDOWS}; g = min(gains.values())
            worst = max(float(x[i] - base[i]) for i in x.index if i[1] != "all")
            wi = max((i for i in x.index if i[1] != "all"), key=lambda i: float(x[i] - base[i]))
            ok = g > 0 and worst <= g
            rows.append({"kind": k, "variant": v, "gain_2019-22": gains["2019-22"], "gain_2023-25": gains["2023-25"], "smaller_gain": g,
                         "worst_week": f"{wi[0]} wk {wi[1]}", "worst_week_loss": worst, "passes": "yes" if ok else "no"})
    V = pd.DataFrame(rows)
    V["adopted"] = ""
    for k in KINDS:
        ok = V[(V.kind == k) & (V.passes == "yes") & (V.variant != "scaled")]
        if len(ok):
            V.loc[(ok["gain_2019-22"] + ok["gain_2023-25"]).idxmax(), "adopted"] = "ADOPT"
    return V


def report():
    o = pd.read_csv(REP / "player_availability.csv"); o["asof_week"] = o.asof_week.astype(str)
    full = (REP / "player_availability.md").read_text()
    tail = ("\n## Verdict" + full.split("\n## Verdict", 1)[1]) if "\n## Verdict" in full else ""   # hand-written verdict kept across reruns
    md = full.split("\n## Results")[0].rstrip() + "\n"
    m = o[(o.row == "mae")]
    fits = o[o.row == "fit"].set_index(["kind", "variant"])
    t = m[m.asof_week == "all"][["kind", "variant", "window", "n", "mae", "pace_mae", "bias", "within10", "within20", "within20_top", "games_miss"]].copy()
    t["n"] = t.n.astype(int); t["bias"] = t.bias.round(1)
    order = {v: i for i, v in enumerate(["today", "flat", "share", "mult", "capped", "scaled"])}
    t = t.sort_values(["kind", "window", "variant"], key=lambda c: c.map(order) if c.name == "variant" else c)
    t = t[t.variant != "today"]
    md += "\n## Results\n\n### Season-total error by kind, variant and window (every projected player, as of weeks 1, 5, 9, 13)\n\n"
    md += "games_miss = mean absolute miss on the games left he played (share x team games left against what he played).\n\n" + _md(t) + "\n"
    md += "\nConstants fitted on 2016-18 (the blend always refit; fit_mae = 2016-18 season-total error with out-of-season shares):\n\n"
    fc = fits.reset_index()[["kind", "variant", "feature", "mae"]].rename(columns={"feature": "constants", "mae": "fit_mae"})
    md += _md(fc) + "\n"
    V = verdict(o)
    md += "\n### The rule, per kind and variant (against flat)\n\n" + _md(V) + "\n"
    md += "\n### Per as-of week (season-total MAE; flat against each variant)\n\n"
    wk = m[(m.asof_week != "all") & (m.variant.isin(["flat", "share", "mult", "capped", "scaled"]))].pivot_table(index=["kind", "window", "asof_week"], columns="variant", values="mae").reset_index()
    wk["asof_week"] = wk.asof_week.astype(int); wk = wk.sort_values(["kind", "window", "asof_week"])
    for v in ["share", "mult", "capped", "scaled"]:
        wk[f"{v}-flat"] = wk[v] - wk.flat
    md += _md(wk[["kind", "window", "asof_week", "flat", "mult", "mult-flat", "share-flat", "capped-flat", "scaled-flat"]]) + "\n"
    md += "\n### Calibration: predicted against realised share of the team's games left played (logit p; weighted by games left)\n\n"
    c = o[(o.row == "calib") & (o.kind == "all")][["window", "feature", "n", "pred", "real"]].rename(columns={"feature": "band"})
    cw = c.pivot_table(index="band", columns="window", values=["n", "pred", "real"], sort=False)
    cw.columns = [f"{a}_{b}" for a, b in cw.columns]; cw = cw.reset_index()
    order_b = ["<0.3", "0.3-0.5", "0.5-0.6", "0.6-0.7", "0.7-0.8", "0.8-0.9", "0.9-1"]
    cw = cw.set_index("band").reindex(order_b).reset_index()
    cols = ["band"] + [f"{a}_{w}" for w in ["2016-18", "2019-22", "2023-25"] for a in ("n", "pred", "real")]
    cw = cw[cols]
    for cc in cw.columns:
        if cc.startswith("n_"):
            cw[cc] = cw[cc].fillna(0).astype(int)
    md += "(2016-18 rows are out-of-season predictions.) By kind: `calib` rows in the csv.\n\n" + _md(cw) + "\n"
    sf = o[o.row == "share_fit"][["kind", "window", "n", "logloss", "logloss_flat", "games_miss", "games_miss_flat"]].copy(); sf["n"] = sf.n.astype(int)
    md += "\n### The share model itself (against the flat 2016-18 rate of the kind)\n\n" + _md(sf) + "\n"
    cf = o[o.row == "coef"][["feature", "value"]].rename(columns={"value": "coef"})
    md += "\n### The model\n\nBinomial logistic regression, pooled over kinds, fitted on 2016-18 (sklearn LogisticRegression, L2, C=1, " \
          "each row as games played / not played of the team's games left). Features (all as of the week):\n\n" + _md(cf) + "\n"
    pv = o[o.row == "prevalence"].pivot_table(index="feature", columns=["window"], values="value", aggfunc="mean").reset_index()
    md += "\nFeature means by window (mean over kinds):\n\n" + _md(pv) + "\n"
    (REP / "player_availability.md").write_text(md.rstrip() + "\n" + tail)
    return V


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "build":
        only = (int(a[a.index("--only") + 1]), int(a[a.index("--only") + 2])) if "--only" in a else None
        jobs = int(a[a.index("--jobs") + 1]) if "--jobs" in a else 1
        build(only, jobs)
    elif a and a[0] == "study":
        study(Path(a[a.index("--rows") + 1]) if "--rows" in a else ROWS)
    elif a and a[0] == "report":
        print(report().to_string(index=False))
    else:
        print(__doc__)
