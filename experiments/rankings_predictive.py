"""Are the player rankings predictive, out of sample? (29 Sep 2026)

The Players tab ranks players by a decayed, shrunk EPA per play as of the week (players.PlayerValues, DEFAULT: 0.985 a
game, k 480 plays, replacement level at the 10th percentile) and, for defenders, by their group's recipe
(positions.role_rates). This study asks, for every player-week in 2019-2025 (weeks 2..18), how well the value as of
that week predicts what the player does over his NEXT 4 games in that role, against the plain alternatives:

  value          the live value (PlayerValues.value with DEFAULT; role_rates for defenders)
  last4/8/17     his last n games' EPA per play, unshrunk (any season)
  season_to_date season-to-date EPA per play (games this season before the week)
  last_season    last season's EPA per play
  d{decay}_k{k}  the live value at other knobs: decay {0.97, 0.985, 1.0} x k {120, 240, 480, 960}
  def_plain_*    defenders only: the same decayed, shrunk EPA per snap on the summed value components (what the
                 skill players get), with the page's DEF_DECAY / DEF_K / DEF_FADE as one more cell

A predictor with no history (a rookie's last season, a player's first week) is the role's replacement level, the
same prior the value shrinks to, so every predictor is scored on the same player-weeks.

Outcome: the next 4 games the player plays in that role in the same season (regular season and playoffs), all four
required, with at least N plays over them (passer 80, rusher 20, receiver 12, defender 100 snaps): EPA per play over
those games (plays-weighted) and total EPA.

Metrics per role and window (2019-22, 2023-25):
  corr        plays-weighted Pearson correlation of the predictor with next-4 EPA per play (weights: next-4 plays)
  mae         plays-weighted mean absolute error of the predictor against next-4 EPA per play
  spearman    Spearman rank correlation of predictor and next-4 EPA per play, per week among regulars (players with
              100+ plays in the window), averaged over weeks (weighted by players that week)
  corr_total, spearman_total   the same for next-4 total EPA
  corr_own, spearman_own       defenders: the same against the recipe's own target per snap (coverage only for CB;
              coverage plus half the rest for S and IDL; everything plus 0.75 a credited play for LB; everything for
              EDGE), since role_rates does not estimate plain EPA per snap for every group
  churn       mean absolute change in rank, week to week, of the week's top 40 by the predictor among players active
              that season (a game in the season before the week); a player who drops out of the ranking is skipped

Nothing is fit on 2023-25: a knob is a candidate only if it beats DEFAULT on both windows. No market data. As-of
only: a week's predictor uses games before that week.

Writes reports/rankings_predictive.csv and reports/rankings_predictive.md.
Usage: python -m experiments.rankings_predictive [--skip-defenders] [--report-only]
"""
from __future__ import annotations
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import numpy as np, pandas as pd
from scipy.stats import spearmanr
from nflmodel.features import OUT
from nflmodel.players import PlayerValues, DEFAULT
from nflmodel.positions import defender_roles, role_rates, ROLE_SPEC, DEF_DECAY, DEF_FADE, DEF_K, DEF_W, REPL_PCT

ROOT = Path(__file__).resolve().parent.parent
WINDOWS = {"2019-22": (2019, 2022), "2023-25": (2023, 2025)}
SEASONS = range(2019, 2026)
WEEKS = range(2, 19)
HORIZON = 4
MIN_PLAYS = {"passer": 80, "rusher": 20, "receiver": 12, "EDGE": 100, "IDL": 100, "LB": 100, "CB": 100, "S": 100}
DECAYS = [0.97, 0.985, 1.0]
KS = [60.0, 120.0, 240.0, 480.0, 960.0]   # 60 is beyond the asked grid: added because 120, its edge, won everywhere
TRAIL = [4, 8, 17]
REGULAR_PLAYS = 100
TOP_N = 40
DEF_ROLES = list(ROLE_SPEC)


def knob_name(decay: float, k: float) -> str:
    return f"d{decay:g}_k{k:g}"


