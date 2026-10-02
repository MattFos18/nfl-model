"""Opponent-adjusted, time-decayed team ratings, and the as-of feature table for the points model.

For a stat y (EPA per play, pass EPA, rush EPA, success rate, points, plays) observed for team i's
offense against team j's defense in game g, the rating solve is a weighted ridge regression

    y_g = mu + O_i - D_j + h * home_g + e_g,   weight w_g,   penalty alpha * (sum O^2 + sum D^2)

so O_i is how much better than average team i's offense is after accounting for who it played, and
D_j is how much a defense takes away. Weights decay with age (decay ** weeks_ago); last season's games
carry an extra multiplier `prior` (the offseason reset) and are aged from the end of that season. The
ridge penalty pulls thin samples toward the league average, which is what makes Week 1 ratings mostly
last year's rating shrunk toward zero.

The QB rating is a decayed, shrunk average of the starting quarterback's own EPA per dropback over every
game he has played (any team), so a QB change moves the team the moment the schedule names the starter.

`build_features(params)` walks every (season, week) from 2013 on and returns one row per team-game with the
ratings each team carried into that game plus the situational fields. Nothing in a row uses that game or
any later game.
"""
from __future__ import annotations
import numpy as np, pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "processed"

STATS = ["epa_play", "pass_epa", "rush_epa", "success", "pf", "plays"]
DEFAULT = {"decay": 0.94, "prior": 0.8, "alpha": 16.0, "qb_k": 150.0, "qb_decay": 0.985, "qb_prior": -0.12, "qb_season_fade": 0.8}  # qb_season_fade 0.8 (24 Sep 2026, experiments/qb_fix.py): each season back weighs 0.8 on top of the per-game decay, so a backup's prime years fade; team points better on all three windows, spread miss better held out and on 2015-18  # qb_prior -0.12 (was -0.05) swept 23 Sep 2026 on both windows (reports/qb_replacement.csv); 0.90 / 0.5 tuned on 2019-2022 (reports/tuning_ratings.csv); 0.94 / 0.8 re-checked 22 Sep 2026 under the weekly refit on both windows (reports/retune.csv, retune2.csv)


def solve(rows: pd.DataFrame, y: np.ndarray, w: np.ndarray, teams: list, alpha: float):
    """Weighted ridge for mu, h, O_i, D_j. rows has columns team, opp, home. Returns (O, D, mu, h) as Series/floats."""
    n, T = len(rows), len(teams)
    idx = {t: k for k, t in enumerate(teams)}
    X = np.zeros((n, 2 + 2 * T))
    X[:, 0] = 1.0
    X[:, 1] = rows.home.values.astype(float)
    ti = rows.team.map(idx).values
    oi = rows.opp.map(idx).values
    X[np.arange(n), 2 + ti] = 1.0
    X[np.arange(n), 2 + T + oi] = -1.0
    ok = ~np.isnan(y)
    X, yv, wv = X[ok], y[ok], w[ok]
    P = np.zeros(2 + 2 * T)
    P[2:] = alpha
    A = X.T @ (X * wv[:, None]) + np.diag(P)
    b = X.T @ (yv * wv)
    beta = np.linalg.solve(A, b)
    O = pd.Series(beta[2:2 + T], index=teams)
    D = pd.Series(beta[2 + T:], index=teams)
    return O, D, beta[0], beta[1]


def window(tg: pd.DataFrame, season: int, week: int, decay: float, prior: float):
    """Games visible before (season, week) with their weights."""
    cur = tg[(tg.season == season) & (tg.week < week)]
    last = tg[tg.season == season - 1]
    age_cur = (week - cur.week).values.astype(float)
    last_end = last.week.max() if len(last) else 18
    age_last = (week + (last_end + 1 - last.week)).values.astype(float)
    w = np.concatenate([decay ** age_cur, prior * decay ** age_last])
    return pd.concat([cur, last]), w


