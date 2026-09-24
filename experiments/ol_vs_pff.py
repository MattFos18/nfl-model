"""Offensive line units against PFF's 2026 line rankings (24 Sep 2026).

PFF ranks each team's projected starting five (data/reference/consensus/olunit_pff_2026.html, fetched by the
reference workflow). Ours rates the unit by what it did: pressures allowed per dropback and rushing yards before
contact per carry against the league (nflmodel/positions.py, OL_W), per offensive snap, recent games weighted more
(0.92 a game, last season at 0.8, as the lineman values). Also the page's roster view: the sum of the current top
five linemen's values. Spearman rank agreement of each with PFF, plus each part alone. Writes reports/ol_vs_pff.csv.
"""
from __future__ import annotations
import re, numpy as np, pandas as pd
from pathlib import Path
import sys; sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

ROOT = Path(__file__).resolve().parent.parent
RAW, OUT, REP = ROOT / "data" / "raw", ROOT / "data" / "processed", ROOT / "reports"
CITY = {"Arizona": "ARI", "Atlanta": "ATL", "Baltimore": "BAL", "Buffalo": "BUF", "Carolina": "CAR", "Chicago": "CHI", "Cincinnati": "CIN", "Cleveland": "CLE",
        "Dallas": "DAL", "Denver": "DEN", "Detroit": "DET", "Green Bay": "GB", "Houston": "HOU", "Indianapolis": "IND", "Jacksonville": "JAX", "Kansas": "KC",
        "Los Angeles Chargers": "LAC", "Los Angeles Rams": "LA", "Las Vegas": "LV", "Miami": "MIA", "Minnesota": "MIN", "New England": "NE", "New Orleans": "NO",
        "New York Giants": "NYG", "New York Jets": "NYJ", "Philadelphia": "PHI", "Pittsburgh": "PIT", "San Francisco": "SF", "Seattle": "SEA", "Tampa": "TB",
        "Tennessee": "TEN", "Washington": "WAS"}


def pff() -> pd.Series:
    h = open(ROOT / "data" / "reference" / "consensus" / "olunit_pff_2026.html").read()
    t = re.sub(r"<[^>]+>", "\n", re.sub(r"<script.*?</script>|<style.*?</style>", "", h, flags=re.S))
    out = {}
    for m in re.finditer(r"\n(\d{1,2})\.\s*([A-Z][A-Za-z .]+?)\s*\n", t):
        nm = m.group(2).strip()
        team = next((v for k, v in sorted(CITY.items(), key=lambda kv: -len(kv[0])) if nm.startswith(k)), None)
        if team and team not in out.values():
            out[int(m.group(1))] = team
    s = pd.Series({t: r for r, t in out.items()}, name="pff_rank")
    assert len(s) == 32, len(s)
    return s


def units() -> pd.DataFrame:
    from nflmodel.positions import TEAM_FIX, OL_W
    a = pd.concat([pd.read_parquet(f, columns=["game_id", "season", "week", "team", "times_pressured"]) for f in sorted((RAW / "pfr_pass").glob("advstats_week_pass_*.parquet"))])
    u = pd.concat([pd.read_parquet(f, columns=["game_id", "season", "week", "team", "carries", "rushing_yards_before_contact"]) for f in sorted((RAW / "pfr_rush").glob("advstats_week_rush_*.parquet"))])
    for x in (a, u):
        x["team"] = x.team.replace(TEAM_FIX)
    a = a.groupby(["game_id", "season", "week", "team"], as_index=False).times_pressured.sum()
    u = u.groupby(["game_id", "season", "week", "team"], as_index=False)[["carries", "rushing_yards_before_contact"]].sum()
    tg = pd.read_parquet(OUT / "team_games.parquet", columns=["game_id", "team", "pass_plays", "plays"])
    t = a.merge(u, on=["game_id", "season", "week", "team"], how="outer").merge(tg, on=["game_id", "team"], how="left").fillna(0.0)
    t = t[t.season >= 2024]
    lg = t.groupby("season").agg(pr=("times_pressured", "sum"), db=("pass_plays", "sum"), ybc=("rushing_yards_before_contact", "sum"), car=("carries", "sum"))
    t = t.merge((lg.pr / lg.db).rename("lg_press"), on="season").merge((lg.ybc / lg.car).rename("lg_ybc"), on="season")
    t["pass_part"] = OL_W["press"] * (t.lg_press * t.pass_plays - t.times_pressured)
    t["run_part"] = OL_W["ybc"] * (t.rushing_yards_before_contact - t.lg_ybc * t.carries)
    rows = []
    for team, g in t.sort_values(["season", "week"]).groupby("team"):
        n = len(g); w = 0.92 ** np.arange(n - 1, -1, -1) * np.where(g.season.values < 2026, 0.8, 1.0)
        sn = (w * g.plays).sum()
        rows.append({"team": team, "unit_per_100": 100 * (w * (g.pass_part + g.run_part)).sum() / sn,
                     "pass_per_100": 100 * (w * g.pass_part).sum() / sn, "run_per_100": 100 * (w * g.run_part).sum() / sn,
                     "press_rate_2025": g[g.season == 2025].times_pressured.sum() / g[g.season == 2025].pass_plays.sum()})
    return pd.DataFrame(rows).set_index("team")


def roster_view() -> pd.Series:
    import json
    d = json.loads(re.sub(r"^window.PLAYERS=|;$", "", open(ROOT / "web" / "data" / "players.js").read().strip()))
    v = pd.DataFrame(d["values"]); v = v[v.group == "OL"]
    return v.sort_values("share", ascending=False).groupby("team").head(5).groupby("team").value_above_replacement.sum().rename("roster_top5")


if __name__ == "__main__":
    x = units().join(roster_view()).join(pff())
    res = []
    for c in ["unit_per_100", "pass_per_100", "run_per_100", "roster_top5"]:
        rk = x[c].rank(ascending=False)
        res.append({"measure": c, "spearman_vs_pff": round(float(np.corrcoef(rk, x.pff_rank)[0, 1]), 3)})
    rk = (-x.press_rate_2025).rank(ascending=False)
    res.append({"measure": "2025 pressure rate allowed", "spearman_vs_pff": round(float(np.corrcoef(rk, x.pff_rank)[0, 1]), 3)})
    r = pd.DataFrame(res); print(r.to_string(index=False))
    x["our_rank"] = x.unit_per_100.rank(ascending=False).astype(int); x["gap"] = x.our_rank - x.pff_rank
    print(x.sort_values("pff_rank").round(3).to_string())
    REP.mkdir(exist_ok=True); x.sort_values("pff_rank").round(4).to_csv(REP / "ol_vs_pff.csv")
    r.to_csv(REP / "ol_vs_pff_summary.csv", index=False)
