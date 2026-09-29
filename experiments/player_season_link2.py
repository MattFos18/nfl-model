"""Player season totals, round 3 (29 Sep 2026): every variant of experiments/player_season_link.py rerun on top of today's
nflmodel/player_season.py (each player's own availability from the logit: AVAIL x avail_mult, BLEND), plus new as-of
ideas, under the pre-registered rule in reports/round3_rule.md (written before any result).

Rows. The harness cache reports/player_season_rows.csv (2016-25, as-of weeks 1, 5, 9, 13; 2016 week 1 absent) after a
check that one as-of point rebuilt from today's code matches it, plus an early window the harness cannot reach on its
own: 2015 as of weeks 1, 5, 9, 13, built here with the same code (player_season.project with availability 1 and blend 0)
on 2014-15 plays read through nflmodel.scheme.load_plays (the loader behind scheme_plays.parquet; 2014-15 have no
participation charting, which the season totals do not use) and the 2015 weekly roster with its team codes normalised
(ARZ, BLT, CLV, HST, SL, SD, OAK). 2015 was never used to choose anything: it is the rule's "2015-18 never used" window
for this study (2016-18 is the fit window of AVAIL, BLEND and the availability logit).

Windows: 2015 (early, out of sample), 2016-18 (fit), 2019-22, 2023-25. Rule 1: lower season-total miss on all four.

Targets. The harness's actual totals come from player_season.season_actuals (week <= 18 when this ran; regular season only from 29 Sep 2026), which for 2015-2020 also
counts the wild-card round (weeks 18 of those seasons are playoff games). The study scores both that target ("harness")
and the regular-season-only total ("reg"); a variant must pass rule 1 on both.

Configs. "fixed": today's adopted AVAIL and BLEND, the variant only (the code change is the variant alone). "refit":
AVAIL and BLEND refit on 2016-18 on the harness grids for the base and each variant (the code change then includes the
new constants). Verdicts are given per config.

Variants (all from the as-of data; no market input; each is a factor on the cached per-game yards for the games left,
which is exact because per_game is share x team volume x rate):
  from player_season_link.py, unchanged in form:
  b25/b50     the team volume V for the games left blended 0.25/0.5 toward the league mean of the 32 teams' last-17
  c25/c50     V blended toward the team's previous full regular season (2015 and 2016 now have 2014 and 2015 from pbp)
  d           props.game_script over each game left at our game model's expected margin (no total), averaged
  d_m         the margin slope only (V + GS slope x mean margin)
  e_c25_d, e_c25_d_m, e_c50_d, e_c50_d_m   c and d together
  p2          share x the (position group, age band) usage ratio over games he played, fitted on 2016-18 (K_AGE 30)
  p2_all      the same ratio over every game left
  p2+best1, p2_all+best1   on top of the best Part 1 variant for the kind (best = largest smallest-window gain among
              the Part 1 variants passing rule 1 on both targets in the fixed config; base when none)
  new ideas:
  sos/sos_h   the remaining schedule's defenses by kind: the rate x mean over the games left of 1 + W x (allowed /
              league - 1), W the props engine's own opponent weight (0.25 rec, 0.25 rush, 0.5 pass) or half of it;
              allowed = props.defenses as of the week (yards per target, per carry, passing yards per dropback)
  coach25/coach50  a new head coach (the coach of his latest game before the week, or of the week-1 game at week 1,
              differs from the team's coach in last season's final game): V blended toward the league mean by
              w x the share of the last-17 window that is last season's games
  comp25/comp50  target / carry competition from the returning teammates: S = the sum of the usage shares of the
              team's projected players of the kind (as of the week, on the roster, profile on this team); factor
              (S_bar / S)^alpha, S_bar the 2016-18 mean of S by kind and as-of week, alpha 0.25/0.5, clipped [0.75, 1.33]
              (rec and rush; one passer per team)
  recon/recon_h  the props engine's team reconciliation over the games left: the team's expected yards of the kind per
              game (props.TEAM_FIT on our game model's expected points, averaged over the games left) over what its
              projected players add up to per game, normalised by that ratio's 2016-18 median by kind and as-of week,
              clipped [0.5, 2]; factor 1 + w x (ratio - 1), w = props.RECON_W yds (0.25, 0.25, 0.5) or half
Rule 3 placebo (for every variant passing rule 1): the variant's driving input shuffled within season, 50 draws: team
inputs (the team volume the league blend shrinks, the previous season's volume, the game-script shift, the new-coach
flag, the schedule-strength ratio, the teammates' share sum, the reconciliation ratio) take another team's values under
one random permutation of the teams per season; the age takes another player's (same kind, same season). Pass: the
real gain beats the placebo gain on every window in at least 45 of 50 draws (each window separately, on both targets).
Rule 5: the passing pieces of a kind together (best per family), which must itself pass rule 1.
Worst week: the largest loss in any window x as-of week cell, and in any single season x as-of week.

  python experiments/player_season_link2.py build     rows for 2015, the cache check, the team table (scratchpad)
  python experiments/player_season_link2.py study     scoring, placebo, combination; writes reports/player_season_link2.{csv,md}
"""
from __future__ import annotations
import sys, time, os, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import numpy as np, pandas as pd
from nflmodel import player_season as PS, props as PR, season as SE, scheme as SC
from nflmodel.positions import names_by_id
from experiments import player_season_backtest as BT

SCR = Path(os.environ.get("LINK2_SCRATCH", "/tmp/claude-0/-home-user/c1e0d18e-681a-50ba-b0bb-6c809c2e3dee/scratchpad/player_season_link2"))
SCR.mkdir(parents=True, exist_ok=True)
KINDS = ("rec", "rush", "pass")
KIND_VOL = {"rec": "pass_plays_pg", "rush": "runs_pg", "pass": "dropbacks_pg"}
ALLOWED = {"rec": ("ypt_allowed", "ypt"), "rush": ("ypc_allowed", "ypc"), "pass": ("ypd_allowed", "ypd")}
TARGETABLE = 0.97
EARLY = 2015
SEASONS = [EARLY] + BT.FIT_SEASONS + BT.TEST_SEASONS
WINDOWS = ["2015", "2016-18", "2019-22", "2023-25"]
WIN = {s: ("2015" if s == 2015 else "2016-18" if s <= 2018 else "2019-22" if s <= 2022 else "2023-25") for s in SEASONS}
K_AGE = 30
AGE_BANDS = [(0, 24, "<=24"), (25, 27, "25-27"), (28, 30, "28-30"), (31, 99, "31+")]
POS_GROUP = {"rec": {"WR": "WR", "TE": "TE", "RB": "RB", "FB": "RB", "HB": "RB"}, "rush": {"RB": "RB", "FB": "RB", "HB": "RB", "QB": "QB", "WR": "WR", "TE": "WR"}, "pass": {"QB": "QB"}}
N_DRAWS, NEED = 50, 45
COMP_CLIP = (0.75, 1.33)
TARGETS = ("reg", "harness")


# ------------------------------------------------------------------------------------------------ build
def load_main():
    games = pd.read_parquet(PS.OUT / "games.parquet")
    d = PR.official(pd.read_parquet(PS.OUT / "scheme_plays.parquet"))
    return games, d


def load_early() -> pd.DataFrame:
    f = SCR / "plays_2014_15.parquet"
    if f.exists():
        return pd.read_parquet(f)
    d = PR.official(SC.load_plays([2014, 2015]))
    d.to_parquet(f, index=False)
    return d


