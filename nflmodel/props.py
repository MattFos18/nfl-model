"""Player against scheme, matchup projections and the props track record (23 Sep 2026).

From data/processed/scheme_plays.parquet (every play since 2016 with the participation and FTN tags): each QB,
receiver and rusher's numbers over his last WINDOW games, split by the looks he faced (man, zone, pressure, clean,
blitz, light and heavy boxes), and each defense's allowed numbers and mix over its last WINDOW games. For every
game of the current week, each player's projected volume and yards against that defense, by the rule three rounds
of walk-forward backtest chose (experiments/props_backtest.py, props_backtest2.py, props_backtest3.py and their
reports; 2019 to 2025 on both windows, every constant fitted on 2016 to 2018 only):
  volume:   the team's pass plays (or runs, or dropbacks) per game over its last 17, moved by the game script (a
            fitted line on the closing spread and total: favourites run more and pass less, high totals add pass
            plays; GS), shared among the players who are playing in proportion to their usage share, where usage
            is decayed by DECAY per game back so the current role counts most (an absent player's targets go to
            his teammates)
  rate:     the player's yards per touch shrunk toward the league's with K touches of weight (receivers 100 targets,
            rushers 25 carries, QBs 50 dropbacks), then moved W of the way toward what the defense allows per touch
            relative to the league (receivers 0.25, rushers 0.25, QBs 0.5)
  line:     volume x rate x MED, the median factor: yards in a game are right-skewed, so the line that is off by
            least sits below the mean, as a book's over/under does. The mean is kept beside it.
  counts:   receptions = targets x catch rate shrunk toward the league (K_CATCH) x MED_CATCH; touchdowns = volume x
            his rate shrunk toward the league (K_TD), receiving and passing scores moved TD_MARGIN per point of
            expected margin; interceptions = dropbacks x the league rate (his own rate carried no information).
            Chosen in round 5 by absolute error (receptions) and Poisson log loss (scores, picks) on both windows
  team:     each team's players are then moved part of the way (RECON_W) toward what the game model expects of the
            team: its expected points (the game model's own, priced before the game) give the team's expected
            receiving, rushing and passing yards and touchdowns (TEAM_FIT), and every player's line is scaled by
            the ratio of that to what the players add up to (round 6: helps every stat on both windows, passing
            yards by three yards; the game model's margin in place of the closing line changed nothing)
  defense:  each team's defenders too (round 7): tackles plus assists = his decayed share of the team's tackles x the
            team's tackles per play faced x the opponent's plays with the game script x DEF_MED; sacks = his rate per
            play faced shrunk toward the league (K_SACK), x the opponent's plays
  passing:  the team's dropbacks are blended PACE (a quarter) toward what the opponent has allowed per game, and the
            line is cut WIND_C per mph of wind above 10 at kickoff once a forecast is usable (round 4: both helped
            passing yards on both windows; for receiving and rushing every round-4 layer was inside the noise)
The look-by-look splits (man/zone, box, pressure), routes, coverage-specific usage, defense by position and the
coach's pass rate are shown as readings only: projecting with them was worse than not on both windows.
Projections are readings and get graded every run against what happened (data/tracker/props_graded.csv), and
against the closing book line where one was logged (nflmodel/props_lines.py; data/tracker/props_vs_market.csv: the
side the projection took, the result, and the book's own error beside ours), so they build a record before anyone
bets on them. Nothing here feeds the game model.
Usage: python -m nflmodel.props   writes data/processed/props.json, reports/props_<season>_wk<week>.csv and .md, grades last week"""
from __future__ import annotations
import json
import numpy as np, pandas as pd
from .features import RAW, OUT, ROOT
WINDOW, MIN_SPLIT, MIN_VOL = 17, 15, 8
K = {"rec": 100.0, "rush": 25.0, "pass": 50.0}       # touches of league-average weight the player's rate is shrunk with (backtest, 23 Sep 2026)
W = {"rec": 0.25, "rush": 0.25, "pass": 0.5}         # weight toward what the defense allows per touch, relative to the league
DEF_WEIGHT = W["rec"]                                # kept for the page's note
DECAY = 0.85                                         # usage share: weight per game back (0.85 beat 0.90 and flat on both windows, round 3)
GS_TOTAL = 43.5674                                   # league mean closing total the game-script line is centred on (all games in games.parquet)
GS = {"rec": (-0.5969, -0.046, 0.1636), "rush": (0.3413, 0.103, -0.1713), "pass": (-0.5967, -0.0461, 0.1638)}   # plays per game beyond the team's last-17 average: intercept, per point of expected margin, per point of total above GS_TOTAL; least squares on 2016 to 2018 (pass plays, runs, dropbacks)
MED = {"rec": 0.81, "rush": 0.84, "pass": 0.88}      # median factor on the yards line. Rushing 0.84 fitted on 2016 to 2018 in round 3; receiving and passing refit on 2017-18 with today's rule in round 11 (the round-3 values 0.88 and 0.90 had gone stale as rounds 4 to 10 changed the rule under them; reports/props_backtest11.csv, better on both windows)   # 24 Sep 2026: passing refit to 0.88 (and TEAM_FIT pass yds to 100.83 + 6.379 x exp pts) once passing yards became gross, the yards the books settle on (experiments/props_official.py)
K_CATCH, MED_CATCH = 25.0, 0.9                     # catch rate shrunk toward the league with 25 targets of weight (round 5); receptions line x 0.9, refit on 2017-18 in round 11 (was 0.88; reports/props_backtest11.csv, better on both windows)
K_TD = {"rec": 200.0, "rush": 200.0, "pass": 400.0}  # touchdown rate per touch shrunk toward the league (round 5: best Poisson fit on 2016 to 2018, held on both windows)
TD_MARGIN = {"rec": 0.020, "rush": 0.0, "pass": 0.020}   # touchdown rate x (1 + TD_MARGIN x expected margin): favourites score more; fitted on 2016 to 2018 (rushing: no gain on both windows, so 0)
BACKTEST_COUNTS = {'rec_catches': [1.43, 1.35], 'rec_td_ll': [0.5094, 0.4857], 'rush_td_ll': [0.5771, 0.5483], 'pass_td_ll': [1.464, 1.4225], 'pass_int_ll': [1.1454, 1.103]}   # the same run: receptions mean absolute error, touchdown and interception Poisson log loss, 2019-22 / 2023-25 (reports/props_by_season.csv)
RECON_W = {"rec": {"yds": 0.25, "td": 0.5}, "rush": {"yds": 0.25, "td": 0.5}, "pass": {"yds": 0.5, "td": 1.0}}   # round 6: weight of the move toward the team's expected yards and touchdowns from the game model's expected points (best row on both windows per stat)
TEAM_FIT = {"rec": {"td": (-0.2529, 0.07481), "yds": (86.16, 6.483)}, "rush": {"td": (-0.1856, 0.04091), "yds": (71.47, 1.388)}, "pass": {"td": (-0.2618, 0.079), "yds": (100.83, 6.379)}}   # team touchdowns and yards of each kind = intercept + slope x the game model's expected points, least squares on 2016 to 2018 (reports/props_backtest6.csv, *_team_fit rows)
PROP_EDGE = None   # {"rec_yards": 7.5, ...}: the edge (projection minus book line, absolute) at which a prop is flagged, per stat; None until reports/props_vs_market_cuts.csv chooses one that holds on both windows (experiments/props_vs_market_backtest.py). No cut, no flags.
DEF_DECAY, DEF_MED, K_SACK = 0.85, 0.90, 300.0         # round 7 (reports/props_backtest7.csv): tackles = his decayed share of the team's tackles x the team's tackles per play faced x the opponent's plays with the game script, x 0.90; sacks = his rate per play faced shrunk toward the league with 300 plays of weight (best Poisson fit both windows)
BACKTEST_DEF = {"def_tackles": [1.648, 1.633], "def_sacks_ll": [0.3813, 0.3887]}   # tk_85gs_med and sk_K300 in props_backtest7.csv
LONGEST = {"rec": (6.9084, 0.3362, 0.1291, 0.84), "rush": (6.9330, 0.1545, 0.1153, 0.78), "pass": (16.3327, 0.2340, 0.0547, 0.92)}   # round 8 (reports/props_backtest8.csv, l_blend_med): longest gain of the game = median factor x (a + b x his game-longest decayed 0.85 per game back + c x his yards per game); fitted on 2016 to 2018
BACKTEST_LONGEST = {"rec_longest": [9.256, 9.274], "rush_longest": [7.575, 7.309], "pass_longest": [11.803, 11.686]}   # l_blend_med in props_backtest8.csv
FADE = {"rec": (0.5, 0.5), "rush": (0.25, 0.5)}   # round 10 (reports/props_backtest10.csv): the usage share's weights take an extra factor across a season boundary and across a change of team (last year's role counts for less in September); no redistribution of an absent player's share (every form of it lost on both windows)
KICK = {"pts": (2.4861, 0.1843, 0.1489), "fgm": (1.0165, 0.1757, 0.0155)}   # round 9 (reports/props_backtest9.csv, k_blend_team and g_blend_team): kicking points = a + b x his team's kicking points per game decayed 0.85 + c x the team's implied total ((closing total + expected margin) / 2); field goals made the same; fitted on 2016 to 2018
BACKTEST_KICK = {"kick_points": [2.832, 2.925], "field_goals": [0.969, 1.001]}   # k_blend_team and g_blend_team in props_backtest9.csv
PACE = {"rec": 0.0, "rush": 0.0, "pass": 0.25}       # weight on the opponent's allowed plays per game in the team's volume (round 4: helps passing on both windows, nothing on the others)
WIND_C = {"rec": 0.0, "rush": 0.0, "pass": -0.005}   # yards line x (1 + WIND_C x mph of wind above 10 at kickoff), fitted on 2016 to 2018 (round 4: passing only)
BACKTEST = {'rec_yards': [19.31, 18.28], 'rush_yards': [17.86, 17.04], 'pass_yards': [56.6, 56.38]}   # mean absolute error per player-game, 2019-22 / 2023-25, of the adopted rule run walk-forward with league averages as of each game (reports/props_by_season.csv; round 11 factors). The rounds chose the constants with a league average over every season, a small look-ahead: removing it moves the errors by at most 0.05 yards (23 Sep 2026)
TR, REP = ROOT / "data" / "tracker", ROOT / "reports"


