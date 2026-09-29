"""A market-free league scoring-environment input (29 Sep 2026).

The points regression is refit before every week on every played game since 2013, so it learns the league's scoring
level slowly (the intercept is the training mean of points): when league scoring drifts within a season the model
lags. Candidates, all built from our own results (never from a line), as of each week (a week's input uses only games
played before that week):
  pts_prev        last season's league mean points per team-game
  pts_ytd_k{K}    this season's league mean points per team-game over the weeks before this one, shrunk toward
                  pts_prev with K team-games of weight (week 1 equals pts_prev)
  pts_rec_k{K}    the league mean over the last four played weeks (across the season boundary), shrunk the same way
  epa_prev / epa_ytd_k{K} / epa_rec_k{K}   the same three for league offensive EPA per play (team_games.parquet)
K in 64, 128, 256. Each candidate is added, one at a time, to the live points equation (M.FEATS; the blend's ridges
and trees carry it too, as they carry every live input) and separately to the total equation (M.TOTAL_FEATS, read
from the home row of the game frame), then the best pair of each. Scored with M.walk_forward (weekly refit) on
2015-18 (never used for a choice), 2019-22 and 2023-25: team points miss, margin miss, total miss, the 4+ and 5+
spread records, the mean signed total bias (model total minus actual), and the points equation's own team-points
miss and bias (home_pts_eq / away_pts_eq: the equation before the total is shared out by the spread), because a
league-level input is the same number for both teams of a game and cancels in the margin.

Adoption rule: adopted only if the margin miss (points equation) or the total miss (total equation) improves on all
three windows with the team points miss not worse on any; a one- or two-window gain is not adopted.

The trees' cache is read from data/processed but written to the scratch directory (nothing under data/processed
changes). Writes reports/scoring_env.csv and reports/scoring_env.md.
    python -m experiments.scoring_env [--variants base,pts_ytd_k128,...] [--no-epa]
"""
import sys, time, argparse, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import numpy as np, pandas as pd
from nflmodel import model as M, backtest as B
from nflmodel.model import OUT

REP = Path(__file__).resolve().parent.parent / "reports"
CSV, MD = Path(os.environ.get("SCORING_ENV_CSV", REP / "scoring_env.csv")), REP / "scoring_env.md"   # the csv path can be overridden so variants run in parallel and are merged after
# side files (the trees' cache copy, the base run's by-season bias) go to a scratch directory, not the repo
SCRATCH = Path(os.environ.get("SCORING_ENV_SCRATCH", "/tmp/scoring_env"))
BY_SEASON = SCRATCH / "scoring_env_base_by_season.csv"
WINDOWS = {"2015-18": range(2015, 2019), "2019-22": range(2019, 2023), "2023-25": range(2023, 2026)}
KS = (64, 128, 256)
RECENT_WEEKS = 4
GAMES = pd.read_parquet(OUT / "games.parquet")
BASE_FEATS, BASE_TOTAL = list(M.FEATS), list(M.TOTAL_FEATS)
LG_COLS = ["pts_prev"] + [f"pts_ytd_k{k}" for k in KS] + [f"pts_rec_k{k}" for k in KS] + \
          ["epa_prev"] + [f"epa_ytd_k{k}" for k in KS] + [f"epa_rec_k{k}" for k in KS]


