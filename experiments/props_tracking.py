"""Round nineteen (29 Sep 2026): player tracking and charting measures on the per-game yards projection. Can NGS and
charting measures, as of before each game, make the adopted rule's yards line (nflmodel/props.py, round 18) more
accurate? No market input; walk-forward, as of only (a weekly row of week w enters only games after week w).

  frame.    props_by_season.build(kind) run once per kind by exec of its module header (props_backtest17.py's pattern),
            cached in CACHE with the per-row pieces the rule used (as-of league rate, touchdown prior, round-13 factor);
            the rule is re-run from those inputs and reproduces build's yds_line to 1e-13 before any variant is scored.
  signals.  receivers: air-yards share (charted plays) as a second volume signal (a literal blend with the target
            share, and his air share over target share against his position's as a ratio); ADOT x catch rate (each
            shrunk toward his position's) as the rate prior; NGS YAC over expected; NGS separation; PFR drops per
            target; a control (his position's yards per target, no player information). rushers: NGS rush yards over
            expected per carry as the prior (and literally: league + RYOE as the prior, and as his rate outright); his
            share of carries inside the 10 on the touchdown prior (Poisson log loss, a side reading). passers: NGS CPOE;
            charted ADOT; NGS time to throw x the opponent's sacks plus QB hits per dropback. Every signal decayed like
            the live usage (DECAY per row, FADE's season factor), shrunk toward the league or position with its own k.
  forms.    a rate signal as a tilt of the prior (league x (1 + c z)) and as a direct factor on the rate (x (1 + c z)),
            z the shrunk deviation over its standard deviation on 2017-18; k and c (or the blend weight) fitted on
            2017-18 by yards MAE; then the best combination by forward selection on 2017-18.
  scores.   yards MAE and volume MAE per player-game on 2019-22 and 2023-25 (2017-18 the fit window, 2019-25 pooled
            beside them), paired standard errors against the rule, tiers of the rule's line; a placebo (the signal
            shuffled within season, refitted, 40 draws) for every variant that passes.
Adoption rule, set before the run: yards MAE lower on both windows, by more than one paired standard error on at least
one, and no tier worse by more than 0.1 yards on either window; of two passing forms of one signal, the lower 2017-18
MAE. Output reports/props_tracking.csv (table = window | tier) and reports/props_tracking.md.
Usage: PYTHONPATH=. python experiments/props_tracking.py build   (the frames, about a minute), then without build (about two)"""
import numpy as np, pandas as pd, pathlib, time, os, sys
from nflmodel import props as PR
from nflmodel.features import OUT, RAW
CACHE = pathlib.Path(os.environ.get("PROPS_TRACK_CACHE", "/tmp/claude-0/-home-user/c1e0d18e-681a-50ba-b0bb-6c809c2e3dee/scratchpad/props_tracking")); CACHE.mkdir(parents=True, exist_ok=True)
T0 = time.time()
def log(*a): print(f"[{time.time() - T0:7.1f}s]", *a, flush=True)
PLAY_COLS = ["game_id", "season", "week", "season_type", "posteam", "defteam", "pass_play", "dropback", "pass_att", "play_type", "receiver_player_id", "rusher_player_id", "passer_player_id",
             "air_yards", "yards_gained", "pass_yds", "complete_pass", "yardline_100", "sack", "qb_hit", "rush_touchdown", "pass_touchdown"]


# ----------------------------------------------------------------------------------------------------------------- build
def build_frames():
    """props_by_season.build(kind) once per kind (the adopted rule with the round-18 rules), plus the per-row pieces the
    rule used and did not keep (the as-of league rate, the touchdown league rate, the position factor, the round-13
    factor), and the charted plays' slim table for the as-of features. Cached in CACHE."""
    src = pathlib.Path(__file__).with_name("props_by_season.py").read_text().split("by_season, by_pos, by_bucket = [], [], []")[0]
    ns = {"__name__": "bys"}; exec(compile(src, "bys", "exec"), ns); log("props_by_season header loaded")
    d, lg_series = ns["d"], ns["lg_series"]
    d[[c for c in PLAY_COLS if c in d.columns]].to_parquet(CACHE / "plays.parquet"); log("plays", len(d))
    for kind in ("rec", "rush", "pass"):
        t1 = time.time(); f, ev = ns["build"](kind); f = f.reset_index(drop=True)
        if kind == "rec":
            t = d[d.pass_play & d.receiver_player_id.notna()]; lgp = d[d.pass_play]
        elif kind == "rush":
            t = d[d.play_type.eq("run") & d.rusher_player_id.notna()]; lgp = t
        else:
            t = d[d.dropback & d.passer_player_id.notna()].assign(yards_gained=lambda x: x.pass_yds); lgp = t
        f["lg"] = lg_series(f, lgp.assign(yards_gained=lgp.yards_gained.fillna(0.0)), "yards_gained", float(lgp.yards_gained.fillna(0.0).mean())).values
        for k, v in ev.items():
            f[f"lgc_{k}"] = lg_series(f, t, v, float(t[v].mean())).values
        f["pos_fac"] = np.array([PR.td_prior(kind, p_, 1.0) for p_ in f.pos]) if kind != "pass" else 1.0
        if kind in PR.INJ_F:
            grp = [PR.inj_group(a_, b_) for a_, b_ in zip(f.report_status, f.practice_status)]
            f["inj"] = np.array([PR.INJ_F[kind].get(g_, 1.0) for g_ in grp]); f["r13"] = f.inj * np.array([1 + PR.SNAP_W[kind] * (PR.snap_ratio(a_, b_) - 1) for a_, b_ in zip(f.s3, f.s10)])
        else:
            f["inj"] = 1.0; f["r13"] = 1.0
        keep = [c for c in f.columns if f[c].dtype != object or c in ("pid", "posteam", "defteam", "game_id", "home_team", "away_team", "pos", "report_status", "practice_status")]
        f[keep].to_parquet(CACHE / f"frame_{kind}.parquet"); log(kind, "frame", len(f), f"{time.time() - t1:.0f}s")


# ------------------------------------------------------------------------------------------------------------ constants
WIN = {"2019-22": (2019, 2022), "2023-25": (2023, 2025)}; FIT = (2017, 2018); ALLW = {"2017-18": FIT, **WIN, "2019-25": (2019, 2025)}   # 2019-25 pooled: a reading beside the rule, not part of it
TIERS = {"rec": [0, 20, 40, 60, 80, 10000], "rush": [0, 20, 40, 60, 80, 10000], "pass": [0, 150, 200, 250, 300, 10000]}
CGRID = np.round(np.arange(-0.50, 0.5001, 0.025), 3)              # the tilt per standard deviation of the signal (fitted on 2017-18)
TDGRID = np.round(np.arange(-0.5, 1.5001, 0.05), 3)                 # the touchdown prior's tilt per unit of relative deviation (1 = in proportion)
AGRID = np.round(np.arange(-0.4, 1.0001, 0.05), 3)                # the volume blend weight (fitted on 2017-18)
KGRID = {"rec": (5, 10, 25, 50, 100, 200), "rush": (5, 10, 25, 50, 100, 200, 400), "pass": (25, 50, 100, 200, 400, 800, 1600)}   # the signal's own shrinkage weight, in its own units (targets, receptions, carries, attempts), decayed
POSG = {"WR": "WR", "TE": "TE", "RB": "RB", "FB": "RB", "HB": "RB"}
TIER_TOL, OUT_CSV, OUT_MD = 0.1, "reports/props_tracking.csv", "reports/props_tracking.md"


# ------------------------------------------------------------------------------------------------ as-of decayed states
def post_states(src, cols, decay, season_f=1.0, team_f=1.0, team_col=None):
    """src: one row per (pid, season, week) with cols. The decayed running sums AFTER each row (the state a later game
    reads), with the round-10 fade applied at a season boundary (and a change of team when team_col is given) between
    rows, as props_by_season.fade_sums carries the live usage. Returns src's keys + key + the sums + last season/team."""
    a = src.sort_values(["pid", "season", "week"]).reset_index(drop=True); vals = a[cols].values.astype(float); res = np.zeros_like(vals)
    pid = a.pid.values; sn = a.season.values; tm = a[team_col].values if team_col else np.zeros(len(a)); run = np.zeros(len(cols)); last = None; ls = lt = None
    for i in range(len(a)):
        if pid[i] != last: run = np.zeros(len(cols)); last = pid[i]; ls = sn[i]; lt = tm[i]
        if sn[i] != ls: run = run * season_f; ls = sn[i]
        if tm[i] != lt: run = run * team_f; lt = tm[i]
        run = decay * run + vals[i]; res[i] = run
    out = a[["pid", "season", "week"]].copy(); out[cols] = res; out["key"] = out.season.astype("int64") * 100 + out.week.astype("int64"); out["s_season"] = out.season
    if team_col: out["s_team"] = a[team_col].values
    return out.drop(columns=["season", "week"])


def lookup(f, st, cols, season_f=1.0, team_f=1.0):
    """The state each frame row reads: the last source row strictly before the game's (season, week), faded when the
    game is in a later season (or for another team) than that row. Missing -> 0."""
    x = f[["pid", "season", "week", "posteam"]].copy(); x["key"] = x.season.astype("int64") * 100 + x.week.astype("int64"); x["_i"] = np.arange(len(x))
    m = pd.merge_asof(x.sort_values("key"), st.sort_values("key"), on="key", by="pid", direction="backward", allow_exact_matches=False).sort_values("_i")
    fac = np.where(m.s_season.notna() & (m.s_season.values < m.season.values), season_f, 1.0)
    if "s_team" in m: fac = fac * np.where(m.s_team.notna() & (m.s_team.values != m.posteam.values), team_f, 1.0)
    return {c: np.nan_to_num(m[c].values.astype(float)) * fac for c in cols}


