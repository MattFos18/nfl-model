"""Offensive line rating (24 Sep 2026): each lineman rated by his unit in the snaps he played (pressures allowed per
dropback and yards before contact per carry against the league, PFR, in EPA). Test: the team's offensive EPA per
play from its own prior plus the snap-weighted rates of the linemen who played that game, leave-one-season-out in
each window, sweeping the fade. The on/off rating it replaced is not testable this way (it had no per-game rate).
Writes reports/ol_value.csv."""
import numpy as np, pandas as pd
from experiments.def_value import team_prior, OUT, REP
from experiments.def_value_decay import rates

og = pd.read_parquet(OUT / "ol_games.parquet"); og = og[og.season >= 2017]
tg = pd.read_parquet(OUT / "team_games.parquet"); tg = tg[(tg.game_type == "REG") & tg.epa_play.notna() & (tg.season >= 2017)].copy()
tg["prior"] = team_prior(tg, "epa_play")
res = []
for decay, fade in [(None, None), (0.99, 1.0), (0.95, 0.6), (0.95, 0.8), (0.92, 0.8), (0.9, 0.6)]:
    row = {"decay": decay, "fade": fade}
    if decay is not None:
        d = rates(og, decay, fade, 300.0); tsn = d.groupby(["game_id", "team"]).plays.transform("max"); d["L"] = d.r * d.plays / tsn
        x = tg.merge(d.groupby(["game_id", "team"], as_index=False).L.sum(), on=["game_id", "team"])
    else:
        x = tg.assign(L=0.0)
    for window, seasons in [("2019-22", range(2019, 2023)), ("2023-25", range(2023, 2026))]:
        w = x[x.season.isin(seasons)]; err = []
        for s in seasons:
            tr, te = w[w.season != s], w[w.season == s]
            cols = [np.ones(len(tr)), tr.prior] + ([tr.L] if decay else []); colt = [np.ones(len(te)), te.prior] + ([te.L] if decay else [])
            b = np.linalg.lstsq(np.column_stack(cols), tr.epa_play.values, rcond=None)[0]; err.append(te.epa_play.values - np.column_stack(colt) @ b)
        row[window] = round(float(np.sqrt(np.mean(np.concatenate(err) ** 2))), 6)
    res.append(row); print(row, flush=True)
pd.DataFrame(res).to_csv(REP / "ol_value.csv", index=False)
