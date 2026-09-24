"""Which seasons should the cover-odds calibration learn from? (23 Sep 2026). The cards' cover odds come from a
logistic fit of "the model's side covered" on |edge| (capped at 7), over regular-season games from 2019 to the
season before (picks.calibration). The start year was a choice. Here each start (2015, 2016, 2017, 2019) and a
rolling window (the last 3, 4, 5 seasons) is fit walk-forward and scored on the season after, by log loss and Brier
on every game with a line, and on the flagged games alone, 2020-22 and 2023-25 (2019 has no fit from a 2019 start).
Also the stated odds at edges of 4, 5 and 6 for 2026 under each. A change must score better on both windows on
every game and on the flagged games alone. Output reports/calibration_start.csv."""
import sys
import numpy as np, pandas as pd
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from sklearn.linear_model import LogisticRegression
from nflmodel import backtest as B, picks as P
from nflmodel.model import OUT, REP

games = pd.read_parquet(OUT / "games.parquet"); pred = pd.read_parquet(OUT / "pred_v3.parquet")
d = B.join(pred, games); d = d[(d.game_type == "REG") & d.spread_line.notna() & d.home_score.notna()].copy()
d["edge"] = d.model_spread - d.spread_line; d["cm"] = d.home_score - d.away_score - d.spread_line
d = d[d.cm != 0]; d["won"] = (((d.edge > 0) & (d.cm > 0)) | ((d.edge < 0) & (d.cm < 0))).astype(int); d["x"] = np.minimum(d.edge.abs(), 7.0)
d["flag"] = P.rule_mask(d, P.SPREAD_EDGE)
VAR = {"from 2015": ("start", 2015), "from 2016": ("start", 2016), "from 2017": ("start", 2017), "from 2019 (today)": ("start", 2019), "last 3 seasons": ("roll", 3), "last 4 seasons": ("roll", 4), "last 5 seasons": ("roll", 5)}
WIN = {"2020-22": (2020, 2022), "2023-25": (2023, 2025)}


def fit(tr):
    m = LogisticRegression(C=10.0).fit(tr[["x"]].values, tr.won.values); return float(m.intercept_[0]), float(m.coef_[0][0])


rows = []
for name, (kind, v) in VAR.items():
    preds = []
    for s in range(2020, 2027):
        tr = d[(d.season < s) & ((d.season >= v) if kind == "start" else (d.season >= s - v))]
        a, b = fit(tr)
        te = d[d.season == s].copy(); te["p"] = 1 / (1 + np.exp(-(a + b * te.x))); preds.append(te)
        if s == 2026:
            r26 = {f"odds_at_{e}": round(1 / (1 + np.exp(-(a + b * e))), 4) for e in (4, 5, 6)}
    pr = pd.concat(preds); r = {"variant": name, **r26}
    for w, (lo, hi) in WIN.items():
        x = pr[pr.season.between(lo, hi)]; fl = x[x.flag]
        ll = lambda y: float(-np.mean(y.won * np.log(y.p) + (1 - y.won) * np.log(1 - y.p)))
        r[f"logloss_all_{w}"] = round(ll(x), 5); r[f"brier_all_{w}"] = round(float(((x.p - x.won) ** 2).mean()), 5)
        r[f"logloss_flags_{w}"] = round(ll(fl), 5); r[f"flags_said_{w}"] = round(float(fl.p.mean()), 4); r[f"flags_won_{w}"] = round(float(fl.won.mean()), 4); r[f"flags_{w}"] = int(len(fl))
    rows.append(r)
R = pd.DataFrame(rows); base = R[R.variant == "from 2019 (today)"].iloc[0]
# a change must score better on both windows on every game AND on the flagged games (the stakes are sized on the flags)
R["verdict"] = ["today" if r.variant == "from 2019 (today)" else ("better on both windows, all games and flags" if all(r[f"logloss_{k}_{w}"] < base[f"logloss_{k}_{w}"] for w in WIN for k in ("all", "flags")) else ("all games better, flags worse" if all(r[f"logloss_all_{w}"] < base[f"logloss_all_{w}"] for w in WIN) else "not better on both")) for _, r in R.iterrows()]
R.to_csv(REP / "calibration_start.csv", index=False); print(R.to_string(index=False))
