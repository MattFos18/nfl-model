"""Round 3 (29 Sep 2026): situational, kickoff-time, weather, injury and player-vs-player ideas on the per-game player
props, plus two near-misses rerun on the current code. The adoption rule is reports/round3_rule.md, written before any
result; this script follows it as the props side reads it:

  1. better on every window: the miss (yards MAE per player-game; receptions, targets, carries and dropbacks MAE; touchdown
     and interception Poisson log loss, as experiments/props_by_season.py scores them) lower on 2017-18, 2019-22 and
     2023-25. 2017-18 is the earliest the harness scores (2016 is the first charted season); an input with no data before
     2018 (the corner ratings, man/zone) cannot be tested there and is judged on the two later windows with 2017-18 not worse.
  2. no bet cost: the calibrated chance on the lines (props.chance_over, the K nearest past lines of the variant's own
     reference table) no worse in log loss on any window, at book numbers x = the rule's line + delta; and the lean record
     against the real book lines where the harness has them (data/lines/props_log.csv, 2026 Week 3) not worse.
  3. beats its own placebo: the same input shuffled within season, 50 draws, refitted the same way; the real gain must
     beat the placebo's in at least 45 of 50 draws on every window.
  4. no new risk: every input as of before the game, no market input, no data source the weekly run does not pull.
  5. together: the passing pieces rerun together must pass 1 and 2.

Every idea is a multiplicative adjustment on the live projection (the final line after the median factor, the team
reconciliation and the injury/snap factor): line x exp(a x z). Its size (and its shrinkage k, for a player's own split)
is fitted walk-forward: a season's rows are scored with the value that minimises the miss over every earlier season from
2016 (the build keeps the 2016 player-games, which the by-season run drops, only as fitting rows), never on the season
scored. Three shapes:
  L  a condition or level z centred on the player's own decayed history of it (his rate already carries the conditions he
     played in): zc = z - q, q his 0.85-decayed mean of z over his earlier player-games. Fitted pooled and, for receivers
     and rushers, by position group (WR / TE / RB; RB / QB / other), each group's own size.
  P  his own split of a condition, shrunk toward the league's: s = league + (his split - league) x n / (n + k), split in
     log residual (log((actual + f) / (line + f)) against the rule's line), then line x exp(c x s x zc).
  H  his residual history at a key (the stadium, the opposing head coach, the opponent, specific corners): s = n / (n + k) x
     (his mean residual at the key - his mean residual), line x exp(c x s).
Task B: the rushing median factor as a function of the mean (logistic and linear against the flat 0.84, walk-forward), and
receiving usage shares capped at one over the roster the card can know (a fixed rule, no fit).

Usage: PYTHONPATH=. python experiments/situational_props.py build      (the frames, cached in CACHE; a few minutes)
       PYTHONPATH=. python experiments/situational_props.py features   (the inputs, cached)
       PYTHONPATH=. python experiments/situational_props.py run        (scores, placebos, reports/situational_props.md/.csv)"""
import numpy as np, pandas as pd, pathlib, os, sys, time
from nflmodel import props as PR
from nflmodel.features import OUT, RAW
CACHE = pathlib.Path(os.environ.get("SIT_CACHE", "/tmp/claude-0/-home-user/c1e0d18e-681a-50ba-b0bb-6c809c2e3dee/scratchpad/situational")); CACHE.mkdir(parents=True, exist_ok=True)
T0 = time.time()


def log(*a):
    print(f"[{time.time() - T0:7.1f}s]", *a, flush=True)


# ----------------------------------------------------------------------------------------------------------------- build
def build_frames():
    """props_by_season.build(kind) per kind with three changes that do not touch the rule: the 2016 player-games are kept
    (fitting rows only), the share before round 18's absorption is kept (share_pre_abs), and the per-player sums and the
    absorption's known-out table are kept for the share cap and the injury ideas."""
    src = pathlib.Path(__file__).with_name("props_by_season.py").read_text().split("by_season, by_pos, by_bucket = [], [], []")[0]
    reps = [("(f.agames >= 3) & (f.season >= 2017)", "(f.agames >= 3) & (f.season >= 2016)"),
            ("    if kind != \"pass\": share_y = absorb_shares(kind, f, share_y, pg, vcol, sf, tf)", "    f[\"share_pre_abs\"] = share_y\n    if kind != \"pass\": share_y = absorb_shares(kind, f, share_y, pg, vcol, sf, tf)"),
            ("    dg = t.groupby([\"defteam\", \"season\", \"week\", \"game_id\"])", "    globals()[\"_LAST\"] = (pg, R, R85)\n    dg = t.groupby([\"defteam\", \"season\", \"week\", \"game_id\"])"),
            ("    S = C.groupby([\"game_id\", \"posteam\", \"grp\"]).share_abs.sum()", "    S = C.groupby([\"game_id\", \"posteam\", \"grp\"]).share_abs.sum(); globals().setdefault(\"_ABS\", {})[kind] = C.copy()")]
    for a, b in reps:
        assert src.count(a) == 1, a
        src = src.replace(a, b)
    ns = {"__name__": "bys"}; exec(compile(src, "bys", "exec"), ns); log("props_by_season header loaded")
    d, lg_series = ns["d"], ns["lg_series"]
    ns["_KNOWN_OUT"].to_parquet(CACHE / "known_out.parquet"); ns["_REP"].to_parquet(CACHE / "reports.parquet")
    for kind in ("rec", "rush", "pass"):
        t1 = time.time(); f, ev = ns["build"](kind); f = f.reset_index(drop=True)
        if kind == "rec":
            t = d[d.pass_play & d.receiver_player_id.notna()]; lgp = d[d.pass_play]
        elif kind == "rush":
            t = d[d.play_type.eq("run") & d.rusher_player_id.notna()]; lgp = t
        else:
            t = d[d.dropback & d.passer_player_id.notna()].assign(yards_gained=lambda x: x.pass_yds); lgp = t
        f["lg"] = lg_series(f, lgp.assign(yards_gained=lgp.yards_gained.fillna(0.0)), "yards_gained", float(lgp.yards_gained.fillna(0.0).mean())).values
        if kind in PR.INJ_F:
            grp = [PR.inj_group(a_, b_) for a_, b_ in zip(f.report_status, f.practice_status)]
            f["inj"] = np.array([PR.INJ_F[kind].get(g_, 1.0) for g_ in grp]); f["r13"] = f.inj * np.array([1 + PR.SNAP_W[kind] * (PR.snap_ratio(a_, b_) - 1) for a_, b_ in zip(f.s3, f.s10)])
        else:
            f["inj"] = 1.0; f["r13"] = 1.0
        keep = [c for c in f.columns if f[c].dtype != object or c in ("pid", "posteam", "defteam", "game_id", "home_team", "away_team", "pos", "report_status", "practice_status")]
        f[keep].to_parquet(CACHE / f"frame_{kind}.parquet")
        pg, R, R85 = ns["_LAST"]
        if kind != "pass":
            pg.to_parquet(CACHE / f"pg_{kind}.parquet"); R[["pid", "game_id", "n", "games_prev"]].to_parquet(CACHE / f"R_{kind}.parquet"); R85[["pid", "game_id", "n_85", "team_n_85"]].to_parquet(CACHE / f"R85_{kind}.parquet")
            ns["_ABS"][kind].to_parquet(CACHE / f"absorb_{kind}.parquet")
        log(kind, "frame", len(f), f"{time.time() - t1:.0f}s", f.groupby("season").size().to_dict())
    # the pieces the share cap needs for players absent from a game: post-game states of both shares (touch and active)
    for kind in ("rec",):
        post_states_for_cap(ns, kind)


def post_states_for_cap(ns, kind):
    """Every player's round-17 share blend after each of his games (the state a later game reads), touch-games and
    active-games shares, as absorb_shares builds them; cached for the share cap (Task B)."""
    pg = pd.read_parquet(CACHE / f"pg_{kind}.parquet"); vcol = {"rec": "tp", "rush": "tr"}[kind]; sf, tf = PR.FADE.get(kind, (1.0, 1.0)); tv = ns["tv"]; _ACTIVE = ns["_ACTIVE"]
    base = pg[["pid", "posteam", "season", "week", "game_id", "n", "team_n"]]
    za = _ACTIVE[_ACTIVE.pid.isin(pg.pid.unique()) & _ACTIVE.position.isin(PR.SKILL[kind])].merge(pg[["pid", "game_id"]].assign(has=1), on=["pid", "game_id"], how="left")
    za = za[za.has.isna()][["pid", "posteam", "season", "week", "game_id"]].merge(tv[["posteam", "season", "week", "game_id", vcol]].rename(columns={vcol: "team_n"}), on=["posteam", "season", "week", "game_id"], how="inner").assign(n=0)
    zero = dict(n=0, team_n=0.0); last = pg.sort_values(["pid", "season", "week"]).groupby("pid").tail(1)[["pid", "posteam"]].assign(season=9999, week=0, game_id="dummy", **zero)
    post = []
    for name, frame_ in (("touch", pd.concat([base, last], ignore_index=True)), ("active", pd.concat([base, za, last], ignore_index=True))):
        st = ns["fade_sums"](frame_, ["pid"], ["n", "team_n"], PR.DECAY, sf, tf).sort_values(["pid", "season", "week"]).reset_index(drop=True)
        st["pre"] = st.n / st.team_n.replace(0, np.nan); st["post"] = st.groupby("pid").pre.shift(-1)
        st = st[st.season < 9999].dropna(subset=["post"]); st["key"] = st.season.astype("int64") * 100 + st.week.astype("int64")
        post.append(st[["pid", "key", "post"]].rename(columns={"post": f"s_{name}"}))
    P = post[0].merge(post[1], on=["pid", "key"], how="outer").sort_values(["pid", "key"])
    P.to_parquet(CACHE / f"post_{kind}.parquet"); log("post states", kind, len(P))




# ------------------------------------------------------------------------------------------------------------ engine
WIN3 = {"2017-18": (2017, 2018), "2019-22": (2019, 2022), "2023-25": (2023, 2025)}; FIT_FROM = 2016; SEASONS = list(range(2016, 2027))
# stat: (kind, line column, actual column, loss, floor of the log residual)
STATS = {"rec_yards": ("rec", "yds_line", "act_yds", "mae", 10.0), "rec_catches": ("rec", "catch_line", "act_catch", "mae", 1.0), "rec_targets": ("rec", "vol", "act_n", "mae", 1.0),
         "rec_td": ("rec", "td_line", "act_td", "pll", 0.3), "rush_yards": ("rush", "yds_line", "act_yds", "mae", 10.0), "rush_carries": ("rush", "vol", "act_n", "mae", 2.0),
         "rush_td": ("rush", "td_line", "act_td", "pll", 0.3), "pass_yards": ("pass", "yds_line", "act_yds", "mae", 50.0), "pass_dropbacks": ("pass", "vol", "act_n", "mae", 5.0),
         "pass_td": ("pass", "td_line", "act_td", "pll", 0.3), "pass_int": ("pass", "int_line", "act_int", "pll", 0.3)}
CHANCE_OF = {"rec_yards": ("ratio", [-15, -10, -5, 0, 5, 10, 15], 0.0), "rec_catches": ("ratio", [-2, -1, 0, 1, 2], 0.0), "rush_yards": ("diff", [-15, -10, -5, 0, 5, 10, 15], 10.0), "pass_yards": ("diff", [-45, -30, -15, 0, 15, 30, 45], 0.0)}
BOOK_OF = {"rec_yards": "rec_yards", "rec_catches": "rec_catches", "rec_targets": "rec_targets", "rush_yards": "rush_yards", "rush_carries": "rush_attempts", "pass_yards": "pass_yards", "pass_td": "pass_td", "pass_int": "pass_int"}
POSG = {"rec": {"WR": 0, "TE": 1, "RB": 2, "FB": 2, "HB": 2}, "rush": {"RB": 0, "FB": 0, "HB": 0, "QB": 1}}
POSG_NAME = {"rec": ["WR", "TE", "RB", "other"], "rush": ["RB", "QB", "other"]}
A_GRID = np.round(np.linspace(-0.3, 0.3, 241), 5)          # the size per standard deviation of the centred input (L)
C_GRID = np.round(np.arange(-1.0, 2.5001, 0.05), 3)          # the weight on a player's shrunk split or history (P, H)
KS_P, KS_H = (2, 5, 10, 20, 40, 80), (1, 2, 4, 8, 16, 32)
N_PLACEBO, PLACEBO_NEED = 50, 45
DECAY = PR.DECAY


