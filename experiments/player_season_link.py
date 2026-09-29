"""Player season totals: the team's volume linked to its season outlook, and usage-stability priors by age (29 Sep 2026).

Today a projected player's per-game volume for the games left = his usage share x his team's plays per game of that kind
over its last 17 (props.teams_volume), and the season total = so far + per game x games left x AVAIL, blended BLEND of
the way toward pace (nflmodel/player_season.py; harness experiments/player_season_backtest.py). Two questions:

Part 1: the team volume V used for the games LEFT.
  base   the last-17 average (today)
  b25/b50  blended 0.25 / 0.5 of the way toward the league's mean plays per game of that kind as of the week (the mean
         of the 32 teams' last-17 figures)
  c25/c50  blended 0.25 / 0.5 toward the team's previous full regular season (2016 has no charted 2015: base)
  d      a game-script adjustment over the remaining schedule from OUR game model only: for each game left the team's
         expected margin from season.py's equation (profiles + fit_asof + expected_points on the as-of frame, no lines,
         wind at its stand-in, no absences), through props.game_script(kind, V, margin, total=None); averaged over the
         games left. game_script carries the per-game engine's fitted intercept (about -0.6 pass plays, +0.34 runs) as
         well as the margin slope; d_m keeps the margin term only (V + slope x mean margin), since the intercept is not
         about the outlook and a constant shift is what AVAIL absorbs
  e      c and d together (every pair of c25/c50 with d/d_m), for the kinds where both help
Part 2: a usage-stability ratio by position group and age band, fitted on 2016-18 only: for each projected player,
  a = his touches of the kind over the games left that he played (any touch, on the profile's team), e = his as-of
  share x his team's plays of the kind in those games; the band's ratio = sum(a) / sum(e), shrunk toward 1 with K_AGE
  players of weight ((n x r + K_AGE) / (n + K_AGE)); age at the season's September 1 from data/raw/players/players.parquet.
  p2 applies the ratio to the share for the games left (yards and touchdowns per game x ratio); p2_all fits the same
  ratio over every game left, played or not (so it carries the age's availability too, which AVAIL then refits around).
  Tested alone and on top of the best Part 1 variant for the kind.

Every variant is a per-(season, as-of week, team, kind) or per-player factor on the cached per-game columns, which is
exact: per_game is share x V x rate, so a different V for the games left multiplies yards_pg and td_pg by V'/V. The
set of projected players stays the base's (the MIN_PG cut and the starting QB are decided on the last-17 volume, as the
page does). The base rows are the harness cache (reports/player_season_rows.csv) after a check that one as-of point
rebuilt from today's data matches it (else they are rebuilt here); this study's own copies live in the scratchpad.
They are the harness as it stood when this study was set (flat AVAIL, before commit 8e6706c0 gave each player his own
availability and kept game-day inactives in the backtest): 10,801 rows. experiments/player_season_link2.py reran these
variants on today's rule.

Scoring, exactly as the harness: AVAIL and BLEND refit on 2016-18 for each variant on the same grids (they interact
with any change to the per-game number), then season-total MAE by kind on 2019-22 and 2023-25 (as-of weeks pooled and
per week) beside the pace and last-season baselines, bias, the within-10% and within-20% shares and within-20% on the
top of the list. Adoption rule (fixed before the results): a variant is adopted for a kind only if its pooled MAE is
lower than the base's on BOTH windows, and on no as-of week of either window is it worse than the base by more than
the smaller of the two pooled gains.

No market input anywhere (spread_line, total_line and the implied numbers are never read); everything as of the week.
Writes reports/player_season_link.csv and reports/player_season_link.md; does not touch the harness's files.
"""
from __future__ import annotations
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import numpy as np, pandas as pd
from nflmodel import player_season as PS, props as PR, season as SE
from nflmodel.positions import names_by_id
from experiments import player_season_backtest as BT

