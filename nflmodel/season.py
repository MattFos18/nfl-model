"""Season simulation (23 Sep 2026): win totals, division winners, playoff seeds and the Super Bowl, from the game model.

Every remaining regular-season game gets an expected margin from the game model's own equation (model.py: the fit's
coefficients, training means and intercept as of the week, applied to each team's ratings as of the week), and the
week being priced uses the model's actual predictions for those games (pred_v3, with their forecast and injuries).
Games further out carry no forecast or injury information: wind at the league-typical 7 mph outdoors, no one out.
The rest of the season is then played out many times (margins drawn from the model's residual scale), standings are
settled with the league's order of tiebreakers as far as records go (head-to-head among the tied, division record,
conference record, then a coin flip; the strength-of-victory rules beyond those are not applied), the seeds play
the bracket with the higher seed at home and the Super Bowl on a neutral field. Each team's share of the runs gives
its odds. Backtest: experiments/season_backtest.py (reports/season_backtest.csv), as of several weeks of every
season 2019 to 2025, split 2019-22 / 2023-25 like the rest of the model.
"""
from __future__ import annotations
import numpy as np, pandas as pd
from pathlib import Path
from scipy.stats import norm
from . import model as M

ROOT = Path(__file__).resolve().parent.parent
OUT, REP = ROOT / "data" / "processed", ROOT / "reports"

DIV = {"AFC East": ["BUF", "MIA", "NE", "NYJ"], "AFC North": ["BAL", "CIN", "CLE", "PIT"], "AFC South": ["HOU", "IND", "JAX", "TEN"], "AFC West": ["DEN", "KC", "LAC", "LV"],
       "NFC East": ["DAL", "NYG", "PHI", "WAS"], "NFC North": ["CHI", "DET", "GB", "MIN"], "NFC South": ["ATL", "CAR", "NO", "TB"], "NFC West": ["ARI", "LA", "SEA", "SF"]}
TEAMS = sorted(t for d in DIV.values() for t in d)
IDX = {t: i for i, t in enumerate(TEAMS)}
DIV_OF = {t: d for d, ts in DIV.items() for t in ts}
CONF_OF = {t: d[:3] for t, d in DIV_OF.items()}
DIV_IDX = {d: np.array([IDX[t] for t in ts]) for d, ts in DIV.items()}
CONF_IDX = {c: np.array([IDX[t] for t in TEAMS if CONF_OF[t] == c]) for c in ("AFC", "NFC")}
SAME_DIV = np.array([[DIV_OF[a] == DIV_OF[b] and a != b for b in TEAMS] for a in TEAMS])
SAME_CONF = np.array([[CONF_OF[a] == CONF_OF[b] and a != b for b in TEAMS] for a in TEAMS])
TIE_BAND = 0.07          # a drawn margin this close to zero is a tie (about one game in 230, the league's rate)
WIND_FAR = 7.0           # the game model's stand-in wind for an outdoor game with no forecast yet
# adopted knobs (reports/season_backtest.csv): future-game margins are shrunk toward zero by SHRINK and drawn with the
# model's residual scale times SIGMA_MULT; both 0 / 1.0 until a variant beats them on both windows
SHRINK, SIGMA_MULT = 0.0, 1.0


def playoff_format(season: int) -> int:
    return 7 if season >= 2020 else 6


def _frame() -> pd.DataFrame:
    """The game model's own input frame (features_asof plus trends, injuries and records, prepped), regular season only."""
    f = M.prep(M.with_trends(pd.read_parquet(OUT / "features_asof.parquet")))
    return f[f.game_type == "REG"].copy()


def profiles(f: pd.DataFrame, season: int, week: int) -> dict:
    """Each team's ratings as of `week` of `season`: its row for the first game at or after that week (a bye team's next
    game carries the same games played), else its last row before it. Own offense, own defense, QB, continuity, record."""
    out = {}
    fs = f[f.season == season]
    for t, g in fs.groupby("team"):
        g = g.sort_values("week")
        r = g[g.week >= week]
        row = r.iloc[0] if len(r) else g.iloc[-1]
        out[t] = {"off_epa_play": float(row.off_epa_play), "off_pf": float(row.off_pf), "qb_rating": float(row.qb_rating),
                  "own_def_epa_play": float(row.own_def_epa_play), "own_def_pf": float(row.own_def_pf),
                  "off_continuity": float(row.off_continuity), "def_continuity": float(row.def_continuity), "pct_before": float(row.pct_before),
                  "n_games": float(row.n_games), "asof_week": int(row.week)}
    return out


