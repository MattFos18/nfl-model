"""Player season totals and the breakout watch (23 Sep 2026).

A player's season total = what he has so far + his per-game mean against an average defense x the games his team
has left x a fitted share (AVAIL), blended with the pace baseline (BLEND: his own per-game so far over the whole
schedule); both constants fitted on 2016 to 2018 on the season-total error. The
per-game mean is the props rule's own volume and rate (props.py: usage share decayed 0.85 per game back with the
season and team fades, x the team's plays per game over its last 17, x his yards per touch shrunk toward the
league), without the game script, the opponent and the median factor, since a season total is a sum of means.
Breakout watch: a player projected inside the top TOP_N of his kind at a per-game rate at least BREAK_UP times his
previous season's per-game rate (a return from a short injury season is not one); new to the top: no previous season. Backtest: experiments/player_season_backtest.py (reports/player_season_backtest.csv), as of
weeks 1, 5, 9 and 13 of 2019 to 2025 against the actual totals, beside the pace and last-season baselines, split
2019-22 / 2023-25; and how often the breakout flag came true.
"""
from __future__ import annotations
import numpy as np, pandas as pd
from pathlib import Path
from . import props as PR

ROOT = Path(__file__).resolve().parent.parent
OUT, RAW, REP = ROOT / "data" / "processed", ROOT / "data" / "raw", ROOT / "reports"
KINDS = {"rec": ("receiver_player_id", "rec_yards"), "rush": ("rusher_player_id", "rush_yards"), "pass": ("passer_player_id", "pass_yards")}
MIN_PG = {"rec": 2.5, "rush": 4.0, "pass": 20.0}      # per-game volume (targets, carries, dropbacks) a player needs to be projected
TOP_N = {"rec": 24, "rush": 24, "pass": 12}
BREAK_UP = 1.25
# the share of his team's remaining games his per-game mean is applied to, and the weight of the pace baseline in the
# blend, by kind: both fitted on 2016 to 2018 as of the same weeks on the season-total error (reports/player_season_backtest.csv,
# fit rows). The share sits below the share of games such players actually play (0.77, 0.75, 0.74: avail_mean_share rows)
# because the misses are one-sided and the pace half carries part of the load
AVAIL = {"rec": 0.65, "rush": 0.6, "pass": 0.5}
BLEND = {"rec": 0.5, "rush": 0.5, "pass": 0.75}
BACKTEST = {}   # filled from reports/player_season_backtest.csv by export_web (mean absolute error of the season total by kind and window)


def season_actuals(d: pd.DataFrame, season: int, through_week: int | None = None) -> pd.DataFrame:
    """Every player's regular-season yards, touchdowns and games by kind, through `through_week` (exclusive) or the
    whole season. One row per (kind, player)."""
    x = d[(d.season == season) & (d.week <= 18)]
    if through_week is not None:
        x = x[x.week < through_week]
    rows = []
    rec = x[x.pass_play & x.receiver_player_id.notna()]
    for pid, g in rec.groupby("receiver_player_id"):
        rows.append({"kind": "rec", "player_id": pid, "yards": float(g.yards_gained.fillna(0).sum()), "td": float(g.pass_touchdown.fillna(0).sum()), "games": int(g.game_id.nunique()), "touches": int(len(g)), "catches": float(g.complete_pass.fillna(0).sum())})
    run = x[x.play_type.eq("run") & x.rusher_player_id.notna()]
    for pid, g in run.groupby("rusher_player_id"):
        rows.append({"kind": "rush", "player_id": pid, "yards": float(g.yards_gained.fillna(0).sum()), "td": float(g.rush_touchdown.fillna(0).sum()), "games": int(g.game_id.nunique()), "touches": int(len(g)), "catches": np.nan})
    ps = x[x.dropback & x.passer_player_id.notna()]
    for pid, g in ps.groupby("passer_player_id"):
        pp = g[g.pass_play]
        rows.append({"kind": "pass", "player_id": pid, "yards": float(pp.yards_gained.fillna(0).sum()), "td": float(pp.pass_touchdown.fillna(0).sum()), "games": int(g.game_id.nunique()), "touches": int(len(g)), "catches": np.nan})
    return pd.DataFrame(rows, columns=["kind", "player_id", "yards", "td", "games", "touches", "catches"])


