"""Injuries re-tested (1 Oct 2026): Questionable players at the chance they sit, and the linemen's and defenders' value
out on the fixed ids and values.

Matt asked for better injury accuracy: Questionable players, offensive linemen, and any other player who raises a flag.
What was tried before: Questionable at guessed weights 0.3 / 0.5 in the skill value out (experiments/questionable.py,
23 Sep: worse held out); the linemen's on/off value out and the defenders' value out (experiments/positions.py, 22 Sep,
linemen matched by name; experiments/def_value_out.py, 24 Sep, an interim defender value). Since then the linemen got
one id map (nflmodel/ids.py) and a unit rating (ol_games), and the defenders a recipe per group (positions.role_rates).

Variants, pre-registered in reports/injury_retest.md before the results, each refit walk-forward 2015-2025:
  Q1  a Questionable RB / WR / TE (not Out, Doubtful or off the roster) counts as out times the chance he sits: the
      share of Questionable players who then took no snap, by position group and the week's last practice status
      (DNP / limited / full / none), from seasons before the one priced (2013 on), each cell shrunk to its practice
      status's rate with 20 listings. Applied to skill_out_value (own and opponent) and off_snap_out.
  Q2  Q1 at every position: off_snap_out and the opponent's def_snap_out take every Questionable player's last-game
      snap share times his chance to sit, and qb_out becomes that chance when last game's starting QB is Questionable.
  L1  own and opponent offensive linemen's value out (ol_games unit rating, PlayerValues as on the page, by id), added.
  D1  opponent defenders' value out (positions.role_rates, each group's recipe against its replacement), added. Own is
      the same column seen from the other team's row, so it is not a separate input.
  C   the variants that pass parts 1 and 2 of the gate, together (or, when none pass, the best two by summed gain).
The OL unit rating and the defender recipes read PFR charting (2018 on), so L1 and D1 are zero before 2018 and the
2015-18 window changes only through 2018.
Scored through nflmodel.study_gate: team points miss on 2015-18 / 2019-22 / 2023-25 with the live spread flag (edge 4)
and totals flag (55% under) records for the no-bet-cost part. --placebo V runs 50 within-season shuffles of variant V's
new values (about two hours). Writes reports/injury_retest.{md,csv}.

    python -m experiments.injury_retest [--placebo Q1]
"""
from __future__ import annotations
import sys
import numpy as np, pandas as pd
from nflmodel import backtest as B, model as M, picks as P, study_gate as G, players as PL, positions as PS
from nflmodel.features import OUT, ROOT, RAW, TEAM_FIX
from nflmodel.ids import map_pfr

REP = ROOT / "reports"
WIN = {"2015-18": (2015, 2018), "2019-22": (2019, 2022), "2023-25": (2023, 2025)}
GAMES = pd.read_parquet(OUT / "games.parquet")
SEASONS = range(2013, 2026)
CACHE = OUT / "injury_retest_inputs.parquet"   # scratch, not committed
GROUP = {"QB": "QB", "RB": "RB", "FB": "RB", "HB": "RB", "WR": "WR", "TE": "TE", "T": "OL", "G": "OL", "C": "OL", "OT": "OL", "OG": "OL", "OL": "OL",
         "DE": "DL", "DT": "DL", "NT": "DL", "DL": "DL", "LB": "LB", "ILB": "LB", "OLB": "LB", "MLB": "LB", "CB": "DB", "S": "DB", "SS": "DB", "FS": "DB", "DB": "DB",
         "K": "ST", "P": "ST", "LS": "ST"}
SKILL_G = {"RB", "WR", "TE"}
SHRINK = 20.0


def practice(s) -> str:
    s = str(s) if isinstance(s, str) else ""
    return "dnp" if s.startswith("Did Not") else "limited" if s.startswith("Limited") else "full" if s.startswith("Full") else "none"


def load_snaps() -> pd.DataFrame:
    sn = pd.concat([pd.read_parquet(RAW / "snap_counts" / f"snap_counts_{s}.parquet") for s in SEASONS if (RAW / "snap_counts" / f"snap_counts_{s}.parquet").exists()], ignore_index=True)
    sn["team"] = sn.team.replace(TEAM_FIX); sn["key"] = map_pfr(sn)
    return sn