def lossf(kind):
    if kind == "mae":
        return lambda mu, act: np.abs(mu - act)
    return lambda mu, act: (lambda m: m - act * np.log(m))(np.clip(mu, 1e-3, None))


class K:
    """One kind's frame with the situation table merged and the history order."""

    def __init__(self, kind, G):
        f = pd.read_parquet(CACHE / f"frame_{kind}.parquet").reset_index(drop=True)
        if kind == "pass" and "int_line" not in f:
            raise SystemExit("frame_pass lacks int_line")
        f = f.merge(G.rename(columns={"team": "posteam"}), on=["game_id", "posteam"], how="left", suffixes=("", "_g"))
        assert len(f) == len(pd.read_parquet(CACHE / f"frame_{kind}.parquet", columns=["pid"]))
        X = pd.read_parquet(CACHE / f"X_{kind}.parquet"); assert len(X) == len(f) and (X.pid.values == f.pid.values).all()
        for c in X.columns:
            if c not in f.columns: f[c] = X[c].values
        self.kind, self.f = kind, f; self.n = len(f); self.season = f.season.values.astype(int)
        self.order = np.lexsort((f.week.values, f.season.values, f.pid.values)); self.inv = np.empty(self.n, dtype=np.int64); self.inv[self.order] = np.arange(self.n)
        self.pid_sorted = f.pid.values[self.order]
        pm = POSG.get(kind, {}); self.pos_group = np.array([pm.get(p, len(POSG_NAME.get(kind, ["all"])) - 1) for p in f.pos.values]) if kind in POSG else np.zeros(self.n, dtype=int)

    def prior_mean(self, z, fill=None):
        """His 0.85-decayed mean of z over his earlier player-games in this frame (weight 1 on the latest); fill (default the
        mean of z) where he has none."""
        z = np.nan_to_num(np.asarray(z, float)); zs = z[self.order]
        from experiments.situational_props_feats import _seg_decayed
        S = _seg_decayed(self.pid_sorted, np.c_[zs, np.ones_like(zs)], DECAY)
        P = (S - np.c_[zs, np.ones_like(zs)])
        q = np.where(P[:, 1] > 1e-9, P[:, 0] / np.where(P[:, 1] > 1e-9, P[:, 1], 1.0), np.nan)[self.inv]
        return np.where(np.isnan(q), float(np.mean(z)) if fill is None else fill, q)

    def excl_cumsum(self, keys_cols, vals):
        """Sum and count of vals over the same (pid, key) earlier rows (strictly before), in frame order."""
        df = pd.DataFrame({"i": np.arange(self.n), "pid": self.f.pid.values, "s": self.season, "w": self.f.week.values, "v": vals, "one": 1.0})
        for j, k in enumerate(keys_cols): df[f"k{j}"] = k
        df = df.sort_values(["pid", "s", "w"]); gk = ["pid"] + [f"k{j}" for j in range(len(keys_cols))]
        cs = df.groupby(gk, sort=False)[["v", "one"]].cumsum(); df["sv"] = cs.v - df.v; df["sn"] = cs.one - 1.0
        df = df.sort_values("i"); return df.sv.values, df.sn.values


class Stat:
    def __init__(self, name, KF):
        kind, lc, ac, lo, fl = STATS[name]; self.name, self.K, self.kind, self.loss = name, KF, kind, lo
        f = KF.f; self.line = f[lc].values.astype(float); self.act = f[ac].values.astype(float); self.lf = lossf(lo)
        self.l0 = self.lf(self.line, self.act); self.fl = fl
        self.lr = np.log(np.maximum(self.act + fl, 0.5 * fl) / np.maximum(self.line + fl, 0.5 * fl))   # his residual against the rule's line, log scale

    # ---- candidate sets -> walk-forward fit ----
    def fit(self, cands, groups=None, base_lm=None):
        """cands: list of (param magnitude, fn -> log multiplier array). Walk-forward per season (and group): the candidate
        with the least loss over every earlier season from 2016; the zero candidate for 2016 itself. Returns the variant's
        per-row loss, log multiplier, and the choice per season."""
        n = self.K.n; groups = np.zeros(n, dtype=int) if groups is None else groups; ng = int(groups.max()) + 1; ns = len(SEASONS)
        si = self.season_idx(); J = len(cands); E = np.zeros((ns, ng, J)); mags = np.array([c[0] for c in cands], float)
        comb = si * ng + groups; b = np.zeros(n) if base_lm is None else base_lm
        for j, c_ in enumerate(cands):
            lm = c_[1](); E[:, :, j] = np.bincount(comb, weights=self.lf(self.line * np.exp(lm + b), self.act), minlength=ns * ng).reshape(ns, ng)
        zero = int(np.argmin(np.abs(mags))); choice = np.full((ns, ng), zero)
        for s_ in range(1, ns):
            cum = E[:s_].sum(0) + 1e-6 * np.abs(mags)[None, :]
            choice[s_] = np.argmin(cum, axis=1)
        lm = np.zeros(n); cache = {}
        for (s_, g_) in {(a, b) for a, b in zip(si, groups)}:
            j = choice[s_, g_]; m = (si == s_) & (groups == g_)
            if j not in cache: cache[j] = cands[j][1]()
            lm[m] = cache[j][m]
        return self.lf(self.line * np.exp(lm + b), self.act), lm + b, choice

    def season_idx(self):
        return self.K.season - SEASONS[0]

    def windows(self, lv):
        out = {}
        for w, (a, b) in WIN3.items():
            m = (self.K.season >= a) & (self.K.season <= b); d = lv[m] - self.l0[m]
            out[w] = (float(d.mean()), float(d.std(ddof=1) / np.sqrt(m.sum())), float(self.l0[m].mean()))
        return out


def cands_L(zc, fitmask):
    sd = float(np.std(zc[fitmask])) if fitmask.any() else 0.0
    sd = sd if sd > 1e-9 else (float(np.std(zc)) if np.std(zc) > 1e-9 else 1.0)
    return [(abs(a), (lambda a=a: np.clip(a / sd * zc, -0.7, 0.7)), a / sd) for a in A_GRID], sd


def cands_S(svals):
    """svals: {k: s_k array}; candidates c x s_k."""
    out = [(0.0, lambda: np.zeros(len(next(iter(svals.values())))), (0, 0.0))]
    for k, sk in svals.items():
        for c in C_GRID:
            if c == 0: continue
            out.append((abs(c) + 1e-3 * k, (lambda c=c, sk=sk: np.clip(c * sk, -0.7, 0.7)), (k, float(c))))
    return out


def league_split(st, X, lr):
    """Per row: the league's split (mean residual with X=1 minus with X=0) over every earlier season from 2016."""
    out = np.zeros(st.K.n); s = st.K.season
    for s_ in np.unique(s):
        m = s < s_; a, b = m & (X > 0.5), m & (X <= 0.5)
        if a.sum() >= 30 and b.sum() >= 30: out[s == s_] = lr[a].mean() - lr[b].mean()
    return out


def svals_P(st, X):
    """His own split of condition X in log residual, shrunk toward the league's with k player-games (n = nA nB / (nA + nB)),
    times X centred on his decayed history of X."""
    X = np.nan_to_num(np.asarray(X, float)); lr = st.lr
    sa, na = st.K.excl_cumsum([], lr * X)[0], st.K.excl_cumsum([], X)[0]; sb, nb = st.K.excl_cumsum([], lr * (1 - X))[0], st.K.excl_cumsum([], 1 - X)[0]
    L = league_split(st, X, lr); ok = (na > 0) & (nb > 0)
    raw = np.where(ok, sa / np.where(na > 0, na, 1) - sb / np.where(nb > 0, nb, 1), 0.0); neff = np.where(ok, na * nb / np.where(na + nb > 0, na + nb, 1), 0.0)
    zc = X - st.K.prior_mean(X)
    return {k: (L + (raw - L) * neff / (neff + k)) * zc for k in KS_P}


def svals_H(st, key):
    """His mean residual at the key over his mean residual, shrunk with k player-games at the key."""
    key = pd.Series(key).fillna("?").astype(str).values
    sk, nk = st.K.excl_cumsum([key], st.lr); sa, na = st.K.excl_cumsum([], st.lr)
    mall = np.where(na > 0, sa / np.where(na > 0, na, 1), 0.0); dev = np.where(nk > 0, sk / np.where(nk > 0, nk, 1) - mall, 0.0)
    return {k: dev * nk / (nk + k) for k in KS_H}


