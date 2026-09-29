"""The listed starting QB, audited and fixed (29 Sep 2026, after reports/postmortem.md found listed starters with no dropback).

The model's QB input reads the schedule's starter ids (games.parquet home_qb_id / away_qb_id, copied from nflverse's
schedules games.csv): ratings.build_features prices each team-game with that QB's rating (qb_rating, and opp_qb_rating),
model.qb_form reads the same id (qb_form_sum in the totals equation), and the carried-forward starter for unplayed games
(last_qb) is the most recent listed id. qb_out (trends.py, snap counts) and the player model (players.py) do not read it.

1. Audit, 2013-2026: every played team-game's listed id against the QB who took the team's first dropback (play-by-play,
   passer_id, the first dropback by a player whose roster position is QB, so a fake punt or a receiver's trick pass is not
   a "start") and the QB with the most dropbacks. Kinds: the listed QB took no dropback; he played but came in relief
   (someone else took the first dropback); a trick play took the first dropback (not an error); the listed QB started and
   was replaced in the game (not an error). Where the bad ids come from: the raw schedule file, the weekly rosters'
   status of the listed QB, the depth chart's QB1 before the game, and whether the listed QB was the team's previous
   starter (a stale id).
2. Fix candidates for played games: (a) the first-dropback QB, (b) the QB with the most dropbacks. Unplayed games keep
   the schedule's id; only last_qb (the carried-forward starter) comes from the corrected played games.
3. features_asof rebuilt in memory with each games frame (nothing under data/processed is written), walk_forward with the
   weekly refit on 2015-2025, trees cache redirected to a scratch path. Scored on 2015-18, 2019-22, 2023-25.
4. Strict: the corrected ids for every game before the one being priced (the training rows), the priced game keeps the
   listed id; walk_forward with the test rows taken from the listed-id table (the live walk_forward's own source with one
   line changed, checked to reproduce the live function when both tables are the same).

Usage: python -m experiments.qb_id_fix   (QBFIX_SCRATCH=dir for the trees cache and intermediate predictions)
Output: reports/qb_id_fix.csv (variant x window), reports/qb_id_fix.md.
"""
from __future__ import annotations
import os, sys, time, inspect, warnings, shutil
import numpy as np, pandas as pd
from nflmodel import ratings as R, model as M, backtest as B
from nflmodel.model import OUT
from nflmodel.build import TEAM_FIX
from experiments.common import score as common_score

warnings.simplefilter("ignore")
T0 = time.time()
ROOT = OUT.parent.parent
RAW, REP = ROOT / "data" / "raw", ROOT / "reports"
SCR = os.environ.get("QBFIX_SCRATCH", "/tmp/qb_id_fix")
os.makedirs(SCR, exist_ok=True)
WINDOWS = {"2015-18": range(2015, 2019), "2019-22": range(2019, 2023), "2023-25": range(2023, 2026)}
TEST = range(2015, 2026)
SPREAD_EDGE, UNDER_P, LAST_WEEK, VIG = 4.0, 0.55, 17, 1.1
RUNTIME = {}


def log(msg):
    print(f"[{time.time() - T0:7.1f}s] {msg}", flush=True)


# ---------------------------------------------------------------------------------------------------------------------
# 1. The audit
# ---------------------------------------------------------------------------------------------------------------------
def load_dropbacks(seasons=range(2013, 2027)) -> pd.DataFrame:
    fr = []
    for s in seasons:
        f = RAW / "pbp" / f"play_by_play_{s}.parquet"
        if not f.exists():
            continue
        p = pd.read_parquet(f, columns=["game_id", "play_id", "season", "posteam", "qb_dropback", "passer_id", "passer_player_id", "passer"])
        p = p[p.posteam.notna() & (pd.to_numeric(p.qb_dropback, errors="coerce") == 1)]
        fr.append(p)
    p = pd.concat(fr, ignore_index=True)
    p["posteam"] = p.posteam.replace(TEAM_FIX)
    return p.sort_values(["game_id", "play_id"]).reset_index(drop=True)


def load_rosters(seasons=range(2013, 2027)) -> pd.DataFrame:
    r = pd.concat([pd.read_parquet(RAW / "rosters" / f"roster_weekly_{s}.parquet", columns=["season", "week", "team", "gsis_id", "full_name", "position", "status"])
                   for s in seasons if (RAW / "rosters" / f"roster_weekly_{s}.parquet").exists()])
    r = r.dropna(subset=["gsis_id"])
    r["team"] = r.team.replace(TEAM_FIX)
    return r