def asof_ref(f, src, num, den, group=None):
    """The league's (or the group's) ratio sum(num) / sum(den) over last season and this season's weeks before the game,
    for every frame row, as props._asof sees the league. src: rows with season, week (and group)."""
    gcol = [group] if group else []
    g = src.groupby(gcol + ["season", "week"])[[num, den]].sum().reset_index().sort_values(gcol + ["season", "week"]); out = {}
    for gk, gg in (g.groupby(group) if group else [(None, g)]):
        tot = gg.groupby("season")[[num, den]].sum()
        for s_, gs in gg.groupby("season"):
            ps, pn = (tot.loc[s_ - 1, num], tot.loc[s_ - 1, den]) if (s_ - 1) in tot.index else (0.0, 0.0)
            cs, cn = gs[num].cumsum().values, gs[den].cumsum().values; wk = gs.week.values
            out[(gk, int(s_))] = (wk, ps, pn, cs, cn)
    res = np.full(len(f), np.nan); gv = f[group].values if group else [None] * len(f)
    for i, (gk, s_, w_) in enumerate(zip(gv, f.season.values, f.week.values)):
        e = out.get((gk, int(s_)))
        if e is None:
            prev = [v for (g2, s2), v in out.items() if g2 == gk and s2 == int(s_) - 1]
            if prev: wk, ps, pn, cs, cn = prev[0]; res[i] = cs[-1] / cn[-1] if cn[-1] else np.nan
            continue
        wk, ps, pn, cs, cn = e; j = np.searchsorted(wk, w_, side="left") - 1
        a_, b_ = ps + (cs[j] if j >= 0 else 0.0), pn + (cn[j] if j >= 0 else 0.0); res[i] = a_ / b_ if b_ else np.nan
    return res


def shrunk(num, den, k, ref):
    return (num + k * ref) / (den + k)


# ----------------------------------------------------------------------------------------------------------- features
def load():
    F = {k: pd.read_parquet(CACHE / f"frame_{k}.parquet") for k in ("rec", "rush", "pass")}; P = pd.read_parquet(CACHE / "plays.parquet")
    return F, P


def ngs(path, cols):
    x = pd.read_parquet(path); x = x[(x.week > 0) & (x.season_type == "REG") & x.player_gsis_id.notna()].rename(columns={"player_gsis_id": "pid"})
    return x[["pid", "season", "week", "team_abbr"] + cols].drop_duplicates(["pid", "season", "week"])


def features_rec(f, P, posmap):
    """Receivers, as of before each game: from the charted plays (every target since 2016) the air yards, targets with an
    air-yards reading and catches, decayed like the live usage over his games with a target, and the team's air yards
    and targets in the same games (the air-yards share); from NGS weekly (games with 5+ targets) separation (per target)
    and YAC over expected (per catch); from PFR (2018 on) drops per target."""
    sf, tf = PR.FADE["rec"]; t = P[P.pass_play & P.receiver_player_id.notna()].rename(columns={"receiver_player_id": "pid"}).copy()
    t["has_ay"] = t.air_yards.notna().astype(float); t["ay"] = t.air_yards.fillna(0.0); t["comp"] = t.complete_pass.fillna(0.0); t["one"] = 1.0
    team = t.groupby(["game_id", "posteam"]).agg(team_tgt=("one", "sum"), team_ay=("ay", "sum")).reset_index()
    tp = P[P.pass_play].groupby(["game_id", "posteam"]).size().rename("team_pp").reset_index()
    pg = t.groupby(["pid", "posteam", "season", "week", "game_id"]).agg(n=("one", "sum"), n_ay=("has_ay", "sum"), ay=("ay", "sum"), comp=("comp", "sum"), yds=("yards_gained", "sum")).reset_index().merge(team, on=["game_id", "posteam"]).merge(tp, on=["game_id", "posteam"])
    st = post_states(pg, ["n", "n_ay", "ay", "comp", "team_tgt", "team_ay", "team_pp"], PR.DECAY, sf, tf, team_col="posteam")
    S = lookup(f, st, ["n", "n_ay", "ay", "comp", "team_tgt", "team_ay", "team_pp"], sf, tf)
    out = pd.DataFrame(index=f.index)
    out["chk_share"] = np.where(S["team_pp"] > 0, S["n"] / np.where(S["team_pp"] > 0, S["team_pp"], 1), np.nan)   # must equal the frame's n_85 / team_n_85
    with np.errstate(divide="ignore", invalid="ignore"):
        out["tsh"] = S["n"] / S["team_tgt"]; out["ays"] = S["ay"] / S["team_ay"]
    out["posg"] = f.pos.map(POSG).fillna("OTH").values
    pg["posg"] = pg.pid.map(posmap).map(POSG).fillna("OTH")
    out["ref_adot_pos"] = asof_ref(f.assign(posg=out.posg.values), pg, "ay", "n_ay", "posg"); out["ref_catch_pos"] = asof_ref(f.assign(posg=out.posg.values), pg, "comp", "n", "posg")
    out["ref_adot"] = asof_ref(f, pg, "ay", "n_ay"); out["ref_catch"] = asof_ref(f, pg, "comp", "n")
    out["ref_ypt_pos"] = asof_ref(f.assign(posg=out.posg.values), pg, "yds", "n", "posg"); out["ref_ypt"] = asof_ref(f, pg, "yds", "n")
    # the air-yards share over the target share, the position's as of the game (WR 1.2, TE 0.8, RB 0.1): the volume signal relative to his position
    pg["ays_c"] = pg.ay / pg.team_ay.replace(0, np.nan); pg["tsh_c"] = pg.n / pg.team_tgt; pg = pg.dropna(subset=["ays_c"])
    out["ref_ratio_pos"] = asof_ref(f.assign(posg=out.posg.values), pg.assign(ays_c=pg.ays_c.clip(-1, 1)), "ays_c", "tsh_c", "posg")
    out["raw_n"], out["raw_n_ay"], out["raw_ay"], out["raw_comp"] = S["n"], S["n_ay"], S["ay"], S["comp"]
    # NGS receiving
    g = ngs(RAW / "ngs_rec" / "ngs_receiving.parquet", ["avg_separation", "avg_yac_above_expectation", "targets", "receptions"])
    g["sep_w"] = g.avg_separation * g.targets; g["yacoe_w"] = g.avg_yac_above_expectation.fillna(0.0) * g.receptions; g["rec_w"] = np.where(g.avg_yac_above_expectation.notna(), g.receptions, 0.0)
    g["posg"] = g.pid.map(posmap).map(POSG).fillna("OTH")
    st = post_states(g, ["sep_w", "targets", "yacoe_w", "rec_w"], PR.DECAY, sf); S2 = lookup(f, st, ["sep_w", "targets", "yacoe_w", "rec_w"], sf)
    out["sep_num"], out["sep_den"], out["yacoe_num"], out["yacoe_den"] = S2["sep_w"], S2["targets"], S2["yacoe_w"], S2["rec_w"]
    out["ref_sep_pos"] = asof_ref(f.assign(posg=out.posg.values), g, "sep_w", "targets", "posg"); out["ref_yacoe"] = asof_ref(f, g, "yacoe_w", "rec_w")
    # PFR drops (2018 on), per target from the charted plays in the same game
    fr = []
    for s_ in range(2018, 2027):
        p_ = RAW / "pfr_rec" / f"advstats_week_rec_{s_}.parquet"
        if p_.exists(): fr.append(pd.read_parquet(p_, columns=["game_id", "season", "week", "game_type", "pfr_player_id", "receiving_drop"]))
    pf = pd.concat(fr); pf = pf[pf.game_type == "REG"]
    ids = pd.read_parquet(RAW / "players" / "players.parquet", columns=["gsis_id", "pfr_id"]).dropna().drop_duplicates("pfr_id")
    pf = pf.merge(ids, left_on="pfr_player_id", right_on="pfr_id").rename(columns={"gsis_id": "pid"}).merge(pg[["pid", "game_id", "n"]], on=["pid", "game_id"])
    pf["drops"] = pf.receiving_drop.fillna(0.0); pf = pf.drop_duplicates(["pid", "game_id"])
    st = post_states(pf, ["drops", "n"], PR.DECAY, sf); S3 = lookup(f, st, ["drops", "n"], sf)
    out["drop_num"], out["drop_den"] = S3["drops"], S3["n"]; out["ref_drop"] = asof_ref(f, pf, "drops", "n")
    return out


