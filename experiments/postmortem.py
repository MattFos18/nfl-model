"""Postmortem of every bet the model would have made, 2015-2025 walk-forward (pred_v3), plus this season's recorded picks.

Bets: the spread flag (model 4+ points from the closing line, regular season, Weeks 1 to 17) and the totals flag (Under
at a 55%+ raw chance, p_over_emp, same weeks), graded exactly as backtest.grade_spread / picks.record do.

Part 1 decomposes each bet's miss (actual minus the model's number, signed toward the bet) into what happened in the
game, from the play-by-play: turnovers (EPA of the turnover plays; points off turnovers), special-teams return TDs,
kicks (EPA of field goals, extra points and blocked punts), garbage-time points (plays at a home win chance under 10%
or over 90%, with the turnover and return plays taken out), the starting QB's share of dropbacks (under 60% = lost in
game), kickoff weather realised (Open-Meteo archive, kickoff hour) against the reading the model used, penalties
(EPA of accepted penalties that wiped out the play; penalty yards), fourth-down go-for-it EPA, overtime points and
pace (plays against the plays the teams' ratings expected). Each is turned into points by one regression over every
regular-season game 2015-2025 (the model's miss on the components), then signed toward the bet.

Part 2 turns every pattern into a filter or adjustment and scores it on 2015-18, 2019-22 and 2023-25 by record and
units at -110, with a bootstrap of the chance the filtered record beats the unfiltered one.

No market input enters any adjustment: the line only defines and grades the bet (and a filter may read the bet's own
line, e.g. "the model's side lays 7+"). Nothing under nflmodel/, data/processed/, web/ or docs/ is written.

Writes reports/postmortem.csv, reports/postmortem_patterns.csv, reports/postmortem.md.
Usage: python -m experiments.postmortem
"""
from __future__ import annotations
import json, re, sys, time, warnings
import numpy as np, pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from nflmodel import model as M, backtest as B   # noqa: E402

OUT, REP, RAW = ROOT / "data" / "processed", ROOT / "reports", ROOT / "data" / "raw"
TEAM_FIX = {"OAK": "LV", "SD": "LAC", "STL": "LA"}
WINDOWS = {"2015-18": (2015, 2018), "2019-22": (2019, 2022), "2023-25": (2023, 2025)}
SPREAD_EDGE, UNDER_P, LAST_WEEK = 4.0, 0.55, 17
VIG = 1.1
GARBAGE_LO, GARBAGE_HI, QB_LOST = 0.10, 0.90, 0.60
N_BOOT = 10000
warnings.simplefilter("ignore", category=pd.errors.PerformanceWarning)
T0 = time.time()
RNG = np.random.default_rng(20260929)


def log(msg):
    print(f"[{time.time() - T0:6.1f}s] {msg}", flush=True)


def num(s):
    return pd.to_numeric(s, errors="coerce").fillna(0)


# ---------------------------------------------------------------------------------------------------------------------
# 1. The games and the bets
# ---------------------------------------------------------------------------------------------------------------------
games = pd.read_parquet(OUT / "games.parquet")
pred = pd.read_parquet(OUT / "pred_v3.parquet")
d = B.join(pred, games)
d = d[(d.game_type == "REG") & (d.season >= 2015)].copy()
G = d.set_index("game_id")
gx = games.set_index("game_id")
for c in ["primetime", "div_game", "dome", "roof", "home_rest", "away_rest", "overtime", "temp", "wind", "home_qb_id", "away_qb_id", "slot", "referee", "neutral"]:
    G[c] = G.index.map(gx[c])
log(f"{len(G)} played regular-season games 2015+ in pred_v3")

# the as-of inputs the model used (the same prep the walk-forward applies)
f = M.prep(M.with_trends(pd.read_parquet(OUT / "features_asof.parquet")))
fh = f[f.home == 1].set_index("game_id"); fa = f[f.home == 0].set_index("game_id")
ids = G.index.intersection(fh.index).intersection(fa.index)
G = G.loc[ids].copy()
INJ = ["skill_out_value", "opp_skill_out_value", "off_snap_out", "opp_def_snap_out"]
for k in M.FEATS:
    G[f"h_{k}"] = fh.loc[ids, k]; G[f"a_{k}"] = fa.loc[ids, k]
for k in ["off_epa_play", "own_def_epa_play", "off_plays", "def_plays", "qb_rating", "rest", "n_games"]:
    G[f"h_{k}"] = fh.loc[ids, k]; G[f"a_{k}"] = fa.loc[ids, k]
# the ridge equation's pull from the injury inputs on the margin (home minus away); the blend carries the same inputs
G["inj_margin"] = sum(G[f"coef_{k}"] * (G[f"h_{k}"] - G[f"a_{k}"]) for k in INJ)
G["qbout_margin"] = G["coef_qb_out"] * (G["h_qb_out"] - G["a_qb_out"])
G["injq_margin"] = G.inj_margin + G.qbout_margin
G["net_h"] = G.h_off_epa_play - G.h_own_def_epa_play; G["net_a"] = G.a_off_epa_play - G.a_own_def_epa_play
mods = ["ridge", "success", "split", "plays", "alpha3", "alpha30", "trees"]
G["blend_sd"] = np.std(np.column_stack([G[f"home_m_{k}"] - G[f"away_m_{k}"] for k in mods]), axis=1)
G["trees_edge"] = G.home_m_trees - G.away_m_trees - G.spread_line
G["ridge_edge"] = G.home_exp_ridge - G.away_exp_ridge - G.spread_line
G["final_week"] = ((G.season <= 2020) & (G.week == 17)) | (G.week == 18)
G["p_under"] = 1 - G.p_over_emp

# ---------------------------------------------------------------------------------------------------------------------
# 2. Play-by-play: every regular-season game 2015-2026, one read per season
# ---------------------------------------------------------------------------------------------------------------------
COLS = ["game_id", "play_id", "season_type", "posteam", "defteam", "home_team", "away_team", "qtr", "down", "play_type", "epa", "home_wp",
        "interception", "fumble_lost", "fumbled_1_team", "return_touchdown", "td_team", "field_goal_attempt", "field_goal_result",
        "extra_point_attempt", "extra_point_result", "punt_blocked", "punt_attempt", "kickoff_attempt", "penalty", "penalty_team", "penalty_yards",
        "total_home_score", "total_away_score", "fixed_drive", "drive_start_transition", "two_point_attempt", "weather"]


def pbp_game_table(p: pd.DataFrame) -> pd.DataFrame:
    p = p[p.season_type == "REG"].copy()
    for c in ["posteam", "defteam", "home_team", "away_team", "fumbled_1_team", "td_team", "penalty_team"]:
        p[c] = p[c].replace(TEAM_FIX)
    p = p.sort_values(["game_id", "play_id"])
    p["epa"] = pd.to_numeric(p.epa, errors="coerce").fillna(0.0)
    for c in ["interception", "fumble_lost", "return_touchdown", "field_goal_attempt", "extra_point_attempt", "punt_blocked", "punt_attempt",
              "kickoff_attempt", "penalty", "two_point_attempt", "penalty_yards"]:
        p[c] = num(p[c])
    hs, as_ = p.total_home_score.astype(float), p.total_away_score.astype(float)
    p["dh"] = hs.groupby(p.game_id).diff().fillna(hs).clip(lower=0)
    p["da"] = as_.groupby(p.game_id).diff().fillna(as_).clip(lower=0)
    p["hwp"] = p.groupby("game_id").home_wp.transform(lambda s: s.ffill().bfill()).fillna(0.5)
    isH = lambda col: (p[col] == p.home_team)
    isA = lambda col: (p[col] == p.away_team)
    # turnovers: the team that lost the ball (the passer's team on an interception, the fumbler's on a fumble lost)
    to = (p.interception == 1) | (p.fumble_lost == 1)
    loser = np.where(p.interception == 1, p.posteam, p.fumbled_1_team.fillna(p.posteam))
    p["to"] = to; p["loser"] = loser
    e_loser = np.where(loser == p.posteam, p.epa, -p.epa)   # EPA from the losing team's side (negative)
    p["to_epa_h"] = np.where(to & (loser == p.home_team), e_loser, 0.0); p["to_epa_a"] = np.where(to & (loser == p.away_team), e_loser, 0.0)
    p["to_h"] = (to & (loser == p.home_team)).astype(int); p["to_a"] = (to & (loser == p.away_team)).astype(int)
    rtd = p.return_touchdown == 1
    p["def_td_h"] = (rtd & to & isH("td_team")).astype(int); p["def_td_a"] = (rtd & to & isA("td_team")).astype(int)
    kickplay = (p.field_goal_attempt == 1) | (p.extra_point_attempt == 1) | (p.punt_blocked == 1)
    st = rtd & ~to & ~kickplay & ((p.punt_attempt == 1) | (p.kickoff_attempt == 1) | p.play_type.isin(["punt", "kickoff"]))
    e_td = np.where(p.posteam == p.td_team, p.epa, -p.epa)
    p["st_td_h"] = (st & isH("td_team")).astype(int); p["st_td_a"] = (st & isA("td_team")).astype(int)
    p["st_epa_h"] = np.where(st & isH("td_team"), e_td, 0.0); p["st_epa_a"] = np.where(st & isA("td_team"), e_td, 0.0)
    p["blk_td_h"] = (rtd & kickplay & isH("td_team")).astype(int); p["blk_td_a"] = (rtd & kickplay & isA("td_team")).astype(int)
    # kicks: EPA of field goals, extra points and blocked punts for the kicking team (posteam)
    p["kick_epa_h"] = np.where(kickplay & isH("posteam"), p.epa, 0.0); p["kick_epa_a"] = np.where(kickplay & isA("posteam"), p.epa, 0.0)
    fgm = (p.field_goal_attempt == 1) & p.field_goal_result.isin(["missed", "blocked"])
    xpm = (p.extra_point_attempt == 1) & p.extra_point_result.isin(["failed", "blocked", "aborted"])
    blk = ((p.field_goal_attempt == 1) & (p.field_goal_result == "blocked")) | (p.punt_blocked == 1) | ((p.extra_point_attempt == 1) & (p.extra_point_result == "blocked"))
    p["fg_miss_h"] = (fgm & isH("posteam")).astype(int); p["fg_miss_a"] = (fgm & isA("posteam")).astype(int)
    p["xp_miss_h"] = (xpm & isH("posteam")).astype(int); p["xp_miss_a"] = (xpm & isA("posteam")).astype(int)
    p["blk_h"] = (blk & isH("posteam")).astype(int); p["blk_a"] = (blk & isA("posteam")).astype(int)   # kicks of this team blocked
    # garbage time: plays starting with the home side under 10% or over 90% to win; turnover and return plays left out
    garb = ((p.hwp < GARBAGE_LO) | (p.hwp > GARBAGE_HI)) & ~to & ~st
    p["gb_h"] = np.where(garb, p.dh, 0.0); p["gb_a"] = np.where(garb, p.da, 0.0)
    hl, al = garb & (p.hwp > GARBAGE_HI), garb & (p.hwp < GARBAGE_LO)   # home leading / away leading
    p["gbL_h"] = np.where(hl, p.dh, 0.0); p["gbT_a"] = np.where(hl, p.da, 0.0)   # leader's points, trailer's points (home leading)
    p["gbL_a"] = np.where(al, p.da, 0.0); p["gbT_h"] = np.where(al, p.dh, 0.0)
    # penalties: EPA of accepted penalties that wiped the play out (no_play), from the home side; accepted penalty yards
    pen = (p.penalty == 1) & (p.play_type == "no_play")
    p["pen_epa_h"] = np.where(pen, np.where(isH("posteam"), p.epa, -p.epa), 0.0)
    p["pen_yds_h"] = np.where(isH("penalty_team"), p.penalty_yards, 0.0); p["pen_yds_a"] = np.where(isA("penalty_team"), p.penalty_yards, 0.0)
    # fourth downs gone for (run or pass on 4th down, two-point tries excluded)
    fd = (pd.to_numeric(p.down, errors="coerce") == 4) & p.play_type.isin(["pass", "run"]) & (p.two_point_attempt == 0)
    p["fd_epa_h"] = np.where(fd, np.where(isH("posteam"), p.epa, -p.epa), 0.0)
    p["fd_att_h"] = (fd & isH("posteam")).astype(int); p["fd_att_a"] = (fd & isA("posteam")).astype(int)
    # overtime points
    ot = pd.to_numeric(p.qtr, errors="coerce") >= 5
    p["ot_h"] = np.where(ot, p.dh, 0.0); p["ot_a"] = np.where(ot, p.da, 0.0)
    # points off turnovers: points the recovering team scored on the drive that started from the turnover, plus return TDs (7)
    first = p.groupby(["game_id", "fixed_drive"]).agg(tr=("drive_start_transition", "first"), pos=("posteam", lambda s: s.dropna().iloc[0] if s.notna().any() else None),
                                                       ph=("dh", "sum"), pa=("da", "sum")).reset_index()
    first = first.merge(p.groupby("game_id")[["home_team", "away_team"]].first().reset_index(), on="game_id")
    after = first.tr.fillna("").str.contains("INTERCEPTION|FUMBLE|MUFFED")
    first["pot_h"] = np.where(after & (first.pos == first.home_team), first.ph, 0.0)
    first["pot_a"] = np.where(after & (first.pos == first.away_team), first.pa, 0.0)
    pot = first.groupby("game_id")[["pot_h", "pot_a"]].sum()
    agg = {c: "sum" for c in ["to_epa_h", "to_epa_a", "to_h", "to_a", "def_td_h", "def_td_a", "st_td_h", "st_td_a", "st_epa_h", "st_epa_a", "blk_td_h", "blk_td_a",
                              "kick_epa_h", "kick_epa_a", "fg_miss_h", "fg_miss_a", "xp_miss_h", "xp_miss_a", "blk_h", "blk_a", "gb_h", "gb_a", "gbL_h", "gbT_h", "gbL_a", "gbT_a", "pen_epa_h",
                              "pen_yds_h", "pen_yds_a", "fd_epa_h", "fd_att_h", "fd_att_a", "ot_h", "ot_a"]}
    g = p.groupby("game_id").agg({**agg, "weather": "first"})
    g = g.join(pot)
    g["pot_h"] = g.pot_h.fillna(0) + 7 * g.def_td_h; g["pot_a"] = g.pot_a.fillna(0) + 7 * g.def_td_a
    return g


