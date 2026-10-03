"""Save public web pages as clean text for research notes (no logins, no block-dodging).

Run from the repo folder:
    python tools/scrape.py URL [URL ...]          save these pages
    python tools/scrape.py --file urls.txt        one URL per line
    python tools/scrape.py --crawl 200 URL        also follow up to 200 links on the same sites
    python tools/scrape.py --js URL               always render with headless Chrome (JavaScript sites)
    python tools/scrape.py --sitemap nflverse.com --match data   every page in a site's sitemap matching a word
    python tools/scrape.py --watch watchlist.txt  re-check pages and write data/private/research/changes-DATE.md

For each page:
1. Checks robots.txt. Pages it disallows are skipped and logged. Sites that refuse automated
   tools (401, 403, 429) are skipped too: we never get around technical blocks.
2. Fetches politely (a short pause between requests, one retry), with an honest name.
3. Opens JavaScript pages in headless Chrome or Edge; reads PDFs with pypdf.
4. Saves clean text to data/private/research/web-YYYY-MM-DD/<site>-<page>.md and the original
   page or PDF to .../files/. data/private/ is gitignored: third-party pages never go public.
5. Logs every page (saved, skipped, failed, empty, with the reason) to data/private/research/scrape-log.csv.
It never logs in, never solves CAPTCHAs, never disguises itself and never uses proxies.
"""

import argparse
import csv
import difflib
import hashlib
import datetime as dt
import html
import io
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from html.parser import HTMLParser
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "data" / "private" / "research"
AGENT = "NFLModelResearch/1.0 (research)"
DELAY = 1.5
LAST_HIT = {}  # site -> time of last request
BROWSERS = [
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
]
SKIP = {"script", "style", "noscript", "svg", "nav", "footer", "header", "form", "iframe", "button"}
BLOCK = {"p", "div", "section", "article", "main", "li", "tr", "br", "h1", "h2", "h3", "h4", "h5", "h6",
         "table", "ul", "ol", "blockquote", "pre", "dd", "dt"}


class ToText(HTMLParser):
    """Turns HTML into readable markdown-ish text: headings, paragraphs, lists, table rows."""

    def __init__(self, base):
        super().__init__(convert_charrefs=True)
        self.base, self.out, self.skip, self.title = base, [], 0, ""
        self.in_title, self.links = False, []
        self.row, self.cell = None, None

    def handle_starttag(self, tag, attrs):
        if tag in SKIP:
            self.skip += 1
            return
        if tag == "title":
            self.in_title = True
        if self.skip:
            return
        a = dict(attrs)
        if tag == "a" and a.get("href"):
            self.links.append(urllib.parse.urljoin(self.base, a["href"]))
        if tag == "tr":
            self.row = []
            return
        if tag in ("td", "th") and self.row is not None:
            self.cell = []
            return
        if self.cell is not None:
            return
        if tag in BLOCK:
            self.out.append("\n")
        if re.fullmatch(r"h[1-6]", tag):
            self.out.append("#" * int(tag[1]) + " ")
        elif tag == "li":
            self.out.append("- ")

    def handle_endtag(self, tag):
        if tag in SKIP:
            self.skip = max(0, self.skip - 1)
            return
        if tag == "title":
            self.in_title = False
        if self.skip:
            return
        if tag in ("td", "th") and self.cell is not None and self.row is not None:
            self.row.append(re.sub(r"\s+", " ", "".join(self.cell)).strip())
            self.cell = None
            return
        if tag == "tr" and self.row is not None:
            if any(self.row):
                self.out.append("\n| " + " | ".join(self.row) + " |\n")
            self.row = None
            return
        if self.cell is None and tag in BLOCK:
            self.out.append("\n")

    def handle_data(self, data):
        if self.in_title:
            self.title += data
        if self.skip:
            return
        if self.cell is not None:
            self.cell.append(data)
        elif self.row is None:
            self.out.append(data)

    def text(self):
        t = "".join(self.out)
        t = re.sub(r"[ \t\r\f\v]+", " ", t)
        t = re.sub(r" *\n *", "\n", t)
        t = re.sub(r"^-\s*$", "", t, flags=re.M)
        t = re.sub(r"^- Skip to .*$", "", t, flags=re.M)
        t = re.sub(r"-\n(?=\S)", "- ", t)
        return re.sub(r"\n{3,}", "\n\n", t).strip()



