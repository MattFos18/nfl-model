"""Bet tracker: the model's flagged picks and your actual bets, graded automatically, kept apart.

data/tracker/model_picks.csv   every flagged pick the weekly run makes (game, side, line at the time, edge,
                               model probability, flag reason). Appended each run; a game's pick is
                               replaced if the run re-prices it before kickoff.
data/tracker/my_bets.csv       your bets, one row each: game_id, bet (e.g. "KC -3", "Over 47.5", "MIA ML"),
                               odds (American, default -110), stake (units). Edit by hand or from the page.
data/tracker/graded.csv        both, graded against results and the closing line: win/loss/push, units,
                               and closing line value (the line you got minus the close, from your side).

Usage: python -m nflmodel.tracker   (writes reports/track_record.md)
"""
from __future__ import annotations
import re
import numpy as np, pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT, TR, REP = ROOT / "data" / "processed", ROOT / "data" / "tracker", ROOT / "reports"


def parse_bet(bet: str, home: str, away: str):
    """'KC -3' -> ('spread', 'KC', -3); 'Over 47.5' -> ('total', 'over', 47.5); 'KC ML' -> ('ml', 'KC', None)."""
    b = bet.strip()
    m = re.match(r"^(over|under)\s+([\d.]+)$", b, re.I)
    if m:
        return "total", m.group(1).lower(), float(m.group(2))
    m = re.match(r"^([A-Z]{2,3})\s+ML$", b, re.I)
    if m:
        return "ml", m.group(1).upper(), None
    m = re.match(r"^([A-Z]{2,3})\s*([+-]?[\d.]+)$", b, re.I)
    if m:
        return "spread", m.group(1).upper(), float(m.group(2))
    return None, None, None


def payout(odds: float, win: bool, push: bool, stake: float = 1.0):
    if push:
        return 0.0
    if win:
        return stake * (odds / 100 if odds > 0 else 100 / -odds)
    return -stake


def grade_rows(df: pd.DataFrame, games: pd.DataFrame) -> pd.DataFrame:
    g = games.set_index("game_id")
    out = []
    for r in df.itertuples():
        if r.game_id not in g.index:
            continue
        x = g.loc[r.game_id]
        kind, side, line = parse_bet(r.bet, x.home_team, x.away_team)
        row = {**r._asdict()}
        row.pop("Index", None)
        row.update({"kind": kind, "side": side, "line": line, "played": pd.notna(x.home_score)})
        odds = float(getattr(r, "odds", -110) if pd.notna(getattr(r, "odds", np.nan)) else -110)
        stake = float(getattr(r, "stake", 1.0) if pd.notna(getattr(r, "stake", np.nan)) else 1.0)
        if kind is None:
            row["result"] = "unparsed"
            out.append(row)
            continue
        # closing line value from this side's view (positive = you got a better number than the close)
        if kind == "spread":
            close = x.spread_line if side == x.home_team else -x.spread_line
            row["close"] = close
            row["clv"] = (line - close) if pd.notna(close) else np.nan
        elif kind == "total":
            row["close"] = x.total_line
            row["clv"] = (x.total_line - line) if side == "over" else (line - x.total_line)
        else:
            row["close"] = x.home_moneyline if side == x.home_team else x.away_moneyline
            row["clv"] = np.nan
        if pd.isna(x.home_score):
            row["result"] = "pending"
            out.append(row)
            continue
        margin = x.result if side == x.home_team else -x.result
        if kind == "spread":
            d = margin + line
            win, push = d > 0, d == 0
        elif kind == "total":
            d = x.total - line
            win, push = (d > 0) if side == "over" else (d < 0), d == 0
        else:
            win, push = margin > 0, margin == 0
        row["result"] = "push" if push else ("win" if win else "loss")
        row["units"] = payout(odds, win, push, stake)
        out.append(row)
    return pd.DataFrame(out)


def summary(gr: pd.DataFrame, by=None) -> pd.DataFrame:
    gr = gr[gr.result.isin(["win", "loss", "push"])]
    def agg(x):
        w, l, p = (x.result == "win").sum(), (x.result == "loss").sum(), (x.result == "push").sum()
        risked = x.apply(lambda r: (r.stake if pd.notna(getattr(r, "stake", np.nan)) else 1.0) * (1.0 if r.odds > 0 else -r.odds / 100), axis=1).sum() if len(x) else 0
        return pd.Series({"bets": w + l, "wins": w, "losses": l, "pushes": p, "win_pct": w / (w + l) if w + l else np.nan,
                          "units": x.units.sum(), "roi": x.units.sum() / risked if risked else np.nan, "avg_clv": x.clv.mean()})
    if by is None:
        return agg(gr).to_frame("all").T
    return gr.groupby(by).apply(agg, include_groups=False)


