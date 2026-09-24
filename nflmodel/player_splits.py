"""Player splits by matchup and scheme (24 Sep 2026). For every receiver, rusher and passer: how he has done against each
look a defense shows (man or zone, each coverage family, blitz, pressure, box count), in each situation (down, red
zone, formation, personnel, play action, motion) and against each opponent, this season, last season and since 2016.

Source: data/processed/scheme_plays.parquet (every pass and run since 2016 with the participation data's coverage,
pressure, box and personnel, FTN's motion, play action and blitzers; nflmodel/scheme.py). Coverage and pressure exist
through last season (the participation file is published after each season); FTN's looks exist from 2022. A look with
no charting for a window has no row.

Per look: plays (targets, carries or dropbacks), yards per play, EPA per play, success rate, touchdowns, and two per
role: receivers catch rate and average depth of target; rushers the share stopped at or behind the line and the share
of 10+ yard runs; passers completion rate and sack rate. Written to web/data/player_splits.js (Players -> a player ->
Matchups and schemes). Usage: python -m nflmodel.player_splits"""
from __future__ import annotations
import json
import numpy as np, pandas as pd
from pathlib import Path
from .features import OUT

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web" / "data"
MIN_N = 5            # a look needs this many plays in the window to get a row
LOOKS = [            # (key, label, which plays: a function of the play table)
    ("all", "every play", lambda d: np.ones(len(d), bool)),
    ("man", "vs man coverage", lambda d: d.man.values),
    ("zone", "vs zone coverage", lambda d: d.zone.values),
    ("cov0", "vs cover 0", lambda d: (d.coverage == "COVER_0").values),
    ("cov1", "vs cover 1", lambda d: (d.coverage == "COVER_1").values),
    ("cov2", "vs cover 2", lambda d: (d.coverage == "COVER_2").values),
    ("cov2m", "vs 2-man", lambda d: (d.coverage == "2_MAN").values),
    ("cov3", "vs cover 3", lambda d: (d.coverage == "COVER_3").values),
    ("cov4", "vs cover 4 (quarters)", lambda d: (d.coverage == "COVER_4").values),
    ("cov6", "vs cover 6", lambda d: (d.coverage == "COVER_6").values),
    ("blitz", "blitzed (5+ rushers)", lambda d: (d.blitz == 1).values),
    ("noblitz", "not blitzed", lambda d: (d.blitz == 0).values),
    ("press", "under pressure", lambda d: (d.pressure == 1).values),
    ("clean", "clean pocket", lambda d: (d.pressure == 0).values),
    ("light", "light box (6 or fewer)", lambda d: (d.box <= 6).values),
    ("mid", "7 in the box", lambda d: (d.box == 7).values),
    ("heavy", "heavy box (8+)", lambda d: (d.box >= 8).values),
    ("pa", "play action", lambda d: (d.is_play_action == 1).values),
    ("nopa", "no play action", lambda d: (d.is_play_action == 0).values),
    ("motion", "with motion", lambda d: (d.is_motion == 1).values),
    ("nomotion", "without motion", lambda d: (d.is_motion == 0).values),
    ("gun", "shotgun or pistol", lambda d: d.shotgun_f.values.astype(bool)),
    ("center", "under center", lambda d: ~d.shotgun_f.values.astype(bool)),
    ("p11", "11 personnel (1 RB, 1 TE)", lambda d: (d.personnel == "11").values),
    ("p12", "12 personnel (1 RB, 2 TE)", lambda d: (d.personnel == "12").values),
    ("p21", "21 personnel (2 RB, 1 TE)", lambda d: (d.personnel == "21").values),
    ("d1", "1st down", lambda d: (d.down == 1).values),
    ("d2", "2nd down", lambda d: (d.down == 2).values),
    ("d3", "3rd or 4th down", lambda d: (d.down >= 3).values),
    ("rz", "red zone (inside the 20)", lambda d: (d.yardline_100 <= 20).values),
    ("lead", "leading by 9+", lambda d: (d.score_differential >= 9).values),
    ("trail", "trailing by 9+", lambda d: (d.score_differential <= -9).values),
]
COLS = ["look", "n", "yds_per", "epa", "success", "td", "x", "y"]
XY = {"rec": ("catch rate", "average depth of target"), "rush": ("stopped at or behind the line", "10+ yard runs"), "pass": ("completion rate", "sack rate")}


def role_plays(d: pd.DataFrame) -> dict:
    """The plays each role is credited with: targets (a pass thrown to him), carries (a run by him, scrambles
    included), dropbacks (a pass play or scramble or sack by him)."""
    rec = d[d.pass_att & d.receiver_player_id.notna()].assign(pid=lambda x: x.receiver_player_id, yds=lambda x: x.yards_gained.fillna(0), td=lambda x: x.pass_touchdown.fillna(0),
                                                             x=lambda x: x.complete_pass.fillna(0), y=lambda x: x.air_yards)
    rush = d[d.carry].assign(pid=lambda x: x.rusher_player_id, yds=lambda x: x.yards_gained.fillna(0), td=lambda x: x.rush_touchdown.fillna(0),
                              x=lambda x: (x.yards_gained.fillna(0) <= 0).astype(float), y=lambda x: (x.yards_gained.fillna(0) >= 10).astype(float))
    ps = d[d.dropback & d.passer_player_id.notna()].assign(pid=lambda x: x.passer_player_id, yds=lambda x: np.where(x.sack.fillna(0) == 1, x.yards_gained.fillna(0), x.pass_yds), td=lambda x: x.pass_touchdown.fillna(0),
                                                             x=lambda x: np.where(x.pass_att, x.complete_pass.fillna(0), np.nan), y=lambda x: x.sack.fillna(0).astype(float))
    return {"rec": rec, "rush": rush, "pass": ps}


