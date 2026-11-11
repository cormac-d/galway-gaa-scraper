"""Probe the GAA results platform for archived competitions.

Background
----------
The county results pages (galwaygaa.ie/results/) only ever serve the current
season, which is why backfilling 2022-2025 through scraper.py produced nothing.

But competitions on this platform are also addressable directly by a numeric
id, as /league/<id>, and that id is NOT scoped to a county: a Galway
competition can be read through mayogaa.com, gaacork.ie or any other county
domain. If those ids are allocated sequentially over time, earlier seasons are
still sitting there and can be read by id even though the results page will not
surface them.

This script tests that. It does two things:

  1. DISCOVERY - loads the county fixtures/results pages and harvests every
     /league/<id> link it can see, together with any season selector. If the
     site exposes a season dropdown, we get earlier ids for free and no
     scanning is needed.

  2. PROBE - samples competition ids across a wide range and records what
     each one is: competition name, the teams, and the date range of its
     matches. That maps id -> season, which tells us where 2025 lives.

Output lands in data/ as a CSV index plus a readable report, both committed
back to the repo so they can be read from git.

Nothing here writes to any GAA system; it issues ordinary GET requests at a
deliberately gentle rate.
"""

import os
import re
import csv
import json
import time
import random
from datetime import datetime

import requests
from bs4 import BeautifulSoup

UA = "Mozilla/5.0 (compatible; club-archive-research/1.0)"
HEADERS = {"User-Agent": UA, "Accept": "text/html,application/xhtml+xml"}
TIMEOUT = 20
PAUSE = 0.4          # be polite between requests

# Any of these domains serve the same backend; if one is slow or blocks us we
# can read the identical competition through another.
HOSTS = [
    "https://www.galwaygaa.ie",
    "https://mayogaa.com",
    "https://gaacork.ie",
]

# Competition ids already known to exist, all from the 2026 season. These
# anchor the search: whatever numbering scheme is in use, 2025 sits below them.
KNOWN_2026 = [214414, 214631, 215277, 215383, 215416]

DATE_RE = re.compile(r"(\d{1,2})[-/ ]([A-Za-z]{3,9}|\d{1,2})[-/ ](\d{2,4})")
LEAGUE_HREF_RE = re.compile(r"/league/(\d+)")

session = requests.Session()
session.headers.update(HEADERS)


def get(url):
    """GET a page, returning text or None. Never raises."""
    try:
        r = session.get(url, timeout=TIMEOUT)
    except Exception as exc:
        return None, f"error: {type(exc).__name__}"
    if r.status_code != 200:
        return None, f"http {r.status_code}"
    return r.text, "ok"


def years_in(text):
    """Pull plausible match years out of a page."""
    years = set()
    for m in re.finditer(r"\b(20[0-2]\d)\b", text):
        y = int(m.group(1))
        if 2005 <= y <= 2027:
            years.add(y)
    return years


def parse_competition(html):
    """Extract competition name, team names and match years from a page."""
    soup = BeautifulSoup(html, "html.parser")

    title = None
    for sel in ("h1", "h2", ".comp-name", ".competition-title", "title"):
        el = soup.select_one(sel)
        if el and el.get_text(strip=True):
            title = el.get_text(strip=True)
            break

    # Teams tend to appear in the standings table's first column.
    teams = []
    for row in soup.select("table tr"):
        cells = row.find_all(["td", "th"])
        if cells:
            t = cells[0].get_text(strip=True)
            if t and len(t) < 60 and not t.lower().startswith(("pos", "#", "team")):
                teams.append(t)
    teams = [t for t in teams if t][:6]

    text = soup.get_text(" ", strip=True)
    return {
        "title": (title or "")[:160],
        "teams": " | ".join(teams)[:300],
        "years": sorted(years_in(text)),
        "chars": len(text),
    }


