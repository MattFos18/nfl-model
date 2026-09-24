"""Every other position, valued (player model phase 4, 22 Sep 2026).

The skill players (players.py) are valued by the EPA of their own touches. Nobody else has a play attributed to
him in the play-by-play, so each group gets the handle the data allows, always the same shape: a decayed, shrunk
rate per play as of a week, replacement level at the 25th percentile of regulars in earlier seasons, and a value
above replacement times the player's share of his unit's plays.

  QB         EPA per dropback (the QB rating in ratings.py), shown here beside everyone else.
  Defenders  impact plays: the -EPA of every play he is credited on (tackle, assist, TFL, sack, QB hit, pass
             defended, interception, forced or recovered fumble), per defensive snap. A tackle that ends a play
             short of the sticks is worth what it saved; an interception is worth what it took. Snaps come from
             the snap counts, matched by name.
  OL         on/off: the team's offensive EPA per play in games he played 50%+ of the snaps minus in the team's
             games he did not, over the last two seasons, shrunk toward zero by how many games without him there
             are. A lineman who never misses a game sits at zero: the data cannot separate him from his line.
  K, P       EPA per kick (field goals and extra points) and per punt, the kicking team's side.

All positions land in data/processed/player_values.parquet with a `group` column; the page shows every one.
Tested as model inputs in experiments/positions.py: the defenders' and linemen's value out, own and opponent, and
the availability-weighted skill offense (every regular who is playing, not only who is out).
"""
from __future__ import annotations
import numpy as np, pandas as pd
import pyarrow.parquet as pq
from .features import RAW, OUT, TEAM_FIX
from .players import PlayerValues, load_rosters, load_injuries, NOT_AVAILABLE, ROSTER_LABEL, DEFAULT, player_usage, _usage_frames

CREDIT = {"solo_tackle_1_player_id": 1.0, "solo_tackle_2_player_id": 1.0, "assist_tackle_1_player_id": 0.5, "assist_tackle_2_player_id": 0.5, "assist_tackle_3_player_id": 0.5, "assist_tackle_4_player_id": 0.5,
          "tackle_with_assist_1_player_id": 0.7, "tackle_with_assist_2_player_id": 0.7, "tackle_for_loss_1_player_id": 0.5, "tackle_for_loss_2_player_id": 0.5, "sack_player_id": 1.0,
          "qb_hit_1_player_id": 0.5, "qb_hit_2_player_id": 0.5, "pass_defense_1_player_id": 1.0, "pass_defense_2_player_id": 1.0, "interception_player_id": 1.0,
          "forced_fumble_player_1_player_id": 0.5, "forced_fumble_player_2_player_id": 0.5, "fumble_recovery_1_player_id": 0.5, "fumble_recovery_2_player_id": 0.5, "safety_player_id": 1.0}
DCOLS = ["game_id", "season", "week", "posteam", "defteam", "epa", "play_type", "field_goal_result", "kicker_player_id", "kicker_player_name", "punter_player_id", "punter_player_name", "punt_attempt", "field_goal_attempt", "extra_point_attempt"] + list(CREDIT)
OL_POS = {"T", "G", "C", "OL", "OT", "OG"}
DEF_POS = {"DE", "DT", "NT", "DL", "EDGE", "OLB", "ILB", "MLB", "LB", "CB", "NB", "S", "FS", "SS", "DB"}
GROUP = {"QB": "QB", "RB": "Skill", "FB": "Skill", "HB": "Skill", "WR": "Skill", "TE": "Skill", "K": "K", "P": "P", "LS": "Special teams"}
GROUP.update({p: "OL" for p in OL_POS}); GROUP.update({p: "Defense" for p in DEF_POS})
# defenders are valued against their own position group's replacement level: a corner is credited mostly on tackles after
# catches (negative plays), a lineman on sacks and stops (positive), so one pooled replacement level ranked every corner below
# every lineman (23 Sep 2026: DB rates averaged -0.013 per snap, DL +0.013)
DEF_SUB = {**{p: "DL" for p in ["DE", "DT", "NT", "DL", "EDGE"]}, **{p: "LB" for p in ["OLB", "ILB", "MLB", "LB"]}, **{p: "DB" for p in ["CB", "NB", "S", "FS", "SS", "DB"]}}
norm = lambda v: "".join(ch for ch in str(v).lower() if ch.isalpha())


