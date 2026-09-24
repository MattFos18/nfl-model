"""Round twelve (24 Sep 2026): the matchup itself, on the adopted rule (rounds one to eleven), walk-forward, scored on
2019 to 2022 and 2023 to 2025 by the mean miss of the yards line per player-game. Round one already tested the
coverage matchup (his yards against man and against zone, mixed by the defense's man rate) and it lost on both
windows; round ten tested who else is out. New here:

  A. What the defense allows to his position. The rule moves his yards per target a quarter of the way toward what
     the defense allows per target to everyone. Here, toward what it allows to his position group (wide receivers,
     tight ends, backs) over its last 17 games, against the league's rate for that group as of the week; weights 0.25
     and 0.5. Receiving only (rushing is nearly all backs).
  B. Where the defense sends the targets. His targets moved by how much of the defense's targets go to his group
     against the league's share for the group (a defense that funnels throws to tight ends); weights 0.25, 0.5, 1.
  C. His own history against this defense. His yards per touch against this opponent in every earlier game since
     2016, over his overall rate, shrunk with k touches of weight (k = 20, 50, 100, 200). Receiving, rushing, passing.
  D. The best of A, B and C together.

Output reports/props_backtest12.csv. Adopt only a variant better on both windows."""
import numpy as np, pandas as pd, pathlib
from nflmodel import props as PR
src = pathlib.Path(__file__).with_name("props_by_season.py").read_text().split("by_season, by_pos, by_bucket = [], [], []")[0]
ns = {"__name__": "bys"}; exec(compile(src, "bys", "exec"), ns); build = ns["build"]; d = ns["d"]; prev_sums = ns["prev_sums"]; pos_of = ns["pos_of"]; asof_mean = ns["asof_mean"]
WIN = {"2019-22": (2019, 2022), "2023-25": (2023, 2025)}
GRP = lambda p: "RB" if p in ("RB", "FB", "HB") else ("TE" if p == "TE" else "WR")


def mae(f, col):
    return {w: round(float((f[f.season.between(a, b)][col] - f[f.season.between(a, b)].act_yds).abs().mean()), 3) for w, (a, b) in WIN.items()}


def position_frames():
    """Per defense and game: targets and yards allowed to each position group, and the league's as-of rate and share."""
    t = d[d.pass_play & d.receiver_player_id.notna()].copy(); t["grp"] = t.receiver_player_id.map(pos_of).fillna("WR").map(GRP)
    t["n"] = 1
    g = t.groupby(["defteam", "season", "week", "game_id", "grp"]).agg(n=("n", "sum"), y=("yards_gained", "sum")).reset_index()
    games = t[["defteam", "season", "week", "game_id"]].drop_duplicates()
    full = games.assign(k=1).merge(pd.DataFrame({"grp": ["WR", "TE", "RB"], "k": 1}), on="k").drop(columns="k").merge(g, on=["defteam", "season", "week", "game_id", "grp"], how="left").fillna({"n": 0, "y": 0})
    P = prev_sums(full, ["defteam", "grp"], ["n", "y"]).rename(columns={"n": "dp_n", "y": "dp_y"})
    P = P.merge(full[["defteam", "grp", "game_id"]], on=["defteam", "grp", "game_id"])
    tot = P.groupby(["defteam", "game_id"]).dp_n.transform("sum"); P["dp_share"] = P.dp_n / tot.replace(0, np.nan); P["dp_rate"] = np.where(P.dp_n >= 30, P.dp_y / P.dp_n.replace(0, np.nan), np.nan)
    lg = {}
    for gname, x in t.groupby("grp"):
        rate = asof_mean(x, "yards_gained")
        share = asof_mean(t.assign(isg=(t.grp == gname).astype(float)), "isg")
        lg[gname] = (rate, share)
    return P[["defteam", "grp", "game_id", "dp_rate", "dp_share"]], lg


def vs_history(kind):
    """His touches and yards against each defense in every earlier game (all seasons), before the game."""
    if kind == "rec":
        t = d[d.pass_play & d.receiver_player_id.notna()].rename(columns={"receiver_player_id": "pid"})
    elif kind == "rush":
        t = d[d.play_type.eq("run") & d.rusher_player_id.notna()].rename(columns={"rusher_player_id": "pid"})
    else:
        t = d[d.dropback & d.passer_player_id.notna()].assign(yards_gained=lambda x: x.pass_yds).rename(columns={"passer_player_id": "pid"})
    t = t.assign(n=1)
    g = t.groupby(["pid", "defteam", "season", "week", "game_id"]).agg(n=("n", "sum"), y=("yards_gained", "sum")).reset_index().sort_values(["pid", "defteam", "season", "week"])
    g["vs_n"] = g.groupby(["pid", "defteam"]).n.cumsum() - g.n; g["vs_y"] = g.groupby(["pid", "defteam"]).y.cumsum() - g.y
    return g[["pid", "game_id", "vs_n", "vs_y"]]