def features_rush(f, P):
    """Rushers: NGS rush yards over expected (per attempt, weighted by attempts; 2018 on, games with 10+ carries), and from
    the charted plays his carries inside the opponent's 10 over all his carries (for touchdowns)."""
    sf, tf = PR.FADE["rush"]; out = pd.DataFrame(index=f.index)
    g = ngs(RAW / "ngs_rush" / "ngs_rushing.parquet", ["rush_yards_over_expected", "rush_attempts"]); g = g[g.rush_yards_over_expected.notna()]
    st = post_states(g, ["rush_yards_over_expected", "rush_attempts"], PR.DECAY, sf); S = lookup(f, st, ["rush_yards_over_expected", "rush_attempts"], sf)
    out["ryoe_num"], out["ryoe_den"] = S["rush_yards_over_expected"], S["rush_attempts"]; out["ref_ryoe"] = asof_ref(f, g, "rush_yards_over_expected", "rush_attempts")
    t = P[P.play_type.eq("run") & P.rusher_player_id.notna()].rename(columns={"rusher_player_id": "pid"}).copy(); t["one"] = 1.0; t["i10"] = (t.yardline_100 <= 10).astype(float)
    pg = t.groupby(["pid", "posteam", "season", "week", "game_id"]).agg(n=("one", "sum"), i10=("i10", "sum")).reset_index()
    st = post_states(pg, ["n", "i10"], PR.DECAY, sf, tf, team_col="posteam"); S = lookup(f, st, ["n", "i10"], sf, tf)
    out["i10_num"], out["i10_den"] = S["i10"], S["n"]; out["ref_i10"] = asof_ref(f, pg, "i10", "n")
    return out


def features_pass(f, P):
    """Passers: NGS completion percentage over expected and time to throw (weighted by attempts, games with 15+ attempts),
    the charted plays' air yards per attempt (ADOT), and the opponent's sacks plus QB hits per dropback faced over its
    last 17 games (the pressure rate; charted pressure is only in the 2025 plays)."""
    out = pd.DataFrame(index=f.index)
    g = ngs(RAW / "ngs" / "ngs_passing.parquet", ["completion_percentage_above_expectation", "avg_time_to_throw", "attempts"]); g = g[g.completion_percentage_above_expectation.notna()]
    g["cpoe_w"] = g.completion_percentage_above_expectation * g.attempts; g["ttt_w"] = g.avg_time_to_throw * g.attempts
    st = post_states(g, ["cpoe_w", "ttt_w", "attempts"], PR.DECAY); S = lookup(f, st, ["cpoe_w", "ttt_w", "attempts"])
    out["cpoe_num"], out["ttt_num"], out["ngs_den"] = S["cpoe_w"], S["ttt_w"], S["attempts"]; out["ref_cpoe"] = asof_ref(f, g, "cpoe_w", "attempts"); out["ref_ttt"] = asof_ref(f, g, "ttt_w", "attempts")
    t = P[P.pass_att.fillna(False).astype(bool) & P.passer_player_id.notna()].rename(columns={"passer_player_id": "pid"}).copy(); t["has_ay"] = t.air_yards.notna().astype(float); t["ay"] = t.air_yards.fillna(0.0)
    pg = t.groupby(["pid", "posteam", "season", "week", "game_id"]).agg(n_ay=("has_ay", "sum"), ay=("ay", "sum")).reset_index()
    st = post_states(pg, ["ay", "n_ay"], PR.DECAY, team_col="posteam"); S = lookup(f, st, ["ay", "n_ay"])
    out["adot_num"], out["adot_den"] = S["ay"], S["n_ay"]; out["ref_adot"] = asof_ref(f, pg, "ay", "n_ay")
    db = P[P.dropback.fillna(False).astype(bool)].copy(); db["pr"] = ((db.sack.fillna(0) > 0) | (db.qb_hit.fillna(0) > 0)).astype(float); db["one"] = 1.0
    dg = db.groupby(["defteam", "season", "week", "game_id"]).agg(pr=("pr", "sum"), db=("one", "sum")).reset_index().sort_values(["defteam", "season", "week"])
    for c in ("pr", "db"): dg[f"p_{c}"] = dg.groupby("defteam")[c].transform(lambda s: s.rolling(17, min_periods=1).sum().shift(1))
    m = f[["defteam", "game_id"]].merge(dg[["defteam", "game_id", "p_pr", "p_db"]], on=["defteam", "game_id"], how="left")
    out["opp_pr"] = (m.p_pr / m.p_db.replace(0, np.nan)).values; out["ref_pr"] = asof_ref(f, dg, "pr", "db")
    return out


# --------------------------------------------------------------------------------------------------------------- rule
class Rule:
    """The live rule after the inputs, on one kind's frame: rate = (his yards + K x prior) / (touches + K) x the defense
    x the wind [x a direct factor]; mean = volume x rate; line = MED_TIER / MED factor x mean; the round-6 team
    reconciliation over the frame's players of the team-game; the round-13 injury and snap factor. With the league's
    as-of rate as the prior, the base volume and no direct factor it reproduces props_by_season.build's yds_line."""

    def __init__(self, kind, f):
        self.kind, self.f = kind, f; self.K, self.W = PR.K[kind], PR.W[kind]; b = PR.GS[kind]
        self.codes = pd.factorize(f.game_id.astype(str) + "|" + f.posteam.astype(str))[0]; self.ngrp = self.codes.max() + 1
        lg = f.lg.values; dr = f.d_rate.values; self.lg = lg
        self.dadj = np.where(~np.isnan(dr), 1 + self.W * (dr / lg - 1), 1.0); self.wind = 1 + PR.WIND_C[kind] * np.maximum(f.wind.values - 10, 0)
        fy = PR.TEAM_FIT[kind]["yds"]; self.exp_y = fy[0] + fy[1] * f.exp_pts.values.astype(float); self.ok = ~np.isnan(f.exp_pts.values.astype(float)); self.wy = PR.RECON_W[kind]["yds"]
        self.r13 = f.r13.values; self.yds, self.n, self.vol = f.yds.values.astype(float), f.n.values.astype(float), f.vol.values.astype(float)
        team_pg = f.tv.values / f.tgames.values
        if kind == "pass": team_pg = (1 - PR.PACE["pass"]) * team_pg + PR.PACE["pass"] * f.a_tdb.values / f.agames.values
        if kind == "rush" and PR.PACE["rush"]: team_pg = (1 - PR.PACE["rush"]) * team_pg + PR.PACE["rush"] * f.a_tr.values / f.agames.values
        self.tplays = team_pg + b[0] + b[1] * f.me.values + b[2] * f.tc.values
        with np.errstate(divide="ignore", invalid="ignore"): self.share_y = np.where(self.tplays > 0, self.vol / self.tplays, 0.0)

    def recon(self, line, exp, w):
        s = np.bincount(self.codes, weights=line, minlength=self.ngrp)[self.codes]
        with np.errstate(divide="ignore", invalid="ignore"): scale = np.clip(exp / np.where(s == 0, np.nan, s), 0.5, 2.0)
        return np.where(self.ok & ~np.isnan(scale), line * (1 + w * (scale - 1)), line)

    def yards(self, vol=None, prior=None, mult=None, own=None):
        vol = self.vol if vol is None else vol; prior = self.lg if prior is None else prior
        mean = vol * ((self.yds + self.K * prior) / (self.n + self.K) if own is None else own) * self.dadj * self.wind
        if mult is not None: mean = mean * mult
        line = PR.med_factor(self.kind, mean) * mean
        return self.recon(line, self.exp_y, self.wy) * self.r13

    def td(self, prior_tilt=None):
        """The touchdown line (rushing): touchdown volume x his rate shrunk toward the league's x his position's factor
        [x the tilt], x the margin, then the team reconciliation on touchdowns (props_by_season.build)."""
        f, kind = self.f, self.kind; pri = f.lgc_td.values * f.pos_fac.values
        if prior_tilt is not None: pri = pri * prior_tilt
        mu = f.vol_td.values * (f.td.values + PR.K_TD[kind] * pri) / (self.n + PR.K_TD[kind]) * (1 + PR.TD_MARGIN[kind] * f.me.values)
        ft = PR.TEAM_FIT[kind]["td"]; mu = self.recon(mu, ft[0] + ft[1] * f.exp_pts.values.astype(float), PR.RECON_W[kind]["td"])
        return mu * (f.inj.values if kind in PR.INJ_TD else 1.0)


def pll_rows(mu, k):
    from scipy.special import gammaln
    mu = np.clip(mu, 1e-3, None); return mu - k * np.log(mu) + gammaln(k + 1)


# ------------------------------------------------------------------------------------------------------------ signals
# Each signal is (form, fn(X, k) -> raw deviation per row). form "vol": a volume signal; "rate": a rate signal tested two
# ways, as a tilt of the prior the player's own rate is shrunk toward (prior = league x (1 + c x z)) and as a direct factor
# on the rate (x (1 + c x z)); "td": a tilt of the touchdown prior. z is the deviation over its standard deviation on the
# fit window's rows; k (the signal's own shrinkage toward the league / position) and c are chosen on 2017-18.
def _dev(num, den, k, ref):
    bad = np.isnan(ref); ref = np.nan_to_num(ref); return np.where(bad, 0.0, shrunk(num, den, k, ref) - ref)   # no reference yet (no data of the kind): no signal


