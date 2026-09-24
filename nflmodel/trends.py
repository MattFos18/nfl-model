"""Situational trends and injuries, computed as-of each game (nothing from that game or later), one row per
(game_id, team). Each is a candidate input for the points regression and is tested in tune.additions:
it stays only if it lowers the points miss on 2019 to 2022, and the record-type ones also have to persist
from 2012 to 2018 into 2019 to 2025.

Trends (from the schedule file, 1999 to now, and team_games):
  team_home_edge   this team's home-minus-away margin over the previous three seasons, halved, shrunk (k=24 games)
  h2h_cover        this team's average cover margin (result minus spread, its view) in the last six meetings with
                   this opponent, shrunk (k=6)
  coach_ats        head coach's career cover margin per game before this game, shrunk (k=40)
  qb_ats           starting QB's career cover margin per game, shrunk (k=40)
  off_loss         1 if the team lost its previous game
  ref_over         referee's over rate vs the closing total in his previous games, shrunk to 0.5 (k=60)
  ref_home_cover   referee's home cover rate, shrunk (k=60)
  ref_pen          referee's penalties per game (both teams) minus league, shrunk (k=60)
  slot dummies     TNF, SNF, MNF are in primetime already; adds SUN_LATE and body_clock_early (a Pacific or
                   Mountain team playing at 1pm ET on the road)
  cold_edge        team's margin in cold games (under 35F) minus its margin in other games, previous three
                   seasons, shrunk (k=12), applied only when this game is cold; wind_edge the same for 15+ mph
  off_home_split   team's home-game EPA per play minus its away-game EPA per play, previous three seasons, shrunk

Injuries (nflverse injuries + snap counts, 2012 on):
  off_starters_out, def_starters_out   players on the final injury report as Out or Doubtful who played 50%+
                   of the team's offense (defense) snaps in its previous game. Matched by name within team.
  qb_out           1 if the previous game's 50%+ QB is Out or Doubtful
"""
from __future__ import annotations
import numpy as np, pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW, OUT = ROOT / "data" / "raw", ROOT / "data" / "processed"

TZ_WEST = {"SEA", "SF", "LA", "LAC", "LV", "ARI", "DEN"}  # Pacific and Mountain home bases (LV/ARI are Pacific in season)


def shrink(sum_, n, k, prior=0.0):
    return (sum_ + k * prior) / (n + k)


def long_games(games: pd.DataFrame) -> pd.DataFrame:
    """One row per (game, team) with the team's view of the result and line."""
    rows = []
    for side, opp in [("home", "away"), ("away", "home")]:
        m = games[["game_id", "season", "week", "game_type", "gameday", "kickoff_et", "hour_et", "slot", "weekday", f"{side}_team", f"{opp}_team",
                   f"{side}_score", f"{opp}_score", "spread_line", "total_line", "total", "result", f"{side}_coach", f"{side}_qb_id",
                   "referee", "temp", "wind", "dome", "roof"]].copy()
        m.columns = ["game_id", "season", "week", "game_type", "gameday", "kickoff_et", "hour_et", "slot", "weekday", "team", "opp", "pf", "pa",
                     "spread_line", "total_line", "total", "result", "coach", "qb_id", "referee", "temp", "wind", "dome", "roof"]
        m["home"] = side == "home"
        m["margin"] = m.pf - m.pa
        m["team_spread"] = np.where(m.home, m.spread_line, -m.spread_line)      # positive = this team favoured
        m["cover_margin"] = m.margin - m.team_spread                             # >0 covered
        rows.append(m)
    d = pd.concat(rows).sort_values(["gameday", "game_id", "home"]).reset_index(drop=True)
    d["order"] = np.arange(len(d))
    return d