def build_rows(g: pd.DataFrame, role: str, prior: dict, decays, ks, fade: float = 1.0) -> pd.DataFrame:
    """One row per (player, season, week) with the next-4 outcome and every history-based predictor. `g` is the
    role's game rows (player_id, season, week, plays, epa); `prior[season]` the replacement level for that season."""
    g = g.sort_values(["player_id", "season", "week"]).reset_index(drop=True)
    n_min = MIN_PLAYS[role]
    rows = []
    for pid, idx in g.groupby("player_id").indices.items():
        se = g.season.values[idx]; wk = g.week.values[idx]; pl = g.plays.values[idx].astype(float); ep = g.epa.values[idx].astype(float)
        n = len(idx)
        key = se * 100 + wk
        cpl = np.concatenate([[0.0], np.cumsum(pl)]); cep = np.concatenate([[0.0], np.cumsum(ep)])
        # decayed sums after j games, per decay (state arrays; j = 0 is nothing seen)
        states = {}
        for d in decays:
            num = np.zeros(n + 1); den = np.zeros(n + 1)
            for j in range(n):
                f = 1.0
                if fade != 1.0 and j > 0 and se[j] != se[j - 1]:
                    f = fade ** (se[j] - se[j - 1])   # a season boundary: fade everything seen before it
                num[j + 1] = num[j] * d * f + ep[j]; den[j + 1] = den[j] * d * f + pl[j]
            states[d] = (num, den)
        seasons_here = np.unique(se[(se >= SEASONS.start) & (se < SEASONS.stop)])
        for s in seasons_here:
            pr = prior[s]
            for w in WEEKS:
                p = int(np.searchsorted(key, s * 100 + w))          # games before (s, w)
                q = p + HORIZON                                      # the next 4 games
                if q > n or se[q - 1] != s:
                    continue                                         # not four more games this season
                nxt_pl = cpl[q] - cpl[p]; nxt_ep = cep[q] - cep[p]
                if nxt_pl < n_min:
                    continue
                r = {"player_id": pid, "season": s, "week": w, "games_before": p, "next_plays": nxt_pl, "next_epa": nxt_ep, "y": nxt_ep / nxt_pl}
                for t in TRAIL:
                    a = max(0, p - t); tp = cpl[p] - cpl[a]
                    r[f"last{t}"] = (cep[p] - cep[a]) / tp if tp > 0 else pr
                s0 = int(np.searchsorted(key, s * 100)); tp = cpl[p] - cpl[s0]
                r["season_to_date"] = (cep[p] - cep[s0]) / tp if tp > 0 else pr
                l0 = int(np.searchsorted(key, (s - 1) * 100)); l1 = s0; tp = cpl[l1] - cpl[l0]
                r["last_season"] = (cep[l1] - cep[l0]) / tp if tp > 0 else pr
                for d in decays:
                    num, den = states[d]
                    for k in ks:
                        r[knob_name(d, k)] = (num[p] + k * pr) / (den[p] + k)
                rows.append(r)
    return pd.DataFrame(rows)


def wcorr(x, y, w) -> float:
    w = np.asarray(w, float); x = np.asarray(x, float); y = np.asarray(y, float)
    mx = np.average(x, weights=w); my = np.average(y, weights=w)
    cov = np.average((x - mx) * (y - my), weights=w); vx = np.average((x - mx) ** 2, weights=w); vy = np.average((y - my) ** 2, weights=w)
    return float(cov / np.sqrt(vx * vy)) if vx > 0 and vy > 0 else float("nan")


def weekly_spearman(d: pd.DataFrame, pred: str, ycol: str) -> float:
    num = den = 0.0
    for _, g in d.groupby(["season", "week"]):
        if len(g) < 10:
            continue
        rho = spearmanr(g[pred], g[ycol]).correlation
        if rho == rho:
            num += rho * len(g); den += len(g)
    return num / den if den else float("nan")


