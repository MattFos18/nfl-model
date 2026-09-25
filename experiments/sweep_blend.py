"""How the seven models are weighted (25 Sep 2026): the trees' share of the average from none to half, the equations
alone, and each member left out, on the per-game prices in reports/bet_wins_preds.parquet. Writes reports/sweep_blend.csv."""
import numpy as np, pandas as pd
p = pd.read_parquet("reports/bet_wins_preds.parquet"); p = p[p.week <= 17]
LIN = ["sp_base", "sp_success", "sp_split", "sp_plays", "sp_alpha3", "sp_alpha30"]
W = {"2015-18": (2015, 2018), "2019-22": (2019, 2022), "2023-25": (2023, 2025)}
V = {f"trees weight {w:.2f}": (1 - w) * p[LIN].mean(axis=1) + w * p.sp_gbm for w in (0, 1 / 7, 0.2, 0.25, 0.33, 0.5)}
for m in LIN + ["sp_gbm"]:
    rest = [c for c in LIN + ["sp_gbm"] if c != m]; V[f"without {m[3:]}"] = p[rest].mean(axis=1)
V["base + trees only"] = p[["sp_base", "sp_gbm"]].mean(axis=1); V["base + success + trees"] = p[["sp_base", "sp_success", "sp_gbm"]].mean(axis=1)
rows = []
for lab, sp in V.items():
    r = {"variant": lab}
    for w, (a, b) in W.items():
        m = p.season.between(a, b); d = p[m]; s_ = sp[m]; r[f"margin_{w}"] = round(float((s_ - d.result).abs().mean()), 4)
        x = d.spread_line.notna(); e = (s_ - d.spread_line)[x]; dd = d[x]; k = e.abs() >= 4; c = (dd.result - dd.spread_line)[k] * np.sign(e[k])
        r[f"4+_{w}"] = f"{int((c > 0).sum())}-{int((c < 0).sum())}"
    rows.append(r)
o = pd.DataFrame(rows); o.to_csv("reports/sweep_blend.csv", index=False); pd.set_option("display.width", 250); print(o.to_string(index=False))
