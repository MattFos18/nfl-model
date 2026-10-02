"""The Questionable-in-totals shadow (2 Oct 2026, Matt: track it as a hidden shadow; reports/questionable_totals.md).

A second game total, never bet and never shown: the live totals equation (model.TOTAL_FEATS, refit before every week on
every played game so far, plus the wind points) with study variant T2's input added: each team's Questionable players at
the chance they sit, summed over both teams (q_skill_sum, q_off_sum, q_def_sum), and the totals' qb_out_sum taking each
team's max(qb_out, the chance last game's starting QB sits). Its over chance is read off its own training games' total
misses at the line, as model.price_at reads p_over_emp. The hidden shadow rule "shadowqtotals" (picks.SHADOWS) takes the
under at a 55%+ chance from it, weeks 1-17; the shadow watch grades it live like every shadow.

Nothing live reads this module's output: the live total, chance and rules come from model.walk_forward (pred_v3) alone.
The shadow fits its own copy of the equation (model.TOTAL_FEATS and model._game_frame are read, never replaced), writes
only data/processed/shadow/ (qt_pred.parquet, qt_dist.json, qt_inputs.parquet: a folder the page's data catalog does not
list; columns qt_*), and records pred_v3's hash before and after it runs
(standing_checks.qt_isolated checks the live columns are the same with and without it).

The Questionable pieces are built as experiments/injury_retest.py builds them (variant Q2; the rates from earlier seasons
only, last game's snap shares), cut to the four pieces T2 reads, through the current season: a listing for a game not
yet played counts without snap counts (the team-week's snaps exist only after it is played), and a team with no snaps
yet this season reads last season's last game, as Week 1 does in the backtest. On 2013-2025 the pieces equal
injury_retest.build's to 0.0, and the shadow total equals questionable_totals' T2 game for game.

    python -m nflmodel.qtotals             (the weekly run's step "qt shadow", after the model step)
    python -m nflmodel.qtotals --records   (the shadow rule's backtest record per window)
"""
from __future__ import annotations
import hashlib, json, sys, time
import numpy as np, pandas as pd
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .features import OUT, RAW, TEAM_FIX

SHADOW_DIR = OUT / "shadow"   # committed with data/processed by the weekly run; catalog.py lists only data/processed's own files, so the page never shows it
PRED, DIST, INPUTS = SHADOW_DIR / "qt_pred.parquet", SHADOW_DIR / "qt_dist.json", SHADOW_DIR / "qt_inputs.parquet"
COLS = ("qt_model_total", "qt_p_over_emp")   # the shadow's columns: nothing live reads them
FIRST_SEASON = 2013   # the pieces from here (2013 carries none: no earlier rates)
GROUP = {"QB": "QB", "RB": "RB", "FB": "RB", "HB": "RB", "WR": "WR", "TE": "TE", "T": "OL", "G": "OL", "C": "OL", "OT": "OL", "OG": "OL", "OL": "OL",
         "DE": "DL", "DT": "DL", "NT": "DL", "DL": "DL", "LB": "LB", "ILB": "LB", "OLB": "LB", "MLB": "LB", "CB": "DB", "S": "DB", "SS": "DB", "FS": "DB", "DB": "DB",
         "K": "ST", "P": "ST", "LS": "ST"}   # experiments/injury_retest.py GROUP
SKILL_G = {"RB", "WR", "TE"}
SHRINK = 20.0   # each (group, practice) cell shrunk toward its practice status's rate with this many listings
PIECES = {"q_skill": "q1_skill", "q_off": "q2_off", "q_def": "q2_def", "q_qb": "q2_qb"}
ALPHA = 10.0   # model.total_model's ridge penalty


def feats() -> list[str]:
    """The shadow's totals inputs: the live equation's, with qb_out_sum replaced by qb_out_t_sum, plus the three sums."""
    from . import model as M
    return [("qb_out_t_sum" if c == "qb_out_sum" else c) for c in M.TOTAL_FEATS] + ["q_skill_sum", "q_off_sum", "q_def_sum"]


# ---- the Questionable pieces (experiments/injury_retest.build, Q2's part) ----

