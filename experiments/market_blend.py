"""The market as an input, side by side. Add the line's implied points for the team (from the closing spread and
total: what Vegas expects it to score) as a twenty-first input and walk forward on both windows. This will beat the
pure model on the miss if the line carries information the inputs do not (it does); the point is to measure how
much, and to see what a blended line would look like next to the pure one. It is not a candidate to replace the
model: a model that leans on the line stops disagreeing with it. Output reports/market_blend.csv."""
import pandas as pd
from nflmodel import model as M
from nflmodel.model import OUT
from experiments.common import both
f = M.with_trends(pd.read_parquet(OUT / "features_asof.parquet")); g = pd.read_parquet(OUT / "games.parquet").set_index("game_id")
hi, ai = g.home_implied, g.away_implied
f["implied_pf"] = [(hi.get(k) if h == 1 else ai.get(k)) for k, h in zip(f.game_id, f.home)]
f["implied_pf"] = f.implied_pf.fillna(f.implied_pf.mean())
base_feats = M.FEATS.copy(); rows = []
def row(name, r): return {"variant": name, **{f"{k}_{w}": v for w, d in r.items() for k, v in d.items()}}
base = both(f); rows.append(row("pure model (today)", base)); print("base", {w: (base[w]["team_mae"], base[w]["margin_mae"]) for w in base}, flush=True)
M.FEATS = base_feats + ["implied_pf"]; r = both(f); rows.append(row("model + the line's implied points", r)); M.FEATS = base_feats
print("blend", {w: (round(r[w]["team_mae"] - base[w]["team_mae"], 4), round(r[w]["margin_mae"] - base[w]["margin_mae"], 4), r[w]["ats5"]) for w in r}, flush=True)
M.FEATS = ["implied_pf"]; r = both(f); rows.append(row("the line alone", r)); M.FEATS = base_feats
print("line alone", {w: (r[w]["team_mae"], r[w]["margin_mae"]) for w in r}, flush=True)
pd.DataFrame(rows).to_csv("reports/market_blend.csv", index=False); print("DONE")
