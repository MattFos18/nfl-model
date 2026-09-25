"""Bet rules we have not tried (25 Sep 2026, Matt: "how can you improve right now"). The model is unchanged; only
which games are bet and how they are graded. Walk-forward prices from pred_v3 (every game priced with earlier games
only), regular season weeks 1-17, 2015-18 / 2019-22 / 2023-25. Units at the real closing price (nflverse spread and
moneyline odds), not a flat -110.
  A  the live flag (4+ point edge) graded at the real price
  B  flag by the model's cover chance instead of points: its margin spread carries the key numbers (3, 7), so a
     4-point edge across 3 counts for more than one across 5 to 9; cut chosen to bet about as many games as the flag
  C  moneyline value: the model's win chance against the book's (vig removed); bet the side at an edge of x points
Writes reports/bet_rules2.csv."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import numpy as np, pandas as pd
from nflmodel.model import OUT

REP = Path(__file__).resolve().parent.parent / "reports"
W = {"2015-18": (2015, 2018), "2019-22": (2019, 2022), "2023-25": (2023, 2025)}


def payout(odds):
    o = np.asarray(odds, float); return np.where(o > 0, o / 100, 100 / -o)


def grade(won, push, odds):
    return np.where(push, 0.0, np.where(won, payout(odds), -1.0))


def main():
    p = pd.read_parquet(OUT / "pred_v3.parquet")
    g = pd.read_parquet(OUT / "games.parquet")[["game_id", "result", "home_moneyline", "away_moneyline", "home_spread_odds", "away_spread_odds"]]
    d = p.merge(g, on="game_id"); d = d[(d.game_type == "REG") & (d.week <= 17) & d.result.notna() & d.spread_line.notna() & d.season.between(2015, 2025)].copy()
    d["edge"] = d.model_spread - d.spread_line; cm = d.result - d.spread_line
    d["pc_side"] = np.where(d.edge > 0, d.p_cover_home, 1 - d.p_cover_home)
    home = d.edge > 0
    d["s_won"] = np.where(home, cm > 0, cm < 0); d["s_push"] = cm == 0
    d["s_odds"] = np.where(home, d.home_spread_odds, d.away_spread_odds).astype(float)
    d["s_odds"] = d.s_odds.fillna(-110.0)
    d["u_real"] = grade(d.s_won, d.s_push, d.s_odds); d["u_110"] = grade(d.s_won, d.s_push, np.full(len(d), -110.0))
    # moneyline: vig-free book chance, model chance, the side with the bigger gap
    ih, ia = 1 / (1 + payout(d.home_moneyline)), 1 / (1 + payout(d.away_moneyline)); d["book_h"] = ih / (ih + ia)
    d["ml_edge_h"] = d.p_home - d.book_h
    mh = d.ml_edge_h > 0
    d["ml_edge"] = d.ml_edge_h.abs(); d["ml_won"] = np.where(mh, d.result > 0, d.result < 0); d["ml_push"] = d.result == 0
    d["ml_odds"] = np.where(mh, d.home_moneyline, d.away_moneyline).astype(float); d["ml_dog"] = d.ml_odds > 0
    d["u_ml"] = grade(d.ml_won, d.ml_push, d.ml_odds)
    rows = []
    def add(rule, mask, ucol, won, push):
        r = {"rule": rule}
        for w, (a, b) in W.items():
            k = mask & d.season.between(a, b)
            wn, ls = int((won & ~push)[k].sum()), int((~won & ~push)[k].sum())
            r[f"rec_{w}"] = f"{wn}-{ls}"; r[f"units_{w}"] = round(float(d.loc[k, ucol].sum()), 1); r[f"roi_{w}"] = round(float(d.loc[k, ucol].mean() * 100), 1) if k.any() else np.nan
        rows.append(r); print(r, flush=True)
    flag = d.edge.abs() >= 4
    add("A live flag (4+), at -110", flag, "u_110", d.s_won, d.s_push)
    add("A live flag (4+), at the real price", flag, "u_real", d.s_won, d.s_push)
    n_flag = int(flag[d.season.between(2015, 2018)].sum())
    for cut in (0.54, 0.55, 0.56, 0.57, 0.58):
        add(f"B cover chance >= {cut:.2f}", d.pc_side >= cut, "u_real", d.s_won, d.s_push)
    # B at the same bet count as the flag on 2015-18 (the cut is fixed there, never on the later windows)
    q = d.loc[d.season.between(2015, 2018), "pc_side"].sort_values(ascending=False).iloc[n_flag - 1]
    add(f"B cover chance >= {q:.3f} (flag's 2015-18 count)", d.pc_side >= q, "u_real", d.s_won, d.s_push)
    add("B cover chance top-count AND 4+ edge", (d.pc_side >= q) & flag, "u_real", d.s_won, d.s_push)
    for x in (0.03, 0.05, 0.07, 0.10):
        add(f"C moneyline, model beats the book by {x:.0%}", d.ml_edge >= x, "u_ml", d.ml_won, d.ml_push)
        add(f"C moneyline dogs only, {x:.0%}", (d.ml_edge >= x) & d.ml_dog, "u_ml", d.ml_won, d.ml_push)
    add("C moneyline on flagged games (the flag's side)", flag & (np.sign(d.edge) == np.sign(d.ml_edge_h)), "u_ml", d.ml_won, d.ml_push)
    pd.DataFrame(rows).to_csv(REP / "bet_rules2.csv", index=False)


if __name__ == "__main__":
    main()