def rows_early(games, d_early, names) -> pd.DataFrame:
    f = SCR / "rows_2015.csv"
    if f.exists():
        return pd.read_csv(f)
    out = []; t0 = time.time()
    for w in BT.WEEKS:
        ro = PS.roster_at(EARLY, w); ro["team"] = ro.team.replace(PS._TEAM_FIX)
        p = PS.project(d_early, names, games, EARLY, w, roster=ro, mode="asof", avail={"rec": 1.0, "rush": 1.0, "pass": 1.0})
        act = PS.season_actuals(d_early, EARLY).set_index(["kind", "player_id"]); key = list(zip(p.kind, p.player_id))
        p["actual_yards"] = [float(act.yards.get(k, 0.0)) if k in act.index else 0.0 for k in key]
        p["actual_td"] = [float(act.td.get(k, 0.0)) if k in act.index else 0.0 for k in key]
        p["actual_games"] = [int(act.games.get(k, 0)) if k in act.index else 0 for k in key]
        p["games_left_played"] = (p.actual_games - p.games_so_far).clip(lower=0)
        p["actual_rank"] = p.groupby("kind").actual_yards.rank(ascending=False, method="first").astype(int)
        p["actual_pg"] = p.actual_yards / p.actual_games.clip(lower=1)
        out.append(p); print(f"2015 week {w}: {len(p)} rows ({time.time() - t0:.0f}s)", flush=True)
    R = pd.concat(out, ignore_index=True).round(3); R.to_csv(f, index=False)
    return R


def check_cache(games, d, names) -> dict:
    f = SCR / "cache_check.json"
    if f.exists():
        return json.loads(f.read_text())
    t0 = time.time(); p = BT.rows_for(d, games, names, 2019, 5)
    C = pd.read_csv(BT.CACHE); c = C[(C.season == 2019) & (C.week == 5)]
    m = c.merge(p, on=["kind", "player_id"], suffixes=("_c", "_n"), how="outer", indicator=True)
    same = bool((m._merge == "both").all())
    diff = max(float((m[x + "_c"] - m[x + "_n"]).abs().max()) for x in ["volume_pg", "rate", "yards_pg", "yards_so_far", "pace_yards", "actual_yards", "team_games_left", "avail_mult"]) if same else float("inf")
    res = {"same_players": same, "n_cache": int(len(c)), "n_fresh": int(len(p)), "max_diff": diff, "ok": bool(same and diff < 0.002), "secs": round(time.time() - t0)}
    f.write_text(json.dumps(res)); print("cache check", res, flush=True)
    return res


def reg_actuals(d_main, d_early) -> pd.DataFrame:
    """Regular-season-only totals by (season, kind, player)."""
    f = SCR / "reg_actuals.csv"
    if f.exists():
        return pd.read_csv(f)
    out = []
    for s in SEASONS:
        src = d_early if s == EARLY else d_main
        a = PS.season_actuals(src[src.season_type == "REG"], s); a["season"] = s; out.append(a[["season", "kind", "player_id", "yards", "games"]])
    A = pd.concat(out, ignore_index=True); A.to_csv(f, index=False)
    return A


def coach_table(games) -> dict:
    """(season, week, team) -> 1 when the head coach as of the week differs from the coach of last season's final game."""
    g = games[games.game_type == "REG"]
    long = pd.concat([g[["season", "week", "home_team", "home_coach", "home_score"]].rename(columns={"home_team": "team", "home_coach": "coach", "home_score": "sc"}),
                      g[["season", "week", "away_team", "away_coach", "home_score"]].rename(columns={"away_team": "team", "away_coach": "coach", "home_score": "sc"})]).sort_values(["season", "week"])
    last = long.groupby(["season", "team"]).coach.last()
    out = {}
    for s in SEASONS:
        ls = long[long.season == s]
        for t, x in ls.groupby("team"):
            prev = last.get((s - 1, t))
            for w in BT.WEEKS:
                before = x[x.week < w]
                now = before.coach.iloc[-1] if len(before) else x.coach.iloc[0]
                out[(s, w, t)] = float(isinstance(now, str) and isinstance(prev, str) and now != prev)
    return out


def team_table(games, d_main, d_early) -> pd.DataFrame:
    """One row per (season, as-of week, team, kind): the last-17 volume (base), the league mean, the previous regular
    season's volume, the game-script volumes, the mean margin and expected points over the games left, the schedule's
    defensive ratio, the new-coach flag and the share of the last-17 window from last season, the team's expected yards
    per game of the kind over the games left (TEAM_FIT on expected points)."""
    f = SCR / "team_table.csv"
    if f.exists():
        return pd.read_csv(f)
    fr = SE._frame(); pred = pd.read_parquet(PS.OUT / "pred_v3.parquet"); coach = coach_table(games)
    out = []; t0 = time.time()
    for s in SEASONS:
        src = d_early if s == EARLY else d_main
        psrc = d_early if s - 1 in (2014, 2015) else d_main
        reg = games[(games.season == s) & (games.game_type == "REG")]
        dome_of = {}
        for r in reg.itertuples():
            dome_of[r.home_team] = float(r.dome) if pd.notna(r.dome) else dome_of.get(r.home_team, 0.0)
        dp = psrc[(psrc.season == s - 1) & (psrc.season_type == "REG")]
        prev = {}
        for team, g in dp.groupby("posteam"):
            n = max(g.game_id.nunique(), 1)
            prev[team] = {"pass_plays_pg": float(g.pass_play.sum()) / n, "runs_pg": float(g.play_type.eq("run").sum()) / n, "dropbacks_pg": float(g.dropback.sum()) / n}
        for w in BT.WEEKS:
            if s == 2016 and w == 1:
                continue
            a = PR._asof(src, s, w); V = PR.teams_volume(a); D = PR.defenses(a); L = PR.league_baselines(a)
            league = {vk: float(np.mean([v[vk] for v in V.values() if v.get(vk)])) for vk in KIND_VOL.values()}
            P = SE.profiles(fr, s, w); fit = SE.fit_asof(pred, s, w)
            left = reg[reg.week >= w]
            margins, xpts, opps = {}, {}, {}
            for g in left.itertuples():
                opps.setdefault(g.home_team, []).append(g.away_team); opps.setdefault(g.away_team, []).append(g.home_team)
                if g.home_team in P and g.away_team in P:
                    neu = 1.0 if (pd.notna(g.neutral) and g.neutral == 1) else 0.0; dg = 1.0 if g.div_game == 1 else 0.0; dm = 0.0 if neu else dome_of.get(g.home_team, 0.0)
                    eh = SE.expected_points(P[g.home_team], P[g.away_team], fit, 0.0 if neu else 1.0, neu, dm, dg, int(g.week))
                    ea = SE.expected_points(P[g.away_team], P[g.home_team], fit, 0.0, neu, dm, dg, int(g.week))
                    margins.setdefault(g.home_team, []).append(eh - ea); margins.setdefault(g.away_team, []).append(ea - eh)
                    xpts.setdefault(g.home_team, []).append(eh); xpts.setdefault(g.away_team, []).append(ea)
                else:
                    margins.setdefault(g.home_team, []).append(0.0); margins.setdefault(g.away_team, []).append(0.0)
            # games of this season inside the last-17 window: the rest are last season's
            this_n = a[a.season == s].groupby("posteam").game_id.nunique()
            for team, v in V.items():
                ms = margins.get(team, []); xp = xpts.get(team, []); op = opps.get(team, [])
                n_this = int(this_n.get(team, 0)); frac_prev = max(0.0, 17 - n_this) / 17.0
                for k, vk in KIND_VOL.items():
                    b = float(v.get(vk, 0.0))
                    gs = float(np.mean([PR.game_script(k, b, m, None) for m in ms])) if ms else b
                    gs_m = b + PR.GS[k][1] * float(np.mean(ms)) if ms else b
                    ac, lc = ALLOWED[k]
                    rat = [D[o][ac] / L[lc] for o in op if o in D and D[o].get(ac) is not None and not pd.isna(D[o][ac]) and L.get(lc)]
                    fy = PR.TEAM_FIT[k]["yds"]
                    out.append({"season": s, "week": w, "team": team, "kind": k, "base": b, "league": league[vk], "prev": prev.get(team, {}).get(vk, np.nan),
                                "gs": gs, "gs_m": gs_m, "n_left": len(ms), "mean_margin": float(np.mean(ms)) if ms else 0.0,
                                "xpts": float(np.mean(xp)) if xp else np.nan, "team_yds_exp": (fy[0] + fy[1] * float(np.mean(xp))) if xp else np.nan,
                                "sos_ratio": float(np.mean(rat)) if rat else 1.0, "new_coach": coach.get((s, w, team), 0.0), "frac_prev": frac_prev})
            print(f"team table {s} week {w} ({time.time() - t0:.0f}s)", flush=True)
    T = pd.DataFrame(out); T.to_csv(f, index=False)
    return T


