"""Everything not yet in the model (25 Sep 2026, Matt: "does this factor in clutch ... go all possibilities and do it").
Our own data only. Each signal is built per team-game, then carried as of each game (an exponentially weighted mean of
the team's earlier games, half-life 8 games, across seasons; the equation's intercept carries the league level), own and the opponent's
matching side, and added to the live equation one family at a time. Walk-forward, weekly refit, scored by the team
points and margin miss and the 4+ record on 2015-18 (never used for a choice), 2019-22 and 2023-25.

Families
  clutch      EPA per play in the fourth quarter or overtime within 8 points, offense and defense; share of one-score
              games won (the "knows how to win close games" idea)
  third       third-down conversion rate, offense and defense
  redzone     red-zone touchdown rate per trip, offense and defense
  explosive   explosive-play rate, offense and defense
  sacks       sack rate taken and made
  giveaways   turnover rate, offense and defense
  fumbleluck  share of the team's own fumbles it lost (luck: should regress)
  penalties   penalty yards per play, offense and defense
  field       average starting field position, offense and defense
  tempo       seconds per play
  fourth      fourth-down attempts per game (aggressiveness)
  ngs         Next Gen Stats: receivers' separation, rushing yards over expected per carry, QB time to throw, CPOE
  streak      wins in a row (or losses, negative) coming in
  letdown     won the last game by 17+ (letdown spot)
  revenge     lost the last meeting with this opponent
  ot_short    played overtime last game on a short week
  altitude    visiting Denver
Writes reports/new_signals.csv."""
import sys, glob
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import numpy as np, pandas as pd
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from nflmodel import model as M
from nflmodel.model import OUT
from nflmodel.features import RAW

REP = Path(__file__).resolve().parent.parent / "reports"
HL = 8


def clutch_frame() -> pd.DataFrame:
    fr = []
    for f in sorted(glob.glob(str(RAW / "pbp" / "play_by_play_*.parquet"))):
        p = pd.read_parquet(f, columns=["game_id", "qtr", "score_differential", "epa", "posteam", "defteam", "play_type", "fumble", "fumble_lost"])
        p = p[p.play_type.isin(["pass", "run"]) & p.epa.notna()]
        lc = p[(p.qtr >= 4) & (p.score_differential.abs() <= 8)]
        o = lc.groupby(["game_id", "posteam"]).epa.agg(["sum", "count"]).rename(columns={"sum": "lc_epa", "count": "lc_n"}).reset_index().rename(columns={"posteam": "team"})
        d = lc.groupby(["game_id", "defteam"]).epa.agg(["sum", "count"]).rename(columns={"sum": "lcd_epa", "count": "lcd_n"}).reset_index().rename(columns={"defteam": "team"})
        fu = p.groupby(["game_id", "posteam"]).agg(fum=("fumble", "sum"), fum_lost=("fumble_lost", "sum")).reset_index().rename(columns={"posteam": "team"})
        fr.append(o.merge(d, on=["game_id", "team"], how="outer").merge(fu, on=["game_id", "team"], how="outer"))
    return pd.concat(fr, ignore_index=True)


def ngs_frame() -> pd.DataFrame:
    rec = pd.read_parquet(RAW / "ngs_rec" / "ngs_receiving.parquet"); rec = rec[rec.week > 0]
    rec = rec.assign(sep_w=rec.avg_separation * rec.targets).groupby(["season", "week", "team_abbr"]).agg(sep_w=("sep_w", "sum"), tg=("targets", "sum")).reset_index()
    ru = pd.read_parquet(RAW / "ngs_rush" / "ngs_rushing.parquet"); ru = ru[ru.week > 0]
    ru = ru.groupby(["season", "week", "team_abbr"]).agg(ryoe=("rush_yards_over_expected", "sum"), ra=("rush_attempts", "sum")).reset_index()
    pa = pd.read_parquet(RAW / "ngs" / "ngs_passing.parquet"); pa = pa[pa.week > 0]
    pa = pa.assign(ttt_w=pa.avg_time_to_throw * pa.attempts).groupby(["season", "week", "team_abbr"]).agg(ttt_w=("ttt_w", "sum"), att=("attempts", "sum")).reset_index()
    n = rec.merge(ru, on=["season", "week", "team_abbr"], how="outer").merge(pa, on=["season", "week", "team_abbr"], how="outer")
    n["team"] = n.team_abbr.replace({"LAR": "LA", "OAK": "LV", "SD": "LAC", "STL": "LA", "JAC": "JAX"})
    return n


