"""Defender value recency (24 Sep 2026): how fast old games fade. The value decayed 0.99 a game with no season fade,
so a game two seasons back still counted about 70% (Aaron Donald's prime carried him; L'Jarius Sneed ranked on
2022-23). Same team-level test as experiments/def_value.py (team defensive EPA per play from the team's prior plus
the lineup's rates, leave-one-season-out in each window), sweeping the per-game decay, a per-season fade (like the
QB rating's 0.8) and the shrinkage K. Writes reports/def_value_decay.csv."""
import numpy as np, pandas as pd
from experiments.def_value import team_prior, OUT, REP

def rates(d, decay, fade, k):
    d = d.sort_values(["season", "week"]).reset_index(drop=True); out = np.zeros(len(d))
    for _, idx in d.groupby("player_id").indices.items():
        sn = d.plays.values[idx]; v = d.epa.values[idx]; se = d.season.values[idx]; num = den = 0.0; last = None
        for j, i in enumerate(idx):
            if last is not None and se[j] != last:
                num *= fade; den *= fade
            out[i] = num / (den + k)
            den = den * decay + sn[j]; num = num * decay + v[j]; last = se[j]
    return d.assign(r=out)

if __name__ == "__main__":
    dg = pd.read_parquet(OUT / "defender_games.parquet"); dg = dg[dg.season >= 2017]
    tg = pd.read_parquet(OUT / "team_games.parquet"); tg = tg[(tg.game_type == "REG") & tg.def_epa_play.notna() & (tg.season >= 2017)].copy()
    tg["prior"] = team_prior(tg, "def_epa_play")
    res = []
    for decay in [0.99, 0.97, 0.95, 0.92]:
        for fade in [1.0, 0.8, 0.6]:
            for k in [150.0, 300.0]:
                d = rates(dg, decay, fade, k); tsn = d.groupby(["game_id", "team"]).plays.transform("max"); d["L"] = d.r * d.plays / tsn
                x = tg.merge(d.groupby(["game_id", "team"], as_index=False).L.sum(), on=["game_id", "team"])
                row = {"decay": decay, "fade": fade, "k": k}
                for window, seasons in [("2019-22", range(2019, 2023)), ("2023-25", range(2023, 2026))]:
                    w = x[x.season.isin(seasons)]; err = []
                    for s in seasons:
                        tr, te = w[w.season != s], w[w.season == s]
                        b = np.linalg.lstsq(np.column_stack([np.ones(len(tr)), tr.prior, tr.L]), tr.def_epa_play.values, rcond=None)[0]
                        err.append(te.def_epa_play.values - np.column_stack([np.ones(len(te)), te.prior, te.L]) @ b)
                    row[window] = round(float(np.sqrt(np.mean(np.concatenate(err) ** 2))), 6)
                res.append(row); print(row, flush=True)
    pd.DataFrame(res).to_csv(REP / "def_value_decay.csv", index=False)