def touches_left(R: pd.DataFrame, d: pd.DataFrame) -> pd.DataFrame:
    """For the 2016-18 rows (the age ratios are fitted there only): his touches of the kind over the regular-season games
    left on the profile's team, and the team's plays of the kind in the games left he played (any touch)."""
    f = SCR / "touches_left.csv"
    if f.exists():
        return pd.read_csv(f)
    x = d[(d.season_type == "REG") & d.season.isin(BT.FIT_SEASONS)]
    keys = ["season", "week", "game_id", "posteam"]
    mine = {"rec": x[x.pass_play & x.receiver_player_id.notna()].groupby(["receiver_player_id"] + keys).size().rename("n").reset_index().rename(columns={"receiver_player_id": "player_id"}),
            "rush": x[x.play_type.eq("run") & x.rusher_player_id.notna()].groupby(["rusher_player_id"] + keys).size().rename("n").reset_index().rename(columns={"rusher_player_id": "player_id"}),
            "pass": x[x.dropback & x.passer_player_id.notna()].groupby(["passer_player_id"] + keys).size().rename("n").reset_index().rename(columns={"passer_player_id": "player_id"})}
    team = {"rec": x[x.pass_play].groupby(keys).size().rename("t"), "rush": x[x.play_type.eq("run")].groupby(keys).size().rename("t"), "pass": x[x.dropback].groupby(keys).size().rename("t")}
    played = pd.concat([m[["player_id"] + keys] for m in mine.values()]).drop_duplicates(["player_id", "game_id"])
    out = []
    RF = R[R.season.isin(BT.FIT_SEASONS)]
    for k in KINDS:
        rk = RF[RF.kind == k][["kind", "player_id", "season", "week", "team"]].drop_duplicates()
        tk = team[k].reset_index(); mk = mine[k].rename(columns={"week": "gweek"}); pl = played.rename(columns={"week": "gweek"})
        for s, w in rk[["season", "week"]].drop_duplicates().itertuples(index=False):
            rows = rk[(rk.season == s) & (rk.week == w)]
            tg = tk[(tk.season == s) & (tk.week >= w)]; tp = tg.groupby("posteam").t.sum()
            mg = mk[(mk.season == s) & (mk.gweek >= w)]
            pg = pl[(pl.season == s) & (pl.gweek >= w)].merge(tg[["game_id", "posteam", "t"]], on=["game_id", "posteam"])
            m_all = mg.groupby(["player_id", "posteam"]).n.sum(); p_t = pg.groupby(["player_id", "posteam"]).t.sum(); p_n = pg.groupby(["player_id", "posteam"]).size()
            for r in rows.itertuples():
                key = (r.player_id, r.team)
                out.append({"kind": k, "player_id": r.player_id, "season": s, "week": w, "team": r.team, "a_all": float(m_all.get(key, 0.0)), "t_all": float(tp.get(r.team, 0.0)),
                            "a_played": float(m_all.get(key, 0.0)), "t_played": float(p_t.get(key, 0.0)), "n_played": int(p_n.get(key, 0))})
    T = pd.DataFrame(out); T.to_csv(f, index=False)
    return T


def build():
    t0 = time.time()
    games, d = load_main(); names = names_by_id(range(2013, 2027))
    print(f"loaded ({time.time() - t0:.0f}s)", flush=True)
    chk = check_cache(games, d, names)
    if not chk["ok"]:
        print("CACHE DIFFERS from today's code: rebuild reports/player_season_rows.csv with experiments/player_season_backtest.py first", flush=True)
    de = load_early(); print(f"2014-15 plays {len(de)} ({time.time() - t0:.0f}s)", flush=True)
    rows_early(games, de, names)
    reg_actuals(d, de)
    team_table(games, d, de)
    R = all_rows(); touches_left(R, d)
    print(f"build done ({time.time() - t0:.0f}s)", flush=True)


# ------------------------------------------------------------------------------------------------ rows
def all_rows() -> pd.DataFrame:
    C = pd.read_csv(BT.CACHE); E = pd.read_csv(SCR / "rows_2015.csv")
    R = pd.concat([E[C.columns.intersection(E.columns)], C], ignore_index=True)
    R = R[R.team_games_left > 0].reset_index(drop=True)
    A = reg_actuals(None, None) if (SCR / "reg_actuals.csv").exists() else None
    if A is not None:
        R = R.merge(A.rename(columns={"yards": "actual_reg", "games": "games_reg"}), on=["season", "kind", "player_id"], how="left")
        R["actual_reg"] = R.actual_reg.fillna(0.0)
    R["window"] = R.season.map(WIN)
    return R


def ages(R: pd.DataFrame) -> pd.Series:
    p = pd.read_parquet(PS.RAW / "players" / "players.parquet", columns=["gsis_id", "birth_date"]).dropna(subset=["gsis_id"]).drop_duplicates("gsis_id")
    born = dict(zip(p.gsis_id, pd.to_datetime(p.birth_date, errors="coerce")))
    sep1 = pd.to_datetime(R.season.astype(int).astype(str) + "-09-01")
    return ((sep1 - pd.to_datetime(R.player_id.map(born))).dt.days / 365.25).round(2)


def age_band(age: float) -> str:
    if pd.isna(age):
        return "unknown"
    for lo, hi, lab in AGE_BANDS:
        if lo <= age <= hi:
            return lab
    return "unknown"


def fit_age_ratios(R: pd.DataFrame, T: pd.DataFrame, mode: str) -> pd.DataFrame:
    X = R[R.season.isin(BT.FIT_SEASONS)].merge(T, on=["kind", "player_id", "season", "week", "team"], how="left")
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
        rows.append({"kind": kk, "pos_group": pg, "age_band": ab, "n": n, "ratio_raw": round(raw, 4), "ratio": round((n * raw + K_AGE) / (n + K_AGE), 4)})
    return pd.DataFrame(rows)


