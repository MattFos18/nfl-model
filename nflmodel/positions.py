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
DCOLS = ["game_id", "play_id", "season", "week", "posteam", "defteam", "epa", "play_type", "field_goal_result", "kicker_player_id", "kicker_player_name", "punter_player_id", "punter_player_name", "punt_attempt", "field_goal_attempt", "extra_point_attempt"] + list(CREDIT)
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
    """Per (game, defense team, player): credited plays, the -EPA credited (at most one credit per play), and two
    parts of it the defender value uses: run stops (-EPA of runs he is credited on that lost the offense EPA) and
    forced fumbles (-EPA of plays where he forced one). Until 24 Sep 2026 the credits were summed per game, not per
    play, so a defender's game counted once, at his first credited play's EPA."""
    d = p[p.play_type.isin(["pass", "run"]) & p.defteam.notna()].copy()
    d["neg_epa"] = -pd.to_numeric(d.epa, errors="coerce").fillna(0.0)
    parts = []
    for col, w in CREDIT.items():
        if col not in d.columns:
            continue
        x = d[d[col].notna()][["game_id", "play_id", "season", "week", "defteam", "play_type", col, "neg_epa"]].rename(columns={col: "player_id"})
        x["credit"] = w; x["ff"] = 1.0 if col.startswith("forced_fumble") else 0.0
        parts.append(x)
    c = pd.concat(parts, ignore_index=True)
    c = c.groupby(["game_id", "play_id", "season", "week", "defteam", "player_id"], as_index=False).agg(credit=("credit", "sum"), neg_epa=("neg_epa", "first"), play_type=("play_type", "first"), ff=("ff", "max"))
    c["credit"] = c.credit.clip(upper=1.0)
    c["epa"] = c.credit * c.neg_epa
    c["run_stop"] = np.where((c.play_type == "run") & (c.neg_epa > 0), c.epa, 0.0)
    c["ff_epa"] = np.where(c.ff > 0, c.neg_epa.clip(lower=0), 0.0)
    g = c.groupby(["game_id", "season", "week", "defteam", "player_id"], as_index=False).agg(credited=("credit", "sum"), epa=("epa", "sum"), run_stop=("run_stop", "sum"), ff_epa=("ff_epa", "sum"))
    return g.rename(columns={"defteam": "team"})


def snaps_by_game(seasons) -> pd.DataFrame:
    fs = [RAW / "snap_counts" / f"snap_counts_{s}.parquet" for s in seasons]
    s = pd.concat([pd.read_parquet(f) for f in fs if f.exists()], ignore_index=True)
    s["team"] = s.team.replace(TEAM_FIX); s["key"] = s.player.map(norm)
    return s[["game_id", "season", "week", "team", "key", "player", "pfr_player_id", "position", "offense_snaps", "offense_pct", "defense_snaps", "defense_pct"]]


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


# Defender value (24 Sep 2026): what each defender's plays were worth to the team's defensive EPA, per snap. Weights
# measured on 2016-18 plays (both test windows untouched; experiments/def_value.py):
#   coverage   0.095 EPA per yard saved against the league's yards per target (EPA per yard on completions)
#   picks      3.6 EPA per interception on top of the yards (an interception against an incompletion)
#   sacks      2.05 EPA per sack (a sack's EPA against a clean dropback's)
#   pressures  0.39 EPA per pressure that was not a sack (pressured dropbacks without a sack against a clean one, per
#              PFR non-sack pressure; a single 0.84 for every pressure had counted a sack the same as a hurry)
#   run stops  the -EPA of runs he is credited on that lost the offense EPA; forced fumbles the play's -EPA
# Coverage and pressures come from PFR's weekly advanced defense table (2018 on). A tackle after a catch or a long
# run no longer counts against him: allowing the catch is in the coverage numbers of the man who allowed it.
DEF_W = {"cov_yds": 0.095, "cov_int": 3.6, "sacks": 2.05, "press_ns": 0.39}
# how fast old games fade (experiments/def_value_decay.py): 0.92 a game and 0.8 a season back, K 300 snaps, best on
# 2019-22 and better held out than the old 0.99 a game with no fade (a game two seasons back had kept ~70% weight)
DEF_DECAY, DEF_FADE, DEF_K = 0.92, 0.8, 300.0


DEF_ROLE = {"DE": "EDGE", "EDGE": "EDGE", "DT": "IDL", "NT": "IDL", "DL": "IDL", "ILB": "LB", "MLB": "LB", "LB": "LB", "OLB": "LB",
            "CB": "CB", "NB": "CB", "DB": "CB", "FS": "S", "SS": "S", "S": "S"}