def build_raw() -> pd.DataFrame:
    tg = pd.read_parquet(OUT / "team_games.parquet"); tb = pd.read_parquet(OUT / "team_box.parquet")
    g = pd.read_parquet(OUT / "games.parquet")
    d = tg[["game_id", "season", "week", "game_type", "team", "opp", "pf", "pa", "home", "rest", "third_conv", "def_third_conv", "rz_td_rate", "def_rz_td_rate",
            "explosive_rate", "def_explosive_rate", "sack_rate", "def_sack_rate", "turnover_rate", "def_turnover_rate", "avg_start_ytg", "def_avg_start_ytg",
            "sec_per_play", "cpoe", "plays", "def_plays"]].copy()
    b = tb[["game_id", "team", "off_penalty_yards", "def_penalty_yards", "off_fourth_conv", "off_fourth_fail"]]
    d = d.merge(b, on=["game_id", "team"], how="left")
    d["pen_off"] = d.off_penalty_yards / d.plays.replace(0, np.nan); d["pen_def"] = d.def_penalty_yards / d.def_plays.replace(0, np.nan)
    d["fourth_att"] = d.off_fourth_conv + d.off_fourth_fail
    c = clutch_frame(); d = d.merge(c, on=["game_id", "team"], how="left")
    n = ngs_frame(); d = d.merge(n[["season", "week", "team", "sep_w", "tg", "ryoe", "ra", "ttt_w", "att"]], on=["season", "week", "team"], how="left")
    d["margin"] = d.pf - d.pa; d["close"] = (d.margin.abs() <= 8).astype(float); d["close_win"] = np.where(d.close == 1, (d.margin > 0) + 0.5 * (d.margin == 0), np.nan)
    d = d.sort_values(["team", "season", "week"]).reset_index(drop=True)
    ot = g.set_index("game_id").overtime
    d["ot"] = d.game_id.map(ot).fillna(0)
    return d


def asof(d: pd.DataFrame) -> pd.DataFrame:
    """Each signal as of the game: EW mean of earlier games (ratios as EW sums over EW sums), minus the league's."""
    d = d.copy(); grp = d.groupby("team")
    def ew(num, den=None):
        if den is None:
            return grp[num].transform(lambda s: s.shift(1).ewm(halflife=HL, ignore_na=True).mean())
        a = grp[num].transform(lambda s: s.shift(1).fillna(0).ewm(halflife=HL).mean()); b = grp[den].transform(lambda s: s.shift(1).fillna(0).ewm(halflife=HL).mean())
        return a / b.replace(0, np.nan)
    S = {}
    S["lc_off"] = ew("lc_epa", "lc_n"); S["lc_def"] = ew("lcd_epa", "lcd_n"); S["close_win"] = ew("close_win")
    for c in ["third_conv", "def_third_conv", "rz_td_rate", "def_rz_td_rate", "explosive_rate", "def_explosive_rate", "sack_rate", "def_sack_rate",
              "turnover_rate", "def_turnover_rate", "avg_start_ytg", "def_avg_start_ytg", "sec_per_play", "pen_off", "pen_def", "fourth_att", "cpoe"]:
        S[c] = ew(c)
    S["fum_luck"] = ew("fum_lost", "fum"); S["sep"] = ew("sep_w", "tg"); S["ryoe"] = ew("ryoe", "ra"); S["ttt"] = ew("ttt_w", "att")
    out = d[["game_id", "season", "week", "team", "opp", "home", "rest"]].copy()
    for k, v in S.items():
        out[k] = v.values
        out[k] = out[k].fillna(0.0)
    # situational
    res = d.assign(w=np.sign(d.margin))
    def streak(s):
        out, cur = [], 0
        for x in s:
            out.append(cur); cur = (cur + 1 if cur >= 0 else 1) if x > 0 else ((cur - 1 if cur <= 0 else -1) if x < 0 else 0)
        return out
    out["streak"] = res.groupby("team").w.transform(lambda s: pd.Series(streak(s.values), index=s.index))
    out["letdown"] = res.groupby("team").margin.transform(lambda s: (s.shift(1) >= 17).astype(float))
    out["ot_short"] = ((d.groupby("team").ot.shift(1).fillna(0) > 0) & (d.rest <= 6)).astype(float).values
    last = d.sort_values(["season", "week"]).groupby(["team", "opp"]).margin.shift(1)
    out["revenge"] = (last.reindex(d.index) < 0).astype(float).values
    return out