class Study:
    """Everything as arrays on the rows; a variant is a spec, its factor multiplies yards_pg for the games left."""

    def __init__(self):
        R = all_rows(); T = pd.read_csv(SCR / "team_table.csv")
        R = R.merge(T, on=["season", "week", "team", "kind"], how="left")
        R["age"] = ages(R)
        self.R = R; n = len(R)
        self.kind = R.kind.values; self.season = R.season.values; self.week = R.week.values; self.win = R.window.values
        self.so = R.yards_so_far.values.astype(float); self.ypg = R.yards_pg.values.astype(float); self.left = R.team_games_left.values.astype(float)
        self.mult = R.avail_mult.values.astype(float); self.pace = R.pace_yards.values.astype(float)
        self.actual = {"harness": R.actual_yards.values.astype(float), "reg": R.actual_reg.values.astype(float)}
        # team inputs as arrays indexed [season, week, team, kind] for the within-season permutation
        self.S_IDX = {s: i for i, s in enumerate(SEASONS)}; self.W_IDX = {w: i for i, w in enumerate(BT.WEEKS)}; self.K_IDX = {k: i for i, k in enumerate(KINDS)}
        teams = sorted(T.team.unique()); self.teams = teams; self.T_IDX = {t: i for i, t in enumerate(teams)}
        self.si = R.season.map(self.S_IDX).values; self.wi = R.week.map(self.W_IDX).values; self.ki = R.kind.map(self.K_IDX).values
        self.ti = R.team.map(self.T_IDX).fillna(-1).astype(int).values
        # the team's shares sum (comp) and its players' yards per game (recon), from the rows as projected
        base = R.base.replace(0, np.nan)
        share = np.where(R.kind == "pass", 1.0, R.volume_pg / base / np.where(R.kind == "rec", TARGETABLE, 1.0))
        R["share"] = share
        tsum = R.groupby(["season", "week", "team", "kind"]).agg(S=("share", "sum"), ysum=("yards_pg", "sum")).reset_index()
        T = T.merge(tsum, on=["season", "week", "team", "kind"], how="left")
        T["rec_ratio"] = (T.team_yds_exp / T.ysum).clip(0.5, 2.0)
        fitT = T[T.season.isin(BT.FIT_SEASONS)]
        sbar = fitT.groupby(["kind", "week"]).S.mean(); rmed = fitT.groupby(["kind", "week"]).rec_ratio.median()
        T["S_bar"] = [sbar.get((k, w), np.nan) for k, w in zip(T.kind, T.week)]; T["rec_norm"] = [r / rmed.get((k, w), np.nan) for r, k, w in zip(T.rec_ratio, T.kind, T.week)]
        self.sbar, self.rmed = sbar, rmed
        self.T = T
        shape = (len(SEASONS), len(BT.WEEKS), len(teams), len(KINDS))
        self.arr = {}
        for c in ["base", "league", "prev", "gs", "gs_m", "sos_ratio", "new_coach", "frac_prev", "S", "S_bar", "rec_norm"]:
            A = np.full(shape, np.nan)
            A[T.season.map(self.S_IDX).values, T.week.map(self.W_IDX).values, T.team.map(self.T_IDX).values, T.kind.map(self.K_IDX).values] = T[c].values
            self.arr[c] = A
        ok = self.ti >= 0
        assert ok.all(), "rows without a team in the team table"
        self.age = R.age.values.astype(float)
        self.pos_group = np.array([POS_GROUP[k].get(p, "other") for k, p in zip(R.kind, R.pos)])
        self.fit_mask = np.isin(self.season, BT.FIT_SEASONS)
        self.ratios = {}

    # -------------------------------------------------------------- inputs (with an optional within-season permutation)
    def team_input(self, col: str, perm: dict | None = None) -> np.ndarray:
        ti = self.ti if perm is None else np.array([perm[s][t] for s, t in zip(self.si, self.ti)])
        return self.arr[col][self.si, self.wi, ti, self.ki]

    def team_perm(self, rng) -> dict:
        n = len(self.teams)
        return {i: rng.permutation(n) for i in range(len(SEASONS))}

    def age_perm(self, rng) -> np.ndarray:
        """Ages swapped between player-seasons of the same kind and season."""
        R = self.R; key = pd.Series(list(zip(R.kind, R.season, R.player_id)))
        u = pd.DataFrame({"kind": R.kind, "season": R.season, "player_id": R.player_id, "age": self.age}).drop_duplicates(["kind", "season", "player_id"])
        u["age_p"] = u.groupby(["kind", "season"]).age.transform(lambda x: rng.permutation(x.values))
        m = dict(zip(zip(u.kind, u.season, u.player_id), u.age_p))
        return np.array([m[k] for k in key])

    def age_factor(self, mode: str, age: np.ndarray | None = None) -> np.ndarray:
        rt = self.ratios[mode]
        key = {(r.kind, r.pos_group, r.age_band): r.ratio for r in rt.itertuples() if r.pos_group != "other" and r.age_band != "unknown"}
        age = self.age if age is None else age
        return np.array([key.get((k, pg, age_band(a)), 1.0) for k, pg, a in zip(self.kind, self.pos_group, age)])

    # -------------------------------------------------------------- the factor of a spec
    def factor(self, spec: dict, rng=None, shuffle: bool = False) -> np.ndarray:
        """spec keys: league (w), prev (w), gs ('d'|'d_m'), coach (w), age ('played'|'all'), sos (scale of W), comp (alpha),
        recon (scale of RECON_W). shuffle: every driving input of the spec takes a within-season permutation."""
        P = (lambda: self.team_perm(rng)) if shuffle else (lambda: None)
        base = self.arr["base"][self.si, self.wi, self.ti, self.ki]; league = self.arr["league"][self.si, self.wi, self.ti, self.ki]
        V = base.copy()
        if spec.get("league"):
            b_in = self.team_input("base", P())                     # the team volume the league blend shrinks
            V = V + spec["league"] * (league - b_in)
        if spec.get("prev"):
            pv = self.team_input("prev", P()); pv = np.where(np.isnan(pv), base, pv)
            V = V + spec["prev"] * (pv - base)
        if spec.get("gs"):
            col = "gs" if spec["gs"] == "d" else "gs_m"; p = P()
            V = V + (self.team_input(col, p) - self.team_input("base", p))
        if spec.get("coach"):
            nc = self.team_input("new_coach", P()); fp = self.arr["frac_prev"][self.si, self.wi, self.ti, self.ki]
            V = V + spec["coach"] * np.nan_to_num(nc) * fp * (league - base)
        V = np.clip(V, 0, None)
        f = np.where(base > 0, V / np.where(base > 0, base, 1.0), 1.0)
        if spec.get("sos"):
            r = self.team_input("sos_ratio", P()); wk = np.array([PR.W[k] for k in self.kind])
            f = f * (1 + spec["sos"] * wk * (np.nan_to_num(r, nan=1.0) - 1))
        if spec.get("comp"):
            p = P(); S = self.team_input("S", p); Sb = self.arr["S_bar"][self.si, self.wi, self.ti, self.ki]
            c = np.clip((Sb / S) ** spec["comp"], *COMP_CLIP); c = np.where((self.kind == "pass") | ~np.isfinite(c), 1.0, c)
            f = f * c
        if spec.get("recon"):
            r = np.clip(self.team_input("rec_norm", P()), 0.5, 2.0); wk = np.array([PR.RECON_W[k]["yds"] for k in self.kind])
            f = f * np.where(np.isfinite(r), 1 + spec["recon"] * wk * (r - 1), 1.0)
        if spec.get("age"):
            f = f * self.age_factor(spec["age"], self.age_perm(rng) if shuffle else None)
        return np.nan_to_num(f, nan=1.0)

    # -------------------------------------------------------------- scoring
    def proj(self, f: np.ndarray, avail: dict, blend: dict) -> np.ndarray:
        a = np.minimum(np.array([avail[k] for k in self.kind]) * self.mult, 1.0); b = np.array([blend[k] for k in self.kind])
        return (1 - b) * (self.so + self.ypg * f * self.left * a) + b * self.pace

    def refit(self, f: np.ndarray, target: str) -> tuple[dict, dict]:
        av, bl = {}, {}
        y = self.actual[target]
        for k in KINDS:
            m = self.fit_mask & (self.kind == k)
            so, g, left, mu, pace, act = self.so[m], (self.ypg * f)[m], self.left[m], self.mult[m], self.pace[m], y[m]
            A = np.minimum(BT.AVAIL_GRID[:, None] * mu[None, :], 1.0)                 # grid x rows
            own = so[None, :] + g[None, :] * left[None, :] * A
            best = None
            for b in BT.BLEND_GRID:
                e = np.abs((1 - b) * own + b * pace[None, :] - act[None, :]).mean(axis=1)
                i = int(np.argmin(e))
                if best is None or e[i] < best[0] - 1e-12:
                    best = (e[i], float(BT.AVAIL_GRID[i]), float(b))
            av[k], bl[k] = best[1], best[2]
        return av, bl

    def errors(self, f: np.ndarray, config: str, target: str) -> tuple[np.ndarray, dict, dict]:
        if config == "fixed":
            av, bl = dict(PS.AVAIL), dict(PS.BLEND)
        else:
            av, bl = self.refit(f, target)
        return np.abs(self.proj(f, av, bl) - self.actual[target]), av, bl

    def cells(self, err: np.ndarray) -> pd.DataFrame:
        """MAE by kind x window (pooled), kind x window x as-of week, kind x season x as-of week."""
        df = pd.DataFrame({"kind": self.kind, "window": self.win, "season": self.season, "week": self.week, "err": err})
        a = df.groupby(["kind", "window"]).err.agg(["mean", "size"]).reset_index().assign(asof_week="all", season="all")
        b = df.groupby(["kind", "window", "week"]).err.agg(["mean", "size"]).reset_index().rename(columns={"week": "asof_week"}).assign(season="all")
        c = df.groupby(["kind", "window", "season", "week"]).err.agg(["mean", "size"]).reset_index().rename(columns={"week": "asof_week"})
        o = pd.concat([a, b, c], ignore_index=True).rename(columns={"mean": "mae", "size": "n"})
        o["asof_week"] = o.asof_week.astype(str); o["season"] = o.season.astype(str)
        return o

    def window_mae(self, err: np.ndarray) -> dict:
        out = {}
        for k in KINDS:
            for w in WINDOWS:
                m = (self.kind == k) & (self.win == w)
                out[(k, w)] = float(err[m].mean())
        return out


