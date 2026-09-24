"""Season totals game by game (24 Sep 2026). Today's season total uses one per-game number for every game left: the
player's volume and rate against an average defense, at his team's average pace. The standard projection systems
instead project each remaining game on its own and add them up, so a player with a soft schedule left gets more. The
per-game engine already does this for this week's cards (props.project_game): his rate moved toward what the
defense allows, the team's plays moved toward the opponent's pace and by the expected game script. This test applies
it to every remaining game as of the week, with only what was known then.

For each remaining game of the player's team, the player's per-game yards are scaled by
  rate factor:   _toward(1, allowed/league) for that defense (receiving 25%, rushing 25%, passing 50% of the way;
                 props.W), the defense's allowed yards per touch over its last 17 games as of the week
  volume factor: props.game_script for that game (the team's plays per game, the opponent's allowed plays per game at
                 props.PACE, the expected margin and total from the game model as of the week) over the team's average
Variants: base (today), rate (defense only), rate_pace (defense and opponent pace), full (and the game model's expected
margin and total for each game, from season.py's equation with the ratings as of the week). Each variant refits the
two constants (AVAIL, BLEND) on 2016-18 as the base did, then is scored on 2019-22 and 2023-25: mean miss, the share
within 10% and 20% of the actual total, and the breakout flag's hit rate. Adopt only if better on both windows.

Rows come from the backtest cache (reports/player_season_rows.csv, experiments/player_season_backtest.py).
Writes reports/season_by_game.csv."""
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import numpy as np, pandas as pd
from nflmodel import player_season as PS, props as PR, season as SE
from experiments import player_season_backtest as BT

VARIANTS = ["base", "rate", "rate_pace", "full"]
KIND_GS = {"rec": ("pass_plays_pg", "ypt_allowed", "ypt"), "rush": ("runs_pg", "ypc_allowed", "ypc"), "pass": ("dropbacks_pg", "ypd_allowed", "ypd")}


def team_factors() -> pd.DataFrame:
    """One row per (season, as-of week, team, kind, variant): the sum over the team's remaining games of the per-game
    factor, and the count of games (the base variant's sum)."""
    games = pd.read_parquet(PS.OUT / "games.parquet")
    d = PR.official(pd.read_parquet(PS.OUT / "scheme_plays.parquet"))
    f = SE._frame(); pred = pd.read_parquet(PS.OUT / "pred_v3.parquet")
    out = []; t0 = time.time()
    for s in BT.FIT_SEASONS + BT.TEST_SEASONS:
        reg = games[(games.season == s) & (games.game_type == "REG")]
        dome_of = {}
        for r in reg.itertuples():
            dome_of[r.home_team] = float(r.dome) if pd.notna(r.dome) else dome_of.get(r.home_team, 0.0)
        for w in BT.WEEKS:
            if s == 2016 and w == 1:
                continue
            a = PR._asof(d, s, w); D, V, L = PR.defenses(a), PR.teams_volume(a), PR.league_baselines(a)
            P = SE.profiles(f, s, w); fit = SE.fit_asof(pred, s, w)
            left = reg[reg.week >= w]
            acc = {}
            for g in left.itertuples():
                ep = {}
                if g.home_team in P and g.away_team in P:
                    neu = 1.0 if (pd.notna(g.neutral) and g.neutral == 1) else 0.0; dg = 1.0 if g.div_game == 1 else 0.0; dm = 0.0 if neu else dome_of.get(g.home_team, 0.0)
                    ep[g.home_team] = SE.expected_points(P[g.home_team], P[g.away_team], fit, 0.0 if neu else 1.0, neu, dm, dg, int(g.week))
                    ep[g.away_team] = SE.expected_points(P[g.away_team], P[g.home_team], fit, 0.0, neu, dm, dg, int(g.week))
                for team, opp in ((g.home_team, g.away_team), (g.away_team, g.home_team)):
                    dd = D.get(opp, {}); base = V.get(team, {})
                    for k, (vk, ak, lk) in KIND_GS.items():
                        b = base.get(vk, 0.0)
                        if not b:
                            continue
                        rate = PR._toward(1.0, dd.get(ak), L[lk], PR.W[k])
                        # game_script's intercept is part of the per-game engine; the base per-game number has none, so each
                        # volume factor is taken against the same engine at margin 0 and no total (the team's own game)
                        ref = PR.game_script(k, b, 0.0, None, None)
                        vol_pace = PR.game_script(k, b, 0.0, None, dd.get(vk)) / ref if ref else 1.0
                        if ep:
                            m = ep[team] - ep[opp]; tot = ep[team] + ep[opp]
                            vol_full = PR.game_script(k, b, m, tot, dd.get(vk)) / ref if ref else 1.0
                        else:
                            vol_full = vol_pace
                        x = acc.setdefault((team, k), {"base": 0.0, "rate": 0.0, "rate_pace": 0.0, "full": 0.0})
                        x["base"] += 1.0; x["rate"] += rate; x["rate_pace"] += rate * vol_pace; x["full"] += rate * vol_full
            for (team, k), x in acc.items():
                for v, val in x.items():
                    out.append({"season": s, "week": w, "team": team, "kind": k, "variant": v, "factor_sum": val})
            print(f"{s} week {w} ({time.time() - t0:.0f}s)", flush=True)
    return pd.DataFrame(out)


