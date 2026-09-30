"""Price an out player by his usual role, not by last game's snap share (30 Sep 2026), under reports/round3_rule.md.

The live injury inputs (nflmodel/trends.py, injury_table) weigh each player now out by his snap share in the team's
LAST game: off_snap_out / def_snap_out sum those shares, ol_out / off_starters_out / def_starters_out count the ones at
50%+. A starter who also missed last game counts as 0 (this week: WAS's Nick Cross, Sam Cosmi and Laremy Tunsil).
Only off_snap_out and opp_def_snap_out (the opponent's def_snap_out) are in the points equation (model.FEATS); ol_out and
the starter counts are readings the page shows, so they are built and counted here but cannot move a prediction.

Variants: the same out set (Out / Doubtful on the final report, or IR / PUP / suspended etc. on the weekly roster, as
trends.injury_table), the same snap source (nflverse snap counts, keyed to gsis ids exactly as trends.py does), the
same "previous team game" (the team's last game with snap data before this week; last season's final game in Week 1).
Each out player's share on a side is taken over the team's games up to and including that previous game, only games on
this team, only games he played on that side (share > 0):
  current     his share in the previous game (0 if he missed it)                            = the live input
  L3, L4, L8  mean over his last 3 / 4 / 8 games played
  STD         mean over his games played this season to date; last season's if none yet
  MAX_L4      max(current, L4)
  L4_G2/4/8   L4, but only if he played within the team's last 2 / 4 / 8 games (a long-term absence is already out
              of the team's ratings, so his usual share would double count)
Every value is as of before the game (weeks before it, earlier seasons), from a source the weekly run already pulls.

The harness is experiments/situational_game.py's, unchanged: lean_walk_forward (checked there against M.walk_forward
to 1e-9), the seven-model blend (live ridge, five blend ridges, boosted trees) refit before every regular-season week
on every played game since 2013, fresh trees for base and every variant alike (the live trees' cache is neither read
nor written), grading at the closing line with the live flag rules. The total equation carries no snaps-out input, so
its predictions are the base's (read from the base run, not refit). Windows 2015-18, 2019-22, 2023-25; 2026 to date
scored separately (not part of the rule).

Placebo (rule 3): the variant's change to the live values (variant - current, off and def, one row permutation)
shuffled across team-games within each season and added back to the live values (clipped at 0): the same adjustments
landed on the wrong games. 50 draws. A draw beats the variant on a window when its gain in team-points miss is at least
the variant's.

    US_SCRATCH=/path python -m experiments.usual_snaps --stage build|base|real|placebo|report [--jobs 4] [--names A,B]
Writes reports/usual_snaps.csv and reports/usual_snaps.md; everything else goes to US_SCRATCH.
"""
from __future__ import annotations
import os, sys, time, json, argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
SCR = Path(os.environ.get("US_SCRATCH", "/tmp/claude-0/-home-user/c1e0d18e-681a-50ba-b0bb-6c809c2e3dee/scratchpad/usual_snaps"))
SCR.mkdir(parents=True, exist_ok=True)
os.environ["SG_SCRATCH"] = str(SCR / "sg")          # situational_game makes its scratch dir on import; keep it here
import numpy as np, pandas as pd
from nflmodel import model as M, trends as TR
from nflmodel.model import OUT
from experiments import situational_game as SG

ROOT = Path(__file__).resolve().parent.parent
REP = ROOT / "reports"
SG.WINDOWS = {"2015-18": (2015, 2018), "2019-22": (2019, 2022), "2023-25": (2023, 2025), "2026": (2026, 2026)}
RULE_WINDOWS = ["2015-18", "2019-22", "2023-25"]
ALL_WINDOWS = list(SG.WINDOWS)
SEASONS = range(2015, 2027)
BASE_FEATS, BASE_TOTAL = list(M.FEATS), list(M.TOTAL_FEATS)
N_PLACEBO = 50
VARIANTS = ["current", "L3", "L4", "L8", "STD", "MAX_L4", "L4_G2", "L4_G4", "L4_G8"]
LABEL = {"current": "Live: last game's share", "L3": "1. Mean of last 3 games played", "L4": "2. Mean of last 4 games played",
         "L8": "3. Mean of last 8 games played", "STD": "4. Season to date (last season if none)", "MAX_L4": "5. max(last game, last 4 played)",
         "L4_G2": "6a. Last 4 played, only if he played in the team's last 2", "L4_G4": "6b. Last 4 played, only if he played in the team's last 4",
         "L4_G8": "6c. Last 4 played, only if he played in the team's last 8"}