def signals(kind):
    if kind == "rec":
        def ays_blend(X, k):   # the air-yards share (in the share's units: pass plays), shrunk toward his target share with k targets, minus the share behind the line
            conv = np.where(X.tsh > 0, X.chk_share / X.tsh, 0.0); ays = np.nan_to_num(X.ays.values) * conv
            w = X.raw_n_ay.values / (X.raw_n_ay.values + k); return np.nan_to_num(w * (ays - X.chk_share.values))
        def ays_ratio(X, k):   # the air-yards share over the target share (his ADOT over his team's), over his position's, shrunk with k targets: log
            r = np.where((X.tsh > 0) & (X.ays.notna()), X.ays / X.tsh.replace(0, np.nan), np.nan); ref = X.ref_ratio_pos.values
            rs = shrunk(np.nan_to_num(r) * X.raw_n_ay.values, X.raw_n_ay.values, k, ref); return np.nan_to_num(np.log(np.clip(rs / ref, 0.25, 4.0)))
        def adot_catch(X, k):  # ADOT x catch rate, each shrunk toward his position's with k targets, over the league's: ratio - 1
            a = shrunk(X.raw_ay.values, X.raw_n_ay.values, k, X.ref_adot_pos.values); c = shrunk(X.raw_comp.values, X.raw_n.values, k, X.ref_catch_pos.values)
            return np.nan_to_num(a * c / (X.ref_adot.values * X.ref_catch.values) - 1)
        def pos_ypt(X, k):     # control: his position's yards per target over the league's (no player information)
            return np.nan_to_num(X.ref_ypt_pos.values / X.ref_ypt.values - 1)
        return {"air_share_blend": ("vol", ays_blend), "air_share_ratio": ("vol", ays_ratio), "adot_x_catch": ("rate", adot_catch), "pos_ypt_control": ("rate", pos_ypt),
                "yac_over_exp": ("rate", lambda X, k: _dev(X.yacoe_num.values, X.yacoe_den.values, k, X.ref_yacoe.values)),
                "separation": ("rate", lambda X, k: _dev(X.sep_num.values, X.sep_den.values, k, X.ref_sep_pos.values)),
                "drop_rate": ("rate", lambda X, k: _dev(X.drop_num.values, X.drop_den.values, k, X.ref_drop.values))}
    if kind == "rush":
        return {"ryoe": ("rate", lambda X, k: _dev(X.ryoe_num.values, X.ryoe_den.values, k, X.ref_ryoe.values)),
                "inside10_share": ("td", lambda X, k: np.nan_to_num(shrunk(X.i10_num.values, X.i10_den.values, k, np.nan_to_num(X.ref_i10.values)) / X.ref_i10.values - 1))}
    def ttt_pr(X, k):
        zt = _dev(X.ttt_num.values, X.ngs_den.values, k, X.ref_ttt.values); zp = np.nan_to_num(X.opp_pr.values - X.ref_pr.values); return zt * zp
    return {"cpoe": ("rate", lambda X, k: _dev(X.cpoe_num.values, X.ngs_den.values, k, X.ref_cpoe.values)),
            "adot": ("rate", lambda X, k: _dev(X.adot_num.values, X.adot_den.values, k, X.ref_adot.values)),
            "ttt_x_opp_pressure": ("rate_direct", ttt_pr)}


LIT = {"adot_x_catch": ["prior_lit"], "ryoe": ["prior_lit", "rate_lit"]}   # the literal forms asked for: ADOT x catch rate over the league's as the prior (league x ratio); league + RYOE per carry as the prior, and as his rate outright
LIT_ADD = {"ryoe"}   # additive signals: z = deviation / league rate


# ---------------------------------------------------------------------------------------------------------- variants
def apply(R, X, specs):
    """specs: list of (signal, form, k, c, z) -> (vol, prior, mult) for Rule.yards. form: vol_blend (share + c x dev),
    vol_ratio (vol x exp(c x z)), prior (league x (1 + c x z)), direct (rate x (1 + c x z)); z standardized for rates."""
    vol, prior, mult, own = R.vol.copy(), None, None, None; ptilt = np.zeros(len(R.vol)); dtilt = np.zeros(len(R.vol))
    for sig, form, k, c, z in specs:
        if form == "vol_blend": vol = np.maximum(vol + c * z * R.tplays, 0.0)
        elif form == "vol_ratio": vol = vol * np.exp(c * z)
        elif form == "prior": ptilt = ptilt + c * z
        elif form == "direct": dtilt = dtilt + c * z
        elif form == "prior_lit": ptilt = ptilt + z   # z = the unstandardized relative deviation: prior = league x (1 + z)
        elif form == "rate_lit": own = R.lg * np.clip(1 + z, 0.3, 3.0)   # his own rate replaced by league x (1 + z) (no raw yards per touch)
    if ptilt.any(): prior = R.lg * np.clip(1 + ptilt, 0.3, 3.0)
    if dtilt.any(): mult = np.clip(1 + dtilt, 0.3, 3.0)
    return (vol, prior, mult) if own is None else (vol, prior, mult, own)


def zvals(kind, sig, fn, X, k, fitm, form=None):
    raw = fn(X, k); form0 = signals(kind)[sig][0]
    if form in ("prior_lit", "rate_lit"): return raw / X["_lg"].values if sig in LIT_ADD else raw
    if form0 == "vol" or form0 == "td": return raw
    sd = float(np.std(raw[fitm])) if fitm.any() else 0.0
    if sd <= 1e-12: sd = float(np.std(raw[raw != 0])) if (raw != 0).any() else 1.0
    return raw / sd


def fit_signal(kind, sig, R, X, fitm, act, base_line):
    """Grid over the signal's forms, k and c on 2017-18 (yards MAE; touchdown log loss for a td signal). Returns one best
    spec per form: (form, k, c, fit MAE, sd) and the grid."""
    form0, fn = signals(kind)[sig]; best = {}
    forms = {"vol": ["vol_blend"] if sig.endswith("blend") else ["vol_ratio"], "rate": ["prior", "direct"], "rate_direct": ["direct"], "td": ["td_prior"]}[form0] + LIT.get(sig, [])
    for form in forms:
        grid = AGRID if form.startswith("vol") else ([1.0] if form.endswith("_lit") else (TDGRID if form == "td_prior" else CGRID))
        for k in KGRID[kind]:
            z = zvals(kind, sig, fn, X, k, fitm, form)
            for c in grid:
                if form == "td_prior":
                    mu = R.td(np.clip(1 + c * z, 0.2, 5.0)); loss = float(pll_rows(mu[fitm], R.f.act_td.values[fitm]).mean())
                else:
                    line = R.yards(*apply(R, X, [(sig, form, k, c, z)])); loss = float(np.abs(line[fitm] - act[fitm]).mean())
                if form not in best or loss < best[form][3] - 1e-9 or (abs(loss - best[form][3]) <= 1e-9 and abs(c) < abs(best[form][2])):
                    raw = fn(X, k); sd = float(np.std(raw[fitm])) if form0 not in ("vol", "td") and not form.endswith("_lit") else 1.0
                    best[form] = (form, k, float(c), loss, sd)
    return best


def score_rows(kind, variant, line, vol, R, f, base_line, params, rows, tiers, count=None):
    act, actn = f.act_yds.values.astype(float), f.act_n.values.astype(float); tb = np.digitize(base_line, TIERS[kind][1:-1]); T = TIERS[kind]
    for w, (a, b) in ALLW.items():
        m = f.season.between(a, b).values; e = line[m] - act[m]; dd = np.abs(e) - np.abs(base_line[m] - act[m])
        ev = vol[m] - actn[m]; ddv = np.abs(ev) - np.abs(R.vol[m] - actn[m])
        r = {"stat": f"{kind}_yards", "variant": variant, "window": w, "n": int(m.sum()), "yards_mae": round(float(np.abs(e).mean()), 4), "yards_bias": round(float(e.mean()), 3),
             "yards_diff_vs_rule": round(float(dd.mean()), 4), "yards_se_vs_rule": round(float(dd.std(ddof=1) / np.sqrt(len(dd))), 4),
             "vol_mae": round(float(np.abs(ev).mean()), 4), "vol_diff_vs_rule": round(float(ddv.mean()), 4), "vol_se_vs_rule": round(float(ddv.std(ddof=1) / np.sqrt(len(ddv))), 4), "params": params}
        if count is not None:
            mu, base_mu, k_ = count; l1, l0 = pll_rows(mu[m], k_[m]), pll_rows(base_mu[m], k_[m])
            r.update({"td_ll": round(float(l1.mean()), 5), "td_ll_diff_vs_rule": round(float((l1 - l0).mean()), 5), "td_ll_se_vs_rule": round(float((l1 - l0).std(ddof=1) / np.sqrt(m.sum())), 5)})
        rows.append(r)
        for i in range(len(T) - 1):
            mt = m & (tb == i)
            if mt.sum():
                tiers.append({"stat": f"{kind}_yards", "variant": variant, "window": w, "tier": f"{T[i]}-{T[i + 1]}" if i < len(T) - 2 else f"{T[i]}+", "n": int(mt.sum()),
                              "mae": round(float(np.abs(line[mt] - act[mt]).mean()), 3), "rule_mae": round(float(np.abs(base_line[mt] - act[mt]).mean()), 3),
                              "diff": round(float(np.abs(line[mt] - act[mt]).mean() - np.abs(base_line[mt] - act[mt]).mean()), 3), "bias": round(float((line[mt] - act[mt]).mean()), 3)})


def verdict(rows, tiers, variant, stat):
    o = [r for r in rows if r["variant"] == variant and r["stat"] == stat]; g = {r["window"]: r for r in o}
    better = all(g[w]["yards_diff_vs_rule"] < 0 for w in WIN); sig = any(-g[w]["yards_diff_vs_rule"] > g[w]["yards_se_vs_rule"] for w in WIN)
    worst = max([t["diff"] for t in tiers if t["variant"] == variant and t["stat"] == stat and t["window"] in WIN] or [0.0])
    return better and sig and worst <= TIER_TOL, better, sig, worst