def roster_at(season: int, week: int) -> pd.DataFrame:
    """Active players by team as of the week, from the weekly roster (the latest week at or before it)."""
    f = RAW / "rosters" / f"roster_weekly_{season}.parquet"
    if not f.exists():
        return pd.DataFrame(columns=["team", "player_id", "position", "name"])
    r = pd.read_parquet(f, columns=["team", "gsis_id", "status", "week", "position", "full_name"]).dropna(subset=["gsis_id"])
    wk = r[r.week <= week].week.max() if (r.week <= week).any() else r.week.min()
    r = r[(r.week == wk) & (r.status == "ACT")]
    return r.rename(columns={"gsis_id": "player_id", "full_name": "name"})[["team", "player_id", "position", "name"]].drop_duplicates("player_id")


def per_game(R: dict, RU: dict, Q: dict, V: dict, L: dict) -> pd.DataFrame:
    """Each profiled player's per-game mean against an average defense: volume x rate, no script, no median factor."""
    rows = []
    for pid, p in R.items():
        v = V.get(p["team"], {}); tg = p["share"] * v.get("pass_plays_pg", 0.0) * 0.97
        ypt = PR._shrunk(p["ypt"], p["targets"], L["ypt"], PR.K["rec"]); td = PR._shrunk(p["td_pt"], p["targets"], L["td_pt"], PR.K_TD["rec"]); ct = PR._shrunk(p["catch"], p["targets"], L["catch"], PR.K_CATCH)
        rows.append({"kind": "rec", "player_id": pid, "name": p["name"], "pos": p["pos"], "team": p["team"], "volume_pg": tg, "rate": ypt, "yards_pg": tg * ypt, "td_pg": tg * td, "catches_pg": tg * ct, "profile_games": p["games"]})
    for pid, p in RU.items():
        v = V.get(p["team"], {}); ca = p["share"] * v.get("runs_pg", 0.0)
        ypc = PR._shrunk(p["ypc"], p["carries"], L["ypc"], PR.K["rush"]); td = PR._shrunk(p["td_pc"], p["carries"], L["td_pc"], PR.K_TD["rush"])
        rows.append({"kind": "rush", "player_id": pid, "name": p["name"], "pos": p["pos"], "team": p["team"], "volume_pg": ca, "rate": ypc, "yards_pg": ca * ypc, "td_pg": ca * td, "catches_pg": np.nan, "profile_games": p["games"]})
    for pid, p in Q.items():
        v = V.get(p["team"], {}); db = v.get("dropbacks_pg", p["dropbacks_pg"])
        ypd = PR._shrunk(p["ypd"], p["dropbacks"], L["ypd"], PR.K["pass"]); td = PR._shrunk(p["td_db"], p["dropbacks"], L["td_db"], PR.K_TD["pass"])
        rows.append({"kind": "pass", "player_id": pid, "name": p["name"], "pos": p["pos"], "team": p["team"], "volume_pg": db, "rate": ypd, "yards_pg": db * ypd, "td_pg": db * td, "catches_pg": np.nan, "profile_games": p["games"]})
    return pd.DataFrame(rows)