def _prior_mean(d: pd.DataFrame, key: str, val: str, k: float, prior: float, window_seasons=None) -> pd.Series:
    """For each row, mean of `val` over earlier rows with the same `key`, shrunk. Rows ordered by `order`."""
    res = pd.Series(np.nan, index=d.index)
    d = d.sort_values("order")
    for key_val, g in d.groupby(key, sort=False):
        v = g[val].values.astype(float)
        s = g.season.values
        ok = ~np.isnan(v)
        vv = np.where(ok, v, 0.0)
        cs = np.cumsum(vv)
        cn = np.cumsum(ok.astype(float))
        prev_s = np.concatenate([[0.0], cs[:-1]])
        prev_n = np.concatenate([[0.0], cn[:-1]])
        if window_seasons:
            for i in range(len(g)):
                old = (s[:i] < s[i] - window_seasons)
                prev_s[i] -= vv[:i][old].sum()
                prev_n[i] -= ok[:i][old].sum()
        res.loc[g.index] = shrink(prev_s, prev_n, k, prior)
    return res


def trend_table(games: pd.DataFrame, tg: pd.DataFrame) -> pd.DataFrame:
    d = long_games(games[games.game_type.isin(["REG", "POST"])].copy())
    played = d.pf.notna()
    # --- team home edge: home margin minus away margin, previous 3 seasons
    d["home_margin"] = np.where(d.home & played, d.margin, np.nan)
    d["away_margin"] = np.where(~d.home & played, d.margin, np.nan)
    hm = _prior_mean(d, "team", "home_margin", 12, 0.0, window_seasons=3)
    am = _prior_mean(d, "team", "away_margin", 12, 0.0, window_seasons=3)
    d["team_home_edge"] = (hm - am) / 2
    # --- head to head
    d["pair"] = [tuple(sorted([a, b])) for a, b in zip(d.team, d.opp)]
    d["pair"] = d.pair.astype(str)
    d["cm"] = np.where(played, d.cover_margin, np.nan)
    d["h2h_cover"] = _prior_mean(d.assign(pair_team=d.pair + "|" + d.team), "pair_team", "cm", 6, 0.0)
    # --- coach and QB ATS
    d["coach_ats"] = _prior_mean(d, "coach", "cm", 40, 0.0)
    d["qb_ats"] = _prior_mean(d, "qb_id", "cm", 40, 0.0)
    # --- off a loss
    d = d.sort_values("order")
    prev_margin = d.groupby("team").margin.shift(1)
    d["off_loss"] = (prev_margin < 0).astype(float)
    # --- referee
    d["over_hit"] = np.where(played & d.total_line.notna(), (d.total > d.total_line).astype(float), np.nan)
    d["home_cov"] = np.where(played & d.home & d.spread_line.notna(), (d.result > d.spread_line).astype(float), np.nan)
    d["ref_over"] = _prior_mean(d, "referee", "over_hit", 60, 0.5)
    d["ref_home_cover"] = _prior_mean(d[d.home].copy(), "referee", "home_cov", 60, 0.5).reindex(d.index)
    d["ref_home_cover"] = d.groupby("game_id").ref_home_cover.transform("max")
    # penalties per game by referee (both teams), from team_box
    box = pd.read_parquet(OUT / "team_box.parquet")[["game_id", "team", "off_penalties"]]
    d = d.merge(box, on=["game_id", "team"], how="left")
    d["game_pen"] = d.groupby("game_id").off_penalties.transform("sum")
    league_pen = d[played].groupby("season").game_pen.transform("mean")
    d["pen_rel"] = np.where(played, d.game_pen - league_pen, np.nan)
    d["ref_pen"] = _prior_mean(d, "referee", "pen_rel", 60, 0.0)
    # --- slots and body clock
    d["sun_late"] = (d.slot == "SUN_LATE").astype(float)
    d["body_clock_early"] = ((~d.home) & d.team.isin(TZ_WEST) & (d.hour_et == 13)).astype(float)
    # --- cold and wind performance
    d["is_cold"] = ((d.dome == False) & (d.temp < 35)).astype(float)
    d["is_windy"] = ((d.dome == False) & (d.wind >= 15)).astype(float)
    d["cold_margin"] = np.where(played & (d.is_cold == 1), d.margin, np.nan)
    d["mild_margin"] = np.where(played & (d.is_cold == 0), d.margin, np.nan)
    d["cold_edge"] = (_prior_mean(d, "team", "cold_margin", 12, 0.0, 3) - _prior_mean(d, "team", "mild_margin", 12, 0.0, 3)) * d.is_cold
    d["windy_margin"] = np.where(played & (d.is_windy == 1), d.margin, np.nan)
    d["calm_margin"] = np.where(played & (d.is_windy == 0), d.margin, np.nan)
    d["wind_edge"] = (_prior_mean(d, "team", "windy_margin", 12, 0.0, 3) - _prior_mean(d, "team", "calm_margin", 12, 0.0, 3)) * d.is_windy
    # --- home/away split of offense EPA
    e = tg[["game_id", "team", "epa_play"]]
    d = d.merge(e, on=["game_id", "team"], how="left")
    d["home_epa"] = np.where(d.home, d.epa_play, np.nan)
    d["away_epa"] = np.where(~d.home, d.epa_play, np.nan)
    d["off_home_split"] = (_prior_mean(d, "team", "home_epa", 12, 0.0, 3) - _prior_mean(d, "team", "away_epa", 12, 0.0, 3)) * np.where(d.home, 1.0, -1.0)
    keep = ["game_id", "season", "week", "team", "opp", "home", "team_home_edge", "h2h_cover", "coach_ats", "qb_ats", "off_loss", "ref_over",
            "ref_home_cover", "ref_pen", "sun_late", "body_clock_early", "cold_edge", "wind_edge", "off_home_split", "is_cold", "is_windy"]
    return d[keep].reset_index(drop=True)