def league_levels(tg: pd.DataFrame, slots: pd.DataFrame) -> pd.DataFrame:
    """One row per (season, week) slot with every candidate, from the played team-games before that slot."""
    p = tg[tg.pf.notna()].copy(); p["epa_w"] = p.epa_play * p.plays
    wk = p.groupby(["season", "week"]).agg(pf=("pf", "sum"), n=("pf", "size"), epa=("epa_w", "sum"), plays=("plays", "sum")).reset_index()
    seas = wk.groupby("season").agg(pf=("pf", "sum"), n=("n", "sum"), epa=("epa", "sum"), plays=("plays", "sum"))
    prev_pts = (seas.pf / seas.n).to_dict(); prev_epa = (seas.epa / seas.plays).to_dict()
    slots = slots.drop_duplicates().sort_values(["season", "week"]).reset_index(drop=True)
    wk = wk.set_index(["season", "week"]).sort_index()
    played_slots = list(wk.index)   # ordered (season, week) with games played
    rows = []
    for s, w in zip(slots.season, slots.week):
        lp, le = prev_pts.get(s - 1, np.nan), prev_epa.get(s - 1, np.nan)
        ytd = wk[(wk.index.get_level_values(0) == s) & (wk.index.get_level_values(1) < w)]
        before = [k for k in played_slots if k < (s, w)]
        rec = wk.loc[before[-RECENT_WEEKS:]] if before else wk.iloc[0:0]
        r = {"season": s, "week": w, "pts_prev": lp, "epa_prev": le, "ytd_n": int(ytd.n.sum()), "rec_n": int(rec.n.sum())}
        for k in KS:
            r[f"pts_ytd_k{k}"] = (ytd.pf.sum() + k * lp) / (ytd.n.sum() + k)
            r[f"pts_rec_k{k}"] = (rec.pf.sum() + k * lp) / (rec.n.sum() + k)
            # EPA: the same shrink, K team-games of weight expressed in plays at the league's plays per team-game
            ppg = seas.plays.sum() / seas.n.sum()
            r[f"epa_ytd_k{k}"] = (ytd.epa.sum() + k * ppg * le) / (ytd.plays.sum() + k * ppg)
            r[f"epa_rec_k{k}"] = (rec.epa.sum() + k * ppg * le) / (rec.plays.sum() + k * ppg)
        rows.append(r)
    return pd.DataFrame(rows)


def build_features() -> pd.DataFrame:
    f = M.with_trends(pd.read_parquet(OUT / "features_asof.parquet"))
    tg = pd.read_parquet(OUT / "team_games.parquet", columns=["game_id", "season", "week", "team", "pf", "epa_play", "plays"])
    lv = league_levels(tg, f[["season", "week"]])
    assert lv[LG_COLS].notna().all().all(), "a league level is missing (2012 gives 2013 its previous season)"
    return f.merge(lv[["season", "week"] + LG_COLS], on=["season", "week"], how="left")


_game_frame0 = M._game_frame


def game_frame_lg(f: pd.DataFrame) -> pd.DataFrame:
    """The total equation's game frame plus the league levels (the same for both teams; read from the home row)."""
    g = _game_frame0(f)
    h = f[f.home == 1].set_index("game_id")
    for c in LG_COLS:
        if c in h.columns:
            g[c] = h.loc[g.index, c].values
    return g


def score(pred: pd.DataFrame, seasons) -> dict:
    d = B.join(pred, GAMES)
    d = d[(d.game_type == "REG") & d.season.isin(seasons)]
    pm = B.points_miss(d).set_index("target")
    sp4 = B.summarize_bets(B.grade_spread(d, 4.0)).iloc[0]; sp5 = B.summarize_bets(B.grade_spread(d, 5.0)).iloc[0]
    eq_err = np.concatenate([(d.home_pts_eq - d.home_score).values, (d.away_pts_eq - d.away_score).values])
    return {"team_mae": round(float(pm.loc["team points", "model_mae"]), 4), "margin_mae": round(float(pm.loc["margin", "model_mae"]), 4),
            "total_mae": round(float(pm.loc["total", "model_mae"]), 4), "total_bias": round(float(d.total_err.mean()), 3),
            "ats4": f"{int(sp4.wins)}-{int(sp4.losses)}", "ats5": f"{int(sp5.wins)}-{int(sp5.losses)}",
            "pts_eq_mae": round(float(np.abs(eq_err).mean()), 4), "pts_eq_bias": round(float(eq_err.mean()), 3), "n": int(len(d))}


def run(f: pd.DataFrame, feats_extra: list, total_extra: list) -> tuple[dict, float, pd.DataFrame]:
    M.FEATS = BASE_FEATS + feats_extra; M.TOTAL_FEATS = BASE_TOTAL + total_extra
    t0 = time.time(); out = {}
    try:
        pred = M.walk_forward(f, range(2015, 2026))
    finally:
        M.FEATS, M.TOTAL_FEATS = list(BASE_FEATS), list(BASE_TOTAL)
    for name, seasons in WINDOWS.items():
        out[name] = score(pred, seasons)
    return out, time.time() - t0, pred