def load(seasons) -> pd.DataFrame:
    frames = []
    for s in seasons:
        f = RAW / "pbp" / f"play_by_play_{s}.parquet"
        if f.exists():
            have = set(pq.ParquetFile(f).schema.names)
            frames.append(pd.read_parquet(f, columns=[c for c in DCOLS if c in have]))
    p = pd.concat(frames, ignore_index=True)
    for c in ["posteam", "defteam"]:
        p[c] = p[c].replace(TEAM_FIX)
    return p


def defender_credits(p: pd.DataFrame) -> pd.DataFrame:
    """Per (game, defense team, player): credited plays and the -EPA credited (capped at one credit per play)."""
    d = p[p.play_type.isin(["pass", "run"]) & p.defteam.notna()].copy()
    d["neg_epa"] = -pd.to_numeric(d.epa, errors="coerce").fillna(0.0)
    parts = []
    for col, w in CREDIT.items():
        if col not in d.columns:
            continue
        x = d[d[col].notna()][["game_id", "season", "week", "defteam", col, "neg_epa"]].rename(columns={col: "player_id"})
        x["credit"] = w
        parts.append(x)
    c = pd.concat(parts, ignore_index=True)
    c = c.groupby(["game_id", "season", "week", "defteam", "player_id"], as_index=False).agg(credit=("credit", "sum"), neg_epa=("neg_epa", "first"))
    c["credit"] = c.credit.clip(upper=1.0)
    c["epa"] = c.credit * c.neg_epa
    g = c.groupby(["game_id", "season", "week", "defteam", "player_id"], as_index=False).agg(credited=("credit", "sum"), epa=("epa", "sum"))
    return g.rename(columns={"defteam": "team"})


def snaps_by_game(seasons) -> pd.DataFrame:
    fs = [RAW / "snap_counts" / f"snap_counts_{s}.parquet" for s in seasons]
    s = pd.concat([pd.read_parquet(f) for f in fs if f.exists()], ignore_index=True)
    s["team"] = s.team.replace(TEAM_FIX); s["key"] = s.player.map(norm)
    return s[["game_id", "season", "week", "team", "key", "position", "offense_snaps", "offense_pct", "defense_snaps", "defense_pct"]]


def passer_rating(att, cmp, yds, td, ints) -> float:
    if not att:
        return float("nan")
    a = max(0.0, min(2.375, (cmp / att - 0.3) * 5)); b = max(0.0, min(2.375, (yds / att - 3) * 0.25))
    c = max(0.0, min(2.375, td / att * 20)); d = max(0.0, min(2.375, 2.375 - ints / att * 25))
    return (a + b + c + d) / 6 * 100


def coverage_stats(season: int, week: int, n_games: int = 8) -> tuple[pd.DataFrame, dict]:
    """Per defender (gsis id), coverage over his last n games before (season, week) from Pro Football Reference's
    advanced defense table (nflverse pfr_advstats, 2018 on): targets, completions allowed, yards allowed, TDs and
    interceptions, catch rate, yards per target, passer rating allowed, and yards saved per game against the league's
    yards per target that season to date. What the play-by-play cannot see: a cover player's best plays are the
    throws that never come. Returns (table indexed by gsis id, league averages)."""
    fs = [RAW / "pfr_advstats" / f"advstats_week_def_{s}.parquet" for s in (season - 1, season)]
    fs = [f for f in fs if f.exists()]
    if not fs:
        return pd.DataFrame(), {}
    d = pd.concat([pd.read_parquet(f) for f in fs], ignore_index=True)
    d = d[(d.season < season) | ((d.season == season) & (d.week < week))]
    d = d[d.def_targets.fillna(0) > 0]
    ids = {}
    for s in (season - 1, season):
        rf = RAW / "rosters" / f"roster_weekly_{s}.parquet"
        if rf.exists():
            rr = pd.read_parquet(rf, columns=["gsis_id", "pfr_id"]).dropna().drop_duplicates("pfr_id")
            ids.update(dict(zip(rr.pfr_id, rr.gsis_id)))
    d["gsis_id"] = d.pfr_player_id.map(ids); d = d.dropna(subset=["gsis_id"]).sort_values(["season", "week"])
    cur = d[d.season == season] if (d.season == season).any() else d
    league = {"ypt": float(cur.def_yards_allowed.sum() / cur.def_targets.sum()), "catch": float(cur.def_completions_allowed.sum() / cur.def_targets.sum()),
              "rating": passer_rating(float(cur.def_targets.sum()), float(cur.def_completions_allowed.sum()), float(cur.def_yards_allowed.sum()), float(cur.def_receiving_td_allowed.sum()), float(cur.def_ints.sum()))}
    rows = []
    for pid, g in d.groupby("gsis_id"):
        h = g.tail(n_games); att = float(h.def_targets.sum())
        if att <= 0:
            continue
        cmp_, yds, td, ints = float(h.def_completions_allowed.sum()), float(h.def_yards_allowed.sum()), float(h.def_receiving_td_allowed.sum()), float(h.def_ints.sum())
        rows.append({"player_id": pid, "cov_games": int(len(h)), "cov_targets": int(att), "cov_catch_pct": round(cmp_ / att, 3), "cov_ypt": round(yds / att, 2),
                     "cov_rating": round(passer_rating(att, cmp_, yds, td, ints), 1), "cov_yds_saved_pg": round((league["ypt"] * att - yds) / len(h), 2)})
    return pd.DataFrame(rows).set_index("player_id"), league