def _norm(name: pd.Series) -> pd.Series:
    return name.fillna("").str.lower().str.replace(r"[^a-z]", "", regex=True)


OL_POS = {"T", "G", "C", "OL", "OT", "OG"}


def _roster_names(seasons) -> dict:
    """gsis_id -> full name from the weekly rosters (snap counts carry names, not ids, so the join is by name)."""
    out = {}
    for s in seasons:
        f = RAW / "rosters" / f"roster_weekly_{s}.parquet"
        if f.exists():
            r = pd.read_parquet(f, columns=["gsis_id", "full_name"]).dropna().drop_duplicates("gsis_id")
            out.update(dict(zip(r.gsis_id, r.full_name)))
    return out


def injury_table(games: pd.DataFrame, seasons=range(2012, 2027)) -> pd.DataFrame:
    from .players import load_injuries
    snaps = []
    for s in seasons:
        g = RAW / "snap_counts" / f"snap_counts_{s}.parquet"
        if g.exists():
            snaps.append(pd.read_parquet(g))
    inj = load_injuries(seasons)   # the league's reports plus ESPN's same-day fill for the week being priced (players.load_injuries)
    snaps = pd.concat(snaps, ignore_index=True)
    fix = {"OAK": "LV", "SD": "LAC", "STL": "LA"}
    inj["team"] = inj.team.replace(fix)
    snaps["team"] = snaps.team.replace(fix)
    # keyed by player id (24 Sep 2026; it was the name, so "Patrick Surtain II" in the snap counts never met "Pat Surtain
    # II" on the injury report): the reports and rosters carry the gsis id, the snap counts the PFR id, mapped through
    # the rosters; a snap row with no id link falls back to the name inside its team and season
    pmap, nmap = {}, {}
    for s_ in seasons:
        f_ = RAW / "rosters" / f"roster_weekly_{s_}.parquet"
        if f_.exists():
            r_ = pd.read_parquet(f_, columns=["season", "team", "gsis_id", "pfr_id", "full_name"]).dropna(subset=["gsis_id"])
            pmap.update(dict(zip(r_.pfr_id.dropna(), r_.dropna(subset=["pfr_id"]).gsis_id)))
            r_["team"] = r_.team.replace(fix)
            nmap.update({(t_, int(se_), k_): g_ for t_, se_, k_, g_ in zip(r_.team, r_.season, _norm(r_.full_name), r_.gsis_id)})
    inj["key"] = inj.gsis_id
    snaps["key"] = snaps.pfr_player_id.map(pmap)
    miss = snaps.key.isna()
    snaps.loc[miss, "key"] = [nmap.get((t_, int(se_), k_)) for t_, se_, k_ in zip(snaps.team[miss], snaps.season[miss], _norm(snaps.player[miss]))]
    inj = inj[inj.report_status.isin(["Out", "Doubtful"])]
    # players on IR, PUP, suspended or otherwise off the active roster are not on the injury report but are out all the same
    from .players import load_rosters, NOT_AVAILABLE
    ros = load_rosters(seasons); ros = ros[ros.status.isin(NOT_AVAILABLE)].copy()
    ros["key"] = ros.gsis_id
    ros_out = {k: set(g.key) for k, g in ros.groupby(["season", "week", "team"])}
    # the team's previous game with snap data
    snaps = snaps.sort_values(["season", "week"])
    rows = []
    long = long_games(games)
    long = long[long.season.isin(seasons)]
    prev_lookup = {}
    for (season, team), g in snaps.groupby(["season", "team"]):
        prev_lookup[(season, team)] = g
    for r in long.itertuples():
        g = prev_lookup.get((r.season, r.team))
        if g is None:
            rows.append({"game_id": r.game_id, "team": r.team, "off_starters_out": np.nan, "def_starters_out": np.nan, "qb_out": np.nan, "ol_out": np.nan, "off_snap_out": np.nan, "def_snap_out": np.nan})
            continue
        before = g[g.week < r.week]
        if len(before) == 0:
            # first game of the season: use last season's final game
            g2 = prev_lookup.get((r.season - 1, r.team))
            before = g2[g2.week == g2.week.max()] if g2 is not None else before
        else:
            before = before[before.week == before.week.max()]
        starters_off = set(before[before.offense_pct >= 0.5].key)
        starters_def = set(before[before.defense_pct >= 0.5].key)
        qb = set(before[(before.position == "QB") & (before.offense_pct >= 0.5)].key)
        out = set(inj[(inj.season == r.season) & (inj.week == r.week) & (inj.team == r.team)].key) | ros_out.get((r.season, r.week, r.team), set())
        # offensive line continuity and snap-weighted absences: which of last game's linemen are out, and what share of
        # last game's offensive and defensive snaps belonged to players now out (a starter at 95% counts more than a 55% one)
        ol = before[before.position.isin(OL_POS) & (before.offense_pct >= 0.5)]
        ol_out = float(len(set(ol.key) & out))
        off_snap_out = float(before[before.key.isin(out)].offense_pct.clip(0, 1).sum())
        def_snap_out = float(before[before.key.isin(out)].defense_pct.clip(0, 1).sum())
        rows.append({"game_id": r.game_id, "team": r.team, "ol_out": ol_out, "off_snap_out": off_snap_out, "def_snap_out": def_snap_out, "off_starters_out": float(len(starters_off & out)),
                     "def_starters_out": float(len(starters_def & out)), "qb_out": float(len(qb & out) > 0)})
    return pd.DataFrame(rows)