def sit_rates(inj: pd.DataFrame, sn: pd.DataFrame, out_by: dict) -> tuple[pd.DataFrame, dict]:
    """Every Questionable listing (regular season, team-week with snap counts, not otherwise out): did he take a snap?
    Returns the listings and {season: {(group, practice): chance he sits}} from earlier seasons only."""
    tw = set(zip(sn.season, sn.week, sn.team)); played = set(zip(sn.season, sn.week, sn.team, sn.key))
    q = inj[(inj.report_status == "Questionable") & (inj.game_type == "REG")].dropna(subset=["gsis_id"]).copy()
    q["season"] = q.season.astype(int); q["week"] = q.week.astype(int)
    q = q[[(s, w, t) in tw for s, w, t in zip(q.season, q.week, q.team)]]
    q = q[[g not in out_by.get((s, w, t), set()) for s, w, t, g in zip(q.season, q.week, q.team, q.gsis_id)]]
    q["group"] = q.position.map(GROUP).fillna("other"); q["prac"] = q.practice_status.map(practice)
    q["sat"] = [float((s, w, t, g) not in played) for s, w, t, g in zip(q.season, q.week, q.team, q.gsis_id)]
    q = q.drop_duplicates(["season", "week", "team", "gsis_id"])
    rates = {}
    for s in range(2014, 2026):
        h = q[q.season < s]
        pr = h.groupby("prac").sat.agg(["sum", "count"]); base = (pr["sum"] / pr["count"]).to_dict(); allr = float(h.sat.mean())
        c = h.groupby(["group", "prac"]).sat.agg(["sum", "count"])
        rates[s] = {k: float((r["sum"] + SHRINK * base.get(k[1], allr)) / (r["count"] + SHRINK)) for k, r in c.iterrows()}
        rates[s]["_prac"] = base; rates[s]["_all"] = allr
    return q, rates


def chance(rates: dict, season: int, group: str, prac: str) -> float:
    r = rates[season]
    return r.get((group, prac), r["_prac"].get(prac, r["_all"]))


