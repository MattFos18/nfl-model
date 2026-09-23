"""The projections against the closing book lines, 2023 on (23 Sep 2026). Needs data/lines/props_history.csv from
nflmodel/props_history.py (The Odds API, paid plan, closing snapshots one hour before kickoff). For every player-game
with both a walk-forward projection (the adopted rule, experiments/props_by_season.py logic) and a closing line: the
side the projection takes (over above the line, under below), the result, and the edge. Then the threshold sweep the
game model has: the record at every edge cut, on a tuning window (2023 to 2024) and held out (2025 on), with the
break-even at -110 (52.4%). Also the book's own error against the projection's on the same player-games, and a
blended line (projection moved part of the way toward the book) to see whether the book's number improves the
projection. Anytime touchdown: the projection's chance of a score against the book's implied price, graded on
whether he scored. Line shopping: the same side graded against the best line across the books at the close. If an
opening snapshot exists too: the record at the opener and the closing line value (how far the close moved toward
the side taken). Output reports/props_vs_market_backtest.csv (records by cut), props_vs_market_rows.csv (every
graded player-game), props_vs_market_cuts.csv (the cut to flag at per stat, chosen like the game model's: the
largest cut clearing 52.4% on both windows with 100 decided bets on each, or none), and a summary printed."""
import numpy as np, pandas as pd, sys
from nflmodel.model import OUT
from nflmodel.props_lines import norm_name
from nflmodel.props import implied
HIST = OUT.parent / "lines" / "props_history.csv"
if not HIST.exists():
    sys.exit("no data/lines/props_history.csv: run nflmodel/props_history.py first")
# the walk-forward projections: reuse the by-season builder
import importlib.util, pathlib
spec = importlib.util.spec_from_file_location("bys", pathlib.Path(__file__).with_name("props_by_season.py"))
src = pathlib.Path(__file__).with_name("props_by_season.py").read_text().split("by_season, by_pos, by_bucket = [], [], []")[0]   # everything up to the scoring loops
ns = {"__name__": "bys"}; exec(compile(src, "bys", "exec"), ns); build = ns["build"]
names = ns["names"]
h = pd.read_csv(HIST); h["key"] = h.player.map(norm_name); h["snapshot"] = h.get("snapshot", pd.Series(["close"] * len(h))).fillna("close")
def consensus(x):
    return x.groupby(["game_id", "stat", "key"]).agg(line=("line", "median"), books=("book", "nunique"), over_price=("over_price", "mean"), under_price=("under_price", "mean"), best_over=("line", "min"), best_under=("line", "max")).reset_index()
close = consensus(h[h.snapshot == "close"]); opener = consensus(h[h.snapshot == "open"]) if (h.snapshot == "open").any() else None
WIN = {"2023-24": (2023, 2024), "2025+": (2025, 2030)}
rows, sweep = [], []
def side_rows(f, stat, line_col, act_col):
    f = f.copy(); f["key"] = f.pid.map(lambda p: norm_name(names.get(p, ("", ""))[0])); f["stat"] = stat
    m = f.merge(close[close.stat == stat], on=["game_id", "stat", "key"], how="inner")
    m["side"] = np.where(m[line_col] > m.line, "over", np.where(m[line_col] < m.line, "under", "none")); m = m[m.side != "none"]
    m["edge"] = (m[line_col] - m.line).abs(); m["win"] = np.where(m[act_col] == m.line, np.nan, ((m[act_col] > m.line) == (m.side == "over")).astype(float))
    # line shopping: the best line for the side taken across the books at the close (lowest for an over, highest for an under)
    m["best"] = np.where(m.side == "over", m.best_over, m.best_under); m["win_best"] = np.where(m[act_col] == m.best, np.nan, ((m[act_col] > m.best) == (m.side == "over")).astype(float))
    if opener is not None:
        o = opener[opener.stat == stat][["game_id", "stat", "key", "line"]].rename(columns={"line": "open_line"}); m = m.merge(o, on=["game_id", "stat", "key"], how="left")
        m["open_side"] = np.where(m.open_line.isna(), "none", np.where(m[line_col] > m.open_line, "over", np.where(m[line_col] < m.open_line, "under", "none")))
        m["win_open"] = np.where(m.open_side == "none", np.nan, np.where(m[act_col] == m.open_line, np.nan, ((m[act_col] > m.open_line) == (m.open_side == "over")).astype(float)))
        m["clv"] = np.where(m.open_side == "over", m.line - m.open_line, np.where(m.open_side == "under", m.open_line - m.line, np.nan))   # how far the close moved toward the side taken at the open
    m["proj_err"] = (m[line_col] - m[act_col]).abs(); m["line_err"] = (m.line - m[act_col]).abs()
    for w_ in [0.25, 0.5, 0.75]: m[f"blend{int(w_*100)}_err"] = ((1 - w_) * m[line_col] + w_ * m.line - m[act_col]).abs()
    return m