frames = []
for s in range(2015, 2027):
    fp = RAW / "pbp" / f"play_by_play_{s}.parquet"
    if not fp.exists():
        continue
    t = time.time()
    p = pd.read_parquet(fp, columns=COLS)
    frames.append(pbp_game_table(p)); del p
    log(f"pbp {s}: {len(frames[-1])} games ({time.time() - t:.1f}s)")
PB = pd.concat(frames)
G = G.join(PB, how="left")
G["has_pbp"] = G.to_h.notna()
log(f"pbp joined: {int(G.has_pbp.sum())} of {len(G)} games")

# QB: the starter's share of his team's dropbacks
qb = pd.read_parquet(OUT / "qb_games.parquet")
tot = qb.groupby(["game_id", "team"]).dropbacks.sum()
qd = dict(zip(zip(qb.game_id, qb.team, qb.qb_id), qb.dropbacks))
for side, tcol, qcol in [("h", "home_team", "home_qb_id"), ("a", "away_team", "away_qb_id")]:
    num_ = np.array([qd.get((g_, t_, q_), 0) for g_, t_, q_ in zip(G.index, G[tcol], G[qcol])], dtype=float)
    den = np.array([tot.get((g_, t_), np.nan) for g_, t_ in zip(G.index, G[tcol])], dtype=float)
    G[f"qb_share_{side}"] = np.where(den > 0, num_ / np.where(den > 0, den, 1), np.nan)
    # under 60% of the dropbacks = lost in game; no dropback at all = the listed starter (the model's QB input) did not play:
    # a wrong or changed starter known before kickoff, not an in-game loss
    G[f"qb_lost_{side}"] = ((G[f"qb_share_{side}"] > 0) & (G[f"qb_share_{side}"] < QB_LOST)).astype(float)
    G[f"qb_wrong_{side}"] = (G[f"qb_share_{side}"] == 0).astype(float)

# weather: the kickoff-hour reading (Open-Meteo archive; else the play-by-play's game-day text) against the model's input
arc = pd.read_csv(ROOT / "data" / "weather" / "archive_kickoff.csv").set_index("game_id")


def parse_wx(w):
    if not isinstance(w, str):
        return np.nan, np.nan
    t = re.search(r"Temp:\s*(-?\d+)", w); wd = re.search(r"Wind:\s*[A-Za-z/]*\s*(\d+)\s*mph", w)
    return (float(t.group(1)) if t else np.nan), (float(wd.group(1)) if wd else np.nan)


pw = np.array([parse_wx(w) for w in G.weather]) if "weather" in G.columns else np.full((len(G), 2), np.nan)
G["temp_real"] = G.index.map(arc.temp).astype(float); G["wind_real"] = G.index.map(arc.wind).astype(float)
G["wx_src"] = np.where(G.temp_real.notna(), "archive", np.where(~np.isnan(pw[:, 0]), "pbp_text", "none"))
G["temp_real"] = G.temp_real.fillna(pd.Series(pw[:, 0], index=G.index)); G["wind_real"] = G.wind_real.fillna(pd.Series(pw[:, 1], index=G.index))
outdoor = (G.h_dome == 0)
G["d_wind"] = np.where(outdoor & G.wind_real.notna(), G.wind_real - G.h_wind_out, 0.0)
cold_real = np.where(outdoor & G.temp_real.notna(), (G.temp_real < M.COLD_F).astype(float), G.h_cold)
G["d_cold"] = cold_real - G.h_cold
wic_h = cold_real * G.home_team.isin(M.WARM_OR_DOME); wic_a = cold_real * G.away_team.isin(M.WARM_OR_DOME)
G["wx_margin"] = G.coef_warm_in_cold * ((wic_h - G.h_warm_in_cold) - (wic_a - G.a_warm_in_cold))
G["wx_total"] = 2 * G.coef_wind_out * G.d_wind + 2 * G.coef_cold * G.d_cold + G.coef_warm_in_cold * ((wic_h - G.h_warm_in_cold) + (wic_a - G.a_warm_in_cold))

# pace: the game's offensive plays against what the two teams' plays ratings expected (one fit over all games)
tg = pd.read_parquet(OUT / "team_games.parquet", columns=["game_id", "team", "plays"])
pl = tg.groupby("game_id").plays.sum()
G["plays"] = G.index.map(pl).astype(float)
lg_plays = tg.merge(games[["game_id", "season"]], on="game_id").groupby("season").plays.mean() * 2
G["lg_prev_plays"] = (G.season - 1).map(lg_plays)
X = np.column_stack([np.ones(len(G)), G.h_off_plays + G.a_off_plays, G.h_def_plays + G.a_def_plays, G.lg_prev_plays])
ok = G.plays.notna() & G.lg_prev_plays.notna() & (G.season <= 2025)
bp = np.linalg.lstsq(X[ok.values], G.plays[ok].values, rcond=None)[0]
G["exp_plays"] = X @ bp
G["d_plays"] = G.plays - G.exp_plays
G["pace_margin"] = G.model_spread * G.d_plays / G.exp_plays
log("QB share, weather, pace done")

# ---------------------------------------------------------------------------------------------------------------------
# 3. From components to points: one regression of the model's miss over every regular-season game 2015-2025
# ---------------------------------------------------------------------------------------------------------------------
G["miss_margin"] = G.result - G.model_spread     # home side
G["miss_total"] = G.total - G.model_total
G["to_epa_net"] = G.to_epa_h - G.to_epa_a
G["to_net"] = G.to_a - G.to_h                    # turnover margin, home side (takeaways minus giveaways)
G["pot_net"] = G.pot_h - G.pot_a; G["pot_sum"] = G.pot_h + G.pot_a
G["st_epa_net"] = G.st_epa_h - G.st_epa_a
G["ret_td_sum"] = G.def_td_h + G.def_td_a + G.st_td_h + G.st_td_a + G.blk_td_h + G.blk_td_a
G["def_st_td_net"] = (G.def_td_h + G.st_td_h + G.blk_td_h) - (G.def_td_a + G.st_td_a + G.blk_td_a)
G["kick_epa_net"] = G.kick_epa_h - G.kick_epa_a; G["kick_epa_sum"] = G.kick_epa_h + G.kick_epa_a
G["kick_miss_net"] = (G.fg_miss_a + G.xp_miss_a + G.blk_a) - (G.fg_miss_h + G.xp_miss_h + G.blk_h)
G["gb_net"] = G.gb_h - G.gb_a; G["gb_sum"] = G.gb_h + G.gb_a
G["qb_lost_net"] = G.qb_lost_a - G.qb_lost_h; G["qb_lost_sum"] = G.qb_lost_a + G.qb_lost_h
G["ot_net"] = G.ot_h - G.ot_a; G["ot_sum"] = G.ot_h + G.ot_a
G["pen_yds_net"] = G.pen_yds_a - G.pen_yds_h; G["pen_yds_sum"] = G.pen_yds_a + G.pen_yds_h
G["fd_att_sum"] = G.fd_att_h + G.fd_att_a
G["pot_sum_nonret"] = G.pot_sum - 7 * (G.def_td_h + G.def_td_a)

# (component, regression column, group) — margin (home side) and total
COMP_M = [("turnovers", "to_epa_net", "luck"), ("returns", "st_epa_net", "luck"), ("kicks", "kick_epa_net", "luck"), ("garbage", "gb_net", "luck"),
          ("qb_lost", "qb_lost_net", "event"), ("weather", "wx_margin", "event"), ("overtime", "ot_net", "event"), ("pace", "pace_margin", "event"),
          ("penalties", "pen_epa_h", "event"), ("fourth", "fd_epa_h", "event")]
