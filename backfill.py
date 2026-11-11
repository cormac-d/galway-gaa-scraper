"""Backfill earlier Galway football seasons by season and competition id.

Why this works where scraper.py did not
---------------------------------------
scraper.py drives fdate/tdate on /results/. That page has no season control at
all, so it answers for the live season whatever dates you give it - which is
why asking it for 2022-2025 returned nothing.

The competitions page uses a different route:

    POST /wp-admin/admin-ajax.php
        action   = Get_competition_data
        value    = 6929        (football; 44 is hurling)
        seasonid = <season key>

Sweeping seasonid found four seasons still being served, each confirmed by the
match dates on its own competition pages:

    3070 -> 2023 (209 competitions)
    3642 -> 2024 (343)
    3831 -> 2025 (262)
    3976 -> 2026 (205)

So: ask for a season's competitions, then read each competition page by id and
take its matches. Output matches scraper.py's schema exactly, so analyse.py and
everything downstream work unchanged.
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

SEASONS = {           # seasonid -> year, as established by the sweep
    3070: 2023,
    3642: 2024,
    3831: 2025,
    3976: 2026,
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; club-archive-research/1.0)",
    "Referer": f"{BASE}/competitions/",
}
PAUSE = 0.25
TIMEOUT = 30

FIELDS = ["Date", "Time", "Competition", "Home_Team", "Home_Score",
          "Away_Score", "Away_Team", "Venue", "Referee", "Match_Status",
          "Scraped_At"]

session = requests.Session()
session.headers.update(HEADERS)


def competitions_for(seasonid):
    """Competition ids in one season."""
    try:
        r = session.post(
            AJAX,
            data={"action": "Get_competition_data", "value": FOOTBALL,
                  "seasonid": str(seasonid)},
            headers={"X-Requested-With": "XMLHttpRequest"},
            timeout=TIMEOUT,
        )
    except Exception as exc:
        print(f"  season {seasonid}: {type(exc).__name__}")
        return []
    if r.status_code != 200:
        print(f"  season {seasonid}: http {r.status_code}")
        return []
    blob = r.text
    ids = {int(i) for i in re.findall(
        r'"?(?:competition_?id|id)"?\s*[:=]\s*"?(\d{5,7})"?', blob)}
    if not ids:
        ids = {int(i) for i in re.findall(r"/league/(\d+)", blob)}
    return sorted(ids)


def matches_in(cid):
    """Every match on one competition page."""
    try:
        r = session.get(f"{BASE}/league/{cid}", timeout=TIMEOUT)
    except Exception:
        return [], None
    if r.status_code != 200:
        return [], None
    soup = BeautifulSoup(r.text, "html.parser")
    rows = []

    # The platform marks matches up with data- attributes, the same shape the
    # results page uses, so one parser covers both.
    for el in soup.select("[data-hometeam]"):
        g = el.get
        home_s, away_s = g("data-homescore"), g("data-awayscore")
        rows.append({
            "Date": g("data-date") or "",
            "Time": g("data-time") or "",
            "Competition": (g("data-compname") or "").strip(),
            "Home_Team": g("data-hometeam") or "",
            "Home_Score": f"'{home_s}" if home_s else "",
            "Away_Score": f"'{away_s}" if away_s else "",
            "Away_Team": g("data-awayteam") or "",
            "Venue": g("data-venue") or "",
            "Referee": g("data-referee") or "",
            "Match_Status": g("data-comment") or "",
            "Scraped_At": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })

    title = None
    for sel in ("h1", "h2", ".comp-name"):
        el = soup.select_one(sel)
        t = el.get_text(strip=True) if el else ""
        if t and t.lower() not in ("league", "fixtures", "results"):
            title = t
            break

    # Fall back to the page title where a row carried no competition name.
    for row in rows:
        if not row["Competition"] and title:
            row["Competition"] = title
    return rows, title


def scrape_season(seasonid, year, sample_html_for=None):
    print(f"\n=== season {year} (seasonid {seasonid}) ===")
    ids = competitions_for(seasonid)
    print(f"  {len(ids)} competitions")
    time.sleep(PAUSE)

    all_rows, empty, hurling = [], 0, 0
    for n, cid in enumerate(ids, 1):
        rows, title = matches_in(cid)
        time.sleep(PAUSE)
        if not rows:
            empty += 1
            continue
        name = (rows[0]["Competition"] or title or "").lower()
        if "hurling" in name or "camogie" in name:
            hurling += 1
            continue
        all_rows.extend(rows)
        if n % 40 == 0:
            print(f"  {n}/{len(ids)} competitions, {len(all_rows)} matches")

    # Same de-duplication rule scraper.py uses.
    seen, uniq = set(), []
    for r in all_rows:
        key = (r["Date"], r["Time"], r["Home_Team"], r["Away_Team"])
        if key in seen:
            continue
        seen.add(key)
        uniq.append(r)

    print(f"  -> {len(uniq)} football matches "
          f"({empty} empty competitions, {hurling} hurling/camogie skipped)")
    return uniq


def main():
    os.makedirs("data", exist_ok=True)
    wanted = os.environ.get("BACKFILL_YEARS", "2023 2024 2025").split()
    wanted = {int(y) for y in wanted if y.isdigit()}

    summary = []
    for seasonid, year in sorted(SEASONS.items()):
        if year not in wanted:
            continue
        rows = scrape_season(seasonid, year)
        if not rows:
            summary.append(f"- **{year}**: nothing returned")
            continue
        path = f"data/season_{year}.csv"
        with open(path, "w", newline="", encoding="utf-8-sig") as fh:
            w = csv.DictWriter(fh, fieldnames=FIELDS)
            w.writeheader()
            w.writerows(rows)
        comps = len({r["Competition"] for r in rows})
        dates = sorted(r["Date"] for r in rows if r["Date"])
        summary.append(
            f"- **{year}**: {len(rows)} matches across {comps} competitions"
            + (f", {dates[0]} to {dates[-1]}" if dates else "")
        )
        print(f"  wrote {path}")

    with open("data/backfill_report.md", "w", encoding="utf-8") as fh:
        fh.write("# Backfill\n\n")
        fh.write(f"Run {datetime.utcnow():%Y-%m-%d %H:%M} UTC\n\n")
        fh.write("Seasons are fetched by seasonid through admin-ajax.php, then "
                 "each competition is read by id. The results page cannot do "
                 "this: it has no season control.\n\n")
        fh.write("\n".join(summary) + "\n")
    print("\n" + "\n".join(summary))


if __name__ == "__main__":
    main()
