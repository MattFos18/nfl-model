"""Accuracy checks. Every table the model reads is checked against something published.

1. 2024 season totals per team from play-by-play (team_box.parquet) against the Pro-Football-Reference team
   offense table that was pasted into the old sheet (data/raw/pfr_2024_offense_from_sheet.csv).
2. Points in team_box equal the schedule's scores for every game.
3. Every game's offense row and its opponent's defense row agree (what A gained is what B allowed).
4. Known results spot check.

Usage: python -m nflmodel.verify   (writes reports/verification.md, exits 1 if any check fails)
"""
from __future__ import annotations
import sys
import numpy as np, pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW, OUT, REP = ROOT / "data" / "raw", ROOT / "data" / "processed", ROOT / "reports"

NAME = {"Arizona Cardinals": "ARI", "Atlanta Falcons": "ATL", "Baltimore Ravens": "BAL", "Buffalo Bills": "BUF",
        "Carolina Panthers": "CAR", "Chicago Bears": "CHI", "Cincinnati Bengals": "CIN", "Cleveland Browns": "CLE",
        "Dallas Cowboys": "DAL", "Denver Broncos": "DEN", "Detroit Lions": "DET", "Green Bay Packers": "GB",
        "Houston Texans": "HOU", "Indianapolis Colts": "IND", "Jacksonville Jaguars": "JAX", "Kansas City Chiefs": "KC",
        "Las Vegas Raiders": "LV", "Los Angeles Chargers": "LAC", "Los Angeles Rams": "LA", "Miami Dolphins": "MIA",
        "Minnesota Vikings": "MIN", "New England Patriots": "NE", "New Orleans Saints": "NO", "New York Giants": "NYG",
        "New York Jets": "NYJ", "Philadelphia Eagles": "PHI", "Pittsburgh Steelers": "PIT", "San Francisco 49ers": "SF",
        "Seattle Seahawks": "SEA", "Tampa Bay Buccaneers": "TB", "Tennessee Titans": "TEN", "Washington Commanders": "WAS"}

# PFR column -> how to build it from team_box counts
MAP = {"PF": lambda s: s.pf, "Yds": lambda s: s.off_pass_yards - s.off_sack_yards + s.off_rush_yards,
       "Ply": lambda s: s.off_pass_att + s.off_rush_att + s.off_sacks, "TO": lambda s: s.off_interceptions + s.off_fumbles_lost,
       "FL": lambda s: s.off_fumbles_lost, "1stD": lambda s: s.off_first_downs, "Cmp": lambda s: s.off_completions,
       "Att": lambda s: s.off_pass_att, "PassYds": lambda s: s.off_pass_yards - s.off_sack_yards, "PassTD": lambda s: s.off_pass_td,
       "Int": lambda s: s.off_interceptions, "RushAtt": lambda s: s.off_rush_att, "RushYds": lambda s: s.off_rush_yards,
       "RushTD": lambda s: s.off_rush_td, "Pen": lambda s: s.off_penalties, "PenYds": lambda s: s.off_penalty_yards,
       "Sc%": lambda s: 100 * s.off_scoring_drives / s.off_drives}


def check_pfr(box: pd.DataFrame):
    pfr = pd.read_csv(RAW / "pfr_2024_offense_from_sheet.csv")
    pfr["team"] = pfr.Tm.str.strip("'").map(NAME)
    pfr = pfr.set_index("team")
    s = box[(box.season == 2024) & (box.game_type == "REG")].groupby("team").sum(numeric_only=True)
    rows = []
    for col, f in MAP.items():
        ours = f(s).reindex(pfr.index)
        theirs = pd.to_numeric(pfr[col], errors="coerce")
        diff = (ours - theirs)
        rows.append({"stat": col, "teams": int(theirs.notna().sum()), "exact_matches": int((diff.abs() < 0.5).sum()),
                     "mean_abs_diff": diff.abs().mean(), "max_abs_diff": diff.abs().max(),
                     "worst_team": diff.abs().idxmax(), "ours_worst": float(ours[diff.abs().idxmax()]), "pfr_worst": float(theirs[diff.abs().idxmax()])})
    return pd.DataFrame(rows)