COMP_T = [("turnovers", "pot_sum_nonret", "luck"), ("returns", "ret_td_sum", "luck"), ("kicks", "kick_epa_sum", "luck"), ("garbage", "gb_sum", "luck"),
          ("qb_lost", "qb_lost_sum", "event"), ("weather", "wx_total", "event"), ("overtime", "ot_sum", "event"), ("pace", "d_plays", "event"),
          ("penalties", "pen_yds_sum", "event"), ("fourth", "fd_att_sum", "event")]


def fit_components(y, comps):
    fit = G[G.has_pbp & (G.season <= 2025) & G[y].notna()].copy()
    cols = [c for _, c, _ in comps]
    fit[cols] = fit[cols].fillna(0)
    Xf = np.column_stack([np.ones(len(fit))] + [fit[c].values for c in cols])
    beta, *_ = np.linalg.lstsq(Xf, fit[y].values, rcond=None)
    res = fit[y].values - Xf @ beta
    r2 = 1 - res.var() / fit[y].values.var()
    # standard errors
    s2 = res @ res / (len(fit) - Xf.shape[1]); se = np.sqrt(np.diag(s2 * np.linalg.inv(Xf.T @ Xf)))
    means = fit[cols].mean()
    # R2 of the luck group alone and luck + events
    out = {"beta": dict(zip(cols, beta[1:])), "se": dict(zip(cols, se[1:])), "r2": r2, "n": len(fit), "means": means}
    for grp in ["luck"]:
        cc = [c for _, c, g in comps if g == grp]
        Xg = np.column_stack([np.ones(len(fit))] + [fit[c].values for c in cc]); bg, *_ = np.linalg.lstsq(Xg, fit[y].values, rcond=None)
        out[f"r2_{grp}"] = 1 - (fit[y].values - Xg @ bg).var() / fit[y].values.var()
    return out


FM, FT = fit_components("miss_margin", COMP_M), fit_components("miss_total", COMP_T)
log(f"margin regression R2 {FM['r2']:.3f} (luck alone {FM['r2_luck']:.3f}); total R2 {FT['r2']:.3f} (luck alone {FT['r2_luck']:.3f})")
for name, fit, comps in [("margin", FM, COMP_M), ("total", FT, COMP_T)]:
    for (lab, c, grp) in comps:
        G[f"{name}_pts_{lab}"] = fit["beta"][c] * (G[c].fillna(fit["means"][c]) - fit["means"][c])

# ---------------------------------------------------------------------------------------------------------------------
# 4. The bets, one row each, with the decomposition signed toward the bet
# ---------------------------------------------------------------------------------------------------------------------
LUCK = ["turnovers", "returns", "kicks", "garbage"]
EVENTS = ["qb_lost", "weather", "overtime", "pace", "penalties", "fourth"]


def spread_mask(x, edge_col="spread_edge", cut=SPREAD_EDGE):
    return (x[edge_col].abs() >= cut) & (x.week <= LAST_WEEK) & x.spread_line.notna()


def under_mask(x, cut=UNDER_P):
    return (x.p_under >= cut) & (x.week <= LAST_WEEK) & x.total_line.notna()


def grade_spread_rows(x, edge_col="spread_edge"):
    s = np.sign(x[edge_col]); cm = x.result - x.spread_line
    win = ((s > 0) & (cm > 0)) | ((s < 0) & (cm < 0)); push = cm == 0
    return win.values, push.values, np.where(push, 0.0, np.where(win, 1.0, -VIG))


def grade_under_rows(x):
    cm = x.total - x.total_line; win = cm < 0; push = cm == 0
    return win.values, push.values, np.where(push, 0.0, np.where(win, 1.0, -VIG))


# situations, from the model's side (the bet side for a spread), defined on every game so the filters can be scored
s_side = np.sign(G.spread_edge)
G["bet_home"] = s_side > 0
G["side_line"] = np.where(G.bet_home, -G.spread_line, G.spread_line)   # the bet side's number: negative = laying points
G["side_fav"] = G.side_line < 0; G["side_dog"] = G.side_line > 0
G["edge_abs"] = G.spread_edge.abs()
G["side_rest"] = np.where(G.bet_home, G.h_rest, G.a_rest); G["opp_rest"] = np.where(G.bet_home, G.a_rest, G.h_rest)
G["side_net"] = np.where(G.bet_home, G.net_h, G.net_a); G["opp_net"] = np.where(G.bet_home, G.net_a, G.net_h)
G["side_qb_rating"] = np.where(G.bet_home, G.h_qb_rating, G.a_qb_rating); G["opp_qb_rating"] = np.where(G.bet_home, G.a_qb_rating, G.h_qb_rating)
G["side_qb_out"] = np.where(G.bet_home, G.h_qb_out, G.a_qb_out); G["opp_qb_out"] = np.where(G.bet_home, G.a_qb_out, G.h_qb_out)
G["inj_toward"] = s_side * G.inj_margin; G["injq_toward"] = s_side * G.injq_margin
G["edge_wo_inj"] = G.edge_abs - G.inj_toward; G["edge_wo_injq"] = G.edge_abs - G.injq_toward
ks = [3, 7, -3, -7]
G["crosses_key"] = np.column_stack([((G.model_spread - k) * (G.spread_line - k) < 0) for k in ks]).any(axis=1)
G["on_key"] = G.spread_line.abs().isin([3, 7])
G["near_key"] = G.spread_line.abs().isin([2.5, 3, 3.5, 6.5, 7, 7.5])
G["outdoor_bad_wx"] = (G.h_dome == 0) & ((G.wind.fillna(0) >= 15) | (G.temp.fillna(60) < M.COLD_F))
G["trees_disagree"] = np.sign(G.trees_edge) != s_side
G["ridge_small"] = G.ridge_edge.abs() * (np.sign(G.ridge_edge) == s_side) < SPREAD_EDGE
G["early_n"] = G.home_n_games < 4
G["side_dead"] = np.where(G.bet_home, G.h_dead_late, G.a_dead_late) > 0; G["opp_dead"] = np.where(G.bet_home, G.a_dead_late, G.h_dead_late) > 0

SITS = {   # name -> (boolean over games, plain words); every one becomes a "skip these" filter in Part 2
    "side_fav": (G.side_fav, "model's side is the favourite"),
    "side_dog": (G.side_dog, "model's side is the underdog"),
    "side_lays7": (G.side_line <= -7, "model's side lays 7+"),
    "side_gets7": (G.side_line >= 7, "model's side gets 7+"),
    "bet_home": (G.bet_home, "model's side at home"),
    "bet_away": (~G.bet_home, "model's side away"),
    "edge_4_5": ((G.edge_abs >= 4) & (G.edge_abs < 5), "edge 4 to 5"),
    "edge_5_7": ((G.edge_abs >= 5) & (G.edge_abs < 7), "edge 5 to 7"),
    "edge_7p": (G.edge_abs >= 7, "edge 7+"),
    "on_key": (G.on_key, "line exactly 3 or 7"),
    "near_key": (G.near_key, "line within a half point of 3 or 7"),
    "no_key_cross": (~G.crosses_key, "model and line on the same side of 3 and 7"),
    "fav_lays_key": (G.side_fav & G.on_key, "model's side lays exactly 3 or 7"),
    "wk1_2": (G.week <= 2, "Weeks 1-2"),
    "wk3_4": (G.week.between(3, 4), "Weeks 3-4"),
    "wk5_8": (G.week.between(5, 8), "Weeks 5-8"),
    "wk9_13": (G.week.between(9, 13), "Weeks 9-13"),
    "wk14_17": (G.week.between(14, 17), "Weeks 14-17"),
    "wk17": (G.week == 17, "Week 17"),
    "final_week": (G.final_week, "season's final regular-season week"),
    "side_short_rest": (G.side_rest <= 5, "model's side on short rest"),
    "opp_short_rest": (G.opp_rest <= 5, "opponent on short rest"),
    "side_off_bye": (G.side_rest >= 10, "model's side off a bye/long week"),
    "opp_off_bye": (G.opp_rest >= 10, "opponent off a bye/long week"),
    "rest_disadv": (G.side_rest - G.opp_rest <= -3, "model's side 3+ fewer days' rest"),
    "primetime": (G.primetime.astype(bool), "primetime"),
    "division": (G.div_game.astype(bool), "division game"),
    "dome": (G.h_dome == 1, "dome / closed roof"),
    "bad_weather": (G.outdoor_bad_wx, "outdoors, wind 15+ or under 35F"),
    "side_strong": (G.side_net > G.side_net.quantile(0.75), "model's side top-quartile rating"),
    "side_weak": (G.side_net < G.side_net.quantile(0.25), "model's side bottom-quartile rating"),
    "opp_strong": (G.opp_net > G.opp_net.quantile(0.75), "opponent top-quartile rating"),
    "opp_weak": (G.opp_net < G.opp_net.quantile(0.25), "opponent bottom-quartile rating"),
    "side_qb_out": (G.side_qb_out > 0, "model's side without last game's starting QB"),
    "opp_qb_out": (G.opp_qb_out > 0, "opponent without last game's starting QB"),
    "inj_only": (G.edge_wo_inj < SPREAD_EDGE, "edge under 4 without the player-injury inputs"),
    "injq_only": (G.edge_wo_injq < SPREAD_EDGE, "edge under 4 without the injury inputs and QB-out"),
    "inj_big": (G.injq_toward.abs() >= 2, "injury inputs move the margin 2+ points"),
    "trees_disagree": (G.trees_disagree, "boosted trees on the other side of the line"),
    "ridge_small": (G.ridge_small, "the ridge equation alone under 4"),
    "blend_sd_hi": (G.blend_sd >= G.blend_sd.quantile(0.8), "the seven models disagree (top fifth of spread)"),
    "early_n": (G.early_n, "home team under 4 games played this season"),
    "side_dead": (G.side_dead, "model's side out of the race (Week 12+, 40% or worse)"),
    "opp_dead": (G.opp_dead, "opponent out of the race"),
    "neutral": (G.neutral.astype(bool), "neutral site"),
    "side_qb_low": (G.side_qb_rating < G.side_qb_rating.quantile(0.25), "model's side QB bottom-quartile rating"),
    "opp_qb_high": (G.opp_qb_rating > G.opp_qb_rating.quantile(0.75), "opponent QB top-quartile rating"),
}
TSITS = {   # totals situations (under bets)
    "wk1_2": (G.week <= 2, "Weeks 1-2"), "wk3_4": (G.week.between(3, 4), "Weeks 3-4"), "wk5_8": (G.week.between(5, 8), "Weeks 5-8"),
    "wk9_13": (G.week.between(9, 13), "Weeks 9-13"), "wk14_17": (G.week.between(14, 17), "Weeks 14-17"), "wk17": (G.week == 17, "Week 17"),
    "final_week": (G.final_week, "season's final regular-season week"),
    "pu_55_57": (G.p_under.between(0.55, 0.57, inclusive="left"), "under chance 55-57%"),
    "pu_57_60": (G.p_under.between(0.57, 0.60, inclusive="left"), "under chance 57-60%"),
    "pu_60p": (G.p_under >= 0.60, "under chance 60%+"),
    "line_50p": (G.total_line >= 50, "total line 50+"), "line_u41": (G.total_line < 41, "total line under 41"),
    "mt_48p": (G.model_total >= 48, "model total 48+"), "mt_u40": (G.model_total < 40, "model total under 40"),
    "dome": (G.h_dome == 1, "dome / closed roof"), "windy": ((G.h_dome == 0) & (G.wind.fillna(0) >= 15), "outdoors, wind 15+"),
    "cold": ((G.h_dome == 0) & (G.temp.fillna(60) < M.COLD_F), "outdoors, under 35F"), "rain": (G.h_rain > 0, "rain"),
    "primetime": (G.primetime.astype(bool), "primetime"), "division": (G.div_game.astype(bool), "division game"),
    "qb_out_any": ((G.h_qb_out + G.a_qb_out) > 0, "either starting QB out"),
    "off_strong": ((G.h_off_epa_play + G.a_off_epa_play) > (G.h_off_epa_play + G.a_off_epa_play).quantile(0.75), "both offenses strong (top-quartile sum)"),
    "off_weak": ((G.h_off_epa_play + G.a_off_epa_play) < (G.h_off_epa_play + G.a_off_epa_play).quantile(0.25), "both offenses weak (bottom-quartile sum)"),
    "fast_pace": (G.exp_plays > G.exp_plays.quantile(0.75), "fast expected pace (top quartile)"),
    "slow_pace": (G.exp_plays < G.exp_plays.quantile(0.25), "slow expected pace (bottom quartile)"),
    "short_rest": ((G.h_rest <= 5) | (G.a_rest <= 5), "Thursday / short rest"),
    "early_n": (G.early_n, "home team under 4 games played this season"),
    "dead_any": ((G.h_dead_late + G.a_dead_late) > 0, "a team out of the race"),
    "neutral": (G.neutral.astype(bool), "neutral site"),
}


