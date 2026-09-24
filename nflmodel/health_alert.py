"""Alert when the site's checks fail (24 Sep 2026). Reads web/data/health.js (written by tie_check on every weekly run
and every line-watch run) and keeps one GitHub issue labelled `site-health` in step with it: opened when a check
fails (GitHub emails the repository's owner), its body refreshed while checks keep failing, closed with a note when
everything passes again. Also flags a late line watch (no line snapshot for over two hours). Needs GH_TOKEN with
issues: write; does nothing without it.

python -m nflmodel.health_alert
"""
from __future__ import annotations
import json, os, subprocess
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web" / "data"
LABEL = "site-health"


def _gh(*args) -> str:
    r = subprocess.run(["gh", *args], capture_output=True, text=True, cwd=ROOT)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip()[:300])
    return r.stdout.strip()


def status() -> tuple[bool, list[str], dict]:
    h = json.loads((WEB / "health.js").read_text().split("=", 1)[1].rstrip().rstrip(";")) if (WEB / "health.js").exists() else None
    problems = []
    if h is None:
        problems.append("web/data/health.js is missing: the checks did not run")
    else:
        problems += [f"{f['what']}: reads {f['reads']}, should read {f['should']}" for f in h.get("fails", [])]
    if os.environ.get("JOB_STATUS") and os.environ["JOB_STATUS"] != "success":   # the run itself failed before or after the checks
        run = f"{os.environ.get('GITHUB_SERVER_URL', 'https://github.com')}/{os.environ.get('GITHUB_REPOSITORY', '')}/actions/runs/{os.environ.get('GITHUB_RUN_ID', '')}"
        problems.append(f"{os.environ.get('GITHUB_WORKFLOW', 'a workflow')} run failed ({os.environ['JOB_STATUS']}): {run}")
    wl = ROOT / "data" / "lines" / "watch_log.csv"
    if wl.exists():
        last = pd.read_csv(wl, usecols=["ts"]).ts.iloc[-1]
        t = pd.to_datetime(last, format="%Y-%m-%dT%H-%M-%SZ", errors="coerce")
        if pd.notna(t) and (pd.Timestamp.now("UTC").tz_localize(None) - t).total_seconds() > 2 * 3600:
            problems.append(f"line watch late: last snapshot {last}")
    return (not problems), problems, (h or {})


def main():
    ok, problems, h = status()
    print("site checks:", "all pass" if ok else f"{len(problems)} failing", flush=True)
    import shutil
    if not os.environ.get("GH_TOKEN") or not shutil.which("gh"):
        print("no GH_TOKEN or gh CLI here: not touching issues"); return
    try:
        _sync_issue(ok, problems, h)
    except Exception as e:  # noqa  (an alert must never fail the run it reports on)
        print("could not update the issue:", str(e)[:200])


def _sync_issue(ok, problems, h):
    try:
        _gh("label", "create", LABEL, "--color", "d73a4a", "--description", "the site's tie and freshness checks")
    except Exception:  # noqa  (the label exists)
        pass
    open_ = json.loads(_gh("issue", "list", "--label", LABEL, "--state", "open", "--json", "number", "--limit", "5") or "[]")
    body = (f"Checked {h.get('checked', '?')} by the {h.get('source', '?')} ({h.get('passed', '?')} of {h.get('total', '?')} ties).\n\n"
            + "\n".join(f"- {p}" for p in problems[:40]) + "\n\nThe page shows the same list under Model -> Health checks. This issue closes itself when every check passes.")
    if not ok and not open_:
        _gh("issue", "create", "--title", "Site checks failing", "--label", LABEL, "--body", body); print("issue opened")
    elif not ok:
        _gh("issue", "edit", str(open_[0]["number"]), "--body", body); print("issue updated")
    elif open_:
        for i in open_:
            _gh("issue", "close", str(i["number"]), "--comment", f"Every check passes again ({h.get('passed')} of {h.get('total')}, {h.get('checked')})."); print("issue closed")


if __name__ == "__main__":
    main()