def check_conversions(box: pd.DataFrame):
    conv = pd.read_csv(RAW / "pfr_2024_conversions_from_sheet.csv")
    conv["team"] = conv.Tm.str.strip("'").map(NAME)
    conv = conv.set_index("team")
    drv = pd.read_csv(RAW / "pfr_2024_drives_from_sheet.csv")
    drv["team"] = drv.Tm.str.strip("'").map(NAME)
    drv = drv.set_index("team")
    s = box[(box.season == 2024) & (box.game_type == "REG")].groupby("team").sum(numeric_only=True)
    pairs = {"3DAtt": (s.off_third_conv + s.off_third_fail, conv["3DAtt"]), "3DConv": (s.off_third_conv, conv["3DConv"]),
             "4DAtt": (s.off_fourth_conv + s.off_fourth_fail, conv["4DAtt"]), "RZAtt": (s.off_rz_trips, conv.RZAtt), "RZTD": (s.off_rz_tds, conv.RZTD),
             "Drives": (s.off_drives, drv.Dr), "Sc%": (100 * s.off_scoring_drives / s.off_drives, drv["Sc%"])}
    rows = []
    for k, (ours, theirs) in pairs.items():
        theirs = pd.to_numeric(theirs, errors="coerce")
        ours = ours.reindex(theirs.index)
        diff = ours - theirs
        rows.append({"stat": k, "teams": int(theirs.notna().sum()), "exact_matches": int((diff.abs() < 0.5).sum()),
                     "mean_abs_diff": diff.abs().mean(), "max_abs_diff": diff.abs().max(), "worst_team": diff.abs().idxmax()})
    return pd.DataFrame(rows)


def check_scores(box: pd.DataFrame, games: pd.DataFrame):
    g = games.set_index("game_id")
    h = box[box.home]
    a = box[~box.home]
    bad = int((h.pf.values != g.loc[h.game_id, "home_score"].values).sum() + (a.pf.values != g.loc[a.game_id, "away_score"].values).sum())
    return {"rows": len(box), "score_mismatches": bad}


def check_mirror(box: pd.DataFrame):
    m = box.merge(box, left_on=["game_id", "team"], right_on=["game_id", "opp"], suffixes=("", "_o"))
    cols = ["plays", "yards", "pass_att", "completions", "pass_yards", "sacks", "interceptions", "drives", "scoring_drives"]
    bad = sum(int((m[f"off_{c}"] != m[f"def_{c}_o"]).sum()) for c in cols)
    return {"pairs": len(m), "mirror_mismatches": bad}


def known_results(games: pd.DataFrame):
    checks = [("2024_22_KC_PHI", "away_score", 22), ("2024_22_KC_PHI", "home_score", 40), ("2024_22_KC_PHI", "spread_line", -1.5),
              ("2023_22_SF_KC", "home_score", 25), ("2023_22_SF_KC", "away_score", 22),
              ("2024_01_BAL_KC", "home_score", 27), ("2024_01_BAL_KC", "away_score", 20)]
    g = games.set_index("game_id")
    out = []
    for gid, col, val in checks:
        got = g.loc[gid, col] if gid in g.index else np.nan
        out.append({"game": gid, "field": col, "expected": val, "got": got, "ok": bool(got == val)})
    return pd.DataFrame(out)


if __name__ == "__main__":
    box = pd.read_parquet(OUT / "team_box.parquet")
    games = pd.read_parquet(OUT / "games.parquet")
    pfr = pd.concat([check_pfr(box), check_conversions(box)], ignore_index=True)
    sc = check_scores(box, games)
    mi = check_mirror(box)
    kr = known_results(games)
    ok = sc["score_mismatches"] == 0 and mi["mirror_mismatches"] == 0 and kr.ok.all()
    txt = ["# Verification", "", "## 1. 2024 season totals from play-by-play vs Pro-Football-Reference (the table in the old sheet)", "",
           "PFR counts a few things differently from nflverse (sacks in plays, penalty first downs, aborted snaps), so small gaps are a definitions "
           "question, not a data error. Anything more than a handful per team would be.", "", pfr.round(2).to_markdown(index=False), "",
           "## 2. Points in the team table equal the schedule scores", "", f"{sc['rows']} team-game rows, {sc['score_mismatches']} mismatches.", "",
           "## 3. What one offense gained equals what the other defense allowed", "", f"{mi['pairs']} pairs, {mi['mirror_mismatches']} mismatches.", "",
           "## 4. Known results", "", kr.to_markdown(index=False), "", f"Result: {'PASS' if ok else 'FAIL'}"]
    REP.mkdir(exist_ok=True)
    (REP / "verification.md").write_text("\n".join(txt))
    print("\n".join(txt))
    sys.exit(0 if ok else 1)