def bet_rows(kind: str) -> pd.DataFrame:
    x = G[spread_mask(G) if kind == "spread" else under_mask(G)].copy()
    if kind == "spread":
        s = np.sign(x.spread_edge); x["bet"] = pd.Series(np.where(s > 0, x.home_team, x.away_team), index=x.index) + " " + x.side_line.map(lambda v: f"{v:+g}")
        x["miss"] = s * x.miss_margin; x["cover"] = s * (x.result - x.spread_line); x["edge"] = x.edge_abs
        for lab, _, _ in COMP_M:
            x[f"c_{lab}"] = s * x[f"margin_pts_{lab}"]
        win, push, units = grade_spread_rows(x)
    else:
        s = -1.0; x["bet"] = "Under " + x.total_line.map(lambda v: f"{v:g}")
        x["miss"] = -(x.total - x.model_total); x["cover"] = x.total_line - x.total; x["edge"] = x.model_total - x.total_line
        for lab, _, _ in COMP_T:
            x[f"c_{lab}"] = s * x[f"total_pts_{lab}"]
        win, push, units = grade_under_rows(x)
    x["kind"] = kind; x["win"] = win; x["push"] = push; x["units"] = units
    x.loc[~x.has_pbp, [f"c_{c}" for c in LUCK + EVENTS]] = np.nan
    x["luck"] = x[[f"c_{c}" for c in LUCK]].sum(axis=1, min_count=1)
    if kind == "spread":   # sensitivity: garbage time counted only as the trailing side's points (backdoor), not the leader's pile-on
        bd = G.loc[G.season <= 2025, "gbT_h"] - G.loc[G.season <= 2025, "gbT_a"]
        x["c_garbage_backdoor"] = s * FM["beta"]["gb_net"] * ((x.gbT_h - x.gbT_a) - bd.mean())
        x["luck_backdoor_only"] = x[["c_turnovers", "c_returns", "c_kicks", "c_garbage_backdoor"]].sum(axis=1, min_count=1)
    x["events"] = x[[f"c_{c}" for c in EVENTS]].sum(axis=1, min_count=1)
    x["residual"] = x.miss - x.luck.fillna(0) - x.events.fillna(0)
    x["window"] = pd.cut(x.season, [2014, 2018, 2022, 2025, 2030], labels=["2015-18", "2019-22", "2023-25", "2026"]).astype(str)
    return x


SB, UB = bet_rows("spread"), bet_rows("under")
for nm, bb in [("spread", SB), ("under", UB)]:
    for w, (a, b_) in WINDOWS.items():
        y = bb[bb.season.between(a, b_)]
        log(f"{nm} {w}: {int((y.win & ~y.push).sum())}-{int((~y.win & ~y.push).sum())}-{int(y.push.sum())} units {y.units.sum():+.1f}")

# ---------------------------------------------------------------------------------------------------------------------
# 5. Part 2: filters and adjustments, three windows, bootstrap
# ---------------------------------------------------------------------------------------------------------------------
GT = G[G.season <= 2025]


def record(mask, kind, edge_col="spread_edge"):
    out = {}
    for w, (a, b_) in WINDOWS.items():
        x = GT[mask & GT.season.between(a, b_)]
        win, push, units = grade_spread_rows(x, edge_col) if kind == "spread" else grade_under_rows(x)
        out[w] = (int((win & ~push).sum()), int((~win & ~push).sum()), int(push.sum()), float(units.sum()))
    return out


def bootstrap(base_mask, new_mask, kind, edge_col_new="spread_edge"):
    """P(filtered units > unfiltered units) resampling the games in either set (2015-2025), N_BOOT times; per window too."""
    u = base_mask | new_mask
    x = GT[u]
    _, _, ub = grade_spread_rows(x) if kind == "spread" else grade_under_rows(x)
    _, _, un = grade_spread_rows(x, edge_col_new) if kind == "spread" else grade_under_rows(x)
    diff = np.where(new_mask[u].values, un, 0.0) - np.where(base_mask[u].values, ub, 0.0)
    res = {}
    for w, (a, b_) in list(WINDOWS.items()) + [("all", (2015, 2025))]:
        dd = diff[x.season.between(a, b_).values]
        n = len(dd)
        if n == 0 or np.all(dd == 0):
            res[w] = np.nan; continue
        W = RNG.poisson(1.0, size=(N_BOOT, n))
        res[w] = float(((W @ dd) > 0).mean())
    return res


def test_rule(name, label, kind, new_mask, source, edge_col_new="spread_edge"):
    base = spread_mask(GT) if kind == "spread" else under_mask(GT)
    rb, rn = record(base, kind), record(new_mask, kind, edge_col_new)
    row = {"kind": kind, "rule": name, "label": label, "source": source}
    better_all, vol_ok = True, True
    for w in WINDOWS:
        wb, lb, pb, ub = rb[w]; wn, ln, pn, un = rn[w]
        row[f"base_{w}"] = f"{wb}-{lb}" + (f"-{pb}" if pb else ""); row[f"base_units_{w}"] = round(ub, 1)
        row[f"rec_{w}"] = f"{wn}-{ln}" + (f"-{pn}" if pn else ""); row[f"units_{w}"] = round(un, 1)
        row[f"win_pct_{w}"] = round(wn / (wn + ln), 3) if wn + ln else np.nan
        row[f"d_units_{w}"] = round(un - ub, 1)
        nb, nn = wb + lb + pb, wn + ln + pn
        row[f"bets_share_{w}"] = round(nn / nb, 3) if nb else np.nan
        better_all &= (un > ub + 1e-9); vol_ok &= (nn >= 0.8 * nb)
    tb, tn = sum(rb[w][3] for w in WINDOWS), sum(rn[w][3] for w in WINDOWS)
    row["units_all"] = round(tn, 1); row["d_units_all"] = round(tn - tb, 1)
    row["units_better_all3"] = better_all; row["volume_80pct_all3"] = vol_ok; row["adopt"] = better_all and vol_ok
    bs = bootstrap(base, new_mask, kind, edge_col_new)
    for w, v in bs.items():
        row[f"p_boot_better_{w}"] = round(v, 3) if pd.notna(v) else np.nan
    return row


rules = []
MASKS = {}
sb = spread_mask(GT); ub_ = under_mask(GT)
# pre-registered spread candidates (the brief's examples and the docs' open questions)
PRE_S = {
    "side_lays7": "skip when the model's side lays 7+", "wk1_2": "skip Weeks 1-2", "wk17": "skip Week 17 (Weeks 17-18; 18 is already skipped)",
    "final_week": "skip each season's final regular-season week (Week 17 through 2020)", "inj_only": "skip when the edge comes only from the player-injury inputs",
    "injq_only": "skip when the edge comes only from the injury inputs incl. QB-out", "wk14_17": "skip Weeks 14-17 (the shadowearly rule)",
    "side_fav": "skip favourites (the shadowdog rule)", "fav_lays_key": "skip when the model's side lays exactly 3 or 7",
    "no_key_cross": "skip when the edge crosses neither 3 nor 7", "edge_7p": "skip edges of 7+", "trees_disagree": "skip when the boosted trees disagree",
    "blend_sd_hi": "skip when the seven models disagree most", "side_qb_out": "skip when the model's side is without its starting QB",
    "opp_qb_out": "skip when the opponent is without its starting QB",
}
for k, (m_, lab) in SITS.items():
    MASKS[("spread", f"skip_{k}")] = sb & ~m_.loc[GT.index].astype(bool)
    rules.append(test_rule(f"skip_{k}", PRE_S.get(k, f"skip: {lab}"), "spread", MASKS[("spread", f"skip_{k}")], "pre-registered" if k in PRE_S else "every situation"))
# adjustments: cap the injury pull on the margin, recompute the edge on every game
for cap in [1.0, 2.0, 3.0]:
    for nm, col in [("inj", "inj_margin"), ("injq", "injq_margin")]:
        e = GT.model_spread - GT[col] + GT[col].clip(-cap, cap) - GT.spread_line
        GT = GT.assign(**{f"edge_cap_{nm}_{cap:g}": e})
        m_ = spread_mask(GT, f"edge_cap_{nm}_{cap:g}")
        rules.append(test_rule(f"cap_{nm}_{cap:g}", f"cap the {'player-injury' if nm == 'inj' else 'injury + QB-out'} pull on the margin at {cap:g} pts, re-flag every game",
                               "spread", m_, "pre-registered", f"edge_cap_{nm}_{cap:g}"))
e = GT.model_spread - GT.injq_margin - GT.spread_line
GT = GT.assign(edge_noinj=e)
rules.append(test_rule("drop_injq", "drop the injury inputs' pull entirely, re-flag every game", "spread", spread_mask(GT, "edge_noinj"), "pre-registered", "edge_noinj"))
# under candidates
PRE_U = {"wk1_2": "skip Weeks 1-2", "wk17": "skip Week 17", "final_week": "skip each season's final week", "wk14_17": "skip Weeks 14-17", "dome": "skip domes",
         "windy": "skip wind 15+", "primetime": "skip primetime", "qb_out_any": "skip when either starter is out", "line_50p": "skip total lines 50+"}
for k, (m_, lab) in TSITS.items():
    MASKS[("under", f"skip_{k}")] = ub_ & ~m_.loc[GT.index].astype(bool)
    rules.append(test_rule(f"skip_{k}", PRE_U.get(k, f"skip: {lab}"), "under", MASKS[("under", f"skip_{k}")], "pre-registered" if k in PRE_U else "every situation"))