def fit_asof(pred: pd.DataFrame, season: int, week: int) -> dict:
    """The regression as of the week: coefficients, training means, intercept and residual scale from the prediction
    table's rows for that week (or the latest earlier week of the season, or the last week of the season before)."""
    p = pred[(pred.season == season) & (pred.week <= week) & (pred.game_type == "REG")]
    if not len(p):
        p = pred[(pred.season < season) & (pred.game_type == "REG")]
    row = p.sort_values(["season", "week"]).iloc[-1]
    return {"coef": {k: float(row[f"coef_{k}"]) for k in M.FEATS}, "mean": {k: float(row[f"mean_{k}"]) for k in M.FEATS},
            "intercept": float(row.intercept), "sigma": float(row.sigma_margin), "season": int(row.season), "week": int(row.week)}


def expected_points(pa: dict, pb: dict, fit: dict, home: float, neutral: float, dome: float, div_game: float, game_week: int,
                    wind: float | None = None, overrides: dict | None = None) -> float:
    """Team A's expected points against team B from the model's equation. Situational inputs a future game cannot know
    (weather beyond the forecast, absences) sit at their stand-ins; `overrides` sets any input outright (the tie check)."""
    early = 1.0 if game_week <= M.EARLY_WEEKS else 0.0
    late = 1.0 if game_week >= M.LATE_WEEK else 0.0
    x = {"off_epa_play": pa["off_epa_play"], "def_epa_play": pb["own_def_epa_play"], "off_pf": pa["off_pf"], "def_pf": pb["own_def_pf"], "qb_rating": pa["qb_rating"],
         "home": home, "neutral": neutral, "dome": dome, "wind_out": 0.0 if dome else (WIND_FAR if wind is None else wind), "cold": 0.0, "rain": 0.0, "warm_in_cold": 0.0,
         "div_game": div_game, "qb_out": 0.0, "skill_out_value": 0.0, "opp_skill_out_value": 0.0, "off_snap_out": 0.0, "opp_def_snap_out": 0.0,
         "off_turnover_early": (1.0 - pa["off_continuity"]) * early, "opp_def_turnover_early": (1.0 - pb["def_continuity"]) * early,
         "dead_late": late * (1.0 if pa["pct_before"] <= M.DEAD_PCT else 0.0), "opp_dead_late": late * (1.0 if pb["pct_before"] <= M.DEAD_PCT else 0.0)}
    if overrides:
        x.update(overrides)
    return fit["intercept"] + sum(fit["coef"][k] * (x[k] - fit["mean"][k]) for k in M.FEATS)


def margin_matrices(P: dict, fit: dict, game_week: int, dome_of: dict) -> tuple[np.ndarray, np.ndarray]:
    """MU_home[a, b]: a's expected margin hosting b (a's roof); MU_neutral[a, b]: on a neutral field outdoors."""
    n = len(TEAMS); mh = np.zeros((n, n)); mn = np.zeros((n, n))
    for a in TEAMS:
        for b in TEAMS:
            if a == b:
                continue
            dg = 1.0 if SAME_DIV[IDX[a], IDX[b]] else 0.0
            d = float(dome_of.get(a, 0.0))
            mh[IDX[a], IDX[b]] = expected_points(P[a], P[b], fit, 1.0, 0.0, d, dg, game_week) - expected_points(P[b], P[a], fit, 0.0, 0.0, d, dg, game_week)
            mn[IDX[a], IDX[b]] = expected_points(P[a], P[b], fit, 0.0, 1.0, 0.0, dg, game_week) - expected_points(P[b], P[a], fit, 0.0, 1.0, 0.0, dg, game_week)
    return mh, mn


