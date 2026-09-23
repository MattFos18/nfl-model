"""Does more training history help? The regression trains on every played game from 2013. Snap counts and the player
model start in 2012, so seasons before that cannot be added without missing inputs; instead train from 2015 and
2017 and see how much the held-out miss loses. If it loses, more history helps and 2009 to 2012 would be worth
pulling with the inputs that exist there. Output reports/history_depth.csv."""
import pandas as pd
from nflmodel import model as M
from nflmodel.model import OUT
from experiments.common import both, WINDOWS, score
f = M.with_trends(pd.read_parquet(OUT / "features_asof.parquet"))
rows = []
for start in [2013, 2015, 2017]:
    r = {name: score(M.walk_forward(f, seasons, 10.0, min_train_season=start, refit="week"), seasons) for name, seasons in WINDOWS.items()}
    rows.append({"variant": f"train from {start}" + (" (today)" if start == 2013 else ""), **{f"{k}_{w}": v for w, d in r.items() for k, v in d.items()}})
    print(start, {w: (r[w]["team_mae"], r[w]["margin_mae"], r[w]["ats5"]) for w in r}, flush=True)
pd.DataFrame(rows).to_csv("reports/history_depth.csv", index=False); print("DONE")
