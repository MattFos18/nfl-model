"""Kickoff-hour weather for the backtest (data/weather/archive_kickoff.csv from the Open-Meteo archive) in place of
the schedule's game-day temperature and wind: rebuild wind_out, cold and rain from the archive readings for every
game that has them, refit, both windows. Adopt only if both windows improve. Output reports/weather_kickoff.csv."""
import numpy as np, pandas as pd
from nflmodel import model as M
from nflmodel.model import OUT
from nflmodel.features import ROOT
from experiments.common import both
arc = pd.read_csv(ROOT / "data" / "weather" / "archive_kickoff.csv")
print("archive rows", len(arc), "seasons", sorted(arc.season.unique()), flush=True)
f0 = M.with_trends(pd.read_parquet(OUT / "features_asof.parquet"))
a = arc.set_index("game_id")
f = f0.copy(); has = f.game_id.isin(a.index) & (f.dome != 1)
f.loc[has, "temp"] = f.loc[has, "game_id"].map(a.temp).values; f.loc[has, "wind"] = f.loc[has, "game_id"].map(a.wind).values
f.loc[has, "rain"] = (f.loc[has, "game_id"].map(a.precip).fillna(0).values > 0.0).astype(float)
print("games replaced", int(has.sum()), "of", len(f), flush=True)
rows = []
for name, frame in [("schedule readings (today)", f0), ("kickoff-hour archive readings", f)]:
    r = both(frame); rows.append({"variant": name, **{f"{k}_{w}": v for w, d in r.items() for k, v in d.items()}}); print(name, {w: (r[w]["team_mae"], r[w]["margin_mae"], r[w]["ats5"]) for w in r}, flush=True)
pd.DataFrame(rows).to_csv("reports/weather_kickoff.csv", index=False); print("DONE")