def churn(ranks: pd.DataFrame, pred: str, seasons: tuple) -> float:
    """Mean absolute week-to-week rank change of the top 40 by `pred`. `ranks`: one row per (player, season, week) of
    active players with the predictor columns; rank 1 is the best."""
    r = ranks[ranks.season.between(*seasons)]
    tot = cnt = 0
    for s, gs in r.groupby("season"):
        by_week = {w: g for w, g in gs.groupby("week")}
        for w in WEEKS:
            if w not in by_week or w + 1 not in by_week:
                continue
            a = by_week[w].sort_values(pred, ascending=False).reset_index(drop=True)
            b = by_week[w + 1].sort_values(pred, ascending=False).reset_index(drop=True)
            ra = dict(zip(a.player_id, np.arange(1, len(a) + 1))); rb = dict(zip(b.player_id, np.arange(1, len(b) + 1)))
            top = a.player_id.head(TOP_N)
            diffs = [abs(rb[p] - ra[p]) for p in top if p in rb]
            tot += sum(diffs); cnt += len(diffs)
    return tot / cnt if cnt else float("nan")


def active_ranks(g: pd.DataFrame, rows_pred: pd.DataFrame, role: str, prior: dict, decays, ks, fade: float = 1.0) -> pd.DataFrame:
    """Every (player, season, week) where the player has a game in that season before the week, with the predictors
    as of the week (the ranking's population; the outcome is not needed here)."""
    g = g.sort_values(["player_id", "season", "week"]).reset_index(drop=True)
    rows = []
    for pid, idx in g.groupby("player_id").indices.items():
        se = g.season.values[idx]; wk = g.week.values[idx]; pl = g.plays.values[idx].astype(float); ep = g.epa.values[idx].astype(float)
        n = len(idx); key = se * 100 + wk
        cpl = np.concatenate([[0.0], np.cumsum(pl)]); cep = np.concatenate([[0.0], np.cumsum(ep)])
        states = {}
        for d in decays:
            num = np.zeros(n + 1); den = np.zeros(n + 1)
            for j in range(n):
                f = 1.0
                if fade != 1.0 and j > 0 and se[j] != se[j - 1]:
                    f = fade ** (se[j] - se[j - 1])
                num[j + 1] = num[j] * d * f + ep[j]; den[j + 1] = den[j] * d * f + pl[j]
            states[d] = (num, den)
        for s in np.unique(se[(se >= SEASONS.start) & (se < SEASONS.stop)]):
            pr = prior[s]; s0 = int(np.searchsorted(key, s * 100))
            for w in WEEKS:
                p = int(np.searchsorted(key, s * 100 + w))
                if p == s0:
                    continue        # no game this season yet
                r = {"player_id": pid, "season": s, "week": w}
                for t in TRAIL:
                    a = max(0, p - t); tp = cpl[p] - cpl[a]; r[f"last{t}"] = (cep[p] - cep[a]) / tp if tp > 0 else pr
                tp = cpl[p] - cpl[s0]; r["season_to_date"] = (cep[p] - cep[s0]) / tp if tp > 0 else pr
                l0 = int(np.searchsorted(key, (s - 1) * 100)); tp = cpl[s0] - cpl[l0]; r["last_season"] = (cep[s0] - cep[l0]) / tp if tp > 0 else pr
                for d in decays:
                    num, den = states[d]
                    for k in ks:
                        r[knob_name(d, k)] = (num[p] + k * pr) / (den[p] + k)
                rows.append(r)
    return pd.DataFrame(rows)


