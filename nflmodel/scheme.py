"""Scheme and play-calling profiles (23 Sep 2026). Every play since 2016 joined with what the participation data
and FTN charting say about it: the offense's formation, personnel, motion, play action, RPO, screens, tempo; the
defense's man or zone call, coverage family, box count, rushers, blitz, pressure. Per team and season, offense and
defense: how they play (rates) and how it has gone (EPA per play in each look), as-of a week so nothing leaks.
Readings for the page (Team -> Overview, the card's matchup section); not model inputs until tested on both windows.

Sources: data/raw/pbp (EPA, down, distance, win probability), data/raw/participation (nflverse pbp_participation:
offense_formation, offense_personnel, defenders_in_box, defense_personnel, number_of_pass_rushers, was_pressure,
defense_man_zone_type, defense_coverage_type, time_to_throw), data/raw/ftn (FTN charting, 2022 on: is_motion,
is_play_action, is_rpo, is_screen_pass, is_no_huddle, n_blitzers, n_pass_rushers, qb_location, n_defense_box).
Usage: python -m nflmodel.scheme            builds data/processed/scheme_plays.parquet and scheme_profiles.parquet"""
from __future__ import annotations
import re
import numpy as np, pandas as pd
import pyarrow.parquet as pq
from .features import RAW, OUT, TEAM_FIX

PBP = ["game_id", "play_id", "season", "week", "posteam", "defteam", "play_type", "pass", "rush", "qb_dropback", "epa", "success", "down", "ydstogo", "passer_player_id", "receiver_player_id", "rusher_player_id", "yards_gained", "pass_touchdown", "rush_touchdown", "interception", "fumble_lost",
       "yardline_100", "wp", "shotgun", "no_huddle", "sack", "qb_hit", "complete_pass", "air_yards", "xpass", "half_seconds_remaining", "game_seconds_remaining", "score_differential"]
PART = ["nflverse_game_id", "play_id", "offense_formation", "offense_personnel", "defenders_in_box", "defense_personnel", "number_of_pass_rushers", "was_pressure",
        "defense_man_zone_type", "defense_coverage_type", "time_to_throw"]
FTN = ["nflverse_game_id", "nflverse_play_id", "is_motion", "is_play_action", "is_rpo", "is_screen_pass", "is_no_huddle", "n_blitzers", "n_pass_rushers", "qb_location",
       "n_defense_box", "is_qb_out_of_pocket", "is_drop", "is_contested_ball", "is_catchable_ball", "is_interception_worthy", "is_qb_fault_sack", "is_trick_play"]


def _count(personnel: str, pos: tuple) -> int:
    n = 0
    for m in re.finditer(r"(\d+) ([A-Z]+)", str(personnel)):
        if m.group(2) in pos:
            n += int(m.group(1))
    return n