EDGE_PRESS = 0.015  # a linebacker who pressures on 1.5%+ of his snaps (2018 on) is an edge rusher (off-ball ILBs: 90th percentile 1.2%; OLB edges 1.7% and up)


def defender_roles(dg: pd.DataFrame) -> dict:
    """Each defender's group for his replacement level: his latest roster depth-chart position (DE, DT, NT, OLB, ILB,
    MLB, CB, FS, SS; the roster's generic DL / LB / DB mixes edge rushers with nose tackles and off-ball linebackers),
    else his usual snap-count position; any linebacker who pressures on 1.5%+ of his snaps (2018 on) is an edge rusher."""
    dc = {}
    for f in sorted((RAW / "rosters").glob("roster_weekly_*.parquet")):
        rr = pd.read_parquet(f, columns=["gsis_id", "depth_chart_position", "week"]).dropna().sort_values("week")
        dc.update(dict(zip(rr.gsis_id, rr.depth_chart_position)))
    h = dg.sort_values(["season", "week"]).groupby("player_id").tail(17)
    snap_pos = h.groupby("player_id").position.agg(lambda x: x.mode().iloc[0] if len(x.mode()) else "")
    r = dg[dg.season >= 2018].groupby("player_id").agg(press=("press", "sum"), plays=("plays", "sum"))
    rate = (r.press / r.plays.where(r.plays > 0)).reindex(snap_pos.index).fillna(0.0)
    out = {}
    for pid, sp in snap_pos.items():
        role = DEF_ROLE.get(dc.get(pid, ""), DEF_ROLE.get(sp, "CB"))
        out[pid] = "EDGE" if role == "LB" and rate[pid] >= EDGE_PRESS else role
    return out


def pfr_ids() -> dict:
    ids = {}
    for f in sorted((RAW / "rosters").glob("roster_weekly_*.parquet")):
        rr = pd.read_parquet(f, columns=["gsis_id", "pfr_id"]).dropna().drop_duplicates("pfr_id"); ids.update(dict(zip(rr.pfr_id, rr.gsis_id)))
    return ids


def pfr_def_games() -> pd.DataFrame:
    """Per (game_id, pfr id): coverage yards saved, interceptions, pressures, targets, missed tackles (PFR, 2018 on)."""
    fs = sorted((RAW / "pfr_advstats").glob("advstats_week_def_*.parquet"))
    if not fs:
        return pd.DataFrame(columns=["game_id", "pfr_player_id", "cov_yds", "cov_int", "press", "sacks", "press_ns", "targets"])
    a = pd.concat([pd.read_parquet(f) for f in fs], ignore_index=True)
    tg = a[a.def_targets.fillna(0) > 0]
    lg = (tg.groupby("season").def_yards_allowed.sum() / tg.groupby("season").def_targets.sum()).rename("lg_ypt")
    a = a.merge(lg, on="season", how="left")
    a["cov_yds"] = a.lg_ypt * a.def_targets.fillna(0) - a.def_yards_allowed.fillna(0)
    a["cov_int"] = a.def_ints.fillna(0); a["press"] = a.def_pressures.fillna(0); a["targets"] = a.def_targets.fillna(0)
    a["sacks"] = a.def_sacks.fillna(0); a["press_ns"] = (a.press - a.sacks).clip(lower=0)
    return a.groupby(["game_id", "pfr_player_id"], as_index=False)[["cov_yds", "cov_int", "press", "sacks", "press_ns", "targets"]].sum()


def with_ids(sn: pd.DataFrame, names: dict) -> pd.DataFrame:
    """Snap-count rows with the gsis id: by PFR id through the rosters, else the name (one row per game and player)."""
    sn = sn.copy(); sn["player_id"] = sn.pfr_player_id.map(pfr_ids())
    miss = sn.player_id.isna()
    if miss.any():
        by_name = {}
        for pid, (nm, _) in names.items():
            by_name.setdefault(norm(nm), pid)
        sn.loc[miss, "player_id"] = sn.loc[miss, "key"].map(by_name)
    return sn.dropna(subset=["player_id"]).drop_duplicates(["game_id", "player_id"])


# Offensive line (24 Sep 2026): no public data says which lineman allowed a pressure, so a lineman is rated by his
# unit in the snaps he played: pressures allowed per dropback against the league (PFR, 0.84 EPA a pressure, as for
# the pass rushers) and rushing yards before contact per carry against the league (PFR, 0.135 EPA a yard, the EPA of
# a rushing yard on 2016-18 runs). It replaced the on/off split (team EPA with him minus without), which put every
# lineman who never missed a game at exactly zero and swung on a handful of games.
OL_W = {"press": 0.84, "ybc": 0.135}


