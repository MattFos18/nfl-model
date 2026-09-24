"""Opponent-adjusted player values (24 Sep 2026). A player's EPA per play is the play-by-play's EPA (nflfastR), which
does not know who he faced: 100 targets against the league's best pass defenses count the same as 100 against the
worst. Test: adjust each game's EPA per play by the opponent defense's strength coming in (its decayed EPA allowed per
pass play for passers and receivers, per run for rushers, before that game, minus the league's), then ask which rate
predicts the player's next game better.

  raw       the value as the page computes it: decayed (0.985 a game), shrunk (K plays toward 0)
  adjusted  the same on (game EPA - opponent strength x plays), and the next game's prediction adds that game's
            opponent strength back (so both predict the same raw quantity)
  half      adjusted with half the opponent strength (the opponent's own rating is a noisy estimate)
  raw_plus_next, adjusted_no_next, half_no_next   the two parts apart: the next opponent added to the raw rate, and
            the past games adjusted with no next-opponent term (the player's own quality, what the page shows)

Scored by play-weighted mean squared error of the next game's EPA per play (players with 5+ plays that game), per
role and window. Adopt only if better on both windows (2019-22, 2023-25); 2015-18 shown. Writes reports/opp_adjust.csv.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import numpy as np, pandas as pd
from nflmodel.model import OUT
from nflmodel.players import DEFAULT

DECAY, K = DEFAULT["decay"], DEFAULT["k"]
TEAM_DECAY, TEAM_FADE, TEAM_K = 0.94, 0.8, 3.0


def opp_strength() -> pd.DataFrame:
    """Per (game_id, team): the opponent defense's pass and run EPA allowed per play before this game, decayed, shrunk,
    minus that season's league average. (The same as nflmodel.players.opponent_strength, which the page uses.)"""
    tg = pd.read_parquet(OUT / "team_games.parquet", columns=["game_id", "season", "week", "team", "opp", "game_type", "def_pass_epa", "def_rush_epa"])
    tg = tg.sort_values(["season", "week"]).reset_index(drop=True)
    for col in ["def_pass_epa", "def_rush_epa"]:
        pri = np.full(len(tg), np.nan)
        for _, g in tg.groupby("team"):
            num = den = 0.0; last = None
            for i, s, v in zip(g.index, g.season, g[col]):
                if last is not None and s != last:
                    num *= TEAM_FADE; den *= TEAM_FADE
                pri[i] = num / (den + TEAM_K)
                if pd.notna(v):
                    num = num * TEAM_DECAY + v; den = den * TEAM_DECAY + 1.0
                last = s
        tg[f"pri_{col}"] = pri - tg.groupby("season")[col].transform("mean")
    # the team's opponent's defense: look up the opponent's row in the same game
    o = tg[["game_id", "team", "pri_def_pass_epa", "pri_def_rush_epa"]].rename(columns={"team": "opp", "pri_def_pass_epa": "opp_pass", "pri_def_rush_epa": "opp_rush"})
    return tg[["game_id", "team", "opp"]].merge(o, on=["game_id", "opp"], how="left")


def run() -> pd.DataFrame:
    pg = pd.read_parquet(OUT / "player_games.parquet")
    pg = pg[pg.plays > 0].merge(opp_strength(), on=["game_id", "team"], how="left").fillna({"opp_pass": 0.0, "opp_rush": 0.0})
    pg["opp"] = np.where(pg.role == "rusher", pg.opp_rush, pg.opp_pass)
    pg = pg.sort_values(["season", "week"]).reset_index(drop=True)
    res = []
    for role, d in pg.groupby("role"):
        preds = {k: np.full(len(d), np.nan) for k in ("raw", "adjusted", "half", "raw_plus_next", "adjusted_no_next", "half_no_next")}
        idx_all = d.index.values; pos = {ix: n for n, ix in enumerate(idx_all)}
        for _, g in d.groupby("player_id"):
            num = {k: 0.0 for k in ("raw", "adjusted", "half")}; den = 0.0
            for ix, pl, ep, op in zip(g.index, g.plays.values, g.epa.values, g.opp.values):
                n = pos[ix]
                preds["raw"][n] = num["raw"] / (den + K)
                preds["adjusted"][n] = num["adjusted"] / (den + K) + op
                preds["half"][n] = num["half"] / (den + K) + 0.5 * op
                preds["raw_plus_next"][n] = num["raw"] / (den + K) + op
                preds["adjusted_no_next"][n] = num["adjusted"] / (den + K)
                preds["half_no_next"][n] = num["half"] / (den + K)
                den = den * DECAY + pl
                num["raw"] = num["raw"] * DECAY + ep
                num["adjusted"] = num["adjusted"] * DECAY + ep - op * pl
                num["half"] = num["half"] * DECAY + ep - 0.5 * op * pl
        x = d.assign(**{f"p_{k}": v for k, v in preds.items()}); x = x[x.plays >= 5]; y = x.epa / x.plays
        for w, (a, b) in {"2015-18": (2015, 2018), "2019-22": (2019, 2022), "2023-25": (2023, 2025)}.items():
            m = x.season.between(a, b)
            row = {"role": role, "window": w, "n": int(m.sum())}
            for k in preds:
                row[k] = float(np.average((y[m] - x.loc[m, f"p_{k}"]) ** 2, weights=x.plays[m]))
            res.append(row)
    return pd.DataFrame(res)


if __name__ == "__main__":
    r = run(); r.to_csv(Path(__file__).resolve().parent.parent / "reports" / "opp_adjust.csv", index=False)
    for k in ["adjusted", "half", "raw_plus_next", "adjusted_no_next", "half_no_next"]:
        r[k] = (100 * (r.raw - r[k]) / r.raw).round(2)
    pd.set_option("display.width", 200); print("percent lower error than raw:"); print(r.drop(columns="raw").to_string(index=False))
