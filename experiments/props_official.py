"""Props on the official box score (24 Sep 2026). The audit against nflverse's official player stats found the props
projected and graded passing yards net of sack yards (about 13 yards a QB-game under what the books settle on), counted
sacks as pass attempts, left kneel-downs out of carries and counted two-point tries as targets and carries.
props.official() and scheme.load_plays now use the box score's terms; every constant fitted on yards is refit here the
way it was first fitted, on the same seasons:
  TEAM_FIT yds   team yards of each kind = a + b x the game model's expected points, least squares on 2016 to 2018 (round 6)
  MED            the median factor on the yards line, one constant refit on 2017-18 with the team reconciliation (round 11)
Scored on 2019-22 and 2023-25 against the official numbers: the old constants and the refit ones. Passing's target
changed (gross yards), so its refit is adopted; receiving and rushing moved only by the two-point and kneel fixes, so
their refits are adopted only if they lower the error on both windows. Output reports/props_official.csv."""
import numpy as np, pandas as pd, pathlib, json
from nflmodel import props as PR
src = pathlib.Path(__file__).with_name("props_by_season.py").read_text().split("by_season, by_pos, by_bucket = [], [], []")[0]
src = src.replace("    # round 6: the team's players moved toward", "    f[\"base_line\"] = f.yds_line / PR.MED[kind]\n    # round 6: the team's players moved toward", 1)
ns = {"__name__": "bys"}; exec(compile(src, "bys", "exec"), ns); build = ns["build"]
WIN = {"2019-22": (2019, 2022), "2023-25": (2023, 2025)}
GRID = np.round(np.arange(0.70, 1.1001, 0.01), 2)


def recon_line(f, line, fy, wy):
    s = pd.Series(line, index=f.index).groupby([f.game_id, f.posteam]).transform("sum").values
    scale = np.clip((fy[0] + fy[1] * f.exp_pts.values) / np.where(s == 0, np.nan, s), 0.5, 2.0); ok = f.exp_pts.notna().values & ~np.isnan(scale)
    return np.where(ok, line * (1 + wy * (scale - 1)), line)


rows, new = [], {}
for kind in ("rec", "rush", "pass"):
    f, ev = build(kind); f = f.reset_index(drop=True); wy = PR.RECON_W[kind]["yds"]
    tg = f[f.exp_pts.notna()].groupby(["game_id", "posteam", "season"]).agg(act_yds=("act_yds", "sum"), exp_pts=("exp_pts", "first")).reset_index()
    fit = tg[tg.season <= 2018]; A = np.c_[np.ones(len(fit)), fit.exp_pts]; cy = np.linalg.lstsq(A, fit.act_yds, rcond=None)[0]; fy_new = (round(float(cy[0]), 2), round(float(cy[1]), 3))
    fs = f.season.values <= 2018
    tot = {m: float(np.abs(recon_line(f, m * f.base_line.values, fy_new, wy)[fs] - f.act_yds.values[fs]).mean()) for m in GRID}; m_new = float(min(tot, key=tot.get))
    variants = {"old constants": (PR.TEAM_FIT[kind]["yds"], PR.MED[kind]), "refit on the official numbers": (fy_new, m_new)}
    here = []
    for name, (fy, m) in variants.items():
        ln = recon_line(f, m * f.base_line.values, fy, wy); r = {"stat": f"{kind}_yards", "variant": name, "team_fit": f"{fy[0]} + {fy[1]} x exp pts", "med": m}
        for w, (a, b) in WIN.items():
            mk = f.season.between(a, b).values
            r[f"mae_{w}"] = round(float(np.abs(ln[mk] - f.act_yds.values[mk]).mean()), 2); r[f"bias_{w}"] = round(float((ln[mk] - f.act_yds.values[mk]).mean()), 2); r[f"n_{w}"] = int(mk.sum())
        here.append(r)
    better = all(here[1][f"mae_{w}"] < here[0][f"mae_{w}"] for w in WIN)
    here[1]["verdict"] = "adopted (the target changed to gross yards)" if kind == "pass" else ("adopted: better on both windows" if better else "not adopted")
    here[0]["verdict"] = "replaced" if (kind == "pass" or better) else "kept"
    if kind == "pass" or better: new[kind] = {"team_fit_yds": fy_new, "med": m_new}
    rows += here; print(pd.DataFrame(here).to_string(index=False), flush=True)
pd.DataFrame(rows).to_csv("reports/props_official.csv", index=False); print("NEW", json.dumps(new)); print("DONE")