def _asof(d: pd.DataFrame, season: int, week: int) -> pd.DataFrame:
    return d[((d.season < season) | ((d.season == season) & (d.week < week))) & (d.season >= season - 1)]


def _last(g: pd.DataFrame, n: int = WINDOW) -> pd.DataFrame:
    ids = g.drop_duplicates("game_id").sort_values(["season", "week"]).game_id.tail(n)
    return g[g.game_id.isin(ids)]


def _stat(x: pd.DataFrame, min_n: int) -> dict | None:
    if len(x) < min_n:
        return None
    return {"n": int(len(x)), "epa": round(float(x.epa.mean()), 3), "yds": round(float(x.yards_gained.fillna(0).mean()), 2), "success": round(float(x.success.mean()), 3)}


def _longest(g_all: pd.DataFrame, g: pd.DataFrame, kind: str) -> dict:
    """His longest gain of the game (completed passes for receivers and passers, runs for rushers; 0 when none),
    decayed DECAY per game back over the as-of frame, and his yards per game over the window: the two inputs of the
    round-8 line. Returns the projected line too."""
    lg = g_all.yards_gained.fillna(0.0) if kind == "rush" else g_all.yards_gained.fillna(0.0).where(g_all.complete_pass.fillna(0).eq(1), 0.0)
    per = lg.groupby([g_all.season, g_all.week, g_all.game_id]).max().reset_index().sort_values(["season", "week"], ascending=False)
    wts = DECAY ** np.arange(len(per)); dec = float((per.iloc[:, -1].values * wts).sum() / wts.sum()) if len(per) else 0.0
    ypg = float(g.yards_gained.fillna(0).sum() / max(g.game_id.nunique(), 1)); a, b, c, med = LONGEST[kind]
    return {"longest_dec": round(dec, 2), "ypg": round(ypg, 2), "proj_longest": round(med * (a + b * dec + c * ypg), 1)}


def _share(g: pd.DataFrame, team_by_game: pd.Series, kind: str = "rec") -> float:
    """His plays over his teams' plays in the same games, both decayed by DECAY per game back from his most recent
    game, over every game in the as-of frame (a player traded in keeps the usage he had elsewhere), with the round-10
    fade: an extra factor on every game before a season boundary and before a change of team."""
    pairs = g.groupby(["game_id", "posteam", "season", "week"]).size().reset_index(name="n").sort_values(["season", "week"], ascending=False)
    sf, tf = FADE.get(kind, (1.0, 1.0)); sn = pairs.season.values; tm = pairs.posteam.values
    sc = np.cumsum(np.r_[0, sn[1:] != sn[:-1]]) if len(pairs) else np.array([]); tc = np.cumsum(np.r_[0, tm[1:] != tm[:-1]]) if len(pairs) else np.array([])
    wts = DECAY ** np.arange(len(pairs)) * sf ** sc * tf ** tc
    mine = float((pairs.n.values * wts).sum())
    tot = float(sum(w * team_by_game.get((r.game_id, r.posteam), 0) for w, r in zip(wts, pairs.itertuples())))
    return mine / tot if tot else 0.0


def game_script(kind: str, per_game: float, margin: float | None, total: float | None, opp_allowed: float | None = None) -> float:
    """The team's plays of this kind expected in this game: its last-17 average (blended PACE of the way toward what
    the opponent has allowed per game) plus the fitted game-script line (expected margin from the closing spread,
    from the team's side; total above the league mean). Missing lines count as zero, as in the backtest."""
    b = GS[kind]
    me = 0.0 if margin is None or pd.isna(margin) else float(margin)
    tc = 0.0 if total is None or pd.isna(total) else float(total) - GS_TOTAL
    if PACE[kind] and opp_allowed is not None and not pd.isna(opp_allowed):
        per_game = (1 - PACE[kind]) * per_game + PACE[kind] * float(opp_allowed)
    return max(per_game + b[0] + b[1] * me + b[2] * tc, 0.0)


def wind_factor(kind: str, wind: float | None) -> float:
    """1 + WIND_C x mph above 10 at kickoff; 1 when the wind is unknown (domes, no forecast yet), as in the backtest."""
    if wind is None or pd.isna(wind) or not WIND_C[kind]:
        return 1.0
    return 1 + WIND_C[kind] * max(float(wind) - 10.0, 0.0)


def official(d: pd.DataFrame) -> pd.DataFrame:
    """The charted plays on the official box score's terms (24 Sep 2026, checked against nflverse's player stats):
    a kneel-down is a run (a carry by the QB), a spike is a pass attempt and nothing else, two-point tries are not
    plays (dropped in scheme.load_plays). Passing yards per dropback use pass_yds, the yards on completions: a
    sack's lost yards are not passing yards, and the books settle passing yards gross."""
    d = d[d.play_type.isin(["pass", "run", "qb_kneel", "qb_spike"])].copy()
    d.loc[d.play_type.eq("qb_kneel"), "play_type"] = "run"
    spk = d.play_type.eq("qb_spike"); d.loc[spk, "pass_play"] = False; d.loc[spk, "dropback"] = False
    return d


def receivers(d: pd.DataFrame, names: dict) -> dict:
    out = {}
    t = d[d.pass_play & d.receiver_player_id.notna()]
    team_pass = t.groupby(["game_id", "posteam"]).size()
    for pid, g in t.groupby("receiver_player_id"):
        if names.get(pid, ("", ""))[1] == "QB":
            continue
        g_all = g; g = _last(g); tgt = len(g)
        if tgt < MIN_VOL:
            continue
        team = g.sort_values(["season", "week"]).posteam.iloc[-1]
        share = _share(g_all, team_pass, "rec")
        out[pid] = {"name": names.get(pid, (pid, ""))[0], "pos": names.get(pid, ("", ""))[1], "team": team, "games": int(g.game_id.nunique()), "targets": int(tgt), "targets_pg": round(tgt / g.game_id.nunique(), 2), "share": round(share, 3),
                    "catch": round(float(g.complete_pass.fillna(0).mean()), 3), "ypt": round(float(g.yards_gained.fillna(0).mean()), 2), "epa_pt": round(float(g.epa.mean()), 3), "adot": (round(float(g.air_yards.mean()), 1) if g.air_yards.notna().any() else None),
                    "td_pt": round(float(g.pass_touchdown.fillna(0).mean()), 3), "vs_man": _stat(g[g.man], MIN_SPLIT), "vs_zone": _stat(g[g.zone], MIN_SPLIT), "vs_blitz": _stat(g[g.blitz == 1], MIN_SPLIT), "vs_press": _stat(g[g.pressure == 1], MIN_SPLIT), **_longest(g_all, g, "rec")}
    return out


def rushers(d: pd.DataFrame, names: dict) -> dict:
    out = {}
    t = d[d.play_type.eq("run") & d.rusher_player_id.notna()]
    team_run = t.groupby(["game_id", "posteam"]).size()
    for pid, g in t.groupby("rusher_player_id"):
        g_all = g; g = _last(g); n = len(g)
        if n < MIN_VOL:
            continue
        team = g.sort_values(["season", "week"]).posteam.iloc[-1]
        out[pid] = {"name": names.get(pid, (pid, ""))[0], "pos": names.get(pid, ("", ""))[1], "team": team, "games": int(g.game_id.nunique()), "carries": int(n), "carries_pg": round(n / g.game_id.nunique(), 2), "share": round(_share(g_all, team_run, "rush"), 3),
                    "ypc": round(float(g.yards_gained.fillna(0).mean()), 2), "epa_pc": round(float(g.epa.mean()), 3), "success": round(float(g.success.mean()), 3), "td_pc": round(float(g.rush_touchdown.fillna(0).mean()), 3),
                    "light": _stat(g[g.box <= 6], MIN_SPLIT), "heavy": _stat(g[g.box >= 8], MIN_SPLIT), "mid": _stat(g[g.box == 7], MIN_SPLIT), **_longest(g_all, g, "rush")}
    return out


def passers(d: pd.DataFrame, names: dict) -> dict:
    out = {}
    t = d[d.dropback & d.passer_player_id.notna()]
    for pid, g in t.groupby("passer_player_id"):
        g_all = g[g.pass_play]; g = _last(g); n = len(g)
        if n < MIN_VOL * 3:
            continue
        team = g.sort_values(["season", "week"]).posteam.iloc[-1]
        out[pid] = {"name": names.get(pid, (pid, ""))[0], "pos": names.get(pid, ("", ""))[1], "team": team, "games": int(g.game_id.nunique()), "dropbacks": int(n), "dropbacks_pg": round(n / g.game_id.nunique(), 1),
                    "epa_db": round(float(g.epa.mean()), 3), "ypd": round(float(g.pass_yds.mean()), 2), "sack_rate": round(float(g.sack.fillna(0).mean()), 3), "td_db": round(float(g.pass_touchdown.fillna(0).mean()), 3), "int_db": round(float(g.interception.fillna(0).mean()), 3),
                    "att_rate": round(float(g.pass_play.mean()), 3), "comp": round(float(g[g.pass_att].complete_pass.fillna(0).mean()), 3) if g.pass_att.any() else None,
                    "press": _stat(g[g.pressure == 1], MIN_SPLIT), "clean": _stat(g[g.pressure == 0], MIN_SPLIT), "blitz": _stat(g[g.blitz == 1], MIN_SPLIT), "noblitz": _stat(g[g.blitz == 0], MIN_SPLIT), "vs_man": _stat(g[g.man], MIN_SPLIT), "vs_zone": _stat(g[g.zone], MIN_SPLIT), **_longest(g_all, g[g.pass_play], "pass")}
    return out


