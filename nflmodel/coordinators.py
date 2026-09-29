"""Head coach, offensive and defensive coordinators per team-season, from Wikipedia's team-season articles (29 Sep 2026,
Matt: coordinators and play-callers for the matchup studies; Pro Football Reference refuses GitHub's runners). Each
"<season> <team> season" article's staff section lists "Head coach – [[...]]", "Offensive coordinator – [[...]]" and
"Defensive coordinator – [[...]]"; several names when the job changed hands. Older articles sometimes carry the staff
only in prose; those rows are written with blanks and status "no staff list", never guessed. Play-callers are not in
any free source, so they are not in this table. Writes data/reference/coordinators.csv and prints it between CSV
markers, so a probe run can hand it over from GitHub's network (this sandbox cannot reach Wikipedia).
Usage: python -m nflmodel.coordinators --seasons 2013-2026"""
from __future__ import annotations
import argparse, re, time
import pandas as pd, requests
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTF = ROOT / "data" / "reference" / "coordinators.csv"
API = "https://en.wikipedia.org/w/api.php"
UA = {"User-Agent": "nfl-model research (github.com/MattFos18/nfl-model)"}


def team_name(team: str, season: int) -> str:
    fixed = {"ARI": "Arizona Cardinals", "ATL": "Atlanta Falcons", "BAL": "Baltimore Ravens", "BUF": "Buffalo Bills", "CAR": "Carolina Panthers",
             "CHI": "Chicago Bears", "CIN": "Cincinnati Bengals", "CLE": "Cleveland Browns", "DAL": "Dallas Cowboys", "DEN": "Denver Broncos",
             "DET": "Detroit Lions", "GB": "Green Bay Packers", "HOU": "Houston Texans", "IND": "Indianapolis Colts", "JAX": "Jacksonville Jaguars",
             "KC": "Kansas City Chiefs", "MIA": "Miami Dolphins", "MIN": "Minnesota Vikings", "NE": "New England Patriots", "NO": "New Orleans Saints",
             "NYG": "New York Giants", "NYJ": "New York Jets", "PHI": "Philadelphia Eagles", "PIT": "Pittsburgh Steelers", "SEA": "Seattle Seahawks",
             "SF": "San Francisco 49ers", "TB": "Tampa Bay Buccaneers", "TEN": "Tennessee Titans"}
    if team in fixed:
        return fixed[team]
    if team == "LAC":
        return "San Diego Chargers" if season <= 2016 else "Los Angeles Chargers"
    if team == "LA":
        return "St. Louis Rams" if season <= 2015 else "Los Angeles Rams"
    if team == "LV":
        return "Oakland Raiders" if season <= 2019 else "Las Vegas Raiders"
    if team == "WAS":
        return "Washington Redskins" if season <= 2019 else ("Washington Football Team" if season <= 2021 else "Washington Commanders")
    raise KeyError(team)


TEAMS = ["ARI", "ATL", "BAL", "BUF", "CAR", "CHI", "CIN", "CLE", "DAL", "DEN", "DET", "GB", "HOU", "IND", "JAX", "KC", "LAC", "LA", "LV", "MIA",
         "MIN", "NE", "NO", "NYG", "NYJ", "PHI", "PIT", "SEA", "SF", "TB", "TEN", "WAS"]


def _role(w: str, label: str) -> str:
    """Names on staff-list lines for this role ("Offensive coordinator – [[A|B]]"), in order, without duplicates."""
    out = []
    for line in re.findall(r"(?im)^[^\n]*\b" + label + r"\b[^\n]*$", w):
        if not re.search(r"[–—-]\s*\[\[", line):
            continue
        for link in re.findall(r"\[\[([^\]]+)\]\]", line.split(label, 1)[-1] if label in line else line):
            name = link.split("|")[-1].strip()
            if name and name not in out and "coordinator" not in name.lower():
                out.append(name)
        if out:
            break
    return "; ".join(out)


def fetch(team: str, season: int) -> dict:
    page = f"{season} {team_name(team, season)} season"
    for attempt in range(3):
        try:
            r = requests.get(API, params={"action": "parse", "page": page, "prop": "wikitext", "format": "json", "redirects": 1}, headers=UA, timeout=30)
            r.raise_for_status(); j = r.json()
            if "error" in j:
                return {"team": team, "season": season, "head_coach": "", "oc": "", "dc": "", "status": "no article"}
            w = j["parse"]["wikitext"]["*"]
            oc, dc, hc = _role(w, "Offensive coordinator"), _role(w, "Defensive coordinator"), _role(w, "Head coach")
            return {"team": team, "season": season, "head_coach": hc, "oc": oc, "dc": dc, "status": "ok" if (oc or dc) else "no staff list"}
        except Exception as e:  # noqa
            err = str(e)[:80]; time.sleep(3 * (attempt + 1))
    return {"team": team, "season": season, "head_coach": "", "oc": "", "dc": "", "status": "error: " + err}


def main(seasons, only_errors=False):
    rows = []
    print("ROWHEAD,team,season,head_coach,oc,dc,status", flush=True)
    redo = None
    if only_errors and OUTF.exists():   # refetch only the rows a run could not read (rate-limited), one at a time
        have = pd.read_csv(OUTF)
        redo = set(zip(have.team, have.season)) - set(zip(have[have.status.isin(["ok", "no staff list", "no article"])].team, have[have.status.isin(["ok", "no staff list", "no article"])].season))
    for s in seasons:
        for t in TEAMS:
            if redo is not None and (t, s) not in redo:
                continue
            rows.append(fetch(t, s)); time.sleep(1.0 if redo is not None else 0.2)
            r = rows[-1]; print("ROW," + ",".join(str(r[c]).replace(",", " ") for c in ["team", "season", "head_coach", "oc", "dc", "status"]), flush=True)   # as it lands, so a run cut off by its time limit still hands over what it fetched
    out = pd.DataFrame(rows).sort_values(["season", "team"])
    if redo is not None:   # keep every row already read, replace the refetched ones
        out = pd.concat([pd.read_csv(OUTF), out], ignore_index=True).drop_duplicates(["team", "season"], keep="last").sort_values(["season", "team"])
    OUTF.parent.mkdir(parents=True, exist_ok=True); out.to_csv(OUTF, index=False)
    print("coverage:"); print(out.groupby("season").status.value_counts().unstack(fill_value=0).to_string())
    print("===CSV START==="); print(out.to_csv(index=False), end=""); print("===CSV END===")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--seasons", default="2013-2026"); ap.add_argument("--only-errors", action="store_true"); a = ap.parse_args()
    lo, hi = (a.seasons.split("-") + [None])[:2]
    main(list(range(int(lo), int(hi or lo) + 1)), a.only_errors)