def score(role: str, rows: pd.DataFrame, ranks: pd.DataFrame, preds: list, plays_by_player: pd.DataFrame) -> list:
    out = []
    for wname, (a, b) in WINDOWS.items():
        d = rows[rows.season.between(a, b)]
        reg = plays_by_player[(plays_by_player.season.between(a, b))].groupby("player_id").plays.sum()
        regulars = set(reg[reg >= REGULAR_PLAYS].index)
        dr = d[d.player_id.isin(regulars)]
        for p in preds:
            if p not in d.columns:
                continue
            out.append({"role": role, "window": wname, "predictor": p, "n": int(len(d)), "n_regular_weeks": int(len(dr)),
                        "corr": round(wcorr(d[p], d.y, d.next_plays), 4), "mae": round(float(np.average(np.abs(d[p] - d.y), weights=d.next_plays)), 4),
                        "spearman": round(weekly_spearman(dr, p, "y"), 4),
                        "corr_total": round(float(np.corrcoef(d[p], d.next_epa)[0, 1]), 4), "spearman_total": round(weekly_spearman(dr, p, "next_epa"), 4),
                        "churn_top40": round(churn(ranks, p, (a, b)), 2),
                        **({"corr_own": round(wcorr(d[p], d.y_own, d.next_plays), 4), "spearman_own": round(weekly_spearman(dr, p, "y_own"), 4)} if "y_own" in d.columns else {})})
    return out


def skill() -> list:
    pg = pd.read_parquet(OUT / "player_games.parquet")
    pg = pg[pg.plays > 0]
    pv = PlayerValues(pg, DEFAULT["decay"], DEFAULT["k"], DEFAULT["pct"])
    res = []
    for role in ["passer", "rusher", "receiver"]:
        t0 = time.time()
        g = pg[pg.role == role][["player_id", "season", "week", "plays", "epa"]]
        prior = {s: pv.prior(role, s) for s in SEASONS}
        rows = build_rows(g, role, prior, DECAYS, KS)
        # the live value from the page's own class, as a check on the vectorised grid cell at DEFAULT
        rows["value"] = [pv.value(pid, role, int(s), int(w))[0] for pid, s, w in zip(rows.player_id, rows.season, rows.week)]
        gap = float(np.abs(rows.value - rows[knob_name(DEFAULT["decay"], DEFAULT["k"])]).max())
        assert gap < 1e-9, f"{role}: grid cell at DEFAULT differs from PlayerValues.value by {gap}"
        ranks = active_ranks(g, rows, role, prior, DECAYS, KS); ranks["value"] = ranks[knob_name(DEFAULT["decay"], DEFAULT["k"])]
        preds = ["value"] + [f"last{t}" for t in TRAIL] + ["season_to_date", "last_season"] + [knob_name(d, k) for d in DECAYS for k in KS]
        res += score(role, rows, ranks, preds, g)
        print(f"{role}: {len(rows)} player-weeks, {len(ranks)} ranking rows, {time.time() - t0:.0f}s", flush=True)
    return res