def situation_extras(games: pd.DataFrame, seasons=range(2012, 2027)) -> pd.DataFrame:
    """Per (game, team): rain and snow at kickoff (from the play-by-play weather text, outdoor games only), miles travelled
    from the team's home stadium to the venue, and the time-zone shift in hours (positive = travelling east). Home teams
    travel 0. International venues use the stadium name. Known before kickoff, so usable as-of."""
    import pyarrow.parquet as pq
    from .weather import STADIUM, INTL
    wx = {}
    for s in seasons:
        f = ROOT / "data" / "raw" / "pbp" / f"play_by_play_{s}.parquet"
        if not f.exists():
            continue
        t = pq.read_table(f, columns=["game_id", "weather"]).to_pandas()
        wx.update(t.groupby("game_id").weather.first().to_dict())
    def venue(g):
        for k, v in INTL.items():
            if isinstance(g.stadium, str) and k.lower() in g.stadium.lower():
                return v
        if isinstance(g.stadium, str) and any(k in g.stadium.lower() for k in ["wembley", "tottenham", "twickenham", "craven"]):
            return INTL["London"]
        if isinstance(g.stadium, str) and ("allianz" in g.stadium.lower() or "deutsche bank" in g.stadium.lower() or "waldstadion" in g.stadium.lower()):
            return INTL["Munich"] if "allianz" in g.stadium.lower() else INTL["Frankfurt"]
        if isinstance(g.stadium, str) and "azteca" in g.stadium.lower():
            return INTL["Mexico City"]
        return STADIUM.get(g.home_team)
    def hav(a, b):
        if a is None or b is None:
            return np.nan
        la1, lo1, la2, lo2 = map(np.radians, [a[0], a[1], b[0], b[1]])
        h = np.sin((la2 - la1) / 2) ** 2 + np.cos(la1) * np.cos(la2) * np.sin((lo2 - lo1) / 2) ** 2
        return 3958.8 * 2 * np.arcsin(np.sqrt(h))
    # unplayed games: the latest kickoff forecast (weather.py) stands in for the weather text
    # (only forecasts within weather.USE_WITHIN_DAYS of kickoff; further out the game is priced as dry)
    from .weather import usable_forecast
    d = usable_forecast().reset_index()
    fc = {r.game_id: (float(r.precip_prob) if pd.notna(r.precip_prob) else 0.0, float(r.precip) if pd.notna(r.precip) else 0.0) for r in d.itertuples()}
    rows = []
    for g in games.itertuples():
        w = str(wx.get(g.game_id, "") or "").lower()
        outdoor = g.roof in ("outdoors", "open") if isinstance(g.roof, str) else True
        rain = float(outdoor and any(k in w for k in ["rain", "shower", "drizzle", "storm"]))
        if not w and g.game_id in fc and outdoor:
            # Open-Meteo gives precipitation in millimetres: rain when the hour's chance is 50%+ or 1 mm+ is forecast
            rain = float(fc[g.game_id][0] >= 50 or fc[g.game_id][1] >= 1.0)
        snow = float(outdoor and any(k in w for k in ["snow", "flurr", "sleet"]))
        v = venue(g)
        for side in ["home", "away"]:
            t = getattr(g, f"{side}_team")
            hm = STADIUM.get(t)
            miles = 0.0 if (side == "home" and not g.neutral) else hav(hm, v)
            tz = 0.0 if (side == "home" and not g.neutral) else ((((round((v[1] - hm[1]) / 15.0) + 12) % 24) - 12) if (v and hm) else np.nan)
            rows.append({"game_id": g.game_id, "team": t, "rain": rain, "snow": snow, "travel_miles": miles, "tz_shift": tz})
    return pd.DataFrame(rows)