def depth_qb1(L: pd.DataFrame) -> pd.Series:
    """The depth chart's QB1 before each game: the weekly chart (through 2024: club, week, depth_team 1, QB) or, from 2025,
    the latest ESPN snapshot taken before kickoff (pos_abb QB, pos_rank 1)."""
    out = pd.Series(index=L.index, dtype=object)
    old = []
    for s in range(2013, 2025):
        d = pd.read_parquet(RAW / "depth_charts" / f"depth_charts_{s}.parquet")
        d = d[(d.formation == "Offense") & (d.position == "QB") & (d.depth_position == "QB") & (d.depth_team.astype(str) == "1")]
        old.append(d.assign(team=d.club_code.replace(TEAM_FIX), week=d.week.astype(float))[["season", "week", "team", "gsis_id"]])
    dq = pd.concat(old).drop_duplicates(["season", "week", "team"]).set_index(["season", "week", "team"]).gsis_id
    m = L.season < 2025
    out[m] = [dq.get((s, float(w), t)) for s, w, t in zip(L.season[m], L.week[m], L.team[m])]
    for s in (2025, 2026):
        f = RAW / "depth_charts" / f"depth_charts_{s}.parquet"
        if not f.exists():
            continue
        d = pd.read_parquet(f)
        d = d[(d.pos_abb == "QB") & (d.pos_rank == 1)].copy()
        d["team"] = d.team.replace(TEAM_FIX)
        d["dt"] = pd.to_datetime(d.dt).dt.tz_convert("America/New_York").dt.tz_localize(None)
        by = {t: x.sort_values("dt") for t, x in d.groupby("team")}
        for i in L.index[L.season == s]:
            x = by.get(L.at[i, "team"])
            if x is None:
                continue
            x = x[x.dt < L.at[i, "kickoff_et"]]
            out[i] = x.gsis_id.iloc[-1] if len(x) else None
    return out


def audit(games: pd.DataFrame):
    p = load_dropbacks()
    ros = load_rosters()
    pos_s = ros.drop_duplicates(["season", "gsis_id"], keep="last").set_index(["season", "gsis_id"]).position
    pos_any = ros.drop_duplicates("gsis_id", keep="last").set_index("gsis_id").position
    name = ros.drop_duplicates("gsis_id", keep="last").set_index("gsis_id").full_name
    d = p.dropna(subset=["passer_id"]).copy()
    d["pos"] = [pos_s.get((s, q), pos_any.get(q)) for s, q in zip(d.season, d.passer_id)]
    d["is_qb"] = d.pos.isna() | (d.pos == "QB")          # an unknown position counts as a QB
    g = d.groupby(["game_id", "posteam"])
    first_any = g.agg(first_any=("passer_id", "first"), first_any_name=("passer", "first"))
    first_qb = d[d.is_qb].groupby(["game_id", "posteam"]).agg(first_qb=("passer_id", "first"), first_qb_name=("passer", "first"))
    # passer_player_id (the column the question names): empty on scrambles, so its first non-empty value can differ
    first_ppid = p.dropna(subset=["passer_player_id"]).groupby(["game_id", "posteam"]).passer_player_id.first().rename("first_ppid")
    d["ord"] = np.arange(len(d))
    cnt = d.groupby(["game_id", "posteam", "passer_id"]).agg(n=("ord", "size"), o=("ord", "min"), nm=("passer", "first")).reset_index()
    most = cnt.sort_values(["n", "o"], ascending=[False, True]).drop_duplicates(["game_id", "posteam"]).set_index(["game_id", "posteam"])
    most = most.rename(columns={"passer_id": "most_qb", "n": "most_n", "nm": "most_name"})[["most_qb", "most_n", "most_name"]]
    tot = cnt.groupby(["game_id", "posteam"]).n.sum().rename("team_db")
    nqb = cnt.groupby(["game_id", "posteam"]).size().rename("n_passers")
    first_qb = first_any.join(first_qb)[["first_qb", "first_qb_name"]]
    nq = first_qb.first_qb.isna()   # no QB dropped back (2020_12_NO_DEN: a receiver played quarterback): the first passer
    first_qb.loc[nq, "first_qb"], first_qb.loc[nq, "first_qb_name"] = first_any.loc[nq, "first_any"], first_any.loc[nq, "first_any_name"]
    J = first_any.join(first_qb, how="left", rsuffix="_").join(first_ppid).join(most).join(tot).join(nqb).rename_axis(["game_id", "team"]).reset_index()

    pl = games[games.home_score.notna() & (games.season >= 2013)]
    rows = []
    for side in ("home", "away"):
        x = pl[["game_id", "season", "week", "game_type", "kickoff_et", f"{side}_team", f"{side}_qb_id", f"{side}_qb_name"]].copy()
        x.columns = ["game_id", "season", "week", "game_type", "kickoff_et", "team", "listed_id", "listed_name"]
        x["side"] = side
        rows.append(x)
    L = pd.concat(rows).merge(J, on=["game_id", "team"], how="left").sort_values(["season", "week", "game_id", "side"]).reset_index(drop=True)
    c = cnt.set_index(["game_id", "posteam", "passer_id"]).n
    L["listed_n"] = [int(c.get((gi, t, q), 0)) for gi, t, q in zip(L.game_id, L.team, L.listed_id)]
    L["first_qb_n"] = [int(c.get((gi, t, q), 0)) if isinstance(q, str) else 0 for gi, t, q in zip(L.game_id, L.team, L.first_qb)]
    has = L.first_qb.notna()
    L["kind"] = np.select(
        [L.listed_id.isna(), ~has, (L.listed_id == L.first_qb) & (L.first_qb == L.most_qb), L.listed_id == L.first_qb, L.listed_n == 0],
        ["no listed id", "no play-by-play", "ok", "started, replaced in game", "listed QB took no dropback"], "listed QB came in relief")
    L["trick_first"] = has & (L.first_any != L.first_qb)
    L["listed_id_name"] = L.listed_id.map(name)
    nrm = lambda s: s.fillna("").str.lower().str.replace(r"[^a-z]", "", regex=True).str.replace(r"(jr|iii|ii)$", "", regex=True).str[-5:]
    L["id_name_disagree"] = L.listed_id.notna() & L.listed_id_name.notna() & (nrm(L.listed_id_name) != nrm(L.listed_name))
    st = ros.drop_duplicates(["season", "week", "team", "gsis_id"]).set_index(["season", "week", "team", "gsis_id"]).status
    L["listed_status"] = [st.get((s, w, t, q)) for s, w, t, q in zip(L.season, L.week, L.team, L.listed_id)]
    L["depth_qb1"] = depth_qb1(L)
    # the team's previous starter (first-dropback QB of its previous played game), and every earlier starter this season
    L = L.sort_values(["team", "season", "week"]).reset_index(drop=True)
    L["prev_first"] = L.groupby("team").first_qb.shift(1)
    seen, early = {}, []
    for t, s, q, fq in zip(L.team, L.season, L.listed_id, L.first_qb):
        k = (t, s); early.append(q in seen.get(k, set())); seen.setdefault(k, set()).add(fq)
    L["started_earlier_season"] = early
    L = L.sort_values(["season", "week", "game_id", "side"]).reset_index(drop=True)
    # the raw file: is the bad id already in nflverse's schedules games.csv (not introduced by build.py)?
    raw = pd.read_csv(RAW / "schedules" / "games.csv", usecols=["game_id", "home_qb_id", "away_qb_id"]).set_index("game_id")
    L["raw_id"] = [raw.at[gi, f"{sd}_qb_id"] if gi in raw.index else None for gi, sd in zip(L.game_id, L.side)]
    return L, p