for cut in [0.56, 0.57, 0.58, 0.60]:
    rules.append(test_rule(f"under_cut_{cut:g}", f"raise the under cut to {100 * cut:.0f}%", "under", under_mask(GT, cut), "pre-registered"))
RULES = pd.DataFrame(rules)
log(f"{len(RULES)} rules scored")


def placebo(kind, new_mask, n_sim=20000):
    """The chance that dropping the same number of today's bets AT RANDOM in each window improves units on all three windows
    (what the adoption rule's first test passes by luck for a filter of this size)."""
    base = spread_mask(GT) if kind == "spread" else under_mask(GT)
    pr = 1.0
    for w, (a, b_) in WINDOWS.items():
        bw = base & GT.season.between(a, b_)
        _, _, u = grade_spread_rows(GT[bw]) if kind == "spread" else grade_under_rows(GT[bw])
        k = int((bw & ~new_mask).sum())
        if k == 0:
            return 0.0
        R = RNG.random((n_sim, len(u))); idx = np.argpartition(R, k - 1, axis=1)[:, :k]
        pr *= float((u[idx].sum(axis=1) < -1e-9).mean())
    return pr


RULES["p_random_pass"] = [round(placebo(r.kind, MASKS[(r.kind, r.rule)]), 3) if (r.kind, r.rule) in MASKS else np.nan for r in RULES.itertuples()]
log("placebo done")

# ---------------------------------------------------------------------------------------------------------------------
# 6. Part 1 comparisons: losses against wins on every component and situation
# ---------------------------------------------------------------------------------------------------------------------


def welch(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float); a, b = a[~np.isnan(a)], b[~np.isnan(b)]
    if len(a) < 3 or len(b) < 3:
        return np.nan
    return (a.mean() - b.mean()) / np.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))


pat = []
for kind, bb, sits in [("spread", SB, SITS), ("under", UB, TSITS)]:
    bt = bb[(bb.season <= 2025) & ~bb.push]
    L, W = bt[~bt.win], bt[bt.win]
    for c in ["miss", "luck", "events", "residual"] + [f"c_{x}" for x in LUCK + EVENTS]:
        row = {"kind": kind, "type": "component (pts toward bet)", "name": c, "mean_losses": round(L[c].mean(), 2), "mean_wins": round(W[c].mean(), 2),
               "mean_all": round(bt[c].mean(), 2), "t_all_vs_zero": round(bt[c].mean() / (bt[c].std() / np.sqrt(bt[c].notna().sum())), 2) if c != "miss" else np.nan,
               "t_loss_vs_win": round(welch(L[c], W[c]), 2)}
        for w, (a, b_) in WINDOWS.items():
            row[f"mean_all_{w}"] = round(bt[bt.season.between(a, b_)][c].mean(), 2)
        pat.append(row)
    raw = {"spread": [("turnover margin (takeaways - giveaways)", "to_net", "net"), ("points off turnovers, net", "pot_net", "net"),
                      ("def/ST TDs, net", "def_st_td_net", "net"), ("kicks missed or blocked, net (opp - own)", "kick_miss_net", "net"),
                      ("garbage-time points, net", "gb_net", "net"), ("penalty yards, net (opp - own)", "pen_yds_net", "net"), ("overtime", "overtime", "flag"),
                      ("own starter lost in game", "qb_lost_own", "flag"), ("opp starter lost in game", "qb_lost_opp", "flag"),
                      ("plays vs expected", "d_plays", "raw"), ("wind realised - used", "d_wind", "raw")],
           "under": [("turnovers, both teams", "to_sum", "raw"), ("points off turnovers, both", "pot_sum", "raw"), ("def/ST TDs, both", "ret_td_sum", "raw"),
                     ("garbage-time points, both", "gb_sum", "raw"), ("overtime", "overtime", "flag"), ("a starter lost in game", "qb_lost_sum", "raw"),
                     ("plays vs expected", "d_plays", "raw"), ("wind realised - used", "d_wind", "raw"), ("penalty yards, both", "pen_yds_sum", "raw"),
                     ("fourth-down tries, both", "fd_att_sum", "raw")]}[kind]
    bt = bt.copy()
    s = np.where(bt.bet_home, 1, -1) if kind == "spread" else np.ones(len(bt))
    bt["to_sum"] = bt.to_h + bt.to_a
    bt["qb_lost_own"] = np.where(bt.bet_home, bt.qb_lost_h, bt.qb_lost_a); bt["qb_lost_opp"] = np.where(bt.bet_home, bt.qb_lost_a, bt.qb_lost_h)
    bt["overtime"] = bt.overtime.astype(float)
    for lab, c, how in raw:
        v = bt[c] * (s if how == "net" else 1)
        L_, W_ = v[~bt.win], v[bt.win]
        pat.append({"kind": kind, "type": "game stat (bet side)" if how == "net" else "game stat", "name": lab, "mean_losses": round(L_.mean(), 3), "mean_wins": round(W_.mean(), 3),
                    "mean_all": round(v.mean(), 3), "t_loss_vs_win": round(welch(L_, W_), 2)})
    for k, (m_, lab) in sits.items():
        mk = m_.loc[bt.index].astype(bool)
        a1, a0 = bt[mk], bt[~mk]
        r = {"kind": kind, "type": "situation", "name": k, "label": lab, "n_in": len(a1), "win_pct_in": round(a1.win.mean(), 3) if len(a1) else np.nan,
             "units_in": round(a1.units.sum(), 1), "win_pct_out": round(a0.win.mean(), 3) if len(a0) else np.nan, "units_out": round(a0.units.sum(), 1),
             "share_of_losses": round(mk[~bt.win].mean(), 3), "share_of_wins": round(mk[bt.win].mean(), 3),
             "mean_residual_in": round(a1.residual.mean(), 2) if len(a1) else np.nan, "mean_residual_out": round(a0.residual.mean(), 2)}
        # two-proportion z on the win rate in vs out
        if len(a1) >= 5 and len(a0) >= 5:
            p1, p0 = a1.win.mean(), a0.win.mean(); pp = bt.win.mean()
            r["z_winrate"] = round((p1 - p0) / np.sqrt(pp * (1 - pp) * (1 / len(a1) + 1 / len(a0))), 2)
        for w, (a, b_) in WINDOWS.items():
            y = a1[a1.season.between(a, b_)]
            r[f"in_{w}"] = f"{int(y.win.sum())}-{int((~y.win).sum())}"; r[f"units_in_{w}"] = round(y.units.sum(), 1)
        r["units_in_negative_all3"] = all(r[f"units_in_{w}"] < 0 for w in WINDOWS)
        pat.append(r)
PAT = pd.DataFrame(pat)

# knowable: a loss inside a "skip" rule whose removal improved units on all three windows (volume ignored)
syst_s = RULES[(RULES.kind == "spread") & RULES.units_better_all3 & RULES.rule.str.startswith("skip_")].rule.str.replace("skip_", "", regex=False).tolist()
syst_u = RULES[(RULES.kind == "under") & RULES.units_better_all3 & RULES.rule.str.startswith("skip_")].rule.str.replace("skip_", "", regex=False).tolist()
log(f"systematic (units better on all three windows): spread {syst_s}; under {syst_u}")


def classify(bb, sits, syst):
    bb = bb.copy()
    kn = pd.Series(False, index=bb.index); why = pd.Series("", index=bb.index)
    for k in syst:
        m_ = sits[k][0].loc[bb.index].astype(bool); kn |= m_; why = np.where(m_ & (why == ""), k, why); why = pd.Series(why, index=bb.index)
    wrong = (bb.qb_wrong_h + bb.qb_wrong_a) > 0
    why = pd.Series(np.where(wrong, "listed starter did not play (model priced the wrong QB)", why), index=bb.index)
    kn = kn | wrong
    bb["knowable_pattern"] = why.where(kn, "")
    lost = ~bb.win & ~bb.push
    adj_l = bb.cover - bb.luck.fillna(0); adj_le = adj_l - bb.events.fillna(0)
    cls = np.select([~lost, adj_l >= 0, adj_le >= 0, kn], ["", "luck", "in-game events", "knowable"], "variance")
    bb["loss_class"] = cls
    if "luck_backdoor_only" in bb.columns:
        adj_b = bb.cover - bb.luck_backdoor_only.fillna(0); adj_be = adj_b - bb.events.fillna(0)
        bb["loss_class_backdoor"] = np.select([~lost, adj_b >= 0, adj_be >= 0, kn], ["", "luck", "in-game events", "knowable"], "variance")
    won = bb.win & ~bb.push
    bb["win_class"] = np.select([~won, (bb.cover - bb.luck.fillna(0)) <= 0], ["", "luck"], "earned")
    return bb


SB, UB = classify(SB, SITS, syst_s), classify(UB, TSITS, syst_u)

# reasons for the worst misses
PHRASE = {"turnovers": "turnovers", "returns": "return TD", "kicks": "kicks", "garbage": "garbage-time points", "qb_lost": "QB lost in game",
          "weather": "weather surprise", "overtime": "overtime", "pace": "pace", "penalties": "penalties", "fourth": "fourth downs"}


def reason(r):
    if not r.has_pbp:
        return "no play-by-play yet"
    comps = {c: r[f"c_{c}"] for c in LUCK + EVENTS if pd.notna(r[f"c_{c}"])}
    bad = sorted([(v, c) for c, v in comps.items() if v <= -3], key=lambda t: t[0])[:2]
    parts = []
    home = r.bet_home if r.kind == "spread" else None
    for v, c in bad:
        if c == "turnovers":
            if r.kind == "spread":
                own, opp = (r.to_h, r.to_a) if home else (r.to_a, r.to_h); parts.append(f"turnovers {int(own)}-{int(opp)} ({v:+.1f})")
            else:
                parts.append(f"{int(r.to_h + r.to_a)} turnovers, {int(r.pot_sum)} pts off them ({v:+.1f})")
        elif c == "qb_lost":
            sh = (r.qb_share_h if home else r.qb_share_a) if r.kind == "spread" else min(r.qb_share_h, r.qb_share_a)
            parts.append(f"QB lost in game ({100 * sh:.0f}% of dropbacks) ({v:+.1f})")
        elif c == "kicks":
            parts.append(f"kicks ({int(r.fg_miss_h + r.fg_miss_a)} FG missed, {int(r.blk_h + r.blk_a)} blocked) ({v:+.1f})")
        elif c == "returns":
            parts.append(f"return TD ({v:+.1f})")
        elif c == "garbage":
            parts.append(f"garbage time ({v:+.1f})")
        else:
            parts.append(f"{PHRASE[c]} ({v:+.1f})")
    if r.qb_wrong_h + r.qb_wrong_a > 0:
        parts.insert(0, "model priced a QB who did not play")
    won = bool(r.win) and not bool(r.push)
    if not parts:
        if won:
            return f"covered anyway (miss {r.miss:+.1f} inside the edge)"
        if r.residual <= -8:
            return f"outplayed, no luck (residual {r.residual:+.1f})"
        return f"nothing stands out: ordinary miss (residual {r.residual:+.1f})"
    if r.residual <= -8:
        parts.append(f"and outplayed ({r.residual:+.1f})")
    return ("covered anyway; " if won else "") + "; ".join(parts)


