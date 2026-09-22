"""Analysis lab studies. Each writes a table to reports/ and is meant to be rerun weekly.

Study 1, stat correlations: for every offense stat in team_games, correlate a team's average through Week 8
with its points per game over Weeks 9 to 17 (predictive), next to the correlation with its own points per
game over the same Weeks 1 to 8 (descriptive, what the old sheet's Stat Corelations tab measured).
Averaged over seasons 2012 to 2025. Stats that describe scoring (PF itself) look great descriptively and
much weaker predictively.

Study 2, stat reliability: split-half correlation (odd vs even games within a season) per stat.

Usage: python -m nflmodel.lab
"""
from __future__ import annotations
import numpy as np, pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT, REP = ROOT / "data" / "processed", ROOT / "reports"

OFF = ["pf", "epa_play", "epa_play_ng", "success", "success_ng", "pass_epa", "pass_epa_ng", "rush_epa", "rush_success",
       "early_down_epa", "early_down_success", "explosive_rate", "pass_rate", "pass_oe", "cpoe", "air_yards_att", "sack_rate",
       "int_rate", "turnover_rate", "yards_play", "third_conv", "rz_epa", "score_rate", "td_rate", "drive_to_rate",
       "rz_td_rate", "sec_per_play", "avg_start_ytg", "plays", "drives"]
DEF = ["pa", "def_epa_play", "def_epa_play_ng", "def_success", "def_pass_epa", "def_rush_epa", "def_early_down_epa",
       "def_explosive_rate", "def_sack_rate", "def_int_rate", "def_turnover_rate", "def_yards_play", "def_third_conv",
       "def_score_rate", "def_td_rate", "def_rz_td_rate", "def_avg_start_ytg"]


def stat_correlations(split_week=8) -> pd.DataFrame:
    tg = pd.read_parquet(OUT / "team_games.parquet")
    tg = tg[(tg.game_type == "REG") & tg.pf.notna()]
    rows = []
    for stat, target in [(s, "pf") for s in OFF] + [(s, "pa") for s in DEF]:
        pred, desc = [], []
        for s, d in tg.groupby("season"):
            early = d[d.week <= split_week].groupby("team")[list(dict.fromkeys([stat, target]))].mean()
            late = d[d.week > split_week].groupby("team")[target].mean()
            j = early.join(late.rename("late")).dropna()
            if len(j) < 20:
                continue
            pred.append(j[stat].corr(j.late))
            desc.append(j[stat].corr(j[target]))
        rows.append({"stat": stat, "target": target, "predictive_r": np.mean(pred), "same_season_r": np.mean(desc), "seasons": len(pred)})
    df = pd.DataFrame(rows)
    df["drop"] = df.same_season_r.abs() - df.predictive_r.abs()
    return df.sort_values(["target", "predictive_r"], key=lambda c: c.abs() if c.name == "predictive_r" else c, ascending=[True, False])


def reliability() -> pd.DataFrame:
    tg = pd.read_parquet(OUT / "team_games.parquet")
    tg = tg[(tg.game_type == "REG") & tg.pf.notna()].copy()
    tg["odd"] = tg.groupby(["season", "team"]).cumcount() % 2
    rows = []
    for stat in OFF + DEF:
        rs = []
        for s, d in tg.groupby("season"):
            piv = d.groupby(["team", "odd"])[stat].mean().unstack()
            if piv.shape[1] == 2 and len(piv) >= 20:
                rs.append(piv[0].corr(piv[1]))
        rows.append({"stat": stat, "split_half_r": np.mean(rs)})
    return pd.DataFrame(rows).sort_values("split_half_r", ascending=False)


if __name__ == "__main__":
    REP.mkdir(exist_ok=True)
    sc = stat_correlations()
    sc.to_csv(REP / "lab_stat_correlations.csv", index=False)
    rl = reliability()
    rl.to_csv(REP / "lab_stat_reliability.csv", index=False)
    txt = ["# Analysis lab", "", "## Stat correlations: through Week 8 vs points per game in Weeks 9 to 17 (2012 to 2025 average)", "",
           "predictive_r = correlation of the stat through Week 8 with future points; same_season_r = with points over the same weeks "
           "(what the old sheet measured). 'drop' is how much of the same-season correlation disappears when you ask the stat to predict.", "",
           sc.round(3).to_markdown(index=False), "", "## Reliability: split-half correlation within a season (odd vs even games)", "",
           rl.round(3).to_markdown(index=False), ""]
    (REP / "lab.md").write_text("\n".join(txt))
    print("\n".join(txt))
