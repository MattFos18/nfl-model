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
MED = {"rec": 0.88, "rush": 0.84, "pass": 0.90}      # median factor on the yards line, fitted on 2016 to 2018 (0.02 grid)
K_CATCH, MED_CATCH = 25.0, 0.88                     # catch rate shrunk toward the league with 25 targets of weight; receptions line x 0.88 (round 5, both windows)
K_TD = {"rec": 200.0, "rush": 200.0, "pass": 400.0}  # touchdown rate per touch shrunk toward the league (round 5: best Poisson fit on 2016 to 2018, held on both windows)
TD_MARGIN = {"rec": 0.020, "rush": 0.0, "pass": 0.020}   # touchdown rate x (1 + TD_MARGIN x expected margin): favourites score more; fitted on 2016 to 2018 (rushing: no gain on both windows, so 0)
BACKTEST_COUNTS = {"rec_catches": [1.438, 1.359], "rec_td_ll": [0.5101, 0.4869], "rush_td_ll": [0.5948, 0.5655], "pass_td_ll": [1.4868, 1.4543], "pass_int_ll": [1.1449, 1.1047]}   # reports/props_backtest5.csv: catches MAE (catch_K25_med), touchdown and interception Poisson log loss (td_K200_gs, td_K200, td_K400_gs, int_league)
PACE = {"rec": 0.0, "rush": 0.0, "pass": 0.25}       # weight on the opponent's allowed plays per game in the team's volume (round 4: helps passing on both windows, nothing on the others)
WIND_C = {"rec": 0.0, "rush": 0.0, "pass": -0.005}   # yards line x (1 + WIND_C x mph of wind above 10 at kickoff), fitted on 2016 to 2018 (round 4: passing only)
BACKTEST = {"rec_yards": [19.44, 18.46], "rush_yards": [18.36, 17.60], "pass_yards": [60.71, 61.08]}   # mean absolute error, 2019-22 / 2023-25: reports/props_backtest4.csv rows base (receiving, rushing; = A85B_med in props_backtest3.csv) and combo (passing: pace and wind added)
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


def _share(g: pd.DataFrame, team_by_game: pd.Series) -> float:
    """His plays over his teams' plays in the same games, both decayed by DECAY per game back from his most recent
    game, over every game in the as-of frame (a player traded in keeps the usage he had elsewhere)."""
    pairs = g.groupby(["game_id", "posteam", "season", "week"]).size().reset_index(name="n").sort_values(["season", "week"], ascending=False)
    wts = DECAY ** np.arange(len(pairs))
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
        share = _share(g_all, team_pass)
        out[pid] = {"name": names.get(pid, (pid, ""))[0], "team": team, "games": int(g.game_id.nunique()), "targets": int(tgt), "targets_pg": round(tgt / g.game_id.nunique(), 2), "share": round(share, 3),
                    "catch": round(float(g.complete_pass.fillna(0).mean()), 3), "ypt": round(float(g.yards_gained.fillna(0).mean()), 2), "epa_pt": round(float(g.epa.mean()), 3), "adot": (round(float(g.air_yards.mean()), 1) if g.air_yards.notna().any() else None),
                    "td_pt": round(float(g.pass_touchdown.fillna(0).mean()), 3), "vs_man": _stat(g[g.man], MIN_SPLIT), "vs_zone": _stat(g[g.zone], MIN_SPLIT), "vs_blitz": _stat(g[g.blitz == 1], MIN_SPLIT), "vs_press": _stat(g[g.pressure == 1], MIN_SPLIT)}
    return out