def names_by_id(seasons) -> dict:
    out = {}
    for s in seasons:
        f = RAW / "rosters" / f"roster_weekly_{s}.parquet"
        if f.exists():
            r = pd.read_parquet(f, columns=["gsis_id", "full_name", "position"]).dropna(subset=["gsis_id"]).drop_duplicates("gsis_id")
            out.update({r_.gsis_id: (r_.full_name, r_.position) for r_ in r.itertuples()})
    return out


def defender_games(p: pd.DataFrame, snaps: pd.DataFrame, names: dict) -> pd.DataFrame:
    """One row per (game, team, defender): defensive snaps (the plays) and the credited -EPA, for PlayerValues."""
    c = defender_credits(p)
    c["key"] = c.player_id.map(lambda i: norm(names.get(i, ("", ""))[0]))
    sn = snaps[snaps.defense_snaps > 0][["game_id", "team", "key", "defense_snaps"]].drop_duplicates(["game_id", "team", "key"])
    g = c.merge(sn, on=["game_id", "team", "key"], how="left")
    g = g[g.defense_snaps.notna()]
    g["plays"] = g.defense_snaps.astype(float); g["role"] = "defender"
    g["name"] = g.player_id.map(lambda i: names.get(i, ("", ""))[0])
    return g[["game_id", "season", "week", "team", "player_id", "role", "plays", "epa", "name"]]


def kicking_games(p: pd.DataFrame, names: dict) -> pd.DataFrame:
    rows = []
    k = p[(pd.to_numeric(p.field_goal_attempt, errors="coerce") == 1) | (pd.to_numeric(p.extra_point_attempt, errors="coerce") == 1)]
    k = k[k.kicker_player_id.notna()].copy(); k["epa"] = pd.to_numeric(k.epa, errors="coerce")
    g = k.groupby(["game_id", "season", "week", "posteam", "kicker_player_id"], as_index=False).agg(plays=("epa", "size"), epa=("epa", "sum"), name=("kicker_player_name", "first"))
    g = g.rename(columns={"posteam": "team", "kicker_player_id": "player_id"}); g["role"] = "kicker"; rows.append(g)
    u = p[(pd.to_numeric(p.punt_attempt, errors="coerce") == 1) & p.punter_player_id.notna()].copy(); u["epa"] = pd.to_numeric(u.epa, errors="coerce")
    g = u.groupby(["game_id", "season", "week", "posteam", "punter_player_id"], as_index=False).agg(plays=("epa", "size"), epa=("epa", "sum"), name=("punter_player_name", "first"))
    g = g.rename(columns={"posteam": "team", "punter_player_id": "player_id"}); g["role"] = "punter"; rows.append(g)
    out = pd.concat(rows, ignore_index=True)
    out["name"] = [names.get(i, (n, ""))[0] or n for i, n in zip(out.player_id, out.name)]
    return out[["game_id", "season", "week", "team", "player_id", "role", "plays", "epa", "name"]]