def defenses(d: pd.DataFrame) -> dict:
    out = {}
    for team, g in d.groupby("defteam"):
        g = _last(g); ps = g[g.pass_play]; db = g[g.dropback]; run = g[g.play_type.eq("run")]; cv = ps[ps.cov_known]
        out[team] = {"games": int(g.game_id.nunique()), "ypt_allowed": round(float(ps.yards_gained.fillna(0).mean()), 2), "epa_pt_allowed": round(float(ps.epa.mean()), 3), "catch_allowed": round(float(ps.complete_pass.fillna(0).mean()), 3),
                     "ypc_allowed": round(float(run.yards_gained.fillna(0).mean()), 2), "epa_pc_allowed": round(float(run.epa.mean()), 3), "ypd_allowed": round(float(db[db.passer_player_id.notna()].pass_yds.mean()), 2),
                     "man": (round(float(cv.man.mean()), 3) if len(cv) >= 50 else None), "pressure": (round(float(db.pressure.mean()), 3) if db.pressure.notna().sum() >= 50 else None), "blitz": (round(float(db.blitz.mean()), 3) if db.blitz.notna().sum() >= 50 else None),
                     "heavy_box": (round(float((run.box >= 8).mean()), 3) if run.box.notna().sum() >= 30 else None), "light_box": (round(float((run.box <= 6).mean()), 3) if run.box.notna().sum() >= 30 else None),
                     "pass_plays_pg": round(len(ps) / max(g.game_id.nunique(), 1), 1), "runs_pg": round(len(run) / max(g.game_id.nunique(), 1), 1), "dropbacks_pg": round(len(db) / max(g.game_id.nunique(), 1), 1)}
    return out


def teams_volume(d: pd.DataFrame) -> dict:
    out = {}
    for team, g in d.groupby("posteam"):
        g = _last(g); n = max(g.game_id.nunique(), 1)
        out[team] = {"pass_plays_pg": round(float(g.pass_play.sum()) / n, 1), "runs_pg": round(float(g.play_type.eq("run").sum()) / n, 1), "dropbacks_pg": round(float(g.dropback.sum()) / n, 1)}
    return out


def league_baselines(d: pd.DataFrame) -> dict:
    ps = d[d.pass_play]; run = d[d.play_type.eq("run")]; db = d[d.dropback]; pdb = db[db.passer_player_id.notna()]; att = d[d.pass_att]   # pdb: the dropbacks a passer's own rates are counted on (scrambles are his runs)
    tg = ps[ps.receiver_player_id.notna()]
    return {"ypt": round(float(ps.yards_gained.fillna(0).mean()), 2), "epa_pt": round(float(ps.epa.mean()), 3), "catch": round(float(tg.complete_pass.fillna(0).mean()), 4), "ypc": round(float(run.yards_gained.fillna(0).mean()), 2), "ypd": round(float(pdb.pass_yds.mean()), 2),
            "td_pt": round(float(tg.pass_touchdown.fillna(0).mean()), 4), "td_pc": round(float(run.rush_touchdown.fillna(0).mean()), 4), "td_db": round(float(pdb.pass_touchdown.fillna(0).mean()), 4), "int_db": round(float(pdb.interception.fillna(0).mean()), 4),
            "comp_pp": round(float(att.complete_pass.fillna(0).mean()), 4), "att_rate": round(float(db.pass_play.mean()), 4),
            "man": round(float(ps[ps.cov_known].man.mean()), 3) if ps.cov_known.any() else None, "pressure": (round(float(db.pressure.mean()), 3) if db.pressure.notna().any() else None), "heavy_box": (round(float((run.box >= 8).mean()), 3) if run.box.notna().any() else None)}


TACKLE_COLS = ["solo_tackle_1_player_id", "solo_tackle_2_player_id", "assist_tackle_1_player_id", "assist_tackle_2_player_id", "assist_tackle_3_player_id", "assist_tackle_4_player_id", "tackle_with_assist_1_player_id", "tackle_with_assist_2_player_id"]


def defender_games(seasons=range(2016, 2027), force: bool = False) -> pd.DataFrame:
    """One row per defender and game from the raw play-by-play: tackles plus assists as the books count them (every
    solo, assist and tackle-with-assist credit), solo tackles, sacks (half sacks as 0.5), interceptions, passes
    defended, and the offense's plays he was on the field against (the team's plays faced). Cached in
    data/processed/def_games.parquet; rebuilt when the newest season's play-by-play is newer than the cache."""
    out = OUT / "def_games.parquet"; files = [RAW / "pbp" / f"play_by_play_{s}.parquet" for s in seasons]; files = [f for f in files if f.exists()]
    if out.exists() and not force and out.stat().st_mtime >= max(f.stat().st_mtime for f in files):
        return pd.read_parquet(out)
    rows = []
    for f in files:
        cols = ["season", "week", "game_id", "posteam", "defteam", "play_type", "sack_player_id", "half_sack_1_player_id", "half_sack_2_player_id", "interception_player_id", "pass_defense_1_player_id", "pass_defense_2_player_id"] + TACKLE_COLS
        d = pd.read_parquet(f, columns=cols); d = d[d.play_type.isin(["pass", "run"]) & d.defteam.notna()]
        plays = d.groupby(["season", "week", "game_id", "defteam"]).size().rename("plays_faced").reset_index()
        parts = []
        for c in TACKLE_COLS: parts.append(d[["season", "week", "game_id", "defteam", c]].rename(columns={c: "pid"}).dropna().assign(tk=1.0, solo=float(c.startswith("solo")), sack=0.0, int_=0.0, pd_=0.0))
        parts.append(d[["season", "week", "game_id", "defteam", "sack_player_id"]].rename(columns={"sack_player_id": "pid"}).dropna().assign(tk=0.0, solo=0.0, sack=1.0, int_=0.0, pd_=0.0))
        for c in ["half_sack_1_player_id", "half_sack_2_player_id"]: parts.append(d[["season", "week", "game_id", "defteam", c]].rename(columns={c: "pid"}).dropna().assign(tk=0.0, solo=0.0, sack=0.5, int_=0.0, pd_=0.0))
        parts.append(d[["season", "week", "game_id", "defteam", "interception_player_id"]].rename(columns={"interception_player_id": "pid"}).dropna().assign(tk=0.0, solo=0.0, sack=0.0, int_=1.0, pd_=0.0))
        for c in ["pass_defense_1_player_id", "pass_defense_2_player_id"]: parts.append(d[["season", "week", "game_id", "defteam", c]].rename(columns={c: "pid"}).dropna().assign(tk=0.0, solo=0.0, sack=0.0, int_=0.0, pd_=1.0))
        t = pd.concat(parts).groupby(["season", "week", "game_id", "defteam", "pid"]).agg(tackles=("tk", "sum"), solo=("solo", "sum"), sacks=("sack", "sum"), ints=("int_", "sum"), pd=("pd_", "sum")).reset_index().merge(plays, on=["season", "week", "game_id", "defteam"])
        rows.append(t)
    g = pd.concat(rows, ignore_index=True); g.to_parquet(out, index=False); return g


def kicker_games(seasons) -> pd.DataFrame:
    """One row per kicker and game from the raw play-by-play: field goals made and tried, extra points made and tried,
    kicking points (3 x field goals + extra points)."""
    parts = []
    for sn in seasons:
        f = RAW / "pbp" / f"play_by_play_{sn}.parquet"
        if not f.exists(): continue
        p = pd.read_parquet(f, columns=["game_id", "season", "week", "posteam", "field_goal_attempt", "field_goal_result", "extra_point_attempt", "extra_point_result", "kicker_player_id"])
        k = p[((p.field_goal_attempt == 1) | (p.extra_point_attempt == 1)) & p.kicker_player_id.notna()].copy()
        k["fgm"] = (k.field_goal_result == "made").astype(float); k["fga"] = (k.field_goal_attempt == 1).astype(float); k["xpm"] = (k.extra_point_result == "good").astype(float); k["xpa"] = (k.extra_point_attempt == 1).astype(float)
        parts.append(k.groupby(["game_id", "season", "week", "posteam", "kicker_player_id"]).agg(fgm=("fgm", "sum"), fga=("fga", "sum"), xpm=("xpm", "sum"), xpa=("xpa", "sum")).reset_index())
    if not parts: return pd.DataFrame(columns=["game_id", "season", "week", "team", "player_id", "fgm", "fga", "xpm", "xpa", "pts"])
    kg = pd.concat(parts, ignore_index=True).rename(columns={"posteam": "team", "kicker_player_id": "player_id"}); kg["pts"] = 3 * kg.fgm + kg.xpm
    return kg


def kickers(kg: pd.DataFrame, names: dict, season: int, week: int) -> dict:
    """Per team as of (season, week): kicking points and field goals per game decayed DECAY per game back over the
    team's games (the round-9 inputs), and each kicker's own line for the card."""
    a = kg[((kg.season < season) | ((kg.season == season) & (kg.week < week))) & (kg.season >= season - 1)]
    teams = {}
    for team, g in a.groupby("team"):
        per = g.groupby(["season", "week", "game_id"]).agg(pts=("pts", "sum"), fgm=("fgm", "sum"), fga=("fga", "sum")).reset_index().sort_values(["season", "week"], ascending=False)
        w = DECAY ** np.arange(len(per)); teams[team] = {"pts_dec": round(float((per.pts.values * w).sum() / w.sum()), 2), "fgm_dec": round(float((per.fgm.values * w).sum() / w.sum()), 3), "games": int(len(per))}
    players = {}
    for pid, g in a.groupby("player_id"):
        g = g.sort_values(["season", "week"]).tail(WINDOW); n = int(len(g))
        players[pid] = {"name": names.get(pid, (pid, ""))[0], "team": g.team.iloc[-1], "games": n, "pts_pg": round(float(g.pts.sum() / n), 2), "fgm": int(g.fgm.sum()), "fga": int(g.fga.sum()), "fg_pct": (round(float(g.fgm.sum() / g.fga.sum()), 3) if g.fga.sum() else None), "xpm": int(g.xpm.sum()), "xpa": int(g.xpa.sum())}
    return {"teams": teams, "players": players}