def _rank_key(pct: np.ndarray, H: np.ndarray, members: np.ndarray, rng, conf_pct: np.ndarray, div_pct: np.ndarray | None) -> np.ndarray:
    """A sortable key (higher is better) for the teams in `members` (shape S x k): win share, then head-to-head share
    among the teams tied on win share, then division share (division races only), then conference share, then a coin."""
    S = pct.shape[0]; k = members.shape[1]
    p = np.take_along_axis(pct, members, axis=1)                                  # S x k
    same = np.abs(p[:, :, None] - p[:, None, :]) < 1e-9                          # S x k x k, tied pairs
    np.einsum("sii->si", same)[:] = False
    Hm = H[np.arange(S)[:, None, None], members[:, :, None], members[:, None, :]]  # S x k x k: wins of i over j
    w = (same * Hm).sum(2); g = (same * (Hm + np.transpose(Hm, (0, 2, 1)))).sum(2)
    h2h = np.where(g > 0, w / np.maximum(g, 1e-9), 0.5)
    cp = np.take_along_axis(conf_pct, members, axis=1)
    dp = np.take_along_axis(div_pct, members, axis=1) if div_pct is not None else np.zeros_like(cp)
    return p * 1e8 + h2h * 1e5 + dp * 1e3 + cp * 10 + rng.random((S, k))


