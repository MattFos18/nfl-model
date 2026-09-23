"""Do the scheme profiles move the game model? Candidate inputs per team-game, as of the game from the team's and
opponent's previous 17 games (scheme_plays.parquet, participation 2016 on, FTN 2022 on): matchup fits (how much
the opponent's coverage, pressure and blitz mix suits this offense against its own average) and raw tendencies
(pass rate over expected, motion, play action; the opponent's man, blitz and pressure rates). Each added alone and
in groups to the twenty-two-input model, walk-forward, both windows. Output reports/scheme_inputs.csv."""
import numpy as np, pandas as pd
from nflmodel import model as M
from nflmodel.model import OUT
from experiments.common import both
N = 17
d = pd.read_parquet(OUT / "scheme_plays.parquet")
d = d[d.play_type.isin(["pass", "run"])].copy()
ps, db, run = d.pass_play, d.dropback, d.play_type.eq("run")
looks = {"man": ps & d.man, "zone": ps & d.zone, "press": db & (d.pressure == 1), "clean": db & (d.pressure == 0), "blitz": db & (d.blitz == 1), "noblitz": db & (d.blitz == 0), "pass": ps, "all": d.play_type.notna()}
def per_game(side):
    team = d.posteam if side == "off" else d.defteam
    g = pd.DataFrame({"game_id": d.game_id, "season": d.season, "week": d.week, "team": team})
    for k, m in looks.items():
        g[f"{k}_n"] = m.astype(int); g[f"{k}_epa"] = np.where(m, d.epa, 0.0)
    g["neutral_n"] = d.neutral.astype(int); g["neutral_pass"] = (d.neutral & ps).astype(int); g["xpass_sum"] = np.where(d.neutral & d.xpass.notna(), d.xpass, 0.0); g["xpass_n"] = (d.neutral & d.xpass.notna()).astype(int)
    g["motion_n"] = d.is_motion.notna().astype(int); g["motion"] = (d.is_motion == 1).astype(int); g["pa_n"] = (db & d.is_play_action.notna()).astype(int); g["pa"] = (db & (d.is_play_action == 1)).astype(int)
    g["cov_n"] = (ps & d.cov_known).astype(int); g["man_calls"] = (ps & d.man).astype(int); g["press_n"] = (db & d.pressure.notna()).astype(int); g["press"] = (db & (d.pressure == 1)).astype(int); g["blitz_n"] = (db & d.blitz.notna()).astype(int); g["blitzes"] = (db & (d.blitz == 1)).astype(int)
    a = g.groupby(["team", "season", "week", "game_id"]).sum(numeric_only=True).reset_index().sort_values(["team", "season", "week"])
    cols = [c for c in a.columns if c not in ("team", "season", "week", "game_id")]
    prev = a.groupby("team")[cols].transform(lambda s: s.rolling(N, min_periods=1).sum().shift(1))   # the previous N games, nothing from this one
    return pd.concat([a[["team", "season", "week", "game_id"]], prev], axis=1)
off, dfn = per_game("off"), per_game("def")
def rate(x, num, den, min_n=30): return np.where(x[den] >= min_n, x[num] / x[den].replace(0, np.nan), np.nan)
def epa(x, k, min_n=30): return np.where(x[f"{k}_n"] >= min_n, x[f"{k}_epa"] / x[f"{k}_n"].replace(0, np.nan), np.nan)
O = off[["game_id", "team"]].copy()
for k in ["man", "zone", "press", "clean", "blitz", "noblitz", "pass"]:
    O[f"o_{k}"] = epa(off, k)