def ol_unit_games(snaps: pd.DataFrame, names: dict) -> pd.DataFrame:
    """One row per (game, team, lineman): his offensive snaps (plays) and the unit's EPA saved per snap times them."""
    fp = sorted((RAW / "pfr_pass").glob("advstats_week_pass_*.parquet")); fr = sorted((RAW / "pfr_rush").glob("advstats_week_rush_*.parquet"))
    if not fp or not fr:
        return pd.DataFrame(columns=["game_id", "season", "week", "team", "player_id", "role", "plays", "epa", "name"])
    a = pd.concat([pd.read_parquet(f, columns=["game_id", "season", "team", "times_pressured"]) for f in fp]); a["team"] = a.team.replace(TEAM_FIX)
    u = pd.concat([pd.read_parquet(f, columns=["game_id", "season", "team", "carries", "rushing_yards_before_contact"]) for f in fr]); u["team"] = u.team.replace(TEAM_FIX)
    a = a.groupby(["game_id", "season", "team"], as_index=False).times_pressured.sum()
    u = u.groupby(["game_id", "season", "team"], as_index=False)[["carries", "rushing_yards_before_contact"]].sum()
    tg = pd.read_parquet(OUT / "team_games.parquet", columns=["game_id", "team", "pass_plays"])
    t = a.merge(u, on=["game_id", "season", "team"], how="outer").merge(tg, on=["game_id", "team"], how="left").fillna(0.0)
    lg = t.groupby("season").agg(pr=("times_pressured", "sum"), db=("pass_plays", "sum"), ybc=("rushing_yards_before_contact", "sum"), car=("carries", "sum"))
    t = t.merge((lg.pr / lg.db).rename("lg_press"), on="season").merge((lg.ybc / lg.car).rename("lg_ybc"), on="season")
    t["saved"] = OL_W["press"] * (t.lg_press * t.pass_plays - t.times_pressured) + OL_W["ybc"] * (t.rushing_yards_before_contact - t.lg_ybc * t.carries)
    sn = with_ids(snaps[snaps.position.isin(OL_POS) & (snaps.offense_snaps > 0)], names)
    team_off = snaps.groupby(["game_id", "team"]).offense_snaps.max().rename("team_off").reset_index()
    g = sn.merge(t[["game_id", "team", "saved"]], on=["game_id", "team"], how="inner").merge(team_off, on=["game_id", "team"])
    g["plays"] = g.offense_snaps.astype(float); g["epa"] = g.saved / g.team_off * g.plays; g["role"] = "OL"
    g["name"] = [names.get(i, (n, ""))[0] or n for i, n in zip(g.player_id, g.player)]
    return g[["game_id", "season", "week", "team", "player_id", "role", "plays", "epa", "name"]]