def simulate(season: int, week: int, games: pd.DataFrame, P: dict, fit: dict, pred: pd.DataFrame | None = None, n_sims: int = 5000,
             shrink: float = SHRINK, sigma_mult: float = SIGMA_MULT, seed: int = 0, played_mode: str = "asof") -> dict:
    """Play out the season from `week`. played_mode "asof": games before `week` count as played (their real scores),
    games from `week` on are drawn, whatever their scores (the backtest). "now": every game with a score counts as
    played and only unplayed games are drawn (the live run, mid-week)."""
    rng = np.random.default_rng(seed)
    reg = games[(games.season == season) & (games.game_type == "REG")].copy()
    if played_mode == "asof":
        played = reg[(reg.week < week) & reg.home_score.notna()]; todo = reg[reg.week >= week]
    else:
        played = reg[reg.home_score.notna()]; todo = reg[reg.home_score.isna()]
    n = len(TEAMS); S = n_sims
    W0 = np.zeros(n); H0 = np.zeros((n, n)); L0 = np.zeros(n); T0 = np.zeros(n)
    for r in played.itertuples():
        h, a = IDX[r.home_team], IDX[r.away_team]
        if r.home_score > r.away_score:
            W0[h] += 1; H0[h, a] += 1; L0[a] += 1
        elif r.home_score < r.away_score:
            W0[a] += 1; H0[a, h] += 1; L0[h] += 1
        else:
            W0[h] += 0.5; W0[a] += 0.5; H0[h, a] += 0.5; H0[a, h] += 0.5; T0[h] += 1; T0[a] += 1
    dome_of = {}
    for r in reg.itertuples():
        dome_of[r.home_team] = float(r.dome) if pd.notna(r.dome) else dome_of.get(r.home_team, 0.0)
    # expected margins: the week being priced from the prediction table where it has the game, later games from the equation
    pmap = {}
    if pred is not None:
        pw = pred[(pred.season == season) & (pred.week == week)]
        pmap = dict(zip(pw.game_id, pw.model_spread))
    mus, sig, hs, as_ = [], [], [], []
    mh_cache = {}
    for r in todo.itertuples():
        h, a = IDX[r.home_team], IDX[r.away_team]
        if r.game_id in pmap and pd.notna(pmap[r.game_id]):
            mu = float(pmap[r.game_id])
        else:
            wk = int(r.week)
            if wk not in mh_cache:
                mh_cache[wk] = margin_matrices(P, fit, wk, dome_of)
            mh, mn = mh_cache[wk]
            mu = float(mn[h, a] if (pd.notna(r.neutral) and r.neutral == 1) else mh[h, a]) * (1.0 - shrink)
        mus.append(mu); sig.append(fit["sigma"] * sigma_mult); hs.append(h); as_.append(a)
    G = len(mus); mus = np.array(mus); sig = np.array(sig); hs = np.array(hs, dtype=int); as_ = np.array(as_, dtype=int)
    Z = rng.standard_normal((S, G)) if G else np.zeros((S, 0))
    Mg = mus[None, :] + sig[None, :] * Z
    hw = (Mg > TIE_BAND).astype(np.float32); aw = (Mg < -TIE_BAND).astype(np.float32); tie = 1.0 - hw - aw
    Hm = np.zeros((G, n), dtype=np.float32); Am = np.zeros((G, n), dtype=np.float32)
    Hm[np.arange(G), hs] = 1; Am[np.arange(G), as_] = 1
    W = W0[None, :] + hw @ Hm + aw @ Am + 0.5 * tie @ (Hm + Am)
    H = np.repeat(H0[None, :, :].astype(np.float32), S, axis=0)
    for g in range(G):
        H[:, hs[g], as_[g]] += hw[:, g] + 0.5 * tie[:, g]
        H[:, as_[g], hs[g]] += aw[:, g] + 0.5 * tie[:, g]
    n_games = np.array([((reg.home_team == t) | (reg.away_team == t)).sum() for t in TEAMS], dtype=float)
    pct = W / n_games[None, :]
    div_w = (H * SAME_DIV[None, :, :]).sum(2); div_g = ((H + np.transpose(H, (0, 2, 1))) * SAME_DIV[None, :, :]).sum(2)
    conf_w = (H * SAME_CONF[None, :, :]).sum(2); conf_g = ((H + np.transpose(H, (0, 2, 1))) * SAME_CONF[None, :, :]).sum(2)
    div_pct = np.where(div_g > 0, div_w / np.maximum(div_g, 1e-9), 0.5); conf_pct = np.where(conf_g > 0, conf_w / np.maximum(conf_g, 1e-9), 0.5)
    # division winners
    div_win = np.zeros((S, n), dtype=bool)
    for d, idx in DIV_IDX.items():
        members = np.repeat(idx[None, :], S, axis=0)
        key = _rank_key(pct, H, members, rng, conf_pct, div_pct)
        win = idx[np.argmax(key, axis=1)]
        div_win[np.arange(S), win] = True
    # seeds per conference: division winners by record, then the wild cards
    fmt = playoff_format(season); n_wc = fmt - 4
    seeds = {}
    for c, cidx in CONF_IDX.items():
        winners = np.array([cidx[div_win[s, cidx]] for s in range(S)])          # S x 4
        key = _rank_key(pct, H, winners, rng, conf_pct, None)
        order = np.argsort(-key, axis=1); top4 = np.take_along_axis(winners, order, axis=1)
        others = np.array([cidx[~div_win[s, cidx]] for s in range(S)])         # S x 12
        key2 = _rank_key(pct, H, others, rng, conf_pct, None)
        order2 = np.argsort(-key2, axis=1); wc = np.take_along_axis(others, order2, axis=1)[:, :n_wc]
        seeds[c] = np.concatenate([top4, wc], axis=1)                          # S x fmt
    playoffs = np.zeros((S, n), dtype=bool); bye = np.zeros((S, n), dtype=bool)
    for c in seeds:
        for j in range(fmt):
            playoffs[np.arange(S), seeds[c][:, j]] = True
        bye[np.arange(S), seeds[c][:, 0]] = True
        if fmt == 6:
            bye[np.arange(S), seeds[c][:, 1]] = True
    # the bracket: higher seed hosts, the Super Bowl on a neutral field
    wk_post = int(reg.week.max()) + 1
    mh, mn = mh_cache.get(wk_post) or margin_matrices(P, fit, wk_post, dome_of)
    sigp = fit["sigma"] * sigma_mult

    def game(hi, lo, neutral=False):
        mu = (mn if neutral else mh)[hi, lo] * (1.0 - shrink)
        p = norm.cdf(mu / sigp)
        return np.where(rng.random(S) < p, hi, lo)

    champs = {}
    for c in seeds:
        sd = seeds[c]
        if fmt == 7:
            w27 = game(sd[:, 1], sd[:, 6]); w36 = game(sd[:, 2], sd[:, 5]); w45 = game(sd[:, 3], sd[:, 4])
            alive = np.stack([sd[:, 0], w27, w36, w45], axis=1)                # seed order kept by column
            seed_no = np.stack([np.zeros(S, int), np.where(w27 == sd[:, 1], 1, 6), np.where(w36 == sd[:, 2], 2, 5), np.where(w45 == sd[:, 3], 3, 4)], axis=1)
        else:
            w36 = game(sd[:, 2], sd[:, 5]); w45 = game(sd[:, 3], sd[:, 4])
            alive = np.stack([sd[:, 0], sd[:, 1], w36, w45], axis=1)
            seed_no = np.stack([np.zeros(S, int), np.ones(S, int), np.where(w36 == sd[:, 2], 2, 5), np.where(w45 == sd[:, 3], 3, 4)], axis=1)
        order = np.argsort(seed_no, axis=1)                                     # best seed first
        al = np.take_along_axis(alive, order, axis=1)
        d1 = game(al[:, 0], al[:, 3]); d2 = game(al[:, 1], al[:, 2])
        sn = np.take_along_axis(seed_no, order, axis=1)
        s1 = np.where(d1 == al[:, 0], sn[:, 0], sn[:, 3]); s2 = np.where(d2 == al[:, 1], sn[:, 1], sn[:, 2])
        hi = np.where(s1 < s2, d1, d2); lo = np.where(s1 < s2, d2, d1)
        champs[c] = game(hi, lo)
    sb = game(champs["AFC"], champs["NFC"], neutral=True)
    conf_champ = np.zeros((S, n), dtype=bool); sb_win = np.zeros((S, n), dtype=bool)
    for c in champs:
        conf_champ[np.arange(S), champs[c]] = True
    sb_win[np.arange(S), sb] = True
    teams = []
    for t in TEAMS:
        i = IDX[t]
        teams.append({"team": t, "division": DIV_OF[t], "wins_now": float(W0[i]), "losses_now": int(L0[i]), "ties_now": int(T0[i]), "games_played": int(((played.home_team == t) | (played.away_team == t)).sum()),
                      "games": int(n_games[i]), "wins": float(W[:, i].mean()), "wins_sd": float(W[:, i].std()),
                      "wins_p10": float(np.quantile(W[:, i], 0.1)), "wins_p90": float(np.quantile(W[:, i], 0.9)),
                      "p_div": float(div_win[:, i].mean()), "p_playoffs": float(playoffs[:, i].mean()), "p_bye": float(bye[:, i].mean()),
                      "p_conf": float(conf_champ[:, i].mean()), "p_sb": float(sb_win[:, i].mean())})
    return {"season": season, "week": week, "n_sims": S, "games_left": G, "sigma": float(fit["sigma"] * sigma_mult), "shrink": shrink, "sigma_mult": sigma_mult,
            "fit_week": fit["week"], "teams": teams, "format": fmt}