# ---------------------------------------------------------------------------------------------------------------------
# 2-4. Features, walk-forward, scoring
# ---------------------------------------------------------------------------------------------------------------------
def patch(games: pd.DataFrame, L: pd.DataFrame, col: str) -> pd.DataFrame:
    """games with the played team-games' ids replaced by L[col] where the play-by-play has one (else the listed id)."""
    g = games.copy()
    for side in ("home", "away"):
        m = L[(L.side == side) & L[col].notna()].set_index("game_id")[col]
        idx = g.game_id.isin(m.index)
        g.loc[idx, f"{side}_qb_id"] = g.loc[idx, "game_id"].map(m).values
    return g


def make_split_walk_forward():
    """The live walk_forward with the test rows read from a second table (fte). Everything else is the live source."""
    src = inspect.getsource(M.walk_forward)
    reps = [("def walk_forward(f: pd.DataFrame, test_seasons,", "def walk_forward_split(f: pd.DataFrame, fte: pd.DataFrame, test_seasons,"),
            ("    f = prep(f)\n", "    f = prep(f); fte = prep(fte)\n"),
            ("test_all = f[f.season == s]", "test_all = fte[fte.season == s]")]
    for a, b in reps:
        assert src.count(a) == 1, a
        src = src.replace(a, b)
    ns = dict(M.__dict__)
    exec(src, ns)
    return ns["walk_forward_split"]


