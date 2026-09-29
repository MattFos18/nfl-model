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
BOOK_OF = {"rec_yards": "rec_yards", "rec_catches": "rec_catches", "rec_targets": "rec_targets", "rush_yards": "rush_yards", "rush_carries": "rush_attempts", "pass_yards": "pass_yards"}
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
    def fit(self, cands, groups=None, labels=None):
        """cands: list of (param magnitude, fn -> log multiplier array). Walk-forward per season (and group): the candidate
        with the least loss over every earlier season from 2016; the zero candidate for 2016 itself. Returns the variant's
        per-row loss, log multiplier, and the choice per season."""
        n = self.K.n; groups = np.zeros(n, dtype=int) if groups is None else groups; ng = int(groups.max()) + 1; ns = len(SEASONS)
        si = self.season_idx(); J = len(cands); E = np.zeros((ns, ng, J)); mags = np.array([c[0] for c in cands], float)
        comb = si * ng + groups
        for j, (_, fn) in enumerate(cands):
            lm = fn(); E[:, :, j] = np.bincount(comb, weights=self.lf(self.line * np.exp(lm), self.act), minlength=ns * ng).reshape(ns, ng)
        zero = int(np.argmin(np.abs(mags))); choice = np.full((ns, ng), zero)
        for s_ in range(1, ns):
            cum = E[:s_].sum(0) + 1e-6 * np.abs(mags)[None, :]
            choice[s_] = np.argmin(cum, axis=1)
        lm = np.zeros(n); cache = {}
        for (s_, g_) in {(a, b) for a, b in zip(si, groups)}:
            j = choice[s_, g_]; m = (si == s_) & (groups == g_)
            if j not in cache: cache[j] = cands[j][1]()
            lm[m] = cache[j][m]
        return self.lf(self.line * np.exp(lm), self.act), lm, choice

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
    return [(a, (lambda a=a: np.clip(a / sd * zc, -0.7, 0.7))) for a in A_GRID], sd


