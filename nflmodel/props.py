"""Player against scheme, matchup projections and the props track record (23 Sep 2026).

From data/processed/scheme_plays.parquet (every play since 2016 with the participation and FTN tags): each QB,
receiver and rusher's numbers over his last WINDOW games, split by the looks he faced (man, zone, pressure, clean,
blitz, light and heavy boxes), and each defense's allowed numbers and mix over its last WINDOW games. For every
game of the current week, each player's projected volume and yards against that defense's mix:
  receivers: targets = his target share x the team's pass plays per game; yards per target in the mix = his yards
             per target against man x the defense's man rate + against zone x (1 - man rate), when both splits
             have MIN_SPLIT targets, else his overall; then moved half way toward what the defense allows per
             target relative to the league (a hand-set half weight, stated on the page, to be tuned on the graded record)
  rushers:   carries = share x runs per game; yards per carry from his light-box and heavy-box splits weighted by
             the defense's heavy-box rate, moved half way toward the defense's allowed yards per carry
  QBs:       dropbacks per game; EPA and yards per dropback under pressure / clean weighted by the defense's pressure rate
Projections are readings and get graded every run against what happened (data/tracker/props_graded.csv), so
they build a record before anyone bets on them. Nothing here feeds the game model.
Usage: python -m nflmodel.props   writes data/processed/props.json, reports/props_<season>_wk<week>.csv and .md, grades last week"""
from __future__ import annotations
import json
import numpy as np, pandas as pd
from .features import RAW, OUT, ROOT
WINDOW, MIN_SPLIT, MIN_VOL, DEF_WEIGHT = 17, 15, 8, 0.5
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
    """His plays over his teams' plays in the same games (a player traded in keeps the usage he had elsewhere)."""
    pairs = g.groupby(["game_id", "posteam"]).size()
    tot = float(sum(team_by_game.get(k, 0) for k in pairs.index))
    return float(len(g)) / tot if tot else 0.0


def receivers(d: pd.DataFrame, names: dict) -> dict:
    out = {}
    t = d[d.pass_play & d.receiver_player_id.notna()]
    team_pass = t.groupby(["game_id", "posteam"]).size()
    for pid, g in t.groupby("receiver_player_id"):
        if names.get(pid, ("", ""))[1] == "QB":
            continue
        g = _last(g); tgt = len(g)
        if tgt < MIN_VOL:
            continue
        team = g.sort_values(["season", "week"]).posteam.iloc[-1]
        share = _share(g, team_pass)
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
        g = _last(g); n = len(g)
        if n < MIN_VOL:
            continue
        team = g.sort_values(["season", "week"]).posteam.iloc[-1]
        out[pid] = {"name": names.get(pid, (pid, ""))[0], "team": team, "games": int(g.game_id.nunique()), "carries": int(n), "carries_pg": round(n / g.game_id.nunique(), 2), "share": round(_share(g, team_run), 3),
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
                     "pass_plays_pg": round(len(ps) / max(g.game_id.nunique(), 1), 1), "runs_pg": round(len(run) / max(g.game_id.nunique(), 1), 1)}
    return out


def teams_volume(d: pd.DataFrame) -> dict:
    out = {}
    for team, g in d.groupby("posteam"):
        g = _last(g); n = max(g.game_id.nunique(), 1)
        out[team] = {"pass_plays_pg": round(float(g.pass_play.sum()) / n, 1), "runs_pg": round(float(g.play_type.eq("run").sum()) / n, 1), "dropbacks_pg": round(float(g.dropback.sum()) / n, 1)}
    return out


