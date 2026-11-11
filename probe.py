"""Find out how the GAA results platform exposes earlier seasons.

Why
---
galwaygaa.ie/results/ only ever serves the current season, so the 2022-2025
backfill came back empty. But every competition page on the platform carries
the strings 2023, 2024, 2025 and 2026, which looks like a season control
somewhere in the page rather than four years of match dates.

If there is a season parameter, scraper.py needs one extra field and the whole
backfill works. This script goes looking for it, and reports exactly what it
finds so the next step is an informed one rather than another guess.

It dumps:
  - every <select> and its options, on the results page and a competition page
  - every form field (name/type/value), which is what the results page is
    actually driven by
  - every occurrence of "season" / "year" in the markup, with surrounding
    context
  - every link carrying a four-digit year
  - the real match rows on a competition page, so we can tell a live page from
    a placeholder

Output goes to data/structure_report.md, committed back to the repo.
"""

import os
import re
import json
from datetime import datetime

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; club-archive-research/1.0)",
    "Accept": "text/html,application/xhtml+xml",
}
TIMEOUT = 25

PAGES = [
    ("Galway results page", "https://www.galwaygaa.ie/results/"),
    ("Galway competitions page", "https://www.galwaygaa.ie/competitions/"),
    ("Galway U19 A Football League (known 2026)", "https://mayogaa.com/league/215277"),
    ("A low-band id", "https://mayogaa.com/league/180000"),
    ("A low-band Galway id", "https://www.galwaygaa.ie/league/178819"),
]

session = requests.Session()
session.headers.update(HEADERS)
out = []


def w(line=""):
    out.append(line)


def get(url):
    try:
        r = session.get(url, timeout=TIMEOUT)
        return r.text, r.status_code, r.url
    except Exception as exc:
        return None, f"error {type(exc).__name__}", url


def dump_selects(soup):
    rows = []
    for sel in soup.find_all("select"):
        name = sel.get("name") or sel.get("id") or "(unnamed)"
        opts = [(o.get("value"), o.get_text(strip=True))
                for o in sel.find_all("option")][:40]
        rows.append((name, opts))
    return rows


def dump_inputs(soup):
    rows = []
    for inp in soup.find_all(["input", "button"]):
        rows.append({
            "tag": inp.name,
            "type": inp.get("type"),
            "name": inp.get("name"),
            "id": inp.get("id"),
            "value": (inp.get("value") or "")[:40],
        })
    return rows[:60]


def context_hits(html, word, limit=12, pad=110):
    hits = []
    for m in re.finditer(word, html, re.I):
        a, b = max(0, m.start() - pad), min(len(html), m.end() + pad)
        frag = re.sub(r"\s+", " ", html[a:b])
        hits.append(frag)
        if len(hits) >= limit:
            break
    return hits


def year_links(soup):
    found = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if re.search(r"(19|20)\d\d", href) and len(href) < 220:
            found.append((a.get_text(" ", strip=True)[:60], href[:200]))
    # de-duplicate, keep order
    seen, uniq = set(), []
    for t, h in found:
        if h not in seen:
            seen.add(h)
            uniq.append((t, h))
    return uniq[:40]


def match_rows(soup):
    """The results page marks matches up as ul.table-body.results with
    data- attributes; competition pages use plain tables."""
    rows = []
    for el in soup.select("ul.table-body.results")[:5]:
        rows.append({k: v for k, v in el.attrs.items()
                     if k.startswith("data-")})
    if not rows:
        for tr in soup.select("table tr")[:8]:
            cells = [td.get_text(" ", strip=True)[:40]
                     for td in tr.find_all(["td", "th"])]
            if any(cells):
                rows.append(cells)
    return rows


def main():
    os.makedirs("data", exist_ok=True)
    w("# Platform structure probe")
    w()
    w(f"Run {datetime.utcnow():%Y-%m-%d %H:%M} UTC")
    w()
    w("Looking for whatever controls the season, so the backfill can ask for "
      "one. Each page below is reported in full: controls, season/year "
      "mentions, year-bearing links, and a sample of real match rows.")
    w()

    for label, url in PAGES:
        w(f"## {label}")
        w()
        w(f"`{url}`")
        w()
        html, status, final = get(url)
        if html is None:
            w(f"- **{status}**")
            w()
            continue
        w(f"- status {status}, {len(html):,} bytes, final url `{final}`")
        soup = BeautifulSoup(html, "html.parser")

        sels = dump_selects(soup)
        w(f"- {len(sels)} select element(s)")
        for name, opts in sels:
            shown = ", ".join(f"{v!r}:{t!r}" for v, t in opts[:14])
            w(f"    - **{name}** -> {shown}")

        inputs = dump_inputs(soup)
        named = [i for i in inputs if i["name"]]
        w(f"- {len(named)} named form field(s): "
          + ", ".join(f"{i['name']}({i['type']})" for i in named[:20]))

        for word in ("season", "year"):
            hits = context_hits(html, word)
            w(f"- {len(hits)} '{word}' mention(s) shown:")
            for h in hits:
                w(f"    - `{h}`")

        yl = year_links(soup)
        w(f"- {len(yl)} link(s) containing a year:")
        for t, h in yl[:20]:
            w(f"    - {t or '(no text)'} -> `{h}`")

        mr = match_rows(soup)
        w(f"- {len(mr)} sample content row(s):")
        for r in mr:
            w(f"    - `{json.dumps(r)[:400]}`")
        w()

    with open("data/structure_report.md", "w", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