def actuals(games: pd.DataFrame, season: int) -> dict | None:
    """What happened: final wins, the division winners and playoff field (from the bracket: wild-card hosts and the
    teams that skipped the wild-card round won their divisions), conference champions and the champion."""
    reg = games[(games.season == season) & (games.game_type == "REG")]
    if reg.home_score.isna().any():
        return None
    W = {t: 0.0 for t in TEAMS}
    for r in reg.itertuples():
        if r.home_score > r.away_score: W[r.home_team] += 1
        elif r.home_score < r.away_score: W[r.away_team] += 1
        else: W[r.home_team] += 0.5; W[r.away_team] += 0.5
    post = games[(games.season == season) & (games.game_type != "REG")]
    wc = post[post.game_type == "WC"]; dv = post[post.game_type == "DIV"]; cn = post[post.game_type == "CON"]; sb = post[post.game_type == "SB"]
    if not len(sb) or sb.home_score.isna().any():
        return None
    in_wc = set(wc.home_team) | set(wc.away_team)
    byes = (set(dv.home_team) | set(dv.away_team)) - in_wc
    div_winners = set(wc.home_team) | byes
    playoff = in_wc | byes
    conf_ch = set(sb.home_team) | set(sb.away_team)
    s = sb.iloc[0]; champ = s.home_team if s.home_score > s.away_score else s.away_team
    return {"wins": W, "div": div_winners, "playoffs": playoff, "conf": conf_ch, "champ": champ, "byes": byes}