def ol_onoff(snaps: pd.DataFrame, tg: pd.DataFrame, names_key: dict, season: int, week: int, k_games: float = 8.0, window_games: int = 34) -> pd.DataFrame:
    """Offensive linemen as of (season, week): team offensive EPA per play with him (50%+ of snaps) minus without,
    over the team's last `window_games` games, shrunk by games-without. One row per (team, key)."""
    t = tg[(tg.season < season) | ((tg.season == season) & (tg.week < week))][["game_id", "season", "week", "team", "epa_play"]].dropna()
    t = t.sort_values(["season", "week"]).groupby("team").tail(window_games)
    ol = snaps[snaps.position.isin(OL_POS) & snaps.game_id.isin(t.game_id)]
    rows = []
    for (team, key), g in ol.groupby(["team", "key"]):
        tt = t[t.team == team]
        on = set(g[g.offense_pct >= 0.5].game_id)
        with_ = tt[tt.game_id.isin(on)].epa_play; without = tt[~tt.game_id.isin(on)].epa_play
        if len(with_) == 0:
            continue
        diff = float(with_.mean() - without.mean()) if len(without) else 0.0
        n_eff = len(with_) * len(without) / (len(with_) + len(without)) if len(without) else 0.0   # both sides must have games
        shrunk = diff * n_eff / (n_eff + k_games)
        rows.append({"team": team, "key": key, "games_on": int(len(with_)), "games_off": int(len(without)), "onoff_raw": round(diff, 4), "onoff": round(shrunk, 4),
                     "snap_pct": round(float(g.offense_pct.tail(8).mean()), 3), "position": g.position.iloc[-1]})
    return pd.DataFrame(rows)


