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
VARIANTS = ["current", "L3", "L4", "L8", "STD", "MAX_L4", "L4_G2", "L4_G4", "L4_G8", "MAX_L4_G4", "STD_G4"]
LABEL = {"current": "Live: last game's share", "L3": "1. Mean of last 3 games played", "L4": "2. Mean of last 4 games played",
         "L8": "3. Mean of last 8 games played", "STD": "4. Season to date (last season if none)", "MAX_L4": "5. max(last game, last 4 played)",
         "L4_G2": "6a. Last 4 played, only if he played in the team's last 2", "L4_G4": "6b. Last 4 played, only if he played in the team's last 4",
         "L4_G8": "6c. Last 4 played, only if he played in the team's last 8",
         "MAX_L4_G4": "6d. max(last game, last 4 played), the usual part only if he played in the team's last 4",
         "STD_G4": "6e. Season to date, only if he played in the team's last 4"}
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
                            "L4_G2": l4 if recent(2) else 0.0, "L4_G4": l4 if recent(4) else 0.0, "L4_G8": l4 if recent(8) else 0.0,
                            "MAX_L4_G4": max(last, l4 if recent(4) else 0.0), "STD_G4": std if recent(4) else 0.0}
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
    if not (SNAP / "fp.parquet").exists():
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
                x[f"{c}__{v}"] = x[f"{c}__{v}"].fillna(0.0).round(9)   # with_trends fills a missing injury input with 0; rounded (see RND)
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
    return np.round(np.clip(cur_o + do, 0, None), 9), np.round(np.clip(cur_d + dd, 0, None), 9)


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


# The rule's base is the "current" run: the live values rebuilt by this script's code and rounded to 9 decimals like
# every variant, run through the same path. The "(base)" run (the live table's values as the model reads them) differs
# from it only in last-digit float noise, which still moves the boosted trees' bins; it is kept as a reading of that noise.
BASE = "current"


def verdicts(real: pd.DataFrame) -> pd.DataFrame:
    b = real[real.name == BASE].iloc[0]; rows = []
    for _, r in real[~real.name.isin(["(base)", BASE])].iterrows():
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
    b = real[real.name == BASE].iloc[0]; r = real[real.name == v].iloc[0]
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