def league_baselines(d: pd.DataFrame) -> dict:
    ps = d[d.pass_play]; run = d[d.play_type.eq("run")]; db = d[d.dropback]
    return {"ypt": round(float(ps.yards_gained.fillna(0).mean()), 2), "epa_pt": round(float(ps.epa.mean()), 3), "catch": round(float(ps.complete_pass.fillna(0).mean()), 3), "ypc": round(float(run.yards_gained.fillna(0).mean()), 2), "ypd": round(float(db.yards_gained.fillna(0).mean()), 2),
            "man": round(float(ps[ps.cov_known].man.mean()), 3) if ps.cov_known.any() else None, "pressure": (round(float(db.pressure.mean()), 3) if db.pressure.notna().any() else None), "heavy_box": (round(float((run.box >= 8).mean()), 3) if run.box.notna().any() else None)}


def _mix(a: dict | None, b: dict | None, rate: float | None, key: str, fallback: float) -> float:
    """a in look x rate + b outside it x (1 - rate), when both splits and the rate exist; else the fallback."""
    if a is None or b is None or rate is None:
        return fallback
    return a[key] * rate + b[key] * (1 - rate)


def _toward(v: float, allowed: float | None, league: float) -> float:
    return v if allowed is None else v * (1 + DEF_WEIGHT * (allowed / league - 1)) if league else v


