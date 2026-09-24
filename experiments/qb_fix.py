"""QB rating audit (24 Sep 2026, Matt: "how is Dart supposedly worse than Jameis"). Two faults found in the rating:
  1. scrambles were dropped: qb_games counted dropbacks with passer_player_id, which nflverse leaves empty on every
     scramble (the scrambler is in passer_id). Scrambles average about +0.5 EPA, so mobile QBs were rated low.
  2. age was counted in the QB's own games, so a backup's games from years ago kept most of their weight (Winston's
     2015 to 2019 starts still counted heavily in 2026). Variant: age in league weeks elapsed.
Also tested on top: designed QB runs added, the shrinkage (k) and the decay per week re-swept.
Both windows, weekly refit. Output reports/qb_fix.csv."""
import os, numpy as np, pandas as pd
from nflmodel import ratings as R, model as M
from nflmodel.features import RAW, OUT
from experiments.common import both

tg = pd.read_parquet(OUT / "team_games.parquet"); games = pd.read_parquet(OUT / "games.parquet"); qb0 = pd.read_parquet(OUT / "qb_games.parquet")
fr = []
for s in range(2012, 2027):
    f = RAW / "pbp" / f"play_by_play_{s}.parquet"
    if f.exists():
        fr.append(pd.read_parquet(f, columns=["game_id", "season", "week", "posteam", "qb_dropback", "passer_id", "passer_player_id", "rusher_id", "qb_scramble", "play_type", "qb_epa", "epa"]))
p = pd.concat(fr)
db = p[p.posteam.notna() & (pd.to_numeric(p.qb_dropback, errors="coerce") == 1) & p.passer_id.notna()]
qb1 = db.groupby(["game_id", "season", "week", "posteam", "passer_id"]).agg(dropbacks=("qb_epa", "size"), qb_epa=("qb_epa", "sum")).reset_index().rename(columns={"posteam": "team", "passer_id": "qb_id"})
runs = p[p.posteam.notna() & (p.play_type == "run") & (pd.to_numeric(p.qb_dropback, errors="coerce") != 1) & p.rusher_id.notna()]
runs = runs[runs.rusher_id.isin(set(qb1.qb_id))]
rq = runs.groupby(["game_id", "season", "week", "posteam", "rusher_id"]).agg(n=("epa", "size"), e=("epa", "sum")).reset_index().rename(columns={"posteam": "team", "rusher_id": "qb_id"})
qb2 = qb1.merge(rq, on=["game_id", "season", "week", "team", "qb_id"], how="left").fillna({"n": 0, "e": 0})
qb2 = qb2.assign(dropbacks=qb2.dropbacks + qb2.n, qb_epa=qb2.qb_epa + qb2.e).drop(columns=["n", "e"])
print("dropbacks: current", int(qb0.dropbacks.sum()), "with scrambles", int(qb1.dropbacks.sum()), "plus designed runs", int(qb2.dropbacks.sum()), flush=True)

WK = {sw: i for i, sw in enumerate(sorted(set(zip(games.season, games.week))))}


class WeekAged(R.QBRatings):
    """Same shrinkage, but a game's weight is decay ** (league weeks since it was played)."""
    def __init__(self, qb, k, decay, prior_epa=-0.12):
        super().__init__(qb, k, decay, prior_epa)
        self.qb = self.qb.assign(ix=[WK[(s, w)] for s, w in zip(self.qb.season, self.qb.week)])

    def rating(self, qb_id, season, week):
        key = (qb_id, season, week)
        if key in self._cache:
            return self._cache[key]
        now = WK[(season, week)]; h = self.qb[(self.qb.qb_id == qb_id) & (self.qb.ix < now)]
        if len(h) == 0:
            r = self.prior
        else:
            w = self.decay ** (now - h.ix.values)
            r = ((h.qb_epa.values * w).sum() + self.k * self.prior) / ((h.dropbacks.values * w).sum() + self.k)
        self._cache[key] = r
        return r


class HybridAged(WeekAged):
    """Age = the QB's own games since + LAM x the other league weeks since (weeks he sat, the offseason): LAM 0 is the
    current rule, LAM 1 is pure league weeks. The middle ground the published QB models use (nfelo, 538: per start in
    season, plus regression across the offseason; PFF: calendar time)."""
    LAM = 0.5

    def rating(self, qb_id, season, week):
        key = (qb_id, season, week)
        if key in self._cache:
            return self._cache[key]
        now = WK[(season, week)]; h = self.qb[(self.qb.qb_id == qb_id) & (self.qb.ix < now)]
        if len(h) == 0:
            r = self.prior
        else:
            own = np.arange(len(h))[::-1]; wks = now - h.ix.values - 1
            age = own + self.LAM * np.maximum(wks - own, 0)
            w = self.decay ** age
            r = ((h.qb_epa.values * w).sum() + self.k * self.prior) / ((h.dropbacks.values * w).sum() + self.k)
        self._cache[key] = r
        return r


class Hybrid25(HybridAged): LAM = 0.25


class Hybrid10(HybridAged): LAM = 0.10