def sanity() -> dict:
    """The readings the report quotes: this week's WAS game, 2025's missed 90%+ starters, the biggest movers."""
    W = _load(); X, fp = W["X"], W["fp"]
    Pl = pd.read_parquet(SCR / "players.parquet")
    pr = {v: pd.read_parquet(SCR / "preds" / f"{v}.parquet").set_index("game_id") for v in VARIANTS if (SCR / "preds" / f"{v}.parquet").exists()}
    out = {}
    g = "2026_04_IND_WAS"
    w = Pl[(Pl.game_id == g) & (Pl.team == "WAS")]
    out["was_players"] = w[["player", "position", "games_since_played", "off_current", "off_L4", "off_L4_G4", "off_L4_G8", "def_current", "def_L4", "def_L4_G4", "def_L4_G8"]]
    m = ((fp.game_id == g) & (fp.team == "WAS")).values
    out["was_inputs"] = pd.DataFrame([{"variant": v, "WAS off_snap_out": float(X.loc[m, f"off_snap_out__{v}"].iloc[0]), "WAS def_snap_out": float(X.loc[m, f"def_snap_out__{v}"].iloc[0]),
                                       "model spread (WAS)": float(pr[v].loc[g, "model_spread"]) if v in pr else np.nan} for v in VARIANTS])
    x = Pl[(Pl.season == 2025) & (Pl.week <= 18) & (Pl.games_since_played >= 1)].copy()
    x["usual"] = np.maximum(x.off_L4, x.def_L4); s_ = x[x.usual >= 0.9]
    out["missed90"] = {"players": int(len(s_)), "team_games": int(s_[["game_id", "team"]].drop_duplicates().shape[0]),
                       "missed_1": int((s_.games_since_played == 1).sum()), "missed_2_3": int(s_.games_since_played.between(2, 3).sum()),
                       "missed_4_7": int(s_.games_since_played.between(4, 7).sum()), "missed_8plus": int((s_.games_since_played >= 8).sum()),
                       **{f"counted_{v}": float((np.maximum(s_[f"off_{v}"], s_[f"def_{v}"]) > 0).mean()) for v in VARIANTS[1:]}}
    out["missed90_examples"] = s_[s_.games_since_played <= 2].sort_values(["week", "team"]).head(12)[["game_id", "team", "player", "position", "games_since_played", "off_L4", "def_L4"]]
    # biggest movers (2015-25 regular season): team-games whose inputs move most under the best gated variant
    best = out["best"] = "L4_G4"
    d = pd.DataFrame({"game_id": fp.game_id, "team": fp.team, "season": fp.season, "game_type": fp.game_type,
                      "off_live": X["off_snap_out__current"], "off_var": X[f"off_snap_out__{best}"], "def_live": X["def_snap_out__current"], "def_var": X[f"def_snap_out__{best}"]})
    d = d[d.season.between(2015, 2025) & (d.game_type == "REG")]
    d["move"] = (d.off_var - d.off_live).abs() + (d.def_var - d.def_live).abs()
    top = d.sort_values("move", ascending=False).head(10).copy()
    def who(r):
        q = Pl[(Pl.game_id == r.game_id) & (Pl.team == r.team)]
        q = q.assign(add=(q[f"off_{best}"] - q.off_current).abs() + (q[f"def_{best}"] - q.def_current).abs()).sort_values("add", ascending=False)
        return ", ".join(f"{a} ({max(o, e):.0%})" for a, o, e in zip(q.player.head(4), q[f"off_{best}"].head(4), q[f"def_{best}"].head(4)) if max(o, e) > 0)
    top["players"] = [who(r) for r in top.itertuples()]
    top["home_spread_move"] = [float(pr[best].loc[gid, "model_spread"] - pr["current"].loc[gid, "model_spread"]) if best in pr else np.nan for gid in top.game_id]
    out["movers"] = top
    sp = {}
    for v in VARIANTS[1:]:
        if v in pr:
            dd = (pr[v].model_spread - pr["current"].model_spread)[pr["current"].season.between(2015, 2025)]
            sp[v] = {"mean_abs": float(dd.abs().mean()), "moved_0.5+": int((dd.abs() >= 0.5).sum()), "games": int(len(dd))}
    out["spread_moves"] = sp
    return out