FAM = {"clutch": ["lc_off", "lc_def", "close_win"], "third": ["third_conv", "def_third_conv"], "redzone": ["rz_td_rate", "def_rz_td_rate"],
       "explosive": ["explosive_rate", "def_explosive_rate"], "sacks": ["sack_rate", "def_sack_rate"], "giveaways": ["turnover_rate", "def_turnover_rate"],
       "fumbleluck": ["fum_luck"], "penalties": ["pen_off", "pen_def"], "field": ["avg_start_ytg", "def_avg_start_ytg"], "tempo": ["sec_per_play"],
       "fourth": ["fourth_att"], "ngs": ["sep", "ryoe", "ttt", "cpoe"], "streak": ["streak"], "letdown": ["letdown"], "revenge": ["revenge"],
       "ot_short": ["ot_short"], "altitude": ["altitude"]}
# the opponent's matching side: own offense against the opponent's defense, and the opponent's own form
OPP_OF = {"lc_off": "lc_def", "lc_def": "lc_off", "third_conv": "def_third_conv", "def_third_conv": "third_conv", "rz_td_rate": "def_rz_td_rate", "def_rz_td_rate": "rz_td_rate",
          "explosive_rate": "def_explosive_rate", "def_explosive_rate": "explosive_rate", "sack_rate": "def_sack_rate", "def_sack_rate": "sack_rate",
          "turnover_rate": "def_turnover_rate", "def_turnover_rate": "turnover_rate", "avg_start_ytg": "def_avg_start_ytg", "def_avg_start_ytg": "avg_start_ytg",
          "pen_off": "pen_def", "pen_def": "pen_off", "close_win": "close_win", "fum_luck": "fum_luck", "sec_per_play": "sec_per_play", "fourth_att": "fourth_att",
          "sep": "sep", "ryoe": "ryoe", "ttt": "ttt", "cpoe": "cpoe", "streak": "streak", "letdown": "letdown", "revenge": "revenge", "ot_short": "ot_short"}