def flat(name: str, eq: str, inputs: list, res: dict, secs: float) -> dict:
    r = {"variant": name, "equation": eq, "inputs": " ".join(inputs) if inputs else "", "secs": round(secs, 1)}
    for w, v in res.items():
        for k, x in v.items():
            r[f"{k}_{w}"] = x
    return r


def season_bias(pred: pd.DataFrame) -> pd.DataFrame:
    d = B.join(pred, GAMES); d = d[(d.game_type == "REG")]
    eq_h, eq_a = d.home_pts_eq - d.home_score, d.away_pts_eq - d.away_score
    d = d.assign(eq_bias=(eq_h + eq_a) / 2)
    return d.groupby("season").agg(total_bias=("total_err", "mean"), pts_eq_bias=("eq_bias", "mean"), n=("game_id", "size")).round(3)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variants", default=None, help="comma list of variant names to (re)run; default: every one not yet in the csv")
    ap.add_argument("--no-epa", action="store_true")
    ap.add_argument("--no-md", action="store_true", help="skip the md (a partial, parallel run)")
    a = ap.parse_args()
    # the trees' cache: read the model's, write this run's to the scratch directory (data/processed is not touched)
    M._trees_cache()
    SCRATCH.mkdir(parents=True, exist_ok=True); M.TREES_CACHE = SCRATCH / "trees_cache.parquet"
    if M.TREES_CACHE.exists():   # fits an earlier run of this study made
        M._TC["df"] = pd.concat([M._TC["df"], pd.read_parquet(M.TREES_CACHE)], ignore_index=True).drop_duplicates(["key", "game_id", "team"], keep="last")
    def save_all():   # keep every fit across the variants of one process (the model's save drops keys the last run did not touch)
        out = pd.concat([M._trees_cache()] + M._TC["new"], ignore_index=True).drop_duplicates(["key", "game_id", "team"], keep="last")
        out.to_parquet(M.TREES_CACHE, index=False); M._TC["df"] = out; M._TC["new"] = []
    M.save_trees_cache = save_all
    M._game_frame = game_frame_lg
    f = build_features()
    print(f[["season", "week"] + LG_COLS].drop_duplicates().query("week == 1 or week == 9").to_string(index=False), flush=True)
    cands = [c for c in LG_COLS if not (a.no_epa and c.startswith("epa"))]
    variants = {"base": ([], [])}
    for c in cands:
        variants[f"pts:{c}"] = ([c], []); variants[f"tot:{c}"] = ([], [c])
    done = pd.read_csv(CSV) if CSV.exists() else pd.DataFrame(columns=["variant"])
    todo = [v for v in variants if v not in set(done.variant)] if a.variants is None else a.variants.split(",")
    rows = [r.to_dict() for _, r in done.iterrows() if r.variant not in todo]
    def do(name, fe, te):
        res, secs, pred = run(f, fe, te)
        r = flat(name, "points" if fe and not te else "total" if te and not fe else "both" if fe else "base", fe + te, res, secs)
        print(f"{name:26s} {secs:6.0f}s  " + "  ".join(f"{w}: team {v['team_mae']} margin {v['margin_mae']} total {v['total_mae']} bias {v['total_bias']:+.2f} eq {v['pts_eq_mae']} eqbias {v['pts_eq_bias']:+.2f} 4+ {v['ats4']}" for w, v in res.items()), flush=True)
        rows.append(r); pd.DataFrame(rows).to_csv(CSV, index=False)
        if name == "base":
            season_bias(pred).to_csv(BY_SEASON)
        return r
    for name in todo:
        if name in variants:
            do(name, *variants[name])
    tab = pd.DataFrame(rows).set_index("variant")
    # the best pair for each equation: the two best singles (distinct measures: prev / ytd / rec) by the equation's target
    # miss summed over the three windows, run together
    def best_pair(prefix, target):
        singles = [v for v in tab.index if v.startswith(prefix)]
        base = tab.loc["base"]
        gain = {v: sum(tab.loc[v, f"{target}_{w}"] - base[f"{target}_{w}"] for w in WINDOWS) for v in singles}
        order = sorted(singles, key=lambda v: gain[v]); pick = []
        for v in order:
            kind = v.split(":")[1].rsplit("_k", 1)[0]
            if all(kind != p.split(":")[1].rsplit("_k", 1)[0] for p in pick):
                pick.append(v)
            if len(pick) == 2:
                break
        return [p.split(":")[1] for p in pick]
    if a.variants is None or any(v.startswith("pair") for v in a.variants.split(",")):
        pp = best_pair("pts:", "margin_mae"); pt = best_pair("tot:", "total_mae")
        for name, fe, te in [(f"pair pts:{'+'.join(pp)}", pp, []), (f"pair tot:{'+'.join(pt)}", [], pt)]:
            if name not in tab.index:
                do(name, fe, te)
        # and the two equations' best singles together
        bp, bt = best_pair("pts:", "margin_mae")[:1], best_pair("tot:", "total_mae")[:1]
        name = f"both pts:{bp[0]} tot:{bt[0]}"
        if name not in tab.index:
            do(name, bp, bt)
    if not a.no_md:
        write_md(pd.DataFrame(rows))


