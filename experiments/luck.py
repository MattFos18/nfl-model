"""Turnover luck: EPA per play carries every interception and fumble at full weight, and turnovers are the noisiest
part of football. Rebuild the offense/defense EPA ratings on (a) per-play EPA clipped to [-4, +4] and (b) EPA with
turnover plays replaced by the league-average EPA of a turnover-free play of that type, keep everything else, and
score both windows. Also: the third window at the new 4-point flag. Output reports/luck.csv."""
import numpy as np, pandas as pd, pyarrow.parquet as pq
from nflmodel import ratings as R, model as M, backtest as B
from nflmodel.features import RAW, OUT, TEAM_FIX
from experiments.common import both
tg = pd.read_parquet(OUT / "team_games.parquet"); games = pd.read_parquet(OUT / "games.parquet"); qb = pd.read_parquet(OUT / "qb_games.parquet")
frames = []
for s in range(2012, 2027):
    f = RAW / "pbp" / f"play_by_play_{s}.parquet"
    if f.exists(): frames.append(pd.read_parquet(f, columns=["game_id", "posteam", "play_type", "epa", "interception", "fumble_lost"]))
p = pd.concat(frames, ignore_index=True); p = p[p.play_type.isin(["pass", "run"]) & p.posteam.notna()].copy(); p["posteam"] = p.posteam.replace(TEAM_FIX)
p["epa"] = pd.to_numeric(p.epa, errors="coerce"); p = p[p.epa.notna()]
to = (pd.to_numeric(p.interception, errors="coerce").fillna(0) == 1) | (pd.to_numeric(p.fumble_lost, errors="coerce").fillna(0) == 1)
p["epa_clip"] = p.epa.clip(-4, 4)
mean_noto = p[~to].groupby("play_type").epa.mean(); p["epa_noto"] = np.where(to, p.play_type.map(mean_noto), p.epa)
agg = p.groupby(["game_id", "posteam"]).agg(epa_clip=("epa_clip", "mean"), epa_noto=("epa_noto", "mean")).reset_index().rename(columns={"posteam": "team"})
tg2 = tg.merge(agg, on=["game_id", "team"], how="left")
print("turnover plays share", round(float(to.mean()), 4), "corr epa vs clipped", round(float(tg2[["epa_play", "epa_clip"]].corr().iloc[0, 1]), 3), flush=True)
rows = []
def run(name, col):
    t = tg2.copy()
    if col: t["epa_play"] = t[col].fillna(t.epa_play)
    f = M.with_trends(R.build_features(R.DEFAULT, tg=t, games=games, qb=qb)); r = both(f)
    rows.append({"variant": name, **{f"{k}_{w}": v for w, d in r.items() for k, v in d.items()}}); print(name, {w: (r[w]["team_mae"], r[w]["margin_mae"], r[w]["ats5"]) for w in r}, flush=True)
    return f
f0 = run("current EPA per play", None); run("EPA clipped to +-4 per play", "epa_clip"); run("turnover plays at the average play's EPA", "epa_noto")
# third window at the 4-point flag with the current model
p3 = M.walk_forward(f0, range(2015, 2019)); d = B.join(p3, games); d = d[(d.game_type == "REG") & d.season.isin(range(2015, 2019)) & (d.week < 18) & d.spread_line.notna() & d.home_score.notna()]
e = d.model_spread - d.spread_line; res = np.sign(d.home_score - d.away_score - d.spread_line)
for cut in [4, 4.5, 5]:
    m = (np.abs(e) >= cut) & (res != 0); w = int((np.sign(e[m]) == res[m]).sum()); l = int(m.sum() - w); print("third window cut", cut, f"{w}-{l}", round(w / (w + l), 3) if w + l else None, flush=True)
    rows.append({"variant": f"third window 2015-18 at cut {cut}", "ats": f"{w}-{l}", "pct": round(w / (w + l), 3) if w + l else None})
pd.DataFrame(rows).to_csv("reports/luck.csv", index=False); print("DONE")
