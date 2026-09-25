"""Round thirteen (25 Sep 2026): who is playing and how his role is moving, on the adopted rule (rounds one to twelve),
walk-forward, scored on 2019 to 2022 and 2023 to 2025 by the mean miss of the yards line per player-game. Our own
data only (no market).

  A. This week's injury report for a player who plays: Questionable, and a limited or no practice day on the final
     report. Each group's factor = (its actual / line) over (unlisted players' actual / line), fitted on 2017-18.
  B. Snap momentum: his offensive snap share over his last 3 games against his last 10 (nflverse snap counts), the
     line moved w of the way (w = 0.25, 0.5, 1).
  C. Role momentum: his share of the team's targets (carries) over his last 3 games against the rule's decayed share,
     the volume moved w of the way (w = 0.25, 0.5).
  D. The best of each together.

Output reports/props_backtest13.csv. Adopt only a variant better on both windows."""
import numpy as np, pandas as pd, pathlib
from nflmodel import props as PR
from nflmodel.features import RAW, OUT
src = pathlib.Path(__file__).with_name("props_by_season.py").read_text().split("by_season, by_pos, by_bucket = [], [], []")[0]
ns = {"__name__": "bys"}; exec(compile(src, "bys", "exec"), ns); build = ns["build"]; d = ns["d"]
WIN = {"2019-22": (2019, 2022), "2023-25": (2023, 2025)}; FIT = (2017, 2018)


def mae(f, col):
    return {w: round(float((f[f.season.between(a, b)][col] - f[f.season.between(a, b)].act_yds).abs().mean()), 3) for w, (a, b) in WIN.items()}


def report():
    fr = []
    for s in range(2016, 2027):
        p = RAW / "injuries" / f"injuries_{s}.parquet"
        if p.exists():
            x = pd.read_parquet(p); col = "season_type" if "season_type" in x.columns else "game_type"
            fr.append(x[x[col] == "REG"][["season", "week", "gsis_id", "report_status", "practice_status"]])
    x = pd.concat(fr).dropna(subset=["gsis_id"]).drop_duplicates(["season", "week", "gsis_id"], keep="last")
    return x.rename(columns={"gsis_id": "pid"})


def snaps():
    e = pd.read_parquet(OUT / "snap_exposure.parquet", columns=["player_id", "game_id", "season", "week", "off_pct"]).rename(columns={"player_id": "pid"}).dropna(subset=["off_pct"])
    e = e[e.off_pct > 0].sort_values(["pid", "season", "week"])
    g = e.groupby("pid").off_pct
    e["s3"] = g.transform(lambda v: v.shift(1).rolling(3, min_periods=2).mean()); e["s10"] = g.transform(lambda v: v.shift(1).rolling(10, min_periods=4).mean())
    return e[["pid", "game_id", "s3", "s10"]]


def share3(kind):
    if kind == "rec":
        t = d[d.pass_play & d.receiver_player_id.notna()].rename(columns={"receiver_player_id": "pid"}); tm = d[d.pass_play]
    else:
        t = d[d.play_type.eq("run") & d.rusher_player_id.notna()].rename(columns={"rusher_player_id": "pid"}); tm = d[d.play_type.eq("run")]
    pn = t.groupby(["pid", "posteam", "season", "week", "game_id"]).size().rename("n").reset_index()
    tn = tm.groupby(["posteam", "game_id"]).size().rename("tn").reset_index()
    pn = pn.merge(tn, on=["posteam", "game_id"]).sort_values(["pid", "season", "week"])
    g = pn.groupby("pid")
    pn["n3"] = g.n.transform(lambda v: v.shift(1).rolling(3, min_periods=2).sum()); pn["t3"] = g.tn.transform(lambda v: v.shift(1).rolling(3, min_periods=2).sum())
    pn["sh3"] = pn.n3 / pn.t3.replace(0, np.nan)
    return pn[["pid", "game_id", "sh3"]]


def main():
    rows = []; REP = report(); SN = snaps()
    for kind in ("rec", "rush", "pass"):
        f, _ = build(kind); f = f.copy()
        base = mae(f, "yds_line"); rows.append({"stat": f"{kind}_yards", "variant": "base", **{f"mae_{w}": v for w, v in base.items()}}); print(kind, "base", base, flush=True)
        # A. the injury report for players who played
        f = f.merge(REP, on=["pid", "season", "week"], how="left")
        f["grp"] = np.select([f.report_status.eq("Questionable"), f.practice_status.fillna("").str.startswith("Did Not"), f.practice_status.fillna("").str.startswith("Limited")], ["Q", "DNP", "LIM"], "none")
        fit = f[f.season.between(*FIT)]; r0 = fit[fit.grp == "none"].act_yds.sum() / fit[fit.grp == "none"].yds_line.sum()
        fac = {g_: (x.act_yds.sum() / x.yds_line.sum()) / r0 for g_, x in fit.groupby("grp") if g_ != "none" and len(x) >= 50}
        f["A_injury"] = f.yds_line * f.grp.map(fac).fillna(1.0)
        m = mae(f, "A_injury"); rows.append({"stat": f"{kind}_yards", "variant": "A_injury " + ", ".join(f"{k} {v:.3f}" for k, v in fac.items()), **{f"mae_{w}": v for w, v in m.items()}}); print(kind, "A", fac, m, flush=True)
        # B. snap momentum
        f = f.merge(SN, on=["pid", "game_id"], how="left"); rr = (f.s3 / f.s10).replace([np.inf, -np.inf], np.nan).fillna(1.0).clip(0.4, 2.0)
        for w in (0.25, 0.5, 1.0):
            col = f"B_snap_w{w}"; f[col] = f.yds_line * (1 + w * (rr - 1))
            m = mae(f, col); rows.append({"stat": f"{kind}_yards", "variant": col, **{f"mae_{w_}": v for w_, v in m.items()}}); print(kind, col, m, flush=True)
        if kind != "pass":
            # C. role momentum
            f = f.merge(share3(kind), on=["pid", "game_id"], how="left")
            sh85 = f.n_85 / f.team_n_85.replace(0, np.nan); rs = (f.sh3 / sh85).replace([np.inf, -np.inf], np.nan).fillna(1.0).clip(0.4, 2.5)
            for w in (0.25, 0.5):
                col = f"C_role_w{w}"; f[col] = f.yds_line * (1 + w * (rs - 1))
                m = mae(f, col); rows.append({"stat": f"{kind}_yards", "variant": col, **{f"mae_{w_}": v for w_, v in m.items()}}); print(kind, col, m, flush=True)
        # D. the best of each on 2019-22, together
        cand = [r for r in rows if r["stat"] == f"{kind}_yards" and r["variant"] != "base"]
        best = {}
        for r in cand:
            key = r["variant"][0]; col = r["variant"].split(" ")[0]
            if r["mae_2019-22"] < base["2019-22"] and (key not in best or r["mae_2019-22"] < best[key][1]):
                best[key] = (col, r["mae_2019-22"])
        if len(best) >= 2:
            f["D_all"] = f.yds_line * np.prod([f[c] / f.yds_line for c, _ in best.values()], axis=0)
            m = mae(f, "D_all"); rows.append({"stat": f"{kind}_yards", "variant": "D_all (" + ", ".join(c for c, _ in best.values()) + ")", **{f"mae_{w}": v for w, v in m.items()}}); print(kind, "D", m, flush=True)
    o = pd.DataFrame(rows); o.to_csv("reports/props_backtest13.csv", index=False); print(o.to_string(index=False))


if __name__ == "__main__":
    main()
