"""The 2 Oct 2026 data fixes, before and after (data audit; Matt approved the fixes as data corrections, not a model change).

Fixes (all in code, applied when build.py rebuilds games.parquet):
  1. build.fix_starters: a played game's listed starting QB who took no dropback is replaced by the QB who started
     (first dropback among passers with 3+, from the play-by-play); 44 team-games 2022-2025 (33 in 2024), 3 in 2026.
  2. venues.fix_venues / venues.site: eleven 2025-26 games abroad listed at a US stadium or under a dome; every weather
     reader takes the game's real site; the stored forecast history drops games abroad (read at US airports).
  3. build.fix_wind: schedule wind more than 10 mph from the Open-Meteo archive (refetched at the real site) is replaced
     where no forecast exists or the GFS forecast sides with the archive; 30 games 2013-2024 (24 from 2015), one 2008
     reading of 70 mph blanked.
  4. lines.before_kickoff: once a game starts, its line is the last snapshot before kickoff (no model effect).

How the two runs were made (same raw data, same machine): python experiments/data_fixes.py <base_dir> <after_dir>, where
each dir holds games.parquet and pred_v3.parquet from build -> features -> weather.apply_to_games -> ratings -> trends
-> model --seasons 2015-2025, base on the code before the fixes and after on the code with them. Records are
picks.rule_records on backtest.join (regular season, weeks 1-17); the wind under reads the stored forecast history
(less games abroad after). Writes reports/data_fixes.csv.
"""
import sys
import numpy as np, pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from nflmodel import backtest as BT, picks as P, forecast_history as FH   # noqa: E402
from nflmodel.venues import sites   # noqa: E402


def score(tag: str, d_: Path) -> list[dict]:
    g = pd.read_parquet(d_ / "games.parquet"); pr = pd.read_parquet(d_ / "pred_v3.parquet")
    d = BT.join(pr, g); d = d[(d.game_type == "REG") & d.season.between(2015, 2025) & d.spread_line.notna()]
    h = pd.read_csv(FH.OUTF)
    if tag == "after":
        h = h[~h.game_id.isin(set(g.game_id[sites(g).abroad.astype(bool).values]))]
    m = h[["gfs_wind_d0", "nbs_wind_d0", "jma_wind_d0"]].apply(pd.to_numeric, errors="coerce").mean(axis=1)
    P._WIND = {gid: float(v) for gid, v in zip(h.game_id, m) if pd.notna(v)}
    P._NEUTRAL = set(g.game_id[g.location.eq("Neutral")]); P._PRIME = set(g.game_id[g.primetime.fillna(False).astype(bool)])
    rr = P.rule_records(d).set_index("rule")
    out = []
    for w, (a, b) in P.WINDOWS.items():
        x = d[d.season.between(a, b)]
        out.append({"run": tag, "window": w, "team_mae": round(float(np.abs(np.r_[x.home_err, x.away_err]).mean()), 4),
                    "margin_mae": round(float(np.abs(x.margin_err).mean()), 4), "total_mae": round(float(np.abs(x.total_err).mean()), 4),
                    "spread_flag": rr.at["model", w], "under_55": rr.at["shadowunder", w], "wind_under": rr.at["windunder", w]})
    return out


if __name__ == "__main__":
    base, after = Path(sys.argv[1]), Path(sys.argv[2])
    t = pd.DataFrame(score("base", base) + score("after", after))
    t.to_csv(ROOT / "reports" / "data_fixes.csv", index=False)
    print(t.to_string(index=False))