class SeasonFade(R.QBRatings):
    """The per-game decay as now, times SF per season between the game and now (PFF's published QB model fades by
    calendar time, about 0.7 a year), so a backup's prime years fade even though he has barely played since."""
    SF = 0.8

    def rating(self, qb_id, season, week):
        key = (qb_id, season, week)
        if key in self._cache:
            return self._cache[key]
        h = self.qb[(self.qb.qb_id == qb_id) & ((self.qb.season < season) | ((self.qb.season == season) & (self.qb.week < week)))]
        if len(h) == 0:
            r = self.prior
        else:
            w = self.decay ** np.arange(len(h))[::-1] * self.SF ** (season - h.season.values)
            r = ((h.qb_epa.values * w).sum() + self.k * self.prior) / ((h.dropbacks.values * w).sum() + self.k)
        self._cache[key] = r
        return r


class SeasonFade6(SeasonFade): SF = 0.6


class SeasonFade9(SeasonFade): SF = 0.9


VARIANTS = [
    ("current (scrambles dropped, aged by own games)", qb0, R.QBRatings, {}),
    ("scrambles counted", qb1, R.QBRatings, {}),
    ("scrambles counted, aged by weeks (0.985)", qb1, WeekAged, {}),
    ("scrambles counted, aged by weeks (0.98)", qb1, WeekAged, {"qb_decay": 0.98}),
    ("scrambles counted, aged by weeks (0.99)", qb1, WeekAged, {"qb_decay": 0.99}),
    ("scrambles counted, aged by weeks (0.975)", qb1, WeekAged, {"qb_decay": 0.975}),
    ("scrambles and designed runs, aged by weeks (0.985)", qb2, WeekAged, {}),
    ("scrambles and designed runs", qb2, R.QBRatings, {}),
    ("scrambles and designed runs, season fade 0.8", qb2, SeasonFade, {}),
    ("scrambles and designed runs, season fade 0.6", qb2, SeasonFade6, {}),
    ("scrambles and designed runs, season fade 0.9", qb2, SeasonFade9, {}),
    ("scrambles and designed runs, idle weeks at 0.5", qb2, HybridAged, {}),
    ("scrambles and designed runs, idle weeks at 0.25", qb2, Hybrid25, {}),
    ("scrambles and designed runs, idle weeks at 0.10", qb2, Hybrid10, {}),
    ("scrambles and designed runs, aged by weeks (0.98)", qb2, WeekAged, {"qb_decay": 0.98}),
    ("scrambles counted, aged by weeks (0.985), k 100", qb1, WeekAged, {"qb_k": 100.0}),
    ("scrambles counted, aged by weeks (0.985), k 200", qb1, WeekAged, {"qb_k": 200.0}),
]
if os.environ.get("ONLY"):
    VARIANTS = [v for v in VARIANTS if any(v[0] == o[1:] if o.startswith("=") else o in v[0] for o in os.environ["ONLY"].split("|"))]
rows = []; orig = R.QBRatings
if os.environ.get("THIRD"):   # the window nobody tuned on: 2015 to 2018, same scoring as experiments/qb_third.py
    from nflmodel import backtest as B
    for name, q, cls, over in VARIANTS:
        R.QBRatings = cls
        f = M.with_trends(R.build_features({**R.DEFAULT, **over}, tg=tg, games=games, qb=q)); R.QBRatings = orig
        p3 = M.walk_forward(f, range(2015, 2019)); d = B.join(p3, games)
        d = d[(d.game_type == "REG") & d.season.isin(range(2015, 2019)) & (d.week < 18) & d.spread_line.notna() & d.home_score.notna()]
        pm = B.points_miss(d).set_index("target"); e = d.model_spread - d.spread_line; res = np.sign(d.home_score - d.away_score - d.spread_line)
        row = {"variant": name, "team_mae": round(float(pm.loc["team points", "model_mae"]), 4), "margin_mae": round(float(pm.loc["margin", "model_mae"]), 4), "n": int(len(d))}
        for cut in [4, 5]:
            m = (np.abs(e) >= cut) & (res != 0); w = int((np.sign(e[m]) == res[m]).sum()); row[f"ats{cut}"] = f"{w}-{int(m.sum() - w)}"
        rows.append(row); print(row, flush=True)
    out = os.environ.get("OUT", "reports/qb_fix_third.csv"); old = pd.read_csv(out) if os.path.exists(out) and os.path.getsize(out) > 5 else pd.DataFrame()
    pd.concat([old, pd.DataFrame(rows)], ignore_index=True).drop_duplicates("variant", keep="last").to_csv(out, index=False); print("DONE"); raise SystemExit
for name, q, cls, over in VARIANTS:
    R.QBRatings = cls
    f = M.with_trends(R.build_features({**R.DEFAULT, **over}, tg=tg, games=games, qb=q)); r = both(f)
    rows.append({"variant": name, **{f"{k}_{w}": v for w, d in r.items() for k, v in d.items()}})
    print(name, {w: (r[w]["team_mae"], r[w]["margin_mae"], r[w]["ats5"], r[w]["ats4"]) for w in r}, flush=True)
    R.QBRatings = orig
out = os.environ.get("OUT", "reports/qb_fix.csv")
old = pd.read_csv(out) if os.path.exists(out) and os.path.getsize(out) > 5 else pd.DataFrame()
pd.concat([old, pd.DataFrame(rows)], ignore_index=True).drop_duplicates("variant", keep="last").to_csv(out, index=False); print("DONE")