def window_variant(tg: pd.DataFrame, season: int, week: int, p: dict, kind: str):
    """Alternative windows for the Rankings tab. "model" is the real one (decay, last season at half weight). The others
    answer "who is playing well lately" without decay or last season: "season" = this season's games, equal weight;
    "last3" = the last three weeks; "last1" = last week only; "lastseason" = all of last season, equal weight."""
    if kind == "model":
        return window(tg, season, week, p["decay"], p["prior"])
    if kind == "lastseason":
        last = tg[tg.season == season - 1]
        return last, np.ones(len(last))
    cur = tg[(tg.season == season) & (tg.week < week)]
    if kind == "season":
        return cur, np.ones(len(cur))
    if kind == "last3":
        cur = cur[cur.week >= week - 3]
        return cur, np.ones(len(cur))
    if kind == "last1":
        cur = cur[cur.week == week - 1]
        return cur, np.ones(len(cur))
    raise ValueError(kind)


def team_ratings(tg: pd.DataFrame, season: int, week: int, p: dict, kind: str = "model") -> pd.DataFrame:
    rows, w = window_variant(tg, season, week, p, kind)
    teams = sorted(set(tg[tg.season == season].team) | set(rows.team))
    out = pd.DataFrame(index=teams)
    for s in STATS:
        O, D, mu, h = solve(rows, rows[s].values.astype(float), w, teams, p["alpha"])
        out[f"off_{s}"] = O
        out[f"def_{s}"] = D
        out.attrs[f"mu_{s}"] = mu
        out.attrs[f"hfa_{s}"] = h
    out["n_games"] = tg[(tg.season == season) & (tg.week < week)].groupby("team").size().reindex(teams).fillna(0)
    return out


class QBRatings:
    """Starting QB EPA per dropback, decayed by games and shrunk to a replacement-level prior."""

    def __init__(self, qb: pd.DataFrame, k: float, decay: float, prior_epa: float = -0.12, season_fade: float = 1.0):
        self.qb = qb.sort_values(["season", "week"])
        self.k, self.decay, self.prior, self.season_fade = k, decay, prior_epa, season_fade
        self._cache = {}

    def rating(self, qb_id: str, season: int, week: int) -> float:
        key = (qb_id, season, week)
        if key in self._cache:
            return self._cache[key]
        h = self.qb[(self.qb.qb_id == qb_id) & ((self.qb.season < season) | ((self.qb.season == season) & (self.qb.week < week)))]
        if len(h) == 0:
            r = self.prior
        else:
            age = np.arange(len(h))[::-1]
            w = self.decay ** age * self.season_fade ** (season - h.season.values)   # per game played, and per season back
            db = (h.dropbacks.values * w).sum()
            ep = (h.qb_epa.values * w).sum()
            r = (ep + self.k * self.prior) / (db + self.k)
        self._cache[key] = r
        return r


SITUATION = ["home", "rest", "dome", "temp", "wind", "div_game", "primetime"]


SWAPS = ROOT / "data" / "runs" / "qb_swaps.json"   # the week's QB-out check: status, and every swap with the source that chose the QB (health, tie check)