def summarize(p: pd.DataFrame) -> list:
    """One row per look with at least MIN_N plays: [look index, n, yards per play, EPA per play, success, TD, x, y]."""
    out = []
    for i, (key, _, f) in enumerate(LOOKS):
        m = np.nan_to_num(np.asarray(f(p), dtype=float)).astype(bool)   # a look not charted on a play (NaN) does not count it
        x = p[m]
        if len(x) < MIN_N:
            continue
        r3 = lambda v: None if v is None or pd.isna(v) else round(float(v), 3)
        out.append([i, int(len(x)), round(float(x.yds.mean()), 2), r3(x.epa.mean()), r3(x.success.mean()), int(x.td.sum()), r3(x.x.mean()), r3(x.y.mean())])
    return out


def build(season: int) -> dict:
    d = pd.read_parquet(OUT / "scheme_plays.parquet")
    d = d[(d.season_type == "REG") | (d.season_type.isna())] if "season_type" in d.columns else d
    roles = role_plays(d)
    recent = set()
    for k, p in roles.items():
        recent |= set(p[p.season >= season - 1].pid.dropna())
    rows, opp = {}, {}
    for role, p in roles.items():
        p = p[p.pid.isin(recent)]
        for pid, g in p.groupby("pid"):
            r = {}
            for w, sel in (("cur", g.season == season), ("last", g.season == season - 1), ("all", np.ones(len(g), bool))):
                s_ = summarize(g[sel])
                if s_:
                    r[w] = s_
            if r:
                rows.setdefault(pid, {})[role] = r
            o = g.groupby("defteam").agg(games=("game_id", "nunique"), n=("play_id", "size"), yds=("yds", "sum"), epa=("epa", "mean"), td=("td", "sum")).reset_index()
            o = o[o.n >= MIN_N]
            if len(o):
                opp.setdefault(pid, {})[role] = [[t, int(gm), int(n), int(y), round(float(e), 3), int(td_)] for t, gm, n, y, e, td_ in o[["defteam", "games", "n", "yds", "epa", "td"]].itertuples(index=False)]
    return {"season": season, "cols": COLS, "looks": [[k, lab] for k, lab, _ in LOOKS], "xy": XY, "min_n": MIN_N,
            "opp_cols": ["opp", "games", "n", "yds", "epa", "td"], "rows": rows, "opp": opp}


NGS = {   # NFL Next Gen Stats, weekly per player (data/raw/ngs*): the season's figures, each week weighted by his volume that week
    "pass": ("ngs/ngs_passing.parquet", "attempts", [("avg_time_to_throw", "Time to throw, s"), ("avg_intended_air_yards", "Intended air yards"), ("avg_completed_air_yards", "Completed air yards"),
                                                    ("aggressiveness", "Aggressiveness, % into tight windows"), ("completion_percentage_above_expectation", "Completion % over expected"), ("avg_air_yards_to_sticks", "Air yards past the sticks")]),
    "rec": ("ngs_rec/ngs_receiving.parquet", "targets", [("avg_separation", "Separation at the catch, yd"), ("avg_cushion", "Cushion at the snap, yd"), ("avg_intended_air_yards", "Intended air yards"),
                                                        ("percent_share_of_intended_air_yards", "Share of team air yards, %"), ("avg_yac_above_expectation", "YAC over expected")]),
    "rush": ("ngs_rush/ngs_rushing.parquet", "rush_attempts", [("rush_yards_over_expected_per_att", "Rush yards over expected a carry"), ("rush_pct_over_expected", "Carries beating expected, %"),
                                                             ("efficiency", "Efficiency (distance run per yard gained)"), ("percent_attempts_gte_eight_defenders", "Carries into 8+ box, %"), ("avg_time_to_los", "Time to the line, s")]),
}


def ngs(pids: set) -> dict:
    """{pid: {kind: [[season, weeks, volume, value, ...]]}} for the regular season, from the weekly NGS files."""
    from .features import RAW
    out = {}
    for kind, (f, vol, cols) in NGS.items():
        fp = RAW / f
        if not fp.exists():
            continue
        d = pd.read_parquet(fp)
        d = d[(d.week > 0) & (d.season_type == "REG") & d.player_gsis_id.isin(pids)]
        for (pid, yr), g in d.groupby(["player_gsis_id", "season"]):
            w = g[vol].fillna(0).astype(float)
            if w.sum() <= 0:
                continue
            vals = [round(float((g[c] * w).sum() / w[g[c].notna()].sum()), 2) if g[c].notna().any() and w[g[c].notna()].sum() > 0 else None for c, _ in cols]
            out.setdefault(pid, {}).setdefault(kind, []).append([int(yr), int(len(g)), int(w.sum())] + vals)
    return out


def export(season: int) -> int:
    out = build(season)
    ids = set(out["rows"]) | set(out["opp"])
    out["ngs"] = ngs(ids); out["ngs_cols"] = {k: [lab for _, lab in v[2]] for k, v in NGS.items()}; out["ngs_vol"] = {"pass": "attempts", "rec": "targets", "rush": "carries"}
    txt = "window.PSPLITS=" + json.dumps(out, separators=(",", ":")) + ";"
    WEB.mkdir(parents=True, exist_ok=True); (WEB / "player_splits.js").write_text(txt)
    return len(txt)


if __name__ == "__main__":
    games = pd.read_parquet(OUT / "games.parquet")
    n = export(int(games.season.max())); print("player_splits.js", round(n / 1e6, 2), "MB")