# -------------------------------------------------------------------------------------------------------------- main
def main():
    F, P = load(); log("cache loaded", {k: len(v) for k, v in F.items()})
    from nflmodel.positions import names_by_id
    posmap = {pid: v[1] for pid, v in names_by_id(range(2014, 2027)).items()}
    rows, tiers, fits, checks, combos, KEEP = [], [], [], {}, {}, {}
    for kind in ("rec", "rush", "pass"):
        t1 = time.time(); f = F[kind].reset_index(drop=True)
        X = features_rec(f, P, posmap) if kind == "rec" else (features_rush(f, P) if kind == "rush" else features_pass(f, P)); log(kind, "features", f"{time.time() - t1:.0f}s")
        X["_lg"] = f.lg.values; R = Rule(kind, f); base_line = R.yards(); act = f.act_yds.values.astype(float); fitm = f.season.between(*FIT).values
        checks[f"{kind}_line_repro_maxdiff"] = float(np.nanmax(np.abs(base_line - f.yds_line.values)))
        if kind == "rec": checks["rec_share_state_maxdiff"] = float(np.nanmax(np.abs(X.chk_share.values - (f.n_85 / f.team_n_85.replace(0, np.nan)).values)))
        if kind == "rush": checks["rush_td_repro_maxdiff"] = float(np.nanmax(np.abs(R.td() - f.td_line.values)))
        log(kind, "reproduction", {k: v for k, v in checks.items() if k.startswith(kind)})
        cover = {}
        for c_ in ("sep_den", "yacoe_den", "drop_den", "ryoe_den", "ngs_den", "i10_den", "raw_n_ay", "adot_den"):
            if c_ in X: cover[c_] = {w: round(float((X[c_].values[f.season.between(a, b).values] > 0).mean()), 3) for w, (a, b) in ALLW.items()}
        checks[f"{kind}_coverage"] = cover
        score_rows(kind, "rule", base_line, R.vol, R, f, base_line, "the adopted rule (props_by_season.build)", rows, tiers)
        base_fit = float(np.abs(base_line[fitm] - act[fitm]).mean()); cand = {}
        for sig, (form0, fn) in signals(kind).items():
            t2 = time.time(); best = fit_signal(kind, sig, R, X, fitm, act, base_line)
            for form, (fm, k, c, loss, sd) in best.items():
                z = zvals(kind, sig, fn, X, k, fitm, form); name = f"{sig}[{form}]"
                pstr = (f"k={k} (literal, no c)" if form.endswith("_lit") else f"k={k} c={c:+.3f}" + (f" per sd; sd={sd:.4g}, c per unit={c / sd:+.4g}" if form in ("prior", "direct") else ""))
                if form == "td_prior":
                    mu, mu0 = R.td(np.clip(1 + c * z, 0.2, 5.0)), R.td()
                    score_rows(kind, name, base_line, R.vol, R, f, base_line, pstr, rows, tiers, count=(mu, mu0, f.act_td.values.astype(float)))
                    fits.append({"stat": f"{kind}_td", "signal": sig, "form": form, "k": k, "c": c, "sd": sd, "fit_loss": round(loss, 5), "rule_fit_loss": round(float(pll_rows(mu0[fitm], f.act_td.values[fitm]).mean()), 5)})
                    continue
                a_ = apply(R, X, [(sig, form, k, c, z)]); vol = a_[0]; line = R.yards(*a_)
                score_rows(kind, name, line, vol, R, f, base_line, pstr, rows, tiers)
                fits.append({"stat": f"{kind}_yards", "signal": sig, "form": form, "k": k, "c": c, "sd": sd, "fit_loss": round(loss, 4), "rule_fit_loss": round(base_fit, 4)})
                if loss < base_fit - 1e-6 and not sig.endswith("control") and not form.endswith("_lit") and (sig not in cand or loss < cand[sig][3]): cand[sig] = (form, k, c, loss, z)
            log(kind, sig, {fm: (b[1], b[2], round(b[3], 4)) for fm, b in best.items()}, f"rule fit {base_fit:.4f}", f"{time.time() - t2:.0f}s")
        # the best combination: forward selection on 2017-18 among the signals that beat the rule there, c re-fitted at each step, then one coordinate pass
        specs, cur = [], base_fit
        while True:
            step = None
            for sig, (form, k, c0, loss, z) in cand.items():
                if any(s[0] == sig for s in specs): continue
                grid = AGRID if form.startswith("vol") else CGRID
                for c in grid:
                    line = R.yards(*apply(R, X, specs + [(sig, form, k, c, z)])); l_ = float(np.abs(line[fitm] - act[fitm]).mean())
                    if l_ < cur - 1e-6 and (step is None or l_ < step[1]): step = ((sig, form, k, float(c), z), l_)
            if step is None: break
            specs.append(step[0]); cur = step[1]
        for i in range(len(specs)):
            sig, form, k, _, z = specs[i]; grid = AGRID if form.startswith("vol") else CGRID; bestc = (specs[i][3], cur)
            for c in grid:
                trial = specs[:i] + [(sig, form, k, float(c), z)] + specs[i + 1:]; l_ = float(np.abs(R.yards(*apply(R, X, trial))[fitm] - act[fitm]).mean())
                if l_ < bestc[1] - 1e-6: bestc = (float(c), l_)
            specs[i] = (sig, form, k, bestc[0], z); cur = bestc[1]
        if len(specs) >= 2:
            a_ = apply(R, X, specs); vol = a_[0]; line = R.yards(*a_)
            pstr = "; ".join(f"{s}[{fm}] k={k} c={c:+.3f}" for s, fm, k, c, _ in specs)
            score_rows(kind, "combo", line, vol, R, f, base_line, pstr, rows, tiers); combos[kind] = (pstr, round(cur, 4))
        else:
            combos[kind] = ("fewer than two signals beat the rule on 2017-18: no combination" + (f" (only {specs[0][0]})" if specs else ""), None)
        log(kind, "combo", combos[kind], f"{time.time() - t1:.0f}s"); KEEP[kind] = (R, X, f, base_line)
    o = pd.DataFrame(rows); tt = pd.DataFrame(tiers); pd.concat([o.assign(table="window"), tt.rename(columns={"mae": "yards_mae", "bias": "yards_bias", "diff": "yards_diff_vs_rule"}).assign(table="tier")], ignore_index=True).to_csv(OUT_CSV, index=False)
    V = []
    for (stat, v), g in o.groupby(["stat", "variant"], sort=False):
        if v == "rule": continue
        if "td_ll" in g and g.td_ll.notna().any():
            gg = {r.window: r for r in g.itertuples()}; b_ = all(gg[w].td_ll_diff_vs_rule < 0 for w in WIN); s_ = any(-gg[w].td_ll_diff_vs_rule > gg[w].td_ll_se_vs_rule for w in WIN)
            V.append({"stat": stat.replace("yards", "td"), "variant": v, "better_both": b_, "beyond_1se": s_, "worst_tier_diff": None, "adopt": b_ and s_}); continue
        a_, b_, s_, w_ = verdict(rows, tiers, v, stat); V.append({"stat": stat, "variant": v, "better_both": b_, "beyond_1se": s_, "worst_tier_diff": w_, "adopt": a_})
    V = pd.DataFrame(V); log("verdicts\n" + V.to_string()); log("checks", checks)
    PL = []
    for r in V[V.adopt & V.stat.str.endswith("yards")].itertuples():
        kind = r.stat.split("_")[0]; sig, form = r.variant[:-1].split("["); R, X, f, base_line = KEEP[kind]; t2 = time.time()
        real = float(o[(o.stat == r.stat) & (o.variant == r.variant) & (o.window == "2019-25")].yards_diff_vs_rule.iloc[0])
        PL.append({"stat": r.stat, "variant": r.variant, **placebo(kind, sig, form, R, X, f, base_line, real)}); log("placebo", PL[-1], f"{time.time() - t2:.0f}s")
    checks.update(integration_check(KEEP, V, o)); log("integration", {k: v for k, v in checks.items() if "integration" in k or "live" in k or "scored" in k})
    write_md(o, tt, pd.DataFrame(fits), V, checks, combos, pd.DataFrame(PL))
    print(o.drop(columns=["params"]).to_string()); log("DONE")


# ------------------------------------------------------------------------------------------------ integration check
# The adopted constants as they would go into nflmodel/props.py (TRACK) and the two pieces of code the integration
# needs, written here so they can be checked against the variants scored above before anyone pastes them.
TRACK = {"rec": ("ngs_rec/ngs_receiving.parquet", "avg_yac_above_expectation", "receptions", False, 100.0, "mul", 0.2474),
         "rush": ("ngs_rush/ngs_rushing.parquet", "rush_yards_over_expected", "rush_attempts", True, 5.0, "add", 1.0),
         "pass": ("ngs/ngs_passing.parquet", "completion_percentage_above_expectation", "attempts", False, 25.0, "mul", 0.03743)}


def track_prior(kind, league, dev):
    """props.track_prior: the league rate a player's own rate is shrunk toward, moved by his tracking signal (round 19)."""
    _, _, _, _, _, form, c = TRACK[kind]
    return league + c * dev if form == "add" else league * (1 + c * dev)


