"""Picks-final alert (1 Oct 2026, Matt: "alert me when injury reports come out so I know our picks are final"). Teams post
their last injury report, with game statuses, at about 4pm ET two days before a game (Friday for Sunday, Saturday for
Monday), the day before for a Thursday game. Once that report is in for a slate and the model has re-priced on it,
this opens one GitHub issue labelled picks-final with the slate's bets (GitHub pushes it to the mobile app and emails it).

A slate is final when: an hour has passed since its final report, a line-watch check of the reports ran after it, no
re-price it asked for is still waiting on the weekly run (the newest weekly picks run is later than the newest re-price
request), and the slate has not kicked off. Run from nflmodel/health_alert.py on every line watch and weekly run.
"""
from __future__ import annotations
import json
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB, RUNS = ROOT / "web" / "data", ROOT / "data" / "runs"
LABEL = "picks-final"
REPORT_HOUR, WAIT = 16, pd.Timedelta(hours=1)


def final_report(kickoff: pd.Timestamp) -> pd.Timestamp:
    """When the last injury report with game statuses comes out for a game kicking off at kickoff (ET, naive)."""
    days = 1 if kickoff.dayofweek == 3 else 2   # Thursday games: Wednesday; the rest: two days before
    return (kickoff.normalize() - pd.Timedelta(days=days)) + pd.Timedelta(hours=REPORT_HOUR)


def _utc_to_et(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s.str.replace(" UTC", ""), errors="coerce").dt.tz_localize("UTC").dt.tz_convert("America/New_York").dt.tz_localize(None)


def slates(now_et: pd.Timestamp | None = None) -> list[dict]:
    """The week's slates (games sharing a final report), each with whether its picks are final now and its bets."""
    wk = json.loads((WEB / "week.js").read_text().split("=", 1)[1].rstrip().rstrip(";"))
    now = now_et if now_et is not None else pd.Timestamp.now(tz="America/New_York").tz_localize(None)
    rl = pd.read_csv(RUNS / "refresh_log.csv") if (RUNS / "refresh_log.csv").exists() else pd.DataFrame(columns=["checked", "reprice"])
    checked = _utc_to_et(rl.checked.astype(str)) if len(rl) else pd.Series(dtype="datetime64[ns]")
    asked = checked[rl.reprice.astype(str).eq("True").values] if len(rl) else checked
    runs = pd.read_csv(RUNS / "run_log.csv") if (RUNS / "run_log.csv").exists() else pd.DataFrame(columns=["step", "status", "run_at"])
    picks = _utc_to_et(runs.loc[(runs.step == "picks") & (runs.status == "ok"), "run_at"].astype(str))
    last_pick = picks.max() if len(picks) else pd.NaT
    out = {}
    for g in wk.get("games", []):
        if g.get("home_score") is not None or not g.get("kickoff"):
            continue
        ko = pd.Timestamp(g["kickoff"]); fr = final_report(ko)
        s = out.setdefault(fr, {"final_report": fr, "games": [], "first_kickoff": ko})
        s["first_kickoff"] = min(s["first_kickoff"], ko)
        bets = list(dict.fromkeys(b for b in [g.get("bet") or "", g.get("shadowunder_bet") or "", g.get("windunder_bet") or ""] if b))   # the wind under once when the totals flag has it too
        s["games"].append({"game": f"{g['away_team']} @ {g['home_team']}", "kickoff": ko, "bets": bets})
    res = []
    for fr, s in sorted(out.items()):
        seen = checked[checked >= fr]
        pending = len(asked) and pd.notna(asked.max()) and (pd.isna(last_pick) or asked.max() > last_pick)
        s["final"] = bool(now >= fr + WAIT and len(seen) and not pending and now < s["first_kickoff"])
        s["title"] = f"Week {wk['week']} picks final: {s['first_kickoff']:%a %b} {s['first_kickoff'].day} games"
        res.append(s)
    return res


def body(s: dict, owner: str = "") -> str:
    L = [f"Final injury reports are in and the model has re-priced. {'@' + owner if owner else ''}".strip(), ""]
    bets = [(g, b) for g in s["games"] for b in g["bets"]]
    if bets:
        L += [f"- **{b}** ({g['game']}, {g['kickoff']:%a %-I:%M %p} ET)" for g, b in bets]
    else:
        L += ["No bets in these games."]
    L += ["", f"Games: {', '.join(g['game'] for g in s['games'])}.", "", "Lines can still move; the page has the live number."]
    return "\n".join(L)


def notify(gh) -> None:
    """Open one picks-final issue per final slate (once per title). gh: health_alert._gh."""
    import os
    final = [s for s in slates() if s["final"]]
    if not final:
        return
    try:
        gh("label", "create", LABEL, "--color", "1d76db", "--description", "the week's picks after the final injury report")
    except Exception:  # noqa  (the label exists)
        pass
    have = {i["title"] for i in json.loads(gh("issue", "list", "--label", LABEL, "--state", "all", "--json", "title", "--limit", "200") or "[]")}
    owner = os.environ.get("GITHUB_REPOSITORY_OWNER", "")
    for s in final:
        if s["title"] in have:
            continue
        for i in json.loads(gh("issue", "list", "--label", LABEL, "--state", "open", "--json", "number", "--limit", "50") or "[]"):
            gh("issue", "close", str(i["number"]))   # the last slate's alert is done once the next one is out
        gh("issue", "create", "--title", s["title"], "--label", LABEL, "--body", body(s, owner)); print("picks-final issue opened:", s["title"])


if __name__ == "__main__":
    for s in slates():
        print(s["title"], "| final report", s["final_report"], "| final now:", s["final"], "|", [b for g in s["games"] for b in g["bets"]])
