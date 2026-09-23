"""The weekly audit: everything that can be checked by a program, in one report with one result.
Sections: health (freshness and steps), data verification, the tie-out (sources and page), the leak test, the
JavaScript syntax, every page data file parsing, and a Chromium walk of every view (when node and Playwright are
available). Writes reports/weekly_audit.md and exits non-zero if any section fails.
Usage: python -m nflmodel.audit_weekly [--no-browser]"""
from __future__ import annotations
import glob, json, os, re, subprocess, sys, time
import pandas as pd
from .features import ROOT
REP = ROOT / "reports"; WEB = ROOT / "web"


def section(name, fn):
    t = time.time()
    try:
        ok, detail = fn()
    except Exception as e:  # noqa
        ok, detail = False, f"crashed: {str(e)[:200]}"
    return {"section": name, "ok": bool(ok), "detail": detail, "seconds": round(time.time() - t, 1)}


def run_health():
    from . import health as H
    ok = H.main(); txt = (REP / "health.md").read_text()
    m = re.search(r"\*\*(HEALTHY|BROKEN)\*\*: (.*)", txt); return ok, m.group(0).replace("**", "") if m else "no summary"


def run_verify():
    r = subprocess.run([sys.executable, "-m", "nflmodel.verify"], capture_output=True, text=True, cwd=ROOT)
    txt = (REP / "verification.md").read_text() if (REP / "verification.md").exists() else r.stdout
    return "Result: PASS" in txt and r.returncode == 0, (re.findall(r"Result: .*", txt) or [r.stderr[-200:]])[-1]


def run_tie():
    from . import tie_check as T
    ok = T.main(True); txt = (REP / "tie_check.md").read_text(); return ok, (re.findall(r"Result: .*", txt) or ["?"])[-1]


def run_leak():
    from .audit import leakage_test
    r = leakage_test(); ok = r["max_rating_change_after_corrupting_future"] == 0 and r["max_prediction_change_after_corrupting_targets"] == 0
    return ok, f"rating change {r['max_rating_change_after_corrupting_future']}, prediction change {r['max_prediction_change_after_corrupting_targets']} after corrupting every future game"


def run_js():
    js = "const fs=require('fs');const h=fs.readFileSync(process.argv[1],'utf8');const m=h.match(/<script>([\\s\\S]*?)<\\/script>/g)||[];let bad=[];for(const s of m){const c=s.replace(/^<script>/,'').replace(/<\\/script>$/,'');try{new Function(c)}catch(e){bad.push(e.message)}}console.log(JSON.stringify({blocks:m.length,bad}));process.exit(bad.length?1:0)"
    r = subprocess.run(["node", "-e", js, str(WEB / "index.html")], capture_output=True, text=True)
    if r.returncode not in (0, 1) or not r.stdout.strip():
        return False, f"node unavailable or crashed: {r.stderr[-200:]}"
    j = json.loads(r.stdout); return not j["bad"], f"{j['blocks']} script blocks, " + ("all parse" if not j["bad"] else "; ".join(j["bad"])[:200])


def run_parse():
    bad = []
    files = sorted(glob.glob(str(WEB / "data" / "*.js")))
    for f in files:
        s = open(f).read().rstrip().rstrip(";")
        i = (s.index('"]=') + 2) if s.startswith("window.TEAMDATA") else s.index("=")
        try: json.loads(s[i + 1:])
        except Exception as e: bad.append(f"{os.path.basename(f)}: {str(e)[:60]}")
    return not bad and len(files) >= 39, f"{len(files)} files, " + ("all parse" if not bad else "; ".join(bad)[:200])


def run_walk():
    exe = os.environ.get("CHROMIUM_PATH") or ("/opt/pw-browsers/chromium" if os.path.exists("/opt/pw-browsers/chromium") else "")
    env = dict(os.environ)
    if os.path.isdir("/opt/node22/lib/node_modules"): env["NODE_PATH"] = "/opt/node22/lib/node_modules"
    r = subprocess.run(["node", str(ROOT / "tools" / "page_walk.js"), str(WEB / "index.html")] + ([exe] if exe else []), capture_output=True, text=True, cwd=ROOT, env=env, timeout=600)
    if not r.stdout.strip().startswith("{"):
        return False, f"walk did not run: {(r.stderr or r.stdout)[-200:]}"
    j = json.loads(r.stdout.strip().splitlines()[-1])
    return j["ok"], f"{len(j['views'])} views, {j['cards']} cards, errors {j['errors'][:3]}, bad {j['bad'][:3]}"


def main(browser: bool = True) -> bool:
    now = pd.Timestamp.now("UTC").tz_localize(None)
    secs = [section("Health: runs, steps, freshness, picks vs tracker, page settings", run_health),
            section("Data verification: scores, mirrors, PFR totals, known results", run_verify),
            section("Tie-out: every headline number across README, docs, sweep, picks, tracker and page", run_tie),
            section("Leak test: corrupt every future game, nothing before the cut may move", run_leak),
            section("Page JavaScript parses", run_js),
            section("Every page data file parses", run_parse)]
    if browser:
        secs.append(section("Chromium walk of every view: no errors, no NaN, nothing empty", run_walk))
    ok = all(s["ok"] for s in secs)
    L = [f"# Weekly audit, {now:%Y-%m-%d %H:%M} UTC", "", f"**{'CLEAN' if ok else 'FAILING'}**: {sum(s['ok'] for s in secs)} of {len(secs)} sections pass.", "",
         "| Section | Result | Detail | Seconds |", "|---|---|---|---|"] + [f"| {s['section']} | {'PASS' if s['ok'] else 'FAIL'} | {s['detail']} | {s['seconds']} |" for s in secs] + \
        ["", "The health table is in reports/health.md, the tie-out rows in reports/tie_check.md, the verification detail in reports/verification.md.", "", f"Result: {'PASS' if ok else 'FAIL'}"]
    REP.mkdir(exist_ok=True); (REP / "weekly_audit.md").write_text("\n".join(L) + "\n"); print("\n".join(L))
    return ok


if __name__ == "__main__":
    sys.exit(0 if main("--no-browser" not in sys.argv) else 1)