def project_kicker(team: str, KK: dict, roster: pd.DataFrame, margin: float | None, total: float | None, mk: pd.DataFrame | None) -> list:
    """The team's kicker (the roster's K) by the round-9 rule: his team's decayed kicking rate and the implied total."""
    ro = roster[(roster.team == team) & (roster.position == "K")] if len(roster) and "position" in roster else pd.DataFrame()
    tm = KK["teams"].get(team); me = 0.0 if margin is None or pd.isna(margin) else float(margin); tt = ((GS_TOTAL if total is None or pd.isna(total) else float(total)) + me) / 2
    OUT_WORDS = ("Out", "Doubtful", "IR", "PUP", "Suspended", "Exempt", "NFI", "Retired", "not on roster")
    rows = []
    for r in ro.itertuples():
        if tm is None: break
        st = (r.roster if isinstance(r.roster, str) and r.roster != "Active" else (r.report if isinstance(r.report, str) else "")) or ""; is_out = any(st.startswith(w) for w in OUT_WORDS)
        p = KK["players"].get(r.player_id, {"name": r.name, "games": 0, "pts_pg": None, "fgm": 0, "fga": 0, "fg_pct": None, "xpm": 0, "xpa": 0})
        a, b, c = KICK["pts"]; pts = a + b * tm["pts_dec"] + c * tt; a2, b2, c2 = KICK["fgm"]; fgm = a2 + b2 * tm["fgm_dec"] + c2 * tt
        rows.append({"player_id": r.player_id, "name": p["name"], "pos": "K", "status": st, "out": is_out, "games": p["games"], "pts_pg": p["pts_pg"], "fgm": p["fgm"], "fga": p["fga"], "fg_pct": p["fg_pct"], "xpm": p["xpm"], "xpa": p["xpa"],
                     "team_pts_dec": tm["pts_dec"], "team_fgm_dec": tm["fgm_dec"], "team_games": tm["games"], "implied_total": round(tt, 2), "proj_kick_points": round(pts, 1), "proj_field_goals": round(fgm, 2)})
    rows.sort(key=lambda r: (r["out"], -(r["games"] or 0)))
    rows = rows[:1]; attach_all_markets(rows, mk)
    return rows


def defenders(dg: pd.DataFrame, names: dict, season: int, week: int) -> dict:
    """Every defender's profile as of the week from the defender game table: last-17 tackles a game, solo, sacks,
    interceptions, passes defended; his decayed share of his team's tackles; the team's tackles per play faced."""
    a = dg[((dg.season < season) | ((dg.season == season) & (dg.week < week))) & (dg.season >= season - 1)].copy()
    tm = a.groupby(["defteam", "season", "week", "game_id"]).agg(team_tk=("tackles", "sum")).reset_index(); a = a.merge(tm, on=["defteam", "season", "week", "game_id"])
    tpp = {}
    for t, g in a.groupby("defteam"):
        gg = g.drop_duplicates("game_id").sort_values(["season", "week"]).tail(WINDOW); tpp[t] = round(float(gg.team_tk.sum() / max(gg.plays_faced.sum(), 1)), 3)
    out = {}
    for pid, g in a.groupby("pid"):
        g = g.sort_values(["season", "week"]); last = g.tail(WINDOW)
        if len(last) < 3: continue
        w = DEF_DECAY ** np.arange(len(g))[::-1]; share = float((g.tackles * w).sum() / max((g.team_tk * w).sum(), 1e-9))
        n = int(len(last)); team = g.defteam.iloc[-1]
        out[pid] = {"name": names.get(pid, (pid, ""))[0], "pos": names.get(pid, ("", ""))[1], "team": team, "games": n, "tackles_pg": round(float(last.tackles.mean()), 2), "solo_pg": round(float(last.solo.mean()), 2), "sacks_pg": round(float(last.sacks.mean()), 2), "ints": int(last.ints.sum()), "pd": int(last.pd.sum()),
                    "share": round(share, 3), "sack_rate": round(float(last.sacks.sum() / max(last.plays_faced.sum(), 1)), 4), "faced": int(last.plays_faced.sum()), "team_tpp": tpp.get(team)}
    lg_sack = round(float(a.sacks.sum() / max(a.plays_faced.sum(), 1)), 5)
    return {"players": out, "league_sack_rate": lg_sack}


def project_defense(team: str, opp: str, DF: dict, V: dict, roster: pd.DataFrame, margin: float | None, total: float | None, mk: pd.DataFrame | None, VS: dict | None) -> list:
    """The team's defenders against the opponent's offense: tackles plus assists and sacks, by the round-7 rule."""
    ro = roster[roster.team == team].set_index("player_id") if len(roster) else pd.DataFrame(); ov = V.get(opp, {})
    om = None if margin is None or pd.isna(margin) else -float(margin)   # the opponent's expected margin
    opp_plays = game_script("rec", ov.get("pass_plays_pg", 0), om, total) + game_script("rush", ov.get("runs_pg", 0), om, total)
    OUT_WORDS = ("Out", "Doubtful", "IR", "PUP", "Suspended", "Exempt", "NFI", "Retired", "not on roster")
    rows = []
    for pid, p in DF["players"].items():
        if p["team"] != team or pid not in ro.index: continue
        r = ro.loc[pid]; st = (r.roster if isinstance(r.roster, str) and r.roster != "Active" else (r.report if isinstance(r.report, str) else "")) or ""; is_out = any(st.startswith(w) for w in OUT_WORDS)
        tk = p["share"] * (p["team_tpp"] or 0.95) * opp_plays; sk = (p["sack_rate"] * p["faced"] + K_SACK * DF["league_sack_rate"]) / (p["faced"] + K_SACK) * opp_plays
        hist = (VS or {}).get(("def", pid, opp))
        rows.append({"player_id": pid, "name": p["name"], "pos": p["pos"], "status": st, "out": is_out, "tackles_pg": p["tackles_pg"], "solo_pg": p["solo_pg"], "share": p["share"], "games": p["games"], "sacks_pg": p["sacks_pg"], "ints": p["ints"], "pd": p["pd"],
                     "proj_tackles_mean": round(tk, 1), "proj_tackles": round(tk * DEF_MED, 1), "proj_solo_tackles": round(tk * DEF_MED * (p["solo_pg"] / p["tackles_pg"] if p["tackles_pg"] else 0.6), 1), "proj_sacks": round(sk, 2), "opp_plays": round(opp_plays, 1), "vs_opp": vs_summary(hist)})
    rows.sort(key=lambda r: (r["out"], -r["proj_tackles"]))
    attach_market(rows, mk, [("def_tackles", "mkt_tackles")])
    rows = rows[:8]; attach_all_markets(rows, mk)
    return rows


def vs_defense(d: pd.DataFrame) -> dict:
    """Every player's games against each defense since 2016: {(kind, player, defteam): [{season, week, n, yds, td}, ...]},
    newest first. The card shows a player's record against the defense he faces this week."""
    out = {}
    for kind, mask, pcol, tdcol in [("rec", d.pass_play & d.receiver_player_id.notna(), "receiver_player_id", "pass_touchdown"), ("rush", d.play_type.eq("run") & d.rusher_player_id.notna(), "rusher_player_id", "rush_touchdown"), ("pass", d.dropback & d.passer_player_id.notna(), "passer_player_id", "pass_touchdown")]:
        t = d[mask]; g = t.groupby([pcol, "defteam", "season", "week"]).agg(n=("play_id", "count"), yds=("yards_gained", "sum"), td=(tdcol, "sum")).reset_index().sort_values(["season", "week"], ascending=False)
        for r in g.itertuples():
            out.setdefault((kind, getattr(r, pcol), r.defteam), []).append({"season": int(r.season), "week": int(r.week), "n": int(r.n), "yds": round(float(r.yds), 0), "td": int(r.td)})
    return out


def vs_offense(dg: pd.DataFrame, games: pd.DataFrame) -> dict:
    """Every defender's games against each offense: {("def", player, posteam): [{season, week, n (tackles), yds (sacks), td (ints)}, ...]}, newest first."""
    opp = games.set_index("game_id")[["home_team", "away_team"]]
    g = dg.merge(opp, left_on="game_id", right_index=True, how="inner"); g["opp"] = np.where(g.defteam == g.home_team, g.away_team, g.home_team)
    out = {}
    for r in g.sort_values(["season", "week"], ascending=False).itertuples():
        out.setdefault(("def", r.pid, r.opp), []).append({"season": int(r.season), "week": int(r.week), "n": int(r.tackles), "yds": float(r.sacks), "td": int(r.ints)})
    return out


def vs_summary(hist: list | None) -> dict | None:
    if not hist:
        return None
    n = len(hist)
    return {"games": n, "n_pg": round(sum(h["n"] for h in hist) / n, 1), "yds_pg": round(sum(h["yds"] for h in hist) / n, 1), "td": int(sum(h["td"] for h in hist)), "last": hist[:5]}


def _mix(a: dict | None, b: dict | None, rate: float | None, key: str, fallback: float) -> float:
    """a in look x rate + b outside it x (1 - rate), when both splits and the rate exist; else the fallback."""
    if a is None or b is None or rate is None:
        return fallback
    return a[key] * rate + b[key] * (1 - rate)


def _toward(v: float, allowed: float | None, league: float, w: float) -> float:
    return v if (allowed is None or not league) else v * (1 + w * (allowed / league - 1))


def _shrunk(rate: float, n: float, league: float, k: float) -> float:
    return (rate * n + k * league) / (n + k)


MARKET_LABEL = {"pass_yards": "Pass yds", "pass_td": "Pass TD", "pass_completions": "Completions", "pass_attempts": "Attempts", "pass_int": "INT thrown", "pass_longest": "Longest completion", "rush_yards": "Rush yds", "rush_attempts": "Rush att", "rush_rec_yards": "Rush + rec yds", "rush_longest": "Longest rush", "pass_rush_yards": "Pass + rush yds", "rec_targets": "Targets",
                "rec_catches": "Receptions", "rec_yards": "Rec yds", "rec_longest": "Longest rec", "anytime_td": "Anytime TD", "def_tackles": "Tackles + ast (defense)", "def_solo_tackles": "Solo tackles", "def_sacks": "Sacks", "def_int": "INT", "kick_points": "Kicking pts", "field_goals": "Field goals"}


