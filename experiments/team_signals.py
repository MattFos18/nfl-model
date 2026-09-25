"""Team model: offseason signals for the early weeks, and finer ratings (25 Sep 2026, Matt). Our own data only.

A3, the offseason, active in Weeks 1 to 8 like the continuity inputs already in the model (own and opponent):
  qb_new_early     the starting QB is not last season's main QB (most dropbacks), and it is Week 1 to 8
  coach_new_early  the head coach is not the one who finished last season
  ol_ret_early     the share of last season's offensive-line snaps returning to the team (0 to 1), minus the league's
A4, finer ratings:
  split            pass and rush EPA ratings for the offense and the opponent's defense, beside the overall ones
  success          success rate for the offense and the opponent's defense
Each variant is the model's inputs plus the new ones, walk-forward with the weekly refit, scored by the miss of team
points and the margin on 2019-22 and 2023-25 (and 2015-18), and the flag's record. Adopt only if better on both.
Writes reports/team_signals.csv."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import numpy as np, pandas as pd
from nflmodel import model as M, backtest as B
from nflmodel.model import OUT
from nflmodel.features import RAW
from experiments.common import both, GAMES

EARLY = M.EARLY_WEEKS


def offseason(f: pd.DataFrame) -> pd.DataFrame:
    f = f.copy(); early = (f.week <= EARLY).astype(float)
    # QB: last season's main QB by games started (the frame's qb_id per team game)
    q = f[f.game_type == "REG"].groupby(["season", "team"]).qb_id.agg(lambda s: s.value_counts().index[0] if s.notna().any() else None)
    last_qb = {(s + 1, t): v for (s, t), v in q.items()}
    f["qb_new_early"] = [float(isinstance(qid, str) and last_qb.get((s, t)) not in (None, qid)) for s, t, qid in zip(f.season, f.team, f.qb_id)] * early
    # head coach: the one on the sideline for the team's last game of the season before
    g = GAMES[GAMES.game_type == "REG"].sort_values(["season", "week"])
    hc = pd.concat([g[["season", "week", "home_team", "home_coach"]].rename(columns={"home_team": "team", "home_coach": "coach"}), g[["season", "week", "away_team", "away_coach"]].rename(columns={"away_team": "team", "away_coach": "coach"})])
    last_c = hc.sort_values(["season", "week"]).groupby(["season", "team"]).coach.last(); cur = hc.set_index(["season", "week", "team"]).coach
    f["coach_new_early"] = [float(last_c.get((s - 1, t)) is not None and cur.get((s, w, t)) is not None and cur.get((s, w, t)) != last_c.get((s - 1, t))) for s, w, t in zip(f.season, f.week, f.team)] * early
    # offensive line: the share of last season's line snaps by players on the team's roster in week 1 of this season
    ex = pd.read_parquet(OUT / "snap_exposure.parquet", columns=["player_id", "season", "team", "position", "offense_snaps"])
    ol = ex[ex.position.isin(["T", "G", "C", "OL", "OT", "OG"])]
    tot = ol.groupby(["season", "team"]).offense_snaps.sum(); byp = ol.groupby(["season", "team", "player_id"]).offense_snaps.sum()
    ret = {}
    for s in sorted(f.season.unique()):
        rp = RAW / "rosters" / f"roster_weekly_{s}.parquet"
        if not rp.exists() or (s - 1) not in tot.index.get_level_values(0):
            continue
        r = pd.read_parquet(rp, columns=["team", "gsis_id", "week"]); r = r[r.week == r.week.min()]
        on = set(zip(r.team, r.gsis_id))
        last = byp.loc[s - 1]
        for t in last.index.get_level_values(0).unique():
            x = last.loc[t]; ret[(s, t)] = float(sum(v for p, v in x.items() if (t, p) in on) / max(x.sum(), 1))
    lg = np.mean(list(ret.values())) if ret else 0.0
    f["ol_ret_early"] = [(ret.get((s, t), lg) - lg) for s, t in zip(f.season, f.team)] * early
    for c in ("qb_new_early", "coach_new_early", "ol_ret_early"):
        o = f[["game_id", "team", c]].rename(columns={"team": "opp", c: "opp_" + c}); f = f.merge(o, on=["game_id", "opp"], how="left"); f["opp_" + c] = f["opp_" + c].fillna(0.0)
    return f


def third(f):
    p3 = M.walk_forward(f, range(2015, 2019)); d = B.join(p3, GAMES)
    d = d[(d.game_type == "REG") & d.season.isin(range(2015, 2019)) & (d.week < 18) & d.spread_line.notna() & d.home_score.notna()]
    pm = B.points_miss(d).set_index("target"); return round(float(pm.loc["team points", "model_mae"]), 4), round(float(pm.loc["margin", "model_mae"]), 4)


def run(f, extra, label, rows):
    base_feats = list(M.FEATS)
    M.FEATS[:] = base_feats + extra
    try:
        r = both(f); t = third(f)
    finally:
        M.FEATS[:] = base_feats
    rows.append({"variant": label, **{f"{k}_{w}": v for w, d in r.items() for k, v in d.items()}, "team_mae_2015-18": t[0], "margin_mae_2015-18": t[1]})
    print(rows[-1], flush=True)


def main():
    f0 = M.with_trends(pd.read_parquet(OUT / "features_asof.parquet"))
    f = offseason(f0); rows = []
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    run(f, [], "base (today)", rows)
    if which in ("all", "a3"):
        run(f, ["qb_new_early", "opp_qb_new_early"], "A3 new QB, early", rows)
        run(f, ["coach_new_early", "opp_coach_new_early"], "A3 new head coach, early", rows)
        run(f, ["ol_ret_early", "opp_ol_ret_early"], "A3 line returning, early", rows)
        run(f, ["qb_new_early", "opp_qb_new_early", "coach_new_early", "opp_coach_new_early", "ol_ret_early", "opp_ol_ret_early"], "A3 all three", rows)
    if which in ("all", "a4"):
        run(f, ["off_pass_epa", "def_pass_epa", "off_rush_epa", "def_rush_epa"], "A4 pass and rush ratings", rows)
        run(f, ["off_success", "def_success"], "A4 success rate", rows)
        run(f, ["off_pass_epa", "def_pass_epa", "off_rush_epa", "def_rush_epa", "off_success", "def_success"], "A4 both", rows)
    pd.DataFrame(rows).to_csv(Path(__file__).resolve().parent.parent / "reports" / f"team_signals_{which}.csv", index=False)


if __name__ == "__main__":
    main()