SCRATCH = Path("/tmp/claude-0/-home-user/c1e0d18e-681a-50ba-b0bb-6c809c2e3dee/scratchpad/player_season")
SCRATCH.mkdir(parents=True, exist_ok=True)
SEASONS = BT.FIT_SEASONS + BT.TEST_SEASONS
KIND_VOL = {"rec": "pass_plays_pg", "rush": "runs_pg", "pass": "dropbacks_pg"}
TARGETABLE = 0.97   # per_game's share of pass plays that are targets (player_season.per_game): the share is volume_pg / (V x 0.97)
K_AGE = 30
ERRS: dict = {}   # variant -> its per-row test errors (for the clustered standard error of the gain)
AGE_BANDS = [(0, 24, "<=24"), (25, 27, "25-27"), (28, 30, "28-30"), (31, 99, "31+")]
POS_GROUP = {"rec": {"WR": "WR", "TE": "TE", "RB": "RB", "FB": "RB", "HB": "RB"}, "rush": {"RB": "RB", "FB": "RB", "HB": "RB", "QB": "QB", "WR": "WR", "TE": "WR"}, "pass": {"QB": "QB"}}
PART1 = ["base", "b25", "b50", "c25", "c50", "d", "d_m", "e_c25_d", "e_c25_d_m", "e_c50_d", "e_c50_d_m"]
KINDS = ("rec", "rush", "pass")


def load():
    games = pd.read_parquet(PS.OUT / "games.parquet")
    d = PR.official(pd.read_parquet(PS.OUT / "scheme_plays.parquet"))
    return games, d


def base_rows(games, d) -> pd.DataFrame:
    """The harness's cached rows, checked against a fresh build of one as-of point (2019 week 5); rebuilt here when
    the check fails. Kept in the scratchpad."""
    f = SCRATCH / "rows_base.csv"
    if f.exists():
        return pd.read_csv(f)
    names = names_by_id(range(2014, 2027)); t0 = time.time()
    p = BT.rows_for(d, games, names, 2019, 5)
    print(f"check build 2019 week 5: {len(p)} rows in {time.time() - t0:.0f}s", flush=True)
    ok = False
    if BT.CACHE.exists():
        C = pd.read_csv(BT.CACHE); c = C[(C.season == 2019) & (C.week == 5)]
        m = c.merge(p, on=["kind", "player_id"], suffixes=("_c", "_n"), how="outer", indicator=True)
        same = (m._merge == "both").all() and len(m) == len(p)
        diff = max(float((m[x + "_c"] - m[x + "_n"]).abs().max()) for x in ["volume_pg", "rate", "yards_pg", "yards_so_far", "pace_yards", "actual_yards", "team_games_left"]) if same else np.inf
        ok = same and diff < 0.002
        print(f"harness cache {'matches' if ok else 'differs from'} the fresh build (max diff {diff:.4f}, same players {same})", flush=True)
    if ok:
        R = C
    else:
        rows = []
        for s in SEASONS:
            for w in BT.WEEKS:
                if s == 2016 and w == 1:
                    continue
                x = BT.rows_for(d, games, names, s, w); rows.append(x)
                print(f"{s} week {w}: {len(x)} players ({time.time() - t0:.0f}s)", flush=True)
        R = pd.concat(rows, ignore_index=True).round(3)
    R.to_csv(f, index=False)
    return R