def cands_S(svals):
    """svals: {k: s_k array}; candidates c x s_k."""
    out = [(0.0, lambda: np.zeros(len(next(iter(svals.values())))))]
    for k, sk in svals.items():
        for c in C_GRID:
            if c == 0: continue
            out.append((abs(c) + 1e-3 * k, (lambda c=c, sk=sk: np.clip(c * sk, -0.7, 0.7))))
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
        x["st_"] = pd.to_datetime(x.start, utc=True, errors="coerce"); x = x[x.ts_ < x.st_]; x["key"] = x.player.map(norm_name)
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
        our = L[q.i.values]; bk = q.line.values; a = st.act[q.i.values]; side = np.sign(our - bk); dec = (side != 0) & (a != bk)
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
    """Player vs player: the man/zone split (receivers and QBs), the shadow index and the corner pair histories' inputs."""
    import experiments.situational_props_feats as SF
    P = pd.read_parquet(OUT / "scheme_plays.parquet", columns=["game_id", "season", "week", "posteam", "defteam", "pass_play", "dropback", "receiver_player_id", "passer_player_id", "yards_gained", "pass_yds", "man", "cov_known"])
    P = P[P.cov_known.fillna(False).astype(bool) & P.pass_play.fillna(False).astype(bool)].copy(); P["m"] = P.man.fillna(0).astype(float); P["z"] = 1 - P.m
    for kind, idc, yc, kk in (("rec", "receiver_player_id", "yards_gained", 30.0), ("pass", "passer_player_id", "pass_yds", 100.0)):
        t = P[P[idc].notna()].rename(columns={idc: "pid"}).copy(); t["y"] = t[yc].fillna(0.0)
        pg = t.assign(ym=t.y * t.m, yz=t.y * t.z).groupby(["pid", "season", "week"]).agg(nm=("m", "sum"), nz=("z", "sum"), ym=("ym", "sum"), yz=("yz", "sum")).reset_index().sort_values(["pid", "season", "week"])
        cs = pg.groupby("pid")[["nm", "nz", "ym", "yz"]].cumsum(); pg[["cnm", "cnz", "cym", "cyz"]] = cs.values; pg["key"] = _key(pg.season, pg.week)
        lgm = t.groupby("season").apply(lambda x: (x.y * x.m).sum() / x.m.sum()); lgz = t.groupby("season").apply(lambda x: (x.y * x.z).sum() / x.z.sum())
        f = pd.read_parquet(CACHE / f"frame_{kind}.parquet", columns=["pid", "season", "week"]).reset_index(drop=True); f["i"] = np.arange(len(f)); f["key"] = _key(f.season, f.week)
        m = pd.merge_asof(f.sort_values("key"), pg[["pid", "key", "cnm", "cnz", "cym", "cyz"]].sort_values("key"), on="key", by="pid", direction="backward", allow_exact_matches=False).sort_values("i")
        lm_ = f.season.map(lambda s: lgm.get(s - 1, np.nan)).values; lz_ = f.season.map(lambda s: lgz.get(s - 1, np.nan)).values
        ypm = (m.cym.fillna(0).values + kk * lm_) / (m.cnm.fillna(0).values + kk); ypz = (m.cyz.fillna(0).values + kk * lz_) / (m.cnz.fillna(0).values + kk)
        s_mz = np.log(ypm / ypz) - np.log(lm_ / lz_)
        X = pd.read_parquet(CACHE / f"X_{kind}.parquet"); lgman = X.groupby("season").opp_man.transform("mean")
        X["mz_split"] = s_mz; X["mz_x_man"] = np.nan_to_num(s_mz) * np.nan_to_num(X.opp_man - lgman)
        X["mz_n"] = (m.cnm.fillna(0) + m.cnz.fillna(0)).values; X.to_parquet(CACHE / f"X_{kind}.parquet"); log("man/zone", kind)
    # ---- shadow index and pair histories (receivers) ----
    pl = SF.pass_plays_with_defenders(); log("targeted plays with defenders", len(pl))
    fr = pd.read_parquet(CACHE / "frame_rec.parquet", columns=["pid", "posteam", "defteam", "season", "week", "game_id", "pos", "vol"])
    fr["tplays"] = fr.vol   # the as-of expected targets rank the team's receivers
    wr = fr[fr.pos.eq("WR")].sort_values("vol", ascending=False).drop_duplicates(["game_id", "posteam"])[["game_id", "posteam", "pid"]].rename(columns={"pid": "wr1"})
    pl = pl.merge(wr, on=["game_id", "posteam"], how="left")
    wrs = set(fr[fr.pos.eq("WR")].pid)
    pl = pl[pl.receiver_player_id.isin(wrs)].copy(); pl["is1"] = (pl.receiver_player_id == pl.wr1).astype(float)
    cred_cols = ["solo_tackle_1_player_id", "solo_tackle_2_player_id", "assist_tackle_1_player_id", "assist_tackle_2_player_id", "pass_defense_1_player_id", "pass_defense_2_player_id", "interception_player_id"]
    cr = pd.concat([pl[["game_id", "season", "week", "defteam", "is1", c]].rename(columns={c: "cb"}) for c in cred_cols]).dropna(subset=["cb"])
    share1 = pl.groupby(["game_id", "posteam"]).is1.mean().rename("s1").reset_index()
    cr = cr.merge(pl[["game_id", "defteam", "posteam"]].drop_duplicates(), on=["game_id", "defteam"]).merge(share1, on=["game_id", "posteam"])
    cg = cr.groupby(["cb", "season", "week", "game_id"]).agg(c1=("is1", "sum"), cw=("is1", "size"), e=("s1", "sum")).reset_index().sort_values(["cb", "season", "week"])
    cs = cg.groupby("cb")[["c1", "cw", "e"]].cumsum(); cg[["C1", "CW", "E"]] = cs.values; cg["key"] = _key(cg.season, cg.week); cg["shadow"] = (cg.C1 - cg.E) / (cg.CW + 10.0)
    cg.to_parquet(CACHE / "shadow_states.parquet")
    # persistence: the index over one season against the next (corners with 20+ credits on WR targets in both)
    per = cr.groupby(["cb", "season"]).agg(c1=("is1", "sum"), cw=("is1", "size"), e=("s1", "sum")).reset_index(); per = per[per.cw >= 20]; per["ix"] = (per.c1 - per.e) / per.cw
    nx = per.merge(per.assign(season=per.season - 1), on=["cb", "season"], suffixes=("", "_next"))
    shadow_persist = float(np.corrcoef(nx.ix, nx.ix_next)[0, 1]) if len(nx) > 20 else np.nan
    # the rows: WR1 against a shadow corner gets the corner's own rating, the other WRs the rest of the unit
    ed = ED[["game_id", "defteam", "cb_list", "CB_r"]].copy(); ed["key"] = _key(ED.season, ED.week)
    X = pd.read_parquet(CACHE / "X_rec.parquet"); fr = fr.reset_index(drop=True); fr["i"] = np.arange(len(fr)); fr = fr.merge(wr, on=["game_id", "posteam"], how="left").sort_values("i")
    st_last = cg[["cb", "key", "shadow", "CW"]].sort_values("key")
    rows = ed.explode("cb_list").dropna(subset=["cb_list"]); rows["cb"] = rows.cb_list.map(lambda t: t[0]); rows["sh"] = rows.cb_list.map(lambda t: t[1]); rows["rt"] = rows.cb_list.map(lambda t: t[2])
    rows = pd.merge_asof(rows.sort_values("key"), st_last, on="key", by="cb", direction="backward", allow_exact_matches=False)
    rows["is_shadow"] = (rows.shadow >= 0.15) & (rows.CW >= 20)
    top = rows.dropna(subset=["rt"]).sort_values("rt", ascending=False).drop_duplicates(["game_id", "defteam"])
    top = top[top.is_shadow][["game_id", "defteam", "cb", "rt"]].rename(columns={"cb": "shadow_cb", "rt": "shadow_rt"})
    rest = rows.dropna(subset=["rt"]).merge(top[["game_id", "defteam", "shadow_cb"]], on=["game_id", "defteam"], how="inner"); rest = rest[rest.cb != rest.shadow_cb]
    rest = rest.assign(w=rest.sh * rest.rt).groupby(["game_id", "defteam"]).agg(w=("w", "sum"), s=("sh", "sum")).reset_index(); rest["rest_rt"] = rest.w / rest.s
    q = fr[["i", "game_id", "defteam", "pid", "pos", "wr1"]].merge(top, on=["game_id", "defteam"], how="left").merge(rest[["game_id", "defteam", "rest_rt"]], on=["game_id", "defteam"], how="left").sort_values("i")
    unit = X.opp_cb_r.values; isw = q.pos.eq("WR").values; sh = q.shadow_cb.notna().values; one = (q.pid == q.wr1).values
    X["cb_shadow_assign"] = np.where(~isw, np.nan, np.where(sh & one, q.shadow_rt.values, np.where(sh, q.rest_rt.fillna(pd.Series(unit)).values, unit)))
    X["cb_unit_wr"] = np.where(isw, unit, np.nan)
    X["vs_shadow_wr1"] = (isw & sh & one).astype(float)
    X.to_parquet(CACHE / "X_rec.parquet")
    # pair table: receiver x defender on the field on his targets, per game (share of his targets with that defender on)
    pl2 = SF.pass_plays_with_defenders(); pl2 = pl2[pl2.defense_players.notna()].copy(); pl2["dp"] = pl2.defense_players.str.split(";")
    ex = pl2[["game_id", "season", "week", "receiver_player_id", "dp"]].explode("dp").rename(columns={"receiver_player_id": "pid", "dp": "cb"})
    cbset = set(k for k, v in __import__("nflmodel.positions", fromlist=["x"]).__dict__.get("_dummy", {}).items()) if False else None
    tt = pl2.groupby(["pid" if "pid" in pl2 else "receiver_player_id", "game_id"]).size().rename("tg").reset_index().rename(columns={"receiver_player_id": "pid"})
    pr = ex.groupby(["pid", "cb", "game_id", "season", "week"]).size().rename("on").reset_index().merge(tt, on=["pid", "game_id"]); pr["v"] = pr.on / pr.tg
    pr.to_parquet(CACHE / "pairs.parquet")
    meta = {"shadow_persist": shadow_persist, "shadow_flag_share": float(rows.is_shadow.mean()), "shadow_rows_wr1": int((isw & sh & one).sum()), "cb_rows": int(len(rows)), "pairs": int(len(pr))}
    pd.Series(meta).to_json(CACHE / "pvp_meta.json"); log("pvp meta", meta)


if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] in ("build", "features"):
    build_frames() if sys.argv[1] == "build" else build_features(); log("DONE", sys.argv[1]); sys.exit(0)
