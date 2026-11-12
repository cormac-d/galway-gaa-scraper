"""Backfill earlier Galway football seasons by season and competition id.

Why the results page could not do this
--------------------------------------
scraper.py drives fdate/tdate on /results/. That page has no season control,
so it answers for the live season whatever dates you give it - which is why
asking it for 2022-2025 returned nothing. Wrong door, not a bug.

The route that works
--------------------
    POST /wp-admin/admin-ajax.php
        action   = Get_competition_data
        value    = 6929        (football; 44 is hurling)
        seasonid = <season key>

returns {"groups": [...], "competition": "<html list of competitions>"}, where
the HTML holds one <a href=".../league/<id>">Name</a> per competition.

Sweeping seasonid found four seasons still served, each dated from real match
dates on its own competition pages:

    3070 -> 2023 (209 competitions)
    3642 -> 2024 (343)
    3831 -> 2025 (262)
    3976 -> 2026 (205)

Each /league/<id> page then carries its matches as data- attributes, exactly
the shape scraper.py already parses from the results page: data-date,
data-hometeam, data-homescore, data-venue, data-compname and the rest. So the
output below keeps scraper.py's schema and analyse.py needs no change.

One trap worth recording: the JSON escapes forward slashes, so the hrefs come
back as "https:\\/\\/www.galwaygaa.ie\\/league\\/189937". A regex for
"/league/(\\d+)" against the raw body matches nothing. Parse the JSON first,
then read the HTML it contains.
"""

import os
import re
import csv
import json
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup

BASE = "https://www.galwaygaa.ie"
AJAX = f"{BASE}/wp-admin/admin-ajax.php"
FOOTBALL = "6929"

# Every season the archive still serves, found by sweeping seasonid.
# The year is confirmed from each season's own match dates at run time
# rather than trusted from this map.
SEASONS = {1617: 2016, 1745: 2017, 1891: 2018, 2063: 2019, 2266: 2020,
           2588: 2021, 2849: 2022, 3070: 2023, 3642: 2024, 3831: 2025,
           3976: 2026}

# Schools and third-level competitions run on the same system but are not
# club football, so they are filtered out alongside hurling and camogie.
NOT_CLUB = re.compile(
    r'post primary|schools|colleges|ppsnr|ppsjn|bunscol|university|'
    r'sigerson|freshers|vocational', re.I)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; club-archive-research/1.0)",
    "Referer": f"{BASE}/competitions/",
}
PAUSE = 0.2
TIMEOUT = 30

FIELDS = ["Date", "Time", "Competition", "Home_Team", "Home_Score",
          "Away_Score", "Away_Team", "Venue", "Referee", "Match_Status",
          "Scraped_At"]

session = requests.Session()
session.headers.update(HEADERS)


def competitions_for(seasonid):
    """{competition_id: name} for one season."""
    try:
        r = session.post(
            AJAX,
            data={"action": "Get_competition_data", "value": FOOTBALL,
                  "seasonid": str(seasonid)},
            headers={"X-Requested-With": "XMLHttpRequest"},
            timeout=TIMEOUT,
        )
    except Exception as exc:
        print(f"  seasonid {seasonid}: {type(exc).__name__}")
        return {}
    if r.status_code != 200:
        print(f"  seasonid {seasonid}: http {r.status_code}")
        return {}

    # The competition list arrives as HTML inside a JSON field. Parsing the
    # JSON first is what unescapes the hrefs.
    try:
        html = r.json().get("competition", "") or ""
    except Exception:
        html = r.text.replace("\\/", "/")

    out = {}
    for a in BeautifulSoup(html, "html.parser").find_all("a", href=True):
        m = re.search(r"/league/(\d+)", a["href"])
        if m:
            out[int(m.group(1))] = a.get_text(" ", strip=True)
    return out