def persistence(games: pd.DataFrame) -> pd.DataFrame:
    """Do referee, coach and head-to-head records persist from 2012 to 2018 into 2019 to 2025?"""
    d = long_games(games[(games.game_type == "REG") & games.home_score.notna()].copy())
    d["over_hit"] = (d.total > d.total_line).astype(float)
    d["home_cov"] = (d.result > d.spread_line).astype(float)
    d["covered"] = (d.cover_margin > 0).astype(float)
    out = []
    for name, key, val, minn, sub in [("referee over rate", "referee", "over_hit", 40, d.home), ("referee home cover rate", "referee", "home_cov", 40, d.home),
                                      ("coach cover rate", "coach", "covered", 40, d.season > 0), ("QB cover rate", "qb_id", "covered", 30, d.season > 0),
                                      ("head-to-head cover margin", "pair_team", "cover_margin", 6, d.season > 0)]:
        x = d[sub].copy()
        if key == "pair_team":
            x["pair_team"] = [str(tuple(sorted([a, b]))) + "|" + a for a, b in zip(x.team, x.opp)]
        a = x[(x.season >= 2012) & (x.season <= 2018)].groupby(key)[val].agg(["mean", "size"])
        b = x[(x.season >= 2019) & (x.season <= 2025)].groupby(key)[val].agg(["mean", "size"])
        j = a.join(b, lsuffix="_1", rsuffix="_2", how="inner")
        j = j[(j.size_1 >= minn) & (j.size_2 >= minn)]
        out.append({"trend": name, "n_keys": len(j), "corr_between_periods": j.mean_1.corr(j.mean_2) if len(j) > 3 else np.nan,
                    "top5_period1": j.sort_values("mean_1", ascending=False).head(5).mean_1.mean() if len(j) else np.nan,
                    "top5_in_period2": j.sort_values("mean_1", ascending=False).head(5).mean_2.mean() if len(j) else np.nan})
    return pd.DataFrame(out)