def team_volume_table(games, d) -> pd.DataFrame:
    """One row per (season, as-of week, team, kind): the last-17 volume (base), the league mean as of the week, the team's
    previous full regular season, and the game-script average over the games left from the game model's margins."""
    f = SCRATCH / "team_volume.csv"
    if f.exists():
        return pd.read_csv(f)
    fr = SE._frame(); pred = pd.read_parquet(PS.OUT / "pred_v3.parquet")
    out = []; t0 = time.time()
    for s in SEASONS:
        reg = games[(games.season == s) & (games.game_type == "REG")]
        dome_of = {}
        for r in reg.itertuples():
            dome_of[r.home_team] = float(r.dome) if pd.notna(r.dome) else dome_of.get(r.home_team, 0.0)
        dp = d[(d.season == s - 1) & (d.week <= 18)]
        prev = {}
        for team, g in dp.groupby("posteam"):
            n = max(g.game_id.nunique(), 1)
            prev[team] = {"pass_plays_pg": float(g.pass_play.sum()) / n, "runs_pg": float(g.play_type.eq("run").sum()) / n, "dropbacks_pg": float(g.dropback.sum()) / n}
        for w in BT.WEEKS:
            if s == 2016 and w == 1:
                continue
            a = PR._asof(d, s, w); V = PR.teams_volume(a)
            league = {vk: float(np.mean([v[vk] for v in V.values() if v.get(vk)])) for vk in KIND_VOL.values()}
            P = SE.profiles(fr, s, w); fit = SE.fit_asof(pred, s, w)
            left = reg[reg.week >= w]
            margins = {}
            for g in left.itertuples():
                if g.home_team in P and g.away_team in P:
                    neu = 1.0 if (pd.notna(g.neutral) and g.neutral == 1) else 0.0; dg = 1.0 if g.div_game == 1 else 0.0; dm = 0.0 if neu else dome_of.get(g.home_team, 0.0)
                    eh = SE.expected_points(P[g.home_team], P[g.away_team], fit, 0.0 if neu else 1.0, neu, dm, dg, int(g.week))
                    ea = SE.expected_points(P[g.away_team], P[g.home_team], fit, 0.0, neu, dm, dg, int(g.week))
                    margins.setdefault(g.home_team, []).append(eh - ea); margins.setdefault(g.away_team, []).append(ea - eh)
                else:
                    margins.setdefault(g.home_team, []).append(0.0); margins.setdefault(g.away_team, []).append(0.0)
            for team, v in V.items():
                ms = margins.get(team, [])
                for k, vk in KIND_VOL.items():
                    b = float(v.get(vk, 0.0))
                    gs = float(np.mean([PR.game_script(k, b, m, None) for m in ms])) if ms else b
                    gs_m = b + PR.GS[k][1] * float(np.mean(ms)) if ms else b
                    out.append({"season": s, "week": w, "team": team, "kind": k, "base": b, "league": league[vk], "prev": prev.get(team, {}).get(vk, np.nan), "gs": gs, "gs_m": gs_m, "n_left": len(ms), "mean_margin": float(np.mean(ms)) if ms else 0.0})
            print(f"volume {s} week {w} ({time.time() - t0:.0f}s)", flush=True)
    T = pd.DataFrame(out); T.to_csv(f, index=False)
    return T


def touches_left(R: pd.DataFrame, d: pd.DataFrame) -> pd.DataFrame:
    """For every base row: his touches of the kind over the games left (regular season, on the profile's team), the
    team's plays of the kind over the same games, both over every game left and over the games he played (any touch)."""
    f = SCRATCH / "touches_left.csv"
    if f.exists():
        return pd.read_csv(f)
    x = d[d.week <= 18]
    keys = ["season", "week", "game_id", "posteam"]
    mine = {"rec": x[x.pass_play & x.receiver_player_id.notna()].groupby(["receiver_player_id"] + keys).size().rename("n").reset_index().rename(columns={"receiver_player_id": "player_id"}),
            "rush": x[x.play_type.eq("run") & x.rusher_player_id.notna()].groupby(["rusher_player_id"] + keys).size().rename("n").reset_index().rename(columns={"rusher_player_id": "player_id"}),
            "pass": x[x.dropback & x.passer_player_id.notna()].groupby(["passer_player_id"] + keys).size().rename("n").reset_index().rename(columns={"passer_player_id": "player_id"})}
    team = {"rec": x[x.pass_play].groupby(keys).size().rename("t"), "rush": x[x.play_type.eq("run")].groupby(keys).size().rename("t"), "pass": x[x.dropback].groupby(keys).size().rename("t")}
    played = pd.concat([m[["player_id"] + keys] for m in mine.values()]).drop_duplicates(["player_id", "game_id"])
    out = []
    for k in KINDS:
        rk = R[R.kind == k][["kind", "player_id", "season", "week", "team"]].drop_duplicates()
        tk = team[k].reset_index()
        mk = mine[k].rename(columns={"week": "gweek"})
        pl = played.rename(columns={"week": "gweek"})
        for s, w in rk[["season", "week"]].drop_duplicates().itertuples(index=False):
            rows = rk[(rk.season == s) & (rk.week == w)]
            tg = tk[(tk.season == s) & (tk.week >= w)]                      # every team-game left
            tp = tg.groupby("posteam").t.sum()
            mg = mk[(mk.season == s) & (mk.gweek >= w)]                      # his touches in games left
            pg = pl[(pl.season == s) & (pl.gweek >= w)].merge(tg[["game_id", "posteam", "t"]], on=["game_id", "posteam"])   # games he played, with the team's plays
            m_all = mg.groupby(["player_id", "posteam"]).n.sum(); p_t = pg.groupby(["player_id", "posteam"]).t.sum(); p_n = pg.groupby(["player_id", "posteam"]).size()
            for r in rows.itertuples():
                key = (r.player_id, r.team)
                out.append({"kind": k, "player_id": r.player_id, "season": s, "week": w, "team": r.team, "a_all": float(m_all.get(key, 0.0)), "t_all": float(tp.get(r.team, 0.0)),
                            "a_played": float(m_all.get(key, 0.0)), "t_played": float(p_t.get(key, 0.0)), "n_played": int(p_n.get(key, 0))})
    T = pd.DataFrame(out); T.to_csv(f, index=False)
    return T