def qbs_out_now(games: pd.DataFrame, status: dict | None = None) -> tuple[tuple, dict]:
    """(season, week), {team: set of QB ids who cannot play} for the week being priced: Out or Doubtful on the league's
    report or ESPN's same-day page (players.load_injuries), or off the active roster. 2 Oct 2026 (Matt: the WAS card
    priced Jayden Daniels after ESPN ruled him Out): the schedule names the coming week's starter before the injury news,
    and the backtest priced every game at the QB who actually started, so an upcoming game must swap in the replacement.

    `status` (a dict, filled in): "ok"; "no injury file" (the season's league report is not on this machine, the one
    expected gap: only the roster lists count); or "error" with the reason. 2 Oct 2026 (code review): every exception
    used to return "nobody out" silently, so a broken injury load priced ruled-out starters with no sign; an error now
    prints a warning, and ratings' main writes it to SWAPS and fails its weekly step (run log, health, tie check)."""
    import sys
    from .lines import current_week
    from .features import RAW
    from . import players as PL
    st = {} if status is None else status
    st.update(status="ok", detail="", season=None, week=None, espn_unmatched=[])
    def fail(what, e):
        st.update(status="error", detail=(st["detail"] + "; " if st["detail"] else "") + f"{what}: {type(e).__name__}: {str(e)[:200]}")
    try:
        season, week = current_week(games)
        st.update(season=int(season), week=int(week))
    except Exception as e:  # noqa  (no week to price: nothing to swap, and say so loudly)
        fail("current week", e)
        print(f"WARNING qbs_out_now: the QB-out check failed, named starters priced as listed: {st['detail']}", file=sys.stderr, flush=True)
        return (None, None), {}
    out = {}
    try:
        if (RAW / "injuries" / f"injuries_{season}.parquet").exists():
            inj = PL.load_injuries([season])
            if PL.ESPN_MERGE["error"]:   # the league's report loaded, ESPN's same-day page did not: price what loaded, flag it
                st.update(status="error", detail=f"ESPN injury page not merged: {PL.ESPN_MERGE['error']}")
            st["espn_unmatched"] = list(PL.ESPN_MERGE.get("unmatched") or [])
            inj = inj[(inj.season == season) & (inj.week == week) & inj.report_status.isin(["Out", "Doubtful"])]
            out = {t: set(g.gsis_id.dropna()) for t, g in inj.groupby("team")}
        else:
            st.update(status="no injury file", detail=f"injuries_{season}.parquet not on this machine: only the roster lists (IR and the like) count")
    except Exception as e:  # noqa  (anything else: the injury report is not counted, and say so loudly)
        fail("injury report", e)
    try:   # the roster lists (IR, PUP, suspended) count even when the injury report failed
        for (s_, w_, t), ids in PL.unavailable_by_week([season]).items():
            if s_ == season and w_ == week:
                out.setdefault(t, set()).update(ids)
    except Exception as e:  # noqa
        fail("roster lists", e)
    if st["status"] == "error":
        print(f"WARNING qbs_out_now: the QB-out check failed, starters it could not see are priced as listed: {st['detail']}", file=sys.stderr, flush=True)
    return (season, week), out


def active_qbs(team: str, season: int, week: int | None = None) -> set | None:
    """Player ids with status ACT on the team's weekly roster (nflverse) for the priced week, or its latest week before
    it; None when there is no weekly roster for the season (nothing to check against)."""
    from .features import RAW
    f = RAW / "rosters" / f"roster_weekly_{season}.parquet"
    if not f.exists():
        return None
    r = pd.read_parquet(f, columns=["team", "gsis_id", "status", "week"])
    r = r[r.gsis_id.notna()]
    wks = r.week[r.week <= week] if week is not None else r.week
    if not len(wks):
        return None
    r = r[(r.week == wks.max()) & (r.team == team)]
    return set(r[r.status == "ACT"].gsis_id)


def replacement_qb(team: str, out: set, season: int, qb: pd.DataFrame, week: int | None = None) -> tuple[str | None, str]:
    """(QB id, the source that chose him) for a starter who cannot play: the next QB on the depth chart (roster_now) not
    out, else the team's QB with the most dropbacks this season not out, else None (the rating's prior). Either way he
    must be ACT on the team's current weekly roster (2 Oct 2026, code review: roster_now is the previous run's, since
    ratings runs before positions, so a backup released or made inactive since would have been priced)."""
    act = active_qbs(team, season, week)
    ok = lambda pid: act is None or pid in act
    note = "" if act is not None else " (no weekly roster to check)"
    skipped = []
    f = OUT / "roster_now.parquet"
    if f.exists():
        r = pd.read_parquet(f, columns=["team", "player_id", "position", "depth"])
        r = r[(r.team == team) & (r.position == "QB") & r.depth.notna() & ~r.player_id.isin(out)].sort_values("depth")
        for pid in r.player_id:
            if ok(pid):
                return str(pid), "depth chart" + note
            skipped.append(str(pid))
    d = qb[(qb.season == season) & (qb.team == team) & ~qb.qb_id.isin(out)].groupby("qb_id").dropbacks.sum().sort_values(ascending=False)
    why = f"; depth chart's {', '.join(skipped)} not ACT on the weekly roster" if skipped else ""
    for pid in d.index:
        if ok(pid):
            return str(pid), "most dropbacks this season" + note + why
    return None, "none: the replacement-level prior" + why