def discover():
    """Harvest competition ids and any season selector from index pages."""
    found = {}
    notes = []
    index_paths = [
        "/fixtures-results/",
        "/fixtures-and-results/",
        "/results/",
        "/competitions/",
    ]
    for host in HOSTS:
        for path in index_paths:
            url = host + path
            html, status = get(url)
            time.sleep(PAUSE)
            if not html:
                notes.append(f"{url} -> {status}")
                continue

            ids = set(int(i) for i in LEAGUE_HREF_RE.findall(html))
            soup = BeautifulSoup(html, "html.parser")

            # Does the page offer a season / year selector?
            selectors = []
            for sel in soup.find_all("select"):
                name = (sel.get("name") or sel.get("id") or "").lower()
                opts = [o.get_text(strip=True) for o in sel.find_all("option")][:30]
                if any(re.fullmatch(r"20\d\d", o or "") for o in opts) or \
                   any(k in name for k in ("season", "year")):
                    selectors.append({"name": name, "options": opts})

            notes.append(
                f"{url} -> ok, {len(ids)} league ids, {len(selectors)} season selector(s)"
            )
            if selectors:
                notes.append("    selectors: " + json.dumps(selectors)[:800])
            if ids:
                found.setdefault(host, set()).update(ids)
                notes.append(
                    f"    id range {min(ids)}-{max(ids)} (sample {sorted(ids)[:8]})"
                )
    return found, notes


def probe_ids(ids, host):
    """Fetch each competition id and describe it."""
    rows = []
    for cid in ids:
        url = f"{host}/league/{cid}"
        html, status = get(url)
        time.sleep(PAUSE)
        if not html:
            rows.append({"id": cid, "status": status, "title": "", "teams": "",
                         "years": "", "url": url})
            continue
        info = parse_competition(html)
        rows.append({
            "id": cid,
            "status": "ok" if info["chars"] > 400 else "thin",
            "title": info["title"],
            "teams": info["teams"],
            "years": ",".join(str(y) for y in info["years"]),
            "url": url,
        })
        print(f"{cid}: {info['title'][:70]} | years={info['years']}")
    return rows


def main():
    os.makedirs("data", exist_ok=True)
    report = []
    report.append("# Competition id probe")
    report.append("")
    report.append(f"Run {datetime.utcnow():%Y-%m-%d %H:%M} UTC")
    report.append("")

    # ---- 1. discovery -----------------------------------------------------
    report.append("## 1. Discovery on index pages")
    report.append("")
    found, notes = discover()
    report.extend("- " + n for n in notes)
    report.append("")

    discovered = sorted({i for s in found.values() for i in s})
    if discovered:
        report.append(
            f"Discovered {len(discovered)} ids, range "
            f"{min(discovered)}-{max(discovered)}."
        )
    else:
        report.append("No ids discovered from index pages.")
    report.append("")

    # ---- 2. probe ---------------------------------------------------------
    # Anchor on the known 2026 ids, then walk backwards in widening steps to
    # find where earlier seasons sit. Geometric spread first: if 2025 is only
    # a few thousand below 2026 we want to know before scanning finely.
    anchor = min(KNOWN_2026)
    offsets = [0, 500, 1000, 2000, 3000, 5000, 7500, 10000, 15000, 20000,
               25000, 30000, 40000, 50000, 65000, 80000, 100000]
    targets = [anchor - o for o in offsets if anchor - o > 1000]
    targets += KNOWN_2026
    targets += random.sample(discovered, min(8, len(discovered))) if discovered else []
    targets = sorted(set(targets), reverse=True)

    host = os.environ.get("PROBE_HOST", HOSTS[1])   # mayogaa by default
    report.append(f"## 2. Id probe via {host}")
    report.append("")
    report.append(f"Probing {len(targets)} ids.")
    report.append("")

    rows = probe_ids(targets, host)

    with open("data/competition_index.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["id", "status", "title", "teams",
                                           "years", "url"])
        w.writeheader()
        w.writerows(rows)

    report.append("| id | status | years | title |")
    report.append("|---|---|---|---|")
    for r in rows:
        report.append(
            f"| {r['id']} | {r['status']} | {r['years'] or '-'} | {r['title'][:70] or '-'} |"
        )
    report.append("")

    # ---- 3. read the result ----------------------------------------------
    by_year = {}
    for r in rows:
        for y in (r["years"] or "").split(","):
            if y:
                by_year.setdefault(int(y), []).append(r["id"])
    report.append("## 3. Which ids carry which season")
    report.append("")
    if by_year:
        for y in sorted(by_year, reverse=True):
            ids = sorted(by_year[y])
            report.append(f"- **{y}**: {len(ids)} ids, {min(ids)}-{max(ids)}")
    else:
        report.append("No dated competitions found - the pages may be "
                      "JavaScript-rendered, in which case this needs the "
                      "playwright approach used by scraper.py.")
    report.append("")

    with open("data/probe_report.md", "w", encoding="utf-8") as fh:
        fh.write("\n".join(report) + "\n")
    print("\n".join(report[-30:]))


if __name__ == "__main__":
    main()