def ages(R: pd.DataFrame) -> pd.Series:
    """Age at the season's September 1, from the players table (NaN when the birth date is unknown)."""
    p = pd.read_parquet(PS.RAW / "players" / "players.parquet", columns=["gsis_id", "birth_date"]).dropna(subset=["gsis_id"]).drop_duplicates("gsis_id")
    born = dict(zip(p.gsis_id, pd.to_datetime(p.birth_date, errors="coerce")))
    sep1 = pd.to_datetime(R.season.astype(int).astype(str) + "-09-01")
    b = pd.to_datetime(R.player_id.map(born))
    return ((sep1 - b).dt.days / 365.25).round(2)


def age_band(age: float) -> str:
    if pd.isna(age):
        return "unknown"
    age = int(np.floor(age))   # whole years at September 1 (29 Sep 2026: fractional ages fell between the bands)
    for lo, hi, lab in AGE_BANDS:
        if lo <= age <= hi:
            return lab
    return "unknown"


def fit_age_ratios(R: pd.DataFrame, T: pd.DataFrame, V: pd.DataFrame, mode: str = "played", k: float = K_AGE) -> pd.DataFrame:
    """The usage-stability ratio by (kind, position group, age band) on 2016-18: sum of touches over the games left over
    the sum of what the as-of share expected in those games, shrunk toward 1 with k players of weight."""
    X = R[R.season.isin(BT.FIT_SEASONS) & (R.team_games_left > 0)].merge(T, on=["kind", "player_id", "season", "week", "team"], how="left")
    X = X.merge(V[["season", "week", "team", "kind", "base"]], on=["season", "week", "team", "kind"], how="left")
    if mode == "played":
        X = X[X.n_played > 0]
    a = X.a_played if mode == "played" else X.a_all
    sh = pd.Series(np.where(X.kind == "pass", 1.0, X.volume_pg / X.base.replace(0, np.nan) / np.where(X.kind == "rec", TARGETABLE, 1.0)), index=X.index)
    e = sh * (X.t_played if mode == "played" else X.t_all)
    X = X.assign(a=a, e=e, pos_group=[POS_GROUP[kk].get(pp, "other") for kk, pp in zip(X.kind, X.pos)], age_band=[age_band(x) for x in X.age])
    X = X[X.e.notna() & (X.e > 0)]
    rows = []
    for (kk, pg, ab), g in X.groupby(["kind", "pos_group", "age_band"]):
        n = len(g); raw = float(g.a.sum() / g.e.sum())
        rows.append({"kind": kk, "pos_group": pg, "age_band": ab, "n": n, "ratio_raw": round(raw, 4), "ratio": round((n * raw + k) / (n + k), 4), "mean_age": round(float(g.age.mean()), 1) if g.age.notna().any() else np.nan})
    return pd.DataFrame(rows)