def attach_all_markets(rows: list, mk: pd.DataFrame) -> set:
    """Every market the book posts for each listed player: [{stat, line, books, over, under}] on the row. Returns the
    keys matched, so the leftovers (kickers, players without a profile) can be listed on their own."""
    matched = set()
    if mk is None or not len(mk):
        for r in rows: r["markets"] = []
        return matched
    from .props_lines import norm_name
    for r in rows:
        k = norm_name(r["name"]); hit = mk[mk.key == k]; matched.add(k)
        r["markets"] = [{"stat": h.stat, "line": (None if pd.isna(h.line) else float(h.line)), "books": int(h.books), "over": (None if pd.isna(h.over_price) else int(h.over_price)), "under": (None if pd.isna(h.under_price) else int(h.under_price)), "open": (None if pd.isna(h.open_line) else float(h.open_line)), "open_over": (None if pd.isna(h.open_over) else int(h.open_over)), "pulls": int(h.pulls)} for h in hit.itertuples()]
    return matched


def attach_market(rows: list, mk: pd.DataFrame, pairs: list) -> None:
    """Put the closing book line beside each projection: pairs = [(stat in the log, key on the row)], matched on the
    player's normalised name. line, books and the prices; the anytime-touchdown price as an implied probability."""
    if mk is None or not len(mk):
        return
    from .props_lines import norm_name
    for r in rows:
        k = norm_name(r["name"])
        for stat, key in pairs:
            hit = mk[(mk.stat == stat) & (mk.key == k)]
            if not len(hit):
                continue
            h = hit.iloc[0]
            if stat == "anytime_td":
                p_ = h.over_price
                r["mkt_td_price"] = None if pd.isna(p_) else int(p_); r["mkt_td_prob"] = None if pd.isna(p_) else round(implied(p_), 3)
            else:
                r[key] = None if pd.isna(h.line) else float(h.line); r[key + "_books"] = int(h.books)
                cut = (PROP_EDGE or {}).get(stat); proj = r.get({"mkt_rec_yards": "proj_rec_yards", "mkt_catches": "proj_catches", "mkt_rush_yards": "proj_rush_yards", "mkt_pass_yards": "proj_pass_yards", "mkt_tackles": "proj_tackles"}[key])
                if cut is not None and proj is not None and not pd.isna(h.line) and abs(proj - float(h.line)) >= cut:
                    r[key + "_flag"] = "over" if proj > h.line else "under"


def implied(price: float) -> float:
    """American price -> implied probability, vig included."""
    price = float(price)
    return 100 / (price + 100) if price > 0 else -price / (-price + 100)


def reconcile(rows: list, kind: str, exp_pts: float | None, yds_key: str, td_key: str, starter_only: bool = False) -> dict:
    """Scale the players' yards and touchdowns toward the team's expected totals from the game model's expected points:
    factor = 1 + w x (expected / what the players add up to - 1), the ratio clipped to [0.5, 2] as in the backtest. The
    sum is over the players who are playing (the starter alone for passing); every row gets the factor, so a listed-out
    player's "would have" line moves with his team."""
    out = {"exp_pts": None if exp_pts is None or pd.isna(exp_pts) else round(float(exp_pts), 1), "yds_factor": 1.0, "td_factor": 1.0}
    if out["exp_pts"] is None or not rows:
        return out
    act = [r for r in rows if not r["out"]]; act = act[:1] if starter_only else act
    if not act:
        return out
    fy, ft = TEAM_FIT[kind]["yds"], TEAM_FIT[kind]["td"]; wy, wt = RECON_W[kind]["yds"], RECON_W[kind]["td"]
    exp_y, exp_t = fy[0] + fy[1] * exp_pts, ft[0] + ft[1] * exp_pts; sum_y, sum_t = sum(r[yds_key] for r in act), sum(r[td_key] for r in act)
    fac_y = 1 + wy * (min(max(exp_y / sum_y, 0.5), 2.0) - 1) if sum_y > 0 else 1.0; fac_t = 1 + wt * (min(max(exp_t / sum_t, 0.5), 2.0) - 1) if sum_t > 0 else 1.0
    for r in rows:
        r[yds_key] = round(r[yds_key] * fac_y, 1); r[yds_key + "_mean"] = round(r[yds_key + "_mean"] * fac_y, 1); r[td_key] = round(r[td_key] * fac_t, 3)
    out.update({"team_yds_exp": round(exp_y, 1), "team_yds_players": round(sum_y, 1), "yds_factor": round(fac_y, 3), "team_td_exp": round(exp_t, 2), "team_td_players": round(sum_t, 2), "td_factor": round(fac_t, 3)})
    return out


def project_game(team: str, opp: str, R: dict, RU: dict, Q: dict, D: dict, V: dict, L: dict, roster: pd.DataFrame, margin: float | None = None, total: float | None = None, wind: float | None = None, mk: pd.DataFrame | None = None, exp_pts: float | None = None, VS: dict | None = None, starter: str | None = None) -> dict:
    """One offense against one defense: every rostered receiver, rusher and QB with a profile, projected. margin is the
    team's expected margin from the closing spread (positive when favoured), total the closing total, wind the mph at
    kickoff (None in a dome or before a usable forecast), exp_pts the game model's expected points for the team."""
    dd = D.get(opp, {}); base = V.get(team, {}); ro = roster[roster.team == team].set_index("player_id") if len(roster) else pd.DataFrame()
    me = 0.0 if margin is None or pd.isna(margin) else float(margin)
    vol = dict(base); vol.update({"pass_plays": round(game_script("rec", base.get("pass_plays_pg", 0), margin, total, dd.get("pass_plays_pg")), 1), "runs": round(game_script("rush", base.get("runs_pg", 0), margin, total, dd.get("runs_pg")), 1), "dropbacks": round(game_script("pass", base.get("dropbacks_pg", 0), margin, total, dd.get("dropbacks_pg")), 1), "margin": (None if margin is None or pd.isna(margin) else float(margin)), "total": (None if total is None or pd.isna(total) else float(total)), "wind": (None if wind is None or pd.isna(wind) else float(wind)), "wind_factor_pass": round(wind_factor("pass", wind), 3)})
    def status(pid):
        if pid not in ro.index: return "not on roster"
        r = ro.loc[pid]; lab = r.roster if isinstance(r.roster, str) and r.roster != "Active" else (r.report if isinstance(r.report, str) else "")
        return lab or ""
    OUT_WORDS = ("Out", "Doubtful", "IR", "PUP", "Suspended", "Exempt", "NFI", "Retired", "not on roster")
    rec = []
    for pid, p in R.items():
        if p["team"] != team or pid not in ro.index: continue
        st = status(pid); is_out = any(st.startswith(w) for w in OUT_WORDS)
        ypt_s = _shrunk(p["ypt"], p["targets"], L["ypt"], K["rec"]); ypt = _toward(ypt_s, dd.get("ypt_allowed"), L["ypt"], W["rec"])
        ypt_mix = _mix(p["vs_man"], p["vs_zone"], dd.get("man"), "yds", p["ypt"])   # reading only
        catch_s = _shrunk(p["catch"], p["targets"], L["catch"], K_CATCH); td_s = _shrunk(p["td_pt"], p["targets"], L["td_pt"], K_TD["rec"]) * (1 + TD_MARGIN["rec"] * me)
        rec.append({"player_id": pid, "name": p["name"], "pos": p.get("pos", ""), "vs_opp": vs_summary((VS or {}).get(("rec", pid, opp))), "status": st, "out": is_out, "targets_pg": p["targets_pg"], "share": p["share"], "catch": p["catch"], "catch_shrunk": round(catch_s, 3), "td_pt": p["td_pt"], "td_pt_proj": round(td_s, 4),
                    "ypt": p["ypt"], "ypt_shrunk": round(ypt_s, 2), "ypt_mix": round(ypt_mix, 2), "proj_ypt": round(ypt, 2),
                    "vs_man": p["vs_man"], "vs_zone": p["vs_zone"], "vs_press": p["vs_press"], "adot": p["adot"], "games": p["games"], "targets": p["targets"], "longest_dec": p["longest_dec"], "ypg": p["ypg"], "proj_rec_longest": p["proj_longest"]})
    # his share x the team's game-script pass plays (97%: the rest are throwaways and spikes). An absent teammate's share is
    # not handed to the others: every form of redistribution lost on both windows (round 10)
    for r in rec:
        tg = r["share"] * vol["pass_plays"] * 0.97
        r.update({"proj_targets": round(tg, 1), "proj_catches_mean": round(tg * r["catch_shrunk"], 1), "proj_catches": round(tg * r["catch_shrunk"] * MED_CATCH, 1), "proj_rec_yards_mean": round(tg * r["proj_ypt"], 1), "proj_rec_yards": round(tg * r["proj_ypt"] * MED["rec"], 1), "proj_rec_td": round(tg * r["td_pt_proj"], 3)})
    rec.sort(key=lambda r: (r["out"], -r["proj_targets"]))
    rus = []
    for pid, p in RU.items():
        if p["team"] != team or pid not in ro.index: continue
        st = status(pid); is_out = any(st.startswith(w) for w in OUT_WORDS)
        ypc_s = _shrunk(p["ypc"], p["carries"], L["ypc"], K["rush"]); ypc = _toward(ypc_s, dd.get("ypc_allowed"), L["ypc"], W["rush"])
        ypc_mix = _mix(p["heavy"], p["light"] if p["light"] else p["mid"], dd.get("heavy_box"), "yds", p["ypc"])   # reading only
        td_s = _shrunk(p["td_pc"], p["carries"], L["td_pc"], K_TD["rush"]) * (1 + TD_MARGIN["rush"] * me)
        rus.append({"player_id": pid, "name": p["name"], "pos": p.get("pos", ""), "vs_opp": vs_summary((VS or {}).get(("rush", pid, opp))), "status": st, "out": is_out, "carries_pg": p["carries_pg"], "share": p["share"], "td_pc": p["td_pc"], "td_pc_proj": round(td_s, 4), "ypc": p["ypc"], "ypc_shrunk": round(ypc_s, 2), "ypc_mix": round(ypc_mix, 2), "proj_ypc": round(ypc, 2),
                    "light": p["light"], "heavy": p["heavy"], "games": p["games"], "carries": p["carries"], "longest_dec": p["longest_dec"], "ypg": p["ypg"], "proj_rush_longest": p["proj_longest"]})
    for r in rus:
        ca = r["share"] * vol["runs"]
        r.update({"proj_carries": round(ca, 1), "proj_rush_yards_mean": round(ca * r["proj_ypc"], 1), "proj_rush_yards": round(ca * r["proj_ypc"] * MED["rush"], 1), "proj_rush_td": round(ca * r["td_pc_proj"], 3)})
    rus.sort(key=lambda r: (r["out"], -r["proj_carries"]))
    qbs = []
    for pid, p in Q.items():
        if p["team"] != team or pid not in ro.index: continue
        st = status(pid); is_out = any(st.startswith(w) for w in OUT_WORDS)
        ypd_s = _shrunk(p["ypd"], p["dropbacks"], L["ypd"], K["pass"]); ypd = _toward(ypd_s, dd.get("ypd_allowed"), L["ypd"], W["pass"])
        epa_mix = _mix(p["press"], p["clean"], dd.get("pressure"), "epa", p["epa_db"])   # reading only
        dbs = vol["dropbacks"] if base else p["dropbacks_pg"]
        td_s = _shrunk(p["td_db"], p["dropbacks"], L["td_db"], K_TD["pass"]) * (1 + TD_MARGIN["pass"] * me)
        att = dbs * (1 - p["sack_rate"]); comp = att * _shrunk(p.get("comp") if p.get("comp") is not None else L["comp_pp"], p["dropbacks"], L["comp_pp"], 100.0)
        qbs.append({"player_id": pid, "name": p["name"], "pos": p.get("pos", ""), "vs_opp": vs_summary((VS or {}).get(("pass", pid, opp))), "status": st, "out": is_out, "proj_pass_attempts": round(att, 1), "proj_pass_completions": round(comp, 1), "td_db": p["td_db"], "int_db": p["int_db"], "sack_rate": p["sack_rate"], "comp": p.get("comp"), "dropbacks_pg": p["dropbacks_pg"], "proj_dropbacks": round(dbs, 1), "epa_db": p["epa_db"], "epa_mix": round(epa_mix, 3), "ypd": p["ypd"], "ypd_shrunk": round(ypd_s, 2), "proj_ypd": round(ypd, 2),
                    "proj_pass_yards_mean": round(dbs * ypd * wind_factor("pass", wind), 1), "proj_pass_yards": round(dbs * ypd * MED["pass"] * wind_factor("pass", wind), 1), "td_db_proj": round(td_s, 4), "proj_pass_td": round(dbs * td_s, 3), "proj_int": round(dbs * L["int_db"], 3), "press": p["press"], "clean": p["clean"], "blitz": p["blitz"], "noblitz": p["noblitz"], "vs_man": p["vs_man"], "vs_zone": p["vs_zone"], "games": p["games"], "dropbacks": p["dropbacks"], "longest_dec": p["longest_dec"], "ypg": p["ypg"], "proj_pass_longest": p["proj_longest"]})
    # the starter is the schedule's named QB when it names one (as the game model uses), else the most dropbacks per game
    qbs.sort(key=lambda r: (r["out"], 0 if (starter and r["player_id"] == starter) else 1, -r["dropbacks_pg"]))
    for u in rus: u["proj_rush_attempts"] = u["proj_carries"]
    recon = {"rec": reconcile(rec, "rec", exp_pts, "proj_rec_yards", "proj_rec_td"), "rush": reconcile(rus, "rush", exp_pts, "proj_rush_yards", "proj_rush_td"), "pass": reconcile(qbs, "pass", exp_pts, "proj_pass_yards", "proj_pass_td", starter_only=True)}
    for r in rec: r["proj_td_any"] = round(1 - np.exp(-(r["proj_rec_td"] + next((u["proj_rush_td"] for u in rus if u["player_id"] == r["player_id"]), 0.0))), 3)
    for u in rus: u["proj_td_any"] = round(1 - np.exp(-(u["proj_rush_td"] + next((r["proj_rec_td"] for r in rec if r["player_id"] == u["player_id"]), 0.0))), 3)
    for q in qbs:
        u = next((u for u in rus if u["player_id"] == q["player_id"]), None); q["proj_rush_yards"] = u["proj_rush_yards"] if u else None; q["proj_rush_td"] = u["proj_rush_td"] if u else 0.0; q["proj_td_any"] = round(1 - np.exp(-q["proj_rush_td"]), 3); q["proj_pass_rush_yards"] = round(q["proj_pass_yards"] + (q["proj_rush_yards"] or 0.0), 1)
    for r in rec: r["proj_rush_rec_yards"] = round(r["proj_rec_yards"] + next((u["proj_rush_yards"] for u in rus if u["player_id"] == r["player_id"]), 0.0), 1)
    for u in rus: u["proj_rush_rec_yards"] = round(u["proj_rush_yards"] + next((r["proj_rec_yards"] for r in rec if r["player_id"] == u["player_id"]), 0.0), 1)
    attach_market(rec, mk, [("rec_yards", "mkt_rec_yards"), ("rec_catches", "mkt_catches"), ("anytime_td", "mkt_td")])
    attach_market(rus, mk, [("rush_yards", "mkt_rush_yards"), ("anytime_td", "mkt_td")])
    attach_market(qbs, mk, [("pass_yards", "mkt_pass_yards")])
    matched = attach_all_markets(rec, mk) | attach_all_markets(rus, mk) | attach_all_markets(qbs, mk)
    return {"defense": dd, "volume": vol, "recon": recon, "qb": qbs[:2], "receivers": rec[:8], "rushers": rus[:4], "market_ts": (str(mk.ts.iloc[0]) if mk is not None and len(mk) else None), "_matched": sorted(matched)}


