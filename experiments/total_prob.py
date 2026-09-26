"""One probability for a game total (26 Sep 2026). The card showed two chances for the same event: the totals flag's
chip read the model's own skewed-residual chance (pred_v3.p_over_emp: the training games' misses shifted to this
game's total) and the cover bar read the calibrated chance (picks.calibration: a logistic fit of "the model's side
won" on the capped total edge, regular season, seasons before this one). Which one to keep is scored here on the
three backtest windows, walk-forward (every number for a game made only from earlier seasons):

  log loss and Brier of P(over), pushes left out;
  calibration of the side taken: the average stated chance of the side each rule favours against how often it won.

The calibrated fit needs earlier seasons: production starts it in 2019 (so 2020 on); for 2016-18 it starts in 2015,
the first priced season. p_over_emp is scored on the same games. Also the under flag (an under at 55%+): its record
on both probabilities at the same 55% cut.

Output reports/total_prob.csv."""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from nflmodel import backtest as B, picks as P
from nflmodel.model import OUT
REP = Path(__file__).resolve().parent.parent / "reports"


def cal_fit(d: pd.DataFrame):
    from sklearn.linear_model import LogisticRegression
    edge = d.model_total - d.total_line; res = np.sign(d.home_score + d.away_score - d.total_line)
    ok = edge.notna() & (res != 0) & res.notna(); won = (np.sign(edge[ok]) == res[ok]).astype(int)
    x = np.minimum(np.abs(edge[ok].values), 7.0)[:, None]
    m = LogisticRegression(C=10.0).fit(x, won); return float(m.intercept_[0]), float(m.coef_[0][0])


def main():
    games = pd.read_parquet(OUT / "games.parquet"); pred = pd.read_parquet(OUT / "pred_v3.parquet")
    d = B.join(pred, games); d = d[(d.game_type == "REG") & d.total_line.notna() & d.home_score.notna()].copy()
    d["over"] = np.sign(d.home_score + d.away_score - d.total_line); d = d[d.over != 0]; d["y"] = (d.over > 0).astype(float)
    d["edge"] = d.model_total - d.total_line
    d["p_cal"] = np.nan
    for s in sorted(d.season.unique()):
        start = 2019 if s >= 2020 else 2015
        tr = d[(d.season >= start) & (d.season < s)]
        if len(tr) < 200:
            continue
        cal = cal_fit(tr); m = d.season == s
        d.loc[m, "p_cal"] = [P.cal_p(cal, e) if e > 0 else 1 - P.cal_p(cal, e) for e in d.loc[m, "edge"]]
    rows = []
    for w, (a, b) in {"2016-18": (2016, 2018), "2020-22": (2020, 2022), "2023-25": (2023, 2025)}.items():
        x = d[d.season.between(a, b) & d.p_cal.notna() & d.p_over_emp.notna()]
        for name, col in (("p_over_emp (model, skewed residuals)", "p_over_emp"), ("p_over_cal (calibrated on the edge)", "p_cal")):
            p = x[col].clip(1e-6, 1 - 1e-6); y = x.y
            side_p = np.maximum(p, 1 - p); side_won = np.where(p >= 0.5, y, 1 - y)
            und = (1 - p) >= P.TOTAL_SHADOW["prob"]; uw = int(((y == 0) & und & (x.week < 18)).sum()); ul = int(((y == 1) & und & (x.week < 18)).sum())
            rows.append({"window": w, "prob": name, "games": int(len(x)), "log_loss": round(float(-(y * np.log(p) + (1 - y) * np.log(1 - p)).mean()), 5),
                         "brier": round(float(((p - y) ** 2).mean()), 5), "side_stated": round(float(side_p.mean()), 4), "side_won": round(float(side_won.mean()), 4),
                         "side_gap": round(float(side_won.mean() - side_p.mean()), 4), "under55_record": f"{uw}-{ul}"})
    r = pd.DataFrame(rows); r.to_csv(REP / "total_prob.csv", index=False); print(r.to_string(index=False))


if __name__ == "__main__":
    main()