def defender_games(p: pd.DataFrame, snaps: pd.DataFrame, names: dict) -> pd.DataFrame:
    """One row per (game, team, defender) who played a defensive snap, from the snap counts matched by PFR id (names
    differ: Patrick Surtain II in the snap counts is Pat Surtain II on the roster): snaps (the plays), the value
    components and their sum (epa, the team defensive EPA his game saved), for PlayerValues."""
    sn = with_ids(snaps[snaps.defense_snaps > 0], names)
    c = defender_credits(p)
    g = sn.merge(c.drop(columns=["season", "week", "team"]).rename(columns={"epa": "credit_epa"}), on=["game_id", "player_id"], how="left")
    g = g.merge(pfr_def_games(), on=["game_id", "pfr_player_id"], how="left")
    for col in ["credited", "credit_epa", "run_stop", "ff_epa", "cov_yds", "cov_int", "press", "sacks", "press_ns", "targets"]:
        g[col] = g[col].fillna(0.0)
    g["epa"] = g.run_stop + g.ff_epa + sum(w * g[k] for k, w in DEF_W.items())
    g["plays"] = g.defense_snaps.astype(float); g["role"] = "defender"
    g["name"] = [names.get(i, (n, ""))[0] or n for i, n in zip(g.player_id, g.player)]
    return g[["game_id", "season", "week", "team", "player_id", "role", "plays", "epa", "name", "position", "credited", "credit_epa", "run_stop", "ff_epa", "cov_yds", "cov_int", "press", "sacks", "press_ns", "targets"]]


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
    roles = defender_roles(dg)
    dg = dg.assign(role=dg.player_id.map(roles))   # the role is the position group, so the replacement level is per group
    pv_def = PlayerValues(dg, DEF_DECAY, DEF_K, season_fade=DEF_FADE); pv_kick = PlayerValues(kg, 0.99, 40.0)
    from .ratings import QBRatings, DEFAULT as RD
    qb = pd.read_parquet(OUT / "qb_games.parquet"); qbr = QBRatings(qb, RD["qb_k"], RD["qb_decay"], RD.get("qb_prior", -0.12), RD.get("qb_season_fade", 1.0))
    team_db = qb.groupby(["game_id", "team"]).dropbacks.sum().rename("team_db").reset_index()
    tg = pd.read_parquet(OUT / "team_games.parquet"); snaps = snaps_by_game(range(season - 2, season + 1))
    og = pd.read_parquet(OUT / "ol_games.parquet") if (OUT / "ol_games.parquet").exists() else pd.DataFrame(columns=["player_id"])
    pv_ol = PlayerValues(og, DEF_DECAY, 300.0, season_fade=DEF_FADE); ol_by = {pid: g for pid, g in og.groupby("player_id")}   # current form, as for defenders
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
                    role = roles.get(r.gsis_id, DEF_ROLE.get(pos, "CB")); v, n = pv_def.value(r.gsis_id, role, season, week); pr = pv_def.prior(role, season)
                    snap_share = float(rec.plays.mean())
                    # the unit's snaps in each game he played, for the team he played it for: a player who changed teams
                    # was divided by his new team's snaps in games it did not play (share 0; 24 Sep 2026)
                    tsn = snaps.merge(rec[["game_id", "team"]].drop_duplicates(), on=["game_id", "team"]).groupby("game_id").defense_snaps.max().mean()
                    share = float(snap_share / tsn) if tsn and not np.isnan(tsn) else 0.0
                    row.update({"games": int(len(rec)), "plays_per_game": round(snap_share, 1), "share": round(min(share, 1.0), 3), "epa_per_play": round(v, 4), "value_above_replacement": round((v - pr) * min(share, 1.0), 4), "basis": f"Defensive EPA saved per snap (coverage, pressures, interceptions, run stops) x snap share, against {role} replacement", "def_role": role})
            if len(cov) and r.gsis_id in cov.index:
                row.update({k: (int(v) if k in ("cov_games", "cov_targets") else float(v)) for k, v in cov.loc[r.gsis_id].items()})
                row["cov_league_ypt"] = round(cov_league["ypt"], 2); row["cov_league_rating"] = round(cov_league["rating"], 1)
        elif grp == "OL":
            g = ol_by.get(r.gsis_id)
            if g is not None:
                rec = last8(g)
                if len(rec):
                    v, n = pv_ol.value(r.gsis_id, "OL", season, week); pr = pv_ol.prior("OL", season)
                    tsn = snaps.merge(rec[["game_id", "team"]].drop_duplicates(), on=["game_id", "team"]).groupby("game_id").offense_snaps.max().mean()
                    share = float(rec.plays.mean() / tsn) if tsn and not np.isnan(tsn) else 0.0
                    row.update({"games": int(len(rec)), "plays_per_game": round(float(rec.plays.mean()), 1), "share": round(min(share, 1.0), 3), "epa_per_play": round(v, 4),
                                "value_above_replacement": round((v - pr) * min(share, 1.0), 4), "basis": "Line unit in his snaps: pressures allowed and yards before contact against the league, per snap x snap share"})
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
    # defenders against the average starter of their own group (24 Sep 2026): an edge rusher's value runs on a larger
    # scale than a safety's, so one median across all eleven set every edge above average; per team 2 EDGE, 2 IDL,
    # 2 LB, 3 CB, 2 S by snap share
    DTOP = {"EDGE": 2, "IDL": 2, "LB": 2, "CB": 3, "S": 2}; dref = {}
    if "def_role" in out.columns:
        for role_, k_ in DTOP.items():
            x_ = out[(out.group == "Defense") & (out.def_role == role_) & out.value_above_replacement.notna()]
            if len(x_):
                dref[role_] = float(x_.assign(_k=x_.share.fillna(0)).sort_values("_k", ascending=False).groupby("team").head(k_).value_above_replacement.median())
    out["avg_starter_ref"] = [dref.get(r_, ref.get(g_)) if g_ == "Defense" else ref.get(g_) for g_, r_ in zip(out.group, out.get("def_role", pd.Series([None] * len(out), index=out.index)))]
    out["value_vs_avg"] = (out.value_above_replacement - out.avg_starter_ref).round(4)
    return out.sort_values(["team", "group", "value_above_replacement"], ascending=[True, True, False], na_position="last")


def build(seasons=range(2013, 2027)):
    p = load(seasons); names = names_by_id(range(2012, max(seasons) + 1)); snaps = snaps_by_game(seasons)
    dg = defender_games(p, snaps, names); dg.to_parquet(OUT / "defender_games.parquet", index=False)
    kg = kicking_games(p, names); kg.to_parquet(OUT / "kicking_games.parquet", index=False)
    og = ol_unit_games(snaps, names); og.to_parquet(OUT / "ol_games.parquet", index=False)
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