def bet_records(pred: pd.DataFrame, games: pd.DataFrame, seasons) -> dict:
    d = B.join(pred, games)
    d = d[(d.game_type == "REG") & d.season.isin(seasons) & (d.week <= LAST_WEEK)]
    s = d[d.spread_line.notna() & (d.spread_edge.abs() >= SPREAD_EDGE)]
    cm = (s.result - s.spread_line) * np.sign(s.spread_edge)
    sw, sl, sp = int((cm > 0).sum()), int((cm < 0).sum()), int((cm == 0).sum())
    u = d[d.total_line.notna() & ((1 - d.p_over_emp) >= UNDER_P)]
    ud = u.total - u.total_line
    uw, ul, up = int((ud < 0).sum()), int((ud > 0).sum()), int((ud == 0).sum())
    return {"spread4": f"{sw}-{sl}" + (f"-{sp}" if sp else ""), "spread4_units": round(sw - VIG * sl, 1), "spread4_pct": round(sw / max(sw + sl, 1), 3),
            "under55": f"{uw}-{ul}" + (f"-{up}" if up else ""), "under55_units": round(uw - VIG * ul, 1)}


def score_all(pred: pd.DataFrame, games: pd.DataFrame, changed: set) -> dict:
    out = {}
    for w, seasons in WINDOWS.items():
        r = common_score(pred, seasons)
        r = {k: r[k] for k in ("team_mae", "margin_mae", "total_mae", "ats4", "n")}
        r.update(bet_records(pred, games, seasons))
        d = B.join(pred, games)
        d = d[(d.game_type == "REG") & d.season.isin(seasons) & d.game_id.isin(changed)]
        a = B.join(pred, games); a = a[(a.game_type == "REG") & a.season.isin(seasons)]
        r["margin_mae_ridge"] = round(float((a.home_exp_ridge - a.away_exp_ridge - a.result).abs().mean()), 4)   # the ridge equation alone (no trees): less refit noise
        r["n_fixed_games"] = int(len(d)); r["margin_mae_fixed_games"] = round(float(d.margin_err.abs().mean()), 3) if len(d) else np.nan
        out[w] = r
    return out


def run_models(games, L, qb, tg):
    ck = os.path.join(SCR, "trees_cache.parquet")
    if not os.path.exists(ck):   # seed the scratch cache with the live one (keyed by the fit's inputs, so a stale key is never read)
        seeds = [OUT / "trees_cache.parquet"] + [x for x in os.environ.get("QBFIX_SEED", "").split(":") if x]
        parts = [pd.read_parquet(s) for s in seeds if os.path.exists(s)]
        pd.concat(parts, ignore_index=True).drop_duplicates(["key", "game_id", "team"]).to_parquet(ck, index=False)
    M.TREES_CACHE = type(OUT)(ck); M._TC = {"df": None, "used": set(), "new": []}
    tables = {"listed": games, "first": patch(games, L, "first_qb"), "most": patch(games, L, "most_qb")}
    F = {}
    for k, g in tables.items():
        fp = os.path.join(SCR, f"features_{k}.parquet")
        t = time.time()
        if os.path.exists(fp):
            F[k] = pd.read_parquet(fp)
        else:
            F[k] = M.with_trends(R.build_features(R.DEFAULT, seasons=range(2013, 2026), tg=tg, games=g, qb=qb))
            F[k].to_parquet(fp, index=False)
            RUNTIME[f"build_features {k}"] = round(time.time() - t, 1)
        log(f"features {k}: {len(F[k])} rows")
    # the listed table reproduces today's features_asof (the live file, same seasons)
    live = M.with_trends(pd.read_parquet(OUT / "features_asof.parquet"))
    live = live[live.season.between(2013, 2025)].set_index(["game_id", "team"]).sort_index()
    mine = F["listed"].set_index(["game_id", "team"]).sort_index()
    common_idx = live.index.intersection(mine.index)
    diffs = {c: float(np.nanmax(np.abs(live.loc[common_idx, c].astype(float).values - mine.loc[common_idx, c].astype(float).values)))
             for c in [c for c in M.FEATS if c in live.columns and c in mine.columns] + ["qb_rating", "opp_qb_rating"]}
    log(f"listed features vs features_asof: {len(common_idx)} of {len(live)} rows, largest input difference {max(diffs.values()):.2e}")
    RUNTIME["check vs features_asof: max diff"] = max(diffs.values())

    wf_split = make_split_walk_forward()
    P = {}
    specs = [("base (listed ids, today)", lambda: M.walk_forward(F["listed"], TEST)),
             ("(a) first-dropback QB, every played game", lambda: M.walk_forward(F["first"], TEST)),
             ("(b) most-dropbacks QB, every played game", lambda: M.walk_forward(F["most"], TEST)),
             ("strict: first-dropback QB for earlier games, priced game listed", lambda: wf_split(F["first"], F["listed"], TEST))]
    for i, (name, fn) in enumerate(specs):
        pp = os.path.join(SCR, f"pred_{i}.parquet")
        if os.path.exists(pp):
            P[name] = pd.read_parquet(pp); log(f"read {name}"); continue
        t = time.time(); log(f"walk_forward {name} ...")
        P[name] = fn(); P[name].to_parquet(pp, index=False)
        RUNTIME[f"walk_forward {name}"] = round(time.time() - t, 1); log(f"  done in {time.time() - t:.0f}s")
    # the split walk-forward reproduces the live one when both tables are the same (one season, trees from the cache)
    t = time.time()
    chk = wf_split(F["listed"], F["listed"], [2024])
    b = P["base (listed ids, today)"]; b = b[b.season == 2024].set_index("game_id").loc[chk.game_id]
    RUNTIME["split walk_forward check (max |spread diff|, 2024)"] = float(np.abs(b.model_spread.values - chk.model_spread.values).max())
    log(f"split check: {RUNTIME['split walk_forward check (max |spread diff|, 2024)']:.2e} ({time.time() - t:.0f}s)")
    return F, P


