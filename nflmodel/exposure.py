"""How much of each game a player actually played (24 Sep 2026). One row per player and game from nflverse snap
counts (2012 on), keyed by gsis id through the weekly rosters' Pro-Football-Reference ids: offense and defense
snap share. Per-game numbers (usage shares, touches or dropbacks a game, tackles a game) use it so that a game a
player left on the first drive, or a one-play cameo, does not count as a full game.

  exposure(pid, game) = his snap share in the game / his median snap share over his recent games, capped at 1:
  about 1 for a normal game, 0.1 for a game he left early.

python -m nflmodel.exposure   builds data/processed/snap_exposure.parquet
"""
from __future__ import annotations
import pandas as pd
from .features import RAW, OUT, TEAM_FIX


def build(seasons=range(2012, 2027)) -> pd.DataFrame:
    pmap = {}
    for s in seasons:
        f = RAW / "rosters" / f"roster_weekly_{s}.parquet"
        if f.exists():
            r = pd.read_parquet(f, columns=["gsis_id", "pfr_id"]).dropna().drop_duplicates()
            pmap.update(dict(zip(r.pfr_id, r.gsis_id)))
    fr = []
    for s in seasons:
        f = RAW / "snap_counts" / f"snap_counts_{s}.parquet"
        if f.exists():
            fr.append(pd.read_parquet(f, columns=["game_id", "season", "week", "pfr_player_id", "team", "position", "offense_snaps", "offense_pct", "defense_snaps", "defense_pct"]))
    d = pd.concat(fr, ignore_index=True)
    d["player_id"] = d.pfr_player_id.map(pmap); d["team"] = d.team.replace(TEAM_FIX)
    d = d[d.player_id.notna()].rename(columns={"offense_pct": "off_pct", "defense_pct": "def_pct"})
    d = d.drop_duplicates(["player_id", "game_id"])[["player_id", "game_id", "season", "week", "team", "position", "offense_snaps", "off_pct", "defense_snaps", "def_pct"]]
    d.to_parquet(OUT / "snap_exposure.parquet", index=False)
    return d


def load() -> pd.DataFrame:
    f = OUT / "snap_exposure.parquet"
    return pd.read_parquet(f) if f.exists() else build()


if __name__ == "__main__":
    d = build(); print("snap exposure", d.shape, "seasons", d.season.min(), "to", d.season.max())