def build() -> pd.DataFrame:
    if CACHE.exists():
        return pd.read_parquet(CACHE)
    inj = PL.load_injuries(SEASONS); inj = inj[inj.game_type == "REG"].copy()
    inj["season"] = inj.season.astype(int); inj["week"] = inj.week.astype(int)
    od = inj[inj.report_status.isin(["Out", "Doubtful"])]
    out_by = {k: set(g.gsis_id.dropna()) for k, g in od.groupby(["season", "week", "team"])}
    skill_out = {k: set(g.gsis_id.dropna()) for k, g in od[od.position != "QB"].groupby(["season", "week", "team"])}   # players.injury_value's set
    for k, ids in PL.unavailable_by_week(SEASONS).items():
        out_by[k] = out_by.get(k, set()) | ids; skill_out[k] = skill_out.get(k, set()) | ids
    sn = load_snaps()
    q, rates = sit_rates(inj, sn, out_by)
    q.to_csv(REP / "injury_retest_listings.csv", index=False) if "--listings" in sys.argv else None
    q_by = {k: g for k, g in q.groupby(["season", "week", "team"])}
    # skill value (players.injury_value's own objects)
    pg = pd.read_parquet(OUT / "player_games.parquet"); p = PL.DEFAULT
    pv = PL.PlayerValues(pg, p["decay"], p["k"], p.get("pct", 25)); _, by_player, by_team = PL._usage_frames(pg)
    # linemen (positions.all_values's objects)
    og = pd.read_parquet(OUT / "ol_games.parquet"); pv_ol = PL.PlayerValues(og, PS.DEF_DECAY, 300.0, PS.REPL_PCT, season_fade=PS.DEF_FADE)
    ol_by = {pid: g.sort_values(["season", "week"]) for pid, g in og.groupby("player_id")}
    team_off = sn.groupby(["game_id", "team"]).offense_snaps.max(); team_def = sn.groupby(["game_id", "team"]).defense_snaps.max()
    # defenders
    dg = pd.read_parquet(OUT / "defender_games.parquet"); roles = PS.defender_roles(dg)
    def_by = {pid: g.sort_values(["season", "week"]) for pid, g in dg.groupby("player_id")}
    prev = {k: g.sort_values("week") for k, g in sn.groupby(["season", "team"])}
    long = pd.concat([GAMES[["game_id", "season", "week", "home_team"]].rename(columns={"home_team": "team"}), GAMES[["game_id", "season", "week", "away_team"]].rename(columns={"away_team": "team"})])
    long = long[long.season.isin(SEASONS) & long.game_id.map(GAMES.set_index("game_id").game_type).eq("REG")].sort_values(["season", "week"])
    rr_cache = {}
    def last8(g, s, w):
        h = g[(g.season < s) | ((g.season == s) & (g.week < w))]
        return h[h.game_id.isin(h.game_id.drop_duplicates().tail(8))]
    rows = []
    for r in long.itertuples():
        s, w, t = int(r.season), int(r.week), r.team
        outs = out_by.get((s, w, t), set())
        # last game's snaps (trends.injury_table's rule)
        g = prev.get((s, t)); before = pd.DataFrame(columns=sn.columns)
        if g is not None:
            b = g[g.week < w]
            if len(b): before = b[b.week == b.week.max()]
            else:
                g2 = prev.get((s - 1, t)); before = g2[g2.week == g2.week.max()] if g2 is not None else before
        bo = dict(zip(before.key, before.offense_pct.clip(0, 1))); bd = dict(zip(before.key, before.defense_pct.clip(0, 1)))
        qb_start = set(before[(before.position == "QB") & (before.offense_pct >= 0.5)].key)
        base_off = sum(bo.get(k, 0.0) for k in outs if k in bo)
        base_skill = sum(PL.player_value_out(pv, by_player, pid, s, w, p["usage_games"], t, by_team)["value"] for pid in skill_out.get((s, w, t), set()))
        row = {"game_id": r.game_id, "team": t, "season": s, "base_off": base_off, "base_skill": base_skill,
               "q1_skill": 0.0, "q1_off": 0.0, "q2_off": 0.0, "q2_def": 0.0, "q2_qb": 0.0, "n_q": 0, "ol_value_out": 0.0, "def_value_out": 0.0}
        if s >= 2014 and (s, w, t) in q_by and s in rates:
            for x in q_by[(s, w, t)].itertuples():
                c = chance(rates, s, x.group, x.prac); row["n_q"] += 1
                if x.group in SKILL_G:
                    if x.gsis_id in by_player:
                        row["q1_skill"] += c * PL.player_value_out(pv, by_player, x.gsis_id, s, w, p["usage_games"], t, by_team)["value"]
                    row["q1_off"] += c * bo.get(x.gsis_id, 0.0)
                row["q2_off"] += c * bo.get(x.gsis_id, 0.0); row["q2_def"] += c * bd.get(x.gsis_id, 0.0)
                if x.gsis_id in qb_start:
                    row["q2_qb"] = max(row["q2_qb"], c)
        if s >= 2018 and outs:
            for pid in outs:
                go = ol_by.get(pid)
                if go is not None:
                    rec = last8(go, s, w)
                    if len(rec):
                        v, _ = pv_ol.value(pid, "OL", s, w); pr = pv_ol.prior("OL", s)
                        tsn = team_off.reindex(list(zip(rec.game_id, rec.team))).mean()
                        sh = float(rec.plays.mean() / tsn) if tsn and not np.isnan(tsn) else 0.0
                        row["ol_value_out"] += (v - pr) * min(sh, 1.0)
                gd = def_by.get(pid)
                if gd is not None:
                    rec = last8(gd, s, w)
                    if len(rec):
                        if (s, w) not in rr_cache:
                            rr_cache[(s, w)] = PS.role_rates(dg, roles, s, w)
                        rate, repl = rr_cache[(s, w)]; role = roles.get(pid)
                        if pid in rate and role in repl:
                            tsn = team_def.reindex(list(zip(rec.game_id, rec.team))).mean()
                            sh = float(rec.plays.mean() / tsn) if tsn and not np.isnan(tsn) else 0.0
                            row["def_value_out"] += (rate[pid] - repl[role]) * min(sh, 1.0)
        rows.append(row)
        if len(rows) % 1000 == 0:
            print(len(rows), flush=True)
    X = pd.DataFrame(rows); X.to_parquet(CACHE, index=False)
    # the sit table for the report: 2016-2025 listings, and the rates as of 2026's pricing would be
    q.groupby(["group", "prac"]).agg(listings=("sat", "size"), sat=("sat", "mean")).reset_index().to_csv(REP / "injury_retest_sit.csv", index=False)
    return X


NEW = {"Q1": [], "Q2": [], "L1": ["ol_value_out", "opp_ol_value_out"], "D1": ["opp_def_value_out"]}
SHUF = {"Q1": ["q1_skill", "q1_off"], "Q2": ["q1_skill", "q2_off", "q2_def", "q2_qb"], "L1": ["ol_value_out"], "D1": ["def_value_out"]}