SOURCE_NOTE = """Reading of the sources. The bad ids are in nflverse's schedule file itself (`games.csv`), and they are not derived from nflverse's
play-by-play: the pbp's first dropback (`passer_id`; `passer_player_id` agrees wherever it is filled) names the real starter in every error row.
Two different faults show up:

- **2013-2021 (1-3 a season): the id and the name come from different sources.** In the relief rows the schedule's *name* is the starter and the
  *id* is the QB who threw the most (2017 Wk 17 PHI: name Nick Foles, id Nate Sudfeld; 2015 Wk 17 TEN: Mettenberger / Tanney; 2020 Wk 17 ARI:
  Kyler Murray / Streveler; 2018 Wk 17 GB, 2019 Wk 17 BUF, 2021 Wk 16 CAR the same pattern with name and id both the reliever). These are
  games where the starter left early, and the id follows the passing leader.
- **2022 on, and above all 2024 Weeks 8-18: a pre-game "projected starter" that was never reconciled with who played.** The listed QB took no
  dropback at all. In most rows he is the team's earlier starter or the depth chart's QB1 (a stale chart: Dalton for Carolina after Young
  took the job back, Rudolph for Tennessee after Levis returned, Flacco for Indianapolis around Richardson's benching, DeVito for the Giants
  while Lock started, Minshew / O'Connell swapped for Las Vegas), and in the rest he is the injured starter (the weekly roster already had
  him inactive or on reserve that week: Hurts 2024 Wk 17, Tua 2024 Wk 18, Winston, Daniels 2025 Wks 4 and 8, Young 2025 Wk 8, Tyrod Taylor
  2025 Wk 17). Mariota listed for Washington in Weeks 9-13 of 2024 was the QB who finished Week 7 after Daniels' rib injury. The depth chart is no
  fix: its QB1 matches the first-dropback QB in only 86-96% of team-games in any season 2013-2025."""

INTEGRATE = """### The code change, if the fix is taken anyway (nothing was integrated)

nflmodel/build.py: correct the played games' ids from the play-by-play and keep nflverse's as `*_qb_id_listed`; unplayed games keep the
schedule's announced starter, and `ratings.build_features` needs no change (its `last_qb` then comes from the corrected played games).

```python
def first_dropback_qb(seasons) -> pd.DataFrame:
    \"\"\"(game_id, team, qb_id): the QB on each team's first dropback (passer_id, which also carries scrambles). A passer whose roster
    position is not QB is skipped, so a fake punt or a receiver's trick pass is not a start (if no QB dropped back, the first passer).\"\"\"
    pos = {}
    for s in seasons:
        f = RAW / "rosters" / f"roster_weekly_{s}.parquet"
        if f.exists():
            r = pd.read_parquet(f, columns=["gsis_id", "position"]).dropna().drop_duplicates("gsis_id", keep="last")
            pos.update({(s, g): p for g, p in zip(r.gsis_id, r.position)})
    out = []
    for s in seasons:
        f = RAW / "pbp" / f"play_by_play_{s}.parquet"
        if not f.exists():
            continue
        p = pd.read_parquet(f, columns=["game_id", "play_id", "posteam", "qb_dropback", "passer_id"])
        p = p[p.posteam.notna() & (pd.to_numeric(p.qb_dropback, errors="coerce") == 1) & p.passer_id.notna()].sort_values(["game_id", "play_id"])
        p["posteam"] = p.posteam.replace(TEAM_FIX)
        p["qb"] = [pos.get((s, q), "QB") == "QB" for q in p.passer_id]
        fq = p[p.qb].groupby(["game_id", "posteam"]).passer_id.first()
        fa = p.groupby(["game_id", "posteam"]).passer_id.first()
        out.append(fq.reindex(fa.index).fillna(fa).rename("qb_id").rename_axis(["game_id", "team"]).reset_index())
    return pd.concat(out, ignore_index=True)


def fix_starters(g: pd.DataFrame, seasons) -> pd.DataFrame:
    \"\"\"Played games: the first-dropback QB replaces nflverse's listed id (wrong in 45 team-games 2022-2026, reports/qb_id_fix.md).\"\"\"
    fq = first_dropback_qb(seasons).set_index(["game_id", "team"]).qb_id
    for side in ("home", "away"):
        g[f"{side}_qb_id_listed"] = g[f"{side}_qb_id"]
        new = pd.Series([fq.get((k, t)) for k, t in zip(g.game_id, g[f"{side}_team"])], index=g.index)
        m = g.home_score.notna() & new.notna()
        g.loc[m, f"{side}_qb_id"] = new[m]
    return g

# in __main__, after games = build_games():
    games = fix_starters(games, seasons)
```

In the backtest this is variant (a) for every priced game (a played game's own first dropback); live it is the strict variant (the week being priced
is unplayed and keeps the announced starter). The strict variant in the backtest would also need `build_features` to carry the listed id's rating for
the priced row (e.g. a `qb_rating_listed` column that `walk_forward` swaps in for the test rows), which is more than a data fix."""