def defenders() -> list:
    dg = pd.read_parquet(OUT / "defender_games.parquet")
    dg = dg[(dg.plays > 0) & (dg.season >= 2018)].copy()    # the value components need PFR's charting, 2018 on
    roles = defender_roles(dg)
    dg["role"] = dg.player_id.map(roles); dg = dg[dg.role.isin(DEF_ROLES)]
    cov = DEF_W["cov_yds"] * dg.cov_yds + DEF_W["cov_int"] * dg.cov_int; rush = DEF_W["sacks"] * dg.sacks + DEF_W["press_ns"] * dg.press_ns
    dg = dg.assign(cov_v=cov, other_v=rush + dg.run_stop, all_v=cov + rush + dg.run_stop + dg.ff_epa)   # as role_rates
    # role_rates once per (season, week): the page's defender value as of the week
    t0 = time.time(); live = {}
    for s in SEASONS:
        for w in WEEKS:
            rate, _ = role_rates(dg, roles, s, w); live[(s, w)] = rate
        print(f"role_rates {s}: {time.time() - t0:.0f}s", flush=True)
    res = []
    def_knobs = [(d, k) for d in DECAYS for k in KS]
    for role in DEF_ROLES:
        t0 = time.time()
        gr = dg[dg.role == role]
        g = gr[["player_id", "season", "week", "plays", "epa"]]
        # the recipe's own target (role_rates): coverage per target for CB (S, IDL: plus half the rest), everything plus
        # 0.75 a credited play for LB, everything for EDGE; per snap over the next four games as y_own
        sp = ROLE_SPEC[role]
        own = (gr.cov_v + sp["a"] * gr.other_v) if sp["kind"] == "t" else (gr.all_v + sp.get("tackle", 0.0) * gr.credited)
        g_own = g.assign(epa=own.values)
        prior = {}
        for s in SEASONS:   # replacement level: REPL_PCT of regulars (300+ snaps) in earlier seasons, as role_rates
            h = g[g.season < s].groupby("player_id").agg(plays=("plays", "sum"), epa=("epa", "sum")); h = h[h.plays >= 300]
            prior[s] = float(np.percentile(h.epa / h.plays, REPL_PCT)) if len(h) else 0.0
        rows = build_rows(g, role, prior, DECAYS, KS)
        own_rows = build_rows(g_own, role, prior, [DECAYS[0]], [KS[0]])[["player_id", "season", "week", "y", "next_epa"]].rename(columns={"y": "y_own", "next_epa": "next_own"})
        rows = rows.merge(own_rows, on=["player_id", "season", "week"], how="left")
        rows["value"] = [live[(int(s), int(w))].get(pid, np.nan) for pid, s, w in zip(rows.player_id, rows.season, rows.week)]
        rows = rows[rows.value.notna()]
        # the page's own recency on the plain rate (0.92 a game, 0.8 a season, K 300), for comparison
        page = build_rows(g, role, prior, [DEF_DECAY], [DEF_K], fade=DEF_FADE).rename(columns={knob_name(DEF_DECAY, DEF_K): "def_plain_page"})
        rows = rows.merge(page[["player_id", "season", "week", "def_plain_page"]], on=["player_id", "season", "week"], how="left")
        ranks = active_ranks(g, rows, role, prior, DECAYS, KS)
        ranks["value"] = [live[(int(s), int(w))].get(pid, np.nan) for pid, s, w in zip(ranks.player_id, ranks.season, ranks.week)]
        ranks = ranks[ranks.value.notna()]
        rp = active_ranks(g, rows, role, prior, [DEF_DECAY], [DEF_K], fade=DEF_FADE).rename(columns={knob_name(DEF_DECAY, DEF_K): "def_plain_page"})
        ranks = ranks.merge(rp[["player_id", "season", "week", "def_plain_page"]], on=["player_id", "season", "week"], how="left")
        preds = ["value"] + [f"last{t}" for t in TRAIL] + ["season_to_date", "last_season", "def_plain_page"] + [knob_name(d, k) for d, k in def_knobs]
        res += score(role, rows, ranks, preds, g)
        print(f"{role}: {len(rows)} player-weeks, {len(ranks)} ranking rows, {time.time() - t0:.0f}s", flush=True)
    return res