def main_part(page):
    """Return just the <main> (or first <article>) section if the page marks one; else the whole page."""
    for tag in ("main", "article"):
        m = re.search(rf"<{tag}[\s>].*?</{tag}>", page, re.S | re.I)
        if m and len(m.group(0)) > 2000:
            return m.group(0)
    return page


def allowed(url, cache):
    """Returns (ok, reason). Reasons explain blocks."""
    p = urllib.parse.urlsplit(url)
    root = f"{p.scheme}://{p.netloc}"
    if root not in cache:
        rp = urllib.robotparser.RobotFileParser(root + "/robots.txt")
        try:
            req = urllib.request.Request(root + "/robots.txt", headers={"User-Agent": AGENT})
            with urllib.request.urlopen(req, timeout=30) as r:
                rp.parse(r.read().decode("utf-8", "ignore").splitlines())
            cache[root] = (rp, None)
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                cache[root] = (None, f"site refuses automated tools (robots.txt answered {e.code}); a technical block, not a rule")
            else:
                cache[root] = (None, "")  # no robots.txt: allowed
        except Exception:
            cache[root] = (None, "")
    rp, reason = cache[root]
    if reason:
        return False, reason
    if rp is None:
        return True, "no robots.txt (allowed)"
    if rp.can_fetch(AGENT, url) and rp.can_fetch("*", url):
        return True, "allowed"
    return False, "robots.txt says do not copy this page"


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": AGENT})
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.read(), r.headers.get_content_type(), r.geturl()


def browser_dom(url):
    for b in BROWSERS:
        if b.exists():
            r = subprocess.run([str(b), "--headless", "--disable-gpu", f"--user-agent={AGENT}",
                                "--virtual-time-budget=8000", "--dump-dom", url],
                               capture_output=True, timeout=90)
            return r.stdout.decode("utf-8", "ignore")
    return ""


def pdf_text(data):
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(data))
    return "\n\n".join((p.extract_text() or "") for p in reader.pages)


def slug(url):
    p = urllib.parse.urlsplit(url)
    s = (p.netloc.replace("www.", "") + "-" + p.path.strip("/").replace("/", "-")).lower()
    s = re.sub(r"[^a-z0-9.-]+", "-", s).strip("-.")
    s = s or "page"
    if p.query:  # same path, different query string: keep them apart
        s = s[:81].rstrip("-.") + "-q" + hashlib.sha1(url.encode("utf-8")).hexdigest()[:6]
    if len(s) > 90:  # long URLs: keep a short fingerprint so two pages never share a file name
        s = s[:81].rstrip("-.") + "-" + hashlib.sha1(url.encode("utf-8")).hexdigest()[:8]
    return s