def verdict_text(res: pd.DataFrame) -> str:
    b, a, m, st = (res.iloc[i] for i in range(4))
    W = list(WINDOWS)
    d = lambda r, k: ", ".join(f"{w} {r[f'{k}_{w}'] - b[f'{k}_{w}']:+.4f}" for w in W)
    rec = lambda r: ", ".join(f"{w} {r[f'spread4_{w}']} vs {b[f'spread4_{w}']}" for w in W)
    lines = [f"- **Strict (the rule's test): {st.verdict}.** Margin MAE against base: {d(st, 'margin_mae')}; 4+ record: {rec(st)}. "
             f"The ridge equation alone: {d(st, 'margin_mae_ridge')}.",
             f"- **(a) first-dropback QB for every played game: {a.verdict}.** Margin MAE: {d(a, 'margin_mae')}; 4+ record: {rec(a)}.",
             f"- (b) most-dropbacks QB (not a pre-game quantity: it knows who finished the game) margin MAE: {d(m, 'margin_mae')}; 4+ record: {rec(m)}.",
             "",
             "What the numbers say. The fix touches few rows: 64 team-games 2013-2025 change QB under (a) (10 of them in 2014-2018). In the strict version "
             "only training rows move (64 of 7,124, under 1%), and every window moves by less than 0.005 of margin MAE in both directions, the blend and the "
             "ridge alone (no placebo was run, so this is read as refit noise rather than measured against it). On (a)'s 2015-18 loss of 0.012, the 8 "
             "fixed games account for about 0.008 (their miss rises 1.06 points each) and the refit for the rest. The priced game's own id is where (a)'s "
             "effects come from: on the fixed games themselves (the column above) (a) is better on 2019-22 and much better on 2023-25 (43 games), where the "
             "listed QB never played, and worse on the 8 games of 2015-18, which are relief games whose listed id was the reliever who threw most "
             "(e.g. Kizer for Rodgers): the first-dropback QB is the better pre-game guess there, but the game was played by the backup. "
             "So nearly all of (a)'s gain on 2023-25 is the priced game's own id, and the strict version shows no gain.",
             "",
             "Caveat on (a): the first dropback is the announced starter in nearly every game, but not all: a starter benched for the first series "
             "(2016 Wk 13 CAR, Derek Anderson for Newton's dress-code benching), a planned one-series start (2024 Wk 18 NE, Maye before Milton), a "
             "surprise late switch. A handful of team-games in thirteen seasons."]
    return "\n".join(lines)


