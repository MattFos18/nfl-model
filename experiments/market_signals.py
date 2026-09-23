"""Market signals from the line log (data/lines/lines_log.csv, every 30 minutes since Week 3 of 2026), testable only
once it holds a good part of a season. For every graded game with an opener and a close in the log: did the line
move toward or away from the model between the opener and the close, and how often did the model's side cover in
each case; did the model's edge at the opener predict the direction of the move (bet early or wait); and reverse
line movement, where the books' consensus moved against the side the model favoured. Prints counts and writes
reports/market_signals.md. Says so and stops when there are fewer than 60 graded games."""
import numpy as np, pandas as pd
from nflmodel.model import OUT
from nflmodel.features import ROOT
LOG = ROOT / "data" / "lines" / "lines_log.csv"; RUNS = ROOT / "data" / "runs" / "pred_history.csv"
lines = pd.read_csv(LOG); lines = lines[lines.home_spread.notna()].copy(); lines["t"] = pd.to_datetime(lines.ts.str.replace("Z", ""), format="%Y-%m-%dT%H-%M-%S", errors="coerce")
games = pd.read_parquet(OUT / "games.parquet").set_index("game_id")
runs = pd.read_csv(RUNS) if RUNS.exists() else pd.DataFrame()
rows = []
for gid, h in lines.groupby("game_id"):
    if gid not in games.index or pd.isna(games.loc[gid, "home_score"]): continue
    h = h.sort_values("t"); cons = h.groupby("t").home_spread.median()
    opener, close = float(cons.iloc[0]), float(cons.iloc[-1])
    r = runs[runs.game_id == gid].sort_values("run_at") if len(runs) else pd.DataFrame()
    if len(r) == 0: continue
    model_open = float(r.model_spread.iloc[0])   # the model's line at its first run of the week
    margin = float(games.loc[gid, "home_score"] - games.loc[gid, "away_score"])
    edge_open = model_open - opener; side = 1 if edge_open > 0 else -1
    move = (close - opener) * side   # positive: the line moved toward the model's side (the number got worse for that side)
    covered = np.sign(margin - close) == side if margin != close else np.nan
    rows.append({"game_id": gid, "opener": opener, "close": close, "model_open": model_open, "edge_open": edge_open, "move_toward_model": move, "covered_at_close": covered,
                 "covered_at_open": (np.sign(margin - opener) == side) if margin != opener else np.nan})
d = pd.DataFrame(rows)
L = [f"# Market signals, {pd.Timestamp.now('UTC'):%Y-%m-%d}", ""]
if len(d) < 60:
    L += [f"Not enough data yet: {len(d)} graded games with an opener, a close and a model line in the log (need 60)."]
else:
    big = d[d.edge_open.abs() >= 3]
    toward, away = big[big.move_toward_model > 0], big[big.move_toward_model < 0]
    rec = lambda x: f"{int((x.covered_at_close == True).sum())}-{int((x.covered_at_close == False).sum())}"
    L += [f"{len(d)} graded games; {len(big)} with a 3+ edge at the opener.", "",
          f"Line moved toward the model's side (the market agreed): {len(toward)} games, model's side covered at the close {rec(toward)}.",
          f"Line moved away from the model's side (the market disagreed): {len(away)} games, covered {rec(away)}.",
          f"Model's side at the opener's number instead of the close: {rec(big.assign(covered_at_close=big.covered_at_open))} against {rec(big)} at the close.",
          f"Correlation between the edge at the opener and the move toward the model: {np.corrcoef(big.edge_open.abs(), big.move_toward_model)[0, 1]:.2f} (positive: the market drifts toward the model, so bet early).", ""]
(ROOT / "reports" / "market_signals.md").write_text("\n".join(L) + "\n"); print("\n".join(L)); d.to_csv(ROOT / "reports" / "market_signals.csv", index=False)