def record_model_picks(picks: pd.DataFrame, run_at: str):
    """Append this run's flagged picks (from picks.table) to model_picks.csv, replacing earlier rows for the same game."""
    TR.mkdir(parents=True, exist_ok=True)
    games = pd.read_parquet(OUT / "games.parquet").set_index("game_id")
    now = pd.Timestamp.now(tz="America/New_York").tz_localize(None)
    rows = []
    for r in picks.itertuples():
        if not r.bet:
            continue
        if r.game_id in games.index and (pd.notna(games.loc[r.game_id, "home_score"]) or games.loc[r.game_id, "kickoff_et"] <= now):
            continue  # never record a pick on a game that has kicked off
        for b in r.bet.split(", "):
            rows.append({"run_at": run_at, "season": r.season, "week": r.week, "game_id": r.game_id, "bet": b, "odds": -110, "stake": 1.0,
                         "spread_edge": round(r.spread_edge, 2) if pd.notna(r.spread_edge) else np.nan,
                         "total_edge": round(r.total_edge, 2) if pd.notna(r.total_edge) else np.nan,
                         "p_cover": round(r.p_cover_home if r.home_team in b else 1 - r.p_cover_home, 3) if b[:2].isalpha() and pd.notna(r.p_cover_home) and not b.startswith(("Over", "Under")) else np.nan})
    new = pd.DataFrame(rows)
    f = TR / "model_picks.csv"
    if f.exists():
        old = pd.read_csv(f)
        # keep old rows for games already kicked off; replace the rest with this run's
        played = old.game_id.map(games.home_score).notna()
        old = old[played | ~old.game_id.isin(new.game_id)]
        new = pd.concat([old, new], ignore_index=True)
    new.to_csv(f, index=False)
    return new


def main():
    games = pd.read_parquet(OUT / "games.parquet")
    TR.mkdir(parents=True, exist_ok=True)
    mp = pd.read_csv(TR / "model_picks.csv") if (TR / "model_picks.csv").exists() else pd.DataFrame(columns=["game_id", "bet", "odds", "stake"])
    mb = pd.read_csv(TR / "my_bets.csv") if (TR / "my_bets.csv").exists() else pd.DataFrame(columns=["game_id", "bet", "odds", "stake"])
    gm = grade_rows(mp, games).assign(who="model") if len(mp) else pd.DataFrame()
    gb = grade_rows(mb, games).assign(who="matt") if len(mb) else pd.DataFrame()
    gr = pd.concat([gm, gb], ignore_index=True)
    for c in ["season", "week", "game_id", "bet", "odds", "stake", "close", "clv", "result", "units", "kind", "who"]:
        if c not in gr.columns:
            gr[c] = np.nan
    gr.to_csv(TR / "graded.csv", index=False)
    L = ["# Track record", "", "Model picks and Matt's bets, graded against results, at the odds recorded. Closing line value (CLV) is the line "
         "recorded minus the closing line from the bet's side: positive means the number beat the close.", ""]
    for who, name in [("model", "Model picks (flagged at 5+ spread, 6+ total)"), ("matt", "Matt's bets")]:
        x = gr[gr.who == who] if len(gr) else gr
        L += [f"## {name}", ""]
        if len(x) == 0:
            L += ["No bets recorded yet.", ""]
            continue
        settled = x[x.result.isin(["win", "loss", "push"])]
        L += [f"{len(x)} recorded, {len(settled)} settled, {int((x.result == 'pending').sum())} pending.", ""]
        if len(settled):
            L += [summary(x).round(3).to_markdown(), "", "By kind:", "", summary(x, "kind").round(3).to_markdown(), "", "By week:", "", summary(x, ["season", "week"]).round(3).to_markdown(), ""]
        L += ["Every bet:", "", x[["season", "week", "game_id", "bet", "odds", "close", "clv", "result", "units"]].round(2).to_markdown(index=False), ""]
    (REP / "track_record.md").write_text("\n".join(L))
    print("\n".join(L[:12]))


if __name__ == "__main__":
    main()
