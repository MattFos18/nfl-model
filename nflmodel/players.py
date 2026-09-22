"""Player-level offense, phase 1 of the player model.

player_games.parquet   one row per (game, team, player, role) from the play-by-play: plays and EPA as passer, rusher or
                       receiver (targets), with the player's name. 2013 on.
PlayerValues           a decayed, shrunk EPA per play for any player and role as of a week: nothing from that week or
                       later. Same shape as the QB rating (ratings.QBRatings): value = (sum w*epa + k*prior) / (sum w*plays + k).
                       The prior is replacement level for the role: the 25th percentile of per-play EPA among players
                       with 100+ plays in the seasons before the one asked for.
injury_value()         per (game, team): the value the offense loses to skill players listed Out or Doubtful on the
                       final report, in EPA per team play: sum over those players of (value - replacement) x their usage
                       share of the team's touches in the previous eight games. skill_out_value is the phase 2 candidate
                       input (experiments/player_injury.py); the QB is excluded because qb_out already covers it.

Usage: python -m nflmodel.players            builds player_games.parquet and player_injury.parquet
"""
from __future__ import annotations
import numpy as np, pandas as pd
from pathlib import Path
from .features import RAW, OUT, TEAM_FIX

ROLES = {"passer": ("passer_player_id", "passer_player_name", "qb_dropback"), "rusher": ("rusher_player_id", "rusher_player_name", "rush_attempt"),
         "receiver": ("receiver_player_id", "receiver_player_name", "pass_attempt")}
SKILL = {"rusher", "receiver"}
DEFAULT = {"decay": 0.985, "k": 80.0, "usage_games": 8}
PCOLS = ["game_id", "season", "week", "season_type", "posteam", "epa", "qb_epa", "qb_dropback", "rush_attempt", "pass_attempt", "play_type"] + [c for r in ROLES.values() for c in r[:2]]


def load(seasons) -> pd.DataFrame:
    frames = []
    for s in seasons:
        f = RAW / "pbp" / f"play_by_play_{s}.parquet"
        if f.exists():
            import pyarrow.parquet as pq
            have = set(pq.ParquetFile(f).schema.names)
            frames.append(pd.read_parquet(f, columns=[c for c in PCOLS if c in have]))
    p = pd.concat(frames, ignore_index=True)
    p["posteam"] = p.posteam.replace(TEAM_FIX)
    return p[p.posteam.notna() & p.play_type.isin(["pass", "run"])]


def player_box(p: pd.DataFrame) -> pd.DataFrame:
    out = []
    for role, (idc, namec, flag) in ROLES.items():
        d = p[(pd.to_numeric(p[flag], errors="coerce") == 1) & p[idc].notna()].copy()
        d["epa"] = pd.to_numeric(d.qb_epa if role == "passer" else d.epa, errors="coerce")
        g = d.groupby(["game_id", "season", "week", "posteam", idc]).agg(plays=("epa", "size"), epa=("epa", "sum"), name=(namec, "first")).reset_index()
        g = g.rename(columns={"posteam": "team", idc: "player_id"}); g["role"] = role
        out.append(g)
    return pd.concat(out, ignore_index=True).sort_values(["season", "week", "game_id", "team", "role"]).reset_index(drop=True)


class PlayerValues:
    def __init__(self, pg: pd.DataFrame, decay=DEFAULT["decay"], k=DEFAULT["k"]):
        self.pg = pg.sort_values(["season", "week"]); self.decay, self.k = decay, k
        self._cache, self._prior = {}, {}
        self.by = {key: g for key, g in self.pg.groupby(["player_id", "role"])}

    def prior(self, role: str, season: int) -> float:
        key = (role, season)
        if key not in self._prior:
            h = self.pg[(self.pg.role == role) & (self.pg.season < season)]
            tot = h.groupby("player_id").agg(plays=("plays", "sum"), epa=("epa", "sum"))
            tot = tot[tot.plays >= 100]
            self._prior[key] = float(np.percentile(tot.epa / tot.plays, 25)) if len(tot) else 0.0
        return self._prior[key]

    def value(self, pid: str, role: str, season: int, week: int) -> tuple[float, float]:
        """(value, weighted plays) as of (season, week)."""
        key = (pid, role, season, week)
        if key in self._cache:
            return self._cache[key]
        g = self.by.get((pid, role))
        pr = self.prior(role, season)
        if g is None:
            r = (pr, 0.0)
        else:
            h = g[(g.season < season) | ((g.season == season) & (g.week < week))]
            if len(h) == 0:
                r = (pr, 0.0)
            else:
                w = self.decay ** np.arange(len(h))[::-1]
                n = float((h.plays.values * w).sum()); e = float((h.epa.values * w).sum())
                r = ((e + self.k * pr) / (n + self.k), n)
        self._cache[key] = r
        return r