def load_plays(seasons) -> pd.DataFrame:
    frames = []
    for s in seasons:
        f = RAW / "pbp" / f"play_by_play_{s}.parquet"
        if not f.exists():
            continue
        have = set(pq.ParquetFile(f).schema.names)
        p = pd.read_parquet(f, columns=[c for c in PBP if c in have])
        p = p[p.play_type.isin(["pass", "run"]) & p.posteam.notna()].copy()
        pf = RAW / "participation" / f"pbp_participation_{s}.parquet"
        if pf.exists():
            q = pd.read_parquet(pf, columns=[c for c in PART if c in set(pq.ParquetFile(pf).schema.names)]).rename(columns={"nflverse_game_id": "game_id"})
            q = q.drop_duplicates(["game_id", "play_id"])
            p = p.merge(q, on=["game_id", "play_id"], how="left")
        ff = RAW / "ftn" / f"ftn_charting_{s}.parquet"
        if ff.exists():
            t = pd.read_parquet(ff, columns=[c for c in FTN if c in set(pq.ParquetFile(ff).schema.names)]).rename(columns={"nflverse_game_id": "game_id", "nflverse_play_id": "play_id"})
            t = t.drop_duplicates(["game_id", "play_id"])
            p = p.merge(t, on=["game_id", "play_id"], how="left")
        frames.append(p)
    d = pd.concat(frames, ignore_index=True)
    for c in ["posteam", "defteam"]:
        d[c] = d[c].replace(TEAM_FIX)
    for c in PART[2:] + FTN[2:]:
        if c not in d.columns:
            d[c] = np.nan
    # derived looks
    d["dropback"] = d.qb_dropback.fillna(0).astype(float) == 1
    d["pass_play"] = d["pass"].fillna(0).astype(float) == 1
    mz = d.defense_man_zone_type.fillna("").astype(str)
    d["man"] = mz.eq("MAN_COVERAGE"); d["zone"] = mz.eq("ZONE_COVERAGE"); d["cov_known"] = d.man | d.zone
    d["coverage"] = d.defense_coverage_type.fillna("").astype(str).replace({"": None})
    d["rb"] = d.offense_personnel.map(lambda v: _count(v, ("RB", "FB", "HB")) if isinstance(v, str) else np.nan)
    d["te"] = d.offense_personnel.map(lambda v: _count(v, ("TE",)) if isinstance(v, str) else np.nan)
    d["wr"] = d.offense_personnel.map(lambda v: _count(v, ("WR",)) if isinstance(v, str) else np.nan)
    d["personnel"] = np.where(d.rb.notna() & d.te.notna(), d.rb.fillna(0).astype(int).astype(str) + d.te.fillna(0).astype(int).astype(str), None)
    d["dbs"] = d.defense_personnel.map(lambda v: _count(v, ("CB", "FS", "SS", "S", "DB")) if isinstance(v, str) else np.nan)
    d["box"] = d.defenders_in_box.astype(float)
    d["box"] = d.box.fillna(d.n_defense_box.astype(float) if "n_defense_box" in d else np.nan)
    d["rushers"] = d.number_of_pass_rushers.astype(float)
    d["rushers"] = d.rushers.fillna(d.n_pass_rushers.astype(float) if "n_pass_rushers" in d else np.nan)
    d["blitz"] = np.where(d.rushers.notna(), d.rushers >= 5, np.where(d.n_blitzers.notna(), d.n_blitzers.astype(float) > 0, np.nan)).astype(float)
    d["pressure"] = d.was_pressure.astype(float)
    d["formation"] = d.offense_formation.fillna("").astype(str)
    d["shotgun_f"] = np.where(d.formation != "", d.formation.isin(["SHOTGUN", "PISTOL"]), d.shotgun.fillna(0).astype(float) == 1)
    d["neutral"] = d.wp.between(0.2, 0.8) & (d.down <= 2)
    for c in ["is_motion", "is_play_action", "is_rpo", "is_screen_pass", "is_no_huddle", "is_qb_out_of_pocket", "is_drop", "is_contested_ball", "is_catchable_ball", "is_interception_worthy", "is_qb_fault_sack"]:
        d[c] = d[c].astype(float) if c in d.columns else np.nan
    return d


def _rate(mask: pd.Series, base: pd.Series) -> float | None:
    n = int(base.sum())
    return round(float(mask[base].mean()), 3) if n else None


def _epa(d: pd.DataFrame, mask: pd.Series, min_n: int = 20) -> dict:
    x = d[mask]
    return {"n": int(len(x)), "epa": (round(float(x.epa.mean()), 3) if len(x) >= min_n else None), "success": (round(float(x.success.mean()), 3) if len(x) >= min_n else None)}