# --------------------------------------------------------------------------------------------- rule 2: chance, lean
def chance_ll(st, line_var):
    """Log loss of props.chance_over's reading (the K reference rows nearest in the line, K a tenth of the table, 300 to
    1500; the reference: every earlier projected player-game from 2017 with its line and actual) at book numbers x = the
    rule's line + delta, for the rule and for the variant (each on its own lines and its own reference table), on the rows
    where both lines are at or above the chance's minimum. Returns {window: (rule ll, variant ll, n)}."""
    how, deltas, minl = CHANCE_OF[st.name]; s = st.K.season; out = {}; base = st.line; act = st.act; acc = {w: [0.0, 0.0, 0] for w in WIN3}
    for s_ in range(2018, 2026):
        q = (s == s_) & (base > 0) & (line_var > 0) & (base >= minl) & (line_var >= minl)
        if not q.any(): continue
        lls = []
        for L_all in (base, line_var):
            r = (s >= 2017) & (s < s_) & (L_all > 0); hL, hv = L_all[r], act[r]; o = np.argsort(hL, kind="stable"); hL, hv = hL[o], hv[o]; n = len(hL)
            Kk = int(min(PR.CHANCE_K[2], max(PR.CHANCE_K[1], PR.CHANCE_K[0] * n))); Kk = min(Kk, n)
            Lq = L_all[q]; pos = np.clip(np.searchsorted(hL, Lq) - Kk // 2, 0, max(n - Kk, 0)); idx = pos[:, None] + np.arange(Kk)[None, :]
            w = (hv / np.where(hL > 0, hL, np.nan)) if how == "ratio" else (hv - hL); W = w[idx]
            ll = np.zeros(q.sum()); cnt = np.zeros(q.sum())
            for dl in deltas:
                x = base[q] + dl; ok = (x >= 0.5) & (act[q] != x)
                t = (x / Lq) if how == "ratio" else (x - Lq)
                p = np.clip(np.nanmean(W > t[:, None], axis=1), 0.001, 0.999); y = (act[q] > x).astype(float)
                ll += np.where(ok, -(y * np.log(p) + (1 - y) * np.log(1 - p)), 0.0); cnt += ok
            lls.append((ll, cnt))
        for w_, (a, b) in WIN3.items():
            if a <= s_ <= b:
                acc[w_][0] += lls[0][0].sum(); acc[w_][1] += lls[1][0].sum(); acc[w_][2] += lls[0][1].sum()
    return {w: ((v[0] / v[2], v[1] / v[2], int(v[2])) if v[2] else (np.nan, np.nan, 0)) for w, v in acc.items()}


_BOOK = None


def book_lines():
    """The consensus book line per (game_id, stat, normalised name): the median across books of each book's last line
    before kickoff (data/lines/props_log.csv; 2026 from Week 3)."""
    global _BOOK
    if _BOOK is None:
        from nflmodel.props_lines import norm_name
        x = pd.read_csv(RAW.parent / "lines" / "props_log.csv"); x = x[x.line.notna()].copy(); x["ts_"] = pd.to_datetime(x.ts.str.replace(r"T(\d\d)-(\d\d)-(\d\d)Z", r" \1:\2:\3", regex=True), utc=True, errors="coerce")
        g = pd.read_parquet(OUT / "games.parquet", columns=["game_id", "kickoff_et"]); ko = pd.to_datetime(g.kickoff_et).dt.tz_localize("America/New_York", ambiguous="NaT", nonexistent="NaT").dt.tz_convert("UTC")
        x["st_"] = x.game_id.map(dict(zip(g.game_id, ko))); x = x[x.ts_ < x.st_]; x["key"] = x.player.map(norm_name)   # the kickoff from the schedule (pick'em rows carry no start)
        x = x.sort_values("ts_").groupby(["game_id", "stat", "key", "book"]).tail(1)
        _BOOK = x.groupby(["game_id", "stat", "key"]).line.median().reset_index()
    return _BOOK


_NAMES = None


def lean_record(st, line_var):
    """Wins and losses of the side each line takes against the consensus book line (over when our line is above it), rule
    and variant, on the harness rows that have one (2026 Week 3). Returns (rule w, l, variant w, l, n)."""
    global _NAMES
    if st.name not in BOOK_OF: return None
    from nflmodel.props_lines import norm_name
    if _NAMES is None:
        from nflmodel.positions import names_by_id
        _NAMES = {p: norm_name(v[0]) for p, v in names_by_id(range(2014, 2027)).items()}
    f = st.K.f; m = f.season.values == 2026
    if not m.any(): return None
    q = pd.DataFrame({"i": np.flatnonzero(m), "game_id": f.game_id.values[m], "key": [_NAMES.get(p, "") for p in f.pid.values[m]]}).assign(stat=BOOK_OF[st.name])
    q = q.merge(book_lines(), on=["game_id", "stat", "key"], how="inner")
    if not len(q): return (0, 0, 0, 0, 0)
    res = []
    for L in (st.line, line_var):
        our = L[q.i.values]; bk = q.line.values; a = st.act[q.i.values]
        if st.loss == "pll":
            from scipy.stats import poisson
            side = np.sign((1 - poisson.cdf(np.floor(bk), np.clip(our, 1e-3, None))) - 0.5)   # a count: over when P(more than the line) > 1/2
        else:
            side = np.sign(our - bk)
        dec = (side != 0) & (a != bk)
        win = dec & (np.sign(a - bk) == side); res += [int(win.sum()), int((dec & ~win).sum())]
    return tuple(res) + (len(q),)


# ---------------------------------------------------------------------------------------------------------- features
def _key(s, w):
    return np.asarray(s).astype("int64") * 100 + np.asarray(w).astype("int64")


def _team_asof(tg, cols, n=17):
    """tg: one row per (team, season, week, game_id) with cols; the sums over the team's previous n games."""
    tg = tg.sort_values(["team", "season", "week"]).copy()
    for c in cols: tg[f"p_{c}"] = tg.groupby("team")[c].transform(lambda s: s.rolling(n, min_periods=1).sum().shift(1))
    return tg


def build_features():
    """Per kind, per frame row: the custom inputs (former team, teammates out, the opponent's defense this week, the
    player-vs-player readings), saved as CACHE/X_<kind>.parquet in frame order, with G (the situation table)."""
    import experiments.situational_props_feats as SF
    G = SF.game_table(); G.to_parquet(CACHE / "G.parquet"); log("situation table", G.shape)
    ko = pd.read_parquet(CACHE / "known_out.parquet")
    R, roles = SF.defender_ratings(); log("defender ratings", len(R))
    ED = SF.expected_defense(ko, R, roles); ED.to_pickle(CACHE / "expected_defense.pkl"); log("expected defense", ED.shape)
    P = pd.read_parquet(OUT / "scheme_plays.parquet", columns=["game_id", "season", "week", "posteam", "defteam", "pass_play", "dropback", "play_type", "receiver_player_id", "passer_player_id",
                                                               "yards_gained", "pass_yds", "man", "zone", "cov_known", "box", "sack", "qb_hit", "season_type"])
    P = P[(P.season >= 2015)]
    # own pass protection: sacks + QB hits allowed per dropback over the team's last 17 games; the opponent's man rate
    # (pass plays with a known coverage) and heavy-box rate (runs with a box count, 8+) over its last 17
    db = P[P.dropback.fillna(False).astype(bool)].assign(pr=lambda x: ((x.sack.fillna(0) > 0) | (x.qb_hit.fillna(0) > 0)).astype(float), one=1.0)
    prot = _team_asof(db.groupby(["posteam", "season", "week", "game_id"]).agg(pr=("pr", "sum"), db=("one", "sum")).reset_index().rename(columns={"posteam": "team"}), ["pr", "db"])
    prot["own_prot"] = prot.p_pr / prot.p_db
    pp = P[P.pass_play.fillna(False).astype(bool) & P.cov_known.fillna(False).astype(bool)].assign(m=lambda x: x.man.fillna(0).astype(float), one=1.0)
    man = _team_asof(pp.groupby(["defteam", "season", "week", "game_id"]).agg(m=("m", "sum"), c=("one", "sum")).reset_index().rename(columns={"defteam": "team"}), ["m", "c"])
    man["opp_man"] = np.where(man.p_c >= 100, man.p_m / man.p_c, np.nan)
    rn = P[P.play_type.eq("run") & P.box.notna()].assign(h=lambda x: (x.box >= 8).astype(float), one=1.0)
    box = _team_asof(rn.groupby(["defteam", "season", "week", "game_id"]).agg(h=("h", "sum"), c=("one", "sum")).reset_index().rename(columns={"defteam": "team"}), ["h", "c"])
    box["opp_heavy"] = np.where(box.p_c >= 50, box.p_h / box.p_c, np.nan)
    # snap history for "former team"
    sx = pd.read_parquet(OUT / "snap_exposure.parquet", columns=["player_id", "team", "season", "week", "off_pct"]); sx = sx[sx.off_pct > 0]
    first = sx.assign(key=_key(sx.season, sx.week)).groupby(["player_id", "team"]).key.min().rename("first_key").reset_index().rename(columns={"player_id": "pid", "team": "opp"})
    ab = {k: pd.read_parquet(CACHE / f"absorb_{k}.parquet") for k in ("rec", "rush")}
    outs = pd.concat([ab["rec"], ab["rush"]]).groupby(["game_id", "posteam", "grp"]).share_abs.sum().unstack(fill_value=0.0).reset_index()
    for c in ("WR", "TE", "RB"):
        if c not in outs: outs[c] = 0.0
    outs = outs.rename(columns={"WR": "wr_out", "TE": "te_out", "RB": "rb_out"})[["game_id", "posteam", "wr_out", "te_out", "rb_out"]]
    posmap = {"WR": "wr_out", "TE": "te_out", "RB": "rb_out", "FB": "rb_out", "HB": "rb_out"}
    for kind in ("rec", "rush", "pass"):
        f = pd.read_parquet(CACHE / f"frame_{kind}.parquet", columns=["pid", "posteam", "defteam", "season", "week", "game_id", "pos"]).reset_index(drop=True); f["i"] = np.arange(len(f))
        X = f.merge(first, left_on=["pid", "defteam"], right_on=["pid", "opp"], how="left"); X["vs_former"] = ((X.first_key < _key(X.season, X.week)) & (X.defteam != X.posteam)).astype(float)
        X = X.drop(columns=["opp", "first_key"]).merge(outs, on=["game_id", "posteam"], how="left")
        for c in ("wr_out", "te_out", "rb_out"): X[c] = X[c].fillna(0.0)
        X["same_out"] = [getattr(r, posmap.get(r.pos, "rb_out")) if r.pos in posmap else 0.0 for r in X.itertuples()]
        X["cross_out"] = np.where(X.pos.eq("WR"), X.te_out, np.where(X.pos.eq("TE"), X.wr_out, X.wr_out + X.te_out))
        e = ED.drop(columns=["cb_list"]).rename(columns={"season": "_s", "week": "_w"})
        X = X.merge(e.drop(columns=["_s", "_w"]), on=["game_id", "defteam"], how="left")
        X["opp_cb_r"] = X.CB_r; X["opp_cb_chg"] = X.CB_r - X.CB_base; X["opp_lbs_r"] = X[["LB_r", "S_r"]].mean(axis=1); X["opp_lbs_chg"] = X[["LB_r", "S_r"]].mean(axis=1) - X[["LB_base", "S_base"]].mean(axis=1)
        X["opp_front_r"] = X[["IDL_r", "LB_r", "EDGE_r"]].mean(axis=1); X["opp_front_chg"] = X.opp_front_r - X[["IDL_base", "LB_base", "EDGE_base"]].mean(axis=1)
        X["opp_rush_r"] = X[["EDGE_r", "IDL_r"]].mean(axis=1); X["opp_rush_chg"] = X.opp_rush_r - X[["EDGE_base", "IDL_base"]].mean(axis=1)
        X["opp_cb_out"] = X.CB_out; X["opp_s_out"] = X.S_out; X["opp_lb_out"] = X.LB_out; X["opp_dl_out"] = X.EDGE_out + X.IDL_out
        X = X.merge(prot[["team", "game_id", "own_prot"]].rename(columns={"team": "posteam"}), on=["posteam", "game_id"], how="left")
        X = X.merge(man[["team", "game_id", "opp_man"]].rename(columns={"team": "defteam"}), on=["defteam", "game_id"], how="left").merge(box[["team", "game_id", "opp_heavy"]].rename(columns={"team": "defteam"}), on=["defteam", "game_id"], how="left")
        zr = (X.opp_rush_r - X.opp_rush_r.mean()) / X.opp_rush_r.std(); zp = (X.own_prot - X.own_prot.mean()) / X.own_prot.std()
        X["rush_vs_prot"] = (zr.fillna(0.0) + zp.fillna(0.0)) * (X.opp_rush_r.notna() & X.own_prot.notna())   # a strong rush against a leaky line: both high
        X = X.sort_values("i").reset_index(drop=True); assert len(X) == len(f)
        X.to_parquet(CACHE / f"X_{kind}.parquet"); log("features", kind, X.shape)
    pvp_features(ED)


def pvp_features(ED):
    """Player vs player. The participation file (who is on the field, the man/zone call, the box) is published after a
    season, so its readings enter only later seasons: a receiver's and a QB's man/zone split over his earlier seasons,
    the opponent's man rate and heavy-box rate last season, and a receiver's history against specific corners over earlier
    seasons. The shadow index uses the play-by-play credits (weekly), as of before the game."""
    import experiments.situational_props_feats as SF
    pl = SF.plays_participation(); log("plays with participation", len(pl))
    pa = pl[pl.play_type.eq("pass") & (pl.sack.fillna(0) == 0)].copy(); mzt = pa.defense_man_zone_type.fillna("")
    pa["m"] = mzt.eq("MAN_COVERAGE").astype(float); pa["z"] = mzt.eq("ZONE_COVERAGE").astype(float); pa["y"] = pa.yards_gained.fillna(0.0)
    known = pa[(pa.m + pa.z) > 0]
    # the opponent's man rate last season; heavy-box rate on runs last season
    dm = known.groupby(["defteam", "season"]).agg(mm=("m", "sum"), c=("m", "size")).reset_index(); dm["opp_man_ly"] = np.where(dm.c >= 150, dm.mm / dm.c, np.nan); dm["season"] += 1
    rn = pl[pl.play_type.eq("run") & pl.defenders_in_box.notna() & (pl.defenders_in_box > 0)].assign(h=lambda x: (x.defenders_in_box >= 8).astype(float))
    bx = rn.groupby(["defteam", "season"]).agg(hh=("h", "sum"), c=("h", "size")).reset_index(); bx["opp_heavy_ly"] = np.where(bx.c >= 150, bx.hh / bx.c, np.nan); bx["season"] += 1
    for kind, idc, kk in (("rec", "receiver_player_id", 30.0), ("pass", "passer_player_id", 100.0)):
        t = known[known[idc].notna()].rename(columns={idc: "pid"})
        ps = t.assign(ym=t.y * t.m, yz=t.y * t.z).groupby(["pid", "season"]).agg(nm=("m", "sum"), nz=("z", "sum"), ym=("ym", "sum"), yz=("yz", "sum")).reset_index().sort_values(["pid", "season"])
        ps[["cnm", "cnz", "cym", "cyz"]] = ps.groupby("pid")[["nm", "nz", "ym", "yz"]].cumsum().values
        lg = t.groupby("season").apply(lambda x: pd.Series({"lm": (x.y * x.m).sum() / x.m.sum(), "lz": (x.y * x.z).sum() / x.z.sum()}))
        X = pd.read_parquet(CACHE / f"X_{kind}.parquet"); f = X[["pid", "season"]].copy(); f["i"] = np.arange(len(f))
        # his sums over every season before this one: the state at the end of his latest earlier season
        f["ks"] = f.season - 1; st = ps.rename(columns={"season": "ks"})[["pid", "ks", "cnm", "cnz", "cym", "cyz"]].sort_values("ks")
        m = pd.merge_asof(f.sort_values("ks"), st, on="ks", by="pid", direction="backward").sort_values("i")
        lm_ = f.season.map(lambda s: lg.lm.get(s - 1, np.nan)).values; lz_ = f.season.map(lambda s: lg.lz.get(s - 1, np.nan)).values
        ypm = (m.cym.fillna(0).values + kk * lm_) / (m.cnm.fillna(0).values + kk); ypz = (m.cyz.fillna(0).values + kk * lz_) / (m.cnz.fillna(0).values + kk)
        s_mz = np.log(ypm / ypz) - np.log(lm_ / lz_)
        X = X.drop(columns=[c for c in ("opp_man", "opp_heavy", "mz_split", "mz_x_man", "mz_n", "opp_man_ly", "opp_heavy_ly") if c in X.columns])
        X = X.merge(dm[["defteam", "season", "opp_man_ly"]], on=["defteam", "season"], how="left").merge(bx[["defteam", "season", "opp_heavy_ly"]], on=["defteam", "season"], how="left")
        lgman = X.groupby("season").opp_man_ly.transform("mean")
        X["mz_split"] = s_mz; X["mz_x_man"] = np.where(np.isfinite(s_mz) & X.opp_man_ly.notna(), np.nan_to_num(s_mz) * (X.opp_man_ly - lgman), np.nan)
        X["mz_n"] = (m.cnm.fillna(0) + m.cnz.fillna(0)).values; X.to_parquet(CACHE / f"X_{kind}.parquet"); log("man/zone", kind, "coverage", float(np.isfinite(X.mz_x_man).mean()))
    X = pd.read_parquet(CACHE / "X_rush.parquet").drop(columns=[c for c in ("opp_heavy_ly", "opp_man_ly") if c in pd.read_parquet(CACHE / "X_rush.parquet").columns])
    X = X.merge(bx[["defteam", "season", "opp_heavy_ly"]], on=["defteam", "season"], how="left"); X.to_parquet(CACHE / "X_rush.parquet")
    # ---- shadow index (play-by-play credits, weekly) ----
    fr = pd.read_parquet(CACHE / "frame_rec.parquet", columns=["pid", "posteam", "defteam", "season", "week", "game_id", "pos", "vol"])
    wr = fr[fr.pos.eq("WR")].sort_values("vol", ascending=False).drop_duplicates(["game_id", "posteam"])[["game_id", "posteam", "pid"]].rename(columns={"pid": "wr1"})
    wrs = set(fr[fr.pos.eq("WR")].pid)
    pw = pl[pl.play_type.eq("pass") & pl.receiver_player_id.isin(wrs)].merge(wr, on=["game_id", "posteam"], how="inner"); pw["is1"] = (pw.receiver_player_id == pw.wr1).astype(float)
    cred_cols = ["solo_tackle_1_player_id", "solo_tackle_2_player_id", "assist_tackle_1_player_id", "assist_tackle_2_player_id", "pass_defense_1_player_id", "pass_defense_2_player_id", "interception_player_id"]
    cr = pd.concat([pw[["game_id", "season", "week", "posteam", "is1", c]].rename(columns={c: "cb"}) for c in cred_cols]).dropna(subset=["cb"])
    share1 = pw.groupby(["game_id", "posteam"]).is1.mean().rename("s1").reset_index(); cr = cr.merge(share1, on=["game_id", "posteam"])
    cg = cr.groupby(["cb", "season", "week", "game_id"]).agg(c1=("is1", "sum"), cw=("is1", "size"), e=("s1", "sum")).reset_index().sort_values(["cb", "season", "week"])
    cg[["C1", "CW", "E"]] = cg.groupby("cb")[["c1", "cw", "e"]].cumsum().values; cg["key"] = _key(cg.season, cg.week); cg["shadow"] = (cg.C1 - cg.E) / (cg.CW + 10.0)
    per = cr.groupby(["cb", "season"]).agg(c1=("is1", "sum"), cw=("is1", "size"), e=("s1", "sum")).reset_index(); per = per[per.cw >= 20]; per["ix"] = (per.c1 - per.e) / per.cw
    nx = per.merge(per.assign(season=per.season - 1), on=["cb", "season"], suffixes=("", "_next"))
    shadow_persist = float(np.corrcoef(nx.ix, nx.ix_next)[0, 1]) if len(nx) > 20 else np.nan
    ed = ED[["game_id", "defteam", "cb_list", "season", "week"]].copy(); ed["key"] = _key(ed.season, ed.week)
    rows = ed.explode("cb_list").dropna(subset=["cb_list"]); rows["cb"] = rows.cb_list.map(lambda t: t[0]); rows["sh"] = rows.cb_list.map(lambda t: t[1]); rows["rt"] = rows.cb_list.map(lambda t: t[2])
    rows = pd.merge_asof(rows.sort_values("key"), cg[["cb", "key", "shadow", "CW"]].sort_values("key"), on="key", by="cb", direction="backward", allow_exact_matches=False)
    rows["is_shadow"] = (rows.shadow >= 0.15) & (rows.CW >= 20)
    top = rows.dropna(subset=["rt"]).sort_values("rt", ascending=False).drop_duplicates(["game_id", "defteam"])
    top = top[top.is_shadow][["game_id", "defteam", "cb", "rt"]].rename(columns={"cb": "shadow_cb", "rt": "shadow_rt"})
    rest = rows.dropna(subset=["rt"]).merge(top[["game_id", "defteam", "shadow_cb"]], on=["game_id", "defteam"], how="inner"); rest = rest[rest.cb != rest.shadow_cb]
    rest = rest.assign(w=rest.sh * rest.rt).groupby(["game_id", "defteam"]).agg(w=("w", "sum"), s=("sh", "sum")).reset_index(); rest["rest_rt"] = rest.w / rest.s
    X = pd.read_parquet(CACHE / "X_rec.parquet"); fr = fr.reset_index(drop=True); fr["i"] = np.arange(len(fr)); fr = fr.merge(wr, on=["game_id", "posteam"], how="left").sort_values("i")
    q = fr[["i", "game_id", "defteam", "pid", "pos", "wr1"]].merge(top, on=["game_id", "defteam"], how="left").merge(rest[["game_id", "defteam", "rest_rt"]], on=["game_id", "defteam"], how="left").sort_values("i")
    unit = X.opp_cb_r.values; isw = q.pos.eq("WR").values; sh = q.shadow_cb.notna().values; one = (q.pid.values == q.wr1.values)
    X["cb_shadow_assign"] = np.where(~isw, np.nan, np.where(sh & one, q.shadow_rt.values, np.where(sh, np.where(np.isnan(q.rest_rt.values), unit, q.rest_rt.values), unit)))
    X["cb_unit_wr"] = np.where(isw, unit, np.nan); X["vs_shadow_wr1"] = (isw & sh & one).astype(float)
    X.to_parquet(CACHE / "X_rec.parquet")
    # ---- pair table: receiver x defender on the field on his targets, per game (share of his targets with him on) ----
    tp = pl[pl.play_type.eq("pass") & pl.receiver_player_id.notna() & pl.defense_players.notna()].copy(); tp["dp"] = tp.defense_players.str.split(";")
    ex = tp[["game_id", "season", "week", "receiver_player_id", "dp"]].explode("dp").rename(columns={"receiver_player_id": "pid", "dp": "cb"})
    tt = tp.groupby(["receiver_player_id", "game_id"]).size().rename("tg").reset_index().rename(columns={"receiver_player_id": "pid"})
    pr = ex.groupby(["pid", "cb", "game_id", "season", "week"]).size().rename("on").reset_index().merge(tt, on=["pid", "game_id"]); pr["v"] = pr.on / pr.tg
    pr.to_parquet(CACHE / "pairs.parquet")
    meta = {"shadow_persist": shadow_persist, "shadow_flag_share": float(rows.is_shadow.mean()), "shadow_rows_wr1": int((isw & sh & one).sum()), "cb_rows": int(len(rows)), "pairs": int(len(pr)),
            "corner_seasons_with_20_credits": int(len(per))}
    pd.Series(meta).to_json(CACHE / "pvp_meta.json"); log("pvp meta", meta)


# ------------------------------------------------------------------------------------------------------------- ideas
# (family, name, type, column, kinds, by position, what it is)
ALLK = ("rec", "rush", "pass"); RR = ("rec", "rush")
IDEAS = [
    # ---- Task A: situation ----
    ("Situational", "turf", "L", "turf", ALLK, True, "artificial turf (the schedule's surface) against grass"),
    ("Situational", "indoor", "L", "indoor", ALLK, True, "dome or closed roof (as the game model's dome input)"),
    ("Situational", "dome_fixed", "L", "dome_fixed", ALLK, True, "fixed dome only"),
    ("Situational", "home", "L", "home", ALLK, True, "home (neutral sites 0)"),
    ("Situational", "division", "L", "div", ALLK, True, "division opponent"),
    ("Situational", "short_week", "L", "short_week", ALLK, True, "5 or fewer days of rest"),
    ("Situational", "off_bye", "L", "off_bye", ALLK, True, "13+ days of rest"),
    ("Situational", "rest_days", "L", "rest_days", ALLK, True, "days of rest (4 to 14), per day"),
    ("Situational", "rest_diff", "L", "rest_diff", ALLK, True, "own rest minus the opponent's (-7 to 7), per day"),
    ("Situational", "opp_off_bye", "L", "opp_off_bye", ALLK, True, "the opponent off a bye"),
    ("Situational", "travel", "L", "travel", ALLK, True, "km from the team's home stadium to the venue, per 1,000"),
    ("Situational", "tz_signed", "L", "tz_signed", ALLK, True, "time-zone shift of the venue from home, hours (east +)"),
    ("Situational", "tz_abs", "L", "tz_abs", ALLK, True, "time zones crossed, hours"),
    ("Situational", "altitude", "L", "altitude", ALLK, True, "a visitor at Denver"),
    ("Situational", "vs_former_team", "L", "vs_former", ALLK, True, "against a team he played for before (snap counts)"),
    ("Situational", "own_turf_split", "P", "turf", ALLK, False, "his own turf/grass split, shrunk toward the league's"),
    ("Situational", "own_indoor_split", "P", "indoor", ALLK, False, "his own indoor/outdoor split"),
    ("Situational", "own_home_split", "P", "home", ALLK, False, "his own home/away split"),
    ("Situational", "own_division_split", "P", "div", ALLK, False, "his own split against division opponents"),
    ("Situational", "at_stadium", "H", "stadium_id", ALLK, False, "his residual history at this stadium"),
    ("Situational", "vs_head_coach", "H", "opp_coach", ALLK, False, "his residual history against this opposing head coach"),
    ("Situational", "vs_opponent", "H", "defteam", ALLK, False, "his residual history against this opponent"),
    # ---- Primetime and kickoff time ----
    ("Primetime and kickoff time", "primetime", "L", "primetime", ALLK, True, "the schedule's primetime flag"),
    ("Primetime and kickoff time", "night", "L", "night", ALLK, True, "kickoff 7 PM ET or later, or SNF / MNF / TNF"),
    ("Primetime and kickoff time", "slot_early", "L", "early", ALLK, True, "Sunday 1 PM ET"),
    ("Primetime and kickoff time", "slot_late", "L", "late", ALLK, True, "Sunday 4 PM ET"),
    ("Primetime and kickoff time", "SNF", "L", "snf", ALLK, True, "Sunday night"),
    ("Primetime and kickoff time", "MNF", "L", "mnf", ALLK, True, "Monday night"),
    ("Primetime and kickoff time", "TNF", "L", "tnf", ALLK, True, "Thursday night (by position: the short-week usage shift)"),
    ("Primetime and kickoff time", "thursday", "L", "thu", ALLK, True, "any Thursday game"),
    ("Primetime and kickoff time", "saturday", "L", "sat", ALLK, True, "Saturday"),
    ("Primetime and kickoff time", "sunday", "L", "sun", ALLK, True, "Sunday"),
    ("Primetime and kickoff time", "monday", "L", "mon", ALLK, True, "Monday"),
    ("Primetime and kickoff time", "west_team_1pm", "L", "west_1pm", ALLK, True, "a Pacific/Mountain team away at 1 PM ET (body clock 10 AM)"),
    ("Primetime and kickoff time", "east_team_late_west", "L", "east_late_west", ALLK, True, "an Eastern team at a Pacific venue, kickoff 8 PM ET or later"),
    ("Primetime and kickoff time", "body_clock_hour", "L", "body_hour", ALLK, True, "kickoff hour on the team's home clock, per hour"),
    ("Primetime and kickoff time", "holiday", "L", "holiday", ALLK, True, "Thanksgiving, Black Friday, Christmas Day"),
    ("Primetime and kickoff time", "international", "L", "international", ALLK, True, "London, Germany, Mexico, Brazil and the other foreign venues"),
    ("Primetime and kickoff time", "own_primetime_split", "P", "primetime", ALLK, False, "his own primetime split, shrunk toward the league's"),
    ("Primetime and kickoff time", "own_night_split", "P", "night", ALLK, False, "his own night-game split"),
    # ---- Weather ----
    ("Weather", "wind_over_10", "L", "wind10", ALLK, True, "mph of kickoff wind above 10, outdoors (passing: on top of the live WIND_C)"),
    ("Weather", "rain", "L", "rain", ALLK, True, "rain at kickoff (outdoors)"),
    ("Weather", "snow", "L", "snow", ALLK, True, "snow at kickoff (outdoors)"),
    ("Weather", "cold", "L", "cold", ALLK, True, "under 35 F outdoors"),
    ("Weather", "bad_weather", "L", "bad", ALLK, True, "any of wind 15+, rain, snow, cold"),
    ("Weather", "warm_team_in_cold", "L", "warm_in_cold", ALLK, True, "a warm-climate or dome team outdoors under 35 F (the game model's list)"),
    ("Weather", "bad_x_turf", "L", "bad_turf", ALLK, True, "bad weather on turf"),
    ("Weather", "bad_x_grass", "L", "bad_grass", ALLK, True, "bad weather on grass"),
    ("Weather", "bad_x_night", "L", "bad_night", ALLK, True, "bad weather at night"),
    ("Weather", "wind_x_turf", "L", "wind_turf", ALLK, True, "wind above 10 on turf"),
    ("Weather", "own_bad_weather_split", "P", "bad", ALLK, False, "his own bad-weather split, shrunk toward the league's"),
    # ---- Injuries ----
    ("Injuries", "teammate_out_same_group", "L", "same_out", RR, True, "shares of known-out starters at his position group (on top of ABSORB)"),
    ("Injuries", "teammate_out_cross", "L", "cross_out", ("rec",), True, "known-out starters at the other receiving groups (WR out for TE / RB, TE out for WR)"),
    ("Injuries", "wr_out", "L", "wr_out", ALLK, True, "known-out WR starters' shares"),
    ("Injuries", "te_out", "L", "te_out", ALLK, True, "known-out TE starters' shares"),
    ("Injuries", "rb_out", "L", "rb_out", ALLK, True, "known-out RB starters' shares (RB2 carries and receptions)"),
    ("Injuries", "qb_out", "L", "qb_out", RR, True, "the team's usual starting QB listed out (backup QB)"),
    ("Injuries", "qb_rating", "L", "qb_rating", RR, True, "this week's starter's QB rating, against his history of QBs"),
    ("Injuries", "own_backup_qb_split", "P", "qb_out", RR, False, "each receiver's / rusher's own split with the backup QB"),
    ("Injuries", "ol_out", "L", "ol_out", ALLK, True, "OL starters listed out (QB pass yards; rushing)"),
    ("Injuries", "off_starters_out", "L", "off_starters_out", ALLK, True, "offensive starters listed out"),
    ("Injuries", "opp_cb_out", "L", "opp_cb_out", ("rec", "pass"), True, "the opponent's expected starting CBs known out (snap-weighted)"),
    ("Injuries", "opp_s_out", "L", "opp_s_out", ("rec", "pass"), True, "the opponent's starting safeties known out"),
    ("Injuries", "opp_lb_out", "L", "opp_lb_out", ALLK, True, "the opponent's starting LBs known out (TE and RB receiving; rushing)"),
    ("Injuries", "opp_dl_out", "L", "opp_dl_out", ALLK, True, "the opponent's starting EDGE / IDL known out (rushing; pass yards)"),
    ("Injuries", "opp_def_starters_out", "L", "opp_def_starters_out", ALLK, True, "the opponent's defensive starters listed out (the game model's count)"),
    ("Injuries", "injuries_x_bad_weather", "L", "inj_x_bad", ALLK, True, "offensive starters out x bad weather"),
    ("Injuries", "qb_out_x_bad_weather", "L", "qbout_x_bad", RR, True, "backup QB x bad weather"),
    ("Injuries", "injuries_x_short_week", "L", "inj_x_short", ALLK, True, "offensive starters out x short week"),
    # ---- Player vs player ----
    ("Player vs player", "opp_cb_unit_rating", "L", "opp_cb_r", ("rec", "pass"), True, "this week's expected starting corners' rating (snap-weighted, positions.py recipe)"),
    ("Player vs player", "opp_cb_unit_change", "L", "opp_cb_chg", ("rec", "pass"), True, "that minus the corners who played the defense's last 8 games (the change the allowed rate has not seen)"),
    ("Player vs player", "cb_unit_wr_only", "L", "cb_unit_wr", ("rec",), False, "the corner unit rating on WR rows only"),
    ("Player vs player", "cb_shadow_assigned", "L", "cb_shadow_assign", ("rec",), False, "a shadow corner's own rating on the WR1, the rest of the unit on the other WRs"),
    ("Player vs player", "vs_shadow_corner_wr1", "L", "vs_shadow_wr1", ("rec",), False, "the WR1 against a corner whose credits follow WR1s"),
    ("Player vs player", "man_zone_x_opp_man", "L", "mz_x_man", ("rec", "pass"), True, "his man/zone split (earlier seasons) x the opponent's man rate last season"),
    ("Player vs player", "opp_lb_s_rating", "L", "opp_lbs_r", ("rec",), True, "the opponent's expected LBs and safeties (TE / RB receiving)"),
    ("Player vs player", "opp_lb_s_change", "L", "opp_lbs_chg", ("rec",), True, "that against the last 8 games' unit"),
    ("Player vs player", "opp_front_rating", "L", "opp_front_r", ("rush",), True, "the opponent's expected IDL, LB and EDGE (the run front)"),
    ("Player vs player", "opp_front_change", "L", "opp_front_chg", ("rush",), True, "that against the last 8 games' unit"),
    ("Player vs player", "opp_heavy_box_last_season", "L", "opp_heavy_ly", ("rush",), True, "the opponent's 8+ box rate on runs last season (participation)"),
    ("Player vs player", "opp_pass_rush_rating", "L", "opp_rush_r", ("pass",), False, "the opponent's expected EDGE and IDL"),
    ("Player vs player", "opp_pass_rush_change", "L", "opp_rush_chg", ("pass",), False, "that against the last 8 games' unit"),
    ("Player vs player", "pass_rush_vs_protection", "L", "rush_vs_prot", ("pass",), False, "the opponent's rush rating plus his line's sacks and hits allowed per dropback (both standardised)"),
    ("Player vs player", "vs_specific_corners", "C", "cb_pairs", ("rec",), False, "his residual history against this week's expected corners, counting only his targets with each on the field (earlier seasons)"),
]


def available(z, s):
    """True when the input has a reading (not missing, not constant) in the 2016-17 rows that fit the 2017 and 2018 seasons."""
    m = s <= 2017; v = z[m]; v = v[~np.isnan(v)]
    return len(v) > 30 and np.std(v) > 1e-12


def zc_of(KF, z):
    """z centred on the player's own decayed history of it (missing z: no adjustment)."""
    z = np.asarray(z, float); ok = ~np.isnan(z)
    zz = np.where(ok, z, 0.0); from experiments.situational_props_feats import _seg_decayed
    zs, vs = zz[KF.order], ok[KF.order].astype(float)
    S = _seg_decayed(KF.pid_sorted, np.c_[zs * vs, vs], DECAY); P = S - np.c_[zs * vs, vs]
    q = np.where(P[:, 1] > 1e-9, P[:, 0] / np.where(P[:, 1] > 1e-9, P[:, 1], 1.0), np.nan)[KF.inv]
    q = np.where(np.isnan(q), np.nanmean(z) if ok.any() else 0.0, q)
    return np.where(ok, z - q, 0.0)


class Pairs:
    """His residual history against specific corners: per earlier-season game, each defender's share of his targets
    with that defender on the field (participation); for this game, this week's expected corners (cb_list) weighted by
    expected snap share. s_k = sum over corners of w_c x (sum v lr / (sum v + k)) / sum w_c."""

    def __init__(self, KF):
        pr = pd.read_parquet(CACHE / "pairs.parquet"); ed = pd.read_pickle(CACHE / "expected_defense.pkl")[["game_id", "defteam", "cb_list"]]
        f = KF.f[["pid", "game_id", "season", "defteam"]].copy(); f["i"] = np.arange(len(f))
        cur = f.merge(ed, on=["game_id", "defteam"], how="left").explode("cb_list").dropna(subset=["cb_list"])
        cur["cb"] = cur.cb_list.map(lambda t: t[0]); cur["w"] = cur.cb_list.map(lambda t: t[1]); self.cur = cur[["i", "pid", "season", "cb", "w"]].reset_index(drop=True)
        self.pr = pr.merge(f[["pid", "game_id", "i"]].rename(columns={"i": "row"}), on=["pid", "game_id"], how="inner")   # only games that are frame rows carry a residual
        self.KF = KF

    def svals(self, lr, cur=None):
        cur = self.cur if cur is None else cur
        h = self.pr.assign(vl=self.pr.v * lr[self.pr.row.values]).groupby(["pid", "cb", "season"]).agg(v=("v", "sum"), vl=("vl", "sum")).reset_index().sort_values(["pid", "cb", "season"])
        h[["cv", "cvl"]] = h.groupby(["pid", "cb"])[["v", "vl"]].cumsum().values; h["season"] = h.season + 1   # the state entering the next season
        m = pd.merge_asof(cur.sort_values("season"), h[["pid", "cb", "season", "cv", "cvl"]].sort_values("season"), on="season", by=["pid", "cb"], direction="backward")
        out = {}
        for k in KS_H:
            m["s"] = np.where(m.cv.notna(), m.cvl.fillna(0) / (m.cv.fillna(0) + k), 0.0); g = m.assign(ws=m.w * m.s).groupby("i").agg(ws=("ws", "sum"), w=("w", "sum"))
            v = np.zeros(self.KF.n); v[g.index.values] = (g.ws / g.w.replace(0, np.nan)).fillna(0.0).values; out[k] = v
        self.n_shared = m.cv.fillna(0.0).values; return out


def make_cands(st, typ, raw, fitmask, pairs=None):
    if typ == "L":
        zc = zc_of(st.K, raw); c, sd = cands_L(zc, fitmask); return c, {"sd": sd, "zc": zc}
    if typ == "P":
        return cands_S(svals_P(st, raw)), {}
    if typ == "H":
        return cands_S(svals_H(st, raw)), {}
    if typ == "C":
        return cands_S(pairs.svals(st.lr, raw)), {}
    raise ValueError(typ)


def shuffle_within(raw, season, rng):
    idx = np.arange(len(season))
    for s_ in np.unique(season):
        m = np.flatnonzero(season == s_); idx[m] = rng.permutation(m)
    if isinstance(raw, pd.DataFrame):
        return raw.iloc[idx].reset_index(drop=True)
    return np.asarray(raw)[idx]


def describe_fit(typ, choice, cands, gnames, lines=None, groups=None, season=None, binary=True, sd=1.0):
    """The size the live code would use (the last refit, on 2016-2025), per group: for L the change per unit of the input
    (in % and, at the group's mean line over 2019-25, in the stat's units); for P / H / C the weight c and shrinkage k."""
    out, eff = [], {}
    for g_ in range(choice.shape[1]):
        j = choice[-1, g_]; lab = cands[j][2]
        if typ == "L":
            unit = 1.0 if binary else sd; pct = 100 * (np.exp(lab * unit) - 1); ml = float(np.mean(lines[(groups == g_) & (season >= 2019) & (season <= 2025)])) if lines is not None else np.nan
            u = "on vs off" if binary else f"per sd ({sd:.3g})"
            out.append(f"{gnames[g_]} {pct:+.2f}% {u} ({pct / 100 * ml:+.2f} at a {ml:.1f} line)"); eff[gnames[g_]] = (pct, pct / 100 * ml)
        else:
            out.append(f"{gnames[g_]} k={lab[0]} c={lab[1]:+.2f}"); eff[gnames[g_]] = lab
    return "; ".join(out), eff
# --------------------------------------------------------------------------------------------------------------- run
KF_, ST_, PAIRS_ = {}, {}, {}


def setup():
    G = pd.read_parquet(CACHE / "G.parquet")
    for kind in ALLK: KF_[kind] = K(kind, G)
    for name, spec in STATS.items(): ST_[name] = Stat(name, KF_[spec[0]])
    PAIRS_["rec"] = Pairs(KF_["rec"]); log("frames", {k: v.n for k, v in KF_.items()})


def raw_of(KF, typ, col):
    if typ == "C": return PAIRS_["rec"].cur
    v = KF.f[col].values
    return v.astype(float) if typ == "L" else (np.nan_to_num(v.astype(float)) if typ == "P" else v)


def one_fit(st, typ, raw, groups, has1718):
    fitmask = st.K.season <= 2017
    if not has1718: fitmask = st.K.season <= 2025
    cands, extra = make_cands(st, typ, raw, fitmask, PAIRS_.get("rec"))
    lv, lm, choice = st.fit(cands, groups)
    return lv, lm, choice, cands


def rule1(W, has1718):
    ok = all(W[w][0] < 0 for w in ("2019-22", "2023-25"))
    return ok and (W["2017-18"][0] < 0 if has1718 else W["2017-18"][0] <= 1e-12)


def placebo_job(args):
    """50 draws of the input shuffled within season, refitted walk-forward the same way. Returns per window the number of
    draws whose gain is below the real one, and the draws' diffs."""
    name, typ, col, sname, vname, real, has1718, seed = args
    st = ST_[sname]; KF = st.K; groups = KF.pos_group if vname == "by position" else None; rng = np.random.default_rng(seed)
    raw = raw_of(KF, typ, col); diffs = {w: [] for w in WIN3}
    for _ in range(N_PLACEBO):
        if typ == "C":
            perm = shuffle_within(np.arange(KF.n), KF.season, rng); rp = raw.copy(); rp["i"] = perm[rp.i.values]
            rp["season"] = KF.season[rp.i.values]; rp["pid"] = KF.f.pid.values[rp.i.values]; r_ = rp
        else:
            r_ = shuffle_within(raw, KF.season, rng)
        lv, _, _, _ = one_fit(st, typ, r_, groups, has1718); W = st.windows(lv)
        for w in WIN3: diffs[w].append(W[w][0])
    beat = {w: int(sum(d > real[w] for d in diffs[w])) for w in WIN3}   # draws whose diff is above (worse than) the real diff
    return (name, sname, vname), beat, {w: [round(x, 5) for x in v] for w, v in diffs.items()}


def run_ideas(families=None):
    rows, keep = [], {}
    for fam, name, typ, col, kinds, bypos, desc in IDEAS:
        if families and fam not in families: continue
        if os.environ.get("SIT_ONLY") and name not in os.environ["SIT_ONLY"].split(","): continue
        t1 = time.time()
        for sname, st in ST_.items():
            KF = st.K
            if KF.kind not in kinds: continue
            raw = raw_of(KF, typ, col)
            if typ == "C":
                has1718 = bool((st.K.season[raw.i.values] <= 2017).any())
            else:
                zz = raw.astype(float) if typ != "H" else pd.Series(raw).notna().astype(float).values
                has1718 = available(zz, KF.season) if typ != "H" else True
            variants = [("pooled", None)] + ([("by position", KF.pos_group)] if bypos and KF.kind in POSG else [])
            for vname, groups in variants:
                lv, lm, choice, cands = one_fit(st, typ, raw, groups, has1718)
                W = st.windows(lv); r1 = rule1(W, has1718)
                gn = POSG_NAME[KF.kind] if groups is not None else ["all"]
                rv = raw.astype(float) if typ == "L" else None; binary = bool(typ == "L" and np.isin(rv[~np.isnan(rv)], (0.0, 1.0)).all())
                sd_raw = float(np.nanstd(rv)) if typ == "L" else 1.0
                fitdesc, eff = describe_fit(typ, choice, cands, gn, st.line, groups if groups is not None else np.zeros(KF.n, dtype=int), KF.season, binary, sd_raw)
                row = {"family": fam, "idea": name, "type": typ, "variant": vname, "stat": sname, "has_2017_18": has1718, "what": desc, "fit_2026": fitdesc,
                       **{f"diff_{w}": round(W[w][0], 5) for w in WIN3}, **{f"se_{w}": round(W[w][1], 5) for w in WIN3}, **{f"base_{w}": round(W[w][2], 4) for w in WIN3}, "rule1": r1}
                rows.append(row)
                if r1: keep[(name, sname, vname)] = {"lm": lm, "typ": typ, "col": col, "has1718": has1718, "W": W, "row": row, "eff": eff}
        log(fam, name, f"{time.time() - t1:.0f}s", "rule 1 passes:", [k for k in keep if k[0] == name])
    return rows, keep


def rule2(keep):
    for key, v in keep.items():
        st = ST_[key[1]]; line_var = st.line * np.exp(v["lm"]); row = v["row"]
        ok = True
        if st.name in CHANCE_OF:
            ch = chance_ll(st, line_var)
            for w, (b_, v_, n_) in ch.items():
                row[f"chance_ll_diff_{w}"] = round(v_ - b_, 6) if n_ else None; row[f"chance_ll_base_{w}"] = round(b_, 5) if n_ else None
                if n_ and v_ > b_ + 1e-12: ok = False
        lr_ = lean_record(st, line_var)
        if lr_:
            row["lean_rule"] = f"{lr_[0]}-{lr_[1]}"; row["lean_variant"] = f"{lr_[2]}-{lr_[3]}"; row["lean_n"] = lr_[4]
            if (lr_[2] - lr_[3]) < (lr_[0] - lr_[1]): ok = False
        row["rule2"] = ok
    return keep


def run_placebos(keep, workers=4):
    import multiprocessing as mp
    jobs = []
    for i, (key, v) in enumerate(keep.items()):
        if not v["row"].get("rule2"): continue
        real = {w: v["W"][w][0] for w in WIN3}; jobs.append((key[0], v["typ"], v["col"], key[1], key[2], real, v["has1718"], 1000 + i))
    log("placebo jobs", len(jobs))
    if not jobs: return keep
    with mp.get_context("fork").Pool(workers) as pool:
        for (key, beat, diffs) in pool.imap_unordered(placebo_job, jobs):
            v = keep[key]; row = v["row"]; wins = [w for w in WIN3 if v["has1718"] or w != "2017-18"]
            row.update({f"placebo_beat_{w}": beat[w] for w in WIN3}); row["placebo_min_pct"] = min(beat[w] for w in wins) / N_PLACEBO
            row["rule3"] = all(beat[w] >= PLACEBO_NEED for w in wins); v["placebo"] = diffs; log("placebo", key, beat, row["rule3"])
    return keep
# ------------------------------------------------------------------------------------------------------------ Task B
class Rule:
    """The live rule after the mean: median factor -> the team reconciliation over the frame's players of the team-game
    (round 6) -> the injury report and snap trend (round 13), as props_by_season.build applies them."""

    def __init__(self, KF):
        f = KF.f; kind = KF.kind; self.kind = kind
        self.codes = pd.factorize(f.game_id.astype(str) + "|" + f.posteam.astype(str))[0]; self.ngrp = self.codes.max() + 1
        fy = PR.TEAM_FIT[kind]["yds"]; self.exp_y = fy[0] + fy[1] * f.exp_pts.values.astype(float); self.ok = ~np.isnan(f.exp_pts.values.astype(float)); self.wy = PR.RECON_W[kind]["yds"]
        self.r13 = f.r13.values.astype(float); self.mean = f.mean_line.values.astype(float)

    def recon(self, line):
        s_ = np.bincount(self.codes, weights=line, minlength=self.ngrp)[self.codes]
        with np.errstate(divide="ignore", invalid="ignore"): sc = np.clip(self.exp_y / np.where(s_ == 0, np.nan, s_), 0.5, 2.0)
        return np.where(self.ok & ~np.isnan(sc), line * (1 + self.wy * (sc - 1)), line)

    def yds(self, mean=None, medf=None):
        mean = self.mean if mean is None else mean; medf = PR.med_factor(self.kind, mean) if medf is None else medf
        return self.recon(medf * mean) * self.r13


MED_FORMS = {"flat refit": (lambda p, m: np.full(len(m), p[0]), [[0.84]]),
             "linear": (lambda p, m: np.clip(p[0] + p[1] * m, 0.5, 1.2), [[0.84, 0.0], [0.72, 0.003]]),
             "logistic, scale 5": (lambda p, m: p[0] + (p[1] - p[0]) / (1 + np.exp(-(m - p[2]) / 5.0)), [[0.75, 0.9, 30.0], [0.8, 0.88, 50.0]]),
             "logistic, free scale": (lambda p, m: p[0] + (p[1] - p[0]) / (1 + np.exp(-(m - p[2]) / max(abs(p[3]), 0.5))), [[0.75, 0.9, 30.0, 5.0], [0.8, 0.88, 50.0, 10.0]])}


def med_walkforward(R, act, season, form, arg=None):
    """The rushing median factor of `form` in the mean, refitted walk-forward (Nelder-Mead on the yards MAE with the team
    reconciliation applied, every season before the scored one from 2016). arg: the curve's input (the mean, or a
    shuffled mean for the placebo). Returns the line and the parameters per season."""
    from scipy.optimize import minimize
    fn, inits = MED_FORMS[form]; arg = R.mean if arg is None else arg; line = R.yds(); params = {}
    for s_ in range(2017, 2027):
        m = (season >= 2016) & (season < s_)
        obj = lambda p: float(np.abs(R.yds(medf=fn(p, arg))[m] - act[m]).mean())
        best = None
        for p0 in inits:
            r = minimize(obj, np.array(p0, float), method="Nelder-Mead", options={"xatol": 1e-4, "fatol": 1e-5, "maxiter": 3000})
            if best is None or r.fun < best.fun: best = r
        params[s_] = best.x; full = R.yds(medf=fn(best.x, arg)); line = np.where(season == s_, full, line)
    return line, params


def task_b1(workers=4):
    st = ST_["rush_yards"]; KF = st.K; R = Rule(KF); rep = float(np.nanmax(np.abs(R.yds() - st.line))); out, keep = [], {}
    log("B1 rule reproduction max diff", rep)
    for form in MED_FORMS:
        line, params = med_walkforward(R, st.act, KF.season, form); lv = st.lf(line, st.act); W = st.windows(lv); r1 = rule1(W, True)
        row = {"family": "Task B", "idea": f"rushing median factor: {form}", "type": "B", "variant": "pooled", "stat": "rush_yards", "has_2017_18": True,
               "what": "the rushing median factor as a function of the mean, refitted walk-forward, against the flat 0.84",
               "fit_2026": ", ".join(f"{x:.4f}" for x in params[2026]), **{f"diff_{w}": round(W[w][0], 5) for w in WIN3}, **{f"se_{w}": round(W[w][1], 5) for w in WIN3},
               **{f"base_{w}": round(W[w][2], 4) for w in WIN3}, "rule1": r1}
        out.append(row); log("B1", form, {w: round(W[w][0], 4) for w in WIN3}, r1)
        if r1: keep[(row["idea"], "rush_yards", "pooled")] = {"lm": np.log(np.where(st.line > 0, line / np.where(st.line > 0, st.line, 1), 1.0)), "typ": "B1", "col": form, "has1718": True, "W": W, "row": row, "line": line}
    rule2(keep)
    for key, v in keep.items():
        if not v["row"].get("rule2"): continue
        rng = np.random.default_rng(77); diffs = {w: [] for w in WIN3}
        for _ in range(N_PLACEBO):
            arg = shuffle_within(R.mean, KF.season, rng); line, _ = med_walkforward(R, st.act, KF.season, v["col"], arg); W = st.windows(st.lf(line, st.act))
            for w in WIN3: diffs[w].append(W[w][0])
        beat = {w: int(sum(d > v["W"][w][0] for d in diffs[w])) for w in WIN3}; v["row"].update({f"placebo_beat_{w}": beat[w] for w in WIN3})
        v["row"]["placebo_min_pct"] = min(beat.values()) / N_PLACEBO; v["row"]["rule3"] = all(b >= PLACEBO_NEED for b in beat.values()); log("B1 placebo", key, beat)
    return out, keep


def share_sums_known(KF, roster_too=False):
    """Per rec frame row: the sum of the round-17 blended shares over the roster the card can know for the team-game:
    the frame's players (their share after round 18's absorption) plus anyone with a profile (8+ targets over his previous
    17 games with a target, 3+ games) who took a snap at a receiving position for the team in one of its last three games,
    less this week's Out and Doubtful (roster_too: and anyone without an active roster listing that week)."""
    f = KF.f; b = PR.GS["rec"]; tplays = f.tv.values / f.tgames.values + b[0] + b[1] * f.me.values + b[2] * f.tc.values
    share_f = np.where(tplays > 0, f.vol.values / tplays, 0.0)
    S = pd.Series(share_f).groupby([f.game_id.values, f.posteam.values]).sum()
    sx = pd.read_parquet(OUT / "snap_exposure.parquet", columns=["player_id", "game_id", "season", "week", "team", "position", "off_pct"]).rename(columns={"player_id": "pid"})
    sx = sx[(sx.off_pct > 0) & sx.position.isin(PR.SKILL["rec"]) & (sx.season >= 2015)]
    tg = sx[["team", "game_id", "season", "week"]].drop_duplicates().sort_values(["team", "season", "week"]).reset_index(drop=True); tg["k"] = tg.groupby("team").cumcount()
    sx = sx.merge(tg[["team", "game_id", "k"]], on=["team", "game_id"])
    C = pd.concat([sx[["pid", "team", "k"]].assign(k=sx.k + o) for o in (1, 2, 3)]).drop_duplicates().merge(tg, on=["team", "k"]).rename(columns={"team": "posteam"})
    C = C.merge(f[["pid", "game_id"]].assign(inframe=1), on=["pid", "game_id"], how="left"); C = C[C.inframe.isna()].drop(columns=["inframe"])
    rep = pd.read_parquet(CACHE / "reports.parquet"); od = rep[rep.report_status.isin(["Out", "Doubtful"])][["season", "week", "pid"]].assign(out=1)
    C = C.merge(od.drop_duplicates(), on=["season", "week", "pid"], how="left"); C = C[C.out.isna()]
    if roster_too:
        ko = pd.read_parquet(CACHE / "known_out.parquet")[["season", "week", "pid"]].drop_duplicates().assign(ko=1); C = C.merge(ko, on=["season", "week", "pid"], how="left"); C = C[C.ko.isna()]
    pg = pd.read_parquet(CACHE / "pg_rec.parquet")[["pid", "game_id", "season", "week", "n"]]; Rr = pd.read_parquet(CACHE / "R_rec.parquet").rename(columns={"n": "n17"})
    el = pg.merge(Rr, on=["pid", "game_id"]); el["n17p"] = el.n17 + el.n; el["gp"] = el.games_prev + 1; el["key"] = _key(el.season, el.week)
    post = pd.read_parquet(CACHE / "post_rec.parquet")
    C["key"] = _key(C.season, C.week); C = C.sort_values("key")
    C = pd.merge_asof(C, el[["pid", "key", "n17p", "gp"]].sort_values("key"), on="key", by="pid", direction="backward", allow_exact_matches=False)
    C = pd.merge_asof(C.sort_values("key"), post.sort_values("key"), on="key", by="pid", direction="backward", allow_exact_matches=False)
    C = C[(C.n17p >= 8) & (C.gp >= 3) & C.s_touch.notna()]
    C["sh"] = PR.share_blend("rec", C.s_touch, C.s_active.fillna(C.s_touch))
    add = C.groupby(["game_id", "posteam"]).sh.sum()
    tot = S.add(add, fill_value=0.0)
    return np.array([tot.get((g, t), 1.0) for g, t in zip(f.game_id.values, f.posteam.values)]), share_f, C


def task_b2():
    KF = KF_["rec"]; R = Rule(KF); out, keep = [], {}
    log("B2 rule reproduction max diff", float(np.nanmax(np.abs(R.yds() - KF.f.yds_line.values))))
    for label, roster_too in (("Out/Doubtful removed (as specified)", False), ("Out/Doubtful and inactive roster removed", True)):
        S, share_f, C = share_sums_known(KF, roster_too); cap = np.minimum(1.0, 1.0 / np.where(S > 0, S, 1.0))
        log("B2", label, "share sum > 1 on", float((S > 1).mean()), "mean sum", float(S.mean()), "absent candidates", len(C))
        mean_c = R.mean * cap; lines = {"rec_yards": R.yds(mean_c), "rec_catches": KF.f.catch_line.values * cap, "rec_targets": KF.f.vol.values * cap}
        for sname, line in lines.items():
            st = ST_[sname]; lv = st.lf(line, st.act); W = st.windows(lv); r1 = rule1(W, True)
            row = {"family": "Task B", "idea": f"receiving shares capped at one: {label}", "type": "B", "variant": "pooled", "stat": sname, "has_2017_18": True,
                   "what": "shares scaled by min(1, 1 / sum) over the roster the card can know", "fit_2026": f"sum > 1 on {100 * (S > 1).mean():.1f}% of rows",
                   **{f"diff_{w}": round(W[w][0], 5) for w in WIN3}, **{f"se_{w}": round(W[w][1], 5) for w in WIN3}, **{f"base_{w}": round(W[w][2], 4) for w in WIN3}, "rule1": r1}
            out.append(row); log("B2", label, sname, {w: round(W[w][0], 4) for w in WIN3}, r1)
            if r1: keep[(row["idea"], sname, "pooled")] = {"lm": np.log(np.where(st.line > 0, line / np.where(st.line > 0, st.line, 1), 1.0)), "typ": "B2", "col": label, "has1718": True, "W": W, "row": row, "S": S, "line": line}
    rule2(keep)
    # placebo: the team-game's sum shuffled among the team-games of the season
    f = KF.f; tgk = pd.factorize(f.game_id.astype(str) + "|" + f.posteam.astype(str))[0]
    for key, v in keep.items():
        if not v["row"].get("rule2"): continue
        st = ST_[key[1]]; S = v["S"]; rng = np.random.default_rng(99); diffs = {w: [] for w in WIN3}
        first = pd.Series(np.arange(len(tgk))).groupby(tgk).first().values; tseason = KF.season[first]; tS = S[first]
        for _ in range(N_PLACEBO):
            Sp = shuffle_within(tS, tseason, rng)[tgk]; cap = np.minimum(1.0, 1.0 / np.where(Sp > 0, Sp, 1.0))
            line = {"rec_yards": lambda: R.yds(R.mean * cap), "rec_catches": lambda: f.catch_line.values * cap, "rec_targets": lambda: f.vol.values * cap}[key[1]]()
            W = st.windows(st.lf(line, st.act))
            for w in WIN3: diffs[w].append(W[w][0])
        beat = {w: int(sum(d > v["W"][w][0] for d in diffs[w])) for w in WIN3}; v["row"].update({f"placebo_beat_{w}": beat[w] for w in WIN3})
        v["row"]["placebo_min_pct"] = min(beat.values()) / N_PLACEBO; v["row"]["rule3"] = all(b >= PLACEBO_NEED for b in beat.values()); log("B2 placebo", key, beat)
    return out, keep


def readings_absorb():
    """The injury rules already live, re-checked alone: the rule without round 18's absorption, and without round 13's
    own-report factor (readings: removing a live piece, walk-forward is not needed)."""
    out = []
    for kind, sname in (("rec", "rec_yards"), ("rush", "rush_yards")):
        KF = KF_[kind]; R = Rule(KF); st = ST_[sname]; f = KF.f
        b = PR.GS[kind]; tpl = f.tv.values / f.tgames.values
        if kind == "rush": tpl = (1 - PR.PACE["rush"]) * tpl + PR.PACE["rush"] * f.a_tr.values / f.agames.values
        tpl = tpl + b[0] + b[1] * f.me.values + b[2] * f.tc.values; sh_now = f.vol.values / tpl; r_ = np.where(sh_now > 0, f.share_pre_abs.values / sh_now, 1.0)
        variants = {"without ABSORB (round 18)": R.yds(R.mean * r_), "without the own injury-report factor (round 13)": R.yds() / f.inj.values}
        for lab, line in variants.items():
            W = st.windows(st.lf(line, st.act))
            out.append({"family": "Injuries", "idea": f"live rule {lab}", "type": "R", "variant": "reading", "stat": sname, "has_2017_18": True, "what": "a live piece removed (positive diff = the live piece helps)",
                        "fit_2026": f"rows changed {100 * (np.abs(line - st.line) > 1e-9).mean():.1f}%", **{f"diff_{w}": round(W[w][0], 5) for w in WIN3}, **{f"se_{w}": round(W[w][1], 5) for w in WIN3},
                        **{f"base_{w}": round(W[w][2], 4) for w in WIN3}, "rule1": None})
            log("reading", sname, lab, {w: round(W[w][0], 4) for w in WIN3})
    return out


def together(keep):
    """The pieces passing rules 1-3, per stat, refitted together: each piece fitted walk-forward on top of the ones
    before it (in order of their 2019-25 gain); the combination must pass rules 1 and 2."""
    out = {}; by = {}
    for key, v in keep.items():
        if v["row"].get("rule3") and v["typ"] in ("L", "P", "H", "C"): by.setdefault(key[1], []).append((key, v))
    for sname, items in by.items():
        st = ST_[sname]; KF = st.K; items.sort(key=lambda kv: kv[1]["W"]["2019-22"][0] + kv[1]["W"]["2023-25"][0]); lm = np.zeros(KF.n)
        for key, v in items:
            groups = KF.pos_group if key[2] == "by position" else None; raw = raw_of(KF, v["typ"], v["col"])
            cands, _ = make_cands(st, v["typ"], raw, KF.season <= (2017 if v["has1718"] else 2025), PAIRS_.get("rec"))
            _, lm, _ = st.fit(cands, groups, base_lm=lm)
        lv = st.lf(st.line * np.exp(lm), st.act); W = st.windows(lv); has = all(v["has1718"] for _, v in items)
        row = {"family": "Together", "idea": " + ".join(f"{k[0]}[{k[2]}]" for k, _ in items), "type": "T", "variant": "together", "stat": sname, "has_2017_18": has, "what": "the passing pieces refitted together",
               "fit_2026": "", **{f"diff_{w}": round(W[w][0], 5) for w in WIN3}, **{f"se_{w}": round(W[w][1], 5) for w in WIN3}, **{f"base_{w}": round(W[w][2], 4) for w in WIN3}, "rule1": rule1(W, has)}
        k2 = {("together", sname, "together"): {"lm": lm, "row": row, "W": W}}; rule2(k2); out[sname] = row; log("together", sname, row)
    return out
def main_run():
    import pickle
    setup(); fams = sys.argv[2:] or None
    rows, keep = run_ideas(fams); log("rule 1 passes", len(keep), "of", len(rows))
    rule2(keep); log("rule 2 passes", sum(1 for v in keep.values() if v["row"].get("rule2")))
    run_placebos(keep); log("rule 3 passes", sum(1 for v in keep.values() if v["row"].get("rule3")))
    if not fams or "Task B" in fams:
        b1, k1 = task_b1(); b2, k2 = task_b2(); rows += b1 + b2; keep.update(k1); keep.update(k2)
        rows += readings_absorb()
    tog = together(keep); rows += list(tog.values())
    res = {"rows": rows, "keep": {k: {kk: vv for kk, vv in v.items() if kk not in ("lm", "line", "S")} for k, v in keep.items()}}
    tag = "_".join(f.replace(" ", "") for f in fams) if fams else "all"
    with open(CACHE / f"results_{tag}.pkl", "wb") as fh: pickle.dump(res, fh)
    pd.DataFrame(rows).to_csv(CACHE / f"results_{tag}.csv", index=False); log("DONE run", tag)


# ------------------------------------------------------------------------------------------------------------ report
def verdict(r):
    if r.get("type") == "R": return "reading"
    if not r.get("rule1"):
        bad = [w for w in WIN3 if not (r.get(f"diff_{w}", 1) < 0 or (w == "2017-18" and not r.get("has_2017_18") and r.get(f"diff_{w}", 1) <= 1e-12))]
        return "fails 1 (" + ", ".join(bad) + ")"
    if r.get("rule2") is False:
        why = [w for w in WIN3 if (r.get(f"chance_ll_diff_{w}") or 0) > 1e-12]
        lean = ""
        if r.get("lean_rule") and r.get("lean_variant"):
            a_, b_ = (int(x) for x in r["lean_rule"].split("-")); c_, d_ = (int(x) for x in r["lean_variant"].split("-"))
            if c_ - d_ < a_ - b_: lean = "lean record"
        return "fails 2 (" + ", ".join((["chance " + w for w in why]) + ([lean] if lean else [])) + ")"
    if r.get("rule3") is None: return "passes 1-2, placebo not run"
    if not r.get("rule3"): return f"fails 3 (placebo, worst window beaten in {int(round(50 * r['placebo_min_pct']))}/50)"
    return "passes 1-3"


def fmt(x, nd=4):
    return "" if x is None or (isinstance(x, float) and np.isnan(x)) else (f"{x:+.{nd}f}" if isinstance(x, (float, int, np.floating)) else str(x))


def write_report(tag="all"):
    import pickle, json
    res = pickle.load(open(CACHE / f"results_{tag}.pkl", "rb")); D = pd.DataFrame(res["rows"]); D["verdict"] = [verdict(r) for r in res["rows"]]
    cols = ["family", "idea", "type", "variant", "stat", "has_2017_18", "diff_2017-18", "diff_2019-22", "diff_2023-25", "se_2017-18", "se_2019-22", "se_2023-25", "base_2017-18", "base_2019-22", "base_2023-25",
            "chance_ll_diff_2017-18", "chance_ll_diff_2019-22", "chance_ll_diff_2023-25", "lean_rule", "lean_variant", "lean_n", "placebo_beat_2017-18", "placebo_beat_2019-22", "placebo_beat_2023-25", "placebo_min_pct",
            "rule1", "rule2", "rule3", "verdict", "fit_2026", "what"]
    for c in cols:
        if c not in D: D[c] = None
    D[cols].to_csv("reports/situational_props.csv", index=False)
    meta = json.load(open(CACHE / "pvp_meta.json"))
    L = [REPORT_HEAD]
    n_tests = int((D.type.isin(["L", "P", "H", "C"])).sum()); n1 = int(D.rule1.fillna(False).astype(bool).sum())
    L.append(f"\n## Tally\n\n{n_tests} idea x stat x variant tests (Task A and the four added families), {n1} pass rule 1 (all windows lower), "
             f"{int(D.rule2.fillna(False).astype(bool).sum())} pass rules 1-2, {int(D.rule3.fillna(False).astype(bool).sum())} pass rules 1-3. Under pure noise about one test in eight would pass rule 1 "
             f"(three windows each a coin flip), about {n_tests // 8} here: the placebo is what separates the rest.\n")
    def table(g):
        out = ["| idea | variant | stat | miss 2017-18 | 2019-22 | 2023-25 | chance LL 2018 / 19-22 / 23-25 | lean rule / variant | placebo (beaten of 50, worst window) | verdict |", "|---|---|---|---|---|---|---|---|---|---|"]
        for _, r in g.iterrows():
            ch = " / ".join(fmt(r.get(f"chance_ll_diff_{w}"), 5) for w in WIN3) if r.get("rule1") in (True,) else ""
            ln = f"{r.lean_rule} / {r.lean_variant}" if isinstance(r.lean_rule, str) else ""
            pl = f"{int(round(50 * r.placebo_min_pct))}" if r.placebo_min_pct is not None and not pd.isna(r.placebo_min_pct) else ""
            d17 = fmt(r["diff_2017-18"]) + ("" if r.has_2017_18 else " (no data)")
            out.append(f"| {r.idea} | {r.variant} | {r.stat} | {d17} | {fmt(r['diff_2019-22'])} | {fmt(r['diff_2023-25'])} | {ch} | {ln} | {pl} | {r.verdict} |")
        return out
    for fam in ["Situational", "Primetime and kickoff time", "Weather", "Injuries", "Player vs player", "Task B", "Together"]:
        g = D[D.family == fam]
        if not len(g): continue
        L.append(f"\n## {fam}\n"); L.append(FAMILY_NOTE.get(fam, "").format(**meta))
        if fam in ("Task B", "Together"):
            L += table(g)
        else:
            p1 = g[g.rule1.fillna(False).astype(bool) | g.type.eq("R")]
            L.append(f"\n{len(g)} tests; {len(p1[p1.type != 'R'])} pass rule 1. Every test that passes rule 1 (the rest, with every number, are in reports/situational_props.csv):\n")
            L += table(p1)
            # compact grid: idea x stat, best verdict code over its variants
            code = lambda v: "A" if v == "passes 1-3" else ("3" if v.startswith("fails 3") else ("2" if v.startswith("fails 2") else ("P" if v.startswith("passes 1-2") else ("r" if v == "reading" else "1"))))
            stats = [s_ for s_ in STATS if s_ in set(g.stat)]
            L.append("\nEvery idea x stat, the furthest any variant got (1 = fails the windows, 2 = fails the chance or lean record, 3 = fails its placebo, A = passes 1-3, . = not tested):\n")
            L.append("| idea | " + " | ".join(stats) + " |"); L.append("|---|" + "---|" * len(stats))
            order = "A3P21r"
            for idea, gi in g.groupby("idea", sort=False):
                cells = []
                for s_ in stats:
                    v = gi[gi.stat == s_].verdict.map(code).tolist(); cells.append(min(v, key=order.index) if v else ".")
                L.append(f"| {idea} | " + " | ".join(cells) + " |")
            # readings: the size the last refit would carry, yards stats, by position where fitted
            rd = g[g.type.eq("L") & g.stat.isin(["rec_yards", "rush_yards", "pass_yards", "rush_carries", "rec_targets"]) & ((g.variant == "by position") | (g.stat.str.startswith("pass")) | ~g.idea.isin(g[g.variant == "by position"].idea))]
            if len(rd):
                L.append("\nReadings: the size the last walk-forward refit (on 2016-2025) carries, per unit of the input for an on/off input (per standard deviation otherwise), and in the stat's units at the group's mean line over 2019-25. A size of 0 means the fit found nothing worth moving:\n")
                L.append("| idea | stat | size |"); L.append("|---|---|---|")
                for _, r in rd.iterrows(): L.append(f"| {r.idea} | {r.stat} | {r.fit_2026} |")
    L.append(CODE_NOTE)
    open("reports/situational_props.md", "w").write("\n".join(L) + "\n"); log("report written", len(D))


REPORT_HEAD = """# Situational, kickoff, weather, injury and player-vs-player ideas on the per-game props (round 3, 29 Sep 2026)

`experiments/situational_props.py` (+ `experiments/situational_props_feats.py`); every number in `reports/situational_props.csv`.
The rule is `reports/round3_rule.md`, written before any result, read for props as: (1) the miss lower on 2017-18, 2019-22
and 2023-25 (yards MAE per player-game; receptions, targets, carries and dropbacks MAE; touchdown and interception Poisson
log loss); an input that has no data before 2018 is judged on the two later windows with 2017-18 not worse; (2) the
calibrated chance on the lines (props.chance_over: the K nearest past lines of the variant's own reference table) no worse
in log loss on any window (2017-18 = 2018, the first season with a reference), at book numbers x = the rule's line + delta
(+-15 yards by 5, passing +-45 by 15, receptions +-2), and the lean record against the real book lines where the harness
has them (data/lines/props_log.csv, the consensus of each book's last pre-kickoff line: 2026 Week 3 only, about 80 to 160
decided sides per stat) not worse; (3) 50 within-season shuffles of the input, each refitted the same way, and the real gain
above the placebo's in at least 45 of 50 on every window; (4) as of before the game, no market input, no new source;
(5) the passing pieces refitted together must pass 1 and 2.

**How each idea is applied.** A multiplicative factor on the live line (after the median factor, the team reconciliation
and the injury/snap factor), exp(size x input). The size (and for a player's own history its shrinkage k) is refitted
walk-forward: every season is scored with the value that minimises the miss over all earlier seasons from 2016 (the build
keeps the 2016 player-games only as fitting rows; the harness scores from 2017), never on the season scored. Three shapes:
L, a condition or level centred on the player's own 0.85-decayed history of it (his rate already carries the conditions he
played in), pooled and, for receivers and rushers, a separate size per position group (WR / TE / RB; RB / QB); P, his own
split of a condition in log residual against the rule's line, shrunk toward the league's split (k player-games), applied to
the centred condition; H / C, his residual history at a key (stadium, opposing head coach, opponent, this week's corners)
over his own average, shrunk with k. The frames reproduce data/processed/props_reference.parquet's lines exactly (max
difference 1e-14).

**Scope limits, stated plainly.** Weather: the backtest has no archive of the kickoff forecast; the only historical weather
is the recorded kickoff reading (the schedule's wind and temperature, the play-by-play's weather text for rain and snow),
the same stand-in the game model's backtest and the props' own wind rule (WIND_C) were fitted on. Live, the Open-Meteo
kickoff forecast takes its place, which is noisier, so any weather gain here is an upper bound. Kickers and QB sacks are not
scored by this harness (kickers live in props_backtest9), so the FG / kicker props and the sack side of pass rush vs
protection are not tested. Injuries: only this week's final report (Out / Doubtful) and the weekly roster's active flag,
never game-day actives. The defensive play-caller is not in any pulled data (the schedule names head coaches only).
"""

FAMILY_NOTE = {
    "Situational": "Surface, roof, home, division, rest, travel (the static stadium table), time zones, altitude, former team; his own turf / indoor / home / division splits; his history at the stadium, against the opposing head coach and against the opponent.",
    "Primetime and kickoff time": "Slots (Sunday 1 PM, 4 PM, night), days (Thursday, Saturday, Sunday, Monday), SNF / MNF / TNF each alone, the body clock (a Pacific or Mountain team at 1 PM ET; an Eastern team at a Pacific venue at 8 PM ET or later; the kickoff hour on the team's home clock), holidays and international venues; his own primetime and night splits. The Thursday short-week shift by position is the TNF and short-week rows by position group (carries for RB vs QB, targets for WR / TE / RB).",
    "Weather": "Wind above 10 mph (for passing on top of the live WIND_C), rain, snow, cold, any bad weather, a warm or dome team in the cold, bad weather x turf, x grass, x night, wind x turf; his own bad-weather split. Weather x roof is degenerate here (indoor games carry no weather), so it is the turf / grass and indoor rows. Every weather input is 0 indoors.",
    "Injuries": "The live injury pieces re-checked alone (readings: the rule without ABSORB, and without the own-report factor; a positive difference means the live piece helps), then: known-out starters at his own group (on top of ABSORB) and at the other groups (WR1 out -> TE / RB targets), RB starters out (RB2 carries and receptions), the backup QB (the usual starter listed out; this week's starter's rating against his history; each receiver's own backup-QB split), OL starters out (pass yards, dropbacks, rushing), offensive starters out, the opponent's expected starters known out by position (CB -> WR, LB -> TE / RB, DL -> rushing), and injuries x bad weather, x short week.",
    "Player vs player": ("**What the free data can say about who covers whom.** Nothing assigns a defender to a receiver: nflverse's play-by-play "
        "has no coverage assignment; the participation file lists the 11 defenders on the field, the man / zone call "
        "(defense_man_zone_type, 2018 on) and the coverage shell (defense_coverage_type), with the route only for the targeted "
        "receiver and no alignment for anyone (no wide / slot for corners or receivers), and it is published after a season, "
        "so it can enter only later seasons; FTN charting (2022 on, weekly) has box counts, blitzers and catchable / contested "
        "flags but no coverage or alignment; the play-by-play credits a pass defensed, an interception or a tackle, which is "
        "the defender near the ball at the end, not the one in coverage. The depth charts name starting corners (LCB / RCB / NB "
        "in the 2025-26 format) without saying who they follow. So every proxy here is indirect: this week's expected "
        "corners (the top three by snap share over the team's last three games, less the known-out) rated by the positions.py "
        "corner recipe (PFR coverage, 2018 on); a receiver's history against a specific corner counting only his targets with "
        "that corner on the field (earlier seasons; {pairs} receiver x defender x game rows); a shadow index from the credits "
        "(a corner's credits on the offense's WR1 targets above the WR1's share of WR targets, shrunk: it flags only "
        "{shadow_flag_share:.1%} of expected-corner rows, {shadow_rows_wr1} WR1 rows in all, and its season-to-season "
        "correlation is {shadow_persist:.2f}, so a credits-based shadow reading is mostly noise); the receiver's and the QB's "
        "man / zone split from earlier seasons x the opponent's man rate last season; LBs and safeties against TE / RB "
        "receiving; the front (IDL, LB, EDGE) and last season's 8+ box rate against rushing; the pass rush (EDGE, IDL) and "
        "his line's sacks and hits allowed against passing. The play-caller's coverage mix is the defense's man rate."),
}

CODE_NOTE = """
## Code change for anything that passed

Only an idea marked **passes 1-3** in a table above (and whose "together" row passes 1 and 2) is a candidate; the change is
described here, not applied (nflmodel/ is not touched by this study). See the summary for which, if any.
"""


if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "run":
    main_run(); write_report("_".join(f.replace(" ", "") for f in sys.argv[2:]) if sys.argv[2:] else "all"); sys.exit(0)
if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "report":
    write_report(sys.argv[2] if len(sys.argv) > 2 else "all"); sys.exit(0)
if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] in ("build", "features"):
    build_frames() if sys.argv[1] == "build" else build_features(); log("DONE", sys.argv[1]); sys.exit(0)
