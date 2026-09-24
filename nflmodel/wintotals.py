"""The books' preseason win totals against the model's (24 Sep 2026). Sports Odds History's archive of each season's
regular-season win totals (data/reference/wintotals/soh_<season>.html, fetched by the reference workflow): the
line, the over and under prices, and the wins each team finished with.

The market's expected wins: the line moved by the no-vig chance of the over, through a normal with the spread of a
season's wins (a team's wins over 17 games vary by about 2; a line of 9.5 at -150 over is about 9.9 expected). The
model's: its season simulation as of Week 1 (reports/season_team_odds.csv, experiments/season_backtest.py), made
only from games before the season. Both against what happened, 2019 to 2025, per team and season.

python -m nflmodel.wintotals   writes data/reference/win_totals.csv and reports/win_totals_vs_vegas.csv"""
from __future__ import annotations
import re
import numpy as np, pandas as pd
from pathlib import Path
from scipy.stats import norm

ROOT = Path(__file__).resolve().parent.parent
REF, REP = ROOT / "data" / "reference", ROOT / "reports"
WIN_SD = 2.0
NAMES = {"Arizona": "ARI", "Atlanta": "ATL", "Baltimore": "BAL", "Buffalo": "BUF", "Carolina": "CAR", "Chicago": "CHI", "Cincinnati": "CIN", "Cleveland": "CLE", "Dallas": "DAL",
         "Denver": "DEN", "Detroit": "DET", "Green Bay": "GB", "Houston": "HOU", "Indianapolis": "IND", "Jacksonville": "JAX", "Kansas City": "KC", "Las Vegas": "LV", "Oakland": "LV",
         "Los Angeles Chargers": "LAC", "San Diego": "LAC", "Los Angeles Rams": "LA", "St. Louis": "LA", "Miami": "MIA", "Minnesota": "MIN", "New England": "NE", "New Orleans": "NO",
         "New York Giants": "NYG", "New York Jets": "NYJ", "Philadelphia": "PHI", "Pittsburgh": "PIT", "San Francisco": "SF", "Seattle": "SEA", "Tampa Bay": "TB", "Tennessee": "TEN", "Washington": "WAS"}


def team_of(name: str) -> str | None:
    name = " ".join(name.split())
    for k in sorted(NAMES, key=len, reverse=True):
        if name.startswith(k):
            return NAMES[k]
    return None


def _prob(odds: float) -> float:
    return 100 / (odds + 100) if odds > 0 else -odds / (-odds + 100)


def parse() -> pd.DataFrame:
    rows = []
    for f in sorted((REF / "wintotals").glob("soh_*.html")):
        season = int(f.stem.split("_")[1]); h = f.read_text()
        body = h[h.find("<tbody>"):]
        for tr in re.findall(r"<tr>(.*?)</tr>", body, flags=re.S):
            cells = [re.sub(r"<[^>]+>", " ", c).strip() for c in re.findall(r"<td[^>]*>(.*?)</td>", tr, flags=re.S)]
            cells = [" ".join(c.split()) for c in cells]
            if len(cells) < 6:
                continue
            t = team_of(cells[0])
            try:
                line = float(cells[1]); over = float(cells[2].replace("+", "")); under = float(cells[3].replace("+", ""))
            except ValueError:
                continue
            if not t:
                continue
            actual = pd.to_numeric(cells[5], errors="coerce")
            po, pu = _prob(over), _prob(under); p = po / (po + pu)
            rows.append({"season": season, "team": t, "line": line, "over": int(over), "under": int(under), "p_over": round(p, 4),
                         "vegas_wins": round(line + WIN_SD * float(norm.ppf(min(max(p, 0.01), 0.99))), 2), "actual_wins": actual})
    d = pd.DataFrame(rows).drop_duplicates(["season", "team"], keep="first")
    return d


def compare(d: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    m = pd.read_csv(REP / "season_team_odds.csv"); m = m[m.asof_week == 1][["season", "window", "team", "wins", "actual_wins"]].rename(columns={"wins": "model_wins", "actual_wins": "actual"})
    x = m.merge(d[["season", "team", "line", "vegas_wins"]], on=["season", "team"], how="inner")
    x["blend_wins"] = (x.model_wins + x.vegas_wins) / 2
    rows = []
    for w, g in list(x.groupby("window")) + [("2019-25", x)]:
        e = lambda c: round(float((g[c] - g.actual).abs().mean()), 3)
        edge = g.model_wins - g.line; big = g[edge.abs() >= 1.0]; won = ((big.actual - big.line) * np.sign(big.model_wins - big.line) > 0).sum(); push = (big.actual == big.line).sum()
        rows.append({"window": w, "teams": len(g), "model_miss": e("model_wins"), "vegas_miss": e("vegas_wins"), "line_miss": e("line"), "blend_miss": e("blend_wins"),
                     "corr_model_vegas": round(float(np.corrcoef(g.model_wins, g.vegas_wins)[0, 1]), 3),
                     "model_side_1win": f"{int(won)}-{int(len(big) - won - push)}" + (f"-{int(push)}" if push else "")})
    return x, pd.DataFrame(rows)


if __name__ == "__main__":
    d = parse(); d.to_csv(REF / "win_totals.csv", index=False)
    print(d.groupby("season").size().to_dict())
    x, s = compare(d); x.to_csv(REP / "win_totals_vs_vegas.csv", index=False)
    pd.set_option("display.width", 200); print(s.to_string(index=False))