def profile(d: pd.DataFrame, team: str, side: str) -> dict:
    """One team's profile from the plays in d (already limited to the games wanted): rates of each look and EPA per
    play in it. side = "offense" (d.posteam == team) or "defense" (d.defteam == team; EPA is what it allowed)."""
    x = d[(d.posteam if side == "offense" else d.defteam) == team]
    if not len(x):
        return {"plays": 0}
    db = x.dropback; ps = x.pass_play; run = x.play_type.eq("run"); nb = x.neutral
    out = {"plays": int(len(x)), "games": int(x.game_id.nunique()), "epa": round(float(x.epa.mean()), 3), "success": round(float(x.success.mean()), 3),
           "pass_rate": _rate(ps, x.play_type.notna()), "pass_rate_neutral": _rate(ps, nb), "pass_oe": (round(float((ps.astype(float) - x.xpass)[nb & x.xpass.notna()].mean()), 3) if (nb & x.xpass.notna()).any() else None),
           "epa_pass": _epa(x, ps)["epa"], "epa_run": _epa(x, run)["epa"], "success_pass": _epa(x, ps)["success"], "success_run": _epa(x, run)["success"]}
    if side == "offense":
        out.update({"shotgun": _rate(x.shotgun_f, x.play_type.notna()), "motion": _rate(x.is_motion == 1, x.is_motion.notna()), "play_action": _rate(x.is_play_action == 1, db & x.is_play_action.notna()),
                    "rpo": _rate(x.is_rpo == 1, x.is_rpo.notna()), "screen": _rate(x.is_screen_pass == 1, db & x.is_screen_pass.notna()), "no_huddle": _rate(x.is_no_huddle == 1, x.is_no_huddle.notna()),
                    "personnel": {k: round(float(v), 3) for k, v in x.personnel.value_counts(normalize=True).head(5).items()} if x.personnel.notna().any() else {},
                    "time_to_throw": (round(float(x.time_to_throw[db].mean()), 2) if x.time_to_throw[db].notna().any() else None),
                    "vs": {"man": _epa(x, ps & x.man), "zone": _epa(x, ps & x.zone), "blitz": _epa(x, db & (x.blitz == 1)), "no_blitz": _epa(x, db & (x.blitz == 0)), "pressure": _epa(x, db & (x.pressure == 1)), "clean": _epa(x, db & (x.pressure == 0)),
                           "play_action": _epa(x, db & (x.is_play_action == 1)), "no_play_action": _epa(x, db & (x.is_play_action == 0)), "motion": _epa(x, x.is_motion == 1), "no_motion": _epa(x, x.is_motion == 0),
                           "light_box": _epa(x, run & (x.box <= 6)), "heavy_box": _epa(x, run & (x.box >= 8)),
                           **{f"cov_{c}": _epa(x, ps & (x.coverage == c)) for c in ["COVER_1", "COVER_2", "COVER_3", "COVER_4", "2_MAN", "COMBO"]}}})
        cv = x[ps & x.cov_known]
        out["faced_man"] = round(float(cv.man.mean()), 3) if len(cv) else None
    else:
        cv = x[ps & x.cov_known]
        out.update({"man": (round(float(cv.man.mean()), 3) if len(cv) else None), "zone": (round(float(cv.zone.mean()), 3) if len(cv) else None),
                    "coverage": {k: round(float(v), 3) for k, v in x.coverage.dropna().value_counts(normalize=True).items()} if x.coverage.notna().any() else {},
                    "blitz": _rate(x.blitz == 1, db & x.blitz.notna()), "pressure": _rate(x.pressure == 1, db & x.pressure.notna()), "rushers": (round(float(x.rushers[db].mean()), 2) if x.rushers[db].notna().any() else None),
                    "box_run": (round(float(x.box[run].mean()), 2) if x.box[run].notna().any() else None), "heavy_box_rate": _rate(x.box >= 8, run & x.box.notna()),
                    "nickel_plus": _rate(x.dbs >= 5, x.dbs.notna()), "dime_plus": _rate(x.dbs >= 6, x.dbs.notna()),
                    "vs": {"man": _epa(x, ps & x.man), "zone": _epa(x, ps & x.zone), "blitz": _epa(x, db & (x.blitz == 1)), "no_blitz": _epa(x, db & (x.blitz == 0)), "pressure": _epa(x, db & (x.pressure == 1)), "clean": _epa(x, db & (x.pressure == 0)),
                           "play_action": _epa(x, db & (x.is_play_action == 1)), "no_play_action": _epa(x, db & (x.is_play_action == 0)), "light_box": _epa(x, run & (x.box <= 6)), "heavy_box": _epa(x, run & (x.box >= 8)),
                           **{f"cov_{c}": _epa(x, ps & (x.coverage == c)) for c in ["COVER_1", "COVER_2", "COVER_3", "COVER_4", "2_MAN", "COMBO"]}}})
    return out


