"""Offensive line unit rating: variants against the AP All-Pro linemen (24 Sep 2026).

Against PFF's 2026 line rankings (experiments/ol_vs_pff.py) the unit rating's run half ranked Baltimore, Washington and
Buffalo near the top: rushing yards before contact counted quarterback runs, and a quarterback who runs well gets
yards before contact no line made. Variants of the team-game EPA saved (then spread over the linemen by snaps, the
page's method, rate = decayed saved / (decayed snaps + K)):

  V0 page now: pressures allowed per dropback + yards before contact per carry, all carries
  V1 carries by non-quarterbacks only (league average likewise)
  V2 V1, pressure half only (no run half)
  V3 V1 with the run half at half weight
  V4 V1, decay 0.98 / fade 0.9 (the defender groups' slower recency)

Scored like the defender groups (experiments/allpro_check.py): every lineman with 600+ offensive snaps in season S,
valued as of the end of S; where do that season's All-Pro linemen land (median rank, in top 20, average percentile),
per window. Adopt only if it helps on both windows. Writes reports/ol_allpro.csv.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import numpy as np, pandas as pd
from nflmodel import positions as P
from nflmodel.model import OUT
from nflmodel.reference import allpro

RAW = P.RAW
AP = allpro(); AP = AP[AP.group == "OL"]
sn = pd.concat([pd.read_parquet(f) for f in sorted((RAW / "snap_counts").glob("snap_counts_*.parquet"))], ignore_index=True)
sn = sn[sn.game_type == "REG"]; sn["team"] = sn.team.replace(P.TEAM_FIX)
qb_ids = set(sn[sn.position == "QB"].pfr_player_id)
a = pd.concat([pd.read_parquet(f, columns=["game_id", "season", "team", "times_pressured"]) for f in sorted((RAW / "pfr_pass").glob("advstats_week_pass_*.parquet"))])
u = pd.concat([pd.read_parquet(f, columns=["game_id", "season", "team", "pfr_player_id", "carries", "rushing_yards_before_contact"]) for f in sorted((RAW / "pfr_rush").glob("advstats_week_rush_*.parquet"))])
for x in (a, u):
    x["team"] = x.team.replace(P.TEAM_FIX)
u["qb"] = u.pfr_player_id.isin(qb_ids)
a = a.groupby(["game_id", "season", "team"], as_index=False).times_pressured.sum()
ua = u.groupby(["game_id", "season", "team"], as_index=False)[["carries", "rushing_yards_before_contact"]].sum()
un = u[~u.qb].groupby(["game_id", "season", "team"], as_index=False)[["carries", "rushing_yards_before_contact"]].sum().rename(columns={"carries": "car_nq", "rushing_yards_before_contact": "ybc_nq"})
tg = pd.read_parquet(OUT / "team_games.parquet", columns=["game_id", "team", "pass_plays"])
t = a.merge(ua, on=["game_id", "season", "team"], how="outer").merge(un, on=["game_id", "season", "team"], how="left").merge(tg, on=["game_id", "team"], how="left").fillna(0.0)
lg = t.groupby("season")[["times_pressured", "pass_plays", "rushing_yards_before_contact", "carries", "ybc_nq", "car_nq"]].sum()
t = t.join((lg.times_pressured / lg.pass_plays).rename("lp"), on="season").join((lg.rushing_yards_before_contact / lg.carries).rename("ly"), on="season").join((lg.ybc_nq / lg.car_nq).rename("lyn"), on="season")
W = P.OL_W
t["pass"] = W["press"] * (t.lp * t.pass_plays - t.times_pressured)
t["run_all"] = W["ybc"] * (t.rushing_yards_before_contact - t.ly * t.carries)
t["run_nq"] = W["ybc"] * (t.ybc_nq - t.lyn * t.car_nq)
VARIANTS = {"V0 page now (all carries)": ("run_all", 1.0, 0.92, 0.8), "V1 non-QB carries": ("run_nq", 1.0, 0.92, 0.8), "V2 pressures only": ("run_nq", 0.0, 0.92, 0.8),
            "V3 non-QB carries, run half x0.5": ("run_nq", 0.5, 0.92, 0.8), "V4 non-QB carries, 0.98 / 0.9": ("run_nq", 1.0, 0.98, 0.9)}
ids = P.pfr_ids()
ol = sn[sn.position.isin(P.OL_POS) & (sn.offense_snaps > 0)].copy(); ol["player_id"] = ol.pfr_player_id.map(ids); ol = ol.dropna(subset=["player_id"])
team_off = sn.groupby(["game_id", "team"]).offense_snaps.max().rename("team_off").reset_index()
g = ol.merge(t[["game_id", "team", "pass", "run_all", "run_nq"]], on=["game_id", "team"]).merge(team_off, on=["game_id", "team"])
g = g[g.season >= 2016].sort_values(["season", "week"]); g["plays"] = g.offense_snaps.astype(float); g["f"] = g.plays / g.team_off
K = 300.0


def run():
    res = []; by = {p: x for p, x in g.groupby("player_id")}
    for S in range(2016, 2026):
        snaps = g[g.season == S].groupby("player_id").plays.sum()
        ap = AP[AP.season == S].dropna(subset=["gsis_id"])
        pool = sorted(set([p for p in snaps.index if snaps[p] >= 600]) | set(p for p in ap.gsis_id if p in by))
        for name, (rc, rw, dec, fade) in VARIANTS.items():
            val = {}
            for p in pool:
                x = by[p][by[p].season <= S]
                w = dec ** np.arange(len(x))[::-1] * fade ** (S - x.season.values)
                val[p] = float((w * x.f * (x["pass"] + rw * x[rc])).sum() / ((w * x.plays).sum() + K))
            rk = pd.Series(val).rank(ascending=False); got = rk.reindex([p for p in ap.gsis_id if p in rk.index])
            res.append({"season": S, "variant": name, "n_pool": len(pool), "n_ap": len(got), "median_rank": float(got.median()),
                        "in_top20": int((got <= 20).sum()), "pct": float((1 - (got - 1) / len(pool)).mean())})
    r = pd.DataFrame(res); r["window"] = np.select([r.season <= 2018, r.season <= 2022], ["2015-18", "2019-22"], "2023-25")
    return r


if __name__ == "__main__":
    r = run(); r.to_csv(Path(__file__).resolve().parent.parent / "reports" / "ol_allpro.csv", index=False)
    s = r.groupby(["variant", "window"]).agg(median_rank=("median_rank", "mean"), in_top20=("in_top20", "sum"), n_ap=("n_ap", "sum"), pct=("pct", "mean")).round(3)
    pd.set_option("display.width", 250); print(s.unstack("window").to_string())