MARKET_STATS = {k: k for k in ["rec_yards", "rush_yards", "pass_yards", "rec_catches", "def_tackles", "pass_td", "pass_int", "pass_attempts", "pass_completions", "rush_attempts", "rush_rec_yards", "def_sacks", "def_solo_tackles", "rec_targets", "pass_rush_yards", "rec_longest", "rush_longest", "pass_longest", "kick_points", "field_goals"]}


def grade_market(graded: pd.DataFrame, run_at: str) -> pd.DataFrame | None:
    """Every graded projection with a closing book line: the line, the side the projection took (over when above the
    line, under when below), and the result against what happened. Also the book's own error, so the two can be
    compared. Anytime touchdown: the projection's chance of a score against the book's implied price, graded on
    whether he scored. Kept in data/tracker/props_vs_market.csv."""
    from .props_lines import load_log, closing, norm_name
    log = load_log()
    if not len(log) or graded is None or not len(graded):
        return None
    done = pd.read_csv(TR / "props_vs_market.csv") if (TR / "props_vs_market.csv").exists() else pd.DataFrame(columns=["game_id", "player_id", "stat"])
    rows = []
    for gid, g in graded.groupby("game_id"):
        mk = closing(log, gid)
        if not len(mk): continue
        td = g[g.stat.isin(["rec_td", "rush_td"])].groupby(["player_id", "name", "team", "season", "week"]).agg(proj=("proj", "sum"), actual=("actual", "sum")).reset_index()
        for r in g[g.stat.isin(MARKET_STATS)].itertuples():
            if ((done.game_id == gid) & (done.player_id == r.player_id) & (done.stat == r.stat)).any(): continue
            hit = mk[(mk.stat == r.stat) & (mk.key == norm_name(r.name))]
            if not len(hit) or pd.isna(hit.iloc[0].line): continue
            h = hit.iloc[0]; side = "over" if r.proj > h.line else ("under" if r.proj < h.line else "none")
            res = "push" if r.actual == h.line else ("win" if (r.actual > h.line) == (side == "over") else "loss") if side != "none" else "none"
            rows.append({"season": r.season, "week": r.week, "game_id": gid, "team": r.team, "player_id": r.player_id, "name": r.name, "stat": r.stat, "proj": r.proj, "line": float(h.line), "books": int(h.books), "over_price": h.over_price, "under_price": h.under_price, "side": side, "edge": round(float(r.proj - h.line), 2), "actual": r.actual, "result": res, "proj_error": round(float(r.proj - r.actual), 2), "line_error": round(float(h.line - r.actual), 2), "graded_at": run_at})
        for r in td.itertuples():
            if ((done.game_id == gid) & (done.player_id == r.player_id) & (done.stat == "anytime_td")).any(): continue
            hit = mk[(mk.stat == "anytime_td") & (mk.key == norm_name(r.name))]
            if not len(hit) or pd.isna(hit.iloc[0].over_price): continue
            h = hit.iloc[0]; p_us = 1 - np.exp(-r.proj); p_bk = implied(h.over_price); side = "yes" if p_us > p_bk else "no"
            res = "win" if (r.actual >= 1) == (side == "yes") else "loss"
            rows.append({"season": r.season, "week": r.week, "game_id": gid, "team": r.team, "player_id": r.player_id, "name": r.name, "stat": "anytime_td", "proj": round(p_us, 3), "line": round(p_bk, 3), "books": int(h.books), "over_price": h.over_price, "under_price": None, "side": side, "edge": round(p_us - p_bk, 3), "actual": r.actual, "result": res, "proj_error": None, "line_error": None, "graded_at": run_at})
    if not rows: return None
    out = pd.concat([done, pd.DataFrame(rows)], ignore_index=True) if len(done) else pd.DataFrame(rows)
    TR.mkdir(parents=True, exist_ok=True); out.to_csv(TR / "props_vs_market.csv", index=False); return out


def market_summary(vm: pd.DataFrame) -> list[dict]:
    """Record against the closing line by stat, and by size of the edge: wins, losses, pushes, and the two errors."""
    out = []
    for stat, g in vm.groupby("stat"):
        g = g[g.side != "none"]
        buckets = [("all", g)] + ([(">= 5", g[g.edge.abs() >= 5]), (">= 10", g[g.edge.abs() >= 10])] if stat.endswith("yards") else [(">= 0.5", g[g.edge.abs() >= 0.5]), (">= 1", g[g.edge.abs() >= 1])] if stat in ("rec_catches", "def_tackles") else [(">= 0.05", g[g.edge.abs() >= 0.05])])
        for lab, x in buckets:
            if not len(x): continue
            w, l, p_ = int((x.result == "win").sum()), int((x.result == "loss").sum()), int((x.result == "push").sum())
            out.append({"stat": stat, "edge": lab, "n": int(len(x)), "wins": w, "losses": l, "pushes": p_, "pct": round(w / (w + l), 3) if w + l else None,
                        "proj_mae": (round(float(x.proj_error.abs().mean()), 2) if x.proj_error.notna().any() else None), "line_mae": (round(float(x.line_error.abs().mean()), 2) if x.line_error.notna().any() else None)})
    return out