def _track_rows(kind):
    path, col, wcol, total, k, _, _ = TRACK[kind]; x = pd.read_parquet(RAW / path)
    x = x[(x.week > 0) & (x.season_type == "REG") & x.player_gsis_id.notna() & x[col].notna()].drop_duplicates(["player_gsis_id", "season", "week"]).copy()
    x["v"] = x[col] if total else x[col] * x[wcol]; x["w"] = x[wcol].astype(float); return x.rename(columns={"player_gsis_id": "pid"})


def tracking_live(kind, season, week):
    """props.tracking (live): player id -> his decayed, shrunk signal minus the league's, as of (season, week): his NGS
    weekly rows before the week, the latest weighted 1 and each earlier one DECAY more, FADE's season factor per season
    boundary (between rows, and between his last row and this season); the league's over last season and this season
    before the week; shrunk toward it with k (TRACK)."""
    x = _track_rows(kind); x = x[(x.season < season) | ((x.season == season) & (x.week < week))]; k = TRACK[kind][4]
    lgr = x[x.season >= season - 1]; ref = float(lgr.v.sum() / lgr.w.sum()) if lgr.w.sum() else 0.0
    sf = PR.FADE.get(kind, (1.0, 1.0))[0]; out = {}
    for pid, g in x.sort_values(["season", "week"], ascending=False).groupby("pid"):
        sn = g.season.values; bnd = np.r_[int(sn[0] < season), (sn[1:] != sn[:-1]).astype(int)].cumsum()
        wts = PR.DECAY ** np.arange(len(g)) * sf ** bnd; num, den = float((g.v.values * wts).sum()), float((g.w.values * wts).sum())
        out[pid] = (num + k * ref) / (den + k) - ref
    return out


def track_dev_frame(kind, f):
    """props_by_season (the backtest): the same deviation for every frame row, as of before its game (the rows' own
    post-row decayed sums, merge_asof strictly before the game's week, the season factor at lookup)."""
    x = _track_rows(kind); k = TRACK[kind][4]; sf = PR.FADE.get(kind, (1.0, 1.0))[0]
    st = post_states(x, ["v", "w"], PR.DECAY, sf); S = lookup(f, st, ["v", "w"], sf); ref = asof_ref(f, x, "v", "w")
    return np.where(np.isnan(ref), 0.0, (S["v"] + k * np.nan_to_num(ref)) / (S["w"] + k) - np.nan_to_num(ref))


def integration_check(KEEP, V, o):
    """The pasted code against the scored variants: the frame deviation reproduces the variant's line, and the live
    function gives the same deviation as the frame for the players of sample weeks."""
    res = {}
    for kind, var in (("rec", "yac_over_exp[prior]"), ("rush", "ryoe[prior_lit]"), ("pass", "cpoe[prior]")):
        R, X, f, base_line = KEEP[kind]; dev = track_dev_frame(kind, f); line = R.yards(prior=track_prior(kind, R.lg, dev)); act = f.act_yds.values
        res[f"{kind}_integration_mae"] = {w: round(float(np.abs(line - act)[f.season.between(a, b).values].mean()), 4) for w, (a, b) in ALLW.items()}
        res[f"{kind}_scored_mae"] = {w: float(o[(o.variant == var) & (o.window == w)].yards_mae.iloc[0]) for w in ALLW}
        mx = 0.0
        for s_, w_ in ((2018, 5), (2019, 9), (2021, 1), (2023, 2), (2025, 14)):
            m = (f.season.values == s_) & (f.week.values == w_); live = tracking_live(kind, s_, w_)
            mx = max(mx, float(np.max(np.abs(np.array([live.get(p_, 0.0) for p_ in f.pid.values[m]]) - dev[m]))) if m.any() else 0.0)
        res[f"{kind}_live_vs_frame_maxdiff"] = mx
    return res


N_PLACEBO = 40


def placebo(kind, sig, form, R, X, f, base_line, real):
    """The same variant with the signal's columns shuffled among the frame's rows of the same season (the player linkage
    broken, the distribution kept), refitted on 2017-18 and judged by the same rule: how often noise passes."""
    rng = np.random.default_rng(7); act = f.act_yds.values.astype(float); fitm = f.season.between(*FIT).values; passes, pooled = 0, []
    cols = [c for c in X.columns if c not in ("_lg", "posg")]; seas = f.season.values
    for i in range(N_PLACEBO):
        idx = np.arange(len(f))
        for s_ in np.unique(seas):
            m = np.where(seas == s_)[0]; idx[m] = rng.permutation(m)
        Xp = X.copy(); Xp[cols] = X[cols].values[idx]
        best = fit_signal(kind, sig, R, Xp, fitm, act, base_line)[form]; _, k, c, _, _ = best
        z = zvals(kind, sig, signals(kind)[sig][1], Xp, k, fitm, form); line = R.yards(*apply(R, Xp, [(sig, form, k, c, z)]))
        ok_w, sig_w, worst = True, False, 0.0; tb = np.digitize(base_line, TIERS[kind][1:-1])
        for w, (a, b) in WIN.items():
            m = f.season.between(a, b).values; dd = np.abs(line[m] - act[m]) - np.abs(base_line[m] - act[m]); d_, se = dd.mean(), dd.std(ddof=1) / np.sqrt(m.sum())
            ok_w &= d_ < 0; sig_w |= -d_ > se
            for t_ in range(len(TIERS[kind]) - 1):
                mt = m & (tb == t_)
                if mt.sum(): worst = max(worst, float(np.abs(line[mt] - act[mt]).mean() - np.abs(base_line[mt] - act[mt]).mean()))
        passes += int(ok_w and sig_w and worst <= TIER_TOL); mp = f.season.between(2019, 2025).values
        pooled.append(float((np.abs(line[mp] - act[mp]) - np.abs(base_line[mp] - act[mp])).mean()))
    return {"draws": N_PLACEBO, "placebo_passes": passes, "real_pooled_diff": round(real, 4), "placebo_pooled_diff_mean": round(float(np.mean(pooled)), 4), "placebo_pooled_diff_min": round(float(np.min(pooled)), 4),
            "p_placebo": round((1 + sum(p_ <= real for p_ in pooled)) / (N_PLACEBO + 1), 3)}


def write_md(o, tt, fits, V, checks, combos, PL):
    L = [MD_HEAD]
    L.append("\n## Checks\n")
    for k, v in checks.items(): L.append(f"- `{k}`: {v}")
    L.append("\n## Results: yards and volume MAE per player-game, paired standard error against the adopted rule\n")
    L.append("diff = variant MAE minus the rule's (negative is better); SE = paired standard error of that difference. 2017-18 is the fit window (k and c chosen there for each form).\n")
    for stat, g in o.groupby("stat", sort=False):
        L.append(f"\n### {stat}\n\n| variant | window | yards MAE | diff | SE | volume MAE | diff | SE | params |\n|---|---|---|---|---|---|---|---|---|")
        for r in g.itertuples():
            L.append(f"| {r.variant} | {r.window} | {r.yards_mae:.3f} | {r.yards_diff_vs_rule:+.4f} | {r.yards_se_vs_rule:.4f} | {r.vol_mae:.3f} | {r.vol_diff_vs_rule:+.4f} | {r.vol_se_vs_rule:.4f} | {r.params if r.variant != 'rule' else ''} |")
        if "td_ll" in g and g.td_ll.notna().any():
            L.append("\nRushing touchdowns (the inside-10 signal; Poisson log loss on the same rows, the touch frame):\n\n| variant | window | log loss | diff | SE |\n|---|---|---|---|---|")
            for r in g[g.td_ll.notna()].itertuples(): L.append(f"| {r.variant} | {r.window} | {r.td_ll:.5f} | {r.td_ll_diff_vs_rule:+.5f} | {r.td_ll_se_vs_rule:.5f} |")
    L.append("\n## Fits on 2017-18 (best k and c per signal and form)\n\n| stat | signal | form | k | c | sd of the deviation | fit loss | rule's fit loss |\n|---|---|---|---|---|---|---|---|")
    for r in fits.itertuples(): L.append(f"| {r.stat} | {r.signal} | {r.form} | {r.k} | {r.c:+.3f} | {r.sd:.4g} | {r.fit_loss} | {r.rule_fit_loss} |")
    L.append("\nCombinations (forward selection on 2017-18 among the signals that beat the rule there):\n")
    for k, (p, l_) in combos.items(): L.append(f"- {k}: {p}" + (f" (fit MAE {l_})" if l_ is not None else ""))
    L.append("\n## Verdict per variant (the rule above)\n\n| stat | variant | better on both windows | beyond one SE on one | worst tier diff (either window) | adopted |\n|---|---|---|---|---|---|")
    for r in V.itertuples(): L.append(f"| {r.stat} | {r.variant} | {r.better_both} | {r.beyond_1se} | {'' if r.worst_tier_diff is None or pd.isna(r.worst_tier_diff) else f'{r.worst_tier_diff:+.3f}'} | {('passes (side reading, log loss)' if r.stat.endswith('_td') else '**passes**') if r.adopt else 'no'} |")
    # tiers of the variants that pass the window test (or, if none, the best variant per stat on 2019-22)
    show = list(V[V.better_both & V.stat.str.endswith("yards")].variant.items())
    if len(PL):
        L.append("\n## Placebo (the signal shuffled within season, refitted on 2017-18, 40 draws)\n\n| stat | variant | placebo passes | real pooled 2019-25 diff | placebo mean | placebo min | p (placebo <= real) |\n|---|---|---|---|---|---|---|")
        for r in PL.itertuples(): L.append(f"| {r.stat} | {r.variant} | {r.placebo_passes} / {r.draws} | {r.real_pooled_diff:+.4f} | {r.placebo_pooled_diff_mean:+.4f} | {r.placebo_pooled_diff_min:+.4f} | {r.p_placebo:.3f} |")
    L.append("\n## Tier check (tiers of the rule's yards line; diff = variant MAE minus the rule's)\n")
    pick = V[V.better_both & V.stat.str.endswith("yards")][["stat", "variant"]].values.tolist()
    if not pick:
        for stat, g in o[(o.window == "2019-22") & (o.variant != "rule")].groupby("stat"): pick.append([stat, g.sort_values("yards_mae").variant.iloc[0]])
        L.append("No variant improved on both windows; shown: the best variant per stat on 2019-22.\n")
    for stat, v in pick:
        g = tt[(tt.stat == stat) & (tt.variant == v)]
        L.append(f"\n{stat} {v}\n\n| window | tier | n | MAE | rule MAE | diff | bias |\n|---|---|---|---|---|---|---|")
        for r in g.itertuples(): L.append(f"| {r.window} | {r.tier} | {r.n} | {r.mae:.3f} | {r.rule_mae:.3f} | {r.diff:+.3f} | {r.bias:+.3f} |")
    L.append(f"\n## Runtime\n\nbuild (props_by_season.build x 3, cached; once): 54s on the shared machine; this scoring run, placebo included: {time.time() - T0:.0f}s.\n")
    L.append(MD_TAIL)
    pathlib.Path(OUT_MD).write_text("\n".join(L) + "\n")