def qb_names(season: int | None = None) -> dict:
    """QB id -> name: the schedule's starters, the season's weekly roster, then the current depth chart."""
    from .features import RAW
    names = {}
    f = OUT / "roster_now.parquet"
    if f.exists():
        r = pd.read_parquet(f, columns=["player_id", "name"]); names.update(zip(r.player_id, r.name))
    rf = RAW / "rosters" / f"roster_weekly_{season}.parquet"
    if season is not None and rf.exists():
        r = pd.read_parquet(rf, columns=["gsis_id", "full_name"]).dropna(); names.update(zip(r.gsis_id, r.full_name))
    gf = OUT / "games.parquet"
    if gf.exists():
        g = pd.read_parquet(gf, columns=["home_qb_id", "home_qb_name", "away_qb_id", "away_qb_name"])
        for s in ("home", "away"):
            names.update(zip(g[f"{s}_qb_id"], g[f"{s}_qb_name"]))
    return {k: v for k, v in names.items() if isinstance(k, str) and isinstance(v, str)}


def write_swaps(f: pd.DataFrame) -> dict:
    """data/runs/qb_swaps.json: the QB-out check's status and the week's swaps (the starter ruled out, the QB priced and
    the source that chose him), for health.py and the tie check."""
    import json
    st = dict(f.attrs.get("qb_out_status", {})); s, w = st.get("season"), st.get("week")
    nm = qb_names(s)
    sw = f[f.qb_swap_from.notna()] if "qb_swap_from" in f.columns else f.iloc[0:0]
    src = f.attrs.get("qb_swap_source", {})
    st["swaps"] = [{"game_id": r.game_id, "team": r.team, "from": r.qb_swap_from, "from_name": nm.get(r.qb_swap_from), "to": r.qb_id if isinstance(r.qb_id, str) else None,
                    "to_name": nm.get(r.qb_id) if isinstance(r.qb_id, str) else None, "source": src.get(r.team, "")} for r in sw.itertuples()]
    SWAPS.parent.mkdir(parents=True, exist_ok=True); SWAPS.write_text(json.dumps(st, indent=1))
    return st