COLS = ["off_snap_out", "def_snap_out", "ol_out", "off_starters_out", "def_starters_out"]
FIX = {"OAK": "LV", "SD": "LAC", "STL": "LA"}


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


# The weekly run rewrites data/processed while a study runs (it did at 16:23 on 30 Sep 2026, between the base and the
# variant runs). So the build stage snapshots what every later stage reads (the games table and the model's prepped
# team rows) into the scratch folder, and every stage reads the snapshot: base, variants and placebo on the same data.
SNAP = SCR / "snapshot"
if (SNAP / "games.parquet").exists():
    SG.GAMES = pd.read_parquet(SNAP / "games.parquet")


# ----------------------------------------------------------------------------------------------- the variant inputs
def _snaps_and_out(seasons):
    """trends.injury_table's snap rows (keyed by gsis id the same way) and out sets, unchanged."""
    from nflmodel.players import load_injuries, load_rosters, NOT_AVAILABLE
    from nflmodel.ids import pfr_ids
    snaps = pd.concat([pd.read_parquet(TR.RAW / "snap_counts" / f"snap_counts_{s}.parquet") for s in seasons
                       if (TR.RAW / "snap_counts" / f"snap_counts_{s}.parquet").exists()], ignore_index=True)
    inj = load_injuries(seasons)
    inj["team"] = inj.team.replace(FIX); snaps["team"] = snaps.team.replace(FIX)
    nmap = {}
    for s_ in seasons:
        f_ = TR.RAW / "rosters" / f"roster_weekly_{s_}.parquet"
        if f_.exists():
            r_ = pd.read_parquet(f_, columns=["season", "team", "gsis_id", "pfr_id", "full_name"]).dropna(subset=["gsis_id"])
            r_["team"] = r_.team.replace(FIX)
            nmap.update({(t_, int(se_), k_): g_ for t_, se_, k_, g_ in zip(r_.team, r_.season, TR._norm(r_.full_name), r_.gsis_id)})
    pmap = pfr_ids()
    inj["key"] = inj.gsis_id
    snaps["key"] = snaps.pfr_player_id.map(pmap)
    miss = snaps.key.isna()
    snaps.loc[miss, "key"] = [nmap.get((t_, int(se_), k_)) for t_, se_, k_ in zip(snaps.team[miss], snaps.season[miss], TR._norm(snaps.player[miss]))]
    inj = inj[inj.report_status.isin(["Out", "Doubtful"])]
    ros = load_rosters(seasons); ros = ros[ros.status.isin(NOT_AVAILABLE)].copy(); ros["key"] = ros.gsis_id
    ros_out = {k: set(g.key) for k, g in ros.groupby(["season", "week", "team"])}
    inj_out = {k: set(g.key) for k, g in inj.groupby(["season", "week", "team"])}
    return snaps, inj_out, ros_out