def project(d: pd.DataFrame, names: dict, games: pd.DataFrame, season: int, week: int, roster: pd.DataFrame | None = None, mode: str = "asof", avail: dict | None = None, blend: dict | None = None) -> pd.DataFrame:
    """Season totals as of `week`. mode "asof": games before `week` are the season so far and the team's games from
    `week` on are left (the backtest); "now": played games so far, unplayed games left. A player is projected when he
    is active on his team's roster, has a profile and reaches MIN_PG of volume; only the starting QB by dropbacks per team."""
    avail = avail or AVAIL; blend = BLEND if blend is None else blend
    a = PR._asof(d, season, week)
    R, RU, Q, V, L = PR.receivers(a, names), PR.rushers(a, names), PR.passers(a, names), PR.teams_volume(a), PR.league_baselines(a)
    pg = per_game(R, RU, Q, V, L)
    ro = roster if roster is not None else roster_at(season, week)
    pg = pg.merge(ro[["team", "player_id", "position"]].rename(columns={"team": "roster_team"}), on="player_id", how="inner")
    pg = pg[pg.team == pg.roster_team].drop(columns="roster_team")     # his profile's latest team is the roster's team
    pg["pos"] = np.where(pg.pos.eq("") | pg.pos.isna(), pg.position, pg.pos); pg = pg.drop(columns="position")
    pg = pg[pg.volume_pg >= pg.kind.map(MIN_PG)]
    qb = pg[pg.kind == "pass"].sort_values("volume_pg", ascending=False).drop_duplicates("team")
    pg = pd.concat([pg[pg.kind != "pass"], qb], ignore_index=True)
    reg = games[(games.season == season) & (games.game_type == "REG")]
    left = reg[reg.week >= week] if mode == "asof" else reg[reg.home_score.isna()]
    played_g = reg[reg.week < week] if mode == "asof" else reg[reg.home_score.notna()]
    n_left = {t: int(((left.home_team == t) | (left.away_team == t)).sum()) for t in set(reg.home_team)}
    n_played = {t: int(((played_g.home_team == t) | (played_g.away_team == t)).sum()) for t in set(reg.home_team)}
    n_total = {t: n_left.get(t, 0) + n_played.get(t, 0) for t in n_left}
    so_far = season_actuals(d, season, week if mode == "asof" else 99).set_index(["kind", "player_id"])
    prev = season_actuals(d, season - 1).set_index(["kind", "player_id"])
    out = pg.copy()
    key = list(zip(out.kind, out.player_id))
    for c, src in [("yards_so_far", "yards"), ("td_so_far", "td"), ("games_so_far", "games"), ("catches_so_far", "catches")]:
        out[c] = [float(so_far[src].get(k, 0.0)) if k in so_far.index else 0.0 for k in key]
    for c, src in [("prev_yards", "yards"), ("prev_td", "td"), ("prev_games", "games")]:
        out[c] = [float(prev[src].get(k, 0.0)) if k in prev.index else 0.0 for k in key]
    out["team_games_left"] = out.team.map(n_left).fillna(0).astype(int); out["team_games_played"] = out.team.map(n_played).fillna(0).astype(int); out["team_games"] = out.team.map(n_total).fillna(0).astype(int)
    out["avail"] = out.kind.map(avail)
    out["games_left_exp"] = out.team_games_left * out.avail
    # baselines: pace (his season so far per team game, over the whole schedule; last season when nothing is played), last season
    out["pace_yards"] = np.where(out.team_games_played > 0, out.yards_so_far / out.team_games_played.clip(lower=1) * out.team_games, out.prev_yards)
    out["blend"] = out.kind.map(blend)
    out["own_yards"] = out.yards_so_far + out.yards_pg * out.games_left_exp
    out["proj_yards"] = (1 - out.blend) * out.own_yards + out.blend * out.pace_yards
    out["proj_td"] = out.td_so_far + out.td_pg * out.games_left_exp
    out["proj_catches"] = np.where(out.kind == "rec", out.catches_so_far + out.catches_pg.fillna(0) * out.games_left_exp, np.nan)
    out["rank"] = out.groupby("kind").proj_yards.rank(ascending=False, method="first").astype(int)
    # breakout: a top-N projection at a per-game rate at least BREAK_UP x his previous season's per-game rate (so a
    # return from a short injury season is not one); new_top: a top-N projection with no previous season at all
    out["proj_pg"] = out.proj_yards / out.team_games.clip(lower=1); out["prev_pg"] = out.prev_yards / out.prev_games.clip(lower=1)
    out["breakout"] = (out["rank"] <= out.kind.map(TOP_N)) & (out.proj_pg >= BREAK_UP * out.prev_pg) & (out.prev_games > 0)
    out["new_top"] = (out["rank"] <= out.kind.map(TOP_N)) & (out.prev_games == 0)
    out["season"], out["week"] = season, week
    return out.sort_values(["kind", "rank"]).reset_index(drop=True)


def run_now() -> pd.DataFrame:
    from .lines import current_week
    from .positions import names_by_id
    games = pd.read_parquet(OUT / "games.parquet"); season, week = current_week(games)
    d = pd.read_parquet(OUT / "scheme_plays.parquet"); d = d[d.play_type.isin(["pass", "run"])]
    names = names_by_id(range(season - 2, season + 1))
    return project(d, names, games, season, week, mode="now")


if __name__ == "__main__":
    p = run_now()
    for k in KINDS:
        print(k); print(p[p.kind == k].head(12)[["name", "pos", "team", "yards_so_far", "yards_pg", "team_games_left", "proj_yards", "proj_td", "prev_yards", "pace_yards", "breakout"]].round(1).to_string(index=False))