def age_factor(R: pd.DataFrame, ratios: pd.DataFrame) -> pd.Series:
    key = {(r.kind, r.pos_group, r.age_band): r.ratio for r in ratios.itertuples() if r.pos_group != "other" and r.age_band != "unknown"}
    return pd.Series([key.get((kk, POS_GROUP[kk].get(pp, "other"), age_band(ag)), 1.0) for kk, pp, ag in zip(R.kind, R.pos, R.age)], index=R.index)


def volume_factor(R: pd.DataFrame, V: pd.DataFrame, variant: str) -> pd.Series:
    """V'/V per row for a Part 1 variant (1 where the team's volume is missing)."""
    X = R[["season", "week", "team", "kind"]].merge(V, on=["season", "week", "team", "kind"], how="left")
    b = X.base.replace(0, np.nan)
    prev = X.prev.fillna(X.base)
    def blend(col, w):
        return ((1 - w) * X.base + w * col) / b
    parts = variant.split("_") if variant.startswith("e_") else [variant]
    f = pd.Series(1.0, index=X.index)
    if variant == "base":
        return f.fillna(1.0)
    cpart = next((p for p in parts if p.startswith("c")), None); bpart = next((p for p in parts if p.startswith("b")), None)
    dpart = "d_m" if variant.endswith("d_m") else ("d" if variant.endswith("d") else None)
    base_adj = X.base.copy()
    if cpart:
        w = int(cpart[1:]) / 100; base_adj = (1 - w) * X.base + w * prev
    if bpart:
        w = int(bpart[1:]) / 100; base_adj = (1 - w) * X.base + w * X.league
    if dpart:
        # the game-script move is a shift on the last-17 number (the engine's own form); the same shift on the blended base
        shift = (X.gs if dpart == "d" else X.gs_m) - X.base
        base_adj = (base_adj + shift).clip(lower=0)
    return (base_adj / b).fillna(1.0)


def fit_constants(fit: pd.DataFrame) -> tuple[dict, dict, dict]:
    avail, blend, err = {}, {}, {}
    for k in KINDS:
        fk = fit[fit.kind == k]; best = None
        for a in BT.AVAIL_GRID:
            for b in BT.BLEND_GRID:
                e = BT.evaluate(fk, {k: a}, {k: b}).err.mean()
                if best is None or e < best[0]:
                    best = (e, float(a), float(b))
        avail[k], blend[k], err[k] = best[1], best[2], best[0]
    return avail, blend, err


def score(R: pd.DataFrame, factor: pd.Series, variant: str) -> list[dict]:
    """Refit AVAIL and BLEND on 2016-18 with the factor on the per-game columns, then the test windows pooled and per week."""
    X = R.copy(); X["yards_pg"] = X.yards_pg * factor; X["td_pg"] = X.td_pg * factor
    fit = X[X.season.isin(BT.FIT_SEASONS)]; test = X[X.season.isin(BT.TEST_SEASONS)].copy(); test["window"] = test.season.map(BT.WINDOW)
    avail, blend, ferr = fit_constants(fit)
    out = [{"variant": variant, "row": "fit", "kind": k, "window": "2016-18", "asof_week": "all", "avail": avail[k], "blend": blend[k], "n": int((fit.kind == k).sum()), "mae": ferr[k]} for k in KINDS]
    T = BT.evaluate(test, avail, blend)
    ERRS[variant] = T[["kind", "window", "week", "season", "team", "err"]]
    def rec(k, w, wk, g):
        return {"variant": variant, "row": "mae", "kind": k, "window": w, "asof_week": wk, "avail": avail[k], "blend": blend[k], "n": int(len(g)), "mae": g.err.mean(), "pace_mae": g.pace_err.mean(), "prev_mae": g.prev_err.mean(), "bias": g.bias.mean(),
                "within10": float((g.rel <= 0.10).mean()), "within20": float((g.rel <= 0.20).mean()), "within20_top": float((g[g["rank"] <= BT.TOPW[k]].rel <= 0.20).mean()), "n_top": int((g["rank"] <= BT.TOPW[k]).sum())}
    for (k, w), g in T.groupby(["kind", "window"]):
        out.append(rec(k, w, "all", g))
    for (k, w, wk), g in T.groupby(["kind", "window", "week"]):
        out.append(rec(k, w, int(wk), g))
    return out