for bb in (SB, UB):
    bb["reason"] = [reason(r) for _, r in bb.iterrows()]

# ---------------------------------------------------------------------------------------------------------------------
# 7. This season's recorded picks (data/tracker), graded ones decomposed where the data exist
# ---------------------------------------------------------------------------------------------------------------------
trk = []
tp = ROOT / "data" / "tracker" / "graded.csv"
if tp.exists():
    gr = pd.read_csv(tp)
    gr = gr[gr.who.isin(["model", "shadowunder"])]
    for r in gr.itertuples():
        row = {"game_id": r.game_id, "season": r.season, "week": r.week, "who": r.who, "bet": r.bet, "line": r.line, "odds": r.odds, "result": r.result, "units": r.units}
        if r.game_id in G.index:
            g_ = G.loc[r.game_id]
            row.update({"model_spread": g_.model_spread, "model_total": g_.model_total, "actual_margin": g_.result, "actual_total": g_.total})
            if r.kind == "total":
                row["miss"] = -(g_.total - g_.model_total); row["cover"] = r.line - g_.total
        # ESPN summary for games the play-by-play does not reach yet
        sj = ROOT / "data" / "results" / f"summary_{r.game_id}.json"
        if sj.exists() and r.result in ("win", "loss", "push"):
            j = json.loads(sj.read_text()); spl = j.get("scoringPlays", [])
            ret = [s_ for s_ in spl if re.search(r"Return Touchdown|Blocked", s_["type"]["text"])]
            ot_pts = 0
            if spl:
                reg = [s_ for s_ in spl if s_["period"]["number"] <= 4]; last = reg[-1] if reg else {"awayScore": 0, "homeScore": 0}
                ot_pts = (spl[-1]["awayScore"] + spl[-1]["homeScore"]) - (last["awayScore"] + last["homeScore"])
            dr = j.get("drives", {}).get("previous", [])
            tos = [i for i, x in enumerate(dr) if re.search(r"Interception|Fumble", x.get("displayResult", ""), re.I)]
            pot = 0
            for i in tos:   # the recovering team's next drive (a return TD is counted once, below)
                if "Touchdown" in dr[i].get("displayResult", ""):
                    continue
                nx = dr[i + 1] if i + 1 < len(dr) else None
                if nx is not None and nx["team"]["abbreviation"] != dr[i]["team"]["abbreviation"] and nx.get("isScore"):
                    pot += 7 if "Touchdown" in nx.get("displayResult", "") else 3
            miss_fg = sum(1 for x in dr if re.search(r"Missed FG|Blocked FG", x.get("displayResult", ""), re.I))
            row.update({"espn_return_tds": len(ret), "espn_turnovers": len(tos), "espn_pts_off_to": pot + 7 * len(ret), "espn_ot_pts": ot_pts, "espn_missed_fg": miss_fg,
                        "espn_note": "; ".join(s_["type"]["text"] + " " + s_["team"]["abbreviation"] for s_ in ret)})
        trk.append(row)
TRK = pd.DataFrame(trk)
log(f"tracker rows {len(TRK)}")

# ---------------------------------------------------------------------------------------------------------------------
# 8. Outputs
# ---------------------------------------------------------------------------------------------------------------------
KEEP = ["kind", "window", "season", "week", "home_team", "away_team", "bet", "spread_line", "total_line", "model_spread", "model_total", "edge", "p_cover_home", "p_under",
        "home_score", "away_score", "result", "total", "win", "push", "units", "cover", "miss", "luck", "events", "residual"] + [f"c_{c}" for c in LUCK + EVENTS] + \
       ["loss_class", "win_class", "knowable_pattern", "reason", "c_garbage_backdoor", "luck_backdoor_only", "loss_class_backdoor", "to_h", "to_a", "to_epa_h", "to_epa_a", "pot_h", "pot_a", "def_td_h", "def_td_a", "st_td_h", "st_td_a",
        "blk_td_h", "blk_td_a", "fg_miss_h", "fg_miss_a", "xp_miss_h", "xp_miss_a", "blk_h", "blk_a", "kick_epa_h", "kick_epa_a", "gb_h", "gb_a", "gbL_h", "gbT_h", "gbL_a", "gbT_a", "qb_wrong_h", "qb_wrong_a", "qb_share_h", "qb_share_a",
        "wind", "wind_real", "temp", "temp_real", "wx_src", "d_wind", "d_cold", "pen_epa_h", "pen_yds_h", "pen_yds_a", "fd_att_h", "fd_att_a", "fd_epa_h", "overtime",
        "ot_h", "ot_a", "plays", "exp_plays", "d_plays", "bet_home", "side_line", "inj_margin", "injq_margin", "edge_wo_injq", "blend_sd", "trees_edge",
        "primetime", "div_game", "h_dome", "side_rest", "opp_rest", "side_net", "opp_net", "has_pbp"]
ALL = pd.concat([SB, UB])
ALL.index.name = "game_id"
ALL[[c for c in KEEP if c in ALL.columns]].round(3).to_csv(REP / "postmortem.csv")
patterns = pd.concat([PAT.assign(section="loss_vs_win"), RULES.assign(section="filter_test")], ignore_index=True)
patterns.to_csv(REP / "postmortem_patterns.csv", index=False)
log("csv written")


def fmt_rec(x):
    w, l, p = int((x.win & ~x.push).sum()), int((~x.win & ~x.push).sum()), int(x.push.sum())
    return f"{w}-{l}" + (f"-{p}" if p else "")


def what_we_missed(bb, variant=False):
    bt = bb[(bb.season <= 2025)].copy()
    if variant:
        bt["loss_class"] = bt["loss_class_backdoor"]; bt["c_garbage"] = bt["c_garbage_backdoor"]
        bt["residual"] = bt.miss - bt.luck_backdoor_only.fillna(0) - bt.events.fillna(0)
    L = bt[(~bt.win) & (~bt.push)]
    rows = []
    n = len(L)
    tot_miss = L.miss.sum()
    luck_pts = L[[f"c_{c}" for c in LUCK]].sum().sum(); ev_pts = L[[f"c_{c}" for c in EVENTS]].sum().sum()
    kn = L.loss_class == "knowable"
    resid_kn = L.residual[kn].sum(); resid_var = L.residual[~kn].sum()
    for lab, cnt, p_ in [("Luck (turnovers, returns, kicks, garbage time)", (L.loss_class == "luck").sum(), luck_pts),
                         ("In-game events (QB lost, weather, overtime, pace, penalties, 4th downs)", (L.loss_class == "in-game events").sum(), ev_pts),
                         ("Knowable (the model priced a QB who did not play, or a pattern that lost on all three windows)", kn.sum(), resid_kn),
                         ("Ordinary variance (the rest)", (L.loss_class == "variance").sum(), resid_var)]:
        rows.append({"Explained by": lab, "Losses (count, first that flips it)": f"{int(cnt)} ({100 * cnt / n:.0f}%)",
                     "Points of the miss": f"{p_:+.0f} ({100 * p_ / tot_miss:.0f}%)"})
    rows.append({"Explained by": "All losses", "Losses (count, first that flips it)": f"{n}", "Points of the miss": f"{tot_miss:+.0f} (mean {tot_miss / n:+.1f})"})
    return pd.DataFrame(rows)


def comp_table(bb):
    bt = bb[(bb.season <= 2025) & ~bb.push]
    rows = []
    for c in ["miss", "luck"] + [f"c_{x}" for x in LUCK] + ["events"] + [f"c_{x}" for x in EVENTS] + ["residual"]:
        L, W = bt[~bt.win][c], bt[bt.win][c]
        rows.append({"Component (pts toward the bet)": c.replace("c_", "  "), "Losses": round(L.mean(), 2), "Wins": round(W.mean(), 2), "All bets": round(bt[c].mean(), 2),
                     "t (all bets vs 0)": round(bt[c].mean() / (bt[c].std() / np.sqrt(bt[c].notna().sum())), 1) if c not in ("miss",) else "",
                     **{w: round(bt[bt.season.between(a, b_)][c].mean(), 2) for w, (a, b_) in WINDOWS.items()}})
    return pd.DataFrame(rows)


def luck_symmetry(bb):
    bt = bb[(bb.season <= 2025)]
    L, W = bt[~bt.win & ~bt.push], bt[bt.win & ~bt.push]
    return (int((L.loss_class == "luck").sum()), len(L), int((W.win_class == "luck").sum()), len(W))


def worst(bb, n=10):
    out = []
    for s_, x in bb.sort_values("miss").groupby("season"):
        x = x.head(n)
        for gid, r in x.iterrows():
            out.append({"Season": s_, "Wk": int(r.week), "Game": f"{r.away_team} @ {r.home_team}", "Bet": r.bet, "Final": f"{int(r.away_score)}-{int(r.home_score)}",
                        "Model": f"{r.model_spread:+.1f}" if r.kind == "spread" else f"{r.model_total:.1f}", "Miss": round(r.miss, 1),
                        "Result": "W" if r.win and not r.push else ("P" if r.push else "L"), "Reason": r.reason})
    return pd.DataFrame(out)


def rules_md(kind, only=None, top=None):
    x = RULES[RULES.kind == kind].copy()
    if only is not None:
        x = x[x.source.isin(only)]
    x = x.sort_values("d_units_all", ascending=False)
    if top:
        x = x.head(top)
    cols = {"label": "Rule", "rec_2015-18": "2015-18", "d_units_2015-18": "Δu", "rec_2019-22": "2019-22", "d_units_2019-22": "Δu ",
            "rec_2023-25": "2023-25", "d_units_2023-25": "Δu  ", "d_units_all": "Δu all", "p_boot_better_all": "P(boot better)", "adopt": "Adopt"}
    y = x[list(cols)].rename(columns=cols)
    y["Bets kept"] = [f"{100 * min(a, b_, c):.0f}%" for a, b_, c in zip(x["bets_share_2015-18"], x["bets_share_2019-22"], x["bets_share_2023-25"])]
    y["Adopt"] = y["Adopt"].map({True: "yes", False: "no"})
    y["P(random pass)"] = x["p_random_pass"].values
    return y.to_markdown(index=False)


def base_line(kind):
    r = RULES[RULES.kind == kind].iloc[0]
    return ", ".join(f"{w} {r[f'base_{w}']} ({r[f'base_units_{w}']:+.1f}u)" for w in WINDOWS)


ws, ns, wu, nu = luck_symmetry(SB)
ls_u = luck_symmetry(UB)