def rushers(d: pd.DataFrame, names: dict) -> dict:
    out = {}
    t = d[d.play_type.eq("run") & d.rusher_player_id.notna()]
    team_run = t.groupby(["game_id", "posteam"]).size()
    for pid, g in t.groupby("rusher_player_id"):
        if names.get(pid, ("", ""))[1] == "QB":
            continue
        g_all = g; g = _last(g); n = len(g)
        if n < MIN_VOL:
            continue
        team = g.sort_values(["season", "week"]).posteam.iloc[-1]
        out[pid] = {"name": names.get(pid, (pid, ""))[0], "team": team, "games": int(g.game_id.nunique()), "carries": int(n), "carries_pg": round(n / g.game_id.nunique(), 2), "share": round(_share(g_all, team_run), 3),
                    "ypc": round(float(g.yards_gained.fillna(0).mean()), 2), "epa_pc": round(float(g.epa.mean()), 3), "success": round(float(g.success.mean()), 3), "td_pc": round(float(g.rush_touchdown.fillna(0).mean()), 3),
                    "light": _stat(g[g.box <= 6], MIN_SPLIT), "heavy": _stat(g[g.box >= 8], MIN_SPLIT), "mid": _stat(g[g.box == 7], MIN_SPLIT)}
    return out


def passers(d: pd.DataFrame, names: dict) -> dict:
    out = {}
    t = d[d.dropback & d.passer_player_id.notna()]
    for pid, g in t.groupby("passer_player_id"):
        g = _last(g); n = len(g)
        if n < MIN_VOL * 3:
            continue
        team = g.sort_values(["season", "week"]).posteam.iloc[-1]
        out[pid] = {"name": names.get(pid, (pid, ""))[0], "team": team, "games": int(g.game_id.nunique()), "dropbacks": int(n), "dropbacks_pg": round(n / g.game_id.nunique(), 1),
                    "epa_db": round(float(g.epa.mean()), 3), "ypd": round(float(g.yards_gained.fillna(0).mean()), 2), "sack_rate": round(float(g.sack.fillna(0).mean()), 3), "td_db": round(float(g.pass_touchdown.fillna(0).mean()), 3), "int_db": round(float(g.interception.fillna(0).mean()), 3),
                    "press": _stat(g[g.pressure == 1], MIN_SPLIT), "clean": _stat(g[g.pressure == 0], MIN_SPLIT), "blitz": _stat(g[g.blitz == 1], MIN_SPLIT), "noblitz": _stat(g[g.blitz == 0], MIN_SPLIT), "vs_man": _stat(g[g.man], MIN_SPLIT), "vs_zone": _stat(g[g.zone], MIN_SPLIT)}
    return out


