"""Live games priced on the backtest's weather readings (2 Oct 2026, re-audit items 3, 5, 6; reports/live_weather_match.md).

A  the walk-forward 2015-2025 on the stored features, the stored fits read but never rewritten
   (model.trees_cache_read_only): spread flag, totals flag and wind under records, team points and total miss per window.
   Run on main before the change and on this branch: the change touches only unplayed games, so A must not move.
B  every unplayed outdoor game's weather as priced now (weather.live_source): the GFS MOS / Japan reading where wind_live
   has one, else Open-Meteo, beside the Open-Meteo values the model used before.
C  players.opponent_strength centred on the weeks before (league_mean_before) against the full-season mean: the shift.

    python -m experiments.live_weather_match        (writes reports/live_weather_match.csv)
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from nflmodel import model as M, weather as WX, players as PL, forecast_history as FH   # noqa: E402

OUT = ROOT / "data" / "processed"
WINDOWS = {"2015-18": (2015, 2018), "2019-22": (2019, 2022), "2023-25": (2023, 2025)}


def records(pred: pd.DataFrame, games: pd.DataFrame) -> pd.DataFrame:
    h = pd.read_csv(FH.OUTF); ab = FH.abroad_ids()
    w = h[list(FH.PRE_KICKOFF_WIND)].apply(pd.to_numeric, errors="coerce").mean(axis=1)
    wd = {k: v for k, v in zip(h.game_id, w) if pd.notna(v) and k not in ab}
    d = pred[["game_id", "season", "week", "model_spread", "model_total", "p_over_emp", "home_exp", "away_exp"]].merge(
        games[["game_id", "game_type", "home_score", "away_score", "spread_line", "total_line"]], on="game_id")
    d = d[(d.game_type == "REG") & d.home_score.notna()]
    rows = []
    for name, (a, b) in WINDOWS.items():
        x0 = d[d.season.between(a, b)]; x = x0[x0.week <= 17]
        cm = x.home_score - x.away_score - x.spread_line; e = x.model_spread - x.spread_line
        m = (e.abs() >= 4) & x.spread_line.notna() & (cm != 0); sw = int(((e > 0) == (cm > 0))[m].sum())
        tt = x.home_score + x.away_score - x.total_line
        mu = ((1 - x.p_over_emp) >= 0.55) & x.total_line.notna() & (tt != 0); uw = int((tt < 0)[mu].sum())
        mw = (x.game_id.map(wd) >= 10) & x.total_line.notna() & (tt != 0); ww = int((tt < 0)[mw].sum())
        rows.append({"window": name, "spread_flag": f"{sw}-{int(m.sum()) - sw}", "totals_flag": f"{uw}-{int(mu.sum()) - uw}",
                     "wind_under": f"{ww}-{int(mw.sum()) - ww}",
                     "team_miss": round(float(np.concatenate([(x0.home_exp - x0.home_score).abs(), (x0.away_exp - x0.away_score).abs()]).mean()), 4),
                     "total_miss": round(float((x0.model_total - x0.home_score - x0.away_score).abs().mean()), 4)})
    return pd.DataFrame(rows)


def live_table(games: pd.DataFrame) -> pd.DataFrame:
    src = WX.live_source(games); un = games.set_index("game_id")
    return pd.DataFrame([{"game_id": gid, "open_meteo_wind": un.wind.get(gid), "open_meteo_temp": un.temp.get(gid), "wind": d["wind"], "temp": d["temp"],
                          "mos_rain_chance": d["pop"], "open_meteo_rain_chance": d["precip_prob"], "source": f'{d["wind_src"]}/{d["temp_src"]}/{d["rain_src"]}'}
                         for gid, d in src.items() if d["wind_src"] or d["temp_src"]])


def centring_shift() -> pd.DataFrame:
    tg = pd.read_parquet(OUT / "team_games.parquet", columns=["season", "week", "def_pass_epa", "def_rush_epa"])
    rows = []
    for c in ["def_pass_epa", "def_rush_epa"]:
        dlt = (PL.league_mean_before(tg, c) - tg.groupby("season")[c].transform("mean")).abs()
        rows.append({"column": c, "mean_abs_shift": round(float(dlt.mean()), 4), "p90": round(float(dlt.quantile(0.9)), 4), "max": round(float(dlt.max()), 4)})
    return pd.DataFrame(rows)


if __name__ == "__main__":
    games = pd.read_parquet(OUT / "games.parquet")
    with M.trees_cache_read_only():
        pred = M.walk_forward(M.with_trends(pd.read_parquet(OUT / "features_asof.parquet")), range(2015, 2026))
    a = records(pred, games); print(a.to_string(index=False))
    b = live_table(games); print(b.round(1).to_string(index=False))
    c = centring_shift(); print(c.to_string(index=False))
    pd.concat([a.assign(part="A"), b.assign(part="B"), c.assign(part="C")]).to_csv(ROOT / "reports" / "live_weather_match.csv", index=False)
