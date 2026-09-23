"""Training from 2015 instead of 2013 helped both windows (experiments/history_depth.py), which says the oldest
seasons hurt more than they help. A rolling training window (the most recent N seasons plus the current one) is
the clean version of that idea: it would also apply to 2015 to 2018 evenly. N = 6, 8, 10 against everything since
2013. Output reports/rolling_window.csv."""
import pandas as pd
from nflmodel import model as M
from nflmodel.model import OUT
from experiments.common import WINDOWS, score
f = M.with_trends(pd.read_parquet(OUT / "features_asof.parquet"))
orig = M.walk_forward; rows = []
def run(name, n=None):
    out = {}
    for w, seasons in WINDOWS.items():
        preds = []
        for s in seasons:
            start = 2013 if n is None else max(2013, s - n)
            preds.append(orig(f, [s], 10.0, min_train_season=start, refit="week"))
        out[w] = score(pd.concat(preds, ignore_index=True), seasons)
    rows.append({"variant": name, **{f"{k}_{ww}": v for ww, d in out.items() for k, v in d.items()}}); print(name, {ww: (out[ww]["team_mae"], out[ww]["margin_mae"], out[ww]["ats5"]) for ww in out}, flush=True)
run("everything since 2013 (today)"); run("last 10 seasons", 10); run("last 8 seasons", 8); run("last 6 seasons", 6)
pd.DataFrame(rows).to_csv("reports/rolling_window.csv", index=False); print("DONE")