def write_md(tab: pd.DataFrame):
    base = tab[tab.variant == "base"].iloc[0]
    W = list(WINDOWS)
    def verdict(r):
        if r.variant == "base":
            return "base"
        tgt = "margin_mae" if r.equation == "points" else "total_mae" if r.equation == "total" else None
        if tgt is None:
            m_ok = all(r[f"margin_mae_{w}"] < base[f"margin_mae_{w}"] for w in W); t_ok = all(r[f"total_mae_{w}"] < base[f"total_mae_{w}"] for w in W)
            team_ok = all(r[f"team_mae_{w}"] <= base[f"team_mae_{w}"] for w in W)
            if m_ok and t_ok and team_ok:
                return "adoptable (margin and total better on all three, team not worse)"
            return "not adopted: " + "; ".join(x for x, ok in [("margin not better on all three", m_ok), ("total not better on all three", t_ok),
                                                              ("team points worse on " + ", ".join(w for w in W if r[f"team_mae_{w}"] > base[f"team_mae_{w}"]), team_ok)] if not ok)
        wins = [w for w in W if r[f"{tgt}_{w}"] < base[f"{tgt}_{w}"]]
        team_ok = all(r[f"team_mae_{w}"] <= base[f"team_mae_{w}"] for w in W)
        if len(wins) == 3 and team_ok:
            return "ADOPTABLE: better on all three, team points not worse"
        if len(wins) == 3:
            return "not adopted: target better on all three but team points worse on " + ", ".join(w for w in W if r[f"team_mae_{w}"] > base[f"team_mae_{w}"])
        return f"not adopted: {tgt.split('_')[0]} better on {len(wins)} of 3" + (f" ({', '.join(wins)})" if wins else "")
    tab = tab.copy(); tab["verdict"] = [verdict(r) for _, r in tab.iterrows()]
    tab.to_csv(CSV, index=False)
    L = ["# A league scoring-environment input (29 Sep 2026)", "",
         "`experiments/scoring_env.py`, `reports/scoring_env.csv`. The points regression's intercept is the training mean of points",
         "since 2013, so it learns the league's scoring level slowly and lags a within-season drift. Candidates built from our own",
         "results only (no line anywhere): last season's league mean points per team-game (`pts_prev`); this season's mean over the",
         "weeks before this one, shrunk toward `pts_prev` with K team-games of weight so week 1 equals `pts_prev` (`pts_ytd_kK`);",
         "the mean over the last four played weeks, across the season boundary, shrunk the same way (`pts_rec_kK`); and the same",
         "three for league offensive EPA per play (`epa_*`). K in 64, 128, 256. Each candidate added, one at a time, to the points",
         "equation (`M.FEATS`; the blend's ridges and trees carry it too) and separately to the total equation (`M.TOTAL_FEATS`),",
         "then the best pair of each and the two equations' best singles together. Walk-forward, weekly refit, as-of only.", "",
         "**Adoption rule (stated before the results):** adopted only if the margin miss (points equation) or the total miss (total",
         "equation) improves on all three windows, 2015-18 (never used for a choice), 2019-22 and 2023-25, with the team points miss",
         "not worse on any. A one- or two-window gain is not adopted.", "",
         "Columns: team, margin and total miss (MAE); total bias, the mean of model total minus actual; 4+ and 5+ the spread record at",
         "that edge; eq miss / eq bias, the points equation's own team points (before the total is shared out by the spread), where a",
         "league-level input shows: it is the same number for both teams of a game, so it cancels in the margin and cannot move the",
         "graded team points, which are the total equation's number shared out by the spread.", ""]
    L += ["| variant | eq | " + " | ".join(f"{w} team / margin / total / total bias / 4+ / eq miss / eq bias" for w in W) + " | secs | verdict |",
          "|---|---|" + "---|" * len(W) + "---|---|"]
    for _, r in tab.iterrows():
        cells = [f"{r[f'team_mae_{w}']:.4f} / {r[f'margin_mae_{w}']:.4f} / {r[f'total_mae_{w}']:.4f} / {r[f'total_bias_{w}']:+.2f} / {r[f'ats4_{w}']} / {r[f'pts_eq_mae_{w}']:.4f} / {r[f'pts_eq_bias_{w}']:+.2f}" for w in W]
        L.append(f"| {r.variant} | {r.equation} | " + " | ".join(cells) + f" | {r.secs:.0f} | {r.verdict} |")
    L += ["", "## Change against the base (miss deltas; negative is better)", "",
          "| variant | " + " | ".join(f"d team {w} | d margin {w} | d total {w}" for w in W) + " | d eq miss (3 windows) |", "|---|" + "---|" * (3 * len(W)) + "---|"]
    for _, r in tab.iterrows():
        if r.variant == "base":
            continue
        cells = [f"{r[f'team_mae_{w}'] - base[f'team_mae_{w}']:+.4f} | {r[f'margin_mae_{w}'] - base[f'margin_mae_{w}']:+.4f} | {r[f'total_mae_{w}'] - base[f'total_mae_{w}']:+.4f}" for w in W]
        eq = " / ".join(f"{r[f'pts_eq_mae_{w}'] - base[f'pts_eq_mae_{w}']:+.4f}" for w in W)
        L.append(f"| {r.variant} | " + " | ".join(cells) + f" | {eq} |")
    if BY_SEASON.exists():
        s = pd.read_csv(BY_SEASON)
        L += ["", "## The drift the study is about: the base model's signed bias by season (model minus actual, regular season)", "",
              "| season | total bias | points-equation bias per team | games |", "|---|---|---|---|"]
        for _, r in s.iterrows():
            L.append(f"| {int(r.season)} | {r.total_bias:+.2f} | {r.pts_eq_bias:+.2f} | {int(r.n)} |")
    ad = tab[tab.verdict.str.startswith("ADOPTABLE") | tab.verdict.str.startswith("adoptable")]
    L += ["", "## Reading the points-equation rows", "",
          "A league-level input is the same number for both teams, so in the ridge it cancels in the margin exactly; what moves the",
          "margin is the other coefficients re-settling around it and the boosted trees in the blend, which do not cancel. The",
          "margin gains are hundredths of a point at most. The `pair tot:` and `both` rows refit the trees where the singles read",
          "the cache, and the base inputs refit on this machine moved the margin miss by 0.0002 (9.9493 against 9.9491 on 2015-18),",
          "so a 2023-25 margin gain of 0.001 or less is inside the trees' own noise. The 4+ spread record, which the rule does not",
          "score, is worse on every window for `pts_rec_k64` (66-56 / 79-54 / 44-28 against 68-55 / 83-54 / 44-26) and about level",
          "for `epa_ytd_k64` and the pair. In the total equation, where the input would matter most,",
          "every candidate is worse on 2015-18: it adds a positive bias there (+0.4 to +1.1 against +0.35) while trimming the",
          "2023-25 miss and bias, the same shape as the passing rolling factor for props (fixes the late drift, costs the early",
          "windows).", "", "## Verdict", ""]
    if len(ad):
        L.append("Variants meeting the letter of the rule: " + ", ".join(f"`{v}`" for v in ad.variant) + ". Each passes only at one k (its k128 and k256")
        L.append("siblings fail), none wins more spread bets at 4+, and the 2023-25 margin gains are within the trees' refit noise, so the")
        L.append("pass is not a stable effect. Recommendation: not adopted; the points equation's intercept keeps carrying the league level. No")
        L.append("total-equation candidate passes.")
    else:
        L.append("No variant meets the rule: none improves its equation's target miss on all three windows with the team points miss not worse. Not adopted.")
    MD.write_text("\n".join(L) + "\n")
    print(MD.read_text())


if __name__ == "__main__":
    main()