def build_features(p: dict = DEFAULT, seasons=range(2013, 2027), tg=None, games=None, qb=None, verbose=False) -> pd.DataFrame:
    tg = pd.read_parquet(OUT / "team_games.parquet") if tg is None else tg
    games = pd.read_parquet(OUT / "games.parquet") if games is None else games
    qb = pd.read_parquet(OUT / "qb_games.parquet") if qb is None else qb
    played = tg[tg.pf.notna()].copy()
    played["plays"] = played.plays.fillna(played.plays.mean())
    qbr = QBRatings(qb, p["qb_k"], p["qb_decay"], p.get("qb_prior", -0.12), p.get("qb_season_fade", 1.0))
    # each team's most recent named starter, in schedule order (played games and the coming week carry ids)
    named = games[games.home_qb_id.notna() | games.away_qb_id.notna()].sort_values(["season", "week"])
    qstat = {}
    (cs, cw), qout = qbs_out_now(games, status=qstat)   # the week being priced: QBs ruled out, swapped for their replacement below
    chosen = {}   # team -> (QB priced, source that chose him), once per team
    def swap(team, qid_):
        """(QB to price, the ruled-out starter's id or None)."""
        if not (isinstance(qid_, str) and qid_ in qout.get(team, set())):
            return qid_, None
        if team not in chosen:
            chosen[team] = replacement_qb(team, qout[team], cs, qb, week=cw)
            print(f"qb swap {cs} week {cw} {team}: {qid_} ruled out, priced {chosen[team][0]} ({chosen[team][1]})", flush=True)
        return chosen[team][0], qid_
    last_qb = {}
    feats = []
    for s in seasons:
        weeks = sorted(games[games.season == s].week.unique())
        for wk in weeks:
            gw = games[(games.season == s) & (games.week == wk)]
            if len(gw) == 0:
                continue
            for g in named[(named.season == s) & (named.week == wk)].itertuples():
                if isinstance(g.home_qb_id, str):
                    last_qb[g.home_team] = g.home_qb_id
                if isinstance(g.away_qb_id, str):
                    last_qb[g.away_team] = g.away_qb_id
            R = team_ratings(played, s, wk, p)
            hfa = R.attrs.get("hfa_pf", 0.0)
            for g in gw.itertuples():
                for side, opp in [("home", "away"), ("away", "home")]:
                    t, o = getattr(g, f"{side}_team"), getattr(g, f"{opp}_team")
                    if t not in R.index or o not in R.index:
                        continue
                    row = {"game_id": g.game_id, "season": s, "week": wk, "game_type": g.game_type, "team": t, "opp": o,
                           "home": float(side == "home"), "pf": getattr(g, f"{side}_score"), "pa": getattr(g, f"{opp}_score"),
                           "rest": getattr(g, f"{side}_rest"), "opp_rest": getattr(g, f"{opp}_rest"),
                           "dome": float(bool(g.dome)), "temp": g.temp, "wind": g.wind, "div_game": float(g.div_game),
                           "primetime": float(bool(g.primetime)), "neutral": float(bool(g.neutral)),
                           "spread_line": g.spread_line, "total_line": g.total_line, "implied": getattr(g, f"{side}_implied"),
                           "n_games": R.n_games[t], "hfa_fit": hfa}
                    for st in STATS:
                        row[f"off_{st}"] = R.loc[t, f"off_{st}"]
                        row[f"def_{st}"] = R.loc[o, f"def_{st}"]          # the defense this offense faces
                        row[f"own_def_{st}"] = R.loc[t, f"def_{st}"]
                        row[f"opp_off_{st}"] = R.loc[o, f"off_{st}"]
                    # nflverse names the starters only for played games and the coming week. For a later unplayed game
                    # carry each team's most recent starter forward rather than pricing a replacement-level QB.
                    qid = getattr(g, f"{side}_qb_id")
                    if not isinstance(qid, str) and pd.isna(getattr(g, f"{side}_score")):
                        qid = last_qb.get(t)
                    swapped = None
                    if pd.isna(getattr(g, f"{side}_score")) and (s, wk) == (cs, cw):
                        qid, swapped = swap(t, qid)
                    row["qb_id"] = qid
                    row["qb_swap_from"] = swapped   # the ruled-out starter's id when the QB priced is his replacement (2 Oct 2026)
                    row["qb_rating"] = qbr.rating(qid, s, wk) if isinstance(qid, str) else qbr.prior
                    oqid = getattr(g, f"{opp}_qb_id")
                    if not isinstance(oqid, str) and pd.isna(getattr(g, f"{side}_score")):
                        oqid = last_qb.get(o)
                    if pd.isna(getattr(g, f"{side}_score")) and (s, wk) == (cs, cw):
                        oqid, _ = swap(o, oqid)
                    row["opp_qb_rating"] = qbr.rating(oqid, s, wk) if isinstance(oqid, str) else qbr.prior
                    feats.append(row)
        if verbose:
            print("features", s, len(feats), flush=True)
    out = pd.DataFrame(feats)
    if "qb_swap_from" in out.columns:
        out["qb_swap_from"] = out.qb_swap_from.astype(object).where(out.qb_swap_from.notna(), None)
    out.attrs["qb_out_status"] = qstat; out.attrs["qb_swap_source"] = {t: v[1] for t, v in chosen.items()}
    return out


def main() -> int:
    """The weekly step: write features_asof and qb_swaps.json; 1 when the QB-out check failed (the features are still
    written, named starters priced, and the step fails so the run log and health show it)."""
    import sys
    f = build_features(verbose=True)
    f.to_parquet(OUT / "features_asof.parquet", index=False)
    st = write_swaps(f)
    print(f.shape, f"QB-out check: {st.get('status')}; swaps: " + ("; ".join(f"{x['team']} {x['from_name']} -> {x['to_name']} ({x['source']})" for x in st["swaps"]) or "none"))
    if st.get("status") == "error":
        print(f"QB-out check failed: {st.get('detail')}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