def adopt_check(o: pd.DataFrame, variant: str, kind: str) -> dict:
    """The rule: pooled MAE lower than base on both windows, and no as-of week worse than base by more than the smaller
    pooled gain."""
    b = o[(o.variant == "base") & (o.kind == kind) & (o.row == "mae")]; v = o[(o.variant == variant) & (o.kind == kind) & (o.row == "mae")]
    m = b.merge(v, on=["window", "asof_week"], suffixes=("_b", "_v"))
    pooled = m[m.asof_week.astype(str) == "all"].set_index("window"); gains = (pooled.mae_b - pooled.mae_v)
    weekly = m[m.asof_week.astype(str) != "all"]; worst = float((weekly.mae_b - weekly.mae_v).min()) if len(weekly) else 0.0
    both = bool((gains > 0).all()) and len(gains) == 2
    ok = both and worst >= -float(gains.min())
    se = gain_se(variant, kind)
    return {"variant": variant, "kind": kind, "gain_2019_22": round(float(gains.get("2019-22", np.nan)), 2), "gain_2023_25": round(float(gains.get("2023-25", np.nan)), 2), "worst_week": round(worst, 2), "both_windows": both, "adopt": ok,
            "se_2019_22": se.get("2019-22", np.nan), "se_2023_25": se.get("2023-25", np.nan)}


def gain_se(variant: str, kind: str) -> dict:
    """Standard error of the pooled gain (base error - variant error, the same rows) clustered by (season, team): a
    team's players and as-of weeks share its season, so they are not independent draws. For reading, not in the rule."""
    if variant not in ERRS or "base" not in ERRS:
        return {}
    b = ERRS["base"]; v = ERRS[variant]; b = b[b.kind == kind]; v = v.loc[b.index]
    x = b.assign(diff=b.err - v.err)
    out = {}
    for w, g in x.groupby("window"):
        m = g["diff"].mean(); c = (g["diff"] - m).groupby([g.season, g.team]).sum(); n = len(g); nc = len(c)
        out[w] = round(float(np.sqrt((c ** 2).sum() * nc / max(nc - 1, 1)) / n), 3)
    return out


