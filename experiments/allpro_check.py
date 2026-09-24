"""Player values against the AP All-Pro teams (24 Sep 2026). For each season S and position group, every regular's
value as of the end of S (earlier and same-season games, the variant's weights) is ranked; where do that season's AP
first and second teams land? Scored per window (2019-22, 2023-25): the All-Pros' median rank, how many sit in our top
10, and the average percentile. The All-Pro teams are a consensus of what happened that season (50 voters), so this is
a yardstick with history, not one published list. Defender groups use defender_games.parquet; regulars have 400+
snaps that season. Writes reports/allpro_check.csv. Usage: python -m experiments.allpro_check [GROUP ...]"""
import sys
import numpy as np, pandas as pd
from nflmodel import positions as P
from nflmodel.model import OUT
from nflmodel.reference import allpro

AP = allpro()
dg = pd.read_parquet(OUT / "defender_games.parquet"); W = P.DEF_W
dg = dg.assign(cov=W["cov_yds"] * dg.cov_yds + W["cov_int"] * dg.cov_int, rush=W["sacks"] * dg.sacks + W["press_ns"] * dg.press_ns)
dg = dg[dg.season >= 2018].sort_values(["season", "week"])
# each defender's group in each season: his snap-count position that season, linebackers who pressure on 1.5%+ as edge
def season_roles(S):
    x = dg[dg.season == S]
    pos = x.groupby("player_id").position.agg(lambda v: v.mode().iloc[0] if len(v.mode()) else "")
    r = x.groupby("player_id").agg(press=("press", "sum"), plays=("plays", "sum")); rate = r.press / r.plays.where(r.plays > 0)
    return {pid: ("EDGE" if P.DEF_ROLE.get(p, "CB") == "LB" and rate.get(pid, 0) >= P.EDGE_PRESS else P.DEF_ROLE.get(p, "CB")) for pid, p in pos.items()}

T_CB = float(dg[dg.position == "CB"].targets.sum() / dg[dg.position == "CB"].plays.sum())

def rate(g, S, v):
    """v: dict(kind, decay, fade, k, parts, a)."""
    w = v["decay"] ** np.arange(len(g))[::-1] * v["fade"] ** (S - g.season.values)
    if v["kind"] == "snap":
        num = sum(v["parts"].get(c, 0) * g[c].values for c in ["cov", "rush", "run_stop", "ff_epa", "credit_epa", "credited"])
        return float((w * num).sum() / ((w * g.plays.values).sum() + v["k"]))
    cov = (w * g["cov"].values).sum() / ((w * g.targets.values).sum() + v["k"]) * T_CB
    other = sum(v["parts"].get(c, 0) * g[c].values for c in ["rush", "run_stop", "ff_epa"])
    return float(cov + v.get("a", 0) * (w * other).sum() / ((w * g.plays.values).sum() + 300))

ALL = {"cov": 1, "rush": 1, "run_stop": 1, "ff_epa": 1}
VARIANTS = {
    "per snap, every part, 0.92 / 0.8 (page now)": dict(kind="snap", decay=0.92, fade=0.8, k=300, parts=ALL),
    "per snap, every part, 0.98 / 0.9": dict(kind="snap", decay=0.98, fade=0.9, k=300, parts=ALL),
    "per snap, no forced fumbles, 0.92 / 0.8": dict(kind="snap", decay=0.92, fade=0.8, k=300, parts={"cov": 1, "rush": 1, "run_stop": 1}),
    "per snap, coverage + rush only, 0.92 / 0.8": dict(kind="snap", decay=0.92, fade=0.8, k=300, parts={"cov": 1, "rush": 1}),
    "per target coverage, 0.99 (CB page now)": dict(kind="t", decay=0.99, fade=1.0, k=150, parts={}, a=0),
    "per target coverage + run/rush share 0.5, 0.99": dict(kind="t", decay=0.99, fade=1.0, k=150, parts={"rush": 1, "run_stop": 1}, a=0.5),
    "per target coverage + run/rush share 1.0, 0.99": dict(kind="t", decay=0.99, fade=1.0, k=150, parts={"rush": 1, "run_stop": 1}, a=1.0),
    # linebackers (24 Sep 2026): run stops and tackle credit carry the position
    "per snap, every part, 0.99 / 1.0": dict(kind="snap", decay=0.99, fade=1.0, k=300, parts=ALL),
    "per snap, run stops x2, 0.92 / 0.8": dict(kind="snap", decay=0.92, fade=0.8, k=300, parts={"cov": 1, "rush": 1, "run_stop": 2, "ff_epa": 1}),
    "per snap, run stops x2, 0.98 / 0.9": dict(kind="snap", decay=0.98, fade=0.9, k=300, parts={"cov": 1, "rush": 1, "run_stop": 2, "ff_epa": 1}),
    "per snap, every part + credited plays, 0.92 / 0.8": dict(kind="snap", decay=0.92, fade=0.8, k=300, parts={**ALL, "credit_epa": 1}),
    "per snap, every part + credited plays, 0.98 / 0.9": dict(kind="snap", decay=0.98, fade=0.9, k=300, parts={**ALL, "credit_epa": 1}),
    "per snap, every part + tackles x0.3, 0.98 / 0.9": dict(kind="snap", decay=0.98, fade=0.9, k=300, parts={**ALL, "credited": 0.3}),
    **{f"per snap, every part + tackles x{t}, {d} / {f}": dict(kind="snap", decay=d, fade=f, k=300, parts={**ALL, "credited": t})
       for t in (0.1, 0.2, 0.5, 0.75, 1.0, 1.5) for d, f in ((0.92, 0.8), (0.98, 0.9))},
    "per snap, every part + tackles x0.3, 0.92 / 0.8": dict(kind="snap", decay=0.92, fade=0.8, k=300, parts={**ALL, "credited": 0.3}),
}

def run(groups):
    res = []; by = {p: g for p, g in dg.groupby("player_id")}
    for S in range(2019, 2026):
        roles = season_roles(S); snaps = dg[dg.season == S].groupby("player_id").plays.sum()
        for grp in groups:
            ap = AP[(AP.season == S) & (AP.group == grp)].dropna(subset=["gsis_id"])
            pool = [p for p in snaps.index if snaps[p] >= 400 and roles.get(p) == grp] + [p for p in ap.gsis_id if p in by]
            pool = sorted(set(pool))
            for name, v in VARIANTS.items():
                val = pd.Series({p: rate(by[p][by[p].season <= S], S, v) for p in pool})
                rk = val.rank(ascending=False)
                got = rk.reindex([p for p in ap.gsis_id if p in rk.index])
                res.append({"season": S, "group": grp, "variant": name, "n_pool": len(pool), "n_ap": len(got), "median_rank": float(got.median()) if len(got) else np.nan,
                            "in_top10": int((got <= 10).sum()), "pct": float((1 - (got - 1) / len(pool)).mean()) if len(got) else np.nan})
    r = pd.DataFrame(res); r["window"] = np.where(r.season <= 2022, "2019-22", "2023-25")
    return r

if __name__ == "__main__":
    groups = sys.argv[1:] or ["S", "LB", "CB", "EDGE", "IDL"]
    r = run(groups); r.to_csv("reports/allpro_check.csv", index=False)
    s = r.groupby(["group", "variant", "window"]).agg(median_rank=("median_rank", "mean"), in_top10=("in_top10", "sum"), n_ap=("n_ap", "sum"), pct=("pct", "mean")).round(3)
    pd.set_option("display.width", 250); print(s.unstack("window").to_string())