# ---------------------------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    import json
    rt_file = os.path.join(SCR, "runtimes.json")   # the timings of the stages a rerun reads back from the scratch dir
    if os.path.exists(rt_file):
        RUNTIME.update(json.load(open(rt_file)))
    games = pd.read_parquet(OUT / "games.parquet")
    qb = pd.read_parquet(OUT / "qb_games.parquet")
    tg = pd.read_parquet(OUT / "team_games.parquet")
    t = time.time()
    L, pbp = audit(games)
    RUNTIME["audit"] = round(time.time() - t, 1)
    L.to_parquet(os.path.join(SCR, "audit.parquet"), index=False)
    log(f"audit: {len(L)} played team-games")
    reg = L[L.season <= 2026]
    tab = pd.crosstab(reg.season, reg.kind)
    for c in ["ok", "listed QB took no dropback", "listed QB came in relief", "started, replaced in game", "no play-by-play", "no listed id"]:
        if c not in tab.columns:
            tab[c] = 0
    tab["trick play took the first dropback"] = reg.groupby("season").trick_first.sum()
    tab["listed id != first-dropback QB"] = reg.groupby("season").apply(lambda x: int((x.first_qb.notna() & (x.listed_id != x.first_qb)).sum()))
    tab["first-dropback QB != most-dropbacks QB"] = reg.groupby("season").apply(lambda x: int((x.first_qb.notna() & (x.first_qb != x.most_qb)).sum()))
    tab["team-games"] = reg.groupby("season").size()
    tab = tab[["team-games", "ok", "listed QB took no dropback", "listed QB came in relief", "listed id != first-dropback QB", "started, replaced in game",
               "first-dropback QB != most-dropbacks QB", "trick play took the first dropback", "no play-by-play"]]
    print(tab.to_string(), flush=True)
    if len(sys.argv) > 1 and sys.argv[1] == "audit":
        sys.exit(0)
    bad = L[L.kind.isin(["listed QB took no dropback", "listed QB came in relief"])].copy()
    bad["listed_is_depth_qb1"] = bad.listed_id == bad.depth_qb1
    bad["first_is_depth_qb1"] = bad.first_qb == bad.depth_qb1
    bad["listed_was_prev_starter"] = bad.listed_id == bad.prev_first
    bad["raw_file_same_id"] = bad.raw_id == bad.listed_id
    # whole-sample context: how often the depth chart's QB1 is the first-dropback QB
    dep = L[L.first_qb.notna() & L.depth_qb1.notna()].groupby("season").apply(lambda x: round(float((x.depth_qb1 == x.first_qb).mean()), 3))
    ppid_diff = int((L.first_ppid.notna() & L.first_qb.notna() & (L.first_ppid != L.first_qb) & (L.first_any == L.first_qb)).sum())

    F, P = run_models(games, L, qb, tg)
    changed_a = set(L[L.first_qb.notna() & (L.first_qb != L.listed_id)].game_id)
    rows = []
    for name, pred in P.items():
        r = score_all(pred, games, changed_a)
        rows.append({"variant": name, **{f"{k}_{w}": v for w, d in r.items() for k, v in d.items()}})
        log(f"{name}: " + "; ".join(f"{w} margin {d['margin_mae']} team {d['team_mae']} total {d['total_mae']} 4+ {d['spread4']} u55 {d['under55']}" for w, d in r.items()))
    res = pd.DataFrame(rows)
    base, strict, first = res.iloc[0], res.iloc[3], res.iloc[1]
    pct = lambda s: int(s.split("-")[0]) / max(int(s.split("-")[0]) + int(s.split("-")[1]), 1)
    ok_strict = all(strict[f"margin_mae_{w}"] <= base[f"margin_mae_{w}"] and pct(strict[f"spread4_{w}"]) >= pct(base[f"spread4_{w}"]) for w in WINDOWS)
    ok_a = all(first[f"margin_mae_{w}"] < base[f"margin_mae_{w}"] for w in WINDOWS)
    res["verdict"] = ["base", ("backtest uses (a): margin better on all three" if ok_a else "not used for the backtest: margin not better on all three"), "compared only",
                      ("ADOPTED: margin and 4+ record not worse on any window" if ok_strict else "not adopted: worse on a window")]
    res.to_csv(REP / "qb_id_fix.csv", index=False)
    RUNTIME["total (this run)"] = round(time.time() - T0, 1)
    json.dump({k: v for k, v in RUNTIME.items() if k.startswith(("build_features", "walk_forward", "total (first"))}, open(rt_file, "w"), indent=1)

    # ---- the md ----
    def mdtab(df):
        return df.to_markdown(index=False)
    rule = open(REP / "qb_id_fix.md").read().split("\n## 1. Audit")[0].split("\nResults follow below")[0].split("\nRun ")[0] if (REP / "qb_id_fix.md").exists() else ""
    vt = []
    for _, r in res.iterrows():
        for w in WINDOWS:
            vt.append({"variant": r.variant, "window": w, "team MAE": r[f"team_mae_{w}"], "margin MAE": r[f"margin_mae_{w}"], "total MAE": r[f"total_mae_{w}"],
                       "4+ spread (Wk 1-17)": f"{r[f'spread4_{w}']} ({r[f'spread4_units_{w}']:+.1f}u)", "55%+ under (Wk 1-17)": f"{r[f'under55_{w}']} ({r[f'under55_units_{w}']:+.1f}u)",
                       "4+ all REG weeks": r[f"ats4_{w}"], "margin MAE, ridge alone": r[f"margin_mae_ridge_{w}"], "margin MAE, fixed games": f"{r[f'margin_mae_fixed_games_{w}']} (n={r[f'n_fixed_games_{w}']})"})
    vt = pd.DataFrame(vt)
    lst = bad[["game_id", "team", "kind", "listed_name", "listed_n", "first_qb_name", "most_name", "team_db", "listed_status", "listed_is_depth_qb1", "first_is_depth_qb1", "listed_was_prev_starter", "id_name_disagree"]]
    src_rows = bad[bad.season >= 2022].groupby("season").agg(errors=("game_id", "size"), in_raw_games_csv=("raw_file_same_id", "sum"), listed_is_depth_qb1=("listed_is_depth_qb1", "sum"),
                                                              listed_was_prev_starter=("listed_was_prev_starter", "sum"), listed_started_earlier=("started_earlier_season", "sum"),
                                                              listed_inactive_or_reserve=("listed_status", lambda s: int(s.isin(["INA", "RES", "RSN", "RSR", "PUP", "SUS", "DEV"]).sum()))).reset_index()
    md = [rule.rstrip(), "",
          f"Run {pd.Timestamp.now():%d %b %Y %H:%M}, {RUNTIME['total (this run)']:.0f}s (features and predictions read back from the scratch dir when present; the first full run's timings are under Runtimes). Nothing under nflmodel/, data/processed/, web/ or docs/ was written; the features were rebuilt in memory and the "
          f"trees cache pointed at `{SCR}`.", "",
          "## 1. Audit: the listed starter against who actually dropped back, 2013-2026", "",
          "Every played team-game (regular season and playoffs). The first-dropback QB is the passer (`passer_id`, which also carries scrambles) on the team's first dropback "
          "by a player whose roster position is QB; the most-dropbacks QB counts every dropback. 'Listed QB came in relief' = he dropped back, but another QB took the first one. "
          "'Started, replaced in game' is not an error (the listed QB took the first dropback, another QB took more). A trick play (a punter or receiver throwing first) is not "
          "counted as a start.", "", tab.reset_index().to_markdown(index=False), "",
          f"Errors (took no dropback + came in relief): " + ", ".join(f"{s}: {int(v)}" for s, v in (tab['listed QB took no dropback'] + tab['listed QB came in relief']).items()) + ".", "",
          f"`passer_player_id` agrees with `passer_id` on every dropback where both are filled; it is empty on scrambles, so reading the first non-empty `passer_player_id` "
          f"instead gives a different starter in {ppid_diff} team-games; `passer_id` is used.", "",
          "## 2. Where the bad ids come from", "",
          "The ids are nflverse's: `build.py` copies `home_qb_id` / `away_qb_id` straight from `data/raw/schedules/games.csv` (every bad id below is the same in the raw file). "
          "Checks against nflverse's other sources, for the error rows from 2022 on:", "", src_rows.to_markdown(index=False), "",
          "Depth chart QB1 before the game equals the first-dropback QB in this share of team-games (the chart is itself often stale, so it is no fix): "
          + ", ".join(f"{s} {v:.0%}" for s, v in dep.items()) + ".", "",
          SOURCE_NOTE, "",
          "Every error row:", "", mdtab(lst), "",
          "## 3-4. Rebuilt features, walk-forward with the weekly refit, 2015-2025", "",
          "Variants: base = today's inputs (listed ids; reproduces `features_asof.parquet`, largest input difference "
          f"{RUNTIME['check vs features_asof: max diff']:.1e}); (a) every played game carries its first-dropback QB, the priced game included; (b) the most-dropbacks QB; strict = the "
          "fit's training rows carry the first-dropback QB, the priced game keeps the listed id (what the live week sees). Unplayed games are unchanged in all of them "
          "(only the carried-forward starter moves). The QB inputs that move: `qb_rating`, `opp_qb_rating` (not in the equation), `qb_form` (totals equation, `qb_form_sum`). "
          "`qb_out` is built from snap counts and the injury report (trends.py) and does not read the schedule id. "
          f"The split walk-forward reproduces the live one on 2024 when both tables are the same (largest spread difference {RUNTIME['split walk_forward check (max |spread diff|, 2024)']:.1e}).", "",
          "4+ spread and 55%+ under: the postmortem's rules (regular season, Weeks 1-17, -110). '4+ all REG weeks' is `experiments/common.score`'s count. "
          f"'Fixed games': games where either side's listed id differs from its first-dropback QB ({len(changed_a)} games 2013-2026).", "",
          mdtab(vt), "",
          "## Verdict", "", verdict_text(res), "", INTEGRATE, "",
          "## Runtimes", "", "\n".join(f"- {k}: {v}" for k, v in RUNTIME.items()), ""]
    open(REP / "qb_id_fix.md", "w").write("\n".join(md))
    log("DONE")