def continuity_table(games: pd.DataFrame, seasons=range(2013, 2027)) -> pd.DataFrame:
    """Offseason turnover, per (game, team): the share of last season's offensive and defensive snaps taken by players
    on this week's active roster (weekly rosters by name against last season's snap counts). 1.0 means the same
    unit; 0.6 means forty percent of last year's snaps walked out. In the model since 23 Sep 2026 as
    off_turnover_early and opp_def_turnover_early: (1 - share) for weeks 1 to 8, when the ratings still lean on
    last season (reports/continuity.csv, continuity2.csv)."""
    from .positions import snaps_by_game, norm
    snaps = snaps_by_game(range(min(seasons) - 1, max(seasons) + 1))
    ros = []
    for s in seasons:
        f = RAW / "rosters" / f"roster_weekly_{s}.parquet"
        if f.exists():
            r = pd.read_parquet(f, columns=["season", "week", "team", "full_name", "status"]); r["team"] = r.team.replace({"OAK": "LV", "SD": "LAC", "STL": "LA"}); ros.append(r[r.status == "ACT"])
    ros = pd.concat(ros, ignore_index=True); ros["key"] = ros.full_name.map(norm)
    roster_keys = {k: set(g.key) for k, g in ros.groupby(["season", "week", "team"])}
    last_off, last_def = {}, {}
    for (s, t), g in snaps.groupby(["season", "team"]):
        last_off[(s, t)] = g.groupby("key").offense_snaps.sum(); last_def[(s, t)] = g.groupby("key").defense_snaps.sum()
    def share(prev, keys):
        if prev is None or keys is None or prev.sum() == 0:
            return np.nan
        return float(prev[prev.index.isin(keys)].sum() / prev.sum())
    rows = []
    for r in long_games(games).itertuples():
        if r.season not in seasons:
            continue
        keys = roster_keys.get((r.season, r.week, r.team))
        rows.append({"game_id": r.game_id, "team": r.team, "off_continuity": share(last_off.get((r.season - 1, r.team)), keys), "def_continuity": share(last_def.get((r.season - 1, r.team)), keys)})
    return pd.DataFrame(rows)


if __name__ == "__main__":
    games = pd.read_parquet(OUT / "games.parquet")
    tg = pd.read_parquet(OUT / "team_games.parquet")
    t = trend_table(games, tg)
    i = injury_table(games)
    t = t.merge(i, on=["game_id", "team"], how="left")
    t = t.merge(situation_extras(games), on=["game_id", "team"], how="left")
    t = t.merge(continuity_table(games), on=["game_id", "team"], how="left")
    t.to_parquet(OUT / "trends_asof.parquet", index=False)
    print(t.shape)
    print(t[t.season == 2024].describe().T.round(3).to_string())
    p = persistence(games)
    p.to_csv(ROOT / "reports" / "trend_persistence.csv", index=False)
    print(p.round(3).to_string(index=False))