O["o_pass_oe"] = rate(off, "neutral_pass", "neutral_n") - np.where(off.xpass_n >= 30, off.xpass_sum / off.xpass_n.replace(0, np.nan), np.nan)
O["o_motion"] = rate(off, "motion", "motion_n"); O["o_pa"] = rate(off, "pa", "pa_n")
D = dfn[["game_id", "team"]].copy()
D["d_man"] = rate(dfn, "man_calls", "cov_n"); D["d_press"] = rate(dfn, "press", "press_n"); D["d_blitz"] = rate(dfn, "blitzes", "blitz_n")
for k in ["man", "zone", "press", "clean", "blitz", "noblitz", "pass"]:
    D[f"d_{k}"] = epa(dfn, k)
f0 = M.with_trends(pd.read_parquet(OUT / "features_asof.parquet"))
f = f0.merge(O, on=["game_id", "team"], how="left").merge(D.rename(columns={"team": "opp"}), on=["game_id", "opp"], how="left")
# matchup fits: the offense's EPA in the mix the opponent plays, against its own passing average (0 when unknown)
f["cov_fit"] = (f.o_man * f.d_man + f.o_zone * (1 - f.d_man) - f.o_pass).fillna(0.0)
f["press_fit"] = (f.o_press * f.d_press + f.o_clean * (1 - f.d_press) - f.o_pass).fillna(0.0)
f["blitz_fit"] = (f.o_blitz * f.d_blitz + f.o_noblitz * (1 - f.d_blitz) - f.o_pass).fillna(0.0)
# the defense's side of the same fits: what it allows in the looks it plays, against its average
f["d_cov_fit"] = (f.d_man * f.d_man + f.d_zone * (1 - f.d_man) - f.d_pass).fillna(0.0)
for c in ["o_pass_oe", "o_motion", "o_pa", "d_man", "d_press", "d_blitz"]:
    f[c] = f[c].fillna(f[c].mean())
print("fits: nonzero share", {c: round(float((f[c] != 0).mean()), 3) for c in ["cov_fit", "press_fit", "blitz_fit"]}, "2019+ nonzero", round(float((f[f.season >= 2019].cov_fit != 0).mean()), 3), flush=True)
rows = []; base_feats = M.FEATS.copy()
def row(name, r): return {"added": name, **{f"{k}_{w}": v for w, d in r.items() for k, v in d.items()}}
base = both(f); rows.append(row("(none)", base)); print("base", {w: (base[w]["team_mae"], base[w]["margin_mae"], base[w]["ats4"]) for w in base}, flush=True)
def run(name, cols):
    M.FEATS = base_feats + cols; r = both(f); M.FEATS = base_feats; rows.append(row(name, r))
    print(name, {w: (round(r[w]["team_mae"] - base[w]["team_mae"], 4), round(r[w]["margin_mae"] - base[w]["margin_mae"], 4), r[w]["ats4"]) for w in r}, flush=True)
run("coverage fit (offense vs the opponent's man/zone mix)", ["cov_fit"])
run("pressure fit", ["press_fit"])
run("blitz fit", ["blitz_fit"])
run("all three fits", ["cov_fit", "press_fit", "blitz_fit"])
run("pass rate over expected", ["o_pass_oe"])
run("motion rate", ["o_motion"])
run("play-action rate", ["o_pa"])
run("opponent man rate", ["d_man"])
run("opponent pressure rate", ["d_press"])
run("opponent blitz rate", ["d_blitz"])
run("all tendencies", ["o_pass_oe", "o_motion", "o_pa", "d_man", "d_press", "d_blitz"])
df = pd.DataFrame(rows)
for w in ["2019-22", "2023-25"]: df[f"delta_{w}"] = (df[f"team_mae_{w}"] - df.loc[0, f"team_mae_{w}"]).round(4)
df["verdict"] = ["base" if i == 0 else ("helps both" if a < -0.001 and b < -0.001 else ("helps one" if a < -0.001 or b < -0.001 else "no")) for i, (a, b) in enumerate(zip(df["delta_2019-22"], df["delta_2023-25"]))]
df.to_csv("reports/scheme_inputs.csv", index=False); print(df[["added", "delta_2019-22", "delta_2023-25", "verdict"]].to_string()); print("DONE")
