"""Cornerback value against the consensus and against next season (24 Sep 2026).

Matt: the corner list was nothing like a consensus view (Nahshon Wright 2nd, Surtain 27th, Sauce Gardner 109th).
Two yardsticks, so no single list is fitted:

1. Consensus, 2026 (confirmed ranks only): FOX Sports' top 10 (Surtain, Stingley, Gonzalez, Witherspoon, McDuffie,
   Mitchell, D. Ward, Horn, DeJean, Gardner; https://www.foxsports.com/stories/nfl/2026-nfl-top-10-cbs-which-cornerback-best-league),
   PFF's top 32 where confirmed (1 Witherspoon, 2 Gardner, 3 Surtain, 5 DeJean, 6 Mitchell, 8 Gonzalez, 9 Lassiter,
   10 M. Jackson, 14 J. Johnson, 15 J. Watson, 20 D. Ward, 24 C. Ward, 30 T. Still, 32 K. Nixon;
   https://www.pff.com/news/pff-cornerback-rankings-the-top-32-players-entering-the-2026-nfl-season). Scored: how many
   of the 17 sit in our top 15, their median rank, and the rank correlation among them.
2. Next season: each corner's rating before a season against his coverage per target that season (30+ targets),
   correlation per season, averaged over 2019-22 (tuning) and 2023-25 (held out). The rule: best on 2019-22, better
   than today's recipe held out.

Variants: today's (per snap, every part, 0.92 / 0.8), per snap with a longer memory, coverage per target at two
memories, and per target with a draft-round prior and a run share. Writes reports/cb_value.csv."""
import numpy as np, pandas as pd
from nflmodel import positions as P
from nflmodel.model import OUT

FOX = ["Pat Surtain II", "Derek Stingley Jr.", "Christian Gonzalez", "Devon Witherspoon", "Trent McDuffie", "Quinyon Mitchell", "Denzel Ward", "Jaycee Horn", "Cooper DeJean", "Sauce Gardner"]
PFF = {"Devon Witherspoon": 1, "Sauce Gardner": 2, "Pat Surtain II": 3, "Cooper DeJean": 5, "Quinyon Mitchell": 6, "Christian Gonzalez": 8, "Kamari Lassiter": 9, "Mike Jackson": 10,
       "Jaylon Johnson": 14, "Jaylen Watson": 15, "Denzel Ward": 20, "Charvarius Ward": 24, "Tarheeb Still": 30, "Keisean Nixon": 32}
dg = pd.read_parquet(OUT / "defender_games.parquet"); W = P.DEF_W
d = dg.assign(cov=W["cov_yds"] * dg.cov_yds + W["cov_int"] * dg.cov_int, non=W["sacks"] * dg.sacks + W["press_ns"] * dg.press_ns + dg.run_stop + dg.ff_epa)
d = d[d.season >= 2018].sort_values(["season", "week"])
roles = P.defender_roles(dg); d = d[d.player_id.map(roles) == "CB"]
T = float(d.targets.sum() / d.plays.sum())
drx = pd.read_parquet(P.RAW / "draft" / "draft_picks.parquet", columns=["gsis_id", "round"]).dropna().drop_duplicates("gsis_id").set_index("gsis_id")["round"]
bucket = lambda r: 1 if r == 1 else (2 if r == 2 else (3 if r <= 4 else 4))
h = d[d.season == 2018]; pri = h.assign(b=h.player_id.map(lambda p: bucket(drx.get(p, 8)))).groupby("b").apply(lambda g: g["cov"].sum() / g.targets.sum())
V = {"today: per snap, every part, 0.92 / 0.8": ("snap", 0.92, 0.8, 300, 0, 0), "per snap, every part, 0.98 / 0.9": ("snap", 0.98, 0.9, 300, 0, 0),
     "per target, 0.98 / 0.9, K150": ("t", 0.98, 0.9, 150, 0, 0), "per target, 0.99 / 1.0, K150 (adopted)": ("t", 0.99, 1.0, 150, 0, 0),
     "per target + draft prior K250 + run 0.25, 0.98 / 0.9": ("t", 0.98, 0.9, 0, 0.25, 250)}


def rating(g, kind, dec, fade, k, a, kp, season):
    w = dec ** np.arange(len(g))[::-1] * fade ** (season - g.season.values)
    if kind == "snap":
        return float((w * (g["cov"].values + g.non.values)).sum() / ((w * g.plays.values).sum() + k))
    p = pri.get(bucket(drx.get(g.player_id.iloc[0], 8)), 0.0) if kp else 0.0
    cov = ((w * g["cov"].values).sum() + kp * p) / ((w * g.targets.values).sum() + k + kp)
    return float(cov * T + (a * (w * g.non.values).sum() / ((w * g.plays.values).sum() + 300) if a else 0.0))


by = {p: g for p, g in d.groupby("player_id")}
names = dict(zip(dg.player_id, dg.name))
cons = {}
for n in set(FOX) | set(PFF):
    r = ([FOX.index(n) + 1] if n in FOX else [PFF[n] + 5]) + ([PFF[n]] if n in PFF else [16])
    cons[n] = float(np.mean(r))
cons = pd.Series(cons)
res = []
for name, (kind, dec, fade, k, a, kp) in V.items():
    row = {"variant": name}
    for window, seasons in [("2019-22", range(2019, 2023)), ("2023-25", range(2023, 2026))]:
        cs = []
        for S in seasons:
            act = d[d.season == S].groupby("player_id").agg(t=("targets", "sum"), c=("cov", "sum")); act = act[act.t >= 30]; act["y"] = act.c / act.t
            pr = []
            for pid in act.index:
                g = by[pid]; g = g[g.season < S]
                pr.append(rating(g, kind, dec, fade, k, a, kp, S) if len(g) else (pri.get(bucket(drx.get(pid, 8)), 0.0) * T if kp else 0.0))
            cs.append(np.corrcoef(pr, act.y)[0, 1])
        row[f"next_season_corr_{window}"] = round(float(np.mean(cs)), 3)
    now = pd.Series({pid: rating(g, kind, dec, fade, k, a, kp, 2026) for pid, g in by.items() if g.season.max() >= 2025})
    rk = now.rank(ascending=False); rk.index = [names.get(i, i) for i in rk.index]; rk = rk.groupby(level=0).min()   # two players can share a name
    got = rk.reindex(cons.index).dropna()
    row.update({"consensus_in_top15": int((got <= 15).sum()), "consensus_median_rank": float(got.median()),
                "consensus_rank_corr": round(float(pd.Series(cons[got.index].values).rank().corr(pd.Series(got.values).rank())), 2),
                "top10": ", ".join(rk.sort_values().index[:10])})
    res.append(row); print(row, flush=True)
pd.DataFrame(res).to_csv("reports/cb_value.csv", index=False)