def practice(s) -> str:
    s = str(s) if isinstance(s, str) else ""
    return "dnp" if s.startswith("Did Not") else "limited" if s.startswith("Limited") else "full" if s.startswith("Full") else "none"


def _snaps(seasons) -> pd.DataFrame:
    from .ids import map_pfr
    fs = [RAW / "snap_counts" / f"snap_counts_{s}.parquet" for s in seasons]
    fs = [f for f in fs if f.exists()]
    if not fs:
        raise FileNotFoundError("no snap count files in data/raw/snap_counts")
    sn = pd.concat([pd.read_parquet(f) for f in fs], ignore_index=True)
    sn["team"] = sn.team.replace(TEAM_FIX); sn["key"] = map_pfr(sn)
    return sn


def listings(inj: pd.DataFrame, sn: pd.DataFrame, out_by: dict, unplayed: set) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Every Questionable listing (regular season, not otherwise out). Returns (graded, priced): graded = the listings of
    team-weeks with snap counts, with sat = took no snap (the rates learn from these, injury_retest.sit_rates); priced =
    those plus the listings of games not yet played (no snap counts yet), which the pieces price."""
    tw = set(zip(sn.season, sn.week, sn.team)); played = set(zip(sn.season, sn.week, sn.team, sn.key))
    q = inj[(inj.report_status == "Questionable") & (inj.game_type == "REG")].dropna(subset=["gsis_id"]).copy()
    q["season"] = q.season.astype(int); q["week"] = q.week.astype(int)
    q = q[[(s, w, t) in tw or (s, w, t) in unplayed for s, w, t in zip(q.season, q.week, q.team)]]
    q = q[[g not in out_by.get((s, w, t), set()) for s, w, t, g in zip(q.season, q.week, q.team, q.gsis_id)]]
    q["group"] = q.position.map(GROUP).fillna("other"); q["prac"] = q.practice_status.map(practice)
    q["graded"] = [(s, w, t) in tw for s, w, t in zip(q.season, q.week, q.team)]
    q["sat"] = [float((s, w, t, g) not in played) for s, w, t, g in zip(q.season, q.week, q.team, q.gsis_id)]
    q = q.drop_duplicates(["season", "week", "team", "gsis_id"])
    return q[q.graded], q


def sit_rates(q: pd.DataFrame, seasons) -> dict:
    """{season: {(group, practice): chance he sits}} from the graded listings of earlier seasons only."""
    rates = {}
    for s in seasons:
        h = q[q.season < s]
        if not len(h):
            continue
        pr = h.groupby("prac").sat.agg(["sum", "count"]); base = (pr["sum"] / pr["count"]).to_dict(); allr = float(h.sat.mean())
        c = h.groupby(["group", "prac"]).sat.agg(["sum", "count"])
        rates[s] = {k: float((r["sum"] + SHRINK * base.get(k[1], allr)) / (r["count"] + SHRINK)) for k, r in c.iterrows()}
        rates[s]["_prac"] = base; rates[s]["_all"] = allr
    return rates


def chance(rates: dict, season: int, group: str, prac: str) -> float:
    r = rates[season]
    return r.get((group, prac), r["_prac"].get(prac, r["_all"]))


def inputs_key(last_season: int, inj: pd.DataFrame, sn: pd.DataFrame, out_by: dict, pg: pd.DataFrame, reg: pd.DataFrame) -> str:
    """Everything the seasons before last_season's pieces are built from, as loaded: the code (this file, players.py,
    ids.py), the injury listings, the snap counts after the id mapping, the players ruled out, player_games and the
    schedule of those seasons. Any change rebuilds every season (cached_pieces)."""
    from pathlib import Path
    from . import players as PL
    h = hashlib.sha1()
    for f in (Path(__file__), Path(__file__).with_name("players.py"), Path(__file__).with_name("ids.py")):
        h.update(f.read_bytes())
    h.update(json.dumps(PL.DEFAULT, sort_keys=True, default=str).encode())
    past = lambda d, cols: d.loc[d.season < last_season, cols].sort_values(cols, kind="stable").astype(str)
    for d, cols in ((inj, ["season", "week", "team", "gsis_id", "report_status", "position", "practice_status"]),
                    (sn, ["season", "week", "team", "key", "position", "offense_pct", "defense_pct"]),
                    (pg, list(pg.columns)), (reg, ["game_id", "season", "week", "home_team", "away_team", "home_score"])):
        h.update(pd.util.hash_pandas_object(past(d, cols), index=False).values.tobytes())
    h.update(json.dumps(sorted((list(map(str, k)), sorted(map(str, v))) for k, v in out_by.items() if k[0] < last_season)).encode())
    return h.hexdigest()[:16]


def pieces(last_season: int | None = None, games: pd.DataFrame | None = None, cached: tuple | None = None) -> tuple[pd.DataFrame, str]:
    """One row per regular-season team-game, FIRST_SEASON to last_season: q1_skill (Questionable RB / WR / TE skill value
    out times the chance he sits), q2_off / q2_def (every Questionable player's last-game offensive / defensive snap share
    times the chance), q2_qb (the chance when last game's starting QB is Questionable), n_q (listings counted). Returns
    (pieces, inputs_key). cached = (earlier pieces, their key): when the key still matches, the seasons before
    last_season are taken from it and only last_season is rebuilt (the rates always learn from every earlier season)."""
    from . import players as PL
    games = pd.read_parquet(OUT / "games.parquet") if games is None else games
    last_season = int(games.season.max()) if last_season is None else int(last_season)
    seasons = range(FIRST_SEASON, last_season + 1)
    reg = games[games.season.isin(seasons) & games.game_type.eq("REG")]
    started = bool(reg[reg.season == last_season].home_score.notna().any())   # the current season's files must exist once a game is played
    need = [(d, n, s_) for s_ in seasons for d, n in (("injuries", "injuries"), ("snap_counts", "snap_counts"), ("rosters", "roster_weekly")) if s_ < last_season or started]
    gone = [f"{d}/{n}_{s_}.parquet" for d, n, s_ in need if not (RAW / d / f"{n}_{s_}.parquet").exists()]
    if gone:   # a missing season would price the shadow on fewer rates and listings with no sign: fail the step instead
        raise FileNotFoundError(f"raw files missing for the Questionable pieces: {', '.join(gone[:6])}" + (f" and {len(gone) - 6} more" if len(gone) > 6 else ""))
    inj = PL.load_injuries(seasons); inj = inj[inj.game_type == "REG"].copy()
    inj["season"] = inj.season.astype(int); inj["week"] = inj.week.astype(int)
    od = inj[inj.report_status.isin(["Out", "Doubtful"])]
    out_by = {k: set(g.gsis_id.dropna()) for k, g in od.groupby(["season", "week", "team"])}
    for k, ids in PL.unavailable_by_week(seasons).items():
        out_by[k] = out_by.get(k, set()) | ids
    sn = _snaps(seasons)
    up = reg[reg.home_score.isna()]
    unplayed = {(int(s), int(w), t) for s, w, h, a in zip(up.season, up.week, up.home_team, up.away_team) for t in (h, a)}
    graded, priced = listings(inj, sn, out_by, unplayed)
    rates = sit_rates(graded, range(FIRST_SEASON + 1, last_season + 1))
    q_by = {k: g for k, g in priced.groupby(["season", "week", "team"])}
    pg = pd.read_parquet(OUT / "player_games.parquet"); p = PL.DEFAULT
    key = inputs_key(last_season, inj, sn, out_by, pg, reg)
    reuse = cached is not None and cached[1] == key
    pv = PL.PlayerValues(pg, p["decay"], p["k"], p.get("pct", 25)); _, by_player, by_team = PL._usage_frames(pg)
    prev = {k: g.sort_values("week") for k, g in sn.groupby(["season", "team"])}
    long = pd.concat([reg[["game_id", "season", "week", "home_team"]].rename(columns={"home_team": "team"}),
                      reg[["game_id", "season", "week", "away_team"]].rename(columns={"away_team": "team"})]).sort_values(["season", "week"])
    if reuse:
        long = long[long.season == last_season]
    rows = []
    for r in long.itertuples():
        s, w, t = int(r.season), int(r.week), r.team
        row = {"game_id": r.game_id, "team": t, "season": s, "week": w, "q1_skill": 0.0, "q2_off": 0.0, "q2_def": 0.0, "q2_qb": 0.0, "n_q": 0}
        if (s, w, t) in q_by and s in rates:
            g = prev.get((s, t)); before = sn.iloc[:0]   # last game's snaps (trends.injury_table's rule): this season's last week before, else last season's last
            if g is not None:
                b = g[g.week < w]
                if len(b):
                    before = b[b.week == b.week.max()]
                else:
                    g2 = prev.get((s - 1, t)); before = g2[g2.week == g2.week.max()] if g2 is not None else before
            elif (s - 1, t) in prev:
                g2 = prev[(s - 1, t)]; before = g2[g2.week == g2.week.max()]
            bo = dict(zip(before.key, before.offense_pct.clip(0, 1))); bd = dict(zip(before.key, before.defense_pct.clip(0, 1)))
            qb_start = set(before[(before.position == "QB") & (before.offense_pct >= 0.5)].key)
            for x in q_by[(s, w, t)].itertuples():
                c = chance(rates, s, x.group, x.prac); row["n_q"] += 1
                if x.group in SKILL_G and x.gsis_id in by_player:
                    row["q1_skill"] += c * PL.player_value_out(pv, by_player, x.gsis_id, s, w, p["usage_games"], t, by_team)["value"]
                row["q2_off"] += c * bo.get(x.gsis_id, 0.0); row["q2_def"] += c * bd.get(x.gsis_id, 0.0)
                if x.gsis_id in qb_start:
                    row["q2_qb"] = max(row["q2_qb"], c)
        rows.append(row)
    X = pd.DataFrame(rows, columns=["game_id", "team", "season", "week", "q1_skill", "q2_off", "q2_def", "q2_qb", "n_q"])
    if reuse:
        X = pd.concat([cached[0][cached[0].season < last_season], X], ignore_index=True)
    return X, key


# ---- the shadow total (model.walk_forward's totals path, with the T2 input) ----

def attach(f0: pd.DataFrame, X: pd.DataFrame) -> pd.DataFrame:
    """Each team-game's own Questionable pieces (zero where it has none: postseason, 2013, no report), and qb_out_t."""
    f = f0.copy(); x = X.set_index(["game_id", "team"]); own = pd.MultiIndex.from_arrays([f.game_id, f.team])
    for c, src in PIECES.items():
        f[c] = x[src].reindex(own).fillna(0.0).values
    f["qb_out_t"] = np.maximum(f.qb_out.values, f.q_qb.values)
    return f


def frame(f: pd.DataFrame) -> pd.DataFrame:
    """model._game_frame (read, never replaced) plus the Questionable sums over both teams, in the same game order."""
    from . import model as M
    g = M._game_frame(f)
    h, a = f[f.home == 1].set_index("game_id"), f[f.home == 0].set_index("game_id"); ids = h.index.intersection(a.index)
    for c in ("q_skill", "q_off", "q_def", "qb_out_t"):
        g[c + "_sum"] = (h.loc[ids, c] + a.loc[ids, c]).values
    return g


def p_over_emp(model_total: float, total_line, tres) -> float:
    """model.price_at's p_over_emp: the over read off the training games' own total misses shifted to this total, pushes out."""
    if total_line is None or pd.isna(total_line):
        return np.nan
    tres = np.asarray(tres, dtype=float); tl = float(total_line)
    return float(np.mean(model_total + tres > tl) / max(1e-9, np.mean(model_total + tres != tl)))


def fit_week(train: pd.DataFrame, test: pd.DataFrame, cols: list[str] | None = None) -> tuple[np.ndarray, np.ndarray]:
    """One week's shadow fit (model.total_model's form: scaled ridge on the game frame, alpha 10): (the raw total for each of
    test's games, in its home rows' game_id order, as total_model returns it; the training games' own total misses)."""
    cols = feats() if cols is None else cols
    trf, tef = frame(train), frame(test)
    m = make_pipeline(StandardScaler(), Ridge(alpha=ALPHA)).fit(trf[cols].values, trf.total.values)
    h, a = test[test.home == 1].set_index("game_id"), test[test.home == 0].set_index("game_id")
    raw = pd.Series(m.predict(tef[cols].values), index=tef.index).reindex(h.index.intersection(a.index)).values
    return raw, trf.total.values - m.predict(trf[cols].values)


def walk(f: pd.DataFrame, test_seasons, min_train_season: int | None = None) -> tuple[pd.DataFrame, dict]:
    """The shadow total for every game of test_seasons, priced with only earlier games: model.walk_forward's weekly refit,
    training and pricing rows (prep, priced_weather), wind points (from the shadow's own totals) and over chance. f is
    model.with_trends' table with attach()'s columns. Returns (rows, {(season, week): training total misses})."""
    from . import model as M
    min_train_season = M.TRAIN_FROM if min_train_season is None else min_train_season
    cols = feats()
    f = M.prep(f)
    played = f[f.pf.notna()]
    fpr = M.priced_weather(f)
    wind = M._wind_readings(); wpool, dist, out = {}, {}, []
    _h, _a = played[played.home == 1].set_index("game_id"), played[played.home == 0].set_index("game_id")
    actual_total = (_h.pf + _a.pf.reindex(_h.index)).dropna().to_dict()
    for s in test_seasons:
        test_all = fpr[fpr.season == s]
        for wk in sorted(test_all.week.unique()):
            train = played[(played.season >= min_train_season) & ((played.season < s) | ((played.season == s) & (played.week < wk)))]
            test = test_all[test_all.week == wk]
            h, a = test[test.home == 1].set_index("game_id"), test[test.home == 0].set_index("game_id")
            ids = h.index.intersection(a.index)
            if len(ids) == 0:
                continue
            raw, tres = fit_week(train, test, cols)
            pool_ = [x for s_, v in wpool.items() if s_ < s for x in v]
            wfc = pd.Series(ids).map(wind).astype(float).values
            wpts = np.array([M.wind_points(pool_, fw) for fw in wfc])
            g = pd.DataFrame({"game_id": ids, "season": int(s), "week": int(wk), "game_type": h.loc[ids, "game_type"].values,
                              "total_line": h.loc[ids, "total_line"].values, "qt_model_total_raw": raw, "qt_wind_pts": wpts, "qt_model_total": raw + wpts})
            g["qt_p_over_emp"] = [p_over_emp(mt, tl, tres) for mt, tl in zip(g.qt_model_total, g.total_line)]
            dist[(int(s), int(wk))] = tres
            out.append(g)
            for gid, fw, rw, gt in zip(g.game_id, wfc, raw, g.game_type):
                if pd.notna(fw) and gt == "REG" and gid in actual_total:
                    wpool.setdefault(s, []).append((float(fw), float(actual_total[gid]) - float(rw)))
    return pd.concat(out, ignore_index=True), dist


def _sha(p) -> str:
    return hashlib.sha1(p.read_bytes()).hexdigest()[:16] if p.exists() else "missing"


def cached_pieces(season: int, games: pd.DataFrame) -> pd.DataFrame:
    """The pieces, the seasons before `season` read from INPUTS when the inputs they were built from are unchanged (they
    cannot change once played; about two minutes to rebuild), the current season rebuilt every run. Writes INPUTS and its key."""
    kf = INPUTS.with_suffix(".key")
    cached = (pd.read_parquet(INPUTS), kf.read_text().strip()) if INPUTS.exists() and kf.exists() else None
    X, key = pieces(season, games, cached)
    SHADOW_DIR.mkdir(parents=True, exist_ok=True); X.to_parquet(INPUTS, index=False); kf.write_text(key + "\n")
    return X


def run(first: int = 2015) -> pd.DataFrame:
    """The weekly step: the pieces, the shadow walk-forward first..current season, qt_pred.parquet and the current season's
    fits (qt_dist.json, with pred_v3's hash before and after: the shadow never writes the live table)."""
    from . import model as M
    t0 = time.time(); before = _sha(OUT / "pred_v3.parquet")
    games = pd.read_parquet(OUT / "games.parquet"); season = int(games.season.max())
    X = cached_pieces(season, games)
    f = attach(M.with_trends(pd.read_parquet(OUT / "features_asof.parquet")), X)
    pred, dist = walk(f, range(first, season + 1))
    after = _sha(OUT / "pred_v3.parquet")
    if before != after:
        raise RuntimeError("pred_v3.parquet changed while the shadow ran: the shadow must never write the live table")
    SHADOW_DIR.mkdir(parents=True, exist_ok=True); pred.to_parquet(PRED, index=False)
    n_q = X[X.season == season].groupby("week").n_q.sum()
    DIST.write_text(json.dumps({"season": season, "weeks": {str(w): [float(v) for v in d] for (s, w), d in dist.items() if s == season},
                                "feats": feats(), "pred_v3_sha_before": before, "pred_v3_sha_after": after, "listings_by_week": {str(int(k)): int(v) for k, v in n_q.items()},
                                "built": pd.Timestamp.now("UTC").strftime("%Y-%m-%d %H:%M UTC"), "seconds": round(time.time() - t0, 1)}, separators=(",", ":")))
    print(f"qt shadow: {len(pred)} games, {int(X.n_q.sum())} Questionable listings priced, {time.time() - t0:.0f}s", flush=True)
    return pred


def stored() -> pd.DataFrame:
    """qt_pred.parquet, or an empty frame (the shadow rule then bets nothing)."""
    if not PRED.exists():
        return pd.DataFrame(columns=["game_id", "season", "week", "total_line", "qt_model_total", "qt_p_over_emp"])
    return pd.read_parquet(PRED)


def live(p: pd.DataFrame, season: int, week: int) -> pd.DataFrame:
    """The shadow's total and over chance for the picks table's games (p: game_id, total_line = the live line): the chance
    re-priced at the live line with the shadow's own fit for the week (qt_dist.json); without that fit, the stored chance
    where the line is the one it was priced at, blank where it moved (the live table's stale-chance rule)."""
    from .warnlog import warn
    q = stored().set_index("game_id")
    meta = json.loads(DIST.read_text()) if DIST.exists() else {}
    if len(q) and meta.get("pred_v3_sha_after") != _sha(OUT / "pred_v3.parquet"):   # the model re-ran without the shadow (its step failed): never price on the old totals
        warn("qt shadow", f"shadow total stale (priced beside pred_v3 {meta.get('pred_v3_sha_after')}, pred_v3 now {_sha(OUT / 'pred_v3.parquet')}): shadowqtotals bets nothing")
        q = q.iloc[:0]
    if not p.game_id.isin(q.index).any():
        warn("qt shadow", f"no shadow total for {season} week {week} ({PRED.name} {'has none' if PRED.exists() else 'missing'}): shadowqtotals bets nothing")
    tot = p.game_id.map(q.qt_model_total).astype(float) if len(q) else pd.Series(np.nan, index=p.index)
    tres = meta.get("weeks", {}).get(str(int(week))) if int(meta.get("season", -1)) == int(season) else None
    if tres is not None:
        ch = [p_over_emp(t, tl, tres) if pd.notna(t) else np.nan for t, tl in zip(tot, p.total_line)]
    else:
        at = p.game_id.map(q.total_line).astype(float) if len(q) else pd.Series(np.nan, index=p.index)
        ch = np.where(at.values == p.total_line.astype(float).values, p.game_id.map(q.qt_p_over_emp).astype(float).values if len(q) else np.nan, np.nan)
    return pd.DataFrame({"qt_model_total": tot.values, "qt_p_over_emp": np.asarray(ch, dtype=float)}, index=p.index)


def records(pred: pd.DataFrame | None = None, games: pd.DataFrame | None = None) -> dict:
    """The shadow rule's backtest record per window (picks.rule_mask / record, regular season, weeks 1-17)."""
    from . import backtest as B, picks as P
    games = pd.read_parquet(OUT / "games.parquet") if games is None else games
    q = stored() if pred is None else pred
    d = B.join(pd.read_parquet(OUT / "pred_v3.parquet"), games)
    d = d[(d.game_type == "REG") & d.spread_line.notna()].copy()
    d["qt_p_over_emp"] = d.game_id.map(q.set_index("game_id").qt_p_over_emp).astype(float)
    edge, sr, _ = P.SHADOWS["shadowqtotals"]
    return {w: "%d-%d" % P.record(x, P.rule_mask(x, edge, sr), sr) for w, (lo, hi) in P.WINDOWS.items() for x in [d[d.season.between(lo, hi)]]}


if __name__ == "__main__":
    if "--records" in sys.argv:
        print(records())
    else:
        run()