def all_values(games: pd.DataFrame, season: int, week: int, p=DEFAULT) -> pd.DataFrame:
    """Every rostered player on every team as of (season, week), valued by his group's handle. Same columns for all:
    group, games, plays_per_game, share, epa_per_play, value_above_replacement, status."""
    seasons = range(2013, season + 1)
    pg = pd.read_parquet(OUT / "player_games.parquet")
    dg = pd.read_parquet(OUT / "defender_games.parquet"); kg = pd.read_parquet(OUT / "kicking_games.parquet")
    names = names_by_id(range(2012, season + 1))
    ros = load_rosters([season]); ros = ros[ros.week == (week if (ros.week == week).any() else ros.week.max())].dropna(subset=["gsis_id"]).drop_duplicates(["team", "gsis_id"])
    rf = RAW / "rosters" / f"roster_weekly_{season}.parquet"
    rr = pd.read_parquet(rf, columns=["week", "team", "gsis_id", "full_name", "position", "status"]); rr["team"] = rr.team.replace(TEAM_FIX)
    rr = rr[rr.week == ros.week.iloc[0]].dropna(subset=["gsis_id"]).drop_duplicates(["team", "gsis_id"])
    inj = load_injuries([season]); inj = inj[(inj.season == season) & (inj.week == week)]
    status = {(r.team, r.gsis_id): (r.report_status if isinstance(r.report_status, str) else (r.practice_status if isinstance(r.practice_status, str) else "")) for r in inj.itertuples()}
    for r in rr[rr.status.isin(NOT_AVAILABLE)].itertuples():
        status[(r.team, r.gsis_id)] = ROSTER_LABEL.get(r.status, r.status)
    # skill (players.py logic) and QB, defenders, kickers through PlayerValues on each table
    pv_skill = PlayerValues(pg, p["decay"], p["k"], p.get("pct", 25)); _, by_player, by_team = _usage_frames(pg)
    sub = {pid: DEF_SUB.get(names.get(pid, ("", ""))[1], "DB") for pid in dg.player_id.unique()}
    dg = dg.assign(role=dg.player_id.map(sub))   # the role is the position group, so the replacement level is per group
    pv_def = PlayerValues(dg, 0.99, 300.0); pv_kick = PlayerValues(kg, 0.99, 40.0)
    from .ratings import QBRatings, DEFAULT as RD
    qb = pd.read_parquet(OUT / "qb_games.parquet"); qbr = QBRatings(qb, RD["qb_k"], RD["qb_decay"], RD.get("qb_prior", -0.12), RD.get("qb_season_fade", 1.0))
    team_db = qb.groupby(["game_id", "team"]).dropbacks.sum().rename("team_db").reset_index()
    tg = pd.read_parquet(OUT / "team_games.parquet"); snaps = snaps_by_game(range(season - 2, season + 1))
    ol = ol_onoff(snaps, tg, names, season, week).set_index(["team", "key"]) if len(snaps) else pd.DataFrame()
    def_by = {pid: g for pid, g in dg.groupby("player_id")}; kick_by = {pid: g for pid, g in kg.groupby("player_id")}
    cov, cov_league = coverage_stats(season, week)
    def last8(g):
        h = g[(g.season < season) | ((g.season == season) & (g.week < week))]
        ids = h.game_id.drop_duplicates().tail(p["usage_games"]); return h[h.game_id.isin(ids)]
    rows = []
    for r in rr.itertuples():
        pos = r.position; grp = GROUP.get(pos, "Other"); st = status.get((r.team, r.gsis_id), "")
        row = {"team": r.team, "player_id": r.gsis_id, "name": r.full_name, "position": pos, "group": grp, "roster": ROSTER_LABEL.get(r.status, {"ACT": "Active", "DEV": "Practice squad", "INA": "Inactive", "CUT": "Cut"}.get(r.status, r.status)),
               "games": 0, "plays_per_game": None, "share": None, "epa_per_play": None, "value_above_replacement": None, "status": st, "basis": ""}
        if grp == "QB":
            h = qb[(qb.qb_id == r.gsis_id) & ((qb.season < season) | ((qb.season == season) & (qb.week < week)))]
            if len(h):
                rating = qbr.rating(r.gsis_id, season, week)
                # dropbacks a game over his last eight starts: games where he had at least half his team's dropbacks,
                # so a first-drive exit or a one-play relief appearance is not averaged in as a game (24 Sep 2026)
                st = h.merge(team_db, on=["game_id", "team"], how="left"); st = st[st.dropbacks >= 0.5 * st.team_db]
                rec = st.tail(8) if len(st) else h.tail(8)
                row.update({"games": int(len(rec)), "plays_per_game": round(float(rec.dropbacks.mean()), 1), "share": None, "epa_per_play": round(rating, 3), "value_above_replacement": round(rating - qbr.prior, 4), "basis": "EPA per dropback (QB rating)"})
        elif grp == "Skill":
            from .players import player_value_out
            d = player_value_out(pv_skill, by_player, r.gsis_id, season, week, p["usage_games"], r.team, by_team)
            if d["games"]:
                row.update({"games": d["games"], "plays_per_game": round(d["per_game"], 1), "share": round(d["share"], 3), "epa_per_play": round(d["epa_play"], 3), "value_above_replacement": round(d["value"], 4), "basis": "EPA per touch x touch share"})
        elif grp == "Defense":
            g = def_by.get(r.gsis_id)
            if g is not None:
                rec = last8(g)
                if len(rec):
                    role = DEF_SUB.get(pos, "DB"); v, n = pv_def.value(r.gsis_id, role, season, week); pr = pv_def.prior(role, season)
                    snap_share = float(rec.plays.mean())
                    # the unit's snaps in each game he played, for the team he played it for: a player who changed teams
                    # was divided by his new team's snaps in games it did not play (share 0; 24 Sep 2026)
                    tsn = snaps.merge(rec[["game_id", "team"]].drop_duplicates(), on=["game_id", "team"]).groupby("game_id").defense_snaps.max().mean()
                    share = float(snap_share / tsn) if tsn and not np.isnan(tsn) else 0.0
                    row.update({"games": int(len(rec)), "plays_per_game": round(snap_share, 1), "share": round(min(share, 1.0), 3), "epa_per_play": round(v, 4), "value_above_replacement": round((v - pr) * min(share, 1.0), 4), "basis": f"Impact -EPA per defensive snap x snap share, against {role} replacement"})
            if len(cov) and r.gsis_id in cov.index:
                row.update({k: (int(v) if k in ("cov_games", "cov_targets") else float(v)) for k, v in cov.loc[r.gsis_id].items()})
                row["cov_league_ypt"] = round(cov_league["ypt"], 2); row["cov_league_rating"] = round(cov_league["rating"], 1)
        elif grp == "OL":
            key = (r.team, norm(r.full_name))
            if len(ol) and key in ol.index:
                o = ol.loc[key]
                row.update({"games": int(o.games_on), "plays_per_game": None, "share": float(o.snap_pct), "epa_per_play": float(o.onoff_raw), "value_above_replacement": round(float(o.onoff) * float(o.snap_pct), 4), "basis": f"On/off: team EPA per play with him minus without ({int(o.games_off)} games without)"})
        elif grp in ("K", "P"):
            g = kick_by.get(r.gsis_id)
            if g is not None:
                role = "kicker" if grp == "K" else "punter"; rec = last8(g[g.role == role])
                if len(rec):
                    v, n = pv_kick.value(r.gsis_id, role, season, week); pr = pv_kick.prior(role, season)
                    row.update({"games": int(len(rec)), "plays_per_game": round(float(rec.plays.mean()), 1), "share": 1.0, "epa_per_play": round(v, 4), "value_above_replacement": round(v - pr, 4), "basis": "EPA per kick" if grp == "K" else "EPA per punt"})
        rows.append(row)
    out = pd.DataFrame(rows)
    # value against an average starter (24 Sep 2026, Matt): the zero point of every value on the page is the median
    # starter at his position group, the same for every team. Starters: each team's QB with the most dropbacks over its
    # last 17 games; its top 5 skill players by share of the team's touches, top 5 linemen and top 11 defenders by snap
    # share, and its kicker and punter. value_vs_avg = value_above_replacement - that median (same units); the order
    # within a group is unchanged. "Points if out" keeps the replacement level: it is what a team loses to his backup.
    TOP = {"Skill": 5, "OL": 5, "Defense": 11, "K": 1, "P": 1}
    h17 = qb[(qb.season < season) | ((qb.season == season) & (qb.week < week))]
    last17 = h17.merge(h17.groupby("team").game_id.apply(lambda s_: set(s_.drop_duplicates().tail(17))).rename("keep"), left_on="team", right_index=True)
    last17 = last17[[g_ in k_ for g_, k_ in zip(last17.game_id, last17.keep)]]
    starters_qb = set(last17.groupby(["team", "qb_id"]).dropbacks.sum().reset_index().sort_values("dropbacks", ascending=False).drop_duplicates("team").qb_id)
    ref = {}
    q_ = out[(out.group == "QB") & out.player_id.isin(starters_qb) & out.value_above_replacement.notna()]
    if len(q_): ref["QB"] = float(q_.value_above_replacement.median())
    for grp_, k_ in TOP.items():
        x_ = out[(out.group == grp_) & out.value_above_replacement.notna()].copy()
        if not len(x_): continue
        key_ = x_.share.fillna(x_.plays_per_game).fillna(0) if grp_ in ("Skill", "OL", "Defense") else x_.plays_per_game.fillna(0)
        x_ = x_.assign(_k=key_).sort_values("_k", ascending=False).groupby("team").head(k_)
        ref[grp_] = float(x_.value_above_replacement.median())
    out["avg_starter_ref"] = out.group.map(ref)
    out["value_vs_avg"] = (out.value_above_replacement - out.avg_starter_ref).round(4)
    return out.sort_values(["team", "group", "value_above_replacement"], ascending=[True, True, False], na_position="last")


def build(seasons=range(2013, 2027)):
    p = load(seasons); names = names_by_id(range(2012, max(seasons) + 1)); snaps = snaps_by_game(seasons)
    dg = defender_games(p, snaps, names); dg.to_parquet(OUT / "defender_games.parquet", index=False)
    kg = kicking_games(p, names); kg.to_parquet(OUT / "kicking_games.parquet", index=False)
    print("defender_games", dg.shape, "kicking_games", kg.shape, flush=True)


if __name__ == "__main__":
    import sys
    games = pd.read_parquet(OUT / "games.parquet")
    if "--values-only" not in sys.argv:
        build()
    from .lines import current_week
    cs, cw = current_week(games)
    av = all_values(games, cs, cw)
    av.to_parquet(OUT / "player_values_all.parquet", index=False)
    print("player_values_all", av.shape, av.group.value_counts().to_dict())
    from .players import team_roster
    ro = team_roster(games, cs, cw); ro.to_parquet(OUT / "roster_now.parquet", index=False); print("roster_now", ro.shape)
    print(av[av.value_above_replacement.notna()].groupby("group").value_above_replacement.describe()[["count", "mean", "50%", "max"]].to_string())