def defenses(d: pd.DataFrame) -> dict:
    out = {}
    for team, g in d.groupby("defteam"):
        g = _last(g); ps = g[g.pass_play]; db = g[g.dropback]; run = g[g.play_type.eq("run")]; cv = ps[ps.cov_known]
        out[team] = {"games": int(g.game_id.nunique()), "ypt_allowed": round(float(ps.yards_gained.fillna(0).mean()), 2), "epa_pt_allowed": round(float(ps.epa.mean()), 3), "catch_allowed": round(float(ps.complete_pass.fillna(0).mean()), 3),
                     "ypc_allowed": round(float(run.yards_gained.fillna(0).mean()), 2), "epa_pc_allowed": round(float(run.epa.mean()), 3), "ypd_allowed": round(float(db.yards_gained.fillna(0).mean()), 2),
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
    ps = d[d.pass_play]; run = d[d.play_type.eq("run")]; db = d[d.dropback]
    tg = ps[ps.receiver_player_id.notna()]
    return {"ypt": round(float(ps.yards_gained.fillna(0).mean()), 2), "epa_pt": round(float(ps.epa.mean()), 3), "catch": round(float(tg.complete_pass.fillna(0).mean()), 4), "ypc": round(float(run.yards_gained.fillna(0).mean()), 2), "ypd": round(float(db.yards_gained.fillna(0).mean()), 2),
            "td_pt": round(float(tg.pass_touchdown.fillna(0).mean()), 4), "td_pc": round(float(run.rush_touchdown.fillna(0).mean()), 4), "td_db": round(float(db.pass_touchdown.fillna(0).mean()), 4), "int_db": round(float(db.interception.fillna(0).mean()), 4),
            "man": round(float(ps[ps.cov_known].man.mean()), 3) if ps.cov_known.any() else None, "pressure": (round(float(db.pressure.mean()), 3) if db.pressure.notna().any() else None), "heavy_box": (round(float((run.box >= 8).mean()), 3) if run.box.notna().any() else None)}


def _mix(a: dict | None, b: dict | None, rate: float | None, key: str, fallback: float) -> float:
    """a in look x rate + b outside it x (1 - rate), when both splits and the rate exist; else the fallback."""
    if a is None or b is None or rate is None:
        return fallback
    return a[key] * rate + b[key] * (1 - rate)


def _toward(v: float, allowed: float | None, league: float, w: float) -> float:
    return v if (allowed is None or not league) else v * (1 + w * (allowed / league - 1))


def _shrunk(rate: float, n: float, league: float, k: float) -> float:
    return (rate * n + k * league) / (n + k)


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


def implied(price: float) -> float:
    """American price -> implied probability, vig included."""
    price = float(price)
    return 100 / (price + 100) if price > 0 else -price / (-price + 100)


def project_game(team: str, opp: str, R: dict, RU: dict, Q: dict, D: dict, V: dict, L: dict, roster: pd.DataFrame, margin: float | None = None, total: float | None = None, wind: float | None = None, mk: pd.DataFrame | None = None) -> dict:
    """One offense against one defense: every rostered receiver, rusher and QB with a profile, projected. margin is the
    team's expected margin from the closing spread (positive when favoured), total the closing total, wind the mph at
    kickoff (None in a dome or before a usable forecast)."""
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
        rec.append({"player_id": pid, "name": p["name"], "status": st, "out": is_out, "targets_pg": p["targets_pg"], "share": p["share"], "catch": p["catch"], "catch_shrunk": round(catch_s, 3), "td_pt": p["td_pt"], "td_pt_proj": round(td_s, 4),
                    "ypt": p["ypt"], "ypt_shrunk": round(ypt_s, 2), "ypt_mix": round(ypt_mix, 2), "proj_ypt": round(ypt, 2),
                    "vs_man": p["vs_man"], "vs_zone": p["vs_zone"], "vs_press": p["vs_press"], "adot": p["adot"], "games": p["games"], "targets": p["targets"]})
    # volume is shared out among the players who are playing: an absent player's targets go to the others in proportion
    # to their usage, and the team's targets add up to its game-script pass plays (97%: the rest are throwaways and spikes)
    act = [r for r in rec if not r["out"]]; tot = sum(r["share"] for r in act)
    for r in rec:
        tg = (r["share"] / tot * vol["pass_plays"] * 0.97) if (tot and not r["out"]) else r["share"] * vol["pass_plays"] * 0.97
        r.update({"proj_targets": round(tg, 1), "proj_catches_mean": round(tg * r["catch_shrunk"], 1), "proj_catches": round(tg * r["catch_shrunk"] * MED_CATCH, 1), "proj_rec_yards_mean": round(tg * r["proj_ypt"], 1), "proj_rec_yards": round(tg * r["proj_ypt"] * MED["rec"], 1), "proj_rec_td": round(tg * r["td_pt_proj"], 3)})
    rec.sort(key=lambda r: (r["out"], -r["proj_targets"]))
    rus = []
    for pid, p in RU.items():
        if p["team"] != team or pid not in ro.index: continue
        st = status(pid); is_out = any(st.startswith(w) for w in OUT_WORDS)
        ypc_s = _shrunk(p["ypc"], p["carries"], L["ypc"], K["rush"]); ypc = _toward(ypc_s, dd.get("ypc_allowed"), L["ypc"], W["rush"])
        ypc_mix = _mix(p["heavy"], p["light"] if p["light"] else p["mid"], dd.get("heavy_box"), "yds", p["ypc"])   # reading only
        td_s = _shrunk(p["td_pc"], p["carries"], L["td_pc"], K_TD["rush"]) * (1 + TD_MARGIN["rush"] * me)
        rus.append({"player_id": pid, "name": p["name"], "status": st, "out": is_out, "carries_pg": p["carries_pg"], "share": p["share"], "td_pc": p["td_pc"], "td_pc_proj": round(td_s, 4), "ypc": p["ypc"], "ypc_shrunk": round(ypc_s, 2), "ypc_mix": round(ypc_mix, 2), "proj_ypc": round(ypc, 2),
                    "light": p["light"], "heavy": p["heavy"], "games": p["games"], "carries": p["carries"]})
    act = [r for r in rus if not r["out"]]; tot = sum(r["share"] for r in act)
    for r in rus:
        ca = (r["share"] / tot * vol["runs"]) if (tot and not r["out"]) else r["share"] * vol["runs"]
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
        qbs.append({"player_id": pid, "name": p["name"], "status": st, "out": is_out, "dropbacks_pg": p["dropbacks_pg"], "proj_dropbacks": round(dbs, 1), "epa_db": p["epa_db"], "epa_mix": round(epa_mix, 3), "ypd": p["ypd"], "ypd_shrunk": round(ypd_s, 2), "proj_ypd": round(ypd, 2),
                    "proj_pass_yards_mean": round(dbs * ypd * wind_factor("pass", wind), 1), "proj_pass_yards": round(dbs * ypd * MED["pass"] * wind_factor("pass", wind), 1), "td_db_proj": round(td_s, 4), "proj_pass_td": round(dbs * td_s, 3), "proj_int": round(dbs * L["int_db"], 3), "press": p["press"], "clean": p["clean"], "blitz": p["blitz"], "noblitz": p["noblitz"], "vs_man": p["vs_man"], "vs_zone": p["vs_zone"], "games": p["games"], "dropbacks": p["dropbacks"]})
    qbs.sort(key=lambda r: (r["out"], -r["dropbacks_pg"]))
    for r in rec: r["proj_td_any"] = round(1 - np.exp(-(r["proj_rec_td"] + next((u["proj_rush_td"] for u in rus if u["player_id"] == r["player_id"]), 0.0))), 3)
    for u in rus: u["proj_td_any"] = round(1 - np.exp(-(u["proj_rush_td"] + next((r["proj_rec_td"] for r in rec if r["player_id"] == u["player_id"]), 0.0))), 3)
    attach_market(rec, mk, [("rec_yards", "mkt_rec_yards"), ("rec_catches", "mkt_catches"), ("anytime_td", "mkt_td")])
    attach_market(rus, mk, [("rush_yards", "mkt_rush_yards"), ("anytime_td", "mkt_td")])
    attach_market(qbs, mk, [("pass_yards", "mkt_pass_yards")])
    return {"defense": dd, "volume": vol, "qb": qbs[:2], "receivers": rec[:8], "rushers": rus[:4], "market_ts": (str(mk.ts.iloc[0]) if mk is not None and len(mk) else None)}


MARKET_STATS = {"rec_yards": "rec_yards", "rush_yards": "rush_yards", "pass_yards": "pass_yards", "rec_catches": "rec_catches"}


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
        buckets = [("all", g)] + ([(">= 5", g[g.edge.abs() >= 5]), (">= 10", g[g.edge.abs() >= 10])] if stat.endswith("yards") else [(">= 0.5", g[g.edge.abs() >= 0.5])] if stat == "rec_catches" else [(">= 0.05", g[g.edge.abs() >= 0.05])])
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
        def agg(mask, col, val):
            return plays[mask].groupby(["game_id", col]).agg(yards=("yards_gained", "sum"), catches=("complete_pass", "sum"), pass_td=("pass_touchdown", "sum"), rush_td=("rush_touchdown", "sum"), ints=("interception", "sum"), n=("play_id", "count")).reset_index().rename(columns={col: "player_id"})
        ry = agg(plays.pass_play, "receiver_player_id", None); rr = agg(plays.play_type.eq("run"), "rusher_player_id", None); py = agg(plays.dropback, "passer_player_id", None)
        SRC = {"rec_yards": (ry, "yards"), "rec_catches": (ry, "catches"), "rec_td": (ry, "pass_td"), "rush_yards": (rr, "yards"), "rush_td": (rr, "rush_td"), "pass_yards": (py, "yards"), "pass_td": (py, "pass_td"), "pass_int": (py, "ints")}
        played = set(plays.game_id)
        for _, r in pr.iterrows():
            if r.game_id not in played or ((done.game_id == r.game_id) & (done.player_id == r.player_id) & (done.stat == r.stat)).any(): continue
            src, col = SRC[r.stat]; hit = src[(src.game_id == r.game_id) & (src.player_id == r.player_id)]
            actual = float(hit[col].fillna(0).iloc[0]) if len(hit) else 0.0; vol_ = int(hit.n.iloc[0]) if len(hit) else 0
            rows.append({"season": season, "week": wk, "game_id": r.game_id, "team": r.team, "player_id": r.player_id, "name": r["name"], "stat": r.stat, "proj": r.proj, "proj_volume": r.proj_volume, "actual": actual, "actual_volume": vol_, "error": round(actual - r.proj, 3), "graded_at": run_at})
    if not rows: return None
    g = pd.concat([done, pd.DataFrame(rows)], ignore_index=True) if len(done) else pd.DataFrame(rows)
    TR.mkdir(parents=True, exist_ok=True); g.to_csv(TR / "props_graded.csv", index=False); return g


def main():
    from .lines import current_week
    from .positions import names_by_id
    games = pd.read_parquet(OUT / "games.parquet"); season, week = current_week(games)
    run_at = pd.Timestamp.now("UTC").strftime("%Y-%m-%d %H:%M UTC")
    d = pd.read_parquet(OUT / "scheme_plays.parquet"); d = d[d.play_type.isin(["pass", "run"])]
    graded = grade(d, season, week, run_at)
    vm = grade_market(graded, run_at)
    from .props_lines import load_log, closing
    plog = load_log()
    a = _asof(d, season, week); names = names_by_id(range(season - 2, season + 1))
    roster = pd.read_parquet(OUT / "roster_now.parquet") if (OUT / "roster_now.parquet").exists() else pd.DataFrame(columns=["team", "player_id", "roster", "report"])
    R, RU, Q, D, V, L = receivers(a, names), rushers(a, names), passers(a, names), defenses(a), teams_volume(a), league_baselines(a)
    wk = games[(games.season == season) & (games.week == week)]
    out = {"season": season, "week": week, "built": run_at, "window_games": WINDOW, "min_split": MIN_SPLIT, "k": K, "w": W, "decay": DECAY, "gs": GS, "gs_total": GS_TOTAL, "med": MED, "pace": PACE, "wind_c": WIND_C, "k_catch": K_CATCH, "med_catch": MED_CATCH, "k_td": K_TD, "td_margin": TD_MARGIN, "backtest_counts": BACKTEST_COUNTS, "league": L, "games": {},
           "backtest": dict(BACKTEST, note="mean absolute error in yards per player-game with this rule, 2019 to 2022 and 2023 to 2025 (reports/props_backtest4.csv: base for receiving and rushing, combo for passing)")}
    rows = []
    for g in wk.itertuples():
        sp = None if pd.isna(g.spread_line) else float(g.spread_line)   # nflverse: positive when the home team is favoured
        wd = None if (bool(g.dome) or pd.isna(g.wind)) else float(g.wind)   # kickoff forecast once one is usable (weather.apply_to_games), else unknown
        mk = closing(plog, g.game_id) if len(plog) else None
        out["games"][g.game_id] = {g.away_team: project_game(g.away_team, g.home_team, R, RU, Q, D, V, L, roster, None if sp is None else -sp, g.total_line, wd, mk), g.home_team: project_game(g.home_team, g.away_team, R, RU, Q, D, V, L, roster, sp, g.total_line, wd, mk)}
        for team, side in out["games"][g.game_id].items():
            def add(r, stat, proj, volume):
                rows.append({"season": season, "week": week, "game_id": g.game_id, "team": team, "player_id": r["player_id"], "name": r["name"], "stat": stat, "proj": proj, "proj_volume": volume, "run_at": run_at})
            for r in side["receivers"]:
                if not r["out"]: add(r, "rec_yards", r["proj_rec_yards"], r["proj_targets"]); add(r, "rec_catches", r["proj_catches"], r["proj_targets"]); add(r, "rec_td", r["proj_rec_td"], r["proj_targets"])
            for r in side["rushers"]:
                if not r["out"]: add(r, "rush_yards", r["proj_rush_yards"], r["proj_carries"]); add(r, "rush_td", r["proj_rush_td"], r["proj_carries"])
            for r in side["qb"][:1]:
                if not r["out"]: add(r, "pass_yards", r["proj_pass_yards"], r["proj_dropbacks"]); add(r, "pass_td", r["proj_pass_td"], r["proj_dropbacks"]); add(r, "pass_int", r["proj_int"], r["proj_dropbacks"])
    pr = pd.DataFrame(rows)
    if len(pr):
        pr.to_csv(REP / f"props_{season}_wk{week}.csv", index=False)
        md = [f"# Week {week}, {season}: player projections (readings, graded next run)", "", f"Volume (the team's plays per game moved by the game script from the closing spread and total, shared among the players who are playing by usage decayed {DECAY} per game back) x the player's yards per touch shrunk toward the league (receivers {K['rec']:.0f} targets, rushers {K['rush']:.0f} carries, QBs {K['pass']:.0f} dropbacks of weight) and moved toward what the defense allows (receivers {W['rec']:.0%}, rushers {W['rush']:.0%}, QBs {W['pass']:.0%}) x the median factor (receivers {MED['rec']}, rushers {MED['rush']}, QBs {MED['pass']}). Passing yards also blend the opponent's allowed dropbacks (a quarter) and drop {abs(WIND_C['pass']):.1%} per mph of kickoff wind above 10. The rule four rounds of backtest chose: {BACKTEST['rec_yards'][0]} / {BACKTEST['rec_yards'][1]} yards off on receiving, {BACKTEST['rush_yards'][0]} / {BACKTEST['rush_yards'][1]} on rushing and {BACKTEST['pass_yards'][0]} / {BACKTEST['pass_yards'][1]} on passing yards per player-game, 2019-22 / 2023-25 (reports/props_backtest4.csv). Receptions: targets x catch rate shrunk toward the league ({K_CATCH:.0f} targets) x {MED_CATCH}; touchdowns: volume x his rate shrunk toward the league ({K_TD['rec']:.0f} / {K_TD['rush']:.0f} / {K_TD['pass']:.0f} touches), receiving and passing scores moved {TD_MARGIN['rec']:.1%} per point of expected margin; interceptions at the league rate (reports/props_backtest5.csv). Not a market comparison. Built {run_at}.", "", pr.drop(columns=["run_at"]).to_markdown(index=False), ""]
        (REP / f"props_{season}_wk{week}.md").write_text("\n".join(md))
    out["market_lines"] = int(sum(1 for gm in out["games"].values() for side in gm.values() for grp in ("receivers", "rushers", "qb") for r in side[grp] if any(k.startswith("mkt_") for k in r)))
    if (TR / "props_vs_market.csv").exists():
        vm_all = pd.read_csv(TR / "props_vs_market.csv"); out["market"] = market_summary(vm_all); out["market_rows"] = int(len(vm_all))
    if graded is not None and len(graded):
        s = graded.groupby("stat").agg(n=("error", "size"), mae=("error", lambda e: round(float(e.abs().mean()), 2)), bias=("error", lambda e: round(float(e.mean()), 2))).reset_index()
        out["graded"] = s.to_dict("records")
    (OUT / "props.json").write_text(json.dumps(out, default=lambda v: None if (isinstance(v, float) and np.isnan(v)) else (v.item() if hasattr(v, "item") else str(v))))
    print("props", len(pr), "projections for week", week, "graded rows", 0 if graded is None else len(graded), "market lines on the cards", out["market_lines"], "graded against the market", out.get("market_rows", 0))


if __name__ == "__main__":
    main()