def main():
    t0 = time.time()
    games, d = load()
    R = base_rows(games, d); R = R[R.team_games_left > 0].reset_index(drop=True)
    print(f"rows {len(R)} ({time.time() - t0:.0f}s)", flush=True)
    V = team_volume_table(games, d)
    print(f"team volume table {len(V)} ({time.time() - t0:.0f}s)", flush=True)
    T = touches_left(R, d)
    print(f"touches table {len(T)} ({time.time() - t0:.0f}s)", flush=True)
    R["age"] = ages(R)
    print(f"ages known for {R.age.notna().mean():.3f} of rows", flush=True)
    res = []; factors = {}
    for v in PART1:
        factors[v] = volume_factor(R, V, v); res += score(R, factors[v], v)
        print(f"scored {v} ({time.time() - t0:.0f}s)", flush=True)
    o = pd.DataFrame(res)
    # Part 1 winner per kind: the largest of the smaller pooled gains among the variants that pass the rule; else base
    checks = [adopt_check(o, v, k) for v in PART1[1:] for k in KINDS]
    ck = pd.DataFrame(checks)
    best1 = {}
    for k in KINDS:
        c = ck[(ck.kind == k) & ck.adopt].copy()
        if len(c):
            c["gain"] = c[["gain_2019_22", "gain_2023_25"]].min(axis=1); best1[k] = c.sort_values("gain", ascending=False).variant.iloc[0]
        else:
            best1[k] = "base"
    print("Part 1 best by kind:", best1, flush=True)
    # Part 2: the age ratios (played games; every game), alone and on the best Part 1 factor
    ratios = {m: fit_age_ratios(R, T, V, m) for m in ("played", "all")}
    for m, rt in ratios.items():
        rt.assign(mode=m).to_csv(SCRATCH / f"age_ratios_{m}.csv", index=False)
        print(rt.to_string(index=False), flush=True)
    for m, name in (("played", "p2"), ("all", "p2_all")):
        fa = age_factor(R, ratios[m]); factors[name] = fa; res += score(R, fa, name)
        fb = pd.Series([factors[best1[k]].iloc[i] for i, k in enumerate(R.kind)], index=R.index) * fa
        factors[name + "+best1"] = fb; res += score(R, fb, name + "+best1")
        print(f"scored {name} ({time.time() - t0:.0f}s)", flush=True)
    o = pd.DataFrame(res)
    ALL = PART1[1:] + ["p2", "p2_all", "p2+best1", "p2_all+best1"]
    ck = pd.DataFrame([adopt_check(o, v, k) for v in ALL for k in KINDS])
    o = pd.concat([o, ck.assign(row="adopt")], ignore_index=True)
    for m, rt in ratios.items():
        o = pd.concat([o, rt.assign(row="age_ratio", variant="p2" if m == "played" else "p2_all")], ignore_index=True)
    o["best1"] = o.kind.map(best1)
    o.round(4).to_csv(PS.REP / "player_season_link.csv", index=False)
    pd.set_option("display.width", 250)
    P = o[(o.row == "mae") & (o.asof_week.astype(str) == "all")]
    print(P.pivot_table(index=["kind", "variant"], columns="window", values=["mae", "bias", "within20"]).round(2).to_string())
    print(ck.to_string(index=False))
    write_md(o, ck, best1, ratios, time.time() - t0)