def garbage_split(bb):
    bt = bb[(bb.season <= 2025) & ~bb.push & bb.has_pbp].copy()
    h = bt.bet_home.values
    bt["own pts, own side leading"] = np.where(h, bt.gbL_h, bt.gbL_a)
    bt["opp pts, own side leading (backdoor against)"] = -np.where(h, bt.gbT_a, bt.gbT_h)
    bt["own pts, own side trailing (backdoor for)"] = np.where(h, bt.gbT_h, bt.gbT_a)
    bt["opp pts, own side trailing (pile-on)"] = -np.where(h, bt.gbL_a, bt.gbL_h)
    cols = ["own pts, own side leading", "opp pts, own side leading (backdoor against)", "own pts, own side trailing (backdoor for)", "opp pts, own side trailing (pile-on)"]
    bt["net"] = bt[cols].sum(axis=1); cols.append("net")
    rows = []
    for lab, m_ in [("losses", ~bt.win), ("wins", bt.win), ("all bets", bt.win | ~bt.win), ("model's side the underdog", bt.side_line > 0), ("model's side the favourite", bt.side_line < 0)]:
        rows.append({"Bets": lab, "n": int(m_.sum()), **{c: round(bt.loc[m_, c].mean(), 2) for c in cols}})
    return pd.DataFrame(rows)


def luck_neutral(bb):
    out = {}
    for w, (a, b_) in list(WINDOWS.items()) + [("2015-25", (2015, 2025))]:
        x = bb[bb.season.between(a, b_) & bb.has_pbp]
        c0 = x.cover; c1 = x.cover - x.luck.fillna(0)
        out[w] = (f"{int((c0 > 0).sum())}-{int((c0 < 0).sum())}", f"{int((c1 > 0).sum())}-{int((c1 < 0).sum())}")
    return pd.DataFrame({"Window": list(out), "Actual record": [v[0] for v in out.values()], "Record with the four luck components taken out": [v[1] for v in out.values()]})
adopted = RULES[RULES.adopt]
sp_sit = PAT[(PAT.kind == "spread") & (PAT.type == "situation")].copy()
un_sit = PAT[(PAT.kind == "under") & (PAT.type == "situation")].copy()


def sit_md(x):
    x = x.assign(absz=x.z_winrate.abs()).sort_values("absz", ascending=False)
    cols = {"label": "Situation", "n_in": "Bets", "win_pct_in": "Win% in", "win_pct_out": "Win% out", "z_winrate": "z", "units_in": "Units in",
            "in_2015-18": "2015-18", "in_2019-22": "2019-22", "in_2023-25": "2023-25", "units_in_negative_all3": "Lost units all 3"}
    y = x[list(cols)].rename(columns=cols)
    y["Lost units all 3"] = y["Lost units all 3"].map({True: "yes", False: ""})
    return y.to_markdown(index=False)


def beta_md(fit, comps):
    rows = []
    for lab, c, grp in comps:
        rows.append({"Component": lab, "Measured as": c, "Group": grp, "Points per unit": round(fit["beta"][c], 3), "se": round(fit["se"][c], 3)})
    return pd.DataFrame(rows).to_markdown(index=False)


from scipy.stats import binomtest
_s = SB[(SB.season <= 2025) & ~SB.push]
_own = np.where(_s.bet_home, _s.qb_lost_h, _s.qb_lost_a) > 0; _opp = np.where(_s.bet_home, _s.qb_lost_a, _s.qb_lost_h) > 0
_p_qb = binomtest(int(_own.sum()), int(_own.sum() + _opp.sum()), 0.5).pvalue
_rs = lambda k, r: RULES[(RULES.kind == k) & (RULES.rule == r)].iloc[0]
_sk = RULES[RULES.p_random_pass.notna()]
_obs, _exp = int(_sk.units_better_all3.sum()), float(_sk.p_random_pass.sum())
_c1, _c2, _c3 = _rs("spread", "cap_injq_1"), _rs("spread", "cap_injq_2"), _rs("spread", "cap_injq_3")
_ps = RULES[RULES.adopt & RULES.p_random_pass.notna()]
_nb = {"spread": {w: int(spread_mask(GT)[GT.season.between(a, b_)].sum()) for w, (a, b_) in WINDOWS.items()},
       "under": {w: int(under_mask(GT)[GT.season.between(a, b_)].sum()) for w, (a, b_) in WINDOWS.items()}}
_drop = [round(_nb[r.kind][w] * (1 - r[f"bets_share_{w}"])) for _, r in _ps.iterrows() for w in WINDOWS]
_n_found = int((RULES.adopt & (RULES.source == "every situation")).sum())
VERDICT = f"""**{int(RULES.adopt.sum())} rules meet the letter of the adoption rule; none should be adopted.** The rule is a necessary condition ("adopted only if"), and
what passes it here looks like what random filters would do:

- Each passing skip rule drops {min(_drop)} to {max(_drop)} bets per window. Its gain on the held-out 2023-25 is {_ps['d_units_2023-25'].min():.1f} to
  {_ps['d_units_2023-25'].max():.1f} units, one or two bets. Dropping the same number of bets at random passes the all-three-windows test
  {100 * _ps.p_random_pass.min():.0f}% to {100 * _ps.p_random_pass.max():.0f}% of the time for each of them (P(random pass)). Across the
  {len(_sk)} skip rules scored, {_obs} passed against {_exp:.1f} expected by chance, and the rules overlap, so they are not {len(_sk)}
  independent tries. {_n_found} of the {int(RULES.adopt.sum())} were found by looking (every situation turned into a filter), not named in advance.
- The injury cap passes at 1 point ({_c1['d_units_2015-18']:+.1f} / {_c1['d_units_2019-22']:+.1f} / {_c1['d_units_2023-25']:+.1f} units) and fails at 2 points
  ({_c2['d_units_2015-18']:+.1f} / {_c2['d_units_2019-22']:+.1f} / {_c2['d_units_2023-25']:+.1f}) and at 3 ({_c3['d_units_2015-18']:+.1f} / {_c3['d_units_2019-22']:+.1f} / {_c3['d_units_2023-25']:+.1f}).
  A real overreaction would show a dose response, and this has none. The injury-only skip, the brief's own suggestion, loses on every window
  (the injury inputs earn their place).
- "Skip total lines under 41" reads the market total. The model-total version of the same idea fails.
- The brief's named candidates all fail: skip laying 7+ (+1.3 / -1.9 / -1.9), skip Weeks 1-2 (-2.3 / -4.3 / -10.8; the early weeks are the
  flag's best stretch), skip Week 17 (+0.7 / +0.4 / -0.9), skip the season's final week (+0.7 / -0.7 / 0), and every injury cap but the 1-point one.

`nflmodel/picks.py` should stay as it is. If the rule is applied to the letter anyway, the change is:

```python
# rule_mask(), spread branch, and the same tests in table().bet():
m &= ~((np.sign(d.home_m_trees - d.away_m_trees - d.spread_line) != np.sign(e)))      # skip when the boosted trees disagree
m &= ~np.where(e > 0, d.away_qb_out, d.home_qb_out).astype(bool)                       # skip when the opponent's starting QB is out
m &= ~np.where(e > 0, d.home_dead_late, d.away_dead_late).astype(bool)                 # skip when the model's side is out of the race
# (home/away qb_out and dead_late are not in pred_v3 today; walk_forward would have to write them)
# under_prob branch:
return ((1 - d.p_over_emp) >= edge) & (d.week <= LAST_BET_WEEK) & ~d.week.between(3, 4) & (d.total_line >= 41) & d.total_line.notna()
```

plus the 1-point cap on the injury inputs' pull, which changes the model's spread itself (model.py, not picks.py).

**What the losses tell us instead.** Most of the damage is the game, not a pattern: the four luck components flip 39% of the spread losses
(56% of the points), and the model's side covers 212-104 instead of 188-127 without them. That figure leans on the brief's garbage-time
definition, though. The garbage points that hurt are the favourite piling on while the model's underdog is being blown out, which is
being outplayed. Counted as backdoor points only, luck explains 13% of the losses. Three things are systematic and are not luck:

1. **The model's edge is about half real.** On the 4+ bets the average edge is {_s.edge.mean():.1f} points and the average cover is
   {_s.cover.mean():+.1f}, so the residual is negative on every window (t = -4.4 on the spread, -5.9 on the unders). The line holds the rest.
   The cut already allows for this, and it is not a filter.
2. **The model's side loses its starting QB in the game far more often than the opponent does:** {int(_own.sum())} times against
   {int(_opp.sum())} over 2015-25 (binomial p = {_p_qb:.3f}; the base rate is about 4.4% of team-games for each side). Those bets went
   {int(_s[_own].win.sum())}-{int((~_s[_own].win).sum())}. The model mostly backs underdogs, and their quarterbacks get hurt or benched.
   No pre-game input tried here predicts it (the model's side with a bottom-quartile QB rating, or without last week's starter, does not
   lose units on every window), so it stays a finding, not a rule.
3. **The listed starter who did not play** (section above) is a data error in the QB input, mostly 2024 Weeks 8-18. It cost little on the
   bets (10-8), but it feeds every 2024-25 prediction and the training rows. It should be fixed in the data build, not filtered.

The under flag's losses are mostly ordinary variance. Luck is neutral there: the record with luck taken out is 382-321, against 381-314
actual. The one systematic component is small: the realised kickoff wind comes in under the model's input on the games it bets under
(-0.1 points, t = -4.4). That is the selection effect of betting unders on high reported wind."""
strong_s = sp_sit.assign(absz=sp_sit.z_winrate.abs()).sort_values("absz", ascending=False).head(5)
runtime = time.time() - T0
md = []
md += ["# Postmortem: every bet the model would have made, 2015-2025 (and 2026 so far)", "",
       f"`experiments/postmortem.py`, run {pd.Timestamp.now():%d %b %Y}, {runtime:.0f}s. Walk-forward predictions from `data/processed/pred_v3.parquet`, "
       "no refit. Rows: `reports/postmortem.csv` (one per bet, with the decomposition); every comparison and every filter test: `reports/postmortem_patterns.csv`.", "",
       "## The bets", "",
       f"- **Spread flag**: the model 4+ points from the closing line, regular season, Weeks 1-17. {base_line('spread')}.",
       f"- **Under flag**: an under at a 55%+ raw chance (`p_over_emp`), Weeks 1-17. {base_line('under')}.",
       "- Graded at -110 (a loss costs 1.1 units), pushes out of the record, exactly as `backtest.grade_spread` and `picks.record`.", "",
       "## Adoption rule (fixed before any result below)", "",
       "A filter or adjustment is adopted only if (1) its units at -110 are higher than today's rule on **each** of 2015-18, 2019-22 and 2023-25, and "
       "(2) it keeps at least 80% of today's bets in **each** window. The bootstrap probability that the filtered record beats the unfiltered one "
       f"({N_BOOT:,} Poisson-weight resamples of the games in either set) is reported beside every rule but does not decide. No adjustment may read a market input: the line "
       "defines and grades the bet only (a filter may read the bet's own number, e.g. 'the model's side lays 7+').", "",
       "Pre-registered candidates (the brief's examples and the docs' open questions): skip when the model's side lays 7+; skip Weeks 1-2; skip Week 17 "
       "(Week 18 is already out); skip each season's final week (Week 17 through 2020); skip when the edge comes only from the injury inputs (with and without "
       "QB-out); cap the injury inputs' pull on the margin at 1, 2 or 3 points or drop it; skip Weeks 14-17; skip favourites; skip laying exactly 3 or 7; skip "
       "edges that cross neither 3 nor 7; skip 7+ edges; skip when the trees disagree or the seven models disagree most; skip when either side's starting QB "
       "is out. Unders: skip Weeks 1-2, Week 17, the final week, Weeks 14-17, domes, wind 15+, primetime, either starter out, lines 50+; raise the cut to "
       "56/57/58/60%. On top of these, every situation in the loss-against-win comparison is scored as a 'skip it' filter (marked 'every situation'); "
       "those are found by looking, so a pass there needs more than the rule to be believed.", "",
       "## How the miss is decomposed", "",
       "The miss is the actual margin (or total) minus the model's, signed so negative hurt the bet. Each game's components come from its play-by-play "
       "(one read per season). They are put in points by one least-squares fit of the model's miss on all of them over every regular-season game "
       f"2015-2025 ({FM['n']} games), then centred on the league mean and signed toward the bet. Margin fit R² {FM['r2']:.2f} (the four luck components "
       f"alone {FM['r2_luck']:.2f}); total fit R² {FT['r2']:.2f} (luck alone {FT['r2_luck']:.2f}).", "",
       "Margin (home side):", "", beta_md(FM, COMP_M), "", "Total:", "", beta_md(FT, COMP_T), "",
       "Notes. Turnovers: the EPA of every interception and lost fumble (muffs included) on the side that lost the ball, return TDs on them included; "
       "points off turnovers (the next drive's points plus return TDs) are in the CSV and drive the totals version. Returns: kickoff and punt return TDs. "
       "Kicks: EPA of every field goal, extra point and blocked punt (a miss or block is the luck; a made kick of average difficulty is about zero). "
       "Garbage time: points on plays that start with the home side under 10% or over 90% to win, turnover and return plays taken out. QB: the starter "
       "(the schedule's QB id) under 60% of his team's dropbacks. Weather: the Open-Meteo kickoff-hour reading (archive; the play-by-play's game-day "
       "text when the archive lacks the game) against the temp/wind the model read. In the backtest that input is the schedule's game-day reading, "
       "not a forecast, so the weather surprise here is small by construction; live, the model reads a forecast. Pace: the game's offensive plays "
       "against a fit of plays on the two teams' plays ratings; on the margin, the model's margin scaled by the extra plays. Penalties: EPA of "
       "accepted penalties that wiped the play out (margin), accepted penalty yards (total). Fourth downs: EPA of go-for-it plays (margin), the number "
       "of tries (total).", "",
       "## What we missed", "",
       "### Spread flag, the losses 2015-2025", "",
       "A loss is put in the first class that flips it: 'luck' if taking the four luck components out would have covered, then 'in-game events', then "
       "'knowable' if the model priced a QB who did not play or the bet sits in a situation whose removal improved units on all three windows "
       "(an upper bound: the Part 2 placebo puts those situations at chance level), else 'ordinary variance'. Points: the sum over the "
       "losses of each group's points (knowable and variance share the residual).", "",
       what_we_missed(SB).to_markdown(index=False), "",
       f"Luck cuts both ways: {ws} of {ns} losses flip to a cover without the luck, and {wu} of {nu} wins flip to a loss without it. Some of that "
       "asymmetry is mechanical (a bet with a real edge sits above the line more often than below it, so symmetric noise pushes more would-be "
       "wins under than would-be losses over); the record with the luck taken out:", "", luck_neutral(SB).to_markdown(index=False), "",
       "Garbage time is the one luck component that is not zero on average over all spread bets (table below). Split by who was ahead "
       "(mean points per bet toward the model's side, plays at a 90%+ win chance):", "", garbage_split(SB).to_markdown(index=False), "",
       "Nearly all of it is the leader's points: when the model's side (four in five times the underdog) is being blown out, the favourite keeps "
       "scoring after the game is decided. That is the tail of being outplayed, not a backdoor. The backdoor parts (the trailing side's garbage "
       "points) cancel. Counting only the trailing side's garbage points as luck (the leader's pile-on moves to the residual):", "",
       what_we_missed(SB, variant=True).to_markdown(index=False), "",
       "### Under flag, the losses 2015-2025", "",
       what_we_missed(UB).to_markdown(index=False), "",
       f"Luck both ways: {ls_u[0]} of {ls_u[1]} losses flip without the luck; {ls_u[2]} of {ls_u[3]} wins flip the other way.", "",
       luck_neutral(UB).to_markdown(index=False), "",
       "### Losses against wins, component by component (mean points toward the bet)", "",
       "The line that matters for 'systematic' is the all-bets mean: luck that is noise averages zero over every bet; a component that is negative on "
       "every bet, wins and losses together, in every window, is something the model gets wrong before kickoff.", "",
       "Spread flag:", "", comp_table(SB).to_markdown(index=False), "", "Under flag:", "", comp_table(UB).to_markdown(index=False), "",
       "### Losses against wins by situation (spread flag, 2015-2025, sorted by |z| of the win-rate gap)", "", sit_md(sp_sit), "",
       "### Losses against wins by situation (under flag)", "", sit_md(un_sit), "",
       "## Part 2: the pattern tests", "",
       "Δu: units of the rule minus units of today's rule in that window. Bets kept: the smallest share of today's bets across the three windows. "
       "P(boot better): share of bootstrap resamples (2015-2025) in which the rule's units beat today's. P(random pass): the chance that dropping "
       "the same number of today's bets at random in each window improves units on all three windows, i.e. passes the first half of the adoption "
       "rule by luck (skip rules only). Adopt: meets the adoption rule as written.", "",
       "### Spread flag, pre-registered", "", rules_md("spread", ["pre-registered"]), "",
       "### Spread flag, every situation as a filter (top 12 by units gained)", "", rules_md("spread", ["every situation"], 12), "",
       "### Under flag, pre-registered", "", rules_md("under", ["pre-registered"]), "",
       "### Under flag, every situation as a filter (top 12 by units gained)", "", rules_md("under", ["every situation"], 12), ""]