def build_inputs(seasons=range(2012, 2027)) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Per (game_id, team): the five inputs under every variant, and per (game_id, team, out player) the shares."""
    games = SG.GAMES
    snaps, inj_out, ros_out = _snaps_and_out(seasons)
    snaps = snaps[snaps.key.notna()].copy()
    snaps["off"] = snaps.offense_pct.clip(0, 1).fillna(0.0); snaps["dfn"] = snaps.defense_pct.clip(0, 1).fillna(0.0)
    # a team's games with snap data, in order; each player-row gets the team-game index
    tg = snaps[["team", "season", "week"]].drop_duplicates().sort_values(["team", "season", "week"]).reset_index(drop=True)
    tg["idx"] = tg.groupby("team").cumcount()
    snaps = snaps.merge(tg, on=["team", "season", "week"])
    # one row per (team, idx, key): shares summed as the live code sums a duplicated key; position from the row
    pl = snaps.groupby(["team", "idx", "key"], as_index=False).agg(off=("off", "sum"), dfn=("dfn", "sum"), position=("position", "last"), season=("season", "first"), player=("player", "last"))
    hist = {k: (g.idx.values, g.off.values, g.dfn.values, g.season.values, g.position.values, g.player.values) for k, g in pl.sort_values("idx").groupby(["team", "key"])}
    tgi = {t: (g.season.values, g.week.values) for t, g in tg.groupby("team")}
    long = TR.long_games(games); long = long[long.season.isin(seasons)]
    seas_have = set(zip(snaps.season, snaps.team))
    rows, prow = [], []
    for r in long.itertuples():
        base = {"game_id": r.game_id, "team": r.team, "season": r.season, "week": r.week}
        if (r.season, r.team) not in seas_have or r.team not in tgi:
            rows.append({**base, **{f"{c}__{v}": np.nan for c in COLS for v in VARIANTS}}); continue
        ss, ww = tgi[r.team]
        this = np.where((ss == r.season) & (ww < r.week))[0]
        if len(this):
            p = int(this[-1])
        else:
            last = np.where(ss == r.season - 1)[0]
            p = int(last[-1]) if len(last) else -1        # live: an empty "before", every input 0
        out = inj_out.get((r.season, r.week, r.team), set()) | ros_out.get((r.season, r.week, r.team), set())
        acc = {f"{c}__{v}": 0.0 for c in COLS for v in VARIANTS}
        for key in out:
            h = hist.get((r.team, key))
            if h is None or p < 0:
                continue
            idx, off, dfn, sea, pos, nm = h
            m = idx <= p
            if not m.any():
                continue
            idx, off, dfn, sea, pos = idx[m], off[m], dfn[m], sea[m], pos[m]
            is_ol = pos[-1] in TR.OL_POS
            is_ol_last = bool(idx[-1] == p and pos[-1] in TR.OL_POS)
            sh = {}
            for side, s in (("off", off), ("def", dfn)):
                last = float(s[-1]) if idx[-1] == p else 0.0
                pm = s > 0; ps, pi, pse = s[pm], idx[pm], sea[pm]
                mean_k = lambda k: float(ps[-k:].mean()) if len(ps) else 0.0
                if (pse == r.season).any():
                    std = float(ps[pse == r.season].mean())
                elif (pse == r.season - 1).any():
                    std = float(ps[pse == r.season - 1].mean())
                else:
                    std = 0.0
                l4 = mean_k(4)
                recent = lambda n: bool(len(pi) and pi[-1] > p - n)
                sh[side] = {"current": last, "L3": mean_k(3), "L4": l4, "L8": mean_k(8), "STD": std, "MAX_L4": max(last, l4),
                            "L4_G2": l4 if recent(2) else 0.0, "L4_G4": l4 if recent(4) else 0.0, "L4_G8": l4 if recent(8) else 0.0}
            for v in VARIANTS:
                o, d = sh["off"][v], sh["def"][v]
                acc[f"off_snap_out__{v}"] += o; acc[f"def_snap_out__{v}"] += d
                acc[f"off_starters_out__{v}"] += float(o >= 0.5); acc[f"def_starters_out__{v}"] += float(d >= 0.5)
                acc[f"ol_out__{v}"] += float((is_ol_last if v == "current" else is_ol) and o >= 0.5)
            if max(max(sh["off"].values()), max(sh["def"].values())) > 0:
                prow.append({**base, "key": key, "player": nm[m][-1], "position": pos[-1], "games_since_played": int(p - idx[-1]),
                             **{f"off_{v}": sh["off"][v] for v in VARIANTS}, **{f"def_{v}": sh["def"][v] for v in VARIANTS}})
        rows.append({**base, **acc})
    return pd.DataFrame(rows), pd.DataFrame(prow)


def stage_build():
    t0 = time.time()
    SNAP.mkdir(exist_ok=True)
    SG.GAMES = pd.read_parquet(OUT / "games.parquet"); SG.GAMES.to_parquet(SNAP / "games.parquet", index=False)
    M.prep(M.with_trends(pd.read_parquet(OUT / "features_asof.parquet"))).to_parquet(SNAP / "fp.parquet", index=False)
    pd.read_parquet(OUT / "trends_asof.parquet").to_parquet(SNAP / "trends_asof.parquet", index=False)
    pd.read_parquet(OUT / "pred_v3.parquet").to_parquet(SNAP / "pred_v3.parquet", index=False)
    V, P = build_inputs()
    log("built", V.shape, P.shape, round(time.time() - t0), "s")
    # the live values reproduced?
    tr = pd.read_parquet(SNAP / "trends_asof.parquet")[["game_id", "team"] + COLS]
    j = V.merge(tr, on=["game_id", "team"], how="inner")
    chk = {}
    for c in COLS:
        a, b = j[f"{c}__current"], j[c]
        both_nan = a.isna() & b.isna()
        diff = (a - b).abs()
        chk[c] = {"rows": int(len(j)), "max_abs_diff": float(diff.max()), "rows_differ": int(((diff > 1e-9) | (a.isna() != b.isna())).sum() - 0), "both_nan": int(both_nan.sum())}
    log("current vs trends_asof:", json.dumps(chk))
    (SCR / "build_check.json").write_text(json.dumps(chk, indent=1))
    V.to_parquet(SCR / "variants.parquet", index=False); P.to_parquet(SCR / "players.parquet", index=False)


# ------------------------------------------------------------------------------------------------ the model runs
_W: dict = {}


def _load():
    if not _W:
        from threadpoolctl import threadpool_limits
        _W["tl"] = threadpool_limits(limits=1)
        fp = pd.read_parquet(SNAP / "fp.parquet")
        V = pd.read_parquet(SCR / "variants.parquet")
        # the live table (trends_asof) has no playoff rows (trend_table keeps game_type REG / POST, and playoff games are
        # WC / DIV / CON / SB), so with_trends gives playoff training rows 0; every variant keeps that
        tk = pd.read_parquet(SNAP / "trends_asof.parquet", columns=["game_id", "team"])
        V = V.merge(tk, on=["game_id", "team"], how="inner")
        x = fp[["game_id", "team"]].merge(V, on=["game_id", "team"], how="left")
        assert len(x) == len(fp)
        for c in COLS:
            for v in VARIANTS:
                x[f"{c}__{v}"] = x[f"{c}__{v}"].fillna(0.0)      # with_trends fills a missing injury input with 0
        _W["fp"], _W["X"] = fp, x
        _W["opp_ix"] = pd.MultiIndex.from_arrays([fp.game_id, fp.team])
        _W["G0"] = SG.game_frame(fp)
        _W["G0"]["total_line"] = _W["G0"].index.map(SG.GAMES.set_index("game_id").total_line)
        if (SCR / "base.parquet").exists():
            _W["base"] = pd.read_parquet(SCR / "base.parquet")
    return _W


def _with_values(fp, off, dfn):
    fp = fp.copy()
    fp["off_snap_out"] = off; fp["def_snap_out"] = dfn
    m = pd.Series(dfn, index=pd.MultiIndex.from_arrays([fp.game_id, fp.team]))
    fp["opp_def_snap_out"] = m.reindex(pd.MultiIndex.from_arrays([fp.game_id, fp.opp])).fillna(0.0).values
    return fp


def variant_values(v, seed=None):
    W = _load(); X = W["X"]
    cur_o, cur_d = X["off_snap_out__current"].values, X["def_snap_out__current"].values
    o, d = X[f"off_snap_out__{v}"].values, X[f"def_snap_out__{v}"].values
    if seed is None:
        return o, d
    rng = np.random.default_rng(seed)
    seas = W["fp"].season.values
    perm = np.empty(len(seas), int)
    for s in np.unique(seas):
        ix = np.where(seas == s)[0]; perm[ix] = rng.permutation(ix)
    do, dd = (o - cur_o)[perm], (d - cur_d)[perm]
    return np.clip(cur_o + do, 0, None), np.clip(cur_d + dd, 0, None)


def run_variant(v, seed=None, keep_pred=False) -> dict:
    W = _load(); t0 = time.time()
    o, d = variant_values(v, seed)
    fp = _with_values(W["fp"], o, d)
    P = SG.lean_walk_forward(fp, W["G0"], BASE_FEATS, BASE_TOTAL, seasons=SEASONS, points=True, total=False)
    P = SG.finish(P, W["base"])
    if keep_pred:
        (SCR / "preds").mkdir(exist_ok=True); P.to_parquet(SCR / "preds" / f"{v}.parquet", index=False)
    return {"name": v, "seed": -1 if seed is None else seed, "secs": round(time.time() - t0, 1), **SG.flat(SG.score(P))}


def stage_base():
    """Base = the live inputs, fresh trees, 2015-2026, points and total; checks that fp carries the live values."""
    W = _load(); fp = W["fp"]
    chk = {"off_max_diff": float(np.abs(fp.off_snap_out.values - W["X"]["off_snap_out__current"].values).max()),
           "oppdef_max_diff": float(np.abs(fp.opp_def_snap_out.values - _with_values(fp, W["X"]["off_snap_out__current"].values, W["X"]["def_snap_out__current"].values).opp_def_snap_out.values).max())}
    log("fp live inputs vs rebuilt current:", chk)
    t0 = time.time()
    base = SG.finish(SG.lean_walk_forward(fp, W["G0"], BASE_FEATS, BASE_TOTAL, seasons=SEASONS))
    log("base run", round(time.time() - t0), "s")
    base.to_parquet(SCR / "base.parquet", index=False)
    live = pd.read_parquet(SNAP / "pred_v3.parquet")
    j = base.merge(live[["game_id", "model_spread", "model_total"]], on="game_id", suffixes=("", "_live"))
    chk["fresh_vs_cached_trees_spread_mean"] = float((j.model_spread - j.model_spread_live).abs().mean())
    chk["fresh_vs_cached_trees_spread_max"] = float((j.model_spread - j.model_spread_live).abs().max())
    chk["total_vs_live_max"] = float((j.model_total - j.model_total_live).abs().max())
    (SCR / "base_check.json").write_text(json.dumps(chk, indent=1)); log("check", chk)
    SG._append(SCR / "real.csv", [{"name": "(base)", "seed": -1, "secs": 0.0, **SG.flat(SG.score(base))}])


def stage_real(jobs, names=None):
    from joblib import Parallel, delayed
    path = SCR / "real.csv"; done = SG._done(path)
    todo = [v for v in (names or VARIANTS) if v not in done]
    log("variants to run", todo)
    from experiments.usual_snaps import run_variant as RV
    rows = Parallel(n_jobs=jobs, backend="loky")(delayed(RV)(v, None, True) for v in todo)
    SG._append(path, rows)
    for r in rows:
        log("done", r["name"], r["secs"], "s")


def verdicts(real: pd.DataFrame) -> pd.DataFrame:
    b = real[real.name == "(base)"].iloc[0]; rows = []
    for _, r in real[real.name != "(base)"].iterrows():
        v = {"name": r["name"]}
        for w in ALL_WINDOWS:
            v[f"d_team_{w}"] = r[f"team_mae_{w}"] - b[f"team_mae_{w}"]
            v[f"d_margin_{w}"] = r[f"margin_mae_{w}"] - b[f"margin_mae_{w}"]
            v[f"d_total_{w}"] = r[f"total_mae_{w}"] - b[f"total_mae_{w}"]
            v[f"d_sp_{w}"] = (r[f"sp_w_{w}"] - r[f"sp_l_{w}"]) - (b[f"sp_w_{w}"] - b[f"sp_l_{w}"])
            v[f"d_to_{w}"] = (r[f"to_w_{w}"] - r[f"to_l_{w}"]) - (b[f"to_w_{w}"] - b[f"to_l_{w}"])
            v[f"d_ll_{w}"] = r[f"ll_cal_{w}"] - b[f"ll_cal_{w}"]
            v[f"d_brier_{w}"] = r[f"brier_cal_{w}"] - b[f"brier_cal_{w}"]
        v["rule1"] = all(v[f"d_team_{w}"] < 0 and v[f"d_margin_{w}"] < 0 for w in RULE_WINDOWS)
        v["rule2"] = all(v[f"d_sp_{w}"] >= 0 and v[f"d_to_{w}"] >= 0 and v[f"d_ll_{w}"] <= 1e-12 and v[f"d_brier_{w}"] <= 1e-12 for w in RULE_WINDOWS)
        rows.append(v)
    return pd.DataFrame(rows)


def stage_placebo(jobs, names, draws=N_PLACEBO):
    from joblib import Parallel, delayed
    from experiments.usual_snaps import run_variant as RV
    path = SCR / "placebo.csv"
    for v in names:
        have = set(pd.read_csv(path).query("name == @v").seed) if path.exists() else set()
        seeds = [s for s in range(1000, 1000 + draws) if s not in have]
        log("placebo", v, "draws to run", len(seeds))
        for k in range(0, len(seeds), jobs * 2):
            rows = Parallel(n_jobs=jobs, backend="loky")(delayed(RV)(v, s) for s in seeds[k:k + jobs * 2])
            SG._append(path, rows); log("  ", v, "draws done", len(have) + k + len(rows))


def placebo_summary(v, real, pl) -> dict:
    b = real[real.name == "(base)"].iloc[0]; r = real[real.name == v].iloc[0]
    x = pl[pl.name == v] if len(pl) else pl
    if not len(x):
        return {"draws": 0}
    out = {"draws": int(len(x))}
    gain = {w: b[f"team_mae_{w}"] - r[f"team_mae_{w}"] for w in ALL_WINDOWS}
    pg = {w: (b[f"team_mae_{w}"] - x[f"team_mae_{w}"]).values for w in ALL_WINDOWS}
    for w in ALL_WINDOWS:
        out[f"real_beats_{w}"] = int((gain[w] > pg[w]).sum())
    out["real_beats_all3"] = int(sum(all(gain[w] > pg[w][k] for w in RULE_WINDOWS) for k in range(len(x))))
    out["pass"] = bool(out["draws"] >= N_PLACEBO and out["real_beats_all3"] >= 45)
    return out


# ------------------------------------------------------------------------------------------------------------ report
def change_counts() -> pd.DataFrame:
    """Per variant and window: team-games whose off_snap_out or def_snap_out (the inputs the model reads) differ from
    the live value, and the same for ol_out and the starter counts (readings only)."""
    W = _load(); X, fp = W["X"], W["fp"]
    rows = []
    for v in VARIANTS[1:]:
        for w, (a, b) in SG.WINDOWS.items():
            m = fp.season.between(a, b).values
            do = X[f"off_snap_out__{v}"].values[m] - X["off_snap_out__current"].values[m]
            dd = X[f"def_snap_out__{v}"].values[m] - X["def_snap_out__current"].values[m]
            ch = (np.abs(do) > 1e-9) | (np.abs(dd) > 1e-9)
            r = {"name": v, "window": w, "team_games": int(m.sum()), "changed": int(ch.sum()), "changed_by_0.5+": int(((np.abs(do) >= 0.5) | (np.abs(dd) >= 0.5)).sum()),
                 "mean_off_live": float(X["off_snap_out__current"].values[m].mean()), "mean_off_var": float(X[f"off_snap_out__{v}"].values[m].mean()),
                 "mean_def_live": float(X["def_snap_out__current"].values[m].mean()), "mean_def_var": float(X[f"def_snap_out__{v}"].values[m].mean())}
            for c in ["ol_out", "off_starters_out", "def_starters_out"]:
                r[f"{c}_changed"] = int((np.abs(X[f"{c}__{v}"].values[m] - X[f"{c}__current"].values[m]) > 1e-9).sum())
            rows.append(r)
    return pd.DataFrame(rows)


def _fmt_wl(w, l):
    return f"{int(w)}-{int(l)}"


def write_report():
    real = pd.read_csv(SCR / "real.csv").drop_duplicates("name", keep="last")
    pl = pd.read_csv(SCR / "placebo.csv") if (SCR / "placebo.csv").exists() else pd.DataFrame()
    V = verdicts(real).set_index("name"); CC = change_counts()
    b = real[real.name == "(base)"].iloc[0]
    PS = {v: placebo_summary(v, real, pl) for v in VARIANTS[1:] if v in set(real.name)}
    rows = []
    for v in ["(base)"] + [v for v in VARIANTS[1:] if v in set(real.name)]:
        r = real[real.name == v].iloc[0]
        for w in ALL_WINDOWS:
            o = {"variant": v, "label": LABEL.get(v, "Live inputs (base)") if v != "(base)" else "Live: last game's share (base)", "window": w,
                 "games": int(r[f"n_{w}"]), "team_points_miss": round(r[f"team_mae_{w}"], 4), "margin_miss": round(r[f"margin_mae_{w}"], 4),
                 "total_miss": round(r[f"total_mae_{w}"], 4), "spread_flag": _fmt_wl(r[f"sp_w_{w}"], r[f"sp_l_{w}"]),
                 "totals_flag": _fmt_wl(r[f"to_w_{w}"], r[f"to_l_{w}"]), "log_loss_cal": round(r[f"ll_cal_{w}"], 5), "brier_cal": round(r[f"brier_cal_{w}"], 5)}
            if v != "(base)":
                d = V.loc[v]
                o.update({"d_team_points_miss": round(d[f"d_team_{w}"], 4), "d_margin_miss": round(d[f"d_margin_{w}"], 4),
                          "d_spread_wl": int(d[f"d_sp_{w}"]), "d_totals_wl": int(d[f"d_to_{w}"]), "d_log_loss": round(d[f"d_ll_{w}"], 5), "d_brier": round(d[f"d_brier_{w}"], 5)})
                c = CC[(CC.name == v) & (CC.window == w)].iloc[0]
                o.update({"team_games_changed": int(c.changed), "team_games_changed_by_0.5+": int(c["changed_by_0.5+"])})
                p = PS.get(v, {})
                o.update({"placebo_draws": p.get("draws", 0), "placebo_real_beats": p.get(f"real_beats_{w}", ""),
                          "placebo_real_beats_all3": p.get("real_beats_all3", ""),
                          "rule1_accuracy": bool(d.rule1), "rule2_no_bet_cost": bool(d.rule2), "rule3_placebo": p.get("pass", False) if p.get("draws") else "not run"})
            rows.append(o)
    T = pd.DataFrame(rows)
    T.to_csv(REP / "usual_snaps.csv", index=False)
    CC.to_csv(SCR / "change_counts.csv", index=False)
    log("wrote reports/usual_snaps.csv", T.shape)
    return T, V, PS, CC


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", required=True)
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--names", default=None)
    ap.add_argument("--draws", type=int, default=N_PLACEBO)
    a = ap.parse_args()
    names = a.names.split(",") if a.names else None
    if a.stage == "build":
        stage_build()
    elif a.stage == "base":
        stage_base()
    elif a.stage == "real":
        stage_real(a.jobs, names)
    elif a.stage == "placebo":
        stage_placebo(a.jobs, names or [], a.draws)
    elif a.stage == "report":
        write_report()