def write_md(o: pd.DataFrame, ck: pd.DataFrame, best1: dict, ratios: dict, secs: float):
    L = []
    L.append("# Player season totals: team volume linked to the outlook, and usage priors by age (29 Sep 2026)\n")
    L.append("`experiments/player_season_link.py`, rows from the harness cache (checked against a fresh build), scored exactly as `experiments/player_season_backtest.py`: AVAIL and BLEND refit on 2016-18 for every variant, then season-total MAE by kind on 2019-22 and 2023-25, as-of weeks 1, 5, 9, 13 pooled and per week. No market input; game script from our game model's margins only.\n")
    L.append("## Adoption rule (set before the results)\n")
    L.append("A variant is adopted for a kind (receiving, rushing, passing separately) only if its pooled MAE is lower than the base's on BOTH windows, and on no as-of week of either window is it worse than the base by more than the smaller of the two pooled gains.\n")
    L.append("## Variants\n")
    L.append("Part 1, the team volume V for the games left: base (last 17); b25/b50 (toward the league mean of the 32 teams' last-17 as of the week); c25/c50 (toward the team's previous full regular season; 2016 falls back to base); d (props.game_script over each game left at the game model's expected margin, no total, averaged: carries the engine's intercept); d_m (the margin slope only, no intercept); e_* (c and d together). Part 2: p2 = share x the (position group, age band) ratio fitted on 2016-18 over the games he played (K_AGE = %d players of shrink toward 1); p2_all = the ratio over every game left, played or not. Each also on the best Part 1 variant for the kind.\n" % K_AGE)
    P = o[(o.row == "mae") & (o.asof_week.astype(str) == "all")].copy()
    L.append("## Kind x variant x window (as-of weeks pooled)\n")
    L.append("| kind | variant | window | n | avail | blend | mae | pace_mae | prev_mae | bias | within10 | within20 | within20_top |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for r in P.sort_values(["kind", "variant", "window"]).itertuples():
        L.append(f"| {r.kind} | {r.variant} | {r.window} | {int(r.n)} | {r.avail} | {r.blend} | {r.mae:.1f} | {r.pace_mae:.1f} | {r.prev_mae:.1f} | {r.bias:+.1f} | {r.within10:.3f} | {r.within20:.3f} | {r.within20_top:.3f} |")
    L.append("\n## Fit (2016-18) constants and error\n")
    F = o[o.row == "fit"]
    L.append("| kind | variant | avail | blend | fit mae |"); L.append("|---|---|---|---|---|")
    for r in F.sort_values(["kind", "variant"]).itertuples():
        L.append(f"| {r.kind} | {r.variant} | {r.avail} | {r.blend} | {r.mae:.1f} |")
    L.append("\n## Adoption check (gain = base MAE - variant MAE, pooled; worst_week = the worst per-week change over both windows)\n")
    L.append("Standard errors (se) of each pooled gain are clustered by (season, team) and are for reading only; they are not part of the rule. A gain inside about two standard errors of zero is not distinguishable from noise.\n")
    L.append("| kind | variant | gain 2019-22 (se) | gain 2023-25 (se) | worst week | both windows | adopt |"); L.append("|---|---|---|---|---|---|---|")
    for r in ck.sort_values(["kind", "variant"]).itertuples():
        L.append(f"| {r.kind} | {r.variant} | {r.gain_2019_22:+.2f} ({r.se_2019_22:.2f}) | {r.gain_2023_25:+.2f} ({r.se_2023_25:.2f}) | {r.worst_week:+.2f} | {r.both_windows} | {'YES' if r.adopt else 'no'} |")
    L.append("\nNote on best1: the best Part 1 variant per kind is picked among those passing the rule by their test-window gains, so p2+best1 is a selection on the windows it is then scored on; its pass is weaker evidence than a variant's own.\n")
    L.append("\n## Per as-of week: base against the best Part 1 variant and the Part 2 variants\n")
    W = o[(o.row == "mae") & (o.asof_week.astype(str) != "all")].copy(); W["asof_week"] = W.asof_week.astype(int)
    for k in KINDS:
        show = ["base", best1[k], "p2", "p2_all", "p2+best1", "p2_all+best1"]; show = list(dict.fromkeys(show))
        L.append(f"\n### {k} (best Part 1: {best1[k]})\n")
        L.append("| window | week | n | " + " | ".join(show) + " |"); L.append("|---|---|---|" + "---|" * len(show))
        for (w, wk), g in W[(W.kind == k)].groupby(["window", "asof_week"]):
            vals = {r.variant: r.mae for r in g.itertuples()}; n = int(g.n.iloc[0])
            L.append(f"| {w} | {wk} | {n} | " + " | ".join(f"{vals.get(v, np.nan):.1f}" for v in show) + " |")
    L.append("\n## Age ratios fitted on 2016-18 (sum of touches over the games left / sum of what the as-of share expected; shrunk toward 1 with %d players)\n" % K_AGE)
    for m, rt in ratios.items():
        L.append(f"\n### {'games he played' if m == 'played' else 'every game left'} ({'p2' if m == 'played' else 'p2_all'})\n")
        L.append("| kind | pos group | age band | n | mean age | raw ratio | ratio used |"); L.append("|---|---|---|---|---|---|---|")
        for r in rt.sort_values(["kind", "pos_group", "age_band"]).itertuples():
            L.append(f"| {r.kind} | {r.pos_group} | {r.age_band} | {int(r.n)} | {r.mean_age} | {r.ratio_raw:.3f} | {r.ratio:.3f} |")
    L.append("\n## Verdict\n")
    ad = ck[ck.adopt]
    if len(ad):
        for r in ad.itertuples():
            L.append(f"- {r.kind}: {r.variant} passes (gains {r.gain_2019_22:+.2f} / {r.gain_2023_25:+.2f}, worst week {r.worst_week:+.2f}).")
    else:
        L.append("- No variant passes the rule on any kind.")
    L.append(f"\nRuntime of the scoring run: {secs:.0f}s (base rows from the harness cache; team-volume and touches tables cached in the scratchpad).\n")
    (PS.REP / "player_season_link.md").write_text("\n".join(L))


if __name__ == "__main__":
    main()