SUMMARY = """## Summary (29 Sep 2026)

**Skill players: yes, and the value beats the plain averages.** For passers, rushers and receivers the live value's
correlation with the next four games' EPA per play is above every trailing average, the season to date and last
season on both windows (passer 0.383 / 0.505 against last17's 0.371 / 0.404; rusher 0.271 / 0.286 against 0.251 /
0.285; receiver 0.204 / 0.216 against 0.146 / 0.190). The one place a plain average keeps up is the rank order among
regulars: an unshrunk 17-game average ranks passers and rushers about as well as the value (Spearman 0.347 / 0.508
against 0.335 / 0.482 for passers, 0.230 / 0.223 against 0.179 / 0.156 for rushers), because 480 plays of shrinkage
toward the 10th percentile pulls regulars with a season of evidence toward one another. The value's MAE is also
worse than last17's for passers for the same reason (the prior is replacement level, so every estimate is biased
low); the correlation and rank measures are what a ranking is judged on.

**Knobs: the shrinkage is too heavy for the ranking; the decay is fine.** In the decay x k grid, k is what moves
the result and lighter is better everywhere: at decay 0.985, k 120 beats DEFAULT's k 480 on both windows for all
three roles on correlation, rank correlation and MAE (passer 0.397 / 0.530 against 0.383 / 0.505; rusher 0.344 /
0.345 against 0.271 / 0.286; receiver 0.212 / 0.237 against 0.204 / 0.216), and k 60 (beyond the asked grid, added
because the grid's edge won) is better still for rushers (0.363 / 0.367) and about level for passers and receivers.
Decay 0.97 against 0.985 is worth about 0.005 for passers and receivers and nothing for rushers; 1.0 is worse for
passers and receivers. The cost is churn: the top 40 move 0.9 places a week at k 480 and 1.1 at k 120 for passers,
1.6 to 1.6 for rushers, 1.5 to 2.3 for receivers; still far below any trailing average (last17: 2.6, 5.7, 12.4).
Recommendation: keep decay 0.985, and for the ranking use k 120 (better on both windows for every role, and the
same direction the All-Pro check found on 24 Sep: allpro_skill_k120.csv). The catch is that DEFAULT is shared with
the game model's skill-out inputs, where the 23 Sep sweep chose 480 on team-points miss (reports/player_knobs.csv).
That sweep was about a different question (how much a listed-out player costs his team, where usage carries the
value and the rate is mostly noise); this one is about ordering players by their own rate. So either the page's
ranking gets its own k (120) and the game model keeps 480, or player_knobs is re-run at 120 before any shared change.
Nothing under nflmodel/ was changed here.

**Defenders: EDGE and IDL are predictive and the recipes earn their keep; CB, S and LB are weak.** The group
recipes (positions.role_rates) for edge rushers and interior linemen beat every trailing average, last season and
the plain decayed EPA per snap at the page's recency on both windows (EDGE 0.300 / 0.296, IDL 0.336 / 0.221 on
correlation; Spearman about 0.30 and 0.33 / 0.24). Cornerbacks are the weak spot: the CB rate's correlation with
the next four games is 0.138 / 0.053 and its rank correlation among regulars 0.137 / 0.035, and the picture is the
same against its own target, coverage per snap (0.117 / 0.066; Spearman 0.119 / 0.039): a corner's next month is
close to unpredictable from his last one at this horizon, and the plain decayed EPA per snap (0.161 / 0.111 at
0.985 / 480) does better than the coverage recipe on both windows. Safeties (0.139 / 0.129) and linebackers (0.084 /
0.091) are the same story: the plain rate beats the recipe on both windows (S 0.181 / 0.165, LB 0.170 / 0.136), and
the LB recipe's 0.75 EPA per credited play, chosen on All-Pro placement, does not help it predict even its own
target (0.128 / 0.092). These recipes were picked on where All-Pros land and on a corner's coverage the next season,
not on a four-game forecast, so this is a second yardstick rather than a reversal; but on this yardstick the CB, S
and LB rankings carry little signal and the plain rate would be the better choice. Churn for defenders is 1.1 to 3.0
places a week for the live values against 5 to 17 for the trailing averages.

**Sizes.** 3,615 passer, 6,802 rusher and 16,812 receiver player-weeks; 7,500 to 11,200 per defender group.
"""


