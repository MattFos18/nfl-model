"""A QB's prior should depend on where he was drafted, not one flat replacement level. Priors by draft slot from
QBs' first 200 dropbacks in 2013 to 2018 (before the tuning window), then the features rebuilt with per-QB priors
and scored on both windows. Output reports/qb_prior.csv."""
import numpy as np, pandas as pd
from nflmodel import ratings as R, model as M
from nflmodel.features import RAW, OUT
from experiments.common import both
tg = pd.read_parquet(OUT / "team_games.parquet"); games = pd.read_parquet(OUT / "games.parquet"); qb = pd.read_parquet(OUT / "qb_games.parquet")
d = pd.read_parquet(RAW / "draft" / "draft_picks.parquet"); d = d[(d.position == "QB") & d.gsis_id.notna()]
pick = dict(zip(d.gsis_id, d.pick))
def bucket(pid):
    p = pick.get(pid)
    if p is None: return "undrafted"
    return "top 10" if p <= 10 else ("round 1" if p <= 32 else ("rounds 2-3" if p <= 100 else "rounds 4-7"))
# early-career EPA per dropback by bucket, first 200 dropbacks, QBs whose first dropback came 2013 to 2018
q = qb.sort_values(["season", "week"]); q["cum"] = q.groupby("qb_id").dropbacks.cumsum(); first = q.groupby("qb_id").season.min()
early = q[q.qb_id.map(first).between(2013, 2018) & (q.cum <= 200)]
tab = early.assign(b=early.qb_id.map(bucket)).groupby("b").agg(dropbacks=("dropbacks", "sum"), epa=("qb_epa", "sum"), qbs=("qb_id", "nunique"))
tab["epa_per_db"] = tab.epa / tab.dropbacks; print(tab.round(3).to_string(), flush=True)
prior_by = {b: float(0.5 * (tab.loc[b, "epa_per_db"]) + 0.5 * (-0.05)) for b in tab.index}   # halfway between the bucket's rate and the flat prior
print("priors", {k: round(v, 3) for k, v in prior_by.items()}, flush=True)
class QBP(R.QBRatings):
    def rating(self, qb_id, season, week):
        key = (qb_id, season, week)
        if key in self._cache: return self._cache[key]
        pr = prior_by.get(bucket(qb_id), self.prior)
        h = self.qb[(self.qb.qb_id == qb_id) & ((self.qb.season < season) | ((self.qb.season == season) & (self.qb.week < week)))]
        if len(h) == 0: r = pr
        else:
            w = self.decay ** np.arange(len(h))[::-1]; db = (h.dropbacks.values * w).sum(); ep = (h.qb_epa.values * w).sum(); r = (ep + self.k * pr) / (db + self.k)
        self._cache[key] = r; return r
rows = []
for name, cls in [("flat prior (current)", R.QBRatings), ("prior by draft slot", QBP)]:
    R.QBRatings = cls
    f = M.with_trends(R.build_features(R.DEFAULT, tg=tg, games=games, qb=qb)); r = both(f)
    rows.append({"variant": name, **{f"{k}_{w}": v for w, d_ in r.items() for k, v in d_.items()}}); print(name, {w: (r[w]["team_mae"], r[w]["margin_mae"], r[w]["ats5"]) for w in r}, flush=True)
pd.DataFrame(rows).to_csv("reports/qb_prior.csv", index=False); print("DONE")