def variant(f0: pd.DataFrame, X: pd.DataFrame, parts: list[str]) -> tuple[pd.DataFrame, list[str]]:
    f = f0.copy(); x = X.set_index(["game_id", "team"])
    own = pd.MultiIndex.from_arrays([f.game_id, f.team]); opp = pd.MultiIndex.from_arrays([f.game_id, f.opp])
    get = lambda c, ix: x[c].reindex(ix).fillna(0.0).values
    feats = list(M.FEATS)
    if "Q2" in parts:
        f["skill_out_value"] += get("q1_skill", own); f["opp_skill_out_value"] += get("q1_skill", opp)
        f["off_snap_out"] += get("q2_off", own); f["opp_def_snap_out"] += get("q2_def", opp)
        f["qb_out"] = np.maximum(f.qb_out.values, get("q2_qb", own))
    elif "Q1" in parts:
        f["skill_out_value"] += get("q1_skill", own); f["opp_skill_out_value"] += get("q1_skill", opp)
        f["off_snap_out"] += get("q1_off", own)
    if "L1" in parts:
        f["ol_value_out"] = get("ol_value_out", own); f["opp_ol_value_out"] = get("ol_value_out", opp); feats += NEW["L1"]
    if "D1" in parts:
        f["opp_def_value_out"] = get("def_value_out", opp); feats += NEW["D1"]
    return f, feats


def score(pred: pd.DataFrame) -> dict:
    d = B.join(pred, GAMES); d = d[(d.game_type == "REG") & d.season.between(2015, 2025)]
    out = {}
    for w, (lo, hi) in WIN.items():
        x = d[d.season.between(lo, hi)]
        tp = float(np.r_[x.home_err.abs(), x.away_err.abs()].mean())
        sp = P.record(x, P.rule_mask(x, P.SPREAD_EDGE)); tf = P.record(x, P.rule_mask(x, P.TOTAL_SHADOW["prob"], "under_prob"), "under_prob")
        out[w] = {"team": tp, "total": float(x.total_err.abs().mean()), "margin": float(x.margin_err.abs().mean()), "spread": sp, "totals": tf}
    return out


def run(f0, X, parts):
    keep = M.FEATS
    f, feats = variant(f0, X, parts) if parts else (f0, list(M.FEATS))
    M.FEATS = feats
    try:
        return score(M.walk_forward(f, range(2015, 2026), 10.0))
    finally:
        M.FEATS = keep


def gate_rows(base, sc, placebo=None):
    return G.gate({w: (base[w]["team"], sc[w]["team"]) for w in WIN},
                  {w: {"spread flag": (base[w]["spread"], sc[w]["spread"]), "totals flag": (base[w]["totals"], sc[w]["totals"])} for w in WIN},
                  placebo)


def p12(rows) -> bool:
    return all(ok for what, ok, _ in rows if not what.startswith("beats"))


def shuffled(X: pd.DataFrame, cols: list[str], rng) -> pd.DataFrame:
    X = X.copy(); seas = X.season.values
    perm = np.empty(len(X), dtype=int)
    for s in np.unique(seas):   # one permutation per season for all of the variant's columns, so a team-game's parts move together
        i = np.flatnonzero(seas == s); perm[i] = i[rng.permutation(len(i))]
    for c in cols:
        X[c] = X[c].values[perm]
    return X