def sweep_rows(m, stat, cuts):
    for w, (a, b) in WIN.items():
        x = m[m.season.between(a, b)]
        for c in cuts:
            y = x[x.edge >= c]; g = y.win.dropna(); wins, losses = int(g.sum()), int(len(g) - g.sum())
            gb = y.win_best.dropna() if "win_best" in y else pd.Series(dtype=float); go = y.win_open.dropna() if "win_open" in y else pd.Series(dtype=float)
            sweep.append({"stat": stat, "window": w, "cut": c, "n": int(len(y)), "wins": wins, "losses": losses, "pushes": int(y.win.isna().sum()), "pct": round(wins / (wins + losses), 4) if wins + losses else None,
                          "pct_best_line": (round(float(gb.mean()), 4) if len(gb) else None), "n_open": int(len(go)), "pct_open": (round(float(go.mean()), 4) if len(go) else None), "clv": (round(float(y.clv.mean()), 3) if "clv" in y and y.clv.notna().any() else None),
                          "proj_mae": round(float(y.proj_err.mean()), 3) if len(y) else None, "line_mae": round(float(y.line_err.mean()), 3) if len(y) else None, **{f"blend{k}_mae": (round(float(y[f"blend{k}_err"].mean()), 3) if len(y) else None) for k in (25, 50, 75)}})
for kind in ["rec", "rush", "pass"]:
    f, ev = build(kind); f = f[f.season >= 2023]
    stat = f"{kind}_yards"; m = side_rows(f, stat, "yds_line", "act_yds"); rows.append(m); sweep_rows(m, stat, [0, 2.5, 5, 7.5, 10, 15, 20] if kind != "pass" else [0, 5, 10, 15, 20, 30, 40])
    if kind == "rec":
        m = side_rows(f, "rec_catches", "catch_line", "act_catch"); rows.append(m); sweep_rows(m, "rec_catches", [0, 0.25, 0.5, 0.75, 1.0, 1.5])
    # anytime touchdown: receiving + rushing expected scores per player-game
    f["td_any_line"] = f.td_line if kind == "pass" else f.td_line
    if kind != "pass":
        t = f[["pid", "game_id", "season", "week", "td_line", "act_td"]].rename(columns={"td_line": f"td_{kind}", "act_td": f"act_{kind}"}); ns[f"td_{kind}"] = t
if "td_rec" in ns and "td_rush" in ns:
    t = ns["td_rec"].merge(ns["td_rush"], on=["pid", "game_id", "season", "week"], how="outer").fillna(0.0)
    t["p_us"] = 1 - np.exp(-(t.td_rec + t.td_rush)); t["scored"] = ((t.act_rec + t.act_rush) >= 1).astype(float); t["key"] = t.pid.map(lambda p: norm_name(names.get(p, ("", ""))[0])); t["stat"] = "anytime_td"
    m = t.merge(close[close.stat == "anytime_td"], on=["game_id", "stat", "key"], how="inner"); m = m[m.over_price.notna()].copy(); m["p_book"] = m.over_price.map(implied)
    m["side"] = np.where(m.p_us > m.p_book, "yes", "no"); m["edge"] = (m.p_us - m.p_book).abs(); m["win"] = ((m.scored == 1) == (m.side == "yes")).astype(float)
    m["proj_err"] = (m.p_us - m.scored).abs(); m["line_err"] = (m.p_book - m.scored).abs()
    for w_ in [25, 50, 75]: m[f"blend{w_}_err"] = ((1 - w_ / 100) * m.p_us + w_ / 100 * m.p_book - m.scored).abs()
    m["yes_wins"] = np.where(m.side == "yes", m.win, np.nan)
    rows.append(m); sweep_rows(m, "anytime_td", [0, 0.02, 0.05, 0.08, 0.10, 0.15]); sweep_rows(m[m.side == "yes"], "anytime_td_yes", [0, 0.02, 0.05, 0.08, 0.10, 0.15])   # only the yes side is offered at most books
allrows = pd.concat(rows, ignore_index=True); keep = [c for c in ["stat", "season", "week", "game_id", "pid", "key", "side", "edge", "line", "best", "open_line", "books", "win", "win_best", "win_open", "clv", "proj_err", "line_err"] if c in allrows.columns]
allrows[keep].to_csv("reports/props_vs_market_rows.csv", index=False); S = pd.DataFrame(sweep); S.to_csv("reports/props_vs_market_backtest.csv", index=False)
# the cut to flag at, chosen the way the game model's was: the largest cut whose record clears break-even (52.4% at -110)
# on BOTH windows with at least 100 decided bets on each, taking the higher combined win rate among ties; none if no cut does
chosen = []
for stat, g in S.groupby("stat"):
    ok = None
    for c in sorted(g.cut.unique()):
        a, b = g[(g.window == "2023-24") & (g.cut == c)], g[(g.window == "2025+") & (g.cut == c)]
        if len(a) and len(b) and a.pct.iloc[0] is not None and b.pct.iloc[0] is not None and a.pct.iloc[0] >= 0.524 and b.pct.iloc[0] >= 0.524 and (a.wins.iloc[0] + a.losses.iloc[0]) >= 100 and (b.wins.iloc[0] + b.losses.iloc[0]) >= 100:
            tot = (a.wins.iloc[0] + b.wins.iloc[0]) / (a.wins.iloc[0] + a.losses.iloc[0] + b.wins.iloc[0] + b.losses.iloc[0])
            if ok is None or tot > ok[1]: ok = (c, tot, int(a.wins.iloc[0] + a.losses.iloc[0] + b.wins.iloc[0] + b.losses.iloc[0]))
    chosen.append({"stat": stat, "cut": None if ok is None else ok[0], "pct_both": None if ok is None else round(ok[1], 4), "decided": None if ok is None else ok[2]})
pd.DataFrame(chosen).to_csv("reports/props_vs_market_cuts.csv", index=False)
print(S.to_string()); print(pd.DataFrame(chosen).to_string()); print("DONE")