# ------------------------------------------------------------------------------------------------ variants
PART1 = {"b25": {"league": 0.25}, "b50": {"league": 0.5}, "c25": {"prev": 0.25}, "c50": {"prev": 0.5}, "d": {"gs": "d"}, "d_m": {"gs": "d_m"},
         "e_c25_d": {"prev": 0.25, "gs": "d"}, "e_c25_d_m": {"prev": 0.25, "gs": "d_m"}, "e_c50_d": {"prev": 0.5, "gs": "d"}, "e_c50_d_m": {"prev": 0.5, "gs": "d_m"}}
NEW = {"sos": {"sos": 1.0}, "sos_h": {"sos": 0.5}, "coach25": {"coach": 0.25}, "coach50": {"coach": 0.5}, "comp25": {"comp": 0.25}, "comp50": {"comp": 0.5},
       "recon": {"recon": 1.0}, "recon_h": {"recon": 0.5}}
FAMILY = {"league": "league", "prev": "prev", "gs": "gs", "coach": "coach", "age": "age", "sos": "sos", "comp": "comp", "recon": "recon"}
NA = {("comp25", "pass"), ("comp50", "pass")}


def study():
    t0 = time.time(); st = Study(); R = st.R
    print(f"rows {len(R)} by window: {R.groupby(['window']).size().to_dict()} ({time.time() - t0:.0f}s)", flush=True)
    T = pd.read_csv(SCR / "touches_left.csv")
    X = R.assign(base=st.arr["base"][st.si, st.wi, st.ti, st.ki])
    for m in ("played", "all"):
        st.ratios[m] = fit_age_ratios(X, T, m)
    print(f"ages known for {np.isfinite(st.age).mean():.3f} of rows", flush=True)
    ones = np.ones(len(R))
    base_err = {(c, t): st.errors(ones, c, t) for c in ("fixed", "refit") for t in TARGETS}
    base_cells = {ct: st.cells(e[0]) for ct, e in base_err.items()}
    base_win = {ct: st.window_mae(e[0]) for ct, e in base_err.items()}
    for ct, e in base_err.items():
        print("base", ct, "avail", e[1], "blend", e[2], {k: round(v, 1) for k, v in base_win[ct].items()}, flush=True)
    specs = dict(PART1)
    results, cellrows, verdict = [], [], []
    real_f = {}

    def run(name, spec, kinds=KINDS, configs=None):
        f = st.factor(spec); real_f[(name, kinds)] = f
        for (c, t) in base_err:
            if configs is not None and c not in configs:
                continue
            e, av, bl = st.errors(f, c, t)
            wm = st.window_mae(e); cl = st.cells(e).merge(base_cells[(c, t)], on=["kind", "window", "asof_week", "season"], suffixes=("", "_base"))
            cl["gain"] = cl.mae_base - cl.mae
            for k in kinds:
                if (name, k) in NA:
                    continue
                ck = cl[cl.kind == k]
                pooled = ck[(ck.asof_week == "all")].set_index("window").gain
                wk = ck[(ck.asof_week != "all") & (ck.season == "all")]; sw = ck[(ck.season != "all")]
                results.append({"variant": name, "kind": k, "config": c, "target": t, "avail": av[k], "blend": bl[k],
                                **{f"mae_{w}": wm[(k, w)] for w in WINDOWS}, **{f"base_{w}": base_win[(c, t)][(k, w)] for w in WINDOWS},
                                **{f"gain_{w}": float(pooled.get(w, np.nan)) for w in WINDOWS},
                                "rule1": bool(all(pooled.get(w, -1) > 0 for w in WINDOWS)),
                                "worst_cell": float(wk.gain.min()), "worst_cell_at": f"{wk.loc[wk.gain.idxmin(), 'window']} wk{wk.loc[wk.gain.idxmin(), 'asof_week']}",
                                "worst_season_week": float(sw.gain.min()), "worst_season_week_at": f"{sw.loc[sw.gain.idxmin(), 'season']} wk{sw.loc[sw.gain.idxmin(), 'asof_week']}"})
                cellrows.append(ck.assign(variant=name, config=c, target=t))
        print(f"scored {name} {'/'.join(kinds)} ({time.time() - t0:.0f}s)", flush=True)

    for name, spec in PART1.items():
        run(name, spec)
    res = pd.DataFrame(results)

    def rule1_both(name, k, c="fixed"):
        x = res[(res.variant == name) & (res.kind == k) & (res.config == c)]
        return bool(len(x) == 2 and x.rule1.all())

    def min_gain(name, k, c="fixed"):
        x = res[(res.variant == name) & (res.kind == k) & (res.config == c)]
        return float(x[[f"gain_{w}" for w in WINDOWS]].min(axis=1).min())

    best1 = {}
    for k in KINDS:
        c = [(min_gain(v, k), v) for v in PART1 if rule1_both(v, k)]
        best1[k] = max(c)[1] if c else "base"
    print("best Part 1 by kind (rule 1, fixed, both targets):", best1, flush=True)
    for m, name in (("played", "p2"), ("all", "p2_all")):
        specs[name] = {"age": m}; run(name, {"age": m})
    # p2 + best1: per kind, the age ratio on top of the kind's best Part 1 piece
    for m, name in (("played", "p2+best1"), ("all", "p2_all+best1")):
        for k in KINDS:
            spec = {"age": m, **(PART1[best1[k]] if best1[k] != "base" else {})}
            specs[name + ":" + k] = spec; run(name, spec, kinds=(k,))
    for name, spec in NEW.items():
        specs[name] = spec; run(name, spec)
    res = pd.DataFrame(results)
    res.to_csv(SCR / "results_stage1.csv", index=False)
    # ---------------------------------------------------------------- placebo for every variant passing rule 1 (per config)
    def spec_of(name, k):
        return specs.get(name + ":" + k, specs.get(name))

    plac = []
    cand = res[res.rule1].groupby(["variant", "kind", "config"]).target.nunique().reset_index()
    cand = cand[cand.target == 2]
    print(f"placebo candidates (rule 1 on both targets): {len(cand)}", flush=True)
    for r in cand.itertuples():
        spec = spec_of(r.variant, r.kind); rng = np.random.default_rng(20260929)
        real = {t: res[(res.variant == r.variant) & (res.kind == r.kind) & (res.config == r.config) & (res.target == t)].iloc[0] for t in TARGETS}
        pg = {t: {w: [] for w in WINDOWS} for t in TARGETS}
        for dnum in range(N_DRAWS):
            f = st.factor(spec, rng, shuffle=True)
            for t in TARGETS:
                e, _, _ = st.errors(f, r.config, t); m = (st.kind == r.kind)
                for w in WINDOWS:
                    mm = m & (st.win == w)
                    pg[t][w].append(base_win[(r.config, t)][(r.kind, w)] - float(e[mm].mean()))
        row = {"variant": r.variant, "kind": r.kind, "config": r.config}
        allpass = True
        for t in TARGETS:
            joint = np.ones(N_DRAWS, bool)
            for w in WINDOWS:
                g = np.array(pg[t][w]); rg = float(real[t][f"gain_{w}"])
                beat = int((g < rg).sum()); joint &= (g < rg)
                row[f"{t}_{w}_real"] = rg; row[f"{t}_{w}_p90"] = float(np.percentile(g, 90)); row[f"{t}_{w}_beat"] = beat; row[f"{t}_{w}_pct"] = float((g < rg).mean() * 100)
                allpass &= beat >= NEED
            row[f"{t}_joint_beat"] = int(joint.sum())
        row["rule3"] = bool(allpass)
        plac.append(row); print(f"placebo {r.variant} {r.kind} {r.config}: rule 3 {'pass' if allpass else 'fail'} ({time.time() - t0:.0f}s)", flush=True)
    PL = pd.DataFrame(plac)
    PL.to_csv(SCR / "placebo.csv", index=False)
    # ---------------------------------------------------------------- rule 5: passing pieces together, per kind and config
    combos = []
    for c in ("fixed", "refit"):
        for k in KINDS:
            ok = PL[(PL.kind == k) & (PL.config == c) & PL.rule3] if len(PL) else PL
            if not len(ok):
                continue
            fam_best = {}
            for v in ok.variant:
                sp = spec_of(v, k); fams = tuple(sorted({FAMILY[x] for x in sp}))
                g = float(res[(res.variant == v) & (res.kind == k) & (res.config == c)][[f"gain_{w}" for w in WINDOWS]].min(axis=1).min())
                if fams not in fam_best or g > fam_best[fams][0]:
                    fam_best[fams] = (g, v, sp)
            # greedy union over families, largest smallest-window gain first, no family twice
            used, spec, names_ = set(), {}, []
            for fams, (g, v, sp) in sorted(fam_best.items(), key=lambda x: -x[1][0]):
                if used & set(fams):
                    continue
                used |= set(fams); spec.update(sp); names_.append(v)
            combos.append((c, k, "+".join(names_), spec, len(names_)))
    for c, k, nm, spec, npieces in combos:
        name = f"combo[{nm}]"; specs[name + ":" + k] = spec
        run(name, spec, kinds=(k,), configs=(c,))
    res = pd.DataFrame(results)
    cells = pd.concat(cellrows, ignore_index=True)
    res.to_csv(SCR / "results.csv", index=False)
    out = pd.concat([res.assign(row="summary"), PL.assign(row="placebo") if len(PL) else pd.DataFrame(),
                     cells.assign(row="cell")], ignore_index=True)
    out.round(4).to_csv(PS.REP / "player_season_link2.csv", index=False)
    meta = {"rmed": {f"{k}|{w}": float(v) for (k, w), v in st.rmed.items()}, "sbar": {f"{k}|{w}": float(v) for (k, w), v in st.sbar.items()}, "best1": best1, "secs": round(time.time() - t0), "ratios": {m: st.ratios[m].to_dict("records") for m in st.ratios},
            "base": {f"{c}|{t}": {"avail": base_err[(c, t)][1], "blend": base_err[(c, t)][2], "mae": {f"{k}|{w}": round(v, 3) for (k, w), v in base_win[(c, t)].items()}} for (c, t) in base_err},
            "n_rows": R.groupby(["window", "kind"]).size().reset_index().values.tolist(), "specs": {k: v for k, v in specs.items()}, "combos": [(c, k, nm, npieces) for c, k, nm, _, npieces in combos]}
    (SCR / "meta.json").write_text(json.dumps(meta, default=str, indent=1))
    print(f"study done ({time.time() - t0:.0f}s)", flush=True)