def main():
    f0 = M.with_trends(pd.read_parquet(OUT / "features_asof.parquet")); X = build()
    if "--placebo" in sys.argv:
        v = sys.argv[sys.argv.index("--placebo") + 1]; parts = v.split("+"); rng = np.random.default_rng(11)
        base = run(f0, X, []); real = run(f0, X, parts); gains = {w: [] for w in WIN}
        cols = sorted({c for p_ in parts for c in SHUF[p_]})
        for i in range(50):
            sc = run(f0, shuffled(X, cols, rng), parts)
            for w in WIN:
                gains[w].append(base[w]["team"] - sc[w]["team"])
            print(f"placebo {i + 1}/50", {w: round(gains[w][-1], 4) for w in WIN}, flush=True)
        rows = gate_rows(base, real, gains)
        pd.DataFrame(gains).to_csv(REP / f"injury_retest_placebo_{v.replace('+', '_')}.csv", index=False)
        md = REP / "injury_retest.md"
        md.write_text(md.read_text(encoding="utf-8") + f"\n## Placebo, variant {v} (50 within-season shuffles)\n\n" + G.markdown(rows) + "\n", encoding="utf-8")
        print(G.markdown(rows)); return
    # checks that the rebuilt base reproduces the live inputs
    pi = pd.read_parquet(OUT / "player_injury.parquet").merge(X, on=["game_id", "team"])
    tr = pd.read_parquet(OUT / "trends_asof.parquet").merge(X, on=["game_id", "team"])
    chk = {"skill value out, rebuilt vs live: share within 0.001": float(((pi.skill_out_value - pi.base_skill).abs() < 1e-3).mean()),
           "offensive snaps out, rebuilt vs live: share within 0.01": float(((tr.off_snap_out - tr.base_off).abs() < 1e-2).mean())}
    print(chk)
    res = {"base": run(f0, X, [])}
    for v in ("Q1", "Q2", "L1", "D1"):
        res[v] = run(f0, X, [v]); print(v, {w: round(res[v][w]["team"], 4) for w in WIN}, flush=True)
    gates = {v: gate_rows(res["base"], res[v]) for v in ("Q1", "Q2", "L1", "D1")}
    ok = [v for v in ("Q1", "Q2", "L1", "D1") if p12(gates[v])]
    if "Q1" in ok and "Q2" in ok:
        ok.remove("Q1" if sum(res["Q1"][w]["team"] for w in WIN) > sum(res["Q2"][w]["team"] for w in WIN) else "Q2")
    if len(ok) >= 2:
        cparts = ok; why = "the variants that pass parts 1 and 2"
    else:
        gain = {v: sum(res["base"][w]["team"] - res[v][w]["team"] for w in WIN) for v in ("Q2", "L1", "D1")}
        gain["Q1"] = sum(res["base"][w]["team"] - res["Q1"][w]["team"] for w in WIN)
        best = sorted(gain, key=gain.get, reverse=True)
        cparts = [best[0]] + [b for b in best[1:] if not ({"Q1", "Q2"} <= {best[0], b})][:1]
        why = "fewer than two pass parts 1 and 2: the best two by summed gain"
    cname = "C (" + "+".join(cparts) + ")"
    res[cname] = run(f0, X, cparts); gates[cname] = gate_rows(res["base"], res[cname])
    rows = []
    for v, sc in res.items():
        for w in WIN:
            rows.append({"variant": v, "window": w, "team_miss": round(sc[w]["team"], 4), "total_miss": round(sc[w]["total"], 4),
                         "margin_miss": round(sc[w]["margin"], 4), "spread_flag": "%d-%d" % sc[w]["spread"], "totals_flag": "%d-%d" % sc[w]["totals"]})
    pd.DataFrame(rows).to_csv(REP / "injury_retest.csv", index=False)
    sit = pd.read_csv(REP / "injury_retest_sit.csv")
    cov = X.groupby("season").agg(q_listed=("n_q", "sum"), q1_rows=("q1_skill", lambda s_: int((s_ != 0).sum())), ol_rows=("ol_value_out", lambda s_: int((s_ != 0).sum())), def_rows=("def_value_out", lambda s_: int((s_ != 0).sum())))
    md = REP / "injury_retest.md"; head = md.read_text(encoding="utf-8").split("\n## Results")[0] if md.exists() else "# Injuries re-tested\n"
    L = [head.rstrip(), "", "## Results", "", "Rebuilt inputs against the live ones: " + "; ".join(f"{k} {v:.2%}" for k, v in chk.items()) + ".", "",
         "Chance a Questionable player sat (took no snap), 2013-2025 listings not otherwise out, by group and last practice:", "",
         "| Group | Practice | Listings | Sat |", "|---|---|---|---|"]
    L += [f"| {r.group} | {r.prac} | {r.listings} | {r.sat:.0%} |" for r in sit.itertuples() if r.listings >= 30]
    L += ["", "Team-games with a non-zero input, by season (Questionable players listed; Q1 skill value; linemen out; defenders out):", "",
          "| Season | Questionable listed | Q1 skill rows | Linemen rows | Defender rows |", "|---|---|---|---|---|"]
    L += [f"| {s} | {int(r.q_listed)} | {int(r.q1_rows)} | {int(r.ol_rows)} | {int(r.def_rows)} |" for s, r in cov.iterrows()]
    L += ["", "Each variant refit walk-forward 2015-2025. Team points miss is the yardstick; flags at the live rules (weeks 1-17).", "",
          "| Variant | Window | Team miss | Total miss | Margin miss | Spread flag | Totals flag |", "|---|---|---|---|---|---|---|"]
    L += [f"| {r['variant']} | {r['window']} | {r['team_miss']:.4f} | {r['total_miss']:.4f} | {r['margin_miss']:.4f} | {r['spread_flag']} | {r['totals_flag']} |" for r in rows]
    L += ["", f"Variant C combines {why}."]
    for v, g_ in gates.items():
        L += ["", f"## Gate, variant {v} (parts 1 and 2; the placebo runs only for a variant that passes them)", "", G.markdown(g_)]
    md.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