def report(df: pd.DataFrame) -> str:
    L = ["# Are the player rankings predictive?", "",
         "Every player-week 2019-2025 (weeks 2-18): how well each predictor, as of the week, predicts the player's EPA per play over his next four games in that role (same season, all four required; passers 80+ dropbacks, rushers 20+ carries, receivers 12+ targets, defenders 100+ snaps over the four).",
         "`value` is the live value (PlayerValues with DEFAULT, decay 0.985 / k 480 / 10th percentile prior; role_rates for defenders). `last4/8/17` are unshrunk trailing averages, `season_to_date` is season to date, `last_season` last season's rate; a predictor with no history is the replacement level. `d{decay}_k{k}` is the live value at other knobs. Defenders also get `def_plain_page`: the plain decayed, shrunk EPA per snap at the page's DEF_DECAY 0.92 / fade 0.8 / K 300.",
         "", "Metrics: `corr` plays-weighted Pearson correlation with next-4 EPA per play; `mae` plays-weighted mean absolute error; `spearman` per-week Spearman rank correlation among regulars (100+ plays in the window), averaged over weeks; `corr_total` / `spearman_total` the same against next-4 total EPA; `corr_own` / `spearman_own` (defenders) against the recipe's own target per snap (coverage for CB; coverage plus half the rest for S and IDL; everything plus 0.75 a credited play for LB; everything for EDGE); `churn_top40` mean absolute week-to-week rank change of the top 40 among players active that season. Nothing was fit on 2023-25; k 60 is beyond the asked grid, added because the grid's edge (120) won everywhere.", "", SUMMARY, "## Tables", ""]
    base_preds = ["value", "last4", "last8", "last17", "season_to_date", "last_season"]
    for role, dr in df.groupby("role", sort=False):
        L.append(f"## {role}"); L.append("")
        n = {w: int(dr[dr.window == w].n.iloc[0]) for w in WINDOWS}
        L.append(f"Player-weeks: {n['2019-22']} (2019-22), {n['2023-25']} (2023-25).")
        L.append("")
        own = "corr_own" in dr.columns and dr.corr_own.notna().any()
        L.append("| predictor | corr 19-22 | corr 23-25 | mae 19-22 | mae 23-25 | spearman 19-22 | spearman 23-25 | corr_total 19-22 | corr_total 23-25 |" + (" corr_own 19-22 | corr_own 23-25 | spearman_own 19-22 | spearman_own 23-25 |" if own else "") + " churn 19-22 | churn 23-25 |")
        L.append("|---|---|---|---|---|---|---|---|---|" + ("---|---|---|---|" if own else "") + "---|---|")
        for p in dr.predictor.unique():
            a = dr[(dr.predictor == p) & (dr.window == "2019-22")].iloc[0]; b = dr[(dr.predictor == p) & (dr.window == "2023-25")].iloc[0]
            L.append(f"| {p} | {a['corr']:.3f} | {b['corr']:.3f} | {a.mae:.4f} | {b.mae:.4f} | {a.spearman:.3f} | {b.spearman:.3f} | {a.corr_total:.3f} | {b.corr_total:.3f} |"
                     + (f" {a.corr_own:.3f} | {b.corr_own:.3f} | {a.spearman_own:.3f} | {b.spearman_own:.3f} |" if own else "") + f" {a.churn_top40:.1f} | {b.churn_top40:.1f} |")
        L.append("")
        L += verdict(role, dr)
        L.append("")
    return "\n".join(L)