# ------------------------------------------------------------------------------------------------ report
def verdicts(res: pd.DataFrame, PL: pd.DataFrame) -> pd.DataFrame:
    """Per variant x kind x config: rule 1 on each target, rule 3, the failing rule."""
    out = []
    for (v, k, c), g in res.groupby(["variant", "kind", "config"], sort=False):
        r1 = {t: bool(g[g.target == t].rule1.iloc[0]) for t in TARGETS if (g.target == t).any()}
        p = PL[(PL.variant == v) & (PL.kind == k) & (PL.config == c)] if len(PL) else PL
        r3 = bool(p.rule3.iloc[0]) if len(p) else None
        if not all(r1.values()):
            fails = [t for t, x in r1.items() if not x]
            gg = g[g.target.isin(fails)]
            bad = sorted({w for _, r in gg.iterrows() for w in WINDOWS if not r[f"gain_{w}"] > 0}, key=WINDOWS.index)
            why = "rule 1 (" + ", ".join(bad) + (" on " + "/".join(fails) if len(fails) < 2 else "") + ")"
        elif r3 is False:
            bad = [f"{t} {w}" for t in TARGETS for w in WINDOWS if p.iloc[0][f"{t}_{w}_beat"] < NEED]
            why = "rule 3 (placebo: " + ", ".join(bad) + ")"
        else:
            why = ""
        pct = None
        if len(p):
            pct = min(p.iloc[0][f"reg_{w}_pct"] for w in WINDOWS)
        out.append({"variant": v, "kind": k, "config": c, "rule1_reg": r1.get("reg"), "rule1_harness": r1.get("harness"), "rule3": r3, "placebo_min_pct_reg": pct,
                    "pass": bool(all(r1.values()) and r3 is True), "fails": why})
    return pd.DataFrame(out)