def evaluate(R: pd.DataFrame, avail: dict, blend: dict) -> pd.DataFrame:
    """As the base backtest, with the games left replaced by the variant's factor sum."""
    R = R.copy()
    a = R.kind.map(avail).astype(float); b = R.kind.map(blend).astype(float)
    ours = R.yards_so_far + R.yards_pg * R.factor_sum * a
    R["proj_yards"] = (1 - b) * ours + b * R.pace_yards
    R["proj_pg"] = R.proj_yards / R.team_games.clip(lower=1)
    R["rank"] = R.groupby(["season", "week", "kind"]).proj_yards.rank(ascending=False, method="first").astype(int)
    R["breakout"] = (R["rank"] <= R.kind.map(PS.TOP_N)) & (R.proj_pg >= PS.BREAK_UP * R.prev_pg) & (R.prev_games > 0)
    R["err"] = (R.proj_yards - R.actual_yards).abs()
    R["rel"] = R.err / R.actual_yards.clip(lower=1)
    return R


def main():
    fac_f = PS.REP / "season_by_game_factors.csv"
    F = pd.read_csv(fac_f) if fac_f.exists() else team_factors()
    F.to_csv(fac_f, index=False)
    R0 = pd.read_csv(BT.CACHE); R0 = R0[R0.team_games_left > 0]
    res = []
    for v in VARIANTS:
        R = R0.merge(F[F.variant == v].drop(columns="variant"), on=["season", "week", "team", "kind"], how="left")
        R["factor_sum"] = R.factor_sum.fillna(R.team_games_left)
        fit = R[R.season.isin(BT.FIT_SEASONS)]; test = R[R.season.isin(BT.TEST_SEASONS)].copy(); test["window"] = test.season.map(BT.WINDOW)
        avail, blend = {}, {}
        for k in ("rec", "rush", "pass"):
            fk = fit[fit.kind == k]; best = None
            for a in BT.AVAIL_GRID:
                for b in BT.BLEND_GRID:
                    e = evaluate(fk, {k: a}, {k: b}).err.mean()
                    if best is None or e < best[0]:
                        best = (e, float(a), float(b))
            avail[k], blend[k] = best[1], best[2]
        T = evaluate(test, avail, blend)
        T["hit"] = (T.actual_pg >= PS.BREAK_UP * T.prev_pg) & (T.actual_rank <= T.kind.map(PS.TOP_N)) & (T.prev_games > 0)
        for (k, w), g in T.groupby(["kind", "window"]):
            fl = g[g.breakout & (g["rank"] <= g.kind.map(PS.TOP_N))]
            res.append({"variant": v, "kind": k, "window": w, "avail": avail[k], "blend": blend[k], "n": len(g), "mae": round(g.err.mean(), 1),
                        "within10": round(float((g.rel <= 0.10).mean()), 3), "within20": round(float((g.rel <= 0.20).mean()), 3),
                        "flags": int(len(fl)), "hit": round(float(fl.hit.mean()), 3) if len(fl) else np.nan})
    o = pd.DataFrame(res); o.to_csv(PS.REP / "season_by_game.csv", index=False)
    pd.set_option("display.width", 220)
    print(o.pivot_table(index=["kind", "variant"], columns="window", values=["mae", "within20", "hit"]).to_string())


if __name__ == "__main__":
    main()