passing_units = RULES[RULES.units_better_all3]
md += ["### Rules that improved units on all three windows", ""]
if len(passing_units):
    md += [passing_units[["kind", "rule", "label", "source", "rec_2015-18", "d_units_2015-18", "rec_2019-22", "d_units_2019-22", "rec_2023-25", "d_units_2023-25",
                          "bets_share_2015-18", "bets_share_2019-22", "bets_share_2023-25", "p_boot_better_all", "p_random_pass", "adopt"]].to_markdown(index=False), ""]
else:
    md += ["None.", ""]
for kind in ["spread", "under"]:
    sk = RULES[(RULES.kind == kind) & RULES.p_random_pass.notna()]
    md += [f"{kind.capitalize()}: {len(sk)} skip rules scored; {int(sk.units_better_all3.sum())} improved units on all three windows; dropping the same numbers "
           f"of bets at random would pass that test {sk.p_random_pass.sum():.1f} times in expectation. "
           f"Meeting the full rule (with the 80% volume floor): {int(sk.adopt.sum())} observed against {sk.p_random_pass[sk.volume_80pct_all3].sum():.1f} expected by chance.", ""]
n_tested = len(RULES)
QW = []
for side in ["h", "a"]:
    t_ = G[(G.season <= 2026) & G.has_pbp][["season", f"qb_wrong_{side}"]].rename(columns={f"qb_wrong_{side}": "w"}); QW.append(t_)
QW = pd.concat(QW).groupby("season").w.agg(["sum", "count"])
aff = ALL[(ALL.qb_wrong_h + ALL.qb_wrong_a) > 0]
md += ["## A data problem the postmortem turned up: the listed starter who did not play", "",
       "The model's QB input is the schedule's starter (`games.parquet` home_qb_id / away_qb_id, from nflverse). In some games that QB took no "
       "dropback at all (`qb_games.parquet`), so the game was priced with a quarterback who did not play. Team-games per season where the listed "
       "starter had zero dropbacks:", "",
       " ".join(f"{int(k)}: {int(v)}" + ("," if i < len(QW) - 1 else "") for i, (k, v) in enumerate(QW["sum"].items())), "",
       "2024 (Weeks 8-18) holds most of them: Mariota listed for Washington while Daniels played, Dalton for Carolina while Young played, Rudolph, "
       "Flacco, O'Connell, DeVito and others; 2025 has Tyrod Taylor listed for the Jets in games Fields or Cook started. These are not in-game losses "
       "(they are kept out of the QB-lost component) and they were knowable before kickoff. Bets touched:", "",
       aff.reset_index()[["game_id", "kind", "bet", "win", "units", "miss"]].round(1).to_markdown(index=False), "",
       f"Record on those bets: {int(aff.win.sum())}-{int((~aff.win & ~aff.push).sum())}, {aff.units.sum():+.1f} units. Small money, but the fix belongs in "
       "the data (the starter should be the QB who took the snaps for played games, and the announced starter for coming ones), not in a filter.", ""]
md += ["## Verdict", ""]
if len(adopted):
    md += [f"Meet the adoption rule as written ({n_tested} rules scored): " + "; ".join(adopted.kind + ": " + adopted.label) + ".", ""]
else:
    md += [f"No filter or adjustment meets the adoption rule ({n_tested} rules scored).", ""]
md += [VERDICT, "",
       "## This season's recorded picks (data/tracker)", ""]
if len(TRK):
    tg_ = TRK[TRK.result.isin(["win", "loss", "push"])]
    pend = TRK[~TRK.result.isin(["win", "loss", "push"])]
    cols_ = [c for c in ["game_id", "who", "bet", "result", "units", "model_total", "actual_total", "miss", "cover", "espn_return_tds", "espn_turnovers",
                         "espn_pts_off_to", "espn_missed_fg", "espn_ot_pts", "espn_note"] if c in tg_.columns]
    md += ["Graded:", "", tg_[cols_].round(2).to_markdown(index=False), "",
           "Pending (Week 4): " + ", ".join(pend.who + " " + pend.bet + " (" + pend.game_id + ")") + ".", "",
           "The 2026 play-by-play reaches Week 2 only, so the graded Week 3 unders are read from the ESPN game summaries in `data/results` (return TDs, "
           "turnovers and the points after them, missed field goals, overtime). The backtest rule's 2026 bets (Weeks 1-3, schedule line) are in the CSV "
           "with window 2026.", ""]
s26 = ALL[ALL.season == 2026]
if len(s26):
    md += ["Backtest-rule bets in 2026 so far:", "", s26.reset_index()[["game_id", "kind", "bet", "win", "push", "miss", "luck", "residual", "reason"]].round(1).to_markdown(index=False), ""]
md += ["## The ten worst misses per season", "", "Miss: actual minus the model, signed toward the bet. Model: the model's home margin (spread bets) or "
       "total (unders). Reason: the one or two luck or event components that cost 3+ points toward the bet (points in brackets), and 'outplayed' "
       "where the residual after them is 8+ points; 'outplayed, no luck' when nothing in the game explains a big miss. A season with few losses "
       "fills its ten with its smallest wins.", "",
       "### Spread flag", "", worst(SB).to_markdown(index=False), "", "### Under flag", "", worst(UB).to_markdown(index=False), "",
       f"Runtime: {time.time() - T0:.0f}s on 4 shared cores (play-by-play read once per season, 2015-2026)."]
(REP / "postmortem.md").write_text("\n".join(md))
log("md written")