def report():
    res = pd.read_csv(SCR / "results.csv"); PL = pd.read_csv(SCR / "placebo.csv") if (SCR / "placebo.csv").exists() else pd.DataFrame()
    meta = json.loads((SCR / "meta.json").read_text()); chk = json.loads((SCR / "cache_check.json").read_text())
    V = verdicts(res, PL)
    L = ["# Player season totals, round 3: the team link and age priors rerun on today's availability, and new as-of ideas (29 Sep 2026)\n",
         "`experiments/player_season_link2.py`. The rule is `reports/round3_rule.md`, written before any result, followed as written: "
         "(1) lower season-total miss on every window, (3) beats its own within-season shuffle placebo on every window in at least 45 of 50 draws, "
         "(4) no market input, no look-ahead, no new data source, (5) the passing pieces rerun together must pass (1). Rule 2 (bet records) does not apply: season totals do not touch the game model.\n",
         "## Set-up\n",
         f"- Rows: the harness cache `reports/player_season_rows.csv` (today's `player_season.project` with the availability logit; checked: a fresh build of 2019 week 5 from today's code matches it, same players {chk['same_players']}, max difference {chk['max_diff']:.4f}) for 2016-25, "
         "plus 2015 built with the same code on 2014-15 plays read through `nflmodel.scheme.load_plays` (the loader behind scheme_plays.parquet) and the 2015 weekly roster with its team codes normalised. As-of weeks 1, 5, 9, 13 (2016 week 1 absent, as in the harness).",
         "- Windows: **2015** (early, never used to choose anything; the only season before the fit window the plays reach), **2016-18** (fit window of AVAIL, BLEND, the availability logit and every fitted piece here), **2019-22**, **2023-25**. Rule 1 needs a lower miss on all four.",
         "- Targets: the harness's actual totals count every game with week <= 18, which for 2015-2020 includes the wild-card round (week 18 of those seasons is a playoff week: a bug in `player_season.season_actuals`, see the note at the end; fixed 29 Sep 2026 after this study). Every variant is scored on the harness target and on the regular-season-only total (**reg**); rule 1 must hold on both. The placebo is counted on both.",
         "- Configs: **fixed** = today's AVAIL and BLEND unchanged (the code change is the variant alone); **refit** = AVAIL and BLEND refit on 2016-18 on the harness grids for the base and for each variant (the change then includes the refit constants).",
         "- The miss is the mean absolute error of the season total (yards), all players projected at the as-of week, as-of weeks pooled. Gain = base miss - variant miss (positive = better).\n",
         "## Base\n", "| config | target | kind | AVAIL | BLEND | 2015 | 2016-18 | 2019-22 | 2023-25 |", "|---|---|---|---|---|---|---|---|---|"]
    for ct, b in meta["base"].items():
        c, t = ct.split("|")
        for k in KINDS:
            L.append(f"| {c} | {t} | {k} | {b['avail'][k]} | {b['blend'][k]} | " + " | ".join(f"{b['mae'][k + '|' + w]:.1f}" for w in WINDOWS) + " |")
    L.append("\nRows per window and kind: " + ", ".join(f"{w} {k} {n}" for w, k, n in meta["n_rows"]) + "\n")
    for c in ("fixed", "refit"):
        L.append(f"## Every variant, {c} config\n")
        L.append("Gains in yards of season-total miss, reg target / harness target. Worst week = the largest loss in any window x as-of week cell (reg target), and in any single season x as-of week (reg). Placebo = the lowest, over the four windows, of the share of the 50 shuffles the real gain beats (reg target); blank when rule 1 fails.\n")
        L.append("| kind | variant | 2015 | 2016-18 | 2019-22 | 2023-25 | worst window-week | worst season-week | placebo | verdict |")
        L.append("|---|---|---|---|---|---|---|---|---|---|")
        for k in KINDS:
            for v in res[(res.kind == k) & (res.config == c)].variant.unique():
                g = res[(res.variant == v) & (res.kind == k) & (res.config == c)].set_index("target")
                if "reg" not in g.index:
                    continue
                r, h = g.loc["reg"], g.loc["harness"]
                vv = V[(V.variant == v) & (V.kind == k) & (V.config == c)].iloc[0]
                pl = "" if pd.isna(vv.placebo_min_pct_reg) or vv.placebo_min_pct_reg is None else f"{vv.placebo_min_pct_reg:.0f}%"
                L.append(f"| {k} | {v} | " + " | ".join(f"{r[f'gain_{w}']:+.2f} / {h[f'gain_{w}']:+.2f}" for w in WINDOWS) +
                         f" | {r.worst_cell:+.2f} ({r.worst_cell_at}) | {r.worst_season_week:+.2f} ({r.worst_season_week_at}) | {pl} | {'**PASS**' if vv['pass'] else 'fail: ' + vv.fails} |")
        L.append("")
    if len(PL):
        L.append("## Placebo detail (variants passing rule 1 on both targets)\n")
        L.append("Real gain, the 90th percentile of the 50 shuffled gains, and how many of 50 the real gain beats, per window (reg target; harness in the csv).\n")
        L.append("| kind | variant | config | " + " | ".join(WINDOWS) + " | joint (all four) reg / harness | rule 3 |")
        L.append("|---|---|---|" + "---|" * len(WINDOWS) + "---|---|")
        for r in PL.itertuples():
            L.append(f"| {r.kind} | {r.variant} | {r.config} | " + " | ".join(f"{PL.loc[r.Index, f'reg_{w}_real']:+.2f} vs {PL.loc[r.Index, f'reg_{w}_p90']:+.2f} ({int(PL.loc[r.Index, f'reg_{w}_beat'])}/50)" for w in WINDOWS) +
                     f" | {int(PL.loc[r.Index, 'reg_joint_beat'])} / {int(PL.loc[r.Index, 'harness_joint_beat'])} | {'pass' if r.rule3 else 'fail'} |")
        L.append("")
    L.append("## Rule 5: the passing pieces together\n")
    cmb = res[res.variant.str.startswith("combo[")]
    if len(cmb):
        L.append("| kind | config | combination | 2015 | 2016-18 | 2019-22 | 2023-25 | worst window-week | rule 1 (reg, harness) |"); L.append("|---|---|---|---|---|---|---|---|---|")
        for (v, k, c), g in cmb.groupby(["variant", "kind", "config"]):
            g = g.set_index("target"); r, h = g.loc["reg"], g.loc["harness"]
            L.append(f"| {k} | {c} | {v} | " + " | ".join(f"{r[f'gain_{w}']:+.2f} / {h[f'gain_{w}']:+.2f}" for w in WINDOWS) + f" | {r.worst_cell:+.2f} | {bool(r.rule1)}, {bool(h.rule1)} |")
    else:
        L.append("No variant passed rules 1, 3 and 4, so there is nothing to combine.")
    L.append("\n## Age ratios (fitted on 2016-18; touches over the games left / what the as-of share expected; shrunk toward 1 with 30 players)\n")
    for m, rt in meta["ratios"].items():
        L.append(f"{'p2 (games he played)' if m == 'played' else 'p2_all (every game left)'}: " + "; ".join(f"{r['kind']} {r['pos_group']} {r['age_band']} {r['ratio']:.3f} (n {r['n']})" for r in rt if r['pos_group'] != 'other' and r['age_band'] != 'unknown'))
        L.append("")
    L.append(f"Best Part 1 piece by kind for p2+best1 (fixed config, rule 1 on both targets): {meta['best1']}.\n")
    (SCR / "verdicts.csv").write_text(V.to_csv(index=False))
    return L, V