def score(sim: dict, act: dict) -> dict:
    """Skill scores of one simulation against what happened, with the naive baselines beside them."""
    T = {t["team"]: t for t in sim["teams"]}
    eps = 1e-4
    wins_mae = float(np.mean([abs(T[t]["wins"] - act["wins"][t]) for t in TEAMS]))
    pace = {t: T[t]["wins_now"] + 0.5 * (T[t]["games"] - T[t]["games_played"]) for t in TEAMS}
    pace_mae = float(np.mean([abs(pace[t] - act["wins"][t]) for t in TEAMS]))
    div_brier = float(np.mean([(T[t]["p_div"] - (t in act["div"])) ** 2 for t in TEAMS]))
    div_ll = float(np.mean([-np.log(max(T[t]["p_div"], eps)) for t in act["div"]]))
    # the naive division call: the current leader by win share takes it (ties split)
    lead = {}
    for d, ts in DIV.items():
        top = max(T[t]["wins_now"] for t in ts); tied = [t for t in ts if T[t]["wins_now"] == top]
        for t in ts: lead[t] = (1.0 / len(tied)) if t in tied else 0.0
    div_brier_lead = float(np.mean([(lead[t] - (t in act["div"])) ** 2 for t in TEAMS]))
    div_hit = float(np.mean([max(ts, key=lambda t: T[t]["p_div"]) in act["div"] for ts in DIV.values()]))
    fmt = sim["format"]
    po_brier = float(np.mean([(T[t]["p_playoffs"] - (t in act["playoffs"])) ** 2 for t in TEAMS]))
    po_brier_flat = float(np.mean([(fmt / 16 - (t in act["playoffs"])) ** 2 for t in TEAMS]))
    sb_ll = float(-np.log(max(T[act["champ"]]["p_sb"], eps)))
    conf_ll = float(np.mean([-np.log(max(T[t]["p_conf"], eps)) for t in act["conf"]]))
    rank = int(1 + sum(T[t]["p_sb"] > T[act["champ"]]["p_sb"] for t in TEAMS))
    return {"wins_mae": wins_mae, "pace_mae": pace_mae, "div_brier": div_brier, "div_brier_leader": div_brier_lead, "div_brier_flat": 0.25 * 0.75, "div_ll": div_ll, "div_ll_flat": float(np.log(4)),
            "div_hit": div_hit, "po_brier": po_brier, "po_brier_flat": po_brier_flat, "sb_ll": sb_ll, "sb_ll_flat": float(np.log(32)), "conf_ll": conf_ll, "conf_ll_flat": float(np.log(16)), "champ_rank": rank}


def run_now(n_sims: int = 10000) -> dict:
    """The live simulation for the week being priced, with the game model's predictions for that week's games."""
    from .lines import current_week
    games = pd.read_parquet(OUT / "games.parquet"); pred = pd.read_parquet(OUT / "pred_v3.parquet")
    season, week = current_week(games)
    f = _frame(); P = profiles(f, season, week); fit = fit_asof(pred, season, week)
    sim = simulate(season, week, games, P, fit, pred, n_sims=n_sims, played_mode="now")
    sim["ratings"] = {t: {k: round(v, 6) if isinstance(v, float) else v for k, v in P[t].items()} for t in TEAMS}
    return sim


if __name__ == "__main__":
    import json, sys
    s = run_now(int(sys.argv[1]) if len(sys.argv) > 1 else 10000)
    df = pd.DataFrame(s["teams"]).sort_values("p_sb", ascending=False)
    print(df[["team", "wins_now", "wins", "wins_p10", "wins_p90", "p_div", "p_playoffs", "p_bye", "p_conf", "p_sb"]].round(3).to_string(index=False))
    print(json.dumps({k: v for k, v in s.items() if k not in ("teams", "ratings")}))
