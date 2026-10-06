"""Check the live site for the current week: every game priced, the QB priced (game model and props) against ESPN's
depth chart (skipping QBs ruled out), forecasts on outdoor games, and the page's health checks.

    python tools/verify_live.py        (run from the repo folder, after git fetch/reset so the injury file is current)
"""
import json, time, urllib.request
import pandas as pd

BASE = "https://mattfos18.github.io/nfl-model/data/"
UA = {"User-Agent": "NFLModelResearch/1.0"}
ESPN_ABBR = {"WAS": "wsh", "LA": "lar"}


def js(name):
    t = urllib.request.urlopen(urllib.request.Request(BASE + name + f"?t={time.time()}", headers=UA), timeout=60).read().decode("utf-8")
    return json.loads(t.split("=", 1)[1].rstrip().rstrip(";"))


def depth_qbs(team):
    a = ESPN_ABBR.get(team, team.lower())
    url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/{a}/depthcharts"
    d = json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60))
    for grp in d.get("depthchart", []):
        if "qb" in grp.get("positions", {}):
            return [x["displayName"] for x in grp["positions"]["qb"]["athletes"]]
    return []


wk, h, pr = js("week.js"), js("health.js"), js("props.js")
print("week", wk["season"], wk["week"], "built", wk.get("built"), "| props built", pr.get("built"))
print("health:", h["passed"], "of", h["total"], "checked", h["checked"], "fails:", h["fails"])
inj = pd.read_csv("data/raw/injuries/espn_injuries.csv")
problems = []
for g in wk["games"]:
    if g.get("home_score") is not None:
        continue
    gid = g["game_id"]
    if g.get("model_spread") is None or g.get("model_total") is None or g.get("spread_line") is None:
        problems.append(f"{gid}: not priced")
    for t, sd in g["sides"].items():
        name, depth = sd.get("qb_name"), depth_qbs(t)
        out = set(inj[(inj.team == t) & inj.status.isin(["Out", "Doubtful", "Injured Reserve"])].name)
        expect = next((n for n in depth if n not in out), None)
        pq = [q["name"] for q in pr.get("games", {}).get(gid, {}).get(t, {}).get("qb", []) if not q["out"]][:1]
        pq = pq[0] if pq else None
        if name != expect:
            problems.append(f"{gid} {t}: priced {name}, ESPN QB1 (healthy) {expect}")
        if pq is not None and pq != name:
            problems.append(f"{gid} {t}: props QB {pq}, game model QB {name}")
        print(f"{gid:18} {t:4} QB {name!s:22} props {pq!s:20} ESPN {depth[:3]}")
    wx = g.get("wx") or {}
    if g.get("roof") == "outdoors" and wx.get("s") != "forecast":
        problems.append(f"{gid}: outdoor game without a forecast ({wx})")
print("\nPROBLEMS:" if problems else "\nNO PROBLEMS", *problems, sep="\n")