def injury_value(games: pd.DataFrame, pg: pd.DataFrame, seasons=range(2013, 2027), p=DEFAULT) -> pd.DataFrame:
    inj = pd.concat([pd.read_parquet(RAW / "injuries" / f"injuries_{s}.parquet") for s in seasons if (RAW / "injuries" / f"injuries_{s}.parquet").exists()], ignore_index=True)
    inj["team"] = inj.team.replace({"OAK": "LV", "SD": "LAC", "STL": "LA"})
    inj = inj[inj.report_status.isin(["Out", "Doubtful"]) & (inj.position != "QB")]
    out_by = {k: set(g.gsis_id.dropna()) for k, g in inj.groupby(["season", "week", "team"])}
    pv = PlayerValues(pg, p["decay"], p["k"])
    skill = pg[pg.role.isin(SKILL)]
    team_touch = skill.groupby(["game_id", "season", "week", "team"]).plays.sum().rename("team_plays").reset_index()
    skill = skill.merge(team_touch, on=["game_id", "season", "week", "team"])
    by_team = {t: g.sort_values(["season", "week"]) for t, g in skill.groupby("team")}
    rows = []
    long = pd.concat([games[["game_id", "season", "week", "home_team"]].rename(columns={"home_team": "team"}), games[["game_id", "season", "week", "away_team"]].rename(columns={"away_team": "team"})])
    long = long[long.season.isin(seasons)]
    for r in long.itertuples():
        outs = out_by.get((r.season, r.week, r.team), set())
        g = by_team.get(r.team)
        if g is None or not outs:
            rows.append({"game_id": r.game_id, "team": r.team, "skill_out_value": 0.0, "skill_out_share": 0.0, "n_skill_out": 0}); continue
        h = g[(g.season < r.season) | ((g.season == r.season) & (g.week < r.week))]
        recent_ids = h.game_id.drop_duplicates().tail(p["usage_games"])
        h = h[h.game_id.isin(recent_ids)]
        tot = float(h.groupby("game_id").team_plays.first().sum()) or 1.0
        val, share, n = 0.0, 0.0, 0
        for pid in outs:
            hp = h[h.player_id == pid]
            if len(hp) == 0:
                continue
            s = float(hp.plays.sum()) / tot
            v = 0.0
            for role in SKILL:
                hr = hp[hp.role == role]
                if len(hr) == 0:
                    continue
                vv, _ = pv.value(pid, role, r.season, r.week)
                v += (vv - pv.prior(role, r.season)) * float(hr.plays.sum()) / tot
            val += v; share += s; n += 1
        rows.append({"game_id": r.game_id, "team": r.team, "skill_out_value": val, "skill_out_share": share, "n_skill_out": n})
    return pd.DataFrame(rows)


if __name__ == "__main__":
    games = pd.read_parquet(OUT / "games.parquet")
    pg = player_box(load(range(2013, 2027)))
    pg.to_parquet(OUT / "player_games.parquet", index=False)
    print("player_games", pg.shape, pg.player_id.nunique(), "players")
    iv = injury_value(games, pg)
    iv.to_parquet(OUT / "player_injury.parquet", index=False)
    print("player_injury", iv.shape, "rows with a skill player out:", int((iv.n_skill_out > 0).sum()))
    print(iv[iv.n_skill_out > 0].describe().to_string())
