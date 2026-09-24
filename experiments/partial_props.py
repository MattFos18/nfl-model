"""Partial games, part B (24 Sep 2026): the props' usage share (a receiver's share of team targets, a back's share
of carries, decayed per game) with games he left early counted as full games (none), dropped (exclude: under half
his usual snap share, by the median of his previous eight games), or counted by his snap share (weight). The rule
in play otherwise unchanged; scored per player-game on 2019-22 and 2023-25: yards and receptions error, touchdown
Poisson log loss. Adopt per kind only if it helps both windows. Appends to reports/partial_games.csv."""
import os, numpy as np, pandas as pd, pathlib
from nflmodel import props as PR
src = pathlib.Path(__file__).with_name("props_by_season.py").read_text().split("by_season, by_pos, by_bucket = [], [], []")[0]
src = src.replace("    # round 6: the team's players moved toward", "    f[\"base_line\"] = f.yds_line / PR.MED[kind]\n    # round 6: the team's players moved toward", 1)
ns = {"__name__": "bys"}; exec(compile(src, "bys", "exec"), ns); build = ns["build"]; pll = ns["pll"]
WIN = {"2019-22": (2019, 2022), "2023-25": (2023, 2025)}
rows = []
for kind in ("rec", "rush"):
    for mode in (__import__("os").environ.get("MODES") or "none,exclude,weight").split(","):
        ns["PARTIAL_MODE"] = None if mode == "none" else ("exclude" if mode.startswith("exclude") else mode); ns["PARTIAL_T"] = 0.25 if mode == "exclude25" else 0.5
        f, ev = build(kind)
        # each variant gets its own median factors refit on 2017-18 (the constants absorb how high the shares run)
        GRID = np.round(np.arange(0.60, 1.2001, 0.01), 2); fy, wy = PR.TEAM_FIT[kind]["yds"], PR.RECON_W[kind]["yds"]
        def recon(line):
            s_ = pd.Series(line, index=f.index).groupby([f.game_id, f.posteam]).transform("sum").values
            sc = np.clip((fy[0] + fy[1] * f.exp_pts.values) / np.where(s_ == 0, np.nan, s_), 0.5, 2.0); ok = f.exp_pts.notna().values & ~np.isnan(sc)
            return np.where(ok, line * (1 + wy * (sc - 1)), line)
        fs = f.season.values <= 2018
        tot = {m: float(np.abs(recon(m * f.base_line.values)[fs] - f.act_yds.values[fs]).mean()) for m in GRID}; m_y = float(min(tot, key=tot.get)); f["yds_line"] = recon(m_y * f.base_line.values)
        if "catch_line" in f:
            cb = f.catch_line.values / PR.MED_CATCH; tc = {m: float(np.abs(m * cb[fs] - f.act_catch.values[fs]).mean()) for m in GRID}; m_c = float(min(tc, key=tc.get)); f["catch_line"] = m_c * cb
        else:
            m_c = None
        r = {"part": f"B props {kind} (factors refit)", "variant": mode, "med": m_y, "med_catch": m_c}
        for w, (a, b) in WIN.items():
            x = f[f.season.between(a, b)]
            r[f"yds_mae_{w}"] = round(float((x.yds_line - x.act_yds).abs().mean()), 3)
            if "catch_line" in x: r[f"catch_mae_{w}"] = round(float((x.catch_line - x.act_catch).abs().mean()), 4)
            r[f"td_ll_{w}"] = round(pll(x.td_line.values, x.act_td.values), 4); r[f"n_{w}"] = int(len(x))
        rows.append(r); print(r, flush=True)
out = "reports/partial_games.csv"; old = pd.read_csv(out) if os.path.exists(out) else pd.DataFrame()
pd.concat([old, pd.DataFrame(rows)], ignore_index=True).drop_duplicates(["part", "variant"], keep="last").to_csv(out, index=False); print("DONE")
