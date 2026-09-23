"""Round six (23 Sep 2026): tie the player projections to the game model. Two links, each on the adopted rule, walk-forward
with the game model's own as-of expected points (data/processed/pred_v3.parquet, priced before each game):
  A. game script from the model's expected margin and total instead of the closing line, and a half-and-half blend
  B. reconciliation: the team's expected touchdowns (and yards) from its expected points, fitted on 2016 to 2018
     (actual team touchdowns against model expected points), and every player's projection scaled so the team's
     players add up to it, with the scale shrunk toward 1 by a weight w
Scored on both windows by absolute error (yards) and Poisson log loss (touchdowns). Output reports/props_backtest6.csv."""
import numpy as np, pandas as pd, pathlib
from scipy.special import gammaln
from nflmodel.model import OUT
from nflmodel import props as PR
src = pathlib.Path(__file__).with_name("props_by_season.py").read_text().split("by_season, by_pos, by_bucket = [], [], []")[0]
ns = {"__name__": "bys"}; exec(compile(src, "bys", "exec"), ns); build = ns["build"]; pll = ns["pll"]
pred = pd.read_parquet(OUT / "pred_v3.parquet")[["game_id", "home_exp", "away_exp"]]
WIN = {"2019-22": (2019, 2022), "2023-25": (2023, 2025)}
rows = []
def ev(f, col, act, count):
    out = {}
    for w, (a, b) in WIN.items():
        x = f[f.season.between(a, b)]; out[f"mae_{w}"] = round(float((x[col] - x[act]).abs().mean()), 3); out[f"ll_{w}"] = round(pll(x[col].values, x[act].values), 4) if count else None; out[f"n_{w}"] = int(len(x))
    return out
for kind in ["rec", "rush", "pass"]:
    f, evs = build(kind); f = f.merge(pred, on="game_id", how="left")
    f["is_home"] = (f.posteam == f.home_team); f["exp_pts"] = np.where(f.is_home, f.home_exp, f.away_exp); f["opp_exp"] = np.where(f.is_home, f.away_exp, f.home_exp)
    f = f[f.exp_pts.notna()].copy(); f["me_model"] = f.exp_pts - f.opp_exp; f["tc_model"] = f.exp_pts + f.opp_exp - PR.GS_TOTAL
    b = PR.GS[kind]; base_pg = f.tv / f.tgames
    if kind == "pass": base_pg = (1 - PR.PACE["pass"]) * base_pg + PR.PACE["pass"] * f.a_tdb / f.agames
    lg = float({"rec": ns["d"][ns["d"].pass_play], "rush": ns["d"][ns["d"].play_type.eq("run")], "pass": ns["d"][ns["d"].dropback]}[kind].yards_gained.mean()); K, W = PR.K[kind], PR.W[kind]
    adj = lambda base: base * np.where(f.d_rate.notna(), 1 + W * (f.d_rate / lg - 1), 1.0)
    share = 1.0 if kind == "pass" else f.n_85 / f.team_n_85.replace(0, np.nan); wind = 1 + PR.WIND_C[kind] * np.maximum(f.wind - 10, 0); rate = (f.yds + K * lg) / (f.n + K)
    def line(me, tc): return PR.MED[kind] * adj(share * (base_pg + b[0] + b[1] * me + b[2] * tc) * rate) * wind
    f["yds_vegas"] = line(f.me, f.tc); f["yds_model"] = line(f.me_model, f.tc_model); f["yds_blend"] = line(0.5 * (f.me + f.me_model), 0.5 * (f.tc + f.tc_model))
    lgc = float(ns["d"][{"rec": ns["d"].pass_play & ns["d"].receiver_player_id.notna(), "rush": ns["d"].play_type.eq("run") & ns["d"].rusher_player_id.notna(), "pass": ns["d"].dropback & ns["d"].passer_player_id.notna()}[kind]][{"rec": "pass_touchdown", "rush": "rush_touchdown", "pass": "pass_touchdown"}[kind]].mean())
    def tdline(me): return f.vol * (f.td + PR.K_TD[kind] * lgc) / (f.n + PR.K_TD[kind]) * (1 + PR.TD_MARGIN[kind] * me)
    f["td_vegas"] = tdline(f.me); f["td_model"] = tdline(f.me_model); f["td_blend"] = tdline(0.5 * (f.me + f.me_model))
    # B. reconciliation to the team's expected points: fit team touchdowns of this kind = a + b x expected points on 2016 to 2018
    tg = f.groupby(["game_id", "posteam", "season"]).agg(act_td=("act_td", "sum"), proj_td=("td_vegas", "sum"), act_yds=("act_yds", "sum"), proj_yds=("yds_vegas", "sum"), exp_pts=("exp_pts", "first")).reset_index()
    fit = tg[tg.season <= 2018]; A = np.c_[np.ones(len(fit)), fit.exp_pts]
    ct = np.linalg.lstsq(A, fit.act_td, rcond=None)[0]; cy = np.linalg.lstsq(A, fit.act_yds, rcond=None)[0]
    tg["team_td_exp"] = ct[0] + ct[1] * tg.exp_pts; tg["team_yds_exp"] = cy[0] + cy[1] * tg.exp_pts
    tg["scale_td"] = (tg.team_td_exp / tg.proj_td.replace(0, np.nan)).clip(0.5, 2.0); tg["scale_yds"] = (tg.team_yds_exp / tg.proj_yds.replace(0, np.nan)).clip(0.5, 2.0)
    f = f.merge(tg[["game_id", "posteam", "scale_td", "scale_yds"]], on=["game_id", "posteam"], how="left")
    for w in [0.25, 0.5, 1.0]:
        f[f"td_recon{int(w*100)}"] = f.td_vegas * (1 + w * (f.scale_td.fillna(1) - 1)); f[f"yds_recon{int(w*100)}"] = f.yds_vegas * (1 + w * (f.scale_yds.fillna(1) - 1))
    print(kind, "team fit: td = %.3f + %.4f x pts; yds = %.1f + %.2f x pts" % (ct[0], ct[1], cy[0], cy[1]), flush=True)
    for col in ["yds_vegas", "yds_model", "yds_blend", "yds_recon25", "yds_recon50", "yds_recon100"]: rows.append({"stat": f"{kind}_yards", "variant": col, **ev(f, col, "act_yds", False)})
    for col in ["td_vegas", "td_model", "td_blend", "td_recon25", "td_recon50", "td_recon100"]: rows.append({"stat": f"{kind}_td", "variant": col, **ev(f, col, "act_td", True)})
    print(pd.DataFrame(rows)[pd.DataFrame(rows).stat.str.startswith(kind)].to_string(), flush=True)
pd.DataFrame(rows).to_csv("reports/props_backtest6.csv", index=False); print("DONE")