def main():
    raw = build_raw(); A = asof(raw)
    o = A.rename(columns={c: "o_" + c for c in OPP_OF}).rename(columns={"team": "opp", "opp": "team"})[["game_id", "team"] + ["o_" + c for c in OPP_OF]]
    A = A.merge(o, on=["game_id", "team"], how="left")
    f = M.prep(M.with_trends(pd.read_parquet(OUT / "features_asof.parquet")))
    f = f.merge(A.drop(columns=["season", "week", "opp", "home", "rest"]), on=["game_id", "team"], how="left")
    f["altitude"] = ((f.opp == "DEN") & (f.home == 0)).astype(float); f["o_altitude"] = 0.0
    newc = [c for c in A.columns if c not in ("game_id", "season", "week", "team", "opp", "home", "rest")] + ["altitude"]
    f[newc] = f[newc].fillna(0.0)
    variants = {"base": []}
    for k, cols in FAM.items():
        variants[k] = cols + ["o_" + OPP_OF[c] if c in OPP_OF else None for c in cols]
        variants[k] = [c for c in variants[k] if c and c in f.columns and c != "o_altitude"]
    variants["all"] = sorted(set(sum(variants.values(), [])))
    played = f[f.pf.notna()]; rows = []
    for s in range(2015, 2026):
        for wk in sorted(f[f.season == s].week.unique()):
            train = played[(played.season >= 2013) & ((played.season < s) | ((played.season == s) & (played.week < wk)))]
            test = f[(f.season == s) & (f.week == wk)]
            h = test[test.home == 1].set_index("game_id"); a = test[test.home == 0].set_index("game_id"); ids = h.index.intersection(a.index)
            if len(ids) == 0:
                continue
            g = pd.DataFrame({"game_id": ids, "season": s, "week": wk, "hs": h.loc[ids, "pf"].values, "as_": a.loc[ids, "pf"].values})
            for name, extra in variants.items():
                cols = list(M.FEATS) + extra
                m = make_pipeline(StandardScaler(), Ridge(alpha=10.0)).fit(train[cols].values, train.pf.values)
                g[f"h_{name}"] = m.predict(h.loc[ids, cols].values); g[f"a_{name}"] = m.predict(a.loc[ids, cols].values)
            rows.append(g)
        print("priced", s, flush=True)
    p = pd.concat(rows, ignore_index=True)
    gm = pd.read_parquet(OUT / "games.parquet")[["game_id", "game_type", "result", "spread_line"]]
    p = p.merge(gm, on="game_id"); p = p[(p.game_type == "REG") & p.result.notna()]
    p.to_parquet(REP / "new_signals_preds.parquet", index=False)
    W = {"2015-18": (2015, 2018), "2019-22": (2019, 2022), "2023-25": (2023, 2025)}; out = []
    for name in variants:
        r = {"variant": name, "inputs": " ".join(variants[name]) if name != "all" else "every family"}
        for w, (a_, b_) in W.items():
            d = p[p.season.between(a_, b_)]
            r[f"team_{w}"] = round(float(pd.concat([(d[f"h_{name}"] - d.hs).abs(), (d[f"a_{name}"] - d.as_).abs()]).mean()), 4)
            sp = d[f"h_{name}"] - d[f"a_{name}"]; r[f"margin_{w}"] = round(float((sp - d.result).abs().mean()), 4)
            x = d[d.spread_line.notna() & (d.week <= 17)]; e = (x[f"h_{name}"] - x[f"a_{name}"]) - x.spread_line; bb = x[e.abs() >= 4]; c = (bb.result - bb.spread_line) * np.sign(e[e.abs() >= 4])
            r[f"4+_{w}"] = f"{int((c > 0).sum())}-{int((c < 0).sum())}"
        out.append(r)
    o = pd.DataFrame(out); b0 = o.iloc[0]
    for w in W:
        o[f"d_margin_{w}"] = (o[f"margin_{w}"] - b0[f"margin_{w}"]).round(4); o[f"d_team_{w}"] = (o[f"team_{w}"] - b0[f"team_{w}"]).round(4)
    o["better_all3"] = [(all(r[f"d_margin_{w}"] < 0 for w in W) and all(r[f"d_team_{w}"] <= 0 for w in W)) for _, r in o.iterrows()]
    o.to_csv(REP / "new_signals.csv", index=False)
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
    print(o[["variant"] + [f"d_team_{w}" for w in W] + [f"d_margin_{w}" for w in W] + [f"4+_{w}" for w in W] + ["better_all3"]].to_string(index=False))


if __name__ == "__main__":
    main()
