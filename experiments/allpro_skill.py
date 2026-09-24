"""Skill values (the page's and the game model's) against the AP All-Pro receivers, backs and tight ends, both windows
(24 Sep 2026). Each season's regulars (60+ touches that season at the position) valued at the season's end; where do
that season's All-Pros land? Also the published 2026 lists where saved. Writes reports/allpro_skill.csv."""
import numpy as np, pandas as pd
from nflmodel import players as PL
from nflmodel.model import OUT
from nflmodel.reference import allpro

AP = allpro()
pg = pd.read_parquet(OUT / "player_games.parquet")
import sys
K = float(sys.argv[1]) if len(sys.argv) > 1 else PL.DEFAULT["k"]
pv = PL.PlayerValues(pg, PL.DEFAULT["decay"], K, PL.DEFAULT.get("pct", 25)); _, by_player, by_team = PL._usage_frames(pg)
POSR = {"WR": "WR", "RB": "RB", "TE": "TE"}
names = pg.groupby("player_id").name.last()
res = []
for S in range(2019, 2026):
    x = pg[(pg.season == S) & pg.role.isin(["receiver", "rusher"])]
    for grp in ["WR", "RB", "TE"]:
        rr = pd.read_parquet(PL.RAW / "rosters" / f"roster_weekly_{S}.parquet", columns=["gsis_id", "position"]).dropna()
        posn = rr.groupby("gsis_id").position.agg(lambda v: v.mode().iloc[0])
        touches = x.groupby("player_id").plays.sum()
        ap = AP[(AP.season == S) & (AP.group == grp)].dropna(subset=["gsis_id"])
        pool = sorted({p for p in touches.index if touches[p] >= 60 and posn.get(p) == grp} | set(ap.gsis_id))
        vals = {}
        for p in pool:
            team = x[x.player_id == p].team.iloc[-1] if (x.player_id == p).any() else None
            vals[p] = PL.player_value_out(pv, by_player, p, S + 1, 1, 8, team, by_team)["value"]
        rk = pd.Series(vals).rank(ascending=False); got = rk.reindex([p for p in ap.gsis_id if p in rk.index])
        res.append({"season": S, "group": grp, "n_pool": len(pool), "n_ap": len(got), "median_rank": float(got.median()) if len(got) else np.nan, "in_top10": int((got <= 10).sum()),
                    "pct": float((1 - (got - 1) / len(pool)).mean()) if len(got) else np.nan, "ap_ranks": ", ".join(f"{names.get(p, p)} {int(r)}" for p, r in got.items())})
        pass
r = pd.DataFrame(res); r["window"] = np.where(r.season <= 2022, "2019-22", "2023-25"); r.to_csv(f"reports/allpro_skill{'' if K == PL.DEFAULT['k'] else '_k' + str(int(K))}.csv", index=False)
print("K", K); print(r.groupby(["group", "window"]).agg(median_rank=("median_rank", "mean"), in_top10=("in_top10", "sum"), n_ap=("n_ap", "sum"), pct=("pct", "mean")).round(3).to_string())