def project_game(team: str, opp: str, R: dict, RU: dict, Q: dict, D: dict, V: dict, L: dict, roster: pd.DataFrame) -> dict:
    """One offense against one defense: every rostered receiver, rusher and QB with a profile, projected."""
    dd = D.get(opp, {}); vol = V.get(team, {}); ro = roster[roster.team == team].set_index("player_id") if len(roster) else pd.DataFrame()
    def status(pid):
        if pid not in ro.index: return "not on roster"
        r = ro.loc[pid]; lab = r.roster if isinstance(r.roster, str) and r.roster != "Active" else (r.report if isinstance(r.report, str) else "")
        return lab or ""
    OUT_WORDS = ("Out", "Doubtful", "IR", "PUP", "Suspended", "Exempt", "NFI", "Retired", "not on roster")
    rec = []
    for pid, p in R.items():
        if p["team"] != team or pid not in ro.index: continue
        st = status(pid); is_out = any(st.startswith(w) for w in OUT_WORDS)
        ypt_mix = _mix(p["vs_man"], p["vs_zone"], dd.get("man"), "yds", p["ypt"]); ypt = _toward(ypt_mix, dd.get("ypt_allowed"), L["ypt"])
        tg = p["share"] * vol.get("pass_plays_pg", 0)
        rec.append({"player_id": pid, "name": p["name"], "status": st, "out": is_out, "targets_pg": p["targets_pg"], "share": p["share"], "proj_targets": round(tg, 1), "proj_catches": round(tg * p["catch"], 1),
                    "ypt": p["ypt"], "ypt_mix": round(ypt_mix, 2), "proj_ypt": round(ypt, 2), "proj_rec_yards": round(tg * ypt, 1), "proj_rec_td": round(tg * p["td_pt"], 2),
                    "vs_man": p["vs_man"], "vs_zone": p["vs_zone"], "vs_press": p["vs_press"], "adot": p["adot"], "games": p["games"], "targets": p["targets"]})
    # volume is shared out among the players who are playing: an absent player's targets go to the others in proportion
    # to their usage, and the team's targets add up to its pass plays (97%: the rest are throwaways and spikes)
    act = [r for r in rec if not r["out"]]; tot = sum(r["share"] for r in act)
    for r in rec:
        tg = (r["share"] / tot * vol.get("pass_plays_pg", 0) * 0.97) if (tot and not r["out"]) else r["share"] * vol.get("pass_plays_pg", 0) * 0.97
        r.update({"proj_targets": round(tg, 1), "proj_catches": round(tg * (r["proj_catches"] / r["proj_targets"] if r["proj_targets"] else 0), 1), "proj_rec_yards": round(tg * r["proj_ypt"], 1), "proj_rec_td": round(tg * (r["proj_rec_td"] / r["proj_targets"] if r["proj_targets"] else 0), 2)})
    rec.sort(key=lambda r: (r["out"], -r["proj_targets"]))
    rus = []
    for pid, p in RU.items():
        if p["team"] != team or pid not in ro.index: continue
        st = status(pid); is_out = any(st.startswith(w) for w in OUT_WORDS)
        ypc_mix = _mix(p["heavy"], p["light"] if p["light"] else p["mid"], dd.get("heavy_box"), "yds", p["ypc"]); ypc = _toward(ypc_mix, dd.get("ypc_allowed"), L["ypc"])
        ca = p["share"] * vol.get("runs_pg", 0)
        rus.append({"player_id": pid, "name": p["name"], "status": st, "out": is_out, "carries_pg": p["carries_pg"], "share": p["share"], "proj_carries": round(ca, 1), "ypc": p["ypc"], "ypc_mix": round(ypc_mix, 2), "proj_ypc": round(ypc, 2),
                    "proj_rush_yards": round(ca * ypc, 1), "proj_rush_td": round(ca * p["td_pc"], 2), "light": p["light"], "heavy": p["heavy"], "games": p["games"], "carries": p["carries"]})
    act = [r for r in rus if not r["out"]]; tot = sum(r["share"] for r in act)
    for r in rus:
        ca = (r["share"] / tot * vol.get("runs_pg", 0)) if (tot and not r["out"]) else r["share"] * vol.get("runs_pg", 0)
        r.update({"proj_carries": round(ca, 1), "proj_rush_yards": round(ca * r["proj_ypc"], 1), "proj_rush_td": round(ca * (r["proj_rush_td"] / r["proj_carries"] if r["proj_carries"] else 0), 2)})
    rus.sort(key=lambda r: (r["out"], -r["proj_carries"]))
    qbs = []
    for pid, p in Q.items():
        if p["team"] != team or pid not in ro.index: continue
        st = status(pid); is_out = any(st.startswith(w) for w in OUT_WORDS)
        ypd_mix = _mix(p["press"], p["clean"], dd.get("pressure"), "yds", p["ypd"]); ypd = _toward(ypd_mix, dd.get("ypd_allowed"), L["ypd"])
        epa_mix = _mix(p["press"], p["clean"], dd.get("pressure"), "epa", p["epa_db"])
        dbs = vol.get("dropbacks_pg", p["dropbacks_pg"])
        qbs.append({"player_id": pid, "name": p["name"], "status": st, "out": is_out, "dropbacks_pg": p["dropbacks_pg"], "epa_db": p["epa_db"], "epa_mix": round(epa_mix, 3), "ypd": p["ypd"], "ypd_mix": round(ypd_mix, 2), "proj_ypd": round(ypd, 2),
                    "proj_pass_yards": round(dbs * ypd, 1), "proj_pass_td": round(dbs * p["td_db"], 2), "proj_int": round(dbs * p["int_db"], 2), "press": p["press"], "clean": p["clean"], "blitz": p["blitz"], "noblitz": p["noblitz"], "vs_man": p["vs_man"], "vs_zone": p["vs_zone"], "games": p["games"], "dropbacks": p["dropbacks"]})
    qbs.sort(key=lambda r: (r["out"], -r["dropbacks_pg"]))
    return {"defense": dd, "volume": vol, "qb": qbs[:2], "receivers": rec[:8], "rushers": rus[:4]}


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
        ry = plays[plays.pass_play].groupby(["game_id", "receiver_player_id"]).agg(actual=("yards_gained", "sum"), n=("play_id", "count")).reset_index().rename(columns={"receiver_player_id": "player_id"})
        rr = plays[plays.play_type.eq("run")].groupby(["game_id", "rusher_player_id"]).agg(actual=("yards_gained", "sum"), n=("play_id", "count")).reset_index().rename(columns={"rusher_player_id": "player_id"})
        py = plays[plays.dropback].groupby(["game_id", "passer_player_id"]).agg(actual=("yards_gained", "sum"), n=("play_id", "count")).reset_index().rename(columns={"passer_player_id": "player_id"})
        played = set(plays.game_id)
        for _, r in pr.iterrows():
            if r.game_id not in played or ((done.game_id == r.game_id) & (done.player_id == r.player_id) & (done.stat == r.stat)).any(): continue
            src = {"rec_yards": ry, "rush_yards": rr, "pass_yards": py}[r.stat]; hit = src[(src.game_id == r.game_id) & (src.player_id == r.player_id)]
            actual = float(hit.actual.iloc[0]) if len(hit) else 0.0; vol_ = int(hit.n.iloc[0]) if len(hit) else 0
            rows.append({"season": season, "week": wk, "game_id": r.game_id, "team": r.team, "player_id": r.player_id, "name": r["name"], "stat": r.stat, "proj": r.proj, "proj_volume": r.proj_volume, "actual": actual, "actual_volume": vol_, "error": round(actual - r.proj, 1), "graded_at": run_at})
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
    a = _asof(d, season, week); names = names_by_id(range(season - 2, season + 1))
    roster = pd.read_parquet(OUT / "roster_now.parquet") if (OUT / "roster_now.parquet").exists() else pd.DataFrame(columns=["team", "player_id", "roster", "report"])
    R, RU, Q, D, V, L = receivers(a, names), rushers(a, names), passers(a, names), defenses(a), teams_volume(a), league_baselines(a)
    wk = games[(games.season == season) & (games.week == week)]
    out = {"season": season, "week": week, "built": run_at, "window_games": WINDOW, "min_split": MIN_SPLIT, "def_weight": DEF_WEIGHT, "league": L, "games": {}}
    rows = []
    for g in wk.itertuples():
        out["games"][g.game_id] = {g.away_team: project_game(g.away_team, g.home_team, R, RU, Q, D, V, L, roster), g.home_team: project_game(g.home_team, g.away_team, R, RU, Q, D, V, L, roster)}
        for team, side in out["games"][g.game_id].items():
            for r in side["receivers"]:
                if not r["out"]: rows.append({"season": season, "week": week, "game_id": g.game_id, "team": team, "player_id": r["player_id"], "name": r["name"], "stat": "rec_yards", "proj": r["proj_rec_yards"], "proj_volume": r["proj_targets"], "run_at": run_at})
            for r in side["rushers"]:
                if not r["out"]: rows.append({"season": season, "week": week, "game_id": g.game_id, "team": team, "player_id": r["player_id"], "name": r["name"], "stat": "rush_yards", "proj": r["proj_rush_yards"], "proj_volume": r["proj_carries"], "run_at": run_at})
            for r in side["qb"][:1]:
                if not r["out"]: rows.append({"season": season, "week": week, "game_id": g.game_id, "team": team, "player_id": r["player_id"], "name": r["name"], "stat": "pass_yards", "proj": r["proj_pass_yards"], "proj_volume": r["dropbacks_pg"], "run_at": run_at})
    pr = pd.DataFrame(rows)
    if len(pr):
        pr.to_csv(REP / f"props_{season}_wk{week}.csv", index=False)
        md = [f"# Week {week}, {season}: player projections (readings, graded next run)", "", f"Projected volume x yards per touch in the opponent's mix (man/zone, box, pressure), moved {DEF_WEIGHT:.0%} of the way toward what the defense allows. Not a market comparison. Built {run_at}.", "", pr.drop(columns=["run_at"]).to_markdown(index=False), ""]
        (REP / f"props_{season}_wk{week}.md").write_text("\n".join(md))
    if graded is not None and len(graded):
        s = graded.groupby("stat").agg(n=("error", "size"), mae=("error", lambda e: round(float(e.abs().mean()), 1)), bias=("error", lambda e: round(float(e.mean()), 1))).reset_index()
        out["graded"] = s.to_dict("records")
    (OUT / "props.json").write_text(json.dumps(out, default=lambda v: None if (isinstance(v, float) and np.isnan(v)) else (v.item() if hasattr(v, "item") else str(v))))
    print("props", len(pr), "projections for week", week, "graded rows", 0 if graded is None else len(graded))


if __name__ == "__main__":
    main()