def grade(d: pd.DataFrame, season: int, week: int, run_at: str) -> pd.DataFrame | None:
    """Grade every earlier week's projections that have not been graded, against the players' actual yards."""
    files = sorted(REP.glob(f"props_{season}_wk*.csv"))
    done = pd.read_csv(TR / "props_graded.csv") if (TR / "props_graded.csv").exists() else pd.DataFrame(columns=["game_id", "player_id", "stat"])
    rows = []
    for f in files:
        wk = int(f.stem.split("wk")[-1])
        if wk >= week: continue
        pr = pd.read_csv(f)
        plays = d[(d.season == season) & (d.week == wk)]
        if not len(plays): continue
        plays = plays.assign(lg=np.where(plays.play_type.eq("run"), plays.yards_gained.fillna(0.0), np.where(plays.complete_pass.fillna(0).eq(1), plays.yards_gained.fillna(0.0), 0.0)))   # the longest gain of the game: runs, or completed passes
        def agg(mask, col, val):   # val: the yards column (pass_yds for passers: the yards on completions, not net of sacks)
            return plays[mask].groupby(["game_id", col]).agg(yards=(val or "yards_gained", "sum"), catches=("complete_pass", "sum"), pass_td=("pass_touchdown", "sum"), rush_td=("rush_touchdown", "sum"), ints=("interception", "sum"), n=("play_id", "count"), longest=("lg", "max")).reset_index().rename(columns={col: "player_id"})
        ry = agg(plays.pass_play, "receiver_player_id", None); rr = agg(plays.play_type.eq("run"), "rusher_player_id", None); py = agg(plays.dropback, "passer_player_id", "pass_yds"); pa = agg(plays.pass_att, "passer_player_id", None)   # attempts: passes and spikes, not sacks
        rrr = rr.merge(ry[["game_id", "player_id", "yards"]].rename(columns={"yards": "rec_yds"}), on=["game_id", "player_id"], how="outer").fillna({"yards": 0, "rec_yds": 0, "n": 0}); rrr["both"] = rrr.yards + rrr.rec_yds
        prr = py.merge(rr[["game_id", "player_id", "yards"]].rename(columns={"yards": "rush_yds"}), on=["game_id", "player_id"], how="outer").fillna({"yards": 0, "rush_yds": 0, "n": 0}); prr["both"] = prr.yards + prr.rush_yds
        dgw = defender_games(); dgw = dgw[(dgw.season == season) & (dgw.week == wk)].rename(columns={"pid": "player_id"}); dgw["n"] = dgw.plays_faced
        kw = kicker_games([season]); kw = kw[kw.week == wk].copy(); kw["n"] = kw.fga + kw.xpa
        SRC = {"kick_points": (kw, "pts"), "field_goals": (kw, "fgm"), "rec_yards": (ry, "yards"), "rec_catches": (ry, "catches"), "rec_td": (ry, "pass_td"), "rush_yards": (rr, "yards"), "rush_td": (rr, "rush_td"), "pass_yards": (py, "yards"), "pass_td": (py, "pass_td"), "pass_int": (py, "ints"), "def_tackles": (dgw, "tackles"), "def_sacks": (dgw, "sacks"), "def_solo_tackles": (dgw, "solo"), "pass_attempts": (pa, "n"), "pass_completions": (pa, "catches"), "rush_attempts": (rr, "n"), "rush_rec_yards": (rrr, "both"), "rec_targets": (ry, "n"), "pass_rush_yards": (prr, "both"), "rec_longest": (ry, "longest"), "rush_longest": (rr, "longest"), "pass_longest": (pa, "longest")}
        played = set(plays.game_id)
        for _, r in pr.iterrows():
            if r.game_id not in played or ((done.game_id == r.game_id) & (done.player_id == r.player_id) & (done.stat == r.stat)).any(): continue
            src, col = SRC[r.stat]; hit = src[(src.game_id == r.game_id) & (src.player_id == r.player_id)]
            actual = float(hit[col].fillna(0).iloc[0]) if len(hit) else 0.0; vol_ = int(hit.n.iloc[0]) if len(hit) else 0
            rows.append({"season": season, "week": wk, "game_id": r.game_id, "team": r.team, "player_id": r.player_id, "name": r["name"], "stat": r.stat, "proj": r.proj, "proj_volume": r.proj_volume, "actual": actual, "actual_volume": vol_, "error": round(actual - r.proj, 3), "graded_at": run_at, "made": (r["made"] if "made" in pr.columns and isinstance(r.get("made"), str) else "live")})
    if not rows: return None
    g = pd.concat([done, pd.DataFrame(rows)], ignore_index=True) if len(done) else pd.DataFrame(rows)
    TR.mkdir(parents=True, exist_ok=True); g.to_csv(TR / "props_graded.csv", index=False); return g