def league(d: pd.DataFrame) -> dict:
    """League baselines for the same rates and the EPA in each look, so a team's number can be read against them."""
    ps = d.pass_play; db = d.dropback; run = d.play_type.eq("run"); cv = d[ps & d.cov_known]
    return {"pass_rate_neutral": _rate(ps, d.neutral), "man": (round(float(cv.man.mean()), 3) if len(cv) else None), "blitz": _rate(d.blitz == 1, db & d.blitz.notna()), "pressure": _rate(d.pressure == 1, db & d.pressure.notna()),
            "motion": _rate(d.is_motion == 1, d.is_motion.notna()), "play_action": _rate(d.is_play_action == 1, db & d.is_play_action.notna()), "shotgun": _rate(d.shotgun_f, d.play_type.notna()),
            "epa_pass": _epa(d, ps)["epa"], "epa_run": _epa(d, run)["epa"],
            "vs": {"man": _epa(d, ps & d.man), "zone": _epa(d, ps & d.zone), "blitz": _epa(d, db & (d.blitz == 1)), "no_blitz": _epa(d, db & (d.blitz == 0)), "pressure": _epa(d, db & (d.pressure == 1)), "clean": _epa(d, db & (d.pressure == 0)),
                   "play_action": _epa(d, db & (d.is_play_action == 1)), "no_play_action": _epa(d, db & (d.is_play_action == 0)), "light_box": _epa(d, run & (d.box <= 6)), "heavy_box": _epa(d, run & (d.box >= 8)),
                   **{f"cov_{c}": _epa(d, ps & (d.coverage == c)) for c in ["COVER_1", "COVER_2", "COVER_3", "COVER_4", "2_MAN", "COMBO"]}}}


def profiles_asof(d: pd.DataFrame, season: int, week: int) -> dict:
    """Every team's offense and defense profile on this season's games before `week`, and on last season in full,
    plus the league baselines for each. Nothing from `week` or later is used."""
    cur = d[(d.season == season) & (d.week < week)]; last = d[d.season == season - 1]
    teams = sorted(set(d[d.season == season].posteam.dropna()) | set(d[d.season == season - 1].posteam.dropna()))
    out = {"season": season, "week": week, "teams": {}, "league": {"current": league(cur) if len(cur) else {}, "last": league(last) if len(last) else {}}}
    for t in teams:
        out["teams"][t] = {"current": {"offense": profile(cur, t, "offense"), "defense": profile(cur, t, "defense")},
                           "last": {"offense": profile(last, t, "offense"), "defense": profile(last, t, "defense")}}
    return out


if __name__ == "__main__":
    import json, sys
    games = pd.read_parquet(OUT / "games.parquet"); season = int(games.season.max())
    d = load_plays(range(2016, season + 1))
    d.to_parquet(OUT / "scheme_plays.parquet", index=False)
    from .lines import current_week
    cs, cw = current_week(games)
    prof = profiles_asof(d, cs, cw)
    (OUT / "scheme_profiles.json").write_text(json.dumps(prof, default=lambda v: None if (isinstance(v, float) and np.isnan(v)) else (v.item() if hasattr(v, "item") else str(v))))
    print("scheme_plays", d.shape, "profiles for", len(prof["teams"]), "teams as of", cs, cw)