def matches_in(cid):
    """Every match on one competition page, in scraper.py's schema."""
    try:
        r = session.get(f"{BASE}/league/{cid}", timeout=TIMEOUT)
    except Exception:
        return []
    if r.status_code != 200:
        return []

    rows = []
    for el in BeautifulSoup(r.text, "html.parser").select("[data-hometeam]"):
        g = el.get
        home_s, away_s = g("data-homescore"), g("data-awayscore")
        rows.append({
            "Date": g("data-date") or "",
            "Time": g("data-time") or "",
            "Competition": (g("data-compname") or "").strip(),
            "Home_Team": g("data-hometeam") or "",
            # Leading apostrophe stops a spreadsheet reading 2-6 as a date,
            # matching what scraper.py writes.
            "Home_Score": f"'{home_s}" if home_s else "",
            "Away_Score": f"'{away_s}" if away_s else "",
            "Away_Team": g("data-awayteam") or "",
            "Venue": g("data-venue") or "",
            "Referee": g("data-referee") or "",
            "Match_Status": g("data-comment") or "",
            "Scraped_At": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })
    return rows


def scrape_season(seasonid, year):
    print(f"\n=== season {year} (seasonid {seasonid}) ===")
    comps = competitions_for(seasonid)
    print(f"  {len(comps)} competitions")
    time.sleep(PAUSE)

    all_rows, skipped = [], 0
    for n, (cid, name) in enumerate(sorted(comps.items()), 1):
        if ("hurling" in name.lower() or "camogie" in name.lower()
                or NOT_CLUB.search(name)):
            skipped += 1
            continue
        rows = matches_in(cid)
        time.sleep(PAUSE)
        for r in rows:
            if not r["Competition"]:
                r["Competition"] = name
        # Some competitions are mixed-code listings; filter per row too.
        rows = [r for r in rows
                if "hurling" not in r["Competition"].lower()
                and "camogie" not in r["Competition"].lower()
                and not NOT_CLUB.search(r["Competition"])]
        all_rows.extend(rows)
        if n % 50 == 0:
            print(f"  {n}/{len(comps)} competitions, {len(all_rows)} matches")

    seen, uniq = set(), []
    for r in all_rows:
        key = (r["Date"], r["Time"], r["Home_Team"], r["Away_Team"])
        if key in seen:
            continue
        seen.add(key)
        uniq.append(r)

    yrs = {}
    for r in uniq:
        m = re.search(r'(?:19|20)\d\d', r["Date"] or '')
        if m:
            yrs[int(m.group())] = yrs.get(int(m.group()), 0) + 1
    actual = max(yrs, key=yrs.get) if yrs else year
    if actual != year:
        print(f"  !! map says {year}, match dates say {actual} "
              f"({sorted(yrs.items(), key=lambda x: -x[1])[:3]})")
    print(f"  -> {len(uniq)} club football matches "
          f"({skipped} non-club competitions skipped), dated {actual}")
    return uniq, actual


def main():
    os.makedirs("data", exist_ok=True)
    wanted = {int(y) for y in
              os.environ.get("BACKFILL_YEARS", "2016 2017 2018 2019 2020 2021 2022").split()
              if y.isdigit()}

    summary = []
    for seasonid, year in sorted(SEASONS.items()):
        if year not in wanted:
            continue
        rows, year = scrape_season(seasonid, year)
        if not rows:
            summary.append(f"- **{year}**: nothing returned")
            continue
        path = f"data/season_{year}.csv"
        with open(path, "w", newline="", encoding="utf-8-sig") as fh:
            w = csv.DictWriter(fh, fieldnames=FIELDS)
            w.writeheader()
            w.writerows(rows)
        comps = len({r["Competition"] for r in rows})
        dates = sorted(d for d in (r["Date"] for r in rows) if d)
        mc = sum(1 for r in rows
                 if "Mhaigh Cuilinn" in (r["Home_Team"] + r["Away_Team"])
                 or "Maigh Cuilinn" in (r["Home_Team"] + r["Away_Team"]))
        summary.append(
            f"- **{year}**: {len(rows)} matches, {comps} competitions, "
            f"{mc} involving Moycullen"
            + (f" ({dates[0]} to {dates[-1]})" if dates else "")
        )
        print(f"  wrote {path}")

    with open("data/backfill_report.md", "w", encoding="utf-8") as fh:
        fh.write("# Backfill\n\n")
        fh.write(f"Run {datetime.utcnow():%Y-%m-%d %H:%M} UTC\n\n")
        fh.write("Seasons are requested by seasonid through admin-ajax.php, "
                 "then each competition is read by id. The results page "
                 "cannot do this: it has no season control.\n\n")
        fh.write("\n".join(summary) + "\n")
    print("\n" + "\n".join(summary))


if __name__ == "__main__":
    main()