def verdict(role: str, dr: pd.DataFrame) -> list:
    piv = {m: dr.pivot(index="predictor", columns="window", values=m) for m in ["corr", "mae", "spearman", "churn_top40"]}
    v = {m: piv[m].loc["value"] for m in piv}
    alts = ["last4", "last8", "last17", "season_to_date", "last_season"]
    beats = []
    for a in alts:
        wc = sum(piv["corr"].loc["value", w] > piv["corr"].loc[a, w] for w in WINDOWS); ws = sum(piv["spearman"].loc["value", w] > piv["spearman"].loc[a, w] for w in WINDOWS)
        beats.append((a, wc, ws))
    best_alt = max(alts, key=lambda a: piv["corr"].loc[a].mean())
    grid = [p for p in dr.predictor.unique() if p.startswith("d") and "_k" in p]
    default = knob_name(DEFAULT["decay"], DEFAULT["k"])
    better = [p for p in grid if p != default and all(piv["corr"].loc[p, w] > piv["corr"].loc[default, w] and piv["spearman"].loc[p, w] >= piv["spearman"].loc[default, w] for w in WINDOWS)]
    best_grid = max(grid, key=lambda p: piv["corr"].loc[p, "2019-22"])   # chosen on 2019-22 only
    lines = []
    all_beat = all(wc == 2 and ws == 2 for _, wc, ws in beats)
    lines.append(f"**Verdict ({role}).** The live value's correlation with the next four games is {v['corr']['2019-22']:.3f} (2019-22) and {v['corr']['2023-25']:.3f} (2023-25); rank correlation among regulars {v['spearman']['2019-22']:.3f} and {v['spearman']['2023-25']:.3f}. "
                 + ("It beats every trailing average, the season to date and last season on both windows, on both correlation and rank correlation. " if all_beat
                    else "It does not beat every simple average on both windows: " + ", ".join(f"{a} (beaten on {wc}/2 windows by correlation, {ws}/2 by rank correlation)" for a, wc, ws in beats if wc < 2 or ws < 2) + ". ")
                 + f"The strongest simple alternative is {best_alt} (corr {piv['corr'].loc[best_alt, '2019-22']:.3f} / {piv['corr'].loc[best_alt, '2023-25']:.3f}).")
    if role in ("passer", "rusher", "receiver"):
        gd = ", ".join(f"{p} ({piv['corr'].loc[p, '2019-22']:.3f} / {piv['corr'].loc[p, '2023-25']:.3f})" for p in better) if better else "none"
        lines.append(f"Knobs: the best grid cell on 2019-22 is {best_grid} (corr {piv['corr'].loc[best_grid, '2019-22']:.3f}, held out {piv['corr'].loc[best_grid, '2023-25']:.3f}); DEFAULT {default} is {piv['corr'].loc[default, '2019-22']:.3f} / {piv['corr'].loc[default, '2023-25']:.3f}. Cells better than DEFAULT on both windows (correlation up, rank correlation not down): {gd}.")
    else:
        pg_ = "def_plain_page"
        lines.append(f"Against the plain decayed EPA per snap at the page's recency ({pg_}: corr {piv['corr'].loc[pg_, '2019-22']:.3f} / {piv['corr'].loc[pg_, '2023-25']:.3f}, spearman {piv['spearman'].loc[pg_, '2019-22']:.3f} / {piv['spearman'].loc[pg_, '2023-25']:.3f}) the group recipe is "
                     + ("better on both windows." if all(piv["corr"].loc["value", w] > piv["corr"].loc[pg_, w] for w in WINDOWS) else "not better on both windows.")
                     + f" Best plain grid cell on 2019-22: {best_grid} ({piv['corr'].loc[best_grid, '2019-22']:.3f} / {piv['corr'].loc[best_grid, '2023-25']:.3f}).")
    lines.append(f"Churn: the top 40 by the live value move {v['churn_top40']['2019-22']:.1f} places a week (2019-22) and {v['churn_top40']['2023-25']:.1f} (2023-25); by last4 {piv['churn_top40'].loc['last4', '2019-22']:.1f} / {piv['churn_top40'].loc['last4', '2023-25']:.1f}, by last17 {piv['churn_top40'].loc['last17', '2019-22']:.1f} / {piv['churn_top40'].loc['last17', '2023-25']:.1f}.")
    return lines


if __name__ == "__main__":
    t0 = time.time()
    (ROOT / "reports").mkdir(exist_ok=True)
    if "--report-only" in sys.argv:      # rewrite the markdown from the saved csv
        df = pd.read_csv(ROOT / "reports" / "rankings_predictive.csv")
    else:
        res = skill()
        if "--skip-defenders" not in sys.argv:
            res += defenders()
        df = pd.DataFrame(res)
        df.to_csv(ROOT / "reports" / "rankings_predictive.csv", index=False)
    (ROOT / "reports" / "rankings_predictive.md").write_text(report(df))
    print(df[df.predictor.isin(["value", "last4", "last8", "last17", "season_to_date", "last_season"])].to_string(index=False))
    print(f"done in {time.time() - t0:.0f}s", flush=True)