def save(url, title, text, robots_note, out_dir, original=None, ext="html"):
    """Save the cleaned text, plus the original page or PDF in files/ (kept on the laptop, not on GitHub)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    name = slug(url)
    path = out_dir / f"{name}.md"
    orig_note = ""
    if original is not None:
        files = out_dir / "files"
        files.mkdir(exist_ok=True)
        (files / f"{name}.{ext}").write_bytes(original)
        orig_note = f"- Original: files/{name}.{ext} (on the laptop only)\n"
    head = (f"# {title.strip() or url}\n\n"
            f"- Source URL: {url}\n- Saved: {dt.date.today().isoformat()}\n"
            f"- robots.txt: {robots_note}\n{orig_note}- Note: Frozen copy. Never edit.\n\n---\n\n")
    path.write_text(head + text + "\n", encoding="utf-8")
    return path


HASHES = None


def known_hashes():
    """Hashes of every page already saved (so the same page isn't saved twice)."""
    global HASHES
    if HASHES is None:
        HASHES = set()
        for f in OUT.glob("web-*/*.md"):
            body = f.read_text(encoding="utf-8", errors="ignore").split("\n---\n", 1)[-1].strip()
            HASHES.add(hashlib.sha1(re.sub(r"\s+", " ", body).encode("utf-8")).hexdigest())
    return HASHES


def log(url, status, reason, path="", chars=0):
    """One line per page in data/private/research/scrape-log.csv."""
    OUT.mkdir(parents=True, exist_ok=True)
    f = OUT / "scrape-log.csv"
    new = not f.exists()
    with open(f, "a", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        if new:
            w.writerow(["date", "url", "status", "reason", "file", "chars"])
        w.writerow([dt.datetime.now().strftime("%Y-%m-%d %H:%M"), url, status, reason, path, chars])


def wait_turn(url, cache):
    """Wait as long as the site asks (robots.txt Crawl-delay), at least DELAY seconds per site."""
    p = urllib.parse.urlsplit(url)
    root = f"{p.scheme}://{p.netloc}"
    delay = DELAY
    rp = cache.get(root, (None, ""))[0]
    if rp is not None:
        cd = rp.crawl_delay(AGENT) or rp.crawl_delay("*")
        if cd:
            delay = max(delay, float(cd))
    last = LAST_HIT.get(root)
    if last is not None:
        gap = time.time() - last
        if gap < delay:
            time.sleep(delay - gap)
    LAST_HIT[root] = time.time()


def sitemap_urls(site, match=None, limit=2000):
    """List page URLs from a site's sitemap(s) (robots.txt Sitemap lines, else /sitemap.xml)."""
    p = urllib.parse.urlsplit(site if "://" in site else "https://" + site)
    root = f"{p.scheme}://{p.netloc}"
    todo, found, seen = [], [], set()
    try:
        robots = fetch(root + "/robots.txt")[0].decode("utf-8", "ignore")
        todo += re.findall(r"(?im)^\s*sitemap:\s*(\S+)", robots)
    except Exception:
        pass
    if not todo:
        todo.append(root + "/sitemap.xml")
    while todo and len(found) < limit:
        sm = todo.pop(0)
        if sm in seen:
            continue
        seen.add(sm)
        try:
            data = fetch(sm)[0]
            if sm.endswith(".gz"):
                import gzip
                data = gzip.decompress(data)
            xml = data.decode("utf-8", "ignore")
        except Exception:
            continue
        locs = [html.unescape(u) for u in re.findall(r"<loc>\s*(.*?)\s*</loc>", xml, re.S)]
        if "<sitemapindex" in xml:
            todo += locs
        else:
            found += [u for u in locs if not match or re.search(match, u, re.I)]
    return found[:limit]


def get(url):
    """Fetch with one retry on a timeout or dropped connection."""
    for attempt in (1, 2):
        try:
            return fetch(url)
        except urllib.error.HTTPError:
            raise
        except Exception:
            if attempt == 2:
                raise
            time.sleep(5)


def run(urls, crawl, force_js=False, watch=None):
    out_dir = OUT / f"web-{dt.date.today().isoformat()}"
    cache, seen, queue = {}, set(), list(urls)
    saved, skipped = [], []
    sites = {urllib.parse.urlsplit(u).netloc for u in urls}
    budget = crawl
    while queue:
        url = queue.pop(0).split("#")[0]
        if url in seen:
            continue
        seen.add(url)
        ok, reason = allowed(url, cache)
        if not ok:
            skipped.append(url)
            log(url, "skipped", reason)
            print(f"SKIPPED ({reason}): {url}")
            continue
        note = reason
        wait_turn(url, cache)
        try:
            data, ctype, final = get(url)
        except urllib.error.HTTPError as e:
            why = f"site refused the page ({e.code}); a technical block" if e.code in (401, 403, 429) else f"error {e.code}"
            skipped.append(url)
            log(url, "skipped", why)
            print(f"SKIPPED ({why}): {url}")
            continue
        except Exception as e:
            log(url, "failed", str(e)[:120])
            print(f"FAILED {url}: {e}")
            continue
        links, ext = [], "html"
        try:
            if ctype == "application/pdf" or url.lower().endswith(".pdf"):
                title, text, ext = url.rsplit("/", 1)[-1], pdf_text(data), "pdf"
            else:
                page = data.decode("utf-8", "ignore")
                title_m = re.search(r"<title[^>]*>(.*?)</title>", page, re.S | re.I)
                p = ToText(final)
                p.feed(main_part(page))
                text, links = p.text(), p.links
                title = html.unescape(title_m.group(1)) if title_m else ""
                if force_js or len(text) < 500:  # probably needs JavaScript
                    dom = browser_dom(url)
                    if dom:
                        p = ToText(final)
                        p.feed(main_part(dom))
                        if len(p.text()) > len(text):
                            text, links, data = p.text(), p.links, dom.encode("utf-8")
        except Exception as e:
            log(url, "failed", f"could not read: {str(e)[:100]}")
            print(f"FAILED to read {url}: {e}")
            continue
        digest = hashlib.sha1(re.sub(r"\s+", " ", text).encode("utf-8")).hexdigest()
        if digest in known_hashes():
            log(url, "duplicate", "same text already saved")
            print(f"DUPLICATE (already saved): {url}")
            continue
        if len(text.strip()) < 100:
            log(url, "empty", "almost no text (needs a person to look)")
            print(f"EMPTY (needs a person to look): {url}")
            continue
        path = save(url, title, text, note, out_dir, data, ext)
        saved.append(path)
        rel = str(path.relative_to(REPO))
        log(url, "saved", note, rel, len(text))
        HASHES.add(digest)
        if watch is not None:
            watch.append((url, rel))
        print(f"saved {rel} ({len(text):,} chars)")
        if budget > 0:
            for link in links:
                link = link.split("#")[0]
                if urllib.parse.urlsplit(link).netloc in sites and link not in seen and link not in queue and budget > 0 \
                        and not re.search(r"\.(jpg|jpeg|png|gif|webp|zip|mp4|mp3|css|js|ico|svg)$", link, re.I) \
                        and not re.search(r"(login|signin|sign-in|cart|checkout|account|mailto:|tel:)", link, re.I):
                    queue.append(link)
                    budget -= 1
    print(f"\nDone: {len(saved)} saved, {len(skipped)} skipped (full log: data/private/research/scrape-log.csv)")
    return saved, skipped


def watch_report(pairs):
    """Compare each newly saved page with its previous saved copy; write data/private/research/changes-DATE.md."""
    today = dt.date.today().isoformat()
    lines = [f"# What changed on watched pages ({today})", ""]
    for url, rel in pairs:
        new = REPO / rel
        olds = sorted(f for f in OUT.glob(f"web-*/{new.name}") if f != new)
        if not olds:
            lines.append(f"- NEW (no earlier copy): {url}")
            continue
        a = olds[-1].read_text(encoding="utf-8", errors="ignore").split("\n---\n", 1)[-1].splitlines()
        b = new.read_text(encoding="utf-8", errors="ignore").split("\n---\n", 1)[-1].splitlines()
        diff = [l for l in difflib.unified_diff(a, b, lineterm="", n=0) if l[:1] in "+-" and l[:3] not in ("+++", "---")]
        lines.append(f"- {'CHANGED' if diff else 'no change'}: {url}" + (f" ({len(diff)} lines; vs {olds[-1].parent.name})" if diff else ""))
        lines += [f"    {l[:200]}" for l in diff[:40]]
    out = OUT / f"changes-{today}.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Change report: {out.relative_to(REPO)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("urls", nargs="*")
    ap.add_argument("--file", help="text file with one URL per line")
    ap.add_argument("--crawl", type=int, default=0, help="also follow up to N links on the same sites")
    ap.add_argument("--sitemap", help="add pages from this site's sitemap (e.g. nflverse.com)")
    ap.add_argument("--match", help="with --sitemap: only URLs containing this text or pattern")
    ap.add_argument("--watch", help="re-check the URLs in this file and write a 'what changed' report")
    ap.add_argument("--js", action="store_true", help="always open pages in headless Chrome (for sites that load text by JavaScript)")
    a = ap.parse_args()
    urls = list(a.urls)
    if a.file:
        urls += [l.strip() for l in Path(a.file).read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
    if a.sitemap:
        urls += sitemap_urls(a.sitemap, a.match)
    pairs = None
    if a.watch:
        urls += [l.strip() for l in Path(a.watch).read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
        pairs = []
        HASHES = set()  # in watch mode, save even if unchanged, so it can be compared
    if not urls:
        sys.exit("Give at least one URL.")
    run(urls, a.crawl, a.js, pairs)
    if pairs is not None:
        watch_report(pairs)