def main(season: int | None = None, week: int | None = None, backfill: bool = False):
    """The week's projections. backfill=True projects an earlier week of the season with the data as of that week (the
    same rule, nothing from the week itself), writes only its CSV and markdown with made = "after the fact", and
    leaves the live panel, profiles and grades alone; the next run grades it like any other week."""
    from .lines import current_week
    from .positions import names_by_id
    games = pd.read_parquet(OUT / "games.parquet")
    if season is None or week is None:
        season, week = current_week(games)
    run_at = pd.Timestamp.now("UTC").strftime("%Y-%m-%d %H:%M UTC")
    d = official(pd.read_parquet(OUT / "scheme_plays.parquet"))
    graded = None if backfill else grade(d, season, week, run_at)
    vm = None if backfill else grade_market(graded, run_at)
    from .props_lines import load_log, closing
    plog = load_log()
    a = _asof(d, season, week); names = names_by_id(range(season - 2, season + 1))
    roster = pd.read_parquet(OUT / "roster_now.parquet") if (OUT / "roster_now.parquet").exists() else pd.DataFrame(columns=["team", "player_id", "roster", "report"])
    R, RU, Q, D, V, L = receivers(a, names), rushers(a, names), passers(a, names), defenses(a), teams_volume(a), league_baselines(a)
    VS = vs_defense(d[(d.season < season) | ((d.season == season) & (d.week < week))])   # every charted season, for the card's "against this defense" column
    dg = defender_games(); DF = defenders(dg, names, season, week); VS.update(vs_offense(dg[(dg.season < season) | ((dg.season == season) & (dg.week < week))], games))
    KK = kickers(kicker_games(range(season - 1, season + 1)), names, season, week)
    wk = games[(games.season == season) & (games.week == week)]
    pv = OUT / "pred_v3.parquet"; xp = pd.read_parquet(pv, columns=["game_id", "home_exp", "away_exp"]).set_index("game_id") if pv.exists() else pd.DataFrame(columns=["home_exp", "away_exp"])   # the game model's expected points, priced before the game
    out = {"season": season, "week": week, "built": run_at, "window_games": WINDOW, "min_split": MIN_SPLIT, "k": K, "w": W, "decay": DECAY, "gs": GS, "gs_total": GS_TOTAL, "med": MED, "pace": PACE, "wind_c": WIND_C, "prop_edge": PROP_EDGE, "recon_w": RECON_W, "team_fit": TEAM_FIT, "k_catch": K_CATCH, "med_catch": MED_CATCH, "k_td": K_TD, "td_margin": TD_MARGIN, "backtest_counts": BACKTEST_COUNTS, "backtest_def": BACKTEST_DEF, "longest": LONGEST, "backtest_longest": BACKTEST_LONGEST, "fade": FADE, "kick": KICK, "backtest_kick": BACKTEST_KICK, "market_labels": MARKET_LABEL, "def_decay": DEF_DECAY, "def_med": DEF_MED, "k_sack": K_SACK, "league": L, "games": {},
           "backtest": dict(BACKTEST, note="mean absolute error in yards per player-game with this rule, 2019 to 2022 and 2023 to 2025, run walk-forward with league averages as of each game (reports/props_by_season.csv)")}
    rows = []
    for g in wk.itertuples():
        sp = None if pd.isna(g.spread_line) else float(g.spread_line)   # nflverse: positive when the home team is favoured
        wd = None if (bool(g.dome) or pd.isna(g.wind)) else float(g.wind)   # kickoff forecast once one is usable (weather.apply_to_games), else unknown
        mk = closing(plog, g.game_id) if len(plog) else None
        ha = (float(xp.loc[g.game_id, "home_exp"]), float(xp.loc[g.game_id, "away_exp"])) if g.game_id in xp.index else (None, None)
        aq = g.away_qb_id if isinstance(g.away_qb_id, str) else None; hq = g.home_qb_id if isinstance(g.home_qb_id, str) else None   # nflverse names the starters for played games and the coming week
        out["games"][g.game_id] = {g.away_team: project_game(g.away_team, g.home_team, R, RU, Q, D, V, L, roster, None if sp is None else -sp, g.total_line, wd, mk, ha[1], VS, aq), g.home_team: project_game(g.home_team, g.away_team, R, RU, Q, D, V, L, roster, sp, g.total_line, wd, mk, ha[0], VS, hq)}
        out["games"][g.game_id][g.away_team]["defenders"] = project_defense(g.away_team, g.home_team, DF, V, roster, None if sp is None else -sp, g.total_line, mk, VS)
        out["games"][g.game_id][g.home_team]["defenders"] = project_defense(g.home_team, g.away_team, DF, V, roster, sp, g.total_line, mk, VS)
        out["games"][g.game_id][g.away_team]["kicker"] = project_kicker(g.away_team, KK, roster, None if sp is None else -sp, g.total_line, mk)
        out["games"][g.game_id][g.home_team]["kicker"] = project_kicker(g.home_team, KK, roster, sp, g.total_line, mk)
        if mk is not None and len(mk):   # the book's lines on anyone not listed above (kickers, players without a profile), by team where the roster says
            from .props_lines import norm_name
            byname = {norm_name(r.name): r.team for r in roster[roster.team.isin([g.away_team, g.home_team])].itertuples()}
            for team in (g.away_team, g.home_team):
                side = out["games"][g.game_id][team]; listed = set(side.pop("_matched", [])) | {norm_name(r["name"]) for r in side.get("defenders", []) + side.get("kicker", [])}
                side["others"] = [{"name": h.player, "stat": h.stat, "line": (None if pd.isna(h.line) else float(h.line)), "books": int(h.books), "over": (None if pd.isna(h.over_price) else int(h.over_price)), "under": (None if pd.isna(h.under_price) else int(h.under_price)), "open": (None if pd.isna(h.open_line) else float(h.open_line)), "pulls": int(h.pulls)} for h in mk.itertuples() if h.key not in listed and byname.get(h.key) == team]
                side["market_open_ts"] = str(mk.open_ts.iloc[0]); side["market_pulls"] = int(mk.pulls.iloc[0])
        else:
            for team in (g.away_team, g.home_team): out["games"][g.game_id][team].pop("_matched", None); out["games"][g.game_id][team]["others"] = []
        for team, side in out["games"][g.game_id].items():
            def add(r, stat, proj, volume):
                rows.append({"season": season, "week": week, "game_id": g.game_id, "team": team, "player_id": r["player_id"], "name": r["name"], "stat": stat, "proj": proj, "proj_volume": volume, "run_at": run_at, "made": ("after the fact" if backfill else "live")})
            for r in side["receivers"]:
                if not r["out"]: add(r, "rec_yards", r["proj_rec_yards"], r["proj_targets"]); add(r, "rec_catches", r["proj_catches"], r["proj_targets"]); add(r, "rec_td", r["proj_rec_td"], r["proj_targets"]); add(r, "rec_targets", r["proj_targets"], r["proj_targets"]); add(r, "rec_longest", r["proj_rec_longest"], r["proj_targets"])
            for r in side["rushers"]:
                if not r["out"]: add(r, "rush_yards", r["proj_rush_yards"], r["proj_carries"]); add(r, "rush_td", r["proj_rush_td"], r["proj_carries"]); add(r, "rush_attempts", r["proj_rush_attempts"], r["proj_carries"]); add(r, "rush_rec_yards", r["proj_rush_rec_yards"], r["proj_carries"]); add(r, "rush_longest", r["proj_rush_longest"], r["proj_carries"])
            for r in side["qb"][:1]:
                if not r["out"]: add(r, "pass_yards", r["proj_pass_yards"], r["proj_dropbacks"]); add(r, "pass_td", r["proj_pass_td"], r["proj_dropbacks"]); add(r, "pass_int", r["proj_int"], r["proj_dropbacks"]); add(r, "pass_attempts", r["proj_pass_attempts"], r["proj_dropbacks"]); add(r, "pass_completions", r["proj_pass_completions"], r["proj_dropbacks"]); add(r, "pass_rush_yards", r["proj_pass_rush_yards"], r["proj_dropbacks"]); add(r, "pass_longest", r["proj_pass_longest"], r["proj_dropbacks"])
            for r in side.get("defenders", []):
                if not r["out"]: add(r, "def_tackles", r["proj_tackles"], r["opp_plays"]); add(r, "def_sacks", r["proj_sacks"], r["opp_plays"]); add(r, "def_solo_tackles", r["proj_solo_tackles"], r["opp_plays"])
            for r in side.get("kicker", []):
                if not r["out"]: add(r, "kick_points", r["proj_kick_points"], r["implied_total"]); add(r, "field_goals", r["proj_field_goals"], r["implied_total"])
    pr = pd.DataFrame(rows)
    if len(pr):
        pr.to_csv(REP / f"props_{season}_wk{week}.csv", index=False)
        if backfill:
            print(f"props backfill: {len(pr)} projections for week {week} of {season}, made after the fact with the data as of that week", flush=True); return
        md = [f"# Week {week}, {season}: player projections (readings, graded next run)", "", f"Volume (the team's plays per game moved by the game script from the closing spread and total, shared among the players who are playing by usage decayed {DECAY} per game back) x the player's yards per touch shrunk toward the league (receivers {K['rec']:.0f} targets, rushers {K['rush']:.0f} carries, QBs {K['pass']:.0f} dropbacks of weight) and moved toward what the defense allows (receivers {W['rec']:.0%}, rushers {W['rush']:.0%}, QBs {W['pass']:.0%}) x the median factor (receivers {MED['rec']}, rushers {MED['rush']}, QBs {MED['pass']}). Passing yards also blend the opponent's allowed dropbacks (a quarter) and drop {abs(WIND_C['pass']):.1%} per mph of kickoff wind above 10. The rule four rounds of backtest chose: {BACKTEST['rec_yards'][0]} / {BACKTEST['rec_yards'][1]} yards off on receiving, {BACKTEST['rush_yards'][0]} / {BACKTEST['rush_yards'][1]} on rushing and {BACKTEST['pass_yards'][0]} / {BACKTEST['pass_yards'][1]} on passing yards per player-game, 2019-22 / 2023-25 (reports/props_backtest4.csv). Each team's players are then moved toward what the game model's expected points say the team should produce (yards a quarter of the way, passing half; touchdowns half, passing fully; reports/props_backtest6.csv). Receptions: targets x catch rate shrunk toward the league ({K_CATCH:.0f} targets) x {MED_CATCH}; touchdowns: volume x his rate shrunk toward the league ({K_TD['rec']:.0f} / {K_TD['rush']:.0f} / {K_TD['pass']:.0f} touches), receiving and passing scores moved {TD_MARGIN['rec']:.1%} per point of expected margin; interceptions at the league rate (reports/props_backtest5.csv). Not a market comparison. Built {run_at}.", "", pr.drop(columns=["run_at"]).to_markdown(index=False), ""]
        (REP / f"props_{season}_wk{week}.md").write_text("\n".join(md))
    out["market_lines"] = int(sum(1 for gm in out["games"].values() for side in gm.values() for grp in ("receivers", "rushers", "qb") for r in side[grp] if any(k.startswith("mkt_") for k in r)))
    if (TR / "props_vs_market.csv").exists():
        vm_all = pd.read_csv(TR / "props_vs_market.csv"); out["market"] = market_summary(vm_all); out["market_rows"] = int(len(vm_all))
    if graded is not None and len(graded):
        s = graded.groupby("stat").agg(n=("error", "size"), mae=("error", lambda e: round(float(e.abs().mean()), 2)), bias=("error", lambda e: round(float(e.mean()), 2))).reset_index()
        out["graded"] = s.to_dict("records")
    (OUT / "props.json").write_text(json.dumps(out, default=lambda v: None if (isinstance(v, float) and np.isnan(v)) else (v.item() if hasattr(v, "item") else str(v))))
    # every player's profile, every defense and the league, for the Players tab (the card shows only this week's games)
    prof = {"season": season, "week": week, "built": run_at, "window_games": WINDOW, "min_split": MIN_SPLIT, "receivers": R, "rushers": RU, "passers": Q, "defenses": D, "volume": V, "league": L}
    (OUT / "props_profiles.json").write_text(json.dumps(prof, default=lambda v: None if (isinstance(v, float) and np.isnan(v)) else (v.item() if hasattr(v, "item") else str(v))))
    print("props", len(pr), "projections for week", week, "graded rows", 0 if graded is None else len(graded), "market lines on the cards", out["market_lines"], "graded against the market", out.get("market_rows", 0))


def reattach_markets() -> None:
    """Re-read the props log and put the newest lines beside this week's projections without rebuilding them (the line
    watch runs this after every snapshot, then export_web --week rewrites props.js): every market per listed player, the
    mkt_ keys the takeaways use, and each side's market timestamp and pull count."""
    from .props_lines import load_log, closing
    f = OUT / "props.json"
    if not f.exists(): return
    out = json.loads(f.read_text()); plog = load_log()
    for gid, gm in out["games"].items():
        mk = closing(plog, gid) if len(plog) else None
        for team, side in gm.items():
            for grp in ("qb", "receivers", "rushers", "defenders", "kicker"):
                for r in side.get(grp, []):
                    for k in [k for k in r if k.startswith("mkt_")]: r.pop(k)
                attach_all_markets(side.get(grp, []), mk)
            attach_market(side.get("receivers", []), mk, [("rec_yards", "mkt_rec_yards"), ("rec_catches", "mkt_catches"), ("anytime_td", "mkt_td")])
            attach_market(side.get("rushers", []), mk, [("rush_yards", "mkt_rush_yards"), ("anytime_td", "mkt_td")])
            attach_market(side.get("qb", []), mk, [("pass_yards", "mkt_pass_yards")]); attach_market(side.get("defenders", []), mk, [("def_tackles", "mkt_tackles")])
            side["market_ts"] = (str(mk.ts.iloc[0]) if mk is not None and len(mk) else None)
            if mk is not None and len(mk): side["market_open_ts"] = str(mk.open_ts.iloc[0]); side["market_pulls"] = int(mk.pulls.iloc[0])
            side["others"] = []
    out["market_lines"] = int(sum(1 for gm in out["games"].values() for side in gm.values() for grp in ("receivers", "rushers", "qb") for r in side[grp] if any(k.startswith("mkt_") for k in r)))
    out["market_refreshed"] = pd.Timestamp.now("UTC").strftime("%Y-%m-%d %H:%M UTC")
    f.write_text(json.dumps(out, default=lambda v: None if isinstance(v, float) and np.isnan(v) else (float(v) if isinstance(v, (np.floating,)) else int(v) if isinstance(v, np.integer) else str(v))))
    print("props markets refreshed", out["market_lines"], "lines on the cards; newest pull", max([str(side.get("market_ts")) for gm in out["games"].values() for side in gm.values() if side.get("market_ts")] or ["none"]), flush=True)


if __name__ == "__main__":
    import sys
    if "--markets" in sys.argv:
        reattach_markets()
    elif "--backfill" in sys.argv:   # python -m nflmodel.props --backfill 2026 1
        i = sys.argv.index("--backfill"); main(int(sys.argv[i + 1]), int(sys.argv[i + 2]), backfill=True)
    else:
        main()