def _md_table(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for r in df.itertuples(index=False):
        lines.append("| " + " | ".join(str(v) for v in r) + " |")
    return "\n".join(lines)


def write_report():
    real = pd.read_csv(SCR / "real.csv").drop_duplicates("name", keep="last")
    pl = pd.read_csv(SCR / "placebo.csv") if (SCR / "placebo.csv").exists() else pd.DataFrame()
    V = verdicts(real).set_index("name"); CC = change_counts()
    PS = {v: placebo_summary(v, real, pl) for v in VARIANTS[1:] if v in set(real.name)}
    have = [v for v in VARIANTS[1:] if v in set(real.name)]
    rows = []
    for v in [BASE, "(base)"] + have:
        r = real[real.name == v].iloc[0]
        for w in ALL_WINDOWS:
            o = {"variant": v, "label": ("Base: live last-game share, rebuilt (the rule's base)" if v == BASE else
                                         "Reading: live table's own values (float-noise check)" if v == "(base)" else LABEL[v]), "window": w,
                 "games": int(r[f"n_{w}"]), "team_points_miss": round(r[f"team_mae_{w}"], 4), "margin_miss": round(r[f"margin_mae_{w}"], 4),
                 "total_miss": round(r[f"total_mae_{w}"], 4), "spread_flag_wl": _fmt_wl(r[f"sp_w_{w}"], r[f"sp_l_{w}"]),
                 "totals_flag_wl": _fmt_wl(r[f"to_w_{w}"], r[f"to_l_{w}"]), "log_loss_cal": round(r[f"ll_cal_{w}"], 5), "brier_cal": round(r[f"brier_cal_{w}"], 5)}
            if v in V.index:
                d = V.loc[v]; c = CC[(CC.name == v) & (CC.window == w)].iloc[0]; p = PS.get(v, {})
                o.update({"d_team_points_miss": round(d[f"d_team_{w}"], 4), "d_margin_miss": round(d[f"d_margin_{w}"], 4),
                          "d_spread_w_minus_l": int(d[f"d_sp_{w}"]), "d_totals_w_minus_l": int(d[f"d_to_{w}"]),
                          "d_log_loss": round(d[f"d_ll_{w}"], 5), "d_brier": round(d[f"d_brier_{w}"], 5),
                          "team_games_changed": int(c.changed), "team_games_changed_by_0.5+": int(c["changed_by_0.5+"]),
                          "placebo_draws": p.get("draws", 0), "placebo_real_beats_on_window": p.get(f"real_beats_{w}", ""),
                          "placebo_real_beats_all3": p.get("real_beats_all3", ""),
                          "rule1_accuracy": bool(d.rule1), "rule2_no_bet_cost": bool(d.rule2),
                          "rule3_placebo": (bool(p["pass"]) if p.get("draws") else "not run")})
            rows.append(o)
    T = pd.DataFrame(rows); T.to_csv(REP / "usual_snaps.csv", index=False); log("wrote reports/usual_snaps.csv", T.shape)
    S_ = sanity()
    b = real[real.name == BASE].iloc[0]; b0 = real[real.name == "(base)"].iloc[0]
    fmt3 = lambda d, k, nd=4: " / ".join(f"{d[f'{k}_{w}']:+.{nd}f}" for w in RULE_WINDOWS)
    def fails(v):
        d = V.loc[v]; f = []
        bad1 = [w for w in RULE_WINDOWS if d[f"d_team_{w}"] >= 0]; badm = [w for w in RULE_WINDOWS if d[f"d_margin_{w}"] >= 0]
        if bad1: f.append("1: team miss up " + ", ".join(bad1))
        if badm: f.append("1: margin miss up " + ", ".join(badm))
        bs = [w for w in RULE_WINDOWS if d[f"d_sp_{w}"] < 0]; bt = [w for w in RULE_WINDOWS if d[f"d_to_{w}"] < 0]
        bl = [w for w in RULE_WINDOWS if d[f"d_ll_{w}"] > 1e-12 or d[f"d_brier_{w}"] > 1e-12]
        if bs: f.append("2: spread flag down " + ", ".join(bs))
        if bt: f.append("2: totals flag down " + ", ".join(bt))
        if bl: f.append("2: log loss / Brier up " + ", ".join(bl))
        p = PS.get(v, {})
        if p.get("draws"):
            f.append(f"3: beats the placebo on all three windows in {p['real_beats_all3']} of {p['draws']}" + (" (needs 45 of 50)" if not p["pass"] else ""))
        return "; ".join(f) if f else "passes"
    tab = []
    for v in have:
        d = V.loc[v]; p = PS.get(v, {})
        tab.append({"variant": LABEL[v], "team points miss": fmt3(d, "d_team"), "margin miss": fmt3(d, "d_margin"),
                    "spread flag W-L": " / ".join(f"{int(d[f'd_sp_{w}']):+d}" for w in RULE_WINDOWS),
                    "totals flag W-L": " / ".join(f"{int(d[f'd_to_{w}']):+d}" for w in RULE_WINDOWS),
                    "log loss x1000": " / ".join(f"{1000 * d[f'd_ll_{w}']:+.2f}" for w in RULE_WINDOWS),
                    "Brier x1000": " / ".join(f"{1000 * d[f'd_brier_{w}']:+.2f}" for w in RULE_WINDOWS),
                    "placebo (real beats, per window)": (" / ".join(str(p.get(f"real_beats_{w}")) for w in RULE_WINDOWS) + f" of {p['draws']}") if p.get("draws") else "not run",
                    "2026 team miss": f"{d['d_team_2026']:+.4f}", "verdict": "ADOPT" if (d.rule1 and d.rule2 and p.get("pass")) else "no: " + fails(v)})
    tab = pd.DataFrame(tab)
    cc = CC[CC.window != "2026"].groupby("name")[["team_games", "changed", "changed_by_0.5+", "ol_out_changed", "off_starters_out_changed", "def_starters_out_changed"]].sum()
    c25 = CC[CC.window == "2023-25"].set_index("name")
    cct = pd.DataFrame([{"variant": v, "team-games changed (of %d)" % cc.loc[v, "team_games"]: int(cc.loc[v, "changed"]), "changed by 0.5+": int(cc.loc[v, "changed_by_0.5+"]),
                         "mean off_snap_out 2023-25 (live %.2f)" % c25.loc[v, "mean_off_live"]: round(c25.loc[v, "mean_off_var"], 2),
                         "mean |spread move|": round(S_["spread_moves"][v]["mean_abs"], 2), "games moved 0.5+": S_["spread_moves"][v]["moved_0.5+"],
                         "ol_out changed": int(cc.loc[v, "ol_out_changed"]), "off starters changed": int(cc.loc[v, "off_starters_out_changed"]),
                         "def starters changed": int(cc.loc[v, "def_starters_out_changed"])} for v in have])
    base_tab = pd.DataFrame([{"window": w, "games": int(b[f"n_{w}"]), "team points miss": f"{b[f'team_mae_{w}']:.4f}", "margin miss": f"{b[f'margin_mae_{w}']:.4f}",
                              "total miss": f"{b[f'total_mae_{w}']:.4f}", "spread flag": _fmt_wl(b[f"sp_w_{w}"], b[f"sp_l_{w}"]), "totals flag": _fmt_wl(b[f"to_w_{w}"], b[f"to_l_{w}"]),
                              "log loss (cal)": f"{b[f'll_cal_{w}']:.4f}", "Brier (cal)": f"{b[f'brier_cal_{w}']:.4f}"} for w in ALL_WINDOWS])
    m90 = S_["missed90"]
    head = HEADLINE.format(**{k: v for k, v in globals().items() if k.isupper()}) if "{" in HEADLINE else HEADLINE
    md = f"""# Usual snaps: pricing an out player by his usual role (30 Sep 2026)

`experiments/usual_snaps.py`; every variant and window in `reports/usual_snaps.csv`. Rule: `reports/round3_rule.md`.

{head}

## The rule, variant by variant

Each variant replaces the live last-game share in `off_snap_out` and `def_snap_out` (so also the opponent's
`opp_def_snap_out`), the only snaps-out inputs the model reads. Changes against the base, per window 2015-18 / 2019-22 / 2023-25
(misses in points, below zero is better; flag records as the change in wins minus losses; log loss and Brier of the calibrated
win chance, times 1000, below zero is better). Rule 1 here needs both the team points miss and the margin miss lower on all three
windows; rule 2 needs both flag records not worse and log loss and Brier not worse on all three. The totals flag never moves: the
total equation has no snaps-out input. The placebo ran for the four variants that lower the team points miss on every window
(50 draws for the best, 20 for the others, as a reading: none of them passes rule 2, which gates the placebo).

{_md_table(tab)}

Base (the live inputs rebuilt by the script, same code path as every variant, fresh trees):

{_md_table(base_tab)}

## How much each variant changes

Regular and postseason team-games 2015-2025 (the model's rows). "Changed" means `off_snap_out` or `def_snap_out` differs from the live
value. Spread move: the model spread against the base, 2015-25 regular season ({S_['spread_moves'][have[0]]['games']} games).

{_md_table(cct)}

The ungated usual shares (1 to 5) carry every player still on IR or PUP for as long as he stays there, including players hurt a
season or more ago: the average team-game goes from 0.33 of a player's offensive snaps out to about 2. Those players are already out
of the team's ratings (every game they missed is in its EPA and points), so the input double counts, and all five raise the margin
miss on 2019-22 and lose spread wins on every window. Gating at the team's last 4 or 8 games removes most of that and lowers the
team points miss on every window, but still raises the margin miss on 2019-22 and loses spread wins on 2015-18.

## Sanity checks

This week, WAS (home to IND). Out players with any share, and the WAS inputs and model spread (home margin) under each variant:

{_md_table(S_['was_players'].round(2))}

{_md_table(S_['was_inputs'].round(2))}

2025 regular season: {m90['players']} times an out player whose usual share (last 4 games played) was 90%+ had also missed the previous
game, on {m90['team_games']} team-games; the live input counted every one as 0. He had missed 1 game in {m90['missed_1']} of them, 2 to 3 in
{m90['missed_2_3']}, 4 to 7 in {m90['missed_4_7']} and 8 or more in {m90['missed_8plus']}. Share still counted: last 4 gated at 2 games
{m90['counted_L4_G2']:.0%}, at 4 {m90['counted_L4_G4']:.0%}, at 8 {m90['counted_L4_G8']:.0%}; ungated 100%. Examples (missed 1 or 2 games):

{_md_table(S_['missed90_examples'].round(2))}

Biggest movers under {LABEL[S_['best']]} (2015-25 regular season; the players added, at their usual share):

{_md_table(S_['movers'][['game_id', 'team', 'off_live', 'off_var', 'def_live', 'def_var', 'home_spread_move', 'players']].round(2))}

## Caveats

- The rule's base is the live input rebuilt by this script (it matches `trends_asof.parquet` to 1e-15 on all 7,870 team-games) and
  rounded to 9 decimals like every variant. Run straight from the live table, the base differs by last-digit float noise, which
  moves the boosted trees' bins: team points miss {b0['team_mae_2015-18'] - b['team_mae_2015-18']:+.4f} / {b0['team_mae_2019-22'] - b['team_mae_2019-22']:+.4f} / {b0['team_mae_2023-25'] - b['team_mae_2023-25']:+.4f}. That is the noise floor of a single comparison; the gated variants' gains (about 0.004 to 0.02) sit above it
  on 2015-18 and 2023-25 and near it on 2019-22.
- Fresh trees on this machine for base and every variant (the live trees' cache holds GitHub runners' fits; fresh fits move the
  base spread by 0.008 points on average). Weekly refit, 2013 on, as the live walk-forward.
- A player's history counts only games for this team (a player traded in or signed counts 0 until he plays for it), and only games
  with snap data (2012 on). The out set, snap source and id matching are the live ones; nothing new is pulled.
- The gate counts the team's games, across the offseason: in Weeks 1 to 4 a player who last played in the final games of last
  season still counts, including one since retired or released but still listed as unavailable (Aaron Donald, retired, counts
  for LA in 2024 Week 4 above). The ungated variants carry such players all season.
- `ol_out`, `off_starters_out` and `def_starters_out` are not model inputs (only readings on the page), so their changes, counted
  above, cannot move a prediction. `qb_out` was left as it is.
- 2026 is weeks 1 to 3 only ({int(b['n_2026'])} games): a reading, not part of the rule. The gated variants are worse there by 0.02 to 0.03.
- Data snapshot: the weekly run rewrote `data/processed` at 16:23 while the study ran, so every run here reads one snapshot taken
  after it (scratch folder), base and variants alike.
"""
    (REP / "usual_snaps.md").write_text(md); log("wrote reports/usual_snaps.md")
    return T, V, PS, CC


HEADLINE = "(headline written after the runs)"


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
