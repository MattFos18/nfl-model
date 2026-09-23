"""Should the game model's absence input read the matchup? skill_out_value is a listed-out player's EPA per touch
above replacement times his share of touches, summed. The matchup version scales each absent receiver's value by
how his yards per target in the opponent's man/zone mix compare with his own average (players.py values, props.py
splits), so losing a receiver who beats man hurts more against a man-heavy defense. Both windows, against the
twenty-two inputs. Output reports/skill_out_matchup.csv."""
import numpy as np, pandas as pd
from nflmodel import model as M
from nflmodel.model import OUT
from experiments.common import both
d = pd.read_parquet(OUT / "scheme_plays.parquet"); d = d[d.play_type.isin(["pass", "run"])]
ps = d.pass_play
# per receiver-game: targets and yards against man / zone / all, rolling over his previous 17 games
t = d[ps & d.receiver_player_id.notna()].copy()
for k, m in {"man": t.man, "zone": t.zone, "all": t.man | ~t.man}.items():
    t[f"{k}_n"] = m.astype(int); t[f"{k}_y"] = np.where(m, t.yards_gained.fillna(0), 0.0)
rg = t.groupby(["receiver_player_id", "season", "week", "game_id"])[[c for c in t.columns if c.endswith("_n") or c.endswith("_y")]].sum().reset_index().sort_values(["receiver_player_id", "season", "week"])
cols = [c for c in rg.columns if c.endswith("_n") or c.endswith("_y")]
prev = rg.groupby("receiver_player_id")[cols].transform(lambda s: s.rolling(17, min_periods=1).sum().shift(1))
rg = pd.concat([rg[["receiver_player_id", "season", "week", "game_id"]], prev], axis=1)
rg["ypt_man"] = np.where(rg.man_n >= 15, rg.man_y / rg.man_n.replace(0, np.nan), np.nan); rg["ypt_zone"] = np.where(rg.zone_n >= 15, rg.zone_y / rg.zone_n.replace(0, np.nan), np.nan); rg["ypt"] = np.where(rg.all_n >= 15, rg.all_y / rg.all_n.replace(0, np.nan), np.nan)
R = rg.set_index(["receiver_player_id", "game_id"])
# per defense-game: man rate over the previous 17 games
q = d[ps & d.cov_known].copy(); q["man_i"] = q.man.astype(int); q["cov_i"] = 1
dg = q.groupby(["defteam", "season", "week", "game_id"])[["man_i", "cov_i"]].sum().reset_index().sort_values(["defteam", "season", "week"])
pv = dg.groupby("defteam")[["man_i", "cov_i"]].transform(lambda s: s.rolling(17, min_periods=1).sum().shift(1)); dg = pd.concat([dg[["defteam", "game_id"]], pv], axis=1)
dg["man_rate"] = np.where(dg.cov_i >= 50, dg.man_i / dg.cov_i.replace(0, np.nan), np.nan); DM = dg.set_index(["defteam", "game_id"]).man_rate
# the absent players behind each team-game's skill_out_value (names and values in player_injury.parquet detail; ids via names)
pi = pd.read_parquet(OUT / "player_injury.parquet"); f0 = M.with_trends(pd.read_parquet(OUT / "features_asof.parquet"))
from nflmodel.positions import names_by_id
names = names_by_id(range(2013, 2027)); by_name = {}
for pid, (nm, pos) in names.items(): by_name.setdefault(nm, pid)
def adj(row):
    if not isinstance(row.skill_out_detail, str) or not row.skill_out_detail: return row.skill_out_value
    total = 0.0
    for part in row.skill_out_detail.split(";"):
        try: nm, val, share = part.split("|"); val = float(val)
        except ValueError: continue
        pid = by_name.get(nm); k = (pid, row.game_id)
        if pid is None or k not in R.index: total += val; continue
        r = R.loc[k]; mr = DM.get((row.opp, row.game_id), np.nan)
        if np.isnan(mr) or np.isnan(r.ypt_man) or np.isnan(r.ypt_zone) or not r.ypt: total += val; continue
        mix = r.ypt_man * mr + r.ypt_zone * (1 - mr); total += val * max(0.25, min(2.0, mix / r.ypt))   # scaled by his rate in this mix against his average, capped
    return total
g = pd.read_parquet(OUT / "games.parquet")[["game_id", "home_team", "away_team"]]
pi = pi.merge(g, on="game_id"); pi["opp"] = np.where(pi.team == pi.home_team, pi.away_team, pi.home_team)
pi["skill_out_matchup"] = [adj(r) for r in pi.itertuples()]
print("changed rows", int((pi.skill_out_matchup != pi.skill_out_value).sum()), "of", int((pi.skill_out_value > 0).sum()), "with a value", flush=True)
iv = pi[["game_id", "team", "skill_out_matchup"]]
f = f0.merge(iv, on=["game_id", "team"], how="left").merge(iv.rename(columns={"team": "opp", "skill_out_matchup": "opp_skill_out_matchup"}), on=["game_id", "opp"], how="left")
f[["skill_out_matchup", "opp_skill_out_matchup"]] = f[["skill_out_matchup", "opp_skill_out_matchup"]].fillna(0.0)
rows = []; base_feats = M.FEATS.copy()
def row(name, r): return {"variant": name, **{f"{k}_{w}": v for w, dd in r.items() for k, v in dd.items()}}
base = both(f); rows.append(row("skill out as today", base)); print("base", {w: (base[w]["team_mae"], base[w]["margin_mae"], base[w]["ats4"]) for w in base}, flush=True)
M.FEATS = [c.replace("skill_out_value", "skill_out_matchup") for c in base_feats]; r = both(f); M.FEATS = base_feats
rows.append(row("skill out scaled by the receiver's rate in the opponent's man/zone mix", r)); print("matchup", {w: (round(r[w]["team_mae"] - base[w]["team_mae"], 4), round(r[w]["margin_mae"] - base[w]["margin_mae"], 4), r[w]["ats4"]) for w in r}, flush=True)
df = pd.DataFrame(rows)
for w in ["2019-22", "2023-25"]: df[f"delta_{w}"] = (df[f"team_mae_{w}"] - df.loc[0, f"team_mae_{w}"]).round(4)
df["verdict"] = ["base", "helps both" if df.loc[1, "delta_2019-22"] < -0.001 and df.loc[1, "delta_2023-25"] < -0.001 else ("helps one" if df.loc[1, "delta_2019-22"] < -0.001 or df.loc[1, "delta_2023-25"] < -0.001 else "no")]
df.to_csv("reports/skill_out_matchup.csv", index=False); print(df[["variant", "delta_2019-22", "delta_2023-25", "verdict"]].to_string()); print("DONE")