CHANGE = {
    "league": "in project(), after per_game(): for the kind, yards_pg and td_pg x (1 + {w} x (league_V / V_team - 1)), where V_team = props.teams_volume(a)[team][{vk}] and league_V = the mean of that over the teams in V (the as-of frame), i.e. the team volume for the games left is blended {w} of the way to the league mean",
    "prev": "in project(): for the kind, yards_pg and td_pg x (1 + {w} x (prev_V / V_team - 1)), prev_V = the team's {vk} over the previous regular season (season_type REG, plays of season - 1 in d; V_team when missing)",
    "gs": "in project(): for the kind, yards_pg and td_pg x (V_team + mean over the team's games left of (props.game_script(kind, V_team, margin, None) - V_team)) / V_team, margin = season.py's expected margin for each game left ({mode})",
    "coach": "in project(): for the kind, yards_pg and td_pg x (1 + {w} x new_coach x frac_prev x (league_V / V_team - 1)), new_coach = the head coach of his team's latest game before the week (week-1 game at week 1) differs from the coach of last season's final game, frac_prev = (17 - the team's games this season inside the last-17 window) / 17",
    "sos": "in project(): for the kind, yards_pg x (1 + {w} x props.W[kind] x (mean over the team's games left of allowed_opp / league - 1)), allowed from props.defenses(a) ({ac}) and league from props.league_baselines(a) ({lc})",
    "comp": "in project(): for the kind, yards_pg and td_pg x clip((S_BAR[kind][week] / S) ** {w}, 0.75, 1.33), S = the sum over the team's projected players of the kind of volume_pg / (V_team x {tg}); S_BAR the 2016-18 means below",
    "recon": "in project(): for the kind, yards_pg x (1 + {w} x props.RECON_W[kind]['yds'] x (clip(r / R_MED[kind][week], 0.5, 2) - 1)), r = clip(team expected yards per game over the games left (props.TEAM_FIT[kind]['yds'] on season.py expected points) / sum of the team's projected yards_pg, 0.5, 2)",
    "age": "in project(): yards_pg and td_pg x the (kind, position group, age band) ratio below ({mode})",
}


def change_text(spec: dict, kind: str) -> list[str]:
    out = []
    for key, val in spec.items():
        vk = KIND_VOL[kind]; ac, lc = ALLOWED[kind]
        out.append(CHANGE[key].format(w=val, vk=vk, mode=val, ac=ac, lc=lc, tg=TARGETABLE if kind == "rec" else 1.0))
    return out


def write_report():
    L, V = report()
    meta = json.loads((SCR / "meta.json").read_text()); res = pd.read_csv(SCR / "results.csv")
    L.append("## Verdict\n")
    P = V[V["pass"]]
    if not len(P):
        L.append("Nothing passes. Every variant fails at least one of rules 1 and 3 on at least one kind (the failing rule is in the tables above); nothing changes in nflmodel/player_season.py.\n")
    for r in P.itertuples():
        spec = meta["specs"].get(f"{r.variant}:{r.kind}", meta["specs"].get(r.variant))
        g = res[(res.variant == r.variant) & (res.kind == r.kind) & (res.config == r.config) & (res.target == "reg")].iloc[0]
        L.append(f"- **{r.kind} {r.variant} ({r.config})** passes rules 1, 3 and 4. Code change: " + "; ".join(change_text(spec, r.kind)) +
                 (f"; AVAIL[{r.kind}] {g.avail}, BLEND[{r.kind}] {g.blend}" if r.config == "refit" else "; AVAIL and BLEND unchanged") + ".")
    # the regular-season target alone (the harness target counts wild-card games for 2015-20): what would pass on it
    PL = pd.read_csv(SCR / "placebo.csv") if (SCR / "placebo.csv").exists() else pd.DataFrame()
    near = []
    for r in PL.itertuples():
        reg_ok = all(PL.loc[r.Index, f"reg_{w}_beat"] >= NEED for w in WINDOWS)
        if reg_ok and not r.rule3:
            near.append(r)
    L.append("\n### On the regular-season target alone\n")
    if not near:
        L.append("Nothing passes rules 1 and 3 even on the regular-season-only total.\n")
    for r in near:
        spec = meta["specs"].get(f"{r.variant}:{r.kind}", meta["specs"].get(r.variant))
        g = res[(res.variant == r.variant) & (res.kind == r.kind) & (res.config == r.config)].set_index("target")
        hb = ", ".join(f"{w} {int(PL.loc[r.Index, f'harness_{w}_beat'])}/50" for w in WINDOWS)
        L.append(f"- {r.kind} {r.variant} ({r.config}) passes rule 1 on both targets and the placebo on every window of the regular-season target "
                 f"({', '.join(str(int(PL.loc[r.Index, f'reg_{w}_beat'])) + '/50' for w in WINDOWS)}), but not on the harness target ({hb}). "
                 "Gains reg " + ", ".join("%+.2f" % g.loc["reg", "gain_" + w] for w in WINDOWS) + "; worst window-week %+.2f, worst season-week %+.2f. " % (g.loc["reg", "worst_cell"], g.loc["reg", "worst_season_week"]) +
                 "The change it would be: " + "; ".join(change_text(spec, r.kind)) +
                 (("; R_MED[%s] by as-of week (2016-18 medians of r): " % r.kind) + ", ".join("wk%d %.4f" % (w, meta["rmed"][f"{r.kind}|{w}"]) for w in BT.WEEKS) + " (the page runs every week: weeks between would need the nearest or an interpolated value, which this study did not score)" if "recon" in spec else "") +
                 ". Under the joint reading of the placebo (all four windows at once) it beats %d of 50 on the regular-season target." % int(PL.loc[r.Index, "reg_joint_beat"]))
    L.append("")
    L.append("## Rule 4 (no new risk)\n")
    L.append("Every variant reads only what the weekly run already pulls and only as of the week: plays (last-17 volumes, the previous regular season, the defenses' allowed rates), "
             "our own game model (season.py profiles, fit_asof and expected_points on features_asof and pred_v3, no lines or totals), the schedule's head coach (games.parquet, filled for unplayed games), "
             "birth dates (players.parquet, already read by the availability logit), and the rows' own projected shares. No market input anywhere. All pass rule 4; none reaches rule 5 under the rule as registered.\n")
    L.append("## Notes\n")
    L.append("- (Fixed 29 Sep 2026, after this study.) `nflmodel/player_season.season_actuals` filtered `week <= 18` without `season_type`: for 2015-2020 week 18 is the wild-card round, so the harness's actual totals (and `prev_yards`, the week-1 pace baseline for 2016-21) include a playoff game for players on wild-card teams. The live page is unaffected for 2021 on (18 regular-season weeks), but the published backtest misses for 2016-20 are measured against partly-playoff totals. Not changed here (nflmodel/ is out of scope).")
    L.append("- The refit config refits AVAIL and BLEND on 2016-18 with that window's in-sample availability chances; for passers this flatters the fit and costs the test windows (base passing refit: 572.5 / 615.8 against today's 568.4 / 602.9 on the regular-season target), as the harness notes.")
    L.append("- recon for rushing: the team's expected rushing yards from props.TEAM_FIT (71.47 + 1.388 x expected points) barely moves with our game model (sd 3.8 yards a game over the team-weeks), so on rushing the reconciliation works mostly as a shrink of each team's summed rusher projections toward about 103 yards a game, not as information from the game model.")
    L.append("- The placebo for the previous-season volume (c) shuffles another team's previous season in, which on average pulls toward the league mean; its gains on rushing come close to the real one's, i.e. most of c's rushing gain is shrinkage, not the team's own history.")
    L.append(f"\nRuntime of the scoring run: {meta['secs']}s (build of the 2015 rows, the check and the team table: about 3 minutes).\n")
    (PS.REP / "player_season_link2.md").write_text("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    {"build": build, "study": study, "report": write_report}[sys.argv[1]]()
