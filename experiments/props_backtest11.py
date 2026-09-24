"""Round eleven (23 Sep 2026): a walk-forward median factor for the yards lines. The factor that turns a player's mean
yards into the line that misses by least (receivers 0.88, rushers 0.84, QBs 0.90) was fitted once on 2016 to 2018.
League passing has fallen since, and the passing line's bias drifted from about 0 (2019-22) to +6 yards (2023-25).
Variants, per kind, each season's factor chosen on earlier seasons only (grid 0.70 to 1.10 by 0.01, the team
reconciliation of round six applied at each candidate, in the order the live rule applies them):
  fixed      the adopted constant
  expanding  every season from 2017 to the one before
  rolling3   the three seasons before
  rolling2   the two seasons before
Scored by mean absolute error per player-game on 2019-22 and 2023-25, league averages as of each game. A variant is
adopted for a kind only if it lowers the error on both windows.
Output reports/props_backtest11.csv."""
import numpy as np, pandas as pd, pathlib
from nflmodel import props as PR
src = pathlib.Path(__file__).with_name("props_by_season.py").read_text().split("by_season, by_pos, by_bucket = [], [], []")[0]
src = src.replace("    # round 6: the team's players moved toward", "    f[\"base_line\"] = f.yds_line / PR.MED[kind]\n    # round 6: the team's players moved toward", 1)
ns = {"__name__": "bys"}; exec(compile(src, "bys", "exec"), ns); build = ns["build"]
WIN = {"2019-22": (2019, 2022), "2023-25": (2023, 2025)}
GRID = np.round(np.arange(0.70, 1.1001, 0.01), 2)


def recon_line(f, line, kind):
    fy, wy = PR.TEAM_FIT[kind]["yds"], PR.RECON_W[kind]["yds"]
    s = pd.Series(line, index=f.index).groupby([f.game_id, f.posteam]).transform("sum").values
    scale = np.clip((fy[0] + fy[1] * f.exp_pts.values) / np.where(s == 0, np.nan, s), 0.5, 2.0); ok = f.exp_pts.notna().values & ~np.isnan(scale)
    return np.where(ok, line * (1 + wy * (scale - 1)), line)


rows = []
for kind in ("rec", "rush", "pass"):
    f, ev = build(kind); f = f.reset_index(drop=True)
    err, lines = {}, {}
    for m in GRID:
        ln = recon_line(f, m * f.base_line.values, kind); lines[m] = ln
        e = np.abs(ln - f.act_yds.values)
        for s, idx in f.groupby("season").groups.items():
            err[(int(s), m)] = (float(e[idx].sum()), len(idx))
    fixed = recon_line(f, PR.MED[kind] * f.base_line.values, kind)
    seasons = sorted(int(s) for s in f.season.unique())
    choose = {}
    for name, lookback in (("expanding", None), ("rolling3", 3), ("rolling2", 2)):
        pick = {}
        for s in seasons:
            prior = [p for p in seasons if p < s and (lookback is None or p >= s - lookback)]
            if prior:
                tot = {m: sum(err[(p, m)][0] for p in prior) / sum(err[(p, m)][1] for p in prior) for m in GRID}
                pick[s] = float(min(tot, key=tot.get))
        choose[name] = pick
    # the clean form: one constant refit on the fitting seasons (2017-18: 2016 has no prior charted season) with today's rule
    fit_s = [p for p in seasons if p <= 2018]
    tot = {m: sum(err[(p, m)][0] for p in fit_s) / sum(err[(p, m)][1] for p in fit_s) for m in GRID}; m_fit = float(min(tot, key=tot.get))
    choose["refit_2017_18"] = {s: m_fit for s in seasons}
    out = {"fixed": fixed}
    for name, pick in choose.items():
        out[name] = np.array([lines[pick[int(s)]][i] if int(s) in pick else fixed[i] for i, s in enumerate(f.season.values)])
    here = []
    for name, ln in out.items():
        r = {"stat": f"{kind}_yards", "variant": name}
        for w, (a, b) in WIN.items():
            mk = f.season.between(a, b).values
            r[f"mae_{w}"] = round(float(np.abs(ln[mk] - f.act_yds.values[mk]).mean()), 3); r[f"bias_{w}"] = round(float((ln[mk] - f.act_yds.values[mk]).mean()), 2); r[f"n_{w}"] = int(mk.sum())
        r["factors"] = "" if name == "fixed" else (f"{m_fit:.2f}" if name == "refit_2017_18" else ", ".join(f"{s}: {v:.2f}" for s, v in choose[name].items() if s >= 2019))
        here.append(r)
    fx = here[0]; fx["verdict"] = "adopted today"
    for x in here[1:]:
        x["verdict"] = "better on both windows" if all(x[f"mae_{w}"] < fx[f"mae_{w}"] for w in WIN) else "not adopted"
    rows += here
    print(pd.DataFrame(here).to_string(index=False), flush=True)
    if kind == "rec":   # receptions: the same test on MED_CATCH (no team reconciliation on catches)
        cb = f.catch_line.values / PR.MED_CATCH; ce = {}
        for m in GRID:
            e = np.abs(m * cb - f.act_catch.values)
            for s_, idx in f.groupby("season").groups.items():
                ce[(int(s_), m)] = (float(e[idx].sum()), len(idx))
        tot = {m: sum(ce[(p, m)][0] for p in fit_s) / sum(ce[(p, m)][1] for p in fit_s) for m in GRID}; mc = float(min(tot, key=tot.get))
        exp_pick = {}
        for s_ in seasons:
            prior = [p for p in seasons if p < s_]
            if prior:
                t2 = {m: sum(ce[(p, m)][0] for p in prior) / sum(ce[(p, m)][1] for p in prior) for m in GRID}; exp_pick[s_] = float(min(t2, key=t2.get))
        cvars = {"fixed": np.full(len(f), PR.MED_CATCH), "refit_2017_18": np.full(len(f), mc), "expanding": np.array([exp_pick.get(int(s_), PR.MED_CATCH) for s_ in f.season.values])}
        here = []
        for name, mm in cvars.items():
            ln = mm * cb; r = {"stat": "rec_catches", "variant": name}
            for w, (a, b) in WIN.items():
                mk = f.season.between(a, b).values
                r[f"mae_{w}"] = round(float(np.abs(ln[mk] - f.act_catch.values[mk]).mean()), 4); r[f"bias_{w}"] = round(float((ln[mk] - f.act_catch.values[mk]).mean()), 3); r[f"n_{w}"] = int(mk.sum())
            r["factors"] = "" if name == "fixed" else (f"{mc:.2f}" if name == "refit_2017_18" else ", ".join(f"{s_}: {v:.2f}" for s_, v in exp_pick.items() if s_ >= 2019))
            here.append(r)
        here[0]["verdict"] = "adopted today"
        for x in here[1:]:
            x["verdict"] = "better on both windows" if all(x[f"mae_{w}"] < here[0][f"mae_{w}"] for w in WIN) else "not adopted"
        rows += here; print(pd.DataFrame(here).to_string(index=False), flush=True)
pd.DataFrame(rows).to_csv("reports/props_backtest11.csv", index=False)
print("DONE")
