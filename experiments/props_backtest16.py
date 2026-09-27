"""Round sixteen (27 Sep 2026): defensive tackles by tier. The round-7 rule turns the mean into the line with one flat
median factor (DEF_MED 0.90). A count's median sits further below its mean the smaller the mean is (a 4-tackle backup
is skewed, a 10-tackle linebacker nearly symmetric), so one factor over-shrinks the high-volume players and
under-shrinks the low-volume ones. Here: the signed bias (line minus actual) and the absolute miss by tier of the
projected mean for the adopted rule (tk_85gs_med), then a median factor that depends on the mean (per tier, and a
linear form a + b x mean clipped to [0.8, 1.0]) fitted on 2016 to 2018, scored on both windows by absolute error per
defender-game. Kicking points and field goals: the bias by tier only (a linear fit, not a median factor). Output
reports/props_backtest16.csv (variants) and reports/props_backtest16_tiers.csv (tier tables)."""
import numpy as np, pandas as pd, pathlib
src = pathlib.Path(__file__).with_name("props_backtest7.py").read_text().split("rows = []")[0]
ns = {"__name__": "bt7"}; exec(compile(src, "bt7", "exec"), ns)
f, WIN, fit_grid, PR = ns["f"], ns["WIN"], ns["fit_grid"], ns["PR"]
share_85, team_tk_per_play, vol_gs = ns["share_85"], ns["team_tk_per_play"], ns["vol_gs"]
f["mean"] = share_85 * team_tk_per_play * vol_gs
f["cur"] = PR.DEF_MED * f["mean"]                       # the adopted rule
EDGES = [0, 3, 5, 7, 9, 11, 99]
f["tier"] = pd.cut(f["mean"], EDGES, right=False)
rows, tiers = [], []


def ev(col):
    out = {}
    for w, (a, b) in WIN.items():
        x = f[f.season.between(a, b)]; out[f"mae_{w}"] = round(float((x[col] - x.act_tk).abs().mean()), 4); out[f"bias_{w}"] = round(float((x[col] - x.act_tk).mean()), 3); out[f"n_{w}"] = int(len(x))
    return out


def tier_table(col, name):
    for w, (a, b) in WIN.items():
        x = f[f.season.between(a, b)]
        for t, g in x.groupby("tier", observed=True):
            tiers.append({"variant": name, "window": w, "tier": str(t), "n": int(len(g)), "mean_line": round(float(g[col].mean()), 2), "mean_actual": round(float(g.act_tk.mean()), 2), "median_actual": float(g.act_tk.median()), "bias": round(float((g[col] - g.act_tk).mean()), 3), "mae": round(float((g[col] - g.act_tk).abs().mean()), 3)})


# 1. the adopted rule, by tier
tier_table("cur", "cur"); rows.append({"stat": "def_tackles", "variant": "cur (flat 0.90)", **ev("cur")})
# 2. a median factor per tier, fitted on 2016 to 2018 (the factor that minimises the absolute miss within the tier)
fit = f[f.season <= 2018]; fac = {}
for t, g in fit.groupby("tier", observed=True):
    grid = np.arange(0.70, 1.11, 0.01); errs = [float((c * g["mean"] - g.act_tk).abs().mean()) for c in grid]; fac[t] = float(grid[int(np.argmin(errs))])
f["tiered"] = f["mean"] * f.tier.map(fac).astype(float)
tier_table("tiered", "tiered"); rows.append({"stat": "def_tackles", "variant": "median factor per tier", **ev("tiered"), "fitted": {str(k): v for k, v in fac.items()}})
# 3. a linear factor in the mean: a + b x mean, clipped to [0.8, 1.0], fitted on 2016 to 2018 over a small grid
best, best_err = None, 1e9
for a in np.arange(0.70, 0.96, 0.02):
    for b in np.arange(0.0, 0.041, 0.005):
        c = np.clip(a + b * fit["mean"], 0.8, 1.0); err = float((c * fit["mean"] - fit.act_tk).abs().mean())
        if err < best_err: best, best_err = (round(float(a), 2), round(float(b), 3)), err
f["linear"] = f["mean"] * np.clip(best[0] + best[1] * f["mean"], 0.8, 1.0)
tier_table("linear", "linear"); rows.append({"stat": "def_tackles", "variant": "linear factor a + b x mean, clipped 0.8 to 1.0", **ev("linear"), "fitted": f"a {best[0]}, b {best[1]}"})
# 4. the mean itself (no factor) and a rounding to the half point of the linear one (the books post .5 lines)
rows.append({"stat": "def_tackles", "variant": "mean (factor 1)", **ev("mean")})
# kickers: the adopted round-9 rule (k_blend_team, g_blend_team), signed bias by tier of the line
ks = pathlib.Path(__file__).with_name("props_backtest9.py").read_text().split('for c in ["g_avg"')[0]
kn = {"__name__": "bt9"}; exec(compile(ks, "bt9", "exec"), kn); kf = kn["f"]
for col, act, name, edges in (("k_blend_team", "act_pts", "kick_points", [0, 6, 8, 10, 99]), ("g_blend_team", "act_fgm", "field_goals", [0, 1.5, 2.0, 2.5, 99])):
    kf["tier"] = pd.cut(kf[col], edges, right=False)
    for w, (a, b) in WIN.items():
        x = kf[kf.season.between(a, b)]
        for t, g in x.groupby("tier", observed=True):
            tiers.append({"variant": name, "window": w, "tier": str(t), "n": int(len(g)), "mean_line": round(float(g[col].mean()), 2), "mean_actual": round(float(g[act].mean()), 2), "median_actual": float(g[act].median()), "bias": round(float((g[col] - g[act]).mean()), 3), "mae": round(float((g[col] - g[act]).abs().mean()), 3)})
S = pd.DataFrame(rows); T = pd.DataFrame(tiers)
S.to_csv("reports/props_backtest16.csv", index=False); T.to_csv("reports/props_backtest16_tiers.csv", index=False)
print(S.to_string()); print(T.to_string()); print("DONE")