def main():
    rows = []; P, LG = position_frames()
    for kind in ("rec", "rush", "pass"):
        f, _ = build(kind); f = f.copy()
        base = mae(f, "yds_line"); rows.append({"stat": f"{kind}_yards", "variant": "base", **{f"mae_{w}": v for w, v in base.items()}, "n": len(f)})
        print(kind, "base", base, flush=True)
        # C. his history against this defense
        f = f.merge(vs_history(kind), on=["pid", "game_id"], how="left").fillna({"vs_n": 0, "vs_y": 0})
        own = (f.yds / f.n.replace(0, np.nan))
        ratio = ((f.vs_y / f.vs_n.replace(0, np.nan)) / own).replace([np.inf, -np.inf], np.nan).fillna(1.0).clip(0.2, 3.0)
        best_c = None
        for k in (20, 50, 100, 200):
            col = f"C_k{k}"; f[col] = f.yds_line * (1 + (ratio - 1) * f.vs_n / (f.vs_n + k))
            m = mae(f, col); rows.append({"stat": f"{kind}_yards", "variant": col, **{f"mae_{w}": v for w, v in m.items()}, "n": len(f)}); print(kind, col, m, flush=True)
            if all(m[w] < base[w] for w in WIN) and (best_c is None or m["2019-22"] < best_c[1]["2019-22"]):
                best_c = (col, m)
        if kind != "rec":
            continue
        # A and B: the defense against his position group
        f["grp"] = f.pos.map(GRP)
        f = f.merge(P, on=["defteam", "grp", "game_id"], how="left")
        lg_rate = pd.Series([LG[g_][0].get((int(s), int(w)), np.nan) for g_, s, w in zip(f.grp, f.season, f.week)], index=f.index)
        lg_share = pd.Series([LG[g_][1].get((int(s), int(w)), np.nan) for g_, s, w in zip(f.grp, f.season, f.week)], index=f.index)
        # the rule's overall defense factor, to swap out: 1 + W (d_rate / lg - 1), with lg the league rate as of the week (as build computes it)
        lgp = d[d.pass_play]; lgm = asof_mean(lgp.assign(yards_gained=lgp.yards_gained.fillna(0.0)), "yards_gained")
        lg0 = pd.Series([lgm.get((int(s), int(w)), float(lgp.yards_gained.mean())) for s, w in zip(f.season, f.week)], index=f.index)
        adj0 = np.where(f.d_rate.notna(), 1 + PR.W["rec"] * (f.d_rate / lg0 - 1), 1.0)
        for w_ in (0.25, 0.5):
            col = f"A_pos_rate_w{w_}"
            adjp = np.where(f.dp_rate.notna() & lg_rate.notna(), 1 + w_ * (f.dp_rate / lg_rate - 1), adj0)
            f[col] = f.yds_line / adj0 * adjp
            m = mae(f, col); rows.append({"stat": "rec_yards", "variant": col, **{f"mae_{w}": v for w, v in m.items()}, "n": len(f)}); print("rec", col, m, flush=True)
        for w_ in (0.25, 0.5, 1.0):
            col = f"B_pos_share_w{w_}"
            fac = np.where(f.dp_share.notna() & lg_share.notna() & (lg_share > 0), 1 + w_ * (f.dp_share / lg_share - 1), 1.0)
            f[col] = f.yds_line * np.clip(fac, 0.5, 1.5)
            m = mae(f, col); rows.append({"stat": "rec_yards", "variant": col, **{f"mae_{w}": v for w, v in m.items()}, "n": len(f)}); print("rec", col, m, flush=True)
        # D. together: the best position rate, the best share and the best history
        pick = lambda pre: min((r for r in rows if r["stat"] == "rec_yards" and r["variant"].startswith(pre)), key=lambda r: r["mae_2019-22"])["variant"]
        a_, b_, c_ = pick("A_"), pick("B_"), pick("C_")
        f["D_all"] = f.yds_line * (f[a_] / f.yds_line) * (f[b_] / f.yds_line) * (f[c_] / f.yds_line)
        m = mae(f, "D_all"); rows.append({"stat": "rec_yards", "variant": f"D_all ({a_}, {b_}, {c_})", **{f"mae_{w}": v for w, v in m.items()}, "n": len(f)}); print("rec D", m, flush=True)
    o = pd.DataFrame(rows); o.to_csv("reports/props_backtest12.csv", index=False); print(o.to_string(index=False))


if __name__ == "__main__":
    main()