MD_HEAD = """# Props: player tracking and charting measures (29 Sep 2026)

`experiments/props_tracking.py`; rows in `reports/props_tracking.csv` (`table` = window or tier).

**Question.** Can player-level tracking (NGS) and charting measures, as of before each game, make the per-game yards
projection more accurate than the adopted rule (round 18: share x game-script plays, rate shrunk toward the league
with K and moved W toward the defense, MED_TIER, round-6 team reconciliation, round-13 injury and snap factors, PACE
and ABSORB)? No market input anywhere.

**Frame.** `props_by_season.build(kind)` run once per kind (exec of the module header, as `props_backtest17.py` does),
cached: receiving 36,630, rushing 17,788, passing 5,031 player-games 2017-25. The rule is re-run from the frame's
own inputs and reproduces `build`'s `yds_line` to 1e-13 (checks below), so every variant differs from the rule only
by the signal it adds.

**Signals, each as of before the game** (weekly rows of week w enter only games after week w; NGS and PFR rows are
regular season only; a player's rows are decayed DECAY = 0.85 per game with the round-10 season fade, as the live
usage; each shrunk toward the league or his position with its own k chosen on 2017-18):

- receivers: (1) air-yards share (his air yards over the team's, charted plays, every target) as a second volume
  signal: `share + a x (air share - target share)` (literal blend) and `share x (air share / target share over his
  position's)^a`; (2) ADOT x catch rate (each shrunk toward his position's) as the rate prior; (3) NGS YAC over
  expected per catch; (4) NGS separation per target (against his position's); (5) PFR drops per target (2018 on).
  Control: his position's yards per target as the prior (no player information), to separate a position effect from
  the signal.
- rushers: (6) NGS rush yards over expected per carry (2018 on; games with 10+ carries) as the rate prior; (7) his
  share of carries inside the opponent's 10 (for touchdowns, scored on the touchdown line's Poisson log loss).
- passers: (8) NGS CPOE (games with 15+ attempts); (9) ADOT (charted air yards per attempt); (10) NGS time to throw x
  the opponent's pressure rate (sacks plus QB hits per dropback over its last 17; charted pressure exists only in the
  2025 plays).

**Forms.** A rate signal z (the shrunk deviation over its standard deviation on 2017-18) enters two ways: `prior`
(the league rate the player's own rate is shrunk toward becomes league x (1 + c z)) and `direct` (the rate x (1 + c z)).
The literal forms asked for are scored too, with no c: ADOT x catch over the league's as the prior
(`adot_x_catch[prior_lit]`), league + RYOE per carry as the prior (`ryoe[prior_lit]`) and as his rate outright
(`ryoe[rate_lit]`). k and c (or the blend weight a) are chosen on 2017-18 by yards MAE. The combination: forward
selection on 2017-18 among the signals that beat the rule there, weights refitted at each step.

**Scores.** Yards MAE and volume MAE (targets, carries, dropbacks) per player-game, 2019-22 and 2023-25 (2017-18 is
the fit window; 2019-25 pooled is a reading beside the rule), the paired standard error of the difference from the
rule, and the rule's yards-line tiers (0-20 ... 80+; passing 0-150 ... 300+).

## Adoption rule (set before the run)

A variant is adopted only if its yards MAE is lower than the rule's on both 2019-22 and 2023-25, by more than one
paired standard error on at least one of them, and it is not worse than the rule by more than 0.1 yards in any tier
on either window. Where more than one form of the same signal passes, the one with the lower 2017-18 MAE is taken.
The inside-10 touchdown signal cannot move a yards line; it is judged by the same rule on the rushing touchdown
Poisson log loss (no tier test), on this touch frame, as a side reading. A placebo check follows the verdict: each
passing variant is refitted and rescored 40 times with its signal shuffled among the same season's rows (the
player linkage broken), to show how often noise passes the same rule.
"""
MD_TAIL = r'''## Verdict

**Three variants pass the rule, one per stat, each by a few hundredths of a yard or less:**

| stat | variant (constants fitted on 2017-18) | 2019-22 rule -> variant (diff, SE) | 2023-25 rule -> variant (diff, SE) | worst tier | placebo |
|---|---|---|---|---|---|
| receiving yards | YAC over expected as the prior: prior = league x (1 + 0.2474 x (YACOE - league's)), YACOE shrunk with k = 100 catches | 19.131 -> 19.125 (-0.0060, 0.0044) | 18.145 -> 18.144 (-0.0017, 0.0047) | +0.013 | 0 / 40 pass; real beats all 40 |
| rushing yards | RYOE as the prior, literally: prior = league ypc + (RYOE per carry - league's), RYOE shrunk with k = 5 carries | 17.687 -> 17.671 (-0.0155, 0.0072) | 16.968 -> 16.958 (-0.0097, 0.0093) | +0.045 | 8 / 40 pass; real beats all 40 |
| passing yards | CPOE as the prior: prior = league x (1 + 0.03743 x (CPOE - league's)), CPOE shrunk with k = 25 attempts | 56.574 -> 56.564 (-0.0100, 0.0491) | 56.109 -> 56.038 (-0.0715, 0.0649) | +0.033 | 1 / 40 pass; real beats all 40 |

Volume MAE is unchanged by all three (they move the rate, not the volume). The rushing direct form (the rate x (1 +
0.0725 per yard of RYOE over the league's, k = 5)) also passes with a larger gain on both windows (-0.028 / -0.025,
pooled -0.027 against -0.013), but its 2017-18 MAE is higher (18.033 against 18.025), so the tie-break set before the
run takes the literal prior. Where CPOE helps is the backups and spot starters (the 0-150 and 150-200 tiers), whose
few dropbacks leave the league prior most of the weight; the starters' tiers move by 0.03 yards.

**Read it for what it is.** The question was whether tracking and charting measures make the per-game yards
projection more accurate. They barely do: the three that pass change the error by 0.002 to 0.07 yards per
player-game (0.01% to 0.13% of it). Each beat every one of 40 refits of the same variant on a shuffled signal
(pooled 2019-25), so each carries some information. But 22 single-signal yards variants (and two combinations) were
scored, and the rule is loose: two independent windows let a pure-noise variant through about one time in eight,
and the placebo refits passed 10 times in 160 (8 of 40 for the RYOE literal prior, whose paired errors are so
tightly matched that a hundredth of a yard is one standard error). The fit window is thin for these signals: RYOE
and PFR drops start in 2018, so 2017-18 is effectively 2018 for them (22% of rushing rows carry an RYOE reading
there), and the RYOE k = 5 sits at the grid's lower edge (nearly unshrunk). NGS's own
expected-yards and expected-completion models are fitted by NGS on seasons that may include the test windows, a
look-ahead this study cannot remove.

**What lost** (each against the rule, 2019-22 / 2023-25; details in the tables above):
- Air-yards share as a second volume signal: the literal blend (a = 0.25 on the air-yards share) helps 2019-22
  receiving yards (-0.021, 2.8 SE) and nothing on 2023-25 (+0.001), makes targets worse on both (+0.004 / +0.006,
  3-5 SE) and the 80+ tier worse by 0.28 / 0.19 (the stars' targets pulled toward their air yards); the
  position-relative ratio form fits to almost nothing and is worse on both (+0.002 / +0.004).
- ADOT x catch rate as the prior: -0.025 / +0.004 (the fitted tilt), +0.34 / +0.44 literally (league x his ADOT x catch
  rate over the league's: the round-2 lesson again, taking yards per target apart makes it worse). His position's
  yards per target alone, with no player information (the control), gets most of the 2019-22 gain (-0.019 / +0.011).
- Separation: +0.023 / -0.004 (worse on 2019-22 by 3 SE). Drop rate: worse on both. YAC over expected as a direct
  factor: fitted to zero.
- Rushing RYOE as his rate outright (league + RYOE, his yards per carry dropped): +0.19 / +0.14.
- Passing ADOT: +0.14 / -0.01 (prior), +0.10 / -0.06 (direct); CPOE as a direct factor +0.44 / +0.29; time to throw x
  the opponent's pressure rate: fitted to zero.
- Combinations (forward selection on 2017-18): receiving (ADOT x catch, separation, drops, YACOE, air share ratio)
  -0.043 on the fit window, +0.001 / +0.015 after; passing (CPOE direct, ADOT prior) +0.64 / +0.40, fitted to 1,046
  QB-games. Rushing has one yards signal, so no combination; the three passing variants are one per stat and do not
  interact (each moves one kind's line).
- Side reading, touchdowns: the share of his carries inside the 10 as a tilt of the rushing touchdown prior lowers the
  Poisson log loss by 0.00004 / 0.00036 (0.2 / 1.6 SE) on this touch frame, with the tilt at the grid's edge. Round 10
  (B) lost with a yard-line prior; a touchdown change is judged on the active frame (BACKTEST_TD), which this study
  did not build. Not proposed.

## Integration (if taken)

The three pass the rule; the gains are small enough that leaving the rule alone is also defensible, and each adds a
dependency on the weekly NGS pull (a player or week without an NGS row gets 0 deviation, which is the rule as
before). The code below is checked in this script (`integration_check`): the backtest function reproduces the scored
MAE to the fourth decimal (constants rounded to four significant figures) and the live function returns the same
deviation as the backtest for every projected player in five sample weeks (max difference 3e-15).

**nflmodel/props.py**, beside the other round constants (after `SHARE_A_W`):

```python
# round 19 (29 Sep 2026, experiments/props_tracking.py, reports/props_tracking.md): a tracking signal moves the league rate a
# player's own rate is shrunk toward. Receivers: NGS YAC over expected per catch; rushers: NGS rush yards over expected per
# carry (league ypc + his RYOE over the league's); QBs: NGS CPOE. Each from his NGS weekly rows before the week (games the
# NGS pages list: 5+ targets, 10+ carries, 15+ attempts), decayed DECAY per row with FADE's season factor, shrunk toward the
# league's (last season and this season before the week) with k of its own weight. Fitted on 2017-18. Each passed the
# pre-set rule (better on both windows, beyond one paired SE on one, no tier worse by 0.1): receiving 19.131 / 18.145 ->
# 19.125 / 18.144, rushing 17.687 / 16.968 -> 17.671 / 16.958, passing 56.574 / 56.109 -> 56.564 / 56.038.
# Entries: NGS file under RAW, value column, weight column, value is a total (else a per-weight average), k, form, c.
TRACK = {"rec": ("ngs_rec/ngs_receiving.parquet", "avg_yac_above_expectation", "receptions", False, 100.0, "mul", 0.2474),
         "rush": ("ngs_rush/ngs_rushing.parquet", "rush_yards_over_expected", "rush_attempts", True, 5.0, "add", 1.0),
         "pass": ("ngs/ngs_passing.parquet", "completion_percentage_above_expectation", "attempts", False, 25.0, "mul", 0.03743)}


def track_prior(kind: str, league: float, dev: float):
    """The league rate his own rate is shrunk toward, moved by his tracking signal's deviation (round 19)."""
    _, _, _, _, _, form, c = TRACK[kind]
    return league + c * dev if form == "add" else league * (1 + c * dev)


def tracking(season: int, week: int) -> dict:
    """kind -> player id -> his NGS signal (TRACK) decayed and shrunk toward the league's, minus the league's, as of
    (season, week). A player without an NGS row gets nothing (0 in project_game), the rule as before."""
    out = {}
    for kind, (path, col, wcol, total, k, _, _) in TRACK.items():
        f = RAW / path; out[kind] = {}
        if not f.exists():
            continue
        x = pd.read_parquet(f); x = x[(x.week > 0) & (x.season_type == "REG") & x.player_gsis_id.notna() & x[col].notna()].drop_duplicates(["player_gsis_id", "season", "week"])
        x = x[(x.season < season) | ((x.season == season) & (x.week < week))].assign(v=lambda y: (y[col] if total else y[col] * y[wcol]).astype(float), w=lambda y: y[wcol].astype(float))
        lg = x[x.season >= season - 1]; ref = float(lg.v.sum() / lg.w.sum()) if lg.w.sum() > 0 else None
        if ref is None:
            continue
        sf = FADE.get(kind, (1.0, 1.0))[0]
        for pid, g in x.sort_values(["season", "week"], ascending=False).groupby("player_gsis_id"):
            sn = g.season.values; bnd = np.r_[int(sn[0] < season), (sn[1:] != sn[:-1]).astype(int)].cumsum()
            wts = DECAY ** np.arange(len(g)) * sf ** bnd
            out[kind][pid] = ((g.v.values * wts).sum() + k * ref) / ((g.w.values * wts).sum() + k) - ref
    return out
```

in `run()`, after `R, RU, Q, D, V, L = ...`:

```python
TK = tracking(season, week)   # round 19
for kind_, P_ in (("rec", R), ("rush", RU), ("pass", Q)):
    for pid_, p_ in P_.items(): p_["track_dev"] = round(float(TK[kind_].get(pid_, 0.0)), 4)
```

in `project_game`, the three shrinkage lines (the defense move `_toward` keeps the plain league rate):

```python
ypt_s = _shrunk(p["ypt"], p["targets"], track_prior("rec", L["ypt"], p.get("track_dev", 0.0)), K["rec"])
ypc_s = _shrunk(p["ypc"], p["carries"], track_prior("rush", L["ypc"], p.get("track_dev", 0.0)), K["rush"])
ypd_s = _shrunk(p["ypd"], p["dropbacks"], track_prior("pass", L["ypd"], p.get("track_dev", 0.0)), K["pass"])
```

and `BACKTEST` from the next `props_by_season.py` run (this frame: receiving 19.13 / 18.14, rushing 17.67 / 16.96,
passing 56.56 / 56.04). Optionally carry `track_dev` onto the card rows beside `ypt_shrunk` / `ypc_shrunk` /
`ypd_shrunk` as a reading.

**experiments/props_by_season.py**: add the function (before `build`) and, in `build`, the prior:

```python
def track_dev(kind, f):
    """Round 19 (experiments/props_tracking.py): his NGS signal (props.TRACK) as of before each game, decayed like the
    usage (DECAY per row, FADE's season factor per season boundary), shrunk toward the league's as of the game (last
    season and this season before the week) with k, minus the league's; 0 without a league reading."""
    from nflmodel.features import RAW
    path, col, wcol, total, k, _, _ = PR.TRACK[kind]; sf = PR.FADE.get(kind, (1.0, 1.0))[0]
    x = pd.read_parquet(RAW / path); x = x[(x.week > 0) & (x.season_type == "REG") & x.player_gsis_id.notna() & x[col].notna()].drop_duplicates(["player_gsis_id", "season", "week"])
    x = x.assign(pid=x.player_gsis_id, v=(x[col] if total else x[col] * x[wcol]).astype(float), w=x[wcol].astype(float)).sort_values(["pid", "season", "week"]).reset_index(drop=True)
    v, w, pid, sn = x.v.values, x.w.values, x.pid.values, x.season.values; sv, sw = np.zeros(len(x)), np.zeros(len(x)); a = b = 0.0
    for i in range(len(x)):
        if i == 0 or pid[i] != pid[i - 1]: a = b = 0.0
        elif sn[i] != sn[i - 1]: a, b = a * sf, b * sf
        a, b = PR.DECAY * a + v[i], PR.DECAY * b + w[i]; sv[i], sw[i] = a, b
    st = pd.DataFrame({"pid": pid, "s_season": sn, "key": sn.astype("int64") * 100 + x.week.values.astype("int64"), "sv": sv, "sw": sw})
    q = pd.DataFrame({"pid": f.pid.values, "season": f.season.values, "key": f.season.values.astype("int64") * 100 + f.week.values.astype("int64"), "_i": np.arange(len(f))})
    m = pd.merge_asof(q.sort_values("key"), st.sort_values("key"), on="key", by="pid", allow_exact_matches=False).sort_values("_i")
    fac = np.where(m.s_season.notna() & (m.s_season < m.season), sf, 1.0); Sv, Sw = m.sv.fillna(0.0).values * fac, m.sw.fillna(0.0).values * fac
    g = x.groupby(["season", "week"])[["v", "w"]].sum().reset_index(); ref = np.full(len(f), np.nan)
    for s_ in np.unique(f.season.values):
        gp, gs = g[g.season == s_ - 1], g[g.season == s_]; cv, cw = np.r_[0.0, gs.v.cumsum().values], np.r_[0.0, gs.w.cumsum().values]
        mr = f.season.values == s_; j = np.searchsorted(gs.week.values, f.week.values[mr], side="left"); den = gp.w.sum() + cw[j]
        ref[mr] = np.where(den > 0, (gp.v.sum() + cv[j]) / np.where(den > 0, den, 1.0), np.nan)
    return np.where(np.isnan(ref), 0.0, (Sv + k * np.nan_to_num(ref)) / (Sw + k) - np.nan_to_num(ref))
```

```python
# in build(kind), replacing the mean_line line:
prior = PR.track_prior(kind, lg, track_dev(kind, f))   # round 19: the tracking signal moves the prior (props.TRACK)
f["mean_line"] = adj(f.vol * (f.yds + K * prior) / (f.n + K)) * wind
```
'''

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "build":
        build_frames(); log("BUILD DONE")
    else:
        main()
