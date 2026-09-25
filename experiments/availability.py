"""Who will actually play (25 Sep 2026, Matt). The season totals miss mostly on games missed: only about a third of
projected players play every game their team has left. Today every player of a kind gets one flat share of the games
left (player_season.AVAIL, fitted on 2016-18). This test predicts each player's share from what is known before the
week, from our own data only (no market):

  this week's injury report (Out, Doubtful, Questionable; practice DNP, limited, full), from the nflverse reports
  his share of his team's games played so far this season and last season
  how often he was listed Out or Doubtful over the previous two seasons (injury history)
  his age

A linear fit of the share of the games left he went on to play, per kind, on 2016-18; the season total is then yards
so far + his per-game mean x games left x the predicted share x a fitted scale, blended with pace (the blend refit).
Scored on 2019-22 and 2023-25 against today's rule: mean miss of the season total, within 20% (every projected
player, and the top of each list), and the miss on the games played themselves. Adopt only if better on both.
Writes reports/availability.csv."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import numpy as np, pandas as pd
from experiments import player_season_backtest as BT
from nflmodel import player_season as PS

RAW = PS.RAW
TOPW = {"rec": 48, "rush": 32, "pass": 24}
FREE_BLEND = "--free" in sys.argv


def injuries() -> pd.DataFrame:
    fr = []
    for s in range(2014, 2027):
        f = RAW / "injuries" / f"injuries_{s}.parquet"
        if f.exists():
            x = pd.read_parquet(f); col = "season_type" if "season_type" in x.columns else "game_type"
            fr.append(x[x[col] == "REG"][["season", "week", "gsis_id", "report_status", "practice_status"]])
    return pd.concat(fr, ignore_index=True).dropna(subset=["gsis_id"])


def features(R: pd.DataFrame) -> pd.DataFrame:
    inj = injuries()
    # this week's report (the one before the as-of week's games)
    wk = inj.drop_duplicates(["season", "week", "gsis_id"], keep="last").set_index(["season", "week", "gsis_id"])
    key = list(zip(R.season, R.week, R.player_id))
    rs = [wk.report_status.get(k) if k in wk.index else None for k in key]; ps = [wk.practice_status.get(k) if k in wk.index else None for k in key]
    R = R.copy()
    R["rep_out"] = [1.0 if s in ("Out",) else 0.0 for s in rs]; R["rep_doubt"] = [1.0 if s == "Doubtful" else 0.0 for s in rs]; R["rep_q"] = [1.0 if s == "Questionable" else 0.0 for s in rs]
    R["prac_dnp"] = [1.0 if isinstance(p, str) and p.startswith("Did Not") else 0.0 for p in ps]; R["prac_lim"] = [1.0 if isinstance(p, str) and p.startswith("Limited") else 0.0 for p in ps]
    # injury history: weeks listed Out or Doubtful in the two seasons before
    od = inj[inj.report_status.isin(["Out", "Doubtful"])].groupby(["gsis_id", "season"]).week.nunique()
    R["hist_out"] = [float(od.get((p, s - 1), 0) + od.get((p, s - 2), 0)) for p, s in zip(R.player_id, R.season)]
    R["share_now"] = np.where(R.team_games_played > 0, R.games_so_far / R.team_games_played.clip(lower=1), np.nan)
    R["share_prev"] = (R.prev_games / 17.0).clip(upper=1.0)
    pl = pd.read_parquet(RAW / "players" / "players.parquet", columns=["gsis_id", "birth_date"]).dropna()
    born = dict(zip(pl.gsis_id, pd.to_datetime(pl.birth_date, errors="coerce")))
    R["age"] = [((pd.Timestamp(f"{s}-09-01") - born[p]).days / 365.25) if p in born and pd.notna(born[p]) else np.nan for p, s in zip(R.player_id, R.season)]
    R["age"] = R.age.fillna(R.groupby("kind").age.transform("median"))
    return R


def design(d: pd.DataFrame) -> np.ndarray:
    sn = d.share_now.fillna(d.share_prev); has_now = d.share_now.notna().astype(float)
    return np.column_stack([np.ones(len(d)), d.rep_out, d.rep_doubt, d.rep_q, d.prac_dnp, d.prac_lim, sn * has_now, d.share_prev, d.hist_out.clip(upper=17) / 17.0, (d.age - 27).clip(lower=0), (27 - d.age).clip(lower=0)])


def main():
    R = pd.read_csv(BT.CACHE); R = R[R.team_games_left > 0].copy()
    R = features(R); R["played_share"] = (R.games_left_played / R.team_games_left).clip(0, 1)
    out = []
    for k in ("rec", "rush", "pass"):
        g = R[R.kind == k].copy(); fit = g[g.season.isin(BT.FIT_SEASONS)]
        beta = np.linalg.lstsq(design(fit), fit.played_share.values, rcond=None)[0]
        g["av_hat"] = np.clip(design(g) @ beta, 0.05, 1.0)
        fk = g[g.season.isin(BT.FIT_SEASONS)]
        proj = lambda d, m, b: (1 - b) * (d.yards_so_far + d.yards_pg * d.team_games_left * np.clip(m * d.av_hat, 0, 1.2)) + b * d.pace_yards
        a0, b0 = PS.AVAIL[k], PS.BLEND[k]
        # the pace weight held at today's (only the share changes), unless FREE_BLEND
        grid_b = BT.BLEND_GRID if FREE_BLEND else [b0]
        best = min(((float((proj(fk, m, b) - fk.actual_yards).abs().mean()), m, b) for m in np.round(np.arange(0.5, 1.31, 0.025), 3) for b in grid_b))
        m, b = best[1], best[2]
        old = lambda d: (1 - b0) * (d.yards_so_far + d.yards_pg * d.team_games_left * a0) + b0 * d.pace_yards
        print(k, "share fit:", np.round(beta, 3), "scale", m, "blend", b, flush=True)
        for w, (s0, s1) in {"2019-22": (2019, 2022), "2023-25": (2023, 2025)}.items():
            t = g[g.season.between(s0, s1)].copy(); t["old"] = old(t); t["new"] = proj(t, m, b)
            t["rk"] = t.groupby(["season", "week"]).old.rank(ascending=False)
            for v in ("old", "new"):
                rel = (t[v] - t.actual_yards).abs() / t.actual_yards.clip(lower=1); top = t.rk <= TOPW[k]
                share_hat = (a0 if v == "old" else np.clip(m * t.av_hat, 0, 1))
                out.append({"kind": k, "window": w, "variant": v, "n": len(t), "mae": round(float((t[v] - t.actual_yards).abs().mean()), 1),
                            "within20": round(float((rel <= 0.2).mean()), 3), "within20_top": round(float((rel[top] <= 0.2).mean()), 3),
                            "games_miss": round(float((share_hat * t.team_games_left - t.games_left_played).abs().mean()), 2), "scale": m if v == "new" else a0, "blend": b if v == "new" else b0})
    o = pd.DataFrame(out); o.to_csv(PS.REP / "availability.csv", index=False)
    pd.set_option("display.width", 200); print(o.to_string(index=False))


if __name__ == "__main__":
    main()
