"""Before publishing the page (24 Sep 2026). A page was once published from data built before a fix was merged, while
the fix was reported as live. This refuses that, and a page whose health checks fail. Run from a checkout:

    python -m nflmodel.publish_check [--ref origin/main]

Checks, on the ref's committed files (git show, so a local rebuild never passes for the committed one):
  1. web/data/meta.js carries the commit whose code built the data (code_sha), and every commit that changed the
     code that builds data (nflmodel/, experiments/) is inside it: the data is not older than the newest code. A change
     to web/index.html alone builds no data, so it publishes without a new weekly run (26 Sep 2026: every page tweak
     had waited 15 minutes for a full rebuild); the page still needs every file it loads (3)
  2. web/data/health.js: every health check passes
  3. every data file the page loads exists
Exit status 0 when all pass, 1 otherwise, with the reasons.
"""
from __future__ import annotations
import json, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CODE = ["nflmodel", "experiments"]   # the code that builds the data; the page (web/index.html) only reads it


def _git(*a: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True)


def _js(ref: str, path: str) -> dict | None:
    r = _git("show", f"{ref}:{path}")
    if r.returncode:
        return None
    s = r.stdout
    return json.loads(s[s.index("=") + 1:].rstrip().rstrip(";"))


def check(ref: str = "origin/main") -> list[str]:
    bad = []
    meta = _js(ref, "web/data/meta.js")
    sha = (meta or {}).get("code_sha", "")
    newest = _git("log", "-1", "--format=%H", ref, "--", *CODE).stdout.strip()
    if not sha:
        bad.append("web/data/meta.js has no code_sha: the data predates the stamp; run the weekly run")
    elif _git("cat-file", "-e", f"{sha}^{{commit}}").returncode:
        bad.append(f"code_sha {sha[:9]} is not a known commit (git fetch first)")
    elif newest and _git("merge-base", "--is-ancestor", newest, sha).returncode:
        bad.append(f"data built by {sha[:9]}, older than the newest code change {newest[:9]} "
                   f"({_git('log', '-1', '--format=%s', newest).stdout.strip()[:80]}): run the weekly run and wait for its commit")
    h = _js(ref, "web/data/health.js")
    if h is None:
        bad.append("web/data/health.js missing")
    else:
        fails = h.get("fails") or [c[0] for c in h.get("checks", []) if not c[1]]
        if not h.get("ok") or fails:
            bad.append(f"health checks failing ({h.get('passed')} of {h.get('total')} pass, {h.get('checked')}): " + "; ".join(str(f)[:80] for f in fails[:5]))
    page = _git("show", f"{ref}:web/index.html").stdout
    for src in sorted(set(re.findall(r'src="(data/[^"?]+)', page))):
        if _git("cat-file", "-e", f"{ref}:web/{src}").returncode:
            bad.append(f"page loads {src}, which is not committed")
    return bad


if __name__ == "__main__":
    ref = sys.argv[sys.argv.index("--ref") + 1] if "--ref" in sys.argv else "origin/main"
    b = check(ref)
    print("publish check: PASS" if not b else "publish check: FAIL\n  " + "\n  ".join(b))
    sys.exit(1 if b else 0)
